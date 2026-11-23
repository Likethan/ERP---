"""External Consumable Examinations API (Platform v1).

Enforces:
- Scope: examinations.read
- Underlying PBAC: examinations:results:read
- Tenant boundary isolation
- Published status check (unfinalized drafts never exposed externally)
- Usage metering telemetry
"""

import time
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.models.examination import SemesterExamResult
from app.platform_api.dependencies import (
    ApiConsumerContext,
    require_api_consumer,
)
from app.platform_api.schemas import (
    PublicExamResult,
    PublicExamResultResponse,
)
from app.platform_api.scopes import SCOPE_EXAMINATIONS_READ
from app.platform_api.usage import usage_metering_service

router = APIRouter(prefix="/platform/v1/examinations", tags=["Platform API - Examinations"])


@router.get("/results", response_model=PublicExamResultResponse)
async def query_examination_results(
    request: Request,
    consumer: Annotated[
        ApiConsumerContext,
        Depends(
            require_api_consumer(
                required_scope=SCOPE_EXAMINATIONS_READ,
                required_permission="examinations:results:read",
            )
        ),
    ],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    student_id: UUID | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
) -> PublicExamResultResponse:
    """Retrieve published semester examination results."""
    start_time = time.perf_counter()

    stmt = (
        select(SemesterExamResult)
        .where(
            SemesterExamResult.tenant_id == consumer.tenant_id,
            SemesterExamResult.publication_status == "PUBLISHED",
        )
        .limit(limit)
    )
    if student_id:
        stmt = stmt.where(SemesterExamResult.student_id == student_id)

    res = await db.execute(stmt)
    results = res.scalars().all()

    items = [
        PublicExamResult(
            id=r.id,
            student_id=r.student_id,
            subject_code=None,
            marks_obtained=float(r.total_marks),
            max_marks=100.0,
            grade=r.grade_letter,
            status=r.result_status,
        )
        for r in results
    ]

    latency_ms = (time.perf_counter() - start_time) * 1000
    await usage_metering_service.record_usage(
        db=db,
        tenant_id=consumer.tenant_id,
        application_id=consumer.application_id,
        credential_id=consumer.credential_id,
        method="GET",
        path="/api/v1/platform/v1/examinations/results",
        version="v1",
        status_code=200,
        latency_ms=latency_ms,
        correlation_id=request.headers.get("X-Correlation-ID"),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )

    return PublicExamResultResponse(
        items=items,
        total_count=len(items),
    )
