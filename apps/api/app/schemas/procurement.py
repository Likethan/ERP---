"""Pydantic v2 Schemas for Enterprise Procurement, Vendor Management, Purchase Orders & Inventory Control (Step 50).

CampusOS Tagline: "One Campus. One System. One Source of Truth."
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.procurement import (
    AmendmentStatus,
    AwardDecision,
    GoodsReceiptStatus,
    InternalRequestStatus,
    InvoiceMatchStatus,
    ItemCategory,
    LocationType,
    MovementType,
    PurchaseOrderStatus,
    QualityInspectionStatus,
    QuotationStatus,
    RequisitionPriority,
    RequisitionStatus,
    ReturnResolutionType,
    RfqStatus,
    VendorCategory,
    VendorReturnReason,
    VendorReturnStatus,
    VendorStatus,
)

# =============================================================================
# 1. VENDOR & SUPPLIER MANAGEMENT
# =============================================================================


class VendorContactCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., max_length=128)
    designation: str | None = Field(None, max_length=128)
    email: str = Field(..., max_length=255)
    phone: str = Field(..., max_length=32)
    is_primary: bool = False


class VendorContactUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str | None = Field(None, max_length=128)
    designation: str | None = Field(None, max_length=128)
    email: str | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=32)
    is_primary: bool | None = None


class VendorContactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    vendor_id: UUID
    name: str
    designation: str | None
    email: str
    phone: str
    is_primary: bool
    created_at: datetime
    updated_at: datetime


class VendorCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str = Field(..., max_length=64, description="Unique vendor code, e.g. VEN-2026-001")
    name: str = Field(..., max_length=255)
    legal_name: str = Field(..., max_length=255)
    category: VendorCategory = VendorCategory.GOODS
    classification: str | None = None
    tax_identifier: str | None = Field(None, max_length=64, description="GSTIN/PAN/Tax ID")
    email: str = Field(..., max_length=255)
    phone: str = Field(..., max_length=32)
    website: str | None = Field(None, max_length=255)
    address_line1: str = Field(..., max_length=255)
    address_line2: str | None = Field(None, max_length=255)
    city: str = Field(..., max_length=128)
    state: str = Field(..., max_length=128)
    postal_code: str = Field(..., max_length=32)
    country: str = Field(default="India", max_length=64)
    payment_terms_days: int = Field(default=30, ge=0)
    documents_json: dict[str, Any] = Field(default_factory=dict)
    bank_details_masked: dict[str, Any] = Field(default_factory=dict)
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    contacts: list[VendorContactCreate] = Field(default_factory=list)


class VendorUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str | None = Field(None, max_length=255)
    legal_name: str | None = Field(None, max_length=255)
    category: VendorCategory | None = None
    classification: str | None = None
    tax_identifier: str | None = Field(None, max_length=64)
    email: str | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=32)
    website: str | None = Field(None, max_length=255)
    address_line1: str | None = Field(None, max_length=255)
    address_line2: str | None = Field(None, max_length=255)
    city: str | None = Field(None, max_length=128)
    state: str | None = Field(None, max_length=128)
    postal_code: str | None = Field(None, max_length=32)
    country: str | None = Field(None, max_length=64)
    payment_terms_days: int | None = Field(None, ge=0)
    documents_json: dict[str, Any] | None = None
    bank_details_masked: dict[str, Any] | None = None
    metadata_json: dict[str, Any] | None = None


class VendorStatusTransitionRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: VendorStatus
    reason: str | None = None


class VendorPerformanceReviewCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    review_date: date
    delivery_score: int = Field(..., ge=1, le=5)
    quality_score: int = Field(..., ge=1, le=5)
    pricing_score: int = Field(..., ge=1, le=5)
    comments: str | None = None
    recommendation: str = Field(default="CONTINUE", max_length=64)


class VendorPerformanceReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    vendor_id: UUID
    review_date: date
    reviewer_id: UUID
    delivery_score: int
    quality_score: int
    pricing_score: int
    overall_score: Decimal
    comments: str | None
    recommendation: str
    created_at: datetime


class VendorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    code: str
    name: str
    legal_name: str
    category: VendorCategory
    classification: str | None
    status: VendorStatus
    tax_identifier: str | None
    email: str
    phone: str
    website: str | None
    city: str
    state: str
    country: str
    payment_terms_days: int
    rating_score: Decimal
    is_verified: bool
    verified_at: datetime | None
    verified_by: UUID | None
    created_at: datetime
    updated_at: datetime


class VendorDetailResponse(VendorResponse):
    address_line1: str
    address_line2: str | None
    postal_code: str
    documents_json: dict[str, Any]
    bank_details_masked: dict[str, Any]
    metadata_json: dict[str, Any]
    contacts: list[VendorContactResponse] = Field(default_factory=list)
    reviews: list[VendorPerformanceReviewResponse] = Field(default_factory=list)


class VendorDuplicateCheckRequest(BaseModel):
    legal_name: str
    tax_identifier: str | None = None
    email: str | None = None


class VendorDuplicateMatch(BaseModel):
    vendor_id: UUID
    code: str
    name: str
    legal_name: str
    tax_identifier: str | None
    email: str
    similarity_score: float
    matched_on: list[str]


class VendorDuplicateCheckResponse(BaseModel):
    has_potential_duplicates: bool
    matches: list[VendorDuplicateMatch] = Field(default_factory=list)


# =============================================================================
# 2. PURCHASE REQUISITIONS
# =============================================================================


class PurchaseRequisitionLineCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    item_id: UUID | None = None
    item_description: str = Field(..., max_length=255)
    unit_of_measure: str = Field(default="PCS", max_length=32)
    quantity_requested: Decimal = Field(..., gt=0)
    estimated_unit_price: Decimal = Field(..., ge=0)
    specifications: str | None = None


class PurchaseRequisitionLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    requisition_id: UUID
    item_id: UUID | None
    item_description: str
    unit_of_measure: str
    quantity_requested: Decimal
    estimated_unit_price: Decimal
    estimated_total_price: Decimal
    quantity_ordered: Decimal
    quantity_fulfilled: Decimal
    specifications: str | None
    created_at: datetime
    updated_at: datetime


class PurchaseRequisitionCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    requisition_number: str = Field(..., max_length=64, description="Requisition code, e.g. PR-2026-0001")
    department_id: UUID
    campus_id: UUID
    title: str = Field(..., max_length=255)
    justification: str
    category: VendorCategory = VendorCategory.GOODS
    priority: RequisitionPriority = RequisitionPriority.MEDIUM
    required_date: date
    delivery_location: str = Field(..., max_length=255)
    currency: str = Field(default="INR", max_length=16)
    budget_code: str | None = Field(None, max_length=64)
    notes: str | None = None
    lines: list[PurchaseRequisitionLineCreate] = Field(..., min_length=1)


class PurchaseRequisitionUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str | None = Field(None, max_length=255)
    justification: str | None = None
    priority: RequisitionPriority | None = None
    required_date: date | None = None
    delivery_location: str | None = Field(None, max_length=255)
    budget_code: str | None = Field(None, max_length=64)
    notes: str | None = None


class PurchaseRequisitionApprovalRequest(BaseModel):
    action: str = Field(..., pattern="^(APPROVE|REJECT|RETURN_FOR_CORRECTION)$")
    comments: str | None = None


class PurchaseRequisitionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    requisition_number: str
    department_id: UUID
    campus_id: UUID
    requestor_id: UUID
    title: str
    justification: str
    category: VendorCategory
    priority: RequisitionPriority
    status: RequisitionStatus
    required_date: date
    delivery_location: str
    estimated_total_amount: Decimal
    currency: str
    budget_code: str | None
    approved_by_id: UUID | None
    approved_at: datetime | None
    rejection_reason: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class PurchaseRequisitionDetailResponse(PurchaseRequisitionResponse):
    lines: list[PurchaseRequisitionLineResponse] = Field(default_factory=list)


# =============================================================================
# 3. REQUEST FOR QUOTATION (RFQ) & QUOTATIONS
# =============================================================================


class QuotationRequestCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rfq_number: str = Field(..., max_length=64, description="RFQ identifier, e.g. RFQ-2026-0001")
    requisition_id: UUID
    title: str = Field(..., max_length=255)
    deadline_date: date
    evaluation_criteria_json: dict[str, Any] = Field(
        default_factory=lambda: {"price_weight": 0.5, "quality_weight": 0.3, "delivery_weight": 0.2}
    )
    notes: str | None = None


class QuotationRequestUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str | None = Field(None, max_length=255)
    deadline_date: date | None = None
    status: RfqStatus | None = None
    evaluation_criteria_json: dict[str, Any] | None = None
    notes: str | None = None


class QuotationRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    rfq_number: str
    requisition_id: UUID
    title: str
    deadline_date: date
    status: RfqStatus
    evaluation_criteria_json: dict[str, Any]
    notes: str | None
    created_at: datetime
    updated_at: datetime


class VendorQuotationCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rfq_id: UUID
    vendor_id: UUID
    quotation_reference: str = Field(..., max_length=128)
    submission_date: date
    validity_until: date
    total_quoted_amount: Decimal = Field(..., ge=0)
    delivery_lead_days: int = Field(default=14, ge=1)
    warranty_months: int = Field(default=12, ge=0)
    payment_terms: str | None = Field(None, max_length=255)
    document_storage_key: str | None = Field(None, max_length=255)


class VendorQuotationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    rfq_id: UUID
    vendor_id: UUID
    quotation_reference: str
    submission_date: date
    validity_until: date
    total_quoted_amount: Decimal
    delivery_lead_days: int
    warranty_months: int
    payment_terms: str | None
    document_storage_key: str | None
    status: QuotationStatus
    evaluation_score: Decimal
    disqualification_reason: str | None
    evaluation_notes: str | None
    created_at: datetime
    updated_at: datetime


class QuotationEvaluationCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rfq_id: UUID
    evaluation_date: date
    scoring_details_json: dict[str, Any] = Field(default_factory=dict)
    recommended_vendor_id: UUID | None = None
    award_decision: AwardDecision = AwardDecision.PENDING
    single_source_justification: str | None = None


class QuotationEvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    rfq_id: UUID
    evaluator_id: UUID
    evaluation_date: date
    scoring_details_json: dict[str, Any]
    recommended_vendor_id: UUID | None
    award_decision: AwardDecision
    single_source_justification: str | None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 4. PURCHASE ORDERS
# =============================================================================


class PurchaseOrderLineCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    requisition_line_id: UUID | None = None
    item_id: UUID | None = None
    item_description: str = Field(..., max_length=255)
    unit_of_measure: str = Field(default="PCS", max_length=32)
    quantity_ordered: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)
    tax_rate: Decimal = Field(default=Decimal("0.00"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    total_price: Decimal = Field(default=Decimal("0.00"), ge=0)


class PurchaseOrderLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    po_id: UUID
    requisition_line_id: UUID | None
    item_id: UUID | None
    item_description: str
    unit_of_measure: str
    quantity_ordered: Decimal
    quantity_received: Decimal
    quantity_accepted: Decimal
    quantity_rejected: Decimal
    quantity_invoiced: Decimal
    unit_price: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    total_price: Decimal
    created_at: datetime
    updated_at: datetime


class PurchaseOrderCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    po_number: str = Field(..., max_length=64, description="PO identifier, e.g. PO-2026-0001")
    vendor_id: UUID
    requisition_id: UUID | None = None
    rfq_id: UUID | None = None
    vendor_quotation_id: UUID | None = None
    campus_id: UUID
    order_date: date
    expected_delivery_date: date
    delivery_address: str = Field(..., max_length=255)
    billing_address: str = Field(..., max_length=255)
    payment_terms: str = Field(default="Net 30", max_length=128)
    currency: str = Field(default="INR", max_length=16)
    discount_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    lines: list[PurchaseOrderLineCreate] = Field(..., min_length=1)


class PurchaseOrderUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    delivery_address: str | None = Field(None, max_length=255)
    billing_address: str | None = Field(None, max_length=255)
    payment_terms: str | None = Field(None, max_length=128)
    expected_delivery_date: date | None = None
    revision_notes: str | None = None


class PurchaseOrderAmendmentCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    reason: str
    changes_json: dict[str, Any] = Field(default_factory=dict)


class PurchaseOrderAmendmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    po_id: UUID
    amendment_number: int
    reason: str
    changes_json: dict[str, Any]
    requested_by_id: UUID
    approved_by_id: UUID | None
    approved_at: datetime | None
    status: AmendmentStatus
    created_at: datetime
    updated_at: datetime


class PurchaseOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    po_number: str
    vendor_id: UUID
    requisition_id: UUID | None
    rfq_id: UUID | None
    vendor_quotation_id: UUID | None
    campus_id: UUID
    status: PurchaseOrderStatus
    order_date: date
    expected_delivery_date: date
    delivery_address: str
    billing_address: str
    payment_terms: str
    currency: str
    subtotal: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    issued_by_id: UUID | None
    issued_at: datetime | None
    approved_by_id: UUID | None
    approved_at: datetime | None
    version_number: int
    revision_notes: str | None
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class PurchaseOrderDetailResponse(PurchaseOrderResponse):
    lines: list[PurchaseOrderLineResponse] = Field(default_factory=list)
    amendments: list[PurchaseOrderAmendmentResponse] = Field(default_factory=list)


# =============================================================================
# 5. GOODS RECEIPT & QUALITY INSPECTION
# =============================================================================


class GoodsReceiptLineCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    po_line_id: UUID
    item_id: UUID | None = None
    item_description: str = Field(..., max_length=255)
    unit_of_measure: str = Field(default="PCS", max_length=32)
    quantity_received: Decimal = Field(..., gt=0)
    quantity_accepted: Decimal = Field(..., ge=0)
    quantity_rejected: Decimal = Field(default=Decimal("0.00"), ge=0)
    rejection_reason: str | None = None
    batch_lot_number: str | None = Field(None, max_length=64)
    expiry_date: date | None = None


class GoodsReceiptLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    grn_id: UUID
    po_line_id: UUID
    item_id: UUID | None
    item_description: str
    unit_of_measure: str
    quantity_received: Decimal
    quantity_accepted: Decimal
    quantity_rejected: Decimal
    rejection_reason: str | None
    batch_lot_number: str | None
    expiry_date: date | None
    created_at: datetime
    updated_at: datetime


class GoodsReceiptCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    grn_number: str = Field(..., max_length=64, description="GRN identifier, e.g. GRN-2026-0001")
    po_id: UUID
    vendor_id: UUID
    receipt_date: date
    carrier_name: str | None = Field(None, max_length=128)
    tracking_number: str | None = Field(None, max_length=128)
    delivery_note_reference: str | None = Field(None, max_length=128)
    storage_location_id: UUID | None = None
    inspection_notes: str | None = None
    lines: list[GoodsReceiptLineCreate] = Field(..., min_length=1)


class GoodsReceiptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    grn_number: str
    po_id: UUID
    vendor_id: UUID
    receipt_date: date
    received_by_id: UUID
    carrier_name: str | None
    tracking_number: str | None
    delivery_note_reference: str | None
    status: GoodsReceiptStatus
    storage_location_id: UUID | None
    inspection_notes: str | None
    quality_status: QualityInspectionStatus
    inspected_by_id: UUID | None
    inspected_at: datetime | None
    created_at: datetime
    updated_at: datetime


class GoodsReceiptDetailResponse(GoodsReceiptResponse):
    lines: list[GoodsReceiptLineResponse] = Field(default_factory=list)


class QualityInspectionRecordRequest(BaseModel):
    quality_status: QualityInspectionStatus
    inspection_notes: str | None = None


# =============================================================================
# 6. INVENTORY LOCATIONS, ITEMS, BALANCES & MOVEMENTS
# =============================================================================


class InventoryLocationCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    campus_id: UUID
    code: str = Field(..., max_length=32, description="Unique location code, e.g. WH-MAIN-01")
    name: str = Field(..., max_length=128)
    type: LocationType = LocationType.CENTRAL_WAREHOUSE


class InventoryLocationUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str | None = Field(None, max_length=128)
    type: LocationType | None = None
    is_active: bool | None = None


class InventoryLocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    campus_id: UUID
    code: str
    name: str
    type: LocationType
    is_active: bool
    created_at: datetime
    updated_at: datetime


class InventoryItemCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sku: str = Field(..., max_length=64, description="Item SKU/Catalog number, e.g. SKU-STAT-001")
    name: str = Field(..., max_length=255)
    category: ItemCategory = ItemCategory.STATIONERY
    unit_of_measure: str = Field(default="PCS", max_length=32)
    unit_price_average: Decimal = Field(default=Decimal("0.00"), ge=0)
    reorder_threshold: Decimal = Field(default=Decimal("10.00"), ge=0)
    reorder_quantity: Decimal = Field(default=Decimal("50.00"), ge=0)


class InventoryItemUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str | None = Field(None, max_length=255)
    category: ItemCategory | None = None
    unit_of_measure: str | None = None
    unit_price_average: Decimal | None = None
    reorder_threshold: Decimal | None = None
    reorder_quantity: Decimal | None = None
    is_active: bool | None = None


class InventoryItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    sku: str
    name: str
    category: ItemCategory
    unit_of_measure: str
    unit_price_average: Decimal
    reorder_threshold: Decimal
    reorder_quantity: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime


class StockBalanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    item_id: UUID
    location_id: UUID
    quantity_on_hand: Decimal
    quantity_reserved: Decimal
    quantity_available: Decimal
    quantity_in_transit: Decimal
    last_reconciled_at: datetime | None
    created_at: datetime
    updated_at: datetime


class StockMovementCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    movement_number: str = Field(..., max_length=64, description="Movement number, e.g. MOV-2026-0001")
    item_id: UUID
    movement_type: MovementType
    source_location_id: UUID | None = None
    destination_location_id: UUID | None = None
    quantity: Decimal = Field(..., gt=0)
    unit_cost: Decimal = Field(default=Decimal("0.00"), ge=0)
    reference_type: str | None = None
    reference_id: UUID | None = None
    notes: str | None = None


class StockTransferRequest(BaseModel):
    movement_number: str = Field(..., max_length=64)
    item_id: UUID
    source_location_id: UUID
    destination_location_id: UUID
    quantity: Decimal = Field(..., gt=0)
    notes: str | None = None


class StockMovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    movement_number: str
    item_id: UUID
    movement_type: MovementType
    source_location_id: UUID | None
    destination_location_id: UUID | None
    quantity: Decimal
    unit_cost: Decimal
    total_value: Decimal
    reference_type: str | None
    reference_id: UUID | None
    performed_by_id: UUID
    timestamp: datetime
    notes: str | None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 7. INTERNAL STOCK REQUESTS
# =============================================================================


class InternalStockRequestLineCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    item_id: UUID
    quantity_requested: Decimal = Field(..., gt=0)


class InternalStockRequestLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    request_id: UUID
    item_id: UUID
    quantity_requested: Decimal
    quantity_issued: Decimal
    created_at: datetime
    updated_at: datetime


class InternalStockRequestCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    request_number: str = Field(..., max_length=64, description="Internal requisition code, e.g. ISR-2026-0001")
    department_id: UUID
    location_id: UUID
    required_date: date
    notes: str | None = None
    lines: list[InternalStockRequestLineCreate] = Field(..., min_length=1)


class InternalStockRequestFulfillRequest(BaseModel):
    line_fulfillments: list[dict[str, Any]] = Field(
        ...,
        description="List of {line_id: UUID, quantity_to_issue: Decimal}",
    )


class InternalStockRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    request_number: str
    department_id: UUID
    requestor_id: UUID
    location_id: UUID
    status: InternalRequestStatus
    required_date: date
    notes: str | None
    approved_by_id: UUID | None
    approved_at: datetime | None
    created_at: datetime
    updated_at: datetime


class InternalStockRequestDetailResponse(InternalStockRequestResponse):
    lines: list[InternalStockRequestLineResponse] = Field(default_factory=list)


# =============================================================================
# 8. THREE-WAY INVOICE MATCHING
# =============================================================================


class SupplierInvoiceMatchCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    match_reference: str = Field(..., max_length=64, description="Match ref, e.g. MAT-2026-0001")
    po_id: UUID
    grn_id: UUID
    invoice_reference_number: str = Field(..., max_length=128)
    invoice_date: date
    invoice_amount: Decimal = Field(..., ge=0)
    quantity_tolerance_pct: Decimal = Field(default=Decimal("0.00"), ge=0)
    price_tolerance_pct: Decimal = Field(default=Decimal("0.00"), ge=0)
    variance_notes: str | None = None


class SupplierInvoiceMatchOverrideRequest(BaseModel):
    override_reason: str = Field(..., min_length=5)


class SupplierInvoiceMatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    match_reference: str
    po_id: UUID
    grn_id: UUID
    invoice_reference_number: str
    invoice_date: date
    invoice_amount: Decimal
    po_amount: Decimal
    received_amount: Decimal
    quantity_variance: Decimal
    price_variance: Decimal
    status: InvoiceMatchStatus
    matched_by_id: UUID
    matched_at: datetime
    variance_notes: str | None
    override_reason: str | None
    override_approved_by_id: UUID | None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 9. VENDOR RETURNS (RTV)
# =============================================================================


class VendorReturnCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    return_number: str = Field(..., max_length=64, description="Return identifier, e.g. RTV-2026-0001")
    po_id: UUID
    grn_id: UUID | None = None
    vendor_id: UUID
    item_id: UUID | None = None
    quantity: Decimal = Field(..., gt=0)
    reason: VendorReturnReason = VendorReturnReason.DEFECTIVE
    resolution_type: ReturnResolutionType = ReturnResolutionType.REPLACEMENT
    resolution_reference: str | None = Field(None, max_length=128)
    credit_note_amount: Decimal = Field(default=Decimal("0.00"), ge=0)


class VendorReturnStatusUpdateRequest(BaseModel):
    status: VendorReturnStatus
    resolution_reference: str | None = None
    credit_note_amount: Decimal | None = None


class VendorReturnResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    return_number: str
    po_id: UUID
    grn_id: UUID | None
    vendor_id: UUID
    item_id: UUID | None
    quantity: Decimal
    reason: VendorReturnReason
    status: VendorReturnStatus
    resolution_type: ReturnResolutionType
    resolution_reference: str | None
    credit_note_amount: Decimal
    created_by_id: UUID
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 10. PROCUREMENT & INVENTORY ANALYTICS
# =============================================================================


class ProcurementSummaryReport(BaseModel):
    total_vendors_count: int
    active_approved_vendors_count: int
    pending_requisitions_count: int
    approved_requisitions_value: Decimal
    open_purchase_orders_count: int
    open_purchase_orders_value: Decimal
    closed_purchase_orders_value: Decimal
    goods_receipts_count: int
    matched_invoices_count: int
    discrepancy_invoices_count: int


class InventoryValuationReport(BaseModel):
    total_items_count: int
    low_stock_items_count: int
    total_inventory_valuation: Decimal
    total_locations_count: int
    items_by_category: dict[str, int] = Field(default_factory=dict)
