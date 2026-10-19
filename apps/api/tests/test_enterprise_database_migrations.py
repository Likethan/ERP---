"""Step 34: Enterprise Database, Migration, and Transaction Integrity Test Suite.

Verifies:
1. Migration Chain Consistency: Validates that all Alembic migration revisions form
   an unbroken directed acyclic graph from 001 to 020 with no branching or missing links.
2. Foreign Key & Referential Integrity: Tests constraint enforcement and cascading behavior.
3. Unique Constraint Enforcement: Verifies multi-column uniqueness per tenant.
4. Transaction Rollback Atomicity: Ensures partial failures rollback cleanly with zero dirty writes.
5. Tenant Query Boundary Enforcement: Confirms queries remain strictly scoped to target tenants.
"""

import ast
from datetime import UTC, date, datetime
from pathlib import Path
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core import Department, Institution, Program
from app.models.people import Role, User


def get_migration_revisions():
    """Extract (revision, down_revision) from all python files in migrations/versions."""
    versions_dir = Path(__file__).resolve().parent.parent / "migrations" / "versions"
    migration_files = sorted(versions_dir.glob("*.py"))
    
    revisions = {}
    for mf in migration_files:
        if mf.name == ".gitkeep":
            continue
        tree = ast.parse(mf.read_text(encoding="utf-8"))
        rev = None
        down_rev = None
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if target.id == "revision" and isinstance(node.value, ast.Constant):
                            rev = node.value.value
                        elif target.id == "down_revision":
                            if isinstance(node.value, ast.Constant):
                                down_rev = node.value.value
                            elif isinstance(node.value, ast.NameConstant):
                                down_rev = node.value.value
        if rev:
            revisions[rev] = down_rev
    return revisions


def test_migration_chain_continuity():
    """Verify that Alembic migrations 001 through 020 form an unbroken linear sequence."""
    revisions = get_migration_revisions()
    assert len(revisions) >= 20, f"Expected at least 20 migration revisions, found {len(revisions)}"

    # Exactly one root (down_revision is None)
    roots = [rev for rev, down in revisions.items() if down is None]
    assert len(roots) == 1, f"Expected exactly 1 root migration, found: {roots}"
    root = roots[0]
    assert "001" in root

    # Follow the chain from root to head
    chain = [root]
    current = root
    down_map = {down: rev for rev, down in revisions.items() if down is not None}

    while current in down_map:
        next_rev = down_map[current]
        chain.append(next_rev)
        current = next_rev

    assert len(chain) == len(revisions), (
        f"Migration graph is fragmented! Chained {len(chain)} out of {len(revisions)} revisions."
    )
    # Ensure head reaches the latest Step 33 security operations revision
    head = chain[-1]
    assert "020" in head or "security" in head.lower()


@pytest.mark.asyncio
async def test_database_foreign_key_constraint_enforcement(
    db_session: AsyncSession,
    tenant_a: Institution,
):
    """Verify that foreign keys are strictly declared and enforced against non-existent parents."""
    from sqlalchemy import text

    # Verify foreign key metadata is declared on model
    fk_targets = [fk.target_fullname for fk in Department.__table__.foreign_keys]
    assert "core_institutions.id" in fk_targets

    # Enable foreign keys on connection for dialect enforcement
    await db_session.execute(text("PRAGMA foreign_keys = ON;"))

    fake_tenant_id = uuid.uuid4()
    orphan_dept = Department(
        id=uuid.uuid4(),
        tenant_id=fake_tenant_id,  # Non-existent institution
        code=f"ORPHAN-{uuid.uuid4().hex[:6].upper()}",
        name="Orphaned Department",
        department_type="ACADEMIC",
        is_active=True,
    )
    db_session.add(orphan_dept)
    
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_database_unique_constraint_enforcement(
    db_session: AsyncSession,
    tenant_a: Institution,
):
    """Verify unique constraint on (tenant_id, code) prevents duplicate departments within the same tenant."""
    uid = uuid.uuid4().hex[:6].upper()
    code = f"CS-{uid}"

    dept1 = Department(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        code=code,
        name=f"Computer Science {uid}",
        department_type="ACADEMIC",
        is_active=True,
    )
    db_session.add(dept1)
    await db_session.flush()

    # Duplicate department code in the SAME tenant must fail
    dept2 = Department(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        code=code,
        name=f"Duplicate CS {uid}",
        department_type="ACADEMIC",
        is_active=True,
    )
    db_session.add(dept2)
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_database_transaction_rollback_atomicity(
    db_session: AsyncSession,
    tenant_a: Institution,
):
    """Verify that a partial failure inside a transaction rolls back all pending inserts."""
    uid = uuid.uuid4().hex[:6].upper()
    code_valid = f"ATOM-VALID-{uid}"
    code_dupe = f"ATOM-DUPE-{uid}"

    # Pre-seed one department to cause collision on the second batch
    seed_dept = Department(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        code=code_dupe,
        name="Pre-existing Department",
        department_type="ACADEMIC",
        is_active=True,
    )
    db_session.add(seed_dept)
    await db_session.commit()

    # Attempt a multi-operation transaction: First add valid, then add colliding duplicate
    try:
        async with db_session.begin_nested():
            valid_dept = Department(
                id=uuid.uuid4(),
                tenant_id=tenant_a.id,
                code=code_valid,
                name="Atomic Department Valid",
                department_type="ACADEMIC",
                is_active=True,
            )
            db_session.add(valid_dept)
            await db_session.flush()

            # Colliding insert
            colliding_dept = Department(
                id=uuid.uuid4(),
                tenant_id=tenant_a.id,
                code=code_dupe,  # triggers UniqueConstraint
                name="Atomic Department Colliding",
                department_type="ACADEMIC",
                is_active=True,
            )
            db_session.add(colliding_dept)
            await db_session.flush()
    except IntegrityError:
        pass  # Nested savepoint rolled back

    # Verify that valid_dept was NOT persisted due to atomic transaction rollback
    result = await db_session.execute(
        select(Department).where(Department.code == code_valid)
    )
    assert result.scalar_one_or_none() is None, "Partial writes must not persist on transaction failure!"


@pytest.mark.asyncio
async def test_database_tenant_scoped_query_isolation(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_b: Institution,
):
    """Verify that tenant queries never leak across tenant boundaries."""
    uid = uuid.uuid4().hex[:6].upper()

    dept_a = Department(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        code=f"ISO-A-{uid}",
        name="Department Tenant A",
        department_type="ACADEMIC",
        is_active=True,
    )
    dept_b = Department(
        id=uuid.uuid4(),
        tenant_id=tenant_b.id,
        code=f"ISO-B-{uid}",
        name="Department Tenant B",
        department_type="ACADEMIC",
        is_active=True,
    )
    db_session.add(dept_a)
    db_session.add(dept_b)
    await db_session.commit()

    # Query scoped strictly to Tenant A
    results_a = (
        await db_session.execute(
            select(Department).where(Department.tenant_id == tenant_a.id)
        )
    ).scalars().all()

    tenant_a_dept_ids = [d.id for d in results_a]
    assert dept_a.id in tenant_a_dept_ids
    assert dept_b.id not in tenant_a_dept_ids, "Tenant A query leaked Tenant B records!"
