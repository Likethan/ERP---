"""Security Event Detection and Alerting Service for CampusOS.

Monitors security-sensitive events including authentication brute-forcing,
cross-tenant boundary escape attempts, permission denial spikes, rate limit breaches,
and token abuse.
"""

from collections import deque
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.core.logging import logger
from app.core.sanitizer import mask_sensitive_dict


class SecurityEvent(BaseModel):
    """Structured security incident or alert representation."""

    id: UUID = Field(default_factory=uuid4)
    event_type: str
    severity: str  # HIGH, MEDIUM, LOW, CRITICAL
    tenant_id: UUID | None = None
    user_id: UUID | None = None
    ip_address: str = "unknown"
    request_id: str = "-"
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SecurityEventService:
    """In-memory security monitoring and alert aggregation engine."""

    def __init__(self, max_history: int = 500):
        self._history: deque[SecurityEvent] = deque(maxlen=max_history)
        self._ip_failures: dict[str, list[datetime]] = {}

    def record_event(
        self,
        event_type: str,
        severity: str,
        tenant_id: UUID | None = None,
        user_id: UUID | None = None,
        ip_address: str = "unknown",
        request_id: str = "-",
        details: dict[str, Any] | None = None,
    ) -> SecurityEvent:
        """Log, record, and categorize a security event."""
        sanitized_details = mask_sensitive_dict(details or {})
        event = SecurityEvent(
            event_type=event_type,
            severity=severity.upper(),
            tenant_id=tenant_id,
            user_id=user_id,
            ip_address=ip_address,
            request_id=request_id,
            details=sanitized_details,
        )
        self._history.append(event)

        log_fn = logger.warning
        if event.severity in ("HIGH", "CRITICAL"):
            log_fn = logger.error

        log_fn(
            "SECURITY EVENT [%s] (%s) ip=%s req=%s tenant=%s user=%s details=%s",
            event.event_type,
            event.severity,
            event.ip_address,
            event.request_id,
            event.tenant_id,
            event.user_id,
            sanitized_details,
        )
        return event

    def record_failed_login(
        self,
        ip_address: str,
        email: str,
        tenant_id: UUID | None = None,
        request_id: str = "-",
    ) -> None:
        """Track login failures and flag brute-force threshold breaches."""
        now = datetime.now(UTC)
        window_minutes = 10
        threshold = 5

        # Prune old failures for this IP
        failures = [
            t for t in self._ip_failures.get(ip_address, [])
            if (now - t).total_seconds() <= window_minutes * 60
        ]
        failures.append(now)
        self._ip_failures[ip_address] = failures

        if len(failures) >= threshold:
            self.record_event(
                event_type="AUTH_BRUTE_FORCE_SUSPECTED",
                severity="HIGH",
                tenant_id=tenant_id,
                ip_address=ip_address,
                request_id=request_id,
                details={
                    "consecutive_failures": len(failures),
                    "window_minutes": window_minutes,
                    "target_account": email,
                },
            )
        else:
            self.record_event(
                event_type="AUTH_LOGIN_FAILED",
                severity="LOW",
                tenant_id=tenant_id,
                ip_address=ip_address,
                request_id=request_id,
                details={"target_account": email},
            )

    def record_cross_tenant_attempt(
        self,
        actor_tenant_id: UUID,
        target_tenant_id: UUID,
        user_id: UUID | None = None,
        ip_address: str = "unknown",
        request_id: str = "-",
        resource: str = "unknown",
    ) -> None:
        """Record a prohibited cross-tenant access attempt."""
        self.record_event(
            event_type="SECURITY_ACCESS_DENIED",
            severity="HIGH",
            tenant_id=actor_tenant_id,
            user_id=user_id,
            ip_address=ip_address,
            request_id=request_id,
            details={
                "violation": "cross_tenant_boundary_attempt",
                "actor_tenant": str(actor_tenant_id),
                "target_tenant": str(target_tenant_id),
                "resource": resource,
            },
        )

    def get_events(
        self,
        tenant_id: UUID | None = None,
        limit: int = 50,
        severity: str | None = None,
    ) -> list[SecurityEvent]:
        """Query security events with optional tenant and severity filtering."""
        results: list[SecurityEvent] = []
        for event in reversed(self._history):
            if tenant_id is not None and event.tenant_id != tenant_id:
                continue
            if severity is not None and event.severity != severity.upper():
                continue
            results.append(event)
            if len(results) >= limit:
                break
        return results

    def clear(self) -> None:
        """Clear recorded events (used in test fixtures)."""
        self._history.clear()
        self._ip_failures.clear()


security_events = SecurityEventService()
