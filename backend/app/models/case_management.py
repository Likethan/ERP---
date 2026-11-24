"""Enterprise Workflow, Case Management & Human-in-the-Loop Operations Models (Step 25).

Provides long-running human workflows, operational cases, work queues, human tasks,
explicit decisions, time-bounded delegations, and SLA tracking clocks.
"""

from datetime import UTC, datetime
from enum import StrEnum
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


class CasePriority(StrEnum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class CaseStatus(StrEnum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING = "WAITING"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"
    REOPENED = "REOPENED"


class TaskType(StrEnum):
    REVIEW = "REVIEW"
    APPROVAL = "APPROVAL"
    FORM_INPUT = "FORM_INPUT"
    DECISION = "DECISION"
    CORRECTION = "CORRECTION"
    NOTIFICATION = "NOTIFICATION"
    ESCALATION = "ESCALATION"


class TaskStatus(StrEnum):
    PENDING = "PENDING"
    CLAIMED = "CLAIMED"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING = "WAITING"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    ESCALATED = "ESCALATED"


class AssignmentStrategy(StrEnum):
    DIRECT_USER = "DIRECT_USER"
    ROLE = "ROLE"
    QUEUE = "QUEUE"
    ROUND_ROBIN = "ROUND_ROBIN"
    LEAST_LOADED = "LEAST_LOADED"
    MANUAL = "MANUAL"


class HumanDecision(StrEnum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    REQUEST_CORRECTION = "REQUEST_CORRECTION"
    RETURN = "RETURN"
    ESCALATE = "ESCALATE"
    DEFER = "DEFER"


class CommentVisibility(StrEnum):
    INTERNAL = "INTERNAL"
    CASE_PARTICIPANT = "CASE_PARTICIPANT"
    RESTRICTED = "RESTRICTED"


class CaseRelationshipType(StrEnum):
    RELATED_TO = "RELATED_TO"
    DUPLICATE_OF = "DUPLICATE_OF"
    CHILD_OF = "CHILD_OF"
    BLOCKED_BY = "BLOCKED_BY"
    DEPENDS_ON = "DEPENDS_ON"
    ESCALATED_FROM = "ESCALATED_FROM"


class CaseTimelineEventType(StrEnum):
    CASE_CREATED = "CASE_CREATED"
    TASK_CREATED = "TASK_CREATED"
    TASK_ASSIGNED = "TASK_ASSIGNED"
    TASK_CLAIMED = "TASK_CLAIMED"
    TASK_RELEASED = "TASK_RELEASED"
    COMMENT_ADDED = "COMMENT_ADDED"
    DOCUMENT_ATTACHED = "DOCUMENT_ATTACHED"
    DECISION_MADE = "DECISION_MADE"
    ESCALATED = "ESCALATED"
    STATUS_CHANGED = "STATUS_CHANGED"
    WORKFLOW_TRANSITIONED = "WORKFLOW_TRANSITIONED"
    CASE_RESOLVED = "CASE_RESOLVED"
    CASE_CLOSED = "CASE_CLOSED"
    CASE_REOPENED = "CASE_REOPENED"


class SlaStatus(StrEnum):
    ON_TRACK = "ON_TRACK"
    AT_RISK = "AT_RISK"
    BREACHED = "BREACHED"
    PAUSED = "PAUSED"
    MET = "MET"


class CaseType(BaseModel, SoftDeleteMixin):
    """Configurable case type classification (system default or tenant-specific)."""

    __tablename__ = "case_types"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_case_type_tenant_code"),
        Index("idx_case_type_tenant_active", "tenant_id", "is_active"),
        Index("idx_case_type_module", "tenant_id", "module"),
    )

    tenant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    module: Mapped[str] = mapped_column(String(32), nullable=False, default="GENERAL")
    default_priority: Mapped[str] = mapped_column(
        String(32), nullable=False, default=CasePriority.NORMAL
    )
    default_queue_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    sla_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=48)
    requires_decision: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class WorkQueue(TenantScopedModel):
    """Shared operational work queue (e.g. Admissions Desk, Finance Review)."""

    __tablename__ = "work_queues"
    __table_args__ = (
        UniqueConstraint("tenant_id", "key", name="uq_work_queue_tenant_key"),
        Index("idx_work_queue_module", "tenant_id", "module"),
        Index("idx_work_queue_active", "tenant_id", "is_active"),
    )

    key: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    module: Mapped[str] = mapped_column(String(32), nullable=False, default="GENERAL")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    assignment_policy: Mapped[str] = mapped_column(
        String(32), nullable=False, default=AssignmentStrategy.MANUAL
    )
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True, default=100)
    supervisor_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    sla_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)

    members: Mapped[list["QueueMember"]] = relationship(
        "QueueMember",
        back_populates="queue",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class QueueMember(TenantScopedModel):
    """Operator membership within a work queue with optional supervisor flag."""

    __tablename__ = "queue_members"
    __table_args__ = (
        UniqueConstraint("tenant_id", "queue_id", "user_id", name="uq_queue_member"),
        Index("idx_queue_member_user", "tenant_id", "user_id"),
    )

    queue_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("work_queues.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_supervisor: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    max_active_tasks: Mapped[int] = mapped_column(Integer, default=10, nullable=False)

    queue: Mapped["WorkQueue"] = relationship("WorkQueue", back_populates="members")


class Case(TenantScopedModel, SoftDeleteMixin):
    """Core operational matter representing an issue, review, or multi-step case."""

    __tablename__ = "cases"
    __table_args__ = (
        UniqueConstraint("tenant_id", "case_number", name="uq_case_tenant_number"),
        Index("idx_case_tenant_status", "tenant_id", "status"),
        Index("idx_case_tenant_priority", "tenant_id", "priority"),
        Index("idx_case_tenant_owner", "tenant_id", "owner_id"),
        Index("idx_case_tenant_queue", "tenant_id", "assigned_queue_id"),
        Index("idx_case_workflow_exec", "workflow_execution_id"),
        Index("idx_case_subject", "tenant_id", "subject_entity_type", "subject_entity_id"),
    )

    case_number: Mapped[str] = mapped_column(String(64), nullable=False)
    case_type_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("case_types.id", ondelete="SET NULL"),
        nullable=True,
    )
    case_type_code: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(String(32), default=CasePriority.NORMAL, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=CaseStatus.OPEN, nullable=False)
    owner_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    assigned_queue_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("work_queues.id", ondelete="SET NULL"),
        nullable=True,
    )
    workflow_execution_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workflow_executions.id", ondelete="SET NULL"),
        nullable=True,
    )
    subject_entity_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    subject_entity_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    created_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_reason: Mapped[str | None] = mapped_column(String(128), nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reopen_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sla_breached: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    tasks: Mapped[list["HumanTask"]] = relationship(
        "HumanTask",
        back_populates="case",
        cascade="all, delete-orphan",
        order_by="HumanTask.created_at",
        lazy="selectin",
    )
    comments: Mapped[list["CaseComment"]] = relationship(
        "CaseComment",
        back_populates="case",
        cascade="all, delete-orphan",
        order_by="CaseComment.created_at",
        lazy="selectin",
    )
    timeline_events: Mapped[list["CaseTimelineEvent"]] = relationship(
        "CaseTimelineEvent",
        back_populates="case",
        cascade="all, delete-orphan",
        order_by="CaseTimelineEvent.occurred_at",
        lazy="selectin",
    )
    attachments: Mapped[list["CaseAttachment"]] = relationship(
        "CaseAttachment",
        back_populates="case",
        cascade="all, delete-orphan",
        order_by="CaseAttachment.created_at",
        lazy="selectin",
    )


class CaseRelationship(TenantScopedModel):
    """Explicit cross-case linking (e.g. duplicate, dependency, parent-child)."""

    __tablename__ = "case_relationships"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "source_case_id",
            "target_case_id",
            "relationship_type",
            name="uq_case_relationship",
        ),
        Index("idx_case_rel_source", "tenant_id", "source_case_id"),
        Index("idx_case_rel_target", "tenant_id", "target_case_id"),
    )

    source_case_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_case_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    relationship_type: Mapped[str] = mapped_column(
        String(32), default=CaseRelationshipType.RELATED_TO, nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )


class CaseComment(TenantScopedModel):
    """Operational note or comment attached to a case or specific task."""

    __tablename__ = "case_comments"
    __table_args__ = (
        Index("idx_comment_case", "tenant_id", "case_id"),
        Index("idx_comment_task", "tenant_id", "task_id"),
    )

    case_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    task_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("human_tasks.id", ondelete="SET NULL"),
        nullable=True,
    )
    author_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    visibility: Mapped[str] = mapped_column(
        String(32), default=CommentVisibility.INTERNAL, nullable=False
    )
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    case: Mapped["Case"] = relationship("Case", back_populates="comments")
    task: Mapped["HumanTask | None"] = relationship("HumanTask", back_populates="comments")


class CaseAttachment(TenantScopedModel):
    """Case document attachment referencing existing storage document."""

    __tablename__ = "case_attachments"
    __table_args__ = (
        Index("idx_attachment_case", "tenant_id", "case_id"),
        Index("idx_attachment_doc", "tenant_id", "document_id"),
    )

    case_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    task_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("human_tasks.id", ondelete="SET NULL"),
        nullable=True,
    )
    document_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents_records.id", ondelete="RESTRICT"),
        nullable=False,
    )
    attachment_type: Mapped[str] = mapped_column(
        String(64), nullable=False, default="SUPPORTING_EVIDENCE"
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    visibility: Mapped[str] = mapped_column(
        String(32), default=CommentVisibility.INTERNAL, nullable=False
    )
    uploaded_by_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    case: Mapped["Case"] = relationship("Case", back_populates="attachments")


class CaseTimelineEvent(TenantScopedModel):
    """Chronological, auditable operational event along a case lifecycle."""

    __tablename__ = "case_timeline_events"
    __table_args__ = (Index("idx_timeline_case_time", "tenant_id", "case_id", "occurred_at"),)

    case_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    task_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("human_tasks.id", ondelete="SET NULL"),
        nullable=True,
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    details_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    case: Mapped["Case"] = relationship("Case", back_populates="timeline_events")


class HumanTask(TenantScopedModel, SoftDeleteMixin):
    """First-class human actionable work item requiring review, approval, or decision."""

    __tablename__ = "human_tasks"
    __table_args__ = (
        Index("idx_task_case_status", "tenant_id", "case_id", "status"),
        Index("idx_task_assigned_user", "tenant_id", "assigned_user_id", "status"),
        Index("idx_task_assigned_queue", "tenant_id", "assigned_queue_id", "status"),
        Index("idx_task_assigned_role", "tenant_id", "assigned_role", "status"),
        Index("idx_task_workflow_exec", "workflow_execution_id"),
    )

    case_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    workflow_execution_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workflow_executions.id", ondelete="SET NULL"),
        nullable=True,
    )
    step_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    task_type: Mapped[str] = mapped_column(String(32), default=TaskType.REVIEW, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=TaskStatus.PENDING, nullable=False)
    priority: Mapped[str] = mapped_column(String(32), default=CasePriority.NORMAL, nullable=False)
    assigned_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    assigned_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    assigned_queue_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("work_queues.id", ondelete="SET NULL"),
        nullable=True,
    )
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    sla_breached: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    input_context_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    output_result_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    case: Mapped["Case"] = relationship("Case", back_populates="tasks")
    decisions: Mapped[list["TaskDecision"]] = relationship(
        "TaskDecision",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="TaskDecision.created_at",
        lazy="selectin",
    )
    comments: Mapped[list["CaseComment"]] = relationship(
        "CaseComment",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="CaseComment.created_at",
        lazy="selectin",
    )


class TaskDecision(TenantScopedModel):
    """Authoritative human judgment recorded on a human task."""

    __tablename__ = "task_decisions"
    __table_args__ = (
        Index("idx_decision_task", "tenant_id", "task_id"),
        Index("idx_decision_case", "tenant_id", "case_id"),
        Index("idx_decision_actor", "tenant_id", "actor_id"),
    )

    task_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("human_tasks.id", ondelete="CASCADE"),
        nullable=False,
    )
    case_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    actor_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    decision: Mapped[str] = mapped_column(String(32), default=HumanDecision.APPROVE, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resulting_transition: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    task: Mapped["HumanTask"] = relationship("HumanTask", back_populates="decisions")


class TaskDelegation(TenantScopedModel):
    """Temporary, time-bounded authority delegation from one user to another."""

    __tablename__ = "task_delegations"
    __table_args__ = (
        Index("idx_delegation_delegator", "tenant_id", "delegator_user_id", "is_active"),
        Index("idx_delegation_delegatee", "tenant_id", "delegatee_user_id", "is_active"),
        Index("idx_delegation_validity", "valid_from", "valid_until"),
    )

    delegator_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="CASCADE"),
        nullable=False,
    )
    delegatee_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="CASCADE"),
        nullable=False,
    )
    scope_module: Mapped[str | None] = mapped_column(String(32), nullable=True)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class SlaPolicy(TenantScopedModel):
    """Configurable Service Level Agreement duration and escalation policy."""

    __tablename__ = "sla_policies"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "module", "priority", "case_type_code", name="uq_sla_policy_scope"
        ),
        Index("idx_sla_module_prio", "tenant_id", "module", "priority"),
    )

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    module: Mapped[str] = mapped_column(String(32), nullable=False, default="GENERAL")
    case_type_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    priority: Mapped[str] = mapped_column(String(32), default=CasePriority.NORMAL, nullable=False)
    target_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=2880)
    warning_threshold_percentage: Mapped[int] = mapped_column(Integer, nullable=False, default=75)
    business_hours_only: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    business_start_hour: Mapped[int] = mapped_column(Integer, default=9, nullable=False)
    business_end_hour: Mapped[int] = mapped_column(Integer, default=18, nullable=False)
    escalation_queue_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("work_queues.id", ondelete="SET NULL"),
        nullable=True,
    )
    escalation_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class SlaInstance(TenantScopedModel):
    """Runtime operational clock measuring SLA compliance for a case or task."""

    __tablename__ = "sla_instances"
    __table_args__ = (
        Index("idx_sla_inst_case", "tenant_id", "case_id", "status"),
        Index("idx_sla_inst_task", "tenant_id", "task_id", "status"),
        Index("idx_sla_inst_due", "due_at", "status"),
    )

    sla_policy_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("sla_policies.id", ondelete="SET NULL"),
        nullable=True,
    )
    case_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=True,
    )
    task_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("human_tasks.id", ondelete="CASCADE"),
        nullable=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    warning_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    elapsed_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=SlaStatus.ON_TRACK, nullable=False)
    breached: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    escalated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    escalated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
