"""SQLAlchemy Entities for CampusOS Enterprise API Platform & Developer Portal (Step 21).

Implements:
- Developer application registry with ownership, environment tiers, and approvals
- Cryptographic application credentials, lifecycle states, and safe rotation
- Granular capability-based scope grants with risk-tiered approval requirements
- API catalog (Products, Operations, Classifications, and Versions)
- Per-application rate limiting and aggregate multi-period quotas
- Privacy-aware, sanitized API usage metering records
- Idempotency guarantees for consequential mutations
- Full application approval and credential lifecycle audit trails
"""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, TenantScopedModel

# -----------------------------------------------------------------------------
# Enums
# -----------------------------------------------------------------------------


class ApplicationType(StrEnum):
    INTERNAL = "INTERNAL"
    MOBILE = "MOBILE"
    WEB = "WEB"
    PARTNER = "PARTNER"
    THIRD_PARTY = "THIRD_PARTY"
    SYSTEM = "SYSTEM"


class ApplicationStatus(StrEnum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"
    ARCHIVED = "ARCHIVED"


class ApplicationEnvironment(StrEnum):
    DEVELOPMENT = "DEVELOPMENT"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"


class CredentialType(StrEnum):
    API_KEY = "API_KEY"
    CLIENT_SECRET = "CLIENT_SECRET"
    OAUTH_CLIENT = "OAUTH_CLIENT"


class CredentialStatus(StrEnum):
    ACTIVE = "ACTIVE"
    ROTATING = "ROTATING"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class ScopeGrantStatus(StrEnum):
    PENDING_APPROVAL = "PENDING_APPROVAL"
    GRANTED = "GRANTED"
    REVOKED = "REVOKED"
    REJECTED = "REJECTED"


class ApiClassification(StrEnum):
    INTERNAL_ONLY = "INTERNAL_ONLY"
    TENANT_API = "TENANT_API"
    PARTNER_API = "PARTNER_API"
    PUBLIC_READ = "PUBLIC_READ"
    PUBLIC_WEBHOOK = "PUBLIC_WEBHOOK"


class ApiLifecycleStatus(StrEnum):
    DRAFT = "DRAFT"
    PREVIEW = "PREVIEW"
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"
    SUNSET = "SUNSET"
    RETIRED = "RETIRED"


class RateLimitTier(StrEnum):
    DEFAULT = "DEFAULT"
    PARTNER = "PARTNER"
    ENTERPRISE = "ENTERPRISE"
    INTERNAL = "INTERNAL"


class QuotaTier(StrEnum):
    DEFAULT = "DEFAULT"
    PARTNER = "PARTNER"
    ENTERPRISE = "ENTERPRISE"
    INTERNAL = "INTERNAL"


class QuotaStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    WARNING = "WARNING"
    EXCEEDED = "EXCEEDED"
    SUSPENDED = "SUSPENDED"


class IdempotencyStatus(StrEnum):
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# -----------------------------------------------------------------------------
# 1. Developer Application
# -----------------------------------------------------------------------------


class DeveloperApplication(TenantScopedModel):
    """Registered application consuming CampusOS platform APIs."""

    __tablename__ = "core_developer_applications"

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    application_type: Mapped[str] = mapped_column(
        String(32), default=ApplicationType.INTERNAL.value, nullable=False, index=True
    )
    owner_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32), default=ApplicationStatus.DRAFT.value, nullable=False, index=True
    )
    environment: Mapped[str] = mapped_column(
        String(32), default=ApplicationEnvironment.DEVELOPMENT.value, nullable=False, index=True
    )

    # Traffic governance & quotas
    rate_limit_tier: Mapped[str] = mapped_column(
        String(32), default=RateLimitTier.DEFAULT.value, nullable=False
    )
    rate_limit_custom: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    quota_tier: Mapped[str] = mapped_column(
        String(32), default=QuotaTier.DEFAULT.value, nullable=False
    )
    quota_custom: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    quota_status: Mapped[str] = mapped_column(
        String(32), default=QuotaStatus.AVAILABLE.value, nullable=False, index=True
    )

    # Network & integration security
    allowed_ips: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    callback_urls: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)

    # Approval lifecycle
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approval_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    credentials: Mapped[list["ApplicationCredential"]] = relationship(
        "ApplicationCredential", back_populates="application", cascade="all, delete-orphan"
    )
    scope_grants: Mapped[list["ApplicationScopeGrant"]] = relationship(
        "ApplicationScopeGrant", back_populates="application", cascade="all, delete-orphan"
    )
    subscriptions: Mapped[list["ApiSubscription"]] = relationship(
        "ApiSubscription", back_populates="application", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_dev_app_tenant_name"),
        Index("idx_dev_app_tenant_status", "tenant_id", "status"),
    )


# -----------------------------------------------------------------------------
# 2. Application Credential (API Keys & Secrets)
# -----------------------------------------------------------------------------


class ApplicationCredential(TenantScopedModel):
    """Cryptographic API credential associated with an application."""

    __tablename__ = "core_application_credentials"

    application_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_developer_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    credential_type: Mapped[str] = mapped_column(
        String(32), default=CredentialType.API_KEY.value, nullable=False
    )
    client_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    key_prefix: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    secret_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    environment: Mapped[str] = mapped_column(
        String(32), default=ApplicationEnvironment.DEVELOPMENT.value, nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(32), default=CredentialStatus.ACTIVE.value, nullable=False, index=True
    )

    # Lifespan and rotation overlap window
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    grace_period_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    revocation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    application: Mapped["DeveloperApplication"] = relationship(
        "DeveloperApplication", back_populates="credentials"
    )

    __table_args__ = (
        Index("idx_app_cred_tenant_app", "tenant_id", "application_id"),
        Index("idx_app_cred_status_env", "status", "environment"),
    )


# -----------------------------------------------------------------------------
# 3. Application Scope Grant
# -----------------------------------------------------------------------------


class ApplicationScopeGrant(TenantScopedModel):
    """Scope authorization attached to an application."""

    __tablename__ = "core_application_scope_grants"

    application_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_developer_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scope_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(32), default=ScopeGrantStatus.GRANTED.value, nullable=False, index=True
    )
    granted_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    application: Mapped["DeveloperApplication"] = relationship(
        "DeveloperApplication", back_populates="scope_grants"
    )

    __table_args__ = (
        UniqueConstraint("application_id", "scope_code", name="uq_app_scope_grant"),
        Index("idx_app_scope_tenant_code", "tenant_id", "scope_code"),
    )


# -----------------------------------------------------------------------------
# 4. API Product & Operation Catalog
# -----------------------------------------------------------------------------


class ApiProduct(BaseModel):
    """Logical grouping of exposed API capabilities."""

    __tablename__ = "core_api_products"

    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String(32), default="v1", nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=ApiLifecycleStatus.ACTIVE.value, nullable=False
    )

    operations: Mapped[list["ApiOperation"]] = relationship(
        "ApiOperation", back_populates="product", cascade="all, delete-orphan"
    )


class ApiOperation(BaseModel):
    """Individual API endpoint definition with exposure classification and lifecycle."""

    __tablename__ = "core_api_operations"

    product_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_api_products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    method: Mapped[str] = mapped_column(String(16), nullable=False)
    path: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(32), default="v1", nullable=False)
    summary: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    scope_required: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    classification: Mapped[str] = mapped_column(
        String(32), default=ApiClassification.INTERNAL_ONLY.value, nullable=False, index=True
    )
    rate_limit_policy: Mapped[str] = mapped_column(String(64), default="DEFAULT", nullable=False)
    governance_policy: Mapped[str] = mapped_column(String(64), default="STANDARD", nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=ApiLifecycleStatus.ACTIVE.value, nullable=False, index=True
    )

    # Deprecation and sunsetting metadata
    deprecated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sunset_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    replacement_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    migration_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    product: Mapped["ApiProduct"] = relationship("ApiProduct", back_populates="operations")

    @property
    def product_code(self) -> str:
        return self.product.code if self.product else ""

    __table_args__ = (
        UniqueConstraint("method", "path", "version", name="uq_api_operation_endpoint"),
        Index("idx_api_op_classification_status", "classification", "status"),
    )


class ApiChangelog(BaseModel):
    """API version change log, tracking breaking changes and deprecations."""

    __tablename__ = "core_api_changelogs"

    version: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    release_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    changes: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    breaking_changes: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    deprecated_operations: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    migration_notes: Mapped[str | None] = mapped_column(Text, nullable=True)


# -----------------------------------------------------------------------------
# 5. API Subscription
# -----------------------------------------------------------------------------


class ApiSubscription(TenantScopedModel):
    """Subscription linking an application to an API product."""

    __tablename__ = "core_api_subscriptions"

    application_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_developer_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False, index=True)
    subscribed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    application: Mapped["DeveloperApplication"] = relationship(
        "DeveloperApplication", back_populates="subscriptions"
    )

    __table_args__ = (
        UniqueConstraint("application_id", "product_code", name="uq_app_product_sub"),
        Index("idx_api_sub_tenant_product", "tenant_id", "product_code"),
    )


# -----------------------------------------------------------------------------
# 6. Aggregate Quota Tracker
# -----------------------------------------------------------------------------


class ApiQuotaUsage(TenantScopedModel):
    """Tracks aggregate consumption counters against application and tenant quotas."""

    __tablename__ = "core_api_quotas"

    application_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_developer_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    period: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True
    )  # YYYY-MM-DD or YYYY-MM
    period_type: Mapped[str] = mapped_column(String(16), nullable=False)  # DAILY or MONTHLY
    requests_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    data_exports_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    webhook_deliveries_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=QuotaStatus.AVAILABLE.value, nullable=False, index=True
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "application_id", "period", "period_type", name="uq_api_quota_tracking"
        ),
        Index("idx_api_quota_tenant_period", "tenant_id", "period"),
    )


# -----------------------------------------------------------------------------
# 7. Privacy-Aware Usage Record
# -----------------------------------------------------------------------------


class ApiUsageRecord(TenantScopedModel):
    """Audit and metering record for every external API interaction."""

    __tablename__ = "core_api_usage_records"

    application_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_developer_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    credential_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )
    api_operation: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    method: Mapped[str] = mapped_column(String(16), nullable=False)
    path: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(32), default="v1", nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    status_code: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    request_size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    response_size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rate_limited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    quota_consumed: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    correlation_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    client_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        Index("idx_usage_tenant_app_time", "tenant_id", "application_id", "timestamp"),
        Index("idx_usage_op_time", "api_operation", "timestamp"),
    )


# -----------------------------------------------------------------------------
# 8. API Idempotency
# -----------------------------------------------------------------------------


class ApiIdempotencyRecord(TenantScopedModel):
    """Guarantees exactly-once execution for sensitive state mutations."""

    __tablename__ = "core_api_idempotency"

    application_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_developer_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=IdempotencyStatus.PROCESSING.value, nullable=False
    )
    response_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "application_id", "idempotency_key", name="uq_api_idempotency_key"
        ),
        Index("idx_idempotency_expiry", "expires_at"),
    )


# -----------------------------------------------------------------------------
# 9. Application Approval Audit
# -----------------------------------------------------------------------------


class ApplicationApprovalAudit(BaseModel):
    """Audit log of developer application approval decisions and lifecycle shifts."""

    __tablename__ = "core_application_approval_audits"

    application_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_developer_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reviewer_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    previous_status: Mapped[str] = mapped_column(String(32), nullable=False)
    new_status: Mapped[str] = mapped_column(String(32), nullable=False)

    __table_args__ = (Index("idx_app_approval_app_time", "application_id", "reviewed_at"),)
