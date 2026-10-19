"""Enterprise Data Import, Bulk Migration, Reconciliation & Interoperability Operations (Step 40).

Revision ID: 026_enterprise_data_import_migration_reconciliation
Revises: 025_enterprise_marketplace_app_integrations
Create Date: 2026-10-18 17:45:00.000000

Creates normalized tables for:
- import_templates: Approved domain import specifications, required/optional fields, policies
- import_jobs: Institutional data import jobs, lifecycle state machine, file reference, and record counters
- import_mapping_definitions: Source-to-target column mappings, transformation pipelines, defaults
- import_job_state_histories: Append-only audit trail of 14-state lifecycle transitions
- import_record_results: Row-level processing outcomes, errors, warnings, and committed entity IDs
- import_conflict_records: Detected record discrepancies between source files and existing tenant state
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "026_enterprise_data_import_migration_reconciliation"
down_revision = "025_enterprise_marketplace_app_integrations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Import Templates
    op.create_table(
        "import_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("target_domain", sa.String(64), nullable=False, index=True),
        sa.Column("target_entity", sa.String(64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("required_fields", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("optional_fields", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("field_definitions", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("supported_matching_keys", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("supported_policies", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("requires_approval_threshold", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("is_system_template", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # 2. Import Jobs
    op.create_table(
        "import_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("import_templates.id", ondelete="SET NULL"), nullable=True),
        sa.Column("template_code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("target_domain", sa.String(64), nullable=False),
        sa.Column("target_entity", sa.String(64), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="DRAFT", index=True),
        sa.Column("execution_policy", sa.String(32), nullable=False, server_default="CREATE_NEW"),
        sa.Column("matching_key", sa.String(64), nullable=True),
        sa.Column("source_filename", sa.String(255), nullable=True),
        sa.Column("source_file_storage_key", sa.String(512), nullable=True),
        sa.Column("source_file_checksum", sa.String(64), nullable=True),
        sa.Column("source_file_size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source_file_format", sa.String(16), nullable=True),
        sa.Column("source_record_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("valid_record_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_record_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("warning_record_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processed_record_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_record_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_record_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_record_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_record_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_processed_row", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("requires_approval", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("approved_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approval_notes", sa.Text(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_summary", sa.Text(), nullable=True),
        sa.Column("error_report_storage_key", sa.String(512), nullable=True),
        sa.Column("reconciliation_status", sa.String(32), nullable=False, server_default="NOT_RUN"),
        sa.Column("reconciliation_diff_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reconciliation_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("idx_import_jobs_tenant_status", "import_jobs", ["tenant_id", "status"])
    op.create_index("idx_import_jobs_tenant_domain", "import_jobs", ["tenant_id", "target_domain"])
    op.create_index("idx_import_jobs_tenant_created", "import_jobs", ["tenant_id", "created_at"])

    # 3. Import Mapping Definitions
    op.create_table(
        "import_mapping_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("import_jobs.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("template_code", sa.String(64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("column_mappings", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("transformations", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("default_values", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("is_validated", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "job_id", name="uq_import_mapping_tenant_job"),
    )

    # 4. Import Job State Histories
    op.create_table(
        "import_job_state_histories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("import_jobs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("from_status", sa.String(50), nullable=False),
        sa.Column("to_status", sa.String(50), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("idx_import_history_tenant_job", "import_job_state_histories", ["tenant_id", "job_id"])

    # 5. Import Record Results
    op.create_table(
        "import_record_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("import_jobs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("matching_key_value", sa.String(255), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("target_entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_data_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("transformed_data_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("errors_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("warnings_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("idx_import_record_tenant_job", "import_record_results", ["tenant_id", "job_id"])
    op.create_index("idx_import_record_row", "import_record_results", ["job_id", "row_number"])
    op.create_index("idx_import_record_status", "import_record_results", ["job_id", "status"])

    # 6. Import Conflict Records
    op.create_table(
        "import_conflict_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("import_jobs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("matching_key", sa.String(64), nullable=False),
        sa.Column("matching_value", sa.String(255), nullable=False),
        sa.Column("existing_entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("conflict_type", sa.String(64), nullable=False),
        sa.Column("source_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("existing_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("discrepancies_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("resolution", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("resolved_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("idx_import_conflict_tenant_job", "import_conflict_records", ["tenant_id", "job_id"])
    op.create_index("idx_import_conflict_resolution", "import_conflict_records", ["job_id", "resolution"])


def downgrade() -> None:
    op.drop_table("import_conflict_records")
    op.drop_table("import_record_results")
    op.drop_table("import_job_state_histories")
    op.drop_table("import_mapping_definitions")
    op.drop_table("import_jobs")
    op.drop_table("import_templates")
