"""SQLAlchemy Entities for Enterprise Sports, Athletics, Recreation & Student Fitness Management (Step 57).

Product Principle: "One Campus. One System. One Source of Truth."

Coordinates institutional sports administration, recreation centers, multi-venue facilities and courts,
student athlete and participant rosters, coaching assignments, training camps and attendance,
tournaments and competition fixtures, match scoring and verified standings, sports achievements,
equipment checkout, and finance invoicing.
"""

from datetime import date, datetime, time
from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantScopedModel

# Cross-dialect JSON type for PostgreSQL JSONB and SQLite JSON
JSONType = JSON().with_variant(JSONB, "postgresql")


# =============================================================================
# 1. ENUMS & DOMAIN CONSTANTS
# =============================================================================


class DepartmentStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"


class ActivityCategory(StrEnum):
    VARSITY = "VARSITY"
    INTRAMURAL = "INTRAMURAL"
    CLUB = "CLUB"
    RECREATIONAL = "RECREATIONAL"
    FITNESS = "FITNESS"
    COMPETITIVE = "COMPETITIVE"


class EligibilityRuleType(StrEnum):
    ACADEMIC_CGPA = "ACADEMIC_CGPA"
    MIN_ATTENDANCE = "MIN_ATTENDANCE"
    HEALTH_CLEARANCE = "HEALTH_CLEARANCE"
    MAX_SEASONS = "MAX_SEASONS"
    DISCIPLINARY_CLEAN = "DISCIPLINARY_CLEAN"


class FacilityType(StrEnum):
    CRICKET_GROUND = "CRICKET_GROUND"
    FOOTBALL_FIELD = "FOOTBALL_FIELD"
    BASKETBALL_COURT = "BASKETBALL_COURT"
    VOLLEYBALL_COURT = "VOLLEYBALL_COURT"
    BADMINTON_COURT = "BADMINTON_COURT"
    TENNIS_COURT = "TENNIS_COURT"
    SWIMMING_POOL = "SWIMMING_POOL"
    GYMNASIUM = "GYMNASIUM"
    INDOOR_HALL = "INDOOR_HALL"
    ATHLETIC_TRACK = "ATHLETIC_TRACK"
    RECREATION_ROOM = "RECREATION_ROOM"
    OUTDOOR_GROUND = "OUTDOOR_GROUND"
    OTHER = "OTHER"


class FacilitySurface(StrEnum):
    GRASS = "GRASS"
    TURF = "TURF"
    WOOD = "WOOD"
    SYNTHETIC = "SYNTHETIC"
    CLAY = "CLAY"
    CONCRETE = "CONCRETE"
    WATER = "WATER"
    OTHER = "OTHER"


class FacilityStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    MAINTENANCE_CLOSED = "MAINTENANCE_CLOSED"
    RENOVATION = "RENOVATION"
    INACTIVE = "INACTIVE"


class MaintenanceType(StrEnum):
    GOOD = "GOOD"
    ROUTINE = "ROUTINE"
    REPAIR_REQUIRED = "REPAIR_REQUIRED"
    CRITICAL = "CRITICAL"


class BookingPurpose(StrEnum):
    TRAINING = "TRAINING"
    INTRAMURAL_MATCH = "INTRAMURAL_MATCH"
    TOURNAMENT = "TOURNAMENT"
    RECREATIONAL = "RECREATIONAL"
    MAINTENANCE = "MAINTENANCE"
    CAMPUS_EVENT = "CAMPUS_EVENT"


class BookingStatus(StrEnum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class ParticipantStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    GRADUATED = "GRADUATED"


class ClearanceStatus(StrEnum):
    CLEARED = "CLEARED"
    PENDING_REVIEW = "PENDING_REVIEW"
    RESTRICTED = "RESTRICTED"
    EXPIRED = "EXPIRED"
    SUSPENDED = "SUSPENDED"


class TeamStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DISBANDED = "DISBANDED"


class MemberRole(StrEnum):
    CAPTAIN = "CAPTAIN"
    VICE_CAPTAIN = "VICE_CAPTAIN"
    PLAYER = "PLAYER"
    RESERVE = "RESERVE"


class RosterStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    INJURED_RESERVE = "INJURED_RESERVE"
    TRANSFERRED = "TRANSFERRED"


class CoachingRole(StrEnum):
    HEAD_COACH = "HEAD_COACH"
    ASSISTANT_COACH = "ASSISTANT_COACH"
    FITNESS_TRAINER = "FITNESS_TRAINER"
    PHYSIOTHERAPIST = "PHYSIOTHERAPIST"
    COORDINATOR = "COORDINATOR"


class ProgramType(StrEnum):
    CAMP = "CAMP"
    DEVELOPMENT = "DEVELOPMENT"
    FITNESS_CLASS = "FITNESS_CLASS"
    RECREATIONAL = "RECREATIONAL"
    BOOTCAMP = "BOOTCAMP"


class SessionStatus(StrEnum):
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    RESCHEDULED = "RESCHEDULED"


class AttendanceStatus(StrEnum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    EXCUSED = "EXCUSED"
    LATE = "LATE"


class CompetitionType(StrEnum):
    INTERNAL = "INTERNAL"
    INTER_COLLEGIATE = "INTER_COLLEGIATE"
    STATE = "STATE"
    NATIONAL = "NATIONAL"
    INVITATIONAL = "INVITATIONAL"


class TournamentFormat(StrEnum):
    SINGLE_ELIMINATION = "SINGLE_ELIMINATION"
    DOUBLE_ELIMINATION = "DOUBLE_ELIMINATION"
    ROUND_ROBIN = "ROUND_ROBIN"
    LEAGUE_CUM_KNOCKOUT = "LEAGUE_CUM_KNOCKOUT"


class RegistrationType(StrEnum):
    TEAM = "TEAM"
    INDIVIDUAL = "INDIVIDUAL"


class CompetitionStatus(StrEnum):
    DRAFT = "DRAFT"
    REGISTRATION_OPEN = "REGISTRATION_OPEN"
    REGISTRATION_CLOSED = "REGISTRATION_CLOSED"
    FIXTURES_PUBLISHED = "FIXTURES_PUBLISHED"
    ONGOING = "ONGOING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class MatchStage(StrEnum):
    ROUND_OF_32 = "ROUND_OF_32"
    ROUND_OF_16 = "ROUND_OF_16"
    QUARTER_FINAL = "QUARTER_FINAL"
    SEMI_FINAL = "SEMI_FINAL"
    THIRD_PLACE = "THIRD_PLACE"
    FINAL = "FINAL"
    GROUP_STAGE = "GROUP_STAGE"


class FixtureStatus(StrEnum):
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    POSTPONED = "POSTPONED"
    CANCELLED = "CANCELLED"
    FORFEITED = "FORFEITED"


class OfficialRole(StrEnum):
    REFEREE = "REFEREE"
    UMPIRE = "UMPIRE"
    LINESMAN = "LINESMAN"
    TIMEKEEPER = "TIMEKEEPER"
    SCORER = "SCORER"
    TABLE_OFFICIAL = "TABLE_OFFICIAL"


class OfficialAssignmentStatus(StrEnum):
    ASSIGNED = "ASSIGNED"
    CONFIRMED = "CONFIRMED"
    DECLINED = "DECLINED"
    CHECKED_IN = "CHECKED_IN"


class StandingCalculationType(StrEnum):
    STANDARD_POINTS = "STANDARD_POINTS"
    PERCENTAGE = "PERCENTAGE"
    CUSTOM = "CUSTOM"


class AchievementType(StrEnum):
    CHAMPION = "CHAMPION"
    RUNNER_UP = "RUNNER_UP"
    THIRD_PLACE = "THIRD_PLACE"
    MVP = "MVP"
    BEST_DEFENDER = "BEST_DEFENDER"
    RECORD_BREAKER = "RECORD_BREAKER"
    FAIR_PLAY = "FAIR_PLAY"


class RecognitionLevel(StrEnum):
    INSTITUTIONAL = "INSTITUTIONAL"
    DISTRICT = "DISTRICT"
    UNIVERSITY = "UNIVERSITY"
    STATE = "STATE"
    NATIONAL = "NATIONAL"


class EquipmentCondition(StrEnum):
    NEW = "NEW"
    GOOD = "GOOD"
    FAIR = "FAIR"
    DAMAGED = "DAMAGED"
    DESTROYED = "DESTROYED"
    LOST = "LOST"


class CheckoutStatus(StrEnum):
    CHECKED_OUT = "CHECKED_OUT"
    RETURNED = "RETURNED"
    OVERDUE = "OVERDUE"
    DAMAGED = "DAMAGED"
    LOST = "LOST"


# =============================================================================
# 2. DEPARTMENT & FACILITY MODELS
# =============================================================================


class SportsDepartment(TenantScopedModel):
    """Institutional sports department, recreation center, or athletic unit."""

    __tablename__ = "sports_departments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_sports_departments_tenant_code"),
        Index("idx_sports_dept_tenant", "tenant_id", "campus_id"),
    )

    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="SET NULL"),
        nullable=True,
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[DepartmentStatus] = mapped_column(
        String(32), default=DepartmentStatus.ACTIVE, nullable=False
    )
    head_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    operating_hours: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    policies: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)

    facilities: Mapped[list["SportsFacility"]] = relationship(
        "SportsFacility", back_populates="department", cascade="all, delete-orphan"
    )
    teams: Mapped[list["SportsTeam"]] = relationship(
        "SportsTeam", back_populates="department"
    )


class SportsFacility(TenantScopedModel):
    """Sports grounds, courts, tracks, pools, and gymnasiums."""

    __tablename__ = "sports_facilities"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_sports_facilities_tenant_code"),
        Index("idx_sports_facilities_lookup", "tenant_id", "status", "facility_type"),
    )

    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="SET NULL"),
        nullable=True,
    )
    department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports_departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    facility_type: Mapped[FacilityType] = mapped_column(
        String(32), default=FacilityType.OUTDOOR_GROUND, nullable=False
    )
    surface: Mapped[FacilitySurface] = mapped_column(
        String(32), default=FacilitySurface.GRASS, nullable=False
    )
    is_indoor: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    location_details: Mapped[str | None] = mapped_column(String(255), nullable=True)
    operating_hours: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    status: Mapped[FacilityStatus] = mapped_column(
        String(32), default=FacilityStatus.AVAILABLE, nullable=False
    )
    asset_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("asset_registry.id", ondelete="SET NULL"),
        nullable=True,
    )
    equipment_requirements: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    accessibility_features: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    maintenance_status: Mapped[MaintenanceType] = mapped_column(
        String(32), default=MaintenanceType.GOOD, nullable=False
    )
    last_inspected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    department: Mapped["SportsDepartment | None"] = relationship(
        "SportsDepartment", back_populates="facilities"
    )
    bookings: Mapped[list["FacilityBooking"]] = relationship(
        "FacilityBooking", back_populates="facility", cascade="all, delete-orphan"
    )


class FacilityBooking(TenantScopedModel):
    """Time-slot reservation for a facility with overlap prevention."""

    __tablename__ = "sports_facility_bookings"
    __table_args__ = (
        Index("idx_sports_fac_booking_slot", "tenant_id", "facility_id", "booking_date", "status"),
    )

    facility_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports_facilities.id", ondelete="CASCADE"),
        nullable=False,
    )
    booking_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    purpose: Mapped[BookingPurpose] = mapped_column(
        String(32), default=BookingPurpose.TRAINING, nullable=False
    )
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    booked_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    team_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    competition_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    training_program_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    status: Mapped[BookingStatus] = mapped_column(
        String(32), default=BookingStatus.CONFIRMED, nullable=False
    )
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_maintenance_block: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    facility: Mapped["SportsFacility"] = relationship("SportsFacility", back_populates="bookings")


# =============================================================================
# 3. PARTICIPANTS, TEAMS & ROSTERS
# =============================================================================


class SportsParticipant(TenantScopedModel):
    """Participant or student-athlete profile with clearance and privacy tracking."""

    __tablename__ = "sports_participants"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", name="uq_sports_participants_tenant_user"),
        UniqueConstraint("tenant_id", "participant_code", name="uq_sports_participants_tenant_code"),
        Index("idx_sports_participant_lookup", "tenant_id", "primary_sport", "status"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="SET NULL"),
        nullable=True,
    )
    participant_code: Mapped[str] = mapped_column(String(32), nullable=False)
    primary_sport: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[ParticipantStatus] = mapped_column(
        String(32), default=ParticipantStatus.ACTIVE, nullable=False
    )
    clearance_status: Mapped[ClearanceStatus] = mapped_column(
        String(32), default=ClearanceStatus.CLEARED, nullable=False
    )
    clearance_expiry: Mapped[date | None] = mapped_column(Date, nullable=True)
    consent_recorded: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    consent_recorded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    operational_restrictions: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    sports_history: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)

    memberships: Mapped[list["TeamMembership"]] = relationship(
        "TeamMembership", back_populates="participant", cascade="all, delete-orphan"
    )


class SportsTeam(TenantScopedModel):
    """Athletic or recreational team."""

    __tablename__ = "sports_teams"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_sports_teams_tenant_code"),
        Index("idx_sports_teams_lookup", "tenant_id", "sport", "category"),
    )

    department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports_departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    sport: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[ActivityCategory] = mapped_column(
        String(32), default=ActivityCategory.VARSITY, nullable=False
    )
    gender_category: Mapped[str] = mapped_column(String(32), default="COED", nullable=False)
    captain_participant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports_participants.id", ondelete="SET NULL"),
        nullable=True,
    )
    head_coach_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    max_roster_size: Mapped[int] = mapped_column(Integer, default=25, nullable=False)
    status: Mapped[TeamStatus] = mapped_column(
        String(32), default=TeamStatus.ACTIVE, nullable=False
    )

    department: Mapped["SportsDepartment | None"] = relationship("SportsDepartment", back_populates="teams")
    memberships: Mapped[list["TeamMembership"]] = relationship(
        "TeamMembership", back_populates="team", cascade="all, delete-orphan"
    )
    coaching_assignments: Mapped[list["CoachingAssignment"]] = relationship(
        "CoachingAssignment", back_populates="team"
    )


class TeamMembership(TenantScopedModel):
    """Roster record linking participant to team with jersey number and status."""

    __tablename__ = "sports_team_memberships"
    __table_args__ = (
        UniqueConstraint("tenant_id", "team_id", "participant_id", name="uq_sports_team_memberships_unique"),
    )

    team_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports_teams.id", ondelete="CASCADE"),
        nullable=False,
    )
    participant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports_participants.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[MemberRole] = mapped_column(String(32), default=MemberRole.PLAYER, nullable=False)
    jersey_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    position: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[RosterStatus] = mapped_column(
        String(32), default=RosterStatus.ACTIVE, nullable=False
    )
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    team: Mapped["SportsTeam"] = relationship("SportsTeam", back_populates="memberships")
    participant: Mapped["SportsParticipant"] = relationship("SportsParticipant", back_populates="memberships")


class CoachingAssignment(TenantScopedModel):
    """Coaching, trainer, and support staff assignments."""

    __tablename__ = "sports_coaching_assignments"

    team_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports_teams.id", ondelete="CASCADE"),
        nullable=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[CoachingRole] = mapped_column(
        String(32), default=CoachingRole.HEAD_COACH, nullable=False
    )
    sport: Mapped[str] = mapped_column(String(64), nullable=False)
    qualification: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    assigned_from: Mapped[date] = mapped_column(Date, nullable=False)
    assigned_to: Mapped[date | None] = mapped_column(Date, nullable=True)

    team: Mapped["SportsTeam | None"] = relationship("SportsTeam", back_populates="coaching_assignments")


# =============================================================================
# 4. TRAINING PROGRAMS, SESSIONS & ATTENDANCE
# =============================================================================


class SportsTrainingProgram(TenantScopedModel):
    """Training camp, recreational course, or fitness academy program."""

    __tablename__ = "sports_training_programs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_sports_training_programs_tenant_code"),
    )

    department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports_departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    program_type: Mapped[ProgramType] = mapped_column(
        String(32), default=ProgramType.DEVELOPMENT, nullable=False
    )
    sport: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    lead_coach_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    facility_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports_facilities.id", ondelete="SET NULL"),
        nullable=True,
    )
    capacity: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    registration_deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    fee_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)

    sessions: Mapped[list["TrainingSession"]] = relationship(
        "TrainingSession", back_populates="program", cascade="all, delete-orphan"
    )


TrainingProgram = SportsTrainingProgram


class TrainingSession(TenantScopedModel):
    """Specific scheduled date/time training session."""

    __tablename__ = "sports_training_sessions"

    program_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports_training_programs.id", ondelete="CASCADE"),
        nullable=False,
    )
    facility_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports_facilities.id", ondelete="SET NULL"),
        nullable=True,
    )
    session_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[SessionStatus] = mapped_column(
        String(32), default=SessionStatus.SCHEDULED, nullable=False
    )
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    program: Mapped["SportsTrainingProgram"] = relationship("SportsTrainingProgram", back_populates="sessions")
    attendances: Mapped[list["TrainingAttendance"]] = relationship(
        "TrainingAttendance", back_populates="session", cascade="all, delete-orphan"
    )


class TrainingAttendance(TenantScopedModel):
    """Participant attendance verification for a training session."""

    __tablename__ = "sports_training_attendances"
    __table_args__ = (
        UniqueConstraint("tenant_id", "session_id", "participant_id", name="uq_sports_train_att_unique"),
    )

    session_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports_training_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    participant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports_participants.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[AttendanceStatus] = mapped_column(
        String(32), default=AttendanceStatus.PRESENT, nullable=False
    )
    check_in_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    recorded_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)

    session: Mapped["TrainingSession"] = relationship("TrainingSession", back_populates="attendances")


# =============================================================================
# 5. COMPETITIONS, FIXTURES, RESULTS & STANDINGS
# =============================================================================


class Competition(TenantScopedModel):
    """Tournament, sports league, or championship meet."""

    __tablename__ = "sports_competitions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_sports_competitions_tenant_code"),
        Index("idx_sports_comp_lookup", "tenant_id", "sport", "status"),
    )

    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="SET NULL"),
        nullable=True,
    )
    department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports_departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    competition_type: Mapped[CompetitionType] = mapped_column(
        String(32), default=CompetitionType.INTERNAL, nullable=False
    )
    tournament_format: Mapped[TournamentFormat] = mapped_column(
        String(32), default=TournamentFormat.SINGLE_ELIMINATION, nullable=False
    )
    sport: Mapped[str] = mapped_column(String(64), nullable=False)
    registration_type: Mapped[RegistrationType] = mapped_column(
        String(32), default=RegistrationType.TEAM, nullable=False
    )
    standing_rule: Mapped[StandingCalculationType] = mapped_column(
        String(32), default=StandingCalculationType.STANDARD_POINTS, nullable=False
    )
    points_for_win: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    points_for_draw: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    points_for_loss: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    registration_deadline: Mapped[date] = mapped_column(Date, nullable=False)
    max_participants: Mapped[int] = mapped_column(Integer, default=16, nullable=False)
    fee_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    status: Mapped[CompetitionStatus] = mapped_column(
        String(32), default=CompetitionStatus.DRAFT, nullable=False
    )
    rules_config: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)

    registrations: Mapped[list["CompetitionRegistration"]] = relationship(
        "CompetitionRegistration", back_populates="competition", cascade="all, delete-orphan"
    )
    fixtures: Mapped[list["MatchFixture"]] = relationship(
        "MatchFixture", back_populates="competition", cascade="all, delete-orphan"
    )
    standings: Mapped[list["CompetitionStanding"]] = relationship(
        "CompetitionStanding", back_populates="competition", cascade="all, delete-orphan"
    )


class CompetitionRegistration(TenantScopedModel):
    """Team or participant entry into a competition."""

    __tablename__ = "sports_competition_registrations"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "competition_id", "team_id", "participant_id", name="uq_sports_comp_reg_unique"
        ),
    )

    competition_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports_competitions.id", ondelete="CASCADE"),
        nullable=False,
    )
    team_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports_teams.id", ondelete="CASCADE"),
        nullable=True,
    )
    participant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports_participants.id", ondelete="CASCADE"),
        nullable=True,
    )
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="REGISTERED", nullable=False)
    seed_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    invoice_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("finance_invoices.id", ondelete="SET NULL"),
        nullable=True,
    )
    payment_status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)

    competition: Mapped["Competition"] = relationship("Competition", back_populates="registrations")


class MatchFixture(TenantScopedModel):
    """Individual match fixture within a tournament."""

    __tablename__ = "sports_match_fixtures"
    __table_args__ = (
        UniqueConstraint("tenant_id", "competition_id", "match_number", name="uq_sports_match_fixtures_unique"),
        Index("idx_sports_fixtures_schedule", "tenant_id", "match_date", "facility_id"),
    )

    competition_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports_competitions.id", ondelete="CASCADE"),
        nullable=False,
    )
    match_number: Mapped[str] = mapped_column(String(32), nullable=False)
    stage: Mapped[MatchStage] = mapped_column(
        String(32), default=MatchStage.GROUP_STAGE, nullable=False
    )
    round_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    home_team_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports_teams.id", ondelete="SET NULL"),
        nullable=True,
    )
    away_team_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports_teams.id", ondelete="SET NULL"),
        nullable=True,
    )
    home_participant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports_participants.id", ondelete="SET NULL"),
        nullable=True,
    )
    away_participant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports_participants.id", ondelete="SET NULL"),
        nullable=True,
    )
    facility_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports_facilities.id", ondelete="SET NULL"),
        nullable=True,
    )
    match_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    status: Mapped[FixtureStatus] = mapped_column(
        String(32), default=FixtureStatus.SCHEDULED, nullable=False
    )
    postponement_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    competition: Mapped["Competition"] = relationship("Competition", back_populates="fixtures")
    result: Mapped["MatchResult | None"] = relationship("MatchResult", uselist=False, back_populates="fixture")
    officials: Mapped[list["MatchOfficialAssignment"]] = relationship(
        "MatchOfficialAssignment", back_populates="fixture", cascade="all, delete-orphan"
    )


class MatchOfficialAssignment(TenantScopedModel):
    """Referee, umpire, or official assigned to a fixture."""

    __tablename__ = "sports_match_official_assignments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "fixture_id", "user_id", name="uq_sports_match_officials_unique"),
    )

    fixture_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports_match_fixtures.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[OfficialRole] = mapped_column(
        String(32), default=OfficialRole.REFEREE, nullable=False
    )
    status: Mapped[OfficialAssignmentStatus] = mapped_column(
        String(32), default=OfficialAssignmentStatus.ASSIGNED, nullable=False
    )
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)

    fixture: Mapped["MatchFixture"] = relationship("MatchFixture", back_populates="officials")


class MatchResult(TenantScopedModel):
    """Auditable final match result and scores."""

    __tablename__ = "sports_match_results"
    __table_args__ = (
        UniqueConstraint("tenant_id", "fixture_id", name="uq_sports_match_results_fixture"),
    )

    fixture_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports_match_fixtures.id", ondelete="CASCADE"),
        nullable=False,
    )
    home_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    away_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    winning_team_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports_teams.id", ondelete="SET NULL"),
        nullable=True,
    )
    winning_participant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports_participants.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_draw: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_forfeit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    forfeit_team_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports_teams.id", ondelete="SET NULL"),
        nullable=True,
    )
    score_breakdown: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    recorded_by_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    verified_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    correction_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    audit_history: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONType, nullable=True)

    fixture: Mapped["MatchFixture"] = relationship("MatchFixture", back_populates="result")


class CompetitionStanding(TenantScopedModel):
    """League table standings entry."""

    __tablename__ = "sports_competition_standings"
    __table_args__ = (
        UniqueConstraint("tenant_id", "competition_id", "team_id", "participant_id", name="uq_sports_standings_unique"),
        Index("idx_sports_standings_rank", "tenant_id", "competition_id", "rank"),
    )

    competition_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports_competitions.id", ondelete="CASCADE"),
        nullable=False,
    )
    team_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports_teams.id", ondelete="CASCADE"),
        nullable=True,
    )
    participant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports_participants.id", ondelete="CASCADE"),
        nullable=True,
    )
    played: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    won: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    drawn: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lost: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    points_for: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    points_against: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bonus_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    competition: Mapped["Competition"] = relationship("Competition", back_populates="standings")


# =============================================================================
# 6. ACHIEVEMENTS & EQUIPMENT
# =============================================================================


class SportsAchievement(TenantScopedModel):
    """Institutional sports award, medal, or record."""

    __tablename__ = "sports_achievements"

    competition_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports_competitions.id", ondelete="SET NULL"),
        nullable=True,
    )
    team_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports_teams.id", ondelete="SET NULL"),
        nullable=True,
    )
    participant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports_participants.id", ondelete="SET NULL"),
        nullable=True,
    )
    achievement_type: Mapped[AchievementType] = mapped_column(
        String(32), default=AchievementType.CHAMPION, nullable=False
    )
    recognition_level: Mapped[RecognitionLevel] = mapped_column(
        String(32), default=RecognitionLevel.INSTITUTIONAL, nullable=False
    )
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    citation: Mapped[str | None] = mapped_column(Text, nullable=True)
    awarded_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class EquipmentAssignment(TenantScopedModel):
    """Sports equipment custody, checkout and condition tracking."""

    __tablename__ = "sports_equipment_assignments"
    __table_args__ = (
        Index("idx_sports_equip_status", "tenant_id", "status", "due_date"),
    )

    asset_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("asset_registry.id", ondelete="SET NULL"),
        nullable=True,
    )
    equipment_name: Mapped[str] = mapped_column(String(128), nullable=False)
    sport: Mapped[str] = mapped_column(String(64), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    assigned_to_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="CASCADE"),
        nullable=False,
    )
    team_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports_teams.id", ondelete="SET NULL"),
        nullable=True,
    )
    facility_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sports_facilities.id", ondelete="SET NULL"),
        nullable=True,
    )
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    checkout_condition: Mapped[EquipmentCondition] = mapped_column(
        String(32), default=EquipmentCondition.GOOD, nullable=False
    )
    return_condition: Mapped[EquipmentCondition | None] = mapped_column(String(32), nullable=True)
    status: Mapped[CheckoutStatus] = mapped_column(
        String(32), default=CheckoutStatus.CHECKED_OUT, nullable=False
    )
    damage_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    replacement_fee: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
