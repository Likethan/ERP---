"""Institution API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_tenant_context, require_permission
from app.core.permissions import CORE_INSTITUTION_MANAGE, CORE_INSTITUTION_READ
from app.core.tenant import TenantContext
from app.models.people import User
from app.schemas.common import ApiResponse
from app.schemas.core import InstitutionResponse, InstitutionUpdateRequest
from app.services.core_service import CoreService

router = APIRouter(prefix="/institutions", tags=["Institutions"])


@router.get("", response_model=ApiResponse[InstitutionResponse])
async def get_current_institution(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CORE_INSTITUTION_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[InstitutionResponse]:
    institution = await CoreService.get_institution(db, tenant.tenant_id)
    return ApiResponse(data=InstitutionResponse.model_validate(institution))


@router.patch("/{institution_id}", response_model=ApiResponse[InstitutionResponse])
async def update_institution(
    institution_id: UUID,
    payload: InstitutionUpdateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CORE_INSTITUTION_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[InstitutionResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    institution = await CoreService.update_institution(
        db, tenant.tenant_id, payload, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=InstitutionResponse.model_validate(institution))
