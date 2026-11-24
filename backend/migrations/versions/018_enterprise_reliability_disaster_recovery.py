"""Enterprise Reliability Engineering, Disaster Recovery & Business Continuity Migration (Step 31).

Revision ID: 018_enterprise_reliability_disaster_recovery
Revises: 017_enterprise_platform_administration_saas_operations
Create Date: 2026-10-15 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "018_enterprise_reliability_disaster_recovery"
down_revision = "017_enterprise_platform_administration_saas_operations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create platform_backup_records
    op.create_table(
        "platform_backup_records",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("backup_type", sa.String(32), nullable=False, server_default="FULL"),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(512), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("sha256_checksum", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retention_days", sa.Integer(), nullable=False, server_default="14"),
        sa.Column("is_known_good", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("triggered_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
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
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_platform_backup_status", "platform_backup_records", ["status"])
    op.create_index("idx_platform_backup_started", "platform_backup_records", ["started_at"])
    op.create_index("idx_platform_backup_known_good", "platform_backup_records", ["is_known_good"])

    # 2. Create platform_restore_verifications
    op.create_table(
        "platform_restore_verifications",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "backup_record_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("platform_backup_records.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sandbox_database_name", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("sha256_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("schema_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("tables_verified_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("table_row_counts_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("isolation_check_passed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("tested_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
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
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_restore_verify_status", "platform_restore_verifications", ["status"])
    op.create_index("idx_restore_verify_backup", "platform_restore_verifications", ["backup_record_id"])

    # 3. Create platform_circuit_breaker_states
    op.create_table(
        "platform_circuit_breaker_states",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("dependency_name", sa.String(64), nullable=False, unique=True),
        sa.Column("state", sa.String(32), nullable=False, server_default="CLOSED"),
        sa.Column("failure_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("success_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "last_state_change_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("failure_threshold", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("recovery_timeout_seconds", sa.Integer(), nullable=False, server_default="60"),
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
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_circuit_breaker_dep", "platform_circuit_breaker_states", ["dependency_name"])

    # 4. Create platform_storage_audit_records
    op.create_table(
        "platform_storage_audit_records",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("status", sa.String(32), nullable=False, server_default="RUNNING"),
        sa.Column("total_db_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_storage_files", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("missing_files_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("orphaned_files_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("missing_file_keys", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("orphaned_file_keys", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("error_message", sa.Text(), nullable=True),
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
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("platform_storage_audit_records")
    op.drop_table("platform_circuit_breaker_states")
    op.drop_table("platform_restore_verifications")
    op.drop_table("platform_backup_records")
