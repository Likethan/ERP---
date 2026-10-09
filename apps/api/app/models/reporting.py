"""Reporting & Analytics Domain Models for CampusOS.

Provides relational schema for Report Definitions, Immutable Versions,
Report Executions, Exports, and User Saved Reports.
Enforces multi-tenant isolation, role-based visibility, and reproducible reporting.
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

from app.models.base import BaseModel, TenantScopedModel


class ReportStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class ReportVisibility(StrEnum):
    PRIVATE = "PRIVATE"
    ROLE = "ROLE"
    TENANT = "TENANT"
    SYSTEM = "SYSTEM"


class ReportExecutionStatus(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class ReportExportFormat(StrEnum):
    CSV = "CSV"
    XLSX = "XLSX"
    PDF = "PDF"
    JSON = "JSON"


class ReportDefinition(BaseModel):
    """Institutional Report Definition with domain grouping and access controls."""

    __tablename__ = "reporting_definitions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_report_tenant_code"),
        Index("ix_report_tenant_domain_status", "tenant_id", "domain", "status"),
    )

    tenant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    domain: Mapped[str] = mapped_column(
        String(32), nullable=False, default="GENERAL"
    )  # PEOPLE, ACADEMICS, ATTENDANCE, EXAMINATIONS, FINANCE, PLACEMENT, CAMPUS, INFRASTRUCTURE, DOCUMENTS, CROSS_DOMAIN
    category: Mapped[str] = mapped_column(String(64), nullable=False, default="OPERATIONAL")
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=ReportStatus.DRAFT
    )
    visibility: Mapped[str] = mapped_column(
        String(32), nullable=False, default=ReportVisibility.ROLE
    )
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allowed_roles: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list
    )  # Empty implies open to all authorized report viewers in tenant

    active_version_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    updated_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    versions: Mapped[list["ReportVersion"]] = relationship(
        "ReportVersion",
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="ReportVersion.version_number",
    )
    executions: Mapped[list["ReportExecution"]] = relationship(
        "ReportExecution",
        back_populates="report",
        cascade="all, delete-orphan",
    )
    saved_instances: Mapped[list["SavedReport"]] = relationship(
        "SavedReport",
        back_populates="report",
        cascade="all, delete-orphan",
    )

    @property
    def active_version(self) -> int:
        if self.active_version_id:
            for v in self.versions:
                if v.id == self.active_version_id:
                    return v.version_number
        for v in self.versions:
            if v.is_active:
                return v.version_number
        return 1

    @active_version.setter
    def active_version(self, value: int) -> None:
        pass


class ReportVersion(BaseModel):
    """Immutable version of a report query specification."""

    __tablename__ = "reporting_versions"
    __table_args__ = (
        UniqueConstraint("report_id", "version_number", name="uq_report_version_number"),
        Index("ix_report_version_lookup", "report_id", "is_active"),
    )

    tenant_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_institutions.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    report_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("reporting_definitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    change_summary: Mapped[str | None] = mapped_column(String(255), nullable=True)
    query_spec_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    report: Mapped["ReportDefinition"] = relationship(
        "ReportDefinition", back_populates="versions"
    )

    @property
    def query_spec(self) -> dict[str, Any]:
        return self.query_spec_json if isinstance(self.query_spec_json, dict) else {}

    @query_spec.setter
    def query_spec(self, value: dict[str, Any]) -> None:
        self.query_spec_json = value


class ReportExecution(TenantScopedModel):
    """Execution audit and state tracking for a report or analytics query."""

    __tablename__ = "reporting_executions"
    __table_args__ = (
        Index("ix_report_exec_tenant_status", "tenant_id", "status"),
        Index("ix_report_exec_created_at", "tenant_id", "created_at"),
        Index("ix_report_exec_correlation", "tenant_id", "correlation_id"),
    )

    report_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("reporting_definitions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    report_version_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("reporting_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    requested_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32), default=ReportExecutionStatus.QUEUED, nullable=False
    )
    query_spec_snapshot: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    row_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    execution_time_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False)
    is_snapshot: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    snapshot_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    report: Mapped["ReportDefinition | None"] = relationship(
        "ReportDefinition", back_populates="executions"
    )
    exports: Mapped[list["ReportExport"]] = relationship(
        "ReportExport", back_populates="execution", cascade="all, delete-orphan"
    )


class ReportExport(TenantScopedModel):
    """Generated downloadable export artifact with storage keys and expiration."""

    __tablename__ = "reporting_exports"
    __table_args__ = (
        Index("ix_report_export_tenant_expires", "tenant_id", "expires_at"),
    )

    execution_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("reporting_executions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    export_format: Mapped[str] = mapped_column(
        String(16), nullable=False, default=ReportExportFormat.CSV
    )
    storage_key: Mapped[str] = mapped_column(String(255), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    download_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    execution: Mapped["ReportExecution"] = relationship(
        "ReportExecution", back_populates="exports"
    )

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        exp = self.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=UTC)
        return datetime.now(UTC) > exp


class SavedReport(TenantScopedModel):
    """Personalized or shared saved report configuration for rapid access."""

    __tablename__ = "reporting_saved_reports"
    __table_args__ = (
        Index("ix_saved_report_user_tenant", "tenant_id", "user_id"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    report_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("reporting_definitions.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    query_spec_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    report: Mapped["ReportDefinition | None"] = relationship(
        "ReportDefinition", back_populates="saved_instances"
    )

    @property
    def query_spec(self) -> dict[str, Any]:
        return self.query_spec_json if isinstance(self.query_spec_json, dict) else {}

    @query_spec.setter
    def query_spec(self, value: dict[str, Any]) -> None:
        self.query_spec_json = value
