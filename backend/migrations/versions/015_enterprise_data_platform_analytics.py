"""Enterprise Data Platform, Real-Time Analytics & Business Intelligence Engine Migration (Step 28).

Revision ID: 015_enterprise_data_platform_analytics
Revises: 014_domain_event_backbone_and_consumers
Create Date: 2026-10-09 20:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "015_enterprise_data_platform_analytics"
down_revision = "014_domain_event_backbone_and_consumers"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create analytics_daily_metrics
    op.create_table(
        "analytics_daily_metrics",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("metric_id", sa.String(64), nullable=False, index=True),
        sa.Column("metric_date", sa.Date(), nullable=False, index=True),
        sa.Column("dimension_type", sa.String(64), nullable=False, server_default="GLOBAL"),
        sa.Column("dimension_value", sa.String(128), nullable=False, server_default="ALL"),
        sa.Column("value_numeric", sa.Numeric(18, 4), nullable=False, server_default="0.0000"),
        sa.Column("record_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "metric_id",
            "metric_date",
            "dimension_type",
            "dimension_value",
            name="uq_analytics_daily_metric_slot",
        ),
    )
    op.create_index(
        "ix_analytics_daily_tenant_metric_date",
        "analytics_daily_metrics",
        ["tenant_id", "metric_id", "metric_date"],
    )
    op.create_index(
        "ix_analytics_daily_dimension",
        "analytics_daily_metrics",
        ["tenant_id", "dimension_type", "dimension_value"],
    )

    # 2. Create analytics_metric_freshness
    op.create_table(
        "analytics_metric_freshness",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("metric_id", sa.String(64), nullable=False, index=True),
        sa.Column(
            "last_ingested_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "last_recalculated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("ingestion_lag_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source_event_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(32), nullable=False, server_default="FRESH"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("tenant_id", "metric_id", name="uq_analytics_metric_freshness"),
    )
    op.create_index(
        "ix_analytics_freshness_tenant_status",
        "analytics_metric_freshness",
        ["tenant_id", "status"],
    )

    # 3. Create analytics_reconciliation_findings
    op.create_table(
        "analytics_reconciliation_findings",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("rule_code", sa.String(64), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False, server_default="WARNING"),
        sa.Column("metric_id", sa.String(64), nullable=False),
        sa.Column("source_table", sa.String(64), nullable=False),
        sa.Column("operational_value", sa.Numeric(18, 4), nullable=True),
        sa.Column("analytics_value", sa.Numeric(18, 4), nullable=True),
        sa.Column("discrepancy_delta", sa.Numeric(18, 4), nullable=True),
        sa.Column(
            "details_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("resolution_status", sa.String(32), nullable=False, server_default="OPEN"),
        sa.Column(
            "detected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index(
        "ix_analytics_recon_tenant_severity",
        "analytics_reconciliation_findings",
        ["tenant_id", "severity"],
    )
    op.create_index(
        "ix_analytics_recon_tenant_status",
        "analytics_reconciliation_findings",
        ["tenant_id", "resolution_status"],
    )
    op.create_index(
        "ix_analytics_recon_rule_detected",
        "analytics_reconciliation_findings",
        ["tenant_id", "rule_code", "detected_at"],
    )


def downgrade() -> None:
    # 3. Drop analytics_reconciliation_findings
    op.drop_index(
        "ix_analytics_recon_rule_detected", table_name="analytics_reconciliation_findings"
    )
    op.drop_index(
        "ix_analytics_recon_tenant_status", table_name="analytics_reconciliation_findings"
    )
    op.drop_index(
        "ix_analytics_recon_tenant_severity", table_name="analytics_reconciliation_findings"
    )
    op.drop_table("analytics_reconciliation_findings")

    # 2. Drop analytics_metric_freshness
    op.drop_index("ix_analytics_freshness_tenant_status", table_name="analytics_metric_freshness")
    op.drop_table("analytics_metric_freshness")

    # 1. Drop analytics_daily_metrics
    op.drop_index("ix_analytics_daily_dimension", table_name="analytics_daily_metrics")
    op.drop_index("ix_analytics_daily_tenant_metric_date", table_name="analytics_daily_metrics")
    op.drop_table("analytics_daily_metrics")
