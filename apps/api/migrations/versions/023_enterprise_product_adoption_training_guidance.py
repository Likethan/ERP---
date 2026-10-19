"""Enterprise Product Adoption, Training, In-App Guidance & Change Management Migration (Step 37).

Revision ID: 023_enterprise_product_adoption_training_guidance
Revises: 022_enterprise_customer_support_service_desk
Create Date: 2026-10-18 12:35:00.000000

Creates normalized tables for:
- adoption_journey_definitions: configurable role-specific onboarding journeys
- adoption_journey_steps: ordered journey steps with completion criteria & resources
- user_journey_progress: user completion tracking across sessions and devices
- training_programs: modular learning paths and courses for roles/departments
- training_modules: text instructions, external links, and document references
- training_assignments: user enrollments, deadlines, and completion validation
- contextual_guidance: route-aware tooltips, walkthroughs, and banners
- user_guidance_state: user impressions, dismissals, and completions
- product_announcements: release notices, workflow changes, and maintenance alerts
- user_announcement_receipts: user read and mandatory acknowledgement states
- feature_adoption_targets: institution adoption goals per feature
- feature_adoption_milestones: server-validated feature discovery & usage events
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "023_enterprise_product_adoption_training_guidance"
down_revision = "022_enterprise_customer_support_service_desk"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Adoption Journey Definitions
    op.create_table(
        "adoption_journey_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column("code", sa.String(64), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("target_roles", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column(
            "target_department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("product_version", sa.String(32), default="v1.0", nullable=False),
        sa.Column("status", sa.String(32), default="DRAFT", nullable=False, index=True),
        sa.Column("version", sa.Integer(), default=1, nullable=False),
        sa.Column("is_mandatory", sa.Boolean(), default=True, nullable=False),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", "version", name="uq_adoption_journey_tenant_code_ver"),
    )
    op.create_index("idx_adoption_journey_tenant_role", "adoption_journey_definitions", ["tenant_id", "status"])

    # 2. Adoption Journey Steps
    op.create_table(
        "adoption_journey_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "journey_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("adoption_journey_definitions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("step_key", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("completion_criteria", sa.String(32), default="CONFIRM_CHECKLIST", nullable=False),
        sa.Column("route_path", sa.String(255), nullable=True),
        sa.Column("contextual_resource_url", sa.String(512), nullable=True),
        sa.Column("estimated_duration_minutes", sa.Integer(), default=5, nullable=False),
        sa.Column("is_required", sa.Boolean(), default=True, nullable=False),
        sa.Column("action_event_key", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("journey_id", "step_key", name="uq_adoption_step_journey_key"),
    )
    op.create_index("idx_adoption_step_journey_order", "adoption_journey_steps", ["journey_id", "step_order"])

    # 3. User Journey Progress
    op.create_table(
        "user_journey_progress",
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
            "journey_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("adoption_journey_definitions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("journey_version", sa.Integer(), default=1, nullable=False),
        sa.Column("status", sa.String(32), default="NOT_STARTED", nullable=False, index=True),
        sa.Column("current_step_order", sa.Integer(), default=1, nullable=False),
        sa.Column("completed_step_keys", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("step_progress_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("progress_pct", sa.Float(), default=0.0, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_active_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "user_id", "journey_id", name="uq_user_journey_progress"),
    )
    op.create_index("idx_user_journey_status", "user_journey_progress", ["tenant_id", "user_id", "status"])

    # 4. Training Programs
    op.create_table(
        "training_programs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column("code", sa.String(64), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(64), default="ONBOARDING", nullable=False),
        sa.Column("target_roles", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column(
            "target_department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("version", sa.Integer(), default=1, nullable=False),
        sa.Column("status", sa.String(32), default="DRAFT", nullable=False, index=True),
        sa.Column("estimated_duration_minutes", sa.Integer(), default=30, nullable=False),
        sa.Column("is_mandatory", sa.Boolean(), default=False, nullable=False),
        sa.Column("completion_rule", sa.String(32), default="ALL_MODULES", nullable=False),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", "version", name="uq_training_program_tenant_code_ver"),
    )
    op.create_index("idx_training_program_status", "training_programs", ["tenant_id", "status"])

    # 5. Training Modules
    op.create_table(
        "training_modules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "program_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("training_programs.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("module_order", sa.Integer(), nullable=False),
        sa.Column("module_key", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(32), default="TEXT_INSTRUCTION", nullable=False),
        sa.Column("content_body", sa.Text(), nullable=True),
        sa.Column("external_url", sa.String(512), nullable=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("estimated_duration_minutes", sa.Integer(), default=10, nullable=False),
        sa.Column("is_required", sa.Boolean(), default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("program_id", "module_key", name="uq_training_module_program_key"),
    )
    op.create_index("idx_training_module_program_order", "training_modules", ["program_id", "module_order"])

    # 6. Training Assignments
    op.create_table(
        "training_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "program_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("training_programs.id", ondelete="CASCADE"),
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
            "assigned_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(32), default="ASSIGNED", nullable=False, index=True),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_module_keys", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("module_progress_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("progress_pct", sa.Float(), default=0.0, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("certificate_reference", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "program_id", "user_id", name="uq_user_training_assignment"),
    )
    op.create_index("idx_training_assign_status_due", "training_assignments", ["tenant_id", "status", "due_date"])

    # 7. Contextual Guidance
    op.create_table(
        "contextual_guidance",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column("guidance_key", sa.String(64), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("guidance_type", sa.String(32), default="TOOLTIP", nullable=False),
        sa.Column("route_path", sa.String(255), nullable=False, index=True),
        sa.Column("feature_key", sa.String(64), nullable=True, index=True),
        sa.Column("step_order", sa.Integer(), default=1, nullable=False),
        sa.Column("is_mandatory", sa.Boolean(), default=False, nullable=False),
        sa.Column("target_roles", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("status", sa.String(32), default="ACTIVE", nullable=False, index=True),
        sa.Column("version", sa.Integer(), default=1, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("document_url", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "guidance_key", "version", name="uq_guidance_tenant_key_ver"),
    )
    op.create_index("idx_guidance_route_roles", "contextual_guidance", ["route_path", "status"])

    # 8. User Guidance State
    op.create_table(
        "user_guidance_state",
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
            "guidance_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("contextual_guidance.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("status", sa.String(32), default="SEEN", nullable=False),
        sa.Column("impressions_count", sa.Integer(), default=1, nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dismissed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "user_id", "guidance_id", name="uq_user_guidance_state"),
    )
    op.create_index("idx_user_guidance_lookup", "user_guidance_state", ["tenant_id", "user_id", "status"])

    # 9. Product Announcements
    op.create_table(
        "product_announcements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column("announcement_code", sa.String(64), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("summary", sa.String(512), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("category", sa.String(32), default="FEATURE_RELEASE", nullable=False, index=True),
        sa.Column("priority", sa.String(16), default="NORMAL", nullable=False),
        sa.Column("status", sa.String(32), default="DRAFT", nullable=False, index=True),
        sa.Column("effective_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("requires_acknowledgement", sa.Boolean(), default=False, nullable=False),
        sa.Column("target_roles", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("target_departments", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("feature_flag_key", sa.String(128), nullable=True),
        sa.Column("doc_link_url", sa.String(512), nullable=True),
        sa.Column("version", sa.Integer(), default=1, nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "announcement_code", "version", name="uq_announcement_tenant_code_ver"),
    )
    op.create_index("idx_announcement_effective_status", "product_announcements", ["tenant_id", "status", "effective_at"])

    # 10. User Announcement Receipts
    op.create_table(
        "user_announcement_receipts",
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
            "announcement_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("product_announcements.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("announcement_version", sa.Integer(), default=1, nullable=False),
        sa.Column("is_read", sa.Boolean(), default=True, nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("is_acknowledged", sa.Boolean(), default=False, nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledgement_notes", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "user_id", "announcement_id", name="uq_user_announcement_receipt"),
    )
    op.create_index("idx_user_announcement_ack", "user_announcement_receipts", ["tenant_id", "user_id", "is_acknowledged"])

    # 11. Feature Adoption Targets
    op.create_table(
        "feature_adoption_targets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("feature_key", sa.String(128), nullable=False, index=True),
        sa.Column("feature_name", sa.String(255), nullable=False),
        sa.Column("target_roles", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("target_adoption_pct", sa.Float(), default=80.0, nullable=False),
        sa.Column("window_start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("window_end_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(32), default="ACTIVE", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "feature_key", name="uq_tenant_feature_adoption_target"),
    )
    op.create_index("idx_adoption_target_window", "feature_adoption_targets", ["tenant_id", "status", "window_end_date"])

    # 12. Feature Adoption Milestones
    op.create_table(
        "feature_adoption_milestones",
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
        sa.Column("feature_key", sa.String(128), nullable=False, index=True),
        sa.Column("milestone_type", sa.String(32), default="DISCOVERY", nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("idx_adoption_ms_lookup", "feature_adoption_milestones", ["tenant_id", "user_id", "feature_key", "milestone_type"])
    op.create_index("idx_adoption_ms_feature_time", "feature_adoption_milestones", ["tenant_id", "feature_key", "recorded_at"])


def downgrade() -> None:
    op.drop_table("feature_adoption_milestones")
    op.drop_table("feature_adoption_targets")
    op.drop_table("user_announcement_receipts")
    op.drop_table("product_announcements")
    op.drop_table("user_guidance_state")
    op.drop_table("contextual_guidance")
    op.drop_table("training_assignments")
    op.drop_table("training_modules")
    op.drop_table("training_programs")
    op.drop_table("user_journey_progress")
    op.drop_table("adoption_journey_steps")
    op.drop_table("adoption_journey_definitions")
