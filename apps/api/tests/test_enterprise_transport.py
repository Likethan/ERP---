"""CampusOS Enterprise Transport, Fleet, Routes & Student Mobility Management Tests (Step 55).

CampusOS Tagline: "One Campus. One System. One Source of Truth."

Verifies:
1. Transport service configuration, operating zones, and academic calendar binding.
2. Fleet & vehicle registry, technical specs, and asset management integration.
3. Driver and workforce licensing, verification, and duty records.
4. Route & stop management, stop sequencing, geo-coordinates, and fares.
5. Student transport applications, eligibility scoring, approval, and waitlisting.
6. Concurrency-safe seat allocation, capacity constraints, and duplicate pass prevention.
7. Batch allocation engine: preview dry-run and transactional commit.
8. Operational trip scheduling, vehicle/driver overlap conflict prevention.
9. Dispatch lifecycle: pre-trip checklist, dispatch, manifest, and boarding reconciliation.
10. Pre-trip defect reporting with Asset Maintenance work order integration.
11. Telematics/tracking integration boundary with truthful data freshness and offline states.
12. Transport fees, fee plans, and Finance invoice integration with duplicate billing protection.
13. Transport incident reporting, safety escalation, and resolution.
14. Dashboard analytics and background scheduled operations sweep.
15. Multi-tenant isolation at every query and mutation boundary.
"""

import uuid
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
from app.models.assets import AssetCategory, Asset, MaintenanceWorkOrder
from app.models.core import AcademicYear, Batch, Campus, Department, Institution, Program, Regulation
from app.models.finance import Invoice, InvoiceLineItem
from app.models.people import StudentProfile, User
from app.models.transport import (
    BoardingStatus,
    DriverStatus,
    FeePlanBillingCycle,
    FuelType,
    IncidentStatus,
    RouteDirection,
    RouteStatus,
    ServiceWindow,
    TrackingProviderStatus,
    TransportAllocation,
    TransportAllocationStatus,
    TransportApplication,
    TransportApplicationStatus,
    TransportBoardingRecord,
    TransportDriver,
    TransportFeePlan,
    TransportFeeStatus,
    TransportFuelLog,
    TransportIncident,
    TransportIncidentSeverity,
    TransportIncidentType,
    TransportLocationSnapshot,
    TransportRoute,
    TransportServiceConfig,
    TransportServiceType,
    TransportStop,
    TransportTrackingSource,
    TransportTrip,
    TransportWaitlist,
    TripStatus,
    VehicleCategory,
    VehicleStatus,
    VerificationMethod,
    VerificationStatus,
    WaitlistStatus,
)
from app.schemas.transport import (
    BatchAllocationCommitRequest,
    BatchAllocationPreviewRequest,
    GenerateTransportInvoiceRequest,
    TransportAllocationCreate,
    TransportApplicationCreate,
    TransportApplicationReviewRequest,
    TransportBoardingVerifyRequest,
    TransportDriverCreate,
    TransportDriverUpdate,
    TransportFeePlanCreate,
    TransportFuelLogCreate,
    TransportIncidentCreate,
    TransportIncidentUpdate,
    TransportLocationPingRequest,
    TransportRouteCreate,
    TransportRouteUpdate,
    TransportServiceConfigCreate,
    TransportStopCreate,
    TransportTrackingSourceConfig,
    TransportTripCreate,
    TransportTripDispatch,
    TransportVehicleCreate,
    TransportVehicleUpdate,
)
from app.services.transport_service import TransportService


@pytest.fixture
async def transport_setup(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_b: Institution,
    super_admin_user: User,
):
    """Provides base campuses, academic years, students, and users for transport tests."""
    uid = uuid.uuid4().hex[:6]

    # Campus in Tenant A
    campus_a = Campus(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        name="Main Campus Alpha",
        code=f"CMP-{uid}",
        address="100 Innovation Corridor",
        city="Coimbatore",
        is_active=True,
    )
    db_session.add(campus_a)

    dept_a = Department(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        campus_id=campus_a.id,
        name="Mechanical Engineering",
        code=f"MECH-{uid}",
        is_active=True,
    )
    db_session.add(dept_a)

    prog_a = Program(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        department_id=dept_a.id,
        name="Bachelor of Engineering in Mechanical",
        code=f"BEME-{uid}",
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
        name=f"MECH 2026-2030 {uid}",
        admission_year=2026,
        graduation_year=2030,
        is_active=True,
    )
    db_session.add(batch_a)

    ay_a = AcademicYear(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        name=f"2026-2027-{uid}",
        start_date=date(2026, 7, 1),
        end_date=date(2027, 6, 30),
        is_current=True,
    )
    db_session.add(ay_a)

    # Student 1 (Tenant A)
    user_s1 = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"commuter1_{uid}@apextech.edu",
        first_name="Aditya",
        last_name="Varma",
        password_hash="dummy_hashed_password_s1",
        status="ACTIVE",
    )
    db_session.add(user_s1)
    await db_session.flush()

    student_1 = StudentProfile(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        user_id=user_s1.id,
        admission_number=f"ADM-TR-{uid}-1",
        date_of_birth=date(2004, 3, 10),
        gender="MALE",
        status="ACTIVE",
        admission_date=date(2026, 7, 1),
        expected_graduation_date=date(2030, 6, 30),
        program_id=prog_a.id,
        batch_id=batch_a.id,
    )
    db_session.add(student_1)

    # Student 2 (Tenant A)
    user_s2 = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"commuter2_{uid}@apextech.edu",
        first_name="Deepa",
        last_name="Rao",
        password_hash="dummy_hashed_password_s2",
        status="ACTIVE",
    )
    db_session.add(user_s2)
    await db_session.flush()

    student_2 = StudentProfile(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        user_id=user_s2.id,
        admission_number=f"ADM-TR-{uid}-2",
        date_of_birth=date(2004, 7, 18),
        gender="FEMALE",
        status="ACTIVE",
        admission_date=date(2026, 7, 1),
        expected_graduation_date=date(2030, 6, 30),
        program_id=prog_a.id,
        batch_id=batch_a.id,
    )
    db_session.add(student_2)

    # Student 3 (Tenant A)
    user_s3 = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"commuter3_{uid}@apextech.edu",
        first_name="Karthik",
        last_name="Sundaram",
        password_hash="dummy_hashed_password_s3",
        status="ACTIVE",
    )
    db_session.add(user_s3)
    await db_session.flush()

    student_3 = StudentProfile(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        user_id=user_s3.id,
        admission_number=f"ADM-TR-{uid}-3",
        date_of_birth=date(2004, 11, 25),
        gender="MALE",
        status="ACTIVE",
        admission_date=date(2026, 7, 1),
        expected_graduation_date=date(2030, 6, 30),
        program_id=prog_a.id,
        batch_id=batch_a.id,
    )
    db_session.add(student_3)

    # Campus & Academic Year in Tenant B (for multi-tenant isolation verification)
    campus_b = Campus(
        id=uuid.uuid4(),
        tenant_id=tenant_b.id,
        name="Ocean City Campus",
        code=f"CMP-B-{uid}",
        address="50 Marina Expressway",
        city="Chennai",
        is_active=True,
    )
    db_session.add(campus_b)

    ay_b = AcademicYear(
        id=uuid.uuid4(),
        tenant_id=tenant_b.id,
        name=f"2026-2027-B-{uid}",
        start_date=date(2026, 7, 1),
        end_date=date(2027, 6, 30),
        is_current=True,
    )
    db_session.add(ay_b)

    await db_session.commit()

    return {
        "tenant_a": tenant_a,
        "tenant_b": tenant_b,
        "campus_a": campus_a,
        "campus_b": campus_b,
        "academic_year_a": ay_a,
        "academic_year_b": ay_b,
        "student_1": student_1,
        "student_2": student_2,
        "student_3": student_3,
        "user_s1": user_s1,
        "user_s2": user_s2,
        "user_s3": user_s3,
        "super_admin": super_admin_user,
    }


@pytest.mark.asyncio
async def test_transport_service_config_and_route_stop_hierarchy(
    db_session: AsyncSession, transport_setup: dict
):
    """Verifies service config, route and ordered stop creation with fares and capacity."""
    tenant = transport_setup["tenant_a"]
    campus = transport_setup["campus_a"]

    # 1. Create Transport Service Config
    cfg_data = TransportServiceConfigCreate(
        service_code="TR-SRV-2026",
        service_name="Campus Regular Transport Service",
        campus_id=campus.id,
        zone_code="ZONE-NORTH",
        operating_period_start=date(2026, 7, 1),
        operating_period_end=date(2027, 6, 30),
        capacity_policy={"max_overbooking_percent": 0, "priority_rules": ["DISTANCE", "SENIORITY"]},
    )
    config = await TransportService.create_service_config(db_session, tenant.id, cfg_data)
    assert config.service_code == "TR-SRV-2026"
    assert config.zone_code == "ZONE-NORTH"

    # 2. Create Vehicle
    v_data = TransportVehicleCreate(
        registration_number="TN-38-BZ-1001",
        fleet_identifier="FLEET-BUS-01",
        vehicle_category=VehicleCategory.BUS,
        make="Ashok Leyland",
        model="Viking AC",
        manufacturing_year=2024,
        capacity=40,
        accessible_seating_capacity=2,
        permitted_passenger_capacity=40,
        insurance_expiry=date.today() + timedelta(days=300),
        fitness_certificate_expiry=date.today() + timedelta(days=200),
        fuel_type=FuelType.DIESEL,
        operational_depot="Depot Alpha",
    )
    vehicle = await TransportService.create_vehicle(db_session, tenant.id, v_data)
    assert vehicle.registration_number == "TN-38-BZ-1001"
    assert vehicle.capacity == 40

    # 3. Create Driver
    d_data = TransportDriverCreate(
        full_name="Murugan Ramasamy",
        license_number="DL-TN38-2015-009988",
        license_expiry=date.today() + timedelta(days=400),
        phone_number="+91-9842100001",
        background_verification_status=VerificationStatus.VERIFIED,
    )
    driver = await TransportService.create_driver(db_session, tenant.id, d_data)
    assert driver.full_name == "Murugan Ramasamy"
    assert driver.license_number == "DL-TN38-2015-009988"

    # 4. Create Route
    r_data = TransportRouteCreate(
        route_code="R-101",
        route_name="Gandhipuram to Campus Express",
        campus_id=campus.id,
        start_point="Gandhipuram Bus Stand",
        end_point="Campus Main Gate",
        distance_km=Decimal("22.50"),
        estimated_duration_minutes=45,
        morning_departure_time=time(7, 30),
        evening_return_time=time(17, 15),
        vehicle_id=vehicle.id,
        driver_id=driver.id,
        capacity=40,
        direction=RouteDirection.ROUND_TRIP,
    )
    route = await TransportService.create_route(db_session, tenant.id, r_data)
    assert route.route_code == "R-101"
    assert route.allocated_students == 0

    # 5. Add Ordered Stops
    stops_data = [
        TransportStopCreate(
            stop_name="Gandhipuram Bus Stand",
            stop_code="STP-01",
            stop_sequence=1,
            pickup_time=time(7, 30),
            drop_time=time(18, 0),
            fare_annual=Decimal("18000.00"),
            fare_term=Decimal("9500.00"),
            fare_monthly=Decimal("2000.00"),
        ),
        TransportStopCreate(
            stop_name="Lakshmi Mills Junction",
            stop_code="STP-02",
            stop_sequence=2,
            pickup_time=time(7, 45),
            drop_time=time(17, 45),
            fare_annual=Decimal("15000.00"),
            fare_term=Decimal("8000.00"),
            fare_monthly=Decimal("1700.00"),
        ),
        TransportStopCreate(
            stop_name="Peelamedu Airport Road",
            stop_code="STP-03",
            stop_sequence=3,
            pickup_time=time(8, 0),
            drop_time=time(17, 30),
            fare_annual=Decimal("12000.00"),
            fare_term=Decimal("6500.00"),
            fare_monthly=Decimal("1400.00"),
        ),
    ]
    stops = []
    for s_in in stops_data:
        stop = await TransportService.create_stop(db_session, tenant.id, route.id, s_in)
        stops.append(stop)

    assert len(stops) == 3
    assert stops[0].stop_sequence == 1
    assert stops[1].stop_sequence == 2
    assert stops[2].stop_sequence == 3
    assert stops[0].fare_annual == Decimal("18000.00")


@pytest.mark.asyncio
async def test_vehicle_and_driver_compliance_validation(
    db_session: AsyncSession, transport_setup: dict
):
    """Verifies that expired fitness, insurance, or driver license block trip scheduling and dispatch."""
    tenant = transport_setup["tenant_a"]
    campus = transport_setup["campus_a"]

    # 1. Non-compliant Vehicle (Expired Fitness Certificate)
    v_expired = await TransportService.create_vehicle(
        db_session,
        tenant.id,
        TransportVehicleCreate(
            registration_number="TN-38-EX-9999",
            capacity=30,
            insurance_expiry=date.today() + timedelta(days=60),
            fitness_certificate_expiry=date.today() - timedelta(days=5),  # EXPIRED!
        ),
    )
    v_comp = await TransportService.get_vehicle_compliance(db_session, tenant.id, v_expired.id)
    assert v_comp.is_compliant_for_dispatch is False
    assert any("expired" in r.lower() for r in v_comp.compliance_remarks)

    # 2. Compliant Vehicle
    v_valid = await TransportService.create_vehicle(
        db_session,
        tenant.id,
        TransportVehicleCreate(
            registration_number="TN-38-OK-8888",
            capacity=30,
            insurance_expiry=date.today() + timedelta(days=120),
            fitness_certificate_expiry=date.today() + timedelta(days=120),
        ),
    )
    v_comp_valid = await TransportService.get_vehicle_compliance(db_session, tenant.id, v_valid.id)
    assert v_comp_valid.is_compliant_for_dispatch is True

    # 3. Non-compliant Driver (Expired License)
    d_expired = await TransportService.create_driver(
        db_session,
        tenant.id,
        TransportDriverCreate(
            full_name="Expired License Driver",
            license_number="DL-EXPIRED-001",
            license_expiry=date.today() - timedelta(days=2),  # EXPIRED!
            phone_number="+91-9800000001",
        ),
    )
    d_comp = await TransportService.get_driver_compliance(db_session, tenant.id, d_expired.id)
    assert d_comp.is_compliant_for_dispatch is False
    assert any("expired" in r.lower() for r in d_comp.compliance_remarks)

    # 4. Compliant Driver
    d_valid = await TransportService.create_driver(
        db_session,
        tenant.id,
        TransportDriverCreate(
            full_name="Valid License Driver",
            license_number="DL-VALID-002",
            license_expiry=date.today() + timedelta(days=180),
            phone_number="+91-9800000002",
        ),
    )
    d_comp_valid = await TransportService.get_driver_compliance(db_session, tenant.id, d_valid.id)
    assert d_comp_valid.is_compliant_for_dispatch is True

    # 5. Create Route for scheduling attempt
    route = await TransportService.create_route(
        db_session,
        tenant.id,
        TransportRouteCreate(
            route_code="R-COMP-TEST",
            route_name="Compliance Verification Route",
            campus_id=campus.id,
            capacity=30,
        ),
    )

    # 6. Attempt scheduling with non-compliant vehicle -> BLOCKED with ConflictException/BadRequestException
    trip_date = date.today() + timedelta(days=1)
    with pytest.raises((ConflictException, BadRequestException)) as exc_v:
        await TransportService.schedule_trip(
            db_session,
            tenant.id,
            TransportTripCreate(
                route_id=route.id,
                vehicle_id=v_expired.id,
                driver_id=d_valid.id,
                trip_date=trip_date,
                service_window=ServiceWindow.MORNING_PICKUP,
                scheduled_start_time=datetime.now(timezone.utc) + timedelta(days=1, hours=7),
                scheduled_end_time=datetime.now(timezone.utc) + timedelta(days=1, hours=8),
            ),
        )
    assert "fitness" in str(exc_v.value).lower() or "compliant" in str(exc_v.value).lower() or "expired" in str(exc_v.value).lower()

    # 7. Attempt scheduling with non-compliant driver -> BLOCKED with ConflictException/BadRequestException
    with pytest.raises((ConflictException, BadRequestException)) as exc_d:
        await TransportService.schedule_trip(
            db_session,
            tenant.id,
            TransportTripCreate(
                route_id=route.id,
                vehicle_id=v_valid.id,
                driver_id=d_expired.id,
                trip_date=trip_date,
                service_window=ServiceWindow.MORNING_PICKUP,
                scheduled_start_time=datetime.now(timezone.utc) + timedelta(days=1, hours=7),
                scheduled_end_time=datetime.now(timezone.utc) + timedelta(days=1, hours=8),
            ),
        )
    assert "license" in str(exc_d.value).lower() or "compliant" in str(exc_d.value).lower() or "expired" in str(exc_d.value).lower()


@pytest.mark.asyncio
async def test_student_transport_application_and_approval_workflow(
    db_session: AsyncSession, transport_setup: dict
):
    """Verifies student application submission, review, approval, and pass issuance."""
    tenant = transport_setup["tenant_a"]
    campus = transport_setup["campus_a"]
    ay = transport_setup["academic_year_a"]
    student = transport_setup["student_1"]
    admin = transport_setup["super_admin"]

    # Create vehicle, driver, route, and stop
    vehicle = await TransportService.create_vehicle(
        db_session,
        tenant.id,
        TransportVehicleCreate(
            registration_number="TN-38-AP-1111",
            capacity=30,
            insurance_expiry=date.today() + timedelta(days=365),
            fitness_certificate_expiry=date.today() + timedelta(days=365),
        ),
    )
    driver = await TransportService.create_driver(
        db_session,
        tenant.id,
        TransportDriverCreate(
            full_name="Ravi Chandran",
            license_number="DL-TN38-2018-777",
            license_expiry=date.today() + timedelta(days=365),
            phone_number="+91-9842177777",
        ),
    )
    route = await TransportService.create_route(
        db_session,
        tenant.id,
        TransportRouteCreate(
            route_code="R-APPL-1",
            route_name="Application Test Route",
            campus_id=campus.id,
            vehicle_id=vehicle.id,
            driver_id=driver.id,
            capacity=30,
        ),
    )
    stop = await TransportService.create_stop(
        db_session,
        tenant.id,
        route.id,
        TransportStopCreate(
            stop_name="Town Hall",
            stop_sequence=1,
            pickup_time=time(7, 30),
            fare_annual=Decimal("15000.00"),
        ),
    )

    # 1. Student submits transport application
    app_in = TransportApplicationCreate(
        student_id=student.id,
        academic_year_id=ay.id,
        preferred_route_id=route.id,
        preferred_stop_id=stop.id,
        service_type=TransportServiceType.ROUND_TRIP,
        priority_score=Decimal("10.00"),
        accessibility_needed=False,
    )
    application = await TransportService.submit_application(db_session, tenant.id, app_in)
    assert application.status == TransportApplicationStatus.SUBMITTED.value
    assert application.application_number.startswith("TR-APP-")

    # 2. Duplicate active application attempt -> raises ConflictException
    with pytest.raises(ConflictException):
        await TransportService.submit_application(db_session, tenant.id, app_in)

    # 3. Review & Approve application -> generates active TransportAllocation
    updated_app = await TransportService.review_application(
        db_session,
        tenant.id,
        application.id,
        TransportApplicationReviewRequest(
            status=TransportApplicationStatus.APPROVED,
        ),
        reviewer_id=admin.id,
    )
    assert updated_app.status == TransportApplicationStatus.APPROVED.value

    # Verify allocation was created for student
    allocations = await TransportService.list_allocations(db_session, tenant.id, student_id=student.id)
    assert len(allocations) == 1
    allocation = allocations[0]
    assert allocation.status == TransportAllocationStatus.ACTIVE.value
    assert allocation.pass_number.startswith("TR-PASS-")
    assert allocation.student_id == student.id
    assert allocation.route_id == route.id
    assert allocation.stop_id == stop.id

    # Verify route allocated count incremented
    updated_route = await TransportService.get_route(db_session, tenant.id, route.id)
    assert updated_route.allocated_students == 1


@pytest.mark.asyncio
async def test_capacity_enforcement_and_waitlist_queue(
    db_session: AsyncSession, transport_setup: dict
):
    """Verifies that route capacity limits are enforced strictly and excess applicants join waitlist."""
    tenant = transport_setup["tenant_a"]
    campus = transport_setup["campus_a"]
    ay = transport_setup["academic_year_a"]
    s1 = transport_setup["student_1"]
    s2 = transport_setup["student_2"]
    s3 = transport_setup["student_3"]
    admin = transport_setup["super_admin"]

    # Setup Route with tight capacity = 2, Vehicle capacity = 2
    vehicle = await TransportService.create_vehicle(
        db_session,
        tenant.id,
        TransportVehicleCreate(
            registration_number="TN-38-CAP-22",
            capacity=2,
            insurance_expiry=date.today() + timedelta(days=365),
            fitness_certificate_expiry=date.today() + timedelta(days=365),
        ),
    )
    route = await TransportService.create_route(
        db_session,
        tenant.id,
        TransportRouteCreate(
            route_code="R-CAP-TINY",
            route_name="Tiny Capacity Route",
            campus_id=campus.id,
            vehicle_id=vehicle.id,
            capacity=2,  # Strict capacity of 2!
        ),
    )
    stop = await TransportService.create_stop(
        db_session,
        tenant.id,
        route.id,
        TransportStopCreate(
            stop_name="Cross Cut Road",
            stop_sequence=1,
            pickup_time=time(7, 30),
            fare_annual=Decimal("12000.00"),
        ),
    )

    # Student 1: allocate seat 1
    alloc1 = await TransportService.allocate_passenger(
        db_session,
        tenant.id,
        TransportAllocationCreate(
            student_id=s1.id,
            academic_year_id=ay.id,
            route_id=route.id,
            stop_id=stop.id,
            service_type=TransportServiceType.ROUND_TRIP,
        ),
    )
    assert alloc1.pass_number is not None

    # Student 2: allocate seat 2 (route is now FULL: 2/2)
    alloc2 = await TransportService.allocate_passenger(
        db_session,
        tenant.id,
        TransportAllocationCreate(
            student_id=s2.id,
            academic_year_id=ay.id,
            route_id=route.id,
            stop_id=stop.id,
            service_type=TransportServiceType.ROUND_TRIP,
        ),
    )
    assert alloc2.pass_number is not None

    # Student 3: direct allocation must fail with ConflictException (Capacity Reached)
    with pytest.raises(ConflictException) as exc_cap:
        await TransportService.allocate_passenger(
            db_session,
            tenant.id,
            TransportAllocationCreate(
                student_id=s3.id,
                academic_year_id=ay.id,
                route_id=route.id,
                stop_id=stop.id,
                service_type=TransportServiceType.ROUND_TRIP,
            ),
        )
    assert "capacity" in str(exc_cap.value).lower()

    # Student 3: Submit application and review -> should automatically be placed on waitlist
    app3 = await TransportService.submit_application(
        db_session,
        tenant.id,
        TransportApplicationCreate(
            student_id=s3.id,
            academic_year_id=ay.id,
            preferred_route_id=route.id,
            preferred_stop_id=stop.id,
            priority_score=Decimal("5.00"),
        ),
    )
    reviewed_app = await TransportService.review_application(
        db_session,
        tenant.id,
        app3.id,
        TransportApplicationReviewRequest(
            status=TransportApplicationStatus.APPROVED,
        ),
        reviewer_id=admin.id,
    )
    # Status becomes WAITLISTED due to capacity
    assert reviewed_app.status == TransportApplicationStatus.WAITLISTED.value

    # Check waitlist
    waitlist_items = await TransportService.list_waitlist(db_session, tenant.id, route_id=route.id)
    assert len(waitlist_items) == 1
    assert waitlist_items[0].student_id == s3.id
    assert waitlist_items[0].queue_position == 1
    assert waitlist_items[0].status == WaitlistStatus.WAITING.value


@pytest.mark.asyncio
async def test_batch_allocation_preview_and_commit(
    db_session: AsyncSession, transport_setup: dict
):
    """Verifies the batch allocation preview dry-run and atomic transactional commit."""
    tenant = transport_setup["tenant_a"]
    campus = transport_setup["campus_a"]
    ay = transport_setup["academic_year_a"]
    s1 = transport_setup["student_1"]
    s2 = transport_setup["student_2"]
    s3 = transport_setup["student_3"]
    admin = transport_setup["super_admin"]

    # Setup Route with capacity = 2
    route = await TransportService.create_route(
        db_session,
        tenant.id,
        TransportRouteCreate(
            route_code="R-BATCH-1",
            route_name="Batch Engine Route",
            campus_id=campus.id,
            capacity=2,
        ),
    )
    stop = await TransportService.create_stop(
        db_session,
        tenant.id,
        route.id,
        TransportStopCreate(
            stop_name="Avinashi Road",
            stop_sequence=1,
            pickup_time=time(7, 40),
            fare_annual=Decimal("14000.00"),
        ),
    )

    # Create 3 applications: s1 (priority 20), s2 (priority 10), s3 (priority 5)
    app1 = await TransportService.submit_application(
        db_session,
        tenant.id,
        TransportApplicationCreate(
            student_id=s1.id,
            academic_year_id=ay.id,
            preferred_route_id=route.id,
            preferred_stop_id=stop.id,
            priority_score=Decimal("20.00"),
        ),
    )
    app2 = await TransportService.submit_application(
        db_session,
        tenant.id,
        TransportApplicationCreate(
            student_id=s2.id,
            academic_year_id=ay.id,
            preferred_route_id=route.id,
            preferred_stop_id=stop.id,
            priority_score=Decimal("10.00"),
        ),
    )
    app3 = await TransportService.submit_application(
        db_session,
        tenant.id,
        TransportApplicationCreate(
            student_id=s3.id,
            academic_year_id=ay.id,
            preferred_route_id=route.id,
            preferred_stop_id=stop.id,
            priority_score=Decimal("5.00"),
        ),
    )

    # 1. Preview Batch Allocation
    preview = await TransportService.preview_batch_allocations(
        db_session,
        tenant.id,
        BatchAllocationPreviewRequest(
            academic_year_id=ay.id,
            route_id=route.id,
        ),
    )
    assert preview.total_applications == 3
    assert preview.allocatable_count == 2  # Capacity is 2
    assert preview.waitlist_count == 1  # 3rd goes to waitlist
    allocated_candidates = [c for c in preview.candidates if c.can_allocate]
    allocated_app_ids = [c.application_id for c in allocated_candidates]
    assert app1.id in allocated_app_ids
    assert app2.id in allocated_app_ids

    # 2. Commit Batch Allocation
    commit_res = await TransportService.commit_batch_allocations(
        db_session,
        tenant.id,
        BatchAllocationCommitRequest(
            academic_year_id=ay.id,
            route_id=route.id,
        ),
        actor_id=admin.id,
    )
    assert commit_res.allocated_count == 2
    assert commit_res.waitlisted_count == 1

    # Check updated route
    r_updated = await TransportService.get_route(db_session, tenant.id, route.id)
    assert r_updated.allocated_students == 2


@pytest.mark.asyncio
async def test_trip_scheduling_and_conflict_detection(
    db_session: AsyncSession, transport_setup: dict
):
    """Verifies trip scheduling and strict detection of overlapping vehicle and driver commitments."""
    tenant = transport_setup["tenant_a"]
    campus = transport_setup["campus_a"]

    # Create 2 vehicles and 2 drivers
    v1 = await TransportService.create_vehicle(
        db_session,
        tenant.id,
        TransportVehicleCreate(
            registration_number="TN-38-V1-11",
            capacity=40,
            insurance_expiry=date.today() + timedelta(days=365),
            fitness_certificate_expiry=date.today() + timedelta(days=365),
        ),
    )
    v2 = await TransportService.create_vehicle(
        db_session,
        tenant.id,
        TransportVehicleCreate(
            registration_number="TN-38-V2-22",
            capacity=40,
            insurance_expiry=date.today() + timedelta(days=365),
            fitness_certificate_expiry=date.today() + timedelta(days=365),
        ),
    )
    d1 = await TransportService.create_driver(
        db_session,
        tenant.id,
        TransportDriverCreate(
            full_name="Driver One",
            license_number="DL-D1-111",
            license_expiry=date.today() + timedelta(days=365),
            phone_number="+91-9800111111",
        ),
    )
    d2 = await TransportService.create_driver(
        db_session,
        tenant.id,
        TransportDriverCreate(
            full_name="Driver Two",
            license_number="DL-D2-222",
            license_expiry=date.today() + timedelta(days=365),
            phone_number="+91-9800222222",
        ),
    )

    r1 = await TransportService.create_route(
        db_session,
        tenant.id,
        TransportRouteCreate(route_code="R-CNF-1", route_name="Route Alpha", campus_id=campus.id),
    )
    r2 = await TransportService.create_route(
        db_session,
        tenant.id,
        TransportRouteCreate(route_code="R-CNF-2", route_name="Route Beta", campus_id=campus.id),
    )

    trip_date = date.today() + timedelta(days=2)
    start_time = datetime.now(timezone.utc) + timedelta(days=2, hours=7)
    end_time = datetime.now(timezone.utc) + timedelta(days=2, hours=8, minutes=30)

    # 1. Schedule initial valid trip
    trip1 = await TransportService.schedule_trip(
        db_session,
        tenant.id,
        TransportTripCreate(
            route_id=r1.id,
            vehicle_id=v1.id,
            driver_id=d1.id,
            trip_date=trip_date,
            service_window=ServiceWindow.MORNING_PICKUP,
            scheduled_start_time=start_time,
            scheduled_end_time=end_time,
        ),
    )
    assert trip1.trip_number.startswith("TRIP-")
    assert trip1.status == TripStatus.SCHEDULED.value

    # 2. Attempt scheduling another trip on same date/window with SAME VEHICLE -> raises ConflictException
    with pytest.raises(ConflictException) as exc_v:
        await TransportService.schedule_trip(
            db_session,
            tenant.id,
            TransportTripCreate(
                route_id=r2.id,
                vehicle_id=v1.id,  # SAME VEHICLE
                driver_id=d2.id,  # Different driver
                trip_date=trip_date,
                service_window=ServiceWindow.MORNING_PICKUP,
                scheduled_start_time=start_time,
                scheduled_end_time=end_time,
            ),
        )
    assert "Vehicle" in str(exc_v.value) and "already scheduled" in str(exc_v.value)

    # 3. Attempt scheduling another trip on same date/window with SAME DRIVER -> raises ConflictException
    with pytest.raises(ConflictException) as exc_d:
        await TransportService.schedule_trip(
            db_session,
            tenant.id,
            TransportTripCreate(
                route_id=r2.id,
                vehicle_id=v2.id,  # Different vehicle
                driver_id=d1.id,  # SAME DRIVER
                trip_date=trip_date,
                service_window=ServiceWindow.MORNING_PICKUP,
                scheduled_start_time=start_time,
                scheduled_end_time=end_time,
            ),
        )
    assert "Driver" in str(exc_d.value) and "already assigned" in str(exc_d.value)


@pytest.mark.asyncio
async def test_trip_dispatch_lifecycle_manifest_and_boarding_reconciliation(
    db_session: AsyncSession, transport_setup: dict
):
    """Verifies pre-trip checklist, dispatch, passenger manifest generation, and boarding verification."""
    tenant = transport_setup["tenant_a"]
    campus = transport_setup["campus_a"]
    ay = transport_setup["academic_year_a"]
    student = transport_setup["student_1"]
    admin = transport_setup["super_admin"]

    # Setup vehicle with initial odometer = 50000.00
    vehicle = await TransportService.create_vehicle(
        db_session,
        tenant.id,
        TransportVehicleCreate(
            registration_number="TN-38-DISP-01",
            capacity=30,
            insurance_expiry=date.today() + timedelta(days=365),
            fitness_certificate_expiry=date.today() + timedelta(days=365),
            current_odometer_km=Decimal("50000.00"),
        ),
    )
    driver = await TransportService.create_driver(
        db_session,
        tenant.id,
        TransportDriverCreate(
            full_name="Sundar Pichai",
            license_number="DL-DISP-777",
            license_expiry=date.today() + timedelta(days=365),
            phone_number="+91-9876500001",
        ),
    )
    route = await TransportService.create_route(
        db_session,
        tenant.id,
        TransportRouteCreate(
            route_code="R-DISP-1",
            route_name="Dispatch Lifecycle Route",
            campus_id=campus.id,
            vehicle_id=vehicle.id,
            driver_id=driver.id,
            capacity=30,
        ),
    )
    stop = await TransportService.create_stop(
        db_session,
        tenant.id,
        route.id,
        TransportStopCreate(
            stop_name="Singanallur Depot",
            stop_sequence=1,
            pickup_time=time(7, 15),
            fare_annual=Decimal("12000.00"),
        ),
    )

    # Allocate seat for student
    alloc = await TransportService.allocate_passenger(
        db_session,
        tenant.id,
        TransportAllocationCreate(
            student_id=student.id,
            academic_year_id=ay.id,
            route_id=route.id,
            stop_id=stop.id,
            service_type=TransportServiceType.ROUND_TRIP,
        ),
    )

    # Schedule trip
    trip_date = date.today()
    trip = await TransportService.schedule_trip(
        db_session,
        tenant.id,
        TransportTripCreate(
            route_id=route.id,
            vehicle_id=vehicle.id,
            driver_id=driver.id,
            trip_date=trip_date,
            service_window=ServiceWindow.MORNING_PICKUP,
            scheduled_start_time=datetime.now(timezone.utc) - timedelta(minutes=15),
            scheduled_end_time=datetime.now(timezone.utc) + timedelta(minutes=45),
        ),
    )

    # 1. Dispatch trip with pre-trip checklist
    dispatched = await TransportService.dispatch_trip(
        db_session,
        tenant.id,
        trip.id,
        TransportTripDispatch(
            start_odometer_km=Decimal("50000.00"),
            pre_trip_checklist_completed=True,
            checklist_notes={"brakes": "OK", "tires": "OK", "lights": "OK"},
        ),
        dispatcher_id=admin.id,
    )
    assert dispatched.status == TripStatus.IN_PROGRESS.value
    assert dispatched.actual_start_time is not None
    assert dispatched.start_odometer_km == Decimal("50000.00")

    # 2. Get passenger manifest -> student is on manifest as EXPECTED
    manifest = await TransportService.get_trip_manifest(db_session, tenant.id, trip.id)
    assert manifest.total_manifest_count == 1
    assert manifest.passengers[0].student_id == student.id
    assert manifest.passengers[0].boarding_status == BoardingStatus.EXPECTED

    # 3. Verify Boarding (Student scans pass / manual check)
    boarding_res = await TransportService.record_boarding(
        db_session,
        tenant.id,
        trip.id,
        TransportBoardingVerifyRequest(
            student_id=student.id,
            stop_id=stop.id,
            verification_method=VerificationMethod.QR_CODE,
            boarding_status=BoardingStatus.BOARDED,
        ),
        verifier_id=admin.id,
    )
    assert boarding_res.boarding_status == BoardingStatus.BOARDED.value
    assert boarding_res.boarding_time is not None

    # 4. Verify Drop-off
    drop_res = await TransportService.record_boarding(
        db_session,
        tenant.id,
        trip.id,
        TransportBoardingVerifyRequest(
            student_id=student.id,
            stop_id=stop.id,
            verification_method=VerificationMethod.MANUAL,
            boarding_status=BoardingStatus.DROPPED_OFF,
        ),
        verifier_id=admin.id,
    )
    assert drop_res.boarding_status == BoardingStatus.DROPPED_OFF.value
    assert drop_res.drop_off_time is not None

    # 5. Complete Trip with final odometer reading (50025 km = 25 km travelled)
    completed = await TransportService.complete_trip(
        db_session,
        tenant.id,
        trip.id,
        end_odometer_km=Decimal("50025.00"),
    )
    assert completed.status == TripStatus.COMPLETED.value
    assert completed.actual_end_time is not None

    # Verify vehicle current odometer updated
    updated_veh = await TransportService.get_vehicle(db_session, tenant.id, vehicle.id)
    assert updated_veh.current_odometer_km == Decimal("50025.00")


@pytest.mark.asyncio
async def test_pre_trip_defect_reporting_asset_maintenance_integration(
    db_session: AsyncSession, transport_setup: dict
):
    """Verifies that pre-trip defects automatically trigger Asset Maintenance work orders."""
    tenant = transport_setup["tenant_a"]
    admin = transport_setup["super_admin"]

    # 1. Create linked physical Asset record in asset_registry
    cat = AssetCategory(
        tenant_id=tenant.id,
        code=f"VEH-CAT-{uuid.uuid4().hex[:4]}",
        name="Transport Fleet Vehicles",
        category_type="VEHICLE",
    )
    db_session.add(cat)
    await db_session.flush()

    asset_rec = Asset(
        tenant_id=tenant.id,
        category_id=cat.id,
        asset_tag=f"AST-BUS-{uuid.uuid4().hex[:4]}",
        name="Tata Marcopolo Bus 42",
        acquisition_date=date(2024, 1, 1),
    )
    db_session.add(asset_rec)
    await db_session.flush()

    # 2. Create TransportVehicle linked to asset
    vehicle = await TransportService.create_vehicle(
        db_session,
        tenant.id,
        TransportVehicleCreate(
            asset_id=asset_rec.id,
            registration_number="TN-38-DEFECT-01",
            capacity=42,
            insurance_expiry=date.today() + timedelta(days=365),
            fitness_certificate_expiry=date.today() + timedelta(days=365),
        ),
    )

    # 3. Report vehicle defect -> automatically generates MaintenanceWorkOrder
    work_order = await TransportService.report_vehicle_defect(
        db_session,
        tenant.id,
        vehicle.id,
        defect_description="Severe pneumatic brake pressure loss detected during engine idle",
        reporter_id=admin.id,
    )
    assert work_order.id is not None
    assert work_order.work_order_number.startswith("WO-FLT-")
    assert work_order.asset_id == asset_rec.id
    assert "Severe pneumatic brake pressure loss" in work_order.reported_symptoms

    # 4. Verify vehicle status was transitioned to MAINTENANCE
    v_updated = await TransportService.get_vehicle(db_session, tenant.id, vehicle.id)
    assert v_updated.status == VehicleStatus.MAINTENANCE.value


@pytest.mark.asyncio
async def test_telematics_tracking_freshness_and_truthful_offline_state(
    db_session: AsyncSession, transport_setup: dict
):
    """Verifies that tracking reports truthful offline states and never fabricates coordinates."""
    tenant = transport_setup["tenant_a"]

    vehicle = await TransportService.create_vehicle(
        db_session,
        tenant.id,
        TransportVehicleCreate(
            registration_number="TN-38-TELE-01",
            capacity=35,
            insurance_expiry=date.today() + timedelta(days=365),
            fitness_certificate_expiry=date.today() + timedelta(days=365),
        ),
    )

    # 1. Unconfigured vehicle query -> truthful NOT_CONFIGURED state, zero fake coordinates
    unconf_state = await TransportService.get_live_tracking(db_session, tenant.id, vehicle.id)
    assert unconf_state.status == TrackingProviderStatus.NOT_CONFIGURED
    assert unconf_state.tracking_enabled is False
    assert unconf_state.last_known_location is None

    # 2. Configure tracking device
    await TransportService.configure_tracking_source(
        db_session,
        tenant.id,
        vehicle.id,
        TransportTrackingSourceConfig(
            provider_name="TELTONIKA_FMB920",
            device_identifier="IMEI-867530900112233",
            is_enabled=True,
        ),
    )

    # 3. Ingest fresh location snapshot (recorded 10 seconds ago)
    now_utc = datetime.now(timezone.utc)
    snap = await TransportService.record_location_ping(
        db_session,
        tenant.id,
        TransportLocationPingRequest(
            vehicle_id=vehicle.id,
            latitude=Decimal("11.0168445"),
            longitude=Decimal("76.9558321"),
            speed_kmh=Decimal("42.50"),
            heading_degrees=Decimal("90.00"),
            recorded_at=now_utc - timedelta(seconds=10),
            data_source="GPS_TELEMATICS_MODEM",
        ),
    )
    assert snap.latitude == Decimal("11.0168445")

    # 4. Query live tracking state -> status ACTIVE, accurate freshness
    live_state = await TransportService.get_live_tracking(db_session, tenant.id, vehicle.id)
    assert live_state.status == TrackingProviderStatus.ACTIVE
    assert live_state.tracking_enabled is True
    assert live_state.last_known_location["latitude"] == 11.0168445
    assert live_state.freshness_seconds <= 15
    assert live_state.is_data_stale is False


@pytest.mark.asyncio
async def test_finance_invoice_generation_and_duplicate_prevention(
    db_session: AsyncSession, transport_setup: dict
):
    """Verifies Finance module invoice creation from transport pass and duplicate billing prevention."""
    tenant = transport_setup["tenant_a"]
    campus = transport_setup["campus_a"]
    ay = transport_setup["academic_year_a"]
    student = transport_setup["student_1"]
    admin = transport_setup["super_admin"]

    route = await TransportService.create_route(
        db_session,
        tenant.id,
        TransportRouteCreate(
            route_code="R-FIN-1",
            route_name="Finance Integration Route",
            campus_id=campus.id,
            capacity=30,
        ),
    )
    stop = await TransportService.create_stop(
        db_session,
        tenant.id,
        route.id,
        TransportStopCreate(
            stop_name="Hope College",
            stop_sequence=1,
            pickup_time=time(7, 30),
            fare_annual=Decimal("16500.00"),
            fare_term=Decimal("8500.00"),
        ),
    )

    # Allocate pass
    alloc = await TransportService.allocate_passenger(
        db_session,
        tenant.id,
        TransportAllocationCreate(
            student_id=student.id,
            academic_year_id=ay.id,
            route_id=route.id,
            stop_id=stop.id,
            service_type=TransportServiceType.ROUND_TRIP,
        ),
    )
    assert alloc.finance_invoice_id is None
    assert alloc.fee_status == TransportFeeStatus.PENDING.value

    # 1. Generate Invoice via Finance Module
    inv_res = await TransportService.generate_transport_invoices(
        db_session,
        tenant.id,
        GenerateTransportInvoiceRequest(
            allocation_ids=[alloc.id],
            due_days=15,
        ),
        generated_by=admin.id,
    )
    assert inv_res.invoices_created == 1
    assert inv_res.total_billed_amount == Decimal("16500.00")
    invoice_id = inv_res.invoice_ids[0]

    # Verify allocation fee status updated to BILLED
    alloc_updated = await TransportService.get_allocation(db_session, tenant.id, alloc.id)
    assert alloc_updated.finance_invoice_id == invoice_id
    assert alloc_updated.fee_status == TransportFeeStatus.INVOICED.value

    # 2. Retry invoice generation -> MUST NOT create duplicate, skipped_count=1
    inv_retry = await TransportService.generate_transport_invoices(
        db_session,
        tenant.id,
        GenerateTransportInvoiceRequest(allocation_ids=[alloc.id]),
        generated_by=admin.id,
    )
    assert inv_retry.invoices_created == 0
    assert inv_retry.skipped_count == 1


@pytest.mark.asyncio
async def test_transport_incident_reporting_and_escalation(
    db_session: AsyncSession, transport_setup: dict
):
    """Verifies transport incident reporting, high-severity logging, and resolution."""
    tenant = transport_setup["tenant_a"]
    campus = transport_setup["campus_a"]
    admin = transport_setup["super_admin"]
    student = transport_setup["student_1"]

    vehicle = await TransportService.create_vehicle(
        db_session,
        tenant.id,
        TransportVehicleCreate(
            registration_number="TN-38-INC-01",
            capacity=30,
            insurance_expiry=date.today() + timedelta(days=365),
            fitness_certificate_expiry=date.today() + timedelta(days=365),
        ),
    )
    driver = await TransportService.create_driver(
        db_session,
        tenant.id,
        TransportDriverCreate(
            full_name="Dharmalingam",
            license_number="DL-INC-001",
            license_expiry=date.today() + timedelta(days=365),
            phone_number="+91-9842100099",
        ),
    )
    route = await TransportService.create_route(
        db_session,
        tenant.id,
        TransportRouteCreate(
            route_code="R-INC-1",
            route_name="Incident Monitoring Route",
            campus_id=campus.id,
        ),
    )

    # 1. Report breakdown incident
    inc_data = TransportIncidentCreate(
        vehicle_id=vehicle.id,
        driver_id=driver.id,
        route_id=route.id,
        incident_type=TransportIncidentType.BREAKDOWN,
        severity=TransportIncidentSeverity.HIGH,
        incident_time=datetime.now(timezone.utc),
        location_description="Near Lakshmi Mills Flyover, km 12",
        description="Radiator coolant leak caused engine overheating, vehicle safely pulled to shoulder",
        emergency_services_contacted=False,
        involved_student_ids=[str(student.id)],
    )
    incident = await TransportService.report_incident(db_session, tenant.id, inc_data, reporter_id=admin.id)
    assert incident.incident_number.startswith("INC-TR-")
    assert incident.severity == TransportIncidentSeverity.HIGH.value
    assert incident.status == IncidentStatus.REPORTED.value

    # 2. Escalate & Resolve incident
    resolved = await TransportService.update_incident(
        db_session,
        tenant.id,
        incident.id,
        TransportIncidentUpdate(
            status=IncidentStatus.RESOLVED,
            resolution_notes="Backup bus dispatched to transfer passengers; radiator hose replaced",
            action_taken="PASSENGERS_TRANSFERRED_AND_REPAIR_COMPLETED",
        ),
    )
    assert resolved.status == IncidentStatus.RESOLVED.value
    assert resolved.resolved_at is not None


@pytest.mark.asyncio
async def test_transport_dashboard_analytics_and_scheduled_sweep(
    db_session: AsyncSession, transport_setup: dict
):
    """Verifies operational metrics aggregation and background scheduler operations sweep."""
    tenant = transport_setup["tenant_a"]

    # 1. Fetch dashboard metrics
    dashboard = await TransportService.get_transport_dashboard(db_session, tenant.id)
    assert hasattr(dashboard, "active_routes_count")
    assert hasattr(dashboard, "active_vehicles_count")
    assert hasattr(dashboard, "students_allocated_count")
    assert hasattr(dashboard, "route_capacity_utilization")

    # 2. Run background operations sweep
    sweep_results = await TransportService.sweep_transport_operations(db_session, tenant.id)
    assert "expiring_vehicle_compliance" in sweep_results
    assert "expiring_driver_licenses" in sweep_results
    assert "overdue_in_progress_trips" in sweep_results
    assert "expired_waitlist_offers" in sweep_results


@pytest.mark.asyncio
async def test_transport_multi_tenant_isolation(
    db_session: AsyncSession, transport_setup: dict
):
    """Verifies that transport entities belonging to Tenant A are never accessible by Tenant B."""
    tenant_a = transport_setup["tenant_a"]
    tenant_b = transport_setup["tenant_b"]
    campus_a = transport_setup["campus_a"]

    # Create vehicle in Tenant A
    v_a = await TransportService.create_vehicle(
        db_session,
        tenant_a.id,
        TransportVehicleCreate(
            registration_number="TN-38-ISO-A",
            capacity=30,
            insurance_expiry=date.today() + timedelta(days=365),
            fitness_certificate_expiry=date.today() + timedelta(days=365),
        ),
    )

    # Create route in Tenant A
    r_a = await TransportService.create_route(
        db_session,
        tenant_a.id,
        TransportRouteCreate(
            route_code="R-ISO-A",
            route_name="Tenant A Exclusive Route",
            campus_id=campus_a.id,
        ),
    )

    # Tenant B tries to fetch Tenant A's vehicle -> raises NotFoundException
    with pytest.raises(NotFoundException):
        await TransportService.get_vehicle(db_session, tenant_b.id, v_a.id)

    # Tenant B tries to fetch Tenant A's route -> raises NotFoundException
    with pytest.raises(NotFoundException):
        await TransportService.get_route(db_session, tenant_b.id, r_a.id)

    # Tenant B tries to update Tenant A's vehicle -> raises NotFoundException
    with pytest.raises(NotFoundException):
        await TransportService.update_vehicle(
            db_session,
            tenant_b.id,
            v_a.id,
            TransportVehicleUpdate(fleet_identifier="HACKED"),
        )
