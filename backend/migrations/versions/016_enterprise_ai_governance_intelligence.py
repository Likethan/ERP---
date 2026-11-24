"""Enterprise AI Governance, Predictive Intelligence & Decision Support Engine Migration (Step 29).

Revision ID: 016_enterprise_ai_governance_intelligence
Revises: 015_enterprise_data_platform_analytics
Create Date: 2026-10-09 21:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "016_enterprise_ai_governance_intelligence"
down_revision = "015_enterprise_data_platform_analytics"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create intelligence_governance_policies
    op.create_table(
        "intelligence_governance_policies",
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
        sa.Column("policy_name", sa.String(128), nullable=False, server_default="DEFAULT_INSTITUTIONAL_POLICY"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("allowed_providers", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("allowed_models", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("permitted_use_cases", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("prohibited_use_cases", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("max_context_tokens", sa.Integer(), nullable=False, server_default="4096"),
        sa.Column("max_output_tokens", sa.Integer(), nullable=False, server_default="2048"),
        sa.Column("daily_budget_usd", sa.Numeric(10, 2), nullable=False, server_default="50.00"),
        sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("enforce_prompt_guard", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_intel_gov_tenant_active",
        "intelligence_governance_policies",
        ["tenant_id", "is_active"],
    )

    # 2. Create intelligence_predictions
    op.create_table(
        "intelligence_predictions",
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
        sa.Column("prediction_id", sa.String(100), nullable=False, index=True),
        sa.Column("prediction_type", sa.String(64), nullable=False),
        sa.Column("target_type", sa.String(32), nullable=False),
        sa.Column("target_id", sa.String(128), nullable=False, index=True),
        sa.Column("model_name", sa.String(128), nullable=False),
        sa.Column("model_version", sa.String(32), nullable=False),
        sa.Column("is_rule_based", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("prediction_score", sa.Numeric(8, 4), nullable=False),
        sa.Column("risk_level", sa.String(32), nullable=False),
        sa.Column("signals", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("limitations", sa.Text(), nullable=True),
        sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING_REVIEW"),
        sa.Column(
            "reviewed_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_intel_pred_tenant_target",
        "intelligence_predictions",
        ["tenant_id", "target_type", "target_id"],
    )
    op.create_index(
        "idx_intel_pred_tenant_status",
        "intelligence_predictions",
        ["tenant_id", "status"],
    )
    op.create_index(
        "idx_intel_pred_tenant_risk",
        "intelligence_predictions",
        ["tenant_id", "risk_level"],
    )

    # 3. Create intelligence_recommendations
    op.create_table(
        "intelligence_recommendations",
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
        sa.Column("recommendation_id", sa.String(100), nullable=False, index=True),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("domain", sa.String(32), nullable=False),
        sa.Column("priority", sa.String(32), nullable=False, server_default="MEDIUM"),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("reasoning_summary", sa.Text(), nullable=False),
        sa.Column("supporting_evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("metric_references", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("suggested_action", sa.Text(), nullable=False),
        sa.Column("suggested_action_type", sa.String(64), nullable=False, server_default="NOTIFY_ADVISOR"),
        sa.Column("status", sa.String(32), nullable=False, server_default="PROPOSED"),
        sa.Column("workflow_case_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "reviewed_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_intel_rec_tenant_status",
        "intelligence_recommendations",
        ["tenant_id", "status"],
    )
    op.create_index(
        "idx_intel_rec_tenant_category",
        "intelligence_recommendations",
        ["tenant_id", "category"],
    )

    # 4. Create intelligence_evaluation_runs
    op.create_table(
        "intelligence_evaluation_runs",
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
        sa.Column("suite_name", sa.String(128), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("model", sa.String(128), nullable=False),
        sa.Column("total_cases", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("passed_cases", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_cases", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("score_pct", sa.Numeric(6, 2), nullable=False, server_default="0.0"),
        sa.Column("groundedness_score", sa.Numeric(6, 2), nullable=False, server_default="0.0"),
        sa.Column("injection_resistance_score", sa.Numeric(6, 2), nullable=False, server_default="0.0"),
        sa.Column("schema_compliance_score", sa.Numeric(6, 2), nullable=False, server_default="0.0"),
        sa.Column("results_detail", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="PASSED"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_intel_eval_tenant_suite",
        "intelligence_evaluation_runs",
        ["tenant_id", "suite_name"],
    )

    # 5. Create intelligence_usage_records
    op.create_table(
        "intelligence_usage_records",
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
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("request_id", sa.String(100), nullable=False, index=True),
        sa.Column("use_case", sa.String(64), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("model", sa.String(128), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_cost_usd", sa.Numeric(10, 4), nullable=False, server_default="0.0000"),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(32), nullable=False, server_default="SUCCESS"),
        sa.Column("error_reason", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_intel_usage_tenant_user",
        "intelligence_usage_records",
        ["tenant_id", "user_id"],
    )
    op.create_index(
        "idx_intel_usage_tenant_created",
        "intelligence_usage_records",
        ["tenant_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_table("intelligence_usage_records")
    op.drop_table("intelligence_evaluation_runs")
    op.drop_table("intelligence_recommendations")
    op.drop_table("intelligence_predictions")
    op.drop_table("intelligence_governance_policies")
