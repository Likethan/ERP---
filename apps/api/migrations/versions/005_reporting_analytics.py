"""Reporting and Analytics Layer Migration.

Revision ID: 005_reporting_analytics
Revises: 004_workflow_engine
Create Date: 2026-10-05 20:30:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "005_reporting_analytics"
down_revision = "004_workflow_engine"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. reporting_definitions
    op.create_table(
        "reporting_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=True,
            index=True,
        ),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("domain", sa.String(32), server_default="GENERAL", nullable=False),
        sa.Column("category", sa.String(64), server_default="OPERATIONAL", nullable=False),
        sa.Column("status", sa.String(32), server_default="DRAFT", nullable=False),
        sa.Column("visibility", sa.String(32), server_default="ROLE", nullable=False),
        sa.Column("is_system", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("allowed_roles", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("active_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "updated_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("tenant_id", "code", name="uq_report_tenant_code"),
    )
    op.create_index(
        "ix_report_tenant_domain_status",
        "reporting_definitions",
        ["tenant_id", "domain", "status"],
    )

    # 2. reporting_versions
    op.create_table(
        "reporting_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "report_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("reporting_definitions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("change_summary", sa.String(255), nullable=True),
        sa.Column(
            "query_spec_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("report_id", "version_number", name="uq_report_version_number"),
    )
    op.create_index(
        "ix_report_version_lookup",
        "reporting_versions",
        ["report_id", "is_active"],
    )

    # 3. reporting_executions
    op.create_table(
        "reporting_executions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "report_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("reporting_definitions.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "report_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("reporting_versions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "requested_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(32), server_default="QUEUED", nullable=False),
        sa.Column(
            "query_spec_snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column("row_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("execution_time_ms", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("correlation_id", sa.String(64), nullable=False),
        sa.Column("is_snapshot", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "snapshot_data",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_report_exec_tenant_status", "reporting_executions", ["tenant_id", "status"])
    op.create_index("ix_report_exec_created_at", "reporting_executions", ["tenant_id", "created_at"])
    op.create_index("ix_report_exec_correlation", "reporting_executions", ["tenant_id", "correlation_id"])

    # 4. reporting_exports
    op.create_table(
        "reporting_exports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "execution_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("reporting_executions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("export_format", sa.String(16), server_default="CSV", nullable=False),
        sa.Column("storage_key", sa.String(255), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(128), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("download_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_report_export_tenant_expires", "reporting_exports", ["tenant_id", "expires_at"])

    # 5. reporting_saved_reports
    op.create_table(
        "reporting_saved_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "report_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("reporting_definitions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "query_spec_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column("is_favorite", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_saved_report_user_tenant", "reporting_saved_reports", ["tenant_id", "user_id"])


def downgrade() -> None:
    op.drop_table("reporting_saved_reports")
    op.drop_table("reporting_exports")
    op.drop_table("reporting_executions")
    op.drop_table("reporting_versions")
    op.drop_table("reporting_definitions")
