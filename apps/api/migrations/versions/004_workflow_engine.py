"""Workflow and Automation Engine Migration.

Revision ID: 004_workflow_engine
Revises: 003_saas_hardening
Create Date: 2026-10-05 19:55:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "004_workflow_engine"
down_revision = "003_saas_hardening"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. workflow_definitions
    op.create_table(
        "workflow_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=True,
            index=True,
        ),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("domain", sa.String(32), server_default="GENERAL", nullable=False),
        sa.Column("status", sa.String(32), server_default="DRAFT", nullable=False),
        sa.Column("is_system", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("active_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "updated_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "code", name="uq_workflow_tenant_code"),
    )
    op.create_index("idx_workflow_tenant_status", "workflow_definitions", ["tenant_id", "status"])
    op.create_index("idx_workflow_domain", "workflow_definitions", ["tenant_id", "domain"])

    # 2. workflow_versions
    op.create_table(
        "workflow_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "workflow_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workflow_definitions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), server_default="DRAFT", nullable=False),
        sa.Column("definition_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("change_summary", sa.String(255), nullable=True),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("workflow_id", "version_number", name="uq_workflow_version_number"),
    )
    op.create_index("idx_workflow_version_published", "workflow_versions", ["workflow_id", "status"])

    # 3. workflow_triggers
    op.create_table(
        "workflow_triggers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "workflow_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workflow_definitions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("trigger_type", sa.String(32), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=True),
        sa.Column("cron_expression", sa.String(64), nullable=True),
        sa.Column("schedule_interval", sa.String(32), nullable=True),
        sa.Column("schedule_time", sa.String(16), nullable=True),
        sa.Column("timezone", sa.String(64), server_default="Asia/Kolkata", nullable=False),
        sa.Column("configuration_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_trigger_tenant_type", "workflow_triggers", ["tenant_id", "trigger_type"])
    op.create_index("idx_trigger_event_type", "workflow_triggers", ["tenant_id", "event_type"])

    # 4. workflow_executions
    op.create_table(
        "workflow_executions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "workflow_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workflow_definitions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "workflow_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workflow_versions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("trigger_type", sa.String(32), nullable=False),
        sa.Column("trigger_reference", sa.String(128), nullable=True),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("status", sa.String(32), server_default="QUEUED", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_retries", sa.Integer(), server_default="3", nullable=False),
        sa.Column("correlation_id", sa.String(64), nullable=False),
        sa.Column("actor_type", sa.String(32), server_default="SYSTEM", nullable=False),
        sa.Column("actor_id", sa.String(64), nullable=True),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("context_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_execution_tenant_idempotency"),
    )
    op.create_index("idx_exec_tenant_status", "workflow_executions", ["tenant_id", "status"])
    op.create_index("idx_exec_workflow_status", "workflow_executions", ["workflow_id", "status"])
    op.create_index("idx_exec_started_at", "workflow_executions", ["tenant_id", "started_at"])

    # 5. workflow_execution_steps
    op.create_table(
        "workflow_execution_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "execution_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workflow_executions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("step_key", sa.String(64), nullable=False),
        sa.Column("step_type", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), server_default="PENDING", nullable=False),
        sa.Column("input_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("output_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_exec_step_execution", "workflow_execution_steps", ["execution_id", "status"])
    op.create_index("idx_exec_step_tenant", "workflow_execution_steps", ["tenant_id", "status"])

    # 6. workflow_outbox_events
    op.create_table(
        "workflow_outbox_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("event_type", sa.String(64), nullable=False, index=True),
        sa.Column("aggregate_type", sa.String(64), nullable=False),
        sa.Column("aggregate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(32), server_default="PENDING", nullable=False),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_attempts", sa.Integer(), server_default="5", nullable=False),
        sa.Column(
            "available_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("correlation_id", sa.String(64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_outbox_status_available", "workflow_outbox_events", ["status", "available_at"])
    op.create_index("idx_outbox_tenant_event", "workflow_outbox_events", ["tenant_id", "event_type"])

    # 7. workflow_dead_letters
    op.create_table(
        "workflow_dead_letters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "workflow_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workflow_definitions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "execution_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workflow_executions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("error_code", sa.String(64), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("resolved", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "resolved_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_dlq_tenant_resolved", "workflow_dead_letters", ["tenant_id", "resolved"])
    op.create_index("idx_dlq_workflow", "workflow_dead_letters", ["workflow_id"])


def downgrade() -> None:
    op.drop_index("idx_dlq_workflow", table_name="workflow_dead_letters")
    op.drop_index("idx_dlq_tenant_resolved", table_name="workflow_dead_letters")
    op.drop_table("workflow_dead_letters")

    op.drop_index("idx_outbox_tenant_event", table_name="workflow_outbox_events")
    op.drop_index("idx_outbox_status_available", table_name="workflow_outbox_events")
    op.drop_table("workflow_outbox_events")

    op.drop_index("idx_exec_step_tenant", table_name="workflow_execution_steps")
    op.drop_index("idx_exec_step_execution", table_name="workflow_execution_steps")
    op.drop_table("workflow_execution_steps")

    op.drop_index("idx_exec_started_at", table_name="workflow_executions")
    op.drop_index("idx_exec_workflow_status", table_name="workflow_executions")
    op.drop_index("idx_exec_tenant_status", table_name="workflow_executions")
    op.drop_table("workflow_executions")

    op.drop_index("idx_trigger_event_type", table_name="workflow_triggers")
    op.drop_index("idx_trigger_tenant_type", table_name="workflow_triggers")
    op.drop_table("workflow_triggers")

    op.drop_index("idx_workflow_version_published", table_name="workflow_versions")
    op.drop_table("workflow_versions")

    op.drop_index("idx_workflow_domain", table_name="workflow_definitions")
    op.drop_index("idx_workflow_tenant_status", table_name="workflow_definitions")
    op.drop_table("workflow_definitions")
