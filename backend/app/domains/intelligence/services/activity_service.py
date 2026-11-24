"""Audit telemetry and activity logging for AI Engine."""

import hashlib
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.intelligence import AIActivity


class ActivityService:
    """Manages immutable audit records of AI queries and tool invocations."""

    @classmethod
    async def log_activity(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        user_name: str,
        user_role: str,
        query: str,
        domain: str,
        tools_invoked: list[str],
        result_summary: str,
        duration_ms: int,
        status: str = "COMPLETED",
        data_sources: list[str] | None = None,
        context_summary: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        error_code: str | None = None,
        conversation_id: UUID | None = None,
    ) -> AIActivity:
        query_hash = hashlib.sha256(query.encode("utf-8")).hexdigest()[:16]

        act = AIActivity(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            user_name=user_name,
            user_role=user_role,
            conversation_id=conversation_id,
            query=query[:500],
            query_hash=query_hash,
            domain=domain.upper() if domain else "ALL",
            tools_invoked=tools_invoked,
            result_summary=result_summary[:500],
            duration_ms=duration_ms,
            status=status,
            data_sources=data_sources or [],
            context_summary=context_summary,
            provider=provider or "mock",
            model=model or "campusos-v1",
            error_code=error_code,
        )
        db.add(act)
        await db.commit()
        await db.refresh(act)
        return act

    @classmethod
    async def list_activities(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        is_admin: bool = False,
        limit: int = 50,
    ) -> list[AIActivity]:
        stmt = select(AIActivity).where(AIActivity.tenant_id == tenant_id)
        if not is_admin:
            stmt = stmt.where(AIActivity.user_id == user_id)

        stmt = stmt.order_by(AIActivity.created_at.desc()).limit(limit)
        return list((await db.execute(stmt)).scalars().all())
