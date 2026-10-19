"""Pydantic Request & Response Schemas for Institutional Research, Innovation & IP (Step 44)."""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.models.research import (
    ResearchEthicsApprovalType,
    ResearchEthicsStatus,
    ResearchGrantExternalStatus,
    ResearchGrantInternalStatus,
    ResearchIPConfidentiality,
    ResearchMilestoneStatus,
    ResearchOpportunityStatus,
    ResearchOutputType,
    ResearchOutputVerificationStatus,
    ResearchPatentStatus,
    ResearchProjectCategory,
    ResearchProjectStatus,
    ResearchRiskSeverity,
    ResearchRiskStatus,
    ResearchTeamRole,
)


# =============================================================================
# 1. RESEARCH PROJECT SCHEMAS
# =============================================================================


class ResearchProjectCreate(BaseModel):
    project_code: str = Field(..., min_length=2, max_length=64)
    title: str = Field(..., min_length=3, max_length=255)
    abstract: str = Field(default="Institutional research project abstract", min_length=1)
    description: str | None = None
    research_objectives: list[str] = Field(default_factory=list)
    research_category: ResearchProjectCategory = Field(default=ResearchProjectCategory.FACULTY_LED, alias="category")
    research_domain: str = Field(..., max_length=128)
    principal_investigator_id: UUID
    department_id: UUID | None = Field(default=None, alias="lead_department_id")
    campus_id: UUID | None = Field(default=None, alias="lead_campus_id")
    start_date: date = Field(default_factory=date.today)
    planned_end_date: date = Field(default_factory=lambda: date.today() + timedelta(days=365), alias="planned_completion_date")
    currency: str = Field(default="USD", max_length=8)
    proposed_budget: float = Field(default=0.0, ge=0.0, alias="total_budget_allocated")
    requires_ethics_approval: bool = False
    ethics_approval_status: str = "NOT_REQUIRED"
    risks_summary: str | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)


class ResearchProjectUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=255)
    abstract: str | None = None
    description: str | None = None
    research_objectives: list[str] | None = None
    research_domain: str | None = None
    lead_department_id: UUID | None = None
    lead_campus_id: UUID | None = None
    start_date: date | None = None
    planned_completion_date: date | None = None
    total_budget_allocated: float | None = Field(default=None, ge=0.0)
    requires_ethics_approval: bool | None = None
    ethics_approval_status: str | None = None
    risks_summary: str | None = None
    metadata_json: dict[str, Any] | None = None


class ResearchProjectTransition(BaseModel):
    to_status: ResearchProjectStatus
    reason: str = Field(..., min_length=3, max_length=1000)
    decision_notes: str | None = None
    extension_date: date | None = None


class ResearchProjectStatusHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    from_status: str
    to_status: str
    changed_by_user_id: UUID
    reason: str
    decision_notes: str | None = None
    transition_date: datetime


class ResearchProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    project_code: str
    title: str
    abstract: str
    description: str | None = None
    research_objectives: list[str] | None = None
    category: str
    research_domain: str
    status: str
    principal_investigator_id: UUID
    lead_department_id: UUID | None = None
    lead_campus_id: UUID | None = None
    start_date: date
    planned_completion_date: date
    actual_completion_date: date | None = None
    currency: str
    total_budget_allocated: float
    requires_ethics_approval: bool
    ethics_approval_status: str
    risks_summary: str | None = None
    lock_version: int
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    # Convenience properties for backward compatibility
    @property
    def proposed_budget(self) -> float:
        return float(self.total_budget_allocated)

    @property
    def approved_budget(self) -> float:
        return float(self.total_budget_allocated)

    @property
    def actual_expenditure(self) -> float:
        return 0.0


# =============================================================================
# 2. RESEARCH TEAM MEMBER SCHEMAS
# =============================================================================


class ResearchTeamMemberCreate(BaseModel):
    project_id: UUID
    user_id: UUID | None = None
    external_collaborator_name: str | None = Field(default=None, alias="external_name")
    external_institution: str | None = None
    external_email: str | None = None
    is_external: bool = False
    role: ResearchTeamRole = ResearchTeamRole.FACULTY_RESEARCHER
    contribution_description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    access_scope: str = Field(default="FULL_READ_WRITE", max_length=32)

    model_config = ConfigDict(populate_by_name=True)


class ResearchTeamMemberUpdate(BaseModel):
    role: ResearchTeamRole | None = None
    contribution_description: str | None = None
    access_scope: str | None = None
    is_active: bool | None = None
    end_date: date | None = None


class ResearchTeamMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    project_id: UUID
    user_id: UUID | None = None
    external_collaborator_name: str | None = None
    external_institution: str | None = None
    role: str
    contribution_description: str | None = None
    start_date: date
    end_date: date | None = None
    is_active: bool
    access_scope: str
    created_at: datetime

    @property
    def is_external(self) -> bool:
        return self.user_id is None

    @property
    def external_name(self) -> str | None:
        return self.external_collaborator_name


# =============================================================================
# 3. RESEARCH FUNDING OPPORTUNITY SCHEMAS
# =============================================================================


class ResearchFundingOpportunityCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=64, alias="opportunity_code")
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(default="", min_length=0)
    funding_agency_name: str = Field(..., min_length=2, max_length=128, alias="funding_organization")
    category: str = Field(default="GOVERNMENT_GRANT", max_length=64)
    research_domains: list[str] = Field(default_factory=list)
    eligibility_criteria: str = Field(default="Standard institutional eligibility", min_length=1)
    opening_date: date = Field(default_factory=date.today)
    closing_date: date
    min_funding_amount: float | None = Field(default=None, ge=0.0, alias="min_amount")
    max_funding_amount: float | None = Field(default=None, ge=0.0, alias="max_amount")
    currency: str = Field(default="USD", max_length=8)
    application_procedure_url: str | None = Field(default=None, alias="opportunity_url")
    internal_opportunity_owner_id: UUID | None = Field(default=None, alias="internal_contact_user_id")
    visibility_scope: str = "INSTITUTION_WIDE"
    campus_id: UUID | None = None
    department_id: UUID | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)


class ResearchFundingOpportunityUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    funding_agency_name: str | None = None
    category: str | None = None
    research_domains: list[str] | None = None
    eligibility_criteria: str | None = None
    opening_date: date | None = None
    closing_date: date | None = None
    min_funding_amount: float | None = None
    max_funding_amount: float | None = None
    status: ResearchOpportunityStatus | None = None
    internal_opportunity_owner_id: UUID | None = None
    metadata_json: dict[str, Any] | None = None


class ResearchFundingOpportunityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    code: str
    title: str
    description: str
    funding_agency_name: str
    category: str
    research_domains: list[str]
    eligibility_criteria: str
    opening_date: date
    closing_date: date
    min_funding_amount: float | None = None
    max_funding_amount: float | None = None
    currency: str
    application_procedure_url: str | None = None
    internal_opportunity_owner_id: UUID | None = None
    visibility_scope: str
    campus_id: UUID | None = None
    department_id: UUID | None = None
    status: str
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    @property
    def opportunity_code(self) -> str:
        return self.code

    @property
    def funding_organization(self) -> str:
        return self.funding_agency_name


# =============================================================================
# 4. RESEARCH GRANT APPLICATION SCHEMAS
# =============================================================================


class ResearchGrantApplicationCreate(BaseModel):
    application_code: str = Field(..., min_length=2, max_length=64)
    funding_opportunity_id: UUID | None = Field(default=None, alias="opportunity_id")
    project_id: UUID | None = None
    title: str = Field(..., min_length=3, max_length=255)
    principal_investigator_id: UUID
    research_proposal_summary: str = Field(default="Grant research proposal", alias="proposal_abstract")
    objectives_json: list[str] = Field(default_factory=list, alias="research_objectives")
    methodology_summary: str | None = Field(default=None, alias="methodology")
    work_packages_json: list[dict[str, Any]] = Field(default_factory=list)
    proposed_budget: float = Field(default=0.0, ge=0.0)
    currency: str = Field(default="USD", max_length=8)
    metadata_json: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)


class ResearchGrantApplicationUpdate(BaseModel):
    title: str | None = None
    research_proposal_summary: str | None = None
    objectives_json: list[str] | None = None
    methodology_summary: str | None = None
    work_packages_json: list[dict[str, Any]] | None = None
    proposed_budget: float | None = None
    metadata_json: dict[str, Any] | None = None


class ResearchGrantInternalReview(BaseModel):
    decision: ResearchGrantInternalStatus = Field(..., alias="decision")
    comments: str = Field(..., min_length=3, max_length=2000)

    model_config = ConfigDict(populate_by_name=True)


class ResearchGrantExternalSubmissionConfirm(BaseModel):
    external_submission_reference: str = Field(..., min_length=2, max_length=128, alias="external_reference_number")
    submission_date: date
    portal_url: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class ResearchGrantApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    application_code: str
    funding_opportunity_id: UUID | None = None
    project_id: UUID | None = None
    title: str
    principal_investigator_id: UUID
    research_proposal_summary: str
    objectives_json: list[str]
    methodology_summary: str | None = None
    work_packages_json: list[dict[str, Any]]
    proposed_budget: float
    currency: str
    internal_review_status: str
    external_submission_status: str
    external_reference_number: str | None = None
    external_submitted_at: datetime | None = None
    submitted_by_user_id: UUID | None = None
    internal_approved_by_id: UUID | None = None
    internal_approved_at: datetime | None = None
    rejection_reason: str | None = None
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    @property
    def external_submission_reference(self) -> str | None:
        return self.external_reference_number


# =============================================================================
# 5. RESEARCH GRANT AWARD SCHEMAS
# =============================================================================


class ResearchGrantAwardCreate(BaseModel):
    award_number: str = Field(..., min_length=2, max_length=64, alias="award_code")
    project_id: UUID
    grant_application_id: UUID | None = Field(default=None, alias="application_id")
    funding_organization: str = Field(..., min_length=2, max_length=128)
    award_amount: float = Field(..., ge=0.0)
    currency: str = Field(default="USD", max_length=8)
    award_date: date
    start_date: date = Field(..., alias="period_start_date")
    end_date: date = Field(..., alias="period_end_date")
    approved_budget_json: dict[str, Any] = Field(default_factory=dict)
    disbursement_schedule_json: list[dict[str, Any]] = Field(default_factory=list)
    spending_conditions: str | None = Field(default=None, alias="conditions_and_restrictions")
    reporting_deadlines_json: list[dict[str, Any]] = Field(default_factory=list, alias="reporting_requirements")
    financial_owner_id: UUID | None = Field(default=None, alias="financial_manager_id")
    metadata_json: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)


class ResearchGrantAwardUpdate(BaseModel):
    disbursement_schedule_json: list[dict[str, Any]] | None = None
    spending_conditions: str | None = None
    end_date: date | None = None
    metadata_json: dict[str, Any] | None = None


class ResearchGrantAwardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    award_number: str
    project_id: UUID
    grant_application_id: UUID | None = None
    funding_organization: str
    award_amount: float
    currency: str
    award_date: date
    start_date: date
    end_date: date
    approved_budget_json: dict[str, Any]
    disbursement_schedule_json: list[dict[str, Any]]
    spending_conditions: str | None = None
    financial_owner_id: UUID
    received_amount: float
    allocated_amount: float
    committed_expenditure: float
    actual_expenditure: float
    remaining_budget: float
    status: str
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    @property
    def award_code(self) -> str:
        return self.award_number

    @property
    def remaining_balance(self) -> float:
        return float(self.remaining_budget)

    @property
    def spent_amount(self) -> float:
        return float(self.actual_expenditure)


# =============================================================================
# 6. RESEARCH BUDGET PLAN SCHEMAS
# =============================================================================


class ResearchBudgetPlanCreate(BaseModel):
    project_id: UUID
    award_id: UUID | None = None
    category: str = Field(default="PERSONNEL", max_length=64)
    item_description: str = Field(default="Budget Line Item", max_length=255)
    personnel_costs: float = Field(default=0.0, ge=0.0)
    equipment_costs: float = Field(default=0.0, ge=0.0)
    consumables_materials_costs: float = Field(default=0.0, ge=0.0)
    travel_fieldwork_costs: float = Field(default=0.0, ge=0.0)
    computing_software_costs: float = Field(default=0.0, ge=0.0)
    publication_dissemination_costs: float = Field(default=0.0, ge=0.0)
    external_services_costs: float = Field(default=0.0, ge=0.0)
    institutional_overheads: float = Field(default=0.0, ge=0.0)
    contingency_costs: float = Field(default=0.0, ge=0.0)
    total_budget: float = Field(default=0.0, ge=0.0, alias="allocated_amount")
    currency: str = Field(default="USD", max_length=8)
    proposed_amount: float = Field(default=0.0, ge=0.0)
    approved_amount: float = Field(default=0.0, ge=0.0)
    approval_notes: str | None = Field(default=None, alias="justification")
    metadata_json: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)


class ResearchBudgetRevisionRequest(BaseModel):
    revised_allocated_amount: float = Field(..., ge=0.0)
    revision_reason: str = Field(..., min_length=3, max_length=1000)


class ResearchBudgetPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    project_id: UUID
    award_id: UUID | None = None
    version_number: int
    status: str
    personnel_costs: float
    equipment_costs: float
    consumables_materials_costs: float
    travel_fieldwork_costs: float
    computing_software_costs: float
    publication_dissemination_costs: float
    external_services_costs: float
    institutional_overheads: float
    contingency_costs: float
    total_budget: float
    currency: str
    approved_by_id: UUID | None = None
    approved_at: datetime | None = None
    approval_notes: str | None = None
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    @property
    def allocated_amount(self) -> float:
        return float(self.total_budget)

    @property
    def revision_reason(self) -> str | None:
        return self.approval_notes


# =============================================================================
# 7. RESEARCH MILESTONE SCHEMAS
# =============================================================================


class ResearchMilestoneCreate(BaseModel):
    project_id: UUID
    milestone_code: str = Field(default_factory=lambda: f"MS-{uuid4().hex[:6].upper()}", max_length=64)
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(default="Milestone deliverable", min_length=1)
    planned_start_date: date = Field(default_factory=date.today)
    planned_completion_date: date = Field(..., alias="planned_date")
    responsible_owner_id: UUID | None = Field(default=None, alias="responsible_user_id")
    acceptance_criteria: str = Field(default="Independent verification required", min_length=1)
    deliverable_reference: str | None = None
    is_mandatory_for_closure: bool = True
    dependencies_json: list[str] = Field(default_factory=list)
    metadata_json: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)


class ResearchMilestoneUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    planned_completion_date: date | None = None
    actual_completion_date: date | None = None
    responsible_owner_id: UUID | None = None
    acceptance_criteria: str | None = None
    deliverable_reference: str | None = None
    completion_percentage: float | None = Field(default=None, ge=0.0, le=100.0)
    is_mandatory_for_closure: bool | None = None
    blocker_notes: str | None = None
    metadata_json: dict[str, Any] | None = None


class ResearchMilestoneVerify(BaseModel):
    decision: ResearchMilestoneStatus = ResearchMilestoneStatus.ACCEPTED
    verification_notes: str = Field(..., min_length=3, max_length=1000)


class ResearchMilestoneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    project_id: UUID
    milestone_code: str
    title: str
    description: str
    sequence_number: int
    planned_start_date: date
    planned_completion_date: date
    actual_completion_date: date | None = None
    responsible_owner_id: UUID
    dependencies_json: list[str]
    acceptance_criteria: str
    completion_percentage: float
    status: str
    is_mandatory_for_closure: bool
    deliverable_reference: str | None = None
    evidence_document_id: UUID | None = None
    verified_by_user_id: UUID | None = None
    verified_at: datetime | None = None
    verification_notes: str | None = None
    created_at: datetime
    updated_at: datetime

    @property
    def planned_date(self) -> date:
        return self.planned_completion_date

    @property
    def actual_date(self) -> date | None:
        return self.actual_completion_date


# =============================================================================
# 8. RESEARCH ETHICS APPROVAL SCHEMAS
# =============================================================================


class ResearchEthicsApprovalCreate(BaseModel):
    project_id: UUID
    approval_code: str = Field(default_factory=lambda: f"ETH-{uuid4().hex[:6].upper()}", max_length=64)
    approval_type: ResearchEthicsApprovalType = ResearchEthicsApprovalType.HUMAN_PARTICIPANTS
    governing_policy_reference: str = Field(..., min_length=2, max_length=128, alias="governing_policy")
    review_committee_name: str = Field(..., min_length=2, max_length=128, alias="committee_name")
    submission_date: date = Field(default_factory=date.today)
    application_reference: str | None = None
    conditions_and_restrictions: str | None = None
    confidential_notes: str | None = None
    document_id: UUID | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)


class ResearchEthicsApprovalDecision(BaseModel):
    decision: ResearchEthicsStatus
    decision_rationale: str = Field(..., min_length=3, max_length=2000)
    approval_date: date
    expiry_date: date | None = None
    conditions_and_restrictions: str | None = None


class ResearchEthicsApprovalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    approval_code: str
    project_id: UUID
    approval_type: str
    governing_policy_reference: str
    review_committee_name: str
    reviewer_user_id: UUID | None = None
    submission_date: date
    decision_date: date | None = None
    status: str
    conditions_and_restrictions: str | None = None
    expiry_date: date | None = None
    decision_rationale: str | None = None
    is_confidential: bool
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 9. RESEARCH PUBLICATIONS & OUTPUTS SCHEMAS
# =============================================================================


class ResearchOutputCreate(BaseModel):
    project_id: UUID | None = None
    output_type: ResearchOutputType = ResearchOutputType.JOURNAL_ARTICLE
    title: str = Field(..., min_length=3, max_length=255)
    abstract: str = Field(default="Scholarly publication abstract", min_length=1)
    authors_json: list[dict[str, Any]] = Field(default_factory=list)
    lead_author_user_id: UUID | None = None
    publication_date: date = Field(default_factory=date.today)
    publisher_or_venue: str = Field(default="Academic Press", max_length=255, alias="publication_venue")
    doi_or_urn: str | None = Field(default=None, max_length=128)
    citation_count: int = Field(default=0, ge=0)
    research_domain: str = Field(default="Multidisciplinary", max_length=128)
    open_access_status: bool = False
    funding_acknowledgements: str | None = Field(default=None, alias="funding_acknowledgement")
    document_id: UUID | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)


class ResearchOutputUpdate(BaseModel):
    title: str | None = None
    abstract: str | None = None
    authors_json: list[dict[str, Any]] | None = None
    publisher_or_venue: str | None = None
    publication_date: date | None = None
    doi_or_urn: str | None = None
    citation_count: int | None = None
    open_access_status: bool | None = None
    funding_acknowledgement: str | None = None
    metadata_json: dict[str, Any] | None = None


class ResearchOutputVerify(BaseModel):
    is_verified: bool = True
    verification_notes: str = Field(..., min_length=3, max_length=1000)
    external_indexing_status: str | None = None


class ResearchOutputResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    project_id: UUID | None = None
    output_type: str
    title: str
    abstract: str
    authors_json: list[dict[str, Any]]
    lead_author_user_id: UUID | None = None
    publication_date: date
    publisher_or_venue: str
    doi_or_urn: str | None = None
    citation_count: int
    research_domain: str
    verification_status: str
    verified_by_user_id: UUID | None = None
    verified_at: datetime | None = None
    verification_notes: str | None = None
    created_at: datetime
    updated_at: datetime

    @property
    def is_verified(self) -> bool:
        return self.verification_status == "VERIFIED"

    @property
    def status(self) -> str:
        return self.verification_status


# =============================================================================
# 10. INTELLECTUAL PROPERTY & INVENTION DISCLOSURES
# =============================================================================


class ResearchInventionDisclosureCreate(BaseModel):
    project_id: UUID | None = None
    award_id: UUID | None = None
    disclosure_code: str = Field(..., min_length=2, max_length=64)
    invention_title: str = Field(..., min_length=3, max_length=255, alias="title")
    technical_abstract: str = Field(..., min_length=10, alias="technical_description")
    detailed_description: str | None = None
    inventors_json: list[dict[str, Any]] = Field(default_factory=list)
    submission_date: date = Field(default_factory=date.today)
    confidentiality_level: ResearchIPConfidentiality = ResearchIPConfidentiality.INTERNAL_CONFIDENTIAL
    institutional_ownership_pct: float = Field(default=100.0, ge=0.0, le=100.0, alias="institutional_ownership_percentage")
    patent_application_number: str | None = None
    patent_jurisdiction: str | None = None
    patent_filing_date: date | None = None
    patent_status: ResearchPatentStatus = Field(default=ResearchPatentStatus.NOT_FILED, alias="patent_filing_status")
    commercialization_revenue: float = Field(default=0.0, ge=0.0)
    licensing_notes: str | None = None
    document_id: UUID | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)


class ResearchInventionDisclosureUpdate(BaseModel):
    invention_title: str | None = None
    technical_abstract: str | None = None
    institutional_ownership_pct: float | None = None
    confidentiality_level: ResearchIPConfidentiality | None = None
    patent_status: ResearchPatentStatus | None = None
    patent_application_number: str | None = None
    patent_jurisdiction: str | None = None
    patent_filing_date: date | None = None
    licensing_notes: str | None = None
    commercialization_revenue: float | None = None
    metadata_json: dict[str, Any] | None = None


class ResearchInventionDisclosureResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    disclosure_code: str
    project_id: UUID | None = None
    award_id: UUID | None = None
    invention_title: str
    technical_abstract: str
    detailed_description: str | None = None
    inventors_json: list[dict[str, Any]]
    submission_date: date
    confidentiality_level: str
    institutional_ownership_pct: float
    evaluation_status: str
    patent_application_number: str | None = None
    patent_jurisdiction: str | None = None
    patent_filing_date: date | None = None
    patent_status: str
    commercialization_status: str
    license_revenue_total: float
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    @property
    def title(self) -> str:
        return self.invention_title

    @property
    def patent_filing_status(self) -> str:
        return self.patent_status

    @property
    def commercialization_revenue(self) -> float:
        return float(self.license_revenue_total)


# =============================================================================
# 11. RESEARCH FACILITY REFERENCES & PROJECT RISKS
# =============================================================================


class ResearchFacilityReferenceCreate(BaseModel):
    project_id: UUID
    facility_name: str = Field(..., min_length=2, max_length=128)
    facility_type: str = Field(default="LAB", max_length=64)
    asset_reference_id: str | None = Field(default=None, alias="equipment_identifier")
    booking_reference: str | None = Field(default=None, alias="booking_reference_id")
    usage_hours: float = Field(default=0.0, ge=0.0, alias="usage_hours_consumed")
    notes: str | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)


class ResearchFacilityReferenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    project_id: UUID
    facility_name: str
    facility_type: str
    equipment_identifier: str | None = None
    booking_reference_id: str | None = None
    usage_hours_consumed: float
    notes: str | None = None
    created_at: datetime


class ResearchProjectRiskCreate(BaseModel):
    project_id: UUID
    risk_code: str = Field(default_factory=lambda: f"RSK-{uuid4().hex[:6].upper()}", max_length=64)
    title: str = Field(..., min_length=3, max_length=255, alias="risk_title")
    category: str = Field(default="TECHNICAL", max_length=64, alias="risk_category")
    likelihood: int = Field(default=3, ge=1, le=5)
    impact: int = Field(default=3, ge=1, le=5)
    responsible_owner_id: UUID | None = Field(default=None, alias="owner_user_id")
    mitigation_plan: str = Field(default="Mitigation strategy established", min_length=1)
    target_resolution_date: date = Field(default_factory=lambda: date.today() + timedelta(days=90))
    metadata_json: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)


class ResearchProjectRiskUpdate(BaseModel):
    status: ResearchRiskStatus | None = None
    likelihood: int | None = Field(default=None, ge=1, le=5)
    impact: int | None = Field(default=None, ge=1, le=5)
    mitigation_plan: str | None = None
    target_resolution_date: date | None = None
    resolution_notes: str | None = None


class ResearchProjectRiskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    project_id: UUID
    risk_code: str
    title: str
    category: str
    likelihood: str
    impact: str
    calculated_risk_level: str
    responsible_owner_id: UUID
    mitigation_plan: str
    target_resolution_date: date
    status: str
    resolution_notes: str | None = None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 12. RESEARCH ANALYTICS & SCHEDULER SWEEPS
# =============================================================================


class ResearchAnalyticsSummaryResponse(BaseModel):
    total_projects: int
    active_projects: int
    completed_projects: int
    under_review_projects: int
    total_proposed_budget: float
    total_awarded_funding: float
    total_actual_expenditure: float
    budget_utilization_rate: float
    total_funding_opportunities: int
    total_grant_applications: int
    approved_grant_applications: int
    grant_success_rate: float
    total_milestones: int
    overdue_milestones: int
    ethics_approvals_count: int
    expiring_ethics_approvals: int
    total_publications: int
    verified_publications: int
    total_citations: int
    total_invention_disclosures: int
    patents_filed_or_granted: int
    commercialization_revenue: float


class ResearchDeadlineSweepResponse(BaseModel):
    processed_at: datetime
    expiring_ethics_approvals_flagged: int
    overdue_milestones_flagged: int
    closing_opportunities_flagged: int
