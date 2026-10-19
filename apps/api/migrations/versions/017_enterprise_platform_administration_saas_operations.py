"""Enterprise Platform Administration, SaaS Operations & Tenant Lifecycle Management Migration (Step 30).

Revision ID: 017_enterprise_platform_administration_saas_operations
Revises: 016_enterprise_ai_governance_intelligence
Create Date: 2026-10-14 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "017_enterprise_platform_administration_saas_operations"
down_revision = "016_enterprise_ai_governance_intelligence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create platform_tenant_lifecycle_transitions
    op.create_table(
        "platform_tenant_lifecycle_transitions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("from_status", sa.String(32), nullable=False),
        sa.Column("to_status", sa.String(32), nullable=False),
        sa.Column(
            "actor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("actor_email", sa.String(255), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "idx_lifecycle_trans_tenant",
        "platform_tenant_lifecycle_transitions",
        ["tenant_id"],
    )
    op.create_index(
        "idx_lifecycle_trans_status",
        "platform_tenant_lifecycle_transitions",
        ["from_status", "to_status"],
    )
    op.create_index(
        "idx_lifecycle_trans_created",
        "platform_tenant_lifecycle_transitions",
        ["created_at"],
    )

    # 2. Create platform_tenant_provisioning_operations
    op.create_table(
        "platform_tenant_provisioning_operations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("stage", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("details_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("tenant_id", "stage", name="uq_tenant_provision_stage"),
    )
    op.create_index(
        "idx_tenant_prov_status",
        "platform_tenant_provisioning_operations",
        ["tenant_id", "status"],
    )

    # 3. Create platform_tenant_entitlements
    op.create_table(
        "platform_tenant_entitlements",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
            index=True,
        ),
        sa.Column("plan", sa.String(32), nullable=False, server_default="ENTERPRISE"),
        sa.Column("max_users", sa.Integer(), nullable=False, server_default="10000"),
        sa.Column("max_campuses", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("max_storage_bytes", sa.BigInteger(), nullable=False, server_default="107374182400"),
        sa.Column("max_api_rpm", sa.Integer(), nullable=False, server_default="300"),
        sa.Column("max_ai_tokens_monthly", sa.BigInteger(), nullable=False, server_default="1000000"),
        sa.Column("enabled_modules", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("feature_entitlements", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("is_trial", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("grace_period_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("custom_limits", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column(
            "updated_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "idx_tenant_entitlement_plan",
        "platform_tenant_entitlements",
        ["plan"],
    )
    op.create_index(
        "idx_tenant_entitlement_trial",
        "platform_tenant_entitlements",
        ["is_trial", "trial_ends_at"],
    )

    # 4. Create platform_tenant_quota_usage
    op.create_table(
        "platform_tenant_quota_usage",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("resource_type", sa.String(64), nullable=False),
        sa.Column("current_usage", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("soft_limit", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("hard_limit", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("unit", sa.String(32), nullable=False, server_default="COUNT"),
        sa.Column("warning_threshold_percent", sa.Integer(), nullable=False, server_default="80"),
        sa.Column(
            "period_start",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_exceeded", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("warning_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("tenant_id", "resource_type", name="uq_tenant_resource_quota"),
    )
    op.create_index(
        "idx_quota_usage_tenant_res",
        "platform_tenant_quota_usage",
        ["tenant_id", "resource_type"],
    )
    op.create_index(
        "idx_quota_usage_exceeded",
        "platform_tenant_quota_usage",
        ["is_exceeded"],
    )

    # 5. Create platform_support_access_sessions
    op.create_table(
        "platform_support_access_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "operator_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("ticket_reference", sa.String(128), nullable=True),
        sa.Column("permissions_scope", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "revoked_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("revocation_reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "idx_support_sess_tenant_active",
        "platform_support_access_sessions",
        ["tenant_id", "is_active"],
    )
    op.create_index(
        "idx_support_sess_expires",
        "platform_support_access_sessions",
        ["expires_at"],
    )
    op.create_index(
        "idx_support_sess_operator",
        "platform_support_access_sessions",
        ["operator_user_id"],
    )

    # 6. Create platform_tenant_deletion_plans
    op.create_table(
        "platform_tenant_deletion_plans",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("status", sa.String(32), nullable=False, server_default="PROPOSED"),
        sa.Column(
            "requested_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "approved_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("retention_clearance", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("legal_holds_clearance", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("financial_clearance", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("export_completed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("blocking_reasons", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("impact_summary_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("scheduled_deletion_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "idx_del_plan_tenant_status",
        "platform_tenant_deletion_plans",
        ["tenant_id", "status"],
    )


def downgrade() -> None:
    op.drop_table("platform_tenant_deletion_plans")
    op.drop_table("platform_support_access_sessions")
    op.drop_table("platform_tenant_quota_usage")
    op.drop_table("platform_tenant_entitlements")
    op.drop_table("platform_tenant_provisioning_operations")
    op.drop_table("platform_tenant_lifecycle_transitions")
