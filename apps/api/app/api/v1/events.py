"""Enterprise Domain Events, Transactional Outbox & Reliability API Endpoints (Step 27).

Provides:
- Outbox event inspection & monitoring
- Dead-letter triage & resolution
- Audited retry & replay workflows
- Consumer registry introspection & health
- Operational metrics (throughput, backlog age, failure rates)
"""

import logging
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditEventCategory, record_audit_log
from app.core.database import get_db_session
from app.core.deps import (
    require_permission,
)
from app.core.event_consumer import ConsumerRegistry
from app.core.events import (
    OutboxService,
)
from app.core.exceptions import NotFoundException, ValidationException
from app.core.permissions import (
    DOMAIN_EVENTS_CONSUMERS_MANAGE,
    DOMAIN_EVENTS_METRICS_READ,
    DOMAIN_EVENTS_READ,
    DOMAIN_EVENTS_REPLAY,
    DOMAIN_EVENTS_RETRY,
)
from app.models.event import (
    ConsumerCheckpointStatus,
    EventConsumerCheckpoint,
    EventDeadLetter,
)
from app.models.people import User
from app.models.workflow import OutboxEvent, OutboxEventStatus
from app.schemas.common import ApiResponse
from app.schemas.event import (
    EventConsumerInfoResponse,
    EventDeadLetterListResponse,
    EventDeadLetterResolveRequest,
    EventDeadLetterResponse,
    EventMetricsResponse,
    EventReplayRequest,
    EventReplayResponse,
    EventRetryResponse,
    OutboxEventDetailResponse,
    OutboxEventListResponse,
    OutboxEventSummaryResponse,
)

logger = logging.getLogger("campusos.api.events")

router = APIRouter(prefix="/admin/events", tags=["Enterprise Domain Events & Outbox"])


def _resolve_tenant_id(user: User, request: Request) -> UUID:
    """Extract authenticated tenant ID with server-side validation."""
    if hasattr(request.state, "tenant") and request.state.tenant and request.state.tenant.tenant_id:
        return request.state.tenant.tenant_id
    if user.institution_id:
        return user.institution_id
    raise ValidationException("Operation requires an active tenant context.")


# -----------------------------------------------------------------------------
# 1. OUTBOX EVENTS MONITORING
# -----------------------------------------------------------------------------


@router.get(
    "/outbox",
    response_model=ApiResponse[OutboxEventListResponse],
    summary="List Outbox Events",
)
async def list_outbox_events(
    request: Request,
    current_user: Annotated[User, Depends(require_permission(DOMAIN_EVENTS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status: str | None = Query(
        None,
        description="Filter by event status (PENDING, PROCESSING, PROCESSED, FAILED, DEAD_LETTER)",
    ),
    event_type: str | None = Query(None, description="Filter by event type"),
    correlation_id: str | None = Query(None, description="Filter by correlation ID"),
    from_date: datetime | None = Query(None, description="Filter events created after timestamp"),
    to_date: datetime | None = Query(None, description="Filter events created before timestamp"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List tenant-scoped outbox events with filtering and pagination."""
    tenant_id = _resolve_tenant_id(current_user, request)
    conditions = [OutboxEvent.tenant_id == tenant_id]

    if status:
        conditions.append(OutboxEvent.status == status.upper())
    if event_type:
        conditions.append(OutboxEvent.event_type == event_type)
    if correlation_id:
        conditions.append(OutboxEvent.correlation_id == correlation_id)
    if from_date:
        conditions.append(OutboxEvent.created_at >= from_date)
    if to_date:
        conditions.append(OutboxEvent.created_at <= to_date)

    count_stmt = select(func.count(OutboxEvent.id)).where(and_(*conditions))
    total_count = (await db.execute(count_stmt)).scalar() or 0

    query = (
        select(OutboxEvent)
        .where(and_(*conditions))
        .order_by(OutboxEvent.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    res = await db.execute(query)
    events = res.scalars().all()

    items = [OutboxEventSummaryResponse.model_validate(e) for e in events]
    return ApiResponse(
        data=OutboxEventListResponse(items=items, total=total_count, limit=limit, offset=offset)
    )


@router.get(
    "/outbox/{event_id}",
    response_model=ApiResponse[OutboxEventDetailResponse],
    summary="Get Outbox Event Details",
)
async def get_outbox_event(
    event_id: UUID,
    request: Request,
    current_user: Annotated[User, Depends(require_permission(DOMAIN_EVENTS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Retrieve full details of an outbox event including sanitized payload."""
    tenant_id = _resolve_tenant_id(current_user, request)
    stmt = select(OutboxEvent).where(
        and_(OutboxEvent.id == event_id, OutboxEvent.tenant_id == tenant_id)
    )
    res = await db.execute(stmt)
    event = res.scalar_one_or_none()
    if not event:
        raise NotFoundException(f"Outbox event '{event_id}' not found.")

    return ApiResponse(data=OutboxEventDetailResponse.model_validate(event))


# -----------------------------------------------------------------------------
# 2. RETRY AND REPLAY OPERATIONS
# -----------------------------------------------------------------------------


@router.post(
    "/outbox/{event_id}/retry",
    response_model=ApiResponse[EventRetryResponse],
    summary="Retry Outbox Event",
)
async def retry_outbox_event(
    event_id: UUID,
    request: Request,
    current_user: Annotated[User, Depends(require_permission(DOMAIN_EVENTS_RETRY))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Reset a failed or dead-letter outbox event for immediate background retry."""
    tenant_id = _resolve_tenant_id(current_user, request)
    event = await OutboxService.retry_event(
        db, tenant_id=tenant_id, event_id=event_id, user_id=current_user.id
    )

    # Immutable forensic audit logging
    await record_audit_log(
        db=db,
        tenant_id=tenant_id,
        action=AuditEventCategory.EVENT_OUTBOX_RETRY,
        entity_type="OutboxEvent",
        entity_id=event.id,
        user_id=current_user.id,
        new_values_json={"event_type": event.event_type, "status": event.status},
        business_context=f"Operator retried outbox event {event.id}.",
    )
    await db.commit()

    return ApiResponse(
        data=EventRetryResponse(
            success=True,
            event_id=event.id,
            status=event.status,
            message="Outbox event reset to PENDING for immediate processing.",
        )
    )


@router.post(
    "/outbox/{event_id}/replay",
    response_model=ApiResponse[EventReplayResponse],
    summary="Replay Outbox Event",
)
async def replay_outbox_event(
    event_id: UUID,
    payload: EventReplayRequest,
    request: Request,
    current_user: Annotated[User, Depends(require_permission(DOMAIN_EVENTS_REPLAY))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Replay a domain event, selectively resetting specified consumer checkpoints."""
    tenant_id = _resolve_tenant_id(current_user, request)
    event = await OutboxService.replay_event(
        db,
        tenant_id=tenant_id,
        event_id=event_id,
        user_id=current_user.id,
        consumer_names=payload.consumer_names,
    )

    # Immutable forensic audit logging
    await record_audit_log(
        db=db,
        tenant_id=tenant_id,
        action=AuditEventCategory.EVENT_OUTBOX_REPLAY,
        entity_type="OutboxEvent",
        entity_id=event.id,
        user_id=current_user.id,
        new_values_json={
            "event_type": event.event_type,
            "consumers": payload.consumer_names or ["ALL"],
            "reason": payload.reason,
        },
        business_context=f"Operator replayed outbox event {event.id}.",
    )
    await db.commit()

    return ApiResponse(
        data=EventReplayResponse(
            success=True,
            event_id=event.id,
            status=event.status,
            target_consumers=payload.consumer_names or ["ALL"],
            message=(
                f"Event re-queued for replay across consumers: "
                f"{payload.consumer_names or 'ALL'}"
            ),
        )
    )


# -----------------------------------------------------------------------------
# 3. DEAD-LETTER MANAGEMENT
# -----------------------------------------------------------------------------


@router.get(
    "/dead-letter",
    response_model=ApiResponse[EventDeadLetterListResponse],
    summary="List Dead-Letter Events",
)
async def list_dead_letters(
    request: Request,
    current_user: Annotated[User, Depends(require_permission(DOMAIN_EVENTS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    is_resolved: bool | None = Query(None, description="Filter by resolution status"),
    event_type: str | None = Query(None, description="Filter by event type"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List exhausted domain events stored in the dead-letter review queue."""
    tenant_id = _resolve_tenant_id(current_user, request)
    conditions = [EventDeadLetter.tenant_id == tenant_id]

    if is_resolved is not None:
        conditions.append(EventDeadLetter.is_resolved == is_resolved)
    if event_type:
        conditions.append(EventDeadLetter.event_type == event_type)

    count_stmt = select(func.count(EventDeadLetter.id)).where(and_(*conditions))
    total_count = (await db.execute(count_stmt)).scalar() or 0

    query = (
        select(EventDeadLetter)
        .where(and_(*conditions))
        .order_by(EventDeadLetter.first_failed_at.desc())
        .offset(offset)
        .limit(limit)
    )
    res = await db.execute(query)
    records = res.scalars().all()

    items = [EventDeadLetterResponse.model_validate(r) for r in records]
    return ApiResponse(
        data=EventDeadLetterListResponse(items=items, total=total_count, limit=limit, offset=offset)
    )


@router.post(
    "/dead-letter/{dlq_id}/resolve",
    response_model=ApiResponse[EventDeadLetterResponse],
    summary="Resolve Dead-Letter Record",
)
async def resolve_dead_letter(
    dlq_id: UUID,
    payload: EventDeadLetterResolveRequest,
    request: Request,
    current_user: Annotated[User, Depends(require_permission(DOMAIN_EVENTS_RETRY))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Mark a dead-letter entry as resolved with administrative notes."""
    tenant_id = _resolve_tenant_id(current_user, request)
    stmt = select(EventDeadLetter).where(
        and_(EventDeadLetter.id == dlq_id, EventDeadLetter.tenant_id == tenant_id)
    )
    res = await db.execute(stmt)
    dlq = res.scalar_one_or_none()
    if not dlq:
        raise NotFoundException(f"Dead letter record '{dlq_id}' not found.")

    dlq.is_resolved = True
    dlq.resolved_at = datetime.now(UTC)
    dlq.resolved_by_id = current_user.id
    dlq.resolution_notes = payload.resolution_notes
    await db.commit()
    await db.refresh(dlq)

    return ApiResponse(data=EventDeadLetterResponse.model_validate(dlq))


# -----------------------------------------------------------------------------
# 4. CONSUMER INTROSPECTION & METRICS
# -----------------------------------------------------------------------------


@router.get(
    "/consumers",
    response_model=ApiResponse[list[EventConsumerInfoResponse]],
    summary="List Registered Event Consumers",
)
async def list_event_consumers(
    request: Request,
    current_user: Annotated[User, Depends(require_permission(DOMAIN_EVENTS_CONSUMERS_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Introspect registered consumers, subscribed event contracts, and processing totals."""
    tenant_id = _resolve_tenant_id(current_user, request)
    registered = ConsumerRegistry.all_consumers()
    responses: list[EventConsumerInfoResponse] = []

    for consumer in registered:
        # Aggregate checkpoint stats
        stats_stmt = (
            select(
                EventConsumerCheckpoint.status,
                func.count(EventConsumerCheckpoint.id).label("count"),
                func.avg(EventConsumerCheckpoint.duration_ms).label("avg_lat"),
            )
            .where(
                and_(
                    EventConsumerCheckpoint.tenant_id == tenant_id,
                    EventConsumerCheckpoint.consumer_name == consumer.consumer_name,
                )
            )
            .group_by(EventConsumerCheckpoint.status)
        )
        res = await db.execute(stats_stmt)
        rows = res.all()

        completed_count = 0
        failed_count = 0
        pending_count = 0
        total_lat = 0.0
        row_lat_count = 0

        for r in rows:
            stat_name = r[0]
            c = r[1]
            lat = r[2] or 0.0
            if stat_name == ConsumerCheckpointStatus.COMPLETED:
                completed_count = c
            elif stat_name == ConsumerCheckpointStatus.FAILED:
                failed_count = c
            elif stat_name == ConsumerCheckpointStatus.PENDING:
                pending_count = c
            total_lat += float(lat)
            row_lat_count += 1

        avg_lat = (total_lat / row_lat_count) if row_lat_count > 0 else 0.0

        responses.append(
            EventConsumerInfoResponse(
                consumer_name=consumer.consumer_name,
                supported_event_types=consumer.supported_event_types,
                total_completed=completed_count,
                total_failed=failed_count,
                total_pending=pending_count,
                avg_latency_ms=round(avg_lat, 2),
            )
        )

    return ApiResponse(data=responses)


@router.get(
    "/metrics",
    response_model=ApiResponse[EventMetricsResponse],
    summary="Get Outbox & Reliability Metrics",
)
async def get_event_metrics(
    request: Request,
    current_user: Annotated[User, Depends(require_permission(DOMAIN_EVENTS_METRICS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    """Retrieve operational outbox backlog, throughput, and error metrics."""
    tenant_id = _resolve_tenant_id(current_user, request)

    # 1. Outbox status counts
    status_stmt = (
        select(OutboxEvent.status, func.count(OutboxEvent.id))
        .where(OutboxEvent.tenant_id == tenant_id)
        .group_by(OutboxEvent.status)
    )
    status_res = await db.execute(status_stmt)
    status_counts = dict(status_res.all())

    pending_cnt = status_counts.get(OutboxEventStatus.PENDING, 0)
    processing_cnt = status_counts.get(OutboxEventStatus.PROCESSING, 0)
    processed_cnt = status_counts.get(OutboxEventStatus.PROCESSED, 0)
    failed_cnt = status_counts.get(OutboxEventStatus.FAILED, 0)
    dlq_cnt = status_counts.get(OutboxEventStatus.DEAD_LETTER, 0)

    # 2. Oldest pending age in seconds
    oldest_stmt = select(func.min(OutboxEvent.created_at)).where(
        and_(
            OutboxEvent.tenant_id == tenant_id,
            OutboxEvent.status == OutboxEventStatus.PENDING,
        )
    )
    oldest_res = (await db.execute(oldest_stmt)).scalar()
    oldest_age_sec = 0.0
    if oldest_res:
        now = datetime.now(UTC)
        oldest_age_sec = max(0.0, (now - oldest_res).total_seconds())

    # 3. Average consumer execution latency
    avg_stmt = select(func.avg(EventConsumerCheckpoint.duration_ms)).where(
        EventConsumerCheckpoint.tenant_id == tenant_id
    )
    avg_lat = (await db.execute(avg_stmt)).scalar() or 0.0

    return ApiResponse(
        data=EventMetricsResponse(
            tenant_id=tenant_id,
            pending_count=pending_cnt,
            processing_count=processing_cnt,
            processed_count=processed_cnt,
            failed_count=failed_cnt,
            dead_letter_count=dlq_cnt,
            oldest_pending_age_seconds=round(oldest_age_sec, 2),
            average_consumer_latency_ms=round(float(avg_lat), 2),
        )
    )
