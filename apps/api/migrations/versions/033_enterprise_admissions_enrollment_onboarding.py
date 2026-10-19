"""Enterprise Student Lifecycle, Admissions, Enrollment & Onboarding Orchestration (Step 48).

Revision ID: 033_enterprise_admissions_enrollment_onboarding
Revises: 032_enterprise_student_success_advising_early_warning
Create Date: 2026-10-19 18:00:00.000000

Creates normalized tables for:
- admissions_cycles: Configurable admission cycles per academic year
- admissions_applicants: Prospective student applicant profiles, identity, and duplicate tracking
- admissions_applications: Formal admission applications with program choices and status lifecycle
- admissions_program_choices: Ranked program preferences on applications
- admissions_document_requirements: Configurable required evidence definitions
- admissions_documents: Uploaded applicant evidence, verification status, and reviewer notes
- admissions_eligibility_rules: Versioned eligibility rules and threshold criteria
- admissions_eligibility_evaluations: Explainable automated evaluation logs
- admissions_reviews: Reviewer evaluations, multi-tier notes, scores, and decisions
- admissions_seat_allocations: Program and category seat capacity with concurrency-safe allocation
- admissions_selection_runs: Selection rounds and merit list publishing
- admissions_selection_results: Individual applicant merit rank, score, and outcome
- admissions_offers: Generated admission offers with expiry deadlines and stipulations
- admissions_enrollment_workflows: Idempotent student-record creation connecting offers to StudentProfile
- admissions_onboarding_checklists: Post-enrollment institutional onboarding coordination
- admissions_onboarding_tasks: Verifiable onboarding tasks and completion tracking
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "033_enterprise_admissions_enrollment_onboarding"
down_revision = "032_enterprise_student_success_advising_early_warning"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Admission Cycles
    op.create_table(
        "admissions_cycles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "academic_year_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_academic_years.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("admission_term", sa.String(32), nullable=False, server_default="FALL"),
        sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT"),
        sa.Column("application_start_date", sa.Date(), nullable=False),
        sa.Column("application_end_date", sa.Date(), nullable=False),
        sa.Column("document_deadline", sa.Date(), nullable=False),
        sa.Column("offer_acceptance_deadline", sa.Date(), nullable=False),
        sa.Column("publication_date", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("settings", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("total_applications_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_enrolled_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_admissions_cycles_tenant_code"),
    )
    op.create_index("idx_adm_cycle_tenant_status", "admissions_cycles", ["tenant_id", "status"])
    op.create_index(
        "idx_adm_cycle_tenant_dates",
        "admissions_cycles",
        ["tenant_id", "application_start_date", "application_end_date"],
    )

    # 2. Applicant Profiles
    op.create_table(
        "admissions_applicants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("applicant_number", sa.String(64), nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone_number", sa.String(32), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("gender", sa.String(16), nullable=False),
        sa.Column("nationality", sa.String(64), nullable=False, server_default="Indian"),
        sa.Column("address_line1", sa.String(255), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("postal_code", sa.String(32), nullable=True),
        sa.Column("country", sa.String(100), nullable=False, server_default="India"),
        sa.Column("emergency_contact_name", sa.String(128), nullable=True),
        sa.Column("emergency_contact_phone", sa.String(32), nullable=True),
        sa.Column("verification_status", sa.String(32), nullable=False, server_default="PENDING_VERIFICATION"),
        sa.Column("is_duplicate", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "merged_into_applicant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admissions_applicants.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("merge_reason", sa.Text(), nullable=True),
        sa.Column("merged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "applicant_number", name="uq_admissions_applicants_number"),
    )
    op.create_index("idx_adm_applicant_tenant_email", "admissions_applicants", ["tenant_id", "email"])
    op.create_index("idx_adm_applicant_tenant_phone", "admissions_applicants", ["tenant_id", "phone_number"])

    # 3. Admission Applications
    op.create_table(
        "admissions_applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "cycle_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admissions_cycles.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "applicant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admissions_applicants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("application_number", sa.String(64), nullable=False),
        sa.Column(
            "program_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_programs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "campus_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_campuses.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("admission_category", sa.String(32), nullable=False, server_default="GENERAL"),
        sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT"),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("correction_window_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("qualifying_exam_name", sa.String(128), nullable=True),
        sa.Column("qualifying_exam_score", sa.Numeric(6, 2), nullable=True),
        sa.Column("qualifying_exam_max_score", sa.Numeric(6, 2), nullable=True),
        sa.Column("qualifying_percentage", sa.Numeric(5, 2), nullable=True),
        sa.Column("application_fee_paid", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("payment_reference", sa.String(128), nullable=True),
        sa.Column("withdrawal_reason", sa.Text(), nullable=True),
        sa.Column("reopened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "reopened_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reopening_reason", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "application_number", name="uq_admissions_app_number"),
    )
    op.create_index("idx_adm_app_tenant_cycle", "admissions_applications", ["tenant_id", "cycle_id"])
    op.create_index("idx_adm_app_tenant_applicant", "admissions_applications", ["tenant_id", "applicant_id"])
    op.create_index("idx_adm_app_tenant_status", "admissions_applications", ["tenant_id", "status"])
    op.create_index("idx_adm_app_tenant_program", "admissions_applications", ["tenant_id", "program_id"])

    # 4. Application Program Choices
    op.create_table(
        "admissions_program_choices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admissions_applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "program_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_programs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "campus_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_campuses.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("preference_rank", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("application_id", "preference_rank", name="uq_app_choice_rank"),
    )
    op.create_index("idx_adm_choice_app_rank", "admissions_program_choices", ["application_id", "preference_rank"])

    # 5. Document Requirements
    op.create_table(
        "admissions_document_requirements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "cycle_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admissions_cycles.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "program_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_programs.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("document_name", sa.String(128), nullable=False),
        sa.Column("document_code", sa.String(64), nullable=False),
        sa.Column("is_mandatory", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_adm_doc_req_tenant_cycle", "admissions_document_requirements", ["tenant_id", "cycle_id"])
    op.create_index("idx_adm_doc_req_tenant_prog", "admissions_document_requirements", ["tenant_id", "program_id"])

    # 6. Application Documents
    op.create_table(
        "admissions_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admissions_applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "requirement_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admissions_document_requirements.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("document_name", sa.String(128), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("mime_type", sa.String(128), nullable=False, server_default="application/pdf"),
        sa.Column("storage_key", sa.String(255), nullable=False),
        sa.Column("verification_status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column(
            "verified_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_adm_doc_tenant_app", "admissions_documents", ["tenant_id", "application_id"])
    op.create_index("idx_adm_doc_tenant_status", "admissions_documents", ["tenant_id", "verification_status"])

    # 7. Eligibility Rules
    op.create_table(
        "admissions_eligibility_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "cycle_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admissions_cycles.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "program_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_programs.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("min_score_percentage", sa.Numeric(5, 2), nullable=False, server_default="50.00"),
        sa.Column("required_qualification", sa.String(128), nullable=True),
        sa.Column("rule_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("criteria_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_admissions_elig_rule_code"),
    )
    op.create_index(
        "idx_adm_elig_tenant_cycle_prog",
        "admissions_eligibility_rules",
        ["tenant_id", "cycle_id", "program_id"],
    )

    # 8. Eligibility Evaluations
    op.create_table(
        "admissions_eligibility_evaluations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admissions_applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "rule_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admissions_eligibility_rules.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("rule_version", sa.Integer(), nullable=False),
        sa.Column("is_eligible", sa.Boolean(), nullable=False),
        sa.Column("observed_percentage", sa.Numeric(5, 2), nullable=True),
        sa.Column("evaluation_summary", sa.Text(), nullable=True),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "evaluated_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_adm_eval_tenant_app", "admissions_eligibility_evaluations", ["tenant_id", "application_id"])

    # 9. Application Reviews
    op.create_table(
        "admissions_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admissions_applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "reviewer_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("review_stage", sa.String(32), nullable=False, server_default="ACADEMIC_REVIEW"),
        sa.Column("score", sa.Numeric(5, 2), nullable=True),
        sa.Column("decision", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("reviewer_notes", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_completed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_adm_review_tenant_app", "admissions_reviews", ["tenant_id", "application_id"])
    op.create_index("idx_adm_review_tenant_reviewer", "admissions_reviews", ["tenant_id", "reviewer_user_id"])

    # 10. Seat Allocations
    op.create_table(
        "admissions_seat_allocations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "cycle_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admissions_cycles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "program_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_programs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "campus_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_campuses.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("admission_category", sa.String(32), nullable=False, server_default="GENERAL"),
        sa.Column("total_capacity", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("reserved_seats", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("confirmed_seats", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("waitlist_capacity", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "tenant_id",
            "cycle_id",
            "program_id",
            "campus_id",
            "admission_category",
            name="uq_admissions_seat_alloc_composite",
        ),
    )
    op.create_index(
        "idx_adm_seat_tenant_cycle_prog",
        "admissions_seat_allocations",
        ["tenant_id", "cycle_id", "program_id"],
    )

    # 11. Selection Runs
    op.create_table(
        "admissions_selection_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "cycle_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admissions_cycles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "program_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_programs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("run_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("cutoff_score", sa.Numeric(6, 2), nullable=True),
        sa.Column("total_selected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_waitlisted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_approved", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "approved_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "idx_adm_sel_tenant_cycle_prog",
        "admissions_selection_runs",
        ["tenant_id", "cycle_id", "program_id"],
    )

    # 12. Selection Results
    op.create_table(
        "admissions_selection_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "selection_run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admissions_selection_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admissions_applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "applicant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admissions_applicants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("merit_rank", sa.Integer(), nullable=False),
        sa.Column("merit_score", sa.Numeric(6, 2), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="SELECTED"),
        sa.Column("waitlist_rank", sa.Integer(), nullable=True),
        sa.Column("seat_offered", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("selection_run_id", "application_id", name="uq_adm_sel_run_app"),
    )
    op.create_index("idx_adm_sel_res_tenant_run", "admissions_selection_results", ["tenant_id", "selection_run_id"])
    op.create_index("idx_adm_sel_res_tenant_app", "admissions_selection_results", ["tenant_id", "application_id"])

    # 13. Admission Offers
    op.create_table(
        "admissions_offers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admissions_applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "applicant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admissions_applicants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "program_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_programs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "cycle_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admissions_cycles.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("offer_number", sa.String(64), nullable=False),
        sa.Column("offer_date", sa.Date(), nullable=False),
        sa.Column("expiry_date", sa.Date(), nullable=False),
        sa.Column("deposit_required", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("conditions_text", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="ISSUED"),
        sa.Column("response_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decline_reason", sa.Text(), nullable=True),
        sa.Column("revocation_reason", sa.Text(), nullable=True),
        sa.Column(
            "revoked_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "offer_number", name="uq_admissions_offers_number"),
    )
    op.create_index("idx_adm_offer_tenant_app", "admissions_offers", ["tenant_id", "application_id"])
    op.create_index("idx_adm_offer_tenant_status", "admissions_offers", ["tenant_id", "status"])
    op.create_index(
        "idx_adm_offer_tenant_expiry",
        "admissions_offers",
        ["tenant_id", "expiry_date", "status"],
    )

    # 14. Enrollment Workflows
    op.create_table(
        "admissions_enrollment_workflows",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admissions_applications.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "offer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admissions_offers.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "applicant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admissions_applicants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_students.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("workflow_number", sa.String(64), nullable=False),
        sa.Column(
            "batch_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_batches.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "current_semester_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_semesters.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "current_section_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_sections.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("status", sa.String(32), nullable=False, server_default="INITIATED"),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("failure_stage", sa.String(64), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_student_admission_number", sa.String(64), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "workflow_number", name="uq_admissions_enr_wf_number"),
        sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_admissions_enr_idempotency"),
    )
    op.create_index("idx_adm_enr_tenant_app", "admissions_enrollment_workflows", ["tenant_id", "application_id"])
    op.create_index("idx_adm_enr_tenant_offer", "admissions_enrollment_workflows", ["tenant_id", "offer_id"])
    op.create_index("idx_adm_enr_tenant_student", "admissions_enrollment_workflows", ["tenant_id", "student_id"])

    # 15. Onboarding Checklists
    op.create_table(
        "admissions_onboarding_checklists",
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
            sa.ForeignKey("people_students.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "enrollment_workflow_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admissions_enrollment_workflows.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="IN_PROGRESS"),
        sa.Column("total_tasks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_tasks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("target_completion_date", sa.Date(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "student_id", name="uq_adm_onboarding_student"),
    )
    op.create_index(
        "idx_adm_onboarding_tenant_status",
        "admissions_onboarding_checklists",
        ["tenant_id", "status"],
    )

    # 16. Onboarding Tasks
    op.create_table(
        "admissions_onboarding_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "checklist_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("admissions_onboarding_checklists.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(128), nullable=False),
        sa.Column("task_category", sa.String(32), nullable=False, server_default="ADMINISTRATIVE"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_mandatory", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "verified_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("verification_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "idx_adm_onboarding_task_tenant_checklist",
        "admissions_onboarding_tasks",
        ["tenant_id", "checklist_id"],
    )
    op.create_index(
        "idx_adm_onboarding_task_tenant_status",
        "admissions_onboarding_tasks",
        ["tenant_id", "status"],
    )


def downgrade() -> None:
    op.drop_table("admissions_onboarding_tasks")
    op.drop_table("admissions_onboarding_checklists")
    op.drop_table("admissions_enrollment_workflows")
    op.drop_table("admissions_offers")
    op.drop_table("admissions_selection_results")
    op.drop_table("admissions_selection_runs")
    op.drop_table("admissions_seat_allocations")
    op.drop_table("admissions_reviews")
    op.drop_table("admissions_eligibility_evaluations")
    op.drop_table("admissions_eligibility_rules")
    op.drop_table("admissions_documents")
    op.drop_table("admissions_document_requirements")
    op.drop_table("admissions_program_choices")
    op.drop_table("admissions_applications")
    op.drop_table("admissions_applicants")
    op.drop_table("admissions_cycles")
