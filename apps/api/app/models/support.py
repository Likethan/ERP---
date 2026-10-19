"""Enterprise Customer Support, Service Desk & SLA Management Models (Step 36).

Provides support tickets, multi-tenant isolation, public vs internal communications,
SLA policies and clocks, team routing, CSAT ratings, and incident correlation.
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

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

from app.models.base import Base, BaseModel

JSONB_COMPAT = JSONB


# -----------------------------------------------------------------------------
# 1. Enums
# -----------------------------------------------------------------------------


class SupportTicketStatus(StrEnum):
    """Lifecycle status of a customer support ticket."""

    NEW = "NEW"
    TRIAGED = "TRIAGED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING_FOR_REQUESTER = "WAITING_FOR_REQUESTER"
    WAITING_FOR_ENGINEERING = "WAITING_FOR_ENGINEERING"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REOPENED = "REOPENED"
    ESCALATED = "ESCALATED"
    ON_HOLD = "ON_HOLD"
    CANCELLED = "CANCELLED"


class SupportPriority(StrEnum):
    """Urgency / business priority classification."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class SupportSeverity(StrEnum):
    """Impact severity classification."""

    SEV_1_CRITICAL = "SEV_1_CRITICAL"
    SEV_2_MAJOR = "SEV_2_MAJOR"
    SEV_3_MODERATE = "SEV_3_MODERATE"
    SEV_4_MINOR = "SEV_4_MINOR"


class SupportRequestType(StrEnum):
    """Nature of the customer support request."""

    INCIDENT = "INCIDENT"
    SERVICE_REQUEST = "SERVICE_REQUEST"
    ACCESS_REQUEST = "ACCESS_REQUEST"
    CONFIGURATION_REQUEST = "CONFIGURATION_REQUEST"
    DATA_CORRECTION = "DATA_CORRECTION"
    FEATURE_REQUEST = "FEATURE_REQUEST"


class SupportCategory(StrEnum):
    """Functional ERP domain category for ticket intake and routing."""

    ACCOUNT_ACCESS = "ACCOUNT_ACCESS"
    STUDENT_STAFF_ADMIN = "STUDENT_STAFF_ADMIN"
    ACADEMIC_CONFIG = "ACADEMIC_CONFIG"
    ATTENDANCE = "ATTENDANCE"
    EXAMINATIONS = "EXAMINATIONS"
    FINANCE_FEES = "FINANCE_FEES"
    PLACEMENTS = "PLACEMENTS"
    CAMPUS_OPERATIONS = "CAMPUS_OPERATIONS"
    DOCUMENTS_RECORDS = "DOCUMENTS_RECORDS"
    REPORTS_ANALYTICS = "REPORTS_ANALYTICS"
    INTEGRATIONS_APIS = "INTEGRATIONS_APIS"
    AI_FEATURES = "AI_FEATURES"
    PERFORMANCE_AVAILABILITY = "PERFORMANCE_AVAILABILITY"
    DATA_MIGRATION_ONBOARDING = "DATA_MIGRATION_ONBOARDING"
    FEATURE_REQUEST = "FEATURE_REQUEST"
    GENERAL_ASSISTANCE = "GENERAL_ASSISTANCE"


class RequesterType(StrEnum):
    """Institutional role of the ticket requester."""

    STUDENT = "STUDENT"
    FACULTY = "FACULTY"
    STAFF = "STAFF"
    INSTITUTION_ADMIN = "INSTITUTION_ADMIN"
    PLATFORM_OPERATOR = "PLATFORM_OPERATOR"


class SupportMessageType(StrEnum):
    """Visibility scope of a communication message."""

    PUBLIC_REPLY = "PUBLIC_REPLY"
    INTERNAL_NOTE = "INTERNAL_NOTE"


class SupportSlaState(StrEnum):
    """Operational measurement status of a support SLA commitment."""

    ON_TRACK = "ON_TRACK"
    AT_RISK = "AT_RISK"
    BREACHED = "BREACHED"
    PAUSED = "PAUSED"
    MET = "MET"
    UNCONFIGURED = "UNCONFIGURED"


class SupportTimelineEventType(StrEnum):
    """Timeline event classification."""

    CREATED = "CREATED"
    STATUS_CHANGED = "STATUS_CHANGED"
    TRIAGED = "TRIAGED"
    ASSIGNED = "ASSIGNED"
    REASSIGNED = "REASSIGNED"
    PUBLIC_REPLY_ADDED = "PUBLIC_REPLY_ADDED"
    INTERNAL_NOTE_ADDED = "INTERNAL_NOTE_ADDED"
    ESCALATED = "ESCALATED"
    SLA_WARNING = "SLA_WARNING"
    SLA_BREACHED = "SLA_BREACHED"
    SLA_PAUSED = "SLA_PAUSED"
    SLA_RESUMED = "SLA_RESUMED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REOPENED = "REOPENED"
    CSAT_SUBMITTED = "CSAT_SUBMITTED"
    INCIDENT_LINKED = "INCIDENT_LINKED"
    ARTICLE_LINKED = "ARTICLE_LINKED"


# -----------------------------------------------------------------------------
# 2. Entities
# -----------------------------------------------------------------------------


class SupportTeam(BaseModel):
    """Designated support team or resolution queue (e.g., Tier-1 Ops, Finance Desk)."""

    __tablename__ = "support_teams"

    tenant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    specialization_modules: Mapped[list[str]] = mapped_column(
        JSONB_COMPAT,
        nullable=False,
        default=list,
        server_default="[]",
    )
    supervisor_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_platform_team: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    members = relationship(
        "SupportTeamMember",
        back_populates="team",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    tickets = relationship("SupportTicket", back_populates="team")


class SupportTeamMember(BaseModel):
    """Membership of an agent or engineer within a support team."""

    __tablename__ = "support_team_members"

    team_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("support_teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_email: Mapped[str] = mapped_column(String(255), nullable=False)
    is_team_lead: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    active_ticket_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    team = relationship("SupportTeam", back_populates="members")

    __table_args__ = (
        UniqueConstraint("team_id", "user_id", name="uq_support_team_member"),
    )


class SupportSlaPolicy(BaseModel):
    """Service Level Agreement duration targets and escalation thresholds."""

    __tablename__ = "support_sla_policies"

    tenant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    service_plan: Mapped[str] = mapped_column(
        String(32), default="ALL", nullable=False, index=True
    )  # ALL, ENTERPRISE, STANDARD, BASIC
    priority: Mapped[str] = mapped_column(
        String(32), default=SupportPriority.MEDIUM.value, nullable=False, index=True
    )
    severity: Mapped[str | None] = mapped_column(String(32), nullable=True)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)

    response_target_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=120)
    resolution_target_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=1440)
    business_hours_only: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    business_start_hour: Mapped[int] = mapped_column(Integer, default=9, nullable=False)
    business_end_hour: Mapped[int] = mapped_column(Integer, default=18, nullable=False)
    escalation_threshold_pct: Mapped[int] = mapped_column(Integer, default=75, nullable=False)

    escalation_team_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("support_teams.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class SupportTicket(BaseModel):
    """Core enterprise support request entity spanning requester, tenant, and resolution."""

    __tablename__ = "support_tickets"

    tenant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    ticket_number: Mapped[str] = mapped_column(
        String(32), unique=True, nullable=False, index=True
    )  # e.g., TICK-2026-0001

    # Requester
    requester_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    requester_email: Mapped[str] = mapped_column(String(255), nullable=False)
    requester_name: Mapped[str] = mapped_column(String(255), nullable=False)
    requester_type: Mapped[str] = mapped_column(
        String(32), default=RequesterType.STUDENT.value, nullable=False
    )

    # Core Ticket Details
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(
        String(64), default=SupportCategory.GENERAL_ASSISTANCE.value, nullable=False, index=True
    )
    subcategory: Mapped[str | None] = mapped_column(String(64), nullable=True)
    request_type: Mapped[str] = mapped_column(
        String(32), default=SupportRequestType.SERVICE_REQUEST.value, nullable=False
    )
    priority: Mapped[str] = mapped_column(
        String(32), default=SupportPriority.MEDIUM.value, nullable=False, index=True
    )
    severity: Mapped[str] = mapped_column(
        String(32), default=SupportSeverity.SEV_3_MODERATE.value, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), default=SupportTicketStatus.NEW.value, nullable=False, index=True
    )

    # Routing & Ownership
    assigned_team_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("support_teams.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    assigned_team_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    assigned_agent_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    assigned_agent_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # ERP & Incident Correlation
    related_erp_module: Mapped[str | None] = mapped_column(String(64), nullable=True)
    related_resource_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    related_resource_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    related_incident_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    related_security_incident_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("security_incidents.id", ondelete="SET NULL"),
        nullable=True,
    )

    # SLA Tracking
    sla_policy_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("support_sla_policies.id", ondelete="SET NULL"),
        nullable=True,
    )
    response_due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolution_due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    first_response_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    triaged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reopened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    escalated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    sla_response_status: Mapped[str] = mapped_column(
        String(32), default=SupportSlaState.ON_TRACK.value, nullable=False
    )
    sla_resolution_status: Mapped[str] = mapped_column(
        String(32), default=SupportSlaState.ON_TRACK.value, nullable=False
    )
    sla_paused_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sla_total_paused_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Resolution & Closure
    resolution_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    closure_reason: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reopen_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reopen_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    escalation_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    escalation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # CSAT Feedback
    csat_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    csat_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    csat_submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Context & Tags
    tags: Mapped[list[str]] = mapped_column(
        JSONB_COMPAT,
        nullable=False,
        default=list,
        server_default="[]",
    )
    attachments_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB_COMPAT,
        nullable=False,
        default=list,
        server_default="[]",
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB_COMPAT,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    # Relationships
    team = relationship("SupportTeam", back_populates="tickets")
    _messages = relationship(
        "SupportTicketMessage",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="SupportTicketMessage.created_at",
        lazy="selectin",
    )
    timeline = relationship(
        "SupportTicketTimeline",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="SupportTicketTimeline.created_at",
        lazy="selectin",
    )
    kb_links = relationship(
        "SupportTicketArticleLink",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="SupportTicketArticleLink.created_at",
        lazy="selectin",
    )

    _filter_internal_notes: bool = False

    @property
    def messages(self) -> list["SupportTicketMessage"]:
        raw = getattr(self, "_messages", []) or []
        if getattr(self, "_filter_internal_notes", False):
            return [m for m in raw if m.message_type == SupportMessageType.PUBLIC_REPLY.value]
        return list(raw)

    @messages.setter
    def messages(self, val: list["SupportTicketMessage"]) -> None:
        self._messages = val

    __table_args__ = (
        Index("idx_supp_tick_tenant_status", "tenant_id", "status"),
        Index("idx_supp_tick_tenant_priority", "tenant_id", "priority"),
        Index("idx_supp_tick_requester", "requester_id", "status"),
        Index("idx_supp_tick_agent", "assigned_agent_id", "status"),
        Index("idx_supp_tick_team", "assigned_team_id", "status"),
        Index("idx_supp_tick_due", "resolution_due_at", "status"),
    )


class SupportTicketMessage(BaseModel):
    """Communication record within a ticket, segregated into public reply vs internal note."""

    __tablename__ = "support_ticket_messages"

    ticket_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("support_tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tenant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    sender_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    sender_email: Mapped[str] = mapped_column(String(255), nullable=False)
    sender_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sender_role: Mapped[str] = mapped_column(String(64), nullable=False)

    message_type: Mapped[str] = mapped_column(
        String(32), default=SupportMessageType.PUBLIC_REPLY.value, nullable=False, index=True
    )  # PUBLIC_REPLY vs INTERNAL_NOTE
    body: Mapped[str] = mapped_column(Text, nullable=False)

    attachments_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB_COMPAT,
        nullable=False,
        default=list,
        server_default="[]",
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB_COMPAT,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    ticket = relationship("SupportTicket", back_populates="_messages")

    __table_args__ = (
        Index("idx_supp_msg_ticket_type", "ticket_id", "message_type"),
    )


class SupportTicketTimeline(BaseModel):
    """Audit event tracking lifecycle transitions, SLA warnings, and handoffs."""

    __tablename__ = "support_ticket_timeline"

    ticket_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("support_tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tenant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(
        String(64), default=SupportTimelineEventType.CREATED.value, nullable=False, index=True
    )
    actor_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    actor_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    from_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    to_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    summary: Mapped[str] = mapped_column(String(255), nullable=False)
    details_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB_COMPAT,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    ticket = relationship("SupportTicket", back_populates="timeline")


class SupportTicketArticleLink(BaseModel):
    """Correlation linking an approved knowledge-base article to a support ticket."""

    __tablename__ = "support_ticket_article_links"

    ticket_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("support_tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    article_id: Mapped[str] = mapped_column(String(64), nullable=False)
    article_title: Mapped[str] = mapped_column(String(255), nullable=False)
    article_url: Mapped[str] = mapped_column(String(512), nullable=False)
    relevance_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    was_helpful: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    linked_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    ticket = relationship("SupportTicket", back_populates="kb_links")
