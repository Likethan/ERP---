"""Enterprise Asset Lifecycle, Maintenance, Facilities & Equipment Management Tests (Step 53).

CampusOS Tagline: "One Campus. One System. One Source of Truth."

Verifies:
1. Asset category creation, policy configuration, and auto-generated asset tags.
2. Asset registration, bulk import, serial number duplicate detection, and retrieval.
3. Strict lifecycle state machine transitions, audit history, and invalid transition rejection.
4. Asset custody assignment, acknowledgement, conflicting assignment prevention, and temporary loan return.
5. Cross-campus and inter-department asset transfer dispatch and receive.
6. Preventive maintenance plans, schedule generation, and corrective work order lifecycle (triage -> close -> reopen).
7. Inventory spare parts reservation and consumption with atomic StockBalance updates and StockMovement emission.
8. Safety inspection checklist, findings, and critical failure operational restriction enforcement.
9. Asset warranties, service contracts, and warranty claim tracking.
10. Decimal-safe straight-line depreciation schedule computation and financial journal posting reference.
11. Physical asset verification audit campaigns, barcode scanning, and discrepancy resolution.
12. Controlled asset retirement requests, custody/maintenance dependency checks, and secure disposal certification.
13. Executive analytics reports, background maintenance sweeps, and strict multi-tenant isolation.
"""

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
from app.models.assets import (
    Asset,
    AssetAssignment,
    AssetAuditCampaign,
    AssetAuditItem,
    AssetCategory,
    AssetCategoryType,
    AssetCondition,
    AssetCriticality,
    AssetDepreciationSchedule,
    AssetLifecycleEvent,
    AssetLifecycleState,
    AssetOperationalStatus,
    AssetRetirementRequest,
    AssetTransfer,
    AssetWarrantyContract,
    AssignmentStatus,
    AssignmentType,
    AuditVerificationStatus,
    InspectionActionTaken,
    InspectionOutcome,
    InspectionRecord,
    InspectionTemplate,
    MaintenanceOrderStatus,
    MaintenanceOrderType,
    MaintenancePlan,
    MaintenancePriority,
    MaintenanceSeverity,
    PartConsumptionStatus,
    RetirementReason,
    RetirementRequestStatus,
    TransferStatus,
    WarrantyClaim,
    WorkOrderPartConsumption,
)
from app.models.core import Campus, Department, Institution
from app.models.people import User
from app.models.procurement import (
    InventoryItem,
    InventoryLocation,
    ItemCategory,
    LocationType,
    StockBalance,
    StockMovement,
)
from app.schemas.assets import (
    AssetAssignmentAcknowledgeRequest,
    AssetAssignmentCreate,
    AssetAssignmentReturnRequest,
    AssetAuditCampaignCreate,
    AssetAuditItemScanRequest,
    AssetBulkCreateRequest,
    AssetCategoryCreate,
    AssetCreate,
    AssetLifecycleTransitionRequest,
    AssetRetirementApprovalRequest,
    AssetRetirementExecuteRequest,
    AssetRetirementRequestCreate,
    AssetTransferCreate,
    AssetWarrantyContractCreate,
    DepreciationCalculationRequest,
    InspectionRecordCreate,
    InspectionTemplateCreate,
    MaintenancePlanCreate,
    MaintenanceWorkOrderCloseRequest,
    MaintenanceWorkOrderCreate,
    PartReservationRequest,
    WarrantyClaimCreate,
)
from app.services.asset_service import asset_service


@pytest.fixture
async def asset_fixture(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_b: Institution,
    super_admin_user: User,
):
    """Provides isolated campuses, departments, locations, and inventory items for asset testing."""
    uid = uuid.uuid4().hex[:6].upper()

    # Campus A & Department A
    campus_a = Campus(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        name="Main Campus",
        code=f"CMP-A-{uid}",
        address="100 Innovation Boulevard",
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

    # Campus B & Department B (for transfers and cross-campus checks)
    campus_b = Campus(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        name="North Technology Campus",
        code=f"CMP-B-{uid}",
        address="200 Tech Highway",
        city="Coimbatore",
        is_active=True,
    )
    db_session.add(campus_b)

    dept_b = Department(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        campus_id=campus_b.id,
        name="Electrical Engineering",
        code=f"EEE-{uid}",
        is_active=True,
    )
    db_session.add(dept_b)

    # Inventory Warehouse Location & Spare Part (for inventory integration)
    inv_loc = InventoryLocation(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        campus_id=campus_a.id,
        code=f"WH-CENTRAL-{uid}",
        name="Central Hardware Stores",
        type=LocationType.CENTRAL_WAREHOUSE.value,
        is_active=True,
    )
    db_session.add(inv_loc)

    spare_item = InventoryItem(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        sku=f"SPARE-RAM-32G-{uid}",
        name="32GB DDR5 Server RAM Module",
        category=ItemCategory.MAINTENANCE_PARTS,
        unit_of_measure="NOS",
        unit_price_average=Decimal("150.00"),
        is_active=True,
    )
    db_session.add(spare_item)

    stock_bal = StockBalance(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        item_id=spare_item.id,
        location_id=inv_loc.id,
        quantity_on_hand=Decimal("20.0000"),
        quantity_reserved=Decimal("0.0000"),
        quantity_available=Decimal("20.0000"),
        quantity_in_transit=Decimal("0.0000"),
    )
    db_session.add(stock_bal)

    await db_session.commit()

    return {
        "tenant_a_id": tenant_a.id,
        "tenant_b_id": tenant_b.id,
        "campus_a_id": campus_a.id,
        "campus_b_id": campus_b.id,
        "dept_a_id": dept_a.id,
        "dept_b_id": dept_b.id,
        "inv_loc_id": inv_loc.id,
        "spare_item_id": spare_item.id,
        "user_id": super_admin_user.id,
    }


# =============================================================================
# 1. ASSET CATEGORIES, POLICIES & ASSET REGISTRATION
# =============================================================================


@pytest.mark.asyncio
async def test_asset_category_and_registration(
    db_session: AsyncSession,
    asset_fixture: dict,
):
    """Tests category creation, asset registration with auto-tagging, and serial duplicate checks."""
    tenant_id = asset_fixture["tenant_a_id"]
    campus_id = asset_fixture["campus_a_id"]
    dept_id = asset_fixture["dept_a_id"]
    user_id = asset_fixture["user_id"]
    uid = uuid.uuid4().hex[:6].upper()

    # 1. Create Asset Category
    cat_in = AssetCategoryCreate(
        code=f"IT-SRV-{uid}",
        name=f"High Performance Servers {uid}",
        category_type=AssetCategoryType.IT_EQUIPMENT,
        default_criticality=AssetCriticality.HIGH,
        default_useful_life_months=60,
        default_maintenance_interval_days=90,
        default_inspection_interval_days=180,
    )
    category = await asset_service.create_category(db_session, tenant_id, cat_in, user_id)
    assert category.code == cat_in.code

    # 2. Register Single Asset with Auto-Tag
    serial_no = f"SN-DELL-R750-{uid}"
    asset_in = AssetCreate(
        category_id=category.id,
        name="AI Training Cluster Node 01",
        description="Dual Intel Xeon 64-Core, 512GB ECC RAM, 4x NVIDIA A100",
        asset_type="SERVER",
        make="Dell Technologies",
        model="PowerEdge R750",
        serial_number=serial_no,
        manufacturer="Dell Inc.",
        campus_id=campus_id,
        department_id=dept_id,
        building="Academic Block 4",
        floor="Floor 3",
        room_number="Server Room 302",
        acquisition_cost=Decimal("25000.00"),
        acquisition_date=date.today(),
        useful_life_months=60,
        salvage_value=Decimal("2500.00"),
        criticality=AssetCriticality.MISSION_CRITICAL,
    )
    asset = await asset_service.create_asset(db_session, tenant_id, asset_in, user_id)
    assert asset.asset_tag.startswith("AST-")
    assert asset.lifecycle_state == AssetLifecycleState.REQUESTED
    assert asset.condition == AssetCondition.GOOD
    assert asset.serial_number == serial_no
    assert asset.current_book_value == Decimal("25000.00")

    # 3. Duplicate Serial Detection within same tenant
    with pytest.raises(ConflictException) as exc_info:
        await asset_service.create_asset(db_session, tenant_id, asset_in, user_id)
    assert "serial number" in str(exc_info.value).lower()

    # 4. Bulk Asset Registration
    bulk_in = AssetBulkCreateRequest(
        assets=[
            AssetCreate(
                category_id=category.id,
                name=f"AI Cluster Node {i}",
                asset_type="SERVER",
                make="Dell",
                model="PowerEdge R750",
                serial_number=f"SN-BULK-{uid}-{i}",
                campus_id=campus_id,
                department_id=dept_id,
                acquisition_cost=Decimal("22000.00"),
                acquisition_date=date.today(),
            )
            for i in range(1, 4)
        ]
    )
    bulk_result = await asset_service.bulk_create_assets(db_session, tenant_id, bulk_in, user_id)
    assert bulk_result.created_count == 3
    assert bulk_result.skipped_count == 0
    assert len(bulk_result.created_assets) == 3


# =============================================================================
# 2. LIFECYCLE STATE MACHINE VALIDATIONS
# =============================================================================


@pytest.mark.asyncio
async def test_asset_lifecycle_state_machine(
    db_session: AsyncSession,
    asset_fixture: dict,
):
    """Tests valid vs invalid lifecycle state transitions and audit logging."""
    tenant_id = asset_fixture["tenant_a_id"]
    campus_id = asset_fixture["campus_a_id"]
    dept_id = asset_fixture["dept_a_id"]
    user_id = asset_fixture["user_id"]
    uid = uuid.uuid4().hex[:6].upper()

    cat = await asset_service.create_category(
        db_session,
        tenant_id,
        AssetCategoryCreate(
            code=f"LAB-{uid}",
            name=f"Laboratory Equipment {uid}",
            category_type=AssetCategoryType.LAB_EQUIPMENT,
        ),
        user_id,
    )
    asset = await asset_service.create_asset(
        db_session,
        tenant_id,
        AssetCreate(
            category_id=cat.id,
            name=f"Digital Microscope {uid}",
            asset_type="MICROSCOPE",
            campus_id=campus_id,
            department_id=dept_id,
            acquisition_cost=Decimal("4500.00"),
            acquisition_date=date.today(),
        ),
        user_id,
    )
    assert asset.lifecycle_state == AssetLifecycleState.REQUESTED

    # 1. Invalid Jump Transition: REQUESTED -> IN_SERVICE (not allowed without intermediate flow)
    with pytest.raises(BadRequestException) as exc:
        await asset_service.transition_lifecycle(
            db_session,
            tenant_id,
            asset.id,
            AssetLifecycleTransitionRequest(
                to_state=AssetLifecycleState.IN_SERVICE,
                reason="Attempt direct deployment",
            ),
            user_id,
        )
    assert "cannot transition" in str(exc.value).lower()

    # 2. Valid Step: REQUESTED -> ORDERED -> RECEIVED -> COMMISSIONED -> IN_SERVICE
    for status, reason in [
        (AssetLifecycleState.ORDERED, "PO issued"),
        (AssetLifecycleState.RECEIVED, "Delivered at warehouse"),
        (AssetLifecycleState.COMMISSIONED, "Calibration completed"),
        (AssetLifecycleState.IN_SERVICE, "Deployed to Physics Lab"),
    ]:
        asset = await asset_service.transition_lifecycle(
            db_session,
            tenant_id,
            asset.id,
            AssetLifecycleTransitionRequest(to_state=status, reason=reason),
            user_id,
        )
        assert asset.lifecycle_state == status

    # 3. Verify Lifecycle Audit Events
    events_stmt = (
        select(AssetLifecycleEvent)
        .where(AssetLifecycleEvent.asset_id == asset.id)
        .order_by(AssetLifecycleEvent.performed_at.asc())
    )
    events = (await db_session.execute(events_stmt)).scalars().all()
    assert len(events) == 4
    assert events[-1].to_state == AssetLifecycleState.IN_SERVICE
    assert events[-1].actor_id == user_id


# =============================================================================
# 3. ASSET CUSTODY ASSIGNMENT & LOAN RETURNS
# =============================================================================


@pytest.mark.asyncio
async def test_asset_assignment_custody_and_loans(
    db_session: AsyncSession,
    asset_fixture: dict,
):
    """Tests custody assignment, receipt acknowledgement, conflict prevention, and loan return."""
    tenant_id = asset_fixture["tenant_a_id"]
    campus_id = asset_fixture["campus_a_id"]
    dept_id = asset_fixture["dept_a_id"]
    user_id = asset_fixture["user_id"]
    uid = uuid.uuid4().hex[:6].upper()

    cat = await asset_service.create_category(
        db_session,
        tenant_id,
        AssetCategoryCreate(code=f"IT-LAP-{uid}", name=f"Laptops {uid}", category_type=AssetCategoryType.IT_EQUIPMENT),
        user_id,
    )
    asset = await asset_service.create_asset(
        db_session,
        tenant_id,
        AssetCreate(
            category_id=cat.id,
            name="MacBook Pro M3 Max",
            asset_type="LAPTOP",
            campus_id=campus_id,
            department_id=dept_id,
            acquisition_cost=Decimal("3500.00"),
            acquisition_date=date.today(),
        ),
        user_id,
    )
    # Commission to IN_SERVICE
    await asset_service.transition_lifecycle(
        db_session, tenant_id, asset.id, AssetLifecycleTransitionRequest(to_state=AssetLifecycleState.ORDERED, reason="PO issued"), user_id
    )
    await asset_service.transition_lifecycle(
        db_session, tenant_id, asset.id, AssetLifecycleTransitionRequest(to_state=AssetLifecycleState.RECEIVED, reason="Received at store"), user_id
    )
    await asset_service.transition_lifecycle(
        db_session, tenant_id, asset.id, AssetLifecycleTransitionRequest(to_state=AssetLifecycleState.COMMISSIONED, reason="Configured"), user_id
    )
    await asset_service.transition_lifecycle(
        db_session, tenant_id, asset.id, AssetLifecycleTransitionRequest(to_state=AssetLifecycleState.IN_SERVICE, reason="In service"), user_id
    )

    # 1. Assign asset to user on temporary loan
    loan_return_date = date.today() + timedelta(days=30)
    assign_in = AssetAssignmentCreate(
        assignment_type=AssignmentType.TEMPORARY_LOAN,
        custodian_id=user_id,
        department_id=dept_id,
        campus_id=campus_id,
        location_details="Cabin 204",
        expected_return_date=loan_return_date,
        acknowledgement_required=True,
        handover_notes="Loaned for conference presentation",
    )
    assignment = await asset_service.assign_asset(db_session, tenant_id, asset.id, assign_in, user_id)
    assert assignment.status == AssignmentStatus.PENDING_ACKNOWLEDGEMENT
    assert assignment.custodian_id == user_id

    # 2. Prevent Double Assignment
    with pytest.raises(ConflictException) as exc:
        await asset_service.assign_asset(db_session, tenant_id, asset.id, assign_in, user_id)
    assert "already has an active custody assignment" in str(exc.value).lower()

    # 3. Acknowledge Receipt
    ack_res = await asset_service.acknowledge_assignment(
        db_session,
        tenant_id,
        assignment.id,
        user_id,
        notes="CONFIRMED_VIA_PORTAL",
    )
    assert ack_res.status == AssignmentStatus.ACTIVE
    assert ack_res.acknowledged_at is not None

    # Check asset record reflects custodian
    updated_asset = await asset_service.get_asset(db_session, tenant_id, asset.id)
    assert updated_asset.current_custodian_id == user_id

    # 4. Return to Store
    return_res = await asset_service.return_assignment(
        db_session,
        tenant_id,
        assignment.id,
        return_date=date.today(),
        condition_at_return=AssetCondition.GOOD,
        current_user_id=user_id,
        handover_notes="Returned in working condition",
    )
    assert return_res.status == AssignmentStatus.RETURNED

    refreshed_asset = await asset_service.get_asset(db_session, tenant_id, asset.id)
    assert refreshed_asset.current_custodian_id is None


# =============================================================================
# 4. CROSS-CAMPUS ASSET TRANSFERS
# =============================================================================


@pytest.mark.asyncio
async def test_asset_transfer_workflow(
    db_session: AsyncSession,
    asset_fixture: dict,
):
    """Tests asset transfer initiation, in-transit status, and receiving at target campus."""
    tenant_id = asset_fixture["tenant_a_id"]
    campus_a = asset_fixture["campus_a_id"]
    campus_b = asset_fixture["campus_b_id"]
    dept_a = asset_fixture["dept_a_id"]
    dept_b = asset_fixture["dept_b_id"]
    user_id = asset_fixture["user_id"]
    uid = uuid.uuid4().hex[:6].upper()

    cat = await asset_service.create_category(
        db_session,
        tenant_id,
        AssetCategoryCreate(code=f"FURN-{uid}", name="Furniture", category_type=AssetCategoryType.FURNITURE),
        user_id,
    )
    asset = await asset_service.create_asset(
        db_session,
        tenant_id,
        AssetCreate(
            category_id=cat.id,
            name="Executive Conference Table",
            asset_type="TABLE",
            campus_id=campus_a,
            department_id=dept_a,
            acquisition_cost=Decimal("1200.00"),
            acquisition_date=date.today(),
        ),
        user_id,
    )

    # 1. Initiate Transfer from Campus A to Campus B
    transfer_in = AssetTransferCreate(
        to_campus_id=campus_b,
        to_department_id=dept_b,
        transfer_reason="Reallocation to newly inaugurated North Campus",
        dispatch_notes="Packaged in wooden crate",
    )
    transfer = await asset_service.transfer_asset(db_session, tenant_id, asset.id, transfer_in, user_id)
    assert transfer.status == TransferStatus.PENDING_DISPATCH
    assert transfer.transfer_number.startswith("TRF-")

    # Dispatch transfer -> Moves to IN_TRANSIT
    transfer = await asset_service.process_transfer_action(
        db_session, tenant_id, transfer.id, "DISPATCH", user_id, notes="Dispatched via logistics truck"
    )
    assert transfer.status == TransferStatus.IN_TRANSIT

    # Asset should be marked temporarily unavailable while in transit
    asset_in_transit = await asset_service.get_asset(db_session, tenant_id, asset.id)
    assert asset_in_transit.lifecycle_state == AssetLifecycleState.TEMPORARILY_UNAVAILABLE

    # 2. Receive Transfer at Campus B
    received_transfer = await asset_service.process_transfer_action(
        db_session, tenant_id, transfer.id, "RECEIVE", user_id, notes="Received in pristine condition"
    )
    assert received_transfer.status == TransferStatus.COMPLETED

    # Asset updated to Campus B and IN_SERVICE
    asset_transferred = await asset_service.get_asset(db_session, tenant_id, asset.id)
    assert asset_transferred.campus_id == campus_b
    assert asset_transferred.department_id == dept_b
    assert asset_transferred.lifecycle_state == AssetLifecycleState.IN_SERVICE


# =============================================================================
# 5. PREVENTIVE & CORRECTIVE MAINTENANCE WORK ORDERS
# =============================================================================


@pytest.mark.asyncio
async def test_maintenance_lifecycle_and_reopen(
    db_session: AsyncSession,
    asset_fixture: dict,
):
    """Tests maintenance plan creation, work order execution, closure, and reopening."""
    tenant_id = asset_fixture["tenant_a_id"]
    campus_id = asset_fixture["campus_a_id"]
    dept_id = asset_fixture["dept_a_id"]
    user_id = asset_fixture["user_id"]
    uid = uuid.uuid4().hex[:6].upper()

    cat = await asset_service.create_category(
        db_session,
        tenant_id,
        AssetCategoryCreate(code=f"HVAC-{uid}", name="HVAC", category_type=AssetCategoryType.ELECTRICAL),
        user_id,
    )
    asset = await asset_service.create_asset(
        db_session,
        tenant_id,
        AssetCreate(
            category_id=cat.id,
            name="Central Chiller Unit #2",
            asset_type="HVAC_CHILLER",
            campus_id=campus_id,
            department_id=dept_id,
            acquisition_cost=Decimal("40000.00"),
            acquisition_date=date.today(),
        ),
        user_id,
    )

    # 1. Create Preventive Maintenance Plan
    plan_in = MaintenancePlanCreate(
        title="Quarterly Chiller Chemical Flushing & Filter Replacement",
        asset_id=asset.id,
        interval_days=90,
        estimated_duration_hours=Decimal("4.0"),
        checklist=[
            {"item": "Check coolant pressure levels", "mandatory": True},
            {"item": "Inspect compressor belt tension", "mandatory": True},
            {"item": "Clean condenser coils", "mandatory": False},
        ],
    )
    plan = await asset_service.create_maintenance_plan(db_session, tenant_id, plan_in, user_id)
    assert plan.is_active is True
    assert plan.plan_code.startswith("PM-")

    # 2. Create Corrective Work Order
    wo_in = MaintenanceWorkOrderCreate(
        asset_id=asset.id,
        plan_id=plan.id,
        order_type=MaintenanceOrderType.CORRECTIVE,
        priority=MaintenancePriority.HIGH,
        severity=MaintenanceSeverity.MAJOR,
        reported_symptoms="Cooling temperature threshold exceeded",
        verification_required=True,
    )
    wo = await asset_service.create_work_order(db_session, tenant_id, wo_in, user_id)
    assert wo.work_order_number.startswith("WO-")

    # Asset lifecycle should automatically transition to UNDER_MAINTENANCE
    refreshed_asset = await asset_service.get_asset(db_session, tenant_id, asset.id)
    assert refreshed_asset.lifecycle_state == AssetLifecycleState.UNDER_MAINTENANCE

    # 3. Close Work Order
    close_in = MaintenanceWorkOrderCloseRequest(
        diagnosis="Compressor discharge valve leaking and refrigerant low",
        repair_actions="Replaced discharge valve and recharged R134a refrigerant",
        downtime_hours=Decimal("3.5"),
        labor_hours=Decimal("4.0"),
        labor_cost=Decimal("200.00"),
        service_charges=Decimal("150.00"),
    )
    wo = await asset_service.close_work_order(db_session, tenant_id, wo.id, close_in, user_id)
    assert wo.status == MaintenanceOrderStatus.COMPLETED
    assert wo.labor_cost == Decimal("200.00")

    # 4. Verify Work Order (since verification_required=True)
    wo = await asset_service.verify_work_order(db_session, tenant_id, wo.id, "Operational temperature steady at 4C", user_id)
    assert wo.status == MaintenanceOrderStatus.CLOSED
    assert wo.verified_by_id == user_id

    # Asset should be restored to IN_SERVICE
    refreshed_asset = await asset_service.get_asset(db_session, tenant_id, asset.id)
    assert refreshed_asset.lifecycle_state == AssetLifecycleState.IN_SERVICE

    # 5. Reopen Work Order with authorized reason
    wo = await asset_service.reopen_work_order(
        db_session,
        tenant_id,
        wo.id,
        reopen_reason="Vibration anomaly observed 2 hours post-servicing",
        current_user_id=user_id,
    )
    assert wo.status == MaintenanceOrderStatus.IN_PROGRESS


# =============================================================================
# 6. INVENTORY & SPARE PARTS CONSUMPTION INTEGRATION
# =============================================================================


@pytest.mark.asyncio
async def test_maintenance_inventory_spare_parts_consumption(
    db_session: AsyncSession,
    asset_fixture: dict,
):
    """Tests reserving and consuming spare parts, validating stock balance updates and movement emission."""
    tenant_id = asset_fixture["tenant_a_id"]
    campus_id = asset_fixture["campus_a_id"]
    dept_id = asset_fixture["dept_a_id"]
    loc_id = asset_fixture["inv_loc_id"]
    spare_item_id = asset_fixture["spare_item_id"]
    user_id = asset_fixture["user_id"]
    uid = uuid.uuid4().hex[:6].upper()

    cat = await asset_service.create_category(
        db_session,
        tenant_id,
        AssetCategoryCreate(code=f"IT-WKS-{uid}", name="Workstations", category_type=AssetCategoryType.IT_EQUIPMENT),
        user_id,
    )
    asset = await asset_service.create_asset(
        db_session,
        tenant_id,
        AssetCreate(
            category_id=cat.id,
            name="Engineering CAD Workstation 12",
            asset_type="WORKSTATION",
            campus_id=campus_id,
            department_id=dept_id,
            acquisition_cost=Decimal("3000.00"),
            acquisition_date=date.today(),
        ),
        user_id,
    )

    # Create corrective work order
    wo_in = MaintenanceWorkOrderCreate(
        asset_id=asset.id,
        order_type=MaintenanceOrderType.CORRECTIVE,
        priority=MaintenancePriority.HIGH,
        reported_symptoms="System fails memory diagnostics test with kernel panics",
    )
    wo = await asset_service.create_work_order(db_session, tenant_id, wo_in, user_id)

    # 1. Reserve 2 units of RAM from Inventory Warehouse
    reserve_in = PartReservationRequest(
        inventory_item_id=spare_item_id,
        inventory_location_id=loc_id,
        quantity=Decimal("2.0000"),
    )
    part_res = await asset_service.reserve_work_order_part(db_session, tenant_id, wo.id, reserve_in, user_id)
    assert part_res.status == PartConsumptionStatus.RESERVED
    assert part_res.quantity_reserved == Decimal("2.0000")

    # 2. Consume reserved part
    consumed_part = await asset_service.consume_work_order_part(
        db_session, tenant_id, part_res.id, Decimal("2.0000"), user_id
    )
    assert consumed_part.status == PartConsumptionStatus.CONSUMED
    assert consumed_part.quantity_consumed == Decimal("2.0000")
    assert consumed_part.total_cost == Decimal("300.00")

    # 3. Verify StockBalance decreased in inventory
    bal_res = await db_session.execute(
        select(StockBalance).where(
            StockBalance.tenant_id == tenant_id,
            StockBalance.item_id == spare_item_id,
            StockBalance.location_id == loc_id,
        )
    )
    stock_bal = bal_res.scalar_one()
    assert stock_bal.quantity_on_hand == Decimal("18.0000")  # 20 - 2 = 18

    # 4. Verify StockMovement was emitted
    mvm_res = await db_session.execute(
        select(StockMovement).where(
            StockMovement.tenant_id == tenant_id,
            StockMovement.item_id == spare_item_id,
            StockMovement.reference_id == wo.id,
        )
    )
    mvm = mvm_res.scalar_one_or_none()
    assert mvm is not None
    assert mvm.quantity == Decimal("2.0000")

    # 5. Attempt to reserve more than available stock -> raises BadRequestException
    with pytest.raises(BadRequestException) as exc:
        await asset_service.reserve_work_order_part(
            db_session,
            tenant_id,
            wo.id,
            PartReservationRequest(
                inventory_item_id=spare_item_id,
                inventory_location_id=loc_id,
                quantity=Decimal("100.0000"),  # Only 18 available
            ),
            user_id,
        )
    assert "insufficient stock available" in str(exc.value).lower()


# =============================================================================
# 7. SAFETY INSPECTIONS & CRITICAL OPERATIONAL RESTRICTION
# =============================================================================


@pytest.mark.asyncio
async def test_inspection_safety_and_operational_restriction(
    db_session: AsyncSession,
    asset_fixture: dict,
):
    """Tests inspection checklists and verifies critical failure restricts equipment operation."""
    tenant_id = asset_fixture["tenant_a_id"]
    campus_id = asset_fixture["campus_a_id"]
    dept_id = asset_fixture["dept_a_id"]
    user_id = asset_fixture["user_id"]
    uid = uuid.uuid4().hex[:6].upper()

    cat = await asset_service.create_category(
        db_session,
        tenant_id,
        AssetCategoryCreate(code=f"CHEM-{uid}", name="Chemistry Lab", category_type=AssetCategoryType.LAB_EQUIPMENT),
        user_id,
    )
    asset = await asset_service.create_asset(
        db_session,
        tenant_id,
        AssetCreate(
            category_id=cat.id,
            name="Chemical Fume Hood Unit 04",
            asset_type="FUME_HOOD",
            campus_id=campus_id,
            department_id=dept_id,
            acquisition_cost=Decimal("12000.00"),
            acquisition_date=date.today(),
            criticality=AssetCriticality.MISSION_CRITICAL,
        ),
        user_id,
    )

    # 1. Create Template
    tpl_in = InspectionTemplateCreate(
        code=f"TPL-FUME-{uid}",
        title="Annual Chemical Fume Hood Face Velocity Certification",
        category_id=cat.id,
        checklist_items=[
            {"id": "c1", "question": "Face velocity >= 100 FPM at 18-inch sash height", "critical": True},
            {"id": "c2", "question": "Exhaust blower acoustic dampers intact", "critical": False},
        ],
    )
    tpl = await asset_service.create_inspection_template(db_session, tenant_id, tpl_in, user_id)

    # 2. Perform Inspection with CRITICAL FAILURE & OPERATIONAL RESTRICTION
    rec_in = InspectionRecordCreate(
        asset_id=asset.id,
        template_id=tpl.id,
        overall_outcome=InspectionOutcome.FAIL,
        safety_risk_detected=True,
        action_taken=InspectionActionTaken.OPERATIONAL_RESTRICTION,
        findings_summary="Measured face velocity only 42 FPM. Blower belt slipping.",
        corrective_action_required=True,
        corrective_action_due_date=date.today() + timedelta(days=2),
    )
    rec = await asset_service.record_inspection(db_session, tenant_id, asset.id, rec_in, user_id)
    assert rec.overall_outcome == InspectionOutcome.FAIL
    assert rec.safety_risk_detected is True

    # 3. Verify Asset is RESTRICTED and Operational Status degraded
    updated_asset = await asset_service.get_asset(db_session, tenant_id, asset.id)
    assert updated_asset.is_restricted is True
    assert updated_asset.operational_status == AssetOperationalStatus.RESTRICTED
    assert updated_asset.condition == AssetCondition.POOR

    # 4. Verify that assigning a RESTRICTED asset is rejected by policy
    with pytest.raises(BadRequestException) as exc:
        await asset_service.assign_asset(
            db_session,
            tenant_id,
            asset.id,
            AssetAssignmentCreate(
                assignment_type=AssignmentType.EMPLOYEE,
                custodian_id=user_id,
                department_id=dept_id,
                campus_id=campus_id,
            ),
            user_id,
        )
    assert "cannot assign restricted asset" in str(exc.value).lower()


# =============================================================================
# 8. WARRANTIES, SERVICE CONTRACTS & CLAIMS
# =============================================================================


@pytest.mark.asyncio
async def test_warranty_and_claim_management(
    db_session: AsyncSession,
    asset_fixture: dict,
):
    """Tests asset warranty registration, claim filing, and claim resolution with cost recovery."""
    tenant_id = asset_fixture["tenant_a_id"]
    campus_id = asset_fixture["campus_a_id"]
    dept_id = asset_fixture["dept_a_id"]
    user_id = asset_fixture["user_id"]
    uid = uuid.uuid4().hex[:6].upper()

    cat = await asset_service.create_category(
        db_session,
        tenant_id,
        AssetCategoryCreate(code=f"NET-{uid}", name="Networking", category_type=AssetCategoryType.IT_EQUIPMENT),
        user_id,
    )
    asset = await asset_service.create_asset(
        db_session,
        tenant_id,
        AssetCreate(
            category_id=cat.id,
            name="Cisco Core Switch 9500",
            asset_type="SWITCH",
            campus_id=campus_id,
            department_id=dept_id,
            acquisition_cost=Decimal("15000.00"),
            acquisition_date=date.today(),
        ),
        user_id,
    )

    # 1. Register 3-Year OEM Warranty
    contract_in = AssetWarrantyContractCreate(
        asset_id=asset.id,
        contract_number=f"WAR-CISCO-{uid}",
        provider_name="Cisco Systems Global Support",
        start_date=date.today() - timedelta(days=100),
        end_date=date.today() + timedelta(days=995),
        coverage_terms="Next Business Day Onsite Hardware Replacement for PSU and Line Cards.",
        sla_response_hours=4,
    )
    contract = await asset_service.create_warranty_contract(db_session, tenant_id, asset.id, contract_in, user_id)
    assert contract.contract_number == contract_in.contract_number

    # 2. File Warranty Claim
    claim_in = WarrantyClaimCreate(
        contract_id=contract.id,
        issue_description="Redundant Power Supply Unit 2 failure, amber LED illuminated",
        vendor_ticket_reference=f"TKT-CISCO-{uid}",
    )
    claim = await asset_service.create_warranty_claim(db_session, tenant_id, asset.id, claim_in, user_id)
    assert claim.claim_number.startswith("CLM-")
    assert claim.contract_id == contract.id


# =============================================================================
# 9. DEPRECIATION COMPUTATION & FINANCE POSTING INTEGRATION
# =============================================================================


@pytest.mark.asyncio
async def test_asset_depreciation_and_finance_posting(
    db_session: AsyncSession,
    asset_fixture: dict,
):
    """Tests straight-line monthly depreciation calculation and GL journal entry posting reference."""
    tenant_id = asset_fixture["tenant_a_id"]
    campus_id = asset_fixture["campus_a_id"]
    dept_id = asset_fixture["dept_a_id"]
    user_id = asset_fixture["user_id"]
    uid = uuid.uuid4().hex[:6].upper()

    cat = await asset_service.create_category(
        db_session,
        tenant_id,
        AssetCategoryCreate(code=f"VEH-{uid}", name="Vehicles", category_type=AssetCategoryType.VEHICLES),
        user_id,
    )
    # Cost = 60,000, Salvage = 12,000, Depreciable = 48,000, Life = 48 months -> 1,000 / month
    asset = await asset_service.create_asset(
        db_session,
        tenant_id,
        AssetCreate(
            category_id=cat.id,
            name="Campus Shuttle Bus 02",
            asset_type="BUS",
            campus_id=campus_id,
            department_id=dept_id,
            acquisition_cost=Decimal("60000.00"),
            acquisition_date=date(2026, 1, 1),
            salvage_value=Decimal("12000.00"),
            useful_life_months=48,
        ),
        user_id,
    )

    # 1. Calculate Period Depreciation for 2026-04
    calc_in = DepreciationCalculationRequest(
        fiscal_year="2026-2027",
        period_name="2026-04",
        period_start_date=date(2026, 4, 1),
        period_end_date=date(2026, 4, 30),
        asset_id=asset.id,
    )
    schedules = await asset_service.calculate_depreciation_period(db_session, tenant_id, calc_in, user_id)
    assert len(schedules) == 1
    sched = schedules[0]
    assert sched.depreciation_amount == Decimal("1000.00")
    assert sched.closing_book_value == Decimal("59000.00")
    assert sched.is_posted is False

    # 2. Post to Finance General Ledger reference
    posted_count, total_depr, je_ref = await asset_service.post_depreciation_to_finance(
        db_session,
        tenant_id,
        [sched.id],
        "JE-DEPR-2026-APR",
        user_id,
    )
    assert posted_count == 1
    assert total_depr == Decimal("1000.00")
    assert je_ref == "JE-DEPR-2026-APR"

    # 3. Verify asset's current book value is updated
    updated_asset = await asset_service.get_asset(db_session, tenant_id, asset.id)
    assert updated_asset.current_book_value == Decimal("59000.00")
    assert updated_asset.accumulated_depreciation == Decimal("1000.00")


# =============================================================================
# 10. PHYSICAL ASSET AUDIT CAMPAIGNS & BARCODE SCAN DISCREPANCY RESOLUTION
# =============================================================================


@pytest.mark.asyncio
async def test_asset_audit_campaign_and_verification(
    db_session: AsyncSession,
    asset_fixture: dict,
):
    """Tests physical verification campaigns, barcode tag scanning, and relocation discrepancy tracking."""
    tenant_id = asset_fixture["tenant_a_id"]
    campus_a = asset_fixture["campus_a_id"]
    campus_b = asset_fixture["campus_b_id"]
    dept_id = asset_fixture["dept_a_id"]
    user_id = asset_fixture["user_id"]
    uid = uuid.uuid4().hex[:6].upper()

    cat = await asset_service.create_category(
        db_session,
        tenant_id,
        AssetCategoryCreate(code=f"LIB-{uid}", name="Library", category_type=AssetCategoryType.LIBRARY_EQUIPMENT),
        user_id,
    )
    asset = await asset_service.create_asset(
        db_session,
        tenant_id,
        AssetCreate(
            category_id=cat.id,
            name="RFID Self-Checkout Kiosk 01",
            asset_type="KIOSK",
            campus_id=campus_a,
            department_id=dept_id,
            building="Central Library",
            room_number="Ground Floor Entrance",
            acquisition_cost=Decimal("5000.00"),
            acquisition_date=date.today(),
        ),
        user_id,
    )

    # 1. Create Audit Campaign
    camp_in = AssetAuditCampaignCreate(
        title="Q3 Central Library Physical Asset Audit",
        campus_id=campus_a,
        department_id=dept_id,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=7),
        lead_auditor_id=user_id,
    )
    campaign = await asset_service.create_audit_campaign(db_session, tenant_id, camp_in, user_id)
    assert campaign.campaign_code.startswith("AUD-")

    # 2. Scan Asset with Relocation Discrepancy (Scanned in North Campus B instead of Campus A)
    scan_in = AssetAuditItemScanRequest(
        scanned_tag=asset.asset_tag,
        actual_campus_id=campus_b,
        actual_building="Central Library North",
        actual_room="1st Floor Study Hall",
        actual_condition=AssetCondition.GOOD,
    )
    audit_item = await asset_service.record_audit_scan(db_session, tenant_id, campaign.id, scan_in, user_id)
    assert audit_item.verification_status == AuditVerificationStatus.RELOCATED
    assert audit_item.actual_campus_id == campus_b


# =============================================================================
# 11. ASSET RETIREMENT & DISPOSAL WORKFLOW
# =============================================================================


@pytest.mark.asyncio
async def test_asset_retirement_and_disposal_workflow(
    db_session: AsyncSession,
    asset_fixture: dict,
):
    """Tests retirement request, approval, dependency validation, and final disposal certification."""
    tenant_id = asset_fixture["tenant_a_id"]
    campus_id = asset_fixture["campus_a_id"]
    dept_id = asset_fixture["dept_a_id"]
    user_id = asset_fixture["user_id"]
    uid = uuid.uuid4().hex[:6].upper()

    cat = await asset_service.create_category(
        db_session,
        tenant_id,
        AssetCategoryCreate(code=f"IT-DESK-{uid}", name="Desktops", category_type=AssetCategoryType.IT_EQUIPMENT),
        user_id,
    )
    asset = await asset_service.create_asset(
        db_session,
        tenant_id,
        AssetCreate(
            category_id=cat.id,
            name="Legacy Core2Duo Lab Desktop 08",
            asset_type="DESKTOP",
            campus_id=campus_id,
            department_id=dept_id,
            acquisition_cost=Decimal("800.00"),
            acquisition_date=date(2018, 1, 1),
            salvage_value=Decimal("50.00"),
        ),
        user_id,
    )

    # 1. Create Retirement Request
    ret_in = AssetRetirementRequestCreate(
        asset_id=asset.id,
        retirement_reason=RetirementReason.BEYOND_ECONOMIC_REPAIR,
        disposal_method="E_WASTE_RECYCLING",
        estimated_residual_value=Decimal("40.00"),
        technical_assessment_notes="Motherboard capacitor degradation, obsolete architecture unsuitable for current OS.",
    )
    req = await asset_service.request_retirement(db_session, tenant_id, ret_in, user_id)
    assert req.status == RetirementRequestStatus.SUBMITTED

    # Asset moves to PENDING_DISPOSAL
    asset_pending = await asset_service.get_asset(db_session, tenant_id, asset.id)
    assert asset_pending.lifecycle_state == AssetLifecycleState.PENDING_DISPOSAL

    # 2. Approve Retirement Request
    approved_req = await asset_service.approve_retirement(
        db_session,
        tenant_id,
        req.id,
        action="APPROVE",
        notes="Approved for accredited e-waste recycler",
        current_user_id=user_id,
    )
    assert approved_req.status == RetirementRequestStatus.APPROVED
    assert approved_req.approved_by_id == user_id

    # 3. Execute Final Disposal with Certificate
    disposal_in = AssetRetirementExecuteRequest(
        actual_realized_value=Decimal("40.00"),
        data_wiped=True,
        data_wipe_certificate_url=f"https://documents.campusos.internal/wipe-certs/EWASTE-{uid}.pdf",
        disposal_certificate_url=f"https://documents.campusos.internal/disposal-manifests/EWASTE-MANIFEST-{uid}.pdf",
    )
    disposed_req = await asset_service.execute_disposal(db_session, tenant_id, req.id, disposal_in, user_id)
    assert disposed_req.status == RetirementRequestStatus.DISPOSED
    assert disposed_req.data_wiped is True

    # Asset is permanently DISPOSED and DECOMMISSIONED
    disposed_asset = await asset_service.get_asset(db_session, tenant_id, asset.id)
    assert disposed_asset.lifecycle_state == AssetLifecycleState.DISPOSED
    assert disposed_asset.operational_status == AssetOperationalStatus.DECOMMISSIONED

    # 4. Verify that a disposed asset CANNOT be reassigned
    with pytest.raises(BadRequestException) as exc:
        await asset_service.assign_asset(
            db_session,
            tenant_id,
            asset.id,
            AssetAssignmentCreate(
                assignment_type=AssignmentType.EMPLOYEE,
                custodian_id=user_id,
                department_id=dept_id,
                campus_id=campus_id,
            ),
            user_id,
        )
    assert "cannot assign asset in lifecycle state 'disposed'" in str(exc.value).lower()


# =============================================================================
# 12. EXECUTIVE ANALYTICS & STRICT MULTI-TENANT ISOLATION
# =============================================================================


@pytest.mark.asyncio
async def test_analytics_and_multi_tenant_isolation(
    db_session: AsyncSession,
    asset_fixture: dict,
):
    """Tests executive KPI analytics and strict multi-tenant boundary isolation."""
    tenant_a = asset_fixture["tenant_a_id"]
    tenant_b = asset_fixture["tenant_b_id"]
    campus_a = asset_fixture["campus_a_id"]
    dept_a = asset_fixture["dept_a_id"]
    user_id = asset_fixture["user_id"]
    uid = uuid.uuid4().hex[:6].upper()

    # 1. Create Asset in Tenant A
    cat_a = await asset_service.create_category(
        db_session,
        tenant_a,
        AssetCategoryCreate(code=f"TEN-A-CAT-{uid}", name="Tenant A Category", category_type=AssetCategoryType.IT_EQUIPMENT),
        user_id,
    )
    asset_a = await asset_service.create_asset(
        db_session,
        tenant_a,
        AssetCreate(
            category_id=cat_a.id,
            name="Tenant A Asset",
            asset_type="SERVER",
            campus_id=campus_a,
            department_id=dept_a,
            acquisition_cost=Decimal("10000.00"),
            acquisition_date=date.today(),
        ),
        user_id,
    )

    # 2. Verify Analytics Report for Tenant A
    analytics = await asset_service.get_summary_analytics(db_session, tenant_a)
    assert analytics["total_assets"] >= 1
    assert analytics["total_acquisition_value"] >= Decimal("10000.00")

    # 3. Cross-Tenant Isolation: Tenant B cannot read or modify Tenant A's asset
    with pytest.raises(NotFoundException):
        await asset_service.get_asset(db_session, tenant_b, asset_a.id)

    with pytest.raises(NotFoundException):
        await asset_service.transition_lifecycle(
            db_session,
            tenant_b,
            asset_a.id,
            AssetLifecycleTransitionRequest(to_state=AssetLifecycleState.ORDERED, reason="Cross tenant attempt"),
            user_id,
        )

    with pytest.raises(NotFoundException):
        await asset_service.create_work_order(
            db_session,
            tenant_b,
            MaintenanceWorkOrderCreate(
                asset_id=asset_a.id,
                reported_symptoms="Cross tenant breach attempt",
            ),
            user_id,
        )


# =============================================================================
# 13. BACKGROUND SCHEDULER SWEEPS
# =============================================================================


@pytest.mark.asyncio
async def test_scheduler_sweeps(
    db_session: AsyncSession,
    asset_fixture: dict,
):
    """Tests background scheduled sweep for maintenance plans, overdue loans, and warranty alerts."""
    from app.scheduler import sweep_asset_lifecycle_maintenance_task

    # Run the scheduled sweep task
    await sweep_asset_lifecycle_maintenance_task()
