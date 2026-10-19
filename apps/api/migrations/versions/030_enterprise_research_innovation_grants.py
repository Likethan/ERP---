"""Enterprise Institutional Research, Innovation, Grants & Intellectual Property (Step 44).

Revision ID: 030_enterprise_research_innovation_grants
Revises: 029_enterprise_accreditation_quality_assurance
Create Date: 2026-10-18 23:40:00.000000

Creates normalized tables for:
- research_projects: Central project registry across faculty, student, collaborative, and industry research
- research_project_status_history: Audited lifecycle transitions with preconditions and decisions
- research_team_members: Internal investigators and authorized external collaborators with access scopes
- research_funding_opportunities: Grants, RFPs, industry calls, and funding directory
- research_grant_applications: Internal proposal review, departmental approvals, and external submission tracking
- research_grant_awards: Sanctioned funding records integrated with finance tracking
- research_budget_plans: Itemized budget planning, versions, and revision workflows
- research_milestones: Deliverables, dependencies, and independent acceptance verification
- research_ethics_approvals: Multi-committee compliance approvals (human, animal, biosafety, privacy)
- research_outputs: Scholarly publications, datasets, software tools, and DOI duplicate protection
- research_invention_disclosures: Intellectual property, patent lifecycle, and commercial licensing
- research_facility_references: Laboratory and instrumentation resource usage references
- research_project_risks: Project risk registers, severity ratings, and mitigation plans
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "030_enterprise_research_innovation_grants"
down_revision = "029_enterprise_accreditation_quality_assurance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Research Projects
    op.create_table(
        "research_projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("project_code", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("abstract", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("research_objectives", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("category", sa.String(64), nullable=False, server_default="FACULTY_LED"),
        sa.Column("research_domain", sa.String(128), nullable=False),
        sa.Column(
            "principal_investigator_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "lead_department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "lead_campus_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_campuses.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("planned_completion_date", sa.Date(), nullable=False),
        sa.Column("actual_completion_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT"),
        sa.Column("total_budget_allocated", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("currency", sa.String(8), nullable=False, server_default="INR"),
        sa.Column("requires_ethics_approval", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("ethics_approval_status", sa.String(32), nullable=False, server_default="NOT_REQUIRED"),
        sa.Column("risks_summary", sa.Text(), nullable=True),
        sa.Column("lock_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "project_code", name="uq_research_projects_tenant_code"),
    )
    op.create_index("idx_research_projects_tenant_status", "research_projects", ["tenant_id", "status"])
    op.create_index("idx_research_projects_tenant_pi", "research_projects", ["tenant_id", "principal_investigator_id"])
    op.create_index("idx_research_projects_tenant_dept", "research_projects", ["tenant_id", "lead_department_id"])
    op.create_index("idx_research_projects_tenant_category", "research_projects", ["tenant_id", "category"])

    # 2. Research Project Status History
    op.create_table(
        "research_project_status_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("research_projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("from_status", sa.String(32), nullable=False),
        sa.Column("to_status", sa.String(32), nullable=False),
        sa.Column(
            "changed_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("reason", sa.String(255), nullable=False),
        sa.Column("decision_notes", sa.Text(), nullable=True),
        sa.Column("transition_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_research_history_tenant_project", "research_project_status_history", ["tenant_id", "project_id"])

    # 3. Research Team Members
    op.create_table(
        "research_team_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("research_projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("external_collaborator_name", sa.String(128), nullable=True),
        sa.Column("external_institution", sa.String(255), nullable=True),
        sa.Column("role", sa.String(64), nullable=False, server_default="CO_INVESTIGATOR"),
        sa.Column("contribution_description", sa.Text(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("access_scope", sa.String(32), nullable=False, server_default="FULL_READ_WRITE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_research_team_tenant_project", "research_team_members", ["tenant_id", "project_id"])
    op.create_index("idx_research_team_tenant_user", "research_team_members", ["tenant_id", "user_id"])

    # 4. Research Funding Opportunities
    op.create_table(
        "research_funding_opportunities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("funding_agency_name", sa.String(128), nullable=False),
        sa.Column("category", sa.String(64), nullable=False, server_default="GOVERNMENT_GRANT"),
        sa.Column("research_domains", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("eligibility_criteria", sa.Text(), nullable=False),
        sa.Column("opening_date", sa.Date(), nullable=False),
        sa.Column("closing_date", sa.Date(), nullable=False),
        sa.Column("min_funding_amount", sa.Numeric(14, 2), nullable=True),
        sa.Column("max_funding_amount", sa.Numeric(14, 2), nullable=True),
        sa.Column("currency", sa.String(8), nullable=False, server_default="INR"),
        sa.Column("application_procedure_url", sa.String(512), nullable=True),
        sa.Column(
            "internal_opportunity_owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("visibility_scope", sa.String(32), nullable=False, server_default="INSTITUTION_WIDE"),
        sa.Column(
            "campus_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_campuses.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(32), nullable=False, server_default="OPEN"),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "code", name="uq_research_opps_tenant_code"),
    )
    op.create_index("idx_research_opps_tenant_status", "research_funding_opportunities", ["tenant_id", "status"])
    op.create_index("idx_research_opps_tenant_closing", "research_funding_opportunities", ["tenant_id", "closing_date"])

    # 5. Research Grant Applications
    op.create_table(
        "research_grant_applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("application_code", sa.String(64), nullable=False),
        sa.Column(
            "funding_opportunity_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("research_funding_opportunities.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("research_projects.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column(
            "principal_investigator_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("research_proposal_summary", sa.Text(), nullable=False),
        sa.Column("objectives_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("methodology_summary", sa.Text(), nullable=True),
        sa.Column("work_packages_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("proposed_budget", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False, server_default="INR"),
        sa.Column("internal_review_status", sa.String(32), nullable=False, server_default="DRAFT"),
        sa.Column("external_submission_status", sa.String(32), nullable=False, server_default="NOT_SUBMITTED"),
        sa.Column("external_reference_number", sa.String(128), nullable=True),
        sa.Column("external_submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "submitted_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "internal_approved_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("internal_approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("submission_readiness_checklist_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "application_code", name="uq_research_grants_tenant_code"),
    )
    op.create_index("idx_research_grants_tenant_status", "research_grant_applications", ["tenant_id", "internal_review_status"])
    op.create_index("idx_research_grants_tenant_pi", "research_grant_applications", ["tenant_id", "principal_investigator_id"])

    # 6. Research Grant Awards
    op.create_table(
        "research_grant_awards",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("award_number", sa.String(64), nullable=False),
        sa.Column(
            "grant_application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("research_grant_applications.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("research_projects.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("funding_organization", sa.String(128), nullable=False),
        sa.Column("award_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False, server_default="INR"),
        sa.Column("award_date", sa.Date(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("approved_budget_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("disbursement_schedule_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("spending_conditions", sa.Text(), nullable=True),
        sa.Column("reporting_deadlines_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column(
            "financial_owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("received_amount", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("allocated_amount", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("committed_expenditure", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("actual_expenditure", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("remaining_budget", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "award_number", name="uq_research_awards_tenant_num"),
    )
    op.create_index("idx_research_awards_tenant_proj", "research_grant_awards", ["tenant_id", "project_id"])
    op.create_index("idx_research_awards_tenant_status", "research_grant_awards", ["tenant_id", "status"])

    # 7. Research Budget Plans
    op.create_table(
        "research_budget_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("research_projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "award_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("research_grant_awards.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(32), nullable=False, server_default="PROPOSED"),
        sa.Column("personnel_costs", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("equipment_costs", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("consumables_materials_costs", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("travel_fieldwork_costs", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("computing_software_costs", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("publication_dissemination_costs", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("external_services_costs", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("institutional_overheads", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("contingency_costs", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("total_budget", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False, server_default="INR"),
        sa.Column(
            "approved_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approval_notes", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_research_budget_tenant_proj", "research_budget_plans", ["tenant_id", "project_id"])

    # 8. Research Milestones
    op.create_table(
        "research_milestones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("research_projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("milestone_code", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("planned_start_date", sa.Date(), nullable=False),
        sa.Column("planned_completion_date", sa.Date(), nullable=False),
        sa.Column("actual_completion_date", sa.Date(), nullable=True),
        sa.Column(
            "responsible_owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("dependencies_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("acceptance_criteria", sa.Text(), nullable=False),
        sa.Column("completion_percentage", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("status", sa.String(32), nullable=False, server_default="PLANNED"),
        sa.Column("is_mandatory_for_closure", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("deliverable_reference", sa.String(255), nullable=True),
        sa.Column(
            "evidence_document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents_records.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "verified_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verification_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "project_id", "milestone_code", name="uq_milestones_proj_code"),
    )
    op.create_index("idx_milestones_tenant_project", "research_milestones", ["tenant_id", "project_id"])
    op.create_index("idx_milestones_tenant_status", "research_milestones", ["tenant_id", "status"])

    # 9. Research Ethics Approvals
    op.create_table(
        "research_ethics_approvals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("approval_code", sa.String(64), nullable=False),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("research_projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("approval_type", sa.String(64), nullable=False, server_default="HUMAN_PARTICIPANTS"),
        sa.Column("governing_policy_reference", sa.String(128), nullable=False),
        sa.Column("review_committee_name", sa.String(128), nullable=False),
        sa.Column(
            "reviewer_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("submission_date", sa.Date(), nullable=False),
        sa.Column("decision_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("conditions_and_restrictions", sa.Text(), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column(
            "evidence_document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents_records.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("decision_rationale", sa.Text(), nullable=True),
        sa.Column("is_confidential", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "approval_code", name="uq_ethics_tenant_code"),
    )
    op.create_index("idx_ethics_tenant_project", "research_ethics_approvals", ["tenant_id", "project_id"])
    op.create_index("idx_ethics_tenant_status", "research_ethics_approvals", ["tenant_id", "status"])
    op.create_index("idx_ethics_tenant_expiry", "research_ethics_approvals", ["tenant_id", "expiry_date"])

    # 10. Research Outputs
    op.create_table(
        "research_outputs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("research_projects.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("output_type", sa.String(64), nullable=False, server_default="JOURNAL_ARTICLE"),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("abstract", sa.Text(), nullable=False),
        sa.Column("authors_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column(
            "lead_author_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("publication_date", sa.Date(), nullable=False),
        sa.Column("publisher_or_venue", sa.String(255), nullable=False),
        sa.Column("doi_or_urn", sa.String(128), nullable=True),
        sa.Column("issn_isbn", sa.String(64), nullable=True),
        sa.Column("citation_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("research_domain", sa.String(128), nullable=False),
        sa.Column("peer_review_status", sa.String(32), nullable=False, server_default="PEER_REVIEWED"),
        sa.Column("open_access_type", sa.String(32), nullable=False, server_default="GOLD_OA"),
        sa.Column("funding_acknowledgement", sa.String(255), nullable=True),
        sa.Column(
            "evidence_document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents_records.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("verification_status", sa.String(32), nullable=False, server_default="UNVERIFIED"),
        sa.Column(
            "verified_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verification_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "doi_or_urn", name="uq_research_outputs_doi"),
    )
    op.create_index("idx_research_outputs_tenant_proj", "research_outputs", ["tenant_id", "project_id"])
    op.create_index("idx_research_outputs_tenant_type", "research_outputs", ["tenant_id", "output_type"])

    # 11. Research Invention Disclosures
    op.create_table(
        "research_invention_disclosures",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("disclosure_code", sa.String(64), nullable=False),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("research_projects.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "award_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("research_grant_awards.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("invention_title", sa.String(255), nullable=False),
        sa.Column("technical_abstract", sa.Text(), nullable=False),
        sa.Column("detailed_description", sa.Text(), nullable=True),
        sa.Column("inventors_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("submission_date", sa.Date(), nullable=False),
        sa.Column("confidentiality_level", sa.String(32), nullable=False, server_default="INTERNAL_CONFIDENTIAL"),
        sa.Column("institutional_ownership_pct", sa.Numeric(5, 2), nullable=False, server_default="100.00"),
        sa.Column("evaluation_status", sa.String(32), nullable=False, server_default="SUBMITTED"),
        sa.Column(
            "evaluated_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("evaluation_date", sa.Date(), nullable=True),
        sa.Column("evaluation_notes", sa.Text(), nullable=True),
        sa.Column("patent_application_number", sa.String(128), nullable=True),
        sa.Column("patent_jurisdiction", sa.String(64), nullable=True),
        sa.Column("patent_filing_date", sa.Date(), nullable=True),
        sa.Column("patent_status", sa.String(32), nullable=False, server_default="NOT_FILED"),
        sa.Column("patent_grant_date", sa.Date(), nullable=True),
        sa.Column("patent_number", sa.String(128), nullable=True),
        sa.Column("commercialization_status", sa.String(32), nullable=False, server_default="NOT_MARKETED"),
        sa.Column("licensee_organization", sa.String(255), nullable=True),
        sa.Column("license_revenue_total", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column(
            "evidence_document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents_records.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "disclosure_code", name="uq_disclosures_tenant_code"),
    )
    op.create_index("idx_disclosures_tenant_proj", "research_invention_disclosures", ["tenant_id", "project_id"])
    op.create_index("idx_disclosures_tenant_patent", "research_invention_disclosures", ["tenant_id", "patent_status"])

    # 12. Research Facility References
    op.create_table(
        "research_facility_references",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("research_projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("facility_name", sa.String(128), nullable=False),
        sa.Column("facility_type", sa.String(64), nullable=False),
        sa.Column(
            "campus_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_campuses.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("equipment_identifier", sa.String(64), nullable=True),
        sa.Column("equipment_name", sa.String(128), nullable=True),
        sa.Column("booking_reference_id", sa.String(64), nullable=True),
        sa.Column("usage_hours_allocated", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("usage_hours_consumed", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_facility_refs_tenant_proj", "research_facility_references", ["tenant_id", "project_id"])

    # 13. Research Project Risks
    op.create_table(
        "research_project_risks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("research_projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("risk_code", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("likelihood", sa.String(16), nullable=False, server_default="MEDIUM"),
        sa.Column("impact", sa.String(16), nullable=False, server_default="MEDIUM"),
        sa.Column("calculated_risk_level", sa.String(16), nullable=False, server_default="MEDIUM"),
        sa.Column(
            "responsible_owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("mitigation_plan", sa.Text(), nullable=False),
        sa.Column("target_resolution_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="IDENTIFIED"),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "project_id", "risk_code", name="uq_research_risks_code"),
    )
    op.create_index("idx_research_risks_tenant_proj", "research_project_risks", ["tenant_id", "project_id"])
    op.create_index("idx_research_risks_tenant_severity", "research_project_risks", ["tenant_id", "calculated_risk_level"])


def downgrade() -> None:
    op.drop_table("research_project_risks")
    op.drop_table("research_facility_references")
    op.drop_table("research_invention_disclosures")
    op.drop_table("research_outputs")
    op.drop_table("research_ethics_approvals")
    op.drop_table("research_milestones")
    op.drop_table("research_budget_plans")
    op.drop_table("research_grant_awards")
    op.drop_table("research_grant_applications")
    op.drop_table("research_funding_opportunities")
    op.drop_table("research_team_members")
    op.drop_table("research_project_status_history")
    op.drop_table("research_projects")
