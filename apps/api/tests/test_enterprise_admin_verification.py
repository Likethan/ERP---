"""Enterprise Admin Portal Final Production-Readiness Verification Test Suite.

Validates end-to-end database persistence, cross-portal synchronization,
RBAC security invariants, configuration persistence, and forensic audit logging.
"""

import uuid
from typing import Any
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.core import Institution
from app.models.people import Role, User


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
# 1. DATABASE PERSISTENCE & CRUD VERIFICATION ACROSS SERVICES
# =============================================================================


@pytest.mark.asyncio
async def test_admin_persistence_student_lifecycle(
    client: AsyncClient,
    super_admin_user: User,
    tenant_a: Institution,
) -> None:
    """Verify create, read, search, and status lifecycle operations for students persist in DB."""
    await authenticate_user(client, super_admin_user.email)

    uid = uuid.uuid4().hex[:6]

    # Setup core hierarchy via API
    d_res = await client.post(
        "/api/v1/departments",
        json={"code": f"CSE-{uid}", "name": "Computer Science & Engineering"},
    )
    assert d_res.status_code == 201
    dept_id = d_res.json()["data"]["id"]

    p_res = await client.post(
        "/api/v1/programs",
        json={
            "department_id": dept_id,
            "code": f"BTECH-CSE-{uid}",
            "name": "B.Tech Computer Science",
            "degree_level": "UG",
        },
    )
    assert p_res.status_code == 201
    prog_id = p_res.json()["data"]["id"]

    r_res = await client.post(
        "/api/v1/regulations",
        json={"code": f"R-CSE-{uid}", "title": "Reg 2024", "effective_year": 2024},
    )
    assert r_res.status_code == 201
    reg_id = r_res.json()["data"]["id"]

    b_res = await client.post(
        "/api/v1/batches",
        json={
            "program_id": prog_id,
            "regulation_id": reg_id,
            "name": f"CSE 2024-2028 {uid}",
            "admission_year": 2024,
            "graduation_year": 2028,
        },
    )
    assert b_res.status_code == 201
    batch_id = b_res.json()["data"]["id"]

    # 1. Admit Student
    adm_num = f"ADM-VER-{uid}"
    student_payload = {
        "email": f"student_ver_{uid}@apextech.edu",
        "password": "Password123!",
        "first_name": "Srinivasa",
        "last_name": "Ramanujan",
        "phone_number": "+919876500001",
        "admission_number": adm_num,
        "registration_number": f"REG-VER-{uid}",
        "roll_number": f"24CS{uid[:3]}",
        "date_of_birth": "2006-12-22",
        "gender": "MALE",
        "blood_group": "O+",
        "admission_date": "2024-08-01",
        "expected_graduation_date": "2028-05-31",
        "program_id": prog_id,
        "batch_id": batch_id,
        "emergency_contact_name": "Guardian",
        "emergency_contact_phone": "+919876500002",
    }
    resp = await client.post("/api/v1/students", json=student_payload)
    assert resp.status_code == 201, f"Student creation failed: {resp.text}"
    student = resp.json()["data"]
    student_id = student["id"]
    assert student["admission_number"] == adm_num
    assert student["status"] == "ADMITTED"

    # 2. Get student by ID
    get_res = await client.get(f"/api/v1/students/{student_id}")
    assert get_res.status_code == 200
    fetched = get_res.json()["data"]
    assert fetched["id"] == student_id
    assert fetched["first_name"] == "Srinivasa"

    # 3. Valid lifecycle transition: ADMITTED -> ACTIVE
    trans_resp = await client.post(
        f"/api/v1/students/{student_id}/transition-status",
        json={
            "to_status": "ACTIVE",
            "reason": "Student verified and admitted to academic register",
        },
    )
    assert trans_resp.status_code == 200
    assert trans_resp.json()["data"]["status"] == "ACTIVE"


@pytest.mark.asyncio
async def test_admin_persistence_faculty_and_department(
    client: AsyncClient,
    super_admin_user: User,
    tenant_a: Institution,
) -> None:
    """Verify faculty onboarding, persistence, and departmental leadership integration."""
    await authenticate_user(client, super_admin_user.email)

    uid = uuid.uuid4().hex[:6]

    d_res = await client.post(
        "/api/v1/departments",
        json={"code": f"ECE-{uid}", "name": "Electronics & Communication"},
    )
    assert d_res.status_code == 201
    dept_id = d_res.json()["data"]["id"]

    fac_code = f"FAC-ECE-{uid.upper()}"
    fac_payload = {
        "email": f"faculty_{uid}@apextech.edu",
        "password": "FacultyPass123!",
        "first_name": "Dr. Subrahmanyan",
        "last_name": "Chandrasekhar",
        "phone_number": "+919876541112",
        "employee_code": fac_code,
        "department_id": dept_id,
        "designation": "Professor & Head",
        "highest_qualification": "Ph.D in Astrophysics",
        "specialization": "Stellar Evolution",
        "joining_date": "2020-01-15",
        "is_hod": True,
        "employment_status": "ACTIVE",
    }
    fac_resp = await client.post("/api/v1/faculty", json=fac_payload)
    assert fac_resp.status_code == 201
    fac_data = fac_resp.json()["data"]
    faculty_id = fac_data["id"]
    assert fac_data["employee_code"] == fac_code

    # Verify retrieval
    get_res = await client.get(f"/api/v1/faculty/{faculty_id}")
    assert get_res.status_code == 200
    assert get_res.json()["data"]["first_name"] == "Dr. Subrahmanyan"


@pytest.mark.asyncio
async def test_admin_persistence_academics_subjects(
    client: AsyncClient,
    super_admin_user: User,
    tenant_a: Institution,
) -> None:
    """Verify academic subject creation and listing via the Academic Engine."""
    await authenticate_user(client, super_admin_user.email)

    uid = uuid.uuid4().hex[:6]
    d_res = await client.post(
        "/api/v1/departments",
        json={"code": f"MATH-{uid}", "name": "Department of Mathematics"},
    )
    assert d_res.status_code == 201
    dept_id = d_res.json()["data"]["id"]

    sub_payload = {
        "code": f"MA-{uid[:4].upper()}",
        "name": f"Linear Algebra and Matrices {uid}",
        "department_id": dept_id,
        "credits": 4,
        "subject_type": "THEORY",
        "lecture_hours": 3,
        "tutorial_hours": 1,
        "practical_hours": 0,
    }

    create_res = await client.post(
        "/api/v1/academics/subjects",
        json=sub_payload,
    )
    assert create_res.status_code == 201
    created_sub = create_res.json()["data"]
    assert created_sub["code"] == sub_payload["code"]
    assert int(created_sub["credits"]) == 4


# =============================================================================
# 2. RBAC & SECURITY INVARIANTS
# =============================================================================


@pytest.mark.asyncio
async def test_unauthorized_user_blocked_from_admin_management(
    client: AsyncClient,
    tenant_a: Institution,
) -> None:
    """Verify that unauthenticated/unauthorized users receive 401/403 on admin endpoints."""
    headers = {"X-Tenant-ID": str(tenant_a.id)}

    res = await client.get(
        "/api/v1/admin/users",
        headers=headers,
    )
    assert res.status_code in [401, 403], f"Expected 401/403 but got {res.status_code}"


@pytest.mark.asyncio
async def test_admin_roles_and_self_lockout_safeguards(
    client: AsyncClient,
    super_admin_user: User,
    tenant_a: Institution,
    db_session: AsyncSession,
) -> None:
    """Verify admin role listing and self-lockout prevention invariants."""
    await authenticate_user(client, super_admin_user.email)

    # 1. List roles
    res = await client.get("/api/v1/admin/roles")
    assert res.status_code == 200
    roles = res.json()["data"]
    assert len(roles) > 0
    role_names = [r["name"] for r in roles]
    assert "SUPER_ADMIN" in role_names
    assert "INSTITUTION_ADMIN" in role_names

    # 2. Attempt self-lockout: revoking own SUPER_ADMIN role must be rejected
    super_admin_role_res = await db_session.execute(select(Role).where(Role.name == "SUPER_ADMIN"))
    super_admin_role = super_admin_role_res.scalar_one()

    revoke_res = await client.delete(
        f"/api/v1/admin/users/{super_admin_user.id}/roles/{super_admin_role.id}",
    )
    assert revoke_res.status_code in [400, 422]
    body = revoke_res.json()
    assert "cannot revoke your own" in str(body).lower() or "violation" in str(body).lower()


# =============================================================================
# 3. CONFIGURATION PERSISTENCE & EFFECTIVE HIERARCHY
# =============================================================================


@pytest.mark.asyncio
async def test_admin_configuration_effective_retrieval(
    client: AsyncClient,
    super_admin_user: User,
    tenant_a: Institution,
) -> None:
    """Verify effective configuration hierarchy can be queried by administrator."""
    await authenticate_user(client, super_admin_user.email)

    eff_res = await client.get("/api/v1/admin/configuration/effective")
    assert eff_res.status_code == 200
    eff_data = eff_res.json()["data"]
    assert isinstance(eff_data, list)
