"""SQLAlchemy Entities for Enterprise Customer Success, Subscription Lifecycle & SaaS Entitlements (Step 38).

Implements:
- Configurable SaaS subscription plans with resource allowances and versioning
- Complete tenant subscription lifecycle (trials, activations, renewals, overdues, grace periods, suspensions)
- Centralized entitlement overrides and policy-governed capabilities
- Concurrency-safe usage event ingestion and aggregate quota tracking
- SaaS billing invoices, payment attempts, and cryptographic webhook verification
- Plan change workflows with downgrade capacity impact assessments
- Customer success health scoring, telemetry-backed signals, and platform notes
"""

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, TenantScopedModel

# -----------------------------------------------------------------------------
# 1. Enums
# -----------------------------------------------------------------------------


class SubscriptionPlanStatus(StrEnum):
    """Lifecycle availability of a SaaS packaging plan."""

    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"


class BillingInterval(StrEnum):
    """Recurring billing frequency for SaaS subscriptions."""

    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    ANNUAL = "ANNUAL"


class SubscriptionStatus(StrEnum):
    """Authoritative tenant subscription state machine states."""

    TRIAL_PENDING = "TRIAL_PENDING"
    TRIAL_ACTIVE = "TRIAL_ACTIVE"
    ACTIVE = "ACTIVE"
    PAYMENT_OVERDUE = "PAYMENT_OVERDUE"
    GRACE_PERIOD = "GRACE_PERIOD"
    SUSPENDED = "SUSPENDED"
    CANCELLATION_SCHEDULED = "CANCELLATION_SCHEDULED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class SubscriptionChangeType(StrEnum):
    """Nature of commercial subscription plan modification."""

    UPGRADE = "UPGRADE"
    DOWNGRADE = "DOWNGRADE"
    INTERVAL_CHANGE = "INTERVAL_CHANGE"


class SubscriptionChangeStatus(StrEnum):
    """Status of an institutional plan change workflow."""

    PENDING_APPROVAL = "PENDING_APPROVAL"
    SCHEDULED = "SCHEDULED"
    APPLIED = "APPLIED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class OverrideType(StrEnum):
    """Classification of temporary entitlement overrides."""

    MODULE_GATE = "MODULE_GATE"
    CAPABILITY = "CAPABILITY"
    QUOTA_LIMIT = "QUOTA_LIMIT"


class InvoiceStatus(StrEnum):
    """Financial lifecycle states of SaaS billing invoices."""

    DRAFT = "DRAFT"
    ISSUED = "ISSUED"
    PAID = "PAID"
    PAST_DUE = "PAST_DUE"
    VOID = "VOID"
    REFUNDED = "REFUNDED"


class PaymentStatus(StrEnum):
    """Transaction status of payment attempts."""

    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class CustomerHealthStatus(StrEnum):
    """Calculated account health state for Customer Success governance."""

    HEALTHY = "HEALTHY"
    GOOD = "GOOD"
    NEEDS_ATTENTION = "NEEDS_ATTENTION"
    AT_RISK = "AT_RISK"
    CRITICAL = "CRITICAL"


class CustomerNoteType(StrEnum):
    """Classification of platform-internal customer success interactions."""

    GENERAL = "GENERAL"
    CALL_LOG = "CALL_LOG"
    RENEWAL_RISK = "RENEWAL_RISK"
    EXPANSION_OPPORTUNITY = "EXPANSION_OPPORTUNITY"
    ESCALATION = "ESCALATION"


# -----------------------------------------------------------------------------
# 2. Subscription Plans & Packaging
# -----------------------------------------------------------------------------


class SubscriptionPlan(BaseModel):
    """Global SaaS subscription packaging tier defining price, resource quotas, and modules."""

    __tablename__ = "subscription_plans"
    __table_args__ = (
        UniqueConstraint("code", name="uq_subscription_plan_code"),
        Index("idx_sub_plan_status", "status"),
        Index("idx_sub_plan_interval", "billing_interval"),
    )

    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=SubscriptionPlanStatus.ACTIVE.value, nullable=False
    )
    billing_interval: Mapped[str] = mapped_column(
        String(32), default=BillingInterval.ANNUAL.value, nullable=False
    )
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    base_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    trial_eligible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    trial_duration_days: Mapped[int] = mapped_column(Integer, default=14, nullable=False)

    # Resource allowances & limits
    max_active_users: Mapped[int] = mapped_column(Integer, default=500, nullable=False)
    max_students: Mapped[int] = mapped_column(Integer, default=5000, nullable=False)
    max_faculty: Mapped[int] = mapped_column(Integer, default=250, nullable=False)
    max_storage_bytes: Mapped[int] = mapped_column(BigInteger, default=107374182400, nullable=False)  # 100GB
    max_api_rpm: Mapped[int] = mapped_column(Integer, default=300, nullable=False)
    max_ai_tokens_monthly: Mapped[int] = mapped_column(BigInteger, default=1000000, nullable=False)
    max_integrations: Mapped[int] = mapped_column(Integer, default=10, nullable=False)

    # Modules & Capabilities
    included_modules: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    feature_capabilities: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    support_tier: Mapped[str] = mapped_column(String(64), default="STANDARD", nullable=False)

    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    retired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# -----------------------------------------------------------------------------
# 3. Tenant Subscriptions & Lifecycle
# -----------------------------------------------------------------------------


class TenantSubscription(TenantScopedModel):
    """Institutional commercial subscription record linking an institution to its active plan."""

    __tablename__ = "subscription_tenant_subscriptions"
    __table_args__ = (
        Index("idx_tenant_sub_status", "tenant_id", "status"),
        Index("idx_tenant_sub_period_end", "current_period_end"),
        Index("idx_tenant_sub_plan", "plan_id"),
    )

    plan_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("subscription_plans.id", ondelete="RESTRICT"),
        nullable=False,
    )
    plan_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=SubscriptionStatus.TRIAL_ACTIVE.value, nullable=False
    )
    billing_interval: Mapped[str] = mapped_column(
        String(32), default=BillingInterval.ANNUAL.value, nullable=False
    )
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)

    current_period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    trial_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    grace_period_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    cancellation_effective_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    payment_method_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Immutably captured snapshots at subscription time (protects against upstream plan mutations)
    snapshot_limits_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    snapshot_modules_json: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    snapshot_features_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    # Relationships
    plan: Mapped["SubscriptionPlan"] = relationship("SubscriptionPlan", lazy="joined")


class SubscriptionLifecycleHistory(TenantScopedModel):
    """Immutable chronological audit of subscription state transitions."""

    __tablename__ = "subscription_lifecycle_histories"
    __table_args__ = (
        Index("idx_sub_life_sub", "subscription_id"),
        Index("idx_sub_life_tenant", "tenant_id"),
        Index("idx_sub_life_created", "created_at"),
    )

    subscription_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("subscription_tenant_subscriptions.id", ondelete="CASCADE"),
        nullable=False,
    )
    from_status: Mapped[str] = mapped_column(String(32), nullable=False)
    to_status: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    actor_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    actor_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


# -----------------------------------------------------------------------------
# 4. Entitlement Overrides
# -----------------------------------------------------------------------------


class SubscriptionEntitlementOverride(TenantScopedModel):
    """Explicit, authorized, and time-limited overrides to standard plan entitlements."""

    __tablename__ = "subscription_entitlement_overrides"
    __table_args__ = (
        Index("idx_ent_override_tenant_target", "tenant_id", "target_key"),
        Index("idx_ent_override_expiry", "expires_at", "is_active"),
    )

    override_type: Mapped[str] = mapped_column(
        String(32), default=OverrideType.CAPABILITY.value, nullable=False
    )
    target_key: Mapped[str] = mapped_column(String(128), nullable=False)
    override_value_json: Mapped[Any] = mapped_column(JSONB, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    granted_by_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


# -----------------------------------------------------------------------------
# 5. Usage Metering & Quota Aggregates
# -----------------------------------------------------------------------------


class SubscriptionUsageEvent(TenantScopedModel):
    """Raw metered consumption events with idempotency keys to prevent duplicate tallying."""

    __tablename__ = "subscription_usage_events"
    __table_args__ = (
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_sub_usage_event_idempotency"),
        Index("idx_sub_usage_tenant_res", "tenant_id", "resource_type"),
        Index("idx_sub_usage_measured", "measured_at"),
    )

    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    quantity: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    measured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    source_subsystem: Mapped[str] = mapped_column(String(64), default="API", nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class SubscriptionUsageAggregate(TenantScopedModel):
    """Aggregated resource usage counters per billing cycle."""

    __tablename__ = "subscription_usage_aggregates"
    __table_args__ = (
        UniqueConstraint("tenant_id", "resource_type", "billing_cycle", name="uq_sub_usage_cycle"),
        Index("idx_sub_usage_agg_tenant", "tenant_id", "billing_cycle"),
    )

    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    billing_cycle: Mapped[str] = mapped_column(String(16), nullable=False)  # YYYY-MM
    current_usage: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    soft_limit: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    hard_limit: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    is_exceeded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    overage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# -----------------------------------------------------------------------------
# 6. Invoices, Payments & Webhooks
# -----------------------------------------------------------------------------


class SubscriptionInvoice(TenantScopedModel):
    """Commercial SaaS subscription invoices issued to institutional tenants."""

    __tablename__ = "subscription_invoices"
    __table_args__ = (
        UniqueConstraint("invoice_number", name="uq_sub_invoice_number"),
        Index("idx_sub_inv_tenant_status", "tenant_id", "status"),
        Index("idx_sub_inv_period", "billing_period_start", "billing_period_end"),
    )

    subscription_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("subscription_tenant_subscriptions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    invoice_number: Mapped[str] = mapped_column(String(64), nullable=False)
    billing_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    billing_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=InvoiceStatus.ISSUED.value, nullable=False)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    line_items_json: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)
    download_url: Mapped[str | None] = mapped_column(String(512), nullable=True)


class SubscriptionPaymentAttempt(TenantScopedModel):
    """Audit log of individual payment executions for a subscription invoice."""

    __tablename__ = "subscription_payment_attempts"
    __table_args__ = (
        Index("idx_sub_pay_inv", "invoice_id"),
        Index("idx_sub_pay_gateway", "gateway_order_id", "gateway_payment_id"),
    )

    invoice_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("subscription_invoices.id", ondelete="CASCADE"),
        nullable=False,
    )
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    gateway_order_id: Mapped[str] = mapped_column(String(128), nullable=False)
    gateway_payment_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=PaymentStatus.PENDING.value, nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SubscriptionWebhookEvent(BaseModel):
    """Idempotent store of verified external payment gateway callback events."""

    __tablename__ = "subscription_webhook_events"
    __table_args__ = (
        UniqueConstraint("provider", "event_id", name="uq_sub_webhook_provider_event"),
        Index("idx_sub_webhook_status", "status"),
    )

    event_id: Mapped[str] = mapped_column(String(128), nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    signature: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PROCESSED", nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# -----------------------------------------------------------------------------
# 7. Plan Changes & Downgrade Impact Assessments
# -----------------------------------------------------------------------------


class SubscriptionChangeRequest(TenantScopedModel):
    """Workflow tracking institutional plan change requests (upgrades/downgrades)."""

    __tablename__ = "subscription_change_requests"
    __table_args__ = (
        Index("idx_sub_change_tenant", "tenant_id", "status"),
    )

    subscription_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("subscription_tenant_subscriptions.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_plan_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("subscription_plans.id", ondelete="RESTRICT"),
        nullable=False,
    )
    target_billing_interval: Mapped[str] = mapped_column(String(32), nullable=False)
    change_type: Mapped[str] = mapped_column(
        String(32), default=SubscriptionChangeType.UPGRADE.value, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), default=SubscriptionChangeStatus.PENDING_APPROVAL.value, nullable=False
    )
    effective_type: Mapped[str] = mapped_column(String(32), default="PERIOD_END", nullable=False)
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    impact_summary_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    prorated_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    requested_by_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    approved_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )


# -----------------------------------------------------------------------------
# 8. Customer Success Health & Monitoring
# -----------------------------------------------------------------------------


class CustomerSuccessHealthSnapshot(TenantScopedModel):
    """Composite health evaluation for customer success management based on real operational signals."""

    __tablename__ = "customer_success_health_snapshots"
    __table_args__ = (
        Index("idx_cs_health_tenant", "tenant_id", "calculated_at"),
        Index("idx_cs_health_status", "health_status"),
    )

    health_score: Mapped[int] = mapped_column(Integer, default=100, nullable=False)  # 0 to 100
    health_status: Mapped[str] = mapped_column(
        String(32), default=CustomerHealthStatus.HEALTHY.value, nullable=False
    )
    utilization_score: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    adoption_score: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    support_score: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    financial_score: Mapped[int] = mapped_column(Integer, default=100, nullable=False)

    signals_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    recommendations: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CustomerSuccessNote(TenantScopedModel):
    """Platform-internal customer success log entry, strictly invisible to tenant users."""

    __tablename__ = "customer_success_notes"
    __table_args__ = (
        Index("idx_cs_note_tenant", "tenant_id", "created_at"),
    )

    author_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    author_email: Mapped[str] = mapped_column(String(255), nullable=False)
    note_type: Mapped[str] = mapped_column(
        String(32), default=CustomerNoteType.GENERAL.value, nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
