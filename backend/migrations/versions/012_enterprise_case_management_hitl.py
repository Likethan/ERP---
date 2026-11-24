"""Enterprise Workflow, Case Management & Human-in-the-Loop Operations Migration (Step 25).

Revision ID: 012_enterprise_case_management_hitl
Revises: 011_enterprise_master_data_quality
Create Date: 2026-10-08 21:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "012_enterprise_case_management_hitl"
down_revision = "011_enterprise_master_data_quality"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. case_types
    op.create_table(
        "case_types",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=True,
            index=True,
        ),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("module", sa.String(32), nullable=False, server_default="GENERAL"),
        sa.Column("default_priority", sa.String(32), nullable=False, server_default="NORMAL"),
        sa.Column("default_queue_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("sla_hours", sa.Integer(), nullable=False, server_default="48"),
        sa.Column("requires_decision", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "code", name="uq_case_type_tenant_code"),
    )
    op.create_index("idx_case_type_tenant_active", "case_types", ["tenant_id", "is_active"])
    op.create_index("idx_case_type_module", "case_types", ["tenant_id", "module"])

    # 2. work_queues
    op.create_table(
        "work_queues",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("key", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("module", sa.String(32), nullable=False, server_default="GENERAL"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("assignment_policy", sa.String(32), nullable=False, server_default="MANUAL"),
        sa.Column("capacity", sa.Integer(), nullable=True, server_default="100"),
        sa.Column(
            "supervisor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("sla_hours", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("tenant_id", "key", name="uq_work_queue_tenant_key"),
    )
    op.create_index("idx_work_queue_module", "work_queues", ["tenant_id", "module"])
    op.create_index("idx_work_queue_active", "work_queues", ["tenant_id", "is_active"])

    # 3. queue_members
    op.create_table(
        "queue_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "queue_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("work_queues.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("is_supervisor", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("max_active_tasks", sa.Integer(), nullable=False, server_default="10"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("tenant_id", "queue_id", "user_id", name="uq_queue_member"),
    )
    op.create_index("idx_queue_member_user", "queue_members", ["tenant_id", "user_id"])

    # 4. cases
    op.create_table(
        "cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("case_number", sa.String(64), nullable=False),
        sa.Column(
            "case_type_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("case_types.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("case_type_code", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", sa.String(32), nullable=False, server_default="NORMAL"),
        sa.Column("status", sa.String(32), nullable=False, server_default="OPEN"),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "assigned_queue_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("work_queues.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "workflow_execution_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workflow_executions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("subject_entity_type", sa.String(64), nullable=True),
        sa.Column("subject_entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_reason", sa.String(128), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("reopen_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sla_breached", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "case_number", name="uq_case_tenant_number"),
    )
    op.create_index("idx_case_tenant_status", "cases", ["tenant_id", "status"])
    op.create_index("idx_case_tenant_priority", "cases", ["tenant_id", "priority"])
    op.create_index("idx_case_tenant_owner", "cases", ["tenant_id", "owner_id"])
    op.create_index("idx_case_tenant_queue", "cases", ["tenant_id", "assigned_queue_id"])
    op.create_index("idx_case_workflow_exec", "cases", ["workflow_execution_id"])
    op.create_index(
        "idx_case_subject", "cases", ["tenant_id", "subject_entity_type", "subject_entity_id"]
    )

    # 5. case_relationships
    op.create_table(
        "case_relationships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "source_case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "target_case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("relationship_type", sa.String(32), nullable=False, server_default="RELATED_TO"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "source_case_id",
            "target_case_id",
            "relationship_type",
            name="uq_case_relationship",
        ),
    )
    op.create_index("idx_case_rel_source", "case_relationships", ["tenant_id", "source_case_id"])
    op.create_index("idx_case_rel_target", "case_relationships", ["tenant_id", "target_case_id"])

    # 6. human_tasks
    op.create_table(
        "human_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "workflow_execution_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workflow_executions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("step_key", sa.String(64), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("task_type", sa.String(32), nullable=False, server_default="REVIEW"),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("priority", sa.String(32), nullable=False, server_default="NORMAL"),
        sa.Column(
            "assigned_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("assigned_role", sa.String(64), nullable=True),
        sa.Column(
            "assigned_queue_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("work_queues.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "completed_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("sla_breached", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("input_context_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("output_result_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_task_case_status", "human_tasks", ["tenant_id", "case_id", "status"])
    op.create_index(
        "idx_task_assigned_user", "human_tasks", ["tenant_id", "assigned_user_id", "status"]
    )
    op.create_index(
        "idx_task_assigned_queue", "human_tasks", ["tenant_id", "assigned_queue_id", "status"]
    )
    op.create_index(
        "idx_task_assigned_role", "human_tasks", ["tenant_id", "assigned_role", "status"]
    )
    op.create_index("idx_task_workflow_exec", "human_tasks", ["workflow_execution_id"])

    # 7. case_comments
    op.create_table(
        "case_comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "task_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("human_tasks.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "author_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("visibility", sa.String(32), nullable=False, server_default="INTERNAL"),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("idx_comment_case", "case_comments", ["tenant_id", "case_id"])
    op.create_index("idx_comment_task", "case_comments", ["tenant_id", "task_id"])

    # 8. case_attachments
    op.create_table(
        "case_attachments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "task_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("human_tasks.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents_records.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "attachment_type",
            sa.String(64),
            nullable=False,
            server_default="SUPPORTING_EVIDENCE",
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("visibility", sa.String(32), nullable=False, server_default="INTERNAL"),
        sa.Column(
            "uploaded_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("idx_attachment_case", "case_attachments", ["tenant_id", "case_id"])
    op.create_index("idx_attachment_doc", "case_attachments", ["tenant_id", "document_id"])

    # 9. case_timeline_events
    op.create_table(
        "case_timeline_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "task_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("human_tasks.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column(
            "actor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("details_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column(
            "occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index(
        "idx_timeline_case_time", "case_timeline_events", ["tenant_id", "case_id", "occurred_at"]
    )

    # 10. task_decisions
    op.create_table(
        "task_decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "task_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("human_tasks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "actor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("decision", sa.String(32), nullable=False, server_default="APPROVE"),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("evidence_reference", sa.String(255), nullable=True),
        sa.Column("resulting_transition", sa.String(64), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("idx_decision_task", "task_decisions", ["tenant_id", "task_id"])
    op.create_index("idx_decision_case", "task_decisions", ["tenant_id", "case_id"])
    op.create_index("idx_decision_actor", "task_decisions", ["tenant_id", "actor_id"])

    # 11. task_delegations
    op.create_table(
        "task_delegations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "delegator_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "delegatee_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("scope_module", sa.String(32), nullable=True),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index(
        "idx_delegation_delegator",
        "task_delegations",
        ["tenant_id", "delegator_user_id", "is_active"],
    )
    op.create_index(
        "idx_delegation_delegatee",
        "task_delegations",
        ["tenant_id", "delegatee_user_id", "is_active"],
    )
    op.create_index("idx_delegation_validity", "task_delegations", ["valid_from", "valid_until"])

    # 12. sla_policies
    op.create_table(
        "sla_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("module", sa.String(32), nullable=False, server_default="GENERAL"),
        sa.Column("case_type_code", sa.String(64), nullable=True),
        sa.Column("priority", sa.String(32), nullable=False, server_default="NORMAL"),
        sa.Column("target_duration_minutes", sa.Integer(), nullable=False, server_default="2880"),
        sa.Column("warning_threshold_percentage", sa.Integer(), nullable=False, server_default="75"),
        sa.Column("business_hours_only", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("business_start_hour", sa.Integer(), nullable=False, server_default="9"),
        sa.Column("business_end_hour", sa.Integer(), nullable=False, server_default="18"),
        sa.Column(
            "escalation_queue_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("work_queues.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("escalation_role", sa.String(64), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint(
            "tenant_id", "module", "priority", "case_type_code", name="uq_sla_policy_scope"
        ),
    )
    op.create_index("idx_sla_module_prio", "sla_policies", ["tenant_id", "module", "priority"])

    # 13. sla_instances
    op.create_table(
        "sla_instances",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "sla_policy_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sla_policies.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cases.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "task_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("human_tasks.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("warning_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("elapsed_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(32), nullable=False, server_default="ON_TRACK"),
        sa.Column("breached", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("escalated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("escalated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("idx_sla_inst_case", "sla_instances", ["tenant_id", "case_id", "status"])
    op.create_index("idx_sla_inst_task", "sla_instances", ["tenant_id", "task_id", "status"])
    op.create_index("idx_sla_inst_due", "sla_instances", ["due_at", "status"])


def downgrade() -> None:
    op.drop_table("sla_instances")
    op.drop_table("sla_policies")
    op.drop_table("task_delegations")
    op.drop_table("task_decisions")
    op.drop_table("case_timeline_events")
    op.drop_table("case_attachments")
    op.drop_table("case_comments")
    op.drop_table("human_tasks")
    op.drop_table("case_relationships")
    op.drop_table("cases")
    op.drop_table("queue_members")
    op.drop_table("work_queues")
    op.drop_table("case_types")
