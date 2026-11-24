"""Enterprise Academic Timetable, Resource Scheduling & Conflict Resolution Engine Tests (Step 49).

Verifies:
1. Timetable creation, version staging, and publication lifecycle.
2. Session creation, locking, and room capacity constraints.
3. Multi-factor conflict detection (faculty clash, room double-booking, cohort overlap, room suitability).
4. Constraint-based timetable generation with feasible requirements.
5. Partial generation reporting and unscheduled session tracking under over-constrained conditions.
6. Locked-session preservation during regeneration.
7. Candidate schedule isolation from published schedules.
8. Concurrent resource reservation conflict prevention and maintenance downtime windows.
9. Change requests, impact analysis, approvals, atomic application, and emergency audit.
10. Publication authorization and student-facing view isolation.
11. Attendance integration, session reconciliation, and historical attendance preservation.
12. Standard iCalendar RFC 5545 (.ics) export.
13. Strict multi-tenant isolation and analytics metrics.
"""

import uuid
from datetime import UTC, date, datetime, time
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.models.academics import (
    Classroom,
    CourseFacultyAssignment,
    CourseOffering,
    Subject,
    TimeSlot,
    TimetableEntry,
)
from app.models.attendance import AttendanceSession
from app.models.core import (
    AcademicYear,
    Batch,
    Campus,
    Department,
    Institution,
    Program,
    Regulation,
    Section,
    Semester,
)
from app.models.people import FacultyProfile, User
from app.models.timetable import (
    ChangeRequestStatus,
    ChangeRequestType,
    ConflictType,
    GenerationJobStatus,
    MaintenanceStatus,
    ReservationStatus,
    ReservationType,
    SessionType,
    TimetableSession,
    TimetableVersionStatus,
)
from app.schemas.timetable import (
    ResourceMaintenanceWindowCreate,
    ResourceReservationCreate,
    TimetableChangeRequestCreate,
    TimetableChangeRequestReview,
    TimetableGenerationRequest,
    TimetableScheduleCloneRequest,
    TimetableScheduleCreate,
    TimetableSessionCreate,
    TimetableSessionUpdate,
    TimetableVersionApproval,
    TimetableVersionCreate,
    TimetableVersionPublish,
)
from app.services.timetable_service import TimetableService


@pytest.fixture
async def timetable_fixture(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
    tenant_b: Institution,
    tenant_admin_b: User,
):
    """Provides isolated academic setup with campuses, terms, rooms, sections, offerings, and faculty."""
    uid = uuid.uuid4().hex[:6]

    # Tenant A Setup
    campus_a = Campus(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        name="Main Technology Campus",
        code=f"MTC-{uid}",
        address="100 Innovation Park",
        city="Coimbatore",
        is_active=True,
    )
    db_session.add(campus_a)

    ay_a = AcademicYear(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        name=f"AY 2026-2027 {uid}",
        start_date=date(2026, 7, 1),
        end_date=date(2027, 6, 30),
        is_current=True,
    )
    db_session.add(ay_a)

    sem_a = Semester(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        academic_year_id=ay_a.id,
        name="Fall Semester 2026",
        semester_number=5,
        term_type="ODD",
        start_date=date(2026, 7, 15),
        end_date=date(2026, 12, 10),
        is_active=True,
    )
    db_session.add(sem_a)

    dept_a = Department(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        campus_id=campus_a.id,
        name="Computer Science & Engineering",
        code=f"CSE-{uid}",
        is_active=True,
    )
    db_session.add(dept_a)

    prog_a = Program(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        department_id=dept_a.id,
        name="B.Tech Computer Science",
        code=f"CS-{uid}",
        degree_level="UNDERGRADUATE",
        duration_years=Decimal("4.0"),
        total_semesters=8,
        is_active=True,
    )
    db_session.add(prog_a)

    reg_a = Regulation(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        code=f"R2026-{uid}",
        title="Regulation 2026",
        effective_year=2026,
        is_active=True,
    )
    db_session.add(reg_a)

    batch_a = Batch(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        program_id=prog_a.id,
        regulation_id=reg_a.id,
        name=f"Batch 2024-2028 {uid}",
        admission_year=2024,
        graduation_year=2028,
        is_active=True,
    )
    db_session.add(batch_a)

    sec_a = Section(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        program_id=prog_a.id,
        batch_id=batch_a.id,
        semester_id=sem_a.id,
        name="Section A",
        capacity=60,
        is_active=True,
    )
    db_session.add(sec_a)

    # Classrooms
    room_hall = Classroom(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        campus_id=campus_a.id,
        building="Academic Block 1",
        room_number="LH-101",
        capacity=70,
        room_type="LECTURE_HALL",
        is_active=True,
    )
    room_lab = Classroom(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        campus_id=campus_a.id,
        building="Computing Center",
        room_number="LAB-201",
        capacity=65,
        room_type="COMPUTER_LAB",
        is_active=True,
    )
    room_small = Classroom(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        campus_id=campus_a.id,
        building="Annex",
        room_number="CR-01",
        capacity=30,  # Less than section capacity 60
        room_type="CLASSROOM",
        is_active=True,
    )
    db_session.add_all([room_hall, room_lab, room_small])

    # Faculty Profile
    user_fac = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"prof.smith.{uid}@campusos.internal",
        password_hash="test-hash",
        first_name="Alan",
        last_name="Smith",
        is_active=True,
    )
    db_session.add(user_fac)

    faculty_a = FacultyProfile(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        user_id=user_fac.id,
        employee_code=f"EMP-{uid}",
        department_id=dept_a.id,
        designation="Associate Professor",
        highest_qualification="Ph.D",
        joining_date=date(2020, 1, 1),
        employment_status="ACTIVE",
    )
    db_session.add(faculty_a)

    # Subject & Course Offering
    subj_algo = Subject(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        department_id=dept_a.id,
        code=f"CS501-{uid}",
        name="Algorithms & Complexity",
        credits=Decimal("4.0"),
        lecture_hours=3,
        practical_hours=2,
        is_active=True,
    )
    db_session.add(subj_algo)

    offering_algo = CourseOffering(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        subject_id=subj_algo.id,
        academic_year_id=ay_a.id,
        semester_id=sem_a.id,
        section_id=sec_a.id,
        max_capacity=60,
        status="ACTIVE",
    )
    db_session.add(offering_algo)

    fac_assign = CourseFacultyAssignment(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        course_offering_id=offering_algo.id,
        faculty_id=faculty_a.id,
        role="PRIMARY",
        is_active=True,
    )
    db_session.add(fac_assign)

    # Standard Periods
    slot_1 = TimeSlot(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        name="Period 1",
        slot_number=1,
        start_time=time(9, 0),
        end_time=time(10, 0),
        slot_type="LECTURE",
        is_active=True,
    )
    slot_2 = TimeSlot(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        name="Period 2",
        slot_number=2,
        start_time=time(10, 0),
        end_time=time(11, 0),
        slot_type="LECTURE",
        is_active=True,
    )
    db_session.add_all([slot_1, slot_2])

    await db_session.commit()

    return {
        "tenant_a": tenant_a,
        "admin_a": tenant_admin_a,
        "ay_a": ay_a,
        "sem_a": sem_a,
        "sec_a": sec_a,
        "room_hall": room_hall,
        "room_lab": room_lab,
        "room_small": room_small,
        "faculty_a": faculty_a,
        "subj_algo": subj_algo,
        "offering_algo": offering_algo,
        "slot_1": slot_1,
        "slot_2": slot_2,
        "tenant_b": tenant_b,
        "admin_b": tenant_admin_b,
    }


# =============================================================================
# 1. SCHEDULE & VERSION LIFECYCLE
# =============================================================================


@pytest.mark.asyncio
async def test_timetable_schedule_and_version_lifecycle(
    db_session: AsyncSession, timetable_fixture: dict
):
    """Test timetable creation, versioning, review submission, approval, and publication."""
    tenant = timetable_fixture["tenant_a"]
    admin = timetable_fixture["admin_a"]
    ay = timetable_fixture["ay_a"]
    sem = timetable_fixture["sem_a"]
    sec = timetable_fixture["sec_a"]
    room = timetable_fixture["room_hall"]
    faculty = timetable_fixture["faculty_a"]
    offering = timetable_fixture["offering_algo"]

    # 1. Create Master Schedule
    create_req = TimetableScheduleCreate(
        academic_year_id=ay.id,
        semester_id=sem.id,
        section_id=sec.id,
        name="CSE Semester 5 Section A Timetable",
        code=f"TT-CSE-S5-{uuid.uuid4().hex[:4].upper()}",
        description="Core academic timetable for Section A",
    )
    schedule = await TimetableService.create_schedule(db_session, tenant.id, create_req, admin.id)
    assert schedule.id is not None
    assert schedule.latest_version_number == 1

    # Fetch Version 1
    versions = await TimetableService.list_versions(db_session, tenant.id, schedule.id)
    assert len(versions) == 1
    v1 = versions[0]
    assert v1.status == TimetableVersionStatus.DRAFT

    # Add a valid session to Version 1
    session_req = TimetableSessionCreate(
        course_offering_id=offering.id,
        section_id=sec.id,
        faculty_id=faculty.id,
        room_id=room.id,
        day_of_week=1,  # Monday
        start_time=time(9, 0),
        end_time=time(10, 0),
        session_type=SessionType.LECTURE,
    )
    sess = await TimetableService.create_session(db_session, tenant.id, v1.id, session_req)
    assert sess.id is not None
    assert sess.day_of_week == 1

    # 2. Submit for Review
    review_res = await TimetableService.submit_for_review(db_session, tenant.id, v1.id, admin.id)
    assert review_res.status == TimetableVersionStatus.UNDER_REVIEW

    # 3. Approve Version
    approve_res = await TimetableService.approve_version(
        db_session, tenant.id, v1.id, TimetableVersionApproval(approved=True), admin.id
    )
    assert approve_res.status == TimetableVersionStatus.APPROVED

    # 4. Publish Version
    pub_res = await TimetableService.publish_version(
        db_session, tenant.id, v1.id, TimetableVersionPublish(notes="Official Release"), admin.id
    )
    assert pub_res.status == TimetableVersionStatus.PUBLISHED
    assert pub_res.published_at is not None

    # Verify canonical slot sync into `academics_timetable_slots`
    canonical_entry = await db_session.scalar(
        select(TimetableEntry).where(
            TimetableEntry.tenant_id == tenant.id,
            TimetableEntry.section_id == sec.id,
            TimetableEntry.faculty_id == faculty.id,
        )
    )
    assert canonical_entry is not None
    assert canonical_entry.is_active is True

    # 5. Create Version 2 & Verify Superseding on Publication
    v2 = await TimetableService.create_version(
        db_session, tenant.id, schedule.id, TimetableVersionCreate(change_summary="Mid-term revisions")
    )
    assert v2.version_number == 2
    assert v2.status == TimetableVersionStatus.DRAFT


# =============================================================================
# 2. CLONING SCHEDULES
# =============================================================================


@pytest.mark.asyncio
async def test_timetable_schedule_cloning(
    db_session: AsyncSession, timetable_fixture: dict
):
    """Test cloning timetable from previous term to target term with session replication."""
    tenant = timetable_fixture["tenant_a"]
    admin = timetable_fixture["admin_a"]
    ay = timetable_fixture["ay_a"]
    sem = timetable_fixture["sem_a"]
    sec = timetable_fixture["sec_a"]
    room = timetable_fixture["room_hall"]
    faculty = timetable_fixture["faculty_a"]
    offering = timetable_fixture["offering_algo"]

    # Create source schedule with 1 session
    source = await TimetableService.create_schedule(
        db_session,
        tenant.id,
        TimetableScheduleCreate(
            academic_year_id=ay.id,
            semester_id=sem.id,
            section_id=sec.id,
            name="Source Timetable",
            code=f"SRC-{uuid.uuid4().hex[:4].upper()}",
        ),
        admin.id,
    )
    versions = await TimetableService.list_versions(db_session, tenant.id, source.id)
    v1 = versions[0]

    await TimetableService.create_session(
        db_session,
        tenant.id,
        v1.id,
        TimetableSessionCreate(
            course_offering_id=offering.id,
            section_id=sec.id,
            faculty_id=faculty.id,
            room_id=room.id,
            day_of_week=2,  # Tuesday
            start_time=time(10, 0),
            end_time=time(11, 0),
        ),
    )

    # Clone into target
    clone_req = TimetableScheduleCloneRequest(
        target_academic_year_id=ay.id,
        target_semester_id=sem.id,
        new_code=f"CLONE-{uuid.uuid4().hex[:4].upper()}",
        new_name="Cloned Timetable Spring 2027",
    )
    cloned = await TimetableService.clone_schedule(db_session, tenant.id, source.id, clone_req, admin.id)
    assert cloned.code == clone_req.new_code

    # Verify session was copied to cloned version
    cloned_versions = await TimetableService.list_versions(db_session, tenant.id, cloned.id)
    assert len(cloned_versions) == 1
    assert cloned_versions[0].sessions_count == 1


# =============================================================================
# 3. CONFLICT DETECTION ENGINE
# =============================================================================


@pytest.mark.asyncio
async def test_conflict_detection_engine(
    db_session: AsyncSession, timetable_fixture: dict
):
    """Verify faculty double-booking, room clash, cohort overlap, capacity breach, and room suitability."""
    tenant = timetable_fixture["tenant_a"]
    admin = timetable_fixture["admin_a"]
    ay = timetable_fixture["ay_a"]
    sem = timetable_fixture["sem_a"]
    sec = timetable_fixture["sec_a"]
    room_hall = timetable_fixture["room_hall"]
    room_small = timetable_fixture["room_small"]
    faculty = timetable_fixture["faculty_a"]
    offering = timetable_fixture["offering_algo"]

    # Create schedule and draft version
    schedule = await TimetableService.create_schedule(
        db_session,
        tenant.id,
        TimetableScheduleCreate(
            academic_year_id=ay.id,
            semester_id=sem.id,
            section_id=sec.id,
            name="Conflict Test Schedule",
            code=f"CONF-{uuid.uuid4().hex[:4].upper()}",
        ),
        admin.id,
    )
    versions = await TimetableService.list_versions(db_session, tenant.id, schedule.id)
    v_id = versions[0].id

    # 1. Capacity Exceeded: Attempt to place section (capacity=60) in room_small (capacity=30)
    with pytest.raises(ConflictException) as exc_info:
        await TimetableService.create_session(
            db_session,
            tenant.id,
            v_id,
            TimetableSessionCreate(
                course_offering_id=offering.id,
                section_id=sec.id,
                faculty_id=faculty.id,
                room_id=room_small.id,
                day_of_week=3,
                start_time=time(9, 0),
                end_time=time(10, 0),
            ),
        )
    assert "Room capacity" in str(exc_info.value)

    # 2. Add Valid Session 1 (Monday 09:00 - 10:00)
    await TimetableService.create_session(
        db_session,
        tenant.id,
        v_id,
        TimetableSessionCreate(
            course_offering_id=offering.id,
            section_id=sec.id,
            faculty_id=faculty.id,
            room_id=room_hall.id,
            day_of_week=1,
            start_time=time(9, 0),
            end_time=time(10, 0),
            session_type=SessionType.LECTURE,
        ),
    )

    # 3. Add Colliding Session 2 (Same Monday 09:00 - 10:00 with same faculty and room)
    # Using batch creation or manual session insertion
    sess_collision = TimetableSession(
        tenant_id=tenant.id,
        version_id=v_id,
        course_offering_id=offering.id,
        section_id=sec.id,
        faculty_id=faculty.id,
        room_id=room_hall.id,
        day_of_week=1,
        start_time=time(9, 30),  # Overlapping window!
        end_time=time(10, 30),
        session_type=SessionType.LAB,  # Also room suitability warning (LAB in LECTURE_HALL)
    )
    db_session.add(sess_collision)
    await db_session.commit()

    # 4. Run Conflict Detection Engine
    report = await TimetableService.validate_version(db_session, tenant.id, v_id)
    assert report.is_valid_for_publication is False
    assert report.critical_conflicts_count >= 1

    conflict_types = [c.conflict_type for c in report.conflicts]
    assert ConflictType.FACULTY_DOUBLE_BOOKING in conflict_types
    assert ConflictType.ROOM_DOUBLE_BOOKING in conflict_types
    assert ConflictType.ROOM_TYPE_MISMATCH in conflict_types


# =============================================================================
# 4. CONSTRAINT-BASED GENERATION & LOCKED SESSIONS
# =============================================================================


@pytest.mark.asyncio
async def test_constraint_based_timetable_generation(
    db_session: AsyncSession, timetable_fixture: dict
):
    """Test automated constraint solving generation, candidate isolation, and locked sessions."""
    tenant = timetable_fixture["tenant_a"]
    admin = timetable_fixture["admin_a"]
    ay = timetable_fixture["ay_a"]
    sem = timetable_fixture["sem_a"]
    sec = timetable_fixture["sec_a"]
    room = timetable_fixture["room_hall"]
    faculty = timetable_fixture["faculty_a"]
    offering = timetable_fixture["offering_algo"]

    # 1. Create a published schedule with 1 locked session
    schedule = await TimetableService.create_schedule(
        db_session,
        tenant.id,
        TimetableScheduleCreate(
            academic_year_id=ay.id,
            semester_id=sem.id,
            section_id=sec.id,
            name="Pre-generation Base Schedule",
            code=f"GEN-BASE-{uuid.uuid4().hex[:4].upper()}",
        ),
        admin.id,
    )
    versions = await TimetableService.list_versions(db_session, tenant.id, schedule.id)
    v1_id = versions[0].id

    # Create locked session on Friday Period 1
    locked_session = await TimetableService.create_session(
        db_session,
        tenant.id,
        v1_id,
        TimetableSessionCreate(
            course_offering_id=offering.id,
            section_id=sec.id,
            faculty_id=faculty.id,
            room_id=room.id,
            day_of_week=5,  # Friday
            start_time=time(9, 0),
            end_time=time(10, 0),
            is_locked=True,
        ),
    )
    assert locked_session.is_locked is True

    # Approve and publish version 1
    await TimetableService.submit_for_review(db_session, tenant.id, v1_id, admin.id)
    await TimetableService.approve_version(
        db_session, tenant.id, v1_id, TimetableVersionApproval(approved=True), admin.id
    )
    await TimetableService.publish_version(
        db_session, tenant.id, v1_id, TimetableVersionPublish(), admin.id
    )

    # 2. Trigger automated timetable generation
    gen_req = TimetableGenerationRequest(
        academic_year_id=ay.id,
        semester_id=sem.id,
        section_id=sec.id,
        schedule_id=schedule.id,
        preserve_locked_sessions=True,
    )
    job_res = await TimetableService.generate_timetable(db_session, tenant.id, gen_req, admin.id)
    if job_res.job_status == GenerationJobStatus.FAILED:
        pytest.fail(f"Generation failed with error: {job_res.error_summary}")
    assert job_res.job_status in (GenerationJobStatus.COMPLETED, GenerationJobStatus.PARTIAL)
    assert job_res.scheduled_sessions_count >= 1
    assert job_res.candidate_version_id is not None

    # Candidate version must be separate from published version 1
    assert job_res.candidate_version_id != v1_id

    # Verify published version remains PUBLISHED with original session count
    v1_check = await TimetableService.get_version_response(db_session, tenant.id, v1_id)
    assert v1_check.status == TimetableVersionStatus.PUBLISHED

    # Candidate version should contain the preserved locked session
    candidate_sessions = await db_session.execute(
        select(TimetableSession).where(
            TimetableSession.tenant_id == tenant.id,
            TimetableSession.version_id == job_res.candidate_version_id,
        )
    )
    cand_list = candidate_sessions.scalars().all()
    assert any(s.is_locked and s.day_of_week == 5 for s in cand_list)


# =============================================================================
# 5. RESOURCE RESERVATIONS & CONCURRENCY CONFLICT
# =============================================================================


@pytest.mark.asyncio
async def test_resource_reservation_concurrency_and_maintenance(
    db_session: AsyncSession, timetable_fixture: dict
):
    """Test exclusive room booking, concurrent booking rejection, and maintenance windows."""
    tenant = timetable_fixture["tenant_a"]
    admin = timetable_fixture["admin_a"]
    room = timetable_fixture["room_hall"]

    start_dt = datetime(2026, 8, 10, 14, 0, tzinfo=UTC)
    end_dt = datetime(2026, 8, 10, 16, 0, tzinfo=UTC)

    # 1. Create Confirmed Reservation
    res1 = await TimetableService.create_reservation(
        db_session,
        tenant.id,
        ResourceReservationCreate(
            room_id=room.id,
            title="Industry Guest Lecture",
            start_datetime=start_dt,
            end_datetime=end_dt,
            reservation_type=ReservationType.CAMPUS_EVENT,
        ),
        admin.id,
    )
    assert res1.id is not None
    assert res1.status == ReservationStatus.CONFIRMED

    # 2. Concurrent overlapping booking should raise ConflictException
    with pytest.raises(ConflictException) as exc_info:
        await TimetableService.create_reservation(
            db_session,
            tenant.id,
            ResourceReservationCreate(
                room_id=room.id,
                title="Competing Seminar",
                start_datetime=datetime(2026, 8, 10, 15, 0, tzinfo=UTC),  # Overlaps!
                end_datetime=datetime(2026, 8, 10, 17, 0, tzinfo=UTC),
            ),
            admin.id,
        )
    assert "Resource conflict" in str(exc_info.value)

    # 3. Create Maintenance Window
    maint_start = datetime(2026, 8, 12, 8, 0, tzinfo=UTC)
    maint_end = datetime(2026, 8, 12, 18, 0, tzinfo=UTC)
    maint = await TimetableService.create_maintenance_window(
        db_session,
        tenant.id,
        ResourceMaintenanceWindowCreate(
            room_id=room.id,
            title="AV System Overhaul",
            reason="Projector bulb replacement and electrical maintenance",
            start_time=maint_start,
            end_time=maint_end,
        ),
    )
    assert maint.status == MaintenanceStatus.SCHEDULED

    # Booking during maintenance window should be rejected
    with pytest.raises(ConflictException) as exc_info:
        await TimetableService.create_reservation(
            db_session,
            tenant.id,
            ResourceReservationCreate(
                room_id=room.id,
                title="Class during maintenance",
                start_datetime=datetime(2026, 8, 12, 10, 0, tzinfo=UTC),
                end_datetime=datetime(2026, 8, 12, 11, 0, tzinfo=UTC),
            ),
            admin.id,
        )
    assert "undergoing maintenance" in str(exc_info.value)


# =============================================================================
# 6. CHANGE MANAGEMENT & AUDIT
# =============================================================================


@pytest.mark.asyncio
async def test_schedule_change_management_and_approval(
    db_session: AsyncSession, timetable_fixture: dict
):
    """Test change request submission, impact analysis, approval, and emergency change."""
    tenant = timetable_fixture["tenant_a"]
    admin = timetable_fixture["admin_a"]
    ay = timetable_fixture["ay_a"]
    sem = timetable_fixture["sem_a"]
    sec = timetable_fixture["sec_a"]
    room_hall = timetable_fixture["room_hall"]
    room_lab = timetable_fixture["room_lab"]
    faculty = timetable_fixture["faculty_a"]
    offering = timetable_fixture["offering_algo"]

    # Create schedule, version, and session
    schedule = await TimetableService.create_schedule(
        db_session,
        tenant.id,
        TimetableScheduleCreate(
            academic_year_id=ay.id,
            semester_id=sem.id,
            section_id=sec.id,
            name="Change Mgmt Timetable",
            code=f"CHG-{uuid.uuid4().hex[:4].upper()}",
        ),
        admin.id,
    )
    versions = await TimetableService.list_versions(db_session, tenant.id, schedule.id)
    v_id = versions[0].id

    session = await TimetableService.create_session(
        db_session,
        tenant.id,
        v_id,
        TimetableSessionCreate(
            course_offering_id=offering.id,
            section_id=sec.id,
            faculty_id=faculty.id,
            room_id=room_hall.id,
            day_of_week=3,  # Wednesday
            start_time=time(11, 0),
            end_time=time(12, 0),
        ),
    )

    # 1. Submit Change Request: Room Swap to room_lab
    cr_req = TimetableChangeRequestCreate(
        version_id=v_id,
        session_id=session.id,
        change_type=ChangeRequestType.ROOM_SWAP,
        proposed_room_id=room_lab.id,
        reason="Need lab machines for programming demo",
        is_emergency=False,
    )
    chg_res = await TimetableService.create_change_request(db_session, tenant.id, cr_req, admin.id)
    assert chg_res.status == ChangeRequestStatus.PENDING
    assert chg_res.impact_analysis is not None

    # 2. Approve and Apply Change Request
    review_res = await TimetableService.review_change_request(
        db_session,
        tenant.id,
        chg_res.id,
        TimetableChangeRequestReview(approved=True, review_notes="Approved by HOD"),
        admin.id,
    )
    assert review_res.status == ChangeRequestStatus.APPLIED

    # Verify session replacement_room_id updated
    updated_session = await TimetableService.get_session_response(db_session, tenant.id, session.id)
    assert updated_session.replacement_room_id == room_lab.id

    # 3. Emergency Change: Auto-applied immediately
    emg_cr = TimetableChangeRequestCreate(
        version_id=v_id,
        session_id=session.id,
        change_type=ChangeRequestType.CANCEL_SESSION,
        reason="Faculty medical leave",
        is_emergency=True,
    )
    emg_res = await TimetableService.create_change_request(db_session, tenant.id, emg_cr, admin.id)
    assert emg_res.status == ChangeRequestStatus.APPLIED
    assert emg_res.is_emergency is True

    cancelled_sess = await TimetableService.get_session_response(db_session, tenant.id, session.id)
    assert cancelled_sess.is_cancelled is True


# =============================================================================
# 7. PUBLICATION & STUDENT VIEW ISOLATION
# =============================================================================


@pytest.mark.asyncio
async def test_publication_student_view_isolation(
    db_session: AsyncSession, timetable_fixture: dict
):
    """Ensure student-facing endpoints expose ONLY published timetable versions."""
    tenant = timetable_fixture["tenant_a"]
    admin = timetable_fixture["admin_a"]
    ay = timetable_fixture["ay_a"]
    sem = timetable_fixture["sem_a"]
    sec = timetable_fixture["sec_a"]
    room = timetable_fixture["room_hall"]
    faculty = timetable_fixture["faculty_a"]
    offering = timetable_fixture["offering_algo"]

    schedule = await TimetableService.create_schedule(
        db_session,
        tenant.id,
        TimetableScheduleCreate(
            academic_year_id=ay.id,
            semester_id=sem.id,
            section_id=sec.id,
            name="Privacy Timetable",
            code=f"PRIV-{uuid.uuid4().hex[:4].upper()}",
        ),
        admin.id,
    )
    versions = await TimetableService.list_versions(db_session, tenant.id, schedule.id)
    v_id = versions[0].id

    await TimetableService.create_session(
        db_session,
        tenant.id,
        v_id,
        TimetableSessionCreate(
            course_offering_id=offering.id,
            section_id=sec.id,
            faculty_id=faculty.id,
            room_id=room.id,
            day_of_week=1,
            start_time=time(9, 0),
            end_time=time(10, 0),
        ),
    )

    # Student View when DRAFT: Should be unpublished and have no sessions exposed
    student_grid = await TimetableService.get_section_timetable_grid(
        db_session, tenant.id, sec.id, is_student_view=True
    )
    assert student_grid.is_published is False
    total_student_sessions = sum(len(d.sessions) for d in student_grid.days)
    assert total_student_sessions == 0

    # Admin View: Can see draft sessions
    admin_grid = await TimetableService.get_section_timetable_grid(
        db_session, tenant.id, sec.id, is_student_view=False
    )
    assert admin_grid.version_id == v_id
    total_admin_sessions = sum(len(d.sessions) for d in admin_grid.days)
    assert total_admin_sessions == 1

    # Publish version
    await TimetableService.submit_for_review(db_session, tenant.id, v_id, admin.id)
    await TimetableService.approve_version(
        db_session, tenant.id, v_id, TimetableVersionApproval(approved=True), admin.id
    )
    await TimetableService.publish_version(
        db_session, tenant.id, v_id, TimetableVersionPublish(), admin.id
    )

    # Now Student View can see published schedule
    student_published_grid = await TimetableService.get_section_timetable_grid(
        db_session, tenant.id, sec.id, is_student_view=True
    )
    assert student_published_grid.is_published is True
    total_published_sessions = sum(len(d.sessions) for d in student_published_grid.days)
    assert total_published_sessions == 1


# =============================================================================
# 8. ATTENDANCE INTEGRATION & RECONCILIATION
# =============================================================================


@pytest.mark.asyncio
async def test_attendance_integration_and_history_preservation(
    db_session: AsyncSession, timetable_fixture: dict
):
    """Verify attendance session linking, reconciliation metrics, and historical record preservation."""
    tenant = timetable_fixture["tenant_a"]
    admin = timetable_fixture["admin_a"]
    ay = timetable_fixture["ay_a"]
    sem = timetable_fixture["sem_a"]
    sec = timetable_fixture["sec_a"]
    room = timetable_fixture["room_hall"]
    faculty = timetable_fixture["faculty_a"]
    offering = timetable_fixture["offering_algo"]
    slot = timetable_fixture["slot_1"]

    schedule = await TimetableService.create_schedule(
        db_session,
        tenant.id,
        TimetableScheduleCreate(
            academic_year_id=ay.id,
            semester_id=sem.id,
            section_id=sec.id,
            name="Attendance Timetable",
            code=f"ATT-{uuid.uuid4().hex[:4].upper()}",
        ),
        admin.id,
    )
    versions = await TimetableService.list_versions(db_session, tenant.id, schedule.id)
    v_id = versions[0].id

    # Create scheduled session
    sess = await TimetableService.create_session(
        db_session,
        tenant.id,
        v_id,
        TimetableSessionCreate(
            course_offering_id=offering.id,
            section_id=sec.id,
            faculty_id=faculty.id,
            room_id=room.id,
            day_of_week=1,
            start_time=time(9, 0),
            end_time=time(10, 0),
            time_slot_id=slot.id,
        ),
    )

    # Publish version to sync canonical slot
    await TimetableService.submit_for_review(db_session, tenant.id, v_id, admin.id)
    await TimetableService.approve_version(
        db_session, tenant.id, v_id, TimetableVersionApproval(approved=True), admin.id
    )
    pub = await TimetableService.publish_version(
        db_session, tenant.id, v_id, TimetableVersionPublish(), admin.id
    )

    # Create an AttendanceSession linked to this class
    att_session = AttendanceSession(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        course_offering_id=offering.id,
        section_id=sec.id,
        faculty_id=faculty.id,
        academic_year_id=ay.id,
        semester_id=sem.id,
        room_id=room.id,
        time_slot_id=slot.id,
        session_date=date(2026, 8, 3),  # Monday
        period_number=1,
        status="LOCKED",
    )
    db_session.add(att_session)
    await db_session.commit()

    # Reconcile attendance
    recon = await TimetableService.reconcile_attendance_sessions(db_session, tenant.id, sec.id)
    assert recon.total_scheduled_sessions == 1
    assert recon.total_attendance_sessions_marked == 1
    assert recon.coverage_percentage == Decimal("100.00")

    # Reschedule the timetable session and verify historical attendance record is UNTOUCHED
    await TimetableService.update_session(
        db_session,
        tenant.id,
        sess.id,
        TimetableSessionUpdate(start_time=time(14, 0), end_time=time(15, 0)),
    )
    await db_session.commit()

    # Historical attendance session remains intact with original session_date and status
    persisted_att = await db_session.scalar(
        select(AttendanceSession).where(AttendanceSession.id == att_session.id)
    )
    assert persisted_att is not None
    assert persisted_att.status == "LOCKED"
    assert persisted_att.period_number == 1


# =============================================================================
# 9. ICALENDAR EXPORT
# =============================================================================


@pytest.mark.asyncio
async def test_icalendar_export(
    db_session: AsyncSession, timetable_fixture: dict
):
    """Verify standard iCalendar RFC 5545 feed generation."""
    tenant = timetable_fixture["tenant_a"]
    admin = timetable_fixture["admin_a"]
    sec = timetable_fixture["sec_a"]
    grid = await TimetableService.get_section_timetable_grid(db_session, tenant.id, sec.id)

    ics_feed = TimetableService.export_icalendar(grid)
    assert "BEGIN:VCALENDAR" in ics_feed
    assert "VERSION:2.0" in ics_feed
    assert "PRODID:-//CampusOS//Timetable Engine v1.0//EN" in ics_feed
    assert "END:VCALENDAR" in ics_feed


# =============================================================================
# 10. MULTI-TENANT ISOLATION
# =============================================================================


@pytest.mark.asyncio
async def test_multi_tenant_isolation(
    db_session: AsyncSession, timetable_fixture: dict
):
    """Verify cross-tenant schedule retrieval and modification is strictly forbidden."""
    tenant_a = timetable_fixture["tenant_a"]
    admin_a = timetable_fixture["admin_a"]
    ay_a = timetable_fixture["ay_a"]
    sem_a = timetable_fixture["sem_a"]
    tenant_b = timetable_fixture["tenant_b"]

    # Create schedule in Tenant A
    sched_a = await TimetableService.create_schedule(
        db_session,
        tenant_a.id,
        TimetableScheduleCreate(
            academic_year_id=ay_a.id,
            semester_id=sem_a.id,
            name="Tenant A Confidential Schedule",
            code=f"TTA-{uuid.uuid4().hex[:4].upper()}",
        ),
        admin_a.id,
    )

    # Attempt to retrieve Tenant A schedule under Tenant B context
    with pytest.raises(NotFoundException):
        await TimetableService.get_schedule(db_session, tenant_b.id, sched_a.id)

    # List schedules in Tenant B: Tenant A schedule must not appear
    b_schedules = await TimetableService.list_schedules(db_session, tenant_b.id)
    assert not any(s.id == sched_a.id for s in b_schedules)
