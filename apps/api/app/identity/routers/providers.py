"""Identity Provider Administrative Endpoints (Step 22)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_current_active_user, get_tenant_context, require_permission
from app.core.permissions import (
    IDENTITY_PROVIDERS_MANAGE,
    IDENTITY_PROVIDERS_READ,
    IDENTITY_PROVIDERS_TEST,
)
from app.core.tenant import TenantContext
from app.identity.models import IdentityProvider
from app.identity.schemas import (
    IdentityProviderCreate,
    IdentityProviderResponse,
    IdentityProviderTestResponse,
    IdentityProviderUpdate,
)
from app.identity.service import EnterpriseIdentityService
from app.models.people import User
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/providers", tags=["Identity Providers"])


def to_provider_response(p: IdentityProvider) -> IdentityProviderResponse:
    res = IdentityProviderResponse.model_validate(p)
    res.has_client_secret = bool(p.client_secret_reference)
    return res


@router.get("", response_model=ApiResponse[list[IdentityProviderResponse]])
async def list_identity_providers(
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(IDENTITY_PROVIDERS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[list[IdentityProviderResponse]]:
    """List all identity providers configured for the active tenant."""
    providers = await EnterpriseIdentityService.list_providers(db, tenant_context.tenant_id)
    responses = [to_provider_response(p) for p in providers]
    return ApiResponse(success=True, data=responses)


@router.post("", response_model=ApiResponse[IdentityProviderResponse], status_code=status.HTTP_201_CREATED)
async def create_identity_provider(
    payload: IdentityProviderCreate,
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(IDENTITY_PROVIDERS_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[IdentityProviderResponse]:
    """Create a new identity provider integration in DRAFT status."""
    provider = await EnterpriseIdentityService.create_provider(
        db, tenant_context.tenant_id, payload.model_dump()
    )
    return ApiResponse(
        success=True,
        data=to_provider_response(provider),
        message="Identity provider created in DRAFT status.",
    )


@router.get("/{provider_id}", response_model=ApiResponse[IdentityProviderResponse])
async def get_identity_provider(
    provider_id: UUID,
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(IDENTITY_PROVIDERS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[IdentityProviderResponse]:
    """Get identity provider details by ID."""
    provider = await EnterpriseIdentityService.get_provider(db, tenant_context.tenant_id, provider_id)
    return ApiResponse(
        success=True,
        data=to_provider_response(provider),
    )


@router.patch("/{provider_id}", response_model=ApiResponse[IdentityProviderResponse])
async def update_identity_provider(
    provider_id: UUID,
    payload: IdentityProviderUpdate,
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(IDENTITY_PROVIDERS_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[IdentityProviderResponse]:
    """Update identity provider configuration parameters."""
    provider = await EnterpriseIdentityService.update_provider(
        db, tenant_context.tenant_id, provider_id, payload.model_dump(exclude_unset=True)
    )
    return ApiResponse(
        success=True,
        data=to_provider_response(provider),
        message="Identity provider updated.",
    )


@router.post("/{provider_id}/activate", response_model=ApiResponse[IdentityProviderResponse])
async def activate_identity_provider(
    provider_id: UUID,
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(IDENTITY_PROVIDERS_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[IdentityProviderResponse]:
    """Activate an identity provider after validating required configuration."""
    provider = await EnterpriseIdentityService.activate_provider(
        db, tenant_context.tenant_id, provider_id
    )
    return ApiResponse(
        success=True,
        data=to_provider_response(provider),
        message="Identity provider activated.",
    )


@router.post("/{provider_id}/disable", response_model=ApiResponse[IdentityProviderResponse])
async def disable_identity_provider(
    provider_id: UUID,
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(IDENTITY_PROVIDERS_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[IdentityProviderResponse]:
    """Disable an active identity provider."""
    provider = await EnterpriseIdentityService.disable_provider(
        db, tenant_context.tenant_id, provider_id
    )
    return ApiResponse(
        success=True,
        data=to_provider_response(provider),
        message="Identity provider disabled.",
    )


@router.post("/{provider_id}/test", response_model=ApiResponse[IdentityProviderTestResponse])
async def test_identity_provider(
    provider_id: UUID,
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(IDENTITY_PROVIDERS_TEST))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[IdentityProviderTestResponse]:
    """Test outbound network reachability and health of provider endpoints with SSRF safety."""
    result = await EnterpriseIdentityService.test_provider_connectivity(
        db, tenant_context.tenant_id, provider_id
    )
    return ApiResponse(
        success=True,
        data=IdentityProviderTestResponse.model_validate(result),
        message=result["message"],
    )
