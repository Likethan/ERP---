"""Pydantic v2 schemas for Enterprise Institutional Knowledge Base & Policy Library (Step 42)."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.knowledge import (
    KnowledgeConfidentiality,
    KnowledgeRelationshipType,
    KnowledgeReviewDecision,
    KnowledgeScopeType,
)

# =============================================================================
# BASE CONFIG
# =============================================================================


class KnowledgeBaseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
        str_strip_whitespace=True,
    )


# =============================================================================
# CATEGORY SCHEMAS
# =============================================================================


class KnowledgeCategoryBase(KnowledgeBaseSchema):
    code: str = Field(..., max_length=64)
    name: str = Field(..., max_length=128)
    description: str | None = None
    is_system: bool = False
    requires_approval: bool = True
    requires_attestation: bool = False
    default_review_months: int = Field(default=12, ge=1, le=120)
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class KnowledgeCategoryCreate(KnowledgeCategoryBase):
    pass


class KnowledgeCategoryUpdate(KnowledgeBaseSchema):
    name: str | None = Field(None, max_length=128)
    description: str | None = None
    requires_approval: bool | None = None
    requires_attestation: bool | None = None
    default_review_months: int | None = Field(None, ge=1, le=120)
    metadata_json: dict[str, Any] | None = None


class KnowledgeCategoryResponse(KnowledgeCategoryBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime


# =============================================================================
# CONTENT & DRAFT SCHEMAS
# =============================================================================


class KnowledgeSection(KnowledgeBaseSchema):
    id: str = Field(..., max_length=64)
    title: str = Field(..., max_length=256)
    level: int = Field(default=1, ge=1, le=6)
    content: str = ""
    order: int = Field(default=0, ge=0)


class KnowledgeItemDraftUpdate(KnowledgeBaseSchema):
    title: str | None = Field(None, max_length=256)
    summary: str | None = None
    draft_content_markdown: str | None = None
    draft_sections_json: list[KnowledgeSection] | None = None
    tags: list[str] | None = None
    document_attachment_ids: list[str] | None = None
    lock_version: int = Field(..., description="Optimistic concurrency control token")
    change_summary: str | None = None


class KnowledgeDraftValidationResult(KnowledgeBaseSchema):
    is_valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    word_count: int = 0
    sections_count: int = 0
    sanitized_preview_html: str = ""


# =============================================================================
# KNOWLEDGE ITEM SCHEMAS
# =============================================================================


class KnowledgeItemCreate(KnowledgeBaseSchema):
    item_code: str = Field(..., max_length=64, description="Unique institutional identifier (e.g. POL-ACAD-001)")
    title: str = Field(..., max_length=256)
    summary: str
    category_code: str = Field(..., max_length=64)
    scope_type: KnowledgeScopeType = KnowledgeScopeType.INSTITUTION
    visibility_role: str | None = Field(None, max_length=64)
    confidentiality: KnowledgeConfidentiality = KnowledgeConfidentiality.INTERNAL_ONLY
    campus_id: UUID | None = None
    department_id: UUID | None = None
    responsible_reviewer_id: UUID | None = None
    draft_content_markdown: str = ""
    draft_sections_json: list[KnowledgeSection] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    document_attachment_ids: list[str] = Field(default_factory=list)
    effective_from: datetime | None = None
    effective_until: datetime | None = None
    review_by_date: datetime | None = None
    requires_acknowledgement: bool = False
    change_summary: str | None = None


class KnowledgeItemMetadataUpdate(KnowledgeBaseSchema):
    title: str | None = Field(None, max_length=256)
    summary: str | None = None
    category_code: str | None = Field(None, max_length=64)
    scope_type: KnowledgeScopeType | None = None
    visibility_role: str | None = Field(None, max_length=64)
    confidentiality: KnowledgeConfidentiality | None = None
    campus_id: UUID | None = None
    department_id: UUID | None = None
    responsible_reviewer_id: UUID | None = None
    owner_user_id: UUID | None = None
    effective_from: datetime | None = None
    effective_until: datetime | None = None
    review_by_date: datetime | None = None
    requires_acknowledgement: bool | None = None


class KnowledgeItemVersionSummary(KnowledgeBaseSchema):
    id: UUID
    version_number: int
    title: str
    summary: str
    published_at: datetime
    effective_from: datetime
    effective_until: datetime | None = None
    author_user_id: UUID
    published_by_user_id: UUID
    change_summary: str | None = None


class KnowledgeReviewStageResponse(KnowledgeBaseSchema):
    id: UUID
    item_id: UUID
    version_number: int
    stage_order: int
    stage_name: str
    reviewer_user_id: UUID | None = None
    reviewer_role: str | None = None
    status: str
    comments: str | None = None
    reviewed_at: datetime | None = None
    created_at: datetime


class KnowledgeItemResponse(KnowledgeBaseSchema):
    id: UUID
    tenant_id: UUID
    item_code: str
    title: str
    summary: str
    category_id: UUID
    category_code: str
    owner_user_id: UUID
    responsible_reviewer_id: UUID | None = None
    last_edited_by_user_id: UUID | None = None
    campus_id: UUID | None = None
    department_id: UUID | None = None
    scope_type: str
    visibility_role: str | None = None
    confidentiality: str
    status: str
    current_version_number: int
    current_version_id: UUID | None = None
    lock_version: int
    draft_content_markdown: str
    draft_sections_json: list[dict[str, Any]]
    tags: list[str]
    document_attachment_ids: list[str]
    change_summary: str | None = None
    effective_from: datetime | None = None
    effective_until: datetime | None = None
    review_by_date: datetime | None = None
    published_at: datetime | None = None
    superseded_at: datetime | None = None
    superseded_by_item_id: UUID | None = None
    requires_acknowledgement: bool
    search_indexed_at: datetime | None = None
    search_index_status: str
    created_at: datetime
    updated_at: datetime
    versions: list[KnowledgeItemVersionSummary] = Field(default_factory=list)
    review_stages: list[KnowledgeReviewStageResponse] = Field(default_factory=list)


class KnowledgeItemVersionDetail(KnowledgeBaseSchema):
    id: UUID
    tenant_id: UUID
    item_id: UUID
    version_number: int
    title: str
    summary: str
    content_markdown: str
    sections_json: list[dict[str, Any]]
    metadata_snapshot: dict[str, Any]
    tags: list[str]
    document_attachment_ids: list[str]
    author_user_id: UUID
    reviewer_user_id: UUID | None = None
    approval_decision: str
    approved_at: datetime | None = None
    published_by_user_id: UUID
    published_at: datetime
    effective_from: datetime
    effective_until: datetime | None = None
    change_summary: str | None = None
    supersedes_version_id: UUID | None = None
    created_at: datetime


# =============================================================================
# WORKFLOW SCHEMAS
# =============================================================================


class KnowledgeReviewSubmitRequest(KnowledgeBaseSchema):
    change_summary: str = Field(..., min_length=5, description="Rationale for changes")
    reviewer_user_ids: list[UUID] | None = None


class KnowledgeReviewActionRequest(KnowledgeBaseSchema):
    decision: KnowledgeReviewDecision = Field(
        ..., description="Review outcome: APPROVED, CHANGES_REQUESTED, or REJECTED"
    )
    comments: str = Field(..., min_length=3, description="Review feedback or rejection explanation")


class KnowledgePublishRequest(KnowledgeBaseSchema):
    effective_from: datetime | None = None
    effective_until: datetime | None = None
    review_by_date: datetime | None = None
    change_summary: str | None = None
    supersedes_item_id: UUID | None = None


class KnowledgeSchedulePublicationRequest(KnowledgeBaseSchema):
    scheduled_publish_at: datetime = Field(..., description="Future UTC datetime when publication triggers")
    effective_from: datetime
    effective_until: datetime | None = None
    review_by_date: datetime | None = None
    change_summary: str | None = None


class KnowledgeRetireRequest(KnowledgeBaseSchema):
    reason: str = Field(..., min_length=5)
    superseded_by_item_id: UUID | None = None


# =============================================================================
# RELATIONSHIP SCHEMAS
# =============================================================================


class KnowledgeRelationshipCreate(KnowledgeBaseSchema):
    target_item_id: UUID
    relationship_type: KnowledgeRelationshipType
    description: str | None = Field(None, max_length=256)


class KnowledgeRelationshipResponse(KnowledgeBaseSchema):
    id: UUID
    tenant_id: UUID
    source_item_id: UUID
    target_item_id: UUID
    relationship_type: str
    description: str | None = None
    created_at: datetime


# =============================================================================
# ACKNOWLEDGEMENT & ATTESTATION SCHEMAS
# =============================================================================


class KnowledgeAcknowledgementRequirementCreate(KnowledgeBaseSchema):
    version_number: int = Field(..., ge=1)
    target_role: str | None = Field(None, max_length=64)
    target_department_id: UUID | None = None
    target_campus_id: UUID | None = None
    deadline_days: int = Field(default=30, ge=1, le=365)
    is_mandatory: bool = True
    statement_prompt: str = Field(
        default="I have read, understood, and agree to abide by this institutional policy and its requirements."
    )


class KnowledgeAcknowledgementRequirementResponse(KnowledgeBaseSchema):
    id: UUID
    tenant_id: UUID
    item_id: UUID
    version_number: int
    target_role: str | None = None
    target_department_id: UUID | None = None
    target_campus_id: UUID | None = None
    deadline_days: int
    is_mandatory: bool
    statement_prompt: str
    created_at: datetime


class KnowledgeUserAcknowledgementCreate(KnowledgeBaseSchema):
    version_number: int = Field(..., ge=1)
    statement_confirmed: str = Field(..., min_length=10)


class KnowledgeUserAcknowledgementResponse(KnowledgeBaseSchema):
    id: UUID
    tenant_id: UUID
    item_id: UUID
    version_number: int
    user_id: UUID
    acknowledged_at: datetime
    ip_address: str
    user_agent: str | None = None
    statement_confirmed: str


class KnowledgeAttestationComplianceReport(KnowledgeBaseSchema):
    item_id: UUID
    item_code: str
    item_title: str
    version_number: int
    is_mandatory: bool
    deadline_days: int
    total_required: int
    total_acknowledged: int
    compliance_percentage: float
    acknowledged_users: list[dict[str, Any]] = Field(default_factory=list)


# =============================================================================
# SEARCH & GOVERNANCE SCHEMAS
# =============================================================================


class KnowledgeSearchFilter(KnowledgeBaseSchema):
    query: str | None = None
    category_codes: list[str] | None = None
    scope_types: list[str] | None = None
    statuses: list[str] | None = None
    campus_id: UUID | None = None
    department_id: UUID | None = None
    tags: list[str] | None = None
    effective_as_of: datetime | None = None
    requires_acknowledgement: bool | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class KnowledgeSearchResultItem(KnowledgeBaseSchema):
    id: UUID
    item_code: str
    title: str
    summary: str
    category_code: str
    scope_type: str
    confidentiality: str
    status: str
    current_version_number: int
    effective_from: datetime | None = None
    effective_until: datetime | None = None
    review_by_date: datetime | None = None
    tags: list[str] = Field(default_factory=list)
    snippet: str = ""
    match_score: float = 1.0


class KnowledgeSearchResponse(KnowledgeBaseSchema):
    items: list[KnowledgeSearchResultItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class KnowledgeGovernanceSummary(KnowledgeBaseSchema):
    total_items: int
    published_count: int
    in_review_count: int
    draft_count: int
    superseded_count: int
    retired_count: int
    overdue_reviews_count: int
    expiring_soon_count: int
    mandatory_attestation_items_count: int
