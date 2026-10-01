"""Comprehensive automated tests for CampusOS Step 6: Attendance Management Engine."""

import uuid
from datetime import date
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.core import Institution
from app.models.people import FacultyProfile, Role, StudentProfile, User, UserRoleAssignment


async def authenticate_user(
    client: AsyncClient, email: str, password: str = "SuperSecret123!"
) -> dict[str, Any]:
    """Helper to authenticate a test client and establish session cookies."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert resp.status_code == 200, f"Authentication failed: {resp.text}"
    return resp.json()["data"]


async def setup_academic_environment(client: AsyncClient) -> dict[str, Any]:
    """Helper to initialize department, program, academic year, semester, section, subject, offering."""
    uid = uuid.uuid4().hex[:5]

    # 1. Department
    dept_res = await client.post(
        "/api/v1/departments",
        json={"code": f"CSE_{uid.upper()}", "name": f"Computer Science {uid}"},
    )
    assert dept_res.status_code == 201
    dept_id = dept_res.json()["data"]["id"]

    # 2. Program
    prog_res = await client.post(
        "/api/v1/programs",
        json={
            "department_id": dept_id,
            "code": f"BTECH_CS_{uid.upper()}",
            "name": "B.Tech Computer Science",
            "degree_level": "UNDERGRADUATE",
            "duration_years": 4,
            "total_semesters": 8,
        },
    )
    assert prog_res.status_code == 201
    prog_id = prog_res.json()["data"]["id"]

    # 3. Academic Year & Semester
    ay_res = await client.post(
        "/api/v1/academic-years",
        json={
            "code": f"AY_{uid.upper()}",
            "name": "2026-2027",
            "start_date": "2026-06-01",
            "end_date": "2027-05-31",
            "is_current": True,
        },
    )
    assert ay_res.status_code == 201
    ay_id = ay_res.json()["data"]["id"]

    sem_res = await client.post(
        "/api/v1/semesters",
        json={
            "academic_year_id": ay_id,
            "name": "Fall 2026",
            "semester_number": 3,
            "term_type": "ODD",
            "start_date": "2026-07-01",
            "end_date": "2026-11-30",
        },
    )
    assert sem_res.status_code == 201
    sem_id = sem_res.json()["data"]["id"]

    # 4. Regulation & Batch
    reg_res = await client.post(
        "/api/v1/regulations",
        json={
            "code": f"REG_{uid.upper()}",
            "title": "Regulation 2026",
            "effective_year": 2026,
        },
    )
    assert reg_res.status_code == 201
    reg_id = reg_res.json()["data"]["id"]

    batch_res = await client.post(
        "/api/v1/batches",
        json={
            "program_id": prog_id,
            "regulation_id": reg_id,
            "name": f"Batch 2025-2029 {uid}",
            "admission_year": 2025,
            "graduation_year": 2029,
        },
    )
    assert batch_res.status_code == 201
    batch_id = batch_res.json()["data"]["id"]

    # 5. Section
    sec_res = await client.post(
        "/api/v1/sections",
        json={
            "program_id": prog_id,
            "batch_id": batch_id,
            "semester_id": sem_id,
            "name": f"Sec-{uid.upper()}",
            "capacity": 60,
        },
    )
    assert sec_res.status_code == 201
    sec_id = sec_res.json()["data"]["id"]

    # 6. Subject
    subj_res = await client.post(
        "/api/v1/academics/subjects",
        json={
            "department_id": dept_id,
            "code": f"CS_{uid.upper()}",
            "name": "Algorithms and Data Structures",
            "credits": 4.0,
            "lecture_hours": 3,
            "tutorial_hours": 1,
            "practical_hours": 2,
            "subject_type": "THEORY",
        },
    )
    assert subj_res.status_code == 201
    subj_id = subj_res.json()["data"]["id"]

    # 7. Course Offering
    off_res = await client.post(
        "/api/v1/academics/course-offerings",
        json={
            "subject_id": subj_id,
            "academic_year_id": ay_id,
            "semester_id": sem_id,
            "section_id": sec_id,
            "max_capacity": 60,
            "status": "ACTIVE",
        },
    )
    assert off_res.status_code == 201
    off_id = off_res.json()["data"]["id"]

    # 8. Faculty
    fac_email = f"prof_{uid}@apextech.edu"
    fac_res = await client.post(
        "/api/v1/faculty",
        json={
            "email": fac_email,
            "first_name": "Barbara",
            "last_name": "Liskov",
            "department_id": dept_id,
            "employee_code": f"FAC_{uid.upper()}",
            "designation": "Professor",
            "highest_qualification": "Ph.D.",
            "joining_date": "2020-01-01",
        },
    )
    assert fac_res.status_code == 201
    fac_id = fac_res.json()["data"]["id"]

    # Assign Faculty
    assign_res = await client.post(
        f"/api/v1/academics/course-offerings/{off_id}/faculty",
        json={"faculty_id": fac_id, "role": "PRIMARY"},
    )
    assert assign_res.status_code == 200

    # 9. Admit 2 Students
    stud_ids = []
    for i in range(1, 3):
        stu_res = await client.post(
            "/api/v1/students",
            json={
                "email": f"stud{i}_{uid}@apextech.edu",
                "admission_number": f"ADM_{uid}_{i}",
                "first_name": f"Student{i}",
                "last_name": f"Test",
                "date_of_birth": "2005-05-15",
                "gender": "FEMALE" if i == 1 else "MALE",
                "admission_date": "2025-08-01",
                "expected_graduation_date": "2029-05-31",
                "program_id": prog_id,
                "batch_id": batch_id,
                "current_semester_id": sem_id,
                "current_section_id": sec_id,
                "roll_number": f"CS25{uid.upper()}{i:02d}",
            },
        )
        assert stu_res.status_code == 201, f"Student admit failed: {stu_res.text}"
        sid = stu_res.json()["data"]["id"]
        stud_ids.append(sid)

        # Enroll student in course offering
        enr_res = await client.post(
            f"/api/v1/academics/course-offerings/{off_id}/students",
            json={"student_id": sid, "enrollment_type": "REGULAR"},
        )
        assert enr_res.status_code == 201, f"Course enrollment failed: {enr_res.text}"

    return {
        "dept_id": dept_id,
        "prog_id": prog_id,
        "ay_id": ay_id,
        "sem_id": sem_id,
        "sec_id": sec_id,
        "subj_id": subj_id,
        "off_id": off_id,
        "fac_id": fac_id,
        "fac_email": fac_email,
        "student_ids": stud_ids,
    }


# =============================================================================
# 1. ATTENDANCE POLICY MANAGEMENT & RESOLUTION
# =============================================================================
@pytest.mark.asyncio
async def test_attendance_policy_lifecycle(
    client: AsyncClient,
    super_admin_user: User,
    tenant_a: Institution,
) -> None:
    await authenticate_user(client, super_admin_user.email)

    # 1. Create institutional policy
    policy_res = await client.post(
        "/api/v1/attendance/policies",
        json={
            "name": "Institutional Standard Policy",
            "minimum_percentage": 75.0,
            "warning_threshold_percentage": 80.0,
            "critical_threshold_percentage": 65.0,
            "condonation_percentage": 65.0,
            "late_grace_minutes": 10,
            "late_weight": 1.0,
            "excused_counts_as_present": True,
            "on_leave_counts_as_present": False,
        },
    )
    assert policy_res.status_code == 201
    pol_data = policy_res.json()["data"]
    assert pol_data["name"] == "Institutional Standard Policy"
    assert float(pol_data["minimum_percentage"]) == 75.0
    policy_id = pol_data["id"]

    # 2. Update policy
    patch_res = await client.patch(
        f"/api/v1/attendance/policies/{policy_id}",
        json={"warning_threshold_percentage": 82.0},
    )
    assert patch_res.status_code == 200
    assert float(patch_res.json()["data"]["warning_threshold_percentage"]) == 82.0

    # 3. List policies
    list_res = await client.get("/api/v1/attendance/policies")
    assert list_res.status_code == 200
    assert len(list_res.json()["data"]) >= 1


# =============================================================================
# 2. SESSION CREATION, LIFECYCLE & TIMETABLE INTEGRATION
# =============================================================================
@pytest.mark.asyncio
async def test_attendance_session_lifecycle(
    client: AsyncClient,
    super_admin_user: User,
    tenant_a: Institution,
) -> None:
    await authenticate_user(client, super_admin_user.email)
    env = await setup_academic_environment(client)

    # 1. Create manual session
    sess_payload = {
        "course_offering_id": env["off_id"],
        "section_id": env["sec_id"],
        "faculty_id": env["fac_id"],
        "session_date": "2026-09-15",
        "period_number": 1,
        "session_type": "LECTURE",
        "topic": "Binary Search Trees",
    }
    create_res = await client.post("/api/v1/attendance/sessions", json=sess_payload)
    assert create_res.status_code == 201
    sess_data = create_res.json()["data"]
    assert sess_data["status"] == "SCHEDULED"
    assert sess_data["period_number"] == 1
    assert sess_data["topic"] == "Binary Search Trees"
    session_id = sess_data["id"]

    # 2. Invalid date: Outside semester (semester ends 2026-11-30)
    invalid_date_payload = dict(sess_payload, session_date="2026-12-15", period_number=2)
    inv_res = await client.post("/api/v1/attendance/sessions", json=invalid_date_payload)
    assert inv_res.status_code == 422
    assert "outside Semester period" in inv_res.json()["error"]["message"]

    # 3. Duplicate slot: same offering, date, period_number -> 409
    dup_res = await client.post("/api/v1/attendance/sessions", json=sess_payload)
    assert dup_res.status_code == 409

    # 4. Open session
    open_res = await client.post(f"/api/v1/attendance/sessions/{session_id}/open")
    assert open_res.status_code == 200
    assert open_res.json()["data"]["status"] == "OPEN"

    # 5. Get session detail & roster
    detail_res = await client.get(f"/api/v1/attendance/sessions/{session_id}")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()["data"]
    assert len(detail_data["roster"]) == 2
    assert detail_data["session"]["status"] == "OPEN"

    # 6. Timetable integration: create time slot and timetable entry
    ts_res = await client.post(
        "/api/v1/academics/time-slots",
        json={
            "name": f"P1_{uuid.uuid4().hex[:4]}",
            "slot_number": 2,
            "start_time": "09:00:00",
            "end_time": "09:50:00",
            "slot_type": "LECTURE",
        },
    )
    assert ts_res.status_code == 201
    ts_id = ts_res.json()["data"]["id"]

    tt_res = await client.post(
        "/api/v1/academics/timetable",
        json={
            "course_offering_id": env["off_id"],
            "section_id": env["sec_id"],
            "academic_year_id": env["ay_id"],
            "semester_id": env["sem_id"],
            "faculty_id": env["fac_id"],
            "time_slot_id": ts_id,
            "day_of_week": 2,  # Tuesday
        },
    )
    assert tt_res.status_code == 201
    tt_id = tt_res.json()["data"]["id"]

    # Generate session from timetable
    from_tt_res = await client.post(
        "/api/v1/attendance/sessions/from-timetable",
        json={
            "timetable_entry_id": tt_id,
            "session_date": "2026-09-15",
            "topic": "AVL Trees and Rotations",
        },
    )
    assert from_tt_res.status_code == 201
    from_tt_data = from_tt_res.json()["data"]
    assert from_tt_data["period_number"] == 2
    assert from_tt_data["topic"] == "AVL Trees and Rotations"


# =============================================================================
# 3. BULK ATTENDANCE RECORDING & LOCKED IMMUTABILITY
# =============================================================================
@pytest.mark.asyncio
async def test_bulk_attendance_marking_and_locking(
    client: AsyncClient,
    super_admin_user: User,
    tenant_a: Institution,
) -> None:
    await authenticate_user(client, super_admin_user.email)
    env = await setup_academic_environment(client)

    # 1. Create and open session
    sess_res = await client.post(
        "/api/v1/attendance/sessions",
        json={
            "course_offering_id": env["off_id"],
            "section_id": env["sec_id"],
            "faculty_id": env["fac_id"],
            "session_date": "2026-09-16",
            "period_number": 1,
            "session_type": "LECTURE",
        },
    )
    assert sess_res.status_code == 201
    session_id = sess_res.json()["data"]["id"]

    # 2. Bulk submit attendance
    s1_id = env["student_ids"][0]
    s2_id = env["student_ids"][1]

    bulk_payload = {
        "records": [
            {"student_id": s1_id, "status": "PRESENT", "remarks": "On time"},
            {"student_id": s2_id, "status": "ABSENT", "remarks": "Unexcused"},
        ],
        "auto_lock": False,
    }
    bulk_res = await client.post(
        f"/api/v1/attendance/sessions/{session_id}/records/bulk",
        json=bulk_payload,
    )
    assert bulk_res.status_code == 200
    b_data = bulk_res.json()["data"]
    assert b_data["status"] == "MARKED"
    assert b_data["total_present"] == 1
    assert b_data["total_absent"] == 1

    # 3. Lock session
    lock_res = await client.post(f"/api/v1/attendance/sessions/{session_id}/lock")
    assert lock_res.status_code == 200
    assert lock_res.json()["data"]["status"] == "LOCKED"

    # 4. Immutability guard: Attempting to modify records on locked session fails with 422
    fail_mod_res = await client.post(
        f"/api/v1/attendance/sessions/{session_id}/records/bulk",
        json=bulk_payload,
    )
    assert fail_mod_res.status_code == 422
    assert "locked" in fail_mod_res.json()["error"]["message"]


# =============================================================================
# 4. VALIDATION & SECURITY (UNENROLLED STUDENT & DUPLICATES)
# =============================================================================
@pytest.mark.asyncio
async def test_unenrolled_student_rejection(
    client: AsyncClient,
    super_admin_user: User,
    tenant_a: Institution,
) -> None:
    await authenticate_user(client, super_admin_user.email)
    env = await setup_academic_environment(client)

    sess_res = await client.post(
        "/api/v1/attendance/sessions",
        json={
            "course_offering_id": env["off_id"],
            "section_id": env["sec_id"],
            "faculty_id": env["fac_id"],
            "session_date": "2026-09-17",
            "period_number": 1,
        },
    )
    session_id = sess_res.json()["data"]["id"]

    fake_student_id = str(uuid.uuid4())
    bad_payload = {
        "records": [
            {"student_id": fake_student_id, "status": "PRESENT"},
        ]
    }
    bad_res = await client.post(
        f"/api/v1/attendance/sessions/{session_id}/records/bulk",
        json=bad_payload,
    )
    assert bad_res.status_code == 422
    assert "not enrolled" in bad_res.json()["error"]["message"]

    # Duplicate student in same payload
    dup_payload = {
        "records": [
            {"student_id": env["student_ids"][0], "status": "PRESENT"},
            {"student_id": env["student_ids"][0], "status": "ABSENT"},
        ]
    }
    dup_res = await client.post(
        f"/api/v1/attendance/sessions/{session_id}/records/bulk",
        json=dup_payload,
    )
    assert dup_res.status_code == 422
    assert "Duplicate student_id" in dup_res.json()["error"]["message"]


# =============================================================================
# 5. ATTENDANCE CALCULATION & SUMMARIES
# =============================================================================
@pytest.mark.asyncio
async def test_attendance_calculation_and_summaries(
    client: AsyncClient,
    super_admin_user: User,
    tenant_a: Institution,
) -> None:
    await authenticate_user(client, super_admin_user.email)
    env = await setup_academic_environment(client)

    s1_id = env["student_ids"][0]
    s2_id = env["student_ids"][1]

    # Conduct 4 sessions:
    # Student 1: 3 PRESENT, 1 ABSENT -> 75%
    # Student 2: 1 PRESENT, 3 ABSENT -> 25% (CRITICAL)
    pattern = [
        ("PRESENT", "ABSENT"),
        ("PRESENT", "ABSENT"),
        ("PRESENT", "ABSENT"),
        ("ABSENT", "PRESENT"),
    ]

    for p_num, (s1_stat, s2_stat) in enumerate(pattern, start=1):
        s_res = await client.post(
            "/api/v1/attendance/sessions",
            json={
                "course_offering_id": env["off_id"],
                "section_id": env["sec_id"],
                "faculty_id": env["fac_id"],
                "session_date": f"2026-09-2{p_num}",
                "period_number": 1,
            },
        )
        s_id = s_res.json()["data"]["id"]

        await client.post(
            f"/api/v1/attendance/sessions/{s_id}/records/bulk",
            json={
                "records": [
                    {"student_id": s1_id, "status": s1_stat},
                    {"student_id": s2_id, "status": s2_stat},
                ],
                "auto_lock": True,
            },
        )

    # 1. Student 1 Summary
    s1_sum_res = await client.get(f"/api/v1/attendance/students/{s1_id}/summary")
    assert s1_sum_res.status_code == 200
    s1_data = s1_sum_res.json()["data"]
    assert s1_data["total_conducted_sessions"] == 4
    assert float(s1_data["total_attended_sessions"]) == 3.0
    assert float(s1_data["overall_percentage"]) == 75.0
    assert s1_data["status"] == "NORMAL"

    # 2. Student 2 Summary
    s2_sum_res = await client.get(f"/api/v1/attendance/students/{s2_id}/summary")
    assert s2_sum_res.status_code == 200
    s2_data = s2_sum_res.json()["data"]
    assert s2_data["total_conducted_sessions"] == 4
    assert float(s2_data["total_attended_sessions"]) == 1.0
    assert float(s2_data["overall_percentage"]) == 25.0
    assert s2_data["status"] == "CRITICAL"

    # 3. Course Offering Summary
    course_sum_res = await client.get(
        f"/api/v1/attendance/course-offerings/{env['off_id']}/summary"
    )
    assert course_sum_res.status_code == 200
    c_data = course_sum_res.json()["data"]
    assert c_data["total_sessions_conducted"] == 4
    assert c_data["total_enrolled_students"] == 2
    assert float(c_data["average_attendance_percentage"]) == 50.0  # (75 + 25) / 2
    assert c_data["students_below_minimum"] == 1  # s2 is below minimum 75%


# =============================================================================
# 6. LEAVE MANAGEMENT & ATTENDANCE IMPACT
# =============================================================================
@pytest.mark.asyncio
async def test_student_leave_workflow_and_impact(
    client: AsyncClient,
    super_admin_user: User,
    tenant_a: Institution,
) -> None:
    await authenticate_user(client, super_admin_user.email)
    env = await setup_academic_environment(client)
    s1_id = env["student_ids"][0]

    # 1. Mark session on 2026-09-21 with student 1 ABSENT
    sess_res = await client.post(
        "/api/v1/attendance/sessions",
        json={
            "course_offering_id": env["off_id"],
            "section_id": env["sec_id"],
            "faculty_id": env["fac_id"],
            "session_date": "2026-09-21",
            "period_number": 1,
        },
    )
    s_id = sess_res.json()["data"]["id"]
    await client.post(
        f"/api/v1/attendance/sessions/{s_id}/records/bulk",
        json={
            "records": [
                {"student_id": s1_id, "status": "ABSENT"},
                {"student_id": env["student_ids"][1], "status": "PRESENT"},
            ],
            "auto_lock": False,
        },
    )

    # 2. Student applies for leave covering 2026-09-20 to 2026-09-22
    leave_payload = {
        "student_id": s1_id,
        "leave_type": "MEDICAL",
        "start_date": "2026-09-20",
        "end_date": "2026-09-22",
        "reason": "Severe fever and doctor consultation",
    }
    leave_res = await client.post("/api/v1/attendance/leaves", json=leave_payload)
    assert leave_res.status_code == 201
    l_data = leave_res.json()["data"]
    assert l_data["status"] == "PENDING"
    assert l_data["days_count"] == 3
    leave_id = l_data["id"]

    # 3. Overlap rejection: duplicate leave for same dates -> 409
    dup_leave = await client.post("/api/v1/attendance/leaves", json=leave_payload)
    assert dup_leave.status_code == 409

    # 4. Approve leave
    approve_res = await client.post(
        f"/api/v1/attendance/leaves/{leave_id}/approve",
        json={"review_notes": "Medical certificate verified"},
    )
    assert approve_res.status_code == 200
    assert approve_res.json()["data"]["status"] == "APPROVED"

    # 5. Verify attendance impact: ABSENT record on 2026-09-21 was updated to ON_LEAVE
    rec_res = await client.get(f"/api/v1/attendance/sessions/{s_id}/records")
    assert rec_res.status_code == 200
    s1_rec = next(r for r in rec_res.json()["data"] if r["student_id"] == s1_id)
    assert s1_rec["status"] == "ON_LEAVE"


# =============================================================================
# 7. ATTENDANCE CORRECTION WORKFLOW (LOCKED REGISTER REVISION)
# =============================================================================
@pytest.mark.asyncio
async def test_attendance_correction_workflow(
    client: AsyncClient,
    super_admin_user: User,
    tenant_a: Institution,
) -> None:
    await authenticate_user(client, super_admin_user.email)
    env = await setup_academic_environment(client)
    s1_id = env["student_ids"][0]

    # 1. Create, mark and lock a session with student 1 marked ABSENT
    sess_res = await client.post(
        "/api/v1/attendance/sessions",
        json={
            "course_offering_id": env["off_id"],
            "section_id": env["sec_id"],
            "faculty_id": env["fac_id"],
            "session_date": "2026-09-23",
            "period_number": 1,
        },
    )
    s_id = sess_res.json()["data"]["id"]
    await client.post(
        f"/api/v1/attendance/sessions/{s_id}/records/bulk",
        json={
            "records": [
                {"student_id": s1_id, "status": "ABSENT"},
                {"student_id": env["student_ids"][1], "status": "PRESENT"},
            ],
            "auto_lock": True,
        },
    )

    # Fetch record ID
    rec_res = await client.get(f"/api/v1/attendance/sessions/{s_id}/records")
    s1_rec = next(r for r in rec_res.json()["data"] if r["student_id"] == s1_id)
    rec_id = s1_rec["id"]

    # 2. Request correction
    corr_res = await client.post(
        "/api/v1/attendance/corrections",
        json={
            "attendance_record_id": rec_id,
            "requested_status": "PRESENT",
            "reason": "Student was physically in class but arrived right as attendance was taken.",
        },
    )
    assert corr_res.status_code == 201
    c_data = corr_res.json()["data"]
    assert c_data["approval_status"] == "PENDING"
    assert c_data["previous_status"] == "ABSENT"
    assert c_data["requested_status"] == "PRESENT"
    corr_id = c_data["id"]

    # 3. Approve correction
    app_res = await client.post(
        f"/api/v1/attendance/corrections/{corr_id}/approve",
        json={"approval_notes": "Confirmed by faculty in person."},
    )
    assert app_res.status_code == 200
    assert app_res.json()["data"]["approval_status"] == "APPROVED"

    # 4. Verify record status is now updated to PRESENT
    rec_check = await client.get(f"/api/v1/attendance/sessions/{s_id}/records")
    s1_updated_rec = next(r for r in rec_check.json()["data"] if r["student_id"] == s1_id)
    assert s1_updated_rec["status"] == "PRESENT"


# =============================================================================
# 8. LOW ATTENDANCE INTELLIGENCE & DASHBOARD
# =============================================================================
@pytest.mark.asyncio
async def test_low_attendance_and_dashboard(
    client: AsyncClient,
    super_admin_user: User,
    tenant_a: Institution,
) -> None:
    await authenticate_user(client, super_admin_user.email)
    env = await setup_academic_environment(client)

    # Create 3 sessions with student 2 absent so low attendance threshold triggers
    s2_id = env["student_ids"][1]
    for p in range(1, 4):
        s_res = await client.post(
            "/api/v1/attendance/sessions",
            json={
                "course_offering_id": env["off_id"],
                "section_id": env["sec_id"],
                "faculty_id": env["fac_id"],
                "session_date": f"2026-09-1{p}",
                "period_number": 1,
            },
        )
        s_id = s_res.json()["data"]["id"]
        await client.post(
            f"/api/v1/attendance/sessions/{s_id}/records/bulk",
            json={
                "records": [
                    {"student_id": env["student_ids"][0], "status": "PRESENT"},
                    {"student_id": s2_id, "status": "ABSENT"},
                ],
                "auto_lock": True,
            },
        )

    # 1. Trigger low attendance evaluation
    low_res = await client.get(
        f"/api/v1/attendance/low-attendance?course_offering_id={env['off_id']}"
    )
    assert low_res.status_code == 200
    low_students = low_res.json()["data"]
    assert len(low_students) >= 1
    assert any(item["student_id"] == s2_id for item in low_students)

    # 2. Query Dashboard
    dash_res = await client.get("/api/v1/attendance/dashboard")
    assert dash_res.status_code == 200
    dash_data = dash_res.json()["data"]
    assert "today_sessions_count" in dash_data
    assert "average_attendance_percentage" in dash_data
    assert dash_data["total_students_low_attendance"] >= 1


# =============================================================================
# 9. TENANT ISOLATION
# =============================================================================
@pytest.mark.asyncio
async def test_attendance_tenant_isolation(
    client: AsyncClient,
    super_admin_user: User,
    tenant_a: Institution,
    tenant_b: Institution,
    db_session: AsyncSession,
) -> None:
    # 1. Create a session in Tenant A
    await authenticate_user(client, super_admin_user.email)
    env = await setup_academic_environment(client)
    sess_res = await client.post(
        "/api/v1/attendance/sessions",
        json={
            "course_offering_id": env["off_id"],
            "section_id": env["sec_id"],
            "faculty_id": env["fac_id"],
            "session_date": "2026-09-18",
            "period_number": 1,
        },
    )
    assert sess_res.status_code == 201
    session_id = sess_res.json()["data"]["id"]

    # 2. Create and authenticate Admin for Tenant B
    uid_b = uuid.uuid4().hex[:6]
    user_b = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_b.id,
        email=f"admin_{uid_b}@beaconuni.edu",
        phone_number="+1999888777",
        password_hash=get_password_hash("SuperSecret123!"),
        status="ACTIVE",
        first_name="Beacon",
        last_name="Admin",
    )
    db_session.add(user_b)
    await db_session.flush()

    role_res = await db_session.execute(select(Role).where(Role.name == "INSTITUTION_ADMIN"))
    inst_admin_role = role_res.scalar_one_or_none()
    if inst_admin_role:
        db_session.add(
            UserRoleAssignment(
                id=uuid.uuid4(),
                tenant_id=tenant_b.id,
                user_id=user_b.id,
                role_id=inst_admin_role.id,
            )
        )
    await db_session.commit()

    # Authenticate as Tenant B
    await authenticate_user(client, user_b.email)

    # 3. Tenant B attempts to read Tenant A's session -> 404
    t_b_read = await client.get(f"/api/v1/attendance/sessions/{session_id}")
    assert t_b_read.status_code == 404

    # 4. Tenant B attempts to lock Tenant A's session -> 404
    t_b_lock = await client.post(f"/api/v1/attendance/sessions/{session_id}/lock")
    assert t_b_lock.status_code == 404
