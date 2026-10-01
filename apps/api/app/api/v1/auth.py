"""Authentication and identity endpoints for CampusOS."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db_session
from app.core.deps import get_current_active_user, resolve_user_permissions
from app.core.security import (
    ACCESS_TOKEN_COOKIE_NAME,
    REFRESH_TOKEN_COOKIE_NAME,
    AuthenticationException,
)
from app.core.tenant import get_optional_tenant_context
from app.models.core import Institution
from app.models.people import User
from app.schemas.auth import (
    AuthRoleInfo,
    AuthTenantInfo,
    ChangePasswordRequest,
    CurrentUserResponse,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    ResetPasswordRequest,
    UserResponse,
)
from app.schemas.common import ApiResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication & Identity"])


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Set secure, HttpOnly authentication cookies on HTTP response."""
    is_secure = settings.ENVIRONMENT == "production"

    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    """Remove authentication cookies."""
    response.delete_cookie(key=ACCESS_TOKEN_COOKIE_NAME, path="/")
    response.delete_cookie(key=REFRESH_TOKEN_COOKIE_NAME, path="/")


def _build_user_response(
    user: User, tenant_info: AuthTenantInfo | None = None
) -> UserResponse:
    """Serialize User ORM entity into safe UserResponse schema."""
    roles_info = [
        AuthRoleInfo(
            id=ur.role.id,
            name=ur.role.name,
            display_name=ur.role.display_name,
            campus_id=ur.campus_id,
            department_id=ur.department_id,
        )
        for ur in user.roles
        if ur.role
    ]
    permissions = sorted(resolve_user_permissions(user))

    return UserResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        status=user.status,
        roles=roles_info,
        permissions=permissions,
        tenant=tenant_info,
    )


@router.post(
    "/login",
    response_model=ApiResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and establish session",
)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[UserResponse]:
    """Authenticate credentials, establish session, and set HttpOnly cookies."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent")

    user, access_token, refresh_token = await AuthService.authenticate_user(
        db=db,
        email=payload.email,
        password=payload.password,
        client_ip=client_ip,
        user_agent=user_agent,
    )

    tenant_info = None
    if user.primary_tenant_id:
        tenant_res = await db.execute(
            select(Institution).where(Institution.id == user.primary_tenant_id)
        )
        inst = tenant_res.scalar_one_or_none()
        if inst:
            tenant_info = AuthTenantInfo(
                id=inst.id,
                code=inst.code,
                name=inst.legal_name,
            )

    _set_auth_cookies(response, access_token, refresh_token)
    return ApiResponse(data=_build_user_response(user, tenant_info=tenant_info))


@router.post(
    "/logout",
    response_model=ApiResponse[MessageResponse],
    summary="Revoke session and clear authentication cookies",
)
async def logout(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> ApiResponse[MessageResponse]:
    """Invalidate current session and remove client cookies."""
    refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE_NAME)
    client_ip = request.client.host if request.client else "127.0.0.1"

    await AuthService.logout_user(
        db=db,
        user_id=current_user.id,
        refresh_token=refresh_token,
        client_ip=client_ip,
    )

    _clear_auth_cookies(response)
    return ApiResponse(data=MessageResponse(message="Successfully logged out."))


@router.get(
    "/me",
    response_model=ApiResponse[CurrentUserResponse],
    summary="Retrieve current authenticated identity and permissions",
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> ApiResponse[CurrentUserResponse]:
    """Return safe identity representation, roles, permissions, and tenant context."""
    tenant_ctx = get_optional_tenant_context()
    tenant_info = (
        AuthTenantInfo(
            id=tenant_ctx.tenant_id,
            code=tenant_ctx.code,
            name=tenant_ctx.name,
        )
        if tenant_ctx
        else None
    )

    return ApiResponse(
        data=_build_user_response(current_user, tenant_info=tenant_info)
    )


@router.post(
    "/refresh",
    response_model=ApiResponse[UserResponse],
    summary="Rotate refresh token and issue new access token",
)
async def refresh_token_endpoint(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[UserResponse]:
    """Rotate tokens using valid HttpOnly refresh cookie."""
    refresh_token = request.cookies.get(REFRESH_TOKEN_COOKIE_NAME)
    if not refresh_token:
        # Fallback to Authorization header if provided
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            refresh_token = auth_header[7:].strip()

    if not refresh_token:
        raise AuthenticationException("No refresh token provided.")

    client_ip = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent")

    user, new_access, new_refresh = await AuthService.refresh_user_session(
        db=db,
        refresh_token=refresh_token,
        client_ip=client_ip,
        user_agent=user_agent,
    )

    tenant_info = None
    if user.primary_tenant_id:
        tenant_res = await db.execute(
            select(Institution).where(Institution.id == user.primary_tenant_id)
        )
        inst = tenant_res.scalar_one_or_none()
        if inst:
            tenant_info = AuthTenantInfo(
                id=inst.id,
                code=inst.code,
                name=inst.legal_name,
            )

    _set_auth_cookies(response, new_access, new_refresh)
    return ApiResponse(data=_build_user_response(user, tenant_info=tenant_info))


@router.post(
    "/change-password",
    response_model=ApiResponse[MessageResponse],
    summary="Change authenticated user password",
)
async def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    response: Response,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[MessageResponse]:
    """Verify current password, validate complexity, and update hash."""
    client_ip = request.client.host if request.client else "127.0.0.1"

    await AuthService.change_password(
        db=db,
        user=current_user,
        current_password=payload.current_password,
        new_password=payload.new_password,
        confirm_password=payload.confirm_password,
        client_ip=client_ip,
    )

    _clear_auth_cookies(response)
    return ApiResponse(
        data=MessageResponse(message="Password successfully changed. Please log in again.")
    )


@router.post(
    "/forgot-password",
    response_model=ApiResponse[MessageResponse],
    summary="Request a time-limited password reset link",
)
async def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[MessageResponse]:
    """Issue password reset token without disclosing user account existence."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    await AuthService.request_password_reset(db=db, email=payload.email, client_ip=client_ip)

    return ApiResponse(
        data=MessageResponse(
            message=(
                "If an active institutional account exists for that email, "
                "password reset instructions have been dispatched."
            )
        )
    )


@router.post(
    "/reset-password",
    response_model=ApiResponse[MessageResponse],
    summary="Complete password reset using one-time token",
)
async def reset_password(
    payload: ResetPasswordRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[MessageResponse]:
    """Reset password using verified one-time token."""
    client_ip = request.client.host if request.client else "127.0.0.1"

    await AuthService.reset_password(
        db=db,
        token=payload.token,
        new_password=payload.new_password,
        confirm_password=payload.confirm_password,
        client_ip=client_ip,
    )

    return ApiResponse(
        data=MessageResponse(message="Password has been reset successfully. You may now log in.")
    )
