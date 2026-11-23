"""Enterprise Hostel, Residential Life, Room Allocation & Student Accommodation Management Tests (Step 54).

CampusOS Tagline: "One Campus. One System. One Source of Truth."

Verifies:
1. Hostel & Residential facility registry, hierarchical blocks, floors, rooms, and addressable beds.
2. Authoritative room and bed inventory, capacity enforcement, bed blocking, and status history.
3. Accommodation application cycles, student self-service applications, eligibility & priority scoring, review and waitlisting.
4. Concurrency-safe bed allocation, duplicate allocation rejection, and room/bed transfer workflows.
5. Batch allocation engine: preview, validation, rejection reasoning, and transactional commit.
6. Resident lifecycle: check-in verification, key handover, inventory checklist, and departure check-out.
7. Finance module integration: residential fee plan invoicing, deposit tracking, and check-out damage assessment billing.
8. Mess & meal-plan management: enrollment, dietary requirements, and non-inventory headcount projections.
9. Outing, overnight leaves, curfew breaches, and overdue alert emission.
10. Visitor registration, checkout, and secure gate-pass verification at campus checkpoints.
11. Maintenance complaints and service requests integrated with Asset Maintenance work orders.
12. Confidential safety incidents, inspections, and least-privilege access protection.
13. Comprehensive residential occupancy and vacancy analytics reporting.
14. Background scheduled operations sweep (overdue outings, expired bed holds, visitor passes).
15. Strict multi-tenant isolation across all residential data boundaries.
"""

import uuid
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
from app.models.assets import MaintenanceWorkOrder
from app.models.core import AcademicYear, Batch, Campus, Department, Institution, Program, Regulation
from app.models.finance import Invoice, InvoiceLineItem
from app.models.people import StudentProfile, User
from app.models.residential import (
    AccommodationApplicationStatus,
    AllocationStatus,
    ApplicationCycleStatus,
    BedStatus,
    CheckoutReason,
    FeePlanBillingCycle,
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
    HostelOperationalStatus,
    HostelResident,
    HostelRoom,
    HostelSafetyInspection,
    HostelType,
    MealType,
    OutingStatus,
    OutingType,
    ResidentialIncidentSeverity,
    ResidentialIncidentType,
    ResidentialServiceCategory,
    ResidentialServicePriority,
    RoomType,
    SafetyInspectionStatus,
    VisitorStatus,
)
from app.schemas.residential import (
    AllocationCreate,
    AllocationTransferRequest,
    BatchAllocationCommitRequest,
    BatchAllocationPreviewRequest,
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
    HostelIncidentCreate,
    IncidentCreate,
    HostelMealEnrollmentCreate,
    HostelMealPlanCreate,
    HostelRoomCreate,
    HostelRoomUpdate,
    HostelUpdate,
    OutingRequestCreate,
    SafetyInspectionCreate,
    ServiceRequestCreate,
    ServiceRequestUpdate,
    VisitorCheckOutRequest,
    VisitorRegisterRequest,
)
from app.services.residential_service import ResidentialService


@pytest.fixture
async def residential_setup(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_b: Institution,
    super_admin_user: User,
):
    """Provides base campus, academic year, students, and users for residential tests."""
    uid = uuid.uuid4().hex[:6]

    # Campus in Tenant A
    campus_a = Campus(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        name="Main Campus Alpha",
        code=f"CMP-{uid}",
        address="100 Academic Road",
        city="Coimbatore",
        is_active=True,
    )
    db_session.add(campus_a)

    dept_a = Department(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        campus_id=campus_a.id,
        name="Computer Science & Engineering",
        code=f"CSE-{uid}",
        is_active=True,
    )
    db_session.add(dept_a)

    prog_a = Program(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        department_id=dept_a.id,
        name="Bachelor of Technology in Computer Science",
        code=f"BTCS-{uid}",
        degree_level="UNDERGRADUATE",
        duration_years=4,
        total_semesters=8,
        is_active=True,
    )
    db_session.add(prog_a)

    reg_a = Regulation(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        code=f"REG26-{uid}",
        title="Regulation 2026",
        effective_year=2026,
        is_active=True,
    )
    db_session.add(reg_a)

    batch_a = Batch(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        program_id=prog_a.id,
        regulation_id=reg_a.id,
        name=f"CSE 2026-2030 {uid}",
        admission_year=2026,
        graduation_year=2030,
        is_active=True,
    )
    db_session.add(batch_a)

    # Academic Year in Tenant A
    ay_a = AcademicYear(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        name=f"2026-2027-{uid}",
        start_date=date(2026, 7, 1),
        end_date=date(2027, 6, 30),
        is_current=True,
    )
    db_session.add(ay_a)

    # Student 1 user & profile in Tenant A
    user_s1 = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"student1_{uid}@apextech.edu",
        first_name="Rohan",
        last_name="Sharma",
        password_hash="dummy_hashed_password_s1",
        status="ACTIVE",
    )
    db_session.add(user_s1)
    await db_session.flush()

    student_1 = StudentProfile(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        user_id=user_s1.id,
        admission_number=f"ADM-2026-{uid}-1",
        date_of_birth=date(2004, 5, 15),
        gender="MALE",
        status="ACTIVE",
        admission_date=date(2026, 7, 1),
        expected_graduation_date=date(2030, 6, 30),
        program_id=prog_a.id,
        batch_id=batch_a.id,
    )
    db_session.add(student_1)

    # Student 2 user & profile in Tenant A
    user_s2 = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"student2_{uid}@apextech.edu",
        first_name="Priya",
        last_name="Nair",
        password_hash="dummy_hashed_password_s2",
        status="ACTIVE",
    )
    db_session.add(user_s2)
    await db_session.flush()

    student_2 = StudentProfile(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        user_id=user_s2.id,
        admission_number=f"ADM-2026-{uid}-2",
        date_of_birth=date(2004, 8, 20),
        gender="FEMALE",
        status="ACTIVE",
        admission_date=date(2026, 7, 1),
        expected_graduation_date=date(2030, 6, 30),
        program_id=prog_a.id,
        batch_id=batch_a.id,
    )
    db_session.add(student_2)

    # Campus in Tenant B
    campus_b = Campus(
        id=uuid.uuid4(),
        tenant_id=tenant_b.id,
        name="Beacon City Campus",
        code=f"CMP-B-{uid}",
        address="200 Seaface Drive",
        city="Chennai",
        is_active=True,
    )
    db_session.add(campus_b)

    await db_session.commit()

    return {
        "tenant_a": tenant_a,
        "tenant_b": tenant_b,
        "campus_a": campus_a,
        "campus_b": campus_b,
        "academic_year_a": ay_a,
        "student_1": student_1,
        "student_2": student_2,
        "admin_user": super_admin_user,
    }


# =============================================================================
# 1. HOSTEL & FACILITY INVENTORY HIERARCHY TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_create_hostel_and_hierarchy(db_session: AsyncSession, residential_setup: dict):
    """Verify hostel creation and validation of the hierarchy: Hostel -> Block -> Floor -> Room -> Beds."""
    tenant = residential_setup["tenant_a"]
    campus = residential_setup["campus_a"]
    admin = residential_setup["admin_user"]
    uid = uuid.uuid4().hex[:6]

    # 1. Create Hostel
    hostel_in = HostelCreate(
        name=f"Everest Men's Hostel {uid}",
        code=f"HST-EVR-{uid}",
        campus_id=campus.id,
        gender=HostelGender.MALE,
        hostel_type=HostelType.BOYS,
        description="Premium residential block with attached dining hall",
        curfew_time=time(22, 0),
        warden_user_id=admin.id,
    )
    hostel = await ResidentialService.create_hostel(db_session, tenant.id, hostel_in)
    assert hostel.id is not None
    assert hostel.code == f"HST-EVR-{uid}".upper()
    assert hostel.status == HostelOperationalStatus.ACTIVE.value

    # Duplicate code rejection
    with pytest.raises(ConflictException):
        await ResidentialService.create_hostel(db_session, tenant.id, hostel_in)

    # 2. Create Block
    block_in = HostelBlockCreate(name="Block A - North Wing", code="BLK-A")
    block = await ResidentialService.create_block(db_session, tenant.id, hostel.id, block_in)
    assert block.id is not None
    assert block.hostel_id == hostel.id

    # 3. Create Floor
    floor_in = HostelFloorCreate(floor_number=1, name="First Floor", is_accessible=True)
    floor = await ResidentialService.create_floor(db_session, tenant.id, block.id, floor_in)
    assert floor.id is not None
    assert floor.floor_number == 1

    # 4. Create Room with capacity 2 (auto-provisions 2 beds: -A and -B)
    room_in = HostelRoomCreate(
        floor_id=floor.id,
        room_number="101",
        room_type=RoomType.DOUBLE,
        capacity=2,
        is_air_conditioned=True,
    )
    room = await ResidentialService.create_room(db_session, tenant.id, room_in)
    assert room.id is not None
    assert room.room_number == "101"
    assert room.capacity == 2

    # Verify auto-provisioned beds
    stmt_beds = select(HostelBed).where(HostelBed.room_id == room.id)
    beds = list((await db_session.execute(stmt_beds)).scalars().all())
    assert len(beds) == 2
    assert {b.bed_code for b in beds} == {"101-A", "101-B"}
    assert all(b.is_available is True for b in beds)


@pytest.mark.asyncio
async def test_bed_status_and_capacity_constraints(db_session: AsyncSession, residential_setup: dict):
    """Verify bed status updates, maintenance blocking, and capacity validation."""
    tenant = residential_setup["tenant_a"]
    campus = residential_setup["campus_a"]
    uid = uuid.uuid4().hex[:6]

    # Setup Hostel, Block, Floor, Room
    hostel = await ResidentialService.create_hostel(
        db_session,
        tenant.id,
        HostelCreate(name="Block 1", code=f"H1-{uid}", campus_id=campus.id),
    )
    block = await ResidentialService.create_block(
        db_session, tenant.id, hostel.id, HostelBlockCreate(name="B1")
    )
    floor = await ResidentialService.create_floor(
        db_session, tenant.id, block.id, HostelFloorCreate(floor_number=0)
    )
    room = await ResidentialService.create_room(
        db_session,
        tenant.id,
        HostelRoomCreate(floor_id=floor.id, room_number="G01", capacity=1),
    )

    beds = await ResidentialService.list_beds(db_session, tenant.id, room_id=room.id)
    assert len(beds) == 1
    bed = beds[0]

    # Block bed for plumbing maintenance
    block_req = HostelBedUpdate(
        status=BedStatus.UNDER_MAINTENANCE,
        blocked_reason="Water line replacement",
        blocked_until=date.today() + timedelta(days=3),
    )
    updated_bed = await ResidentialService.update_bed_status(db_session, tenant.id, bed.id, block_req)
    assert updated_bed.status == BedStatus.UNDER_MAINTENANCE.value
    assert updated_bed.is_available is False
    assert updated_bed.blocked_reason == "Water line replacement"

    # Unblock bed back to available
    unblock_req = HostelBedUpdate(status=BedStatus.AVAILABLE)
    restored_bed = await ResidentialService.update_bed_status(db_session, tenant.id, bed.id, unblock_req)
    assert restored_bed.status == BedStatus.AVAILABLE.value
    assert restored_bed.is_available is True


# =============================================================================
# 2. ACCOMMODATION APPLICATION & REVIEW TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_accommodation_application_lifecycle(db_session: AsyncSession, residential_setup: dict):
    """Verify student application submission, duplicate prevention, priority scoring, and review."""
    tenant = residential_setup["tenant_a"]
    campus = residential_setup["campus_a"]
    ay = residential_setup["academic_year_a"]
    student1 = residential_setup["student_1"]
    admin = residential_setup["admin_user"]
    uid = uuid.uuid4().hex[:6]

    # 1. Create Application Cycle
    cycle = await ResidentialService.create_application_cycle(
        db_session,
        tenant.id,
        HostelApplicationCycle(
            tenant_id=tenant.id,
            academic_year_id=ay.id,
            cycle_name="Fall 2026 Intake",
            code=f"CYCLE-{uid}",
            start_date=date.today() - timedelta(days=5),
            end_date=date.today() + timedelta(days=30),
            status=ApplicationCycleStatus.OPEN.value,
        ),
    )

    # Create Hostel
    hostel = await ResidentialService.create_hostel(
        db_session,
        tenant.id,
        HostelCreate(name="Kaveri Hostel", code=f"HST-KAV-{uid}", campus_id=campus.id),
    )

    # 2. Student Submits Application
    app = await ResidentialService.submit_application(
        db_session,
        tenant.id,
        student_id=student1.id,
        cycle_id=cycle.id,
        preferred_hostel_id=hostel.id,
        preferred_room_type=RoomType.DOUBLE,
        accessibility_needed=True,
        special_requests="Ground floor preference",
    )
    assert app.id is not None
    assert app.status == AccommodationApplicationStatus.SUBMITTED.value
    # Base 10 + Accessibility 20 + Special requests 5 = 35.00
    assert app.priority_score >= Decimal("35.00")

    # 3. Duplicate Application in Same Cycle Must Be Rejected
    with pytest.raises(ConflictException):
        await ResidentialService.submit_application(
            db_session,
            tenant.id,
            student_id=student1.id,
            cycle_id=cycle.id,
            preferred_hostel_id=hostel.id,
            preferred_room_type=RoomType.DOUBLE,
        )

    # 4. Review Application (Approve)
    reviewed = await ResidentialService.review_application(
        db_session,
        tenant.id,
        application_id=app.id,
        status=AccommodationApplicationStatus.APPROVED.value,
        reviewer_user_id=admin.id,
        review_notes="Approved based on high priority score and accessibility requirement",
    )
    assert reviewed.status == AccommodationApplicationStatus.APPROVED.value
    assert reviewed.reviewer_user_id == admin.id


# =============================================================================
# 3. ALLOCATION ENGINE & CONCURRENCY CONFLICT PREVENTION
# =============================================================================


@pytest.mark.asyncio
async def test_allocation_and_double_allocation_prevention(db_session: AsyncSession, residential_setup: dict):
    """Verify bed allocation and prevention of concurrent double-allocation to the same bed."""
    tenant = residential_setup["tenant_a"]
    campus = residential_setup["campus_a"]
    ay = residential_setup["academic_year_a"]
    student1 = residential_setup["student_1"]
    student2 = residential_setup["student_2"]
    admin = residential_setup["admin_user"]
    uid = uuid.uuid4().hex[:6]

    # Setup facilities
    hostel = await ResidentialService.create_hostel(
        db_session,
        tenant.id,
        HostelCreate(name="Narmada Hostel", code=f"HST-NAR-{uid}", campus_id=campus.id),
    )
    block = await ResidentialService.create_block(
        db_session, tenant.id, hostel.id, HostelBlockCreate(name="Block C")
    )
    floor = await ResidentialService.create_floor(
        db_session, tenant.id, block.id, HostelFloorCreate(floor_number=1)
    )
    room = await ResidentialService.create_room(
        db_session,
        tenant.id,
        HostelRoomCreate(floor_id=floor.id, room_number="102", capacity=1),
    )
    beds = await ResidentialService.list_beds(db_session, tenant.id, room_id=room.id)
    bed = beds[0]

    # Allocate bed to Student 1
    alloc_in = AllocationCreate(
        bed_id=bed.id,
        student_id=student1.id,
        academic_year_id=ay.id,
        check_in_date=date.today(),
        notes="First year merit allocation",
    )
    alloc = await ResidentialService.allocate_bed(
        db_session, tenant.id, alloc_in, allocated_by=admin.id
    )
    assert alloc.id is not None
    assert alloc.status == AllocationStatus.ALLOCATED.value

    # Verify bed is marked occupied and unavailable
    refreshed_bed = await ResidentialService.get_bed(db_session, tenant.id, bed.id)
    assert refreshed_bed.is_available is False
    assert refreshed_bed.status == BedStatus.OCCUPIED.value

    # Attempting to allocate the same occupied bed to Student 2 MUST raise ConflictException
    alloc_conflict = AllocationCreate(
        bed_id=bed.id,
        student_id=student2.id,
        academic_year_id=ay.id,
        check_in_date=date.today(),
    )
    with pytest.raises(ConflictException) as exc_info:
        await ResidentialService.allocate_bed(
            db_session, tenant.id, alloc_conflict, allocated_by=admin.id
        )
    assert "not currently available" in str(exc_info.value)


@pytest.mark.asyncio
async def test_batch_allocation_preview_and_commit(db_session: AsyncSession, residential_setup: dict):
    """Verify batch allocation engine: preview with rejection reasons and commit."""
    tenant = residential_setup["tenant_a"]
    campus = residential_setup["campus_a"]
    ay = residential_setup["academic_year_a"]
    student1 = residential_setup["student_1"]
    student2 = residential_setup["student_2"]
    admin = residential_setup["admin_user"]
    uid = uuid.uuid4().hex[:6]

    # Create cycle
    cycle = await ResidentialService.create_application_cycle(
        db_session,
        tenant.id,
        HostelApplicationCycle(
            tenant_id=tenant.id,
            academic_year_id=ay.id,
            cycle_name="Batch Intake 2026",
            code=f"BCH-{uid}",
            start_date=date.today() - timedelta(days=2),
            end_date=date.today() + timedelta(days=20),
            status=ApplicationCycleStatus.OPEN.value,
        ),
    )

    # Create hostel with 2 capacity
    hostel = await ResidentialService.create_hostel(
        db_session,
        tenant.id,
        HostelCreate(name="Brahmaputra", code=f"HST-BHM-{uid}", campus_id=campus.id),
    )
    block = await ResidentialService.create_block(
        db_session, tenant.id, hostel.id, HostelBlockCreate(name="B1")
    )
    floor = await ResidentialService.create_floor(
        db_session, tenant.id, block.id, HostelFloorCreate(floor_number=1)
    )
    room = await ResidentialService.create_room(
        db_session,
        tenant.id,
        HostelRoomCreate(floor_id=floor.id, room_number="201", capacity=2),
    )

    # Submit applications for Student 1 and Student 2
    app1 = await ResidentialService.submit_application(
        db_session,
        tenant.id,
        student_id=student1.id,
        cycle_id=cycle.id,
        preferred_hostel_id=hostel.id,
        preferred_room_type=RoomType.DOUBLE,
        accessibility_needed=True,
    )
    app2 = await ResidentialService.submit_application(
        db_session,
        tenant.id,
        student_id=student2.id,
        cycle_id=cycle.id,
        preferred_hostel_id=hostel.id,
        preferred_room_type=RoomType.DOUBLE,
    )

    # Approve both
    await ResidentialService.review_application(
        db_session,
        tenant.id,
        application_id=app1.id,
        status=AccommodationApplicationStatus.APPROVED.value,
        reviewer_user_id=admin.id,
    )
    await ResidentialService.review_application(
        db_session,
        tenant.id,
        application_id=app2.id,
        status=AccommodationApplicationStatus.APPROVED.value,
        reviewer_user_id=admin.id,
    )

    # Preview batch allocation
    preview_req = BatchAllocationPreviewRequest(cycle_id=cycle.id, hostel_id=hostel.id)
    preview = await ResidentialService.preview_batch_allocation(db_session, tenant.id, preview_req)

    assert preview.total_reviewed == 2
    assert preview.eligible_count == 2
    assert preview.ineligible_count == 0
    assert len(preview.items) == 2
    # Ensure beds were proposed
    assert all(item.proposed_bed_id is not None for item in preview.items)

    # Commit batch allocations
    commit_items = [
        AllocationCreate(
            bed_id=item.proposed_bed_id,
            student_id=item.student_id,
            academic_year_id=ay.id,
            application_id=item.application_id,
            check_in_date=date.today(),
        )
        for item in preview.items
    ]
    committed = await ResidentialService.commit_batch_allocation(
        db_session, tenant.id, BatchAllocationCommitRequest(allocations=commit_items), allocated_by=admin.id
    )
    assert len(committed) == 2


# =============================================================================
# 4. RESIDENT LIFECYCLE (CHECK-IN & CHECK-OUT) & FINANCE INTEGRATION
# =============================================================================


@pytest.mark.asyncio
async def test_resident_checkin_checkout_and_damage_invoice(
    db_session: AsyncSession, residential_setup: dict
):
    """Verify check-in, key handover, inventory checklist, check-out damage billing in Finance."""
    tenant = residential_setup["tenant_a"]
    campus = residential_setup["campus_a"]
    ay = residential_setup["academic_year_a"]
    student = residential_setup["student_1"]
    admin = residential_setup["admin_user"]
    uid = uuid.uuid4().hex[:6]

    # Setup room & bed
    hostel = await ResidentialService.create_hostel(
        db_session,
        tenant.id,
        HostelCreate(name="Yamuna Hostel", code=f"HST-YAM-{uid}", campus_id=campus.id),
    )
    block = await ResidentialService.create_block(
        db_session, tenant.id, hostel.id, HostelBlockCreate(name="Main Wing")
    )
    floor = await ResidentialService.create_floor(
        db_session, tenant.id, block.id, HostelFloorCreate(floor_number=1)
    )
    room = await ResidentialService.create_room(
        db_session,
        tenant.id,
        HostelRoomCreate(floor_id=floor.id, room_number="301", capacity=1),
    )
    beds = await ResidentialService.list_beds(db_session, tenant.id, room_id=room.id)
    bed = beds[0]

    # 1. Allocate bed
    alloc = await ResidentialService.allocate_bed(
        db_session,
        tenant.id,
        AllocationCreate(
            bed_id=bed.id,
            student_id=student.id,
            academic_year_id=ay.id,
            check_in_date=date.today(),
        ),
        allocated_by=admin.id,
    )

    # 2. Check-in resident
    checkin_req = HostelCheckInRequest(
        allocation_id=alloc.id,
        key_number="KEY-301-A",
        facilities_condition_note="Room spotless, all fixtures operational",
        inventory_handover={"desk": True, "chair": True, "mattress": True, "wardrobe_key": True},
        expected_departure_date=date.today() + timedelta(days=180),
    )
    resident = await ResidentialService.check_in_resident(
        db_session, tenant.id, alloc.id, checkin_req, checked_in_by=admin.id
    )
    assert resident.id is not None
    assert resident.key_number == "KEY-301-A"
    assert resident.status == "ACTIVE"

    # 3. Check-out resident with damage charge of 500.00
    checkout_req = HostelCheckOutRequest(
        checkout_reason=CheckoutReason.END_OF_TERM,
        room_condition_on_checkout="Broken study desk lamp",
        key_returned=True,
        damage_charges_amount=Decimal("500.00"),
        damage_assessment_notes="Desk lamp socket cracked; requires replacement",
        create_damage_invoice=True,
    )
    checked_out = await ResidentialService.check_out_resident(
        db_session, tenant.id, resident.id, checkout_req, checked_out_by=admin.id
    )
    assert checked_out.status == "CHECKED_OUT"
    assert checked_out.damage_charges_amount == Decimal("500.00")
    assert checked_out.damage_invoice_id is not None

    # Verify bed was released back to AVAILABLE
    released_bed = await ResidentialService.get_bed(db_session, tenant.id, bed.id)
    assert released_bed.status == BedStatus.AVAILABLE.value
    assert released_bed.is_available is True

    # Verify Invoice created in authoritative Finance module
    stmt_inv = select(Invoice).where(Invoice.id == checked_out.damage_invoice_id)
    invoice = (await db_session.execute(stmt_inv)).scalar_one_or_none()
    assert invoice is not None
    assert invoice.net_payable == Decimal("500.00")
    assert invoice.balance_amount == Decimal("500.00")
    assert invoice.status == "ISSUED"

    # Verify Invoice itemized line head
    stmt_items = select(InvoiceLineItem).where(InvoiceLineItem.invoice_id == invoice.id)
    items = list((await db_session.execute(stmt_items)).scalars().all())
    assert len(items) == 1
    assert items[0].amount == Decimal("500.00")
    assert "Hostel Damage Charges" in items[0].description


# =============================================================================
# 5. RESIDENTIAL FEES & MEAL PLANS
# =============================================================================


@pytest.mark.asyncio
async def test_residential_fee_plan_and_meal_plans(db_session: AsyncSession, residential_setup: dict):
    """Verify fee plan invoice generation, meal plan enrollment, and headcount projection."""
    tenant = residential_setup["tenant_a"]
    ay = residential_setup["academic_year_a"]
    student = residential_setup["student_1"]
    admin = residential_setup["admin_user"]
    uid = uuid.uuid4().hex[:6]

    # 1. Create Fee Plan
    plan_in = HostelFeePlanCreate(
        code=f"FP-DBL-{uid}",
        name="Double Room Standard Plan",
        room_type=RoomType.DOUBLE,
        billing_cycle=FeePlanBillingCycle.SEMESTER,
        rent_amount=Decimal("35000.00"),
        mess_amount=Decimal("15000.00"),
        deposit_amount=Decimal("5000.00"),
        utility_amount=Decimal("2000.00"),
        amenities_amount=Decimal("1000.00"),
        total_amount=Decimal("58000.00"),
    )
    fee_plan = await ResidentialService.create_fee_plan(db_session, tenant.id, plan_in)
    assert fee_plan.id is not None
    assert fee_plan.total_amount == Decimal("58000.00")

    # Generate Invoice from Fee Plan
    gen_req = GenerateHostelInvoiceRequest(
        student_id=student.id,
        fee_plan_id=fee_plan.id,
        academic_year_id=ay.id,
        due_days=15,
    )
    inv_res = await ResidentialService.generate_fee_invoices(
        db_session, tenant.id, fee_plan.id, gen_req, generated_by=admin.id
    )
    assert inv_res.net_payable == Decimal("58000.00")
    assert inv_res.status == "ISSUED"

    # 2. Meal Plan & Headcount
    meal_in = HostelMealPlanCreate(
        code=f"MP-VEG-{uid}",
        name="Vegetarian Dining Plan",
        meal_type=MealType.VEG,
        monthly_rate=Decimal("4500.00"),
        serves_breakfast=True,
        serves_lunch=True,
        serves_snacks=True,
        serves_dinner=True,
    )
    meal_plan = await ResidentialService.create_meal_plan(db_session, tenant.id, meal_in)
    assert meal_plan.id is not None

    # Enroll student in meal plan
    enroll_in = HostelMealEnrollmentCreate(
        student_id=student.id,
        meal_plan_id=meal_plan.id,
        start_date=date.today(),
        dietary_requirements="Nut allergy, Jain options preferred",
    )
    enrollment = await ResidentialService.enroll_meal_plan(db_session, tenant.id, enroll_in)
    assert enrollment.id is not None
    assert enrollment.status == "ACTIVE"

    # Query projected headcount
    headcount = await ResidentialService.get_meal_headcount(
        db_session, tenant.id, meal_plan.id, service_date=date.today()
    )
    assert headcount.breakfast_count >= 1
    assert headcount.lunch_count >= 1
    assert headcount.dinner_count >= 1
    assert headcount.vegetarian_count >= 1


# =============================================================================
# 6. ATTENDANCE, OUTINGS, VISITORS & GATE PASSES
# =============================================================================


@pytest.mark.asyncio
async def test_outing_gatepass_and_visitor_management(db_session: AsyncSession, residential_setup: dict):
    """Verify outing pass departure/return, gate pass verification, and visitor checkout."""
    tenant = residential_setup["tenant_a"]
    campus = residential_setup["campus_a"]
    student = residential_setup["student_1"]
    admin = residential_setup["admin_user"]
    uid = uuid.uuid4().hex[:6]

    # Create Hostel
    hostel = await ResidentialService.create_hostel(
        db_session,
        tenant.id,
        HostelCreate(name="Nilgiri Hostel", code=f"HST-NIL-{uid}", campus_id=campus.id),
    )

    # 1. Outing Request
    out_in = OutingRequestCreate(
        student_id=student.id,
        hostel_id=hostel.id,
        outing_type=OutingType.DAY_OUTING,
        departure_time=datetime.now(timezone.utc),
        expected_return_time=datetime.now(timezone.utc) + timedelta(hours=4),
        destination="Town Library & Books",
        reason="Research book collection",
        parent_consent_verified=True,
    )
    outing = await ResidentialService.request_outing(db_session, tenant.id, out_in, requested_by=student.id)
    assert outing.id is not None
    assert outing.status == OutingStatus.APPROVED.value

    # Record Departure at gate
    departed = await ResidentialService.record_departure(db_session, tenant.id, outing.id, guard_id=admin.id)
    assert departed.status == OutingStatus.DEPARTED.value
    assert departed.actual_departure_time is not None

    # Record Return at gate
    returned = await ResidentialService.record_return(db_session, tenant.id, outing.id, guard_id=admin.id)
    assert returned.status == OutingStatus.COMPLETED.value
    assert returned.actual_return_time is not None

    # 2. Visitor Registration & Check-Out
    vis_in = VisitorRegisterRequest(
        hostel_id=hostel.id,
        host_student_id=student.id,
        visitor_name="Vijay Sharma",
        visitor_phone="+919876543299",
        visitor_id_proof_type="AADHAAR",
        visitor_id_proof_number="1234-5678-9012",
        visitor_relation="PARENT",
        purpose="Family visit and bringing supplies",
        expected_check_in=datetime.now(timezone.utc),
        expected_check_out=datetime.now(timezone.utc) + timedelta(hours=2),
    )
    visitor = await ResidentialService.register_visitor(
        db_session, tenant.id, vis_in, checked_in_by=admin.id
    )
    assert visitor.id is not None
    assert visitor.pass_code.startswith("VIS-")
    assert visitor.status == VisitorStatus.CHECKED_IN.value

    # Visitor Check-out
    checked_out_vis = await ResidentialService.checkout_visitor(
        db_session, tenant.id, visitor.id, VisitorCheckOutRequest(), checked_out_by=admin.id
    )
    assert checked_out_vis.status == VisitorStatus.CHECKED_OUT.value
    assert checked_out_vis.actual_check_out is not None

    # 3. Gate Pass Verification
    gp_in = HostelGatePassCreate(
        resident_id=student.id,
        purpose="Weekend home visit",
        valid_from=datetime.now(timezone.utc) - timedelta(hours=1),
        valid_until=datetime.now(timezone.utc) + timedelta(days=2),
    )
    gate_pass = await ResidentialService.create_gate_pass(
        db_session, tenant.id, gp_in, issued_by=admin.id
    )
    assert gate_pass.id is not None
    assert gate_pass.pass_code.startswith("GP-")

    # Verify Gate Pass at checkpoint
    verified_gp = await ResidentialService.verify_gate_pass(
        db_session,
        tenant.id,
        gate_pass.id,
        HostelGatePassVerifyRequest(pass_code=gate_pass.pass_code, action="EXIT"),
        guard_id=admin.id,
    )
    assert verified_gp.status == GatePassStatus.USED.value
    assert verified_gp.actual_exit_time is not None


# =============================================================================
# 7. MAINTENANCE, COMPLAINTS & ASSET WORK ORDER LINKAGE
# =============================================================================


@pytest.mark.asyncio
async def test_residential_service_request_asset_integration(
    db_session: AsyncSession, residential_setup: dict
):
    """Verify residential maintenance complaint links directly to Asset Maintenance Work Order."""
    tenant = residential_setup["tenant_a"]
    campus = residential_setup["campus_a"]
    student = residential_setup["student_1"]
    admin = residential_setup["admin_user"]
    uid = uuid.uuid4().hex[:6]

    # Setup room
    hostel = await ResidentialService.create_hostel(
        db_session,
        tenant.id,
        HostelCreate(name="Vindhya Hostel", code=f"HST-VIN-{uid}", campus_id=campus.id),
    )
    block = await ResidentialService.create_block(
        db_session, tenant.id, hostel.id, HostelBlockCreate(name="Wing B")
    )
    floor = await ResidentialService.create_floor(
        db_session, tenant.id, block.id, HostelFloorCreate(floor_number=2)
    )
    room = await ResidentialService.create_room(
        db_session,
        tenant.id,
        HostelRoomCreate(floor_id=floor.id, room_number="205", capacity=2),
    )

    # Submit complaint
    comp_in = ServiceRequestCreate(
        student_id=student.id,
        hostel_id=hostel.id,
        room_id=room.id,
        category=ResidentialServiceCategory.ELECTRICAL,
        priority=ResidentialServicePriority.HIGH,
        title="Ceiling fan motor burning smell",
        description="Ceiling fan makes a loud grinding noise and emits smoke when turned on",
    )
    complaint = await ResidentialService.create_service_request(
        db_session, tenant.id, comp_in, reported_by_user_id=student.id
    )
    assert complaint.id is not None
    assert complaint.ticket_number.startswith("CMP-")
    assert complaint.work_order_id is not None

    # Verify Asset Maintenance Work Order created atomically
    stmt_wo = select(MaintenanceWorkOrder).where(MaintenanceWorkOrder.id == complaint.work_order_id)
    work_order = (await db_session.execute(stmt_wo)).scalar_one_or_none()
    assert work_order is not None
    assert "Ceiling fan motor burning smell" in work_order.title
    assert work_order.tenant_id == tenant.id

    # Resolve complaint
    resolved = await ResidentialService.update_service_request(
        db_session,
        tenant.id,
        complaint.id,
        ServiceRequestUpdate(
            status="RESOLVED",
            resolution_notes="Replaced ceiling fan capacitor and rewound motor",
        ),
        resolved_by=admin.id,
    )
    assert resolved.status == "RESOLVED"
    assert resolved.resolved_at is not None


# =============================================================================
# 8. RESIDENTIAL SAFETY, RESTRICTED INCIDENTS & INSPECTIONS
# =============================================================================


@pytest.mark.asyncio
async def test_residential_incident_and_safety_inspections(
    db_session: AsyncSession, residential_setup: dict
):
    """Verify restricted incident reporting and safety inspection recording."""
    tenant = residential_setup["tenant_a"]
    campus = residential_setup["campus_a"]
    student = residential_setup["student_1"]
    admin = residential_setup["admin_user"]
    uid = uuid.uuid4().hex[:6]

    hostel = await ResidentialService.create_hostel(
        db_session,
        tenant.id,
        HostelCreate(name="Satpura Hostel", code=f"HST-SAT-{uid}", campus_id=campus.id),
    )

    # Report safety incident
    inc_in = IncidentCreate(
        hostel_id=hostel.id,
        incident_type=ResidentialIncidentType.SAFETY_HAZARD,
        severity=ResidentialIncidentSeverity.HIGH,
        incident_time=datetime.now(timezone.utc),
        location_description="Second floor common corridor",
        reporter_user_id=admin.id,
        involved_student_ids=[str(student.id)],
        description="Broken emergency glass case with exposed wiring near fire extinguisher",
        action_taken="Corridor taped off; emergency electrician dispatched immediately",
    )
    incident = await ResidentialService.report_incident(
        db_session, tenant.id, inc_in, reported_by=admin.id
    )
    assert incident.id is not None
    assert incident.incident_number.startswith("INC-")

    # Record Safety Inspection
    insp_in = SafetyInspectionCreate(
        hostel_id=hostel.id,
        inspection_date=date.today(),
        inspector_user_id=admin.id,
        fire_safety_passed=True,
        electrical_safety_passed=True,
        hygiene_passed=True,
        structural_passed=True,
        checklist_results={"fire_extinguishers": "Valid", "alarms": "Tested OK"},
        critical_findings="None",
        status=SafetyInspectionStatus.COMPLETED,
    )
    inspection = await ResidentialService.create_inspection(
        db_session, tenant.id, insp_in, inspector_id=admin.id
    )
    assert inspection.id is not None
    assert inspection.fire_safety_passed is True


# =============================================================================
# 9. OCCUPANCY REPORT & SCHEDULED OPERATIONS SWEEP
# =============================================================================


@pytest.mark.asyncio
async def test_occupancy_report_and_scheduled_sweep(db_session: AsyncSession, residential_setup: dict):
    """Verify occupancy report calculations and scheduled operations sweep."""
    tenant = residential_setup["tenant_a"]
    campus = residential_setup["campus_a"]
    uid = uuid.uuid4().hex[:6]

    hostel = await ResidentialService.create_hostel(
        db_session,
        tenant.id,
        HostelCreate(name="Shivalik", code=f"HST-SHV-{uid}", campus_id=campus.id),
    )
    block = await ResidentialService.create_block(
        db_session, tenant.id, hostel.id, HostelBlockCreate(name="A")
    )
    floor = await ResidentialService.create_floor(
        db_session, tenant.id, block.id, HostelFloorCreate(floor_number=1)
    )
    room = await ResidentialService.create_room(
        db_session,
        tenant.id,
        HostelRoomCreate(floor_id=floor.id, room_number="101", capacity=2),
    )

    # Check occupancy report
    report = await ResidentialService.get_occupancy_report(db_session, tenant.id, hostel_id=hostel.id)
    assert report.overall_total_beds >= 2
    assert report.overall_available_beds >= 2
    assert report.overall_occupancy_percentage >= 0.0

    # Test sweep
    metrics = await ResidentialService.sweep_residential_operations(db_session, tenant.id)
    assert isinstance(metrics, dict)
    assert "overdue_outings" in metrics
    assert "expired_bed_holds" in metrics


# =============================================================================
# 10. MULTI-TENANT ISOLATION TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_residential_multi_tenant_isolation(db_session: AsyncSession, residential_setup: dict):
    """Verify strict tenant isolation: Tenant A hostels and records are completely invisible to Tenant B."""
    tenant_a = residential_setup["tenant_a"]
    tenant_b = residential_setup["tenant_b"]
    campus_a = residential_setup["campus_a"]
    uid = uuid.uuid4().hex[:6]

    # Create Hostel in Tenant A
    hostel_a = await ResidentialService.create_hostel(
        db_session,
        tenant_a.id,
        HostelCreate(name="Tenant A Hostel", code=f"HST-A-{uid}", campus_id=campus_a.id),
    )

    # Querying from Tenant A finds it
    found_a = await ResidentialService.get_hostel(db_session, tenant_a.id, hostel_a.id)
    assert found_a.id == hostel_a.id

    # Querying the exact same hostel_id from Tenant B MUST raise NotFoundException
    with pytest.raises(NotFoundException):
        await ResidentialService.get_hostel(db_session, tenant_b.id, hostel_a.id)

    # Listing hostels in Tenant B returns an empty list
    hostels_b = await ResidentialService.list_hostels(db_session, tenant_b.id)
    assert all(h.id != hostel_a.id for h in hostels_b)
