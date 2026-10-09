"""External Consumable Academics API (Platform v1).

Enforces:
- Scope: academics.read
- Underlying PBAC: academics:courses:read
- Tenant boundary isolation
- Usage metering telemetry
"""

import time
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.models.academics import CurriculumScheme, Subject
from app.platform_api.dependencies import (
    ApiConsumerContext,
    require_api_consumer,
)
from app.platform_api.schemas import (
    PublicCourseResponse,
    PublicCurriculumResponse,
)
from app.platform_api.scopes import SCOPE_ACADEMICS_READ
from app.platform_api.usage import usage_metering_service

router = APIRouter(prefix="/platform/v1", tags=["Platform API - Academics"])


@router.get("/courses", response_model=list[PublicCourseResponse])
async def list_courses(
    request: Request,
    consumer: Annotated[
        ApiConsumerContext,
        Depends(
            require_api_consumer(
                required_scope=SCOPE_ACADEMICS_READ, required_permission="academics:courses:read"
            )
        ),
    ],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    limit: int = Query(50, ge=1, le=100),
) -> list[PublicCourseResponse]:
    """Query course catalog offerings within tenant boundary."""
    start_time = time.perf_counter()

    stmt = (
        select(Subject)
        .where(Subject.tenant_id == consumer.tenant_id)
        .order_by(Subject.code.asc())
        .limit(limit)
    )
    res = await db.execute(stmt)
    subjects = res.scalars().all()

    items = [
        PublicCourseResponse(
            id=s.id,
            code=s.code,
            name=s.name,
            credits=float(s.credits),
            department_id=s.department_id,
            is_active=s.is_active,
        )
        for s in subjects
    ]

    latency_ms = (time.perf_counter() - start_time) * 1000
    await usage_metering_service.record_usage(
        db=db,
        tenant_id=consumer.tenant_id,
        application_id=consumer.application_id,
        credential_id=consumer.credential_id,
        method="GET",
        path="/api/v1/platform/v1/courses",
        version="v1",
        status_code=200,
        latency_ms=latency_ms,
        correlation_id=request.headers.get("X-Correlation-ID"),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )

    return items


@router.get("/curriculum", response_model=list[PublicCurriculumResponse])
async def list_curriculums(
    request: Request,
    consumer: Annotated[
        ApiConsumerContext,
        Depends(
            require_api_consumer(
                required_scope=SCOPE_ACADEMICS_READ, required_permission="academics:curriculum:read"
            )
        ),
    ],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    limit: int = Query(50, ge=1, le=100),
) -> list[PublicCurriculumResponse]:
    """Retrieve curriculum structures."""
    start_time = time.perf_counter()

    stmt = (
        select(CurriculumScheme)
        .where(CurriculumScheme.tenant_id == consumer.tenant_id)
        .limit(limit)
    )
    res = await db.execute(stmt)
    curriculums = res.scalars().all()

    items = [
        PublicCurriculumResponse(
            id=c.id,
            program_id=c.program_id,
            academic_year=None,
            total_credits=getattr(c, "total_credits", 160.0),
        )
        for c in curriculums
    ]

    latency_ms = (time.perf_counter() - start_time) * 1000
    await usage_metering_service.record_usage(
        db=db,
        tenant_id=consumer.tenant_id,
        application_id=consumer.application_id,
        credential_id=consumer.credential_id,
        method="GET",
        path="/api/v1/platform/v1/curriculum",
        version="v1",
        status_code=200,
        latency_ms=latency_ms,
        correlation_id=request.headers.get("X-Correlation-ID"),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )

    return items
