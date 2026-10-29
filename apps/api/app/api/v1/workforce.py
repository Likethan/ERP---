"""CampusOS Enterprise Workforce Management, Staff Lifecycle, Leave & Workload Administration REST API Router (Step 51).

CampusOS Tagline: "One Campus. One System. One Source of Truth."
"""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_current_user, get_tenant_context, require_permission
from app.core.exceptions import NotFoundException
from app.core.permissions import (
    WORKFORCE_AVAILABILITY_READ,
    WORKFORCE_EMPLOYEE_MANAGE,
    WORKFORCE_EMPLOYEE_READ,
    WORKFORCE_HR_CASE_MANAGE,
    WORKFORCE_HR_CASE_READ,
    WORKFORCE_LEAVE_APPROVE,
    WORKFORCE_LEAVE_BALANCE_MANAGE,
    WORKFORCE_LEAVE_POLICY_MANAGE,
    WORKFORCE_LEAVE_READ,
    WORKFORCE_LEAVE_SUBMIT,
    WORKFORCE_LIFECYCLE_MANAGE,
    WORKFORCE_READ,
    WORKFORCE_REPORTS_READ,
    WORKFORCE_WORKLOAD_MANAGE,
    WORKFORCE_WORKLOAD_READ,
)
from app.core.tenant import TenantContext
from app.models.people import User
from app.schemas.workforce import (
    WorkforceAvailabilityCheckResponse,
    WorkforceCapacityReport,
    WorkforceEmployeeCreate,
    WorkforceEmployeeResponse,
    WorkforceEmployeeTransitionRequest,
    WorkforceEmployeeUpdate,
    WorkforceEmploymentHistoryResponse,
    WorkforceHeadcountReport,
    WorkforceHRCaseCreate,
    WorkforceHRCaseResponse,
    WorkforceHRCaseUpdate,
    WorkforceLeaveBalanceAdjustRequest,
    WorkforceLeaveBalanceResponse,
    WorkforceLeaveCalendarEntry,
    WorkforceLeaveDecisionRequest,
    WorkforceLeavePolicyCreate,
    WorkforceLeavePolicyResponse,
    WorkforceLeaveRequestCreate,
    WorkforceLeaveRequestResponse,
    WorkforceLeaveTypeCreate,
    WorkforceLeaveTypeResponse,
    WorkforceLeaveUtilizationReport,
    WorkforceLifecycleCaseCreate,
    WorkforceLifecycleCaseResponse,
    WorkforceLifecycleTaskResponse,
    WorkforceLifecycleTaskUpdate,
    WorkforceSeparationInitiateRequest,
    WorkforceWorkloadAdjustmentCreate,
    WorkforceWorkloadAdjustmentResponse,
    WorkforceWorkloadExpectationCreate,
    WorkforceWorkloadExpectationResponse,
    WorkforceWorkloadSummaryResponse,
)
from app.services.workforce_service import workforce_service

router = APIRouter(prefix="/workforce", tags=["Workforce Management"])


# =============================================================================
# 1. EMPLOYEE MASTER & EMPLOYMENT RECORDS
# =============================================================================


@router.post(
    "/employees",
    response_model=WorkforceEmployeeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new workforce employee record",
    dependencies=[Depends(require_permission(WORKFORCE_EMPLOYEE_MANAGE))],
)
async def create_employee(
    payload: WorkforceEmployeeCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> WorkforceEmployeeResponse:
    return await workforce_service.create_employee(db, ctx.tenant_id, payload, current_user.id)


@router.get(
    "/employees",
    response_model=list[WorkforceEmployeeResponse],
    summary="List workforce employees with filtering and pagination",
    dependencies=[Depends(require_permission(WORKFORCE_EMPLOYEE_READ))],
)
async def list_employees(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    search: str | None = Query(None),
    department_id: UUID | None = Query(None),
    campus_id: UUID | None = Query(None),
    status_val: str | None = Query(None, alias="status"),
    employment_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> list[WorkforceEmployeeResponse]:
    employees, _ = await workforce_service.list_employees(
        db,
        ctx.tenant_id,
        search=search,
        department_id=department_id,
        campus_id=campus_id,
        status=status_val,
        employment_type=employment_type,
        page=page,
        page_size=page_size,
    )
    return employees


@router.get(
    "/employees/{employee_id}",
    response_model=WorkforceEmployeeResponse,
    summary="Get employee details",
    dependencies=[Depends(require_permission(WORKFORCE_EMPLOYEE_READ))],
)
async def get_employee(
    employee_id: UUID,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> WorkforceEmployeeResponse:
    return await workforce_service.get_employee_response(db, ctx.tenant_id, employee_id)


@router.patch(
    "/employees/{employee_id}",
    response_model=WorkforceEmployeeResponse,
    summary="Update employee details",
    dependencies=[Depends(require_permission(WORKFORCE_EMPLOYEE_MANAGE))],
)
async def update_employee(
    employee_id: UUID,
    payload: WorkforceEmployeeUpdate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> WorkforceEmployeeResponse:
    return await workforce_service.update_employee(db, ctx.tenant_id, employee_id, payload, current_user.id)


@router.post(
    "/employees/{employee_id}/transition",
    response_model=WorkforceEmployeeResponse,
    summary="Transition employee status with audit tracking",
    dependencies=[Depends(require_permission(WORKFORCE_EMPLOYEE_MANAGE))],
)
async def transition_employee_status(
    employee_id: UUID,
    payload: WorkforceEmployeeTransitionRequest,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> WorkforceEmployeeResponse:
    return await workforce_service.transition_employee_status(
        db, ctx.tenant_id, employee_id, payload, current_user.id
    )


@router.get(
    "/employees/{employee_id}/employment-history",
    response_model=list[WorkforceEmploymentHistoryResponse],
    summary="Get employment progression history",
    dependencies=[Depends(require_permission(WORKFORCE_EMPLOYEE_READ))],
)
async def get_employment_history(
    employee_id: UUID,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[WorkforceEmploymentHistoryResponse]:
    return await workforce_service.get_employment_history(db, ctx.tenant_id, employee_id)


# =============================================================================
# 2. STAFF LIFECYCLE: ONBOARDING & OFFBOARDING
# =============================================================================


@router.post(
    "/lifecycle-cases",
    response_model=WorkforceLifecycleCaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create onboarding or offboarding lifecycle case",
    dependencies=[Depends(require_permission(WORKFORCE_LIFECYCLE_MANAGE))],
)
async def create_lifecycle_case(
    payload: WorkforceLifecycleCaseCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> WorkforceLifecycleCaseResponse:
    return await workforce_service.create_lifecycle_case(db, ctx.tenant_id, payload, current_user.id)


@router.get(
    "/lifecycle-cases",
    response_model=list[WorkforceLifecycleCaseResponse],
    summary="List lifecycle cases with filters",
    dependencies=[Depends(require_permission(WORKFORCE_LIFECYCLE_MANAGE))],
)
async def list_lifecycle_cases(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    employee_id: UUID | None = Query(None),
    case_type: str | None = Query(None),
    status_val: str | None = Query(None, alias="status"),
) -> list[WorkforceLifecycleCaseResponse]:
    return await workforce_service.list_lifecycle_cases(
        db, ctx.tenant_id, employee_id=employee_id, case_type=case_type, status=status_val
    )


@router.get(
    "/lifecycle-cases/{case_id}",
    response_model=WorkforceLifecycleCaseResponse,
    summary="Get lifecycle case details and tasks",
    dependencies=[Depends(require_permission(WORKFORCE_LIFECYCLE_MANAGE))],
)
async def get_lifecycle_case(
    case_id: UUID,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> WorkforceLifecycleCaseResponse:
    return await workforce_service.get_lifecycle_case(db, ctx.tenant_id, case_id)


@router.patch(
    "/lifecycle-tasks/{task_id}",
    response_model=WorkforceLifecycleTaskResponse,
    summary="Update or complete a lifecycle task",
    dependencies=[Depends(require_permission(WORKFORCE_LIFECYCLE_MANAGE))],
)
async def update_lifecycle_task(
    task_id: UUID,
    payload: WorkforceLifecycleTaskUpdate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> WorkforceLifecycleTaskResponse:
    return await workforce_service.update_lifecycle_task(db, ctx.tenant_id, task_id, payload, current_user.id)


@router.post(
    "/employees/{employee_id}/initiate-offboarding",
    response_model=WorkforceLifecycleCaseResponse,
    summary="Initiate offboarding and exit clearance workflow",
    dependencies=[Depends(require_permission(WORKFORCE_LIFECYCLE_MANAGE))],
)
async def initiate_offboarding(
    employee_id: UUID,
    payload: WorkforceSeparationInitiateRequest,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> WorkforceLifecycleCaseResponse:
    payload.employee_id = employee_id
    return await workforce_service.initiate_offboarding(db, ctx.tenant_id, payload, current_user.id)


# =============================================================================
# 3. LEAVE TYPES & POLICIES
# =============================================================================


@router.post(
    "/leave/types",
    response_model=WorkforceLeaveTypeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create leave category",
    dependencies=[Depends(require_permission(WORKFORCE_LEAVE_POLICY_MANAGE))],
)
async def create_leave_type(
    payload: WorkforceLeaveTypeCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> WorkforceLeaveTypeResponse:
    return await workforce_service.create_leave_type(db, ctx.tenant_id, payload)


@router.get(
    "/leave/types",
    response_model=list[WorkforceLeaveTypeResponse],
    summary="List leave types",
    dependencies=[Depends(require_permission(WORKFORCE_READ))],
)
async def list_leave_types(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    active_only: bool = Query(True),
) -> list[WorkforceLeaveTypeResponse]:
    return await workforce_service.list_leave_types(db, ctx.tenant_id, active_only=active_only)


@router.post(
    "/leave/policies",
    response_model=WorkforceLeavePolicyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create leave policy",
    dependencies=[Depends(require_permission(WORKFORCE_LEAVE_POLICY_MANAGE))],
)
async def create_leave_policy(
    payload: WorkforceLeavePolicyCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> WorkforceLeavePolicyResponse:
    return await workforce_service.create_leave_policy(db, ctx.tenant_id, payload)


@router.get(
    "/leave/policies",
    response_model=list[WorkforceLeavePolicyResponse],
    summary="List leave policies",
    dependencies=[Depends(require_permission(WORKFORCE_READ))],
)
async def list_leave_policies(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    leave_type_id: UUID | None = Query(None),
) -> list[WorkforceLeavePolicyResponse]:
    return await workforce_service.list_leave_policies(db, ctx.tenant_id, leave_type_id=leave_type_id)


# =============================================================================
# 4. LEAVE BALANCES & TRANSACTIONS
# =============================================================================


@router.get(
    "/leave/balances",
    response_model=list[WorkforceLeaveBalanceResponse],
    summary="List employee leave balances",
    dependencies=[Depends(require_permission(WORKFORCE_LEAVE_READ))],
)
async def list_leave_balances(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    employee_id: UUID | None = Query(None),
    calendar_year: int | None = Query(None),
) -> list[WorkforceLeaveBalanceResponse]:
    return await workforce_service.list_leave_balances(
        db, ctx.tenant_id, employee_id=employee_id, calendar_year=calendar_year
    )


@router.post(
    "/leave/balances/adjust",
    response_model=WorkforceLeaveBalanceResponse,
    summary="Adjust employee leave balance with audit justification",
    dependencies=[Depends(require_permission(WORKFORCE_LEAVE_BALANCE_MANAGE))],
)
async def adjust_leave_balance(
    payload: WorkforceLeaveBalanceAdjustRequest,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> WorkforceLeaveBalanceResponse:
    return await workforce_service.adjust_leave_balance(db, ctx.tenant_id, payload, current_user.id)


# =============================================================================
# 5. LEAVE REQUESTS, APPROVALS & WORKFLOWS
# =============================================================================


@router.post(
    "/leave/requests",
    response_model=WorkforceLeaveRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit staff leave application",
    dependencies=[Depends(require_permission(WORKFORCE_LEAVE_SUBMIT))],
)
async def submit_leave_request(
    payload: WorkforceLeaveRequestCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> WorkforceLeaveRequestResponse:
    return await workforce_service.submit_leave_request(db, ctx.tenant_id, payload, current_user)


@router.get(
    "/leave/requests",
    response_model=list[WorkforceLeaveRequestResponse],
    summary="List leave requests with filters",
    dependencies=[Depends(require_permission(WORKFORCE_LEAVE_READ))],
)
async def list_leave_requests(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    employee_id: UUID | None = Query(None),
    status_val: str | None = Query(None, alias="status"),
    department_id: UUID | None = Query(None),
) -> list[WorkforceLeaveRequestResponse]:
    return await workforce_service.list_leave_requests(
        db, ctx.tenant_id, employee_id=employee_id, status=status_val, department_id=department_id
    )


@router.get(
    "/leave/requests/{request_id}",
    response_model=WorkforceLeaveRequestResponse,
    summary="Get leave request details and decision steps",
    dependencies=[Depends(require_permission(WORKFORCE_LEAVE_READ))],
)
async def get_leave_request(
    request_id: UUID,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> WorkforceLeaveRequestResponse:
    return await workforce_service.get_leave_request_response(db, ctx.tenant_id, request_id)


@router.post(
    "/leave/requests/{request_id}/approve",
    response_model=WorkforceLeaveRequestResponse,
    summary="Approve leave request and consume balance",
    dependencies=[Depends(require_permission(WORKFORCE_LEAVE_APPROVE))],
)
async def approve_leave_request(
    request_id: UUID,
    payload: WorkforceLeaveDecisionRequest,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> WorkforceLeaveRequestResponse:
    return await workforce_service.approve_leave_request(
        db, ctx.tenant_id, request_id, payload.decision_reason, current_user.id
    )


@router.post(
    "/leave/requests/{request_id}/reject",
    response_model=WorkforceLeaveRequestResponse,
    summary="Reject leave request and release reserved days",
    dependencies=[Depends(require_permission(WORKFORCE_LEAVE_APPROVE))],
)
async def reject_leave_request(
    request_id: UUID,
    payload: WorkforceLeaveDecisionRequest,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> WorkforceLeaveRequestResponse:
    reason = payload.decision_reason or "Leave request declined by authorized approver."
    return await workforce_service.reject_leave_request(
        db, ctx.tenant_id, request_id, reason, current_user.id
    )


@router.post(
    "/leave/requests/{request_id}/cancel",
    response_model=WorkforceLeaveRequestResponse,
    summary="Cancel or withdraw leave request",
    dependencies=[Depends(require_permission(WORKFORCE_LEAVE_SUBMIT))],
)
async def cancel_leave_request(
    request_id: UUID,
    payload: WorkforceLeaveDecisionRequest,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> WorkforceLeaveRequestResponse:
    reason = payload.decision_reason or "Leave request withdrawn by applicant."
    return await workforce_service.cancel_or_withdraw_leave_request(
        db, ctx.tenant_id, request_id, reason, current_user.id
    )


@router.get(
    "/leave/calendar",
    response_model=list[WorkforceLeaveCalendarEntry],
    summary="View privacy-preserving absence calendar",
    dependencies=[Depends(require_permission(WORKFORCE_READ))],
)
async def get_leave_calendar(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    start_date: date = Query(...),
    end_date: date = Query(...),
    department_id: UUID | None = Query(None),
    campus_id: UUID | None = Query(None),
) -> list[WorkforceLeaveCalendarEntry]:
    return await workforce_service.get_leave_calendar(
        db, ctx.tenant_id, start_date=start_date, end_date=end_date, department_id=department_id, campus_id=campus_id
    )


# =============================================================================
# 6. AVAILABILITY & TIMETABLE CONFLICTS
# =============================================================================


@router.get(
    "/availability",
    response_model=WorkforceAvailabilityCheckResponse,
    summary="Check staff availability and timetable scheduling collisions",
    dependencies=[Depends(require_permission(WORKFORCE_AVAILABILITY_READ))],
)
async def check_availability(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    employee_id: UUID = Query(...),
    start_date: date = Query(...),
    end_date: date = Query(...),
) -> WorkforceAvailabilityCheckResponse:
    return await workforce_service.check_availability(
        db, ctx.tenant_id, employee_id=employee_id, start_date=start_date, end_date=end_date
    )


# =============================================================================
# 7. WORKLOAD & WORKFORCE PLANNING
# =============================================================================


@router.get(
    "/workload",
    response_model=WorkforceWorkloadSummaryResponse,
    summary="Compute staff workload against weekly targets",
    dependencies=[Depends(require_permission(WORKFORCE_WORKLOAD_READ))],
)
async def get_workload(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    employee_id: UUID = Query(...),
    academic_year_id: UUID | None = Query(None),
    semester_id: UUID | None = Query(None),
) -> WorkforceWorkloadSummaryResponse:
    return await workforce_service.get_workload_summary(
        db, ctx.tenant_id, employee_id=employee_id, academic_year_id=academic_year_id, semester_id=semester_id
    )


@router.post(
    "/workload/expectations",
    response_model=WorkforceWorkloadExpectationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Define workload target expectations",
    dependencies=[Depends(require_permission(WORKFORCE_WORKLOAD_MANAGE))],
)
async def create_workload_expectation(
    payload: WorkforceWorkloadExpectationCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> WorkforceWorkloadExpectationResponse:
    return await workforce_service.create_or_update_workload_expectation(db, ctx.tenant_id, payload)


@router.post(
    "/workload/adjustments",
    response_model=WorkforceWorkloadAdjustmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record authorized workload duty adjustment",
    dependencies=[Depends(require_permission(WORKFORCE_WORKLOAD_MANAGE))],
)
async def create_workload_adjustment(
    payload: WorkforceWorkloadAdjustmentCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> WorkforceWorkloadAdjustmentResponse:
    return await workforce_service.create_workload_adjustment(db, ctx.tenant_id, payload, current_user.id)


# =============================================================================
# 8. EMPLOYEE SELF-SERVICE & HR CASES
# =============================================================================


@router.post(
    "/hr-cases",
    response_model=WorkforceHRCaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit employee self-service inquiry or profile change request",
    dependencies=[Depends(require_permission(WORKFORCE_HR_CASE_READ))],
)
async def create_hr_case(
    payload: WorkforceHRCaseCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> WorkforceHRCaseResponse:
    return await workforce_service.create_hr_case(db, ctx.tenant_id, payload, current_user)


@router.get(
    "/hr-cases",
    response_model=list[WorkforceHRCaseResponse],
    summary="List HR service cases",
    dependencies=[Depends(require_permission(WORKFORCE_HR_CASE_READ))],
)
async def list_hr_cases(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    employee_id: UUID | None = Query(None),
    category: str | None = Query(None),
    status_val: str | None = Query(None, alias="status"),
) -> list[WorkforceHRCaseResponse]:
    return await workforce_service.list_hr_cases(
        db, ctx.tenant_id, employee_id=employee_id, category=category, status=status_val
    )


@router.get(
    "/hr-cases/{case_id}",
    response_model=WorkforceHRCaseResponse,
    summary="Get HR case details",
    dependencies=[Depends(require_permission(WORKFORCE_HR_CASE_READ))],
)
async def get_hr_case(
    case_id: UUID,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> WorkforceHRCaseResponse:
    return await workforce_service.get_hr_case(db, ctx.tenant_id, case_id)


@router.patch(
    "/hr-cases/{case_id}",
    response_model=WorkforceHRCaseResponse,
    summary="Update or resolve HR case",
    dependencies=[Depends(require_permission(WORKFORCE_HR_CASE_MANAGE))],
)
async def update_hr_case(
    case_id: UUID,
    payload: WorkforceHRCaseUpdate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> WorkforceHRCaseResponse:
    return await workforce_service.update_hr_case(db, ctx.tenant_id, case_id, payload, current_user.id)


# =============================================================================
# 9. EMPLOYEE SELF-SERVICE SHORTCUTS
# =============================================================================


@router.get(
    "/self-service/profile",
    response_model=WorkforceEmployeeResponse,
    summary="Get current user's workforce profile",
)
async def get_self_profile(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> WorkforceEmployeeResponse:
    emp = await workforce_service.get_employee_by_user_id(db, ctx.tenant_id, current_user.id)
    if not emp:
        raise NotFoundException("Workforce profile not established for this user")
    return await workforce_service.get_employee_response(db, ctx.tenant_id, emp.id)


@router.get(
    "/self-service/leave-balances",
    response_model=list[WorkforceLeaveBalanceResponse],
    summary="Get current user's leave balances",
)
async def get_self_leave_balances(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    calendar_year: int | None = Query(None),
) -> list[WorkforceLeaveBalanceResponse]:
    emp = await workforce_service.get_employee_by_user_id(db, ctx.tenant_id, current_user.id)
    if not emp:
        return []
    return await workforce_service.list_leave_balances(
        db, ctx.tenant_id, employee_id=emp.id, calendar_year=calendar_year
    )


@router.get(
    "/self-service/leave-requests",
    response_model=list[WorkforceLeaveRequestResponse],
    summary="Get current user's leave requests",
)
async def get_self_leave_requests(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[WorkforceLeaveRequestResponse]:
    emp = await workforce_service.get_employee_by_user_id(db, ctx.tenant_id, current_user.id)
    if not emp:
        return []
    return await workforce_service.list_leave_requests(db, ctx.tenant_id, employee_id=emp.id)


# =============================================================================
# 10. REPORTING & ANALYTICS
# =============================================================================


@router.get(
    "/reports/headcount",
    response_model=WorkforceHeadcountReport,
    summary="Headcount composition by department, designation, and employment status",
    dependencies=[Depends(require_permission(WORKFORCE_REPORTS_READ))],
)
async def get_headcount_report(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> WorkforceHeadcountReport:
    return await workforce_service.get_headcount_report(db, ctx.tenant_id)


@router.get(
    "/reports/leave-utilization",
    response_model=WorkforceLeaveUtilizationReport,
    summary="Leave utilization and pending request turnaround metrics",
    dependencies=[Depends(require_permission(WORKFORCE_REPORTS_READ))],
)
async def get_leave_utilization_report(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    calendar_year: int | None = Query(None),
) -> WorkforceLeaveUtilizationReport:
    return await workforce_service.get_leave_utilization_report(db, ctx.tenant_id, calendar_year=calendar_year)


@router.get(
    "/reports/capacity",
    response_model=WorkforceCapacityReport,
    summary="Workload distribution and staffing capacity report",
    dependencies=[Depends(require_permission(WORKFORCE_REPORTS_READ))],
)
async def get_capacity_report(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> WorkforceCapacityReport:
    return await workforce_service.get_capacity_report(db, ctx.tenant_id)
