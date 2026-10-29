"""Enterprise Identity, SSO, Session & Access Federation Layer Migration.

Revision ID: 009_enterprise_identity_sso_sessions
Revises: 008_enterprise_api_platform
Create Date: 2026-10-07 22:30:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "009_enterprise_identity_sso_sessions"
down_revision = "008_enterprise_api_platform"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. identity_providers
    op.create_table(
        "identity_providers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("slug", sa.String(64), nullable=False, index=True),
        sa.Column("provider_type", sa.String(32), nullable=False, default="OIDC", index=True),
        sa.Column("status", sa.String(32), nullable=False, default="DRAFT", index=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, default=False),
        sa.Column("issuer_url", sa.String(255), nullable=True),
        sa.Column("client_id", sa.String(255), nullable=True),
        sa.Column("client_secret_reference", sa.String(255), nullable=True),
        sa.Column("authorization_endpoint", sa.String(255), nullable=True),
        sa.Column("token_endpoint", sa.String(255), nullable=True),
        sa.Column("userinfo_endpoint", sa.String(255), nullable=True),
        sa.Column("jwks_uri", sa.String(255), nullable=True),
        sa.Column("scopes", postgresql.JSONB(), nullable=False, server_default='["openid", "profile", "email"]'),
        sa.Column("redirect_uri", sa.String(255), nullable=True),
        sa.Column("attribute_mapping", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("role_mapping", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("health_status", sa.String(32), nullable=False, default="UNKNOWN"),
        sa.Column("last_health_check_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_successful_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "slug", name="uq_idp_tenant_slug"),
    )
    op.create_index("idx_idp_tenant_status", "identity_providers", ["tenant_id", "status"])

    # 2. identity_external_identities
    op.create_table(
        "identity_external_identities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
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
            "provider_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("identity_providers.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("subject", sa.String(255), nullable=False, index=True),
        sa.Column("email", sa.String(255), nullable=False, index=True),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("claims_snapshot", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "provider_id", "subject", name="uq_ext_identity_subject"),
    )
    op.create_index("idx_ext_identity_lookup", "identity_external_identities", ["tenant_id", "email"])

    # 3. identity_tenant_policies
    op.create_table(
        "identity_tenant_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("local_login_enabled", sa.Boolean(), nullable=False, default=True),
        sa.Column("external_login_enabled", sa.Boolean(), nullable=False, default=True),
        sa.Column("allowed_identity_provider_ids", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("provisioning_mode", sa.String(32), nullable=False, default="JUST_IN_TIME"),
        sa.Column("allowed_email_domains", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column(
            "default_role_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_roles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("session_duration_minutes", sa.Integer(), nullable=False, default=1440),
        sa.Column("idle_timeout_minutes", sa.Integer(), nullable=False, default=120),
        sa.Column("max_active_sessions_per_user", sa.Integer(), nullable=False, default=5),
        sa.Column("password_min_length", sa.Integer(), nullable=False, default=8),
        sa.Column("password_require_uppercase", sa.Boolean(), nullable=False, default=True),
        sa.Column("password_require_lowercase", sa.Boolean(), nullable=False, default=True),
        sa.Column("password_require_numbers", sa.Boolean(), nullable=False, default=True),
        sa.Column("password_require_special", sa.Boolean(), nullable=False, default=True),
        sa.Column("lockout_threshold", sa.Integer(), nullable=False, default=5),
        sa.Column("lockout_duration_minutes", sa.Integer(), nullable=False, default=15),
        sa.Column("mfa_policy", sa.String(32), nullable=False, default="OPTIONAL"),
        sa.Column("enforce_mfa_for_admins", sa.Boolean(), nullable=False, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", name="uq_tenant_identity_policy"),
    )

    # 4. identity_user_sessions
    op.create_table(
        "identity_user_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("session_identifier", sa.String(128), unique=True, nullable=False, index=True),
        sa.Column("refresh_token_family_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("refresh_token_hash", sa.String(255), nullable=False, index=True),
        sa.Column("status", sa.String(32), nullable=False, default="ACTIVE", index=True),
        sa.Column("ip_address_hash", sa.String(64), nullable=True),
        sa.Column("ip_address_masked", sa.String(64), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("device_summary", sa.String(128), nullable=True),
        sa.Column("authentication_method", sa.String(32), nullable=False, default="LOCAL_PASSWORD"),
        sa.Column("is_mfa_verified", sa.Boolean(), nullable=False, default=False),
        sa.Column("mfa_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), index=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revocation_reason", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_id_session_user_status", "identity_user_sessions", ["user_id", "status"])
    op.create_index("idx_id_session_family", "identity_user_sessions", ["refresh_token_family_id"])

    # 5. identity_mfa_factors
    op.create_table(
        "identity_mfa_factors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("factor_type", sa.String(32), nullable=False, default="TOTP", index=True),
        sa.Column("secret_encrypted", sa.String(512), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=False),
        sa.Column("enrolled_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "user_id", "factor_type", name="uq_user_mfa_factor"),
    )

    # 6. identity_mfa_recovery_codes
    op.create_table(
        "identity_mfa_recovery_codes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("code_hash", sa.String(255), nullable=False, index=True),
        sa.Column("is_used", sa.Boolean(), nullable=False, default=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_mfa_recovery_lookup", "identity_mfa_recovery_codes", ["tenant_id", "user_id", "is_used"])

    # 7. identity_mfa_challenges
    op.create_table(
        "identity_mfa_challenges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=True,
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
            "factor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("identity_mfa_factors.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("challenge_token_hash", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("factor_type", sa.String(32), nullable=False, default="TOTP"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, default=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 8. identity_account_link_requests
    op.create_table(
        "identity_account_link_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
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
            "provider_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("identity_providers.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("external_email", sa.String(255), nullable=False),
        sa.Column("token_hash", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("is_completed", sa.Boolean(), nullable=False, default=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("identity_account_link_requests")
    op.drop_table("identity_mfa_challenges")
    op.drop_table("identity_mfa_recovery_codes")
    op.drop_table("identity_mfa_factors")
    op.drop_table("identity_user_sessions")
    op.drop_table("identity_tenant_policies")
    op.drop_table("identity_external_identities")
    op.drop_table("identity_providers")
