"""Pydantic DTO Schemas for Step 37: Enterprise Product Adoption, Training, In-App Guidance & Change Management.

Enforces zero-trust request validation, tenant boundary protection, strict role targeting,
and server-validated adoption milestone tracking.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# -----------------------------------------------------------------------------
# 1. Adoption Journey & Step Schemas
# -----------------------------------------------------------------------------


class JourneyStepCreateRequest(BaseModel):
    """Payload to define an ordered step in an onboarding journey."""

    model_config = ConfigDict(extra="forbid")

    step_order: int = Field(..., ge=1, description="Sequential position in journey")
    step_key: str = Field(..., min_length=2, max_length=64, description="Unique key within journey")
    title: str = Field(..., min_length=2, max_length=255)
    description: str | None = None
    completion_criteria: str = Field(
        default="CONFIRM_CHECKLIST",
        description="StepCompletionCriteria: ACTION_COMPLETED, VIEW_RESOURCE, CONFIRM_CHECKLIST, TRAINING_COMPLETED",
    )
    route_path: str | None = Field(default=None, max_length=255)
    contextual_resource_url: str | None = Field(default=None, max_length=512)
    estimated_duration_minutes: int = Field(default=5, ge=1, le=120)
    is_required: bool = True
    action_event_key: str | None = Field(default=None, max_length=64)


class JourneyStepResponse(BaseModel):
    """Response DTO for an onboarding journey step."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    journey_id: UUID
    step_order: int
    step_key: str
    title: str
    description: str | None
    completion_criteria: str
    route_path: str | None
    contextual_resource_url: str | None
    estimated_duration_minutes: int
    is_required: bool
    action_event_key: str | None
    created_at: datetime


class AdoptionJourneyCreateRequest(BaseModel):
    """Payload to create an onboarding journey definition."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=2, max_length=64, description="Unique code for journey")
    title: str = Field(..., min_length=3, max_length=255)
    description: str | None = None
    target_roles: list[str] = Field(default_factory=list, description="Roles eligible, e.g. ['STUDENT']")
    target_department_id: UUID | None = None
    product_version: str = Field(default="v1.0", max_length=32)
    is_mandatory: bool = True
    steps: list[JourneyStepCreateRequest] = Field(default_factory=list)


class AdoptionJourneyUpdateRequest(BaseModel):
    """Payload to update an existing draft or active journey definition."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = None
    target_roles: list[str] | None = None
    target_department_id: UUID | None = None
    is_mandatory: bool | None = None


class AdoptionJourneyResponse(BaseModel):
    """Full onboarding journey response with steps."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID | None
    code: str
    title: str
    description: str | None
    target_roles: list[str]
    target_department_id: UUID | None
    product_version: str
    status: str
    version: int
    is_mandatory: bool
    created_by_id: UUID | None
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime
    steps: list[JourneyStepResponse] = Field(default_factory=list)


class UserJourneyStepCompleteRequest(BaseModel):
    """Payload to record progress or completion of a journey step."""

    model_config = ConfigDict(extra="forbid")

    step_key: str = Field(..., min_length=1, max_length=64)
    notes: str | None = Field(default=None, max_length=255)
    metadata: dict[str, Any] = Field(default_factory=dict)


class UserJourneyProgressResponse(BaseModel):
    """User onboarding journey execution state."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    user_id: UUID
    journey_id: UUID
    journey_version: int
    status: str
    current_step_order: int
    completed_step_keys: list[str]
    step_progress_json: dict[str, Any]
    progress_pct: float
    started_at: datetime
    last_active_at: datetime
    completed_at: datetime | None


# -----------------------------------------------------------------------------
# 2. Training Programs & Assignments Schemas
# -----------------------------------------------------------------------------


class TrainingModuleCreateRequest(BaseModel):
    """Payload to define an individual training module or instructional unit."""

    model_config = ConfigDict(extra="forbid")

    module_order: int = Field(..., ge=1)
    module_key: str = Field(..., min_length=2, max_length=64)
    title: str = Field(..., min_length=2, max_length=255)
    content_type: str = Field(
        default="TEXT_INSTRUCTION",
        description="TrainingModuleContentType: TEXT_INSTRUCTION, EXTERNAL_LINK, DOCUMENT_REF, VIDEO_LINK",
    )
    content_body: str | None = None
    external_url: str | None = Field(default=None, max_length=512)
    document_id: UUID | None = None
    estimated_duration_minutes: int = Field(default=10, ge=1, le=240)
    is_required: bool = True


class TrainingModuleResponse(BaseModel):
    """Response DTO for a training module."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    program_id: UUID
    module_order: int
    module_key: str
    title: str
    content_type: str
    content_body: str | None
    external_url: str | None
    document_id: UUID | None
    estimated_duration_minutes: int
    is_required: bool
    created_at: datetime


class TrainingProgramCreateRequest(BaseModel):
    """Payload to create a modular training program."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=2, max_length=64)
    title: str = Field(..., min_length=3, max_length=255)
    description: str | None = None
    category: str = Field(default="ONBOARDING", max_length=64)
    target_roles: list[str] = Field(default_factory=list)
    target_department_id: UUID | None = None
    estimated_duration_minutes: int = Field(default=30, ge=1)
    is_mandatory: bool = False
    completion_rule: str = Field(default="ALL_MODULES", max_length=32)
    modules: list[TrainingModuleCreateRequest] = Field(default_factory=list)


class TrainingProgramUpdateRequest(BaseModel):
    """Payload to update an existing training program."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = None
    category: str | None = None
    target_roles: list[str] | None = None
    target_department_id: UUID | None = None
    estimated_duration_minutes: int | None = None
    is_mandatory: bool | None = None
    completion_rule: str | None = None


class TrainingProgramResponse(BaseModel):
    """Training program response with associated modules."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID | None
    code: str
    title: str
    description: str | None
    category: str
    target_roles: list[str]
    target_department_id: UUID | None
    version: int
    status: str
    estimated_duration_minutes: int
    is_mandatory: bool
    completion_rule: str
    created_by_id: UUID | None
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime
    modules: list[TrainingModuleResponse] = Field(default_factory=list)


class TrainingAssignRequest(BaseModel):
    """Payload to assign a training program to specific users or eligible audience."""

    model_config = ConfigDict(extra="forbid")

    program_id: UUID
    user_ids: list[UUID] = Field(..., min_length=1)
    due_date: datetime | None = None


class TrainingModuleCompleteRequest(BaseModel):
    """Payload to complete an assigned training module."""

    model_config = ConfigDict(extra="forbid")

    module_key: str = Field(..., min_length=1, max_length=64)
    notes: str | None = Field(default=None, max_length=255)


class TrainingAssignmentResponse(BaseModel):
    """Response DTO for a user's assigned training enrollment and progress."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    program_id: UUID
    user_id: UUID
    assigned_by_user_id: UUID | None
    status: str
    due_date: datetime | None
    completed_module_keys: list[str]
    module_progress_json: dict[str, Any]
    progress_pct: float
    started_at: datetime | None
    completed_at: datetime | None
    score: float | None
    certificate_reference: str | None
    created_at: datetime
    program: TrainingProgramResponse | None = None


# -----------------------------------------------------------------------------
# 3. Contextual In-App Guidance Schemas
# -----------------------------------------------------------------------------


class ContextualGuidanceCreateRequest(BaseModel):
    """Payload to configure contextual help, walkthrough steps, or banners."""

    model_config = ConfigDict(extra="forbid")

    guidance_key: str = Field(..., min_length=2, max_length=64)
    title: str = Field(..., min_length=2, max_length=255)
    content: str = Field(..., min_length=5)
    guidance_type: str = Field(default="TOOLTIP", description="GuidanceType: TOOLTIP, WALKTHROUGH, MODAL, BANNER")
    route_path: str = Field(..., min_length=1, max_length=255, description="Semantic frontend route, e.g. '/academics/attendance'")
    feature_key: str | None = Field(default=None, max_length=64)
    step_order: int = Field(default=1, ge=1)
    is_mandatory: bool = False
    target_roles: list[str] = Field(default_factory=list)
    expires_at: datetime | None = None
    document_url: str | None = Field(default=None, max_length=512)


class ContextualGuidanceUpdateRequest(BaseModel):
    """Payload to edit contextual guidance."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=2, max_length=255)
    content: str | None = Field(default=None, min_length=5)
    guidance_type: str | None = None
    step_order: int | None = None
    is_mandatory: bool | None = None
    target_roles: list[str] | None = None
    status: str | None = None
    expires_at: datetime | None = None
    document_url: str | None = None


class ContextualGuidanceResponse(BaseModel):
    """Response DTO for contextual in-app guidance."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID | None
    guidance_key: str
    title: str
    content: str
    guidance_type: str
    route_path: str
    feature_key: str | None
    step_order: int
    is_mandatory: bool
    target_roles: list[str]
    status: str
    version: int
    expires_at: datetime | None
    document_url: str | None
    created_at: datetime


class UserGuidanceActionRequest(BaseModel):
    """Payload to record user interaction with contextual guidance."""

    model_config = ConfigDict(extra="forbid")

    action: str = Field(..., description="UserGuidanceAction: SEEN, DISMISSED, COMPLETED")


class UserGuidanceStateResponse(BaseModel):
    """Response DTO for user guidance state."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    user_id: UUID
    guidance_id: UUID
    status: str
    impressions_count: int
    last_seen_at: datetime
    completed_at: datetime | None
    dismissed_at: datetime | None


# -----------------------------------------------------------------------------
# 4. Product Announcements & Change Notices Schemas
# -----------------------------------------------------------------------------


class ProductAnnouncementCreateRequest(BaseModel):
    """Payload to draft and schedule a product release announcement."""

    model_config = ConfigDict(extra="forbid")

    announcement_code: str = Field(..., min_length=2, max_length=64)
    title: str = Field(..., min_length=3, max_length=255)
    summary: str | None = Field(default=None, max_length=512)
    content: str = Field(..., min_length=5)
    category: str = Field(
        default="FEATURE_RELEASE",
        description="AnnouncementCategory: FEATURE_RELEASE, WORKFLOW_CHANGE, MAINTENANCE, POLICY_UPDATE, DEPRECATION",
    )
    priority: str = Field(default="NORMAL", description="AnnouncementPriority: LOW, NORMAL, HIGH, URGENT")
    effective_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None
    requires_acknowledgement: bool = False
    target_roles: list[str] = Field(default_factory=list)
    target_departments: list[str] = Field(default_factory=list)
    feature_flag_key: str | None = Field(default=None, max_length=128)
    doc_link_url: str | None = Field(default=None, max_length=512)


class ProductAnnouncementUpdateRequest(BaseModel):
    """Payload to update an announcement draft or published notice."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=3, max_length=255)
    summary: str | None = None
    content: str | None = Field(default=None, min_length=5)
    category: str | None = None
    priority: str | None = None
    effective_at: datetime | None = None
    expires_at: datetime | None = None
    requires_acknowledgement: bool | None = None
    target_roles: list[str] | None = None
    target_departments: list[str] | None = None
    feature_flag_key: str | None = None
    doc_link_url: str | None = None


class ProductAnnouncementResponse(BaseModel):
    """Response DTO for a product announcement."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID | None
    announcement_code: str
    title: str
    summary: str | None
    content: str
    category: str
    priority: str
    status: str
    effective_at: datetime
    expires_at: datetime | None
    requires_acknowledgement: bool
    target_roles: list[str]
    target_departments: list[str]
    feature_flag_key: str | None
    doc_link_url: str | None
    version: int
    published_at: datetime | None
    created_by_user_id: UUID | None
    created_at: datetime
    # User-specific contextual status if queried in user context
    user_is_read: bool = False
    user_is_acknowledged: bool = False


class AnnouncementAcknowledgeRequest(BaseModel):
    """Payload for user acknowledgement of a mandatory change announcement."""

    model_config = ConfigDict(extra="forbid")

    acknowledgement_notes: str | None = Field(default=None, max_length=512)


class UserAnnouncementReceiptResponse(BaseModel):
    """Response DTO for user announcement read & acknowledgement receipt."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    user_id: UUID
    announcement_id: UUID
    announcement_version: int
    is_read: bool
    read_at: datetime
    is_acknowledged: bool
    acknowledged_at: datetime | None
    acknowledgement_notes: str | None


# -----------------------------------------------------------------------------
# 5. Adoption Targets & Milestones Schemas
# -----------------------------------------------------------------------------


class FeatureAdoptionTargetCreateRequest(BaseModel):
    """Payload to define an adoption objective for a feature."""

    model_config = ConfigDict(extra="forbid")

    feature_key: str = Field(..., min_length=2, max_length=128)
    feature_name: str = Field(..., min_length=2, max_length=255)
    target_roles: list[str] = Field(default_factory=list)
    target_adoption_pct: float = Field(default=80.0, ge=1.0, le=100.0)
    window_start_date: datetime
    window_end_date: datetime


class FeatureAdoptionTargetResponse(BaseModel):
    """Response DTO for feature adoption targets."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    feature_key: str
    feature_name: str
    target_roles: list[str]
    target_adoption_pct: float
    window_start_date: datetime
    window_end_date: datetime
    status: str
    created_at: datetime


class FeatureAdoptionMilestoneRecordRequest(BaseModel):
    """Payload to record a server-validated feature discovery or usage milestone."""

    model_config = ConfigDict(extra="forbid")

    feature_key: str = Field(..., min_length=2, max_length=128)
    milestone_type: str = Field(
        default="DISCOVERY",
        description="AdoptionMilestoneType: DISCOVERY, FIRST_USE, REPEAT_USE, WORKFLOW_COMPLETED",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class FeatureAdoptionMilestoneResponse(BaseModel):
    """Response DTO for a recorded adoption milestone."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    user_id: UUID
    feature_key: str
    milestone_type: str
    metadata_json: dict[str, Any]
    recorded_at: datetime


# -----------------------------------------------------------------------------
# 6. Adoption Analytics & Reporting Schemas
# -----------------------------------------------------------------------------


class StepDropoffMetric(BaseModel):
    """Step-level drop-off data within an onboarding journey."""

    step_key: str
    step_title: str
    step_order: int
    completed_users_count: int
    dropoff_rate_pct: float


class JourneyAdoptionMetricsResponse(BaseModel):
    """Aggregated onboarding journey metrics."""

    journey_id: UUID
    journey_code: str
    journey_title: str
    total_assigned_or_eligible: int
    started_count: int
    completed_count: int
    completion_rate_pct: float
    median_duration_minutes: float | None = None
    step_metrics: list[StepDropoffMetric] = Field(default_factory=list)


class TrainingProgramMetricsResponse(BaseModel):
    """Aggregated training assignment and completion metrics."""

    program_id: UUID
    program_code: str
    program_title: str
    total_enrolled: int
    in_progress_count: int
    completed_count: int
    overdue_count: int
    completion_rate_pct: float
    average_score: float | None = None


class AnnouncementReadershipMetricsResponse(BaseModel):
    """Aggregated product announcement readership and acknowledgement metrics."""

    announcement_id: UUID
    announcement_code: str
    title: str
    category: str
    total_target_users: int
    read_count: int
    read_rate_pct: float
    acknowledged_count: int
    acknowledgement_rate_pct: float


class FeatureRolloutAdoptionMetricsResponse(BaseModel):
    """Aggregated adoption metrics for an enterprise feature."""

    feature_key: str
    feature_name: str
    target_adoption_pct: float
    current_adoption_pct: float
    total_eligible_users: int
    discovery_count: int
    first_use_count: int
    repeat_use_count: int
    workflow_completed_count: int
    adoption_status: str


class AdoptionSummaryDashboardResponse(BaseModel):
    """Comprehensive high-level adoption and enablement health overview."""

    tenant_id: UUID
    active_journeys_count: int
    journey_overall_completion_rate: float
    active_training_programs_count: int
    training_overall_completion_rate: float
    overdue_trainings_count: int
    active_announcements_count: int
    pending_acknowledgements_count: int
    tracked_features_count: int
    top_adopted_features: list[str] = Field(default_factory=list)
    low_adoption_features: list[str] = Field(default_factory=list)
