"""Enterprise Institutional Library, Learning Resources & Knowledge Access (Step 45).

Revision ID: 031_enterprise_library_learning_resources
Revises: 030_enterprise_research_innovation_grants
Create Date: 2026-10-19 14:00:00.000000

Creates normalized tables for:
- library_branches: Central and departmental library facilities with operating schedules
- library_lending_policies: Configurable lending durations, limits, grace periods, and fine rates
- library_catalog_items: Bibliographic catalog records across print, digital, and media
- library_physical_copies: Accessioned physical inventory volumes with barcodes and shelf locations
- library_member_profiles: Institutional patron profiles with category-based borrowing privileges
- library_circulation_loans: Issue, checkout, renewal, and check-in return tracking with actor attribution
- library_reservations: Resource hold queues, allocation deadlines, and waitlists
- library_fine_records: Overdue and damaged charges integrated with financial obligations and waivers
- library_acquisition_requests: Resource recommendations, approvals, and procurement accessioning
- library_subscriptions: Periodicals, print journals, magazines, and digital repository subscriptions
- library_digital_resource_access: Secure access logging for electronic learning resources
- library_inventory_audits: Physical stock audits, expected snapshots, and discrepancy reconciliation
- library_inventory_audit_items: Scanned physical copy verification findings and resolutions
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "031_enterprise_library_learning_resources"
down_revision = "030_enterprise_research_innovation_grants"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Library Branches
    op.create_table(
        "library_branches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("branch_code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
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
        sa.Column("location_building", sa.String(100), nullable=True),
        sa.Column("location_floor", sa.String(50), nullable=True),
        sa.Column("contact_email", sa.String(255), nullable=True),
        sa.Column("contact_phone", sa.String(50), nullable=True),
        sa.Column("operating_hours_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("closure_dates_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column(
            "head_librarian_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(50), nullable=False, server_default="ACTIVE"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "branch_code", name="uq_library_branch_code_per_tenant"),
    )
    op.create_index("ix_library_branches_tenant_status", "library_branches", ["tenant_id", "status"])

    # 2. Lending Policies
    op.create_table(
        "library_lending_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("policy_code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("member_category", sa.String(50), nullable=False, server_default="STUDENT"),
        sa.Column("resource_type", sa.String(50), nullable=False, server_default="BOOK"),
        sa.Column("max_borrow_limit", sa.Integer(), nullable=False, server_default="4"),
        sa.Column("loan_duration_days", sa.Integer(), nullable=False, server_default="14"),
        sa.Column("renewal_limit", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("fine_daily_rate", sa.Numeric(10, 2), nullable=False, server_default="1.00"),
        sa.Column("fine_grace_period_days", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("max_fine_limit", sa.Numeric(10, 2), nullable=False, server_default="50.00"),
        sa.Column("is_reservation_allowed", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("reservation_queue_limit", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("is_overnight_only", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "policy_code", name="uq_library_lending_policy_code_per_tenant"),
    )
    op.create_index("ix_library_lending_policies_lookup", "library_lending_policies", ["tenant_id", "member_category", "resource_type"])

    # 3. Catalog Items
    op.create_table(
        "library_catalog_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("catalog_code", sa.String(50), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("subtitle", sa.String(500), nullable=True),
        sa.Column("authors_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("publisher", sa.String(255), nullable=True),
        sa.Column("publication_year", sa.Integer(), nullable=True),
        sa.Column("edition", sa.String(50), nullable=True),
        sa.Column("language", sa.String(50), nullable=False, server_default="English"),
        sa.Column("isbn_or_issn", sa.String(50), nullable=True),
        sa.Column("doi_or_urn", sa.String(255), nullable=True),
        sa.Column("call_number", sa.String(100), nullable=True),
        sa.Column("classification_scheme", sa.String(50), nullable=False, server_default="DDC"),
        sa.Column("resource_type", sa.String(50), nullable=False, server_default="BOOK"),
        sa.Column("subject_tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("keywords", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("abstract_description", sa.Text(), nullable=True),
        sa.Column("is_digital", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("digital_access_url", sa.String(1000), nullable=True),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents_records.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("catalog_status", sa.String(50), nullable=False, server_default="CATALOGED"),
        sa.Column("total_copies_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("available_copies_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "catalog_code", name="uq_library_catalog_code_per_tenant"),
    )
    op.create_index("ix_library_catalog_lookup", "library_catalog_items", ["tenant_id", "resource_type", "catalog_status"])
    op.create_index("ix_library_catalog_isbn", "library_catalog_items", ["tenant_id", "isbn_or_issn"])
    op.create_index("ix_library_catalog_title", "library_catalog_items", ["tenant_id", "title"])

    # 4. Physical Copies
    op.create_table(
        "library_physical_copies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "catalog_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("library_catalog_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "owning_library_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("library_branches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("accession_number", sa.String(100), nullable=False),
        sa.Column("barcode", sa.String(100), nullable=True),
        sa.Column("shelf_location", sa.String(100), nullable=True),
        sa.Column("call_number_override", sa.String(100), nullable=True),
        sa.Column("acquisition_date", sa.Date(), nullable=True),
        sa.Column("acquisition_cost", sa.Numeric(10, 2), nullable=True, server_default="0.00"),
        sa.Column("currency", sa.String(10), nullable=False, server_default="USD"),
        sa.Column("condition_grade", sa.String(50), nullable=False, server_default="GOOD"),
        sa.Column("circulation_status", sa.String(50), nullable=False, server_default="AVAILABLE"),
        sa.Column("is_reference_only", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("last_inventory_check_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "accession_number", name="uq_library_copy_accession_per_tenant"),
    )
    op.create_index("ix_library_copies_lookup", "library_physical_copies", ["tenant_id", "owning_library_id", "circulation_status"])
    op.create_index("ix_library_copies_barcode", "library_physical_copies", ["tenant_id", "barcode"])

    # 5. Member Profiles
    op.create_table(
        "library_member_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("membership_number", sa.String(100), nullable=False),
        sa.Column("member_category", sa.String(50), nullable=False, server_default="STUDENT"),
        sa.Column("status", sa.String(50), nullable=False, server_default="ACTIVE"),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.Column("custom_borrow_limit_override", sa.Integer(), nullable=True),
        sa.Column("active_loans_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_historical_loans", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("current_outstanding_fines", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("suspension_reason", sa.Text(), nullable=True),
        sa.Column("suspended_until", sa.Date(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "user_id", name="uq_library_member_user_per_tenant"),
        sa.UniqueConstraint("tenant_id", "membership_number", name="uq_library_member_number_per_tenant"),
    )
    op.create_index("ix_library_members_status", "library_member_profiles", ["tenant_id", "status", "member_category"])

    # 6. Circulation Loans
    op.create_table(
        "library_circulation_loans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("loan_reference_code", sa.String(100), nullable=False),
        sa.Column(
            "copy_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("library_physical_copies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "catalog_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("library_catalog_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "member_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("library_member_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "library_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("library_branches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("returned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("renewal_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_renewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "issued_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "returned_to_library_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("library_branches.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "received_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(50), nullable=False, server_default="ACTIVE"),
        sa.Column("calculated_fine_amount", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("is_fine_posted_to_finance", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "loan_reference_code", name="uq_library_loan_ref_per_tenant"),
    )
    op.create_index("ix_library_loans_active", "library_circulation_loans", ["tenant_id", "status", "due_date"])
    op.create_index("ix_library_loans_member", "library_circulation_loans", ["tenant_id", "member_id", "status"])

    # 7. Reservations
    op.create_table(
        "library_reservations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("reservation_code", sa.String(100), nullable=False),
        sa.Column(
            "catalog_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("library_catalog_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "allocated_copy_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("library_physical_copies.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "member_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("library_member_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "pickup_library_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("library_branches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("queue_position", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("priority_rank", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("reserved_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("allocated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("pickup_deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fulfilled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="WAITING"),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "reservation_code", name="uq_library_reservation_code_per_tenant"),
    )
    op.create_index("ix_library_res_queue", "library_reservations", ["tenant_id", "catalog_item_id", "status", "queue_position"])

    # 8. Fine Records
    op.create_table(
        "library_fine_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("fine_reference_code", sa.String(100), nullable=False),
        sa.Column(
            "loan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("library_circulation_loans.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "member_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("library_member_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("fine_category", sa.String(50), nullable=False, server_default="OVERDUE"),
        sa.Column("base_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("waived_amount", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("final_payable_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False, server_default="USD"),
        sa.Column("fine_status", sa.String(50), nullable=False, server_default="ESTIMATED"),
        sa.Column("days_overdue", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("calculation_basis", sa.String(255), nullable=True),
        sa.Column("finance_invoice_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("finance_payment_reference", sa.String(100), nullable=True),
        sa.Column("waiver_reason", sa.Text(), nullable=True),
        sa.Column(
            "waived_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "fine_reference_code", name="uq_library_fine_ref_per_tenant"),
    )
    op.create_index("ix_library_fines_member", "library_fine_records", ["tenant_id", "member_id", "fine_status"])

    # 9. Acquisition Requests
    op.create_table(
        "library_acquisition_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("request_code", sa.String(100), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("author", sa.String(255), nullable=True),
        sa.Column("publisher", sa.String(255), nullable=True),
        sa.Column("isbn_or_issn", sa.String(50), nullable=True),
        sa.Column(
            "requested_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_departments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "library_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("library_branches.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("justification", sa.Text(), nullable=True),
        sa.Column("number_of_copies", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("estimated_unit_cost", sa.Numeric(10, 2), nullable=True, server_default="0.00"),
        sa.Column("total_estimated_cost", sa.Numeric(10, 2), nullable=True, server_default="0.00"),
        sa.Column("currency", sa.String(10), nullable=False, server_default="USD"),
        sa.Column("approval_status", sa.String(50), nullable=False, server_default="REQUESTED"),
        sa.Column(
            "approved_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("purchase_order_reference", sa.String(100), nullable=True),
        sa.Column("order_date", sa.Date(), nullable=True),
        sa.Column("receipt_date", sa.Date(), nullable=True),
        sa.Column("accession_numbers_created_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "request_code", name="uq_library_acq_code_per_tenant"),
    )
    op.create_index("ix_library_acq_status", "library_acquisition_requests", ["tenant_id", "approval_status"])

    # 10. Subscriptions
    op.create_table(
        "library_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("subscription_code", sa.String(100), nullable=False),
        sa.Column("publication_title", sa.String(500), nullable=False),
        sa.Column("publisher_or_vendor", sa.String(255), nullable=False),
        sa.Column("subscription_type", sa.String(50), nullable=False, server_default="PRINT_JOURNAL"),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("renewal_deadline_date", sa.Date(), nullable=True),
        sa.Column("frequency", sa.String(50), nullable=False, server_default="MONTHLY"),
        sa.Column("annual_subscription_cost", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("currency", sa.String(10), nullable=False, server_default="USD"),
        sa.Column("access_model", sa.String(50), nullable=False, server_default="CAMPUS_WIDE"),
        sa.Column("concurrent_user_limit", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="ACTIVE"),
        sa.Column("digital_access_url", sa.String(1000), nullable=True),
        sa.Column("access_credentials_notes", sa.Text(), nullable=True),
        sa.Column("issues_expected_count", sa.Integer(), nullable=False, server_default="12"),
        sa.Column("issues_received_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "subscription_code", name="uq_library_sub_code_per_tenant"),
    )
    op.create_index("ix_library_sub_status", "library_subscriptions", ["tenant_id", "status", "end_date"])

    # 11. Digital Resource Access
    op.create_table(
        "library_digital_resource_access",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "catalog_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("library_catalog_items.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "subscription_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("library_subscriptions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "member_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("library_member_profiles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("access_timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("access_type", sa.String(50), nullable=False, server_default="VIEW_ONLINE"),
        sa.Column("download_token", sa.String(255), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("bytes_transferred", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_library_digital_access", "library_digital_resource_access", ["tenant_id", "user_id", "access_timestamp"])

    # 12. Inventory Audits
    op.create_table(
        "library_inventory_audits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("audit_code", sa.String(100), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column(
            "library_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("library_branches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("location_section", sa.String(100), nullable=True),
        sa.Column("audit_scope", sa.String(50), nullable=False, server_default="FULL_LIBRARY"),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="PLANNED"),
        sa.Column(
            "auditor_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("total_expected_copies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("verified_present_copies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("missing_copies_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("damaged_copies_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("misplaced_copies_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reconciliation_notes", sa.Text(), nullable=True),
        sa.Column(
            "approved_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "audit_code", name="uq_library_audit_code_per_tenant"),
    )
    op.create_index("ix_library_audits_status", "library_inventory_audits", ["tenant_id", "library_id", "status"])

    # 13. Inventory Audit Items
    op.create_table(
        "library_inventory_audit_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("core_institutions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "audit_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("library_inventory_audits.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "copy_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("library_physical_copies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("accession_number", sa.String(100), nullable=False),
        sa.Column("scanned_barcode", sa.String(100), nullable=True),
        sa.Column("expected_status", sa.String(50), nullable=False),
        sa.Column("scanned_status", sa.String(50), nullable=False, server_default="PRESENT_ON_SHELF"),
        sa.Column("shelf_location_found", sa.String(100), nullable=True),
        sa.Column("discrepancy_resolved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("resolution_action", sa.Text(), nullable=True),
        sa.Column("audited_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column(
            "audited_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people_users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "audit_id", "copy_id", name="uq_library_audit_item_per_audit"),
    )
    op.create_index("ix_library_audit_items", "library_inventory_audit_items", ["tenant_id", "audit_id", "scanned_status"])


def downgrade() -> None:
    op.drop_table("library_inventory_audit_items")
    op.drop_table("library_inventory_audits")
    op.drop_table("library_digital_resource_access")
    op.drop_table("library_subscriptions")
    op.drop_table("library_acquisition_requests")
    op.drop_table("library_fine_records")
    op.drop_table("library_reservations")
    op.drop_table("library_circulation_loans")
    op.drop_table("library_member_profiles")
    op.drop_table("library_physical_copies")
    op.drop_table("library_catalog_items")
    op.drop_table("library_lending_policies")
    op.drop_table("library_branches")
