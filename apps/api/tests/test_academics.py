"""Comprehensive automated tests for CampusOS Step 5: Academic Management Engine."""

import uuid
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core import Institution
from app.models.people import User


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


# =============================================================================
# 1. SUBJECTS MASTER & CONFLICTS
# =============================================================================
@pytest.mark.asyncio
async def test_subject_crud_and_conflict(
    client: AsyncClient,
    super_admin_user: User,
    tenant_a: Institution,
) -> None:
    await authenticate_user(client, super_admin_user.email)

    # 1. Create a Department first
    dept_code = f"CSE_{uuid.uuid4().hex[:4].upper()}"
    dept_res = await client.post(
        "/api/v1/departments",
        json={"code": dept_code, "name": "Computer Science & Engineering"},
    )
    assert dept_res.status_code == 201
    dept_id = dept_res.json()["data"]["id"]

    # 2. Create Subject
    subj_code = f"CS{uuid.uuid4().hex[:3].upper()}"
    create_payload = {
        "department_id": dept_id,
        "code": subj_code,
        "name": "Data Structures and Algorithms",
        "credits": 4.0,
        "lecture_hours": 3,
        "tutorial_hours": 1,
        "practical_hours": 2,
        "subject_type": "THEORY",
        "description": "Fundamental algorithms, asymptotic analysis, and trees.",
    }
    resp = await client.post("/api/v1/academics/subjects", json=create_payload)
    assert resp.status_code == 201
    sub_data = resp.json()["data"]
    assert sub_data["code"] == subj_code
    assert float(sub_data["credits"]) == 4.0
    subject_id = sub_data["id"]

    # 3. Duplicate code conflict (HTTP 409)
    resp_dup = await client.post("/api/v1/academics/subjects", json=create_payload)
    assert resp_dup.status_code == 409
    assert "already exists" in resp_dup.json()["error"]["message"]

    # 4. Read Subject
    get_resp = await client.get(f"/api/v1/academics/subjects/{subject_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["name"] == "Data Structures and Algorithms"

    # 5. Update Subject
    patch_resp = await client.patch(
        f"/api/v1/academics/subjects/{subject_id}",
        json={"name": "Advanced Data Structures & Algorithms", "credits": 4.5},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["data"]["name"] == "Advanced Data Structures & Algorithms"
    assert float(patch_resp.json()["data"]["credits"]) == 4.5


# =============================================================================
# 2. CURRICULUM SCHEMES & VERSIONING
# =============================================================================
@pytest.mark.asyncio
async def test_curriculum_versioning_and_publish_flow(
    client: AsyncClient,
    super_admin_user: User,
    tenant_a: Institution,
) -> None:
    await authenticate_user(client, super_admin_user.email)

    # 1. Setup prerequisites: Department, Program, Regulation, Subject
    dept_res = await client.post(
        "/api/v1/departments",
        json={"code": f"IT_{uuid.uuid4().hex[:4].upper()}", "name": "Information Technology"},
    )
    dept_id = dept_res.json()["data"]["id"]

    prog_res = await client.post(
        "/api/v1/programs",
        json={
            "department_id": dept_id,
            "code": f"BTECH_IT_{uuid.uuid4().hex[:3].upper()}",
            "name": "B.Tech Information Technology",
            "degree_level": "UG",
            "duration_years": 4.0,
            "total_semesters": 8,
            "required_credits": 160,
        },
    )
    prog_id = prog_res.json()["data"]["id"]

    reg_res = await client.post(
        "/api/v1/regulations",
        json={
            "code": f"R_{uuid.uuid4().hex[:4].upper()}",
            "title": "Autonomous Regulation 2024",
            "effective_year": 2024,
        },
    )
    reg_id = reg_res.json()["data"]["id"]

    subj_res = await client.post(
        "/api/v1/academics/subjects",
        json={
            "department_id": dept_id,
            "code": f"IT{uuid.uuid4().hex[:3].upper()}",
            "name": "Web Technology",
            "credits": 3.0,
            "lecture_hours": 3,
            "tutorial_hours": 0,
            "practical_hours": 0,
            "subject_type": "THEORY",
        },
    )
    subj_id = subj_res.json()["data"]["id"]

    # 2. Create Curriculum Version 1
    curr_v1_res = await client.post(
        "/api/v1/academics/curricula",
        json={
            "program_id": prog_id,
            "regulation_id": reg_id,
            "name": "B.Tech IT 2024 Curriculum v1",
            "version": 1,
            "total_credits": 160.0,
        },
    )
    assert curr_v1_res.status_code == 201
    curr_v1 = curr_v1_res.json()["data"]
    assert curr_v1["status"] == "DRAFT"
    assert curr_v1["is_locked"] is False
    curr_id = curr_v1["id"]

    # 3. Add Subject to Semester 1
    add_subj_res = await client.post(
        f"/api/v1/academics/curricula/{curr_id}/subjects",
        json={
            "subject_id": subj_id,
            "semester_number": 1,
            "category": "CORE",
            "is_mandatory": True,
            "credits": 3.0,
            "lecture_hours": 3,
            "tutorial_hours": 0,
            "practical_hours": 0,
        },
    )
    assert add_subj_res.status_code == 200
    assert len(add_subj_res.json()["data"]["subjects"]) == 1

    # 4. Duplicate subject in same semester (HTTP 409)
    dup_subj_res = await client.post(
        f"/api/v1/academics/curricula/{curr_id}/subjects",
        json={
            "subject_id": subj_id,
            "semester_number": 1,
            "category": "CORE",
        },
    )
    assert dup_subj_res.status_code == 409

    # 5. Publish Curriculum Scheme (locks editing)
    pub_res = await client.post(f"/api/v1/academics/curricula/{curr_id}/publish")
    assert pub_res.status_code == 200
    assert pub_res.json()["data"]["status"] == "PUBLISHED"
    assert pub_res.json()["data"]["is_locked"] is True

    # 6. Verify edits are blocked after publishing
    blocked_edit = await client.patch(
        f"/api/v1/academics/curricula/{curr_id}",
        json={"name": "Altered Name After Publish"},
    )
    assert blocked_edit.status_code in (400, 422)
    assert "locked/published" in blocked_edit.json()["error"]["message"]

    # 7. Create Curriculum Version 2 (Versioning allows side-by-side schemes)
    curr_v2_res = await client.post(
        "/api/v1/academics/curricula",
        json={
            "program_id": prog_id,
            "regulation_id": reg_id,
            "name": "B.Tech IT 2024 Curriculum v2 (Revised)",
            "version": 2,
            "total_credits": 165.0,
        },
    )
    assert curr_v2_res.status_code == 201
    assert curr_v2_res.json()["data"]["version"] == 2


# =============================================================================
# 3. CLASSROOMS & TIME SLOTS
# =============================================================================
@pytest.mark.asyncio
async def test_classrooms_and_time_slots(
    client: AsyncClient,
    super_admin_user: User,
    tenant_a: Institution,
) -> None:
    await authenticate_user(client, super_admin_user.email)

    # 1. Create Classroom
    bldg = f"MainBlock_{uuid.uuid4().hex[:3]}"
    room_resp = await client.post(
        "/api/v1/academics/rooms",
        json={
            "building": bldg,
            "room_number": "101",
            "capacity": 70,
            "room_type": "LECTURE_HALL",
        },
    )
    assert room_resp.status_code == 201
    assert room_resp.json()["data"]["room_number"] == "101"

    # Duplicate room in same building -> 409
    dup_room = await client.post(
        "/api/v1/academics/rooms",
        json={"building": bldg, "room_number": "101", "capacity": 70},
    )
    assert dup_room.status_code == 409

    # 2. Create Time Slot
    slot_resp = await client.post(
        "/api/v1/academics/time-slots",
        json={
            "name": "Morning Period 1",
            "slot_number": 99,
            "start_time": "08:30:00",
            "end_time": "09:20:00",
            "slot_type": "LECTURE",
        },
    )
    assert slot_resp.status_code == 201
    assert slot_resp.json()["data"]["slot_number"] == 99


# =============================================================================
# 4. COURSE OFFERINGS & LIFECYCLE
# =============================================================================
@pytest.mark.asyncio
async def test_course_offering_and_lifecycle(
    client: AsyncClient,
    super_admin_user: User,
    tenant_a: Institution,
) -> None:
    await authenticate_user(client, super_admin_user.email)

    # 1. Setup Department, Program, Academic Year, Semester, Regulation, Batch, Section, Subject
    dept_res = await client.post(
        "/api/v1/departments",
        json={"code": f"ECE_{uuid.uuid4().hex[:4].upper()}", "name": "ECE Department"},
    )
    dept_id = dept_res.json()["data"]["id"]

    prog_res = await client.post(
        "/api/v1/programs",
        json={
            "department_id": dept_id,
            "code": f"BE_ECE_{uuid.uuid4().hex[:3].upper()}",
            "name": "B.E Electronics",
            "degree_level": "UG",
            "duration_years": 4.0,
            "total_semesters": 8,
            "required_credits": 160,
        },
    )
    prog_id = prog_res.json()["data"]["id"]

    ay_res = await client.post(
        "/api/v1/academic-years",
        json={
            "name": f"2026-2027-{uuid.uuid4().hex[:3]}",
            "start_date": "2026-06-01",
            "end_date": "2027-05-31",
            "is_current": False,
        },
    )
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
    sem_id = sem_res.json()["data"]["id"]

    reg_res = await client.post(
        "/api/v1/regulations",
        json={
            "code": f"R_{uuid.uuid4().hex[:4].upper()}",
            "title": "Reg 2026",
            "effective_year": 2026,
        },
    )
    reg_id = reg_res.json()["data"]["id"]

    batch_res = await client.post(
        "/api/v1/batches",
        json={
            "program_id": prog_id,
            "regulation_id": reg_id,
            "name": "2025-2029 Cohort",
            "admission_year": 2025,
            "graduation_year": 2029,
        },
    )
    batch_id = batch_res.json()["data"]["id"]

    sec_res = await client.post(
        "/api/v1/sections",
        json={
            "program_id": prog_id,
            "batch_id": batch_id,
            "semester_id": sem_id,
            "name": "A",
            "capacity": 60,
        },
    )
    sec_id = sec_res.json()["data"]["id"]

    subj_res = await client.post(
        "/api/v1/academics/subjects",
        json={
            "department_id": dept_id,
            "code": f"EC{uuid.uuid4().hex[:3].upper()}",
            "name": "Signals and Systems",
            "credits": 4.0,
            "lecture_hours": 3,
            "tutorial_hours": 1,
            "practical_hours": 0,
            "subject_type": "THEORY",
        },
    )
    subj_id = subj_res.json()["data"]["id"]

    # 2. Create Course Offering
    offering_payload = {
        "subject_id": subj_id,
        "academic_year_id": ay_id,
        "semester_id": sem_id,
        "section_id": sec_id,
        "max_capacity": 60,
        "status": "PLANNED",
    }
    off_res = await client.post("/api/v1/academics/course-offerings", json=offering_payload)
    assert off_res.status_code == 201
    off_data = off_res.json()["data"]
    assert off_data["status"] == "PLANNED"
    off_id = off_data["id"]

    # 3. Duplicate Offering Conflict -> 409
    dup_off = await client.post("/api/v1/academics/course-offerings", json=offering_payload)
    assert dup_off.status_code == 409

    # 4. Status Transition: PLANNED -> OPEN -> ACTIVE -> COMPLETED
    t1 = await client.patch(
        f"/api/v1/academics/course-offerings/{off_id}/status", json={"status": "OPEN"}
    )
    assert t1.status_code == 200
    assert t1.json()["data"]["status"] == "OPEN"

    t2 = await client.patch(
        f"/api/v1/academics/course-offerings/{off_id}/status", json={"status": "ACTIVE"}
    )
    assert t2.status_code == 200
    assert t2.json()["data"]["status"] == "ACTIVE"

    t3 = await client.patch(
        f"/api/v1/academics/course-offerings/{off_id}/status", json={"status": "COMPLETED"}
    )
    assert t3.status_code == 200
    assert t3.json()["data"]["status"] == "COMPLETED"

    # Invalid backward transition from COMPLETED -> 400
    bad_t = await client.patch(
        f"/api/v1/academics/course-offerings/{off_id}/status", json={"status": "ACTIVE"}
    )
    assert bad_t.status_code in (400, 422)


# =============================================================================
# 5. FACULTY ASSIGNMENT & STUDENT ENROLLMENTS
# =============================================================================
@pytest.mark.asyncio
async def test_faculty_assignment_and_student_enrollments(
    client: AsyncClient,
    super_admin_user: User,
    tenant_a: Institution,
) -> None:
    await authenticate_user(client, super_admin_user.email)

    # 1. Setup Department & Offering
    dept_res = await client.post(
        "/api/v1/departments",
        json={"code": f"MECH_{uuid.uuid4().hex[:4].upper()}", "name": "Mechanical Eng"},
    )
    dept_id = dept_res.json()["data"]["id"]

    prog_res = await client.post(
        "/api/v1/programs",
        json={
            "department_id": dept_id,
            "code": f"BE_ME_{uuid.uuid4().hex[:3].upper()}",
            "name": "B.E Mechanical",
            "degree_level": "UG",
            "duration_years": 4.0,
            "total_semesters": 8,
            "required_credits": 160,
        },
    )
    prog_id = prog_res.json()["data"]["id"]

    ay_res = await client.post(
        "/api/v1/academic-years",
        json={
            "name": f"2026-2027-{uuid.uuid4().hex[:3]}",
            "start_date": "2026-06-01",
            "end_date": "2027-05-31",
            "is_current": False,
        },
    )
    ay_id = ay_res.json()["data"]["id"]

    sem_res = await client.post(
        "/api/v1/semesters",
        json={
            "academic_year_id": ay_id,
            "name": "Fall 2026",
            "semester_number": 1,
            "term_type": "ODD",
            "start_date": "2026-07-01",
            "end_date": "2026-11-30",
        },
    )
    sem_id = sem_res.json()["data"]["id"]

    reg_res = await client.post(
        "/api/v1/regulations",
        json={
            "code": f"R_{uuid.uuid4().hex[:4].upper()}",
            "title": "Reg 2026",
            "effective_year": 2026,
        },
    )
    reg_id = reg_res.json()["data"]["id"]

    batch_res = await client.post(
        "/api/v1/batches",
        json={
            "program_id": prog_id,
            "regulation_id": reg_id,
            "name": "2026 Cohort",
            "admission_year": 2026,
            "graduation_year": 2030,
        },
    )
    batch_id = batch_res.json()["data"]["id"]

    sec_res = await client.post(
        "/api/v1/sections",
        json={
            "program_id": prog_id,
            "batch_id": batch_id,
            "semester_id": sem_id,
            "name": "A",
            "capacity": 60,
        },
    )
    sec_id = sec_res.json()["data"]["id"]

    subj_res = await client.post(
        "/api/v1/academics/subjects",
        json={
            "department_id": dept_id,
            "code": f"ME{uuid.uuid4().hex[:3].upper()}",
            "name": "Thermodynamics",
            "credits": 4.0,
            "lecture_hours": 3,
            "tutorial_hours": 1,
            "practical_hours": 0,
            "subject_type": "THEORY",
        },
    )
    subj_id = subj_res.json()["data"]["id"]

    off_res = await client.post(
        "/api/v1/academics/course-offerings",
        json={
            "subject_id": subj_id,
            "academic_year_id": ay_id,
            "semester_id": sem_id,
            "section_id": sec_id,
            "max_capacity": 60,
            "status": "OPEN",
        },
    )
    off_id = off_res.json()["data"]["id"]

    # 2. Onboard Faculty
    fac_email = f"prof_{uuid.uuid4().hex[:6]}@apextech.edu"
    fac_res = await client.post(
        "/api/v1/faculty",
        json={
            "email": fac_email,
            "first_name": "Richard",
            "last_name": "Feynman",
            "department_id": dept_id,
            "employee_code": f"FAC_{uuid.uuid4().hex[:4].upper()}",
            "designation": "Professor",
            "highest_qualification": "Ph.D.",
            "joining_date": "2020-01-01",
        },
    )
    fac_id = fac_res.json()["data"]["id"]

    # 3. Assign Faculty to Offering
    assign_res = await client.post(
        f"/api/v1/academics/course-offerings/{off_id}/faculty",
        json={"faculty_id": fac_id, "role": "PRIMARY"},
    )
    assert assign_res.status_code == 200
    assert len(assign_res.json()["data"]["faculty_assignments"]) == 1
    assert assign_res.json()["data"]["faculty_assignments"][0]["role"] == "PRIMARY"

    # Duplicate Assignment -> 409
    dup_assign = await client.post(
        f"/api/v1/academics/course-offerings/{off_id}/faculty",
        json={"faculty_id": fac_id, "role": "CO_FACULTY"},
    )
    assert dup_assign.status_code == 409

    # 4. Admit Student to Section A
    stu_email = f"student_{uuid.uuid4().hex[:6]}@apextech.edu"
    adm_no = f"ADM_{uuid.uuid4().hex[:5].upper()}"
    stu_res = await client.post(
        "/api/v1/students",
        json={
            "email": stu_email,
            "first_name": "James",
            "last_name": "Watt",
            "admission_number": adm_no,
            "date_of_birth": "2006-03-10",
            "gender": "MALE",
            "program_id": prog_id,
            "batch_id": batch_id,
            "current_semester_id": sem_id,
            "current_section_id": sec_id,
            "admission_date": "2026-06-15",
            "expected_graduation_date": "2030-05-31",
        },
    )
    assert stu_res.status_code == 201
    stu_id = stu_res.json()["data"]["id"]

    # 5. Enroll Student into Course Offering
    enroll_res = await client.post(
        f"/api/v1/academics/course-offerings/{off_id}/students",
        json={"student_id": stu_id, "enrollment_type": "REGULAR"},
    )
    assert enroll_res.status_code == 201
    assert enroll_res.json()["data"]["status"] == "ENROLLED"

    # Duplicate Enrollment -> 409
    dup_enroll = await client.post(
        f"/api/v1/academics/course-offerings/{off_id}/students",
        json={"student_id": stu_id},
    )
    assert dup_enroll.status_code == 409

    # 6. List Enrolled Students
    list_stu = await client.get(f"/api/v1/academics/course-offerings/{off_id}/students")
    assert list_stu.status_code == 200
    assert len(list_stu.json()["data"]) == 1
    assert list_stu.json()["data"][0]["student_admission_number"] == adm_no

    # 7. Withdraw Student
    with_res = await client.delete(f"/api/v1/academics/course-offerings/{off_id}/students/{stu_id}")
    assert with_res.status_code == 200


# =============================================================================
# 6. TIMETABLE MULTI-DIMENSIONAL CONFLICT DETECTION
# =============================================================================
@pytest.mark.asyncio
async def test_timetable_conflict_detection(
    client: AsyncClient,
    super_admin_user: User,
    tenant_a: Institution,
) -> None:
    await authenticate_user(client, super_admin_user.email)

    # 1. Setup Department, Program, Academic Year, Semester, Regulation, Batch
    dept_res = await client.post(
        "/api/v1/departments",
        json={"code": f"CIVIL_{uuid.uuid4().hex[:4].upper()}", "name": "Civil Engineering"},
    )
    dept_id = dept_res.json()["data"]["id"]

    prog_res = await client.post(
        "/api/v1/programs",
        json={
            "department_id": dept_id,
            "code": f"BE_CIVIL_{uuid.uuid4().hex[:3].upper()}",
            "name": "B.E Civil",
            "degree_level": "UG",
            "duration_years": 4.0,
            "total_semesters": 8,
            "required_credits": 160,
        },
    )
    prog_id = prog_res.json()["data"]["id"]

    ay_res = await client.post(
        "/api/v1/academic-years",
        json={
            "name": f"2026-2027-{uuid.uuid4().hex[:3]}",
            "start_date": "2026-06-01",
            "end_date": "2027-05-31",
            "is_current": False,
        },
    )
    ay_id = ay_res.json()["data"]["id"]

    sem_res = await client.post(
        "/api/v1/semesters",
        json={
            "academic_year_id": ay_id,
            "name": "Spring 2027",
            "semester_number": 2,
            "term_type": "EVEN",
            "start_date": "2027-01-01",
            "end_date": "2027-05-31",
        },
    )
    sem_id = sem_res.json()["data"]["id"]

    reg_res = await client.post(
        "/api/v1/regulations",
        json={
            "code": f"R_{uuid.uuid4().hex[:4].upper()}",
            "title": "Reg 2026",
            "effective_year": 2026,
        },
    )
    reg_id = reg_res.json()["data"]["id"]

    batch_res = await client.post(
        "/api/v1/batches",
        json={
            "program_id": prog_id,
            "regulation_id": reg_id,
            "name": "2026 Batch",
            "admission_year": 2026,
            "graduation_year": 2030,
        },
    )
    batch_id = batch_res.json()["data"]["id"]

    # 2 Sections: Sec A and Sec B
    sec_a = (
        await client.post(
            "/api/v1/sections",
            json={
                "program_id": prog_id,
                "batch_id": batch_id,
                "semester_id": sem_id,
                "name": "A",
                "capacity": 60,
            },
        )
    ).json()["data"]["id"]
    sec_b = (
        await client.post(
            "/api/v1/sections",
            json={
                "program_id": prog_id,
                "batch_id": batch_id,
                "semester_id": sem_id,
                "name": "B",
                "capacity": 60,
            },
        )
    ).json()["data"]["id"]

    # 2 Subjects: S1 and S2
    s1_id = (
        await client.post(
            "/api/v1/academics/subjects",
            json={
                "department_id": dept_id,
                "code": f"CE1_{uuid.uuid4().hex[:3].upper()}",
                "name": "Surveying",
                "credits": 3.0,
            },
        )
    ).json()["data"]["id"]
    s2_id = (
        await client.post(
            "/api/v1/academics/subjects",
            json={
                "department_id": dept_id,
                "code": f"CE2_{uuid.uuid4().hex[:3].upper()}",
                "name": "Mechanics",
                "credits": 3.0,
            },
        )
    ).json()["data"]["id"]

    # 2 Course Offerings: Offering 1 (S1 in Sec A) and Offering 2 (S2 in Sec B)
    off_1 = (
        await client.post(
            "/api/v1/academics/course-offerings",
            json={
                "subject_id": s1_id,
                "academic_year_id": ay_id,
                "semester_id": sem_id,
                "section_id": sec_a,
                "status": "ACTIVE",
            },
        )
    ).json()["data"]["id"]
    off_2 = (
        await client.post(
            "/api/v1/academics/course-offerings",
            json={
                "subject_id": s2_id,
                "academic_year_id": ay_id,
                "semester_id": sem_id,
                "section_id": sec_b,
                "status": "ACTIVE",
            },
        )
    ).json()["data"]["id"]

    # 2 Rooms: R1 and R2
    bldg_tag = uuid.uuid4().hex[:4]
    r1_id = (
        await client.post(
            "/api/v1/academics/rooms",
            json={"building": f"Block_{bldg_tag}", "room_number": "201", "capacity": 60},
        )
    ).json()["data"]["id"]
    r2_id = (
        await client.post(
            "/api/v1/academics/rooms",
            json={"building": f"Block_{bldg_tag}", "room_number": "202", "capacity": 60},
        )
    ).json()["data"]["id"]

    # 1 TimeSlot: Period 1
    slot_id = (
        await client.post(
            "/api/v1/academics/time-slots",
            json={
                "name": f"P1_{uuid.uuid4().hex[:3]}",
                "slot_number": 80,
                "start_time": "08:30:00",
                "end_time": "09:20:00",
            },
        )
    ).json()["data"]["id"]

    # 2 Faculty Members: Fac X and Fac Y
    fac_x = (
        await client.post(
            "/api/v1/faculty",
            json={
                "email": f"fac_x_{uuid.uuid4().hex[:6]}@apextech.edu",
                "first_name": "Faculty",
                "last_name": "Xavier",
                "department_id": dept_id,
                "employee_code": f"FX_{uuid.uuid4().hex[:4].upper()}",
                "designation": "Associate Professor",
                "highest_qualification": "Ph.D.",
                "joining_date": "2021-01-01",
            },
        )
    ).json()["data"]["id"]
    fac_y = (
        await client.post(
            "/api/v1/faculty",
            json={
                "email": f"fac_y_{uuid.uuid4().hex[:6]}@apextech.edu",
                "first_name": "Faculty",
                "last_name": "Yolanda",
                "department_id": dept_id,
                "employee_code": f"FY_{uuid.uuid4().hex[:4].upper()}",
                "designation": "Assistant Professor",
                "highest_qualification": "M.Tech",
                "joining_date": "2022-01-01",
            },
        )
    ).json()["data"]["id"]

    # --- Schedule Base Entry: Monday (day 1), Period 1, Sec A, Fac X, Room R1 ---
    entry_1 = await client.post(
        "/api/v1/academics/timetable",
        json={
            "course_offering_id": off_1,
            "section_id": sec_a,
            "academic_year_id": ay_id,
            "semester_id": sem_id,
            "time_slot_id": slot_id,
            "day_of_week": 1,
            "faculty_id": fac_x,
            "room_id": r1_id,
        },
    )
    assert entry_1.status_code == 201

    # Conflict 1: Section Clash (Sec A already busy on Monday Period 1)
    clash_sec = await client.post(
        "/api/v1/academics/timetable",
        json={
            "course_offering_id": off_1,
            "section_id": sec_a,
            "academic_year_id": ay_id,
            "semester_id": sem_id,
            "time_slot_id": slot_id,
            "day_of_week": 1,
            "faculty_id": fac_y,
            "room_id": r2_id,
        },
    )
    assert clash_sec.status_code == 409
    assert "section is already scheduled" in clash_sec.json()["error"]["message"].lower()

    # Conflict 2: Faculty Clash (Fac X cannot teach Sec B while busy with Sec A)
    clash_fac = await client.post(
        "/api/v1/academics/timetable",
        json={
            "course_offering_id": off_2,
            "section_id": sec_b,
            "academic_year_id": ay_id,
            "semester_id": sem_id,
            "time_slot_id": slot_id,
            "day_of_week": 1,
            "faculty_id": fac_x,
            "room_id": r2_id,
        },
    )
    assert clash_fac.status_code == 409
    assert "instructor is already teaching" in clash_fac.json()["error"]["message"].lower()

    # Conflict 3: Room Clash (Room R1 cannot host Sec B while holding Sec A)
    clash_room = await client.post(
        "/api/v1/academics/timetable",
        json={
            "course_offering_id": off_2,
            "section_id": sec_b,
            "academic_year_id": ay_id,
            "semester_id": sem_id,
            "time_slot_id": slot_id,
            "day_of_week": 1,
            "faculty_id": fac_y,
            "room_id": r1_id,
        },
    )
    assert clash_room.status_code == 409
    assert "room is already booked" in clash_room.json()["error"]["message"].lower()

    # Success: Sec B, Fac Y, Room R2 -> No clashes
    valid_entry = await client.post(
        "/api/v1/academics/timetable",
        json={
            "course_offering_id": off_2,
            "section_id": sec_b,
            "academic_year_id": ay_id,
            "semester_id": sem_id,
            "time_slot_id": slot_id,
            "day_of_week": 1,
            "faculty_id": fac_y,
            "room_id": r2_id,
        },
    )
    assert valid_entry.status_code == 201


# =============================================================================
# 7. CROSS-TENANT ISOLATION
# =============================================================================
@pytest.mark.asyncio
async def test_cross_tenant_isolation_academics(
    client: AsyncClient,
    super_admin_user: User,
    tenant_a: Institution,
    tenant_b: Institution,
    db_session: AsyncSession,
) -> None:
    # 1. Login as Super Admin (Tenant A) and create a subject
    await authenticate_user(client, super_admin_user.email)
    dept_res = await client.post(
        "/api/v1/departments",
        json={"code": f"PHY_{uuid.uuid4().hex[:4].upper()}", "name": "Physics"},
    )
    dept_id = dept_res.json()["data"]["id"]

    sub_res = await client.post(
        "/api/v1/academics/subjects",
        json={
            "department_id": dept_id,
            "code": f"PH_{uuid.uuid4().hex[:3].upper()}",
            "name": "Engineering Physics",
            "credits": 3.0,
        },
    )
    sub_a_id = sub_res.json()["data"]["id"]

    # 2. Create User in Tenant B
    from app.core.security import get_password_hash
    from app.models.people import Role, UserRoleAssignment

    user_b = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_b.id,
        email=f"admin_b_{uuid.uuid4().hex[:5]}@beaconuni.edu",
        first_name="Admin",
        last_name="TenantB",
        password_hash=get_password_hash("SuperSecret123!"),
        status="ACTIVE",
    )
    db_session.add(user_b)
    await db_session.flush()

    role_res = await db_session.execute(select(Role).where(Role.name == "SUPER_ADMIN"))
    role = role_res.scalar_one_or_none()
    if role:
        db_session.add(
            UserRoleAssignment(
                id=uuid.uuid4(), tenant_id=tenant_b.id, user_id=user_b.id, role_id=role.id
            )
        )
    await db_session.commit()

    # 3. Authenticate as Tenant B User
    await authenticate_user(client, user_b.email)

    # 4. Attempt to fetch Tenant A's subject -> expect 404 Not Found
    cross_res = await client.get(f"/api/v1/academics/subjects/{sub_a_id}")
    assert cross_res.status_code == 404


# =============================================================================
# 8. PBAC PERMISSION ENFORCEMENT
# =============================================================================
@pytest.mark.asyncio
async def test_pbac_academic_permissions_enforcement(
    client: AsyncClient,
    faculty_user: User,
    tenant_a: Institution,
) -> None:
    # Login as Faculty user (lacks academics:subjects:manage permission)
    await authenticate_user(client, faculty_user.email, password="FacultyPass123!")

    # Attempt to create Subject (requires academics:subjects:manage) -> 403 Forbidden
    resp = await client.post(
        "/api/v1/academics/subjects",
        json={
            "department_id": str(uuid.uuid4()),
            "code": "ILLEGAL101",
            "name": "Unauthorized Course",
            "credits": 3.0,
        },
    )
    assert resp.status_code == 403
    assert "PERMISSION_DENIED" in resp.json()["error"]["code"]
