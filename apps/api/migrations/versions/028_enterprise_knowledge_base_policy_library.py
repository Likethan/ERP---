"""Enterprise Institutional Knowledge Base, Policy Library & Controlled Knowledge Management (Step 42).

Revision ID: 028_enterprise_knowledge_base_policy_library
Revises: 027_enterprise_records_lifecycle_retention_archival
Create Date: 2026-10-18 19:30:00.000000

Creates normalized tables for:
- knowledge_categories: Standard and institutional Knowledge Categories across academic, operational, and statutory domains
- knowledge_items: Institutional Knowledge Items with draft management, optimistic concurrency, and controlled visibility
- knowledge_item_versions: Immutable published Knowledge Item Versions capturing cryptographic snapshots and approvals
- knowledge_review_stages: Multi-stage Review Stages enforcing separation of duties and auditable feedback
- knowledge_relationships: Directed Knowledge Relationships (supersedes, implements, references, depends_on, announces)
- knowledge_acknowledgement_requirements: Audience specification for mandatory policy attestations
- knowledge_user_acknowledgements: Tamper-evident user attestation against exact published versions
- knowledge_scheduled_reviews: Scheduled Knowledge Reviews and expiration/review monitoring
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "028_enterprise_knowledge_base_policy_library"
down_revision = "027_enterprise_records_lifecycle_retention_archival"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Knowledge Categories
    op.create_table(
        "knowledge_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("requires_approval", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("requires_attestation", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("default_review_months", sa.Integer(), nullable=False, server_default="12"),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_knowledge_cat_tenant_code"),
    )
    op.create_index("ix_knowledge_cat_tenant_code", "knowledge_categories", ["tenant_id", "code"])

    # 2. Knowledge Items
    op.create_table(
        "knowledge_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("item_code", sa.String(64), nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column(
            "category_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("knowledge_categories.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("category_code", sa.String(64), nullable=False),
        sa.Column(
            "owner_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "responsible_reviewer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "last_edited_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "campus_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_campuses.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_departments.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("scope_type", sa.String(32), nullable=False, server_default="INSTITUTION"),
        sa.Column("visibility_role", sa.String(64), nullable=True),
        sa.Column("confidentiality", sa.String(32), nullable=False, server_default="INTERNAL_ONLY"),
        sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT"),
        sa.Column("current_version_number", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("current_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("lock_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("draft_content_markdown", sa.Text(), nullable=False, server_default=""),
        sa.Column("draft_sections_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("document_attachment_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("change_summary", sa.Text(), nullable=True),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_by_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "superseded_by_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("knowledge_items.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("requires_acknowledgement", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("search_indexed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("search_index_status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "item_code", name="uq_knowledge_item_tenant_code"),
    )
    op.create_index("ix_knowledge_item_tenant_status", "knowledge_items", ["tenant_id", "status"])
    op.create_index("ix_knowledge_item_tenant_scope", "knowledge_items", ["tenant_id", "scope_type"])
    op.create_index("ix_knowledge_item_tenant_review", "knowledge_items", ["tenant_id", "review_by_date"])

    # 3. Knowledge Item Versions
    op.create_table(
        "knowledge_item_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("knowledge_items.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("content_markdown", sa.Text(), nullable=False),
        sa.Column("sections_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("metadata_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("document_attachment_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column(
            "author_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "reviewer_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("approval_decision", sa.String(32), nullable=False, server_default="APPROVED"),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "published_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("change_summary", sa.Text(), nullable=True),
        sa.Column(
            "supersedes_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("knowledge_item_versions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "item_id", "version_number", name="uq_knowledge_ver_tenant_item_num"),
    )
    op.create_index("ix_knowledge_ver_tenant_item", "knowledge_item_versions", ["tenant_id", "item_id"])

    # 4. Knowledge Review Stages
    op.create_table(
        "knowledge_review_stages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("knowledge_items.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("stage_order", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("stage_name", sa.String(64), nullable=False, server_default="Editorial Review"),
        sa.Column(
            "reviewer_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reviewer_role", sa.String(64), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("ix_knowledge_stage_item_ver", "knowledge_review_stages", ["tenant_id", "item_id", "version_number"])

    # 5. Knowledge Relationships
    op.create_table(
        "knowledge_relationships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "source_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("knowledge_items.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "target_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("knowledge_items.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("relationship_type", sa.String(32), nullable=False),
        sa.Column("description", sa.String(256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "tenant_id",
            "source_item_id",
            "target_item_id",
            "relationship_type",
            name="uq_knowledge_rel_source_target_type",
        ),
    )
    op.create_index("ix_knowledge_rel_tenant_source", "knowledge_relationships", ["tenant_id", "source_item_id"])
    op.create_index("ix_knowledge_rel_tenant_target", "knowledge_relationships", ["tenant_id", "target_item_id"])

    # 6. Knowledge Acknowledgement Requirements
    op.create_table(
        "knowledge_acknowledgement_requirements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("knowledge_items.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("target_role", sa.String(64), nullable=True),
        sa.Column(
            "target_department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "target_campus_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_campuses.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("deadline_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("is_mandatory", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "statement_prompt",
            sa.Text(),
            nullable=False,
            server_default="I have read, understood, and agree to abide by this institutional policy and its requirements.",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_knowledge_ack_req_item_ver",
        "knowledge_acknowledgement_requirements",
        ["tenant_id", "item_id", "version_number"],
    )

    # 7. Knowledge User Acknowledgements
    op.create_table(
        "knowledge_user_acknowledgements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("knowledge_items.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=False, server_default="127.0.0.1"),
        sa.Column("user_agent", sa.String(256), nullable=True),
        sa.Column("statement_confirmed", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "tenant_id",
            "item_id",
            "version_number",
            "user_id",
            name="uq_knowledge_user_ack_exact",
        ),
    )
    op.create_index(
        "ix_knowledge_user_ack_lookup",
        "knowledge_user_acknowledgements",
        ["tenant_id", "user_id", "item_id"],
    )

    # 8. Knowledge Scheduled Reviews
    op.create_table(
        "knowledge_scheduled_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("knowledge_items.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("review_type", sa.String(32), nullable=False, server_default="ANNUAL_REVIEW"),
        sa.Column("scheduled_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_knowledge_sched_status_date",
        "knowledge_scheduled_reviews",
        ["tenant_id", "status", "scheduled_date"],
    )


def downgrade() -> None:
    op.drop_table("knowledge_scheduled_reviews")
    op.drop_table("knowledge_user_acknowledgements")
    op.drop_table("knowledge_acknowledgement_requirements")
    op.drop_table("knowledge_relationships")
    op.drop_table("knowledge_review_stages")
    op.drop_table("knowledge_item_versions")
    op.drop_table("knowledge_items")
    op.drop_table("knowledge_categories")
