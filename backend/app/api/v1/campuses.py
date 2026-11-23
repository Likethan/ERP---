"""Campus API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_tenant_context, require_permission
from app.core.permissions import CORE_CAMPUSES_MANAGE, CORE_CAMPUSES_READ
from app.core.tenant import TenantContext
from app.models.people import User
from app.schemas.common import ApiResponse
from app.schemas.core import CampusCreateRequest, CampusResponse, CampusUpdateRequest
from app.services.core_service import CoreService

router = APIRouter(prefix="/campuses", tags=["Campuses"])


@router.get("", response_model=ApiResponse[list[CampusResponse]])
async def list_campuses(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CORE_CAMPUSES_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[list[CampusResponse]]:
    campuses = await CoreService.list_campuses(db, tenant.tenant_id)
    return ApiResponse(data=[CampusResponse.model_validate(c) for c in campuses])


@router.post("", response_model=ApiResponse[CampusResponse], status_code=status.HTTP_201_CREATED)
async def create_campus(
    payload: CampusCreateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CORE_CAMPUSES_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CampusResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    campus = await CoreService.create_campus(
        db, tenant.tenant_id, payload, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=CampusResponse.model_validate(campus))


@router.get("/{campus_id}", response_model=ApiResponse[CampusResponse])
async def get_campus(
    campus_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CORE_CAMPUSES_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CampusResponse]:
    campus = await CoreService.get_campus(db, tenant.tenant_id, campus_id)
    return ApiResponse(data=CampusResponse.model_validate(campus))


@router.patch("/{campus_id}", response_model=ApiResponse[CampusResponse])
async def update_campus(
    campus_id: UUID,
    payload: CampusUpdateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CORE_CAMPUSES_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CampusResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    campus = await CoreService.update_campus(
        db, tenant.tenant_id, campus_id, payload, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=CampusResponse.model_validate(campus))
