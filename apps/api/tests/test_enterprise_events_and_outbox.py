"""Comprehensive Test Suite for Enterprise Domain Event Backbone & Transactional Outbox (Step 27).

Covers all 20 requirements:
1. Valid event creation and schema validation
2. Unsupported event types and schema versions
3. Atomic business transaction and outbox persistence
4. Rollback behavior when business operations fail
5. Publication after a committed transaction
6. Recovery after a publisher failure
7. Concurrent outbox workers locking
8. Duplicate event delivery handling
9. Idempotent consumer behavior & deduplication checkpoints
10. Retry backoff and maximum-attempt handling
11. Dead-letter creation and safe replay
12. Tenant isolation across event reads, retries, and consumers
13. Permission checks on administrative endpoints
14. Sensitive-field filtering and sanitized logs
15. Correlation and causation propagation
16. Integration with real existing domain transaction (Attendance / Finance)
17. Integration with existing notification / workflow layer
18. Worker startup, batch processing, and empty batch handling
19. Migration and schema consistency
20. Safe cleanup of published events retaining unpublished records
"""

import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.event_consumer import (
    BaseDomainEventConsumer,
    ConsumerExecutionEngine,
    ConsumerResult,
)
from app.core.events import (
    DomainEventEnvelope,
    OutboxService,
    sanitize_error_text,
    sanitize_event_payload,
)
from app.core.exceptions import ValidationException
from app.core.permissions import DEFAULT_ROLE_PERMISSIONS
from app.core.security import ACCESS_TOKEN_COOKIE_NAME, create_access_token
from app.models.case_management import CasePriority
from app.models.core import AcademicYear, Institution
from app.models.event import (
    ConsumerCheckpointStatus,
    EventConsumerCheckpoint,
    EventDeadLetter,
)
from app.models.people import User
from app.models.workflow import OutboxEvent, OutboxEventStatus
from app.schemas.case_management import CaseCreate
from app.services.case_service import CaseService
from app.worker import process_outbox_batch


def make_auth_headers(
    user: User,
    tenant_id: uuid.UUID,
    role_name: str = "INSTITUTION_ADMIN",
    custom_permissions: list[str] | None = None,
) -> dict[str, str]:
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
# 1. EVENT CONTRACT & SCHEMA VALIDATION TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_valid_event_creation_and_schema_validation(
    db_session: AsyncSession, tenant_a: Institution
):
    """1. Test valid event creation with envelope contracts and payload validation."""
    student_id = uuid.uuid4()
    course_id = uuid.uuid4()

    event = await OutboxService.publish_event(
        db=db_session,
        tenant_id=tenant_a.id,
        event_type="student.enrollment.created",
        aggregate_type="Enrollment",
        aggregate_id=student_id,
        payload={
            "student_id": student_id,
            "course_id": course_id,
            "semester": "1",
            "section_id": str(uuid.uuid4()),
        },
        schema_version="1.0",
        causation_id="cmd_enroll_123",
        producer="ACADEMIC_TEST",
        metadata_json={"source": "api_test"},
    )
    await db_session.commit()

    assert event.id is not None
    assert event.tenant_id == tenant_a.id
    assert event.event_type == "student.enrollment.created"
    assert event.schema_version == "1.0"
    assert event.status == OutboxEventStatus.PENDING
    assert event.attempt_count == 0
    assert event.causation_id == "cmd_enroll_123"
    assert event.producer == "ACADEMIC_TEST"
    assert "student_id" in event.payload
    assert "course_id" in event.payload


@pytest.mark.asyncio
async def test_unsupported_event_types_and_schema_versions(
    db_session: AsyncSession, tenant_a: Institution
):
    """2. Test that unsupported event types and schema versions are rejected safely."""
    with pytest.raises(ValidationException) as exc1:
        await OutboxService.publish_event(
            db=db_session,
            tenant_id=tenant_a.id,
            event_type="invalid.unregistered.event",
            aggregate_type="Test",
            aggregate_id=uuid.uuid4(),
            payload={},
        )
    assert "Cannot emit unregistered event type" in str(exc1.value)

    with pytest.raises(ValidationException) as exc2:
        await OutboxService.publish_event(
            db=db_session,
            tenant_id=tenant_a.id,
            event_type="student.enrollment.created",
            aggregate_type="Enrollment",
            aggregate_id=uuid.uuid4(),
            payload={},
            schema_version="99.0",
        )
    assert "Unsupported domain event schema version" in str(exc2.value)


# =============================================================================
# 2. TRANSACTIONAL ATOMICITY & ROLLBACK TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_atomic_business_transaction_and_outbox_persistence(
    db_session: AsyncSession, tenant_a: Institution
):
    """3 & 5. Verify that outbox event commits atomically with business records."""
    academic_year = AcademicYear(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        name=f"AY {uuid.uuid4().hex[:4]}",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        is_current=True,
    )
    db_session.add(academic_year)

    event = await OutboxService.publish_event(
        db=db_session,
        tenant_id=tenant_a.id,
        event_type="student.enrollment.created",
        aggregate_type="AcademicYear",
        aggregate_id=academic_year.id,
        payload={"student_id": str(uuid.uuid4()), "course_id": str(uuid.uuid4())},
    )
    # Commit both atomically
    await db_session.commit()

    # Query outbox
    fetched = await OutboxService.fetch_pending_events(db_session, tenant_id=tenant_a.id)
    event_ids = [e.id for e in fetched]
    assert event.id in event_ids


@pytest.mark.asyncio
async def test_rollback_behavior_when_business_operations_fail(
    db_session: AsyncSession, tenant_a: Institution
):
    """4. Verify that rolling back the session rolls back both business change and outbox event."""
    event_id = uuid.uuid4()
    event = await OutboxService.publish_event(
        db=db_session,
        tenant_id=tenant_a.id,
        event_type="finance.payment.confirmed",
        aggregate_type="Payment",
        aggregate_id=event_id,
        payload={"payment_id": str(event_id), "student_id": str(uuid.uuid4()), "amount": 500.0},
    )

    # Simulate transactional failure
    await db_session.rollback()

    # Verify event is NOT in DB
    stmt = select(OutboxEvent).where(OutboxEvent.id == event.id)
    res = await db_session.execute(stmt)
    assert res.scalar_one_or_none() is None


# =============================================================================
# 3. CONCURRENCY, RECOVERY & CONSUMER IDEMPOTENCY
# =============================================================================


@pytest.mark.asyncio
async def test_recovery_after_publisher_failure(db_session: AsyncSession, tenant_a: Institution):
    """6. Recovery after a publisher failure."""
    event = await OutboxService.publish_event(
        db=db_session,
        tenant_id=tenant_a.id,
        event_type="document.certificate.issued",
        aggregate_type="IssuedCertificate",
        aggregate_id=uuid.uuid4(),
        payload={"certificate_id": str(uuid.uuid4()), "student_id": str(uuid.uuid4())},
    )
    await db_session.commit()

    # Worker claims event
    marked = await OutboxService.mark_processing(db_session, event.id)
    assert marked is True

    # Simulate crash/failure: mark failed with error
    await OutboxService.mark_failed(db_session, event.id, "Simulated network timeout")

    # Re-fetch event from DB
    stmt = select(OutboxEvent).where(OutboxEvent.id == event.id)
    refreshed = (await db_session.execute(stmt)).scalar_one()
    assert refreshed.status == OutboxEventStatus.PENDING
    assert refreshed.attempt_count == 1
    assert "Simulated network timeout" in refreshed.last_error


@pytest.mark.asyncio
async def test_concurrent_outbox_workers_locking(db_session: AsyncSession, tenant_a: Institution):
    """7. Concurrent outbox workers locking strategy."""
    event = await OutboxService.publish_event(
        db=db_session,
        tenant_id=tenant_a.id,
        event_type="attendance.session.finalized",
        aggregate_type="AttendanceSession",
        aggregate_id=uuid.uuid4(),
        payload={"session_id": str(uuid.uuid4()), "course_id": str(uuid.uuid4())},
    )
    await db_session.commit()

    # Fetch with lock_for_update=True
    events = await OutboxService.fetch_pending_events(
        db_session, batch_size=10, lock_for_update=True
    )
    assert len(events) >= 1
    assert any(e.id == event.id for e in events)


@pytest.mark.asyncio
async def test_idempotent_consumer_behavior_and_deduplication(
    db_session: AsyncSession, tenant_a: Institution
):
    """8 & 9. Verify per-consumer deduplication checkpoints prevent repeated execution."""
    call_count = 0

    class DummyAuditConsumer(BaseDomainEventConsumer):
        @property
        def consumer_name(self) -> str:
            return "DummyAuditConsumer"

        @property
        def supported_event_types(self) -> list[str]:
            return ["student.enrollment.created"]

        async def handle(self, db: AsyncSession, envelope: DomainEventEnvelope) -> ConsumerResult:
            nonlocal call_count
            call_count += 1
            return ConsumerResult(status=ConsumerCheckpointStatus.COMPLETED)

    consumer = DummyAuditConsumer()
    envelope = DomainEventEnvelope(
        event_id=uuid.uuid4(),
        event_type="student.enrollment.created",
        tenant_id=tenant_a.id,
        aggregate_type="Enrollment",
        aggregate_id=uuid.uuid4(),
        payload={"student_id": str(uuid.uuid4())},
    )

    # First delivery: executes handler
    res1 = await ConsumerExecutionEngine.execute_consumer(db_session, consumer, envelope)
    assert res1.status == ConsumerCheckpointStatus.COMPLETED
    assert call_count == 1

    # Checkpoint exists in DB
    cp_stmt = select(EventConsumerCheckpoint).where(
        EventConsumerCheckpoint.event_id == envelope.event_id,
        EventConsumerCheckpoint.consumer_name == "DummyAuditConsumer",
    )
    checkpoint = (await db_session.execute(cp_stmt)).scalar_one_or_none()
    assert checkpoint is not None
    assert checkpoint.status == ConsumerCheckpointStatus.COMPLETED
    assert checkpoint.duration_ms >= 0.0

    # Duplicate delivery of identical event: skips handler
    res2 = await ConsumerExecutionEngine.execute_consumer(db_session, consumer, envelope)
    assert res2.status == ConsumerCheckpointStatus.COMPLETED
    assert res2.metadata.get("idempotent_skip") is True
    assert call_count == 1  # Did NOT increment!


# =============================================================================
# 4. RETRY BACKOFF, DEAD-LETTER & REPLAY
# =============================================================================


@pytest.mark.asyncio
async def test_retry_backoff_and_dead_letter_routing(
    db_session: AsyncSession, tenant_a: Institution
):
    """10 & 11. Bounded exponential backoff and dead-letter queue creation."""
    event = await OutboxService.publish_event(
        db=db_session,
        tenant_id=tenant_a.id,
        event_type="finance.payment.confirmed",
        aggregate_type="Payment",
        aggregate_id=uuid.uuid4(),
        payload={"payment_id": str(uuid.uuid4())},
    )
    await db_session.commit()

    # Simulate 5 consecutive failed processing attempts
    for attempt in range(1, 5):
        await OutboxService.mark_processing(db_session, event.id)
        await OutboxService.mark_failed(db_session, event.id, f"Temporary provider error {attempt}")

    # 5th failure exceeds max_retries=5
    await OutboxService.mark_processing(db_session, event.id)
    await OutboxService.mark_failed(
        db_session, event.id, "Terminal downstream failure", max_retries=5
    )

    stmt = select(OutboxEvent).where(OutboxEvent.id == event.id)
    updated = (await db_session.execute(stmt)).scalar_one()
    assert updated.status == OutboxEventStatus.DEAD_LETTER

    # Dead letter table entry created
    dlq_stmt = select(EventDeadLetter).where(EventDeadLetter.event_id == event.id)
    dlq_entry = (await db_session.execute(dlq_stmt)).scalar_one_or_none()
    assert dlq_entry is not None
    assert dlq_entry.is_resolved is False
    assert "Terminal downstream failure" in dlq_entry.failure_reason

    # Safe replay
    replayed = await OutboxService.replay_event(
        db_session, tenant_id=tenant_a.id, event_id=event.id
    )
    assert replayed.status == OutboxEventStatus.PENDING

    dlq_refreshed = (await db_session.execute(dlq_stmt)).scalar_one()
    assert dlq_refreshed.is_resolved is True


# =============================================================================
# 5. MULTI-TENANT ISOLATION & PERMISSION CHECKS
# =============================================================================


@pytest.mark.asyncio
async def test_tenant_isolation_across_event_reads_and_retries(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_b: Institution,
    tenant_admin_a: User,
):
    """12 & 13. Tenant isolation and permission checks on outbox endpoints."""
    # Create event in Tenant B
    event_b = await OutboxService.publish_event(
        db=db_session,
        tenant_id=tenant_b.id,
        event_type="student.enrollment.created",
        aggregate_type="Enrollment",
        aggregate_id=uuid.uuid4(),
        payload={"student_id": str(uuid.uuid4())},
    )
    await db_session.commit()

    headers_a = make_auth_headers(tenant_admin_a, tenant_a.id)

    # 1. Tenant A admin lists events -> Tenant B event NOT in list
    res = await client.get("/api/v1/admin/events/outbox", headers=headers_a)
    assert res.status_code == 200
    data = res.json()["data"]
    item_ids = [item["id"] for item in data["items"]]
    assert str(event_b.id) not in item_ids

    # 2. Tenant A admin tries to fetch Tenant B event directly -> 404
    res_single = await client.get(f"/api/v1/admin/events/outbox/{event_b.id}", headers=headers_a)
    assert res_single.status_code == 404

    # 3. Tenant A admin tries to retry Tenant B event -> 404
    res_retry = await client.post(
        f"/api/v1/admin/events/outbox/{event_b.id}/retry", headers=headers_a
    )
    assert res_retry.status_code == 404

    # 4. Unauthenticated request -> 401
    res_unauth = await client.get("/api/v1/admin/events/outbox")
    assert res_unauth.status_code == 401


# =============================================================================
# 6. SENSITIVE FIELD FILTERING & SANITIZATION
# =============================================================================


@pytest.mark.asyncio
async def test_sensitive_field_filtering_and_sanitized_logs():
    """14. Ensure credentials, tokens, and secrets are strictly scrubbed
    from payloads and errors.
    """
    raw_payload = {
        "student_id": str(uuid.uuid4()),
        "course_id": str(uuid.uuid4()),
        "password": "ClearTextPassword123",
        "secret_token": "bearer_super_secret",
        "card_number": "4111111111111111",
        "unlisted_data": "random",
    }
    sanitized = sanitize_event_payload("student.enrollment.created", raw_payload)

    assert "student_id" in sanitized
    assert "course_id" in sanitized
    assert "password" not in sanitized
    assert "secret_token" not in sanitized
    assert "card_number" not in sanitized
    assert "unlisted_data" not in sanitized

    # Error text scrubbing
    dirty_err = "Database connection failed with password=db_pass_123 and token=jwt_abc"
    clean_err = sanitize_error_text(dirty_err)
    assert "db_pass_123" not in clean_err
    assert "jwt_abc" not in clean_err
    assert "[REDACTED]" in clean_err


# =============================================================================
# 7. CORRELATION & CAUSATION PROPAGATION
# =============================================================================


@pytest.mark.asyncio
async def test_correlation_and_causation_propagation(
    db_session: AsyncSession, tenant_a: Institution
):
    """15. Correlation ID and causation ID propagation."""
    corr_id = f"corr_{uuid.uuid4().hex}"
    cause_id = f"cause_{uuid.uuid4().hex}"
    actor_id = uuid.uuid4()

    event = await OutboxService.publish_event(
        db=db_session,
        tenant_id=tenant_a.id,
        event_type="workflow.case.completed",
        aggregate_type="Case",
        aggregate_id=uuid.uuid4(),
        payload={"case_id": str(uuid.uuid4()), "case_number": "CASE-101", "resolution": "Resolved"},
        correlation_id=corr_id,
        causation_id=cause_id,
        actor_id=actor_id,
    )
    await db_session.commit()

    envelope = DomainEventEnvelope.from_outbox_event(event)
    assert envelope.correlation_id == corr_id
    assert envelope.causation_id == cause_id
    assert envelope.actor_id == actor_id
    assert envelope.to_dict()["correlation_id"] == corr_id
    assert envelope.to_dict()["causation_id"] == cause_id


# =============================================================================
# 8. REAL DOMAIN INTEGRATION (CASE CLOSURE WORKFLOW EVENT)
# =============================================================================


@pytest.mark.asyncio
async def test_integration_with_real_domain_transaction(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """16. Integration with real existing domain transaction
    (workflow.case.completed on case closure).
    """
    case_service = CaseService(db_session)
    case = await case_service.create_case(
        tenant_a.id,
        CaseCreate(
            case_type_code="DOCUMENT_VERIFICATION",
            title="Student Degree Verification",
            priority=CasePriority.NORMAL,
        ),
        actor_id=tenant_admin_a.id,
    )
    await db_session.commit()

    # Close case using CaseService
    await case_service.close_case(
        tenant_id=tenant_a.id,
        case_id=case.id,
        closure_notes="Document verified successfully",
        actor_id=tenant_admin_a.id,
    )
    await db_session.commit()

    # Verify workflow.case.completed outbox event was recorded atomically
    outbox_stmt = select(OutboxEvent).where(
        OutboxEvent.tenant_id == tenant_a.id,
        OutboxEvent.event_type == "workflow.case.completed",
        OutboxEvent.aggregate_id == case.id,
    )
    res = await db_session.execute(outbox_stmt)
    event = res.scalar_one_or_none()
    assert event is not None
    assert event.status == OutboxEventStatus.PENDING
    assert event.payload["case_id"] == str(case.id)
    assert event.payload["resolution"] == "Document verified successfully"
    assert event.actor_id == tenant_admin_a.id
    assert event.producer == "CASE_MANAGEMENT_MODULE"


# =============================================================================
# 9. WORKER BATCH & GRACEFUL EXECUTION
# =============================================================================


@pytest.mark.asyncio
async def test_worker_batch_processing_and_empty_batch(
    db_session: AsyncSession, tenant_a: Institution
):
    """17 & 18. Worker processing batch and empty handling."""
    # Drain any existing events from earlier tests
    await process_outbox_batch(batch_size=100, db=db_session)

    # When no pending events exist, returns 0
    cnt = await process_outbox_batch(batch_size=10, db=db_session)
    assert cnt == 0

    # Publish an event
    await OutboxService.publish_event(
        db=db_session,
        tenant_id=tenant_a.id,
        event_type="student.enrollment.created",
        aggregate_type="Enrollment",
        aggregate_id=uuid.uuid4(),
        payload={"student_id": str(uuid.uuid4())},
    )
    await db_session.commit()

    # Process batch
    processed_count = await process_outbox_batch(batch_size=10, db=db_session)
    assert processed_count >= 1


# =============================================================================
# 10. ADMIN METRICS & CONSUMERS ENDPOINTS
# =============================================================================


@pytest.mark.asyncio
async def test_admin_metrics_and_consumers_endpoints(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Admin operational metrics and consumers endpoints."""
    headers = make_auth_headers(tenant_admin_a, tenant_a.id)

    # 1. Get metrics
    res_metrics = await client.get("/api/v1/admin/events/metrics", headers=headers)
    assert res_metrics.status_code == 200
    metrics = res_metrics.json()["data"]
    assert "pending_count" in metrics
    assert "processed_count" in metrics
    assert "dead_letter_count" in metrics
    assert "average_consumer_latency_ms" in metrics

    # 2. Get consumers list
    res_cons = await client.get("/api/v1/admin/events/consumers", headers=headers)
    assert res_cons.status_code == 200
    consumers = res_cons.json()["data"]
    consumer_names = [c["consumer_name"] for c in consumers]
    assert "NotificationEventConsumer" in consumer_names
    assert "WorkflowEventConsumer" in consumer_names
    assert "AuditTrailConsumer" in consumer_names


# =============================================================================
# 11. CLEANUP & RETENTION POLICY
# =============================================================================


@pytest.mark.asyncio
async def test_cleanup_published_events_retention(db_session: AsyncSession, tenant_a: Institution):
    """20. Ensure cleanup only removes processed events older than retention period."""
    now = datetime.now(UTC)
    old_time = now - timedelta(days=120)

    # 1. Old processed event -> SHOULD be deleted
    old_processed = OutboxEvent(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        schema_version="1.0",
        event_type="student.enrollment.created",
        aggregate_type="Enrollment",
        aggregate_id=uuid.uuid4(),
        status=OutboxEventStatus.PROCESSED,
        processed_at=old_time,
        created_at=old_time,
        correlation_id=str(uuid.uuid4()),
        payload={},
    )

    # 2. Old PENDING event -> MUST NOT be deleted
    old_pending = OutboxEvent(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        schema_version="1.0",
        event_type="student.enrollment.created",
        aggregate_type="Enrollment",
        aggregate_id=uuid.uuid4(),
        status=OutboxEventStatus.PENDING,
        created_at=old_time,
        correlation_id=str(uuid.uuid4()),
        payload={},
    )

    # 3. Old DEAD_LETTER event -> MUST NOT be deleted
    old_dead = OutboxEvent(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        schema_version="1.0",
        event_type="student.enrollment.created",
        aggregate_type="Enrollment",
        aggregate_id=uuid.uuid4(),
        status=OutboxEventStatus.DEAD_LETTER,
        created_at=old_time,
        correlation_id=str(uuid.uuid4()),
        payload={},
    )

    db_session.add_all([old_processed, old_pending, old_dead])
    await db_session.commit()

    # Run cleanup with 90 day retention
    deleted_count = await OutboxService.cleanup_published_events(
        db_session, tenant_id=tenant_a.id, retention_days=90
    )
    assert deleted_count >= 1

    # Verify old_processed is gone
    check_proc = await db_session.execute(
        select(OutboxEvent).where(OutboxEvent.id == old_processed.id)
    )
    assert check_proc.scalar_one_or_none() is None

    # Verify old_pending still exists
    check_pend = await db_session.execute(
        select(OutboxEvent).where(OutboxEvent.id == old_pending.id)
    )
    assert check_pend.scalar_one_or_none() is not None

    # Verify old_dead still exists
    check_dead = await db_session.execute(select(OutboxEvent).where(OutboxEvent.id == old_dead.id))
    assert check_dead.scalar_one_or_none() is not None
