"""Enterprise Notification, Communication & Delivery Orchestration Domain Models (Step 26).

Implements:
- Event-driven notifications with standard event representations and minimal sanitized payloads.
- Configurable notification rules with priority, recipient strategies, channel selection, and declarative policy conditions.
- Versioned message templates with strict variable schemas, safe HTML escaping, and immutable active versions.
- Provider abstractions and delivery tracking with attempt logs, latency, and failure classification.
- Controlled suppression lists, user delivery preferences, quiet hours scheduling, and batch digests.
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING
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
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, TenantScopedModel

if TYPE_CHECKING:
    from app.models.campus import NotificationDelivery

# Cross-dialect JSON type for PostgreSQL JSONB and SQLite JSON
JSONType = JSONB


class NotificationChannel(StrEnum):
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    SMS = "SMS"
    PUSH = "PUSH"


class DeliveryStatus(StrEnum):
    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    PROCESSING = "PROCESSING"
    SUBMITTED = "SUBMITTED"
    DELIVERED = "DELIVERED"
    RETRY_WAIT = "RETRY_WAIT"
    FAILED = "FAILED"
    SUPPRESSED = "SUPPRESSED"
    CANCELLED = "CANCELLED"
    READ = "READ"
    UNKNOWN = "UNKNOWN"


class TemplateStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DEPRECATED = "DEPRECATED"


class RecipientStrategy(StrEnum):
    DIRECT = "DIRECT"
    STUDENT = "STUDENT"
    FACULTY = "FACULTY"
    STAFF = "STAFF"
    PARENT = "PARENT"
    ROLE = "ROLE"
    ASSIGNEE = "ASSIGNEE"
    ADMIN = "ADMIN"
    GROUP = "GROUP"


class ChannelStrategy(StrEnum):
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    SMS = "SMS"
    PUSH = "PUSH"
    MULTI_CHANNEL = "MULTI_CHANNEL"
    PREFERENCE_BASED = "PREFERENCE_BASED"


class ProviderType(StrEnum):
    IN_APP = "IN_APP"
    GENERIC_SMTP = "GENERIC_SMTP"
    GENERIC_SMS = "GENERIC_SMS"
    GENERIC_PUSH = "GENERIC_PUSH"
    MOCK = "MOCK"


class ProviderHealthStatus(StrEnum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    UNCONFIGURED = "UNCONFIGURED"


class FailureClassification(StrEnum):
    RETRYABLE = "RETRYABLE"
    PERMANENT = "PERMANENT"
    RATE_LIMITED = "RATE_LIMITED"
    TIMEOUT = "TIMEOUT"
    INVALID_RECIPIENT = "INVALID_RECIPIENT"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    UNCONFIGURED_CHANNEL = "UNCONFIGURED_CHANNEL"


class SuppressionReason(StrEnum):
    USER_OPT_OUT = "USER_OPT_OUT"
    QUIET_HOURS = "QUIET_HOURS"
    INVALID_ADDRESS = "INVALID_ADDRESS"
    BOUNCE = "BOUNCE"
    COMPLAINT = "COMPLAINT"
    MANUAL_SUPPRESSION = "MANUAL_SUPPRESSION"
    RATE_LIMITED = "RATE_LIMITED"
    POLICY_SUPPRESSED = "POLICY_SUPPRESSED"


class SensitivityClassification(StrEnum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"


class DigestType(StrEnum):
    DAILY_TASKS = "DAILY_TASKS"
    DEADLINES = "DEADLINES"
    ANNOUNCEMENTS = "ANNOUNCEMENTS"
    WEEKLY_SUMMARY = "WEEKLY_SUMMARY"


# -----------------------------------------------------------------------------
# 1. NOTIFICATION EVENT MODEL
# -----------------------------------------------------------------------------
class NotificationEvent(TenantScopedModel):
    """Standardized representation of a domain-generated notification event."""

    __tablename__ = "notification_events"
    __table_args__ = (
        Index("ix_notif_events_tenant_type", "tenant_id", "event_type"),
        Index("ix_notif_events_tenant_status", "tenant_id", "status"),
        Index("ix_notif_events_correlation", "correlation_id"),
    )

    event_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), default=uuid4, nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    source_module: Mapped[str] = mapped_column(String(64), nullable=False, default="SYSTEM")
    source_entity_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_entity_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    event_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    recipient_context_json: Mapped[dict | list | None] = mapped_column(
        JSONType, default=dict, nullable=False
    )
    payload_json: Mapped[dict | list | None] = mapped_column(
        JSONType, default=dict, nullable=False
    )
    sensitivity_classification: Mapped[str] = mapped_column(
        String(32), default=SensitivityClassification.INTERNAL, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), default="PENDING", nullable=False
    )  # PENDING, PROCESSED, FAILED, SUPPRESSED
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


# -----------------------------------------------------------------------------
# 2. NOTIFICATION RULES
# -----------------------------------------------------------------------------
class NotificationRule(BaseModel):
    """Configurable routing and dispatch rule mapping domain events to templates and channels."""

    __tablename__ = "notification_rules"
    __table_args__ = (
        UniqueConstraint("tenant_id", "rule_key", name="uq_notif_rule_tenant_key"),
        Index("ix_notif_rules_tenant_event", "tenant_id", "event_type", "is_enabled"),
    )

    tenant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    rule_key: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    module_scope: Mapped[str | None] = mapped_column(String(64), nullable=True)
    priority: Mapped[str] = mapped_column(String(32), default="NORMAL", nullable=False)
    recipient_strategy: Mapped[str] = mapped_column(
        String(32), default=RecipientStrategy.DIRECT, nullable=False
    )
    recipient_config_json: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    channel_strategy: Mapped[str] = mapped_column(
        String(32), default=ChannelStrategy.PREFERENCE_BASED, nullable=False
    )
    channels_json: Mapped[list | None] = mapped_column(
        JSONType, default=lambda: ["IN_APP"], nullable=False
    )
    template_key: Mapped[str] = mapped_column(String(64), nullable=False)
    conditions_json: Mapped[list | None] = mapped_column(JSONType, nullable=True)
    suppression_policy_json: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    scheduling_policy_json: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    effective_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )
    updated_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )


# -----------------------------------------------------------------------------
# 3. MESSAGE TEMPLATES & VERSIONING
# -----------------------------------------------------------------------------
class NotificationTemplate(BaseModel):
    """Institutional template header managing lifecycle and versions per channel."""

    __tablename__ = "notification_templates"
    __table_args__ = (
        UniqueConstraint("tenant_id", "template_key", "channel", name="uq_notif_tmpl_tenant_key_chan"),
        Index("ix_notif_templates_tenant_cat", "tenant_id", "category"),
    )

    tenant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    template_key: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    channel: Mapped[str] = mapped_column(
        String(32), default=NotificationChannel.IN_APP, nullable=False
    )
    category: Mapped[str] = mapped_column(String(64), default="ANNOUNCEMENTS", nullable=False)
    current_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=TemplateStatus.DRAFT, nullable=False
    )
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    effective_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )
    updated_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )

    versions: Mapped[list["NotificationTemplateVersion"]] = relationship(
        "NotificationTemplateVersion",
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="NotificationTemplateVersion.version.desc()",
        lazy="selectin",
    )


class NotificationTemplateVersion(BaseModel):
    """Immutable version of a rendered message template."""

    __tablename__ = "notification_template_versions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "template_id", "version", name="uq_notif_tmpl_version"),
        Index("ix_notif_versions_template", "tenant_id", "template_id", "status"),
    )

    tenant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    template_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("notification_templates.id", ondelete="CASCADE"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=TemplateStatus.DRAFT, nullable=False
    )
    locale: Mapped[str] = mapped_column(String(16), default="en", nullable=False)
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)
    body_html_template: Mapped[str | None] = mapped_column(Text, nullable=True)
    variable_schema_json: Mapped[dict | None] = mapped_column(JSONType, default=dict, nullable=False)
    sample_context_json: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    template: Mapped["NotificationTemplate"] = relationship(
        "NotificationTemplate", back_populates="versions"
    )


# -----------------------------------------------------------------------------
# 4. DELIVERY ATTEMPTS & PROVIDER AUDITING
# -----------------------------------------------------------------------------
class NotificationDeliveryAttempt(TenantScopedModel):
    """Audit log of each individual provider communication attempt."""

    __tablename__ = "notification_delivery_attempts"
    __table_args__ = (
        Index("ix_notif_attempts_delivery", "tenant_id", "delivery_id"),
        Index("ix_notif_attempts_provider", "tenant_id", "provider", "status"),
    )

    delivery_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("campus_notification_deliveries.id", ondelete="CASCADE"),
        nullable=False,
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    response_payload_json: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_retryable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    delivery: Mapped["NotificationDelivery"] = relationship(
        "NotificationDelivery", back_populates="attempts"
    )


# -----------------------------------------------------------------------------
# 5. PROVIDER CONFIGURATIONS
# -----------------------------------------------------------------------------
class NotificationProviderConfig(TenantScopedModel):
    """Institutional provider settings and credentials reference."""

    __tablename__ = "notification_provider_configs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "provider_key", name="uq_notif_provider_tenant_key"),
        Index("ix_notif_providers_channel", "tenant_id", "channel", "is_enabled"),
    )

    provider_key: Mapped[str] = mapped_column(String(64), nullable=False)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_type: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), default="Default Provider", nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    configuration_json: Mapped[dict | None] = mapped_column(
        JSONType, default=dict, nullable=False
    )
    health_status: Mapped[str] = mapped_column(
        String(32), default=ProviderHealthStatus.UNCONFIGURED, nullable=False
    )
    last_health_check_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    health_details_json: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    webhook_signing_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    credentials_vault_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)


# -----------------------------------------------------------------------------
# 6. SUPPRESSION LISTS & CONSENT
# -----------------------------------------------------------------------------
class NotificationSuppression(TenantScopedModel):
    """Tenant-isolated suppression records preventing dispatch to invalid or unsubscribed recipients."""

    __tablename__ = "notification_suppressions"
    __table_args__ = (
        Index("ix_notif_suppressions_recipient", "tenant_id", "recipient_identifier", "channel"),
        Index("ix_notif_suppressions_active", "tenant_id", "is_active"),
    )

    channel: Mapped[str] = mapped_column(String(32), default="ALL", nullable=False)
    recipient_identifier: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str] = mapped_column(
        String(64), default=SuppressionReason.BOUNCE, nullable=False
    )
    origin: Mapped[str] = mapped_column(String(64), default="AUTOMATIC", nullable=False)
    suppressed_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )


# -----------------------------------------------------------------------------
# 7. DIGEST RUNS
# -----------------------------------------------------------------------------
class NotificationDigestRun(TenantScopedModel):
    """Execution log for scheduled recipient digests preventing duplicate runs."""

    __tablename__ = "notification_digest_runs"
    __table_args__ = (
        Index("ix_notif_digest_tenant_period", "tenant_id", "digest_type", "period_start", "period_end"),
    )

    digest_type: Mapped[str] = mapped_column(String(64), nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recipient_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notifications_aggregated_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


# -----------------------------------------------------------------------------
# 8. USER NOTIFICATION PROFILE (QUIET HOURS, TIMEZONE, DIGESTS)
# -----------------------------------------------------------------------------
class UserNotificationProfile(TenantScopedModel):
    """User delivery preferences, quiet hours scheduling, and digest subscriptions."""

    __tablename__ = "notification_user_settings"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", name="uq_notif_user_settings_tenant_user"),
        Index("ix_notif_user_settings_user", "tenant_id", "user_id"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="CASCADE"),
        nullable=False,
    )
    quiet_hours_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    quiet_hours_start: Mapped[str | None] = mapped_column(String(8), default="22:00", nullable=True)
    quiet_hours_end: Mapped[str | None] = mapped_column(String(8), default="07:00", nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Kolkata", nullable=False)
    locale: Mapped[str] = mapped_column(String(16), default="en", nullable=False)
    digest_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    digest_frequency: Mapped[str] = mapped_column(String(32), default="DAILY", nullable=False)
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sms_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    in_app_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user = relationship("User")
