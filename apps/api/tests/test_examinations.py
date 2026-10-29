"""Comprehensive automated tests for CampusOS Step 7: Examination & Assessment Engine."""

import uuid
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.core import Institution
from app.models.people import Role, User, UserRoleAssignment


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


async def setup_academic_and_exam_environment(client: AsyncClient) -> dict[str, Any]:
    """Helper to initialize department, program, academic year, semester, section, subject, offering, and 2 enrolled students."""
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
            "semester_number": 5,
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
            "name": f"Batch 2024-2028 {uid}",
            "admission_year": 2024,
            "graduation_year": 2028,
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
            "name": "Compiler Design & Engineering",
            "credits": 4.0,
            "lecture_hours": 3,
            "tutorial_hours": 1,
            "practical_hours": 0,
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
            "first_name": "Niklaus",
            "last_name": "Wirth",
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
    students = []
    for i in range(1, 3):
        stu_email = f"stud{i}_{uid}@apextech.edu"
        stu_res = await client.post(
            "/api/v1/students",
            json={
                "email": stu_email,
                "admission_number": f"ADM_{uid}_{i}",
                "first_name": f"Student{i}",
                "last_name": "Candidate",
                "date_of_birth": "2004-04-12",
                "gender": "MALE" if i == 1 else "FEMALE",
                "admission_date": "2024-08-01",
                "expected_graduation_date": "2028-05-31",
                "program_id": prog_id,
                "batch_id": batch_id,
                "current_semester_id": sem_id,
                "current_section_id": sec_id,
                "roll_number": f"CS24{uid.upper()}{i:02d}",
            },
        )
        assert stu_res.status_code == 201
        student_data = stu_res.json()["data"]
        student_data["email"] = stu_email
        students.append(student_data)

        # Enroll in Course Offering
        enroll_res = await client.post(
            f"/api/v1/academics/course-offerings/{off_id}/students",
            json={"student_id": student_data["id"]},
        )
        assert enroll_res.status_code == 201

    return {
        "dept_id": dept_id,
        "prog_id": prog_id,
        "academic_year_id": ay_id,
        "semester_id": sem_id,
        "section_id": sec_id,
        "subject_id": subj_id,
        "course_offering_id": off_id,
        "faculty_id": fac_id,
        "students": students,
        "uid": uid,
    }


@pytest.mark.asyncio
async def test_grade_scale_creation_and_listing(
    client: AsyncClient, super_admin_user: User
):
    """Test creating and retrieving configurable academic grade scales."""
    await authenticate_user(client, super_admin_user.email)

    scale_res = await client.post(
        "/api/v1/examinations/grade-scales",
        json={
            "name": f"10-Point UGC Scale {uuid.uuid4().hex[:4]}",
            "description": "Standard university letter grading scale",
            "is_default": True,
            "items": [
                {"grade_letter": "O", "grade_point": 10.0, "min_mark_percent": 90.0, "max_mark_percent": 100.0, "is_passing": True},
                {"grade_letter": "A+", "grade_point": 9.0, "min_mark_percent": 80.0, "max_mark_percent": 89.99, "is_passing": True},
                {"grade_letter": "A", "grade_point": 8.0, "min_mark_percent": 70.0, "max_mark_percent": 79.99, "is_passing": True},
                {"grade_letter": "B+", "grade_point": 7.0, "min_mark_percent": 60.0, "max_mark_percent": 69.99, "is_passing": True},
                {"grade_letter": "B", "grade_point": 6.0, "min_mark_percent": 50.0, "max_mark_percent": 59.99, "is_passing": True},
                {"grade_letter": "C", "grade_point": 5.0, "min_mark_percent": 40.0, "max_mark_percent": 49.99, "is_passing": True},
                {"grade_letter": "F", "grade_point": 0.0, "min_mark_percent": 0.0, "max_mark_percent": 39.99, "is_passing": False},
            ],
        },
    )
    assert scale_res.status_code == 201
    scale_data = scale_res.json()["data"]
    assert scale_data["name"].startswith("10-Point UGC Scale")
    assert len(scale_data["items"]) == 7

    list_res = await client.get("/api/v1/examinations/grade-scales")
    assert list_res.status_code == 200
    scales = list_res.json()["data"]
    assert any(s["id"] == scale_data["id"] for s in scales)


@pytest.mark.asyncio
async def test_assessment_configuration_and_weightage_validation(
    client: AsyncClient, super_admin_user: User
):
    """Test assessment lifecycle and mathematical weightage validation (<= 100%)."""
    await authenticate_user(client, super_admin_user.email)
    env = await setup_academic_and_exam_environment(client)
    off_id = env["course_offering_id"]

    # 1. Create Internal Assessment 1 (20%)
    a1_res = await client.post(
        "/api/v1/examinations/assessments",
        json={
            "course_offering_id": off_id,
            "title": "Internal Assessment 1",
            "assessment_type": "INTERNAL",
            "sequence": 1,
            "max_marks": 50.0,
            "passing_marks": 20.0,
            "weightage_percent": 20.0,
        },
    )
    assert a1_res.status_code == 201
    a1_id = a1_res.json()["data"]["id"]

    # 2. Create Internal Assessment 2 (20%)
    a2_res = await client.post(
        "/api/v1/examinations/assessments",
        json={
            "course_offering_id": off_id,
            "title": "Internal Assessment 2",
            "assessment_type": "INTERNAL",
            "sequence": 2,
            "max_marks": 50.0,
            "passing_marks": 20.0,
            "weightage_percent": 20.0,
        },
    )
    assert a2_res.status_code == 201

    # 3. Create End Semester Exam (60%)
    a3_res = await client.post(
        "/api/v1/examinations/assessments",
        json={
            "course_offering_id": off_id,
            "title": "End Semester Examination",
            "assessment_type": "END_SEMESTER",
            "sequence": 3,
            "max_marks": 100.0,
            "passing_marks": 40.0,
            "weightage_percent": 60.0,
        },
    )
    assert a3_res.status_code == 201

    # 4. Check Course Assessment Structure (Total = 100%)
    struct_res = await client.get(f"/api/v1/examinations/course-offerings/{off_id}/structure")
    assert struct_res.status_code == 200
    struct_data = struct_res.json()["data"]
    assert float(struct_data["total_weightage_percent"]) == 100.0
    assert struct_data["is_weightage_valid"] is True
    assert len(struct_data["assessments"]) == 3

    # 5. Attempt to add a 4th assessment with 10% weightage -> cumulative 110% -> must be rejected
    overflow_res = await client.post(
        "/api/v1/examinations/assessments",
        json={
            "course_offering_id": off_id,
            "title": "Unexpected Extra Assignment",
            "assessment_type": "ASSIGNMENT",
            "sequence": 4,
            "max_marks": 20.0,
            "passing_marks": 8.0,
            "weightage_percent": 10.0,
        },
    )
    assert overflow_res.status_code in [400, 422]
    assert "exceeds 100%" in overflow_res.json()["error"]["message"].lower()


@pytest.mark.asyncio
async def test_exam_schedule_and_conflict_detection(
    client: AsyncClient, super_admin_user: User
):
    """Test examination scheduling and conflict detection (Room and Student simultaneous)."""
    await authenticate_user(client, super_admin_user.email)
    env = await setup_academic_and_exam_environment(client)
    off_id = env["course_offering_id"]

    # Create End Sem assessment
    a_res = await client.post(
        "/api/v1/examinations/assessments",
        json={
            "course_offering_id": off_id,
            "title": "End Semester Exam",
            "assessment_type": "END_SEMESTER",
            "sequence": 1,
            "max_marks": 100.0,
            "passing_marks": 40.0,
            "weightage_percent": 100.0,
        },
    )
    assert a_res.status_code == 201
    assessment_id = a_res.json()["data"]["id"]

    # 1. Schedule exam on 2026-11-20 09:30 to 12:30 in HALL-A
    sched_res = await client.post(
        "/api/v1/examinations/schedules",
        json={
            "assessment_id": assessment_id,
            "exam_date": "2026-11-20",
            "start_time": "09:30:00",
            "end_time": "12:30:00",
            "room_identifier": "HALL-A",
        },
    )
    assert sched_res.status_code == 201
    sched_id = sched_res.json()["data"]["id"]

    # 2. Test Dry-run conflict check for same room at overlapping time (10:00 - 11:30)
    conflict_check = await client.post(
        "/api/v1/examinations/schedules/check-conflict",
        json={
            "assessment_id": assessment_id,
            "exam_date": "2026-11-20",
            "start_time": "10:00:00",
            "end_time": "11:30:00",
            "room_identifier": "HALL-A",
        },
    )
    assert conflict_check.status_code == 200
    assert conflict_check.json()["data"]["has_conflict"] is True
    assert conflict_check.json()["data"]["conflict_type"] == "ROOM_CONFLICT"

    # 3. Create a second subject & offering with same enrolled student
    subj2_res = await client.post(
        "/api/v1/academics/subjects",
        json={
            "department_id": env["dept_id"],
            "code": f"MATH_{env['uid'].upper()}",
            "name": "Discrete Mathematics",
            "credits": 3.0,
            "lecture_hours": 3,
            "tutorial_hours": 0,
            "practical_hours": 0,
            "subject_type": "THEORY",
        },
    )
    subj2_id = subj2_res.json()["data"]["id"]

    off2_res = await client.post(
        "/api/v1/academics/course-offerings",
        json={
            "subject_id": subj2_id,
            "academic_year_id": env["academic_year_id"],
            "semester_id": env["semester_id"],
            "section_id": env["section_id"],
            "max_capacity": 60,
            "status": "ACTIVE",
        },
    )
    off2_id = off2_res.json()["data"]["id"]

    # Enroll student 1 into Course 2 as well
    await client.post(
        f"/api/v1/academics/course-offerings/{off2_id}/students",
        json={"student_id": env["students"][0]["id"]},
    )

    a2_res = await client.post(
        "/api/v1/examinations/assessments",
        json={
            "course_offering_id": off2_id,
            "title": "Math Final Exam",
            "assessment_type": "END_SEMESTER",
            "sequence": 1,
            "max_marks": 100.0,
            "passing_marks": 40.0,
            "weightage_percent": 100.0,
        },
    )
    a2_id = a2_res.json()["data"]["id"]

    # 4. Attempt to schedule Course 2 in a DIFFERENT room (HALL-B), but at the SAME TIME
    # Student 1 is in both courses -> STUDENT_CONFLICT must be triggered!
    student_conflict_res = await client.post(
        "/api/v1/examinations/schedules",
        json={
            "assessment_id": a2_id,
            "exam_date": "2026-11-20",
            "start_time": "09:30:00",
            "end_time": "12:30:00",
            "room_identifier": "HALL-B",
        },
    )
    assert student_conflict_res.status_code == 409
    assert "student" in student_conflict_res.json()["error"]["message"].lower()


@pytest.mark.asyncio
async def test_exam_eligibility_snapshot_and_override(
    client: AsyncClient, super_admin_user: User
):
    """Test evaluating student eligibility from Step 6 Attendance policy and applying audited overrides."""
    await authenticate_user(client, super_admin_user.email)
    env = await setup_academic_and_exam_environment(client)
    off_id = env["course_offering_id"]

    # Create Exam Term
    term_res = await client.post(
        "/api/v1/examinations/terms",
        json={
            "academic_year_id": env["academic_year_id"],
            "semester_id": env["semester_id"],
            "name": f"Semester Exams {env['uid']}",
            "exam_type": "END_SEMESTER",
            "start_date": "2026-11-15",
            "end_date": "2026-11-30",
        },
    )
    assert term_res.status_code == 201
    term_id = term_res.json()["data"]["id"]

    # Evaluate eligibility snapshot with a specified 75% attendance threshold
    eval_res = await client.post(
        f"/api/v1/examinations/course-offerings/{off_id}/eligibility/evaluate",
        json={
            "course_offering_id": off_id,
            "exam_term_id": term_id,
            "minimum_attendance_threshold": 75.0,
        },
    )
    assert eval_res.status_code == 200
    roster = eval_res.json()["data"]
    assert len(roster) == 2

    student1_elig = next(r for r in roster if r["student_id"] == env["students"][0]["id"])
    student2_elig = next(r for r in roster if r["student_id"] == env["students"][1]["id"])

    # Override student 2 eligibility with condonation
    override_res = await client.post(
        f"/api/v1/examinations/eligibility/{student2_elig['id']}/override",
        json={
            "eligibility_status": "ELIGIBLE",
            "override_reason": "Medical certificate approved by Principal and HOD",
        },
    )
    assert override_res.status_code == 200
    updated_elig = override_res.json()["data"]
    assert updated_elig["eligibility_status"] == "ELIGIBLE"
    assert updated_elig["is_overridden"] is True
    assert "Medical certificate" in updated_elig["override_reason"]


@pytest.mark.asyncio
async def test_bulk_marks_entry_validation_and_corrections(
    client: AsyncClient, super_admin_user: User
):
    """Test bulk marks entry, validation limits, finalization locking, and audited correction workflow."""
    await authenticate_user(client, super_admin_user.email)
    env = await setup_academic_and_exam_environment(client)
    off_id = env["course_offering_id"]

    # Create assessment
    a_res = await client.post(
        "/api/v1/examinations/assessments",
        json={
            "course_offering_id": off_id,
            "title": "Midterm Examination",
            "assessment_type": "MIDTERM",
            "sequence": 1,
            "max_marks": 50.0,
            "passing_marks": 20.0,
            "weightage_percent": 50.0,
        },
    )
    assert a_res.status_code == 201
    assessment_id = a_res.json()["data"]["id"]

    # 1. Validation test: Submit marks exceeding max_marks (55 / 50)
    invalid_marks = await client.post(
        f"/api/v1/examinations/assessments/{assessment_id}/marks/bulk",
        json={
            "marks": [
                {"student_id": env["students"][0]["id"], "marks_obtained": 55.0, "status": "PRESENT"},
            ],
            "finalize": False,
        },
    )
    assert invalid_marks.status_code in [400, 422]
    assert "outside valid range" in invalid_marks.json()["error"]["message"].lower()

    # 2. Valid marks bulk entry: Student 1 has 42/50, Student 2 is ABSENT
    valid_submit = await client.post(
        f"/api/v1/examinations/assessments/{assessment_id}/marks/bulk",
        json={
            "marks": [
                {"student_id": env["students"][0]["id"], "marks_obtained": 42.0, "status": "PRESENT"},
                {"student_id": env["students"][1]["id"], "marks_obtained": None, "status": "ABSENT"},
            ],
            "finalize": True,  # Lock marks
        },
    )
    assert valid_submit.status_code == 200
    roster_data = valid_submit.json()["data"]
    assert roster_data["total_students"] == 2
    assert roster_data["total_entered"] == 2
    assert roster_data["total_absent"] == 1
    assert float(roster_data["average_marks"]) == 42.0

    student1_mark = next(m for m in roster_data["roster"] if m["student_id"] == env["students"][0]["id"])
    assert student1_mark["is_finalized"] is True

    # 3. Attempt direct edit on finalized mark -> must be rejected
    rejected_edit = await client.post(
        f"/api/v1/examinations/assessments/{assessment_id}/marks/bulk",
        json={
            "marks": [
                {"student_id": env["students"][0]["id"], "marks_obtained": 45.0, "status": "PRESENT"},
            ],
        },
    )
    assert rejected_edit.status_code in [400, 409]
    assert "locked" in rejected_edit.json()["error"]["message"].lower()

    # 4. Supervised Mark Correction Workflow: Request correction from 42 to 45
    correction_req = await client.post(
        "/api/v1/examinations/marks/corrections",
        json={
            "mark_id": student1_mark["id"],
            "new_marks": 45.0,
            "new_status": "PRESENT",
            "reason": "Recounting verified by examination committee",
        },
    )
    assert correction_req.status_code == 201
    correction_id = correction_req.json()["data"]["id"]
    assert correction_req.json()["data"]["approval_status"] == "PENDING"

    # 5. Approve correction
    approval_res = await client.post(
        f"/api/v1/examinations/marks/corrections/{correction_id}/approve",
        json={"approval_notes": "Recount verified and approved by Dean"},
    )
    assert approval_res.status_code == 200
    assert approval_res.json()["data"]["approval_status"] == "APPROVED"

    # Verify the mark was atomically updated
    refreshed_roster = await client.get(f"/api/v1/examinations/assessments/{assessment_id}/marks")
    assert refreshed_roster.status_code == 200
    refreshed_mark = next(
        m for m in refreshed_roster.json()["data"]["roster"]
        if m["student_id"] == env["students"][0]["id"]
    )
    assert float(refreshed_mark["marks_obtained"]) == 45.0


@pytest.mark.asyncio
async def test_results_calculation_publication_and_student_privacy(
    client: AsyncClient, super_admin_user: User, db_session: AsyncSession
):
    """Test full cycle: Assessment -> Marks -> Results Finalization -> Student Privacy -> Publication."""
    await authenticate_user(client, super_admin_user.email)
    env = await setup_academic_and_exam_environment(client)
    off_id = env["course_offering_id"]

    # Create Exam Term
    term_res = await client.post(
        "/api/v1/examinations/terms",
        json={
            "academic_year_id": env["academic_year_id"],
            "semester_id": env["semester_id"],
            "name": f"Term Exams {env['uid']}",
            "exam_type": "END_SEMESTER",
            "start_date": "2026-11-01",
            "end_date": "2026-11-30",
        },
    )
    term_id = term_res.json()["data"]["id"]

    # Create Assessment (100% weightage for simplicity)
    a_res = await client.post(
        "/api/v1/examinations/assessments",
        json={
            "course_offering_id": off_id,
            "exam_term_id": term_id,
            "title": "Final Examination",
            "assessment_type": "END_SEMESTER",
            "sequence": 1,
            "max_marks": 100.0,
            "passing_marks": 40.0,
            "weightage_percent": 100.0,
        },
    )
    assessment_id = a_res.json()["data"]["id"]

    # Submit marks: Student 1 gets 85 (Grade A+ or O), Student 2 gets 35 (Grade F)
    await client.post(
        f"/api/v1/examinations/assessments/{assessment_id}/marks/bulk",
        json={
            "marks": [
                {"student_id": env["students"][0]["id"], "marks_obtained": 85.0, "status": "PRESENT"},
                {"student_id": env["students"][1]["id"], "marks_obtained": 35.0, "status": "PRESENT"},
            ],
            "finalize": True,
        },
    )

    # 1. Finalize Course Results (creates results in FINALIZED/unpublished status)
    fin_res = await client.post(
        "/api/v1/examinations/results/finalize",
        json={
            "course_offering_id": off_id,
            "exam_term_id": term_id,
        },
    )
    assert fin_res.status_code == 200
    results = fin_res.json()["data"]
    assert len(results) == 2

    res1 = next(r for r in results if r["student_id"] == env["students"][0]["id"])
    res2 = next(r for r in results if r["student_id"] == env["students"][1]["id"])
    assert float(res1["total_marks"]) == 85.0
    assert res1["result_status"] == "PASS"
    assert res1["publication_status"] == "FINALIZED"
    assert float(res2["total_marks"]) == 35.0
    assert res2["result_status"] == "FAIL"

    # 2. Authenticate as Student 1 (Account automatically provisioned during student admission)
    await authenticate_user(client, env["students"][0]["email"], "Welcome@123")

    # 3. PRIVACY CHECK: Before publication, student MUST NOT see any results!
    student_res_before = await client.get("/api/v1/examinations/results")
    assert student_res_before.status_code == 200
    assert len(student_res_before.json()["data"]) == 0, "Student saw unpublished results!"

    # 4. Authenticate back as Admin and PUBLISH results
    await authenticate_user(client, super_admin_user.email)
    pub_res = await client.post(
        "/api/v1/examinations/results/publish",
        json={"exam_term_id": term_id, "course_offering_id": off_id},
    )
    assert pub_res.status_code == 200
    assert pub_res.json()["data"]["published_count"] == 2

    # 5. Authenticate again as Student 1: Now the published result must be visible
    await authenticate_user(client, env["students"][0]["email"], "Welcome@123")
    student_res_after = await client.get("/api/v1/examinations/results")
    assert student_res_after.status_code == 200
    my_results = student_res_after.json()["data"]
    assert len(my_results) == 1
    assert my_results[0]["student_id"] == env["students"][0]["id"]
    assert my_results[0]["publication_status"] == "PUBLISHED"
    assert float(my_results[0]["total_marks"]) == 85.0

    # 6. Check student transcript endpoint
    transcript_res = await client.get(
        f"/api/v1/examinations/students/{env['students'][0]['id']}/transcript?exam_term_id={term_id}"
    )
    assert transcript_res.status_code == 200
    transcript_data = transcript_res.json()["data"]
    assert transcript_data["student_id"] == env["students"][0]["id"]
    assert len(transcript_data["results"]) == 1
    assert float(transcript_data["total_credits_earned"]) > 0

    # 7. Student attempts to access Student 2's transcript -> 403 Forbidden!
    forbidden_transcript = await client.get(
        f"/api/v1/examinations/students/{env['students'][1]['id']}/transcript?exam_term_id={term_id}"
    )
    assert forbidden_transcript.status_code == 403


@pytest.mark.asyncio
async def test_tenant_isolation_examinations(
    client: AsyncClient,
    super_admin_user: User,
    tenant_b: Institution,
    db_session: AsyncSession,
):
    """Verify strict tenant isolation across all examination records and operations."""
    # 1. Create resources in Tenant A
    await authenticate_user(client, super_admin_user.email)
    env = await setup_academic_and_exam_environment(client)
    off_id = env["course_offering_id"]

    a_res = await client.post(
        "/api/v1/examinations/assessments",
        json={
            "course_offering_id": off_id,
            "title": "Tenant A Secret Assessment",
            "assessment_type": "INTERNAL",
            "sequence": 1,
            "max_marks": 50.0,
            "passing_marks": 20.0,
            "weightage_percent": 100.0,
        },
    )
    assert a_res.status_code == 201
    assessment_id = a_res.json()["data"]["id"]

    # 2. Create an admin user for Tenant B
    tenant_b_admin = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_b.id,
        email=f"admin_b_{uuid.uuid4().hex[:5]}@beaconuni.edu",
        phone_number="+919876543299",
        password_hash=get_password_hash("SuperSecret123!"),
        status="ACTIVE",
        first_name="Beacon",
        last_name="Admin",
    )
    db_session.add(tenant_b_admin)
    await db_session.flush()

    role_res = await db_session.execute(select(Role).where(Role.name == "SUPER_ADMIN"))
    role = role_res.scalar_one()
    db_session.add(
        UserRoleAssignment(
            id=uuid.uuid4(),
            tenant_id=tenant_b.id,
            user_id=tenant_b_admin.id,
            role_id=role.id,
        )
    )
    await db_session.commit()

    # 3. Authenticate as Tenant B Admin
    await authenticate_user(client, tenant_b_admin.email, "SuperSecret123!")

    # Tenant B Admin attempts to access Tenant A assessment -> 404 Not Found!
    t_b_get = await client.get(f"/api/v1/examinations/assessments/{assessment_id}")
    assert t_b_get.status_code == 404

    # Tenant B Admin attempts to submit marks to Tenant A assessment -> 404 Not Found!
    t_b_marks = await client.post(
        f"/api/v1/examinations/assessments/{assessment_id}/marks/bulk",
        json={
            "marks": [{"student_id": env["students"][0]["id"], "marks_obtained": 40.0, "status": "PRESENT"}],
        },
    )
    assert t_b_marks.status_code == 404
