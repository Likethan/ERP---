"""Enterprise Hostel, Residential Life, Room Allocation & Student Accommodation Management (Step 54).

Revision ID: 039_enterprise_hostel_residential_life_management
Revises: 038_enterprise_asset_lifecycle_maintenance_facilities
Create Date: 2026-10-22 12:00:00.000000

Creates normalized tables and enhances existing infrastructure tables for:
- Enhanced infrastructure_hostels, blocks, floors, rooms, beds, allocations, passes, complaints
- residential_application_cycles: Accommodation cycle and intake window management
- residential_applications: Student accommodation self-service applications and priority scoring
- residential_residents: Authoritative physical resident lifecycle, check-in, check-out, handovers
- residential_fee_plans: Room and facility pricing matrices and billing definitions
- residential_meal_plans: Mess catering plans, meal frequencies, and daily rates
- residential_meal_enrollments: Student mess enrollments and dietary preference tracking
- residential_visitors: Controlled visitor registration, approvals, check-in, and security passes
- residential_gate_passes: Resident movement authorization and security gate validation
- residential_incidents: Confidential hostel disciplinary, safety, and medical incident records
- residential_safety_inspections: Periodic safety, electrical, hygiene, and fire audit checklists
- residential_night_attendances: Daily residential roll-call and unauthorized absence tracking
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "039_enterprise_hostel_residential_life_management"
down_revision = "038_enterprise_asset_lifecycle_maintenance_facilities"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Application Cycles
    op.create_table(
        "residential_application_cycles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "academic_year_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_academic_years.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("cycle_name", sa.String(128), nullable=False),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT"),
        sa.Column("max_applications", sa.Integer(), nullable=True),
        sa.Column(
            "eligibility_criteria",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "priority_rules",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_appl_cycle_tenant_code"),
    )
    op.create_index("idx_appl_cycle_tenant_status", "residential_application_cycles", ["tenant_id", "status"])

    # 2. Student Applications
    op.create_table(
        "residential_applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "cycle_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("residential_application_cycles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_students.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("application_number", sa.String(32), nullable=False),
        sa.Column(
            "preferred_hostel_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("infrastructure_hostels.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("preferred_room_type", sa.String(32), nullable=False, server_default="DOUBLE"),
        sa.Column("special_requests", sa.Text(), nullable=True),
        sa.Column("accessibility_needed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("disability_notes", sa.Text(), nullable=True),
        sa.Column("emergency_contact_name", sa.String(128), nullable=True),
        sa.Column("emergency_contact_phone", sa.String(32), nullable=True),
        sa.Column("priority_score", sa.Numeric(8, 2), nullable=False, server_default="0.00"),
        sa.Column("status", sa.String(32), nullable=False, server_default="SUBMITTED"),
        sa.Column(
            "reviewer_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "allocated_bed_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("infrastructure_hostel_beds.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "cycle_id", "student_id", name="uq_appl_cycle_student"),
    )
    op.create_index("idx_appl_tenant_student", "residential_applications", ["tenant_id", "student_id"])
    op.create_index("idx_appl_tenant_status", "residential_applications", ["tenant_id", "status"])

    # 3. Residents Lifecycle Records
    op.create_table(
        "residential_residents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "allocation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("infrastructure_hostel_allocations.id", ondelete="RESTRICT"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_students.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "bed_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("infrastructure_hostel_beds.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "hostel_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("infrastructure_hostels.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "academic_year_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_academic_years.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(32), nullable=False, server_default="CHECKED_IN"),
        sa.Column("check_in_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "checked_in_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("key_card_issued", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("key_number", sa.String(32), nullable=True),
        sa.Column("facilities_condition_note", sa.Text(), nullable=True),
        sa.Column("inventory_handover", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("expected_departure_date", sa.Date(), nullable=True),
        sa.Column("check_out_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "checked_out_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("checkout_reason", sa.String(64), nullable=True),
        sa.Column("room_condition_on_checkout", sa.Text(), nullable=True),
        sa.Column("key_returned", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("damage_assessment_notes", sa.Text(), nullable=True),
        sa.Column("damage_charges_amount", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column(
            "damage_invoice_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("finance_invoices.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("cleared_by_finance", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_residents_tenant_student", "residential_residents", ["tenant_id", "student_id"])
    op.create_index("idx_residents_tenant_hostel", "residential_residents", ["tenant_id", "hostel_id"])
    op.create_index("idx_residents_tenant_status", "residential_residents", ["tenant_id", "status"])

    # 4. Fee Plans
    op.create_table(
        "residential_fee_plans",
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
            "hostel_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("infrastructure_hostels.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("room_type", sa.String(32), nullable=False, server_default="DOUBLE"),
        sa.Column("billing_cycle", sa.String(32), nullable=False, server_default="SEMESTER"),
        sa.Column("rent_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("mess_amount", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("deposit_amount", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("utility_amount", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("amenities_amount", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("proration_rule", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_fee_plan_tenant_code"),
    )
    op.create_index("idx_fee_plans_tenant_hostel", "residential_fee_plans", ["tenant_id", "hostel_id"])

    # 5. Meal Plans
    op.create_table(
        "residential_meal_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "hostel_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("infrastructure_hostels.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("meal_type", sa.String(32), nullable=False, server_default="VEG"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("monthly_rate", sa.Numeric(12, 2), nullable=False),
        sa.Column("daily_rate", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("serves_breakfast", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("serves_lunch", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("serves_snacks", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("serves_dinner", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_meal_plan_tenant_code"),
    )
    op.create_index("idx_meal_plans_tenant_hostel", "residential_meal_plans", ["tenant_id", "hostel_id"])

    # 6. Meal Enrollments
    op.create_table(
        "residential_meal_enrollments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_students.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "meal_plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("residential_meal_plans.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "resident_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("residential_residents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("dietary_requirements", sa.String(255), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_meal_enroll_tenant_student", "residential_meal_enrollments", ["tenant_id", "student_id"])
    op.create_index("idx_meal_enroll_tenant_plan", "residential_meal_enrollments", ["tenant_id", "meal_plan_id"])

    # 7. Visitors
    op.create_table(
        "residential_visitors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "hostel_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("infrastructure_hostels.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "host_student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_students.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("visitor_name", sa.String(128), nullable=False),
        sa.Column("visitor_phone", sa.String(32), nullable=False),
        sa.Column("visitor_id_proof_type", sa.String(32), nullable=False, server_default="GOVT_ID"),
        sa.Column("visitor_id_proof_number", sa.String(64), nullable=False),
        sa.Column("visitor_relation", sa.String(64), nullable=False, server_default="PARENT"),
        sa.Column("purpose", sa.String(255), nullable=False),
        sa.Column("pass_code", sa.String(32), nullable=False),
        sa.Column("expected_check_in", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expected_check_out", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actual_check_in", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_check_out", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "approved_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(32), nullable=False, server_default="EXPECTED"),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_visitors_tenant_hostel", "residential_visitors", ["tenant_id", "hostel_id"])
    op.create_index("idx_visitors_tenant_student", "residential_visitors", ["tenant_id", "host_student_id"])
    op.create_index("idx_visitors_tenant_status", "residential_visitors", ["tenant_id", "status"])

    # 8. Gate Passes
    op.create_table(
        "residential_gate_passes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "resident_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("residential_residents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_students.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "hostel_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("infrastructure_hostels.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("pass_code", sa.String(32), nullable=False),
        sa.Column("purpose", sa.String(255), nullable=False),
        sa.Column("destination", sa.String(255), nullable=True),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="ISSUED"),
        sa.Column(
            "verified_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_exit_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_entry_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "pass_code", name="uq_gate_pass_tenant_code"),
    )
    op.create_index("idx_gate_passes_tenant_student", "residential_gate_passes", ["tenant_id", "student_id"])
    op.create_index("idx_gate_passes_tenant_status", "residential_gate_passes", ["tenant_id", "status"])

    # 9. Residential Incidents
    op.create_table(
        "residential_incidents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("incident_number", sa.String(32), nullable=False),
        sa.Column(
            "hostel_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("infrastructure_hostels.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("incident_type", sa.String(32), nullable=False, server_default="OTHER"),
        sa.Column("severity", sa.String(32), nullable=False, server_default="MEDIUM"),
        sa.Column("incident_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("location_description", sa.String(255), nullable=False),
        sa.Column(
            "reporter_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("involved_student_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("action_taken", sa.Text(), nullable=True),
        sa.Column("is_disciplinary_referral", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("status", sa.String(32), nullable=False, server_default="REPORTED"),
        sa.Column(
            "assigned_warden_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_incidents_tenant_hostel", "residential_incidents", ["tenant_id", "hostel_id"])
    op.create_index("idx_incidents_tenant_severity", "residential_incidents", ["tenant_id", "severity"])
    op.create_index("idx_incidents_tenant_status", "residential_incidents", ["tenant_id", "status"])

    # 10. Safety Inspections
    op.create_table(
        "residential_safety_inspections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "hostel_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("infrastructure_hostels.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("inspection_date", sa.Date(), nullable=False),
        sa.Column(
            "inspector_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("fire_safety_passed", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("electrical_safety_passed", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("hygiene_passed", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("structural_passed", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("checklist_results", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("critical_findings", sa.Text(), nullable=True),
        sa.Column("action_items", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="COMPLETED"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_inspections_tenant_hostel", "residential_safety_inspections", ["tenant_id", "hostel_id"])
    op.create_index("idx_inspections_tenant_date", "residential_safety_inspections", ["tenant_id", "inspection_date"])

    # 11. Night Attendance
    op.create_table(
        "residential_night_attendances",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "hostel_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("infrastructure_hostels.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "resident_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("residential_residents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("attendance_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="PRESENT"),
        sa.Column(
            "checked_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("remarks", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "attendance_date", "resident_id", name="uq_night_att_resident_date"),
    )
    op.create_index(
        "idx_night_att_tenant_hostel_date",
        "residential_night_attendances",
        ["tenant_id", "hostel_id", "attendance_date"],
    )


def downgrade() -> None:
    op.drop_table("residential_night_attendances")
    op.drop_table("residential_safety_inspections")
    op.drop_table("residential_incidents")
    op.drop_table("residential_gate_passes")
    op.drop_table("residential_visitors")
    op.drop_table("residential_meal_enrollments")
    op.drop_table("residential_meal_plans")
    op.drop_table("residential_fee_plans")
    op.drop_table("residential_residents")
    op.drop_table("residential_applications")
    op.drop_table("residential_application_cycles")
