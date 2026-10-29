"""Enterprise Student Engagement, Community Service, Volunteering & Civic Impact Management (Step 65).

Revision ID: 047_enterprise_student_engagement_civic_impact
Revises: 046_enterprise_legal_affairs_contract_lifecycle_compliance_risk
Create Date: 2026-10-28 12:00:00.000000

Creates domain tables and indexes for:
- engagement_community_partners
- engagement_programs
- engagement_opportunities
- engagement_applications
- engagement_shifts
- engagement_shift_assignments
- engagement_attendances
- engagement_service_hours
- engagement_hour_corrections
- engagement_reflections
- engagement_safety_consents
- engagement_certificates
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "047_enterprise_student_engagement_civic_impact"
down_revision = "046_enterprise_legal_affairs_contract_lifecycle_compliance_risk"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Community Partners
    op.create_table(
        "engagement_community_partners",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("organization_type", sa.String(64), nullable=False, server_default="NON_PROFIT"),
        sa.Column("registration_number", sa.String(128), nullable=True),
        sa.Column("website", sa.String(255), nullable=True),
        sa.Column("primary_contact_name", sa.String(255), nullable=False),
        sa.Column("primary_contact_email", sa.String(255), nullable=False),
        sa.Column("primary_contact_phone", sa.String(64), nullable=True),
        sa.Column("authorized_representative_name", sa.String(255), nullable=True),
        sa.Column("authorized_representative_title", sa.String(128), nullable=True),
        sa.Column("authorized_representative_email", sa.String(255), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"),
        sa.Column("partnership_purpose", sa.Text(), nullable=True),
        sa.Column("engagement_categories", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("agreement_reference", sa.String(128), nullable=True),
        sa.Column("mou_document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column("review_date", sa.Date(), nullable=True),
        sa.Column("coordinator_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("impact_summary_json", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("verified_hours_contributed", sa.Numeric(10, 2), server_default="0.00", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "name", name="uq_engagement_partner_tenant_name"),
    )
    op.create_index("idx_eng_partner_tenant_status", "engagement_community_partners", ["tenant_id", "status"])
    op.create_index("idx_eng_partner_tenant_type", "engagement_community_partners", ["tenant_id", "organization_type"])

    # 2. Engagement Programs
    op.create_table(
        "engagement_programs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(64), nullable=False, server_default="COMMUNITY_SERVICE"),
        sa.Column("objectives", sa.Text(), nullable=True),
        sa.Column("campus_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_campuses.id", ondelete="SET NULL"), nullable=True),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_departments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("coordinator_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("community_partner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("engagement_community_partners.id", ondelete="SET NULL"), nullable=True),
        sa.Column("target_audience", sa.String(255), nullable=True),
        sa.Column("student_eligibility_criteria", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("registration_deadline", sa.Date(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT"),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("target_service_hours", sa.Numeric(6, 2), nullable=False, server_default="20.00"),
        sa.Column("skills_required", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("prerequisites", sa.Text(), nullable=True),
        sa.Column("accessibility_considerations", sa.Text(), nullable=True),
        sa.Column("delivery_mode", sa.String(32), nullable=False, server_default="ON_CAMPUS"),
        sa.Column("location_name", sa.String(255), nullable=True),
        sa.Column("location_address", sa.Text(), nullable=True),
        sa.Column("approver_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approval_notes", sa.Text(), nullable=True),
        sa.Column("expected_outcomes", sa.Text(), nullable=True),
        sa.Column("sdg_goals", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("safety_requirements_json", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("consent_required", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_eng_prog_tenant_code"),
    )
    op.create_index("idx_eng_prog_tenant_status", "engagement_programs", ["tenant_id", "status"])
    op.create_index("idx_eng_prog_tenant_category", "engagement_programs", ["tenant_id", "category"])
    op.create_index("idx_eng_prog_tenant_dept", "engagement_programs", ["tenant_id", "department_id"])
    op.create_index("idx_eng_prog_tenant_dates", "engagement_programs", ["tenant_id", "start_date", "end_date"])

    # 3. Volunteer Opportunities
    op.create_table(
        "engagement_opportunities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("program_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("engagement_programs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(64), nullable=False, server_default="COMMUNITY_SERVICE"),
        sa.Column("required_skills", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("eligibility_criteria", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("available_positions", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("waitlist_capacity", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("application_deadline", sa.Date(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=True),
        sa.Column("end_time", sa.Time(), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("delivery_mode", sa.String(32), nullable=False, server_default="ON_CAMPUS"),
        sa.Column("expected_hours", sa.Numeric(6, 2), nullable=False, server_default="10.00"),
        sa.Column("shifts_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(32), nullable=False, server_default="PUBLISHED"),
        sa.Column("prerequisites", sa.Text(), nullable=True),
        sa.Column("safety_guidance", sa.Text(), nullable=True),
        sa.Column("coordinator_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("engagement_community_partners.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_eng_opp_tenant_prog", "engagement_opportunities", ["tenant_id", "program_id"])
    op.create_index("idx_eng_opp_tenant_status", "engagement_opportunities", ["tenant_id", "status"])
    op.create_index("idx_eng_opp_tenant_dates", "engagement_opportunities", ["tenant_id", "start_date", "end_date"])

    # 4. Participation Applications
    op.create_table(
        "engagement_applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("engagement_opportunities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("program_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("engagement_programs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="APPLIED"),
        sa.Column("applied_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewer_notes", sa.Text(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("waitlist_position", sa.Integer(), nullable=True),
        sa.Column("statement_of_purpose", sa.Text(), nullable=True),
        sa.Column("skills_declared", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("consent_confirmed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("consent_signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("emergency_contact_name", sa.String(255), nullable=True),
        sa.Column("emergency_contact_phone", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "opportunity_id", "student_id", name="uq_eng_app_tenant_opp_student"),
    )
    op.create_index("idx_eng_app_tenant_student", "engagement_applications", ["tenant_id", "student_id"])
    op.create_index("idx_eng_app_tenant_status", "engagement_applications", ["tenant_id", "status"])
    op.create_index("idx_eng_app_tenant_prog", "engagement_applications", ["tenant_id", "program_id"])

    # 5. Volunteer Shifts
    op.create_table(
        "engagement_shifts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("engagement_opportunities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("program_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("engagement_programs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("shift_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("assigned_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("supervisor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="SCHEDULED"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_eng_shift_tenant_opp", "engagement_shifts", ["tenant_id", "opportunity_id"])
    op.create_index("idx_eng_shift_tenant_date", "engagement_shifts", ["tenant_id", "shift_date"])

    # 6. Shift Assignments
    op.create_table(
        "engagement_shift_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("shift_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("engagement_shifts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("engagement_applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="ASSIGNED"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "shift_id", "student_id", name="uq_eng_shift_student"),
    )
    op.create_index("idx_eng_assign_tenant_shift", "engagement_shift_assignments", ["tenant_id", "shift_id"])
    op.create_index("idx_eng_assign_tenant_student", "engagement_shift_assignments", ["tenant_id", "student_id"])

    # 7. Attendances
    op.create_table(
        "engagement_attendances",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("shift_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("engagement_shifts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("engagement_opportunities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("program_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("engagement_programs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("check_in_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("check_out_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verification_method", sa.String(32), nullable=False, server_default="COORDINATOR_CONFIRMED"),
        sa.Column("verified_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="COMPLETED"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_eng_att_tenant_student", "engagement_attendances", ["tenant_id", "student_id"])
    op.create_index("idx_eng_att_tenant_prog", "engagement_attendances", ["tenant_id", "program_id"])
    op.create_index("idx_eng_att_tenant_shift", "engagement_attendances", ["tenant_id", "shift_id"])

    # 8. Service Hours
    op.create_table(
        "engagement_service_hours",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("program_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("engagement_programs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("engagement_opportunities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("shift_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("engagement_shifts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("attendance_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("engagement_attendances.id", ondelete="SET NULL"), nullable=True),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("service_date", sa.Date(), nullable=False),
        sa.Column("duration_hours", sa.Numeric(5, 2), nullable=False),
        sa.Column("description_of_work", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("verified_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("supervisor_comments", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_eng_hours_tenant_student", "engagement_service_hours", ["tenant_id", "student_id"])
    op.create_index("idx_eng_hours_tenant_status", "engagement_service_hours", ["tenant_id", "status"])
    op.create_index("idx_eng_hours_tenant_prog", "engagement_service_hours", ["tenant_id", "program_id"])
    op.create_index("idx_eng_hours_tenant_date", "engagement_service_hours", ["tenant_id", "service_date"])

    # 9. Hour Corrections Ledger
    op.create_table(
        "engagement_hour_corrections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("service_hour_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("engagement_service_hours.id", ondelete="CASCADE"), nullable=False),
        sa.Column("previous_hours", sa.Numeric(5, 2), nullable=False),
        sa.Column("new_hours", sa.Numeric(5, 2), nullable=False),
        sa.Column("reason_for_change", sa.Text(), nullable=False),
        sa.Column("changed_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_eng_correct_hour_id", "engagement_hour_corrections", ["service_hour_id"])
    op.create_index("idx_eng_correct_tenant", "engagement_hour_corrections", ["tenant_id"])

    # 10. Reflections
    op.create_table(
        "engagement_reflections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("program_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("engagement_programs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("engagement_opportunities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reflection_text", sa.Text(), nullable=False),
        sa.Column("learning_outcomes_summary", sa.Text(), nullable=True),
        sa.Column("skills_developed", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("community_outcomes", sa.Text(), nullable=True),
        sa.Column("deliverables_description", sa.Text(), nullable=True),
        sa.Column("sdg_impact_mapping", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("attachment_document_ids", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("consent_for_impact_showcase", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("status", sa.String(32), nullable=False, server_default="SUBMITTED"),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("feedback_text", sa.Text(), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_eng_refl_tenant_student", "engagement_reflections", ["tenant_id", "student_id"])
    op.create_index("idx_eng_refl_tenant_prog", "engagement_reflections", ["tenant_id", "program_id"])
    op.create_index("idx_eng_refl_tenant_status", "engagement_reflections", ["tenant_id", "status"])

    # 11. Safety & Consent Records
    op.create_table(
        "engagement_safety_consents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("program_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("engagement_programs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("safety_briefing_acknowledged", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("safety_acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("parental_consent_required", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("parental_consent_received", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("risk_assessment_acknowledged", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("emergency_contact_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("incident_reference_id", sa.String(64), nullable=True),
        sa.Column("coordinator_clearance_status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("coordinator_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("cleared_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "program_id", "student_id", name="uq_eng_safety_prog_student"),
    )
    op.create_index("idx_eng_safety_tenant_status", "engagement_safety_consents", ["tenant_id", "coordinator_clearance_status"])

    # 12. Engagement Certificates
    op.create_table(
        "engagement_certificates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("certificate_number", sa.String(64), nullable=False),
        sa.Column("program_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("engagement_programs.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_students.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("recipient_name", sa.String(255), nullable=False),
        sa.Column("recipient_roll_number", sa.String(64), nullable=False),
        sa.Column("recipient_department", sa.String(128), nullable=False),
        sa.Column("total_verified_hours", sa.Numeric(6, 2), nullable=False),
        sa.Column("service_category", sa.String(64), nullable=False),
        sa.Column("program_name", sa.String(255), nullable=False),
        sa.Column("skills_certified", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("issue_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("issuing_authority_name", sa.String(255), nullable=False),
        sa.Column("issued_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("verification_hash", sa.String(64), nullable=False),
        sa.Column("qr_verification_url", sa.String(512), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="ISSUED"),
        sa.Column("revocation_reason", sa.Text(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("document_storage_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "certificate_number", name="uq_eng_cert_number"),
    )
    op.create_index("idx_eng_cert_tenant_student", "engagement_certificates", ["tenant_id", "student_id"])
    op.create_index("idx_eng_cert_tenant_hash", "engagement_certificates", ["tenant_id", "verification_hash"])


def downgrade() -> None:
    op.drop_table("engagement_certificates")
    op.drop_table("engagement_safety_consents")
    op.drop_table("engagement_reflections")
    op.drop_table("engagement_hour_corrections")
    op.drop_table("engagement_service_hours")
    op.drop_table("engagement_attendances")
    op.drop_table("engagement_shift_assignments")
    op.drop_table("engagement_shifts")
    op.drop_table("engagement_applications")
    op.drop_table("engagement_opportunities")
    op.drop_table("engagement_programs")
    op.drop_table("engagement_community_partners")

