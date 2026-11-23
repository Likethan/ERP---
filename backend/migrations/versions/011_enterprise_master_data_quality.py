"""Enterprise Master Data Management & Data Quality Layer Migration.

Revision ID: 011_enterprise_master_data_quality
Revises: 010_enterprise_admin_configuration_policy
Create Date: 2026-10-08 20:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "011_enterprise_master_data_quality"
down_revision = "010_enterprise_admin_configuration_policy"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. master_data_definitions
    op.create_table(
        "master_data_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("key", sa.String(64), unique=True, nullable=False, index=True),
        sa.Column("display_name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("owner_domain", sa.String(64), nullable=False),
        sa.Column(
            "steward_role", sa.String(64), nullable=False, server_default="INSTITUTION_ADMIN"
        ),
        sa.Column("sensitivity", sa.String(32), nullable=False, server_default="INTERNAL"),
        sa.Column(
            "duplicate_detection_enabled", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column("merge_supported", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("archival_supported", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("authoritative_source", sa.String(128), nullable=False),
        sa.Column("canonical_table_name", sa.String(128), nullable=False),
        sa.Column("canonical_id_column", sa.String(64), nullable=False, server_default="id"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )

    # 2. reference_data_definitions
    op.create_table(
        "reference_data_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("category", sa.String(64), unique=True, nullable=False, index=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )

    # 3. reference_data_values
    op.create_table(
        "reference_data_values",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("label", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=True),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("tenant_id", "category", "code", name="uq_ref_val_tenant_cat_code"),
    )
    op.create_index("idx_ref_val_tenant_cat", "reference_data_values", ["tenant_id", "category"])

    # 4. data_quality_rules
    op.create_table(
        "data_quality_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("master_type", sa.String(64), nullable=False),
        sa.Column("rule_key", sa.String(128), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("field_name", sa.String(64), nullable=True),
        sa.Column("rule_type", sa.String(32), nullable=False, server_default="REQUIRED"),
        sa.Column("severity", sa.String(32), nullable=False, server_default="ERROR"),
        sa.Column("parameters_json", postgresql.JSONB(), nullable=True),
        sa.Column("weight", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("tenant_id", "rule_key", name="uq_quality_rule_tenant_key"),
    )
    op.create_index(
        "idx_quality_rule_tenant_type", "data_quality_rules", ["tenant_id", "master_type"]
    )

    # 5. data_quality_results
    op.create_table(
        "data_quality_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("master_type", sa.String(64), nullable=False),
        sa.Column("record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("dimension_scores_json", postgresql.JSONB(), nullable=False),
        sa.Column("rule_results_json", postgresql.JSONB(), nullable=False),
        sa.Column(
            "evaluated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index(
        "idx_dq_result_tenant_record",
        "data_quality_results",
        ["tenant_id", "master_type", "record_id"],
    )
    op.create_index(
        "idx_dq_result_eval_time",
        "data_quality_results",
        ["tenant_id", "evaluated_at"],
    )

    # 6. data_quality_issues
    op.create_table(
        "data_quality_issues",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("master_type", sa.String(64), nullable=False),
        sa.Column("record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "rule_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("data_quality_rules.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("rule_key", sa.String(128), nullable=False),
        sa.Column("severity", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="OPEN"),
        sa.Column("issue_message", sa.Text(), nullable=False),
        sa.Column("field_name", sa.String(64), nullable=True),
        sa.Column(
            "detected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("assigned_to", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("idx_dq_issue_tenant_status", "data_quality_issues", ["tenant_id", "status"])
    op.create_index(
        "idx_dq_issue_tenant_type_record",
        "data_quality_issues",
        ["tenant_id", "master_type", "record_id"],
    )

    # 7. duplicate_candidates
    op.create_table(
        "duplicate_candidates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("master_type", sa.String(64), nullable=False),
        sa.Column("record_a_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("record_b_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("match_score", sa.Float(), nullable=False),
        sa.Column("match_reasons", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint(
            "tenant_id", "master_type", "record_a_id", "record_b_id", name="uq_dup_cand_pair"
        ),
    )
    op.create_index("idx_dup_cand_tenant_status", "duplicate_candidates", ["tenant_id", "status"])

    # 8. master_data_merge_operations
    op.create_table(
        "master_data_merge_operations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("master_type", sa.String(64), nullable=False),
        sa.Column("survivor_record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("merged_record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "survivorship_rule", sa.String(32), nullable=False, server_default="KEEP_CANONICAL"
        ),
        sa.Column("field_decisions_json", postgresql.JSONB(), nullable=True),
        sa.Column("reassigned_counts_json", postgresql.JSONB(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="COMPLETED"),
        sa.Column("is_reversible", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("rolled_back_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rolled_back_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("rollback_reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index(
        "idx_merge_op_tenant_type",
        "master_data_merge_operations",
        ["tenant_id", "master_type"],
    )
    op.create_index(
        "idx_merge_op_survivor",
        "master_data_merge_operations",
        ["tenant_id", "survivor_record_id"],
    )
    op.create_index(
        "idx_merge_op_merged",
        "master_data_merge_operations",
        ["tenant_id", "merged_record_id"],
    )

    # 9. master_data_lineage
    op.create_table(
        "master_data_lineage",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("master_type", sa.String(64), nullable=False),
        sa.Column("record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source", sa.String(32), nullable=False, server_default="MANUAL"),
        sa.Column("source_record_id", sa.String(255), nullable=True),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("modified_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("modification_source", sa.String(64), nullable=True),
        sa.Column("details_json", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index(
        "idx_md_lineage_tenant_record",
        "master_data_lineage",
        ["tenant_id", "master_type", "record_id"],
    )

    # 10. master_data_corrections
    op.create_table(
        "master_data_corrections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("master_type", sa.String(64), nullable=False),
        sa.Column("record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("field_name", sa.String(64), nullable=False),
        sa.Column("old_value", sa.Text(), nullable=True),
        sa.Column("proposed_value", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING_REVIEW"),
        sa.Column("requester_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("idx_md_corr_tenant_status", "master_data_corrections", ["tenant_id", "status"])
    op.create_index(
        "idx_md_corr_tenant_record",
        "master_data_corrections",
        ["tenant_id", "master_type", "record_id"],
    )


def downgrade() -> None:
    op.drop_table("master_data_corrections")
    op.drop_table("master_data_lineage")
    op.drop_table("master_data_merge_operations")
    op.drop_table("duplicate_candidates")
    op.drop_table("data_quality_issues")
    op.drop_table("data_quality_results")
    op.drop_table("data_quality_rules")
    op.drop_table("reference_data_values")
    op.drop_table("reference_data_definitions")
    op.drop_table("master_data_definitions")
