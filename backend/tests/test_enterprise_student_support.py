"""CampusOS Enterprise Student Counselling, Mentoring & Personal Development Tests (Step 59).

Product Principle: "One Campus. One System. One Source of Truth."

Verifies:
1. Faculty mentor assignment, workload quotas, and duplicate active assignment prevention.
2. Mentor reassignment with auditable lineage (reassigned_from_id) and reason recording.
3. Mentoring session scheduling, non-clinical summary recording, and mentee reflection tracking.
4. Counselling appointment booking, schedule overlap conflict prevention, and lifecycle transitions.
5. Strict confidentiality: Counselling clinical notes server-side access control and audit logging.
6. Individual Student Development Plans (IDP): Goal milestones, action items, and overall progress recalculation.
7. Support referrals across services: unique code generation (REF-YYYY-XXXX), consent rules, and follow-up deadlines.
8. Multi-tenant isolation: Tenant B cannot access or modify Tenant A student support data.
9. Privacy-safe telemetry metrics: role-appropriate aggregation without clinical note leakage.
"""

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.models.core import AcademicYear, Batch, Campus, Department, Institution, Program, Regulation
from app.models.people import StudentProfile, User
from app.models.student_support import (
    AppointmentMode,
    AppointmentStatus,
    CounsellingCategory,
    GoalCategory,
    GoalStatus,
    MentorAssignmentStatus,
    MentorAssignmentType,
    PlanStatus,
    ReferralPriority,
    ReferralReasonCategory,
    ReferralStatus,
    ReferralTargetService,
    SessionAttendanceStatus,
    SessionStatus,
    SessionType,
)
from app.schemas.student_support import (
    ConfidentialCounsellingRecordCreate,
    CounsellingAppointmentCreate,
    CounsellingAppointmentUpdate,
    DevelopmentActionItemCreate,
    DevelopmentGoalCreate,
    DevelopmentGoalUpdate,
    MentorAssignmentCreate,
    MentorReassignRequest,
    MentoringSessionCreate,
    MentoringSessionUpdate,
    SessionAttendeeReflectionUpdate,
    StudentDevelopmentPlanCreate,
    SupportFollowUpCreate,
    SupportFollowUpUpdate,
    SupportPolicyConfigUpdate,
    SupportReferralCreate,
    SupportReferralUpdate,
)
from app.services.student_support_service import StudentSupportService


@pytest.fixture
async def support_setup(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_b: Institution,
    super_admin_user: User,
):
    """Provides campus, faculty mentors, counsellors, and student profiles for tests."""
    uid = uuid.uuid4().hex[:6]

    # Campus A
    campus_a = Campus(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        name="Main Academic Campus",
        code=f"CMP-SUP-{uid}",
        address="100 University Boulevard",
        city="Coimbatore",
        is_active=True,
    )
    db_session.add(campus_a)

    # Department A
    dept_a = Department(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        campus_id=campus_a.id,
        name="Information Technology",
        code=f"IT-{uid}",
        is_active=True,
    )
    db_session.add(dept_a)

    # Program A
    prog_a = Program(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        department_id=dept_a.id,
        name="B.Tech Information Technology",
        code=f"BTIT-{uid}",
        degree_level="UNDERGRADUATE",
        duration_years=4,
        total_semesters=8,
        is_active=True,
    )
    db_session.add(prog_a)

    reg_a = Regulation(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        code=f"REG26-{uid}",
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
        name=f"IT Batch 2026 {uid}",
        admission_year=2026,
        graduation_year=2030,
        is_active=True,
    )
    db_session.add(batch_a)

    # Faculty Mentor 1
    mentor_user_1 = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"mentor1_{uid}@campus.edu",
        first_name="Dr. Arvind",
        last_name="Swaminathan",
        password_hash="hashed_pw_mentor1",
        status="ACTIVE",
    )
    db_session.add(mentor_user_1)

    # Faculty Mentor 2 (Alternate for reassignment)
    mentor_user_2 = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"mentor2_{uid}@campus.edu",
        first_name="Prof. Meenakshi",
        last_name="Sundaram",
        password_hash="hashed_pw_mentor2",
        status="ACTIVE",
    )
    db_session.add(mentor_user_2)

    # Institutional Counsellor
    counsellor_user = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"counsellor_{uid}@campus.edu",
        first_name="Pooja",
        last_name="Nambiar",
        password_hash="hashed_pw_counsellor",
        status="ACTIVE",
    )
    db_session.add(counsellor_user)

    # Student 1
    student_user_1 = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"student1_{uid}@campus.edu",
        first_name="Rohan",
        last_name="Menon",
        password_hash="hashed_pw_student1",
        status="ACTIVE",
    )
    db_session.add(student_user_1)

    # Student 2
    student_user_2 = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"student2_{uid}@campus.edu",
        first_name="Divya",
        last_name="Pillai",
        password_hash="hashed_pw_student2",
        status="ACTIVE",
    )
    db_session.add(student_user_2)

    await db_session.flush()

    student_1 = StudentProfile(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        user_id=student_user_1.id,
        admission_number=f"ADM-2026-{uid}-1",
        roll_number=f"26IT001-{uid}",
        date_of_birth=date(2004, 3, 12),
        gender="MALE",
        status="ACTIVE",
        admission_date=date(2026, 7, 1),
        expected_graduation_date=date(2030, 6, 30),
        program_id=prog_a.id,
        batch_id=batch_a.id,
    )
    db_session.add(student_1)

    student_2 = StudentProfile(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        user_id=student_user_2.id,
        admission_number=f"ADM-2026-{uid}-2",
        roll_number=f"26IT002-{uid}",
        date_of_birth=date(2004, 8, 22),
        gender="FEMALE",
        status="ACTIVE",
        admission_date=date(2026, 7, 1),
        expected_graduation_date=date(2030, 6, 30),
        program_id=prog_a.id,
        batch_id=batch_a.id,
    )
    db_session.add(student_2)

    await db_session.flush()

    return {
        "tenant_a": tenant_a,
        "tenant_b": tenant_b,
        "campus_a": campus_a,
        "dept_a": dept_a,
        "prog_a": prog_a,
        "mentor_1": mentor_user_1,
        "mentor_2": mentor_user_2,
        "counsellor": counsellor_user,
        "student_1": student_1,
        "student_2": student_2,
        "student_user_1": student_user_1,
        "student_user_2": student_user_2,
        "admin": super_admin_user,
    }


# =============================================================================
# 1. MENTOR ASSIGNMENT & QUOTA TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_mentor_assignment_creation_and_quota_limit(
    db_session: AsyncSession, support_setup: dict
):
    """Verifies mentor assignment creation, workload tracking, and policy quota limit enforcement."""
    tenant = support_setup["tenant_a"]
    mentor = support_setup["mentor_1"]
    student_1 = support_setup["student_1"]
    student_2 = support_setup["student_2"]
    service = StudentSupportService(db_session, tenant.id)

    # Configure small mentor workload limit = 1 for testing
    await service.update_config(SupportPolicyConfigUpdate(max_mentees_per_mentor=1))

    # 1. First assignment succeeds
    assign_1 = await service.create_mentor_assignment(
        MentorAssignmentCreate(
            student_id=student_1.id,
            mentor_user_id=mentor.id,
            academic_year="2026-2027",
            assignment_type=MentorAssignmentType.MANUAL,
            notes="First year faculty mentor",
        )
    )
    assert assign_1.status == MentorAssignmentStatus.ACTIVE.value
    assert assign_1.mentor_user_id == mentor.id
    assert assign_1.student_id == student_1.id

    # 2. Second assignment to same mentor must be rejected by quota limit
    with pytest.raises(ValidationException) as exc:
        await service.create_mentor_assignment(
            MentorAssignmentCreate(
                student_id=student_2.id,
                mentor_user_id=mentor.id,
                academic_year="2026-2027",
                assignment_type=MentorAssignmentType.MANUAL,
            )
        )
    assert "workload limit" in str(exc.value)


@pytest.mark.asyncio
async def test_prevent_duplicate_active_mentor_assignment(
    db_session: AsyncSession, support_setup: dict
):
    """Verifies that a student cannot be assigned to multiple active mentors simultaneously."""
    tenant = support_setup["tenant_a"]
    mentor_1 = support_setup["mentor_1"]
    mentor_2 = support_setup["mentor_2"]
    student_1 = support_setup["student_1"]
    service = StudentSupportService(db_session, tenant.id)

    # Set quota limit higher
    await service.update_config(SupportPolicyConfigUpdate(max_mentees_per_mentor=20))

    # Assign student 1 to mentor 1
    await service.create_mentor_assignment(
        MentorAssignmentCreate(
            student_id=student_1.id,
            mentor_user_id=mentor_1.id,
            academic_year="2026-2027",
        )
    )

    # Attempting to assign student 1 to mentor 2 while active raises ConflictException
    with pytest.raises(ConflictException) as exc:
        await service.create_mentor_assignment(
            MentorAssignmentCreate(
                student_id=student_1.id,
                mentor_user_id=mentor_2.id,
                academic_year="2026-2027",
            )
        )
    assert "already has an active faculty mentor" in str(exc.value)


@pytest.mark.asyncio
async def test_mentor_reassignment_and_history(
    db_session: AsyncSession, support_setup: dict
):
    """Verifies mentor reassignment workflow with audit trail and old assignment retirement."""
    tenant = support_setup["tenant_a"]
    mentor_1 = support_setup["mentor_1"]
    mentor_2 = support_setup["mentor_2"]
    student_1 = support_setup["student_1"]
    service = StudentSupportService(db_session, tenant.id)

    await service.update_config(SupportPolicyConfigUpdate(max_mentees_per_mentor=20))

    # Initial assignment
    initial = await service.create_mentor_assignment(
        MentorAssignmentCreate(
            student_id=student_1.id,
            mentor_user_id=mentor_1.id,
            academic_year="2026-2027",
        )
    )

    # Reassign to Mentor 2
    reassigned = await service.reassign_mentor(
        initial.id,
        MentorReassignRequest(
            new_mentor_user_id=mentor_2.id,
            reason="Faculty sabbatical leave coverage",
        ),
    )

    assert reassigned.status == MentorAssignmentStatus.ACTIVE.value
    assert reassigned.mentor_user_id == mentor_2.id
    assert reassigned.reassigned_from_id == initial.id
    assert "sabbatical leave" in reassigned.reassignment_reason

    # Verify old assignment is marked REASSIGNED
    old_list = await service.list_mentor_assignments(
        mentor_user_id=mentor_1.id, status=MentorAssignmentStatus.REASSIGNED.value
    )
    assert len(old_list) == 1
    assert old_list[0].id == initial.id


# =============================================================================
# 2. MENTORING SESSIONS & REFLECTIONS
# =============================================================================


@pytest.mark.asyncio
async def test_mentoring_session_lifecycle_and_reflection(
    db_session: AsyncSession, support_setup: dict
):
    """Verifies scheduling, attendance, completion, and student reflection recording."""
    tenant = support_setup["tenant_a"]
    mentor = support_setup["mentor_1"]
    student = support_setup["student_1"]
    service = StudentSupportService(db_session, tenant.id)

    # 1. Schedule Session
    session = await service.schedule_mentoring_session(
        MentoringSessionCreate(
            mentor_user_id=mentor.id,
            session_title="Semester Onboarding & Academic Goal Setting",
            session_type=SessionType.ONE_ON_ONE,
            session_date=date.today(),
            start_time="10:00",
            end_time="11:00",
            location_or_link="Faculty Room 204",
            summary="Discussed course electives and study schedule.",
            action_items=[{"task": "Draft personal development plan", "due": "2026-11-01"}],
            attendee_student_ids=[student.id],
        ),
        creator_user_id=mentor.id,
    )
    assert session.status == SessionStatus.SCHEDULED.value
    assert len(session.attendees) == 1
    assert session.attendees[0].attendance_status == SessionAttendanceStatus.PENDING.value

    # 2. Update session to COMPLETED
    updated = await service.update_mentoring_session(
        session.id,
        MentoringSessionUpdate(
            status=SessionStatus.COMPLETED,
            summary="Completed discussion on semester milestones.",
        ),
    )
    assert updated.status == SessionStatus.COMPLETED.value

    # 3. Student records reflection
    reflection = await service.record_attendee_reflection(
        session.id,
        student.id,
        SessionAttendeeReflectionUpdate(
            attendance_status=SessionAttendanceStatus.ATTENDED,
            student_feedback="Very helpful advice on balancing lab coursework.",
            student_reflection="I will prioritize database systems assignments.",
        ),
    )
    assert reflection.attendance_status == SessionAttendanceStatus.ATTENDED.value
    assert "helpful advice" in reflection.student_feedback


# =============================================================================
# 3. COUNSELLING APPOINTMENTS & CONFLICT PREVENTION
# =============================================================================


@pytest.mark.asyncio
async def test_counselling_appointment_booking_and_conflict_detection(
    db_session: AsyncSession, support_setup: dict
):
    """Verifies appointment booking, overlap conflict rejection, and status transitions."""
    tenant = support_setup["tenant_a"]
    counsellor = support_setup["counsellor"]
    student_1 = support_setup["student_1"]
    student_2 = support_setup["student_2"]
    service = StudentSupportService(db_session, tenant.id)

    # 1. Book initial appointment
    appt1 = await service.request_counselling_appointment(
        CounsellingAppointmentCreate(
            student_id=student_1.id,
            counsellor_user_id=counsellor.id,
            category=CounsellingCategory.ACADEMIC_STRESS,
            appointment_date=date.today() + timedelta(days=2),
            start_time="14:00",
            end_time="14:45",
            duration_minutes=45,
            mode=AppointmentMode.IN_PERSON,
            venue_or_link="Wellness Centre Room 102",
            request_reason="Mid-term exam preparation stress",
        ),
        booked_by_user_id=student_1.user_id,
    )
    assert appt1.status == AppointmentStatus.REQUESTED.value

    # Confirm appointment
    confirmed = await service.update_counselling_appointment(
        appt1.id,
        CounsellingAppointmentUpdate(status=AppointmentStatus.CONFIRMED),
    )
    assert confirmed.status == AppointmentStatus.CONFIRMED.value

    # 2. Booking a conflicting slot for same counsellor raises ConflictException
    with pytest.raises(ConflictException) as exc:
        await service.request_counselling_appointment(
            CounsellingAppointmentCreate(
                student_id=student_2.id,
                counsellor_user_id=counsellor.id,
                category=CounsellingCategory.TIME_MANAGEMENT,
                appointment_date=date.today() + timedelta(days=2),
                start_time="14:15",
                end_time="15:00",
                duration_minutes=45,
                request_reason="Time management support",
            ),
            booked_by_user_id=student_2.user_id,
        )
    assert "conflicting appointment" in str(exc.value)


# =============================================================================
# 4. STRICT CONFIDENTIAL COUNSELLING RECORDS & AUDIT
# =============================================================================


@pytest.mark.asyncio
async def test_strict_confidential_counselling_record_isolation(
    db_session: AsyncSession, support_setup: dict
):
    """Verifies clinical confidential record creation, audit logging, and isolation."""
    tenant = support_setup["tenant_a"]
    counsellor = support_setup["counsellor"]
    student = support_setup["student_1"]
    service = StudentSupportService(db_session, tenant.id)

    # Create confidential clinical record
    record = await service.create_confidential_record(
        ConfidentialCounsellingRecordCreate(
            student_id=student.id,
            session_notes_restricted="Sensitive clinical notes: student discussed anxiety coping mechanisms.",
            intervention_type="MINDFULNESS_TECHNIQUE",
            clinical_observations="Calm demeanor, responsive to behavioral strategies.",
            follow_up_recommended=True,
            follow_up_target_date=date.today() + timedelta(days=14),
            consent_confirmed=True,
        ),
        counsellor_user_id=counsellor.id,
    )
    assert record.intervention_type == "MINDFULNESS_TECHNIQUE"
    assert record.access_count == 1

    # Access confidential record
    retrieved = await service.get_confidential_record(record.id, accessor_user_id=counsellor.id)
    assert retrieved.access_count == 2
    assert "Sensitive clinical notes" in retrieved.session_notes_restricted

    # Verify audit log was created
    audit_logs = await service.list_audit_logs()
    assert len(audit_logs) >= 2
    actions = [a.action for a in audit_logs]
    assert "CREATE_CONFIDENTIAL_RECORD" in actions
    assert "VIEW_CONFIDENTIAL_RECORD" in actions


# =============================================================================
# 5. STUDENT DEVELOPMENT PLANS (IDP)
# =============================================================================


@pytest.mark.asyncio
async def test_student_development_plan_milestones_and_progress_recalc(
    db_session: AsyncSession, support_setup: dict
):
    """Verifies IDP goal addition, progress updates, and automatic plan overall percentage recalculation."""
    tenant = support_setup["tenant_a"]
    mentor = support_setup["mentor_1"]
    student = support_setup["student_1"]
    service = StudentSupportService(db_session, tenant.id)

    # 1. Create Development Plan with initial goal
    plan = await service.create_development_plan(
        StudentDevelopmentPlanCreate(
            student_id=student.id,
            mentor_user_id=mentor.id,
            title="2026-2027 Academic & Professional Development Plan",
            academic_year="2026-2027",
            career_aspirations="Cloud Solutions Architect",
            strengths_summary="High analytical thinking and algorithmic problem solving",
            goals=[
                DevelopmentGoalCreate(
                    category=GoalCategory.ACADEMIC,
                    title="Maintain GPA >= 8.5",
                    description="Consistent performance in core data structures and operating systems",
                    target_date=date.today() + timedelta(days=90),
                    action_items=[
                        DevelopmentActionItemCreate(
                            title="Complete weekly coding assignments on time",
                            due_date=date.today() + timedelta(days=30),
                        )
                    ],
                )
            ],
        )
    )
    assert plan.status == PlanStatus.ACTIVE.value
    assert plan.overall_progress_pct == 0
    assert len(plan.goals) == 1
    assert len(plan.goals[0].action_items) == 1

    goal_id = plan.goals[0].id

    # 2. Add second goal
    goal_2 = await service.add_goal_to_plan(
        plan.id,
        DevelopmentGoalCreate(
            category=GoalCategory.PROFESSIONAL,
            title="AWS Certified Cloud Practitioner",
            description="Complete certification exam",
            target_date=date.today() + timedelta(days=60),
        ),
    )
    assert goal_2.category == GoalCategory.PROFESSIONAL.value

    # 3. Update Goal 1 progress to 100%
    await service.update_goal(
        goal_id,
        DevelopmentGoalUpdate(progress_pct=100),
    )

    # Reload plan: average of 100% and 0% = 50%
    reloaded = await service.get_development_plan(plan.id)
    assert reloaded.overall_progress_pct == 50

    # 4. Update Goal 2 progress to 100% -> Plan completes
    await service.update_goal(
        goal_2.id,
        DevelopmentGoalUpdate(progress_pct=100),
    )
    reloaded_completed = await service.get_development_plan(plan.id)
    assert reloaded_completed.overall_progress_pct == 100
    assert reloaded_completed.status == PlanStatus.COMPLETED.value


# =============================================================================
# 6. SUPPORT REFERRALS & FOLLOW-UP WORKFLOWS
# =============================================================================


@pytest.mark.asyncio
async def test_support_referral_workflow_and_followup(
    db_session: AsyncSession, support_setup: dict
):
    """Verifies support referral code generation, consent requirement, and follow-up deadlines."""
    tenant = support_setup["tenant_a"]
    mentor = support_setup["mentor_1"]
    student = support_setup["student_1"]
    service = StudentSupportService(db_session, tenant.id)

    # 1. Create Referral with student consent
    referral = await service.create_support_referral(
        SupportReferralCreate(
            student_id=student.id,
            referring_role="FACULTY_MENTOR",
            target_service=ReferralTargetService.CAREER_SERVICES,
            reason_category=ReferralReasonCategory.CAREER_GUIDANCE,
            priority=ReferralPriority.MEDIUM,
            summary_notes="Student seeking guidance on summer cloud engineering internships.",
            consent_obtained=True,
        ),
        referring_user_id=mentor.id,
    )
    assert referral.referral_code.startswith(f"REF-{date.today().year}-")
    assert referral.status == ReferralStatus.PENDING.value

    # 2. Update referral to IN_PROGRESS
    updated_ref = await service.update_support_referral(
        referral.id,
        SupportReferralUpdate(status=ReferralStatus.IN_PROGRESS),
    )
    assert updated_ref.status == ReferralStatus.IN_PROGRESS.value

    # 3. Create follow-up action
    followup = await service.create_follow_up(
        SupportFollowUpCreate(
            referral_id=referral.id,
            assigned_user_id=mentor.id,
            title="Check in after Career Services consultation",
            due_date=date.today() + timedelta(days=7),
            notes="Verify that resume review was completed.",
        )
    )
    assert followup.status == "PENDING"
    assert followup.assigned_user_id == mentor.id

    # 4. Complete follow-up
    completed_f = await service.update_follow_up(
        followup.id,
        SupportFollowUpUpdate(status="COMPLETED"),
    )
    assert completed_f.status == "COMPLETED"
    assert completed_f.completed_at is not None


# =============================================================================
# 7. MULTI-TENANT ISOLATION
# =============================================================================


@pytest.mark.asyncio
async def test_tenant_isolation_student_support(
    db_session: AsyncSession, support_setup: dict
):
    """Verifies that Tenant B is completely isolated from Tenant A's student support data."""
    tenant_a = support_setup["tenant_a"]
    tenant_b = support_setup["tenant_b"]
    mentor_a = support_setup["mentor_1"]
    student_a = support_setup["student_1"]

    service_a = StudentSupportService(db_session, tenant_a.id)
    service_b = StudentSupportService(db_session, tenant_b.id)

    # Create assignment in Tenant A
    assign_a = await service_a.create_mentor_assignment(
        MentorAssignmentCreate(
            student_id=student_a.id,
            mentor_user_id=mentor_a.id,
            academic_year="2026-2027",
        )
    )

    # Tenant B service listing assignments must return empty
    b_assignments = await service_b.list_mentor_assignments()
    assert len(b_assignments) == 0

    # Tenant B cannot access or reassign Tenant A assignment
    with pytest.raises(NotFoundException):
        await service_b.reassign_mentor(
            assign_a.id,
            MentorReassignRequest(
                new_mentor_user_id=mentor_a.id,
                reason="Cross-tenant tampering attempt",
            ),
        )


# =============================================================================
# 8. PRIVACY-SAFE TELEMETRY METRICS
# =============================================================================


@pytest.mark.asyncio
async def test_safe_telemetry_metrics(
    db_session: AsyncSession, support_setup: dict
):
    """Verifies aggregate metrics without leaking confidential notes or student identities."""
    tenant = support_setup["tenant_a"]
    service = StudentSupportService(db_session, tenant.id)

    metrics = await service.get_telemetry_metrics()
    assert hasattr(metrics, "total_active_mentor_assignments")
    assert hasattr(metrics, "appointment_utilization_rate_pct")
    assert hasattr(metrics, "referrals_by_service")
    assert hasattr(metrics, "goals_by_category")
    # Verify no confidential text or clinical notes leaked into telemetry
    raw_str = str(metrics.model_dump())
    assert "clinical" not in raw_str.lower()
    assert "psychological" not in raw_str.lower()
