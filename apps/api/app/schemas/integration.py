"""Pydantic request and response schemas for CampusOS Integration Platform.

Enforces:
- Input validation and bounds checking for connectors, credentials, and webhooks.
- Absolute secrecy: secrets and authorization tokens are strictly omitted from responses.
- Output models with standardized serialization.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.integration import (
    ConflictResolutionStrategy,
    ConnectorOwnership,
    ConnectorType,
    CredentialAuthType,
    SyncDirection,
    WebhookStatus,
)


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Credentials ---

class CredentialCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=128)
    auth_type: CredentialAuthType = Field(default=CredentialAuthType.API_KEY)
    credentials: dict[str, Any] = Field(..., description="Raw secrets to encrypt and vault")
    ownership_level: ConnectorOwnership = Field(default=ConnectorOwnership.TENANT)
    expires_at: datetime | None = None


class CredentialResponse(BaseSchema):
    id: UUID
    tenant_id: UUID | None
    ownership_level: str
    name: str
    auth_type: str
    masked_preview: str
    key_version: int
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime


# --- Providers ---

class ProviderResponse(BaseSchema):
    provider_key: str
    display_name: str
    connector_type: str
    supported_operations: list[str]
    authentication_type: str
    capabilities: list[str]
    version: str


# --- Connectors ---

class ConnectorCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=128)
    code: str = Field(..., min_length=2, max_length=64, pattern=r"^[A-Z0-9_-]+$")
    provider_key: str = Field(..., min_length=2, max_length=64)
    connector_type: ConnectorType = Field(default=ConnectorType.REST_API)
    description: str | None = None
    configuration: dict[str, Any] = Field(default_factory=dict)
    credential_reference: UUID | None = None
    allowed_domains: list[str] = Field(default_factory=list)
    ownership_level: ConnectorOwnership = Field(default=ConnectorOwnership.TENANT)


class ConnectorUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=128)
    description: str | None = None
    configuration: dict[str, Any] | None = None
    credential_reference: UUID | None = None
    allowed_domains: list[str] | None = None


class ConnectorResponse(BaseSchema):
    id: UUID
    tenant_id: UUID | None
    ownership_level: str
    name: str
    code: str
    provider_key: str
    connector_type: str
    status: str
    description: str | None
    configuration: dict[str, Any]
    credential_reference: UUID | None
    allowed_domains: list[str]
    created_at: datetime
    updated_at: datetime


class ConnectorTestResult(BaseModel):
    connector_id: UUID
    status: str
    latency_ms: int | None
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


# --- Health ---

class IntegrationHealthResponse(BaseSchema):
    connector_id: UUID
    status: str
    consecutive_failures: int
    last_success_at: datetime | None
    last_failure_at: datetime | None
    last_latency_ms: int | None
    error_rate: float
    circuit_state: str
    last_checked_at: datetime
    details: dict[str, Any]


# --- Webhooks ---

class WebhookSubscriptionCreate(BaseModel):
    connector_id: UUID | None = None
    name: str = Field(..., min_length=2, max_length=128)
    endpoint_url: str = Field(..., min_length=8, max_length=512)
    event_types: list[str] = Field(default_factory=lambda: ["*"])
    secret_reference: UUID | None = None
    filter_criteria: dict[str, Any] | None = None


class WebhookSubscriptionUpdate(BaseModel):
    name: str | None = None
    endpoint_url: str | None = None
    event_types: list[str] | None = None
    secret_reference: UUID | None = None
    status: WebhookStatus | None = None
    filter_criteria: dict[str, Any] | None = None


class WebhookSubscriptionResponse(BaseSchema):
    id: UUID
    tenant_id: UUID
    connector_id: UUID | None
    name: str
    endpoint_url: str
    event_types: list[str]
    status: str
    secret_reference: UUID | None
    created_at: datetime
    updated_at: datetime


class WebhookAttemptResponse(BaseSchema):
    id: UUID
    delivery_id: UUID
    attempt_number: int
    status_code: int | None
    response_body_preview: str | None
    duration_ms: int | None
    error_message: str | None
    attempted_at: datetime


class WebhookDeliveryResponse(BaseSchema):
    id: UUID
    tenant_id: UUID
    subscription_id: UUID
    event_id: str
    event_type: str
    payload: dict[str, Any]
    status: str
    attempt_count: int
    max_attempts: int
    next_attempt_at: datetime | None
    last_attempt_at: datetime | None
    response_status_code: int | None
    response_time_ms: int | None
    failure_reason: str | None
    idempotency_key: str
    created_at: datetime
    updated_at: datetime


# --- Data Mappings ---

class DataMappingCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=128)
    source_type: str = Field(..., min_length=2, max_length=64)
    target_type: str = Field(..., min_length=2, max_length=64)
    rules: list[dict[str, Any]] = Field(default_factory=list)


class DataMappingUpdate(BaseModel):
    name: str | None = None
    rules: list[dict[str, Any]] | None = None


class DataMappingResponse(BaseSchema):
    id: UUID
    tenant_id: UUID
    name: str
    source_type: str
    target_type: str
    rules: list[dict[str, Any]]
    created_at: datetime
    updated_at: datetime


# --- Synchronization ---

class SyncConfigCreate(BaseModel):
    connector_id: UUID
    name: str = Field(..., min_length=2, max_length=128)
    resource_type: str = Field(..., min_length=2, max_length=64)
    direction: SyncDirection = Field(default=SyncDirection.IMPORT)
    mapping_id: UUID | None = None
    conflict_strategy: ConflictResolutionStrategy = Field(
        default=ConflictResolutionStrategy.SOURCE_WINS
    )
    interval_minutes: int = Field(default=60, ge=5, le=1440)


class SyncConfigUpdate(BaseModel):
    name: str | None = None
    mapping_id: UUID | None = None
    conflict_strategy: ConflictResolutionStrategy | None = None
    interval_minutes: int | None = None
    status: str | None = None


class SyncConfigResponse(BaseSchema):
    id: UUID
    tenant_id: UUID
    connector_id: UUID
    name: str
    resource_type: str
    direction: str
    mapping_id: UUID | None
    conflict_strategy: str
    interval_minutes: int
    status: str
    last_synced_at: datetime | None
    created_at: datetime
    updated_at: datetime


class SyncRunResponse(BaseSchema):
    id: UUID
    tenant_id: UUID
    sync_config_id: UUID
    status: str
    records_processed: int
    records_created: int
    records_updated: int
    records_skipped: int
    records_failed: int
    error_summary: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class SyncItemResponse(BaseSchema):
    id: UUID
    sync_run_id: UUID
    external_id: str
    internal_id: UUID | None
    action: str
    status: str
    error_message: str | None


# --- Logs ---

class IntegrationLogResponse(BaseSchema):
    id: UUID
    tenant_id: UUID | None
    connector_id: UUID | None
    operation: str
    event_type: str | None
    request_id: str
    correlation_id: str
    status: str
    http_status: int | None
    duration_ms: int | None
    error_message: str | None
    details: dict[str, Any]
    created_at: datetime
