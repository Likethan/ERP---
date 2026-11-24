"""Enterprise Records Lifecycle, Retention, Archival & Legal Hold Management (Step 41).

Revision ID: 027_enterprise_records_lifecycle_retention_archival
Revises: 026_enterprise_data_import_migration_reconciliation
Create Date: 2026-10-18 18:25:00.000000

Creates normalized tables for:
- records_categories: Institutional record categories and statutory classifications
- records_retention_policies: Configurable retention schedules, triggers, and disposition rules
- records_retention_policy_versions: Immutable version history of retention policies
- records_registry: Centralized registry indexing authoritative domain records
- records_lifecycle_history: Append-only audit trail of 12-state lifecycle transitions
- records_archival_manifests: Cryptographic archival manifests referencing cold storage
- records_archival_access_logs: Controlled access and retrieval tracking for archived records
- records_legal_holds: High-precedence institutional administrative & legal holds
- records_legal_hold_associations: Scoped associations between legal holds and records
- records_disposition_requests: Formal disposition requests and two-person approval tracking
- records_disposition_items: Itemized disposition outcome evaluations
- records_disposition_certificates: Tamper-evident proof of completed record disposition
- records_lifecycle_scheduled_runs: Scheduled background job execution metrics
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "027_enterprise_records_lifecycle_retention_archival"
down_revision = "026_enterprise_data_import_migration_reconciliation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Record Categories
    op.create_table(
        "records_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("confidentiality", sa.String(32), nullable=False, server_default="CONFIDENTIAL"),
        sa.Column("default_retention_years", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("statutory_authority", sa.String(128), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_records_cat_tenant_code"),
    )
    op.create_index("ix_records_cat_tenant_active", "records_categories", ["tenant_id", "is_active"])

    # 2. Retention Policies
    op.create_table(
        "records_retention_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category_code", sa.String(64), nullable=False),
        sa.Column("scope", sa.String(32), nullable=False, server_default="CATEGORY"),
        sa.Column("scope_target", sa.String(128), nullable=True),
        sa.Column("retention_duration", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("retention_unit", sa.String(16), nullable=False, server_default="YEARS"),
        sa.Column("trigger_event", sa.String(32), nullable=False, server_default="CREATION"),
        sa.Column("review_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("archive_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("disposition_method", sa.String(32), nullable=False, server_default="ANONYMIZE"),
        sa.Column("approval_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("effective_from", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("effective_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT"),
        sa.Column("current_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("approved_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_records_pol_tenant_code"),
    )
    op.create_index("ix_records_pol_tenant_status", "records_retention_policies", ["tenant_id", "status"])
    op.create_index("ix_records_pol_tenant_cat", "records_retention_policies", ["tenant_id", "category_code"])

    # 3. Retention Policy Versions
    op.create_table(
        "records_retention_policy_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("policy_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("records_retention_policies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="PUBLISHED"),
        sa.Column("rules_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("change_summary", sa.String(255), nullable=True),
        sa.Column("effective_from", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("effective_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("policy_id", "version_number", name="uq_records_pol_ver_num"),
    )
    op.create_index("ix_records_pol_ver_tenant", "records_retention_policy_versions", ["tenant_id", "policy_id"])

    # 4. Records Registry
    op.create_table(
        "records_registry",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("record_number", sa.String(64), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("records_categories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("category_code", sa.String(64), nullable=False),
        sa.Column("source_module", sa.String(64), nullable=False),
        sa.Column("source_record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_reference", sa.String(128), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("owner_department_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_departments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("responsible_department", sa.String(128), nullable=True),
        sa.Column("confidentiality_level", sa.String(32), nullable=False, server_default="CONFIDENTIAL"),
        sa.Column("lifecycle_state", sa.String(32), nullable=False, server_default="ACTIVE"),
        sa.Column("policy_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("records_retention_policies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("policy_version", sa.Integer(), nullable=True),
        sa.Column("record_created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("retention_start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("calculated_review_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("calculated_eligibility_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("disposed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_held", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("active_hold_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("storage_reference", sa.String(512), nullable=True),
        sa.Column("checksum_sha256", sa.String(64), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "source_module", "source_record_id", name="uq_records_reg_tenant_src"),
        sa.UniqueConstraint("tenant_id", "record_number", name="uq_records_reg_rec_num"),
    )
    op.create_index("ix_records_reg_tenant_state", "records_registry", ["tenant_id", "lifecycle_state"])
    op.create_index("ix_records_reg_tenant_cat", "records_registry", ["tenant_id", "category_code"])
    op.create_index("ix_records_reg_tenant_held", "records_registry", ["tenant_id", "is_held"])
    op.create_index("ix_records_reg_tenant_elig", "records_registry", ["tenant_id", "calculated_eligibility_date"])

    # 5. Lifecycle History
    op.create_table(
        "records_lifecycle_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("record_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("records_registry.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_state", sa.String(32), nullable=False),
        sa.Column("to_state", sa.String(32), nullable=False),
        sa.Column("trigger_action", sa.String(64), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("actor_role", sa.String(64), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("ix_records_hist_tenant_rec", "records_lifecycle_history", ["tenant_id", "record_id"])
    op.create_index("ix_records_hist_created", "records_lifecycle_history", ["tenant_id", "created_at"])

    # 6. Archival Manifests
    op.create_table(
        "records_archival_manifests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("manifest_number", sa.String(64), nullable=False),
        sa.Column("record_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("records_registry.id", ondelete="CASCADE"), nullable=False),
        sa.Column("archive_location", sa.String(128), nullable=False, server_default="S3_COLD_TIER"),
        sa.Column("archive_storage_key", sa.String(512), nullable=False),
        sa.Column("original_storage_key", sa.String(512), nullable=True),
        sa.Column("checksum_sha256", sa.String(64), nullable=False),
        sa.Column("verified_checksum", sa.String(64), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(32), nullable=False, server_default="STORED"),
        sa.Column("archived_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("retrieval_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_retrieved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "record_id", name="uq_records_arch_rec"),
        sa.UniqueConstraint("tenant_id", "manifest_number", name="uq_records_arch_manifest_num"),
    )
    op.create_index("ix_records_arch_tenant_status", "records_archival_manifests", ["tenant_id", "status"])

    # 7. Archival Access Logs
    op.create_table(
        "records_archival_access_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("manifest_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("records_archival_manifests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("access_type", sa.String(32), nullable=False),
        sa.Column("justification", sa.Text(), nullable=False),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("accessed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("ix_records_arch_log_tenant", "records_archival_access_logs", ["tenant_id", "manifest_id"])

    # 8. Legal Holds
    op.create_table(
        "records_legal_holds",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("hold_number", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("case_reference", sa.String(128), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("hold_authority", sa.String(128), nullable=False, server_default="INSTITUTIONAL_COMPLIANCE"),
        sa.Column("scope_type", sa.String(32), nullable=False, server_default="CATEGORY"),
        sa.Column("scope_value", sa.String(128), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("custodians_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default="[]"),
        sa.Column("effective_from", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("review_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("released_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("release_reason", sa.Text(), nullable=True),
        sa.Column("records_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "hold_number", name="uq_records_hold_num"),
    )
    op.create_index("ix_records_hold_tenant_status", "records_legal_holds", ["tenant_id", "status"])
    op.create_index("ix_records_hold_scope", "records_legal_holds", ["tenant_id", "scope_type", "scope_value"])

    # 9. Legal Hold Associations
    op.create_table(
        "records_legal_hold_associations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("hold_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("records_legal_holds.id", ondelete="CASCADE"), nullable=False),
        sa.Column("record_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("records_registry.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"),
        sa.Column("applied_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("applied_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("released_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("hold_id", "record_id", name="uq_records_hold_assoc"),
    )
    op.create_index("ix_records_assoc_tenant_rec", "records_legal_hold_associations", ["tenant_id", "record_id"])

    # 10. Disposition Requests
    op.create_table(
        "records_disposition_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("request_number", sa.String(64), nullable=False),
        sa.Column("policy_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("records_retention_policies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("policy_version", sa.Integer(), nullable=True),
        sa.Column("category_code", sa.String(64), nullable=True),
        sa.Column("requested_disposition_method", sa.String(32), nullable=False, server_default="ANONYMIZE"),
        sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT"),
        sa.Column("records_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("preview_stats_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default="{}"),
        sa.Column("justification", sa.Text(), nullable=False),
        sa.Column("requested_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("reviewed_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "request_number", name="uq_records_disp_req_num"),
    )
    op.create_index("ix_records_disp_tenant_status", "records_disposition_requests", ["tenant_id", "status"])

    # 11. Disposition Items
    op.create_table(
        "records_disposition_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("records_disposition_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("record_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("records_registry.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="ELIGIBLE"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("disposed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("request_id", "record_id", name="uq_records_disp_item"),
    )
    op.create_index("ix_records_disp_item_status", "records_disposition_items", ["tenant_id", "status"])

    # 12. Disposition Certificates
    op.create_table(
        "records_disposition_certificates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("certificate_number", sa.String(64), nullable=False),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("records_disposition_requests.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("disposition_method", sa.String(32), nullable=False),
        sa.Column("total_records_destroyed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_records_anonymized", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_records_archived", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("disposition_manifest_hash", sa.String(64), nullable=False),
        sa.Column("executed_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("approved_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("executed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("certificate_metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "certificate_number", name="uq_records_disp_cert_num"),
    )
    op.create_index("ix_records_disp_cert_req", "records_disposition_certificates", ["tenant_id", "request_id"])

    # 13. Scheduled Lifecycle Runs
    op.create_table(
        "records_lifecycle_scheduled_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("job_type", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="RUNNING"),
        sa.Column("records_evaluated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_transitioned", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_flagged_review", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_blocked", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("summary_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default="{}"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("ix_records_sched_tenant_type", "records_lifecycle_scheduled_runs", ["tenant_id", "job_type"])
    op.create_index("ix_records_sched_started", "records_lifecycle_scheduled_runs", ["tenant_id", "started_at"])


def downgrade() -> None:
    op.drop_table("records_lifecycle_scheduled_runs")
    op.drop_table("records_disposition_certificates")
    op.drop_table("records_disposition_items")
    op.drop_table("records_disposition_requests")
    op.drop_table("records_legal_hold_associations")
    op.drop_table("records_legal_holds")
    op.drop_table("records_archival_access_logs")
    op.drop_table("records_archival_manifests")
    op.drop_table("records_lifecycle_history")
    op.drop_table("records_registry")
    op.drop_table("records_retention_policy_versions")
    op.drop_table("records_retention_policies")
    op.drop_table("records_categories")
