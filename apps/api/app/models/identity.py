"""SQLAlchemy Entities for CampusOS Enterprise Identity, SSO, Session & Access Federation (Step 22).

Implements:
- Identity Provider abstractions (OIDC, OAuth2, SAML, LOCAL) with lifecycle and health monitoring
- External federated identity mappings (subject, provider, email, display name)
- Tenant identity policy configuration (local/external login, JIT provisioning, domains, lockout, MFA policy)
- First-class session model (session identifiers, token families, IP/device metadata, revocation)
- Multi-factor authentication (TOTP, recovery codes, challenge verification, step-up auth)
- Account linking request challenges preventing unverified account takeover
"""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, BaseModel, TenantScopedModel


# -----------------------------------------------------------------------------
# 1. Enums
# -----------------------------------------------------------------------------

class IdentityProviderType(StrEnum):
    LOCAL = "LOCAL"
    OIDC = "OIDC"
    OAUTH2 = "OAUTH2"
    SAML = "SAML"


class IdentityProviderStatus(StrEnum):
    DRAFT = "DRAFT"
    CONFIGURED = "CONFIGURED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    DISABLED = "DISABLED"
    ERROR = "ERROR"


class IdentityProviderHealth(StrEnum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    MISCONFIGURED = "MISCONFIGURED"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


class ProvisioningMode(StrEnum):
    DISABLED = "DISABLED"
    JUST_IN_TIME = "JUST_IN_TIME"
    INVITATION_ONLY = "INVITATION_ONLY"
    PRE_PROVISIONED = "PRE_PROVISIONED"


class MfaPolicyLevel(StrEnum):
    OPTIONAL = "OPTIONAL"
    REQUIRED = "REQUIRED"
    REQUIRED_FOR_ADMIN = "REQUIRED_FOR_ADMIN"
    REQUIRED_FOR_HIGH_RISK_ACTION = "REQUIRED_FOR_HIGH_RISK_ACTION"


class MfaFactorType(StrEnum):
    TOTP = "TOTP"
    EMAIL_OTP = "EMAIL_OTP"
    SMS_OTP = "SMS_OTP"
    WEBAUTHN = "WEBAUTHN"


class SessionStatus(StrEnum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    LOCKED = "LOCKED"


class AccountLifecycleStatus(StrEnum):
    INVITED = "INVITED"
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DISABLED = "DISABLED"
    LOCKED = "LOCKED"
    DEPROVISIONED = "DEPROVISIONED"


# -----------------------------------------------------------------------------
# 2. Identity Provider Entity
# -----------------------------------------------------------------------------

class IdentityProvider(TenantScopedModel):
    """Institutional identity provider integration (OIDC, OAuth2, SAML, LOCAL)."""

    __tablename__ = "identity_providers"

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    provider_type: Mapped[str] = mapped_column(
        String(32), default=IdentityProviderType.OIDC.value, nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(32), default=IdentityProviderStatus.DRAFT.value, nullable=False, index=True
    )
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Core endpoints and federation parameters
    issuer_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    client_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    client_secret_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    authorization_endpoint: Mapped[str | None] = mapped_column(String(255), nullable=True)
    token_endpoint: Mapped[str | None] = mapped_column(String(255), nullable=True)
    userinfo_endpoint: Mapped[str | None] = mapped_column(String(255), nullable=True)
    jwks_uri: Mapped[str | None] = mapped_column(String(255), nullable=True)
    scopes: Mapped[list[str]] = mapped_column(JSONB, default=lambda: ["openid", "profile", "email"], nullable=False)
    redirect_uri: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Claims and role mapping rules (deny-by-default external mappings)
    attribute_mapping: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    role_mapping: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    # Health and operational telemetry
    health_status: Mapped[str] = mapped_column(
        String(32), default=IdentityProviderHealth.UNKNOWN.value, nullable=False
    )
    last_health_check_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_successful_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    external_identities: Mapped[list["ExternalIdentity"]] = relationship(
        "ExternalIdentity", back_populates="provider", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "slug", name="uq_idp_tenant_slug"),
        Index("idx_idp_tenant_status", "tenant_id", "status"),
    )


# -----------------------------------------------------------------------------
# 3. External Identity Entity
# -----------------------------------------------------------------------------

class ExternalIdentity(TenantScopedModel):
    """Maps a federated external identity subject to a CampusOS User account."""

    __tablename__ = "identity_external_identities"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("identity_providers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    claims_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    provider: Mapped["IdentityProvider"] = relationship("IdentityProvider", back_populates="external_identities")

    __table_args__ = (
        UniqueConstraint("tenant_id", "provider_id", "subject", name="uq_ext_identity_subject"),
        Index("idx_ext_identity_lookup", "tenant_id", "email"),
    )


# -----------------------------------------------------------------------------
# 4. Tenant Identity Policy Entity
# -----------------------------------------------------------------------------

class TenantIdentityPolicy(TenantScopedModel):
    """Configurable security, authentication, and provisioning policies per tenant."""

    __tablename__ = "identity_tenant_policies"

    local_login_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    external_login_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allowed_identity_provider_ids: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)

    # Provisioning rules
    provisioning_mode: Mapped[str] = mapped_column(
        String(32), default=ProvisioningMode.JUST_IN_TIME.value, nullable=False
    )
    allowed_email_domains: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    default_role_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_roles.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Session governance
    session_duration_minutes: Mapped[int] = mapped_column(Integer, default=1440, nullable=False)  # 24h
    idle_timeout_minutes: Mapped[int] = mapped_column(Integer, default=120, nullable=False)       # 2h
    max_active_sessions_per_user: Mapped[int] = mapped_column(Integer, default=5, nullable=False)

    # Password policy
    password_min_length: Mapped[int] = mapped_column(Integer, default=8, nullable=False)
    password_require_uppercase: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    password_require_lowercase: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    password_require_numbers: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    password_require_special: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Account Lockout
    lockout_threshold: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    lockout_duration_minutes: Mapped[int] = mapped_column(Integer, default=15, nullable=False)

    # Multi-Factor Authentication (MFA)
    mfa_policy: Mapped[str] = mapped_column(
        String(32), default=MfaPolicyLevel.OPTIONAL.value, nullable=False
    )
    enforce_mfa_for_admins: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", name="uq_tenant_identity_policy"),
    )


# -----------------------------------------------------------------------------
# 5. First-Class Identity Session Entity
# -----------------------------------------------------------------------------

class IdentitySession(TenantScopedModel):
    """First-class user session tracking active devices, token rotation, and activity."""

    __tablename__ = "identity_user_sessions"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_identifier: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False, index=True
    )
    refresh_token_family_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), default=uuid4, nullable=False, index=True
    )
    refresh_token_hash: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(32), default=SessionStatus.ACTIVE.value, nullable=False, index=True
    )

    # Device & Network Telemetry
    ip_address_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ip_address_masked: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    device_summary: Mapped[str | None] = mapped_column(String(128), nullable=True)
    authentication_method: Mapped[str] = mapped_column(String(32), default="LOCAL_PASSWORD", nullable=False)

    # MFA State
    is_mfa_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfa_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Lifecycle Timestamps
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revocation_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        Index("idx_id_session_user_status", "user_id", "status"),
        Index("idx_id_session_family", "refresh_token_family_id"),
    )


# -----------------------------------------------------------------------------
# 6. Multi-Factor Authentication Entities
# -----------------------------------------------------------------------------

class MfaFactor(TenantScopedModel):
    """Enrolled MFA factor (TOTP authenticator, email/SMS fallback) for a user."""

    __tablename__ = "identity_mfa_factors"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    factor_type: Mapped[str] = mapped_column(
        String(32), default=MfaFactorType.TOTP.value, nullable=False, index=True
    )
    secret_encrypted: Mapped[str] = mapped_column(String(512), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", "factor_type", name="uq_user_mfa_factor"),
    )


class MfaRecoveryCode(TenantScopedModel):
    """Hashed single-use emergency recovery codes for MFA account recovery."""

    __tablename__ = "identity_mfa_recovery_codes"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_mfa_recovery_lookup", "tenant_id", "user_id", "is_used"),
    )


class MfaChallenge(TenantScopedModel):
    """Temporary ephemeral challenge token issued during step-up or MFA authentication."""

    __tablename__ = "identity_mfa_challenges"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    factor_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("identity_mfa_factors.id", ondelete="CASCADE"),
        nullable=True,
    )
    challenge_token_hash: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    factor_type: Mapped[str] = mapped_column(String(32), default=MfaFactorType.TOTP.value, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


# -----------------------------------------------------------------------------
# 7. Account Linking Request Entity
# -----------------------------------------------------------------------------

class AccountLinkRequest(TenantScopedModel):
    """Secure, cryptographic challenge token for explicit account linking verification."""

    __tablename__ = "identity_account_link_requests"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("identity_providers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    external_email: Mapped[str] = mapped_column(String(255), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
