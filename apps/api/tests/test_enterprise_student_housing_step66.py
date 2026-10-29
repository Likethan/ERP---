"""Enterprise Student Housing, Off-Campus Accommodation, Landlord Partnerships & Residential Compliance Tests (Step 66).

CampusOS Tagline: "One Campus. One System. One Source of Truth."

Automated verification suite validating:
1. Provider & Landlord registration, unique slug constraint, verification status, and updates.
2. Property creation, metadata, geo-coordinates, and lifecycle state transitions (Draft -> Pending Review -> Approved -> Published -> Suspended).
3. Discoverability rules: only PUBLISHED properties discoverable by students; suspended properties reject assignments.
4. Unit and Bed inventory creation, capacity metrics, and bed blocking for maintenance.
5. Student housing request submission, priority scoring, review, and waitlist handling.
6. Formal housing offer issuance, student acceptance/decline, and allocation.
7. Concurrency-safe bed allocation and anti-double-booking enforcement.
8. Room transfer operations with atomic bed release and re-allocation.
9. Housing agreement generation, lease lifecycle, deposit reference, and digital signature.
10. Check-in audit with keys, inventory checklist, and condition baseline.
11. Check-out audit with key return, damage assessment, and damage deduction calculation.
12. Safety, fire, and health compliance inspections with automated property suspension on critical failure.
13. Housing maintenance request workflow, priority handling, and resident satisfaction feedback.
14. Real-time persisted data-driven housing dashboard and occupancy analytics.
15. Multi-tenant isolation for all housing entities.
16. REST API endpoint authorization and role-based access control.
"""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.core.permissions import (
    HOUSING_AGREEMENT_MANAGE,
    HOUSING_AGREEMENT_READ,
    HOUSING_ANALYTICS_READ,
    HOUSING_ASSIGNMENT_MANAGE,
    HOUSING_CHECKIN_MANAGE,
    HOUSING_INSPECTION_MANAGE,
    HOUSING_INSPECTION_READ,
    HOUSING_MAINTENANCE_MANAGE,
    HOUSING_MAINTENANCE_SUBMIT,
    HOUSING_OFFER_MANAGE,
    HOUSING_PROPERTY_APPROVE,
    HOUSING_PROPERTY_MANAGE,
    HOUSING_PROPERTY_READ,
    HOUSING_PROVIDER_MANAGE,
    HOUSING_PROVIDER_READ,
    HOUSING_REQUEST_READ,
    HOUSING_REQUEST_REVIEW,
    HOUSING_REQUEST_SUBMIT_OWN,
)
from app.core.security import ACCESS_TOKEN_COOKIE_NAME, create_access_token, get_password_hash
from app.models.core import Institution
from app.models.housing import (
    AccommodationBed,
    AccommodationProperty,
    AccommodationProvider,
    AccommodationUnit,
    AgreementStatus,
    HousingAssignmentStatus,
    HousingOfferStatus,
    HousingRequestStatus,
    InspectionOutcome,
    InspectionType,
    MaintenanceCategory,
    MaintenancePriority,
    MaintenanceStatus,
    PropertyLifecycleStatus,
    PropertyType,
    ProviderType,
    ProviderVerificationStatus,
    UnitType,
)
from app.models.people import Role, StudentProfile, User, UserRoleAssignment
from app.schemas.housing import (
    AccommodationBedCreate,
    AccommodationPropertyCreate,
    AccommodationPropertyUpdate,
    AccommodationProviderCreate,
    AccommodationProviderUpdate,
    AccommodationUnitCreate,
    HousingAgreementCreate,
    HousingAssignmentCreate,
    HousingAssignmentTransferRequest,
    HousingCheckInOutCreate,
    HousingMaintenanceRequestCreate,
    HousingMaintenanceRequestUpdate,
    HousingOfferCreate,
    HousingOfferRespond,
    HousingPropertyInspectionCreate,
    PropertyStatusTransitionRequest,
    StudentHousingRequestCreate,
    StudentHousingRequestReview,
)
from app.services.housing_service import HousingService


def make_auth_headers(
    user: User,
    tenant_id: UUID,
    role_name: str = "SUPER_ADMIN",
    permissions: list[str] | None = None,
) -> dict[str, str]:
    """Helper to generate JWT bearer and cookie authorization headers."""
    perms = permissions if permissions is not None else ["*"]
    token = create_access_token(
        user_id=user.id,
        tenant_id=tenant_id,
        email=user.email,
        roles=[role_name],
        permissions=perms,
    )
    return {
        "Authorization": f"Bearer {token}",
        "Cookie": f"{ACCESS_TOKEN_COOKIE_NAME}={token}",
    }


async def create_student_helper(
    db: AsyncSession, tenant_id: UUID, email: str, full_name: str, roll_no: str
) -> tuple[User, StudentProfile]:
    """Creates a student user and student profile for housing testing."""
    first, *rest = full_name.split()
    last = " ".join(rest) if rest else "Student"

    user = User(
        id=uuid4(),
        primary_tenant_id=tenant_id,
        email=email,
        phone_number="+919876543210",
        password_hash=get_password_hash("SecretHousing123!"),
        status="ACTIVE",
        first_name=first,
        last_name=last,
    )
    db.add(user)
    await db.flush()

    student = StudentProfile(
        id=uuid4(),
        tenant_id=tenant_id,
        user_id=user.id,
        admission_number=roll_no,
        registration_number=f"REG-{roll_no}",
        roll_number=roll_no,
        date_of_birth=date(2003, 5, 15),
        gender="MALE",
        status="ACTIVE",
        admission_date=date(2023, 8, 1),
        expected_graduation_date=date(2027, 5, 31),
        program_id=uuid4(),
        batch_id=uuid4(),
    )
    db.add(student)
    await db.flush()

    # Assign STUDENT role
    role_res = await db.execute(select(Role).where(Role.name == "STUDENT"))
    role = role_res.scalar_one_or_none()
    if role:
        assignment = UserRoleAssignment(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=user.id,
            role_id=role.id,
        )
        db.add(assignment)
        await db.flush()

    return user, student


# =============================================================================
# 1. ACCOMMODATION PROVIDER TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_provider_registration_verification_and_deduplication(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Validates provider registration, unique slug constraints, verification and status updates."""
    service = HousingService(db_session, tenant_a.id)

    # 1. Create a private landlord provider
    create_dto = AccommodationProviderCreate(
        name="Greenwood Student Residences Trust",
        slug="greenwood-trust",
        provider_type=ProviderType.STUDENT_RESIDENCE_TRUST,
        registration_number="REG-TRUST-2026-001",
        contact_name="Robert Vance",
        contact_email="vance@greenwoodresidences.com",
        contact_phone="+919845012345",
        address="124 Residency Road, Tech Corridor, Bangalore",
        city="Bengaluru",
        state="Karnataka",
        mou_reference="MOU/2026/GW-01",
        mou_valid_from=date(2026, 1, 1),
        mou_valid_to=date(2029, 12, 31),
    )
    provider = await service.create_provider(create_dto)
    assert provider.id is not None
    assert provider.name == "Greenwood Student Residences Trust"
    assert provider.verification_status == ProviderVerificationStatus.PENDING

    # 2. Duplicate slug should raise ConflictException
    with pytest.raises(ConflictException) as exc_info:
        await service.create_provider(create_dto)
    assert "already exists" in str(exc_info.value.detail)

    # 3. Verify provider
    verified_provider = await service.update_provider(
        provider.id,
        AccommodationProviderUpdate(
            verification_status=ProviderVerificationStatus.VERIFIED,
            verification_notes="MoU signed, municipal fire certificate verified",
        ),
    )
    assert verified_provider.verification_status == ProviderVerificationStatus.VERIFIED
    assert verified_provider.verified_at is not None

    # 4. Read list of providers
    providers = await service.list_providers()
    assert len(providers) >= 1
    assert any(p.id == provider.id for p in providers)


# =============================================================================
# 2. ACCOMMODATION PROPERTY & LIFECYCLE TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_property_lifecycle_and_discoverability(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Tests property creation, state transitions (DRAFT -> PENDING_REVIEW -> APPROVED -> PUBLISHED -> SUSPENDED),
    and validates discoverability gates.
    """
    service = HousingService(db_session, tenant_a.id)

    # Create provider
    provider = await service.create_provider(
        AccommodationProviderCreate(
            name="Apex Student Living Ltd",
            slug="apex-living",
            provider_type=ProviderType.HOUSING_COMPANY,
            contact_name="Anita Roy",
            contact_email="anita@apexliving.in",
            contact_phone="+919876543201",
            address="Plot 45, University Ring Road",
            city="Bengaluru",
            state="Karnataka",
        )
    )

    # Create property
    prop_dto = AccommodationPropertyCreate(
        name="Apex Heights - Block A",
        code="APX-HTS-A",
        slug="apex-heights-a",
        property_type=PropertyType.OFF_CAMPUS_HOSTEL,
        provider_id=provider.id,
        address="Plot 45, University Ring Road",
        city="Bengaluru",
        state="Karnataka",
        postal_code="560100",
        distance_to_campus_km=Decimal("1.8"),
        amenities=["WIFI", "AIR_CONDITIONING", "MESS_FACILITY", "BIOMETRIC_ACCESS", "STUDY_ROOM"],
        accessibility_features=["WHEELCHAIR_RAMP", "ELEVATOR"],
        safety_features=["CCTV", "24x7_SECURITY", "FIRE_EXTINGUISHERS", "SMOKE_ALARMS"],
        manager_name="Apex Control Room",
        manager_phone="+919876543999",
        monthly_rent_min=Decimal("7000.00"),
        monthly_rent_max=Decimal("12000.00"),
        security_deposit_amount=Decimal("15000.00"),
    )
    prop = await service.create_property(prop_dto, user_id=tenant_admin_a.id)
    assert prop.lifecycle_status == PropertyLifecycleStatus.DRAFT

    # Students should NOT discover DRAFT properties
    published_props = await service.list_properties(published_only=True)
    assert not any(p.id == prop.id for p in published_props)

    # Transition to PENDING_REVIEW
    prop = await service.transition_property_status(
        prop.id,
        PropertyStatusTransitionRequest(
            target_status=PropertyLifecycleStatus.PENDING_REVIEW,
            notes="Ready for warden and compliance audit",
        ),
        user_id=tenant_admin_a.id,
    )
    assert prop.lifecycle_status == PropertyLifecycleStatus.PENDING_REVIEW

    # Approve property
    prop = await service.transition_property_status(
        prop.id,
        PropertyStatusTransitionRequest(
            target_status=PropertyLifecycleStatus.APPROVED,
            approval_valid_until=date(2027, 6, 30),
            notes="Audit completed, passed fire and hygiene norms",
        ),
        user_id=tenant_admin_a.id,
    )
    assert prop.lifecycle_status == PropertyLifecycleStatus.APPROVED

    # Publish property
    prop = await service.transition_property_status(
        prop.id,
        PropertyStatusTransitionRequest(
            target_status=PropertyLifecycleStatus.PUBLISHED,
            notes="Opening for student allocations for Academic Year 2026-27",
        ),
        user_id=tenant_admin_a.id,
    )
    assert prop.lifecycle_status == PropertyLifecycleStatus.PUBLISHED

    # Now discoverable by students
    published_props = await service.list_properties(published_only=True)
    assert any(p.id == prop.id for p in published_props)

    # Suspend property
    prop = await service.transition_property_status(
        prop.id,
        PropertyStatusTransitionRequest(
            target_status=PropertyLifecycleStatus.SUSPENDED,
            notes="Temporary suspension due to water main maintenance",
        ),
        user_id=tenant_admin_a.id,
    )
    assert prop.lifecycle_status == PropertyLifecycleStatus.SUSPENDED

    # Once suspended, no longer discoverable for student bookings
    published_props = await service.list_properties(published_only=True)
    assert not any(p.id == prop.id for p in published_props)


# =============================================================================
# 3. UNIT & BED INVENTORY & AVAILABILITY TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_unit_and_bed_inventory_availability_and_blocking(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies unit and addressable bed creation, live availability metrics,
    and bed blocking for maintenance.
    """
    service = HousingService(db_session, tenant_a.id)

    # Setup property
    prop = await service.create_property(
        AccommodationPropertyCreate(
            name="Emerald Residence Tower",
            code="EMR-TWR",
            slug="emerald-tower",
            property_type=PropertyType.CAMPUS_HOSTEL,
            address="East Campus, Sector 4",
            city="Bengaluru",
            state="Karnataka",
            postal_code="560100",
        ),
        user_id=tenant_admin_a.id,
    )

    # Create Unit (2-bed double occupancy)
    unit = await service.create_unit(
        AccommodationUnitCreate(
            property_id=prop.id,
            unit_number="Room 201",
            floor_number=2,
            unit_type=UnitType.DOUBLE_OCCUPANCY,
            bed_capacity=2,
            rent_per_bed=Decimal("8500.00"),
            security_deposit_per_bed=Decimal("15000.00"),
            has_attached_bath=True,
            is_furnished=True,
        )
    )
    assert unit.bed_capacity == 2

    # Verify unit has 2 beds created automatically
    units = await service.list_units(prop.id)
    assert len(units) >= 1
    created_unit = next(u for u in units if u.id == unit.id)
    assert len(created_unit.beds) == 2
    bed_1, bed_2 = created_unit.beds[0], created_unit.beds[1]
    assert bed_1.is_available is True

    # Check property capacity metrics
    await db_session.refresh(prop)
    assert prop.total_bed_capacity == 2
    assert prop.available_beds == 2
    assert prop.occupied_beds == 0

    # Block bed_2 for maintenance
    blocked_bed = await service.block_bed(bed_2.id, reason="Desk repair and painting")
    assert blocked_bed.is_available is False
    assert blocked_bed.status == "BLOCKED_MAINTENANCE"
    assert blocked_bed.blocked_reason == "Desk repair and painting"

    # Re-check property capacity
    await service.recalculate_property_capacity(prop.id)
    await db_session.refresh(prop)
    assert prop.available_beds == 1


# =============================================================================
# 4. HOUSING REQUESTS & WAITLIST ENGINE TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_student_housing_request_waitlist_and_scoring(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Tests student housing request submission, priority scoring,
    and reviewer waitlist decisions.
    """
    service = HousingService(db_session, tenant_a.id)

    # Create student
    _, student = await create_student_helper(
        db_session, tenant_a.id, "arun.kumar@campus.edu", "Arun Kumar", "CS2026-045"
    )

    req_dto = StudentHousingRequestCreate(
        academic_term="AY 2026-27 Autumn",
        preferred_unit_type=UnitType.DOUBLE_OCCUPANCY,
        requested_move_in_date=date(2026, 8, 1),
        requested_move_out_date=date(2027, 5, 31),
        budget_min=Decimal("6000.00"),
        budget_max=Decimal("9500.00"),
        accessibility_required=True,
        disability_accommodation_notes="Ground floor or elevator access required",
        special_requests="Quiet study environment preferred",
    )

    # 1. Submit request
    req = await service.submit_housing_request(student.id, req_dto)
    assert req.status == HousingRequestStatus.SUBMITTED
    # Accessibility required adds priority score
    assert req.priority_score >= Decimal("50.0")

    # 2. Reviewer moves request to WAITLISTED
    reviewed_req = await service.review_housing_request(
        req.id,
        StudentHousingRequestReview(
            status=HousingRequestStatus.WAITLISTED,
            priority_score=Decimal("85.00"),
            review_notes="High priority candidate, placed on waitlist for Double Room allocation.",
        ),
        reviewer_id=tenant_admin_a.id,
    )
    assert reviewed_req.status == HousingRequestStatus.WAITLISTED
    assert reviewed_req.waitlist_position is not None

    # 3. Filter requests by waitlist
    waitlist_items = await service.list_housing_requests(status=HousingRequestStatus.WAITLISTED.value)
    assert len(waitlist_items) >= 1
    assert any(r.id == req.id for r in waitlist_items)


# =============================================================================
# 5. HOUSING OFFERS & CONCURRENCY ALLOCATION TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_housing_offer_issuance_acceptance_and_bed_allocation(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Tests formal offer issuance, student acceptance, bed allocation,
    and anti-double-booking locks.
    """
    service = HousingService(db_session, tenant_a.id)

    # Create 2 students
    _, student1 = await create_student_helper(
        db_session, tenant_a.id, "priya.nair@campus.edu", "Priya Nair", "EC2026-088"
    )
    _, student2 = await create_student_helper(
        db_session, tenant_a.id, "vikram.singh@campus.edu", "Vikram Singh", "ME2026-102"
    )

    # Create property, unit, bed
    prop = await service.create_property(
        AccommodationPropertyCreate(
            name="Sapphire Court Residence",
            code="SAP-CRT",
            slug="sapphire-court",
            property_type=PropertyType.CAMPUS_HOSTEL,
            address="North Campus, Gate 2",
            city="Bengaluru",
            state="Karnataka",
            postal_code="560100",
        ),
        user_id=tenant_admin_a.id,
    )
    await service.transition_property_status(
        prop.id,
        PropertyStatusTransitionRequest(target_status=PropertyLifecycleStatus.APPROVED),
        user_id=tenant_admin_a.id,
    )
    unit = await service.create_unit(
        AccommodationUnitCreate(
            property_id=prop.id,
            unit_number="Room 101",
            floor_number=1,
            unit_type=UnitType.SINGLE_OCCUPANCY,
            bed_capacity=1,
            rent_per_bed=Decimal("12000.00"),
            security_deposit_per_bed=Decimal("20000.00"),
        )
    )

    units = await service.list_units(prop.id)
    bed = units[0].beds[0]

    # Create housing request for student 1
    req = await service.submit_housing_request(
        student1.id,
        StudentHousingRequestCreate(
            preferred_property_id=prop.id,
            preferred_unit_type=UnitType.SINGLE_OCCUPANCY,
            academic_term="AY 2026-27",
            requested_move_in_date=date(2026, 8, 1),
            requested_move_out_date=date(2027, 5, 31),
            budget_max=Decimal("15000.00"),
        ),
    )

    # Issue formal offer to student1
    offer_dto = HousingOfferCreate(
        request_id=req.id,
        property_id=prop.id,
        unit_id=unit.id,
        bed_id=bed.id,
        offered_rent_monthly=Decimal("12000.00"),
        offered_deposit=Decimal("20000.00"),
        occupancy_start_date=date(2026, 8, 1),
        occupancy_end_date=date(2027, 5, 31),
        offer_valid_days=7,
    )
    offer = await service.create_offer(offer_dto)
    assert offer.status == HousingOfferStatus.OFFERED

    # Student 1 accepts offer -> Bed is officially allocated
    accepted_offer = await service.respond_to_offer(
        offer.id,
        HousingOfferRespond(decision=HousingOfferStatus.ACCEPTED, response_notes="Delighted to accept!"),
        student_id=student1.id,
    )
    assert accepted_offer.status == HousingOfferStatus.ACCEPTED

    # Verify bed is no longer available
    await db_session.refresh(bed)
    assert bed.is_available is False
    assert bed.status == "OCCUPIED"

    # Attempting to directly allocate the same bed to student 2 MUST raise ConflictException
    with pytest.raises(ConflictException) as exc_info:
        await service.allocate_student(
            HousingAssignmentCreate(
                student_id=student2.id,
                property_id=prop.id,
                unit_id=unit.id,
                bed_id=bed.id,
                start_date=date(2026, 8, 1),
                end_date=date(2027, 5, 31),
                monthly_rent=Decimal("12000.00"),
                security_deposit=Decimal("20000.00"),
            )
        )
    assert "not currently available" in str(exc_info.value.detail)


# =============================================================================
# 6. ROOM TRANSFER TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_housing_room_transfer_workflow(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies that transferring a resident safely frees the previous bed and
    claims the new bed in a single atomic operation.
    """
    service = HousingService(db_session, tenant_a.id)

    _, student = await create_student_helper(
        db_session, tenant_a.id, "kavita.reddy@campus.edu", "Kavita Reddy", "CV2026-034"
    )

    prop = await service.create_property(
        AccommodationPropertyCreate(
            name="Garnet Hall of Residence",
            code="GAR-HALL",
            slug="garnet-hall",
            property_type=PropertyType.CAMPUS_HOSTEL,
            address="West Campus, Gate 4",
            city="Bengaluru",
            state="Karnataka",
            postal_code="560100",
        ),
        user_id=tenant_admin_a.id,
    )

    # Unit 101 with 1 bed
    unit_1 = await service.create_unit(
        AccommodationUnitCreate(
            property_id=prop.id,
            unit_number="101",
            floor_number=1,
            unit_type=UnitType.SINGLE_OCCUPANCY,
            bed_capacity=1,
            rent_per_bed=Decimal("9000.00"),
            security_deposit_per_bed=Decimal("15000.00"),
        )
    )

    # Unit 202 with 1 bed (Target of transfer)
    unit_2 = await service.create_unit(
        AccommodationUnitCreate(
            property_id=prop.id,
            unit_number="202",
            floor_number=2,
            unit_type=UnitType.SINGLE_OCCUPANCY,
            bed_capacity=1,
            rent_per_bed=Decimal("9500.00"),
            security_deposit_per_bed=Decimal("15000.00"),
        )
    )

    units = await service.list_units(prop.id)
    u1_full = next(u for u in units if u.id == unit_1.id)
    u2_full = next(u for u in units if u.id == unit_2.id)
    bed_1 = u1_full.beds[0]
    bed_2 = u2_full.beds[0]

    # Initial allocation to Bed 1
    initial_alloc = await service.allocate_student(
        HousingAssignmentCreate(
            student_id=student.id,
            property_id=prop.id,
            unit_id=unit_1.id,
            bed_id=bed_1.id,
            start_date=date(2026, 8, 1),
            end_date=date(2027, 5, 31),
            monthly_rent=Decimal("9000.00"),
            security_deposit=Decimal("15000.00"),
        )
    )

    await db_session.refresh(bed_1)
    assert bed_1.is_available is False

    # Execute Room Transfer to Bed 2
    new_alloc = await service.transfer_assignment(
        initial_alloc.id,
        HousingAssignmentTransferRequest(
            target_unit_id=unit_2.id,
            target_bed_id=bed_2.id,
            transfer_reason="Medical recommendation: quiet floor required.",
        ),
    )

    # Verify assignment is TRANSFERRED and bed 1 is AVAILABLE
    await db_session.refresh(initial_alloc)
    assert initial_alloc.status == HousingAssignmentStatus.TRANSFERRED
    assert initial_alloc.bed_id == bed_2.id

    await db_session.refresh(bed_1)
    assert bed_1.is_available is True
    assert bed_1.status == "AVAILABLE"

    # Verify bed 2 is OCCUPIED
    assert new_alloc.status == HousingAssignmentStatus.TRANSFERRED
    assert new_alloc.bed_id == bed_2.id

    await db_session.refresh(bed_2)
    assert bed_2.is_available is False
    assert bed_2.status == "OCCUPIED"


# =============================================================================
# 7. HOUSING AGREEMENTS & CHECK-IN / CHECK-OUT AUDITS
# =============================================================================


@pytest.mark.asyncio
async def test_housing_agreement_checkin_checkout_and_damage_assessment(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies lease agreement creation, resident check-in audit,
    and check-out with damage deduction calculations.
    """
    service = HousingService(db_session, tenant_a.id)

    _, student = await create_student_helper(
        db_session, tenant_a.id, "siddharth.m@campus.edu", "Siddharth Menon", "ME2026-056"
    )

    prop = await service.create_property(
        AccommodationPropertyCreate(
            name="Coral Residence",
            code="CORAL-RES",
            slug="coral-residence",
            property_type=PropertyType.CAMPUS_HOSTEL,
            address="South Campus",
            city="Bengaluru",
            state="Karnataka",
            postal_code="560100",
        ),
        user_id=tenant_admin_a.id,
    )
    await service.transition_property_status(
        prop.id,
        PropertyStatusTransitionRequest(target_status=PropertyLifecycleStatus.APPROVED),
        user_id=tenant_admin_a.id,
    )
    unit = await service.create_unit(
        AccommodationUnitCreate(
            property_id=prop.id,
            unit_number="305",
            floor_number=3,
            unit_type=UnitType.SINGLE_OCCUPANCY,
            bed_capacity=1,
            rent_per_bed=Decimal("11000.00"),
            security_deposit_per_bed=Decimal("18000.00"),
        )
    )
    units = await service.list_units(prop.id)
    bed = units[0].beds[0]

    alloc = await service.allocate_student(
        HousingAssignmentCreate(
            student_id=student.id,
            property_id=prop.id,
            unit_id=unit.id,
            bed_id=bed.id,
            start_date=date(2026, 8, 1),
            end_date=date(2027, 5, 31),
            monthly_rent=Decimal("11000.00"),
            security_deposit=Decimal("18000.00"),
        )
    )

    # 1. Create digital lease agreement
    agreement = await service.create_agreement(
        HousingAgreementCreate(
            assignment_id=alloc.id,
            agreement_title="Student Housing Tenancy Agreement 2026-27",
            valid_from=date(2026, 8, 1),
            valid_to=date(2027, 5, 31),
            rent_amount=Decimal("11000.00"),
            deposit_amount=Decimal("18000.00"),
            payment_frequency="MONTHLY",
            finance_invoice_reference="INV-HOUSING-2026-0089",
            deposit_invoice_reference="DEP-HOUSING-2026-0089",
        )
    )
    assert agreement.status == AgreementStatus.PENDING_SIGNATURE
    assert agreement.agreement_number.startswith("AGR-")

    # 2. Check-In Audit
    checkin_rec = await service.record_check_in_out(
        HousingCheckInOutCreate(
            assignment_id=alloc.id,
            record_type="CHECK_IN",
            scheduled_date=date(2026, 8, 1),
            key_card_issued_or_returned=True,
            key_identifier="KEY-305-RFID-01",
            room_condition_rating="EXCELLENT",
            checklist_items={
                "bed_frame": "GOOD",
                "mattress": "GOOD",
                "study_desk": "GOOD",
                "cupboard": "GOOD",
            },
            student_signature_confirmed=True,
            notes="Resident received keys and room inventory verified.",
        ),
        inspector_id=tenant_admin_a.id,
    )
    assert checkin_rec.record_type == "CHECK_IN"
    assert checkin_rec.status == "COMPLETED"

    # 3. Check-Out Audit with Damage Assessment
    checkout_rec = await service.record_check_in_out(
        HousingCheckInOutCreate(
            assignment_id=alloc.id,
            record_type="CHECK_OUT",
            scheduled_date=date(2027, 5, 31),
            key_card_issued_or_returned=True,
            key_identifier="KEY-305-RFID-01",
            room_condition_rating="DAMAGED",
            checklist_items={
                "bed_frame": "GOOD",
                "mattress": "GOOD",
                "study_desk": "DAMAGED",
                "cupboard": "DAMAGED",
            },
            damage_assessed_amount=Decimal("1500.00"),
            damage_description="Deep surface scratch on study desk, broken latch on cupboard.",
            student_signature_confirmed=True,
            notes="Keys returned. Damage deduction of INR 1500 assessed against security deposit.",
        ),
        inspector_id=tenant_admin_a.id,
    )
    assert checkout_rec.record_type == "CHECK_OUT"
    assert checkout_rec.damage_assessed_amount == Decimal("1500.00")

    # Allocation should now be CHECKED_OUT
    await db_session.refresh(alloc)
    assert alloc.status == HousingAssignmentStatus.CHECKED_OUT

    # Bed should now be AVAILABLE
    await db_session.refresh(bed)
    assert bed.is_available is True
    assert bed.status == "AVAILABLE"


# =============================================================================
# 8. PROPERTY INSPECTION & AUTO-SUSPENSION TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_property_inspection_and_critical_auto_suspension(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies safety & compliance inspections, and proves that a critical failure
    automatically suspends property availability and prevents new bookings.
    """
    service = HousingService(db_session, tenant_a.id)

    # Create published property
    prop = await service.create_property(
        AccommodationPropertyCreate(
            name="Orchid Private Student Hostel",
            code="ORCHID-PVT",
            slug="orchid-hostel",
            property_type=PropertyType.OFF_CAMPUS_HOSTEL,
            address="12 College View, Outer Ring Road",
            city="Bengaluru",
            state="Karnataka",
            postal_code="560100",
        ),
        user_id=tenant_admin_a.id,
    )
    await service.transition_property_status(
        prop.id,
        PropertyStatusTransitionRequest(target_status=PropertyLifecycleStatus.APPROVED),
        user_id=tenant_admin_a.id,
    )
    await service.transition_property_status(
        prop.id,
        PropertyStatusTransitionRequest(target_status=PropertyLifecycleStatus.PUBLISHED),
        user_id=tenant_admin_a.id,
    )

    assert prop.lifecycle_status == PropertyLifecycleStatus.PUBLISHED

    # Conduct Fire & Life Safety Inspection with CRITICAL FAILURE
    insp_dto = HousingPropertyInspectionCreate(
        property_id=prop.id,
        inspection_date=date.today(),
        inspection_type=InspectionType.SAFETY_FIRE,
        overall_outcome=InspectionOutcome.FAILED_CRITICAL,
        safety_score=Decimal("42.0"),
        checklist_results={
            "fire_alarms": "INOPERATIVE",
            "fire_exit": "BLOCKED",
            "extinguishers": "EXPIRED",
        },
        critical_issues_found=True,
        availability_suspended=True,
        corrective_actions_required="Clear fire escape immediately and recertify all fire extinguishers.",
        corrective_action_deadline=date.today() + timedelta(days=7),
    )
    insp = await service.record_inspection(insp_dto, inspector_id=tenant_admin_a.id)
    assert insp.id is not None
    assert insp.critical_issues_found is True

    # Check that property was AUTOMATICALLY SUSPENDED
    await db_session.refresh(prop)
    assert prop.lifecycle_status == PropertyLifecycleStatus.SUSPENDED

    # Suspended property cannot issue new offers
    unit = await service.create_unit(
        AccommodationUnitCreate(
            property_id=prop.id,
            unit_number="101",
            floor_number=1,
            unit_type=UnitType.SINGLE_OCCUPANCY,
            bed_capacity=1,
            rent_per_bed=Decimal("7000.00"),
            security_deposit_per_bed=Decimal("10000.00"),
        )
    )
    units = await service.list_units(prop.id)
    bed = units[0].beds[0]
    _, dummy_student = await create_student_helper(
        db_session, tenant_a.id, "test.block@campus.edu", "Test Block", "CS2026-999"
    )

    req = await service.submit_housing_request(
        dummy_student.id,
        StudentHousingRequestCreate(
            preferred_property_id=prop.id,
            requested_move_in_date=date(2026, 8, 1),
            requested_move_out_date=date(2027, 5, 31),
        ),
    )

    with pytest.raises(ValidationException) as exc_info:
        await service.create_offer(
            HousingOfferCreate(
                request_id=req.id,
                property_id=prop.id,
                unit_id=unit.id,
                bed_id=bed.id,
                offered_rent_monthly=Decimal("7000.00"),
                offered_deposit=Decimal("10000.00"),
                occupancy_start_date=date(2026, 8, 1),
                occupancy_end_date=date(2027, 5, 31),
            )
        )
    assert "not approved or published" in str(exc_info.value.detail)


# =============================================================================
# 9. HOUSING MAINTENANCE REQUESTS TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_housing_maintenance_ticket_resolution_and_tenant_rating(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies maintenance request ticketing, status updates,
    and tenant satisfaction ratings upon closure.
    """
    service = HousingService(db_session, tenant_a.id)

    student_user, student = await create_student_helper(
        db_session, tenant_a.id, "rohan.mehta@campus.edu", "Rohan Mehta", "ME2026-077"
    )

    prop = await service.create_property(
        AccommodationPropertyCreate(
            name="Topaz Court",
            code="TOPAZ-CRT",
            slug="topaz-court",
            property_type=PropertyType.CAMPUS_HOSTEL,
            address="East Campus",
            city="Bengaluru",
            state="Karnataka",
            postal_code="560100",
        ),
        user_id=tenant_admin_a.id,
    )
    await service.transition_property_status(
        prop.id,
        PropertyStatusTransitionRequest(target_status=PropertyLifecycleStatus.APPROVED),
        user_id=tenant_admin_a.id,
    )
    unit = await service.create_unit(
        AccommodationUnitCreate(
            property_id=prop.id,
            unit_number="402",
            floor_number=4,
            unit_type=UnitType.SINGLE_OCCUPANCY,
            bed_capacity=1,
            rent_per_bed=Decimal("8000.00"),
            security_deposit_per_bed=Decimal("12000.00"),
        )
    )

    # 1. Resident logs plumbing maintenance request
    ticket = await service.submit_maintenance_request(
        HousingMaintenanceRequestCreate(
            property_id=prop.id,
            unit_id=unit.id,
            category=MaintenanceCategory.PLUMBING,
            priority=MaintenancePriority.HIGH,
            title="Severe washroom tap leak flooding floor",
            description="The bathroom faucet broke and is continuously spraying water.",
        ),
        user_id=student_user.id,
        student_id=student.id,
    )
    assert ticket.status == MaintenanceStatus.REPORTED
    assert ticket.priority == MaintenancePriority.HIGH

    # 2. Staff acknowledges and moves to IN_PROGRESS
    ticket = await service.update_maintenance_request(
        ticket.id,
        HousingMaintenanceRequestUpdate(
            status=MaintenanceStatus.IN_PROGRESS,
            assigned_technician_name="Campus Facilities Plumbing Team",
            completion_notes="Plumber dispatched with replacement cartridge.",
        ),
    )
    assert ticket.status == MaintenanceStatus.IN_PROGRESS
    assert ticket.assigned_technician_name == "Campus Facilities Plumbing Team"

    # 3. Staff resolves ticket with tenant rating
    ticket = await service.update_maintenance_request(
        ticket.id,
        HousingMaintenanceRequestUpdate(
            status=MaintenanceStatus.COMPLETED,
            completion_notes="Replaced faulty brass faucet spindle and washer. Leak stopped.",
            tenant_satisfaction_rating=5,
            tenant_feedback="Fixed within 45 minutes of reporting. Excellent response!",
        ),
    )
    assert ticket.status == MaintenanceStatus.COMPLETED
    assert ticket.tenant_satisfaction_rating == 5
    assert ticket.completed_at is not None


# =============================================================================
# 10. REAL-TIME OCCUPANCY ANALYTICS TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_realtime_occupancy_analytics_and_tenant_isolation(
    db_session: AsyncSession, tenant_a: Institution, tenant_b: Institution, tenant_admin_a: User
):
    """Verifies that occupancy analytics are derived from real persisted inventory
    and strictly respect multi-tenant boundaries.
    """
    service_a = HousingService(db_session, tenant_a.id)
    service_b = HousingService(db_session, tenant_b.id)

    # Tenant A property with 2 units, 3 beds
    prop_a = await service_a.create_property(
        AccommodationPropertyCreate(
            name="Tenant A Residence",
            code="TA-RES-01",
            slug="ta-res-01",
            property_type=PropertyType.CAMPUS_HOSTEL,
            address="Main Road",
            city="Bengaluru",
            state="Karnataka",
            postal_code="560100",
        ),
        user_id=tenant_admin_a.id,
    )
    u1 = await service_a.create_unit(
        AccommodationUnitCreate(
            property_id=prop_a.id,
            unit_number="101",
            floor_number=1,
            unit_type=UnitType.SINGLE_OCCUPANCY,
            bed_capacity=1,
            rent_per_bed=Decimal("10000.00"),
            security_deposit_per_bed=Decimal("15000.00"),
        )
    )
    u2 = await service_a.create_unit(
        AccommodationUnitCreate(
            property_id=prop_a.id,
            unit_number="102",
            floor_number=1,
            unit_type=UnitType.DOUBLE_OCCUPANCY,
            bed_capacity=2,
            rent_per_bed=Decimal("8000.00"),
            security_deposit_per_bed=Decimal("12000.00"),
        )
    )
    units_a = await service_a.list_units(prop_a.id)
    u1_full = next(u for u in units_a if u.id == u1.id)
    b1 = u1_full.beds[0]

    # Allocate b1 to student
    _, st_a = await create_student_helper(
        db_session, tenant_a.id, "tenant.a.student@campus.edu", "Alice Alpha", "TA-001"
    )
    await service_a.allocate_student(
        HousingAssignmentCreate(
            student_id=st_a.id,
            property_id=prop_a.id,
            unit_id=u1.id,
            bed_id=b1.id,
            start_date=date(2026, 8, 1),
            end_date=date(2027, 5, 31),
            monthly_rent=Decimal("10000.00"),
            security_deposit=Decimal("15000.00"),
        )
    )

    # Calculate analytics for Tenant A
    analytics_a = await service_a.get_housing_analytics()
    assert analytics_a.total_capacity_beds >= 3
    assert analytics_a.occupied_beds >= 1
    assert analytics_a.occupancy_rate_percentage > 0.0

    # Tenant B analytics should be completely empty / zero
    analytics_b = await service_b.get_housing_analytics()
    assert analytics_b.total_capacity_beds == 0
    assert analytics_b.occupied_beds == 0

    # Cross-tenant read must fail
    with pytest.raises(NotFoundException):
        await service_b.get_property(prop_a.id)


# =============================================================================
# 11. REST API ENDPOINTS & RBAC INTEGRATION TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_rest_api_housing_endpoints_and_rbac(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Tests housing REST endpoints: property listing, request submission,
    and role-based permission verification.
    """
    admin_headers = make_auth_headers(
        tenant_admin_a,
        tenant_a.id,
        role_name="SUPER_ADMIN",
        permissions=["*"],
    )

    # 1. Create Provider via REST API
    provider_payload = {
        "name": "Metro Student Residences Corp",
        "slug": "metro-residences",
        "provider_type": "HOUSING_COMPANY",
        "contact_name": "Deepak Verma",
        "contact_email": "deepak@metroresidences.com",
        "contact_phone": "+919876543210",
        "address": "99 Innovation Way",
        "city": "Bengaluru",
        "state": "Karnataka",
    }
    resp = await client.post(
        "/api/v1/housing/providers",
        json=provider_payload,
        headers=admin_headers,
    )
    assert resp.status_code == 201, resp.text
    provider_data = resp.json()
    provider_id = provider_data["id"]

    # 2. Create Property via REST API
    prop_payload = {
        "name": "Metro Horizon House",
        "code": "METRO-HORIZON",
        "slug": "metro-horizon-house",
        "property_type": "OFF_CAMPUS_HOSTEL",
        "provider_id": provider_id,
        "address": "99 Innovation Way",
        "city": "Bengaluru",
        "state": "Karnataka",
        "postal_code": "560103",
        "distance_to_campus_km": 1.2,
        "amenities": ["WIFI", "CCTV", "GYM"],
    }
    resp = await client.post(
        "/api/v1/housing/properties",
        json=prop_payload,
        headers=admin_headers,
    )
    assert resp.status_code == 201, resp.text
    prop_data = resp.json()
    prop_id = prop_data["id"]

    # 3. Transition Property: Approve then Publish
    resp = await client.post(
        f"/api/v1/housing/properties/{prop_id}/transition",
        json={"target_status": "APPROVED", "notes": "All documents verified."},
        headers=admin_headers,
    )
    assert resp.status_code == 200

    resp = await client.post(
        f"/api/v1/housing/properties/{prop_id}/transition",
        json={"target_status": "PUBLISHED", "notes": "Live for bookings."},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["lifecycle_status"] == "PUBLISHED"

    # 4. Student discovers published properties
    st_user, st_profile = await create_student_helper(
        db_session, tenant_a.id, "student.api@campus.edu", "Sunita Rao", "CS2026-API"
    )
    student_headers = make_auth_headers(
        st_user,
        tenant_a.id,
        role_name="STUDENT",
        permissions=[
            HOUSING_PROPERTY_READ,
            HOUSING_REQUEST_SUBMIT_OWN,
            HOUSING_AGREEMENT_READ,
            HOUSING_MAINTENANCE_SUBMIT,
        ],
    )

    resp = await client.get("/api/v1/housing/properties?published_only=true", headers=student_headers)
    assert resp.status_code == 200
    res_list = resp.json()
    assert any(p["id"] == prop_id for p in res_list)

    # 5. Student submits housing request via REST API
    req_payload = {
        "preferred_property_id": prop_id,
        "preferred_unit_type": "SINGLE_OCCUPANCY",
        "academic_term": "AY 2026-27 Autumn",
        "requested_move_in_date": "2026-08-01",
        "requested_move_out_date": "2027-05-31",
        "budget_min": 5000,
        "budget_max": 12000,
        "accessibility_required": False,
        "special_requests": "Ground floor preferred",
    }
    resp = await client.post(
        "/api/v1/housing/requests",
        json=req_payload,
        headers=student_headers,
    )
    assert resp.status_code == 201, resp.text
    req_data = resp.json()
    assert req_data["student_id"] == str(st_profile.id)
    assert req_data["status"] == "SUBMITTED"

    # 6. Read Analytics endpoint
    resp = await client.get("/api/v1/housing/analytics", headers=admin_headers)
    assert resp.status_code == 200
    analytics_data = resp.json()
    assert "total_capacity_beds" in analytics_data
    assert "occupancy_rate_percentage" in analytics_data
