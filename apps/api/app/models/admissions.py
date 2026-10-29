"""SQLAlchemy Entities for CampusOS Student Admissions, Enrollment & Onboarding Orchestration (Step 48).

Tagline: "One Campus. One System. One Source of Truth."

Entities:
- AdmissionCycle: Configurable admission cycles per academic year with application windows and deadline policies.
- ApplicantProfile: Prospective student applicant identity, contact details, duplicate detection & merging.
- AdmissionApplication: Formal admission applications with program choices, category, timestamps, and state machine.
- ApplicationProgramChoice: Ranked program preferences for an application.
- ApplicationDocumentRequirement: Required evidence definitions by cycle or program.
- ApplicationDocument: Uploaded evidence metadata, verification status, and reviewer notes.
- EligibilityRule: Configurable eligibility thresholds, qualifying exam minimums, and versioning.
- EligibilityEvaluation: Explainable evaluation execution results with observed scores.
- ApplicationReview: Reviewer assignments, review stages, scores, and decisions.
- SeatAllocation: Program and quota capacity management with concurrency-safe allocation.
- SelectionRun: Selection and merit-list generation rounds with publishing workflow.
- SelectionResult: Individual applicant merit rank, score, and selection outcome.
- AdmissionOffer: Generated offers with expiry deadlines, stipulations, and deposit requirements.
- EnrollmentWorkflow: Idempotent student-record creation connecting accepted offers to canonical StudentProfile.
- OnboardingChecklist: Post-enrollment institutional onboarding task coordination.
- OnboardingTask: Specific onboarding tasks (profile, documents, finance, orientation) with completion tracking.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    JSON,
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
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantScopedModel

JSONB_COMPAT = JSON().with_variant(JSONB, "postgresql")


# -----------------------------------------------------------------------------
# 1. Enums
# -----------------------------------------------------------------------------


class AdmissionCycleStatus(StrEnum):
    """Lifecycle status for an admission cycle."""

    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    CLOSED = "CLOSED"
    ARCHIVED = "ARCHIVED"


class ApplicantVerificationStatus(StrEnum):
    """Verification status of an applicant identity."""

    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    FLAGGED_DUPLICATE = "FLAGGED_DUPLICATE"


class ApplicationStatus(StrEnum):
    """Comprehensive state-machine for admission applications."""

    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    DOCUMENTS_PENDING = "DOCUMENTS_PENDING"
    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"
    SHORTLISTED = "SHORTLISTED"
    WAITLISTED = "WAITLISTED"
    OFFERED = "OFFERED"
    OFFER_ACCEPTED = "OFFER_ACCEPTED"
    OFFER_DECLINED = "OFFER_DECLINED"
    OFFER_EXPIRED = "OFFER_EXPIRED"
    ENROLLED = "ENROLLED"
    WITHDRAWN = "WITHDRAWN"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class DocumentVerificationStatus(StrEnum):
    """Verification state of an uploaded applicant document."""

    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    RESUBMISSION_REQUESTED = "RESUBMISSION_REQUESTED"


class ReviewDecision(StrEnum):
    """Reviewer recommendation or committee decision."""

    PENDING = "PENDING"
    RECOMMEND_ADMIT = "RECOMMEND_ADMIT"
    RECOMMEND_REJECT = "RECOMMEND_REJECT"
    HOLD = "HOLD"
    REQUEST_INFO = "REQUEST_INFO"


class ReviewStage(StrEnum):
    """Stage in the multi-tier review workflow."""

    ACADEMIC_REVIEW = "ACADEMIC_REVIEW"
    DOCUMENT_VERIFICATION = "DOCUMENT_VERIFICATION"
    COMMITTEE_APPROVAL = "COMMITTEE_APPROVAL"
    INTERVIEW = "INTERVIEW"


class SelectionStatus(StrEnum):
    """Selection outcome for an applicant on a merit run."""

    SELECTED = "SELECTED"
    WAITLISTED = "WAITLISTED"
    NOT_SELECTED = "NOT_SELECTED"


class OfferStatus(StrEnum):
    """Lifecycle state of an admission offer."""

    ISSUED = "ISSUED"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class EnrollmentWorkflowStatus(StrEnum):
    """Status of the idempotent enrollment workflow."""

    INITIATED = "INITIATED"
    IDENTITY_VALIDATED = "IDENTITY_VALIDATED"
    DOCUMENTS_CONFIRMED = "DOCUMENTS_CONFIRMED"
    FEES_VERIFIED = "FEES_VERIFIED"
    STUDENT_RECORD_CREATED = "STUDENT_RECORD_CREATED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"


class OnboardingStatus(StrEnum):
    """Status of an onboarding checklist or individual task."""

    NOT_STARTED = "NOT_STARTED"
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    WAIVED = "WAIVED"


class OnboardingTaskCategory(StrEnum):
    """Functional category for student onboarding tasks."""

    PROFILE_VERIFICATION = "PROFILE_VERIFICATION"
    DOCUMENT_SUBMISSION = "DOCUMENT_SUBMISSION"
    FINANCE_SETTLEMENT = "FINANCE_SETTLEMENT"
    ORIENTATION = "ORIENTATION"
    ACADEMIC_ADVISING = "ACADEMIC_ADVISING"
    CAMPUS_FACILITIES = "CAMPUS_FACILITIES"
    ADMINISTRATIVE = "ADMINISTRATIVE"


# -----------------------------------------------------------------------------
# 2. Database Entities
# -----------------------------------------------------------------------------


class AdmissionCycle(TenantScopedModel):
    """Configurable admission cycle per institution and academic year."""

    __tablename__ = "admissions_cycles"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_admissions_cycles_tenant_code"),
        Index("idx_adm_cycle_tenant_status", "tenant_id", "status"),
        Index("idx_adm_cycle_tenant_dates", "tenant_id", "application_start_date", "application_end_date"),
    )

    academic_year_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_academic_years.id", ondelete="RESTRICT"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)  # e.g., "AY2026-UG-FALL"
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    admission_term: Mapped[str] = mapped_column(String(32), default="FALL", nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=AdmissionCycleStatus.DRAFT, nullable=False
    )
    application_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    application_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    document_deadline: Mapped[date] = mapped_column(Date, nullable=False)
    offer_acceptance_deadline: Mapped[date] = mapped_column(Date, nullable=False)
    publication_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    settings: Mapped[dict | None] = mapped_column(JSONB_COMPAT, nullable=True)

    # Aggregate Counters
    total_applications_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_enrolled_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    academic_year: Mapped["AcademicYear"] = relationship("AcademicYear")  # noqa: F821
    applications: Mapped[list["AdmissionApplication"]] = relationship(
        "AdmissionApplication", back_populates="cycle", cascade="all, delete-orphan"
    )
    seat_allocations: Mapped[list["SeatAllocation"]] = relationship(
        "SeatAllocation", back_populates="cycle", cascade="all, delete-orphan"
    )


class ApplicantProfile(TenantScopedModel):
    """Prospective student applicant identity, contact details, and merge tracking."""

    __tablename__ = "admissions_applicants"
    __table_args__ = (
        UniqueConstraint("tenant_id", "applicant_number", name="uq_admissions_applicants_number"),
        Index("idx_adm_applicant_tenant_email", "tenant_id", "email"),
        Index("idx_adm_applicant_tenant_phone", "tenant_id", "phone_number"),
    )

    applicant_number: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g. "APP-2026-0001"
    user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(32), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(String(16), nullable=False)  # MALE, FEMALE, OTHER
    nationality: Mapped[str] = mapped_column(String(64), default="Indian", nullable=False)
    address_line1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    country: Mapped[str] = mapped_column(String(100), default="India", nullable=False)
    emergency_contact_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)

    verification_status: Mapped[str] = mapped_column(
        String(32), default=ApplicantVerificationStatus.PENDING_VERIFICATION, nullable=False
    )
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    merged_into_applicant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("admissions_applicants.id", ondelete="SET NULL"),
        nullable=True,
    )
    merge_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    merged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User | None"] = relationship("User")  # noqa: F821
    applications: Mapped[list["AdmissionApplication"]] = relationship(
        "AdmissionApplication", back_populates="applicant"
    )


class AdmissionApplication(TenantScopedModel):
    """Formal admission application for an admission cycle and program."""

    __tablename__ = "admissions_applications"
    __table_args__ = (
        UniqueConstraint("tenant_id", "application_number", name="uq_admissions_app_number"),
        Index("idx_adm_app_tenant_cycle", "tenant_id", "cycle_id"),
        Index("idx_adm_app_tenant_applicant", "tenant_id", "applicant_id"),
        Index("idx_adm_app_tenant_status", "tenant_id", "status"),
        Index("idx_adm_app_tenant_program", "tenant_id", "program_id"),
    )

    cycle_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("admissions_cycles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    applicant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("admissions_applicants.id", ondelete="RESTRICT"),
        nullable=False,
    )
    application_number: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g. "ADM-2026-0001"
    program_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_programs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="SET NULL"),
        nullable=True,
    )
    admission_category: Mapped[str] = mapped_column(
        String(32), default="GENERAL", nullable=False
    )  # GENERAL, MANAGEMENT, GOVERNMENT, NRI, MERIT, SPORTS
    status: Mapped[str] = mapped_column(
        String(32), default=ApplicationStatus.DRAFT, nullable=False
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    correction_window_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Academic Qualifying Data
    qualifying_exam_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    qualifying_exam_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    qualifying_exam_max_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    qualifying_percentage: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)

    # Fee / Payment Tracking
    application_fee_paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    payment_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Withdrawal and Reopening
    withdrawal_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reopened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reopened_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reopening_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    cycle: Mapped["AdmissionCycle"] = relationship("AdmissionCycle", back_populates="applications")
    applicant: Mapped["ApplicantProfile"] = relationship("ApplicantProfile", back_populates="applications")
    program: Mapped["Program"] = relationship("Program")  # noqa: F821
    campus: Mapped["Campus | None"] = relationship("Campus")  # noqa: F821
    program_choices: Mapped[list["ApplicationProgramChoice"]] = relationship(
        "ApplicationProgramChoice", back_populates="application", cascade="all, delete-orphan"
    )
    documents: Mapped[list["ApplicationDocument"]] = relationship(
        "ApplicationDocument", back_populates="application", cascade="all, delete-orphan"
    )
    reviews: Mapped[list["ApplicationReview"]] = relationship(
        "ApplicationReview", back_populates="application", cascade="all, delete-orphan"
    )
    offers: Mapped[list["AdmissionOffer"]] = relationship(
        "AdmissionOffer", back_populates="application", cascade="all, delete-orphan"
    )


class ApplicationProgramChoice(TenantScopedModel):
    """Ranked alternative program preferences on an application."""

    __tablename__ = "admissions_program_choices"
    __table_args__ = (
        UniqueConstraint("application_id", "preference_rank", name="uq_app_choice_rank"),
        Index("idx_adm_choice_app_rank", "application_id", "preference_rank"),
    )

    application_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("admissions_applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    program_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_programs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="SET NULL"),
        nullable=True,
    )
    preference_rank: Mapped[int] = mapped_column(Integer, nullable=False)  # 1, 2, 3
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    application: Mapped["AdmissionApplication"] = relationship("AdmissionApplication", back_populates="program_choices")
    program: Mapped["Program"] = relationship("Program")  # noqa: F821


class ApplicationDocumentRequirement(TenantScopedModel):
    """Configurable required evidence definitions by cycle or program."""

    __tablename__ = "admissions_document_requirements"
    __table_args__ = (
        Index("idx_adm_doc_req_tenant_cycle", "tenant_id", "cycle_id"),
        Index("idx_adm_doc_req_tenant_prog", "tenant_id", "program_id"),
    )

    cycle_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("admissions_cycles.id", ondelete="CASCADE"),
        nullable=True,
    )
    program_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_programs.id", ondelete="CASCADE"),
        nullable=True,
    )
    document_name: Mapped[str] = mapped_column(String(128), nullable=False)  # e.g. "10th Marksheet"
    document_code: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g. "DOC_10TH_MARKS"
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ApplicationDocument(TenantScopedModel):
    """Uploaded evidence metadata, verification status, and reviewer feedback."""

    __tablename__ = "admissions_documents"
    __table_args__ = (
        Index("idx_adm_doc_tenant_app", "tenant_id", "application_id"),
        Index("idx_adm_doc_tenant_status", "tenant_id", "verification_status"),
    )

    application_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("admissions_applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    requirement_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("admissions_document_requirements.id", ondelete="SET NULL"),
        nullable=True,
    )
    document_name: Mapped[str] = mapped_column(String(128), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), default="application/pdf", nullable=False)
    storage_key: Mapped[str] = mapped_column(String(255), nullable=False)  # Reference to storage record

    verification_status: Mapped[str] = mapped_column(
        String(32), default=DocumentVerificationStatus.PENDING, nullable=False
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    verified_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    application: Mapped["AdmissionApplication"] = relationship("AdmissionApplication", back_populates="documents")


class AdmissionEligibilityRule(TenantScopedModel):
    """Configurable eligibility thresholds, qualifying exam minimums, and versioning."""

    __tablename__ = "admissions_eligibility_rules"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_admissions_elig_rule_code"),
        Index("idx_adm_elig_tenant_cycle_prog", "tenant_id", "cycle_id", "program_id"),
    )

    cycle_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("admissions_cycles.id", ondelete="CASCADE"),
        nullable=True,
    )
    program_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_programs.id", ondelete="CASCADE"),
        nullable=True,
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g., "ELIG_ENGG_2026"
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    min_score_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("50.00"), nullable=False)
    required_qualification: Mapped[str | None] = mapped_column(String(128), nullable=True)
    rule_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criteria_json: Mapped[dict | None] = mapped_column(JSONB_COMPAT, nullable=True)


EligibilityRule = AdmissionEligibilityRule


class EligibilityEvaluation(TenantScopedModel):
    """Explainable automated evaluation execution results."""

    __tablename__ = "admissions_eligibility_evaluations"
    __table_args__ = (
        Index("idx_adm_eval_tenant_app", "tenant_id", "application_id"),
    )

    application_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("admissions_applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    rule_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("admissions_eligibility_rules.id", ondelete="RESTRICT"),
        nullable=False,
    )
    rule_version: Mapped[int] = mapped_column(Integer, nullable=False)
    is_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False)
    observed_percentage: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    evaluation_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    evaluated_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    rule: Mapped["AdmissionEligibilityRule"] = relationship("AdmissionEligibilityRule")


class ApplicationReview(TenantScopedModel):
    """Reviewer evaluation, multi-stage notes, scoring, and recommendation."""

    __tablename__ = "admissions_reviews"
    __table_args__ = (
        Index("idx_adm_review_tenant_app", "tenant_id", "application_id"),
        Index("idx_adm_review_tenant_reviewer", "tenant_id", "reviewer_user_id"),
    )

    application_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("admissions_applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    reviewer_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    review_stage: Mapped[str] = mapped_column(
        String(32), default=ReviewStage.ACADEMIC_REVIEW, nullable=False
    )
    score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    decision: Mapped[str] = mapped_column(
        String(32), default=ReviewDecision.PENDING, nullable=False
    )
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)  # Staff only
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    application: Mapped["AdmissionApplication"] = relationship("AdmissionApplication", back_populates="reviews")
    reviewer: Mapped["User"] = relationship("User")  # noqa: F821


class SeatAllocation(TenantScopedModel):
    """Program and category admission seat capacity with concurrency-safe allocation."""

    __tablename__ = "admissions_seat_allocations"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "cycle_id",
            "program_id",
            "campus_id",
            "admission_category",
            name="uq_admissions_seat_alloc_composite",
        ),
        Index("idx_adm_seat_tenant_cycle_prog", "tenant_id", "cycle_id", "program_id"),
    )

    cycle_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("admissions_cycles.id", ondelete="CASCADE"),
        nullable=False,
    )
    program_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_programs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="SET NULL"),
        nullable=True,
    )
    admission_category: Mapped[str] = mapped_column(
        String(32), default="GENERAL", nullable=False
    )
    total_capacity: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    reserved_seats: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # Held by active offers
    confirmed_seats: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # Enrolled
    waitlist_capacity: Mapped[int] = mapped_column(Integer, default=30, nullable=False)

    cycle: Mapped["AdmissionCycle"] = relationship("AdmissionCycle", back_populates="seat_allocations")
    program: Mapped["Program"] = relationship("Program")  # noqa: F821


class SelectionRun(TenantScopedModel):
    """Selection round and merit list generation."""

    __tablename__ = "admissions_selection_runs"
    __table_args__ = (
        Index("idx_adm_sel_tenant_cycle_prog", "tenant_id", "cycle_id", "program_id"),
    )

    cycle_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("admissions_cycles.id", ondelete="CASCADE"),
        nullable=False,
    )
    program_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_programs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    run_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)  # e.g., "Round 1 Merit List"
    cutoff_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    total_selected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_waitlisted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    approved_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    results: Mapped[list["SelectionResult"]] = relationship(
        "SelectionResult", back_populates="selection_run", cascade="all, delete-orphan"
    )


class SelectionResult(TenantScopedModel):
    """Individual applicant merit rank, score, and seat allocation result."""

    __tablename__ = "admissions_selection_results"
    __table_args__ = (
        UniqueConstraint("selection_run_id", "application_id", name="uq_adm_sel_run_app"),
        Index("idx_adm_sel_res_tenant_run", "tenant_id", "selection_run_id"),
        Index("idx_adm_sel_res_tenant_app", "tenant_id", "application_id"),
    )

    selection_run_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("admissions_selection_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    application_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("admissions_applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    applicant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("admissions_applicants.id", ondelete="CASCADE"),
        nullable=False,
    )
    merit_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    merit_score: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=SelectionStatus.SELECTED, nullable=False
    )
    waitlist_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    seat_offered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    selection_run: Mapped["SelectionRun"] = relationship("SelectionRun", back_populates="results")
    application: Mapped["AdmissionApplication"] = relationship("AdmissionApplication")


class AdmissionOffer(TenantScopedModel):
    """Formal admission offer extended to an applicant."""

    __tablename__ = "admissions_offers"
    __table_args__ = (
        UniqueConstraint("tenant_id", "offer_number", name="uq_admissions_offers_number"),
        Index("idx_adm_offer_tenant_app", "tenant_id", "application_id"),
        Index("idx_adm_offer_tenant_status", "tenant_id", "status"),
        Index("idx_adm_offer_tenant_expiry", "tenant_id", "expiry_date", "status"),
    )

    application_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("admissions_applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    applicant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("admissions_applicants.id", ondelete="RESTRICT"),
        nullable=False,
    )
    program_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_programs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    cycle_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("admissions_cycles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    offer_number: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g. "OFR-2026-0001"
    offer_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False)
    deposit_required: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    conditions_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default=OfferStatus.ISSUED, nullable=False
    )
    response_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decline_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    revocation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    revoked_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    application: Mapped["AdmissionApplication"] = relationship("AdmissionApplication", back_populates="offers")
    program: Mapped["Program"] = relationship("Program")  # noqa: F821


class EnrollmentWorkflow(TenantScopedModel):
    """Idempotent enrollment orchestration connecting accepted offers to canonical student profiles."""

    __tablename__ = "admissions_enrollment_workflows"
    __table_args__ = (
        UniqueConstraint("tenant_id", "workflow_number", name="uq_admissions_enr_wf_number"),
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_admissions_enr_idempotency"),
        Index("idx_adm_enr_tenant_app", "tenant_id", "application_id"),
        Index("idx_adm_enr_tenant_offer", "tenant_id", "offer_id"),
        Index("idx_adm_enr_tenant_student", "tenant_id", "student_id"),
    )

    application_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("admissions_applications.id", ondelete="RESTRICT"),
        nullable=False,
    )
    offer_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("admissions_offers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    applicant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("admissions_applicants.id", ondelete="RESTRICT"),
        nullable=False,
    )
    student_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="SET NULL"),
        nullable=True,
    )
    workflow_number: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g. "ENR-2026-0001"
    batch_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_batches.id", ondelete="RESTRICT"),
        nullable=False,
    )
    current_semester_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_semesters.id", ondelete="RESTRICT"),
        nullable=True,
    )
    current_section_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_sections.id", ondelete="RESTRICT"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32), default=EnrollmentWorkflowStatus.INITIATED, nullable=False
    )
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    failure_stage: Mapped[str | None] = mapped_column(String(64), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_student_admission_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    student: Mapped["StudentProfile | None"] = relationship("StudentProfile")  # noqa: F821
    application: Mapped["AdmissionApplication"] = relationship("AdmissionApplication")
    offer: Mapped["AdmissionOffer"] = relationship("AdmissionOffer")


class OnboardingChecklist(TenantScopedModel):
    """Institutional onboarding checklist created post-enrollment."""

    __tablename__ = "admissions_onboarding_checklists"
    __table_args__ = (
        UniqueConstraint("tenant_id", "student_id", name="uq_adm_onboarding_student"),
        Index("idx_adm_onboarding_tenant_status", "tenant_id", "status"),
    )

    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="CASCADE"),
        nullable=False,
    )
    enrollment_workflow_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("admissions_enrollment_workflows.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=OnboardingStatus.IN_PROGRESS, nullable=False
    )
    total_tasks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_tasks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    target_completion_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    student: Mapped["StudentProfile"] = relationship("StudentProfile")  # noqa: F821
    tasks: Mapped[list["OnboardingTask"]] = relationship(
        "OnboardingTask", back_populates="checklist", cascade="all, delete-orphan"
    )


class OnboardingTask(TenantScopedModel):
    """Specific verifiable onboarding action item."""

    __tablename__ = "admissions_onboarding_tasks"
    __table_args__ = (
        Index("idx_adm_onboarding_task_tenant_checklist", "tenant_id", "checklist_id"),
        Index("idx_adm_onboarding_task_tenant_status", "tenant_id", "status"),
    )

    checklist_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("admissions_onboarding_checklists.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    task_category: Mapped[str] = mapped_column(
        String(32), default=OnboardingTaskCategory.ADMINISTRATIVE, nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default=OnboardingStatus.PENDING, nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    verification_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    checklist: Mapped["OnboardingChecklist"] = relationship("OnboardingChecklist", back_populates="tasks")
