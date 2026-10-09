"""External Consumable Students API (Platform v1).

Enforces:
- Scope: students.read
- Underlying PBAC: people:students:read
- Field-level governance masking for sensitive personal attributes (email, phone)
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
from app.core.exceptions import NotFoundException
from app.core.governance_registry import mask_email, mask_phone
from app.models.people import StudentProfile
from app.platform_api.dependencies import (
    ApiConsumerContext,
    require_api_consumer,
)
from app.platform_api.schemas import (
    PublicStudentListResponse,
    PublicStudentResponse,
)
from app.platform_api.scopes import SCOPE_STUDENTS_READ
from app.platform_api.usage import usage_metering_service

router = APIRouter(prefix="/platform/v1/students", tags=["Platform API - Students"])


@router.get("", response_model=PublicStudentListResponse)
async def list_students(
    request: Request,
    consumer: Annotated[
        ApiConsumerContext,
        Depends(
            require_api_consumer(
                required_scope=SCOPE_STUDENTS_READ, required_permission="people:students:read"
            )
        ),
    ],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None),
    status: str | None = Query(None),
) -> PublicStudentListResponse:
    """Query student records with pagination and governance masking."""
    start_time = time.perf_counter()

    stmt = (
        select(StudentProfile)
        .where(StudentProfile.tenant_id == consumer.tenant_id)
        .options(selectinload(StudentProfile.user))
        .order_by(StudentProfile.admission_number.asc())
        .limit(limit + 1)
    )
    if status:
        stmt = stmt.where(StudentProfile.status == status.upper())
    if cursor:
        stmt = stmt.where(StudentProfile.admission_number > cursor)

    res = await db.execute(stmt)
    records = list(res.scalars().all())

    has_more = len(records) > limit
    items_to_return = records[:limit]
    next_cursor = items_to_return[-1].admission_number if has_more and items_to_return else None

    # Map to public response with governance masking
    items = []
    for sp in items_to_return:
        u = sp.user
        masked_e = mask_email(u.email) if u else "redacted@example.com"
        masked_p = mask_phone(u.phone_number) if u and u.phone_number else None

        items.append(
            PublicStudentResponse(
                id=sp.id,
                student_id=sp.admission_number,
                first_name=u.first_name if u else "Student",
                last_name=u.last_name if u else "",
                email=masked_e,
                phone_number=masked_p,
                department_id=None,
                current_semester=None,
                status=sp.status,
                enrollment_date=str(sp.admission_date),
            )
        )

    latency_ms = (time.perf_counter() - start_time) * 1000
    await usage_metering_service.record_usage(
        db=db,
        tenant_id=consumer.tenant_id,
        application_id=consumer.application_id,
        credential_id=consumer.credential_id,
        method="GET",
        path="/api/v1/platform/v1/students",
        version="v1",
        status_code=200,
        latency_ms=latency_ms,
        correlation_id=request.headers.get("X-Correlation-ID"),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )

    return PublicStudentListResponse(
        items=items,
        next_cursor=next_cursor,
        has_more=has_more,
        total_count=len(items),
    )


@router.get("/{student_id}", response_model=PublicStudentResponse)
async def get_student(
    student_id: UUID,
    request: Request,
    consumer: Annotated[
        ApiConsumerContext,
        Depends(
            require_api_consumer(
                required_scope=SCOPE_STUDENTS_READ, required_permission="people:students:read"
            )
        ),
    ],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> PublicStudentResponse:
    """Fetch single student profile by UUID."""
    start_time = time.perf_counter()

    stmt = (
        select(StudentProfile)
        .where(
            StudentProfile.tenant_id == consumer.tenant_id,
            StudentProfile.id == student_id,
        )
        .options(selectinload(StudentProfile.user))
    )
    res = await db.execute(stmt)
    sp = res.scalar_one_or_none()
    if not sp:
        raise NotFoundException("StudentProfile", student_id)

    u = sp.user
    masked_e = mask_email(u.email) if u else "redacted@example.com"
    masked_p = mask_phone(u.phone_number) if u and u.phone_number else None

    latency_ms = (time.perf_counter() - start_time) * 1000
    await usage_metering_service.record_usage(
        db=db,
        tenant_id=consumer.tenant_id,
        application_id=consumer.application_id,
        credential_id=consumer.credential_id,
        method="GET",
        path=f"/api/v1/platform/v1/students/{student_id}",
        version="v1",
        status_code=200,
        latency_ms=latency_ms,
        correlation_id=request.headers.get("X-Correlation-ID"),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )

    return PublicStudentResponse(
        id=sp.id,
        student_id=sp.admission_number,
        first_name=u.first_name if u else "Student",
        last_name=u.last_name if u else "",
        email=masked_e,
        phone_number=masked_p,
        department_id=None,
        current_semester=None,
        status=sp.status,
        enrollment_date=str(sp.admission_date),
    )
