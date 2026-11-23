"""External Consumable Attendance API (Platform v1).

Enforces:
- Scope: attendance.read
- Underlying PBAC: attendance:records:read
- Tenant boundary isolation
- Usage metering telemetry
"""

import time
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db_session
from app.models.attendance import AttendanceRecord
from app.platform_api.dependencies import (
    ApiConsumerContext,
    require_api_consumer,
)
from app.platform_api.schemas import (
    PublicAttendanceRecord,
    PublicAttendanceResponse,
)
from app.platform_api.scopes import SCOPE_ATTENDANCE_READ
from app.platform_api.usage import usage_metering_service

router = APIRouter(prefix="/platform/v1/attendance", tags=["Platform API - Attendance"])


@router.get("", response_model=PublicAttendanceResponse)
async def query_attendance(
    request: Request,
    consumer: Annotated[
        ApiConsumerContext,
        Depends(
            require_api_consumer(
                required_scope=SCOPE_ATTENDANCE_READ, required_permission="attendance:records:read"
            )
        ),
    ],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    student_id: UUID | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
) -> PublicAttendanceResponse:
    """Query student attendance session records."""
    start_time = time.perf_counter()

    stmt = (
        select(AttendanceRecord)
        .where(AttendanceRecord.tenant_id == consumer.tenant_id)
        .options(selectinload(AttendanceRecord.session))
        .limit(limit)
    )
    if student_id:
        stmt = stmt.where(AttendanceRecord.student_id == student_id)

    res = await db.execute(stmt)
    records = res.scalars().all()

    items = [
        PublicAttendanceRecord(
            id=r.id,
            student_id=r.student_id,
            date=str(r.session.session_date) if r.session else "2026-01-01",
            status=r.status,
            remarks=r.remarks,
        )
        for r in records
    ]

    latency_ms = (time.perf_counter() - start_time) * 1000
    await usage_metering_service.record_usage(
        db=db,
        tenant_id=consumer.tenant_id,
        application_id=consumer.application_id,
        credential_id=consumer.credential_id,
        method="GET",
        path="/api/v1/platform/v1/attendance",
        version="v1",
        status_code=200,
        latency_ms=latency_ms,
        correlation_id=request.headers.get("X-Correlation-ID"),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )

    return PublicAttendanceResponse(
        items=items,
        total_count=len(items),
    )
