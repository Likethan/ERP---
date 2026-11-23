"""Enterprise Security Operations, Threat Detection & Incident Response (Step 33).

Revision ID: 020_enterprise_security_operations_threat_detection
Revises: 019_enterprise_performance_indexes
Create Date: 2026-10-15 20:00:00.000000

Creates normalized enterprise security operations tables:
- security_incidents: prioritized security incident management
- security_detections: normalized threat signals and evidence links
- security_response_actions: controlled automated & manual containment actions
- security_incident_notes: append-only forensic investigation timeline
- security_remediation_tasks: remediation and post-incident verification tasks
- security_detection_rules: server-side configurable threat detection rules
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "020_enterprise_security_operations_threat_detection"
down_revision = "019_enterprise_performance_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Security Incidents
    op.create_table(
        "security_incidents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column("incident_number", sa.String(32), unique=True, nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False, server_default="MEDIUM", index=True),
        sa.Column("confidence", sa.String(16), nullable=False, server_default="MEDIUM"),
        sa.Column("status", sa.String(32), nullable=False, server_default="NEW", index=True),
        sa.Column(
            "assigned_to_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "resolved_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("triaged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("contained_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_reason", sa.String(64), nullable=True),
        sa.Column("closure_summary", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_sec_incident_tenant_status", "security_incidents", ["tenant_id", "status"])
    op.create_index("idx_sec_incident_tenant_severity", "security_incidents", ["tenant_id", "severity"])
    op.create_index("idx_sec_incident_tenant_created", "security_incidents", ["tenant_id", "created_at"])

    # 2. Security Detections
    op.create_table(
        "security_detections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "incident_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("security_incidents.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("rule_id", sa.String(64), nullable=False, index=True),
        sa.Column("rule_version", sa.String(16), nullable=False, server_default="1.0.0"),
        sa.Column("event_type", sa.String(64), nullable=False, index=True),
        sa.Column("severity", sa.String(16), nullable=False, server_default="MEDIUM", index=True),
        sa.Column("confidence", sa.String(16), nullable=False, server_default="MEDIUM"),
        sa.Column("detection_source", sa.String(64), nullable=False),
        sa.Column("actor_type", sa.String(32), nullable=False, server_default="USER"),
        sa.Column("actor_id", sa.String(128), nullable=True, index=True),
        sa.Column("target_resource_type", sa.String(64), nullable=True),
        sa.Column("target_resource_id", sa.String(128), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=False, server_default="unknown", index=True),
        sa.Column("request_id", sa.String(128), nullable=False, server_default="-"),
        sa.Column(
            "audit_log_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("intelligence_audit_logs.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("dedup_fingerprint", sa.String(128), nullable=False, index=True),
        sa.Column("occurrence_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("details_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default="{}"),
        sa.Column("status", sa.String(32), nullable=False, server_default="UNTRIAGED", index=True),
        sa.Column("suppression_reason", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_sec_detect_tenant_fingerprint", "security_detections", ["tenant_id", "dedup_fingerprint"])
    op.create_index("idx_sec_detect_tenant_created", "security_detections", ["tenant_id", "created_at"])
    op.create_index("idx_sec_detect_ip", "security_detections", ["ip_address"])

    # 3. Security Response Actions
    op.create_table(
        "security_response_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "incident_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("security_incidents.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("action_type", sa.String(64), nullable=False),
        sa.Column("target_type", sa.String(32), nullable=False),
        sa.Column("target_identifier", sa.String(255), nullable=False),
        sa.Column("risk_level", sa.String(16), nullable=False, server_default="LOW"),
        sa.Column("requires_approval", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("status", sa.String(32), nullable=False, server_default="PROPOSED", index=True),
        sa.Column("idempotency_key", sa.String(128), unique=True, nullable=False, index=True),
        sa.Column(
            "proposed_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "approved_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "executed_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("execution_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default="{}"),
        sa.Column("execution_result", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default="{}"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rolled_back_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_sec_action_tenant_status", "security_response_actions", ["tenant_id", "status"])
    op.create_index("idx_sec_action_target", "security_response_actions", ["target_type", "target_identifier"])

    # 4. Security Incident Notes
    op.create_table(
        "security_incident_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "incident_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("security_incidents.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "author_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("note_type", sa.String(32), nullable=False, server_default="INVESTIGATION"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("evidence_references", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 5. Security Remediation Tasks
    op.create_table(
        "security_remediation_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "incident_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("security_incidents.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "assigned_to_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING", index=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_sec_task_tenant_status", "security_remediation_tasks", ["tenant_id", "status"])

    # 6. Security Detection Rules Config
    op.create_table(
        "security_detection_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("rule_id", sa.String(64), unique=True, nullable=False, index=True),
        sa.Column("version", sa.String(16), nullable=False, server_default="1.0.0"),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False, server_default="MEDIUM"),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("evaluation_window_seconds", sa.Integer(), nullable=False, server_default="600"),
        sa.Column("threshold", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("recommended_action", sa.String(64), nullable=True),
        sa.Column("config_parameters", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default="{}"),
        sa.Column("exclusions_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("security_detection_rules")
    op.drop_table("security_remediation_tasks")
    op.drop_table("security_incident_notes")
    op.drop_table("security_response_actions")
    op.drop_table("security_detections")
    op.drop_table("security_incidents")
