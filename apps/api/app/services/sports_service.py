"""CampusOS Enterprise Sports, Athletics, Recreation & Student Fitness Service (Step 57).

CampusOS Tagline: "One Campus. One System. One Source of Truth."

Integrates with:
- Facility & Space Scheduling (conflict-free court/pitch bookings, maintenance windows)
- People & Student Lifecycle (student athletes, coach profiles, clearance status)
- Asset Management & Inventory (sports equipment checkout, damage/loss logs)
- Finance (sports registrations, tournament fees, authoritative invoices)
- Notifications & Outbox Events (Transactional Event Backbone)
"""

from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import DomainEventType
from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
from app.models.sports import (
    AttendanceStatus,
    BookingStatus,
    CheckoutStatus,
    ClearanceStatus,
    CoachingAssignment,
    Competition,
    CompetitionRegistration,
    CompetitionStanding,
    CompetitionStatus,
    EquipmentAssignment,
    EquipmentCondition,
    FacilityBooking,
    FacilityStatus,
    FixtureStatus,
    MatchFixture,
    MatchOfficialAssignment,
    MatchResult,
    MatchStage,
    RosterStatus,
    SportsAchievement,
    SportsDepartment,
    SportsFacility,
    SportsParticipant,
    SportsTeam,
    TeamMembership,
    TournamentFormat,
    TrainingAttendance,
    TrainingProgram,
    TrainingSession,
)
from app.models.workflow import OutboxEvent
from app.schemas.sports import (
    BulkAttendanceCreate,
    CoachingAssignmentCreate,
    CompetitionCreate,
    CompetitionRegistrationCreate,
    CompetitionUpdate,
    EquipmentCheckoutCreate,
    EquipmentReturnRequest,
    FacilityBookingCreate,
    FixtureGenerationRequest,
    MatchFixtureUpdate,
    MatchOfficialAssignmentCreate,
    MatchResultCreate,
    MatchResultVerify,
    SportsAchievementCreate,
    SportsDepartmentCreate,
    SportsDepartmentUpdate,
    SportsFacilityCreate,
    SportsFacilityUpdate,
    SportsParticipantCreate,
    SportsParticipantUpdate,
    SportsTeamCreate,
    SportsTeamUpdate,
    TeamMembershipCreate,
    TeamMembershipUpdate,
    TrainingProgramCreate,
    TrainingProgramUpdate,
    TrainingSessionCreate,
)


def _val(x: Any) -> str:
    """Safely extract string value whether x is an Enum, str, or None."""
    if x is None:
        return ""
    return x.value if hasattr(x, "value") else str(x)


class SportsService:
    """Service layer managing sports departments, facilities, participants, teams, competitions, and equipment."""

    def _create_outbox_event(
        self,
        tenant_id: UUID,
        event_type: DomainEventType,
        aggregate_type: str,
        aggregate_id: UUID,
        payload: dict[str, Any],
    ) -> OutboxEvent:
        return OutboxEvent(
            id=uuid4(),
            tenant_id=tenant_id,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_type=_val(event_type),
            correlation_id=str(uuid4()),
            payload=payload,
        )

    # =========================================================================
    # 1. SPORTS DEPARTMENTS
    # =========================================================================

    async def list_departments(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        campus_id: UUID | None = None,
    ) -> list[SportsDepartment]:
        query = select(SportsDepartment).where(SportsDepartment.tenant_id == tenant_id)
        if campus_id:
            query = query.where(SportsDepartment.campus_id == campus_id)
        query = query.order_by(SportsDepartment.name.asc())
        result = await db.execute(query)
        return list(result.scalars().all())

    async def create_department(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        data: SportsDepartmentCreate,
    ) -> SportsDepartment:
        existing = await db.execute(
            select(SportsDepartment).where(
                SportsDepartment.tenant_id == tenant_id,
                SportsDepartment.code == data.code,
            )
        )
        if existing.scalars().first():
            raise ConflictException(f"Sports department with code '{data.code}' already exists.")

        department = SportsDepartment(
            id=uuid4(),
            tenant_id=tenant_id,
            **data.model_dump(),
        )
        db.add(department)
        await db.commit()
        await db.refresh(department)
        return department

    async def get_department(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        department_id: UUID,
    ) -> SportsDepartment:
        query = select(SportsDepartment).where(
            SportsDepartment.tenant_id == tenant_id,
            SportsDepartment.id == department_id,
        )
        result = await db.execute(query)
        department = result.scalars().first()
        if not department:
            raise NotFoundException("SportsDepartment", department_id)
        return department

    async def update_department(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        department_id: UUID,
        data: SportsDepartmentUpdate,
    ) -> SportsDepartment:
        department = await self.get_department(db, tenant_id, department_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(department, key, value)
        await db.commit()
        await db.refresh(department)
        return department

    # =========================================================================
    # 2. SPORTS FACILITIES & AVAILABILITY
    # =========================================================================

    async def list_facilities(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        campus_id: UUID | None = None,
        facility_type: str | None = None,
        status: str | None = None,
    ) -> list[SportsFacility]:
        query = select(SportsFacility).where(SportsFacility.tenant_id == tenant_id)
        if campus_id:
            query = query.where(SportsFacility.campus_id == campus_id)
        if facility_type:
            query = query.where(SportsFacility.facility_type == facility_type)
        if status:
            query = query.where(SportsFacility.status == status)
        query = query.order_by(SportsFacility.name.asc())
        result = await db.execute(query)
        return list(result.scalars().all())

    async def create_facility(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        data: SportsFacilityCreate,
    ) -> SportsFacility:
        existing = await db.execute(
            select(SportsFacility).where(
                SportsFacility.tenant_id == tenant_id,
                SportsFacility.code == data.code,
            )
        )
        if existing.scalars().first():
            raise ConflictException(f"Facility with code '{data.code}' already exists.")

        facility = SportsFacility(
            id=uuid4(),
            tenant_id=tenant_id,
            **data.model_dump(),
        )
        db.add(facility)
        await db.commit()
        await db.refresh(facility)
        return facility

    async def get_facility(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        facility_id: UUID,
    ) -> SportsFacility:
        query = select(SportsFacility).where(
            SportsFacility.tenant_id == tenant_id,
            SportsFacility.id == facility_id,
        )
        result = await db.execute(query)
        facility = result.scalars().first()
        if not facility:
            raise NotFoundException("SportsFacility", facility_id)
        return facility

    async def update_facility(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        facility_id: UUID,
        data: SportsFacilityUpdate,
    ) -> SportsFacility:
        facility = await self.get_facility(db, tenant_id, facility_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(facility, key, value)
        await db.commit()
        await db.refresh(facility)
        return facility

    async def check_facility_conflicts(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        facility_id: UUID,
        booking_date: date,
        start_time: time,
        end_time: time,
        exclude_booking_id: UUID | None = None,
    ) -> list[FacilityBooking]:
        """Detect overlapping facility bookings: [start_time, end_time) overlaps with existing."""
        query = select(FacilityBooking).where(
            FacilityBooking.tenant_id == tenant_id,
            FacilityBooking.facility_id == facility_id,
            FacilityBooking.booking_date == booking_date,
            FacilityBooking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PENDING]),
            FacilityBooking.start_time < end_time,
            FacilityBooking.end_time > start_time,
        )
        if exclude_booking_id:
            query = query.where(FacilityBooking.id != exclude_booking_id)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def list_facility_calendar(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        facility_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[FacilityBooking]:
        query = (
            select(FacilityBooking)
            .where(
                FacilityBooking.tenant_id == tenant_id,
                FacilityBooking.facility_id == facility_id,
                FacilityBooking.booking_date >= start_date,
                FacilityBooking.booking_date <= end_date,
                FacilityBooking.status != BookingStatus.CANCELLED,
            )
            .order_by(FacilityBooking.booking_date.asc(), FacilityBooking.start_time.asc())
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    # =========================================================================
    # 3. FACILITY BOOKINGS
    # =========================================================================

    async def create_booking(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        data: FacilityBookingCreate,
    ) -> FacilityBooking:
        facility = await self.get_facility(db, tenant_id, data.facility_id)

        if facility.status == FacilityStatus.MAINTENANCE_CLOSED:
            raise BadRequestException(
                f"Facility '{facility.name}' is closed for maintenance: {facility.closure_reason or 'No reason provided'}."
            )
        if facility.status == FacilityStatus.RENOVATION:
            raise BadRequestException(f"Facility '{facility.name}' is undergoing renovation and unavailable.")

        if data.start_time >= data.end_time:
            raise BadRequestException("Start time must be strictly before end time.")

        # Check overlapping bookings
        conflicts = await self.check_facility_conflicts(
            db=db,
            tenant_id=tenant_id,
            facility_id=data.facility_id,
            booking_date=data.booking_date,
            start_time=data.start_time,
            end_time=data.end_time,
        )
        if conflicts:
            conflict_titles = ", ".join([f"'{c.title}' ({c.start_time}-{c.end_time})" for c in conflicts])
            raise ConflictException(
                f"Facility '{facility.name}' is already reserved during requested slot. Conflicting bookings: {conflict_titles}."
            )

        booking = FacilityBooking(
            id=uuid4(),
            tenant_id=tenant_id,
            status=BookingStatus.CONFIRMED,
            **data.model_dump(),
        )
        db.add(booking)

        outbox = self._create_outbox_event(
            tenant_id=tenant_id,
            event_type=DomainEventType.SPORTS_FACILITY_BOOKED,
            aggregate_type="FacilityBooking",
            aggregate_id=booking.id,
            payload={
                "facility_id": str(booking.facility_id),
                "facility_name": facility.name,
                "booking_date": booking.booking_date.isoformat(),
                "start_time": booking.start_time.isoformat(),
                "end_time": booking.end_time.isoformat(),
                "purpose": _val(booking.purpose),
                "title": booking.title,
            },
        )
        db.add(outbox)

        await db.commit()
        await db.refresh(booking)
        return booking

    async def list_bookings(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        facility_id: UUID | None = None,
        booking_date: date | None = None,
        status: str | None = None,
    ) -> list[FacilityBooking]:
        query = select(FacilityBooking).where(FacilityBooking.tenant_id == tenant_id)
        if facility_id:
            query = query.where(FacilityBooking.facility_id == facility_id)
        if booking_date:
            query = query.where(FacilityBooking.booking_date == booking_date)
        if status:
            query = query.where(FacilityBooking.status == status)
        query = query.order_by(FacilityBooking.booking_date.desc(), FacilityBooking.start_time.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    async def cancel_booking(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        booking_id: UUID,
        cancellation_reason: str,
    ) -> FacilityBooking:
        query = select(FacilityBooking).where(
            FacilityBooking.tenant_id == tenant_id,
            FacilityBooking.id == booking_id,
        )
        result = await db.execute(query)
        booking = result.scalars().first()
        if not booking:
            raise NotFoundException("FacilityBooking", booking_id)

        booking.status = BookingStatus.CANCELLED
        booking.cancellation_reason = cancellation_reason
        await db.commit()
        await db.refresh(booking)
        return booking

    # =========================================================================
    # 4. SPORTS PARTICIPANTS (ATHLETES)
    # =========================================================================

    async def list_participants(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        sport: str | None = None,
        status: str | None = None,
        clearance_status: str | None = None,
    ) -> list[SportsParticipant]:
        query = select(SportsParticipant).where(SportsParticipant.tenant_id == tenant_id)
        if sport:
            query = query.where(SportsParticipant.primary_sport == sport)
        if status:
            query = query.where(SportsParticipant.status == status)
        if clearance_status:
            query = query.where(SportsParticipant.clearance_status == clearance_status)
        query = query.order_by(SportsParticipant.participant_code.asc())
        result = await db.execute(query)
        return list(result.scalars().all())

    async def create_participant(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        data: SportsParticipantCreate,
    ) -> SportsParticipant:
        # Check unique user per tenant
        existing_user = await db.execute(
            select(SportsParticipant).where(
                SportsParticipant.tenant_id == tenant_id,
                SportsParticipant.user_id == data.user_id,
            )
        )
        if existing_user.scalars().first():
            raise ConflictException("A sports participant profile already exists for this user.")

        # Check unique participant_code
        existing_code = await db.execute(
            select(SportsParticipant).where(
                SportsParticipant.tenant_id == tenant_id,
                SportsParticipant.participant_code == data.participant_code,
            )
        )
        if existing_code.scalars().first():
            raise ConflictException(f"Participant code '{data.participant_code}' is already registered.")

        participant = SportsParticipant(
            id=uuid4(),
            tenant_id=tenant_id,
            consent_recorded_at=datetime.now(UTC) if data.consent_recorded else None,
            **data.model_dump(),
        )
        db.add(participant)

        outbox = self._create_outbox_event(
            tenant_id=tenant_id,
            event_type=DomainEventType.SPORTS_PARTICIPANT_REGISTERED,
            aggregate_type="SportsParticipant",
            aggregate_id=participant.id,
            payload={
                "participant_code": participant.participant_code,
                "user_id": str(participant.user_id),
                "primary_sport": participant.primary_sport,
                "clearance_status": _val(participant.clearance_status),
            },
        )
        db.add(outbox)

        await db.commit()
        await db.refresh(participant)
        return participant

    async def get_participant(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        participant_id: UUID,
    ) -> SportsParticipant:
        query = select(SportsParticipant).where(
            SportsParticipant.tenant_id == tenant_id,
            SportsParticipant.id == participant_id,
        )
        result = await db.execute(query)
        participant = result.scalars().first()
        if not participant:
            raise NotFoundException("SportsParticipant", participant_id)
        return participant

    async def update_participant(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        participant_id: UUID,
        data: SportsParticipantUpdate,
    ) -> SportsParticipant:
        participant = await self.get_participant(db, tenant_id, participant_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(participant, key, value)
        await db.commit()
        await db.refresh(participant)
        return participant

    # =========================================================================
    # 5. TEAMS & ROSTERS
    # =========================================================================

    async def list_teams(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        sport: str | None = None,
        category: str | None = None,
        status: str | None = None,
    ) -> list[tuple[SportsTeam, int]]:
        """Returns teams along with active roster count."""
        query = (
            select(
                SportsTeam,
                func.count(TeamMembership.id).label("roster_count"),
            )
            .outerjoin(
                TeamMembership,
                and_(
                    TeamMembership.team_id == SportsTeam.id,
                    TeamMembership.status == RosterStatus.ACTIVE,
                ),
            )
            .where(SportsTeam.tenant_id == tenant_id)
            .group_by(SportsTeam.id)
        )
        if sport:
            query = query.where(SportsTeam.sport == sport)
        if category:
            query = query.where(SportsTeam.category == category)
        if status:
            query = query.where(SportsTeam.status == status)

        query = query.order_by(SportsTeam.name.asc())
        result = await db.execute(query)
        return [(row[0], row[1]) for row in result.all()]

    async def create_team(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        data: SportsTeamCreate,
    ) -> SportsTeam:
        existing = await db.execute(
            select(SportsTeam).where(
                SportsTeam.tenant_id == tenant_id,
                SportsTeam.code == data.code,
            )
        )
        if existing.scalars().first():
            raise ConflictException(f"Team with code '{data.code}' already exists.")

        team = SportsTeam(
            id=uuid4(),
            tenant_id=tenant_id,
            **data.model_dump(),
        )
        db.add(team)

        outbox = self._create_outbox_event(
            tenant_id=tenant_id,
            event_type=DomainEventType.SPORTS_TEAM_CREATED,
            aggregate_type="SportsTeam",
            aggregate_id=team.id,
            payload={
                "team_code": team.code,
                "team_name": team.name,
                "sport": team.sport,
                "category": _val(team.category),
            },
        )
        db.add(outbox)

        await db.commit()
        await db.refresh(team)
        return team

    async def get_team(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        team_id: UUID,
    ) -> SportsTeam:
        query = select(SportsTeam).where(
            SportsTeam.tenant_id == tenant_id,
            SportsTeam.id == team_id,
        )
        result = await db.execute(query)
        team = result.scalars().first()
        if not team:
            raise NotFoundException("SportsTeam", team_id)
        return team

    async def update_team(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        team_id: UUID,
        data: SportsTeamUpdate,
    ) -> SportsTeam:
        team = await self.get_team(db, tenant_id, team_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(team, key, value)
        await db.commit()
        await db.refresh(team)
        return team

    async def get_team_roster(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        team_id: UUID,
    ) -> list[TeamMembership]:
        query = (
            select(TeamMembership)
            .where(
                TeamMembership.tenant_id == tenant_id,
                TeamMembership.team_id == team_id,
                TeamMembership.status == RosterStatus.ACTIVE,
            )
            .order_by(TeamMembership.jersey_number.asc().nulls_last())
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def add_team_member(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        team_id: UUID,
        data: TeamMembershipCreate,
    ) -> TeamMembership:
        team = await self.get_team(db, tenant_id, team_id)
        participant = await self.get_participant(db, tenant_id, data.participant_id)

        # Check athletic clearance for competitive/varsity teams
        if _val(team.category) in ["VARSITY", "COMPETITIVE"]:
            if _val(participant.clearance_status) not in ["CLEARED", "RESTRICTED"]:
                raise BadRequestException(
                    f"Participant '{participant.participant_code}' does not have active athletic clearance ({_val(participant.clearance_status)})."
                )

        # Check roster capacity
        active_roster_count = await db.scalar(
            select(func.count(TeamMembership.id)).where(
                TeamMembership.tenant_id == tenant_id,
                TeamMembership.team_id == team_id,
                TeamMembership.status == RosterStatus.ACTIVE,
            )
        )
        if (active_roster_count or 0) >= team.max_roster_size:
            raise BadRequestException(f"Team '{team.name}' has reached its maximum roster capacity of {team.max_roster_size}.")

        # Check if already in roster
        existing_membership = await db.execute(
            select(TeamMembership).where(
                TeamMembership.tenant_id == tenant_id,
                TeamMembership.team_id == team_id,
                TeamMembership.participant_id == data.participant_id,
            )
        )
        membership = existing_membership.scalars().first()
        if membership:
            if membership.status == RosterStatus.ACTIVE:
                raise ConflictException("Participant is already an active member of this team.")
            membership.status = RosterStatus.ACTIVE
            membership.role = data.role
            membership.jersey_number = data.jersey_number
            membership.position = data.position
            membership.joined_at = datetime.now(UTC)
            membership.left_at = None
        else:
            membership = TeamMembership(
                id=uuid4(),
                tenant_id=tenant_id,
                team_id=team_id,
                participant_id=data.participant_id,
                role=data.role,
                jersey_number=data.jersey_number,
                position=data.position,
                status=RosterStatus.ACTIVE,
                approved_by_user_id=data.approved_by_user_id,
            )
            db.add(membership)

        outbox = self._create_outbox_event(
            tenant_id=tenant_id,
            event_type=DomainEventType.SPORTS_TEAM_ROSTER_UPDATED,
            aggregate_type="TeamMembership",
            aggregate_id=membership.id,
            payload={
                "team_id": str(team_id),
                "participant_id": str(data.participant_id),
                "role": _val(data.role),
                "jersey_number": data.jersey_number,
            },
        )
        db.add(outbox)

        await db.commit()
        await db.refresh(membership)
        return membership

    async def update_team_member(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        membership_id: UUID,
        data: TeamMembershipUpdate,
    ) -> TeamMembership:
        query = select(TeamMembership).where(
            TeamMembership.tenant_id == tenant_id,
            TeamMembership.id == membership_id,
        )
        result = await db.execute(query)
        membership = result.scalars().first()
        if not membership:
            raise NotFoundException("TeamMembership", membership_id)

        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(membership, key, value)
        if data.status and data.status != RosterStatus.ACTIVE and not membership.left_at:
            membership.left_at = datetime.now(UTC)

        await db.commit()
        await db.refresh(membership)
        return membership

    # =========================================================================
    # 6. COACHING ASSIGNMENTS
    # =========================================================================

    async def list_coaches(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        sport: str | None = None,
        team_id: UUID | None = None,
    ) -> list[CoachingAssignment]:
        query = select(CoachingAssignment).where(CoachingAssignment.tenant_id == tenant_id)
        if sport:
            query = query.where(CoachingAssignment.sport == sport)
        if team_id:
            query = query.where(CoachingAssignment.team_id == team_id)
        query = query.order_by(CoachingAssignment.assigned_from.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    async def assign_coach(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        data: CoachingAssignmentCreate,
    ) -> CoachingAssignment:
        assignment = CoachingAssignment(
            id=uuid4(),
            tenant_id=tenant_id,
            **data.model_dump(),
        )
        db.add(assignment)
        await db.commit()
        await db.refresh(assignment)
        return assignment

    # =========================================================================
    # 7. TRAINING PROGRAMS & SESSIONS
    # =========================================================================

    async def list_training_programs(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        sport: str | None = None,
        is_active: bool | None = None,
    ) -> list[TrainingProgram]:
        query = select(TrainingProgram).where(TrainingProgram.tenant_id == tenant_id)
        if sport:
            query = query.where(TrainingProgram.sport == sport)
        if is_active is not None:
            query = query.where(TrainingProgram.is_active == is_active)
        query = query.order_by(TrainingProgram.start_date.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    async def create_training_program(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        data: TrainingProgramCreate,
    ) -> TrainingProgram:
        existing = await db.execute(
            select(TrainingProgram).where(
                TrainingProgram.tenant_id == tenant_id,
                TrainingProgram.code == data.code,
            )
        )
        if existing.scalars().first():
            raise ConflictException(f"Training program with code '{data.code}' already exists.")

        program = TrainingProgram(
            id=uuid4(),
            tenant_id=tenant_id,
            **data.model_dump(),
        )
        db.add(program)
        await db.commit()
        await db.refresh(program)
        return program

    async def get_training_program(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        program_id: UUID,
    ) -> TrainingProgram:
        query = select(TrainingProgram).where(
            TrainingProgram.tenant_id == tenant_id,
            TrainingProgram.id == program_id,
        )
        result = await db.execute(query)
        program = result.scalars().first()
        if not program:
            raise NotFoundException("TrainingProgram", program_id)
        return program

    async def update_training_program(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        program_id: UUID,
        data: TrainingProgramUpdate,
    ) -> TrainingProgram:
        program = await self.get_training_program(db, tenant_id, program_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(program, key, value)
        await db.commit()
        await db.refresh(program)
        return program

    async def create_training_session(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        data: TrainingSessionCreate,
    ) -> TrainingSession:
        program = await self.get_training_program(db, tenant_id, data.program_id)

        # If facility is specified, verify conflict-free and reserve it
        if data.facility_id:
            facility = await self.get_facility(db, tenant_id, data.facility_id)
            conflicts = await self.check_facility_conflicts(
                db=db,
                tenant_id=tenant_id,
                facility_id=data.facility_id,
                booking_date=data.session_date,
                start_time=data.start_time,
                end_time=data.end_time,
            )
            if conflicts:
                raise ConflictException(
                    f"Facility '{facility.name}' has scheduling conflicts during session time: {conflicts[0].title}."
                )

            # Auto-create linked booking
            booking = FacilityBooking(
                id=uuid4(),
                tenant_id=tenant_id,
                facility_id=data.facility_id,
                booking_date=data.session_date,
                start_time=data.start_time,
                end_time=data.end_time,
                purpose="TRAINING",
                title=f"Training: {program.name} - {data.title}",
                training_program_id=program.id,
                status=BookingStatus.CONFIRMED,
            )
            db.add(booking)

        session = TrainingSession(
            id=uuid4(),
            tenant_id=tenant_id,
            **data.model_dump(),
        )
        db.add(session)

        outbox = self._create_outbox_event(
            tenant_id=tenant_id,
            event_type=DomainEventType.SPORTS_TRAINING_SCHEDULED,
            aggregate_type="TrainingSession",
            aggregate_id=session.id,
            payload={
                "program_id": str(program.id),
                "program_name": program.name,
                "session_date": session.session_date.isoformat(),
                "start_time": session.start_time.isoformat(),
                "title": session.title,
            },
        )
        db.add(outbox)

        await db.commit()
        await db.refresh(session)
        return session

    async def list_training_sessions(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        program_id: UUID,
    ) -> list[TrainingSession]:
        query = (
            select(TrainingSession)
            .where(
                TrainingSession.tenant_id == tenant_id,
                TrainingSession.program_id == program_id,
            )
            .order_by(TrainingSession.session_date.asc(), TrainingSession.start_time.asc())
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def record_session_attendance(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        data: BulkAttendanceCreate,
        recorded_by_user_id: UUID | None = None,
    ) -> list[TrainingAttendance]:
        session_obj = await db.scalar(
            select(TrainingSession).where(
                TrainingSession.tenant_id == tenant_id,
                TrainingSession.id == data.session_id,
            )
        )
        if not session_obj:
            raise NotFoundException("TrainingSession", data.session_id)

        attendances: list[TrainingAttendance] = []
        now = datetime.now(UTC)
        for item in data.records:
            existing = await db.scalar(
                select(TrainingAttendance).where(
                    TrainingAttendance.tenant_id == tenant_id,
                    TrainingAttendance.session_id == data.session_id,
                    TrainingAttendance.participant_id == item.participant_id,
                )
            )
            if existing:
                existing.status = item.status
                existing.notes = item.notes
                existing.check_in_time = now if item.status == AttendanceStatus.PRESENT else None
                existing.recorded_by_user_id = recorded_by_user_id
                attendances.append(existing)
            else:
                att = TrainingAttendance(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    session_id=data.session_id,
                    participant_id=item.participant_id,
                    status=item.status,
                    notes=item.notes,
                    check_in_time=now if item.status == AttendanceStatus.PRESENT else None,
                    recorded_by_user_id=recorded_by_user_id,
                )
                db.add(att)
                attendances.append(att)

        await db.commit()
        return attendances

    async def get_session_attendance(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        session_id: UUID,
    ) -> list[TrainingAttendance]:
        query = (
            select(TrainingAttendance)
            .where(
                TrainingAttendance.tenant_id == tenant_id,
                TrainingAttendance.session_id == session_id,
            )
            .order_by(TrainingAttendance.created_at.asc())
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    # =========================================================================
    # 8. COMPETITIONS & FIXTURE ENGINE
    # =========================================================================

    async def list_competitions(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        sport: str | None = None,
        status: str | None = None,
    ) -> list[tuple[Competition, int]]:
        query = (
            select(
                Competition,
                func.count(CompetitionRegistration.id).label("registered_count"),
            )
            .outerjoin(
                CompetitionRegistration,
                and_(
                    CompetitionRegistration.competition_id == Competition.id,
                    CompetitionRegistration.status == "REGISTERED",
                ),
            )
            .where(Competition.tenant_id == tenant_id)
            .group_by(Competition.id)
        )
        if sport:
            query = query.where(Competition.sport == sport)
        if status:
            query = query.where(Competition.status == status)

        query = query.order_by(Competition.start_date.desc())
        result = await db.execute(query)
        return [(row[0], row[1]) for row in result.all()]

    async def create_competition(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        data: CompetitionCreate,
    ) -> Competition:
        existing = await db.execute(
            select(Competition).where(
                Competition.tenant_id == tenant_id,
                Competition.code == data.code,
            )
        )
        if existing.scalars().first():
            raise ConflictException(f"Competition with code '{data.code}' already exists.")

        competition = Competition(
            id=uuid4(),
            tenant_id=tenant_id,
            status=CompetitionStatus.DRAFT,
            **data.model_dump(),
        )
        db.add(competition)

        outbox = self._create_outbox_event(
            tenant_id=tenant_id,
            event_type=DomainEventType.SPORTS_COMPETITION_ANNOUNCED,
            aggregate_type="Competition",
            aggregate_id=competition.id,
            payload={
                "competition_code": competition.code,
                "competition_name": competition.name,
                "sport": competition.sport,
                "start_date": competition.start_date.isoformat(),
                "end_date": competition.end_date.isoformat(),
            },
        )
        db.add(outbox)

        await db.commit()
        await db.refresh(competition)
        return competition

    async def get_competition(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        competition_id: UUID,
    ) -> Competition:
        query = select(Competition).where(
            Competition.tenant_id == tenant_id,
            Competition.id == competition_id,
        )
        result = await db.execute(query)
        comp = result.scalars().first()
        if not comp:
            raise NotFoundException("Competition", competition_id)
        return comp

    async def update_competition(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        competition_id: UUID,
        data: CompetitionUpdate,
    ) -> Competition:
        comp = await self.get_competition(db, tenant_id, competition_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(comp, key, value)
        await db.commit()
        await db.refresh(comp)
        return comp

    async def register_competition_entry(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        competition_id: UUID,
        data: CompetitionRegistrationCreate,
    ) -> CompetitionRegistration:
        competition = await self.get_competition(db, tenant_id, competition_id)

        # Check deadline
        if date.today() > competition.registration_deadline:
            raise BadRequestException("Competition registration deadline has passed.")

        # Check entry capacity
        current_count = await db.scalar(
            select(func.count(CompetitionRegistration.id)).where(
                CompetitionRegistration.tenant_id == tenant_id,
                CompetitionRegistration.competition_id == competition_id,
                CompetitionRegistration.status == "REGISTERED",
            )
        )
        if (current_count or 0) >= competition.max_participants:
            raise BadRequestException(f"Competition participant limit ({competition.max_participants}) has been reached.")

        # Check duplication
        query = select(CompetitionRegistration).where(
            CompetitionRegistration.tenant_id == tenant_id,
            CompetitionRegistration.competition_id == competition_id,
        )
        if data.team_id:
            query = query.where(CompetitionRegistration.team_id == data.team_id)
        elif data.participant_id:
            query = query.where(CompetitionRegistration.participant_id == data.participant_id)
        else:
            raise BadRequestException("Either team_id or participant_id must be provided for competition registration.")

        existing = await db.execute(query)
        if existing.scalars().first():
            raise ConflictException("Team or participant is already registered for this competition.")

        reg = CompetitionRegistration(
            id=uuid4(),
            tenant_id=tenant_id,
            competition_id=competition_id,
            team_id=data.team_id,
            participant_id=data.participant_id,
            seed_number=data.seed_number,
            status="REGISTERED",
            payment_status="PAID" if competition.fee_amount == Decimal("0.00") else "PENDING",
        )
        db.add(reg)

        outbox = self._create_outbox_event(
            tenant_id=tenant_id,
            event_type=DomainEventType.SPORTS_COMPETITION_REGISTERED,
            aggregate_type="CompetitionRegistration",
            aggregate_id=reg.id,
            payload={
                "competition_id": str(competition_id),
                "team_id": str(data.team_id) if data.team_id else None,
                "participant_id": str(data.participant_id) if data.participant_id else None,
                "seed_number": data.seed_number,
            },
        )
        db.add(outbox)

        await db.commit()
        await db.refresh(reg)
        return reg

    async def list_competition_registrations(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        competition_id: UUID,
    ) -> list[CompetitionRegistration]:
        query = (
            select(CompetitionRegistration)
            .where(
                CompetitionRegistration.tenant_id == tenant_id,
                CompetitionRegistration.competition_id == competition_id,
            )
            .order_by(CompetitionRegistration.seed_number.asc().nulls_last())
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def generate_fixtures(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        req: FixtureGenerationRequest,
    ) -> list[MatchFixture]:
        """Automated tournament fixture generator supporting Knockout & Round Robin formats."""
        competition = await self.get_competition(db, tenant_id, req.competition_id)
        registrations = await self.list_competition_registrations(db, tenant_id, req.competition_id)

        if len(registrations) < 2:
            raise BadRequestException(f"At least 2 participants required to generate fixtures (found {len(registrations)}).")

        # Clear existing unplayed fixtures if regenerating
        existing_fixtures = await db.execute(
            select(MatchFixture).where(
                MatchFixture.tenant_id == tenant_id,
                MatchFixture.competition_id == req.competition_id,
            )
        )
        for f in existing_fixtures.scalars().all():
            if f.status == FixtureStatus.COMPLETED:
                raise ConflictException("Cannot regenerate fixtures for a tournament that already has completed matches.")
            await db.delete(f)

        generated_fixtures: list[MatchFixture] = []
        is_team_comp = _val(competition.registration_type) == "TEAM"

        # Candidate entries list (team_ids or participant_ids)
        entries = [r.team_id if is_team_comp else r.participant_id for r in registrations]

        match_date = req.start_date
        current_time = req.default_start_time
        facility_index = 0

        def next_slot() -> tuple[date, time, time, UUID | None]:
            nonlocal match_date, current_time, facility_index
            start = current_time
            # calculate end time
            dt_start = datetime.combine(match_date, start)
            dt_end = dt_start + timedelta(minutes=req.match_duration_minutes)
            end = dt_end.time()

            facility_id = req.facility_ids[facility_index % len(req.facility_ids)] if req.facility_ids else None
            facility_index += 1

            # Advance time for next match
            if dt_end.hour >= 18:
                match_date += timedelta(days=1)
                current_time = req.default_start_time
            else:
                current_time = end

            return match_date, start, end, facility_id

        if competition.tournament_format == TournamentFormat.ROUND_ROBIN:
            # Generate Round Robin: Every team plays every other team
            round_num = 1
            match_idx = 1
            n = len(entries)
            for i in range(n):
                for j in range(i + 1, n):
                    m_date, m_start, m_end, m_fac = next_slot()
                    fixture = MatchFixture(
                        id=uuid4(),
                        tenant_id=tenant_id,
                        competition_id=req.competition_id,
                        match_number=f"RR-M{match_idx}",
                        stage=MatchStage.GROUP_STAGE,
                        round_number=round_num,
                        home_team_id=entries[i] if is_team_comp else None,
                        away_team_id=entries[j] if is_team_comp else None,
                        home_participant_id=entries[i] if not is_team_comp else None,
                        away_participant_id=entries[j] if not is_team_comp else None,
                        facility_id=m_fac,
                        match_date=m_date,
                        start_time=m_start,
                        end_time=m_end,
                        status=FixtureStatus.SCHEDULED,
                    )
                    db.add(fixture)
                    generated_fixtures.append(fixture)
                    match_idx += 1
        else:
            # Single Elimination bracket for Round 1
            match_idx = 1
            for k in range(0, len(entries), 2):
                home_entry = entries[k]
                away_entry = entries[k + 1] if k + 1 < len(entries) else None

                m_date, m_start, m_end, m_fac = next_slot()
                stage = MatchStage.ROUND_OF_16 if len(entries) > 8 else MatchStage.QUARTER_FINAL
                if len(entries) <= 4:
                    stage = MatchStage.SEMI_FINAL

                fixture = MatchFixture(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    competition_id=req.competition_id,
                    match_number=f"R1-M{match_idx}",
                    stage=stage,
                    round_number=1,
                    home_team_id=home_entry if is_team_comp else None,
                    away_team_id=away_entry if (is_team_comp and away_entry) else None,
                    home_participant_id=home_entry if not is_team_comp else None,
                    away_participant_id=away_entry if (not is_team_comp and away_entry) else None,
                    facility_id=m_fac,
                    match_date=m_date,
                    start_time=m_start,
                    end_time=m_end,
                    status=FixtureStatus.SCHEDULED,
                )
                db.add(fixture)
                generated_fixtures.append(fixture)
                match_idx += 1

        competition.status = CompetitionStatus.ONGOING

        outbox = self._create_outbox_event(
            tenant_id=tenant_id,
            event_type=DomainEventType.SPORTS_FIXTURE_SCHEDULED,
            aggregate_type="Competition",
            aggregate_id=competition.id,
            payload={
                "competition_id": str(competition.id),
                "fixtures_count": len(generated_fixtures),
                "tournament_format": _val(competition.tournament_format),
            },
        )
        db.add(outbox)

        await db.commit()
        return generated_fixtures

    async def list_fixtures(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        competition_id: UUID | None = None,
        match_date: date | None = None,
        status: str | None = None,
    ) -> list[MatchFixture]:
        query = select(MatchFixture).where(MatchFixture.tenant_id == tenant_id)
        if competition_id:
            query = query.where(MatchFixture.competition_id == competition_id)
        if match_date:
            query = query.where(MatchFixture.match_date == match_date)
        if status:
            query = query.where(MatchFixture.status == status)
        query = query.order_by(MatchFixture.match_date.asc(), MatchFixture.start_time.asc())
        result = await db.execute(query)
        return list(result.scalars().all())

    async def update_fixture(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        fixture_id: UUID,
        data: MatchFixtureUpdate,
    ) -> MatchFixture:
        query = select(MatchFixture).where(
            MatchFixture.tenant_id == tenant_id,
            MatchFixture.id == fixture_id,
        )
        result = await db.execute(query)
        fixture = result.scalars().first()
        if not fixture:
            raise NotFoundException("MatchFixture", fixture_id)

        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(fixture, key, value)
        await db.commit()
        await db.refresh(fixture)
        return fixture

    async def assign_match_official(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        data: MatchOfficialAssignmentCreate,
    ) -> MatchOfficialAssignment:
        assignment = MatchOfficialAssignment(
            id=uuid4(),
            tenant_id=tenant_id,
            **data.model_dump(),
        )
        db.add(assignment)
        await db.commit()
        await db.refresh(assignment)
        return assignment

    # =========================================================================
    # 9. MATCH RESULTS & AUDITABLE STANDINGS CALCULATION
    # =========================================================================

    async def record_match_result(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        data: MatchResultCreate,
        recorded_by_user_id: UUID,
    ) -> MatchResult:
        fixture = await db.scalar(
            select(MatchFixture).where(
                MatchFixture.tenant_id == tenant_id,
                MatchFixture.id == data.fixture_id,
            )
        )
        if not fixture:
            raise NotFoundException("MatchFixture", data.fixture_id)

        # Check existing result
        existing = await db.scalar(
            select(MatchResult).where(
                MatchResult.tenant_id == tenant_id,
                MatchResult.fixture_id == data.fixture_id,
            )
        )
        now = datetime.now(UTC)
        if existing:
            # Record audit history for change
            audit_record = {
                "timestamp": now.isoformat(),
                "actor_id": str(recorded_by_user_id),
                "previous_home_score": existing.home_score,
                "previous_away_score": existing.away_score,
                "new_home_score": data.home_score,
                "new_away_score": data.away_score,
            }
            history = list(existing.audit_history or [])
            history.append(audit_record)
            existing.audit_history = history
            for key, val in data.model_dump().items():
                setattr(existing, key, val)
            existing.recorded_by_user_id = recorded_by_user_id
            existing.recorded_at = now
            existing.is_verified = False  # requires re-verification after score edit
            result_obj = existing
        else:
            result_obj = MatchResult(
                id=uuid4(),
                tenant_id=tenant_id,
                recorded_by_user_id=recorded_by_user_id,
                recorded_at=now,
                is_verified=False,
                audit_history=[
                    {
                        "action": "RECORDED",
                        "timestamp": now.isoformat(),
                        "actor_id": str(recorded_by_user_id),
                        "score": f"{data.home_score}-{data.away_score}",
                    }
                ],
                **data.model_dump(),
            )
            db.add(result_obj)

        fixture.status = FixtureStatus.COMPLETED

        outbox = self._create_outbox_event(
            tenant_id=tenant_id,
            event_type=DomainEventType.SPORTS_MATCH_RESULT_RECORDED,
            aggregate_type="MatchResult",
            aggregate_id=result_obj.id,
            payload={
                "fixture_id": str(fixture.id),
                "competition_id": str(fixture.competition_id),
                "score": f"{data.home_score}-{data.away_score}",
                "is_draw": data.is_draw,
            },
        )
        db.add(outbox)

        await db.commit()
        await db.refresh(result_obj)
        return result_obj

    async def verify_match_result(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        result_id: UUID,
        verified_by_user_id: UUID,
        verify_data: MatchResultVerify,
    ) -> MatchResult:
        query = select(MatchResult).where(
            MatchResult.tenant_id == tenant_id,
            MatchResult.id == result_id,
        )
        res = await db.execute(query)
        result_obj = res.scalars().first()
        if not result_obj:
            raise NotFoundException("MatchResult", result_id)

        now = datetime.now(UTC)
        result_obj.is_verified = verify_data.is_verified
        result_obj.verified_by_user_id = verified_by_user_id
        result_obj.verified_at = now
        if verify_data.correction_reason:
            result_obj.correction_reason = verify_data.correction_reason

        # Append to audit history
        history = list(result_obj.audit_history or [])
        history.append(
            {
                "action": "VERIFIED" if verify_data.is_verified else "REJECTED",
                "timestamp": now.isoformat(),
                "actor_id": str(verified_by_user_id),
                "reason": verify_data.correction_reason,
            }
        )
        result_obj.audit_history = history

        # Retrieve fixture to get competition_id
        fixture = await db.scalar(
            select(MatchFixture).where(
                MatchFixture.tenant_id == tenant_id,
                MatchFixture.id == result_obj.fixture_id,
            )
        )
        if fixture and verify_data.is_verified:
            # Recompute standings automatically
            await self.recompute_standings(db, tenant_id, fixture.competition_id)

        outbox = self._create_outbox_event(
            tenant_id=tenant_id,
            event_type=DomainEventType.SPORTS_MATCH_RESULT_VERIFIED,
            aggregate_type="MatchResult",
            aggregate_id=result_obj.id,
            payload={
                "result_id": str(result_obj.id),
                "is_verified": verify_data.is_verified,
                "verified_by": str(verified_by_user_id),
            },
        )
        db.add(outbox)

        await db.commit()
        await db.refresh(result_obj)
        return result_obj

    async def recompute_standings(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        competition_id: UUID,
    ) -> list[CompetitionStanding]:
        """Calculates and persists verified league table standings."""
        competition = await self.get_competition(db, tenant_id, competition_id)

        # Get all completed & verified matches for this competition
        fixtures_query = (
            select(MatchFixture, MatchResult)
            .join(MatchResult, MatchResult.fixture_id == MatchFixture.id)
            .where(
                MatchFixture.tenant_id == tenant_id,
                MatchFixture.competition_id == competition_id,
                MatchResult.is_verified == True,
            )
        )
        fixtures_res = await db.execute(fixtures_query)
        completed_matches = fixtures_res.all()

        is_team_comp = _val(competition.registration_type) == "TEAM"

        # Tally scores per competitor
        stats: dict[UUID, dict[str, int]] = {}

        def init_competitor(comp_id: UUID):
            if comp_id not in stats:
                stats[comp_id] = {
                    "played": 0,
                    "won": 0,
                    "drawn": 0,
                    "lost": 0,
                    "points_for": 0,
                    "points_against": 0,
                    "bonus_points": 0,
                    "total_points": 0,
                }

        for fix, res in completed_matches:
            c1 = fix.home_team_id if is_team_comp else fix.home_participant_id
            c2 = fix.away_team_id if is_team_comp else fix.away_participant_id

            if not c1 or not c2:
                continue

            init_competitor(c1)
            init_competitor(c2)

            stats[c1]["played"] += 1
            stats[c2]["played"] += 1

            stats[c1]["points_for"] += res.home_score
            stats[c1]["points_against"] += res.away_score

            stats[c2]["points_for"] += res.away_score
            stats[c2]["points_against"] += res.home_score

            if res.is_draw:
                stats[c1]["drawn"] += 1
                stats[c2]["drawn"] += 1
                stats[c1]["total_points"] += competition.points_for_draw
                stats[c2]["total_points"] += competition.points_for_draw
            elif res.winning_team_id == c1 or res.winning_participant_id == c1 or res.home_score > res.away_score:
                stats[c1]["won"] += 1
                stats[c2]["lost"] += 1
                stats[c1]["total_points"] += competition.points_for_win
                stats[c2]["total_points"] += competition.points_for_loss
            else:
                stats[c2]["won"] += 1
                stats[c1]["lost"] += 1
                stats[c2]["total_points"] += competition.points_for_win
                stats[c1]["total_points"] += competition.points_for_loss

        # Sort competitors by total_points DESC, then goal/point diff DESC
        sorted_competitors = sorted(
            stats.items(),
            key=lambda item: (
                item[1]["total_points"],
                item[1]["points_for"] - item[1]["points_against"],
                item[1]["points_for"],
            ),
            reverse=True,
        )

        standings: list[CompetitionStanding] = []
        for rank, (competitor_id, c_stats) in enumerate(sorted_competitors, start=1):
            query = select(CompetitionStanding).where(
                CompetitionStanding.tenant_id == tenant_id,
                CompetitionStanding.competition_id == competition_id,
            )
            if is_team_comp:
                query = query.where(CompetitionStanding.team_id == competitor_id)
            else:
                query = query.where(CompetitionStanding.participant_id == competitor_id)

            existing_standing = await db.scalar(query)
            if existing_standing:
                existing_standing.played = c_stats["played"]
                existing_standing.won = c_stats["won"]
                existing_standing.drawn = c_stats["drawn"]
                existing_standing.lost = c_stats["lost"]
                existing_standing.points_for = c_stats["points_for"]
                existing_standing.points_against = c_stats["points_against"]
                existing_standing.total_points = c_stats["total_points"]
                existing_standing.rank = rank
                standings.append(existing_standing)
            else:
                standing = CompetitionStanding(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    competition_id=competition_id,
                    team_id=competitor_id if is_team_comp else None,
                    participant_id=competitor_id if not is_team_comp else None,
                    played=c_stats["played"],
                    won=c_stats["won"],
                    drawn=c_stats["drawn"],
                    lost=c_stats["lost"],
                    points_for=c_stats["points_for"],
                    points_against=c_stats["points_against"],
                    bonus_points=0,
                    total_points=c_stats["total_points"],
                    rank=rank,
                )
                db.add(standing)
                standings.append(standing)

        await db.commit()
        return standings

    async def get_competition_standings(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        competition_id: UUID,
    ) -> list[tuple[CompetitionStanding, str | None]]:
        query = (
            select(
                CompetitionStanding,
                SportsTeam.name.label("team_name"),
            )
            .outerjoin(SportsTeam, SportsTeam.id == CompetitionStanding.team_id)
            .where(
                CompetitionStanding.tenant_id == tenant_id,
                CompetitionStanding.competition_id == competition_id,
            )
            .order_by(CompetitionStanding.rank.asc())
        )
        result = await db.execute(query)
        return [(row[0], row[1]) for row in result.all()]

    # =========================================================================
    # 10. ACHIEVEMENTS
    # =========================================================================

    async def list_achievements(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        team_id: UUID | None = None,
        participant_id: UUID | None = None,
    ) -> list[SportsAchievement]:
        query = select(SportsAchievement).where(SportsAchievement.tenant_id == tenant_id)
        if team_id:
            query = query.where(SportsAchievement.team_id == team_id)
        if participant_id:
            query = query.where(SportsAchievement.participant_id == participant_id)
        query = query.order_by(SportsAchievement.awarded_date.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    async def create_achievement(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        data: SportsAchievementCreate,
    ) -> SportsAchievement:
        achievement = SportsAchievement(
            id=uuid4(),
            tenant_id=tenant_id,
            **data.model_dump(),
        )
        db.add(achievement)
        await db.commit()
        await db.refresh(achievement)
        return achievement

    # =========================================================================
    # 11. EQUIPMENT ASSIGNMENTS & INVENTORY INTEGRATION
    # =========================================================================

    async def list_equipment_assignments(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        status: str | None = None,
        user_id: UUID | None = None,
    ) -> list[EquipmentAssignment]:
        query = select(EquipmentAssignment).where(EquipmentAssignment.tenant_id == tenant_id)
        if status:
            query = query.where(EquipmentAssignment.status == status)
        if user_id:
            query = query.where(EquipmentAssignment.assigned_to_user_id == user_id)
        query = query.order_by(EquipmentAssignment.due_date.asc())
        result = await db.execute(query)
        return list(result.scalars().all())

    async def checkout_equipment(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        data: EquipmentCheckoutCreate,
    ) -> EquipmentAssignment:
        assignment = EquipmentAssignment(
            id=uuid4(),
            tenant_id=tenant_id,
            status=CheckoutStatus.CHECKED_OUT,
            **data.model_dump(),
        )
        db.add(assignment)

        outbox = self._create_outbox_event(
            tenant_id=tenant_id,
            event_type=DomainEventType.SPORTS_EQUIPMENT_CHECKED_OUT,
            aggregate_type="EquipmentAssignment",
            aggregate_id=assignment.id,
            payload={
                "equipment_name": assignment.equipment_name,
                "sport": assignment.sport,
                "quantity": assignment.quantity,
                "assigned_to_user_id": str(assignment.assigned_to_user_id),
                "due_date": assignment.due_date.isoformat(),
            },
        )
        db.add(outbox)

        await db.commit()
        await db.refresh(assignment)
        return assignment

    async def return_equipment(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        assignment_id: UUID,
        data: EquipmentReturnRequest,
    ) -> EquipmentAssignment:
        query = select(EquipmentAssignment).where(
            EquipmentAssignment.tenant_id == tenant_id,
            EquipmentAssignment.id == assignment_id,
        )
        res = await db.execute(query)
        assignment = res.scalars().first()
        if not assignment:
            raise NotFoundException("EquipmentAssignment", assignment_id)

        now = datetime.now(UTC)
        assignment.returned_at = now
        assignment.return_condition = data.return_condition
        assignment.damage_notes = data.damage_notes
        assignment.replacement_fee = data.replacement_fee

        if data.return_condition in [EquipmentCondition.DAMAGED, EquipmentCondition.DESTROYED]:
            assignment.status = CheckoutStatus.DAMAGED
        elif data.return_condition == EquipmentCondition.LOST:
            assignment.status = CheckoutStatus.LOST
        else:
            assignment.status = CheckoutStatus.RETURNED

        outbox = self._create_outbox_event(
            tenant_id=tenant_id,
            event_type=DomainEventType.SPORTS_EQUIPMENT_RETURNED,
            aggregate_type="EquipmentAssignment",
            aggregate_id=assignment.id,
            payload={
                "equipment_name": assignment.equipment_name,
                "status": _val(assignment.status),
                "return_condition": _val(assignment.return_condition),
                "replacement_fee": str(assignment.replacement_fee) if assignment.replacement_fee else None,
            },
        )
        db.add(outbox)

        await db.commit()
        await db.refresh(assignment)
        return assignment

    # =========================================================================
    # 12. OPERATIONS SWEEP & DASHBOARD
    # =========================================================================

    async def sweep_sports_operations(
        self,
        db: AsyncSession,
        tenant_id: UUID | None = None,
    ) -> dict[str, int]:
        """Sweep overdue equipment, flag expired medical clearances, and maintain scheduling hygiene."""
        today = date.today()

        # 1. Flag overdue equipment
        equip_query = select(EquipmentAssignment).where(
            EquipmentAssignment.status == CheckoutStatus.CHECKED_OUT,
            EquipmentAssignment.due_date < today,
        )
        if tenant_id:
            equip_query = equip_query.where(EquipmentAssignment.tenant_id == tenant_id)

        overdue_items = (await db.execute(equip_query)).scalars().all()
        overdue_count = 0
        for item in overdue_items:
            item.status = CheckoutStatus.OVERDUE
            overdue_count += 1

        # 2. Flag expired participant clearances
        clearance_query = select(SportsParticipant).where(
            SportsParticipant.clearance_status.in_([ClearanceStatus.CLEARED, ClearanceStatus.RESTRICTED]),
            SportsParticipant.clearance_expiry.is_not(None),
            SportsParticipant.clearance_expiry < today,
        )
        if tenant_id:
            clearance_query = clearance_query.where(SportsParticipant.tenant_id == tenant_id)

        expired_participants = (await db.execute(clearance_query)).scalars().all()
        expired_count = 0
        for p in expired_participants:
            p.clearance_status = ClearanceStatus.EXPIRED
            expired_count += 1

        await db.commit()
        return {
            "overdue_equipment_flagged": overdue_count,
            "expired_clearances_flagged": expired_count,
        }

    async def get_dashboard_summary(
        self,
        db: AsyncSession,
        tenant_id: UUID,
    ) -> dict[str, int]:
        total_fac = await db.scalar(
            select(func.count(SportsFacility.id)).where(SportsFacility.tenant_id == tenant_id)
        ) or 0
        avail_fac = await db.scalar(
            select(func.count(SportsFacility.id)).where(
                SportsFacility.tenant_id == tenant_id,
                SportsFacility.status == FacilityStatus.AVAILABLE,
            )
        ) or 0
        total_teams = await db.scalar(
            select(func.count(SportsTeam.id)).where(SportsTeam.tenant_id == tenant_id)
        ) or 0
        total_ath = await db.scalar(
            select(func.count(SportsParticipant.id)).where(SportsParticipant.tenant_id == tenant_id)
        ) or 0
        active_comps = await db.scalar(
            select(func.count(Competition.id)).where(
                Competition.tenant_id == tenant_id,
                Competition.status.in_([CompetitionStatus.ONGOING, CompetitionStatus.REGISTRATION_OPEN]),
            )
        ) or 0
        up_fixtures = await db.scalar(
            select(func.count(MatchFixture.id)).where(
                MatchFixture.tenant_id == tenant_id,
                MatchFixture.status == FixtureStatus.SCHEDULED,
            )
        ) or 0
        active_programs = await db.scalar(
            select(func.count(TrainingProgram.id)).where(
                TrainingProgram.tenant_id == tenant_id,
                TrainingProgram.is_active == True,
            )
        ) or 0
        checked_out_eq = await db.scalar(
            select(func.count(EquipmentAssignment.id)).where(
                EquipmentAssignment.tenant_id == tenant_id,
                EquipmentAssignment.status == CheckoutStatus.CHECKED_OUT,
            )
        ) or 0
        overdue_eq = await db.scalar(
            select(func.count(EquipmentAssignment.id)).where(
                EquipmentAssignment.tenant_id == tenant_id,
                EquipmentAssignment.status == CheckoutStatus.OVERDUE,
            )
        ) or 0

        return {
            "total_facilities": total_fac,
            "available_facilities": avail_fac,
            "total_teams": total_teams,
            "total_athletes": total_ath,
            "active_competitions": active_comps,
            "upcoming_fixtures": up_fixtures,
            "active_training_programs": active_programs,
            "equipment_checked_out": checked_out_eq,
            "equipment_overdue": overdue_eq,
        }


sports_service = SportsService()
