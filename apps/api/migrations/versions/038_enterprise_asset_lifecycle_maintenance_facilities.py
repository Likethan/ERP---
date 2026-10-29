"""Enterprise Asset Lifecycle, Maintenance, Facilities & Equipment Management (Step 53).

Revision ID: 038_enterprise_asset_lifecycle_maintenance_facilities
Revises: 037_enterprise_payroll_compensation_compliance
Create Date: 2026-10-21 12:00:00.000000

Creates normalized tables for:
- asset_categories: Classification taxonomy and management policy configuration
- asset_registry: Centralized enterprise institutional asset records
- asset_lifecycle_events: Immutable audit trail for asset state transitions
- asset_assignments: Authoritative custody allocation and loan management
- asset_transfers: Controlled multi-stage cross-department/campus transfers
- asset_maintenance_plans: Recurring preventive maintenance plans and schedules
- asset_maintenance_work_orders: Preventive and corrective maintenance work orders
- asset_wo_part_consumptions: Spare parts reserved and consumed from inventory
- asset_inspection_templates: Safety and compliance inspection checklist templates
- asset_inspection_records: Recorded outcome of safety and compliance inspections
- asset_warranties_contracts: Warranties, AMC, CMC, and SLA service agreements
- asset_warranty_claims: Formal warranty and service claims tracking
- asset_depreciation_schedules: Period-based fixed-asset depreciation and finance references
- asset_audit_campaigns: Physical verification and stocktaking audit campaigns
- asset_audit_items: Scanned tag verification records and discrepancy tracking
- asset_retirement_requests: Technical assessment, decommissioning, and certified disposal
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "038_enterprise_asset_lifecycle_maintenance_facilities"
down_revision = "037_enterprise_payroll_compensation_compliance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Asset Categories
    op.create_table(
        "asset_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category_type", sa.String(32), nullable=False, server_default="OTHER"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("requires_serial_number", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("requires_custodian_acknowledgement", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("default_inspection_interval_days", sa.Integer(), nullable=True),
        sa.Column("default_maintenance_interval_days", sa.Integer(), nullable=True),
        sa.Column("default_criticality", sa.String(32), nullable=False, server_default="MEDIUM"),
        sa.Column("default_depreciation_method", sa.String(32), nullable=False, server_default="STRAIGHT_LINE"),
        sa.Column("default_useful_life_months", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("default_salvage_value_percent", sa.Numeric(5, 2), nullable=False, server_default="5.00"),
        sa.Column("policy_schema", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("assignment_restrictions", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_asset_category_tenant_code"),
    )
    op.create_index("idx_asset_category_tenant_type", "asset_categories", ["tenant_id", "category_type"])
    op.create_index("idx_asset_category_tenant_active", "asset_categories", ["tenant_id", "is_active"])

    # 2. Asset Registry
    op.create_table(
        "asset_registry",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("asset_tag", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "category_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("asset_categories.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("asset_type", sa.String(64), nullable=False, server_default="GENERAL"),
        sa.Column("make", sa.String(128), nullable=True),
        sa.Column("model", sa.String(128), nullable=True),
        sa.Column("serial_number", sa.String(128), nullable=True),
        sa.Column("manufacturer", sa.String(128), nullable=True),
        sa.Column("barcode_data", sa.String(128), nullable=True),
        sa.Column("acquisition_date", sa.Date(), nullable=False),
        sa.Column("acquisition_cost", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("currency", sa.String(16), nullable=False, server_default="INR"),
        sa.Column("source", sa.String(32), nullable=False, server_default="PURCHASE"),
        sa.Column(
            "supplier_vendor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_vendors.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "purchase_order_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_purchase_orders.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "purchase_order_line_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_purchase_order_lines.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "goods_receipt_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_goods_receipts.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("invoice_reference", sa.String(128), nullable=True),
        sa.Column(
            "campus_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_campuses.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("building", sa.String(128), nullable=True),
        sa.Column("floor", sa.String(32), nullable=True),
        sa.Column("room_number", sa.String(64), nullable=True),
        sa.Column("location_description", sa.Text(), nullable=True),
        sa.Column(
            "department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "current_custodian_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("condition", sa.String(32), nullable=False, server_default="GOOD"),
        sa.Column("operational_status", sa.String(32), nullable=False, server_default="OPERATIONAL"),
        sa.Column("criticality", sa.String(32), nullable=False, server_default="MEDIUM"),
        sa.Column("usage_classification", sa.String(32), nullable=False, server_default="ACADEMIC"),
        sa.Column("lifecycle_state", sa.String(32), nullable=False, server_default="COMMISSIONED"),
        sa.Column("is_restricted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("restriction_reason", sa.Text(), nullable=True),
        sa.Column("warranty_start_date", sa.Date(), nullable=True),
        sa.Column("warranty_end_date", sa.Date(), nullable=True),
        sa.Column("last_maintained_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_maintenance_due", sa.Date(), nullable=True),
        sa.Column("last_inspected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_inspection_due", sa.Date(), nullable=True),
        sa.Column("depreciation_method", sa.String(32), nullable=False, server_default="STRAIGHT_LINE"),
        sa.Column("useful_life_months", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("salvage_value", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("accumulated_depreciation", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("current_book_value", sa.Numeric(14, 2), nullable=False, server_default="0.00"),
        sa.Column("last_depreciated_date", sa.Date(), nullable=True),
        sa.Column("image_keys", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("document_references", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("custom_attributes", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "asset_tag", name="uq_asset_registry_tenant_tag"),
    )
    op.create_index("idx_asset_registry_tenant_cat", "asset_registry", ["tenant_id", "category_id"])
    op.create_index("idx_asset_registry_tenant_state", "asset_registry", ["tenant_id", "lifecycle_state"])
    op.create_index("idx_asset_registry_tenant_campus", "asset_registry", ["tenant_id", "campus_id"])
    op.create_index("idx_asset_registry_tenant_dept", "asset_registry", ["tenant_id", "department_id"])
    op.create_index("idx_asset_registry_tenant_custodian", "asset_registry", ["tenant_id", "current_custodian_id"])
    op.create_index("idx_asset_registry_serial", "asset_registry", ["tenant_id", "serial_number"])

    # 3. Asset Lifecycle Events
    op.create_table(
        "asset_lifecycle_events",
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
            sa.ForeignKey("asset_registry.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("from_state", sa.String(32), nullable=False),
        sa.Column("to_state", sa.String(32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("supporting_documents", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column(
            "actor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("performed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_asset_lifecycle_tenant_asset", "asset_lifecycle_events", ["tenant_id", "asset_id"])
    op.create_index("idx_asset_lifecycle_perf_at", "asset_lifecycle_events", ["tenant_id", "performed_at"])

    # 4. Asset Assignments
    op.create_table(
        "asset_assignments",
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
            sa.ForeignKey("asset_registry.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("assignment_type", sa.String(32), nullable=False, server_default="EMPLOYEE"),
        sa.Column(
            "custodian_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_departments.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "campus_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_campuses.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("location_details", sa.String(255), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("expected_return_date", sa.Date(), nullable=True),
        sa.Column("actual_return_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"),
        sa.Column("acknowledgement_required", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledgement_notes", sa.Text(), nullable=True),
        sa.Column(
            "assigned_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("condition_at_assignment", sa.String(32), nullable=False, server_default="GOOD"),
        sa.Column("condition_at_return", sa.String(32), nullable=True),
        sa.Column("handover_notes", sa.Text(), nullable=True),
        sa.Column("supporting_evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_asset_assign_tenant_asset", "asset_assignments", ["tenant_id", "asset_id"])
    op.create_index("idx_asset_assign_custodian", "asset_assignments", ["tenant_id", "custodian_id"])
    op.create_index("idx_asset_assign_status", "asset_assignments", ["tenant_id", "status"])

    # 5. Asset Transfers
    op.create_table(
        "asset_transfers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("transfer_number", sa.String(64), nullable=False),
        sa.Column(
            "asset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("asset_registry.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "from_campus_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_campuses.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "from_department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_departments.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "from_custodian_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "to_campus_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_campuses.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "to_department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_departments.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "to_custodian_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("transfer_reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="REQUESTED"),
        sa.Column(
            "initiated_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "approved_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("in_transit_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "received_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("dispatch_notes", sa.Text(), nullable=True),
        sa.Column("acceptance_notes", sa.Text(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "transfer_number", name="uq_asset_transfer_number"),
    )
    op.create_index("idx_asset_transfer_tenant_asset", "asset_transfers", ["tenant_id", "asset_id"])
    op.create_index("idx_asset_transfer_status", "asset_transfers", ["tenant_id", "status"])

    # 6. Maintenance Plans
    op.create_table(
        "asset_maintenance_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("plan_code", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "category_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("asset_categories.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "asset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("asset_registry.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "campus_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_campuses.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("interval_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("estimated_duration_hours", sa.Numeric(6, 2), nullable=False, server_default="2.00"),
        sa.Column("checklist", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column(
            "assigned_technician_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "preferred_vendor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_vendors.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "plan_code", name="uq_maintenance_plan_code"),
    )
    op.create_index("idx_maint_plan_tenant_cat", "asset_maintenance_plans", ["tenant_id", "category_id"])
    op.create_index("idx_maint_plan_tenant_asset", "asset_maintenance_plans", ["tenant_id", "asset_id"])

    # 7. Maintenance Work Orders
    op.create_table(
        "asset_maintenance_work_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("work_order_number", sa.String(64), nullable=False),
        sa.Column(
            "asset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("asset_registry.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("asset_maintenance_plans.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("order_type", sa.String(32), nullable=False, server_default="CORRECTIVE"),
        sa.Column("priority", sa.String(32), nullable=False, server_default="MEDIUM"),
        sa.Column("severity", sa.String(32), nullable=False, server_default="MODERATE"),
        sa.Column("operational_impact", sa.String(32), nullable=False, server_default="NO_IMPACT"),
        sa.Column("status", sa.String(32), nullable=False, server_default="REPORTED"),
        sa.Column(
            "reported_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("reported_symptoms", sa.Text(), nullable=False),
        sa.Column("scheduled_start_date", sa.Date(), nullable=True),
        sa.Column("scheduled_end_date", sa.Date(), nullable=True),
        sa.Column("actual_start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "assigned_technician_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "vendor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_vendors.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("diagnosis", sa.Text(), nullable=True),
        sa.Column("repair_actions", sa.Text(), nullable=True),
        sa.Column("downtime_hours", sa.Numeric(8, 2), nullable=False, server_default="0.00"),
        sa.Column("labor_hours", sa.Numeric(8, 2), nullable=False, server_default="0.00"),
        sa.Column("labor_cost", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("parts_cost", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("service_charges", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("total_cost", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("estimated_cost", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("verification_required", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "verified_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verification_notes", sa.Text(), nullable=True),
        sa.Column("attachments", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("checklist_results", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("reopen_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "work_order_number", name="uq_maintenance_wo_number"),
    )
    op.create_index("idx_maint_wo_tenant_asset", "asset_maintenance_work_orders", ["tenant_id", "asset_id"])
    op.create_index("idx_maint_wo_tenant_status", "asset_maintenance_work_orders", ["tenant_id", "status"])
    op.create_index("idx_maint_wo_tenant_priority", "asset_maintenance_work_orders", ["tenant_id", "priority"])

    # 8. Work Order Part Consumptions
    op.create_table(
        "asset_wo_part_consumptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "work_order_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("asset_maintenance_work_orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "inventory_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_inventory_items.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "inventory_location_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_inventory_locations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("quantity_reserved", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("quantity_consumed", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("quantity_returned", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("unit_cost", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("total_cost", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("status", sa.String(32), nullable=False, server_default="RESERVED"),
        sa.Column(
            "stock_movement_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_stock_movements.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_asset_wo_parts_wo", "asset_wo_part_consumptions", ["tenant_id", "work_order_id"])
    op.create_index("idx_asset_wo_parts_item", "asset_wo_part_consumptions", ["tenant_id", "inventory_item_id"])

    # 9. Inspection Templates
    op.create_table(
        "asset_inspection_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "category_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("asset_categories.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("frequency_days", sa.Integer(), nullable=False, server_default="90"),
        sa.Column("checklist_items", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("is_mandatory", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_inspection_template_code"),
    )
    op.create_index("idx_insp_template_tenant_cat", "asset_inspection_templates", ["tenant_id", "category_id"])

    # 10. Inspection Records
    op.create_table(
        "asset_inspection_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("inspection_number", sa.String(64), nullable=False),
        sa.Column(
            "asset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("asset_registry.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("asset_inspection_templates.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "inspector_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("inspection_date", sa.Date(), nullable=False),
        sa.Column("overall_outcome", sa.String(32), nullable=False, server_default="PASS"),
        sa.Column("safety_risk_detected", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("action_taken", sa.String(32), nullable=False, server_default="NONE"),
        sa.Column("checklist_results", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("findings_summary", sa.Text(), nullable=True),
        sa.Column("corrective_action_required", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("corrective_action_due_date", sa.Date(), nullable=True),
        sa.Column(
            "corrective_action_owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("corrective_action_status", sa.String(32), nullable=False, server_default="RESOLVED"),
        sa.Column("evidence_attachments", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "inspection_number", name="uq_inspection_record_number"),
    )
    op.create_index("idx_asset_insp_tenant_asset", "asset_inspection_records", ["tenant_id", "asset_id"])
    op.create_index("idx_asset_insp_tenant_date", "asset_inspection_records", ["tenant_id", "inspection_date"])
    op.create_index("idx_asset_insp_outcome", "asset_inspection_records", ["tenant_id", "overall_outcome"])

    # 11. Asset Warranties & Service Contracts
    op.create_table(
        "asset_warranties_contracts",
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
            sa.ForeignKey("asset_registry.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "vendor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_vendors.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("contract_type", sa.String(32), nullable=False, server_default="MANUFACTURER_WARRANTY"),
        sa.Column("contract_number", sa.String(128), nullable=False),
        sa.Column("provider_name", sa.String(255), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("coverage_terms", sa.Text(), nullable=True),
        sa.Column("exclusions", sa.Text(), nullable=True),
        sa.Column("sla_response_hours", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("cost", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"),
        sa.Column("renewal_reminder_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("documents", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_asset_contract_tenant_asset", "asset_warranties_contracts", ["tenant_id", "asset_id"])
    op.create_index("idx_asset_contract_vendor", "asset_warranties_contracts", ["tenant_id", "vendor_id"])
    op.create_index("idx_asset_contract_status", "asset_warranties_contracts", ["tenant_id", "status"])
    op.create_index("idx_asset_contract_expiry", "asset_warranties_contracts", ["tenant_id", "end_date"])

    # 12. Warranty Claims
    op.create_table(
        "asset_warranty_claims",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "claim_number",
            sa.String(64),
            nullable=False,
        ),
        sa.Column(
            "contract_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("asset_warranties_contracts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "asset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("asset_registry.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("incident_date", sa.Date(), nullable=False),
        sa.Column("issue_description", sa.Text(), nullable=False),
        sa.Column("vendor_ticket_reference", sa.String(128), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="FILED"),
        sa.Column("resolution_summary", sa.Text(), nullable=True),
        sa.Column("reimbursement_amount", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("supporting_evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "claim_number", name="uq_warranty_claim_number"),
    )
    op.create_index("idx_warranty_claim_contract", "asset_warranty_claims", ["tenant_id", "contract_id"])
    op.create_index("idx_warranty_claim_asset", "asset_warranty_claims", ["tenant_id", "asset_id"])

    # 13. Asset Depreciation Schedules
    op.create_table(
        "asset_depreciation_schedules",
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
            sa.ForeignKey("asset_registry.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("fiscal_year", sa.String(16), nullable=False),
        sa.Column("period_name", sa.String(32), nullable=False),
        sa.Column("period_start_date", sa.Date(), nullable=False),
        sa.Column("period_end_date", sa.Date(), nullable=False),
        sa.Column("opening_book_value", sa.Numeric(14, 2), nullable=False),
        sa.Column("depreciation_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("closing_book_value", sa.Numeric(14, 2), nullable=False),
        sa.Column("is_posted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "posted_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("journal_entry_reference", sa.String(128), nullable=True),
        sa.Column("reversal_reference", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "asset_id", "fiscal_year", "period_name", name="uq_asset_depr_period"),
    )
    op.create_index("idx_asset_depr_tenant_asset", "asset_depreciation_schedules", ["tenant_id", "asset_id"])
    op.create_index("idx_asset_depr_fiscal", "asset_depreciation_schedules", ["tenant_id", "fiscal_year", "period_name"])

    # 14. Asset Audit Campaigns
    op.create_table(
        "asset_audit_campaigns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("campaign_code", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "campus_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_campuses.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("building", sa.String(128), nullable=True),
        sa.Column(
            "department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "category_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("asset_categories.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="PLANNED"),
        sa.Column(
            "lead_auditor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("total_assets_scoped", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_verified", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_discrepancies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "campaign_code", name="uq_asset_audit_campaign_code"),
    )
    op.create_index("idx_asset_audit_status", "asset_audit_campaigns", ["tenant_id", "status"])

    # 15. Asset Audit Items
    op.create_table(
        "asset_audit_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "campaign_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("asset_audit_campaigns.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "asset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("asset_registry.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("scanned_tag", sa.String(64), nullable=False),
        sa.Column("verification_status", sa.String(32), nullable=False, server_default="VERIFIED_MATCH"),
        sa.Column("expected_campus_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("actual_campus_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("expected_building", sa.String(128), nullable=True),
        sa.Column("actual_building", sa.String(128), nullable=True),
        sa.Column("expected_room", sa.String(64), nullable=True),
        sa.Column("actual_room", sa.String(64), nullable=True),
        sa.Column("expected_custodian_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("actual_custodian_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("expected_condition", sa.String(32), nullable=True),
        sa.Column("actual_condition", sa.String(32), nullable=True),
        sa.Column(
            "verified_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reconciliation_status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("reconciliation_notes", sa.Text(), nullable=True),
        sa.Column("evidence_attachments", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_audit_items_campaign", "asset_audit_items", ["tenant_id", "campaign_id"])
    op.create_index("idx_audit_items_asset", "asset_audit_items", ["tenant_id", "asset_id"])

    # 16. Asset Retirement Requests
    op.create_table(
        "asset_retirement_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("request_number", sa.String(64), nullable=False),
        sa.Column(
            "asset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("asset_registry.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "requested_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("retirement_reason", sa.String(32), nullable=False, server_default="BEYOND_ECONOMIC_REPAIR"),
        sa.Column("disposal_method", sa.String(32), nullable=False, server_default="RECYCLING"),
        sa.Column("technical_assessment_notes", sa.Text(), nullable=False),
        sa.Column("estimated_residual_value", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("actual_realized_value", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT"),
        sa.Column(
            "approved_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("data_wiped", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("data_wipe_certificate_url", sa.String(255), nullable=True),
        sa.Column("disposal_certificate_url", sa.String(255), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reconciliation_checks_passed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "request_number", name="uq_asset_retirement_req_number"),
    )
    op.create_index("idx_asset_retire_tenant_asset", "asset_retirement_requests", ["tenant_id", "asset_id"])
    op.create_index("idx_asset_retire_status", "asset_retirement_requests", ["tenant_id", "status"])


def downgrade() -> None:
    op.drop_table("asset_retirement_requests")
    op.drop_table("asset_audit_items")
    op.drop_table("asset_audit_campaigns")
    op.drop_table("asset_depreciation_schedules")
    op.drop_table("asset_warranty_claims")
    op.drop_table("asset_warranties_contracts")
    op.drop_table("asset_inspection_records")
    op.drop_table("asset_inspection_templates")
    op.drop_table("asset_wo_part_consumptions")
    op.drop_table("asset_maintenance_work_orders")
    op.drop_table("asset_maintenance_plans")
    op.drop_table("asset_transfers")
    op.drop_table("asset_assignments")
    op.drop_table("asset_lifecycle_events")
    op.drop_table("asset_registry")
    op.drop_table("asset_categories")
