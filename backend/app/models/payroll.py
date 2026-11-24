"""Enterprise Payroll, Compensation, Benefits & Statutory Compliance Models (Step 52).

CampusOS Tagline: "One Campus. One System. One Source of Truth."

Integrates with:
- Workforce Management (WorkforceEmployee, departments, campuses)
- People (User profiles, roles)
- Leave & Attendance (Leave deductions, attendance proration)
- Finance (Accounting journal mapping, debit/credit balanced ledgers)
- Document Storage & Payslips
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
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

from app.models.base import Base, TenantScopedModel

if TYPE_CHECKING:
    from app.models.workforce import WorkforceEmployee

JSONB_COMPAT = JSON().with_variant(JSONB, "postgresql")


# -----------------------------------------------------------------------------
# 1. Enums
# -----------------------------------------------------------------------------


class PayFrequency(StrEnum):
    """Institutional payroll disbursement cycle."""

    MONTHLY = "MONTHLY"
    BI_WEEKLY = "BI_WEEKLY"
    SEMI_MONTHLY = "SEMI_MONTHLY"
    WEEKLY = "WEEKLY"


class ComponentType(StrEnum):
    """Classification of salary components."""

    EARNING = "EARNING"
    DEDUCTION = "DEDUCTION"
    EMPLOYER_CONTRIBUTION = "EMPLOYER_CONTRIBUTION"


class CalculationMethod(StrEnum):
    """Evaluation strategy for compensation line items."""

    FLAT_AMOUNT = "FLAT_AMOUNT"
    PERCENTAGE_OF_BASIC = "PERCENTAGE_OF_BASIC"
    PERCENTAGE_OF_GROSS = "PERCENTAGE_OF_GROSS"
    FORMULA = "FORMULA"


class TaxabilityType(StrEnum):
    """Income tax treatment for compensation components."""

    TAXABLE = "TAXABLE"
    EXEMPT = "EXEMPT"
    PARTIALLY_EXEMPT = "PARTIALLY_EXEMPT"


class PayrollRunStatus(StrEnum):
    """State machine lifecycle for institutional payroll execution."""

    DRAFT = "DRAFT"
    CALCULATING = "CALCULATING"
    CALCULATED = "CALCULATED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    POSTED = "POSTED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class PaymentBatchStatus(StrEnum):
    """Lifecycle for bank disbursement batches."""

    PREPARED = "PREPARED"
    APPROVED = "APPROVED"
    EXPORTED = "EXPORTED"
    PARTIALLY_RECONCILED = "PARTIALLY_RECONCILED"
    RECONCILED = "RECONCILED"
    FAILED = "FAILED"


class PaymentMethod(StrEnum):
    """Disbursement channel for employee net compensation."""

    BANK_TRANSFER = "BANK_TRANSFER"
    DIRECT_DEPOSIT = "DIRECT_DEPOSIT"
    CHEQUE = "CHEQUE"
    CASH = "CASH"


class StatutoryJurisdiction(StrEnum):
    """Compliance tax & social security framework taxonomy."""

    IN_PF = "IN_PF"                     # India Employees' Provident Fund
    IN_ESI = "IN_ESI"                   # India Employee State Insurance
    IN_PT = "IN_PT"                     # India Professional Tax
    IN_TDS = "IN_TDS"                   # India Tax Deducted at Source
    US_FICA = "US_FICA"                 # US FICA (Social Security & Medicare)
    US_FEDERAL_TAX = "US_FEDERAL_TAX"   # US Federal Income Withholding
    GENERAL = "GENERAL"                 # Institution-defined generic rule


# -----------------------------------------------------------------------------
# 2. Salary Grades & Compensation Structures
# -----------------------------------------------------------------------------


class SalaryGrade(TenantScopedModel):
    """Institutional pay band, scale, or hierarchy level."""

    __tablename__ = "payroll_salary_grades"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_salary_grade_tenant_code"),
        Index("ix_salary_grade_tenant", "tenant_id", "is_active"),
    )

    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    min_base_pay: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    max_base_pay: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class SalaryComponent(TenantScopedModel):
    """Reusable compensation building block (allowance, deduction, contribution)."""

    __tablename__ = "payroll_salary_components"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_salary_comp_tenant_code"),
        Index("ix_salary_comp_tenant_type", "tenant_id", "component_type", "is_active"),
    )

    code: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g., BASIC, HRA, PF_EMP, ESI_EMP, PROF_TAX
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    component_type: Mapped[str] = mapped_column(String(32), nullable=False)  # ComponentType
    calculation_method: Mapped[str] = mapped_column(
        String(32), default=CalculationMethod.FLAT_AMOUNT, nullable=False
    )
    default_value: Mapped[Decimal] = mapped_column(Numeric(12, 4), default=Decimal("0.0000"), nullable=False)
    is_statutory: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    taxability: Mapped[str] = mapped_column(String(32), default=TaxabilityType.TAXABLE, nullable=False)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class SalaryStructure(TenantScopedModel):
    """Master compensation formula template grouping components."""

    __tablename__ = "payroll_salary_structures"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_salary_struct_tenant_code"),
        Index("ix_salary_struct_tenant", "tenant_id", "is_active"),
    )

    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    currency: Mapped[str] = mapped_column(String(8), default="INR", nullable=False)
    pay_frequency: Mapped[str] = mapped_column(String(32), default=PayFrequency.MONTHLY, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    items: Mapped[list["SalaryStructureItem"]] = relationship(
        back_populates="structure", cascade="all, delete-orphan", order_by="SalaryStructureItem.sequence"
    )


class SalaryStructureItem(Base):
    """Junction configuring a component within a structure."""

    __tablename__ = "payroll_salary_structure_items"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    structure_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("payroll_salary_structures.id", ondelete="CASCADE"),
        nullable=False,
    )
    component_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("payroll_salary_components.id", ondelete="RESTRICT"),
        nullable=False,
    )
    calculation_method: Mapped[str] = mapped_column(String(32), nullable=False)
    factor_value: Mapped[Decimal] = mapped_column(Numeric(12, 4), default=Decimal("0.0000"), nullable=False)
    fixed_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    structure: Mapped["SalaryStructure"] = relationship(back_populates="items")
    component: Mapped["SalaryComponent"] = relationship()


# -----------------------------------------------------------------------------
# 3. Employee Compensation Assignments & History
# -----------------------------------------------------------------------------


class EmployeeCompensation(TenantScopedModel):
    """Authoritative effective-dated compensation record for an individual employee."""

    __tablename__ = "payroll_employee_compensations"
    __table_args__ = (
        Index("ix_emp_comp_tenant_emp_active", "tenant_id", "employee_id", "is_active"),
        Index("ix_emp_comp_dates", "tenant_id", "employee_id", "effective_from", "effective_to"),
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workforce_employees.id", ondelete="RESTRICT"),
        nullable=False,
    )
    structure_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("payroll_salary_structures.id", ondelete="RESTRICT"),
        nullable=False,
    )
    salary_grade_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("payroll_salary_grades.id", ondelete="SET NULL"),
        nullable=True,
    )
    annual_ctc: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    monthly_gross: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    base_pay: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    currency: Mapped[str] = mapped_column(String(8), default="INR", nullable=False)
    custom_components: Mapped[dict] = mapped_column(JSONB_COMPAT, default=dict, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    employee: Mapped["WorkforceEmployee"] = relationship("WorkforceEmployee")
    structure: Mapped["SalaryStructure"] = relationship("SalaryStructure")
    salary_grade: Mapped["SalaryGrade | None"] = relationship("SalaryGrade")


class EmployeeCompensationHistory(TenantScopedModel):
    """Immutable audit trail of compensation revisions."""

    __tablename__ = "payroll_compensation_history"
    __table_args__ = (
        Index("ix_comp_hist_tenant_emp", "tenant_id", "employee_id", "effective_date"),
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workforce_employees.id", ondelete="RESTRICT"),
        nullable=False,
    )
    compensation_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("payroll_employee_compensations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    previous_annual_ctc: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    new_annual_ctc: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    previous_monthly_gross: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    new_monthly_gross: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    change_reason: Mapped[str] = mapped_column(String(255), nullable=False)
    authorized_by_user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )


class EmployeeBankDetail(TenantScopedModel):
    """Secure banking profile for direct salary disbursement."""

    __tablename__ = "payroll_employee_bank_details"
    __table_args__ = (
        Index("ix_bank_detail_tenant_emp", "tenant_id", "employee_id", "is_primary"),
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workforce_employees.id", ondelete="RESTRICT"),
        nullable=False,
    )
    account_holder_name: Mapped[str] = mapped_column(String(128), nullable=False)
    bank_name: Mapped[str] = mapped_column(String(128), nullable=False)
    account_number_masked: Mapped[str] = mapped_column(String(32), nullable=False)  # e.g., *******1234
    account_number_encrypted: Mapped[str] = mapped_column(String(255), nullable=False)
    ifsc_code: Mapped[str] = mapped_column(String(32), nullable=False)  # or SWIFT/routing
    branch_name: Mapped[str] = mapped_column(String(128), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# -----------------------------------------------------------------------------
# 4. Payroll Calendars & Periods
# -----------------------------------------------------------------------------


class PayrollCalendar(TenantScopedModel):
    """Institutional scheduling template for payroll frequency and cutoff windows."""

    __tablename__ = "payroll_calendars"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_payroll_calendar_tenant_name"),
    )

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    pay_frequency: Mapped[str] = mapped_column(String(32), default=PayFrequency.MONTHLY, nullable=False)
    cutoff_day_of_month: Mapped[int] = mapped_column(Integer, default=25, nullable=False)  # Cutoff for attendance/leave
    pay_day_of_month: Mapped[int] = mapped_column(Integer, default=30, nullable=False)     # Pay disbursement date
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    periods: Mapped[list["PayrollPeriod"]] = relationship(
        back_populates="calendar", cascade="all, delete-orphan", order_by="PayrollPeriod.start_date"
    )


class PayrollPeriod(TenantScopedModel):
    """Discrete operational pay cycle (e.g. August 2026)."""

    __tablename__ = "payroll_periods"
    __table_args__ = (
        UniqueConstraint("tenant_id", "calendar_id", "period_code", name="uq_period_tenant_code"),
        Index("ix_period_tenant_dates", "tenant_id", "start_date", "end_date"),
    )

    calendar_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("payroll_calendars.id", ondelete="RESTRICT"),
        nullable=False,
    )
    period_code: Mapped[str] = mapped_column(String(32), nullable=False)  # e.g. "2026-08"
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    cutoff_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    calendar: Mapped["PayrollCalendar"] = relationship(back_populates="periods")
    payroll_runs: Mapped[list["PayrollRun"]] = relationship(back_populates="period")


# -----------------------------------------------------------------------------
# 5. Payroll Runs & Calculation Ledger
# -----------------------------------------------------------------------------


class PayrollRun(TenantScopedModel):
    """Institutional payroll execution batch."""

    __tablename__ = "payroll_runs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "run_number", name="uq_payroll_run_number"),
        Index("ix_payroll_run_tenant_status", "tenant_id", "status"),
        Index("ix_payroll_run_period", "tenant_id", "period_id"),
    )

    period_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("payroll_periods.id", ondelete="RESTRICT"),
        nullable=False,
    )
    calendar_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("payroll_calendars.id", ondelete="RESTRICT"),
        nullable=False,
    )
    run_number: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g., PR-2026-08-001
    status: Mapped[str] = mapped_column(String(32), default=PayrollRunStatus.DRAFT, nullable=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    campus_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Aggregated Financial Metrics
    total_gross_pay: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    total_deductions: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    total_employer_contributions: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0.00"), nullable=False
    )
    total_net_pay: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    employee_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Approvals & Auditing
    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    posted_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    period: Mapped["PayrollPeriod"] = relationship(back_populates="payroll_runs")
    items: Mapped[list["PayrollRunItem"]] = relationship(
        back_populates="payroll_run", cascade="all, delete-orphan"
    )


class PayrollRunItem(TenantScopedModel):
    """Calculated pay record for an individual employee within a payroll run."""

    __tablename__ = "payroll_run_items"
    __table_args__ = (
        UniqueConstraint("tenant_id", "payroll_run_id", "employee_id", name="uq_run_item_emp"),
        Index("ix_run_item_tenant_emp", "tenant_id", "employee_id"),
    )

    payroll_run_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("payroll_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workforce_employees.id", ondelete="RESTRICT"),
        nullable=False,
    )
    compensation_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("payroll_employee_compensations.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Time & Attendance Inputs Snapshot
    days_in_period: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    worked_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("30.00"), nullable=False)
    paid_leave_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    unpaid_leave_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    proration_factor: Mapped[Decimal] = mapped_column(Numeric(7, 4), default=Decimal("1.0000"), nullable=False)

    # Monetary Results
    gross_earnings: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_deductions: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    employer_contributions: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    net_pay: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    calculation_breakdown: Mapped[dict] = mapped_column(JSONB_COMPAT, default=dict, nullable=False)

    payroll_run: Mapped["PayrollRun"] = relationship(back_populates="items")
    employee: Mapped["WorkforceEmployee"] = relationship("WorkforceEmployee")
    details: Mapped[list["PayrollRunItemDetail"]] = relationship(
        back_populates="run_item", cascade="all, delete-orphan"
    )


class PayrollRunItemDetail(Base):
    """Component-level line item for an employee's calculation."""

    __tablename__ = "payroll_run_item_details"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    run_item_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("payroll_run_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    component_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("payroll_salary_components.id", ondelete="RESTRICT"),
        nullable=False,
    )
    component_name: Mapped[str] = mapped_column(String(128), nullable=False)
    component_type: Mapped[str] = mapped_column(String(32), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    calculation_notes: Mapped[str | None] = mapped_column(String(255), nullable=True)

    run_item: Mapped["PayrollRunItem"] = relationship(back_populates="details")
    component: Mapped["SalaryComponent"] = relationship("SalaryComponent")


# -----------------------------------------------------------------------------
# 6. Finance & Accounting Integration
# -----------------------------------------------------------------------------


class PayrollAccountingMapping(TenantScopedModel):
    """Chart of accounts mapping linking payroll component types to general ledger accounts."""

    __tablename__ = "payroll_accounting_mappings"
    __table_args__ = (
        UniqueConstraint("tenant_id", "category", name="uq_acct_map_tenant_cat"),
    )

    category: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g., BASIC_SALARY, ALLOWANCES, PF_PAYABLE, TDS_PAYABLE, NET_PAY_PAYABLE
    account_code: Mapped[str] = mapped_column(String(64), nullable=False)
    account_name: Mapped[str] = mapped_column(String(128), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class PayrollJournalEntry(TenantScopedModel):
    """Balanced accounting journal entry posted from a finalized payroll run."""

    __tablename__ = "payroll_journal_entries"
    __table_args__ = (
        UniqueConstraint("tenant_id", "payroll_run_id", name="uq_pje_tenant_run"),
        UniqueConstraint("tenant_id", "entry_number", name="uq_pje_tenant_num"),
    )

    payroll_run_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("payroll_runs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    entry_number: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g., JRN-PAY-2026-08-001
    entry_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_debit: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    total_credit: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    is_balanced: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    posted_by_user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    posted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    lines: Mapped[list["PayrollJournalLine"]] = relationship(
        back_populates="journal_entry", cascade="all, delete-orphan"
    )


class PayrollJournalLine(Base):
    """Itemized debit or credit line in the payroll journal entry."""

    __tablename__ = "payroll_journal_lines"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    journal_entry_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("payroll_journal_entries.id", ondelete="CASCADE"),
        nullable=False,
    )
    account_code: Mapped[str] = mapped_column(String(64), nullable=False)
    account_name: Mapped[str] = mapped_column(String(128), nullable=False)
    line_type: Mapped[str] = mapped_column(String(16), nullable=False)  # DEBIT or CREDIT
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    journal_entry: Mapped["PayrollJournalEntry"] = relationship(back_populates="lines")


# -----------------------------------------------------------------------------
# 7. Payment Disbursement Batches & Bank Reconciliation
# -----------------------------------------------------------------------------


class PayrollPaymentBatch(TenantScopedModel):
    """Payment preparation and bank disbursement file batch."""

    __tablename__ = "payroll_payment_batches"
    __table_args__ = (
        UniqueConstraint("tenant_id", "batch_number", name="uq_pay_batch_num"),
        Index("ix_pay_batch_tenant_status", "tenant_id", "status"),
    )

    payroll_run_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("payroll_runs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    batch_number: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g., BAT-PAY-2026-08-01
    payment_method: Mapped[str] = mapped_column(String(32), default=PaymentMethod.BANK_TRANSFER, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=PaymentBatchStatus.PREPARED, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    total_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    disbursed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    exported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    export_format: Mapped[str] = mapped_column(String(32), default="STANDARD_ACH_CSV", nullable=False)

    items: Mapped[list["PayrollPaymentItem"]] = relationship(
        back_populates="batch", cascade="all, delete-orphan"
    )


class PayrollPaymentItem(Base):
    """Per-employee disbursement transaction in a payment batch."""

    __tablename__ = "payroll_payment_items"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    batch_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("payroll_payment_batches.id", ondelete="CASCADE"),
        nullable=False,
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workforce_employees.id", ondelete="RESTRICT"),
        nullable=False,
    )
    run_item_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("payroll_run_items.id", ondelete="RESTRICT"),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    bank_name: Mapped[str] = mapped_column(String(128), nullable=False)
    account_number_masked: Mapped[str] = mapped_column(String(32), nullable=False)
    ifsc_code: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    transaction_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reconciled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    batch: Mapped["PayrollPaymentBatch"] = relationship(back_populates="items")


# -----------------------------------------------------------------------------
# 8. Statutory Compliance Rules
# -----------------------------------------------------------------------------


class StatutoryComplianceRule(TenantScopedModel):
    """Configurable, versioned statutory deduction parameters (PF, ESI, PT, TDS)."""

    __tablename__ = "payroll_statutory_rules"
    __table_args__ = (
        UniqueConstraint("tenant_id", "rule_code", name="uq_statutory_rule_code"),
        Index("ix_statutory_tenant_jur", "tenant_id", "jurisdiction", "is_active"),
    )

    jurisdiction: Mapped[str] = mapped_column(String(32), nullable=False)  # StatutoryJurisdiction
    rule_code: Mapped[str] = mapped_column(String(64), nullable=False)      # e.g., "IN_PF_2026", "IN_PT_KARNATAKA"
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    employee_rate: Mapped[Decimal] = mapped_column(Numeric(7, 4), default=Decimal("0.0000"), nullable=False)
    employer_rate: Mapped[Decimal] = mapped_column(Numeric(7, 4), default=Decimal("0.0000"), nullable=False)
    wage_ceiling: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    slab_configuration: Mapped[list] = mapped_column(JSONB_COMPAT, default=list, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


# -----------------------------------------------------------------------------
# 9. Payslips
# -----------------------------------------------------------------------------


class Payslip(TenantScopedModel):
    """Finalized legal salary slip reference with secure document access."""

    __tablename__ = "payroll_payslips"
    __table_args__ = (
        UniqueConstraint("tenant_id", "payslip_number", name="uq_payslip_num"),
        Index("ix_payslip_tenant_emp_period", "tenant_id", "employee_id", "period_code"),
    )

    payroll_run_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("payroll_runs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    run_item_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("payroll_run_items.id", ondelete="RESTRICT"),
        nullable=False,
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workforce_employees.id", ondelete="RESTRICT"),
        nullable=False,
    )
    payslip_number: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g. "PS-2026-08-00123"
    period_code: Mapped[str] = mapped_column(String(32), nullable=False)
    gross_pay: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_deductions: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    net_pay: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    secure_token: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    employee: Mapped["WorkforceEmployee"] = relationship("WorkforceEmployee")
    run_item: Mapped["PayrollRunItem"] = relationship("PayrollRunItem")
