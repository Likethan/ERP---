"""Enterprise Administration, Configuration & Policy Management Layer Migration.

Revision ID: 010_enterprise_admin_configuration_policy
Revises: 009_enterprise_identity_sso_sessions
Create Date: 2026-10-08 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "010_enterprise_admin_configuration_policy"
down_revision = "009_enterprise_identity_sso_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. configuration_definitions
    op.create_table(
        "configuration_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("key", sa.String(128), unique=True, nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(64), nullable=False, index=True),
        sa.Column("module", sa.String(64), nullable=False, index=True),
        sa.Column("data_type", sa.String(32), nullable=False, default="STRING"),
        sa.Column("default_value", postgresql.JSONB(), nullable=True),
        sa.Column("validation_schema", postgresql.JSONB(), nullable=True),
        sa.Column("allowed_values", postgresql.JSONB(), nullable=True),
        sa.Column("sensitivity", sa.String(32), nullable=False, default="INTERNAL"),
        sa.Column("scope", sa.String(32), nullable=False, default="TENANT"),
        sa.Column("is_editable", sa.Boolean(), nullable=False, default=True),
        sa.Column("is_restart_required", sa.Boolean(), nullable=False, default=False),
        sa.Column("is_feature_flag", sa.Boolean(), nullable=False, default=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True, index=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 2. configuration_values
    op.create_table(
        "configuration_values",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "configuration_definition_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("configuration_definitions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "campus_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_campuses.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column("scope_type", sa.String(32), nullable=False, default="TENANT", index=True),
        sa.Column("value", postgresql.JSONB(), nullable=True),
        sa.Column("source", sa.String(64), nullable=False, default="TENANT_OVERRIDE"),
        sa.Column("version", sa.Integer(), nullable=False, default=1),
        sa.Column("status", sa.String(32), nullable=False, default="ACTIVE", index=True),
        sa.Column(
            "effective_from",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("effective_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "updated_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "tenant_id",
            "configuration_definition_id",
            "scope_type",
            "campus_id",
            name="uq_cfg_val_scoped",
        ),
    )
    op.create_index(
        "idx_cfg_val_tenant_def",
        "configuration_values",
        ["tenant_id", "configuration_definition_id"],
    )

    # 3. configuration_versions
    op.create_table(
        "configuration_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "configuration_definition_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("configuration_definitions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "configuration_value_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("configuration_values.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("previous_version", sa.Integer(), nullable=True),
        sa.Column("value", postgresql.JSONB(), nullable=True),
        sa.Column("change_summary", sa.Text(), nullable=True),
        sa.Column("changed_fields", postgresql.JSONB(), nullable=True),
        sa.Column(
            "actor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("actor_email", sa.String(255), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, default="ACTIVE"),
        sa.Column(
            "effective_from",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("rollback_reference", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index(
        "idx_cfg_ver_tenant_def",
        "configuration_versions",
        ["tenant_id", "configuration_definition_id"],
    )
    op.create_index(
        "idx_cfg_ver_num",
        "configuration_versions",
        ["configuration_definition_id", "version_number"],
    )

    # 4. configuration_policies
    op.create_table(
        "configuration_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column("policy_key", sa.String(128), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("module", sa.String(64), nullable=False, index=True),
        sa.Column("scope", sa.String(32), nullable=False, default="TENANT"),
        sa.Column(
            "campus_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_campuses.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column("conditions", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("actions", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("priority", sa.Integer(), nullable=False, default=100),
        sa.Column("status", sa.String(32), nullable=False, default="ACTIVE", index=True),
        sa.Column("version", sa.Integer(), nullable=False, default=1),
        sa.Column(
            "effective_from",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("effective_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "updated_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "policy_key", "campus_id", name="uq_cfg_policy_scoped"),
    )
    op.create_index(
        "idx_cfg_policy_tenant_key", "configuration_policies", ["tenant_id", "policy_key"]
    )

    # 5. configuration_policy_versions
    op.create_table(
        "configuration_policy_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "policy_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("configuration_policies.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("policy_key", sa.String(128), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("conditions", postgresql.JSONB(), nullable=False),
        sa.Column("actions", postgresql.JSONB(), nullable=False),
        sa.Column("change_summary", sa.Text(), nullable=True),
        sa.Column(
            "actor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index(
        "idx_cfg_pol_ver_policy_num",
        "configuration_policy_versions",
        ["policy_id", "version_number"],
    )

    # 6. feature_flags
    op.create_table(
        "feature_flags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column("key", sa.String(128), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("module", sa.String(64), nullable=False, index=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, default=False, index=True),
        sa.Column("rollout_percentage", sa.Integer(), nullable=False, default=0),
        sa.Column("target_roles", postgresql.JSONB(), nullable=True),
        sa.Column("target_users", postgresql.JSONB(), nullable=True),
        sa.Column("environment", sa.String(32), nullable=False, default="ALL"),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "updated_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "key", name="uq_feature_flag_tenant_key"),
    )

    # 7. module_configurations
    op.create_table(
        "module_configurations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("module", sa.String(64), nullable=False, index=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, default=True, index=True),
        sa.Column("enabled_features", postgresql.JSONB(), nullable=True, server_default="[]"),
        sa.Column("maintenance_mode", sa.Boolean(), nullable=False, default=False),
        sa.Column("maintenance_message", sa.Text(), nullable=True),
        sa.Column("custom_settings", postgresql.JSONB(), nullable=True, server_default="{}"),
        sa.Column(
            "updated_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "module", name="uq_module_config_tenant_module"),
    )

    # 8. numbering_sequences
    op.create_table(
        "numbering_sequences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("sequence_key", sa.String(64), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("prefix", sa.String(32), nullable=False, default=""),
        sa.Column("suffix", sa.String(32), nullable=True),
        sa.Column("pattern", sa.String(128), nullable=False, default="{PREFIX}{YYYY}-{SEQ}"),
        sa.Column("padding", sa.Integer(), nullable=False, default=5),
        sa.Column("current_val", sa.Integer(), nullable=False, default=0),
        sa.Column("step", sa.Integer(), nullable=False, default=1),
        sa.Column("reset_frequency", sa.String(32), nullable=False, default="NEVER"),
        sa.Column("last_reset_year", sa.Integer(), nullable=True),
        sa.Column("last_reset_month", sa.Integer(), nullable=True),
        sa.Column("last_reset_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "sequence_key", name="uq_numbering_seq_tenant_key"),
    )

    # 9. configuration_dependencies
    op.create_table(
        "configuration_dependencies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("configuration_key", sa.String(128), nullable=False, index=True),
        sa.Column("consumer_module", sa.String(64), nullable=False, index=True),
        sa.Column("consumer_component", sa.String(128), nullable=False),
        sa.Column("impact_description", sa.Text(), nullable=False),
        sa.Column("criticality", sa.String(32), nullable=False, default="MEDIUM"),
        sa.Column("is_restart_required", sa.Boolean(), nullable=False, default=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "configuration_key",
            "consumer_module",
            "consumer_component",
            name="uq_cfg_dep_key_consumer",
        ),
    )


def downgrade() -> None:
    op.drop_table("configuration_dependencies")
    op.drop_table("numbering_sequences")
    op.drop_table("module_configurations")
    op.drop_table("feature_flags")
    op.drop_table("configuration_policy_versions")
    op.drop_table("configuration_policies")
    op.drop_table("configuration_versions")
    op.drop_table("configuration_values")
    op.drop_table("configuration_definitions")
