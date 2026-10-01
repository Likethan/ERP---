"""Comprehensive automated tests for Core Institution & People Management."""

import uuid
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core import Campus, Institution
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
# 1. INSTITUTIONS
# =============================================================================


@pytest.mark.asyncio
async def test_get_and_update_institution(
    client: AsyncClient,
    super_admin_user: User,
    tenant_a: Institution,
) -> None:
    await authenticate_user(client, super_admin_user.email)

    # 1. Get institution
    resp = await client.get("/api/v1/institutions")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["id"] == str(tenant_a.id)
    assert data["code"] == tenant_a.code

    # 2. Update institution metadata
    update_payload = {
        "legal_name": "Apex Premier University of Technology",
        "city": "Coimbatore Metropolitan",
        "website": "https://apextech.edu",
    }
    resp = await client.patch(f"/api/v1/institutions/{tenant_a.id}", json=update_payload)
    assert resp.status_code == 200
    updated = resp.json()["data"]
    assert updated["legal_name"] == "Apex Premier University of Technology"
    assert updated["city"] == "Coimbatore Metropolitan"


# =============================================================================
# 2. CAMPUSES & TENANT ISOLATION
# =============================================================================


@pytest.mark.asyncio
async def test_campus_crud_and_conflict(
    client: AsyncClient,
    super_admin_user: User,
    tenant_a: Institution,
) -> None:
    await authenticate_user(client, super_admin_user.email)

    code = f"CMP-{uuid.uuid4().hex[:4].upper()}"
    payload = {
        "code": code,
        "name": "Main Tech Campus",
        "address": "123 Academic Blvd",
        "city": "Coimbatore",
    }

    # 1. Create Campus
    resp = await client.post("/api/v1/campuses", json=payload)
    assert resp.status_code == 201
    campus_data = resp.json()["data"]
    campus_id = campus_data["id"]
    assert campus_data["code"] == code
    assert campus_data["name"] == "Main Tech Campus"

    # 2. Duplicate code conflict within tenant
    dup_resp = await client.post("/api/v1/campuses", json=payload)
    assert dup_resp.status_code == 409
    assert dup_resp.json()["error"]["code"] == "RESOURCE_CONFLICT"

    # 3. List campuses
    list_resp = await client.get("/api/v1/campuses")
    assert list_resp.status_code == 200
    items = list_resp.json()["data"]
    assert any(c["id"] == campus_id for c in items)

    # 4. Update campus
    update_resp = await client.patch(
        f"/api/v1/campuses/{campus_id}",
        json={"name": "Apex Central Tech Campus"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["name"] == "Apex Central Tech Campus"


# =============================================================================
# 3. DEPARTMENTS & PROGRAMS
# =============================================================================


@pytest.mark.asyncio
async def test_department_and_program_hierarchy(
    client: AsyncClient,
    super_admin_user: User,
    tenant_a: Institution,
) -> None:
    await authenticate_user(client, super_admin_user.email)

    dept_code = f"CSE-{uuid.uuid4().hex[:4].upper()}"
    dept_payload = {
        "code": dept_code,
        "name": "Computer Science & Engineering",
        "department_type": "ACADEMIC",
    }

    # 1. Create Department
    resp = await client.post("/api/v1/departments", json=dept_payload)
    assert resp.status_code == 201
    dept_data = resp.json()["data"]
    dept_id = dept_data["id"]

    # 2. Duplicate department code conflict
    dup_resp = await client.post("/api/v1/departments", json=dept_payload)
    assert dup_resp.status_code == 409

    # 3. Create Program under Department
    prog_code = f"BE-CSE-{uuid.uuid4().hex[:4].upper()}"
    prog_payload = {
        "department_id": dept_id,
        "code": prog_code,
        "name": "B.E. Computer Science and Engineering",
        "degree_level": "UG",
        "duration_years": "4.0",
        "total_semesters": 8,
        "required_credits": 160,
    }
    prog_resp = await client.post("/api/v1/programs", json=prog_payload)
    assert prog_resp.status_code == 201
    prog_data = prog_resp.json()["data"]
    assert prog_data["id"]
    assert prog_data["code"] == prog_code
    assert prog_data["department_id"] == dept_id

    # 4. Duplicate program code rejection
    prog_dup = await client.post("/api/v1/programs", json=prog_payload)
    assert prog_dup.status_code == 409


# =============================================================================
# 4. ACADEMIC STRUCTURE: REGULATIONS, YEARS, SEMESTERS, BATCHES, SECTIONS
# =============================================================================


@pytest.mark.asyncio
async def test_academic_structure_flow(
    client: AsyncClient,
    super_admin_user: User,
    tenant_a: Institution,
) -> None:
    await authenticate_user(client, super_admin_user.email)

    uid = uuid.uuid4().hex[:4].upper()

    # 1. Create Department & Program first
    d_resp = await client.post(
        "/api/v1/departments",
        json={"code": f"IT-{uid}", "name": "Information Technology"},
    )
    dept_id = d_resp.json()["data"]["id"]

    p_resp = await client.post(
        "/api/v1/programs",
        json={
            "department_id": dept_id,
            "code": f"BTECH-IT-{uid}",
            "name": "B.Tech Information Technology",
            "degree_level": "UG",
        },
    )
    prog_id = p_resp.json()["data"]["id"]

    # 2. Create Regulation
    reg_resp = await client.post(
        "/api/v1/regulations",
        json={
            "code": f"R2025-{uid}",
            "title": f"Autonomous Regulation 2025 {uid}",
            "effective_year": 2025,
        },
    )
    assert reg_resp.status_code == 201
    reg_id = reg_resp.json()["data"]["id"]

    # 3. Create Academic Year
    ay_resp = await client.post(
        "/api/v1/academic-years",
        json={
            "name": f"2025-2026-{uid}",
            "start_date": "2025-06-01",
            "end_date": "2026-05-31",
            "is_current": True,
        },
    )
    assert ay_resp.status_code == 201
    ay_id = ay_resp.json()["data"]["id"]

    # 4. Create Semester
    sem_resp = await client.post(
        "/api/v1/semesters",
        json={
            "academic_year_id": ay_id,
            "name": f"Odd Term 2025-{uid}",
            "semester_number": 1,
            "term_type": "ODD",
            "start_date": "2025-07-01",
            "end_date": "2025-11-30",
            "is_active": True,
        },
    )
    assert sem_resp.status_code == 201
    sem_id = sem_resp.json()["data"]["id"]

    # 5. Create Batch
    batch_resp = await client.post(
        "/api/v1/batches",
        json={
            "program_id": prog_id,
            "regulation_id": reg_id,
            "name": f"IT Batch 2025-2029 {uid}",
            "admission_year": 2025,
            "graduation_year": 2029,
        },
    )
    assert batch_resp.status_code == 201
    batch_id = batch_resp.json()["data"]["id"]

    # 6. Create Section
    sec_resp = await client.post(
        "/api/v1/sections",
        json={
            "program_id": prog_id,
            "batch_id": batch_id,
            "semester_id": sem_id,
            "name": "A",
            "capacity": 60,
        },
    )
    assert sec_resp.status_code == 201
    assert sec_resp.json()["data"]["name"] == "A"


# =============================================================================
# 5. STUDENTS: ADMISSION, SEARCH, UPDATE & LIFECYCLE TRANSITIONS
# =============================================================================


@pytest.mark.asyncio
async def test_student_lifecycle_and_search(
    client: AsyncClient,
    super_admin_user: User,
    tenant_a: Institution,
) -> None:
    await authenticate_user(client, super_admin_user.email)

    uid = uuid.uuid4().hex[:6]

    # Setup core hierarchy
    d_res = await client.post(
        "/api/v1/departments",
        json={"code": f"MECH-{uid}", "name": "Mechanical Engineering"},
    )
    dept_id = d_res.json()["data"]["id"]

    p_res = await client.post(
        "/api/v1/programs",
        json={
            "department_id": dept_id,
            "code": f"BE-MECH-{uid}",
            "name": "B.E. Mechanical Engineering",
            "degree_level": "UG",
        },
    )
    prog_id = p_res.json()["data"]["id"]

    r_res = await client.post(
        "/api/v1/regulations",
        json={"code": f"R-MECH-{uid}", "title": "Reg Mech", "effective_year": 2024},
    )
    reg_id = r_res.json()["data"]["id"]

    b_res = await client.post(
        "/api/v1/batches",
        json={
            "program_id": prog_id,
            "regulation_id": reg_id,
            "name": f"MECH 2024-2028 {uid}",
            "admission_year": 2024,
            "graduation_year": 2028,
        },
    )
    batch_id = b_res.json()["data"]["id"]

    # 1. Admit Student
    adm_num = f"ADM-2024-{uid}"
    student_payload = {
        "email": f"student_{uid}@apextech.edu",
        "password": "Password123!",
        "first_name": "Srinivasa",
        "last_name": "Ramanujan",
        "phone_number": "+919876500001",
        "admission_number": adm_num,
        "registration_number": f"REG-{uid}",
        "roll_number": "24ME001",
        "date_of_birth": "2006-12-22",
        "gender": "MALE",
        "blood_group": "O+",
        "admission_date": "2024-08-01",
        "expected_graduation_date": "2028-05-31",
        "program_id": prog_id,
        "batch_id": batch_id,
        "emergency_contact_name": "Komalathammal",
        "emergency_contact_phone": "+919876500002",
    }
    resp = await client.post("/api/v1/students", json=student_payload)
    assert resp.status_code == 201
    student = resp.json()["data"]
    student_id = student["id"]
    assert student["admission_number"] == adm_num
    assert student["status"] == "ADMITTED"
    assert len(student["status_history"]) >= 1

    # 2. Reject duplicate admission number
    dup_resp = await client.post("/api/v1/students", json=student_payload)
    assert dup_resp.status_code == 409
    assert dup_resp.json()["error"]["code"] == "RESOURCE_CONFLICT"

    # 3. Search students
    search_resp = await client.get("/api/v1/students", params={"search": "Ramanujan"})
    assert search_resp.status_code == 200
    search_data = search_resp.json()
    assert search_data["pagination"]["total_records"] >= 1
    assert any(s["id"] == student_id for s in search_data["data"])

    # 4. Valid lifecycle transition: ADMITTED -> ACTIVE
    trans_resp = await client.post(
        f"/api/v1/students/{student_id}/transition-status",
        json={
            "to_status": "ACTIVE",
            "reason": "Student completed document verification and reported to campus",
        },
    )
    assert trans_resp.status_code == 200
    assert trans_resp.json()["data"]["status"] == "ACTIVE"
    assert len(trans_resp.json()["data"]["status_history"]) == 2

    # 5. Invalid lifecycle transition: ACTIVE cannot jump directly to ALUMNI
    invalid_trans = await client.post(
        f"/api/v1/students/{student_id}/transition-status",
        json={"to_status": "ALUMNI", "reason": "Illegal transition test"},
    )
    assert invalid_trans.status_code == 422
    assert "Cannot transition student" in invalid_trans.json()["error"]["message"]


# =============================================================================
# 6. FACULTY & STAFF ONBOARDING
# =============================================================================


@pytest.mark.asyncio
async def test_faculty_and_staff_onboarding(
    client: AsyncClient,
    super_admin_user: User,
    tenant_a: Institution,
) -> None:
    await authenticate_user(client, super_admin_user.email)

    uid = uuid.uuid4().hex[:6]

    d_res = await client.post(
        "/api/v1/departments",
        json={"code": f"PHYS-{uid}", "name": "Department of Physics"},
    )
    dept_id = d_res.json()["data"]["id"]

    # 1. Onboard Faculty
    fac_code = f"FAC-{uid.upper()}"
    fac_payload = {
        "email": f"faculty_{uid}@apextech.edu",
        "password": "FacultyPass123!",
        "first_name": "C. V.",
        "last_name": "Raman",
        "phone_number": "+919876541111",
        "employee_code": fac_code,
        "department_id": dept_id,
        "designation": "Professor & Head",
        "highest_qualification": "Ph.D in Physics",
        "specialization": "Optics and Quantum Scattering",
        "joining_date": "2020-01-15",
        "is_hod": True,
        "employment_status": "ACTIVE",
    }
    fac_resp = await client.post("/api/v1/faculty", json=fac_payload)
    assert fac_resp.status_code == 201
    fac_data = fac_resp.json()["data"]
    assert fac_data["employee_code"] == fac_code
    assert fac_data["designation"] == "Professor & Head"

    # Duplicate employee code rejection
    dup_fac = await client.post("/api/v1/faculty", json=fac_payload)
    assert dup_fac.status_code == 409

    # 2. Onboard Staff
    staff_code = f"STF-{uid.upper()}"
    staff_payload = {
        "email": f"staff_{uid}@apextech.edu",
        "password": "StaffPass123!",
        "first_name": "Subramanian",
        "last_name": "Chandrasekhar",
        "phone_number": "+919876542222",
        "employee_code": staff_code,
        "department_id": dept_id,
        "designation": "Senior Laboratory Technologist",
        "employment_type": "FULL_TIME",
        "is_active": True,
    }
    staff_resp = await client.post("/api/v1/staff", json=staff_payload)
    assert staff_resp.status_code == 201
    staff_data = staff_resp.json()["data"]
    assert staff_data["employee_code"] == staff_code


# =============================================================================
# 7. TENANT ISOLATION TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_cross_tenant_isolation(
    client: AsyncClient,
    db_session: AsyncSession,
    super_admin_user: User,
    tenant_a: Institution,
    tenant_b: Institution,
) -> None:
    """Ensure Tenant A user cannot read or mutate Tenant B records."""
    # 1. Create a campus belonging to Tenant B directly in DB
    b_campus = Campus(
        id=uuid.uuid4(),
        tenant_id=tenant_b.id,
        code=f"CMP-B-{uuid.uuid4().hex[:4].upper()}",
        name="Beacon Chennai Campus",
        address="789 Marine Drive",
        city="Chennai",
        is_active=True,
    )
    db_session.add(b_campus)
    await db_session.commit()

    # 2. Login as Tenant A user
    await authenticate_user(client, super_admin_user.email)

    # 3. Attempt to fetch Tenant B's campus through Tenant A session
    resp = await client.get(f"/api/v1/campuses/{b_campus.id}")
    # Must return 404 NOT FOUND, completely hiding Tenant B's record!
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


# =============================================================================
# 8. PBAC AUTHORIZATION ENFORCEMENT
# =============================================================================


@pytest.mark.asyncio
async def test_pbac_permission_denial(
    client: AsyncClient,
    faculty_user: User,
    tenant_a: Institution,
) -> None:
    """Ensure a user lacking manage permission cannot modify institution settings."""
    await authenticate_user(client, faculty_user.email, password="FacultyPass123!")

    # Faculty lacks `core:institutions:manage`
    resp = await client.patch(
        f"/api/v1/institutions/{tenant_a.id}",
        json={"legal_name": "Unauthorized Attempt"},
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "PERMISSION_DENIED"
    assert "core:institutions:manage" in resp.json()["error"]["message"]
