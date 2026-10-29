"""Enterprise Student Housing, Off-Campus Accommodation, Landlord Partnerships & Residential Compliance Management (Step 66).

Revision ID: 048_enterprise_student_housing_offcampus_accommodation
Revises: 047_enterprise_student_engagement_civic_impact
Create Date: 2026-10-28 22:15:00.000000

Creates domain tables and indexes for:
- housing_providers
- housing_properties
- housing_units
- housing_beds
- housing_requests
- housing_offers
- housing_assignments
- housing_agreements
- housing_checkin_checkout
- housing_inspections
- housing_maintenance_requests
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "048_enterprise_student_housing_offcampus_accommodation"
down_revision = "047_enterprise_student_engagement_civic_impact"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Housing Providers & Landlords
    op.create_table(
        "housing_providers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("slug", sa.String(128), nullable=False),
        sa.Column("provider_type", sa.String(32), nullable=False, server_default="PRIVATE_LANDLORD"),
        sa.Column("registration_number", sa.String(64), nullable=True),
        sa.Column("contact_name", sa.String(128), nullable=False),
        sa.Column("contact_email", sa.String(128), nullable=False),
        sa.Column("contact_phone", sa.String(32), nullable=False),
        sa.Column("emergency_phone", sa.String(32), nullable=True),
        sa.Column("tax_id", sa.String(64), nullable=True),
        sa.Column("address", sa.String(255), nullable=True),
        sa.Column("city", sa.String(64), nullable=False, server_default="Chennai"),
        sa.Column("state", sa.String(64), nullable=False, server_default="Tamil Nadu"),
        sa.Column("verification_status", sa.String(32), nullable=False, server_default="VERIFIED"),
        sa.Column("verification_notes", sa.Text(), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("mou_reference", sa.String(64), nullable=True),
        sa.Column("mou_valid_from", sa.Date(), nullable=True),
        sa.Column("mou_valid_to", sa.Date(), nullable=True),
        sa.Column("rating", sa.Numeric(3, 2), nullable=False, server_default="4.50"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("total_properties_managed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_beds_provided", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "slug", name="uq_housing_provider_slug"),
    )
    op.create_index("idx_housing_provider_tenant_status", "housing_providers", ["tenant_id", "verification_status"])

    # 2. Housing Properties
    op.create_table(
        "housing_properties",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("provider_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("housing_providers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("hostel_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("infrastructure_hostels.id", ondelete="SET NULL"), nullable=True),
        sa.Column("campus_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_campuses.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("slug", sa.String(128), nullable=False),
        sa.Column("property_type", sa.String(32), nullable=False, server_default="OFF_CAMPUS_HOSTEL"),
        sa.Column("lifecycle_status", sa.String(32), nullable=False, server_default="APPROVED"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("address", sa.String(255), nullable=False),
        sa.Column("city", sa.String(64), nullable=False, server_default="Chennai"),
        sa.Column("state", sa.String(64), nullable=False, server_default="Tamil Nadu"),
        sa.Column("postal_code", sa.String(16), nullable=True),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("distance_to_campus_km", sa.Numeric(5, 2), nullable=False, server_default="1.50"),
        sa.Column("total_rooms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_bed_capacity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("occupied_beds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("available_beds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("monthly_rent_min", sa.Numeric(10, 2), nullable=False, server_default="6000.00"),
        sa.Column("monthly_rent_max", sa.Numeric(10, 2), nullable=False, server_default="12000.00"),
        sa.Column("security_deposit_amount", sa.Numeric(10, 2), nullable=False, server_default="15000.00"),
        sa.Column("currency", sa.String(8), nullable=False, server_default="INR"),
        sa.Column("amenities", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("utilities_included", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("accessibility_features", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("safety_features", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("house_rules", sa.Text(), nullable=True),
        sa.Column("approval_valid_until", sa.Date(), nullable=True),
        sa.Column("approved_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("manager_name", sa.String(128), nullable=True),
        sa.Column("manager_phone", sa.String(32), nullable=True),
        sa.Column("manager_email", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "code", name="uq_housing_property_code"),
    )
    op.create_index("idx_housing_property_tenant_status", "housing_properties", ["tenant_id", "lifecycle_status"])
    op.create_index("idx_housing_property_provider", "housing_properties", ["tenant_id", "provider_id"])
    op.create_index("idx_housing_property_campus", "housing_properties", ["tenant_id", "campus_id"])

    # 3. Housing Units (Rooms / Apartments)
    op.create_table(
        "housing_units",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("property_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("housing_properties.id", ondelete="CASCADE"), nullable=False),
        sa.Column("hostel_room_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("infrastructure_hostel_rooms.id", ondelete="SET NULL"), nullable=True),
        sa.Column("unit_number", sa.String(32), nullable=False),
        sa.Column("unit_type", sa.String(32), nullable=False, server_default="DOUBLE_OCCUPANCY"),
        sa.Column("floor_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("bed_capacity", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("occupied_beds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rent_per_bed", sa.Numeric(10, 2), nullable=False, server_default="8000.00"),
        sa.Column("security_deposit_per_bed", sa.Numeric(10, 2), nullable=False, server_default="15000.00"),
        sa.Column("is_furnished", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("has_attached_bath", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_accessible", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_available", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("status", sa.String(32), nullable=False, server_default="AVAILABLE"),
        sa.Column("maintenance_reason", sa.String(255), nullable=True),
        sa.Column("closed_until", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("property_id", "unit_number", name="uq_unit_property_number"),
    )
    op.create_index("idx_housing_unit_tenant_property", "housing_units", ["tenant_id", "property_id"])
    op.create_index("idx_housing_unit_status", "housing_units", ["tenant_id", "status"])

    # 4. Housing Beds
    op.create_table(
        "housing_beds",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("housing_units.id", ondelete="CASCADE"), nullable=False),
        sa.Column("hostel_bed_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("infrastructure_hostel_beds.id", ondelete="SET NULL"), nullable=True),
        sa.Column("bed_code", sa.String(32), nullable=False),
        sa.Column("is_available", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("status", sa.String(32), nullable=False, server_default="AVAILABLE"),
        sa.Column("blocked_reason", sa.String(255), nullable=True),
        sa.Column("blocked_until", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("unit_id", "bed_code", name="uq_unit_bed_code"),
    )
    op.create_index("idx_housing_bed_tenant_unit", "housing_beds", ["tenant_id", "unit_id"])
    op.create_index("idx_housing_bed_status", "housing_beds", ["tenant_id", "status"])

    # 5. Housing Requests
    op.create_table(
        "housing_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("request_number", sa.String(32), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_students.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("preferred_property_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("housing_properties.id", ondelete="SET NULL"), nullable=True),
        sa.Column("preferred_unit_type", sa.String(32), nullable=False, server_default="DOUBLE_OCCUPANCY"),
        sa.Column("academic_year_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_academic_years.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("academic_term", sa.String(32), nullable=False, server_default="Academic Year 2026-27"),
        sa.Column("requested_move_in_date", sa.Date(), nullable=False),
        sa.Column("requested_move_out_date", sa.Date(), nullable=False),
        sa.Column("budget_min", sa.Numeric(10, 2), nullable=True),
        sa.Column("budget_max", sa.Numeric(10, 2), nullable=True),
        sa.Column("accessibility_required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("disability_accommodation_notes", sa.Text(), nullable=True),
        sa.Column("dietary_preference", sa.String(64), nullable=True),
        sa.Column("lifestyle_preferences", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("special_requests", sa.Text(), nullable=True),
        sa.Column("supporting_document_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("status", sa.String(32), nullable=False, server_default="SUBMITTED"),
        sa.Column("waitlist_position", sa.Integer(), nullable=True),
        sa.Column("priority_score", sa.Numeric(6, 2), nullable=False, server_default="0.00"),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("reviewed_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "request_number", name="uq_housing_request_number"),
    )
    op.create_index("idx_housing_request_student", "housing_requests", ["tenant_id", "student_id"])
    op.create_index("idx_housing_request_status", "housing_requests", ["tenant_id", "status"])
    op.create_index("idx_housing_request_waitlist", "housing_requests", ["tenant_id", "waitlist_position"])

    # 6. Housing Offers
    op.create_table(
        "housing_offers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("housing_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_students.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("property_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("housing_properties.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("housing_units.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("bed_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("housing_beds.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("offered_rent_monthly", sa.Numeric(10, 2), nullable=False),
        sa.Column("offered_deposit", sa.Numeric(10, 2), nullable=False),
        sa.Column("occupancy_start_date", sa.Date(), nullable=False),
        sa.Column("occupancy_end_date", sa.Date(), nullable=False),
        sa.Column("offer_valid_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="OFFERED"),
        sa.Column("decline_reason", sa.String(255), nullable=True),
        sa.Column("response_notes", sa.Text(), nullable=True),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_housing_offer_tenant_req", "housing_offers", ["tenant_id", "request_id"])
    op.create_index("idx_housing_offer_tenant_student", "housing_offers", ["tenant_id", "student_id"])
    op.create_index("idx_housing_offer_status", "housing_offers", ["tenant_id", "status"])

    # 7. Housing Assignments
    op.create_table(
        "housing_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("assignment_number", sa.String(32), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_students.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("property_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("housing_properties.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("housing_units.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("bed_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("housing_beds.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("housing_requests.id", ondelete="SET NULL"), nullable=True),
        sa.Column("offer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("housing_offers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("hostel_allocation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("infrastructure_hostel_allocations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("monthly_rent", sa.Numeric(10, 2), nullable=False),
        sa.Column("security_deposit", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="ASSIGNED"),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancellation_reason", sa.String(255), nullable=True),
        sa.Column("transfer_to_unit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("housing_units.id", ondelete="SET NULL"), nullable=True),
        sa.Column("transfer_reason", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "assignment_number", name="uq_housing_assignment_num"),
    )
    op.create_index("idx_housing_asgn_student", "housing_assignments", ["tenant_id", "student_id"])
    op.create_index("idx_housing_asgn_bed", "housing_assignments", ["tenant_id", "bed_id"])
    op.create_index("idx_housing_asgn_status", "housing_assignments", ["tenant_id", "status"])

    # 8. Housing Agreements & Leases
    op.create_table(
        "housing_agreements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("assignment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("housing_assignments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("property_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("housing_properties.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("provider_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("housing_providers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_students.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("agreement_number", sa.String(32), nullable=False),
        sa.Column("agreement_title", sa.String(128), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_to", sa.Date(), nullable=False),
        sa.Column("rent_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("deposit_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("payment_frequency", sa.String(32), nullable=False, server_default="MONTHLY"),
        sa.Column("finance_invoice_reference", sa.String(64), nullable=True),
        sa.Column("deposit_invoice_reference", sa.String(64), nullable=True),
        sa.Column("deposit_refund_status", sa.String(32), nullable=False, server_default="HELD"),
        sa.Column("terms_and_conditions_acknowledged", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("student_signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("provider_signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("institutional_witness_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"),
        sa.Column("document_file_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("assignment_id", name="uq_housing_agmt_asgn"),
    )
    op.create_index("idx_housing_agmt_tenant_student", "housing_agreements", ["tenant_id", "student_id"])
    op.create_index("idx_housing_agmt_status", "housing_agreements", ["tenant_id", "status"])

    # 9. Housing Check-In and Check-Out Records
    op.create_table(
        "housing_checkin_checkout",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("assignment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("housing_assignments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_students.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("record_type", sa.String(16), nullable=False),
        sa.Column("scheduled_date", sa.Date(), nullable=False),
        sa.Column("actual_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("inspector_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("key_card_issued_or_returned", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("key_identifier", sa.String(64), nullable=True),
        sa.Column("room_condition_rating", sa.String(32), nullable=False, server_default="GOOD"),
        sa.Column("checklist_items", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("damage_assessed_amount", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("damage_description", sa.Text(), nullable=True),
        sa.Column("damage_billed_invoice_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("finance_invoices.id", ondelete="SET NULL"), nullable=True),
        sa.Column("photos_evidence_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("student_signature_confirmed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="SCHEDULED"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_housing_check_assignment", "housing_checkin_checkout", ["tenant_id", "assignment_id"])
    op.create_index("idx_housing_check_student", "housing_checkin_checkout", ["tenant_id", "student_id"])
    op.create_index("idx_housing_check_type", "housing_checkin_checkout", ["tenant_id", "record_type"])

    # 10. Property Inspections
    op.create_table(
        "housing_inspections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("property_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("housing_properties.id", ondelete="CASCADE"), nullable=False),
        sa.Column("inspection_code", sa.String(32), nullable=False),
        sa.Column("inspector_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("inspection_date", sa.Date(), nullable=False),
        sa.Column("inspection_type", sa.String(32), nullable=False, server_default="SAFETY_FIRE"),
        sa.Column("overall_outcome", sa.String(32), nullable=False, server_default="PASSED"),
        sa.Column("safety_score", sa.Numeric(5, 2), nullable=False, server_default="100.00"),
        sa.Column("checklist_results", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("critical_issues_found", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("availability_suspended", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("corrective_actions_required", sa.Text(), nullable=True),
        sa.Column("corrective_action_deadline", sa.Date(), nullable=True),
        sa.Column("reinspection_due_date", sa.Date(), nullable=True),
        sa.Column("compliance_status", sa.String(32), nullable=False, server_default="COMPLIANT"),
        sa.Column("report_document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_housing_insp_tenant_property", "housing_inspections", ["tenant_id", "property_id"])
    op.create_index("idx_housing_insp_outcome", "housing_inspections", ["tenant_id", "overall_outcome"])

    # 11. Housing Maintenance Requests
    op.create_table(
        "housing_maintenance_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("property_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("housing_properties.id", ondelete="CASCADE"), nullable=False),
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("housing_units.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reported_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("reported_by_student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("people_students.id", ondelete="SET NULL"), nullable=True),
        sa.Column("category", sa.String(32), nullable=False, server_default="PLUMBING"),
        sa.Column("priority", sa.String(32), nullable=False, server_default="MEDIUM"),
        sa.Column("title", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("photo_urls", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("status", sa.String(32), nullable=False, server_default="REPORTED"),
        sa.Column("assigned_technician_name", sa.String(128), nullable=True),
        sa.Column("assigned_vendor_name", sa.String(128), nullable=True),
        sa.Column("linked_work_order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("asset_maintenance_work_orders.id", ondelete="SET NULL"), nullable=True),
        sa.Column("scheduled_visit_date", sa.Date(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completion_notes", sa.Text(), nullable=True),
        sa.Column("tenant_satisfaction_rating", sa.Integer(), nullable=True),
        sa.Column("tenant_feedback", sa.Text(), nullable=True),
        sa.Column("cost_charged_to", sa.String(32), nullable=False, server_default="LANDLORD"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_housing_maint_tenant_property", "housing_maintenance_requests", ["tenant_id", "property_id"])
    op.create_index("idx_housing_maint_status", "housing_maintenance_requests", ["tenant_id", "status"])
    op.create_index("idx_housing_maint_priority", "housing_maintenance_requests", ["tenant_id", "priority"])


def downgrade() -> None:
    op.drop_table("housing_maintenance_requests")
    op.drop_table("housing_inspections")
    op.drop_table("housing_checkin_checkout")
    op.drop_table("housing_agreements")
    op.drop_table("housing_assignments")
    op.drop_table("housing_offers")
    op.drop_table("housing_requests")
    op.drop_table("housing_beds")
    op.drop_table("housing_units")
    op.drop_table("housing_properties")
    op.drop_table("housing_providers")
