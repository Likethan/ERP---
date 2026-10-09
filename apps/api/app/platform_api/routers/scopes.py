"""Capability Scopes & Permissions API Router (Step 21).

Enforces:
- Scope registry discovery and risk categorization.
- Capability-based scope requests.
- Administrative approval workflow for high-risk and critical scopes.
- Immediate scope revocation.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import require_permission
from app.models.people import User
from app.platform_api.schemas import (
    ScopeApprovalRequest,
    ScopeDefinitionResponse,
    ScopeGrantResponse,
    ScopeRequest,
)
from app.platform_api.scopes import API_SCOPE_REGISTRY
from app.platform_api.service import platform_service

router = APIRouter(prefix="/platform", tags=["API Platform - Scopes"])


@router.get("/scopes", response_model=list[ScopeDefinitionResponse])
async def list_available_scopes(
    current_user: Annotated[User, Depends(require_permission("api:applications:read"))],
) -> list[ScopeDefinitionResponse]:
    """Discover all capability-based API scopes supported by the platform."""
    return [
        ScopeDefinitionResponse(
            code=s.code,
            domain=s.domain,
            description=s.description,
            risk_level=s.risk_level,
            requires_approval=s.requires_approval,
            implied_scopes=list(s.implied_scopes),
        )
        for s in API_SCOPE_REGISTRY.values()
    ]


@router.post(
    "/applications/{application_id}/scopes",
    response_model=list[ScopeGrantResponse],
    status_code=status.HTTP_201_CREATED,
)
async def request_application_scopes(
    application_id: UUID,
    body: ScopeRequest,
    request: Request,
    current_user: Annotated[User, Depends(require_permission("api:scopes:manage"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[ScopeGrantResponse]:
    """Request capability scopes for an application. High-risk scopes require admin review."""
    tenant_ctx = getattr(request.state, "tenant", None)
    tenant_id = tenant_ctx.tenant_id if tenant_ctx else current_user.primary_tenant_id

    user_roles = {ur.role.name for ur in current_user.roles if ur.role}
    is_admin = "SUPER_ADMIN" in user_roles or "INSTITUTION_ADMIN" in user_roles

    grants = await platform_service.request_scopes(
        db=db,
        tenant_id=tenant_id,
        application_id=application_id,
        scope_codes=body.scopes,
        user_id=current_user.id,
        justification=body.justification,
        is_admin=is_admin,
    )
    return [ScopeGrantResponse.model_validate(g) for g in grants]


@router.get("/applications/{application_id}/scopes", response_model=list[ScopeGrantResponse])
async def list_application_scopes(
    application_id: UUID,
    request: Request,
    current_user: Annotated[User, Depends(require_permission("api:applications:read"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[ScopeGrantResponse]:
    """List granted and pending capability scopes for an application."""
    tenant_ctx = getattr(request.state, "tenant", None)
    tenant_id = tenant_ctx.tenant_id if tenant_ctx else current_user.primary_tenant_id

    user_roles = {ur.role.name for ur in current_user.roles if ur.role}
    is_admin = "SUPER_ADMIN" in user_roles or "INSTITUTION_ADMIN" in user_roles

    grants = await platform_service.list_scopes(
        db=db,
        tenant_id=tenant_id,
        application_id=application_id,
        user_id=current_user.id,
        is_admin=is_admin,
    )
    return [ScopeGrantResponse.model_validate(g) for g in grants]


@router.post(
    "/applications/{application_id}/scopes/{grant_id}/approve", response_model=ScopeGrantResponse
)
async def approve_application_scope(
    application_id: UUID,
    grant_id: UUID,
    body: ScopeApprovalRequest,
    request: Request,
    current_user: Annotated[User, Depends(require_permission("api:applications:approve"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ScopeGrantResponse:
    """Administrator approves or rejects a high-risk capability scope grant."""
    tenant_ctx = getattr(request.state, "tenant", None)
    tenant_id = tenant_ctx.tenant_id if tenant_ctx else current_user.primary_tenant_id

    if body.action.upper() == "APPROVE":
        grant = await platform_service.approve_scope(
            db=db,
            tenant_id=tenant_id,
            application_id=application_id,
            grant_id=grant_id,
            reviewer_id=current_user.id,
            notes=body.notes,
        )
    else:
        grant = await platform_service.revoke_scope(
            db=db,
            tenant_id=tenant_id,
            application_id=application_id,
            grant_id=grant_id,
            reviewer_id=current_user.id,
        )
    return ScopeGrantResponse.model_validate(grant)


@router.delete(
    "/applications/{application_id}/scopes/{grant_id}", response_model=ScopeGrantResponse
)
async def revoke_application_scope(
    application_id: UUID,
    grant_id: UUID,
    request: Request,
    current_user: Annotated[User, Depends(require_permission("api:scopes:manage"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ScopeGrantResponse:
    """Revoke a capability scope grant."""
    tenant_ctx = getattr(request.state, "tenant", None)
    tenant_id = tenant_ctx.tenant_id if tenant_ctx else current_user.primary_tenant_id

    grant = await platform_service.revoke_scope(
        db=db,
        tenant_id=tenant_id,
        application_id=application_id,
        grant_id=grant_id,
        reviewer_id=current_user.id,
    )
    return ScopeGrantResponse.model_validate(grant)
