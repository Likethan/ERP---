"""Placement and Career Engine Pydantic request and response schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# --- Company & Contacts ---
class CompanyContactBase(BaseModel):
    name: str = Field(..., max_length=128)
    email: str = Field(..., max_length=255)
    phone: str | None = Field(None, max_length=32)
    designation: str | None = Field(None, max_length=128)
    is_primary: bool = False
    status: str = "ACTIVE"


class CompanyContactCreate(CompanyContactBase):
    pass


class CompanyContactResponse(CompanyContactBase):
    id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompanyBase(BaseModel):
    name: str = Field(..., max_length=255)
    legal_name: str | None = Field(None, max_length=255)
    industry: str = Field(..., max_length=128)
    company_type: str = Field("PRODUCT", max_length=64)  # PRODUCT, SERVICE, STARTUP, MNC, PSU, GOVT
    tier: str = Field("TIER_1", max_length=32)  # DREAM, SUPER_DREAM, TIER_1, TIER_2, MASS
    website: str | None = Field(None, max_length=255)
    description: str | None = None
    headquarters_location: str | None = Field(None, max_length=255)
    status: str = Field("ACTIVE", max_length=32)  # PROSPECT, ACTIVE, INACTIVE, BLACKLISTED, ARCHIVED


class CompanyCreate(CompanyBase):
    contacts: list[CompanyContactCreate] | None = None


class CompanyUpdate(BaseModel):
    name: str | None = None
    legal_name: str | None = None
    industry: str | None = None
    company_type: str | None = None
    tier: str | None = None
    website: str | None = None
    description: str | None = None
    headquarters_location: str | None = None
    status: str | None = None


class CompanyResponse(CompanyBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompanyDetailResponse(CompanyResponse):
    contacts: list[CompanyContactResponse] = []


# --- Eligibility Rules ---
class EligibilityRuleBase(BaseModel):
    rule_type: str = Field(..., max_length=64)
    # CGPA_MINIMUM, CGPA_MAXIMUM, BACKLOG_MAXIMUM, BACKLOG_NONE, ATTENDANCE_MINIMUM,
    # PROGRAM_ALLOWED, PROGRAM_EXCLUDED, DEPARTMENT_ALLOWED, DEPARTMENT_EXCLUDED,
    # GRADUATION_YEAR, SEMESTER_STATUS, FEE_CLEARANCE, CUSTOM_INSTITUTION_RULE
    operator: str = Field("GTE", max_length=16)  # GTE, LTE, EQ, NEQ, IN, NOT_IN
    value_json: Any
    metadata_json: Any | None = None
    is_required: bool = True
    sequence: int = 1


class EligibilityRuleCreate(EligibilityRuleBase):
    pass


class EligibilityRuleResponse(EligibilityRuleBase):
    id: UUID
    job_position_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Job Position ---
class JobPositionBase(BaseModel):
    title: str = Field(..., max_length=128)
    description: str | None = None
    employment_type: str = Field("FULL_TIME", max_length=32)  # FULL_TIME, PART_TIME, INTERNSHIP, INTERNSHIP_TO_FULL_TIME
    work_location: str | None = Field(None, max_length=128)
    vacancy_count: int = Field(1, ge=1)
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    currency: str = Field("INR", max_length=3)
    ctc: Decimal = Field(..., ge=0)
    skills_json: list[str] | None = None
    qualification: str | None = Field(None, max_length=255)
    experience_requirement: str | None = Field(None, max_length=128)
    joining_date: date | None = None
    status: str = Field("OPEN", max_length=32)  # OPEN, CLOSED, ON_HOLD, CANCELLED


class JobPositionCreate(JobPositionBase):
    eligibility_rules: list[EligibilityRuleCreate] | None = None


class JobPositionUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    employment_type: str | None = None
    work_location: str | None = None
    vacancy_count: int | None = None
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    currency: str | None = None
    ctc: Decimal | None = None
    skills_json: list[str] | None = None
    qualification: str | None = None
    experience_requirement: str | None = None
    joining_date: date | None = None
    status: str | None = None


class JobPositionResponse(JobPositionBase):
    id: UUID
    job_drive_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobPositionDetailResponse(JobPositionResponse):
    eligibility_rules: list[EligibilityRuleResponse] = []


# --- Recruitment Drives ---
class JobDriveBase(BaseModel):
    company_id: UUID
    academic_year_id: UUID
    title: str = Field(..., max_length=255)
    description: str | None = None
    application_open_at: datetime
    application_close_at: datetime
    drive_date: date
    location: str | None = Field(None, max_length=255)
    mode: str = Field("ON_CAMPUS", max_length=32)  # ON_CAMPUS, OFF_CAMPUS, VIRTUAL, HYBRID
    status: str = Field("DRAFT", max_length=32)  # DRAFT, PUBLISHED, APPLICATIONS_OPEN, APPLICATIONS_CLOSED, SHORTLISTING, INTERVIEWING, OFFERS, CLOSED, CANCELLED


class JobDriveCreate(JobDriveBase):
    positions: list[JobPositionCreate] | None = None


class JobDriveUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    application_open_at: datetime | None = None
    application_close_at: datetime | None = None
    drive_date: date | None = None
    location: str | None = None
    mode: str | None = None
    status: str | None = None


class JobDriveResponse(JobDriveBase):
    id: UUID
    tenant_id: UUID
    drive_code: str
    created_by_user_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobDriveDetailResponse(JobDriveResponse):
    company: CompanyResponse | None = None
    positions: list[JobPositionDetailResponse] = []


# --- Eligibility Evaluation ---
class RuleEvaluationResult(BaseModel):
    rule_type: str
    expected: Any
    actual: Any
    passed: bool
    message: str | None = None


class EligibilityEvaluationResponse(BaseModel):
    student_id: UUID
    job_position_id: UUID
    is_eligible: bool
    evaluated_at: datetime
    rule_results: list[RuleEvaluationResult]
    source_data_snapshot: dict[str, Any]


class EligibilitySnapshotResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    student_id: UUID
    job_position_id: UUID
    is_eligible: bool
    evaluated_at: datetime
    evaluated_by_id: UUID | None = None
    rule_results_json: list[dict[str, Any]]
    source_data_snapshot_json: dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


# --- Student Placement Profile ---
class StudentPlacementProfileBase(BaseModel):
    career_objective: str | None = None
    preferred_locations_json: list[str] | None = None
    preferred_roles_json: list[str] | None = None
    skills_json: list[str] | None = None
    certifications_json: list[dict[str, Any]] | None = None
    portfolio_url: str | None = Field(None, max_length=255)
    github_url: str | None = Field(None, max_length=255)
    linkedin_url: str | None = Field(None, max_length=255)
    resume_document_id: UUID | None = None
    availability_status: str = Field("AVAILABLE", max_length=32)  # AVAILABLE, OPTED_OUT, PLACED, HIGHER_STUDIES


class StudentPlacementProfileCreate(StudentPlacementProfileBase):
    student_id: UUID


class StudentPlacementProfileUpdate(StudentPlacementProfileBase):
    pass


class StudentPlacementProfileResponse(StudentPlacementProfileBase):
    id: UUID
    tenant_id: UUID
    student_id: UUID
    profile_completion_percentage: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Placement Application & Status History ---
class PlacementApplicationCreate(BaseModel):
    job_position_id: UUID


class ApplicationStatusUpdate(BaseModel):
    to_status: str = Field(..., max_length=32)  # SHORTLISTED, REJECTED, WITHDRAWN, INTERVIEWING, SELECTED, OFFERED, ACCEPTED, DECLINED
    reason: str | None = None


class ApplicationHistoryResponse(BaseModel):
    id: UUID
    application_id: UUID
    from_status: str
    to_status: str
    reason: str | None = None
    changed_by_user_id: UUID | None = None
    changed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PlacementApplicationResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    student_id: UUID
    job_position_id: UUID
    eligibility_snapshot_id: UUID | None = None
    application_number: str
    status: str
    applied_at: datetime
    withdrawn_at: datetime | None = None
    withdrawal_reason: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Interview Rounds, Schedules & Evaluations ---
class InterviewRoundBase(BaseModel):
    name: str = Field(..., max_length=64)
    description: str | None = None
    sequence: int = 1
    round_type: str = Field("TECHNICAL", max_length=32)  # APTITUDE, TECHNICAL, CODING, GROUP_DISCUSSION, MANAGERIAL, HR, FINAL, OTHER
    status: str = Field("SCHEDULED", max_length=32)


class InterviewRoundCreate(InterviewRoundBase):
    pass


class InterviewRoundResponse(InterviewRoundBase):
    id: UUID
    job_position_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InterviewScheduleBase(BaseModel):
    interview_round_id: UUID
    application_id: UUID
    scheduled_at: datetime
    duration_minutes: int = 30
    location: str | None = Field(None, max_length=255)
    meeting_url: str | None = Field(None, max_length=255)
    interviewer: str | None = Field(None, max_length=128)
    status: str = Field("SCHEDULED", max_length=32)


class InterviewScheduleCreate(InterviewScheduleBase):
    pass


class InterviewEvaluationBase(BaseModel):
    result: str = Field("PASS", max_length=32)  # PASS, FAIL, ON_HOLD, PENDING, NO_SHOW
    score: Decimal | None = None
    feedback: str | None = None
    internal_notes: str | None = None
    recommendation: str | None = Field(None, max_length=64)  # STRONG_HIRE, HIRE, NO_HIRE


class InterviewEvaluationCreate(InterviewEvaluationBase):
    pass


class InterviewEvaluationResponse(InterviewEvaluationBase):
    id: UUID
    interview_schedule_id: UUID
    evaluated_by_user_id: UUID | None = None
    evaluated_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InterviewScheduleResponse(InterviewScheduleBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Placement Offers ---
class PlacementOfferBase(BaseModel):
    student_id: UUID
    job_position_id: UUID
    company_id: UUID
    placement_application_id: UUID
    offer_date: date
    designation: str = Field(..., max_length=128)
    ctc: Decimal = Field(..., ge=0)
    currency: str = Field("INR", max_length=3)
    work_location: str | None = Field(None, max_length=128)
    joining_date: date | None = None
    employment_type: str = Field("FULL_TIME", max_length=32)
    offer_expiry_date: date
    document_id: UUID | None = None


class PlacementOfferCreate(PlacementOfferBase):
    pass


class OfferDecisionRequest(BaseModel):
    decision: str = Field(..., pattern="^(ACCEPT|DECLINE)$")
    decline_reason: str | None = None


class PlacementOfferResponse(PlacementOfferBase):
    id: UUID
    tenant_id: UUID
    offer_number: str
    status: str  # DRAFT, ISSUED, ACCEPTED, DECLINED, EXPIRED, WITHDRAWN, CANCELLED
    accepted_at: datetime | None = None
    declined_at: datetime | None = None
    decline_reason: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Placement Outcomes & Analytics ---
class PlacementOutcomeBase(BaseModel):
    student_id: UUID
    academic_year_id: UUID
    outcome: str = Field("PLACED", max_length=32)  # PLACED, NOT_PLACED, HIGHER_STUDIES, ENTREPRENEURSHIP, OTHER
    accepted_offer_id: UUID | None = None
    company_id: UUID | None = None
    designation: str | None = Field(None, max_length=128)
    ctc: Decimal | None = None
    remarks: str | None = None


class PlacementOutcomeCreate(PlacementOutcomeBase):
    pass


class PlacementOutcomeResponse(PlacementOutcomeBase):
    id: UUID
    tenant_id: UUID
    recorded_at: datetime
    recorded_by_user_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PlacementAnalyticsSummary(BaseModel):
    total_eligible_students: int = 0
    registered_students: int = 0
    placed_students: int = 0
    placement_percentage: float = 0.0
    total_offers: int = 0
    unique_companies_count: int = 0
    highest_ctc: float = 0.0
    average_ctc: float = 0.0
    median_ctc: float = 0.0
    tier_distribution: dict[str, int] = {}
    department_stats: list[dict[str, Any]] = []
    top_recruiters: list[dict[str, Any]] = []
