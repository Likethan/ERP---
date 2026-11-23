"""SQLAlchemy Entities for Enterprise Student Counselling, Mentoring & Personal Development Management (Step 59).

Product Principle: "One Campus. One System. One Source of Truth."

Coordinates institutional faculty mentoring, student development plans (IDPs),
counselling appointments, strictly confidential counselling session notes,
inter-service support referrals, follow-up workflows, and privacy-safe operational analytics.
"""

from datetime import date, datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any
from uuid import UUID

if TYPE_CHECKING:
    from app.models.people import StudentProfile, User

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantScopedModel

# Cross-dialect JSON type for PostgreSQL JSONB and SQLite JSON
JSONType = JSON().with_variant(JSONB, "postgresql")


# =============================================================================
# 1. ENUMS & DOMAIN CONSTANTS
# =============================================================================


class MentorAssignmentType(StrEnum):
    MANUAL = "MANUAL"
    RULE_BASED = "RULE_BASED"
    REASSIGNED = "REASSIGNED"
    TEMPORARY_COVERAGE = "TEMPORARY_COVERAGE"


class MentorAssignmentStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    REASSIGNED = "REASSIGNED"
    COMPLETED = "COMPLETED"


class SessionType(StrEnum):
    ONE_ON_ONE = "ONE_ON_ONE"
    GROUP = "GROUP"
    CHECK_IN = "CHECK_IN"
    ACADEMIC_REVIEW = "ACADEMIC_REVIEW"
    CAREER_DISCUSSIONS = "CAREER_DISCUSSIONS"


class SessionStatus(StrEnum):
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    RESCHEDULED = "RESCHEDULED"


class SessionAttendanceStatus(StrEnum):
    ATTENDED = "ATTENDED"
    ABSENT = "ABSENT"
    EXCUSED = "EXCUSED"
    PENDING = "PENDING"


class CounsellingCategory(StrEnum):
    ACADEMIC_STRESS = "ACADEMIC_STRESS"
    CAREER_ANXIETY = "CAREER_ANXIETY"
    PERSONAL_COUNSELLING = "PERSONAL_COUNSELLING"
    TIME_MANAGEMENT = "TIME_MANAGEMENT"
    PEER_RELATIONS = "PEER_RELATIONS"
    GENERAL_WELLBEING = "GENERAL_WELLBEING"
    OTHER = "OTHER"


class AppointmentMode(StrEnum):
    IN_PERSON = "IN_PERSON"
    ONLINE = "ONLINE"
    HYBRID = "HYBRID"


class AppointmentStatus(StrEnum):
    REQUESTED = "REQUESTED"
    CONFIRMED = "CONFIRMED"
    RESCHEDULED = "RESCHEDULED"
    CHECKED_IN = "CHECKED_IN"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"


class PlanStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    UNDER_REVIEW = "UNDER_REVIEW"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class GoalCategory(StrEnum):
    ACADEMIC = "ACADEMIC"
    PROFESSIONAL = "PROFESSIONAL"
    COMMUNICATION = "COMMUNICATION"
    LEADERSHIP = "LEADERSHIP"
    PERSONAL = "PERSONAL"
    CAREER = "CAREER"


class GoalStatus(StrEnum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    DEFERRED = "DEFERRED"


class ActionItemStatus(StrEnum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"


class ReferralTargetService(StrEnum):
    ACADEMIC_ADVISING = "ACADEMIC_ADVISING"
    CAREER_SERVICES = "CAREER_SERVICES"
    COUNSELLING_SERVICES = "COUNSELLING_SERVICES"
    DISABILITY_SUPPORT = "DISABILITY_SUPPORT"
    FINANCIAL_AID = "FINANCIAL_AID"
    HEALTH_SERVICES = "HEALTH_SERVICES"


class ReferralReasonCategory(StrEnum):
    ACADEMIC_DIFFICULTY = "ACADEMIC_DIFFICULTY"
    CAREER_GUIDANCE = "CAREER_GUIDANCE"
    PERSONAL_SUPPORT = "PERSONAL_SUPPORT"
    FINANCIAL_ASSISTANCE = "FINANCIAL_ASSISTANCE"
    ATTENDANCE_CONCERN = "ATTENDANCE_CONCERN"
    DISABILITY_ACCOMMODATION = "DISABILITY_ACCOMMODATION"
    OTHER = "OTHER"


class ReferralPriority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class ReferralStatus(StrEnum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    DECLINED = "DECLINED"
    CANCELLED = "CANCELLED"


class FollowUpStatus(StrEnum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class SupportAuditAction(StrEnum):
    VIEW_CONFIDENTIAL_RECORD = "VIEW_CONFIDENTIAL_RECORD"
    CREATE_CONFIDENTIAL_RECORD = "CREATE_CONFIDENTIAL_RECORD"
    UPDATE_CONFIDENTIAL_RECORD = "UPDATE_CONFIDENTIAL_RECORD"
    EXPORT_REPORT = "EXPORT_REPORT"
    REASSIGN_MENTOR = "REASSIGN_MENTOR"


# =============================================================================
# 2. CORE ENTITIES
# =============================================================================


class MentorAssignment(TenantScopedModel):
    """Institutional assignment connecting a student mentee with a faculty mentor."""

    __tablename__ = "ss_mentor_assignments"
    __table_args__ = (
        Index("idx_ss_mentor_assign_student", "tenant_id", "student_id", "status"),
        Index("idx_ss_mentor_assign_mentor", "tenant_id", "mentor_user_id", "status"),
    )

    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="CASCADE"),
        nullable=False,
    )
    mentor_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    program_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_programs.id", ondelete="SET NULL"),
        nullable=True,
    )
    academic_year: Mapped[str] = mapped_column(String(32), nullable=False)
    assignment_type: Mapped[str] = mapped_column(
        String(32), default=MentorAssignmentType.MANUAL.value, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), default=MentorAssignmentStatus.ACTIVE.value, nullable=False
    )
    assigned_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    reassigned_from_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("ss_mentor_assignments.id", ondelete="SET NULL"),
        nullable=True,
    )
    reassignment_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    student: Mapped["StudentProfile"] = relationship("StudentProfile", foreign_keys=[student_id])
    mentor_user: Mapped["User"] = relationship("User", foreign_keys=[mentor_user_id])
    sessions: Mapped[list["MentoringSession"]] = relationship(
        "MentoringSession", back_populates="assignment"
    )


class MentoringSession(TenantScopedModel):
    """Scheduled or completed non-clinical mentoring interaction."""

    __tablename__ = "ss_mentoring_sessions"
    __table_args__ = (
        Index("idx_ss_session_mentor_date", "tenant_id", "mentor_user_id", "session_date"),
        Index("idx_ss_session_status", "tenant_id", "status"),
    )

    assignment_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("ss_mentor_assignments.id", ondelete="SET NULL"),
        nullable=True,
    )
    mentor_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    session_title: Mapped[str] = mapped_column(String(200), nullable=False)
    session_type: Mapped[str] = mapped_column(
        String(32), default=SessionType.ONE_ON_ONE.value, nullable=False
    )
    session_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[str] = mapped_column(String(8), nullable=False)  # HH:MM
    end_time: Mapped[str] = mapped_column(String(8), nullable=False)    # HH:MM
    location_or_link: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default=SessionStatus.SCHEDULED.value, nullable=False
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)  # Strictly non-clinical
    action_items: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSONType, default=list, nullable=True
    )
    follow_up_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_by_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Relationships
    assignment: Mapped["MentorAssignment | None"] = relationship(
        "MentorAssignment", back_populates="sessions"
    )
    mentor_user: Mapped["User"] = relationship("User", foreign_keys=[mentor_user_id])
    created_by: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    attendees: Mapped[list["MentoringSessionAttendee"]] = relationship(
        "MentoringSessionAttendee", back_populates="session", cascade="all, delete-orphan"
    )


class MentoringSessionAttendee(TenantScopedModel):
    """Attendee record and reflection for a student participant in a mentoring session."""

    __tablename__ = "ss_session_attendees"
    __table_args__ = (
        UniqueConstraint("session_id", "student_id", name="uq_session_student_attendee"),
        Index("idx_ss_attendee_student", "tenant_id", "student_id", "attendance_status"),
    )

    session_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("ss_mentoring_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="CASCADE"),
        nullable=False,
    )
    attendance_status: Mapped[str] = mapped_column(
        String(32), default=SessionAttendanceStatus.PENDING.value, nullable=False
    )
    student_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    student_reflection: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    session: Mapped["MentoringSession"] = relationship("MentoringSession", back_populates="attendees")
    student: Mapped["StudentProfile"] = relationship("StudentProfile")


class CounsellingAppointment(TenantScopedModel):
    """Institutional counselling appointment booking, scheduling, and lifecycle tracking."""

    __tablename__ = "ss_counselling_appointments"
    __table_args__ = (
        Index("idx_ss_counsel_counsellor_date", "tenant_id", "counsellor_user_id", "appointment_date", "status"),
        Index("idx_ss_counsel_student_date", "tenant_id", "student_id", "appointment_date"),
    )

    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="CASCADE"),
        nullable=False,
    )
    counsellor_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    category: Mapped[str] = mapped_column(
        String(64), default=CounsellingCategory.GENERAL_WELLBEING.value, nullable=False
    )
    appointment_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[str] = mapped_column(String(8), nullable=False)  # HH:MM
    end_time: Mapped[str] = mapped_column(String(8), nullable=False)    # HH:MM
    duration_minutes: Mapped[int] = mapped_column(Integer, default=45, nullable=False)
    mode: Mapped[str] = mapped_column(
        String(32), default=AppointmentMode.IN_PERSON.value, nullable=False
    )
    venue_or_link: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default=AppointmentStatus.REQUESTED.value, nullable=False
    )
    request_reason: Mapped[str] = mapped_column(String(255), nullable=False)  # Privacy-safe summary
    booked_by_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_confidential: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    student: Mapped["StudentProfile"] = relationship("StudentProfile")
    counsellor_user: Mapped["User | None"] = relationship("User", foreign_keys=[counsellor_user_id])
    booked_by: Mapped["User"] = relationship("User", foreign_keys=[booked_by_user_id])
    confidential_record: Mapped["ConfidentialCounsellingRecord | None"] = relationship(
        "ConfidentialCounsellingRecord", back_populates="appointment", uselist=False
    )


class ConfidentialCounsellingRecord(TenantScopedModel):
    """Strictly restricted clinical counselling session notes.

    CRITICAL ACCESS CONSTRAINT:
    Never expose session content to mentors, HODs, Vice Principals, or general administrators.
    Only authorized professionals with COUNSELLING_CONFIDENTIAL_READ can access.
    Automated psychological diagnosis or mental-health risk scoring is forbidden.
    """

    __tablename__ = "ss_confidential_counselling_records"
    __table_args__ = (
        UniqueConstraint("appointment_id", name="uq_ss_confidential_appointment"),
        Index("idx_ss_confidential_student", "tenant_id", "student_id"),
    )

    appointment_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("ss_counselling_appointments.id", ondelete="SET NULL"),
        nullable=True,
    )
    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="CASCADE"),
        nullable=False,
    )
    counsellor_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    session_notes_restricted: Mapped[str] = mapped_column(Text, nullable=False)
    intervention_type: Mapped[str] = mapped_column(String(64), nullable=False, default="COUNSELLING_DIALOGUE")
    clinical_observations: Mapped[str | None] = mapped_column(Text, nullable=True)
    follow_up_recommended: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    follow_up_target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    consent_confirmed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    access_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    last_accessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    appointment: Mapped["CounsellingAppointment | None"] = relationship(
        "CounsellingAppointment", back_populates="confidential_record"
    )
    student: Mapped["StudentProfile"] = relationship("StudentProfile")
    counsellor_user: Mapped["User"] = relationship("User", foreign_keys=[counsellor_user_id])


class StudentDevelopmentPlan(TenantScopedModel):
    """Individual Student Development Plan (IDP) with goals, milestones, and progress reviews."""

    __tablename__ = "ss_student_development_plans"
    __table_args__ = (
        Index("idx_ss_devplan_student_year", "tenant_id", "student_id", "academic_year"),
        Index("idx_ss_devplan_status", "tenant_id", "status"),
    )

    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="CASCADE"),
        nullable=False,
    )
    mentor_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    academic_year: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=PlanStatus.ACTIVE.value, nullable=False
    )
    overall_progress_pct: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    review_frequency: Mapped[str] = mapped_column(String(32), default="SEMESTER", nullable=False)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_review_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    strengths_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    areas_for_growth: Mapped[str | None] = mapped_column(Text, nullable=True)
    career_aspirations: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    student: Mapped["StudentProfile"] = relationship("StudentProfile")
    mentor_user: Mapped["User | None"] = relationship("User", foreign_keys=[mentor_user_id])
    goals: Mapped[list["DevelopmentGoal"]] = relationship(
        "DevelopmentGoal", back_populates="plan", cascade="all, delete-orphan"
    )


class DevelopmentGoal(TenantScopedModel):
    """Specific measurable target within an individual development plan."""

    __tablename__ = "ss_development_goals"
    __table_args__ = (
        Index("idx_ss_goal_plan", "tenant_id", "plan_id", "status"),
    )

    plan_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("ss_student_development_plans.id", ondelete="CASCADE"),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(
        String(32), default=GoalCategory.ACADEMIC.value, nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=GoalStatus.ACTIVE.value, nullable=False
    )
    progress_pct: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    measurable_milestones: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSONType, default=list, nullable=True
    )
    mentor_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    student_reflection: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    plan: Mapped["StudentDevelopmentPlan"] = relationship("StudentDevelopmentPlan", back_populates="goals")
    action_items: Mapped[list["DevelopmentActionItem"]] = relationship(
        "DevelopmentActionItem", back_populates="goal", cascade="all, delete-orphan"
    )


class DevelopmentActionItem(TenantScopedModel):
    """Actionable task with deadline supporting milestone achievement."""

    __tablename__ = "ss_development_action_items"
    __table_args__ = (
        Index("idx_ss_action_goal", "tenant_id", "goal_id", "status"),
    )

    goal_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("ss_development_goals.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=ActionItemStatus.PENDING.value, nullable=False
    )
    assigned_to_role: Mapped[str] = mapped_column(String(32), default="STUDENT", nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    goal: Mapped["DevelopmentGoal"] = relationship("DevelopmentGoal", back_populates="action_items")


class SupportReferral(TenantScopedModel):
    """Controlled referral across institutional support services."""

    __tablename__ = "ss_support_referrals"
    __table_args__ = (
        UniqueConstraint("tenant_id", "referral_code", name="uq_ss_referral_tenant_code"),
        Index("idx_ss_referral_student", "tenant_id", "student_id", "status"),
        Index("idx_ss_referral_service", "tenant_id", "target_service", "status"),
    )

    referral_code: Mapped[str] = mapped_column(String(64), nullable=False)
    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="CASCADE"),
        nullable=False,
    )
    referring_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    referring_role: Mapped[str] = mapped_column(String(64), nullable=False)
    target_service: Mapped[str] = mapped_column(
        String(64), default=ReferralTargetService.ACADEMIC_ADVISING.value, nullable=False
    )
    reason_category: Mapped[str] = mapped_column(
        String(64), default=ReferralReasonCategory.ACADEMIC_DIFFICULTY.value, nullable=False
    )
    priority: Mapped[str] = mapped_column(
        String(32), default=ReferralPriority.MEDIUM.value, nullable=False
    )
    summary_notes: Mapped[str] = mapped_column(Text, nullable=False)  # Strictly non-clinical safe summary
    status: Mapped[str] = mapped_column(
        String(32), default=ReferralStatus.PENDING.value, nullable=False
    )
    assigned_staff_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    consent_obtained: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    outcome_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    student: Mapped["StudentProfile"] = relationship("StudentProfile")
    referring_user: Mapped["User"] = relationship("User", foreign_keys=[referring_user_id])
    assigned_staff: Mapped["User | None"] = relationship("User", foreign_keys=[assigned_staff_user_id])
    follow_ups: Mapped[list["SupportFollowUp"]] = relationship(
        "SupportFollowUp", back_populates="referral", cascade="all, delete-orphan"
    )


class SupportFollowUp(TenantScopedModel):
    """Actionable follow-up check or review deadline connected to a referral, plan, or appointment."""

    __tablename__ = "ss_support_follow_ups"
    __table_args__ = (
        Index("idx_ss_followup_assigned", "tenant_id", "assigned_user_id", "status"),
        Index("idx_ss_followup_due", "tenant_id", "due_date", "status"),
    )

    referral_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("ss_support_referrals.id", ondelete="CASCADE"),
        nullable=True,
    )
    plan_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("ss_student_development_plans.id", ondelete="CASCADE"),
        nullable=True,
    )
    appointment_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("ss_counselling_appointments.id", ondelete="CASCADE"),
        nullable=True,
    )
    assigned_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default=FollowUpStatus.PENDING.value, nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    referral: Mapped["SupportReferral | None"] = relationship(
        "SupportReferral", back_populates="follow_ups"
    )
    assigned_user: Mapped["User"] = relationship("User", foreign_keys=[assigned_user_id])


class SupportAuditLog(TenantScopedModel):
    """Immutable access and modification audit trail for counselling and student support."""

    __tablename__ = "ss_support_audit_logs"
    __table_args__ = (
        Index("idx_ss_audit_resource", "tenant_id", "resource_type", "resource_id"),
        Index("idx_ss_audit_user", "tenant_id", "user_id", "created_at"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")


class SupportPolicyConfig(TenantScopedModel):
    """Institutional rules, limits, and configurations for mentoring and counselling."""

    __tablename__ = "ss_policy_configs"
    __table_args__ = (
        UniqueConstraint("tenant_id", name="uq_ss_policy_tenant"),
    )

    max_mentees_per_mentor: Mapped[int] = mapped_column(Integer, default=25, nullable=False)
    allow_cross_department_mentors: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    appointment_advance_booking_days: Mapped[int] = mapped_column(Integer, default=14, nullable=False)
    appointment_cancellation_lead_hours: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    default_session_duration_minutes: Mapped[int] = mapped_column(Integer, default=45, nullable=False)
    enable_confidential_counselling: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    require_student_consent_for_referral: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
