"""Pydantic v2 schemas for Enterprise Domain Events and Transactional Outbox (Step 27)."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OutboxEventSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    schema_version: str
    event_type: str
    aggregate_type: str
    aggregate_id: UUID
    status: str
    attempt_count: int
    max_attempts: int
    available_at: datetime
    processed_at: datetime | None = None
    correlation_id: str
    causation_id: str | None = None
    producer: str
    created_at: datetime


class OutboxEventDetailResponse(OutboxEventSummaryResponse):
    payload: dict[str, Any]
    actor_id: UUID | None = None
    actor_context: dict[str, Any] | None = None
    metadata_json: dict[str, Any] | None = None
    last_error: str | None = None


class OutboxEventListResponse(BaseModel):
    items: list[OutboxEventSummaryResponse]
    total: int
    limit: int
    offset: int


class EventRetryResponse(BaseModel):
    success: bool
    event_id: UUID
    status: str
    message: str


class EventReplayRequest(BaseModel):
    consumer_names: list[str] | None = Field(
        default=None, description="Optional list of specific consumers to reset"
    )
    reason: str = Field(default="Manual replay requested", max_length=255)


class EventReplayResponse(BaseModel):
    success: bool
    event_id: UUID
    status: str
    target_consumers: list[str]
    message: str


class EventDeadLetterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    event_id: UUID
    event_type: str
    consumer_name: str | None = None
    failure_reason: str
    error_details_json: dict[str, Any]
    attempt_count: int
    first_failed_at: datetime
    last_failed_at: datetime
    is_resolved: bool
    resolved_at: datetime | None = None
    resolved_by_id: UUID | None = None
    resolution_notes: str | None = None


class EventDeadLetterListResponse(BaseModel):
    items: list[EventDeadLetterResponse]
    total: int
    limit: int
    offset: int


class EventDeadLetterResolveRequest(BaseModel):
    resolution_notes: str = Field(..., min_length=3, max_length=1000)


class EventConsumerCheckpointSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    consumer_name: str
    status: str
    count: int


class EventConsumerInfoResponse(BaseModel):
    consumer_name: str
    supported_event_types: list[str]
    total_completed: int
    total_failed: int
    total_pending: int
    avg_latency_ms: float


class EventMetricsResponse(BaseModel):
    tenant_id: UUID
    pending_count: int
    processing_count: int
    processed_count: int
    failed_count: int
    dead_letter_count: int
    oldest_pending_age_seconds: float
    average_consumer_latency_ms: float
