"""Enterprise API Platform Dependency Pipeline (Step 21).

Enforces:
1. Credential Authentication (X-API-Key or Authorization Bearer)
2. Application Lifecycle Validation (ACTIVE/APPROVED status, IP Allowlist)
3. Tenant Boundary & Lifecycle Enforcement (Active, Not Suspended/Archived)
4. Capability Scope Fulfillment (Scoped capability grants via ScopeResolver)
5. Principal Identity & PBAC Authorization (Owner cannot exceed institutional permissions)
6. Sliding Window Rate Limiting (Per-application tiering)
7. Multi-Period Aggregate Quota Enforcement (Daily/monthly caps)
8. Response Correlation & Deprecation Headers
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db_session
from app.core.deps import resolve_user_permissions
from app.core.exceptions import (
    CampusOSException,
    PermissionDeniedException,
    TenantArchivedException,
    TenantSuspendedException,
)
from app.core.security import (
    AccountDisabledException,
    AccountLockedException,
    AuthenticationException,
)
from app.core.tenant import TenantContext, set_current_tenant_context
from app.models.core import Institution
from app.models.people import Role, RolePermission, User, UserRoleAssignment
from app.platform_api.auth import is_credential_valid_for_auth, verify_credential_secret
from app.platform_api.catalog import catalog_service
from app.platform_api.models import (
    ApplicationCredential,
    ApplicationStatus,
    CredentialStatus,
    DeveloperApplication,
    ScopeGrantStatus,
)
from app.platform_api.quotas import quota_service
from app.platform_api.rate_limits import app_rate_limiter
from app.platform_api.scopes import scope_resolver


@dataclass(frozen=True)
class ApiConsumerContext:
    """Authoritative execution context for an authenticated external API consumer."""

    tenant_id: UUID
    application_id: UUID
    credential_id: UUID
    client_id: str
    application: DeveloperApplication
    credential: ApplicationCredential
    owner: User
    granted_scopes: set[str]
    environment: str


def extract_raw_api_key(
    x_api_key: str | None = None,
    authorization: str | None = None,
) -> str | None:
    """Extract raw key from either X-API-Key or Authorization: Bearer header."""
    if x_api_key and x_api_key.strip():
        return x_api_key.strip()
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return None


def require_api_consumer(
    required_scope: str | None = None,
    required_permission: str | None = None,
    is_export: bool = False,
    is_webhook: bool = False,
) -> Callable:
    """Dependency factory returning authenticated ApiConsumerContext."""

    async def _api_consumer_dependency(
        request: Request,
        response: Response,
        db: Annotated[AsyncSession, Depends(get_db_session)],
        x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
        authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    ) -> ApiConsumerContext:
        # 1. Extract API Key
        raw_key = extract_raw_api_key(x_api_key=x_api_key, authorization=authorization)
        if not raw_key:
            raise AuthenticationException(
                "API credentials missing. Provide 'X-API-Key' or 'Authorization: Bearer <key>'."
            )

        if len(raw_key) < 16:
            raise AuthenticationException("Malformed API key structure.")

        prefix = raw_key[:12]

        # 2. Authenticate Credential
        cred_stmt = (
            select(ApplicationCredential)
            .where(ApplicationCredential.key_prefix == prefix)
            .options(
                selectinload(ApplicationCredential.application).selectinload(
                    DeveloperApplication.scope_grants
                )
            )
        )
        cred_res = await db.execute(cred_stmt)
        credentials = cred_res.scalars().all()

        matched_cred: ApplicationCredential | None = None
        for cred in credentials:
            if verify_credential_secret(raw_key, cred.secret_hash):
                matched_cred = cred
                break

        if not matched_cred:
            raise AuthenticationException("Invalid API key or credential secret.")

        # Check Credential Status & Expiration
        is_valid, reason = is_credential_valid_for_auth(matched_cred)
        if not is_valid:
            if matched_cred.status == CredentialStatus.REVOKED.value:
                raise CampusOSException(
                    status_code=401,
                    code="CREDENTIAL_REVOKED",
                    message="API credential has been revoked.",
                )
            if (
                matched_cred.status == CredentialStatus.EXPIRED.value
                or "expiration" in reason.lower()
            ):
                raise CampusOSException(
                    status_code=401,
                    code="CREDENTIAL_EXPIRED",
                    message="API credential has expired.",
                )
            raise AuthenticationException(f"API credential invalid: {reason}")

        # 3. Validate Application
        app = matched_cred.application
        if not app:
            raise AuthenticationException("Associated developer application not found.")

        if app.status == ApplicationStatus.SUSPENDED.value:
            raise CampusOSException(
                status_code=403,
                code="APPLICATION_SUSPENDED",
                message="Developer application is suspended.",
            )
        if app.status in (ApplicationStatus.REVOKED.value, ApplicationStatus.ARCHIVED.value):
            raise CampusOSException(
                status_code=403,
                code="APPLICATION_REVOKED",
                message=f"Developer application is {app.status.lower()}.",
            )
        if app.status not in (ApplicationStatus.ACTIVE.value, ApplicationStatus.APPROVED.value):
            raise CampusOSException(
                status_code=403,
                code="APPLICATION_INACTIVE",
                message=f"Developer application is in '{app.status}' state and cannot invoke APIs.",
            )

        # Enforce IP Allowlist if configured
        if app.allowed_ips:
            client_host = request.client.host if request.client else "unknown"
            if client_host not in app.allowed_ips and not any(
                ip in ("*", "0.0.0.0/0") for ip in app.allowed_ips
            ):
                raise CampusOSException(
                    status_code=403,
                    code="IP_FORBIDDEN",
                    message=f"Client IP '{client_host}' is not permitted by application firewall policy.",
                )

        # 4. Validate Tenant Lifecycle
        inst_stmt = select(Institution).where(Institution.id == app.tenant_id)
        inst_res = await db.execute(inst_stmt)
        institution = inst_res.scalar_one_or_none()
        if not institution:
            raise AuthenticationException("Associated institution tenant does not exist.")

        tenant_status = (institution.status or "ACTIVE").upper()
        if tenant_status == "SUSPENDED":
            raise TenantSuspendedException(institution.id)
        if tenant_status == "ARCHIVED" or not institution.is_active:
            raise TenantArchivedException(institution.id)

        # 5. Resolve Granted Scopes & Verify Required Scope
        granted_scopes = {
            grant.scope_code
            for grant in app.scope_grants
            if grant.status == ScopeGrantStatus.GRANTED.value
        }

        if required_scope:
            if not scope_resolver.is_scope_granted(granted_scopes, required_scope):
                raise CampusOSException(
                    status_code=403,
                    code="INSUFFICIENT_SCOPE",
                    message=f"Application does not have granted capability scope '{required_scope}'.",
                )

        # 6. Validate Application Owner & PBAC Permissions
        owner_stmt = (
            select(User)
            .where(User.id == app.owner_id)
            .options(
                selectinload(User.roles)
                .selectinload(UserRoleAssignment.role)
                .selectinload(Role.permissions)
                .selectinload(RolePermission.permission)
            )
        )
        owner_res = await db.execute(owner_stmt)
        owner = owner_res.scalar_one_or_none()
        if not owner:
            raise AuthenticationException("Application owner user account not found.")

        if not owner.is_active or owner.status in ("SUSPENDED", "DISABLED"):
            raise AccountDisabledException("Application owner user account is deactivated.")
        if owner.status == "LOCKED":
            raise AccountLockedException("Application owner account is locked.")

        # Check that owner actually holds underlying PBAC permissions
        if required_permission:
            owner_perms = resolve_user_permissions(owner)
            owner_roles = {ur.role.name for ur in owner.roles if ur.role}
            is_super = "SUPER_ADMIN" in owner_roles or "*" in owner_perms

            req_candidates = {required_permission}
            if "." in required_permission:
                req_candidates.add(required_permission.replace(".", ":"))
            if ":" in required_permission:
                req_candidates.add(required_permission.replace(":", "."))
                parts = required_permission.split(":")
                if len(parts) == 3:
                    req_candidates.add(f"{parts[1]}:{parts[2]}")
                    if parts[2] in ("record", "create"):
                        req_candidates.add(f"{parts[1]}:create")
                        req_candidates.add(f"{parts[1]}:record")
                elif len(parts) == 2:
                    for prefix_domain in (
                        "finance",
                        "core",
                        "people",
                        "academics",
                        "attendance",
                        "examination",
                        "events",
                    ):
                        req_candidates.add(f"{prefix_domain}:{parts[0]}:{parts[1]}")

            has_perm = is_super or any(c in owner_perms for c in req_candidates)
            if not has_perm:
                raise PermissionDeniedException(required_permission)

        # 7. Evaluate Velocity Rate Limits
        app_rate_limiter.check_or_raise(
            tenant_id=app.tenant_id,
            application_id=app.id,
            tier=app.rate_limit_tier,
            custom=app.rate_limit_custom,
        )

        # 8. Evaluate Aggregate Multi-Period Quotas
        await quota_service.check_and_consume(
            db=db,
            tenant_id=app.tenant_id,
            application=app,
            units=1,
            is_export=is_export,
            is_webhook=is_webhook,
        )

        # 9. Track Last Used Timestamp on Credential
        matched_cred.last_used_at = datetime.now(UTC)

        # 10. Construct Tenant & Consumer Context
        tenant_ctx = TenantContext(
            tenant_id=institution.id,
            code=institution.code,
            name=institution.legal_name,
            is_active=institution.is_active,
            user_id=owner.id,
            roles=tuple(sorted(ur.role.name for ur in owner.roles if ur.role and ur.role.name)),
            permissions=tuple(sorted(resolve_user_permissions(owner))),
            tenant_status=tenant_status,
            slug=institution.slug,
            plan=institution.plan or "ENTERPRISE",
            timezone=institution.default_timezone or "Asia/Kolkata",
            currency=institution.currency_code or "INR",
            locale=institution.locale or "en-IN",
        )
        set_current_tenant_context(tenant_ctx)
        request.state.tenant = tenant_ctx
        request.state.user = owner

        consumer_ctx = ApiConsumerContext(
            tenant_id=app.tenant_id,
            application_id=app.id,
            credential_id=matched_cred.id,
            client_id=matched_cred.client_id,
            application=app,
            credential=matched_cred,
            owner=owner,
            granted_scopes=granted_scopes,
            environment=matched_cred.environment,
        )
        request.state.consumer = consumer_ctx

        # 11. Add Security & Correlation Headers to Response
        response.headers["X-Application-ID"] = str(app.id)
        response.headers["X-Tenant-ID"] = str(app.tenant_id)

        # 12. Check API Deprecation Headers
        op_meta = await catalog_service.get_operation_metadata(
            db=db,
            method=request.method,
            path=request.url.path,
            version="v1",
        )
        if op_meta and op_meta.deprecated_at:
            response.headers["Deprecation"] = "true"
            if op_meta.sunset_at:
                response.headers["Sunset"] = op_meta.sunset_at.strftime("%a, %d %b %Y %H:%M:%S GMT")
            if op_meta.replacement_path:
                response.headers["Link"] = f'<{op_meta.replacement_path}>; rel="successor-version"'

        return consumer_ctx

    return _api_consumer_dependency
