"""Pydantic DTO Schemas for Enterprise Customer Success, Subscription Lifecycle & SaaS Entitlements (Step 38)."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.subscription import (
    BillingInterval,
    CustomerHealthStatus,
    CustomerNoteType,
    InvoiceStatus,
    OverrideType,
    PaymentStatus,
    SubscriptionChangeStatus,
    SubscriptionChangeType,
    SubscriptionPlanStatus,
    SubscriptionStatus,
)


# -----------------------------------------------------------------------------
# 1. Base Schema
# -----------------------------------------------------------------------------


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")


# -----------------------------------------------------------------------------
# 2. Subscription Plans
# -----------------------------------------------------------------------------


class SubscriptionPlanCreateRequest(BaseSchema):
    code: str = Field(..., min_length=2, max_length=64)
    name: str = Field(..., min_length=2, max_length=128)
    description: str = Field("", max_length=2000)
    status: SubscriptionPlanStatus = SubscriptionPlanStatus.ACTIVE
    billing_interval: BillingInterval = BillingInterval.ANNUAL
    currency: str = Field("INR", min_length=3, max_length=3)
    base_price: Decimal = Field(Decimal("0.00"), ge=Decimal("0.00"))
    trial_eligible: bool = True
    trial_duration_days: int = Field(14, ge=1, le=90)
    max_active_users: int = Field(500, ge=1)
    max_students: int = Field(5000, ge=1)
    max_faculty: int = Field(250, ge=1)
    max_storage_bytes: int = Field(107374182400, ge=1073741824)  # Min 1GB
    max_api_rpm: int = Field(300, ge=10)
    max_ai_tokens_monthly: int = Field(1000000, ge=0)
    max_integrations: int = Field(10, ge=0)
    included_modules: list[str] = Field(default_factory=list)
    feature_capabilities: dict[str, Any] = Field(default_factory=dict)
    support_tier: str = Field("STANDARD", max_length=64)


class SubscriptionPlanUpdateRequest(BaseSchema):
    name: str | None = Field(None, min_length=2, max_length=128)
    description: str | None = Field(None, max_length=2000)
    status: SubscriptionPlanStatus | None = None
    base_price: Decimal | None = Field(None, ge=Decimal("0.00"))
    trial_eligible: bool | None = None
    trial_duration_days: int | None = Field(None, ge=1, le=90)
    max_active_users: int | None = Field(None, ge=1)
    max_students: int | None = Field(None, ge=1)
    max_faculty: int | None = Field(None, ge=1)
    max_storage_bytes: int | None = Field(None, ge=1073741824)
    max_api_rpm: int | None = Field(None, ge=10)
    max_ai_tokens_monthly: int | None = Field(None, ge=0)
    max_integrations: int | None = Field(None, ge=0)
    included_modules: list[str] | None = None
    feature_capabilities: dict[str, Any] | None = None
    support_tier: str | None = Field(None, max_length=64)


class SubscriptionPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    description: str
    status: str
    billing_interval: str
    currency: str
    base_price: Decimal
    trial_eligible: bool
    trial_duration_days: int
    max_active_users: int
    max_students: int
    max_faculty: int
    max_storage_bytes: int
    max_api_rpm: int
    max_ai_tokens_monthly: int
    max_integrations: int
    included_modules: list[str]
    feature_capabilities: dict[str, Any]
    support_tier: str
    version: int
    effective_from: datetime
    retired_at: datetime | None
    created_at: datetime
    updated_at: datetime


# -----------------------------------------------------------------------------
# 3. Tenant Subscriptions
# -----------------------------------------------------------------------------


class TenantSubscriptionCreateRequest(BaseSchema):
    tenant_id: UUID
    plan_id: UUID
    billing_interval: BillingInterval = BillingInterval.ANNUAL
    is_trial: bool = False
    custom_unit_price: Decimal | None = Field(None, ge=Decimal("0.00"))
    payment_method_id: str | None = Field(None, max_length=128)


class TenantSubscriptionTransitionRequest(BaseSchema):
    target_status: SubscriptionStatus
    reason: str = Field(..., min_length=3, max_length=1000)
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class SubscriptionLifecycleHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    subscription_id: UUID
    tenant_id: UUID
    from_status: str
    to_status: str
    reason: str
    actor_id: UUID | None
    actor_email: str | None
    metadata_json: dict[str, Any]
    created_at: datetime


class TenantSubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    plan_id: UUID
    plan_version: int
    status: str
    billing_interval: str
    currency: str
    unit_price: Decimal
    current_period_start: datetime
    current_period_end: datetime
    trial_started_at: datetime | None
    trial_ends_at: datetime | None
    grace_period_ends_at: datetime | None
    cancellation_effective_at: datetime | None
    cancellation_reason: str | None
    auto_renew: bool
    payment_method_id: str | None
    snapshot_limits_json: dict[str, Any]
    snapshot_modules_json: list[str]
    snapshot_features_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    plan: SubscriptionPlanResponse | None = None

    @model_validator(mode="before")
    @classmethod
    def check_unloaded_plan(cls, data: Any) -> Any:
        if hasattr(data, "_sa_instance_state"):
            from sqlalchemy.orm import attributes

            state = attributes.instance_state(data)
            if "plan" in state.unloaded:
                return {
                    "id": data.id,
                    "tenant_id": data.tenant_id,
                    "plan_id": data.plan_id,
                    "plan_version": data.plan_version,
                    "status": data.status,
                    "billing_interval": data.billing_interval,
                    "currency": data.currency,
                    "unit_price": data.unit_price,
                    "current_period_start": data.current_period_start,
                    "current_period_end": data.current_period_end,
                    "trial_started_at": data.trial_started_at,
                    "trial_ends_at": data.trial_ends_at,
                    "grace_period_ends_at": data.grace_period_ends_at,
                    "cancellation_effective_at": data.cancellation_effective_at,
                    "cancellation_reason": data.cancellation_reason,
                    "auto_renew": data.auto_renew,
                    "payment_method_id": data.payment_method_id,
                    "snapshot_limits_json": data.snapshot_limits_json,
                    "snapshot_modules_json": data.snapshot_modules_json,
                    "snapshot_features_json": data.snapshot_features_json,
                    "created_at": data.created_at,
                    "updated_at": data.updated_at,
                    "plan": None,
                }
        return data


# -----------------------------------------------------------------------------
# 4. Entitlement Overrides & Effective Entitlements
# -----------------------------------------------------------------------------


class EntitlementOverrideCreateRequest(BaseSchema):
    override_type: OverrideType = OverrideType.CAPABILITY
    target_key: str = Field(..., min_length=2, max_length=128)
    override_value_json: Any
    reason: str = Field(..., min_length=3, max_length=1000)
    duration_days: int = Field(30, ge=1, le=365)


class EntitlementOverrideResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    override_type: str
    target_key: str
    override_value_json: Any
    reason: str
    granted_by_id: UUID
    starts_at: datetime
    expires_at: datetime
    is_active: bool
    created_at: datetime


class EffectiveEntitlementsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tenant_id: UUID
    plan_code: str
    plan_name: str
    subscription_status: str
    is_active: bool
    is_trial: bool
    trial_days_remaining: int
    enabled_modules: list[str]
    feature_capabilities: dict[str, Any]
    resource_limits: dict[str, Any]
    active_overrides: list[EntitlementOverrideResponse]


# -----------------------------------------------------------------------------
# 5. Usage Metering & Quotas
# -----------------------------------------------------------------------------


class SubscriptionUsageRecordRequest(BaseSchema):
    resource_type: str = Field(..., min_length=2, max_length=64)
    quantity: int = Field(1, ge=1)
    idempotency_key: str = Field(..., min_length=8, max_length=128)
    source_subsystem: str = Field("API", max_length=64)
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class SubscriptionUsageEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    resource_type: str
    quantity: int
    idempotency_key: str
    measured_at: datetime
    source_subsystem: str
    metadata_json: dict[str, Any]
    created_at: datetime


class SubscriptionQuotaStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    resource_type: str
    current_usage: int
    soft_limit: int
    hard_limit: int
    remaining_capacity: int
    utilization_percentage: float
    is_exceeded: bool
    unit: str


# -----------------------------------------------------------------------------
# 6. Invoices, Payments & Webhooks
# -----------------------------------------------------------------------------


class SubscriptionInvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    subscription_id: UUID
    invoice_number: str
    billing_period_start: datetime
    billing_period_end: datetime
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    currency: str
    status: str
    due_date: datetime
    paid_at: datetime | None
    line_items_json: list[dict[str, Any]]
    download_url: str | None
    created_at: datetime


class SubscriptionInvoicePaymentRequest(BaseSchema):
    payment_method: str = Field("ONLINE", max_length=32)
    gateway_payment_id: str | None = Field(None, max_length=128)
    client_notes: str | None = Field(None, max_length=500)


class SubscriptionPaymentAttemptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    invoice_id: UUID
    attempt_number: int
    gateway_order_id: str
    gateway_payment_id: str | None
    amount: Decimal
    currency: str
    status: str
    error_code: str | None
    error_message: str | None
    attempted_at: datetime


class SubscriptionWebhookPayload(BaseSchema):
    event_id: str = Field(..., min_length=4, max_length=128)
    event_type: str = Field(..., min_length=4, max_length=128)
    invoice_id: UUID | None = None
    tenant_id: UUID | None = None
    amount: Decimal | None = None
    currency: str = "INR"
    status: str = "SUCCESS"
    metadata_json: dict[str, Any] = Field(default_factory=dict)


# -----------------------------------------------------------------------------
# 7. Plan Changes & Downgrade Impact Assessments
# -----------------------------------------------------------------------------


class SubscriptionChangeRequestCreate(BaseSchema):
    target_plan_id: UUID
    target_billing_interval: BillingInterval = BillingInterval.ANNUAL
    effective_type: str = Field("PERIOD_END", pattern="^(IMMEDIATE|PERIOD_END)$")


class DowngradeImpactPreviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    can_downgrade_immediately: bool
    has_capacity_violations: bool
    violations: list[dict[str, Any]]
    current_plan: str
    target_plan: str
    resource_comparisons: list[dict[str, Any]]
    removed_modules: list[str]
    removed_features: list[str]
    recommended_actions: list[str]


class SubscriptionChangeRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    subscription_id: UUID
    target_plan_id: UUID
    target_billing_interval: str
    change_type: str
    status: str
    effective_type: str
    scheduled_for: datetime | None
    impact_summary_json: dict[str, Any]
    prorated_amount: Decimal
    requested_by_id: UUID
    approved_by_id: UUID | None
    created_at: datetime


# -----------------------------------------------------------------------------
# 8. Customer Success Health & Notes
# -----------------------------------------------------------------------------


class CustomerSuccessHealthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tenant_id: UUID
    health_score: int
    health_status: str
    utilization_score: int
    adoption_score: int
    support_score: int
    financial_score: int
    signals_json: dict[str, Any]
    recommendations: list[str]
    calculated_at: datetime


class CustomerSuccessNoteCreateRequest(BaseSchema):
    note_type: CustomerNoteType = CustomerNoteType.GENERAL
    content: str = Field(..., min_length=3, max_length=5000)
    is_pinned: bool = False


class CustomerSuccessNoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    author_id: UUID
    author_email: str
    note_type: str
    content: str
    is_pinned: bool
    created_at: datetime


class CustomerSuccessTenantSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tenant_id: UUID
    institution_code: str
    institution_name: str
    plan_name: str
    subscription_status: str
    current_period_end: datetime
    days_until_renewal: int
    health_score: int
    health_status: str
    open_critical_tickets: int
    utilization_pct: float
    adoption_pct: float
    requires_attention: bool
