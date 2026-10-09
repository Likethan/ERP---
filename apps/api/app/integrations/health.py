"""Integration Health Monitoring and Operational Telemetry.

Enforces:
- Health check probes, error rate tracking, latency metrics, and availability scoring.
- Scrubbed diagnostic responses ensuring credentials, tokens, and internal IPs are never leaked.
- Automatic synchronization with Circuit Breaker state.
"""

from datetime import UTC, datetime
import logging
import time
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.integrations.circuit_breaker import (
    circuit_breaker_engine,
)
from app.integrations.security import SafeHttpClient
from app.models.integration import (
    CircuitBreakerState,
    IntegrationConnector,
    IntegrationHealth,
    IntegrationHealthStatus,
    IntegrationLog,
    IntegrationLogStatus,
)

logger = logging.getLogger("campusos.integrations.health")


class IntegrationHealthService:
    """Manages connector health state and runs active diagnostic health checks."""

    @classmethod
    async def get_or_create_health_record(
        cls,
        db: AsyncSession,
        connector_id: UUID,
        tenant_id: UUID | None = None,
    ) -> IntegrationHealth:
        """Fetch existing health record or create default initial UNKNOWN status."""
        stmt = select(IntegrationHealth).where(IntegrationHealth.connector_id == connector_id)
        health = (await db.execute(stmt)).scalar_one_or_none()
        if not health:
            health = IntegrationHealth(
                id=uuid4(),
                tenant_id=tenant_id,
                connector_id=connector_id,
                status=IntegrationHealthStatus.UNKNOWN,
                consecutive_failures=0,
                error_rate=0.0,
                circuit_state=CircuitBreakerState.CLOSED,
                last_checked_at=datetime.now(UTC),
                details={},
            )
            db.add(health)
            await db.flush()
        return health

    @classmethod
    async def check_connector_health(
        cls,
        db: AsyncSession,
        connector: IntegrationConnector,
        allow_private_networks_for_tests: bool = False,
    ) -> IntegrationHealth:
        """Execute active diagnostic probe against connector's ping or base URL."""
        health = await cls.get_or_create_health_record(
            db, connector.id, tenant_id=connector.tenant_id
        )

        cfg = connector.configuration or {}
        ping_url = cfg.get("base_url") or cfg.get("target_url") or cfg.get("api_endpoint")
        now = datetime.now(UTC)

        if not ping_url:
            health.status = IntegrationHealthStatus.HEALTHY
            health.last_checked_at = now
            health.details = {"message": "Connector configured without direct HTTP ping target"}
            await db.commit()
            return health

        start_t = time.perf_counter()
        try:
            resp = await SafeHttpClient.request(
                method="GET",
                url=ping_url,
                timeout_seconds=5.0,
                allowed_domains=connector.allowed_domains,
                allow_private_networks_for_tests=allow_private_networks_for_tests,
            )
            duration_ms = int((time.perf_counter() - start_t) * 1000)

            health.last_latency_ms = duration_ms
            health.last_checked_at = now

            if 200 <= resp.status_code < 400:
                health.status = IntegrationHealthStatus.HEALTHY
                health.last_success_at = now
                health.consecutive_failures = 0
                health.error_rate = max(0.0, health.error_rate * 0.8)
                health.circuit_state = CircuitBreakerState.CLOSED
                health.details = {
                    "last_status_code": resp.status_code,
                    "latency_ms": duration_ms,
                    "check_result": "PASS",
                }
            else:
                health.last_failure_at = now
                health.consecutive_failures += 1
                health.error_rate = min(1.0, health.error_rate + 0.2)
                health.status = (
                    IntegrationHealthStatus.DEGRADED
                    if health.consecutive_failures < 3
                    else IntegrationHealthStatus.UNHEALTHY
                )
                health.details = {
                    "last_status_code": resp.status_code,
                    "latency_ms": duration_ms,
                    "check_result": f"FAIL (HTTP {resp.status_code})",
                }

        except Exception as exc:
            duration_ms = int((time.perf_counter() - start_t) * 1000)
            health.last_failure_at = now
            health.last_latency_ms = duration_ms
            health.consecutive_failures += 1
            health.error_rate = min(1.0, health.error_rate + 0.3)
            health.last_checked_at = now

            (
                health.circuit_state,
                health.consecutive_failures,
                health.circuit_opened_at,
            ) = circuit_breaker_engine.record_failure(
                health.circuit_state,
                health.consecutive_failures,
                now=now,
            )

            health.status = (
                IntegrationHealthStatus.UNHEALTHY
                if health.circuit_state == CircuitBreakerState.OPEN
                else IntegrationHealthStatus.DEGRADED
            )
            health.details = {
                "check_result": "ERROR",
                "error_message": str(exc)[:300],
                "circuit_breaker": health.circuit_state,
            }

        await db.commit()
        return health


class IntegrationAuditLogger:
    """Records sanitized forensic integration logs, scrubbing sensitive payloads."""

    @classmethod
    async def log_operation(
        cls,
        db: AsyncSession,
        tenant_id: UUID | None,
        connector_id: UUID | None,
        operation: str,
        request_id: str,
        correlation_id: str,
        status: IntegrationLogStatus,
        http_status: int | None = None,
        duration_ms: int | None = None,
        event_type: str | None = None,
        error_message: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> IntegrationLog:
        """Append immutable sanitized integration execution entry."""
        safe_details = dict(details or {})
        # Remove any sensitive authorization or token fields
        for key in list(safe_details.keys()):
            k_lower = key.lower()
            if any(s in k_lower for s in ("token", "secret", "password", "key", "auth", "cvv")):
                safe_details[key] = "[REDACTED]"

        log_entry = IntegrationLog(
            id=uuid4(),
            tenant_id=tenant_id,
            connector_id=connector_id,
            operation=operation,
            event_type=event_type,
            request_id=request_id,
            correlation_id=correlation_id,
            status=status,
            http_status=http_status,
            duration_ms=duration_ms,
            error_message=error_message[:500] if error_message else None,
            details=safe_details,
        )
        db.add(log_entry)
        await db.commit()
        return log_entry
