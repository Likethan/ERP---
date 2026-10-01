"""Student API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_tenant_context, require_permission
from app.core.permissions import (
    PEOPLE_STUDENTS_CREATE,
    PEOPLE_STUDENTS_READ,
    PEOPLE_STUDENTS_UPDATE,
)
from app.core.tenant import TenantContext
from app.models.people import User
from app.schemas.common import ApiResponse, PaginatedResponse
from app.schemas.people import (
    StudentCreateRequest,
    StudentDetailResponse,
    StudentStatusTransitionRequest,
    StudentSummaryResponse,
    StudentUpdateRequest,
)
from app.services.people_service import PeopleService

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("", response_model=PaginatedResponse[StudentSummaryResponse])
async def list_students(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(PEOPLE_STUDENTS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    search: str | None = Query(None),
    program_id: UUID | None = Query(None),
    batch_id: UUID | None = Query(None),
    status: str | None = Query(None),
    section_id: UUID | None = Query(None),
) -> PaginatedResponse[StudentSummaryResponse]:
    items, meta = await PeopleService.list_students(
        db,
        tenant.tenant_id,
        page=page,
        page_size=page_size,
        search=search,
        program_id=program_id,
        batch_id=batch_id,
        status=status,
        section_id=section_id,
    )
    return PaginatedResponse(data=items, pagination=meta)


@router.post(
    "",
    response_model=ApiResponse[StudentDetailResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_student(
    payload: StudentCreateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(PEOPLE_STUDENTS_CREATE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[StudentDetailResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    student = await PeopleService.create_student(
        db, tenant.tenant_id, payload, author_user_id=current_user.id, ip_address=ip
    )
    detail = await PeopleService.get_student_detail(db, tenant.tenant_id, student.id)
    return ApiResponse(data=detail)


@router.get("/{student_id}", response_model=ApiResponse[StudentDetailResponse])
async def get_student(
    student_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(PEOPLE_STUDENTS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[StudentDetailResponse]:
    detail = await PeopleService.get_student_detail(db, tenant.tenant_id, student_id)
    return ApiResponse(data=detail)


@router.patch("/{student_id}", response_model=ApiResponse[StudentDetailResponse])
async def update_student(
    student_id: UUID,
    payload: StudentUpdateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(PEOPLE_STUDENTS_UPDATE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[StudentDetailResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    detail = await PeopleService.update_student(
        db, tenant.tenant_id, student_id, payload, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=detail)


@router.post(
    "/{student_id}/transition-status",
    response_model=ApiResponse[StudentDetailResponse],
)
async def transition_student_status(
    student_id: UUID,
    payload: StudentStatusTransitionRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(PEOPLE_STUDENTS_UPDATE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[StudentDetailResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    detail = await PeopleService.transition_student_status(
        db,
        tenant.tenant_id,
        student_id,
        payload,
        author_user_id=current_user.id,
        ip_address=ip,
    )
    return ApiResponse(data=detail)
