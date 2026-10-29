"""Pydantic Schemas for Enterprise Student Counselling, Mentoring & Personal Development (Step 59).

Product Principle: "One Campus. One System. One Source of Truth."
"""

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.student_support import (
    ActionItemStatus,
    AppointmentMode,
    AppointmentStatus,
    CounsellingCategory,
    GoalCategory,
    GoalStatus,
    MentorAssignmentStatus,
    MentorAssignmentType,
    PlanStatus,
    ReferralPriority,
    ReferralReasonCategory,
    ReferralStatus,
    ReferralTargetService,
    SessionAttendanceStatus,
    SessionStatus,
    SessionType,
)

# =============================================================================
# 1. MENTOR ASSIGNMENT SCHEMAS
# =============================================================================


class MentorAssignmentCreate(BaseModel):
    student_id: UUID
    mentor_user_id: UUID
    department_id: UUID | None = None
    program_id: UUID | None = None
    academic_year: str = Field(..., max_length=32)
    assignment_type: MentorAssignmentType = MentorAssignmentType.MANUAL
    assigned_date: date = Field(default_factory=date.today)
    notes: str | None = None


class MentorAssignmentUpdate(BaseModel):
    status: MentorAssignmentStatus | None = None
    end_date: date | None = None
    notes: str | None = None


class MentorReassignRequest(BaseModel):
    new_mentor_user_id: UUID
    reason: str = Field(..., min_length=3)
    effective_date: date = Field(default_factory=date.today)


class MentorAssignmentResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    student_id: UUID
    mentor_user_id: UUID
    department_id: UUID | None = None
    program_id: UUID | None = None
    academic_year: str
    assignment_type: str
    status: str
    assigned_date: date
    end_date: date | None = None
    notes: str | None = None
    reassigned_from_id: UUID | None = None
    reassignment_reason: str | None = None
    student_name: str | None = None
    student_roll: str | None = None
    mentor_name: str | None = None
    mentor_email: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 2. MENTORING SESSION SCHEMAS
# =============================================================================


class SessionAttendeeInput(BaseModel):
    student_id: UUID
    attendance_status: SessionAttendanceStatus = SessionAttendanceStatus.PENDING


class MentoringSessionCreate(BaseModel):
    assignment_id: UUID | None = None
    mentor_user_id: UUID
    session_title: str = Field(..., min_length=2, max_length=200)
    session_type: SessionType = SessionType.ONE_ON_ONE
    session_date: date
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    location_or_link: str | None = None
    summary: str | None = None  # Non-clinical
    action_items: list[dict[str, Any]] = Field(default_factory=list)
    follow_up_date: date | None = None
    attendee_student_ids: list[UUID] = Field(default_factory=list)


class MentoringSessionUpdate(BaseModel):
    session_title: str | None = None
    session_date: date | None = None
    start_time: str | None = None
    end_time: str | None = None
    location_or_link: str | None = None
    status: SessionStatus | None = None
    summary: str | None = None
    action_items: list[dict[str, Any]] | None = None
    follow_up_date: date | None = None


class SessionAttendeeResponse(BaseModel):
    id: UUID
    session_id: UUID
    student_id: UUID
    student_name: str | None = None
    attendance_status: str
    student_feedback: str | None = None
    student_reflection: str | None = None

    model_config = ConfigDict(from_attributes=True)


class MentoringSessionResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    assignment_id: UUID | None = None
    mentor_user_id: UUID
    mentor_name: str | None = None
    session_title: str
    session_type: str
    session_date: date
    start_time: str
    end_time: str
    location_or_link: str | None = None
    status: str
    summary: str | None = None
    action_items: list[dict[str, Any]] | None = None
    follow_up_date: date | None = None
    created_by_user_id: UUID
    attendees: list[SessionAttendeeResponse] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class SessionAttendeeReflectionUpdate(BaseModel):
    attendance_status: SessionAttendanceStatus | None = None
    student_feedback: str | None = None
    student_reflection: str | None = None


# =============================================================================
# 3. COUNSELLING APPOINTMENT SCHEMAS
# =============================================================================


class CounsellingAppointmentCreate(BaseModel):
    student_id: UUID
    counsellor_user_id: UUID | None = None
    category: CounsellingCategory = CounsellingCategory.GENERAL_WELLBEING
    appointment_date: date
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    duration_minutes: int = 45
    mode: AppointmentMode = AppointmentMode.IN_PERSON
    venue_or_link: str | None = None
    request_reason: str = Field(..., min_length=2, max_length=255)


class CounsellingAppointmentUpdate(BaseModel):
    counsellor_user_id: UUID | None = None
    category: CounsellingCategory | None = None
    appointment_date: date | None = None
    start_time: str | None = None
    end_time: str | None = None
    duration_minutes: int | None = None
    mode: AppointmentMode | None = None
    venue_or_link: str | None = None
    status: AppointmentStatus | None = None
    cancellation_reason: str | None = None


class CounsellingAppointmentResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    student_id: UUID
    student_name: str | None = None
    counsellor_user_id: UUID | None = None
    counsellor_name: str | None = None
    category: str
    appointment_date: date
    start_time: str
    end_time: str
    duration_minutes: int
    mode: str
    venue_or_link: str | None = None
    status: str
    request_reason: str
    booked_by_user_id: UUID
    cancellation_reason: str | None = None
    is_confidential: bool
    has_confidential_notes: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 4. CONFIDENTIAL COUNSELLING RECORD SCHEMAS
# =============================================================================


class ConfidentialCounsellingRecordCreate(BaseModel):
    appointment_id: UUID | None = None
    student_id: UUID
    session_notes_restricted: str = Field(..., min_length=5)
    intervention_type: str = "COUNSELLING_DIALOGUE"
    clinical_observations: str | None = None
    follow_up_recommended: bool = False
    follow_up_target_date: date | None = None
    consent_confirmed: bool = True


class ConfidentialCounsellingRecordUpdate(BaseModel):
    session_notes_restricted: str | None = None
    intervention_type: str | None = None
    clinical_observations: str | None = None
    follow_up_recommended: bool | None = None
    follow_up_target_date: date | None = None
    consent_confirmed: bool | None = None


class ConfidentialCounsellingRecordResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    appointment_id: UUID | None = None
    student_id: UUID
    student_name: str | None = None
    counsellor_user_id: UUID
    counsellor_name: str | None = None
    session_notes_restricted: str
    intervention_type: str
    clinical_observations: str | None = None
    follow_up_recommended: bool
    follow_up_target_date: date | None = None
    consent_confirmed: bool
    access_count: int
    last_accessed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 5. STUDENT DEVELOPMENT PLAN SCHEMAS
# =============================================================================


class DevelopmentActionItemCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    due_date: date
    assigned_to_role: str = "STUDENT"


class DevelopmentActionItemUpdate(BaseModel):
    title: str | None = None
    due_date: date | None = None
    status: ActionItemStatus | None = None
    assigned_to_role: str | None = None


class DevelopmentActionItemResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    goal_id: UUID
    title: str
    due_date: date
    status: str
    assigned_to_role: str
    completed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class DevelopmentGoalCreate(BaseModel):
    category: GoalCategory = GoalCategory.ACADEMIC
    title: str = Field(..., min_length=2, max_length=200)
    description: str
    target_date: date
    measurable_milestones: list[dict[str, Any]] = Field(default_factory=list)
    mentor_notes: str | None = None
    action_items: list[DevelopmentActionItemCreate] = Field(default_factory=list)


class DevelopmentGoalUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    target_date: date | None = None
    status: GoalStatus | None = None
    progress_pct: int | None = Field(None, ge=0, le=100)
    measurable_milestones: list[dict[str, Any]] | None = None
    mentor_notes: str | None = None
    student_reflection: str | None = None


class DevelopmentGoalResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    plan_id: UUID
    category: str
    title: str
    description: str
    target_date: date
    status: str
    progress_pct: int
    measurable_milestones: list[dict[str, Any]] | None = None
    mentor_notes: str | None = None
    student_reflection: str | None = None
    action_items: list[DevelopmentActionItemResponse] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class StudentDevelopmentPlanCreate(BaseModel):
    student_id: UUID
    mentor_user_id: UUID | None = None
    title: str = Field(..., min_length=2, max_length=200)
    academic_year: str = Field(..., max_length=32)
    review_frequency: str = "SEMESTER"
    next_review_date: date | None = None
    strengths_summary: str | None = None
    areas_for_growth: str | None = None
    career_aspirations: str | None = None
    goals: list[DevelopmentGoalCreate] = Field(default_factory=list)


class StudentDevelopmentPlanUpdate(BaseModel):
    title: str | None = None
    status: PlanStatus | None = None
    review_frequency: str | None = None
    next_review_date: date | None = None
    strengths_summary: str | None = None
    areas_for_growth: str | None = None
    career_aspirations: str | None = None


class StudentDevelopmentPlanResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    student_id: UUID
    student_name: str | None = None
    mentor_user_id: UUID | None = None
    mentor_name: str | None = None
    title: str
    academic_year: str
    status: str
    overall_progress_pct: int
    review_frequency: str
    last_reviewed_at: datetime | None = None
    next_review_date: date | None = None
    strengths_summary: str | None = None
    areas_for_growth: str | None = None
    career_aspirations: str | None = None
    goals: list[DevelopmentGoalResponse] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 6. SUPPORT REFERRALS & FOLLOW-UPS
# =============================================================================


class SupportReferralCreate(BaseModel):
    student_id: UUID
    referring_role: str = "FACULTY"
    target_service: ReferralTargetService = ReferralTargetService.ACADEMIC_ADVISING
    reason_category: ReferralReasonCategory = ReferralReasonCategory.ACADEMIC_DIFFICULTY
    priority: ReferralPriority = ReferralPriority.MEDIUM
    summary_notes: str = Field(..., min_length=5)
    consent_obtained: bool = True
    assigned_staff_user_id: UUID | None = None


class SupportReferralUpdate(BaseModel):
    status: ReferralStatus | None = None
    assigned_staff_user_id: UUID | None = None
    outcome_notes: str | None = None


class SupportFollowUpCreate(BaseModel):
    referral_id: UUID | None = None
    plan_id: UUID | None = None
    appointment_id: UUID | None = None
    assigned_user_id: UUID
    title: str = Field(..., min_length=2, max_length=200)
    due_date: date
    notes: str | None = None


class SupportFollowUpUpdate(BaseModel):
    title: str | None = None
    due_date: date | None = None
    notes: str | None = None
    status: str | None = None


class SupportFollowUpResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    referral_id: UUID | None = None
    plan_id: UUID | None = None
    appointment_id: UUID | None = None
    assigned_user_id: UUID
    assigned_user_name: str | None = None
    title: str
    due_date: date
    notes: str | None = None
    status: str
    completed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class SupportReferralResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    referral_code: str
    student_id: UUID
    student_name: str | None = None
    referring_user_id: UUID
    referring_user_name: str | None = None
    referring_role: str
    target_service: str
    reason_category: str
    priority: str
    summary_notes: str
    status: str
    assigned_staff_user_id: UUID | None = None
    assigned_staff_name: str | None = None
    consent_obtained: bool
    outcome_notes: str | None = None
    closed_at: datetime | None = None
    follow_ups: list[SupportFollowUpResponse] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 7. AUDIT LOG & CONFIGURATION SCHEMAS
# =============================================================================


class SupportAuditLogResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    user_id: UUID
    user_name: str | None = None
    action: str
    resource_id: UUID
    resource_type: str
    ip_address: str | None = None
    user_agent: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SupportPolicyConfigUpdate(BaseModel):
    max_mentees_per_mentor: int | None = Field(None, ge=1, le=100)
    allow_cross_department_mentors: bool | None = None
    appointment_advance_booking_days: int | None = Field(None, ge=1, le=90)
    appointment_cancellation_lead_hours: int | None = Field(None, ge=0, le=48)
    default_session_duration_minutes: int | None = Field(None, ge=15, le=120)
    enable_confidential_counselling: bool | None = None
    require_student_consent_for_referral: bool | None = None


class SupportPolicyConfigResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    max_mentees_per_mentor: int
    allow_cross_department_mentors: bool
    appointment_advance_booking_days: int
    appointment_cancellation_lead_hours: int
    default_session_duration_minutes: int
    enable_confidential_counselling: bool
    require_student_consent_for_referral: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 8. TELEMETRY & ANALYTICS SCHEMAS (PRIVACY-SAFE)
# =============================================================================


class StudentSupportTelemetryResponse(BaseModel):
    """Aggregate metrics with small-group suppression. Never exposes confidential clinical notes."""
    total_active_mentor_assignments: int = 0
    total_unassigned_students: int = 0
    mentoring_sessions_completed_this_month: int = 0
    appointment_utilization_rate_pct: float = 0.0
    pending_support_referrals: int = 0
    overdue_follow_ups: int = 0
    development_plan_completion_rate_pct: float = 0.0
    referrals_by_service: dict[str, int] = Field(default_factory=dict)
    goals_by_category: dict[str, int] = Field(default_factory=dict)
