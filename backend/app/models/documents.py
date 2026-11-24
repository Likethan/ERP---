"""SQLAlchemy Models for the CampusOS Documents & Digital Records Domain."""

from datetime import datetime
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
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import SoftDeleteMixin, TenantScopedModel

# =============================================================================
# 1. DOCUMENT CATEGORY & TYPE
# =============================================================================


class DocumentCategory(TenantScopedModel):
    """Broad classification for institutional documents."""

    __tablename__ = "documents_categories"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_doc_categories_code"),
        Index("idx_doc_cat_tenant_code", "tenant_id", "code"),
        Index("idx_doc_cat_tenant_active", "tenant_id", "is_active"),
    )

    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    requires_verification: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    requires_expiry: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    applicable_roles: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    applicable_document_types: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    document_types: Mapped[list["DocumentType"]] = relationship(
        "DocumentType", back_populates="category", cascade="all, delete-orphan"
    )
    documents: Mapped[list["Document"]] = relationship("Document", back_populates="category")


class DocumentType(TenantScopedModel):
    """Specific document type definition within a category."""

    __tablename__ = "documents_types"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_doc_types_code"),
        Index("idx_doc_types_tenant_cat", "tenant_id", "category_id"),
        Index("idx_doc_types_tenant_active", "tenant_id", "is_active"),
    )

    category_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents_categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_required_by_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_expiry: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_verification: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allowed_owner_types: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    category: Mapped["DocumentCategory"] = relationship(
        "DocumentCategory", back_populates="document_types"
    )
    requirements: Mapped[list["DocumentRequirement"]] = relationship(
        "DocumentRequirement", back_populates="document_type", cascade="all, delete-orphan"
    )
    documents: Mapped[list["Document"]] = relationship("Document", back_populates="document_type")


class DocumentRequirement(TenantScopedModel):
    """Configurable data-driven document requirements per program, department, or role."""

    __tablename__ = "documents_requirements"
    __table_args__ = (
        Index("idx_doc_req_tenant_owner", "tenant_id", "owner_type"),
        Index("idx_doc_req_prog_dept", "tenant_id", "program_id", "department_id"),
    )

    document_type_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents_types.id", ondelete="RESTRICT"),
        nullable=False,
    )
    owner_type: Mapped[str] = mapped_column(
        String(32), default="STUDENT", nullable=False
    )  # STUDENT, FACULTY, STAFF, DEPARTMENT, INSTITUTION
    program_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_programs.id", ondelete="SET NULL"),
        nullable=True,
    )
    department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    academic_year_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_academic_years.id", ondelete="SET NULL"),
        nullable=True,
    )
    semester: Mapped[int | None] = mapped_column(Integer, nullable=True)
    role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationship
    document_type: Mapped["DocumentType"] = relationship(
        "DocumentType", back_populates="requirements"
    )


# =============================================================================
# 2. STORAGE RECORDS & DOCUMENTS
# =============================================================================


class StorageDocument(TenantScopedModel):
    """Metadata record referencing physical binary stored in object storage (MinIO/S3/Local)."""

    __tablename__ = "documents_storage_records"
    __table_args__ = (
        Index("idx_doc_storage_tenant_key", "tenant_id", "storage_key"),
    )

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


class Document(TenantScopedModel, SoftDeleteMixin):
    """Primary institutional digital document record."""

    __tablename__ = "documents_records"
    __table_args__ = (
        Index("idx_doc_tenant_owner", "tenant_id", "owner_type", "owner_id"),
        Index("idx_doc_tenant_status", "tenant_id", "status"),
        Index("idx_doc_tenant_category", "tenant_id", "category_id"),
        Index("idx_doc_tenant_type", "tenant_id", "document_type_id"),
        Index("idx_doc_tenant_expiry", "tenant_id", "expiry_date"),
        Index("idx_doc_tenant_created", "tenant_id", "created_at"),
    )

    category_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents_categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    document_type_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents_types.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_type: Mapped[str] = mapped_column(
        String(32), default="STUDENT", nullable=False
    )  # STUDENT, FACULTY, STAFF, INSTITUTION, DEPARTMENT
    owner_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    owner_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    owner_roll_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    owner_department: Mapped[str | None] = mapped_column(String(128), nullable=True)
    program: Mapped[str | None] = mapped_column(String(128), nullable=True)
    academic_year: Mapped[str | None] = mapped_column(String(32), nullable=True)
    semester: Mapped[int | None] = mapped_column(Integer, nullable=True)

    status: Mapped[str] = mapped_column(
        String(32), default="UPLOADED", nullable=False
    )  # REQUIRED, MISSING, UPLOADED, UNDER_REVIEW, VERIFIED, REJECTED, EXPIRED, ARCHIVED, REVOKED
    confidentiality: Mapped[str] = mapped_column(
        String(32), default="INTERNAL", nullable=False
    )  # PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED
    priority: Mapped[str] = mapped_column(
        String(32), default="NORMAL", nullable=False
    )  # LOW, NORMAL, HIGH, URGENT

    document_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    issue_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expiry_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    issuing_authority: Mapped[str | None] = mapped_column(String(255), nullable=True)

    file_reference: Mapped[str | None] = mapped_column(String(512), nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_size: Mapped[str | None] = mapped_column(String(32), nullable=True)
    file_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    uploaded_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    verified_by_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    assigned_reviewer_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    assigned_reviewer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    verification_checklist: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    category: Mapped["DocumentCategory"] = relationship("DocumentCategory", back_populates="documents")
    document_type: Mapped["DocumentType | None"] = relationship("DocumentType", back_populates="documents")
    verifications: Mapped[list["DocumentVerification"]] = relationship(
        "DocumentVerification", back_populates="document", cascade="all, delete-orphan"
    )
    history: Mapped[list["DocumentHistory"]] = relationship(
        "DocumentHistory", back_populates="document", cascade="all, delete-orphan"
    )
    versions: Mapped[list["DocumentVersion"]] = relationship(
        "DocumentVersion", back_populates="document", cascade="all, delete-orphan"
    )


class DocumentVerification(TenantScopedModel):
    """Audit record for individual review/verification events."""

    __tablename__ = "documents_verifications"
    __table_args__ = (
        Index("idx_doc_verif_tenant_doc", "tenant_id", "document_id"),
        Index("idx_doc_verif_reviewer", "tenant_id", "reviewer_id"),
    )

    document_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    reviewer_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    reviewer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # UNDER_REVIEW, VERIFIED, REJECTED
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    checklist_snapshot: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    document: Mapped["Document"] = relationship("Document", back_populates="verifications")


class DocumentHistory(TenantScopedModel):
    """Audit trail and activity timeline item for a document."""

    __tablename__ = "documents_history"
    __table_args__ = (
        Index("idx_doc_hist_tenant_doc", "tenant_id", "document_id", "created_at"),
    )

    document_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    performed_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    performed_by_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    document: Mapped["Document"] = relationship("Document", back_populates="history")


class DocumentVersion(TenantScopedModel):
    """Historical version snapshot when a document file is replaced."""

    __tablename__ = "documents_versions"
    __table_args__ = (
        UniqueConstraint("tenant_id", "document_id", "version_number", name="uq_doc_versions_num"),
        Index("idx_doc_vers_tenant_doc", "tenant_id", "document_id"),
    )

    document_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    file_reference: Mapped[str] = mapped_column(String(512), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    file_size: Mapped[str] = mapped_column(String(32), nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    uploaded_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    metadata_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    document: Mapped["Document"] = relationship("Document", back_populates="versions")


# =============================================================================
# 3. CERTIFICATE TEMPLATES, REQUESTS & ISSUANCE
# =============================================================================


class CertificateTemplate(TenantScopedModel):
    """Institutional template configuration for digital credentials and certificates."""

    __tablename__ = "documents_certificate_templates"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_cert_templates_code"),
        Index("idx_cert_tmpl_tenant_type", "tenant_id", "certificate_type"),
        Index("idx_cert_tmpl_tenant_status", "tenant_id", "status"),
    )

    code: Mapped[str] = mapped_column(String(64), nullable=False)
    template_name: Mapped[str] = mapped_column(String(255), nullable=False)
    certificate_type: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # BONAFIDE, COURSE_COMPLETION, TRANSFER, CONDUCT, CHARACTER, ATTENDANCE, INTERNSHIP, PLACEMENT, PARTICIPATION, OTHER
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    applicable_audience: Mapped[list] = mapped_column(
        JSONB, default=lambda: ["STUDENT"], nullable=False
    )  # ["STUDENT", "FACULTY", "STAFF", "ALL"]
    status: Mapped[str] = mapped_column(
        String(32), default="ACTIVE", nullable=False
    )  # DRAFT, ACTIVE, INACTIVE, ARCHIVED
    current_version: Mapped[str] = mapped_column(String(32), default="1.0", nullable=False)
    template_body: Mapped[str] = mapped_column(Text, nullable=False)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    versions: Mapped[list["CertificateTemplateVersion"]] = relationship(
        "CertificateTemplateVersion", back_populates="template", cascade="all, delete-orphan"
    )
    fields: Mapped[list["CertificateTemplateField"]] = relationship(
        "CertificateTemplateField", back_populates="template", cascade="all, delete-orphan"
    )
    requests: Mapped[list["CertificateRequest"]] = relationship(
        "CertificateRequest", back_populates="template"
    )


class CertificateTemplateVersion(TenantScopedModel):
    """Immutable version history for a certificate template."""

    __tablename__ = "documents_certificate_template_versions"
    __table_args__ = (
        Index("idx_cert_ver_tenant_tmpl", "tenant_id", "template_id"),
    )

    template_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents_certificate_templates.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_string: Mapped[str] = mapped_column(String(32), nullable=False)
    template_body: Mapped[str] = mapped_column(Text, nullable=False)
    changelog: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    published_by_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    template: Mapped["CertificateTemplate"] = relationship(
        "CertificateTemplate", back_populates="versions"
    )


class CertificateTemplateField(TenantScopedModel):
    """Dynamic placeholders and fields bound to a certificate template."""

    __tablename__ = "documents_certificate_template_fields"
    __table_args__ = (
        Index("idx_cert_field_tenant_tmpl", "tenant_id", "template_id"),
    )

    template_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents_certificate_templates.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    field_type: Mapped[str] = mapped_column(
        String(32), default="TEXT", nullable=False
    )  # TEXT, NUMBER, DATE, SYSTEM_VARIABLE
    required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    system_variable_mapping: Mapped[str | None] = mapped_column(String(128), nullable=True)
    default_value: Mapped[str | None] = mapped_column(String(255), nullable=True)

    template: Mapped["CertificateTemplate"] = relationship(
        "CertificateTemplate", back_populates="fields"
    )


class CertificateRequest(TenantScopedModel):
    """Official application by a student for institutional certificate issuance."""

    __tablename__ = "documents_certificate_requests"
    __table_args__ = (
        Index("idx_cert_req_tenant_student", "tenant_id", "student_id"),
        Index("idx_cert_req_tenant_status", "tenant_id", "status"),
        Index("idx_cert_req_tenant_created", "tenant_id", "created_at"),
    )

    request_id: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g. REQ-2026-0001
    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    student_name: Mapped[str] = mapped_column(String(255), nullable=False)
    roll_number: Mapped[str] = mapped_column(String(64), nullable=False)
    program: Mapped[str] = mapped_column(String(128), nullable=False)
    department: Mapped[str] = mapped_column(String(128), nullable=False)

    template_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents_certificate_templates.id", ondelete="RESTRICT"),
        nullable=False,
    )
    template_version_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents_certificate_template_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    certificate_type: Mapped[str] = mapped_column(String(64), nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    required_by_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    status: Mapped[str] = mapped_column(
        String(32), default="SUBMITTED", nullable=False
    )  # DRAFT, SUBMITTED, UNDER_REVIEW, APPROVED, REJECTED, ISSUED, CANCELLED

    reviewer_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    issued_certificate_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    issued_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finance_reference_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    validation_checks: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    timeline: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Relationship
    template: Mapped["CertificateTemplate"] = relationship(
        "CertificateTemplate", back_populates="requests"
    )


class IssuedCertificate(TenantScopedModel):
    """Cryptographically verifiable digital credential issued to an individual."""

    __tablename__ = "documents_issued_certificates"
    __table_args__ = (
        UniqueConstraint("tenant_id", "certificate_number", name="uq_issued_certs_number"),
        Index("idx_issued_cert_tenant_recip", "tenant_id", "recipient_id"),
        Index("idx_issued_cert_tenant_status", "tenant_id", "status"),
        Index("idx_issued_cert_tenant_hash", "tenant_id", "verification_hash"),
    )

    request_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents_certificate_requests.id", ondelete="SET NULL"),
        nullable=True,
    )
    certificate_number: Mapped[str] = mapped_column(String(64), nullable=False)
    certificate_type: Mapped[str] = mapped_column(String(64), nullable=False)

    recipient_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    recipient_name: Mapped[str] = mapped_column(String(255), nullable=False)
    recipient_roll_number: Mapped[str] = mapped_column(String(64), nullable=False)
    recipient_program: Mapped[str] = mapped_column(String(128), nullable=False)
    recipient_department: Mapped[str] = mapped_column(String(128), nullable=False)

    template_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents_certificate_templates.id", ondelete="RESTRICT"),
        nullable=False,
    )
    template_version_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents_certificate_template_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    template_version_string: Mapped[str] = mapped_column(String(32), default="1.0", nullable=False)
    issuing_authority: Mapped[str] = mapped_column(String(255), nullable=False)
    issue_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    status: Mapped[str] = mapped_column(String(32), default="ISSUED", nullable=False)  # ISSUED, REVOKED
    verification_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    qr_verification_url: Mapped[str] = mapped_column(String(512), nullable=False)

    storage_document_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents_storage_records.id", ondelete="SET NULL"),
        nullable=True,
    )
    file_reference: Mapped[str | None] = mapped_column(String(512), nullable=True)

    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    revocation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


# =============================================================================
# 4. INSTITUTIONAL RECORDS & GOVERNANCE
# =============================================================================


class InstitutionalRecord(TenantScopedModel):
    """Official institutional governance records (Accreditations, Policies, Circulars)."""

    __tablename__ = "documents_institutional_records"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_institutional_records_code"),
        Index("idx_inst_rec_tenant_code", "tenant_id", "code"),
        Index("idx_inst_rec_tenant_cat", "tenant_id", "category"),
        Index("idx_inst_rec_tenant_status", "tenant_id", "status"),
        Index("idx_inst_rec_tenant_conf", "tenant_id", "confidentiality"),
    )

    record_name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)  # REC-GOV-001
    category: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # ACCREDITATION, POLICY, CIRCULAR, APPROVAL, AFFILIATION, INSTITUTIONAL_CERTIFICATE, REGULATORY, MEETING, ADMINISTRATIVE, OTHER
    owner_department: Mapped[str] = mapped_column(String(128), nullable=False)
    confidentiality: Mapped[str] = mapped_column(
        String(32), default="INTERNAL", nullable=False
    )  # PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED
    status: Mapped[str] = mapped_column(
        String(32), default="ACTIVE", nullable=False
    )  # ACTIVE, EXPIRED, ARCHIVED, REVOKED

    created_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    issuing_authority: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reference_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    file_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    file_size: Mapped[str | None] = mapped_column(String(32), nullable=True)
    file_reference: Mapped[str | None] = mapped_column(String(512), nullable=True)

    related_document_ids: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    related_documents: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    history: Mapped[list["InstitutionalRecordHistory"]] = relationship(
        "InstitutionalRecordHistory", back_populates="record", cascade="all, delete-orphan"
    )


class InstitutionalRecordHistory(TenantScopedModel):
    """Forensic modification and access history for institutional governance records."""

    __tablename__ = "documents_institutional_record_history"
    __table_args__ = (
        Index("idx_inst_hist_tenant_rec", "tenant_id", "record_id", "created_at"),
    )

    record_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents_institutional_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    performed_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    performed_by_name: Mapped[str] = mapped_column(String(255), nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)

    record: Mapped["InstitutionalRecord"] = relationship(
        "InstitutionalRecord", back_populates="history"
    )


# =============================================================================
# 5. LEGACY PROFILE RECORD COMPATIBILITY
# =============================================================================


class StudentDocumentRecord(TenantScopedModel):
    """Legacy compatibility bridge for student-linked storage documents."""

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
    document_type: Mapped[str] = mapped_column(String(64), nullable=False)
    verification_status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    verified_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class FacultyDocumentRecord(TenantScopedModel):
    """Legacy compatibility bridge for faculty-linked storage documents."""

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
    document_type: Mapped[str] = mapped_column(String(64), nullable=False)
