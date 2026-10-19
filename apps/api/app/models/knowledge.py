"""Enterprise Institutional Knowledge Base, Policy Library & Controlled Knowledge Management Models for CampusOS (Step 42).

Provides multi-tenant relational persistence for:
- Standard and institutional Knowledge Categories across academic, operational, and statutory domains
- Institutional Knowledge Items with draft management, optimistic concurrency, and controlled visibility
- Immutable published Knowledge Item Versions capturing cryptographic snapshots and approvals
- Multi-stage Review Stages enforcing separation of duties and auditable feedback
- Directed Knowledge Relationships (supersedes, implements, references, depends_on, announces)
- Exact-version Policy Attestations / Acknowledgements with audience scoping and compliance auditing
- Scheduled Knowledge Reviews and expiration/review monitoring
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantScopedModel

# Cross-dialect JSONB compatibility
JSONB_COMPAT = JSONB


# =============================================================================
# ENUMS & DOMAIN CONSTANTS
# =============================================================================


class KnowledgeCategoryCode(StrEnum):
    INSTITUTIONAL_POLICY = "INSTITUTIONAL_POLICY"
    ACADEMIC_REGULATION = "ACADEMIC_REGULATION"
    STANDARD_OPERATING_PROCEDURE = "STANDARD_OPERATING_PROCEDURE"
    STUDENT_HANDBOOK = "STUDENT_HANDBOOK"
    FACULTY_HANDBOOK = "FACULTY_HANDBOOK"
    DEPARTMENT_GUIDELINE = "DEPARTMENT_GUIDELINE"
    ADMIN_PROCEDURE = "ADMIN_PROCEDURE"
    FINANCE_PROCUREMENT = "FINANCE_PROCUREMENT"
    HR_POLICY = "HR_POLICY"
    CAMPUS_SAFETY = "CAMPUS_SAFETY"
    IT_SECURITY = "IT_SECURITY"
    CIRCULAR_NOTICE = "CIRCULAR_NOTICE"
    ACCREDITATION_QA = "ACCREDITATION_QA"
    TECHNICAL_MANUAL = "TECHNICAL_MANUAL"


class KnowledgeItemStatus(StrEnum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    IN_REVIEW = "IN_REVIEW"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    APPROVED = "APPROVED"
    SCHEDULED = "SCHEDULED"
    PUBLISHED = "PUBLISHED"
    SUPERSEDED = "SUPERSEDED"
    RETIRED = "RETIRED"


class KnowledgeScopeType(StrEnum):
    INSTITUTION = "INSTITUTION"
    CAMPUS = "CAMPUS"
    DEPARTMENT = "DEPARTMENT"
    ROLE = "ROLE"
    RESTRICTED = "RESTRICTED"


class KnowledgeConfidentiality(StrEnum):
    PUBLIC_INSTITUTION = "PUBLIC_INSTITUTION"
    INTERNAL_ONLY = "INTERNAL_ONLY"
    CONFIDENTIAL_ADMIN = "CONFIDENTIAL_ADMIN"
    RESTRICTED = "RESTRICTED"


class KnowledgeRelationshipType(StrEnum):
    SUPERSEDES = "SUPERSEDES"
    IMPLEMENTS = "IMPLEMENTS"
    REFERENCES = "REFERENCES"
    DEPENDS_ON = "DEPENDS_ON"
    ANNOUNCES = "ANNOUNCES"
    REQUIRES_ACKNOWLEDGEMENT = "REQUIRES_ACKNOWLEDGEMENT"


class KnowledgeReviewDecision(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    REJECTED = "REJECTED"


class KnowledgeReviewScheduleType(StrEnum):
    ANNUAL_REVIEW = "ANNUAL_REVIEW"
    EXPIRATION_CHECK = "EXPIRATION_CHECK"
    ACKNOWLEDGEMENT_REMINDER = "ACKNOWLEDGEMENT_REMINDER"


class KnowledgeReviewScheduleStatus(StrEnum):
    PENDING = "PENDING"
    NOTIFIED = "NOTIFIED"
    OVERDUE = "OVERDUE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


# =============================================================================
# MODELS
# =============================================================================


class KnowledgeCategory(TenantScopedModel):
    """Institutional Knowledge Category classifying policies, SOPs, handbooks, etc."""

    __tablename__ = "knowledge_categories"

    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    requires_attestation: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    default_review_months: Mapped[int] = mapped_column(Integer, default=12, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB_COMPAT, default=dict, server_default="{}", nullable=False
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_knowledge_cat_tenant_code"),
        Index("ix_knowledge_cat_tenant_code", "tenant_id", "code"),
    )


class KnowledgeItem(TenantScopedModel):
    """Authoritative Knowledge Item representing an institutional policy, SOP, or manual."""

    __tablename__ = "knowledge_items"

    item_code: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    category_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("knowledge_categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    category_code: Mapped[str] = mapped_column(String(64), nullable=False)

    owner_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    responsible_reviewer_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    last_edited_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    scope_type: Mapped[str] = mapped_column(
        String(32), default=KnowledgeScopeType.INSTITUTION.value, nullable=False
    )
    visibility_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    confidentiality: Mapped[str] = mapped_column(
        String(32), default=KnowledgeConfidentiality.INTERNAL_ONLY.value, nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(32), default=KnowledgeItemStatus.DRAFT.value, nullable=False, index=True
    )
    current_version_number: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_version_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )
    lock_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Working Draft Content
    draft_content_markdown: Mapped[str] = mapped_column(Text, default="", nullable=False)
    draft_sections_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB_COMPAT, default=list, server_default="[]", nullable=False
    )
    tags: Mapped[list[str]] = mapped_column(
        JSONB_COMPAT, default=list, server_default="[]", nullable=False
    )
    document_attachment_ids: Mapped[list[str]] = mapped_column(
        JSONB_COMPAT, default=list, server_default="[]", nullable=False
    )
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Validity & Review
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    effective_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_by_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    superseded_by_item_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("knowledge_items.id", ondelete="SET NULL"),
        nullable=True,
    )

    requires_acknowledgement: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Search & Indexing
    search_indexed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    search_index_status: Mapped[str] = mapped_column(
        String(32), default="PENDING", nullable=False
    )

    # Relationships
    category: Mapped["KnowledgeCategory"] = relationship("KnowledgeCategory")
    owner: Mapped[Any] = relationship("User", foreign_keys=[owner_user_id])
    versions: Mapped[list["KnowledgeItemVersion"]] = relationship(
        "KnowledgeItemVersion",
        back_populates="item",
        cascade="all, delete-orphan",
        order_by="desc(KnowledgeItemVersion.version_number)",
        foreign_keys="KnowledgeItemVersion.item_id",
    )
    review_stages: Mapped[list["KnowledgeReviewStage"]] = relationship(
        "KnowledgeReviewStage",
        back_populates="item",
        cascade="all, delete-orphan",
        order_by="KnowledgeReviewStage.stage_order",
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "item_code", name="uq_knowledge_item_tenant_code"),
        Index("ix_knowledge_item_tenant_status", "tenant_id", "status"),
        Index("ix_knowledge_item_tenant_scope", "tenant_id", "scope_type"),
        Index("ix_knowledge_item_tenant_review", "tenant_id", "review_by_date"),
    )


class KnowledgeItemVersion(TenantScopedModel):
    """Immutable published snapshot of a Knowledge Item."""

    __tablename__ = "knowledge_item_versions"

    item_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("knowledge_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    sections_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB_COMPAT, default=list, server_default="[]", nullable=False
    )
    metadata_snapshot: Mapped[dict[str, Any]] = mapped_column(
        JSONB_COMPAT, default=dict, server_default="{}", nullable=False
    )
    tags: Mapped[list[str]] = mapped_column(
        JSONB_COMPAT, default=list, server_default="[]", nullable=False
    )
    document_attachment_ids: Mapped[list[str]] = mapped_column(
        JSONB_COMPAT, default=list, server_default="[]", nullable=False
    )

    author_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    reviewer_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approval_decision: Mapped[str] = mapped_column(
        String(32), default=KnowledgeReviewDecision.APPROVED.value, nullable=False
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    published_by_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    effective_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    supersedes_version_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("knowledge_item_versions.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    item: Mapped["KnowledgeItem"] = relationship(
        "KnowledgeItem", back_populates="versions", foreign_keys=[item_id]
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "item_id", "version_number", name="uq_knowledge_ver_tenant_item_num"),
        Index("ix_knowledge_ver_tenant_item", "tenant_id", "item_id"),
    )


class KnowledgeReviewStage(TenantScopedModel):
    """Configured or active review stage in a multi-stage approval workflow."""

    __tablename__ = "knowledge_review_stages"

    item_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("knowledge_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    stage_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    stage_name: Mapped[str] = mapped_column(String(64), nullable=False, default="Editorial Review")
    reviewer_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewer_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default=KnowledgeReviewDecision.PENDING.value, nullable=False
    )
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    item: Mapped["KnowledgeItem"] = relationship("KnowledgeItem", back_populates="review_stages")

    __table_args__ = (
        Index("ix_knowledge_stage_item_ver", "tenant_id", "item_id", "version_number"),
    )


class KnowledgeRelationship(TenantScopedModel):
    """Explicit directed relationship between knowledge items."""

    __tablename__ = "knowledge_relationships"

    source_item_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("knowledge_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_item_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("knowledge_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relationship_type: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str | None] = mapped_column(String(256), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "source_item_id",
            "target_item_id",
            "relationship_type",
            name="uq_knowledge_rel_source_target_type",
        ),
        Index("ix_knowledge_rel_tenant_source", "tenant_id", "source_item_id"),
        Index("ix_knowledge_rel_tenant_target", "tenant_id", "target_item_id"),
    )


class KnowledgeAcknowledgementRequirement(TenantScopedModel):
    """Specification of mandatory audience acknowledgement for an item version."""

    __tablename__ = "knowledge_acknowledgement_requirements"

    item_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("knowledge_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    target_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    target_department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    target_campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="SET NULL"),
        nullable=True,
    )
    deadline_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    statement_prompt: Mapped[str] = mapped_column(
        Text,
        default="I have read, understood, and agree to abide by this institutional policy and its requirements.",
        nullable=False,
    )

    __table_args__ = (
        Index("ix_knowledge_ack_req_item_ver", "tenant_id", "item_id", "version_number"),
    )


class KnowledgeUserAcknowledgement(TenantScopedModel):
    """Tamper-evident user attestation against an exact published version."""

    __tablename__ = "knowledge_user_acknowledgements"

    item_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("knowledge_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    acknowledged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    ip_address: Mapped[str] = mapped_column(String(45), default="127.0.0.1", nullable=False)
    user_agent: Mapped[str | None] = mapped_column(String(256), nullable=True)
    statement_confirmed: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "item_id",
            "version_number",
            "user_id",
            name="uq_knowledge_user_ack_exact",
        ),
        Index("ix_knowledge_user_ack_lookup", "tenant_id", "user_id", "item_id"),
    )


class KnowledgeScheduledReview(TenantScopedModel):
    """Scheduled review, reminder, or expiration check on a knowledge item."""

    __tablename__ = "knowledge_scheduled_reviews"

    item_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("knowledge_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    review_type: Mapped[str] = mapped_column(
        String(32), default=KnowledgeReviewScheduleType.ANNUAL_REVIEW.value, nullable=False
    )
    scheduled_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=KnowledgeReviewScheduleStatus.PENDING.value, nullable=False, index=True
    )
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_knowledge_sched_status_date", "tenant_id", "status", "scheduled_date"),
    )
