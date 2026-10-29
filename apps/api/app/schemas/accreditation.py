"""Pydantic Request & Response Schemas for Institutional Accreditation & Quality Assurance (Step 43)."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.accreditation import (
    AccreditationCriterionType,
    AccreditationEvidenceCategory,
    AccreditationEvidenceVerificationStatus,
    AccreditationFrameworkType,
    AccreditationMaturityLevel,
    AccreditationScoringModel,
    QualityAuditType,
    QualityCAPAType,
    QualityFindingSeverity,
    QualityImprovementStatus,
    QualityIndicatorCategory,
)

# =============================================================================
# 1. ACCREDITATION FRAMEWORK SCHEMAS
# =============================================================================


class AccreditationFrameworkCreate(BaseModel):
    code: str = Field(..., max_length=64)
    name: str = Field(..., max_length=255)
    description: str | None = None
    issuing_body: str = Field(..., max_length=128)
    framework_type: AccreditationFrameworkType = AccreditationFrameworkType.CUSTOM
    scope_type: str = "INSTITUTION"
    campus_id: UUID | None = None
    department_id: UUID | None = None
    effective_from: datetime | None = None
    effective_until: datetime | None = None
    review_by_date: datetime | None = None
    scoring_model: AccreditationScoringModel = AccreditationScoringModel.NUMERIC_SCALE
    max_score: float | None = 1000.0
    weighting_supported: bool = True
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class AccreditationFrameworkUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    issuing_body: str | None = None
    scope_type: str | None = None
    effective_from: datetime | None = None
    effective_until: datetime | None = None
    review_by_date: datetime | None = None
    max_score: float | None = None
    weighting_supported: bool | None = None
    metadata_json: dict[str, Any] | None = None


class AccreditationFrameworkPublish(BaseModel):
    change_summary: str = Field(..., min_length=5, max_length=1000)


class AccreditationFrameworkVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    framework_id: UUID
    version_number: int
    title: str
    description: str | None = None
    rules_snapshot_json: dict[str, Any]
    criteria_snapshot_json: list[dict[str, Any]]
    change_summary: str | None = None
    published_by_user_id: UUID
    published_at: datetime
    created_at: datetime


class AccreditationFrameworkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    code: str
    name: str
    description: str | None = None
    issuing_body: str
    framework_type: str
    scope_type: str
    campus_id: UUID | None = None
    department_id: UUID | None = None
    status: str
    current_version_number: int
    effective_from: datetime | None = None
    effective_until: datetime | None = None
    review_by_date: datetime | None = None
    owner_user_id: UUID
    scoring_model: str
    max_score: float | None = None
    weighting_supported: bool
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 2. CRITERIA SCHEMAS
# =============================================================================


class AccreditationCriterionCreate(BaseModel):
    code: str = Field(..., max_length=64)
    title: str = Field(..., max_length=255)
    description: str | None = None
    parent_criterion_id: UUID | None = None
    criterion_type: AccreditationCriterionType = AccreditationCriterionType.QUALITATIVE
    weight: float = 1.0
    max_score: float = 100.0
    is_mandatory: bool = True
    assessment_guidelines: str | None = None
    evidence_requirements: list[str] = Field(default_factory=list)
    order_index: int = 0
    is_active: bool = True
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class AccreditationCriterionUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    parent_criterion_id: UUID | None = None
    criterion_type: AccreditationCriterionType | None = None
    weight: float | None = None
    max_score: float | None = None
    is_mandatory: bool | None = None
    assessment_guidelines: str | None = None
    evidence_requirements: list[str] | None = None
    order_index: int | None = None
    is_active: bool | None = None
    metadata_json: dict[str, Any] | None = None


class AccreditationCriterionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    framework_id: UUID
    parent_criterion_id: UUID | None = None
    code: str
    title: str
    description: str | None = None
    criterion_type: str
    weight: float
    max_score: float
    is_mandatory: bool
    assessment_guidelines: str | None = None
    evidence_requirements: list[str]
    order_index: int
    is_active: bool
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 3. ASSESSMENT CYCLE & CRITERION ASSESSMENT SCHEMAS
# =============================================================================


class AccreditationCycleCreate(BaseModel):
    framework_id: UUID
    code: str = Field(..., max_length=64)
    title: str = Field(..., max_length=255)
    academic_year: str = Field(..., max_length=32)
    start_date: datetime
    end_date: datetime
    target_submission_date: datetime | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class AccreditationCycleUpdate(BaseModel):
    title: str | None = None
    target_submission_date: datetime | None = None
    status: str | None = None
    metadata_json: dict[str, Any] | None = None


class AccreditationCycleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    framework_id: UUID
    code: str
    title: str
    academic_year: str
    start_date: datetime
    end_date: datetime
    target_submission_date: datetime | None = None
    status: str
    overall_score: float | None = None
    readiness_percentage: float
    lead_coordinator_id: UUID
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class CriterionAssessmentDraftUpdate(BaseModel):
    department_id: UUID | None = None
    score: float | None = None
    target_score: float | None = None
    maturity_level: AccreditationMaturityLevel | None = None
    not_applicable_reason: str | None = None
    executive_summary: str | None = None
    findings: str | None = None
    strengths: str | None = None
    weaknesses: str | None = None
    recommendations: str | None = None
    lock_version: int = Field(..., description="Optimistic locking version")


class CriterionAssessmentSubmit(BaseModel):
    lock_version: int
    submission_notes: str | None = None


class CriterionAssessmentReview(BaseModel):
    decision: str = Field(..., description="APPROVED or CHANGES_REQUESTED or NON_COMPLIANT")
    reviewer_comments: str = Field(..., min_length=3)
    adjusted_score: float | None = None


class CriterionAssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    cycle_id: UUID
    criterion_id: UUID
    department_id: UUID | None = None
    accountable_owner_id: UUID
    status: str
    score: float | None = None
    target_score: float | None = None
    maturity_level: str | None = None
    not_applicable_reason: str | None = None
    executive_summary: str | None = None
    findings: str | None = None
    strengths: str | None = None
    weaknesses: str | None = None
    recommendations: str | None = None
    assessor_id: UUID | None = None
    reviewer_id: UUID | None = None
    assessed_at: datetime | None = None
    reviewed_at: datetime | None = None
    lock_version: int
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 4. EVIDENCE SCHEMAS
# =============================================================================


class AccreditationEvidenceCreate(BaseModel):
    evidence_code: str = Field(..., max_length=64)
    title: str = Field(..., max_length=255)
    description: str | None = None
    evidence_category: AccreditationEvidenceCategory = AccreditationEvidenceCategory.POLICY_SOP
    source_type: str = "DOCUMENT"
    document_id: UUID | None = None
    knowledge_item_id: UUID | None = None
    record_id: UUID | None = None
    external_uri: str | None = None
    campus_id: UUID | None = None
    department_id: UUID | None = None
    valid_from: datetime
    valid_until: datetime | None = None
    confidentiality: str = "INTERNAL"
    integrity_hash_sha256: str | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class AccreditationEvidenceVerify(BaseModel):
    verification_status: AccreditationEvidenceVerificationStatus = AccreditationEvidenceVerificationStatus.VERIFIED
    reviewer_notes: str = Field(..., min_length=3)


class AccreditationEvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    evidence_code: str
    title: str
    description: str | None = None
    evidence_category: str
    source_type: str
    document_id: UUID | None = None
    knowledge_item_id: UUID | None = None
    record_id: UUID | None = None
    external_uri: str | None = None
    campus_id: UUID | None = None
    department_id: UUID | None = None
    owner_user_id: UUID
    valid_from: datetime
    valid_until: datetime | None = None
    is_expired: bool
    confidentiality: str
    verification_status: str
    verified_by_user_id: UUID | None = None
    verified_at: datetime | None = None
    reviewer_notes: str | None = None
    integrity_hash_sha256: str | None = None
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class AccreditationEvidenceMapCreate(BaseModel):
    evidence_id: UUID
    relevance_remarks: str | None = None


class AccreditationEvidenceMapResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    assessment_id: UUID
    evidence_id: UUID
    relevance_remarks: str | None = None
    mapped_by_user_id: UUID
    created_at: datetime


# =============================================================================
# 5. QUALITY INDICATORS & OBSERVATIONS
# =============================================================================


class QualityIndicatorCreate(BaseModel):
    code: str = Field(..., max_length=64)
    name: str = Field(..., max_length=255)
    description: str | None = None
    category: QualityIndicatorCategory = QualityIndicatorCategory.ACADEMIC_EXCELLENCE
    source_module: str = "ACADEMICS"
    calculation_method: str
    reporting_frequency: str = "ANNUAL"
    unit_of_measurement: str = "PERCENTAGE"
    target_value: float = 100.0
    benchmark_threshold: float = 75.0
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class QualityIndicatorUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category: QualityIndicatorCategory | None = None
    calculation_method: str | None = None
    target_value: float | None = None
    benchmark_threshold: float | None = None
    is_active: bool | None = None
    metadata_json: dict[str, Any] | None = None


class QualityIndicatorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    code: str
    name: str
    description: str | None = None
    category: str
    source_module: str
    calculation_method: str
    reporting_frequency: str
    unit_of_measurement: str
    target_value: float
    benchmark_threshold: float
    current_value: float | None = None
    last_calculated_at: datetime | None = None
    data_quality_status: str
    data_quality_notes: str | None = None
    owner_user_id: UUID
    is_active: bool
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class QualityIndicatorObservationCreate(BaseModel):
    period_label: str = Field(..., max_length=64)
    observation_date: datetime
    observed_value: float
    target_value: float
    data_source_mode: str = "AUTOMATED_QUERY"
    is_verified: bool = True
    data_completeness_pct: float = 100.0
    outlier_flag: bool = False
    notes: str | None = None


class QualityIndicatorObservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    indicator_id: UUID
    period_label: str
    observation_date: datetime
    observed_value: float
    target_value: float
    data_source_mode: str
    is_verified: bool
    data_completeness_pct: float
    outlier_flag: bool
    notes: str | None = None
    observed_by_user_id: UUID
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 6. INTERNAL AUDITS & QUALITY REVIEWS
# =============================================================================


class QualityAuditProgramCreate(BaseModel):
    code: str = Field(..., max_length=64)
    title: str = Field(..., max_length=255)
    description: str | None = None
    audit_type: QualityAuditType = QualityAuditType.ACADEMIC_AUDIT
    scope: str = "INSTITUTION_WIDE"
    campus_id: UUID | None = None
    department_id: UUID | None = None
    co_auditors_json: list[str] = Field(default_factory=list)
    scheduled_start_date: datetime
    scheduled_end_date: datetime
    conflict_of_interest_declared: bool = False
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class QualityAuditFinalize(BaseModel):
    summary_findings: str = Field(..., min_length=10)
    recommendations: str = Field(..., min_length=10)


class QualityAuditProgramResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    code: str
    title: str
    description: str | None = None
    audit_type: str
    scope: str
    campus_id: UUID | None = None
    department_id: UUID | None = None
    lead_auditor_id: UUID
    co_auditors_json: list[str]
    scheduled_start_date: datetime
    scheduled_end_date: datetime
    actual_completion_date: datetime | None = None
    status: str
    conflict_of_interest_declared: bool
    summary_findings: str | None = None
    recommendations: str | None = None
    finalized_at: datetime | None = None
    finalized_by_user_id: UUID | None = None
    is_immutable: bool
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class QualityAuditChecklistItemCreate(BaseModel):
    criterion_id: UUID | None = None
    item_code: str = Field(..., max_length=64)
    requirement_description: str
    compliance_status: str = "COMPLIANT"
    auditor_notes: str | None = None
    evidence_reference: str | None = None
    order_index: int = 0


class QualityAuditChecklistItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    audit_program_id: UUID
    criterion_id: UUID | None = None
    item_code: str
    requirement_description: str
    compliance_status: str
    auditor_notes: str | None = None
    evidence_reference: str | None = None
    order_index: int
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 7. FINDINGS & CORRECTIVE ACTIONS (CAPA)
# =============================================================================


class QualityFindingCreate(BaseModel):
    finding_code: str = Field(..., max_length=64)
    source_type: str = "INTERNAL_AUDIT"
    audit_program_id: UUID | None = None
    criterion_id: UUID | None = None
    department_id: UUID | None = None
    title: str = Field(..., max_length=255)
    description: str
    root_cause_analysis: str | None = None
    severity: QualityFindingSeverity = QualityFindingSeverity.MEDIUM
    assigned_owner_id: UUID
    target_resolution_date: datetime
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class QualityFindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    finding_code: str
    source_type: str
    audit_program_id: UUID | None = None
    criterion_id: UUID | None = None
    department_id: UUID | None = None
    title: str
    description: str
    root_cause_analysis: str | None = None
    severity: str
    status: str
    identified_by_user_id: UUID
    assigned_owner_id: UUID
    target_resolution_date: datetime
    resolved_at: datetime | None = None
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class QualityCAPACreate(BaseModel):
    action_code: str = Field(..., max_length=64)
    action_type: QualityCAPAType = QualityCAPAType.CORRECTIVE
    proposed_action: str
    preventive_measures: str | None = None
    responsible_owner_id: UUID
    due_date: datetime
    verification_criteria: str
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class QualityCAPAClose(BaseModel):
    closure_decision: str = Field(..., description="CLOSED_EFFECTIVE or REJECTED_FURTHER_ACTION")
    closure_notes: str = Field(..., min_length=5)
    evidence_notes: str | None = None
    evidence_document_id: UUID | None = None


class QualityCAPAResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    finding_id: UUID
    action_code: str
    action_type: str
    proposed_action: str
    preventive_measures: str | None = None
    responsible_owner_id: UUID
    status: str
    due_date: datetime
    completed_at: datetime | None = None
    evidence_notes: str | None = None
    evidence_document_id: UUID | None = None
    verification_criteria: str
    verified_by_user_id: UUID | None = None
    verified_at: datetime | None = None
    closure_decision: str | None = None
    closure_notes: str | None = None
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 8. CONTINUOUS QUALITY IMPROVEMENT (CQI) SCHEMAS
# =============================================================================


class QualityImprovementPlanCreate(BaseModel):
    code: str = Field(..., max_length=64)
    title: str = Field(..., max_length=255)
    objective: str
    baseline_measurement: str
    target_outcome: str
    linked_indicator_id: UUID | None = None
    responsible_owner_id: UUID
    start_date: datetime
    target_date: datetime
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class QualityImprovementPlanUpdate(BaseModel):
    title: str | None = None
    objective: str | None = None
    status: QualityImprovementStatus | None = None
    evaluation_notes: str | None = None
    lessons_learned: str | None = None
    metadata_json: dict[str, Any] | None = None


class QualityImprovementPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    code: str
    title: str
    objective: str
    baseline_measurement: str
    target_outcome: str
    linked_indicator_id: UUID | None = None
    responsible_owner_id: UUID
    start_date: datetime
    target_date: datetime
    actual_completion_date: datetime | None = None
    status: str
    evaluation_notes: str | None = None
    lessons_learned: str | None = None
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 9. ACCREDITATION READINESS & SUMMARY SCHEMAS
# =============================================================================


class AccreditationReadinessResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    cycle_id: UUID
    framework_id: UUID
    overall_readiness_score: float
    criteria_assessed_count: int
    criteria_total_count: int
    evidence_verified_count: int
    evidence_required_count: int
    open_high_risk_findings_count: int
    score_projected: float | None = None
    score_maximum: float | None = None
    readiness_category: str
    gap_summary_json: list[dict[str, Any]]
    department_readiness_json: dict[str, Any]
    calculated_by_user_id: UUID
    created_at: datetime


class AccreditationDashboardSummary(BaseModel):
    active_frameworks_count: int
    active_cycles_count: int
    total_criteria_count: int
    assessed_criteria_count: int
    verified_evidences_count: int
    total_evidences_count: int
    open_findings_count: int
    critical_findings_count: int
    active_audits_count: int
    active_cqi_plans_count: int
    overall_readiness_avg_pct: float
