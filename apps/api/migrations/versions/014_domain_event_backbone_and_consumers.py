"""Enterprise Event Backbone, Transactional Outbox & Domain Event Reliability Migration (Step 27).

Revision ID: 014_domain_event_backbone_and_consumers
Revises: 013_enterprise_notifications_delivery
Create Date: 2026-10-09 19:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "014_domain_event_backbone_and_consumers"
down_revision = "013_enterprise_notifications_delivery"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Enrich workflow_outbox_events table
    op.add_column(
        "workflow_outbox_events",
        sa.Column("schema_version", sa.String(16), nullable=False, server_default="1.0"),
    )
    op.add_column(
        "workflow_outbox_events",
        sa.Column("causation_id", sa.String(64), nullable=True),
    )
    op.add_column(
        "workflow_outbox_events",
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "workflow_outbox_events",
        sa.Column("actor_context", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default="{}"),
    )
    op.add_column(
        "workflow_outbox_events",
        sa.Column("producer", sa.String(64), nullable=False, server_default="CAMPUSOS_CORE"),
    )
    op.add_column(
        "workflow_outbox_events",
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default="{}"),
    )

    # 2. event_consumer_checkpoints
    op.create_table(
        "event_consumer_checkpoints",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "event_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workflow_outbox_events.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("consumer_name", sa.String(64), nullable=False, index=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("duration_ms", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("is_retryable", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("checkpoint_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()
        ),
        sa.UniqueConstraint("tenant_id", "event_id", "consumer_name", name="uq_consumer_event_checkpoint"),
    )
    op.create_index(
        "idx_consumer_checkpoint_tenant_status",
        "event_consumer_checkpoints",
        ["tenant_id", "consumer_name", "status"],
    )
    op.create_index(
        "idx_consumer_checkpoint_event",
        "event_consumer_checkpoints",
        ["event_id"],
    )

    # 3. event_dead_letters
    op.create_table(
        "event_dead_letters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "event_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workflow_outbox_events.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("event_type", sa.String(64), nullable=False, index=True),
        sa.Column("consumer_name", sa.String(64), nullable=True),
        sa.Column("failure_reason", sa.String(255), nullable=False),
        sa.Column("error_details_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "first_failed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "last_failed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("is_resolved", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "resolved_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()
        ),
    )
    op.create_index(
        "idx_event_dlq_tenant_resolved",
        "event_dead_letters",
        ["tenant_id", "is_resolved"],
    )
    op.create_index(
        "idx_event_dlq_tenant_type",
        "event_dead_letters",
        ["tenant_id", "event_type"],
    )
    op.create_index(
        "idx_event_dlq_event",
        "event_dead_letters",
        ["event_id"],
    )


def downgrade() -> None:
    # 3. Drop event_dead_letters
    op.drop_index("idx_event_dlq_event", table_name="event_dead_letters")
    op.drop_index("idx_event_dlq_tenant_type", table_name="event_dead_letters")
    op.drop_index("idx_event_dlq_tenant_resolved", table_name="event_dead_letters")
    op.drop_table("event_dead_letters")

    # 2. Drop event_consumer_checkpoints
    op.drop_index("idx_consumer_checkpoint_event", table_name="event_consumer_checkpoints")
    op.drop_index("idx_consumer_checkpoint_tenant_status", table_name="event_consumer_checkpoints")
    op.drop_table("event_consumer_checkpoints")

    # 1. Remove columns from workflow_outbox_events
    op.drop_column("workflow_outbox_events", "metadata_json")
    op.drop_column("workflow_outbox_events", "producer")
    op.drop_column("workflow_outbox_events", "actor_context")
    op.drop_column("workflow_outbox_events", "actor_id")
    op.drop_column("workflow_outbox_events", "causation_id")
    op.drop_column("workflow_outbox_events", "schema_version")
