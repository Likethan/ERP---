"""Enterprise Records Lifecycle, Retention, Archival & Legal Hold Models for CampusOS (Step 41).

Provides multi-tenant relational persistence for:
- Standard and configurable Record Categories across institutional domains
- Centralized Records Registry tracking source module records without sensitive duplication
- Comprehensive, versioned Retention Policy specifications and historical versions
- Controlled 12-state Record Lifecycle State Machine and transition histories
- Tamper-evident Archival Manifests, checksum verifications, and controlled access logs
- High-precedence Administrative and Legal Holds, custodian assignments, and associations
- Controlled Disposition Requests, multi-person approvals, item outcomes, and Certificates
- Operational Scheduled Lifecycle Run tracking and execution metrics
"""

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

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
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantScopedModel

# Cross-dialect JSONB compatibility
JSONB_COMPAT = JSONB


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================


class RecordLifecycleState(StrEnum):
    ACTIVE = "ACTIVE"
    RETENTION_PENDING = "RETENTION_PENDING"
    RETENTION_IN_PROGRESS = "RETENTION_IN_PROGRESS"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    ELIGIBLE_FOR_ARCHIVAL = "ELIGIBLE_FOR_ARCHIVAL"
    ARCHIVED = "ARCHIVED"
    DISPOSITION_ELIGIBLE = "DISPOSITION_ELIGIBLE"
    DISPOSITION_PENDING_APPROVAL = "DISPOSITION_PENDING_APPROVAL"
    DISPOSITION_APPROVED = "DISPOSITION_APPROVED"
    DISPOSITION_COMPLETED = "DISPOSITION_COMPLETED"
    LEGAL_HOLD = "LEGAL_HOLD"
    REVIEW_BLOCKED = "REVIEW_BLOCKED"


class RetentionUnit(StrEnum):
    DAYS = "DAYS"
    MONTHS = "MONTHS"
    YEARS = "YEARS"
    PERMANENT = "PERMANENT"


class RetentionTriggerEvent(StrEnum):
    CREATION = "CREATION"
    GRADUATION = "GRADUATION"
    TERMINATION = "TERMINATION"
    FY_CLOSE = "FY_CLOSE"
    CONTRACT_EXPIRY = "CONTRACT_EXPIRY"
    CASE_CLOSURE = "CASE_CLOSURE"
    COMPLETION = "COMPLETION"


class RetentionPolicyStatus(StrEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    DEPRECATED = "DEPRECATED"
    ARCHIVED = "ARCHIVED"


class PolicyScope(StrEnum):
    GLOBAL = "GLOBAL"
    CATEGORY = "CATEGORY"
    MODULE = "MODULE"
    DEPARTMENT = "DEPARTMENT"


class DispositionMethod(StrEnum):
    SECURE_DELETE = "SECURE_DELETE"
    ANONYMIZE = "ANONYMIZE"
    PERMANENT_ARCHIVE = "PERMANENT_ARCHIVE"
    REVIEW_ONLY = "REVIEW_ONLY"


class LegalHoldStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"
    EXPIRED = "EXPIRED"


class LegalHoldScope(StrEnum):
    ALL = "ALL"
    CATEGORY = "CATEGORY"
    MODULE = "MODULE"
    DEPARTMENT = "DEPARTMENT"
    SPECIFIC_RECORD = "SPECIFIC_RECORD"


class ArchivalStatus(StrEnum):
    PREPARING = "PREPARING"
    STORED = "STORED"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    RESTORED = "RESTORED"


class DispositionRequestStatus(StrEnum):
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class DispositionItemStatus(StrEnum):
    ELIGIBLE = "ELIGIBLE"
    BLOCKED_HOLD = "BLOCKED_HOLD"
    BLOCKED_DEPENDENCY = "BLOCKED_DEPENDENCY"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"


class ScheduledRunType(StrEnum):
    ELIGIBILITY_RECALCULATION = "ELIGIBILITY_RECALCULATION"
    RETENTION_REVIEW_SWEEP = "RETENTION_REVIEW_SWEEP"
    ARCHIVE_CANDIDATE_SWEEP = "ARCHIVE_CANDIDATE_SWEEP"
    HOLD_COVERAGE_CHECK = "HOLD_COVERAGE_CHECK"
    DISPOSITION_QUEUE_SWEEP = "DISPOSITION_QUEUE_SWEEP"


class ScheduledRunStatus(StrEnum):
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# =============================================================================
# 1. RECORD CATEGORY & CLASSIFICATION
# =============================================================================


class RecordCategory(TenantScopedModel):
    """Institutional classification defining statutory authorities and governance guidelines."""

    __tablename__ = "records_categories"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_records_cat_tenant_code"),
        Index("ix_records_cat_tenant_active", "tenant_id", "is_active"),
    )

    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidentiality: Mapped[str] = mapped_column(String(32), default="CONFIDENTIAL", nullable=False)
    default_retention_years: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    statutory_authority: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    metadata_json: Mapped[dict | list | None] = mapped_column(JSONB_COMPAT, default=dict, nullable=True)

    # Relationships
    registry_entries: Mapped[list["RecordRegistryEntry"]] = relationship(
        "RecordRegistryEntry", back_populates="category"
    )


# =============================================================================
# 2. RETENTION POLICIES & IMMUTABLE VERSIONS
# =============================================================================


class RetentionPolicyDefinition(TenantScopedModel):
    """Configurable, versioned retention specification establishing lifecycle triggers and rules."""

    __tablename__ = "records_retention_policies"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_records_pol_tenant_code"),
        Index("ix_records_pol_tenant_status", "tenant_id", "status"),
        Index("ix_records_pol_tenant_cat", "tenant_id", "category_code"),
    )

    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_code: Mapped[str] = mapped_column(String(64), nullable=False)
    scope: Mapped[str] = mapped_column(String(32), default=PolicyScope.CATEGORY, nullable=False)
    scope_target: Mapped[str | None] = mapped_column(String(128), nullable=True)

    retention_duration: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    retention_unit: Mapped[str] = mapped_column(String(16), default=RetentionUnit.YEARS, nullable=False)
    trigger_event: Mapped[str] = mapped_column(String(32), default=RetentionTriggerEvent.CREATION, nullable=False)

    review_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    archive_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    disposition_method: Mapped[str] = mapped_column(String(32), default=DispositionMethod.ANONYMIZE, nullable=False)
    approval_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    effective_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default=RetentionPolicyStatus.DRAFT, nullable=False)
    current_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    owner_user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    approved_by_user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict | list | None] = mapped_column(JSONB_COMPAT, default=dict, nullable=True)

    # Relationships
    versions: Mapped[list["RetentionPolicyVersionRecord"]] = relationship(
        "RetentionPolicyVersionRecord",
        back_populates="policy",
        cascade="all, delete-orphan",
        order_by="desc(RetentionPolicyVersionRecord.version_number)",
        lazy="selectin",
    )
    registry_entries: Mapped[list["RecordRegistryEntry"]] = relationship(
        "RecordRegistryEntry", back_populates="retention_policy"
    )


class RetentionPolicyVersionRecord(TenantScopedModel):
    """Historical immutable snapshot of retention policy rules ensuring complete traceability."""

    __tablename__ = "records_retention_policy_versions"
    __table_args__ = (
        UniqueConstraint("policy_id", "version_number", name="uq_records_pol_ver_num"),
        Index("ix_records_pol_ver_tenant", "tenant_id", "policy_id"),
    )

    policy_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("records_retention_policies.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=RetentionPolicyStatus.PUBLISHED, nullable=False)
    rules_json: Mapped[dict | list] = mapped_column(JSONB_COMPAT, default=dict, nullable=False)
    change_summary: Mapped[str | None] = mapped_column(String(255), nullable=True)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    effective_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    policy: Mapped["RetentionPolicyDefinition"] = relationship(
        "RetentionPolicyDefinition", back_populates="versions"
    )


# =============================================================================
# 3. RECORDS REGISTRY & LIFECYCLE STATE TRACKING
# =============================================================================


class RecordRegistryEntry(TenantScopedModel):
    """Central metadata registry indexing authoritative institutional records across all modules."""

    __tablename__ = "records_registry"
    __table_args__ = (
        UniqueConstraint("tenant_id", "source_module", "source_record_id", name="uq_records_reg_tenant_src"),
        Index("ix_records_reg_tenant_state", "tenant_id", "lifecycle_state"),
        Index("ix_records_reg_tenant_cat", "tenant_id", "category_code"),
        Index("ix_records_reg_tenant_held", "tenant_id", "is_held"),
        Index("ix_records_reg_tenant_elig", "tenant_id", "calculated_eligibility_date"),
        Index("ix_records_reg_rec_num", "tenant_id", "record_number", unique=True),
    )

    record_number: Mapped[str] = mapped_column(String(64), nullable=False)
    category_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("records_categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    category_code: Mapped[str] = mapped_column(String(64), nullable=False)
    source_module: Mapped[str] = mapped_column(String(64), nullable=False)  # students, faculty, academics, exams, finance, documents, placement
    source_record_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    source_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)  # e.g., USN, Employee ID, Invoice Number
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    owner_user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    owner_department_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    responsible_department: Mapped[str | None] = mapped_column(String(128), nullable=True)
    confidentiality_level: Mapped[str] = mapped_column(String(32), default="CONFIDENTIAL", nullable=False)

    lifecycle_state: Mapped[str] = mapped_column(String(32), default=RecordLifecycleState.ACTIVE, nullable=False)
    policy_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("records_retention_policies.id", ondelete="SET NULL"),
        nullable=True,
    )
    policy_version: Mapped[int | None] = mapped_column(Integer, nullable=True)

    record_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    retention_start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    calculated_review_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    calculated_eligibility_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    disposed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    is_held: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    active_hold_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    storage_reference: Mapped[str | None] = mapped_column(String(512), nullable=True)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[dict | list | None] = mapped_column(JSONB_COMPAT, default=dict, nullable=True)

    # Relationships
    category: Mapped["RecordCategory | None"] = relationship("RecordCategory", back_populates="registry_entries")
    retention_policy: Mapped["RetentionPolicyDefinition | None"] = relationship(
        "RetentionPolicyDefinition", back_populates="registry_entries"
    )
    history: Mapped[list["RecordLifecycleHistory"]] = relationship(
        "RecordLifecycleHistory", back_populates="record", cascade="all, delete-orphan", order_by="desc(RecordLifecycleHistory.created_at)", lazy="selectin"
    )
    archival_manifest: Mapped["RecordArchivalRecord | None"] = relationship(
        "RecordArchivalRecord", back_populates="record", uselist=False, lazy="selectin"
    )
    hold_associations: Mapped[list["RecordLegalHoldAssociation"]] = relationship(
        "RecordLegalHoldAssociation", back_populates="record", cascade="all, delete-orphan", lazy="selectin"
    )


class RecordLifecycleHistory(TenantScopedModel):
    """Immutable audit trail of record lifecycle transitions."""

    __tablename__ = "records_lifecycle_history"
    __table_args__ = (
        Index("ix_records_hist_tenant_rec", "tenant_id", "record_id"),
        Index("ix_records_hist_created", "tenant_id", "created_at"),
    )

    record_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("records_registry.id", ondelete="CASCADE"),
        nullable=False,
    )
    from_state: Mapped[str] = mapped_column(String(32), nullable=False)
    to_state: Mapped[str] = mapped_column(String(32), nullable=False)
    trigger_action: Mapped[str] = mapped_column(String(64), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor_user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    actor_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[dict | list | None] = mapped_column(JSONB_COMPAT, default=dict, nullable=True)

    record: Mapped["RecordRegistryEntry"] = relationship("RecordRegistryEntry", back_populates="history")


# =============================================================================
# 4. ARCHIVAL MANIFESTS & AUDITED ACCESS LOGS
# =============================================================================


class RecordArchivalRecord(TenantScopedModel):
    """Manifest referencing cold / archival storage with cryptographic integrity verification."""

    __tablename__ = "records_archival_manifests"
    __table_args__ = (
        UniqueConstraint("tenant_id", "record_id", name="uq_records_arch_rec"),
        Index("ix_records_arch_tenant_status", "tenant_id", "status"),
        Index("ix_records_arch_manifest_num", "tenant_id", "manifest_number", unique=True),
    )

    manifest_number: Mapped[str] = mapped_column(String(64), nullable=False)
    record_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("records_registry.id", ondelete="CASCADE"),
        nullable=False,
    )
    archive_location: Mapped[str] = mapped_column(String(128), default="S3_COLD_TIER", nullable=False)
    archive_storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    original_storage_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    verified_checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=ArchivalStatus.STORED, nullable=False)

    archived_by_user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    archived_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    retrieval_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict | list | None] = mapped_column(JSONB_COMPAT, default=dict, nullable=True)

    record: Mapped["RecordRegistryEntry"] = relationship("RecordRegistryEntry", back_populates="archival_manifest")
    access_logs: Mapped[list["RecordArchivalAccessLog"]] = relationship(
        "RecordArchivalAccessLog", back_populates="manifest", cascade="all, delete-orphan", lazy="selectin"
    )


class RecordArchivalAccessLog(TenantScopedModel):
    """Controlled access and retrieval history for archived institutional records."""

    __tablename__ = "records_archival_access_logs"
    __table_args__ = (
        Index("ix_records_arch_log_tenant", "tenant_id", "manifest_id"),
    )

    manifest_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("records_archival_manifests.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    access_type: Mapped[str] = mapped_column(String(32), nullable=False)  # METADATA_VIEW, FILE_DOWNLOAD, RESTORATION_REQUEST
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    accessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    manifest: Mapped["RecordArchivalRecord"] = relationship("RecordArchivalRecord", back_populates="access_logs")


# =============================================================================
# 5. LEGAL HOLDS & SCOPED ASSOCIATIONS
# =============================================================================


class RecordLegalHold(TenantScopedModel):
    """Institutional administrative and legal hold preventing automated or manual disposition."""

    __tablename__ = "records_legal_holds"
    __table_args__ = (
        UniqueConstraint("tenant_id", "hold_number", name="uq_records_hold_num"),
        Index("ix_records_hold_tenant_status", "tenant_id", "status"),
        Index("ix_records_hold_scope", "tenant_id", "scope_type", "scope_value"),
    )

    hold_number: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    case_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    hold_authority: Mapped[str] = mapped_column(String(128), default="INSTITUTIONAL_COMPLIANCE", nullable=False)
    scope_type: Mapped[str] = mapped_column(String(32), default=LegalHoldScope.CATEGORY, nullable=False)
    scope_value: Mapped[str | None] = mapped_column(String(128), nullable=True)  # category code, department UUID, module name, or record UUID

    status: Mapped[str] = mapped_column(String(32), default=LegalHoldStatus.ACTIVE, nullable=False)
    owner_user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    custodians_json: Mapped[list | None] = mapped_column(JSONB_COMPAT, default=list, nullable=True)

    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    review_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    released_by_user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    release_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    records_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    metadata_json: Mapped[dict | list | None] = mapped_column(JSONB_COMPAT, default=dict, nullable=True)

    # Relationships
    associations: Mapped[list["RecordLegalHoldAssociation"]] = relationship(
        "RecordLegalHoldAssociation", back_populates="hold", cascade="all, delete-orphan", lazy="selectin"
    )


class RecordLegalHoldAssociation(TenantScopedModel):
    """Direct association between a legal hold and a registered institutional record."""

    __tablename__ = "records_legal_hold_associations"
    __table_args__ = (
        UniqueConstraint("hold_id", "record_id", name="uq_records_hold_assoc"),
        Index("ix_records_assoc_tenant_rec", "tenant_id", "record_id"),
    )

    hold_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("records_legal_holds.id", ondelete="CASCADE"),
        nullable=False,
    )
    record_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("records_registry.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    applied_by_user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    released_by_user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    hold: Mapped["RecordLegalHold"] = relationship("RecordLegalHold", back_populates="associations")
    record: Mapped["RecordRegistryEntry"] = relationship("RecordRegistryEntry", back_populates="hold_associations")


# =============================================================================
# 6. DISPOSITION WORKFLOW, APPROVALS & CERTIFICATES
# =============================================================================


class RecordDispositionRequest(TenantScopedModel):
    """Formal governance batch request to execute disposition (deletion, anonymization, permanent archive)."""

    __tablename__ = "records_disposition_requests"
    __table_args__ = (
        UniqueConstraint("tenant_id", "request_number", name="uq_records_disp_req_num"),
        Index("ix_records_disp_tenant_status", "tenant_id", "status"),
    )

    request_number: Mapped[str] = mapped_column(String(64), nullable=False)
    policy_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("records_retention_policies.id", ondelete="SET NULL"),
        nullable=True,
    )
    policy_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    category_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    requested_disposition_method: Mapped[str] = mapped_column(String(32), default=DispositionMethod.ANONYMIZE, nullable=False)

    status: Mapped[str] = mapped_column(String(32), default=DispositionRequestStatus.DRAFT, nullable=False)
    records_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    preview_stats_json: Mapped[dict | None] = mapped_column(JSONB_COMPAT, default=dict, nullable=True)
    justification: Mapped[str] = mapped_column(Text, nullable=False)

    requested_by_user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    reviewed_by_user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by_user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | list | None] = mapped_column(JSONB_COMPAT, default=dict, nullable=True)

    items: Mapped[list["RecordDispositionItem"]] = relationship(
        "RecordDispositionItem", back_populates="request", cascade="all, delete-orphan", lazy="selectin"
    )
    certificate: Mapped["RecordDispositionCertificate | None"] = relationship(
        "RecordDispositionCertificate", back_populates="request", uselist=False, lazy="selectin"
    )


class RecordDispositionItem(TenantScopedModel):
    """Itemized evaluation outcome for individual record in disposition batch."""

    __tablename__ = "records_disposition_items"
    __table_args__ = (
        UniqueConstraint("request_id", "record_id", name="uq_records_disp_item"),
        Index("ix_records_disp_item_status", "tenant_id", "status"),
    )

    request_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("records_disposition_requests.id", ondelete="CASCADE"),
        nullable=False,
    )
    record_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("records_registry.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(32), default=DispositionItemStatus.ELIGIBLE, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    disposed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    request: Mapped["RecordDispositionRequest"] = relationship("RecordDispositionRequest", back_populates="items")
    record: Mapped["RecordRegistryEntry"] = relationship("RecordRegistryEntry")


class RecordDispositionCertificate(TenantScopedModel):
    """Tamper-evident legal certificate verifying completed disposition of records."""

    __tablename__ = "records_disposition_certificates"
    __table_args__ = (
        UniqueConstraint("tenant_id", "certificate_number", name="uq_records_disp_cert_num"),
        Index("ix_records_disp_cert_req", "tenant_id", "request_id"),
    )

    certificate_number: Mapped[str] = mapped_column(String(64), nullable=False)
    request_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("records_disposition_requests.id", ondelete="RESTRICT"),
        nullable=False,
    )
    disposition_method: Mapped[str] = mapped_column(String(32), nullable=False)
    total_records_destroyed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_records_anonymized: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_records_archived: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    disposition_manifest_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256 digest of record IDs and details

    executed_by_user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    approved_by_user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    certificate_metadata_json: Mapped[dict | list | None] = mapped_column(JSONB_COMPAT, default=dict, nullable=True)

    request: Mapped["RecordDispositionRequest"] = relationship("RecordDispositionRequest", back_populates="certificate")


# =============================================================================
# 7. SCHEDULED LIFECYCLE RUNS & METRICS
# =============================================================================


class RecordLifecycleScheduledRun(TenantScopedModel):
    """Audit log of scheduled background jobs executing lifecycle sweeps and reconciliations."""

    __tablename__ = "records_lifecycle_scheduled_runs"
    __table_args__ = (
        Index("ix_records_sched_tenant_type", "tenant_id", "job_type"),
        Index("ix_records_sched_started", "tenant_id", "started_at"),
    )

    job_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=ScheduledRunStatus.RUNNING, nullable=False)
    records_evaluated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_transitioned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_flagged_review: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_blocked: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    summary_json: Mapped[dict | None] = mapped_column(JSONB_COMPAT, default=dict, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
