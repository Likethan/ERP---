"""Domain Event Backbone Models, Consumer Checkpoints & Dead-Letter Storage (Step 27).

Enforces:
- Per-consumer idempotency and deduplication tracking
- Dead-letter triage and audited replay records
- Re-exports transactional outbox models
"""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantScopedModel
from app.models.workflow import OutboxEvent


class ConsumerCheckpointStatus(StrEnum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class EventConsumerCheckpoint(TenantScopedModel):
    """Per-consumer execution checkpoint for idempotent domain event processing."""

    __tablename__ = "event_consumer_checkpoints"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "event_id", "consumer_name", name="uq_consumer_event_checkpoint"
        ),
        Index("idx_consumer_checkpoint_tenant_status", "tenant_id", "consumer_name", "status"),
        Index("idx_consumer_checkpoint_event", "event_id"),
    )

    event_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workflow_outbox_events.id", ondelete="CASCADE"),
        nullable=False,
    )
    consumer_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(32), default=ConsumerCheckpointStatus.PENDING, nullable=False
    )
    attempt_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    duration_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_retryable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    checkpoint_metadata: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    outbox_event: Mapped["OutboxEvent"] = relationship(
        "OutboxEvent", foreign_keys=[event_id], lazy="joined"
    )


class EventDeadLetter(TenantScopedModel):
    """Dead-letter archive for exhausted or terminally failed domain events."""

    __tablename__ = "event_dead_letters"
    __table_args__ = (
        Index("idx_event_dlq_tenant_resolved", "tenant_id", "is_resolved"),
        Index("idx_event_dlq_tenant_type", "tenant_id", "event_type"),
        Index("idx_event_dlq_event", "event_id"),
    )

    event_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workflow_outbox_events.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    consumer_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    failure_reason: Mapped[str] = mapped_column(String(255), nullable=False)
    error_details_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    first_failed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_failed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    outbox_event: Mapped["OutboxEvent"] = relationship(
        "OutboxEvent", foreign_keys=[event_id], lazy="joined"
    )
