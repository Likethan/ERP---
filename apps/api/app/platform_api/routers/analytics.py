"""API Analytics, Quotas & Usage Telemetry Router (Step 21).

Enforces:
- Aggregated metrics across requests, latencies (avg, p95, p99), errors, and hot endpoints.
- Application-specific usage audit trails.
- Privacy-aware telemetry disclosure.
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import require_permission
from app.models.people import User
from app.platform_api.models import ApiUsageRecord
from app.platform_api.schemas import (
    UsageAnalyticsResponse,
    UsageRecordResponse,
)
from app.platform_api.service import platform_service
from app.platform_api.usage import usage_metering_service

router = APIRouter(prefix="/platform", tags=["API Platform - Analytics"])


@router.get("/analytics", response_model=UsageAnalyticsResponse)
async def get_platform_analytics(
    request: Request,
    current_user: Annotated[User, Depends(require_permission("api:analytics:read"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    application_id: UUID | None = Query(None),
    start_time: datetime | None = Query(None),
    end_time: datetime | None = Query(None),
) -> UsageAnalyticsResponse:
    """Retrieve aggregated API performance, error rates, and consumption statistics."""
    tenant_ctx = getattr(request.state, "tenant", None)
    tenant_id = tenant_ctx.tenant_id if tenant_ctx else current_user.primary_tenant_id

    data = await usage_metering_service.get_analytics(
        db=db,
        tenant_id=tenant_id,
        application_id=application_id,
        start_time=start_time,
        end_time=end_time,
    )
    return UsageAnalyticsResponse(**data)


@router.get("/applications/{application_id}/usage", response_model=list[UsageRecordResponse])
async def get_application_usage_records(
    application_id: UUID,
    request: Request,
    current_user: Annotated[User, Depends(require_permission("api:applications:read"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    limit: int = Query(50, ge=1, le=200),
) -> list[UsageRecordResponse]:
    """Retrieve recent sanitized usage telemetry records for an application."""
    tenant_ctx = getattr(request.state, "tenant", None)
    tenant_id = tenant_ctx.tenant_id if tenant_ctx else current_user.primary_tenant_id

    user_roles = {ur.role.name for ur in current_user.roles if ur.role}
    is_admin = "SUPER_ADMIN" in user_roles or "INSTITUTION_ADMIN" in user_roles

    # Verify access to application
    await platform_service.get_application(
        db=db,
        tenant_id=tenant_id,
        application_id=application_id,
        owner_id=current_user.id,
        is_admin=is_admin,
    )

    stmt = (
        select(ApiUsageRecord)
        .where(
            ApiUsageRecord.tenant_id == tenant_id,
            ApiUsageRecord.application_id == application_id,
        )
        .order_by(ApiUsageRecord.timestamp.desc())
        .limit(limit)
    )
    res = await db.execute(stmt)
    records = res.scalars().all()

    return [UsageRecordResponse.model_validate(r) for r in records]
