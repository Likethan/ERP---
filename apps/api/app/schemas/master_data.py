"""Pydantic v2 Schemas for Enterprise Master Data Management & Data Quality (Step 24)."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.master_data import (
    CorrectionStatus,
    DuplicateStatus,
    LineageSource,
    MasterDataSensitivity,
    QualityIssueStatus,
    QualityRuleType,
    QualitySeverity,
    SurvivorshipRule,
)

# =============================================================================
# 1. MASTER DATA DEFINITIONS
# =============================================================================


class MasterDataDefinitionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    key: str
    display_name: str
    description: str | None = None
    owner_domain: str
    steward_role: str
    sensitivity: MasterDataSensitivity
    duplicate_detection_enabled: bool
    merge_supported: bool
    archival_supported: bool
    authoritative_source: str
    canonical_table_name: str
    canonical_id_column: str
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None


class MasterDataDefinitionCreate(BaseModel):
    key: str = Field(..., max_length=64, description="Unique key for governed master entity")
    display_name: str = Field(..., max_length=128)
    description: str | None = None
    owner_domain: str = Field(..., max_length=64)
    steward_role: str = Field("INSTITUTION_ADMIN", max_length=64)
    sensitivity: MasterDataSensitivity = MasterDataSensitivity.INTERNAL
    duplicate_detection_enabled: bool = True
    merge_supported: bool = False
    archival_supported: bool = True
    authoritative_source: str = Field(..., max_length=128)
    canonical_table_name: str = Field(..., max_length=128)
    canonical_id_column: str = Field("id", max_length=64)
    is_active: bool = True


class MasterDataDefinitionUpdate(BaseModel):
    display_name: str | None = None
    description: str | None = None
    steward_role: str | None = None
    sensitivity: MasterDataSensitivity | None = None
    duplicate_detection_enabled: bool | None = None
    merge_supported: bool | None = None
    archival_supported: bool | None = None
    is_active: bool | None = None


# =============================================================================
# 2. REFERENCE DATA DEFINITIONS & VALUES
# =============================================================================


class ReferenceDataDefinitionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    category: str
    name: str
    description: str | None = None
    is_system: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None


class ReferenceDataDefinitionCreate(BaseModel):
    category: str = Field(..., max_length=64, description="Unique reference category identifier")
    name: str = Field(..., max_length=128)
    description: str | None = None
    is_system: bool = False
    is_active: bool = True


class ReferenceDataValueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    category: str
    code: str
    label: str
    description: str | None = None
    display_order: int
    metadata_json: dict[str, Any] | None = None
    effective_from: datetime | None = None
    effective_until: datetime | None = None
    is_active: bool
    is_system: bool
    created_at: datetime
    updated_at: datetime | None = None


class ReferenceDataValueCreate(BaseModel):
    category: str = Field(..., max_length=64)
    code: str = Field(..., max_length=64, description="Machine-readable code")
    label: str = Field(..., max_length=128, description="User-facing display label")
    description: str | None = None
    display_order: int = 0
    metadata_json: dict[str, Any] | None = None
    effective_from: datetime | None = None
    effective_until: datetime | None = None
    is_active: bool = True


class ReferenceDataValueUpdate(BaseModel):
    label: str | None = None
    description: str | None = None
    display_order: int | None = None
    metadata_json: dict[str, Any] | None = None
    effective_from: datetime | None = None
    effective_until: datetime | None = None
    is_active: bool | None = None


# =============================================================================
# 3. DATA QUALITY RULES & VALIDATION
# =============================================================================


class DataQualityRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    master_type: str
    rule_key: str
    name: str
    description: str | None = None
    field_name: str | None = None
    rule_type: QualityRuleType
    severity: QualitySeverity
    parameters_json: dict[str, Any] | None = None
    weight: float
    is_active: bool
    version: int
    created_at: datetime
    updated_at: datetime | None = None


class DataQualityRuleCreate(BaseModel):
    master_type: str = Field(..., description="Master data category (e.g. STUDENT, DEPARTMENT)")
    rule_key: str = Field(..., max_length=128, description="Unique rule identifier")
    name: str = Field(..., max_length=255)
    description: str | None = None
    field_name: str | None = None
    rule_type: QualityRuleType = QualityRuleType.REQUIRED
    severity: QualitySeverity = QualitySeverity.ERROR
    parameters_json: dict[str, Any] | None = None
    weight: float = 1.0
    is_active: bool = True


class DataQualityRuleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    field_name: str | None = None
    severity: QualitySeverity | None = None
    parameters_json: dict[str, Any] | None = None
    weight: float | None = None
    is_active: bool | None = None


class DataQualityValidateRequest(BaseModel):
    master_type: str = Field(..., description="Master data category to validate against")
    record_id: UUID | None = Field(None, description="Optional record UUID if inspecting existing")
    payload: dict[str, Any] = Field(..., description="Record fields and values to evaluate")


class RuleEvaluationItem(BaseModel):
    rule_key: str
    rule_name: str
    rule_type: str
    severity: str
    field_name: str | None = None
    passed: bool
    weight: float
    message: str | None = None


class DataQualityValidateResponse(BaseModel):
    master_type: str
    overall_score: float = Field(..., description="Calculated data quality score (0.0 to 100.0)")
    dimension_scores: dict[str, float] = Field(
        ...,
        description="Dimension scores: completeness, validity, consistency, uniqueness, timeliness",
    )
    passed_rules_count: int
    failed_rules_count: int
    rule_evaluations: list[RuleEvaluationItem]


class DataQualityRecalculateRequest(BaseModel):
    master_type: str = Field(..., description="Master data type to recalculate scores for")
    limit: int = Field(100, ge=1, le=1000, description="Batch limit for records to evaluate")


# =============================================================================
# 4. DATA QUALITY RESULTS & ISSUES
# =============================================================================


class DataQualityResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    master_type: str
    record_id: UUID
    overall_score: float
    dimension_scores_json: dict[str, Any]
    rule_results_json: list[dict[str, Any]]
    evaluated_at: datetime


class DataQualityIssueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    master_type: str
    record_id: UUID
    rule_id: UUID | None = None
    rule_key: str
    severity: QualitySeverity
    status: QualityIssueStatus
    issue_message: str
    field_name: str | None = None
    detected_at: datetime
    assigned_to: UUID | None = None
    resolved_at: datetime | None = None
    resolution_notes: str | None = None


class DataQualityIssueUpdate(BaseModel):
    status: QualityIssueStatus | None = None
    assigned_to: UUID | None = None
    resolution_notes: str | None = None


class DataQualitySummaryResponse(BaseModel):
    total_governed_records: int
    records_with_critical_issues: int
    records_with_errors: int
    records_with_warnings: int
    open_quality_issues: int
    open_issues_count: int = 0
    resolved_quality_issues: int
    pending_duplicate_candidates: int
    duplicate_candidates_count: int = 0
    average_quality_score: float
    dimension_averages: dict[str, float]
    breakdown_by_master_type: dict[str, dict[str, Any]]


# =============================================================================
# 5. DUPLICATE CANDIDATES & MATCHING
# =============================================================================


class DuplicateDetectRequest(BaseModel):
    master_type: str = Field(..., description="Master data category to run detection on")
    limit: int = Field(50, ge=1, le=500, description="Max candidate pairs to discover")


class DuplicateCandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    master_type: str
    record_a_id: UUID
    record_b_id: UUID
    match_score: float
    match_reasons: list[str]
    status: DuplicateStatus
    reviewed_by: UUID | None = None
    reviewed_at: datetime | None = None
    review_notes: str | None = None
    created_at: datetime
    record_a_summary: dict[str, Any] | None = None
    record_b_summary: dict[str, Any] | None = None


class DuplicateCandidateReviewRequest(BaseModel):
    status: DuplicateStatus = Field(
        ...,
        description="Resolution status: CONFIRMED_DUPLICATE, NOT_DUPLICATE, or DISMISSED",
    )
    notes: str | None = None
    review_notes: str | None = None


# =============================================================================
# 6. MERGE OPERATIONS & SURVIVORSHIP
# =============================================================================


class MasterDataMergeRequest(BaseModel):
    master_type: str = Field(..., description="Master data type (STUDENT, COMPANY, DEPARTMENT)")
    survivor_record_id: UUID = Field(..., description="Canonical record that will survive")
    merged_record_id: UUID = Field(..., description="Duplicate record to be merged and deactivated")
    survivorship_rule: SurvivorshipRule = Field(
        SurvivorshipRule.KEEP_CANONICAL,
        description="Survivorship rule for attributes",
    )
    field_decisions: dict[str, Any] | None = Field(
        None,
        description="Field level overrides when using EXPLICIT_FIELD_SELECTION",
    )
    reason: str = Field(..., min_length=5, description="Auditable justification for merge")


class MasterDataMergeResponse(BaseModel):
    operation_id: UUID
    tenant_id: UUID
    master_type: str
    survivor_record_id: UUID
    merged_record_id: UUID
    survivorship_rule: str
    reassigned_counts: dict[str, int]
    status: str
    is_reversible: bool
    created_at: datetime


class MasterDataMergeRollbackRequest(BaseModel):
    reason: str = Field(..., min_length=5, description="Auditable justification for rollback")


# =============================================================================
# 7. MASTER DATA LINEAGE & CORRECTIONS
# =============================================================================


class MasterDataLineageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    master_type: str
    record_id: UUID
    source: LineageSource
    source_record_id: str | None = None
    imported_at: datetime | None = None
    last_verified_at: datetime | None = None
    modified_by: UUID | None = None
    modification_source: str | None = None
    details_json: dict[str, Any] | None = None
    created_at: datetime


class MasterDataLineageCreate(BaseModel):
    master_type: str
    record_id: UUID
    source: LineageSource = LineageSource.MANUAL
    source_record_id: str | None = None
    imported_at: datetime | None = None
    last_verified_at: datetime | None = None
    modification_source: str | None = None
    details_json: dict[str, Any] | None = None


class MasterDataCorrectionCreate(BaseModel):
    master_type: str = Field(..., description="Master data category")
    record_id: UUID = Field(..., description="Target record UUID")
    field_name: str = Field(..., max_length=64, description="Attribute name to correct")
    proposed_value: str = Field(..., description="Proposed corrected value")
    reason: str = Field(..., min_length=5, description="Business justification")


class MasterDataCorrectionReviewRequest(BaseModel):
    decision: CorrectionStatus = Field(
        ...,
        description="APPROVED or REJECTED",
    )
    notes: str | None = None


class MasterDataCorrectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    master_type: str
    record_id: UUID
    field_name: str
    old_value: str | None = None
    proposed_value: str
    reason: str
    status: CorrectionStatus
    requester_id: UUID | None = None
    reviewer_id: UUID | None = None
    reviewed_at: datetime | None = None
    rejection_reason: str | None = None
    applied_at: datetime | None = None
    created_at: datetime
