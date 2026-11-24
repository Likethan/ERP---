"""Pydantic v2 Schemas for Enterprise Workforce Management, Staff Lifecycle, Leave & Workload Administration (Step 51).

CampusOS Tagline: "One Campus. One System. One Source of Truth."
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.workforce import (
    EmploymentStatus,
    EmploymentType,
    HRCaseCategory,
    HRCasePriority,
    LeaveAccrualFrequency,
    LifecycleCaseType,
    LifecycleTaskCategory,
    WorkloadCategory,
)

# =============================================================================
# 1. EMPLOYEE & EMPLOYMENT RECORDS
# =============================================================================


class WorkforceEmployeeCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    employee_number: str | None = Field(None, max_length=64)
    employment_type: str = Field(EmploymentType.PERMANENT, max_length=32)
    employment_status: str = Field(EmploymentStatus.DRAFT, max_length=32)
    designation: str = Field(..., min_length=1, max_length=128)
    job_title: str = Field(..., min_length=1, max_length=128)
    department_id: UUID | None = None
    campus_id: UUID | None = None
    reporting_manager_id: UUID | None = None
    work_location: str | None = Field(None, max_length=128)
    joining_date: date
    probation_end_date: date | None = None
    confirmation_date: date | None = None
    contract_start_date: date | None = None
    contract_end_date: date | None = None
    notice_period_days: int = Field(30, ge=0)
    qualifications: list[dict[str, Any]] = Field(default_factory=list)
    certifications: list[dict[str, Any]] = Field(default_factory=list)
    metadata_properties: dict[str, Any] = Field(default_factory=dict)


class WorkforceEmployeeUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employment_type: str | None = None
    designation: str | None = Field(None, max_length=128)
    job_title: str | None = Field(None, max_length=128)
    department_id: UUID | None = None
    campus_id: UUID | None = None
    reporting_manager_id: UUID | None = None
    work_location: str | None = Field(None, max_length=128)
    probation_end_date: date | None = None
    confirmation_date: date | None = None
    contract_start_date: date | None = None
    contract_end_date: date | None = None
    notice_period_days: int | None = Field(None, ge=0)
    qualifications: list[dict[str, Any]] | None = None
    certifications: list[dict[str, Any]] | None = None
    metadata_properties: dict[str, Any] | None = None
    is_active: bool | None = None


class WorkforceEmployeeTransitionRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    new_status: str = Field(..., max_length=32)
    effective_date: date = Field(default_factory=date.today)
    reason: str = Field(..., min_length=3)
    reference_document_id: str | None = Field(None, max_length=128)


class WorkforceEmployeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    user_id: UUID
    employee_number: str
    employment_type: str
    employment_status: str
    designation: str
    job_title: str
    department_id: UUID | None
    department_name: str | None = None
    campus_id: UUID | None
    campus_name: str | None = None
    reporting_manager_id: UUID | None
    reporting_manager_name: str | None = None
    reporting_manager_employee_number: str | None = None
    work_location: str | None
    joining_date: date
    probation_end_date: date | None
    confirmation_date: date | None
    contract_start_date: date | None
    contract_end_date: date | None
    separation_date: date | None
    separation_reason: str | None
    notice_period_days: int
    qualifications: list[dict[str, Any]]
    certifications: list[dict[str, Any]]
    metadata_properties: dict[str, Any]
    is_active: bool
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone_number: str | None = None
    created_at: datetime
    updated_at: datetime


class WorkforceEmploymentHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    employee_id: UUID
    change_type: str
    effective_date: date
    previous_values: dict[str, Any]
    new_values: dict[str, Any]
    reason: str
    authorized_by_user_id: UUID
    authorized_by_name: str | None = None
    reference_document_id: str | None
    created_at: datetime


# =============================================================================
# 2. STAFF LIFECYCLE: ONBOARDING & OFFBOARDING
# =============================================================================


class WorkforceLifecycleTaskCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    task_name: str = Field(..., min_length=2, max_length=128)
    task_category: str = Field(LifecycleTaskCategory.HR, max_length=32)
    assigned_role: str | None = Field(None, max_length=64)
    assigned_user_id: UUID | None = None
    is_mandatory: bool = True
    due_date: date | None = None


class WorkforceLifecycleTaskUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str = Field(..., max_length=32)
    completion_evidence: str | None = None
    blocker_reason: str | None = None


class WorkforceLifecycleTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    case_id: UUID
    task_name: str
    task_category: str
    assigned_role: str | None
    assigned_user_id: UUID | None
    assigned_user_name: str | None = None
    is_mandatory: bool
    status: str
    due_date: date | None
    completed_at: datetime | None
    completed_by_user_id: UUID | None
    completed_by_name: str | None = None
    completion_evidence: str | None
    blocker_reason: str | None
    created_at: datetime


class WorkforceLifecycleCaseCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employee_id: UUID
    case_type: str = Field(LifecycleCaseType.ONBOARDING, max_length=32)
    target_date: date
    notes: str | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    custom_tasks: list[WorkforceLifecycleTaskCreate] | None = None


class WorkforceLifecycleCaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    employee_id: UUID
    employee_name: str | None = None
    employee_number: str | None = None
    case_number: str
    case_type: str
    status: str
    target_date: date
    completion_date: date | None
    initiator_user_id: UUID
    initiator_name: str | None = None
    notes: str | None
    metadata_json: dict[str, Any]
    tasks: list[WorkforceLifecycleTaskResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class WorkforceSeparationInitiateRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employee_id: UUID
    separation_date: date
    separation_reason: str = Field(..., min_length=2, max_length=128)
    notice_period_days: int = Field(30, ge=0)
    notes: str | None = None


# =============================================================================
# 3. LEAVE TYPES & POLICIES
# =============================================================================


class WorkforceLeaveTypeCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str = Field(..., min_length=2, max_length=32)
    name: str = Field(..., min_length=2, max_length=128)
    description: str | None = None
    is_paid: bool = True
    is_active: bool = True


class WorkforceLeaveTypeUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str | None = Field(None, max_length=128)
    description: str | None = None
    is_paid: bool | None = None
    is_active: bool | None = None


class WorkforceLeaveTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    code: str
    name: str
    description: str | None
    is_paid: bool
    is_active: bool
    created_at: datetime


class WorkforceLeavePolicyCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    leave_type_id: UUID
    policy_code: str = Field(..., min_length=2, max_length=64)
    name: str = Field(..., min_length=2, max_length=128)
    effective_from: date
    effective_to: date | None = None
    applicable_employment_types: list[str] = Field(default_factory=list)
    applicable_departments: list[str] = Field(default_factory=list)
    annual_entitlement: Decimal = Field(default=Decimal("12.00"), ge=0)
    accrual_frequency: str = Field(LeaveAccrualFrequency.ANNUAL, max_length=32)
    accrual_rate: Decimal = Field(default=Decimal("1.00"), ge=0)
    carry_forward_max: Decimal = Field(default=Decimal("0.00"), ge=0)
    expiry_months: int | None = Field(None, ge=1)
    max_consecutive_days: int | None = Field(None, ge=1)
    requires_document: bool = False
    document_mandatory_after_days: int = Field(3, ge=1)
    allow_half_day: bool = True
    is_active: bool = True


class WorkforceLeavePolicyUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str | None = Field(None, max_length=128)
    effective_to: date | None = None
    applicable_employment_types: list[str] | None = None
    applicable_departments: list[str] | None = None
    annual_entitlement: Decimal | None = None
    accrual_frequency: str | None = None
    accrual_rate: Decimal | None = None
    carry_forward_max: Decimal | None = None
    expiry_months: int | None = None
    max_consecutive_days: int | None = None
    requires_document: bool | None = None
    document_mandatory_after_days: int | None = None
    allow_half_day: bool | None = None
    is_active: bool | None = None


class WorkforceLeavePolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    leave_type_id: UUID
    leave_type_name: str | None = None
    policy_code: str
    name: str
    version: int
    effective_from: date
    effective_to: date | None
    applicable_employment_types: list[str]
    applicable_departments: list[str]
    annual_entitlement: Decimal
    accrual_frequency: str
    accrual_rate: Decimal
    carry_forward_max: Decimal
    expiry_months: int | None
    max_consecutive_days: int | None
    requires_document: bool
    document_mandatory_after_days: int
    allow_half_day: bool
    is_active: bool
    created_at: datetime


# =============================================================================
# 4. LEAVE BALANCES & TRANSACTIONS
# =============================================================================


class WorkforceLeaveBalanceAdjustRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employee_id: UUID
    leave_type_id: UUID
    calendar_year: int
    adjustment_days: Decimal
    reason: str = Field(..., min_length=3)


class WorkforceLeaveBalanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    employee_id: UUID
    employee_name: str | None = None
    employee_number: str | None = None
    leave_type_id: UUID
    leave_type_code: str | None = None
    leave_type_name: str | None = None
    calendar_year: int
    entitled_days: Decimal
    accrued_days: Decimal
    carried_forward_days: Decimal
    used_days: Decimal
    pending_days: Decimal
    adjusted_days: Decimal
    expired_days: Decimal
    available_days: Decimal


class WorkforceLeaveBalanceTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    balance_id: UUID
    transaction_type: str
    amount: Decimal
    running_balance: Decimal
    reference_type: str | None
    reference_id: str | None
    reason: str
    created_by_user_id: UUID
    created_by_name: str | None = None
    created_at: datetime


class WorkforceLeaveAccrualRunRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    calendar_year: int
    leave_type_id: UUID | None = None
    department_id: UUID | None = None


# =============================================================================
# 5. LEAVE REQUESTS & APPROVAL INBOX
# =============================================================================


class WorkforceLeaveRequestCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employee_id: UUID | None = None  # HR or admin can specify employee; else self
    leave_type_id: UUID
    start_date: date
    end_date: date
    is_half_day: bool = False
    half_day_session: str | None = Field(None, max_length=32)
    reason: str = Field(..., min_length=3)
    supporting_document_url: str | None = Field(None, max_length=255)


class WorkforceLeaveDecisionRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    decision_reason: str | None = None


class WorkforceLeaveApprovalStepResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    request_id: UUID
    step_number: int
    approver_user_id: UUID | None
    approver_name: str | None = None
    approver_role: str | None
    status: str
    comments: str | None
    decided_at: datetime | None


class WorkforceLeaveRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    employee_id: UUID
    employee_name: str | None = None
    employee_number: str | None = None
    department_name: str | None = None
    leave_type_id: UUID
    leave_type_code: str | None = None
    leave_type_name: str | None = None
    request_number: str
    start_date: date
    end_date: date
    is_half_day: bool
    half_day_session: str | None
    total_days: Decimal
    reason: str
    supporting_document_url: str | None
    status: str
    decision_reason: str | None
    submitted_at: datetime
    decided_at: datetime | None
    decided_by_user_id: UUID | None
    decided_by_name: str | None = None
    has_timetable_conflicts: bool = False
    approval_steps: list[WorkforceLeaveApprovalStepResponse] = Field(default_factory=list)
    created_at: datetime


class WorkforceLeaveCalendarEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: date
    employee_id: UUID
    employee_name: str
    department_name: str | None
    leave_type_code: str
    leave_type_name: str
    is_half_day: bool
    half_day_session: str | None
    status: str


# =============================================================================
# 6. WORKFORCE AVAILABILITY & TIMETABLE CONFLICTS
# =============================================================================


class WorkforceAvailabilityCheckRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employee_id: UUID
    start_date: date
    end_date: date


class WorkforceAvailabilityCheckResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employee_id: UUID
    employee_name: str
    status: str
    is_available: bool
    approved_leave_days: list[date] = Field(default_factory=list)
    pending_leave_days: list[date] = Field(default_factory=list)
    timetable_session_conflicts: list[dict[str, Any]] = Field(default_factory=list)


class WorkforceConflictOverrideRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    override_reason: str = Field(..., min_length=3)
    substitute_employee_id: UUID | None = None


class WorkforceAvailabilityConflictResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    employee_id: UUID
    employee_name: str | None = None
    leave_request_id: UUID
    conflict_date: date
    timetable_session_id: UUID | None
    timetable_session_info: dict[str, Any] | None = None
    conflict_type: str
    severity: str
    is_overridden: bool
    override_reason: str | None
    substitute_employee_id: UUID | None
    substitute_employee_name: str | None = None
    created_at: datetime


# =============================================================================
# 7. WORKLOAD & WORKFORCE PLANNING
# =============================================================================


class WorkforceWorkloadExpectationCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employee_id: UUID
    academic_year_id: UUID
    semester_id: UUID | None = None
    teaching_hours_per_week: Decimal = Field(default=Decimal("16.00"), ge=0)
    research_hours_per_week: Decimal = Field(default=Decimal("8.00"), ge=0)
    admin_hours_per_week: Decimal = Field(default=Decimal("6.00"), ge=0)
    exam_hours_per_week: Decimal = Field(default=Decimal("4.00"), ge=0)
    effective_from: date
    effective_to: date | None = None
    notes: str | None = None


class WorkforceWorkloadExpectationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    employee_id: UUID
    employee_name: str | None = None
    academic_year_id: UUID
    semester_id: UUID | None
    teaching_hours_per_week: Decimal
    research_hours_per_week: Decimal
    admin_hours_per_week: Decimal
    exam_hours_per_week: Decimal
    total_expected_hours_per_week: Decimal
    effective_from: date
    effective_to: date | None
    notes: str | None
    created_at: datetime


class WorkforceWorkloadAdjustmentCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employee_id: UUID
    category: str = Field(WorkloadCategory.TEACHING, max_length=32)
    adjusted_hours_per_week: Decimal
    reason: str = Field(..., min_length=3)
    effective_from: date
    effective_to: date | None = None


class WorkforceWorkloadAdjustmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    employee_id: UUID
    employee_name: str | None = None
    category: str
    adjusted_hours_per_week: Decimal
    reason: str
    effective_from: date
    effective_to: date | None
    authorized_by_user_id: UUID
    authorized_by_name: str | None = None
    created_at: datetime


class WorkforceWorkloadSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employee_id: UUID
    employee_name: str
    employee_number: str
    department_name: str | None
    academic_year_id: UUID | None
    semester_id: UUID | None
    expected_hours: Decimal
    scheduled_teaching_hours: Decimal
    adjusted_hours: Decimal
    total_actual_hours: Decimal
    variance_hours: Decimal
    load_status: str  # BALANCED, UNDER_ALLOCATED, OVERLOAD
    sessions_count: int


# =============================================================================
# 8. EMPLOYEE SELF-SERVICE & HR CASES
# =============================================================================


class WorkforceHRCaseCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employee_id: UUID | None = None  # Can be inferred from current user
    category: str = Field(HRCaseCategory.GENERAL_INQUIRY, max_length=32)
    priority: str = Field(HRCasePriority.NORMAL, max_length=32)
    subject: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=5)
    proposed_changes: dict[str, Any] = Field(default_factory=dict)
    is_confidential: bool = False


class WorkforceHRCaseUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str | None = Field(None, max_length=32)
    priority: str | None = Field(None, max_length=32)
    assigned_to_user_id: UUID | None = None
    resolution: str | None = None


class WorkforceHRCaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    employee_id: UUID
    employee_name: str | None = None
    employee_number: str | None = None
    case_number: str
    category: str
    priority: str
    status: str
    subject: str
    description: str
    proposed_changes: dict[str, Any]
    is_confidential: bool
    assigned_to_user_id: UUID | None
    assigned_to_name: str | None = None
    resolution: str | None
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 9. REPORTING & ANALYTICS
# =============================================================================


class WorkforceHeadcountReport(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_headcount: int
    active_count: int
    onboarding_count: int
    on_leave_count: int
    notice_period_count: int
    separated_count: int
    by_department: list[dict[str, Any]]
    by_employment_type: list[dict[str, Any]]
    by_status: list[dict[str, Any]]


class WorkforceLeaveUtilizationReport(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_leave_days_taken: Decimal
    pending_approval_count: int
    by_leave_type: list[dict[str, Any]]
    by_department: list[dict[str, Any]]


class WorkforceCapacityReport(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_workforce_evaluated: int
    overloaded_staff_count: int
    balanced_staff_count: int
    underutilized_staff_count: int
    department_metrics: list[dict[str, Any]]
