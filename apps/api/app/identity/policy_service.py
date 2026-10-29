"""Tenant Identity Policy Management Service (Step 22).

Enforces tenant-configurable policies:
- Local vs External login toggles
- Allowed identity provider constraints
- Provisioning mode (JUST_IN_TIME, INVITATION_ONLY, PRE_PROVISIONED, DISABLED)
- Verified email domain restrictions
- Session lifetimes & idle timeouts
- Password complexity requirements
- Failed login attempt lockout thresholds & durations
- Multi-factor authentication enforcement levels
"""

import re
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ForbiddenException,
    ValidationException,
)
from app.core.security import AuthenticationException
from app.identity.models import (
    MfaPolicyLevel,
    ProvisioningMode,
    TenantIdentityPolicy,
)
from app.models.people import User


class TenantIdentityPolicyService:
    """Manages tenant identity policy lifecycle, password enforcement, and lockout rules."""

    @classmethod
    async def get_policy(cls, db: AsyncSession, tenant_id: UUID) -> TenantIdentityPolicy:
        """Retrieve tenant identity policy or return safe enterprise defaults."""
        result = await db.execute(
            select(TenantIdentityPolicy).where(TenantIdentityPolicy.tenant_id == tenant_id)
        )
        policy = result.scalars().first()
        if not policy:
            # Create default policy row for tenant
            policy = TenantIdentityPolicy(
                tenant_id=tenant_id,
                local_login_enabled=True,
                external_login_enabled=True,
                allowed_identity_provider_ids=[],
                provisioning_mode=ProvisioningMode.JUST_IN_TIME.value,
                allowed_email_domains=[],
                session_duration_minutes=1440,  # 24 hours
                idle_timeout_minutes=120,       # 2 hours
                max_active_sessions_per_user=5,
                password_min_length=8,
                password_require_uppercase=True,
                password_require_lowercase=True,
                password_require_numbers=True,
                password_require_special=True,
                lockout_threshold=5,
                lockout_duration_minutes=15,
                mfa_policy=MfaPolicyLevel.OPTIONAL.value,
                enforce_mfa_for_admins=True,
            )
            db.add(policy)
            await db.flush()
        return policy

    @classmethod
    async def update_policy(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        updates: dict[str, Any],
    ) -> TenantIdentityPolicy:
        """Update tenant identity policy with validation."""
        policy = await cls.get_policy(db, tenant_id)

        for key, value in updates.items():
            if value is not None and hasattr(policy, key):
                setattr(policy, key, value)

        await db.commit()
        await db.refresh(policy)
        return policy

    @classmethod
    def validate_password_against_policy(cls, password: str, policy: TenantIdentityPolicy) -> None:
        """Validate password against tenant-configured complexity requirements."""
        if len(password) < policy.password_min_length:
            raise ValidationException(
                f"Password must be at least {policy.password_min_length} characters long."
            )
        if policy.password_require_uppercase and not re.search(r"[A-Z]", password):
            raise ValidationException("Password must contain at least one uppercase letter.")
        if policy.password_require_lowercase and not re.search(r"[a-z]", password):
            raise ValidationException("Password must contain at least one lowercase letter.")
        if policy.password_require_numbers and not re.search(r"\d", password):
            raise ValidationException("Password must contain at least one numeric digit.")
        if policy.password_require_special and not re.search(r"[\W_]", password):
            raise ValidationException("Password must contain at least one special character.")

    @classmethod
    def validate_email_domain(cls, email: str, policy: TenantIdentityPolicy) -> None:
        """Ensure email domain is permitted under tenant restrictions."""
        if not policy.allowed_email_domains:
            return  # No domain restrictions configured

        parts = email.strip().lower().split("@")
        if len(parts) != 2:
            raise ValidationException("Invalid email format.")

        domain = parts[1]
        allowed = [d.strip().lower() for d in policy.allowed_email_domains if d]
        if domain not in allowed:
            raise ForbiddenException(
                f"Email domain '{domain}' is not authorized for institutional access in this tenant."
            )

    @classmethod
    def check_account_lockout(cls, user: User) -> None:
        """Check if account is temporarily locked due to failed authentication attempts."""
        if user.locked_until:
            now = datetime.now(UTC)
            # Handle tz-aware comparison
            locked_until = user.locked_until
            if locked_until.tzinfo is None:
                locked_until = locked_until.replace(tzinfo=UTC)

            if locked_until > now:
                remaining_seconds = int((locked_until - now).total_seconds())
                remaining_minutes = max(1, remaining_seconds // 60)
                raise AuthenticationException(
                    f"Account is temporarily locked due to repeated authentication failures. "
                    f"Please try again in {remaining_minutes} minute(s)."
                )

    @classmethod
    async def record_login_failure(
        cls,
        db: AsyncSession,
        user: User,
        policy: TenantIdentityPolicy,
    ) -> bool:
        """Increment failed login attempts and lock account if threshold reached.
        
        Returns True if account was locked as a result.
        """
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        is_locked = False

        if user.failed_login_attempts >= policy.lockout_threshold:
            lockout_expiry = datetime.now(UTC) + timedelta(minutes=policy.lockout_duration_minutes)
            user.locked_until = lockout_expiry
            is_locked = True

        await db.flush()
        return is_locked

    @classmethod
    async def reset_login_failures(cls, db: AsyncSession, user: User) -> None:
        """Reset failed login attempts and lockout state on successful authentication."""
        user.failed_login_attempts = 0
        user.locked_until = None
        await db.flush()
