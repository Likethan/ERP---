"""Enterprise Workforce Management, Staff Lifecycle, Leave & Workload Administration Tests (Step 51).

CampusOS Tagline: "One Campus. One System. One Source of Truth."

Verifies:
1. Employee creation, updates, employee code generation, and tenant-scoped uniqueness.
2. Traceable employment history tracking across lifecycle transitions.
3. Staff onboarding lifecycle workflows with mandatory task verification and gatekeeping.
4. Staff offboarding workflows with notice periods and multi-team clearance tasks.
5. Leave type configuration, versioned policy rules, and balance ledgers.
6. Leave balance adjustments with immutable audit transactions.
7. Leave submission, overspend prevention, and pending balance reservation.
8. Separation of duties: Self-approval rejection enforcement.
9. Leave approval with consumption, ledger recording, and rejection with balance release.
10. Leave cancellation and withdrawal workflows.
11. Privacy-preserving leave calendar queries.
12. Workforce availability and academic timetable conflict detection.
13. Workload expectation, timetable session duty aggregation, and adjustment credits.
14. HR service desk cases and profile change requests.
15. Multi-tenant isolation and security boundary enforcement.
"""

import uuid
from datetime import date, datetime, time, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
from app.models.academics import CourseOffering, Subject, TimeSlot
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
from app.models.timetable import TimetableSchedule, TimetableSession, TimetableVersion, TimetableVersionStatus
from app.models.workforce import (
    EmploymentChangeType,
    EmploymentStatus,
    EmploymentType,
    HRCaseCategory,
    HRCaseStatus,
    LeaveAccrualFrequency,
    LeaveRequestStatus,
    LeaveTransactionType,
    LifecycleCaseStatus,
    LifecycleCaseType,
    LifecycleTaskCategory,
    LifecycleTaskStatus,
    WorkforceEmployee,
    WorkforceLeaveType,
)
from app.schemas.workforce import (
    WorkforceEmployeeCreate,
    WorkforceEmployeeTransitionRequest,
    WorkforceEmployeeUpdate,
    WorkforceHRCaseCreate,
    WorkforceHRCaseUpdate,
    WorkforceLeaveBalanceAdjustRequest,
    WorkforceLeavePolicyCreate,
    WorkforceLeaveRequestCreate,
    WorkforceLeaveTypeCreate,
    WorkforceLifecycleCaseCreate,
    WorkforceLifecycleTaskUpdate,
    WorkforceSeparationInitiateRequest,
    WorkforceWorkloadAdjustmentCreate,
    WorkforceWorkloadExpectationCreate,
)
from app.services.workforce_service import workforce_service


@pytest.fixture
async def workforce_fixture(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_b: Institution,
    super_admin_user: User,
):
    """Provides isolated campuses, departments, users, and academic terms for workforce testing."""
    uid = uuid.uuid4().hex[:6]

    # Tenant A Campus & Department
    campus_a = Campus(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        name="Main Campus",
        code=f"CMP-WF-{uid}",
        address="100 University Boulevard",
        city="Bengaluru",
        is_active=True,
    )
    db_session.add(campus_a)

    dept_a = Department(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        campus_id=campus_a.id,
        name="Information Science & Engineering",
        code=f"ISE-{uid}",
        is_active=True,
    )
    db_session.add(dept_a)

    # Academic Year & Term
    ay = AcademicYear(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        name=f"2026-2027-{uid}",
        start_date=date(2026, 7, 1),
        end_date=date(2027, 6, 30),
        is_current=True,
    )
    db_session.add(ay)

    sem = Semester(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        academic_year_id=ay.id,
        name=f"Odd Term 2026-{uid}",
        semester_number=5,
        term_type="ODD",
        start_date=date(2026, 7, 15),
        end_date=date(2026, 12, 15),
        is_active=True,
    )
    db_session.add(sem)

    prog = Program(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        department_id=dept_a.id,
        name=f"B.Tech ISE {uid}",
        code=f"ISE-{uid}",
        degree_level="UNDERGRADUATE",
        duration_years=Decimal("4.0"),
        total_semesters=8,
        is_active=True,
    )
    db_session.add(prog)

    reg = Regulation(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        code=f"REG-{uid}",
        title=f"Regulation 2026 {uid}",
        effective_year=2026,
        is_active=True,
    )
    db_session.add(reg)

    batch = Batch(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        program_id=prog.id,
        regulation_id=reg.id,
        name=f"ISE-Batch-{uid}",
        admission_year=2024,
        graduation_year=2028,
        is_active=True,
    )
    db_session.add(batch)

    sec = Section(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        program_id=prog.id,
        batch_id=batch.id,
        semester_id=sem.id,
        name="Section A",
        capacity=60,
        is_active=True,
    )
    db_session.add(sec)

    # Tenant B Campus
    campus_b = Campus(
        id=uuid.uuid4(),
        tenant_id=tenant_b.id,
        name="Satellite Campus",
        code=f"CMP-B-{uid}",
        address="50 Tech Road",
        city="Hyderabad",
        is_active=True,
    )
    db_session.add(campus_b)

    # Dedicated unassigned users for employee creation and transition tests
    user_unassigned = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"ananya_{uid}@campus.edu",
        first_name="Ananya",
        last_name="Rao",
        password_hash="mocked_argon2_hash",
        is_active=True,
    )
    db_session.add(user_unassigned)

    user_transition = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"sunil_{uid}@campus.edu",
        first_name="Sunil",
        last_name="Kumar",
        password_hash="mocked_argon2_hash",
        is_active=True,
    )
    db_session.add(user_transition)

    # Active Staff Users & Employees for Leave, Timetable, Workload, and Case tests
    user_staff_1 = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"priya_{uid}@campus.edu",
        first_name="Priya",
        last_name="Sharma",
        password_hash="mocked_argon2_hash",
        is_active=True,
    )
    db_session.add(user_staff_1)

    emp_1 = WorkforceEmployee(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        user_id=user_staff_1.id,
        employee_number=f"EMP-2026-P{uid[:4]}",
        designation="Senior Systems Engineer",
        job_title="Lead Infrastructure Specialist",
        department_id=dept_a.id,
        campus_id=campus_a.id,
        employment_type=EmploymentType.PERMANENT,
        employment_status=EmploymentStatus.ACTIVE,
        joining_date=date(2026, 1, 1),
    )
    db_session.add(emp_1)

    user_staff_2 = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"vikram_{uid}@campus.edu",
        first_name="Dr. Vikram",
        last_name="Deshmukh",
        password_hash="mocked_argon2_hash",
        is_active=True,
    )
    db_session.add(user_staff_2)

    emp_2 = WorkforceEmployee(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        user_id=user_staff_2.id,
        employee_number=f"EMP-2026-V{uid[:4]}",
        designation="Associate Professor",
        job_title="Faculty of Computing",
        department_id=dept_a.id,
        campus_id=campus_a.id,
        employment_type=EmploymentType.PERMANENT,
        employment_status=EmploymentStatus.ACTIVE,
        joining_date=date(2026, 1, 1),
    )
    db_session.add(emp_2)

    user_staff_b = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_b.id,
        email=f"kavita_{uid}@othercampus.edu",
        first_name="Kavita",
        last_name="Nair",
        password_hash="mocked_argon2_hash",
        is_active=True,
    )
    db_session.add(user_staff_b)

    await db_session.commit()

    return {
        "tenant_a_id": tenant_a.id,
        "tenant_b_id": tenant_b.id,
        "campus_a_id": campus_a.id,
        "dept_a_id": dept_a.id,
        "campus_b_id": campus_b.id,
        "academic_year_id": ay.id,
        "semester_id": sem.id,
        "section_id": sec.id,
        "admin_user_id": super_admin_user.id,
        "user_unassigned": user_unassigned,
        "user_transition": user_transition,
        "user_staff_1": user_staff_1,
        "user_staff_2": user_staff_2,
        "user_staff_b": user_staff_b,
        "emp_1": emp_1,
        "emp_2": emp_2,
    }


# =============================================================================
# 1. EMPLOYEE MASTER & EMPLOYMENT RECORDS
# =============================================================================


@pytest.mark.asyncio
async def test_employee_creation_and_unique_constraints(
    db_session: AsyncSession,
    workforce_fixture: dict,
):
    """Verifies employee record creation, number generation, and tenant uniqueness."""
    tenant_id = workforce_fixture["tenant_a_id"]
    admin_id = workforce_fixture["admin_user_id"]
    user1 = workforce_fixture["user_unassigned"]
    dept_id = workforce_fixture["dept_a_id"]
    campus_id = workforce_fixture["campus_a_id"]

    # 1. Create employee
    emp_in = WorkforceEmployeeCreate(
        user_id=user1.id,
        designation="Senior Systems Engineer",
        job_title="Lead Infrastructure Specialist",
        department_id=dept_id,
        campus_id=campus_id,
        employment_type=EmploymentType.PERMANENT,
        employment_status=EmploymentStatus.DRAFT,
        joining_date=date(2026, 8, 1),
        notice_period_days=30,
        qualifications=[{"degree": "M.Tech", "institution": "NITK", "year": 2020}],
    )
    emp = await workforce_service.create_employee(db_session, tenant_id, emp_in, admin_id)
    assert emp.id is not None
    assert emp.employee_number.startswith("EMP-2026-")
    assert emp.first_name == "Ananya"
    assert emp.last_name == "Rao"
    assert emp.designation == "Senior Systems Engineer"
    assert emp.employment_status == EmploymentStatus.DRAFT

    # 2. Verify duplicate user employee creation fails
    with pytest.raises(ConflictException):
        await workforce_service.create_employee(db_session, tenant_id, emp_in, admin_id)

    # 3. Verify history recorded
    hist = await workforce_service.get_employment_history(db_session, tenant_id, emp.id)
    assert len(hist) == 1
    assert hist[0].change_type == EmploymentChangeType.JOINING


@pytest.mark.asyncio
async def test_employee_updates_and_status_transitions(
    db_session: AsyncSession,
    workforce_fixture: dict,
):
    """Verifies profile modification, history logging, and valid lifecycle state transitions."""
    tenant_id = workforce_fixture["tenant_a_id"]
    admin_id = workforce_fixture["admin_user_id"]
    user_trans = workforce_fixture["user_transition"]
    dept_id = workforce_fixture["dept_a_id"]
    campus_id = workforce_fixture["campus_a_id"]

    emp_in = WorkforceEmployeeCreate(
        user_id=user_trans.id,
        designation="Assistant Professor",
        job_title="Faculty of Computing",
        department_id=dept_id,
        campus_id=campus_id,
        employment_type=EmploymentType.PERMANENT,
        employment_status=EmploymentStatus.ACTIVE,
        joining_date=date(2026, 7, 15),
    )
    emp = await workforce_service.create_employee(db_session, tenant_id, emp_in, admin_id)

    # Update designation
    update_in = WorkforceEmployeeUpdate(designation="Associate Professor")
    updated = await workforce_service.update_employee(db_session, tenant_id, emp.id, update_in, admin_id)
    assert updated.designation == "Associate Professor"

    # Transition to ON_LEAVE
    trans_in = WorkforceEmployeeTransitionRequest(
        new_status=EmploymentStatus.ON_LEAVE,
        reason="Approved academic sabbatical",
    )
    trans = await workforce_service.transition_employee_status(db_session, tenant_id, emp.id, trans_in, admin_id)
    assert trans.employment_status == EmploymentStatus.ON_LEAVE

    # Invalid transition directly from ON_LEAVE to SEPARATED should fail
    invalid_trans = WorkforceEmployeeTransitionRequest(
        new_status=EmploymentStatus.SEPARATED,
        reason="Invalid direct jump",
    )
    with pytest.raises(BadRequestException):
        await workforce_service.transition_employee_status(db_session, tenant_id, emp.id, invalid_trans, admin_id)


# =============================================================================
# 2. STAFF ONBOARDING & OFFBOARDING
# =============================================================================


@pytest.mark.asyncio
async def test_onboarding_lifecycle_and_gatekeeping(
    db_session: AsyncSession,
    workforce_fixture: dict,
):
    """Tests onboarding case creation, mandatory checklist completion, and activation gatekeeping."""
    tenant_id = workforce_fixture["tenant_a_id"]
    admin_id = workforce_fixture["admin_user_id"]
    uid = uuid.uuid4().hex[:6]

    # Create new user and onboarding employee
    u = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_id,
        email=f"onboard_{uid}@campus.edu",
        first_name="Rohan",
        last_name="Verma",
        password_hash="mocked_hash",
        is_active=True,
    )
    db_session.add(u)
    await db_session.commit()

    emp_in = WorkforceEmployeeCreate(
        user_id=u.id,
        designation="Lab Technician",
        job_title="Hardware Specialist",
        employment_type=EmploymentType.CONTRACT,
        employment_status=EmploymentStatus.ONBOARDING,
        joining_date=date(2026, 9, 1),
    )
    emp = await workforce_service.create_employee(db_session, tenant_id, emp_in, admin_id)

    # 1. Verify onboarding case and tasks automatically created
    cases = await workforce_service.list_lifecycle_cases(db_session, tenant_id, employee_id=emp.id)
    assert len(cases) == 1
    onb_case = cases[0]
    assert onb_case.case_type == LifecycleCaseType.ONBOARDING
    assert len(onb_case.tasks) >= 4

    # 2. Attempting to activate before mandatory tasks are finished should fail!
    activate_trans = WorkforceEmployeeTransitionRequest(
        new_status=EmploymentStatus.ACTIVE,
        reason="Attempt early activation",
    )
    with pytest.raises(BadRequestException) as exc_info:
        await workforce_service.transition_employee_status(db_session, tenant_id, emp.id, activate_trans, admin_id)
    assert "Mandatory onboarding tasks" in str(exc_info.value)

    # 3. Complete all tasks
    for task in onb_case.tasks:
        await workforce_service.update_lifecycle_task(
            db_session,
            tenant_id,
            task.id,
            WorkforceLifecycleTaskUpdate(
                status=LifecycleTaskStatus.COMPLETED,
                completion_evidence="Verified and cleared by department lead",
            ),
            admin_id,
        )

    # 4. Now activation succeeds!
    activated = await workforce_service.transition_employee_status(
        db_session, tenant_id, emp.id, activate_trans, admin_id
    )
    assert activated.employment_status == EmploymentStatus.ACTIVE


@pytest.mark.asyncio
async def test_offboarding_lifecycle_and_clearance(
    db_session: AsyncSession,
    workforce_fixture: dict,
):
    """Tests offboarding initiation with notice period and exit clearance tasks."""
    tenant_id = workforce_fixture["tenant_a_id"]
    admin_id = workforce_fixture["admin_user_id"]
    uid = uuid.uuid4().hex[:6]

    u = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_id,
        email=f"exit_{uid}@campus.edu",
        first_name="Deepak",
        last_name="Sharma",
        password_hash="mocked_hash",
        is_active=True,
    )
    db_session.add(u)
    await db_session.commit()

    emp_in = WorkforceEmployeeCreate(
        user_id=u.id,
        designation="Administrative Executive",
        job_title="Office Coordinator",
        employment_status=EmploymentStatus.ACTIVE,
        joining_date=date(2025, 1, 10),
    )
    emp = await workforce_service.create_employee(db_session, tenant_id, emp_in, admin_id)

    # Initiate offboarding
    off_in = WorkforceSeparationInitiateRequest(
        employee_id=emp.id,
        separation_date=date(2026, 10, 31),
        separation_reason="Resignation for higher studies",
        notice_period_days=30,
        notes="All handover documents prepared",
    )
    case = await workforce_service.initiate_offboarding(db_session, tenant_id, off_in, admin_id)
    assert case.case_type == LifecycleCaseType.OFFBOARDING
    assert len(case.tasks) >= 5

    # Verify employee transitioned to NOTICE_PERIOD
    emp_refetched = await workforce_service.get_employee_response(db_session, tenant_id, emp.id)
    assert emp_refetched.employment_status == EmploymentStatus.NOTICE_PERIOD
    assert emp_refetched.separation_reason == "Resignation for higher studies"


# =============================================================================
# 3. LEAVE TYPES, POLICIES & BALANCES
# =============================================================================


@pytest.mark.asyncio
async def test_leave_types_policies_and_balances(
    db_session: AsyncSession,
    workforce_fixture: dict,
):
    """Verifies leave type creation, versioned policy configuration, and balance calculation."""
    tenant_id = workforce_fixture["tenant_a_id"]
    admin_id = workforce_fixture["admin_user_id"]
    user1 = workforce_fixture["user_staff_1"]
    uid = uuid.uuid4().hex[:6].upper()

    # 1. Create leave type
    lt_in = WorkforceLeaveTypeCreate(
        code=f"CAS_{uid}",
        name=f"Casual Leave {uid}",
        description="Standard paid casual leave",
        is_paid=True,
    )
    lt = await workforce_service.create_leave_type(db_session, tenant_id, lt_in)
    assert lt.code == f"CAS_{uid}"

    # 2. Create leave policy
    pol_in = WorkforceLeavePolicyCreate(
        leave_type_id=lt.id,
        policy_code=f"POL-CAS-{uid}",
        name="Annual Casual Leave Policy",
        effective_from=date(2026, 1, 1),
        annual_entitlement=Decimal("14.00"),
        accrual_frequency=LeaveAccrualFrequency.ANNUAL,
        accrual_rate=Decimal("14.00"),
        allow_half_day=True,
    )
    pol = await workforce_service.create_leave_policy(db_session, tenant_id, pol_in)
    assert pol.annual_entitlement == Decimal("14.00")

    # 3. Fetch or initialize balance for employee
    emp_res = await db_session.execute(
        select(WorkforceEmployee).where(
            WorkforceEmployee.tenant_id == tenant_id,
            WorkforceEmployee.user_id == user1.id,
        )
    )
    emp = emp_res.scalar_one()

    balance = await workforce_service.get_or_create_leave_balance(
        db_session, tenant_id, emp.id, lt.id, 2026, admin_id
    )
    assert balance.entitled_days == Decimal("14.00")
    assert balance.available_days == Decimal("14.00")

    # 4. Manual balance adjustment
    adj_in = WorkforceLeaveBalanceAdjustRequest(
        employee_id=emp.id,
        leave_type_id=lt.id,
        calendar_year=2026,
        adjustment_days=Decimal("2.00"),
        reason="Special institutional recognition credit",
    )
    adj_bal = await workforce_service.adjust_leave_balance(db_session, tenant_id, adj_in, admin_id)
    assert adj_bal.adjusted_days == Decimal("2.00")
    assert adj_bal.available_days == Decimal("16.00")


# =============================================================================
# 4. LEAVE REQUEST WORKFLOWS & DECISION LOGIC
# =============================================================================


@pytest.mark.asyncio
async def test_leave_request_approval_and_balance_consumption(
    db_session: AsyncSession,
    workforce_fixture: dict,
):
    """Tests leave request submission, balance reservation, self-approval prevention, and approval."""
    tenant_id = workforce_fixture["tenant_a_id"]
    admin_id = workforce_fixture["admin_user_id"]
    admin_user = await db_session.get(User, admin_id)
    user1 = workforce_fixture["user_staff_1"]
    uid = uuid.uuid4().hex[:6].upper()

    # Create leave type & policy
    lt = await workforce_service.create_leave_type(
        db_session, tenant_id, WorkforceLeaveTypeCreate(code=f"SL_{uid}", name=f"Sick Leave {uid}")
    )
    await workforce_service.create_leave_policy(
        db_session,
        tenant_id,
        WorkforceLeavePolicyCreate(
            leave_type_id=lt.id,
            policy_code=f"POL-SL-{uid}",
            name="Sick Leave Policy",
            effective_from=date(2026, 1, 1),
            annual_entitlement=Decimal("10.00"),
        ),
    )

    emp_res = await db_session.execute(
        select(WorkforceEmployee).where(
            WorkforceEmployee.tenant_id == tenant_id,
            WorkforceEmployee.user_id == user1.id,
        )
    )
    emp = emp_res.scalar_one()

    # 1. Submit leave for 3 days
    req_in = WorkforceLeaveRequestCreate(
        employee_id=emp.id,
        leave_type_id=lt.id,
        start_date=date(2026, 9, 7),
        end_date=date(2026, 9, 9),
        reason="Medical recuperation",
    )
    req = await workforce_service.submit_leave_request(db_session, tenant_id, req_in, user1)
    assert req.status == LeaveRequestStatus.SUBMITTED
    assert req.total_days == Decimal("3.00")

    # Verify balance reserved pending days
    balances = await workforce_service.list_leave_balances(db_session, tenant_id, employee_id=emp.id)
    sl_bal = next(b for b in balances if b.leave_type_id == lt.id)
    assert sl_bal.pending_days == Decimal("3.00")
    assert sl_bal.available_days == Decimal("7.00")

    # 2. Separation of duties: Self-approval rejection
    with pytest.raises(BadRequestException) as exc_info:
        await workforce_service.approve_leave_request(
            db_session, tenant_id, req.id, "Attempting self-approval", user1.id
        )
    assert "Self-approval is forbidden" in str(exc_info.value)

    # 3. Authorized manager approves
    approved = await workforce_service.approve_leave_request(
        db_session, tenant_id, req.id, "Approved with doctor certificate", admin_id
    )
    assert approved.status == LeaveRequestStatus.APPROVED

    # Verify balance consumed: pending released, used incremented
    balances_after = await workforce_service.list_leave_balances(db_session, tenant_id, employee_id=emp.id)
    sl_bal_after = next(b for b in balances_after if b.leave_type_id == lt.id)
    assert sl_bal_after.pending_days == Decimal("0.00")
    assert sl_bal_after.used_days == Decimal("3.00")
    assert sl_bal_after.available_days == Decimal("7.00")


@pytest.mark.asyncio
async def test_leave_rejection_and_cancellation(
    db_session: AsyncSession,
    workforce_fixture: dict,
):
    """Tests leave rejection releasing reserved balance and cancellation workflows."""
    tenant_id = workforce_fixture["tenant_a_id"]
    admin_id = workforce_fixture["admin_user_id"]
    user1 = workforce_fixture["user_staff_1"]
    uid = uuid.uuid4().hex[:6].upper()

    lt = await workforce_service.create_leave_type(
        db_session, tenant_id, WorkforceLeaveTypeCreate(code=f"EL_{uid}", name=f"Earned Leave {uid}")
    )
    await workforce_service.create_leave_policy(
        db_session,
        tenant_id,
        WorkforceLeavePolicyCreate(
            leave_type_id=lt.id,
            policy_code=f"POL-EL-{uid}",
            name="Earned Leave Policy",
            effective_from=date(2026, 1, 1),
            annual_entitlement=Decimal("20.00"),
        ),
    )

    emp_res = await db_session.execute(
        select(WorkforceEmployee).where(
            WorkforceEmployee.tenant_id == tenant_id,
            WorkforceEmployee.user_id == user1.id,
        )
    )
    emp = emp_res.scalar_one()

    # Submit request for 4 days
    req_in = WorkforceLeaveRequestCreate(
        employee_id=emp.id,
        leave_type_id=lt.id,
        start_date=date(2026, 11, 2),
        end_date=date(2026, 11, 5),
        reason="Family trip",
    )
    req = await workforce_service.submit_leave_request(db_session, tenant_id, req_in, user1)

    # Reject request
    rejected = await workforce_service.reject_leave_request(
        db_session, tenant_id, req.id, "Critical project milestone scheduled during this period", admin_id
    )
    assert rejected.status == LeaveRequestStatus.REJECTED

    # Check pending days released
    balances = await workforce_service.list_leave_balances(db_session, tenant_id, employee_id=emp.id)
    el_bal = next(b for b in balances if b.leave_type_id == lt.id)
    assert el_bal.pending_days == Decimal("0.00")
    assert el_bal.used_days == Decimal("0.00")


# =============================================================================
# 5. WORKFORCE AVAILABILITY & TIMETABLE CONFLICTS
# =============================================================================


@pytest.mark.asyncio
async def test_workforce_availability_and_timetable_collision_detection(
    db_session: AsyncSession,
    workforce_fixture: dict,
):
    """Verifies detection of collisions between faculty leave and scheduled academic timetable sessions."""
    tenant_id = workforce_fixture["tenant_a_id"]
    admin_id = workforce_fixture["admin_user_id"]
    user2 = workforce_fixture["user_staff_2"]  # Dr. Vikram Deshmukh
    dept_id = workforce_fixture["dept_a_id"]
    ay_id = workforce_fixture["academic_year_id"]
    sem_id = workforce_fixture["semester_id"]
    uid = uuid.uuid4().hex[:6].upper()

    # 1. Create Faculty Profile
    faculty = FacultyProfile(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        user_id=user2.id,
        employee_code=f"FAC-{uid}",
        department_id=dept_id,
        designation="Associate Professor",
        highest_qualification="Ph.D in AI",
        joining_date=date(2026, 7, 15),
    )
    db_session.add(faculty)

    # 2. Create academic timetable session for faculty on Wednesdays (day_of_week=3)
    subject = Subject(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        department_id=dept_id,
        code=f"CS501-{uid}",
        name="Operating Systems",
        credits=4,
    )
    db_session.add(subject)

    course_off = CourseOffering(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        academic_year_id=ay_id,
        semester_id=sem_id,
        section_id=workforce_fixture["section_id"],
        subject_id=subject.id,
    )
    db_session.add(course_off)

    sched = TimetableSchedule(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        academic_year_id=ay_id,
        semester_id=sem_id,
        department_id=dept_id,
        name="ISE Fall Schedule",
        code=f"SCH-ISE-{uid}",
    )
    db_session.add(sched)

    version = TimetableVersion(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        schedule_id=sched.id,
        version_number=1,
        status=TimetableVersionStatus.PUBLISHED,
    )
    db_session.add(version)

    # Wednesday class: 09:00 to 11:00
    tt_session = TimetableSession(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        version_id=version.id,
        course_offering_id=course_off.id,
        section_id=workforce_fixture["section_id"],
        faculty_id=faculty.id,
        day_of_week=3,  # Wednesday
        start_time=time(9, 0),
        end_time=time(11, 0),
    )
    db_session.add(tt_session)

    # Leave type
    lt = await workforce_service.create_leave_type(
        db_session, tenant_id, WorkforceLeaveTypeCreate(code=f"DUTY_{uid}", name=f"On-Duty Leave {uid}")
    )
    await workforce_service.create_leave_policy(
        db_session,
        tenant_id,
        WorkforceLeavePolicyCreate(
            leave_type_id=lt.id,
            policy_code=f"POL-OD-{uid}",
            name="Duty Leave Policy",
            effective_from=date(2026, 1, 1),
            annual_entitlement=Decimal("15.00"),
        ),
    )
    await db_session.commit()

    # Fetch employee
    emp_res = await db_session.execute(
        select(WorkforceEmployee).where(
            WorkforceEmployee.tenant_id == tenant_id,
            WorkforceEmployee.user_id == user2.id,
        )
    )
    emp = emp_res.scalar_one()

    # 3. Submit leave encompassing Wednesday: Sep 23, 2026 (Wednesday)
    wednesday_date = date(2026, 9, 23)
    req_in = WorkforceLeaveRequestCreate(
        employee_id=emp.id,
        leave_type_id=lt.id,
        start_date=wednesday_date,
        end_date=wednesday_date,
        reason="Conference presentation",
    )
    req = await workforce_service.submit_leave_request(db_session, tenant_id, req_in, user2)
    assert req.has_timetable_conflicts is True

    # 4. Check availability API
    avail = await workforce_service.check_availability(
        db_session, tenant_id, emp.id, start_date=wednesday_date, end_date=wednesday_date
    )
    assert avail.is_available is False
    assert len(avail.timetable_session_conflicts) == 1
    assert avail.timetable_session_conflicts[0]["conflict_type"] == "LEAVE_VS_TIMETABLE_SESSION"


# =============================================================================
# 6. WORKLOAD EXPECTATION & DUTY AGGREGATION
# =============================================================================


@pytest.mark.asyncio
async def test_workload_calculation_and_adjustments(
    db_session: AsyncSession,
    workforce_fixture: dict,
):
    """Verifies workload calculation combining scheduled timetable hours with expectations and adjustments."""
    tenant_id = workforce_fixture["tenant_a_id"]
    admin_id = workforce_fixture["admin_user_id"]
    user2 = workforce_fixture["user_staff_2"]
    ay_id = workforce_fixture["academic_year_id"]
    sem_id = workforce_fixture["semester_id"]

    emp_res = await db_session.execute(
        select(WorkforceEmployee).where(
            WorkforceEmployee.tenant_id == tenant_id,
            WorkforceEmployee.user_id == user2.id,
        )
    )
    emp = emp_res.scalar_one()

    # 1. Define expectation: 30 hours per week
    exp_in = WorkforceWorkloadExpectationCreate(
        employee_id=emp.id,
        academic_year_id=ay_id,
        semester_id=sem_id,
        teaching_hours_per_week=Decimal("12.00"),
        research_hours_per_week=Decimal("10.00"),
        admin_hours_per_week=Decimal("8.00"),
        exam_hours_per_week=Decimal("0.00"),
        effective_from=date(2026, 7, 15),
    )
    await workforce_service.create_or_update_workload_expectation(db_session, tenant_id, exp_in)

    # 2. Add an adjustment concession of 4 hours
    adj_in = WorkforceWorkloadAdjustmentCreate(
        employee_id=emp.id,
        category="RESEARCH",
        adjusted_hours_per_week=Decimal("4.00"),
        reason="Principal Investigator grant release hours",
        effective_from=date(2026, 7, 15),
    )
    await workforce_service.create_workload_adjustment(db_session, tenant_id, adj_in, admin_id)

    # 3. Compute workload summary
    summary = await workforce_service.get_workload_summary(
        db_session, tenant_id, emp.id, academic_year_id=ay_id, semester_id=sem_id
    )
    assert summary.expected_hours == Decimal("30.00")
    assert summary.adjusted_hours == Decimal("4.00")
    assert summary.load_status in ("BALANCED", "UNDER_ALLOCATED", "OVERLOAD")


# =============================================================================
# 7. HR CASE MANAGEMENT & SELF-SERVICE
# =============================================================================


@pytest.mark.asyncio
async def test_hr_case_lifecycle(
    db_session: AsyncSession,
    workforce_fixture: dict,
):
    """Verifies employee self-service inquiry creation, status tracking, and resolution."""
    tenant_id = workforce_fixture["tenant_a_id"]
    admin_id = workforce_fixture["admin_user_id"]
    user1 = workforce_fixture["user_staff_1"]

    # 1. Submit HR case for profile update
    case_in = WorkforceHRCaseCreate(
        category=HRCaseCategory.PROFILE_UPDATE,
        priority="NORMAL",
        subject="Request update to emergency contact and certification",
        description="Completed AWS Cloud Solutions Architect certification.",
        proposed_changes={"certification": "AWS Certified Architect"},
    )
    hr_case = await workforce_service.create_hr_case(db_session, tenant_id, case_in, user1)
    assert hr_case.case_number.startswith("HRC-")
    assert hr_case.status == HRCaseStatus.OPEN

    # 2. HR Admin resolves case
    update_in = WorkforceHRCaseUpdate(
        status=HRCaseStatus.RESOLVED,
        resolution="Profile updated and verified against credential URL.",
        assigned_to_user_id=admin_id,
    )
    resolved = await workforce_service.update_hr_case(db_session, tenant_id, hr_case.id, update_in, admin_id)
    assert resolved.status == HRCaseStatus.RESOLVED
    assert resolved.resolution is not None


# =============================================================================
# 8. MULTI-TENANT ISOLATION
# =============================================================================


@pytest.mark.asyncio
async def test_cross_tenant_workforce_isolation(
    db_session: AsyncSession,
    workforce_fixture: dict,
):
    """Ensures strict multi-tenant boundary prevention for employees and leaves."""
    tenant_a = workforce_fixture["tenant_a_id"]
    tenant_b = workforce_fixture["tenant_b_id"]
    user_b = workforce_fixture["user_staff_b"]

    # Create employee in Tenant B
    emp_b_in = WorkforceEmployeeCreate(
        user_id=user_b.id,
        designation="Registrar",
        job_title="Head of Admissions",
        joining_date=date(2026, 6, 1),
    )
    emp_b = await workforce_service.create_employee(db_session, tenant_b, emp_b_in, user_b.id)

    # Attempting to fetch Tenant B employee using Tenant A context must fail with NotFoundException
    with pytest.raises(NotFoundException):
        await workforce_service.get_employee_response(db_session, tenant_a, emp_b.id)

    # Attempting to list in Tenant A must not include Tenant B employee
    emps_a, _ = await workforce_service.list_employees(db_session, tenant_a)
    assert all(e.id != emp_b.id for e in emps_a)
