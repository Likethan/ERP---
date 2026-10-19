"""Enterprise Tenant Onboarding, Readiness Certification & Go-Live Orchestration (Step 35).

Revision ID: 021_enterprise_tenant_onboarding_go_live_orchestration
Revises: 020_enterprise_security_operations_threat_detection
Create Date: 2026-10-17 22:00:00.000000

Creates normalized enterprise tenant onboarding tables:
- tenant_onboarding_plans: central lifecycle orchestration record
- onboarding_checklist_items: atomic, auditable readiness verification criteria across 7 categories
- onboarding_migration_jobs: bounded data migration jobs, dry-run tracking, and reconciliation
- onboarding_uat_scenarios: User Acceptance Testing scenarios, tester assignment, and defects
- onboarding_approvals: multi-role governance approvals with policy invalidation
- onboarding_golive_executions: ordered launch steps, idempotency keys, and recovery instructions
- onboarding_hypercare_records: post-launch telemetry monitoring, error spikes, and operational handoff
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "021_enterprise_tenant_onboarding_go_live_orchestration"
down_revision = "020_enterprise_security_operations_threat_detection"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Tenant Onboarding Plans
    op.create_table(
        "tenant_onboarding_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            unique=True,
            nullable=False,
            index=True,
        ),
        sa.Column("current_state", sa.String(50), nullable=False, server_default="DRAFT", index=True),
        sa.Column("previous_state", sa.String(50), nullable=True),
        sa.Column("target_go_live_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_go_live_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("assigned_lead_email", sa.String(255), nullable=True),
        sa.Column("state_reason", sa.Text(), nullable=True),
        sa.Column("rollback_reason", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # 2. Onboarding Checklist Items
    op.create_table(
        "onboarding_checklist_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenant_onboarding_plans.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("item_code", sa.String(50), nullable=False, index=True),
        sa.Column("category", sa.String(50), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("verification_method", sa.String(50), nullable=False, server_default="AUTOMATED"),
        sa.Column("status", sa.String(50), nullable=False, server_default="NOT_STARTED", index=True),
        sa.Column("evidence_ref", sa.String(500), nullable=True),
        sa.Column("responsible_owner", sa.String(255), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("blocker_reason", sa.Text(), nullable=True),
        sa.Column("waiver_reason", sa.Text(), nullable=True),
        sa.Column("waiver_approved_by", sa.String(255), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("plan_id", "item_code", name="uq_onboarding_checklist_plan_item"),
    )
    op.create_index(
        "ix_onboarding_checklist_category_status",
        "onboarding_checklist_items",
        ["category", "status"],
    )

    # 3. Onboarding Migration Jobs
    op.create_table(
        "onboarding_migration_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenant_onboarding_plans.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("domain_name", sa.String(100), nullable=False, index=True),
        sa.Column("source_filename", sa.String(255), nullable=False),
        sa.Column("source_checksum", sa.String(64), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="PENDING", index=True),
        sa.Column("source_record_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("accepted_record_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rejected_record_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duplicate_record_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("imported_record_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reconciliation_diff_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_batches_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unresolved_exceptions_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("dry_run", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("validation_findings", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("reconciliation_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column(
            "executed_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "approved_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # 4. Onboarding UAT Scenarios
    op.create_table(
        "onboarding_uat_scenarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenant_onboarding_plans.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("scenario_code", sa.String(50), nullable=False, index=True),
        sa.Column("module", sa.String(50), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("expected_outcome", sa.Text(), nullable=False),
        sa.Column("assigned_tester_email", sa.String(255), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="UNVERIFIED", index=True),
        sa.Column("evidence_ref", sa.String(500), nullable=True),
        sa.Column("defect_severity", sa.String(50), nullable=False, server_default="NONE"),
        sa.Column("defect_description", sa.Text(), nullable=True),
        sa.Column("retest_notes", sa.Text(), nullable=True),
        sa.Column("sign_off_by", sa.String(255), nullable=True),
        sa.Column("sign_off_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("plan_id", "scenario_code", name="uq_onboarding_uat_plan_scenario"),
    )

    # 5. Onboarding Approvals
    op.create_table(
        "onboarding_approvals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenant_onboarding_plans.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("role", sa.String(50), nullable=False, index=True),
        sa.Column("decision", sa.String(50), nullable=False, server_default="PENDING", index=True),
        sa.Column(
            "approver_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("approver_email", sa.String(255), nullable=True),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("policy_version", sa.String(50), nullable=False, server_default="1.0"),
        sa.Column("decision_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("invalidation_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("plan_id", "role", "policy_version", name="uq_onboarding_approval_plan_role"),
    )

    # 6. Onboarding Go-Live Executions
    op.create_table(
        "onboarding_golive_executions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenant_onboarding_plans.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("execution_run_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("step_name", sa.String(100), nullable=False, index=True),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="PENDING", index=True),
        sa.Column("is_dry_run", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("idempotency_key", sa.String(100), nullable=False, index=True),
        sa.Column(
            "actor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("result_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("recovery_instruction", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # 7. Onboarding Hypercare Records
    op.create_table(
        "onboarding_hypercare_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenant_onboarding_plans.id", ondelete="CASCADE"),
            unique=True,
            nullable=False,
            index=True,
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("hypercare_start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("hypercare_end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("assigned_support_lead", sa.String(255), nullable=False),
        sa.Column("escalation_contacts", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("daily_summaries", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("unresolved_issues_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("auth_failure_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("api_error_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("integration_failure_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("job_failure_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("exit_criteria_met", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("handoff_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("handoff_signoff_by", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("onboarding_hypercare_records")
    op.drop_table("onboarding_golive_executions")
    op.drop_table("onboarding_approvals")
    op.drop_table("onboarding_uat_scenarios")
    op.drop_table("onboarding_migration_jobs")
    op.drop_index("ix_onboarding_checklist_category_status", table_name="onboarding_checklist_items")
    op.drop_table("onboarding_checklist_items")
    op.drop_table("tenant_onboarding_plans")
