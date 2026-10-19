"""Pydantic DTO Schemas for Enterprise Records Lifecycle, Retention, Archival & Legal Hold Management (Step 41).

Enforces strict schemas (`extra='forbid'`, `from_attributes=True`) for:
- Record Category definitions & statutory configurations
- Central Records Registry indexing & lifecycle transitions
- Retention Policy specifications, versioning, and rule evaluation
- Archival manifests, cryptographic checksums, and access audit logs
- Legal hold creation, custodian scopes, associations, and releases
- Disposition preview (dry-run), approval workflows, items, and certificates
- Scheduled lifecycle background run telemetry and summaries
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.records_lifecycle import (
    ArchivalStatus,
    DispositionItemStatus,
    DispositionMethod,
    DispositionRequestStatus,
    LegalHoldScope,
    LegalHoldStatus,
    PolicyScope,
    RecordLifecycleState,
    RetentionPolicyStatus,
    RetentionTriggerEvent,
    RetentionUnit,
    ScheduledRunStatus,
    ScheduledRunType,
)


# =============================================================================
# 1. RECORD CATEGORY SCHEMAS
# =============================================================================


class RecordCategoryBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., max_length=64, description="Standard code e.g. STUDENT_ACADEMIC, FINANCE_ACCOUNTING")
    name: str = Field(..., max_length=128, description="Human readable category name")
    description: str | None = Field(None, description="Detailed scope of institutional records")
    confidentiality: str = Field("CONFIDENTIAL", max_length=32, description="PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED, SENSITIVE")
    default_retention_years: int = Field(5, ge=0, le=100, description="Default statutory retention duration in years")
    statutory_authority: str | None = Field(None, max_length=128, description="Regulatory reference e.g. UGC, AICTE, Income Tax Act")
    is_active: bool = Field(True, description="Whether category is available for registration")
    metadata_json: dict[str, Any] | list[Any] | None = Field(default_factory=dict)


class RecordCategoryCreate(RecordCategoryBase):
    pass


class RecordCategoryUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(None, max_length=128)
    description: str | None = None
    confidentiality: str | None = Field(None, max_length=32)
    default_retention_years: int | None = Field(None, ge=0, le=100)
    statutory_authority: str | None = Field(None, max_length=128)
    is_active: bool | None = None
    metadata_json: dict[str, Any] | list[Any] | None = None


class RecordCategoryRead(RecordCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 2. RETENTION POLICY & VERSION SCHEMAS
# =============================================================================


class RetentionPolicyBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., max_length=64, description="Unique policy identifier e.g. POL_STUDENT_TRANSCRIPTS")
    name: str = Field(..., max_length=128, description="Policy title")
    description: str | None = None
    category_code: str = Field(..., max_length=64, description="Target record category code")
    scope: PolicyScope = Field(PolicyScope.CATEGORY, description="GLOBAL, CATEGORY, MODULE, DEPARTMENT")
    scope_target: str | None = Field(None, max_length=128, description="Specific target ID if scope is MODULE or DEPARTMENT")

    retention_duration: int = Field(..., ge=0, description="Duration value (0 if permanent)")
    retention_unit: RetentionUnit = Field(RetentionUnit.YEARS, description="DAYS, MONTHS, YEARS, PERMANENT")
    trigger_event: RetentionTriggerEvent = Field(RetentionTriggerEvent.CREATION, description="CREATION, GRADUATION, TERMINATION, FY_CLOSE, CONTRACT_EXPIRY, CASE_CLOSURE")

    review_required: bool = Field(True, description="Whether administrative review is mandatory before action")
    archive_required: bool = Field(True, description="Whether record must be moved to cold storage prior to disposition")
    disposition_method: DispositionMethod = Field(DispositionMethod.ANONYMIZE, description="SECURE_DELETE, ANONYMIZE, PERMANENT_ARCHIVE, REVIEW_ONLY")
    approval_required: bool = Field(True, description="Whether disposition requires formal sign-off")

    effective_from: datetime | None = None
    effective_until: datetime | None = None
    metadata_json: dict[str, Any] | list[Any] | None = Field(default_factory=dict)


class RetentionPolicyCreate(RetentionPolicyBase):
    pass


class RetentionPolicyUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(None, max_length=128)
    description: str | None = None
    retention_duration: int | None = Field(None, ge=0)
    retention_unit: RetentionUnit | None = None
    trigger_event: RetentionTriggerEvent | None = None
    review_required: bool | None = None
    archive_required: bool | None = None
    disposition_method: DispositionMethod | None = None
    approval_required: bool | None = None
    effective_until: datetime | None = None
    metadata_json: dict[str, Any] | list[Any] | None = None


class RetentionPolicyVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    policy_id: UUID
    version_number: int
    status: RetentionPolicyStatus
    rules_json: dict[str, Any] | list[Any]
    change_summary: str | None = None
    effective_from: datetime
    effective_until: datetime | None = None
    created_by_user_id: UUID | None = None
    created_at: datetime


class RetentionPolicyRead(RetentionPolicyBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    status: RetentionPolicyStatus
    current_version: int
    owner_user_id: UUID | None = None
    approved_by_user_id: UUID | None = None
    approved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    versions: list[RetentionPolicyVersionRead] = Field(default_factory=list)


class RetentionPolicyPublishRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    change_summary: str = Field(..., max_length=255, description="Auditable rationale for publishing this policy version")


# =============================================================================
# 3. RECORDS REGISTRY & LIFECYCLE SCHEMAS
# =============================================================================


class RecordRegistryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category_code: str = Field(..., max_length=64, description="Standard Category Code")
    source_module: str = Field(..., max_length=64, description="Domain e.g. students, faculty, academics, exams, finance, documents, placement")
    source_record_id: UUID = Field(..., description="UUID of domain entity")
    source_reference: str | None = Field(None, max_length=128, description="Institutional natural key e.g. Roll No, Invoice No")
    title: str = Field(..., max_length=255, description="Institutional title of record")
    description: str | None = None
    owner_user_id: UUID | None = None
    owner_department_id: UUID | None = None
    responsible_department: str | None = Field(None, max_length=128)
    confidentiality_level: str = Field("CONFIDENTIAL", max_length=32)
    record_created_at: datetime | None = None
    retention_start_date: datetime | None = None
    storage_reference: str | None = Field(None, max_length=512)
    checksum_sha256: str | None = Field(None, max_length=64)
    metadata_json: dict[str, Any] | list[Any] | None = Field(default_factory=dict)


class RecordLifecycleTransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_state: RecordLifecycleState = Field(..., description="Desired target lifecycle state")
    reason: str = Field(..., max_length=500, description="Formal administrative justification for transition")
    metadata_json: dict[str, Any] | list[Any] | None = Field(default_factory=dict)


class RecordLifecycleHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    record_id: UUID
    from_state: RecordLifecycleState
    to_state: RecordLifecycleState
    trigger_action: str
    reason: str | None = None
    actor_user_id: UUID | None = None
    actor_role: str | None = None
    created_at: datetime
    metadata_json: dict[str, Any] | list[Any] | None = None


class RecordRegistryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    record_number: str
    category_id: UUID | None = None
    category_code: str
    source_module: str
    source_record_id: UUID
    source_reference: str | None = None
    title: str
    description: str | None = None
    owner_user_id: UUID | None = None
    owner_department_id: UUID | None = None
    responsible_department: str | None = None
    confidentiality_level: str
    lifecycle_state: RecordLifecycleState
    policy_id: UUID | None = None
    policy_version: int | None = None
    record_created_at: datetime
    retention_start_date: datetime | None = None
    calculated_review_date: datetime | None = None
    calculated_eligibility_date: datetime | None = None
    archived_at: datetime | None = None
    disposed_at: datetime | None = None
    is_held: bool
    active_hold_count: int
    storage_reference: str | None = None
    checksum_sha256: str | None = None
    metadata_json: dict[str, Any] | list[Any] | None = None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 4. RETENTION EVALUATION SCHEMAS
# =============================================================================


class RetentionEvaluationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    record_id: UUID = Field(..., description="Record Registry ID to evaluate")


class RetentionEvaluationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    record_id: UUID
    record_number: str
    current_state: RecordLifecycleState
    recommended_state: RecordLifecycleState
    is_held: bool
    hold_reasons: list[str] = Field(default_factory=list)
    policy_id: UUID | None = None
    policy_code: str | None = None
    policy_version: int | None = None
    retention_start_date: datetime | None = None
    calculated_eligibility_date: datetime | None = None
    is_eligible_for_disposition: bool
    is_eligible_for_archival: bool
    disposition_method: DispositionMethod | None = None
    has_dependency_block: bool
    dependency_reasons: list[str] = Field(default_factory=list)
    evaluation_summary: str


# =============================================================================
# 5. ARCHIVAL SCHEMAS
# =============================================================================


class RecordArchivalExecuteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    record_id: UUID = Field(..., description="Record Registry ID to archive")
    archive_location: str = Field("S3_COLD_TIER", max_length=128, description="Target cold storage location")
    justification: str = Field(..., max_length=500, description="Archival justification")


class RecordArchivalAccessLogCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    access_type: str = Field(..., description="METADATA_VIEW, FILE_DOWNLOAD, RESTORATION_REQUEST")
    justification: str = Field(..., max_length=500, description="Access justification")


class RecordArchivalAccessLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    manifest_id: UUID
    user_id: UUID
    access_type: str
    justification: str
    ip_address: str | None = None
    accessed_at: datetime


class RecordArchivalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    manifest_number: str
    record_id: UUID
    archive_location: str
    archive_storage_key: str
    original_storage_key: str | None = None
    checksum_sha256: str
    verified_checksum: str | None = None
    file_size_bytes: int
    status: ArchivalStatus
    archived_by_user_id: UUID | None = None
    archived_at: datetime
    retrieval_count: int
    last_retrieved_at: datetime | None = None
    metadata_json: dict[str, Any] | list[Any] | None = None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 6. LEGAL HOLD SCHEMAS
# =============================================================================


class RecordLegalHoldCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., max_length=128, description="Name or title of hold")
    case_reference: str | None = Field(None, max_length=128, description="Court case or audit ticket reference")
    reason: str = Field(..., description="Detailed institutional legal hold rationale")
    hold_authority: str = Field("INSTITUTIONAL_COMPLIANCE", max_length=128)
    scope_type: LegalHoldScope = Field(LegalHoldScope.CATEGORY, description="ALL, CATEGORY, MODULE, DEPARTMENT, SPECIFIC_RECORD")
    scope_value: str | None = Field(None, max_length=128, description="Target category code, department ID, module name, or record ID")
    custodians_json: list[str] | None = Field(default_factory=list, description="List of responsible custodian emails or IDs")
    review_date: datetime | None = None
    metadata_json: dict[str, Any] | list[Any] | None = Field(default_factory=dict)


class RecordLegalHoldReleaseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    release_reason: str = Field(..., max_length=500, description="Formal justification for releasing the hold")


class RecordLegalHoldAssociationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    hold_id: UUID
    record_id: UUID
    status: str
    applied_at: datetime
    applied_by_user_id: UUID | None = None
    released_at: datetime | None = None
    released_by_user_id: UUID | None = None


class RecordLegalHoldRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    hold_number: str
    name: str
    case_reference: str | None = None
    reason: str
    hold_authority: str
    scope_type: LegalHoldScope
    scope_value: str | None = None
    status: LegalHoldStatus
    owner_user_id: UUID | None = None
    custodians_json: list[str] | None = None
    effective_from: datetime
    review_date: datetime | None = None
    released_at: datetime | None = None
    released_by_user_id: UUID | None = None
    release_reason: str | None = None
    records_count: int
    metadata_json: dict[str, Any] | list[Any] | None = None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 7. DISPOSITION SCHEMAS
# =============================================================================


class RecordDispositionPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category_code: str | None = Field(None, description="Optional category filter")
    policy_id: UUID | None = Field(None, description="Optional policy filter")
    as_of_date: datetime | None = None


class RecordDispositionPreviewItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    record_id: UUID
    record_number: str
    title: str
    category_code: str
    current_state: RecordLifecycleState
    calculated_eligibility_date: datetime | None = None
    is_held: bool
    hold_reason: str | None = None
    has_dependency_block: bool
    dependency_reason: str | None = None
    eligible_for_disposition: bool
    recommended_method: DispositionMethod


class RecordDispositionPreviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_records_analyzed: int
    eligible_count: int
    blocked_by_hold_count: int
    blocked_by_dependency_count: int
    records: list[RecordDispositionPreviewItem] = Field(default_factory=list)


class RecordDispositionRequestCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy_id: UUID | None = None
    category_code: str | None = None
    requested_disposition_method: DispositionMethod = Field(DispositionMethod.ANONYMIZE)
    justification: str = Field(..., max_length=1000, description="Formal request justification")
    record_ids: list[UUID] = Field(..., min_length=1, description="List of record registry UUIDs to include")


class RecordDispositionApproveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision_notes: str | None = Field(None, max_length=500)


class RecordDispositionRejectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rejection_reason: str = Field(..., max_length=500, description="Rejection reason")


class RecordDispositionItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    request_id: UUID
    record_id: UUID
    status: DispositionItemStatus
    error_message: str | None = None
    disposed_at: datetime | None = None


class RecordDispositionCertificateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    certificate_number: str
    request_id: UUID
    disposition_method: DispositionMethod
    total_records_destroyed: int
    total_records_anonymized: int
    total_records_archived: int
    disposition_manifest_hash: str
    executed_by_user_id: UUID
    approved_by_user_id: UUID
    executed_at: datetime
    certificate_metadata_json: dict[str, Any] | list[Any] | None = None


class RecordDispositionRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    request_number: str
    policy_id: UUID | None = None
    policy_version: int | None = None
    category_code: str | None = None
    requested_disposition_method: DispositionMethod
    status: DispositionRequestStatus
    records_count: int
    preview_stats_json: dict[str, Any] | None = None
    justification: str
    requested_by_user_id: UUID
    reviewed_by_user_id: UUID | None = None
    reviewed_at: datetime | None = None
    approved_by_user_id: UUID | None = None
    approved_at: datetime | None = None
    rejection_reason: str | None = None
    created_at: datetime
    updated_at: datetime
    certificate: RecordDispositionCertificateRead | None = None


# =============================================================================
# 8. SCHEDULED RUNS & METRICS
# =============================================================================


class ScheduledLifecycleRunTrigger(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_type: ScheduledRunType = Field(ScheduledRunType.ELIGIBILITY_RECALCULATION)
    batch_size: int = Field(100, ge=1, le=500)


class ScheduledLifecycleRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    job_type: ScheduledRunType
    status: ScheduledRunStatus
    records_evaluated: int
    records_transitioned: int
    records_flagged_review: int
    records_blocked: int
    started_at: datetime
    completed_at: datetime | None = None
    summary_json: dict[str, Any] | None = None
    error_message: str | None = None


class RecordLifecycleDashboardSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_records: int
    active_records: int
    retention_pending_records: int
    archived_records: int
    legal_hold_records: int
    disposition_eligible_records: int
    review_required_records: int
    active_holds_count: int
    published_policies_count: int
    pending_disposition_requests_count: int
