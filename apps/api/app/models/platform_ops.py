"""SQLAlchemy Entities for CampusOS Enterprise Platform Administration, SaaS Operations & Tenant Lifecycle Management (Step 30).

Implements:
- Tenant lifecycle state machine history & audit transitions
- Multi-stage idempotent tenant provisioning pipeline tracking
- Centralized subscription plans, licensing, and feature entitlements
- Tenant quotas, resource limits, and capacity monitoring
- Audited, time-limited platform support access sessions
- Governance-aware deactivation and deletion approval plans
"""

from datetime import datetime
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
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel

# -----------------------------------------------------------------------------
# 1. Enums
# -----------------------------------------------------------------------------


class TenantLifecycleStatus(StrEnum):
    """Authoritative tenant operational lifecycle states."""

    PROVISIONING = "PROVISIONING"
    TRIAL = "TRIAL"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DEACTIVATION_PENDING = "DEACTIVATION_PENDING"
    DEACTIVATED = "DEACTIVATED"
    DELETION_PENDING = "DELETION_PENDING"
    DELETED = "DELETED"
    ARCHIVED = "ARCHIVED"  # Backwards compatibility alias


class TenantProvisioningStage(StrEnum):
    """Ordered stages of the automated institutional onboarding pipeline."""

    TENANT_INITIALIZED = "TENANT_INITIALIZED"
    DEFAULT_ROLES = "DEFAULT_ROLES"
    ADMIN_SETUP = "ADMIN_SETUP"
    ACADEMIC_DEFAULTS = "ACADEMIC_DEFAULTS"
    ENTITLEMENTS_SETUP = "ENTITLEMENTS_SETUP"
    CONFIG_DEFAULTS = "CONFIG_DEFAULTS"
    MODULES_SETUP = "MODULES_SETUP"
    STORAGE_NAMESPACE = "STORAGE_NAMESPACE"
    READINESS_VERIFIED = "READINESS_VERIFIED"
    COMPLETED = "COMPLETED"


class TenantProvisioningStatus(StrEnum):
    """Status of an individual provisioning stage execution."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"


class PlatformPlanTier(StrEnum):
    """Institutional SaaS commercial subscription and packaging tier."""

    FREE = "FREE"
    STARTER = "STARTER"
    PROFESSIONAL = "PROFESSIONAL"
    ENTERPRISE = "ENTERPRISE"


class TenantResourceType(StrEnum):
    """Measurable resource dimensions subject to institutional quota governance."""

    ACTIVE_USERS = "ACTIVE_USERS"
    CAMPUS_COUNT = "CAMPUS_COUNT"
    STORAGE_BYTES = "STORAGE_BYTES"
    API_CALLS_MONTHLY = "API_CALLS_MONTHLY"
    AI_TOKENS_MONTHLY = "AI_TOKENS_MONTHLY"
    ENABLED_MODULES = "ENABLED_MODULES"


class DeletionPlanStatus(StrEnum):
    """Lifecycle states of an institutional deletion governance workflow."""

    PROPOSED = "PROPOSED"
    ELIGIBILITY_CHECKED = "ELIGIBILITY_CHECKED"
    APPROVED = "APPROVED"
    BLOCKED = "BLOCKED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"


# -----------------------------------------------------------------------------
# 2. Tenant Lifecycle Transition History
# -----------------------------------------------------------------------------


class TenantLifecycleTransition(BaseModel):
    """Forensic record of a state machine transition in an institution's SaaS lifecycle."""

    __tablename__ = "platform_tenant_lifecycle_transitions"
    __table_args__ = (
        Index("idx_lifecycle_trans_tenant", "tenant_id"),
        Index("idx_lifecycle_trans_status", "from_status", "to_status"),
        Index("idx_lifecycle_trans_created", "created_at"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=False,
    )
    from_status: Mapped[str] = mapped_column(String(32), nullable=False)
    to_status: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    actor_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    correlation_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


# -----------------------------------------------------------------------------
# 3. Tenant Provisioning Stage Tracking
# -----------------------------------------------------------------------------


class TenantProvisioningOperation(BaseModel):
    """Execution state tracking for each discrete stage of automated tenant onboarding."""

    __tablename__ = "platform_tenant_provisioning_operations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "stage", name="uq_tenant_provision_stage"),
        Index("idx_tenant_prov_status", "tenant_id", "status"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=False,
    )
    stage: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=TenantProvisioningStatus.PENDING, nullable=False
    )
    attempt_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    details_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# -----------------------------------------------------------------------------
# 4. Tenant Feature Entitlement & Subscription Packaging
# -----------------------------------------------------------------------------


class TenantEntitlement(BaseModel):
    """Authoritative backend definition of an institution's plan, feature flags, and limits."""

    __tablename__ = "platform_tenant_entitlements"
    __table_args__ = (
        Index("idx_tenant_entitlement_plan", "plan"),
        Index("idx_tenant_entitlement_trial", "is_trial", "trial_ends_at"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    plan: Mapped[str] = mapped_column(
        String(32), default=PlatformPlanTier.ENTERPRISE, nullable=False
    )
    max_users: Mapped[int] = mapped_column(Integer, default=10000, nullable=False)
    max_campuses: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    max_storage_bytes: Mapped[int] = mapped_column(BigInteger, default=107374182400, nullable=False)  # 100 GB
    max_api_rpm: Mapped[int] = mapped_column(Integer, default=300, nullable=False)
    max_ai_tokens_monthly: Mapped[int] = mapped_column(BigInteger, default=1000000, nullable=False)
    enabled_modules: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    feature_entitlements: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )
    is_trial: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    grace_period_ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    custom_limits: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    updated_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )


# -----------------------------------------------------------------------------
# 5. Tenant Resource Quota Usage & Governance
# -----------------------------------------------------------------------------


class TenantResourceQuotaUsage(BaseModel):
    """Resource consumption metrics, limits, and threshold breach indicators per tenant."""

    __tablename__ = "platform_tenant_quota_usage"
    __table_args__ = (
        UniqueConstraint("tenant_id", "resource_type", name="uq_tenant_resource_quota"),
        Index("idx_quota_usage_tenant_res", "tenant_id", "resource_type"),
        Index("idx_quota_usage_exceeded", "is_exceeded"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=False,
    )
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    current_usage: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    soft_limit: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    hard_limit: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    unit: Mapped[str] = mapped_column(String(32), default="COUNT", nullable=False)
    warning_threshold_percent: Mapped[int] = mapped_column(Integer, default=80, nullable=False)
    period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_exceeded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    warning_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# -----------------------------------------------------------------------------
# 6. Controlled Platform Support Access Sessions
# -----------------------------------------------------------------------------


class PlatformSupportSession(BaseModel):
    """Time-limited, purpose-bound, and strictly audited support access delegation."""

    __tablename__ = "platform_support_access_sessions"
    __table_args__ = (
        Index("idx_support_sess_tenant_active", "tenant_id", "is_active"),
        Index("idx_support_sess_expires", "expires_at"),
        Index("idx_support_sess_operator", "operator_user_id"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=False,
    )
    operator_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    ticket_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    permissions_scope: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    revocation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


# -----------------------------------------------------------------------------
# 7. Tenant Deletion Governance & Audit Plan
# -----------------------------------------------------------------------------


class TenantDeletionAuditPlan(BaseModel):
    """Audited pre-flight analysis and execution record for tenant decommissioning."""

    __tablename__ = "platform_tenant_deletion_plans"
    __table_args__ = (
        Index("idx_del_plan_tenant_status", "tenant_id", "status"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32), default=DeletionPlanStatus.PROPOSED, nullable=False
    )
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
    retention_clearance: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    legal_holds_clearance: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    financial_clearance: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    export_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    blocking_reasons: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    impact_summary_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )
    scheduled_deletion_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
