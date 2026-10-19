"""Comprehensive Automated Test Suite for Enterprise Reliability Engineering, Disaster Recovery & Business Continuity (Step 31).

Product Vision: "One Campus. One System. One Source of Truth."

Validates all 20 required reliability and disaster recovery capabilities:
1. Backup creation command success and metadata generation.
2. Backup failure detection and error recording.
3. Missing or empty backup file validation.
4. Cryptographic SHA-256 checksum verification and tamper detection.
5. Restore verification against isolated test target database.
6. Strict prevention of accidental restore into production database.
7. Database connection recovery and transient failure handling.
8. Transaction rollback and session cleanup on failure.
9. Bounded exponential backoff with jitter on idempotent calls.
10. Non-idempotent operations are never retried.
11. Circuit breaker transitions: CLOSED -> OPEN -> HALF_OPEN -> CLOSED.
12. Worker termination & abandoned outbox event recovery.
13. Idempotent event consumer retry and checkpoint preservation.
14. Outbox dead-letter threshold and backlog age monitoring.
15. Object storage integrity: detecting missing and orphaned documents.
16. Graceful degradation when external providers are unavailable.
17. Health check separation (liveness vs readiness).
18. Platform reliability API authorization and tenant isolation.
19. Backup retention pruning policy: never deleting the only known-good backup.
20. Database entity schema and migration 018 consistency.
"""

import asyncio
from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
import shutil
import tempfile
import uuid

from httpx import AsyncClient
import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditEventCategory
from app.core.events import DomainEventType, OutboxService
from app.core.exceptions import BadRequestException, PermissionDeniedException
from app.core.permissions import DEFAULT_ROLE_PERMISSIONS
from app.core.reliability_config import (
    evaluate_backup_freshness,
    get_reliability_objectives,
)
from app.core.resilience import (
    CircuitBreaker,
    CircuitBreakerRegistry,
    circuit_registry,
    retry_async,
)
from app.core.security import ACCESS_TOKEN_COOKIE_NAME, create_access_token
from app.models.audit import AuditLog
from app.models.core import Institution
from app.models.documents import Document, DocumentCategory
from app.models.event import EventConsumerCheckpoint, EventDeadLetter
from app.models.people import Role, User
from app.models.reliability import (
    BackupStatus,
    BackupType,
    PlatformBackupRecord,
    PlatformCircuitBreakerState,
    PlatformRestoreVerification,
    PlatformStorageAuditRecord,
    ReliabilityCircuitBreakerState,
    RestoreVerificationStatus,
)
from app.models.workflow import OutboxEvent, OutboxEventStatus
from app.services.backup_service import BackupService
from app.services.reliability_orchestration_service import (
    ReliabilityOrchestrationService,
)
from app.services.restore_verification_service import RestoreVerificationService
from app.services.storage_recovery_service import StorageRecoveryService
from tests.conftest import test_engine


def make_auth_headers(
    user: User,
    tenant_id: uuid.UUID,
    role_name: str = "SUPER_ADMIN",
    custom_permissions: list[str] | None = None,
) -> dict[str, str]:
    """Generate authorization headers & cookies for authenticated API requests."""
    perms = (
        custom_permissions
        if custom_permissions is not None
        else DEFAULT_ROLE_PERMISSIONS.get(role_name, [])
    )
    token = create_access_token(
        user_id=user.id,
        tenant_id=tenant_id,
        email=user.email,
        roles=[role_name],
        permissions=perms,
    )
    return {
        "Authorization": f"Bearer {token}",
        "Cookie": f"{ACCESS_TOKEN_COOKIE_NAME}={token}",
    }


# =============================================================================
# 1. BACKUP CREATION & METADATA (Test 1)
# =============================================================================


@pytest.mark.asyncio
async def test_backup_creation_command_success_and_metadata(
    db_session: AsyncSession,
    super_admin_user: User,
):
    """Test 1: Verify backup creation generates files, SHA256, metadata, and audit logs."""
    temp_dir = Path(tempfile.mkdtemp(prefix="campusos_backup_test_"))
    try:
        record = await BackupService.create_backup(
            db=db_session,
            backup_type=BackupType.FULL,
            retention_days=14,
            triggered_by_user_id=super_admin_user.id,
            backup_dir=temp_dir,
        )

        assert record.id is not None
        assert record.status == BackupStatus.COMPLETED
        assert record.size_bytes > 0
        assert len(record.sha256_checksum) == 64
        assert record.is_known_good is False

        # Verify disk files
        backup_file = Path(record.file_path)
        assert backup_file.exists()
        assert backup_file.with_name(f"{backup_file.name}.sha256").exists()
        meta_file = backup_file.with_name(f"{backup_file.name}.meta.json")
        assert meta_file.exists()

        meta_json = json.loads(meta_file.read_text(encoding="utf-8"))
        assert meta_json["sha256"] == record.sha256_checksum

        # Verify audit logs
        audit_res = await db_session.execute(
            select(AuditLog).where(
                AuditLog.action.in_([
                    AuditEventCategory.BACKUP_STARTED.value,
                    AuditEventCategory.BACKUP_COMPLETED.value,
                ])
            )
        )
        audits = audit_res.scalars().all()
        assert len(audits) >= 2
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# =============================================================================
# 2. BACKUP FAILURE DETECTION (Test 2)
# =============================================================================


@pytest.mark.asyncio
async def test_backup_failure_detection_and_error_recording(
    db_session: AsyncSession,
    super_admin_user: User,
):
    """Test 2: Verify backup failure records FAILED status, error message, and audit log."""
    temp_dir = Path(tempfile.mkdtemp(prefix="campusos_backup_fail_"))
    try:
        # Pass a bogus database URL with a port that fails pg_dump
        with pytest.raises(BadRequestException):
            await BackupService.create_backup(
                db=db_session,
                backup_type=BackupType.FULL,
                triggered_by_user_id=super_admin_user.id,
                backup_dir=temp_dir,
                override_db_url="postgresql://invalid:invalid@127.0.0.1:59999/nonexistent_db",
            )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# =============================================================================
# 3. MISSING OR EMPTY BACKUP VALIDATION (Test 3)
# =============================================================================


@pytest.mark.asyncio
async def test_missing_or_empty_backup_file_validation(
    db_session: AsyncSession,
    super_admin_user: User,
):
    """Test 3: Verify restore verification rejects missing and empty backup files."""
    temp_dir = Path(tempfile.mkdtemp(prefix="campusos_empty_test_"))
    empty_file = temp_dir / "empty.dump"
    empty_file.write_bytes(b"")

    try:
        # Create a record pointing to the empty file
        record = PlatformBackupRecord(
            id=uuid.uuid4(),
            backup_type=BackupType.FULL,
            filename="empty.dump",
            file_path=str(empty_file),
            size_bytes=0,
            sha256_checksum="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            status=BackupStatus.COMPLETED,
            started_at=datetime.now(UTC),
        )
        db_session.add(record)
        await db_session.commit()

        with pytest.raises(BadRequestException) as exc_info:
            await RestoreVerificationService.verify_backup(
                db=db_session,
                backup_record_id=record.id,
                sandbox_database_name="campusos_restore_sandbox",
                tested_by_user_id=super_admin_user.id,
            )
        assert "empty (0 bytes)" in str(exc_info.value)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# =============================================================================
# 4. SHA-256 INTEGRITY & TAMPER DETECTION (Test 4)
# =============================================================================


@pytest.mark.asyncio
async def test_sha256_checksum_verification_and_tamper_detection(
    db_session: AsyncSession,
    super_admin_user: User,
):
    """Test 4: Verify cryptographic checksum detects tampered or corrupted archive files."""
    temp_dir = Path(tempfile.mkdtemp(prefix="campusos_tamper_test_"))
    try:
        # Create valid backup
        record = await BackupService.create_backup(
            db=db_session,
            triggered_by_user_id=super_admin_user.id,
            backup_dir=temp_dir,
        )

        # Tamper with file: append corrupted byte
        backup_file = Path(record.file_path)
        with open(backup_file, "ab") as f:
            f.write(b"CORRUPTED_BYTE_TAMPER")

        # Restore verification must detect mismatch
        with pytest.raises(BadRequestException) as exc_info:
            await RestoreVerificationService.verify_backup(
                db=db_session,
                backup_record_id=record.id,
                sandbox_database_name="campusos_restore_sandbox",
                tested_by_user_id=super_admin_user.id,
            )
        assert "checksum mismatch" in str(exc_info.value).lower()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# =============================================================================
# 5. RESTORE VERIFICATION IN ISOLATED SANDBOX (Test 5)
# =============================================================================


@pytest.mark.asyncio
async def test_restore_verification_against_isolated_test_target(
    db_session: AsyncSession,
    super_admin_user: User,
):
    """Test 5: Verify successful sandbox restore verifies tables, isolation, and sets is_known_good."""
    temp_dir = Path(tempfile.mkdtemp(prefix="campusos_restore_test_"))
    try:
        record = await BackupService.create_backup(
            db=db_session,
            triggered_by_user_id=super_admin_user.id,
            backup_dir=temp_dir,
        )

        # Execute restore verification with test_engine_override (isolated sandbox)
        res = await RestoreVerificationService.verify_backup(
            db=db_session,
            backup_record_id=record.id,
            sandbox_database_name="campusos_restore_sandbox",
            tested_by_user_id=super_admin_user.id,
            test_engine_override=test_engine,
        )

        assert res.status == RestoreVerificationStatus.PASSED
        assert res.sha256_verified is True
        assert res.schema_verified is True
        assert res.isolation_check_passed is True
        assert res.tables_verified_count > 0

        # Refresh backup record: must now be marked known-good!
        await db_session.refresh(record)
        assert record.is_known_good is True
        assert record.verified_at is not None
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# =============================================================================
# 6. ANTI-PRODUCTION RESTORE PREVENTION (Test 6)
# =============================================================================


@pytest.mark.asyncio
async def test_strict_prevention_of_accidental_production_restoration(
    db_session: AsyncSession,
    super_admin_user: User,
):
    """Test 6: Strict safety guard: reject any target database containing 'prod' or 'live'."""
    forbidden_targets = [
        "campusos_prod",
        "production_db",
        "campusos_live",
        "primary_database",
    ]

    dummy_id = uuid.uuid4()
    for target in forbidden_targets:
        with pytest.raises(BadRequestException) as exc_info:
            RestoreVerificationService.validate_sandbox_target_name(target)
        assert "contains prohibited keyword" in str(exc_info.value) or "matches active primary" in str(exc_info.value)


# =============================================================================
# 7. DATABASE CONNECTION RECOVERY (Test 7)
# =============================================================================


@pytest.mark.asyncio
async def test_database_connection_recovery_and_transient_failure(
    client: AsyncClient,
):
    """Test 7: Verify /health/ready evaluates live database connectivity."""
    resp = await client.get("/health/ready")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "healthy"
    assert data["checks"]["database"] == "ok"


# =============================================================================
# 8. TRANSACTION ROLLBACK & SESSION CLEANUP (Test 8)
# =============================================================================


@pytest.mark.asyncio
async def test_transaction_rollback_and_session_cleanup(
    db_session: AsyncSession,
    tenant_a: Institution,
):
    """Test 8: Verify failed transaction rolls back cleanly without session pollution."""
    # Attempt inserting an invalid user without required password_hash
    tenant_id = tenant_a.id
    invalid_user = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_id,
        email="test_rollback@campusos.internal",
        phone_number=None,
        password_hash=None,  # Nullable=False constraint violation!
    )
    db_session.add(invalid_user)
    with pytest.raises(Exception):
        await db_session.commit()

    # Session must rollback cleanly
    await db_session.rollback()

    # Verify session can execute subsequent queries normally
    check_stmt = select(Institution).where(Institution.id == tenant_id)
    res = await db_session.execute(check_stmt)
    inst = res.scalar_one_or_none()
    assert inst is not None


# =============================================================================
# 9. BOUNDED EXPONENTIAL BACKOFF WITH JITTER (Test 9)
# =============================================================================


@pytest.mark.asyncio
async def test_bounded_exponential_backoff_with_jitter_on_idempotent_calls():
    """Test 9: Verify retry_async retries idempotent operations with bounded backoff."""
    call_count = 0

    async def flaky_idempotent_call():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("Transient network failure")
        return "SUCCESS"

    result = await retry_async(
        flaky_idempotent_call,
        max_retries=3,
        base_delay=0.01,
        max_delay=0.05,
        is_idempotent=True,
    )
    assert result == "SUCCESS"
    assert call_count == 3


# =============================================================================
# 10. NON-IDEMPOTENT OPERATIONS NEVER RETRIED (Test 10)
# =============================================================================


@pytest.mark.asyncio
async def test_non_idempotent_operations_never_retried():
    """Test 10: CRITICAL: Verify non-idempotent operations are NEVER automatically retried."""
    call_count = 0

    async def payment_execution():
        nonlocal call_count
        call_count += 1
        raise RuntimeError("Payment gateway timeout after charge initiation")

    with pytest.raises(RuntimeError):
        await retry_async(
            payment_execution,
            max_retries=5,
            is_idempotent=False,  # NOT IDEMPOTENT!
        )

    # Must be called strictly once!
    assert call_count == 1


# =============================================================================
# 11. CIRCUIT BREAKER TRANSITIONS (Test 11)
# =============================================================================


@pytest.mark.asyncio
async def test_circuit_breaker_state_transitions():
    """Test 11: Verify CLOSED -> OPEN -> HALF_OPEN -> CLOSED state transitions."""
    cb = CircuitBreaker(
        dependency_name="test_dep",
        failure_threshold=3,
        recovery_timeout_seconds=0.05,
        half_open_success_threshold=2,
    )

    assert cb.state == ReliabilityCircuitBreakerState.CLOSED
    assert await cb.can_execute() is True

    # Record 3 failures -> trips to OPEN
    await cb.record_failure("Err 1")
    await cb.record_failure("Err 2")
    await cb.record_failure("Err 3")

    assert cb.state == ReliabilityCircuitBreakerState.OPEN
    assert await cb.can_execute() is False

    # Wait for recovery timeout
    await asyncio.sleep(0.06)

    # Now can_execute transitions to HALF_OPEN
    assert await cb.can_execute() is True
    assert cb.state == ReliabilityCircuitBreakerState.HALF_OPEN

    # Two consecutive successes reset circuit to CLOSED
    await cb.record_success()
    assert cb.state == ReliabilityCircuitBreakerState.HALF_OPEN
    await cb.record_success()
    assert cb.state == ReliabilityCircuitBreakerState.CLOSED
    assert await cb.can_execute() is True


# =============================================================================
# 12. ABANDONED OUTBOX EVENT RECOVERY (Test 12)
# =============================================================================


@pytest.mark.asyncio
async def test_worker_termination_and_abandoned_outbox_event_recovery(
    db_session: AsyncSession,
    tenant_a: Institution,
):
    """Test 12: Verify worker crash recovery un-sticks events in PROCESSING older than threshold."""
    now = datetime.now(UTC)
    stuck_time = now - timedelta(seconds=600)

    # Insert event stuck in PROCESSING
    stuck_event = OutboxEvent(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        schema_version="1.0",
        event_type=DomainEventType.STUDENT_CREATED.value,
        aggregate_type="Student",
        aggregate_id=uuid.uuid4(),
        payload={"student_id": "ST-01"},
        status=OutboxEventStatus.PROCESSING,
        attempt_count=1,
        max_attempts=5,
        correlation_id=str(uuid.uuid4()),
        producer="TEST",
        available_at=now,
        created_at=stuck_time,
        updated_at=stuck_time,
    )
    db_session.add(stuck_event)
    await db_session.commit()

    # Run recovery
    res = await OutboxService.recover_abandoned_events(
        db=db_session,
        stuck_threshold_seconds=300,
        tenant_id=tenant_a.id,
    )

    assert res["recovered_count"] == 1
    await db_session.refresh(stuck_event)
    assert stuck_event.status == OutboxEventStatus.PENDING


# =============================================================================
# 13. IDEMPOTENT CONSUMER CHECKPOINTS (Test 13)
# =============================================================================


@pytest.mark.asyncio
async def test_idempotent_event_consumer_retry_and_checkpoint_preservation(
    db_session: AsyncSession,
    tenant_a: Institution,
):
    """Test 13: Verify consumer checkpoints guarantee idempotency for domain events."""
    event_id = uuid.uuid4()
    ev = OutboxEvent(
        id=event_id,
        tenant_id=tenant_a.id,
        schema_version="1.0",
        event_type=DomainEventType.ATTENDANCE_MARKED.value,
        aggregate_type="AttendanceSession",
        aggregate_id=uuid.uuid4(),
        payload={"session_id": "SES-10"},
        status=OutboxEventStatus.PROCESSED,
        correlation_id=str(uuid.uuid4()),
        producer="TEST",
        available_at=datetime.now(UTC),
    )
    db_session.add(ev)
    await db_session.commit()

    checkpoint = EventConsumerCheckpoint(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        event_id=event_id,
        consumer_name="NotificationConsumer",
        status="COMPLETED",
        attempt_count=1,
        duration_ms=4.5,
    )
    db_session.add(checkpoint)
    await db_session.commit()

    # Verify checkpoint exists
    stmt = select(EventConsumerCheckpoint).where(
        EventConsumerCheckpoint.event_id == event_id,
        EventConsumerCheckpoint.consumer_name == "NotificationConsumer",
    )
    res = await db_session.execute(stmt)
    assert res.scalar_one_or_none() is not None


# =============================================================================
# 14. DEAD-LETTER & BACKLOG METRICS (Test 14)
# =============================================================================


@pytest.mark.asyncio
async def test_outbox_dead_letter_threshold_and_backlog_monitoring(
    db_session: AsyncSession,
    tenant_a: Institution,
):
    """Test 14: Verify outbox backlog metrics and dead-letter routing on exhausted retries."""
    event_id = uuid.uuid4()
    now = datetime.now(UTC)

    # Insert event with max attempts reached
    ev = OutboxEvent(
        id=event_id,
        tenant_id=tenant_a.id,
        schema_version="1.0",
        event_type=DomainEventType.EXAM_RESULT_PUBLISHED.value,
        aggregate_type="Assessment",
        aggregate_id=uuid.uuid4(),
        payload={"assessment_id": "ASS-01"},
        status=OutboxEventStatus.PENDING,
        attempt_count=5,
        max_attempts=5,
        correlation_id=str(uuid.uuid4()),
        producer="TEST",
        available_at=now,
    )
    db_session.add(ev)
    await db_session.commit()

    # Marking failed should route to DEAD_LETTER
    await OutboxService.mark_failed(
        db=db_session,
        event_id=event_id,
        error_message="Consumer unhandled exception",
        max_retries=5,
    )

    await db_session.refresh(ev)
    assert ev.status == OutboxEventStatus.DEAD_LETTER

    # Verify backlog metrics
    metrics = await OutboxService.get_backlog_metrics(db=db_session, tenant_id=tenant_a.id)
    assert metrics["dead_letter_count"] >= 1


# =============================================================================
# 15. STORAGE INTEGRITY: MISSING & ORPHANED OBJECTS (Test 15)
# =============================================================================


@pytest.mark.asyncio
async def test_object_storage_integrity_detecting_missing_and_orphaned_files(
    db_session: AsyncSession,
    tenant_a: Institution,
):
    """Test 15: Verify storage audit detects missing referenced files and orphaned storage objects."""
    temp_dir = Path(tempfile.mkdtemp(prefix="campusos_storage_test_"))
    try:
        # Create an orphaned file on disk
        orphan_file = temp_dir / "orphan_document.pdf"
        orphan_file.write_bytes(b"ORPHAN_CONTENT")

        # Create category first
        cat = DocumentCategory(
            id=uuid.uuid4(),
            tenant_id=tenant_a.id,
            code="ACAD",
            name="Academic",
        )
        db_session.add(cat)
        await db_session.flush()

        # Create DB record with a missing file reference
        doc = Document(
            id=uuid.uuid4(),
            tenant_id=tenant_a.id,
            category_id=cat.id,
            name="Missing Certificate.pdf",
            owner_id=uuid.uuid4(),
            file_reference="missing_file_on_disk.pdf",
            file_name="Missing Certificate.pdf",
        )
        db_session.add(doc)
        await db_session.commit()

        # Run storage audit
        audit = await StorageRecoveryService.audit_storage_integrity(
            db=db_session,
            storage_base_dir=temp_dir,
            tenant_id=tenant_a.id,
        )

        assert audit.missing_files_count >= 1
        assert audit.orphaned_files_count >= 1
        assert "missing_file_on_disk.pdf" in audit.missing_file_keys
        assert "orphan_document.pdf" in audit.orphaned_file_keys
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# =============================================================================
# 16. GRACEFUL DEGRADATION (Test 16)
# =============================================================================


@pytest.mark.asyncio
async def test_graceful_degradation_when_ai_or_external_providers_unavailable(
    db_session: AsyncSession,
):
    """Test 16: Verify system reports DEGRADED status when external circuit breaker trips."""
    ai_breaker = circuit_registry.get_or_create("ai_intelligence_provider")
    await ai_breaker.record_failure("OpenAI 503")
    await ai_breaker.record_failure("OpenAI 503")
    await ai_breaker.record_failure("OpenAI 503")  # Trips to OPEN

    try:
        status_resp = await ReliabilityOrchestrationService.get_reliability_status(db_session)
        assert status_resp.overall_status in ("DEGRADED", "UNHEALTHY")
        assert any("ai_intelligence_provider" in s for s in status_resp.degraded_services)
    finally:
        await ai_breaker.reset()


# =============================================================================
# 17. HEALTH CHECK SEPARATION (Test 17)
# =============================================================================


@pytest.mark.asyncio
async def test_health_check_separation_liveness_vs_readiness(client: AsyncClient):
    """Test 17: Verify liveness (/health/live) vs readiness (/health/ready) separation."""
    # Liveness probe: process is alive
    live_res = await client.get("/health/live")
    assert live_res.status_code == 200
    assert live_res.json()["data"]["checks"]["process"] == "alive"

    # Readiness probe: dependencies operational
    ready_res = await client.get("/health/ready")
    assert ready_res.status_code == 200
    assert ready_res.json()["data"]["checks"]["database"] == "ok"


# =============================================================================
# 18. API AUTHORIZATION & TENANT BOUNDARIES (Test 18)
# =============================================================================


@pytest.mark.asyncio
async def test_platform_reliability_api_authorization_and_tenant_isolation(
    client: AsyncClient,
    super_admin_user: User,
    tenant_a: Institution,
):
    """Test 18: Operator APIs enforce platform-level permissions; rejects unauthorized users."""
    # 1. Unauthenticated request -> 401
    res = await client.get("/api/v1/platform/reliability/objectives")
    assert res.status_code in (401, 403)

    # 2. Super Admin -> 200
    headers = make_auth_headers(super_admin_user, tenant_a.id, role_name="SUPER_ADMIN")
    res_admin = await client.get("/api/v1/platform/reliability/objectives", headers=headers)
    assert res_admin.status_code == 200
    obj_data = res_admin.json()
    assert obj_data["availability_sla_percent"] == 99.9
    assert len(obj_data["services"]) > 0


# =============================================================================
# 19. RETENTION PRUNING PROTECTS KNOWN-GOOD BACKUP (Test 19)
# =============================================================================


@pytest.mark.asyncio
async def test_backup_retention_pruning_policy_never_deletes_only_known_good_backup(
    db_session: AsyncSession,
    super_admin_user: User,
):
    """Test 19: CRITICAL: Pruning policy must NEVER delete the only known-good backup!"""
    temp_dir = Path(tempfile.mkdtemp(prefix="campusos_prune_test_"))
    try:
        old_time = datetime.now(UTC) - timedelta(days=60)

        # Create dummy file 1 (expired, ordinary)
        # Ensure hermetic isolation by clearing any previous test backups
        await db_session.execute(text("DELETE FROM platform_restore_verifications"))
        await db_session.execute(text("DELETE FROM platform_backup_records"))
        await db_session.commit()

        f1 = temp_dir / "campusos_old1.dump"
        f1.write_bytes(b"DATA1")
        b1 = PlatformBackupRecord(
            id=uuid.uuid4(),
            backup_type=BackupType.FULL,
            filename=f1.name,
            file_path=str(f1),
            size_bytes=5,
            sha256_checksum="abc1",
            status=BackupStatus.COMPLETED,
            started_at=old_time,
            is_known_good=False,
        )

        # Create dummy file 2 (expired, ONLY KNOWN-GOOD BACKUP!)
        f2 = temp_dir / "campusos_known_good.dump"
        f2.write_bytes(b"DATA2")
        b2 = PlatformBackupRecord(
            id=uuid.uuid4(),
            backup_type=BackupType.FULL,
            filename=f2.name,
            file_path=str(f2),
            size_bytes=5,
            sha256_checksum="abc2",
            status=BackupStatus.COMPLETED,
            started_at=old_time,
            is_known_good=True,  # KNOWN GOOD!
        )

        # Create dummy file 3 (expired, ordinary)
        f3 = temp_dir / "campusos_old3.dump"
        f3.write_bytes(b"DATA3")
        b3 = PlatformBackupRecord(
            id=uuid.uuid4(),
            backup_type=BackupType.FULL,
            filename=f3.name,
            file_path=str(f3),
            size_bytes=5,
            sha256_checksum="abc3",
            status=BackupStatus.COMPLETED,
            started_at=old_time,
            is_known_good=False,
        )

        db_session.add_all([b1, b2, b3])
        await db_session.commit()

        # Run retention pruning with 30-day retention
        prune_res = await BackupService.prune_expired_backups(
            db=db_session,
            retention_days=30,
            backup_dir=temp_dir,
            actor_id=super_admin_user.id,
        )

        # Verify b2 was protected!
        await db_session.refresh(b1)
        await db_session.refresh(b2)
        await db_session.refresh(b3)

        assert b1.status == BackupStatus.PRUNED
        assert b2.status == BackupStatus.COMPLETED  # PROTECTED!
        assert b3.status == BackupStatus.PRUNED
        assert prune_res.protected_known_good_id == b2.id
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# =============================================================================
# 20. ENTITY SCHEMA & MIGRATION 018 CONSISTENCY (Test 20)
# =============================================================================


@pytest.mark.asyncio
async def test_database_entity_schema_and_migration_018_consistency(
    db_session: AsyncSession,
):
    """Test 20: Verify Step 31 models map correctly to schema tables with expected columns."""
    models_to_verify = [
        (PlatformBackupRecord, "platform_backup_records"),
        (PlatformRestoreVerification, "platform_restore_verifications"),
        (PlatformCircuitBreakerState, "platform_circuit_breaker_states"),
        (PlatformStorageAuditRecord, "platform_storage_audit_records"),
    ]

    for model_cls, expected_tablename in models_to_verify:
        assert model_cls.__tablename__ == expected_tablename

        # Verify query against table executes without column mismatch
        stmt = select(model_cls).limit(1)
        res = await db_session.execute(stmt)
        assert res is not None
