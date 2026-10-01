"""Placement and Career Engine Models.

Authoritative domain models for corporate partners, recruitment drives,
job positions, configurable eligibility evaluation rules, eligibility snapshots,
student placement profiles, applications with status history, interview rounds,
schedules, evaluations, formal offers, and institutional placement outcomes.
"""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, BaseModel, TenantScopedModel

# Cross-dialect JSON type for PostgreSQL JSONB and SQLite JSON
JSONType = JSON().with_variant(JSONB, "postgresql")


class Company(TenantScopedModel):
    """Corporate recruitment partner profile."""

    __tablename__ = "placement_companies"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_placement_companies_tenant_name"),
        Index("ix_placement_companies_tenant_status", "tenant_id", "status"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    legal_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    industry: Mapped[str] = mapped_column(String(128), nullable=False)  # IT, Banking, Core Engineering, EdTech, etc.
    company_type: Mapped[str] = mapped_column(
        String(64), default="PRODUCT", nullable=False
    )  # PRODUCT, SERVICE, STARTUP, MNC, PSU, GOVT, OTHER
    tier: Mapped[str] = mapped_column(
        String(32), default="TIER_1", nullable=False
    )  # DREAM, SUPER_DREAM, TIER_1, TIER_2, MASS
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    headquarters_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default="ACTIVE", nullable=False
    )  # PROSPECT, ACTIVE, INACTIVE, BLACKLISTED, ARCHIVED

    contacts: Mapped[list["CompanyContact"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    drives: Mapped[list["JobDrive"]] = relationship(
        back_populates="company"
    )
    offers: Mapped[list["PlacementOffer"]] = relationship(
        back_populates="company"
    )


class CompanyContact(BaseModel):
    """HR recruiter or coordinator contact for a company."""

    __tablename__ = "placement_contacts"
    __table_args__ = (
        Index("ix_placement_contacts_company", "company_id"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("placement_companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    designation: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)

    company: Mapped["Company"] = relationship(back_populates="contacts")


class JobDrive(TenantScopedModel):
    """Campus recruitment event/process organized around a corporate partner."""

    __tablename__ = "placement_drives"
    __table_args__ = (
        UniqueConstraint("tenant_id", "drive_code", name="uq_placement_drives_tenant_code"),
        Index("ix_placement_drives_tenant_status", "tenant_id", "status"),
        Index("ix_placement_drives_tenant_year", "tenant_id", "academic_year_id"),
    )

    company_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("placement_companies.id", ondelete="RESTRICT"),
        nullable=False,
    )
    academic_year_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_academic_years.id", ondelete="RESTRICT"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    drive_code: Mapped[str] = mapped_column(String(64), nullable=False)  # DRV-2026-000001
    application_open_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    application_close_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    drive_date: Mapped[date] = mapped_column(Date, nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mode: Mapped[str] = mapped_column(
        String(32), default="ON_CAMPUS", nullable=False
    )  # ON_CAMPUS, OFF_CAMPUS, VIRTUAL, HYBRID
    status: Mapped[str] = mapped_column(
        String(32), default="DRAFT", nullable=False
    )  # DRAFT, PUBLISHED, APPLICATIONS_OPEN, APPLICATIONS_CLOSED, SHORTLISTING, INTERVIEWING, OFFERS, CLOSED, CANCELLED
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    company: Mapped["Company"] = relationship(back_populates="drives")
    positions: Mapped[list["JobPosition"]] = relationship(
        back_populates="drive", cascade="all, delete-orphan"
    )


class JobPosition(BaseModel):
    """Specific employment role being offered through a recruitment drive."""

    __tablename__ = "placement_positions"
    __table_args__ = (
        Index("ix_placement_positions_drive", "job_drive_id"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    job_drive_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("placement_drives.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(128), nullable=False)  # Software Engineer, Data Analyst
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    employment_type: Mapped[str] = mapped_column(
        String(32), default="FULL_TIME", nullable=False
    )  # FULL_TIME, PART_TIME, CONTRACT, INTERNSHIP, INTERNSHIP_TO_FULL_TIME
    work_location: Mapped[str | None] = mapped_column(String(128), nullable=True)
    vacancy_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    salary_min: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    salary_max: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    ctc: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)  # Annual CTC in INR (e.g. 1200000.00)
    skills_json: Mapped[dict | list | None] = mapped_column(JSONType, nullable=True)  # ["Python", "SQL", "React"]
    qualification: Mapped[str | None] = mapped_column(String(255), nullable=True)  # B.Tech / M.Tech
    experience_requirement: Mapped[str | None] = mapped_column(String(128), nullable=True)  # Freshers / 0-1 yr
    joining_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default="OPEN", nullable=False
    )  # OPEN, CLOSED, ON_HOLD, CANCELLED

    drive: Mapped["JobDrive"] = relationship(back_populates="positions")
    eligibility_rules: Mapped[list["EligibilityRule"]] = relationship(
        back_populates="position", cascade="all, delete-orphan", order_by="EligibilityRule.sequence"
    )
    applications: Mapped[list["PlacementApplication"]] = relationship(
        back_populates="position"
    )
    rounds: Mapped[list["InterviewRound"]] = relationship(
        back_populates="position", cascade="all, delete-orphan", order_by="InterviewRound.sequence"
    )


class EligibilityRule(BaseModel):
    """Configurable domain rule governing placement participation eligibility."""

    __tablename__ = "placement_eligibility_rules"
    __table_args__ = (
        Index("ix_placement_elig_rules_position", "job_position_id"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    job_position_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("placement_positions.id", ondelete="CASCADE"),
        nullable=False,
    )
    rule_type: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # CGPA_MINIMUM, CGPA_MAXIMUM, BACKLOG_MAXIMUM, BACKLOG_NONE, ATTENDANCE_MINIMUM,
       # PROGRAM_ALLOWED, PROGRAM_EXCLUDED, DEPARTMENT_ALLOWED, DEPARTMENT_EXCLUDED,
       # GRADUATION_YEAR, SEMESTER_STATUS, FEE_CLEARANCE, CUSTOM_INSTITUTION_RULE
    operator: Mapped[str] = mapped_column(
        String(16), default="GTE", nullable=False
    )  # GTE, LTE, EQ, NEQ, IN, NOT_IN
    value_json: Mapped[dict | list | str | int | float | bool] = mapped_column(
        JSONType, nullable=False
    )  # "7.5", 0, ["CSE", "AI_DS"], 2027, true
    metadata_json: Mapped[dict | list | None] = mapped_column(JSONType, nullable=True)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    position: Mapped["JobPosition"] = relationship(back_populates="eligibility_rules")


class StudentEligibilitySnapshot(BaseModel):
    """Historically reproducible snapshot of an eligibility decision for a student and position."""

    __tablename__ = "placement_eligibility_snapshots"
    __table_args__ = (
        UniqueConstraint("job_position_id", "student_id", name="uq_placement_snapshot_pos_student"),
        Index("ix_placement_snapshots_student", "student_id"),
        Index("ix_placement_snapshots_position", "job_position_id"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    job_position_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("placement_positions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    is_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    evaluated_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    rule_results_json: Mapped[list | dict] = mapped_column(
        JSONType, nullable=False
    )  # [{"rule_type": "CGPA_MINIMUM", "expected": ">= 7.5", "actual": "8.1", "passed": true}]
    source_data_snapshot_json: Mapped[dict] = mapped_column(
        JSONType, nullable=False
    )  # {"cgpa": "8.1", "active_backlogs": 0, "attendance_percent": "84.5", "fee_cleared": true}

    student = relationship("StudentProfile")
    position = relationship("JobPosition")


class StudentPlacementProfile(TenantScopedModel):
    """Placement-specific career metadata extending the canonical Student entity."""

    __tablename__ = "placement_student_profiles"
    __table_args__ = (
        UniqueConstraint("tenant_id", "student_id", name="uq_placement_student_profile"),
        Index("ix_placement_student_profiles_tenant_student", "tenant_id", "student_id"),
    )

    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    career_objective: Mapped[str | None] = mapped_column(Text, nullable=True)
    preferred_locations_json: Mapped[list | None] = mapped_column(JSONType, nullable=True)  # ["Bangalore", "Chennai"]
    preferred_roles_json: Mapped[list | None] = mapped_column(JSONType, nullable=True)  # ["Backend Developer"]
    skills_json: Mapped[list | None] = mapped_column(JSONType, nullable=True)  # ["Python", "Docker", "FastAPI"]
    certifications_json: Mapped[list | None] = mapped_column(JSONType, nullable=True)  # [{"name": "AWS CCP", "year": 2026}]
    portfolio_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    github_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resume_document_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    profile_completion_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=0.00, nullable=False
    )
    availability_status: Mapped[str] = mapped_column(
        String(32), default="AVAILABLE", nullable=False
    )  # AVAILABLE, OPTED_OUT, PLACED, HIGHER_STUDIES

    student = relationship("StudentProfile")


class PlacementApplication(TenantScopedModel):
    """Student application for a job position within a recruitment drive."""

    __tablename__ = "placement_applications"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "job_position_id", "student_id", name="uq_placement_app_position_student"
        ),
        Index("ix_placement_apps_tenant_status", "tenant_id", "status"),
        Index("ix_placement_apps_tenant_student", "tenant_id", "student_id"),
    )

    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    job_position_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("placement_positions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    eligibility_snapshot_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("placement_eligibility_snapshots.id", ondelete="SET NULL"),
        nullable=True,
    )
    application_number: Mapped[str] = mapped_column(String(64), nullable=False)  # APP-2026-000001
    status: Mapped[str] = mapped_column(
        String(32), default="APPLIED", nullable=False
    )  # DRAFT, APPLIED, SHORTLISTED, REJECTED, WITHDRAWN, INTERVIEWING, SELECTED, OFFERED, ACCEPTED, DECLINED
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    withdrawal_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    position: Mapped["JobPosition"] = relationship(back_populates="applications")
    student = relationship("StudentProfile")
    eligibility_snapshot = relationship("StudentEligibilitySnapshot")
    status_history: Mapped[list["ApplicationStatusHistory"]] = relationship(
        back_populates="application", cascade="all, delete-orphan", order_by="ApplicationStatusHistory.changed_at"
    )
    interviews: Mapped[list["InterviewSchedule"]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )
    offer: Mapped["PlacementOffer | None"] = relationship(
        back_populates="application", uselist=False
    )


class ApplicationStatusHistory(BaseModel):
    """Immutable audit trail of application lifecycle stage transitions."""

    __tablename__ = "placement_application_history"
    __table_args__ = (
        Index("ix_placement_app_history_app", "application_id"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    application_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("placement_applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    from_status: Mapped[str] = mapped_column(String(32), nullable=False)
    to_status: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    application: Mapped["PlacementApplication"] = relationship(back_populates="status_history")


class InterviewRound(BaseModel):
    """Defined selection stage in a recruitment pipeline (Aptitude, Tech, HR)."""

    __tablename__ = "placement_interview_rounds"
    __table_args__ = (
        Index("ix_placement_rounds_position", "job_position_id"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    job_position_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("placement_positions.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)  # Aptitude Test, Tech 1, HR
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sequence: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    round_type: Mapped[str] = mapped_column(
        String(32), default="TECHNICAL", nullable=False
    )  # APTITUDE, TECHNICAL, CODING, GROUP_DISCUSSION, MANAGERIAL, HR, FINAL, OTHER
    status: Mapped[str] = mapped_column(
        String(32), default="SCHEDULED", nullable=False
    )  # SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED

    position: Mapped["JobPosition"] = relationship(back_populates="rounds")
    schedules: Mapped[list["InterviewSchedule"]] = relationship(
        back_populates="round", cascade="all, delete-orphan"
    )


class InterviewSchedule(BaseModel):
    """Scheduled interview occurrence for an applicant in a specific round."""

    __tablename__ = "placement_interview_schedules"
    __table_args__ = (
        Index("ix_placement_schedules_round", "interview_round_id"),
        Index("ix_placement_schedules_app", "application_id"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    interview_round_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("placement_interview_rounds.id", ondelete="CASCADE"),
        nullable=False,
    )
    application_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("placement_applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meeting_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    interviewer: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default="SCHEDULED", nullable=False
    )  # SCHEDULED, RESCHEDULED, COMPLETED, CANCELLED, NO_SHOW

    round: Mapped["InterviewRound"] = relationship(back_populates="schedules")
    application: Mapped["PlacementApplication"] = relationship(back_populates="interviews")
    evaluation: Mapped["InterviewEvaluation | None"] = relationship(
        back_populates="schedule", uselist=False, cascade="all, delete-orphan"
    )


class InterviewEvaluation(BaseModel):
    """Performance evaluation and scoring outcome for an interview schedule."""

    __tablename__ = "placement_interview_evaluations"
    __table_args__ = (
        UniqueConstraint("interview_schedule_id", name="uq_placement_eval_schedule"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    interview_schedule_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("placement_interview_schedules.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    result: Mapped[str] = mapped_column(
        String(32), default="PASS", nullable=False
    )  # PASS, FAIL, ON_HOLD, PENDING, NO_SHOW
    score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)  # Public feedback visible to candidate
    internal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)  # Internal recruiter notes (shielded from candidate)
    recommendation: Mapped[str | None] = mapped_column(String(64), nullable=True)  # STRONG_HIRE, HIRE, NO_HIRE
    evaluated_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    schedule: Mapped["InterviewSchedule"] = relationship(back_populates="evaluation")


class PlacementOffer(TenantScopedModel):
    """Formal employment offer extended to a student with compensation and acceptance lifecycle."""

    __tablename__ = "placement_offers"
    __table_args__ = (
        UniqueConstraint("tenant_id", "offer_number", name="uq_placement_offers_tenant_num"),
        Index("ix_placement_offers_tenant_student", "tenant_id", "student_id"),
        Index("ix_placement_offers_tenant_status", "tenant_id", "status"),
    )

    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    job_position_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("placement_positions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    company_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("placement_companies.id", ondelete="RESTRICT"),
        nullable=False,
    )
    placement_application_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("placement_applications.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    offer_number: Mapped[str] = mapped_column(String(64), nullable=False)  # OFF-2026-000001
    offer_date: Mapped[date] = mapped_column(Date, nullable=False)
    designation: Mapped[str] = mapped_column(String(128), nullable=False)
    ctc: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)  # in INR
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    work_location: Mapped[str | None] = mapped_column(String(128), nullable=True)
    joining_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    employment_type: Mapped[str] = mapped_column(String(32), default="FULL_TIME", nullable=False)
    offer_expiry_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="ISSUED", nullable=False
    )  # DRAFT, ISSUED, ACCEPTED, DECLINED, EXPIRED, WITHDRAWN, CANCELLED
    document_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    declined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decline_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    company: Mapped["Company"] = relationship(back_populates="offers")
    position: Mapped["JobPosition"] = relationship()
    application: Mapped["PlacementApplication"] = relationship(back_populates="offer")
    student = relationship("StudentProfile")


class PlacementOutcome(TenantScopedModel):
    """Institutional placement milestone recorded for a student during an academic year."""

    __tablename__ = "placement_outcomes"
    __table_args__ = (
        UniqueConstraint("tenant_id", "student_id", "academic_year_id", name="uq_placement_outcomes_student_year"),
        Index("ix_placement_outcomes_tenant_outcome", "tenant_id", "outcome"),
    )

    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    academic_year_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_academic_years.id", ondelete="RESTRICT"),
        nullable=False,
    )
    outcome: Mapped[str] = mapped_column(
        String(32), default="PLACED", nullable=False
    )  # PLACED, NOT_PLACED, HIGHER_STUDIES, ENTREPRENEURSHIP, OTHER
    accepted_offer_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("placement_offers.id", ondelete="SET NULL"),
        nullable=True,
    )
    company_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("placement_companies.id", ondelete="SET NULL"),
        nullable=True,
    )
    designation: Mapped[str | None] = mapped_column(String(128), nullable=True)
    ctc: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recorded_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    student = relationship("StudentProfile")
    accepted_offer = relationship("PlacementOffer")
    company = relationship("Company")


# Aliases for compatibility
PlacementEligibilityRule = EligibilityRule
InterviewRoundResult = InterviewEvaluation

