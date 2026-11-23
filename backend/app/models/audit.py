from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AuditLog(Base):
    """Immutable forensic audit log answering WHO, WHAT, WHEN, WHERE, WHICH ENTITY,
    WHICH RECORD, BEFORE, AFTER, WHY."""

    __tablename__ = "intelligence_audit_logs"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # CREATE, UPDATE, DELETE, PUBLISH, APPROVE, REVERSE
    entity_type: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # StudentProfile, Invoice, Result, AttendanceRecord
    entity_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    old_values_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    new_values_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    route_endpoint: Mapped[str | None] = mapped_column(String(255), nullable=True)
    correlation_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, default=uuid4
    )
    business_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_audit_tenant_entity", "tenant_id", "entity_type", "entity_id", "created_at"),
        Index("idx_audit_tenant_chronological", "tenant_id", "created_at"),
    )
