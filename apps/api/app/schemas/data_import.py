"""Pydantic DTO Schemas for Enterprise Data Import, Bulk Migration & Reconciliation (Step 40)."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ImportBaseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


# -----------------------------------------------------------------------------
# 1. Template Schemas
# -----------------------------------------------------------------------------


class ImportTemplateResponse(ImportBaseSchema):
    id: UUID
    code: str
    name: str
    target_domain: str
    target_entity: str
    description: str | None = None
    version: int
    required_fields: list[str]
    optional_fields: list[str]
    field_definitions: dict[str, Any]
    supported_matching_keys: list[str]
    supported_policies: list[str]
    requires_approval_threshold: int
    is_system_template: bool
    is_active: bool
    created_at: datetime


# -----------------------------------------------------------------------------
# 2. Job Creation & Update Schemas
# -----------------------------------------------------------------------------


class ImportJobCreateRequest(ImportBaseSchema):
    template_code: str = Field(..., min_length=2, max_length=64)
    name: str = Field(..., min_length=2, max_length=255)
    execution_policy: str = Field(default="CREATE_NEW")
    matching_key: str | None = Field(default=None, max_length=64)


class ImportMappingUpdateRequest(ImportBaseSchema):
    column_mappings: dict[str, str] = Field(..., description="Map source file header to target field")
    transformations: dict[str, Any] = Field(default_factory=dict, description="Field transformation rules")
    default_values: dict[str, Any] = Field(default_factory=dict, description="Default fallbacks for missing values")


class ImportMappingResponse(ImportBaseSchema):
    id: UUID
    job_id: UUID
    template_code: str
    version: int
    column_mappings: dict[str, str]
    transformations: dict[str, Any]
    default_values: dict[str, Any]
    is_validated: bool


class ImportJobResponse(ImportBaseSchema):
    id: UUID
    tenant_id: UUID
    template_id: UUID | None = None
    template_code: str
    name: str
    target_domain: str
    target_entity: str
    status: str
    execution_policy: str
    matching_key: str | None = None
    source_filename: str | None = None
    source_file_checksum: str | None = None
    source_file_size_bytes: int
    source_file_format: str | None = None
    source_record_count: int
    valid_record_count: int
    error_record_count: int
    warning_record_count: int
    processed_record_count: int
    created_record_count: int
    updated_record_count: int
    skipped_record_count: int
    failed_record_count: int
    last_processed_row: int
    requires_approval: bool
    approved_by_id: UUID | None = None
    approved_at: datetime | None = None
    approval_notes: str | None = None
    rejection_reason: str | None = None
    created_by_id: UUID
    started_at: datetime | None = None
    completed_at: datetime | None = None
    last_error_summary: str | None = None
    reconciliation_status: str
    reconciliation_diff_count: int
    reconciliation_summary: dict[str, Any]
    created_at: datetime
    updated_at: datetime


# -----------------------------------------------------------------------------
# 3. Validation & Preview Schemas
# -----------------------------------------------------------------------------


class ImportValidationSummary(ImportBaseSchema):
    job_id: UUID
    status: str
    total_records: int
    valid_records: int
    error_records: int
    warning_records: int
    errors_by_field: dict[str, int]
    sample_errors: list[dict[str, Any]]
    can_execute: bool
    requires_approval: bool


class ImportPreviewResponse(ImportBaseSchema):
    job_id: UUID
    execution_policy: str
    matching_key: str | None = None
    total_source_records: int
    records_to_create: int
    records_to_update: int
    records_to_skip: int
    records_with_warnings: int
    records_blocking_execution: int
    potential_duplicate_matches: int
    high_impact_summary: list[str]
    sample_transformed_records: list[dict[str, Any]]


# -----------------------------------------------------------------------------
# 4. Approval & Execution Schemas
# -----------------------------------------------------------------------------


class ImportApprovalRequest(ImportBaseSchema):
    approved: bool
    notes: str | None = None
    rejection_reason: str | None = None


class ImportExecutionRequest(ImportBaseSchema):
    batch_size: int = Field(default=50, ge=1, le=500)
    stop_on_first_error: bool = Field(default=False)


class ImportConflictResolutionRequest(ImportBaseSchema):
    resolution: str = Field(..., description="Action: SKIP, OVERWRITE, SELECT_EXISTING")
    notes: str | None = None


# -----------------------------------------------------------------------------
# 5. Conflict & Record Outcomes
# -----------------------------------------------------------------------------


class ImportConflictResponse(ImportBaseSchema):
    id: UUID
    job_id: UUID
    row_number: int
    matching_key: str
    matching_value: str
    existing_entity_id: UUID | None = None
    conflict_type: str
    source_payload: dict[str, Any]
    existing_payload: dict[str, Any]
    discrepancies_json: dict[str, Any]
    resolution: str
    resolved_by_id: UUID | None = None
    resolved_at: datetime | None = None


class ImportRecordResultResponse(ImportBaseSchema):
    id: UUID
    job_id: UUID
    row_number: int
    matching_key_value: str | None = None
    status: str
    target_entity_id: UUID | None = None
    source_data_json: dict[str, Any]
    transformed_data_json: dict[str, Any]
    errors_json: list[dict[str, Any]]
    warnings_json: list[dict[str, Any]]
    executed_at: datetime | None = None


class ImportReconciliationResponse(ImportBaseSchema):
    job_id: UUID
    reconciliation_status: str
    source_record_count: int
    valid_record_count: int
    created_record_count: int
    updated_record_count: int
    skipped_record_count: int
    failed_record_count: int
    unaccounted_difference: int
    is_balanced: bool = True
    discrepancy_details: list[dict[str, Any]] | dict[str, Any] = Field(default_factory=dict)
