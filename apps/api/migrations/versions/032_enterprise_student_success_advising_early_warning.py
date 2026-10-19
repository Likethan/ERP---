"""Enterprise Student Success, Academic Advising, Early-Warning & Intervention Management (Step 47).

Revision ID: 032_enterprise_student_success_advising_early_warning
Revises: 031_enterprise_library_learning_resources
Create Date: 2026-10-19 16:00:00.000000

Creates normalized tables for:
- student_success_advisor_profiles: Academic advisor roles, capacities, and departmental scopes
- student_success_cases: Student success case management, triage, and review milestones
- student_success_case_notes: Case history notes with student-visibility boundary
- student_success_advisor_assignments: Advisor-student pairings and reassignment audit trail
- student_success_advising_plans: Student advising roadmap and target goals
- student_success_advising_action_items: Milestones and tasks in an advising plan
- student_success_early_warning_rules: Configurable risk rule definitions and thresholds
- student_success_early_warning_rule_versions: Audit trail of rule parameter revisions
- student_success_early_warning_evaluations: Batch/event evaluation execution logs
- student_success_early_warning_signals: Concrete explainable risk alert instances
- student_success_intervention_plans: Multi-disciplinary student intervention workflows
- student_success_intervention_actions: Granular intervention tasks and execution milestones
- student_success_advising_appointments: Appointment booking and conflict checking
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "032_enterprise_student_success_advising_early_warning"
down_revision = "031_enterprise_library_learning_resources"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Advisor Profiles
    op.create_table(
        "student_success_advisor_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "staff_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_staff.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("advisor_category", sa.String(64), nullable=False, server_default="FACULTY_ADVISOR"),
        sa.Column(
            "department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "campus_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_campuses.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "program_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_programs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("max_student_capacity", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("current_student_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("availability_schedule", postgresql.JSONB(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "user_id", name="uq_advisor_tenant_user"),
    )
    op.create_index(
        "ix_advisor_dept_active",
        "student_success_advisor_profiles",
        ["tenant_id", "department_id", "is_active"],
    )

    # 2. Student Success Cases
    op.create_table(
        "student_success_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("case_number", sa.String(64), nullable=False),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_students.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("category", sa.String(64), nullable=False, server_default="ACADEMIC_PERFORMANCE"),
        sa.Column("priority", sa.String(32), nullable=False, server_default="MEDIUM"),
        sa.Column("status", sa.String(32), nullable=False, server_default="OPEN"),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("objective", sa.Text(), nullable=True),
        sa.Column("creation_source", sa.String(64), nullable=False, server_default="ADVISOR_MANUAL"),
        sa.Column(
            "assigned_advisor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("student_success_advisor_profiles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "assigned_to_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("target_completion_date", sa.Date(), nullable=True),
        sa.Column("next_review_date", sa.Date(), nullable=True),
        sa.Column("actual_resolution_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closure_reason", sa.String(64), nullable=True),
        sa.Column("outcome_classification", sa.String(64), nullable=True),
        sa.Column("outcome_notes", sa.Text(), nullable=True),
        sa.Column("is_escalated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("escalation_reason", sa.Text(), nullable=True),
        sa.Column("escalated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reopened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reopened_reason", sa.Text(), nullable=True),
        sa.Column(
            "related_case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("student_success_cases.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "case_number", name="uq_student_success_case_number"),
    )
    op.create_index(
        "ix_ssc_tenant_student_status",
        "student_success_cases",
        ["tenant_id", "student_id", "status"],
    )
    op.create_index(
        "ix_ssc_tenant_advisor_status",
        "student_success_cases",
        ["tenant_id", "assigned_advisor_id", "status"],
    )
    op.create_index(
        "ix_ssc_tenant_category_priority",
        "student_success_cases",
        ["tenant_id", "category", "priority"],
    )
    op.create_index(
        "ix_ssc_tenant_next_review",
        "student_success_cases",
        ["tenant_id", "next_review_date"],
    )
    op.create_index(
        "ix_ssc_tenant_is_escalated",
        "student_success_cases",
        ["tenant_id", "is_escalated"],
    )

    # 3. Case Notes
    op.create_table(
        "student_success_case_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("student_success_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "author_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("note_type", sa.String(64), nullable=False, server_default="INTERNAL_NOTE"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_student_visible", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_sscn_case_visible",
        "student_success_case_notes",
        ["case_id", "is_student_visible"],
    )
    op.create_index(
        "ix_sscn_case_created",
        "student_success_case_notes",
        ["case_id", "created_at"],
    )

    # 4. Advisor Student Assignments
    op.create_table(
        "student_success_advisor_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "advisor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("student_success_advisor_profiles.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_students.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("relationship_type", sa.String(32), nullable=False, server_default="PRIMARY"),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"),
        sa.Column("reassignment_reason", sa.Text(), nullable=True),
        sa.Column(
            "assigned_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_asa_advisor_student_status",
        "student_success_advisor_assignments",
        ["tenant_id", "advisor_id", "student_id", "status"],
    )
    op.create_index(
        "ix_asa_student_status",
        "student_success_advisor_assignments",
        ["tenant_id", "student_id", "status"],
    )

    # 5. Advising Plans
    op.create_table(
        "student_success_advising_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_students.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "advisor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("student_success_advisor_profiles.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("student_success_cases.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("academic_goals", sa.Text(), nullable=True),
        sa.Column("target_gpa", sa.Numeric(4, 2), nullable=True),
        sa.Column("target_credits", sa.Integer(), nullable=True),
        sa.Column("review_frequency", sa.String(32), nullable=False, server_default="MONTHLY"),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"),
        sa.Column("is_student_visible", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_ap_student_status",
        "student_success_advising_plans",
        ["tenant_id", "student_id", "status"],
    )
    op.create_index(
        "ix_ap_case_id",
        "student_success_advising_plans",
        ["case_id"],
    )

    # 6. Advising Action Items
    op.create_table(
        "student_success_advising_action_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "advising_plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("student_success_advising_plans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("responsible_party", sa.String(32), nullable=False, server_default="STUDENT"),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("completed_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("is_student_visible", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("student_progress_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_aai_plan_status",
        "student_success_advising_action_items",
        ["advising_plan_id", "status"],
    )
    op.create_index(
        "ix_aai_due_date",
        "student_success_advising_action_items",
        ["tenant_id", "due_date"],
    )

    # 7. Early Warning Rules
    op.create_table(
        "student_success_early_warning_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(64), nullable=False, server_default="ATTENDANCE"),
        sa.Column("operator", sa.String(32), nullable=False, server_default="LESS_THAN"),
        sa.Column("threshold_value", sa.Numeric(8, 2), nullable=False),
        sa.Column("evaluation_window_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column(
            "department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "program_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_programs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "academic_term_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("examination_terms.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("severity", sa.String(32), nullable=False, server_default="HIGH"),
        sa.Column("recommended_intervention_category", sa.String(64), nullable=False, server_default="ATTENDANCE_FOLLOWUP"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("current_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_ewr_tenant_code"),
    )
    op.create_index(
        "ix_ewr_tenant_category_active",
        "student_success_early_warning_rules",
        ["tenant_id", "category", "is_active"],
    )
    op.create_index(
        "ix_ewr_tenant_dept_active",
        "student_success_early_warning_rules",
        ["tenant_id", "department_id", "is_active"],
    )

    # 8. Early Warning Rule Versions
    op.create_table(
        "student_success_early_warning_rule_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "rule_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("student_success_early_warning_rules.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("operator", sa.String(32), nullable=False),
        sa.Column("threshold_value", sa.Numeric(8, 2), nullable=False),
        sa.Column("evaluation_window_days", sa.Integer(), nullable=False),
        sa.Column("severity", sa.String(32), nullable=False),
        sa.Column(
            "changed_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("change_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("rule_id", "version_number", name="uq_ewrv_rule_version"),
    )
    op.create_index(
        "ix_ewrv_rule",
        "student_success_early_warning_rule_versions",
        ["rule_id"],
    )

    # 9. Early Warning Evaluations
    op.create_table(
        "student_success_early_warning_evaluations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "rule_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("student_success_early_warning_rules.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("evaluation_scope", sa.String(64), nullable=False, server_default="ALL_STUDENTS"),
        sa.Column("scope_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("evaluation_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("triggered_by", sa.String(64), nullable=False, server_default="SCHEDULED_JOB"),
        sa.Column("students_evaluated_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("warnings_generated_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(32), nullable=False, server_default="COMPLETED"),
        sa.Column("execution_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_ewe_tenant_rule",
        "student_success_early_warning_evaluations",
        ["tenant_id", "rule_id"],
    )
    op.create_index(
        "ix_ewe_timestamp",
        "student_success_early_warning_evaluations",
        ["evaluation_timestamp"],
    )

    # 10. Early Warning Signals
    op.create_table(
        "student_success_early_warning_signals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_students.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "rule_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("student_success_early_warning_rules.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("rule_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "evaluation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("student_success_early_warning_evaluations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("signal_code", sa.String(64), nullable=False),
        sa.Column("observation_period_start", sa.Date(), nullable=False),
        sa.Column("observation_period_end", sa.Date(), nullable=False),
        sa.Column("metric_observed_value", sa.Numeric(8, 2), nullable=False),
        sa.Column("threshold_condition", sa.String(128), nullable=False),
        sa.Column("source_record_references", postgresql.JSONB(), nullable=False),
        sa.Column("severity", sa.String(32), nullable=False, server_default="HIGH"),
        sa.Column("status", sa.String(32), nullable=False, server_default="NEWLY_DETECTED"),
        sa.Column("dismissal_reason", sa.Text(), nullable=True),
        sa.Column("is_false_positive", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "acknowledged_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column(
            "success_case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("student_success_cases.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "signal_code", name="uq_ews_tenant_signal_code"),
    )
    op.create_index(
        "ix_ews_tenant_student_status",
        "student_success_early_warning_signals",
        ["tenant_id", "student_id", "status"],
    )
    op.create_index(
        "ix_ews_tenant_rule_status",
        "student_success_early_warning_signals",
        ["tenant_id", "rule_id", "status"],
    )
    op.create_index(
        "ix_ews_tenant_severity",
        "student_success_early_warning_signals",
        ["tenant_id", "severity"],
    )
    op.create_index(
        "ix_ews_tenant_created",
        "student_success_early_warning_signals",
        ["tenant_id", "created_at"],
    )

    # 11. Intervention Plans
    op.create_table(
        "student_success_intervention_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_students.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("student_success_cases.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "warning_signal_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("student_success_early_warning_signals.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("objective", sa.Text(), nullable=True),
        sa.Column("intervention_type", sa.String(64), nullable=False, server_default="ACADEMIC_ADVISING"),
        sa.Column("priority", sa.String(32), nullable=False, server_default="MEDIUM"),
        sa.Column("status", sa.String(32), nullable=False, server_default="PLANNED"),
        sa.Column(
            "assigned_to_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("planned_start_date", sa.Date(), nullable=False),
        sa.Column("target_completion_date", sa.Date(), nullable=False),
        sa.Column("actual_completion_date", sa.Date(), nullable=True),
        sa.Column("student_participation", sa.String(32), nullable=False, server_default="SCHEDULED"),
        sa.Column("outcome_classification", sa.String(32), nullable=True),
        sa.Column("outcome_notes", sa.Text(), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_ip_tenant_student_status",
        "student_success_intervention_plans",
        ["tenant_id", "student_id", "status"],
    )
    op.create_index(
        "ix_ip_tenant_case",
        "student_success_intervention_plans",
        ["tenant_id", "case_id"],
    )
    op.create_index(
        "ix_ip_tenant_assigned_status",
        "student_success_intervention_plans",
        ["tenant_id", "assigned_to_user_id", "status"],
    )
    op.create_index(
        "ix_ip_tenant_target_date",
        "student_success_intervention_plans",
        ["tenant_id", "target_completion_date"],
    )

    # 12. Intervention Actions
    op.create_table(
        "student_success_intervention_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "intervention_plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("student_success_intervention_plans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("completed_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("is_student_visible", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("completion_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_ia_plan_status",
        "student_success_intervention_actions",
        ["intervention_plan_id", "status"],
    )
    op.create_index(
        "ix_ia_due_date",
        "student_success_intervention_actions",
        ["tenant_id", "due_date"],
    )

    # 13. Advising Appointments
    op.create_table(
        "student_success_advising_appointments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "advisor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("student_success_advisor_profiles.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_students.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("student_success_cases.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("scheduled_start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scheduled_end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("meeting_mode", sa.String(32), nullable=False, server_default="IN_PERSON"),
        sa.Column("location_or_url", sa.String(255), nullable=True),
        sa.Column("agenda", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="REQUESTED"),
        sa.Column("meeting_notes", sa.Text(), nullable=True),
        sa.Column("agreed_action_summary", sa.Text(), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_saa_tenant_advisor_time",
        "student_success_advising_appointments",
        ["tenant_id", "advisor_id", "scheduled_start_time", "scheduled_end_time"],
    )
    op.create_index(
        "ix_saa_tenant_student_time",
        "student_success_advising_appointments",
        ["tenant_id", "student_id", "scheduled_start_time"],
    )
    op.create_index(
        "ix_saa_tenant_status",
        "student_success_advising_appointments",
        ["tenant_id", "status"],
    )


def downgrade() -> None:
    op.drop_table("student_success_advising_appointments")
    op.drop_table("student_success_intervention_actions")
    op.drop_table("student_success_intervention_plans")
    op.drop_table("student_success_early_warning_signals")
    op.drop_table("student_success_early_warning_evaluations")
    op.drop_table("student_success_early_warning_rule_versions")
    op.drop_table("student_success_early_warning_rules")
    op.drop_table("student_success_advising_action_items")
    op.drop_table("student_success_advising_plans")
    op.drop_table("student_success_advisor_assignments")
    op.drop_table("student_success_case_notes")
    op.drop_table("student_success_cases")
    op.drop_table("student_success_advisor_profiles")
