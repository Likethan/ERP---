"""Enterprise Workforce Management, Staff Lifecycle, Leave & Workload Administration (Step 51).

Revision ID: 036_enterprise_workforce_leave_workload
Revises: 035_enterprise_procurement_vendor_inventory
Create Date: 2026-10-20 20:00:00.000000

Creates normalized tables for:
- workforce_employees: Enterprise staff employment master records
- workforce_employment_history: Traceable effective-dated history of employee transitions
- workforce_lifecycle_cases: Structured onboarding and offboarding lifecycle workflows
- workforce_lifecycle_tasks: Cross-functional operational checklist tasks
- workforce_leave_types: Institutional leave categories catalogue
- workforce_leave_policies: Versioned accrual and eligibility policies
- workforce_leave_balances: Annual balance snapshots per employee and leave type
- workforce_leave_balance_transactions: Immutable audit ledger for balance accruals, consumption, and adjustments
- workforce_leave_requests: Formal staff leave applications with concurrency protection
- workforce_leave_approval_steps: Multi-stage hierarchical approval workflow steps
- workforce_availability_conflicts: Detected schedule collisions between leave and timetable assignments
- workforce_workload_expectations: Effective-dated weekly workload hour expectations
- workforce_workload_adjustments: Authorized adjustments or duty concessions
- workforce_hr_cases: Employee self-service requests and HR inquiries
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "036_enterprise_workforce_leave_workload"
down_revision = "035_enterprise_procurement_vendor_inventory"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Workforce Employees
    op.create_table(
        "workforce_employees",
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
        sa.Column("employee_number", sa.String(64), nullable=False),
        sa.Column("employment_type", sa.String(32), nullable=False, server_default="PERMANENT"),
        sa.Column("employment_status", sa.String(32), nullable=False, server_default="DRAFT"),
        sa.Column("designation", sa.String(128), nullable=False),
        sa.Column("job_title", sa.String(128), nullable=False),
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
            "reporting_manager_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workforce_employees.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("work_location", sa.String(128), nullable=True),
        sa.Column("joining_date", sa.Date(), nullable=False),
        sa.Column("probation_end_date", sa.Date(), nullable=True),
        sa.Column("confirmation_date", sa.Date(), nullable=True),
        sa.Column("contract_start_date", sa.Date(), nullable=True),
        sa.Column("contract_end_date", sa.Date(), nullable=True),
        sa.Column("separation_date", sa.Date(), nullable=True),
        sa.Column("separation_reason", sa.String(128), nullable=True),
        sa.Column("notice_period_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("qualifications", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("certifications", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("metadata_properties", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "employee_number", name="uq_workforce_emp_tenant_num"),
        sa.UniqueConstraint("tenant_id", "user_id", name="uq_workforce_emp_tenant_user"),
    )
    op.create_index("ix_workforce_emp_dept_status", "workforce_employees", ["tenant_id", "department_id", "employment_status"])
    op.create_index("ix_workforce_emp_campus", "workforce_employees", ["tenant_id", "campus_id"])
    op.create_index("ix_workforce_emp_manager", "workforce_employees", ["tenant_id", "reporting_manager_id"])

    # 2. Employment History
    op.create_table(
        "workforce_employment_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "employee_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workforce_employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("change_type", sa.String(32), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("previous_values", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("new_values", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "authorized_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("reference_document_id", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_workforce_hist_emp_date", "workforce_employment_history", ["tenant_id", "employee_id", "effective_date"])

    # 3. Lifecycle Cases
    op.create_table(
        "workforce_lifecycle_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "employee_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workforce_employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("case_number", sa.String(64), nullable=False),
        sa.Column("case_type", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT"),
        sa.Column("target_date", sa.Date(), nullable=False),
        sa.Column("completion_date", sa.Date(), nullable=True),
        sa.Column(
            "initiator_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "case_number", name="uq_workforce_case_tenant_num"),
    )
    op.create_index("ix_workforce_case_emp_type", "workforce_lifecycle_cases", ["tenant_id", "employee_id", "case_type"])
    op.create_index("ix_workforce_case_status", "workforce_lifecycle_cases", ["tenant_id", "status"])

    # 4. Lifecycle Tasks
    op.create_table(
        "workforce_lifecycle_tasks",
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
            sa.ForeignKey("workforce_lifecycle_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("task_name", sa.String(128), nullable=False),
        sa.Column("task_category", sa.String(32), nullable=False, server_default="HR"),
        sa.Column("assigned_role", sa.String(64), nullable=True),
        sa.Column(
            "assigned_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("is_mandatory", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "completed_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("completion_evidence", sa.Text(), nullable=True),
        sa.Column("blocker_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_workforce_task_case_status", "workforce_lifecycle_tasks", ["tenant_id", "case_id", "status"])
    op.create_index("ix_workforce_task_assigned_user", "workforce_lifecycle_tasks", ["tenant_id", "assigned_user_id"])

    # 5. Leave Types
    op.create_table(
        "workforce_leave_types",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_paid", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "code", name="uq_workforce_leave_type_tenant_code"),
    )

    # 6. Leave Policies
    op.create_table(
        "workforce_leave_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "leave_type_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workforce_leave_types.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("policy_code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("applicable_employment_types", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("applicable_departments", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("annual_entitlement", sa.Numeric(5, 2), nullable=False, server_default="12.00"),
        sa.Column("accrual_frequency", sa.String(32), nullable=False, server_default="ANNUAL"),
        sa.Column("accrual_rate", sa.Numeric(5, 2), nullable=False, server_default="1.00"),
        sa.Column("carry_forward_max", sa.Numeric(5, 2), nullable=False, server_default="0.00"),
        sa.Column("expiry_months", sa.Integer(), nullable=True),
        sa.Column("max_consecutive_days", sa.Integer(), nullable=True),
        sa.Column("requires_document", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("document_mandatory_after_days", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("allow_half_day", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "policy_code", "version", name="uq_workforce_policy_ver"),
    )
    op.create_index("ix_workforce_pol_type_dates", "workforce_leave_policies", ["tenant_id", "leave_type_id", "effective_from"])

    # 7. Leave Balances
    op.create_table(
        "workforce_leave_balances",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "employee_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workforce_employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "leave_type_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workforce_leave_types.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("calendar_year", sa.Integer(), nullable=False),
        sa.Column("entitled_days", sa.Numeric(6, 2), nullable=False, server_default="0.00"),
        sa.Column("accrued_days", sa.Numeric(6, 2), nullable=False, server_default="0.00"),
        sa.Column("carried_forward_days", sa.Numeric(6, 2), nullable=False, server_default="0.00"),
        sa.Column("used_days", sa.Numeric(6, 2), nullable=False, server_default="0.00"),
        sa.Column("pending_days", sa.Numeric(6, 2), nullable=False, server_default="0.00"),
        sa.Column("adjusted_days", sa.Numeric(6, 2), nullable=False, server_default="0.00"),
        sa.Column("expired_days", sa.Numeric(6, 2), nullable=False, server_default="0.00"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "employee_id", "leave_type_id", "calendar_year", name="uq_workforce_balance_emp_year"),
    )
    op.create_index("ix_workforce_bal_emp_year", "workforce_leave_balances", ["tenant_id", "employee_id", "calendar_year"])

    # 8. Leave Balance Transactions
    op.create_table(
        "workforce_leave_balance_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "balance_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workforce_leave_balances.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("transaction_type", sa.String(32), nullable=False),
        sa.Column("amount", sa.Numeric(6, 2), nullable=False),
        sa.Column("running_balance", sa.Numeric(6, 2), nullable=False),
        sa.Column("reference_type", sa.String(64), nullable=True),
        sa.Column("reference_id", sa.String(64), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_workforce_tx_bal_created", "workforce_leave_balance_transactions", ["tenant_id", "balance_id", "created_at"])

    # 9. Leave Requests
    op.create_table(
        "workforce_leave_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "employee_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workforce_employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "leave_type_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workforce_leave_types.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "policy_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workforce_leave_policies.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("request_number", sa.String(64), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("is_half_day", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("half_day_session", sa.String(32), nullable=True),
        sa.Column("total_days", sa.Numeric(5, 2), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("supporting_document_url", sa.String(255), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="SUBMITTED"),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "decided_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "request_number", name="uq_workforce_leave_req_num"),
    )
    op.create_index("ix_workforce_req_emp_dates", "workforce_leave_requests", ["tenant_id", "employee_id", "start_date", "end_date"])
    op.create_index("ix_workforce_req_status", "workforce_leave_requests", ["tenant_id", "status"])

    # 10. Leave Approval Steps
    op.create_table(
        "workforce_leave_approval_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "request_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workforce_leave_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("step_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "approver_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("approver_role", sa.String(64), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_workforce_step_req_num", "workforce_leave_approval_steps", ["tenant_id", "request_id", "step_number"])

    # 11. Availability Conflicts
    op.create_table(
        "workforce_availability_conflicts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "employee_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workforce_employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "leave_request_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workforce_leave_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("conflict_date", sa.Date(), nullable=False),
        sa.Column(
            "timetable_session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("timetable_sessions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("conflict_type", sa.String(64), nullable=False, server_default="LEAVE_VS_TIMETABLE_SESSION"),
        sa.Column("severity", sa.String(32), nullable=False, server_default="WARNING"),
        sa.Column("is_overridden", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("override_reason", sa.Text(), nullable=True),
        sa.Column(
            "overridden_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "substitute_employee_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workforce_employees.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_workforce_conf_emp_date", "workforce_availability_conflicts", ["tenant_id", "employee_id", "conflict_date"])

    # 12. Workload Expectations
    op.create_table(
        "workforce_workload_expectations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "employee_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workforce_employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "academic_year_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_academic_years.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "semester_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_semesters.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("teaching_hours_per_week", sa.Numeric(5, 2), nullable=False, server_default="16.00"),
        sa.Column("research_hours_per_week", sa.Numeric(5, 2), nullable=False, server_default="8.00"),
        sa.Column("admin_hours_per_week", sa.Numeric(5, 2), nullable=False, server_default="6.00"),
        sa.Column("exam_hours_per_week", sa.Numeric(5, 2), nullable=False, server_default="4.00"),
        sa.Column("total_expected_hours_per_week", sa.Numeric(5, 2), nullable=False, server_default="34.00"),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_workforce_workload_emp_term", "workforce_workload_expectations", ["tenant_id", "employee_id", "academic_year_id"])

    # 13. Workload Adjustments
    op.create_table(
        "workforce_workload_adjustments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "employee_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workforce_employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category", sa.String(32), nullable=False, server_default="TEACHING"),
        sa.Column("adjusted_hours_per_week", sa.Numeric(5, 2), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column(
            "authorized_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_workforce_adj_emp_dates", "workforce_workload_adjustments", ["tenant_id", "employee_id", "effective_from"])

    # 14. HR Cases
    op.create_table(
        "workforce_hr_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "employee_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workforce_employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("case_number", sa.String(64), nullable=False),
        sa.Column("category", sa.String(32), nullable=False, server_default="GENERAL_INQUIRY"),
        sa.Column("priority", sa.String(32), nullable=False, server_default="NORMAL"),
        sa.Column("status", sa.String(32), nullable=False, server_default="OPEN"),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("proposed_changes", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("is_confidential", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "assigned_to_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "case_number", name="uq_workforce_hr_case_num"),
    )
    op.create_index("ix_workforce_hr_case_emp_status", "workforce_hr_cases", ["tenant_id", "employee_id", "status"])
    op.create_index("ix_workforce_hr_case_assigned", "workforce_hr_cases", ["tenant_id", "assigned_to_user_id"])


def downgrade() -> None:
    op.drop_table("workforce_hr_cases")
    op.drop_table("workforce_workload_adjustments")
    op.drop_table("workforce_workload_expectations")
    op.drop_table("workforce_availability_conflicts")
    op.drop_table("workforce_leave_approval_steps")
    op.drop_table("workforce_leave_requests")
    op.drop_table("workforce_leave_balance_transactions")
    op.drop_table("workforce_leave_balances")
    op.drop_table("workforce_leave_policies")
    op.drop_table("workforce_leave_types")
    op.drop_table("workforce_lifecycle_tasks")
    op.drop_table("workforce_lifecycle_cases")
    op.drop_table("workforce_employment_history")
    op.drop_table("workforce_employees")
