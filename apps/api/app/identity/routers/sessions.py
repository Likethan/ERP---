"""Session Visibility and Revocation Endpoints (Step 22)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_current_active_user, get_tenant_context
from app.core.tenant import TenantContext
from app.identity.schemas import (
    RevokeAllSessionsResponse,
    RevokeSessionResponse,
    SessionResponse,
)
from app.identity.session_service import IdentitySessionService
from app.models.people import User
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/sessions", tags=["Session Management"])


@router.get("", response_model=ApiResponse[list[SessionResponse]])
async def list_user_sessions(
    current_user: Annotated[User, Depends(get_current_active_user)],
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[list[SessionResponse]]:
    """List all active sessions for the current authenticated user with device and IP visibility."""
    sessions = await IdentitySessionService.list_user_sessions(
        db,
        user_id=current_user.id,
        tenant_id=tenant_context.tenant_id,
    )
    return ApiResponse(
        success=True,
        data=[SessionResponse.model_validate(s) for s in sessions],
    )


@router.post("/{session_id}/revoke", response_model=ApiResponse[RevokeSessionResponse])
async def revoke_session(
    session_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[RevokeSessionResponse]:
    """Revoke a specific session. Users may revoke their own sessions; admins can revoke tenant sessions."""
    # Check if user is admin or revoking their own
    is_admin = any(
        ur.role.name in ("SUPER_ADMIN", "INSTITUTION_ADMIN", "ADMIN")
        for ur in current_user.roles
        if ur.role
    )
    user_constraint = None if is_admin else current_user.id

    revoked = await IdentitySessionService.revoke_session(
        db,
        session_id=session_id,
        user_id=user_constraint,
        tenant_id=tenant_context.tenant_id,
        reason="USER_REVOCATION" if not is_admin else "ADMIN_REVOCATION",
    )
    await db.commit()

    return ApiResponse(
        success=True,
        data=RevokeSessionResponse(
            revoked_session_id=revoked.id,
            status=revoked.status,
            message="Session successfully revoked.",
        ),
        message="Session revoked.",
    )


@router.post("/revoke-all", response_model=ApiResponse[RevokeAllSessionsResponse])
async def revoke_all_sessions(
    current_user: Annotated[User, Depends(get_current_active_user)],
    tenant_context: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[RevokeAllSessionsResponse]:
    """Revoke all active sessions for the authenticated user across all devices."""
    count = await IdentitySessionService.revoke_all_user_sessions(
        db,
        user_id=current_user.id,
        tenant_id=tenant_context.tenant_id,
        reason="USER_REVOKE_ALL",
    )
    await db.commit()

    return ApiResponse(
        success=True,
        data=RevokeAllSessionsResponse(
            revoked_count=count,
            message=f"Successfully revoked {count} active session(s).",
        ),
        message="All sessions revoked.",
    )
