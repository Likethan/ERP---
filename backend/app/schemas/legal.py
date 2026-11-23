"""Pydantic v2 Request & Response Schemas for Step 62: Enterprise Legal Affairs, Contract Lifecycle, Policy Compliance & Institutional Risk Management."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.legal import (
    ComplianceAssessmentStatus,
    ComplianceCategory,
    ConfidentialityLevel,
    ContractCategory,
    ContractStatus,
    MatterCategory,
    MatterPriority,
    MatterRestrictedClassification,
    MatterStatus,
    ObligationType,
    RiskCategory,
    RiskStatus,
)

# =============================================================================
# 1. CONTRACT AMENDMENT SCHEMAS
# =============================================================================


class ContractAmendmentCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    description: str | None = None
    effective_date: date
    extended_expiration_date: date | None = None
    financial_value_adjustment: Decimal = Field(default=Decimal("0.00"))
    document_id: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class ContractAmendmentResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    contract_id: UUID
    amendment_number: int
    title: str
    description: str | None = None
    effective_date: date
    extended_expiration_date: date | None = None
    financial_value_adjustment: Decimal
    document_id: UUID | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 2. CONTRACT OBLIGATION SCHEMAS
# =============================================================================


class ContractObligationCreate(BaseModel):
    contract_id: UUID
    obligation_code: str | None = Field(default=None, max_length=64)
    title: str = Field(..., min_length=2, max_length=255)
    description: str | None = None
    obligation_type: ObligationType = Field(default=ObligationType.DELIVERABLE)
    responsible_owner_id: UUID | None = None
    accountable_department_id: UUID | None = None
    due_date: date
    review_date: date | None = None
    reminder_lead_days: int = Field(default=14, ge=1, le=180)

    model_config = ConfigDict(from_attributes=True)


class ObligationCompleteRequest(BaseModel):
    evidence_document_id: UUID | None = None
    completion_notes: str | None = None


class ObligationWaiveRequest(BaseModel):
    waived_reason: str = Field(..., min_length=5)


class ContractObligationResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    contract_id: UUID
    obligation_code: str
    title: str
    description: str | None = None
    obligation_type: str
    responsible_owner_id: UUID | None = None
    accountable_department_id: UUID | None = None
    due_date: date
    review_date: date | None = None
    reminder_lead_days: int
    status: str
    evidence_document_id: UUID | None = None
    completion_notes: str | None = None
    completed_by_id: UUID | None = None
    completed_at: datetime | None = None
    waived_by_id: UUID | None = None
    waived_at: datetime | None = None
    waived_reason: str | None = None
    escalation_level: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 3. CONTRACT LIFECYCLE SCHEMAS
# =============================================================================


class ContractCreate(BaseModel):
    contract_number: str | None = Field(default=None, max_length=64)
    title: str = Field(..., min_length=3, max_length=255)
    category: ContractCategory = Field(default=ContractCategory.OTHER)
    purpose: str | None = None
    internal_owner_id: UUID
    department_id: UUID | None = None
    campus_id: UUID | None = None
    counterparty_name: str = Field(..., min_length=2, max_length=255)
    counterparty_contact_json: dict[str, Any] = Field(default_factory=dict)
    related_entity_type: str | None = None
    related_entity_id: UUID | None = None
    effective_date: date | None = None
    expiration_date: date | None = None
    auto_renew: bool = False
    renewal_notice_days: int = Field(default=30, ge=0)
    termination_notice_days: int = Field(default=30, ge=0)
    financial_value: Decimal | None = None
    currency: str = Field(default="USD", max_length=8)
    confidentiality_level: ConfidentialityLevel = Field(default=ConfidentialityLevel.INTERNAL)
    draft_document_id: UUID | None = None
    governing_law: str | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class ContractUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=255)
    category: ContractCategory | None = None
    purpose: str | None = None
    internal_owner_id: UUID | None = None
    department_id: UUID | None = None
    campus_id: UUID | None = None
    counterparty_name: str | None = None
    counterparty_contact_json: dict[str, Any] | None = None
    effective_date: date | None = None
    expiration_date: date | None = None
    auto_renew: bool | None = None
    renewal_notice_days: int | None = None
    termination_notice_days: int | None = None
    financial_value: Decimal | None = None
    currency: str | None = None
    confidentiality_level: ConfidentialityLevel | None = None
    draft_document_id: UUID | None = None
    governing_law: str | None = None
    metadata_json: dict[str, Any] | None = None


class ContractTransitionRequest(BaseModel):
    target_status: ContractStatus
    comment: str | None = None


class ContractExecutionConfirmRequest(BaseModel):
    execution_method: str = Field(
        ...,
        description="Verified method, e.g. WET_SIGNATURE_CONFIRMED, EXTERNAL_DIGITAL_SUITE_CONFIRMED, EXCHANGE_OF_LETTERS",
    )
    executed_at: datetime
    executed_document_id: UUID | None = None
    notes: str | None = None


class ContractResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    contract_number: str
    title: str
    category: str
    purpose: str | None = None
    internal_owner_id: UUID
    department_id: UUID | None = None
    campus_id: UUID | None = None
    counterparty_name: str
    counterparty_contact_json: dict[str, Any] | None = None
    related_entity_type: str | None = None
    related_entity_id: UUID | None = None
    status: str
    effective_date: date | None = None
    expiration_date: date | None = None
    auto_renew: bool
    renewal_notice_days: int
    termination_notice_days: int
    financial_value: Decimal | None = None
    currency: str
    confidentiality_level: str
    draft_document_id: UUID | None = None
    executed_document_id: UUID | None = None
    execution_method: str | None = None
    executed_at: datetime | None = None
    executed_by_id: UUID | None = None
    governing_law: str | None = None
    approval_chain_json: list[dict[str, Any]] | None = None
    metadata_json: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime
    amendments: list[ContractAmendmentResponse] = Field(default_factory=list)
    obligations: list[ContractObligationResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 4. INSTITUTIONAL LEGAL MATTER SCHEMAS
# =============================================================================


class MatterCreate(BaseModel):
    matter_number: str | None = Field(default=None, max_length=64)
    title: str = Field(..., min_length=3, max_length=255)
    category: MatterCategory = Field(default=MatterCategory.OTHER)
    restricted_classification: MatterRestrictedClassification = Field(
        default=MatterRestrictedClassification.ATTORNEY_CLIENT_PRIVILEGED
    )
    internal_owner_id: UUID
    lead_counsel_user_id: UUID | None = None
    external_counsel_ref: str | None = None
    counterparty_name: str | None = None
    opposing_counsel_name: str | None = None
    related_contract_id: UUID | None = None
    related_department_id: UUID | None = None
    campus_id: UUID | None = None
    priority: MatterPriority = Field(default=MatterPriority.MEDIUM)
    financial_exposure_estimate: Decimal | None = None
    opened_date: date = Field(default_factory=date.today)
    target_resolution_date: date | None = None
    key_deadlines_json: list[dict[str, Any]] = Field(default_factory=list)
    associated_documents_json: list[dict[str, Any]] = Field(default_factory=list)
    confidential_notes: str | None = None

    model_config = ConfigDict(from_attributes=True)


class MatterUpdate(BaseModel):
    title: str | None = None
    category: MatterCategory | None = None
    restricted_classification: MatterRestrictedClassification | None = None
    internal_owner_id: UUID | None = None
    lead_counsel_user_id: UUID | None = None
    external_counsel_ref: str | None = None
    counterparty_name: str | None = None
    opposing_counsel_name: str | None = None
    status: MatterStatus | None = None
    priority: MatterPriority | None = None
    financial_exposure_estimate: Decimal | None = None
    target_resolution_date: date | None = None
    closed_date: date | None = None
    key_deadlines_json: list[dict[str, Any]] | None = None
    associated_documents_json: list[dict[str, Any]] | None = None
    confidential_notes: str | None = None
    resolution_summary: str | None = None


class MatterResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    matter_number: str
    title: str
    category: str
    restricted_classification: str
    internal_owner_id: UUID
    lead_counsel_user_id: UUID | None = None
    external_counsel_ref: str | None = None
    counterparty_name: str | None = None
    opposing_counsel_name: str | None = None
    related_contract_id: UUID | None = None
    related_department_id: UUID | None = None
    campus_id: UUID | None = None
    status: str
    priority: str
    financial_exposure_estimate: Decimal | None = None
    opened_date: date
    target_resolution_date: date | None = None
    closed_date: date | None = None
    key_deadlines_json: list[dict[str, Any]] | None = None
    associated_documents_json: list[dict[str, Any]] | None = None
    confidential_notes: str | None = None
    resolution_summary: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 5. COMPLIANCE OBLIGATION SCHEMAS
# =============================================================================


class ComplianceCreate(BaseModel):
    obligation_code: str | None = Field(default=None, max_length=64)
    name: str = Field(..., min_length=3, max_length=255)
    description: str | None = None
    authoritative_source_reference: str = Field(..., min_length=2, max_length=255)
    category: ComplianceCategory = Field(default=ComplianceCategory.STATUTORY_REGULATORY)
    responsible_owner_id: UUID | None = None
    department_id: UUID | None = None
    campus_id: UUID | None = None
    review_frequency_months: int = Field(default=12, ge=1, le=60)
    due_date: date
    next_review_date: date | None = None
    required_controls: str | None = None
    related_policy_id: UUID | None = None
    related_contract_id: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class ComplianceAssessRequest(BaseModel):
    status: ComplianceAssessmentStatus
    assessment_findings: str = Field(..., min_length=3)
    evidence_records_json: list[dict[str, Any]] = Field(default_factory=list)
    corrective_actions_json: list[dict[str, Any]] = Field(default_factory=list)
    next_review_date: date | None = None


class ComplianceResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    obligation_code: str
    name: str
    description: str | None = None
    authoritative_source_reference: str
    category: str
    responsible_owner_id: UUID | None = None
    department_id: UUID | None = None
    campus_id: UUID | None = None
    review_frequency_months: int
    due_date: date
    next_review_date: date | None = None
    required_controls: str | None = None
    status: str
    assessment_findings: str | None = None
    assessed_by_id: UUID | None = None
    assessed_at: datetime | None = None
    related_policy_id: UUID | None = None
    related_contract_id: UUID | None = None
    evidence_records_json: list[dict[str, Any]] | None = None
    corrective_actions_json: list[dict[str, Any]] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 6. INSTITUTIONAL ENTERPRISE RISK SCHEMAS
# =============================================================================


class RiskCreate(BaseModel):
    risk_code: str | None = Field(default=None, max_length=64)
    title: str = Field(..., min_length=3, max_length=255)
    description: str | None = None
    category: RiskCategory = Field(default=RiskCategory.GOVERNANCE_LEGAL)
    department_id: UUID | None = None
    campus_id: UUID | None = None
    responsible_owner_id: UUID | None = None
    inherent_likelihood: int = Field(default=3, ge=1, le=5)
    inherent_impact: int = Field(default=3, ge=1, le=5)
    existing_controls: str | None = None
    residual_likelihood: int = Field(default=2, ge=1, le=5)
    residual_impact: int = Field(default=2, ge=1, le=5)
    mitigation_plan: str | None = None
    target_completion_date: date | None = None
    related_contract_id: UUID | None = None
    related_policy_id: UUID | None = None
    related_compliance_id: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class RiskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    category: RiskCategory | None = None
    department_id: UUID | None = None
    campus_id: UUID | None = None
    responsible_owner_id: UUID | None = None
    inherent_likelihood: int | None = Field(default=None, ge=1, le=5)
    inherent_impact: int | None = Field(default=None, ge=1, le=5)
    existing_controls: str | None = None
    residual_likelihood: int | None = Field(default=None, ge=1, le=5)
    residual_impact: int | None = Field(default=None, ge=1, le=5)
    mitigation_plan: str | None = None
    target_completion_date: date | None = None
    status: RiskStatus | None = None


class RiskAcceptRequest(BaseModel):
    acceptance_rationale: str = Field(..., min_length=5)


class RiskResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    risk_code: str
    title: str
    description: str | None = None
    category: str
    department_id: UUID | None = None
    campus_id: UUID | None = None
    responsible_owner_id: UUID | None = None
    inherent_likelihood: int
    inherent_impact: int
    inherent_score: int
    existing_controls: str | None = None
    residual_likelihood: int
    residual_impact: int
    residual_score: int
    risk_level: str
    mitigation_plan: str | None = None
    target_completion_date: date | None = None
    status: str
    accepted_by_id: UUID | None = None
    acceptance_rationale: str | None = None
    related_contract_id: UUID | None = None
    related_policy_id: UUID | None = None
    related_compliance_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 7. DASHBOARD & RENEWAL AUTOMATION SCHEMAS
# =============================================================================


class LegalOperationsDashboardResponse(BaseModel):
    contracts_pending_review_count: int
    contracts_expiring_soon_count: int
    obligations_overdue_count: int
    policies_pending_review_count: int
    open_legal_matters_count: int
    compliance_actions_outstanding_count: int
    high_priority_risks_count: int
    recent_contracts: list[ContractResponse]
    expiring_contracts: list[ContractResponse]
    overdue_obligations: list[ContractObligationResponse]
    critical_matters: list[MatterResponse]
    critical_risks: list[RiskResponse]


class RenewalSweepResult(BaseModel):
    contracts_flagged_expiring: int
    obligations_flagged_overdue: int
    compliance_reviews_flagged: int
    notifications_dispatched: int
