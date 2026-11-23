"""Enterprise Institutional Legal Affairs, Contract Lifecycle, Policy Compliance & Institutional Risk Models (Step 62).

Implements centralized institutional contract management, review and approval workflows,
contractual obligations & commitments register, restricted legal case and matter tracking,
statutory/accreditation compliance evaluations, and 5x5 enterprise institutional risk registers.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantScopedModel

# =============================================================================
# ENUMS
# =============================================================================


class ContractCategory(StrEnum):
    VENDOR_PROCUREMENT = "VENDOR_PROCUREMENT"
    EMPLOYMENT_CONSULTING = "EMPLOYMENT_CONSULTING"
    SERVICE_LEVEL = "SERVICE_LEVEL"
    STUDENT_SERVICE = "STUDENT_SERVICE"
    RESEARCH_SPONSORED = "RESEARCH_SPONSORED"
    INDUSTRY_COLLABORATION = "INDUSTRY_COLLABORATION"
    DATA_PROCESSING_NDA = "DATA_PROCESSING_NDA"
    FACILITY_PARTNERSHIP = "FACILITY_PARTNERSHIP"
    INTERNATIONAL_INSTITUTIONAL = "INTERNATIONAL_INSTITUTIONAL"
    OTHER = "OTHER"


class ContractStatus(StrEnum):
    DRAFT = "DRAFT"
    INTERNAL_REVIEW = "INTERNAL_REVIEW"
    DEPARTMENT_APPROVAL = "DEPARTMENT_APPROVAL"
    LEGAL_REVIEW = "LEGAL_REVIEW"
    AUTHORIZED_APPROVAL = "AUTHORIZED_APPROVAL"
    READY_FOR_EXECUTION = "READY_FOR_EXECUTION"
    EXECUTED = "EXECUTED"
    ACTIVE = "ACTIVE"
    EXPIRING = "EXPIRING"
    RENEWED = "RENEWED"
    TERMINATED = "TERMINATED"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"
    ON_HOLD = "ON_HOLD"
    ARCHIVED = "ARCHIVED"


class ConfidentialityLevel(StrEnum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED_LEGAL = "RESTRICTED_LEGAL"


class ObligationType(StrEnum):
    DELIVERABLE = "DELIVERABLE"
    REPORTING = "REPORTING"
    PAYMENT_MILESTONE = "PAYMENT_MILESTONE"
    SERVICE_COMMITMENT = "SERVICE_COMMITMENT"
    RENEWAL_NOTICE = "RENEWAL_NOTICE"
    INSURANCE_CERTIFICATE = "INSURANCE_CERTIFICATE"
    COMPLIANCE_AUDIT = "COMPLIANCE_AUDIT"
    OTHER = "OTHER"


class ObligationStatus(StrEnum):
    PENDING = "PENDING"
    APPROACHING = "APPROACHING"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"
    WAIVED = "WAIVED"
    DISPUTED = "DISPUTED"


class MatterCategory(StrEnum):
    CONTRACT_DISPUTE = "CONTRACT_DISPUTE"
    VENDOR_DISPUTE = "VENDOR_DISPUTE"
    EMPLOYMENT_DISPUTE = "EMPLOYMENT_DISPUTE"
    INSTITUTIONAL_CLAIM = "INSTITUTIONAL_CLAIM"
    REGULATORY_INQUIRY = "REGULATORY_INQUIRY"
    EXTERNAL_COUNSEL_ENGAGEMENT = "EXTERNAL_COUNSEL_ENGAGEMENT"
    LITIGATION_PROCEEDING = "LITIGATION_PROCEEDING"
    LEGAL_OPINION = "LEGAL_OPINION"
    PRE_LITIGATION_CORRESPONDENCE = "PRE_LITIGATION_CORRESPONDENCE"
    OTHER = "OTHER"


class MatterRestrictedClassification(StrEnum):
    STRICTLY_CONFIDENTIAL = "STRICTLY_CONFIDENTIAL"
    ATTORNEY_CLIENT_PRIVILEGED = "ATTORNEY_CLIENT_PRIVILEGED"
    RESTRICTED_EXECUTIVE = "RESTRICTED_EXECUTIVE"
    LEGAL_INTERNAL = "LEGAL_INTERNAL"


class MatterStatus(StrEnum):
    OPEN = "OPEN"
    UNDER_REVIEW = "UNDER_REVIEW"
    ACTIVE_PROCEEDING = "ACTIVE_PROCEEDING"
    SETTLEMENT_PENDING = "SETTLEMENT_PENDING"
    CLOSED_RESOLVED = "CLOSED_RESOLVED"
    CLOSED_DISMISSED = "CLOSED_DISMISSED"
    ON_HOLD = "ON_HOLD"


class MatterPriority(StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ComplianceCategory(StrEnum):
    STATUTORY_REGULATORY = "STATUTORY_REGULATORY"
    ACCREDITATION_STANDARD = "ACCREDITATION_STANDARD"
    DATA_PRIVACY_SECURITY = "DATA_PRIVACY_SECURITY"
    LABOR_EMPLOYMENT = "LABOR_EMPLOYMENT"
    FINANCIAL_TAX = "FINANCIAL_TAX"
    HEALTH_SAFETY_ENVIRONMENT = "HEALTH_SAFETY_ENVIRONMENT"
    RESEARCH_ETHICS = "RESEARCH_ETHICS"
    INSTITUTIONAL_BYLAW = "INSTITUTIONAL_BYLAW"


class ComplianceAssessmentStatus(StrEnum):
    NOT_ASSESSED = "NOT_ASSESSED"
    IN_PROGRESS = "IN_PROGRESS"
    EVIDENCE_REQUIRED = "EVIDENCE_REQUIRED"
    UNDER_REVIEW = "UNDER_REVIEW"
    COMPLIANT = "COMPLIANT"
    PARTIALLY_COMPLIANT = "PARTIALLY_COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    REMEDIATION_IN_PROGRESS = "REMEDIATION_IN_PROGRESS"
    CLOSED = "CLOSED"


class RiskCategory(StrEnum):
    GOVERNANCE_LEGAL = "GOVERNANCE_LEGAL"
    FINANCIAL = "FINANCIAL"
    OPERATIONAL = "OPERATIONAL"
    REPUTATIONAL = "REPUTATIONAL"
    ACADEMIC_ACCREDITATION = "ACADEMIC_ACCREDITATION"
    INFORMATION_SECURITY_PRIVACY = "INFORMATION_SECURITY_PRIVACY"
    HEALTH_SAFETY_ENVIRONMENTAL = "HEALTH_SAFETY_ENVIRONMENTAL"
    STRATEGIC_PARTNERSHIP = "STRATEGIC_PARTNERSHIP"


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskStatus(StrEnum):
    IDENTIFIED = "IDENTIFIED"
    ASSESSED = "ASSESSED"
    MITIGATION_IN_PROGRESS = "MITIGATION_IN_PROGRESS"
    RESIDUAL_RISK_ACCEPTED = "RESIDUAL_RISK_ACCEPTED"
    RETIRED_RESOLVED = "RETIRED_RESOLVED"


# =============================================================================
# MODELS
# =============================================================================


class InstitutionalContract(TenantScopedModel):
    """Core Institutional Contract Lifecycle Entity."""

    __tablename__ = "institutional_contracts"

    contract_number: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(
        String(64), default=ContractCategory.OTHER.value, nullable=False, index=True
    )
    purpose: Mapped[str | None] = mapped_column(Text, nullable=True)

    internal_owner_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    counterparty_name: Mapped[str] = mapped_column(String(255), nullable=False)
    counterparty_contact_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, default=dict, nullable=True
    )

    # Linkage to existing ERP records (e.g. Procurement PO, Research Project, Intl Partner)
    related_entity_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    related_entity_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )

    status: Mapped[str] = mapped_column(
        String(32), default=ContractStatus.DRAFT.value, nullable=False, index=True
    )

    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiration_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    renewal_notice_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    termination_notice_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)

    financial_value: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2), nullable=True
    )
    currency: Mapped[str] = mapped_column(String(8), default="USD", nullable=False)

    confidentiality_level: Mapped[str] = mapped_column(
        String(32), default=ConfidentialityLevel.INTERNAL.value, nullable=False
    )

    # Controlled document references
    draft_document_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    executed_document_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )

    # Controlled execution verification (prevents falsely claiming automated electronic signature)
    execution_method: Mapped[str | None] = mapped_column(String(64), nullable=True)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    executed_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    governing_law: Mapped[str | None] = mapped_column(String(128), nullable=True)
    approval_chain_json: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSONB, default=list, nullable=True
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, default=dict, nullable=True
    )

    # Relationships
    amendments: Mapped[list["ContractAmendment"]] = relationship(
        "ContractAmendment",
        back_populates="contract",
        cascade="all, delete-orphan",
        order_by="ContractAmendment.amendment_number",
    )
    obligations: Mapped[list["ContractObligation"]] = relationship(
        "ContractObligation",
        back_populates="contract",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "contract_number", name="uq_contract_tenant_number"),
        Index("ix_contract_tenant_status", "tenant_id", "status"),
        Index("ix_contract_tenant_expiration", "tenant_id", "expiration_date"),
    )


class ContractAmendment(TenantScopedModel):
    """Institutional Contract Amendment and Version Control."""

    __tablename__ = "contract_amendments"

    contract_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("institutional_contracts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amendment_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    extended_expiration_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    financial_value_adjustment: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0.00"), nullable=False
    )

    document_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    status: Mapped[str] = mapped_column(String(32), default="DRAFT", nullable=False)

    contract: Mapped["InstitutionalContract"] = relationship(
        "InstitutionalContract", back_populates="amendments"
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "contract_id", "amendment_number", name="uq_amendment_contract_num"
        ),
    )


class ContractObligation(TenantScopedModel):
    """Contractual Commitments and Obligations Tracking."""

    __tablename__ = "contract_obligations"

    contract_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("institutional_contracts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    obligation_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    obligation_type: Mapped[str] = mapped_column(
        String(64), default=ObligationType.DELIVERABLE.value, nullable=False
    )

    responsible_owner_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    accountable_department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_departments.id", ondelete="SET NULL"),
        nullable=True,
    )

    due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    review_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    reminder_lead_days: Mapped[int] = mapped_column(Integer, default=14, nullable=False)

    status: Mapped[str] = mapped_column(
        String(32), default=ObligationStatus.PENDING.value, nullable=False, index=True
    )

    evidence_document_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    completion_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    waived_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    waived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    waived_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    escalation_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    contract: Mapped["InstitutionalContract"] = relationship(
        "InstitutionalContract", back_populates="obligations"
    )

    __table_args__ = (
        Index("ix_obligation_tenant_due", "tenant_id", "due_date", "status"),
    )


class InstitutionalLegalMatter(TenantScopedModel):
    """Restricted Confidential Legal Matter and Dispute Management."""

    __tablename__ = "institutional_legal_matters"

    matter_number: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(
        String(64), default=MatterCategory.OTHER.value, nullable=False
    )
    restricted_classification: Mapped[str] = mapped_column(
        String(64),
        default=MatterRestrictedClassification.ATTORNEY_CLIENT_PRIVILEGED.value,
        nullable=False,
    )

    internal_owner_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    lead_counsel_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    external_counsel_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)

    counterparty_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    opposing_counsel_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    related_contract_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("institutional_contracts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    related_department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="SET NULL"),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(32), default=MatterStatus.OPEN.value, nullable=False, index=True
    )
    priority: Mapped[str] = mapped_column(
        String(32), default=MatterPriority.MEDIUM.value, nullable=False
    )

    financial_exposure_estimate: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2), nullable=True
    )

    opened_date: Mapped[date] = mapped_column(Date, nullable=False)
    target_resolution_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    closed_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    key_deadlines_json: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSONB, default=list, nullable=True
    )
    associated_documents_json: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSONB, default=list, nullable=True
    )

    # Strictly restricted confidential notes (only counsel & authorized administrators)
    confidential_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolution_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "matter_number", name="uq_matter_tenant_number"),
        Index("ix_matter_tenant_status", "tenant_id", "status"),
    )


class InstitutionalComplianceObligation(TenantScopedModel):
    """Institutional Statutory, Regulatory and Accreditation Compliance Obligations."""

    __tablename__ = "institutional_compliance_obligations"

    obligation_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    authoritative_source_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(
        String(64), default=ComplianceCategory.STATUTORY_REGULATORY.value, nullable=False
    )

    responsible_owner_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="SET NULL"),
        nullable=True,
    )

    review_frequency_months: Mapped[int] = mapped_column(Integer, default=12, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    next_review_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    required_controls: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32),
        default=ComplianceAssessmentStatus.NOT_ASSESSED.value,
        nullable=False,
        index=True,
    )

    assessment_findings: Mapped[str | None] = mapped_column(Text, nullable=True)
    assessed_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    assessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Cross-references to existing policy and contract systems
    related_policy_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    related_contract_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("institutional_contracts.id", ondelete="SET NULL"),
        nullable=True,
    )

    evidence_records_json: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSONB, default=list, nullable=True
    )
    corrective_actions_json: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSONB, default=list, nullable=True
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "obligation_code", name="uq_comp_tenant_code"),
        Index("ix_comp_tenant_status", "tenant_id", "status"),
    )


class InstitutionalRisk(TenantScopedModel):
    """Institutional Enterprise Risk Register with 5x5 Matrix Scoring."""

    __tablename__ = "institutional_risks"

    risk_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(
        String(64), default=RiskCategory.GOVERNANCE_LEGAL.value, nullable=False
    )

    department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="SET NULL"),
        nullable=True,
    )
    responsible_owner_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # 5x5 Matrix: Likelihood (1-5), Impact (1-5)
    inherent_likelihood: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    inherent_impact: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    inherent_score: Mapped[int] = mapped_column(Integer, default=9, nullable=False)

    existing_controls: Mapped[str | None] = mapped_column(Text, nullable=True)

    residual_likelihood: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    residual_impact: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    residual_score: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    risk_level: Mapped[str] = mapped_column(
        String(32), default=RiskLevel.LOW.value, nullable=False, index=True
    )

    mitigation_plan: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_completion_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default=RiskStatus.IDENTIFIED.value, nullable=False, index=True
    )

    accepted_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    acceptance_rationale: Mapped[str | None] = mapped_column(Text, nullable=True)

    related_contract_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("institutional_contracts.id", ondelete="SET NULL"),
        nullable=True,
    )
    related_policy_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    related_compliance_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("institutional_compliance_obligations.id", ondelete="SET NULL"),
        nullable=True,
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "risk_code", name="uq_risk_tenant_code"),
        Index("ix_risk_tenant_level", "tenant_id", "risk_level"),
        Index("ix_risk_tenant_status", "tenant_id", "status"),
    )
