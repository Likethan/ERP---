"""Developer Applications Management API Router (Step 21).

Enforces:
- Registration, inspection, and updates of developer applications.
- Multi-step approval workflows (DRAFT -> SUBMITTED -> APPROVED -> ACTIVE).
- Strict tenant boundary isolation and PBAC authorization.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import require_permission
from app.models.people import User
from app.platform_api.schemas import (
    ApplicationApprovalRequest,
    ApplicationCreate,
    ApplicationResponse,
    ApplicationSubmitRequest,
    ApplicationUpdate,
)
from app.platform_api.service import platform_service

router = APIRouter(prefix="/platform/applications", tags=["API Platform - Applications"])


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_developer_application(
    data: ApplicationCreate,
    request: Request,
    current_user: Annotated[User, Depends(require_permission("api:applications:create"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApplicationResponse:
    """Register a new developer application."""
    tenant_ctx = getattr(request.state, "tenant", None)
    tenant_id = tenant_ctx.tenant_id if tenant_ctx else current_user.primary_tenant_id

    app = await platform_service.create_application(
        db=db,
        tenant_id=tenant_id,
        owner_id=current_user.id,
        data=data,
    )
    return ApplicationResponse.model_validate(app)


@router.get("", response_model=list[ApplicationResponse])
async def list_developer_applications(
    request: Request,
    current_user: Annotated[User, Depends(require_permission("api:applications:read"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[ApplicationResponse]:
    """List developer applications within tenant boundary."""
    tenant_ctx = getattr(request.state, "tenant", None)
    tenant_id = tenant_ctx.tenant_id if tenant_ctx else current_user.primary_tenant_id

    user_roles = {ur.role.name for ur in current_user.roles if ur.role}
    is_admin = "SUPER_ADMIN" in user_roles or "INSTITUTION_ADMIN" in user_roles

    apps = await platform_service.list_applications(
        db=db,
        tenant_id=tenant_id,
        owner_id=current_user.id,
        is_admin=is_admin,
    )
    return [ApplicationResponse.model_validate(a) for a in apps]


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_developer_application(
    application_id: UUID,
    request: Request,
    current_user: Annotated[User, Depends(require_permission("api:applications:read"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApplicationResponse:
    """Retrieve details for a developer application."""
    tenant_ctx = getattr(request.state, "tenant", None)
    tenant_id = tenant_ctx.tenant_id if tenant_ctx else current_user.primary_tenant_id

    user_roles = {ur.role.name for ur in current_user.roles if ur.role}
    is_admin = "SUPER_ADMIN" in user_roles or "INSTITUTION_ADMIN" in user_roles

    app = await platform_service.get_application(
        db=db,
        tenant_id=tenant_id,
        application_id=application_id,
        owner_id=current_user.id,
        is_admin=is_admin,
    )
    return ApplicationResponse.model_validate(app)


@router.patch("/{application_id}", response_model=ApplicationResponse)
async def update_developer_application(
    application_id: UUID,
    data: ApplicationUpdate,
    request: Request,
    current_user: Annotated[User, Depends(require_permission("api:applications:manage"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApplicationResponse:
    """Update developer application configuration."""
    tenant_ctx = getattr(request.state, "tenant", None)
    tenant_id = tenant_ctx.tenant_id if tenant_ctx else current_user.primary_tenant_id

    user_roles = {ur.role.name for ur in current_user.roles if ur.role}
    is_admin = "SUPER_ADMIN" in user_roles or "INSTITUTION_ADMIN" in user_roles

    app = await platform_service.update_application(
        db=db,
        tenant_id=tenant_id,
        application_id=application_id,
        data=data,
        user_id=current_user.id,
        is_admin=is_admin,
    )
    return ApplicationResponse.model_validate(app)


@router.post("/{application_id}/submit", response_model=ApplicationResponse)
async def submit_application_for_approval(
    application_id: UUID,
    request: Request,
    current_user: Annotated[User, Depends(require_permission("api:applications:create"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    body: ApplicationSubmitRequest | None = None,
) -> ApplicationResponse:
    """Submit a draft application for administrative approval."""
    tenant_ctx = getattr(request.state, "tenant", None)
    tenant_id = tenant_ctx.tenant_id if tenant_ctx else current_user.primary_tenant_id

    notes = body.notes if body else None
    app = await platform_service.submit_application(
        db=db,
        tenant_id=tenant_id,
        application_id=application_id,
        user_id=current_user.id,
        notes=notes,
    )
    return ApplicationResponse.model_validate(app)


@router.post("/{application_id}/approve", response_model=ApplicationResponse)
async def approve_developer_application(
    application_id: UUID,
    body: ApplicationApprovalRequest,
    request: Request,
    current_user: Annotated[User, Depends(require_permission("api:applications:approve"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApplicationResponse:
    """Administrator reviews and approves an application."""
    tenant_ctx = getattr(request.state, "tenant", None)
    tenant_id = tenant_ctx.tenant_id if tenant_ctx else current_user.primary_tenant_id

    if body.action.upper() == "APPROVE":
        app = await platform_service.approve_application(
            db=db,
            tenant_id=tenant_id,
            application_id=application_id,
            reviewer_id=current_user.id,
            notes=body.notes,
        )
    else:
        app = await platform_service.reject_application(
            db=db,
            tenant_id=tenant_id,
            application_id=application_id,
            reviewer_id=current_user.id,
            reason=body.notes,
        )
    return ApplicationResponse.model_validate(app)


@router.post("/{application_id}/suspend", response_model=ApplicationResponse)
async def suspend_developer_application(
    application_id: UUID,
    request: Request,
    current_user: Annotated[User, Depends(require_permission("api:applications:approve"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    reason: str | None = Query(None),
) -> ApplicationResponse:
    """Administrator suspends an application."""
    tenant_ctx = getattr(request.state, "tenant", None)
    tenant_id = tenant_ctx.tenant_id if tenant_ctx else current_user.primary_tenant_id

    app = await platform_service.suspend_application(
        db=db,
        tenant_id=tenant_id,
        application_id=application_id,
        reviewer_id=current_user.id,
        reason=reason,
    )
    return ApplicationResponse.model_validate(app)


@router.delete("/{application_id}", response_model=ApplicationResponse)
async def archive_developer_application(
    application_id: UUID,
    request: Request,
    current_user: Annotated[User, Depends(require_permission("api:applications:manage"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApplicationResponse:
    """Archive an application and revoke all its active credentials."""
    tenant_ctx = getattr(request.state, "tenant", None)
    tenant_id = tenant_ctx.tenant_id if tenant_ctx else current_user.primary_tenant_id

    user_roles = {ur.role.name for ur in current_user.roles if ur.role}
    is_admin = "SUPER_ADMIN" in user_roles or "INSTITUTION_ADMIN" in user_roles

    app = await platform_service.archive_application(
        db=db,
        tenant_id=tenant_id,
        application_id=application_id,
        user_id=current_user.id,
        is_admin=is_admin,
    )
    return ApplicationResponse.model_validate(app)
