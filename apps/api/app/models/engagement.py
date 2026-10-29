"""SQLAlchemy Domain Models for Enterprise Student Engagement, Community Service,
Volunteering & Civic Impact Management (Step 65).

Product: CampusOS — "One Campus. One System. One Source of Truth."
"""

from datetime import date, datetime, time
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
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantScopedModel

# Cross-dialect JSON type for PostgreSQL JSONB and SQLite JSON
JSONType = JSON().with_variant(JSONB, "postgresql")


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================


class PartnerOrgType(StrEnum):
    NGO = "NGO"
    NON_PROFIT = "NON_PROFIT"
    GOVERNMENT_AGENCY = "GOVERNMENT_AGENCY"
    COMMUNITY_ORGANIZATION = "COMMUNITY_ORGANIZATION"
    HEALTHCARE_SYSTEM = "HEALTHCARE_SYSTEM"
    EDUCATIONAL_INSTITUTION = "EDUCATIONAL_INSTITUTION"
    CSR_CORPORATE = "CSR_CORPORATE"
    OTHER = "OTHER"


class PartnerStatus(StrEnum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    EXPIRED = "EXPIRED"
    ARCHIVED = "ARCHIVED"


class ProgramCategory(StrEnum):
    COMMUNITY_SERVICE = "COMMUNITY_SERVICE"
    CIVIC_ENGAGEMENT = "CIVIC_ENGAGEMENT"
    ENVIRONMENTAL = "ENVIRONMENTAL"
    HEALTH_WELLNESS = "HEALTH_WELLNESS"
    DISASTER_RELIEF = "DISASTER_RELIEF"
    EDUCATION_LITERACY = "EDUCATION_LITERACY"
    SOCIAL_JUSTICE = "SOCIAL_JUSTICE"
    ELDER_CARE = "ELDER_CARE"
    ANIMAL_WELFARE = "ANIMAL_WELFARE"
    OTHER = "OTHER"


class ProgramDeliveryMode(StrEnum):
    ON_CAMPUS = "ON_CAMPUS"
    OFF_CAMPUS = "OFF_CAMPUS"
    REMOTE = "REMOTE"
    HYBRID = "HYBRID"


class ProgramStatus(StrEnum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    ARCHIVED = "ARCHIVED"


class OpportunityStatus(StrEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    FULL = "FULL"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class ApplicationStatus(StrEnum):
    DRAFT = "DRAFT"
    APPLIED = "APPLIED"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    WAITLISTED = "WAITLISTED"
    REJECTED = "REJECTED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    WITHDRAWN = "WITHDRAWN"


class ShiftStatus(StrEnum):
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ShiftAssignmentStatus(StrEnum):
    ASSIGNED = "ASSIGNED"
    CONFIRMED = "CONFIRMED"
    COMPLETED = "COMPLETED"
    ABSENT = "ABSENT"
    CANCELLED = "CANCELLED"


class AttendanceStatus(StrEnum):
    CHECKED_IN = "CHECKED_IN"
    COMPLETED = "COMPLETED"
    DISCREPANCY = "DISCREPANCY"
    MISSED_CHECKOUT = "MISSED_CHECKOUT"
    EXCUSED = "EXCUSED"


class AttendanceVerificationMethod(StrEnum):
    QR_CODE = "QR_CODE"
    COORDINATOR_CONFIRMED = "COORDINATOR_CONFIRMED"
    GEOFENCE = "GEOFENCE"
    MANUAL = "MANUAL"


class ServiceHourStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CORRECTION_REQUESTED = "CORRECTION_REQUESTED"
    RESUBMITTED = "RESUBMITTED"


class ReflectionStatus(StrEnum):
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REVISION_REQUESTED = "REVISION_REQUESTED"


class SafetyClearanceStatus(StrEnum):
    PENDING = "PENDING"
    CLEARED = "CLEARED"
    BLOCKED = "BLOCKED"


class CertificateStatus(StrEnum):
    ISSUED = "ISSUED"
    REVOKED = "REVOKED"
    REISSUED = "REISSUED"


# =============================================================================
# DOMAIN ENTITIES
# =============================================================================


class CommunityPartner(TenantScopedModel):
    """External community partner organization collaborating on civic initiatives."""

    __tablename__ = "engagement_community_partners"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_engagement_partner_tenant_name"),
        Index("idx_eng_partner_tenant_status", "tenant_id", "status"),
        Index("idx_eng_partner_tenant_type", "tenant_id", "organization_type"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    organization_type: Mapped[str] = mapped_column(
        String(64), default=PartnerOrgType.NON_PROFIT, nullable=False
    )
    registration_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Primary Contact (institutional / administrative)
    primary_contact_name: Mapped[str] = mapped_column(String(255), nullable=False)
    primary_contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    primary_contact_phone: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Authorized Representative (signatory for agreements)
    authorized_representative_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    authorized_representative_title: Mapped[str | None] = mapped_column(String(128), nullable=True)
    authorized_representative_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    status: Mapped[str] = mapped_column(
        String(32), default=PartnerStatus.ACTIVE, nullable=False
    )
    partnership_purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    engagement_categories: Mapped[list[str]] = mapped_column(JSONType, default=list, nullable=False)

    # Agreement / MoU references
    agreement_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    mou_document_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    review_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Internal responsible contact
    coordinator_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Aggregated partner contributions
    impact_summary_json: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    verified_hours_contributed: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), nullable=False
    )

    # Relationships
    coordinator = relationship("User", foreign_keys=[coordinator_user_id])
    programs: Mapped[list["EngagementProgram"]] = relationship(
        "EngagementProgram", back_populates="partner"
    )
    opportunities: Mapped[list["VolunteerOpportunity"]] = relationship(
        "VolunteerOpportunity", back_populates="partner"
    )


class EngagementProgram(TenantScopedModel):
    """Institution-approved community service or civic impact program."""

    __tablename__ = "engagement_programs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_eng_prog_tenant_code"),
        Index("idx_eng_prog_tenant_status", "tenant_id", "status"),
        Index("idx_eng_prog_tenant_category", "tenant_id", "category"),
        Index("idx_eng_prog_tenant_dept", "tenant_id", "department_id"),
        Index("idx_eng_prog_tenant_dates", "tenant_id", "start_date", "end_date"),
    )

    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(
        String(64), default=ProgramCategory.COMMUNITY_SERVICE, nullable=False
    )
    objectives: Mapped[str | None] = mapped_column(Text, nullable=True)

    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="SET NULL"),
        nullable=True,
    )
    department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    coordinator_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    community_partner_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("engagement_community_partners.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Audience & eligibility
    target_audience: Mapped[str | None] = mapped_column(String(255), nullable=True)
    student_eligibility_criteria: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)

    # Dates
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    registration_deadline: Mapped[date | None] = mapped_column(Date, nullable=True)

    status: Mapped[str] = mapped_column(
        String(32), default=ProgramStatus.DRAFT, nullable=False
    )
    capacity: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    target_service_hours: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), default=Decimal("20.00"), nullable=False
    )

    # Requirements & Delivery
    skills_required: Mapped[list[str]] = mapped_column(JSONType, default=list, nullable=False)
    prerequisites: Mapped[str | None] = mapped_column(Text, nullable=True)
    accessibility_considerations: Mapped[str | None] = mapped_column(Text, nullable=True)
    delivery_mode: Mapped[str] = mapped_column(
        String(32), default=ProgramDeliveryMode.ON_CAMPUS, nullable=False
    )
    location_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location_address: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Approval governance
    approver_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approval_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Impact & Outcomes
    expected_outcomes: Mapped[str | None] = mapped_column(Text, nullable=True)
    sdg_goals: Mapped[list[str]] = mapped_column(JSONType, default=list, nullable=False)

    # Safety & Consent
    safety_requirements_json: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    consent_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    campus = relationship("Campus")
    department = relationship("Department")
    coordinator = relationship("User", foreign_keys=[coordinator_id])
    approver = relationship("User", foreign_keys=[approver_id])
    partner: Mapped["CommunityPartner | None"] = relationship(
        "CommunityPartner", back_populates="programs"
    )
    opportunities: Mapped[list["VolunteerOpportunity"]] = relationship(
        "VolunteerOpportunity", back_populates="program", cascade="all, delete-orphan"
    )
    applications: Mapped[list["ParticipationApplication"]] = relationship(
        "ParticipationApplication", back_populates="program"
    )
    certificates: Mapped[list["EngagementCertificate"]] = relationship(
        "EngagementCertificate", back_populates="program"
    )


class VolunteerOpportunity(TenantScopedModel):
    """Specific volunteering position or activity linked to a program."""

    __tablename__ = "engagement_opportunities"
    __table_args__ = (
        Index("idx_eng_opp_tenant_prog", "tenant_id", "program_id"),
        Index("idx_eng_opp_tenant_status", "tenant_id", "status"),
        Index("idx_eng_opp_tenant_dates", "tenant_id", "start_date", "end_date"),
    )

    program_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("engagement_programs.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(
        String(64), default=ProgramCategory.COMMUNITY_SERVICE, nullable=False
    )
    required_skills: Mapped[list[str]] = mapped_column(JSONType, default=list, nullable=False)
    eligibility_criteria: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)

    available_positions: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    waitlist_capacity: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    application_deadline: Mapped[date | None] = mapped_column(Date, nullable=True)

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)

    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    delivery_mode: Mapped[str] = mapped_column(
        String(32), default=ProgramDeliveryMode.ON_CAMPUS, nullable=False
    )

    expected_hours: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), default=Decimal("10.00"), nullable=False
    )
    shifts_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    status: Mapped[str] = mapped_column(
        String(32), default=OpportunityStatus.PUBLISHED, nullable=False
    )
    prerequisites: Mapped[str | None] = mapped_column(Text, nullable=True)
    safety_guidance: Mapped[str | None] = mapped_column(Text, nullable=True)

    coordinator_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    partner_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("engagement_community_partners.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    program: Mapped["EngagementProgram"] = relationship("EngagementProgram", back_populates="opportunities")
    coordinator = relationship("User", foreign_keys=[coordinator_id])
    partner: Mapped["CommunityPartner | None"] = relationship(
        "CommunityPartner", back_populates="opportunities"
    )
    shifts: Mapped[list["VolunteerShift"]] = relationship(
        "VolunteerShift", back_populates="opportunity", cascade="all, delete-orphan"
    )
    applications: Mapped[list["ParticipationApplication"]] = relationship(
        "ParticipationApplication", back_populates="opportunity", cascade="all, delete-orphan"
    )


class ParticipationApplication(TenantScopedModel):
    """Student application to participate in an engagement opportunity."""

    __tablename__ = "engagement_applications"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "opportunity_id", "student_id",
            name="uq_eng_app_tenant_opp_student",
        ),
        Index("idx_eng_app_tenant_student", "tenant_id", "student_id"),
        Index("idx_eng_app_tenant_status", "tenant_id", "status"),
        Index("idx_eng_app_tenant_prog", "tenant_id", "program_id"),
    )

    opportunity_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("engagement_opportunities.id", ondelete="CASCADE"),
        nullable=False,
    )
    program_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("engagement_programs.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="CASCADE"),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(32), default=ApplicationStatus.APPLIED, nullable=False
    )
    applied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewer_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    waitlist_position: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Student submission
    statement_of_purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    skills_declared: Mapped[list[str]] = mapped_column(JSONType, default=list, nullable=False)

    # Consent & Emergency
    consent_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    consent_signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    emergency_contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Relationships
    opportunity: Mapped["VolunteerOpportunity"] = relationship(
        "VolunteerOpportunity", back_populates="applications"
    )
    program: Mapped["EngagementProgram"] = relationship(
        "EngagementProgram", back_populates="applications"
    )
    student = relationship("StudentProfile")
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    shift_assignments: Mapped[list["ShiftAssignment"]] = relationship(
        "ShiftAssignment", back_populates="application", cascade="all, delete-orphan"
    )


class VolunteerShift(TenantScopedModel):
    """Specific operational time slot / shift for volunteer duties."""

    __tablename__ = "engagement_shifts"
    __table_args__ = (
        Index("idx_eng_shift_tenant_opp", "tenant_id", "opportunity_id"),
        Index("idx_eng_shift_tenant_date", "tenant_id", "shift_date"),
    )

    opportunity_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("engagement_opportunities.id", ondelete="CASCADE"),
        nullable=False,
    )
    program_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("engagement_programs.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    shift_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)

    capacity: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    assigned_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)

    supervisor_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32), default=ShiftStatus.SCHEDULED, nullable=False
    )

    # Relationships
    opportunity: Mapped["VolunteerOpportunity"] = relationship(
        "VolunteerOpportunity", back_populates="shifts"
    )
    supervisor = relationship("User", foreign_keys=[supervisor_id])
    assignments: Mapped[list["ShiftAssignment"]] = relationship(
        "ShiftAssignment", back_populates="shift", cascade="all, delete-orphan"
    )


class ShiftAssignment(TenantScopedModel):
    """Roster record assigning an approved participant to a specific shift."""

    __tablename__ = "engagement_shift_assignments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "shift_id", "student_id", name="uq_eng_shift_student"),
        Index("idx_eng_assign_tenant_shift", "tenant_id", "shift_id"),
        Index("idx_eng_assign_tenant_student", "tenant_id", "student_id"),
    )

    shift_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("engagement_shifts.id", ondelete="CASCADE"),
        nullable=False,
    )
    application_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("engagement_applications.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32), default=ShiftAssignmentStatus.ASSIGNED, nullable=False
    )

    shift: Mapped["VolunteerShift"] = relationship("VolunteerShift", back_populates="assignments")
    application: Mapped["ParticipationApplication"] = relationship(
        "ParticipationApplication", back_populates="shift_assignments"
    )
    student = relationship("StudentProfile")


class ParticipationAttendance(TenantScopedModel):
    """Attendance verification record for volunteer service sessions."""

    __tablename__ = "engagement_attendances"
    __table_args__ = (
        Index("idx_eng_att_tenant_student", "tenant_id", "student_id"),
        Index("idx_eng_att_tenant_prog", "tenant_id", "program_id"),
        Index("idx_eng_att_tenant_shift", "tenant_id", "shift_id"),
    )

    shift_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("engagement_shifts.id", ondelete="SET NULL"),
        nullable=True,
    )
    opportunity_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("engagement_opportunities.id", ondelete="CASCADE"),
        nullable=False,
    )
    program_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("engagement_programs.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="CASCADE"),
        nullable=False,
    )

    check_in_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    check_out_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    verification_method: Mapped[str] = mapped_column(
        String(32), default=AttendanceVerificationMethod.COORDINATOR_CONFIRMED, nullable=False
    )
    verified_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32), default=AttendanceStatus.COMPLETED, nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    student = relationship("StudentProfile")
    verified_by = relationship("User", foreign_keys=[verified_by_user_id])


class ServiceHourEntry(TenantScopedModel):
    """Verifiable student service-hour log submitted for supervisor review."""

    __tablename__ = "engagement_service_hours"
    __table_args__ = (
        Index("idx_eng_hours_tenant_student", "tenant_id", "student_id"),
        Index("idx_eng_hours_tenant_status", "tenant_id", "status"),
        Index("idx_eng_hours_tenant_prog", "tenant_id", "program_id"),
        Index("idx_eng_hours_tenant_date", "tenant_id", "service_date"),
    )

    program_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("engagement_programs.id", ondelete="CASCADE"),
        nullable=False,
    )
    opportunity_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("engagement_opportunities.id", ondelete="SET NULL"),
        nullable=True,
    )
    shift_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("engagement_shifts.id", ondelete="SET NULL"),
        nullable=True,
    )
    attendance_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("engagement_attendances.id", ondelete="SET NULL"),
        nullable=True,
    )
    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="CASCADE"),
        nullable=False,
    )

    service_date: Mapped[date] = mapped_column(Date, nullable=False)
    duration_hours: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    description_of_work: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[str] = mapped_column(
        String(32), default=ServiceHourStatus.PENDING, nullable=False
    )
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    verified_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    supervisor_comments: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    student = relationship("StudentProfile")
    program = relationship("EngagementProgram")
    opportunity = relationship("VolunteerOpportunity")
    verified_by = relationship("User", foreign_keys=[verified_by_id])
    corrections: Mapped[list["ServiceHourCorrectionHistory"]] = relationship(
        "ServiceHourCorrectionHistory",
        back_populates="service_hour",
        cascade="all, delete-orphan",
        order_by="ServiceHourCorrectionHistory.changed_at.desc()",
    )


class ServiceHourCorrectionHistory(TenantScopedModel):
    """Audit ledger tracking manual adjustments or corrections to service hours."""

    __tablename__ = "engagement_hour_corrections"
    __table_args__ = (
        Index("idx_eng_correct_hour_id", "service_hour_id"),
        Index("idx_eng_correct_tenant", "tenant_id"),
    )

    service_hour_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("engagement_service_hours.id", ondelete="CASCADE"),
        nullable=False,
    )
    previous_hours: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    new_hours: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    reason_for_change: Mapped[str] = mapped_column(Text, nullable=False)
    changed_by_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    service_hour: Mapped["ServiceHourEntry"] = relationship(
        "ServiceHourEntry", back_populates="corrections"
    )
    changed_by = relationship("User", foreign_keys=[changed_by_user_id])


class ReflectionSubmission(TenantScopedModel):
    """Student reflection and civic outcome evidence submission."""

    __tablename__ = "engagement_reflections"
    __table_args__ = (
        Index("idx_eng_refl_tenant_student", "tenant_id", "student_id"),
        Index("idx_eng_refl_tenant_prog", "tenant_id", "program_id"),
        Index("idx_eng_refl_tenant_status", "tenant_id", "status"),
    )

    program_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("engagement_programs.id", ondelete="CASCADE"),
        nullable=False,
    )
    opportunity_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("engagement_opportunities.id", ondelete="SET NULL"),
        nullable=True,
    )
    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="CASCADE"),
        nullable=False,
    )

    reflection_text: Mapped[str] = mapped_column(Text, nullable=False)
    learning_outcomes_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    skills_developed: Mapped[list[str]] = mapped_column(JSONType, default=list, nullable=False)
    community_outcomes: Mapped[str | None] = mapped_column(Text, nullable=True)
    deliverables_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sdg_impact_mapping: Mapped[list[str]] = mapped_column(JSONType, default=list, nullable=False)
    attachment_document_ids: Mapped[list[str]] = mapped_column(JSONType, default=list, nullable=False)

    consent_for_impact_showcase: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    status: Mapped[str] = mapped_column(
        String(32), default=ReflectionStatus.SUBMITTED, nullable=False
    )
    reviewer_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    feedback_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-5 rating

    student = relationship("StudentProfile")
    program = relationship("EngagementProgram")
    reviewer = relationship("User", foreign_keys=[reviewer_id])


class SafetyAndConsentRecord(TenantScopedModel):
    """Program-level safety checklist, briefings, and consent records."""

    __tablename__ = "engagement_safety_consents"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "program_id", "student_id",
            name="uq_eng_safety_prog_student",
        ),
        Index("idx_eng_safety_tenant_status", "tenant_id", "coordinator_clearance_status"),
    )

    program_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("engagement_programs.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="CASCADE"),
        nullable=False,
    )

    safety_briefing_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    safety_acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    parental_consent_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    parental_consent_received: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    risk_assessment_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    emergency_contact_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    incident_reference_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    coordinator_clearance_status: Mapped[str] = mapped_column(
        String(32), default=SafetyClearanceStatus.PENDING, nullable=False
    )
    coordinator_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    cleared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    student = relationship("StudentProfile")
    program = relationship("EngagementProgram")
    coordinator = relationship("User", foreign_keys=[coordinator_id])


class EngagementCertificate(TenantScopedModel):
    """Verifiable credential issued for verified community service and civic impact."""

    __tablename__ = "engagement_certificates"
    __table_args__ = (
        UniqueConstraint("tenant_id", "certificate_number", name="uq_eng_cert_number"),
        Index("idx_eng_cert_tenant_student", "tenant_id", "student_id"),
        Index("idx_eng_cert_tenant_hash", "tenant_id", "verification_hash"),
    )

    certificate_number: Mapped[str] = mapped_column(String(64), nullable=False)
    program_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("engagement_programs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="RESTRICT"),
        nullable=False,
    )

    recipient_name: Mapped[str] = mapped_column(String(255), nullable=False)
    recipient_roll_number: Mapped[str] = mapped_column(String(64), nullable=False)
    recipient_department: Mapped[str] = mapped_column(String(128), nullable=False)

    total_verified_hours: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    service_category: Mapped[str] = mapped_column(String(64), nullable=False)
    program_name: Mapped[str] = mapped_column(String(255), nullable=False)
    skills_certified: Mapped[list[str]] = mapped_column(JSONType, default=list, nullable=False)

    issue_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    issuing_authority_name: Mapped[str] = mapped_column(String(255), nullable=False)
    issued_by_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    verification_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    qr_verification_url: Mapped[str] = mapped_column(String(512), nullable=False)

    status: Mapped[str] = mapped_column(
        String(32), default=CertificateStatus.ISSUED, nullable=False
    )
    revocation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    document_storage_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    # Relationships
    program: Mapped["EngagementProgram"] = relationship("EngagementProgram", back_populates="certificates")
    student = relationship("StudentProfile")
    issued_by = relationship("User", foreign_keys=[issued_by_user_id])
    revoked_by = relationship("User", foreign_keys=[revoked_by_id])

