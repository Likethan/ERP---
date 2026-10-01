"""Pydantic request and response schemas for Finance, Fees & Billing Engine."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Fee Categories
# ---------------------------------------------------------------------------


class FeeCategoryBase(BaseModel):
    code: str = Field(..., max_length=32, description="Unique category code, e.g. TUITION, HOSTEL")
    name: str = Field(..., max_length=128, description="Human readable category name")
    description: str | None = Field(None, max_length=255)
    is_refundable: bool = Field(False, description="Whether fee under this head is refundable")
    is_active: bool = Field(True, description="Whether fee category is currently active")


class FeeCategoryCreate(FeeCategoryBase):
    pass


class FeeCategoryUpdate(BaseModel):
    name: str | None = Field(None, max_length=128)
    description: str | None = Field(None, max_length=255)
    is_refundable: bool | None = None
    is_active: bool | None = None


class FeeCategoryResponse(FeeCategoryBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Fee Items (Line items within a fee structure)
# ---------------------------------------------------------------------------


class FeeItemCreate(BaseModel):
    category_id: UUID
    name: str = Field(..., max_length=128)
    amount: Decimal = Field(..., ge=0, description="Amount with exact 2 decimal places")
    is_optional: bool = False
    sequence: int = Field(1, ge=1)


class FeeItemResponse(BaseModel):
    id: UUID
    fee_structure_id: UUID
    category_id: UUID
    category_name: str | None = None
    category_code: str | None = None
    name: str
    amount: Decimal
    is_optional: bool
    sequence: int

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Fee Structure
# ---------------------------------------------------------------------------


class FeeStructureCreate(BaseModel):
    program_id: UUID
    academic_year_id: UUID
    semester_id: UUID | None = None
    batch_id: UUID | None = None
    quota_type: str = Field("GENERAL", max_length=32)
    name: str = Field(..., max_length=128)
    items: list[FeeItemCreate] = Field(default_factory=list)


class FeeStructureUpdate(BaseModel):
    name: str | None = Field(None, max_length=128)
    quota_type: str | None = Field(None, max_length=32)
    status: str | None = Field(None, max_length=32)


class FeeStructureResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    program_id: UUID
    program_name: str | None = None
    academic_year_id: UUID
    academic_year_name: str | None = None
    semester_id: UUID | None = None
    semester_name: str | None = None
    batch_id: UUID | None = None
    batch_name: str | None = None
    quota_type: str
    name: str
    status: str
    version: int
    total_amount: Decimal = Decimal("0.00")
    items: list[FeeItemResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Student Fee Assignment
# ---------------------------------------------------------------------------


class StudentFeeAssignmentCreate(BaseModel):
    student_id: UUID
    fee_structure_id: UUID
    academic_year_id: UUID
    semester_id: UUID | None = None
    remarks: str | None = None


class StudentFeeAssignmentResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    student_id: UUID
    student_name: str | None = None
    student_roll_number: str | None = None
    student_admission_number: str | None = None
    fee_structure_id: UUID
    fee_structure_name: str | None = None
    academic_year_id: UUID
    academic_year_name: str | None = None
    semester_id: UUID | None = None
    status: str
    assigned_date: date
    remarks: str | None = None
    total_amount: Decimal = Decimal("0.00")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Invoices & Invoice Lines
# ---------------------------------------------------------------------------


class InvoiceLineCreate(BaseModel):
    category_id: UUID
    description: str = Field(..., max_length=255)
    amount: Decimal = Field(..., ge=0)
    waived_amount: Decimal = Field(Decimal("0.00"), ge=0)


class InvoiceLineResponse(BaseModel):
    id: UUID
    invoice_id: UUID
    category_id: UUID
    category_name: str | None = None
    description: str
    amount: Decimal
    waived_amount: Decimal

    model_config = ConfigDict(from_attributes=True)


class InvoiceCreate(BaseModel):
    student_id: UUID
    academic_year_id: UUID
    semester_id: UUID | None = None
    due_date: date
    currency: str = Field("INR", max_length=8)
    fee_structure_id: UUID | None = None
    items: list[InvoiceLineCreate] | None = None
    apply_scholarships: bool = True
    remarks: str | None = None


class InvoiceUpdate(BaseModel):
    due_date: date | None = None
    remarks: str | None = None


class InvoiceResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    student_id: UUID
    student_name: str | None = None
    student_roll_number: str | None = None
    student_admission_number: str | None = None
    academic_year_id: UUID
    academic_year_name: str | None = None
    semester_id: UUID | None = None
    semester_name: str | None = None
    invoice_number: str
    issue_date: date
    due_date: date
    currency: str
    gross_amount: Decimal
    concession_amount: Decimal
    adjustment_amount: Decimal
    net_payable: Decimal
    paid_amount: Decimal
    balance_amount: Decimal
    status: str
    remarks: str | None = None
    is_overdue: bool = False
    items: list[InvoiceLineResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Payments & Allocations
# ---------------------------------------------------------------------------


class PaymentAllocationItem(BaseModel):
    invoice_id: UUID
    amount: Decimal = Field(..., gt=0)


class PaymentCreate(BaseModel):
    student_id: UUID
    amount: Decimal = Field(..., gt=0)
    payment_mode: str = Field("BANK_TRANSFER", max_length=32)
    transaction_reference: str = Field(..., max_length=128)
    payment_date: datetime | None = None
    currency: str = Field("INR", max_length=8)
    gateway_provider: str | None = None
    gateway_transaction_id: str | None = None
    allocations: list[PaymentAllocationItem] | None = None
    remarks: str | None = None


class PaymentAllocationResponse(BaseModel):
    id: UUID
    payment_id: UUID
    invoice_id: UUID
    invoice_number: str | None = None
    allocated_amount: Decimal
    allocated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    student_id: UUID
    student_name: str | None = None
    student_roll_number: str | None = None
    payment_number: str
    transaction_reference: str
    payment_mode: str
    gateway_provider: str | None = None
    gateway_transaction_id: str | None = None
    payment_date: datetime
    amount: Decimal
    currency: str
    status: str
    received_by_user_id: UUID | None = None
    received_by_name: str | None = None
    remarks: str | None = None
    allocations: list[PaymentAllocationResponse] = Field(default_factory=list)
    receipt_number: str | None = None
    receipt_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Receipts
# ---------------------------------------------------------------------------


class ReceiptResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    payment_id: UUID
    payment_number: str
    receipt_number: str
    student_id: UUID
    student_name: str | None = None
    student_roll_number: str | None = None
    student_admission_number: str | None = None
    amount: Decimal
    currency: str
    payment_mode: str
    transaction_reference: str
    issue_date: datetime
    is_cancelled: bool
    invoice_numbers: list[str] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Scholarships & Concessions
# ---------------------------------------------------------------------------


class ScholarshipCreate(BaseModel):
    student_id: UUID
    academic_year_id: UUID
    category_id: UUID | None = None
    concession_name: str = Field(..., max_length=128)
    concession_type: str = Field("SCHOLARSHIP", max_length=32)
    amount: Decimal = Field(..., ge=0)
    percentage: Decimal | None = Field(None, ge=0, le=100)
    remarks: str | None = None


class ScholarshipResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    student_id: UUID
    student_name: str | None = None
    student_roll_number: str | None = None
    academic_year_id: UUID
    academic_year_name: str | None = None
    category_id: UUID | None = None
    category_name: str | None = None
    concession_name: str
    concession_type: str
    amount: Decimal
    percentage: Decimal | None = None
    status: str
    approved_by_user_id: UUID | None = None
    approved_by_name: str | None = None
    remarks: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Financial Adjustments (Debit/Credit Notes)
# ---------------------------------------------------------------------------


class FinancialAdjustmentCreate(BaseModel):
    invoice_id: UUID
    adjustment_type: str = Field(..., max_length=16, description="DEBIT or CREDIT")
    amount: Decimal = Field(..., gt=0)
    reason: str = Field(...)


class FinancialAdjustmentResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    invoice_id: UUID
    invoice_number: str | None = None
    adjustment_type: str
    amount: Decimal
    reason: str
    status: str
    requested_by_user_id: UUID | None = None
    requested_by_name: str | None = None
    approved_by_user_id: UUID | None = None
    approved_by_name: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Refunds
# ---------------------------------------------------------------------------


class RefundCreate(BaseModel):
    payment_id: UUID
    refund_amount: Decimal = Field(..., gt=0)
    reason: str = Field(...)
    refund_mode: str = Field("ORIGINAL_METHOD", max_length=32)
    refund_reference: str | None = Field(None, max_length=128)


class RefundResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    payment_id: UUID
    payment_number: str | None = None
    student_id: UUID | None = None
    student_name: str | None = None
    refund_amount: Decimal
    reason: str
    status: str
    refund_mode: str
    refund_reference: str | None = None
    requested_by_user_id: UUID | None = None
    requested_by_name: str | None = None
    approved_by_user_id: UUID | None = None
    approved_by_name: str | None = None
    processed_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Telemetry & Summaries
# ---------------------------------------------------------------------------


class FinanceDashboard(BaseModel):
    total_billed: Decimal = Decimal("0.00")
    total_collected: Decimal = Decimal("0.00")
    total_outstanding: Decimal = Decimal("0.00")
    total_overdue: Decimal = Decimal("0.00")
    active_fee_structures_count: int = 0
    pending_payments_count: int = 0
    pending_refunds_count: int = 0
    total_scholarships_granted: Decimal = Decimal("0.00")
    recent_payments: list[PaymentResponse] = Field(default_factory=list)
    recent_invoices: list[InvoiceResponse] = Field(default_factory=list)


class StudentFinancialSummary(BaseModel):
    student_id: UUID
    student_name: str
    student_roll_number: str | None = None
    student_admission_number: str
    total_invoiced: Decimal = Decimal("0.00")
    total_paid: Decimal = Decimal("0.00")
    total_outstanding: Decimal = Decimal("0.00")
    total_overdue: Decimal = Decimal("0.00")
    total_concessions: Decimal = Decimal("0.00")
    invoices: list[InvoiceResponse] = Field(default_factory=list)
    payments: list[PaymentResponse] = Field(default_factory=list)
    scholarships: list[ScholarshipResponse] = Field(default_factory=list)
