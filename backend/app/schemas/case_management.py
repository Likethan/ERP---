"""Pydantic v2 Schemas for Enterprise Workflow, Case Management & HITL Operations (Step 25)."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.case_management import (
    AssignmentStrategy,
    CasePriority,
    CaseRelationshipType,
    CaseStatus,
    CaseTimelineEventType,
    CommentVisibility,
    HumanDecision,
    SlaStatus,
    TaskStatus,
    TaskType,
)

# =============================================================================
# 1. CASE TYPES
# =============================================================================


class CaseTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID | None = None
    code: str
    name: str
    description: str | None = None
    module: str
    default_priority: CasePriority
    default_queue_id: UUID | None = None
    sla_hours: int
    requires_decision: bool
    is_active: bool
    is_system: bool
    created_at: datetime
    updated_at: datetime | None = None


class CaseTypeCreate(BaseModel):
    code: str = Field(..., max_length=64, description="Unique code for case type classification")
    name: str = Field(..., max_length=128)
    description: str | None = None
    module: str = Field("GENERAL", max_length=32)
    default_priority: CasePriority = CasePriority.NORMAL
    default_queue_id: UUID | None = None
    sla_hours: int = Field(48, ge=1, le=8760)
    requires_decision: bool = True
    is_active: bool = True


class CaseTypeUpdate(BaseModel):
    name: str | None = Field(None, max_length=128)
    description: str | None = None
    module: str | None = Field(None, max_length=32)
    default_priority: CasePriority | None = None
    default_queue_id: UUID | None = None
    sla_hours: int | None = Field(None, ge=1, le=8760)
    requires_decision: bool | None = None
    is_active: bool | None = None


# =============================================================================
# 2. WORK QUEUES & MEMBERS
# =============================================================================


class QueueMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    queue_id: UUID
    user_id: UUID
    is_supervisor: bool
    is_active: bool
    max_active_tasks: int
    created_at: datetime
    updated_at: datetime | None = None


class QueueMemberCreate(BaseModel):
    user_id: UUID
    is_supervisor: bool = False
    is_active: bool = True
    max_active_tasks: int = Field(10, ge=1, le=100)


class WorkQueueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    key: str
    name: str
    description: str | None = None
    module: str
    is_active: bool
    assignment_policy: AssignmentStrategy
    capacity: int | None = None
    supervisor_id: UUID | None = None
    sla_hours: int | None = None
    created_at: datetime
    updated_at: datetime | None = None
    members: list[QueueMemberResponse] = []


class WorkQueueCreate(BaseModel):
    key: str = Field(..., max_length=64, description="Unique alphanumeric identifier for queue")
    name: str = Field(..., max_length=128)
    description: str | None = None
    module: str = Field("GENERAL", max_length=32)
    is_active: bool = True
    assignment_policy: AssignmentStrategy = AssignmentStrategy.MANUAL
    capacity: int | None = Field(100, ge=1)
    supervisor_id: UUID | None = None
    sla_hours: int | None = Field(None, ge=1)


class WorkQueueUpdate(BaseModel):
    name: str | None = Field(None, max_length=128)
    description: str | None = None
    module: str | None = Field(None, max_length=32)
    is_active: bool | None = None
    assignment_policy: AssignmentStrategy | None = None
    capacity: int | None = None
    supervisor_id: UUID | None = None
    sla_hours: int | None = None


# =============================================================================
# 3. COMMENTS, ATTACHMENTS & TIMELINE
# =============================================================================


class CaseCommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    case_id: UUID
    task_id: UUID | None = None
    author_id: UUID
    content: str
    visibility: CommentVisibility
    metadata_json: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime | None = None


class CaseCommentCreate(BaseModel):
    task_id: UUID | None = None
    content: str = Field(..., min_length=1, max_length=10000)
    visibility: CommentVisibility = CommentVisibility.INTERNAL
    metadata_json: dict[str, Any] | None = None


class CaseAttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    case_id: UUID
    task_id: UUID | None = None
    document_id: UUID
    attachment_type: str
    title: str
    visibility: CommentVisibility
    uploaded_by_id: UUID
    created_at: datetime


class CaseAttachmentCreate(BaseModel):
    task_id: UUID | None = None
    document_id: UUID
    attachment_type: str = Field("SUPPORTING_EVIDENCE", max_length=64)
    title: str = Field(..., max_length=255)
    visibility: CommentVisibility = CommentVisibility.INTERNAL


class CaseTimelineEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    case_id: UUID
    task_id: UUID | None = None
    event_type: CaseTimelineEventType | str
    actor_id: UUID | None = None
    title: str
    details_json: dict[str, Any] = {}
    occurred_at: datetime


# =============================================================================
# 4. RELATIONSHIPS
# =============================================================================


class CaseRelationshipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    source_case_id: UUID
    target_case_id: UUID
    relationship_type: CaseRelationshipType
    notes: str | None = None
    created_by_id: UUID | None = None
    created_at: datetime


class CaseRelationshipCreate(BaseModel):
    target_case_id: UUID
    relationship_type: CaseRelationshipType = CaseRelationshipType.RELATED_TO
    notes: str | None = None


# =============================================================================
# 5. DECISIONS & DELEGATIONS
# =============================================================================


class TaskDecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    task_id: UUID
    case_id: UUID
    actor_id: UUID
    decision: HumanDecision
    reason: str
    notes: str | None = None
    evidence_reference: str | None = None
    resulting_transition: str | None = None
    metadata_json: dict[str, Any] | None = None
    created_at: datetime


class TaskDecisionCreate(BaseModel):
    decision: HumanDecision
    reason: str = Field(
        ..., min_length=2, max_length=2000, description="Mandatory decision justification"
    )
    notes: str | None = None
    evidence_reference: str | None = None
    resulting_transition: str | None = None
    metadata_json: dict[str, Any] | None = None


class TaskDelegationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    delegator_user_id: UUID
    delegatee_user_id: UUID
    scope_module: str | None = None
    valid_from: datetime
    valid_until: datetime
    reason: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None


class TaskDelegationCreate(BaseModel):
    delegatee_user_id: UUID
    scope_module: str | None = Field(None, max_length=32)
    valid_from: datetime
    valid_until: datetime
    reason: str | None = Field(None, max_length=1000)


# =============================================================================
# 6. HUMAN TASKS
# =============================================================================


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    case_id: UUID
    workflow_execution_id: UUID | None = None
    step_key: str | None = None
    title: str
    description: str | None = None
    task_type: TaskType
    status: TaskStatus
    priority: CasePriority
    assigned_user_id: UUID | None = None
    assigned_role: str | None = None
    assigned_queue_id: UUID | None = None
    due_at: datetime | None = None
    claimed_at: datetime | None = None
    completed_at: datetime | None = None
    completed_by_id: UUID | None = None
    sla_breached: bool = False
    input_context_json: dict[str, Any] | None = None
    output_result_json: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime | None = None


class TaskDetailResponse(TaskResponse):
    decisions: list[TaskDecisionResponse] = []
    comments: list[CaseCommentResponse] = []


class TaskCreate(BaseModel):
    case_id: UUID
    workflow_execution_id: UUID | None = None
    step_key: str | None = None
    title: str = Field(..., max_length=255)
    description: str | None = None
    task_type: TaskType = TaskType.REVIEW
    priority: CasePriority = CasePriority.NORMAL
    assigned_user_id: UUID | None = None
    assigned_role: str | None = None
    assigned_queue_id: UUID | None = None
    due_at: datetime | None = None
    input_context_json: dict[str, Any] | None = None


class TaskClaimResponse(BaseModel):
    task: TaskResponse
    claimed_by_id: UUID
    claimed_at: datetime


class TaskReleaseRequest(BaseModel):
    reason: str | None = Field(None, max_length=500)


class TaskReassignRequest(BaseModel):
    new_user_id: UUID | None = None
    new_queue_id: UUID | None = None
    reason: str = Field(..., min_length=2, max_length=500)


class TaskCompleteRequest(BaseModel):
    decision: HumanDecision
    reason: str = Field(..., min_length=2, max_length=2000)
    notes: str | None = None
    evidence_reference: str | None = None
    resulting_transition: str | None = None
    output_result_json: dict[str, Any] | None = None


# =============================================================================
# 7. CASES
# =============================================================================


class CaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    case_number: str
    case_type_id: UUID | None = None
    case_type_code: str
    title: str
    description: str | None = None
    priority: CasePriority
    status: CaseStatus
    owner_id: UUID | None = None
    assigned_queue_id: UUID | None = None
    workflow_execution_id: UUID | None = None
    subject_entity_type: str | None = None
    subject_entity_id: UUID | None = None
    created_by_id: UUID | None = None
    due_at: datetime | None = None
    resolved_at: datetime | None = None
    closed_at: datetime | None = None
    resolution_reason: str | None = None
    resolution_notes: str | None = None
    reopen_count: int = 0
    sla_breached: bool = False
    metadata_json: dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime | None = None


class CaseDetailResponse(CaseResponse):
    tasks: list[TaskResponse] = []
    comments: list[CaseCommentResponse] = []
    timeline_events: list[CaseTimelineEventResponse] = []
    attachments: list[CaseAttachmentResponse] = []


class CaseCreate(BaseModel):
    case_type_code: str = Field(..., max_length=64)
    title: str = Field(..., min_length=2, max_length=255)
    description: str | None = None
    priority: CasePriority = CasePriority.NORMAL
    owner_id: UUID | None = None
    assigned_queue_id: UUID | None = None
    subject_entity_type: str | None = Field(None, max_length=64)
    subject_entity_id: UUID | None = None
    due_at: datetime | None = None
    metadata_json: dict[str, Any] = {}


class CaseUpdate(BaseModel):
    title: str | None = Field(None, min_length=2, max_length=255)
    description: str | None = None
    priority: CasePriority | None = None
    owner_id: UUID | None = None
    assigned_queue_id: UUID | None = None
    due_at: datetime | None = None
    metadata_json: dict[str, Any] | None = None


class CaseResolveRequest(BaseModel):
    resolution_reason: str = Field(..., min_length=2, max_length=128)
    resolution_notes: str = Field(..., min_length=2, max_length=5000)


class CaseCloseRequest(BaseModel):
    closure_notes: str | None = Field(None, max_length=2000)


class CaseReopenRequest(BaseModel):
    reopen_reason: str = Field(..., min_length=2, max_length=1000)


# =============================================================================
# 8. SLA POLICIES & INSTANCES
# =============================================================================


class SlaPolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    module: str
    case_type_code: str | None = None
    priority: CasePriority
    target_duration_minutes: int
    warning_threshold_percentage: int
    business_hours_only: bool
    business_start_hour: int
    business_end_hour: int
    escalation_queue_id: UUID | None = None
    escalation_role: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None


class SlaPolicyCreate(BaseModel):
    name: str = Field(..., max_length=128)
    module: str = Field("GENERAL", max_length=32)
    case_type_code: str | None = Field(None, max_length=64)
    priority: CasePriority = CasePriority.NORMAL
    target_duration_minutes: int = Field(2880, ge=1, le=525600)
    warning_threshold_percentage: int = Field(75, ge=1, le=99)
    business_hours_only: bool = True
    business_start_hour: int = Field(9, ge=0, le=23)
    business_end_hour: int = Field(18, ge=0, le=23)
    escalation_queue_id: UUID | None = None
    escalation_role: str | None = None
    is_active: bool = True


class SlaPolicyUpdate(BaseModel):
    name: str | None = Field(None, max_length=128)
    target_duration_minutes: int | None = Field(None, ge=1, le=525600)
    warning_threshold_percentage: int | None = Field(None, ge=1, le=99)
    business_hours_only: bool | None = None
    business_start_hour: int | None = None
    business_end_hour: int | None = None
    escalation_queue_id: UUID | None = None
    escalation_role: str | None = None
    is_active: bool | None = None


class SlaInstanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    sla_policy_id: UUID | None = None
    case_id: UUID | None = None
    task_id: UUID | None = None
    started_at: datetime
    due_at: datetime
    warning_at: datetime | None = None
    completed_at: datetime | None = None
    elapsed_minutes: int
    status: SlaStatus
    breached: bool
    escalated: bool
    escalated_at: datetime | None = None


# =============================================================================
# 9. WORKFLOW TRANSITIONS & HITL BRIDGE
# =============================================================================


class WorkflowInstanceTransitionRequest(BaseModel):
    action: str = Field(
        ..., max_length=64, description="Action or decision triggering the transition"
    )
    target_step_key: str | None = Field(None, max_length=64)
    reason: str = Field(..., min_length=2, max_length=1000)
    evidence_reference: str | None = None
    task_id: UUID | None = None
    context_updates: dict[str, Any] = {}


class WorkflowInstanceTransitionResponse(BaseModel):
    workflow_instance_id: UUID
    previous_step: str | None = None
    current_step: str
    status: str
    transitioned_at: datetime
    decision_recorded: str | None = None


# =============================================================================
# 10. CASE ANALYTICS
# =============================================================================


class CaseAnalyticsMetrics(BaseModel):
    tenant_id: UUID
    open_cases: int
    in_progress_cases: int
    waiting_cases: int
    escalated_cases: int
    resolved_cases: int
    closed_cases: int
    total_cases: int
    avg_resolution_time_hours: float
    sla_compliance_rate: float
    sla_breaches_total: int
    cases_by_priority: dict[str, int]
    cases_by_status: dict[str, int]
    cases_by_module: dict[str, int]
    cases_by_queue: dict[str, int]
    tasks_by_status: dict[str, int]
    escalation_rate: float
    reassignment_count: int
    total_human_tasks: int
