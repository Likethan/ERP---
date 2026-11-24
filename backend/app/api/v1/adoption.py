"""Enterprise Product Adoption, Training, In-App Guidance & Change Management Router (Step 37).

Exposes RESTful endpoints for:
- Role-aware onboarding journeys & ordered step execution
- Persistent user journey progress tracking across devices
- Modular training programs, modules, assignments, and certification
- Route-based contextual in-app guidance and walkthroughs
- Controlled product announcements, change notices, and mandatory acknowledgements
- Feature adoption targets and server-validated adoption milestones
- Multi-tenant enablement analytics, completion rates, and drop-off reporting
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_current_active_user
from app.core.exceptions import PermissionDeniedException
from app.models.people import User
from app.schemas.adoption import (
    AdoptionJourneyCreateRequest,
    AdoptionJourneyResponse,
    AdoptionSummaryDashboardResponse,
    AnnouncementAcknowledgeRequest,
    AnnouncementReadershipMetricsResponse,
    ContextualGuidanceCreateRequest,
    ContextualGuidanceResponse,
    FeatureAdoptionMilestoneRecordRequest,
    FeatureAdoptionMilestoneResponse,
    FeatureAdoptionTargetCreateRequest,
    FeatureAdoptionTargetResponse,
    FeatureRolloutAdoptionMetricsResponse,
    JourneyAdoptionMetricsResponse,
    ProductAnnouncementCreateRequest,
    ProductAnnouncementResponse,
    TrainingAssignmentResponse,
    TrainingAssignRequest,
    TrainingProgramCreateRequest,
    TrainingProgramMetricsResponse,
    TrainingProgramResponse,
    UserAnnouncementReceiptResponse,
    UserGuidanceActionRequest,
    UserGuidanceStateResponse,
    UserJourneyProgressResponse,
    UserJourneyStepCompleteRequest,
)
from app.services.adoption_service import AdoptionService

router = APIRouter(prefix="/adoption", tags=["Product Adoption & Enablement"])


def _get_user_roles(user: User) -> list[str]:
    """Extract string list of role names from authenticated user context."""
    return [ur.role.name for ur in user.roles if ur.role and ur.role.name]


def _check_admin_access(user: User) -> None:
    """Verify user is an institution or platform administrator."""
    roles = set(_get_user_roles(user))
    if not roles.intersection({"SUPER_ADMIN", "PLATFORM_OPERATOR", "INSTITUTION_ADMIN"}):
        raise PermissionDeniedException("adoption:admin:manage")


# =============================================================================
# 1. USER-FACING ONBOARDING JOURNEYS
# =============================================================================


@router.get("/journeys", response_model=list[AdoptionJourneyResponse])
async def list_user_journeys(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[AdoptionJourneyResponse]:
    """Retrieve published onboarding journeys matching the user's role and tenant."""
    roles = _get_user_roles(current_user)
    tenant_id = current_user.primary_tenant_id
    role_filter = roles[0] if roles else None
    journeys = await AdoptionService.list_journeys(
        db=db,
        tenant_id=tenant_id,
        role=role_filter,
        status_filter="PUBLISHED",
    )
    return [AdoptionJourneyResponse.model_validate(j) for j in journeys]


@router.get("/journeys/{journey_id}", response_model=AdoptionJourneyResponse)
async def get_journey_details(
    journey_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> AdoptionJourneyResponse:
    """Retrieve detailed onboarding journey specification and ordered milestones."""
    tenant_id = current_user.primary_tenant_id
    journey = await AdoptionService.get_journey_by_id(db, journey_id, tenant_id)
    return AdoptionJourneyResponse.model_validate(journey)


@router.get("/journeys/{journey_id}/progress", response_model=UserJourneyProgressResponse)
async def get_user_journey_progress(
    journey_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserJourneyProgressResponse:
    """Fetch current user's execution state or resume incomplete journey across devices."""
    tenant_id = current_user.primary_tenant_id
    if not tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Active tenant required.")

    progress = await AdoptionService.get_or_initialize_user_progress(
        db=db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        journey_id=journey_id,
    )
    return UserJourneyProgressResponse.model_validate(progress)


@router.post("/journeys/{journey_id}/steps/complete", response_model=UserJourneyProgressResponse)
async def complete_journey_step(
    journey_id: UUID,
    payload: UserJourneyStepCompleteRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserJourneyProgressResponse:
    """Record completion of a journey step and recompute progression percentage."""
    tenant_id = current_user.primary_tenant_id
    if not tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Active tenant required.")

    progress = await AdoptionService.complete_journey_step(
        db=db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        journey_id=journey_id,
        step_key=payload.step_key,
        notes=payload.notes,
        metadata=payload.metadata,
    )
    return UserJourneyProgressResponse.model_validate(progress)


# =============================================================================
# 2. TRAINING PROGRAMS & LEARNING ASSIGNMENTS
# =============================================================================


@router.get("/training/assigned", response_model=list[TrainingAssignmentResponse])
async def list_assigned_training(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status: str | None = Query(default=None),
) -> list[TrainingAssignmentResponse]:
    """Retrieve all training programs assigned to or enrolled by the user."""
    tenant_id = current_user.primary_tenant_id
    if not tenant_id:
        return []
    assignments = await AdoptionService.list_user_training_assignments(
        db=db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        status_filter=status,
    )
    return [TrainingAssignmentResponse.model_validate(a) for a in assignments]


@router.get("/training/programs/{program_id}", response_model=TrainingProgramResponse)
async def get_training_program(
    program_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TrainingProgramResponse:
    """Retrieve training program curriculum and modules."""
    tenant_id = current_user.primary_tenant_id
    program = await AdoptionService.get_training_program_by_id(db, program_id, tenant_id)
    return TrainingProgramResponse.model_validate(program)


@router.post("/training/programs/{program_id}/modules/complete", response_model=TrainingAssignmentResponse)
async def complete_training_module(
    program_id: UUID,
    module_key: str = Query(...),
    notes: str | None = Query(default=None),
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db_session)] = None,
) -> TrainingAssignmentResponse:
    """Record verified module completion and evaluate program certification."""
    tenant_id = current_user.primary_tenant_id
    if not tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Active tenant required.")

    assignment = await AdoptionService.complete_training_module(
        db=db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        program_id=program_id,
        module_key=module_key,
        notes=notes,
    )
    return TrainingAssignmentResponse.model_validate(assignment)


# =============================================================================
# 3. CONTEXTUAL IN-APP GUIDANCE
# =============================================================================


@router.get("/guidance", response_model=list[ContextualGuidanceResponse])
async def get_contextual_guidance(
    route_path: str = Query(..., description="Semantic route path in frontend"),
    feature_key: str | None = Query(default=None),
    current_user: Annotated[User, Depends(get_current_active_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db_session)] = None,
) -> list[ContextualGuidanceResponse]:
    """Retrieve active guidance, walkthroughs, or tooltips for the current product context."""
    tenant_id = current_user.primary_tenant_id or UUID("00000000-0000-0000-0000-000000000000")
    roles = _get_user_roles(current_user)

    items = await AdoptionService.get_guidance_for_route(
        db=db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        user_roles=roles,
        route_path=route_path,
        feature_key=feature_key,
    )
    return [ContextualGuidanceResponse.model_validate(g) for g in items]


@router.post("/guidance/{guidance_id}/action", response_model=UserGuidanceStateResponse)
async def record_guidance_action(
    guidance_id: UUID,
    payload: UserGuidanceActionRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserGuidanceStateResponse:
    """Record user impression, dismissal, or completion of contextual guidance."""
    tenant_id = current_user.primary_tenant_id or UUID("00000000-0000-0000-0000-000000000000")
    state = await AdoptionService.record_guidance_action(
        db=db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        guidance_id=guidance_id,
        action=payload.action,
    )
    return UserGuidanceStateResponse.model_validate(state)


# =============================================================================
# 4. PRODUCT ANNOUNCEMENTS & CHANGE NOTICES
# =============================================================================


@router.get("/announcements", response_model=list[ProductAnnouncementResponse])
async def list_user_announcements(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[ProductAnnouncementResponse]:
    """List published feature releases, workflow updates, and maintenance announcements."""
    tenant_id = current_user.primary_tenant_id or UUID("00000000-0000-0000-0000-000000000000")
    roles = _get_user_roles(current_user)
    return await AdoptionService.list_user_announcements(
        db=db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        user_roles=roles,
    )


@router.post("/announcements/{announcement_id}/read", response_model=UserAnnouncementReceiptResponse)
async def mark_announcement_read(
    announcement_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserAnnouncementReceiptResponse:
    """Record read receipt for a product announcement."""
    tenant_id = current_user.primary_tenant_id or UUID("00000000-0000-0000-0000-000000000000")
    receipt = await AdoptionService.mark_announcement_read(
        db=db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        announcement_id=announcement_id,
    )
    return UserAnnouncementReceiptResponse.model_validate(receipt)


@router.post("/announcements/{announcement_id}/acknowledge", response_model=UserAnnouncementReceiptResponse)
async def acknowledge_announcement(
    announcement_id: UUID,
    payload: AnnouncementAcknowledgeRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserAnnouncementReceiptResponse:
    """Acknowledge mandatory policy update or material workflow change notice."""
    tenant_id = current_user.primary_tenant_id or UUID("00000000-0000-0000-0000-000000000000")
    receipt = await AdoptionService.acknowledge_announcement(
        db=db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        announcement_id=announcement_id,
        notes=payload.acknowledgement_notes,
    )
    return UserAnnouncementReceiptResponse.model_validate(receipt)


# =============================================================================
# 5. FEATURE ADOPTION MILESTONES
# =============================================================================


@router.post("/milestones", response_model=FeatureAdoptionMilestoneResponse, status_code=status.HTTP_201_CREATED)
async def record_feature_milestone(
    payload: FeatureAdoptionMilestoneRecordRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> FeatureAdoptionMilestoneResponse:
    """Record server-validated feature discovery, first use, or workflow completion."""
    tenant_id = current_user.primary_tenant_id
    if not tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Active tenant required.")

    milestone = await AdoptionService.record_adoption_milestone(
        db=db,
        tenant_id=tenant_id,
        user_id=current_user.id,
        data=payload,
    )
    return FeatureAdoptionMilestoneResponse.model_validate(milestone)


# =============================================================================
# 6. ADMINISTRATIVE CONFIGURATION
# =============================================================================


@router.post("/admin/journeys", response_model=AdoptionJourneyResponse, status_code=status.HTTP_201_CREATED)
async def create_journey_definition(
    payload: AdoptionJourneyCreateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_id: UUID | None = Query(default=None, description="Optional tenant scoping for platform admin"),
) -> AdoptionJourneyResponse:
    """Configure an onboarding journey for a role or department."""
    _check_admin_access(current_user)
    roles = set(_get_user_roles(current_user))
    is_super = bool(roles.intersection({"SUPER_ADMIN", "PLATFORM_OPERATOR"}))

    resolved_tenant = tenant_id if is_super else current_user.primary_tenant_id

    journey = await AdoptionService.create_journey(
        db=db,
        tenant_id=resolved_tenant,
        data=payload,
        current_user=current_user,
    )
    return AdoptionJourneyResponse.model_validate(journey)


@router.post("/admin/journeys/{journey_id}/publish", response_model=AdoptionJourneyResponse)
async def publish_journey_definition(
    journey_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> AdoptionJourneyResponse:
    """Publish a journey definition for live user onboarding."""
    _check_admin_access(current_user)
    roles = set(_get_user_roles(current_user))
    is_super = bool(roles.intersection({"SUPER_ADMIN", "PLATFORM_OPERATOR"}))
    tenant_id = None if is_super else current_user.primary_tenant_id

    journey = await AdoptionService.publish_journey(
        db=db,
        journey_id=journey_id,
        tenant_id=tenant_id,
        current_user=current_user,
    )
    return AdoptionJourneyResponse.model_validate(journey)


@router.post("/admin/journeys/{journey_id}/archive", response_model=AdoptionJourneyResponse)
async def archive_journey_definition(
    journey_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> AdoptionJourneyResponse:
    """Archive an onboarding journey."""
    _check_admin_access(current_user)
    roles = set(_get_user_roles(current_user))
    is_super = bool(roles.intersection({"SUPER_ADMIN", "PLATFORM_OPERATOR"}))
    tenant_id = None if is_super else current_user.primary_tenant_id

    journey = await AdoptionService.archive_journey(
        db=db,
        journey_id=journey_id,
        tenant_id=tenant_id,
        current_user=current_user,
    )
    return AdoptionJourneyResponse.model_validate(journey)


@router.post("/admin/journeys/seed-defaults", response_model=list[AdoptionJourneyResponse])
async def seed_default_onboarding_journeys(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[AdoptionJourneyResponse]:
    """Seed standard onboarding journeys (Student, Faculty, Admin)."""
    _check_admin_access(current_user)
    tenant_id = current_user.primary_tenant_id
    seeded = await AdoptionService.seed_default_journeys(db, tenant_id, current_user)
    return [AdoptionJourneyResponse.model_validate(j) for j in seeded]


@router.post("/admin/training/programs", response_model=TrainingProgramResponse, status_code=status.HTTP_201_CREATED)
async def create_training_program(
    payload: TrainingProgramCreateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_id: UUID | None = Query(default=None),
) -> TrainingProgramResponse:
    """Create a training program curriculum and modules."""
    _check_admin_access(current_user)
    roles = set(_get_user_roles(current_user))
    is_super = bool(roles.intersection({"SUPER_ADMIN", "PLATFORM_OPERATOR"}))
    resolved_tenant = tenant_id if is_super else current_user.primary_tenant_id

    program = await AdoptionService.create_training_program(
        db=db,
        tenant_id=resolved_tenant,
        data=payload,
        current_user=current_user,
    )
    return TrainingProgramResponse.model_validate(program)


@router.post("/admin/training/programs/{program_id}/publish", response_model=TrainingProgramResponse)
async def publish_training_program(
    program_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TrainingProgramResponse:
    """Publish a training program."""
    _check_admin_access(current_user)
    roles = set(_get_user_roles(current_user))
    is_super = bool(roles.intersection({"SUPER_ADMIN", "PLATFORM_OPERATOR"}))
    tenant_id = None if is_super else current_user.primary_tenant_id

    program = await AdoptionService.publish_training_program(
        db=db,
        program_id=program_id,
        tenant_id=tenant_id,
        current_user=current_user,
    )
    return TrainingProgramResponse.model_validate(program)


@router.post("/admin/training/assign", response_model=list[TrainingAssignmentResponse])
async def assign_training_program(
    payload: TrainingAssignRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[TrainingAssignmentResponse]:
    """Assign training program to users with notification dispatch."""
    _check_admin_access(current_user)
    tenant_id = current_user.primary_tenant_id
    if not tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Active tenant required.")

    assignments = await AdoptionService.assign_training_program(
        db=db,
        tenant_id=tenant_id,
        data=payload,
        current_user=current_user,
    )
    return [TrainingAssignmentResponse.model_validate(a) for a in assignments]


@router.post("/admin/guidance", response_model=ContextualGuidanceResponse, status_code=status.HTTP_201_CREATED)
async def create_guidance(
    payload: ContextualGuidanceCreateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_id: UUID | None = Query(default=None),
) -> ContextualGuidanceResponse:
    """Create contextual guidance, tooltip, or banner."""
    _check_admin_access(current_user)
    roles = set(_get_user_roles(current_user))
    is_super = bool(roles.intersection({"SUPER_ADMIN", "PLATFORM_OPERATOR"}))
    resolved_tenant = tenant_id if is_super else current_user.primary_tenant_id

    guidance = await AdoptionService.create_contextual_guidance(
        db=db,
        tenant_id=resolved_tenant,
        data=payload,
        current_user=current_user,
    )
    return ContextualGuidanceResponse.model_validate(guidance)


@router.post("/admin/announcements", response_model=ProductAnnouncementResponse, status_code=status.HTTP_201_CREATED)
async def create_announcement(
    payload: ProductAnnouncementCreateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_id: UUID | None = Query(default=None),
) -> ProductAnnouncementResponse:
    """Draft a product release announcement or change notice."""
    _check_admin_access(current_user)
    roles = set(_get_user_roles(current_user))
    is_super = bool(roles.intersection({"SUPER_ADMIN", "PLATFORM_OPERATOR"}))
    resolved_tenant = tenant_id if is_super else current_user.primary_tenant_id

    announcement = await AdoptionService.create_announcement(
        db=db,
        tenant_id=resolved_tenant,
        data=payload,
        current_user=current_user,
    )
    return ProductAnnouncementResponse.model_validate(announcement)


@router.post("/admin/announcements/{announcement_id}/publish", response_model=ProductAnnouncementResponse)
async def publish_announcement(
    announcement_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ProductAnnouncementResponse:
    """Publish a product announcement."""
    _check_admin_access(current_user)
    roles = set(_get_user_roles(current_user))
    is_super = bool(roles.intersection({"SUPER_ADMIN", "PLATFORM_OPERATOR"}))
    tenant_id = None if is_super else current_user.primary_tenant_id

    announcement = await AdoptionService.publish_announcement(
        db=db,
        announcement_id=announcement_id,
        tenant_id=tenant_id,
        current_user=current_user,
    )
    return ProductAnnouncementResponse.model_validate(announcement)


@router.post("/admin/targets", response_model=FeatureAdoptionTargetResponse, status_code=status.HTTP_201_CREATED)
async def create_adoption_target(
    payload: FeatureAdoptionTargetCreateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> FeatureAdoptionTargetResponse:
    """Configure an institutional adoption target for a feature."""
    _check_admin_access(current_user)
    tenant_id = current_user.primary_tenant_id
    if not tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Active tenant required.")

    target = await AdoptionService.create_adoption_target(
        db=db,
        tenant_id=tenant_id,
        data=payload,
    )
    return FeatureAdoptionTargetResponse.model_validate(target)


# =============================================================================
# 7. ADOPTION ANALYTICS & REPORTING
# =============================================================================


@router.get("/admin/reports/journeys/{journey_id}", response_model=JourneyAdoptionMetricsResponse)
async def get_journey_report(
    journey_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> JourneyAdoptionMetricsResponse:
    """Analyze step-by-step dropoff and completion rates for an onboarding journey."""
    _check_admin_access(current_user)
    tenant_id = current_user.primary_tenant_id
    if not tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Active tenant required.")

    return await AdoptionService.get_journey_metrics(db, tenant_id, journey_id)


@router.get("/admin/reports/training/{program_id}", response_model=TrainingProgramMetricsResponse)
async def get_training_report(
    program_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TrainingProgramMetricsResponse:
    """Analyze training enrollment, completion, and overdue metrics."""
    _check_admin_access(current_user)
    tenant_id = current_user.primary_tenant_id
    if not tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Active tenant required.")

    return await AdoptionService.get_training_metrics(db, tenant_id, program_id)


@router.get("/admin/reports/announcements/{announcement_id}", response_model=AnnouncementReadershipMetricsResponse)
async def get_announcement_report(
    announcement_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> AnnouncementReadershipMetricsResponse:
    """Analyze announcement readership and mandatory acknowledgement rates."""
    _check_admin_access(current_user)
    tenant_id = current_user.primary_tenant_id
    if not tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Active tenant required.")

    return await AdoptionService.get_announcement_metrics(db, tenant_id, announcement_id)


@router.get("/admin/reports/features/{feature_key}", response_model=FeatureRolloutAdoptionMetricsResponse)
async def get_feature_adoption_report(
    feature_key: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> FeatureRolloutAdoptionMetricsResponse:
    """Measure feature discovery, first-use, and workflow completion against target."""
    _check_admin_access(current_user)
    tenant_id = current_user.primary_tenant_id
    if not tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Active tenant required.")

    return await AdoptionService.get_feature_adoption_metrics(db, tenant_id, feature_key)


@router.get("/admin/dashboard", response_model=AdoptionSummaryDashboardResponse)
async def get_adoption_dashboard_summary(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> AdoptionSummaryDashboardResponse:
    """High-level institutional adoption and enablement summary dashboard."""
    _check_admin_access(current_user)
    tenant_id = current_user.primary_tenant_id
    if not tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Active tenant required.")

    return await AdoptionService.get_dashboard_summary(db, tenant_id)
