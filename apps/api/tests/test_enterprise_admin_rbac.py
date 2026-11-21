"""Test Suite for Admin User & Role Management (RBAC)."""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import ACCESS_TOKEN_COOKIE_NAME, create_access_token
from app.models.core import Institution
from app.models.people import Role, User, UserRoleAssignment


@pytest.fixture
def super_admin_auth_cookie(super_admin_user: User, tenant_a: Institution) -> dict[str, str]:
    """Generate auth token cookie for super admin user."""
    token = create_access_token(
        user_id=super_admin_user.id,
        tenant_id=tenant_a.id,
        email=super_admin_user.email,
        roles=["SUPER_ADMIN"],
        permissions=["*"],
    )
    return {ACCESS_TOKEN_COOKIE_NAME: token}


@pytest.mark.asyncio
async def test_list_admin_roles(
    client: AsyncClient,
    super_admin_auth_cookie: dict[str, str],
    tenant_a: Institution,
):
    """Test retrieving system and tenant roles."""
    headers = {"X-Tenant-ID": str(tenant_a.id)}
    res = await client.get(
        "/api/v1/admin/roles",
        headers=headers,
        cookies=super_admin_auth_cookie,
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data) > 0
    role_names = [r["name"] for r in data]
    assert "SUPER_ADMIN" in role_names
    assert "INSTITUTION_ADMIN" in role_names
    assert "FACULTY" in role_names
    assert "STUDENT" in role_names


@pytest.mark.asyncio
async def test_list_admin_users(
    client: AsyncClient,
    super_admin_auth_cookie: dict[str, str],
    tenant_a: Institution,
    super_admin_user: User,
):
    """Test listing users within the active tenant."""
    headers = {"X-Tenant-ID": str(tenant_a.id)}
    res = await client.get(
        "/api/v1/admin/users",
        headers=headers,
        cookies=super_admin_auth_cookie,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    users = body["data"]
    assert len(users) >= 1
    user_emails = [u["email"] for u in users]
    assert super_admin_user.email in user_emails


@pytest.mark.asyncio
async def test_create_user_and_assign_role(
    client: AsyncClient,
    db_session: AsyncSession,
    super_admin_auth_cookie: dict[str, str],
    tenant_a: Institution,
):
    """Test creating a new user and assigning an additional role."""
    headers = {"X-Tenant-ID": str(tenant_a.id)}

    # Fetch a role ID
    role_res = await db_session.execute(select(Role).where(Role.name == "FACULTY"))
    faculty_role = role_res.scalar_one()

    uid = uuid.uuid4().hex[:6]
    payload = {
        "email": f"prof_{uid}@apextech.edu",
        "password": "Password123!",
        "first_name": "Test",
        "last_name": "Faculty",
        "phone_number": "+919876543210",
        "role_id": str(faculty_role.id),
    }

    create_res = await client.post(
        "/api/v1/admin/users",
        json=payload,
        headers=headers,
        cookies=super_admin_auth_cookie,
    )
    assert create_res.status_code == 201
    user_data = create_res.json()["data"]
    user_id = user_data["id"]
    assert user_data["email"] == payload["email"]
    assert len(user_data["roles"]) == 1
    assert user_data["roles"][0]["role_name"] == "FACULTY"

    # Assign an additional HOD role
    hod_role_res = await db_session.execute(select(Role).where(Role.name == "HOD"))
    hod_role = hod_role_res.scalar_one()

    assign_res = await client.post(
        f"/api/v1/admin/users/{user_id}/roles",
        json={"role_id": str(hod_role.id)},
        headers=headers,
        cookies=super_admin_auth_cookie,
    )
    assert assign_res.status_code == 200
    updated_user = assign_res.json()["data"]
    assigned_roles = [r["role_name"] for r in updated_user["roles"]]
    assert "FACULTY" in assigned_roles
    assert "HOD" in assigned_roles

    # Revoke HOD role
    revoke_res = await client.delete(
        f"/api/v1/admin/users/{user_id}/roles/{hod_role.id}",
        headers=headers,
        cookies=super_admin_auth_cookie,
    )
    assert revoke_res.status_code == 200
    revoked_user = revoke_res.json()["data"]
    remaining_roles = [r["role_name"] for r in revoked_user["roles"]]
    assert "HOD" not in remaining_roles
    assert "FACULTY" in remaining_roles


@pytest.mark.asyncio
async def test_self_lockout_safeguard(
    client: AsyncClient,
    db_session: AsyncSession,
    super_admin_auth_cookie: dict[str, str],
    super_admin_user: User,
    tenant_a: Institution,
):
    """Test that a super admin cannot revoke their own SUPER_ADMIN role."""
    headers = {"X-Tenant-ID": str(tenant_a.id)}

    super_admin_role_res = await db_session.execute(select(Role).where(Role.name == "SUPER_ADMIN"))
    super_admin_role = super_admin_role_res.scalar_one()

    # Attempt to revoke own SUPER_ADMIN role
    res = await client.delete(
        f"/api/v1/admin/users/{super_admin_user.id}/roles/{super_admin_role.id}",
        headers=headers,
        cookies=super_admin_auth_cookie,
    )
    assert res.status_code in [400, 422]
    body = res.json()
    assert "cannot revoke your own" in str(body).lower() or "violation" in str(body).lower()


@pytest.mark.asyncio
async def test_self_deactivation_safeguard(
    client: AsyncClient,
    super_admin_auth_cookie: dict[str, str],
    super_admin_user: User,
    tenant_a: Institution,
):
    """Test that an administrator cannot deactivate their own account."""
    headers = {"X-Tenant-ID": str(tenant_a.id)}

    res = await client.patch(
        f"/api/v1/admin/users/{super_admin_user.id}/status",
        json={"status": "SUSPENDED", "reason": "Accidental self-lockout test"},
        headers=headers,
        cookies=super_admin_auth_cookie,
    )
    assert res.status_code in [400, 422]
    body = res.json()
    assert "cannot deactivate" in str(body).lower() or "violation" in str(body).lower()
