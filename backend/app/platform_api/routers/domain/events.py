"""External Consumable Campus Events API (Platform v1).

Enforces:
- Scope: events.read
- Underlying PBAC: events:read
- Tenant boundary isolation
- Public & institutional visibility filtering
- Usage metering telemetry
"""

import time
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.models.campus import CampusEvent
from app.platform_api.dependencies import (
    ApiConsumerContext,
    require_api_consumer,
)
from app.platform_api.schemas import PublicEventResponse
from app.platform_api.scopes import SCOPE_EVENTS_READ
from app.platform_api.usage import usage_metering_service

router = APIRouter(prefix="/platform/v1/events", tags=["Platform API - Events"])


@router.get("", response_model=list[PublicEventResponse])
async def list_events(
    request: Request,
    consumer: Annotated[
        ApiConsumerContext,
        Depends(
            require_api_consumer(
                required_scope=SCOPE_EVENTS_READ, required_permission="events:read"
            )
        ),
    ],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    limit: int = Query(50, ge=1, le=100),
) -> list[PublicEventResponse]:
    """List approved campus events within tenant boundary."""
    start_time = time.perf_counter()

    stmt = (
        select(CampusEvent)
        .where(
            CampusEvent.tenant_id == consumer.tenant_id,
            CampusEvent.status.in_(["PUBLISHED", "REGISTRATION_OPEN", "ONGOING", "COMPLETED"]),
        )
        .order_by(CampusEvent.start_at.asc())
        .limit(limit)
    )
    res = await db.execute(stmt)
    events = res.scalars().all()

    items = [
        PublicEventResponse(
            id=e.id,
            title=e.title,
            description=e.description,
            category=None,
            start_time=e.start_at,
            end_time=e.end_at,
            venue_name=e.venue_name,
            status=e.status,
        )
        for e in events
    ]

    latency_ms = (time.perf_counter() - start_time) * 1000
    await usage_metering_service.record_usage(
        db=db,
        tenant_id=consumer.tenant_id,
        application_id=consumer.application_id,
        credential_id=consumer.credential_id,
        method="GET",
        path="/api/v1/platform/v1/events",
        version="v1",
        status_code=200,
        latency_ms=latency_ms,
        correlation_id=request.headers.get("X-Correlation-ID"),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )

    return items
