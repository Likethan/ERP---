"""Enterprise Transport, Fleet, Routes & Student Mobility Management (Step 55).

Revision ID: 040_enterprise_transport_fleet_routes_mobility
Revises: 039_enterprise_hostel_residential_life_management
Create Date: 2026-10-23 12:00:00.000000

Creates normalized tables and schema objects for:
- transport_service_configs: Transport service areas, operational calendars, policies
- infrastructure_vehicles: Fleet registry, specs, seating, compliance certificates, odometer
- infrastructure_drivers: Driver credentials, licenses, background checks, shift history
- infrastructure_routes: Corridors, stops itineraries, schedules, capacity limits
- infrastructure_stops: Sequential boarding points, landmarks, geocoordinates, fares
- transport_applications: Student transport registrations, reviews, and status workflow
- infrastructure_transport_allocations: Concurrency-safe seat allocations and bus passes
- transport_waitlists: Priority-scored passenger waiting lists
- transport_trips: Scheduled transit runs, pre-trip checklists, dispatch state transitions
- transport_boarding_records: Trip manifests, boarding scans, student attendance verification
- transport_tracking_sources: Vehicle telematics and tracking provider configurations
- transport_location_snapshots: Audited privacy-conscious GPS/telematics location fixes
- transport_fee_plans: Route and stop transport fee schedules and pricing matrices
- transport_fuel_logs: Fuel purchases, odometer progression, and fleet operating costs
- transport_incidents: Safety breakdowns, route disruptions, and emergency response records
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "040_enterprise_transport_fleet_routes_mobility"
down_revision = "039_enterprise_hostel_residential_life_management"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Transport Service Configurations
    op.create_table(
        "transport_service_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "campus_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_campuses.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("service_code", sa.String(32), nullable=False),
        sa.Column("service_name", sa.String(128), nullable=False),
        sa.Column(
            "academic_year_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_academic_years.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("zone_code", sa.String(64), nullable=True),
        sa.Column("operating_period_start", sa.Date(), nullable=True),
        sa.Column("operating_period_end", sa.Date(), nullable=True),
        sa.Column("eligibility_criteria", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("capacity_policy", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "service_code", name="uq_tr_config_tenant_code"),
    )
    op.create_index("idx_tr_config_tenant", "transport_service_configs", ["tenant_id", "is_active"])

    # 2. Infrastructure Vehicles (Fleet Registry)
    op.create_table(
        "infrastructure_vehicles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "asset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("asset_registry.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "campus_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_campuses.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("registration_number", sa.String(32), nullable=False),
        sa.Column("fleet_identifier", sa.String(64), nullable=True),
        sa.Column("vehicle_category", sa.String(32), nullable=False, server_default="BUS"),
        sa.Column("make", sa.String(64), nullable=True),
        sa.Column("model", sa.String(64), nullable=True),
        sa.Column("manufacturing_year", sa.Integer(), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("accessible_seating_capacity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("permitted_passenger_capacity", sa.Integer(), nullable=True),
        sa.Column("insurance_policy_number", sa.String(128), nullable=True),
        sa.Column("insurance_expiry", sa.Date(), nullable=False),
        sa.Column("fitness_certificate_number", sa.String(128), nullable=True),
        sa.Column("fitness_certificate_expiry", sa.Date(), nullable=False),
        sa.Column("permit_number", sa.String(128), nullable=True),
        sa.Column("permit_expiry", sa.Date(), nullable=True),
        sa.Column("pollution_certificate_expiry", sa.Date(), nullable=True),
        sa.Column("fuel_type", sa.String(32), nullable=False, server_default="DIESEL"),
        sa.Column("operational_depot", sa.String(128), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"),
        sa.Column("current_odometer_km", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("safety_equipment_details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "registration_number", name="uq_vehicles_reg_number"),
    )
    op.create_index("idx_tr_vehicles_tenant_status", "infrastructure_vehicles", ["tenant_id", "status"])

    # 3. Infrastructure Drivers
    op.create_table(
        "infrastructure_drivers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "employee_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workforce_employees.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("full_name", sa.String(128), nullable=False),
        sa.Column("license_number", sa.String(64), nullable=False),
        sa.Column("license_categories", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("license_expiry", sa.Date(), nullable=False),
        sa.Column("phone_number", sa.String(32), nullable=False),
        sa.Column("email", sa.String(128), nullable=True),
        sa.Column("badge_number", sa.String(64), nullable=True),
        sa.Column("badge_expiry", sa.Date(), nullable=True),
        sa.Column("certifications", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("background_verification_status", sa.String(32), nullable=False, server_default="VERIFIED"),
        sa.Column("shift_preference", sa.String(32), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"),
        sa.Column("emergency_contact_name", sa.String(128), nullable=True),
        sa.Column("emergency_contact_phone", sa.String(32), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "license_number", name="uq_drivers_license"),
    )
    op.create_index("idx_tr_drivers_tenant_status", "infrastructure_drivers", ["tenant_id", "status"])

    # 4. Infrastructure Routes
    op.create_table(
        "infrastructure_routes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "campus_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_campuses.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("route_code", sa.String(32), nullable=False),
        sa.Column("route_name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_point", sa.String(128), nullable=False, server_default="Campus Depot"),
        sa.Column("end_point", sa.String(128), nullable=False, server_default="Terminal"),
        sa.Column("distance_km", sa.Numeric(8, 2), nullable=False, server_default="0.00"),
        sa.Column("estimated_duration_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("morning_departure_time", sa.Time(), nullable=True),
        sa.Column("evening_return_time", sa.Time(), nullable=True),
        sa.Column(
            "vehicle_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("infrastructure_vehicles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "driver_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("infrastructure_drivers.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="52"),
        sa.Column("allocated_students", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("direction", sa.String(32), nullable=False, server_default="ROUND_TRIP"),
        sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "route_code", name="uq_routes_tenant_code"),
    )
    op.create_index("idx_tr_routes_tenant_status", "infrastructure_routes", ["tenant_id", "status"])

    # 5. Infrastructure Stops
    op.create_table(
        "infrastructure_stops",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "route_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("infrastructure_routes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("stop_name", sa.String(128), nullable=False),
        sa.Column("stop_code", sa.String(32), nullable=True),
        sa.Column("stop_sequence", sa.Integer(), nullable=False),
        sa.Column("address", sa.String(255), nullable=True),
        sa.Column("landmark", sa.String(128), nullable=True),
        sa.Column("latitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("longitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("pickup_time", sa.Time(), nullable=False),
        sa.Column("drop_time", sa.Time(), nullable=True),
        sa.Column("fare_annual", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("fare_term", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("fare_monthly", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("max_boarding_capacity", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.create_index("idx_tr_stops_route_seq", "infrastructure_stops", ["route_id", "stop_sequence"])

    # 6. Transport Applications
    op.create_table(
        "transport_applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("application_number", sa.String(32), nullable=False),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_students.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "academic_year_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_academic_years.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "preferred_route_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("infrastructure_routes.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "preferred_stop_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("infrastructure_stops.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("service_type", sa.String(32), nullable=False, server_default="ROUND_TRIP"),
        sa.Column("status", sa.String(32), nullable=False, server_default="SUBMITTED"),
        sa.Column("priority_score", sa.Numeric(8, 2), nullable=False, server_default="0.00"),
        sa.Column("accessibility_needed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("special_requests", sa.Text(), nullable=True),
        sa.Column(
            "reviewer_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "application_number", name="uq_tr_appl_tenant_num"),
    )
    op.create_index("idx_tr_appl_tenant_student", "transport_applications", ["tenant_id", "student_id"])

    # 7. Transport Allocations (Passes)
    op.create_table(
        "infrastructure_transport_allocations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("pass_number", sa.String(64), nullable=False),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_students.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "academic_year_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_academic_years.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "route_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("infrastructure_routes.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "stop_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("infrastructure_stops.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "vehicle_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("infrastructure_vehicles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("service_type", sa.String(32), nullable=False, server_default="ROUND_TRIP"),
        sa.Column("seat_number", sa.String(32), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.Column(
            "finance_invoice_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("finance_invoices.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("fee_status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "pass_number", name="uq_tr_alloc_pass_num"),
    )
    op.create_index("idx_tr_alloc_tenant_student", "infrastructure_transport_allocations", ["tenant_id", "student_id"])
    op.create_index("idx_tr_alloc_route_status", "infrastructure_transport_allocations", ["tenant_id", "route_id", "status"])

    # 8. Transport Waitlists
    op.create_table(
        "transport_waitlists",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "route_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("infrastructure_routes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "stop_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("infrastructure_stops.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_students.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("transport_applications.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("priority_score", sa.Numeric(8, 2), nullable=False, server_default="0.00"),
        sa.Column("queue_position", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(32), nullable=False, server_default="WAITING"),
        sa.Column("offered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_tr_waitlist_route_status", "transport_waitlists", ["tenant_id", "route_id", "status"])

    # 9. Transport Trips
    op.create_table(
        "transport_trips",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("trip_number", sa.String(32), nullable=False),
        sa.Column(
            "route_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("infrastructure_routes.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "vehicle_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("infrastructure_vehicles.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "driver_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("infrastructure_drivers.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("trip_date", sa.Date(), nullable=False),
        sa.Column("service_window", sa.String(32), nullable=False, server_default="MORNING_PICKUP"),
        sa.Column("scheduled_start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scheduled_end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actual_start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("start_odometer_km", sa.Numeric(12, 2), nullable=True),
        sa.Column("end_odometer_km", sa.Numeric(12, 2), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="SCHEDULED"),
        sa.Column("pre_trip_checklist_completed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("checklist_notes", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("disruption_notes", sa.Text(), nullable=True),
        sa.Column(
            "dispatched_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "trip_number", name="uq_tr_trips_tenant_num"),
    )
    op.create_index("idx_tr_trips_date_route", "transport_trips", ["tenant_id", "trip_date", "route_id"])
    op.create_index("idx_tr_trips_vehicle_date", "transport_trips", ["tenant_id", "vehicle_id", "trip_date"])
    op.create_index("idx_tr_trips_driver_date", "transport_trips", ["tenant_id", "driver_id", "trip_date"])

    # 10. Transport Boarding Records (Trip Manifest)
    op.create_table(
        "transport_boarding_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "trip_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("transport_trips.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_students.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "allocation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("infrastructure_transport_allocations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "stop_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("infrastructure_stops.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("boarding_status", sa.String(32), nullable=False, server_default="EXPECTED"),
        sa.Column("boarding_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("drop_off_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verification_method", sa.String(32), nullable=False, server_default="MANUAL"),
        sa.Column(
            "verified_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("remarks", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_tr_boarding_trip_student", "transport_boarding_records", ["tenant_id", "trip_id", "student_id"])

    # 11. Transport Tracking Sources
    op.create_table(
        "transport_tracking_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "vehicle_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("infrastructure_vehicles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider_name", sa.String(64), nullable=False, server_default="DISABLED"),
        sa.Column("device_identifier", sa.String(128), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="NOT_CONFIGURED"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "vehicle_id", name="uq_tr_tracking_vehicle"),
    )

    # 12. Transport Location Snapshots
    op.create_table(
        "transport_location_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "vehicle_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("infrastructure_vehicles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "trip_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("transport_trips.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("latitude", sa.Numeric(10, 7), nullable=False),
        sa.Column("longitude", sa.Numeric(10, 7), nullable=False),
        sa.Column("speed_kmh", sa.Numeric(6, 2), nullable=False, server_default="0.00"),
        sa.Column("heading_degrees", sa.Numeric(5, 2), nullable=True),
        sa.Column("odometer_reading", sa.Numeric(12, 2), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("data_source", sa.String(64), nullable=False, server_default="TELEMATICS"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_tr_loc_snap_vehicle_time", "transport_location_snapshots", ["tenant_id", "vehicle_id", "recorded_at"])

    # 13. Transport Fee Plans
    op.create_table(
        "transport_fee_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column(
            "academic_year_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_academic_years.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "campus_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_campuses.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "route_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("infrastructure_routes.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "stop_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("infrastructure_stops.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("service_type", sa.String(32), nullable=False, server_default="ROUND_TRIP"),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(8), nullable=False, server_default="INR"),
        sa.Column("billing_cycle", sa.String(32), nullable=False, server_default="ANNUAL"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_tr_fee_plan_code"),
    )

    # 14. Transport Fuel Logs
    op.create_table(
        "transport_fuel_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "vehicle_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("infrastructure_vehicles.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "driver_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("infrastructure_drivers.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "trip_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("transport_trips.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("fuel_date", sa.Date(), nullable=False),
        sa.Column("odometer_reading", sa.Numeric(12, 2), nullable=False),
        sa.Column("fuel_quantity_liters", sa.Numeric(8, 2), nullable=False),
        sa.Column("fuel_cost_total", sa.Numeric(10, 2), nullable=False),
        sa.Column("fuel_station_name", sa.String(128), nullable=True),
        sa.Column("receipt_number", sa.String(64), nullable=True),
        sa.Column(
            "verified_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_tr_fuel_vehicle_date", "transport_fuel_logs", ["tenant_id", "vehicle_id", "fuel_date"])

    # 15. Transport Incidents
    op.create_table(
        "transport_incidents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("incident_number", sa.String(32), nullable=False),
        sa.Column(
            "trip_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("transport_trips.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "vehicle_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("infrastructure_vehicles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "driver_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("infrastructure_drivers.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "route_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("infrastructure_routes.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("incident_type", sa.String(32), nullable=False, server_default="BREAKDOWN"),
        sa.Column("severity", sa.String(32), nullable=False, server_default="MEDIUM"),
        sa.Column("incident_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("location_description", sa.String(255), nullable=False),
        sa.Column(
            "reporter_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("action_taken", sa.Text(), nullable=True),
        sa.Column("involved_student_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("emergency_services_contacted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("status", sa.String(32), nullable=False, server_default="REPORTED"),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "incident_number", name="uq_tr_incidents_tenant_num"),
    )
    op.create_index("idx_tr_incidents_tenant_time", "transport_incidents", ["tenant_id", "incident_time"])


def downgrade() -> None:
    op.drop_table("transport_incidents")
    op.drop_table("transport_fuel_logs")
    op.drop_table("transport_fee_plans")
    op.drop_table("transport_location_snapshots")
    op.drop_table("transport_tracking_sources")
    op.drop_table("transport_boarding_records")
    op.drop_table("transport_trips")
    op.drop_table("transport_waitlists")
    op.drop_table("infrastructure_transport_allocations")
    op.drop_table("transport_applications")
    op.drop_table("infrastructure_stops")
    op.drop_table("infrastructure_routes")
    op.drop_table("infrastructure_drivers")
    op.drop_table("infrastructure_vehicles")
    op.drop_table("transport_service_configs")
