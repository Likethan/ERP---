"""Multi-Tenant SaaS Hardening & Tenant Isolation Migration.

Revision ID: 003_saas_hardening
Revises: 002_intelligence_engine
Create Date: 2026-10-03 23:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "003_saas_hardening"
down_revision = "002_intelligence_engine"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add SaaS lifecycle and multi-tenancy columns to core_institutions
    op.add_column(
        "core_institutions",
        sa.Column("slug", sa.String(64), nullable=True),
    )
    op.add_column(
        "core_institutions",
        sa.Column("status", sa.String(32), server_default="ACTIVE", nullable=False),
    )
    op.add_column(
        "core_institutions",
        sa.Column("plan", sa.String(32), server_default="ENTERPRISE", nullable=False),
    )
    op.add_column(
        "core_institutions",
        sa.Column("locale", sa.String(32), server_default="en-IN", nullable=False),
    )
    op.add_column(
        "core_institutions",
        sa.Column("suspended_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "core_institutions",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index("ix_core_institutions_slug", "core_institutions", ["slug"], unique=True)
    op.create_index("ix_core_institutions_status", "core_institutions", ["status"])

    # 2. Create core_tenant_memberships table
    op.create_table(
        "core_tenant_memberships",
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
        sa.Column("status", sa.String(32), server_default="ACTIVE", nullable=False),
        sa.Column("role_scope", sa.String(64), server_default="TENANT_MEMBER", nullable=False),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
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
        sa.UniqueConstraint("tenant_id", "user_id", name="uq_tenant_memberships_tenant_user"),
    )
    op.create_index(
        "idx_tenant_membership_status",
        "core_tenant_memberships",
        ["tenant_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("idx_tenant_membership_status", table_name="core_tenant_memberships")
    op.drop_table("core_tenant_memberships")

    op.drop_index("ix_core_institutions_status", table_name="core_institutions")
    op.drop_index("ix_core_institutions_slug", table_name="core_institutions")

    op.drop_column("core_institutions", "deleted_at")
    op.drop_column("core_institutions", "suspended_at")
    op.drop_column("core_institutions", "locale")
    op.drop_column("core_institutions", "plan")
    op.drop_column("core_institutions", "status")
    op.drop_column("core_institutions", "slug")
