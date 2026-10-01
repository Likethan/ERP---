"""Department API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_tenant_context, require_permission
from app.core.permissions import CORE_DEPARTMENTS_MANAGE, CORE_DEPARTMENTS_READ
from app.core.tenant import TenantContext
from app.models.people import User
from app.schemas.common import ApiResponse
from app.schemas.core import (
    DepartmentCreateRequest,
    DepartmentResponse,
    DepartmentUpdateRequest,
)
from app.services.core_service import CoreService

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.get("", response_model=ApiResponse[list[DepartmentResponse]])
async def list_departments(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CORE_DEPARTMENTS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    campus_id: UUID | None = Query(None),
    search: str | None = Query(None),
) -> ApiResponse[list[DepartmentResponse]]:
    departments = await CoreService.list_departments(
        db, tenant.tenant_id, campus_id=campus_id, search=search
    )
    result = []
    for d in departments:
        resp = DepartmentResponse.model_validate(d)
        if d.hod:
            resp.hod_name = f"{d.hod.first_name} {d.hod.last_name}"
        result.append(resp)
    return ApiResponse(data=result)


@router.post(
    "",
    response_model=ApiResponse[DepartmentResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_department(
    payload: DepartmentCreateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CORE_DEPARTMENTS_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[DepartmentResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    dept = await CoreService.create_department(
        db, tenant.tenant_id, payload, user_id=current_user.id, ip_address=ip
    )
    resp = DepartmentResponse.model_validate(dept)
    if dept.hod:
        resp.hod_name = f"{dept.hod.first_name} {dept.hod.last_name}"
    return ApiResponse(data=resp)


@router.get("/{department_id}", response_model=ApiResponse[DepartmentResponse])
async def get_department(
    department_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CORE_DEPARTMENTS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[DepartmentResponse]:
    dept = await CoreService.get_department(db, tenant.tenant_id, department_id)
    resp = DepartmentResponse.model_validate(dept)
    if dept.hod:
        resp.hod_name = f"{dept.hod.first_name} {dept.hod.last_name}"
    return ApiResponse(data=resp)


@router.patch("/{department_id}", response_model=ApiResponse[DepartmentResponse])
async def update_department(
    department_id: UUID,
    payload: DepartmentUpdateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CORE_DEPARTMENTS_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[DepartmentResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    dept = await CoreService.update_department(
        db, tenant.tenant_id, department_id, payload, user_id=current_user.id, ip_address=ip
    )
    resp = DepartmentResponse.model_validate(dept)
    if dept.hod:
        resp.hod_name = f"{dept.hod.first_name} {dept.hod.last_name}"
    return ApiResponse(data=resp)
