"""External Identity & Account Linking Endpoints (Step 22)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_current_active_user, get_tenant_context
from app.core.tenant import TenantContext
from app.identity.schemas import (
    AccountLinkConfirmRequest,
    AccountLinkInitiateRequest,
    AccountLinkInitiateResponse,
    ExternalIdentityResponse,
)
from app.identity.service import EnterpriseIdentityService
from app.models.people import User
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/identities", tags=["External Identity Linking"])


@router.get("", response_model=ApiResponse[list[ExternalIdentityResponse]])
async def list_linked_identities(
    current_user: Annotated[User, Depends(get_current_active_user)],
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[list[ExternalIdentityResponse]]:
    """List external federated identities linked to the current user account."""
    identities = await EnterpriseIdentityService.list_user_external_identities(
        db, tenant_context.tenant_id, current_user.id
    )
    return ApiResponse(
        success=True,
        data=[ExternalIdentityResponse.model_validate(i) for i in identities],
    )


@router.post("/link/initiate", response_model=ApiResponse[AccountLinkInitiateResponse])
async def initiate_account_link(
    payload: AccountLinkInitiateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AccountLinkInitiateResponse]:
    """Initiate a secure account linking challenge to link an external SSO identity."""
    res = await EnterpriseIdentityService.initiate_account_link(
        db,
        tenant_id=tenant_context.tenant_id,
        user_id=current_user.id,
        provider_id=payload.provider_id,
        subject=payload.subject,
        external_email=payload.external_email,
    )
    return ApiResponse(
        success=True,
        data=AccountLinkInitiateResponse.model_validate(res),
        message=res["message"],
    )


@router.post("/link/confirm", response_model=ApiResponse[ExternalIdentityResponse])
async def confirm_account_link(
    payload: AccountLinkConfirmRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[ExternalIdentityResponse]:
    """Confirm account link with challenge token and user password verification."""
    ext = await EnterpriseIdentityService.confirm_account_link(
        db,
        tenant_id=tenant_context.tenant_id,
        user=current_user,
        link_token=payload.link_token,
        current_password=payload.current_password,
    )
    return ApiResponse(
        success=True,
        data=ExternalIdentityResponse.model_validate(ext),
        message="External identity successfully linked.",
    )


@router.delete("/{external_identity_id}", response_model=ApiResponse[dict[str, str]])
async def unlink_external_identity(
    external_identity_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[dict[str, str]]:
    """Unlink an external identity while ensuring another authentication method exists."""
    await EnterpriseIdentityService.unlink_external_identity(
        db,
        tenant_id=tenant_context.tenant_id,
        user=current_user,
        external_identity_id=external_identity_id,
    )
    return ApiResponse(
        success=True,
        data={"status": "UNLINKED"},
        message="External identity successfully unlinked.",
    )
