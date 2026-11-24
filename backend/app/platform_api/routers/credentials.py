"""Application Credentials & Safe Rotation API Router (Step 21).

Enforces:
- Issuance of cryptographically secure API keys.
- One-time disclosure of raw secrets upon generation.
- Never returning plaintext secrets on inspection listings.
- Safe credential rotation with overlapping grace period windows.
- Immediate revocation enforcement.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import require_permission
from app.models.people import User
from app.platform_api.schemas import (
    CredentialCreate,
    CredentialCreatedResponse,
    CredentialResponse,
    CredentialRotateRequest,
    CredentialRotateResponse,
)
from app.platform_api.service import platform_service

router = APIRouter(
    prefix="/platform/applications/{application_id}/credentials",
    tags=["API Platform - Credentials"],
)


@router.post("", response_model=CredentialCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_credential(
    application_id: UUID,
    data: CredentialCreate,
    request: Request,
    current_user: Annotated[User, Depends(require_permission("api:credentials:create"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> CredentialCreatedResponse:
    """Generate and issue a new API credential.

    CRITICAL: The raw secret is returned ONLY ONCE in this response.
    Save it securely; it cannot be retrieved again.
    """
    tenant_ctx = getattr(request.state, "tenant", None)
    tenant_id = tenant_ctx.tenant_id if tenant_ctx else current_user.primary_tenant_id

    user_roles = {ur.role.name for ur in current_user.roles if ur.role}
    is_admin = "SUPER_ADMIN" in user_roles or "INSTITUTION_ADMIN" in user_roles

    cred, raw_secret = await platform_service.create_credential(
        db=db,
        tenant_id=tenant_id,
        application_id=application_id,
        data=data,
        user_id=current_user.id,
        is_admin=is_admin,
    )
    return CredentialCreatedResponse(
        credential=CredentialResponse.model_validate(cred),
        raw_secret=raw_secret,
    )


@router.get("", response_model=list[CredentialResponse])
async def list_credentials(
    application_id: UUID,
    request: Request,
    current_user: Annotated[User, Depends(require_permission("api:applications:read"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[CredentialResponse]:
    """List issued credentials for an application. Plaintext secrets are NEVER included."""
    tenant_ctx = getattr(request.state, "tenant", None)
    tenant_id = tenant_ctx.tenant_id if tenant_ctx else current_user.primary_tenant_id

    user_roles = {ur.role.name for ur in current_user.roles if ur.role}
    is_admin = "SUPER_ADMIN" in user_roles or "INSTITUTION_ADMIN" in user_roles

    creds = await platform_service.list_credentials(
        db=db,
        tenant_id=tenant_id,
        application_id=application_id,
        user_id=current_user.id,
        is_admin=is_admin,
    )
    return [CredentialResponse.model_validate(c) for c in creds]


@router.post("/{credential_id}/rotate", response_model=CredentialRotateResponse)
async def rotate_credential(
    application_id: UUID,
    credential_id: UUID,
    body: CredentialRotateRequest,
    request: Request,
    current_user: Annotated[User, Depends(require_permission("api:credentials:rotate"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> CredentialRotateResponse:
    """Execute a safe credential rotation.

    The existing credential enters ROTATING status for the configured overlap window (default 24h),
    allowing seamless client migration without downtime.
    """
    tenant_ctx = getattr(request.state, "tenant", None)
    tenant_id = tenant_ctx.tenant_id if tenant_ctx else current_user.primary_tenant_id

    user_roles = {ur.role.name for ur in current_user.roles if ur.role}
    is_admin = "SUPER_ADMIN" in user_roles or "INSTITUTION_ADMIN" in user_roles

    old_cred, new_cred, raw_new_secret = await platform_service.rotate_credential(
        db=db,
        tenant_id=tenant_id,
        application_id=application_id,
        credential_id=credential_id,
        overlap_hours=body.overlap_hours,
        user_id=current_user.id,
        is_admin=is_admin,
    )
    return CredentialRotateResponse(
        retiring_credential=CredentialResponse.model_validate(old_cred),
        active_credential=CredentialResponse.model_validate(new_cred),
        raw_secret=raw_new_secret,
    )


@router.delete("/{credential_id}", response_model=CredentialResponse)
async def revoke_credential(
    application_id: UUID,
    credential_id: UUID,
    request: Request,
    current_user: Annotated[User, Depends(require_permission("api:credentials:revoke"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    reason: str | None = Query(None),
) -> CredentialResponse:
    """Immediately revoke an API credential, preventing all further authentication."""
    tenant_ctx = getattr(request.state, "tenant", None)
    tenant_id = tenant_ctx.tenant_id if tenant_ctx else current_user.primary_tenant_id

    user_roles = {ur.role.name for ur in current_user.roles if ur.role}
    is_admin = "SUPER_ADMIN" in user_roles or "INSTITUTION_ADMIN" in user_roles

    cred = await platform_service.revoke_credential(
        db=db,
        tenant_id=tenant_id,
        application_id=application_id,
        credential_id=credential_id,
        reason=reason,
        user_id=current_user.id,
        is_admin=is_admin,
    )
    return CredentialResponse.model_validate(cred)
