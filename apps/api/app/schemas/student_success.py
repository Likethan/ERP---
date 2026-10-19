"""Pydantic v2 Schemas for Student Success, Advising, Early-Warning & Intervention (Step 47)."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.student_success import (
    ActionItemStatus,
    ActionResponsibleParty,
    AdvisingPlanStatus,
    AdvisorCategory,
    AppointmentMode,
    AppointmentStatus,
    AssignmentRelationshipType,
    CaseCategory,
    CaseClosureReason,
    CaseCreationSource,
    CaseOutcomeClassification,
    CasePriority,
    CaseStatus,
    ComparisonOperator,
    EarlyWarningCategory,
    EvaluationScope,
    InterventionStatus,
    InterventionType,
    NoteType,
    ReviewFrequency,
    StudentParticipation,
    WarningSeverity,
)

# =============================================================================
# CASE MANAGEMENT SCHEMAS
# =============================================================================


class StudentSuccessCaseNoteCreate(BaseModel):
    """Payload to add a comment or note to a case."""

    note_type: NoteType = NoteType.INTERNAL_NOTE
    content: str = Field(..., min_length=1)
    is_student_visible: bool = False


class StudentSuccessCaseNoteResponse(BaseModel):
    """Case note record with author attribution and student-visibility flag."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    case_id: UUID
    author_user_id: UUID
    author_name: str | None = None
    note_type: str
    content: str
    is_student_visible: bool
    created_at: datetime
    updated_at: datetime


class StudentSuccessCaseCreate(BaseModel):
    """Payload to open a new student success case."""

    student_id: UUID
    category: CaseCategory = CaseCategory.ACADEMIC_PERFORMANCE
    priority: CasePriority = CasePriority.MEDIUM
    title: str = Field(..., min_length=3, max_length=255)
    description: str | None = None
    objective: str | None = None
    creation_source: CaseCreationSource = CaseCreationSource.ADVISOR_MANUAL
    assigned_advisor_id: UUID | None = None
    assigned_to_user_id: UUID | None = None
    target_completion_date: date | None = None
    next_review_date: date | None = None
    related_case_id: UUID | None = None


class StudentSuccessCaseUpdate(BaseModel):
    """Payload to update editable metadata of an active case."""

    title: str | None = Field(None, min_length=3, max_length=255)
    description: str | None = None
    objective: str | None = None
    priority: CasePriority | None = None
    category: CaseCategory | None = None
    target_completion_date: date | None = None
    next_review_date: date | None = None


class StudentSuccessCaseStatusTransition(BaseModel):
    """Payload to transition lifecycle status of a case."""

    status: CaseStatus
    transition_notes: str | None = None
    closure_reason: CaseClosureReason | None = None
    outcome_classification: CaseOutcomeClassification | None = None
    outcome_notes: str | None = None


class StudentSuccessCaseReassign(BaseModel):
    """Payload to reassign case ownership with an audit trail."""

    assigned_advisor_id: UUID | None = None
    assigned_to_user_id: UUID | None = None
    reassignment_reason: str = Field(..., min_length=3)


class StudentSuccessCaseEscalate(BaseModel):
    """Payload to escalate an overdue or critical case."""

    escalation_reason: str = Field(..., min_length=3)


class StudentSuccessCaseReopen(BaseModel):
    """Payload to reopen a previously resolved/closed case."""

    reopen_reason: str = Field(..., min_length=3)


class StudentSuccessCaseResponse(BaseModel):
    """Comprehensive view of a student success case."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    case_number: str
    student_id: UUID
    student_name: str | None = None
    student_admission_number: str | None = None
    category: str
    priority: str
    status: str
    title: str
    description: str | None = None
    objective: str | None = None
    creation_source: str
    assigned_advisor_id: UUID | None = None
    assigned_advisor_name: str | None = None
    assigned_to_user_id: UUID | None = None
    created_by_user_id: UUID | None = None
    target_completion_date: date | None = None
    next_review_date: date | None = None
    actual_resolution_date: datetime | None = None
    closure_reason: str | None = None
    outcome_classification: str | None = None
    outcome_notes: str | None = None
    is_escalated: bool
    escalation_reason: str | None = None
    escalated_at: datetime | None = None
    reopened_at: datetime | None = None
    reopened_reason: str | None = None
    related_case_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# ADVISOR PROFILE & ASSIGNMENT SCHEMAS
# =============================================================================


class AdvisorProfileCreate(BaseModel):
    """Payload to register an academic advisor with capacity limits."""

    user_id: UUID
    staff_id: UUID | None = None
    advisor_category: AdvisorCategory = AdvisorCategory.FACULTY_ADVISOR
    department_id: UUID | None = None
    campus_id: UUID | None = None
    program_id: UUID | None = None
    max_student_capacity: int = Field(30, ge=1, le=500)
    availability_schedule: dict[str, Any] | None = None


class AdvisorProfileUpdate(BaseModel):
    """Payload to update an advisor's capacity or departmental scope."""

    advisor_category: AdvisorCategory | None = None
    department_id: UUID | None = None
    campus_id: UUID | None = None
    program_id: UUID | None = None
    max_student_capacity: int | None = Field(None, ge=1, le=500)
    availability_schedule: dict[str, Any] | None = None
    is_active: bool | None = None


class AdvisorProfileResponse(BaseModel):
    """Academic advisor profile with caseload capacity telemetry."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    user_id: UUID
    advisor_name: str | None = None
    staff_id: UUID | None = None
    advisor_category: str
    department_id: UUID | None = None
    department_name: str | None = None
    campus_id: UUID | None = None
    program_id: UUID | None = None
    max_student_capacity: int
    current_student_count: int
    available_capacity: int = 0
    availability_schedule: dict[str, Any] | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AdvisorStudentAssignmentCreate(BaseModel):
    """Assign an advisor to a student."""

    advisor_id: UUID
    student_id: UUID
    relationship_type: AssignmentRelationshipType = AssignmentRelationshipType.PRIMARY
    start_date: date = Field(default_factory=date.today)
    end_date: date | None = None


class AdvisorStudentAssignmentReassign(BaseModel):
    """Reassign student to a new advisor with recorded reason."""

    new_advisor_id: UUID
    reassignment_reason: str = Field(..., min_length=3)


class AdvisorStudentAssignmentResponse(BaseModel):
    """Advisor-to-student relationship record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    advisor_id: UUID
    advisor_name: str | None = None
    student_id: UUID
    student_name: str | None = None
    relationship_type: str
    start_date: date
    end_date: date | None = None
    status: str
    reassignment_reason: str | None = None
    assigned_by_user_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# ADVISING PLAN & ACTION ITEM SCHEMAS
# =============================================================================


class AdvisingActionItemCreate(BaseModel):
    """Payload to create an action item in an advising plan."""

    title: str = Field(..., min_length=3, max_length=255)
    description: str | None = None
    responsible_party: ActionResponsibleParty = ActionResponsibleParty.STUDENT
    due_date: date | None = None
    is_student_visible: bool = True


class AdvisingActionItemUpdate(BaseModel):
    """Payload to update or complete an advising action item."""

    title: str | None = Field(None, min_length=3, max_length=255)
    description: str | None = None
    responsible_party: ActionResponsibleParty | None = None
    due_date: date | None = None
    completed_date: date | None = None
    status: ActionItemStatus | None = None
    is_student_visible: bool | None = None
    student_progress_notes: str | None = None


class AdvisingActionItemResponse(BaseModel):
    """Action item details within an advising plan."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    advising_plan_id: UUID
    title: str
    description: str | None = None
    responsible_party: str
    due_date: date | None = None
    completed_date: date | None = None
    status: str
    is_student_visible: bool
    student_progress_notes: str | None = None
    created_at: datetime
    updated_at: datetime


class AdvisingPlanCreate(BaseModel):
    """Payload to establish an academic advising plan."""

    student_id: UUID
    advisor_id: UUID
    case_id: UUID | None = None
    title: str = Field(..., min_length=3, max_length=255)
    academic_goals: str | None = None
    target_gpa: Decimal | None = Field(None, ge=0.0, le=10.0)
    target_credits: int | None = Field(None, ge=0)
    review_frequency: ReviewFrequency = ReviewFrequency.MONTHLY
    start_date: date = Field(default_factory=date.today)
    end_date: date | None = None
    is_student_visible: bool = True
    initial_action_items: list[AdvisingActionItemCreate] = Field(default_factory=list)


class AdvisingPlanUpdate(BaseModel):
    """Payload to update an advising plan."""

    title: str | None = Field(None, min_length=3, max_length=255)
    academic_goals: str | None = None
    target_gpa: Decimal | None = Field(None, ge=0.0, le=10.0)
    target_credits: int | None = Field(None, ge=0)
    review_frequency: ReviewFrequency | None = None
    status: AdvisingPlanStatus | None = None
    end_date: date | None = None
    is_student_visible: bool | None = None


class AdvisingPlanResponse(BaseModel):
    """Academic advising plan with nested action items."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    student_id: UUID
    student_name: str | None = None
    advisor_id: UUID
    advisor_name: str | None = None
    case_id: UUID | None = None
    title: str
    academic_goals: str | None = None
    target_gpa: Decimal | None = None
    target_credits: int | None = None
    review_frequency: str
    start_date: date
    end_date: date | None = None
    status: str
    is_student_visible: bool
    action_items: list[AdvisingActionItemResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


# =============================================================================
# EARLY WARNING RULES & EVALUATIONS SCHEMAS
# =============================================================================


class EarlyWarningRuleCreate(BaseModel):
    """Payload to author a configurable early-warning risk rule."""

    code: str = Field(..., min_length=3, max_length=64)
    name: str = Field(..., min_length=3, max_length=255)
    description: str | None = None
    category: EarlyWarningCategory = EarlyWarningCategory.ATTENDANCE
    operator: ComparisonOperator = ComparisonOperator.LESS_THAN
    threshold_value: Decimal = Field(..., description="Target threshold (e.g. 75.00 for attendance %)")
    evaluation_window_days: int = Field(30, ge=1, le=365)
    department_id: UUID | None = None
    program_id: UUID | None = None
    academic_term_id: UUID | None = None
    severity: WarningSeverity = WarningSeverity.HIGH
    recommended_intervention_category: InterventionType = InterventionType.ATTENDANCE_FOLLOWUP
    effective_from: date | None = None
    effective_to: date | None = None


class EarlyWarningRuleUpdate(BaseModel):
    """Payload to revise thresholds or settings of a rule, creating an audit version."""

    name: str | None = Field(None, min_length=3, max_length=255)
    description: str | None = None
    operator: ComparisonOperator | None = None
    threshold_value: Decimal | None = None
    evaluation_window_days: int | None = Field(None, ge=1, le=365)
    severity: WarningSeverity | None = None
    recommended_intervention_category: InterventionType | None = None
    is_active: bool | None = None
    change_reason: str = Field(..., min_length=3, description="Justification for threshold modification")


class EarlyWarningRuleVersionResponse(BaseModel):
    """Audit version record of an early-warning rule."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    rule_id: UUID
    version_number: int
    operator: str
    threshold_value: Decimal
    evaluation_window_days: int
    severity: str
    changed_by_user_id: UUID | None = None
    change_reason: str | None = None
    created_at: datetime


class EarlyWarningRuleResponse(BaseModel):
    """Early-warning rule definition with active version."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    code: str
    name: str
    description: str | None = None
    category: str
    operator: str
    threshold_value: Decimal
    evaluation_window_days: int
    department_id: UUID | None = None
    program_id: UUID | None = None
    academic_term_id: UUID | None = None
    severity: str
    recommended_intervention_category: str
    is_active: bool
    current_version: int
    effective_from: date | None = None
    effective_to: date | None = None
    created_at: datetime
    updated_at: datetime


class EarlyWarningEvaluationRequest(BaseModel):
    """Request to trigger rule evaluation for a scope."""

    rule_id: UUID | None = None  # None evaluates all active rules
    evaluation_scope: EvaluationScope = EvaluationScope.ALL_STUDENTS
    scope_id: UUID | None = None
    student_id: UUID | None = None


class EarlyWarningEvaluationResponse(BaseModel):
    """Execution report of a rule evaluation run."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    rule_id: UUID
    evaluation_scope: str
    scope_id: UUID | None = None
    evaluation_timestamp: datetime
    triggered_by: str
    students_evaluated_count: int
    warnings_generated_count: int
    status: str
    execution_notes: str | None = None
    created_at: datetime


# =============================================================================
# EARLY WARNING SIGNAL SCHEMAS
# =============================================================================


class EarlyWarningSignalDismiss(BaseModel):
    """Payload to dismiss an early-warning signal."""

    dismissal_reason: str = Field(..., min_length=3)
    is_false_positive: bool = False


class EarlyWarningSignalResolve(BaseModel):
    """Payload to mark a signal as resolved."""

    resolution_notes: str = Field(..., min_length=3)


class EarlyWarningSignalLinkCase(BaseModel):
    """Payload to link a signal to an existing case or create a new case."""

    case_id: UUID | None = None
    create_new_case: bool = False
    new_case_title: str | None = None


class EarlyWarningSignalResponse(BaseModel):
    """Explainable risk alert with source metrics and audit evidence."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    student_id: UUID
    student_name: str | None = None
    student_admission_number: str | None = None
    rule_id: UUID
    rule_code: str | None = None
    rule_name: str | None = None
    rule_version: int
    evaluation_id: UUID | None = None
    signal_code: str
    observation_period_start: date
    observation_period_end: date
    metric_observed_value: Decimal
    threshold_condition: str
    source_record_references: list[dict[str, Any]]
    severity: str
    status: str
    dismissal_reason: str | None = None
    is_false_positive: bool
    acknowledged_at: datetime | None = None
    acknowledged_by_user_id: UUID | None = None
    resolved_at: datetime | None = None
    resolution_notes: str | None = None
    success_case_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# INTERVENTION SCHEMAS
# =============================================================================


class InterventionActionCreate(BaseModel):
    """Payload to add an action to an intervention plan."""

    title: str = Field(..., min_length=3, max_length=255)
    description: str | None = None
    due_date: date | None = None
    is_student_visible: bool = True


class InterventionActionUpdate(BaseModel):
    """Payload to update or complete an intervention action."""

    title: str | None = Field(None, min_length=3, max_length=255)
    description: str | None = None
    due_date: date | None = None
    completed_date: date | None = None
    status: ActionItemStatus | None = None
    is_student_visible: bool | None = None
    completion_notes: str | None = None


class InterventionActionResponse(BaseModel):
    """Action item details within an intervention plan."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    intervention_plan_id: UUID
    title: str
    description: str | None = None
    due_date: date | None = None
    completed_date: date | None = None
    status: str
    is_student_visible: bool
    completion_notes: str | None = None
    created_at: datetime
    updated_at: datetime


class InterventionPlanCreate(BaseModel):
    """Payload to initiate a student intervention."""

    student_id: UUID
    case_id: UUID | None = None
    warning_signal_id: UUID | None = None
    title: str = Field(..., min_length=3, max_length=255)
    description: str | None = None
    objective: str | None = None
    intervention_type: InterventionType = InterventionType.ACADEMIC_ADVISING
    priority: CasePriority = CasePriority.MEDIUM
    assigned_to_user_id: UUID | None = None
    planned_start_date: date = Field(default_factory=date.today)
    target_completion_date: date
    actions: list[InterventionActionCreate] = Field(default_factory=list)


class InterventionPlanUpdate(BaseModel):
    """Payload to update an intervention workflow."""

    title: str | None = Field(None, min_length=3, max_length=255)
    description: str | None = None
    objective: str | None = None
    priority: CasePriority | None = None
    status: InterventionStatus | None = None
    target_completion_date: date | None = None
    actual_completion_date: date | None = None
    student_participation: StudentParticipation | None = None
    outcome_classification: str | None = None
    outcome_notes: str | None = None
    cancellation_reason: str | None = None


class InterventionPlanResponse(BaseModel):
    """Intervention plan with execution actions and outcome metrics."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    student_id: UUID
    student_name: str | None = None
    case_id: UUID | None = None
    warning_signal_id: UUID | None = None
    title: str
    description: str | None = None
    objective: str | None = None
    intervention_type: str
    priority: str
    status: str
    assigned_to_user_id: UUID | None = None
    assigned_to_name: str | None = None
    planned_start_date: date
    target_completion_date: date
    actual_completion_date: date | None = None
    student_participation: str
    outcome_classification: str | None = None
    outcome_notes: str | None = None
    cancellation_reason: str | None = None
    actions: list[InterventionActionResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


# =============================================================================
# APPOINTMENT SCHEMAS
# =============================================================================


class AdvisingAppointmentRequest(BaseModel):
    """Student or advisor request to schedule an advising session."""

    advisor_id: UUID
    student_id: UUID | None = None  # Inferred if requested by student
    case_id: UUID | None = None
    scheduled_start_time: datetime
    scheduled_end_time: datetime
    meeting_mode: AppointmentMode = AppointmentMode.IN_PERSON
    location_or_url: str | None = None
    agenda: str | None = None


class AdvisingAppointmentUpdate(BaseModel):
    """Update appointment details, record meeting summary or cancel."""

    scheduled_start_time: datetime | None = None
    scheduled_end_time: datetime | None = None
    meeting_mode: AppointmentMode | None = None
    location_or_url: str | None = None
    agenda: str | None = None
    status: AppointmentStatus | None = None
    meeting_notes: str | None = None  # Advisor internal notes
    agreed_action_summary: str | None = None  # Shared with student
    cancellation_reason: str | None = None


class AdvisingAppointmentResponse(BaseModel):
    """Advising appointment record (permission-aware)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    advisor_id: UUID
    advisor_name: str | None = None
    student_id: UUID
    student_name: str | None = None
    case_id: UUID | None = None
    scheduled_start_time: datetime
    scheduled_end_time: datetime
    meeting_mode: str
    location_or_url: str | None = None
    agenda: str | None = None
    status: str
    meeting_notes: str | None = None  # Scrubbed in student self-service
    agreed_action_summary: str | None = None
    cancellation_reason: str | None = None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# STUDENT SELF-SERVICE SCHEMAS
# =============================================================================


class StudentSelfOverviewResponse(BaseModel):
    """Sanitized student-facing portal summary. Excludes internal case notes and risk internals."""

    student_id: UUID
    student_name: str
    primary_advisor_name: str | None = None
    primary_advisor_id: UUID | None = None
    active_plans_count: int
    pending_action_items_count: int
    upcoming_appointments_count: int
    active_plans: list[AdvisingPlanResponse] = Field(default_factory=list)
    upcoming_appointments: list[AdvisingAppointmentResponse] = Field(default_factory=list)


class StudentActionProgressSubmit(BaseModel):
    """Student progress update on a permitted action item."""

    action_item_id: UUID
    student_progress_notes: str = Field(..., min_length=1)


# =============================================================================
# REPORTING & ANALYTICS SCHEMAS
# =============================================================================


class StudentSuccessOverviewMetrics(BaseModel):
    """Tenant-scoped aggregate student success operational metrics."""

    total_cases: int
    active_cases: int
    under_review_cases: int
    resolved_cases: int
    closed_cases: int
    escalated_cases: int
    overdue_cases: int

    total_warning_signals: int
    active_warning_signals: int
    acknowledged_signals: int
    false_positive_signals: int
    signals_by_severity: dict[str, int]
    signals_by_category: dict[str, int]

    total_interventions: int
    in_progress_interventions: int
    completed_interventions: int
    overdue_interventions: int

    total_advisors: int
    average_advisor_caseload: float
    capacity_utilization_percent: float

    # Explanatory and ethical governance notice
    analytical_notice: str = (
        "Statistical warning counts represent observational indicators for human triage. "
        "Correlations in intervention outcomes do not constitute causal claims without "
        "controlled counterfactual evaluation."
    )


class AdvisorCaseloadSummaryItem(BaseModel):
    """Caseload metric per academic advisor."""

    advisor_id: UUID
    advisor_name: str
    department_name: str | None = None
    max_capacity: int
    current_caseload: int
    utilization_percent: float
    active_cases_count: int
