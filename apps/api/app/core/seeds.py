"""System seed routine for standard roles, permissions, and initial mappings."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.core.permissions import ALL_PERMISSIONS, DEFAULT_ROLE_PERMISSIONS
from app.models.people import Permission, Role, RolePermission


async def seed_system_permissions_and_roles(db: AsyncSession) -> None:
    """Seed standard system permissions, roles, and default mappings idempotently."""
    logger.info("Verifying system permissions and roles...")

    # 1. Seed Permissions
    existing_perms_res = await db.execute(select(Permission))
    existing_perms = {p.code: p for p in existing_perms_res.scalars().all()}

    now = datetime.now(UTC)
    for perm_def in ALL_PERMISSIONS:
        if perm_def.code not in existing_perms:
            new_perm = Permission(
                id=uuid4(),
                code=perm_def.code,
                domain=perm_def.domain,
                description=perm_def.description,
                created_at=now,
            )
            db.add(new_perm)
            existing_perms[perm_def.code] = new_perm

    await db.flush()

    # 2. Seed System Roles
    existing_roles_res = await db.execute(select(Role).where(Role.is_system.is_(True)))
    existing_roles = {r.name: r for r in existing_roles_res.scalars().all()}

    for role_name, perm_codes in DEFAULT_ROLE_PERMISSIONS.items():
        if role_name not in existing_roles:
            role = Role(
                id=uuid4(),
                tenant_id=None,  # System roles are global templates
                name=role_name,
                display_name=role_name.replace("_", " ").title(),
                description=f"Standard institutional role for {role_name}.",
                is_system=True,
            )
            db.add(role)
            await db.flush()
            existing_roles[role_name] = role

        role = existing_roles[role_name]

        # 3. Seed Role-Permission Mappings
        existing_rp_res = await db.execute(
            select(RolePermission).where(RolePermission.role_id == role.id)
        )
        existing_rp_set = {rp.permission_id for rp in existing_rp_res.scalars().all()}

        for p_code in perm_codes:
            perm_obj = existing_perms.get(p_code)
            if perm_obj and perm_obj.id not in existing_rp_set:
                db.add(
                    RolePermission(
                        role_id=role.id,
                        permission_id=perm_obj.id,
                    )
                )

    await db.commit()
    logger.info("System permissions and roles synchronized successfully.")
