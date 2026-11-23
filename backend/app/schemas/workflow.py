"""CampusOS Enterprise Workflow Engine Pydantic Schemas.

Defines client and internal DTOs for:
- Workflows (CRUD, versions, lifecycle)
- Triggers (Schedule, Event, Manual)
- Steps and safe condition ASTs
- Executions and step tracking
- Dead-letter and operational health metrics
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WorkflowTriggerSchema(BaseModel):
    trigger_type: str = Field(..., description="SCHEDULE, EVENT, or MANUAL")
    event_type: str | None = Field(None, description="Registered domain event type if trigger_type=EVENT")
    cron_expression: str | None = Field(None, description="Cron expression if trigger_type=SCHEDULE")
    interval_seconds: int | None = Field(None, description="Interval in seconds for periodic execution")
    schedule_time: str | None = Field(None, description="Local time (HH:MM) to execute in tenant timezone")
    days_of_week: list[int] | None = Field(None, description="0=Monday, 6=Sunday")
    config: dict[str, Any] = Field(default_factory=dict)


class WorkflowStepSchema(BaseModel):
    id: str = Field(..., description="Unique step identifier within the workflow definition")
    name: str = Field(..., description="Human-readable step name")
    step_type: str = Field(..., description="CONDITION, ACTION, NOTIFICATION, or WAIT")
    condition: dict[str, Any] | None = Field(None, description="Condition tree without eval")
    action_type: str | None = Field(None, description="Registered action type from ACTION_REGISTRY")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Parameters matching action definition")
    next_step_id: str | None = Field(None, description="ID of step to execute next")
    on_failure_step_id: str | None = Field(None, description="Fallback step ID on error")


class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: str | None = Field(None, max_length=2000)
    domain: str = Field(default="GENERAL", max_length=64)
    trigger: WorkflowTriggerSchema
    steps: list[WorkflowStepSchema] = Field(..., min_length=1)


class WorkflowUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=255)
    description: str | None = Field(None, max_length=2000)
    domain: str | None = Field(None, max_length=64)
    trigger: WorkflowTriggerSchema | None = None
    steps: list[WorkflowStepSchema] | None = None
    change_summary: str | None = Field(None, max_length=500)


class WorkflowVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workflow_id: UUID
    version: int
    is_active: bool
    change_summary: str | None
    trigger_definition: dict[str, Any]
    steps_definition: list[dict[str, Any]]
    created_at: datetime


class WorkflowRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    description: str | None
    domain: str
    status: str
    is_system: bool
    active_version: int
    current_version_id: UUID | None
    created_by: UUID | None
    updated_by: UUID | None
    created_at: datetime
    updated_at: datetime
    versions: list[WorkflowVersionRead] | None = None


class WorkflowExecutionStepRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    step_id: str
    step_type: str
    action_type: str | None
    status: str
    started_at: datetime
    completed_at: datetime | None
    attempt_count: int
    input_data: dict[str, Any] | None
    output_data: dict[str, Any] | None
    error_message: str | None


class WorkflowExecutionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    workflow_id: UUID
    workflow_version_id: UUID
    trigger_type: str
    trigger_reference: str | None
    idempotency_key: str | None
    status: str
    started_at: datetime
    completed_at: datetime | None
    attempt_count: int
    max_retries: int
    correlation_id: str | None
    error_code: str | None
    error_message: str | None
    steps: list[WorkflowExecutionStepRead] | None = None


class WorkflowDeadLetterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    execution_id: UUID
    workflow_id: UUID
    failure_reason: str
    last_error: str | None
    attempt_count: int
    first_failure_at: datetime
    last_failure_at: datetime
    created_at: datetime


class WorkflowOperationalMetrics(BaseModel):
    active_workflows: int = 0
    paused_workflows: int = 0
    draft_workflows: int = 0
    archived_workflows: int = 0
    executions_today: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    dead_letter_count: int = 0
    queue_depth: int = 0


class WorkflowManualExecutionRequest(BaseModel):
    correlation_id: str | None = None
    input_context: dict[str, Any] = Field(default_factory=dict)
    reason: str | None = Field(None, max_length=500)


class EventRegistryItem(BaseModel):
    event_type: str
    aggregate_type: str
    description: str
    allowed_payload_keys: list[str]


class ActionRegistryItem(BaseModel):
    action_type: str
    description: str
    required_permission: str
    is_system_only: bool
    allowed_params: list[str]
