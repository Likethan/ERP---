"""Pydantic v2 Schemas for Enterprise Identity, SSO, Sessions & Federation (Step 22)."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


# -----------------------------------------------------------------------------
# 1. Identity Provider Schemas
# -----------------------------------------------------------------------------

class IdentityProviderBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=128)
    slug: str = Field(..., min_length=2, max_length=64, pattern=r"^[a-z0-9-]+$")
    provider_type: str = Field(default="OIDC", description="OIDC, OAUTH2, SAML, LOCAL")
    is_default: bool = False
    issuer_url: str | None = None
    client_id: str | None = None
    authorization_endpoint: str | None = None
    token_endpoint: str | None = None
    userinfo_endpoint: str | None = None
    jwks_uri: str | None = None
    scopes: list[str] = Field(default_factory=lambda: ["openid", "profile", "email"])
    redirect_uri: str | None = None
    attribute_mapping: dict[str, Any] = Field(default_factory=dict)
    role_mapping: dict[str, Any] = Field(default_factory=dict)


class IdentityProviderCreate(IdentityProviderBase):
    client_secret: str | None = Field(None, description="Plaintext secret passed once upon configuration")


class IdentityProviderUpdate(BaseModel):
    name: str | None = None
    is_default: bool | None = None
    issuer_url: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    authorization_endpoint: str | None = None
    token_endpoint: str | None = None
    userinfo_endpoint: str | None = None
    jwks_uri: str | None = None
    scopes: list[str] | None = None
    redirect_uri: str | None = None
    attribute_mapping: dict[str, Any] | None = None
    role_mapping: dict[str, Any] | None = None


class IdentityProviderResponse(IdentityProviderBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID | None = None
    status: str
    health_status: str
    has_client_secret: bool = False
    last_health_check_at: datetime | None = None
    last_successful_login_at: datetime | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime | None = None


class IdentityProviderTestResponse(BaseModel):
    provider_id: UUID
    provider_name: str
    is_healthy: bool
    status_code: int | None = None
    latency_ms: float = 0.0
    message: str
    endpoints_reachable: dict[str, bool] = Field(default_factory=dict)


# -----------------------------------------------------------------------------
# 2. Session Schemas
# -----------------------------------------------------------------------------

class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_identifier: str
    status: str
    device_summary: str | None = None
    ip_address_masked: str | None = None
    authentication_method: str
    is_current: bool = False
    is_mfa_verified: bool = False
    created_at: datetime
    last_activity_at: datetime
    expires_at: datetime


class RevokeSessionResponse(BaseModel):
    revoked_session_id: UUID
    status: str = "REVOKED"
    message: str = "Session successfully invalidated."


class RevokeAllSessionsResponse(BaseModel):
    revoked_count: int
    message: str = "All active sessions have been invalidated."


# -----------------------------------------------------------------------------
# 3. External Identity & Account Linking Schemas
# -----------------------------------------------------------------------------

class ExternalIdentityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    provider_id: UUID
    provider_name: str | None = None
    provider_type: str | None = None
    subject: str
    email: str
    display_name: str | None = None
    last_login_at: datetime | None = None
    created_at: datetime


class AccountLinkInitiateRequest(BaseModel):
    provider_id: UUID
    subject: str = Field(..., min_length=1)
    external_email: str = Field(..., min_length=3)
    id_token: str | None = None


class AccountLinkInitiateResponse(BaseModel):
    link_token: str
    expires_at: datetime
    message: str = "Confirmation required. Submit link token with user authorization to complete linking."


class AccountLinkConfirmRequest(BaseModel):
    link_token: str
    current_password: str | None = None


# -----------------------------------------------------------------------------
# 4. Tenant Identity Policy Schemas
# -----------------------------------------------------------------------------

class TenantIdentityPolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tenant_id: UUID
    local_login_enabled: bool = True
    external_login_enabled: bool = True
    allowed_identity_provider_ids: list[str] = Field(default_factory=list)
    provisioning_mode: str = "JUST_IN_TIME"
    allowed_email_domains: list[str] = Field(default_factory=list)
    session_duration_minutes: int = 1440
    idle_timeout_minutes: int = 120
    max_active_sessions_per_user: int = 5
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_special: bool = True
    lockout_threshold: int = 5
    lockout_duration_minutes: int = 15
    mfa_policy: str = "OPTIONAL"
    enforce_mfa_for_admins: bool = True


class TenantIdentityPolicyUpdate(BaseModel):
    local_login_enabled: bool | None = None
    external_login_enabled: bool | None = None
    allowed_identity_provider_ids: list[str] | None = None
    provisioning_mode: str | None = None
    allowed_email_domains: list[str] | None = None
    session_duration_minutes: int | None = Field(None, ge=15, le=43200)
    idle_timeout_minutes: int | None = Field(None, ge=5, le=1440)
    max_active_sessions_per_user: int | None = Field(None, ge=1, le=50)
    password_min_length: int | None = Field(None, ge=8, le=128)
    password_require_uppercase: bool | None = None
    password_require_lowercase: bool | None = None
    password_require_numbers: bool | None = None
    password_require_special: bool | None = None
    lockout_threshold: int | None = Field(None, ge=3, le=20)
    lockout_duration_minutes: int | None = Field(None, ge=1, le=1440)
    mfa_policy: str | None = None
    enforce_mfa_for_admins: bool | None = None


# -----------------------------------------------------------------------------
# 5. Multi-Factor Authentication (MFA) Schemas
# -----------------------------------------------------------------------------

class MfaStatusResponse(BaseModel):
    is_mfa_enabled: bool
    enrolled_factors: list[str]
    has_recovery_codes: bool
    is_mfa_required: bool
    enforce_reason: str | None = None


class TotpEnrollResponse(BaseModel):
    factor_id: UUID
    secret_key: str
    totp_uri: str
    recovery_codes: list[str]
    instructions: str = "Enter the 6-digit TOTP code into your authenticator app to complete enrollment."


class TotpVerifyEnrollRequest(BaseModel):
    factor_id: UUID
    code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


class MfaChallengeResponse(BaseModel):
    challenge_token: str
    supported_factors: list[str]
    expires_at: datetime
    message: str = "Multi-factor authentication challenge required."


class MfaChallengeVerifyRequest(BaseModel):
    challenge_token: str
    code: str = Field(..., min_length=6, max_length=16)


# -----------------------------------------------------------------------------
# 6. OIDC & Federation Authorization Schemas
# -----------------------------------------------------------------------------

class OidcLoginInitiateResponse(BaseModel):
    authorization_url: str
    state: str
    provider_id: UUID


class OidcCallbackRequest(BaseModel):
    code: str
    state: str
    provider_id: UUID | None = None
