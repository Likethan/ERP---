"""Enterprise Campus Sustainability, Energy Management, Environmental Compliance & Carbon Intelligence (Step 67).

Revision ID: 049_enterprise_campus_sustainability_carbon_intelligence
Revises: 048_enterprise_student_housing_offcampus_accommodation
Create Date: 2026-10-29 00:15:00.000000

Creates domain tables and indexes for:
- sustainability_profiles
- sustainability_targets
- sustainability_emission_factors
- sustainability_resource_measurements
- sustainability_water_incidents
- sustainability_waste_records
- sustainability_carbon_emissions
- sustainability_initiatives
- sustainability_compliance_requirements
- sustainability_corrective_actions
- sustainability_iot_meters
- sustainability_iot_events
- sustainability_import_batches
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "049_enterprise_campus_sustainability_carbon_intelligence"
down_revision = "048_enterprise_student_housing_offcampus_accommodation"
branch_labels = None
depends_on = None

json_type = sa.JSON().with_variant(postgresql.JSONB, "postgresql")


def upgrade() -> None:
    # 1. Sustainability Profiles
    op.create_table(
        "sustainability_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("campus_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_campuses.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("reporting_cycle", sa.String(32), nullable=False, server_default="ANNUAL"),
        sa.Column("baseline_year", sa.Integer(), nullable=False, server_default="2022"),
        sa.Column("target_net_zero_year", sa.Integer(), nullable=False, server_default="2040"),
        sa.Column("lead_coordinator_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("coordinator_name", sa.String(128), nullable=False, server_default="Sustainability Office"),
        sa.Column("coordinator_email", sa.String(128), nullable=False, server_default="sustainability@campus.edu"),
        sa.Column("settings", json_type, nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "code", name="uq_sustainability_profile_code"),
    )
    op.create_index("idx_sustainability_profile_tenant_campus", "sustainability_profiles", ["tenant_id", "campus_id"])

    # 2. Sustainability Targets
    op.create_table(
        "sustainability_targets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sustainability_profiles.id", ondelete="CASCADE"), nullable=True),
        sa.Column("campus_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_campuses.id", ondelete="SET NULL"), nullable=True),
        sa.Column("category", sa.String(32), nullable=False, server_default="ENERGY_REDUCTION"),
        sa.Column("target_code", sa.String(64), nullable=False),
        sa.Column("title", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("baseline_year", sa.Integer(), nullable=False, server_default="2022"),
        sa.Column("baseline_value", sa.Numeric(14, 3), nullable=False),
        sa.Column("target_year", sa.Integer(), nullable=False, server_default="2030"),
        sa.Column("target_value", sa.Numeric(14, 3), nullable=False),
        sa.Column("current_value", sa.Numeric(14, 3), nullable=False, server_default="0.000"),
        sa.Column("unit", sa.String(32), nullable=False, server_default="kWh"),
        sa.Column("reduction_pct_target", sa.Numeric(5, 2), nullable=False, server_default="25.00"),
        sa.Column("reduction_pct_achieved", sa.Numeric(5, 2), nullable=False, server_default="0.00"),
        sa.Column("status", sa.String(32), nullable=False, server_default="ON_TRACK"),
        sa.Column("responsible_team", sa.String(128), nullable=False, server_default="Estate & Facilities"),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "target_code", name="uq_sustainability_target_code"),
    )
    op.create_index("idx_sustainability_target_status", "sustainability_targets", ["tenant_id", "category", "status"])

    # 3. Emission Factors
    op.create_table(
        "sustainability_emission_factors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("factor_code", sa.String(64), nullable=False),
        sa.Column("category", sa.String(32), nullable=False, server_default="ELECTRICITY_GRID"),
        sa.Column("scope", sa.String(16), nullable=False, server_default="SCOPE_2"),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("source_authority", sa.String(128), nullable=False),
        sa.Column("factor_version", sa.String(32), nullable=False, server_default="v2024.1"),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("factor_value", sa.Numeric(12, 6), nullable=False),
        sa.Column("unit_denominator", sa.String(32), nullable=False, server_default="kWh"),
        sa.Column("gwp_standard", sa.String(32), nullable=False, server_default="AR5"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "factor_code", "factor_version", name="uq_sustainability_factor_version"),
    )
    op.create_index("idx_sustainability_factor_lookup", "sustainability_emission_factors", ["tenant_id", "category", "scope", "is_active"])

    # 4. Resource Measurements
    op.create_table(
        "sustainability_resource_measurements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("campus_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_campuses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("building_name", sa.String(128), nullable=False),
        sa.Column("meter_code", sa.String(64), nullable=False),
        sa.Column("resource_type", sa.String(32), nullable=False, server_default="ELECTRICITY_GRID"),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reading_value", sa.Numeric(14, 3), nullable=False),
        sa.Column("unit", sa.String(32), nullable=False, server_default="kWh"),
        sa.Column("source_type", sa.String(32), nullable=False, server_default="IOT_SENSOR"),
        sa.Column("baseline_expected_value", sa.Numeric(14, 3), nullable=True),
        sa.Column("variance_pct", sa.Numeric(6, 2), nullable=True),
        sa.Column("is_anomaly", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("anomaly_severity", sa.String(32), nullable=True),
        sa.Column("anomaly_reason", sa.Text(), nullable=True),
        sa.Column("verified_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("verification_status", sa.String(32), nullable=False, server_default="VERIFIED"),
        sa.Column("linked_work_order_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_sustainability_meas_lookup", "sustainability_resource_measurements", ["tenant_id", "campus_id", "resource_type", "period_start"])
    op.create_index("idx_sustainability_meas_anomaly", "sustainability_resource_measurements", ["tenant_id", "is_anomaly"])

    # 5. Water Incidents
    op.create_table(
        "sustainability_water_incidents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("campus_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_campuses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("incident_code", sa.String(64), nullable=False),
        sa.Column("incident_type", sa.String(32), nullable=False, server_default="LEAK_PIPE"),
        sa.Column("location", sa.String(128), nullable=False),
        sa.Column("estimated_loss_litres", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("severity", sa.String(32), nullable=False, server_default="MEDIUM"),
        sa.Column("status", sa.String(32), nullable=False, server_default="DETECTED"),
        sa.Column("linked_work_order_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("remediation_notes", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "incident_code", name="uq_sustainability_water_incident_code"),
    )
    op.create_index("idx_sustainability_water_status", "sustainability_water_incidents", ["tenant_id", "status"])

    # 6. Waste Records
    op.create_table(
        "sustainability_waste_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("campus_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_campuses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("waste_code", sa.String(64), nullable=False),
        sa.Column("waste_category", sa.String(32), nullable=False, server_default="GENERAL"),
        sa.Column("is_hazardous", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("quantity", sa.Numeric(12, 3), nullable=False),
        sa.Column("unit", sa.String(32), nullable=False, server_default="kg"),
        sa.Column("collection_date", sa.Date(), nullable=False),
        sa.Column("disposal_method", sa.String(32), nullable=False, server_default="RECYCLING_VENDOR"),
        sa.Column("partner_name", sa.String(128), nullable=False),
        sa.Column("manifest_number", sa.String(64), nullable=True),
        sa.Column("certificate_ref", sa.String(128), nullable=True),
        sa.Column("verified_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="COLLECTED"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "waste_code", name="uq_sustainability_waste_code"),
    )
    op.create_index("idx_sustainability_waste_cat", "sustainability_waste_records", ["tenant_id", "waste_category", "is_hazardous"])

    # 7. Carbon Emissions
    op.create_table(
        "sustainability_carbon_emissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("campus_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_campuses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reporting_period", sa.String(32), nullable=False),
        sa.Column("scope", sa.String(16), nullable=False, server_default="SCOPE_2"),
        sa.Column("activity_category", sa.String(64), nullable=False),
        sa.Column("activity_quantity", sa.Numeric(14, 3), nullable=False),
        sa.Column("activity_unit", sa.String(32), nullable=False),
        sa.Column("emission_factor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sustainability_emission_factors.id", ondelete="SET NULL"), nullable=True),
        sa.Column("factor_value_applied", sa.Numeric(12, 6), nullable=False),
        sa.Column("factor_source_applied", sa.String(128), nullable=False),
        sa.Column("emissions_kg_co2e", sa.Numeric(16, 3), nullable=False),
        sa.Column("emissions_mt_co2e", sa.Numeric(14, 4), nullable=False),
        sa.Column("is_estimated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("calculation_method", sa.String(64), nullable=False, server_default="LOCATION_BASED"),
        sa.Column("audit_hash", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_sustainability_carbon_lookup", "sustainability_carbon_emissions", ["tenant_id", "campus_id", "reporting_period", "scope"])

    # 8. Sustainability Initiatives
    op.create_table(
        "sustainability_initiatives",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("campus_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_campuses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("initiative_code", sa.String(64), nullable=False),
        sa.Column("title", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(32), nullable=False, server_default="SOLAR_ROOFTOP"),
        sa.Column("status", sa.String(32), nullable=False, server_default="PROPOSED"),
        sa.Column("budget_allocated", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("budget_spent", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("annual_co2_savings_mt", sa.Numeric(10, 3), nullable=False, server_default="0.000"),
        sa.Column("annual_energy_savings_kwh", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("annual_water_savings_kl", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("completion_date", sa.Date(), nullable=True),
        sa.Column("responsible_owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("lead_department", sa.String(128), nullable=False, server_default="Estate Operations"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "initiative_code", name="uq_sustainability_initiative_code"),
    )
    op.create_index("idx_sustainability_initiative_status", "sustainability_initiatives", ["tenant_id", "status"])

    # 9. Environmental Compliance Requirements
    op.create_table(
        "sustainability_compliance_requirements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("campus_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_campuses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("compliance_code", sa.String(64), nullable=False),
        sa.Column("regulation_title", sa.String(255), nullable=False),
        sa.Column("regulatory_body", sa.String(128), nullable=False),
        sa.Column("compliance_category", sa.String(32), nullable=False, server_default="WATER_CONSENT"),
        sa.Column("frequency", sa.String(32), nullable=False, server_default="ANNUAL"),
        sa.Column("last_audit_date", sa.Date(), nullable=True),
        sa.Column("next_renewal_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="COMPLIANT"),
        sa.Column("permit_number", sa.String(128), nullable=True),
        sa.Column("document_reference", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "compliance_code", name="uq_sustainability_compliance_code"),
    )
    op.create_index("idx_sustainability_compliance_status", "sustainability_compliance_requirements", ["tenant_id", "status", "next_renewal_date"])

    # 10. Environmental Corrective Actions
    op.create_table(
        "sustainability_corrective_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("requirement_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sustainability_compliance_requirements.id", ondelete="CASCADE"), nullable=True),
        sa.Column("campus_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_campuses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action_code", sa.String(64), nullable=False),
        sa.Column("issue_description", sa.Text(), nullable=False),
        sa.Column("action_plan", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(32), nullable=False, server_default="MEDIUM"),
        sa.Column("status", sa.String(32), nullable=False, server_default="OPEN"),
        sa.Column("assigned_to_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("linked_work_order_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "action_code", name="uq_sustainability_action_code"),
    )
    op.create_index("idx_sustainability_action_status", "sustainability_corrective_actions", ["tenant_id", "status"])

    # 11. IoT Meter Streams
    op.create_table(
        "sustainability_iot_meters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("device_id", sa.String(64), nullable=False),
        sa.Column("device_name", sa.String(128), nullable=False),
        sa.Column("campus_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_campuses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("building_name", sa.String(128), nullable=False),
        sa.Column("meter_type", sa.String(32), nullable=False, server_default="ELECTRICITY_GRID"),
        sa.Column("protocol", sa.String(32), nullable=False, server_default="MQTT"),
        sa.Column("sampling_interval_secs", sa.Integer(), nullable=False, server_default="900"),
        sa.Column("last_heartbeat", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_reading_value", sa.Numeric(14, 3), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="ONLINE"),
        sa.Column("api_key_hash", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "device_id", name="uq_sustainability_iot_device_id"),
    )
    op.create_index("idx_sustainability_iot_meter_status", "sustainability_iot_meters", ["tenant_id", "campus_id", "status"])

    # 12. IoT Events (with dedup hash index)
    op.create_table(
        "sustainability_iot_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("device_id", sa.String(64), nullable=False),
        sa.Column("event_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metric_name", sa.String(64), nullable=False),
        sa.Column("metric_value", sa.Numeric(14, 3), nullable=False),
        sa.Column("unit", sa.String(32), nullable=False, server_default="kWh"),
        sa.Column("raw_payload", json_type, nullable=True),
        sa.Column("ingestion_status", sa.String(32), nullable=False, server_default="PROCESSED"),
        sa.Column("dedup_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_sustainability_iot_dedup", "sustainability_iot_events", ["tenant_id", "dedup_hash"], unique=True)
    op.create_index("idx_sustainability_iot_device_time", "sustainability_iot_events", ["tenant_id", "device_id", "event_timestamp"])

    # 13. Sustainability Import Batches
    op.create_table(
        "sustainability_import_batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("batch_number", sa.String(64), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(32), nullable=False, server_default="ENERGY_INVOICE"),
        sa.Column("total_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processed_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("imported_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("error_summary", json_type, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "batch_number", name="uq_sustainability_import_batch_no"),
    )


def downgrade() -> None:
    op.drop_table("sustainability_import_batches")
    op.drop_table("sustainability_iot_events")
    op.drop_table("sustainability_iot_meters")
    op.drop_table("sustainability_corrective_actions")
    op.drop_table("sustainability_compliance_requirements")
    op.drop_table("sustainability_initiatives")
    op.drop_table("sustainability_carbon_emissions")
    op.drop_table("sustainability_waste_records")
    op.drop_table("sustainability_water_incidents")
    op.drop_table("sustainability_resource_measurements")
    op.drop_table("sustainability_emission_factors")
    op.drop_table("sustainability_targets")
    op.drop_table("sustainability_profiles")

