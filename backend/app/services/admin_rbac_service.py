"""Enterprise Admin RBAC & User Management Service."""

from math import ceil
from uuid import UUID, uuid4

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.core.security import get_password_hash
from app.models.people import Role, RolePermission, User, UserRoleAssignment
from app.schemas.admin_rbac import (
    AdminRoleAssignRequest,
    AdminRoleResponse,
    AdminUserCreateRequest,
    AdminUserResponse,
    AdminUserRoleInfo,
    AdminUserStatusUpdateRequest,
)
from app.schemas.common import PaginatedMeta


class AdminRbacService:
    @staticmethod
    async def list_roles(db: AsyncSession, tenant_id: UUID) -> list[AdminRoleResponse]:
        """List all system and tenant-specific roles with assigned permissions."""
        stmt = (
            select(Role)
            .where(or_(Role.tenant_id == tenant_id, Role.tenant_id.is_(None)))
            .options(
                selectinload(Role.permissions).selectinload(RolePermission.permission)
            )
            .order_by(Role.is_system.desc(), Role.name.asc())
        )
        res = await db.execute(stmt)
        roles = res.scalars().all()

        results = []
        for r in roles:
            perm_codes = [
                rp.permission.code
                for rp in (r.permissions or [])
                if rp.permission
            ]
            results.append(
                AdminRoleResponse(
                    id=r.id,
                    name=r.name,
                    display_name=r.display_name,
                    description=r.description,
                    is_system=r.is_system,
                    permissions_count=len(perm_codes),
                    permissions=perm_codes,
                )
            )
        return results

    @staticmethod
    async def list_users(
        db: AsyncSession,
        tenant_id: UUID,
        page: int = 1,
        page_size: int = 25,
        search: str | None = None,
        role_name: str | None = None,
        status: str | None = None,
    ) -> tuple[list[AdminUserResponse], PaginatedMeta]:
        """List institutional users with assigned roles, scoped by tenant."""
        query = select(User).options(
            selectinload(User.roles).selectinload(UserRoleAssignment.role)
        )

        # Tenant filter: users belonging to this tenant
        conditions = [
            or_(
                User.primary_tenant_id == tenant_id,
                User.roles.any(UserRoleAssignment.tenant_id == tenant_id),
            )
        ]

        if search:
            s = f"%{search.strip().lower()}%"
            conditions.append(
                or_(
                    func.lower(User.email).like(s),
                    func.lower(User.first_name).like(s),
                    func.lower(User.last_name).like(s),
                )
            )

        if status and status != "ALL":
            conditions.append(User.status == status)

        if role_name and role_name != "ALL":
            conditions.append(
                User.roles.any(
                    and_(
                        UserRoleAssignment.tenant_id == tenant_id,
                        UserRoleAssignment.role.has(Role.name == role_name),
                    )
                )
            )

        query = query.where(and_(*conditions))

        # Count total
        count_stmt = select(func.count(User.id)).where(and_(*conditions))
        total_res = await db.execute(count_stmt)
        total_records = total_res.scalar_one() or 0

        # Paginate
        offset = (page - 1) * page_size
        query = query.order_by(User.created_at.desc()).offset(offset).limit(page_size)

        res = await db.execute(query)
        users = res.scalars().all()

        results = []
        for u in users:
            role_infos = []
            for ura in (u.roles or []):
                if ura.tenant_id == tenant_id and ura.role:
                    role_infos.append(
                        AdminUserRoleInfo(
                            id=ura.id,
                            role_id=ura.role.id,
                            role_name=ura.role.name,
                            display_name=ura.role.display_name,
                            campus_id=ura.campus_id,
                            department_id=ura.department_id,
                        )
                    )
            results.append(
                AdminUserResponse(
                    id=u.id,
                    email=u.email,
                    first_name=u.first_name,
                    last_name=u.last_name,
                    phone_number=u.phone_number,
                    status=u.status,
                    roles=role_infos,
                    created_at=u.created_at,
                    updated_at=u.updated_at,
                )
            )

        total_pages = ceil(total_records / page_size) if total_records > 0 else 1
        meta = PaginatedMeta(
            page=page,
            page_size=page_size,
            total_records=total_records,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )
        return results, meta

    @staticmethod
    async def create_user(
        db: AsyncSession,
        tenant_id: UUID,
        payload: AdminUserCreateRequest,
        actor_id: UUID,
    ) -> AdminUserResponse:
        """Create a new user account with initial role assignment."""
        # Check email uniqueness
        existing_res = await db.execute(select(User).where(User.email == payload.email))
        if existing_res.scalar_one_or_none():
            raise ConflictException(f"User with email '{payload.email}' already exists.")

        user = User(
            id=uuid4(),
            primary_tenant_id=tenant_id,
            email=payload.email,
            password_hash=get_password_hash(payload.password),
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone_number=payload.phone_number,
            status="ACTIVE",
            is_active=True,
        )
        db.add(user)
        await db.flush()

        role_infos = []
        if payload.role_id:
            role_res = await db.execute(select(Role).where(Role.id == payload.role_id))
            role = role_res.scalar_one_or_none()
            if not role:
                raise NotFoundException("Role", payload.role_id)

            ura = UserRoleAssignment(
                id=uuid4(),
                tenant_id=tenant_id,
                user_id=user.id,
                role_id=role.id,
                campus_id=payload.campus_id,
                department_id=payload.department_id,
            )
            db.add(ura)
            await db.flush()
            role_infos.append(
                AdminUserRoleInfo(
                    id=ura.id,
                    role_id=role.id,
                    role_name=role.name,
                    display_name=role.display_name,
                    campus_id=ura.campus_id,
                    department_id=ura.department_id,
                )
            )

        await db.commit()
        await db.refresh(user)

        return AdminUserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            phone_number=user.phone_number,
            status=user.status,
            roles=role_infos,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    @staticmethod
    async def assign_role(
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        payload: AdminRoleAssignRequest,
        actor_id: UUID,
    ) -> AdminUserResponse:
        """Assign an institutional role to a user."""
        user_res = await db.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.roles).selectinload(UserRoleAssignment.role))
        )
        user = user_res.scalar_one_or_none()
        if not user:
            raise NotFoundException("User", user_id)

        role_res = await db.execute(select(Role).where(Role.id == payload.role_id))
        role = role_res.scalar_one_or_none()
        if not role:
            raise NotFoundException("Role", payload.role_id)

        # Check existing assignment
        for ura in user.roles:
            if (
                ura.tenant_id == tenant_id
                and ura.role_id == payload.role_id
                and ura.campus_id == payload.campus_id
                and ura.department_id == payload.department_id
            ):
                raise ConflictException(f"User already holds role '{role.display_name}' in this scope.")

        assignment = UserRoleAssignment(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=user.id,
            role_id=role.id,
            campus_id=payload.campus_id,
            department_id=payload.department_id,
        )
        db.add(assignment)
        await db.commit()

        # Re-fetch user with refreshed roles
        return await AdminRbacService.get_user(db, tenant_id, user.id)

    @staticmethod
    async def revoke_role(
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        role_id: UUID,
        actor_id: UUID,
    ) -> AdminUserResponse:
        """Revoke a role from a user, with self-lockout and last-superadmin safeguards."""
        # Find the role to inspect its name
        role_res = await db.execute(select(Role).where(Role.id == role_id))
        role = role_res.scalar_one_or_none()
        if not role:
            raise NotFoundException("Role", role_id)

        # Safeguard 1: Admin cannot revoke their own SUPER_ADMIN role
        if user_id == actor_id and role.name in {"SUPER_ADMIN", "ADMIN"}:
            raise ValidationException(f"Security Policy Violation: You cannot revoke your own '{role.display_name}' role.")

        # Safeguard 2: Prevent removing the last active SUPER_ADMIN in the tenant
        if role.name == "SUPER_ADMIN":
            active_super_admins_stmt = (
                select(func.count(UserRoleAssignment.id))
                .join(Role, UserRoleAssignment.role_id == Role.id)
                .where(
                    UserRoleAssignment.tenant_id == tenant_id,
                    Role.name == "SUPER_ADMIN",
                )
            )
            count_res = await db.execute(active_super_admins_stmt)
            super_admin_count = count_res.scalar_one() or 0
            if super_admin_count <= 1:
                raise ValidationException(
                    "Security Policy Violation: Cannot revoke the sole remaining SUPER_ADMIN of the institution."
                )

        stmt = select(UserRoleAssignment).where(
            UserRoleAssignment.tenant_id == tenant_id,
            UserRoleAssignment.user_id == user_id,
            UserRoleAssignment.role_id == role_id,
        )
        res = await db.execute(stmt)
        assignment = res.scalar_one_or_none()
        if not assignment:
            raise NotFoundException("UserRoleAssignment", f"user={user_id}, role={role_id}")

        await db.delete(assignment)
        await db.commit()

        return await AdminRbacService.get_user(db, tenant_id, user_id)

    @staticmethod
    async def update_user_status(
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        payload: AdminUserStatusUpdateRequest,
        actor_id: UUID,
    ) -> AdminUserResponse:
        """Update user account status (ACTIVE, SUSPENDED, INACTIVE) with self-deactivation protection."""
        if user_id == actor_id and payload.status != "ACTIVE":
            raise ValidationException("Security Policy Violation: Administrators cannot deactivate or suspend their own account.")

        user_res = await db.execute(select(User).where(User.id == user_id))
        user = user_res.scalar_one_or_none()
        if not user:
            raise NotFoundException("User", user_id)

        user.status = payload.status
        user.is_active = (payload.status == "ACTIVE")
        await db.commit()

        return await AdminRbacService.get_user(db, tenant_id, user_id)

    @staticmethod
    async def get_user(db: AsyncSession, tenant_id: UUID, user_id: UUID) -> AdminUserResponse:
        """Retrieve a single user with tenant roles."""
        user_res = await db.execute(
            select(User)
            .where(User.id == user_id)
        )
        user = user_res.scalar_one_or_none()
        if not user:
            raise NotFoundException("User", user_id)

        assignments_res = await db.execute(
            select(UserRoleAssignment)
            .where(
                UserRoleAssignment.user_id == user_id,
                UserRoleAssignment.tenant_id == tenant_id,
            )
            .options(selectinload(UserRoleAssignment.role))
        )
        assignments = assignments_res.scalars().all()

        role_infos = [
            AdminUserRoleInfo(
                id=ura.id,
                role_id=ura.role.id,
                role_name=ura.role.name,
                display_name=ura.role.display_name,
                campus_id=ura.campus_id,
                department_id=ura.department_id,
            )
            for ura in assignments
            if ura.role
        ]

        return AdminUserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            phone_number=user.phone_number,
            status=user.status,
            roles=role_infos,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
