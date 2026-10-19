"""Pydantic Request and Response Schemas for Security Operations (Step 33)."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SecurityDetectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID | None = None
    incident_id: UUID | None = None
    rule_id: str
    rule_version: str
    event_type: str
    severity: str
    confidence: str
    detection_source: str
    actor_type: str
    actor_id: str | None = None
    target_resource_type: str | None = None
    target_resource_id: str | None = None
    ip_address: str
    request_id: str
    audit_log_id: UUID | None = None
    occurrence_count: int
    first_seen_at: datetime
    last_seen_at: datetime
    details_json: dict[str, Any] | None = None
    status: str
    suppression_reason: str | None = None
    created_at: datetime


class SecurityDetectionListResponse(BaseModel):
    items: list[SecurityDetectionResponse]
    total: int


class SecurityIncidentNoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    incident_id: UUID
    author_user_id: UUID | None = None
    note_type: str
    content: str
    evidence_references: list[dict[str, Any]] | None = None
    created_at: datetime


class SecurityIncidentNoteCreateRequest(BaseModel):
    content: str
    note_type: str = "INVESTIGATION"
    evidence_references: list[dict[str, Any]] | None = None


class SecurityRemediationTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    incident_id: UUID
    tenant_id: UUID | None = None
    title: str
    description: str | None = None
    assigned_to_user_id: UUID | None = None
    status: str
    due_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime


class SecurityRemediationTaskCreateRequest(BaseModel):
    title: str
    description: str | None = None
    assigned_to_user_id: UUID | None = None
    due_at: datetime | None = None


class SecurityRemediationTaskStatusUpdateRequest(BaseModel):
    status: str


class SecurityResponseActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID | None = None
    incident_id: UUID | None = None
    action_type: str
    target_type: str
    target_identifier: str
    risk_level: str
    requires_approval: bool
    status: str
    idempotency_key: str
    proposed_by_user_id: UUID | None = None
    approved_by_user_id: UUID | None = None
    executed_by_user_id: UUID | None = None
    execution_payload: dict[str, Any] | None = None
    execution_result: dict[str, Any] | None = None
    error_message: str | None = None
    expires_at: datetime | None = None
    executed_at: datetime | None = None
    created_at: datetime


class SecurityResponseActionProposeRequest(BaseModel):
    incident_id: UUID
    action_type: str  # RATE_LIMIT_IP, REVOKE_SESSION, REVOKE_API_KEY, LOCK_ACCOUNT, etc.
    target_type: str  # IP, SESSION, API_KEY, USER, TASK, NOTIFICATION
    target_identifier: str
    risk_level: str = "MEDIUM"
    requires_approval: bool = False
    payload: dict[str, Any] | None = None


class SecurityResponseActionRejectRequest(BaseModel):
    reason: str | None = None


class SecurityIncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID | None = None
    incident_number: str
    title: str
    description: str
    severity: str
    confidence: str
    status: str
    assigned_to_user_id: UUID | None = None
    created_by_user_id: UUID | None = None
    resolved_by_user_id: UUID | None = None
    triaged_at: datetime | None = None
    contained_at: datetime | None = None
    resolved_at: datetime | None = None
    closed_at: datetime | None = None
    resolution_reason: str | None = None
    closure_summary: str | None = None
    metadata_json: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

    detections: list[SecurityDetectionResponse] = Field(default_factory=list)
    notes: list[SecurityIncidentNoteResponse] = Field(default_factory=list)
    actions: list[SecurityResponseActionResponse] = Field(default_factory=list)
    remediation_tasks: list[SecurityRemediationTaskResponse] = Field(default_factory=list)


class SecurityIncidentListResponse(BaseModel):
    items: list[SecurityIncidentResponse]
    total: int


class SecurityIncidentStatusUpdateRequest(BaseModel):
    status: str
    reason: str | None = None
    closure_summary: str | None = None


class SecurityIncidentAssignRequest(BaseModel):
    assigned_to_user_id: UUID | None = None


class SecurityDetectionRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    rule_id: str
    version: str
    name: str
    description: str
    category: str
    severity: str
    is_enabled: bool
    evaluation_window_seconds: int
    threshold: int
    recommended_action: str | None = None
    config_parameters: dict[str, Any] | None = None
    exclusions_json: list[dict[str, Any]] | None = None


class SecurityDetectionRuleUpdateRequest(BaseModel):
    is_enabled: bool | None = None
    threshold: int | None = None
    evaluation_window_seconds: int | None = None
    severity: str | None = None


class SocOverviewResponse(BaseModel):
    critical_incidents: int
    high_incidents: int
    medium_incidents: int
    low_incidents: int
    recent_detections_24h: int
    pending_action_approvals: int
    oldest_unresolved_hours: float
    timestamp: str
