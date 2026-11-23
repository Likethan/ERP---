"""Enterprise Payroll, Compensation, Benefits & Statutory Compliance (Step 52).

Revision ID: 037_enterprise_payroll_compensation_compliance
Revises: 036_enterprise_workforce_leave_workload
Create Date: 2026-10-20 22:30:00.000000

Creates normalized tables for:
- payroll_salary_grades: Enterprise compensation grades and pay scales
- payroll_salary_components: Configurable earning and deduction elements
- payroll_salary_structures: Grouped salary packages with versioning
- payroll_salary_structure_items: Component composition within salary structures
- payroll_employee_compensations: Active employee compensation assignments
- payroll_compensation_history: Versioned audit trail for salary revisions
- payroll_employee_bank_details: Masked employee disbursement accounts
- payroll_calendars: Pay frequencies, cutoff schedules, and pay day policies
- payroll_periods: Specific calendarized pay periods with lock states
- payroll_runs: Batch payroll calculation and lifecycle executions
- payroll_run_items: Per-employee computation outputs and attendance snapshots
- payroll_run_item_details: Granular line item calculation breakdown
- payroll_accounting_mappings: Chart of accounts mappings for double-entry journals
- payroll_journal_entries: Balanced financial general ledger transactions
- payroll_journal_lines: Balanced debit and credit accounting lines
- payroll_payment_batches: Payment disbursement batches and export files
- payroll_payment_items: Individual payment instructions and bank reconciliations
- payroll_statutory_rules: Configurable jurisdiction compliance parameters
- payroll_payslips: Finalized self-service employee payslip documents
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "037_enterprise_payroll_compensation_compliance"
down_revision = "036_enterprise_workforce_leave_workload"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Salary Grades
    op.create_table(
        "payroll_salary_grades",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("min_base_pay", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("max_base_pay", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_salary_grade_tenant_code"),
    )
    op.create_index("ix_salary_grade_tenant", "payroll_salary_grades", ["tenant_id", "is_active"])

    # 2. Salary Components
    op.create_table(
        "payroll_salary_components",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("component_type", sa.String(32), nullable=False),
        sa.Column("calculation_method", sa.String(32), nullable=False, server_default="FLAT_AMOUNT"),
        sa.Column("default_value", sa.Numeric(12, 4), nullable=False, server_default="0.0000"),
        sa.Column("is_statutory", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("taxability", sa.String(32), nullable=False, server_default="TAXABLE"),
        sa.Column("is_recurring", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_salary_comp_tenant_code"),
    )
    op.create_index("ix_salary_comp_tenant_type", "payroll_salary_components", ["tenant_id", "component_type", "is_active"])

    # 3. Salary Structures
    op.create_table(
        "payroll_salary_structures",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("currency", sa.String(8), nullable=False, server_default="INR"),
        sa.Column("pay_frequency", sa.String(32), nullable=False, server_default="MONTHLY"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_salary_struct_tenant_code"),
    )
    op.create_index("ix_salary_struct_tenant", "payroll_salary_structures", ["tenant_id", "is_active"])

    # 4. Salary Structure Items
    op.create_table(
        "payroll_salary_structure_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "structure_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("payroll_salary_structures.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "component_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("payroll_salary_components.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("calculation_method", sa.String(32), nullable=False),
        sa.Column("factor_value", sa.Numeric(12, 4), nullable=False, server_default="0.0000"),
        sa.Column("fixed_amount", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("sequence", sa.Integer(), nullable=False, server_default="1"),
    )

    # 5. Employee Compensations
    op.create_table(
        "payroll_employee_compensations",
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
            sa.ForeignKey("workforce_employees.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "structure_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("payroll_salary_structures.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "salary_grade_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("payroll_salary_grades.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("annual_ctc", sa.Numeric(14, 2), nullable=False),
        sa.Column("monthly_gross", sa.Numeric(12, 2), nullable=False),
        sa.Column("base_pay", sa.Numeric(12, 2), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("currency", sa.String(8), nullable=False, server_default="INR"),
        sa.Column("custom_components", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_emp_comp_tenant_emp_active", "payroll_employee_compensations", ["tenant_id", "employee_id", "is_active"])
    op.create_index("ix_emp_comp_dates", "payroll_employee_compensations", ["tenant_id", "employee_id", "effective_from", "effective_to"])

    # 6. Employee Compensation History
    op.create_table(
        "payroll_compensation_history",
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
            sa.ForeignKey("workforce_employees.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "compensation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("payroll_employee_compensations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("previous_annual_ctc", sa.Numeric(14, 2), nullable=False),
        sa.Column("new_annual_ctc", sa.Numeric(14, 2), nullable=False),
        sa.Column("previous_monthly_gross", sa.Numeric(12, 2), nullable=False),
        sa.Column("new_monthly_gross", sa.Numeric(12, 2), nullable=False),
        sa.Column("change_reason", sa.String(255), nullable=False),
        sa.Column(
            "authorized_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_comp_hist_tenant_emp", "payroll_compensation_history", ["tenant_id", "employee_id", "effective_date"])

    # 7. Employee Bank Details
    op.create_table(
        "payroll_employee_bank_details",
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
            sa.ForeignKey("workforce_employees.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("account_holder_name", sa.String(128), nullable=False),
        sa.Column("bank_name", sa.String(128), nullable=False),
        sa.Column("account_number_masked", sa.String(32), nullable=False),
        sa.Column("account_number_encrypted", sa.String(255), nullable=False),
        sa.Column("ifsc_code", sa.String(32), nullable=False),
        sa.Column("branch_name", sa.String(128), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "verified_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_bank_detail_tenant_emp", "payroll_employee_bank_details", ["tenant_id", "employee_id", "is_primary"])

    # 8. Payroll Calendars
    op.create_table(
        "payroll_calendars",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("pay_frequency", sa.String(32), nullable=False, server_default="MONTHLY"),
        sa.Column("cutoff_day_of_month", sa.Integer(), nullable=False, server_default="25"),
        sa.Column("pay_day_of_month", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "name", name="uq_payroll_calendar_tenant_name"),
    )

    # 9. Payroll Periods
    op.create_table(
        "payroll_periods",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "calendar_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("payroll_calendars.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("period_code", sa.String(32), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("cutoff_date", sa.Date(), nullable=False),
        sa.Column("is_closed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "calendar_id", "period_code", name="uq_period_tenant_code"),
    )
    op.create_index("ix_period_tenant_dates", "payroll_periods", ["tenant_id", "start_date", "end_date"])

    # 10. Payroll Runs
    op.create_table(
        "payroll_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "period_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("payroll_periods.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "calendar_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("payroll_calendars.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("run_number", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT"),
        sa.Column("is_locked", sa.Boolean(), nullable=False, server_default="false"),
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
        sa.Column("total_gross_pay", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("total_deductions", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("total_employer_contributions", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("total_net_pay", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("employee_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "approved_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "posted_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "run_number", name="uq_payroll_run_number"),
    )
    op.create_index("ix_payroll_run_tenant_status", "payroll_runs", ["tenant_id", "status"])
    op.create_index("ix_payroll_run_period", "payroll_runs", ["tenant_id", "period_id"])

    # 11. Payroll Run Items
    op.create_table(
        "payroll_run_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "payroll_run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("payroll_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "employee_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workforce_employees.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "compensation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("payroll_employee_compensations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("days_in_period", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("worked_days", sa.Numeric(5, 2), nullable=False, server_default="30.00"),
        sa.Column("paid_leave_days", sa.Numeric(5, 2), nullable=False, server_default="0.00"),
        sa.Column("unpaid_leave_days", sa.Numeric(5, 2), nullable=False, server_default="0.00"),
        sa.Column("proration_factor", sa.Numeric(7, 4), nullable=False, server_default="1.0000"),
        sa.Column("gross_earnings", sa.Numeric(12, 2), nullable=False),
        sa.Column("total_deductions", sa.Numeric(12, 2), nullable=False),
        sa.Column("employer_contributions", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("net_pay", sa.Numeric(12, 2), nullable=False),
        sa.Column("calculation_breakdown", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "payroll_run_id", "employee_id", name="uq_run_item_emp"),
    )
    op.create_index("ix_run_item_tenant_emp", "payroll_run_items", ["tenant_id", "employee_id"])

    # 12. Payroll Run Item Details
    op.create_table(
        "payroll_run_item_details",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "run_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("payroll_run_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "component_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("payroll_salary_components.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("component_name", sa.String(128), nullable=False),
        sa.Column("component_type", sa.String(32), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("calculation_notes", sa.String(255), nullable=True),
    )

    # 13. Accounting Mappings
    op.create_table(
        "payroll_accounting_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("account_code", sa.String(64), nullable=False),
        sa.Column("account_name", sa.String(128), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "category", name="uq_acct_map_tenant_cat"),
    )

    # 14. Journal Entries
    op.create_table(
        "payroll_journal_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "payroll_run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("payroll_runs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("entry_number", sa.String(64), nullable=False),
        sa.Column("entry_date", sa.Date(), nullable=False),
        sa.Column("total_debit", sa.Numeric(14, 2), nullable=False),
        sa.Column("total_credit", sa.Numeric(14, 2), nullable=False),
        sa.Column("is_balanced", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "posted_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "payroll_run_id", name="uq_pje_tenant_run"),
        sa.UniqueConstraint("tenant_id", "entry_number", name="uq_pje_tenant_num"),
    )

    # 15. Journal Lines
    op.create_table(
        "payroll_journal_lines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "journal_entry_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("payroll_journal_entries.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("account_code", sa.String(64), nullable=False),
        sa.Column("account_name", sa.String(128), nullable=False),
        sa.Column("line_type", sa.String(16), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("description", sa.String(255), nullable=True),
    )

    # 16. Payment Batches
    op.create_table(
        "payroll_payment_batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "payroll_run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("payroll_runs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("batch_number", sa.String(64), nullable=False),
        sa.Column("payment_method", sa.String(32), nullable=False, server_default="BANK_TRANSFER"),
        sa.Column("status", sa.String(32), nullable=False, server_default="PREPARED"),
        sa.Column("total_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("total_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("disbursed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("exported_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("export_format", sa.String(32), nullable=False, server_default="STANDARD_ACH_CSV"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "batch_number", name="uq_pay_batch_num"),
    )
    op.create_index("ix_pay_batch_tenant_status", "payroll_payment_batches", ["tenant_id", "status"])

    # 17. Payment Items
    op.create_table(
        "payroll_payment_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "batch_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("payroll_payment_batches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "employee_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workforce_employees.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "run_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("payroll_run_items.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("bank_name", sa.String(128), nullable=False),
        sa.Column("account_number_masked", sa.String(32), nullable=False),
        sa.Column("ifsc_code", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("transaction_reference", sa.String(128), nullable=True),
        sa.Column("reconciled_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 18. Statutory Rules
    op.create_table(
        "payroll_statutory_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("jurisdiction", sa.String(32), nullable=False),
        sa.Column("rule_code", sa.String(64), nullable=False),
        sa.Column("title", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("employee_rate", sa.Numeric(7, 4), nullable=False, server_default="0.0000"),
        sa.Column("employer_rate", sa.Numeric(7, 4), nullable=False, server_default="0.0000"),
        sa.Column("wage_ceiling", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("slab_configuration", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "rule_code", name="uq_statutory_rule_code"),
    )
    op.create_index("ix_statutory_tenant_jur", "payroll_statutory_rules", ["tenant_id", "jurisdiction", "is_active"])

    # 19. Payslips
    op.create_table(
        "payroll_payslips",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "payroll_run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("payroll_runs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "run_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("payroll_run_items.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "employee_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workforce_employees.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("payslip_number", sa.String(64), nullable=False),
        sa.Column("period_code", sa.String(32), nullable=False),
        sa.Column("gross_pay", sa.Numeric(12, 2), nullable=False),
        sa.Column("total_deductions", sa.Numeric(12, 2), nullable=False),
        sa.Column("net_pay", sa.Numeric(12, 2), nullable=False),
        sa.Column("secure_token", sa.String(64), nullable=False),
        sa.Column("storage_key", sa.String(255), nullable=True),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "payslip_number", name="uq_payslip_num"),
    )
    op.create_index("ix_payslip_tenant_emp_period", "payroll_payslips", ["tenant_id", "employee_id", "period_code"])


def downgrade() -> None:
    op.drop_table("payroll_payslips")
    op.drop_table("payroll_statutory_rules")
    op.drop_table("payroll_payment_items")
    op.drop_table("payroll_payment_batches")
    op.drop_table("payroll_journal_lines")
    op.drop_table("payroll_journal_entries")
    op.drop_table("payroll_accounting_mappings")
    op.drop_table("payroll_run_item_details")
    op.drop_table("payroll_run_items")
    op.drop_table("payroll_runs")
    op.drop_table("payroll_periods")
    op.drop_table("payroll_calendars")
    op.drop_table("payroll_employee_bank_details")
    op.drop_table("payroll_compensation_history")
    op.drop_table("payroll_employee_compensations")
    op.drop_table("payroll_salary_structure_items")
    op.drop_table("payroll_salary_structures")
    op.drop_table("payroll_salary_components")
    op.drop_table("payroll_salary_grades")
