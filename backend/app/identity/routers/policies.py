"""Tenant Identity Policy Endpoints (Step 22)."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_tenant_context, require_permission
from app.core.permissions import IDENTITY_POLICIES_MANAGE, IDENTITY_POLICIES_READ
from app.core.tenant import TenantContext
from app.identity.policy_service import TenantIdentityPolicyService
from app.identity.schemas import (
    TenantIdentityPolicyResponse,
    TenantIdentityPolicyUpdate,
)
from app.models.people import User
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/policies", tags=["Tenant Identity Policies"])


@router.get("", response_model=ApiResponse[TenantIdentityPolicyResponse])
async def get_tenant_identity_policy(
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(IDENTITY_POLICIES_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[TenantIdentityPolicyResponse]:
    """Retrieve identity, password, session, and MFA policy configuration for the tenant."""
    policy = await TenantIdentityPolicyService.get_policy(db, tenant_context.tenant_id)
    return ApiResponse(
        success=True,
        data=TenantIdentityPolicyResponse.model_validate(policy),
    )


@router.patch("", response_model=ApiResponse[TenantIdentityPolicyResponse])
async def update_tenant_identity_policy(
    payload: TenantIdentityPolicyUpdate,
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(IDENTITY_POLICIES_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[TenantIdentityPolicyResponse]:
    """Update tenant identity, session, and password policy settings."""
    policy = await TenantIdentityPolicyService.update_policy(
        db,
        tenant_context.tenant_id,
        payload.model_dump(exclude_unset=True),
    )
    return ApiResponse(
        success=True,
        data=TenantIdentityPolicyResponse.model_validate(policy),
        message="Tenant identity policy updated successfully.",
    )
