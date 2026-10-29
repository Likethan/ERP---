"""CampusOS Enterprise Sports, Athletics, Recreation & Student Fitness API Router (Step 57).

CampusOS Tagline: "One Campus. One System. One Source of Truth."
"""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_tenant_context, require_permission
from app.core.permissions import (
    SPORTS_ATTENDANCE_RECORD,
    SPORTS_BOOKING_CANCEL,
    SPORTS_BOOKING_CREATE,
    SPORTS_COMPETITION_MANAGE,
    SPORTS_COMPETITION_READ,
    SPORTS_COMPETITION_REGISTER,
    SPORTS_DEPARTMENT_MANAGE,
    SPORTS_DEPARTMENT_READ,
    SPORTS_EQUIPMENT_MANAGE,
    SPORTS_EQUIPMENT_READ,
    SPORTS_FACILITY_MANAGE,
    SPORTS_FACILITY_READ,
    SPORTS_MATCH_OFFICIATE,
    SPORTS_MATCH_SCHEDULE,
    SPORTS_PARTICIPANT_MANAGE,
    SPORTS_PARTICIPANT_READ,
    SPORTS_REPORT_READ,
    SPORTS_RESULT_RECORD,
    SPORTS_RESULT_VERIFY,
    SPORTS_ROSTER_MANAGE,
    SPORTS_TEAM_MANAGE,
    SPORTS_TEAM_READ,
    SPORTS_TRAINING_MANAGE,
    SPORTS_TRAINING_READ,
)
from app.core.tenant import TenantContext
from app.models.people import User
from app.schemas.sports import (
    BulkAttendanceCreate,
    CoachingAssignmentCreate,
    CoachingAssignmentResponse,
    CompetitionCreate,
    CompetitionRegistrationCreate,
    CompetitionRegistrationResponse,
    CompetitionResponse,
    CompetitionStandingResponse,
    CompetitionUpdate,
    EquipmentAssignmentResponse,
    EquipmentCheckoutCreate,
    EquipmentReturnRequest,
    FacilityBookingCreate,
    FacilityBookingResponse,
    FixtureGenerationRequest,
    MatchFixtureResponse,
    MatchFixtureUpdate,
    MatchOfficialAssignmentCreate,
    MatchOfficialAssignmentResponse,
    MatchResultCreate,
    MatchResultResponse,
    MatchResultVerify,
    SportsAchievementCreate,
    SportsAchievementResponse,
    SportsDashboardSummary,
    SportsDepartmentCreate,
    SportsDepartmentResponse,
    SportsDepartmentUpdate,
    SportsFacilityCreate,
    SportsFacilityResponse,
    SportsFacilityUpdate,
    SportsParticipantCreate,
    SportsParticipantResponse,
    SportsParticipantUpdate,
    SportsTeamCreate,
    SportsTeamResponse,
    SportsTeamUpdate,
    TeamMembershipCreate,
    TeamMembershipResponse,
    TeamMembershipUpdate,
    TrainingAttendanceResponse,
    TrainingProgramCreate,
    TrainingProgramResponse,
    TrainingProgramUpdate,
    TrainingSessionCreate,
    TrainingSessionResponse,
)
from app.services.sports_service import sports_service

sports_router = APIRouter(prefix="/sports", tags=["Sports & Athletics Management"])


# =============================================================================
# 1. OPERATIONS DASHBOARD & ANALYTICS
# =============================================================================


@sports_router.get(
    "/dashboard",
    response_model=SportsDashboardSummary,
    summary="Get centralized sports operations KPIs and metrics",
)
async def get_sports_dashboard(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_REPORT_READ))],
):
    return await sports_service.get_dashboard_summary(db, tenant.tenant_id)


# =============================================================================
# 2. SPORTS DEPARTMENTS
# =============================================================================


@sports_router.get(
    "/departments",
    response_model=list[SportsDepartmentResponse],
    summary="List athletic departments and recreation centers",
)
async def list_sports_departments(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_DEPARTMENT_READ))],
    campus_id: UUID | None = Query(None),
):
    return await sports_service.list_departments(db, tenant.tenant_id, campus_id=campus_id)


@sports_router.post(
    "/departments",
    response_model=SportsDepartmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create sports department / athletic unit",
)
async def create_sports_department(
    data: SportsDepartmentCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_DEPARTMENT_MANAGE))],
):
    return await sports_service.create_department(db, tenant.tenant_id, data)


@sports_router.get(
    "/departments/{department_id}",
    response_model=SportsDepartmentResponse,
    summary="Get department details by ID",
)
async def get_sports_department(
    department_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_DEPARTMENT_READ))],
):
    return await sports_service.get_department(db, tenant.tenant_id, department_id)


@sports_router.put(
    "/departments/{department_id}",
    response_model=SportsDepartmentResponse,
    summary="Update sports department",
)
async def update_sports_department(
    department_id: UUID,
    data: SportsDepartmentUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_DEPARTMENT_MANAGE))],
):
    return await sports_service.update_department(db, tenant.tenant_id, department_id, data)


# =============================================================================
# 3. SPORTS FACILITIES & CALENDAR
# =============================================================================


@sports_router.get(
    "/facilities",
    response_model=list[SportsFacilityResponse],
    summary="List sports facilities, grounds, courts and pools",
)
async def list_sports_facilities(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_FACILITY_READ))],
    campus_id: UUID | None = Query(None),
    facility_type: str | None = Query(None),
    facility_status: str | None = Query(None, alias="status"),
):
    return await sports_service.list_facilities(
        db, tenant.tenant_id, campus_id=campus_id, facility_type=facility_type, status=facility_status
    )


@sports_router.post(
    "/facilities",
    response_model=SportsFacilityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new sports facility or court",
)
async def create_sports_facility(
    data: SportsFacilityCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_FACILITY_MANAGE))],
):
    return await sports_service.create_facility(db, tenant.tenant_id, data)


@sports_router.get(
    "/facilities/{facility_id}",
    response_model=SportsFacilityResponse,
    summary="Get sports facility by ID",
)
async def get_sports_facility(
    facility_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_FACILITY_READ))],
):
    return await sports_service.get_facility(db, tenant.tenant_id, facility_id)


@sports_router.put(
    "/facilities/{facility_id}",
    response_model=SportsFacilityResponse,
    summary="Update sports facility configuration",
)
async def update_sports_facility(
    facility_id: UUID,
    data: SportsFacilityUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_FACILITY_MANAGE))],
):
    return await sports_service.update_facility(db, tenant.tenant_id, facility_id, data)


@sports_router.get(
    "/facilities/{facility_id}/calendar",
    response_model=list[FacilityBookingResponse],
    summary="Get facility availability calendar within date range",
)
async def get_facility_calendar(
    facility_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_FACILITY_READ))],
    start_date: date = Query(...),
    end_date: date = Query(...),
):
    return await sports_service.list_facility_calendar(db, tenant.tenant_id, facility_id, start_date, end_date)


# =============================================================================
# 4. FACILITY BOOKINGS
# =============================================================================


@sports_router.get(
    "/facility-bookings",
    response_model=list[FacilityBookingResponse],
    summary="List facility bookings with conflict monitoring",
)
async def list_facility_bookings(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_FACILITY_READ))],
    facility_id: UUID | None = Query(None),
    booking_date: date | None = Query(None),
    booking_status: str | None = Query(None, alias="status"),
):
    return await sports_service.list_bookings(
        db, tenant.tenant_id, facility_id=facility_id, booking_date=booking_date, status=booking_status
    )


@sports_router.post(
    "/facility-bookings",
    response_model=FacilityBookingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Book a sports facility with automatic overlap detection",
)
async def create_facility_booking(
    data: FacilityBookingCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(SPORTS_BOOKING_CREATE))],
):
    if not data.booked_by_user_id:
        data.booked_by_user_id = user.id
    return await sports_service.create_booking(db, tenant.tenant_id, data)


@sports_router.post(
    "/facility-bookings/{booking_id}/cancel",
    response_model=FacilityBookingResponse,
    summary="Cancel a confirmed facility reservation",
)
async def cancel_facility_booking(
    booking_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_BOOKING_CANCEL))],
    cancellation_reason: str = Query(..., min_length=3),
):
    return await sports_service.cancel_booking(db, tenant.tenant_id, booking_id, cancellation_reason)


# =============================================================================
# 5. PARTICIPANTS (ATHLETES)
# =============================================================================


@sports_router.get(
    "/participants",
    response_model=list[SportsParticipantResponse],
    summary="List student athletes and recreation participants",
)
async def list_sports_participants(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_PARTICIPANT_READ))],
    sport: str | None = Query(None),
    participant_status: str | None = Query(None, alias="status"),
    clearance_status: str | None = Query(None),
):
    return await sports_service.list_participants(
        db, tenant.tenant_id, sport=sport, status=participant_status, clearance_status=clearance_status
    )


@sports_router.post(
    "/participants",
    response_model=SportsParticipantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register athlete / sports participant profile",
)
async def create_sports_participant(
    data: SportsParticipantCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_PARTICIPANT_MANAGE))],
):
    return await sports_service.create_participant(db, tenant.tenant_id, data)


@sports_router.get(
    "/participants/{participant_id}",
    response_model=SportsParticipantResponse,
    summary="Get athlete profile by ID",
)
async def get_sports_participant(
    participant_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_PARTICIPANT_READ))],
):
    return await sports_service.get_participant(db, tenant.tenant_id, participant_id)


@sports_router.put(
    "/participants/{participant_id}",
    response_model=SportsParticipantResponse,
    summary="Update athlete participation profile & clearance flags",
)
async def update_sports_participant(
    participant_id: UUID,
    data: SportsParticipantUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_PARTICIPANT_MANAGE))],
):
    return await sports_service.update_participant(db, tenant.tenant_id, participant_id, data)


# =============================================================================
# 6. TEAMS & ROSTERS
# =============================================================================


@sports_router.get(
    "/teams",
    response_model=list[SportsTeamResponse],
    summary="List athletic teams with active roster counts",
)
async def list_sports_teams(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_TEAM_READ))],
    sport: str | None = Query(None),
    category: str | None = Query(None),
    team_status: str | None = Query(None, alias="status"),
):
    team_tuples = await sports_service.list_teams(
        db, tenant.tenant_id, sport=sport, category=category, status=team_status
    )
    responses: list[SportsTeamResponse] = []
    for team, count in team_tuples:
        res = SportsTeamResponse.model_validate(team)
        res.roster_count = count
        responses.append(res)
    return responses


@sports_router.post(
    "/teams",
    response_model=SportsTeamResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create sports team",
)
async def create_sports_team(
    data: SportsTeamCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_TEAM_MANAGE))],
):
    team = await sports_service.create_team(db, tenant.tenant_id, data)
    res = SportsTeamResponse.model_validate(team)
    res.roster_count = 0
    return res


@sports_router.get(
    "/teams/{team_id}",
    response_model=SportsTeamResponse,
    summary="Get sports team details",
)
async def get_sports_team(
    team_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_TEAM_READ))],
):
    team = await sports_service.get_team(db, tenant.tenant_id, team_id)
    return SportsTeamResponse.model_validate(team)


@sports_router.put(
    "/teams/{team_id}",
    response_model=SportsTeamResponse,
    summary="Update sports team details",
)
async def update_sports_team(
    team_id: UUID,
    data: SportsTeamUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_TEAM_MANAGE))],
):
    team = await sports_service.update_team(db, tenant.tenant_id, team_id, data)
    return SportsTeamResponse.model_validate(team)


@sports_router.get(
    "/teams/{team_id}/roster",
    response_model=list[TeamMembershipResponse],
    summary="Get active roster for a sports team",
)
async def get_team_roster(
    team_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_TEAM_READ))],
):
    return await sports_service.get_team_roster(db, tenant.tenant_id, team_id)


@sports_router.post(
    "/teams/{team_id}/roster",
    response_model=TeamMembershipResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an athlete to team roster with capacity & clearance validation",
)
async def add_team_member(
    team_id: UUID,
    data: TeamMembershipCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(SPORTS_ROSTER_MANAGE))],
):
    if not data.approved_by_user_id:
        data.approved_by_user_id = user.id
    return await sports_service.add_team_member(db, tenant.tenant_id, team_id, data)


@sports_router.put(
    "/teams/roster/{membership_id}",
    response_model=TeamMembershipResponse,
    summary="Update roster membership (role, jersey, status)",
)
async def update_team_member(
    membership_id: UUID,
    data: TeamMembershipUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_ROSTER_MANAGE))],
):
    return await sports_service.update_team_member(db, tenant.tenant_id, membership_id, data)


# =============================================================================
# 7. COACHES & OFFICIALS
# =============================================================================


@sports_router.get(
    "/coaches",
    response_model=list[CoachingAssignmentResponse],
    summary="List coaching assignments",
)
async def list_coaches(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_TEAM_READ))],
    sport: str | None = Query(None),
    team_id: UUID | None = Query(None),
):
    return await sports_service.list_coaches(db, tenant.tenant_id, sport=sport, team_id=team_id)


@sports_router.post(
    "/coaches",
    response_model=CoachingAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Assign coach to team or sports discipline",
)
async def assign_coach(
    data: CoachingAssignmentCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_TEAM_MANAGE))],
):
    return await sports_service.assign_coach(db, tenant.tenant_id, data)


# =============================================================================
# 8. TRAINING PROGRAMS & SESSIONS
# =============================================================================


@sports_router.get(
    "/training-programs",
    response_model=list[TrainingProgramResponse],
    summary="List sports development and fitness training programs",
)
async def list_training_programs(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_TRAINING_READ))],
    sport: str | None = Query(None),
    is_active: bool | None = Query(None),
):
    return await sports_service.list_training_programs(db, tenant.tenant_id, sport=sport, is_active=is_active)


@sports_router.post(
    "/training-programs",
    response_model=TrainingProgramResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create training or fitness program",
)
async def create_training_program(
    data: TrainingProgramCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_TRAINING_MANAGE))],
):
    return await sports_service.create_training_program(db, tenant.tenant_id, data)


@sports_router.get(
    "/training-programs/{program_id}",
    response_model=TrainingProgramResponse,
    summary="Get training program details",
)
async def get_training_program(
    program_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_TRAINING_READ))],
):
    return await sports_service.get_training_program(db, tenant.tenant_id, program_id)


@sports_router.put(
    "/training-programs/{program_id}",
    response_model=TrainingProgramResponse,
    summary="Update training program",
)
async def update_training_program(
    program_id: UUID,
    data: TrainingProgramUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_TRAINING_MANAGE))],
):
    return await sports_service.update_training_program(db, tenant.tenant_id, program_id, data)


@sports_router.get(
    "/training-programs/{program_id}/sessions",
    response_model=list[TrainingSessionResponse],
    summary="List training sessions for a program",
)
async def list_training_sessions(
    program_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_TRAINING_READ))],
):
    return await sports_service.list_training_sessions(db, tenant.tenant_id, program_id)


@sports_router.post(
    "/training-sessions",
    response_model=TrainingSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Schedule training session with synchronized facility reservation",
)
async def create_training_session(
    data: TrainingSessionCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_TRAINING_MANAGE))],
):
    return await sports_service.create_training_session(db, tenant.tenant_id, data)


@sports_router.get(
    "/training-sessions/{session_id}/attendance",
    response_model=list[TrainingAttendanceResponse],
    summary="Get attendance records for training session",
)
async def get_session_attendance(
    session_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_TRAINING_READ))],
):
    return await sports_service.get_session_attendance(db, tenant.tenant_id, session_id)


@sports_router.post(
    "/training-sessions/{session_id}/attendance",
    response_model=list[TrainingAttendanceResponse],
    summary="Record bulk attendance for training session",
)
async def record_session_attendance(
    session_id: UUID,
    data: BulkAttendanceCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(SPORTS_ATTENDANCE_RECORD))],
):
    return await sports_service.record_session_attendance(
        db, tenant.tenant_id, data, recorded_by_user_id=user.id
    )


# =============================================================================
# 9. COMPETITIONS, FIXTURES & STANDINGS
# =============================================================================


@sports_router.get(
    "/competitions",
    response_model=list[CompetitionResponse],
    summary="List tournaments, leagues, and athletic competitions",
)
async def list_competitions(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_COMPETITION_READ))],
    sport: str | None = Query(None),
    comp_status: str | None = Query(None, alias="status"),
):
    comp_tuples = await sports_service.list_competitions(db, tenant.tenant_id, sport=sport, status=comp_status)
    responses: list[CompetitionResponse] = []
    for comp, count in comp_tuples:
        res = CompetitionResponse.model_validate(comp)
        res.registered_count = count
        responses.append(res)
    return responses


@sports_router.post(
    "/competitions",
    response_model=CompetitionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create tournament or athletic meet",
)
async def create_competition(
    data: CompetitionCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_COMPETITION_MANAGE))],
):
    comp = await sports_service.create_competition(db, tenant.tenant_id, data)
    res = CompetitionResponse.model_validate(comp)
    res.registered_count = 0
    return res


@sports_router.get(
    "/competitions/{competition_id}",
    response_model=CompetitionResponse,
    summary="Get tournament details",
)
async def get_competition(
    competition_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_COMPETITION_READ))],
):
    comp = await sports_service.get_competition(db, tenant.tenant_id, competition_id)
    return CompetitionResponse.model_validate(comp)


@sports_router.put(
    "/competitions/{competition_id}",
    response_model=CompetitionResponse,
    summary="Update competition configuration or rules",
)
async def update_competition(
    competition_id: UUID,
    data: CompetitionUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_COMPETITION_MANAGE))],
):
    comp = await sports_service.update_competition(db, tenant.tenant_id, competition_id, data)
    return CompetitionResponse.model_validate(comp)


@sports_router.get(
    "/competitions/{competition_id}/registrations",
    response_model=list[CompetitionRegistrationResponse],
    summary="List registered teams and athletes for competition",
)
async def list_competition_registrations(
    competition_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_COMPETITION_READ))],
):
    return await sports_service.list_competition_registrations(db, tenant.tenant_id, competition_id)


@sports_router.post(
    "/competitions/{competition_id}/registrations",
    response_model=CompetitionRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register team or athlete for a competition",
)
async def register_competition_entry(
    competition_id: UUID,
    data: CompetitionRegistrationCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_COMPETITION_REGISTER))],
):
    return await sports_service.register_competition_entry(db, tenant.tenant_id, competition_id, data)


@sports_router.post(
    "/competitions/{competition_id}/generate-fixtures",
    response_model=list[MatchFixtureResponse],
    summary="Generate tournament match fixtures automatically",
)
async def generate_competition_fixtures(
    competition_id: UUID,
    request: FixtureGenerationRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_MATCH_SCHEDULE))],
):
    request.competition_id = competition_id
    return await sports_service.generate_fixtures(db, tenant.tenant_id, request)


@sports_router.get(
    "/fixtures",
    response_model=list[MatchFixtureResponse],
    summary="List match fixtures with calendar filtering",
)
async def list_match_fixtures(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_COMPETITION_READ))],
    competition_id: UUID | None = Query(None),
    match_date: date | None = Query(None),
    fixture_status: str | None = Query(None, alias="status"),
):
    return await sports_service.list_fixtures(
        db, tenant.tenant_id, competition_id=competition_id, match_date=match_date, status=fixture_status
    )


@sports_router.put(
    "/fixtures/{fixture_id}",
    response_model=MatchFixtureResponse,
    summary="Update fixture schedule, venue or postponement reason",
)
async def update_match_fixture(
    fixture_id: UUID,
    data: MatchFixtureUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_MATCH_SCHEDULE))],
):
    return await sports_service.update_fixture(db, tenant.tenant_id, fixture_id, data)


@sports_router.post(
    "/fixtures/{fixture_id}/officials",
    response_model=MatchOfficialAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Assign match referee, umpire or scorekeeper",
)
async def assign_match_official(
    fixture_id: UUID,
    data: MatchOfficialAssignmentCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_MATCH_OFFICIATE))],
):
    data.fixture_id = fixture_id
    return await sports_service.assign_match_official(db, tenant.tenant_id, data)


@sports_router.post(
    "/fixtures/{fixture_id}/results",
    response_model=MatchResultResponse,
    summary="Record match scores and final result",
)
async def record_match_result(
    fixture_id: UUID,
    data: MatchResultCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(SPORTS_RESULT_RECORD))],
):
    data.fixture_id = fixture_id
    return await sports_service.record_match_result(db, tenant.tenant_id, data, recorded_by_user_id=user.id)


@sports_router.post(
    "/results/{result_id}/verify",
    response_model=MatchResultResponse,
    summary="Authorize and verify match result with audit log and standings update",
)
async def verify_match_result(
    result_id: UUID,
    verification: MatchResultVerify,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(SPORTS_RESULT_VERIFY))],
):
    return await sports_service.verify_match_result(
        db, tenant.tenant_id, result_id, verified_by_user_id=user.id, verify_data=verification
    )


@sports_router.get(
    "/competitions/{competition_id}/standings",
    response_model=list[CompetitionStandingResponse],
    summary="Get league points table / competition standings",
)
async def get_competition_standings(
    competition_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_COMPETITION_READ))],
):
    standing_tuples = await sports_service.get_competition_standings(db, tenant.tenant_id, competition_id)
    results: list[CompetitionStandingResponse] = []
    for s, team_name in standing_tuples:
        res = CompetitionStandingResponse.model_validate(s)
        res.team_name = team_name
        results.append(res)
    return results


# =============================================================================
# 10. ACHIEVEMENTS & AWARDS
# =============================================================================


@sports_router.get(
    "/achievements",
    response_model=list[SportsAchievementResponse],
    summary="List athletic awards, medals, and recognitions",
)
async def list_sports_achievements(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_REPORT_READ))],
    team_id: UUID | None = Query(None),
    participant_id: UUID | None = Query(None),
):
    return await sports_service.list_achievements(
        db, tenant.tenant_id, team_id=team_id, participant_id=participant_id
    )


@sports_router.post(
    "/achievements",
    response_model=SportsAchievementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Award trophy, medal or athletic honor",
)
async def create_sports_achievement(
    data: SportsAchievementCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_COMPETITION_MANAGE))],
):
    return await sports_service.create_achievement(db, tenant.tenant_id, data)


# =============================================================================
# 11. EQUIPMENT ASSIGNMENTS
# =============================================================================


@sports_router.get(
    "/equipment-assignments",
    response_model=list[EquipmentAssignmentResponse],
    summary="List sports equipment checkout log and status",
)
async def list_equipment_assignments(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_EQUIPMENT_READ))],
    status: str | None = Query(None),
    user_id: UUID | None = Query(None),
):
    return await sports_service.list_equipment_assignments(db, tenant.tenant_id, status=status, user_id=user_id)


@sports_router.post(
    "/equipment-assignments/checkout",
    response_model=EquipmentAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Check out sports gear and equipment",
)
async def checkout_equipment(
    data: EquipmentCheckoutCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_EQUIPMENT_MANAGE))],
):
    return await sports_service.checkout_equipment(db, tenant.tenant_id, data)


@sports_router.post(
    "/equipment-assignments/{assignment_id}/return",
    response_model=EquipmentAssignmentResponse,
    summary="Process equipment return, condition inspection, and damages",
)
async def return_equipment(
    assignment_id: UUID,
    data: EquipmentReturnRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[User, Depends(require_permission(SPORTS_EQUIPMENT_MANAGE))],
):
    return await sports_service.return_equipment(db, tenant.tenant_id, assignment_id, data)
