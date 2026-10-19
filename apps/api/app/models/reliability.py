"""SQLAlchemy Models for Enterprise Reliability Engineering, Disaster Recovery & Business Continuity (Step 31).

Provides persistence for:
1. Platform Backup Records & Cryptographic Verification Tracking
2. Sandbox Restore Verifications & Tenant Isolation Safety
3. Platform Dependency Circuit Breaker States
4. Document Storage & Object Integrity Audits
"""

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class BackupType(StrEnum):
    FULL = "FULL"
    LOGICAL = "LOGICAL"
    DIAGNOSTIC = "DIAGNOSTIC"


class BackupStatus(StrEnum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PRUNED = "PRUNED"


class RestoreVerificationStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    INCOMPLETE = "INCOMPLETE"


class ReliabilityCircuitBreakerState(StrEnum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class StorageAuditStatus(StrEnum):
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class PlatformBackupRecord(BaseModel):
    """Immutable audit record of a PostgreSQL database backup operation."""

    __tablename__ = "platform_backup_records"
    __table_args__ = (
        Index("idx_platform_backup_status", "status"),
        Index("idx_platform_backup_started", "started_at"),
        Index("idx_platform_backup_known_good", "is_known_good"),
    )

    backup_type: Mapped[str] = mapped_column(
        String(32), default=BackupType.FULL, nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    sha256_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=BackupStatus.PENDING, nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retention_days: Mapped[int] = mapped_column(Integer, default=14, nullable=False)
    is_known_good: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    triggered_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    restore_verifications: Mapped[list["PlatformRestoreVerification"]] = relationship(
        "PlatformRestoreVerification",
        back_populates="backup_record",
        cascade="all, delete-orphan",
    )


class PlatformRestoreVerification(BaseModel):
    """Audit record of a restore verification performed in an isolated sandbox environment."""

    __tablename__ = "platform_restore_verifications"
    __table_args__ = (
        Index("idx_restore_verify_status", "status"),
        Index("idx_restore_verify_backup", "backup_record_id"),
    )

    backup_record_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("platform_backup_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    sandbox_database_name: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=RestoreVerificationStatus.PENDING, nullable=False
    )
    sha256_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    schema_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tables_verified_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    table_row_counts_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    isolation_check_passed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    tested_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )

    backup_record: Mapped["PlatformBackupRecord"] = relationship(
        "PlatformBackupRecord", back_populates="restore_verifications"
    )


class PlatformCircuitBreakerState(BaseModel):
    """Persistent tracking of downstream dependency health and circuit breaker tripping."""

    __tablename__ = "platform_circuit_breaker_states"

    dependency_name: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    state: Mapped[str] = mapped_column(
        String(32), default=ReliabilityCircuitBreakerState.CLOSED, nullable=False
    )
    failure_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_failure_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_success_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_state_change_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    failure_threshold: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    recovery_timeout_seconds: Mapped[int] = mapped_column(
        Integer, default=60, nullable=False
    )


class PlatformStorageAuditRecord(BaseModel):
    """Audit log of storage integrity inspections detecting missing or orphaned objects."""

    __tablename__ = "platform_storage_audit_records"

    status: Mapped[str] = mapped_column(
        String(32), default=StorageAuditStatus.RUNNING, nullable=False
    )
    total_db_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_storage_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    missing_files_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    orphaned_files_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    missing_file_keys: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    orphaned_file_keys: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
