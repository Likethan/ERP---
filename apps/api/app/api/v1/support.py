"""Enterprise Customer Support, Service Desk & SLA Management Router for CampusOS (Step 36).

Exposes RESTful endpoints for:
- Creating, listing, and filtering customer support requests
- Retrieving ticket details with zero-trust internal note segregation
- Executing guarded lifecycle transitions with SLA clock pause/resumption
- Managing team and agent assignments and escalations
- Posting customer-visible public replies and restricted internal notes
- Linking operational and security incidents without leaking privileged evidence
- Recording CSAT customer satisfaction ratings and feedback
- Generating operational analytics and SLA compliance reporting
"""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_current_active_user, require_platform_admin
from app.core.exceptions import NotFoundException, PermissionDeniedException
from app.models.people import User
from app.models.support import SupportSlaPolicy, SupportTeam
from app.schemas.common import PaginatedMeta, PaginatedResponse
from app.schemas.support import (
    SupportAnalyticsMetrics,
    SupportSlaPolicyCreateRequest,
    SupportSlaPolicyResponse,
    SupportTeamResponse,
    SupportTicketArticleLinkRequest,
    SupportTicketArticleLinkResponse,
    SupportTicketAssignRequest,
    SupportTicketCloseRequest,
    SupportTicketCreateRequest,
    SupportTicketCsatRequest,
    SupportTicketDetailResponse,
    SupportTicketEscalateRequest,
    SupportTicketIncidentLinkRequest,
    SupportTicketMessageCreateRequest,
    SupportTicketMessageResponse,
    SupportTicketPaginatedResponse,
    SupportTicketReopenRequest,
    SupportTicketResolveRequest,
    SupportTicketResponse,
    SupportTicketTransitionRequest,
    SupportTicketUpdateRequest,
)
from app.services.support_service import SupportService

router = APIRouter(prefix="/support", tags=["Customer Support & Service Desk"])


async def _can_access_internal_notes(db: AsyncSession, user: User) -> bool:
    """Check if the user is authorized to view or create internal investigation notes."""
    roles = await SupportService.get_user_roles(db, user)
    return bool(roles.intersection({"SUPER_ADMIN", "PLATFORM_OPERATOR", "INSTITUTION_ADMIN", "SUPPORT_AGENT"}))


# =============================================================================
# 1. TICKET INTAKE & MANAGEMENT
# =============================================================================


@router.post("/tickets", response_model=SupportTicketResponse, status_code=status.HTTP_201_CREATED)
async def create_support_ticket(
    payload: SupportTicketCreateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SupportTicketResponse:
    """Intake an institutional support request with automated category routing and SLA clock start."""
    tenant_id = current_user.primary_tenant_id
    ticket = await SupportService.create_ticket(
        db=db,
        requester=current_user,
        tenant_id=tenant_id,
        payload=payload,
    )
    return SupportTicketResponse.model_validate(ticket)


@router.get("/tickets", response_model=SupportTicketPaginatedResponse)
async def list_support_tickets(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    category: str | None = Query(default=None),
    assigned_agent_id: UUID | None = Query(default=None),
    assigned_team_id: UUID | None = Query(default=None),
    tenant_id: UUID | None = Query(default=None, description="Platform operator filter"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
) -> SupportTicketPaginatedResponse:
    """List tickets scoped strictly to user permissions (requester, institution admin, or platform)."""
    tickets, total = await SupportService.list_tickets(
        db=db,
        current_user=current_user,
        tenant_id=tenant_id,
        status=status,
        priority=priority,
        category=category,
        assigned_agent_id=assigned_agent_id,
        assigned_team_id=assigned_team_id,
        page=page,
        limit=limit,
    )
    items = [SupportTicketResponse.model_validate(t) for t in tickets]
    total_pages = (total + limit - 1) // limit if total > 0 else 1
    return SupportTicketPaginatedResponse(
        items=items,
        data=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


@router.get("/tickets/{ticket_id}", response_model=SupportTicketDetailResponse)
async def get_support_ticket(
    ticket_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SupportTicketDetailResponse:
    """Retrieve ticket details. Internal notes are stripped unless caller is authorized support staff."""
    can_view_internal = await _can_access_internal_notes(db, current_user)
    ticket = await SupportService.get_ticket(
        db=db,
        ticket_id=ticket_id,
        current_user=current_user,
        can_view_internal_notes=can_view_internal,
    )
    return SupportTicketDetailResponse.model_validate(ticket)


@router.patch("/tickets/{ticket_id}", response_model=SupportTicketResponse)
async def update_support_ticket(
    ticket_id: UUID,
    payload: SupportTicketUpdateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SupportTicketResponse:
    """Update editable metadata on a ticket."""
    ticket = await SupportService.get_ticket(db, ticket_id, current_user, can_view_internal_notes=True)

    if payload.subject is not None:
        ticket.subject = payload.subject
    if payload.description is not None:
        ticket.description = payload.description
    if payload.category is not None:
        ticket.category = payload.category.upper()
    if payload.subcategory is not None:
        ticket.subcategory = payload.subcategory
    if payload.priority is not None:
        ticket.priority = payload.priority.upper()
    if payload.severity is not None:
        ticket.severity = payload.severity.upper()
    if payload.related_erp_module is not None:
        ticket.related_erp_module = payload.related_erp_module.upper()
    if payload.tags is not None:
        ticket.tags = payload.tags

    await db.flush()
    await db.refresh(ticket)
    return SupportTicketResponse.model_validate(ticket)


# =============================================================================
# 2. LIFECYCLE & ASSIGNMENTS
# =============================================================================


@router.post("/tickets/{ticket_id}/transition", response_model=SupportTicketResponse)
@router.post("/tickets/{ticket_id}/transitions", response_model=SupportTicketResponse)
async def transition_ticket_status(
    ticket_id: UUID,
    payload: SupportTicketTransitionRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SupportTicketResponse:
    """Execute a guarded status machine transition with pause/resume of SLA clocks."""
    ticket = await SupportService.transition_status(
        db=db,
        ticket_id=ticket_id,
        payload=payload,
        actor=current_user,
    )
    return SupportTicketResponse.model_validate(ticket)


@router.post("/tickets/{ticket_id}/assignment", response_model=SupportTicketResponse)
@router.post("/tickets/{ticket_id}/assignments", response_model=SupportTicketResponse)
async def assign_support_ticket(
    ticket_id: UUID,
    payload: SupportTicketAssignRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SupportTicketResponse:
    """Assign or reassign ticket to an operational team and/or agent."""
    if not await _can_access_internal_notes(db, current_user):
        raise PermissionDeniedException("Only authorized support personnel can reassign tickets.")

    ticket = await SupportService.assign_ticket(
        db=db,
        ticket_id=ticket_id,
        payload=payload,
        actor=current_user,
    )
    return SupportTicketResponse.model_validate(ticket)


# =============================================================================
# 3. COMMUNICATIONS (Public Reply vs Internal Note)
# =============================================================================


@router.post("/tickets/{ticket_id}/messages", response_model=SupportTicketMessageResponse, status_code=status.HTTP_201_CREATED)
async def post_ticket_message(
    ticket_id: UUID,
    payload: SupportTicketMessageCreateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SupportTicketMessageResponse:
    """Add a customer-visible public reply or restricted internal investigation note."""
    msg = await SupportService.add_message(
        db=db,
        ticket_id=ticket_id,
        payload=payload,
        actor=current_user,
    )
    return SupportTicketMessageResponse.model_validate(msg)


# =============================================================================
# 4. RESOLUTION, CLOSURE, REOPEN & CSAT
# =============================================================================


@router.post("/tickets/{ticket_id}/resolve", response_model=SupportTicketResponse)
async def resolve_ticket(
    ticket_id: UUID,
    payload: SupportTicketResolveRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SupportTicketResponse:
    """Provide official resolution summary and transition ticket to RESOLVED."""
    ticket = await SupportService.resolve_ticket(
        db=db,
        ticket_id=ticket_id,
        payload=payload,
        actor=current_user,
    )
    return SupportTicketResponse.model_validate(ticket)


@router.post("/tickets/{ticket_id}/close", response_model=SupportTicketResponse)
async def close_ticket(
    ticket_id: UUID,
    payload: SupportTicketCloseRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SupportTicketResponse:
    """Formally close a verified ticket."""
    ticket = await SupportService.close_ticket(
        db=db,
        ticket_id=ticket_id,
        payload=payload,
        actor=current_user,
    )
    return SupportTicketResponse.model_validate(ticket)


@router.post("/tickets/{ticket_id}/reopen", response_model=SupportTicketResponse)
async def reopen_ticket(
    ticket_id: UUID,
    payload: SupportTicketReopenRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SupportTicketResponse:
    """Reopen a resolved or closed ticket with documented customer reason."""
    ticket = await SupportService.reopen_ticket(
        db=db,
        ticket_id=ticket_id,
        payload=payload,
        actor=current_user,
    )
    return SupportTicketResponse.model_validate(ticket)


@router.post("/tickets/{ticket_id}/escalate", response_model=SupportTicketResponse)
async def escalate_ticket(
    ticket_id: UUID,
    payload: SupportTicketEscalateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SupportTicketResponse:
    """Escalate ticket to higher support tier or supervisor queue."""
    ticket = await SupportService.escalate_ticket(
        db=db,
        ticket_id=ticket_id,
        payload=payload,
        actor=current_user,
    )
    return SupportTicketResponse.model_validate(ticket)


@router.post("/tickets/{ticket_id}/csat", response_model=SupportTicketResponse)
async def submit_ticket_csat(
    ticket_id: UUID,
    payload: SupportTicketCsatRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SupportTicketResponse:
    """Submit customer satisfaction rating and qualitative feedback."""
    ticket = await SupportService.submit_csat(
        db=db,
        ticket_id=ticket_id,
        payload=payload,
        actor=current_user,
    )
    return SupportTicketResponse.model_validate(ticket)


# =============================================================================
# 5. INCIDENTS & KNOWLEDGE BASE
# =============================================================================


@router.post("/tickets/{ticket_id}/link-incident", response_model=SupportTicketResponse)
async def link_incident_to_ticket(
    ticket_id: UUID,
    payload: SupportTicketIncidentLinkRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SupportTicketResponse:
    """Correlate ticket with an operational outage or security incident."""
    ticket = await SupportService.link_incident(
        db=db,
        ticket_id=ticket_id,
        payload=payload,
        actor=current_user,
    )
    return SupportTicketResponse.model_validate(ticket)


@router.post("/tickets/{ticket_id}/link-article", response_model=SupportTicketArticleLinkResponse, status_code=status.HTTP_201_CREATED)
async def link_article_to_ticket(
    ticket_id: UUID,
    payload: SupportTicketArticleLinkRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SupportTicketArticleLinkResponse:
    """Attach approved knowledge base article to a ticket."""
    link = await SupportService.link_article(
        db=db,
        ticket_id=ticket_id,
        payload=payload,
        actor=current_user,
    )
    return SupportTicketArticleLinkResponse.model_validate(link)


# =============================================================================
# 6. TEAMS, SLA POLICIES & ANALYTICS
# =============================================================================


@router.get("/teams", response_model=list[SupportTeamResponse])
async def list_support_teams(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[SupportTeamResponse]:
    """List operational support teams and specialization modules."""
    teams = await SupportService.get_or_seed_default_teams(db, current_user.primary_tenant_id)
    return [SupportTeamResponse.model_validate(t) for t in teams]


@router.get("/sla-policies", response_model=list[SupportSlaPolicyResponse])
async def list_sla_policies(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[SupportSlaPolicyResponse]:
    """List active SLA policies and targets."""
    stmt = select(SupportSlaPolicy).where(SupportSlaPolicy.is_active.is_(True))
    policies = list((await db.execute(stmt)).scalars().all())
    return [SupportSlaPolicyResponse.model_validate(p) for p in policies]


@router.post("/sla-policies", response_model=SupportSlaPolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_sla_policy(
    payload: SupportSlaPolicyCreateRequest,
    current_user: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SupportSlaPolicyResponse:
    """Establish a new platform or tenant-level SLA policy."""
    policy = SupportSlaPolicy(
        id=uuid4(),
        name=payload.name,
        description=payload.description,
        service_plan=payload.service_plan.upper(),
        priority=payload.priority.upper(),
        severity=payload.severity.upper() if payload.severity else None,
        category=payload.category.upper() if payload.category else None,
        response_target_minutes=payload.response_target_minutes,
        resolution_target_minutes=payload.resolution_target_minutes,
        business_hours_only=payload.business_hours_only,
        business_start_hour=payload.business_start_hour,
        business_end_hour=payload.business_end_hour,
        escalation_threshold_pct=payload.escalation_threshold_pct,
        escalation_team_id=payload.escalation_team_id,
        is_active=True,
    )
    db.add(policy)
    await db.flush()
    await db.refresh(policy)
    return SupportSlaPolicyResponse.model_validate(policy)


@router.get("/analytics", response_model=SupportAnalyticsMetrics)
async def get_support_analytics(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_id: UUID | None = Query(default=None, description="Platform operator filter"),
) -> SupportAnalyticsMetrics:
    """Retrieve operational service desk indicators, response speeds, and SLA compliance."""
    return await SupportService.get_analytics(
        db=db,
        current_user=current_user,
        tenant_id=tenant_id,
    )
