"""CampusOS Enterprise Procurement, Vendor Management, Purchase Orders & Inventory Control Models (Step 50).

Governs:
- Vendors, contacts, onboarding verifications, performance reviews, and duplicate detection
- Purchase requisitions, line items, and multi-level approval workflows
- Requests for Quotation (RFQ), vendor quotations, weighted scoring, and single-source justifications
- Purchase orders, decimal-validated lines, versioned amendments, and order closures
- Goods receipt notes (GRN), quality inspections, quarantine, and over-receipt prevention
- Multi-location inventory control, item catalog, stock balances, and immutable movement ledgers
- Internal departmental stock requests, reservations, issues, and transfers
- Three-way invoice matching (PO vs GRN vs Supplier Invoice) with tolerance and variance handling
- Vendor returns (RTV) and replacement/credit-note tracking
"""

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantScopedModel

# =============================================================================
# ENUM TAXONOMY
# =============================================================================


class VendorCategory(StrEnum):
    """Institutional classification of vendor capabilities."""

    GOODS = "GOODS"
    SERVICES = "SERVICES"
    MAINTENANCE = "MAINTENANCE"
    TECHNOLOGY = "TECHNOLOGY"
    EDUCATIONAL_SUPPLIES = "EDUCATIONAL_SUPPLIES"
    LABORATORY_EQUIPMENT = "LABORATORY_EQUIPMENT"
    FACILITIES = "FACILITIES"
    OTHER = "OTHER"


class VendorStatus(StrEnum):
    """Lifecycle state of an institutional vendor profile."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    SUSPENDED = "SUSPENDED"
    INACTIVE = "INACTIVE"


class RequisitionPriority(StrEnum):
    """Urgency level for departmental purchase requisitions."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class RequisitionStatus(StrEnum):
    """Lifecycle stages of a purchase requisition."""

    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RETURNED_FOR_CORRECTION = "RETURNED_FOR_CORRECTION"
    CANCELLED = "CANCELLED"
    PARTIALLY_FULFILLED = "PARTIALLY_FULFILLED"
    FULFILLED = "FULFILLED"


class RfqStatus(StrEnum):
    """Status of a formal Request for Quotation."""

    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    CLOSED = "CLOSED"
    EVALUATED = "EVALUATED"
    CANCELLED = "CANCELLED"


class QuotationStatus(StrEnum):
    """Vendor quotation evaluation state."""

    SUBMITTED = "SUBMITTED"
    UNDER_EVALUATION = "UNDER_EVALUATION"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    DISQUALIFIED = "DISQUALIFIED"


class AwardDecision(StrEnum):
    """Final decision outcome for quotation evaluation."""

    AWARDED = "AWARDED"
    PENDING = "PENDING"
    REJECTED = "REJECTED"


class PurchaseOrderStatus(StrEnum):
    """Binding purchase order lifecycle status."""

    DRAFT = "DRAFT"
    ISSUED = "ISSUED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    PARTIALLY_DELIVERED = "PARTIALLY_DELIVERED"
    DELIVERED = "DELIVERED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class AmendmentStatus(StrEnum):
    """Purchase order amendment review status."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class GoodsReceiptStatus(StrEnum):
    """Receipt and physical delivery inspection status."""

    RECEIVED = "RECEIVED"
    INSPECTED = "INSPECTED"
    ACCEPTED = "ACCEPTED"
    PARTIALLY_ACCEPTED = "PARTIALLY_ACCEPTED"
    REJECTED = "REJECTED"
    QUARANTINED = "QUARANTINED"


class QualityInspectionStatus(StrEnum):
    """Formal quality control outcome for delivered goods."""

    PENDING = "PENDING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    WAIVED = "WAIVED"


class LocationType(StrEnum):
    """Type of institutional storage or warehouse facility."""

    CENTRAL_WAREHOUSE = "CENTRAL_WAREHOUSE"
    DEPARTMENT_STORE = "DEPARTMENT_STORE"
    LAB_STORE = "LAB_STORE"
    ASSET_DEPOT = "ASSET_DEPOT"
    QUARANTINE = "QUARANTINE"


class ItemCategory(StrEnum):
    """Category classification for inventory catalogue items."""

    STATIONERY = "STATIONERY"
    LAB_CONSUMABLE = "LAB_CONSUMABLE"
    IT_EQUIPMENT = "IT_EQUIPMENT"
    CHEMICAL = "CHEMICAL"
    HARDWARE = "HARDWARE"
    MAINTENANCE_PARTS = "MAINTENANCE_PARTS"
    MEDICAL_SUPPLIES = "MEDICAL_SUPPLIES"
    FURNITURE = "FURNITURE"
    OTHER = "OTHER"


class MovementType(StrEnum):
    """Immutable stock transaction movement classification."""

    RECEIPT = "RECEIPT"
    ISSUE = "ISSUE"
    TRANSFER_OUT = "TRANSFER_OUT"
    TRANSFER_IN = "TRANSFER_IN"
    RETURN_TO_VENDOR = "RETURN_TO_VENDOR"
    ADJUSTMENT = "ADJUSTMENT"
    RETURN_FROM_DEPARTMENT = "RETURN_FROM_DEPARTMENT"


class InternalRequestStatus(StrEnum):
    """Departmental internal stock supply request status."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    FULFILLED = "FULFILLED"
    PARTIALLY_FULFILLED = "PARTIALLY_FULFILLED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class InvoiceMatchStatus(StrEnum):
    """Three-way match reconciliation status between PO, GRN, and Supplier Invoice."""

    MATCHED = "MATCHED"
    QUANTITY_DISCREPANCY = "QUANTITY_DISCREPANCY"
    PRICE_DISCREPANCY = "PRICE_DISCREPANCY"
    OVERRIDE_APPROVED = "OVERRIDE_APPROVED"
    REJECTED = "REJECTED"


class VendorReturnStatus(StrEnum):
    """Return to Vendor (RTV) status."""

    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    DISPATCHED = "DISPATCHED"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


class VendorReturnReason(StrEnum):
    """Reason for returning goods to vendor."""

    DAMAGED = "DAMAGED"
    DEFECTIVE = "DEFECTIVE"
    WRONG_ITEM = "WRONG_ITEM"
    EXCESS = "EXCESS"
    WARRANTY_REPAIR = "WARRANTY_REPAIR"


class ReturnResolutionType(StrEnum):
    """Financial or stock resolution for returned items."""

    REPLACEMENT = "REPLACEMENT"
    CREDIT_NOTE = "CREDIT_NOTE"
    REFUND = "REFUND"


# =============================================================================
# 1. VENDOR & SUPPLIER MANAGEMENT
# =============================================================================


class Vendor(TenantScopedModel):
    """Institutional supplier or vendor organization."""

    __tablename__ = "procurement_vendors"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_procurement_vendor_code"),
        Index("idx_procurement_vendor_category", "tenant_id", "category"),
        Index("idx_procurement_vendor_status", "tenant_id", "status"),
    )

    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(64), default=VendorCategory.GOODS, nullable=False)
    classification: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default=VendorStatus.PENDING, nullable=False)
    tax_identifier: Mapped[str | None] = mapped_column(String(64), nullable=True)  # GSTIN, EIN, VAT
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_line1: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(128), nullable=False)
    state: Mapped[str] = mapped_column(String(128), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(32), nullable=False)
    country: Mapped[str] = mapped_column(String(64), default="India", nullable=False)
    payment_terms_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    rating_score: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("5.00"), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )
    documents_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    bank_details_masked: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    # Relationships
    contacts: Mapped[list["VendorContact"]] = relationship(
        back_populates="vendor", cascade="all, delete-orphan"
    )
    reviews: Mapped[list["VendorPerformanceReview"]] = relationship(
        back_populates="vendor", cascade="all, delete-orphan"
    )
    quotations: Mapped[list["VendorQuotation"]] = relationship(back_populates="vendor")
    purchase_orders: Mapped[list["PurchaseOrder"]] = relationship(back_populates="vendor")


class VendorContact(TenantScopedModel):
    """Authorized representative or point of contact for a vendor."""

    __tablename__ = "procurement_vendor_contacts"
    __table_args__ = (
        Index("idx_procurement_vendor_contacts_vendor", "tenant_id", "vendor_id"),
    )

    vendor_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_vendors.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    designation: Mapped[str | None] = mapped_column(String(128), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    vendor: Mapped["Vendor"] = relationship(back_populates="contacts")


class VendorPerformanceReview(TenantScopedModel):
    """Historical supplier performance scorecard and procurement rating."""

    __tablename__ = "procurement_vendor_reviews"
    __table_args__ = (
        Index("idx_procurement_vendor_reviews_vendor", "tenant_id", "vendor_id"),
    )

    vendor_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_vendors.id", ondelete="CASCADE"), nullable=False
    )
    review_date: Mapped[date] = mapped_column(Date, nullable=False)
    reviewer_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False
    )
    delivery_score: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 to 5
    quality_score: Mapped[int] = mapped_column(Integer, nullable=False)   # 1 to 5
    pricing_score: Mapped[int] = mapped_column(Integer, nullable=False)   # 1 to 5
    overall_score: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str] = mapped_column(String(64), default="CONTINUE", nullable=False)

    vendor: Mapped["Vendor"] = relationship(back_populates="reviews")


# =============================================================================
# 2. PURCHASE REQUISITIONS & LINES
# =============================================================================


class PurchaseRequisition(TenantScopedModel):
    """Departmental request for purchasing goods, supplies, or services."""

    __tablename__ = "procurement_purchase_requisitions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "requisition_number", name="uq_procurement_req_number"),
        Index("idx_procurement_req_dept", "tenant_id", "department_id"),
        Index("idx_procurement_req_status", "tenant_id", "status"),
    )

    requisition_number: Mapped[str] = mapped_column(String(64), nullable=False)
    department_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_departments.id", ondelete="RESTRICT"), nullable=False
    )
    campus_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_campuses.id", ondelete="RESTRICT"), nullable=False
    )
    requestor_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(64), default=VendorCategory.GOODS, nullable=False)
    priority: Mapped[str] = mapped_column(String(32), default=RequisitionPriority.MEDIUM, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=RequisitionStatus.DRAFT, nullable=False)
    required_date: Mapped[date] = mapped_column(Date, nullable=False)
    delivery_location: Mapped[str] = mapped_column(String(255), nullable=False)
    estimated_total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    currency: Mapped[str] = mapped_column(String(16), default="INR", nullable=False)
    budget_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    approved_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    lines: Mapped[list["PurchaseRequisitionLine"]] = relationship(
        back_populates="requisition", cascade="all, delete-orphan"
    )


class PurchaseRequisitionLine(TenantScopedModel):
    """Line item requested in a purchase requisition."""

    __tablename__ = "procurement_requisition_lines"
    __table_args__ = (
        Index("idx_procurement_req_lines_req", "tenant_id", "requisition_id"),
    )

    requisition_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_purchase_requisitions.id", ondelete="CASCADE"), nullable=False
    )
    item_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_inventory_items.id", ondelete="SET NULL"), nullable=True
    )
    item_description: Mapped[str] = mapped_column(String(255), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(32), default="PCS", nullable=False)
    quantity_requested: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    estimated_unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    estimated_total_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    quantity_ordered: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    quantity_fulfilled: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    specifications: Mapped[str | None] = mapped_column(Text, nullable=True)

    requisition: Mapped["PurchaseRequisition"] = relationship(back_populates="lines")


# =============================================================================
# 3. QUOTATIONS & EVALUATIONS (RFQ)
# =============================================================================


class QuotationRequest(TenantScopedModel):
    """Formal Request for Quotation (RFQ) issued to prospective vendors."""

    __tablename__ = "procurement_quotation_requests"
    __table_args__ = (
        UniqueConstraint("tenant_id", "rfq_number", name="uq_procurement_rfq_number"),
        Index("idx_procurement_rfq_status", "tenant_id", "status"),
    )

    rfq_number: Mapped[str] = mapped_column(String(64), nullable=False)
    requisition_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_purchase_requisitions.id", ondelete="RESTRICT"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    deadline_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=RfqStatus.DRAFT, nullable=False)
    evaluation_criteria_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )  # e.g. {"price_weight": 0.5, "quality_weight": 0.3, "delivery_weight": 0.2}
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    quotations: Mapped[list["VendorQuotation"]] = relationship(
        back_populates="rfq", cascade="all, delete-orphan"
    )
    evaluations: Mapped[list["QuotationEvaluation"]] = relationship(
        back_populates="rfq", cascade="all, delete-orphan"
    )


class VendorQuotation(TenantScopedModel):
    """Commercial and technical quotation submitted by a vendor."""

    __tablename__ = "procurement_vendor_quotations"
    __table_args__ = (
        Index("idx_procurement_quotation_rfq", "tenant_id", "rfq_id"),
        Index("idx_procurement_quotation_vendor", "tenant_id", "vendor_id"),
    )

    rfq_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_quotation_requests.id", ondelete="CASCADE"), nullable=False
    )
    vendor_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_vendors.id", ondelete="RESTRICT"), nullable=False
    )
    quotation_reference: Mapped[str] = mapped_column(String(128), nullable=False)
    submission_date: Mapped[date] = mapped_column(Date, nullable=False)
    validity_until: Mapped[date] = mapped_column(Date, nullable=False)
    total_quoted_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    delivery_lead_days: Mapped[int] = mapped_column(Integer, default=14, nullable=False)
    warranty_months: Mapped[int] = mapped_column(Integer, default=12, nullable=False)
    payment_terms: Mapped[str | None] = mapped_column(String(255), nullable=True)
    document_storage_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default=QuotationStatus.SUBMITTED, nullable=False)
    evaluation_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    disqualification_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    rfq: Mapped["QuotationRequest"] = relationship(back_populates="quotations")
    vendor: Mapped["Vendor"] = relationship(back_populates="quotations")


class QuotationEvaluation(TenantScopedModel):
    """Comparative scoring and procurement committee evaluation."""

    __tablename__ = "procurement_quotation_evaluations"
    __table_args__ = (
        Index("idx_procurement_eval_rfq", "tenant_id", "rfq_id"),
    )

    rfq_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_quotation_requests.id", ondelete="CASCADE"), nullable=False
    )
    evaluator_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False
    )
    evaluation_date: Mapped[date] = mapped_column(Date, nullable=False)
    scoring_details_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    recommended_vendor_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_vendors.id", ondelete="SET NULL"), nullable=True
    )
    award_decision: Mapped[str] = mapped_column(String(32), default=AwardDecision.PENDING, nullable=False)
    single_source_justification: Mapped[str | None] = mapped_column(Text, nullable=True)

    rfq: Mapped["QuotationRequest"] = relationship(back_populates="evaluations")


# =============================================================================
# 4. PURCHASE ORDERS & AMENDMENTS
# =============================================================================


class PurchaseOrder(TenantScopedModel):
    """Binding commercial contract issued to an approved supplier."""

    __tablename__ = "procurement_purchase_orders"
    __table_args__ = (
        UniqueConstraint("tenant_id", "po_number", name="uq_procurement_po_number"),
        Index("idx_procurement_po_vendor", "tenant_id", "vendor_id"),
        Index("idx_procurement_po_status", "tenant_id", "status"),
    )

    po_number: Mapped[str] = mapped_column(String(64), nullable=False)
    requisition_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_purchase_requisitions.id", ondelete="SET NULL"), nullable=True
    )
    rfq_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_quotation_requests.id", ondelete="SET NULL"), nullable=True
    )
    vendor_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_vendors.id", ondelete="RESTRICT"), nullable=False
    )
    vendor_quotation_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_vendor_quotations.id", ondelete="SET NULL"), nullable=True
    )
    campus_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_campuses.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), default=PurchaseOrderStatus.DRAFT, nullable=False)
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_delivery_date: Mapped[date] = mapped_column(Date, nullable=False)
    delivery_address: Mapped[str] = mapped_column(String(255), nullable=False)
    billing_address: Mapped[str] = mapped_column(String(255), nullable=False)
    payment_terms: Mapped[str] = mapped_column(String(128), default="Net 30", nullable=False)
    currency: Mapped[str] = mapped_column(String(16), default="INR", nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    issued_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    version_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    revision_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    # Relationships
    vendor: Mapped["Vendor"] = relationship(back_populates="purchase_orders")
    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        back_populates="purchase_order", cascade="all, delete-orphan"
    )
    amendments: Mapped[list["PurchaseOrderAmendment"]] = relationship(
        back_populates="purchase_order", cascade="all, delete-orphan"
    )
    goods_receipts: Mapped[list["GoodsReceipt"]] = relationship(back_populates="purchase_order")


class PurchaseOrderLine(TenantScopedModel):
    """Itemized line ordered in a purchase order."""

    __tablename__ = "procurement_purchase_order_lines"
    __table_args__ = (
        Index("idx_procurement_po_lines_po", "tenant_id", "po_id"),
    )

    po_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_purchase_orders.id", ondelete="CASCADE"), nullable=False
    )
    requisition_line_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_requisition_lines.id", ondelete="SET NULL"), nullable=True
    )
    item_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_inventory_items.id", ondelete="SET NULL"), nullable=True
    )
    item_description: Mapped[str] = mapped_column(String(255), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(32), default="PCS", nullable=False)
    quantity_ordered: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    quantity_received: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    quantity_accepted: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    quantity_rejected: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    quantity_invoiced: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    purchase_order: Mapped["PurchaseOrder"] = relationship(back_populates="lines")


class PurchaseOrderAmendment(TenantScopedModel):
    """Versioned change record to an issued purchase order."""

    __tablename__ = "procurement_po_amendments"
    __table_args__ = (
        Index("idx_procurement_po_amendments_po", "tenant_id", "po_id"),
    )

    po_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_purchase_orders.id", ondelete="CASCADE"), nullable=False
    )
    amendment_number: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    changes_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    requested_by_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False
    )
    approved_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default=AmendmentStatus.PENDING, nullable=False)

    purchase_order: Mapped["PurchaseOrder"] = relationship(back_populates="amendments")


# =============================================================================
# 5. GOODS RECEIPT & QUALITY INSPECTION
# =============================================================================


class GoodsReceipt(TenantScopedModel):
    """Goods Receipt Note (GRN) recording delivery against an active PO."""

    __tablename__ = "procurement_goods_receipts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "grn_number", name="uq_procurement_grn_number"),
        Index("idx_procurement_grn_po", "tenant_id", "po_id"),
        Index("idx_procurement_grn_status", "tenant_id", "status"),
    )

    grn_number: Mapped[str] = mapped_column(String(64), nullable=False)
    po_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_purchase_orders.id", ondelete="RESTRICT"), nullable=False
    )
    vendor_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_vendors.id", ondelete="RESTRICT"), nullable=False
    )
    receipt_date: Mapped[date] = mapped_column(Date, nullable=False)
    received_by_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False
    )
    carrier_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tracking_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    delivery_note_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default=GoodsReceiptStatus.RECEIVED, nullable=False)
    storage_location_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_inventory_locations.id", ondelete="SET NULL"), nullable=True
    )
    inspection_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    quality_status: Mapped[str] = mapped_column(
        String(32), default=QualityInspectionStatus.PENDING, nullable=False
    )
    inspected_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )
    inspected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(back_populates="goods_receipts")
    lines: Mapped[list["GoodsReceiptLine"]] = relationship(
        back_populates="goods_receipt", cascade="all, delete-orphan"
    )


class GoodsReceiptLine(TenantScopedModel):
    """Line item receipt quantity and quality inspection outcome."""

    __tablename__ = "procurement_goods_receipt_lines"
    __table_args__ = (
        Index("idx_procurement_grn_lines_grn", "tenant_id", "grn_id"),
    )

    grn_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_goods_receipts.id", ondelete="CASCADE"), nullable=False
    )
    po_line_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_purchase_order_lines.id", ondelete="RESTRICT"), nullable=False
    )
    item_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_inventory_items.id", ondelete="SET NULL"), nullable=True
    )
    item_description: Mapped[str] = mapped_column(String(255), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(32), default="PCS", nullable=False)
    quantity_received: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    quantity_accepted: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    quantity_rejected: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    batch_lot_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    goods_receipt: Mapped["GoodsReceipt"] = relationship(back_populates="lines")


# =============================================================================
# 6. INVENTORY LOCATIONS, ITEMS, BALANCES & MOVEMENTS
# =============================================================================


class InventoryLocation(TenantScopedModel):
    """Physical stockroom, central warehouse, or laboratory dispensary."""

    __tablename__ = "procurement_inventory_locations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_procurement_location_code"),
        Index("idx_procurement_location_campus", "tenant_id", "campus_id"),
    )

    campus_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_campuses.id", ondelete="RESTRICT"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    type: Mapped[str] = mapped_column(String(32), default=LocationType.CENTRAL_WAREHOUSE, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    balances: Mapped[list["StockBalance"]] = relationship(back_populates="location")


class InventoryItem(TenantScopedModel):
    """Catalogue of stocked consumables, equipment, and materials."""

    __tablename__ = "procurement_inventory_items"
    __table_args__ = (
        UniqueConstraint("tenant_id", "sku", name="uq_procurement_item_sku"),
        Index("idx_procurement_item_category", "tenant_id", "category"),
    )

    sku: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(64), default=ItemCategory.STATIONERY, nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(32), default="PCS", nullable=False)
    unit_price_average: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    reorder_threshold: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("10.00"), nullable=False)
    reorder_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("50.00"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    balances: Mapped[list["StockBalance"]] = relationship(back_populates="item")


class StockBalance(TenantScopedModel):
    """Aggregate stock levels per item per location."""

    __tablename__ = "procurement_stock_balances"
    __table_args__ = (
        UniqueConstraint("tenant_id", "item_id", "location_id", name="uq_procurement_stock_balance"),
        Index("idx_procurement_stock_item", "tenant_id", "item_id"),
    )

    item_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_inventory_items.id", ondelete="CASCADE"), nullable=False
    )
    location_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_inventory_locations.id", ondelete="CASCADE"), nullable=False
    )
    quantity_on_hand: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    quantity_reserved: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    quantity_available: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    quantity_in_transit: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    last_reconciled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    item: Mapped["InventoryItem"] = relationship(back_populates="balances")
    location: Mapped["InventoryLocation"] = relationship(back_populates="balances")


class StockMovement(TenantScopedModel):
    """Immutable transactional ledger of stock movements and adjustments."""

    __tablename__ = "procurement_stock_movements"
    __table_args__ = (
        UniqueConstraint("tenant_id", "movement_number", name="uq_procurement_movement_number"),
        Index("idx_procurement_movements_item", "tenant_id", "item_id"),
        Index("idx_procurement_movements_type", "tenant_id", "movement_type"),
    )

    movement_number: Mapped[str] = mapped_column(String(64), nullable=False)
    item_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_inventory_items.id", ondelete="RESTRICT"), nullable=False
    )
    movement_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_location_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_inventory_locations.id", ondelete="RESTRICT"), nullable=True
    )
    destination_location_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_inventory_locations.id", ondelete="RESTRICT"), nullable=True
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    total_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    reference_type: Mapped[str | None] = mapped_column(String(64), nullable=True)  # GRN, INTERNAL_REQUEST, PO, ADJUSTMENT
    reference_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    performed_by_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


# =============================================================================
# 7. INTERNAL STOCK REQUESTS
# =============================================================================


class InternalStockRequest(TenantScopedModel):
    """Departmental request to issue materials from an institutional store."""

    __tablename__ = "procurement_internal_stock_requests"
    __table_args__ = (
        UniqueConstraint("tenant_id", "request_number", name="uq_procurement_internal_req_number"),
        Index("idx_procurement_internal_req_dept", "tenant_id", "department_id"),
        Index("idx_procurement_internal_req_status", "tenant_id", "status"),
    )

    request_number: Mapped[str] = mapped_column(String(64), nullable=False)
    department_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("core_departments.id", ondelete="RESTRICT"), nullable=False
    )
    requestor_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False
    )
    location_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_inventory_locations.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), default=InternalRequestStatus.PENDING, nullable=False)
    required_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    lines: Mapped[list["InternalStockRequestLine"]] = relationship(
        back_populates="request", cascade="all, delete-orphan"
    )


class InternalStockRequestLine(TenantScopedModel):
    """Item line requested in an internal departmental stock requisition."""

    __tablename__ = "procurement_internal_stock_request_lines"
    __table_args__ = (
        Index("idx_procurement_internal_req_lines", "tenant_id", "request_id"),
    )

    request_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_internal_stock_requests.id", ondelete="CASCADE"), nullable=False
    )
    item_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_inventory_items.id", ondelete="RESTRICT"), nullable=False
    )
    quantity_requested: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    quantity_issued: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)

    request: Mapped["InternalStockRequest"] = relationship(back_populates="lines")


# =============================================================================
# 8. THREE-WAY INVOICE MATCHING
# =============================================================================


class SupplierInvoiceMatch(TenantScopedModel):
    """Three-way match reconciliation record between PO, GRN, and Supplier Invoice."""

    __tablename__ = "procurement_supplier_invoice_matches"
    __table_args__ = (
        UniqueConstraint("tenant_id", "match_reference", name="uq_procurement_match_ref"),
        Index("idx_procurement_match_po", "tenant_id", "po_id"),
        Index("idx_procurement_match_grn", "tenant_id", "grn_id"),
    )

    match_reference: Mapped[str] = mapped_column(String(64), nullable=False)
    po_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_purchase_orders.id", ondelete="RESTRICT"), nullable=False
    )
    grn_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_goods_receipts.id", ondelete="RESTRICT"), nullable=False
    )
    invoice_reference_number: Mapped[str] = mapped_column(String(128), nullable=False)
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    invoice_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    po_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    received_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    quantity_variance: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    price_variance: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=InvoiceMatchStatus.MATCHED, nullable=False)
    matched_by_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False
    )
    matched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    variance_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    override_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    override_approved_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True
    )


# =============================================================================
# 9. VENDOR RETURNS (RTV)
# =============================================================================


class VendorReturn(TenantScopedModel):
    """Return to Vendor (RTV) record for defective, damaged, or excess goods."""

    __tablename__ = "procurement_vendor_returns"
    __table_args__ = (
        UniqueConstraint("tenant_id", "return_number", name="uq_procurement_return_number"),
        Index("idx_procurement_return_vendor", "tenant_id", "vendor_id"),
        Index("idx_procurement_return_po", "tenant_id", "po_id"),
    )

    return_number: Mapped[str] = mapped_column(String(64), nullable=False)
    po_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_purchase_orders.id", ondelete="RESTRICT"), nullable=False
    )
    grn_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_goods_receipts.id", ondelete="SET NULL"), nullable=True
    )
    vendor_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_vendors.id", ondelete="RESTRICT"), nullable=False
    )
    item_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("procurement_inventory_items.id", ondelete="SET NULL"), nullable=True
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    reason: Mapped[str] = mapped_column(String(32), default=VendorReturnReason.DEFECTIVE, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=VendorReturnStatus.REQUESTED, nullable=False)
    resolution_type: Mapped[str] = mapped_column(
        String(32), default=ReturnResolutionType.REPLACEMENT, nullable=False
    )
    resolution_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    credit_note_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    created_by_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False
    )
