"""Enterprise Customer Support, Service Desk & SLA Management Migration (Step 36).

Revision ID: 022_enterprise_customer_support_service_desk
Revises: 021_enterprise_tenant_onboarding_go_live_orchestration
Create Date: 2026-10-17 22:30:00.000000

Creates normalized support desk and SLA tables:
- support_teams: tiered operational support teams & specialization modules
- support_team_members: agent team memberships & capacity tracking
- support_sla_policies: priority and severity based SLA duration targets
- support_tickets: core customer support requests with full tenant isolation
- support_ticket_messages: segregated public replies vs internal notes
- support_ticket_timeline: auditable lifecycle and SLA clock transitions
- support_ticket_article_links: knowledge-base article correlations
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "022_enterprise_customer_support_service_desk"
down_revision = "021_enterprise_tenant_onboarding_go_live_orchestration"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Support Teams
    op.create_table(
        "support_teams",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column("code", sa.String(64), unique=True, nullable=False, index=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("specialization_modules", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column(
            "supervisor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("is_platform_team", sa.Boolean(), default=False, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # 2. Support Team Members
    op.create_table(
        "support_team_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "team_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("support_teams.id", ondelete="CASCADE"),
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
        sa.Column("user_email", sa.String(255), nullable=False),
        sa.Column("is_team_lead", sa.Boolean(), default=False, nullable=False),
        sa.Column("is_available", sa.Boolean(), default=True, nullable=False),
        sa.Column("active_ticket_count", sa.Integer(), default=0, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("team_id", "user_id", name="uq_support_team_member"),
    )

    # 3. Support SLA Policies
    op.create_table(
        "support_sla_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("service_plan", sa.String(32), default="ALL", nullable=False, index=True),
        sa.Column("priority", sa.String(32), default="MEDIUM", nullable=False, index=True),
        sa.Column("severity", sa.String(32), nullable=True),
        sa.Column("category", sa.String(64), nullable=True),
        sa.Column("response_target_minutes", sa.Integer(), default=120, nullable=False),
        sa.Column("resolution_target_minutes", sa.Integer(), default=1440, nullable=False),
        sa.Column("business_hours_only", sa.Boolean(), default=True, nullable=False),
        sa.Column("business_start_hour", sa.Integer(), default=9, nullable=False),
        sa.Column("business_end_hour", sa.Integer(), default=18, nullable=False),
        sa.Column("escalation_threshold_pct", sa.Integer(), default=75, nullable=False),
        sa.Column(
            "escalation_team_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("support_teams.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # 4. Support Tickets
    op.create_table(
        "support_tickets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column("ticket_number", sa.String(32), unique=True, nullable=False, index=True),
        sa.Column(
            "requester_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column("requester_email", sa.String(255), nullable=False),
        sa.Column("requester_name", sa.String(255), nullable=False),
        sa.Column("requester_type", sa.String(32), default="STUDENT", nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(64), default="GENERAL_ASSISTANCE", nullable=False, index=True),
        sa.Column("subcategory", sa.String(64), nullable=True),
        sa.Column("request_type", sa.String(32), default="SERVICE_REQUEST", nullable=False),
        sa.Column("priority", sa.String(32), default="MEDIUM", nullable=False, index=True),
        sa.Column("severity", sa.String(32), default="SEV_3_MODERATE", nullable=False),
        sa.Column("status", sa.String(32), default="NEW", nullable=False, index=True),
        sa.Column(
            "assigned_team_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("support_teams.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("assigned_team_name", sa.String(128), nullable=True),
        sa.Column(
            "assigned_agent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("assigned_agent_email", sa.String(255), nullable=True),
        sa.Column("related_erp_module", sa.String(64), nullable=True),
        sa.Column("related_resource_type", sa.String(64), nullable=True),
        sa.Column("related_resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("related_incident_id", sa.String(64), nullable=True),
        sa.Column(
            "related_security_incident_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("security_incidents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "sla_policy_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("support_sla_policies.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("response_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("first_response_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("triaged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reopened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("escalated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sla_response_status", sa.String(32), default="ON_TRACK", nullable=False),
        sa.Column("sla_resolution_status", sa.String(32), default="ON_TRACK", nullable=False),
        sa.Column("sla_paused_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sla_total_paused_minutes", sa.Integer(), default=0, nullable=False),
        sa.Column("resolution_summary", sa.Text(), nullable=True),
        sa.Column("closure_reason", sa.String(128), nullable=True),
        sa.Column("reopen_count", sa.Integer(), default=0, nullable=False),
        sa.Column("reopen_reason", sa.Text(), nullable=True),
        sa.Column("escalation_level", sa.Integer(), default=0, nullable=False),
        sa.Column("escalation_reason", sa.Text(), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("csat_rating", sa.Integer(), nullable=True),
        sa.Column("csat_feedback", sa.Text(), nullable=True),
        sa.Column("csat_submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("attachments_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    op.create_index("idx_supp_tick_tenant_status", "support_tickets", ["tenant_id", "status"])
    op.create_index("idx_supp_tick_tenant_priority", "support_tickets", ["tenant_id", "priority"])
    op.create_index("idx_supp_tick_requester", "support_tickets", ["requester_id", "status"])
    op.create_index("idx_supp_tick_agent", "support_tickets", ["assigned_agent_id", "status"])
    op.create_index("idx_supp_tick_team", "support_tickets", ["assigned_team_id", "status"])
    op.create_index("idx_supp_tick_due", "support_tickets", ["resolution_due_at", "status"])

    # 5. Support Ticket Messages
    op.create_table(
        "support_ticket_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "ticket_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("support_tickets.id", ondelete="CASCADE"),
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
        sa.Column(
            "sender_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("sender_email", sa.String(255), nullable=False),
        sa.Column("sender_name", sa.String(255), nullable=False),
        sa.Column("sender_role", sa.String(64), nullable=False),
        sa.Column("message_type", sa.String(32), default="PUBLIC_REPLY", nullable=False, index=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("attachments_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("idx_supp_msg_ticket_type", "support_ticket_messages", ["ticket_id", "message_type"])

    # 6. Support Ticket Timeline
    op.create_table(
        "support_ticket_timeline",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "ticket_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("support_tickets.id", ondelete="CASCADE"),
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
        sa.Column("event_type", sa.String(64), default="CREATED", nullable=False, index=True),
        sa.Column(
            "actor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("actor_email", sa.String(255), nullable=True),
        sa.Column("from_status", sa.String(32), nullable=True),
        sa.Column("to_status", sa.String(32), nullable=True),
        sa.Column("summary", sa.String(255), nullable=False),
        sa.Column("details_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # 7. Support Ticket Article Links
    op.create_table(
        "support_ticket_article_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "ticket_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("support_tickets.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("article_id", sa.String(64), nullable=False),
        sa.Column("article_title", sa.String(255), nullable=False),
        sa.Column("article_url", sa.String(512), nullable=False),
        sa.Column("relevance_score", sa.Float(), default=1.0, nullable=False),
        sa.Column("was_helpful", sa.Boolean(), nullable=True),
        sa.Column(
            "linked_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("support_ticket_article_links")
    op.drop_table("support_ticket_timeline")
    op.drop_table("support_ticket_messages")
    op.drop_table("support_tickets")
    op.drop_table("support_sla_policies")
    op.drop_table("support_team_members")
    op.drop_table("support_teams")
