"""Enterprise Marketplace, App Integrations & Extensibility Ecosystem (Step 39).

Revision ID: 025_enterprise_marketplace_app_integrations
Revises: 024_enterprise_customer_success_subscription_lifecycle
Create Date: 2026-10-18 13:30:00.000000

Creates normalized tables for:
- marketplace_apps: Approved and governed integration catalog definitions
- marketplace_app_versions: Versioned metadata and compatibility schemas
- tenant_app_installations: Tenant-scoped connected integration instances
- tenant_app_installation_lifecycles: Audit log of connection state transitions
- integration_sync_checkpoints: Resumable sync cursors and watermark timestamps
- integration_data_conflicts: Detected sync collisions and dispute resolution state
- marketplace_sync_runs: Telemetry and execution metrics for integration runs
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "025_enterprise_marketplace_app_integrations"
down_revision = "024_enterprise_customer_success_subscription_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Marketplace Apps Catalog
    op.create_table(
        "marketplace_apps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("category", sa.String(48), nullable=False, index=True),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("provider_name", sa.String(128), nullable=False),
        sa.Column("provider_url", sa.String(256), nullable=True),
        sa.Column("provider_email", sa.String(256), nullable=True),
        sa.Column("icon_url", sa.String(512), nullable=True),
        sa.Column("supported_modules", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("required_scopes", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("connection_method", sa.String(32), nullable=False, server_default="API_KEY"),
        sa.Column("config_schema", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("supported_capabilities", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("documentation_url", sa.String(512), nullable=True),
        sa.Column("setup_instructions", sa.Text(), nullable=False, server_default=""),
        sa.Column("min_platform_version", sa.String(32), nullable=False, server_default="1.0.0"),
        sa.Column("required_entitlements", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("publication_status", sa.String(32), nullable=False, server_default="DRAFT", index=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deprecation_notice", sa.Text(), nullable=True),
        sa.Column("deprecated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # 2. Marketplace App Versions
    op.create_table(
        "marketplace_app_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("app_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("marketplace_apps.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("version", sa.String(32), nullable=False),
        sa.Column("changelog", sa.Text(), nullable=False, server_default=""),
        sa.Column("config_schema", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("supported_capabilities", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("publication_status", sa.String(32), nullable=False, server_default="APPROVED", index=True),
        sa.Column("released_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("is_latest", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("app_id", "version", name="uq_marketplace_app_version"),
    )

    # 3. Tenant App Installations
    op.create_table(
        "tenant_app_installations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("app_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("marketplace_apps.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("app_version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("marketplace_app_versions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("display_name", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="NOT_CONNECTED", index=True),
        sa.Column("connection_method", sa.String(32), nullable=False, server_default="API_KEY"),
        sa.Column("enabled_capabilities", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("authorized_scopes", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("configuration", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}" ),
        sa.Column("field_mappings", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}" ),
        sa.Column("sync_direction", sa.String(32), nullable=False, server_default="BIDIRECTIONAL"),
        sa.Column("conflict_policy", sa.String(32), nullable=False, server_default="CAMPUSOS_AUTHORITATIVE"),
        sa.Column("credential_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("integration_credentials.id", ondelete="SET NULL"), nullable=True),
        sa.Column("oauth_state", sa.String(128), nullable=True),
        sa.Column("oauth_state_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("webhook_secret", sa.String(128), nullable=True),
        sa.Column("health_status", sa.String(32), nullable=False, server_default="UNKNOWN"),
        sa.Column("health_details", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}" ),
        sa.Column("last_health_check_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consecutive_failure_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_successful_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_summary", sa.Text(), nullable=True),
        sa.Column("connected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("disconnected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("installed_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "app_id", name="uq_tenant_marketplace_app"),
    )

    # 4. Tenant App Installation Lifecycle Audit
    op.create_table(
        "tenant_app_installation_lifecycles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("installation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenant_app_installations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("from_status", sa.String(32), nullable=True),
        sa.Column("to_status", sa.String(32), nullable=False, index=True),
        sa.Column("reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("triggered_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("metadata_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}" ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 5. Integration Sync Checkpoints
    op.create_table(
        "integration_sync_checkpoints",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("installation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenant_app_installations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("cursor_position", sa.String(256), nullable=True),
        sa.Column("last_sync_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("checkpoint_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}" ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("installation_id", "entity_type", name="uq_installation_entity_checkpoint"),
    )

    # 6. Integration Data Conflicts
    op.create_table(
        "integration_data_conflicts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("installation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenant_app_installations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("entity_type", sa.String(64), nullable=False, index=True),
        sa.Column("record_identifier", sa.String(128), nullable=False, index=True),
        sa.Column("campusos_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}" ),
        sa.Column("provider_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}" ),
        sa.Column("conflicting_fields", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("applied_resolution", sa.String(48), nullable=False, server_default="MANUAL_REVIEW"),
        sa.Column("resolved_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}" ),
        sa.Column("resolved_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="OPEN", index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # 7. Marketplace Sync Runs
    op.create_table(
        "marketplace_sync_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("installation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenant_app_installations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("trigger_type", sa.String(32), nullable=False, server_default="MANUAL", index=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING", index=True),
        sa.Column("records_fetched", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_created", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_updated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_skipped", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("execution_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}" ),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("marketplace_sync_runs")
    op.drop_table("integration_data_conflicts")
    op.drop_table("integration_sync_checkpoints")
    op.drop_table("tenant_app_installation_lifecycles")
    op.drop_table("tenant_app_installations")
    op.drop_table("marketplace_app_versions")
    op.drop_table("marketplace_apps")
