"""Student Success, Academic Advising, Early-Warning & Intervention API Router (Step 47)."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_current_user, get_tenant_context, require_permission
from app.core.permissions import (
    STUDENT_SUCCESS_ADVISING_MANAGE,
    STUDENT_SUCCESS_ADVISING_READ,
    STUDENT_SUCCESS_APPOINTMENT_MANAGE,
    STUDENT_SUCCESS_CASE_MANAGE,
    STUDENT_SUCCESS_CASE_READ,
    STUDENT_SUCCESS_EARLY_WARNING_MANAGE,
    STUDENT_SUCCESS_EARLY_WARNING_READ,
    STUDENT_SUCCESS_INTERVENTION_MANAGE,
    STUDENT_SUCCESS_INTERVENTION_READ,
    STUDENT_SUCCESS_REPORTS_READ,
    STUDENT_SUCCESS_STUDENT_SELF_READ,
)
from app.core.tenant import TenantContext
from app.models.people import User
from app.schemas.common import ApiResponse
from app.schemas.student_success import (
    AdvisingActionItemCreate,
    AdvisingActionItemResponse,
    AdvisingActionItemUpdate,
    AdvisingAppointmentRequest,
    AdvisingAppointmentResponse,
    AdvisingAppointmentUpdate,
    AdvisingPlanCreate,
    AdvisingPlanResponse,
    AdvisorCaseloadSummaryItem,
    AdvisorProfileCreate,
    AdvisorProfileResponse,
    AdvisorProfileUpdate,
    AdvisorStudentAssignmentCreate,
    AdvisorStudentAssignmentReassign,
    AdvisorStudentAssignmentResponse,
    EarlyWarningEvaluationRequest,
    EarlyWarningEvaluationResponse,
    EarlyWarningRuleCreate,
    EarlyWarningRuleResponse,
    EarlyWarningRuleUpdate,
    EarlyWarningRuleVersionResponse,
    EarlyWarningSignalDismiss,
    EarlyWarningSignalLinkCase,
    EarlyWarningSignalResolve,
    EarlyWarningSignalResponse,
    InterventionActionCreate,
    InterventionActionResponse,
    InterventionActionUpdate,
    InterventionPlanCreate,
    InterventionPlanResponse,
    InterventionPlanUpdate,
    StudentActionProgressSubmit,
    StudentSelfOverviewResponse,
    StudentSuccessCaseCreate,
    StudentSuccessCaseEscalate,
    StudentSuccessCaseNoteCreate,
    StudentSuccessCaseNoteResponse,
    StudentSuccessCaseReassign,
    StudentSuccessCaseReopen,
    StudentSuccessCaseResponse,
    StudentSuccessCaseStatusTransition,
    StudentSuccessCaseUpdate,
    StudentSuccessOverviewMetrics,
)
from app.services.student_success_service import StudentSuccessService

student_success_router = APIRouter(prefix="/student-success", tags=["Student Success & Advising"])


# =============================================================================
# 1. CASE MANAGEMENT ENDPOINTS
# =============================================================================


@student_success_router.post(
    "/cases",
    response_model=ApiResponse[StudentSuccessCaseResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_CASE_MANAGE))],
)
async def create_case(
    payload: StudentSuccessCaseCreate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[StudentSuccessCaseResponse]:
    """Open a structured student-success case."""
    service = StudentSuccessService(db)
    case = await service.create_case(tenant_ctx.tenant_id, payload, current_user.id)
    return ApiResponse(data=StudentSuccessCaseResponse.model_validate(case))


@student_success_router.get(
    "/cases",
    response_model=ApiResponse[list[StudentSuccessCaseResponse]],
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_CASE_READ))],
)
async def list_cases(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    student_id: UUID | None = None,
    category: str | None = None,
    priority: str | None = None,
    status_val: str | None = Query(None, alias="status"),
    assigned_advisor_id: UUID | None = None,
    is_escalated: bool | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> ApiResponse[list[StudentSuccessCaseResponse]]:
    """List student-success cases with filtering."""
    service = StudentSuccessService(db)
    cases = await service.list_cases(
        tenant_id=tenant_ctx.tenant_id,
        student_id=student_id,
        category=category,
        priority=priority,
        status_val=status_val,
        assigned_advisor_id=assigned_advisor_id,
        is_escalated=is_escalated,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(data=[StudentSuccessCaseResponse.model_validate(c) for c in cases])


@student_success_router.get(
    "/cases/{case_id}",
    response_model=ApiResponse[StudentSuccessCaseResponse],
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_CASE_READ))],
)
async def get_case(
    case_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
) -> ApiResponse[StudentSuccessCaseResponse]:
    """Fetch details of a single student-success case."""
    service = StudentSuccessService(db)
    case = await service.get_case(tenant_ctx.tenant_id, case_id)
    return ApiResponse(data=StudentSuccessCaseResponse.model_validate(case))


@student_success_router.patch(
    "/cases/{case_id}",
    response_model=ApiResponse[StudentSuccessCaseResponse],
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_CASE_MANAGE))],
)
async def update_case(
    case_id: UUID,
    payload: StudentSuccessCaseUpdate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[StudentSuccessCaseResponse]:
    """Update editable fields of a case."""
    service = StudentSuccessService(db)
    case = await service.update_case(tenant_ctx.tenant_id, case_id, payload, current_user.id)
    return ApiResponse(data=StudentSuccessCaseResponse.model_validate(case))


@student_success_router.post(
    "/cases/{case_id}/status",
    response_model=ApiResponse[StudentSuccessCaseResponse],
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_CASE_MANAGE))],
)
async def transition_case_status(
    case_id: UUID,
    payload: StudentSuccessCaseStatusTransition,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[StudentSuccessCaseResponse]:
    """Transition case lifecycle status."""
    service = StudentSuccessService(db)
    case = await service.transition_case_status(tenant_ctx.tenant_id, case_id, payload, current_user.id)
    return ApiResponse(data=StudentSuccessCaseResponse.model_validate(case))


@student_success_router.post(
    "/cases/{case_id}/reassign",
    response_model=ApiResponse[StudentSuccessCaseResponse],
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_CASE_MANAGE))],
)
async def reassign_case(
    case_id: UUID,
    payload: StudentSuccessCaseReassign,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[StudentSuccessCaseResponse]:
    """Reassign case ownership with justification."""
    service = StudentSuccessService(db)
    case = await service.reassign_case(tenant_ctx.tenant_id, case_id, payload, current_user.id)
    return ApiResponse(data=StudentSuccessCaseResponse.model_validate(case))


@student_success_router.post(
    "/cases/{case_id}/escalate",
    response_model=ApiResponse[StudentSuccessCaseResponse],
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_CASE_MANAGE))],
)
async def escalate_case(
    case_id: UUID,
    payload: StudentSuccessCaseEscalate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[StudentSuccessCaseResponse]:
    """Escalate case for leadership review."""
    service = StudentSuccessService(db)
    case = await service.escalate_case(tenant_ctx.tenant_id, case_id, payload, current_user.id)
    return ApiResponse(data=StudentSuccessCaseResponse.model_validate(case))


@student_success_router.post(
    "/cases/{case_id}/reopen",
    response_model=ApiResponse[StudentSuccessCaseResponse],
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_CASE_MANAGE))],
)
async def reopen_case(
    case_id: UUID,
    payload: StudentSuccessCaseReopen,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[StudentSuccessCaseResponse]:
    """Reopen a closed or resolved case."""
    service = StudentSuccessService(db)
    case = await service.reopen_case(tenant_ctx.tenant_id, case_id, payload, current_user.id)
    return ApiResponse(data=StudentSuccessCaseResponse.model_validate(case))


@student_success_router.post(
    "/cases/{case_id}/notes",
    response_model=ApiResponse[StudentSuccessCaseNoteResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_CASE_MANAGE))],
)
async def add_case_note(
    case_id: UUID,
    payload: StudentSuccessCaseNoteCreate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[StudentSuccessCaseNoteResponse]:
    """Add a note or comment to a case."""
    service = StudentSuccessService(db)
    note = await service.add_case_note(tenant_ctx.tenant_id, case_id, payload, current_user.id)
    return ApiResponse(data=StudentSuccessCaseNoteResponse.model_validate(note))


@student_success_router.get(
    "/cases/{case_id}/notes",
    response_model=ApiResponse[list[StudentSuccessCaseNoteResponse]],
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_CASE_READ))],
)
async def list_case_notes(
    case_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
) -> ApiResponse[list[StudentSuccessCaseNoteResponse]]:
    """List case notes and meeting summaries."""
    service = StudentSuccessService(db)
    notes = await service.list_case_notes(tenant_ctx.tenant_id, case_id, student_view=False)
    return ApiResponse(data=[StudentSuccessCaseNoteResponse.model_validate(n) for n in notes])


# =============================================================================
# 2. ADVISOR PROFILES & ASSIGNMENTS ENDPOINTS
# =============================================================================


@student_success_router.post(
    "/advisors",
    response_model=ApiResponse[AdvisorProfileResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_ADVISING_MANAGE))],
)
async def create_advisor(
    payload: AdvisorProfileCreate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
) -> ApiResponse[AdvisorProfileResponse]:
    """Register an advisor profile with capacity limits."""
    service = StudentSuccessService(db)
    adv = await service.create_advisor_profile(tenant_ctx.tenant_id, payload)
    return ApiResponse(data=AdvisorProfileResponse.model_validate(adv))


@student_success_router.get(
    "/advisors",
    response_model=ApiResponse[list[AdvisorProfileResponse]],
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_ADVISING_READ))],
)
async def list_advisors(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    department_id: UUID | None = None,
    is_active: bool | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> ApiResponse[list[AdvisorProfileResponse]]:
    """List advisor profiles with caseload utilization telemetry."""
    service = StudentSuccessService(db)
    advisors = await service.list_advisor_profiles(
        tenant_id=tenant_ctx.tenant_id,
        department_id=department_id,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(data=[AdvisorProfileResponse.model_validate(a) for a in advisors])


@student_success_router.get(
    "/advisors/{advisor_id}",
    response_model=ApiResponse[AdvisorProfileResponse],
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_ADVISING_READ))],
)
async def get_advisor(
    advisor_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
) -> ApiResponse[AdvisorProfileResponse]:
    """Fetch an advisor profile."""
    service = StudentSuccessService(db)
    adv = await service.get_advisor_profile(tenant_ctx.tenant_id, advisor_id)
    return ApiResponse(data=AdvisorProfileResponse.model_validate(adv))


@student_success_router.patch(
    "/advisors/{advisor_id}",
    response_model=ApiResponse[AdvisorProfileResponse],
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_ADVISING_MANAGE))],
)
async def update_advisor(
    advisor_id: UUID,
    payload: AdvisorProfileUpdate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
) -> ApiResponse[AdvisorProfileResponse]:
    """Update an advisor's capacity or departmental scope."""
    service = StudentSuccessService(db)
    adv = await service.update_advisor_profile(tenant_ctx.tenant_id, advisor_id, payload)
    return ApiResponse(data=AdvisorProfileResponse.model_validate(adv))


@student_success_router.post(
    "/assignments",
    response_model=ApiResponse[AdvisorStudentAssignmentResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_ADVISING_MANAGE))],
)
async def assign_advisor(
    payload: AdvisorStudentAssignmentCreate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[AdvisorStudentAssignmentResponse]:
    """Pair an advisor to a student, checking capacity."""
    service = StudentSuccessService(db)
    assign = await service.assign_advisor_to_student(tenant_ctx.tenant_id, payload, current_user.id)
    return ApiResponse(data=AdvisorStudentAssignmentResponse.model_validate(assign))


@student_success_router.get(
    "/assignments",
    response_model=ApiResponse[list[AdvisorStudentAssignmentResponse]],
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_ADVISING_READ))],
)
async def list_assignments(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    student_id: UUID | None = None,
    advisor_id: UUID | None = None,
    status_val: str | None = Query(None, alias="status"),
) -> ApiResponse[list[AdvisorStudentAssignmentResponse]]:
    """List advisor-to-student pairings."""
    service = StudentSuccessService(db)
    assignments = await service.list_student_assignments(
        tenant_id=tenant_ctx.tenant_id,
        student_id=student_id,
        advisor_id=advisor_id,
        status_val=status_val,
    )
    return ApiResponse(data=[AdvisorStudentAssignmentResponse.model_validate(a) for a in assignments])


@student_success_router.post(
    "/assignments/{assignment_id}/reassign",
    response_model=ApiResponse[AdvisorStudentAssignmentResponse],
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_ADVISING_MANAGE))],
)
async def reassign_advisor_student(
    assignment_id: UUID,
    payload: AdvisorStudentAssignmentReassign,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[AdvisorStudentAssignmentResponse]:
    """Reassign student to a new advisor."""
    service = StudentSuccessService(db)
    new_assign = await service.reassign_advisor_student(
        tenant_ctx.tenant_id, assignment_id, payload, current_user.id
    )
    return ApiResponse(data=AdvisorStudentAssignmentResponse.model_validate(new_assign))


# =============================================================================
# 3. ADVISING PLANS ENDPOINTS
# =============================================================================


@student_success_router.post(
    "/plans",
    response_model=ApiResponse[AdvisingPlanResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_ADVISING_MANAGE))],
)
async def create_advising_plan(
    payload: AdvisingPlanCreate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[AdvisingPlanResponse]:
    """Create an academic advising roadmap."""
    service = StudentSuccessService(db)
    plan = await service.create_advising_plan(tenant_ctx.tenant_id, payload, current_user.id)
    return ApiResponse(data=AdvisingPlanResponse.model_validate(plan))


@student_success_router.get(
    "/plans",
    response_model=ApiResponse[list[AdvisingPlanResponse]],
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_ADVISING_READ))],
)
async def list_advising_plans(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    student_id: UUID | None = None,
    advisor_id: UUID | None = None,
    status_val: str | None = Query(None, alias="status"),
) -> ApiResponse[list[AdvisingPlanResponse]]:
    """List advising plans."""
    service = StudentSuccessService(db)
    plans = await service.list_advising_plans(
        tenant_id=tenant_ctx.tenant_id,
        student_id=student_id,
        advisor_id=advisor_id,
        status_val=status_val,
    )
    return ApiResponse(data=[AdvisingPlanResponse.model_validate(p) for p in plans])


@student_success_router.get(
    "/plans/{plan_id}",
    response_model=ApiResponse[AdvisingPlanResponse],
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_ADVISING_READ))],
)
async def get_advising_plan(
    plan_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
) -> ApiResponse[AdvisingPlanResponse]:
    """Fetch an advising plan with action items."""
    service = StudentSuccessService(db)
    plan = await service.get_advising_plan(tenant_ctx.tenant_id, plan_id)
    return ApiResponse(data=AdvisingPlanResponse.model_validate(plan))


@student_success_router.post(
    "/plans/{plan_id}/actions",
    response_model=ApiResponse[AdvisingActionItemResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_ADVISING_MANAGE))],
)
async def add_action_item(
    plan_id: UUID,
    payload: AdvisingActionItemCreate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
) -> ApiResponse[AdvisingActionItemResponse]:
    """Add a milestone or action item to an advising plan."""
    service = StudentSuccessService(db)
    item = await service.add_action_item(tenant_ctx.tenant_id, plan_id, payload)
    return ApiResponse(data=AdvisingActionItemResponse.model_validate(item))


@student_success_router.patch(
    "/action-items/{action_id}",
    response_model=ApiResponse[AdvisingActionItemResponse],
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_ADVISING_MANAGE))],
)
async def update_action_item(
    action_id: UUID,
    payload: AdvisingActionItemUpdate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
) -> ApiResponse[AdvisingActionItemResponse]:
    """Update progress or complete an action item."""
    service = StudentSuccessService(db)
    item = await service.update_action_item(tenant_ctx.tenant_id, action_id, payload)
    return ApiResponse(data=AdvisingActionItemResponse.model_validate(item))


# =============================================================================
# 4. EARLY WARNING RULES & EVALUATIONS ENDPOINTS
# =============================================================================


@student_success_router.post(
    "/rules",
    response_model=ApiResponse[EarlyWarningRuleResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_EARLY_WARNING_MANAGE))],
)
async def create_early_warning_rule(
    payload: EarlyWarningRuleCreate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[EarlyWarningRuleResponse]:
    """Create an early-warning risk rule."""
    service = StudentSuccessService(db)
    rule = await service.create_early_warning_rule(tenant_ctx.tenant_id, payload, current_user.id)
    return ApiResponse(data=EarlyWarningRuleResponse.model_validate(rule))


@student_success_router.get(
    "/rules",
    response_model=ApiResponse[list[EarlyWarningRuleResponse]],
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_EARLY_WARNING_READ))],
)
async def list_early_warning_rules(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    category: str | None = None,
    is_active: bool | None = None,
) -> ApiResponse[list[EarlyWarningRuleResponse]]:
    """List early-warning rules."""
    service = StudentSuccessService(db)
    rules = await service.list_early_warning_rules(tenant_ctx.tenant_id, category, is_active)
    return ApiResponse(data=[EarlyWarningRuleResponse.model_validate(r) for r in rules])


@student_success_router.get(
    "/rules/{rule_id}",
    response_model=ApiResponse[EarlyWarningRuleResponse],
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_EARLY_WARNING_READ))],
)
async def get_early_warning_rule(
    rule_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
) -> ApiResponse[EarlyWarningRuleResponse]:
    """Fetch an early-warning rule."""
    service = StudentSuccessService(db)
    rule = await service.get_early_warning_rule(tenant_ctx.tenant_id, rule_id)
    return ApiResponse(data=EarlyWarningRuleResponse.model_validate(rule))


@student_success_router.patch(
    "/rules/{rule_id}",
    response_model=ApiResponse[EarlyWarningRuleResponse],
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_EARLY_WARNING_MANAGE))],
)
async def update_early_warning_rule(
    rule_id: UUID,
    payload: EarlyWarningRuleUpdate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[EarlyWarningRuleResponse]:
    """Update rule thresholds, automatically incrementing audit version."""
    service = StudentSuccessService(db)
    rule = await service.update_early_warning_rule(
        tenant_ctx.tenant_id, rule_id, payload, current_user.id
    )
    return ApiResponse(data=EarlyWarningRuleResponse.model_validate(rule))


@student_success_router.get(
    "/rules/{rule_id}/versions",
    response_model=ApiResponse[list[EarlyWarningRuleVersionResponse]],
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_EARLY_WARNING_READ))],
)
async def list_rule_versions(
    rule_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
) -> ApiResponse[list[EarlyWarningRuleVersionResponse]]:
    """Fetch audit history of threshold and parameter changes to a rule."""
    service = StudentSuccessService(db)
    versions = await service.list_rule_versions(tenant_ctx.tenant_id, rule_id)
    return ApiResponse(data=[EarlyWarningRuleVersionResponse.model_validate(v) for v in versions])


@student_success_router.post(
    "/evaluations",
    response_model=ApiResponse[list[EarlyWarningEvaluationResponse]],
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_EARLY_WARNING_MANAGE))],
)
async def trigger_evaluations(
    payload: EarlyWarningEvaluationRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[list[EarlyWarningEvaluationResponse]]:
    """Trigger explainable rule evaluation across cohorts, generating deduplicated signals."""
    service = StudentSuccessService(db)
    evals = await service.evaluate_rules(
        tenant_id=tenant_ctx.tenant_id,
        payload=payload,
        triggered_by="MANUAL_REQUEST",
        user_id=current_user.id,
    )
    return ApiResponse(data=[EarlyWarningEvaluationResponse.model_validate(e) for e in evals])


# =============================================================================
# 5. RISK SIGNALS LIFECYCLE ENDPOINTS
# =============================================================================


@student_success_router.get(
    "/signals",
    response_model=ApiResponse[list[EarlyWarningSignalResponse]],
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_EARLY_WARNING_READ))],
)
async def list_signals(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    student_id: UUID | None = None,
    rule_id: UUID | None = None,
    status_val: str | None = Query(None, alias="status"),
    severity: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> ApiResponse[list[EarlyWarningSignalResponse]]:
    """List early warning signals."""
    service = StudentSuccessService(db)
    signals = await service.list_signals(
        tenant_id=tenant_ctx.tenant_id,
        student_id=student_id,
        rule_id=rule_id,
        status_val=status_val,
        severity=severity,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(data=[EarlyWarningSignalResponse.model_validate(s) for s in signals])


@student_success_router.get(
    "/signals/{signal_id}",
    response_model=ApiResponse[EarlyWarningSignalResponse],
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_EARLY_WARNING_READ))],
)
async def get_signal(
    signal_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
) -> ApiResponse[EarlyWarningSignalResponse]:
    """Fetch an early warning risk signal with source metric audit evidence."""
    service = StudentSuccessService(db)
    signal = await service.get_signal(tenant_ctx.tenant_id, signal_id)
    return ApiResponse(data=EarlyWarningSignalResponse.model_validate(signal))


@student_success_router.post(
    "/signals/{signal_id}/acknowledge",
    response_model=ApiResponse[EarlyWarningSignalResponse],
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_EARLY_WARNING_MANAGE))],
)
async def acknowledge_signal(
    signal_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[EarlyWarningSignalResponse]:
    """Acknowledge a newly detected warning signal."""
    service = StudentSuccessService(db)
    sig = await service.acknowledge_signal(tenant_ctx.tenant_id, signal_id, current_user.id)
    return ApiResponse(data=EarlyWarningSignalResponse.model_validate(sig))


@student_success_router.post(
    "/signals/{signal_id}/dismiss",
    response_model=ApiResponse[EarlyWarningSignalResponse],
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_EARLY_WARNING_MANAGE))],
)
async def dismiss_signal(
    signal_id: UUID,
    payload: EarlyWarningSignalDismiss,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[EarlyWarningSignalResponse]:
    """Dismiss a warning signal with recorded reason (or false-positive flag)."""
    service = StudentSuccessService(db)
    sig = await service.dismiss_signal(
        tenant_ctx.tenant_id, signal_id, payload, current_user.id
    )
    return ApiResponse(data=EarlyWarningSignalResponse.model_validate(sig))


@student_success_router.post(
    "/signals/{signal_id}/resolve",
    response_model=ApiResponse[EarlyWarningSignalResponse],
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_EARLY_WARNING_MANAGE))],
)
async def resolve_signal(
    signal_id: UUID,
    payload: EarlyWarningSignalResolve,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[EarlyWarningSignalResponse]:
    """Resolve a warning signal after completed intervention."""
    service = StudentSuccessService(db)
    sig = await service.resolve_signal(
        tenant_ctx.tenant_id, signal_id, payload, current_user.id
    )
    return ApiResponse(data=EarlyWarningSignalResponse.model_validate(sig))


@student_success_router.post(
    "/signals/{signal_id}/link-case",
    response_model=ApiResponse[EarlyWarningSignalResponse],
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_EARLY_WARNING_MANAGE))],
)
async def link_signal_to_case(
    signal_id: UUID,
    payload: EarlyWarningSignalLinkCase,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[EarlyWarningSignalResponse]:
    """Link warning signal to an existing case or create a new case."""
    service = StudentSuccessService(db)
    sig = await service.link_signal_to_case(
        tenant_ctx.tenant_id, signal_id, payload, current_user.id
    )
    return ApiResponse(data=EarlyWarningSignalResponse.model_validate(sig))


# =============================================================================
# 6. INTERVENTIONS PLANNING & EXECUTION ENDPOINTS
# =============================================================================


@student_success_router.post(
    "/interventions",
    response_model=ApiResponse[InterventionPlanResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_INTERVENTION_MANAGE))],
)
async def create_intervention(
    payload: InterventionPlanCreate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[InterventionPlanResponse]:
    """Create a student intervention plan."""
    service = StudentSuccessService(db)
    plan = await service.create_intervention_plan(tenant_ctx.tenant_id, payload, current_user.id)
    return ApiResponse(data=InterventionPlanResponse.model_validate(plan))


@student_success_router.get(
    "/interventions",
    response_model=ApiResponse[list[InterventionPlanResponse]],
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_INTERVENTION_READ))],
)
async def list_interventions(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    student_id: UUID | None = None,
    case_id: UUID | None = None,
    status_val: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> ApiResponse[list[InterventionPlanResponse]]:
    """List student intervention plans."""
    service = StudentSuccessService(db)
    plans = await service.list_intervention_plans(
        tenant_id=tenant_ctx.tenant_id,
        student_id=student_id,
        case_id=case_id,
        status_val=status_val,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(data=[InterventionPlanResponse.model_validate(p) for p in plans])


@student_success_router.get(
    "/interventions/{intervention_id}",
    response_model=ApiResponse[InterventionPlanResponse],
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_INTERVENTION_READ))],
)
async def get_intervention(
    intervention_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
) -> ApiResponse[InterventionPlanResponse]:
    """Fetch an intervention plan with actions."""
    service = StudentSuccessService(db)
    plan = await service.get_intervention_plan(tenant_ctx.tenant_id, intervention_id)
    return ApiResponse(data=InterventionPlanResponse.model_validate(plan))


@student_success_router.patch(
    "/interventions/{intervention_id}",
    response_model=ApiResponse[InterventionPlanResponse],
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_INTERVENTION_MANAGE))],
)
async def update_intervention(
    intervention_id: UUID,
    payload: InterventionPlanUpdate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[InterventionPlanResponse]:
    """Update intervention progress, outcomes, and participation status."""
    service = StudentSuccessService(db)
    plan = await service.update_intervention_plan(
        tenant_ctx.tenant_id, intervention_id, payload, current_user.id
    )
    return ApiResponse(data=InterventionPlanResponse.model_validate(plan))


@student_success_router.post(
    "/interventions/{intervention_id}/actions",
    response_model=ApiResponse[InterventionActionResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_INTERVENTION_MANAGE))],
)
async def add_intervention_action(
    intervention_id: UUID,
    payload: InterventionActionCreate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
) -> ApiResponse[InterventionActionResponse]:
    """Add an action item to an intervention plan."""
    service = StudentSuccessService(db)
    act = await service.add_intervention_action(tenant_ctx.tenant_id, intervention_id, payload)
    return ApiResponse(data=InterventionActionResponse.model_validate(act))


@student_success_router.patch(
    "/intervention-actions/{action_id}",
    response_model=ApiResponse[InterventionActionResponse],
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_INTERVENTION_MANAGE))],
)
async def update_intervention_action(
    action_id: UUID,
    payload: InterventionActionUpdate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
) -> ApiResponse[InterventionActionResponse]:
    """Update progress or complete an intervention action."""
    service = StudentSuccessService(db)
    act = await service.update_intervention_action(tenant_ctx.tenant_id, action_id, payload)
    return ApiResponse(data=InterventionActionResponse.model_validate(act))


# =============================================================================
# 7. APPOINTMENTS & SCHEDULING ENDPOINTS
# =============================================================================


@student_success_router.post(
    "/appointments",
    response_model=ApiResponse[AdvisingAppointmentResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_APPOINTMENT_MANAGE))],
)
async def schedule_appointment(
    payload: AdvisingAppointmentRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[AdvisingAppointmentResponse]:
    """Schedule an advising appointment with conflict prevention."""
    service = StudentSuccessService(db)
    appt = await service.schedule_appointment(
        tenant_ctx.tenant_id, payload, current_user.id, is_student_request=False
    )
    return ApiResponse(data=AdvisingAppointmentResponse.model_validate(appt))


@student_success_router.get(
    "/appointments",
    response_model=ApiResponse[list[AdvisingAppointmentResponse]],
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_ADVISING_READ))],
)
async def list_appointments(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    advisor_id: UUID | None = None,
    student_id: UUID | None = None,
    status_val: str | None = Query(None, alias="status"),
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> ApiResponse[list[AdvisingAppointmentResponse]]:
    """List advising appointments."""
    service = StudentSuccessService(db)
    appts = await service.list_appointments(
        tenant_id=tenant_ctx.tenant_id,
        advisor_id=advisor_id,
        student_id=student_id,
        status_val=status_val,
        start_date=start_date,
        end_date=end_date,
        student_view=False,
    )
    return ApiResponse(data=[AdvisingAppointmentResponse.model_validate(a) for a in appts])


@student_success_router.patch(
    "/appointments/{appointment_id}",
    response_model=ApiResponse[AdvisingAppointmentResponse],
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_APPOINTMENT_MANAGE))],
)
async def update_appointment(
    appointment_id: UUID,
    payload: AdvisingAppointmentUpdate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[AdvisingAppointmentResponse]:
    """Reschedule, cancel, or record summary for an appointment."""
    service = StudentSuccessService(db)
    appt = await service.update_appointment(
        tenant_ctx.tenant_id, appointment_id, payload, current_user.id
    )
    return ApiResponse(data=AdvisingAppointmentResponse.model_validate(appt))


# =============================================================================
# 8. STUDENT SELF-SERVICE PORTAL ENDPOINTS
# =============================================================================


@student_success_router.get(
    "/self/overview",
    response_model=ApiResponse[StudentSelfOverviewResponse],
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_STUDENT_SELF_READ))],
)
async def get_student_self_overview(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[StudentSelfOverviewResponse]:
    """Permitted student advising portal overview (scrubs internal notes/risk parameters)."""
    service = StudentSuccessService(db)
    overview = await service.get_student_self_overview(tenant_ctx.tenant_id, current_user.id)
    return ApiResponse(data=overview)


@student_success_router.post(
    "/self/appointments",
    response_model=ApiResponse[AdvisingAppointmentResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_STUDENT_SELF_READ))],
)
async def student_request_appointment(
    payload: AdvisingAppointmentRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[AdvisingAppointmentResponse]:
    """Student request an appointment with their academic advisor."""
    service = StudentSuccessService(db)
    appt = await service.schedule_appointment(
        tenant_ctx.tenant_id, payload, current_user.id, is_student_request=True
    )
    return ApiResponse(data=AdvisingAppointmentResponse.model_validate(appt))


@student_success_router.post(
    "/self/action-progress",
    response_model=ApiResponse[AdvisingActionItemResponse],
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_STUDENT_SELF_READ))],
)
async def student_submit_action_progress(
    payload: StudentActionProgressSubmit,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[AdvisingActionItemResponse]:
    """Submit progress updates on a permitted action item."""
    service = StudentSuccessService(db)
    act = await service.submit_student_progress(tenant_ctx.tenant_id, current_user.id, payload)
    return ApiResponse(data=AdvisingActionItemResponse.model_validate(act))


# =============================================================================
# 9. REPORTING & ANALYTICS ENDPOINTS
# =============================================================================


@student_success_router.get(
    "/reports/overview",
    response_model=ApiResponse[StudentSuccessOverviewMetrics],
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_REPORTS_READ))],
)
async def get_reports_overview(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
) -> ApiResponse[StudentSuccessOverviewMetrics]:
    """Tenant-scoped aggregate student success metrics."""
    service = StudentSuccessService(db)
    metrics = await service.get_overview_metrics(tenant_ctx.tenant_id)
    return ApiResponse(data=metrics)


@student_success_router.get(
    "/reports/advisor-caseload",
    response_model=ApiResponse[list[AdvisorCaseloadSummaryItem]],
    dependencies=[Depends(require_permission(STUDENT_SUCCESS_REPORTS_READ))],
)
async def get_advisor_caseload_report(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
) -> ApiResponse[list[AdvisorCaseloadSummaryItem]]:
    """Caseload distribution per academic advisor."""
    service = StudentSuccessService(db)
    caseload = await service.get_advisor_caseload_report(tenant_ctx.tenant_id)
    return ApiResponse(data=caseload)
