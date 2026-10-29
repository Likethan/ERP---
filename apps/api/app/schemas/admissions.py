"""Pydantic v2 Schemas for CampusOS Student Admissions, Enrollment & Onboarding Orchestration (Step 48)."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.admissions import (
    AdmissionCycleStatus,
    ApplicantVerificationStatus,
    ApplicationStatus,
    DocumentVerificationStatus,
    OnboardingStatus,
    OnboardingTaskCategory,
    ReviewDecision,
    ReviewStage,
)

# =============================================================================
# 1. ADMISSION CYCLES
# =============================================================================


class AdmissionCycleCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    academic_year_id: UUID
    code: str = Field(..., max_length=32, description="Cycle code e.g. AY2026-UG-FALL")
    name: str = Field(..., max_length=128)
    admission_term: str = Field("FALL", max_length=32)
    application_start_date: date
    application_end_date: date
    document_deadline: date
    offer_acceptance_deadline: date
    publication_date: date | None = None
    settings: dict[str, Any] | None = None


class AdmissionCycleUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str | None = None
    status: AdmissionCycleStatus | None = None
    application_start_date: date | None = None
    application_end_date: date | None = None
    document_deadline: date | None = None
    offer_acceptance_deadline: date | None = None
    publication_date: date | None = None
    is_active: bool | None = None
    settings: dict[str, Any] | None = None


class AdmissionCycleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    academic_year_id: UUID
    code: str
    name: str
    admission_term: str
    status: str
    application_start_date: date
    application_end_date: date
    document_deadline: date
    offer_acceptance_deadline: date
    publication_date: date | None
    is_active: bool
    settings: dict[str, Any] | None
    total_applications_count: int
    total_enrolled_count: int
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 2. APPLICANT PROFILES
# =============================================================================


class ApplicantProfileCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    email: EmailStr
    phone_number: str = Field(..., max_length=32)
    date_of_birth: date
    gender: str = Field(..., max_length=16)  # MALE, FEMALE, OTHER
    nationality: str = Field("Indian", max_length=64)
    address_line1: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str = Field("India", max_length=100)
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    user_id: UUID | None = None


class ApplicantProfileUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    first_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None
    address_line1: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    verification_status: ApplicantVerificationStatus | None = None


class ApplicantMergeRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    target_applicant_id: UUID
    merge_reason: str = Field(..., min_length=5, description="Reason for merging duplicate applicant")


class ApplicantProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    applicant_number: str
    user_id: UUID | None
    first_name: str
    last_name: str
    email: str
    phone_number: str
    date_of_birth: date
    gender: str
    nationality: str
    address_line1: str | None
    city: str | None
    state: str | None
    postal_code: str | None
    country: str
    emergency_contact_name: str | None
    emergency_contact_phone: str | None
    verification_status: str
    is_duplicate: bool
    merged_into_applicant_id: UUID | None
    merge_reason: str | None
    merged_at: datetime | None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 3. APPLICATIONS & PROGRAM CHOICES
# =============================================================================


class ApplicationProgramChoiceCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    program_id: UUID
    preference_rank: int = Field(..., ge=1, le=10)
    campus_id: UUID | None = None


class ApplicationProgramChoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    application_id: UUID
    program_id: UUID
    campus_id: UUID | None
    preference_rank: int
    is_active: bool
    created_at: datetime


class AdmissionApplicationCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cycle_id: UUID
    applicant_id: UUID
    program_id: UUID
    campus_id: UUID | None = None
    admission_category: str = Field("GENERAL", max_length=32)
    qualifying_exam_name: str | None = None
    qualifying_exam_score: Decimal | None = None
    qualifying_exam_max_score: Decimal | None = None
    qualifying_percentage: Decimal | None = None
    program_choices: list[ApplicationProgramChoiceCreate] | None = None
    notes: str | None = None


class AdmissionApplicationUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    campus_id: UUID | None = None
    admission_category: str | None = None
    qualifying_exam_name: str | None = None
    qualifying_exam_score: Decimal | None = None
    qualifying_exam_max_score: Decimal | None = None
    qualifying_percentage: Decimal | None = None
    notes: str | None = None


class ApplicationStatusTransition(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    to_status: ApplicationStatus
    notes: str | None = None


class ApplicationWithdrawRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    withdrawal_reason: str = Field(..., min_length=3)


class ApplicationReopenRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    reopening_reason: str = Field(..., min_length=5)
    correction_window_hours: int = Field(48, ge=1, le=168)


class AdmissionApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    cycle_id: UUID
    applicant_id: UUID
    application_number: str
    program_id: UUID
    campus_id: UUID | None
    admission_category: str
    status: str
    submitted_at: datetime | None
    correction_window_end: datetime | None
    qualifying_exam_name: str | None
    qualifying_exam_score: Decimal | None
    qualifying_exam_max_score: Decimal | None
    qualifying_percentage: Decimal | None
    application_fee_paid: bool
    payment_reference: str | None
    withdrawal_reason: str | None
    reopened_at: datetime | None
    reopening_reason: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 4. DOCUMENTS & VERIFICATION
# =============================================================================


class ApplicationDocumentRequirementCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cycle_id: UUID | None = None
    program_id: UUID | None = None
    document_name: str = Field(..., max_length=128)
    document_code: str = Field(..., max_length=64)
    is_mandatory: bool = True
    description: str | None = None


class ApplicationDocumentRequirementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    cycle_id: UUID | None
    program_id: UUID | None
    document_name: str
    document_code: str
    is_mandatory: bool
    description: str | None
    is_active: bool
    created_at: datetime


class ApplicationDocumentUpload(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    requirement_id: UUID | None = None
    document_name: str = Field(..., max_length=128)
    file_name: str = Field(..., max_length=255)
    file_size_bytes: int = Field(0, ge=0)
    mime_type: str = Field("application/pdf", max_length=128)
    storage_key: str = Field(..., max_length=255)


class ApplicationDocumentVerify(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    verification_status: DocumentVerificationStatus
    rejection_reason: str | None = None


class ApplicationDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    application_id: UUID
    requirement_id: UUID | None
    document_name: str
    file_name: str
    file_size_bytes: int
    mime_type: str
    storage_key: str
    verification_status: str
    rejection_reason: str | None
    verified_by_user_id: UUID | None
    verified_at: datetime | None
    created_at: datetime


# =============================================================================
# 5. ELIGIBILITY & REVIEWS
# =============================================================================


class EligibilityRuleCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cycle_id: UUID | None = None
    program_id: UUID | None = None
    code: str = Field(..., max_length=64)
    name: str = Field(..., max_length=128)
    min_score_percentage: Decimal = Field(Decimal("50.00"), ge=0, le=100)
    required_qualification: str | None = None
    criteria_json: dict[str, Any] | None = None


class EligibilityRuleUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str | None = None
    min_score_percentage: Decimal | None = None
    required_qualification: str | None = None
    is_active: bool | None = None
    criteria_json: dict[str, Any] | None = None


class EligibilityRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    cycle_id: UUID | None
    program_id: UUID | None
    code: str
    name: str
    min_score_percentage: Decimal
    required_qualification: str | None
    rule_version: int
    is_active: bool
    criteria_json: dict[str, Any] | None
    created_at: datetime


class EligibilityEvaluationRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rule_id: UUID


class EligibilityEvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    application_id: UUID
    rule_id: UUID
    rule_version: int
    is_eligible: bool
    observed_percentage: Decimal | None
    evaluation_summary: str | None
    evaluated_at: datetime
    evaluated_by_user_id: UUID | None


class ApplicationReviewCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    reviewer_user_id: UUID
    review_stage: ReviewStage = ReviewStage.ACADEMIC_REVIEW
    score: Decimal | None = None
    decision: ReviewDecision = ReviewDecision.PENDING
    decision_reason: str | None = None
    reviewer_notes: str | None = None
    is_completed: bool = False


class ApplicationReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    application_id: UUID
    reviewer_user_id: UUID
    review_stage: str
    score: Decimal | None
    decision: str
    decision_reason: str | None
    reviewer_notes: str | None
    reviewed_at: datetime | None
    is_completed: bool
    created_at: datetime


# =============================================================================
# 6. SEAT ALLOCATION & SELECTION
# =============================================================================


class SeatAllocationCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cycle_id: UUID
    program_id: UUID
    campus_id: UUID | None = None
    admission_category: str = Field("GENERAL", max_length=32)
    total_capacity: int = Field(60, ge=1)
    waitlist_capacity: int = Field(30, ge=0)


class SeatAllocationUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_capacity: int | None = None
    waitlist_capacity: int | None = None


class SeatAllocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    cycle_id: UUID
    program_id: UUID
    campus_id: UUID | None
    admission_category: str
    total_capacity: int
    reserved_seats: int
    confirmed_seats: int
    waitlist_capacity: int
    available_seats: int = 0
    created_at: datetime


class SelectionRunCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cycle_id: UUID
    program_id: UUID
    name: str = Field(..., max_length=128)
    cutoff_score: Decimal | None = None


class SelectionRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    cycle_id: UUID
    program_id: UUID
    run_number: int
    name: str
    cutoff_score: Decimal | None
    total_selected: int
    total_waitlisted: int
    is_approved: bool
    approved_by_user_id: UUID | None
    approved_at: datetime | None
    is_published: bool
    published_at: datetime | None
    created_at: datetime


class SelectionResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    selection_run_id: UUID
    application_id: UUID
    applicant_id: UUID
    merit_rank: int
    merit_score: Decimal
    status: str
    waitlist_rank: int | None
    seat_offered: bool
    created_at: datetime


# =============================================================================
# 7. ADMISSION OFFERS
# =============================================================================


class AdmissionOfferCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    application_id: UUID
    expiry_date: date
    deposit_required: Decimal = Field(Decimal("0.00"), ge=0)
    conditions_text: str | None = None


class AdmissionOfferRespond(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    accept: bool
    decline_reason: str | None = None


class AdmissionOfferRevoke(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    revocation_reason: str = Field(..., min_length=5)


class AdmissionOfferResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    application_id: UUID
    applicant_id: UUID
    program_id: UUID
    cycle_id: UUID
    offer_number: str
    offer_date: date
    expiry_date: date
    deposit_required: Decimal
    conditions_text: str | None
    status: str
    response_date: datetime | None
    decline_reason: str | None
    revocation_reason: str | None
    created_at: datetime


# =============================================================================
# 8. ENROLLMENT WORKFLOW
# =============================================================================


class EnrollmentWorkflowInitiate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    application_id: UUID
    offer_id: UUID
    batch_id: UUID
    current_semester_id: UUID | None = None
    current_section_id: UUID | None = None
    idempotency_key: str = Field(..., max_length=128)
    deposit_payment_reference: str | None = None


class EnrollmentWorkflowRetry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    notes: str | None = None


class EnrollmentWorkflowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    application_id: UUID
    offer_id: UUID
    applicant_id: UUID
    student_id: UUID | None
    workflow_number: str
    batch_id: UUID
    current_semester_id: UUID | None
    current_section_id: UUID | None
    status: str
    idempotency_key: str
    failure_stage: str | None
    failure_reason: str | None
    retry_count: int
    created_student_admission_number: str | None
    completed_at: datetime | None
    created_at: datetime


# =============================================================================
# 9. ONBOARDING CHECKLIST & TASKS
# =============================================================================


class OnboardingTaskCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str = Field(..., max_length=128)
    task_category: OnboardingTaskCategory = OnboardingTaskCategory.ADMINISTRATIVE
    description: str | None = None
    is_mandatory: bool = True
    due_date: date | None = None


class OnboardingTaskUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: OnboardingStatus
    verification_notes: str | None = None


class OnboardingTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    checklist_id: UUID
    title: str
    task_category: str
    description: str | None
    is_mandatory: bool
    due_date: date | None
    status: str
    completed_at: datetime | None
    verified_by_user_id: UUID | None
    verification_notes: str | None
    created_at: datetime


class OnboardingChecklistResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    student_id: UUID
    enrollment_workflow_id: UUID | None
    title: str
    status: str
    total_tasks: int
    completed_tasks: int
    target_completion_date: date | None
    completed_at: datetime | None
    tasks: list[OnboardingTaskResponse] = []
    created_at: datetime


# =============================================================================
# 10. DETAIL & ANALYTICS RESPONSES
# =============================================================================


class AdmissionApplicationDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    application: AdmissionApplicationResponse
    applicant: ApplicantProfileResponse
    program_choices: list[ApplicationProgramChoiceResponse] = []
    documents: list[ApplicationDocumentResponse] = []
    reviews: list[ApplicationReviewResponse] = []
    offers: list[AdmissionOfferResponse] = []


class AdmissionsAnalyticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_applicants: int
    total_applications: int
    submitted_applications: int
    under_review_applications: int
    eligible_applications: int
    offered_applications: int
    accepted_offers: int
    enrolled_students: int
    conversion_rate_percentage: Decimal
    seat_utilization_percentage: Decimal
    missing_documents_count: int
