"""CampusOS Enterprise Student Housing, Off-Campus Accommodation, Landlord Partnerships & Residential Compliance Models (Step 66).

CampusOS Tagline: "One Campus. One System. One Source of Truth."

Enterprise Data Models Governing:
1. Accommodation Providers & Landlord Partnership Directory
2. Accommodation Property Registry (Campus Hostels, Off-Campus Private Hostels, Apartments, Shared Housing)
3. Accommodation Units & Bed Capacity Inventory
4. Student Housing Requests & Waitlist Engine
5. Housing Offers & Formal Allocation Lifecycle
6. Housing Agreements & Digital Leases with Finance Integration
7. Resident Check-In & Check-Out Audits with Damage Assessment
8. Property Safety, Fire & Compliance Inspections
9. Housing Maintenance Requests with Asset Work Order Linkage
"""

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any
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
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantScopedModel

# Cross-dialect JSON type for PostgreSQL JSONB and SQLite JSON
JSONType = JSON().with_variant(JSONB, "postgresql")


# =============================================================================
# ENUM TAXONOMY
# =============================================================================

class ProviderType(StrEnum):
    """Classification of accommodation partner or provider."""
    PRIVATE_LANDLORD = "PRIVATE_LANDLORD"
    HOUSING_COMPANY = "HOUSING_COMPANY"
    STUDENT_RESIDENCE_TRUST = "STUDENT_RESIDENCE_TRUST"
    UNIVERSITY_AFFILIATE = "UNIVERSITY_AFFILIATE"
    HOMESTAY_HOST = "HOMESTAY_HOST"


class ProviderVerificationStatus(StrEnum):
    """Institutional verification state of provider."""
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    SUSPENDED = "SUSPENDED"
    TERMINATED = "TERMINATED"


class PropertyType(StrEnum):
    """Structural type of accommodation property."""
    CAMPUS_HOSTEL = "CAMPUS_HOSTEL"
    OFF_CAMPUS_HOSTEL = "OFF_CAMPUS_HOSTEL"
    PRIVATE_APARTMENT = "PRIVATE_APARTMENT"
    SHARED_HOUSING = "SHARED_HOUSING"
    HOMESTAY = "HOMESTAY"
    STUDENT_VILLAGE = "STUDENT_VILLAGE"


class PropertyLifecycleStatus(StrEnum):
    """State machine governing property discoverability and operations."""
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"
    SUSPENDED = "SUSPENDED"
    ARCHIVED = "ARCHIVED"


class UnitType(StrEnum):
    """Room or apartment configuration type."""
    SINGLE_OCCUPANCY = "SINGLE_OCCUPANCY"
    DOUBLE_OCCUPANCY = "DOUBLE_OCCUPANCY"
    TRIPLE_OCCUPANCY = "TRIPLE_OCCUPANCY"
    DORMITORY = "DORMITORY"
    STUDIO_APARTMENT = "STUDIO_APARTMENT"
    MULTI_BED_APARTMENT = "MULTI_BED_APARTMENT"


class UnitStatus(StrEnum):
    """Operational status of a room or apartment unit."""
    AVAILABLE = "AVAILABLE"
    FULL = "FULL"
    MAINTENANCE = "MAINTENANCE"
    TEMPORARILY_CLOSED = "TEMPORARILY_CLOSED"
    RESERVED = "RESERVED"


class HousingRequestStatus(StrEnum):
    """Lifecycle of a student accommodation request."""
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    ADDITIONAL_INFO_REQUIRED = "ADDITIONAL_INFO_REQUIRED"
    APPROVED = "APPROVED"
    WAITLISTED = "WAITLISTED"
    OFFERED = "OFFERED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class HousingOfferStatus(StrEnum):
    """Status of an accommodation offer sent to a student."""
    OFFERED = "OFFERED"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class HousingAssignmentStatus(StrEnum):
    """State of a confirmed housing placement."""
    ASSIGNED = "ASSIGNED"
    CHECKED_IN = "CHECKED_IN"
    ACTIVE = "ACTIVE"
    TRANSFER_REQUESTED = "TRANSFER_REQUESTED"
    TRANSFERRED = "TRANSFERRED"
    CHECKED_OUT = "CHECKED_OUT"
    TERMINATED = "TERMINATED"
    CANCELLED = "CANCELLED"


class AgreementStatus(StrEnum):
    """Legal lease or housing contract lifecycle."""
    DRAFT = "DRAFT"
    PENDING_SIGNATURE = "PENDING_SIGNATURE"
    ACTIVE = "ACTIVE"
    EXPIRING_SOON = "EXPIRING_SOON"
    RENEWED = "RENEWED"
    TERMINATED = "TERMINATED"
    EXPIRED = "EXPIRED"


class InspectionType(StrEnum):
    """Type of safety, fire, or quality compliance inspection."""
    ANNUAL_COMPLIANCE = "ANNUAL_COMPLIANCE"
    SAFETY_FIRE = "SAFETY_FIRE"
    HYGIENE_HEALTH = "HYGIENE_HEALTH"
    COMPLAINT_INVESTIGATION = "COMPLAINT_INVESTIGATION"
    PROVIDER_APPROVAL_AUDIT = "PROVIDER_APPROVAL_AUDIT"


class InspectionOutcome(StrEnum):
    """Formal audit result of property inspection."""
    PASSED = "PASSED"
    CONDITIONAL_PASS = "CONDITIONAL_PASS"
    FAILED_CRITICAL = "FAILED_CRITICAL"
    REQUIRES_REINSPECTION = "REQUIRES_REINSPECTION"


class MaintenanceCategory(StrEnum):
    """Classification of maintenance tickets."""
    PLUMBING = "PLUMBING"
    ELECTRICAL = "ELECTRICAL"
    CARPENTRY = "CARPENTRY"
    HVAC_AC = "HVAC_AC"
    APPLIANCE = "APPLIANCE"
    STRUCTURAL = "STRUCTURAL"
    PEST_CONTROL = "PEST_CONTROL"
    SECURITY_LOCKS = "SECURITY_LOCKS"
    OTHER = "OTHER"


class MaintenancePriority(StrEnum):
    """Urgency level of maintenance issue."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    EMERGENCY_CRITICAL = "EMERGENCY_CRITICAL"


class MaintenanceStatus(StrEnum):
    """Lifecycle of housing maintenance ticket."""
    REPORTED = "REPORTED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING_PARTS = "WAITING_PARTS"
    COMPLETED = "COMPLETED"
    VERIFIED_BY_TENANT = "VERIFIED_BY_TENANT"
    CANCELLED = "CANCELLED"


# =============================================================================
# 1. ACCOMMODATION PROVIDERS & LANDLORD DIRECTORY
# =============================================================================

class AccommodationProvider(TenantScopedModel):
    """Approved external landlord, housing trust, or student living partner."""

    __tablename__ = "housing_providers"
    __table_args__ = (
        UniqueConstraint("tenant_id", "slug", name="uq_housing_provider_slug"),
        Index("idx_housing_provider_tenant_status", "tenant_id", "verification_status"),
    )

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), nullable=False)
    provider_type: Mapped[str] = mapped_column(
        String(32), default=ProviderType.PRIVATE_LANDLORD.value, nullable=False
    )
    registration_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    contact_name: Mapped[str] = mapped_column(String(128), nullable=False)
    contact_email: Mapped[str] = mapped_column(String(128), nullable=False)
    contact_phone: Mapped[str] = mapped_column(String(32), nullable=False)
    emergency_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    tax_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(64), default="Chennai", nullable=False)
    state: Mapped[str] = mapped_column(String(64), default="Tamil Nadu", nullable=False)
    verification_status: Mapped[str] = mapped_column(
        String(32), default=ProviderVerificationStatus.VERIFIED.value, nullable=False
    )
    verification_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )
    mou_reference: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mou_valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    mou_valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    rating: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("4.50"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    total_properties_managed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_beds_provided: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    properties: Mapped[list["AccommodationProperty"]] = relationship(
        "AccommodationProperty", back_populates="provider", cascade="all, delete-orphan"
    )


# =============================================================================
# 2. ACCOMMODATION PROPERTIES
# =============================================================================

class AccommodationProperty(TenantScopedModel):
    """Residential property (Campus Hostel, Private Hostel, Apartment, Homestay)."""

    __tablename__ = "housing_properties"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_housing_property_code"),
        Index("idx_housing_property_tenant_status", "tenant_id", "lifecycle_status"),
        Index("idx_housing_property_provider", "tenant_id", "provider_id"),
        Index("idx_housing_property_campus", "tenant_id", "campus_id"),
    )

    provider_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("housing_providers.id", ondelete="SET NULL"), nullable=True
    )
    hostel_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("infrastructure_hostels.id", ondelete="SET NULL"), nullable=True
    )
    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_campuses.id", ondelete="RESTRICT"), nullable=True
    )

    code: Mapped[str] = mapped_column(String(32), nullable=False)  # e.g. "PROP-OFF-001"
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), nullable=False)
    property_type: Mapped[str] = mapped_column(
        String(32), default=PropertyType.OFF_CAMPUS_HOSTEL.value, nullable=False
    )
    lifecycle_status: Mapped[str] = mapped_column(
        String(32), default=PropertyLifecycleStatus.APPROVED.value, nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(64), default="Chennai", nullable=False)
    state: Mapped[str] = mapped_column(String(64), default="Tamil Nadu", nullable=False)
    postal_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    distance_to_campus_km: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("1.50"), nullable=False)

    total_rooms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_bed_capacity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    occupied_beds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    available_beds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    monthly_rent_min: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("6000.00"), nullable=False)
    monthly_rent_max: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("12000.00"), nullable=False)
    security_deposit_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("15000.00"), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="INR", nullable=False)

    amenities: Mapped[list[str]] = mapped_column(JSONType, default=list, nullable=False)
    utilities_included: Mapped[list[str]] = mapped_column(JSONType, default=list, nullable=False)
    accessibility_features: Mapped[list[str]] = mapped_column(JSONType, default=list, nullable=False)
    safety_features: Mapped[list[str]] = mapped_column(JSONType, default=list, nullable=False)
    house_rules: Mapped[str | None] = mapped_column(Text, nullable=True)

    approval_valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    approved_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    manager_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    manager_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    manager_email: Mapped[str | None] = mapped_column(String(128), nullable=True)

    provider: Mapped["AccommodationProvider | None"] = relationship("AccommodationProvider", back_populates="properties")
    units: Mapped[list["AccommodationUnit"]] = relationship("AccommodationUnit", back_populates="property", cascade="all, delete-orphan")
    inspections: Mapped[list["HousingPropertyInspection"]] = relationship("HousingPropertyInspection", back_populates="property", cascade="all, delete-orphan")
    maintenance_requests: Mapped[list["HousingMaintenanceRequest"]] = relationship("HousingMaintenanceRequest", back_populates="property", cascade="all, delete-orphan")


# =============================================================================
# 3. ACCOMMODATION UNITS & BEDS
# =============================================================================

class AccommodationUnit(TenantScopedModel):
    """Individual room or apartment unit inside a property."""

    __tablename__ = "housing_units"
    __table_args__ = (
        UniqueConstraint("property_id", "unit_number", name="uq_unit_property_number"),
        Index("idx_housing_unit_tenant_property", "tenant_id", "property_id"),
        Index("idx_housing_unit_status", "tenant_id", "status"),
    )

    property_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("housing_properties.id", ondelete="CASCADE"), nullable=False
    )
    hostel_room_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("infrastructure_hostel_rooms.id", ondelete="SET NULL"), nullable=True
    )

    unit_number: Mapped[str] = mapped_column(String(32), nullable=False)  # e.g. "101", "204"
    unit_type: Mapped[str] = mapped_column(
        String(32), default=UnitType.DOUBLE_OCCUPANCY.value, nullable=False
    )
    floor_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    bed_capacity: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    occupied_beds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    rent_per_bed: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("8000.00"), nullable=False)
    security_deposit_per_bed: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("15000.00"), nullable=False)

    is_furnished: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    has_attached_bath: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_accessible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=UnitStatus.AVAILABLE.value, nullable=False)
    maintenance_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    closed_until: Mapped[date | None] = mapped_column(Date, nullable=True)

    property: Mapped["AccommodationProperty"] = relationship("AccommodationProperty", back_populates="units")
    beds: Mapped[list["AccommodationBed"]] = relationship("AccommodationBed", back_populates="unit", cascade="all, delete-orphan")


class AccommodationBed(TenantScopedModel):
    """Specific addressable bed in a unit."""

    __tablename__ = "housing_beds"
    __table_args__ = (
        UniqueConstraint("unit_id", "bed_code", name="uq_unit_bed_code"),
        Index("idx_housing_bed_tenant_unit", "tenant_id", "unit_id"),
        Index("idx_housing_bed_status", "tenant_id", "status"),
    )

    unit_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("housing_units.id", ondelete="CASCADE"), nullable=False
    )
    hostel_bed_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("infrastructure_hostel_beds.id", ondelete="SET NULL"), nullable=True
    )

    bed_code: Mapped[str] = mapped_column(String(32), nullable=False)  # e.g. "101-A", "204-B"
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="AVAILABLE", nullable=False)
    blocked_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    blocked_until: Mapped[date | None] = mapped_column(Date, nullable=True)

    unit: Mapped["AccommodationUnit"] = relationship("AccommodationUnit", back_populates="beds")


# =============================================================================
# 4. STUDENT HOUSING REQUESTS & OFFERS
# =============================================================================

class StudentHousingRequest(TenantScopedModel):
    """Student request for campus or approved off-campus accommodation."""

    __tablename__ = "housing_requests"
    __table_args__ = (
        UniqueConstraint("tenant_id", "request_number", name="uq_housing_request_number"),
        Index("idx_housing_request_student", "tenant_id", "student_id"),
        Index("idx_housing_request_status", "tenant_id", "status"),
        Index("idx_housing_request_waitlist", "tenant_id", "waitlist_position"),
    )

    request_number: Mapped[str] = mapped_column(String(32), nullable=False)  # e.g. "REQ-HOU-2026-0001"
    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_students.id", ondelete="RESTRICT"), nullable=False
    )
    preferred_property_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("housing_properties.id", ondelete="SET NULL"), nullable=True
    )
    preferred_unit_type: Mapped[str] = mapped_column(
        String(32), default=UnitType.DOUBLE_OCCUPANCY.value, nullable=False
    )
    academic_year_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_academic_years.id", ondelete="RESTRICT"), nullable=True
    )
    academic_term: Mapped[str] = mapped_column(String(32), default="Academic Year 2026-27", nullable=False)

    requested_move_in_date: Mapped[date] = mapped_column(Date, nullable=False)
    requested_move_out_date: Mapped[date] = mapped_column(Date, nullable=False)
    budget_min: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    budget_max: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    accessibility_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    disability_accommodation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    dietary_preference: Mapped[str | None] = mapped_column(String(64), nullable=True)
    lifestyle_preferences: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    special_requests: Mapped[str | None] = mapped_column(Text, nullable=True)
    supporting_document_ids: Mapped[list[str]] = mapped_column(JSONType, default=list, nullable=False)

    status: Mapped[str] = mapped_column(
        String(32), default=HousingRequestStatus.SUBMITTED.value, nullable=False
    )
    waitlist_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    priority_score: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal("0.00"), nullable=False)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    preferred_property: Mapped["AccommodationProperty | None"] = relationship("AccommodationProperty")
    offers: Mapped[list["HousingOffer"]] = relationship("HousingOffer", back_populates="request", cascade="all, delete-orphan")


class HousingOffer(TenantScopedModel):
    """Specific room/bed offer made to a student."""

    __tablename__ = "housing_offers"
    __table_args__ = (
        Index("idx_housing_offer_tenant_req", "tenant_id", "request_id"),
        Index("idx_housing_offer_tenant_student", "tenant_id", "student_id"),
        Index("idx_housing_offer_status", "tenant_id", "status"),
    )

    request_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("housing_requests.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_students.id", ondelete="RESTRICT"), nullable=False
    )
    property_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("housing_properties.id", ondelete="RESTRICT"), nullable=False
    )
    unit_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("housing_units.id", ondelete="RESTRICT"), nullable=False
    )
    bed_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("housing_beds.id", ondelete="RESTRICT"), nullable=False
    )

    offered_rent_monthly: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    offered_deposit: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    occupancy_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    occupancy_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    offer_valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    status: Mapped[str] = mapped_column(
        String(32), default=HousingOfferStatus.OFFERED.value, nullable=False
    )
    decline_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    response_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    request: Mapped["StudentHousingRequest"] = relationship("StudentHousingRequest", back_populates="offers")
    property: Mapped["AccommodationProperty"] = relationship("AccommodationProperty")
    unit: Mapped["AccommodationUnit"] = relationship("AccommodationUnit")
    bed: Mapped["AccommodationBed"] = relationship("AccommodationBed")


# =============================================================================
# 5. ASSIGNMENTS, AGREEMENTS & OCCUPANCY
# =============================================================================

class HousingAssignment(TenantScopedModel):
    """Confirmed housing placement for a student."""

    __tablename__ = "housing_assignments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "assignment_number", name="uq_housing_assignment_num"),
        Index("idx_housing_asgn_student", "tenant_id", "student_id"),
        Index("idx_housing_asgn_bed", "tenant_id", "bed_id"),
        Index("idx_housing_asgn_status", "tenant_id", "status"),
    )

    assignment_number: Mapped[str] = mapped_column(String(32), nullable=False)  # e.g. "ASGN-HOU-2026-0001"
    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_students.id", ondelete="RESTRICT"), nullable=False
    )
    property_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("housing_properties.id", ondelete="RESTRICT"), nullable=False
    )
    unit_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("housing_units.id", ondelete="RESTRICT"), nullable=False
    )
    bed_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("housing_beds.id", ondelete="RESTRICT"), nullable=False
    )
    request_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("housing_requests.id", ondelete="SET NULL"), nullable=True
    )
    offer_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("housing_offers.id", ondelete="SET NULL"), nullable=True
    )
    hostel_allocation_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("infrastructure_hostel_allocations.id", ondelete="SET NULL"), nullable=True
    )

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    monthly_rent: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    security_deposit: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=HousingAssignmentStatus.ASSIGNED.value, nullable=False
    )

    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    transfer_to_unit_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("housing_units.id", ondelete="SET NULL"), nullable=True
    )
    transfer_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    property: Mapped["AccommodationProperty"] = relationship("AccommodationProperty")
    unit: Mapped["AccommodationUnit"] = relationship("AccommodationUnit", foreign_keys=[unit_id])
    bed: Mapped["AccommodationBed"] = relationship("AccommodationBed")
    agreement: Mapped["HousingAgreementReference | None"] = relationship("HousingAgreementReference", back_populates="assignment", uselist=False)
    check_records: Mapped[list["HousingCheckInOutRecord"]] = relationship("HousingCheckInOutRecord", back_populates="assignment", cascade="all, delete-orphan")


class HousingAgreementReference(TenantScopedModel):
    """Lease or accommodation contract tying into CampusOS finance & document registry."""

    __tablename__ = "housing_agreements"
    __table_args__ = (
        UniqueConstraint("assignment_id", name="uq_housing_agmt_asgn"),
        Index("idx_housing_agmt_tenant_student", "tenant_id", "student_id"),
        Index("idx_housing_agmt_status", "tenant_id", "status"),
    )

    assignment_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("housing_assignments.id", ondelete="CASCADE"), nullable=False
    )
    property_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("housing_properties.id", ondelete="RESTRICT"), nullable=False
    )
    provider_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("housing_providers.id", ondelete="SET NULL"), nullable=True
    )
    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_students.id", ondelete="RESTRICT"), nullable=False
    )

    agreement_number: Mapped[str] = mapped_column(String(32), nullable=False)  # e.g. "AGR-HOU-2026-0042"
    agreement_title: Mapped[str] = mapped_column(String(128), nullable=False)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date] = mapped_column(Date, nullable=False)
    rent_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    deposit_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    payment_frequency: Mapped[str] = mapped_column(String(32), default="MONTHLY", nullable=False)

    finance_invoice_reference: Mapped[str | None] = mapped_column(String(64), nullable=True)
    deposit_invoice_reference: Mapped[str | None] = mapped_column(String(64), nullable=True)
    deposit_refund_status: Mapped[str] = mapped_column(String(32), default="HELD", nullable=False)

    terms_and_conditions_acknowledged: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    student_signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    provider_signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    institutional_witness_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )

    status: Mapped[str] = mapped_column(String(32), default=AgreementStatus.PENDING_SIGNATURE.value, nullable=False)
    document_file_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    assignment: Mapped["HousingAssignment"] = relationship("HousingAssignment", back_populates="agreement")


class HousingCheckInOutRecord(TenantScopedModel):
    """Check-in and check-out condition record with damage assessments."""

    __tablename__ = "housing_checkin_checkout"
    __table_args__ = (
        Index("idx_housing_check_assignment", "tenant_id", "assignment_id"),
        Index("idx_housing_check_student", "tenant_id", "student_id"),
        Index("idx_housing_check_type", "tenant_id", "record_type"),
    )

    assignment_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("housing_assignments.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_students.id", ondelete="RESTRICT"), nullable=False
    )

    record_type: Mapped[str] = mapped_column(String(16), nullable=False)  # "CHECK_IN" or "CHECK_OUT"
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)
    actual_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    inspector_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )

    key_card_issued_or_returned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    key_identifier: Mapped[str | None] = mapped_column(String(64), nullable=True)
    room_condition_rating: Mapped[str] = mapped_column(String(32), default="GOOD", nullable=False)
    checklist_items: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)

    damage_assessed_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    damage_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    damage_billed_invoice_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("finance_invoices.id", ondelete="SET NULL"), nullable=True
    )
    photos_evidence_ids: Mapped[list[str]] = mapped_column(JSONType, default=list, nullable=False)
    student_signature_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="SCHEDULED", nullable=False)

    assignment: Mapped["HousingAssignment"] = relationship("HousingAssignment", back_populates="check_records")


# =============================================================================
# 6. PROPERTY INSPECTIONS & RESIDENTIAL SAFETY
# =============================================================================

class HousingPropertyInspection(TenantScopedModel):
    """Safety, fire, hygiene, and structural compliance inspection."""

    __tablename__ = "housing_inspections"
    __table_args__ = (
        Index("idx_housing_insp_tenant_property", "tenant_id", "property_id"),
        Index("idx_housing_insp_outcome", "tenant_id", "overall_outcome"),
    )

    property_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("housing_properties.id", ondelete="CASCADE"), nullable=False
    )
    inspection_code: Mapped[str] = mapped_column(String(32), nullable=False)  # e.g. "INSP-HOU-2026-001"
    inspector_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False
    )
    inspection_date: Mapped[date] = mapped_column(Date, nullable=False)
    inspection_type: Mapped[str] = mapped_column(
        String(32), default=InspectionType.SAFETY_FIRE.value, nullable=False
    )
    overall_outcome: Mapped[str] = mapped_column(
        String(32), default=InspectionOutcome.PASSED.value, nullable=False
    )
    safety_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("100.00"), nullable=False)
    checklist_results: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)

    critical_issues_found: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    availability_suspended: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    corrective_actions_required: Mapped[str | None] = mapped_column(Text, nullable=True)
    corrective_action_deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    reinspection_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    compliance_status: Mapped[str] = mapped_column(String(32), default="COMPLIANT", nullable=False)
    report_document_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    property: Mapped["AccommodationProperty"] = relationship("AccommodationProperty", back_populates="inspections")


# =============================================================================
# 7. MAINTENANCE & SERVICE REQUESTS
# =============================================================================

class HousingMaintenanceRequest(TenantScopedModel):
    """Resident, coordinator, or landlord service ticket."""

    __tablename__ = "housing_maintenance_requests"
    __table_args__ = (
        Index("idx_housing_maint_tenant_property", "tenant_id", "property_id"),
        Index("idx_housing_maint_status", "tenant_id", "status"),
        Index("idx_housing_maint_priority", "tenant_id", "priority"),
    )

    property_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("housing_properties.id", ondelete="CASCADE"), nullable=False
    )
    unit_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("housing_units.id", ondelete="SET NULL"), nullable=True
    )
    reported_by_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False
    )
    reported_by_student_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_students.id", ondelete="SET NULL"), nullable=True
    )

    category: Mapped[str] = mapped_column(
        String(32), default=MaintenanceCategory.PLUMBING.value, nullable=False
    )
    priority: Mapped[str] = mapped_column(
        String(32), default=MaintenancePriority.MEDIUM.value, nullable=False
    )
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    photo_urls: Mapped[list[str]] = mapped_column(JSONType, default=list, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=MaintenanceStatus.REPORTED.value, nullable=False
    )

    assigned_technician_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    assigned_vendor_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    linked_work_order_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("asset_maintenance_work_orders.id", ondelete="SET NULL"), nullable=True
    )

    scheduled_visit_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completion_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    tenant_satisfaction_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tenant_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    cost_charged_to: Mapped[str] = mapped_column(String(32), default="LANDLORD", nullable=False)

    property: Mapped["AccommodationProperty"] = relationship("AccommodationProperty", back_populates="maintenance_requests")
    unit: Mapped["AccommodationUnit | None"] = relationship("AccommodationUnit")
