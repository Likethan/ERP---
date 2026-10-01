from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TenantScopedModel


class Hostel(TenantScopedModel):
    """Student residential facility."""

    __tablename__ = "infrastructure_hostels"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_hostels_tenant_code"),)

    campus_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="RESTRICT"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    gender: Mapped[str] = mapped_column(String(16), nullable=False)  # MALE, FEMALE, CO_ED
    warden_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    blocks: Mapped[list["HostelBlock"]] = relationship(back_populates="hostel")


class HostelBlock(Base):
    """Block or wing within a hostel."""

    __tablename__ = "infrastructure_hostel_blocks"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    hostel_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_hostels.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g. "A Block"

    hostel: Mapped["Hostel"] = relationship(back_populates="blocks")
    floors: Mapped[list["HostelFloor"]] = relationship(back_populates="block")


class HostelFloor(Base):
    """Floor level within a hostel block."""

    __tablename__ = "infrastructure_hostel_floors"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    block_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_hostel_blocks.id", ondelete="CASCADE"),
        nullable=False,
    )
    floor_number: Mapped[int] = mapped_column(nullable=False)

    block: Mapped["HostelBlock"] = relationship(back_populates="floors")
    rooms: Mapped[list["HostelRoom"]] = relationship(back_populates="floor")


class HostelRoom(Base):
    """Dormitory room."""

    __tablename__ = "infrastructure_hostel_rooms"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    floor_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_hostel_floors.id", ondelete="CASCADE"),
        nullable=False,
    )
    room_number: Mapped[str] = mapped_column(String(32), nullable=False)
    room_type: Mapped[str] = mapped_column(
        String(32), default="DOUBLE", nullable=False
    )  # SINGLE, DOUBLE, TRIPLE, DORMITORY
    capacity: Mapped[int] = mapped_column(default=2, nullable=False)

    floor: Mapped["HostelFloor"] = relationship(back_populates="rooms")
    beds: Mapped[list["HostelBed"]] = relationship(back_populates="room")


class HostelBed(Base):
    """Individual bed within a hostel room."""

    __tablename__ = "infrastructure_hostel_beds"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    room_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_hostel_rooms.id", ondelete="CASCADE"),
        nullable=False,
    )
    bed_code: Mapped[str] = mapped_column(String(16), nullable=False)  # e.g. "B101-A"
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    room: Mapped["HostelRoom"] = relationship(back_populates="beds")
    allocations: Mapped[list["HostelAllocation"]] = relationship(back_populates="bed")


class HostelAllocation(TenantScopedModel):
    """Historical and active bed reservation ledger."""

    __tablename__ = "infrastructure_hostel_allocations"

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
    check_in_date: Mapped[date] = mapped_column(Date, nullable=False)
    check_out_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default="ALLOCATED", nullable=False
    )  # ALLOCATED, VACATED, CANCELLED

    bed: Mapped["HostelBed"] = relationship(back_populates="allocations")


class HostelLeavePass(TenantScopedModel):
    """Student outing or home leave permission pass."""

    __tablename__ = "infrastructure_hostel_passes"

    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    departure_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expected_return_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_return_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    parent_consent_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="REQUESTED", nullable=False
    )  # REQUESTED, APPROVED, REJECTED, CHECKED_OUT, RETURNED


class HostelComplaint(TenantScopedModel):
    """Hostel maintenance ticket."""

    __tablename__ = "infrastructure_hostel_complaints"

    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    room_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_hostel_rooms.id", ondelete="RESTRICT"),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # ELECTRICAL, PLUMBING, HYGIENE, WIFI
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="OPEN", nullable=False
    )  # OPEN, ASSIGNED, RESOLVED, CLOSED


# Transport Logistics
class TransportVehicle(TenantScopedModel):
    """Institutional bus, van, or shuttle vehicle."""

    __tablename__ = "infrastructure_vehicles"
    __table_args__ = (
        UniqueConstraint("tenant_id", "registration_number", name="uq_vehicles_reg_number"),
    )

    registration_number: Mapped[str] = mapped_column(String(32), nullable=False)
    capacity: Mapped[int] = mapped_column(nullable=False)
    fitness_certificate_expiry: Mapped[date] = mapped_column(Date, nullable=False)
    insurance_expiry: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class TransportDriver(TenantScopedModel):
    """Institutional vehicle driver profile."""

    __tablename__ = "infrastructure_drivers"
    __table_args__ = (UniqueConstraint("tenant_id", "license_number", name="uq_drivers_license"),)

    user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    license_number: Mapped[str] = mapped_column(String(64), nullable=False)
    license_expiry: Mapped[date] = mapped_column(Date, nullable=False)
    phone_number: Mapped[str] = mapped_column(String(32), nullable=False)


class TransportRoute(TenantScopedModel):
    """Scheduled transit route connecting municipal stops to campus."""

    __tablename__ = "infrastructure_routes"
    __table_args__ = (UniqueConstraint("tenant_id", "route_code", name="uq_routes_tenant_code"),)

    route_code: Mapped[str] = mapped_column(String(32), nullable=False)
    route_name: Mapped[str] = mapped_column(String(128), nullable=False)
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
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    stops: Mapped[list["TransportStop"]] = relationship(back_populates="route")


class TransportStop(Base):
    """Designated boarding point along a transit route."""

    __tablename__ = "infrastructure_stops"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    route_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_routes.id", ondelete="CASCADE"),
        nullable=False,
    )
    stop_name: Mapped[str] = mapped_column(String(128), nullable=False)
    stop_sequence: Mapped[int] = mapped_column(nullable=False)
    pickup_time: Mapped[time] = mapped_column(Time, nullable=False)
    fare_annual: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    route: Mapped["TransportRoute"] = relationship(back_populates="stops")
    allocations: Mapped[list["TransportAllocation"]] = relationship(back_populates="stop")


class TransportAllocation(TenantScopedModel):
    """Historical and active bus pass allocation."""

    __tablename__ = "infrastructure_transport_allocations"

    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    stop_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("infrastructure_stops.id", ondelete="RESTRICT"),
        nullable=False,
    )
    academic_year_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_academic_years.id", ondelete="RESTRICT"),
        nullable=False,
    )
    pass_number: Mapped[str] = mapped_column(String(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    stop: Mapped["TransportStop"] = relationship(back_populates="allocations")
