"""Enterprise Customer Success, Subscription Lifecycle & SaaS Entitlements Migration (Step 38).

Revision ID: 024_enterprise_customer_success_subscription_lifecycle
Revises: 023_enterprise_product_adoption_training_guidance
Create Date: 2026-10-18 13:00:00.000000

Creates normalized tables for:
- subscription_plans: SaaS packaging tiers, pricing, resource limits, and included modules
- subscription_tenant_subscriptions: tenant commercial subscriptions and period snapshots
- subscription_lifecycle_histories: state transitions audit log
- subscription_entitlement_overrides: time-limited authorized capability overrides
- subscription_usage_events: idempotent raw metered consumption events
- subscription_usage_aggregates: billing cycle aggregated usage counters
- subscription_invoices: commercial SaaS billing invoices
- subscription_payment_attempts: transaction logs for invoice payments
- subscription_webhook_events: idempotent verified gateway callback records
- subscription_change_requests: plan upgrade/downgrade requests with impact analysis
- customer_success_health_snapshots: telemetry-backed composite health scores
- customer_success_notes: platform-internal CS journal and interaction records
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "024_enterprise_customer_success_subscription_lifecycle"
down_revision = "023_enterprise_product_adoption_training_guidance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Subscription Plans
    op.create_table(
        "subscription_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE", index=True),
        sa.Column("billing_interval", sa.String(32), nullable=False, server_default="ANNUAL", index=True),
        sa.Column("currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column("base_price", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("trial_eligible", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("trial_duration_days", sa.Integer(), nullable=False, server_default="14"),
        sa.Column("max_active_users", sa.Integer(), nullable=False, server_default="500"),
        sa.Column("max_students", sa.Integer(), nullable=False, server_default="5000"),
        sa.Column("max_faculty", sa.Integer(), nullable=False, server_default="250"),
        sa.Column("max_storage_bytes", sa.BigInteger(), nullable=False, server_default="107374182400"),
        sa.Column("max_api_rpm", sa.Integer(), nullable=False, server_default="300"),
        sa.Column("max_ai_tokens_monthly", sa.BigInteger(), nullable=False, server_default="1000000"),
        sa.Column("max_integrations", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("included_modules", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("feature_capabilities", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("support_tier", sa.String(64), nullable=False, server_default="STANDARD"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("effective_from", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # 2. Tenant Subscriptions
    op.create_table(
        "subscription_tenant_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("subscription_plans.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("plan_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(32), nullable=False, server_default="TRIAL_ACTIVE", index=True),
        sa.Column("billing_interval", sa.String(32), nullable=False, server_default="ANNUAL"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("current_period_start", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("trial_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("grace_period_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancellation_effective_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("auto_renew", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("payment_method_id", sa.String(128), nullable=True),
        sa.Column("snapshot_limits_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("snapshot_modules_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("snapshot_features_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index(
        "idx_tenant_sub_status",
        "subscription_tenant_subscriptions",
        ["tenant_id", "status"],
    )

    # 3. Subscription Lifecycle Histories
    op.create_table(
        "subscription_lifecycle_histories",
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
            sa.ForeignKey("subscription_tenant_subscriptions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("from_status", sa.String(32), nullable=False),
        sa.Column("to_status", sa.String(32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "actor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("actor_email", sa.String(255), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # 4. Entitlement Overrides
    op.create_table(
        "subscription_entitlement_overrides",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("override_type", sa.String(32), nullable=False, server_default="CAPABILITY"),
        sa.Column("target_key", sa.String(128), nullable=False),
        sa.Column("override_value_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "granted_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("starts_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index(
        "idx_ent_override_tenant_target",
        "subscription_entitlement_overrides",
        ["tenant_id", "target_key"],
    )
    op.create_index(
        "idx_ent_override_expiry",
        "subscription_entitlement_overrides",
        ["expires_at", "is_active"],
    )

    # 5. Usage Events
    op.create_table(
        "subscription_usage_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("resource_type", sa.String(64), nullable=False),
        sa.Column("quantity", sa.BigInteger(), nullable=False, server_default="1"),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("measured_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
        sa.Column("source_subsystem", sa.String(64), nullable=False, server_default="API"),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_sub_usage_event_idempotency"),
    )
    op.create_index(
        "idx_sub_usage_tenant_res",
        "subscription_usage_events",
        ["tenant_id", "resource_type"],
    )

    # 6. Usage Aggregates
    op.create_table(
        "subscription_usage_aggregates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("resource_type", sa.String(64), nullable=False),
        sa.Column("billing_cycle", sa.String(16), nullable=False),
        sa.Column("current_usage", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("soft_limit", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("hard_limit", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("is_exceeded", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("overage_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "resource_type", "billing_cycle", name="uq_sub_usage_cycle"),
    )
    op.create_index(
        "idx_sub_usage_agg_tenant",
        "subscription_usage_aggregates",
        ["tenant_id", "billing_cycle"],
    )

    # 7. Invoices
    op.create_table(
        "subscription_invoices",
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
            sa.ForeignKey("subscription_tenant_subscriptions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("invoice_number", sa.String(64), nullable=False, unique=True),
        sa.Column("billing_period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("billing_period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False),
        sa.Column("tax_amount", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column("status", sa.String(32), nullable=False, server_default="ISSUED", index=True),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("line_items_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("download_url", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index(
        "idx_sub_inv_period",
        "subscription_invoices",
        ["billing_period_start", "billing_period_end"],
    )

    # 8. Payment Attempts
    op.create_table(
        "subscription_payment_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "invoice_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("subscription_invoices.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("gateway_order_id", sa.String(128), nullable=False),
        sa.Column("gateway_payment_id", sa.String(128), nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING", index=True),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("attempted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index(
        "idx_sub_pay_gateway",
        "subscription_payment_attempts",
        ["gateway_order_id", "gateway_payment_id"],
    )

    # 9. Webhook Events
    op.create_table(
        "subscription_webhook_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_id", sa.String(128), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("signature", sa.String(255), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("status", sa.String(32), nullable=False, server_default="PROCESSED", index=True),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("processed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("provider", "event_id", name="uq_sub_webhook_provider_event"),
    )

    # 10. Plan Change Requests
    op.create_table(
        "subscription_change_requests",
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
            sa.ForeignKey("subscription_tenant_subscriptions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "target_plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("subscription_plans.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("target_billing_interval", sa.String(32), nullable=False),
        sa.Column("change_type", sa.String(32), nullable=False, server_default="UPGRADE"),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING_APPROVAL", index=True),
        sa.Column("effective_type", sa.String(32), nullable=False, server_default="PERIOD_END"),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
        sa.Column("impact_summary_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("prorated_amount", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
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
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # 11. Customer Success Health Snapshots
    op.create_table(
        "customer_success_health_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("health_score", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("health_status", sa.String(32), nullable=False, server_default="HEALTHY", index=True),
        sa.Column("utilization_score", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("adoption_score", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("support_score", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("financial_score", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("signals_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("recommendations", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("calculated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # 12. Customer Success Notes
    op.create_table(
        "customer_success_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "author_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("author_email", sa.String(255), nullable=False),
        sa.Column("note_type", sa.String(32), nullable=False, server_default="GENERAL"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("customer_success_notes")
    op.drop_table("customer_success_health_snapshots")
    op.drop_table("subscription_change_requests")
    op.drop_table("subscription_webhook_events")
    op.drop_table("subscription_payment_attempts")
    op.drop_table("subscription_invoices")
    op.drop_table("subscription_usage_aggregates")
    op.drop_table("subscription_usage_events")
    op.drop_table("subscription_entitlement_overrides")
    op.drop_table("subscription_lifecycle_histories")
    op.drop_table("subscription_tenant_subscriptions")
    op.drop_table("subscription_plans")
