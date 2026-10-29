"""CampusOS Enterprise Transport, Fleet, Routes & Student Mobility Models (Step 55).

CampusOS Tagline: "One Campus. One System. One Source of Truth."

Enterprise Data Models Governing:
1. Transport Administration & Multi-Campus Service Areas
2. Authoritative Institutional Vehicle Fleet Registry & Asset Module Integration
3. Driver & Transport Personnel Management with Workforce & License Compliance
4. Configurable Routes, Ordered Transit Stops & Boarding Allocations
5. Student Transport Applications, Review & Subscriptions
6. Concurrency-Safe Passenger Seat Allocation & Waitlist Priority Engine
7. Trip Operations, Manifests & Operational Dispatch Engine
8. Passenger Boarding, Barcode/QR Verification & Student Safety
9. Privacy-Conscious Telematics, GPS Tracking & Freshness Verification
10. Transport Fee Schedules & Authoritative Finance Invoicing Integration
11. Fleet Maintenance, Pre-Trip Checklist Defect Reporting & Asset Work Orders
12. Fuel Consumption, Mileage Progression & Operating Cost Analytics
13. Transport Safety Incidents, Breakdowns & Emergency Dispatch Escalation
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


class VehicleCategory(StrEnum):
    """Institutional transport vehicle classification."""

    BUS = "BUS"
    MINI_BUS = "MINI_BUS"
    VAN = "VAN"
    SHUTTLE = "SHUTTLE"
    SUV = "SUV"
    CAR = "CAR"
    AMBULANCE = "AMBULANCE"
    OTHER = "OTHER"


class VehicleStatus(StrEnum):
    """Authoritative vehicle operational status."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"
    DECOMMISSIONED = "DECOMMISSIONED"


class FuelType(StrEnum):
    """Vehicle propulsion fuel type."""

    DIESEL = "DIESEL"
    PETROL = "PETROL"
    CNG = "CNG"
    ELECTRIC = "ELECTRIC"
    HYBRID = "HYBRID"


class DriverStatus(StrEnum):
    """Operational status of driver profile."""

    ACTIVE = "ACTIVE"
    ON_LEAVE = "ON_LEAVE"
    SUSPENDED = "SUSPENDED"
    INACTIVE = "INACTIVE"
    TERMINATED = "TERMINATED"


class VerificationStatus(StrEnum):
    """Background and credential verification status."""

    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    EXEMPT = "EXEMPT"


class RouteStatus(StrEnum):
    """Lifecycle status of transit route."""

    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    REVISED = "REVISED"
    RETIRED = "RETIRED"


class RouteDirection(StrEnum):
    """Directionality of transport route."""

    ROUND_TRIP = "ROUND_TRIP"
    ONE_WAY_INBOUND = "ONE_WAY_INBOUND"
    ONE_WAY_OUTBOUND = "ONE_WAY_OUTBOUND"


class TransportServiceType(StrEnum):
    """Student subscription subscription service scope."""

    ROUND_TRIP = "ROUND_TRIP"
    ONE_WAY_PICKUP = "ONE_WAY_PICKUP"
    ONE_WAY_DROP = "ONE_WAY_DROP"


class ServiceWindow(StrEnum):
    """Operational trip dispatch window."""

    MORNING_PICKUP = "MORNING_PICKUP"
    EVENING_DROP = "EVENING_DROP"
    AFTERNOON_RETURN = "AFTERNOON_RETURN"
    SPECIAL_TRIP = "SPECIAL_TRIP"
    SHUTTLE = "SHUTTLE"


class TransportApplicationStatus(StrEnum):
    """Student transport application workflow state machine."""

    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    WAITLISTED = "WAITLISTED"
    CANCELLED = "CANCELLED"


class TransportAllocationStatus(StrEnum):
    """Passenger seat allocation lifecycle state."""

    RESERVED = "RESERVED"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class WaitlistStatus(StrEnum):
    """Waitlist queue state."""

    WAITING = "WAITING"
    OFFERED = "OFFERED"
    EXPIRED = "EXPIRED"
    ALLOCATED = "ALLOCATED"
    CANCELLED = "CANCELLED"


class TripStatus(StrEnum):
    """Authoritative trip dispatch state machine."""

    SCHEDULED = "SCHEDULED"
    READY = "READY"
    DEPARTED = "DEPARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    DISRUPTED = "DISRUPTED"


class BoardingStatus(StrEnum):
    """Passenger trip attendance state."""

    EXPECTED = "EXPECTED"
    BOARDED = "BOARDED"
    DROPPED_OFF = "DROPPED_OFF"
    ABSENT = "ABSENT"
    MISSED = "MISSED"


class VerificationMethod(StrEnum):
    """Boarding authentication method."""

    QR_CODE = "QR_CODE"
    RFID_BARCODE = "RFID_BARCODE"
    MANUAL = "MANUAL"


class TrackingProviderStatus(StrEnum):
    """Telematics integration status."""

    ACTIVE = "ACTIVE"
    OFFLINE = "OFFLINE"
    ERROR = "ERROR"
    NOT_CONFIGURED = "NOT_CONFIGURED"


class TransportIncidentType(StrEnum):
    """Classification of transit incidents."""

    ACCIDENT = "ACCIDENT"
    BREAKDOWN = "BREAKDOWN"
    DELAY = "DELAY"
    PASSENGER_BEHAVIOR = "PASSENGER_BEHAVIOR"
    MEDICAL = "MEDICAL"
    ROUTE_OBSTRUCTION = "ROUTE_OBSTRUCTION"
    WEATHER = "WEATHER"
    OTHER = "OTHER"


class TransportIncidentSeverity(StrEnum):
    """Severity classification of transport incident."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentStatus(StrEnum):
    """Incident handling lifecycle."""

    REPORTED = "REPORTED"
    UNDER_INVESTIGATION = "UNDER_INVESTIGATION"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class FeePlanBillingCycle(StrEnum):
    """Transport fee billing periodicity."""

    ANNUAL = "ANNUAL"
    SEMESTER = "SEMESTER"
    TERM = "TERM"
    MONTHLY = "MONTHLY"


class TransportFeeStatus(StrEnum):
    """Passenger transport fee status."""

    PENDING = "PENDING"
    INVOICED = "INVOICED"
    PAID = "PAID"
    WAIVED = "WAIVED"
    REFUNDED = "REFUNDED"
    PARTIAL = "PARTIAL"


# =============================================================================
# 1. TRANSPORT ADMINISTRATION & CONFIGURATION
# =============================================================================


class TransportServiceConfig(TenantScopedModel):
    """Campus transport service administration policy and operating zones."""

    __tablename__ = "transport_service_configs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "service_code", name="uq_tr_config_tenant_code"),
    )

    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="SET NULL"),
        nullable=True,
    )
    service_code: Mapped[str] = mapped_column(String(32), nullable=False)
    service_name: Mapped[str] = mapped_column(String(128), nullable=False)
    academic_year_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_academic_years.id", ondelete="SET NULL"),
        nullable=True,
    )
    zone_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    operating_period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    operating_period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    eligibility_criteria: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    capacity_policy: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


# =============================================================================
# 2. VEHICLE & FLEET REGISTRY
# =============================================================================


class TransportVehicle(TenantScopedModel):
    """Authoritative institutional transport vehicle, integrated with Asset Management."""

    __tablename__ = "infrastructure_vehicles"
    __table_args__ = (
        UniqueConstraint("tenant_id", "registration_number", name="uq_vehicles_reg_number"),
        Index("idx_tr_vehicles_tenant_status", "tenant_id", "status"),
    )

    asset_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("asset_registry.id", ondelete="SET NULL"),
        nullable=True,
    )
    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="SET NULL"),
        nullable=True,
    )
    registration_number: Mapped[str] = mapped_column(String(32), nullable=False)
    fleet_identifier: Mapped[str | None] = mapped_column(String(64), nullable=True)
    vehicle_category: Mapped[str] = mapped_column(
        String(32), default=VehicleCategory.BUS.value, nullable=False
    )
    make: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model: Mapped[str | None] = mapped_column(String(64), nullable=True)
    manufacturing_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)  # Total seating capacity
    accessible_seating_capacity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    permitted_passenger_capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    insurance_policy_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    insurance_expiry: Mapped[date] = mapped_column(Date, nullable=False)
    fitness_certificate_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    fitness_certificate_expiry: Mapped[date] = mapped_column(Date, nullable=False)
    permit_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    permit_expiry: Mapped[date | None] = mapped_column(Date, nullable=True)
    pollution_certificate_expiry: Mapped[date | None] = mapped_column(Date, nullable=True)
    fuel_type: Mapped[str] = mapped_column(
        String(32), default=FuelType.DIESEL.value, nullable=False
    )
    operational_depot: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default=VehicleStatus.ACTIVE.value, nullable=False
    )
    current_odometer_km: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    safety_equipment_details: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    routes: Mapped[list["TransportRoute"]] = relationship(
        "TransportRoute", back_populates="vehicle"
    )
    trips: Mapped[list["TransportTrip"]] = relationship(
        "TransportTrip", back_populates="vehicle"
    )
    fuel_logs: Mapped[list["TransportFuelLog"]] = relationship(
        "TransportFuelLog", back_populates="vehicle"
    )
    incidents: Mapped[list["TransportIncident"]] = relationship(
        "TransportIncident", back_populates="vehicle"
    )


# =============================================================================
# 3. DRIVER & TRANSPORT PERSONNEL REGISTRY
# =============================================================================


class TransportDriver(TenantScopedModel):
    """Institutional vehicle driver profile linked to workforce and licensing."""

    __tablename__ = "infrastructure_drivers"
    __table_args__ = (
        UniqueConstraint("tenant_id", "license_number", name="uq_drivers_license"),
        Index("idx_tr_drivers_tenant_status", "tenant_id", "status"),
    )

    user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    employee_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workforce_employees.id", ondelete="SET NULL"),
        nullable=True,
    )
    full_name: Mapped[str] = mapped_column(String(128), default="Driver", nullable=False)
    license_number: Mapped[str] = mapped_column(String(64), nullable=False)
    license_categories: Mapped[list[str] | None] = mapped_column(JSONType, nullable=True)
    license_expiry: Mapped[date] = mapped_column(Date, nullable=False)
    phone_number: Mapped[str] = mapped_column(String(32), nullable=False)
    email: Mapped[str | None] = mapped_column(String(128), nullable=True)
    badge_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    badge_expiry: Mapped[date | None] = mapped_column(Date, nullable=True)
    certifications: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    background_verification_status: Mapped[str] = mapped_column(
        String(32), default=VerificationStatus.VERIFIED.value, nullable=False
    )
    shift_preference: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default=DriverStatus.ACTIVE.value, nullable=False
    )
    emergency_contact_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    routes: Mapped[list["TransportRoute"]] = relationship(
        "TransportRoute", back_populates="driver"
    )
    trips: Mapped[list["TransportTrip"]] = relationship(
        "TransportTrip", back_populates="driver"
    )
    fuel_logs: Mapped[list["TransportFuelLog"]] = relationship(
        "TransportFuelLog", back_populates="driver"
    )
    incidents: Mapped[list["TransportIncident"]] = relationship(
        "TransportIncident", back_populates="driver"
    )


# =============================================================================
# 4. ROUTE & STOP MANAGEMENT
# =============================================================================


class TransportRoute(TenantScopedModel):
    """Transit corridor connecting municipal passenger stops to campus depots."""

    __tablename__ = "infrastructure_routes"
    __table_args__ = (
        UniqueConstraint("tenant_id", "route_code", name="uq_routes_tenant_code"),
        Index("idx_tr_routes_tenant_status", "tenant_id", "status"),
    )

    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="SET NULL"),
        nullable=True,
    )
    route_code: Mapped[str] = mapped_column(String(32), nullable=False)
    route_name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_point: Mapped[str] = mapped_column(String(128), default="Campus Depot", nullable=False)
    end_point: Mapped[str] = mapped_column(String(128), default="Terminal", nullable=False)
    distance_km: Mapped[Decimal] = mapped_column(
        Numeric(8, 2), default=Decimal("0.00"), nullable=False
    )
    estimated_duration_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    morning_departure_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    evening_return_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    vehicle_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_vehicles.id", ondelete="SET NULL"),
        nullable=True,
    )
    driver_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_drivers.id", ondelete="SET NULL"),
        nullable=True,
    )
    capacity: Mapped[int] = mapped_column(Integer, default=52, nullable=False)
    allocated_students: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    direction: Mapped[str] = mapped_column(
        String(32), default=RouteDirection.ROUND_TRIP.value, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), default=RouteStatus.ACTIVE.value, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    vehicle: Mapped["TransportVehicle | None"] = relationship(
        "TransportVehicle", back_populates="routes"
    )
    driver: Mapped["TransportDriver | None"] = relationship(
        "TransportDriver", back_populates="routes"
    )
    stops: Mapped[list["TransportStop"]] = relationship(
        "TransportStop",
        back_populates="route",
        order_by="TransportStop.stop_sequence",
        cascade="all, delete-orphan",
    )
    allocations: Mapped[list["TransportAllocation"]] = relationship(
        "TransportAllocation", back_populates="route"
    )
    trips: Mapped[list["TransportTrip"]] = relationship(
        "TransportTrip", back_populates="route"
    )


class TransportStop(Base):
    """Designated passenger pickup and drop-off point along a transit route."""

    __tablename__ = "infrastructure_stops"
    __table_args__ = (
        Index("idx_tr_stops_route_seq", "route_id", "stop_sequence"),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=True,
    )
    route_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_routes.id", ondelete="CASCADE"),
        nullable=False,
    )
    stop_name: Mapped[str] = mapped_column(String(128), nullable=False)
    stop_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    stop_sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    landmark: Mapped[str | None] = mapped_column(String(128), nullable=True)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    pickup_time: Mapped[time] = mapped_column(Time, nullable=False)
    drop_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    fare_annual: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    fare_term: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    fare_monthly: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    max_boarding_capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    route: Mapped["TransportRoute"] = relationship("TransportRoute", back_populates="stops")
    allocations: Mapped[list["TransportAllocation"]] = relationship(
        "TransportAllocation", back_populates="stop"
    )


# =============================================================================
# 5. STUDENT TRANSPORT APPLICATIONS & WAITLIST
# =============================================================================


class TransportApplication(TenantScopedModel):
    """Student transport self-service registration and route application."""

    __tablename__ = "transport_applications"
    __table_args__ = (
        UniqueConstraint("tenant_id", "application_number", name="uq_tr_appl_tenant_num"),
        Index("idx_tr_appl_tenant_student", "tenant_id", "student_id"),
        Index("idx_tr_appl_tenant_status", "tenant_id", "status"),
    )

    application_number: Mapped[str] = mapped_column(String(32), nullable=False)
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
    preferred_route_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_routes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    preferred_stop_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_stops.id", ondelete="RESTRICT"),
        nullable=False,
    )
    service_type: Mapped[str] = mapped_column(
        String(32), default=TransportServiceType.ROUND_TRIP.value, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), default=TransportApplicationStatus.SUBMITTED.value, nullable=False
    )
    priority_score: Mapped[Decimal] = mapped_column(
        Numeric(8, 2), default=Decimal("0.00"), nullable=False
    )
    accessibility_needed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    special_requests: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewer_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class TransportWaitlist(TenantScopedModel):
    """Queue of unallocated students awaiting route/stop capacity availability."""

    __tablename__ = "transport_waitlists"
    __table_args__ = (
        Index("idx_tr_waitlist_route_status", "tenant_id", "route_id", "status"),
    )

    route_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_routes.id", ondelete="CASCADE"),
        nullable=False,
    )
    stop_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_stops.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="CASCADE"),
        nullable=False,
    )
    application_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("transport_applications.id", ondelete="SET NULL"),
        nullable=True,
    )
    priority_score: Mapped[Decimal] = mapped_column(
        Numeric(8, 2), default=Decimal("0.00"), nullable=False
    )
    queue_position: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=WaitlistStatus.WAITING.value, nullable=False
    )
    offered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# =============================================================================
# 6. SEAT ALLOCATION & SUBSCRIPTIONS
# =============================================================================


class TransportAllocation(TenantScopedModel):
    """Authoritative student transport pass and confirmed route seat allocation."""

    __tablename__ = "infrastructure_transport_allocations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "pass_number", name="uq_tr_alloc_pass_num"),
        Index("idx_tr_alloc_tenant_student", "tenant_id", "student_id"),
        Index("idx_tr_alloc_route_status", "tenant_id", "route_id", "status"),
    )

    pass_number: Mapped[str] = mapped_column(String(64), nullable=False)
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
    route_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_routes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    stop_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_stops.id", ondelete="RESTRICT"),
        nullable=False,
    )
    vehicle_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_vehicles.id", ondelete="SET NULL"),
        nullable=True,
    )
    service_type: Mapped[str] = mapped_column(
        String(32), default=TransportServiceType.ROUND_TRIP.value, nullable=False
    )
    seat_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default=TransportAllocationStatus.ACTIVE.value, nullable=False
    )
    valid_from: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    finance_invoice_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("finance_invoices.id", ondelete="SET NULL"),
        nullable=True,
    )
    fee_status: Mapped[str] = mapped_column(
        String(32), default=TransportFeeStatus.PENDING.value, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    route: Mapped["TransportRoute"] = relationship("TransportRoute", back_populates="allocations")
    stop: Mapped["TransportStop"] = relationship("TransportStop", back_populates="allocations")


# =============================================================================
# 7. TRIP SCHEDULING, DISPATCH & MANIFESTS
# =============================================================================


class TransportTrip(TenantScopedModel):
    """Operational transit service run scheduled for a specific date and route."""

    __tablename__ = "transport_trips"
    __table_args__ = (
        UniqueConstraint("tenant_id", "trip_number", name="uq_tr_trips_tenant_num"),
        Index("idx_tr_trips_date_route", "tenant_id", "trip_date", "route_id"),
        Index("idx_tr_trips_vehicle_date", "tenant_id", "vehicle_id", "trip_date"),
        Index("idx_tr_trips_driver_date", "tenant_id", "driver_id", "trip_date"),
    )

    trip_number: Mapped[str] = mapped_column(String(32), nullable=False)
    route_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_routes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    vehicle_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_vehicles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    driver_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_drivers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    trip_date: Mapped[date] = mapped_column(Date, nullable=False)
    service_window: Mapped[str] = mapped_column(
        String(32), default=ServiceWindow.MORNING_PICKUP.value, nullable=False
    )
    scheduled_start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scheduled_end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    start_odometer_km: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    end_odometer_km: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default=TripStatus.SCHEDULED.value, nullable=False
    )
    pre_trip_checklist_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    checklist_notes: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    disruption_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    dispatched_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    route: Mapped["TransportRoute"] = relationship("TransportRoute", back_populates="trips")
    vehicle: Mapped["TransportVehicle"] = relationship("TransportVehicle", back_populates="trips")
    driver: Mapped["TransportDriver"] = relationship("TransportDriver", back_populates="trips")
    boarding_records: Mapped[list["TransportBoardingRecord"]] = relationship(
        "TransportBoardingRecord", back_populates="trip", cascade="all, delete-orphan"
    )
    incidents: Mapped[list["TransportIncident"]] = relationship(
        "TransportIncident", back_populates="trip"
    )


class TransportBoardingRecord(TenantScopedModel):
    """Passenger manifest item and trip boarding/drop-off verification."""

    __tablename__ = "transport_boarding_records"
    __table_args__ = (
        Index("idx_tr_boarding_trip_student", "tenant_id", "trip_id", "student_id"),
    )

    trip_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("transport_trips.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    allocation_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_transport_allocations.id", ondelete="SET NULL"),
        nullable=True,
    )
    stop_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_stops.id", ondelete="RESTRICT"),
        nullable=False,
    )
    boarding_status: Mapped[str] = mapped_column(
        String(32), default=BoardingStatus.EXPECTED.value, nullable=False
    )
    boarding_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    drop_off_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verification_method: Mapped[str] = mapped_column(
        String(32), default=VerificationMethod.MANUAL.value, nullable=False
    )
    verified_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    remarks: Mapped[str | None] = mapped_column(String(255), nullable=True)

    trip: Mapped["TransportTrip"] = relationship("TransportTrip", back_populates="boarding_records")


# =============================================================================
# 8. LIVE TRACKING BOUNDARY & LOCATION SNAPSHOTS
# =============================================================================


class TransportTrackingSource(TenantScopedModel):
    """Telematics hardware/provider configuration boundary for an institutional vehicle."""

    __tablename__ = "transport_tracking_sources"
    __table_args__ = (
        UniqueConstraint("tenant_id", "vehicle_id", name="uq_tr_tracking_vehicle"),
    )

    vehicle_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_vehicles.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider_name: Mapped[str] = mapped_column(String(64), default="DISABLED", nullable=False)
    device_identifier: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default=TrackingProviderStatus.NOT_CONFIGURED.value, nullable=False
    )


class TransportLocationSnapshot(TenantScopedModel):
    """Audited, privacy-conscious geographic snapshot received from verified tracker."""

    __tablename__ = "transport_location_snapshots"
    __table_args__ = (
        Index("idx_tr_loc_snap_vehicle_time", "tenant_id", "vehicle_id", "recorded_at"),
    )

    vehicle_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_vehicles.id", ondelete="CASCADE"),
        nullable=False,
    )
    trip_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("transport_trips.id", ondelete="SET NULL"),
        nullable=True,
    )
    latitude: Mapped[Decimal] = mapped_column(Numeric(10, 7), nullable=False)
    longitude: Mapped[Decimal] = mapped_column(Numeric(10, 7), nullable=False)
    speed_kmh: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal("0.00"), nullable=False)
    heading_degrees: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    odometer_reading: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    data_source: Mapped[str] = mapped_column(String(64), default="TELEMATICS", nullable=False)


# =============================================================================
# 9. TRANSPORT FEES & FINANCE INTEGRATION
# =============================================================================


class TransportFeePlan(TenantScopedModel):
    """Institutional transport fee schedule and pricing matrix."""

    __tablename__ = "transport_fee_plans"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_tr_fee_plan_code"),
    )

    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    academic_year_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_academic_years.id", ondelete="SET NULL"),
        nullable=True,
    )
    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="SET NULL"),
        nullable=True,
    )
    route_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_routes.id", ondelete="SET NULL"),
        nullable=True,
    )
    stop_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_stops.id", ondelete="SET NULL"),
        nullable=True,
    )
    service_type: Mapped[str] = mapped_column(
        String(32), default=TransportServiceType.ROUND_TRIP.value, nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="INR", nullable=False)
    billing_cycle: Mapped[str] = mapped_column(
        String(32), default=FeePlanBillingCycle.ANNUAL.value, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


# =============================================================================
# 10. FUEL, MILEAGE & OPERATING COSTS
# =============================================================================


class TransportFuelLog(TenantScopedModel):
    """Audited vehicle fueling and operating expense entry."""

    __tablename__ = "transport_fuel_logs"
    __table_args__ = (
        Index("idx_tr_fuel_vehicle_date", "tenant_id", "vehicle_id", "fuel_date"),
    )

    vehicle_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_vehicles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    driver_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_drivers.id", ondelete="SET NULL"),
        nullable=True,
    )
    trip_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("transport_trips.id", ondelete="SET NULL"),
        nullable=True,
    )
    fuel_date: Mapped[date] = mapped_column(Date, nullable=False)
    odometer_reading: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    fuel_quantity_liters: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    fuel_cost_total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    fuel_station_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    receipt_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    verified_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    vehicle: Mapped["TransportVehicle"] = relationship("TransportVehicle", back_populates="fuel_logs")
    driver: Mapped["TransportDriver | None"] = relationship("TransportDriver", back_populates="fuel_logs")


# =============================================================================
# 11. TRANSPORT INCIDENTS & SAFETY
# =============================================================================


class TransportIncident(TenantScopedModel):
    """Recorded in-transit breakdown, safety disruption, or emergency event."""

    __tablename__ = "transport_incidents"
    __table_args__ = (
        UniqueConstraint("tenant_id", "incident_number", name="uq_tr_incidents_tenant_num"),
        Index("idx_tr_incidents_tenant_time", "tenant_id", "incident_time"),
    )

    incident_number: Mapped[str] = mapped_column(String(32), nullable=False)
    trip_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("transport_trips.id", ondelete="SET NULL"),
        nullable=True,
    )
    vehicle_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_vehicles.id", ondelete="SET NULL"),
        nullable=True,
    )
    driver_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_drivers.id", ondelete="SET NULL"),
        nullable=True,
    )
    route_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_routes.id", ondelete="SET NULL"),
        nullable=True,
    )
    incident_type: Mapped[str] = mapped_column(
        String(32), default=TransportIncidentType.BREAKDOWN.value, nullable=False
    )
    severity: Mapped[str] = mapped_column(
        String(32), default=TransportIncidentSeverity.MEDIUM.value, nullable=False
    )
    incident_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    location_description: Mapped[str] = mapped_column(String(255), nullable=False)
    reporter_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    action_taken: Mapped[str | None] = mapped_column(Text, nullable=True)
    involved_student_ids: Mapped[list[str] | None] = mapped_column(JSONType, nullable=True)
    emergency_services_contacted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=IncidentStatus.REPORTED.value, nullable=False
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    trip: Mapped["TransportTrip | None"] = relationship("TransportTrip", back_populates="incidents")
    vehicle: Mapped["TransportVehicle | None"] = relationship("TransportVehicle", back_populates="incidents")
    driver: Mapped["TransportDriver | None"] = relationship("TransportDriver", back_populates="incidents")
    route: Mapped["TransportRoute | None"] = relationship("TransportRoute")
