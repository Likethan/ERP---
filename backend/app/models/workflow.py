"""SQLAlchemy models for CampusOS Workflow and Automation Engine.

Implements workflow definitions, immutable versioning, triggers (schedule, event, manual),
execution runs, step execution tracking, reliable transactional outbox events,
and dead-letter queues.
"""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
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

from app.models.base import BaseModel, SoftDeleteMixin, TenantScopedModel


class WorkflowStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ARCHIVED = "ARCHIVED"


class WorkflowVersionStatus(StrEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class WorkflowTriggerType(StrEnum):
    SCHEDULE = "SCHEDULE"
    EVENT = "EVENT"
    MANUAL = "MANUAL"


class WorkflowExecutionStatus(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ExecutionStepStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class OutboxEventStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"
    DEAD_LETTER = "DEAD_LETTER"


class WorkflowDefinition(BaseModel, SoftDeleteMixin):
    """Workflow specification and lifecycle container."""

    __tablename__ = "workflow_definitions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_workflow_tenant_code"),
        Index("idx_workflow_tenant_status", "tenant_id", "status"),
        Index("idx_workflow_domain", "tenant_id", "domain"),
    )

    tenant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    domain: Mapped[str] = mapped_column(
        String(32), nullable=False, default="GENERAL"
    )  # ATTENDANCE, FINANCE, DOCUMENTS, PLACEMENT, ACADEMICS, GENERAL
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=WorkflowStatus.DRAFT
    )
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    active_version_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    updated_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    versions: Mapped[list["WorkflowVersion"]] = relationship(
        "WorkflowVersion",
        back_populates="workflow",
        cascade="all, delete-orphan",
        order_by="WorkflowVersion.version_number",
    )
    triggers: Mapped[list["WorkflowTrigger"]] = relationship(
        "WorkflowTrigger",
        back_populates="workflow",
        cascade="all, delete-orphan",
    )
    executions: Mapped[list["WorkflowExecution"]] = relationship(
        "WorkflowExecution",
        back_populates="workflow",
        cascade="all, delete-orphan",
    )

    @property
    def active_version(self) -> int:
        if self.active_version_id:
            for v in self.versions:
                if v.id == self.active_version_id:
                    return v.version_number
        for v in self.versions:
            if v.is_active:
                return v.version_number
        return 1

    @active_version.setter
    def active_version(self, value: int) -> None:
        pass  # Managed via version records

    @property
    def current_version_id(self) -> UUID | None:
        return self.active_version_id

    @current_version_id.setter
    def current_version_id(self, value: UUID | None) -> None:
        self.active_version_id = value

    @property
    def created_by(self) -> UUID | None:
        return self.created_by_user_id

    @created_by.setter
    def created_by(self, value: UUID | None) -> None:
        self.created_by_user_id = value

    @property
    def updated_by(self) -> UUID | None:
        return self.updated_by_user_id

    @updated_by.setter
    def updated_by(self, value: UUID | None) -> None:
        self.updated_by_user_id = value


class WorkflowVersion(BaseModel):
    """Immutable version snapshot of a workflow step graph and execution rules."""

    __tablename__ = "workflow_versions"
    __table_args__ = (
        UniqueConstraint("workflow_id", "version_number", name="uq_workflow_version_number"),
        Index("idx_workflow_version_published", "workflow_id", "status"),
    )

    tenant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    workflow_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workflow_definitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=WorkflowVersionStatus.DRAFT, nullable=False
    )
    definition_json: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    change_summary: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    workflow: Mapped["WorkflowDefinition"] = relationship(
        "WorkflowDefinition", back_populates="versions"
    )

    @property
    def version(self) -> int:
        return self.version_number

    @version.setter
    def version(self, value: int) -> None:
        self.version_number = value

    @property
    def is_active(self) -> bool:
        return self.status == WorkflowVersionStatus.PUBLISHED

    @is_active.setter
    def is_active(self, value: bool) -> None:
        self.status = WorkflowVersionStatus.PUBLISHED if value else WorkflowVersionStatus.DRAFT

    @property
    def trigger_definition(self) -> dict[str, Any]:
        return self.definition_json.get("trigger", {}) if isinstance(self.definition_json, dict) else {}

    @trigger_definition.setter
    def trigger_definition(self, value: dict[str, Any]) -> None:
        if not isinstance(self.definition_json, dict):
            self.definition_json = {}
        self.definition_json["trigger"] = value

    @property
    def steps_definition(self) -> list[dict[str, Any]]:
        return self.definition_json.get("steps", []) if isinstance(self.definition_json, dict) else []

    @steps_definition.setter
    def steps_definition(self, value: list[dict[str, Any]]) -> None:
        if not isinstance(self.definition_json, dict):
            self.definition_json = {}
        self.definition_json["steps"] = value

    @property
    def created_by(self) -> UUID | None:
        return self.created_by_user_id

    @created_by.setter
    def created_by(self, value: UUID | None) -> None:
        self.created_by_user_id = value


class WorkflowTrigger(BaseModel):
    """Trigger configuration activating a workflow via schedule, event, or manual invocation."""

    __tablename__ = "workflow_triggers"
    __table_args__ = (
        Index("idx_trigger_tenant_type", "tenant_id", "trigger_type"),
        Index("idx_trigger_event_type", "tenant_id", "event_type"),
    )

    tenant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    workflow_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workflow_definitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    trigger_type: Mapped[str] = mapped_column(
        String(32), nullable=False
    )
    event_type: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )
    cron_expression: Mapped[str | None] = mapped_column(String(64), nullable=True)
    schedule_interval: Mapped[str | None] = mapped_column(
        String(32), nullable=True
    )
    schedule_time: Mapped[str | None] = mapped_column(
        String(16), nullable=True
    )
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Kolkata", nullable=False)
    configuration_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    workflow: Mapped["WorkflowDefinition"] = relationship(
        "WorkflowDefinition", back_populates="triggers"
    )

    @property
    def is_enabled(self) -> bool:
        return self.is_active

    @is_enabled.setter
    def is_enabled(self, value: bool) -> None:
        self.is_active = value

    @property
    def interval_seconds(self) -> int | None:
        if self.configuration_json and isinstance(self.configuration_json, dict):
            return self.configuration_json.get("interval_seconds")
        return None

    @interval_seconds.setter
    def interval_seconds(self, value: int | None) -> None:
        if not isinstance(self.configuration_json, dict):
            self.configuration_json = {}
        self.configuration_json["interval_seconds"] = value

    @property
    def days_of_week(self) -> list[int] | None:
        if self.configuration_json and isinstance(self.configuration_json, dict):
            return self.configuration_json.get("days_of_week")
        return None

    @days_of_week.setter
    def days_of_week(self, value: list[int] | None) -> None:
        if not isinstance(self.configuration_json, dict):
            self.configuration_json = {}
        self.configuration_json["days_of_week"] = value

    @property
    def config(self) -> dict[str, Any]:
        return self.configuration_json or {}

    @config.setter
    def config(self, value: dict[str, Any] | None) -> None:
        self.configuration_json = value


class WorkflowExecution(TenantScopedModel):
    """Runtime execution instance of a workflow."""

    __tablename__ = "workflow_executions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_execution_tenant_idempotency"),
        Index("idx_exec_tenant_status", "tenant_id", "status"),
        Index("idx_exec_workflow_status", "workflow_id", "status"),
        Index("idx_exec_started_at", "tenant_id", "started_at"),
    )

    workflow_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workflow_definitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workflow_version_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workflow_versions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    trigger_type: Mapped[str] = mapped_column(
        String(32), nullable=False
    )
    trigger_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)

    status: Mapped[str] = mapped_column(
        String(32), default=WorkflowExecutionStatus.QUEUED, nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False)

    actor_type: Mapped[str] = mapped_column(String(32), default="SYSTEM", nullable=False)
    actor_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    context_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    workflow: Mapped["WorkflowDefinition"] = relationship(
        "WorkflowDefinition", back_populates="executions"
    )
    steps: Mapped[list["WorkflowExecutionStep"]] = relationship(
        "WorkflowExecutionStep",
        back_populates="execution",
        cascade="all, delete-orphan",
        order_by="WorkflowExecutionStep.created_at",
    )

    @property
    def input_context(self) -> dict[str, Any]:
        return self.context_data or {}

    @input_context.setter
    def input_context(self, value: dict[str, Any] | None) -> None:
        self.context_data = value


class WorkflowExecutionStep(TenantScopedModel):
    """Audit and telemetry record for an individual step within a workflow execution."""

    __tablename__ = "workflow_execution_steps"
    __table_args__ = (
        Index("idx_exec_step_execution", "execution_id", "status"),
        Index("idx_exec_step_tenant", "tenant_id", "status"),
    )

    execution_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workflow_executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_key: Mapped[str] = mapped_column(String(64), nullable=False)
    step_type: Mapped[str] = mapped_column(
        String(32), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), default=ExecutionStepStatus.PENDING, nullable=False
    )
    input_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    output_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    execution: Mapped["WorkflowExecution"] = relationship(
        "WorkflowExecution", back_populates="steps"
    )

    @property
    def step_id(self) -> str:
        return self.step_key

    @step_id.setter
    def step_id(self, value: str) -> None:
        self.step_key = value

    @property
    def action_type(self) -> str | None:
        if self.input_data and isinstance(self.input_data, dict):
            return self.input_data.get("action_type")
        return None

    @action_type.setter
    def action_type(self, value: str | None) -> None:
        if value:
            if not isinstance(self.input_data, dict):
                self.input_data = {}
            self.input_data["action_type"] = value


class OutboxEvent(TenantScopedModel):
    """Transactional Outbox event ensuring atomic domain changes and event emission."""

    __tablename__ = "workflow_outbox_events"
    __table_args__ = (
        Index("idx_outbox_status_available", "status", "available_at"),
        Index("idx_outbox_tenant_event", "tenant_id", "event_type"),
    )

    schema_version: Mapped[str] = mapped_column(String(16), default="1.0", nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    aggregate_type: Mapped[str] = mapped_column(String(64), nullable=False)
    aggregate_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    payload: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    status: Mapped[str] = mapped_column(
        String(32), default=OutboxEventStatus.PENDING, nullable=False
    )
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False)
    causation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    actor_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    actor_context: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    producer: Mapped[str] = mapped_column(String(64), default="CAMPUSOS_CORE", nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)


class WorkflowDeadLetter(TenantScopedModel):
    """Dead-letter archive for permanently failed workflow runs and exhausted retries."""

    __tablename__ = "workflow_dead_letters"
    __table_args__ = (
        Index("idx_dlq_tenant_resolved", "tenant_id", "resolved"),
        Index("idx_dlq_workflow", "workflow_id"),
    )

    workflow_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workflow_definitions.id", ondelete="CASCADE"),
        nullable=False,
    )
    execution_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workflow_executions.id", ondelete="CASCADE"),
        nullable=False,
    )
    error_code: Mapped[str] = mapped_column(String(64), nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    @property
    def failure_reason(self) -> str:
        return self.error_code

    @failure_reason.setter
    def failure_reason(self, value: str) -> None:
        self.error_code = value

    @property
    def last_error(self) -> str | None:
        return self.error_message

    @last_error.setter
    def last_error(self, value: str | None) -> None:
        self.error_message = value or ""

    @property
    def first_failure_at(self) -> datetime:
        return self.created_at

    @first_failure_at.setter
    def first_failure_at(self, value: datetime) -> None:
        pass

    @property
    def last_failure_at(self) -> datetime:
        return self.updated_at

    @last_failure_at.setter
    def last_failure_at(self, value: datetime) -> None:
        pass
