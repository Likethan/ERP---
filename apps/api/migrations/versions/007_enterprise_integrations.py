"""Enterprise Integration & Interoperability Layer Migration.

Revision ID: 007_enterprise_integrations
Revises: 006_governance_privacy_compliance
Create Date: 2026-10-06 18:30:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "007_enterprise_integrations"
down_revision = "006_governance_privacy_compliance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. integration_credentials
    op.create_table(
        "integration_credentials",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column("ownership_level", sa.String(32), server_default="TENANT", nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("auth_type", sa.String(32), server_default="API_KEY", nullable=False),
        sa.Column("encrypted_data", sa.Text(), nullable=False),
        sa.Column("masked_preview", sa.String(128), nullable=False),
        sa.Column("key_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("idx_int_cred_tenant", "integration_credentials", ["tenant_id"])
    op.create_index("idx_int_cred_ownership", "integration_credentials", ["ownership_level"])

    # 2. integration_connectors
    op.create_table(
        "integration_connectors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column("ownership_level", sa.String(32), server_default="TENANT", nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("provider_key", sa.String(64), nullable=False),
        sa.Column("connector_type", sa.String(32), server_default="REST_API", nullable=False),
        sa.Column("status", sa.String(32), server_default="DRAFT", nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("configuration", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column(
            "credential_reference",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("integration_credentials.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("allowed_domains", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_connector_tenant_code"),
    )
    op.create_index("idx_connector_tenant_status", "integration_connectors", ["tenant_id", "status"])
    op.create_index("idx_connector_provider", "integration_connectors", ["provider_key"])
    op.create_index("idx_connector_ownership", "integration_connectors", ["ownership_level"])

    # 3. integration_health
    op.create_table(
        "integration_health",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "connector_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("integration_connectors.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("status", sa.String(32), server_default="UNKNOWN", nullable=False),
        sa.Column("consecutive_failures", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_latency_ms", sa.Integer(), nullable=True),
        sa.Column("error_rate", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("circuit_state", sa.String(32), server_default="CLOSED", nullable=False),
        sa.Column("circuit_opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("idx_int_health_status", "integration_health", ["status"])
    op.create_index("idx_int_health_connector", "integration_health", ["connector_id"])

    # 4. integration_webhook_subscriptions
    op.create_table(
        "integration_webhook_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "connector_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("integration_connectors.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("endpoint_url", sa.String(512), nullable=False),
        sa.Column("event_types", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("status", sa.String(32), server_default="ACTIVE", nullable=False),
        sa.Column(
            "secret_reference",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("integration_credentials.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("filter_criteria", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("idx_webhook_tenant_status", "integration_webhook_subscriptions", ["tenant_id", "status"])
    op.create_index("idx_webhook_connector", "integration_webhook_subscriptions", ["connector_id"])

    # 5. integration_webhook_deliveries
    op.create_table(
        "integration_webhook_deliveries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "subscription_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("integration_webhook_subscriptions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_id", sa.String(64), nullable=False, index=True),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("status", sa.String(32), server_default="PENDING", nullable=False),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_attempts", sa.Integer(), server_default="5", nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("response_status_code", sa.Integer(), nullable=True),
        sa.Column("response_time_ms", sa.Integer(), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("idempotency_key", sa.String(128), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("idx_delivery_tenant_status", "integration_webhook_deliveries", ["tenant_id", "status"])
    op.create_index("idx_delivery_subscription", "integration_webhook_deliveries", ["subscription_id"])
    op.create_index("idx_delivery_next_attempt", "integration_webhook_deliveries", ["next_attempt_at"])

    # 6. integration_webhook_attempts
    op.create_table(
        "integration_webhook_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "delivery_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("integration_webhook_deliveries.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("response_body_preview", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("attempted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("idx_attempt_delivery", "integration_webhook_attempts", ["delivery_id"])

    # 7. integration_data_mappings
    op.create_table(
        "integration_data_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("source_type", sa.String(64), nullable=False),
        sa.Column("target_type", sa.String(64), nullable=False),
        sa.Column("rules", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "name", name="uq_data_mapping_tenant_name"),
    )
    op.create_index("idx_mapping_tenant", "integration_data_mappings", ["tenant_id"])

    # 8. integration_sync_configs
    op.create_table(
        "integration_sync_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "connector_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("integration_connectors.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("resource_type", sa.String(64), nullable=False),
        sa.Column("direction", sa.String(32), server_default="IMPORT", nullable=False),
        sa.Column(
            "mapping_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("integration_data_mappings.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("conflict_strategy", sa.String(32), server_default="SOURCE_WINS", nullable=False),
        sa.Column("interval_minutes", sa.Integer(), server_default="60", nullable=False),
        sa.Column("status", sa.String(32), server_default="ACTIVE", nullable=False),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("idx_sync_tenant_status", "integration_sync_configs", ["tenant_id", "status"])
    op.create_index("idx_sync_connector", "integration_sync_configs", ["connector_id"])

    # 9. integration_sync_runs
    op.create_table(
        "integration_sync_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "sync_config_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("integration_sync_configs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(32), server_default="QUEUED", nullable=False),
        sa.Column("records_processed", sa.Integer(), server_default="0", nullable=False),
        sa.Column("records_created", sa.Integer(), server_default="0", nullable=False),
        sa.Column("records_updated", sa.Integer(), server_default="0", nullable=False),
        sa.Column("records_skipped", sa.Integer(), server_default="0", nullable=False),
        sa.Column("records_failed", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("idx_sync_run_tenant_status", "integration_sync_runs", ["tenant_id", "status"])
    op.create_index("idx_sync_run_config", "integration_sync_runs", ["sync_config_id"])

    # 10. integration_sync_items
    op.create_table(
        "integration_sync_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "sync_run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("integration_sync_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("external_id", sa.String(128), nullable=False),
        sa.Column("internal_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(32), server_default="SKIPPED", nullable=False),
        sa.Column("status", sa.String(32), server_default="SUCCESS", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("idx_sync_item_run", "integration_sync_items", ["sync_run_id"])

    # 11. integration_external_resource_mappings
    op.create_table(
        "integration_external_resource_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "connector_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("integration_connectors.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("external_resource_type", sa.String(64), nullable=False),
        sa.Column("external_id", sa.String(128), nullable=False),
        sa.Column("internal_resource_type", sa.String(64), nullable=False),
        sa.Column("internal_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "tenant_id",
            "connector_id",
            "external_resource_type",
            "external_id",
            name="uq_ext_mapping_unique_remote",
        ),
    )
    op.create_index("idx_ext_mapping_internal", "integration_external_resource_mappings", ["tenant_id", "internal_resource_type", "internal_id"])
    op.create_index("idx_ext_mapping_connector", "integration_external_resource_mappings", ["connector_id"])

    # 12. integration_logs
    op.create_table(
        "integration_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "connector_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("integration_connectors.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("operation", sa.String(64), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=True),
        sa.Column("request_id", sa.String(64), nullable=False),
        sa.Column("correlation_id", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), server_default="SUCCESS", nullable=False),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("idx_int_log_tenant_created", "integration_logs", ["tenant_id", "created_at"])
    op.create_index("idx_int_log_connector", "integration_logs", ["connector_id"])
    op.create_index("idx_int_log_correlation", "integration_logs", ["correlation_id"])

    # 13. integration_idempotency_keys
    op.create_table(
        "integration_idempotency_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column("scope", sa.String(64), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), server_default="PROCESSING", nullable=False),
        sa.Column("response_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "scope", "idempotency_key", name="uq_int_idempotency_key"),
    )
    op.create_index("idx_int_idemp_expires", "integration_idempotency_keys", ["expires_at"])


def downgrade() -> None:
    op.drop_table("integration_idempotency_keys")
    op.drop_table("integration_logs")
    op.drop_table("integration_external_resource_mappings")
    op.drop_table("integration_sync_items")
    op.drop_table("integration_sync_runs")
    op.drop_table("integration_sync_configs")
    op.drop_table("integration_data_mappings")
    op.drop_table("integration_webhook_attempts")
    op.drop_table("integration_webhook_deliveries")
    op.drop_table("integration_webhook_subscriptions")
    op.drop_table("integration_health")
    op.drop_table("integration_connectors")
    op.drop_table("integration_credentials")
