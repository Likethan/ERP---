"""Enterprise API Platform, Developer Portal & Extensibility Layer Migration.

Revision ID: 008_enterprise_api_platform
Revises: 007_enterprise_integrations
Create Date: 2026-10-07 20:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "008_enterprise_api_platform"
down_revision = "007_enterprise_integrations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. core_developer_applications
    op.create_table(
        "core_developer_applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("application_type", sa.String(32), server_default="INTERNAL", nullable=False),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("status", sa.String(32), server_default="DRAFT", nullable=False),
        sa.Column("environment", sa.String(32), server_default="DEVELOPMENT", nullable=False),
        sa.Column("rate_limit_tier", sa.String(32), server_default="DEFAULT", nullable=False),
        sa.Column("rate_limit_custom", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("quota_tier", sa.String(32), server_default="DEFAULT", nullable=False),
        sa.Column("quota_custom", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("quota_status", sa.String(32), server_default="AVAILABLE", nullable=False),
        sa.Column("allowed_ips", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("callback_urls", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "approved_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approval_notes", sa.Text(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "name", name="uq_dev_app_tenant_name"),
    )
    op.create_index("idx_dev_app_tenant_status", "core_developer_applications", ["tenant_id", "status"])
    op.create_index("idx_dev_app_env", "core_developer_applications", ["environment"])

    # 2. core_application_credentials
    op.create_table(
        "core_application_credentials",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_developer_applications.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("credential_type", sa.String(32), server_default="API_KEY", nullable=False),
        sa.Column("client_id", sa.String(64), unique=True, nullable=False, index=True),
        sa.Column("key_prefix", sa.String(32), nullable=False, index=True),
        sa.Column("secret_hash", sa.String(255), nullable=False),
        sa.Column("environment", sa.String(32), server_default="DEVELOPMENT", nullable=False),
        sa.Column("status", sa.String(32), server_default="ACTIVE", nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("grace_period_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "revoked_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("revocation_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("idx_app_cred_tenant_app", "core_application_credentials", ["tenant_id", "application_id"])
    op.create_index("idx_app_cred_status_env", "core_application_credentials", ["status", "environment"])

    # 3. core_application_scope_grants
    op.create_table(
        "core_application_scope_grants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_developer_applications.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("scope_code", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), server_default="GRANTED", nullable=False),
        sa.Column(
            "granted_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("granted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("application_id", "scope_code", name="uq_app_scope_grant"),
    )
    op.create_index("idx_app_scope_tenant_code", "core_application_scope_grants", ["tenant_id", "scope_code"])

    # 4. core_api_products
    op.create_table(
        "core_api_products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(64), unique=True, nullable=False, index=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("version", sa.String(32), server_default="v1", nullable=False),
        sa.Column("status", sa.String(32), server_default="ACTIVE", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # 5. core_api_operations
    op.create_table(
        "core_api_operations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_api_products.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("method", sa.String(16), nullable=False),
        sa.Column("path", sa.String(255), nullable=False),
        sa.Column("version", sa.String(32), server_default="v1", nullable=False),
        sa.Column("summary", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("scope_required", sa.String(64), nullable=False),
        sa.Column("classification", sa.String(32), server_default="INTERNAL_ONLY", nullable=False),
        sa.Column("rate_limit_policy", sa.String(64), server_default="DEFAULT", nullable=False),
        sa.Column("governance_policy", sa.String(64), server_default="STANDARD", nullable=False),
        sa.Column("status", sa.String(32), server_default="ACTIVE", nullable=False),
        sa.Column("deprecated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sunset_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replacement_path", sa.String(255), nullable=True),
        sa.Column("migration_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("method", "path", "version", name="uq_api_operation_endpoint"),
    )
    op.create_index("idx_api_op_classification_status", "core_api_operations", ["classification", "status"])

    # 6. core_api_changelogs
    op.create_table(
        "core_api_changelogs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("version", sa.String(32), nullable=False, index=True),
        sa.Column("release_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("changes", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("breaking_changes", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("deprecated_operations", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("migration_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 7. core_api_subscriptions
    op.create_table(
        "core_api_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_developer_applications.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("product_code", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), server_default="ACTIVE", nullable=False),
        sa.Column("subscribed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("application_id", "product_code", name="uq_app_product_sub"),
    )
    op.create_index("idx_api_sub_tenant_product", "core_api_subscriptions", ["tenant_id", "product_code"])

    # 8. core_api_quotas
    op.create_table(
        "core_api_quotas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_developer_applications.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("period", sa.String(32), nullable=False),
        sa.Column("period_type", sa.String(16), nullable=False),
        sa.Column("requests_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("data_exports_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("webhook_deliveries_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", sa.String(32), server_default="AVAILABLE", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "application_id", "period", "period_type", name="uq_api_quota_tracking"),
    )
    op.create_index("idx_api_quota_tenant_period", "core_api_quotas", ["tenant_id", "period"])

    # 9. core_api_usage_records
    op.create_table(
        "core_api_usage_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_developer_applications.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("credential_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("api_operation", sa.String(255), nullable=False),
        sa.Column("method", sa.String(16), nullable=False),
        sa.Column("path", sa.String(255), nullable=False),
        sa.Column("version", sa.String(32), server_default="v1", nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("latency_ms", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("request_size_bytes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("response_size_bytes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("rate_limited", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("quota_consumed", sa.Integer(), server_default="1", nullable=False),
        sa.Column("correlation_id", sa.String(128), nullable=True),
        sa.Column("client_ip", sa.String(64), nullable=True),
        sa.Column("user_agent", sa.String(255), nullable=True),
    )
    op.create_index("idx_usage_tenant_app_time", "core_api_usage_records", ["tenant_id", "application_id", "timestamp"])
    op.create_index("idx_usage_op_time", "core_api_usage_records", ["api_operation", "timestamp"])

    # 10. core_api_idempotency
    op.create_table(
        "core_api_idempotency",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_developer_applications.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("endpoint", sa.String(255), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), server_default="PROCESSING", nullable=False),
        sa.Column("response_code", sa.Integer(), nullable=True),
        sa.Column("response_body", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "application_id", "idempotency_key", name="uq_api_idempotency_key"),
    )
    op.create_index("idx_idempotency_expiry", "core_api_idempotency", ["expires_at"])

    # 11. core_application_approval_audits
    op.create_table(
        "core_application_approval_audits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_developer_applications.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "reviewer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("previous_status", sa.String(32), nullable=False),
        sa.Column("new_status", sa.String(32), nullable=False),
    )
    op.create_index("idx_app_approval_app_time", "core_application_approval_audits", ["application_id", "reviewed_at"])


def downgrade() -> None:
    op.drop_table("core_application_approval_audits")
    op.drop_table("core_api_idempotency")
    op.drop_table("core_api_usage_records")
    op.drop_table("core_api_quotas")
    op.drop_table("core_api_subscriptions")
    op.drop_table("core_api_changelogs")
    op.drop_table("core_api_operations")
    op.drop_table("core_api_products")
    op.drop_table("core_application_scope_grants")
    op.drop_table("core_application_credentials")
    op.drop_table("core_developer_applications")
