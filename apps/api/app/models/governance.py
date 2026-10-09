"""Data Governance, Retention, Legal Holds, and Privacy Domain Models for CampusOS.

Provides multi-tenant relational persistence for:
- Governance Policies & Policy Versions
- Retention Schedules & Evaluator Rules
- Legal / Governance Administrative Holds
- Privacy / Data Subject Requests (Access, Export, Correction, Deletion)
- Periodic Access Review Campaigns & Decisions
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

# Cross-dialect JSON type
JSONType = JSONB().with_variant(String, "sqlite")


class GovernancePolicyCategory(StrEnum):
    DATA_CLASSIFICATION = "DATA_CLASSIFICATION"
    RETENTION = "RETENTION"
    ACCESS = "ACCESS"
    EXPORT = "EXPORT"
    PRIVACY = "PRIVACY"
    ARCHIVAL = "ARCHIVAL"
    DELETION = "DELETION"
    DOCUMENT = "DOCUMENT"
    REPORTING = "REPORTING"
    AI = "AI"


class GovernancePolicyStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    RETIRED = "RETIRED"


class RetentionAction(StrEnum):
    RETAIN = "RETAIN"
    ARCHIVE = "ARCHIVE"
    ANONYMIZE = "ANONYMIZE"
    DELETE = "DELETE"
    REVIEW = "REVIEW"


class RetentionUnit(StrEnum):
    DAYS = "DAYS"
    MONTHS = "MONTHS"
    YEARS = "YEARS"


class RetentionTriggerEvent(StrEnum):
    CREATION = "CREATION"
    COMPLETION = "COMPLETION"
    GRADUATION = "GRADUATION"
    EXPIRATION = "EXPIRATION"
    DEACTIVATION = "DEACTIVATION"


class HoldStatus(StrEnum):
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"
    EXPIRED = "EXPIRED"


class PrivacyRequestType(StrEnum):
    ACCESS = "ACCESS"
    EXPORT = "EXPORT"
    CORRECTION = "CORRECTION"
    RESTRICTION = "RESTRICTION"
    DELETION = "DELETION"
    REVIEW = "REVIEW"


class PrivacyRequestStatus(StrEnum):
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    IDENTITY_VERIFICATION_REQUIRED = "IDENTITY_VERIFICATION_REQUIRED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    PARTIALLY_COMPLETED = "PARTIALLY_COMPLETED"
    CANCELLED = "CANCELLED"


class AccessReviewStatus(StrEnum):
    OPEN = "OPEN"
    IN_REVIEW = "IN_REVIEW"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"


class AccessReviewDecisionType(StrEnum):
    PENDING = "PENDING"
    RETAIN = "RETAIN"
    REVOKE = "REVOKE"
    MODIFY = "MODIFY"
    ESCALATE = "ESCALATE"


class GovernancePolicy(TenantScopedModel):
    """Institutional Governance Policy definition governing data lifecycle and privacy rules."""

    __tablename__ = "governance_policies"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_gov_policies_tenant_code"),
        Index("ix_gov_policies_tenant_cat", "tenant_id", "category"),
        Index("ix_gov_policies_tenant_status", "tenant_id", "status"),
    )

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[str] = mapped_column(String(64), default=GovernancePolicyCategory.RETENTION, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default=GovernancePolicyStatus.ACTIVE, nullable=False)
    is_system_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    active_version_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    created_by_user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    updated_by_user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    versions: Mapped[list["GovernancePolicyVersion"]] = relationship(
        "GovernancePolicyVersion",
        back_populates="policy",
        cascade="all, delete-orphan",
        order_by="desc(GovernancePolicyVersion.version_number)",
    )
    retention_rules: Mapped[list["RetentionPolicy"]] = relationship(
        "RetentionPolicy",
        back_populates="policy",
    )


class GovernancePolicyVersion(TenantScopedModel):
    """Immutable, versioned policy rule set with effective duration."""

    __tablename__ = "governance_policy_versions"
    __table_args__ = (
        UniqueConstraint("policy_id", "version_number", name="uq_gov_policy_versions_num"),
        Index("ix_gov_policy_versions_active", "tenant_id", "policy_id", "is_active"),
    )

    policy_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("governance_policies.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=GovernancePolicyStatus.ACTIVE, nullable=False)
    rules_json: Mapped[dict | list] = mapped_column(JSONType, default=dict, nullable=False)
    change_summary: Mapped[str | None] = mapped_column(String(255), nullable=True)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    effective_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    policy: Mapped["GovernancePolicy"] = relationship("GovernancePolicy", back_populates="versions")


class RetentionPolicy(TenantScopedModel):
    """Fine-grained retention schedule for a specific institutional resource type."""

    __tablename__ = "governance_retention_policies"
    __table_args__ = (
        UniqueConstraint("tenant_id", "resource_type", name="uq_gov_retention_tenant_res"),
        Index("ix_gov_retention_tenant_active", "tenant_id", "is_active"),
    )

    policy_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("governance_policies.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    retention_period: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    retention_unit: Mapped[str] = mapped_column(String(16), default=RetentionUnit.YEARS, nullable=False)
    trigger_event: Mapped[str] = mapped_column(String(32), default=RetentionTriggerEvent.CREATION, nullable=False)
    action: Mapped[str] = mapped_column(String(32), default=RetentionAction.ARCHIVE, nullable=False)
    archive_after_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    delete_after_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    legal_hold_behavior: Mapped[str] = mapped_column(String(16), default="BLOCK", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    policy: Mapped["GovernancePolicy | None"] = relationship("GovernancePolicy", back_populates="retention_rules")


class GovernanceHold(TenantScopedModel):
    """Legal or administrative hold preventing automated deletion or anonymization."""

    __tablename__ = "governance_holds"
    __table_args__ = (
        Index("ix_gov_holds_tenant_status", "tenant_id", "status"),
        Index("ix_gov_holds_target", "tenant_id", "target_entity_type", "target_entity_id"),
    )

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    case_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    target_entity_type: Mapped[str] = mapped_column(String(64), nullable=False)  # STUDENT, FACULTY, DOCUMENT, INVOICE, ALL
    target_entity_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=HoldStatus.ACTIVE, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    released_by_user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    release_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    @property
    def is_active(self) -> bool:
        if self.status != HoldStatus.ACTIVE:
            return False
        if self.expires_at:
            exp = self.expires_at
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=UTC)
            return datetime.now(UTC) <= exp
        return True


class PrivacyRequest(TenantScopedModel):
    """Data Subject Access / Privacy Fulfillment Request across institutional domains."""

    __tablename__ = "governance_privacy_requests"
    __table_args__ = (
        UniqueConstraint("tenant_id", "request_number", name="uq_gov_privacy_req_num"),
        Index("ix_gov_privacy_tenant_status", "tenant_id", "status"),
        Index("ix_gov_privacy_subject", "tenant_id", "data_subject_id"),
    )

    request_number: Mapped[str] = mapped_column(String(64), nullable=False)
    request_type: Mapped[str] = mapped_column(String(32), default=PrivacyRequestType.ACCESS, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=PrivacyRequestStatus.SUBMITTED, nullable=False)
    data_subject_type: Mapped[str] = mapped_column(String(32), default="STUDENT", nullable=False)
    data_subject_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    requested_by_user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    reviewed_by_user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_domains_json: Mapped[list] = mapped_column(JSONType, default=list, nullable=False)
    payload_json: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    export_storage_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    export_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    actions: Mapped[list["PrivacyRequestAction"]] = relationship(
        "PrivacyRequestAction",
        back_populates="request",
        cascade="all, delete-orphan",
        order_by="PrivacyRequestAction.created_at",
    )


class PrivacyRequestAction(TenantScopedModel):
    """Sub-action or domain mutation performed during privacy request fulfillment."""

    __tablename__ = "governance_privacy_request_actions"
    __table_args__ = (
        Index("ix_gov_priv_act_req", "tenant_id", "request_id"),
    )

    request_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("governance_privacy_requests.id", ondelete="CASCADE"),
        nullable=False,
    )
    action_type: Mapped[str] = mapped_column(String(32), nullable=False)
    domain: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    blocked_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    old_values_json: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    new_values_json: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    performed_by_user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    performed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    request: Mapped["PrivacyRequest"] = relationship("PrivacyRequest", back_populates="actions")


class AccessReview(TenantScopedModel):
    """Campaign reviewing privileged user access and roles for regulatory compliance."""

    __tablename__ = "governance_access_reviews"
    __table_args__ = (
        Index("ix_gov_reviews_tenant_status", "tenant_id", "status"),
    )

    title: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_type: Mapped[str] = mapped_column(String(64), default="PRIVILEGED_ROLES", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=AccessReviewStatus.OPEN, nullable=False)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reviewer_user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    items: Mapped[list["AccessReviewItem"]] = relationship(
        "AccessReviewItem",
        back_populates="review",
        cascade="all, delete-orphan",
    )


class AccessReviewItem(TenantScopedModel):
    """Single permission/role evaluation item within an Access Review campaign."""

    __tablename__ = "governance_access_review_items"
    __table_args__ = (
        Index("ix_gov_rev_items_review", "tenant_id", "review_id"),
        Index("ix_gov_rev_items_user", "tenant_id", "user_id"),
    )

    review_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("governance_access_reviews.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_roles.id", ondelete="SET NULL"),
        nullable=True,
    )
    permission_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    decision: Mapped[str] = mapped_column(String(32), default=AccessReviewDecisionType.PENDING, nullable=False)
    decision_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_by_user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    review: Mapped["AccessReview"] = relationship("AccessReview", back_populates="items")
