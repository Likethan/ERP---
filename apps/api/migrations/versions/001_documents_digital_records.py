"""Create documents and digital records tables

Revision ID: 001_documents_digital_records
Revises: 
Create Date: 2026-10-03 21:50:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "001_documents_digital_records"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Document Categories
    op.create_table(
        "documents_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("requires_verification", sa.Boolean(), default=True, nullable=False),
        sa.Column("requires_expiry", sa.Boolean(), default=False, nullable=False),
        sa.Column("applicable_roles", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("applicable_document_types", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_doc_categories_code"),
    )
    op.create_index("idx_doc_cat_tenant_code", "documents_categories", ["tenant_id", "code"])
    op.create_index("idx_doc_cat_tenant_active", "documents_categories", ["tenant_id", "is_active"])

    # 2. Document Types
    op.create_table(
        "documents_types",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "category_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents_categories.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_required_by_default", sa.Boolean(), default=False, nullable=False),
        sa.Column("requires_expiry", sa.Boolean(), default=False, nullable=False),
        sa.Column("requires_verification", sa.Boolean(), default=True, nullable=False),
        sa.Column("allowed_owner_types", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_doc_types_code"),
    )
    op.create_index("idx_doc_types_tenant_cat", "documents_types", ["tenant_id", "category_id"])
    op.create_index("idx_doc_types_tenant_active", "documents_types", ["tenant_id", "is_active"])

    # 3. Document Requirements
    op.create_table(
        "documents_requirements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "document_type_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents_types.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("owner_type", sa.String(32), default="STUDENT", nullable=False),
        sa.Column("program_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_programs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_departments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("academic_year_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_academic_years.id", ondelete="SET NULL"), nullable=True),
        sa.Column("semester", sa.Integer(), nullable=True),
        sa.Column("role", sa.String(64), nullable=True),
        sa.Column("is_required", sa.Boolean(), default=True, nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_doc_req_tenant_owner", "documents_requirements", ["tenant_id", "owner_type"])

    # 4. Storage Records
    op.create_table(
        "documents_storage_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "category_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents_categories.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(128), nullable=False),
        sa.Column("storage_bucket", sa.String(128), nullable=False),
        sa.Column("storage_key", sa.String(255), nullable=False, unique=True),
        sa.Column("checksum_sha256", sa.String(64), nullable=False),
        sa.Column(
            "uploaded_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 5. Documents Records
    op.create_table(
        "documents_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "category_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents_categories.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "document_type_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents_types.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("owner_type", sa.String(32), default="STUDENT", nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_name", sa.String(255), nullable=True),
        sa.Column("owner_roll_number", sa.String(64), nullable=True),
        sa.Column("owner_department", sa.String(128), nullable=True),
        sa.Column("program", sa.String(128), nullable=True),
        sa.Column("academic_year", sa.String(32), nullable=True),
        sa.Column("semester", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(32), default="UPLOADED", nullable=False),
        sa.Column("confidentiality", sa.String(32), default="INTERNAL", nullable=False),
        sa.Column("priority", sa.String(32), default="NORMAL", nullable=False),
        sa.Column("document_number", sa.String(128), nullable=True),
        sa.Column("issue_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expiry_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("issuing_authority", sa.String(255), nullable=True),
        sa.Column("file_reference", sa.String(512), nullable=True),
        sa.Column("file_name", sa.String(255), nullable=True),
        sa.Column("file_size", sa.String(32), nullable=True),
        sa.Column("file_type", sa.String(128), nullable=True),
        sa.Column("checksum", sa.String(64), nullable=True),
        sa.Column("version", sa.Integer(), default=1, nullable=False),
        sa.Column("uploaded_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("verified_by_name", sa.String(255), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("assigned_reviewer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("assigned_reviewer_name", sa.String(255), nullable=True),
        sa.Column("verification_checklist", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_doc_tenant_owner", "documents_records", ["tenant_id", "owner_type", "owner_id"])
    op.create_index("idx_doc_tenant_status", "documents_records", ["tenant_id", "status"])
    op.create_index("idx_doc_tenant_category", "documents_records", ["tenant_id", "category_id"])
    op.create_index("idx_doc_tenant_expiry", "documents_records", ["tenant_id", "expiry_date"])

    # 6. Document Verifications
    op.create_table(
        "documents_verifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents_records.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "reviewer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("reviewer_name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("checklist_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_doc_verif_tenant_doc", "documents_verifications", ["tenant_id", "document_id"])

    # 7. Document History
    op.create_table(
        "documents_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents_records.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("performed_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("performed_by_name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(64), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_doc_hist_tenant_doc", "documents_history", ["tenant_id", "document_id", "created_at"])

    # 8. Document Versions
    op.create_table(
        "documents_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents_records.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("file_reference", sa.String(512), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(128), nullable=False),
        sa.Column("file_size", sa.String(32), nullable=False),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("uploaded_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("metadata_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "document_id", "version_number", name="uq_doc_versions_num"),
    )

    # 9. Certificate Templates
    op.create_table(
        "documents_certificate_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("template_name", sa.String(255), nullable=False),
        sa.Column("certificate_type", sa.String(64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("applicable_audience", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(32), default="ACTIVE", nullable=False),
        sa.Column("current_version", sa.String(32), default="1.0", nullable=False),
        sa.Column("template_body", sa.Text(), nullable=False),
        sa.Column("usage_count", sa.Integer(), default=0, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_cert_templates_code"),
    )

    # 10. Certificate Template Versions
    op.create_table(
        "documents_certificate_template_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents_certificate_templates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_string", sa.String(32), nullable=False),
        sa.Column("template_body", sa.Text(), nullable=False),
        sa.Column("changelog", sa.Text(), nullable=True),
        sa.Column("published_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("published_by_name", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 11. Certificate Template Fields
    op.create_table(
        "documents_certificate_template_fields",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents_certificate_templates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("label", sa.String(128), nullable=False),
        sa.Column("field_type", sa.String(32), default="TEXT", nullable=False),
        sa.Column("required", sa.Boolean(), default=True, nullable=False),
        sa.Column("system_variable_mapping", sa.String(128), nullable=True),
        sa.Column("default_value", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 12. Certificate Requests
    op.create_table(
        "documents_certificate_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("request_id", sa.String(64), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_students.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("student_name", sa.String(255), nullable=False),
        sa.Column("roll_number", sa.String(64), nullable=False),
        sa.Column("program", sa.String(128), nullable=False),
        sa.Column("department", sa.String(128), nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents_certificate_templates.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("template_version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents_certificate_template_versions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("certificate_type", sa.String(64), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("required_by_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(32), default="SUBMITTED", nullable=False),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewer_name", sa.String(255), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("issued_certificate_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("issued_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finance_reference_id", sa.String(64), nullable=True),
        sa.Column("validation_checks", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("timeline", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_cert_req_tenant_student", "documents_certificate_requests", ["tenant_id", "student_id"])
    op.create_index("idx_cert_req_tenant_status", "documents_certificate_requests", ["tenant_id", "status"])

    # 13. Issued Certificates
    op.create_table(
        "documents_issued_certificates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents_certificate_requests.id", ondelete="SET NULL"), nullable=True),
        sa.Column("certificate_number", sa.String(64), nullable=False),
        sa.Column("certificate_type", sa.String(64), nullable=False),
        sa.Column("recipient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recipient_name", sa.String(255), nullable=False),
        sa.Column("recipient_roll_number", sa.String(64), nullable=False),
        sa.Column("recipient_program", sa.String(128), nullable=False),
        sa.Column("recipient_department", sa.String(128), nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents_certificate_templates.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("template_version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents_certificate_template_versions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("template_version_string", sa.String(32), default="1.0", nullable=False),
        sa.Column("issuing_authority", sa.String(255), nullable=False),
        sa.Column("issue_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(32), default="ISSUED", nullable=False),
        sa.Column("verification_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("qr_verification_url", sa.String(512), nullable=False),
        sa.Column("storage_document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents_storage_records.id", ondelete="SET NULL"), nullable=True),
        sa.Column("file_reference", sa.String(512), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("revocation_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "certificate_number", name="uq_issued_certs_number"),
    )
    op.create_index("idx_issued_cert_tenant_recip", "documents_issued_certificates", ["tenant_id", "recipient_id"])
    op.create_index("idx_issued_cert_tenant_status", "documents_issued_certificates", ["tenant_id", "status"])

    # 14. Institutional Records
    op.create_table(
        "documents_institutional_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("record_name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("owner_department", sa.String(128), nullable=False),
        sa.Column("confidentiality", sa.String(32), default="INTERNAL", nullable=False),
        sa.Column("status", sa.String(32), default="ACTIVE", nullable=False),
        sa.Column("created_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("issuing_authority", sa.String(255), nullable=True),
        sa.Column("reference_number", sa.String(128), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("file_type", sa.String(64), nullable=True),
        sa.Column("file_size", sa.String(32), nullable=True),
        sa.Column("file_reference", sa.String(512), nullable=True),
        sa.Column("related_document_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("related_documents", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_institutional_records_code"),
    )
    op.create_index("idx_inst_rec_tenant_code", "documents_institutional_records", ["tenant_id", "code"])
    op.create_index("idx_inst_rec_tenant_cat", "documents_institutional_records", ["tenant_id", "category"])

    # 15. Institutional Record History
    op.create_table(
        "documents_institutional_record_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "record_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents_institutional_records.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("performed_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("performed_by_name", sa.String(255), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("documents_institutional_record_history")
    op.drop_table("documents_institutional_records")
    op.drop_table("documents_issued_certificates")
    op.drop_table("documents_certificate_requests")
    op.drop_table("documents_certificate_template_fields")
    op.drop_table("documents_certificate_template_versions")
    op.drop_table("documents_certificate_templates")
    op.drop_table("documents_versions")
    op.drop_table("documents_history")
    op.drop_table("documents_verifications")
    op.drop_table("documents_records")
    op.drop_table("documents_storage_records")
    op.drop_table("documents_requirements")
    op.drop_table("documents_types")
    op.drop_table("documents_categories")
