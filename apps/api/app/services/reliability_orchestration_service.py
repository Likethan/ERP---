"""Enterprise Platform Reliability & Disaster Recovery Orchestration Service (Step 31).

Product Vision: "One Campus. One System. One Source of Truth."

Aggregates:
- Comprehensive disaster recovery posture and readiness
- Backup freshness, verification badges, and RPO compliance
- Worker queue lag and event backlog diagnostics
- Downstream dependency circuit breaker states
- Graceful degradation status reporting
"""

from datetime import UTC, datetime
import logging
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import OutboxService
from app.core.reliability_config import evaluate_backup_freshness
from app.core.resilience import circuit_registry
from app.models.reliability import (
    BackupStatus,
    PlatformBackupRecord,
    PlatformRestoreVerification,
    ReliabilityCircuitBreakerState,
    RestoreVerificationStatus,
)
from app.schemas.reliability import (
    CircuitBreakerResponse,
    PlatformReliabilityStatusResponse,
)

logger = logging.getLogger("campusos.reliability_orchestration")


class ReliabilityOrchestrationService:
    """Aggregates platform resilience posture, backup readiness, and degraded modes."""

    @classmethod
    async def get_reliability_status(cls, db: AsyncSession) -> PlatformReliabilityStatusResponse:
        """Compute holistic reliability and disaster recovery status."""
        # 1. Inspect Backups
        last_backup_stmt = (
            select(PlatformBackupRecord)
            .order_by(desc(PlatformBackupRecord.started_at))
            .limit(1)
        )
        last_backup_res = await db.execute(last_backup_stmt)
        last_backup = last_backup_res.scalar_one_or_none()

        last_success_stmt = (
            select(PlatformBackupRecord)
            .where(PlatformBackupRecord.status == BackupStatus.COMPLETED)
            .order_by(desc(PlatformBackupRecord.started_at))
            .limit(1)
        )
        last_success_res = await db.execute(last_success_stmt)
        last_success = last_success_res.scalar_one_or_none()

        freshness_status, backup_age_hours = evaluate_backup_freshness(
            last_success.completed_at if last_success else None
        )

        # 2. Inspect Restore Verifications
        last_restore_stmt = (
            select(PlatformRestoreVerification)
            .order_by(desc(PlatformRestoreVerification.started_at))
            .limit(1)
        )
        last_restore_res = await db.execute(last_restore_stmt)
        last_restore = last_restore_res.scalar_one_or_none()

        # 3. Inspect Outbox & Worker Backlog
        backlog_metrics = await OutboxService.get_backlog_metrics(db)

        # 4. Inspect Circuit Breakers
        all_breakers = circuit_registry.get_all()
        cb_responses: list[CircuitBreakerResponse] = []
        open_count = 0
        degraded_services: list[str] = []

        for b in all_breakers:
            cb_data = b.to_dict()
            cb_responses.append(CircuitBreakerResponse(**cb_data))
            if b.state == ReliabilityCircuitBreakerState.OPEN:
                open_count += 1
                degraded_services.append(f"Dependency '{b.dependency_name}' circuit is OPEN (fast-failing).")
            elif b.state == ReliabilityCircuitBreakerState.HALF_OPEN:
                degraded_services.append(f"Dependency '{b.dependency_name}' is in HALF_OPEN canary probe state.")

        # Check queue delay degradation
        if not backlog_metrics["is_healthy"]:
            degraded_services.append(
                f"Outbox processing backlog delay elevated ({backlog_metrics['oldest_event_age_seconds']}s)."
            )

        # 5. Determine Overall Status
        if freshness_status == "CRITICAL" or open_count >= 3:
            overall_status = "UNHEALTHY"
        elif freshness_status == "WARNING" or open_count > 0 or not backlog_metrics["is_healthy"]:
            overall_status = "DEGRADED"
        else:
            overall_status = "HEALTHY"

        return PlatformReliabilityStatusResponse(
            overall_status=overall_status,
            last_backup_at=last_backup.started_at if last_backup else None,
            last_successful_backup_at=last_success.completed_at if last_success else None,
            last_restore_verification_at=last_restore.started_at if last_restore else None,
            last_restore_verification_status=last_restore.status if last_restore else None,
            backup_freshness_status=freshness_status,
            backup_age_hours=backup_age_hours,
            outbox_pending_count=backlog_metrics["pending_count"],
            outbox_processing_count=backlog_metrics["processing_count"],
            outbox_dead_letter_count=backlog_metrics["dead_letter_count"],
            outbox_oldest_event_age_seconds=backlog_metrics["oldest_event_age_seconds"],
            outbox_queue_healthy=backlog_metrics["is_healthy"],
            open_circuit_breakers_count=open_count,
            circuit_breakers=cb_responses,
            degraded_services=degraded_services,
        )
