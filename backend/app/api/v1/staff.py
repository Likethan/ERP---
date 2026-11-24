"""Staff API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_tenant_context, require_permission
from app.core.permissions import PEOPLE_STAFF_MANAGE, PEOPLE_STAFF_READ
from app.core.tenant import TenantContext
from app.models.people import User
from app.schemas.common import ApiResponse
from app.schemas.people import StaffCreateRequest, StaffResponse, StaffUpdateRequest
from app.services.people_service import PeopleService

router = APIRouter(prefix="/staff", tags=["Staff"])


@router.get("", response_model=ApiResponse[list[StaffResponse]])
async def list_staff(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(PEOPLE_STAFF_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    department_id: UUID | None = Query(None),
    search: str | None = Query(None),
) -> ApiResponse[list[StaffResponse]]:
    staff_list = await PeopleService.list_staff(
        db, tenant.tenant_id, department_id=department_id, search=search
    )
    return ApiResponse(data=staff_list)


@router.post("", response_model=ApiResponse[StaffResponse], status_code=status.HTTP_201_CREATED)
async def create_staff(
    payload: StaffCreateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(PEOPLE_STAFF_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[StaffResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    staff = await PeopleService.create_staff(
        db, tenant.tenant_id, payload, author_user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=staff)


@router.get("/{staff_id}", response_model=ApiResponse[StaffResponse])
async def get_staff(
    staff_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(PEOPLE_STAFF_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[StaffResponse]:
    staff = await PeopleService.get_staff_response(db, tenant.tenant_id, staff_id)
    return ApiResponse(data=staff)


@router.patch("/{staff_id}", response_model=ApiResponse[StaffResponse])
async def update_staff(
    staff_id: UUID,
    payload: StaffUpdateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(PEOPLE_STAFF_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[StaffResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    staff = await PeopleService.update_staff(
        db, tenant.tenant_id, staff_id, payload, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=staff)
