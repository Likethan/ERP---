"""Enterprise Campus Physical Security, Visitor Management, Gate Operations & Emergency Response (Step 68).

Revision ID: 050_enterprise_campus_security_access_control_emergency
Revises: 049_enterprise_campus_sustainability_carbon_intelligence
Create Date: 2026-10-29 18:00:00.000000

Creates domain tables and indexes for:
- campus_security_checkpoints
- campus_security_zones
- campus_security_visitor_profiles
- campus_security_visitor_requests
- campus_security_visitor_passes
- campus_security_contractor_profiles
- campus_security_access_grants
- campus_security_physical_incidents
- campus_security_emergency_events
- campus_security_emergency_tasks
- campus_security_patrol_plans
- campus_security_patrol_records
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "050_enterprise_campus_security_access_control_emergency"
down_revision = "049_enterprise_campus_sustainability_carbon_intelligence"
branch_labels = None
depends_on = None

json_type = sa.JSON().with_variant(postgresql.JSONB, "postgresql")


def upgrade() -> None:
    # 1. Security Checkpoints (Gates & Barriers)
    op.create_table(
        "campus_security_checkpoints",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("checkpoint_type", sa.String(32), nullable=False, server_default="MAIN_GATE"),
        sa.Column("location_description", sa.String(255), nullable=False),
        sa.Column("is_manned", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("operating_hours", sa.String(64), nullable=False, server_default="24x7"),
        sa.Column("guard_post_phone", sa.String(32), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("metadata_json", json_type, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "code", name="uq_campus_sec_chkpt_tenant_code"),
    )
    op.create_index("ix_campus_sec_chkpt_tenant_active", "campus_security_checkpoints", ["tenant_id", "is_active"])
    op.create_index("ix_campus_sec_chkpt_type", "campus_security_checkpoints", ["tenant_id", "checkpoint_type"])

    # 2. Security Zones (Restricted Areas & Clearances)
    op.create_table(
        "campus_security_zones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("clearance_level", sa.String(32), nullable=False, server_default="CAMPUS_GENERAL"),
        sa.Column("building_name", sa.String(128), nullable=True),
        sa.Column("floor_number", sa.Integer(), nullable=True),
        sa.Column("requires_escort", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("max_occupancy", sa.Integer(), nullable=True),
        sa.Column("emergency_assembly_point", sa.String(128), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("metadata_json", json_type, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "code", name="uq_campus_sec_zone_tenant_code"),
    )
    op.create_index("ix_campus_sec_zone_tenant_clearance", "campus_security_zones", ["tenant_id", "clearance_level"])

    # 3. Visitor Profiles
    op.create_table(
        "campus_security_visitor_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("full_name", sa.String(128), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(32), nullable=False),
        sa.Column("organization", sa.String(128), nullable=True),
        sa.Column("id_document_type", sa.String(32), nullable=False, server_default="OTHER"),
        sa.Column("id_document_number_masked", sa.String(64), nullable=True),
        sa.Column("is_vip", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_blacklisted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("blacklist_reason", sa.Text(), nullable=True),
        sa.Column("total_visits", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata_json", json_type, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_campus_sec_visitor_tenant_phone", "campus_security_visitor_profiles", ["tenant_id", "phone"])
    op.create_index("ix_campus_sec_visitor_tenant_email", "campus_security_visitor_profiles", ["tenant_id", "email"])

    # 4. Visitor Requests
    op.create_table(
        "campus_security_visitor_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("request_number", sa.String(32), nullable=False),
        sa.Column("visitor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("campus_security_visitor_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("visitor_name", sa.String(128), nullable=False),
        sa.Column("visitor_phone", sa.String(32), nullable=False),
        sa.Column("visitor_email", sa.String(255), nullable=False),
        sa.Column("visitor_category", sa.String(32), nullable=False, server_default="GUEST"),
        sa.Column("host_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("host_name", sa.String(128), nullable=False),
        sa.Column("host_department", sa.String(128), nullable=True),
        sa.Column("visit_purpose", sa.String(255), nullable=False),
        sa.Column("destination_zone_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("campus_security_zones.id", ondelete="SET NULL"), nullable=True),
        sa.Column("destination_description", sa.String(255), nullable=False),
        sa.Column("expected_arrival_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expected_departure_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("approval_required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("approved_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("vehicle_number", sa.String(32), nullable=True),
        sa.Column("has_vehicle", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("accompanying_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata_json", json_type, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "request_number", name="uq_campus_sec_visreq_number"),
    )
    op.create_index("ix_campus_sec_visreq_tenant_status", "campus_security_visitor_requests", ["tenant_id", "status"])
    op.create_index("ix_campus_sec_visreq_arrival", "campus_security_visitor_requests", ["tenant_id", "expected_arrival_at"])

    # 5. Visitor Passes (Check-in & Sessions)
    op.create_table(
        "campus_security_visitor_passes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("pass_number", sa.String(32), nullable=False),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("campus_security_visitor_requests.id", ondelete="SET NULL"), nullable=True),
        sa.Column("visitor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("campus_security_visitor_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("visitor_name", sa.String(128), nullable=False),
        sa.Column("visitor_category", sa.String(32), nullable=False),
        sa.Column("host_name", sa.String(128), nullable=False),
        sa.Column("destination", sa.String(255), nullable=False),
        sa.Column("signed_token", sa.String(255), unique=True, nullable=False),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="ISSUED"),
        sa.Column("check_in_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("check_in_checkpoint_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("campus_security_checkpoints.id", ondelete="SET NULL"), nullable=True),
        sa.Column("check_in_officer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("check_out_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("check_out_checkpoint_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("campus_security_checkpoints.id", ondelete="SET NULL"), nullable=True),
        sa.Column("check_out_officer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("is_overdue", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revocation_reason", sa.Text(), nullable=True),
        sa.Column("metadata_json", json_type, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "pass_number", name="uq_campus_sec_vispass_number"),
    )
    op.create_index("ix_campus_sec_vispass_tenant_status", "campus_security_visitor_passes", ["tenant_id", "status"])
    op.create_index("ix_campus_sec_vispass_signed_token", "campus_security_visitor_passes", ["signed_token"])

    # 6. Contractor Profiles
    op.create_table(
        "campus_security_contractor_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("contractor_code", sa.String(32), nullable=False),
        sa.Column("organization_name", sa.String(128), nullable=False),
        sa.Column("contractor_name", sa.String(128), nullable=False),
        sa.Column("contractor_phone", sa.String(32), nullable=False),
        sa.Column("service_type", sa.String(64), nullable=False),
        sa.Column("work_order_reference", sa.String(64), nullable=True),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_until", sa.Date(), nullable=False),
        sa.Column("is_safety_induction_completed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("safety_induction_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"),
        sa.Column("authorized_zone_ids", json_type, nullable=True),
        sa.Column("emergency_contact_phone", sa.String(32), nullable=True),
        sa.Column("badge_reference", sa.String(64), nullable=True),
        sa.Column("metadata_json", json_type, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "contractor_code", name="uq_campus_sec_cont_code"),
    )
    op.create_index("ix_campus_sec_cont_tenant_status", "campus_security_contractor_profiles", ["tenant_id", "status"])

    # 7. Access Grants (Zone Access)
    op.create_table(
        "campus_security_access_grants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("grant_number", sa.String(32), nullable=False),
        sa.Column("zone_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("campus_security_zones.id", ondelete="CASCADE"), nullable=False),
        sa.Column("grantee_type", sa.String(32), nullable=False),
        sa.Column("grantee_id", sa.String(128), nullable=False),
        sa.Column("grantee_name", sa.String(128), nullable=False),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_temporary", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("granted_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("grant_reason", sa.String(255), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("revocation_reason", sa.Text(), nullable=True),
        sa.Column("metadata_json", json_type, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "grant_number", name="uq_campus_sec_accgrant_number"),
    )
    op.create_index("ix_campus_sec_accgrant_tenant_zone", "campus_security_access_grants", ["tenant_id", "zone_id"])
    op.create_index("ix_campus_sec_accgrant_grantee", "campus_security_access_grants", ["tenant_id", "grantee_id"])

    # 8. Physical Security Incidents
    op.create_table(
        "campus_security_physical_incidents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("incident_number", sa.String(32), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False, server_default="MEDIUM"),
        sa.Column("status", sa.String(32), nullable=False, server_default="REPORTED"),
        sa.Column("reported_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reported_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reported_by_name", sa.String(128), nullable=True),
        sa.Column("reported_location", sa.String(255), nullable=False),
        sa.Column("zone_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("campus_security_zones.id", ondelete="SET NULL"), nullable=True),
        sa.Column("checkpoint_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("campus_security_checkpoints.id", ondelete="SET NULL"), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("assigned_team", sa.String(64), nullable=True),
        sa.Column("assigned_to_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_escalated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("escalated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("escalation_reason", sa.Text(), nullable=True),
        sa.Column("resolution_summary", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("corrective_action_notes", sa.Text(), nullable=True),
        sa.Column("evidence_urls", json_type, nullable=True),
        sa.Column("metadata_json", json_type, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "incident_number", name="uq_campus_sec_inc_number"),
    )
    op.create_index("ix_campus_sec_inc_tenant_status", "campus_security_physical_incidents", ["tenant_id", "status"])
    op.create_index("ix_campus_sec_inc_tenant_severity", "campus_security_physical_incidents", ["tenant_id", "severity"])

    # 9. Emergency Events
    op.create_table(
        "campus_security_emergency_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("event_code", sa.String(32), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False, server_default="EMERGENCY"),
        sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"),
        sa.Column("affected_campus_areas", sa.String(255), nullable=False),
        sa.Column("affected_zone_ids", json_type, nullable=True),
        sa.Column("coordinator_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("coordinator_name", sa.String(128), nullable=False),
        sa.Column("emergency_broadcast_message", sa.Text(), nullable=True),
        sa.Column("initiated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("all_clear_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("after_action_report", sa.Text(), nullable=True),
        sa.Column("external_services_contacted", json_type, nullable=True),
        sa.Column("metadata_json", json_type, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "event_code", name="uq_campus_sec_emg_code"),
    )
    op.create_index("ix_campus_sec_emg_tenant_status", "campus_security_emergency_events", ["tenant_id", "status"])

    # 10. Emergency Tasks
    op.create_table(
        "campus_security_emergency_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("campus_security_emergency_events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("task_title", sa.String(255), nullable=False),
        sa.Column("priority", sa.String(16), nullable=False, server_default="HIGH"),
        sa.Column("assigned_to_role", sa.String(64), nullable=True),
        sa.Column("assigned_to_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("action_checklist", json_type, nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_campus_sec_emgtask_event", "campus_security_emergency_tasks", ["tenant_id", "event_id"])
    op.create_index("ix_campus_sec_emgtask_status", "campus_security_emergency_tasks", ["tenant_id", "status"])

    # 11. Security Patrol Plans
    op.create_table(
        "campus_security_patrol_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("plan_code", sa.String(32), nullable=False),
        sa.Column("title", sa.String(128), nullable=False),
        sa.Column("shift_name", sa.String(64), nullable=False, server_default="MORNING_SHIFT"),
        sa.Column("frequency_hours", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("assigned_team_name", sa.String(64), nullable=False),
        sa.Column("checkpoints_sequence", json_type, nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("supervisor_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("metadata_json", json_type, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "plan_code", name="uq_campus_sec_patrol_code"),
    )
    op.create_index("ix_campus_sec_patrol_tenant_active", "campus_security_patrol_plans", ["tenant_id", "is_active"])

    # 12. Patrol Checkpoint Records
    op.create_table(
        "campus_security_patrol_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("campus_security_patrol_plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("checkpoint_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("campus_security_checkpoints.id", ondelete="CASCADE"), nullable=False),
        sa.Column("officer_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("officer_name", sa.String(128), nullable=False),
        sa.Column("scheduled_round_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scanned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="COMPLETED"),
        sa.Column("verification_token", sa.String(128), nullable=True),
        sa.Column("observations", sa.Text(), nullable=True),
        sa.Column("incident_created_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("campus_security_physical_incidents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("supervisor_reviewed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("supervisor_review_notes", sa.Text(), nullable=True),
        sa.Column("metadata_json", json_type, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_campus_sec_patrolrec_plan", "campus_security_patrol_records", ["tenant_id", "plan_id"])
    op.create_index("ix_campus_sec_patrolrec_chkpt", "campus_security_patrol_records", ["tenant_id", "checkpoint_id"])
    op.create_index("ix_campus_sec_patrolrec_status", "campus_security_patrol_records", ["tenant_id", "status"])


def downgrade() -> None:
    op.drop_table("campus_security_patrol_records")
    op.drop_table("campus_security_patrol_plans")
    op.drop_table("campus_security_emergency_tasks")
    op.drop_table("campus_security_emergency_events")
    op.drop_table("campus_security_physical_incidents")
    op.drop_table("campus_security_access_grants")
    op.drop_table("campus_security_contractor_profiles")
    op.drop_table("campus_security_visitor_passes")
    op.drop_table("campus_security_visitor_requests")
    op.drop_table("campus_security_visitor_profiles")
    op.drop_table("campus_security_zones")
    op.drop_table("campus_security_checkpoints")

