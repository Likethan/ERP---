"""Student Success, Academic Advising, Early-Warning & Intervention Management Models (Step 47).

Authoritative models for:
- Student-Success Cases & Case History Notes
- Academic Advisor Profiles & Caseload Capacity Management
- Advisor-to-Student Assignments
- Academic Advising Plans & Action Items
- Configurable, Explainable Early-Warning Rules & Versioning
- Early-Warning Evaluations & Deduplicated Warning Signals
- Interventions Plans, Actions & Outcome Tracking
- Advising Appointments & Scheduling Conflict Prevention
"""

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantScopedModel

if TYPE_CHECKING:
    from app.models.core import Campus, Department, Program
    from app.models.examination import ExamTerm
    from app.models.people import StaffProfile, StudentProfile, User


# =============================================================================
# ENUMS
# =============================================================================


class CaseCategory(StrEnum):
    """Categorization for student success cases."""

    ACADEMIC_PERFORMANCE = "ACADEMIC_PERFORMANCE"
    ATTENDANCE_CONCERNS = "ATTENDANCE_CONCERNS"
    ASSESSMENT_DIFFICULTIES = "ASSESSMENT_DIFFICULTIES"
    STUDY_PLANNING = "STUDY_PLANNING"
    ACADEMIC_PROGRESSION = "ACADEMIC_PROGRESSION"
    GENERAL_SUPPORT = "GENERAL_SUPPORT"


class CasePriority(StrEnum):
    """Urgency / priority of a student success case."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class CaseStatus(StrEnum):
    """Lifecycle status of a student success case."""

    OPEN = "OPEN"
    UNDER_REVIEW = "UNDER_REVIEW"
    INTERVENTION_PLANNED = "INTERVENTION_PLANNED"
    MONITORING = "MONITORING"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class CaseCreationSource(StrEnum):
    """Origin of case creation."""

    EARLY_WARNING_RULE = "EARLY_WARNING_RULE"
    ADVISOR_MANUAL = "ADVISOR_MANUAL"
    FACULTY_REFERRAL = "FACULTY_REFERRAL"
    STUDENT_REQUEST = "STUDENT_REQUEST"
    ADMINISTRATIVE = "ADMINISTRATIVE"


class CaseClosureReason(StrEnum):
    """Classifications for case closure."""

    ACADEMIC_IMPROVEMENT_ACHIEVED = "ACADEMIC_IMPROVEMENT_ACHIEVED"
    ATTENDANCE_TARGET_MET = "ATTENDANCE_TARGET_MET"
    STUDENT_WITHDRAWN = "STUDENT_WITHDRAWN"
    RESOLVED_NO_FURTHER_ACTION = "RESOLVED_NO_FURTHER_ACTION"
    ADMINISTRATIVE_CLOSURE = "ADMINISTRATIVE_CLOSURE"
    DUPLICATE_CONSOLIDATED = "DUPLICATE_CONSOLIDATED"


class CaseOutcomeClassification(StrEnum):
    """Human-reviewed final outcome of a student success case."""

    SUCCESSFUL = "SUCCESSFUL"
    PARTIALLY_SUCCESSFUL = "PARTIALLY_SUCCESSFUL"
    UNSUCCESSFUL = "UNSUCCESSFUL"
    INCONCLUSIVE = "INCONCLUSIVE"


class NoteType(StrEnum):
    """Classification for case notes."""

    INTERNAL_NOTE = "INTERNAL_NOTE"
    MEETING_SUMMARY = "MEETING_SUMMARY"
    STUDENT_UPDATE = "STUDENT_UPDATE"
    ACTION_UPDATE = "ACTION_UPDATE"
    STATUS_CHANGE_AUDIT = "STATUS_CHANGE_AUDIT"
    REASSIGNMENT_AUDIT = "REASSIGNMENT_AUDIT"


class AdvisorCategory(StrEnum):
    """Role/specialization of an academic advisor."""

    FACULTY_ADVISOR = "FACULTY_ADVISOR"
    DEPARTMENT_COORDINATOR = "DEPARTMENT_COORDINATOR"
    ACADEMIC_SUCCESS_COACH = "ACADEMIC_SUCCESS_COACH"
    PEER_MENTOR = "PEER_MENTOR"


class AssignmentRelationshipType(StrEnum):
    """Type of advising relationship."""

    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    SPECIALIST = "SPECIALIST"


class AssignmentStatus(StrEnum):
    """Status of an advisor-to-student assignment."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    COMPLETED = "COMPLETED"
    REASSIGNED = "REASSIGNED"


class AdvisingPlanStatus(StrEnum):
    """Status of an academic advising plan."""

    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class ReviewFrequency(StrEnum):
    """Cadence for student advising check-ins."""

    WEEKLY = "WEEKLY"
    BIWEEKLY = "BIWEEKLY"
    MONTHLY = "MONTHLY"
    TERMLY = "TERMLY"


class ActionResponsibleParty(StrEnum):
    """Responsible party for completing an advising action."""

    STUDENT = "STUDENT"
    ADVISOR = "ADVISOR"
    FACULTY = "FACULTY"


class ActionItemStatus(StrEnum):
    """Status of an advising or intervention action."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"


class EarlyWarningCategory(StrEnum):
    """Domain category for early warning rules."""

    ATTENDANCE = "ATTENDANCE"
    ASSESSMENT_FAILURE = "ASSESSMENT_FAILURE"
    CGPA_DROP = "CGPA_DROP"
    MISSING_COURSEWORK = "MISSING_COURSEWORK"


class ComparisonOperator(StrEnum):
    """Evaluation operator for early warning rules."""

    LESS_THAN = "LESS_THAN"
    LESS_THAN_OR_EQUAL = "LESS_THAN_OR_EQUAL"
    GREATER_THAN = "GREATER_THAN"
    GREATER_THAN_OR_EQUAL = "GREATER_THAN_OR_EQUAL"
    EQUALS = "EQUALS"


class WarningSeverity(StrEnum):
    """Risk severity classification."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EarlyWarningSignalStatus(StrEnum):
    """Lifecycle status of an early warning signal."""

    NEWLY_DETECTED = "NEWLY_DETECTED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    UNDER_REVIEW = "UNDER_REVIEW"
    INTERVENTION_INITIATED = "INTERVENTION_INITIATED"
    MONITORING = "MONITORING"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class EvaluationScope(StrEnum):
    """Target scope of an early warning evaluation run."""

    ALL_STUDENTS = "ALL_STUDENTS"
    DEPARTMENT = "DEPARTMENT"
    PROGRAM = "PROGRAM"
    COHORT = "COHORT"
    INDIVIDUAL_STUDENT = "INDIVIDUAL_STUDENT"


class EvaluationTrigger(StrEnum):
    """Trigger source for rule evaluation."""

    SCHEDULED_JOB = "SCHEDULED_JOB"
    EVENT_TRIGGER = "EVENT_TRIGGER"
    MANUAL_REQUEST = "MANUAL_REQUEST"


class EvaluationStatus(StrEnum):
    """Execution status of an evaluation job."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class InterventionType(StrEnum):
    """Types of support interventions."""

    ACADEMIC_ADVISING = "ACADEMIC_ADVISING"
    FACULTY_CONSULTATION = "FACULTY_CONSULTATION"
    STUDY_PLANNING = "STUDY_PLANNING"
    ASSESSMENT_PREPARATION = "ASSESSMENT_PREPARATION"
    ATTENDANCE_FOLLOWUP = "ATTENDANCE_FOLLOWUP"
    TUTORING_REFERRAL = "TUTORING_REFERRAL"
    SKILLS_WORKSHOP = "SKILLS_WORKSHOP"
    INSTITUTIONAL_SUPPORT_REFERRAL = "INSTITUTIONAL_SUPPORT_REFERRAL"


class InterventionStatus(StrEnum):
    """Status of an intervention plan."""

    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    OVERDUE = "OVERDUE"


class StudentParticipation(StrEnum):
    """Status of student participation in an intervention."""

    SCHEDULED = "SCHEDULED"
    ATTENDED = "ATTENDED"
    PARTIALLY_ATTENDED = "PARTIALLY_ATTENDED"
    NO_SHOW = "NO_SHOW"
    EXCUSED = "EXCUSED"


class AppointmentMode(StrEnum):
    """Format of an advising appointment."""

    IN_PERSON = "IN_PERSON"
    VIRTUAL_MEETING = "VIRTUAL_MEETING"
    PHONE_CALL = "PHONE_CALL"


class AppointmentStatus(StrEnum):
    """Status of an advising appointment."""

    REQUESTED = "REQUESTED"
    CONFIRMED = "CONFIRMED"
    COMPLETED = "COMPLETED"
    RESCHEDULED = "RESCHEDULED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"


# =============================================================================
# DOMAIN ENTITIES
# =============================================================================


class StudentSuccessCase(TenantScopedModel):
    """Structured student-success case management entity."""

    __tablename__ = "student_success_cases"
    __table_args__ = (
        UniqueConstraint("tenant_id", "case_number", name="uq_student_success_case_number"),
        Index("ix_ssc_tenant_student_status", "tenant_id", "student_id", "status"),
        Index("ix_ssc_tenant_advisor_status", "tenant_id", "assigned_advisor_id", "status"),
        Index("ix_ssc_tenant_category_priority", "tenant_id", "category", "priority"),
        Index("ix_ssc_tenant_next_review", "tenant_id", "next_review_date"),
        Index("ix_ssc_tenant_is_escalated", "tenant_id", "is_escalated"),
    )

    case_number: Mapped[str] = mapped_column(String(64), nullable=False)
    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(
        String(64), default=CaseCategory.ACADEMIC_PERFORMANCE, nullable=False
    )
    priority: Mapped[str] = mapped_column(
        String(32), default=CasePriority.MEDIUM, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), default=CaseStatus.OPEN, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    objective: Mapped[str | None] = mapped_column(Text, nullable=True)
    creation_source: Mapped[str] = mapped_column(
        String(64), default=CaseCreationSource.ADVISOR_MANUAL, nullable=False
    )

    assigned_advisor_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("student_success_advisor_profiles.id", ondelete="SET NULL"),
        nullable=True,
    )
    assigned_to_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    target_completion_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_review_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    actual_resolution_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    closure_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    outcome_classification: Mapped[str | None] = mapped_column(String(64), nullable=True)
    outcome_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_escalated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    escalation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    escalated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    reopened_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reopened_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    related_case_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("student_success_cases.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    student: Mapped["StudentProfile"] = relationship("StudentProfile")
    assigned_advisor: Mapped["AdvisorProfile | None"] = relationship(
        "AdvisorProfile", back_populates="cases", foreign_keys=[assigned_advisor_id]
    )
    assigned_user: Mapped["User | None"] = relationship(
        "User", foreign_keys=[assigned_to_user_id]
    )
    created_by: Mapped["User | None"] = relationship(
        "User", foreign_keys=[created_by_user_id]
    )
    notes: Mapped[list["StudentSuccessCaseNote"]] = relationship(
        "StudentSuccessCaseNote", back_populates="case", cascade="all, delete-orphan"
    )
    advising_plans: Mapped[list["AdvisingPlan"]] = relationship(
        "AdvisingPlan", back_populates="case"
    )
    interventions: Mapped[list["InterventionPlan"]] = relationship(
        "InterventionPlan", back_populates="case"
    )
    warning_signals: Mapped[list["EarlyWarningSignal"]] = relationship(
        "EarlyWarningSignal", back_populates="success_case"
    )
    appointments: Mapped[list["AdvisingAppointment"]] = relationship(
        "AdvisingAppointment", back_populates="case"
    )


class StudentSuccessCaseNote(TenantScopedModel):
    """Case comment, meeting record, or internal note with privacy visibility boundary."""

    __tablename__ = "student_success_case_notes"
    __table_args__ = (
        Index("ix_sscn_case_visible", "case_id", "is_student_visible"),
        Index("ix_sscn_case_created", "case_id", "created_at"),
    )

    case_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("student_success_cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    author_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    note_type: Mapped[str] = mapped_column(
        String(64), default=NoteType.INTERNAL_NOTE, nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_student_visible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    case: Mapped["StudentSuccessCase"] = relationship(
        "StudentSuccessCase", back_populates="notes"
    )
    author: Mapped["User"] = relationship("User")


class AdvisorProfile(TenantScopedModel):
    """Institutional academic advisor profile, workload limits, and departmental scope."""

    __tablename__ = "student_success_advisor_profiles"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", name="uq_advisor_tenant_user"),
        Index("ix_advisor_dept_active", "tenant_id", "department_id", "is_active"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    staff_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_staff.id", ondelete="SET NULL"),
        nullable=True,
    )
    advisor_category: Mapped[str] = mapped_column(
        String(64), default=AdvisorCategory.FACULTY_ADVISOR, nullable=False
    )
    department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="SET NULL"),
        nullable=True,
    )
    program_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_programs.id", ondelete="SET NULL"),
        nullable=True,
    )
    max_student_capacity: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    current_student_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    availability_schedule: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User")
    staff: Mapped["StaffProfile | None"] = relationship("StaffProfile")
    department: Mapped["Department | None"] = relationship("Department")
    campus: Mapped["Campus | None"] = relationship("Campus")
    program: Mapped["Program | None"] = relationship("Program")
    student_assignments: Mapped[list["AdvisorStudentAssignment"]] = relationship(
        "AdvisorStudentAssignment", back_populates="advisor"
    )
    cases: Mapped[list["StudentSuccessCase"]] = relationship(
        "StudentSuccessCase", back_populates="assigned_advisor"
    )
    advising_plans: Mapped[list["AdvisingPlan"]] = relationship(
        "AdvisingPlan", back_populates="advisor"
    )
    appointments: Mapped[list["AdvisingAppointment"]] = relationship(
        "AdvisingAppointment", back_populates="advisor"
    )


class AdvisorStudentAssignment(TenantScopedModel):
    """Advisor-to-student assignment with relationship type and reassignment history."""

    __tablename__ = "student_success_advisor_assignments"
    __table_args__ = (
        Index(
            "ix_asa_advisor_student_status",
            "tenant_id",
            "advisor_id",
            "student_id",
            "status",
        ),
        Index("ix_asa_student_status", "tenant_id", "student_id", "status"),
    )

    advisor_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("student_success_advisor_profiles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    relationship_type: Mapped[str] = mapped_column(
        String(32), default=AssignmentRelationshipType.PRIMARY, nullable=False
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default=AssignmentStatus.ACTIVE, nullable=False
    )
    reassignment_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    assigned_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    advisor: Mapped["AdvisorProfile"] = relationship(
        "AdvisorProfile", back_populates="student_assignments"
    )
    student: Mapped["StudentProfile"] = relationship("StudentProfile")
    assigned_by: Mapped["User | None"] = relationship(
        "User", foreign_keys=[assigned_by_user_id]
    )


class AdvisingPlan(TenantScopedModel):
    """Academic progress roadmap, target goals, and check-in cadence."""

    __tablename__ = "student_success_advising_plans"
    __table_args__ = (
        Index("ix_ap_student_status", "tenant_id", "student_id", "status"),
        Index("ix_ap_case_id", "case_id"),
    )

    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    advisor_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("student_success_advisor_profiles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    case_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("student_success_cases.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    academic_goals: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_gpa: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)
    target_credits: Mapped[int | None] = mapped_column(Integer, nullable=True)
    review_frequency: Mapped[str] = mapped_column(
        String(32), default=ReviewFrequency.MONTHLY, nullable=False
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default=AdvisingPlanStatus.ACTIVE, nullable=False
    )
    is_student_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    student: Mapped["StudentProfile"] = relationship("StudentProfile")
    advisor: Mapped["AdvisorProfile"] = relationship(
        "AdvisorProfile", back_populates="advising_plans"
    )
    case: Mapped["StudentSuccessCase | None"] = relationship(
        "StudentSuccessCase", back_populates="advising_plans"
    )
    action_items: Mapped[list["AdvisingActionItem"]] = relationship(
        "AdvisingActionItem", back_populates="advising_plan", cascade="all, delete-orphan"
    )


class AdvisingActionItem(TenantScopedModel):
    """Actionable milestone/task within an advising plan."""

    __tablename__ = "student_success_advising_action_items"
    __table_args__ = (
        Index("ix_aai_plan_status", "advising_plan_id", "status"),
        Index("ix_aai_due_date", "tenant_id", "due_date"),
    )

    advising_plan_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("student_success_advising_plans.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    responsible_party: Mapped[str] = mapped_column(
        String(32), default=ActionResponsibleParty.STUDENT, nullable=False
    )
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    completed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default=ActionItemStatus.PENDING, nullable=False
    )
    is_student_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    student_progress_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    advising_plan: Mapped["AdvisingPlan"] = relationship(
        "AdvisingPlan", back_populates="action_items"
    )


class EarlyWarningRule(TenantScopedModel):
    """Configurable, explainable rule defining risk thresholds."""

    __tablename__ = "student_success_early_warning_rules"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ewr_tenant_code"),
        Index("ix_ewr_tenant_category_active", "tenant_id", "category", "is_active"),
        Index("ix_ewr_tenant_dept_active", "tenant_id", "department_id", "is_active"),
    )

    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(
        String(64), default=EarlyWarningCategory.ATTENDANCE, nullable=False
    )
    operator: Mapped[str] = mapped_column(
        String(32), default=ComparisonOperator.LESS_THAN, nullable=False
    )
    threshold_value: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    evaluation_window_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)

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
    academic_term_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("examination_terms.id", ondelete="SET NULL"),
        nullable=True,
    )

    severity: Mapped[str] = mapped_column(
        String(32), default=WarningSeverity.HIGH, nullable=False
    )
    recommended_intervention_category: Mapped[str] = mapped_column(
        String(64), default=InterventionType.ATTENDANCE_FOLLOWUP, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    current_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Relationships
    department: Mapped["Department | None"] = relationship("Department")
    program: Mapped["Program | None"] = relationship("Program")
    academic_term: Mapped["ExamTerm | None"] = relationship("ExamTerm")
    versions: Mapped[list["EarlyWarningRuleVersion"]] = relationship(
        "EarlyWarningRuleVersion", back_populates="rule", cascade="all, delete-orphan"
    )
    evaluations: Mapped[list["EarlyWarningEvaluation"]] = relationship(
        "EarlyWarningEvaluation", back_populates="rule"
    )
    signals: Mapped[list["EarlyWarningSignal"]] = relationship(
        "EarlyWarningSignal", back_populates="rule"
    )


class EarlyWarningRuleVersion(TenantScopedModel):
    """Audit history of threshold or parameter changes to a rule."""

    __tablename__ = "student_success_early_warning_rule_versions"
    __table_args__ = (
        UniqueConstraint("rule_id", "version_number", name="uq_ewrv_rule_version"),
        Index("ix_ewrv_rule", "rule_id"),
    )

    rule_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("student_success_early_warning_rules.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    operator: Mapped[str] = mapped_column(String(32), nullable=False)
    threshold_value: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    evaluation_window_days: Mapped[int] = mapped_column(Integer, nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    changed_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    change_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    rule: Mapped["EarlyWarningRule"] = relationship(
        "EarlyWarningRule", back_populates="versions"
    )
    changed_by: Mapped["User | None"] = relationship("User")


class EarlyWarningEvaluation(TenantScopedModel):
    """Batch or event-triggered execution run of early warning rules."""

    __tablename__ = "student_success_early_warning_evaluations"
    __table_args__ = (
        Index("ix_ewe_tenant_rule", "tenant_id", "rule_id"),
        Index("ix_ewe_timestamp", "evaluation_timestamp"),
    )

    rule_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("student_success_early_warning_rules.id", ondelete="RESTRICT"),
        nullable=False,
    )
    evaluation_scope: Mapped[str] = mapped_column(
        String(64), default=EvaluationScope.ALL_STUDENTS, nullable=False
    )
    scope_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    evaluation_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    triggered_by: Mapped[str] = mapped_column(
        String(64), default=EvaluationTrigger.SCHEDULED_JOB, nullable=False
    )
    students_evaluated_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    warnings_generated_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=EvaluationStatus.COMPLETED, nullable=False
    )
    execution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    rule: Mapped["EarlyWarningRule"] = relationship(
        "EarlyWarningRule", back_populates="evaluations"
    )
    signals: Mapped[list["EarlyWarningSignal"]] = relationship(
        "EarlyWarningSignal", back_populates="evaluation"
    )


class EarlyWarningSignal(TenantScopedModel):
    """Explainable risk alert instance generated for a student."""

    __tablename__ = "student_success_early_warning_signals"
    __table_args__ = (
        UniqueConstraint("tenant_id", "signal_code", name="uq_ews_tenant_signal_code"),
        Index(
            "ix_ews_tenant_student_status",
            "tenant_id",
            "student_id",
            "status",
        ),
        Index("ix_ews_tenant_rule_status", "tenant_id", "rule_id", "status"),
        Index("ix_ews_tenant_severity", "tenant_id", "severity"),
        Index("ix_ews_tenant_created", "tenant_id", "created_at"),
    )

    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    rule_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("student_success_early_warning_rules.id", ondelete="RESTRICT"),
        nullable=False,
    )
    rule_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    evaluation_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("student_success_early_warning_evaluations.id", ondelete="SET NULL"),
        nullable=True,
    )
    signal_code: Mapped[str] = mapped_column(String(64), nullable=False)
    observation_period_start: Mapped[date] = mapped_column(Date, nullable=False)
    observation_period_end: Mapped[date] = mapped_column(Date, nullable=False)
    metric_observed_value: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    threshold_condition: Mapped[str] = mapped_column(String(128), nullable=False)
    source_record_references: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, nullable=False
    )
    severity: Mapped[str] = mapped_column(
        String(32), default=WarningSeverity.HIGH, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), default=EarlyWarningSignalStatus.NEWLY_DETECTED, nullable=False
    )

    dismissal_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_false_positive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    acknowledged_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    success_case_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("student_success_cases.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    student: Mapped["StudentProfile"] = relationship("StudentProfile")
    rule: Mapped["EarlyWarningRule"] = relationship(
        "EarlyWarningRule", back_populates="signals"
    )
    evaluation: Mapped["EarlyWarningEvaluation | None"] = relationship(
        "EarlyWarningEvaluation", back_populates="signals"
    )
    acknowledged_by: Mapped["User | None"] = relationship(
        "User", foreign_keys=[acknowledged_by_user_id]
    )
    success_case: Mapped["StudentSuccessCase | None"] = relationship(
        "StudentSuccessCase", back_populates="warning_signals"
    )
    interventions: Mapped[list["InterventionPlan"]] = relationship(
        "InterventionPlan", back_populates="warning_signal"
    )


class InterventionPlan(TenantScopedModel):
    """Targeted intervention workflow and outcome tracking."""

    __tablename__ = "student_success_intervention_plans"
    __table_args__ = (
        Index("ix_ip_tenant_student_status", "tenant_id", "student_id", "status"),
        Index("ix_ip_tenant_case", "tenant_id", "case_id"),
        Index("ix_ip_tenant_assigned_status", "tenant_id", "assigned_to_user_id", "status"),
        Index("ix_ip_tenant_target_date", "tenant_id", "target_completion_date"),
    )

    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    case_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("student_success_cases.id", ondelete="SET NULL"),
        nullable=True,
    )
    warning_signal_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("student_success_early_warning_signals.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    objective: Mapped[str | None] = mapped_column(Text, nullable=True)
    intervention_type: Mapped[str] = mapped_column(
        String(64), default=InterventionType.ACADEMIC_ADVISING, nullable=False
    )
    priority: Mapped[str] = mapped_column(
        String(32), default=CasePriority.MEDIUM, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), default=InterventionStatus.PLANNED, nullable=False
    )

    assigned_to_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    planned_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    target_completion_date: Mapped[date] = mapped_column(Date, nullable=False)
    actual_completion_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    student_participation: Mapped[str] = mapped_column(
        String(32), default=StudentParticipation.SCHEDULED, nullable=False
    )
    outcome_classification: Mapped[str | None] = mapped_column(String(32), nullable=True)
    outcome_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    student: Mapped["StudentProfile"] = relationship("StudentProfile")
    case: Mapped["StudentSuccessCase | None"] = relationship(
        "StudentSuccessCase", back_populates="interventions"
    )
    warning_signal: Mapped["EarlyWarningSignal | None"] = relationship(
        "EarlyWarningSignal", back_populates="interventions"
    )
    assigned_to: Mapped["User | None"] = relationship(
        "User", foreign_keys=[assigned_to_user_id]
    )
    actions: Mapped[list["InterventionAction"]] = relationship(
        "InterventionAction", back_populates="intervention_plan", cascade="all, delete-orphan"
    )


class InterventionAction(TenantScopedModel):
    """Specific task or milestone within an intervention plan."""

    __tablename__ = "student_success_intervention_actions"
    __table_args__ = (
        Index("ix_ia_plan_status", "intervention_plan_id", "status"),
        Index("ix_ia_due_date", "tenant_id", "due_date"),
    )

    intervention_plan_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("student_success_intervention_plans.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    completed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default=ActionItemStatus.PENDING, nullable=False
    )
    is_student_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    completion_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    intervention_plan: Mapped["InterventionPlan"] = relationship(
        "InterventionPlan", back_populates="actions"
    )


class AdvisingAppointment(TenantScopedModel):
    """Student-advisor meeting record, scheduling, and conflict prevention."""

    __tablename__ = "student_success_advising_appointments"
    __table_args__ = (
        Index(
            "ix_saa_tenant_advisor_time",
            "tenant_id",
            "advisor_id",
            "scheduled_start_time",
            "scheduled_end_time",
        ),
        Index("ix_saa_tenant_student_time", "tenant_id", "student_id", "scheduled_start_time"),
        Index("ix_saa_tenant_status", "tenant_id", "status"),
    )

    advisor_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("student_success_advisor_profiles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    case_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("student_success_cases.id", ondelete="SET NULL"),
        nullable=True,
    )

    scheduled_start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    scheduled_end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    meeting_mode: Mapped[str] = mapped_column(
        String(32), default=AppointmentMode.IN_PERSON, nullable=False
    )
    location_or_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    agenda: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default=AppointmentStatus.REQUESTED, nullable=False
    )

    # Privacy Separation: Internal advisor meeting notes vs. Agreed Action Summary shared with student
    meeting_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    agreed_action_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    advisor: Mapped["AdvisorProfile"] = relationship(
        "AdvisorProfile", back_populates="appointments"
    )
    student: Mapped["StudentProfile"] = relationship("StudentProfile")
    case: Mapped["StudentSuccessCase | None"] = relationship(
        "StudentSuccessCase", back_populates="appointments"
    )
