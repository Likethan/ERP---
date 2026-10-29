"""Enterprise Data Governance, Privacy & Compliance Layer Migration.

Revision ID: 006_governance_privacy_compliance
Revises: 005_reporting_analytics
Create Date: 2026-10-05 21:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "006_governance_privacy_compliance"
down_revision = "005_reporting_analytics"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. governance_policies
    op.create_table(
        "governance_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("category", sa.String(64), server_default="RETENTION", nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), server_default="ACTIVE", nullable=False),
        sa.Column("is_system_default", sa.Boolean(), server_default="false", nullable=False),
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
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_gov_policies_tenant_code"),
    )
    op.create_index("ix_gov_policies_tenant_cat", "governance_policies", ["tenant_id", "category"])
    op.create_index("ix_gov_policies_tenant_status", "governance_policies", ["tenant_id", "status"])

    # 2. governance_policy_versions
    op.create_table(
        "governance_policy_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "policy_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("governance_policies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), server_default="1", nullable=False),
        sa.Column("status", sa.String(32), server_default="ACTIVE", nullable=False),
        sa.Column("rules_json", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("change_summary", sa.String(255), nullable=True),
        sa.Column("effective_from", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("effective_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("policy_id", "version_number", name="uq_gov_policy_versions_num"),
    )
    op.create_index("ix_gov_policy_versions_active", "governance_policy_versions", ["tenant_id", "policy_id", "is_active"])

    # 3. governance_retention_policies
    op.create_table(
        "governance_retention_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "policy_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("governance_policies.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("resource_type", sa.String(64), nullable=False),
        sa.Column("retention_period", sa.Integer(), server_default="5", nullable=False),
        sa.Column("retention_unit", sa.String(16), server_default="YEARS", nullable=False),
        sa.Column("trigger_event", sa.String(32), server_default="CREATION", nullable=False),
        sa.Column("action", sa.String(32), server_default="ARCHIVE", nullable=False),
        sa.Column("archive_after_days", sa.Integer(), nullable=True),
        sa.Column("delete_after_days", sa.Integer(), nullable=True),
        sa.Column("legal_hold_behavior", sa.String(16), server_default="BLOCK", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "resource_type", name="uq_gov_retention_tenant_res"),
    )
    op.create_index("ix_gov_retention_tenant_active", "governance_retention_policies", ["tenant_id", "is_active"])

    # 4. governance_holds
    op.create_table(
        "governance_holds",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("case_reference", sa.String(128), nullable=True),
        sa.Column("target_entity_type", sa.String(64), nullable=False),
        sa.Column("target_entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), server_default="ACTIVE", nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "released_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("release_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("ix_gov_holds_tenant_status", "governance_holds", ["tenant_id", "status"])
    op.create_index("ix_gov_holds_target", "governance_holds", ["tenant_id", "target_entity_type", "target_entity_id"])

    # 5. governance_privacy_requests
    op.create_table(
        "governance_privacy_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("request_number", sa.String(64), nullable=False),
        sa.Column("request_type", sa.String(32), server_default="ACCESS", nullable=False),
        sa.Column("status", sa.String(32), server_default="SUBMITTED", nullable=False),
        sa.Column("data_subject_type", sa.String(32), server_default="STUDENT", nullable=False),
        sa.Column("data_subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "requested_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "reviewed_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("evidence_notes", sa.Text(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("target_domains_json", postgresql.JSONB(astext_type=sa.Text()), server_default="[]", nullable=False),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("export_storage_key", sa.String(512), nullable=True),
        sa.Column("export_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "request_number", name="uq_gov_privacy_req_num"),
    )
    op.create_index("ix_gov_privacy_tenant_status", "governance_privacy_requests", ["tenant_id", "status"])
    op.create_index("ix_gov_privacy_subject", "governance_privacy_requests", ["tenant_id", "data_subject_id"])

    # 6. governance_privacy_request_actions
    op.create_table(
        "governance_privacy_request_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "request_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("governance_privacy_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("action_type", sa.String(32), nullable=False),
        sa.Column("domain", sa.String(64), nullable=False),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(32), server_default="PENDING", nullable=False),
        sa.Column("blocked_reason", sa.Text(), nullable=True),
        sa.Column("old_values_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("new_values_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "performed_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("performed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("ix_gov_priv_act_req", "governance_privacy_request_actions", ["tenant_id", "request_id"])

    # 7. governance_access_reviews
    op.create_table(
        "governance_access_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("title", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("review_type", sa.String(64), server_default="PRIVILEGED_ROLES", nullable=False),
        sa.Column("status", sa.String(32), server_default="OPEN", nullable=False),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "reviewer_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("ix_gov_reviews_tenant_status", "governance_access_reviews", ["tenant_id", "status"])

    # 8. governance_access_review_items
    op.create_table(
        "governance_access_review_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "review_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("governance_access_reviews.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "role_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_roles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("permission_name", sa.String(128), nullable=True),
        sa.Column("decision", sa.String(32), server_default="PENDING", nullable=False),
        sa.Column("decision_notes", sa.Text(), nullable=True),
        sa.Column(
            "decided_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("ix_gov_rev_items_review", "governance_access_review_items", ["tenant_id", "review_id"])
    op.create_index("ix_gov_rev_items_user", "governance_access_review_items", ["tenant_id", "user_id"])


def downgrade() -> None:
    op.drop_table("governance_access_review_items")
    op.drop_table("governance_access_reviews")
    op.drop_table("governance_privacy_request_actions")
    op.drop_table("governance_privacy_requests")
    op.drop_table("governance_holds")
    op.drop_table("governance_retention_policies")
    op.drop_table("governance_policy_versions")
    op.drop_table("governance_policies")
