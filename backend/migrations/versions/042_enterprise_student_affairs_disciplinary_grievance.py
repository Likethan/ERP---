"""Enterprise Student Affairs, Grievance Redressal & Disciplinary Case Management (Step 58).

Revision ID: 042_enterprise_student_affairs_disciplinary_grievance
Revises: 041_enterprise_sports_athletics_recreation_management
Create Date: 2026-10-24 23:30:00.000000

Creates normalized tables and schema objects for:
- sa_offices: Student affairs offices, campus locations, dean/director leadership
- sa_categories: Grievance classifications, SLA response & resolution targets, confidentiality flags
- sa_cases: Core grievances, complaints, inquiries, anonymous submissions, SLA tracking
- sa_case_participants: Stakeholders, investigators, panel members, conflict declarations
- sa_assignment_history: Auditable assignment and conflict-of-interest reassignment logs
- sa_disciplinary_proceedings: Formal disciplinary cases, procedural milestones, findings, sanctions
- sa_case_evidence: Secure evidence documents, redactions, access tiers, preservation of originals
- sa_case_meetings: Hearings, panel reviews, mediation sessions, agreed actions
- sa_case_communications: Confidential threaded messages within case portal
- sa_resolution_actions: Corrective remedies, policy revisions, restitution tracking
- sa_appeals: Formal appeals against disciplinary decisions with separation-of-duties enforcement
- sa_case_escalations: Safeguarding and urgent executive safety referrals
- sa_access_audits: Immutable case access, evidence view, and export audit trails
- sa_policy_configs: Institutional rules, SLA limits, appeal windows, safeguarding policies
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "042_enterprise_student_affairs_disciplinary_grievance"
down_revision = "041_enterprise_sports_athletics_recreation_management"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Student Affairs Offices
    op.create_table(
        "sa_offices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "campus_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_campuses.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "dean_or_director_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_staff.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("contact_email", sa.String(128), nullable=True),
        sa.Column("contact_phone", sa.String(32), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_sa_office_tenant_code"),
    )
    op.create_index("idx_sa_office_tenant_status", "sa_offices", ["tenant_id", "is_active"])

    # 2. Grievance Categories
    op.create_table(
        "sa_categories",
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
        sa.Column("case_type", sa.String(32), server_default="GRIEVANCE", nullable=False),
        sa.Column("default_priority", sa.String(32), server_default="MEDIUM", nullable=False),
        sa.Column("sla_response_hours", sa.Integer(), server_default=sa.text("48"), nullable=False),
        sa.Column("sla_resolution_days", sa.Integer(), server_default=sa.text("15"), nullable=False),
        sa.Column("requires_confidentiality", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("allow_anonymous", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_sa_category_tenant_code"),
    )
    op.create_index("idx_sa_category_active", "sa_categories", ["tenant_id", "is_active"])

    # 3. Grievance Cases
    op.create_table(
        "sa_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("case_number", sa.String(64), nullable=False),
        sa.Column("case_type", sa.String(32), server_default="GRIEVANCE", nullable=False),
        sa.Column(
            "category_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sa_categories.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("requested_resolution", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), server_default="SUBMITTED", nullable=False),
        sa.Column("priority", sa.String(32), server_default="MEDIUM", nullable=False),
        sa.Column("confidentiality_level", sa.String(32), server_default="STANDARD", nullable=False),
        sa.Column("is_anonymous", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("submitter_type", sa.String(32), server_default="STUDENT", nullable=False),
        sa.Column(
            "submitter_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "submitter_student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("submitter_name_redacted", sa.String(128), server_default="Anonymous Submitter", nullable=False),
        sa.Column(
            "campus_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_campuses.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "assigned_office_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sa_offices.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "assigned_officer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_staff.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("target_response_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("target_resolution_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_escalated", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("escalation_reason", sa.Text(), nullable=True),
        sa.Column("resolution_summary", sa.Text(), nullable=True),
        sa.Column("resolution_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reopen_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "case_number", name="uq_sa_case_tenant_number"),
    )
    op.create_index("idx_sa_case_tenant_status", "sa_cases", ["tenant_id", "status"])
    op.create_index("idx_sa_case_tenant_priority", "sa_cases", ["tenant_id", "priority"])
    op.create_index("idx_sa_case_tenant_officer", "sa_cases", ["tenant_id", "assigned_officer_id"])
    op.create_index("idx_sa_case_tenant_type", "sa_cases", ["tenant_id", "case_type"])
    op.create_index("idx_sa_case_confidentiality", "sa_cases", ["tenant_id", "confidentiality_level"])

    # 4. Case Participants
    op.create_table(
        "sa_case_participants",
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
            sa.ForeignKey("sa_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(32), server_default="SUBMITTER", nullable=False),
        sa.Column("is_confidential", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("has_conflict_of_interest", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("conflict_declared_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("conflict_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "case_id", "user_id", "role", name="uq_sa_participant_case_role"),
    )
    op.create_index("idx_sa_part_user", "sa_case_participants", ["tenant_id", "user_id"])
    op.create_index("idx_sa_part_case", "sa_case_participants", ["tenant_id", "case_id"])

    # 5. Case Assignment History
    op.create_table(
        "sa_assignment_history",
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
            sa.ForeignKey("sa_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "previous_officer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_staff.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "new_officer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_staff.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "assigned_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_sa_assign_case", "sa_assignment_history", ["tenant_id", "case_id"])

    # 6. Disciplinary Proceedings
    op.create_table(
        "sa_disciplinary_proceedings",
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
            sa.ForeignKey("sa_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "respondent_student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("allegation_summary", sa.Text(), nullable=False),
        sa.Column("policy_provisions_violated", sa.Text(), nullable=False),
        sa.Column("procedural_stage", sa.String(32), server_default="NOTICE_ISSUED", nullable=False),
        sa.Column("notice_issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("response_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("respondent_plea", sa.String(64), nullable=True),
        sa.Column("findings_summary", sa.Text(), nullable=True),
        sa.Column("finding_status", sa.String(32), server_default="PENDING", nullable=False),
        sa.Column("sanction_type", sa.String(32), server_default="NONE", nullable=False),
        sa.Column("sanction_details", sa.Text(), nullable=True),
        sa.Column(
            "decision_maker_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_staff.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("decision_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_communicated", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("appeal_deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "case_id", name="uq_sa_disciplinary_case"),
    )
    op.create_index("idx_sa_disc_respondent", "sa_disciplinary_proceedings", ["tenant_id", "respondent_student_id"])
    op.create_index("idx_sa_disc_stage", "sa_disciplinary_proceedings", ["tenant_id", "procedural_stage"])

    # 7. Case Evidence
    op.create_table(
        "sa_case_evidence",
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
            sa.ForeignKey("sa_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents_records.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("evidence_type", sa.String(32), server_default="DOCUMENT", nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("file_url", sa.String(512), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "uploaded_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("confidentiality_level", sa.String(32), server_default="STANDARD", nullable=False),
        sa.Column("is_redacted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("redaction_summary", sa.Text(), nullable=True),
        sa.Column(
            "original_evidence_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sa_case_evidence.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_sa_evidence_case", "sa_case_evidence", ["tenant_id", "case_id"])
    op.create_index("idx_sa_evidence_confidentiality", "sa_case_evidence", ["tenant_id", "confidentiality_level"])

    # 8. Case Meetings
    op.create_table(
        "sa_case_meetings",
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
            sa.ForeignKey("sa_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("meeting_type", sa.String(32), server_default="HEARING_PANEL", nullable=False),
        sa.Column("scheduled_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scheduled_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("venue_or_url", sa.String(255), nullable=True),
        sa.Column("status", sa.String(32), server_default="SCHEDULED", nullable=False),
        sa.Column(
            "facilitator_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_staff.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("notes_confidential", sa.Text(), nullable=True),
        sa.Column("agreed_actions", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_sa_meeting_case", "sa_case_meetings", ["tenant_id", "case_id"])
    op.create_index("idx_sa_meeting_time", "sa_case_meetings", ["tenant_id", "scheduled_start"])

    # 9. Case Communications
    op.create_table(
        "sa_case_communications",
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
            sa.ForeignKey("sa_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "sender_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("sender_name", sa.String(128), nullable=False),
        sa.Column("is_internal_only", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("message_text", sa.Text(), nullable=False),
        sa.Column("attachment_url", sa.String(512), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_sa_comm_case", "sa_case_communications", ["tenant_id", "case_id"])
    op.create_index("idx_sa_comm_created", "sa_case_communications", ["tenant_id", "created_at"])

    # 10. Resolution Actions
    op.create_table(
        "sa_resolution_actions",
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
            sa.ForeignKey("sa_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("action_type", sa.String(32), server_default="MEDIATED_AGREEMENT", nullable=False),
        sa.Column(
            "assigned_owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(32), server_default="PENDING", nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completion_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_sa_action_case", "sa_resolution_actions", ["tenant_id", "case_id"])
    op.create_index("idx_sa_action_status", "sa_resolution_actions", ["tenant_id", "status"])

    # 11. Appeals
    op.create_table(
        "sa_appeals",
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
            sa.ForeignKey("sa_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "appellant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("appeal_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("appeal_grounds", sa.String(32), server_default="PROCEDURAL_ERROR", nullable=False),
        sa.Column("grounds_statement", sa.Text(), nullable=False),
        sa.Column(
            "assigned_reviewer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_staff.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("review_status", sa.String(32), server_default="FILED", nullable=False),
        sa.Column("outcome_summary", sa.Text(), nullable=True),
        sa.Column("outcome_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_sa_appeal_case", "sa_appeals", ["tenant_id", "case_id"])
    op.create_index("idx_sa_appeal_status", "sa_appeals", ["tenant_id", "review_status"])

    # 12. Case Escalations
    op.create_table(
        "sa_case_escalations",
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
            sa.ForeignKey("sa_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "escalated_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("escalation_level", sa.String(32), server_default="LEVEL_2_DIRECTOR", nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("actions_taken", sa.Text(), nullable=True),
        sa.Column("safety_referral_sent", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("status", sa.String(32), server_default="ACTIVE", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_sa_esc_case", "sa_case_escalations", ["tenant_id", "case_id"])
    op.create_index("idx_sa_esc_status", "sa_case_escalations", ["tenant_id", "status"])

    # 13. Case Access Audits
    op.create_table(
        "sa_access_audits",
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
            sa.ForeignKey("sa_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_sa_audit_case", "sa_access_audits", ["tenant_id", "case_id"])
    op.create_index("idx_sa_audit_user", "sa_access_audits", ["tenant_id", "user_id"])

    # 14. Student Affairs Policy Configs
    op.create_table(
        "sa_policy_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("grievance_sla_days", sa.Integer(), server_default=sa.text("15"), nullable=False),
        sa.Column("appeal_window_days", sa.Integer(), server_default=sa.text("14"), nullable=False),
        sa.Column("anonymous_reporting_allowed", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("separation_of_appeals_required", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "safeguarding_emergency_contact",
            sa.String(128),
            server_default="Campus Security & Safeguarding Unit (+91 44 2257 8888)",
            nullable=False,
        ),
        sa.Column("policy_handbook_version", sa.String(32), server_default="2026.1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", name="uq_sa_policy_config_tenant"),
    )


def downgrade() -> None:
    op.drop_table("sa_policy_configs")
    op.drop_table("sa_access_audits")
    op.drop_table("sa_case_escalations")
    op.drop_table("sa_appeals")
    op.drop_table("sa_resolution_actions")
    op.drop_table("sa_case_communications")
    op.drop_table("sa_case_meetings")
    op.drop_table("sa_case_evidence")
    op.drop_table("sa_disciplinary_proceedings")
    op.drop_table("sa_assignment_history")
    op.drop_table("sa_case_participants")
    op.drop_table("sa_cases")
    op.drop_table("sa_categories")
    op.drop_table("sa_offices")
