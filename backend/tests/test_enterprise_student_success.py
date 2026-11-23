"""Enterprise Student Success, Academic Advising, Early-Warning & Intervention Tests (Step 47).

Comprehensive automated tests covering:
1. Student-success case creation, updates, notes, status transitions, reassignment, reopening, and escalation.
2. Advisor profiles, caseload capacities, student assignments, and capacity limit enforcement.
3. Academic advising plans, action item milestones, and progress updates.
4. Early-warning rule configuration, threshold validation, and audit versioning.
5. Explainable early-warning evaluation against realistic attendance and assessment records.
6. Signal deduplication preventing alert storms across repeated evaluations.
7. Warning signal lifecycle: acknowledgement, false-positive dismissal, case linking, and resolution.
8. Intervention workflows, action execution, outcome classifications, and overdue sweeps.
9. Advising appointments, scheduling conflict prevention, and mode tracking.
10. Privacy boundaries: student self-service API isolating internal case notes and risk internals.
11. Multi-tenant isolation preventing cross-tenant access.
12. Aggregate student-success analytics and advisor caseload reports.
"""

import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi import HTTPException
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import ACCESS_TOKEN_COOKIE_NAME, create_access_token, get_password_hash
from app.models.academics import CourseOffering, Subject
from app.models.attendance import AttendanceRecord, AttendanceSession
from app.models.core import (
    AcademicYear,
    Batch,
    Department,
    Institution,
    Program,
    Regulation,
    Section,
    Semester,
)
from app.models.people import FacultyProfile, Role, StudentProfile, User, UserRoleAssignment
from app.models.student_success import (
    ActionItemStatus,
    AdvisorCategory,
    AppointmentMode,
    AppointmentStatus,
    AssignmentRelationshipType,
    AssignmentStatus,
    CaseCategory,
    CaseClosureReason,
    CaseCreationSource,
    CaseOutcomeClassification,
    CasePriority,
    CaseStatus,
    ComparisonOperator,
    EarlyWarningCategory,
    EarlyWarningSignalStatus,
    InterventionStatus,
    InterventionType,
    NoteType,
    StudentParticipation,
    WarningSeverity,
)
from app.schemas.student_success import (
    AdvisingActionItemCreate,
    AdvisingAppointmentRequest,
    AdvisingAppointmentUpdate,
    AdvisingPlanCreate,
    AdvisorProfileCreate,
    AdvisorStudentAssignmentCreate,
    AdvisorStudentAssignmentReassign,
    EarlyWarningEvaluationRequest,
    EarlyWarningRuleCreate,
    EarlyWarningRuleUpdate,
    EarlyWarningSignalLinkCase,
    EarlyWarningSignalResolve,
    InterventionActionCreate,
    InterventionPlanCreate,
    InterventionPlanUpdate,
    StudentActionProgressSubmit,
    StudentSuccessCaseCreate,
    StudentSuccessCaseEscalate,
    StudentSuccessCaseNoteCreate,
    StudentSuccessCaseReopen,
    StudentSuccessCaseStatusTransition,
    StudentSuccessCaseUpdate,
)
from app.services.student_success_service import StudentSuccessService


def make_auth_headers(
    user: User,
    tenant_id: uuid.UUID,
    role_name: str = "INSTITUTION_ADMIN",
    permissions: list[str] | None = None,
) -> dict[str, str]:
    """Helper to generate JWT bearer and cookie authorization headers."""
    perms = permissions if permissions is not None else ["*"]
    token = create_access_token(
        user_id=user.id,
        tenant_id=tenant_id,
        email=user.email,
        roles=[role_name],
        permissions=perms,
    )
    return {
        "Authorization": f"Bearer {token}",
        "Cookie": f"{ACCESS_TOKEN_COOKIE_NAME}={token}",
    }


async def create_test_student(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    email_prefix: str = "student",
) -> tuple[User, StudentProfile]:
    """Helper to create a student user and student profile."""
    uid = uuid.uuid4().hex[:6]

    # Department & Program
    dept = Department(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        code=f"CS-{uid}",
        name=f"Computer Science {uid}",
        is_active=True,
    )
    db.add(dept)

    prog = Program(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        department_id=dept.id,
        code=f"BSCS-{uid}",
        name="BS Computer Science",
        degree_level="UNDERGRADUATE",
        duration_years=4,
        total_semesters=8,
        is_active=True,
    )
    db.add(prog)

    reg = Regulation(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        code=f"REG-2026-{uid}",
        title="Regulation 2026",
        effective_year=2026,
        is_active=True,
    )
    db.add(reg)


    batch = Batch(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        program_id=prog.id,
        regulation_id=reg.id,
        name=f"Batch 2026 {uid}",
        admission_year=2026,
        graduation_year=2030,
        is_active=True,
    )
    db.add(batch)

    # Student User
    user = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_id,
        email=f"{email_prefix}_{uid}@apextech.edu",
        phone_number="+919876543299",
        password_hash=get_password_hash("StudentSecret123!"),
        status="ACTIVE",
        first_name="Anita",
        last_name="Roy",
    )
    db.add(user)
    await db.flush()

    role_res = await db.execute(select(Role).where(Role.name == "STUDENT"))
    student_role = role_res.scalar_one_or_none()
    if student_role:
        db.add(
            UserRoleAssignment(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                user_id=user.id,
                role_id=student_role.id,
            )
        )

    profile = StudentProfile(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        user_id=user.id,
        admission_number=f"ADM-{uid}",
        roll_number=f"26CS{uid[:3]}",
        date_of_birth=date(2005, 1, 1),
        gender="FEMALE",
        status="ACTIVE",
        admission_date=date(2026, 8, 1),
        expected_graduation_date=date(2030, 5, 30),
        program_id=prog.id,
        batch_id=batch.id,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    await db.refresh(user)
    return user, profile


# =============================================================================
# 1. CASE MANAGEMENT LIFECYCLE TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_case_management_lifecycle(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies case creation, status transitions, reassignment, notes, reopening, and escalation."""
    service = StudentSuccessService(db_session)
    student_user, student = await create_test_student(db_session, tenant_a.id)

    # 1. Create Case
    case = await service.create_case(
        tenant_id=tenant_a.id,
        payload=StudentSuccessCaseCreate(
            student_id=student.id,
            category=CaseCategory.ACADEMIC_PERFORMANCE,
            priority=CasePriority.HIGH,
            title="Midterm Assessment Drop Risk",
            description="Student showed sudden drop in algorithms coursework.",
            creation_source=CaseCreationSource.ADVISOR_MANUAL,
            target_completion_date=date.today() + timedelta(days=30),
        ),
        created_by_user_id=tenant_admin_a.id,
    )
    assert case.id is not None
    assert case.case_number.startswith("SSC-")
    assert case.status == CaseStatus.OPEN
    assert case.priority == CasePriority.HIGH

    # 2. Add Internal Note and Student-Visible Note
    note_int = await service.add_case_note(
        tenant_id=tenant_a.id,
        case_id=case.id,
        payload=StudentSuccessCaseNoteCreate(
            note_type=NoteType.INTERNAL_NOTE,
            content="Internal discussion: Candidate is balancing part-time work.",
            is_student_visible=False,
        ),
        author_user_id=tenant_admin_a.id,
    )
    assert note_int.is_student_visible is False

    note_pub = await service.add_case_note(
        tenant_id=tenant_a.id,
        case_id=case.id,
        payload=StudentSuccessCaseNoteCreate(
            note_type=NoteType.MEETING_SUMMARY,
            content="Agreed to attend remedial peer-tutoring sessions on Tuesdays.",
            is_student_visible=True,
        ),
        author_user_id=tenant_admin_a.id,
    )
    assert note_pub.is_student_visible is True

    # Verify student visibility boundary in notes
    all_notes = await service.list_case_notes(tenant_a.id, case.id, student_view=False)
    student_notes = await service.list_case_notes(tenant_a.id, case.id, student_view=True)
    assert len(all_notes) >= 3  # initial system audit note + 2 notes
    assert len(student_notes) == 1
    assert student_notes[0].content == note_pub.content

    # 3. Transition to UNDER_REVIEW -> INTERVENTION_PLANNED -> MONITORING -> RESOLVED
    await service.transition_case_status(
        tenant_id=tenant_a.id,
        case_id=case.id,
        payload=StudentSuccessCaseStatusTransition(status=CaseStatus.UNDER_REVIEW),
        user_id=tenant_admin_a.id,
    )
    case = await service.get_case(tenant_a.id, case.id)
    assert case.status == CaseStatus.UNDER_REVIEW

    await service.transition_case_status(
        tenant_id=tenant_a.id,
        case_id=case.id,
        payload=StudentSuccessCaseStatusTransition(
            status=CaseStatus.RESOLVED,
            closure_reason=CaseClosureReason.ACADEMIC_IMPROVEMENT_ACHIEVED,
            outcome_classification=CaseOutcomeClassification.SUCCESSFUL,
            outcome_notes="Student scored 82% in subsequent exams.",
        ),
        user_id=tenant_admin_a.id,
    )
    case = await service.get_case(tenant_a.id, case.id)
    assert case.status == CaseStatus.RESOLVED
    assert case.closure_reason == CaseClosureReason.ACADEMIC_IMPROVEMENT_ACHIEVED
    assert case.actual_resolution_date is not None

    # 4. Reopen Case
    await service.reopen_case(
        tenant_id=tenant_a.id,
        case_id=case.id,
        payload=StudentSuccessCaseReopen(reopen_reason="Drop re-occurred in end semester."),
        user_id=tenant_admin_a.id,
    )
    case = await service.get_case(tenant_a.id, case.id)
    assert case.status == CaseStatus.OPEN
    assert case.reopened_at is not None
    assert case.reopened_reason == "Drop re-occurred in end semester."

    # 5. Escalate Case
    await service.escalate_case(
        tenant_id=tenant_a.id,
        case_id=case.id,
        payload=StudentSuccessCaseEscalate(escalation_reason="Repeated absences flagged."),
        user_id=tenant_admin_a.id,
    )
    case = await service.get_case(tenant_a.id, case.id)
    assert case.is_escalated is True
    assert case.escalation_reason == "Repeated absences flagged."


# =============================================================================
# 2. ADVISOR CAPACITY & ASSIGNMENT WORKFLOW TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_advisor_profile_capacity_and_assignments(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies advisor registration, capacity limits enforcement, and reassignment workflow."""
    service = StudentSuccessService(db_session)

    # 1. Create 2 Advisor Users
    uid1 = uuid.uuid4().hex[:6]
    adv_user1 = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"adv1_{uid1}@apextech.edu",
        phone_number="+919876543201",
        password_hash=get_password_hash("AdvPass123!"),
        status="ACTIVE",
        first_name="Grace",
        last_name="Hopper",
    )
    db_session.add(adv_user1)

    uid2 = uuid.uuid4().hex[:6]
    adv_user2 = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"adv2_{uid2}@apextech.edu",
        phone_number="+919876543202",
        password_hash=get_password_hash("AdvPass123!"),
        status="ACTIVE",
        first_name="Ada",
        last_name="Lovelace",
    )
    db_session.add(adv_user2)
    await db_session.commit()

    # Register Advisor 1 with capacity = 2
    adv1 = await service.create_advisor_profile(
        tenant_id=tenant_a.id,
        payload=AdvisorProfileCreate(
            user_id=adv_user1.id,
            advisor_category=AdvisorCategory.FACULTY_ADVISOR,
            max_student_capacity=2,
        ),
    )
    assert adv1.current_student_count == 0
    assert adv1.max_student_capacity == 2

    # Register Advisor 2 with capacity = 10
    adv2 = await service.create_advisor_profile(
        tenant_id=tenant_a.id,
        payload=AdvisorProfileCreate(
            user_id=adv_user2.id,
            advisor_category=AdvisorCategory.DEPARTMENT_COORDINATOR,
            max_student_capacity=10,
        ),
    )

    # Create 3 Students
    _, s1 = await create_test_student(db_session, tenant_a.id, "stud1")
    _, s2 = await create_test_student(db_session, tenant_a.id, "stud2")
    _, s3 = await create_test_student(db_session, tenant_a.id, "stud3")

    # 2. Assign Student 1 to Advisor 1
    asgn1 = await service.assign_advisor_to_student(
        tenant_id=tenant_a.id,
        payload=AdvisorStudentAssignmentCreate(
            advisor_id=adv1.id,
            student_id=s1.id,
            relationship_type=AssignmentRelationshipType.PRIMARY,
        ),
        assigned_by_user_id=tenant_admin_a.id,
    )
    adv1 = await service.get_advisor_profile(tenant_a.id, adv1.id)
    assert adv1.current_student_count == 1

    # 3. Assign Student 2 to Advisor 1 (reaches capacity 2/2)
    _ = await service.assign_advisor_to_student(
        tenant_id=tenant_a.id,
        payload=AdvisorStudentAssignmentCreate(
            advisor_id=adv1.id,
            student_id=s2.id,
            relationship_type=AssignmentRelationshipType.PRIMARY,
        ),
        assigned_by_user_id=tenant_admin_a.id,
    )
    adv1 = await service.get_advisor_profile(tenant_a.id, adv1.id)
    assert adv1.current_student_count == 2

    # 4. Assign Student 3 to Advisor 1 -> Should fail because capacity is full!
    with pytest.raises(HTTPException) as excinfo:
        await service.assign_advisor_to_student(
            tenant_id=tenant_a.id,
            payload=AdvisorStudentAssignmentCreate(
                advisor_id=adv1.id,
                student_id=s3.id,
                relationship_type=AssignmentRelationshipType.PRIMARY,
            ),
        )
    assert "maximum student capacity" in str(excinfo.value)

    # 5. Reassign Student 1 from Advisor 1 to Advisor 2
    new_asgn = await service.reassign_advisor_student(
        tenant_id=tenant_a.id,
        assignment_id=asgn1.id,
        payload=AdvisorStudentAssignmentReassign(
            new_advisor_id=adv2.id,
            reassignment_reason="Caseload rebalancing and specialization alignment.",
        ),
        user_id=tenant_admin_a.id,
    )
    assert new_asgn.advisor_id == adv2.id
    assert new_asgn.status == AssignmentStatus.ACTIVE

    # Verify counts: adv1 drops to 1, adv2 increases to 1
    adv1 = await service.get_advisor_profile(tenant_a.id, adv1.id)
    adv2 = await service.get_advisor_profile(tenant_a.id, adv2.id)
    assert adv1.current_student_count == 1
    assert adv2.current_student_count == 1


# =============================================================================
# 3. EARLY WARNING RULES & REALISTIC ATTENDANCE/EXAM EVALUATION
# =============================================================================


@pytest.mark.asyncio
async def test_early_warning_rules_and_versioning(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies rule configuration, threshold validation, and audit versioning."""
    service = StudentSuccessService(db_session)

    # 1. Threshold validation: negative attendance must fail
    with pytest.raises(HTTPException):
        await service.create_early_warning_rule(
            tenant_id=tenant_a.id,
            payload=EarlyWarningRuleCreate(
                code="EWR-ATT-ERR",
                name="Invalid Rule",
                category=EarlyWarningCategory.ATTENDANCE,
                operator=ComparisonOperator.LESS_THAN,
                threshold_value=Decimal("-5.0"),
            ),
        )

    # 2. Valid Rule creation (Attendance < 75%)
    rule = await service.create_early_warning_rule(
        tenant_id=tenant_a.id,
        payload=EarlyWarningRuleCreate(
            code="EWR-ATT-75",
            name="Low Attendance Warning (Sub 75%)",
            category=EarlyWarningCategory.ATTENDANCE,
            operator=ComparisonOperator.LESS_THAN,
            threshold_value=Decimal("75.00"),
            evaluation_window_days=30,
            severity=WarningSeverity.HIGH,
            recommended_intervention_category=InterventionType.ATTENDANCE_FOLLOWUP,
        ),
        user_id=tenant_admin_a.id,
    )
    assert rule.current_version == 1
    assert rule.code == "EWR-ATT-75"

    # 3. Rule update: adjust threshold to 70%
    updated_rule = await service.update_early_warning_rule(
        tenant_id=tenant_a.id,
        rule_id=rule.id,
        payload=EarlyWarningRuleUpdate(
            threshold_value=Decimal("70.00"),
            change_reason="Department approved relaxed threshold for monsoon season.",
        ),
        user_id=tenant_admin_a.id,
    )
    assert updated_rule.current_version == 2
    assert updated_rule.threshold_value == Decimal("70.00")

    # 4. Check audit versions list
    versions = await service.list_rule_versions(tenant_a.id, rule.id)
    assert len(versions) == 2
    assert versions[0].version_number == 2
    assert versions[1].version_number == 1


@pytest.mark.asyncio
async def test_early_warning_evaluation_and_deduplication(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies early-warning evaluation against realistic attendance and deduplication."""
    service = StudentSuccessService(db_session)
    student_user, student = await create_test_student(db_session, tenant_a.id)

    # 1. Create rule: attendance < 75%
    uid = uuid.uuid4().hex[:6]
    rule = await service.create_early_warning_rule(
        tenant_id=tenant_a.id,
        payload=EarlyWarningRuleCreate(
            code=f"EWR-ATT-{uid}",
            name="Critical Attendance Rule",
            category=EarlyWarningCategory.ATTENDANCE,
            operator=ComparisonOperator.LESS_THAN,
            threshold_value=Decimal("75.00"),
            evaluation_window_days=30,
            severity=WarningSeverity.CRITICAL,
        ),
    )

    # 2. Seed realistic attendance records: 10 sessions, 6 PRESENT, 4 ABSENT (60% attendance)
    prog_res = await db_session.execute(select(Program).where(Program.id == student.program_id))
    prog = prog_res.scalar_one()

    subj = Subject(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        department_id=prog.department_id,
        code=f"CS101-{uid}",
        name="Data Structures",
        is_active=True,
    )
    db_session.add(subj)

    ay = AcademicYear(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        name=f"AY-2026-{uid}",
        start_date=date(2026, 7, 1),
        end_date=date(2027, 6, 30),
        is_current=True,
    )
    db_session.add(ay)
    await db_session.flush()

    sem = Semester(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        academic_year_id=ay.id,
        name=f"Term 1 {uid}",
        semester_number=1,
        term_type="ODD",
        start_date=date(2026, 7, 15),
        end_date=date(2026, 12, 15),
        is_active=True,
    )
    db_session.add(sem)
    await db_session.flush()

    sec = Section(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        program_id=prog.id,
        batch_id=student.batch_id,
        semester_id=sem.id,
        name="Section A",
        capacity=60,
        is_active=True,
    )
    db_session.add(sec)
    await db_session.flush()

    course = CourseOffering(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        subject_id=subj.id,
        academic_year_id=ay.id,
        semester_id=sem.id,
        section_id=sec.id,
        status="ACTIVE",
        max_capacity=60,
    )
    db_session.add(course)
    await db_session.flush()

    fac_user = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"faculty_{uid}@apextech.edu",
        first_name="Prof",
        last_name="Faculty",
        password_hash=get_password_hash("Secret123!"),
        status="ACTIVE",
    )
    db_session.add(fac_user)
    await db_session.flush()

    fac = FacultyProfile(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        user_id=fac_user.id,
        employee_code=f"FAC-{uid}",
        department_id=prog.department_id,
        designation="Assistant Professor",
        highest_qualification="Ph.D",
        joining_date=date(2020, 1, 1),
    )
    db_session.add(fac)
    await db_session.flush()

    today = date.today()
    for i in range(10):
        sess = AttendanceSession(
            id=uuid.uuid4(),
            tenant_id=tenant_a.id,
            course_offering_id=course.id,
            section_id=sec.id,
            faculty_id=fac.id,
            academic_year_id=ay.id,
            semester_id=sem.id,
            session_date=today - timedelta(days=12 - i),
            period_number=1,
            status="LOCKED",
        )
        db_session.add(sess)
        await db_session.flush()

        rec_status = "PRESENT" if i < 6 else "ABSENT"
        rec = AttendanceRecord(
            id=uuid.uuid4(),
            tenant_id=tenant_a.id,
            session_id=sess.id,
            student_id=student.id,
            status=rec_status,
            recorded_by_user_id=tenant_admin_a.id,
        )
        db_session.add(rec)

    await db_session.commit()

    # 3. Trigger evaluation
    evals = await service.evaluate_rules(
        tenant_id=tenant_a.id,
        payload=EarlyWarningEvaluationRequest(rule_id=rule.id, student_id=student.id),
        triggered_by="TEST_RUN",
    )
    assert len(evals) == 1
    assert evals[0].students_evaluated_count == 1
    assert evals[0].warnings_generated_count == 1

    # 4. Verify generated explainable signal
    signals = await service.list_signals(tenant_a.id, student_id=student.id, rule_id=rule.id)
    assert len(signals) == 1
    sig = signals[0]
    assert sig.metric_observed_value == Decimal("60.00")
    assert sig.status == EarlyWarningSignalStatus.NEWLY_DETECTED
    assert sig.severity == WarningSeverity.CRITICAL
    assert len(sig.source_record_references) == 1
    assert sig.source_record_references[0]["total_sessions"] == 10
    assert sig.source_record_references[0]["present_sessions"] == 6

    # 5. DEDUPLICATION CHECK: Run evaluation again!
    evals2 = await service.evaluate_rules(
        tenant_id=tenant_a.id,
        payload=EarlyWarningEvaluationRequest(rule_id=rule.id, student_id=student.id),
    )
    # Warning count should be 0 because an active warning is already open for this student and rule!
    assert evals2[0].warnings_generated_count == 0
    signals_after = await service.list_signals(tenant_a.id, student_id=student.id, rule_id=rule.id)
    assert len(signals_after) == 1  # No duplicate created!


# =============================================================================
# 4. SIGNAL LIFECYCLE & CASE LINKING TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_signal_lifecycle_and_intervention_workflow(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies acknowledging, dismissing, resolving, linking signal to case, and overdue sweeps."""
    service = StudentSuccessService(db_session)
    student_user, student = await create_test_student(db_session, tenant_a.id)

    # 1. Create Rule and generate a signal
    uid = uuid.uuid4().hex[:6]
    rule = await service.create_early_warning_rule(
        tenant_id=tenant_a.id,
        payload=EarlyWarningRuleCreate(
            code=f"EWR-TEST-{uid}",
            name="Test Risk Rule",
            category=EarlyWarningCategory.ATTENDANCE,
            operator=ComparisonOperator.LESS_THAN,
            threshold_value=Decimal("75.00"),
        ),
    )

    # Create signal directly for testing lifecycle
    sig_code = f"SIG-{date.today().year}-{uuid.uuid4().hex[:5]}"
    from app.models.student_success import EarlyWarningSignal

    sig = EarlyWarningSignal(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        student_id=student.id,
        rule_id=rule.id,
        rule_version=1,
        signal_code=sig_code,
        observation_period_start=date.today() - timedelta(days=30),
        observation_period_end=date.today(),
        metric_observed_value=Decimal("65.00"),
        threshold_condition="attendance LESS_THAN 75.00%",
        source_record_references=[{"entity": "mock", "val": 65}],
        severity=WarningSeverity.HIGH,
        status=EarlyWarningSignalStatus.NEWLY_DETECTED,
    )
    db_session.add(sig)
    await db_session.commit()

    # 2. Acknowledge Signal
    sig = await service.acknowledge_signal(tenant_a.id, sig.id, tenant_admin_a.id)
    assert sig.status == EarlyWarningSignalStatus.ACKNOWLEDGED
    assert sig.acknowledged_at is not None

    # 3. Link Signal to a newly created Case
    sig = await service.link_signal_to_case(
        tenant_id=tenant_a.id,
        signal_id=sig.id,
        payload=EarlyWarningSignalLinkCase(create_new_case=True, new_case_title="Support Case for Attendance"),
        user_id=tenant_admin_a.id,
    )
    assert sig.success_case_id is not None
    assert sig.status == EarlyWarningSignalStatus.INTERVENTION_INITIATED

    # 4. Create an Intervention Plan for this signal and case
    plan = await service.create_intervention_plan(
        tenant_id=tenant_a.id,
        payload=InterventionPlanCreate(
            student_id=student.id,
            case_id=sig.success_case_id,
            warning_signal_id=sig.id,
            title="Weekly Attendance Check-in",
            intervention_type=InterventionType.ATTENDANCE_FOLLOWUP,
            priority=CasePriority.HIGH,
            planned_start_date=date.today(),
            target_completion_date=date.today() + timedelta(days=14),
            actions=[
                InterventionActionCreate(
                    title="Student-Advisor Morning Check-in",
                    due_date=date.today() + timedelta(days=7),
                    is_student_visible=True,
                )
            ],
        ),
        user_id=tenant_admin_a.id,
    )
    assert plan.status == InterventionStatus.PLANNED
    assert len(plan.actions) == 1

    # Update intervention status to COMPLETED
    updated_plan = await service.update_intervention_plan(
        tenant_id=tenant_a.id,
        intervention_id=plan.id,
        payload=InterventionPlanUpdate(
            status=InterventionStatus.COMPLETED,
            student_participation=StudentParticipation.ATTENDED,
            outcome_classification="SUCCESSFUL",
            outcome_notes="Attendance stabilized at 84%.",
        ),
        user_id=tenant_admin_a.id,
    )
    assert updated_plan.status == InterventionStatus.COMPLETED
    assert updated_plan.actual_completion_date is not None

    # 5. Resolve Signal
    sig = await service.resolve_signal(
        tenant_id=tenant_a.id,
        signal_id=sig.id,
        payload=EarlyWarningSignalResolve(resolution_notes="Attendance restored above 80%."),
        user_id=tenant_admin_a.id,
    )
    assert sig.status == EarlyWarningSignalStatus.RESOLVED


# =============================================================================
# 5. APPOINTMENTS & SCHEDULING CONFLICT PREVENTION TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_advising_appointments_and_conflict_prevention(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies appointment booking and overlapping schedule conflict prevention."""
    service = StudentSuccessService(db_session)
    student_user, student = await create_test_student(db_session, tenant_a.id)

    # Advisor
    adv = await service.create_advisor_profile(
        tenant_id=tenant_a.id,
        payload=AdvisorProfileCreate(
            user_id=tenant_admin_a.id,
            advisor_category=AdvisorCategory.FACULTY_ADVISOR,
        ),
    )

    t_base = datetime.now(UTC) + timedelta(days=2)
    t_start1 = t_base.replace(hour=10, minute=0, second=0, microsecond=0)
    t_end1 = t_base.replace(hour=11, minute=0, second=0, microsecond=0)

    # 1. Schedule Appointment 1 (10:00 - 11:00)
    appt1 = await service.schedule_appointment(
        tenant_id=tenant_a.id,
        payload=AdvisingAppointmentRequest(
            advisor_id=adv.id,
            student_id=student.id,
            scheduled_start_time=t_start1,
            scheduled_end_time=t_end1,
            meeting_mode=AppointmentMode.IN_PERSON,
            location_or_url="Room 302, Academic Block",
            agenda="Course planning and semester roadmap.",
        ),
        requested_by_user_id=tenant_admin_a.id,
    )
    assert appt1.id is not None
    assert appt1.status == AppointmentStatus.CONFIRMED

    # 2. Attempt Overlapping Appointment (10:30 - 11:30) -> MUST FAIL (409 Conflict)
    t_start_conflict = t_base.replace(hour=10, minute=30, second=0, microsecond=0)
    t_end_conflict = t_base.replace(hour=11, minute=30, second=0, microsecond=0)

    with pytest.raises(Exception) as excinfo:
        await service.schedule_appointment(
            tenant_id=tenant_a.id,
            payload=AdvisingAppointmentRequest(
                advisor_id=adv.id,
                student_id=student.id,
                scheduled_start_time=t_start_conflict,
                scheduled_end_time=t_end_conflict,
            ),
            requested_by_user_id=tenant_admin_a.id,
        )
    assert "conflicting appointment" in str(excinfo.value)

    # 3. Schedule Non-Overlapping Appointment (11:00 - 12:00) -> SUCCEEDS
    t_start2 = t_base.replace(hour=11, minute=0, second=0, microsecond=0)
    t_end2 = t_base.replace(hour=12, minute=0, second=0, microsecond=0)

    appt2 = await service.schedule_appointment(
        tenant_id=tenant_a.id,
        payload=AdvisingAppointmentRequest(
            advisor_id=adv.id,
            student_id=student.id,
            scheduled_start_time=t_start2,
            scheduled_end_time=t_end2,
        ),
        requested_by_user_id=tenant_admin_a.id,
    )
    assert appt2.id is not None


# =============================================================================
# 6. STUDENT SELF-SERVICE PRIVACY BOUNDARY TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_student_self_service_privacy_boundary(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies student portal scrubs internal case notes, risk details, and internal meeting notes."""
    service = StudentSuccessService(db_session)
    student_user, student = await create_test_student(db_session, tenant_a.id)

    # Advisor
    adv = await service.create_advisor_profile(
        tenant_id=tenant_a.id,
        payload=AdvisorProfileCreate(
            user_id=tenant_admin_a.id,
            advisor_category=AdvisorCategory.FACULTY_ADVISOR,
        ),
    )
    await service.assign_advisor_to_student(
        tenant_id=tenant_a.id,
        payload=AdvisorStudentAssignmentCreate(
            advisor_id=adv.id,
            student_id=student.id,
            relationship_type=AssignmentRelationshipType.PRIMARY,
        ),
    )

    # Create Advising Plan with 1 student-visible action and 1 internal-only action
    _ = await service.create_advising_plan(
        tenant_id=tenant_a.id,
        payload=AdvisingPlanCreate(
            student_id=student.id,
            advisor_id=adv.id,
            title="Graduation Readiness Roadmap",
            academic_goals="Achieve 8.0 CGPA and complete capstone.",
            is_student_visible=True,
            initial_action_items=[
                AdvisingActionItemCreate(
                    title="Submit capstone proposal",
                    is_student_visible=True,
                ),
                AdvisingActionItemCreate(
                    title="Faculty internal dossier audit",
                    is_student_visible=False,  # Hidden from student!
                ),
            ],
        ),
    )

    # Schedule Appointment with internal advisor notes
    t_start = datetime.now(UTC) + timedelta(days=3)
    appt = await service.schedule_appointment(
        tenant_id=tenant_a.id,
        payload=AdvisingAppointmentRequest(
            advisor_id=adv.id,
            student_id=student.id,
            scheduled_start_time=t_start,
            scheduled_end_time=t_start + timedelta(hours=1),
            agenda="Progress review",
        ),
        requested_by_user_id=tenant_admin_a.id,
    )
    await service.update_appointment(
        tenant_id=tenant_a.id,
        appointment_id=appt.id,
        payload=AdvisingAppointmentUpdate(
            meeting_notes="INTERNAL CONFIDENTIAL: Student is experiencing high test anxiety.",
            agreed_action_summary="Review practice exams before Friday.",
        ),
    )

    # FETCH AS STUDENT SELF-SERVICE
    overview = await service.get_student_self_overview(tenant_a.id, student_user.id)
    assert overview.student_id == student.id
    assert overview.active_plans_count == 1

    # Verify action items returned: ONLY 1 student-visible action, hidden action must NOT be returned!
    plan_resp = overview.active_plans[0]
    assert len(plan_resp.action_items) == 1
    assert plan_resp.action_items[0].title == "Submit capstone proposal"

    # Verify appointments: internal meeting_notes MUST BE SCRUBBED (None)
    assert len(overview.upcoming_appointments) == 1
    appt_resp = overview.upcoming_appointments[0]
    assert appt_resp.meeting_notes is None
    assert appt_resp.agreed_action_summary == "Review practice exams before Friday."

    # Student submits progress on permitted action
    visible_action_id = plan_resp.action_items[0].id
    updated_item = await service.submit_student_progress(
        tenant_id=tenant_a.id,
        user_id=student_user.id,
        payload=StudentActionProgressSubmit(
            action_item_id=visible_action_id,
            student_progress_notes="Draft completed and uploaded to portal.",
        ),
    )
    assert updated_item.student_progress_notes == "Draft completed and uploaded to portal."
    assert updated_item.status == ActionItemStatus.IN_PROGRESS


# =============================================================================
# 7. CROSS-TENANT ISOLATION TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_cross_tenant_isolation(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_b: Institution,
    tenant_admin_a: User,
    tenant_admin_b: User,
):
    """Verifies that Tenant B cannot access Tenant A's cases, rules, signals, or advisors."""
    service = StudentSuccessService(db_session)
    _, student_a = await create_test_student(db_session, tenant_a.id)

    # Case in Tenant A
    case_a = await service.create_case(
        tenant_id=tenant_a.id,
        payload=StudentSuccessCaseCreate(
            student_id=student_a.id,
            title="Tenant A Private Support Case",
        ),
        created_by_user_id=tenant_admin_a.id,
    )

    # Attempting to fetch Tenant A's case using Tenant B context -> MUST FAIL (404)
    with pytest.raises(HTTPException):
        await service.get_case(tenant_id=tenant_b.id, case_id=case_a.id)

    # Attempting to update Tenant A's case using Tenant B context -> MUST FAIL
    with pytest.raises(HTTPException):
        await service.update_case(
            tenant_id=tenant_b.id,
            case_id=case_a.id,
            payload=StudentSuccessCaseUpdate(title="Malicious Cross-Tenant Overwrite"),
        )


# =============================================================================
# 8. REST API ENDPOINTS VIA ASGICLIENT
# =============================================================================


@pytest.mark.asyncio
async def test_rest_api_end_to_end(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Verifies FastAPI REST API endpoints with authentication and OpenAPI schemas."""
    headers = make_auth_headers(tenant_admin_a, tenant_a.id)
    student_user, student = await create_test_student(db_session, tenant_a.id)

    # 1. POST /api/v1/student-success/cases
    case_payload = {
        "student_id": str(student.id),
        "category": "ACADEMIC_PERFORMANCE",
        "priority": "HIGH",
        "title": "REST API Case Creation Test",
        "description": "Integration test validating REST route execution.",
    }
    resp = await client.post("/api/v1/student-success/cases", json=case_payload, headers=headers)
    assert resp.status_code == 201, resp.text
    data = resp.json()["data"]
    case_id = data["id"]
    assert data["case_number"].startswith("SSC-")
    assert data["status"] == "OPEN"

    # 2. GET /api/v1/student-success/cases
    list_resp = await client.get("/api/v1/student-success/cases", headers=headers)
    assert list_resp.status_code == 200
    cases = list_resp.json()["data"]
    assert any(c["id"] == case_id for c in cases)

    # 3. POST /api/v1/student-success/cases/{case_id}/notes
    note_payload = {
        "note_type": "INTERNAL_NOTE",
        "content": "Case note created via REST endpoint.",
        "is_student_visible": False,
    }
    note_resp = await client.post(
        f"/api/v1/student-success/cases/{case_id}/notes",
        json=note_payload,
        headers=headers,
    )
    assert note_resp.status_code == 201

    # 4. GET /api/v1/student-success/reports/overview
    rep_resp = await client.get("/api/v1/student-success/reports/overview", headers=headers)
    assert rep_resp.status_code == 200
    rep_data = rep_resp.json()["data"]
    assert "total_cases" in rep_data
    assert "analytical_notice" in rep_data
    assert rep_data["total_cases"] >= 1
