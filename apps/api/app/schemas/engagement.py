"""Pydantic Request & Response Schemas for Enterprise Student Engagement,
Community Service, Volunteering & Civic Impact Management (Step 65).
"""

from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.engagement import (
    AttendanceVerificationMethod,
    PartnerOrgType,
    ProgramCategory,
    ProgramDeliveryMode,
)

# =============================================================================
# 1. COMMUNITY PARTNER SCHEMAS
# =============================================================================


class CommunityPartnerCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    organization_type: str = Field(default=PartnerOrgType.NON_PROFIT)
    registration_number: str | None = None
    website: str | None = None
    primary_contact_name: str = Field(..., min_length=2, max_length=255)
    primary_contact_email: str = Field(..., max_length=255)
    primary_contact_phone: str | None = None
    authorized_representative_name: str | None = None
    authorized_representative_title: str | None = None
    authorized_representative_email: str | None = None
    partnership_purpose: str | None = None
    engagement_categories: list[str] = Field(default_factory=list)
    agreement_reference: str | None = None
    mou_document_id: UUID | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    review_date: date | None = None
    coordinator_user_id: UUID | None = None


class CommunityPartnerUpdate(BaseModel):
    name: str | None = None
    organization_type: str | None = None
    registration_number: str | None = None
    website: str | None = None
    primary_contact_name: str | None = None
    primary_contact_email: str | None = None
    primary_contact_phone: str | None = None
    authorized_representative_name: str | None = None
    authorized_representative_title: str | None = None
    authorized_representative_email: str | None = None
    status: str | None = None
    partnership_purpose: str | None = None
    engagement_categories: list[str] | None = None
    agreement_reference: str | None = None
    mou_document_id: UUID | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    review_date: date | None = None
    coordinator_user_id: UUID | None = None


class CommunityPartnerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    organization_type: str
    registration_number: str | None = None
    website: str | None = None
    primary_contact_name: str
    primary_contact_email: str
    primary_contact_phone: str | None = None
    authorized_representative_name: str | None = None
    authorized_representative_title: str | None = None
    authorized_representative_email: str | None = None
    status: str
    partnership_purpose: str | None = None
    engagement_categories: list[str]
    agreement_reference: str | None = None
    mou_document_id: UUID | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    review_date: date | None = None
    coordinator_user_id: UUID | None = None
    impact_summary_json: dict = Field(default_factory=dict)
    verified_hours_contributed: Decimal
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 2. ENGAGEMENT PROGRAM SCHEMAS
# =============================================================================


class EngagementProgramCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=64)
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=255)
    description: str | None = None
    category: str = Field(default=ProgramCategory.COMMUNITY_SERVICE)
    objectives: str | None = None
    campus_id: UUID | None = None
    department_id: UUID | None = None
    coordinator_id: UUID
    community_partner_id: UUID | None = None
    target_audience: str | None = None
    student_eligibility_criteria: dict = Field(default_factory=dict)
    start_date: date
    end_date: date
    registration_deadline: date | None = None
    capacity: int = Field(default=50, ge=1)
    target_service_hours: Decimal = Field(default=Decimal("20.00"), ge=0)
    skills_required: list[str] = Field(default_factory=list)
    prerequisites: str | None = None
    accessibility_considerations: str | None = None
    delivery_mode: str = Field(default=ProgramDeliveryMode.ON_CAMPUS)
    location_name: str | None = None
    location_address: str | None = None
    expected_outcomes: str | None = None
    sdg_goals: list[str] = Field(default_factory=list)
    safety_requirements_json: dict = Field(default_factory=dict)
    consent_required: bool = False


class EngagementProgramUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    objectives: str | None = None
    campus_id: UUID | None = None
    department_id: UUID | None = None
    coordinator_id: UUID | None = None
    community_partner_id: UUID | None = None
    target_audience: str | None = None
    student_eligibility_criteria: dict | None = None
    start_date: date | None = None
    end_date: date | None = None
    registration_deadline: date | None = None
    capacity: int | None = None
    target_service_hours: Decimal | None = None
    skills_required: list[str] | None = None
    prerequisites: str | None = None
    accessibility_considerations: str | None = None
    delivery_mode: str | None = None
    location_name: str | None = None
    location_address: str | None = None
    expected_outcomes: str | None = None
    sdg_goals: list[str] | None = None
    safety_requirements_json: dict | None = None
    consent_required: bool | None = None


class EngagementProgramTransitionRequest(BaseModel):
    target_status: str
    approval_notes: str | None = None


class EngagementProgramResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    code: str
    name: str
    slug: str
    description: str | None = None
    category: str
    objectives: str | None = None
    campus_id: UUID | None = None
    department_id: UUID | None = None
    coordinator_id: UUID
    community_partner_id: UUID | None = None
    target_audience: str | None = None
    student_eligibility_criteria: dict
    start_date: date
    end_date: date
    registration_deadline: date | None = None
    status: str
    capacity: int
    target_service_hours: Decimal
    skills_required: list[str]
    prerequisites: str | None = None
    accessibility_considerations: str | None = None
    delivery_mode: str
    location_name: str | None = None
    location_address: str | None = None
    approver_id: UUID | None = None
    approved_at: datetime | None = None
    approval_notes: str | None = None
    expected_outcomes: str | None = None
    sdg_goals: list[str]
    safety_requirements_json: dict
    consent_required: bool
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 3. VOLUNTEER OPPORTUNITY SCHEMAS
# =============================================================================


class VolunteerOpportunityCreate(BaseModel):
    program_id: UUID
    title: str = Field(..., min_length=2, max_length=255)
    description: str | None = None
    category: str = Field(default=ProgramCategory.COMMUNITY_SERVICE)
    required_skills: list[str] = Field(default_factory=list)
    eligibility_criteria: dict = Field(default_factory=dict)
    available_positions: int = Field(default=20, ge=1)
    capacity: int = Field(default=20, ge=1)
    waitlist_capacity: int = Field(default=10, ge=0)
    application_deadline: date | None = None
    start_date: date
    end_date: date
    start_time: time | None = None
    end_time: time | None = None
    location: str | None = None
    delivery_mode: str = Field(default=ProgramDeliveryMode.ON_CAMPUS)
    expected_hours: Decimal = Field(default=Decimal("10.00"), ge=0)
    shifts_count: int = Field(default=1, ge=1)
    prerequisites: str | None = None
    safety_guidance: str | None = None
    coordinator_id: UUID | None = None
    partner_id: UUID | None = None


class VolunteerOpportunityUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    category: str | None = None
    required_skills: list[str] | None = None
    eligibility_criteria: dict | None = None
    available_positions: int | None = None
    capacity: int | None = None
    waitlist_capacity: int | None = None
    application_deadline: date | None = None
    start_date: date | None = None
    end_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    location: str | None = None
    delivery_mode: str | None = None
    expected_hours: Decimal | None = None
    shifts_count: int | None = None
    status: str | None = None
    prerequisites: str | None = None
    safety_guidance: str | None = None
    coordinator_id: UUID | None = None
    partner_id: UUID | None = None


class VolunteerOpportunityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    program_id: UUID
    title: str
    description: str | None = None
    category: str
    required_skills: list[str]
    eligibility_criteria: dict
    available_positions: int
    capacity: int
    waitlist_capacity: int
    application_deadline: date | None = None
    start_date: date
    end_date: date
    start_time: time | None = None
    end_time: time | None = None
    location: str | None = None
    delivery_mode: str
    expected_hours: Decimal
    shifts_count: int
    status: str
    prerequisites: str | None = None
    safety_guidance: str | None = None
    coordinator_id: UUID | None = None
    partner_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 4. PARTICIPATION APPLICATION SCHEMAS
# =============================================================================


class ParticipationApplicationCreate(BaseModel):
    opportunity_id: UUID
    statement_of_purpose: str | None = None
    skills_declared: list[str] = Field(default_factory=list)
    consent_confirmed: bool = True
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None


class ParticipationApplicationReviewRequest(BaseModel):
    status: str = Field(..., description="APPROVED, WAITLISTED, or REJECTED")
    reviewer_notes: str | None = None
    rejection_reason: str | None = None


class ParticipationApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    opportunity_id: UUID
    program_id: UUID
    student_id: UUID
    status: str
    applied_at: datetime
    reviewed_at: datetime | None = None
    reviewer_id: UUID | None = None
    reviewer_notes: str | None = None
    rejection_reason: str | None = None
    waitlist_position: int | None = None
    statement_of_purpose: str | None = None
    skills_declared: list[str]
    consent_confirmed: bool
    consent_signed_at: datetime | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 5. VOLUNTEER SHIFTS & ASSIGNMENTS SCHEMAS
# =============================================================================


class VolunteerShiftCreate(BaseModel):
    opportunity_id: UUID
    title: str = Field(..., min_length=2, max_length=255)
    shift_date: date
    start_time: time
    end_time: time
    capacity: int = Field(default=10, ge=1)
    location: str | None = None
    supervisor_id: UUID | None = None


class VolunteerShiftUpdate(BaseModel):
    title: str | None = None
    shift_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    capacity: int | None = None
    location: str | None = None
    supervisor_id: UUID | None = None
    status: str | None = None


class ShiftAssignmentCreate(BaseModel):
    shift_id: UUID
    application_id: UUID
    student_id: UUID


class ShiftAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    shift_id: UUID
    application_id: UUID
    student_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime


class VolunteerShiftResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    opportunity_id: UUID
    program_id: UUID
    title: str
    shift_date: date
    start_time: time
    end_time: time
    capacity: int
    assigned_count: int
    location: str | None = None
    supervisor_id: UUID | None = None
    status: str
    created_at: datetime
    updated_at: datetime
    assignments: list[ShiftAssignmentResponse] = Field(default_factory=list)


# =============================================================================
# 6. ATTENDANCE SCHEMAS
# =============================================================================


class AttendanceCheckInRequest(BaseModel):
    opportunity_id: UUID
    student_id: UUID
    shift_id: UUID | None = None
    check_in_at: datetime | None = None
    verification_method: str = Field(default=AttendanceVerificationMethod.COORDINATOR_CONFIRMED)
    notes: str | None = None


class AttendanceCheckOutRequest(BaseModel):
    check_out_at: datetime | None = None
    notes: str | None = None


class ParticipationAttendanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    shift_id: UUID | None = None
    opportunity_id: UUID
    program_id: UUID
    student_id: UUID
    check_in_at: datetime
    check_out_at: datetime | None = None
    verification_method: str
    verified_by_user_id: UUID | None = None
    status: str
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 7. SERVICE HOUR SCHEMAS
# =============================================================================


class ServiceHourSubmitRequest(BaseModel):
    program_id: UUID
    opportunity_id: UUID | None = None
    shift_id: UUID | None = None
    attendance_id: UUID | None = None
    service_date: date
    duration_hours: Decimal = Field(..., gt=0, le=24)
    description_of_work: str = Field(..., min_length=5)


class ServiceHourVerifyRequest(BaseModel):
    status: str = Field(..., description="APPROVED or REJECTED or CORRECTION_REQUESTED")
    supervisor_comments: str | None = None


class ServiceHourCorrectionRequest(BaseModel):
    new_hours: Decimal = Field(..., gt=0, le=24)
    reason_for_change: str = Field(..., min_length=3)


class ServiceHourCorrectionHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    service_hour_id: UUID
    previous_hours: Decimal
    new_hours: Decimal
    reason_for_change: str
    changed_by_user_id: UUID
    changed_at: datetime


class ServiceHourResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    program_id: UUID
    opportunity_id: UUID | None = None
    shift_id: UUID | None = None
    attendance_id: UUID | None = None
    student_id: UUID
    service_date: date
    duration_hours: Decimal
    description_of_work: str
    status: str
    is_verified: bool
    submitted_at: datetime
    verified_by_id: UUID | None = None
    verified_at: datetime | None = None
    supervisor_comments: str | None = None
    created_at: datetime
    updated_at: datetime
    corrections: list[ServiceHourCorrectionHistoryResponse] = Field(default_factory=list)


# =============================================================================
# 8. REFLECTIONS & OUTCOMES SCHEMAS
# =============================================================================


class ReflectionSubmitRequest(BaseModel):
    program_id: UUID
    opportunity_id: UUID | None = None
    reflection_text: str = Field(..., min_length=10)
    learning_outcomes_summary: str | None = None
    skills_developed: list[str] = Field(default_factory=list)
    community_outcomes: str | None = None
    deliverables_description: str | None = None
    sdg_impact_mapping: list[str] = Field(default_factory=list)
    attachment_document_ids: list[str] = Field(default_factory=list)
    consent_for_impact_showcase: bool = False


class ReflectionReviewRequest(BaseModel):
    status: str = Field(..., description="APPROVED or REVISION_REQUESTED")
    feedback_text: str | None = None
    rating: int | None = Field(default=None, ge=1, le=5)


class ReflectionSubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    program_id: UUID
    opportunity_id: UUID | None = None
    student_id: UUID
    reflection_text: str
    learning_outcomes_summary: str | None = None
    skills_developed: list[str]
    community_outcomes: str | None = None
    deliverables_description: str | None = None
    sdg_impact_mapping: list[str]
    attachment_document_ids: list[str]
    consent_for_impact_showcase: bool
    status: str
    reviewer_id: UUID | None = None
    reviewed_at: datetime | None = None
    feedback_text: str | None = None
    rating: int | None = None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 9. SAFETY & CONSENT SCHEMAS
# =============================================================================


class SafetyAcknowledgeRequest(BaseModel):
    program_id: UUID
    safety_briefing_acknowledged: bool = True
    risk_assessment_acknowledged: bool = True
    emergency_contact_verified: bool = True
    parental_consent_received: bool = False


class SafetyClearanceRequest(BaseModel):
    clearance_status: str = Field(..., description="CLEARED or BLOCKED")
    incident_reference_id: str | None = None


class SafetyAndConsentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    program_id: UUID
    student_id: UUID
    safety_briefing_acknowledged: bool
    safety_acknowledged_at: datetime | None = None
    parental_consent_required: bool
    parental_consent_received: bool
    risk_assessment_acknowledged: bool
    emergency_contact_verified: bool
    incident_reference_id: str | None = None
    coordinator_clearance_status: str
    coordinator_id: UUID | None = None
    cleared_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 10. CERTIFICATE SCHEMAS
# =============================================================================


class EngagementCertificateIssueRequest(BaseModel):
    program_id: UUID
    student_id: UUID
    issuing_authority_name: str = Field(default="Director of Student Affairs & Civic Engagement")


class EngagementCertificateRevokeRequest(BaseModel):
    revocation_reason: str = Field(..., min_length=5)


class EngagementCertificateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    certificate_number: str
    program_id: UUID
    student_id: UUID
    recipient_name: str
    recipient_roll_number: str
    recipient_department: str
    total_verified_hours: Decimal
    service_category: str
    program_name: str
    skills_certified: list[str]
    issue_date: datetime
    issuing_authority_name: str
    issued_by_user_id: UUID
    verification_hash: str
    qr_verification_url: str
    status: str
    revocation_reason: str | None = None
    revoked_at: datetime | None = None
    revoked_by_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 11. DASHBOARD & ANALYTICS SCHEMAS
# =============================================================================


class EngagementDashboardResponse(BaseModel):
    total_programs: int
    active_programs: int
    completed_programs: int
    total_opportunities: int
    active_opportunities: int
    total_applications: int
    pending_applications: int
    approved_participants: int
    waitlisted_participants: int
    total_submitted_hours: Decimal
    total_verified_hours: Decimal
    pending_verification_hours: Decimal
    total_reflections_submitted: int
    approved_reflections: int
    certificates_issued: int
    active_partners: int
    sdg_distribution: dict[str, int] = Field(default_factory=dict)
    category_distribution: dict[str, int] = Field(default_factory=dict)

