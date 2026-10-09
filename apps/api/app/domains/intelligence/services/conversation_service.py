"""Conversation and message lifecycle management service."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundException, PermissionDeniedException
from app.models.intelligence import Conversation, Message
from app.schemas.intelligence import AIConversationCreate, AIConversationUpdate


class ConversationService:
    """Manages multi-turn conversation sessions and message transcripts."""

    @classmethod
    async def list_conversations(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
    ) -> list[Conversation]:
        stmt = (
            select(Conversation)
            .where(
                Conversation.tenant_id == tenant_id,
                Conversation.user_id == user_id,
                Conversation.deleted_at.is_(None),
            )
            .order_by(Conversation.is_pinned.desc(), Conversation.updated_at.desc())
        )
        return list((await db.execute(stmt)).scalars().all())

    @classmethod
    async def create_conversation(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        data: AIConversationCreate,
    ) -> Conversation:
        conv = Conversation(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            title=(data.title or "New Institutional Consultation").strip(),
            domain=data.domain.upper() if data.domain else "ALL",
            context_type=data.context_type.upper() if data.context_type else "GLOBAL",
            context_id=data.context_id,
            status="ACTIVE",
            message_count=0,
        )
        db.add(conv)
        await db.commit()
        await db.refresh(conv)
        return conv

    @classmethod
    async def get_conversation(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        conversation_id: UUID,
        user_id: UUID,
    ) -> Conversation:
        stmt = (
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(
                Conversation.tenant_id == tenant_id,
                Conversation.id == conversation_id,
                Conversation.deleted_at.is_(None),
            )
        )
        conv = await db.scalar(stmt)
        if not conv:
            raise NotFoundException("Conversation", str(conversation_id))

        if conv.user_id != user_id:
            raise PermissionDeniedException("intelligence:conversation_access_denied")

        return conv

    @classmethod
    async def update_conversation(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        conversation_id: UUID,
        user_id: UUID,
        data: AIConversationUpdate,
    ) -> Conversation:
        conv = await cls.get_conversation(db, tenant_id, conversation_id, user_id)
        if data.title is not None and data.title.strip():
            conv.title = data.title.strip()
        if data.is_pinned is not None:
            conv.is_pinned = data.is_pinned
        if data.is_archived is not None:
            conv.is_archived = data.is_archived
        if data.is_saved is not None:
            conv.is_saved = data.is_saved

        await db.commit()
        await db.refresh(conv)
        return conv

    @classmethod
    async def delete_conversation(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        conversation_id: UUID,
        user_id: UUID,
    ) -> None:
        conv = await cls.get_conversation(db, tenant_id, conversation_id, user_id)
        conv.deleted_at = datetime.now(UTC)
        conv.status = "DELETED"
        await db.commit()

    @classmethod
    async def list_messages(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        conversation_id: UUID,
        user_id: UUID,
    ) -> list[Message]:
        # Validate conversation ownership
        await cls.get_conversation(db, tenant_id, conversation_id, user_id)
        stmt = (
            select(Message)
            .where(
                Message.tenant_id == tenant_id,
                Message.conversation_id == conversation_id,
            )
            .order_by(Message.created_at.asc())
        )
        return list((await db.execute(stmt)).scalars().all())

    @classmethod
    async def add_message(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        conversation_id: UUID,
        role: str,
        content: str,
        structured_response: list[dict[str, Any]] | None = None,
        sources: list[dict[str, Any]] | None = None,
        explainability: dict[str, Any] | None = None,
        suggested_actions: list[dict[str, Any]] | None = None,
        tool_calls: list[dict[str, Any]] | None = None,
        model: str | None = None,
        provider: str | None = None,
        latency_ms: int | None = None,
    ) -> Message:
        msg = Message(
            id=uuid4(),
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            role=role,
            status="COMPLETED",
            content=content,
            structured_response=structured_response,
            sources=sources,
            explainability=explainability,
            suggested_actions=suggested_actions,
            tool_calls=tool_calls,
            model=model,
            provider=provider,
            latency_ms=latency_ms,
        )
        db.add(msg)

        # Update conversation stats
        conv = await db.get(Conversation, conversation_id)
        if conv:
            conv.message_count += 1
            conv.last_message_snippet = content[:150]
            conv.last_message_at = datetime.now(UTC)

        await db.commit()
        await db.refresh(msg)
        return msg
