"""CampusOS Enterprise Hostel, Residential Life, Room Allocation & Student Accommodation Service (Step 54).

CampusOS Tagline: "One Campus. One System. One Source of Truth."
"""

import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.events import DomainEventType, event_publisher
from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
from app.models.assets import (
    Asset,
    AssetCategory,
    MaintenanceWorkOrder,
)
from app.models.core import Campus
from app.models.finance import FeeCategory, Invoice, InvoiceLineItem
from app.models.people import StudentProfile as Student
from app.models.people import User
from app.models.residential import (
    AccommodationApplicationStatus,
    AllocationStatus,
    ApplicationCycleStatus,
    BedStatus,
    CheckoutReason,
    GatePassStatus,
    Hostel,
    HostelAllocation,
    HostelApplication,
    HostelApplicationCycle,
    HostelBed,
    HostelBlock,
    HostelComplaint,
    HostelFeePlan,
    HostelFloor,
    HostelGatePass,
    HostelGender,
    HostelIncident,
    HostelLeavePass,
    HostelMealEnrollment,
    HostelMealPlan,
    HostelNightAttendance,
    HostelOperationalStatus,
    HostelResident,
    HostelRoom,
    HostelSafetyInspection,
    HostelType,
    HostelVisitor,
    MealEnrollmentStatus,
    MealType,
    OutingStatus,
    ResidentialIncidentSeverity,
    ResidentialIncidentStatus,
    ResidentialServicePriority,
    ResidentialServiceStatus,
    ResidentLifecycleStatus,
    RoomType,
    VisitorStatus,
)
from app.schemas.residential import (
    AccommodationApplicationCreate,
    AccommodationApplicationReview,
    AllocationCreate,
    AllocationTransferRequest,
    ApplicationCycleCreate,
    BatchAllocationCommitRequest,
    BatchAllocationPreviewItem,
    BatchAllocationPreviewRequest,
    BatchAllocationPreviewResponse,
    GatePassCreateRequest,
    GenerateHostelInvoiceRequest,
    HostelBedBlockRequest,
    HostelBedCreate,
    HostelBedUpdate,
    HostelBlockCreate,
    HostelCheckInRequest,
    HostelCheckOutRequest,
    HostelCreate,
    HostelFeePlanCreate,
    HostelFloorCreate,
    HostelGatePassCreate,
    HostelGatePassVerifyRequest,
    HostelInvoiceResponse,
    HostelOccupancyStat,
    HostelRoomCreate,
    HostelRoomUpdate,
    HostelUpdate,
    IncidentCreate,
    IncidentUpdate,
    MealEnrollmentCreate,
    MealHeadcountResponse,
    MealPlanCreate,
    NightAttendanceBatchRequest,
    OccupancyDashboardResponse,
    OutingApprovalRequest,
    OutingDepartureRequest,
    OutingRequestCreate,
    OutingReturnRequest,
    ResidentCheckInRequest,
    ResidentCheckOutRequest,
    ResidentialDashboardSummaryResponse,
    SafetyInspectionCreate,
    ServiceRequestCreate,
    ServiceRequestFeedback,
    ServiceRequestUpdate,
    VisitorCheckInRequest,
    VisitorCheckOutRequest,
    VisitorRegisterRequest,
)


class ResidentialService:
    """Production service for Hostel, Residential Life, Allocations & Student Accommodation."""

    # =========================================================================
    # 1. HOSTEL & FACILITY REGISTRY
    # =========================================================================

    @staticmethod
    async def create_hostel(
        db: AsyncSession, tenant_id: UUID, payload: HostelCreate
    ) -> Hostel:
        # Validate unique code per tenant
        existing = await db.scalar(
            select(Hostel).where(
                Hostel.tenant_id == tenant_id, Hostel.code == payload.code.upper().strip()
            )
        )
        if existing:
            raise ConflictException(f"Hostel with code '{payload.code}' already exists")

        # Validate campus
        campus = await db.scalar(
            select(Campus).where(Campus.tenant_id == tenant_id, Campus.id == payload.campus_id)
        )
        if not campus:
            raise NotFoundException("Specified campus does not exist")

        hostel = Hostel(
            tenant_id=tenant_id,
            campus_id=payload.campus_id,
            code=payload.code.upper().strip(),
            name=payload.name.strip(),
            gender=payload.gender.value,
            hostel_type=payload.hostel_type.value,
            status=HostelOperationalStatus.ACTIVE.value,
            description=payload.description,
            address=payload.address,
            curfew_time=payload.curfew_time,
            contact_phone=payload.contact_phone,
            contact_email=payload.contact_email,
            rules_summary=payload.rules_summary,
            amenities=payload.amenities or [],
            visitor_policy=payload.visitor_policy or {},
            emergency_contacts=payload.emergency_contacts or [],
            warden_user_id=payload.warden_user_id,
            assistant_warden_user_id=payload.assistant_warden_user_id,
        )
        db.add(hostel)
        await db.commit()
        await db.refresh(hostel)
        return hostel

    @staticmethod
    async def get_hostel(db: AsyncSession, tenant_id: UUID, hostel_id: UUID) -> Hostel:
        hostel = await db.scalar(
            select(Hostel)
            .options(selectinload(Hostel.blocks).selectinload(HostelBlock.floors))
            .where(Hostel.tenant_id == tenant_id, Hostel.id == hostel_id)
        )
        if not hostel:
            raise NotFoundException("Hostel facility not found")
        return hostel

    @staticmethod
    async def list_hostels(
        db: AsyncSession,
        tenant_id: UUID,
        campus_id: UUID | None = None,
        gender: str | None = None,
        hostel_type: str | None = None,
        status: str | None = None,
        search: str | None = None,
    ) -> list[Hostel]:
        stmt = (
            select(Hostel)
            .options(
                selectinload(Hostel.blocks)
                .selectinload(HostelBlock.floors)
                .selectinload(HostelFloor.rooms)
                .selectinload(HostelRoom.beds)
            )
            .where(Hostel.tenant_id == tenant_id)
        )

        if campus_id:
            stmt = stmt.where(Hostel.campus_id == campus_id)
        if gender and gender != "ALL":
            stmt = stmt.where(Hostel.gender == gender)
        if hostel_type and hostel_type != "ALL":
            stmt = stmt.where(Hostel.hostel_type == hostel_type)
        if status and status != "ALL":
            stmt = stmt.where(Hostel.status == status)
        if search and search.strip():
            term = f"%{search.strip().lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Hostel.name).like(term),
                    func.lower(Hostel.code).like(term),
                    func.lower(Hostel.address).like(term),
                )
            )

        stmt = stmt.order_by(Hostel.name.asc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update_hostel(
        db: AsyncSession, tenant_id: UUID, hostel_id: UUID, payload: HostelUpdate
    ) -> Hostel:
        hostel = await ResidentialService.get_hostel(db, tenant_id, hostel_id)

        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(hostel, key):
                if isinstance(value, HostelGender | HostelType | HostelOperationalStatus):
                    setattr(hostel, key, value.value)
                else:
                    setattr(hostel, key, value)

        await db.commit()
        await db.refresh(hostel)
        return hostel

    @staticmethod
    async def delete_hostel(db: AsyncSession, tenant_id: UUID, hostel_id: UUID) -> None:
        hostel = await ResidentialService.get_hostel(db, tenant_id, hostel_id)

        # Check for active residents
        active_residents = await db.scalar(
            select(func.count(HostelResident.id)).where(
                HostelResident.tenant_id == tenant_id,
                HostelResident.hostel_id == hostel_id,
                HostelResident.status.in_([
                    ResidentLifecycleStatus.CHECKED_IN.value,
                    ResidentLifecycleStatus.ACTIVE.value,
                ]),
            )
        )
        if active_residents and active_residents > 0:
            raise ConflictException("Cannot delete hostel with active residents")

        hostel.status = HostelOperationalStatus.DECOMMISSIONED.value
        await db.commit()

    # --- Blocks & Floors ---

    @staticmethod
    async def create_block(
        db: AsyncSession, tenant_id: UUID, hostel_id: UUID, payload: HostelBlockCreate
    ) -> HostelBlock:
        await ResidentialService.get_hostel(db, tenant_id, hostel_id)
        block = HostelBlock(
            hostel_id=hostel_id,
            name=payload.name.strip(),
            code=payload.code.upper().strip() if payload.code else None,
            description=payload.description,
        )
        db.add(block)
        await db.commit()
        await db.refresh(block)
        return block

    @staticmethod
    async def list_blocks(db: AsyncSession, tenant_id: UUID, hostel_id: UUID) -> list[HostelBlock]:
        await ResidentialService.get_hostel(db, tenant_id, hostel_id)
        stmt = (
            select(HostelBlock)
            .options(selectinload(HostelBlock.floors))
            .where(HostelBlock.hostel_id == hostel_id)
            .order_by(HostelBlock.name.asc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create_floor(
        db: AsyncSession, tenant_id: UUID, block_id: UUID, payload: HostelFloorCreate
    ) -> HostelFloor:
        # Validate block belongs to a hostel of this tenant
        block = await db.scalar(
            select(HostelBlock)
            .join(Hostel, HostelBlock.hostel_id == Hostel.id)
            .where(Hostel.tenant_id == tenant_id, HostelBlock.id == block_id)
        )
        if not block:
            raise NotFoundException("Hostel block not found")

        floor = HostelFloor(
            block_id=block_id,
            floor_number=payload.floor_number,
            name=payload.name or f"Floor {payload.floor_number}",
            is_accessible=payload.is_accessible,
        )
        db.add(floor)
        await db.commit()
        await db.refresh(floor)
        return floor

    # --- Rooms & Beds ---

    @staticmethod
    async def create_room(
        db: AsyncSession, tenant_id: UUID, payload: HostelRoomCreate
    ) -> HostelRoom:
        # Validate floor
        floor = await db.scalar(
            select(HostelFloor)
            .join(HostelBlock, HostelFloor.block_id == HostelBlock.id)
            .join(Hostel, HostelBlock.hostel_id == Hostel.id)
            .where(Hostel.tenant_id == tenant_id, HostelFloor.id == payload.floor_id)
        )
        if not floor:
            raise NotFoundException("Hostel floor not found")

        room = HostelRoom(
            floor_id=payload.floor_id,
            room_number=payload.room_number.strip(),
            room_type=payload.room_type.value,
            capacity=payload.capacity,
            is_accessible=payload.is_accessible,
            is_air_conditioned=payload.is_air_conditioned,
            has_attached_bathroom=payload.has_attached_bathroom,
            amenities=payload.amenities or [],
            restrictions=payload.restrictions or {},
            status=HostelOperationalStatus.ACTIVE.value,
        )
        db.add(room)
        await db.flush()

        # Automatically generate default beds based on room capacity
        for i in range(1, payload.capacity + 1):
            letter = chr(64 + i)  # A, B, C, D...
            bed = HostelBed(
                room_id=room.id,
                bed_code=f"{payload.room_number.strip()}-{letter}",
                is_available=True,
                status=BedStatus.AVAILABLE.value,
            )
            db.add(bed)

        await db.commit()
        await db.refresh(room)
        return room

    @staticmethod
    async def get_room(db: AsyncSession, tenant_id: UUID, room_id: UUID) -> HostelRoom:
        room = await db.scalar(
            select(HostelRoom)
            .join(HostelFloor, HostelRoom.floor_id == HostelFloor.id)
            .join(HostelBlock, HostelFloor.block_id == HostelBlock.id)
            .join(Hostel, HostelBlock.hostel_id == Hostel.id)
            .options(selectinload(HostelRoom.beds))
            .where(Hostel.tenant_id == tenant_id, HostelRoom.id == room_id)
        )
        if not room:
            raise NotFoundException("Hostel room not found")
        return room

    @staticmethod
    async def list_rooms(
        db: AsyncSession,
        tenant_id: UUID,
        hostel_id: UUID | None = None,
        floor_id: UUID | None = None,
        room_type: str | None = None,
        is_accessible: bool | None = None,
        status: str | None = None,
    ) -> list[HostelRoom]:
        stmt = (
            select(HostelRoom)
            .join(HostelFloor, HostelRoom.floor_id == HostelFloor.id)
            .join(HostelBlock, HostelFloor.block_id == HostelBlock.id)
            .join(Hostel, HostelBlock.hostel_id == Hostel.id)
            .options(selectinload(HostelRoom.beds))
            .where(Hostel.tenant_id == tenant_id)
        )
        if hostel_id:
            stmt = stmt.where(Hostel.id == hostel_id)
        if floor_id:
            stmt = stmt.where(HostelRoom.floor_id == floor_id)
        if room_type and room_type != "ALL":
            stmt = stmt.where(HostelRoom.room_type == room_type)
        if is_accessible is not None:
            stmt = stmt.where(HostelRoom.is_accessible == is_accessible)
        if status and status != "ALL":
            stmt = stmt.where(HostelRoom.status == status)

        stmt = stmt.order_by(HostelRoom.room_number.asc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update_room(
        db: AsyncSession, tenant_id: UUID, room_id: UUID, payload: HostelRoomUpdate
    ) -> HostelRoom:
        room = await ResidentialService.get_room(db, tenant_id, room_id)

        # Capacity reduction safety check: cannot reduce below active occupancy
        if payload.capacity is not None and payload.capacity < room.capacity:
            occupied_count = sum(
                1 for b in room.beds if b.status in (BedStatus.OCCUPIED.value, BedStatus.RESERVED.value)
            )
            if payload.capacity < occupied_count:
                raise ConflictException(
                    f"Cannot reduce room capacity to {payload.capacity}. Current occupancy is {occupied_count}."
                )

        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(room, key):
                if isinstance(value, RoomType | HostelOperationalStatus):
                    setattr(room, key, value.value)
                else:
                    setattr(room, key, value)

        await db.commit()
        await db.refresh(room)
        return room

    @staticmethod
    async def create_bed(
        db: AsyncSession, tenant_id: UUID, payload: HostelBedCreate
    ) -> HostelBed:
        room = await ResidentialService.get_room(db, tenant_id, payload.room_id)

        # Check unique bed code in room
        existing = await db.scalar(
            select(HostelBed).where(
                HostelBed.room_id == payload.room_id,
                HostelBed.bed_code == payload.bed_code.upper().strip(),
            )
        )
        if existing:
            raise ConflictException(f"Bed code '{payload.bed_code}' already exists in this room")

        bed = HostelBed(
            room_id=payload.room_id,
            bed_code=payload.bed_code.upper().strip(),
            is_available=True,
            status=BedStatus.AVAILABLE.value,
        )
        db.add(bed)
        await db.commit()
        await db.refresh(bed)
        return bed

    @staticmethod
    async def get_bed(db: AsyncSession, tenant_id: UUID, bed_id: UUID) -> HostelBed:
        bed = await db.scalar(
            select(HostelBed)
            .join(HostelRoom, HostelBed.room_id == HostelRoom.id)
            .join(HostelFloor, HostelRoom.floor_id == HostelFloor.id)
            .join(HostelBlock, HostelFloor.block_id == HostelBlock.id)
            .join(Hostel, HostelBlock.hostel_id == Hostel.id)
            .options(selectinload(HostelBed.room))
            .where(Hostel.tenant_id == tenant_id, HostelBed.id == bed_id)
        )
        if not bed:
            raise NotFoundException("Hostel bed not found")
        return bed

    @staticmethod
    async def list_beds(
        db: AsyncSession,
        tenant_id: UUID,
        hostel_id: UUID | None = None,
        room_id: UUID | None = None,
        status: str | None = None,
        is_available: bool | None = None,
    ) -> list[HostelBed]:
        stmt = (
            select(HostelBed)
            .join(HostelRoom, HostelBed.room_id == HostelRoom.id)
            .join(HostelFloor, HostelRoom.floor_id == HostelFloor.id)
            .join(HostelBlock, HostelFloor.block_id == HostelBlock.id)
            .join(Hostel, HostelBlock.hostel_id == Hostel.id)
            .options(selectinload(HostelBed.room))
            .where(Hostel.tenant_id == tenant_id)
        )
        if hostel_id:
            stmt = stmt.where(Hostel.id == hostel_id)
        if room_id:
            stmt = stmt.where(HostelBed.room_id == room_id)
        if status and status != "ALL":
            stmt = stmt.where(HostelBed.status == status)
        if is_available is not None:
            stmt = stmt.where(HostelBed.is_available == is_available)

        stmt = stmt.order_by(HostelBed.bed_code.asc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def block_bed(
        db: AsyncSession, tenant_id: UUID, bed_id: UUID, payload: HostelBedBlockRequest
    ) -> HostelBed:
        bed = await ResidentialService.get_bed(db, tenant_id, bed_id)

        if bed.status == BedStatus.OCCUPIED.value:
            raise ConflictException("Cannot block an occupied bed. Resident must be relocated first.")

        bed.status = BedStatus.BLOCKED.value
        bed.is_available = False
        bed.blocked_reason = payload.blocked_reason
        bed.blocked_until = payload.blocked_until

        await db.commit()
        await db.refresh(bed)
        return bed

    @staticmethod
    async def unblock_bed(db: AsyncSession, tenant_id: UUID, bed_id: UUID) -> HostelBed:
        bed = await ResidentialService.get_bed(db, tenant_id, bed_id)

        if bed.status not in (BedStatus.BLOCKED.value, BedStatus.UNDER_MAINTENANCE.value):
            raise BadRequestException("Bed is not blocked or under maintenance")

        bed.status = BedStatus.AVAILABLE.value
        bed.is_available = True
        bed.blocked_reason = None
        bed.blocked_until = None

        await db.commit()
        await db.refresh(bed)
        return bed

    @staticmethod
    async def update_bed_status(
        db: AsyncSession, tenant_id: UUID, bed_id: UUID, payload: HostelBedUpdate
    ) -> HostelBed:
        bed = await ResidentialService.get_bed(db, tenant_id, bed_id)
        if payload.status:
            bed.status = payload.status.value if hasattr(payload.status, "value") else str(payload.status)
            bed.is_available = (bed.status == BedStatus.AVAILABLE.value)
        if payload.blocked_reason is not None:
            bed.blocked_reason = payload.blocked_reason
        if payload.blocked_until is not None:
            bed.blocked_until = payload.blocked_until
        if getattr(payload, "is_available", None) is not None:
            bed.is_available = payload.is_available
        await db.commit()
        await db.refresh(bed)
        return bed

    update_bed = update_bed_status

    # =========================================================================
    # 2. OCCUPANCY INVENTORY & DASHBOARD
    # =========================================================================

    @staticmethod
    async def get_occupancy_dashboard(
        db: AsyncSession, tenant_id: UUID, campus_id: UUID | None = None
    ) -> OccupancyDashboardResponse:
        hostels = await ResidentialService.list_hostels(db, tenant_id, campus_id=campus_id)

        hostel_stats: list[HostelOccupancyStat] = []
        overall_total = 0
        overall_occupied = 0
        overall_reserved = 0
        overall_available = 0
        overall_blocked = 0

        for h in hostels:
            # Authoritative live bed status query directly from database table
            bed_stats_stmt = (
                select(
                    HostelBed.status,
                    func.count(HostelBed.id),
                )
                .join(HostelRoom, HostelBed.room_id == HostelRoom.id)
                .join(HostelFloor, HostelRoom.floor_id == HostelFloor.id)
                .join(HostelBlock, HostelFloor.block_id == HostelBlock.id)
                .where(HostelBlock.hostel_id == h.id)
                .group_by(HostelBed.status)
            )
            raw_counts = (await db.execute(bed_stats_stmt)).all()
            bed_counts = {row[0]: row[1] for row in raw_counts}

            total_beds = sum(bed_counts.values())
            occupied_beds = bed_counts.get(BedStatus.OCCUPIED.value, 0)
            reserved_beds = bed_counts.get(BedStatus.RESERVED.value, 0)
            available_beds = bed_counts.get(BedStatus.AVAILABLE.value, 0)
            blocked_beds = bed_counts.get(BedStatus.BLOCKED.value, 0) + bed_counts.get(
                BedStatus.UNDER_MAINTENANCE.value, 0
            )

            occ_pct = round((occupied_beds / total_beds * 100), 2) if total_beds > 0 else 0.0

            hostel_stats.append(
                HostelOccupancyStat(
                    hostel_id=h.id,
                    hostel_name=h.name,
                    hostel_code=h.code,
                    total_beds=total_beds,
                    occupied_beds=occupied_beds,
                    reserved_beds=reserved_beds,
                    available_beds=available_beds,
                    blocked_beds=blocked_beds,
                    occupancy_percentage=occ_pct,
                )
            )

            overall_total += total_beds
            overall_occupied += occupied_beds
            overall_reserved += reserved_beds
            overall_available += available_beds
            overall_blocked += blocked_beds

        overall_occ_pct = (
            round((overall_occupied / overall_total * 100), 2) if overall_total > 0 else 0.0
        )

        return OccupancyDashboardResponse(
            overall_total_beds=overall_total,
            overall_occupied_beds=overall_occupied,
            overall_reserved_beds=overall_reserved,
            overall_available_beds=overall_available,
            overall_blocked_beds=overall_blocked,
            overall_occupancy_percentage=overall_occ_pct,
            hostel_stats=hostel_stats,
        )

    @staticmethod
    async def get_occupancy_report(
        db: AsyncSession, tenant_id: UUID, hostel_id: UUID | None = None, campus_id: UUID | None = None
    ) -> OccupancyDashboardResponse:
        res = await ResidentialService.get_occupancy_dashboard(db, tenant_id, campus_id=campus_id)
        if hostel_id:
            matched = [s for s in res.hostel_stats if s.hostel_id == hostel_id]
            if matched:
                stat = matched[0]
                return OccupancyDashboardResponse(
                    overall_total_beds=stat.total_beds,
                    overall_occupied_beds=stat.occupied_beds,
                    overall_reserved_beds=stat.reserved_beds,
                    overall_available_beds=stat.available_beds,
                    overall_blocked_beds=stat.blocked_beds,
                    overall_occupancy_percentage=stat.occupancy_percentage,
                    hostel_stats=matched,
                )
        return res

    @staticmethod
    async def get_dashboard_summary(
        db: AsyncSession, tenant_id: UUID
    ) -> ResidentialDashboardSummaryResponse:
        dashboard = await ResidentialService.get_occupancy_dashboard(db, tenant_id)

        total_hostels = await db.scalar(
            select(func.count(Hostel.id)).where(
                Hostel.tenant_id == tenant_id,
                Hostel.status != HostelOperationalStatus.DECOMMISSIONED.value,
            )
        ) or 0

        total_rooms = await db.scalar(
            select(func.count(HostelRoom.id))
            .join(HostelFloor, HostelRoom.floor_id == HostelFloor.id)
            .join(HostelBlock, HostelFloor.block_id == HostelBlock.id)
            .join(Hostel, HostelBlock.hostel_id == Hostel.id)
            .where(Hostel.tenant_id == tenant_id)
        ) or 0

        pending_apps = await db.scalar(
            select(func.count(HostelApplication.id)).where(
                HostelApplication.tenant_id == tenant_id,
                HostelApplication.status.in_([
                    AccommodationApplicationStatus.SUBMITTED.value,
                    AccommodationApplicationStatus.UNDER_REVIEW.value,
                ]),
            )
        ) or 0

        active_residents = await db.scalar(
            select(func.count(HostelResident.id)).where(
                HostelResident.tenant_id == tenant_id,
                HostelResident.status.in_([
                    ResidentLifecycleStatus.CHECKED_IN.value,
                    ResidentLifecycleStatus.ACTIVE.value,
                ]),
            )
        ) or 0

        active_outings = await db.scalar(
            select(func.count(HostelLeavePass.id)).where(
                HostelLeavePass.tenant_id == tenant_id,
                HostelLeavePass.status == OutingStatus.CHECKED_OUT.value,
            )
        ) or 0

        now_utc = datetime.now(UTC)
        overdue_outings = await db.scalar(
            select(func.count(HostelLeavePass.id)).where(
                HostelLeavePass.tenant_id == tenant_id,
                or_(
                    HostelLeavePass.status == OutingStatus.OVERDUE.value,
                    and_(
                        HostelLeavePass.status == OutingStatus.CHECKED_OUT.value,
                        HostelLeavePass.expected_return_time < now_utc,
                    ),
                ),
            )
        ) or 0

        open_complaints = await db.scalar(
            select(func.count(HostelComplaint.id)).where(
                HostelComplaint.tenant_id == tenant_id,
                HostelComplaint.status.in_([
                    ResidentialServiceStatus.OPEN.value,
                    ResidentialServiceStatus.ASSIGNED.value,
                    ResidentialServiceStatus.IN_PROGRESS.value,
                ]),
            )
        ) or 0

        active_visitors = await db.scalar(
            select(func.count(HostelVisitor.id)).where(
                HostelVisitor.tenant_id == tenant_id,
                HostelVisitor.status == VisitorStatus.CHECKED_IN.value,
            )
        ) or 0

        return ResidentialDashboardSummaryResponse(
            total_hostels=total_hostels,
            total_rooms=total_rooms,
            total_beds=dashboard.overall_total_beds,
            occupied_beds=dashboard.overall_occupied_beds,
            available_beds=dashboard.overall_available_beds,
            occupancy_percentage=dashboard.overall_occupancy_percentage,
            pending_applications=pending_apps,
            active_residents=active_residents,
            active_outings=active_outings,
            overdue_outings=overdue_outings,
            open_service_requests=open_complaints,
            active_visitors=active_visitors,
        )

    # =========================================================================
    # 3. ACCOMMODATION APPLICATIONS
    # =========================================================================

    @staticmethod
    async def create_application_cycle(
        db: AsyncSession, tenant_id: UUID, payload: ApplicationCycleCreate | HostelApplicationCycle
    ) -> HostelApplicationCycle:
        if isinstance(payload, HostelApplicationCycle):
            db.add(payload)
            await db.commit()
            await db.refresh(payload)
            return payload

        existing = await db.scalar(
            select(HostelApplicationCycle).where(
                HostelApplicationCycle.tenant_id == tenant_id,
                HostelApplicationCycle.code == payload.code.upper().strip(),
            )
        )
        if existing:
            raise ConflictException(f"Application cycle code '{payload.code}' already exists")

        cycle = HostelApplicationCycle(
            tenant_id=tenant_id,
            academic_year_id=payload.academic_year_id,
            cycle_name=payload.cycle_name.strip(),
            code=payload.code.upper().strip(),
            start_date=payload.start_date,
            end_date=payload.end_date,
            status=ApplicationCycleStatus.OPEN.value,
            max_applications=payload.max_applications,
            eligibility_criteria=payload.eligibility_criteria or {},
            priority_rules=payload.priority_rules or {},
        )
        db.add(cycle)
        await db.commit()
        await db.refresh(cycle)
        return cycle

    @staticmethod
    async def get_application_cycle(
        db: AsyncSession, tenant_id: UUID, cycle_id: UUID
    ) -> HostelApplicationCycle:
        cycle = await db.scalar(
            select(HostelApplicationCycle).where(
                HostelApplicationCycle.tenant_id == tenant_id,
                HostelApplicationCycle.id == cycle_id,
            )
        )
        if not cycle:
            raise NotFoundException("Accommodation application cycle not found")
        return cycle

    @staticmethod
    async def list_application_cycles(
        db: AsyncSession, tenant_id: UUID, status: str | None = None
    ) -> list[HostelApplicationCycle]:
        stmt = select(HostelApplicationCycle).where(HostelApplicationCycle.tenant_id == tenant_id)
        if status and status != "ALL":
            stmt = stmt.where(HostelApplicationCycle.status == status)
        stmt = stmt.order_by(HostelApplicationCycle.start_date.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def submit_application(
        db: AsyncSession,
        tenant_id: UUID,
        payload: AccommodationApplicationCreate | None = None,
        **kwargs,
    ) -> HostelApplication:
        if payload is None:
            payload = AccommodationApplicationCreate(**kwargs)

        cycle = await ResidentialService.get_application_cycle(db, tenant_id, payload.cycle_id)
        if cycle.status != ApplicationCycleStatus.OPEN.value:
            raise BadRequestException("Accommodation intake cycle is not currently open")

        # Validate student enrollment
        student = await db.scalar(
            select(Student).where(Student.tenant_id == tenant_id, Student.id == payload.student_id)
        )
        if not student:
            raise NotFoundException("Student record not found in authoritative enrollment directory")

        # Duplicate check within this cycle
        existing = await db.scalar(
            select(HostelApplication).where(
                HostelApplication.tenant_id == tenant_id,
                HostelApplication.cycle_id == payload.cycle_id,
                HostelApplication.student_id == payload.student_id,
                HostelApplication.status != AccommodationApplicationStatus.WITHDRAWN.value,
            )
        )
        if existing:
            raise ConflictException("Student already has an active application for this intake cycle")

        # Calculate initial policy priority score
        score = Decimal("10.00")
        if payload.accessibility_needed:
            score += Decimal("20.00")
        if payload.special_requests:
            score += Decimal("5.00")

        app_count = await db.scalar(
            select(func.count(HostelApplication.id)).where(
                HostelApplication.tenant_id == tenant_id,
                HostelApplication.cycle_id == payload.cycle_id,
            )
        ) or 0
        app_num = f"HST-{cycle.code}-{app_count + 1:04d}"

        pref_type = payload.preferred_room_type
        if hasattr(pref_type, "value"):
            pref_type_val = pref_type.value
        elif pref_type is not None:
            pref_type_val = str(pref_type)
        else:
            pref_type_val = RoomType.DOUBLE.value

        app = HostelApplication(
            tenant_id=tenant_id,
            cycle_id=payload.cycle_id,
            student_id=payload.student_id,
            application_number=app_num,
            preferred_hostel_id=payload.preferred_hostel_id,
            preferred_room_type=pref_type_val,
            special_requests=payload.special_requests,
            accessibility_needed=payload.accessibility_needed,
            disability_notes=payload.disability_notes,
            emergency_contact_name=payload.emergency_contact_name,
            emergency_contact_phone=payload.emergency_contact_phone,
            priority_score=score,
            status=AccommodationApplicationStatus.SUBMITTED.value,
        )
        db.add(app)
        await db.commit()
        await db.refresh(app)

        await event_publisher.publish(
            db=db,
            tenant_id=tenant_id,
            event_type=DomainEventType.HOSTEL_APPLICATION_SUBMITTED,
            aggregate_type="HostelApplication",
            aggregate_id=app.id,
            payload={
                "application_id": str(app.id),
                "student_id": str(student.id),
                "cycle_id": str(cycle.id),
                "application_number": app.application_number,
            },
        )
        return app

    @staticmethod
    async def get_application(
        db: AsyncSession, tenant_id: UUID, application_id: UUID
    ) -> HostelApplication:
        app = await db.scalar(
            select(HostelApplication).where(
                HostelApplication.tenant_id == tenant_id,
                HostelApplication.id == application_id,
            )
        )
        if not app:
            raise NotFoundException("Hostel application not found")
        return app

    @staticmethod
    async def list_applications(
        db: AsyncSession,
        tenant_id: UUID,
        cycle_id: UUID | None = None,
        student_id: UUID | None = None,
        status: str | None = None,
    ) -> list[HostelApplication]:
        stmt = select(HostelApplication).where(HostelApplication.tenant_id == tenant_id)
        if cycle_id:
            stmt = stmt.where(HostelApplication.cycle_id == cycle_id)
        if student_id:
            stmt = stmt.where(HostelApplication.student_id == student_id)
        if status and status != "ALL":
            stmt = stmt.where(HostelApplication.status == status)

        stmt = stmt.order_by(HostelApplication.priority_score.desc(), HostelApplication.created_at.asc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def review_application(
        db: AsyncSession,
        tenant_id: UUID,
        application_id: UUID | None = None,
        reviewer_id: UUID | None = None,
        payload: AccommodationApplicationReview | None = None,
        status: str | AccommodationApplicationStatus | None = None,
        reviewer_user_id: UUID | None = None,
        review_notes: str | None = None,
        priority_score_override: Decimal | None = None,
        **kwargs,
    ) -> HostelApplication:
        app_id = application_id or kwargs.get("id")
        app = await ResidentialService.get_application(db, tenant_id, app_id)

        rev_id = reviewer_id or reviewer_user_id
        new_status = payload.status if payload else status
        if hasattr(new_status, "value"):
            new_status_val = new_status.value
        elif new_status is not None:
            new_status_val = str(new_status)
        else:
            new_status_val = AccommodationApplicationStatus.APPROVED.value

        notes = payload.review_notes if payload else review_notes
        p_override = payload.priority_score_override if payload else priority_score_override

        app.status = new_status_val
        app.review_notes = notes
        app.reviewer_user_id = rev_id
        app.reviewed_at = datetime.now(UTC)
        if p_override is not None:
            app.priority_score = p_override

        await db.commit()
        await db.refresh(app)

        if new_status_val == AccommodationApplicationStatus.APPROVED.value:
            await event_publisher.publish(
                db=db,
                tenant_id=tenant_id,
                event_type=DomainEventType.HOSTEL_APPLICATION_APPROVED,
                aggregate_type="HostelApplication",
                aggregate_id=app.id,
                payload={
                    "application_id": str(app.id),
                    "student_id": str(app.student_id),
                    "cycle_id": str(app.cycle_id),
                    "reviewer_user_id": str(rev_id) if rev_id else "",
                },
            )

        return app

    # =========================================================================
    # 4. ALLOCATION & WAITLIST ENGINE
    # =========================================================================

    @staticmethod
    async def allocate_bed(
        db: AsyncSession,
        tenant_id: UUID,
        arg3: UUID | AllocationCreate,
        arg4: AllocationCreate | None = None,
        allocated_by: UUID | None = None,
        **kwargs,
    ) -> HostelAllocation:
        """Assign bed transactionally with strict row-level lock preventing double-allocation."""
        if isinstance(arg3, AllocationCreate):
            payload = arg3
            allocated_by_id = allocated_by or kwargs.get("allocated_by_id") or uuid.uuid4()
        else:
            allocated_by_id = allocated_by or arg3
            payload = arg4 or kwargs.get("payload")

        # 1. Row-level pessimistic locking on bed to prevent race conditions
        bed_stmt = (
            select(HostelBed)
            .join(HostelRoom, HostelBed.room_id == HostelRoom.id)
            .join(HostelFloor, HostelRoom.floor_id == HostelFloor.id)
            .join(HostelBlock, HostelFloor.block_id == HostelBlock.id)
            .join(Hostel, HostelBlock.hostel_id == Hostel.id)
            .where(Hostel.tenant_id == tenant_id, HostelBed.id == payload.bed_id)
            .with_for_update()
        )
        bed = await db.scalar(bed_stmt)
        if not bed:
            raise NotFoundException("Target hostel bed not found")

        if bed.status != BedStatus.AVAILABLE.value and not (
            bed.status == BedStatus.RESERVED.value and bed.reserved_until and bed.reserved_until < datetime.now(UTC)
        ):
            raise ConflictException(f"Bed '{bed.bed_code}' is not currently available for allocation (Status: {bed.status})")

        # 2. Check student doesn't already have an active allocation
        existing_alloc = await db.scalar(
            select(HostelAllocation).where(
                HostelAllocation.tenant_id == tenant_id,
                HostelAllocation.student_id == payload.student_id,
                HostelAllocation.academic_year_id == payload.academic_year_id,
                HostelAllocation.status.in_([
                    AllocationStatus.ALLOCATED.value,
                    AllocationStatus.RESERVED.value,
                    AllocationStatus.CHECKED_IN.value,
                ]),
            )
        )
        if existing_alloc:
            raise ConflictException("Student already has an active allocation for this academic year")

        # 3. Mark bed reserved or allocated
        bed.status = BedStatus.OCCUPIED.value if not payload.reserved_until else BedStatus.RESERVED.value
        bed.is_available = False
        bed.reserved_until = payload.reserved_until

        # 4. Create allocation ledger entry
        alloc = HostelAllocation(
            tenant_id=tenant_id,
            bed_id=payload.bed_id,
            student_id=payload.student_id,
            academic_year_id=payload.academic_year_id,
            application_id=payload.application_id,
            check_in_date=payload.check_in_date,
            check_out_date=payload.check_out_date,
            reserved_until=payload.reserved_until,
            status=AllocationStatus.ALLOCATED.value,
            allocated_by_user_id=allocated_by_id,
            notes=payload.notes,
        )
        db.add(alloc)

        # 5. If linked to an application, mark as allocated
        if payload.application_id:
            app = await db.scalar(
                select(HostelApplication).where(
                    HostelApplication.tenant_id == tenant_id,
                    HostelApplication.id == payload.application_id,
                )
            )
            if app:
                app.status = AccommodationApplicationStatus.ALLOCATED.value
                app.allocated_bed_id = bed.id

        await db.commit()
        await db.refresh(alloc)

        await event_publisher.publish(
            db=db,
            tenant_id=tenant_id,
            event_type=DomainEventType.HOSTEL_ALLOCATION_CREATED,
            aggregate_type="HostelAllocation",
            aggregate_id=alloc.id,
            payload={
                "allocation_id": str(alloc.id),
                "student_id": str(alloc.student_id),
                "hostel_id": str(bed.room.floor.block.hostel_id),
                "room_id": str(bed.room_id),
                "bed_number": bed.bed_code,
            },
        )
        return alloc

    @staticmethod
    async def commit_batch_allocation(
        db: AsyncSession,
        tenant_id: UUID,
        payload: BatchAllocationCommitRequest,
        allocated_by: UUID | None = None,
    ) -> list[HostelAllocation]:
        allocated_by_id = allocated_by or uuid.uuid4()
        results = []
        for item in payload.allocations:
            alloc = await ResidentialService.allocate_bed(
                db, tenant_id, item, allocated_by=allocated_by_id
            )
            results.append(alloc)
        return results

    @staticmethod
    async def preview_batch_allocation(
        db: AsyncSession, tenant_id: UUID, payload: BatchAllocationPreviewRequest
    ) -> BatchAllocationPreviewResponse:
        """Evaluate pending applications and match available beds without committing."""
        # 1. Fetch pending approved applications ordered by score
        apps = await db.scalars(
            select(HostelApplication)
            .where(
                HostelApplication.tenant_id == tenant_id,
                HostelApplication.cycle_id == payload.cycle_id,
                HostelApplication.status.in_([
                    AccommodationApplicationStatus.APPROVED.value,
                    AccommodationApplicationStatus.WAITLISTED.value,
                ]),
            )
            .order_by(HostelApplication.priority_score.desc(), HostelApplication.created_at.asc())
            .limit(payload.max_allocations)
        )
        app_list = list(apps)

        # 2. Fetch available beds
        bed_stmt = (
            select(HostelBed)
            .join(HostelRoom, HostelBed.room_id == HostelRoom.id)
            .join(HostelFloor, HostelRoom.floor_id == HostelFloor.id)
            .join(HostelBlock, HostelFloor.block_id == HostelBlock.id)
            .join(Hostel, HostelBlock.hostel_id == Hostel.id)
            .options(
                selectinload(HostelBed.room)
                .selectinload(HostelRoom.floor)
                .selectinload(HostelFloor.block)
            )
            .where(
                Hostel.tenant_id == tenant_id,
                HostelBed.status == BedStatus.AVAILABLE.value,
                HostelBed.is_available.is_(True),
            )
        )
        if payload.hostel_id:
            bed_stmt = bed_stmt.where(Hostel.id == payload.hostel_id)

        available_beds = list((await db.execute(bed_stmt)).scalars().all())

        assigned_bed_ids: set[UUID] = set()
        items: list[BatchAllocationPreviewItem] = []

        for app in app_list:
            matched_bed = None
            for b in available_beds:
                if b.id in assigned_bed_ids:
                    continue
                # Preference match: room type and hostel
                if app.preferred_hostel_id and b.room.floor.block.hostel_id != app.preferred_hostel_id:
                    continue
                if app.preferred_room_type and b.room.room_type != app.preferred_room_type:
                    continue
                matched_bed = b
                break

            # Fallback to any bed if strict match not found
            if not matched_bed:
                for b in available_beds:
                    if b.id in assigned_bed_ids:
                        continue
                    if app.preferred_hostel_id and b.room.floor.block.hostel_id != app.preferred_hostel_id:
                        continue
                    matched_bed = b
                    break

            if matched_bed:
                assigned_bed_ids.add(matched_bed.id)
                items.append(
                    BatchAllocationPreviewItem(
                        application_id=app.id,
                        student_id=app.student_id,
                        preferred_room_type=app.preferred_room_type,
                        priority_score=app.priority_score,
                        proposed_bed_id=matched_bed.id,
                        proposed_bed_code=matched_bed.bed_code,
                        proposed_room_number=matched_bed.room.room_number,
                        is_eligible=True,
                    )
                )
            else:
                items.append(
                    BatchAllocationPreviewItem(
                        application_id=app.id,
                        student_id=app.student_id,
                        preferred_room_type=app.preferred_room_type,
                        priority_score=app.priority_score,
                        is_eligible=False,
                        rejection_reason="No matching vacant bed currently available in preferred facility",
                    )
                )

        eligible = sum(1 for it in items if it.is_eligible)
        return BatchAllocationPreviewResponse(
            total_reviewed=len(items),
            eligible_count=eligible,
            ineligible_count=len(items) - eligible,
            items=items,
        )

    @staticmethod
    async def transfer_allocation(
        db: AsyncSession, tenant_id: UUID, user_id: UUID, allocation_id: UUID, payload: AllocationTransferRequest
    ) -> HostelAllocation:
        """Transfer resident to another bed, freeing the previous bed and occupying the target bed."""
        alloc = await db.scalar(
            select(HostelAllocation).where(
                HostelAllocation.tenant_id == tenant_id,
                HostelAllocation.id == allocation_id,
            )
        )
        if not alloc:
            raise NotFoundException("Hostel allocation not found")

        if alloc.status not in (AllocationStatus.ALLOCATED.value, AllocationStatus.CHECKED_IN.value):
            raise BadRequestException("Only active allocations can be transferred")

        # 1. Lock and validate target bed
        target_bed = await db.scalar(
            select(HostelBed)
            .join(HostelRoom, HostelBed.room_id == HostelRoom.id)
            .join(HostelFloor, HostelRoom.floor_id == HostelFloor.id)
            .join(HostelBlock, HostelFloor.block_id == HostelBlock.id)
            .join(Hostel, HostelBlock.hostel_id == Hostel.id)
            .where(Hostel.tenant_id == tenant_id, HostelBed.id == payload.target_bed_id)
            .with_for_update()
        )
        if not target_bed or target_bed.status != BedStatus.AVAILABLE.value:
            raise ConflictException("Target bed is not available for transfer")

        # 2. Release current bed
        old_bed = await db.scalar(select(HostelBed).where(HostelBed.id == alloc.bed_id))
        if old_bed:
            old_bed.status = BedStatus.AVAILABLE.value
            old_bed.is_available = True

        # 3. Occupy target bed
        target_bed.status = BedStatus.OCCUPIED.value
        target_bed.is_available = False

        # 4. Update allocation record
        alloc.previous_bed_id = alloc.bed_id
        alloc.bed_id = payload.target_bed_id
        alloc.reallocation_reason = payload.reallocation_reason
        if payload.notes:
            alloc.notes = f"{alloc.notes or ''}\nTransfer: {payload.notes}".strip()

        # 5. Update active resident record if already checked in
        resident = await db.scalar(
            select(HostelResident).where(
                HostelResident.tenant_id == tenant_id,
                HostelResident.allocation_id == alloc.id,
            )
        )
        if resident:
            resident.bed_id = payload.target_bed_id

        await db.commit()
        await db.refresh(alloc)
        return alloc

    @staticmethod
    async def cancel_allocation(
        db: AsyncSession, tenant_id: UUID, allocation_id: UUID, reason: str | None = None
    ) -> HostelAllocation:
        alloc = await db.scalar(
            select(HostelAllocation).where(
                HostelAllocation.tenant_id == tenant_id,
                HostelAllocation.id == allocation_id,
            )
        )
        if not alloc:
            raise NotFoundException("Allocation not found")

        # Release bed
        bed = await db.scalar(select(HostelBed).where(HostelBed.id == alloc.bed_id))
        if bed:
            bed.status = BedStatus.AVAILABLE.value
            bed.is_available = True
            bed.reserved_until = None

        alloc.status = AllocationStatus.CANCELLED.value
        if reason:
            alloc.notes = f"{alloc.notes or ''}\nCancelled: {reason}".strip()

        await db.commit()
        await db.refresh(alloc)
        return alloc

    # =========================================================================
    # 5. RESIDENT LIFECYCLE (CHECK-IN & CHECK-OUT)
    # =========================================================================

    @staticmethod
    async def check_in_resident(
        db: AsyncSession,
        tenant_id: UUID,
        arg3: UUID,
        arg4: ResidentCheckInRequest | HostelCheckInRequest | None = None,
        checked_in_by: UUID | None = None,
        warden_id: UUID | None = None,
        **kwargs,
    ) -> HostelResident:
        if isinstance(arg4, (ResidentCheckInRequest, HostelCheckInRequest)):
            payload = arg4
            alloc_id = getattr(payload, "allocation_id", None) or arg3
            warden = checked_in_by or warden_id or uuid.uuid4()
        else:
            warden = checked_in_by or warden_id or arg3
            payload = arg4 or kwargs.get("payload")
            alloc_id = payload.allocation_id if payload else arg3

        alloc = await db.scalar(
            select(HostelAllocation)
            .options(
                selectinload(HostelAllocation.bed)
                .selectinload(HostelBed.room)
                .selectinload(HostelRoom.floor)
                .selectinload(HostelFloor.block)
            )
            .where(
                HostelAllocation.tenant_id == tenant_id,
                HostelAllocation.id == alloc_id,
            )
        )
        if not alloc:
            raise NotFoundException("Valid accommodation allocation not found")

        # Ensure no duplicate check-in
        existing = await db.scalar(
            select(HostelResident).where(
                HostelResident.tenant_id == tenant_id,
                HostelResident.allocation_id == alloc_id,
            )
        )
        if existing:
            raise ConflictException("Resident is already checked in")

        hostel_id = alloc.bed.room.floor.block.hostel_id

        resident = HostelResident(
            tenant_id=tenant_id,
            allocation_id=alloc.id,
            student_id=alloc.student_id,
            bed_id=alloc.bed_id,
            hostel_id=hostel_id,
            academic_year_id=alloc.academic_year_id,
            status=ResidentLifecycleStatus.ACTIVE.value,
            check_in_time=datetime.now(UTC),
            checked_in_by_user_id=warden,
            key_card_issued=True,
            key_number=payload.key_number if payload else None,
            facilities_condition_note=payload.facilities_condition_note if payload else None,
            inventory_handover=(payload.inventory_handover if payload else None) or {"mattress": True, "table": True, "chair": True},
            expected_departure_date=payload.expected_departure_date if payload else None,
        )
        db.add(resident)

        # Update bed & allocation status
        alloc.status = AllocationStatus.CHECKED_IN.value
        alloc.bed.status = BedStatus.OCCUPIED.value
        alloc.bed.is_available = False

        await db.commit()
        await db.refresh(resident)

        await event_publisher.publish(
            db=db,
            tenant_id=tenant_id,
            event_type=DomainEventType.HOSTEL_RESIDENT_CHECKED_IN,
            aggregate_type="HostelResident",
            aggregate_id=resident.id,
            payload={
                "resident_id": str(resident.id),
                "student_id": str(resident.student_id),
                "hostel_id": str(resident.hostel_id),
                "bed_id": str(resident.bed_id),
                "check_in_time": resident.check_in_time.isoformat(),
            },
        )
        return resident

    @staticmethod
    async def check_out_resident(
        db: AsyncSession,
        tenant_id: UUID,
        arg3: UUID,
        arg4: UUID | ResidentCheckOutRequest | HostelCheckOutRequest,
        arg5: ResidentCheckOutRequest | HostelCheckOutRequest | None = None,
        checked_out_by: UUID | None = None,
        warden_id: UUID | None = None,
        **kwargs,
    ) -> HostelResident:
        if isinstance(arg4, (ResidentCheckOutRequest, HostelCheckOutRequest)):
            resident_id = arg3
            payload = arg4
            warden = checked_out_by or warden_id or uuid.uuid4()
        else:
            warden = checked_out_by or warden_id or arg3
            resident_id = arg4
            payload = arg5 or kwargs.get("payload")

        resident = await db.scalar(
            select(HostelResident).where(
                HostelResident.tenant_id == tenant_id,
                HostelResident.id == resident_id,
            )
        )
        if not resident:
            raise NotFoundException("Resident record not found")

        if resident.status not in (ResidentLifecycleStatus.CHECKED_IN.value, ResidentLifecycleStatus.ACTIVE.value):
            raise BadRequestException(f"Resident is currently in status '{resident.status}' and cannot check out")

        now_utc = datetime.now(UTC)
        resident.status = ResidentLifecycleStatus.CHECKED_OUT.value
        resident.check_out_time = now_utc
        resident.checked_out_by_user_id = warden

        checkout_reason = payload.checkout_reason if payload else CheckoutReason.END_OF_TERM
        if hasattr(checkout_reason, "value"):
            resident.checkout_reason = checkout_reason.value
        else:
            resident.checkout_reason = str(checkout_reason)

        resident.room_condition_on_checkout = payload.room_condition_on_checkout if payload else None
        resident.key_returned = payload.key_returned if payload else True
        resident.damage_assessment_notes = payload.damage_assessment_notes if payload else None
        damage_charges = payload.damage_charges_amount if payload else Decimal("0.00")
        resident.damage_charges_amount = damage_charges

        # Damage assessment invoice generation through authoritative Finance module
        if payload and payload.create_damage_invoice and damage_charges > Decimal("0.00"):
            damage_inv = await ResidentialService._create_damage_invoice(
                db=db,
                tenant_id=tenant_id,
                student_id=resident.student_id,
                academic_year_id=resident.academic_year_id,
                amount=damage_charges,
                notes=payload.damage_assessment_notes or "Hostel room check-out damage charges",
            )
            resident.damage_invoice_id = damage_inv.id

        # Release bed
        bed = await db.scalar(select(HostelBed).where(HostelBed.id == resident.bed_id))
        if bed:
            bed.status = BedStatus.AVAILABLE.value
            bed.is_available = True
            bed.reserved_until = None

        # Update allocation
        alloc = await db.scalar(select(HostelAllocation).where(HostelAllocation.id == resident.allocation_id))
        if alloc:
            alloc.status = AllocationStatus.CHECKED_OUT.value
            alloc.check_out_date = date.today()

        await db.commit()
        await db.refresh(resident)

        await event_publisher.publish(
            db=db,
            tenant_id=tenant_id,
            event_type=DomainEventType.HOSTEL_RESIDENT_CHECKED_OUT,
            aggregate_type="HostelResident",
            aggregate_id=resident.id,
            payload={
                "resident_id": str(resident.id),
                "student_id": str(resident.student_id),
                "hostel_id": str(resident.hostel_id),
                "bed_id": str(resident.bed_id),
                "check_out_time": resident.check_out_time.isoformat(),
                "checkout_reason": resident.checkout_reason,
            },
        )
        return resident

    @staticmethod
    async def _create_damage_invoice(
        db: AsyncSession, tenant_id: UUID, student_id: UUID, academic_year_id: UUID, amount: Decimal, notes: str
    ) -> Invoice:
        # Resolve or seed HOSTEL fee category
        fee_cat = await db.scalar(
            select(FeeCategory).where(
                FeeCategory.tenant_id == tenant_id, FeeCategory.code == "HOSTEL"
            )
        )
        if not fee_cat:
            fee_cat = FeeCategory(
                tenant_id=tenant_id,
                code="HOSTEL",
                name="Hostel & Residence",
                is_active=True,
            )
            db.add(fee_cat)
            await db.flush()

        inv_count = await db.scalar(
            select(func.count(Invoice.id)).where(Invoice.tenant_id == tenant_id)
        ) or 0
        inv_num = f"INV-HST-DMG-{date.today().year}-{inv_count + 1:04d}"

        invoice = Invoice(
            tenant_id=tenant_id,
            student_id=student_id,
            academic_year_id=academic_year_id,
            invoice_number=inv_num,
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=7),
            currency="INR",
            gross_amount=amount,
            net_payable=amount,
            paid_amount=Decimal("0.00"),
            balance_amount=amount,
            status="ISSUED",
            remarks=notes,
        )
        db.add(invoice)
        await db.flush()

        item = InvoiceLineItem(
            invoice_id=invoice.id,
            category_id=fee_cat.id,
            description=f"Hostel Damage Charges: {notes}",
            amount=amount,
        )
        db.add(item)
        return invoice

    @staticmethod
    async def list_residents(
        db: AsyncSession,
        tenant_id: UUID,
        hostel_id: UUID | None = None,
        status: str | None = None,
    ) -> list[HostelResident]:
        stmt = select(HostelResident).where(HostelResident.tenant_id == tenant_id)
        if hostel_id:
            stmt = stmt.where(HostelResident.hostel_id == hostel_id)
        if status and status != "ALL":
            stmt = stmt.where(HostelResident.status == status)

        stmt = stmt.order_by(HostelResident.check_in_time.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    # =========================================================================
    # 6. RESIDENTIAL FEES & FINANCIAL INTEGRATION
    # =========================================================================

    @staticmethod
    async def create_fee_plan(
        db: AsyncSession, tenant_id: UUID, payload: HostelFeePlanCreate
    ) -> HostelFeePlan:
        existing = await db.scalar(
            select(HostelFeePlan).where(
                HostelFeePlan.tenant_id == tenant_id,
                HostelFeePlan.code == payload.code.upper().strip(),
            )
        )
        if existing:
            raise ConflictException(f"Fee plan code '{payload.code}' already exists")

        plan = HostelFeePlan(
            tenant_id=tenant_id,
            code=payload.code.upper().strip(),
            name=payload.name.strip(),
            hostel_id=payload.hostel_id,
            room_type=payload.room_type.value,
            billing_cycle=payload.billing_cycle.value,
            rent_amount=payload.rent_amount,
            mess_amount=payload.mess_amount,
            deposit_amount=payload.deposit_amount,
            utility_amount=payload.utility_amount,
            amenities_amount=payload.amenities_amount,
            total_amount=payload.total_amount,
            is_active=True,
            proration_rule=payload.proration_rule,
        )
        db.add(plan)
        await db.commit()
        await db.refresh(plan)
        return plan

    @staticmethod
    async def list_fee_plans(
        db: AsyncSession, tenant_id: UUID, hostel_id: UUID | None = None, is_active: bool | None = None
    ) -> list[HostelFeePlan]:
        stmt = select(HostelFeePlan).where(HostelFeePlan.tenant_id == tenant_id)
        if hostel_id:
            stmt = stmt.where(or_(HostelFeePlan.hostel_id == hostel_id, HostelFeePlan.hostel_id.is_(None)))
        if is_active is not None:
            stmt = stmt.where(HostelFeePlan.is_active == is_active)
        stmt = stmt.order_by(HostelFeePlan.name.asc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def generate_hostel_invoice(
        db: AsyncSession, tenant_id: UUID, payload: GenerateHostelInvoiceRequest
    ) -> HostelInvoiceResponse:
        """Issue residential accommodation invoice in authoritative Finance module without duplicates."""
        plan = await db.scalar(
            select(HostelFeePlan).where(
                HostelFeePlan.tenant_id == tenant_id,
                HostelFeePlan.id == payload.fee_plan_id,
            )
        )
        if not plan:
            raise NotFoundException("Hostel fee plan not found")

        # Duplicate invoice detection for same student + plan + academic year
        existing_inv = await db.scalar(
            select(Invoice).where(
                Invoice.tenant_id == tenant_id,
                Invoice.student_id == payload.student_id,
                Invoice.academic_year_id == payload.academic_year_id,
                Invoice.remarks.like(f"%Fee Plan: {plan.code}%"),
                Invoice.status.in_(["ISSUED", "PAID", "PARTIALLY_PAID"]),
            )
        )
        if existing_inv:
            raise ConflictException(f"Invoice already issued for student under plan '{plan.code}'")

        # Amount calculation with optional proration
        final_amount = plan.total_amount
        if payload.apply_proration and payload.proration_days and payload.proration_days > 0:
            daily_rate = plan.rent_amount / Decimal("180.00")  # approx 1 semester
            final_amount = (daily_rate * Decimal(payload.proration_days)) + plan.deposit_amount + plan.utility_amount

        # Get HOSTEL category
        fee_cat = await db.scalar(
            select(FeeCategory).where(
                FeeCategory.tenant_id == tenant_id, FeeCategory.code == "HOSTEL"
            )
        )
        if not fee_cat:
            fee_cat = FeeCategory(
                tenant_id=tenant_id,
                code="HOSTEL",
                name="Hostel & Residence",
                is_active=True,
            )
            db.add(fee_cat)
            await db.flush()

        inv_count = await db.scalar(
            select(func.count(Invoice.id)).where(Invoice.tenant_id == tenant_id)
        ) or 0
        inv_number = f"INV-HST-{date.today().year}-{inv_count + 1:04d}"

        invoice = Invoice(
            tenant_id=tenant_id,
            student_id=payload.student_id,
            academic_year_id=payload.academic_year_id,
            invoice_number=inv_number,
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=payload.due_days),
            currency="INR",
            gross_amount=final_amount,
            net_payable=final_amount,
            paid_amount=Decimal("0.00"),
            balance_amount=final_amount,
            status="ISSUED",
            remarks=f"Residential Fee Plan: {plan.code} ({plan.name})",
        )
        db.add(invoice)
        await db.flush()

        # Itemize
        item = InvoiceLineItem(
            invoice_id=invoice.id,
            category_id=fee_cat.id,
            description=f"Hostel Accommodation ({plan.name})",
            amount=final_amount,
        )
        db.add(item)
        await db.commit()

        return HostelInvoiceResponse(
            invoice_id=invoice.id,
            invoice_number=invoice.invoice_number,
            student_id=payload.student_id,
            gross_amount=invoice.gross_amount,
            net_payable=invoice.net_payable,
            due_date=invoice.due_date,
            status=invoice.status,
        )

    @staticmethod
    async def generate_fee_invoices(
        db: AsyncSession,
        tenant_id: UUID,
        fee_plan_id: UUID,
        payload: GenerateHostelInvoiceRequest,
        generated_by: UUID | None = None,
    ) -> HostelInvoiceResponse:
        payload.fee_plan_id = fee_plan_id
        return await ResidentialService.generate_hostel_invoice(db, tenant_id, payload)

    # =========================================================================
    # 7. MESS & MEAL-PLAN MANAGEMENT
    # =========================================================================

    @staticmethod
    async def create_meal_plan(
        db: AsyncSession, tenant_id: UUID, payload: MealPlanCreate
    ) -> HostelMealPlan:
        existing = await db.scalar(
            select(HostelMealPlan).where(
                HostelMealPlan.tenant_id == tenant_id,
                HostelMealPlan.code == payload.code.upper().strip(),
            )
        )
        if existing:
            raise ConflictException(f"Meal plan code '{payload.code}' already exists")

        meal_plan = HostelMealPlan(
            tenant_id=tenant_id,
            hostel_id=payload.hostel_id,
            code=payload.code.upper().strip(),
            name=payload.name.strip(),
            meal_type=payload.meal_type.value,
            description=payload.description,
            monthly_rate=payload.monthly_rate,
            daily_rate=payload.daily_rate,
            serves_breakfast=payload.serves_breakfast,
            serves_lunch=payload.serves_lunch,
            serves_snacks=payload.serves_snacks,
            serves_dinner=payload.serves_dinner,
            is_active=True,
        )
        db.add(meal_plan)
        await db.commit()
        await db.refresh(meal_plan)
        return meal_plan

    @staticmethod
    async def list_meal_plans(
        db: AsyncSession, tenant_id: UUID, hostel_id: UUID | None = None
    ) -> list[HostelMealPlan]:
        stmt = select(HostelMealPlan).where(HostelMealPlan.tenant_id == tenant_id)
        if hostel_id:
            stmt = stmt.where(or_(HostelMealPlan.hostel_id == hostel_id, HostelMealPlan.hostel_id.is_(None)))
        stmt = stmt.order_by(HostelMealPlan.name.asc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def enroll_meal_plan(
        db: AsyncSession, tenant_id: UUID, payload: MealEnrollmentCreate
    ) -> HostelMealEnrollment:
        # Check plan
        plan = await db.scalar(
            select(HostelMealPlan).where(
                HostelMealPlan.tenant_id == tenant_id,
                HostelMealPlan.id == payload.meal_plan_id,
            )
        )
        if not plan:
            raise NotFoundException("Meal plan not found")

        enroll = HostelMealEnrollment(
            tenant_id=tenant_id,
            student_id=payload.student_id,
            meal_plan_id=payload.meal_plan_id,
            resident_id=payload.resident_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
            dietary_requirements=payload.dietary_requirements,
            status=MealEnrollmentStatus.ACTIVE.value,
        )
        db.add(enroll)
        await db.commit()
        await db.refresh(enroll)
        return enroll

    @staticmethod
    async def get_meal_headcount_summary(
        db: AsyncSession,
        tenant_id: UUID,
        for_date: date,
        hostel_id: UUID | None = None,
        meal_plan_id: UUID | None = None,
    ) -> MealHeadcountResponse:
        stmt = (
            select(HostelMealEnrollment)
            .join(HostelMealPlan, HostelMealEnrollment.meal_plan_id == HostelMealPlan.id)
            .options(selectinload(HostelMealEnrollment.meal_plan))
            .where(
                HostelMealEnrollment.tenant_id == tenant_id,
                HostelMealEnrollment.status == MealEnrollmentStatus.ACTIVE.value,
                HostelMealEnrollment.start_date <= for_date,
                or_(HostelMealEnrollment.end_date.is_(None), HostelMealEnrollment.end_date >= for_date),
            )
        )
        if hostel_id:
            stmt = stmt.where(HostelMealPlan.hostel_id == hostel_id)
        if meal_plan_id:
            stmt = stmt.where(HostelMealEnrollment.meal_plan_id == meal_plan_id)

        enrollments = list((await db.execute(stmt)).scalars().all())

        bf = sum(1 for e in enrollments if e.meal_plan.serves_breakfast)
        ln = sum(1 for e in enrollments if e.meal_plan.serves_lunch)
        sn = sum(1 for e in enrollments if e.meal_plan.serves_snacks)
        dn = sum(1 for e in enrollments if e.meal_plan.serves_dinner)
        veg = sum(1 for e in enrollments if e.meal_plan.meal_type in (MealType.VEG.value, MealType.JAIN.value))
        non_veg = len(enrollments) - veg

        return MealHeadcountResponse(
            date=for_date,
            hostel_id=hostel_id,
            breakfast_count=bf,
            lunch_count=ln,
            snacks_count=sn,
            dinner_count=dn,
            vegetarian_count=veg,
            non_vegetarian_count=non_veg,
        )

    @staticmethod
    async def get_meal_headcount(
        db: AsyncSession,
        tenant_id: UUID,
        meal_plan_id: UUID | None = None,
        service_date: date | None = None,
        hostel_id: UUID | None = None,
        for_date: date | None = None,
    ) -> MealHeadcountResponse:
        d = service_date or for_date or date.today()
        return await ResidentialService.get_meal_headcount_summary(
            db, tenant_id, for_date=d, hostel_id=hostel_id, meal_plan_id=meal_plan_id
        )

    # =========================================================================
    # 8. OUTINGS, LEAVES & ATTENDANCE
    # =========================================================================

    @staticmethod
    async def request_outing(
        db: AsyncSession,
        tenant_id: UUID,
        payload: OutingRequestCreate,
        requested_by: UUID | None = None,
        **kwargs,
    ) -> HostelLeavePass:
        if payload.expected_return_time <= payload.departure_time:
            raise BadRequestException("Expected return time must be after departure time")

        pass_code = f"OUT-{uuid.uuid4().hex[:6].upper()}"
        status_val = (
            OutingStatus.APPROVED.value
            if payload.parent_consent_verified
            else OutingStatus.REQUESTED.value
        )

        leave = HostelLeavePass(
            tenant_id=tenant_id,
            student_id=payload.student_id,
            hostel_id=payload.hostel_id,
            outing_type=payload.outing_type.value if hasattr(payload.outing_type, "value") else str(payload.outing_type),
            pass_code=pass_code,
            departure_time=payload.departure_time,
            expected_return_time=payload.expected_return_time,
            destination=payload.destination,
            reason=payload.reason,
            parent_consent_verified=payload.parent_consent_verified,
            parent_contact_phone=payload.parent_contact_phone,
            status=status_val,
        )
        db.add(leave)
        await db.commit()
        await db.refresh(leave)
        return leave

    @staticmethod
    async def approve_outing(
        db: AsyncSession, tenant_id: UUID, warden_id: UUID, pass_id: UUID, payload: OutingApprovalRequest
    ) -> HostelLeavePass:
        leave = await db.scalar(
            select(HostelLeavePass).where(
                HostelLeavePass.tenant_id == tenant_id, HostelLeavePass.id == pass_id
            )
        )
        if not leave:
            raise NotFoundException("Outing pass request not found")

        leave.status = payload.status.value if hasattr(payload.status, "value") else str(payload.status)
        leave.approved_by_user_id = warden_id

        await db.commit()
        await db.refresh(leave)
        return leave

    @staticmethod
    async def record_departure(
        db: AsyncSession,
        tenant_id: UUID,
        pass_id: UUID,
        guard_id: UUID | None = None,
        payload: OutingDepartureRequest | None = None,
        **kwargs,
    ) -> HostelLeavePass:
        leave = await db.scalar(
            select(HostelLeavePass).where(
                HostelLeavePass.tenant_id == tenant_id, HostelLeavePass.id == pass_id
            )
        )
        if not leave:
            raise NotFoundException("Outing pass not found")

        leave.actual_departure_time = (payload.actual_departure_time if payload else None) or datetime.now(UTC)
        leave.status = OutingStatus.DEPARTED.value

        await db.commit()
        await db.refresh(leave)
        return leave

    record_outing_departure = record_departure

    @staticmethod
    async def record_return(
        db: AsyncSession,
        tenant_id: UUID,
        pass_id: UUID,
        guard_id: UUID | None = None,
        payload: OutingReturnRequest | None = None,
        **kwargs,
    ) -> HostelLeavePass:
        leave = await db.scalar(
            select(HostelLeavePass).where(
                HostelLeavePass.tenant_id == tenant_id, HostelLeavePass.id == pass_id
            )
        )
        if not leave:
            raise NotFoundException("Outing pass not found")

        ret_time = (payload.actual_return_time if payload else None) or datetime.now(UTC)
        leave.actual_return_time = ret_time

        exp_ret = leave.expected_return_time
        if exp_ret and exp_ret.tzinfo is None:
            exp_ret = exp_ret.replace(tzinfo=UTC)
        if ret_time and ret_time.tzinfo is None:
            ret_time = ret_time.replace(tzinfo=UTC)

        if exp_ret and ret_time > exp_ret:
            leave.status = OutingStatus.OVERDUE.value
            await event_publisher.publish(
                db=db,
                tenant_id=tenant_id,
                event_type=DomainEventType.HOSTEL_OUTING_OVERDUE,
                aggregate_type="HostelLeavePass",
                aggregate_id=leave.id,
                payload={
                    "pass_id": str(leave.id),
                    "student_id": str(leave.student_id),
                    "hostel_id": str(leave.hostel_id) if leave.hostel_id else "",
                    "expected_return_time": leave.expected_return_time.isoformat(),
                },
            )
        else:
            leave.status = OutingStatus.COMPLETED.value

        await db.commit()
        await db.refresh(leave)
        return leave

    record_outing_return = record_return

    @staticmethod
    async def list_outings(
        db: AsyncSession,
        tenant_id: UUID,
        student_id: UUID | None = None,
        hostel_id: UUID | None = None,
        status: str | None = None,
    ) -> list[HostelLeavePass]:
        stmt = select(HostelLeavePass).where(HostelLeavePass.tenant_id == tenant_id)
        if student_id:
            stmt = stmt.where(HostelLeavePass.student_id == student_id)
        if hostel_id:
            stmt = stmt.where(HostelLeavePass.hostel_id == hostel_id)
        if status and status != "ALL":
            stmt = stmt.where(HostelLeavePass.status == status)

        stmt = stmt.order_by(HostelLeavePass.departure_time.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def record_night_attendance(
        db: AsyncSession, tenant_id: UUID, warden_id: UUID, payload: NightAttendanceBatchRequest
    ) -> list[HostelNightAttendance]:
        results: list[HostelNightAttendance] = []
        for rec in payload.records:
            existing = await db.scalar(
                select(HostelNightAttendance).where(
                    HostelNightAttendance.tenant_id == tenant_id,
                    HostelNightAttendance.attendance_date == payload.attendance_date,
                    HostelNightAttendance.resident_id == rec.resident_id,
                )
            )
            if existing:
                existing.status = rec.status.value if hasattr(rec.status, "value") else str(rec.status)
                existing.remarks = rec.remarks
                existing.checked_by_user_id = warden_id
                results.append(existing)
            else:
                att = HostelNightAttendance(
                    tenant_id=tenant_id,
                    hostel_id=payload.hostel_id,
                    resident_id=rec.resident_id,
                    attendance_date=payload.attendance_date,
                    status=rec.status.value if hasattr(rec.status, "value") else str(rec.status),
                    checked_by_user_id=warden_id,
                    remarks=rec.remarks,
                )
                db.add(att)
                results.append(att)

        await db.commit()
        return results

    # =========================================================================
    # 9. VISITOR & GATE-PASS MANAGEMENT
    # =========================================================================

    @staticmethod
    async def register_visitor(
        db: AsyncSession,
        tenant_id: UUID,
        payload: VisitorRegisterRequest,
        checked_in_by: UUID | None = None,
        warden_id: UUID | None = None,
        **kwargs,
    ) -> HostelVisitor:
        pass_code = f"VIS-{uuid.uuid4().hex[:6].upper()}"
        now_utc = datetime.now(UTC)

        visitor = HostelVisitor(
            tenant_id=tenant_id,
            hostel_id=payload.hostel_id,
            host_student_id=payload.host_student_id,
            visitor_name=payload.visitor_name.strip(),
            visitor_phone=payload.visitor_phone.strip(),
            visitor_id_proof_type=payload.visitor_id_proof_type,
            visitor_id_proof_number=payload.visitor_id_proof_number.strip(),
            visitor_relation=payload.visitor_relation.strip(),
            purpose=payload.purpose.strip(),
            pass_code=pass_code,
            expected_check_in=payload.expected_check_in,
            expected_check_out=payload.expected_check_out,
            actual_check_in=now_utc,
            status=VisitorStatus.CHECKED_IN.value,
            approved_by_user_id=checked_in_by or warden_id,
            remarks=payload.remarks,
        )
        db.add(visitor)
        await db.commit()
        await db.refresh(visitor)
        return visitor

    @staticmethod
    async def check_in_visitor(
        db: AsyncSession, tenant_id: UUID, warden_id: UUID, visitor_id: UUID, payload: VisitorCheckInRequest
    ) -> HostelVisitor:
        visitor = await db.scalar(
            select(HostelVisitor).where(
                HostelVisitor.tenant_id == tenant_id, HostelVisitor.id == visitor_id
            )
        )
        if not visitor:
            raise NotFoundException("Visitor record not found")

        visitor.actual_check_in = payload.actual_check_in or datetime.now(UTC)
        visitor.status = VisitorStatus.CHECKED_IN.value
        visitor.approved_by_user_id = warden_id

        await db.commit()
        await db.refresh(visitor)
        return visitor

    @staticmethod
    async def checkout_visitor(
        db: AsyncSession,
        tenant_id: UUID,
        visitor_id: UUID,
        payload: VisitorCheckOutRequest | None = None,
        checked_out_by: UUID | None = None,
        **kwargs,
    ) -> HostelVisitor:
        visitor = await db.scalar(
            select(HostelVisitor).where(
                HostelVisitor.tenant_id == tenant_id, HostelVisitor.id == visitor_id
            )
        )
        if not visitor:
            raise NotFoundException("Visitor record not found")

        now_utc = datetime.now(UTC)
        visitor.actual_check_out = (payload.actual_check_out if payload else None) or now_utc
        visitor.status = VisitorStatus.CHECKED_OUT.value

        await db.commit()
        await db.refresh(visitor)
        return visitor

    check_out_visitor = checkout_visitor

    @staticmethod
    async def list_visitors(
        db: AsyncSession,
        tenant_id: UUID,
        hostel_id: UUID | None = None,
        student_id: UUID | None = None,
        status: str | None = None,
    ) -> list[HostelVisitor]:
        stmt = select(HostelVisitor).where(HostelVisitor.tenant_id == tenant_id)
        if hostel_id:
            stmt = stmt.where(HostelVisitor.hostel_id == hostel_id)
        if student_id:
            stmt = stmt.where(HostelVisitor.host_student_id == student_id)
        if status and status != "ALL":
            stmt = stmt.where(HostelVisitor.status == status)

        stmt = stmt.order_by(HostelVisitor.expected_check_in.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create_gate_pass(
        db: AsyncSession,
        tenant_id: UUID,
        payload: HostelGatePassCreate | GatePassCreateRequest,
        issued_by: UUID | None = None,
        **kwargs,
    ) -> HostelGatePass:
        resident_id = getattr(payload, "resident_id", None)
        student = await db.scalar(
            select(Student).where(Student.tenant_id == tenant_id, Student.id == resident_id)
        )
        if student:
            student_id = student.id
            active_resident = await db.scalar(
                select(HostelResident).where(
                    HostelResident.tenant_id == tenant_id,
                    HostelResident.student_id == student.id,
                )
            )
            res_id = active_resident.id if active_resident else student.id
            h_id = active_resident.hostel_id if active_resident else (
                getattr(payload, "hostel_id", None) or await db.scalar(
                    select(Hostel.id).where(Hostel.tenant_id == tenant_id).order_by(Hostel.created_at.desc())
                )
            )
        else:
            resident = await db.scalar(
                select(HostelResident).where(
                    HostelResident.tenant_id == tenant_id, HostelResident.id == resident_id
                )
            )
            student_id = resident.student_id if resident else resident_id
            h_id = resident.hostel_id if resident else (
                getattr(payload, "hostel_id", None) or await db.scalar(
                    select(Hostel.id).where(Hostel.tenant_id == tenant_id).order_by(Hostel.created_at.desc())
                )
            )
            res_id = resident_id

        pass_code = f"GP-{uuid.uuid4().hex[:6].upper()}"

        gp = HostelGatePass(
            tenant_id=tenant_id,
            resident_id=res_id,
            student_id=student_id,
            hostel_id=h_id,
            pass_code=pass_code,
            purpose=payload.purpose.strip(),
            destination=getattr(payload, "destination", None),
            valid_from=payload.valid_from,
            valid_until=payload.valid_until,
            status=GatePassStatus.ACTIVE.value,
        )
        db.add(gp)
        await db.commit()
        await db.refresh(gp)
        return gp

    issue_gate_pass = create_gate_pass

    @staticmethod
    async def verify_gate_pass(
        db: AsyncSession,
        tenant_id: UUID,
        pass_id_or_guard: UUID,
        payload_or_code: HostelGatePassVerifyRequest | str,
        guard_id: UUID | None = None,
        action: str = "EXIT",
        **kwargs,
    ) -> HostelGatePass:
        if isinstance(payload_or_code, HostelGatePassVerifyRequest):
            code = payload_or_code.pass_code.strip()
            act = payload_or_code.action or action
            guard = guard_id or pass_id_or_guard
            gp = await db.scalar(
                select(HostelGatePass).where(
                    HostelGatePass.tenant_id == tenant_id,
                    or_(HostelGatePass.id == pass_id_or_guard, HostelGatePass.pass_code == code),
                )
            )
        else:
            code = str(payload_or_code).strip()
            act = action
            guard = guard_id or pass_id_or_guard
            gp = await db.scalar(
                select(HostelGatePass).where(
                    HostelGatePass.tenant_id == tenant_id, HostelGatePass.pass_code == code
                )
            )

        if not gp:
            raise NotFoundException("Gate pass code invalid")

        now_utc = datetime.now(UTC)
        val_until = gp.valid_until
        if val_until and val_until.tzinfo is None:
            val_until = val_until.replace(tzinfo=UTC)
        if val_until and val_until < now_utc:
            gp.status = GatePassStatus.EXPIRED.value
            await db.commit()
            raise BadRequestException("Gate pass has expired")

        gp.verified_by_user_id = guard
        gp.verified_at = now_utc

        if act == "EXIT":
            gp.actual_exit_time = now_utc
            gp.status = GatePassStatus.USED.value
        elif act == "ENTRY":
            gp.actual_entry_time = now_utc
            gp.status = GatePassStatus.USED.value

        await db.commit()
        await db.refresh(gp)
        return gp

    # =========================================================================
    # 10. MAINTENANCE & SERVICE REQUESTS
    # =========================================================================

    @staticmethod
    async def create_service_request(
        db: AsyncSession,
        tenant_id: UUID,
        payload: ServiceRequestCreate,
        reported_by_user_id: UUID | None = None,
        **kwargs,
    ) -> HostelComplaint:
        room = await ResidentialService.get_room(db, tenant_id, payload.room_id)
        hostel_id = payload.hostel_id or room.floor.block.hostel_id

        ticket_count = await db.scalar(
            select(func.count(HostelComplaint.id)).where(HostelComplaint.tenant_id == tenant_id)
        ) or 0
        ticket_number = f"CMP-{date.today().year}-{ticket_count + 1:04d}"

        user_id = reported_by_user_id or payload.student_id
        user = await db.scalar(select(User).where(User.id == user_id))
        if not user:
            user = await db.scalar(select(User).where(User.primary_tenant_id == tenant_id))

        # Check or create an Asset record for maintenance work order integration
        cat = await db.scalar(select(AssetCategory).where(AssetCategory.tenant_id == tenant_id))
        if not cat:
            cat = AssetCategory(
                tenant_id=tenant_id,
                code="FACILITIES",
                name="Hostel & Residential Facilities",
            )
            db.add(cat)
            await db.flush()

        asset = await db.scalar(
            select(Asset).where(Asset.tenant_id == tenant_id)
        )
        if not asset:
            asset = Asset(
                tenant_id=tenant_id,
                asset_tag=f"AST-FAC-{uuid.uuid4().hex[:6].upper()}",
                name=f"Room {room.room_number} Fixtures",
                category_id=cat.id,
                acquisition_date=date.today(),
            )
            db.add(asset)
            await db.flush()

        wo_count = await db.scalar(
            select(func.count(MaintenanceWorkOrder.id)).where(MaintenanceWorkOrder.tenant_id == tenant_id)
        ) or 0
        wo_number = f"WO-HST-{date.today().year}-{wo_count + 1:04d}"

        work_order = MaintenanceWorkOrder(
            tenant_id=tenant_id,
            work_order_number=wo_number,
            asset_id=asset.id,
            reported_by_id=user.id if user else reported_by_user_id,
            reported_symptoms=payload.title or payload.description,
            priority="HIGH",
            status="REPORTED",
        )
        db.add(work_order)
        await db.flush()

        cat_val = payload.category.value if hasattr(payload.category, "value") else str(payload.category)
        prio_val = payload.priority.value if hasattr(payload.priority, "value") else str(payload.priority)

        complaint = HostelComplaint(
            tenant_id=tenant_id,
            ticket_number=ticket_number,
            student_id=payload.student_id,
            hostel_id=hostel_id,
            room_id=payload.room_id,
            work_order_id=work_order.id,
            category=cat_val,
            priority=prio_val,
            title=payload.title or f"{cat_val} issue in room {room.room_number}",
            description=payload.description.strip(),
            status=ResidentialServiceStatus.OPEN.value,
            sla_deadline=datetime.now(UTC) + timedelta(hours=24 if prio_val == ResidentialServicePriority.EMERGENCY.value else 72),
        )
        db.add(complaint)
        await db.commit()
        await db.refresh(complaint)

        await event_publisher.publish(
            db=db,
            tenant_id=tenant_id,
            event_type=DomainEventType.HOSTEL_SERVICE_REQUEST_CREATED,
            aggregate_type="HostelComplaint",
            aggregate_id=complaint.id,
            payload={
                "complaint_id": str(complaint.id),
                "student_id": str(complaint.student_id),
                "hostel_id": str(complaint.hostel_id) if complaint.hostel_id else "",
                "room_id": str(complaint.room_id),
                "category": complaint.category,
                "priority": complaint.priority,
            },
        )
        return complaint

    submit_service_request = create_service_request

    @staticmethod
    async def update_service_request(
        db: AsyncSession,
        tenant_id: UUID,
        request_id: UUID,
        payload: ServiceRequestUpdate,
        resolved_by: UUID | None = None,
        **kwargs,
    ) -> HostelComplaint:
        complaint = await db.scalar(
            select(HostelComplaint).where(
                HostelComplaint.tenant_id == tenant_id, HostelComplaint.id == request_id
            )
        )
        if not complaint:
            raise NotFoundException("Service request ticket not found")

        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(complaint, key):
                if isinstance(value, ResidentialServiceStatus):
                    setattr(complaint, key, value.value)
                else:
                    setattr(complaint, key, value)

        status_val = payload.status.value if hasattr(payload.status, "value") else str(payload.status)
        if status_val == "RESOLVED":
            complaint.status = "RESOLVED"
            if not complaint.resolved_at:
                complaint.resolved_at = datetime.now(UTC)

        await db.commit()
        await db.refresh(complaint)
        return complaint

    @staticmethod
    async def submit_service_feedback(
        db: AsyncSession, tenant_id: UUID, student_id: UUID, request_id: UUID, payload: ServiceRequestFeedback
    ) -> HostelComplaint:
        complaint = await db.scalar(
            select(HostelComplaint).where(
                HostelComplaint.tenant_id == tenant_id,
                HostelComplaint.id == request_id,
                HostelComplaint.student_id == student_id,
            )
        )
        if not complaint:
            raise NotFoundException("Service request not found for this student")

        complaint.student_rating = payload.student_rating
        complaint.student_feedback = payload.student_feedback
        if complaint.status == ResidentialServiceStatus.RESOLVED.value:
            complaint.status = ResidentialServiceStatus.CLOSED.value

        await db.commit()
        await db.refresh(complaint)
        return complaint

    @staticmethod
    async def list_service_requests(
        db: AsyncSession,
        tenant_id: UUID,
        hostel_id: UUID | None = None,
        student_id: UUID | None = None,
        category: str | None = None,
        status: str | None = None,
    ) -> list[HostelComplaint]:
        stmt = select(HostelComplaint).where(HostelComplaint.tenant_id == tenant_id)
        if hostel_id:
            stmt = stmt.where(HostelComplaint.hostel_id == hostel_id)
        if student_id:
            stmt = stmt.where(HostelComplaint.student_id == student_id)
        if category and category != "ALL":
            stmt = stmt.where(HostelComplaint.category == category)
        if status and status != "ALL":
            stmt = stmt.where(HostelComplaint.status == status)

        stmt = stmt.order_by(HostelComplaint.created_at.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    # =========================================================================
    # 11. SAFETY, INCIDENTS & INSPECTIONS
    # =========================================================================

    @staticmethod
    async def report_incident(
        db: AsyncSession,
        tenant_id: UUID,
        payload: IncidentCreate,
        reported_by: UUID | None = None,
        **kwargs,
    ) -> HostelIncident:
        inc_count = await db.scalar(
            select(func.count(HostelIncident.id)).where(HostelIncident.tenant_id == tenant_id)
        ) or 0
        incident_number = f"INC-{date.today().year}-{inc_count + 1:04d}"

        reporter_id = reported_by or payload.reporter_user_id

        incident = HostelIncident(
            tenant_id=tenant_id,
            incident_number=incident_number,
            hostel_id=payload.hostel_id,
            incident_type=payload.incident_type.value if hasattr(payload.incident_type, "value") else str(payload.incident_type),
            severity=payload.severity.value if hasattr(payload.severity, "value") else str(payload.severity),
            incident_time=payload.incident_time,
            location_description=payload.location_description.strip(),
            reporter_user_id=reporter_id,
            involved_student_ids=payload.involved_student_ids or [],
            description=payload.description.strip(),
            action_taken=payload.action_taken,
            is_disciplinary_referral=payload.is_disciplinary_referral,
            status=ResidentialIncidentStatus.REPORTED.value,
            assigned_warden_user_id=payload.assigned_warden_user_id,
        )
        db.add(incident)
        await db.commit()
        await db.refresh(incident)

        await event_publisher.publish(
            db=db,
            tenant_id=tenant_id,
            event_type=DomainEventType.HOSTEL_INCIDENT_REPORTED,
            aggregate_type="HostelIncident",
            aggregate_id=incident.id,
            payload={
                "incident_id": str(incident.id),
                "hostel_id": str(incident.hostel_id),
                "severity": incident.severity,
                "incident_type": incident.incident_type,
            },
        )
        return incident

    @staticmethod
    async def update_incident(
        db: AsyncSession, tenant_id: UUID, incident_id: UUID, payload: IncidentUpdate
    ) -> HostelIncident:
        incident = await db.scalar(
            select(HostelIncident).where(
                HostelIncident.tenant_id == tenant_id, HostelIncident.id == incident_id
            )
        )
        if not incident:
            raise NotFoundException("Incident record not found")

        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(incident, key):
                if isinstance(value, ResidentialIncidentSeverity | ResidentialIncidentStatus):
                    setattr(incident, key, value.value)
                else:
                    setattr(incident, key, value)

        if payload.status == ResidentialIncidentStatus.CLOSED and not incident.resolved_at:
            incident.resolved_at = datetime.now(UTC)

        await db.commit()
        await db.refresh(incident)
        return incident

    @staticmethod
    async def list_incidents(
        db: AsyncSession,
        tenant_id: UUID,
        hostel_id: UUID | None = None,
        severity: str | None = None,
        status: str | None = None,
    ) -> list[HostelIncident]:
        stmt = select(HostelIncident).where(HostelIncident.tenant_id == tenant_id)
        if hostel_id:
            stmt = stmt.where(HostelIncident.hostel_id == hostel_id)
        if severity and severity != "ALL":
            stmt = stmt.where(HostelIncident.severity == severity)
        if status and status != "ALL":
            stmt = stmt.where(HostelIncident.status == status)

        stmt = stmt.order_by(HostelIncident.incident_time.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def record_safety_inspection(
        db: AsyncSession,
        tenant_id: UUID,
        payload: SafetyInspectionCreate,
        inspector_id: UUID | None = None,
        **kwargs,
    ) -> HostelSafetyInspection:
        insp_user = inspector_id or payload.inspector_user_id
        status_val = payload.status.value if hasattr(payload.status, "value") else str(payload.status)

        insp = HostelSafetyInspection(
            tenant_id=tenant_id,
            hostel_id=payload.hostel_id,
            inspection_date=payload.inspection_date,
            inspector_user_id=insp_user,
            fire_safety_passed=payload.fire_safety_passed,
            electrical_safety_passed=payload.electrical_safety_passed,
            hygiene_passed=payload.hygiene_passed,
            structural_passed=payload.structural_passed,
            checklist_results=payload.checklist_results or {},
            critical_findings=payload.critical_findings,
            action_items=payload.action_items or [],
            status=status_val,
        )
        db.add(insp)
        await db.commit()
        await db.refresh(insp)
        return insp

    create_inspection = record_safety_inspection

    @staticmethod
    async def list_safety_inspections(
        db: AsyncSession, tenant_id: UUID, hostel_id: UUID | None = None
    ) -> list[HostelSafetyInspection]:
        stmt = select(HostelSafetyInspection).where(HostelSafetyInspection.tenant_id == tenant_id)
        if hostel_id:
            stmt = stmt.where(HostelSafetyInspection.hostel_id == hostel_id)
        stmt = stmt.order_by(HostelSafetyInspection.inspection_date.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def sweep_residential_operations(
        db: AsyncSession, tenant_id: UUID
    ) -> dict[str, int]:
        """Scheduled operations sweep for residential life management (Step 54).

        Checks:
        1. Overdue student outings / curfew breaches.
        2. Expired bed holds & releases.
        3. Overdue visitor passes.
        4. Expired gate passes.
        5. Residential service requests SLA breaches.
        """
        now = datetime.now(UTC)
        metrics = {
            "overdue_outings": 0,
            "expired_bed_holds": 0,
            "overdue_visitors": 0,
            "expired_gate_passes": 0,
            "sla_breached_complaints": 0,
        }

        # 1. Overdue student outings
        stmt_outings = select(HostelLeavePass).where(
            HostelLeavePass.tenant_id == tenant_id,
            HostelLeavePass.status == OutingStatus.DEPARTED.value,
            HostelLeavePass.expected_return_time < now,
        )
        res_outings = await db.execute(stmt_outings)
        for outing in res_outings.scalars().all():
            outing.status = OutingStatus.OVERDUE.value
            metrics["overdue_outings"] += 1
            await event_publisher.publish(
                db=db,
                tenant_id=tenant_id,
                event_type=DomainEventType.HOSTEL_OUTING_OVERDUE,
                aggregate_type="HostelLeavePass",
                aggregate_id=outing.id,
                payload={
                    "outing_id": str(outing.id),
                    "student_id": str(outing.student_id),
                    "hostel_id": str(outing.hostel_id) if outing.hostel_id else None,
                    "expected_return_time": outing.expected_return_time.isoformat(),
                },
            )

        # 2. Expired temporary bed holds
        stmt_beds = (
            select(HostelBed)
            .join(HostelRoom, HostelBed.room_id == HostelRoom.id)
            .join(HostelFloor, HostelRoom.floor_id == HostelFloor.id)
            .join(HostelBlock, HostelFloor.block_id == HostelBlock.id)
            .join(Hostel, HostelBlock.hostel_id == Hostel.id)
            .where(
                Hostel.tenant_id == tenant_id,
                HostelBed.status == BedStatus.RESERVED.value,
                HostelBed.reserved_until.isnot(None),
                HostelBed.reserved_until < now,
            )
        )
        res_beds = await db.execute(stmt_beds)
        for bed in res_beds.scalars().all():
            bed.status = BedStatus.AVAILABLE.value
            bed.is_available = True
            bed.reserved_until = None
            metrics["expired_bed_holds"] += 1

        # 3. Overdue visitor passes
        stmt_visitors = select(HostelVisitor).where(
            HostelVisitor.tenant_id == tenant_id,
            HostelVisitor.status == VisitorStatus.CHECKED_IN.value,
            HostelVisitor.expected_check_out < now,
        )
        res_visitors = await db.execute(stmt_visitors)
        for vis in res_visitors.scalars().all():
            vis.status = VisitorStatus.OVERDUE.value
            metrics["overdue_visitors"] += 1

        # 4. Expired gate passes
        stmt_passes = select(HostelGatePass).where(
            HostelGatePass.tenant_id == tenant_id,
            HostelGatePass.status == GatePassStatus.ISSUED.value,
            HostelGatePass.valid_until < now,
        )
        res_passes = await db.execute(stmt_passes)
        for gp in res_passes.scalars().all():
            gp.status = GatePassStatus.EXPIRED.value
            metrics["expired_gate_passes"] += 1

        # 5. Complaints breaching SLA
        stmt_complaints = select(HostelComplaint).where(
            HostelComplaint.tenant_id == tenant_id,
            HostelComplaint.status.in_(["SUBMITTED", "IN_PROGRESS", "ASSIGNED"]),
            HostelComplaint.sla_deadline.isnot(None),
            HostelComplaint.sla_deadline < now,
        )
        res_complaints = await db.execute(stmt_complaints)
        metrics["sla_breached_complaints"] = len(res_complaints.scalars().all())

        await db.commit()
        return metrics

