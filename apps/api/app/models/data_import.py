"""Enterprise Data Import, Bulk Migration, Reconciliation & Interoperability Domain Models (Step 40).

Defines production-grade entities governing:
- Reusable Import Templates with schema constraints, required fields, and approval policies
- Full 14-state Import Job Lifecycle state machine with resumable batch progress
- Column Mapping Definitions and transformation pipelines
- Per-record execution outcomes, errors, and warnings
- Data conflict detection, discrepancy tracking, and manual/automated resolution
- Post-import data reconciliation reports and audit histories
"""

from datetime import UTC, datetime
from enum import Enum
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

from app.models.base import Base, BaseModel, TenantScopedModel

# Cross-dialect JSON compatibility for PostgreSQL JSONB and SQLite JSON
JSONB_COMPAT = JSONB


# -----------------------------------------------------------------------------
# 1. Enums and State Machine Definitions
# -----------------------------------------------------------------------------


class ImportJobStatus(str, Enum):
    """Explicit 14-state lifecycle engine for institutional data import jobs."""

    DRAFT = "DRAFT"
    FILE_UPLOADED = "FILE_UPLOADED"
    MAPPING_PENDING = "MAPPING_PENDING"
    VALIDATION_RUNNING = "VALIDATION_RUNNING"
    VALIDATION_COMPLETED = "VALIDATION_COMPLETED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    READY_TO_EXECUTE = "READY_TO_EXECUTE"
    EXECUTION_RUNNING = "EXECUTION_RUNNING"
    PARTIALLY_COMPLETED = "PARTIALLY_COMPLETED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"


class ImportExecutionPolicy(str, Enum):
    """Configurable execution strategy for handling new and existing records."""

    VALIDATE_ONLY = "VALIDATE_ONLY"
    CREATE_NEW = "CREATE_NEW"
    UPDATE_EXISTING = "UPDATE_EXISTING"
    UPSERT = "UPSERT"
    SKIP_CONFLICTS = "SKIP_CONFLICTS"


class ImportRecordStatus(str, Enum):
    """Processing state for an individual imported row."""

    PENDING = "PENDING"
    VALID = "VALID"
    INVALID = "INVALID"
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    SKIPPED = "SKIPPED"
    FAILED = "FAILED"


class ImportConflictType(str, Enum):
    """Classification of detected record conflicts."""

    DUPLICATE_IN_FILE = "DUPLICATE_IN_FILE"
    EXISTING_RECORD_MATCH = "EXISTING_RECORD_MATCH"
    AMBIGUOUS_MATCH = "AMBIGUOUS_MATCH"
    UNRESOLVED_FOREIGN_KEY = "UNRESOLVED_FOREIGN_KEY"


class ConflictResolutionAction(str, Enum):
    """Resolution applied to a conflicting record."""

    PENDING = "PENDING"
    SKIP = "SKIP"
    OVERWRITE = "OVERWRITE"
    SELECT_EXISTING = "SELECT_EXISTING"


class ReconciliationStatus(str, Enum):
    """Overall reconciliation outcome comparing planned vs committed records."""

    NOT_RUN = "NOT_RUN"
    MATCHED = "MATCHED"
    DISCREPANCY_DETECTED = "DISCREPANCY_DETECTED"
    RECONCILED = "RECONCILED"


# -----------------------------------------------------------------------------
# 2. Relational Entities
# -----------------------------------------------------------------------------


class ImportTemplate(BaseModel):
    """Global or system-defined specification for a structured entity import."""

    __tablename__ = "import_templates"

    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_domain: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    target_entity: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    required_fields: Mapped[list[str]] = mapped_column(
        JSONB_COMPAT, nullable=False, default=list, server_default="[]"
    )
    optional_fields: Mapped[list[str]] = mapped_column(
        JSONB_COMPAT, nullable=False, default=list, server_default="[]"
    )
    field_definitions: Mapped[dict[str, Any]] = mapped_column(
        JSONB_COMPAT, nullable=False, default=dict, server_default="{}"
    )
    supported_matching_keys: Mapped[list[str]] = mapped_column(
        JSONB_COMPAT, nullable=False, default=list, server_default="[]"
    )
    supported_policies: Mapped[list[str]] = mapped_column(
        JSONB_COMPAT, nullable=False, default=list, server_default="[]"
    )
    requires_approval_threshold: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    is_system_template: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    jobs: Mapped[list["ImportJob"]] = relationship("ImportJob", back_populates="template")


class ImportJob(TenantScopedModel):
    """Institutional data import job tracking lifecycle, file reference, and execution progress."""

    __tablename__ = "import_jobs"
    __table_args__ = (
        Index("idx_import_jobs_tenant_status", "tenant_id", "status"),
        Index("idx_import_jobs_tenant_domain", "tenant_id", "target_domain"),
        Index("idx_import_jobs_tenant_created", "tenant_id", "created_at"),
    )

    template_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("import_templates.id", ondelete="SET NULL"),
        nullable=True,
    )
    template_code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_domain: Mapped[str] = mapped_column(String(64), nullable=False)
    target_entity: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default=ImportJobStatus.DRAFT.value, nullable=False, index=True
    )
    execution_policy: Mapped[str] = mapped_column(
        String(32), default=ImportExecutionPolicy.CREATE_NEW.value, nullable=False
    )
    matching_key: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Source File Metadata & Storage
    source_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_file_storage_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    source_file_checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_file_size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    source_file_format: Mapped[str | None] = mapped_column(String(16), nullable=True)

    # Record Counters & Progress
    source_record_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    valid_record_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_record_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    warning_record_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_record_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_record_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_record_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    skipped_record_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_record_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_processed_row: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Approval Gating
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    approved_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approval_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Execution & Actor Metadata
    created_by_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_report_storage_key: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Post-Import Reconciliation
    reconciliation_status: Mapped[str] = mapped_column(
        String(32), default=ReconciliationStatus.NOT_RUN.value, nullable=False
    )
    reconciliation_diff_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reconciliation_summary: Mapped[dict[str, Any]] = mapped_column(
        JSONB_COMPAT, nullable=False, default=dict, server_default="{}"
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB_COMPAT, nullable=False, default=dict, server_default="{}"
    )

    # Relationships
    template: Mapped["ImportTemplate | None"] = relationship("ImportTemplate", back_populates="jobs")
    mapping: Mapped["ImportMappingDefinition | None"] = relationship(
        "ImportMappingDefinition",
        back_populates="job",
        uselist=False,
        cascade="all, delete-orphan",
    )
    state_history: Mapped[list["ImportJobStateHistory"]] = relationship(
        "ImportJobStateHistory",
        back_populates="job",
        cascade="all, delete-orphan",
        order_by="ImportJobStateHistory.created_at",
    )
    record_results: Mapped[list["ImportRecordResult"]] = relationship(
        "ImportRecordResult",
        back_populates="job",
        cascade="all, delete-orphan",
        order_by="ImportRecordResult.row_number",
    )
    conflicts: Mapped[list["ImportConflictRecord"]] = relationship(
        "ImportConflictRecord",
        back_populates="job",
        cascade="all, delete-orphan",
        order_by="ImportConflictRecord.row_number",
    )


class ImportMappingDefinition(TenantScopedModel):
    """Configurable column mapping, transformation rules, and defaults for an import job."""

    __tablename__ = "import_mapping_definitions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "job_id", name="uq_import_mapping_tenant_job"),
    )

    job_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("import_jobs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    template_code: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    column_mappings: Mapped[dict[str, str]] = mapped_column(
        JSONB_COMPAT, nullable=False, default=dict, server_default="{}"
    )
    transformations: Mapped[dict[str, Any]] = mapped_column(
        JSONB_COMPAT, nullable=False, default=dict, server_default="{}"
    )
    default_values: Mapped[dict[str, Any]] = mapped_column(
        JSONB_COMPAT, nullable=False, default=dict, server_default="{}"
    )
    is_validated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    job: Mapped["ImportJob"] = relationship("ImportJob", back_populates="mapping")


class ImportJobStateHistory(TenantScopedModel):
    """Immutable append-only audit trail of import job state transitions."""

    __tablename__ = "import_job_state_histories"
    __table_args__ = (
        Index("idx_import_history_tenant_job", "tenant_id", "job_id"),
    )

    job_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("import_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_status: Mapped[str] = mapped_column(String(50), nullable=False)
    to_status: Mapped[str] = mapped_column(String(50), nullable=False)
    actor_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB_COMPAT, nullable=False, default=dict, server_default="{}"
    )

    job: Mapped["ImportJob"] = relationship("ImportJob", back_populates="state_history")


class ImportRecordResult(TenantScopedModel):
    """Per-record processing outcome, validation errors, and committed entity reference."""

    __tablename__ = "import_record_results"
    __table_args__ = (
        Index("idx_import_record_tenant_job", "tenant_id", "job_id"),
        Index("idx_import_record_row", "job_id", "row_number"),
        Index("idx_import_record_status", "job_id", "status"),
    )

    job_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("import_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    matching_key_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default=ImportRecordStatus.PENDING.value, nullable=False
    )
    target_entity_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    source_data_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB_COMPAT, nullable=False, default=dict, server_default="{}"
    )
    transformed_data_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB_COMPAT, nullable=False, default=dict, server_default="{}"
    )
    errors_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB_COMPAT, nullable=False, default=list, server_default="[]"
    )
    warnings_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB_COMPAT, nullable=False, default=list, server_default="[]"
    )
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    job: Mapped["ImportJob"] = relationship("ImportJob", back_populates="record_results")


class ImportConflictRecord(TenantScopedModel):
    """Detected record discrepancy between import data and existing tenant database state."""

    __tablename__ = "import_conflict_records"
    __table_args__ = (
        Index("idx_import_conflict_tenant_job", "tenant_id", "job_id"),
        Index("idx_import_conflict_resolution", "job_id", "resolution"),
    )

    job_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("import_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    matching_key: Mapped[str] = mapped_column(String(64), nullable=False)
    matching_value: Mapped[str] = mapped_column(String(255), nullable=False)
    existing_entity_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    conflict_type: Mapped[str] = mapped_column(String(64), nullable=False)

    source_payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB_COMPAT, nullable=False, default=dict, server_default="{}"
    )
    existing_payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB_COMPAT, nullable=False, default=dict, server_default="{}"
    )
    discrepancies_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB_COMPAT, nullable=False, default=dict, server_default="{}"
    )

    resolution: Mapped[str] = mapped_column(
        String(32), default=ConflictResolutionAction.PENDING.value, nullable=False
    )
    resolved_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    job: Mapped["ImportJob"] = relationship("ImportJob", back_populates="conflicts")
