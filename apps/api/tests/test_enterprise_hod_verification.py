"""Enterprise HOD Portal Milestone P0 Verification Test Suite.

Validates:
1. Department resolution hardening (authoritative assignment, 403 on unassigned or cross-dept).
2. Dedicated student detail endpoint with strict department-boundary isolation (403 on other dept).
3. Database persistence & dashboard aggregation (real aggregates, zero counts for empty dept, no 720/28 fallbacks).
4. Role authorization invariants (401 unauthenticated, 403 non-HOD, admin/VP supervision).
"""

import uuid
from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import ACCESS_TOKEN_COOKIE_NAME, create_access_token, get_password_hash
from app.models.academics import CourseOffering, Subject
from app.models.attendance import AttendanceAlert, AttendanceRecord, AttendanceSession
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


async def create_test_user(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    email: str,
    role_name: str,
    first_name: str = "Test",
    last_name: str = "User",
) -> tuple[User, dict[str, str]]:
    """Helper to create a user with a specific role and generate their auth cookie."""
    user = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_id,
        email=email,
        phone_number="+919876543210",
        password_hash=get_password_hash("SuperSecret123!"),
        status="ACTIVE",
        first_name=first_name,
        last_name=last_name,
    )
    db.add(user)
    await db.flush()

    role_res = await db.execute(select(Role).where(Role.name == role_name))
    role = role_res.scalar_one_or_none()
    if not role:
        role = Role(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            name=role_name,
            code=role_name,
            is_system=True,
        )
        db.add(role)
        await db.flush()

    assignment = UserRoleAssignment(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        user_id=user.id,
        role_id=role.id,
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(
        user_id=user.id,
        tenant_id=tenant_id,
        email=user.email,
        roles=[role_name],
        permissions=["*"] if role_name in ["SUPER_ADMIN", "ADMIN"] else [],
    )
    cookie = {ACCESS_TOKEN_COOKIE_NAME: token}
    return user, cookie


# =============================================================================
# TASK 1: DEPARTMENT RESOLUTION HARDENING & CROSS-DEPARTMENT ISOLATION
# =============================================================================


@pytest.mark.asyncio
async def test_hod_department_isolation_and_cross_department_blocking(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
    super_admin_user: User,
) -> None:
    """Verify that HOD department resolution is authoritative and rejects unassigned or cross-dept access."""
    uid = uuid.uuid4().hex[:6]
    headers = {"X-Tenant-ID": str(tenant_a.id)}

    # 1. Create Department 1 (CSE) and Department 2 (ECE)
    dept1 = Department(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        code=f"CSE-{uid}",
        name="Computer Science & Engineering",
        department_type="ACADEMIC",
        is_active=True,
    )
    dept2 = Department(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        code=f"ECE-{uid}",
        name="Electronics & Communication Engineering",
        department_type="ACADEMIC",
        is_active=True,
    )
    db_session.add_all([dept1, dept2])
    await db_session.flush()

    # 2. Create HOD 1 assigned to Dept 1
    hod1, cookie_hod1 = await create_test_user(
        db_session, tenant_a.id, f"hod_cse_{uid}@campusos.internal", "HOD", "Anand", "KS"
    )
    dept1.hod_user_id = hod1.id

    # 3. Create HOD 2 assigned to Dept 2
    hod2, cookie_hod2 = await create_test_user(
        db_session, tenant_a.id, f"hod_ece_{uid}@campusos.internal", "HOD", "Priya", "Nair"
    )
    dept2.hod_user_id = hod2.id

    # 4. Create HOD 3 with HOD role but NO assigned department
    _hod3, cookie_hod3 = await create_test_user(
        db_session, tenant_a.id, f"hod_unassigned_{uid}@campusos.internal", "HOD", "Unassigned", "HOD"
    )
    await db_session.commit()

    # TEST A: HOD 1 accesses their own department dashboard -> 200 OK
    res1 = await client.get("/api/v1/hod/dashboard", headers=headers, cookies=cookie_hod1)
    assert res1.status_code == 200
    data1 = res1.json()["data"]
    assert data1["department"]["id"] == str(dept1.id)
    assert data1["department"]["code"] == dept1.code

    # TEST B: HOD 1 attempts to access Dept 2 via department_id query param -> 403 Forbidden!
    res_tamper = await client.get(
        f"/api/v1/hod/dashboard?department_id={dept2.id}",
        headers=headers,
        cookies=cookie_hod1,
    )
    assert res_tamper.status_code == 403
    assert "cannot access another department" in res_tamper.json()["detail"].lower()

    # TEST C: HOD 3 (unassigned) calls dashboard -> 403 Forbidden (no unsafe fallback to first dept)!
    res_unassigned = await client.get("/api/v1/hod/dashboard", headers=headers, cookies=cookie_hod3)
    assert res_unassigned.status_code == 403
    assert "not assigned as head of department" in res_unassigned.json()["detail"].lower()

    # TEST D: Super Admin accesses Dept 2 dashboard via supervisory param -> 200 OK
    admin_token = create_access_token(
        user_id=super_admin_user.id,
        tenant_id=tenant_a.id,
        email=super_admin_user.email,
        roles=["SUPER_ADMIN"],
        permissions=["*"],
    )
    cookie_admin = {ACCESS_TOKEN_COOKIE_NAME: admin_token}
    res_admin = await client.get(
        f"/api/v1/hod/dashboard?department_id={dept2.id}",
        headers=headers,
        cookies=cookie_admin,
    )
    assert res_admin.status_code == 200
    assert res_admin.json()["data"]["department"]["id"] == str(dept2.id)


# =============================================================================
# TASK 2: DEDICATED STUDENT DETAIL ENDPOINT & CROSS-DEPARTMENT BOUNDARY
# =============================================================================


@pytest.mark.asyncio
async def test_hod_student_detail_security_and_department_boundary(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
) -> None:
    """Verify GET /api/v1/hod/students/{student_id} enforces strict department isolation."""
    uid = uuid.uuid4().hex[:6]
    headers = {"X-Tenant-ID": str(tenant_a.id)}

    # 1. Setup two departments
    dept_cse = Department(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        code=f"CS-{uid}",
        name="Computer Science",
        department_type="ACADEMIC",
        is_active=True,
    )
    dept_mech = Department(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        code=f"ME-{uid}",
        name="Mechanical Engineering",
        department_type="ACADEMIC",
        is_active=True,
    )
    db_session.add_all([dept_cse, dept_mech])
    await db_session.flush()

    # 2. HOD for CSE
    hod_cse, cookie_cse = await create_test_user(
        db_session, tenant_a.id, f"hod_cs_{uid}@campusos.internal", "HOD", "Ravi", "Varma"
    )
    dept_cse.hod_user_id = hod_cse.id

    # 3. Programs
    prog_cse = Program(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        department_id=dept_cse.id,
        code=f"BTECH-CS-{uid}",
        name="B.Tech Computer Science",
        degree_level="UG",
        duration_years=4,
    )
    prog_mech = Program(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        department_id=dept_mech.id,
        code=f"BTECH-ME-{uid}",
        name="B.Tech Mechanical",
        degree_level="UG",
        duration_years=4,
    )
    db_session.add_all([prog_cse, prog_mech])
    await db_session.flush()

    # 4. Regulation, Batch, AcademicYear, Semester, Section
    reg = Regulation(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        code=f"R-{uid}",
        title=f"Regulation {uid}",
        effective_year=2026,
    )
    db_session.add(reg)
    await db_session.flush()

    batch = Batch(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        program_id=prog_cse.id,
        regulation_id=reg.id,
        name=f"Batch 2026-2030 {uid}",
        admission_year=2026,
        graduation_year=2030,
    )
    ay = AcademicYear(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        name=f"2026-2027 {uid}",
        start_date=date(2026, 7, 1),
        end_date=date(2027, 6, 30),
    )
    sem = Semester(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        academic_year_id=ay.id,
        semester_number=5,
        term_type="ODD",
        name="Semester 5",
        start_date=date(2026, 7, 1),
        end_date=date(2026, 12, 1),
    )
    db_session.add_all([batch, ay, sem])
    await db_session.flush()

    sec = Section(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        program_id=prog_cse.id,
        batch_id=batch.id,
        semester_id=sem.id,
        name="A",
        capacity=60,
    )
    db_session.add(sec)
    await db_session.flush()

    # 5. Student in CSE (Student A)
    u_stu_a, _ = await create_test_user(
        db_session, tenant_a.id, f"student_a_{uid}@campusos.internal", "STUDENT", "Aarav", "Kumar"
    )
    student_a = StudentProfile(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        user_id=u_stu_a.id,
        admission_number=f"ADM-A-{uid}",
        registration_number=f"REG-A-{uid}",
        roll_number=f"24CS001-{uid}",
        date_of_birth=date(2004, 5, 12),
        gender="MALE",
        status="ACTIVE",
        admission_date=date(2024, 8, 1),
        expected_graduation_date=date(2028, 5, 30),
        program_id=prog_cse.id,
        batch_id=batch.id,
        current_semester_id=sem.id,
        current_section_id=sec.id,
    )

    # 6. Student in Mechanical (Student B)
    u_stu_b, _ = await create_test_user(
        db_session, tenant_a.id, f"student_b_{uid}@campusos.internal", "STUDENT", "Bhavik", "Shah"
    )
    student_b = StudentProfile(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        user_id=u_stu_b.id,
        admission_number=f"ADM-B-{uid}",
        registration_number=f"REG-B-{uid}",
        roll_number=f"24ME001-{uid}",
        date_of_birth=date(2004, 8, 20),
        gender="MALE",
        status="ACTIVE",
        admission_date=date(2024, 8, 1),
        expected_graduation_date=date(2028, 5, 30),
        program_id=prog_mech.id,
        batch_id=batch.id,
    )
    db_session.add_all([student_a, student_b])
    await db_session.commit()

    # TEST A: HOD of CSE inspects Student A (CSE) -> 200 OK
    res_a = await client.get(f"/api/v1/hod/students/{student_a.id}", headers=headers, cookies=cookie_cse)
    assert res_a.status_code == 200
    data_a = res_a.json()["data"]
    assert data_a["id"] == str(student_a.id)
    assert data_a["first_name"] == "Aarav"
    assert data_a["program"]["id"] == str(prog_cse.id)
    assert data_a["program"]["department_id"] == str(dept_cse.id)
    assert data_a["current_semester"] == 5
    assert data_a["section_name"] == "A"

    # TEST B: HOD of CSE attempts to inspect Student B (Mechanical) -> 403 Forbidden!
    res_b = await client.get(f"/api/v1/hod/students/{student_b.id}", headers=headers, cookies=cookie_cse)
    assert res_b.status_code == 403
    assert "belongs to another academic department" in res_b.json()["detail"].lower()

    # TEST C: Non-existent student -> 404 Not Found
    res_404 = await client.get(f"/api/v1/hod/students/{uuid.uuid4()}", headers=headers, cookies=cookie_cse)
    assert res_404.status_code == 404


# =============================================================================
# TASK 3: DATABASE-BACKED DASHBOARD AGGREGATES VS ZERO COUNTS
# =============================================================================


@pytest.mark.asyncio
async def test_hod_dashboard_real_aggregates_vs_zeroes(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
) -> None:
    """Verify dashboard metrics are computed from real DB data and empty departments return 0s."""
    uid = uuid.uuid4().hex[:6]
    headers = {"X-Tenant-ID": str(tenant_a.id)}

    # 1. Create an empty department
    dept_empty = Department(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        code=f"EMP-{uid}",
        name="Empty Science Department",
        department_type="ACADEMIC",
        is_active=True,
    )
    db_session.add(dept_empty)
    await db_session.flush()

    hod_empty, cookie_empty = await create_test_user(
        db_session, tenant_a.id, f"hod_empty_{uid}@campusos.internal", "HOD", "Empty", "HOD"
    )
    dept_empty.hod_user_id = hod_empty.id
    await db_session.commit()

    # TEST A: Query empty department dashboard -> All statistics must be 0 (no hardcoded 720/28/42/18)
    res_empty = await client.get("/api/v1/hod/dashboard", headers=headers, cookies=cookie_empty)
    assert res_empty.status_code == 200
    stats_empty = res_empty.json()["data"]["statistics"]

    assert stats_empty["total_students"] == 0
    assert stats_empty["total_faculty"] == 0
    assert stats_empty["total_subjects"] == 0
    assert stats_empty["total_classes"] == 0
    assert stats_empty["average_student_attendance"] == 0.0
    assert stats_empty["average_faculty_attendance"] == 0.0
    assert stats_empty["attendance_shortage_count"] == 0
    assert stats_empty["pending_approval_requests"] == 0

    # 2. Now add real data: Program, Subject, Faculty, Student, and Attendance in a department
    dept_active = Department(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        code=f"ACT-{uid}",
        name="Active Department",
        department_type="ACADEMIC",
        is_active=True,
    )
    db_session.add(dept_active)
    await db_session.flush()

    hod_active, cookie_active = await create_test_user(
        db_session, tenant_a.id, f"hod_active_{uid}@campusos.internal", "HOD", "Active", "Head"
    )
    dept_active.hod_user_id = hod_active.id

    # Faculty in Active Dept
    u_fac, _ = await create_test_user(
        db_session, tenant_a.id, f"faculty_act_{uid}@campusos.internal", "FACULTY", "Prof", "Sharma"
    )
    fac_profile = FacultyProfile(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        user_id=u_fac.id,
        employee_code=f"FAC-{uid}",
        department_id=dept_active.id,
        designation="Professor",
        highest_qualification="Ph.D",
        joining_date=date(2020, 7, 1),
        employment_status="ACTIVE",
    )
    db_session.add(fac_profile)

    # Subject in Active Dept
    subject = Subject(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        department_id=dept_active.id,
        code=f"CS101-{uid}",
        name="Intro to Programming",
        credits=3,
        subject_type="THEORY",
    )
    db_session.add(subject)

    # Program in Active Dept
    prog = Program(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        department_id=dept_active.id,
        code=f"BTECH-ACT-{uid}",
        name="B.Tech Active",
        degree_level="UG",
        duration_years=4,
    )
    db_session.add(prog)
    await db_session.flush()

    # Student in Active Dept
    reg2 = Regulation(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        code=f"R2-{uid}",
        title=f"Regulation 2 {uid}",
        effective_year=2026,
    )
    db_session.add(reg2)
    await db_session.flush()

    ay = AcademicYear(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        name=f"2026-2027-{uid}",
        start_date=date(2026, 7, 1),
        end_date=date(2027, 6, 30),
    )
    batch = Batch(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        program_id=prog.id,
        regulation_id=reg2.id,
        name=f"Batch {uid}",
        admission_year=2026,
        graduation_year=2030,
    )
    sem = Semester(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        academic_year_id=ay.id,
        semester_number=1,
        term_type="ODD",
        name="Semester 1",
        start_date=date(2026, 7, 1),
        end_date=date(2026, 12, 1),
    )
    db_session.add_all([ay, batch, sem])
    await db_session.flush()

    sec = Section(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        program_id=prog.id,
        batch_id=batch.id,
        semester_id=sem.id,
        name="A",
        capacity=60,
    )
    db_session.add(sec)
    await db_session.flush()

    offering = CourseOffering(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        subject_id=subject.id,
        academic_year_id=ay.id,
        semester_id=sem.id,
        section_id=sec.id,
    )
    db_session.add(offering)
    await db_session.flush()

    u_stu, _ = await create_test_user(
        db_session, tenant_a.id, f"student_act_{uid}@campusos.internal", "STUDENT", "Dev", "Patel"
    )
    stu = StudentProfile(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        user_id=u_stu.id,
        admission_number=f"ADM-ACT-{uid}",
        registration_number=f"REG-ACT-{uid}",
        roll_number=f"24ACT01-{uid}",
        date_of_birth=date(2005, 1, 1),
        gender="MALE",
        status="ACTIVE",
        admission_date=date(2024, 8, 1),
        expected_graduation_date=date(2028, 5, 30),
        program_id=prog.id,
        batch_id=batch.id,
        current_semester_id=sem.id,
        current_section_id=sec.id,
    )
    db_session.add(stu)
    await db_session.flush()

    # Real Attendance: 2 sessions, 1 PRESENT, 1 ABSENT -> 50%
    att_session1 = AttendanceSession(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        course_offering_id=offering.id,
        section_id=sec.id,
        faculty_id=fac_profile.id,
        academic_year_id=ay.id,
        semester_id=sem.id,
        session_date=date(2026, 9, 1),
        period_number=1,
    )
    att_session2 = AttendanceSession(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        course_offering_id=offering.id,
        section_id=sec.id,
        faculty_id=fac_profile.id,
        academic_year_id=ay.id,
        semester_id=sem.id,
        session_date=date(2026, 9, 1),
        period_number=2,
    )
    db_session.add_all([att_session1, att_session2])
    await db_session.flush()

    rec1 = AttendanceRecord(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        session_id=att_session1.id,
        student_id=stu.id,
        status="PRESENT",
        recorded_by_user_id=u_fac.id,
    )
    rec2 = AttendanceRecord(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        session_id=att_session2.id,
        student_id=stu.id,
        status="ABSENT",
        recorded_by_user_id=u_fac.id,
    )
    db_session.add_all([rec1, rec2])

    # Add an unresolved AttendanceAlert for another department (Dept Empty) to verify leak isolation
    prog_other = Program(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        department_id=dept_empty.id,
        code=f"BTECH-OTH-{uid}",
        name="B.Tech Other",
        degree_level="UG",
        duration_years=4,
    )
    db_session.add(prog_other)
    await db_session.flush()

    u_other, _ = await create_test_user(
        db_session, tenant_a.id, f"student_other_{uid}@campusos.internal", "STUDENT", "Other", "Student"
    )
    stu_other = StudentProfile(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        user_id=u_other.id,
        admission_number=f"ADM-OTH-{uid}",
        registration_number=f"REG-OTH-{uid}",
        roll_number=f"24OTH01-{uid}",
        date_of_birth=date(2005, 1, 1),
        gender="FEMALE",
        status="ACTIVE",
        admission_date=date(2024, 8, 1),
        expected_graduation_date=date(2028, 5, 30),
        program_id=prog_other.id,
        batch_id=batch.id,
        current_semester_id=sem.id,
    )
    db_session.add(stu_other)
    await db_session.flush()

    alert_other = AttendanceAlert(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        student_id=stu_other.id,
        course_offering_id=offering.id,
        attendance_percentage=60.0,
        threshold_percentage=75.0,
        alert_type="LOW_ATTENDANCE_CRITICAL",
        message="Student attendance critically low",
        is_resolved=False,
    )
    db_session.add(alert_other)
    await db_session.commit()

    # TEST B: Query Active Department Dashboard -> Reflects real counts
    res_active = await client.get("/api/v1/hod/dashboard", headers=headers, cookies=cookie_active)
    assert res_active.status_code == 200
    stats_active = res_active.json()["data"]["statistics"]

    assert stats_active["total_students"] == 1
    assert stats_active["total_faculty"] == 1
    assert stats_active["total_subjects"] == 1
    assert stats_active["average_student_attendance"] == 50.0
    assert stats_active["attendance_shortage_count"] == 0  # Unrelated alert excluded!


# =============================================================================
# TASK 4: ROLE AUTHORIZATION INVARIANTS
# =============================================================================


@pytest.mark.asyncio
async def test_hod_role_authorization_invariants(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
    faculty_user: User,
) -> None:
    """Verify that unauthenticated requests return 401 and unauthorized roles return 403."""
    headers = {"X-Tenant-ID": str(tenant_a.id)}

    # TEST A: Unauthenticated request -> 401 Unauthorized
    res_unauth = await client.get("/api/v1/hod/dashboard", headers=headers)
    assert res_unauth.status_code == 401

    # TEST B: Faculty user (without HOD role) -> 403 Forbidden
    fac_token = create_access_token(
        user_id=faculty_user.id,
        tenant_id=tenant_a.id,
        email=faculty_user.email,
        roles=["FACULTY"],
        permissions=[],
    )
    cookie_fac = {ACCESS_TOKEN_COOKIE_NAME: fac_token}
    res_fac = await client.get("/api/v1/hod/dashboard", headers=headers, cookies=cookie_fac)
    assert res_fac.status_code == 403
    assert "does not have an authorized hod" in res_fac.json()["detail"].lower()
