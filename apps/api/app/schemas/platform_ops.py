"""Pydantic v2 Validation & Serialization Schemas for Enterprise Platform Administration (Step 30)."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# -----------------------------------------------------------------------------
# 1. Tenant Lifecycle & Directory Schemas
# -----------------------------------------------------------------------------


class TenantDirectoryItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    slug: str | None = None
    legal_name: str
    short_name: str
    status: str
    plan: str
    contact_email: str
    contact_phone: str
    city: str
    state: str
    country: str
    is_active: bool
    created_at: datetime
    suspended_at: datetime | None = None
    deleted_at: datetime | None = None


class TenantDirectoryPageResponse(BaseModel):
    items: list[TenantDirectoryItemResponse]
    total: int
    limit: int
    offset: int


class TenantLifecycleTransitionRequest(BaseModel):
    target_status: str = Field(
        ...,
        description="Target lifecycle status: ACTIVE, TRIAL, SUSPENDED, DEACTIVATION_PENDING, DEACTIVATED, DELETION_PENDING, DELETED, ARCHIVED",
    )
    reason: str = Field(..., min_length=3, max_length=1000)
    correlation_id: UUID | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TenantLifecycleTransitionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    from_status: str
    to_status: str
    actor_id: UUID | None
    actor_email: str | None
    reason: str
    correlation_id: UUID | None
    metadata_json: dict[str, Any]
    created_at: datetime


# -----------------------------------------------------------------------------
# 2. Automated Onboarding & Provisioning Schemas
# -----------------------------------------------------------------------------


class TenantOnboardRequest(BaseModel):
    code: str = Field(..., min_length=2, max_length=32, description="Unique uppercase institution code, e.g. VSB")
    slug: str | None = Field(None, min_length=2, max_length=64)
    legal_name: str = Field(..., min_length=2, max_length=255)
    short_name: str = Field(..., min_length=2, max_length=64)
    plan: str = Field("ENTERPRISE", max_length=32, description="FREE, STARTER, PROFESSIONAL, ENTERPRISE")
    contact_email: str = Field(..., max_length=255)
    contact_phone: str = Field(..., max_length=32)
    address_line1: str = Field(..., max_length=255)
    city: str = Field(..., max_length=100)
    state: str = Field(..., max_length=100)
    postal_code: str = Field(..., max_length=32)
    country: str = Field("India", max_length=100)
    default_timezone: str = Field("Asia/Kolkata", max_length=64)
    currency_code: str = Field("INR", max_length=8)
    locale: str = Field("en-IN", max_length=32)
    admin_email: str | None = Field(None, max_length=255)
    admin_first_name: str = Field("Institution", max_length=100)
    admin_last_name: str = Field("Administrator", max_length=100)
    admin_password: str | None = Field(None, min_length=8)
    is_trial: bool = False
    trial_days: int = Field(14, ge=1, le=90)


class TenantProvisioningStageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    stage: str
    status: str
    attempt_count: int
    error_message: str | None = None
    details_json: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime
    completed_at: datetime | None = None


class TenantProvisioningStatusResponse(BaseModel):
    tenant_id: UUID
    overall_status: str
    current_stage: str
    is_completed: bool
    can_retry: bool
    stages: list[TenantProvisioningStageResponse]


# -----------------------------------------------------------------------------
# 3. Entitlement & Subscription Packaging Schemas
# -----------------------------------------------------------------------------


class TenantEntitlementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tenant_id: UUID
    plan: str
    max_users: int
    max_campuses: int
    max_storage_bytes: int
    max_api_rpm: int
    max_ai_tokens_monthly: int
    enabled_modules: list[str]
    feature_entitlements: dict[str, Any]
    is_trial: bool
    trial_ends_at: datetime | None = None
    grace_period_ends_at: datetime | None = None
    custom_limits: dict[str, Any] = Field(default_factory=dict)


class TenantEntitlementUpdateRequest(BaseModel):
    plan: str | None = None
    max_users: int | None = None
    max_campuses: int | None = None
    max_storage_bytes: int | None = None
    max_api_rpm: int | None = None
    max_ai_tokens_monthly: int | None = None
    enabled_modules: list[str] | None = None
    feature_entitlements: dict[str, Any] | None = None
    custom_limits: dict[str, Any] | None = None
    is_trial: bool | None = None
    trial_ends_at: datetime | None = None
    grace_period_ends_at: datetime | None = None


# -----------------------------------------------------------------------------
# 4. Quota Governance Schemas
# -----------------------------------------------------------------------------


class TenantQuotaItemResponse(BaseModel):
    resource_type: str
    current_usage: int
    soft_limit: int
    hard_limit: int
    unit: str
    percentage_used: float
    is_exceeded: bool
    is_warning: bool
    warning_threshold_percent: int


class TenantQuotaSummaryResponse(BaseModel):
    tenant_id: UUID
    quotas: list[TenantQuotaItemResponse]


class TenantQuotaOverrideRequest(BaseModel):
    resource_type: str
    hard_limit: int = Field(..., ge=0)
    soft_limit: int | None = None
    warning_threshold_percent: int = Field(80, ge=10, le=99)


# -----------------------------------------------------------------------------
# 5. Controlled Platform Support Access Schemas
# -----------------------------------------------------------------------------


class PlatformSupportSessionCreateRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=1000)
    duration_hours: int = Field(2, ge=1, le=8)
    ticket_reference: str | None = Field(None, max_length=128)
    permissions_scope: list[str] = Field(default_factory=list)


class PlatformSupportSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    operator_user_id: UUID
    reason: str
    ticket_reference: str | None = None
    permissions_scope: list[str] = Field(default_factory=list)
    is_active: bool
    started_at: datetime
    expires_at: datetime
    revoked_at: datetime | None = None
    revocation_reason: str | None = None


# -----------------------------------------------------------------------------
# 6. Retention, Deactivation & Deletion Governance Schemas
# -----------------------------------------------------------------------------


class TenantDeletionPreviewResponse(BaseModel):
    tenant_id: UUID
    tenant_code: str
    legal_name: str
    can_delete: bool
    retention_clearance: bool
    legal_holds_clearance: bool
    financial_clearance: bool
    export_completed: bool
    blocking_reasons: list[str]
    impact_summary: dict[str, int]


class TenantDeletionExecuteRequest(BaseModel):
    confirmation_code: str = Field(..., description="Must match the exact institution uppercase code")
    reason: str = Field(..., min_length=5, max_length=1000)
    force_override_holds: bool = False


class TenantDeletionPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    status: str
    retention_clearance: bool
    legal_holds_clearance: bool
    financial_clearance: bool
    export_completed: bool
    blocking_reasons: list[str]
    impact_summary_json: dict[str, Any]
    scheduled_deletion_at: datetime | None = None
    completed_at: datetime | None = None


# -----------------------------------------------------------------------------
# 7. Platform Operations & Telemetry Schemas
# -----------------------------------------------------------------------------


class PlatformOperationalHealthResponse(BaseModel):
    status: str
    timestamp: datetime
    database_connected: bool
    database_latency_ms: float
    cache_connected: bool
    scheduler_responsive: bool
    outbox_pending_count: int
    outbox_dead_letter_count: int
    provisioning_backlog_count: int
    active_tenants_count: int
    suspended_tenants_count: int
    total_tenants_count: int
    active_support_sessions_count: int
    subsystems: dict[str, str]
