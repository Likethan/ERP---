"""Saved insights and pinned views management service."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, PermissionDeniedException
from app.models.intelligence import SavedInsight
from app.models.people import User
from app.schemas.intelligence import SavedInsightCreate, SavedInsightUpdate


class SavedInsightService:
    """Manages user-pinned AI query results and analytical views."""

    @classmethod
    async def list_saved(
        cls, db: AsyncSession, tenant_id: UUID, user_id: UUID
    ) -> list[SavedInsight]:
        stmt = (
            select(SavedInsight)
            .where(SavedInsight.tenant_id == tenant_id, SavedInsight.user_id == user_id)
            .order_by(SavedInsight.last_accessed_at.desc())
        )
        return list((await db.execute(stmt)).scalars().all())

    @classmethod
    async def create_saved(
        cls, db: AsyncSession, tenant_id: UUID, user: User, data: SavedInsightCreate
    ) -> SavedInsight:
        saved = SavedInsight(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=user.id,
            title=data.title.strip(),
            type=data.type,
            domain=data.domain.upper() if data.domain else "ALL",
            content_snippet=data.content_snippet.strip(),
            href=data.href or "/intelligence",
            query=data.query,
            response_snapshot=data.response_snapshot,
            filters=data.filters,
            last_accessed_at=datetime.now(UTC),
        )
        db.add(saved)
        await db.commit()
        await db.refresh(saved)
        return saved

    @classmethod
    async def get_saved(
        cls, db: AsyncSession, tenant_id: UUID, saved_id: UUID, user_id: UUID
    ) -> SavedInsight:
        stmt = select(SavedInsight).where(
            SavedInsight.tenant_id == tenant_id, SavedInsight.id == saved_id
        )
        item = await db.scalar(stmt)
        if not item:
            raise NotFoundException("SavedInsight", str(saved_id))
        if item.user_id != user_id:
            raise PermissionDeniedException("intelligence:saved_access_denied")

        item.last_accessed_at = datetime.now(UTC)
        await db.commit()
        return item

    @classmethod
    async def update_saved(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        saved_id: UUID,
        user_id: UUID,
        data: SavedInsightUpdate,
    ) -> SavedInsight:
        item = await cls.get_saved(db, tenant_id, saved_id, user_id)
        if data.title is not None and data.title.strip():
            item.title = data.title.strip()
        if data.content_snippet is not None and data.content_snippet.strip():
            item.content_snippet = data.content_snippet.strip()

        await db.commit()
        await db.refresh(item)
        return item

    @classmethod
    async def delete_saved(
        cls, db: AsyncSession, tenant_id: UUID, saved_id: UUID, user_id: UUID
    ) -> None:
        item = await cls.get_saved(db, tenant_id, saved_id, user_id)
        await db.delete(item)
        await db.commit()
