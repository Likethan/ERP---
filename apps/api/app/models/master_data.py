"""SQLAlchemy Domain Models for Enterprise Master Data Management & Data Quality (Step 24).

Implements:
1. MasterDataDefinition & Canonical Record Registry
2. ReferenceDataDefinition & Controlled Reference Values
3. DataQualityRule, DataQualityResult & DataQualityIssue
4. DuplicateCandidate & Matching Detection
5. MasterDataMergeOperation & Survivorship Rules
6. MasterDataLineage & Provenance
7. MasterDataCorrection Workflows
"""

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel, TenantScopedModel

# Cross-dialect JSON type for PostgreSQL JSONB and SQLite JSON
JSONType = JSON().with_variant(JSONB, "postgresql")


# =============================================================================
# ENUMS
# =============================================================================


class MasterDataType(StrEnum):
    """Governed institutional master data entity categories."""

    INSTITUTION = "INSTITUTION"
    CAMPUS = "CAMPUS"
    DEPARTMENT = "DEPARTMENT"
    PROGRAM = "PROGRAM"
    ACADEMIC_YEAR = "ACADEMIC_YEAR"
    SEMESTER = "SEMESTER"
    SUBJECT = "SUBJECT"
    STUDENT = "STUDENT"
    FACULTY = "FACULTY"
    STAFF = "STAFF"
    COMPANY = "COMPANY"
    FEE_CATEGORY = "FEE_CATEGORY"
    DOCUMENT_CATEGORY = "DOCUMENT_CATEGORY"
    HOSTEL_BLOCK = "HOSTEL_BLOCK"
    TRANSPORT_ROUTE = "TRANSPORT_ROUTE"


class MasterDataSensitivity(StrEnum):
    """Sensitivity classification for governed master data."""

    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"


class QualityRuleType(StrEnum):
    """Supported rule evaluation types."""

    REQUIRED = "REQUIRED"
    UNIQUE = "UNIQUE"
    FORMAT = "FORMAT"
    RANGE = "RANGE"
    ENUM = "ENUM"
    REFERENCE_EXISTS = "REFERENCE_EXISTS"
    REFERENCE_ACTIVE = "REFERENCE_ACTIVE"
    CROSS_FIELD = "CROSS_FIELD"
    CROSS_ENTITY = "CROSS_ENTITY"
    FRESHNESS = "FRESHNESS"
    DUPLICATE = "DUPLICATE"


class QualitySeverity(StrEnum):
    """Severity ratings for quality rule breaches."""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class QualityIssueStatus(StrEnum):
    """Lifecycle status for a detected quality issue."""

    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    IGNORED = "IGNORED"
    REOPENED = "REOPENED"


class DuplicateStatus(StrEnum):
    """Lifecycle status of a detected duplicate candidate pair."""

    PENDING = "PENDING"
    CONFIRMED_DUPLICATE = "CONFIRMED_DUPLICATE"
    NOT_DUPLICATE = "NOT_DUPLICATE"
    DISMISSED = "DISMISSED"
    MERGED = "MERGED"


class SurvivorshipRule(StrEnum):
    """Strategy used to determine attribute values during duplicate merge."""

    KEEP_CANONICAL = "KEEP_CANONICAL"
    KEEP_MOST_RECENT = "KEEP_MOST_RECENT"
    KEEP_NON_EMPTY = "KEEP_NON_EMPTY"
    EXPLICIT_FIELD_SELECTION = "EXPLICIT_FIELD_SELECTION"


class LineageSource(StrEnum):
    """Authoritative ingestion/modification source channel."""

    MANUAL = "MANUAL"
    IMPORT = "IMPORT"
    API = "API"
    INTEGRATION = "INTEGRATION"
    SYSTEM = "SYSTEM"
    MIGRATION = "MIGRATION"
    MERGE = "MERGE"


class CorrectionStatus(StrEnum):
    """Lifecycle state of a master data attribute correction request."""

    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    APPLIED = "APPLIED"
    REJECTED = "REJECTED"


# =============================================================================
# 1. MASTER DATA DEFINITIONS
# =============================================================================


class MasterDataDefinition(BaseModel):
    """Registry definition describing which entity types participate in MDM governance."""

    __tablename__ = "master_data_definitions"

    key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_domain: Mapped[str] = mapped_column(String(64), nullable=False)
    steward_role: Mapped[str] = mapped_column(
        String(64), default="INSTITUTION_ADMIN", nullable=False
    )
    sensitivity: Mapped[str] = mapped_column(
        String(32), default=MasterDataSensitivity.INTERNAL, nullable=False
    )
    duplicate_detection_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    merge_supported: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    archival_supported: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    authoritative_source: Mapped[str] = mapped_column(String(128), nullable=False)
    canonical_table_name: Mapped[str] = mapped_column(String(128), nullable=False)
    canonical_id_column: Mapped[str] = mapped_column(String(64), default="id", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


# =============================================================================
# 2. REFERENCE DATA DEFINITIONS & VALUES
# =============================================================================


class ReferenceDataDefinition(BaseModel):
    """Registry category for runtime-governed controlled reference codes."""

    __tablename__ = "reference_data_definitions"

    category: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ReferenceDataValue(TenantScopedModel):
    """Tenant-controlled runtime reference code value."""

    __tablename__ = "reference_data_values"
    __table_args__ = (
        UniqueConstraint("tenant_id", "category", "code", name="uq_ref_val_tenant_cat_code"),
        Index("idx_ref_val_tenant_cat", "tenant_id", "category"),
    )

    category: Mapped[str] = mapped_column(String(64), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    effective_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    effective_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    updated_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)


# =============================================================================
# 3. DATA QUALITY RULES & RESULTS
# =============================================================================


class DataQualityRule(TenantScopedModel):
    """Configurable quality validation rule for governed master records."""

    __tablename__ = "data_quality_rules"
    __table_args__ = (
        UniqueConstraint("tenant_id", "rule_key", name="uq_quality_rule_tenant_key"),
        Index("idx_quality_rule_tenant_type", "tenant_id", "master_type"),
    )

    master_type: Mapped[str] = mapped_column(String(64), nullable=False)
    rule_key: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    field_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rule_type: Mapped[str] = mapped_column(
        String(32), default=QualityRuleType.REQUIRED, nullable=False
    )
    severity: Mapped[str] = mapped_column(String(32), default=QualitySeverity.ERROR, nullable=False)
    parameters_json: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class DataQualityResult(TenantScopedModel):
    """Historical/current snapshot of quality score evaluation on a master record."""

    __tablename__ = "data_quality_results"
    __table_args__ = (
        Index("idx_dq_result_tenant_record", "tenant_id", "master_type", "record_id"),
        Index("idx_dq_result_eval_time", "tenant_id", "evaluated_at"),
    )

    master_type: Mapped[str] = mapped_column(String(64), nullable=False)
    record_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    dimension_scores_json: Mapped[dict[str, Any]] = mapped_column(JSONType, nullable=False)
    rule_results_json: Mapped[list[dict[str, Any]]] = mapped_column(JSONType, nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class DataQualityIssue(TenantScopedModel):
    """First-class quality defect or anomaly tracked for stewardship remediation."""

    __tablename__ = "data_quality_issues"
    __table_args__ = (
        Index("idx_dq_issue_tenant_status", "tenant_id", "status"),
        Index("idx_dq_issue_tenant_type_record", "tenant_id", "master_type", "record_id"),
    )

    master_type: Mapped[str] = mapped_column(String(64), nullable=False)
    record_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    rule_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("data_quality_rules.id", ondelete="SET NULL"),
        nullable=True,
    )
    rule_key: Mapped[str] = mapped_column(String(128), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=QualityIssueStatus.OPEN, nullable=False)
    issue_message: Mapped[str] = mapped_column(Text, nullable=False)
    field_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    assigned_to: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)


# =============================================================================
# 4. DUPLICATE CANDIDATES
# =============================================================================


class DuplicateCandidate(TenantScopedModel):
    """Identified pair of potential duplicate records pending stewardship resolution."""

    __tablename__ = "duplicate_candidates"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "master_type", "record_a_id", "record_b_id", name="uq_dup_cand_pair"
        ),
        Index("idx_dup_cand_tenant_status", "tenant_id", "status"),
    )

    master_type: Mapped[str] = mapped_column(String(64), nullable=False)
    record_a_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    record_b_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    match_score: Mapped[float] = mapped_column(Float, nullable=False)
    match_reasons: Mapped[list[str]] = mapped_column(JSONType, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=DuplicateStatus.PENDING, nullable=False)
    reviewed_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)


# =============================================================================
# 5. MERGE OPERATIONS & REVERSALS
# =============================================================================


class MasterDataMergeOperation(TenantScopedModel):
    """Forensic ledger of a completed duplicate record merge with rollback capability."""

    __tablename__ = "master_data_merge_operations"
    __table_args__ = (
        Index("idx_merge_op_tenant_type", "tenant_id", "master_type"),
        Index("idx_merge_op_survivor", "tenant_id", "survivor_record_id"),
        Index("idx_merge_op_merged", "tenant_id", "merged_record_id"),
    )

    master_type: Mapped[str] = mapped_column(String(64), nullable=False)
    survivor_record_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    merged_record_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    actor_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    survivorship_rule: Mapped[str] = mapped_column(
        String(32), default=SurvivorshipRule.KEEP_CANONICAL, nullable=False
    )
    field_decisions_json: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    reassigned_counts_json: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="COMPLETED", nullable=False)
    is_reversible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    rolled_back_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rolled_back_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    rollback_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


# =============================================================================
# 6. MASTER DATA LINEAGE & CORRECTIONS
# =============================================================================


class MasterDataLineage(TenantScopedModel):
    """Audit lineage tracking ingestion provenance and verification history."""

    __tablename__ = "master_data_lineage"
    __table_args__ = (
        Index("idx_md_lineage_tenant_record", "tenant_id", "master_type", "record_id"),
    )

    master_type: Mapped[str] = mapped_column(String(64), nullable=False)
    record_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    source: Mapped[str] = mapped_column(String(32), default=LineageSource.MANUAL, nullable=False)
    source_record_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    imported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    modified_by: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    modification_source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    details_json: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)


class MasterDataCorrection(TenantScopedModel):
    """Stewardship correction request with review and approval workflow."""

    __tablename__ = "master_data_corrections"
    __table_args__ = (
        Index("idx_md_corr_tenant_status", "tenant_id", "status"),
        Index("idx_md_corr_tenant_record", "tenant_id", "master_type", "record_id"),
    )

    master_type: Mapped[str] = mapped_column(String(64), nullable=False)
    record_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    field_name: Mapped[str] = mapped_column(String(64), nullable=False)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    proposed_value: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=CorrectionStatus.PENDING_REVIEW, nullable=False
    )
    requester_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    reviewer_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
