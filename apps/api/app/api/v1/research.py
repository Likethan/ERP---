"""Enterprise Institutional Research, Innovation, Grants & IP Management API Router (Step 44)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_current_user, get_tenant_context, require_permission
from app.core.permissions import (
    RESEARCH_ANALYTICS_READ_DOT,
    RESEARCH_AWARDS_MANAGE_DOT,
    RESEARCH_BUDGETS_MANAGE_DOT,
    RESEARCH_ETHICS_REVIEW_DOT,
    RESEARCH_GRANTS_APPLY_DOT,
    RESEARCH_GRANTS_APPROVE_DOT,
    RESEARCH_IP_MANAGE_DOT,
    RESEARCH_OUTPUTS_MANAGE_DOT,
    RESEARCH_OUTPUTS_VERIFY_DOT,
    RESEARCH_PROJECTS_MANAGE_DOT,
    RESEARCH_PROJECTS_READ_DOT,
    RESEARCH_PROJECTS_TRANSITION_DOT,
)
from app.core.tenant import TenantContext
from app.models.people import User
from app.models.research import (
    ResearchExternalSubmissionStatus,
    ResearchGrantInternalReviewStatus,
    ResearchOpportunityStatus,
    ResearchProjectStatus,
)
from app.schemas.common import ApiResponse
from app.schemas.research import (
    ResearchAgreementAmendmentCreate,
    ResearchAnalyticsSummaryResponse,
    ResearchBudgetPlanCreate,
    ResearchBudgetPlanResponse,
    ResearchBudgetRevisionRequest,
    ResearchDeadlineSweepResponse,
    ResearcherWorkloadResponse,
    ResearchEthicsApprovalCreate,
    ResearchEthicsApprovalDecision,
    ResearchEthicsApprovalResponse,
    ResearchExpressionOfInterestCreate,
    ResearchFacilityReferenceCreate,
    ResearchFacilityReferenceResponse,
    ResearchFinancialSummaryResponse,
    ResearchFundingOpportunityCreate,
    ResearchFundingOpportunityResponse,
    ResearchFundingOpportunityUpdate,
    ResearchGrantApplicationCreate,
    ResearchGrantApplicationResponse,
    ResearchGrantApplicationUpdate,
    ResearchGrantAwardCreate,
    ResearchGrantAwardResponse,
    ResearchGrantExternalSubmissionConfirm,
    ResearchGrantInternalReview,
    ResearchInventionDisclosureCreate,
    ResearchInventionDisclosureResponse,
    ResearchInventionDisclosureUpdate,
    ResearchMilestoneCreate,
    ResearchMilestoneResponse,
    ResearchMilestoneUpdate,
    ResearchMilestoneVerify,
    ResearchOpportunitySaveRequest,
    ResearchOutputCreate,
    ResearchOutputResponse,
    ResearchOutputVerify,
    ResearchProjectCreate,
    ResearchProjectDetailResponse,
    ResearchProjectHealthReport,
    ResearchProjectResponse,
    ResearchProjectRiskCreate,
    ResearchProjectRiskResponse,
    ResearchProjectRiskUpdate,
    ResearchProjectStatusHistoryResponse,
    ResearchProjectTransition,
    ResearchProjectUpdate,
    ResearchSponsorDecisionRecord,
    ResearchSponsoredAgreementCreate,
    ResearchTeamMemberCreate,
    ResearchTeamMemberResponse,
    ResearchTeamMemberUpdate,
)
from app.services.research_service import ResearchService

research_router = APIRouter(prefix="/research", tags=["Enterprise Research & Innovation"])


# =============================================================================
# 1. RESEARCH PROJECT REGISTRY & LIFECYCLE
# =============================================================================


@research_router.get(
    "/projects",
    response_model=ApiResponse[list[ResearchProjectResponse]],
    summary="List Institutional Research Projects",
)
async def list_projects(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status: ResearchProjectStatus | None = None,
    category: str | None = None,
    domain: str | None = None,
    department_id: UUID | None = None,
    campus_id: UUID | None = None,
    search: str | None = None,
    pi_id: UUID | None = None,
    user_id: UUID | None = None,
    limit: int = 50,
    offset: int = 0,
):
    projects, _ = await ResearchService.list_projects(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        status=status,
        category=category,
        domain=domain,
        department_id=department_id,
        campus_id=campus_id,
        search=search,
        pi_id=pi_id,
        user_id=user_id,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(data=[ResearchProjectResponse.model_validate(p) for p in projects])


@research_router.post(
    "/projects",
    response_model=ApiResponse[ResearchProjectResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Research Project",
)
async def create_project(
    payload: ResearchProjectCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    project = await ResearchService.create_project(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        data=payload,
        current_user_id=current_user.id,
    )
    return ApiResponse(data=ResearchProjectResponse.model_validate(project))


@research_router.get(
    "/projects/{project_id}",
    response_model=ApiResponse[ResearchProjectResponse],
    summary="Get Research Project by ID",
)
async def get_project(
    project_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    project = await ResearchService.get_project(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        project_id=project_id,
    )
    return ApiResponse(data=ResearchProjectResponse.model_validate(project))


@research_router.get(
    "/projects/{project_id}/health",
    response_model=ApiResponse[ResearchProjectHealthReport],
    summary="Get Explainable Research Project Health Diagnosis",
)
async def get_project_health(
    project_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    health = await ResearchService.get_project_health(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        project_id=project_id,
    )
    return ApiResponse(data=health)


@research_router.get(
    "/projects/{project_id}/details",
    response_model=ApiResponse[ResearchProjectDetailResponse],
    summary="Get 360-degree Unified Research Project Details",
)
async def get_project_details(
    project_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    details = await ResearchService.get_project_details(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        project_id=project_id,
    )
    return ApiResponse(data=details)


@research_router.get(
    "/projects/{project_id}/milestones",
    response_model=ApiResponse[list[ResearchMilestoneResponse]],
    include_in_schema=False,
)
async def list_project_milestones_alias(
    project_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    milestones = await ResearchService.list_milestones(db=db, tenant_id=tenant_ctx.tenant_id, project_id=project_id)
    return ApiResponse(data=[ResearchMilestoneResponse.model_validate(m) for m in milestones])


@research_router.get(
    "/projects/{project_id}/ethics-approvals",
    response_model=ApiResponse[list[ResearchEthicsApprovalResponse]],
    include_in_schema=False,
)
async def list_project_ethics_alias(
    project_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    approvals = await ResearchService.list_ethics_approvals(db=db, tenant_id=tenant_ctx.tenant_id, project_id=project_id)
    return ApiResponse(data=[ResearchEthicsApprovalResponse.model_validate(a) for a in approvals])


@research_router.get(
    "/projects/{project_id}/risks",
    response_model=ApiResponse[list[ResearchProjectRiskResponse]],
    include_in_schema=False,
)
async def list_project_risks_alias(
    project_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    risks = await ResearchService.list_project_risks(db=db, tenant_id=tenant_ctx.tenant_id, project_id=project_id)
    return ApiResponse(data=[ResearchProjectRiskResponse.model_validate(r) for r in risks])


@research_router.patch(
    "/projects/{project_id}",
    response_model=ApiResponse[ResearchProjectResponse],
    summary="Update Research Project",
)
async def update_project(
    project_id: UUID,
    payload: ResearchProjectUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    project = await ResearchService.update_project(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        project_id=project_id,
        data=payload,
        current_user_id=current_user.id,
    )
    return ApiResponse(data=ResearchProjectResponse.model_validate(project))


@research_router.post(
    "/projects/{project_id}/transition",
    response_model=ApiResponse[ResearchProjectResponse],
    summary="Transition Research Project Status",
)
async def transition_project(
    project_id: UUID,
    payload: ResearchProjectTransition,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_TRANSITION_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    project = await ResearchService.transition_project_status(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        project_id=project_id,
        data=payload,
        current_user_id=current_user.id,
    )
    return ApiResponse(data=ResearchProjectResponse.model_validate(project))


@research_router.get(
    "/projects/{project_id}/status-history",
    response_model=ApiResponse[list[ResearchProjectStatusHistoryResponse]],
    summary="Get Research Project Lifecycle History",
)
async def get_status_history(
    project_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    history = await ResearchService.list_project_status_history(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        project_id=project_id,
    )
    return ApiResponse(data=[ResearchProjectStatusHistoryResponse.model_validate(h) for h in history])


# =============================================================================
# 2. RESEARCH TEAM MEMBERS
# =============================================================================


@research_router.get(
    "/projects/{project_id}/team",
    response_model=ApiResponse[list[ResearchTeamMemberResponse]],
    summary="List Research Project Team Members",
)
async def list_team_members(
    project_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    members = await ResearchService.list_team_members(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        project_id=project_id,
    )
    return ApiResponse(data=[ResearchTeamMemberResponse.model_validate(m) for m in members])


@research_router.post(
    "/projects/{project_id}/team",
    response_model=ApiResponse[ResearchTeamMemberResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Add Team Member to Research Project",
)
async def add_team_member(
    project_id: UUID,
    payload: ResearchTeamMemberCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    member = await ResearchService.add_team_member(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        project_id=project_id,
        data=payload,
        current_user_id=current_user.id,
    )
    return ApiResponse(data=ResearchTeamMemberResponse.model_validate(member))


@research_router.patch(
    "/team/{member_id}",
    response_model=ApiResponse[ResearchTeamMemberResponse],
    summary="Update Research Team Member Role/Scope",
)
async def update_team_member(
    member_id: UUID,
    payload: ResearchTeamMemberUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    member = await ResearchService.update_team_member(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        member_id=member_id,
        data=payload,
        current_user_id=current_user.id,
    )
    return ApiResponse(data=ResearchTeamMemberResponse.model_validate(member))


@research_router.delete(
    "/team/{member_id}",
    response_model=ApiResponse[ResearchTeamMemberResponse],
    summary="Deactivate Research Team Member (Preserving Attribution)",
)
async def remove_team_member(
    member_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    member = await ResearchService.remove_team_member(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        member_id=member_id,
        current_user_id=current_user.id,
    )
    return ApiResponse(data=ResearchTeamMemberResponse.model_validate(member))


@research_router.get(
    "/team/users/{user_id}/workload",
    response_model=ApiResponse[ResearcherWorkloadResponse],
    summary="Get Researcher Project Portfolio and Workload Allocation",
)
async def get_researcher_workload(
    user_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    workload = await ResearchService.get_researcher_workload(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        user_id=user_id,
    )
    return ApiResponse(data=workload)


@research_router.get(
    "/team/my-projects",
    response_model=ApiResponse[ResearcherWorkloadResponse],
    summary="Get Current User's Active Research Projects & Workload",
)
async def get_my_projects(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    workload = await ResearchService.get_researcher_workload(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        user_id=current_user.id,
    )
    return ApiResponse(data=workload)



# =============================================================================
# 3. RESEARCH FUNDING OPPORTUNITIES
# =============================================================================


@research_router.get(
    "/opportunities",
    response_model=ApiResponse[list[ResearchFundingOpportunityResponse]],
    summary="List Research Funding Opportunities",
)
async def list_opportunities(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status: ResearchOpportunityStatus | None = None,
    category: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    opps, _ = await ResearchService.list_funding_opportunities(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        status=status,
        category=category,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(data=[ResearchFundingOpportunityResponse.model_validate(o) for o in opps])


@research_router.post(
    "/opportunities",
    response_model=ApiResponse[ResearchFundingOpportunityResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Funding Opportunity",
)
async def create_opportunity(
    payload: ResearchFundingOpportunityCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    opp = await ResearchService.create_funding_opportunity(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        data=payload,
        current_user_id=current_user.id,
    )
    return ApiResponse(data=ResearchFundingOpportunityResponse.model_validate(opp))


@research_router.get(
    "/opportunities/{opportunity_id}",
    response_model=ApiResponse[ResearchFundingOpportunityResponse],
    summary="Get Funding Opportunity by ID",
)
async def get_opportunity(
    opportunity_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    opp = await ResearchService.get_funding_opportunity(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        opportunity_id=opportunity_id,
    )
    return ApiResponse(data=ResearchFundingOpportunityResponse.model_validate(opp))


@research_router.patch(
    "/opportunities/{opportunity_id}",
    response_model=ApiResponse[ResearchFundingOpportunityResponse],
    summary="Update Funding Opportunity",
)
async def update_opportunity(
    opportunity_id: UUID,
    payload: ResearchFundingOpportunityUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    opp = await ResearchService.update_funding_opportunity(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        opportunity_id=opportunity_id,
        data=payload,
        current_user_id=current_user.id,
    )
    return ApiResponse(data=ResearchFundingOpportunityResponse.model_validate(opp))


@research_router.post(
    "/opportunities/{opportunity_id}/save",
    response_model=ApiResponse[ResearchFundingOpportunityResponse],
    summary="Save or Bookmark Funding Opportunity",
)
async def save_opportunity(
    opportunity_id: UUID,
    payload: ResearchOpportunitySaveRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    opp = await ResearchService.save_funding_opportunity(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        opportunity_id=opportunity_id,
        user_id=current_user.id,
        save=payload.saved,
    )
    return ApiResponse(data=ResearchFundingOpportunityResponse.model_validate(opp))


@research_router.post(
    "/opportunities/{opportunity_id}/eoi",
    response_model=ApiResponse[ResearchFundingOpportunityResponse],
    summary="Record Expression of Interest in Funding Opportunity",
)
async def record_expression_of_interest(
    opportunity_id: UUID,
    payload: ResearchExpressionOfInterestCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_GRANTS_APPLY_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    opp = await ResearchService.record_expression_of_interest(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        opportunity_id=opportunity_id,
        data=payload,
        current_user_id=current_user.id,
    )
    return ApiResponse(data=ResearchFundingOpportunityResponse.model_validate(opp))



# =============================================================================
# 4. GRANT APPLICATIONS & INTERNAL REVIEW
# =============================================================================


@research_router.get(
    "/grants/applications",
    response_model=ApiResponse[list[ResearchGrantApplicationResponse]],
    summary="List Grant Applications",
)
async def list_grant_applications(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    project_id: UUID | None = None,
    internal_status: ResearchGrantInternalReviewStatus | None = None,
    external_status: ResearchExternalSubmissionStatus | None = None,
    limit: int = 50,
    offset: int = 0,
):
    apps, _ = await ResearchService.list_grant_applications(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        project_id=project_id,
        internal_status=internal_status,
        external_status=external_status,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(data=[ResearchGrantApplicationResponse.model_validate(a) for a in apps])


@research_router.post(
    "/grants/applications",
    response_model=ApiResponse[ResearchGrantApplicationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Submit Grant Application Draft",
)
async def create_grant_application(
    payload: ResearchGrantApplicationCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_GRANTS_APPLY_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    app = await ResearchService.create_grant_application(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        data=payload,
        current_user_id=current_user.id,
    )
    return ApiResponse(data=ResearchGrantApplicationResponse.model_validate(app))


@research_router.get(
    "/grants/applications/{application_id}",
    response_model=ApiResponse[ResearchGrantApplicationResponse],
    summary="Get Grant Application by ID",
)
async def get_grant_application(
    application_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    app = await ResearchService.get_grant_application(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        application_id=application_id,
    )
    return ApiResponse(data=ResearchGrantApplicationResponse.model_validate(app))


@research_router.patch(
    "/grants/applications/{application_id}",
    response_model=ApiResponse[ResearchGrantApplicationResponse],
    summary="Update Grant Application Draft",
)
async def update_grant_application(
    application_id: UUID,
    payload: ResearchGrantApplicationUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_GRANTS_APPLY_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    app = await ResearchService.update_grant_application(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        application_id=application_id,
        data=payload,
        current_user_id=current_user.id,
    )
    return ApiResponse(data=ResearchGrantApplicationResponse.model_validate(app))


@research_router.post(
    "/grants/applications/{application_id}/review",
    response_model=ApiResponse[ResearchGrantApplicationResponse],
    summary="Record Internal Review Decision on Grant Application",
)
async def review_grant_application(
    application_id: UUID,
    payload: ResearchGrantInternalReview,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_GRANTS_APPROVE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    app = await ResearchService.review_grant_application(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        application_id=application_id,
        data=payload,
        current_user_id=current_user.id,
    )
    return ApiResponse(data=ResearchGrantApplicationResponse.model_validate(app))


@research_router.post(
    "/grants/applications/{application_id}/confirm-submission",
    response_model=ApiResponse[ResearchGrantApplicationResponse],
    summary="Confirm External Grant Agency Submission",
)
async def confirm_external_submission(
    application_id: UUID,
    payload: ResearchGrantExternalSubmissionConfirm,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_GRANTS_APPLY_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    app = await ResearchService.confirm_external_submission(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        application_id=application_id,
        data=payload,
        current_user_id=current_user.id,
    )
    return ApiResponse(data=ResearchGrantApplicationResponse.model_validate(app))


@research_router.post(
    "/grants/applications/{application_id}/sponsor-decision",
    response_model=ApiResponse[ResearchGrantApplicationResponse],
    summary="Record External Sponsor Decision and Award Details",
)
async def record_sponsor_decision(
    application_id: UUID,
    payload: ResearchSponsorDecisionRecord,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_GRANTS_APPROVE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    app = await ResearchService.record_sponsor_decision(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        application_id=application_id,
        data=payload,
        current_user_id=current_user.id,
    )
    return ApiResponse(data=ResearchGrantApplicationResponse.model_validate(app))


@research_router.get(
    "/grant-applications",
    response_model=ApiResponse[list[ResearchGrantApplicationResponse]],
    include_in_schema=False,
)
async def list_grant_applications_alias(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    project_id: UUID | None = None,
    internal_status: ResearchGrantInternalReviewStatus | None = None,
    external_status: ResearchExternalSubmissionStatus | None = None,
    limit: int = 50,
    offset: int = 0,
):
    return await list_grant_applications(
        tenant_ctx=tenant_ctx,
        current_user=current_user,
        db=db,
        project_id=project_id,
        internal_status=internal_status,
        external_status=external_status,
        limit=limit,
        offset=offset,
    )


# =============================================================================
# 5. GRANT AWARDS & SPONSORED RESEARCH AGREEMENTS
# =============================================================================


@research_router.get(
    "/agreements",
    response_model=ApiResponse[list[ResearchGrantAwardResponse]],
    summary="List Sponsored Research Agreements & Grant Awards",
)
async def list_sponsored_agreements(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    project_id: UUID | None = None,
    limit: int = 50,
    offset: int = 0,
):
    awards, _ = await ResearchService.list_grant_awards(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        project_id=project_id,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(data=[ResearchGrantAwardResponse.model_validate(a) for a in awards])


@research_router.post(
    "/agreements",
    response_model=ApiResponse[ResearchGrantAwardResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Sponsored Research Agreement",
)
async def create_sponsored_agreement(
    payload: ResearchSponsoredAgreementCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_AWARDS_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    award = await ResearchService.create_sponsored_agreement(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        data=payload,
        current_user_id=current_user.id,
    )
    return ApiResponse(data=ResearchGrantAwardResponse.model_validate(award))


@research_router.post(
    "/agreements/{award_id}/amendments",
    response_model=ApiResponse[ResearchGrantAwardResponse],
    summary="Record Sponsored Research Agreement Amendment or Renewal",
)
async def record_agreement_amendment(
    award_id: UUID,
    payload: ResearchAgreementAmendmentCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_AWARDS_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    award = await ResearchService.record_agreement_amendment(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        award_id=award_id,
        data=payload,
        current_user_id=current_user.id,
    )
    return ApiResponse(data=ResearchGrantAwardResponse.model_validate(award))



@research_router.get(
    "/awards",
    response_model=ApiResponse[list[ResearchGrantAwardResponse]],
    summary="List Research Grant Awards",
)
async def list_awards(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    project_id: UUID | None = None,
    limit: int = 50,
    offset: int = 0,
):
    awards, _ = await ResearchService.list_grant_awards(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        project_id=project_id,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(data=[ResearchGrantAwardResponse.model_validate(a) for a in awards])


@research_router.post(
    "/awards",
    response_model=ApiResponse[ResearchGrantAwardResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register Research Grant Award",
)
async def create_award(
    payload: ResearchGrantAwardCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_AWARDS_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    award = await ResearchService.create_grant_award(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        data=payload,
        current_user_id=current_user.id,
    )
    return ApiResponse(data=ResearchGrantAwardResponse.model_validate(award))


@research_router.get(
    "/awards/{award_id}",
    response_model=ApiResponse[ResearchGrantAwardResponse],
    summary="Get Grant Award by ID",
)
async def get_award(
    award_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    award = await ResearchService.get_grant_award(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        award_id=award_id,
    )
    return ApiResponse(data=ResearchGrantAwardResponse.model_validate(award))


@research_router.post(
    "/awards/{award_id}/reconcile",
    response_model=ApiResponse[ResearchGrantAwardResponse],
    summary="Reconcile Grant Award Balances with Financial Ledger",
)
async def reconcile_award(
    award_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_AWARDS_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    award = await ResearchService.reconcile_award_expenditure(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        award_id=award_id,
    )
    return ApiResponse(data=ResearchGrantAwardResponse.model_validate(award))


# =============================================================================
# 6. RESEARCH BUDGET PLANNING & REVISIONS
# =============================================================================


@research_router.get(
    "/budgets/projects/{project_id}",
    response_model=ApiResponse[list[ResearchBudgetPlanResponse]],
    summary="List Budget Plans for Project",
)
async def list_budget_plans(
    project_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    award_id: UUID | None = None,
):
    plans = await ResearchService.list_budget_plans(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        project_id=project_id,
        award_id=award_id,
    )
    return ApiResponse(data=[ResearchBudgetPlanResponse.model_validate(p) for p in plans])


@research_router.get(
    "/budgets",
    response_model=ApiResponse[list[ResearchBudgetPlanResponse]],
    summary="List Budget Plans Across Projects",
)
async def list_all_budget_plans(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    project_id: UUID | None = None,
    award_id: UUID | None = None,
):
    plans = await ResearchService.list_budget_plans(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        project_id=project_id,
        award_id=award_id,
    )
    return ApiResponse(data=[ResearchBudgetPlanResponse.model_validate(p) for p in plans])


@research_router.post(
    "/budgets",
    response_model=ApiResponse[ResearchBudgetPlanResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Itemized Research Budget Allocation",
)
async def create_budget_plan(
    payload: ResearchBudgetPlanCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_BUDGETS_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    plan = await ResearchService.create_budget_plan(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        data=payload,
        current_user_id=current_user.id,
    )
    return ApiResponse(data=ResearchBudgetPlanResponse.model_validate(plan))


@research_router.post(
    "/budgets/{plan_id}/revise",
    response_model=ApiResponse[ResearchBudgetPlanResponse],
    summary="Conduct Audited Research Budget Revision",
)
async def revise_budget_plan(
    plan_id: UUID,
    payload: ResearchBudgetRevisionRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_BUDGETS_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    plan = await ResearchService.revise_budget_plan(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        plan_id=plan_id,
        data=payload,
        current_user_id=current_user.id,
    )
    return ApiResponse(data=ResearchBudgetPlanResponse.model_validate(plan))


@research_router.get(
    "/budgets/projects/{project_id}/financial-summary",
    response_model=ApiResponse[ResearchFinancialSummaryResponse],
    summary="Get Reconciled Project Financial Summary and Health",
)
async def get_project_financial_summary(
    project_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    summary = await ResearchService.get_project_financial_summary(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        project_id=project_id,
    )
    return ApiResponse(data=summary)



# =============================================================================
# 7. RESEARCH MILESTONES & DELIVERABLES
# =============================================================================


@research_router.get(
    "/milestones/projects/{project_id}",
    response_model=ApiResponse[list[ResearchMilestoneResponse]],
    summary="List Milestones for Research Project",
)
async def list_milestones(
    project_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    milestones = await ResearchService.list_milestones(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        project_id=project_id,
    )
    return ApiResponse(data=[ResearchMilestoneResponse.model_validate(m) for m in milestones])


@research_router.get(
    "/milestones",
    response_model=ApiResponse[list[ResearchMilestoneResponse]],
    summary="List Milestones Across Portfolio",
)
async def list_all_milestones(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    project_id: UUID | None = None,
):
    milestones = await ResearchService.list_milestones(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        project_id=project_id,
    )
    return ApiResponse(data=[ResearchMilestoneResponse.model_validate(m) for m in milestones])


@research_router.post(
    "/milestones",
    response_model=ApiResponse[ResearchMilestoneResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Research Milestone",
)
async def create_milestone(
    payload: ResearchMilestoneCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    milestone = await ResearchService.create_milestone(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        data=payload,
        current_user_id=current_user.id,
    )
    return ApiResponse(data=ResearchMilestoneResponse.model_validate(milestone))


@research_router.patch(
    "/milestones/{milestone_id}",
    response_model=ApiResponse[ResearchMilestoneResponse],
    summary="Update Milestone Progress and Completion",
)
async def update_milestone(
    milestone_id: UUID,
    payload: ResearchMilestoneUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    milestone = await ResearchService.update_milestone(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        milestone_id=milestone_id,
        data=payload,
        current_user_id=current_user.id,
    )
    return ApiResponse(data=ResearchMilestoneResponse.model_validate(milestone))


@research_router.post(
    "/milestones/{milestone_id}/verify",
    response_model=ApiResponse[ResearchMilestoneResponse],
    summary="Perform Independent Milestone Acceptance Review",
)
async def verify_milestone(
    milestone_id: UUID,
    payload: ResearchMilestoneVerify,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_TRANSITION_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    milestone = await ResearchService.verify_milestone(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        milestone_id=milestone_id,
        data=payload,
        current_user_id=current_user.id,
    )
    return ApiResponse(data=ResearchMilestoneResponse.model_validate(milestone))


# =============================================================================
# 8. ETHICS & COMPLIANCE APPROVALS
# =============================================================================


@research_router.get(
    "/ethics/projects/{project_id}",
    response_model=ApiResponse[list[ResearchEthicsApprovalResponse]],
    summary="List Ethics Approvals for Project",
)
async def list_ethics_approvals(
    project_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    approvals = await ResearchService.list_ethics_approvals(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        project_id=project_id,
    )
    return ApiResponse(data=[ResearchEthicsApprovalResponse.model_validate(a) for a in approvals])


@research_router.get(
    "/ethics",
    response_model=ApiResponse[list[ResearchEthicsApprovalResponse]],
    summary="List Institutional Ethics Approvals",
)
async def list_all_ethics_approvals(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    project_id: UUID | None = None,
):
    approvals = await ResearchService.list_ethics_approvals(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        project_id=project_id,
    )
    return ApiResponse(data=[ResearchEthicsApprovalResponse.model_validate(a) for a in approvals])


@research_router.post(
    "/ethics",
    response_model=ApiResponse[ResearchEthicsApprovalResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Submit Research Ethics/Compliance Application",
)
async def create_ethics_approval(
    payload: ResearchEthicsApprovalCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    approval = await ResearchService.create_ethics_approval(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        data=payload,
        current_user_id=current_user.id,
    )
    return ApiResponse(data=ResearchEthicsApprovalResponse.model_validate(approval))


@research_router.post(
    "/ethics/{approval_id}/decide",
    response_model=ApiResponse[ResearchEthicsApprovalResponse],
    summary="Record Ethics Committee Decision",
)
async def decide_ethics_approval(
    approval_id: UUID,
    payload: ResearchEthicsApprovalDecision,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_ETHICS_REVIEW_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    approval = await ResearchService.decide_ethics_approval(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        approval_id=approval_id,
        data=payload,
        current_user_id=current_user.id,
    )
    return ApiResponse(data=ResearchEthicsApprovalResponse.model_validate(approval))


@research_router.post(
    "/ethics/{approval_id}/decision",
    response_model=ApiResponse[ResearchEthicsApprovalResponse],
    include_in_schema=False,
)
async def decide_ethics_approval_alias(
    approval_id: UUID,
    payload: ResearchEthicsApprovalDecision,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_ETHICS_REVIEW_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    return await decide_ethics_approval(
        approval_id=approval_id,
        payload=payload,
        tenant_ctx=tenant_ctx,
        current_user=current_user,
        db=db,
    )


# =============================================================================
# 9. RESEARCH PUBLICATIONS & OUTPUTS
# =============================================================================


@research_router.get(
    "/outputs",
    response_model=ApiResponse[list[ResearchOutputResponse]],
    summary="List Research Publications and Outputs",
)
async def list_outputs(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    project_id: UUID | None = None,
    output_type: str | None = None,
    is_verified: bool | None = None,
    limit: int = 50,
    offset: int = 0,
):
    outputs, _ = await ResearchService.list_research_outputs(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        project_id=project_id,
        output_type=output_type,
        is_verified=is_verified,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(data=[ResearchOutputResponse.model_validate(o) for o in outputs])


@research_router.post(
    "/outputs",
    response_model=ApiResponse[ResearchOutputResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register Research Publication or Output",
)
async def create_output(
    payload: ResearchOutputCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_OUTPUTS_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    output = await ResearchService.create_research_output(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        data=payload,
        current_user_id=current_user.id,
    )
    return ApiResponse(data=ResearchOutputResponse.model_validate(output))


@research_router.get(
    "/outputs/{output_id}",
    response_model=ApiResponse[ResearchOutputResponse],
    summary="Get Research Publication/Output by ID",
)
async def get_output(
    output_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    output = await ResearchService.get_research_output(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        output_id=output_id,
    )
    return ApiResponse(data=ResearchOutputResponse.model_validate(output))


@research_router.post(
    "/outputs/{output_id}/verify",
    response_model=ApiResponse[ResearchOutputResponse],
    summary="Verify Academic Publication and External Indexing",
)
async def verify_output(
    output_id: UUID,
    payload: ResearchOutputVerify,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_OUTPUTS_VERIFY_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    output = await ResearchService.verify_research_output(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        output_id=output_id,
        data=payload,
        current_user_id=current_user.id,
    )
    return ApiResponse(data=ResearchOutputResponse.model_validate(output))


# =============================================================================
# 10. INTELLECTUAL PROPERTY & INVENTION DISCLOSURES
# =============================================================================


@research_router.get(
    "/ip/disclosures",
    response_model=ApiResponse[list[ResearchInventionDisclosureResponse]],
    summary="List Invention Disclosures (Role Confidentiality Enforced)",
)
async def list_invention_disclosures(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    project_id: UUID | None = None,
    limit: int = 50,
    offset: int = 0,
):
    has_confidential = any(
        r in current_user.roles for r in ["SUPER_ADMIN", "INSTITUTION_ADMIN", "IP_OFFICER"]
    )
    items, _ = await ResearchService.list_invention_disclosures(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        current_user_id=current_user.id,
        has_confidential_permission=has_confidential,
        project_id=project_id,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(data=[ResearchInventionDisclosureResponse.model_validate(i) for i in items])


@research_router.post(
    "/ip/disclosures",
    response_model=ApiResponse[ResearchInventionDisclosureResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register Intellectual Property Invention Disclosure",
)
async def create_invention_disclosure(
    payload: ResearchInventionDisclosureCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_IP_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    disclosure = await ResearchService.create_invention_disclosure(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        data=payload,
        current_user_id=current_user.id,
    )
    return ApiResponse(data=ResearchInventionDisclosureResponse.model_validate(disclosure))


@research_router.get(
    "/ip/disclosures/{disclosure_id}",
    response_model=ApiResponse[ResearchInventionDisclosureResponse],
    summary="Get Invention Disclosure with Confidentiality Verification",
)
async def get_invention_disclosure(
    disclosure_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    has_confidential = any(
        r in current_user.roles for r in ["SUPER_ADMIN", "INSTITUTION_ADMIN", "IP_OFFICER"]
    )
    disclosure = await ResearchService.get_invention_disclosure(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        disclosure_id=disclosure_id,
        current_user_id=current_user.id,
        has_confidential_permission=has_confidential,
    )
    return ApiResponse(data=ResearchInventionDisclosureResponse.model_validate(disclosure))


@research_router.patch(
    "/ip/disclosures/{disclosure_id}",
    response_model=ApiResponse[ResearchInventionDisclosureResponse],
    summary="Update Invention Disclosure & Patent Milestones",
)
async def update_invention_disclosure(
    disclosure_id: UUID,
    payload: ResearchInventionDisclosureUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_IP_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    has_confidential = any(
        r in current_user.roles for r in ["SUPER_ADMIN", "INSTITUTION_ADMIN", "IP_OFFICER"]
    )
    disclosure = await ResearchService.update_invention_disclosure(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        disclosure_id=disclosure_id,
        data=payload,
        current_user_id=current_user.id,
        has_confidential_permission=has_confidential,
    )
    return ApiResponse(data=ResearchInventionDisclosureResponse.model_validate(disclosure))


# =============================================================================
# 11. RESEARCH FACILITIES & PROJECT RISKS
# =============================================================================


@research_router.get(
    "/facilities/projects/{project_id}",
    response_model=ApiResponse[list[ResearchFacilityReferenceResponse]],
    summary="List Facilities Referenced by Project",
)
async def list_facility_references(
    project_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    refs = await ResearchService.list_facility_references(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        project_id=project_id,
    )
    return ApiResponse(data=[ResearchFacilityReferenceResponse.model_validate(r) for r in refs])


@research_router.post(
    "/facilities",
    response_model=ApiResponse[ResearchFacilityReferenceResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Attach Facility/Equipment Reference to Project",
)
async def add_facility_reference(
    payload: ResearchFacilityReferenceCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    ref = await ResearchService.add_facility_reference(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        data=payload,
        current_user_id=current_user.id,
    )
    return ApiResponse(data=ResearchFacilityReferenceResponse.model_validate(ref))


@research_router.get(
    "/risks/projects/{project_id}",
    response_model=ApiResponse[list[ResearchProjectRiskResponse]],
    summary="List Logged Risks for Project",
)
async def list_project_risks(
    project_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    risks = await ResearchService.list_project_risks(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        project_id=project_id,
    )
    return ApiResponse(data=[ResearchProjectRiskResponse.model_validate(r) for r in risks])


@research_router.post(
    "/risks",
    response_model=ApiResponse[ResearchProjectRiskResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Log Research Project Risk",
)
async def create_project_risk(
    payload: ResearchProjectRiskCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    risk = await ResearchService.create_project_risk(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        data=payload,
        current_user_id=current_user.id,
    )
    return ApiResponse(data=ResearchProjectRiskResponse.model_validate(risk))


@research_router.patch(
    "/risks/{risk_id}",
    response_model=ApiResponse[ResearchProjectRiskResponse],
    summary="Update Project Risk Status and Mitigation",
)
async def update_project_risk(
    risk_id: UUID,
    payload: ResearchProjectRiskUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    risk = await ResearchService.update_project_risk(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        risk_id=risk_id,
        data=payload,
        current_user_id=current_user.id,
    )
    return ApiResponse(data=ResearchProjectRiskResponse.model_validate(risk))


# =============================================================================
# 12. RESEARCH ANALYTICS & SCHEDULED COMPLIANCE SWEEPS
# =============================================================================


@research_router.get(
    "/analytics/summary",
    response_model=ApiResponse[ResearchAnalyticsSummaryResponse],
    summary="Get Institutional Research Performance & Analytics Summary",
)
async def get_analytics_summary(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_ANALYTICS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    summary = await ResearchService.get_analytics_summary(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
    )
    return ApiResponse(data=summary)


@research_router.post(
    "/analytics/sweep",
    response_model=ApiResponse[ResearchDeadlineSweepResponse],
    summary="Trigger Scheduled Research Compliance & Deadline Sweep",
)
async def trigger_compliance_sweep(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESEARCH_PROJECTS_TRANSITION_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    res = await ResearchService.sweep_deadlines_and_compliance(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
    )
    return ApiResponse(data=res)
