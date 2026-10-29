import asyncio
import uuid
from collections.abc import AsyncGenerator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, delete
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.ext.compiler import compiles

import app.models  # noqa: F401 - Register all models
from app.core.database import get_db_session
from app.core.security import get_password_hash
from app.core.seeds import seed_system_permissions_and_roles
from app.main import app
from app.models.base import Base
from app.models.core import Institution, TenantMembership
from app.models.people import Role, User, UserRoleAssignment


# Configure SQLite compatibility for PostgreSQL specific types during unit tests
@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_: Any, compiler: Any, **kw: Any) -> str:
    return "JSON"


@compiles(PG_UUID, "sqlite")
def compile_uuid_sqlite(type_: Any, compiler: Any, **kw: Any) -> str:
    return "CHAR(36)"


# Async SQLite engine for isolated test execution
test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    echo=False,
    future=True,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


@pytest.fixture(scope="session", autouse=True)
def event_loop():
    """Create event loop for test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_test_database():
    """Create tables and seed system roles/permissions once for the test suite."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        await seed_system_permissions_and_roles(session)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
async def cleanup_outbox_events():
    """Ensure outbox table is cleaned up after each test to prevent cross-test batch pollution."""
    yield
    async with TestingSessionLocal() as session:
        try:
            from app.models.workflow import OutboxEvent
            await session.execute(delete(OutboxEvent))
            await session.commit()
        except Exception:
            pass



@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional database session for tests."""
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP test client with overridden database dependency."""
    async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
        cookies={},
        follow_redirects=True,
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def tenant_a(db_session: AsyncSession) -> Institution:
    """Create Institution Tenant A."""
    uid = uuid.uuid4().hex[:6]
    inst = Institution(
        id=uuid.uuid4(),
        code=f"INST-A-{uid}",
        slug=f"apex-tech-{uid}",
        legal_name=f"Apex Institute of Technology {uid}",
        short_name="Apex Tech",
        status="ACTIVE",
        plan="ENTERPRISE",
        contact_email=f"admin_{uid}@apextech.edu",
        contact_phone="+919876543210",
        address_line1="123 Tech Campus Way",
        city="Coimbatore",
        state="Tamil Nadu",
        postal_code="641001",
        default_timezone="Asia/Kolkata",
        currency_code="INR",
        locale="en-IN",
        is_active=True,
    )
    db_session.add(inst)
    await db_session.commit()
    await db_session.refresh(inst)
    return inst


@pytest.fixture
async def tenant_b(db_session: AsyncSession) -> Institution:
    """Create Institution Tenant B for cross-tenant isolation testing."""
    uid = uuid.uuid4().hex[:6]
    inst = Institution(
        id=uuid.uuid4(),
        code=f"INST-B-{uid}",
        slug=f"beacon-uni-{uid}",
        legal_name=f"Beacon University {uid}",
        short_name="Beacon Uni",
        status="ACTIVE",
        plan="ENTERPRISE",
        contact_email=f"admin_{uid}@beaconuni.edu",
        contact_phone="+919876543211",
        address_line1="456 Knowledge Park",
        city="Chennai",
        state="Tamil Nadu",
        postal_code="600001",
        default_timezone="Asia/Kolkata",
        currency_code="INR",
        locale="en-IN",
        is_active=True,
    )
    db_session.add(inst)
    await db_session.commit()
    await db_session.refresh(inst)
    return inst


@pytest.fixture
async def super_admin_user(db_session: AsyncSession, tenant_a: Institution) -> User:
    """Create a SUPER_ADMIN user in Tenant A."""
    uid = uuid.uuid4().hex[:6]
    user = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"superadmin_{uid}@campusos.internal",
        phone_number="+1234567890",
        password_hash=get_password_hash("SuperSecret123!"),
        status="ACTIVE",
        first_name="Root",
        last_name="Administrator",
    )
    db_session.add(user)
    await db_session.flush()

    # Assign SUPER_ADMIN role
    role_res = await db_session.execute(select(Role).where(Role.name == "SUPER_ADMIN"))
    role = role_res.scalar_one_or_none()

    if role:
        assignment = UserRoleAssignment(
            id=uuid.uuid4(),
            tenant_id=tenant_a.id,
            user_id=user.id,
            role_id=role.id,
        )
        db_session.add(assignment)

    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def faculty_user(db_session: AsyncSession, tenant_a: Institution) -> User:
    """Create a FACULTY user in Tenant A."""
    uid = uuid.uuid4().hex[:6]
    user = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"faculty_{uid}@apextech.edu",
        phone_number="+1987654321",
        password_hash=get_password_hash("FacultyPass123!"),
        status="ACTIVE",
        first_name="Alan",
        last_name="Turing",
    )
    db_session.add(user)
    await db_session.flush()

    # Assign FACULTY role
    role_res = await db_session.execute(select(Role).where(Role.name == "FACULTY"))
    role = role_res.scalar_one_or_none()

    if role:
        assignment = UserRoleAssignment(
            id=uuid.uuid4(),
            tenant_id=tenant_a.id,
            user_id=user.id,
            role_id=role.id,
        )
        db_session.add(assignment)

    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def tenant_admin_a(db_session: AsyncSession, tenant_a: Institution) -> User:
    """Create an INSTITUTION_ADMIN for Tenant A."""
    uid = uuid.uuid4().hex[:6]
    user = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"admin_{uid}@apextech.edu",
        phone_number="+919876543201",
        password_hash=get_password_hash("AdminPass123!"),
        status="ACTIVE",
        first_name="Admin",
        last_name="Alpha",
    )
    db_session.add(user)
    await db_session.flush()

    mem = TenantMembership(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        user_id=user.id,
        status="ACTIVE",
        role_scope="INSTITUTION_ADMIN",
    )
    db_session.add(mem)

    role_res = await db_session.execute(select(Role).where(Role.name == "INSTITUTION_ADMIN"))
    role = role_res.scalar_one_or_none()
    if role:
        db_session.add(
            UserRoleAssignment(
                id=uuid.uuid4(),
                tenant_id=tenant_a.id,
                user_id=user.id,
                role_id=role.id,
            )
        )
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def tenant_admin_b(db_session: AsyncSession, tenant_b: Institution) -> User:
    """Create an INSTITUTION_ADMIN for Tenant B."""
    uid = uuid.uuid4().hex[:6]
    user = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_b.id,
        email=f"admin_{uid}@beaconuni.edu",
        phone_number="+919876543202",
        password_hash=get_password_hash("AdminPass123!"),
        status="ACTIVE",
        first_name="Admin",
        last_name="Bravo",
    )
    db_session.add(user)
    await db_session.flush()

    mem = TenantMembership(
        id=uuid.uuid4(),
        tenant_id=tenant_b.id,
        user_id=user.id,
        status="ACTIVE",
        role_scope="INSTITUTION_ADMIN",
    )
    db_session.add(mem)

    role_res = await db_session.execute(select(Role).where(Role.name == "INSTITUTION_ADMIN"))
    role = role_res.scalar_one_or_none()
    if role:
        db_session.add(
            UserRoleAssignment(
                id=uuid.uuid4(),
                tenant_id=tenant_b.id,
                user_id=user.id,
                role_id=role.id,
            )
        )
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def user_b(db_session: AsyncSession, tenant_b: Institution) -> User:
    """Create a standard user belonging to Tenant B."""
    uid = uuid.uuid4().hex[:6]
    user = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_b.id,
        email=f"user_{uid}@beaconuni.edu",
        phone_number="+919876543203",
        password_hash=get_password_hash("UserPass123!"),
        status="ACTIVE",
        first_name="Bob",
        last_name="Bravo",
    )
    db_session.add(user)
    await db_session.flush()

    mem = TenantMembership(
        id=uuid.uuid4(),
        tenant_id=tenant_b.id,
        user_id=user.id,
        status="ACTIVE",
        role_scope="STUDENT",
    )
    db_session.add(mem)

    role_res = await db_session.execute(select(Role).where(Role.name == "STUDENT"))
    role = role_res.scalar_one_or_none()
    if role:
        db_session.add(
            UserRoleAssignment(
                id=uuid.uuid4(),
                tenant_id=tenant_b.id,
                user_id=user.id,
                role_id=role.id,
            )
        )
    await db_session.commit()
    await db_session.refresh(user)
    return user
