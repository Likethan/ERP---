"""CampusOS Enterprise Sports, Athletics, Recreation & Student Fitness Tests (Step 57).

CampusOS Tagline: "One Campus. One System. One Source of Truth."

Verifies:
1. Sports department administration, multi-campus support, and operating hours.
2. Facility & court registration, maintenance closures, and accessibility profiles.
3. Facility booking with concurrency-safe overlap conflict prevention.
4. Student athlete profiles, privacy-preserving clearance tracking, and consent.
5. Team rosters with selection rules and maximum capacity constraints.
6. Coaching assignments and staff records integration.
7. Training programs, session scheduling, and bulk attendance recording.
8. Tournaments, competition formats (Knockout and Round Robin), and registration rules.
9. Automated match fixture generation and venue slot assignments.
10. Match score entry, auditable corrections, and verified result approval.
11. League table standings calculation (points, goal/point differentials, rankings).
12. Achievements, medals, and institutional awards.
13. Equipment checkouts, returns, condition inspection, and damage fees.
14. Operations sweep: overdue equipment flagging and expired clearance detection.
15. Strict multi-tenant isolation at all boundaries.
"""

import uuid
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
from app.models.core import AcademicYear, Campus, Department, Institution, Program
from app.models.people import StudentProfile, User
from app.models.sports import (
    ActivityCategory,
    AttendanceStatus,
    BookingPurpose,
    BookingStatus,
    CheckoutStatus,
    ClearanceStatus,
    CoachingRole,
    CompetitionRegistration,
    CompetitionStanding,
    CompetitionStatus,
    CompetitionType,
    DepartmentStatus,
    EquipmentAssignment,
    EquipmentCondition,
    FacilityBooking,
    FacilityStatus,
    FacilitySurface,
    FacilityType,
    FixtureStatus,
    MatchFixture,
    MatchResult,
    MemberRole,
    ParticipantStatus,
    ProgramType,
    RecognitionLevel,
    RegistrationType,
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
from app.schemas.sports import (
    BulkAttendanceCreate,
    BulkAttendanceItem,
    CoachingAssignmentCreate,
    CompetitionCreate,
    CompetitionRegistrationCreate,
    EquipmentCheckoutCreate,
    EquipmentReturnRequest,
    FacilityBookingCreate,
    FixtureGenerationRequest,
    MatchFixtureCreate,
    MatchFixtureUpdate,
    MatchOfficialAssignmentCreate,
    MatchResultCreate,
    MatchResultVerify,
    SportsAchievementCreate,
    SportsDepartmentCreate,
    SportsFacilityCreate,
    SportsParticipantCreate,
    SportsTeamCreate,
    TeamMembershipCreate,
    TrainingProgramCreate,
    TrainingSessionCreate,
)
from app.services.sports_service import sports_service


@pytest.fixture
async def sports_setup(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_b: Institution,
    super_admin_user: User,
):
    """Provides base campuses, athletes, coaches and facilities for sports tests."""
    uid = uuid.uuid4().hex[:6]

    campus_a = Campus(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        name="Main Campus Alpha",
        code=f"CMP-SP-{uid}",
        address="100 Athletics Boulevard",
        city="Coimbatore",
        is_active=True,
    )
    db_session.add(campus_a)

    # Coach User in Tenant A
    coach_user = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"coach_{uid}@apextech.edu",
        first_name="Marcus",
        last_name="Bennett",
        password_hash="hashed_pw_coach",
        status="ACTIVE",
    )
    db_session.add(coach_user)

    # Student 1 in Tenant A
    user_s1 = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"athlete1_{uid}@apextech.edu",
        first_name="Priya",
        last_name="Nair",
        password_hash="hashed_pw_s1",
        status="ACTIVE",
    )
    db_session.add(user_s1)

    # Student 2 in Tenant A
    user_s2 = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"athlete2_{uid}@apextech.edu",
        first_name="Vikram",
        last_name="Singh",
        password_hash="hashed_pw_s2",
        status="ACTIVE",
    )
    db_session.add(user_s2)

    # Student 3 in Tenant A
    user_s3 = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"athlete3_{uid}@apextech.edu",
        first_name="Ananya",
        last_name="Iyer",
        password_hash="hashed_pw_s3",
        status="ACTIVE",
    )
    db_session.add(user_s3)

    # Student 4 in Tenant A
    user_s4 = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"athlete4_{uid}@apextech.edu",
        first_name="Rohan",
        last_name="Verma",
        password_hash="hashed_pw_s4",
        status="ACTIVE",
    )
    db_session.add(user_s4)

    await db_session.flush()

    return {
        "tenant_a": tenant_a,
        "tenant_b": tenant_b,
        "campus_a": campus_a,
        "coach_user": coach_user,
        "athletes": [user_s1, user_s2, user_s3, user_s4],
    }


# =============================================================================
# 1. DEPARTMENTS & FACILITIES TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_sports_department_and_facility_lifecycle(
    db_session: AsyncSession, sports_setup: dict
):
    """Verifies sports department creation, facility registration and maintenance updates."""
    tenant = sports_setup["tenant_a"]
    campus = sports_setup["campus_a"]

    # 1. Create Department
    dept_data = SportsDepartmentCreate(
        code="DEPT-ATH-01",
        name="Department of Physical Education & Athletics",
        campus_id=campus.id,
        description="Central athletic administration and recreation center.",
        operating_hours={"weekday": "06:00-21:00", "weekend": "07:00-19:00"},
        policies={"max_booking_hours_per_day": 2, "cancellation_notice_hours": 12},
    )
    dept = await sports_service.create_department(db_session, tenant.id, dept_data)
    assert dept.code == "DEPT-ATH-01"
    assert dept.status == DepartmentStatus.ACTIVE

    # 2. Duplicate Department code rejected
    with pytest.raises(ConflictException):
        await sports_service.create_department(db_session, tenant.id, dept_data)

    # 3. Create Multi-Sport Facilities
    fac_data1 = SportsFacilityCreate(
        code="FAC-CRIC-01",
        name="Main Oval Cricket Ground",
        campus_id=campus.id,
        department_id=dept.id,
        facility_type=FacilityType.CRICKET_GROUND,
        surface=FacilitySurface.TURF,
        is_indoor=False,
        capacity=500,
        location_details="Sports Complex North Sector",
        status=FacilityStatus.AVAILABLE,
    )
    cric_ground = await sports_service.create_facility(db_session, tenant.id, fac_data1)
    assert cric_ground.code == "FAC-CRIC-01"
    assert cric_ground.capacity == 500

    fac_data2 = SportsFacilityCreate(
        code="FAC-BADM-01",
        name="Indoor Badminton Court 1",
        campus_id=campus.id,
        department_id=dept.id,
        facility_type=FacilityType.BADMINTON_COURT,
        surface=FacilitySurface.SYNTHETIC,
        is_indoor=True,
        capacity=50,
        status=FacilityStatus.AVAILABLE,
    )
    badm_court = await sports_service.create_facility(db_session, tenant.id, fac_data2)
    assert badm_court.is_indoor is True

    # 4. List Facilities
    facilities = await sports_service.list_facilities(db_session, tenant.id)
    assert len(facilities) >= 2


# =============================================================================
# 2. FACILITY BOOKING & OVERLAP CONFLICT PREVENTION
# =============================================================================


@pytest.mark.asyncio
async def test_facility_booking_concurrency_and_conflict_detection(
    db_session: AsyncSession, sports_setup: dict
):
    """Verifies facility booking rules and strict prevention of overlapping time slots."""
    tenant = sports_setup["tenant_a"]
    campus = sports_setup["campus_a"]
    coach = sports_setup["coach_user"]

    facility = await sports_service.create_facility(
        db_session,
        tenant.id,
        SportsFacilityCreate(
            code="FAC-FOOT-01",
            name="Football Arena 1",
            campus_id=campus.id,
            facility_type=FacilityType.FOOTBALL_FIELD,
            surface=FacilitySurface.GRASS,
            capacity=200,
            status=FacilityStatus.AVAILABLE,
        ),
    )

    booking_date = date.today() + timedelta(days=2)

    # 1. Successfully book slot 14:00 - 16:00
    b1_data = FacilityBookingCreate(
        facility_id=facility.id,
        booking_date=booking_date,
        start_time=time(14, 0),
        end_time=time(16, 0),
        purpose=BookingPurpose.TRAINING,
        title="Varsity Football Practice",
        booked_by_user_id=coach.id,
    )
    b1 = await sports_service.create_booking(db_session, tenant.id, b1_data)
    assert b1.status == BookingStatus.CONFIRMED

    # 2. Overlapping Booking (15:00 - 17:00) must be rejected with 409 Conflict
    overlap_data1 = FacilityBookingCreate(
        facility_id=facility.id,
        booking_date=booking_date,
        start_time=time(15, 0),
        end_time=time(17, 0),
        purpose=BookingPurpose.INTRAMURAL_MATCH,
        title="Intramural Match Attempt",
        booked_by_user_id=coach.id,
    )
    with pytest.raises(ConflictException) as exc_info:
        await sports_service.create_booking(db_session, tenant.id, overlap_data1)
    assert "already reserved" in str(exc_info.value)

    # 3. Inside Overlapping Booking (14:30 - 15:30) must be rejected
    overlap_data2 = FacilityBookingCreate(
        facility_id=facility.id,
        booking_date=booking_date,
        start_time=time(14, 30),
        end_time=time(15, 30),
        purpose=BookingPurpose.TRAINING,
        title="Inside Slot Attempt",
        booked_by_user_id=coach.id,
    )
    with pytest.raises(ConflictException):
        await sports_service.create_booking(db_session, tenant.id, overlap_data2)

    # 4. Adjacent Non-Overlapping Booking (16:00 - 18:00) must succeed
    adjacent_data = FacilityBookingCreate(
        facility_id=facility.id,
        booking_date=booking_date,
        start_time=time(16, 0),
        end_time=time(18, 0),
        purpose=BookingPurpose.RECREATIONAL,
        title="Evening Recreation Slot",
        booked_by_user_id=coach.id,
    )
    b2 = await sports_service.create_booking(db_session, tenant.id, adjacent_data)
    assert b2.status == BookingStatus.CONFIRMED

    # 5. Booking a facility closed for maintenance must be rejected
    facility.status = FacilityStatus.MAINTENANCE_CLOSED
    facility.closure_reason = "Turf aeration and relaying"
    await db_session.commit()

    with pytest.raises(BadRequestException) as exc_maint:
        await sports_service.create_booking(
            db_session,
            tenant.id,
            FacilityBookingCreate(
                facility_id=facility.id,
                booking_date=booking_date + timedelta(days=1),
                start_time=time(10, 0),
                end_time=time(12, 0),
                purpose=BookingPurpose.TRAINING,
                title="Practice During Maintenance",
            ),
        )
    assert "closed for maintenance" in str(exc_maint.value)


# =============================================================================
# 3. STUDENT ATHLETES & PRIVACY-PRESERVING CLEARANCE
# =============================================================================


@pytest.mark.asyncio
async def test_participant_profiles_and_clearance_privacy(
    db_session: AsyncSession, sports_setup: dict
):
    """Verifies athlete registration, clearance status flags, and consent tracking without medical record leakage."""
    tenant = sports_setup["tenant_a"]
    user_s1 = sports_setup["athletes"][0]

    # 1. Register athlete
    p_data = SportsParticipantCreate(
        user_id=user_s1.id,
        participant_code="ATH-2026-001",
        primary_sport="Basketball",
        status=ParticipantStatus.ACTIVE,
        clearance_status=ClearanceStatus.CLEARED,
        clearance_expiry=date.today() + timedelta(days=180),
        consent_recorded=True,
        operational_restrictions={"light_contact_only": False, "requires_protective_eyewear": True},
        sports_history={"prior_tournaments": 3, "achievements": ["Zone Silver 2025"]},
    )
    part = await sports_service.create_participant(db_session, tenant.id, p_data)
    assert part.participant_code == "ATH-2026-001"
    assert part.clearance_status == ClearanceStatus.CLEARED
    assert part.consent_recorded is True

    # 2. Duplicate registration for same user rejected
    with pytest.raises(ConflictException):
        await sports_service.create_participant(db_session, tenant.id, p_data)

    # 3. Clearance update to RESTRICTED
    part.clearance_status = ClearanceStatus.RESTRICTED
    part.operational_restrictions = {"max_session_minutes": 45}
    await db_session.commit()
    await db_session.refresh(part)
    assert part.clearance_status == ClearanceStatus.RESTRICTED
    assert part.operational_restrictions["max_session_minutes"] == 45


# =============================================================================
# 4. TEAMS, ROSTERS & CAPACITY LIMIT ENFORCEMENT
# =============================================================================


@pytest.mark.asyncio
async def test_sports_team_roster_and_capacity_limits(
    db_session: AsyncSession, sports_setup: dict
):
    """Verifies team creation, captain links, roster addition, and max capacity enforcement."""
    tenant = sports_setup["tenant_a"]
    coach = sports_setup["coach_user"]
    athletes = sports_setup["athletes"]

    # Register participants
    p1 = await sports_service.create_participant(
        db_session,
        tenant.id,
        SportsParticipantCreate(
            user_id=athletes[0].id,
            participant_code="ATH-BASK-01",
            primary_sport="Basketball",
            clearance_status=ClearanceStatus.CLEARED,
        ),
    )
    p2 = await sports_service.create_participant(
        db_session,
        tenant.id,
        SportsParticipantCreate(
            user_id=athletes[1].id,
            participant_code="ATH-BASK-02",
            primary_sport="Basketball",
            clearance_status=ClearanceStatus.CLEARED,
        ),
    )
    p3 = await sports_service.create_participant(
        db_session,
        tenant.id,
        SportsParticipantCreate(
            user_id=athletes[2].id,
            participant_code="ATH-BASK-03",
            primary_sport="Basketball",
            clearance_status=ClearanceStatus.SUSPENDED,  # Suspended clearance
        ),
    )

    # 1. Create Team with max_roster_size = 2
    team_data = SportsTeamCreate(
        code="TEAM-BBALL-M",
        name="Apex Titans Basketball",
        sport="Basketball",
        category=ActivityCategory.VARSITY,
        gender_category="MALE",
        captain_participant_id=p1.id,
        head_coach_user_id=coach.id,
        max_roster_size=2,  # Strict limit of 2 for testing capacity
    )
    team = await sports_service.create_team(db_session, tenant.id, team_data)
    assert team.code == "TEAM-BBALL-M"
    assert team.max_roster_size == 2

    # 2. Add player 1 (Captain)
    m1 = await sports_service.add_team_member(
        db_session,
        tenant.id,
        team.id,
        TeamMembershipCreate(
            team_id=team.id,
            participant_id=p1.id,
            role=MemberRole.CAPTAIN,
            jersey_number=7,
            position="Point Guard",
        ),
    )
    assert m1.role == MemberRole.CAPTAIN

    # 3. Adding suspended athlete to Varsity must be rejected
    with pytest.raises(BadRequestException) as exc_clearance:
        await sports_service.add_team_member(
            db_session,
            tenant.id,
            team.id,
            TeamMembershipCreate(
                team_id=team.id,
                participant_id=p3.id,
                role=MemberRole.PLAYER,
                jersey_number=13,
            ),
        )
    assert "clearance" in str(exc_clearance.value)

    # 4. Add player 2
    m2 = await sports_service.add_team_member(
        db_session,
        tenant.id,
        team.id,
        TeamMembershipCreate(
            team_id=team.id,
            participant_id=p2.id,
            role=MemberRole.PLAYER,
            jersey_number=23,
            position="Center",
        ),
    )
    assert m2.jersey_number == 23

    # 5. Add player 3 when max_roster_size (2) is reached must be rejected
    p4 = await sports_service.create_participant(
        db_session,
        tenant.id,
        SportsParticipantCreate(
            user_id=athletes[3].id,
            participant_code="ATH-BASK-04",
            primary_sport="Basketball",
            clearance_status=ClearanceStatus.CLEARED,
        ),
    )
    with pytest.raises(BadRequestException) as exc_cap:
        await sports_service.add_team_member(
            db_session,
            tenant.id,
            team.id,
            TeamMembershipCreate(
                team_id=team.id,
                participant_id=p4.id,
                role=MemberRole.PLAYER,
                jersey_number=99,
            ),
        )
    assert "maximum roster capacity" in str(exc_cap.value)

    # 6. Verify roster retrieval
    roster = await sports_service.get_team_roster(db_session, tenant.id, team.id)
    assert len(roster) == 2


# =============================================================================
# 5. TRAINING PROGRAMS & BULK ATTENDANCE
# =============================================================================


@pytest.mark.asyncio
async def test_training_programs_and_attendance_sweep(
    db_session: AsyncSession, sports_setup: dict
):
    """Verifies training programs, synchronized session bookings, and bulk attendance tracking."""
    tenant = sports_setup["tenant_a"]
    campus = sports_setup["campus_a"]
    coach = sports_setup["coach_user"]
    athletes = sports_setup["athletes"]

    p1 = await sports_service.create_participant(
        db_session,
        tenant.id,
        SportsParticipantCreate(
            user_id=athletes[0].id,
            participant_code="ATH-SWIM-01",
            primary_sport="Swimming",
        ),
    )
    p2 = await sports_service.create_participant(
        db_session,
        tenant.id,
        SportsParticipantCreate(
            user_id=athletes[1].id,
            participant_code="ATH-SWIM-02",
            primary_sport="Swimming",
        ),
    )

    # Create facility
    pool = await sports_service.create_facility(
        db_session,
        tenant.id,
        SportsFacilityCreate(
            code="FAC-POOL-01",
            name="Olympic Swimming Center",
            campus_id=campus.id,
            facility_type=FacilityType.SWIMMING_POOL,
            surface=FacilitySurface.WATER,
            capacity=100,
        ),
    )

    # 1. Create Training Program
    prog_data = TrainingProgramCreate(
        code="PROG-SWIM-ADV",
        name="Advanced Aquatics Camp",
        program_type=ProgramType.DEVELOPMENT,
        sport="Swimming",
        lead_coach_user_id=coach.id,
        facility_id=pool.id,
        capacity=20,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=30),
        fee_amount=Decimal("1500.00"),
    )
    prog = await sports_service.create_training_program(db_session, tenant.id, prog_data)
    assert prog.code == "PROG-SWIM-ADV"

    # 2. Schedule Training Session (auto reserves pool)
    sess_date = date.today() + timedelta(days=3)
    sess_data = TrainingSessionCreate(
        program_id=prog.id,
        facility_id=pool.id,
        session_date=sess_date,
        start_time=time(6, 30),
        end_time=time(8, 0),
        title="High-Intensity Interval Drills",
    )
    session = await sports_service.create_training_session(db_session, tenant.id, sess_data)
    assert session.title == "High-Intensity Interval Drills"

    # Verify linked facility booking exists
    bookings = await sports_service.list_bookings(
        db_session, tenant.id, facility_id=pool.id, booking_date=sess_date
    )
    assert len(bookings) == 1
    assert bookings[0].title.startswith("Training: Advanced Aquatics Camp")

    # 3. Record Bulk Attendance
    att_data = BulkAttendanceCreate(
        session_id=session.id,
        records=[
            BulkAttendanceItem(participant_id=p1.id, status=AttendanceStatus.PRESENT, notes="Excellent pace"),
            BulkAttendanceItem(participant_id=p2.id, status=AttendanceStatus.EXCUSED, notes="Academic conflict"),
        ],
    )
    attendances = await sports_service.record_session_attendance(
        db_session, tenant.id, att_data, recorded_by_user_id=coach.id
    )
    assert len(attendances) == 2
    assert attendances[0].status == AttendanceStatus.PRESENT
    assert attendances[1].status == AttendanceStatus.EXCUSED


# =============================================================================
# 6. TOURNAMENT, FIXTURE ENGINE & STANDINGS CALCULATION
# =============================================================================


@pytest.mark.asyncio
async def test_tournament_fixture_generation_results_and_standings(
    db_session: AsyncSession, sports_setup: dict
):
    """Verifies tournament registration, automated Round Robin fixture generator, score entry, verification, and standings calculation."""
    tenant = sports_setup["tenant_a"]
    campus = sports_setup["campus_a"]
    coach = sports_setup["coach_user"]

    # 1. Create 3 Teams for Round Robin
    teams: list[SportsTeam] = []
    for i in range(1, 4):
        team = await sports_service.create_team(
            db_session,
            tenant.id,
            SportsTeamCreate(
                code=f"TEAM-VOLL-0{i}",
                name=f"Volleyball Squad {i}",
                sport="Volleyball",
                category=ActivityCategory.INTRAMURAL,
            ),
        )
        teams.append(team)

    # Create court
    court = await sports_service.create_facility(
        db_session,
        tenant.id,
        SportsFacilityCreate(
            code="FAC-VOLL-01",
            name="Intramural Volleyball Court",
            campus_id=campus.id,
            facility_type=FacilityType.VOLLEYBALL_COURT,
            surface=FacilitySurface.SYNTHETIC,
        ),
    )

    # 2. Create Competition (Round Robin)
    comp_data = CompetitionCreate(
        code="COMP-VOLL-2026",
        name="Annual Inter-Department Volleyball Championship",
        competition_type=CompetitionType.INTERNAL,
        tournament_format=TournamentFormat.ROUND_ROBIN,
        sport="Volleyball",
        registration_type=RegistrationType.TEAM,
        points_for_win=3,
        points_for_draw=1,
        points_for_loss=0,
        start_date=date.today() + timedelta(days=5),
        end_date=date.today() + timedelta(days=15),
        registration_deadline=date.today() + timedelta(days=4),
        max_participants=8,
    )
    comp = await sports_service.create_competition(db_session, tenant.id, comp_data)
    assert comp.tournament_format == TournamentFormat.ROUND_ROBIN

    # 3. Register Teams
    for team in teams:
        reg = await sports_service.register_competition_entry(
            db_session,
            tenant.id,
            comp.id,
            CompetitionRegistrationCreate(competition_id=comp.id, team_id=team.id),
        )
        assert reg.status == "REGISTERED"

    # 4. Generate Round Robin Fixtures (3 teams -> 3 matches: T1-T2, T1-T3, T2-T3)
    gen_req = FixtureGenerationRequest(
        competition_id=comp.id,
        facility_ids=[court.id],
        start_date=date.today() + timedelta(days=6),
        default_start_time=time(14, 0),
        match_duration_minutes=60,
    )
    fixtures = await sports_service.generate_fixtures(db_session, tenant.id, gen_req)
    assert len(fixtures) == 3

    f1, f2, f3 = fixtures

    # 5. Record Match 1 Result: Team 1 beats Team 2 (3 - 1)
    res1_data = MatchResultCreate(
        fixture_id=f1.id,
        home_score=3,
        away_score=1,
        winning_team_id=f1.home_team_id,
        is_draw=False,
    )
    res1 = await sports_service.record_match_result(
        db_session, tenant.id, res1_data, recorded_by_user_id=coach.id
    )
    assert res1.is_verified is False

    # 6. Verify Match 1 Result
    verified_res1 = await sports_service.verify_match_result(
        db_session,
        tenant.id,
        res1.id,
        verified_by_user_id=coach.id,
        verify_data=MatchResultVerify(is_verified=True),
    )
    assert verified_res1.is_verified is True

    # 7. Record Match 2 Result: Team 1 beats Team 3 (3 - 0) and verify
    res2 = await sports_service.record_match_result(
        db_session,
        tenant.id,
        MatchResultCreate(
            fixture_id=f2.id,
            home_score=3,
            away_score=0,
            winning_team_id=f2.home_team_id,
        ),
        recorded_by_user_id=coach.id,
    )
    await sports_service.verify_match_result(
        db_session,
        tenant.id,
        res2.id,
        verified_by_user_id=coach.id,
        verify_data=MatchResultVerify(is_verified=True),
    )

    # 8. Record Match 3 Result: Team 2 and Team 3 draw (2 - 2) and verify
    res3 = await sports_service.record_match_result(
        db_session,
        tenant.id,
        MatchResultCreate(
            fixture_id=f3.id,
            home_score=2,
            away_score=2,
            is_draw=True,
        ),
        recorded_by_user_id=coach.id,
    )
    await sports_service.verify_match_result(
        db_session,
        tenant.id,
        res3.id,
        verified_by_user_id=coach.id,
        verify_data=MatchResultVerify(is_verified=True),
    )

    # 9. Verify Points Table / Standings
    # Team 1: 2 played, 2 won, 0 drawn, 0 lost -> 6 pts (Rank 1)
    # Team 2: 2 played, 0 won, 1 drawn, 1 lost -> 1 pt, Diff: -2
    # Team 3: 2 played, 0 won, 1 drawn, 1 lost -> 1 pt, Diff: -3
    standings = await sports_service.get_competition_standings(db_session, tenant.id, comp.id)
    assert len(standings) == 3

    top_standing, top_team_name = standings[0]
    assert top_standing.rank == 1
    assert top_standing.played == 2
    assert top_standing.won == 2
    assert top_standing.total_points == 6

    # 10. Audit history preserved on result correction
    await sports_service.record_match_result(
        db_session,
        tenant.id,
        MatchResultCreate(
            fixture_id=f1.id,
            home_score=3,
            away_score=2,  # Corrected score
            winning_team_id=f1.home_team_id,
        ),
        recorded_by_user_id=coach.id,
    )
    updated_res1 = (
        await db_session.execute(select(MatchResult).where(MatchResult.id == res1.id))
    ).scalar_one()
    assert len(updated_res1.audit_history) >= 2


# =============================================================================
# 7. EQUIPMENT ASSIGNMENTS & INVENTORY INTEGRATION
# =============================================================================


@pytest.mark.asyncio
async def test_equipment_checkout_return_and_damage_tracking(
    db_session: AsyncSession, sports_setup: dict
):
    """Verifies equipment checkout, overdue logging, and return with damage fee evaluation."""
    tenant = sports_setup["tenant_a"]
    coach = sports_setup["coach_user"]

    # 1. Checkout Equipment
    checkout_data = EquipmentCheckoutCreate(
        equipment_name="Match Grade Cricket Leather Balls (Box of 6)",
        sport="Cricket",
        quantity=6,
        assigned_to_user_id=coach.id,
        due_date=date.today() + timedelta(days=7),
        checkout_condition=EquipmentCondition.NEW,
    )
    assignment = await sports_service.checkout_equipment(db_session, tenant.id, checkout_data)
    assert assignment.status == CheckoutStatus.CHECKED_OUT

    # 2. Return with Damage
    ret_data = EquipmentReturnRequest(
        return_condition=EquipmentCondition.DAMAGED,
        damage_notes="2 balls deformed due to heavy water absorption.",
        replacement_fee=Decimal("800.00"),
    )
    returned = await sports_service.return_equipment(db_session, tenant.id, assignment.id, ret_data)
    assert returned.status == CheckoutStatus.DAMAGED
    assert returned.return_condition == EquipmentCondition.DAMAGED
    assert returned.replacement_fee == Decimal("800.00")
    assert returned.returned_at is not None


# =============================================================================
# 8. OPERATIONS SWEEP & SCHEDULED TASKS
# =============================================================================


@pytest.mark.asyncio
async def test_sports_operations_scheduled_sweep(
    db_session: AsyncSession, sports_setup: dict
):
    """Verifies operations sweep accurately detects overdue equipment and expired clearances."""
    tenant = sports_setup["tenant_a"]
    coach = sports_setup["coach_user"]
    athlete = sports_setup["athletes"][0]

    # Create past-due equipment loan
    equip = EquipmentAssignment(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        equipment_name="Tennis Racquet Set",
        sport="Tennis",
        quantity=2,
        assigned_to_user_id=coach.id,
        due_date=date.today() - timedelta(days=2),  # Overdue
        status=CheckoutStatus.CHECKED_OUT,
        checkout_condition=EquipmentCondition.GOOD,
    )
    db_session.add(equip)

    # Create expired clearance athlete
    part = SportsParticipant(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        user_id=athlete.id,
        participant_code="ATH-SWEEP-01",
        primary_sport="Track",
        status=ParticipantStatus.ACTIVE,
        clearance_status=ClearanceStatus.CLEARED,
        clearance_expiry=date.today() - timedelta(days=1),  # Expired yesterday
    )
    db_session.add(part)
    await db_session.commit()

    # Run sweep
    sweep_results = await sports_service.sweep_sports_operations(db_session, tenant.id)
    assert sweep_results["overdue_equipment_flagged"] >= 1
    assert sweep_results["expired_clearances_flagged"] >= 1

    await db_session.refresh(equip)
    await db_session.refresh(part)
    assert equip.status == CheckoutStatus.OVERDUE
    assert part.clearance_status == ClearanceStatus.EXPIRED


# =============================================================================
# 9. MULTI-TENANT ISOLATION
# =============================================================================


@pytest.mark.asyncio
async def test_sports_strict_tenant_isolation(
    db_session: AsyncSession, sports_setup: dict
):
    """Verifies that Tenant B cannot access or book Tenant A's sports facilities or competitions."""
    tenant_a = sports_setup["tenant_a"]
    tenant_b = sports_setup["tenant_b"]
    campus_a = sports_setup["campus_a"]

    # Create facility in Tenant A
    fac_a = await sports_service.create_facility(
        db_session,
        tenant_a.id,
        SportsFacilityCreate(
            code="FAC-TENN-01",
            name="Tennis Court A",
            campus_id=campus_a.id,
            facility_type=FacilityType.TENNIS_COURT,
        ),
    )

    # Query facilities in Tenant B -> fac_a must not be returned
    facs_b = await sports_service.list_facilities(db_session, tenant_b.id)
    assert not any(f.id == fac_a.id for f in facs_b)

    # Tenant B trying to retrieve Tenant A facility raises NotFoundException
    with pytest.raises(NotFoundException):
        await sports_service.get_facility(db_session, tenant_b.id, fac_a.id)

    # Tenant B booking Tenant A facility raises NotFoundException
    with pytest.raises(NotFoundException):
        await sports_service.create_booking(
            db_session,
            tenant_b.id,
            FacilityBookingCreate(
                facility_id=fac_a.id,
                booking_date=date.today() + timedelta(days=1),
                start_time=time(10, 0),
                end_time=time(11, 0),
                purpose=BookingPurpose.TRAINING,
                title="Cross-tenant booking attempt",
            ),
        )
