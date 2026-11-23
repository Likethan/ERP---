"""SQLAlchemy models for CampusOS Intelligence & AI Engine.

Implements conversational history, AI response telemetry, structured insights,
operational alerts, saved views, and tenant-scoped AI activity records.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import SoftDeleteMixin, TenantScopedModel


class Conversation(TenantScopedModel, SoftDeleteMixin):
    """Institutional conversation session tracking assistant interactions."""

    __tablename__ = "intelligence_conversations"
    __table_args__ = (
        Index("idx_intel_conv_tenant_user", "tenant_id", "user_id"),
        Index("idx_intel_conv_tenant_status", "tenant_id", "status"),
        Index("idx_intel_conv_tenant_created", "tenant_id", "created_at"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), default="New Conversation", nullable=False)
    domain: Mapped[str] = mapped_column(String(32), default="ALL", nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="ACTIVE", nullable=False
    )  # ACTIVE, ARCHIVED, DELETED
    context_type: Mapped[str] = mapped_column(
        String(32), default="GLOBAL", nullable=False
    )  # GLOBAL, STUDENT, FACULTY, STAFF, DEPARTMENT, PROGRAM, COURSE, CAMPUS
    context_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_saved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_message_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


class Message(TenantScopedModel):
    """Individual conversational interaction message with structured response blocks."""

    __tablename__ = "intelligence_messages"
    __table_args__ = (
        Index("idx_intel_msg_tenant_conv", "tenant_id", "conversation_id"),
        Index("idx_intel_msg_conv_created", "conversation_id", "created_at"),
    )

    conversation_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("intelligence_conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)  # USER, ASSISTANT, SYSTEM, TOOL
    status: Mapped[str] = mapped_column(
        String(32), default="COMPLETED", nullable=False
    )  # QUEUED, PROCESSING, COMPLETED, FAILED

    content: Mapped[str] = mapped_column(Text, nullable=False)
    structured_response: Mapped[list | None] = mapped_column(
        JSONB, nullable=True
    )  # list[AIResponseBlock]
    tool_calls: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    sources: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # list[AISource]
    explainability: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    suggested_actions: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    token_usage: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")


class Insight(TenantScopedModel):
    """Automated analytical finding or risk assessment derived from ERP domain data."""

    __tablename__ = "intelligence_insights"
    __table_args__ = (
        Index("idx_intel_insight_tenant_domain", "tenant_id", "domain"),
        Index("idx_intel_insight_tenant_status", "tenant_id", "status"),
        Index("idx_intel_insight_tenant_priority", "tenant_id", "priority"),
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # ACADEMIC, ATTENDANCE, EXAMINATION, FINANCE, PLACEMENT, CAMPUS, INFRASTRUCTURE, DOCUMENT, STUDENT
    domain: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # ACADEMICS, ATTENDANCE, EXAMINATIONS, etc.
    priority: Mapped[str] = mapped_column(
        String(32), default="INFO", nullable=False
    )  # INFO, LOW, MEDIUM, HIGH, CRITICAL
    status: Mapped[str] = mapped_column(
        String(32), default="NEW", nullable=False
    )  # NEW, REVIEWED, DISMISSED, ACTIONED

    summary: Mapped[str] = mapped_column(Text, nullable=False)
    affected_record_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    affected_records: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    recommended_action: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_action_href: Mapped[str | None] = mapped_column(String(255), nullable=True)
    evidence: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    methodology: Mapped[str | None] = mapped_column(Text, nullable=True)
    related_domain_href: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_saved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    activity_timeline: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    source_ids: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Alert(TenantScopedModel):
    """Operational anomaly or threshold breach requiring institutional attention."""

    __tablename__ = "intelligence_alerts"
    __table_args__ = (
        Index("idx_intel_alert_tenant_domain", "tenant_id", "domain"),
        Index("idx_intel_alert_tenant_status", "tenant_id", "status"),
        Index("idx_intel_alert_tenant_severity", "tenant_id", "severity"),
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # ATTENDANCE, ACADEMIC, EXAMINATION, FINANCE, PLACEMENT, INFRASTRUCTURE, DOCUMENT, SYSTEM
    domain: Mapped[str] = mapped_column(String(32), nullable=False)
    severity: Mapped[str] = mapped_column(
        String(32), default="INFO", nullable=False
    )  # INFO, WARNING, HIGH, CRITICAL
    status: Mapped[str] = mapped_column(
        String(32), default="OPEN", nullable=False
    )  # OPEN, ACKNOWLEDGED, RESOLVED, DISMISSED

    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    affected_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    affected_records: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    source_domain: Mapped[str] = mapped_column(String(64), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_action: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_action_href: Mapped[str | None] = mapped_column(String(255), nullable=True)

    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    acknowledged_by_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolved_by_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    activity_timeline: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    source_ids: Mapped[list | None] = mapped_column(JSONB, nullable=True)


class SavedInsight(TenantScopedModel):
    """Saved query result, insight snapshot, or analytics view pinned by an authorized user."""

    __tablename__ = "intelligence_saved_insights"
    __table_args__ = (
        Index("idx_intel_saved_tenant_user", "tenant_id", "user_id"),
        Index("idx_intel_saved_tenant_domain", "tenant_id", "domain"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(
        String(32), default="AI_RESPONSE", nullable=False
    )  # AI_RESPONSE, INSIGHT, ANALYTICS_VIEW, REPORT
    domain: Mapped[str] = mapped_column(String(32), default="ALL", nullable=False)
    content_snippet: Mapped[str] = mapped_column(Text, nullable=False)
    href: Mapped[str] = mapped_column(String(255), default="/intelligence", nullable=False)

    query: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    filters: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    last_accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AIActivity(TenantScopedModel):
    """Audit log of an AI interaction, tool execution, and resource access."""

    __tablename__ = "intelligence_activity"
    __table_args__ = (
        Index("idx_intel_act_tenant_user", "tenant_id", "user_id"),
        Index("idx_intel_act_tenant_created", "tenant_id", "created_at"),
        Index("idx_intel_act_tenant_status", "tenant_id", "status"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_name: Mapped[str] = mapped_column(String(255), nullable=False)
    user_role: Mapped[str] = mapped_column(String(64), nullable=False)
    conversation_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    query: Mapped[str] = mapped_column(Text, nullable=False)
    query_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    domain: Mapped[str] = mapped_column(String(32), default="ALL", nullable=False)

    tools_invoked: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    result_summary: Mapped[str] = mapped_column(Text, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="COMPLETED", nullable=False
    )  # COMPLETED, FAILED, CANCELLED

    data_sources: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    context_summary: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    token_usage: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)


class AIGovernancePolicy(TenantScopedModel):
    """Institutional governance policy defining allowed AI use cases, models, and boundaries."""

    __tablename__ = "intelligence_governance_policies"
    __table_args__ = (Index("idx_intel_gov_tenant_active", "tenant_id", "is_active"),)

    policy_name: Mapped[str] = mapped_column(
        String(128), default="DEFAULT_INSTITUTIONAL_POLICY", nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    allowed_providers: Mapped[list] = mapped_column(
        JSONB, default=lambda: ["mock", "openai", "anthropic", "gemini"], nullable=False
    )
    allowed_models: Mapped[list] = mapped_column(
        JSONB,
        default=lambda: ["campusos-institutional-v1", "gpt-4o", "claude-3-5-sonnet"],
        nullable=False,
    )
    permitted_use_cases: Mapped[list] = mapped_column(
        JSONB,
        default=lambda: [
            "ANALYTICS_QUERY",
            "STUDENT_SUPPORT",
            "ANOMALY_DETECTION",
            "RECOMMENDATION",
            "WORKFLOW_ASSISTANCE",
        ],
        nullable=False,
    )
    prohibited_use_cases: Mapped[list] = mapped_column(
        JSONB,
        default=lambda: [
            "AUTOMATED_GRADING",
            "AUTOMATED_DISCIPLINE",
            "RAW_SQL_EXECUTION",
            "AUTOMATED_ADMISSION_REJECTION",
        ],
        nullable=False,
    )

    max_context_tokens: Mapped[int] = mapped_column(Integer, default=4096, nullable=False)
    max_output_tokens: Mapped[int] = mapped_column(Integer, default=2048, nullable=False)
    daily_budget_usd: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("50.00"), nullable=False
    )
    human_review_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enforce_prompt_guard: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )


class AIPrediction(TenantScopedModel):
    """Predictive intelligence record, such as student academic or attendance risk."""

    __tablename__ = "intelligence_predictions"
    __table_args__ = (
        Index("idx_intel_pred_tenant_target", "tenant_id", "target_type", "target_id"),
        Index("idx_intel_pred_tenant_status", "tenant_id", "status"),
        Index("idx_intel_pred_tenant_risk", "tenant_id", "risk_level"),
    )

    prediction_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    prediction_type: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # STUDENT_ACADEMIC_RISK, STUDENT_ATTENDANCE_RISK
    target_type: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # STUDENT, COURSE, SECTION, DEPARTMENT
    target_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)

    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    is_rule_based: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    prediction_score: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    risk_level: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # LOW, MEDIUM, HIGH, CRITICAL

    signals: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    limitations: Mapped[str | None] = mapped_column(Text, nullable=True)

    human_review_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="PENDING_REVIEW", nullable=False
    )  # PENDING_REVIEW, ACKNOWLEDGED, ACTIONED, OVERRIDDEN

    reviewed_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AIRecommendation(TenantScopedModel):
    """Evidence-grounded recommendation suggesting institutional or workflow action."""

    __tablename__ = "intelligence_recommendations"
    __table_args__ = (
        Index("idx_intel_rec_tenant_status", "tenant_id", "status"),
        Index("idx_intel_rec_tenant_category", "tenant_id", "category"),
    )

    recommendation_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    domain: Mapped[str] = mapped_column(String(32), nullable=False)
    priority: Mapped[str] = mapped_column(String(32), default="MEDIUM", nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    reasoning_summary: Mapped[str] = mapped_column(Text, nullable=False)
    supporting_evidence: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    metric_references: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    suggested_action: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_action_type: Mapped[str] = mapped_column(
        String(64), default="NOTIFY_ADVISOR", nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(32), default="PROPOSED", nullable=False
    )  # PROPOSED, ACCEPTED, REJECTED, ACTIONED, EXPIRED
    workflow_case_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    reviewed_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AIEvaluationRun(TenantScopedModel):
    """Automated AI evaluation suite execution record measuring groundedness, safety, and compliance."""

    __tablename__ = "intelligence_evaluation_runs"
    __table_args__ = (Index("idx_intel_eval_tenant_suite", "tenant_id", "suite_name"),)

    suite_name: Mapped[str] = mapped_column(String(128), nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)

    total_cases: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    passed_cases: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_cases: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    score_pct: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), default=Decimal("0.0"), nullable=False
    )
    groundedness_score: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), default=Decimal("0.0"), nullable=False
    )
    injection_resistance_score: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), default=Decimal("0.0"), nullable=False
    )
    schema_compliance_score: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), default=Decimal("0.0"), nullable=False
    )

    results_detail: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default="PASSED", nullable=False
    )  # PASSED, FAILED, WARNING


class AIUsageRecord(TenantScopedModel):
    """Detailed token usage, latency, and estimated cost audit log per request."""

    __tablename__ = "intelligence_usage_records"
    __table_args__ = (
        Index("idx_intel_usage_tenant_user", "tenant_id", "user_id"),
        Index("idx_intel_usage_tenant_created", "tenant_id", "created_at"),
    )

    user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    request_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    use_case: Mapped[str] = mapped_column(String(64), nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)

    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(10, 4), default=Decimal("0.0"), nullable=False
    )
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    status: Mapped[str] = mapped_column(
        String(32), default="SUCCESS", nullable=False
    )  # SUCCESS, RATE_LIMITED, FAILED, REJECTED
    error_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
