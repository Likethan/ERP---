"""FastAPI dependencies for authentication, tenant context, and PBAC authorization."""

from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db_session
from app.core.exceptions import (
    PermissionDeniedException,
    TenantArchivedException,
    TenantSuspendedException,
)
from app.core.security import (
    ACCESS_TOKEN_COOKIE_NAME,
    AccountDisabledException,
    AccountLockedException,
    AuthenticationException,
    decode_token,
)
from app.core.tenant import (
    TenantContext,
    get_current_tenant_context,
    set_current_tenant_context,
)
from app.models.core import Institution, TenantMembership
from app.models.people import Role, RolePermission, User, UserRoleAssignment


def get_token_from_request(request: Request) -> str:
    """Extract JWT token from HttpOnly cookie or Authorization header."""
    # 1. Check HttpOnly cookie first (preferred browser channel)
    cookie_token = request.cookies.get(ACCESS_TOKEN_COOKIE_NAME)
    if cookie_token:
        return cookie_token

    # 2. Check Authorization header (for programmatic / mobile clients)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    raise AuthenticationException("Authentication required. No credentials provided.")


async def get_current_user(
    request: Request,
    token: Annotated[str, Depends(get_token_from_request)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> User:
    """Validate access token, load user from DB with roles and set tenant context."""
    payload = decode_token(token, expected_type="access")
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise AuthenticationException("Token payload missing subject identifier.")

    try:
        user_id = UUID(user_id_str)
    except ValueError as exc:
        raise AuthenticationException("Invalid user identifier in token.") from exc

    stmt = (
        select(User)
        .options(
            selectinload(User.roles)
            .selectinload(UserRoleAssignment.role)
            .selectinload(Role.permissions)
            .selectinload(RolePermission.permission)
        )
        .where(User.id == user_id)
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise AuthenticationException("User account associated with this token does not exist.")

    # Flatten user roles and permissions
    user_roles_list = tuple(sorted(ur.role.name for ur in user.roles if ur.role and ur.role.name))
    user_perms_list = tuple(sorted(resolve_user_permissions(user)))
    is_super_admin = "SUPER_ADMIN" in user_roles_list or "*" in user_perms_list

    # Resolve tenant context securely from token or primary membership
    token_tenant_id_str = payload.get("tenant_id")
    tenant_id = UUID(token_tenant_id_str) if token_tenant_id_str else user.primary_tenant_id

    if tenant_id:
        # Validate that user actually holds authoritative membership for this tenant
        has_membership = (user.primary_tenant_id == tenant_id) or is_super_admin
        if not has_membership:
            mem_stmt = select(TenantMembership).where(
                TenantMembership.tenant_id == tenant_id,
                TenantMembership.user_id == user.id,
                TenantMembership.status == "ACTIVE",
            )
            mem_res = await db.execute(mem_stmt)
            if mem_res.scalar_one_or_none() is not None:
                has_membership = True

        if not has_membership:
            raise AuthenticationException("User does not have authorized membership in the requested tenant.")

        tenant_stmt = select(Institution).where(Institution.id == tenant_id)
        tenant_res = await db.execute(tenant_stmt)
        institution = tenant_res.scalar_one_or_none()
        if institution:
            # Enforce tenant lifecycle status for non-superadmins
            tenant_status = (institution.status or "ACTIVE").upper()
            if not is_super_admin:
                if tenant_status == "SUSPENDED":
                    raise TenantSuspendedException(institution.id)
                if tenant_status == "ARCHIVED" or not institution.is_active:
                    raise TenantArchivedException(institution.id)

            tenant_ctx = TenantContext(
                tenant_id=institution.id,
                code=institution.code,
                name=institution.legal_name,
                is_active=institution.is_active,
                user_id=user.id,
                roles=user_roles_list,
                permissions=user_perms_list,
                tenant_status=tenant_status,
                slug=institution.slug,
                plan=institution.plan or "ENTERPRISE",
                timezone=institution.default_timezone or "Asia/Kolkata",
                currency=institution.currency_code or "INR",
                locale=institution.locale or "en-IN",
            )
            set_current_tenant_context(tenant_ctx)
            request.state.tenant = tenant_ctx

    request.state.user = user
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Ensure user account is active, verified, and not locked or suspended."""
    if not current_user.is_active:
        raise AccountDisabledException("User account is deactivated.")

    if current_user.status == "LOCKED":
        raise AccountLockedException("Account is locked due to security policy.")

    if current_user.status in ("SUSPENDED", "DISABLED"):
        raise AccountDisabledException(f"Account is {current_user.status.lower()}.")

    return current_user


def resolve_user_permissions(user: User) -> set[str]:
    """Extract flattened set of distinct permission codes granted to the user."""
    perms: set[str] = set()
    for user_role in user.roles:
        if user_role.role and user_role.role.permissions:
            for rp in user_role.role.permissions:
                if rp.permission and rp.permission.code:
                    perms.add(rp.permission.code)
    return perms


def require_permission(permission_code: str) -> Callable:
    """Dependency factory enforcing atomic PBAC permission check."""

    async def _permission_dependency(
        user: Annotated[User, Depends(get_current_active_user)],
    ) -> User:
        user_permissions = resolve_user_permissions(user)
        # SUPER_ADMIN wildcard check or exact permission
        alt_perm = permission_code.replace(".", ":") if "." in permission_code else permission_code.replace(":", ".")
        if "*" in user_permissions or permission_code in user_permissions or alt_perm in user_permissions:
            return user

        # Check if user has SUPER_ADMIN role directly
        user_roles = {ur.role.name for ur in user.roles if ur.role}
        if "SUPER_ADMIN" in user_roles:
            return user

        raise PermissionDeniedException(permission_code)

    return _permission_dependency


def require_permissions(permission_codes: list[str]) -> Callable:
    """Dependency factory enforcing all listed permissions."""

    async def _permissions_dependency(
        user: Annotated[User, Depends(get_current_active_user)],
    ) -> User:
        user_permissions = resolve_user_permissions(user)
        user_roles = {ur.role.name for ur in user.roles if ur.role}
        if "SUPER_ADMIN" in user_roles or "*" in user_permissions:
            return user

        for perm in permission_codes:
            if perm not in user_permissions:
                raise PermissionDeniedException(perm)
        return user

    return _permissions_dependency


async def get_tenant_context(
    user: Annotated[User, Depends(get_current_active_user)],
) -> TenantContext:
    """Retrieve verified tenant context after active user authentication."""
    return get_current_tenant_context()


async def require_platform_admin(
    user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """Ensure authenticated user has Platform Super Admin rights for global/SaaS ops."""
    user_roles = {ur.role.name for ur in user.roles if ur.role and ur.role.name}
    user_perms = resolve_user_permissions(user)
    if "SUPER_ADMIN" in user_roles or "*" in user_perms or "platform:tenants:manage" in user_perms or "platform.tenants.manage" in user_perms:
        return user
    raise PermissionDeniedException("platform:tenants:manage")

