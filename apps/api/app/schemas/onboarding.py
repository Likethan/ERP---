"""Pydantic DTO Schemas for Step 35: Enterprise Product Readiness, Tenant Acceptance & Go-Live Orchestration.

Enforces zero-trust request validation, explainable readiness reporting, and auditable governance payloads.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# -----------------------------------------------------------------------------
# 1. Onboarding Plan & Lifecycle Schemas
# -----------------------------------------------------------------------------


class OnboardingPlanCreateRequest(BaseModel):
    """Payload to establish an institutional onboarding orchestration plan."""

    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    assigned_lead_email: EmailStr | None = None
    target_go_live_date: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class OnboardingLifecycleTransitionRequest(BaseModel):
    """Guarded state machine transition request for institutional onboarding."""

    model_config = ConfigDict(extra="forbid")

    target_state: str = Field(..., description="Target OnboardingLifecycleState")
    reason: str = Field(..., min_length=5, description="Documented justification for transition")
    correlation_id: UUID | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class OnboardingPlanResponse(BaseModel):
    """Full operational view of an institution's onboarding progress."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    current_state: str
    previous_state: str | None
    target_go_live_date: datetime | None
    actual_go_live_date: datetime | None
    assigned_lead_email: str | None
    state_reason: str | None
    rollback_reason: str | None
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime


# -----------------------------------------------------------------------------
# 2. Readiness Checklist Schemas
# -----------------------------------------------------------------------------


class ChecklistItemUpdateRequest(BaseModel):
    """Payload to update an individual readiness checklist criterion."""

    model_config = ConfigDict(extra="forbid")

    status: str = Field(..., description="ChecklistStatus: PASSED, FAILED, BLOCKED, WAIVED, IN_PROGRESS")
    evidence_ref: str | None = None
    responsible_owner: str | None = None
    blocker_reason: str | None = None
    waiver_reason: str | None = None
    waiver_approved_by: str | None = None


class ChecklistItemResponse(BaseModel):
    """Auditable state of a single readiness checklist criterion."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    plan_id: UUID
    tenant_id: UUID
    item_code: str
    category: str
    title: str
    description: str
    is_required: bool
    verification_method: str
    status: str
    evidence_ref: str | None
    responsible_owner: str | None
    completed_at: datetime | None
    verified_at: datetime | None
    blocker_reason: str | None
    waiver_reason: str | None
    waiver_approved_by: str | None
    created_at: datetime
    updated_at: datetime


class ReadinessEvaluationResponse(BaseModel):
    """Explainable result detailing whether an institution can progress to go-live."""

    overall_status: str  # READY, BLOCKED, ACTION_REQUIRED
    can_progress_to_next_stage: bool
    current_state: str
    next_recommended_state: str | None

    total_checks: int
    passed_checks: int
    failed_checks: int
    blocked_checks: int
    waived_checks: int

    completed_requirements: list[str]
    failed_requirements: list[str]
    blocked_requirements: list[str]
    missing_evidence: list[str]
    outstanding_approvals: list[str]

    blocking_reasons: list[str]
    recommended_actions: list[str]


# -----------------------------------------------------------------------------
# 3. Data Migration & Reconciliation Schemas
# -----------------------------------------------------------------------------


class MigrationValidationRequest(BaseModel):
    """Payload to trigger validation and dry-run reconciliation for a domain file."""

    model_config = ConfigDict(extra="forbid")

    domain_name: str = Field(..., description="STUDENTS, FACULTY, COURSES, or FINANCE")
    source_filename: str = Field(..., min_length=3)
    source_checksum: str = Field(..., min_length=16)
    dry_run: bool = Field(default=True)
    records: list[dict[str, Any]] = Field(default_factory=list, description="Bounded batch of records to validate")


class MigrationJobResponse(BaseModel):
    """Result and reconciliation metrics for a data migration execution."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    plan_id: UUID
    tenant_id: UUID
    domain_name: str
    source_filename: str
    source_checksum: str
    status: str
    source_record_count: int
    accepted_record_count: int
    rejected_record_count: int
    duplicate_record_count: int
    imported_record_count: int
    reconciliation_diff_count: int
    failed_batches_count: int
    unresolved_exceptions_count: int
    dry_run: bool
    validation_findings: list[dict[str, Any]]
    reconciliation_summary: dict[str, Any]
    approved_at: datetime | None
    created_at: datetime
    updated_at: datetime


# -----------------------------------------------------------------------------
# 4. User Acceptance Testing (UAT) Schemas
# -----------------------------------------------------------------------------


class UATScenarioExecuteRequest(BaseModel):
    """Record execution, evidence, and sign-off for a UAT scenario."""

    model_config = ConfigDict(extra="forbid")

    status: str = Field(..., description="UATScenarioStatus: PASSED, FAILED, BLOCKED")
    evidence_ref: str | None = None
    defect_severity: str = Field(default="NONE", description="CRITICAL, MAJOR, MINOR, NONE")
    defect_description: str | None = None
    retest_notes: str | None = None
    sign_off_by: str | None = None


class UATScenarioResponse(BaseModel):
    """Verifiable UAT scenario with status and defect records."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    plan_id: UUID
    tenant_id: UUID
    scenario_code: str
    module: str
    title: str
    expected_outcome: str
    assigned_tester_email: str | None
    status: str
    evidence_ref: str | None
    defect_severity: str
    defect_description: str | None
    retest_notes: str | None
    sign_off_by: str | None
    sign_off_at: datetime | None
    created_at: datetime
    updated_at: datetime


# -----------------------------------------------------------------------------
# 5. Go-Live Approval Governance Schemas
# -----------------------------------------------------------------------------


class OnboardingApprovalRequest(BaseModel):
    """Sign-off decision submitted by an authorized governance reviewer."""

    model_config = ConfigDict(extra="forbid")

    role: str = Field(..., description="ApprovalRole")
    decision: str = Field(..., description="APPROVED or REJECTED")
    comments: str | None = None
    rejection_reason: str | None = None
    policy_version: str = Field(default="1.0")


class OnboardingApprovalResponse(BaseModel):
    """Individual accountable approval decision record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    plan_id: UUID
    tenant_id: UUID
    role: str
    decision: str
    approver_id: UUID | None
    approver_email: str | None
    comments: str | None
    rejection_reason: str | None
    policy_version: str
    decision_at: datetime | None
    invalidated_at: datetime | None
    invalidation_reason: str | None
    created_at: datetime


# -----------------------------------------------------------------------------
# 6. Go-Live Execution & Rollback Schemas
# -----------------------------------------------------------------------------


class GoLiveExecutionRequest(BaseModel):
    """Payload to initiate ordered go-live launch steps."""

    model_config = ConfigDict(extra="forbid")

    is_dry_run: bool = Field(default=False)
    idempotency_key: str = Field(..., min_length=8)


class GoLiveExecutionStepResponse(BaseModel):
    """Individual step execution record within a go-live run."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    plan_id: UUID
    tenant_id: UUID
    execution_run_id: UUID
    step_name: str
    step_order: int
    status: str
    is_dry_run: bool
    idempotency_key: str
    duration_ms: int
    result_summary: dict[str, Any]
    error_message: str | None
    recovery_instruction: str | None
    created_at: datetime


class RollbackExecutionRequest(BaseModel):
    """Authorized recovery action to revert a failed go-live safely."""

    model_config = ConfigDict(extra="forbid")

    rollback_reason: str = Field(..., min_length=10)
    target_state: str = Field(default="ROLLBACK_IN_PROGRESS")
    preserve_imported_data: bool = Field(default=True)


class RollbackExecutionResponse(BaseModel):
    """Summary of safe rollback operations executed."""

    plan_id: UUID
    tenant_id: UUID
    previous_state: str
    current_state: str
    rollback_reason: str
    data_preserved: bool
    manual_recovery_instructions: list[str]
    executed_at: datetime


# -----------------------------------------------------------------------------
# 7. Hypercare Monitoring & Operational Handoff Schemas
# -----------------------------------------------------------------------------


class HypercareStatusResponse(BaseModel):
    """Active telemetry, error counts, and operational health signals."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    plan_id: UUID
    tenant_id: UUID
    hypercare_start_at: datetime
    hypercare_end_at: datetime
    assigned_support_lead: str
    escalation_contacts: list[dict[str, Any]]
    is_active: bool
    daily_summaries: list[dict[str, Any]]
    unresolved_issues_count: int
    auth_failure_count: int
    api_error_count: int
    integration_failure_count: int
    job_failure_count: int
    exit_criteria_met: bool
    handoff_completed_at: datetime | None
    handoff_signoff_by: str | None


class HypercareHandoffRequest(BaseModel):
    """Sign-off payload to transition institution to normal operations."""

    model_config = ConfigDict(extra="forbid")

    signoff_by: str = Field(..., min_length=3)
    notes: str = Field(..., min_length=10)
