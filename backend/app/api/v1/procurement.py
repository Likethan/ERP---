"""CampusOS Enterprise Procurement, Vendor Management, Purchase Orders & Inventory Control REST API Router (Step 50).

CampusOS Tagline: "One Campus. One System. One Source of Truth."
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_current_user, get_tenant_context, require_permission
from app.core.permissions import (
    PROCUREMENT_INVENTORY_MANAGE,
    PROCUREMENT_INVENTORY_READ,
    PROCUREMENT_INVOICE_MATCH,
    PROCUREMENT_ORDERS_APPROVE,
    PROCUREMENT_ORDERS_CREATE,
    PROCUREMENT_QUOTATIONS_MANAGE,
    PROCUREMENT_READ,
    PROCUREMENT_RECEIVING_MANAGE,
    PROCUREMENT_REPORTS_READ,
    PROCUREMENT_REQUISITIONS_APPROVE,
    PROCUREMENT_REQUISITIONS_CREATE,
    PROCUREMENT_VENDORS_MANAGE,
)
from app.core.tenant import TenantContext
from app.models.people import User
from app.schemas.procurement import (
    GoodsReceiptCreate,
    GoodsReceiptDetailResponse,
    GoodsReceiptResponse,
    InternalStockRequestCreate,
    InternalStockRequestDetailResponse,
    InternalStockRequestFulfillRequest,
    InternalStockRequestResponse,
    InventoryItemCreate,
    InventoryItemResponse,
    InventoryItemUpdate,
    InventoryLocationCreate,
    InventoryLocationResponse,
    InventoryLocationUpdate,
    InventoryValuationReport,
    ProcurementSummaryReport,
    PurchaseOrderAmendmentCreate,
    PurchaseOrderAmendmentResponse,
    PurchaseOrderCreate,
    PurchaseOrderDetailResponse,
    PurchaseOrderResponse,
    PurchaseOrderUpdate,
    PurchaseRequisitionApprovalRequest,
    PurchaseRequisitionCreate,
    PurchaseRequisitionDetailResponse,
    PurchaseRequisitionResponse,
    PurchaseRequisitionUpdate,
    QualityInspectionRecordRequest,
    QuotationEvaluationCreate,
    QuotationEvaluationResponse,
    QuotationRequestCreate,
    QuotationRequestResponse,
    QuotationRequestUpdate,
    StockBalanceResponse,
    StockMovementCreate,
    StockMovementResponse,
    StockTransferRequest,
    SupplierInvoiceMatchCreate,
    SupplierInvoiceMatchOverrideRequest,
    SupplierInvoiceMatchResponse,
    VendorContactCreate,
    VendorContactResponse,
    VendorContactUpdate,
    VendorCreate,
    VendorDetailResponse,
    VendorDuplicateCheckRequest,
    VendorDuplicateCheckResponse,
    VendorPerformanceReviewCreate,
    VendorPerformanceReviewResponse,
    VendorQuotationCreate,
    VendorQuotationResponse,
    VendorResponse,
    VendorReturnCreate,
    VendorReturnResponse,
    VendorReturnStatusUpdateRequest,
    VendorStatusTransitionRequest,
    VendorUpdate,
)
from app.services.procurement_service import procurement_service

router = APIRouter(prefix="/procurement", tags=["Procurement & Inventory"])


# =============================================================================
# 1. VENDOR & SUPPLIER MANAGEMENT
# =============================================================================


@router.post(
    "/vendors",
    response_model=VendorDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new vendor",
    dependencies=[Depends(require_permission(PROCUREMENT_VENDORS_MANAGE))],
)
async def create_vendor(
    payload: VendorCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> VendorDetailResponse:
    return await procurement_service.create_vendor(db, ctx.tenant_id, payload, current_user.id)


@router.get(
    "/vendors",
    response_model=list[VendorResponse],
    summary="List registered vendors with filters",
    dependencies=[Depends(require_permission(PROCUREMENT_READ))],
)
async def list_vendors(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    category: str | None = Query(None),
    status_val: str | None = Query(None, alias="status"),
    search: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> list[VendorResponse]:
    vendors, _ = await procurement_service.list_vendors(
        db, ctx.tenant_id, category=category, status=status_val, search=search, skip=skip, limit=limit
    )
    return vendors


@router.post(
    "/vendors/duplicate-check",
    response_model=VendorDuplicateCheckResponse,
    summary="Detect potential duplicate vendor profiles",
    dependencies=[Depends(require_permission(PROCUREMENT_READ))],
)
async def check_vendor_duplicates(
    payload: VendorDuplicateCheckRequest,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> VendorDuplicateCheckResponse:
    return await procurement_service.check_vendor_duplicates(db, ctx.tenant_id, payload)


@router.get(
    "/vendors/{vendor_id}",
    response_model=VendorDetailResponse,
    summary="Get vendor profile details and contacts",
    dependencies=[Depends(require_permission(PROCUREMENT_READ))],
)
async def get_vendor(
    vendor_id: UUID,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> VendorDetailResponse:
    return await procurement_service.get_vendor(db, ctx.tenant_id, vendor_id)


@router.patch(
    "/vendors/{vendor_id}",
    response_model=VendorResponse,
    summary="Update vendor profile attributes",
    dependencies=[Depends(require_permission(PROCUREMENT_VENDORS_MANAGE))],
)
async def update_vendor(
    vendor_id: UUID,
    payload: VendorUpdate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> VendorResponse:
    return await procurement_service.update_vendor(db, ctx.tenant_id, vendor_id, payload, current_user.id)


@router.post(
    "/vendors/{vendor_id}/status",
    response_model=VendorResponse,
    summary="Transition vendor lifecycle status (Approve, Suspend, Inactivate)",
    dependencies=[Depends(require_permission(PROCUREMENT_VENDORS_MANAGE))],
)
async def transition_vendor_status(
    vendor_id: UUID,
    payload: VendorStatusTransitionRequest,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> VendorResponse:
    return await procurement_service.transition_vendor_status(
        db, ctx.tenant_id, vendor_id, payload, current_user.id
    )


@router.post(
    "/vendors/{vendor_id}/contacts",
    response_model=VendorContactResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an authorized contact to vendor profile",
    dependencies=[Depends(require_permission(PROCUREMENT_VENDORS_MANAGE))],
)
async def add_vendor_contact(
    vendor_id: UUID,
    payload: VendorContactCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> VendorContactResponse:
    return await procurement_service.add_vendor_contact(db, ctx.tenant_id, vendor_id, payload, current_user.id)


@router.patch(
    "/vendors/{vendor_id}/contacts/{contact_id}",
    response_model=VendorContactResponse,
    summary="Update an authorized vendor contact",
    dependencies=[Depends(require_permission(PROCUREMENT_VENDORS_MANAGE))],
)
async def update_vendor_contact(
    vendor_id: UUID,
    contact_id: UUID,
    payload: VendorContactUpdate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> VendorContactResponse:
    return await procurement_service.update_vendor_contact(
        db, ctx.tenant_id, vendor_id, contact_id, payload, current_user.id
    )


@router.post(
    "/vendors/{vendor_id}/reviews",
    response_model=VendorPerformanceReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record vendor performance review and update rating score",
    dependencies=[Depends(require_permission(PROCUREMENT_VENDORS_MANAGE))],
)
async def create_vendor_performance_review(
    vendor_id: UUID,
    payload: VendorPerformanceReviewCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> VendorPerformanceReviewResponse:
    return await procurement_service.create_vendor_performance_review(
        db, ctx.tenant_id, vendor_id, payload, current_user.id
    )


# =============================================================================
# 2. PURCHASE REQUISITIONS
# =============================================================================


@router.post(
    "/requisitions",
    response_model=PurchaseRequisitionDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create departmental purchase requisition",
    dependencies=[Depends(require_permission(PROCUREMENT_REQUISITIONS_CREATE))],
)
async def create_requisition(
    payload: PurchaseRequisitionCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> PurchaseRequisitionDetailResponse:
    return await procurement_service.create_requisition(db, ctx.tenant_id, payload, current_user.id)


@router.get(
    "/requisitions",
    response_model=list[PurchaseRequisitionResponse],
    summary="List purchase requisitions with filters",
    dependencies=[Depends(require_permission(PROCUREMENT_READ))],
)
async def list_requisitions(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    department_id: UUID | None = Query(None),
    campus_id: UUID | None = Query(None),
    status_val: str | None = Query(None, alias="status"),
    priority: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> list[PurchaseRequisitionResponse]:
    reqs, _ = await procurement_service.list_requisitions(
        db,
        ctx.tenant_id,
        department_id=department_id,
        campus_id=campus_id,
        status=status_val,
        priority=priority,
        skip=skip,
        limit=limit,
    )
    return reqs


@router.get(
    "/requisitions/{requisition_id}",
    response_model=PurchaseRequisitionDetailResponse,
    summary="Get purchase requisition details and line items",
    dependencies=[Depends(require_permission(PROCUREMENT_READ))],
)
async def get_requisition(
    requisition_id: UUID,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> PurchaseRequisitionDetailResponse:
    return await procurement_service.get_requisition(db, ctx.tenant_id, requisition_id)


@router.patch(
    "/requisitions/{requisition_id}",
    response_model=PurchaseRequisitionResponse,
    summary="Update draft purchase requisition",
    dependencies=[Depends(require_permission(PROCUREMENT_REQUISITIONS_CREATE))],
)
async def update_requisition(
    requisition_id: UUID,
    payload: PurchaseRequisitionUpdate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> PurchaseRequisitionResponse:
    return await procurement_service.update_requisition(
        db, ctx.tenant_id, requisition_id, payload, current_user.id
    )


@router.post(
    "/requisitions/{requisition_id}/review",
    response_model=PurchaseRequisitionResponse,
    summary="Approve, reject, or return purchase requisition for correction",
    dependencies=[Depends(require_permission(PROCUREMENT_REQUISITIONS_APPROVE))],
)
async def review_requisition(
    requisition_id: UUID,
    payload: PurchaseRequisitionApprovalRequest,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> PurchaseRequisitionResponse:
    return await procurement_service.review_requisition(
        db, ctx.tenant_id, requisition_id, payload, current_user.id
    )


# =============================================================================
# 3. REQUEST FOR QUOTATION (RFQ) & QUOTATIONS
# =============================================================================


@router.post(
    "/rfqs",
    response_model=QuotationRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Issue formal Request for Quotation (RFQ)",
    dependencies=[Depends(require_permission(PROCUREMENT_QUOTATIONS_MANAGE))],
)
async def create_rfq(
    payload: QuotationRequestCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> QuotationRequestResponse:
    return await procurement_service.create_rfq(db, ctx.tenant_id, payload, current_user.id)


@router.get(
    "/rfqs",
    response_model=list[QuotationRequestResponse],
    summary="List quotation requests with filters",
    dependencies=[Depends(require_permission(PROCUREMENT_READ))],
)
async def list_rfqs(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status_val: str | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> list[QuotationRequestResponse]:
    rfqs, _ = await procurement_service.list_rfqs(db, ctx.tenant_id, status=status_val, skip=skip, limit=limit)
    return rfqs


@router.get(
    "/rfqs/{rfq_id}",
    response_model=QuotationRequestResponse,
    summary="Get RFQ details with received quotations and evaluations",
    dependencies=[Depends(require_permission(PROCUREMENT_READ))],
)
async def get_rfq(
    rfq_id: UUID,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> QuotationRequestResponse:
    return await procurement_service.get_rfq(db, ctx.tenant_id, rfq_id)


@router.patch(
    "/rfqs/{rfq_id}",
    response_model=QuotationRequestResponse,
    summary="Update RFQ details or close bidding",
    dependencies=[Depends(require_permission(PROCUREMENT_QUOTATIONS_MANAGE))],
)
async def update_rfq(
    rfq_id: UUID,
    payload: QuotationRequestUpdate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> QuotationRequestResponse:
    return await procurement_service.update_rfq(db, ctx.tenant_id, rfq_id, payload, current_user.id)


@router.post(
    "/quotations",
    response_model=VendorQuotationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit quotation on behalf of vendor",
    dependencies=[Depends(require_permission(PROCUREMENT_QUOTATIONS_MANAGE))],
)
async def submit_vendor_quotation(
    payload: VendorQuotationCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> VendorQuotationResponse:
    return await procurement_service.submit_vendor_quotation(db, ctx.tenant_id, payload, current_user.id)


@router.post(
    "/evaluations",
    response_model=QuotationEvaluationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record formal quotation evaluation and award decision",
    dependencies=[Depends(require_permission(PROCUREMENT_QUOTATIONS_MANAGE))],
)
async def evaluate_quotation(
    payload: QuotationEvaluationCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> QuotationEvaluationResponse:
    return await procurement_service.evaluate_quotation(db, ctx.tenant_id, payload, current_user.id)


# =============================================================================
# 4. PURCHASE ORDERS & AMENDMENTS
# =============================================================================


@router.post(
    "/orders",
    response_model=PurchaseOrderDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a purchase order for an approved vendor",
    dependencies=[Depends(require_permission(PROCUREMENT_ORDERS_CREATE))],
)
async def create_purchase_order(
    payload: PurchaseOrderCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> PurchaseOrderDetailResponse:
    return await procurement_service.create_purchase_order(db, ctx.tenant_id, payload, current_user.id)


@router.get(
    "/orders",
    response_model=list[PurchaseOrderResponse],
    summary="List purchase orders with filters",
    dependencies=[Depends(require_permission(PROCUREMENT_READ))],
)
async def list_purchase_orders(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    vendor_id: UUID | None = Query(None),
    status_val: str | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> list[PurchaseOrderResponse]:
    orders, _ = await procurement_service.list_purchase_orders(
        db, ctx.tenant_id, vendor_id=vendor_id, status=status_val, skip=skip, limit=limit
    )
    return orders


@router.get(
    "/orders/{po_id}",
    response_model=PurchaseOrderDetailResponse,
    summary="Get purchase order details, lines, and amendments",
    dependencies=[Depends(require_permission(PROCUREMENT_READ))],
)
async def get_purchase_order(
    po_id: UUID,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> PurchaseOrderDetailResponse:
    return await procurement_service.get_purchase_order(db, ctx.tenant_id, po_id)


@router.patch(
    "/orders/{po_id}",
    response_model=PurchaseOrderResponse,
    summary="Update draft purchase order metadata",
    dependencies=[Depends(require_permission(PROCUREMENT_ORDERS_CREATE))],
)
async def update_purchase_order(
    po_id: UUID,
    payload: PurchaseOrderUpdate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> PurchaseOrderResponse:
    return await procurement_service.update_purchase_order(db, ctx.tenant_id, po_id, payload, current_user.id)


@router.post(
    "/orders/{po_id}/issue",
    response_model=PurchaseOrderResponse,
    summary="Issue and approve purchase order to vendor",
    dependencies=[Depends(require_permission(PROCUREMENT_ORDERS_APPROVE))],
)
async def issue_purchase_order(
    po_id: UUID,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> PurchaseOrderResponse:
    return await procurement_service.issue_purchase_order(db, ctx.tenant_id, po_id, current_user.id)


@router.post(
    "/orders/{po_id}/amendments",
    response_model=PurchaseOrderAmendmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create versioned amendment for an issued purchase order",
    dependencies=[Depends(require_permission(PROCUREMENT_ORDERS_APPROVE))],
)
async def create_po_amendment(
    po_id: UUID,
    payload: PurchaseOrderAmendmentCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> PurchaseOrderAmendmentResponse:
    return await procurement_service.create_po_amendment(db, ctx.tenant_id, po_id, payload, current_user.id)


@router.post(
    "/orders/{po_id}/close",
    response_model=PurchaseOrderResponse,
    summary="Close fulfilled purchase order",
    dependencies=[Depends(require_permission(PROCUREMENT_ORDERS_APPROVE))],
)
async def close_purchase_order(
    po_id: UUID,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> PurchaseOrderResponse:
    return await procurement_service.close_purchase_order(db, ctx.tenant_id, po_id, current_user.id)


@router.post(
    "/orders/{po_id}/cancel",
    response_model=PurchaseOrderResponse,
    summary="Cancel purchase order",
    dependencies=[Depends(require_permission(PROCUREMENT_ORDERS_APPROVE))],
)
async def cancel_purchase_order(
    po_id: UUID,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> PurchaseOrderResponse:
    return await procurement_service.cancel_purchase_order(db, ctx.tenant_id, po_id, current_user.id)


# =============================================================================
# 5. GOODS RECEIPT & QUALITY INSPECTION
# =============================================================================


@router.post(
    "/receipts",
    response_model=GoodsReceiptDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Process Goods Receipt Note (GRN) with over-receipt protection",
    dependencies=[Depends(require_permission(PROCUREMENT_RECEIVING_MANAGE))],
)
async def create_goods_receipt(
    payload: GoodsReceiptCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> GoodsReceiptDetailResponse:
    return await procurement_service.create_goods_receipt(db, ctx.tenant_id, payload, current_user.id)


@router.get(
    "/receipts",
    response_model=list[GoodsReceiptResponse],
    summary="List goods receipts with filters",
    dependencies=[Depends(require_permission(PROCUREMENT_READ))],
)
async def list_goods_receipts(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    po_id: UUID | None = Query(None),
    status_val: str | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> list[GoodsReceiptResponse]:
    receipts, _ = await procurement_service.list_goods_receipts(
        db, ctx.tenant_id, po_id=po_id, status=status_val, skip=skip, limit=limit
    )
    return receipts


@router.get(
    "/receipts/{grn_id}",
    response_model=GoodsReceiptDetailResponse,
    summary="Get goods receipt note and line receipts",
    dependencies=[Depends(require_permission(PROCUREMENT_READ))],
)
async def get_goods_receipt(
    grn_id: UUID,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> GoodsReceiptDetailResponse:
    return await procurement_service.get_goods_receipt(db, ctx.tenant_id, grn_id)


@router.post(
    "/receipts/{grn_id}/inspection",
    response_model=GoodsReceiptResponse,
    summary="Record formal quality inspection results and quarantine/reject goods",
    dependencies=[Depends(require_permission(PROCUREMENT_RECEIVING_MANAGE))],
)
async def record_quality_inspection(
    grn_id: UUID,
    payload: QualityInspectionRecordRequest,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> GoodsReceiptResponse:
    return await procurement_service.record_quality_inspection(
        db, ctx.tenant_id, grn_id, payload, current_user.id
    )


# =============================================================================
# 6. INVENTORY LOCATIONS, ITEMS & MOVEMENTS
# =============================================================================


@router.post(
    "/inventory/locations",
    response_model=InventoryLocationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create warehouse or store location",
    dependencies=[Depends(require_permission(PROCUREMENT_INVENTORY_MANAGE))],
)
async def create_location(
    payload: InventoryLocationCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> InventoryLocationResponse:
    return await procurement_service.create_location(db, ctx.tenant_id, payload, current_user.id)


@router.get(
    "/inventory/locations",
    response_model=list[InventoryLocationResponse],
    summary="List inventory locations",
    dependencies=[Depends(require_permission(PROCUREMENT_INVENTORY_READ))],
)
async def list_locations(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    campus_id: UUID | None = Query(None),
    loc_type: str | None = Query(None, alias="type"),
) -> list[InventoryLocationResponse]:
    return await procurement_service.list_locations(db, ctx.tenant_id, campus_id=campus_id, loc_type=loc_type)


@router.patch(
    "/inventory/locations/{loc_id}",
    response_model=InventoryLocationResponse,
    summary="Update warehouse or store location",
    dependencies=[Depends(require_permission(PROCUREMENT_INVENTORY_MANAGE))],
)
async def update_location(
    loc_id: UUID,
    payload: InventoryLocationUpdate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> InventoryLocationResponse:
    return await procurement_service.update_location(db, ctx.tenant_id, loc_id, payload, current_user.id)


@router.post(
    "/inventory/items",
    response_model=InventoryItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register stock item in inventory catalogue",
    dependencies=[Depends(require_permission(PROCUREMENT_INVENTORY_MANAGE))],
)
async def create_item(
    payload: InventoryItemCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> InventoryItemResponse:
    return await procurement_service.create_item(db, ctx.tenant_id, payload, current_user.id)


@router.get(
    "/inventory/items",
    response_model=list[InventoryItemResponse],
    summary="List catalogue items with stock metrics",
    dependencies=[Depends(require_permission(PROCUREMENT_INVENTORY_READ))],
)
async def list_items(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    category: str | None = Query(None),
    is_active: bool | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> list[InventoryItemResponse]:
    items, _ = await procurement_service.list_items(
        db, ctx.tenant_id, category=category, is_active=is_active, skip=skip, limit=limit
    )
    return items


@router.get(
    "/inventory/items/{item_id}",
    response_model=InventoryItemResponse,
    summary="Get inventory item details",
    dependencies=[Depends(require_permission(PROCUREMENT_INVENTORY_READ))],
)
async def get_item(
    item_id: UUID,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> InventoryItemResponse:
    return await procurement_service.get_item(db, ctx.tenant_id, item_id)


@router.patch(
    "/inventory/items/{item_id}",
    response_model=InventoryItemResponse,
    summary="Update inventory catalogue item",
    dependencies=[Depends(require_permission(PROCUREMENT_INVENTORY_MANAGE))],
)
async def update_item(
    item_id: UUID,
    payload: InventoryItemUpdate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> InventoryItemResponse:
    return await procurement_service.update_item(db, ctx.tenant_id, item_id, payload, current_user.id)


@router.get(
    "/inventory/balances",
    response_model=list[StockBalanceResponse],
    summary="List stock balances across locations",
    dependencies=[Depends(require_permission(PROCUREMENT_INVENTORY_READ))],
)
async def list_stock_balances(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    item_id: UUID | None = Query(None),
    location_id: UUID | None = Query(None),
) -> list[StockBalanceResponse]:
    return await procurement_service.list_stock_balances(
        db, ctx.tenant_id, item_id=item_id, location_id=location_id
    )


@router.post(
    "/inventory/movements",
    response_model=StockMovementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record immutable stock movement (Receipt, Issue, Adjustment)",
    dependencies=[Depends(require_permission(PROCUREMENT_INVENTORY_MANAGE))],
)
async def record_stock_movement(
    payload: StockMovementCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> StockMovementResponse:
    return await procurement_service.record_stock_movement(db, ctx.tenant_id, payload, current_user.id)


@router.post(
    "/inventory/transfers",
    response_model=StockMovementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Perform atomic inter-store stock transfer",
    dependencies=[Depends(require_permission(PROCUREMENT_INVENTORY_MANAGE))],
)
async def transfer_stock(
    payload: StockTransferRequest,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> StockMovementResponse:
    return await procurement_service.transfer_stock(db, ctx.tenant_id, payload, current_user.id)


# =============================================================================
# 7. INTERNAL STOCK REQUESTS
# =============================================================================


@router.post(
    "/internal-requests",
    response_model=InternalStockRequestDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create departmental internal stock supply requisition",
    dependencies=[Depends(require_permission(PROCUREMENT_REQUISITIONS_CREATE))],
)
async def create_internal_stock_request(
    payload: InternalStockRequestCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> InternalStockRequestDetailResponse:
    return await procurement_service.create_internal_stock_request(
        db, ctx.tenant_id, payload, current_user.id
    )


@router.get(
    "/internal-requests",
    response_model=list[InternalStockRequestResponse],
    summary="List internal stock requests with filters",
    dependencies=[Depends(require_permission(PROCUREMENT_READ))],
)
async def list_internal_stock_requests(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    department_id: UUID | None = Query(None),
    status_val: str | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> list[InternalStockRequestResponse]:
    reqs, _ = await procurement_service.list_internal_stock_requests(
        db, ctx.tenant_id, department_id=department_id, status=status_val, skip=skip, limit=limit
    )
    return reqs


@router.get(
    "/internal-requests/{request_id}",
    response_model=InternalStockRequestDetailResponse,
    summary="Get internal stock request details and line items",
    dependencies=[Depends(require_permission(PROCUREMENT_READ))],
)
async def get_internal_stock_request(
    request_id: UUID,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> InternalStockRequestDetailResponse:
    return await procurement_service.get_internal_stock_request(db, ctx.tenant_id, request_id)


@router.post(
    "/internal-requests/{request_id}/approve",
    response_model=InternalStockRequestResponse,
    summary="Approve internal stock request and reserve quantities",
    dependencies=[Depends(require_permission(PROCUREMENT_REQUISITIONS_APPROVE))],
)
async def approve_internal_stock_request(
    request_id: UUID,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> InternalStockRequestResponse:
    return await procurement_service.approve_internal_stock_request(
        db, ctx.tenant_id, request_id, current_user.id
    )


@router.post(
    "/internal-requests/{request_id}/fulfill",
    response_model=InternalStockRequestResponse,
    summary="Issue stock and fulfill approved internal stock request",
    dependencies=[Depends(require_permission(PROCUREMENT_INVENTORY_MANAGE))],
)
async def fulfill_internal_stock_request(
    request_id: UUID,
    payload: InternalStockRequestFulfillRequest,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> InternalStockRequestResponse:
    return await procurement_service.fulfill_internal_stock_request(
        db, ctx.tenant_id, request_id, payload, current_user.id
    )


# =============================================================================
# 8. THREE-WAY INVOICE MATCHING
# =============================================================================


@router.post(
    "/invoice-matches",
    response_model=SupplierInvoiceMatchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Execute three-way invoice matching between PO, GRN, and Invoice",
    dependencies=[Depends(require_permission(PROCUREMENT_INVOICE_MATCH))],
)
async def create_invoice_match(
    payload: SupplierInvoiceMatchCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SupplierInvoiceMatchResponse:
    return await procurement_service.create_invoice_match(db, ctx.tenant_id, payload, current_user.id)


@router.get(
    "/invoice-matches",
    response_model=list[SupplierInvoiceMatchResponse],
    summary="List invoice matching reconciliation records",
    dependencies=[Depends(require_permission(PROCUREMENT_READ))],
)
async def list_invoice_matches(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status_val: str | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> list[SupplierInvoiceMatchResponse]:
    matches, _ = await procurement_service.list_invoice_matches(
        db, ctx.tenant_id, status=status_val, skip=skip, limit=limit
    )
    return matches


@router.get(
    "/invoice-matches/{match_id}",
    response_model=SupplierInvoiceMatchResponse,
    summary="Get invoice match reconciliation details",
    dependencies=[Depends(require_permission(PROCUREMENT_READ))],
)
async def get_invoice_match(
    match_id: UUID,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SupplierInvoiceMatchResponse:
    return await procurement_service.get_invoice_match(db, ctx.tenant_id, match_id)


@router.post(
    "/invoice-matches/{match_id}/override",
    response_model=SupplierInvoiceMatchResponse,
    summary="Authorize override on price or quantity discrepancy",
    dependencies=[Depends(require_permission(PROCUREMENT_INVOICE_MATCH))],
)
async def override_invoice_match_discrepancy(
    match_id: UUID,
    payload: SupplierInvoiceMatchOverrideRequest,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SupplierInvoiceMatchResponse:
    return await procurement_service.override_invoice_match_discrepancy(
        db, ctx.tenant_id, match_id, payload, current_user.id
    )


# =============================================================================
# 9. VENDOR RETURNS (RTV)
# =============================================================================


@router.post(
    "/returns",
    response_model=VendorReturnResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initiate return to vendor (RTV) for defective or damaged goods",
    dependencies=[Depends(require_permission(PROCUREMENT_RECEIVING_MANAGE))],
)
async def create_vendor_return(
    payload: VendorReturnCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> VendorReturnResponse:
    return await procurement_service.create_vendor_return(db, ctx.tenant_id, payload, current_user.id)


@router.get(
    "/returns",
    response_model=list[VendorReturnResponse],
    summary="List vendor returns with filters",
    dependencies=[Depends(require_permission(PROCUREMENT_READ))],
)
async def list_vendor_returns(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status_val: str | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> list[VendorReturnResponse]:
    returns, _ = await procurement_service.list_vendor_returns(
        db, ctx.tenant_id, status=status_val, skip=skip, limit=limit
    )
    return returns


@router.get(
    "/returns/{return_id}",
    response_model=VendorReturnResponse,
    summary="Get vendor return details",
    dependencies=[Depends(require_permission(PROCUREMENT_READ))],
)
async def get_vendor_return(
    return_id: UUID,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> VendorReturnResponse:
    return await procurement_service.get_vendor_return(db, ctx.tenant_id, return_id)


@router.patch(
    "/returns/{return_id}/status",
    response_model=VendorReturnResponse,
    summary="Update vendor return status and credit note resolution",
    dependencies=[Depends(require_permission(PROCUREMENT_RECEIVING_MANAGE))],
)
async def update_vendor_return_status(
    return_id: UUID,
    payload: VendorReturnStatusUpdateRequest,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> VendorReturnResponse:
    return await procurement_service.update_vendor_return_status(
        db, ctx.tenant_id, return_id, payload, current_user.id
    )


# =============================================================================
# 10. PROCUREMENT & INVENTORY ANALYTICS
# =============================================================================


@router.get(
    "/reports/summary",
    response_model=ProcurementSummaryReport,
    summary="Procurement KPIs: commitments, orders, receipts, and invoice discrepancies",
    dependencies=[Depends(require_permission(PROCUREMENT_REPORTS_READ))],
)
async def get_procurement_summary(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ProcurementSummaryReport:
    return await procurement_service.get_procurement_summary(db, ctx.tenant_id)


@router.get(
    "/reports/inventory-valuation",
    response_model=InventoryValuationReport,
    summary="Inventory valuation KPIs: stock levels, valuation, and low stock alerts",
    dependencies=[Depends(require_permission(PROCUREMENT_REPORTS_READ))],
)
async def get_inventory_valuation(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> InventoryValuationReport:
    return await procurement_service.get_inventory_valuation(db, ctx.tenant_id)
