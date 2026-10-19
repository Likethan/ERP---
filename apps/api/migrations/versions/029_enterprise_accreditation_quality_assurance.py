"""Enterprise Institutional Accreditation, Quality Assurance & Continuous Improvement (Step 43).

Revision ID: 029_enterprise_accreditation_quality_assurance
Revises: 028_enterprise_knowledge_base_policy_library
Create Date: 2026-10-18 23:05:00.000000

Creates normalized tables for:
- accreditation_frameworks: Configurable frameworks (NAAC, NBA, NIRF, ISO, internal benchmarks)
- accreditation_framework_versions: Immutable published framework definitions
- accreditation_criteria: Criteria and subcriteria hierarchies with weighting and scoring rules
- accreditation_assessment_cycles: Assessment cycles and evaluation periods
- accreditation_criterion_assessments: Criterion evaluations, scores, findings, and reviews
- accreditation_evidences: Traceable institutional evidence linking documents, knowledge, and records
- accreditation_criterion_evidence_maps: Many-to-many evidence reuse mapping across criteria
- quality_indicators: Configurable quality KPIs and monitoring metrics
- quality_indicator_observations: Time-series observations and data quality validations
- quality_audit_programs: Internal quality audit programs, schedules, and finalized reports
- quality_audit_checklist_items: Audit checklist items linked to criteria
- quality_findings: Compliance findings and gap identification
- quality_corrective_actions: Corrective & Preventive Actions (CAPA) with separation of duties
- quality_improvement_plans: Continuous Quality Improvement (CQI) initiatives and milestones
- accreditation_readiness_snapshots: Transparent point-in-time readiness calculations & gap summaries
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "029_enterprise_accreditation_quality_assurance"
down_revision = "028_enterprise_knowledge_base_policy_library"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Accreditation Frameworks
    op.create_table(
        "accreditation_frameworks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("issuing_body", sa.String(128), nullable=False),
        sa.Column("framework_type", sa.String(32), nullable=False, server_default="CUSTOM"),
        sa.Column("scope_type", sa.String(32), nullable=False, server_default="INSTITUTION"),
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
        sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT"),
        sa.Column("current_version_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_by_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "owner_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("scoring_model", sa.String(32), nullable=False, server_default="NUMERIC_SCALE"),
        sa.Column("max_score", sa.Float(), nullable=True),
        sa.Column("weighting_supported", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_accred_frameworks_tenant_code"),
    )
    op.create_index("idx_accred_frameworks_tenant_status", "accreditation_frameworks", ["tenant_id", "status"])
    op.create_index("idx_accred_frameworks_tenant_type", "accreditation_frameworks", ["tenant_id", "framework_type"])

    # 2. Accreditation Framework Versions
    op.create_table(
        "accreditation_framework_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "framework_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("accreditation_frameworks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("rules_snapshot_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("criteria_snapshot_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("change_summary", sa.Text(), nullable=True),
        sa.Column(
            "published_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "framework_id", "version_number", name="uq_accred_framework_versions"),
    )
    op.create_index("idx_accred_framework_ver_fw", "accreditation_framework_versions", ["tenant_id", "framework_id"])

    # 3. Accreditation Criteria
    op.create_table(
        "accreditation_criteria",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "framework_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("accreditation_frameworks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "parent_criterion_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("accreditation_criteria.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("criterion_type", sa.String(32), nullable=False, server_default="QUALITATIVE"),
        sa.Column("weight", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("max_score", sa.Float(), nullable=False, server_default="100.0"),
        sa.Column("is_mandatory", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("assessment_guidelines", sa.Text(), nullable=True),
        sa.Column("evidence_requirements", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "framework_id", "code", name="uq_accred_criteria_code"),
    )
    op.create_index("idx_accred_criteria_framework", "accreditation_criteria", ["tenant_id", "framework_id"])
    op.create_index("idx_accred_criteria_parent", "accreditation_criteria", ["tenant_id", "parent_criterion_id"])

    # 4. Assessment Cycles
    op.create_table(
        "accreditation_assessment_cycles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "framework_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("accreditation_frameworks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("academic_year", sa.String(32), nullable=False),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("target_submission_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"),
        sa.Column("overall_score", sa.Float(), nullable=True),
        sa.Column("readiness_percentage", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column(
            "lead_coordinator_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "framework_id", "code", name="uq_accred_cycles_code"),
    )
    op.create_index("idx_accred_cycles_tenant_status", "accreditation_assessment_cycles", ["tenant_id", "status"])

    # 5. Criterion Assessments
    op.create_table(
        "accreditation_criterion_assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "cycle_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("accreditation_assessment_cycles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "criterion_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("accreditation_criteria.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "accountable_owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(32), nullable=False, server_default="UNASSESSED"),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("target_score", sa.Float(), nullable=True),
        sa.Column("maturity_level", sa.String(32), nullable=True),
        sa.Column("not_applicable_reason", sa.Text(), nullable=True),
        sa.Column("executive_summary", sa.Text(), nullable=True),
        sa.Column("findings", sa.Text(), nullable=True),
        sa.Column("strengths", sa.Text(), nullable=True),
        sa.Column("weaknesses", sa.Text(), nullable=True),
        sa.Column("recommendations", sa.Text(), nullable=True),
        sa.Column(
            "assessor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "reviewer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("lock_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "cycle_id", "criterion_id", name="uq_accred_criterion_assessment"),
    )
    op.create_index("idx_accred_crit_assess_cycle", "accreditation_criterion_assessments", ["tenant_id", "cycle_id"])
    op.create_index("idx_accred_crit_assess_status", "accreditation_criterion_assessments", ["tenant_id", "status"])

    # 6. Evidences
    op.create_table(
        "accreditation_evidences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("evidence_code", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("evidence_category", sa.String(32), nullable=False, server_default="POLICY_SOP"),
        sa.Column("source_type", sa.String(32), nullable=False, server_default="DOCUMENT"),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents_records.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "knowledge_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("knowledge_items.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "record_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("records_registry.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("external_uri", sa.String(1024), nullable=True),
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
        sa.Column(
            "owner_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_expired", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("confidentiality", sa.String(32), nullable=False, server_default="INTERNAL"),
        sa.Column("verification_status", sa.String(32), nullable=False, server_default="UNVERIFIED"),
        sa.Column(
            "verified_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewer_notes", sa.Text(), nullable=True),
        sa.Column("integrity_hash_sha256", sa.String(64), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "evidence_code", name="uq_accred_evidence_code"),
    )
    op.create_index("idx_accred_evid_status", "accreditation_evidences", ["tenant_id", "verification_status"])
    op.create_index("idx_accred_evid_category", "accreditation_evidences", ["tenant_id", "evidence_category"])

    # 7. Criterion Evidence Maps
    op.create_table(
        "accreditation_criterion_evidence_maps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "assessment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("accreditation_criterion_assessments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "evidence_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("accreditation_evidences.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("relevance_remarks", sa.Text(), nullable=True),
        sa.Column(
            "mapped_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "assessment_id", "evidence_id", name="uq_accred_crit_evid_map"),
    )
    op.create_index("idx_accred_map_assess", "accreditation_criterion_evidence_maps", ["tenant_id", "assessment_id"])
    op.create_index("idx_accred_map_evid", "accreditation_criterion_evidence_maps", ["tenant_id", "evidence_id"])

    # 8. Quality Indicators
    op.create_table(
        "quality_indicators",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(32), nullable=False, server_default="ACADEMIC_EXCELLENCE"),
        sa.Column("source_module", sa.String(32), nullable=False, server_default="ACADEMICS"),
        sa.Column("calculation_method", sa.Text(), nullable=False),
        sa.Column("reporting_frequency", sa.String(32), nullable=False, server_default="ANNUAL"),
        sa.Column("unit_of_measurement", sa.String(32), nullable=False, server_default="PERCENTAGE"),
        sa.Column("target_value", sa.Float(), nullable=False, server_default="100.0"),
        sa.Column("benchmark_threshold", sa.Float(), nullable=False, server_default="75.0"),
        sa.Column("current_value", sa.Float(), nullable=True),
        sa.Column("last_calculated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("data_quality_status", sa.String(32), nullable=False, server_default="EXCELLENT"),
        sa.Column("data_quality_notes", sa.Text(), nullable=True),
        sa.Column(
            "owner_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_quality_indicator_code"),
    )
    op.create_index("idx_qi_tenant_category", "quality_indicators", ["tenant_id", "category"])
    op.create_index("idx_qi_tenant_status", "quality_indicators", ["tenant_id", "data_quality_status"])

    # 9. Quality Indicator Observations
    op.create_table(
        "quality_indicator_observations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "indicator_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("quality_indicators.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("period_label", sa.String(64), nullable=False),
        sa.Column("observation_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("observed_value", sa.Float(), nullable=False),
        sa.Column("target_value", sa.Float(), nullable=False),
        sa.Column("data_source_mode", sa.String(32), nullable=False, server_default="AUTOMATED_QUERY"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("data_completeness_pct", sa.Float(), nullable=False, server_default="100.0"),
        sa.Column("outlier_flag", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "observed_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "indicator_id", "period_label", name="uq_qi_obs_period"),
    )
    op.create_index("idx_qi_obs_indicator", "quality_indicator_observations", ["tenant_id", "indicator_id"])

    # 10. Quality Audit Programs
    op.create_table(
        "quality_audit_programs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("audit_type", sa.String(32), nullable=False, server_default="ACADEMIC_AUDIT"),
        sa.Column("scope", sa.String(32), nullable=False, server_default="INSTITUTION_WIDE"),
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
        sa.Column(
            "lead_auditor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("co_auditors_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("scheduled_start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scheduled_end_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actual_completion_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="PLANNED"),
        sa.Column("conflict_of_interest_declared", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("summary_findings", sa.Text(), nullable=True),
        sa.Column("recommendations", sa.Text(), nullable=True),
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "finalized_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("is_immutable", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_quality_audit_code"),
    )
    op.create_index("idx_quality_audit_status", "quality_audit_programs", ["tenant_id", "status"])
    op.create_index("idx_quality_audit_type", "quality_audit_programs", ["tenant_id", "audit_type"])

    # 11. Quality Audit Checklist Items
    op.create_table(
        "quality_audit_checklist_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "audit_program_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("quality_audit_programs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "criterion_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("accreditation_criteria.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("item_code", sa.String(64), nullable=False),
        sa.Column("requirement_description", sa.Text(), nullable=False),
        sa.Column("compliance_status", sa.String(32), nullable=False, server_default="COMPLIANT"),
        sa.Column("auditor_notes", sa.Text(), nullable=True),
        sa.Column("evidence_reference", sa.String(255), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("idx_audit_chk_program", "quality_audit_checklist_items", ["tenant_id", "audit_program_id"])

    # 12. Quality Findings
    op.create_table(
        "quality_findings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("finding_code", sa.String(64), nullable=False),
        sa.Column("source_type", sa.String(32), nullable=False, server_default="INTERNAL_AUDIT"),
        sa.Column(
            "audit_program_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("quality_audit_programs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "criterion_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("accreditation_criteria.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("root_cause_analysis", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(32), nullable=False, server_default="MEDIUM"),
        sa.Column("status", sa.String(32), nullable=False, server_default="OPEN"),
        sa.Column(
            "identified_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "assigned_owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("target_resolution_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "finding_code", name="uq_quality_finding_code"),
    )
    op.create_index("idx_q_finding_severity", "quality_findings", ["tenant_id", "severity"])
    op.create_index("idx_q_finding_status", "quality_findings", ["tenant_id", "status"])

    # 13. Quality Corrective Actions (CAPA)
    op.create_table(
        "quality_corrective_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "finding_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("quality_findings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("action_code", sa.String(64), nullable=False),
        sa.Column("action_type", sa.String(32), nullable=False, server_default="CORRECTIVE"),
        sa.Column("proposed_action", sa.Text(), nullable=False),
        sa.Column("preventive_measures", sa.Text(), nullable=True),
        sa.Column(
            "responsible_owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(32), nullable=False, server_default="PROPOSED"),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evidence_notes", sa.Text(), nullable=True),
        sa.Column(
            "evidence_document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents_records.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("verification_criteria", sa.Text(), nullable=False),
        sa.Column(
            "verified_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closure_decision", sa.String(64), nullable=True),
        sa.Column("closure_notes", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "action_code", name="uq_quality_capa_code"),
    )
    op.create_index("idx_q_capa_status", "quality_corrective_actions", ["tenant_id", "status"])

    # 14. Quality Improvement Plans (CQI)
    op.create_table(
        "quality_improvement_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("baseline_measurement", sa.Text(), nullable=False),
        sa.Column("target_outcome", sa.Text(), nullable=False),
        sa.Column(
            "linked_indicator_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("quality_indicators.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "responsible_owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("target_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actual_completion_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT"),
        sa.Column("evaluation_notes", sa.Text(), nullable=True),
        sa.Column("lessons_learned", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_quality_improvement_code"),
    )
    op.create_index("idx_q_plan_status", "quality_improvement_plans", ["tenant_id", "status"])

    # 15. Accreditation Readiness Snapshots
    op.create_table(
        "accreditation_readiness_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "cycle_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("accreditation_assessment_cycles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "framework_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("accreditation_frameworks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("overall_readiness_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("criteria_assessed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("criteria_total_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("evidence_verified_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("evidence_required_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("open_high_risk_findings_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("score_projected", sa.Float(), nullable=True),
        sa.Column("score_maximum", sa.Float(), nullable=True),
        sa.Column("readiness_category", sa.String(32), nullable=False, server_default="SIGNIFICANT_GAPS"),
        sa.Column("gap_summary_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("department_readiness_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column(
            "calculated_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("idx_accred_readiness_cycle", "accreditation_readiness_snapshots", ["tenant_id", "cycle_id"])
    op.create_index("idx_accred_readiness_created", "accreditation_readiness_snapshots", ["tenant_id", "created_at"])


def downgrade() -> None:
    op.drop_table("accreditation_readiness_snapshots")
    op.drop_table("quality_improvement_plans")
    op.drop_table("quality_corrective_actions")
    op.drop_table("quality_findings")
    op.drop_table("quality_audit_checklist_items")
    op.drop_table("quality_audit_programs")
    op.drop_table("quality_indicator_observations")
    op.drop_table("quality_indicators")
    op.drop_table("accreditation_criterion_evidence_maps")
    op.drop_table("accreditation_evidences")
    op.drop_table("accreditation_criterion_assessments")
    op.drop_table("accreditation_assessment_cycles")
    op.drop_table("accreditation_criteria")
    op.drop_table("accreditation_framework_versions")
    op.drop_table("accreditation_frameworks")
