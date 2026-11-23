"""Create intelligence and AI backend engine tables

Revision ID: 002_intelligence_engine
Revises: 001_documents_digital_records
Create Date: 2026-10-03 22:15:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "002_intelligence_engine"
down_revision = "001_documents_digital_records"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Conversations Table
    op.create_table(
        "intelligence_conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), default="New Conversation", nullable=False),
        sa.Column("domain", sa.String(32), default="ALL", nullable=False),
        sa.Column("status", sa.String(32), default="ACTIVE", nullable=False),
        sa.Column("context_type", sa.String(32), default="GLOBAL", nullable=False),
        sa.Column("context_id", sa.String(128), nullable=True),
        sa.Column("is_pinned", sa.Boolean(), default=False, nullable=False),
        sa.Column("is_archived", sa.Boolean(), default=False, nullable=False),
        sa.Column("is_saved", sa.Boolean(), default=False, nullable=False),
        sa.Column("message_count", sa.Integer(), default=0, nullable=False),
        sa.Column("last_message_snippet", sa.Text(), nullable=True),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), default=False, nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "idx_intel_conv_tenant_user",
        "intelligence_conversations",
        ["tenant_id", "user_id"],
    )
    op.create_index(
        "idx_intel_conv_tenant_status",
        "intelligence_conversations",
        ["tenant_id", "status"],
    )
    op.create_index(
        "idx_intel_conv_tenant_created",
        "intelligence_conversations",
        ["tenant_id", "created_at"],
    )

    # 2. Messages Table
    op.create_table(
        "intelligence_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("intelligence_conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), default="COMPLETED", nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("structured_response", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("tool_calls", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("sources", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("explainability", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("suggested_actions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("model", sa.String(128), nullable=True),
        sa.Column("provider", sa.String(64), nullable=True),
        sa.Column("token_usage", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "idx_intel_msg_tenant_conv",
        "intelligence_messages",
        ["tenant_id", "conversation_id"],
    )
    op.create_index(
        "idx_intel_msg_conv_created",
        "intelligence_messages",
        ["conversation_id", "created_at"],
    )

    # 3. Insights Table
    op.create_table(
        "intelligence_insights",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("type", sa.String(32), nullable=False),
        sa.Column("domain", sa.String(32), nullable=False),
        sa.Column("priority", sa.String(32), default="INFO", nullable=False),
        sa.Column("status", sa.String(32), default="NEW", nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("affected_record_count", sa.Integer(), default=0, nullable=False),
        sa.Column("affected_records", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("recommended_action", sa.Text(), nullable=False),
        sa.Column("recommended_action_href", sa.String(255), nullable=True),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("methodology", sa.Text(), nullable=True),
        sa.Column("related_domain_href", sa.String(255), nullable=True),
        sa.Column("is_saved", sa.Boolean(), default=False, nullable=False),
        sa.Column("activity_timeline", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("source_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "idx_intel_insight_tenant_domain",
        "intelligence_insights",
        ["tenant_id", "domain"],
    )
    op.create_index(
        "idx_intel_insight_tenant_status",
        "intelligence_insights",
        ["tenant_id", "status"],
    )
    op.create_index(
        "idx_intel_insight_tenant_priority",
        "intelligence_insights",
        ["tenant_id", "priority"],
    )

    # 4. Alerts Table
    op.create_table(
        "intelligence_alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("type", sa.String(32), nullable=False),
        sa.Column("domain", sa.String(32), nullable=False),
        sa.Column("severity", sa.String(32), default="INFO", nullable=False),
        sa.Column("status", sa.String(32), default="OPEN", nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("affected_count", sa.Integer(), default=0, nullable=False),
        sa.Column("affected_records", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("source_domain", sa.String(64), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("recommended_action", sa.Text(), nullable=False),
        sa.Column("recommended_action_href", sa.String(255), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "acknowledged_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("acknowledged_by_name", sa.String(255), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "resolved_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("resolved_by_name", sa.String(255), nullable=True),
        sa.Column("activity_timeline", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("source_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "idx_intel_alert_tenant_domain",
        "intelligence_alerts",
        ["tenant_id", "domain"],
    )
    op.create_index(
        "idx_intel_alert_tenant_status",
        "intelligence_alerts",
        ["tenant_id", "status"],
    )
    op.create_index(
        "idx_intel_alert_tenant_severity",
        "intelligence_alerts",
        ["tenant_id", "severity"],
    )

    # 5. Saved Insights Table
    op.create_table(
        "intelligence_saved_insights",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("type", sa.String(32), default="AI_RESPONSE", nullable=False),
        sa.Column("domain", sa.String(32), default="ALL", nullable=False),
        sa.Column("content_snippet", sa.Text(), nullable=False),
        sa.Column("href", sa.String(255), default="/intelligence", nullable=False),
        sa.Column("query", sa.Text(), nullable=True),
        sa.Column("response_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("filters", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("last_accessed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "idx_intel_saved_tenant_user",
        "intelligence_saved_insights",
        ["tenant_id", "user_id"],
    )
    op.create_index(
        "idx_intel_saved_tenant_domain",
        "intelligence_saved_insights",
        ["tenant_id", "domain"],
    )

    # 6. AI Activity Table
    op.create_table(
        "intelligence_activity",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("user_name", sa.String(255), nullable=False),
        sa.Column("user_role", sa.String(64), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("query_hash", sa.String(64), nullable=True),
        sa.Column("domain", sa.String(32), default="ALL", nullable=False),
        sa.Column("tools_invoked", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("result_summary", sa.Text(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), default=0, nullable=False),
        sa.Column("status", sa.String(32), default="COMPLETED", nullable=False),
        sa.Column("data_sources", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("context_summary", sa.String(255), nullable=True),
        sa.Column("provider", sa.String(64), nullable=True),
        sa.Column("model", sa.String(128), nullable=True),
        sa.Column("token_usage", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "idx_intel_act_tenant_user",
        "intelligence_activity",
        ["tenant_id", "user_id"],
    )
    op.create_index(
        "idx_intel_act_tenant_created",
        "intelligence_activity",
        ["tenant_id", "created_at"],
    )
    op.create_index(
        "idx_intel_act_tenant_status",
        "intelligence_activity",
        ["tenant_id", "status"],
    )


def downgrade() -> None:
    op.drop_table("intelligence_activity")
    op.drop_table("intelligence_saved_insights")
    op.drop_table("intelligence_alerts")
    op.drop_table("intelligence_insights")
    op.drop_table("intelligence_messages")
    op.drop_table("intelligence_conversations")
