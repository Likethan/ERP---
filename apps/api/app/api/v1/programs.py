"""Program API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_tenant_context, require_permission
from app.core.permissions import CORE_PROGRAMS_MANAGE, CORE_PROGRAMS_READ
from app.core.tenant import TenantContext
from app.models.people import User
from app.schemas.common import ApiResponse
from app.schemas.core import (
    ProgramCreateRequest,
    ProgramResponse,
    ProgramUpdateRequest,
)
from app.services.core_service import CoreService

router = APIRouter(prefix="/programs", tags=["Programs"])


@router.get("", response_model=ApiResponse[list[ProgramResponse]])
async def list_programs(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CORE_PROGRAMS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    department_id: UUID | None = Query(None),
    search: str | None = Query(None),
) -> ApiResponse[list[ProgramResponse]]:
    programs = await CoreService.list_programs(
        db, tenant.tenant_id, department_id=department_id, search=search
    )
    result = []
    for p in programs:
        resp = ProgramResponse.model_validate(p)
        if p.department:
            resp.department_name = p.department.name
        result.append(resp)
    return ApiResponse(data=result)


@router.post("", response_model=ApiResponse[ProgramResponse], status_code=status.HTTP_201_CREATED)
async def create_program(
    payload: ProgramCreateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CORE_PROGRAMS_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[ProgramResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    program = await CoreService.create_program(
        db, tenant.tenant_id, payload, user_id=current_user.id, ip_address=ip
    )
    resp = ProgramResponse.model_validate(program)
    if program.department:
        resp.department_name = program.department.name
    return ApiResponse(data=resp)


@router.get("/{program_id}", response_model=ApiResponse[ProgramResponse])
async def get_program(
    program_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CORE_PROGRAMS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[ProgramResponse]:
    program = await CoreService.get_program(db, tenant.tenant_id, program_id)
    resp = ProgramResponse.model_validate(program)
    if program.department:
        resp.department_name = program.department.name
    return ApiResponse(data=resp)


@router.patch("/{program_id}", response_model=ApiResponse[ProgramResponse])
async def update_program(
    program_id: UUID,
    payload: ProgramUpdateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CORE_PROGRAMS_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[ProgramResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    program = await CoreService.update_program(
        db, tenant.tenant_id, program_id, payload, user_id=current_user.id, ip_address=ip
    )
    resp = ProgramResponse.model_validate(program)
    if program.department:
        resp.department_name = program.department.name
    return ApiResponse(data=resp)
