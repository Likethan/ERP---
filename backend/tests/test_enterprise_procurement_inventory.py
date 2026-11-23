"""Enterprise Procurement, Vendor Management, Purchase Orders & Inventory Control Tests (Step 50).

CampusOS Tagline: "One Campus. One System. One Source of Truth."

Verifies:
1. Vendor registration, contacts, duplicate detection, performance review, and lifecycle transitions.
2. Departmental purchase requisition creation, line calculation, and multi-level approval workflows.
3. RFQ issuance, vendor quotation submission, and weighted scoring evaluation.
4. Purchase order creation, server-side decimal precision, approved vendor enforcement, and versioned amendments.
5. Goods receipt note (GRN) processing, over-receipt protection, and quality inspection quarantine.
6. Multi-location inventory control, immutable stock movement ledger, negative stock prevention, and atomic transfers.
7. Internal departmental stock supply requests, reservation checks, and store fulfillment.
8. Three-way invoice matching (PO vs GRN vs Supplier Invoice) and discrepancy override management.
9. Vendor returns (RTV) and credit note tracking.
10. Procurement KPI summaries and inventory valuation analytics.
11. Strict multi-tenant isolation and security boundary enforcement.
"""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.core import Campus, Department, Institution
from app.models.people import User
from app.models.procurement import (
    AwardDecision,
    GoodsReceiptStatus,
    InternalRequestStatus,
    InvoiceMatchStatus,
    ItemCategory,
    LocationType,
    MovementType,
    PurchaseOrderStatus,
    QualityInspectionStatus,
    RequisitionPriority,
    RequisitionStatus,
    VendorCategory,
    VendorReturnReason,
    VendorReturnStatus,
    VendorStatus,
)
from app.schemas.procurement import (
    GoodsReceiptCreate,
    GoodsReceiptLineCreate,
    InternalStockRequestCreate,
    InternalStockRequestFulfillRequest,
    InternalStockRequestLineCreate,
    InventoryItemCreate,
    InventoryLocationCreate,
    PurchaseOrderAmendmentCreate,
    PurchaseOrderCreate,
    PurchaseOrderLineCreate,
    PurchaseRequisitionApprovalRequest,
    PurchaseRequisitionCreate,
    PurchaseRequisitionLineCreate,
    QualityInspectionRecordRequest,
    QuotationEvaluationCreate,
    QuotationRequestCreate,
    StockMovementCreate,
    StockTransferRequest,
    SupplierInvoiceMatchCreate,
    SupplierInvoiceMatchOverrideRequest,
    VendorContactCreate,
    VendorCreate,
    VendorDuplicateCheckRequest,
    VendorPerformanceReviewCreate,
    VendorQuotationCreate,
    VendorReturnCreate,
    VendorReturnStatusUpdateRequest,
    VendorStatusTransitionRequest,
)
from app.services.procurement_service import procurement_service


@pytest.fixture
async def procurement_fixture(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_b: Institution,
    super_admin_user: User,
):
    """Provides isolated campus, department, and users for procurement testing."""
    uid = uuid.uuid4().hex[:6]

    # Tenant A Campus & Department
    campus_a = Campus(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        name="Main Campus",
        code=f"CMP-A-{uid}",
        address="100 University Avenue",
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

    # Tenant B Campus
    campus_b = Campus(
        id=uuid.uuid4(),
        tenant_id=tenant_b.id,
        name="Satellite Campus",
        code=f"CMP-B-{uid}",
        address="200 Tech Highway",
        city="Chennai",
        is_active=True,
    )
    db_session.add(campus_b)

    await db_session.commit()

    return {
        "tenant_a_id": tenant_a.id,
        "tenant_b_id": tenant_b.id,
        "campus_a_id": campus_a.id,
        "campus_b_id": campus_b.id,
        "dept_a_id": dept_a.id,
        "user_id": super_admin_user.id,
    }


# =============================================================================
# 1. VENDOR LIFECYCLE & DUPLICATE DETECTION
# =============================================================================


@pytest.mark.asyncio
async def test_vendor_lifecycle_and_duplicate_detection(
    db_session: AsyncSession,
    procurement_fixture: dict,
):
    """Tests vendor registration, contacts, duplicate detection, status transition, and reviews."""
    tenant_id = procurement_fixture["tenant_a_id"]
    user_id = procurement_fixture["user_id"]
    uid = uuid.uuid4().hex[:6]

    # 1. Register vendor with contact
    vendor_in = VendorCreate(
        code=f"VEN-{uid}",
        name=f"Apex Lab Instruments {uid}",
        legal_name=f"Apex Scientific Solutions Pvt Ltd {uid}",
        category=VendorCategory.LABORATORY_EQUIPMENT,
        tax_identifier=f"GSTIN33AAAAA{uid}Z1",
        email=f"procurement_{uid}@apexscientific.com",
        phone="+919876543200",
        address_line1="42 Science Park",
        city="Bengaluru",
        state="Karnataka",
        postal_code="560001",
        contacts=[
            VendorContactCreate(
                name="Dr. K. Raman",
                designation="Sales Director",
                email=f"raman_{uid}@apexscientific.com",
                phone="+919876543201",
                is_primary=True,
            )
        ],
    )
    vendor = await procurement_service.create_vendor(db_session, tenant_id, vendor_in, user_id)
    assert vendor.status == VendorStatus.PENDING
    assert vendor.code == vendor_in.code
    assert len(vendor.contacts) == 1
    assert vendor.contacts[0].is_primary is True

    # 2. Check duplicate vendor detection
    dup_check = await procurement_service.check_vendor_duplicates(
        db_session,
        tenant_id,
        VendorDuplicateCheckRequest(
            legal_name=vendor.legal_name,
            tax_identifier=vendor.tax_identifier,
        ),
    )
    assert dup_check.has_potential_duplicates is True
    assert len(dup_check.matches) > 0
    assert dup_check.matches[0].vendor_id == vendor.id

    # 3. Approve vendor
    approved_vendor = await procurement_service.transition_vendor_status(
        db_session,
        tenant_id,
        vendor.id,
        VendorStatusTransitionRequest(status=VendorStatus.APPROVED, reason="Credentials verified"),
        user_id,
    )
    assert approved_vendor.status == VendorStatus.APPROVED
    assert approved_vendor.is_verified is True
    assert approved_vendor.verified_at is not None

    # 4. Record vendor performance review
    review = await procurement_service.create_vendor_performance_review(
        db_session,
        tenant_id,
        vendor.id,
        VendorPerformanceReviewCreate(
            review_date=date.today(),
            delivery_score=5,
            quality_score=4,
            pricing_score=5,
            comments="Excellent supply quality and turnaround.",
            recommendation="EXPAND_CONTRACT",
        ),
        user_id,
    )
    assert review.overall_score == Decimal("4.67")

    # Refresh vendor
    updated_v = await procurement_service.get_vendor(db_session, tenant_id, vendor.id)
    assert updated_v.rating_score > Decimal("4.00")


# =============================================================================
# 2. PURCHASE REQUISITION & APPROVAL WORKFLOW
# =============================================================================


@pytest.mark.asyncio
async def test_purchase_requisition_workflow(
    db_session: AsyncSession,
    procurement_fixture: dict,
):
    """Tests requisition creation, line calculation, and approval/rejection lifecycle."""
    tenant_id = procurement_fixture["tenant_a_id"]
    campus_id = procurement_fixture["campus_a_id"]
    dept_id = procurement_fixture["dept_a_id"]
    user_id = procurement_fixture["user_id"]
    uid = uuid.uuid4().hex[:6]

    req_in = PurchaseRequisitionCreate(
        requisition_number=f"PR-{uid}",
        department_id=dept_id,
        campus_id=campus_id,
        title="Computer Lab Hardware Upgrades",
        justification="Mandatory upgrade for accredited curriculum AI lab.",
        category=VendorCategory.TECHNOLOGY,
        priority=RequisitionPriority.HIGH,
        required_date=date.today(),
        delivery_location="Room 302, Technology Block",
        lines=[
            PurchaseRequisitionLineCreate(
                item_description="High-Performance GPU Workstation",
                unit_of_measure="UNIT",
                quantity_requested=Decimal("5.00"),
                estimated_unit_price=Decimal("120000.00"),
                specifications="RTX 4090, 64GB RAM, 2TB NVMe",
            ),
            PurchaseRequisitionLineCreate(
                item_description="Smart Display 75-inch",
                unit_of_measure="UNIT",
                quantity_requested=Decimal("2.00"),
                estimated_unit_price=Decimal("75000.00"),
            ),
        ],
    )

    req = await procurement_service.create_requisition(db_session, tenant_id, req_in, user_id)
    assert req.status == RequisitionStatus.SUBMITTED
    # Total = 5 * 120,000 + 2 * 75,000 = 600,000 + 150,000 = 750,000.00
    assert req.estimated_total_amount == Decimal("750000.00")
    assert len(req.lines) == 2

    # Approve requisition
    approved_req = await procurement_service.review_requisition(
        db_session,
        tenant_id,
        req.id,
        PurchaseRequisitionApprovalRequest(action="APPROVE", comments="Approved within budget code CSE-AI-2026"),
        user_id,
    )
    assert approved_req.status == RequisitionStatus.APPROVED
    assert approved_req.approved_by_id == user_id
    assert approved_req.approved_at is not None


# =============================================================================
# 3. REQUEST FOR QUOTATION (RFQ) & EVALUATION
# =============================================================================


@pytest.mark.asyncio
async def test_rfq_and_quotation_evaluation(
    db_session: AsyncSession,
    procurement_fixture: dict,
):
    """Tests RFQ creation, vendor quotations, and multi-criteria evaluation."""
    tenant_id = procurement_fixture["tenant_a_id"]
    campus_id = procurement_fixture["campus_a_id"]
    dept_id = procurement_fixture["dept_a_id"]
    user_id = procurement_fixture["user_id"]
    uid = uuid.uuid4().hex[:6]

    # Setup approved requisition
    req = await procurement_service.create_requisition(
        db_session,
        tenant_id,
        PurchaseRequisitionCreate(
            requisition_number=f"PR-RFQ-{uid}",
            department_id=dept_id,
            campus_id=campus_id,
            title="Lab Test Tubes & Glassware",
            justification="Annual science consumable purchase",
            required_date=date.today(),
            delivery_location="Chemistry Store",
            lines=[
                PurchaseRequisitionLineCreate(
                    item_description="Borosilicate Beaker Set",
                    quantity_requested=Decimal("100.00"),
                    estimated_unit_price=Decimal("250.00"),
                )
            ],
        ),
        user_id,
    )
    await procurement_service.review_requisition(
        db_session, tenant_id, req.id, PurchaseRequisitionApprovalRequest(action="APPROVE"), user_id
    )

    # Issue RFQ
    rfq = await procurement_service.create_rfq(
        db_session,
        tenant_id,
        QuotationRequestCreate(
            rfq_number=f"RFQ-{uid}",
            requisition_id=req.id,
            title="Tender for Chemistry Glassware",
            deadline_date=date.today(),
            evaluation_criteria_json={"price_weight": 0.6, "quality_weight": 0.2, "delivery_weight": 0.2},
        ),
        user_id,
    )
    assert rfq.rfq_number == f"RFQ-{uid}"

    # Setup Vendor 1
    v1 = await procurement_service.create_vendor(
        db_session,
        tenant_id,
        VendorCreate(
            code=f"VEN-Q1-{uid}",
            name=f"Supplier One {uid}",
            legal_name=f"Supplier One Ltd {uid}",
            email=f"q1_{uid}@supplier.com",
            phone="+919876543211",
            address_line1="1 Trade Lane",
            city="Coimbatore",
            state="Tamil Nadu",
            postal_code="641001",
        ),
        user_id,
    )
    await procurement_service.transition_vendor_status(
        db_session, tenant_id, v1.id, VendorStatusTransitionRequest(status=VendorStatus.APPROVED), user_id
    )

    # Submit quotation
    q1 = await procurement_service.submit_vendor_quotation(
        db_session,
        tenant_id,
        VendorQuotationCreate(
            rfq_id=rfq.id,
            vendor_id=v1.id,
            quotation_reference=f"QUO-{uid}-001",
            submission_date=date.today(),
            validity_until=date.today(),
            total_quoted_amount=Decimal("22000.00"),
            delivery_lead_days=7,
            warranty_months=12,
        ),
        user_id,
    )
    assert q1.total_quoted_amount == Decimal("22000.00")

    # Evaluate quotation
    evaluation = await procurement_service.evaluate_quotation(
        db_session,
        tenant_id,
        QuotationEvaluationCreate(
            rfq_id=rfq.id,
            evaluation_date=date.today(),
            scoring_details_json={"price_score": 90, "quality_score": 85, "delivery_score": 95},
            recommended_vendor_id=v1.id,
            award_decision=AwardDecision.AWARDED,
        ),
        user_id,
    )
    assert evaluation.award_decision == AwardDecision.AWARDED


# =============================================================================
# 4. PURCHASE ORDER CREATION, DECIMAL TOTALS & AMENDMENT
# =============================================================================


@pytest.mark.asyncio
async def test_purchase_order_creation_and_amendments(
    db_session: AsyncSession,
    procurement_fixture: dict,
):
    """Tests PO creation, strict approved vendor checks, decimal arithmetic, and amendments."""
    tenant_id = procurement_fixture["tenant_a_id"]
    campus_id = procurement_fixture["campus_a_id"]
    user_id = procurement_fixture["user_id"]
    uid = uuid.uuid4().hex[:6]

    # Create unapproved vendor
    vendor = await procurement_service.create_vendor(
        db_session,
        tenant_id,
        VendorCreate(
            code=f"VEN-PO-{uid}",
            name=f"Vendor PO {uid}",
            legal_name=f"Vendor PO Legal {uid}",
            email=f"vpo_{uid}@vendor.com",
            phone="+919876543222",
            address_line1="10 Market Street",
            city="Coimbatore",
            state="Tamil Nadu",
            postal_code="641001",
        ),
        user_id,
    )

    po_in = PurchaseOrderCreate(
        po_number=f"PO-{uid}",
        vendor_id=vendor.id,
        campus_id=campus_id,
        order_date=date.today(),
        expected_delivery_date=date.today(),
        delivery_address="Main Store, North Gate",
        billing_address="Finance Office, Admin Block",
        payment_terms="Net 30",
        discount_amount=Decimal("500.00"),
        lines=[
            PurchaseOrderLineCreate(
                item_description="Industrial Ethernet Switch 24-Port",
                quantity_ordered=Decimal("10.00"),
                unit_price=Decimal("15000.00"),
                tax_rate=Decimal("18.00"),
            ),
            PurchaseOrderLineCreate(
                item_description="Cat6A Patch Cables 2m (Pack of 50)",
                quantity_ordered=Decimal("5.00"),
                unit_price=Decimal("2000.00"),
                tax_rate=Decimal("18.00"),
            ),
        ],
    )

    # 1. Unapproved vendor should be rejected
    with pytest.raises(BadRequestException, match="APPROVED vendor"):
        await procurement_service.create_purchase_order(db_session, tenant_id, po_in, user_id)

    # 2. Approve vendor
    await procurement_service.transition_vendor_status(
        db_session, tenant_id, vendor.id, VendorStatusTransitionRequest(status=VendorStatus.APPROVED), user_id
    )

    # 3. Create PO with server-side decimal precision
    # Line 1: 10 * 15000 = 150000; Tax (18%) = 27000; Total = 177000.00
    # Line 2: 5 * 2000 = 10000; Tax (18%) = 1800; Total = 11800.00
    # Subtotal = 160000.00, Tax = 28800.00, Discount = 500.00
    # Grand Total = 160000 + 28800 - 500 = 188300.00
    po = await procurement_service.create_purchase_order(db_session, tenant_id, po_in, user_id)
    assert po.subtotal == Decimal("160000.00")
    assert po.tax_amount == Decimal("28800.00")
    assert po.discount_amount == Decimal("500.00")
    assert po.total_amount == Decimal("188300.00")
    assert po.status == PurchaseOrderStatus.DRAFT

    # 4. Issue Purchase Order
    issued_po = await procurement_service.issue_purchase_order(db_session, tenant_id, po.id, user_id)
    assert issued_po.status == PurchaseOrderStatus.ISSUED
    assert issued_po.issued_at is not None

    # 5. Create versioned amendment
    amendment = await procurement_service.create_po_amendment(
        db_session,
        tenant_id,
        po.id,
        PurchaseOrderAmendmentCreate(
            reason="Vendor extended warranty added by agreement",
            changes_json={"warranty_extended": True},
        ),
        user_id,
    )
    assert amendment.amendment_number == 1

    # Verify PO version incremented
    reloaded_po = await procurement_service.get_purchase_order(db_session, tenant_id, po.id)
    assert reloaded_po.version_number == 2


# =============================================================================
# 5. GOODS RECEIPT, OVER-RECEIPT PREVENTION & QUALITY INSPECTION
# =============================================================================


@pytest.mark.asyncio
async def test_goods_receipt_and_over_receipt_prevention(
    db_session: AsyncSession,
    procurement_fixture: dict,
):
    """Tests goods receipts, prevention of over-receipt, and quality inspection workflows."""
    tenant_id = procurement_fixture["tenant_a_id"]
    campus_id = procurement_fixture["campus_a_id"]
    user_id = procurement_fixture["user_id"]
    uid = uuid.uuid4().hex[:6]

    # Setup approved vendor
    vendor = await procurement_service.create_vendor(
        db_session,
        tenant_id,
        VendorCreate(
            code=f"VEN-GRN-{uid}",
            name=f"Hardware Supplier {uid}",
            legal_name=f"Hardware Supplier Ltd {uid}",
            email=f"grn_{uid}@supplier.com",
            phone="+919876543233",
            address_line1="55 Ring Road",
            city="Coimbatore",
            state="Tamil Nadu",
            postal_code="641001",
        ),
        user_id,
    )
    await procurement_service.transition_vendor_status(
        db_session, tenant_id, vendor.id, VendorStatusTransitionRequest(status=VendorStatus.APPROVED), user_id
    )

    # Create & issue PO for 10 units
    po = await procurement_service.create_purchase_order(
        db_session,
        tenant_id,
        PurchaseOrderCreate(
            po_number=f"PO-GRN-{uid}",
            vendor_id=vendor.id,
            campus_id=campus_id,
            order_date=date.today(),
            expected_delivery_date=date.today(),
            delivery_address="Main Gate Warehouse",
            billing_address="Finance Office",
            lines=[
                PurchaseOrderLineCreate(
                    item_description="High-Speed Laser Printer",
                    quantity_ordered=Decimal("10.00"),
                    unit_price=Decimal("25000.00"),
                )
            ],
        ),
        user_id,
    )
    await procurement_service.issue_purchase_order(db_session, tenant_id, po.id, user_id)

    po_line_id = po.lines[0].id

    # 1. Partial receipt of 6 units
    grn1 = await procurement_service.create_goods_receipt(
        db_session,
        tenant_id,
        GoodsReceiptCreate(
            grn_number=f"GRN-{uid}-001",
            po_id=po.id,
            vendor_id=vendor.id,
            receipt_date=date.today(),
            carrier_name="BlueDart",
            delivery_note_reference=f"DN-{uid}-1",
            lines=[
                GoodsReceiptLineCreate(
                    po_line_id=po_line_id,
                    item_description="High-Speed Laser Printer",
                    quantity_received=Decimal("6.00"),
                    quantity_accepted=Decimal("6.00"),
                )
            ],
        ),
        user_id,
    )
    assert grn1.status == GoodsReceiptStatus.RECEIVED

    # Verify PO is PARTIALLY_DELIVERED
    reloaded_po = await procurement_service.get_purchase_order(db_session, tenant_id, po.id)
    assert reloaded_po.status == PurchaseOrderStatus.PARTIALLY_DELIVERED

    # 2. Over-receipt check: Attempting to receive 5 more (6 + 5 = 11 > 10 ordered) must fail!
    with pytest.raises(BadRequestException, match="exceeds remaining order balance"):
        await procurement_service.create_goods_receipt(
            db_session,
            tenant_id,
            GoodsReceiptCreate(
                grn_number=f"GRN-{uid}-OVER",
                po_id=po.id,
                vendor_id=vendor.id,
                receipt_date=date.today(),
                lines=[
                    GoodsReceiptLineCreate(
                        po_line_id=po_line_id,
                        item_description="High-Speed Laser Printer",
                        quantity_received=Decimal("5.00"),
                        quantity_accepted=Decimal("5.00"),
                    )
                ],
            ),
            user_id,
        )

    # 3. Record Quality Inspection on GRN 1
    inspected_grn = await procurement_service.record_quality_inspection(
        db_session,
        tenant_id,
        grn1.id,
        QualityInspectionRecordRequest(
            quality_status=QualityInspectionStatus.PASSED,
            inspection_notes="All 6 printers fully functional and calibrated.",
        ),
        user_id,
    )
    assert inspected_grn.status == GoodsReceiptStatus.ACCEPTED


# =============================================================================
# 6. INVENTORY CONTROL, STOCK MOVEMENTS & ATOMIC TRANSFERS
# =============================================================================


@pytest.mark.asyncio
async def test_inventory_control_and_stock_movements(
    db_session: AsyncSession,
    procurement_fixture: dict,
):
    """Tests multi-location inventory, stock receipt, negative stock prevention, and transfers."""
    tenant_id = procurement_fixture["tenant_a_id"]
    campus_id = procurement_fixture["campus_a_id"]
    user_id = procurement_fixture["user_id"]
    uid = uuid.uuid4().hex[:6]

    # Create locations
    central_wh = await procurement_service.create_location(
        db_session,
        tenant_id,
        InventoryLocationCreate(
            campus_id=campus_id,
            code=f"WH-CTR-{uid}",
            name="Central Warehouse",
            type=LocationType.CENTRAL_WAREHOUSE,
        ),
        user_id,
    )

    lab_store = await procurement_service.create_location(
        db_session,
        tenant_id,
        InventoryLocationCreate(
            campus_id=campus_id,
            code=f"STR-LAB-{uid}",
            name="ECE Department Store",
            type=LocationType.DEPARTMENT_STORE,
        ),
        user_id,
    )

    # Create inventory item
    item = await procurement_service.create_item(
        db_session,
        tenant_id,
        InventoryItemCreate(
            sku=f"SKU-RES-{uid}",
            name="Microcontroller Development Board",
            category=ItemCategory.LAB_CONSUMABLE,
            unit_of_measure="PCS",
            unit_price_average=Decimal("1200.00"),
            reorder_threshold=Decimal("15.00"),
            reorder_quantity=Decimal("50.00"),
        ),
        user_id,
    )

    # 1. Receipt movement into central warehouse (+50)
    await procurement_service.record_stock_movement(
        db_session,
        tenant_id,
        StockMovementCreate(
            movement_number=f"MOV-REC-{uid}",
            item_id=item.id,
            movement_type=MovementType.RECEIPT,
            destination_location_id=central_wh.id,
            quantity=Decimal("50.00"),
            unit_cost=Decimal("1200.00"),
            reference_type="OPENING_STOCK",
        ),
        user_id,
    )

    bal = await procurement_service.get_or_create_stock_balance(db_session, tenant_id, item.id, central_wh.id)
    assert bal.quantity_on_hand == Decimal("50.00")
    assert bal.quantity_available == Decimal("50.00")

    # 2. Negative stock prevention: attempting to issue 60 (> 50) must raise BadRequestException
    with pytest.raises(BadRequestException, match="Insufficient stock"):
        await procurement_service.record_stock_movement(
            db_session,
            tenant_id,
            StockMovementCreate(
                movement_number=f"MOV-NEG-{uid}",
                item_id=item.id,
                movement_type=MovementType.ISSUE,
                source_location_id=central_wh.id,
                quantity=Decimal("60.00"),
            ),
            user_id,
        )

    # 3. Inter-store transfer (20 units from central_wh to lab_store)
    transfer = await procurement_service.transfer_stock(
        db_session,
        tenant_id,
        StockTransferRequest(
            movement_number=f"MOV-TRF-{uid}",
            item_id=item.id,
            source_location_id=central_wh.id,
            destination_location_id=lab_store.id,
            quantity=Decimal("20.00"),
            notes="Transfer to ECE Lab Dispensary",
        ),
        user_id,
    )
    assert transfer.quantity == Decimal("20.00")

    # Verify source & destination balances
    wh_bal = await procurement_service.get_or_create_stock_balance(db_session, tenant_id, item.id, central_wh.id)
    lab_bal = await procurement_service.get_or_create_stock_balance(db_session, tenant_id, item.id, lab_store.id)

    assert wh_bal.quantity_on_hand == Decimal("30.00")
    assert wh_bal.quantity_available == Decimal("30.00")
    assert lab_bal.quantity_on_hand == Decimal("20.00")
    assert lab_bal.quantity_available == Decimal("20.00")


# =============================================================================
# 7. INTERNAL STOCK REQUEST, RESERVATION & FULFILLMENT
# =============================================================================


@pytest.mark.asyncio
async def test_internal_stock_request_reservation_and_fulfillment(
    db_session: AsyncSession,
    procurement_fixture: dict,
):
    """Tests departmental internal stock requests, stock reservation, and fulfillment."""
    tenant_id = procurement_fixture["tenant_a_id"]
    campus_id = procurement_fixture["campus_a_id"]
    dept_id = procurement_fixture["dept_a_id"]
    user_id = procurement_fixture["user_id"]
    uid = uuid.uuid4().hex[:6]

    # Location & item setup
    loc = await procurement_service.create_location(
        db_session,
        tenant_id,
        InventoryLocationCreate(
            campus_id=campus_id,
            code=f"WH-STK-{uid}",
            name="Stationery Store",
        ),
        user_id,
    )

    item = await procurement_service.create_item(
        db_session,
        tenant_id,
        InventoryItemCreate(
            sku=f"SKU-A4-{uid}",
            name="A4 Copier Paper (Ream)",
            category=ItemCategory.STATIONERY,
        ),
        user_id,
    )

    # Initial stock receipt of 100 reams
    await procurement_service.record_stock_movement(
        db_session,
        tenant_id,
        StockMovementCreate(
            movement_number=f"MOV-INIT-{uid}",
            item_id=item.id,
            movement_type=MovementType.RECEIPT,
            destination_location_id=loc.id,
            quantity=Decimal("100.00"),
        ),
        user_id,
    )

    # 1. Create internal stock request for 25 reams
    isr = await procurement_service.create_internal_stock_request(
        db_session,
        tenant_id,
        InternalStockRequestCreate(
            request_number=f"ISR-{uid}",
            department_id=dept_id,
            location_id=loc.id,
            required_date=date.today(),
            notes="Required for semester mid-term exams printing",
            lines=[
                InternalStockRequestLineCreate(
                    item_id=item.id,
                    quantity_requested=Decimal("25.00"),
                )
            ],
        ),
        user_id,
    )
    assert isr.status == InternalRequestStatus.PENDING

    # 2. Approve request and verify stock reservation
    approved_isr = await procurement_service.approve_internal_stock_request(
        db_session, tenant_id, isr.id, user_id
    )
    assert approved_isr.status == InternalRequestStatus.APPROVED

    bal_reserved = await procurement_service.get_or_create_stock_balance(db_session, tenant_id, item.id, loc.id)
    assert bal_reserved.quantity_reserved == Decimal("25.00")
    assert bal_reserved.quantity_available == Decimal("75.00")
    assert bal_reserved.quantity_on_hand == Decimal("100.00")

    # 3. Fulfill request: issue 25 reams
    line_id = approved_isr.lines[0].id
    fulfilled_isr = await procurement_service.fulfill_internal_stock_request(
        db_session,
        tenant_id,
        isr.id,
        InternalStockRequestFulfillRequest(
            line_fulfillments=[{"line_id": str(line_id), "quantity_to_issue": Decimal("25.00")}]
        ),
        user_id,
    )
    assert fulfilled_isr.status == InternalRequestStatus.FULFILLED

    bal_after = await procurement_service.get_or_create_stock_balance(db_session, tenant_id, item.id, loc.id)
    assert bal_after.quantity_reserved == Decimal("0.00")
    assert bal_after.quantity_on_hand == Decimal("75.00")
    assert bal_after.quantity_available == Decimal("75.00")


# =============================================================================
# 8. THREE-WAY INVOICE MATCHING & DISCREPANCY OVERRIDES
# =============================================================================


@pytest.mark.asyncio
async def test_three_way_invoice_matching_and_overrides(
    db_session: AsyncSession,
    procurement_fixture: dict,
):
    """Tests reconciliation between PO, GRN, and Supplier Invoice with discrepancy detection."""
    tenant_id = procurement_fixture["tenant_a_id"]
    campus_id = procurement_fixture["campus_a_id"]
    user_id = procurement_fixture["user_id"]
    uid = uuid.uuid4().hex[:6]

    # Setup vendor
    vendor = await procurement_service.create_vendor(
        db_session,
        tenant_id,
        VendorCreate(
            code=f"VEN-3W-{uid}",
            name=f"Tech Supplies {uid}",
            legal_name=f"Tech Supplies Corp {uid}",
            email=f"tech_{uid}@corp.com",
            phone="+919876543244",
            address_line1="99 Silicon Way",
            city="Coimbatore",
            state="Tamil Nadu",
            postal_code="641001",
        ),
        user_id,
    )
    await procurement_service.transition_vendor_status(
        db_session, tenant_id, vendor.id, VendorStatusTransitionRequest(status=VendorStatus.APPROVED), user_id
    )

    # PO: 10 units at 5,000 = 50,000.00
    po = await procurement_service.create_purchase_order(
        db_session,
        tenant_id,
        PurchaseOrderCreate(
            po_number=f"PO-3W-{uid}",
            vendor_id=vendor.id,
            campus_id=campus_id,
            order_date=date.today(),
            expected_delivery_date=date.today(),
            delivery_address="Main Campus Depot",
            billing_address="Finance Admin",
            lines=[
                PurchaseOrderLineCreate(
                    item_description="Smart Classroom Microphone",
                    quantity_ordered=Decimal("10.00"),
                    unit_price=Decimal("5000.00"),
                )
            ],
        ),
        user_id,
    )
    await procurement_service.issue_purchase_order(db_session, tenant_id, po.id, user_id)

    # GRN: Received & Accepted all 10 units
    grn = await procurement_service.create_goods_receipt(
        db_session,
        tenant_id,
        GoodsReceiptCreate(
            grn_number=f"GRN-3W-{uid}",
            po_id=po.id,
            vendor_id=vendor.id,
            receipt_date=date.today(),
            lines=[
                GoodsReceiptLineCreate(
                    po_line_id=po.lines[0].id,
                    item_description="Smart Classroom Microphone",
                    quantity_received=Decimal("10.00"),
                    quantity_accepted=Decimal("10.00"),
                )
            ],
        ),
        user_id,
    )

    # 1. Matching invoice: exactly 50,000.00
    match_ok = await procurement_service.create_invoice_match(
        db_session,
        tenant_id,
        SupplierInvoiceMatchCreate(
            match_reference=f"MAT-OK-{uid}",
            po_id=po.id,
            grn_id=grn.id,
            invoice_reference_number=f"INV-OK-{uid}",
            invoice_date=date.today(),
            invoice_amount=Decimal("50000.00"),
        ),
        user_id,
    )
    assert match_ok.status == InvoiceMatchStatus.MATCHED
    assert match_ok.price_variance == Decimal("0.00")

    # 2. Discrepancy invoice: 55,000.00 (exceeds 50,000 by 5,000)
    match_disc = await procurement_service.create_invoice_match(
        db_session,
        tenant_id,
        SupplierInvoiceMatchCreate(
            match_reference=f"MAT-DISC-{uid}",
            po_id=po.id,
            grn_id=grn.id,
            invoice_reference_number=f"INV-DISC-{uid}",
            invoice_date=date.today(),
            invoice_amount=Decimal("55000.00"),
            price_tolerance_pct=Decimal("2.00"),  # Only 2% tolerance allowed
        ),
        user_id,
    )
    assert match_disc.status == InvoiceMatchStatus.PRICE_DISCREPANCY
    assert match_disc.price_variance == Decimal("5000.00")

    # 3. Authorized override on discrepancy
    overridden = await procurement_service.override_invoice_match_discrepancy(
        db_session,
        tenant_id,
        match_disc.id,
        SupplierInvoiceMatchOverrideRequest(
            override_reason="Price increase approved by Purchase Committee due to emergency air freight charges"
        ),
        user_id,
    )
    assert overridden.status == InvoiceMatchStatus.OVERRIDE_APPROVED
    assert overridden.override_approved_by_id == user_id


# =============================================================================
# 9. VENDOR RETURNS (RTV)
# =============================================================================


@pytest.mark.asyncio
async def test_vendor_returns_and_credit_notes(
    db_session: AsyncSession,
    procurement_fixture: dict,
):
    """Tests return to vendor (RTV) and credit note tracking."""
    tenant_id = procurement_fixture["tenant_a_id"]
    campus_id = procurement_fixture["campus_a_id"]
    user_id = procurement_fixture["user_id"]
    uid = uuid.uuid4().hex[:6]

    # Setup vendor & PO
    vendor = await procurement_service.create_vendor(
        db_session,
        tenant_id,
        VendorCreate(
            code=f"VEN-RTV-{uid}",
            name=f"Return Vendor {uid}",
            legal_name=f"Return Vendor Legal {uid}",
            email=f"rtv_{uid}@vendor.com",
            phone="+919876543255",
            address_line1="12 Return Boulevard",
            city="Coimbatore",
            state="Tamil Nadu",
            postal_code="641001",
        ),
        user_id,
    )
    await procurement_service.transition_vendor_status(
        db_session, tenant_id, vendor.id, VendorStatusTransitionRequest(status=VendorStatus.APPROVED), user_id
    )

    po = await procurement_service.create_purchase_order(
        db_session,
        tenant_id,
        PurchaseOrderCreate(
            po_number=f"PO-RTV-{uid}",
            vendor_id=vendor.id,
            campus_id=campus_id,
            order_date=date.today(),
            expected_delivery_date=date.today(),
            delivery_address="Depot",
            billing_address="Admin",
            lines=[
                PurchaseOrderLineCreate(
                    item_description="Oscilloscope Probe",
                    quantity_ordered=Decimal("10.00"),
                    unit_price=Decimal("1000.00"),
                )
            ],
        ),
        user_id,
    )

    # Create Return to Vendor
    rtv = await procurement_service.create_vendor_return(
        db_session,
        tenant_id,
        VendorReturnCreate(
            return_number=f"RTV-{uid}",
            po_id=po.id,
            vendor_id=vendor.id,
            quantity=Decimal("2.00"),
            reason=VendorReturnReason.DEFECTIVE,
            credit_note_amount=Decimal("2000.00"),
        ),
        user_id,
    )
    assert rtv.return_number == f"RTV-{uid}"
    assert rtv.quantity == Decimal("2.00")

    # Update return resolution
    updated_rtv = await procurement_service.update_vendor_return_status(
        db_session,
        tenant_id,
        rtv.id,
        VendorReturnStatusUpdateRequest(
            status=VendorReturnStatus.COMPLETED,
            resolution_reference=f"CRN-VEN-{uid}",
        ),
        user_id,
    )
    assert updated_rtv.status == VendorReturnStatus.COMPLETED
    assert updated_rtv.resolution_reference == f"CRN-VEN-{uid}"


# =============================================================================
# 10. PROCUREMENT & INVENTORY ANALYTICS REPORTS
# =============================================================================


@pytest.mark.asyncio
async def test_procurement_and_inventory_analytics(
    db_session: AsyncSession,
    procurement_fixture: dict,
):
    """Tests summary KPIs and inventory valuation calculations."""
    tenant_id = procurement_fixture["tenant_a_id"]
    campus_id = procurement_fixture["campus_a_id"]
    user_id = procurement_fixture["user_id"]
    uid = uuid.uuid4().hex[:6]

    # Create sample vendor
    vendor = await procurement_service.create_vendor(
        db_session,
        tenant_id,
        VendorCreate(
            code=f"VEN-RPT-{uid}",
            name=f"Report Vendor {uid}",
            legal_name=f"Report Vendor Legal {uid}",
            email=f"rpt_{uid}@vendor.com",
            phone="+919876543277",
            address_line1="1 Analytics Ave",
            city="Coimbatore",
            state="Tamil Nadu",
            postal_code="641001",
        ),
        user_id,
    )
    await procurement_service.transition_vendor_status(
        db_session, tenant_id, vendor.id, VendorStatusTransitionRequest(status=VendorStatus.APPROVED), user_id
    )

    # Create location & item
    loc = await procurement_service.create_location(
        db_session,
        tenant_id,
        InventoryLocationCreate(
            campus_id=campus_id,
            code=f"WH-RPT-{uid}",
            name="Analytics Warehouse",
        ),
        user_id,
    )
    item = await procurement_service.create_item(
        db_session,
        tenant_id,
        InventoryItemCreate(
            sku=f"SKU-RPT-{uid}",
            name="Analytics Item",
            unit_price_average=Decimal("150.00"),
        ),
        user_id,
    )
    await procurement_service.record_stock_movement(
        db_session,
        tenant_id,
        StockMovementCreate(
            movement_number=f"MOV-RPT-{uid}",
            item_id=item.id,
            movement_type=MovementType.RECEIPT,
            destination_location_id=loc.id,
            quantity=Decimal("20.00"),
            unit_cost=Decimal("150.00"),
        ),
        user_id,
    )

    summary = await procurement_service.get_procurement_summary(db_session, tenant_id)
    assert summary.total_vendors_count >= 1
    assert summary.active_approved_vendors_count >= 1

    valuation = await procurement_service.get_inventory_valuation(db_session, tenant_id)
    assert valuation.total_items_count >= 1
    assert valuation.total_locations_count >= 1
    assert valuation.total_inventory_valuation >= Decimal("3000.00")


# =============================================================================
# 11. STRICT MULTI-TENANT ISOLATION
# =============================================================================


@pytest.mark.asyncio
async def test_procurement_multi_tenant_isolation(
    db_session: AsyncSession,
    procurement_fixture: dict,
):
    """Ensures records in Tenant A cannot be accessed or manipulated by Tenant B."""
    tenant_a_id = procurement_fixture["tenant_a_id"]
    tenant_b_id = procurement_fixture["tenant_b_id"]
    user_id = procurement_fixture["user_id"]
    uid = uuid.uuid4().hex[:6]

    # Vendor created in Tenant A
    vendor_a = await procurement_service.create_vendor(
        db_session,
        tenant_a_id,
        VendorCreate(
            code=f"VEN-ISO-A-{uid}",
            name=f"Tenant A Vendor {uid}",
            legal_name=f"Tenant A Vendor Legal {uid}",
            email=f"iso_a_{uid}@vendor.com",
            phone="+919876543266",
            address_line1="10 Alpha St",
            city="Coimbatore",
            state="Tamil Nadu",
            postal_code="641001",
        ),
        user_id,
    )

    # 1. Tenant B trying to get Tenant A's vendor must raise NotFoundException
    with pytest.raises(NotFoundException):
        await procurement_service.get_vendor(db_session, tenant_b_id, vendor_a.id)

    # 2. Tenant B listing vendors must not include Tenant A's vendor
    vendors_b, count_b = await procurement_service.list_vendors(db_session, tenant_b_id)
    b_ids = [v.id for v in vendors_b]
    assert vendor_a.id not in b_ids
