"""Pydantic Schemas for Enterprise Data Governance, Privacy & Compliance Layer."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.governance_registry import DataClassificationLevel, MaskingStrategy
from app.models.governance import (
    GovernancePolicyCategory,
    GovernancePolicyStatus,
    PrivacyRequestType,
    RetentionAction,
    RetentionTriggerEvent,
    RetentionUnit,
)

# =============================================================================
# 1. DATA CLASSIFICATION & SENSITIVE FIELDS
# =============================================================================

class SensitiveFieldRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    entity: str
    field: str
    classification: DataClassificationLevel
    masking_strategy: MaskingStrategy
    export_policy: str
    logging_policy: str
    ai_visibility: bool
    allowed_roles: list[str]


class ClassificationTierRead(BaseModel):
    level: DataClassificationLevel
    description: str
    example_entities: list[str]


# =============================================================================
# 2. GOVERNANCE POLICIES & VERSIONS
# =============================================================================

class GovernancePolicyCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=128)
    code: str = Field(..., min_length=2, max_length=64)
    category: str = Field(default=GovernancePolicyCategory.RETENTION)
    description: str | None = None
    status: str = Field(default=GovernancePolicyStatus.ACTIVE)
    initial_rules: dict[str, Any] | list[Any] = Field(default_factory=dict)
    change_summary: str | None = "Initial policy creation"


class GovernancePolicyUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=128)
    description: str | None = None
    status: str | None = None


class GovernancePolicyVersionCreate(BaseModel):
    rules_json: dict[str, Any] | list[Any]
    change_summary: str | None = None
    effective_from: datetime | None = None
    effective_until: datetime | None = None


class GovernancePolicyVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    policy_id: UUID
    version_number: int
    status: str
    rules_json: dict[str, Any] | list[Any]
    change_summary: str | None = None
    effective_from: datetime
    effective_until: datetime | None = None
    is_active: bool
    created_at: datetime


class GovernancePolicyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    code: str
    category: str
    description: str | None = None
    status: str
    is_system_default: bool
    active_version_id: UUID | None = None
    versions: list[GovernancePolicyVersionRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 3. RETENTION POLICIES & EVALUATION
# =============================================================================

class RetentionPolicyCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=128)
    resource_type: str = Field(..., min_length=2, max_length=64)
    retention_period: int = Field(default=5, ge=1)
    retention_unit: str = Field(default=RetentionUnit.YEARS)
    trigger_event: str = Field(default=RetentionTriggerEvent.CREATION)
    action: str = Field(default=RetentionAction.ARCHIVE)
    archive_after_days: int | None = None
    delete_after_days: int | None = None
    legal_hold_behavior: str = Field(default="BLOCK")
    is_active: bool = True
    policy_id: UUID | None = None


class RetentionPolicyUpdate(BaseModel):
    name: str | None = None
    retention_period: int | None = Field(None, ge=1)
    retention_unit: str | None = None
    trigger_event: str | None = None
    action: str | None = None
    archive_after_days: int | None = None
    delete_after_days: int | None = None
    legal_hold_behavior: str | None = None
    is_active: bool | None = None


class RetentionPolicyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    policy_id: UUID | None = None
    name: str
    resource_type: str
    retention_period: int
    retention_unit: str
    trigger_event: str
    action: str
    archive_after_days: int | None = None
    delete_after_days: int | None = None
    legal_hold_behavior: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class RetentionEvaluationRequest(BaseModel):
    resource_type: str
    resource_id: UUID
    record_created_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetentionDecisionRead(BaseModel):
    resource_id: UUID
    resource_type: str
    policy_id: UUID | None = None
    decision: str  # RETAIN, ARCHIVE, ANONYMIZE, DELETE, REVIEW, BLOCKED
    eligible_at: datetime | None = None
    blocked_reason: str | None = None
    is_held: bool = False
    has_dependency_block: bool = False


# =============================================================================
# 4. LEGAL / GOVERNANCE HOLDS
# =============================================================================

class GovernanceHoldCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=128)
    case_reference: str | None = None
    target_entity_type: str = Field(default="ALL")  # STUDENT, FACULTY, DOCUMENT, INVOICE, ALL
    target_entity_id: UUID | None = None
    reason: str = Field(..., min_length=5)
    expires_at: datetime | None = None


class GovernanceHoldRelease(BaseModel):
    release_reason: str = Field(..., min_length=5)


class GovernanceHoldRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    case_reference: str | None = None
    target_entity_type: str
    target_entity_id: UUID | None = None
    reason: str
    status: str
    is_active: bool
    expires_at: datetime | None = None
    created_by_user_id: UUID | None = None
    released_by_user_id: UUID | None = None
    released_at: datetime | None = None
    release_reason: str | None = None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 5. PRIVACY / DATA SUBJECT REQUESTS
# =============================================================================

class PrivacyRequestCreate(BaseModel):
    request_type: str = Field(default=PrivacyRequestType.ACCESS)
    data_subject_type: str = Field(default="STUDENT")
    data_subject_id: UUID
    description: str | None = None
    target_domains: list[str] = Field(default_factory=lambda: ["people", "academics", "attendance", "finance", "documents"])
    payload: dict[str, Any] | None = None


class PrivacyRequestReview(BaseModel):
    status: str = Field(..., description="APPROVED or REJECTED")
    rejection_reason: str | None = None
    evidence_notes: str | None = None


class PrivacyRequestActionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    request_id: UUID
    action_type: str
    domain: str
    entity_type: str
    entity_id: UUID | None = None
    status: str
    blocked_reason: str | None = None
    old_values_json: dict[str, Any] | None = None
    new_values_json: dict[str, Any] | None = None
    performed_at: datetime | None = None


class PrivacyRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    request_number: str
    request_type: str
    status: str
    data_subject_type: str
    data_subject_id: UUID
    requested_by_user_id: UUID
    reviewed_by_user_id: UUID | None = None
    description: str | None = None
    evidence_notes: str | None = None
    rejection_reason: str | None = None
    target_domains_json: list[str] = Field(default_factory=list)
    payload_json: dict[str, Any] | None = None
    export_storage_key: str | None = None
    export_expires_at: datetime | None = None
    completed_at: datetime | None = None
    actions: list[PrivacyRequestActionRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 6. ACCESS REVIEWS
# =============================================================================

class AccessReviewCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=128)
    description: str | None = None
    review_type: str = Field(default="PRIVILEGED_ROLES")
    due_date: datetime


class AccessReviewItemDecide(BaseModel):
    decision: str = Field(..., description="RETAIN, REVOKE, MODIFY, or ESCALATE")
    decision_notes: str | None = None


class AccessReviewItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    review_id: UUID
    user_id: UUID
    role_id: UUID | None = None
    permission_name: str | None = None
    decision: str
    decision_notes: str | None = None
    decided_by_user_id: UUID | None = None
    decided_at: datetime | None = None


class AccessReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    title: str
    description: str | None = None
    review_type: str
    status: str
    due_date: datetime
    reviewer_user_id: UUID | None = None
    completed_at: datetime | None = None
    items: list[AccessReviewItemRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 7. GOVERNANCE SUMMARY
# =============================================================================

class GovernanceSummaryRead(BaseModel):
    tenant_id: UUID
    active_policies_count: int
    active_holds_count: int
    pending_privacy_requests_count: int
    open_access_reviews_count: int
    retention_rules_count: int
    sensitive_fields_count: int
