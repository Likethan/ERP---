from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantScopedModel


class DocumentCategory(TenantScopedModel):
    """Classification for institutional documents."""

    __tablename__ = "documents_categories"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_doc_categories_code"),)

    # Codes: ADMISSION, IDENTITY, DEGREE, POLICY
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)


class StorageDocument(TenantScopedModel):
    """Metadata record referencing physical binary stored in object storage (MinIO/S3)."""

    __tablename__ = "documents_storage_records"

    category_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents_categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    storage_bucket: Mapped[str] = mapped_column(String(128), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    uploaded_by_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )


class StudentDocumentRecord(TenantScopedModel):
    """Document linked to a student with verification status."""

    __tablename__ = "documents_student_records"

    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    storage_document_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents_storage_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_type: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # AADHAR, 10TH_MARKSHEET, 12TH_MARKSHEET, TRANSFER_CERT
    verification_status: Mapped[str] = mapped_column(
        String(32), default="PENDING", nullable=False
    )  # PENDING, VERIFIED, REJECTED
    verified_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class FacultyDocumentRecord(TenantScopedModel):
    """Employment contract or credential document linked to faculty."""

    __tablename__ = "documents_faculty_records"

    faculty_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_faculty.id", ondelete="RESTRICT"),
        nullable=False,
    )
    storage_document_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents_storage_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_type: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # CONTRACT, DEGREE_CERT, PUBLICATION_PROOF


class CertificateTemplate(TenantScopedModel):
    """HTML/Jinja layout template for digital certificates."""

    __tablename__ = "documents_certificate_templates"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_cert_templates_code"),)

    code: Mapped[str] = mapped_column(String(32), nullable=False)  # BONAFIDE, STUDY, COMPLETION
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    template_body: Mapped[str] = mapped_column(Text, nullable=False)


class IssuedCertificate(TenantScopedModel):
    """Cryptographically verifiable digital credential issued to a student."""

    __tablename__ = "documents_issued_certificates"
    __table_args__ = (
        UniqueConstraint("tenant_id", "certificate_number", name="uq_issued_certs_number"),
    )

    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    template_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents_certificate_templates.id", ondelete="RESTRICT"),
        nullable=False,
    )
    certificate_number: Mapped[str] = mapped_column(String(64), nullable=False)
    issue_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    verification_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    storage_document_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents_storage_records.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
