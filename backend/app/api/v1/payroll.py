"""CampusOS Enterprise Payroll, Compensation, Benefits & Statutory Compliance REST API Router (Step 52).

CampusOS Tagline: "One Campus. One System. One Source of Truth."
"""

import secrets
import uuid
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_current_user, get_tenant_context, require_permission
from app.core.exceptions import NotFoundException
from app.core.permissions import (
    PAYROLL_CALENDAR_MANAGE,
    PAYROLL_COMPENSATION_MANAGE,
    PAYROLL_COMPENSATION_READ,
    PAYROLL_COMPLIANCE_MANAGE,
    PAYROLL_PAYMENT_MANAGE,
    PAYROLL_PAYSLIP_READ_AUTH,
    PAYROLL_PAYSLIP_READ_OWN,
    PAYROLL_RECONCILIATION_MANAGE,
    PAYROLL_RUN_APPROVE,
    PAYROLL_RUN_CALCULATE,
    PAYROLL_RUN_CREATE,
    PAYROLL_RUN_POST,
    PAYROLL_RUN_REVIEW,
)
from app.core.tenant import TenantContext
from app.models.people import User
from app.models.workforce import (
    HRCaseCategory,
    HRCasePriority,
    HRCaseStatus,
    WorkforceEmployee,
    WorkforceHRCase,
)
from app.schemas.payroll import (
    EmployeeBankDetailCreate,
    EmployeeBankDetailResponse,
    EmployeeBankDetailVerify,
    EmployeeCompensationCreate,
    EmployeeCompensationResponse,
    PayrollCalendarCreate,
    PayrollCalendarResponse,
    PayrollJournalEntryResponse,
    PayrollPaymentBatchCreate,
    PayrollPaymentBatchReconcileRequest,
    PayrollPaymentBatchResponse,
    PayrollPeriodCreate,
    PayrollPeriodResponse,
    PayrollRunCalculateRequest,
    PayrollRunCancelRequest,
    PayrollRunCreate,
    PayrollRunResponse,
    PayslipDiscrepancyRequest,
    PayslipResponse,
    SalaryComponentCreate,
    SalaryComponentResponse,
    SalaryComponentUpdate,
    SalaryGradeCreate,
    SalaryGradeResponse,
    SalaryGradeUpdate,
    SalaryStructureCreate,
    SalaryStructureResponse,
    StatutoryComplianceRuleCreate,
    StatutoryComplianceRuleResponse,
)
from app.services.payroll_service import PayrollService

router = APIRouter(prefix="/payroll", tags=["Payroll & Compensation"])


# =============================================================================
# 1. SALARY GRADES & PAY SCALES
# =============================================================================


@router.post(
    "/salary-grades",
    response_model=SalaryGradeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a compensation pay grade",
    dependencies=[Depends(require_permission(PAYROLL_COMPENSATION_MANAGE))],
)
async def create_salary_grade(
    payload: SalaryGradeCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SalaryGradeResponse:
    service = PayrollService(db)
    return await service.create_salary_grade(ctx.tenant_id, payload, current_user.id)


@router.get(
    "/salary-grades",
    response_model=list[SalaryGradeResponse],
    summary="List compensation pay grades",
    dependencies=[Depends(require_permission(PAYROLL_COMPENSATION_READ))],
)
async def list_salary_grades(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    is_active: bool | None = Query(None),
) -> list[SalaryGradeResponse]:
    service = PayrollService(db)
    return await service.list_salary_grades(ctx.tenant_id, is_active=is_active)


@router.get(
    "/salary-grades/{grade_id}",
    response_model=SalaryGradeResponse,
    summary="Get compensation pay grade by ID",
    dependencies=[Depends(require_permission(PAYROLL_COMPENSATION_READ))],
)
async def get_salary_grade(
    grade_id: UUID,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SalaryGradeResponse:
    service = PayrollService(db)
    return await service.get_salary_grade(ctx.tenant_id, grade_id)


@router.put(
    "/salary-grades/{grade_id}",
    response_model=SalaryGradeResponse,
    summary="Update compensation pay grade",
    dependencies=[Depends(require_permission(PAYROLL_COMPENSATION_MANAGE))],
)
async def update_salary_grade(
    grade_id: UUID,
    payload: SalaryGradeUpdate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SalaryGradeResponse:
    service = PayrollService(db)
    return await service.update_salary_grade(ctx.tenant_id, grade_id, payload, current_user.id)


# =============================================================================
# 2. SALARY COMPONENTS
# =============================================================================


@router.post(
    "/salary-components",
    response_model=SalaryComponentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a salary earning or deduction component",
    dependencies=[Depends(require_permission(PAYROLL_COMPENSATION_MANAGE))],
)
async def create_salary_component(
    payload: SalaryComponentCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SalaryComponentResponse:
    service = PayrollService(db)
    return await service.create_salary_component(ctx.tenant_id, payload, current_user.id)


@router.get(
    "/salary-components",
    response_model=list[SalaryComponentResponse],
    summary="List salary components",
    dependencies=[Depends(require_permission(PAYROLL_COMPENSATION_READ))],
)
async def list_salary_components(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    component_type: str | None = Query(None),
    is_active: bool | None = Query(None),
) -> list[SalaryComponentResponse]:
    service = PayrollService(db)
    return await service.list_salary_components(ctx.tenant_id, component_type=component_type, is_active=is_active)


@router.put(
    "/salary-components/{component_id}",
    response_model=SalaryComponentResponse,
    summary="Update salary component",
    dependencies=[Depends(require_permission(PAYROLL_COMPENSATION_MANAGE))],
)
async def update_salary_component(
    component_id: UUID,
    payload: SalaryComponentUpdate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SalaryComponentResponse:
    service = PayrollService(db)
    return await service.update_salary_component(ctx.tenant_id, component_id, payload)


# =============================================================================
# 3. SALARY STRUCTURES
# =============================================================================


@router.post(
    "/salary-structures",
    response_model=SalaryStructureResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a grouped salary structure package",
    dependencies=[Depends(require_permission(PAYROLL_COMPENSATION_MANAGE))],
)
async def create_salary_structure(
    payload: SalaryStructureCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SalaryStructureResponse:
    service = PayrollService(db)
    return await service.create_salary_structure(ctx.tenant_id, payload, current_user.id)


@router.get(
    "/salary-structures",
    response_model=list[SalaryStructureResponse],
    summary="List salary structures",
    dependencies=[Depends(require_permission(PAYROLL_COMPENSATION_READ))],
)
async def list_salary_structures(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    is_active: bool | None = Query(None),
) -> list[SalaryStructureResponse]:
    service = PayrollService(db)
    return await service.list_salary_structures(ctx.tenant_id, is_active=is_active)


@router.get(
    "/salary-structures/{structure_id}",
    response_model=SalaryStructureResponse,
    summary="Get salary structure by ID",
    dependencies=[Depends(require_permission(PAYROLL_COMPENSATION_READ))],
)
async def get_salary_structure(
    structure_id: UUID,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SalaryStructureResponse:
    service = PayrollService(db)
    return await service.get_salary_structure(ctx.tenant_id, structure_id)


# =============================================================================
# 4. EMPLOYEE COMPENSATION & BANK DETAILS
# =============================================================================


@router.post(
    "/employee-compensations",
    response_model=EmployeeCompensationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Assign compensation package to an employee",
    dependencies=[Depends(require_permission(PAYROLL_COMPENSATION_MANAGE))],
)
async def assign_employee_compensation(
    payload: EmployeeCompensationCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> EmployeeCompensationResponse:
    service = PayrollService(db)
    return await service.assign_employee_compensation(ctx.tenant_id, payload, current_user.id)


@router.get(
    "/employee-compensations",
    response_model=list[EmployeeCompensationResponse],
    summary="List employee compensation records",
    dependencies=[Depends(require_permission(PAYROLL_COMPENSATION_READ))],
)
async def list_employee_compensations(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    employee_id: UUID | None = Query(None),
) -> list[EmployeeCompensationResponse]:
    service = PayrollService(db)
    return await service.list_employee_compensations(ctx.tenant_id, employee_id=employee_id)


@router.get(
    "/employees/{employee_id}/compensation",
    response_model=EmployeeCompensationResponse,
    summary="Get active compensation for an employee",
    dependencies=[Depends(require_permission(PAYROLL_COMPENSATION_READ))],
)
async def get_current_employee_compensation(
    employee_id: UUID,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> EmployeeCompensationResponse:
    service = PayrollService(db)
    comp = await service.get_current_employee_compensation(ctx.tenant_id, employee_id)
    if not comp:
        raise NotFoundException(f"No active compensation found for employee '{employee_id}'.")
    return comp


@router.post(
    "/employees/{employee_id}/bank-details",
    response_model=EmployeeBankDetailResponse,
    summary="Configure masked disbursement bank details for an employee",
    dependencies=[Depends(require_permission(PAYROLL_COMPENSATION_MANAGE))],
)
async def set_employee_bank_details(
    employee_id: UUID,
    payload: EmployeeBankDetailCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> EmployeeBankDetailResponse:
    payload.employee_id = employee_id
    service = PayrollService(db)
    return await service.set_employee_bank_details(ctx.tenant_id, payload, current_user.id)


@router.get(
    "/employees/{employee_id}/bank-details",
    response_model=EmployeeBankDetailResponse,
    summary="Get masked disbursement bank details for an employee",
    dependencies=[Depends(require_permission(PAYROLL_COMPENSATION_READ))],
)
async def get_employee_bank_details(
    employee_id: UUID,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> EmployeeBankDetailResponse:
    service = PayrollService(db)
    bank = await service.get_employee_bank_details(ctx.tenant_id, employee_id)
    if not bank:
        raise NotFoundException(f"No bank details registered for employee '{employee_id}'.")
    return bank


@router.post(
    "/employees/{employee_id}/bank-details/verify",
    response_model=EmployeeBankDetailResponse,
    summary="Verify employee bank details through authorized workflow",
    dependencies=[Depends(require_permission(PAYROLL_COMPENSATION_MANAGE))],
)
async def verify_employee_bank_details(
    employee_id: UUID,
    payload: EmployeeBankDetailVerify,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> EmployeeBankDetailResponse:
    service = PayrollService(db)
    return await service.verify_employee_bank_details(ctx.tenant_id, employee_id, payload, current_user.id)


# =============================================================================
# 5. STATUTORY COMPLIANCE RULES
# =============================================================================


@router.post(
    "/statutory-rules",
    response_model=StatutoryComplianceRuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Define or update a statutory compliance rule (PF, ESI, Tax)",
    dependencies=[Depends(require_permission(PAYROLL_COMPLIANCE_MANAGE))],
)
async def create_statutory_rule(
    payload: StatutoryComplianceRuleCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> StatutoryComplianceRuleResponse:
    service = PayrollService(db)
    return await service.create_statutory_rule(ctx.tenant_id, payload, current_user.id)


@router.get(
    "/statutory-rules",
    response_model=list[StatutoryComplianceRuleResponse],
    summary="List configured statutory compliance rules",
    dependencies=[Depends(require_permission(PAYROLL_COMPENSATION_READ))],
)
async def list_statutory_rules(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    is_active: bool | None = Query(None),
    jurisdiction: str | None = Query(None),
) -> list[StatutoryComplianceRuleResponse]:
    service = PayrollService(db)
    return await service.list_statutory_rules(ctx.tenant_id, is_active=is_active, jurisdiction=jurisdiction)


# =============================================================================
# 6. PAYROLL CALENDARS & PERIODS
# =============================================================================


@router.post(
    "/calendars",
    response_model=PayrollCalendarResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a payroll calendar and frequency schedule",
    dependencies=[Depends(require_permission(PAYROLL_CALENDAR_MANAGE))],
)
async def create_payroll_calendar(
    payload: PayrollCalendarCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> PayrollCalendarResponse:
    service = PayrollService(db)
    return await service.create_payroll_calendar(ctx.tenant_id, payload, current_user.id)


@router.get(
    "/calendars",
    response_model=list[PayrollCalendarResponse],
    summary="List payroll calendars",
    dependencies=[Depends(require_permission(PAYROLL_CALENDAR_MANAGE))],
)
async def list_payroll_calendars(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    is_active: bool | None = Query(None),
) -> list[PayrollCalendarResponse]:
    service = PayrollService(db)
    return await service.list_payroll_calendars(ctx.tenant_id, is_active=is_active)


@router.post(
    "/periods",
    response_model=PayrollPeriodResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a payroll processing period",
    dependencies=[Depends(require_permission(PAYROLL_CALENDAR_MANAGE))],
)
async def create_payroll_period(
    payload: PayrollPeriodCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> PayrollPeriodResponse:
    service = PayrollService(db)
    return await service.create_payroll_period(ctx.tenant_id, payload, current_user.id)


@router.get(
    "/periods",
    response_model=list[PayrollPeriodResponse],
    summary="List payroll processing periods",
    dependencies=[Depends(require_permission(PAYROLL_CALENDAR_MANAGE))],
)
async def list_payroll_periods(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    calendar_id: UUID | None = Query(None),
) -> list[PayrollPeriodResponse]:
    service = PayrollService(db)
    return await service.list_payroll_periods(ctx.tenant_id, calendar_id=calendar_id)


# =============================================================================
# 7. PAYROLL RUNS & PROCESSING
# =============================================================================


@router.post(
    "/runs",
    response_model=PayrollRunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initialize a new payroll run batch",
    dependencies=[Depends(require_permission(PAYROLL_RUN_CREATE))],
)
async def create_payroll_run(
    payload: PayrollRunCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> PayrollRunResponse:
    service = PayrollService(db)
    return await service.create_payroll_run(ctx.tenant_id, payload, current_user.id)


@router.get(
    "/runs/{run_id}",
    response_model=PayrollRunResponse,
    summary="Get payroll run status and item aggregates",
    dependencies=[Depends(require_permission(PAYROLL_RUN_REVIEW))],
)
async def get_payroll_run(
    run_id: UUID,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> PayrollRunResponse:
    service = PayrollService(db)
    return await service.get_payroll_run(ctx.tenant_id, run_id)


@router.post(
    "/runs/{run_id}/calculate",
    response_model=PayrollRunResponse,
    summary="Execute payroll calculation engine with attendance and statutory integration",
    dependencies=[Depends(require_permission(PAYROLL_RUN_CALCULATE))],
)
async def calculate_payroll_run(
    run_id: UUID,
    payload: PayrollRunCalculateRequest,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> PayrollRunResponse:
    service = PayrollService(db)
    return await service.calculate_payroll_run(ctx.tenant_id, run_id, payload, current_user.id)


@router.post(
    "/runs/{run_id}/approve",
    response_model=PayrollRunResponse,
    summary="Approve calculated payroll run with separation-of-duties check",
    dependencies=[Depends(require_permission(PAYROLL_RUN_APPROVE))],
)
async def approve_payroll_run(
    run_id: UUID,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    notes: str | None = Query(None),
) -> PayrollRunResponse:
    service = PayrollService(db)
    return await service.approve_payroll_run(ctx.tenant_id, run_id, current_user.id, notes=notes)


@router.post(
    "/runs/{run_id}/cancel",
    response_model=PayrollRunResponse,
    summary="Cancel an unposted payroll run with reason",
    dependencies=[Depends(require_permission(PAYROLL_RUN_APPROVE))],
)
async def cancel_payroll_run(
    run_id: UUID,
    payload: PayrollRunCancelRequest,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> PayrollRunResponse:
    service = PayrollService(db)
    return await service.cancel_payroll_run(ctx.tenant_id, run_id, payload.reason, current_user.id)


@router.post(
    "/runs/{run_id}/post",
    response_model=PayrollJournalEntryResponse,
    summary="Post approved payroll run to balanced financial general ledger journal",
    dependencies=[Depends(require_permission(PAYROLL_RUN_POST))],
)
async def post_payroll_run(
    run_id: UUID,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> PayrollJournalEntryResponse:
    service = PayrollService(db)
    return await service.post_payroll_to_accounting(ctx.tenant_id, run_id, actor_id=current_user.id)


@router.get(
    "/runs/{run_id}/journal",
    response_model=PayrollJournalEntryResponse,
    summary="Get balanced general ledger journal entry for payroll run",
    dependencies=[Depends(require_permission(PAYROLL_RUN_POST))],
)
async def get_payroll_journal(
    run_id: UUID,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> PayrollJournalEntryResponse:
    service = PayrollService(db)
    return await service.get_payroll_journal_entry(ctx.tenant_id, run_id)


# =============================================================================
# 8. PAYMENT BATCHES & RECONCILIATION
# =============================================================================


@router.post(
    "/payment-batches",
    response_model=PayrollPaymentBatchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Prepare payment disbursement batch for approved payroll run",
    dependencies=[Depends(require_permission(PAYROLL_PAYMENT_MANAGE))],
)
async def create_payment_batch(
    payload: PayrollPaymentBatchCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> PayrollPaymentBatchResponse:
    service = PayrollService(db)
    return await service.create_payment_batch(ctx.tenant_id, payload, current_user.id)


@router.get(
    "/payment-batches/{batch_id}",
    response_model=PayrollPaymentBatchResponse,
    summary="Get payment batch items and reconciliation status",
    dependencies=[Depends(require_permission(PAYROLL_PAYMENT_MANAGE))],
)
async def get_payment_batch(
    batch_id: UUID,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> PayrollPaymentBatchResponse:
    service = PayrollService(db)
    return await service.get_payment_batch(ctx.tenant_id, batch_id)


@router.post(
    "/payment-batches/{batch_id}/reconcile",
    response_model=PayrollPaymentBatchResponse,
    summary="Reconcile disbursement payment items with bank confirmations",
    dependencies=[Depends(require_permission(PAYROLL_RECONCILIATION_MANAGE))],
)
async def reconcile_payment_batch(
    batch_id: UUID,
    payload: PayrollPaymentBatchReconcileRequest,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> PayrollPaymentBatchResponse:
    service = PayrollService(db)
    return await service.reconcile_payment_batch(ctx.tenant_id, batch_id, payload, current_user.id)


# =============================================================================
# 9. PAYSLIPS & EMPLOYEE SELF-SERVICE
# =============================================================================


@router.get(
    "/payslips/my-payslips",
    response_model=list[PayslipResponse],
    summary="View personal published payslips (Employee Self-Service)",
    dependencies=[Depends(require_permission(PAYROLL_PAYSLIP_READ_OWN))],
)
async def get_my_payslips(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[PayslipResponse]:
    stmt_emp = select(WorkforceEmployee).where(
        WorkforceEmployee.tenant_id == ctx.tenant_id,
        WorkforceEmployee.user_id == current_user.id,
    )
    emp = (await db.execute(stmt_emp)).scalar_one_or_none()
    if not emp:
        return []

    service = PayrollService(db)
    return await service.list_employee_payslips(ctx.tenant_id, emp.id)


@router.get(
    "/employees/{employee_id}/payslips",
    response_model=list[PayslipResponse],
    summary="View employee payslips (Authorized Administrators)",
    dependencies=[Depends(require_permission(PAYROLL_PAYSLIP_READ_AUTH))],
)
async def get_employee_payslips(
    employee_id: UUID,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[PayslipResponse]:
    service = PayrollService(db)
    return await service.list_employee_payslips(ctx.tenant_id, employee_id)


@router.get(
    "/payslips/token/{token}",
    response_model=PayslipResponse,
    summary="Secure token-based payslip document retrieval",
)
async def get_payslip_by_token(
    token: str,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> PayslipResponse:
    service = PayrollService(db)
    return await service.get_payslip_by_token(token)


@router.post(
    "/payslips/dispute",
    status_code=status.HTTP_201_CREATED,
    summary="Submit compensation/payslip discrepancy to Workforce HR case system",
    dependencies=[Depends(require_permission(PAYROLL_PAYSLIP_READ_OWN))],
)
async def submit_payslip_discrepancy(
    payload: PayslipDiscrepancyRequest,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, str]:
    stmt_emp = select(WorkforceEmployee).where(
        WorkforceEmployee.tenant_id == ctx.tenant_id,
        WorkforceEmployee.user_id == current_user.id,
    )
    emp = (await db.execute(stmt_emp)).scalar_one_or_none()
    if not emp:
        raise NotFoundException("Workforce employee profile not found for user.")

    case = WorkforceHRCase(
        id=uuid.uuid4(),
        tenant_id=ctx.tenant_id,
        employee_id=emp.id,
        case_number=f"HRC-PAY-{secrets.token_hex(3).upper()}",
        category=HRCaseCategory.PAYROLL,
        priority=HRCasePriority.HIGH,
        status=HRCaseStatus.SUBMITTED,
        subject=payload.subject,
        description=payload.description,
    )
    db.add(case)
    await db.commit()

    return {
        "status": "SUBMITTED",
        "case_number": case.case_number,
        "message": "Payroll discrepancy case filed successfully with HR.",
    }
