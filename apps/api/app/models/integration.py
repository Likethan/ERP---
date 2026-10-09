"""SQLAlchemy entities for CampusOS Enterprise Integration & Interoperability Layer.

Implements:
- Connector abstractions and lifecycle models
- Encrypted credential references (never plaintext secrets)
- Integration health and telemetry tracking
- Outbound and inbound webhook subscriptions, deliveries, and attempts
- Field mapping, data transformation, and external ID registries
- Controlled bidirectional synchronization configs and run telemetry
- Sanitized, forensic integration audit logs
- Inbound webhook and callback idempotency protection
"""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

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
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, BaseModel, SoftDeleteMixin, TenantScopedModel


class ConnectorOwnership(StrEnum):
    TENANT = "TENANT"
    PLATFORM = "PLATFORM"


class ConnectorType(StrEnum):
    REST_API = "REST_API"
    WEBHOOK = "WEBHOOK"
    OAUTH2 = "OAUTH2"
    API_KEY = "API_KEY"
    SMTP = "SMTP"
    PAYMENT = "PAYMENT"
    STORAGE = "STORAGE"
    IDENTITY = "IDENTITY"
    MESSAGING = "MESSAGING"
    ERP = "ERP"
    LMS = "LMS"
    BI = "BI"
    CUSTOM = "CUSTOM"


class ConnectorStatus(StrEnum):
    DRAFT = "DRAFT"
    CONFIGURED = "CONFIGURED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ERROR = "ERROR"
    DISABLED = "DISABLED"
    REVOKED = "REVOKED"


class CredentialAuthType(StrEnum):
    API_KEY = "API_KEY"
    BEARER_TOKEN = "BEARER_TOKEN"
    BASIC_AUTH = "BASIC_AUTH"
    OAUTH2 = "OAUTH2"
    HMAC_SECRET = "HMAC_SECRET"


class IntegrationHealthStatus(StrEnum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    UNKNOWN = "UNKNOWN"


class CircuitBreakerState(StrEnum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class WebhookStatus(StrEnum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    DISABLED = "DISABLED"


class WebhookDeliveryStatus(StrEnum):
    PENDING = "PENDING"
    DELIVERING = "DELIVERING"
    DELIVERED = "DELIVERED"
    RETRYING = "RETRYING"
    FAILED = "FAILED"
    DEAD_LETTER = "DEAD_LETTER"


class SyncDirection(StrEnum):
    IMPORT = "IMPORT"
    EXPORT = "EXPORT"
    BIDIRECTIONAL = "BIDIRECTIONAL"


class SyncRunStatus(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class SyncItemAction(StrEnum):
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    SKIPPED = "SKIPPED"
    CONFLICT = "CONFLICT"
    FAILED = "FAILED"


class ConflictResolutionStrategy(StrEnum):
    NO_ACTION = "NO_ACTION"
    FLAG = "FLAG"
    QUEUE_FOR_REVIEW = "QUEUE_FOR_REVIEW"
    SOURCE_WINS = "SOURCE_WINS"
    TARGET_WINS = "TARGET_WINS"


class IntegrationLogStatus(StrEnum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"
    BLOCKED = "BLOCKED"


class IntegrationCredential(BaseModel):
    """Encrypted credential vault reference. Plaintext secrets are never stored in normal columns."""

    __tablename__ = "integration_credentials"
    __table_args__ = (
        Index("idx_int_cred_tenant", "tenant_id"),
        Index("idx_int_cred_ownership", "ownership_level"),
    )

    tenant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    ownership_level: Mapped[str] = mapped_column(
        String(32), default=ConnectorOwnership.TENANT, nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    auth_type: Mapped[str] = mapped_column(
        String(32), default=CredentialAuthType.API_KEY, nullable=False
    )
    encrypted_data: Mapped[str] = mapped_column(Text, nullable=False)
    masked_preview: Mapped[str] = mapped_column(String(128), nullable=False)
    key_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )


class IntegrationConnector(BaseModel, SoftDeleteMixin):
    """Institutional or Platform-level External Integration Connector."""

    __tablename__ = "integration_connectors"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_connector_tenant_code"),
        Index("idx_connector_tenant_status", "tenant_id", "status"),
        Index("idx_connector_provider", "provider_key"),
        Index("idx_connector_ownership", "ownership_level"),
    )

    tenant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    ownership_level: Mapped[str] = mapped_column(
        String(32), default=ConnectorOwnership.TENANT, nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_key: Mapped[str] = mapped_column(String(64), nullable=False)
    connector_type: Mapped[str] = mapped_column(
        String(32), default=ConnectorType.REST_API, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), default=ConnectorStatus.DRAFT, nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    configuration: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    credential_reference: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("integration_credentials.id", ondelete="SET NULL"),
        nullable=True,
    )
    allowed_domains: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    created_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    credential: Mapped[IntegrationCredential | None] = relationship(
        "IntegrationCredential", foreign_keys=[credential_reference]
    )
    health: Mapped["IntegrationHealth | None"] = relationship(
        "IntegrationHealth", back_populates="connector", uselist=False, cascade="all, delete-orphan"
    )
    webhooks: Mapped[list["IntegrationWebhookSubscription"]] = relationship(
        "IntegrationWebhookSubscription", back_populates="connector", cascade="all, delete-orphan"
    )
    sync_configs: Mapped[list["IntegrationSyncConfig"]] = relationship(
        "IntegrationSyncConfig", back_populates="connector", cascade="all, delete-orphan"
    )


class IntegrationHealth(BaseModel):
    """Live health, availability, latency, and circuit breaker metrics for a connector."""

    __tablename__ = "integration_health"
    __table_args__ = (
        Index("idx_int_health_status", "status"),
        Index("idx_int_health_connector", "connector_id"),
    )

    tenant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    connector_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("integration_connectors.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    status: Mapped[str] = mapped_column(
        String(32), default=IntegrationHealthStatus.UNKNOWN, nullable=False
    )
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_failure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    circuit_state: Mapped[str] = mapped_column(
        String(32), default=CircuitBreakerState.CLOSED, nullable=False
    )
    circuit_opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    connector: Mapped[IntegrationConnector] = relationship("IntegrationConnector", back_populates="health")


class IntegrationWebhookSubscription(BaseModel, SoftDeleteMixin):
    """Institutional outbound webhook subscription endpoint."""

    __tablename__ = "integration_webhook_subscriptions"
    __table_args__ = (
        Index("idx_webhook_tenant_status", "tenant_id", "status"),
        Index("idx_webhook_connector", "connector_id"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    connector_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("integration_connectors.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    endpoint_url: Mapped[str] = mapped_column(String(512), nullable=False)
    event_types: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    status: Mapped[str] = mapped_column(
        String(32), default=WebhookStatus.ACTIVE, nullable=False
    )
    secret_reference: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("integration_credentials.id", ondelete="SET NULL"),
        nullable=True,
    )
    filter_criteria: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    connector: Mapped[IntegrationConnector | None] = relationship(
        "IntegrationConnector", back_populates="webhooks"
    )
    deliveries: Mapped[list["IntegrationWebhookDelivery"]] = relationship(
        "IntegrationWebhookDelivery", back_populates="subscription", cascade="all, delete-orphan"
    )


class IntegrationWebhookDelivery(BaseModel):
    """Individual outbound webhook delivery execution record."""

    __tablename__ = "integration_webhook_deliveries"
    __table_args__ = (
        Index("idx_delivery_tenant_status", "tenant_id", "status"),
        Index("idx_delivery_subscription", "subscription_id"),
        Index("idx_delivery_event", "event_id"),
        Index("idx_delivery_next_attempt", "next_attempt_at"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subscription_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("integration_webhook_subscriptions.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(
        String(32), default=WebhookDeliveryStatus.PENDING, nullable=False
    )
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    response_status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    subscription: Mapped[IntegrationWebhookSubscription] = relationship(
        "IntegrationWebhookSubscription", back_populates="deliveries"
    )
    attempts: Mapped[list["IntegrationWebhookAttempt"]] = relationship(
        "IntegrationWebhookAttempt", back_populates="delivery", cascade="all, delete-orphan"
    )


class IntegrationWebhookAttempt(BaseModel):
    """Detailed audit of a single HTTP attempt for a webhook delivery."""

    __tablename__ = "integration_webhook_attempts"
    __table_args__ = (
        Index("idx_attempt_delivery", "delivery_id"),
    )

    delivery_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("integration_webhook_deliveries.id", ondelete="CASCADE"),
        nullable=False,
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_body_preview: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    delivery: Mapped[IntegrationWebhookDelivery] = relationship(
        "IntegrationWebhookDelivery", back_populates="attempts"
    )


class IntegrationDataMapping(BaseModel):
    """Institutional entity and field transformation schema."""

    __tablename__ = "integration_data_mappings"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_data_mapping_tenant_name"),
        Index("idx_mapping_tenant", "tenant_id"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    target_type: Mapped[str] = mapped_column(String(64), nullable=False)
    rules: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    created_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )


class IntegrationSyncConfig(BaseModel, SoftDeleteMixin):
    """Scheduled or event-driven dataset synchronization specification."""

    __tablename__ = "integration_sync_configs"
    __table_args__ = (
        Index("idx_sync_tenant_status", "tenant_id", "status"),
        Index("idx_sync_connector", "connector_id"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    connector_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("integration_connectors.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    direction: Mapped[str] = mapped_column(
        String(32), default=SyncDirection.IMPORT, nullable=False
    )
    mapping_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("integration_data_mappings.id", ondelete="SET NULL"),
        nullable=True,
    )
    conflict_strategy: Mapped[str] = mapped_column(
        String(32), default=ConflictResolutionStrategy.SOURCE_WINS, nullable=False
    )
    interval_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    connector: Mapped[IntegrationConnector] = relationship(
        "IntegrationConnector", back_populates="sync_configs"
    )
    mapping: Mapped[IntegrationDataMapping | None] = relationship("IntegrationDataMapping")
    runs: Mapped[list["IntegrationSyncRun"]] = relationship(
        "IntegrationSyncRun", back_populates="sync_config", cascade="all, delete-orphan"
    )


class IntegrationSyncRun(BaseModel):
    """Execution telemetry for a synchronization job run."""

    __tablename__ = "integration_sync_runs"
    __table_args__ = (
        Index("idx_sync_run_tenant_status", "tenant_id", "status"),
        Index("idx_sync_run_config", "sync_config_id"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sync_config_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("integration_sync_configs.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32), default=SyncRunStatus.QUEUED, nullable=False
    )
    records_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_skipped: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    sync_config: Mapped[IntegrationSyncConfig] = relationship(
        "IntegrationSyncConfig", back_populates="runs"
    )
    items: Mapped[list["IntegrationSyncItem"]] = relationship(
        "IntegrationSyncItem", back_populates="sync_run", cascade="all, delete-orphan"
    )


class IntegrationSyncItem(BaseModel):
    """Granular per-record audit result of a sync execution run."""

    __tablename__ = "integration_sync_items"
    __table_args__ = (
        Index("idx_sync_item_run", "sync_run_id"),
    )

    sync_run_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("integration_sync_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)
    internal_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    action: Mapped[str] = mapped_column(String(32), default=SyncItemAction.SKIPPED, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="SUCCESS", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    sync_run: Mapped[IntegrationSyncRun] = relationship(
        "IntegrationSyncRun", back_populates="items"
    )


class ExternalResourceMapping(BaseModel):
    """Canonical mapping table between external system identifiers and internal domain UUIDs."""

    __tablename__ = "integration_external_resource_mappings"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "connector_id",
            "external_resource_type",
            "external_id",
            name="uq_ext_mapping_unique_remote",
        ),
        Index("idx_ext_mapping_internal", "tenant_id", "internal_resource_type", "internal_id"),
        Index("idx_ext_mapping_connector", "connector_id"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    connector_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("integration_connectors.id", ondelete="CASCADE"),
        nullable=False,
    )
    external_resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)
    internal_resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    internal_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    last_synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class IntegrationLog(BaseModel):
    """Forensic, sanitized audit log for all integration operations."""

    __tablename__ = "integration_logs"
    __table_args__ = (
        Index("idx_int_log_tenant_created", "tenant_id", "created_at"),
        Index("idx_int_log_connector", "connector_id"),
        Index("idx_int_log_correlation", "correlation_id"),
    )

    tenant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    connector_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("integration_connectors.id", ondelete="SET NULL"),
        nullable=True,
    )
    operation: Mapped[str] = mapped_column(String(64), nullable=False)
    event_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=IntegrationLogStatus.SUCCESS, nullable=False
    )
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)


class IntegrationIdempotencyKey(BaseModel):
    """Idempotency tracking record for inbound webhooks and payment callbacks."""

    __tablename__ = "integration_idempotency_keys"
    __table_args__ = (
        UniqueConstraint("tenant_id", "scope", "idempotency_key", name="uq_int_idempotency_key"),
        Index("idx_int_idemp_expires", "expires_at"),
    )

    tenant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    scope: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PROCESSING", nullable=False)
    response_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
