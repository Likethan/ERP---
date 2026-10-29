"""Enterprise International Relations, Student Exchange & Global Mobility Management (Step 60).

Revision ID: 044_enterprise_international_relations_global_mobility
Revises: 043_enterprise_student_counselling_mentoring_development
Create Date: 2026-10-25 23:00:00.000000

Creates normalized tables and schema objects for:
- ir_partners: International universities, colleges, research organizations
- ir_agreements: Memoranda of Understanding (MoUs), bilateral exchange agreements, renewals
- ir_agreement_amendments: Historical revision log and amendments to institutional agreements
- ir_programs: Study-abroad offerings, semester exchange, summer schools, dual-degree pathways
- ir_applications: End-to-end student mobility applications with multi-stage reviews
- ir_application_reviews: Reviewer decision logs across department and international office
- ir_inbound_students: Inbound international exchange students, arrival, orientation, check-in
- ir_faculty_mobility: Outbound faculty exchange and visiting international scholars
- ir_course_equivalencies: Academic course equivalency mappings between partner and campus
- ir_credit_transfers: Committee-authorized academic credit transfer and recognition requests
- ir_mobility_documents: Document checklists, passport references, transcripts, insurance
- ir_scholarships: Mobility scholarships, travel grants, funding quotas
- ir_funding_requests: Student scholarship and travel funding allocation requests
- ir_policy_configs: Institutional global mobility policies and renewal notification windows
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "044_enterprise_international_relations_global_mobility"
down_revision = "043_enterprise_student_counselling_mentoring_development"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. International Partners
    op.create_table(
        "ir_partners",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False, index=True),
        sa.Column("country", sa.String(100), nullable=False, index=True),
        sa.Column("country_code", sa.String(10), nullable=True, index=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("website", sa.String(255), nullable=True),
        sa.Column("partnership_category", sa.String(50), nullable=False, server_default="BILATERAL", index=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="ACTIVE", index=True),
        sa.Column("primary_contact_name", sa.String(150), nullable=True),
        sa.Column("primary_contact_email", sa.String(150), nullable=True),
        sa.Column("primary_contact_phone", sa.String(50), nullable=True),
        sa.Column("linked_campuses", sa.JSON(), nullable=True),
        sa.Column("linked_departments", sa.JSON(), nullable=True),
        sa.Column("linked_programs", sa.JSON(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_ir_partners_tenant_country", "ir_partners", ["tenant_id", "country"])
    op.create_index("ix_ir_partners_tenant_status", "ir_partners", ["tenant_id", "status"])

    # 2. Institutional Agreements (MoUs)
    op.create_table(
        "ir_agreements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("agreement_number", sa.String(100), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("agreement_type", sa.String(50), nullable=False, server_default="MOU", index=True),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ir_partners.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("expiry_date", sa.Date(), nullable=False, index=True),
        sa.Column("renewal_reminder_days", sa.Integer(), nullable=False, server_default="90"),
        sa.Column("status", sa.String(50), nullable=False, server_default="ACTIVE", index=True),
        sa.Column("responsible_coordinator_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("scope_student_exchange", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("scope_faculty_exchange", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("scope_joint_research", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("scope_dual_degree", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("scope_internships", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("scope_collaborative_academic", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("document_url", sa.String(500), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "agreement_number", name="uq_ir_agreements_tenant_number"),
    )
    op.create_index("ix_ir_agreements_expiry", "ir_agreements", ["tenant_id", "expiry_date", "status"])

    # 3. Agreement Amendments
    op.create_table(
        "ir_agreement_amendments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("agreement_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ir_agreements.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("amendment_number", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("change_summary", sa.Text(), nullable=False),
        sa.Column("approved_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("document_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 4. Mobility Programs
    op.create_table(
        "ir_programs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("program_code", sa.String(100), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ir_partners.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("agreement_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ir_agreements.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("program_type", sa.String(50), nullable=False, server_default="SEMESTER_EXCHANGE", index=True),
        sa.Column("direction", sa.String(20), nullable=False, server_default="OUTBOUND", index=True),
        sa.Column("academic_term", sa.String(100), nullable=False),
        sa.Column("academic_year", sa.String(50), nullable=False, index=True),
        sa.Column("participating_departments", sa.JSON(), nullable=True),
        sa.Column("eligible_programs", sa.JSON(), nullable=True),
        sa.Column("total_seats_quota", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("min_cgpa_requirement", sa.Float(), nullable=False, server_default="7.0"),
        sa.Column("min_credits_requirement", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("language_requirements", sa.JSON(), nullable=True),
        sa.Column("application_open_date", sa.Date(), nullable=False),
        sa.Column("application_deadline", sa.Date(), nullable=False, index=True),
        sa.Column("duration_weeks", sa.Integer(), nullable=False, server_default="16"),
        sa.Column("academic_workload", sa.String(255), nullable=True),
        sa.Column("required_documents", sa.JSON(), nullable=True),
        sa.Column("funding_scholarship_info", sa.Text(), nullable=True),
        sa.Column("coordinator_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("faculty_contact", sa.String(255), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="DRAFT", index=True),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "program_code", name="uq_ir_programs_tenant_code"),
    )
    op.create_index("ix_ir_programs_deadline_status", "ir_programs", ["tenant_id", "application_deadline", "status"])

    # 5. Mobility Applications
    op.create_table(
        "ir_applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("application_number", sa.String(100), nullable=False, index=True),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_students.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("program_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ir_programs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("academic_term", sa.String(100), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="DRAFT", index=True),
        sa.Column("statement_of_purpose", sa.Text(), nullable=True),
        sa.Column("proposed_courses", sa.JSON(), nullable=True),
        sa.Column("student_cgpa_snapshot", sa.Float(), nullable=True),
        sa.Column("credits_completed_snapshot", sa.Integer(), nullable=True),
        sa.Column("eligibility_check_passed", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("eligibility_exception_waived", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("exception_justification", sa.Text(), nullable=True),
        sa.Column("nomination_date", sa.Date(), nullable=True),
        sa.Column("partner_decision", sa.String(50), nullable=True),
        sa.Column("partner_decision_date", sa.Date(), nullable=True),
        sa.Column("partner_decision_notes", sa.Text(), nullable=True),
        sa.Column("departure_date", sa.Date(), nullable=True),
        sa.Column("return_date", sa.Date(), nullable=True),
        sa.Column("completion_report", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "application_number", name="uq_ir_applications_tenant_num"),
        sa.UniqueConstraint("tenant_id", "student_id", "program_id", name="uq_ir_applications_student_prog"),
    )
    op.create_index("ix_ir_applications_student_status", "ir_applications", ["tenant_id", "student_id", "status"])

    # 6. Application Review History
    op.create_table(
        "ir_application_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ir_applications.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("reviewer_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("reviewer_role", sa.String(50), nullable=False),
        sa.Column("stage", sa.String(50), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 7. Inbound Students
    op.create_table(
        "ir_inbound_students",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ir_applications.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ir_partners.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("student_name", sa.String(255), nullable=False, index=True),
        sa.Column("student_email", sa.String(255), nullable=False),
        sa.Column("nationality", sa.String(100), nullable=False),
        sa.Column("passport_reference", sa.String(100), nullable=True),
        sa.Column("home_institution_student_id", sa.String(100), nullable=True),
        sa.Column("host_department_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_departments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("host_program_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_programs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("study_period_start", sa.Date(), nullable=False),
        sa.Column("study_period_end", sa.Date(), nullable=False),
        sa.Column("academic_term", sa.String(100), nullable=False),
        sa.Column("orientation_completed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("campus_card_issued", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("accommodation_status", sa.String(50), nullable=False, server_default="NOT_REQUIRED"),
        sa.Column("accommodation_reference", sa.String(255), nullable=True),
        sa.Column("academic_registration_status", sa.String(50), nullable=False, server_default="PENDING"),
        sa.Column("assigned_coordinator_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("check_in_status", sa.String(50), nullable=False, server_default="PENDING", index=True),
        sa.Column("check_in_date", sa.Date(), nullable=True),
        sa.Column("departure_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_ir_inbound_status", "ir_inbound_students", ["tenant_id", "check_in_status"])

    # 8. Faculty Mobility & Visiting Scholars
    op.create_table(
        "ir_faculty_mobility",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("staff_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("scholar_name", sa.String(255), nullable=False),
        sa.Column("scholar_email", sa.String(255), nullable=False),
        sa.Column("mobility_type", sa.String(50), nullable=False, server_default="OUTBOUND_FACULTY", index=True),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ir_partners.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("home_institution_name", sa.String(255), nullable=False),
        sa.Column("host_department_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_departments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("visit_start_date", sa.Date(), nullable=False),
        sa.Column("visit_end_date", sa.Date(), nullable=False),
        sa.Column("objectives", sa.Text(), nullable=False),
        sa.Column("invitation_letter_ref", sa.String(500), nullable=True),
        sa.Column("academic_visit_plan", sa.JSON(), nullable=True),
        sa.Column("research_project_link", sa.String(255), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="DRAFT", index=True),
        sa.Column("hod_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("vp_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("outcomes_report", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_ir_faculty_dates", "ir_faculty_mobility", ["tenant_id", "visit_start_date", "visit_end_date"])

    # 9. Course Equivalency Mappings
    op.create_table(
        "ir_course_equivalencies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ir_partners.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("partner_course_code", sa.String(50), nullable=False),
        sa.Column("partner_course_title", sa.String(255), nullable=False),
        sa.Column("partner_credits", sa.Float(), nullable=False, server_default="4.0"),
        sa.Column("grading_scale_info", sa.String(100), nullable=True),
        sa.Column("syllabus_document_url", sa.String(500), nullable=True),
        sa.Column("learning_outcomes", sa.Text(), nullable=True),
        sa.Column("campus_program_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_programs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("campus_course_code", sa.String(50), nullable=False),
        sa.Column("campus_course_title", sa.String(255), nullable=False),
        sa.Column("campus_credits", sa.Float(), nullable=False, server_default="4.0"),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_departments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="PROPOSED", index=True),
        sa.Column("reviewer_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("committee_notes", sa.Text(), nullable=True),
        sa.Column("conditions", sa.Text(), nullable=True),
        sa.Column("effective_academic_year", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "partner_id", "partner_course_code", "campus_course_code", name="uq_ir_course_equiv"),
    )

    # 10. Student Credit Transfer Requests
    op.create_table(
        "ir_credit_transfers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ir_applications.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_students.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("host_transcript_doc_url", sa.String(500), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="SUBMITTED", index=True),
        sa.Column("mapped_courses_summary", sa.JSON(), nullable=True),
        sa.Column("total_credits_requested", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("total_credits_approved", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("committee_approval_ref", sa.String(100), nullable=True),
        sa.Column("authorized_date", sa.Date(), nullable=True),
        sa.Column("authorized_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 11. Mobility Documents
    op.create_table(
        "ir_mobility_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ir_applications.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("inbound_student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ir_inbound_students.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("faculty_mobility_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ir_faculty_mobility.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("document_type", sa.String(50), nullable=False, server_default="PASSPORT", index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("file_url", sa.String(500), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("submission_date", sa.Date(), nullable=False),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("verification_status", sa.String(50), nullable=False, server_default="PENDING", index=True),
        sa.Column("verification_notes", sa.Text(), nullable=True),
        sa.Column("verified_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_ir_docs_status", "ir_mobility_documents", ["tenant_id", "verification_status"])

    # 12. Mobility Scholarships
    op.create_table(
        "ir_scholarships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("code", sa.String(100), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("sponsor_organization", sa.String(255), nullable=False),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ir_partners.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("award_amount", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("currency", sa.String(10), nullable=False, server_default="USD"),
        sa.Column("eligibility_criteria", sa.Text(), nullable=False),
        sa.Column("application_deadline", sa.Date(), nullable=False, index=True),
        sa.Column("total_quota_seats", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("status", sa.String(50), nullable=False, server_default="ACTIVE", index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_ir_scholarships_tenant_code"),
    )

    # 13. Mobility Funding Requests
    op.create_table(
        "ir_funding_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ir_applications.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_students.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("scholarship_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ir_scholarships.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("funding_type", sa.String(50), nullable=False, server_default="SCHOLARSHIP"),
        sa.Column("requested_amount", sa.Float(), nullable=False),
        sa.Column("approved_amount", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(10), nullable=False, server_default="USD"),
        sa.Column("status", sa.String(50), nullable=False, server_default="PROPOSED", index=True),
        sa.Column("finance_disbursement_ref", sa.String(100), nullable=True),
        sa.Column("estimated_total_program_cost", sa.Float(), nullable=True),
        sa.Column("student_funding_gap", sa.Float(), nullable=True),
        sa.Column("approved_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 14. International Policy Config
    op.create_table(
        "ir_policy_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True, index=True),
        sa.Column("agreement_renewal_notice_days", sa.Integer(), nullable=False, server_default="90"),
        sa.Column("default_max_outbound_nominations", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("require_hod_approval", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("require_vp_approval", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("allow_student_self_nomination", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("credit_transfer_committee_required", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("enable_inbound_mobility", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("enable_faculty_exchange", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("ir_policy_configs")
    op.drop_table("ir_funding_requests")
    op.drop_table("ir_scholarships")
    op.drop_table("ir_mobility_documents")
    op.drop_table("ir_credit_transfers")
    op.drop_table("ir_course_equivalencies")
    op.drop_table("ir_faculty_mobility")
    op.drop_table("ir_inbound_students")
    op.drop_table("ir_application_reviews")
    op.drop_table("ir_applications")
    op.drop_table("ir_programs")
    op.drop_table("ir_agreement_amendments")
    op.drop_table("ir_agreements")
    op.drop_table("ir_partners")
