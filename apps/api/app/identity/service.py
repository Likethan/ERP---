"""Enterprise Identity Orchestration Service (Step 22).

Manages:
- Identity Provider CRUD, activation lifecycle, and outbound connectivity testing
- Secure account linking with challenge confirmation preventing account takeover
- Safety-checked unlinking preventing account lockouts
- Controlled user deprovisioning preserving Step 19 governed historical records
"""

from datetime import datetime, timedelta, timezone
import hashlib
import logging
import secrets
import time
from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.core.security import AuthenticationException, pwd_context
from app.identity.models import (
    AccountLifecycleStatus,
    AccountLinkRequest,
    ExternalIdentity,
    IdentityProvider,
    IdentityProviderHealth,
    IdentityProviderStatus,
    IdentityProviderType,
    MfaFactor,
)
from app.identity.session_service import IdentitySessionService
from app.integrations.secrets import SecretManager
from app.integrations.security import SafeHttpClient
from app.models.audit import AuditLog
from app.models.people import User

logger = logging.getLogger("campusos.identity.service")


def hash_token_str(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class EnterpriseIdentityService:
    """Central orchestrator for providers, linking, lifecycle, and health diagnostics."""

    # -------------------------------------------------------------------------
    # 1. Identity Provider Lifecycle
    # -------------------------------------------------------------------------

    @classmethod
    async def list_providers(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
    ) -> list[IdentityProvider]:
        """List configured identity providers for the tenant."""
        stmt = (
            select(IdentityProvider)
            .where(IdentityProvider.tenant_id == tenant_id)
            .order_by(IdentityProvider.created_at.asc())
        )
        res = await db.execute(stmt)
        return res.scalars().all()

    @classmethod
    async def get_provider(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        provider_id: UUID,
    ) -> IdentityProvider:
        """Get an identity provider by ID within the tenant scope."""
        stmt = select(IdentityProvider).where(
            IdentityProvider.id == provider_id,
            IdentityProvider.tenant_id == tenant_id,
        )
        res = await db.execute(stmt)
        provider = res.scalars().first()
        if not provider:
            raise NotFoundException("Identity provider not found.")
        return provider

    @classmethod
    async def create_provider(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        data: dict[str, Any],
    ) -> IdentityProvider:
        """Create a new identity provider in DRAFT status."""
        slug = data.get("slug", "").strip().lower()

        # Check slug uniqueness within tenant
        existing_stmt = select(IdentityProvider).where(
            IdentityProvider.tenant_id == tenant_id,
            IdentityProvider.slug == slug,
        )
        existing_res = await db.execute(existing_stmt)
        if existing_res.scalars().first():
            raise ConflictException(f"An identity provider with slug '{slug}' already exists in this tenant.")

        # Encrypt client secret if provided
        client_secret = data.pop("client_secret", None)
        secret_ref = None
        if client_secret:
            secret_ref = SecretManager.encrypt_payload({"secret": client_secret})

        # If set as default, unset other defaults
        if data.get("is_default"):
            await cls._unset_default_providers(db, tenant_id)

        provider = IdentityProvider(
            tenant_id=tenant_id,
            name=data["name"],
            slug=slug,
            provider_type=data.get("provider_type", IdentityProviderType.OIDC.value),
            status=IdentityProviderStatus.DRAFT.value,
            health_status=IdentityProviderHealth.UNKNOWN.value,
            is_default=bool(data.get("is_default", False)),
            issuer_url=data.get("issuer_url"),
            client_id=data.get("client_id"),
            client_secret_reference=secret_ref,
            authorization_endpoint=data.get("authorization_endpoint"),
            token_endpoint=data.get("token_endpoint"),
            userinfo_endpoint=data.get("userinfo_endpoint"),
            jwks_uri=data.get("jwks_uri"),
            scopes=data.get("scopes", ["openid", "profile", "email"]),
            redirect_uri=data.get("redirect_uri"),
            attribute_mapping=data.get("attribute_mapping", {}),
            role_mapping=data.get("role_mapping", {}),
        )
        db.add(provider)
        await db.commit()
        await db.refresh(provider)
        return provider

    @classmethod
    async def update_provider(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        provider_id: UUID,
        updates: dict[str, Any],
    ) -> IdentityProvider:
        """Update an existing identity provider configuration."""
        provider = await cls.get_provider(db, tenant_id, provider_id)

        client_secret = updates.pop("client_secret", None)
        if client_secret is not None:
            if client_secret:
                provider.client_secret_reference = SecretManager.encrypt_payload(
                    {"secret": client_secret}
                )
            else:
                provider.client_secret_reference = None

        if updates.get("is_default") is True:
            await cls._unset_default_providers(db, tenant_id, exclude_id=provider.id)

        for field, value in updates.items():
            if value is not None and hasattr(provider, field):
                setattr(provider, field, value)

        await db.commit()
        await db.refresh(provider)
        return provider

    @classmethod
    async def activate_provider(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        provider_id: UUID,
    ) -> IdentityProvider:
        """Validate configuration completeness and activate identity provider."""
        provider = await cls.get_provider(db, tenant_id, provider_id)

        if provider.provider_type == IdentityProviderType.OIDC.value:
            if not provider.issuer_url and not (provider.authorization_endpoint and provider.token_endpoint):
                raise ValidationException(
                    "OIDC provider requires an issuer URL or explicit authorization and token endpoints."
                )
            if not provider.client_id:
                raise ValidationException("OIDC provider requires a client ID.")

        provider.status = IdentityProviderStatus.ACTIVE.value
        provider.error_message = None
        await db.commit()
        await db.refresh(provider)
        return provider

    @classmethod
    async def disable_provider(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        provider_id: UUID,
    ) -> IdentityProvider:
        """Deactivate an identity provider."""
        provider = await cls.get_provider(db, tenant_id, provider_id)
        provider.status = IdentityProviderStatus.DISABLED.value
        await db.commit()
        await db.refresh(provider)
        return provider

    @classmethod
    async def test_provider_connectivity(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        provider_id: UUID,
    ) -> dict[str, Any]:
        """Test outbound network reachability and health of provider endpoints with SSRF safety."""
        provider = await cls.get_provider(db, tenant_id, provider_id)
        start_time = time.time()
        now = datetime.now(timezone.utc)

        endpoints = {}
        if provider.issuer_url:
            endpoints["issuer_discovery"] = f"{provider.issuer_url.rstrip('/')}/.well-known/openid-configuration"
        if provider.jwks_uri:
            endpoints["jwks"] = provider.jwks_uri
        if provider.authorization_endpoint:
            endpoints["authorization"] = provider.authorization_endpoint

        if not endpoints:
            return {
                "provider_id": provider.id,
                "provider_name": provider.name,
                "is_healthy": False,
                "status_code": None,
                "latency_ms": 0.0,
                "message": "No testable HTTP endpoints configured.",
                "endpoints_reachable": {},
            }

        endpoints_reachable: dict[str, bool] = {}
        all_passed = True
        sample_status_code = None

        for name, url in endpoints.items():
            try:
                resp = await SafeHttpClient.request(
                    method="GET",
                    url=url,
                    timeout_seconds=5.0,
                    allow_private_networks_for_tests=(settings.ENVIRONMENT.lower() == "test"),
                )
                endpoints_reachable[name] = (resp.status_code < 500)
                if sample_status_code is None:
                    sample_status_code = resp.status_code
                if resp.status_code >= 500:
                    all_passed = False
            except Exception as exc:
                endpoints_reachable[name] = False
                all_passed = False
                logger.warning("Endpoint test failed for %s (%s): %s", name, url, exc)

        latency_ms = round((time.time() - start_time) * 1000, 2)
        provider.health_status = (
            IdentityProviderHealth.HEALTHY.value if all_passed else IdentityProviderHealth.DEGRADED.value
        )
        provider.last_health_check_at = now
        await db.commit()

        return {
            "provider_id": provider.id,
            "provider_name": provider.name,
            "is_healthy": all_passed,
            "status_code": sample_status_code or 200,
            "latency_ms": latency_ms,
            "message": "Connectivity check passed." if all_passed else "Some endpoints were unreachable or degraded.",
            "endpoints_reachable": endpoints_reachable,
        }

    @classmethod
    async def _unset_default_providers(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        exclude_id: UUID | None = None,
    ) -> None:
        stmt = select(IdentityProvider).where(
            IdentityProvider.tenant_id == tenant_id,
            IdentityProvider.is_default.is_(True),
        )
        if exclude_id:
            stmt = stmt.where(IdentityProvider.id != exclude_id)
        res = await db.execute(stmt)
        for p in res.scalars().all():
            p.is_default = False

    # -------------------------------------------------------------------------
    # 2. Account Linking & Unlinking
    # -------------------------------------------------------------------------

    @classmethod
    async def list_user_external_identities(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
    ) -> list[dict[str, Any]]:
        """List external identity federations linked to a user account."""
        stmt = (
            select(ExternalIdentity, IdentityProvider)
            .join(IdentityProvider, ExternalIdentity.provider_id == IdentityProvider.id)
            .where(
                ExternalIdentity.tenant_id == tenant_id,
                ExternalIdentity.user_id == user_id,
            )
        )
        res = await db.execute(stmt)
        rows = res.all()

        output = []
        for ext, prov in rows:
            output.append({
                "id": ext.id,
                "provider_id": ext.provider_id,
                "provider_name": prov.name,
                "provider_type": prov.provider_type,
                "subject": ext.subject,
                "email": ext.email,
                "display_name": ext.display_name,
                "last_login_at": ext.last_login_at,
                "created_at": ext.created_at,
            })
        return output

    @classmethod
    async def initiate_account_link(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        provider_id: UUID,
        subject: str,
        external_email: str,
    ) -> dict[str, Any]:
        """Initiate secure account linking challenge to prevent account takeover."""
        # 1. Verify provider belongs to tenant
        provider = await cls.get_provider(db, tenant_id, provider_id)

        # 2. Ensure subject is not already linked to another account in this tenant
        dup_stmt = select(ExternalIdentity).where(
            ExternalIdentity.tenant_id == tenant_id,
            ExternalIdentity.provider_id == provider_id,
            ExternalIdentity.subject == subject,
        )
        dup_res = await db.execute(dup_stmt)
        if dup_res.scalars().first():
            raise ConflictException("This external identity is already linked to an account.")

        # 3. Create short-lived cryptographic challenge token (15 mins)
        raw_token = f"link_{secrets.token_urlsafe(32)}"
        token_hash = hash_token_str(raw_token)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=15)

        link_req = AccountLinkRequest(
            tenant_id=tenant_id,
            user_id=user_id,
            provider_id=provider_id,
            subject=subject,
            external_email=external_email.lower().strip(),
            token_hash=token_hash,
            is_completed=False,
            expires_at=expires_at,
        )
        db.add(link_req)
        await db.commit()

        return {
            "link_token": raw_token,
            "expires_at": expires_at,
            "message": "Confirmation required. Submit link token with user authorization to complete linking.",
        }

    @classmethod
    async def confirm_account_link(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        user: User,
        link_token: str,
        current_password: str | None = None,
    ) -> ExternalIdentity:
        """Confirm account link with challenge token and password verification."""
        token_hash = hash_token_str(link_token)
        now = datetime.now(timezone.utc)

        stmt = select(AccountLinkRequest).where(
            AccountLinkRequest.token_hash == token_hash,
            AccountLinkRequest.tenant_id == tenant_id,
            AccountLinkRequest.user_id == user.id,
            AccountLinkRequest.is_completed.is_(False),
            AccountLinkRequest.expires_at > now,
        )
        res = await db.execute(stmt)
        req = res.scalars().first()
        if not req:
            raise ValidationException("Invalid or expired account linking token.")

        # Require password verification if user has a set password
        if user.password_hash and not user.password_hash.startswith("EXTERNAL_"):
            if not current_password or not pwd_context.verify(current_password, user.password_hash):
                raise AuthenticationException("Current password verification failed.")

        # Create ExternalIdentity
        ext_identity = ExternalIdentity(
            tenant_id=tenant_id,
            user_id=user.id,
            provider_id=req.provider_id,
            subject=req.subject,
            email=req.external_email,
            display_name=f"{user.first_name} {user.last_name}",
            last_login_at=now,
            claims_snapshot={"linked_at": now.isoformat()},
        )
        db.add(ext_identity)
        req.is_completed = True
        await db.flush()

        # Audit log
        db.add(
            AuditLog(
                tenant_id=tenant_id,
                user_id=user.id,
                action="IDENTITY_LINKED",
                entity_type="ExternalIdentity",
                entity_id=ext_identity.id,
                ip_address="127.0.0.1",
                business_context=f"Linked external identity subject '{req.subject}' from provider {req.provider_id}",
            )
        )
        await db.commit()
        await db.refresh(ext_identity)
        return ext_identity

    @classmethod
    async def unlink_external_identity(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        user: User,
        external_identity_id: UUID,
    ) -> bool:
        """Unlink external identity with safety checks preventing user lockout."""
        stmt = select(ExternalIdentity).where(
            ExternalIdentity.id == external_identity_id,
            ExternalIdentity.tenant_id == tenant_id,
            ExternalIdentity.user_id == user.id,
        )
        res = await db.execute(stmt)
        ext = res.scalars().first()
        if not ext:
            raise NotFoundException("Linked external identity not found.")

        # Security check: Ensure user still has another way to log in!
        # Either a valid local password OR another active external identity.
        has_password = bool(user.password_hash and not user.password_hash.startswith("EXTERNAL_"))

        count_stmt = select(ExternalIdentity).where(
            ExternalIdentity.tenant_id == tenant_id,
            ExternalIdentity.user_id == user.id,
            ExternalIdentity.id != external_identity_id,
        )
        other_ext = (await db.execute(count_stmt)).scalars().all()

        if not has_password and len(other_ext) == 0:
            raise ForbiddenException(
                "Cannot unlink the only authentication method for this account. "
                "Set a local password or link another provider before unlinking."
            )

        await db.delete(ext)

        # Audit log
        db.add(
            AuditLog(
                tenant_id=tenant_id,
                user_id=user.id,
                action="IDENTITY_UNLINKED",
                entity_type="ExternalIdentity",
                entity_id=external_identity_id,
                ip_address="127.0.0.1",
                business_context=f"Unlinked external identity subject '{ext.subject}'",
            )
        )
        await db.commit()
        return True

    # -------------------------------------------------------------------------
    # 3. Controlled Deprovisioning & Offboarding
    # -------------------------------------------------------------------------

    @classmethod
    async def deprovision_user(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        reason: str = "INSTITUTIONAL_OFFBOARDING",
    ) -> bool:
        """Execute controlled deprovisioning preserving Step 19 governed historical records."""
        user_stmt = select(User).where(User.id == user_id, User.primary_tenant_id == tenant_id)
        user_res = await db.execute(user_stmt)
        user = user_res.scalars().first()
        if not user:
            raise NotFoundException("User account not found.")

        # 1. Update lifecycle status to DEPROVISIONED and disable active flag
        user.status = AccountLifecycleStatus.DEPROVISIONED.value
        user.is_active = False

        # 2. Invalidate all active user sessions immediately
        await IdentitySessionService.revoke_all_user_sessions(
            db, user_id=user.id, tenant_id=tenant_id, reason=f"DEPROVISIONED: {reason}"
        )

        # 3. Deactivate all MFA factors
        mfa_stmt = select(MfaFactor).where(MfaFactor.user_id == user.id)
        mfa_res = await db.execute(mfa_stmt)
        for factor in mfa_res.scalars().all():
            factor.is_active = False

        # 4. Audit security deprovisioning event
        db.add(
            AuditLog(
                tenant_id=tenant_id,
                user_id=user.id,
                action="USER_DEPROVISIONED",
                entity_type="User",
                entity_id=user.id,
                ip_address="127.0.0.1",
                business_context=f"Controlled institutional deprovisioning completed. Reason: {reason}",
            )
        )
        await db.commit()
        logger.info("Deprovisioned user %s (ID %s). Preserved governed records.", user.email, user.id)
        return True
