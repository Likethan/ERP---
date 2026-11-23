"""Automated security and identity test suite for CampusOS Authentication & RBAC."""

import uuid
from typing import Annotated

import pytest
from fastapi import APIRouter, Depends
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permission
from app.core.permissions import ACADEMICS_COURSES_READ, FINANCE_STRUCTURES_MANAGE
from app.core.security import get_password_hash
from app.main import app
from app.models.core import Institution
from app.models.people import User, UserSession

# Mount a temporary test router for verifying PBAC dependency enforcement
pbac_mock_router = APIRouter(prefix="/test-pbac", tags=["Test"])


@pbac_mock_router.get("/academics")
async def academics_pbac_view(
    user: Annotated[User, Depends(require_permission(ACADEMICS_COURSES_READ))],
) -> dict[str, str]:
    return {"status": "ok", "user_id": str(user.id)}


@pbac_mock_router.get("/finance")
async def finance_pbac_view(
    user: Annotated[User, Depends(require_permission(FINANCE_STRUCTURES_MANAGE))],
) -> dict[str, str]:
    return {"status": "ok", "user_id": str(user.id)}


app.include_router(pbac_mock_router)


@pytest.mark.asyncio
async def test_login_success(
    client: AsyncClient,
    super_admin_user: User,
    tenant_a: Institution,
) -> None:
    """Verify standard enterprise login returns safe user payload and HttpOnly cookies."""
    payload = {
        "email": super_admin_user.email,
        "password": "SuperSecret123!",
    }
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200

    body = response.json()
    assert body["success"] is True
    data = body["data"]

    # Verify user identity attributes
    assert data["id"] == str(super_admin_user.id)
    assert data["email"] == super_admin_user.email
    assert data["first_name"] == super_admin_user.first_name
    assert data["last_name"] == super_admin_user.last_name
    assert "SUPER_ADMIN" in [r["name"] for r in data["roles"]]
    assert len(data["permissions"]) > 0

    # Ensure tenant context is returned
    assert data["tenant"] is not None
    assert data["tenant"]["id"] == str(tenant_a.id)
    assert data["tenant"]["code"] == tenant_a.code

    # Critical security assertion: password hash must NEVER be present
    assert "password_hash" not in data
    assert "password" not in data
    assert "token" not in data  # Tokens are dispatched exclusively via HttpOnly cookies

    # Verify secure HttpOnly cookies set in response
    cookies = response.cookies
    assert "campusos_access_token" in cookies
    assert "campusos_refresh_token" in cookies


@pytest.mark.asyncio
async def test_login_invalid_password(
    client: AsyncClient,
    super_admin_user: User,
    db_session: AsyncSession,
) -> None:
    """Verify invalid password returns generic 401 and tracks failed attempts."""
    payload = {
        "email": super_admin_user.email,
        "password": "IncorrectPassword999!",
    }
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401

    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "AUTHENTICATION_FAILED"
    # Generic message prevents timing or account-discovery clues
    assert body["error"]["message"] == "Invalid email or password."

    # Verify failed attempt count incremented
    await db_session.refresh(super_admin_user)
    assert super_admin_user.failed_login_attempts >= 1


@pytest.mark.asyncio
async def test_login_unknown_user(client: AsyncClient) -> None:
    """Verify nonexistent email returns identical generic 401 error (no user enumeration)."""
    payload = {
        "email": "nonexistent.user@randomcollege.edu",
        "password": "SomePassword123!",
    }
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401

    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "AUTHENTICATION_FAILED"
    assert body["error"]["message"] == "Invalid email or password."


@pytest.mark.asyncio
async def test_login_lockout_after_consecutive_failures(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
) -> None:
    """Verify account is temporarily locked after 5 consecutive failed attempts."""
    victim_user = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email="lockout_target@apextech.edu",
        phone_number="+1555444333",
        password_hash=get_password_hash("ValidPass123!"),
        status="ACTIVE",
        first_name="Lockout",
        last_name="Target",
    )
    db_session.add(victim_user)
    await db_session.commit()

    # Submit 5 incorrect passwords
    for _ in range(5):
        res = await client.post(
            "/api/v1/auth/login",
            json={"email": victim_user.email, "password": "WrongPassword123!"},
        )
        assert res.status_code in (401, 403)

    # 6th attempt must be rejected with 403 ACCOUNT_LOCKED
    res6 = await client.post(
        "/api/v1/auth/login",
        json={"email": victim_user.email, "password": "ValidPass123!"},
    )
    assert res6.status_code == 403
    assert res6.json()["error"]["code"] == "ACCOUNT_LOCKED"


@pytest.mark.asyncio
async def test_login_disabled_user(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
) -> None:
    """Verify disabled account cannot authenticate."""
    disabled_user = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email="disabled_user@apextech.edu",
        phone_number="+1555999888",
        password_hash=get_password_hash("DisabledPass123!"),
        status="DISABLED",
        first_name="Disabled",
        last_name="Account",
    )
    db_session.add(disabled_user)
    await db_session.commit()

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": disabled_user.email, "password": "DisabledPass123!"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ACCOUNT_DISABLED"


@pytest.mark.asyncio
async def test_current_user_me_authenticated(
    client: AsyncClient,
    faculty_user: User,
    tenant_a: Institution,
) -> None:
    """Verify GET /api/v1/auth/me resolves identity, roles, permissions, and tenant."""
    # 1. Login to establish session cookies
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": faculty_user.email, "password": "FacultyPass123!"},
    )
    assert login_res.status_code == 200

    # 2. Call /api/v1/auth/me with cookies automatically passed
    me_res = await client.get("/api/v1/auth/me")
    assert me_res.status_code == 200

    data = me_res.json()["data"]
    assert data["id"] == str(faculty_user.id)
    assert data["email"] == faculty_user.email
    assert data["first_name"] == "Alan"
    assert data["last_name"] == "Turing"
    assert "FACULTY" in [r["name"] for r in data["roles"]]
    assert ACADEMICS_COURSES_READ in data["permissions"]
    assert data["tenant"]["id"] == str(tenant_a.id)


@pytest.mark.asyncio
async def test_current_user_me_unauthenticated(client: AsyncClient) -> None:
    """Verify unauthenticated request to /api/v1/auth/me returns 401."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_FAILED"


@pytest.mark.asyncio
async def test_logout(
    client: AsyncClient,
    faculty_user: User,
    db_session: AsyncSession,
) -> None:
    """Verify logout revokes user session and deletes auth cookies."""
    # 1. Login
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": faculty_user.email, "password": "FacultyPass123!"},
    )
    assert login_res.status_code == 200

    # 2. Logout
    logout_res = await client.post("/api/v1/auth/logout")
    assert logout_res.status_code == 200
    assert logout_res.json()["success"] is True

    # 3. Check session revocation in database
    sessions_res = await db_session.execute(
        select(UserSession).where(UserSession.user_id == faculty_user.id)
    )
    sessions = sessions_res.scalars().all()
    for s in sessions:
        assert s.is_revoked is True


@pytest.mark.asyncio
async def test_change_password_flow(
    client: AsyncClient,
    faculty_user: User,
) -> None:
    """Verify password change enforces current password and updates credentials."""
    # 1. Login
    await client.post(
        "/api/v1/auth/login",
        json={"email": faculty_user.email, "password": "FacultyPass123!"},
    )

    # 2. Change password
    change_res = await client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "FacultyPass123!",
            "new_password": "NewStrongPass456!",
            "confirm_password": "NewStrongPass456!",
        },
    )
    assert change_res.status_code == 200
    assert change_res.json()["success"] is True

    # 3. Old password should fail
    old_login = await client.post(
        "/api/v1/auth/login",
        json={"email": faculty_user.email, "password": "FacultyPass123!"},
    )
    assert old_login.status_code == 401

    # 4. New password should succeed
    new_login = await client.post(
        "/api/v1/auth/login",
        json={"email": faculty_user.email, "password": "NewStrongPass456!"},
    )
    assert new_login.status_code == 200


@pytest.mark.asyncio
async def test_change_password_invalid_current(
    client: AsyncClient,
    faculty_user: User,
) -> None:
    """Verify changing password fails when current password is wrong."""
    await client.post(
        "/api/v1/auth/login",
        json={"email": faculty_user.email, "password": "FacultyPass123!"},
    )

    change_res = await client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "WrongCurrentPass999!",
            "new_password": "AnotherPass789!",
            "confirm_password": "AnotherPass789!",
        },
    )
    assert change_res.status_code == 401
    assert change_res.json()["error"]["code"] == "AUTHENTICATION_FAILED"


@pytest.mark.asyncio
async def test_change_password_weak_policy_rejection(
    client: AsyncClient,
    faculty_user: User,
) -> None:
    """Verify password complexity policy rejects trivial or short passwords."""
    await client.post(
        "/api/v1/auth/login",
        json={"email": faculty_user.email, "password": "FacultyPass123!"},
    )

    change_res = await client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "FacultyPass123!",
            "new_password": "short",
            "confirm_password": "short",
        },
    )
    assert change_res.status_code in (400, 422)


@pytest.mark.asyncio
async def test_authorization_pbac_enforcement(
    client: AsyncClient,
    faculty_user: User,
    super_admin_user: User,
) -> None:
    """Verify require_permission allows authorized roles and returns 403 for unauthorized."""
    # 1. Login as Faculty User
    login_fac = await client.post(
        "/api/v1/auth/login",
        json={"email": faculty_user.email, "password": "FacultyPass123!"},
    )
    assert login_fac.status_code == 200

    # Faculty HAS 'academics:courses:read' -> 200
    res_academics = await client.get("/test-pbac/academics")
    assert res_academics.status_code == 200
    assert res_academics.json()["status"] == "ok"

    # Faculty DOES NOT HAVE 'finance:fee_structures:manage' -> 403 Forbidden
    res_finance = await client.get("/test-pbac/finance")
    assert res_finance.status_code == 403
    assert res_finance.json()["error"]["code"] == "PERMISSION_DENIED"

    # 2. Login as Super Admin (has all permissions)
    login_adm = await client.post(
        "/api/v1/auth/login",
        json={"email": super_admin_user.email, "password": "SuperSecret123!"},
    )
    assert login_adm.status_code == 200

    # Super Admin can access finance endpoint -> 200
    res_admin_finance = await client.get("/test-pbac/finance")
    assert res_admin_finance.status_code == 200
    assert res_admin_finance.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_tenant_isolation_boundary(
    client: AsyncClient,
    faculty_user: User,
    tenant_a: Institution,
    tenant_b: Institution,
) -> None:
    """Verify tenant isolation: authenticated session is strictly bound to user's tenant."""
    # Login as Faculty of Tenant A
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": faculty_user.email, "password": "FacultyPass123!"},
    )
    assert login_res.status_code == 200

    me_res = await client.get("/api/v1/auth/me")
    assert me_res.status_code == 200
    data = me_res.json()["data"]

    # Must resolve Tenant A, not Tenant B
    assert data["tenant"]["id"] == str(tenant_a.id)
    assert data["tenant"]["id"] != str(tenant_b.id)
