"""Pydantic schemas for Step 39: Enterprise Marketplace & App Integrations."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.marketplace import (
    ConflictResolutionPolicy,
    ConnectionMethod,
    MarketplaceAppCategory,
    MarketplacePublicationStatus,
    SyncDirection,
    SyncRunStatus,
    SyncTriggerType,
    TenantInstallationStatus,
)

# ==========================================
# Marketplace App Catalog Schemas
# ==========================================

class MarketplaceAppCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=2, max_length=64)
    name: str = Field(..., min_length=2, max_length=128)
    category: MarketplaceAppCategory
    description: str = Field(default="", max_length=4000)
    provider_name: str = Field(..., min_length=2, max_length=128)
    provider_url: str | None = Field(default=None, max_length=256)
    provider_email: str | None = Field(default=None, max_length=256)
    icon_url: str | None = Field(default=None, max_length=512)
    supported_modules: list[str] = Field(default_factory=list)
    required_scopes: list[str] = Field(default_factory=list)
    connection_method: ConnectionMethod = ConnectionMethod.API_KEY
    config_schema: dict[str, Any] = Field(default_factory=dict)
    supported_capabilities: list[str] = Field(default_factory=list)
    documentation_url: str | None = Field(default=None, max_length=512)
    setup_instructions: str = Field(default="", max_length=4000)
    min_platform_version: str = Field(default="1.0.0", max_length=32)
    required_entitlements: list[str] = Field(default_factory=list)
    is_featured: bool = False


class MarketplaceAppUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=2, max_length=128)
    category: MarketplaceAppCategory | None = None
    description: str | None = Field(default=None, max_length=4000)
    provider_name: str | None = Field(default=None, min_length=2, max_length=128)
    provider_url: str | None = Field(default=None, max_length=256)
    provider_email: str | None = Field(default=None, max_length=256)
    icon_url: str | None = Field(default=None, max_length=512)
    supported_modules: list[str] | None = None
    required_scopes: list[str] | None = None
    connection_method: ConnectionMethod | None = None
    config_schema: dict[str, Any] | None = None
    supported_capabilities: list[str] | None = None
    documentation_url: str | None = Field(default=None, max_length=512)
    setup_instructions: str | None = Field(default=None, max_length=4000)
    min_platform_version: str | None = Field(default=None, max_length=32)
    required_entitlements: list[str] | None = None
    is_featured: bool | None = None
    publication_status: MarketplacePublicationStatus | None = None
    deprecation_notice: str | None = Field(default=None, max_length=1000)


class MarketplaceAppResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    category: MarketplaceAppCategory
    description: str
    provider_name: str
    provider_url: str | None = None
    provider_email: str | None = None
    icon_url: str | None = None
    supported_modules: list[str]
    required_scopes: list[str]
    connection_method: ConnectionMethod
    config_schema: dict[str, Any]
    supported_capabilities: list[str]
    documentation_url: str | None = None
    setup_instructions: str
    min_platform_version: str
    required_entitlements: list[str]
    publication_status: MarketplacePublicationStatus
    is_verified: bool
    is_featured: bool
    deprecation_notice: str | None = None
    deprecated_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class MarketplaceAppVersionCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str = Field(..., min_length=1, max_length=32)
    changelog: str = Field(default="", max_length=4000)
    config_schema: dict[str, Any] = Field(default_factory=dict)
    supported_capabilities: list[str] = Field(default_factory=list)
    publication_status: MarketplacePublicationStatus = MarketplacePublicationStatus.APPROVED
    is_latest: bool = True


class MarketplaceAppVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    app_id: UUID
    version: str
    changelog: str
    config_schema: dict[str, Any]
    supported_capabilities: list[str]
    publication_status: MarketplacePublicationStatus
    released_at: datetime
    is_latest: bool
    created_at: datetime
    updated_at: datetime


# ==========================================
# Tenant Connection & Lifecycle Schemas
# ==========================================

class TenantAppInstallationCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    app_id: UUID
    display_name: str | None = Field(default=None, max_length=128)
    connection_method: ConnectionMethod | None = None
    configuration: dict[str, Any] = Field(default_factory=dict)
    field_mappings: dict[str, Any] = Field(default_factory=dict)
    sync_direction: SyncDirection = SyncDirection.BIDIRECTIONAL
    conflict_policy: ConflictResolutionPolicy = ConflictResolutionPolicy.CAMPUSOS_AUTHORITATIVE
    credentials: dict[str, Any] | None = None  # Securely vaulted, never logged or stored plaintext


class TenantAppInstallationUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str | None = Field(default=None, max_length=128)
    configuration: dict[str, Any] | None = None
    field_mappings: dict[str, Any] | None = None
    sync_direction: SyncDirection | None = None
    conflict_policy: ConflictResolutionPolicy | None = None
    enabled_capabilities: list[str] | None = None
    credentials: dict[str, Any] | None = None


class TenantAppInstallationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    app_id: UUID
    app_version_id: UUID | None = None
    app_code: str | None = None
    app_name: str | None = None
    app_category: str | None = None
    display_name: str
    status: TenantInstallationStatus
    connection_method: ConnectionMethod
    enabled_capabilities: list[str]
    authorized_scopes: list[str]
    configuration: dict[str, Any]
    field_mappings: dict[str, Any]
    sync_direction: SyncDirection
    conflict_policy: ConflictResolutionPolicy
    credential_id: UUID | None = None
    has_credentials: bool = False
    health_status: str
    health_details: dict[str, Any]
    last_health_check_at: datetime | None = None
    consecutive_failure_count: int
    last_successful_sync_at: datetime | None = None
    last_failure_at: datetime | None = None
    last_error_summary: str | None = None
    connected_at: datetime | None = None
    disconnected_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class TenantAppInstallationLifecycleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    installation_id: UUID
    from_status: str | None = None
    to_status: str
    reason: str
    triggered_by_user_id: UUID | None = None
    metadata_snapshot: dict[str, Any]
    created_at: datetime


# ==========================================
# Synchronization & Checkpoint Schemas
# ==========================================

class SyncTriggerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trigger_type: SyncTriggerType = SyncTriggerType.MANUAL
    entity_types: list[str] | None = None
    force_full_sync: bool = False


class MarketplaceSyncRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    installation_id: UUID
    trigger_type: SyncTriggerType
    status: SyncRunStatus
    records_fetched: int
    records_processed: int
    records_created: int
    records_updated: int
    records_skipped: int
    records_failed: int
    error_summary: str | None = None
    execution_metadata: dict[str, Any]
    started_at: datetime
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class IntegrationSyncCheckpointResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    installation_id: UUID
    entity_type: str
    cursor_position: str | None = None
    last_sync_timestamp: datetime | None = None
    checkpoint_data: dict[str, Any]
    created_at: datetime
    updated_at: datetime


# ==========================================
# Data Conflict Governance Schemas
# ==========================================

class IntegrationDataConflictResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    installation_id: UUID
    entity_type: str
    record_identifier: str
    campusos_payload: dict[str, Any]
    provider_payload: dict[str, Any]
    conflicting_fields: list[str]
    applied_resolution: str
    resolved_payload: dict[str, Any]
    resolved_by_user_id: UUID | None = None
    resolved_at: datetime | None = None
    resolution_notes: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime


class ConflictResolutionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resolution_strategy: ConflictResolutionPolicy = ConflictResolutionPolicy.MANUAL_REVIEW
    resolved_payload: dict[str, Any] | None = None
    notes: str | None = Field(default=None, max_length=1000)


# ==========================================
# Connectivity Probe & OAuth Schemas
# ==========================================

class TestConnectivityResponse(BaseModel):
    success: bool
    status: str
    latency_ms: float
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class OAuthAuthorizeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    redirect_uri: str | None = None
    scopes: list[str] | None = None


class OAuthAuthorizeResponse(BaseModel):
    authorization_url: str
    state: str
    expires_at: datetime


class OAuthCallbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    state: str


# ==========================================
# Webhook Ingestion Schemas
# ==========================================

class WebhookIngestResult(BaseModel):
    success: bool
    message: str
    event_id: str | None = None
    records_affected: int = 0
