"""CampusOS Enterprise Hostel, Residential Life, Room Allocation & Accommodation Models (Step 54).

CampusOS Tagline: "One Campus. One System. One Source of Truth."

Enterprise Data Models Governing:
1. Centralized Hostel & Residential Facility Registry (Hostel, Block, Floor, Room, Bed)
2. Authoritative Room & Bed Inventory with State Machine & Concurrency Controls
3. Student Accommodation Applications & Cycle Management
4. Allocation, Transfer & Waitlist Engine
5. Resident Check-In, Check-Out & Resident Lifecycle (Inventory handover, damage assessment)
6. Residential Fees, Proration & Finance Integration
7. Mess & Meal-Plan Management (Headcounts, Dietary preferences)
8. Hostel Attendance, Outings, Leaves & Curfew Management
9. Visitor & Gate-Pass Management
10. Maintenance Complaints & Residential Service Requests (Linked to Asset Work Orders)
11. Residential Safety, Incident Reports & Safety Inspections
12. Night Roll-Call Attendance
"""

from datetime import date, datetime, time
from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

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
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TenantScopedModel

# Cross-dialect JSON type for PostgreSQL JSONB and SQLite JSON
JSONType = JSON().with_variant(JSONB, "postgresql")


# =============================================================================
# ENUM TAXONOMY
# =============================================================================


class HostelGender(StrEnum):
    """Permitted hostel gender segregation policy."""

    MALE = "MALE"
    FEMALE = "FEMALE"
    CO_ED = "CO_ED"


class HostelType(StrEnum):
    """Institutional classification of residential facility."""

    BOYS = "BOYS"
    GIRLS = "GIRLS"
    CO_ED = "CO_ED"
    POSTGRADUATE = "POSTGRADUATE"
    INTERNATIONAL = "INTERNATIONAL"
    STAFF = "STAFF"
    SPECIAL_NEEDS = "SPECIAL_NEEDS"
    GUEST_HOUSE = "GUEST_HOUSE"
    OTHER = "OTHER"


class HostelOperationalStatus(StrEnum):
    """Operational status of hostel or block."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"
    DECOMMISSIONED = "DECOMMISSIONED"


class RoomType(StrEnum):
    """Dormitory room layout and capacity configuration."""

    SINGLE = "SINGLE"
    DOUBLE = "DOUBLE"
    TRIPLE = "TRIPLE"
    FOUR_SHARING = "FOUR_SHARING"
    DORMITORY = "DORMITORY"
    SUITE = "SUITE"
    DELUXE = "DELUXE"


class BedStatus(StrEnum):
    """Authoritative bed state machine."""

    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    OCCUPIED = "OCCUPIED"
    BLOCKED = "BLOCKED"
    UNDER_MAINTENANCE = "UNDER_MAINTENANCE"
    RETIRED = "RETIRED"


class ApplicationCycleStatus(StrEnum):
    """Accommodation application cycle lifecycle."""

    DRAFT = "DRAFT"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    ARCHIVED = "ARCHIVED"


class AccommodationApplicationStatus(StrEnum):
    """Student accommodation application status."""

    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    WAITLISTED = "WAITLISTED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"
    ALLOCATED = "ALLOCATED"


class AllocationStatus(StrEnum):
    """Bed reservation and allocation status."""

    RESERVED = "RESERVED"
    ALLOCATED = "ALLOCATED"
    CHECKED_IN = "CHECKED_IN"
    CHECKED_OUT = "CHECKED_OUT"
    TRANSFERRED = "TRANSFERRED"
    CANCELLED = "CANCELLED"


class ResidentLifecycleStatus(StrEnum):
    """Physical resident lifecycle state."""

    PENDING_CHECKIN = "PENDING_CHECKIN"
    CHECKED_IN = "CHECKED_IN"
    ACTIVE = "ACTIVE"
    TEMPORARILY_ABSENT = "TEMPORARILY_ABSENT"
    CHECKED_OUT = "CHECKED_OUT"
    TRANSFERRED = "TRANSFERRED"
    EVICTED = "EVICTED"


class CheckoutReason(StrEnum):
    """Official reason for student departure."""

    END_OF_TERM = "END_OF_TERM"
    COURSE_COMPLETION = "COURSE_COMPLETION"
    WITHDRAWAL = "WITHDRAWAL"
    TRANSFER = "TRANSFER"
    DISCIPLINARY = "DISCIPLINARY"
    MEDICAL = "MEDICAL"
    PERSONAL = "PERSONAL"
    OTHER = "OTHER"


class FeePlanBillingCycle(StrEnum):
    """Residential billing cycle."""

    ANNUAL = "ANNUAL"
    SEMESTER = "SEMESTER"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    ACADEMIC_YEAR = "ACADEMIC_YEAR"


class MealType(StrEnum):
    """Mess dietary preference category."""

    VEG = "VEG"
    NON_VEG = "NON_VEG"
    JAIN = "JAIN"
    SPECIAL = "SPECIAL"


class MealEnrollmentStatus(StrEnum):
    """Status of meal plan enrollment."""

    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"


class OutingType(StrEnum):
    """Resident departure permit type."""

    DAY_OUTING = "DAY_OUTING"
    NIGHT_OUT = "NIGHT_OUT"
    WEEKEND_HOME = "WEEKEND_HOME"
    EMERGENCY = "EMERGENCY"
    OFFICIAL_DUTY = "OFFICIAL_DUTY"


class OutingStatus(StrEnum):
    """Outing and leave pass lifecycle status."""

    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CHECKED_OUT = "CHECKED_OUT"
    DEPARTED = "DEPARTED"
    RETURNED = "RETURNED"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"


class VisitorStatus(StrEnum):
    """Visitor pass lifecycle status."""

    EXPECTED = "EXPECTED"
    CHECKED_IN = "CHECKED_IN"
    CHECKED_OUT = "CHECKED_OUT"
    OVERDUE = "OVERDUE"
    REVOKED = "REVOKED"
    DENIED = "DENIED"


class GatePassStatus(StrEnum):
    """Gate security pass lifecycle."""

    ISSUED = "ISSUED"
    ACTIVE = "ACTIVE"
    USED = "USED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class ResidentialServiceCategory(StrEnum):
    """Category of hostel maintenance and service requests."""

    ELECTRICAL = "ELECTRICAL"
    PLUMBING = "PLUMBING"
    CARPENTRY_FURNITURE = "CARPENTRY_FURNITURE"
    INTERNET_WIFI = "INTERNET_WIFI"
    CLEANING_HYGIENE = "CLEANING_HYGIENE"
    APPLIANCES = "APPLIANCES"
    PEST_CONTROL = "PEST_CONTROL"
    CIVIL_MASONRY = "CIVIL_MASONRY"
    OTHER = "OTHER"


class ResidentialServicePriority(StrEnum):
    """Priority grading for residential service requests."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    EMERGENCY = "EMERGENCY"


class ResidentialServiceStatus(StrEnum):
    """Ticket resolution state."""

    OPEN = "OPEN"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REOPENED = "REOPENED"


class ResidentialIncidentType(StrEnum):
    """Hostel security or safety incident classification."""

    MEDICAL_EMERGENCY = "MEDICAL_EMERGENCY"
    DISCIPLINARY = "DISCIPLINARY"
    THEFT_DAMAGE = "THEFT_DAMAGE"
    UNAUTHORIZED_ENTRY = "UNAUTHORIZED_ENTRY"
    FIRE_SAFETY = "FIRE_SAFETY"
    SAFETY_HAZARD = "SAFETY_HAZARD"
    RAGGING_HARASSMENT = "RAGGING_HARASSMENT"
    SUBSTANCE_VIOLATION = "SUBSTANCE_VIOLATION"
    VIOLENCE_ALTERCATION = "VIOLENCE_ALTERCATION"
    OTHER = "OTHER"


class ResidentialIncidentSeverity(StrEnum):
    """Incident severity classification."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ResidentialIncidentStatus(StrEnum):
    """Incident investigation and action state."""

    REPORTED = "REPORTED"
    UNDER_INVESTIGATION = "UNDER_INVESTIGATION"
    ACTION_TAKEN = "ACTION_TAKEN"
    CLOSED = "CLOSED"
    ESCALATED = "ESCALATED"


class SafetyInspectionStatus(StrEnum):
    """Inspection workflow state."""

    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FOLLOW_UP_REQUIRED = "FOLLOW_UP_REQUIRED"


class NightAttendanceStatus(StrEnum):
    """Resident night attendance roll-call result."""

    PRESENT = "PRESENT"
    ON_LEAVE = "ON_LEAVE"
    PERMITTED_OUTING = "PERMITTED_OUTING"
    ABSENT_UNAUTHORIZED = "ABSENT_UNAUTHORIZED"


# =============================================================================
# 1. HOSTEL & RESIDENTIAL FACILITY REGISTRY
# =============================================================================


class Hostel(TenantScopedModel):
    """Student residential facility / hall of residence."""

    __tablename__ = "infrastructure_hostels"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_hostels_tenant_code"),
        Index("idx_hostels_tenant_campus", "tenant_id", "campus_id"),
        Index("idx_hostels_tenant_status", "tenant_id", "status"),
    )

    campus_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="RESTRICT"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    gender: Mapped[str] = mapped_column(String(16), default=HostelGender.MALE.value, nullable=False)
    hostel_type: Mapped[str] = mapped_column(String(32), default=HostelType.BOYS.value, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=HostelOperationalStatus.ACTIVE.value, nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    curfew_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(128), nullable=True)
    rules_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    amenities: Mapped[list[str] | None] = mapped_column(JSONType, nullable=True)
    visitor_policy: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    emergency_contacts: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONType, nullable=True)

    warden_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    assistant_warden_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    blocks: Mapped[list["HostelBlock"]] = relationship(
        back_populates="hostel", cascade="all, delete-orphan"
    )
    residents: Mapped[list["HostelResident"]] = relationship(back_populates="hostel")


class HostelBlock(Base):
    """Block or wing within a hostel."""

    __tablename__ = "infrastructure_hostel_blocks"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    hostel_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_hostels.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g. "A Block", "North Wing"
    code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    hostel: Mapped["Hostel"] = relationship(back_populates="blocks")
    floors: Mapped[list["HostelFloor"]] = relationship(
        back_populates="block", cascade="all, delete-orphan"
    )


class HostelFloor(Base):
    """Floor level within a hostel block."""

    __tablename__ = "infrastructure_hostel_floors"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    block_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_hostel_blocks.id", ondelete="CASCADE"),
        nullable=False,
    )
    floor_number: Mapped[int] = mapped_column(nullable=False)
    name: Mapped[str | None] = mapped_column(String(64), nullable=True)  # e.g. "Ground Floor"
    is_accessible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    block: Mapped["HostelBlock"] = relationship(back_populates="floors")
    rooms: Mapped[list["HostelRoom"]] = relationship(
        back_populates="floor", cascade="all, delete-orphan"
    )


class HostelRoom(Base):
    """Dormitory room within a floor."""

    __tablename__ = "infrastructure_hostel_rooms"
    __table_args__ = (
        Index("idx_hostel_rooms_floor", "floor_id"),
        Index("idx_hostel_rooms_number", "room_number"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    floor_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_hostel_floors.id", ondelete="CASCADE"),
        nullable=False,
    )
    room_number: Mapped[str] = mapped_column(String(32), nullable=False)
    room_type: Mapped[str] = mapped_column(
        String(32), default=RoomType.DOUBLE.value, nullable=False
    )
    capacity: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    is_accessible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_air_conditioned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_attached_bathroom: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=HostelOperationalStatus.ACTIVE.value, nullable=False
    )
    amenities: Mapped[list[str] | None] = mapped_column(JSONType, nullable=True)
    restrictions: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)

    floor: Mapped["HostelFloor"] = relationship(back_populates="rooms")
    beds: Mapped[list["HostelBed"]] = relationship(
        back_populates="room", cascade="all, delete-orphan"
    )


class HostelBed(Base):
    """Individual addressable bed within a hostel room."""

    __tablename__ = "infrastructure_hostel_beds"
    __table_args__ = (
        Index("idx_hostel_beds_room", "room_id"),
        Index("idx_hostel_beds_code", "bed_code"),
        Index("idx_hostel_beds_status", "status"),
        UniqueConstraint("room_id", "bed_code", name="uq_room_bed_code"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    room_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_hostel_rooms.id", ondelete="CASCADE"),
        nullable=False,
    )
    bed_code: Mapped[str] = mapped_column(String(16), nullable=False)  # e.g. "B101-A"
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=BedStatus.AVAILABLE.value, nullable=False
    )
    blocked_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    blocked_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    reserved_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    room: Mapped["HostelRoom"] = relationship(back_populates="beds")
    allocations: Mapped[list["HostelAllocation"]] = relationship(
        back_populates="bed", foreign_keys="[HostelAllocation.bed_id]"
    )


# =============================================================================
# 2. ACCOMMODATION APPLICATIONS & CYCLES
# =============================================================================


class HostelApplicationCycle(TenantScopedModel):
    """Institutional accommodation application intake window."""

    __tablename__ = "residential_application_cycles"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_appl_cycle_tenant_code"),
        Index("idx_appl_cycle_tenant_status", "tenant_id", "status"),
    )

    academic_year_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_academic_years.id", ondelete="RESTRICT"),
        nullable=False,
    )
    cycle_name: Mapped[str] = mapped_column(String(128), nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=ApplicationCycleStatus.DRAFT.value, nullable=False
    )
    max_applications: Mapped[int | None] = mapped_column(Integer, nullable=True)
    eligibility_criteria: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    priority_rules: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)

    applications: Mapped[list["HostelApplication"]] = relationship(back_populates="cycle")


class HostelApplication(TenantScopedModel):
    """Student application for hostel accommodation."""

    __tablename__ = "residential_applications"
    __table_args__ = (
        UniqueConstraint("tenant_id", "cycle_id", "student_id", name="uq_appl_cycle_student"),
        Index("idx_appl_tenant_student", "tenant_id", "student_id"),
        Index("idx_appl_tenant_status", "tenant_id", "status"),
    )

    cycle_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("residential_application_cycles.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    application_number: Mapped[str] = mapped_column(String(32), nullable=False)
    preferred_hostel_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_hostels.id", ondelete="SET NULL"),
        nullable=True,
    )
    preferred_room_type: Mapped[str] = mapped_column(
        String(32), default=RoomType.DOUBLE.value, nullable=False
    )
    special_requests: Mapped[str | None] = mapped_column(Text, nullable=True)
    accessibility_needed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    disability_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    emergency_contact_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    priority_score: Mapped[Decimal] = mapped_column(
        Numeric(8, 2), default=Decimal("0.00"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), default=AccommodationApplicationStatus.SUBMITTED.value, nullable=False
    )
    reviewer_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    allocated_bed_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_hostel_beds.id", ondelete="SET NULL"),
        nullable=True,
    )

    cycle: Mapped["HostelApplicationCycle"] = relationship(back_populates="applications")


# =============================================================================
# 3. ALLOCATION & WAITLIST
# =============================================================================


class HostelAllocation(TenantScopedModel):
    """Historical and active bed reservation ledger."""

    __tablename__ = "infrastructure_hostel_allocations"
    __table_args__ = (
        Index("idx_allocations_tenant_student", "tenant_id", "student_id"),
        Index("idx_allocations_tenant_bed", "tenant_id", "bed_id"),
        Index("idx_allocations_tenant_status", "tenant_id", "status"),
    )

    bed_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_hostel_beds.id", ondelete="RESTRICT"),
        nullable=False,
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
    application_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("residential_applications.id", ondelete="SET NULL"),
        nullable=True,
    )
    check_in_date: Mapped[date] = mapped_column(Date, nullable=False)
    check_out_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    reserved_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default=AllocationStatus.ALLOCATED.value, nullable=False
    )
    allocated_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reallocation_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    previous_bed_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_hostel_beds.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    bed: Mapped["HostelBed"] = relationship(
        back_populates="allocations", foreign_keys=[bed_id]
    )
    resident_record: Mapped["HostelResident | None"] = relationship(
        back_populates="allocation", uselist=False
    )


# =============================================================================
# 4. RESIDENT LIFECYCLE (CHECK-IN & CHECK-OUT)
# =============================================================================


class HostelResident(TenantScopedModel):
    """Active or past physical hostel resident lifecycle record."""

    __tablename__ = "residential_residents"
    __table_args__ = (
        Index("idx_residents_tenant_student", "tenant_id", "student_id"),
        Index("idx_residents_tenant_hostel", "tenant_id", "hostel_id"),
        Index("idx_residents_tenant_status", "tenant_id", "status"),
    )

    allocation_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_hostel_allocations.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    bed_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_hostel_beds.id", ondelete="RESTRICT"),
        nullable=False,
    )
    hostel_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_hostels.id", ondelete="RESTRICT"),
        nullable=False,
    )
    academic_year_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_academic_years.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32), default=ResidentLifecycleStatus.CHECKED_IN.value, nullable=False
    )
    check_in_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    checked_in_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    key_card_issued: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    key_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    facilities_condition_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    inventory_handover: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    expected_departure_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Check-out lifecycle
    check_out_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    checked_out_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    checkout_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    room_condition_on_checkout: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_returned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    damage_assessment_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    damage_charges_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    damage_invoice_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("finance_invoices.id", ondelete="SET NULL"),
        nullable=True,
    )
    cleared_by_finance: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    allocation: Mapped["HostelAllocation"] = relationship(back_populates="resident_record")
    hostel: Mapped["Hostel"] = relationship(back_populates="residents")


# =============================================================================
# 5. RESIDENTIAL FEES & FINANCIAL INTEGRATION
# =============================================================================


class HostelFeePlan(TenantScopedModel):
    """Configurable residential fee structure and rent schedule."""

    __tablename__ = "residential_fee_plans"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_fee_plan_tenant_code"),
        Index("idx_fee_plans_tenant_hostel", "tenant_id", "hostel_id"),
    )

    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    hostel_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_hostels.id", ondelete="CASCADE"),
        nullable=True,
    )
    room_type: Mapped[str] = mapped_column(
        String(32), default=RoomType.DOUBLE.value, nullable=False
    )
    billing_cycle: Mapped[str] = mapped_column(
        String(32), default=FeePlanBillingCycle.SEMESTER.value, nullable=False
    )
    rent_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    mess_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    deposit_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    utility_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    amenities_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    proration_rule: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)


# =============================================================================
# 6. MESS & MEAL-PLAN MANAGEMENT
# =============================================================================


class HostelMealPlan(TenantScopedModel):
    """Mess catering plan and meal schedule."""

    __tablename__ = "residential_meal_plans"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_meal_plan_tenant_code"),
        Index("idx_meal_plans_tenant_hostel", "tenant_id", "hostel_id"),
    )

    hostel_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_hostels.id", ondelete="CASCADE"),
        nullable=True,
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    meal_type: Mapped[str] = mapped_column(String(32), default=MealType.VEG.value, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    monthly_rate: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    daily_rate: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), nullable=False
    )
    serves_breakfast: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    serves_lunch: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    serves_snacks: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    serves_dinner: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    enrollments: Mapped[list["HostelMealEnrollment"]] = relationship(back_populates="meal_plan")


class HostelMealEnrollment(TenantScopedModel):
    """Student enrollment in a residential meal plan."""

    __tablename__ = "residential_meal_enrollments"
    __table_args__ = (
        Index("idx_meal_enroll_tenant_student", "tenant_id", "student_id"),
        Index("idx_meal_enroll_tenant_plan", "tenant_id", "meal_plan_id"),
    )

    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    meal_plan_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("residential_meal_plans.id", ondelete="RESTRICT"),
        nullable=False,
    )
    resident_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("residential_residents.id", ondelete="SET NULL"),
        nullable=True,
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    dietary_requirements: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default=MealEnrollmentStatus.ACTIVE.value, nullable=False
    )

    meal_plan: Mapped["HostelMealPlan"] = relationship(back_populates="enrollments")


# =============================================================================
# 7. OUTINGS, LEAVE PASSES & RESIDENTIAL ATTENDANCE
# =============================================================================


class HostelLeavePass(TenantScopedModel):
    """Student outing or home leave permission pass."""

    __tablename__ = "infrastructure_hostel_passes"
    __table_args__ = (
        Index("idx_hostel_passes_tenant_student", "tenant_id", "student_id"),
        Index("idx_hostel_passes_tenant_status", "tenant_id", "status"),
        Index("idx_hostel_passes_tenant_times", "tenant_id", "departure_time", "expected_return_time"),
    )

    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    hostel_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_hostels.id", ondelete="SET NULL"),
        nullable=True,
    )
    outing_type: Mapped[str] = mapped_column(
        String(32), default=OutingType.DAY_OUTING.value, nullable=False
    )
    pass_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    departure_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expected_return_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_departure_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    actual_return_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    destination: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    parent_consent_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    parent_contact_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    approved_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32), default=OutingStatus.REQUESTED.value, nullable=False
    )


class HostelNightAttendance(TenantScopedModel):
    """Night roll-call attendance record for residential students."""

    __tablename__ = "residential_night_attendances"
    __table_args__ = (
        UniqueConstraint("tenant_id", "attendance_date", "resident_id", name="uq_night_att_resident_date"),
        Index("idx_night_att_tenant_hostel_date", "tenant_id", "hostel_id", "attendance_date"),
    )

    hostel_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_hostels.id", ondelete="CASCADE"),
        nullable=False,
    )
    resident_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("residential_residents.id", ondelete="CASCADE"),
        nullable=False,
    )
    attendance_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=NightAttendanceStatus.PRESENT.value, nullable=False
    )
    checked_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    remarks: Mapped[str | None] = mapped_column(String(255), nullable=True)


# =============================================================================
# 8. VISITOR & GATE-PASS MANAGEMENT
# =============================================================================


class HostelVisitor(TenantScopedModel):
    """Registered hostel visitor entry and exit record."""

    __tablename__ = "residential_visitors"
    __table_args__ = (
        Index("idx_visitors_tenant_hostel", "tenant_id", "hostel_id"),
        Index("idx_visitors_tenant_student", "tenant_id", "host_student_id"),
        Index("idx_visitors_tenant_status", "tenant_id", "status"),
    )

    hostel_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_hostels.id", ondelete="CASCADE"),
        nullable=False,
    )
    host_student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    visitor_name: Mapped[str] = mapped_column(String(128), nullable=False)
    visitor_phone: Mapped[str] = mapped_column(String(32), nullable=False)
    visitor_id_proof_type: Mapped[str] = mapped_column(String(32), default="GOVT_ID", nullable=False)
    visitor_id_proof_number: Mapped[str] = mapped_column(String(64), nullable=False)
    visitor_relation: Mapped[str] = mapped_column(String(64), default="PARENT", nullable=False)
    purpose: Mapped[str] = mapped_column(String(255), nullable=False)
    pass_code: Mapped[str] = mapped_column(String(32), nullable=False)
    expected_check_in: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expected_check_out: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_check_in: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_check_out: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32), default=VisitorStatus.EXPECTED.value, nullable=False
    )
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)


class HostelGatePass(TenantScopedModel):
    """Resident gate pass for campus ingress/egress validation."""

    __tablename__ = "residential_gate_passes"
    __table_args__ = (
        UniqueConstraint("tenant_id", "pass_code", name="uq_gate_pass_tenant_code"),
        Index("idx_gate_passes_tenant_student", "tenant_id", "student_id"),
        Index("idx_gate_passes_tenant_status", "tenant_id", "status"),
    )

    resident_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("residential_residents.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    hostel_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_hostels.id", ondelete="CASCADE"),
        nullable=False,
    )
    pass_code: Mapped[str] = mapped_column(String(32), nullable=False)
    purpose: Mapped[str] = mapped_column(String(255), nullable=False)
    destination: Mapped[str | None] = mapped_column(String(255), nullable=True)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=GatePassStatus.ISSUED.value, nullable=False
    )
    verified_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_exit_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_entry_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# =============================================================================
# 9. MAINTENANCE, COMPLAINTS & SERVICE REQUESTS
# =============================================================================


class HostelComplaint(TenantScopedModel):
    """Hostel maintenance ticket and student service request."""

    __tablename__ = "infrastructure_hostel_complaints"
    __table_args__ = (
        Index("idx_hostel_complaints_tenant_student", "tenant_id", "student_id"),
        Index("idx_hostel_complaints_tenant_room", "tenant_id", "room_id"),
        Index("idx_hostel_complaints_tenant_status", "tenant_id", "status"),
    )

    ticket_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    hostel_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_hostels.id", ondelete="CASCADE"),
        nullable=True,
    )
    room_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_hostel_rooms.id", ondelete="RESTRICT"),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(
        String(32), default=ResidentialServiceCategory.ELECTRICAL.value, nullable=False
    )
    priority: Mapped[str] = mapped_column(
        String(32), default=ResidentialServicePriority.MEDIUM.value, nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(128), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=ResidentialServiceStatus.OPEN.value, nullable=False
    )
    assigned_to_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    work_order_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("asset_maintenance_work_orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    sla_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    student_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    student_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)


# =============================================================================
# 10. RESIDENTIAL SAFETY, INCIDENTS & INSPECTIONS
# =============================================================================


class HostelIncident(TenantScopedModel):
    """Confidential incident report in residential halls."""

    __tablename__ = "residential_incidents"
    __table_args__ = (
        Index("idx_incidents_tenant_hostel", "tenant_id", "hostel_id"),
        Index("idx_incidents_tenant_severity", "tenant_id", "severity"),
        Index("idx_incidents_tenant_status", "tenant_id", "status"),
    )

    incident_number: Mapped[str] = mapped_column(String(32), nullable=False)
    hostel_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_hostels.id", ondelete="CASCADE"),
        nullable=False,
    )
    incident_type: Mapped[str] = mapped_column(
        String(32), default=ResidentialIncidentType.OTHER.value, nullable=False
    )
    severity: Mapped[str] = mapped_column(
        String(32), default=ResidentialIncidentSeverity.MEDIUM.value, nullable=False
    )
    incident_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    location_description: Mapped[str] = mapped_column(String(255), nullable=False)
    reporter_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    involved_student_ids: Mapped[list[str] | None] = mapped_column(JSONType, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)  # Confidential narrative
    action_taken: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_disciplinary_referral: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=ResidentialIncidentStatus.REPORTED.value, nullable=False
    )
    assigned_warden_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class HostelSafetyInspection(TenantScopedModel):
    """Periodic residential facility safety and hygiene audit."""

    __tablename__ = "residential_safety_inspections"
    __table_args__ = (
        Index("idx_inspections_tenant_hostel", "tenant_id", "hostel_id"),
        Index("idx_inspections_tenant_date", "tenant_id", "inspection_date"),
    )

    hostel_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_hostels.id", ondelete="CASCADE"),
        nullable=False,
    )
    inspection_date: Mapped[date] = mapped_column(Date, nullable=False)
    inspector_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    fire_safety_passed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    electrical_safety_passed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    hygiene_passed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    structural_passed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    checklist_results: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    critical_findings: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_items: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONType, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default=SafetyInspectionStatus.COMPLETED.value, nullable=False
    )
