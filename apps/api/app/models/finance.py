from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TenantScopedModel


class FeeCategory(TenantScopedModel):
    """Institutional billing fee category (Tuition, Hostel, Bus, Exam, Lab, Library)."""

    __tablename__ = "finance_fee_categories"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_fee_categories_code"),)

    # Category codes: TUITION, HOSTEL, TRANSPORT, EXAMINATION, LIBRARY, LABORATORY, SPORTS, REGISTRATION, OTHER
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_refundable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class FeeStructure(TenantScopedModel):
    """Fee matrix defined for a program, term, and batch."""

    __tablename__ = "finance_fee_structures"

    program_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_programs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    academic_year_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_academic_years.id", ondelete="RESTRICT"),
        nullable=False,
    )
    semester_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_semesters.id", ondelete="RESTRICT"),
        nullable=True,
    )
    batch_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_batches.id", ondelete="RESTRICT"),
        nullable=True,
    )
    quota_type: Mapped[str] = mapped_column(
        String(32), default="GENERAL", nullable=False
    )  # GENERAL, MANAGEMENT, GOVERNMENT, NRI, MERIT
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="DRAFT", nullable=False
    )  # DRAFT, APPROVED, ACTIVE, RETIRED
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    items: Mapped[list["FeeItem"]] = relationship(
        back_populates="fee_structure", cascade="all, delete-orphan"
    )


class FeeItem(Base):
    """Specific line item within a fee structure."""

    __tablename__ = "finance_fee_items"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False
    )
    fee_structure_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("finance_fee_structures.id", ondelete="CASCADE"),
        nullable=False,
    )
    category_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("finance_fee_categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    is_optional: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    fee_structure: Mapped["FeeStructure"] = relationship(back_populates="items")


class StudentFeeAssignment(TenantScopedModel):
    """Authoritative binding between a student and an applicable FeeStructure."""

    __tablename__ = "finance_fee_assignments"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "student_id",
            "academic_year_id",
            "fee_structure_id",
            name="uq_student_fee_assignment",
        ),
    )

    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    fee_structure_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("finance_fee_structures.id", ondelete="RESTRICT"),
        nullable=False,
    )
    academic_year_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_academic_years.id", ondelete="RESTRICT"),
        nullable=False,
    )
    semester_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_semesters.id", ondelete="RESTRICT"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32), default="ACTIVE", nullable=False
    )  # PENDING, ACTIVE, INVOICED, CANCELLED
    assigned_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    fee_structure: Mapped["FeeStructure"] = relationship()


class StudentFeeConcession(TenantScopedModel):
    """Scholarships, discounts, or fee waivers granted to a student."""

    __tablename__ = "finance_concessions"

    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    category_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("finance_fee_categories.id", ondelete="RESTRICT"),
        nullable=True,
    )
    academic_year_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_academic_years.id", ondelete="RESTRICT"),
        nullable=False,
    )
    concession_name: Mapped[str] = mapped_column(String(128), default="Scholarship", nullable=False)
    concession_type: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # SCHOLARSHIP, SIBLING_DISCOUNT, MERIT, WAIVER, PERCENTAGE, FIXED_AMOUNT
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    percentage: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default="APPROVED", nullable=False
    )  # PENDING, APPROVED, REJECTED
    approved_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)


class Invoice(TenantScopedModel):
    """Institutional billing statement issued to a student."""

    __tablename__ = "finance_invoices"
    __table_args__ = (
        UniqueConstraint("tenant_id", "invoice_number", name="uq_invoices_tenant_number"),
    )

    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    academic_year_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_academic_years.id", ondelete="RESTRICT"),
        nullable=False,
    )
    semester_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_semesters.id", ondelete="RESTRICT"),
        nullable=True,
    )
    invoice_number: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g., INV-2026-000001
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="INR", nullable=False)
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    concession_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    adjustment_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    net_payable: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    paid_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    balance_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="DRAFT", nullable=False
    )  # DRAFT, ISSUED, PARTIALLY_PAID, PAID, OVERDUE, CANCELLED
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    items: Mapped[list["InvoiceLineItem"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan"
    )
    allocations: Mapped[list["PaymentAllocation"]] = relationship(back_populates="invoice")
    adjustments: Mapped[list["FinancialAdjustment"]] = relationship(back_populates="invoice")


class InvoiceLineItem(Base):
    """Itemized line head on a student invoice."""

    __tablename__ = "finance_invoice_items"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False
    )
    invoice_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("finance_invoices.id", ondelete="CASCADE"),
        nullable=False,
    )
    category_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("finance_fee_categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    waived_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )

    invoice: Mapped["Invoice"] = relationship(back_populates="items")


class PaymentTransaction(TenantScopedModel):
    """Immutable record of inward financial transaction."""

    __tablename__ = "finance_payments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "payment_number", name="uq_payments_tenant_number"),
    )

    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    payment_number: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g., PAY-2026-000001
    transaction_reference: Mapped[str] = mapped_column(String(128), nullable=False)
    payment_mode: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # CASH, BANK_TRANSFER, UPI, CARD, CHEQUE, DD, NEFT_RTGS, ONLINE_GATEWAY
    gateway_provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    gateway_transaction_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    payment_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="INR", nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="SUCCESS", nullable=False
    )  # PENDING, SUCCESS, FAILED, CANCELLED, REFUNDED, PARTIALLY_REFUNDED
    received_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    allocations: Mapped[list["PaymentAllocation"]] = relationship(back_populates="payment")
    receipt: Mapped["Receipt | None"] = relationship(back_populates="payment", uselist=False)


class PaymentAllocation(Base):
    """Explicit credit allocation from a payment transaction to an invoice."""

    __tablename__ = "finance_allocations"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False
    )
    payment_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("finance_payments.id", ondelete="RESTRICT"),
        nullable=False,
    )
    invoice_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("finance_invoices.id", ondelete="RESTRICT"),
        nullable=False,
    )
    allocated_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    allocated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    payment: Mapped["PaymentTransaction"] = relationship(back_populates="allocations")
    invoice: Mapped["Invoice"] = relationship(back_populates="allocations")


class Receipt(TenantScopedModel):
    """Official legal receipt generated upon successful payment allocation."""

    __tablename__ = "finance_receipts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "receipt_number", name="uq_receipts_tenant_number"),
    )

    payment_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("finance_payments.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    receipt_number: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g., RCP-2026-000001
    issue_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    pdf_storage_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    payment: Mapped["PaymentTransaction"] = relationship(back_populates="receipt")


class RefundTransaction(TenantScopedModel):
    """Controlled refund disbursement."""

    __tablename__ = "finance_refunds"

    payment_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("finance_payments.id", ondelete="RESTRICT"),
        nullable=False,
    )
    refund_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    requested_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32), default="REQUESTED", nullable=False
    )  # REQUESTED, APPROVED, PROCESSED, REJECTED
    refund_mode: Mapped[str] = mapped_column(
        String(32), default="ORIGINAL_METHOD", nullable=False
    )  # ORIGINAL_METHOD, BANK_TRANSFER, CASH, CHEQUE
    refund_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class FinancialAdjustment(TenantScopedModel):
    """Debit/Credit notes modifying an invoice balance without destroying history."""

    __tablename__ = "finance_adjustments"

    invoice_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("finance_invoices.id", ondelete="RESTRICT"),
        nullable=False,
    )
    adjustment_type: Mapped[str] = mapped_column(String(16), nullable=False)  # DEBIT, CREDIT
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    requested_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32), default="APPROVED", nullable=False
    )  # PENDING, APPROVED, REJECTED

    invoice: Mapped["Invoice"] = relationship(back_populates="adjustments")
