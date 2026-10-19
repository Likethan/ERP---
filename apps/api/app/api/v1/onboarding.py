"""Tenant Onboarding, Readiness & Go-Live Orchestration Router for CampusOS (Step 35).

Exposes RESTful endpoints for:
- Initializing and retrieving institutional onboarding plans
- Executing guarded lifecycle state machine transitions
- Managing and updating readiness checklist items and waivers
- Evaluating readiness rules with explainable blocking conditions
- Running data migration schema validation, duplicate checks, and reconciliation
- Recording traceable User Acceptance Testing (UAT) executions and defects
- Submitting multi-role governance approvals with change invalidation
- Executing idempotent go-live launch steps and safe rollback
- Monitoring hypercare telemetry and completing operational handoffs
"""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_current_active_user, require_platform_admin
from app.core.exceptions import NotFoundException
from app.models.onboarding import (
    OnboardingApproval,
    OnboardingChecklistItem,
    OnboardingMigrationJob,
    OnboardingUATScenario,
    TenantOnboardingPlan,
)
from app.models.people import User
from app.schemas.onboarding import (
    ChecklistItemResponse,
    ChecklistItemUpdateRequest,
    GoLiveExecutionRequest,
    GoLiveExecutionStepResponse,
    HypercareHandoffRequest,
    HypercareStatusResponse,
    MigrationJobResponse,
    MigrationValidationRequest,
    OnboardingApprovalRequest,
    OnboardingApprovalResponse,
    OnboardingLifecycleTransitionRequest,
    OnboardingPlanCreateRequest,
    OnboardingPlanResponse,
    ReadinessEvaluationResponse,
    RollbackExecutionRequest,
    RollbackExecutionResponse,
    UATScenarioExecuteRequest,
    UATScenarioResponse,
)
from app.services.tenant_onboarding_service import TenantOnboardingService

router = APIRouter(prefix="/onboarding", tags=["Tenant Onboarding & Go-Live"])


# =============================================================================
# 1. ONBOARDING PLAN & LIFECYCLE
# =============================================================================


@router.post("/plans", response_model=OnboardingPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_or_get_onboarding_plan(
    payload: OnboardingPlanCreateRequest,
    current_user: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> OnboardingPlanResponse:
    """Initialize or fetch an institutional onboarding plan with standard checklist and UAT."""
    plan = await TenantOnboardingService.get_or_create_plan(
        db=db,
        tenant_id=payload.tenant_id,
        assigned_lead_email=payload.assigned_lead_email,
        target_go_live_date=payload.target_go_live_date,
    )
    return OnboardingPlanResponse.model_validate(plan)


@router.get("/plans/{institution_id}", response_model=OnboardingPlanResponse)
async def get_onboarding_plan(
    institution_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> OnboardingPlanResponse:
    """Retrieve onboarding plan and operational state for an institution."""
    plan = await TenantOnboardingService.get_plan_by_tenant_id(db, institution_id)
    return OnboardingPlanResponse.model_validate(plan)


@router.post("/plans/{institution_id}/transitions", response_model=OnboardingPlanResponse)
async def transition_onboarding_lifecycle(
    institution_id: UUID,
    payload: OnboardingLifecycleTransitionRequest,
    current_user: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> OnboardingPlanResponse:
    """Execute a guarded state transition in the institutional onboarding lifecycle."""
    plan = await TenantOnboardingService.get_plan_by_tenant_id(db, institution_id)
    updated = await TenantOnboardingService.transition_state(
        db=db,
        plan_id=plan.id,
        payload=payload,
        actor_id=current_user.id,
        actor_email=current_user.email,
    )
    return OnboardingPlanResponse.model_validate(updated)


# =============================================================================
# 2. READINESS CHECKLIST & EVALUATOR
# =============================================================================


@router.get("/plans/{institution_id}/checklist", response_model=list[ChecklistItemResponse])
async def list_checklist_items(
    institution_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    category: str | None = Query(None),
) -> list[ChecklistItemResponse]:
    """List all readiness checklist criteria for an institution."""
    plan = await TenantOnboardingService.get_plan_by_tenant_id(db, institution_id)
    stmt = select(OnboardingChecklistItem).where(OnboardingChecklistItem.plan_id == plan.id)
    if category:
        stmt = stmt.where(OnboardingChecklistItem.category == category.upper())
    stmt = stmt.order_by(OnboardingChecklistItem.item_code)
    result = await db.execute(stmt)
    return [ChecklistItemResponse.model_validate(item) for item in result.scalars().all()]


@router.patch("/plans/{institution_id}/checklist/{item_code}", response_model=ChecklistItemResponse)
async def update_checklist_item(
    institution_id: UUID,
    item_code: str,
    payload: ChecklistItemUpdateRequest,
    current_user: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ChecklistItemResponse:
    """Update checklist verification status, documentary evidence, or authorized waiver."""
    plan = await TenantOnboardingService.get_plan_by_tenant_id(db, institution_id)
    updated = await TenantOnboardingService.update_checklist_item(
        db=db,
        plan_id=plan.id,
        item_code=item_code,
        payload=payload,
        actor_email=current_user.email,
    )
    return ChecklistItemResponse.model_validate(updated)


@router.get("/plans/{institution_id}/readiness", response_model=ReadinessEvaluationResponse)
async def evaluate_readiness(
    institution_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ReadinessEvaluationResponse:
    """Calculate deterministic go-live readiness rules and return an explainable report."""
    plan = await TenantOnboardingService.get_plan_by_tenant_id(db, institution_id)
    return await TenantOnboardingService.evaluate_readiness(db, plan.id)


# =============================================================================
# 3. DATA MIGRATION & RECONCILIATION
# =============================================================================


@router.post("/plans/{institution_id}/migration/validate", response_model=MigrationJobResponse)
async def validate_migration(
    institution_id: UUID,
    payload: MigrationValidationRequest,
    current_user: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> MigrationJobResponse:
    """Validate data file structure, detect duplicates, and execute bounded reconciliation dry-run."""
    plan = await TenantOnboardingService.get_plan_by_tenant_id(db, institution_id)
    job = await TenantOnboardingService.validate_and_reconcile_migration(
        db=db,
        plan_id=plan.id,
        payload=payload,
        actor_id=current_user.id,
    )
    return MigrationJobResponse.model_validate(job)


@router.get("/plans/{institution_id}/migration", response_model=list[MigrationJobResponse])
async def list_migration_jobs(
    institution_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[MigrationJobResponse]:
    """Retrieve history and reconciliation metrics for all data migration jobs."""
    plan = await TenantOnboardingService.get_plan_by_tenant_id(db, institution_id)
    stmt = (
        select(OnboardingMigrationJob)
        .where(OnboardingMigrationJob.plan_id == plan.id)
        .order_by(desc(OnboardingMigrationJob.created_at))
    )
    result = await db.execute(stmt)
    return [MigrationJobResponse.model_validate(job) for job in result.scalars().all()]


# =============================================================================
# 4. USER ACCEPTANCE TESTING (UAT)
# =============================================================================


@router.get("/plans/{institution_id}/uat", response_model=list[UATScenarioResponse])
async def list_uat_scenarios(
    institution_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[UATScenarioResponse]:
    """List User Acceptance Testing scenarios, assigned testers, and verification status."""
    plan = await TenantOnboardingService.get_plan_by_tenant_id(db, institution_id)
    stmt = (
        select(OnboardingUATScenario)
        .where(OnboardingUATScenario.plan_id == plan.id)
        .order_by(OnboardingUATScenario.scenario_code)
    )
    result = await db.execute(stmt)
    return [UATScenarioResponse.model_validate(sc) for sc in result.scalars().all()]


@router.post("/plans/{institution_id}/uat/{scenario_code}/execute", response_model=UATScenarioResponse)
async def execute_uat_scenario(
    institution_id: UUID,
    scenario_code: str,
    payload: UATScenarioExecuteRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> UATScenarioResponse:
    """Record UAT test execution, defect details, and institutional sign-off."""
    plan = await TenantOnboardingService.get_plan_by_tenant_id(db, institution_id)
    sc = await TenantOnboardingService.record_uat_execution(
        db=db,
        plan_id=plan.id,
        scenario_code=scenario_code,
        payload=payload,
    )
    return UATScenarioResponse.model_validate(sc)


# =============================================================================
# 5. GO-LIVE APPROVALS & GOVERNANCE
# =============================================================================


@router.get("/plans/{institution_id}/approvals", response_model=list[OnboardingApprovalResponse])
async def list_approvals(
    institution_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[OnboardingApprovalResponse]:
    """Retrieve multi-role go-live approval matrix and sign-off status."""
    plan = await TenantOnboardingService.get_plan_by_tenant_id(db, institution_id)
    stmt = (
        select(OnboardingApproval)
        .where(OnboardingApproval.plan_id == plan.id)
        .order_by(OnboardingApproval.role)
    )
    result = await db.execute(stmt)
    return [OnboardingApprovalResponse.model_validate(app) for app in result.scalars().all()]


@router.post("/plans/{institution_id}/approvals", response_model=OnboardingApprovalResponse)
async def submit_approval(
    institution_id: UUID,
    payload: OnboardingApprovalRequest,
    current_user: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> OnboardingApprovalResponse:
    """Submit an accountable go-live approval or rejection."""
    plan = await TenantOnboardingService.get_plan_by_tenant_id(db, institution_id)
    appr = await TenantOnboardingService.submit_approval(
        db=db,
        plan_id=plan.id,
        payload=payload,
        approver_id=current_user.id,
        approver_email=current_user.email,
    )
    return OnboardingApprovalResponse.model_validate(appr)


# =============================================================================
# 6. GO-LIVE EXECUTION & ROLLBACK
# =============================================================================


@router.get("/plans/{institution_id}/golive/plan")
async def get_golive_execution_plan(
    institution_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[dict[str, Any]]:
    """Retrieve the ordered 10-step launch execution sequence."""
    plan = await TenantOnboardingService.get_plan_by_tenant_id(db, institution_id)
    return [
        {"step_order": order, "step_name": name, "description": desc}
        for order, name, desc in TenantOnboardingService.ORDERED_LAUNCH_STEPS
    ]


@router.post("/plans/{institution_id}/golive/execute", response_model=list[GoLiveExecutionStepResponse])
async def execute_golive(
    institution_id: UUID,
    payload: GoLiveExecutionRequest,
    current_user: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[GoLiveExecutionStepResponse]:
    """Execute ordered launch sequence with idempotency protection and dry-run safety."""
    plan = await TenantOnboardingService.get_plan_by_tenant_id(db, institution_id)
    steps = await TenantOnboardingService.execute_golive_plan(
        db=db,
        plan_id=plan.id,
        is_dry_run=payload.is_dry_run,
        idempotency_key=payload.idempotency_key,
        actor_id=current_user.id,
    )
    return [GoLiveExecutionStepResponse.model_validate(s) for s in steps]


@router.post("/plans/{institution_id}/rollback", response_model=RollbackExecutionResponse)
async def execute_rollback(
    institution_id: UUID,
    payload: RollbackExecutionRequest,
    current_user: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> RollbackExecutionResponse:
    """Safely execute an authorized rollback, suspending access while preserving data."""
    plan = await TenantOnboardingService.get_plan_by_tenant_id(db, institution_id)
    return await TenantOnboardingService.execute_rollback(
        db=db,
        plan_id=plan.id,
        payload=payload,
        actor_id=current_user.id,
    )


# =============================================================================
# 7. HYPERCARE MONITORING & OPERATIONAL HANDOFF
# =============================================================================


@router.get("/plans/{institution_id}/hypercare", response_model=HypercareStatusResponse)
async def get_hypercare_status(
    institution_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> HypercareStatusResponse:
    """Retrieve active hypercare operational telemetry, error counts, and exit criteria."""
    plan = await TenantOnboardingService.get_plan_by_tenant_id(db, institution_id)
    rec = await TenantOnboardingService.get_hypercare_status(db, plan.id)
    return HypercareStatusResponse.model_validate(rec)


@router.post("/plans/{institution_id}/hypercare/handoff", response_model=HypercareStatusResponse)
async def complete_hypercare_handoff(
    institution_id: UUID,
    payload: HypercareHandoffRequest,
    current_user: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> HypercareStatusResponse:
    """Formally transition an institution from hypercare to steady-state operations."""
    plan = await TenantOnboardingService.get_plan_by_tenant_id(db, institution_id)
    rec = await TenantOnboardingService.complete_hypercare_handoff(
        db=db,
        plan_id=plan.id,
        signoff_by=payload.signoff_by,
        notes=payload.notes,
    )
    return HypercareStatusResponse.model_validate(rec)
