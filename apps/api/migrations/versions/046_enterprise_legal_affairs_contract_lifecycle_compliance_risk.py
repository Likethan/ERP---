"""Enterprise Legal Affairs, Contract Lifecycle, Policy Compliance & Institutional Risk Management (Step 62).

Revision ID: 046_enterprise_legal_affairs_contract_lifecycle_compliance_risk
Revises: 045_enterprise_research_collaboration_portfolio_grants
Create Date: 2026-10-27 12:00:00.000000

Creates domain tables and indexes for:
- institutional_contracts
- contract_amendments
- contract_obligations
- institutional_legal_matters
- institutional_compliance_obligations
- institutional_risks
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "046_enterprise_legal_affairs_contract_lifecycle_compliance_risk"
down_revision = "045_enterprise_research_collaboration_portfolio_grants"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Institutional Contracts
    op.create_table(
        "institutional_contracts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("contract_number", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("category", sa.String(64), nullable=False, server_default="OTHER"),
        sa.Column("purpose", sa.Text(), nullable=True),
        sa.Column("internal_owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_departments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("campus_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_campuses.id", ondelete="SET NULL"), nullable=True),
        sa.Column("counterparty_name", sa.String(255), nullable=False),
        sa.Column("counterparty_contact_json", postgresql.JSONB(), server_default="{}", nullable=True),
        sa.Column("related_entity_type", sa.String(64), nullable=True),
        sa.Column("related_entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT"),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("expiration_date", sa.Date(), nullable=True),
        sa.Column("auto_renew", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("renewal_notice_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("termination_notice_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("financial_value", sa.Numeric(14, 2), nullable=True),
        sa.Column("currency", sa.String(8), nullable=False, server_default="USD"),
        sa.Column("confidentiality_level", sa.String(32), nullable=False, server_default="INTERNAL"),
        sa.Column("draft_document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("executed_document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("execution_method", sa.String(64), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("executed_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("governing_law", sa.String(128), nullable=True),
        sa.Column("approval_chain_json", postgresql.JSONB(), server_default="[]", nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(), server_default="{}", nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "contract_number", name="uq_contract_tenant_number"),
    )
    op.create_index("ix_institutional_contracts_tenant_id", "institutional_contracts", ["tenant_id"])
    op.create_index("ix_institutional_contracts_contract_number", "institutional_contracts", ["contract_number"])
    op.create_index("ix_contract_tenant_status", "institutional_contracts", ["tenant_id", "status"])
    op.create_index("ix_contract_tenant_expiration", "institutional_contracts", ["tenant_id", "expiration_date"])

    # 2. Contract Amendments
    op.create_table(
        "contract_amendments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("contract_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("institutional_contracts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amendment_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("extended_expiration_date", sa.Date(), nullable=True),
        sa.Column("financial_value_adjustment", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "contract_id", "amendment_number", name="uq_amendment_contract_num"),
    )
    op.create_index("ix_contract_amendments_tenant_id", "contract_amendments", ["tenant_id"])
    op.create_index("ix_contract_amendments_contract_id", "contract_amendments", ["contract_id"])

    # 3. Contract Obligations
    op.create_table(
        "contract_obligations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("contract_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("institutional_contracts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("obligation_code", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("obligation_type", sa.String(64), nullable=False, server_default="DELIVERABLE"),
        sa.Column("responsible_owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("accountable_department_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_departments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("review_date", sa.Date(), nullable=True),
        sa.Column("reminder_lead_days", sa.Integer(), nullable=False, server_default="14"),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("evidence_document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("completion_notes", sa.Text(), nullable=True),
        sa.Column("completed_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("waived_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("waived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("waived_reason", sa.Text(), nullable=True),
        sa.Column("escalation_level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("ix_contract_obligations_tenant_id", "contract_obligations", ["tenant_id"])
    op.create_index("ix_contract_obligations_contract_id", "contract_obligations", ["contract_id"])
    op.create_index("ix_obligation_tenant_due", "contract_obligations", ["tenant_id", "due_date", "status"])

    # 4. Institutional Legal Matters
    op.create_table(
        "institutional_legal_matters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("matter_number", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("category", sa.String(64), nullable=False, server_default="OTHER"),
        sa.Column("restricted_classification", sa.String(64), nullable=False, server_default="ATTORNEY_CLIENT_PRIVILEGED"),
        sa.Column("internal_owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("lead_counsel_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("external_counsel_ref", sa.String(255), nullable=True),
        sa.Column("counterparty_name", sa.String(255), nullable=True),
        sa.Column("opposing_counsel_name", sa.String(255), nullable=True),
        sa.Column("related_contract_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("institutional_contracts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("related_department_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_departments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("campus_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_campuses.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="OPEN"),
        sa.Column("priority", sa.String(32), nullable=False, server_default="MEDIUM"),
        sa.Column("financial_exposure_estimate", sa.Numeric(14, 2), nullable=True),
        sa.Column("opened_date", sa.Date(), nullable=False),
        sa.Column("target_resolution_date", sa.Date(), nullable=True),
        sa.Column("closed_date", sa.Date(), nullable=True),
        sa.Column("key_deadlines_json", postgresql.JSONB(), server_default="[]", nullable=True),
        sa.Column("associated_documents_json", postgresql.JSONB(), server_default="[]", nullable=True),
        sa.Column("confidential_notes", sa.Text(), nullable=True),
        sa.Column("resolution_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "matter_number", name="uq_matter_tenant_number"),
    )
    op.create_index("ix_institutional_legal_matters_tenant_id", "institutional_legal_matters", ["tenant_id"])
    op.create_index("ix_matter_tenant_status", "institutional_legal_matters", ["tenant_id", "status"])

    # 5. Institutional Compliance Obligations
    op.create_table(
        "institutional_compliance_obligations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("obligation_code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("authoritative_source_reference", sa.String(255), nullable=False),
        sa.Column("category", sa.String(64), nullable=False, server_default="STATUTORY_REGULATORY"),
        sa.Column("responsible_owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_departments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("campus_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_campuses.id", ondelete="SET NULL"), nullable=True),
        sa.Column("review_frequency_months", sa.Integer(), nullable=False, server_default="12"),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("next_review_date", sa.Date(), nullable=True),
        sa.Column("required_controls", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="NOT_ASSESSED"),
        sa.Column("assessment_findings", sa.Text(), nullable=True),
        sa.Column("assessed_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("related_policy_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("related_contract_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("institutional_contracts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("evidence_records_json", postgresql.JSONB(), server_default="[]", nullable=True),
        sa.Column("corrective_actions_json", postgresql.JSONB(), server_default="[]", nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "obligation_code", name="uq_comp_tenant_code"),
    )
    op.create_index("ix_institutional_compliance_obligations_tenant_id", "institutional_compliance_obligations", ["tenant_id"])
    op.create_index("ix_comp_tenant_status", "institutional_compliance_obligations", ["tenant_id", "status"])

    # 6. Institutional Risks (5x5 Matrix)
    op.create_table(
        "institutional_risks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("risk_code", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(64), nullable=False, server_default="GOVERNANCE_LEGAL"),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_departments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("campus_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_campuses.id", ondelete="SET NULL"), nullable=True),
        sa.Column("responsible_owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("inherent_likelihood", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("inherent_impact", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("inherent_score", sa.Integer(), nullable=False, server_default="9"),
        sa.Column("existing_controls", sa.Text(), nullable=True),
        sa.Column("residual_likelihood", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("residual_impact", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("residual_score", sa.Integer(), nullable=False, server_default="4"),
        sa.Column("risk_level", sa.String(32), nullable=False, server_default="LOW"),
        sa.Column("mitigation_plan", sa.Text(), nullable=True),
        sa.Column("target_completion_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="IDENTIFIED"),
        sa.Column("accepted_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("acceptance_rationale", sa.Text(), nullable=True),
        sa.Column("related_contract_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("institutional_contracts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("related_policy_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("related_compliance_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("institutional_compliance_obligations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "risk_code", name="uq_risk_tenant_code"),
    )
    op.create_index("ix_institutional_risks_tenant_id", "institutional_risks", ["tenant_id"])
    op.create_index("ix_risk_tenant_level", "institutional_risks", ["tenant_id", "risk_level"])
    op.create_index("ix_risk_tenant_status", "institutional_risks", ["tenant_id", "status"])


def downgrade() -> None:
    op.drop_table("institutional_risks")
    op.drop_table("institutional_compliance_obligations")
    op.drop_table("institutional_legal_matters")
    op.drop_table("contract_obligations")
    op.drop_table("contract_amendments")
    op.drop_table("institutional_contracts")
