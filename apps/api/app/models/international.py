"""SQLAlchemy Entities for Enterprise International Relations, Student Exchange & Global Mobility Management (Step 60).

Product Principle: "CampusOS — One Campus. One System. One Source of Truth."

Coordinates international institutional partnerships, Memoranda of Understanding (MoUs),
bilateral exchange agreements, study-abroad program configurations, student exchange applications,
partner nominations, inbound exchange student management, visiting scholars, faculty mobility,
academic course equivalency, credit-transfer reviews, mobility checklists, and travel funding.
"""

from datetime import UTC, date, datetime, timedelta
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
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


class PartnershipCategory(StrEnum):
    UNIVERSITY = "UNIVERSITY"
    COLLEGE = "COLLEGE"
    RESEARCH_INSTITUTE = "RESEARCH_INSTITUTE"
    PARTNER_ORGANIZATION = "PARTNER_ORGANIZATION"
    STRATEGIC = "STRATEGIC"
    BILATERAL = "BILATERAL"
    CONSORTIUM = "CONSORTIUM"
    RESEARCH = "RESEARCH"
    ERASMUS = "ERASMUS"
    MOBILITY_NETWORK = "MOBILITY_NETWORK"


class AgreementType(StrEnum):
    MOU = "MOU"
    BILATERAL_EXCHANGE = "BILATERAL_EXCHANGE"
    JOINT_RESEARCH = "JOINT_RESEARCH"
    DUAL_DEGREE = "DUAL_DEGREE"
    FACULTY_EXCHANGE = "FACULTY_EXCHANGE"
    INTERNSHIP = "INTERNSHIP"


class AgreementScopeType(StrEnum):
    STUDENT_EXCHANGE = "STUDENT_EXCHANGE"
    FACULTY_EXCHANGE = "FACULTY_EXCHANGE"
    JOINT_RESEARCH = "JOINT_RESEARCH"
    DUAL_DEGREE = "DUAL_DEGREE"
    INTERNSHIPS = "INTERNSHIPS"
    COLLABORATIVE_ACADEMIC = "COLLABORATIVE_ACADEMIC"


PartnerCategory = PartnershipCategory


class AgreementStatus(StrEnum):
    DRAFT = "DRAFT"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    EXPIRING = "EXPIRING"
    EXPIRED = "EXPIRED"
    SUSPENDED = "SUSPENDED"
    CLOSED = "CLOSED"


class MobilityProgramType(StrEnum):
    SEMESTER_EXCHANGE = "SEMESTER_EXCHANGE"
    SHORT_TERM = "SHORT_TERM"
    SUMMER_WINTER_SCHOOL = "SUMMER_WINTER_SCHOOL"
    INTERNATIONAL_INTERNSHIP = "INTERNATIONAL_INTERNSHIP"
    RESEARCH_EXCHANGE = "RESEARCH_EXCHANGE"
    DUAL_DEGREE = "DUAL_DEGREE"
    INBOUND_EXCHANGE = "INBOUND_EXCHANGE"
    OUTBOUND_STUDY_ABROAD = "OUTBOUND_STUDY_ABROAD"


class MobilityDirection(StrEnum):
    OUTBOUND = "OUTBOUND"
    INBOUND = "INBOUND"
    BIDIRECTIONAL = "BIDIRECTIONAL"


class MobilityApplicationStatus(StrEnum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    ELIGIBILITY_REVIEW = "ELIGIBILITY_REVIEW"
    DEPARTMENT_REVIEW = "DEPARTMENT_REVIEW"
    INTERNATIONAL_OFFICE_REVIEW = "INTERNATIONAL_OFFICE_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"
    WAITLISTED = "WAITLISTED"
    ON_HOLD = "ON_HOLD"
    RETURNED_FOR_INFO = "RETURNED_FOR_INFO"
    PARTNER_NOMINATED = "PARTNER_NOMINATED"
    PARTNER_ACCEPTED = "PARTNER_ACCEPTED"
    PARTNER_DECLINED = "PARTNER_DECLINED"
    PARTNER_REJECTED = "PARTNER_REJECTED"
    PRE_DEPARTURE_PREPARATION = "PRE_DEPARTURE_PREPARATION"
    ACTIVE_MOBILITY = "ACTIVE_MOBILITY"
    COMPLETED = "COMPLETED"


class FacultyMobilityType(StrEnum):
    OUTBOUND_FACULTY = "OUTBOUND_FACULTY"
    VISITING_PROFESSOR = "VISITING_PROFESSOR"
    VISITING_RESEARCHER = "VISITING_RESEARCHER"
    ACADEMIC_DELEGATE = "ACADEMIC_DELEGATE"


class EquivalencyStatus(StrEnum):
    PROPOSED = "PROPOSED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CONDITIONALLY_APPROVED = "CONDITIONALLY_APPROVED"


class CreditTransferStatus(StrEnum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    FACULTY_EVALUATED = "FACULTY_EVALUATED"
    FACULTY_REVIEW = "FACULTY_REVIEW"
    COMMITTEE_APPROVED = "COMMITTEE_APPROVED"
    REJECTED = "REJECTED"
    CREDITS_POSTED = "CREDITS_POSTED"


class MobilityDocumentType(StrEnum):
    PASSPORT = "PASSPORT"
    NOMINATION_LETTER = "NOMINATION_LETTER"
    ADMISSION_LETTER = "ADMISSION_LETTER"
    TRANSCRIPT = "TRANSCRIPT"
    LANGUAGE_PROFICIENCY = "LANGUAGE_PROFICIENCY"
    INSURANCE = "INSURANCE"
    FUNDING_SCHOLARSHIP = "FUNDING_SCHOLARSHIP"
    TRAVEL_ITINERARY = "TRAVEL_ITINERARY"
    HOST_AGREEMENT = "HOST_AGREEMENT"
    ARRIVAL_CONFIRMATION = "ARRIVAL_CONFIRMATION"
    POST_MOBILITY_REPORT = "POST_MOBILITY_REPORT"
    VISA_REFERENCE = "VISA_REFERENCE"


class DocumentVerificationStatus(StrEnum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class FundingStatus(StrEnum):
    PROPOSED = "PROPOSED"
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    DECLINED = "DECLINED"
    REJECTED = "REJECTED"
    DISBURSED = "DISBURSED"


class InboundStudentStatus(StrEnum):
    NOMINATED = "NOMINATED"
    ACCEPTED = "ACCEPTED"
    ACTIVE_STUDY = "ACTIVE_STUDY"
    COMPLETED = "COMPLETED"
    WITHDRAWN = "WITHDRAWN"


class FacultyMobilityDirection(StrEnum):
    OUTBOUND_FACULTY = "OUTBOUND_FACULTY"
    INBOUND_VISITING_SCHOLAR = "INBOUND_VISITING_SCHOLAR"


class FacultyMobilityStatus(StrEnum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    HOD_REVIEW = "HOD_REVIEW"
    VP_REVIEW = "VP_REVIEW"
    APPROVED = "APPROVED"
    SCHEDULED = "SCHEDULED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


CreditEquivalencyStatus = EquivalencyStatus
MobilityDocumentVerificationStatus = DocumentVerificationStatus
MobilityFundingStatus = FundingStatus


class MobilityTermType(StrEnum):
    FALL_SEMESTER = "FALL_SEMESTER"
    SPRING_SEMESTER = "SPRING_SEMESTER"
    SUMMER_TERM = "SUMMER_TERM"
    WINTER_TERM = "WINTER_TERM"
    FULL_YEAR = "FULL_YEAR"


class ScholarshipAwardStatus(StrEnum):
    APPLIED = "APPLIED"
    AWARDED = "AWARDED"
    REJECTED = "REJECTED"
    DISBURSED = "DISBURSED"


# =============================================================================
# 2. MODELS
# =============================================================================


class InternationalPartner(TenantScopedModel):
    """Foreign university, college, research institute, or international partner organization."""

    __tablename__ = "ir_partners"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    country: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    country_code: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    partnership_category: Mapped[str] = mapped_column(
        String(50), nullable=False, default=PartnershipCategory.BILATERAL.value, index=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="ACTIVE", index=True)
    primary_contact_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    primary_contact_email: Mapped[str | None] = mapped_column(String(150), nullable=True)
    primary_contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    linked_campuses: Mapped[list[str] | None] = mapped_column(JSONType, nullable=True, default=list)
    linked_departments: Mapped[list[str] | None] = mapped_column(JSONType, nullable=True, default=list)
    linked_programs: Mapped[list[str] | None] = mapped_column(JSONType, nullable=True, default=list)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    agreements: Mapped[list["InstitutionalAgreement"]] = relationship(
        "InstitutionalAgreement", back_populates="partner", cascade="all, delete-orphan"
    )
    programs: Mapped[list["MobilityProgram"]] = relationship(
        "MobilityProgram", back_populates="partner"
    )

    __table_args__ = (
        Index("ix_ir_partners_tenant_country", "tenant_id", "country"),
        Index("ix_ir_partners_tenant_status", "tenant_id", "status"),
    )

    @property
    def partner_name(self) -> str:
        return self.name

    @partner_name.setter
    def partner_name(self, val: str):
        self.name = val

    @property
    def partner_code(self) -> str:
        return f"PRT-{self.id.hex[:8].upper()}"

    @property
    def country_name(self) -> str:
        return self.country

    @country_name.setter
    def country_name(self, val: str):
        self.country = val

    @property
    def country_code_display(self) -> str:
        return self.country_code or (self.country[:2].upper() if self.country else "XX")

    @property
    def official_website(self) -> str | None:
        return self.website

    @official_website.setter
    def official_website(self, val: str | None):
        self.website = val

    @property
    def category(self) -> PartnershipCategory:
        try:
            return PartnershipCategory(self.partnership_category)
        except Exception:
            return PartnershipCategory.UNIVERSITY

    @category.setter
    def category(self, val: Any):
        self.partnership_category = val.value if hasattr(val, "value") else str(val)

    @property
    def is_active(self) -> bool:
        return self.status == "ACTIVE"

    @is_active.setter
    def is_active(self, val: bool):
        self.status = "ACTIVE" if val else "INACTIVE"


class InstitutionalAgreement(TenantScopedModel):
    """Formal Memoranda of Understanding (MoUs), bilateral exchange, and partnership agreements."""

    __tablename__ = "ir_agreements"

    agreement_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    agreement_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default=AgreementType.MOU.value, index=True
    )
    partner_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("ir_partners.id", ondelete="CASCADE"), nullable=False, index=True
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    renewal_reminder_days: Mapped[int] = mapped_column(Integer, nullable=False, default=90)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=AgreementStatus.ACTIVE.value, index=True
    )
    responsible_coordinator_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    scope_student_exchange: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    scope_faculty_exchange: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    scope_joint_research: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    scope_dual_degree: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    scope_internships: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    scope_collaborative_academic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    document_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    partner: Mapped["InternationalPartner"] = relationship("InternationalPartner", back_populates="agreements")
    amendments: Mapped[list["AgreementAmendment"]] = relationship(
        "AgreementAmendment", back_populates="agreement", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "agreement_number", name="uq_ir_agreements_tenant_number"),
        Index("ix_ir_agreements_expiry", "tenant_id", "expiry_date", "status"),
    )

    @property
    def agreement_reference_number(self) -> str:
        return self.agreement_number

    @agreement_reference_number.setter
    def agreement_reference_number(self, val: str):
        self.agreement_number = val

    @property
    def agreement_title(self) -> str:
        return self.title

    @agreement_title.setter
    def agreement_title(self, val: str):
        self.title = val

    @property
    def effective_start_date(self) -> date:
        return self.start_date

    @effective_start_date.setter
    def effective_start_date(self, val: date):
        self.start_date = val

    @property
    def effective_end_date(self) -> date:
        return self.expiry_date

    @effective_end_date.setter
    def effective_end_date(self, val: date):
        self.expiry_date = val

    @property
    def renewal_window_days(self) -> int:
        return self.renewal_reminder_days

    @renewal_window_days.setter
    def renewal_window_days(self, val: int):
        self.renewal_reminder_days = val

    @property
    def document_reference_url(self) -> str | None:
        return self.document_url

    @document_reference_url.setter
    def document_reference_url(self, val: str | None):
        self.document_url = val

    @property
    def scope_types(self) -> list[AgreementScopeType]:
        scopes = []
        if self.scope_student_exchange:
            scopes.append(AgreementScopeType.STUDENT_EXCHANGE)
        if self.scope_faculty_exchange:
            scopes.append(AgreementScopeType.FACULTY_EXCHANGE)
        if self.scope_joint_research:
            scopes.append(AgreementScopeType.JOINT_RESEARCH)
        if self.scope_dual_degree:
            scopes.append(AgreementScopeType.DUAL_DEGREE)
        if self.scope_internships:
            scopes.append(AgreementScopeType.INTERNSHIPS)
        if self.scope_collaborative_academic:
            scopes.append(AgreementScopeType.COLLABORATIVE_ACADEMIC)
        return scopes

    @scope_types.setter
    def scope_types(self, val: list[Any]):
        vals = [v.value if hasattr(v, "value") else str(v) for v in val]
        self.scope_student_exchange = "STUDENT_EXCHANGE" in vals
        self.scope_faculty_exchange = "FACULTY_EXCHANGE" in vals
        self.scope_joint_research = "JOINT_RESEARCH" in vals
        self.scope_dual_degree = "DUAL_DEGREE" in vals
        self.scope_internships = "INTERNSHIPS" in vals
        self.scope_collaborative_academic = "COLLABORATIVE_ACADEMIC" in vals


class AgreementAmendment(TenantScopedModel):
    """Historical revision log and amendments to institutional agreements."""

    __tablename__ = "ir_agreement_amendments"

    agreement_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("ir_agreements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amendment_number: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    change_summary: Mapped[str] = mapped_column(Text, nullable=False)
    approved_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )
    document_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    agreement: Mapped["InstitutionalAgreement"] = relationship("InstitutionalAgreement", back_populates="amendments")

    @property
    def amendment_type(self) -> str:
        return self.amendment_number

    @amendment_type.setter
    def amendment_type(self, val: str):
        self.amendment_number = val

    @property
    def description(self) -> str:
        return self.change_summary

    @description.setter
    def description(self, val: str):
        self.change_summary = val

    @property
    def new_effective_end_date(self) -> date | None:
        return self.effective_date

    @new_effective_end_date.setter
    def new_effective_end_date(self, val: date | None):
        if val:
            self.effective_date = val

    @property
    def document_reference_url(self) -> str | None:
        return self.document_url

    @document_reference_url.setter
    def document_reference_url(self, val: str | None):
        self.document_url = val


class MobilityProgram(TenantScopedModel):
    """Institutional exchange, study-abroad, summer school, or dual-degree mobility offering."""

    __tablename__ = "ir_programs"

    program_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    partner_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("ir_partners.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agreement_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("ir_agreements.id", ondelete="SET NULL"), nullable=True, index=True
    )
    program_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default=MobilityProgramType.SEMESTER_EXCHANGE.value, index=True
    )
    direction: Mapped[str] = mapped_column(
        String(20), nullable=False, default=MobilityDirection.OUTBOUND.value, index=True
    )
    academic_term: Mapped[str] = mapped_column(String(100), nullable=False)
    academic_year: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    participating_departments: Mapped[list[str] | None] = mapped_column(JSONType, nullable=True, default=list)
    eligible_programs: Mapped[list[str] | None] = mapped_column(JSONType, nullable=True, default=list)
    total_seats_quota: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    min_cgpa_requirement: Mapped[float] = mapped_column(Float, nullable=False, default=7.0)
    min_credits_requirement: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    language_requirements: Mapped[list[str] | None] = mapped_column(JSONType, nullable=True, default=list)
    application_open_date: Mapped[date] = mapped_column(Date, nullable=False)
    application_deadline: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    duration_weeks: Mapped[int] = mapped_column(Integer, nullable=False, default=16)
    academic_workload: Mapped[str | None] = mapped_column(String(255), nullable=True)
    required_documents: Mapped[list[str] | None] = mapped_column(JSONType, nullable=True, default=list)
    funding_scholarship_info: Mapped[str | None] = mapped_column(Text, nullable=True)
    coordinator_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )
    faculty_contact: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="DRAFT", index=True)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)

    partner: Mapped["InternationalPartner"] = relationship("InternationalPartner", back_populates="programs")
    applications: Mapped[list["MobilityApplication"]] = relationship(
        "MobilityApplication", back_populates="program", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "program_code", name="uq_ir_programs_tenant_code"),
        Index("ix_ir_programs_deadline_status", "tenant_id", "application_deadline", "status"),
    )

    @property
    def program_title(self) -> str:
        return self.title

    @program_title.setter
    def program_title(self, val: str):
        self.title = val

    @property
    def application_start_date(self) -> date:
        return self.application_open_date

    @application_start_date.setter
    def application_start_date(self, val: date):
        self.application_open_date = val

    @property
    def expected_start_date(self) -> date:
        return self.application_deadline + timedelta(days=60)

    @expected_start_date.setter
    def expected_start_date(self, val: date):
        pass

    @property
    def expected_end_date(self) -> date:
        return self.application_deadline + timedelta(days=60 + (self.duration_weeks or 16) * 7)

    @expected_end_date.setter
    def expected_end_date(self, val: date):
        pass

    @property
    def total_seats(self) -> int:
        return self.total_seats_quota

    @total_seats.setter
    def total_seats(self, val: int):
        self.total_seats_quota = val

    @property
    def nomination_limit(self) -> int:
        return self.total_seats_quota * 2

    @nomination_limit.setter
    def nomination_limit(self, val: int):
        pass

    @property
    def min_credits_completed(self) -> int:
        return self.min_credits_requirement

    @min_credits_completed.setter
    def min_credits_completed(self, val: int):
        self.min_credits_requirement = val

    @property
    def is_published(self) -> bool:
        return self.status == "PUBLISHED"

    @is_published.setter
    def is_published(self, val: bool):
        self.status = "PUBLISHED" if val else "DRAFT"

    @property
    def term_type(self) -> MobilityTermType:
        return MobilityTermType.FALL_SEMESTER

    @term_type.setter
    def term_type(self, val: Any):
        pass


class MobilityApplication(TenantScopedModel):
    """End-to-end student mobility application with review and nomination tracking."""

    __tablename__ = "ir_applications"

    application_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    program_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("ir_programs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    academic_term: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=MobilityApplicationStatus.DRAFT.value, index=True
    )
    statement_of_purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    proposed_courses: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONType, nullable=True, default=list)
    student_cgpa_snapshot: Mapped[float | None] = mapped_column(Float, nullable=True)
    credits_completed_snapshot: Mapped[int | None] = mapped_column(Integer, nullable=True)
    eligibility_check_passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    eligibility_exception_waived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    exception_justification: Mapped[str | None] = mapped_column(Text, nullable=True)
    nomination_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    partner_decision: Mapped[str | None] = mapped_column(String(50), nullable=True)
    partner_decision_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    partner_decision_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    departure_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    return_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    completion_report: Mapped[str | None] = mapped_column(Text, nullable=True)

    program: Mapped["MobilityProgram"] = relationship("MobilityProgram", back_populates="applications")
    reviews: Mapped[list["ApplicationReviewHistory"]] = relationship(
        "ApplicationReviewHistory", back_populates="application", cascade="all, delete-orphan"
    )
    documents: Mapped[list["MobilityDocument"]] = relationship(
        "MobilityDocument", back_populates="application", cascade="all, delete-orphan"
    )
    credit_transfers: Mapped[list["StudentCreditTransferRequest"]] = relationship(
        "StudentCreditTransferRequest", back_populates="application"
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "application_number", name="uq_ir_applications_tenant_num"),
        UniqueConstraint("tenant_id", "student_id", "program_id", name="uq_ir_applications_student_prog"),
        Index("ix_ir_applications_student_status", "tenant_id", "student_id", "status"),
    )

    @property
    def application_reference_number(self) -> str:
        return self.application_number

    @application_reference_number.setter
    def application_reference_number(self, val: str):
        self.application_number = val

    @property
    def student_cgpa_at_application(self) -> float | None:
        return self.student_cgpa_snapshot

    @student_cgpa_at_application.setter
    def student_cgpa_at_application(self, val: float | None):
        self.student_cgpa_snapshot = val

    @property
    def credits_completed_at_application(self) -> int | None:
        return self.credits_completed_snapshot

    @credits_completed_at_application.setter
    def credits_completed_at_application(self, val: int | None):
        self.credits_completed_snapshot = val

    @property
    def nominated_at(self) -> datetime | None:
        if self.nomination_date:
            return datetime.combine(self.nomination_date, datetime.min.time(), tzinfo=UTC)
        return None

    @nominated_at.setter
    def nominated_at(self, val: Any):
        if val:
            self.nomination_date = val.date() if isinstance(val, datetime) else val

    @property
    def emergency_contact_name(self) -> str:
        return "Guardian"

    @property
    def emergency_contact_phone(self) -> str:
        return "+1-000-0000"

    @property
    def emergency_contact_relationship(self) -> str:
        return "Family"

    @property
    def eligibility_check_details(self) -> dict[str, Any]:
        return getattr(self, "_eligibility_check_details", {})

    @eligibility_check_details.setter
    def eligibility_check_details(self, val: dict[str, Any]):
        self._eligibility_check_details = val

    @property
    def department_decision(self) -> str | None:
        return getattr(self, "_department_decision", None)

    @department_decision.setter
    def department_decision(self, val: str | None):
        self._department_decision = val

    @property
    def department_comments(self) -> str | None:
        return getattr(self, "_department_comments", None)

    @department_comments.setter
    def department_comments(self, val: str | None):
        self._department_comments = val

    @property
    def intl_office_decision(self) -> str | None:
        return getattr(self, "_intl_office_decision", None)

    @intl_office_decision.setter
    def intl_office_decision(self, val: str | None):
        self._intl_office_decision = val

    @property
    def intl_office_comments(self) -> str | None:
        return getattr(self, "_intl_office_comments", None)

    @intl_office_comments.setter
    def intl_office_comments(self, val: str | None):
        self._intl_office_comments = val

    @property
    def pre_departure_checklist(self) -> dict[str, Any]:
        return getattr(self, "_pre_departure_checklist", {})

    @pre_departure_checklist.setter
    def pre_departure_checklist(self, val: dict[str, Any]):
        self._pre_departure_checklist = val

    @property
    def visa_reference_number(self) -> str | None:
        return getattr(self, "_visa_reference_number", None)

    @visa_reference_number.setter
    def visa_reference_number(self, val: str | None):
        self._visa_reference_number = val

    @property
    def travel_itinerary(self) -> dict[str, Any]:
        return getattr(self, "_travel_itinerary", {})

    @travel_itinerary.setter
    def travel_itinerary(self, val: dict[str, Any]):
        self._travel_itinerary = val

    @property
    def insurance_policy_number(self) -> str | None:
        return getattr(self, "_insurance_policy_number", None)

    @insurance_policy_number.setter
    def insurance_policy_number(self, val: str | None):
        self._insurance_policy_number = val


class ApplicationReviewHistory(TenantScopedModel):
    """Audit log of review decisions across departmental and international office stages."""

    __tablename__ = "ir_application_reviews"

    application_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("ir_applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reviewer_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reviewer_role: Mapped[str] = mapped_column(String(50), nullable=False)
    stage: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)

    application: Mapped["MobilityApplication"] = relationship("MobilityApplication", back_populates="reviews")

    @property
    def review_stage(self) -> str:
        return self.stage

    @review_stage.setter
    def review_stage(self, val: str):
        self.stage = val

    @property
    def conditions(self) -> str | None:
        return getattr(self, "_conditions", None)

    @conditions.setter
    def conditions(self, val: str | None):
        self._conditions = val


class InboundStudentProfile(TenantScopedModel):
    """Profile and onboarding tracking for international exchange students studying on campus."""

    __tablename__ = "ir_inbound_students"

    application_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("ir_applications.id", ondelete="SET NULL"), nullable=True, index=True
    )
    partner_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("ir_partners.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    student_email: Mapped[str] = mapped_column(String(255), nullable=False)
    nationality: Mapped[str] = mapped_column(String(100), nullable=False)
    passport_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    home_institution_student_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    host_department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_departments.id", ondelete="SET NULL"), nullable=True
    )
    host_program_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_programs.id", ondelete="SET NULL"), nullable=True
    )
    study_period_start: Mapped[date] = mapped_column(Date, nullable=False)
    study_period_end: Mapped[date] = mapped_column(Date, nullable=False)
    academic_term: Mapped[str] = mapped_column(String(100), nullable=False)
    orientation_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    campus_card_issued: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    accommodation_status: Mapped[str] = mapped_column(String(50), nullable=False, default="NOT_REQUIRED")
    accommodation_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    academic_registration_status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING")
    assigned_coordinator_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )
    check_in_status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING", index=True)
    check_in_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    departure_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    partner: Mapped["InternationalPartner"] = relationship("InternationalPartner")

    __table_args__ = (
        Index("ix_ir_inbound_status", "tenant_id", "check_in_status"),
    )

    @property
    def inbound_reference_number(self) -> str:
        return f"INB-{self.id.hex[:8].upper()}"

    @property
    def status(self) -> InboundStudentStatus:
        if self.check_in_status == "ACTIVE_STUDY":
            return InboundStudentStatus.ACTIVE_STUDY
        elif self.check_in_status == "COMPLETED":
            return InboundStudentStatus.COMPLETED
        return InboundStudentStatus.NOMINATED

    @status.setter
    def status(self, val: Any):
        v = val.value if hasattr(val, "value") else str(val)
        self.check_in_status = v

    @property
    def student_first_name(self) -> str:
        parts = (self.student_name or "").split(" ", 1)
        return parts[0]

    @student_first_name.setter
    def student_first_name(self, val: str):
        last = getattr(self, "_last_name", "")
        self.student_name = f"{val} {last}".strip()

    @property
    def student_last_name(self) -> str:
        parts = (self.student_name or "").split(" ", 1)
        return parts[1] if len(parts) > 1 else ""

    @student_last_name.setter
    def student_last_name(self, val: str):
        self._last_name = val
        first = (self.student_name or "").split(" ", 1)[0]
        self.student_name = f"{first} {val}".strip()

    @property
    def email(self) -> str:
        return self.student_email

    @email.setter
    def email(self, val: str):
        self.student_email = val

    @property
    def phone(self) -> str | None:
        return getattr(self, "_phone", None)

    @phone.setter
    def phone(self, val: str | None):
        self._phone = val

    @property
    def country_of_citizenship(self) -> str:
        return self.nationality

    @country_of_citizenship.setter
    def country_of_citizenship(self, val: str):
        self.nationality = val

    @property
    def home_institution_name(self) -> str:
        return self.home_institution_student_id or "Home University"

    @home_institution_name.setter
    def home_institution_name(self, val: str):
        self.home_institution_student_id = val

    @property
    def home_program_of_study(self) -> str:
        return self.academic_term

    @home_program_of_study.setter
    def home_program_of_study(self, val: str):
        pass

    @property
    def expected_start_date(self) -> date:
        return self.study_period_start

    @expected_start_date.setter
    def expected_start_date(self, val: date):
        self.study_period_start = val

    @property
    def expected_end_date(self) -> date:
        return self.study_period_end

    @expected_end_date.setter
    def expected_end_date(self, val: date):
        self.study_period_end = val

    @property
    def study_period_terms(self) -> str:
        return self.academic_term

    @study_period_terms.setter
    def study_period_terms(self, val: str):
        self.academic_term = val

    @property
    def assigned_mentor_user_id(self) -> UUID | None:
        return self.assigned_coordinator_user_id

    @assigned_mentor_user_id.setter
    def assigned_mentor_user_id(self, val: UUID | None):
        self.assigned_coordinator_user_id = val


class FacultyMobilityRecord(TenantScopedModel):
    """Outbound faculty exchange requests and international visiting scholars on campus."""

    __tablename__ = "ir_faculty_mobility"

    staff_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    scholar_name: Mapped[str] = mapped_column(String(255), nullable=False)
    scholar_email: Mapped[str] = mapped_column(String(255), nullable=False)
    mobility_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default=FacultyMobilityType.OUTBOUND_FACULTY.value, index=True
    )
    partner_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("ir_partners.id", ondelete="CASCADE"), nullable=False, index=True
    )
    home_institution_name: Mapped[str] = mapped_column(String(255), nullable=False)
    host_department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_departments.id", ondelete="SET NULL"), nullable=True
    )
    visit_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    visit_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    objectives: Mapped[str] = mapped_column(Text, nullable=False)
    invitation_letter_ref: Mapped[str | None] = mapped_column(String(500), nullable=True)
    academic_visit_plan: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONType, nullable=True, default=list)
    research_project_link: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="DRAFT", index=True)
    hod_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )
    vp_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )
    outcomes_report: Mapped[str | None] = mapped_column(Text, nullable=True)

    partner: Mapped["InternationalPartner"] = relationship("InternationalPartner")

    __table_args__ = (
        Index("ix_ir_faculty_dates", "tenant_id", "visit_start_date", "visit_end_date"),
    )

    @property
    def mobility_reference_number(self) -> str:
        return f"FAC-{self.id.hex[:8].upper()}"

    @property
    def direction(self) -> FacultyMobilityDirection:
        return FacultyMobilityDirection.OUTBOUND_FACULTY

    @direction.setter
    def direction(self, val: Any):
        self.mobility_type = val.value if hasattr(val, "value") else str(val)

    @property
    def faculty_user_id(self) -> UUID | None:
        return self.staff_user_id

    @faculty_user_id.setter
    def faculty_user_id(self, val: UUID | None):
        self.staff_user_id = val

    @property
    def visiting_scholar_name(self) -> str:
        return self.scholar_name

    @visiting_scholar_name.setter
    def visiting_scholar_name(self, val: str):
        self.scholar_name = val

    @property
    def visiting_scholar_email(self) -> str:
        return self.scholar_email

    @visiting_scholar_email.setter
    def visiting_scholar_email(self, val: str):
        self.scholar_email = val

    @property
    def department_id(self) -> UUID | None:
        return self.host_department_id

    @department_id.setter
    def department_id(self, val: UUID | None):
        self.host_department_id = val

    @property
    def visit_objectives(self) -> str:
        return self.objectives

    @visit_objectives.setter
    def visit_objectives(self, val: str):
        self.objectives = val

    @property
    def lecture_topics(self) -> list[str]:
        return getattr(self, "_lecture_topics", [])

    @lecture_topics.setter
    def lecture_topics(self, val: list[str]):
        self._lecture_topics = val

    @property
    def research_collaboration_areas(self) -> list[str]:
        return getattr(self, "_research_collaboration_areas", [])

    @research_collaboration_areas.setter
    def research_collaboration_areas(self, val: list[str]):
        self._research_collaboration_areas = val

    @property
    def hod_approved_by_user_id(self) -> UUID | None:
        return self.hod_user_id

    @hod_approved_by_user_id.setter
    def hod_approved_by_user_id(self, val: UUID | None):
        self.hod_user_id = val

    @property
    def vp_approved_by_user_id(self) -> UUID | None:
        return self.vp_user_id

    @vp_approved_by_user_id.setter
    def vp_approved_by_user_id(self, val: UUID | None):
        self.vp_user_id = val

    @property
    def completion_report_summary(self) -> str | None:
        return self.outcomes_report

    @completion_report_summary.setter
    def completion_report_summary(self, val: str | None):
        self.outcomes_report = val


class CourseEquivalencyMapping(TenantScopedModel):
    """Authorized academic mappings between international partner courses and campus curriculum."""

    __tablename__ = "ir_course_equivalencies"

    partner_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("ir_partners.id", ondelete="CASCADE"), nullable=False, index=True
    )
    partner_course_code: Mapped[str] = mapped_column(String(50), nullable=False)
    partner_course_title: Mapped[str] = mapped_column(String(255), nullable=False)
    partner_credits: Mapped[float] = mapped_column(Float, nullable=False, default=4.0)
    grading_scale_info: Mapped[str | None] = mapped_column(String(100), nullable=True)
    syllabus_document_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    learning_outcomes: Mapped[str | None] = mapped_column(Text, nullable=True)
    campus_program_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_programs.id", ondelete="SET NULL"), nullable=True
    )
    campus_course_code: Mapped[str] = mapped_column(String(50), nullable=False)
    campus_course_title: Mapped[str] = mapped_column(String(255), nullable=False)
    campus_credits: Mapped[float] = mapped_column(Float, nullable=False, default=4.0)
    department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_departments.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=EquivalencyStatus.PROPOSED.value, index=True
    )
    reviewer_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )
    committee_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    conditions: Mapped[str | None] = mapped_column(Text, nullable=True)
    effective_academic_year: Mapped[str] = mapped_column(String(50), nullable=False, default="2026-2027")

    partner: Mapped["InternationalPartner"] = relationship("InternationalPartner")

    __table_args__ = (
        UniqueConstraint("tenant_id", "partner_id", "partner_course_code", "campus_course_code", name="uq_ir_course_equiv"),
    )

    @property
    def host_course_code(self) -> str:
        return self.partner_course_code

    @host_course_code.setter
    def host_course_code(self, val: str):
        self.partner_course_code = val

    @property
    def host_course_title(self) -> str:
        return self.partner_course_title

    @host_course_title.setter
    def host_course_title(self, val: str):
        self.partner_course_title = val

    @property
    def host_course_credits(self) -> float:
        return self.partner_credits

    @host_course_credits.setter
    def host_course_credits(self, val: float):
        self.partner_credits = val

    @property
    def host_syllabus_reference(self) -> str | None:
        return self.syllabus_document_url

    @host_syllabus_reference.setter
    def host_syllabus_reference(self, val: str | None):
        self.syllabus_document_url = val

    @property
    def host_grading_scale(self) -> str | None:
        return self.grading_scale_info

    @host_grading_scale.setter
    def host_grading_scale(self, val: str | None):
        self.grading_scale_info = val

    @property
    def learning_outcomes_comparison(self) -> str | None:
        return self.learning_outcomes

    @learning_outcomes_comparison.setter
    def learning_outcomes_comparison(self, val: str | None):
        self.learning_outcomes = val

    @property
    def evaluated_by_user_id(self) -> UUID | None:
        return self.reviewer_user_id

    @evaluated_by_user_id.setter
    def evaluated_by_user_id(self, val: UUID | None):
        self.reviewer_user_id = val

    @property
    def evaluator_comments(self) -> str | None:
        return self.committee_notes

    @evaluator_comments.setter
    def evaluator_comments(self, val: str | None):
        self.committee_notes = val

    @property
    def valid_from(self) -> date:
        return getattr(self, "_valid_from", date.today())

    @valid_from.setter
    def valid_from(self, val: date):
        self._valid_from = val

    @property
    def valid_until(self) -> date | None:
        return getattr(self, "_valid_until", None)

    @valid_until.setter
    def valid_until(self, val: date | None):
        self._valid_until = val


class StudentCreditTransferRequest(TenantScopedModel):
    """Formal student academic credit recognition requests with committee authorization."""

    __tablename__ = "ir_credit_transfers"

    application_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("ir_applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    host_transcript_doc_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=CreditTransferStatus.SUBMITTED.value, index=True
    )
    mapped_courses_summary: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONType, nullable=True, default=list)
    total_credits_requested: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_credits_approved: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    committee_approval_ref: Mapped[str | None] = mapped_column(String(100), nullable=True)
    authorized_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    authorized_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    application: Mapped["MobilityApplication"] = relationship("MobilityApplication", back_populates="credit_transfers")

    @property
    def transcript_document_url(self) -> str:
        return self.host_transcript_doc_url or ""

    @transcript_document_url.setter
    def transcript_document_url(self, val: str):
        self.host_transcript_doc_url = val

    @property
    def host_course_code(self) -> str:
        summary = self.mapped_courses_summary or []
        return summary[0].get("host_course_code", "GEN-101") if summary else "GEN-101"

    @property
    def host_course_title(self) -> str:
        summary = self.mapped_courses_summary or []
        return summary[0].get("host_course_title", "General Course") if summary else "General Course"

    @property
    def host_grade_received(self) -> str:
        summary = self.mapped_courses_summary or []
        return summary[0].get("host_grade", "A") if summary else "A"

    @property
    def host_credits_earned(self) -> float:
        return self.total_credits_requested

    @property
    def target_campus_credits(self) -> float:
        return self.total_credits_approved

    @target_campus_credits.setter
    def target_campus_credits(self, val: float):
        self.total_credits_approved = val

    @property
    def committee_resolution_notes(self) -> str | None:
        return self.notes

    @committee_resolution_notes.setter
    def committee_resolution_notes(self, val: str | None):
        self.notes = val

    @property
    def academic_committee_approved_by_user_id(self) -> UUID | None:
        return self.authorized_by_user_id

    @academic_committee_approved_by_user_id.setter
    def academic_committee_approved_by_user_id(self, val: UUID | None):
        self.authorized_by_user_id = val

    @property
    def credits_posted_to_transcript(self) -> bool:
        return (
            self.status == CreditTransferStatus.COMMITTEE_APPROVED.value
            or self.status == CreditTransferStatus.CREDITS_POSTED.value
        )

    @credits_posted_to_transcript.setter
    def credits_posted_to_transcript(self, val: bool):
        if val and self.status == CreditTransferStatus.COMMITTEE_APPROVED.value:
            self.status = CreditTransferStatus.CREDITS_POSTED.value


class MobilityDocument(TenantScopedModel):
    """Mandatory checklists and uploaded references for passports, insurance, transcripts, and arrival confirmations."""

    __tablename__ = "ir_mobility_documents"

    application_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("ir_applications.id", ondelete="CASCADE"), nullable=True, index=True
    )
    inbound_student_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("ir_inbound_students.id", ondelete="CASCADE"), nullable=True, index=True
    )
    faculty_mobility_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("ir_faculty_mobility.id", ondelete="CASCADE"), nullable=True, index=True
    )
    document_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default=MobilityDocumentType.PASSPORT.value, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    submission_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    verification_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=DocumentVerificationStatus.PENDING.value, index=True
    )
    verification_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    verified_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    application: Mapped["MobilityApplication | None"] = relationship("MobilityApplication", back_populates="documents")

    __table_args__ = (
        Index("ix_ir_docs_status", "tenant_id", "verification_status"),
    )

    @property
    def document_name(self) -> str:
        return self.title

    @document_name.setter
    def document_name(self, val: str):
        self.title = val

    @property
    def file_storage_url(self) -> str:
        return self.file_url

    @file_storage_url.setter
    def file_storage_url(self, val: str):
        self.file_url = val

    @property
    def rejection_reason(self) -> str | None:
        return self.verification_notes

    @rejection_reason.setter
    def rejection_reason(self, val: str | None):
        self.verification_notes = val

    @property
    def document_expiry_date(self) -> date | None:
        return self.expiry_date

    @document_expiry_date.setter
    def document_expiry_date(self, val: date | None):
        self.expiry_date = val

    @property
    def file_mime_type(self) -> str | None:
        return self.mime_type

    @file_mime_type.setter
    def file_mime_type(self, val: str | None):
        self.mime_type = val


class MobilityScholarship(TenantScopedModel):
    """Configurable global mobility scholarships and travel grant programs."""

    __tablename__ = "ir_scholarships"

    code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    sponsor_organization: Mapped[str] = mapped_column(String(255), nullable=False)
    partner_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("ir_partners.id", ondelete="SET NULL"), nullable=True, index=True
    )
    award_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    eligibility_criteria: Mapped[str] = mapped_column(Text, nullable=False)
    application_deadline: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    total_quota_seats: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="ACTIVE", index=True)

    partner: Mapped["InternationalPartner | None"] = relationship("InternationalPartner")

    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_ir_scholarships_tenant_code"),
    )

    @property
    def scholarship_name(self) -> str:
        return self.title

    @scholarship_name.setter
    def scholarship_name(self, val: str):
        self.title = val

    @property
    def scholarship_code(self) -> str:
        return self.code

    @scholarship_code.setter
    def scholarship_code(self, val: str):
        self.code = val

    @property
    def funding_source(self) -> str:
        return self.sponsor_organization

    @funding_source.setter
    def funding_source(self, val: str):
        self.sponsor_organization = val

    @property
    def award_amount_per_student(self) -> float:
        return self.award_amount

    @award_amount_per_student.setter
    def award_amount_per_student(self, val: float):
        self.award_amount = val

    @property
    def total_available_slots(self) -> int:
        return self.total_quota_seats

    @total_available_slots.setter
    def total_available_slots(self, val: int):
        self.total_quota_seats = val

    @property
    def is_active(self) -> bool:
        return self.status == "ACTIVE"

    @is_active.setter
    def is_active(self, val: bool):
        self.status = "ACTIVE" if val else "INACTIVE"

    @property
    def eligibility_criteria_notes(self) -> str | None:
        return self.eligibility_criteria

    @eligibility_criteria_notes.setter
    def eligibility_criteria_notes(self, val: str | None):
        self.eligibility_criteria = val or ""


class MobilityFundingRequest(TenantScopedModel):
    """Funding allocation request linked to a mobility application."""

    __tablename__ = "ir_funding_requests"

    application_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("ir_applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scholarship_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("ir_scholarships.id", ondelete="SET NULL"), nullable=True, index=True
    )
    funding_type: Mapped[str] = mapped_column(String(50), nullable=False, default="SCHOLARSHIP")
    requested_amount: Mapped[float] = mapped_column(Float, nullable=False)
    approved_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=FundingStatus.PROPOSED.value, index=True
    )
    finance_disbursement_ref: Mapped[str | None] = mapped_column(String(100), nullable=True)
    estimated_total_program_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    student_funding_gap: Mapped[float | None] = mapped_column(Float, nullable=True)
    approved_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    @property
    def justification(self) -> str:
        return self.notes or ""

    @justification.setter
    def justification(self, val: str):
        self.notes = val

    @property
    def award_status(self) -> ScholarshipAwardStatus:
        if self.status == FundingStatus.APPROVED.value:
            return ScholarshipAwardStatus.AWARDED
        elif self.status in [FundingStatus.DECLINED.value, FundingStatus.REJECTED.value]:
            return ScholarshipAwardStatus.REJECTED
        return ScholarshipAwardStatus.APPLIED

    @award_status.setter
    def award_status(self, val: Any):
        pass

    @property
    def supporting_document_url(self) -> str | None:
        return getattr(self, "_supporting_document_url", None)

    @supporting_document_url.setter
    def supporting_document_url(self, val: str | None):
        self._supporting_document_url = val

    @property
    def review_comments(self) -> str | None:
        return getattr(self, "_review_comments", None)

    @review_comments.setter
    def review_comments(self, val: str | None):
        self._review_comments = val

    @property
    def finance_reference_id(self) -> UUID | None:
        return None

    @finance_reference_id.setter
    def finance_reference_id(self, val: UUID | None):
        if val:
            self.finance_disbursement_ref = str(val)


class InternationalPolicyConfig(TenantScopedModel):
    """Tenant-specific international relations policy thresholds and workflow rules."""

    __tablename__ = "ir_policy_configs"

    agreement_renewal_notice_days: Mapped[int] = mapped_column(Integer, nullable=False, default=90)
    default_max_outbound_nominations: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    require_hod_approval: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    require_vp_approval: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    allow_student_self_nomination: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    credit_transfer_committee_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    enable_inbound_mobility: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    enable_faculty_exchange: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    @property
    def agreement_warning_days(self) -> int:
        return self.agreement_renewal_notice_days

    @agreement_warning_days.setter
    def agreement_warning_days(self, val: int):
        self.agreement_renewal_notice_days = val

    @property
    def min_student_cgpa_default(self) -> float:
        return 6.0

    @min_student_cgpa_default.setter
    def min_student_cgpa_default(self, val: float):
        pass

    @property
    def min_student_credits_completed_default(self) -> int:
        return 30

    @min_student_credits_completed_default.setter
    def min_student_credits_completed_default(self, val: int):
        pass

    @property
    def require_department_approval_first(self) -> bool:
        return self.require_hod_approval

    @require_department_approval_first.setter
    def require_department_approval_first(self, val: bool):
        self.require_hod_approval = val

    @property
    def require_vp_approval_for_faculty(self) -> bool:
        return self.require_vp_approval

    @require_vp_approval_for_faculty.setter
    def require_vp_approval_for_faculty(self, val: bool):
        self.require_vp_approval = val

    @property
    def max_active_applications_per_student(self) -> int:
        return 2

    @max_active_applications_per_student.setter
    def max_active_applications_per_student(self, val: int):
        pass

    @property
    def credit_transfer_requires_academic_council(self) -> bool:
        return self.credit_transfer_committee_required

    @credit_transfer_requires_academic_council.setter
    def credit_transfer_requires_academic_council(self, val: bool):
        self.credit_transfer_committee_required = val

    @property
    def inbound_orientation_mandatory(self) -> bool:
        return self.enable_inbound_mobility

    @inbound_orientation_mandatory.setter
    def inbound_orientation_mandatory(self, val: bool):
        self.enable_inbound_mobility = val

    @property
    def notification_settings(self) -> dict[str, Any]:
        return {}

    @notification_settings.setter
    def notification_settings(self, val: dict[str, Any]):
        pass
