"""Pydantic Schemas for Enterprise International Relations, Student Exchange & Global Mobility (Step 60).

Product Identity: "CampusOS — One Campus. One System. One Source of Truth."
"""

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.international import (
    AgreementScopeType,
    AgreementStatus,
    CreditEquivalencyStatus,
    CreditTransferStatus,
    FacultyMobilityDirection,
    FacultyMobilityStatus,
    InboundStudentStatus,
    MobilityApplicationStatus,
    MobilityDocumentType,
    MobilityDocumentVerificationStatus,
    MobilityFundingStatus,
    MobilityProgramType,
    MobilityTermType,
    PartnerCategory,
    ScholarshipAwardStatus,
)

# =============================================================================
# 1. INTERNATIONAL PARTNER SCHEMAS
# =============================================================================


class InternationalPartnerBase(BaseModel):
    partner_name: str = Field(..., min_length=2, max_length=255)
    legal_name: str | None = Field(None, max_length=255)
    country_code: str = Field(..., min_length=2, max_length=3)
    country_name: str = Field(..., min_length=2, max_length=100)
    city: str = Field(..., min_length=1, max_length=100)
    state_province: str | None = Field(None, max_length=100)
    category: PartnerCategory = PartnerCategory.UNIVERSITY
    official_website: str | None = Field(None, max_length=500)
    primary_contact_name: str | None = Field(None, max_length=150)
    primary_contact_email: str | None = Field(None, max_length=255)
    primary_contact_phone: str | None = Field(None, max_length=50)
    ranking_summary: dict[str, Any] = Field(default_factory=dict)
    institution_id: UUID | None = None
    campus_id: UUID | None = None
    department_id: UUID | None = None
    academic_program_id: UUID | None = None
    is_active: bool = True
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class InternationalPartnerCreate(InternationalPartnerBase):
    pass


class InternationalPartnerUpdate(BaseModel):
    partner_name: str | None = Field(None, min_length=2, max_length=255)
    legal_name: str | None = None
    country_code: str | None = None
    country_name: str | None = None
    city: str | None = None
    state_province: str | None = None
    category: PartnerCategory | None = None
    official_website: str | None = None
    primary_contact_name: str | None = None
    primary_contact_email: str | None = None
    primary_contact_phone: str | None = None
    ranking_summary: dict[str, Any] | None = None
    institution_id: UUID | None = None
    campus_id: UUID | None = None
    department_id: UUID | None = None
    academic_program_id: UUID | None = None
    is_active: bool | None = None
    metadata_json: dict[str, Any] | None = None


class InternationalPartnerResponse(InternationalPartnerBase):
    id: UUID
    tenant_id: UUID
    partner_code: str
    active_agreements_count: int = 0
    active_programs_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 2. INSTITUTIONAL AGREEMENTS & AMENDMENTS
# =============================================================================


class InstitutionalAgreementBase(BaseModel):
    partner_id: UUID
    agreement_title: str = Field(..., min_length=3, max_length=255)
    agreement_type: str = Field(..., max_length=100)  # MOU, Bilateral Exchange, etc.
    scope_types: list[AgreementScopeType] = Field(default_factory=lambda: [AgreementScopeType.STUDENT_EXCHANGE])
    effective_start_date: date
    effective_end_date: date
    renewal_window_days: int = 90
    auto_renew: bool = False
    responsible_coordinator_user_id: UUID | None = None
    department_id: UUID | None = None
    academic_program_id: UUID | None = None
    quota_inbound_per_year: int = 5
    quota_outbound_per_year: int = 5
    funding_support_notes: str | None = None
    document_reference_url: str | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class InstitutionalAgreementCreate(InstitutionalAgreementBase):
    status: AgreementStatus = AgreementStatus.DRAFT


class InstitutionalAgreementUpdate(BaseModel):
    agreement_title: str | None = None
    agreement_type: str | None = None
    scope_types: list[AgreementScopeType] | None = None
    effective_start_date: date | None = None
    effective_end_date: date | None = None
    renewal_window_days: int | None = None
    auto_renew: bool | None = None
    responsible_coordinator_user_id: UUID | None = None
    department_id: UUID | None = None
    academic_program_id: UUID | None = None
    quota_inbound_per_year: int | None = None
    quota_outbound_per_year: int | None = None
    funding_support_notes: str | None = None
    document_reference_url: str | None = None
    status: AgreementStatus | None = None
    metadata_json: dict[str, Any] | None = None


class InstitutionalAgreementResponse(InstitutionalAgreementBase):
    id: UUID
    tenant_id: UUID
    agreement_reference_number: str
    status: AgreementStatus
    approved_by_user_id: UUID | None = None
    approved_at: datetime | None = None
    rejection_or_suspension_reason: str | None = None
    partner_name: str | None = None
    partner_country: str | None = None
    coordinator_name: str | None = None
    is_expiring_soon: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class AgreementAmendmentCreate(BaseModel):
    amendment_type: str = Field(..., max_length=100)
    title: str = Field(..., max_length=255)
    description: str
    new_effective_end_date: date | None = None
    changes_json: dict[str, Any] = Field(default_factory=dict)
    document_reference_url: str | None = None


class AgreementAmendmentResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    agreement_id: UUID
    amendment_type: str
    title: str
    description: str
    new_effective_end_date: date | None = None
    changes_json: dict[str, Any] = Field(default_factory=dict)
    document_reference_url: str | None = None
    created_by_user_id: UUID | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 3. MOBILITY PROGRAMS & CYCLES
# =============================================================================


class MobilityProgramBase(BaseModel):
    partner_id: UUID
    agreement_id: UUID | None = None
    program_title: str = Field(..., min_length=3, max_length=255)
    program_code: str | None = Field(None, max_length=64)
    program_type: MobilityProgramType = MobilityProgramType.SEMESTER_EXCHANGE
    term_type: MobilityTermType = MobilityTermType.FALL_SEMESTER
    academic_year: str = Field(..., max_length=32)
    eligible_department_ids: list[UUID] = Field(default_factory=list)
    eligible_academic_program_ids: list[UUID] = Field(default_factory=list)
    total_seats: int = Field(5, ge=1)
    nomination_limit: int = Field(10, ge=1)
    min_cgpa_requirement: float | None = Field(None, ge=0.0, le=10.0)
    min_credits_completed: int | None = Field(None, ge=0)
    language_requirements: list[str] = Field(default_factory=list)
    eligible_semesters: list[int] = Field(default_factory=list)

    @field_validator("language_requirements", mode="before")
    @classmethod
    def parse_language_requirements(cls, v: Any) -> list[str]:
        if v is None:
            return []
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return []
    application_start_date: date
    application_deadline: date
    expected_start_date: date
    expected_end_date: date
    estimated_credits: int | None = None
    estimated_cost_notes: str | None = None
    scholarship_available: bool = False
    required_document_types: list[str] = Field(default_factory=list)
    coordinator_user_id: UUID | None = None
    faculty_lead_user_id: UUID | None = None
    instructions: str | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class MobilityProgramCreate(MobilityProgramBase):
    is_published: bool = False


class MobilityProgramUpdate(BaseModel):
    partner_id: UUID | None = None
    agreement_id: UUID | None = None
    program_title: str | None = None
    program_type: MobilityProgramType | None = None
    term_type: MobilityTermType | None = None
    academic_year: str | None = None
    eligible_department_ids: list[UUID] | None = None
    eligible_academic_program_ids: list[UUID] | None = None
    total_seats: int | None = None
    nomination_limit: int | None = None
    min_cgpa_requirement: float | None = None
    min_credits_completed: int | None = None
    language_requirements: list[str] | None = None
    eligible_semesters: list[int] | None = None
    application_start_date: date | None = None
    application_deadline: date | None = None
    expected_start_date: date | None = None
    expected_end_date: date | None = None
    estimated_credits: int | None = None
    estimated_cost_notes: str | None = None
    scholarship_available: bool | None = None
    required_document_types: list[str] | None = None
    coordinator_user_id: UUID | None = None
    faculty_lead_user_id: UUID | None = None
    instructions: str | None = None
    is_published: bool | None = None
    metadata_json: dict[str, Any] | None = None


class MobilityProgramResponse(MobilityProgramBase):
    id: UUID
    tenant_id: UUID
    program_code: str
    is_published: bool
    partner_name: str | None = None
    partner_country: str | None = None
    active_applications_count: int = 0
    accepted_students_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 4. STUDENT MOBILITY APPLICATIONS & REVIEWS
# =============================================================================


class MobilityApplicationCreate(BaseModel):
    program_id: UUID
    statement_of_purpose: str = Field(..., min_length=20)
    proposed_courses: list[dict[str, Any]] = Field(default_factory=list)
    emergency_contact_name: str = Field(..., max_length=100)
    emergency_contact_phone: str = Field(..., max_length=50)
    emergency_contact_relationship: str = Field(..., max_length=50)
    passport_number: str | None = Field(None, max_length=64)
    passport_expiry_date: date | None = None
    passport_country: str | None = Field(None, max_length=100)
    funding_source_declaration: str | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    submit_now: bool = False


class MobilityApplicationUpdate(BaseModel):
    statement_of_purpose: str | None = None
    proposed_courses: list[dict[str, Any]] | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    emergency_contact_relationship: str | None = None
    passport_number: str | None = None
    passport_expiry_date: date | None = None
    passport_country: str | None = None
    funding_source_declaration: str | None = None
    metadata_json: dict[str, Any] | None = None


class MobilityApplicationReviewRequest(BaseModel):
    action: str = Field(..., pattern="^(APPROVE|REJECT|RETURN|ESCALATE)$")
    comments: str = Field(..., min_length=3)
    conditions_or_reasons: str | None = None


class PartnerNominationRequest(BaseModel):
    nomination_notes: str | None = None
    partner_contact_email: str | None = None


class PartnerDecisionRequest(BaseModel):
    decision: str = Field(..., pattern="^(ACCEPTED|REJECTED)$")
    partner_reference_code: str | None = None
    official_response_notes: str | None = None


class PreDepartureUpdateRequest(BaseModel):
    pre_departure_checklist: dict[str, Any] = Field(default_factory=dict)
    visa_reference_number: str | None = None
    travel_itinerary: dict[str, Any] = Field(default_factory=dict)
    insurance_policy_number: str | None = None


class MobilityApplicationResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    application_reference_number: str
    program_id: UUID
    student_id: UUID
    status: MobilityApplicationStatus
    submitted_at: datetime | None = None
    statement_of_purpose: str
    proposed_courses: list[dict[str, Any]] = Field(default_factory=list)
    student_cgpa_at_application: float | None = None
    credits_completed_at_application: int | None = None
    eligibility_check_passed: bool = True
    eligibility_check_details: dict[str, Any] = Field(default_factory=dict)
    department_decision: str | None = None
    department_comments: str | None = None
    intl_office_decision: str | None = None
    intl_office_comments: str | None = None
    nominated_at: datetime | None = None
    partner_decision_notes: str | None = None
    pre_departure_checklist: dict[str, Any] = Field(default_factory=dict)
    program_title: str | None = None
    partner_name: str | None = None
    partner_country: str | None = None
    student_name: str | None = None
    student_roll_number: str | None = None
    department_name: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ApplicationReviewHistoryResponse(BaseModel):
    id: UUID
    application_id: UUID
    review_stage: str
    action: str
    reviewer_user_id: UUID | None = None
    reviewer_role: str | None = None
    reviewer_name: str | None = None
    comments: str | None = None
    conditions: str | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 5. INBOUND STUDENT PROFILES
# =============================================================================


class InboundStudentCreate(BaseModel):
    partner_id: UUID
    student_first_name: str = Field(..., min_length=1, max_length=100)
    student_last_name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., max_length=255)
    phone: str | None = Field(None, max_length=50)
    country_of_citizenship: str = Field(..., min_length=2, max_length=100)
    home_institution_name: str = Field(..., max_length=255)
    home_program_of_study: str = Field(..., max_length=150)
    host_department_id: UUID | None = None
    host_academic_program_id: UUID | None = None
    expected_start_date: date
    expected_end_date: date
    study_period_terms: str = Field(..., max_length=64)
    assigned_mentor_user_id: UUID | None = None
    accommodation_reference: str | None = None
    campus_access_id: str | None = None
    special_requirements: str | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class InboundStudentUpdate(BaseModel):
    student_first_name: str | None = None
    student_last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    country_of_citizenship: str | None = None
    host_department_id: UUID | None = None
    host_academic_program_id: UUID | None = None
    expected_start_date: date | None = None
    expected_end_date: date | None = None
    assigned_mentor_user_id: UUID | None = None
    accommodation_reference: str | None = None
    campus_access_id: str | None = None
    status: InboundStudentStatus | None = None
    orientation_completed: bool | None = None
    check_in_date: date | None = None
    departure_date: date | None = None
    special_requirements: str | None = None
    metadata_json: dict[str, Any] | None = None


class InboundOrientationCheckinRequest(BaseModel):
    check_in_date: date = Field(default_factory=date.today)
    orientation_completed: bool = True
    orientation_notes: str | None = None


class InboundStudentResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    inbound_reference_number: str
    partner_id: UUID
    partner_name: str | None = None
    student_first_name: str
    student_last_name: str
    email: str
    phone: str | None = None
    country_of_citizenship: str
    home_institution_name: str
    home_program_of_study: str
    host_department_id: UUID | None = None
    host_department_name: str | None = None
    host_academic_program_id: UUID | None = None
    status: InboundStudentStatus
    expected_start_date: date
    expected_end_date: date
    study_period_terms: str
    assigned_mentor_user_id: UUID | None = None
    assigned_mentor_name: str | None = None
    accommodation_reference: str | None = None
    campus_access_id: str | None = None
    orientation_completed: bool = False
    check_in_date: date | None = None
    departure_date: date | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 6. FACULTY MOBILITY & VISITING SCHOLARS
# =============================================================================


class FacultyMobilityCreate(BaseModel):
    direction: FacultyMobilityDirection = FacultyMobilityDirection.OUTBOUND_FACULTY
    partner_id: UUID
    faculty_user_id: UUID | None = None
    visiting_scholar_name: str | None = Field(None, max_length=150)
    visiting_scholar_email: str | None = Field(None, max_length=255)
    visiting_scholar_designation: str | None = Field(None, max_length=150)
    home_institution_name: str | None = Field(None, max_length=255)
    host_institution_name: str | None = Field(None, max_length=255)
    department_id: UUID | None = None
    visit_start_date: date
    visit_end_date: date
    visit_objectives: str = Field(..., min_length=10)
    academic_visit_plan: dict[str, Any] = Field(default_factory=dict)
    lecture_topics: list[str] = Field(default_factory=list)
    research_collaboration_areas: list[str] = Field(default_factory=list)
    funding_source_notes: str | None = None
    campus_access_id: str | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class FacultyMobilityUpdate(BaseModel):
    visit_start_date: date | None = None
    visit_end_date: date | None = None
    visit_objectives: str | None = None
    academic_visit_plan: dict[str, Any] | None = None
    lecture_topics: list[str] | None = None
    research_collaboration_areas: list[str] | None = None
    funding_source_notes: str | None = None
    campus_access_id: str | None = None
    status: FacultyMobilityStatus | None = None
    completion_report_summary: str | None = None
    metadata_json: dict[str, Any] | None = None


class FacultyMobilityApprovalRequest(BaseModel):
    decision: str = Field(..., pattern="^(APPROVED|REJECTED)$")
    comments: str = Field(..., min_length=3)


class FacultyMobilityResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    mobility_reference_number: str
    direction: FacultyMobilityDirection
    partner_id: UUID
    partner_name: str | None = None
    faculty_user_id: UUID | None = None
    faculty_name: str | None = None
    visiting_scholar_name: str | None = None
    visiting_scholar_email: str | None = None
    visiting_scholar_designation: str | None = None
    home_institution_name: str | None = None
    host_institution_name: str | None = None
    department_id: UUID | None = None
    department_name: str | None = None
    status: FacultyMobilityStatus
    visit_start_date: date
    visit_end_date: date
    visit_objectives: str
    lecture_topics: list[str] = Field(default_factory=list)
    research_collaboration_areas: list[str] = Field(default_factory=list)
    hod_approved_by_user_id: UUID | None = None
    vp_approved_by_user_id: UUID | None = None
    completion_report_summary: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 7. ACADEMIC CREDIT EQUIVALENCY & TRANSFERS
# =============================================================================


class CourseEquivalencyCreate(BaseModel):
    partner_id: UUID
    host_course_code: str = Field(..., min_length=2, max_length=64)
    host_course_title: str = Field(..., min_length=2, max_length=255)
    host_course_credits: float = Field(..., gt=0.0)
    host_syllabus_reference: str | None = None
    host_grading_scale: str | None = None
    campus_academic_program_id: UUID | None = None
    campus_course_id: UUID | None = None
    campus_course_code: str | None = Field(None, max_length=64)
    campus_course_title: str | None = Field(None, max_length=255)
    campus_course_credits: float | None = Field(None, gt=0.0)
    department_id: UUID | None = None
    learning_outcomes_comparison: str | None = None
    valid_from: date = Field(default_factory=date.today)
    valid_until: date | None = None


class CourseEquivalencyEvaluationRequest(BaseModel):
    status: CreditEquivalencyStatus = Field(..., description="APPROVED, REJECTED, CONDITIONALLY_APPROVED")
    evaluator_comments: str = Field(..., min_length=3)
    conditions: str | None = None


class CourseEquivalencyResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    partner_id: UUID
    partner_name: str | None = None
    host_course_code: str
    host_course_title: str
    host_course_credits: float
    campus_course_code: str | None = None
    campus_course_title: str | None = None
    campus_course_credits: float | None = None
    department_id: UUID | None = None
    status: CreditEquivalencyStatus
    evaluated_by_user_id: UUID | None = None
    evaluator_name: str | None = None
    evaluator_comments: str | None = None
    conditions: str | None = None
    valid_from: date
    valid_until: date | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class CreditTransferRequestCreate(BaseModel):
    application_id: UUID
    host_course_code: str = Field(..., max_length=64)
    host_course_title: str = Field(..., max_length=255)
    host_grade_received: str = Field(..., max_length=32)
    host_credits_earned: float = Field(..., gt=0.0)
    equivalency_mapping_id: UUID | None = None
    target_campus_course_id: UUID | None = None
    target_campus_credits: float | None = Field(None, gt=0.0)
    transcript_document_url: str = Field(..., min_length=3)


class CreditTransferApprovalRequest(BaseModel):
    status: CreditTransferStatus = Field(..., description="COMMITTEE_APPROVED or REJECTED")
    committee_resolution_notes: str = Field(..., min_length=3)
    approved_credits: float | None = Field(None, ge=0.0)


class CreditTransferResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    application_id: UUID
    student_id: UUID
    student_name: str | None = None
    host_course_code: str
    host_course_title: str
    host_grade_received: str
    host_credits_earned: float
    target_campus_credits: float | None = None
    equivalency_mapping_id: UUID | None = None
    status: CreditTransferStatus
    transcript_document_url: str
    reviewed_by_user_id: UUID | None = None
    academic_committee_approved_by_user_id: UUID | None = None
    committee_resolution_notes: str | None = None
    credits_posted_to_transcript: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 8. MOBILITY DOCUMENTS
# =============================================================================


class MobilityDocumentCreate(BaseModel):
    application_id: UUID | None = None
    inbound_student_id: UUID | None = None
    faculty_mobility_id: UUID | None = None
    document_type: MobilityDocumentType
    document_name: str = Field(..., min_length=2, max_length=255)
    file_storage_url: str = Field(..., min_length=3)
    file_mime_type: str | None = Field(None, max_length=100)
    file_size_bytes: int | None = None
    document_expiry_date: date | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class MobilityDocumentVerifyRequest(BaseModel):
    status: MobilityDocumentVerificationStatus = Field(..., description="VERIFIED, REJECTED, EXPIRED")
    rejection_reason: str | None = None


class MobilityDocumentResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    application_id: UUID | None = None
    inbound_student_id: UUID | None = None
    faculty_mobility_id: UUID | None = None
    document_type: MobilityDocumentType
    document_name: str
    file_storage_url: str
    file_mime_type: str | None = None
    file_size_bytes: int | None = None
    document_expiry_date: date | None = None
    verification_status: MobilityDocumentVerificationStatus
    verified_by_user_id: UUID | None = None
    verified_at: datetime | None = None
    rejection_reason: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 9. SCHOLARSHIPS & MOBILITY FUNDING
# =============================================================================


class MobilityScholarshipCreate(BaseModel):
    scholarship_name: str = Field(..., min_length=3, max_length=255)
    scholarship_code: str | None = Field(None, max_length=64)
    funding_source: str = Field(..., max_length=150)
    sponsor_name: str | None = Field(None, max_length=150)
    award_amount_per_student: float = Field(..., gt=0.0)
    total_available_slots: int = Field(5, ge=1)
    application_deadline: date | None = None
    eligibility_criteria_notes: str | None = None
    is_active: bool = True
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class MobilityScholarshipUpdate(BaseModel):
    scholarship_name: str | None = None
    funding_source: str | None = None
    sponsor_name: str | None = None
    award_amount_per_student: float | None = None
    total_available_slots: int | None = None
    application_deadline: date | None = None
    eligibility_criteria_notes: str | None = None
    is_active: bool | None = None
    metadata_json: dict[str, Any] | None = None


class MobilityScholarshipResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    scholarship_name: str
    scholarship_code: str
    funding_source: str
    sponsor_name: str | None = None
    award_amount_per_student: float
    total_available_slots: int
    awarded_count: int = 0
    application_deadline: date | None = None
    eligibility_criteria_notes: str | None = None
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class MobilityFundingRequestCreate(BaseModel):
    application_id: UUID
    scholarship_id: UUID | None = None
    requested_amount: float = Field(..., gt=0.0)
    justification: str = Field(..., min_length=10)
    supporting_document_url: str | None = None


class MobilityFundingApprovalRequest(BaseModel):
    status: MobilityFundingStatus = Field(..., description="APPROVED, REJECTED")
    approved_amount: float | None = Field(None, ge=0.0)
    review_comments: str = Field(..., min_length=3)
    finance_reference_id: UUID | None = None


class MobilityFundingRequestResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    application_id: UUID
    student_id: UUID
    student_name: str | None = None
    scholarship_id: UUID | None = None
    scholarship_name: str | None = None
    requested_amount: float
    approved_amount: float | None = None
    status: MobilityFundingStatus
    award_status: ScholarshipAwardStatus
    justification: str
    supporting_document_url: str | None = None
    review_comments: str | None = None
    finance_reference_id: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 10. POLICY CONFIG & DASHBOARD METRICS
# =============================================================================


class InternationalPolicyConfigBase(BaseModel):
    agreement_warning_days: int = 90
    min_student_cgpa_default: float = 6.0
    min_student_credits_completed_default: int = 30
    require_department_approval_first: bool = True
    require_vp_approval_for_faculty: bool = True
    max_active_applications_per_student: int = 2
    credit_transfer_requires_academic_council: bool = True
    inbound_orientation_mandatory: bool = True
    notification_settings: dict[str, Any] = Field(default_factory=dict)
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class InternationalPolicyConfigCreateOrUpdate(InternationalPolicyConfigBase):
    pass


class InternationalPolicyConfigResponse(InternationalPolicyConfigBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class InternationalDashboardMetrics(BaseModel):
    total_active_partners: int = 0
    total_active_agreements: int = 0
    agreements_expiring_soon: int = 0
    total_published_programs: int = 0
    total_active_applications: int = 0
    pending_department_reviews: int = 0
    pending_international_office_reviews: int = 0
    pending_partner_nominations: int = 0
    active_inbound_students: int = 0
    active_outbound_students: int = 0
    active_faculty_mobilities: int = 0
    pending_credit_transfers: int = 0
    pending_funding_requests: int = 0
