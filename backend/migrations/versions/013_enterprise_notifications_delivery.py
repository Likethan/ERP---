"""Enterprise Notification, Communication & Delivery Orchestration Layer Migration (Step 26).

Revision ID: 013_enterprise_notifications_delivery
Revises: 012_enterprise_case_management_hitl
Create Date: 2026-10-09 18:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "013_enterprise_notifications_delivery"
down_revision = "012_enterprise_case_management_hitl"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. notification_events
    op.create_table(
        "notification_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("event_type", sa.String(128), nullable=False, index=True),
        sa.Column("source_module", sa.String(64), nullable=False, index=True),
        sa.Column("source_entity_id", sa.String(128), nullable=True),
        sa.Column("source_entity_type", sa.String(64), nullable=True),
        sa.Column("correlation_id", sa.String(128), nullable=True, index=True),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("recipient_context_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("sensitivity", sa.String(32), nullable=False, server_default="INTERNAL"),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index(
        "idx_notif_event_tenant_type",
        "notification_events",
        ["tenant_id", "event_type", "created_at"],
    )

    # 2. notification_templates
    op.create_table(
        "notification_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=True,
            index=True,
        ),
        sa.Column("template_key", sa.String(128), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("channel", sa.String(32), nullable=False),
        sa.Column("locale", sa.String(16), nullable=False, server_default="en"),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("tenant_id", "template_key", name="uq_notification_template_tenant_key"),
    )
    op.create_index(
        "idx_notif_template_tenant_channel",
        "notification_templates",
        ["tenant_id", "channel"],
    )

    # 3. notification_template_versions
    op.create_table(
        "notification_template_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("notification_templates.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT"),
        sa.Column("subject_template", sa.String(500), nullable=True),
        sa.Column("body_template", sa.Text(), nullable=False),
        sa.Column("variables_schema_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("sample_payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "published_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("template_id", "version", name="uq_notif_template_version"),
    )
    op.create_index(
        "idx_notif_tmpl_ver_status",
        "notification_template_versions",
        ["template_id", "status"],
    )

    # 4. notification_rules
    op.create_table(
        "notification_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=True,
            index=True,
        ),
        sa.Column("rule_key", sa.String(128), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("event_type", sa.String(128), nullable=False, index=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("module_scope", sa.String(64), nullable=True),
        sa.Column("priority", sa.String(32), nullable=False, server_default="NORMAL"),
        sa.Column("recipient_strategy", sa.String(32), nullable=False, server_default="DIRECT"),
        sa.Column("recipient_config_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("channels_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='["IN_APP"]'),
        sa.Column(
            "template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("notification_templates.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("conditions_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("suppression_policy_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("scheduling_policy_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("tenant_id", "rule_key", name="uq_notification_rule_tenant_key"),
    )
    op.create_index(
        "idx_notif_rule_tenant_event",
        "notification_rules",
        ["tenant_id", "event_type", "is_enabled"],
    )

    # 5. Extend campus_notification_deliveries table
    with op.batch_alter_table("campus_notification_deliveries") as batch_op:
        batch_op.alter_column("notification_id", existing_type=postgresql.UUID(as_uuid=True), nullable=True)
        batch_op.add_column(
            sa.Column(
                "event_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("notification_events.id", ondelete="SET NULL"),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "recipient_user_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("core_users.id", ondelete="CASCADE"),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "template_version_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("notification_template_versions.id", ondelete="SET NULL"),
                nullable=True,
            )
        )
        batch_op.add_column(sa.Column("provider", sa.String(64), nullable=True))
        batch_op.add_column(sa.Column("provider_message_id", sa.String(255), nullable=True))
        batch_op.add_column(sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("failure_classification", sa.String(32), nullable=True))
        batch_op.add_column(sa.Column("correlation_id", sa.String(128), nullable=True))
        batch_op.add_column(sa.Column("idempotency_key", sa.String(255), nullable=True))
        batch_op.add_column(sa.Column("suppression_reason", sa.String(32), nullable=True))
        batch_op.add_column(sa.Column("rendered_subject", sa.String(500), nullable=True))
        batch_op.add_column(sa.Column("rendered_body", sa.Text(), nullable=True))

    op.create_index(
        "idx_notif_delivery_sched",
        "campus_notification_deliveries",
        ["tenant_id", "status", "scheduled_at"],
    )
    op.create_index(
        "idx_notif_delivery_idemp",
        "campus_notification_deliveries",
        ["tenant_id", "idempotency_key"],
    )
    op.create_index(
        "idx_notif_delivery_recipient",
        "campus_notification_deliveries",
        ["tenant_id", "recipient_user_id"],
    )

    # 6. notification_delivery_attempts
    op.create_table(
        "notification_delivery_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "delivery_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("campus_notification_deliveries.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("provider_message_id", sa.String(255), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("is_retryable", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("response_payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_index(
        "idx_delivery_attempt_tenant_deliv",
        "notification_delivery_attempts",
        ["tenant_id", "delivery_id"],
    )

    # 7. notification_provider_configs
    op.create_table(
        "notification_provider_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("provider_key", sa.String(64), nullable=False),
        sa.Column("channel", sa.String(32), nullable=False),
        sa.Column("provider_type", sa.String(64), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("health_status", sa.String(32), nullable=False, server_default="UNKNOWN"),
        sa.Column("last_health_check_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("health_details_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("credentials_vault_ref", sa.String(255), nullable=True),
        sa.Column("webhook_signing_secret", sa.String(255), nullable=True),
        sa.Column("config_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("tenant_id", "provider_key", name="uq_notif_provider_tenant_key"),
    )

    # 8. notification_suppressions
    op.create_table(
        "notification_suppressions",
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
            sa.ForeignKey("core_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("channel", sa.String(32), nullable=False),
        sa.Column("contact_target", sa.String(255), nullable=False),
        sa.Column("reason", sa.String(32), nullable=False),
        sa.Column("source", sa.String(64), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index(
        "idx_notif_suppress_target",
        "notification_suppressions",
        ["tenant_id", "channel", "contact_target"],
    )

    # 9. notification_digest_runs
    op.create_table(
        "notification_digest_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("digest_type", sa.String(32), nullable=False),
        sa.Column(
            "recipient_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("items_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "delivery_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("campus_notification_deliveries.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(32), nullable=False, server_default="GENERATED"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("tenant_id", "digest_type", "recipient_user_id", "period_start", name="uq_digest_run_period"),
    )

    # 10. notification_user_settings
    op.create_table(
        "notification_user_settings",
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
            sa.ForeignKey("core_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("timezone", sa.String(64), nullable=False, server_default="Asia/Kolkata"),
        sa.Column("locale", sa.String(16), nullable=False, server_default="en"),
        sa.Column("quiet_hours_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("quiet_hours_start", sa.String(8), nullable=True),
        sa.Column("quiet_hours_end", sa.String(8), nullable=True),
        sa.Column("daily_digest_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("weekly_digest_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("max_daily_notifications", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("tenant_id", "user_id", name="uq_notif_user_settings"),
    )


def downgrade() -> None:
    op.drop_table("notification_user_settings")
    op.drop_table("notification_digest_runs")
    op.drop_table("notification_suppressions")
    op.drop_table("notification_provider_configs")
    op.drop_table("notification_delivery_attempts")

    with op.batch_alter_table("campus_notification_deliveries") as batch_op:
        batch_op.drop_column("rendered_body")
        batch_op.drop_column("rendered_subject")
        batch_op.drop_column("suppression_reason")
        batch_op.drop_column("idempotency_key")
        batch_op.drop_column("correlation_id")
        batch_op.drop_column("failure_classification")
        batch_op.drop_column("last_attempt_at")
        batch_op.drop_column("attempt_count")
        batch_op.drop_column("scheduled_at")
        batch_op.drop_column("provider_message_id")
        batch_op.drop_column("provider")
        batch_op.drop_column("template_version_id")
        batch_op.drop_column("recipient_user_id")
        batch_op.drop_column("event_id")

    op.drop_table("notification_rules")
    op.drop_table("notification_template_versions")
    op.drop_table("notification_templates")
    op.drop_table("notification_events")
