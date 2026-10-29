"""CampusOS Enterprise Sports, Athletics, Recreation & Student Fitness Schemas (Step 57).

CampusOS Tagline: "One Campus. One System. One Source of Truth."
"""

from datetime import date, datetime, time
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.sports import (
    AchievementType,
    ActivityCategory,
    AttendanceStatus,
    BookingPurpose,
    BookingStatus,
    CheckoutStatus,
    ClearanceStatus,
    CoachingRole,
    CompetitionStatus,
    CompetitionType,
    DepartmentStatus,
    EquipmentCondition,
    FacilityStatus,
    FacilitySurface,
    FacilityType,
    FixtureStatus,
    MaintenanceType,
    MatchStage,
    MemberRole,
    OfficialAssignmentStatus,
    OfficialRole,
    ParticipantStatus,
    ProgramType,
    RecognitionLevel,
    RegistrationType,
    RosterStatus,
    SessionStatus,
    StandingCalculationType,
    TeamStatus,
    TournamentFormat,
)

# =============================================================================
# 1. SPORTS DEPARTMENT SCHEMAS
# =============================================================================


class SportsDepartmentBase(BaseModel):
    code: str = Field(..., max_length=32)
    name: str = Field(..., max_length=128)
    campus_id: UUID | None = None
    description: str | None = None
    status: DepartmentStatus = DepartmentStatus.ACTIVE
    head_user_id: UUID | None = None
    operating_hours: dict[str, Any] | None = None
    policies: dict[str, Any] | None = None


class SportsDepartmentCreate(SportsDepartmentBase):
    pass


class SportsDepartmentUpdate(BaseModel):
    name: str | None = None
    campus_id: UUID | None = None
    description: str | None = None
    status: DepartmentStatus | None = None
    head_user_id: UUID | None = None
    operating_hours: dict[str, Any] | None = None
    policies: dict[str, Any] | None = None


class SportsDepartmentResponse(SportsDepartmentBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 2. SPORTS FACILITY SCHEMAS
# =============================================================================


class SportsFacilityBase(BaseModel):
    code: str = Field(..., max_length=32)
    name: str = Field(..., max_length=128)
    campus_id: UUID | None = None
    department_id: UUID | None = None
    facility_type: FacilityType = FacilityType.OUTDOOR_GROUND
    surface: FacilitySurface = FacilitySurface.GRASS
    is_indoor: bool = False
    capacity: int = Field(default=50, ge=1)
    location_details: str | None = None
    operating_hours: dict[str, Any] | None = None
    status: FacilityStatus = FacilityStatus.AVAILABLE
    asset_id: UUID | None = None
    equipment_requirements: dict[str, Any] | None = None
    accessibility_features: dict[str, Any] | None = None
    maintenance_status: MaintenanceType = MaintenanceType.GOOD
    last_inspected_at: datetime | None = None
    closure_reason: str | None = None


class SportsFacilityCreate(SportsFacilityBase):
    pass


class SportsFacilityUpdate(BaseModel):
    name: str | None = None
    campus_id: UUID | None = None
    department_id: UUID | None = None
    facility_type: FacilityType | None = None
    surface: FacilitySurface | None = None
    is_indoor: bool | None = None
    capacity: int | None = None
    location_details: str | None = None
    operating_hours: dict[str, Any] | None = None
    status: FacilityStatus | None = None
    asset_id: UUID | None = None
    equipment_requirements: dict[str, Any] | None = None
    accessibility_features: dict[str, Any] | None = None
    maintenance_status: MaintenanceType | None = None
    last_inspected_at: datetime | None = None
    closure_reason: str | None = None


class SportsFacilityResponse(SportsFacilityBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 3. FACILITY BOOKING SCHEMAS
# =============================================================================


class FacilityBookingBase(BaseModel):
    facility_id: UUID
    booking_date: date
    start_time: time
    end_time: time
    purpose: BookingPurpose = BookingPurpose.TRAINING
    title: str = Field(..., max_length=128)
    team_id: UUID | None = None
    competition_id: UUID | None = None
    training_program_id: UUID | None = None
    is_maintenance_block: bool = False
    notes: str | None = None


class FacilityBookingCreate(FacilityBookingBase):
    booked_by_user_id: UUID | None = None


class FacilityBookingUpdate(BaseModel):
    status: BookingStatus | None = None
    cancellation_reason: str | None = None
    notes: str | None = None


class FacilityBookingResponse(FacilityBookingBase):
    id: UUID
    tenant_id: UUID
    booked_by_user_id: UUID | None = None
    status: BookingStatus
    cancellation_reason: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FacilitySlotAvailability(BaseModel):
    facility_id: UUID
    facility_name: str
    booking_date: date
    is_available: bool
    conflicting_bookings: list[FacilityBookingResponse] = []


# =============================================================================
# 4. PARTICIPANT SCHEMAS
# =============================================================================


class SportsParticipantBase(BaseModel):
    user_id: UUID
    student_id: UUID | None = None
    participant_code: str = Field(..., max_length=32)
    primary_sport: str = Field(..., max_length=64)
    status: ParticipantStatus = ParticipantStatus.ACTIVE
    clearance_status: ClearanceStatus = ClearanceStatus.CLEARED
    clearance_expiry: date | None = None
    consent_recorded: bool = True
    operational_restrictions: dict[str, Any] | None = None
    sports_history: dict[str, Any] | None = None


class SportsParticipantCreate(SportsParticipantBase):
    pass


class SportsParticipantUpdate(BaseModel):
    primary_sport: str | None = None
    status: ParticipantStatus | None = None
    clearance_status: ClearanceStatus | None = None
    clearance_expiry: date | None = None
    consent_recorded: bool | None = None
    operational_restrictions: dict[str, Any] | None = None
    sports_history: dict[str, Any] | None = None


class SportsParticipantResponse(SportsParticipantBase):
    id: UUID
    tenant_id: UUID
    consent_recorded_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 5. TEAM & ROSTER SCHEMAS
# =============================================================================


class SportsTeamBase(BaseModel):
    code: str = Field(..., max_length=32)
    name: str = Field(..., max_length=128)
    sport: str = Field(..., max_length=64)
    department_id: UUID | None = None
    category: ActivityCategory = ActivityCategory.VARSITY
    gender_category: str = "COED"
    captain_participant_id: UUID | None = None
    head_coach_user_id: UUID | None = None
    max_roster_size: int = Field(default=25, ge=1)
    status: TeamStatus = TeamStatus.ACTIVE


class SportsTeamCreate(SportsTeamBase):
    pass


class SportsTeamUpdate(BaseModel):
    name: str | None = None
    sport: str | None = None
    department_id: UUID | None = None
    category: ActivityCategory | None = None
    gender_category: str | None = None
    captain_participant_id: UUID | None = None
    head_coach_user_id: UUID | None = None
    max_roster_size: int | None = None
    status: TeamStatus | None = None


class SportsTeamResponse(SportsTeamBase):
    id: UUID
    tenant_id: UUID
    roster_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TeamMembershipBase(BaseModel):
    team_id: UUID
    participant_id: UUID
    role: MemberRole = MemberRole.PLAYER
    jersey_number: int | None = None
    position: str | None = None
    status: RosterStatus = RosterStatus.ACTIVE


class TeamMembershipCreate(TeamMembershipBase):
    approved_by_user_id: UUID | None = None


class TeamMembershipUpdate(BaseModel):
    role: MemberRole | None = None
    jersey_number: int | None = None
    position: str | None = None
    status: RosterStatus | None = None


class TeamMembershipResponse(TeamMembershipBase):
    id: UUID
    tenant_id: UUID
    joined_at: datetime
    left_at: datetime | None = None
    approved_by_user_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 6. COACHING ASSIGNMENTS
# =============================================================================


class CoachingAssignmentBase(BaseModel):
    team_id: UUID | None = None
    user_id: UUID
    role: CoachingRole = CoachingRole.HEAD_COACH
    sport: str = Field(..., max_length=64)
    qualification: str | None = None
    is_active: bool = True
    assigned_from: date
    assigned_to: date | None = None


class CoachingAssignmentCreate(CoachingAssignmentBase):
    pass


class CoachingAssignmentResponse(CoachingAssignmentBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 7. TRAINING PROGRAMS & SESSIONS
# =============================================================================


class TrainingProgramBase(BaseModel):
    code: str = Field(..., max_length=32)
    name: str = Field(..., max_length=128)
    department_id: UUID | None = None
    program_type: ProgramType = ProgramType.DEVELOPMENT
    sport: str = Field(..., max_length=64)
    description: str | None = None
    lead_coach_user_id: UUID | None = None
    facility_id: UUID | None = None
    capacity: int = Field(default=30, ge=1)
    start_date: date
    end_date: date
    registration_deadline: date | None = None
    is_active: bool = True
    fee_amount: Decimal = Decimal("0.00")


class TrainingProgramCreate(TrainingProgramBase):
    pass


class TrainingProgramUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    lead_coach_user_id: UUID | None = None
    facility_id: UUID | None = None
    capacity: int | None = None
    end_date: date | None = None
    is_active: bool | None = None
    fee_amount: Decimal | None = None


class TrainingProgramResponse(TrainingProgramBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TrainingSessionBase(BaseModel):
    program_id: UUID
    facility_id: UUID | None = None
    session_date: date
    start_time: time
    end_time: time
    title: str = Field(..., max_length=128)
    status: SessionStatus = SessionStatus.SCHEDULED
    cancellation_reason: str | None = None


class TrainingSessionCreate(TrainingSessionBase):
    pass


class TrainingSessionResponse(TrainingSessionBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TrainingAttendanceBase(BaseModel):
    session_id: UUID
    participant_id: UUID
    status: AttendanceStatus = AttendanceStatus.PRESENT
    notes: str | None = None


class TrainingAttendanceCreate(TrainingAttendanceBase):
    check_in_time: datetime | None = None
    recorded_by_user_id: UUID | None = None


class BulkAttendanceItem(BaseModel):
    participant_id: UUID
    status: AttendanceStatus = AttendanceStatus.PRESENT
    notes: str | None = None


class BulkAttendanceCreate(BaseModel):
    session_id: UUID
    records: list[BulkAttendanceItem]


class TrainingAttendanceResponse(TrainingAttendanceBase):
    id: UUID
    tenant_id: UUID
    check_in_time: datetime | None = None
    recorded_by_user_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 8. COMPETITION, FIXTURES & STANDINGS
# =============================================================================


class CompetitionBase(BaseModel):
    code: str = Field(..., max_length=32)
    name: str = Field(..., max_length=128)
    campus_id: UUID | None = None
    department_id: UUID | None = None
    competition_type: CompetitionType = CompetitionType.INTERNAL
    tournament_format: TournamentFormat = TournamentFormat.SINGLE_ELIMINATION
    sport: str = Field(..., max_length=64)
    registration_type: RegistrationType = RegistrationType.TEAM
    standing_rule: StandingCalculationType = StandingCalculationType.STANDARD_POINTS
    points_for_win: int = 3
    points_for_draw: int = 1
    points_for_loss: int = 0
    start_date: date
    end_date: date
    registration_deadline: date
    max_participants: int = Field(default=16, ge=2)
    fee_amount: Decimal = Decimal("0.00")
    rules_config: dict[str, Any] | None = None


class CompetitionCreate(CompetitionBase):
    pass


class CompetitionUpdate(BaseModel):
    name: str | None = None
    status: CompetitionStatus | None = None
    rules_config: dict[str, Any] | None = None
    max_participants: int | None = None
    end_date: date | None = None


class CompetitionResponse(CompetitionBase):
    id: UUID
    tenant_id: UUID
    status: CompetitionStatus
    registered_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompetitionRegistrationBase(BaseModel):
    competition_id: UUID
    team_id: UUID | None = None
    participant_id: UUID | None = None
    seed_number: int | None = None


class CompetitionRegistrationCreate(CompetitionRegistrationBase):
    pass


class CompetitionRegistrationResponse(CompetitionRegistrationBase):
    id: UUID
    tenant_id: UUID
    registered_at: datetime
    status: str
    invoice_id: UUID | None = None
    payment_status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MatchFixtureBase(BaseModel):
    competition_id: UUID
    match_number: str = Field(..., max_length=32)
    stage: MatchStage = MatchStage.GROUP_STAGE
    round_number: int = 1
    home_team_id: UUID | None = None
    away_team_id: UUID | None = None
    home_participant_id: UUID | None = None
    away_participant_id: UUID | None = None
    facility_id: UUID | None = None
    match_date: date
    start_time: time
    end_time: time
    status: FixtureStatus = FixtureStatus.SCHEDULED
    postponement_reason: str | None = None


class MatchFixtureCreate(MatchFixtureBase):
    pass


class MatchFixtureUpdate(BaseModel):
    facility_id: UUID | None = None
    match_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    status: FixtureStatus | None = None
    postponement_reason: str | None = None


class MatchFixtureResponse(MatchFixtureBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FixtureGenerationRequest(BaseModel):
    competition_id: UUID
    facility_ids: list[UUID] = []
    start_date: date
    default_start_time: time = time(14, 0)
    match_duration_minutes: int = 90


class MatchOfficialAssignmentBase(BaseModel):
    fixture_id: UUID
    user_id: UUID
    role: OfficialRole = OfficialRole.REFEREE
    status: OfficialAssignmentStatus = OfficialAssignmentStatus.ASSIGNED
    notes: str | None = None


class MatchOfficialAssignmentCreate(MatchOfficialAssignmentBase):
    pass


class MatchOfficialAssignmentResponse(MatchOfficialAssignmentBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MatchResultBase(BaseModel):
    fixture_id: UUID
    home_score: int = Field(default=0, ge=0)
    away_score: int = Field(default=0, ge=0)
    winning_team_id: UUID | None = None
    winning_participant_id: UUID | None = None
    is_draw: bool = False
    is_forfeit: bool = False
    forfeit_team_id: UUID | None = None
    score_breakdown: dict[str, Any] | None = None


class MatchResultCreate(MatchResultBase):
    pass


class MatchResultVerify(BaseModel):
    is_verified: bool = True
    correction_reason: str | None = None


class MatchResultResponse(MatchResultBase):
    id: UUID
    tenant_id: UUID
    recorded_by_user_id: UUID
    recorded_at: datetime
    verified_by_user_id: UUID | None = None
    verified_at: datetime | None = None
    is_verified: bool
    correction_reason: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompetitionStandingResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    competition_id: UUID
    team_id: UUID | None = None
    participant_id: UUID | None = None
    team_name: str | None = None
    played: int
    won: int
    drawn: int
    lost: int
    points_for: int
    points_against: int
    bonus_points: int
    total_points: int
    rank: int

    model_config = ConfigDict(from_attributes=True)


class SportsAchievementBase(BaseModel):
    competition_id: UUID | None = None
    team_id: UUID | None = None
    participant_id: UUID | None = None
    achievement_type: AchievementType = AchievementType.CHAMPION
    recognition_level: RecognitionLevel = RecognitionLevel.INSTITUTIONAL
    title: str = Field(..., max_length=128)
    citation: str | None = None
    awarded_date: date
    is_published: bool = True


class SportsAchievementCreate(SportsAchievementBase):
    pass


class SportsAchievementResponse(SportsAchievementBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 9. EQUIPMENT ASSIGNMENTS
# =============================================================================


class EquipmentAssignmentBase(BaseModel):
    asset_id: UUID | None = None
    equipment_name: str = Field(..., max_length=128)
    sport: str = Field(..., max_length=64)
    quantity: int = Field(default=1, ge=1)
    assigned_to_user_id: UUID
    team_id: UUID | None = None
    facility_id: UUID | None = None
    due_date: date
    checkout_condition: EquipmentCondition = EquipmentCondition.GOOD


class EquipmentCheckoutCreate(EquipmentAssignmentBase):
    pass


class EquipmentReturnRequest(BaseModel):
    return_condition: EquipmentCondition
    damage_notes: str | None = None
    replacement_fee: Decimal | None = None


class EquipmentAssignmentResponse(EquipmentAssignmentBase):
    id: UUID
    tenant_id: UUID
    issued_at: datetime
    returned_at: datetime | None = None
    return_condition: EquipmentCondition | None = None
    status: CheckoutStatus
    damage_notes: str | None = None
    replacement_fee: Decimal | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 10. OPERATIONS DASHBOARD & ANALYTICS
# =============================================================================


class SportsDashboardSummary(BaseModel):
    total_facilities: int = 0
    available_facilities: int = 0
    total_teams: int = 0
    total_athletes: int = 0
    active_competitions: int = 0
    upcoming_fixtures: int = 0
    active_training_programs: int = 0
    equipment_checked_out: int = 0
    equipment_overdue: int = 0
