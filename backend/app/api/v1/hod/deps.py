"""HOD (Head of Department) Portal API endpoints.

Provides department-scoped access for Department Heads with strict RBAC enforcement.
Ensures HOD can only access records belonging to their assigned academic department.
"""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant import TenantContext
from app.models.core import Department
from app.models.people import User


async def get_hod_department(
    current_user: User,
    tenant: TenantContext,
    db: AsyncSession,
    department_id: UUID | None = None,
) -> Department:
    """Resolve the authenticated HOD's department strictly from trusted session/database context.

    Prevents unauthorized cross-department data tampering.
    """
    user_roles = {ur.role.name for ur in current_user.roles if ur.role and ur.role.name}
    is_super = any(r in user_roles for r in ["SUPER_ADMIN", "ADMIN", "VICE_PRINCIPAL", "PRINCIPAL"])
    is_hod = "HOD" in user_roles

    if not is_super and not is_hod:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authenticated user does not have an authorized HOD role.",
        )

    # 1. Check authoritative department assignment where user is HOD
    stmt = (
        select(Department)
        .where(
            Department.tenant_id == tenant.tenant_id,
            Department.hod_user_id == current_user.id,
            Department.is_active == True,  # noqa: E712
        )
    )
    assigned_dept = (await db.execute(stmt)).scalar_one_or_none()

    # 2. If supervisory user requested a specific department
    if is_super and department_id:
        stmt_req = select(Department).where(
            Department.tenant_id == tenant.tenant_id,
            Department.id == department_id,
            Department.is_active == True,  # noqa: E712
        )
        req_dept = (await db.execute(stmt_req)).scalar_one_or_none()
        if req_dept:
            return req_dept
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested department not found.",
        )

    # 3. If standard HOD tries to access another department
    if not is_super and department_id:
        if not assigned_dept:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Authenticated user is not assigned as Head of Department for any active department.",
            )
        if assigned_dept.id != department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="HOD cannot access another department's records.",
            )

    # 4. If assigned department exists, return it
    if assigned_dept:
        return assigned_dept

    # 5. If super admin has no assigned department and no department_id requested, allow first active academic dept
    if is_super:
        stmt_first = (
            select(Department)
            .where(
                Department.tenant_id == tenant.tenant_id,
                Department.department_type == "ACADEMIC",
                Department.is_active == True,  # noqa: E712
            )
            .limit(1)
        )
        super_first = (await db.execute(stmt_first)).scalar_one_or_none()
        if super_first:
            return super_first

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Authenticated user is not assigned as Head of Department for any active department.",
    )

