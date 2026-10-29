"""Enterprise Procurement, Vendor Management, Purchase Orders & Inventory Control (Step 50).

Revision ID: 035_enterprise_procurement_vendor_inventory
Revises: 034_enterprise_timetable_resource_scheduling
Create Date: 2026-10-19 22:30:00.000000

Creates normalized tables for:
- procurement_vendors: Vendor organizations, categories, classifications, compliance verifications, and ratings
- procurement_vendor_contacts: Authorized vendor representatives and points of contact
- procurement_vendor_reviews: Vendor performance scorecards and evaluations
- procurement_purchase_requisitions: Departmental purchase requisitions and approvals
- procurement_requisition_lines: Itemized requisition line items
- procurement_quotation_requests: Requests for Quotation (RFQ)
- procurement_vendor_quotations: Commercial quotations submitted by vendors
- procurement_quotation_evaluations: Comparative evaluation scores and award decisions
- procurement_purchase_orders: Binding institutional purchase orders
- procurement_purchase_order_lines: Itemized order lines with quantities and taxes
- procurement_po_amendments: Versioned order amendments and revision approvals
- procurement_goods_receipts: Goods Receipt Notes (GRN) and inspection tracking
- procurement_goods_receipt_lines: Received, accepted, and rejected delivery lines
- procurement_inventory_locations: Physical stockrooms, central stores, and depots
- procurement_inventory_items: Item catalogue, units of measure, and reorder levels
- procurement_stock_balances: Location-specific stock quantities (on-hand, reserved, available, in-transit)
- procurement_stock_movements: Immutable transactional stock movement and adjustment ledger
- procurement_internal_stock_requests: Departmental stock issue requests
- procurement_internal_stock_request_lines: Item lines requested for internal issue
- procurement_supplier_invoice_matches: Three-way match reconciliation records (PO vs GRN vs Invoice)
- procurement_vendor_returns: Return to Vendor (RTV) records for replacements or credit notes
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "035_enterprise_procurement_vendor_inventory"
down_revision = "034_enterprise_timetable_resource_scheduling"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Procurement Vendors
    op.create_table(
        "procurement_vendors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("legal_name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(64), nullable=False, server_default="GOODS"),
        sa.Column("classification", sa.String(64), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("tax_identifier", sa.String(64), nullable=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(32), nullable=False),
        sa.Column("website", sa.String(255), nullable=True),
        sa.Column("address_line1", sa.String(255), nullable=False),
        sa.Column("address_line2", sa.String(255), nullable=True),
        sa.Column("city", sa.String(128), nullable=False),
        sa.Column("state", sa.String(128), nullable=False),
        sa.Column("postal_code", sa.String(32), nullable=False),
        sa.Column("country", sa.String(64), nullable=False, server_default="India"),
        sa.Column("payment_terms_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("rating_score", sa.Numeric(3, 2), nullable=False, server_default="5.00"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "verified_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("documents_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("bank_details_masked", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_procurement_vendor_code"),
    )
    op.create_index("idx_procurement_vendor_category", "procurement_vendors", ["tenant_id", "category"])
    op.create_index("idx_procurement_vendor_status", "procurement_vendors", ["tenant_id", "status"])

    # 2. Vendor Contacts
    op.create_table(
        "procurement_vendor_contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "vendor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_vendors.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("designation", sa.String(128), nullable=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(32), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("idx_procurement_vendor_contacts_vendor", "procurement_vendor_contacts", ["tenant_id", "vendor_id"])

    # 3. Vendor Performance Reviews
    op.create_table(
        "procurement_vendor_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "vendor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_vendors.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("review_date", sa.Date(), nullable=False),
        sa.Column(
            "reviewer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("delivery_score", sa.Integer(), nullable=False),
        sa.Column("quality_score", sa.Integer(), nullable=False),
        sa.Column("pricing_score", sa.Integer(), nullable=False),
        sa.Column("overall_score", sa.Numeric(3, 2), nullable=False),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("recommendation", sa.String(64), nullable=False, server_default="CONTINUE"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("idx_procurement_vendor_reviews_vendor", "procurement_vendor_reviews", ["tenant_id", "vendor_id"])

    # 4. Inventory Locations (needed for foreign keys)
    op.create_table(
        "procurement_inventory_locations",
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
            sa.ForeignKey("core_campuses.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("type", sa.String(32), nullable=False, server_default="CENTRAL_WAREHOUSE"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_procurement_location_code"),
    )
    op.create_index("idx_procurement_location_campus", "procurement_inventory_locations", ["tenant_id", "campus_id"])

    # 5. Inventory Items
    op.create_table(
        "procurement_inventory_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("sku", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(64), nullable=False, server_default="STATIONERY"),
        sa.Column("unit_of_measure", sa.String(32), nullable=False, server_default="PCS"),
        sa.Column("unit_price_average", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("reorder_threshold", sa.Numeric(12, 2), nullable=False, server_default="10.00"),
        sa.Column("reorder_quantity", sa.Numeric(12, 2), nullable=False, server_default="50.00"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "sku", name="uq_procurement_item_sku"),
    )
    op.create_index("idx_procurement_item_category", "procurement_inventory_items", ["tenant_id", "category"])

    # 6. Purchase Requisitions
    op.create_table(
        "procurement_purchase_requisitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("requisition_number", sa.String(64), nullable=False),
        sa.Column(
            "department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_departments.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "campus_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_campuses.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "requestor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("justification", sa.Text(), nullable=False),
        sa.Column("category", sa.String(64), nullable=False, server_default="GOODS"),
        sa.Column("priority", sa.String(32), nullable=False, server_default="MEDIUM"),
        sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT"),
        sa.Column("required_date", sa.Date(), nullable=False),
        sa.Column("delivery_location", sa.String(255), nullable=False),
        sa.Column("estimated_total_amount", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("currency", sa.String(16), nullable=False, server_default="INR"),
        sa.Column("budget_code", sa.String(64), nullable=True),
        sa.Column(
            "approved_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "requisition_number", name="uq_procurement_req_number"),
    )
    op.create_index("idx_procurement_req_dept", "procurement_purchase_requisitions", ["tenant_id", "department_id"])
    op.create_index("idx_procurement_req_status", "procurement_purchase_requisitions", ["tenant_id", "status"])

    # 7. Purchase Requisition Lines
    op.create_table(
        "procurement_requisition_lines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "requisition_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_purchase_requisitions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_inventory_items.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("item_description", sa.String(255), nullable=False),
        sa.Column("unit_of_measure", sa.String(32), nullable=False, server_default="PCS"),
        sa.Column("quantity_requested", sa.Numeric(12, 2), nullable=False),
        sa.Column("estimated_unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("estimated_total_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("quantity_ordered", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("quantity_fulfilled", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("specifications", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("idx_procurement_req_lines_req", "procurement_requisition_lines", ["tenant_id", "requisition_id"])

    # 8. Quotation Requests (RFQ)
    op.create_table(
        "procurement_quotation_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("rfq_number", sa.String(64), nullable=False),
        sa.Column(
            "requisition_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_purchase_requisitions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("deadline_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT"),
        sa.Column("evaluation_criteria_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "rfq_number", name="uq_procurement_rfq_number"),
    )
    op.create_index("idx_procurement_rfq_status", "procurement_quotation_requests", ["tenant_id", "status"])

    # 9. Vendor Quotations
    op.create_table(
        "procurement_vendor_quotations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "rfq_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_quotation_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "vendor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_vendors.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("quotation_reference", sa.String(128), nullable=False),
        sa.Column("submission_date", sa.Date(), nullable=False),
        sa.Column("validity_until", sa.Date(), nullable=False),
        sa.Column("total_quoted_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("delivery_lead_days", sa.Integer(), nullable=False, server_default="14"),
        sa.Column("warranty_months", sa.Integer(), nullable=False, server_default="12"),
        sa.Column("payment_terms", sa.String(255), nullable=True),
        sa.Column("document_storage_key", sa.String(255), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="SUBMITTED"),
        sa.Column("evaluation_score", sa.Numeric(5, 2), nullable=False, server_default="0.00"),
        sa.Column("disqualification_reason", sa.Text(), nullable=True),
        sa.Column("evaluation_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("idx_procurement_quotation_rfq", "procurement_vendor_quotations", ["tenant_id", "rfq_id"])
    op.create_index("idx_procurement_quotation_vendor", "procurement_vendor_quotations", ["tenant_id", "vendor_id"])

    # 10. Quotation Evaluations
    op.create_table(
        "procurement_quotation_evaluations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "rfq_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_quotation_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "evaluator_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("evaluation_date", sa.Date(), nullable=False),
        sa.Column("scoring_details_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column(
            "recommended_vendor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_vendors.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("award_decision", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("single_source_justification", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("idx_procurement_eval_rfq", "procurement_quotation_evaluations", ["tenant_id", "rfq_id"])

    # 11. Purchase Orders
    op.create_table(
        "procurement_purchase_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("po_number", sa.String(64), nullable=False),
        sa.Column(
            "requisition_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_purchase_requisitions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "rfq_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_quotation_requests.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "vendor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_vendors.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "vendor_quotation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_vendor_quotations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "campus_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_campuses.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT"),
        sa.Column("order_date", sa.Date(), nullable=False),
        sa.Column("expected_delivery_date", sa.Date(), nullable=False),
        sa.Column("delivery_address", sa.String(255), nullable=False),
        sa.Column("billing_address", sa.String(255), nullable=False),
        sa.Column("payment_terms", sa.String(128), nullable=False, server_default="Net 30"),
        sa.Column("currency", sa.String(16), nullable=False, server_default="INR"),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("tax_amount", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("discount_amount", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column(
            "issued_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "approved_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("revision_notes", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "po_number", name="uq_procurement_po_number"),
    )
    op.create_index("idx_procurement_po_vendor", "procurement_purchase_orders", ["tenant_id", "vendor_id"])
    op.create_index("idx_procurement_po_status", "procurement_purchase_orders", ["tenant_id", "status"])

    # 12. Purchase Order Lines
    op.create_table(
        "procurement_purchase_order_lines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "po_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_purchase_orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "requisition_line_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_requisition_lines.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_inventory_items.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("item_description", sa.String(255), nullable=False),
        sa.Column("unit_of_measure", sa.String(32), nullable=False, server_default="PCS"),
        sa.Column("quantity_ordered", sa.Numeric(12, 2), nullable=False),
        sa.Column("quantity_received", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("quantity_accepted", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("quantity_rejected", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("quantity_invoiced", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("tax_rate", sa.Numeric(5, 2), nullable=False, server_default="0.00"),
        sa.Column("tax_amount", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("total_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("idx_procurement_po_lines_po", "procurement_purchase_order_lines", ["tenant_id", "po_id"])

    # 13. Purchase Order Amendments
    op.create_table(
        "procurement_po_amendments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "po_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_purchase_orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("amendment_number", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("changes_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column(
            "requested_by_id",
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
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("idx_procurement_po_amendments_po", "procurement_po_amendments", ["tenant_id", "po_id"])

    # 14. Goods Receipts (GRN)
    op.create_table(
        "procurement_goods_receipts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("grn_number", sa.String(64), nullable=False),
        sa.Column(
            "po_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_purchase_orders.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "vendor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_vendors.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("receipt_date", sa.Date(), nullable=False),
        sa.Column(
            "received_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("carrier_name", sa.String(128), nullable=True),
        sa.Column("tracking_number", sa.String(128), nullable=True),
        sa.Column("delivery_note_reference", sa.String(128), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="RECEIVED"),
        sa.Column(
            "storage_location_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_inventory_locations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("inspection_notes", sa.Text(), nullable=True),
        sa.Column("quality_status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column(
            "inspected_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("inspected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "grn_number", name="uq_procurement_grn_number"),
    )
    op.create_index("idx_procurement_grn_po", "procurement_goods_receipts", ["tenant_id", "po_id"])
    op.create_index("idx_procurement_grn_status", "procurement_goods_receipts", ["tenant_id", "status"])

    # 15. Goods Receipt Lines
    op.create_table(
        "procurement_goods_receipt_lines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "grn_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_goods_receipts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "po_line_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_purchase_order_lines.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_inventory_items.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("item_description", sa.String(255), nullable=False),
        sa.Column("unit_of_measure", sa.String(32), nullable=False, server_default="PCS"),
        sa.Column("quantity_received", sa.Numeric(12, 2), nullable=False),
        sa.Column("quantity_accepted", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("quantity_rejected", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("batch_lot_number", sa.String(64), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("idx_procurement_grn_lines_grn", "procurement_goods_receipt_lines", ["tenant_id", "grn_id"])

    # 16. Stock Balances
    op.create_table(
        "procurement_stock_balances",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_inventory_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "location_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_inventory_locations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("quantity_on_hand", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("quantity_reserved", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("quantity_available", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("quantity_in_transit", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("last_reconciled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "item_id", "location_id", name="uq_procurement_stock_balance"),
    )
    op.create_index("idx_procurement_stock_item", "procurement_stock_balances", ["tenant_id", "item_id"])

    # 17. Stock Movements (Immutable Ledger)
    op.create_table(
        "procurement_stock_movements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("movement_number", sa.String(64), nullable=False),
        sa.Column(
            "item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_inventory_items.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("movement_type", sa.String(32), nullable=False),
        sa.Column(
            "source_location_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_inventory_locations.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "destination_location_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_inventory_locations.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("quantity", sa.Numeric(12, 2), nullable=False),
        sa.Column("unit_cost", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("total_value", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("reference_type", sa.String(64), nullable=True),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "performed_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "movement_number", name="uq_procurement_movement_number"),
    )
    op.create_index("idx_procurement_movements_item", "procurement_stock_movements", ["tenant_id", "item_id"])
    op.create_index("idx_procurement_movements_type", "procurement_stock_movements", ["tenant_id", "movement_type"])

    # 18. Internal Stock Requests
    op.create_table(
        "procurement_internal_stock_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("request_number", sa.String(64), nullable=False),
        sa.Column(
            "department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_departments.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "requestor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "location_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_inventory_locations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("required_date", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "approved_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "request_number", name="uq_procurement_internal_req_number"),
    )
    op.create_index("idx_procurement_internal_req_dept", "procurement_internal_stock_requests", ["tenant_id", "department_id"])
    op.create_index("idx_procurement_internal_req_status", "procurement_internal_stock_requests", ["tenant_id", "status"])

    # 19. Internal Stock Request Lines
    op.create_table(
        "procurement_internal_stock_request_lines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "request_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_internal_stock_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_inventory_items.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("quantity_requested", sa.Numeric(12, 2), nullable=False),
        sa.Column("quantity_issued", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("idx_procurement_internal_req_lines", "procurement_internal_stock_request_lines", ["tenant_id", "request_id"])

    # 20. Three-Way Invoice Matches
    op.create_table(
        "procurement_supplier_invoice_matches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("match_reference", sa.String(64), nullable=False),
        sa.Column(
            "po_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_purchase_orders.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "grn_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_goods_receipts.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("invoice_reference_number", sa.String(128), nullable=False),
        sa.Column("invoice_date", sa.Date(), nullable=False),
        sa.Column("invoice_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("po_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("received_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("quantity_variance", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("price_variance", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("status", sa.String(32), nullable=False, server_default="MATCHED"),
        sa.Column(
            "matched_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("matched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("variance_notes", sa.Text(), nullable=True),
        sa.Column("override_reason", sa.Text(), nullable=True),
        sa.Column(
            "override_approved_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "match_reference", name="uq_procurement_match_ref"),
    )
    op.create_index("idx_procurement_match_po", "procurement_supplier_invoice_matches", ["tenant_id", "po_id"])
    op.create_index("idx_procurement_match_grn", "procurement_supplier_invoice_matches", ["tenant_id", "grn_id"])

    # 21. Vendor Returns (RTV)
    op.create_table(
        "procurement_vendor_returns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("return_number", sa.String(64), nullable=False),
        sa.Column(
            "po_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_purchase_orders.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "grn_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_goods_receipts.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "vendor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_vendors.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("procurement_inventory_items.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("quantity", sa.Numeric(12, 2), nullable=False),
        sa.Column("reason", sa.String(32), nullable=False, server_default="DEFECTIVE"),
        sa.Column("status", sa.String(32), nullable=False, server_default="REQUESTED"),
        sa.Column("resolution_type", sa.String(32), nullable=False, server_default="REPLACEMENT"),
        sa.Column("resolution_reference", sa.String(128), nullable=True),
        sa.Column("credit_note_amount", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "return_number", name="uq_procurement_return_number"),
    )
    op.create_index("idx_procurement_return_vendor", "procurement_vendor_returns", ["tenant_id", "vendor_id"])
    op.create_index("idx_procurement_return_po", "procurement_vendor_returns", ["tenant_id", "po_id"])


def downgrade() -> None:
    op.drop_table("procurement_vendor_returns")
    op.drop_table("procurement_supplier_invoice_matches")
    op.drop_table("procurement_internal_stock_request_lines")
    op.drop_table("procurement_internal_stock_requests")
    op.drop_table("procurement_stock_movements")
    op.drop_table("procurement_stock_balances")
    op.drop_table("procurement_goods_receipt_lines")
    op.drop_table("procurement_goods_receipts")
    op.drop_table("procurement_po_amendments")
    op.drop_table("procurement_purchase_order_lines")
    op.drop_table("procurement_purchase_orders")
    op.drop_table("procurement_quotation_evaluations")
    op.drop_table("procurement_vendor_quotations")
    op.drop_table("procurement_quotation_requests")
    op.drop_table("procurement_requisition_lines")
    op.drop_table("procurement_purchase_requisitions")
    op.drop_table("procurement_inventory_items")
    op.drop_table("procurement_inventory_locations")
    op.drop_table("procurement_vendor_reviews")
    op.drop_table("procurement_vendor_contacts")
    op.drop_table("procurement_vendors")
