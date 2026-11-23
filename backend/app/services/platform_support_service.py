"""Controlled & Audited Platform Support Access Delegation Service for CampusOS (Step 30).

Implements time-limited, purpose-bound, and scoped support access into tenant environments
with immediate revocation capabilities and forensic logging.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditEventCategory, build_audit_entry
from app.core.exceptions import (
    NotFoundException,
    SupportAccessExpiredException,
)
from app.models.core import Institution
from app.models.platform_ops import PlatformSupportSession


class PlatformSupportService:
    """Governs temporary support delegations with strict bounds and audit trails."""

    @classmethod
    async def create_support_session(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        operator_user_id: UUID,
        reason: str,
        duration_hours: int = 2,
        ticket_reference: str | None = None,
        permissions_scope: list[str] | None = None,
    ) -> PlatformSupportSession:
        """Issue a time-bounded, purpose-justified support session."""
        # Verify tenant exists
        stmt_t = select(Institution).where(Institution.id == tenant_id)
        res_t = await db.execute(stmt_t)
        tenant = res_t.scalar_one_or_none()
        if not tenant:
            raise NotFoundException("Tenant", tenant_id)

        now = datetime.now(UTC)
        duration = max(1, min(duration_hours, 8))
        expires_at = now + timedelta(hours=duration)

        scope = permissions_scope or ["support:diagnostics:read", "support:config:read"]

        session = PlatformSupportSession(
            tenant_id=tenant_id,
            operator_user_id=operator_user_id,
            reason=reason,
            ticket_reference=ticket_reference,
            permissions_scope=scope,
            is_active=True,
            started_at=now,
            expires_at=expires_at,
        )
        db.add(session)
        await db.flush()

        # Audit support access initiation
        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.PLATFORM_SUPPORT_SESSION_STARTED,
                entity_type="PlatformSupportSession",
                entity_id=session.id,
                user_id=operator_user_id,
                new_values_json={
                    "duration_hours": duration,
                    "ticket_reference": ticket_reference,
                    "scope": scope,
                    "reason": reason,
                },
                business_context=f"Support session initiated for {duration}h by operator {operator_user_id}: {reason}",
            )
        )
        await db.flush()
        return session

    @classmethod
    async def revoke_support_session(
        cls,
        db: AsyncSession,
        session_id: UUID,
        revoked_by_id: UUID | None,
        reason: str = "Administrative revocation",
    ) -> PlatformSupportSession:
        """Immediately terminate an active support session."""
        stmt = select(PlatformSupportSession).where(PlatformSupportSession.id == session_id)
        res = await db.execute(stmt)
        session = res.scalar_one_or_none()
        if not session:
            raise NotFoundException("SupportSession", session_id)

        if not session.is_active:
            return session

        now = datetime.now(UTC)
        session.is_active = False
        session.revoked_at = now
        session.revoked_by_id = revoked_by_id
        session.revocation_reason = reason

        db.add(
            build_audit_entry(
                tenant_id=session.tenant_id,
                action=AuditEventCategory.PLATFORM_SUPPORT_SESSION_REVOKED,
                entity_type="PlatformSupportSession",
                entity_id=session.id,
                user_id=revoked_by_id,
                new_values_json={"reason": reason, "revoked_at": now.isoformat()},
                business_context=f"Support session {session.id} revoked: {reason}",
            )
        )
        await db.flush()
        return session

    @classmethod
    async def get_and_validate_session(
        cls,
        db: AsyncSession,
        session_id: UUID,
    ) -> PlatformSupportSession:
        """Validate that a support session is currently valid and active."""
        stmt = select(PlatformSupportSession).where(PlatformSupportSession.id == session_id)
        res = await db.execute(stmt)
        session = res.scalar_one_or_none()
        if not session:
            raise NotFoundException("SupportSession", session_id)

        now = datetime.now(UTC)
        exp = session.expires_at if session.expires_at.tzinfo else session.expires_at.replace(tzinfo=UTC)

        if not session.is_active or now > exp:
            raise SupportAccessExpiredException(session_id)

        return session

    @classmethod
    async def list_support_sessions(
        cls,
        db: AsyncSession,
        tenant_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[PlatformSupportSession]:
        """List historical and active platform support sessions."""
        stmt = select(PlatformSupportSession)
        if tenant_id:
            stmt = stmt.where(PlatformSupportSession.tenant_id == tenant_id)
        stmt = stmt.order_by(desc(PlatformSupportSession.created_at)).offset(offset).limit(limit)
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @classmethod
    async def sweep_expired_sessions(cls, db: AsyncSession) -> int:
        """Deactivate expired support sessions in scheduled background maintenance."""
        now = datetime.now(UTC)
        stmt = (
            select(PlatformSupportSession)
            .where(
                PlatformSupportSession.is_active.is_(True),
                PlatformSupportSession.expires_at <= now,
            )
        )
        res = await db.execute(stmt)
        expired = list(res.scalars().all())

        for s in expired:
            s.is_active = False
            s.revocation_reason = "Expired by schedule"
            db.add(
                build_audit_entry(
                    tenant_id=s.tenant_id,
                    action=AuditEventCategory.PLATFORM_SUPPORT_SESSION_EXPIRED,
                    entity_type="PlatformSupportSession",
                    entity_id=s.id,
                    business_context="Support session automatically expired after configured duration.",
                )
            )

        if expired:
            await db.flush()
        return len(expired)
