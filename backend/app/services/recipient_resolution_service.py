"""Reusable, Tenant-Isolated Recipient Resolution Service for CampusOS (Step 26).

Enforces:
- Resolution across DIRECT, STUDENT, FACULTY, STAFF, PARENT, ROLE, ASSIGNEE, and ADMIN strategies.
- Strict tenant isolation: every recipient is validated against tenant boundaries.
- Contact availability inspection without failing the entire notification batch.
- Privacy preservation: sensitive records are never leaked across tenant or unauthorized boundaries.
"""

import logging
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case_management import QueueMember
from app.models.core import TenantMembership
from app.models.notification import RecipientStrategy
from app.models.people import (
    FacultyProfile,
    GuardianProfile,
    Role,
    StaffProfile,
    StudentProfile,
    User,
    UserRoleAssignment,
)

logger = logging.getLogger("campusos.recipients")


@dataclass(frozen=True)
class ResolvedRecipient:
    """Normalized recipient contact details within tenant boundary."""
    user_id: UUID
    email: str | None
    phone: str | None
    name: str
    role: str | None = None
    is_valid: bool = True
    context_data: dict[str, Any] = field(default_factory=dict)

    def has_contact_for_channel(self, channel: str) -> bool:
        ch = channel.upper()
        if ch == "IN_APP":
            return True
        elif ch == "EMAIL":
            return bool(self.email and "@" in self.email)
        elif ch == "SMS":
            return bool(self.phone and len(self.phone.strip()) >= 7)
        elif ch == "PUSH":
            return True
        return False


class RecipientResolutionService:
    """Resolves operational entities to tenant-verified user recipients."""

    @classmethod
    async def _verify_tenant_user_membership(
        cls, db: AsyncSession, tenant_id: UUID, user_ids: list[UUID]
    ) -> set[UUID]:
        """Verify that user_ids genuinely belong to tenant_id to enforce multi-tenant isolation."""
        if not user_ids:
            return set()

        # Check primary_tenant_id or TenantMembership
        stmt = (
            select(User.id)
            .outerjoin(TenantMembership, TenantMembership.user_id == User.id)
            .where(
                and_(
                    User.id.in_(user_ids),
                    User.is_active.is_(True),
                    or_(
                        User.primary_tenant_id == tenant_id,
                        TenantMembership.tenant_id == tenant_id,
                    ),
                )
            )
        )
        res = await db.execute(stmt)
        return set(res.scalars().all())

    @classmethod
    async def resolve_recipients(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        strategy: str,
        recipient_config: dict[str, Any] | None,
        context: dict[str, Any],
    ) -> list[ResolvedRecipient]:
        """Resolve recipients based on strategy, recipient_config, and event context."""
        strategy_upper = strategy.upper()
        config = recipient_config or {}

        target_user_ids: list[UUID] = []
        custom_recipient_map: dict[UUID, dict[str, Any]] = {}

        # ---------------------------------------------------------------------
        # 1. DIRECT STRATEGY
        # ---------------------------------------------------------------------
        if strategy_upper == RecipientStrategy.DIRECT:
            # Look in context or config
            u_ids = context.get("recipient_user_ids") or context.get("user_ids")
            if not u_ids and "recipient_user_id" in context:
                u_ids = [context["recipient_user_id"]]
            elif not u_ids and "user_id" in context:
                u_ids = [context["user_id"]]
            elif not u_ids and "user_ids" in config:
                u_ids = config["user_ids"]
            elif not u_ids and "user_id" in config:
                u_ids = [config["user_id"]]

            if u_ids:
                for uid in u_ids:
                    try:
                        target_user_ids.append(UUID(str(uid)))
                    except Exception:
                        pass

        # ---------------------------------------------------------------------
        # 2. STUDENT STRATEGY
        # ---------------------------------------------------------------------
        elif strategy_upper == RecipientStrategy.STUDENT:
            s_ids = context.get("student_ids") or (
                [context["student_id"]] if "student_id" in context else []
            )
            parsed_sids = []
            for sid in s_ids:
                try:
                    parsed_sids.append(UUID(str(sid)))
                except Exception:
                    pass

            if parsed_sids:
                stmt = select(StudentProfile).where(
                    and_(
                        StudentProfile.tenant_id == tenant_id,
                        StudentProfile.id.in_(parsed_sids),
                    )
                )
                res = await db.execute(stmt)
                for sp in res.scalars().all():
                    if sp.user_id:
                        target_user_ids.append(sp.user_id)
                        custom_recipient_map[sp.user_id] = {
                            "roll_number": sp.roll_number,
                            "student_id": str(sp.id),
                        }

        # ---------------------------------------------------------------------
        # 3. FACULTY STRATEGY
        # ---------------------------------------------------------------------
        elif strategy_upper == RecipientStrategy.FACULTY:
            f_ids = context.get("faculty_ids") or (
                [context["faculty_id"]] if "faculty_id" in context else []
            )
            parsed_fids = []
            for fid in f_ids:
                try:
                    parsed_fids.append(UUID(str(fid)))
                except Exception:
                    pass

            if parsed_fids:
                stmt = select(FacultyProfile).where(
                    and_(
                        FacultyProfile.tenant_id == tenant_id,
                        FacultyProfile.id.in_(parsed_fids),
                    )
                )
                res = await db.execute(stmt)
                for fp in res.scalars().all():
                    if fp.user_id:
                        target_user_ids.append(fp.user_id)
                        custom_recipient_map[fp.user_id] = {
                            "employee_code": fp.employee_code,
                            "faculty_id": str(fp.id),
                        }

        # ---------------------------------------------------------------------
        # 4. STAFF STRATEGY
        # ---------------------------------------------------------------------
        elif strategy_upper == RecipientStrategy.STAFF:
            st_ids = context.get("staff_ids") or (
                [context["staff_id"]] if "staff_id" in context else []
            )
            parsed_stids = []
            for stid in st_ids:
                try:
                    parsed_stids.append(UUID(str(stid)))
                except Exception:
                    pass

            if parsed_stids:
                stmt = select(StaffProfile).where(
                    and_(
                        StaffProfile.tenant_id == tenant_id,
                        StaffProfile.id.in_(parsed_stids),
                    )
                )
                res = await db.execute(stmt)
                for stp in res.scalars().all():
                    if stp.user_id:
                        target_user_ids.append(stp.user_id)
                        custom_recipient_map[stp.user_id] = {
                            "staff_id": str(stp.id),
                        }

        # ---------------------------------------------------------------------
        # 5. PARENT / GUARDIAN STRATEGY
        # ---------------------------------------------------------------------
        elif strategy_upper == RecipientStrategy.PARENT:
            s_ids = context.get("student_ids") or (
                [context["student_id"]] if "student_id" in context else []
            )
            parsed_sids = []
            for sid in s_ids:
                try:
                    parsed_sids.append(UUID(str(sid)))
                except Exception:
                    pass

            if parsed_sids:
                stmt = select(StudentProfile).where(
                    and_(
                        StudentProfile.tenant_id == tenant_id,
                        StudentProfile.id.in_(parsed_sids),
                    )
                )
                res = await db.execute(stmt)
                students = list(res.scalars().all())

                # Check linked guardian profiles or fallback guardian details
                recipients: list[ResolvedRecipient] = []
                for sp in students:
                    if sp.guardian_id:
                        g_stmt = select(GuardianProfile).where(GuardianProfile.id == sp.guardian_id)
                        g_res = await db.execute(g_stmt)
                        guard = g_res.scalar_one_or_none()
                        if guard and guard.user_id:
                            target_user_ids.append(guard.user_id)
                            continue

                    # If student has guardian email/phone directly on profile
                    if sp.guardian_email or sp.guardian_phone:
                        # Use student's user record or fallback dummy user_id
                        dummy_id = sp.user_id or sp.id
                        recipients.append(
                            ResolvedRecipient(
                                user_id=dummy_id,
                                email=sp.guardian_email,
                                phone=sp.guardian_phone,
                                name=sp.guardian_name or "Parent/Guardian",
                                role="PARENT",
                                context_data={"student_id": str(sp.id), "student_name": f"{sp.roll_number}"},
                            )
                        )
                if recipients:
                    return recipients

        # ---------------------------------------------------------------------
        elif strategy_upper == RecipientStrategy.ROLE:
            roles_to_match = (
                config.get("roles")
                or config.get("role_name")
                or config.get("role")
                or context.get("roles")
                or context.get("role_name")
                or context.get("role")
                or []
            )
            if isinstance(roles_to_match, str):
                roles_to_match = [roles_to_match]

            if roles_to_match:
                stmt = (
                    select(UserRoleAssignment.user_id)
                    .join(Role, UserRoleAssignment.role_id == Role.id)
                    .where(
                        and_(
                            Role.name.in_(roles_to_match),
                            or_(Role.tenant_id == tenant_id, Role.tenant_id.is_(None)),
                        )
                    )
                )
                res = await db.execute(stmt)
                target_user_ids.extend(res.scalars().all())

        # ---------------------------------------------------------------------
        # 7. ASSIGNEE STRATEGY (Task Assignee or Work Queue Members)
        # ---------------------------------------------------------------------
        elif strategy_upper == RecipientStrategy.ASSIGNEE:
            if "assigned_user_id" in context and context["assigned_user_id"]:
                try:
                    target_user_ids.append(UUID(str(context["assigned_user_id"])))
                except Exception:
                    pass

            if "assigned_queue_id" in context and context["assigned_queue_id"]:
                try:
                    qid = UUID(str(context["assigned_queue_id"]))
                    q_stmt = select(QueueMember.user_id).where(
                        and_(
                            QueueMember.tenant_id == tenant_id,
                            QueueMember.queue_id == qid,
                            QueueMember.is_active.is_(True),
                        )
                    )
                    q_res = await db.execute(q_stmt)
                    target_user_ids.extend(q_res.scalars().all())
                except Exception:
                    pass

        # ---------------------------------------------------------------------
        # 8. ADMIN STRATEGY
        # ---------------------------------------------------------------------
        elif strategy_upper == RecipientStrategy.ADMIN:
            stmt = (
                select(UserRoleAssignment.user_id)
                .join(Role, UserRoleAssignment.role_id == Role.id)
                .where(
                    and_(
                        Role.name.in_(["INSTITUTION_ADMIN", "ADMIN", "SUPER_ADMIN"]),
                        or_(Role.tenant_id == tenant_id, Role.tenant_id.is_(None)),
                    )
                )
            )
            res = await db.execute(stmt)
            target_user_ids.extend(res.scalars().all())

            tm_stmt = (
                select(TenantMembership.user_id)
                .where(
                    and_(
                        TenantMembership.tenant_id == tenant_id,
                        TenantMembership.role_scope.in_(["INSTITUTION_ADMIN", "ADMIN", "SUPER_ADMIN"]),
                        TenantMembership.status == "ACTIVE",
                    )
                )
            )
            tm_res = await db.execute(tm_stmt)
            target_user_ids.extend(tm_res.scalars().all())

        # Filter duplicates
        unique_uids = list(set(target_user_ids))
        if not unique_uids:
            return []

        # Validate tenant boundary
        valid_tenant_uids = await cls._verify_tenant_user_membership(db, tenant_id, unique_uids)
        if not valid_tenant_uids:
            logger.warning(
                "No resolved user IDs belonged to tenant %s. Dropping cross-tenant targets.",
                tenant_id,
            )
            return []

        # Load user profiles
        user_stmt = select(User).where(User.id.in_(valid_tenant_uids))
        users_res = await db.execute(user_stmt)
        users = list(users_res.scalars().all())

        resolved_list: list[ResolvedRecipient] = []
        for u in users:
            name = f"{u.first_name} {u.last_name}".strip()
            extra_ctx = custom_recipient_map.get(u.id, {})
            resolved_list.append(
                ResolvedRecipient(
                    user_id=u.id,
                    email=u.email,
                    phone=u.phone_number,
                    name=name or u.email,
                    role=strategy_upper,
                    context_data=extra_ctx,
                )
            )

        return resolved_list
