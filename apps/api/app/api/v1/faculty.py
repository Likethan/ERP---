"""Faculty API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_tenant_context, require_permission
from app.core.permissions import PEOPLE_FACULTY_MANAGE, PEOPLE_FACULTY_READ
from app.core.tenant import TenantContext
from app.models.people import User
from app.schemas.common import ApiResponse
from app.schemas.people import (
    FacultyCreateRequest,
    FacultyResponse,
    FacultyUpdateRequest,
)
from app.services.people_service import PeopleService

router = APIRouter(prefix="/faculty", tags=["Faculty"])


@router.get("", response_model=ApiResponse[list[FacultyResponse]])
async def list_faculty(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(PEOPLE_FACULTY_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    department_id: UUID | None = Query(None),
    search: str | None = Query(None),
) -> ApiResponse[list[FacultyResponse]]:
    faculty_list = await PeopleService.list_faculty(
        db, tenant.tenant_id, department_id=department_id, search=search
    )
    return ApiResponse(data=faculty_list)


@router.post("", response_model=ApiResponse[FacultyResponse], status_code=status.HTTP_201_CREATED)
async def create_faculty(
    payload: FacultyCreateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(PEOPLE_FACULTY_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[FacultyResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    faculty = await PeopleService.create_faculty(
        db, tenant.tenant_id, payload, author_user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=faculty)


@router.get("/{faculty_id}", response_model=ApiResponse[FacultyResponse])
async def get_faculty(
    faculty_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(PEOPLE_FACULTY_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[FacultyResponse]:
    faculty = await PeopleService.get_faculty_response(db, tenant.tenant_id, faculty_id)
    return ApiResponse(data=faculty)


@router.patch("/{faculty_id}", response_model=ApiResponse[FacultyResponse])
async def update_faculty(
    faculty_id: UUID,
    payload: FacultyUpdateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(PEOPLE_FACULTY_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[FacultyResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    faculty = await PeopleService.update_faculty(
        db, tenant.tenant_id, faculty_id, payload, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=faculty)
