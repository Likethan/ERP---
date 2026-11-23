"""CampusOS Enterprise Student Affairs, Grievance Redressal & Disciplinary Case Management Schemas (Step 58).

CampusOS Tagline: "One Campus. One System. One Source of Truth."
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.student_affairs import (
    ActionStatus,
    ActionType,
    AppealGrounds,
    AppealStatus,
    CasePriority,
    CaseStatus,
    CaseType,
    ConfidentialityLevel,
    DisciplinaryStage,
    EscalationLevel,
    EvidenceAccessLevel,
    EvidenceType,
    FindingStatus,
    MeetingStatus,
    MeetingType,
    ParticipantRole,
    SanctionType,
    SubmitterType,
)

# =============================================================================
# 1. OFFICE & CATEGORY SCHEMAS
# =============================================================================


class StudentAffairsOfficeCreate(BaseModel):
    code: str = Field(..., max_length=64)
    name: str = Field(..., max_length=128)
    campus_id: UUID | None = None
    description: str | None = None
    dean_or_director_id: UUID | None = None
    location: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    is_active: bool = True


class StudentAffairsOfficeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    campus_id: UUID | None = None
    code: str
    name: str
    description: str | None = None
    dean_or_director_id: UUID | None = None
    location: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class GrievanceCategoryCreate(BaseModel):
    code: str = Field(..., max_length=64)
    name: str = Field(..., max_length=128)
    description: str | None = None
    case_type: CaseType = CaseType.GRIEVANCE
    default_priority: CasePriority = CasePriority.MEDIUM
    sla_response_hours: int = 48
    sla_resolution_days: int = 15
    requires_confidentiality: bool = False
    allow_anonymous: bool = True
    is_active: bool = True


class GrievanceCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    code: str
    name: str
    description: str | None = None
    case_type: str
    default_priority: str
    sla_response_hours: int
    sla_resolution_days: int
    requires_confidentiality: bool
    allow_anonymous: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 2. GRIEVANCE CASE SCHEMAS
# =============================================================================


class GrievanceCaseSubmit(BaseModel):
    category_id: UUID
    title: str = Field(..., max_length=255)
    description: str
    requested_resolution: str | None = None
    campus_id: UUID | None = None
    is_anonymous: bool = False
    submitter_type: SubmitterType = SubmitterType.STUDENT
    confidentiality_level: ConfidentialityLevel = ConfidentialityLevel.STANDARD
    supporting_document_ids: list[UUID] = Field(default_factory=list)


class GrievanceCaseUpdate(BaseModel):
    status: CaseStatus | None = None
    priority: CasePriority | None = None
    confidentiality_level: ConfidentialityLevel | None = None
    assigned_office_id: UUID | None = None
    assigned_officer_id: UUID | None = None
    target_response_date: datetime | None = None
    target_resolution_date: datetime | None = None
    resolution_summary: str | None = None


class GrievanceCaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    case_number: str
    case_type: str
    category_id: UUID
    category_name: str | None = None
    title: str
    description: str
    requested_resolution: str | None = None
    status: str
    priority: str
    confidentiality_level: str
    is_anonymous: bool
    submitter_type: str
    submitter_name_redacted: str
    campus_id: UUID | None = None
    assigned_office_id: UUID | None = None
    assigned_officer_id: UUID | None = None
    assigned_officer_name: str | None = None
    target_response_date: datetime | None = None
    target_resolution_date: datetime | None = None
    is_escalated: bool
    escalation_reason: str | None = None
    resolution_summary: str | None = None
    resolution_date: datetime | None = None
    closed_at: datetime | None = None
    reopen_count: int
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 3. PARTICIPANTS & ASSIGNMENT SCHEMAS
# =============================================================================


class CaseParticipantCreate(BaseModel):
    user_id: UUID
    role: ParticipantRole
    is_confidential: bool = False


class ConflictDeclaration(BaseModel):
    has_conflict_of_interest: bool
    conflict_reason: str = Field(..., min_length=5)


class CaseParticipantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    case_id: UUID
    user_id: UUID
    user_name: str | None = None
    user_email: str | None = None
    role: str
    is_confidential: bool
    has_conflict_of_interest: bool
    conflict_declared_at: datetime | None = None
    conflict_reason: str | None = None
    created_at: datetime


class CaseReassignRequest(BaseModel):
    new_officer_id: UUID
    reason: str = Field(..., min_length=5)


class CaseAssignmentHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    case_id: UUID
    previous_officer_id: UUID | None = None
    previous_officer_name: str | None = None
    new_officer_id: UUID | None = None
    new_officer_name: str | None = None
    assigned_by_id: UUID
    assigned_by_name: str | None = None
    reason: str | None = None
    created_at: datetime


# =============================================================================
# 4. DISCIPLINARY PROCEEDING SCHEMAS
# =============================================================================


class DisciplinaryProceedingCreate(BaseModel):
    respondent_student_id: UUID
    allegation_summary: str
    policy_provisions_violated: str
    notice_issued_at: datetime | None = None
    response_due_at: datetime | None = None


class DisciplinaryFindingsRecord(BaseModel):
    findings_summary: str
    finding_status: FindingStatus
    procedural_stage: DisciplinaryStage = DisciplinaryStage.FINDINGS_RECORDED


class DisciplinarySanctionApprove(BaseModel):
    sanction_type: SanctionType
    sanction_details: str
    decision_maker_id: UUID
    appeal_deadline_days: int = 14


class DisciplinaryProceedingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    case_id: UUID
    respondent_student_id: UUID
    respondent_name: str | None = None
    allegation_summary: str
    policy_provisions_violated: str
    procedural_stage: str
    notice_issued_at: datetime | None = None
    response_due_at: datetime | None = None
    respondent_plea: str | None = None
    findings_summary: str | None = None
    finding_status: str
    sanction_type: str
    sanction_details: str | None = None
    decision_maker_id: UUID | None = None
    decision_maker_name: str | None = None
    decision_date: datetime | None = None
    is_communicated: bool
    appeal_deadline: datetime | None = None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 5. EVIDENCE & DOCUMENT SCHEMAS
# =============================================================================


class CaseEvidenceUpload(BaseModel):
    evidence_type: EvidenceType = EvidenceType.DOCUMENT
    title: str = Field(..., max_length=255)
    description: str | None = None
    file_url: str
    file_size_bytes: int = 0
    confidentiality_level: EvidenceAccessLevel = EvidenceAccessLevel.STANDARD
    document_id: UUID | None = None


class CaseEvidenceRedact(BaseModel):
    redaction_summary: str
    redacted_file_url: str


class CaseEvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    case_id: UUID
    document_id: UUID | None = None
    evidence_type: str
    title: str
    description: str | None = None
    file_url: str
    file_size_bytes: int
    uploaded_by_id: UUID
    uploaded_by_name: str | None = None
    confidentiality_level: str
    is_redacted: bool
    redaction_summary: str | None = None
    original_evidence_id: UUID | None = None
    created_at: datetime


# =============================================================================
# 6. CASE MEETINGS & COMMUNICATIONS
# =============================================================================


class CaseMeetingCreate(BaseModel):
    title: str = Field(..., max_length=255)
    meeting_type: MeetingType
    scheduled_start: datetime
    scheduled_end: datetime
    venue_or_url: str | None = None
    facilitator_id: UUID | None = None


class CaseMeetingUpdate(BaseModel):
    status: MeetingStatus | None = None
    notes_confidential: str | None = None
    agreed_actions: str | None = None


class CaseMeetingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    case_id: UUID
    title: str
    meeting_type: str
    scheduled_start: datetime
    scheduled_end: datetime
    venue_or_url: str | None = None
    status: str
    facilitator_id: UUID | None = None
    facilitator_name: str | None = None
    notes_confidential: str | None = None
    agreed_actions: str | None = None
    created_at: datetime


class CaseCommunicationCreate(BaseModel):
    message_text: str
    is_internal_only: bool = False
    attachment_url: str | None = None


class CaseCommunicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    case_id: UUID
    sender_id: UUID
    sender_name: str
    is_internal_only: bool
    message_text: str
    attachment_url: str | None = None
    read_at: datetime | None = None
    created_at: datetime


# =============================================================================
# 7. RESOLUTIONS, APPEALS & ESCALATIONS
# =============================================================================


class ResolutionActionCreate(BaseModel):
    description: str
    action_type: ActionType
    assigned_owner_id: UUID | None = None
    due_date: date | None = None


class ResolutionActionUpdate(BaseModel):
    status: ActionStatus
    completion_notes: str | None = None


class ResolutionActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    case_id: UUID
    description: str
    action_type: str
    assigned_owner_id: UUID | None = None
    assigned_owner_name: str | None = None
    due_date: date | None = None
    status: str
    completed_at: datetime | None = None
    completion_notes: str | None = None
    created_at: datetime


class AppealRecordCreate(BaseModel):
    appeal_grounds: AppealGrounds
    grounds_statement: str


class AppealReviewDecision(BaseModel):
    assigned_reviewer_id: UUID
    review_status: AppealStatus
    outcome_summary: str


class AppealRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    case_id: UUID
    appellant_id: UUID
    appellant_name: str | None = None
    appeal_date: datetime
    appeal_grounds: str
    grounds_statement: str
    assigned_reviewer_id: UUID | None = None
    assigned_reviewer_name: str | None = None
    review_status: str
    outcome_summary: str | None = None
    outcome_date: datetime | None = None
    created_at: datetime


class CaseEscalationCreate(BaseModel):
    escalation_level: EscalationLevel = EscalationLevel.LEVEL_2_DIRECTOR
    reason: str
    actions_taken: str | None = None
    safety_referral_sent: bool = False


class CaseEscalationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    case_id: UUID
    escalated_by_id: UUID
    escalated_by_name: str | None = None
    escalation_level: str
    reason: str
    actions_taken: str | None = None
    safety_referral_sent: bool
    status: str
    created_at: datetime


class CaseAccessAuditResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    case_id: UUID
    user_id: UUID
    user_name: str | None = None
    action: str
    ip_address: str | None = None
    details: str | None = None
    created_at: datetime


class StudentAffairsPolicyConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    grievance_sla_days: int
    appeal_window_days: int
    anonymous_reporting_allowed: bool
    separation_of_appeals_required: bool
    safeguarding_emergency_contact: str
    policy_handbook_version: str
    created_at: datetime
    updated_at: datetime


class StudentAffairsDashboardTelemetry(BaseModel):
    total_active_cases: int
    open_grievances: int
    pending_disciplinary_cases: int
    urgent_escalations_count: int
    appeals_under_review: int
    sla_compliance_rate: float
    avg_resolution_days: float
    total_hearings_scheduled: int
    corrective_actions_pending: int
    anonymous_reports_count: int
