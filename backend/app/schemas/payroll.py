"""Pydantic v2 Schemas for Enterprise Payroll, Compensation, Benefits & Statutory Compliance (Step 52).

CampusOS Tagline: "One Campus. One System. One Source of Truth."
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.payroll import (
    CalculationMethod,
    ComponentType,
    PayFrequency,
    PaymentMethod,
    StatutoryJurisdiction,
    TaxabilityType,
)

# =============================================================================
# 1. SALARY GRADES & SCALES
# =============================================================================


class SalaryGradeCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=128)
    description: str | None = None
    min_base_pay: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    max_base_pay: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    is_active: bool = True


class SalaryGradeUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=128)
    description: str | None = None
    min_base_pay: Decimal | None = Field(None, ge=Decimal("0.00"))
    max_base_pay: Decimal | None = Field(None, ge=Decimal("0.00"))
    is_active: bool | None = None


class SalaryGradeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    code: str
    name: str
    description: str | None = None
    min_base_pay: Decimal
    max_base_pay: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 2. SALARY COMPONENTS
# =============================================================================


class SalaryComponentCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=128)
    description: str | None = None
    component_type: str = Field(default=ComponentType.EARNING, max_length=32)
    calculation_method: str = Field(default=CalculationMethod.FLAT_AMOUNT, max_length=32)
    default_value: Decimal = Field(default=Decimal("0.0000"), ge=Decimal("0.0000"))
    is_statutory: bool = False
    taxability: str = Field(default=TaxabilityType.TAXABLE, max_length=32)
    is_recurring: bool = True
    is_active: bool = True


class SalaryComponentUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=128)
    description: str | None = None
    component_type: str | None = Field(None, max_length=32)
    calculation_method: str | None = Field(None, max_length=32)
    default_value: Decimal | None = Field(None, ge=Decimal("0.0000"))
    is_statutory: bool | None = None
    taxability: str | None = None
    is_recurring: bool | None = None
    is_active: bool | None = None


class SalaryComponentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    code: str
    name: str
    description: str | None = None
    component_type: str
    calculation_method: str
    default_value: Decimal
    is_statutory: bool
    taxability: str
    is_recurring: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 3. SALARY STRUCTURES & ITEMS
# =============================================================================


class SalaryStructureItemCreate(BaseModel):
    component_id: UUID
    calculation_method: str = Field(default=CalculationMethod.FLAT_AMOUNT, max_length=32)
    factor_value: Decimal = Field(default=Decimal("0.0000"), ge=Decimal("0.0000"))
    fixed_amount: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    sequence: int = Field(default=1, ge=1)


class SalaryStructureItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    structure_id: UUID
    component_id: UUID
    component_name: str | None = None
    component_type: str | None = None
    calculation_method: str
    factor_value: Decimal
    fixed_amount: Decimal
    sequence: int


class SalaryStructureCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=128)
    description: str | None = None
    currency: str = Field(default="INR", min_length=3, max_length=8)
    pay_frequency: str = Field(default=PayFrequency.MONTHLY, max_length=32)
    is_active: bool = True
    items: list[SalaryStructureItemCreate] = Field(default_factory=list)


class SalaryStructureUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=128)
    description: str | None = None
    currency: str | None = None
    pay_frequency: str | None = None
    is_active: bool | None = None
    items: list[SalaryStructureItemCreate] | None = None


class SalaryStructureResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    code: str
    name: str
    description: str | None = None
    currency: str
    pay_frequency: str
    version: int
    is_active: bool
    items: list[SalaryStructureItemResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 4. EMPLOYEE COMPENSATION & BANK DETAILS
# =============================================================================


class EmployeeCompensationCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employee_id: UUID
    structure_id: UUID
    salary_grade_id: UUID | None = None
    annual_ctc: Decimal = Field(..., ge=Decimal("0.00"))
    monthly_gross: Decimal = Field(..., ge=Decimal("0.00"))
    base_pay: Decimal = Field(..., ge=Decimal("0.00"))
    effective_from: date
    effective_to: date | None = None
    currency: str = Field(default="INR", min_length=3, max_length=8)
    custom_components: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = None


class EmployeeCompensationUpdate(BaseModel):
    structure_id: UUID | None = None
    salary_grade_id: UUID | None = None
    annual_ctc: Decimal | None = Field(None, ge=Decimal("0.00"))
    monthly_gross: Decimal | None = Field(None, ge=Decimal("0.00"))
    base_pay: Decimal | None = Field(None, ge=Decimal("0.00"))
    effective_from: date | None = None
    effective_to: date | None = None
    custom_components: dict[str, Any] | None = None
    notes: str | None = None
    change_reason: str | None = None


class EmployeeCompensationHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    employee_id: UUID
    compensation_id: UUID
    effective_date: date
    previous_annual_ctc: Decimal
    new_annual_ctc: Decimal
    previous_monthly_gross: Decimal
    new_monthly_gross: Decimal
    change_reason: str
    authorized_by_user_id: UUID
    created_at: datetime


class EmployeeCompensationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    employee_id: UUID
    structure_id: UUID
    salary_grade_id: UUID | None = None
    annual_ctc: Decimal
    monthly_gross: Decimal
    base_pay: Decimal
    effective_from: date
    effective_to: date | None = None
    currency: str
    custom_components: dict[str, Any]
    notes: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class EmployeeBankDetailCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employee_id: UUID
    account_holder_name: str = Field(..., min_length=1, max_length=128)
    bank_name: str = Field(..., min_length=1, max_length=128)
    account_number: str = Field(..., min_length=4, max_length=34)
    ifsc_code: str = Field(..., min_length=4, max_length=32)
    branch_name: str = Field(..., min_length=1, max_length=128)
    is_primary: bool = True


class EmployeeBankDetailVerify(BaseModel):
    is_verified: bool = True


class EmployeeBankDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    employee_id: UUID
    account_holder_name: str
    bank_name: str
    account_number_masked: str
    ifsc_code: str
    branch_name: str
    is_primary: bool
    is_verified: bool
    verified_by_user_id: UUID | None = None
    verified_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 5. STATUTORY COMPLIANCE RULES
# =============================================================================


class StatutoryComplianceRuleCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    jurisdiction: str = Field(default=StatutoryJurisdiction.IN_PF, max_length=32)
    rule_code: str = Field(..., min_length=1, max_length=64)
    title: str = Field(..., min_length=1, max_length=128)
    description: str | None = None
    employee_rate: Decimal = Field(default=Decimal("0.0000"), ge=Decimal("0.0000"))
    employer_rate: Decimal = Field(default=Decimal("0.0000"), ge=Decimal("0.0000"))
    wage_ceiling: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    effective_from: date
    effective_to: date | None = None
    slab_configuration: list[dict[str, Any]] = Field(default_factory=list)
    is_active: bool = True


class StatutoryComplianceRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    jurisdiction: str
    rule_code: str
    title: str
    description: str | None = None
    employee_rate: Decimal
    employer_rate: Decimal
    wage_ceiling: Decimal
    effective_from: date
    effective_to: date | None = None
    slab_configuration: list[dict[str, Any]]
    is_active: bool
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 6. PAYROLL CALENDARS & PERIODS
# =============================================================================


class PayrollCalendarCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=1, max_length=128)
    pay_frequency: str = Field(default=PayFrequency.MONTHLY, max_length=32)
    cutoff_day_of_month: int = Field(default=25, ge=1, le=31)
    pay_day_of_month: int = Field(default=30, ge=1, le=31)
    is_active: bool = True


class PayrollCalendarResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    pay_frequency: str
    cutoff_day_of_month: int
    pay_day_of_month: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PayrollPeriodCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    calendar_id: UUID
    period_code: str = Field(..., min_length=1, max_length=32)
    start_date: date
    end_date: date
    cutoff_date: date


class PayrollPeriodResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    calendar_id: UUID
    period_code: str
    start_date: date
    end_date: date
    cutoff_date: date
    is_closed: bool
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 7. PAYROLL RUNS & PROCESSING
# =============================================================================


class PayrollRunCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    period_id: UUID
    calendar_id: UUID
    run_number: str | None = None
    department_id: UUID | None = None
    campus_id: UUID | None = None


class PayrollRunCalculateRequest(BaseModel):
    force_recalculate: bool = False
    notes: str | None = None


class PayrollRunCancelRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=255)


class PayrollRunItemDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    component_id: UUID
    component_name: str
    component_type: str
    amount: Decimal
    calculation_notes: str | None = None


class PayrollRunItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    payroll_run_id: UUID
    employee_id: UUID
    compensation_id: UUID
    days_in_period: int
    worked_days: Decimal
    paid_leave_days: Decimal
    unpaid_leave_days: Decimal
    proration_factor: Decimal
    gross_earnings: Decimal
    total_deductions: Decimal
    employer_contributions: Decimal
    net_pay: Decimal
    calculation_breakdown: dict[str, Any]
    details: list[PayrollRunItemDetailResponse] = Field(default_factory=list)
    created_at: datetime


class PayrollRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    period_id: UUID
    calendar_id: UUID
    run_number: str
    status: str
    is_locked: bool
    department_id: UUID | None = None
    campus_id: UUID | None = None
    total_gross_pay: Decimal
    total_deductions: Decimal
    total_employer_contributions: Decimal
    total_net_pay: Decimal
    employee_count: int
    approved_by_user_id: UUID | None = None
    approved_at: datetime | None = None
    posted_by_user_id: UUID | None = None
    posted_at: datetime | None = None
    rejection_reason: str | None = None
    items: list[PayrollRunItemResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 8. ACCOUNTING & FINANCIAL INTEGRATION
# =============================================================================


class PayrollAccountingMappingCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category: str = Field(..., max_length=64)
    account_code: str = Field(..., min_length=1, max_length=64)
    account_name: str = Field(..., min_length=1, max_length=128)
    is_active: bool = True


class PayrollAccountingMappingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    category: str
    account_code: str
    account_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PayrollJournalLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_code: str
    account_name: str
    line_type: str
    amount: Decimal
    department_id: UUID | None = None
    description: str | None = None


class PayrollJournalEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    payroll_run_id: UUID
    entry_number: str
    entry_date: date
    total_debit: Decimal
    total_credit: Decimal
    is_balanced: bool
    posted_by_user_id: UUID
    posted_at: datetime
    lines: list[PayrollJournalLineResponse] = Field(default_factory=list)
    created_at: datetime


# =============================================================================
# 9. PAYMENT BATCHES & RECONCILIATION
# =============================================================================


class PayrollPaymentBatchCreate(BaseModel):
    payroll_run_id: UUID
    payment_method: str = Field(default=PaymentMethod.BANK_TRANSFER, max_length=32)
    export_format: str = "STANDARD_ACH_CSV"


class PayrollPaymentItemReconcileRequest(BaseModel):
    payment_item_id: UUID
    status: str = Field(default="RECONCILED", max_length=32)
    transaction_reference: str | None = None


class PayrollPaymentBatchReconcileRequest(BaseModel):
    reconciled_items: list[PayrollPaymentItemReconcileRequest] = Field(default_factory=list)


class PayrollPaymentItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    batch_id: UUID
    employee_id: UUID
    run_item_id: UUID
    amount: Decimal
    bank_name: str
    account_number_masked: str
    ifsc_code: str
    status: str
    transaction_reference: str | None = None
    reconciled_at: datetime | None = None


class PayrollPaymentBatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    payroll_run_id: UUID
    batch_number: str
    payment_method: str
    status: str
    total_amount: Decimal
    total_records: int
    disbursed_at: datetime | None = None
    exported_at: datetime | None = None
    export_format: str
    items: list[PayrollPaymentItemResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 10. PAYSLIPS & EMPLOYEE SELF-SERVICE
# =============================================================================


class PayslipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    payroll_run_id: UUID
    run_item_id: UUID
    employee_id: UUID
    payslip_number: str
    period_code: str
    gross_pay: Decimal
    total_deductions: Decimal
    net_pay: Decimal
    secure_token: str
    storage_key: str | None = None
    is_published: bool
    created_at: datetime


class PayslipDiscrepancyRequest(BaseModel):
    subject: str = Field(..., min_length=3, max_length=128)
    description: str = Field(..., min_length=5, max_length=1000)
