"""Platform Reliability & Disaster Recovery REST APIs (Step 31).

Restricted exclusively to Platform Administrators and authorized Platform Operators.
Provides endpoints for:
1. Reliability Objectives (RTO/RPO targets, backup schedules, queue delay thresholds)
2. Platform DR & Health Readiness Status Summary
3. Database Backup Triggering, Listing, and Safe Pruning
4. Sandbox Restore Verification Execution and History
5. Downstream Dependency Circuit Breaker Inspection and Manual Reset
6. Abandoned Outbox Processing Recovery
7. Object Storage and Document Integrity Auditing
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import require_platform_permission
from app.core.events import OutboxService
from app.core.permissions import (
    PLATFORM_BACKUP_TRIGGER,
    PLATFORM_RELIABILITY_MANAGE,
    PLATFORM_RELIABILITY_READ,
    PLATFORM_RESTORE_VERIFY,
)
from app.core.reliability_config import get_reliability_objectives
from app.core.resilience import circuit_registry
from app.models.people import User
from app.models.reliability import (
    PlatformBackupRecord,
    PlatformRestoreVerification,
)
from app.schemas.reliability import (
    BackupCreateRequest,
    BackupPruneResponse,
    BackupRecordResponse,
    CircuitBreakerResetRequest,
    CircuitBreakerResponse,
    OutboxBacklogRecoveryResponse,
    PlatformReliabilityStatusResponse,
    ReliabilityObjectivesResponse,
    RestoreVerificationRequest,
    RestoreVerificationResponse,
    StorageAuditResponse,
)
from app.services.backup_service import BackupService
from app.services.reliability_orchestration_service import (
    ReliabilityOrchestrationService,
)
from app.services.restore_verification_service import RestoreVerificationService
from app.services.storage_recovery_service import StorageRecoveryService

router = APIRouter(prefix="/platform/reliability", tags=["Platform Reliability & Disaster Recovery"])


# =============================================================================
# 1. RELIABILITY OBJECTIVES & RECOVERY TARGETS
# =============================================================================


@router.get("/objectives", response_model=ReliabilityObjectivesResponse)
async def get_objectives(
    _operator: Annotated[User, Depends(require_platform_permission(PLATFORM_RELIABILITY_READ))],
) -> ReliabilityObjectivesResponse:
    """Return platform reliability objectives, RTO/RPO targets, and service criticality tiers."""
    return get_reliability_objectives()


# =============================================================================
# 2. DISASTER RECOVERY READINESS & STATUS SUMMARY
# =============================================================================


@router.get("/status", response_model=PlatformReliabilityStatusResponse)
async def get_reliability_status(
    _operator: Annotated[User, Depends(require_platform_permission(PLATFORM_RELIABILITY_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> PlatformReliabilityStatusResponse:
    """Holistic summary of platform disaster recovery posture, backups, backlog, and degraded modes."""
    return await ReliabilityOrchestrationService.get_reliability_status(db)


# =============================================================================
# 3. DATABASE BACKUPS & RETENTION PRUNING
# =============================================================================


@router.get("/backups", response_model=list[BackupRecordResponse])
async def list_backups(
    _operator: Annotated[User, Depends(require_platform_permission(PLATFORM_RELIABILITY_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[BackupRecordResponse]:
    """List historical database backups with status and verification badges."""
    stmt = select(PlatformBackupRecord).order_by(desc(PlatformBackupRecord.started_at))
    if status_filter:
        stmt = stmt.where(PlatformBackupRecord.status == status_filter.upper())
    stmt = stmt.offset(offset).limit(limit)

    res = await db.execute(stmt)
    records = list(res.scalars().all())
    return [BackupRecordResponse.model_validate(r) for r in records]


@router.post("/backups", response_model=BackupRecordResponse, status_code=status.HTTP_201_CREATED)
async def trigger_backup(
    req: BackupCreateRequest,
    operator: Annotated[User, Depends(require_platform_permission(PLATFORM_BACKUP_TRIGGER))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> BackupRecordResponse:
    """Trigger an on-demand PostgreSQL backup with concurrency lock and SHA-256 checksum."""
    record = await BackupService.create_backup(
        db=db,
        backup_type=req.backup_type,
        retention_days=req.retention_days,
        triggered_by_user_id=operator.id,
    )
    return BackupRecordResponse.model_validate(record)


@router.post("/backups/prune", response_model=BackupPruneResponse)
async def prune_backups(
    operator: Annotated[User, Depends(require_platform_permission(PLATFORM_BACKUP_TRIGGER))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    retention_days: int = Query(30, ge=1, le=365),
) -> BackupPruneResponse:
    """Prune expired backups while strictly protecting the last known-good backup."""
    return await BackupService.prune_expired_backups(
        db=db,
        retention_days=retention_days,
        actor_id=operator.id,
    )


# =============================================================================
# 4. RESTORE VERIFICATION IN DISPOSABLE SANDBOX
# =============================================================================


@router.get("/restore-verifications", response_model=list[RestoreVerificationResponse])
async def list_restore_verifications(
    _operator: Annotated[User, Depends(require_platform_permission(PLATFORM_RELIABILITY_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[RestoreVerificationResponse]:
    """List historical restore verification test executions."""
    stmt = (
        select(PlatformRestoreVerification)
        .order_by(desc(PlatformRestoreVerification.started_at))
        .offset(offset)
        .limit(limit)
    )
    res = await db.execute(stmt)
    records = list(res.scalars().all())
    return [RestoreVerificationResponse.model_validate(r) for r in records]


@router.post("/restore-verifications", response_model=RestoreVerificationResponse, status_code=status.HTTP_201_CREATED)
async def trigger_restore_verification(
    req: RestoreVerificationRequest,
    operator: Annotated[User, Depends(require_platform_permission(PLATFORM_RESTORE_VERIFY))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> RestoreVerificationResponse:
    """Execute a restore verification test in an isolated disposable sandbox database."""
    res = await RestoreVerificationService.verify_backup(
        db=db,
        backup_record_id=req.backup_record_id,
        sandbox_database_name=req.sandbox_database_name,
        tested_by_user_id=operator.id,
    )
    return RestoreVerificationResponse.model_validate(res)


# =============================================================================
# 5. CIRCUIT BREAKERS & DEPENDENCY RESILIENCE
# =============================================================================


@router.get("/circuit-breakers", response_model=list[CircuitBreakerResponse])
async def list_circuit_breakers(
    _operator: Annotated[User, Depends(require_platform_permission(PLATFORM_RELIABILITY_READ))],
) -> list[CircuitBreakerResponse]:
    """Inspect state, failure counters, and trip history of downstream dependency circuit breakers."""
    all_breakers = circuit_registry.get_all()
    return [CircuitBreakerResponse(**b.to_dict()) for b in all_breakers]


@router.post("/circuit-breakers/{dependency_name}/reset", response_model=CircuitBreakerResponse)
async def reset_circuit_breaker(
    dependency_name: str,
    _req: CircuitBreakerResetRequest,
    _operator: Annotated[User, Depends(require_platform_permission(PLATFORM_RELIABILITY_MANAGE))],
) -> CircuitBreakerResponse:
    """Manually reset a tripped circuit breaker to healthy CLOSED state."""
    breaker = circuit_registry.get_or_create(dependency_name)
    await breaker.reset()
    return CircuitBreakerResponse(**breaker.to_dict())


# =============================================================================
# 6. ABANDONED WORKER & OUTBOX EVENT RECOVERY
# =============================================================================


@router.post("/outbox/recover-abandoned", response_model=OutboxBacklogRecoveryResponse)
async def recover_abandoned_outbox_events(
    _operator: Annotated[User, Depends(require_platform_permission(PLATFORM_RELIABILITY_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    stuck_threshold_seconds: int = Query(300, ge=60, le=3600),
) -> OutboxBacklogRecoveryResponse:
    """Recover outbox domain events stuck in PROCESSING due to worker restarts or terminations."""
    res = await OutboxService.recover_abandoned_events(
        db=db, stuck_threshold_seconds=stuck_threshold_seconds
    )
    return OutboxBacklogRecoveryResponse(
        recovered_count=res["recovered_count"],
        stuck_threshold_seconds=stuck_threshold_seconds,
        dead_lettered_count=res["dead_lettered_count"],
        message=f"Recovered {res['recovered_count']} abandoned events; {res['dead_lettered_count']} routed to dead letter.",
    )


# =============================================================================
# 7. DOCUMENT STORAGE & OBJECT INTEGRITY AUDIT
# =============================================================================


@router.post("/storage/audit", response_model=StorageAuditResponse)
async def trigger_storage_audit(
    operator: Annotated[User, Depends(require_platform_permission(PLATFORM_RELIABILITY_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> StorageAuditResponse:
    """Scan document database records vs physical storage to identify missing and orphaned files."""
    audit_record = await StorageRecoveryService.audit_storage_integrity(
        db=db, user_id=operator.id
    )
    return StorageAuditResponse.model_validate(audit_record)
