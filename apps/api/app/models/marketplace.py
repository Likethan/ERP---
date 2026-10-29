"""SQLAlchemy Models for Step 39: Enterprise Marketplace, App Integrations & Extensibility Ecosystem.

Provides:
- Marketplace catalog entities and versioned app releases
- Tenant-scoped app installations and connection lifecycle states
- Immutable connection state transition histories
- Resumable incremental sync checkpoints
- Conflict detection and resolution governance
- Sync execution runs and telemetry
"""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

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
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, TenantScopedModel

# -----------------------------------------------------------------------------
# 1. Enums
# -----------------------------------------------------------------------------


class MarketplaceAppCategory(StrEnum):
    """Classification of third-party ecosystem integrations."""

    LMS = "LMS"
    PAYMENT_GATEWAY = "PAYMENT_GATEWAY"
    PAYMENT = "PAYMENT_GATEWAY"  # Alias
    VIDEO_CONFERENCING = "VIDEO_CONFERENCING"
    HARDWARE_IOT = "HARDWARE_IOT"
    GOVERNMENT_EXCHANGE = "GOVERNMENT_EXCHANGE"
    COMMUNICATION = "COMMUNICATION"
    CLOUD_STORAGE = "CLOUD_STORAGE"
    ANALYTICS = "ANALYTICS"
    IDENTITY = "IDENTITY"
    IDENTITY_PROVIDER = "IDENTITY_PROVIDER"
    LIBRARY = "LIBRARY"
    LIBRARY_SYSTEM = "LIBRARY_SYSTEM"
    BIOMETRIC = "BIOMETRIC"
    PLACEMENT = "PLACEMENT"
    RECRUITMENT = "RECRUITMENT"
    REGULATORY = "REGULATORY"
    OTHER = "OTHER"


class MarketplacePublicationStatus(StrEnum):
    """Publishing lifecycle states for catalog integration definitions."""

    DRAFT = "DRAFT"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"
    DEPRECATED = "DEPRECATED"
    RETIRED = "RETIRED"


class ConnectionMethod(StrEnum):
    """Authorization and connection mechanisms supported by connectors."""

    API_KEY = "API_KEY"
    OAUTH2 = "OAUTH2"
    DEVICE_CREDENTIALS = "DEVICE_CREDENTIALS"
    WEBHOOK_ONLY = "WEBHOOK_ONLY"
    CERTIFICATE = "CERTIFICATE"
    BASIC_AUTH = "BASIC_AUTH"


IntegrationConnectionMethod = ConnectionMethod  # Alias


class SyncDirection(StrEnum):
    """Synchronization data flow direction."""

    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"
    BIDIRECTIONAL = "BIDIRECTIONAL"


class ConflictResolutionPolicy(StrEnum):
    """Policy applied when external and internal records diverge."""

    CAMPUSOS_AUTHORITATIVE = "CAMPUSOS_AUTHORITATIVE"
    PROVIDER_AUTHORITATIVE = "PROVIDER_AUTHORITATIVE"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    NEWEST_WINS = "NEWEST_WINS"


ConflictResolutionStrategy = ConflictResolutionPolicy  # Alias


class TenantInstallationStatus(StrEnum):
    """State machine states for an institution's connected app instance."""

    NOT_CONNECTED = "NOT_CONNECTED"
    SETUP_PENDING = "SETUP_PENDING"
    AWAITING_AUTHORIZATION = "AWAITING_AUTHORIZATION"
    CONNECTED = "CONNECTED"
    SYNC_PAUSED = "SYNC_PAUSED"
    DEGRADED = "DEGRADED"
    REAUTH_REQUIRED = "REAUTH_REQUIRED"
    DISCONNECT_PENDING = "DISCONNECT_PENDING"
    DISCONNECTED = "DISCONNECTED"
    FAILED = "FAILED"


TenantIntegrationStatus = TenantInstallationStatus  # Alias


class SyncTriggerType(StrEnum):
    """Trigger classification for a synchronization execution run."""

    MANUAL = "MANUAL"
    SCHEDULED = "SCHEDULED"
    WEBHOOK = "WEBHOOK"
    INITIAL = "INITIAL"
    INCREMENTAL = "INCREMENTAL"
    REPLAY = "REPLAY"


class SyncRunStatus(StrEnum):
    """Execution outcome status for a synchronization run."""

    PENDING = "PENDING"
    QUEUED = "QUEUED"
    IN_PROGRESS = "IN_PROGRESS"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    COMPLETED = "COMPLETED"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


SyncExecutionStatus = SyncRunStatus  # Alias
DataConflictStatus = StrEnum("DataConflictStatus", ["PENDING", "RESOLVED", "IGNORED"])


# -----------------------------------------------------------------------------
# 2. Marketplace Catalog Entities
# -----------------------------------------------------------------------------


class MarketplaceApp(BaseModel):
    """Governed marketplace catalog integration definition."""

    __tablename__ = "marketplace_apps"
    __table_args__ = (
        Index("idx_marketplace_apps_category", "category"),
        Index("idx_marketplace_apps_status", "publication_status"),
    )

    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(48), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    provider_name: Mapped[str] = mapped_column(String(128), nullable=False)
    provider_url: Mapped[str | None] = mapped_column(String(256), nullable=True)
    provider_email: Mapped[str | None] = mapped_column(String(256), nullable=True)
    icon_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    supported_modules: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    required_scopes: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    connection_method: Mapped[str] = mapped_column(String(32), default=ConnectionMethod.API_KEY.value, nullable=False)
    config_schema: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    supported_capabilities: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    documentation_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    setup_instructions: Mapped[str] = mapped_column(Text, default="", nullable=False)
    min_platform_version: Mapped[str] = mapped_column(String(32), default="1.0.0", nullable=False)
    required_entitlements: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)

    publication_status: Mapped[str] = mapped_column(
        String(32), default=MarketplacePublicationStatus.DRAFT.value, index=True, nullable=False
    )
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deprecation_notice: Mapped[str | None] = mapped_column(Text, nullable=True)
    deprecated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    versions: Mapped[list["MarketplaceAppVersion"]] = relationship(
        "MarketplaceAppVersion", back_populates="app", cascade="all, delete-orphan"
    )
    installations: Mapped[list["TenantAppInstallation"]] = relationship(
        "TenantAppInstallation", back_populates="app"
    )


class MarketplaceAppVersion(BaseModel):
    """Specific released version of a marketplace catalog application."""

    __tablename__ = "marketplace_app_versions"
    __table_args__ = (
        UniqueConstraint("app_id", "version", name="uq_marketplace_app_version"),
        Index("idx_marketplace_app_version_app", "app_id"),
    )

    app_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("marketplace_apps.id", ondelete="CASCADE"),
        nullable=False,
    )
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    changelog: Mapped[str] = mapped_column(Text, default="", nullable=False)
    config_schema: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    supported_capabilities: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    publication_status: Mapped[str] = mapped_column(String(32), default=MarketplacePublicationStatus.APPROVED.value, nullable=False)
    released_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    is_latest: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    app: Mapped[MarketplaceApp] = relationship("MarketplaceApp", back_populates="versions")


# -----------------------------------------------------------------------------
# 3. Tenant Installations & Connections
# -----------------------------------------------------------------------------


class TenantAppInstallation(TenantScopedModel):
    """Institutional connection and operational instance of a marketplace app."""

    __tablename__ = "tenant_app_installations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "app_id", name="uq_tenant_marketplace_app"),
        Index("idx_tenant_app_installations_status", "status"),
        Index("idx_tenant_app_installations_app", "app_id"),
    )

    app_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("marketplace_apps.id", ondelete="RESTRICT"),
        nullable=False,
    )
    app_version_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("marketplace_app_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=TenantInstallationStatus.NOT_CONNECTED.value, nullable=False
    )
    connection_method: Mapped[str] = mapped_column(String(32), default=ConnectionMethod.API_KEY.value, nullable=False)
    enabled_capabilities: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    authorized_scopes: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    field_mappings: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    sync_direction: Mapped[str] = mapped_column(String(32), default=SyncDirection.BIDIRECTIONAL.value, nullable=False)
    conflict_policy: Mapped[str] = mapped_column(
        String(32), default=ConflictResolutionPolicy.CAMPUSOS_AUTHORITATIVE.value, nullable=False
    )

    # Reference to encrypted credential vault
    credential_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("integration_credentials.id", ondelete="SET NULL"),
        nullable=True,
    )
    oauth_state: Mapped[str | None] = mapped_column(String(128), nullable=True)
    oauth_state_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    webhook_secret: Mapped[str | None] = mapped_column(String(128), nullable=True)

    health_status: Mapped[str] = mapped_column(String(32), default="UNKNOWN", nullable=False)
    health_details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    last_health_check_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    consecutive_failure_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_successful_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_failure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    connected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    disconnected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    installed_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    app: Mapped[MarketplaceApp] = relationship("MarketplaceApp", back_populates="installations", lazy="joined")
    sync_runs: Mapped[list["MarketplaceSyncRun"]] = relationship(
        "MarketplaceSyncRun", back_populates="installation", cascade="all, delete-orphan"
    )
    checkpoints: Mapped[list["IntegrationSyncCheckpoint"]] = relationship(
        "IntegrationSyncCheckpoint", back_populates="installation", cascade="all, delete-orphan"
    )
    conflicts: Mapped[list["IntegrationDataConflict"]] = relationship(
        "IntegrationDataConflict", back_populates="installation", cascade="all, delete-orphan"
    )
    lifecycle_histories: Mapped[list["TenantAppInstallationLifecycleHistory"]] = relationship(
        "TenantAppInstallationLifecycleHistory", back_populates="installation", cascade="all, delete-orphan"
    )


class TenantAppInstallationLifecycleHistory(BaseModel):
    """Chronological audit trail of integration connection lifecycle transitions."""

    __tablename__ = "tenant_app_installation_lifecycles"
    __table_args__ = (
        Index("idx_tenant_app_lifecycles_inst", "installation_id"),
        Index("idx_tenant_app_lifecycles_status", "to_status"),
    )

    installation_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenant_app_installations.id", ondelete="CASCADE"),
        nullable=False,
    )
    from_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    to_status: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
    triggered_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    metadata_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    installation: Mapped[TenantAppInstallation] = relationship(
        "TenantAppInstallation", back_populates="lifecycle_histories"
    )


# -----------------------------------------------------------------------------
# 4. Synchronization Runs, Checkpoints & Conflicts
# -----------------------------------------------------------------------------


class IntegrationSyncCheckpoint(BaseModel):
    """Resumable incremental synchronization cursor and timestamp tracking."""

    __tablename__ = "integration_sync_checkpoints"
    __table_args__ = (
        UniqueConstraint(
            "installation_id", "entity_type", name="uq_installation_entity_checkpoint"
        ),
        Index("idx_sync_checkpoints_inst", "installation_id"),
    )

    installation_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenant_app_installations.id", ondelete="CASCADE"),
        nullable=False,
    )
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    cursor_position: Mapped[str | None] = mapped_column(String(256), nullable=True)
    last_sync_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    checkpoint_data: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    installation: Mapped[TenantAppInstallation] = relationship(
        "TenantAppInstallation", back_populates="checkpoints"
    )


class IntegrationDataConflict(BaseModel):
    """Discrepancy record requiring automated policy or administrator dispute resolution."""

    __tablename__ = "integration_data_conflicts"
    __table_args__ = (
        Index("idx_integration_conflicts_inst", "installation_id"),
        Index("idx_integration_conflicts_status", "status"),
        Index("idx_integration_conflicts_entity", "entity_type"),
    )

    installation_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenant_app_installations.id", ondelete="CASCADE"),
        nullable=False,
    )
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    record_identifier: Mapped[str] = mapped_column(String(128), nullable=False)

    campusos_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    provider_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    conflicting_fields: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)

    applied_resolution: Mapped[str] = mapped_column(
        String(48), default=ConflictResolutionPolicy.MANUAL_REVIEW.value, nullable=False
    )
    resolved_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    resolved_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="OPEN", index=True, nullable=False)

    installation: Mapped[TenantAppInstallation] = relationship(
        "TenantAppInstallation", back_populates="conflicts"
    )


class MarketplaceSyncRun(BaseModel):
    """Telemetry and execution metrics for a marketplace integration sync job."""

    __tablename__ = "marketplace_sync_runs"
    __table_args__ = (
        Index("idx_marketplace_sync_runs_inst", "installation_id"),
        Index("idx_marketplace_sync_runs_status", "status"),
    )

    installation_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenant_app_installations.id", ondelete="CASCADE"),
        nullable=False,
    )
    trigger_type: Mapped[str] = mapped_column(
        String(32), default=SyncTriggerType.MANUAL.value, index=True, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), default=SyncRunStatus.PENDING.value, index=True, nullable=False
    )

    records_fetched: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_skipped: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    installation: Mapped[TenantAppInstallation] = relationship(
        "TenantAppInstallation", back_populates="sync_runs"
    )
