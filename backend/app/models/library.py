"""Enterprise Institutional Library, Learning Resources & Knowledge Access Models (Step 45).

Implements central library administration, multi-branch hierarchies, configurable lending policies,
bibliographic cataloging, physical copy inventory, member access profiles, circulation (checkout/return/renew),
hold reservations & waitlists, overdue fine assessment and waivers, acquisitions procurement,
periodicals/subscriptions, digital learning resources access, and inventory stock audits.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantScopedModel

# =============================================================================
# ENUMS
# =============================================================================


class LibraryBranchStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    TEMPORARILY_CLOSED = "TEMPORARILY_CLOSED"
    RENOVATING = "RENOVATING"


class LibraryResourceType(StrEnum):
    BOOK = "BOOK"
    TEXTBOOK = "TEXTBOOK"
    REFERENCE_BOOK = "REFERENCE_BOOK"
    JOURNAL = "JOURNAL"
    PERIODICAL = "PERIODICAL"
    RESEARCH_PUBLICATION = "RESEARCH_PUBLICATION"
    THESIS_DISSERTATION = "THESIS_DISSERTATION"
    NEWSPAPER_MAGAZINE = "NEWSPAPER_MAGAZINE"
    AUDIO_VIDEO = "AUDIO_VIDEO"
    DIGITAL_BOOK = "DIGITAL_BOOK"
    ELECTRONIC_JOURNAL = "ELECTRONIC_JOURNAL"
    INSTITUTIONAL_DOCUMENT = "INSTITUTIONAL_DOCUMENT"
    OTHER = "OTHER"
    # Aliases
    RESEARCH_PAPER = "RESEARCH_PUBLICATION"
    THESIS = "THESIS_DISSERTATION"
    DISSERTATION = "THESIS_DISSERTATION"
    NEWSPAPER = "NEWSPAPER_MAGAZINE"
    MAGAZINE = "NEWSPAPER_MAGAZINE"
    E_BOOK = "DIGITAL_BOOK"
    E_JOURNAL = "ELECTRONIC_JOURNAL"
    INSTITUTIONAL_PUBLICATION = "INSTITUTIONAL_DOCUMENT"


class LibraryCatalogStatus(StrEnum):
    CATALOGED = "CATALOGED"
    CATALOGUED = "CATALOGED"
    IN_REVIEW = "IN_REVIEW"
    UNDER_REVIEW = "IN_REVIEW"
    WITHDRAWN = "WITHDRAWN"
    ARCHIVED = "ARCHIVED"
    DRAFT = "DRAFT"
    RESTRICTED = "RESTRICTED"


class LibraryCopyCondition(StrEnum):
    NEW = "NEW"
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    FAIR = "FAIR"
    POOR = "POOR"
    DAMAGED = "DAMAGED"
    UNDER_REPAIR = "UNDER_REPAIR"
    LOST = "LOST"
    MISSING = "MISSING"
    WITHDRAWN = "WITHDRAWN"


class LibraryCirculationStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    CHECKED_OUT = "CHECKED_OUT"
    RESERVED = "RESERVED"
    ON_HOLD = "ON_HOLD"
    IN_TRANSIT = "IN_TRANSIT"
    UNDER_REPAIR = "UNDER_REPAIR"
    LOST = "LOST"
    MISSING = "MISSING"
    DAMAGED = "DAMAGED"
    WITHDRAWN = "WITHDRAWN"
    RESTRICTED_REFERENCE_ONLY = "RESTRICTED_REFERENCE_ONLY"


class LibraryMemberCategory(StrEnum):
    STUDENT = "STUDENT"
    FACULTY = "FACULTY"
    RESEARCH_SCHOLAR = "RESEARCH_SCHOLAR"
    STAFF = "STAFF"
    ALUMNI = "ALUMNI"
    EXTERNAL_AFFILIATE = "EXTERNAL_AFFILIATE"
    GUEST = "GUEST"
    UNDERGRADUATE_STUDENT = "STUDENT"
    POSTGRADUATE_STUDENT = "STUDENT"
    DOCTORAL_RESEARCHER = "RESEARCH_SCHOLAR"
    EXTERNAL = "EXTERNAL_AFFILIATE"
    VISITING_SCHOLAR = "FACULTY"


class LibraryMemberStatus(StrEnum):
    ACTIVE = "ACTIVE"
    RESTRICTED = "RESTRICTED"
    SUSPENDED = "SUSPENDED"
    EXPIRED = "EXPIRED"
    INACTIVE = "INACTIVE"
    SUSPENDED_OVERDUE = "SUSPENDED"
    SUSPENDED_FINES = "SUSPENDED"
    SUSPENDED_DISCIPLINARY = "SUSPENDED"


class LibraryLoanStatus(StrEnum):
    ACTIVE = "ACTIVE"
    RETURNED = "RETURNED"
    OVERDUE = "OVERDUE"
    REPORTED_LOST = "REPORTED_LOST"
    DAMAGED_RETURN = "DAMAGED_RETURN"
    LOST = "REPORTED_LOST"
    DAMAGED = "DAMAGED_RETURN"
    CLAIMED_RETURNED = "RETURNED"


class LibraryReservationStatus(StrEnum):
    WAITING = "WAITING"
    ALLOCATED_PENDING_PICKUP = "ALLOCATED_PENDING_PICKUP"
    FULFILLED = "FULFILLED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class LibraryFineCategory(StrEnum):
    OVERDUE = "OVERDUE"
    DAMAGED_COPY = "DAMAGED_COPY"
    DAMAGED_ITEM = "DAMAGED_COPY"
    LOST_ITEM_REPLACEMENT = "LOST_ITEM_REPLACEMENT"
    PROCESSING_FEE = "PROCESSING_FEE"


class LibraryFineStatus(StrEnum):
    ESTIMATED = "ESTIMATED"
    POSTED_TO_FINANCE = "POSTED_TO_FINANCE"
    PAID = "PAID"
    PARTIALLY_WAIVED = "PARTIALLY_WAIVED"
    FULLY_WAIVED = "FULLY_WAIVED"
    DISPUTED = "DISPUTED"


class LibraryAcquisitionStatus(StrEnum):
    REQUESTED = "REQUESTED"
    DEPT_APPROVED = "DEPT_APPROVED"
    LIBRARY_APPROVED = "LIBRARY_APPROVED"
    APPROVED = "LIBRARY_APPROVED"
    REJECTED = "REJECTED"
    ORDERED = "ORDERED"
    RECEIVED = "RECEIVED"
    ACCESSIONED = "ACCESSIONED"
    CANCELLED = "CANCELLED"


class LibrarySubscriptionType(StrEnum):
    PRINT_JOURNAL = "PRINT_JOURNAL"
    MAGAZINE = "MAGAZINE"
    NEWSPAPER = "NEWSPAPER"
    ELECTRONIC_JOURNAL_DATABASE = "ELECTRONIC_JOURNAL_DATABASE"
    E_JOURNAL_PACKAGE = "ELECTRONIC_JOURNAL_DATABASE"
    ONLINE_REPOSITORY = "ONLINE_REPOSITORY"


class LibrarySubscriptionStatus(StrEnum):
    ACTIVE = "ACTIVE"
    PENDING_RENEWAL = "PENDING_RENEWAL"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class LibraryInventoryAuditStatus(StrEnum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    RECONCILIATION = "RECONCILIATION"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class LibraryAuditScanResult(StrEnum):
    PRESENT_ON_SHELF = "PRESENT_ON_SHELF"
    MISSING = "MISSING"
    DAMAGED = "DAMAGED"
    MISPLACED = "MISPLACED"
    UNREGISTERED = "UNREGISTERED"


# =============================================================================
# MODELS
# =============================================================================


class LibraryBranch(TenantScopedModel):
    """Institutional library branch or learning resource centre."""

    __tablename__ = "library_branches"

    branch_code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    location_building: Mapped[str | None] = mapped_column(String(100), nullable=True)
    location_floor: Mapped[str | None] = mapped_column(String(50), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    operating_hours_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    closure_dates_json: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    head_librarian_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=LibraryBranchStatus.ACTIVE.value
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "branch_code", name="uq_library_branch_code_per_tenant"),
        Index("ix_library_branches_tenant_status", "tenant_id", "status"),
    )


class LibraryLendingPolicy(TenantScopedModel):
    """Lending rules and limits per member category and resource type."""

    __tablename__ = "library_lending_policies"

    policy_code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    member_category: Mapped[str] = mapped_column(
        String(50), nullable=False, default=LibraryMemberCategory.STUDENT.value
    )
    resource_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default=LibraryResourceType.BOOK.value
    )
    max_borrow_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    loan_duration_days: Mapped[int] = mapped_column(Integer, nullable=False, default=14)
    renewal_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    fine_daily_rate: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("1.00")
    )
    fine_grace_period_days: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    max_fine_limit: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("50.00")
    )
    is_reservation_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    reservation_queue_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    is_overnight_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "policy_code",
            name="uq_library_lending_policy_code_per_tenant",
        ),
        Index("ix_library_lending_policies_lookup", "tenant_id", "member_category", "resource_type"),
    )

    @property
    def max_items_allowed(self) -> int:
        return self.max_borrow_limit

    @property
    def loan_period_days(self) -> int:
        return self.loan_duration_days

    @property
    def max_renewals_allowed(self) -> int:
        return self.renewal_limit

    @property
    def allow_hold_reservations(self) -> bool:
        return self.is_reservation_allowed


class LibraryCatalogItem(TenantScopedModel):
    """Bibliographic catalog record."""

    __tablename__ = "library_catalog_items"

    catalog_code: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(500), nullable=True)
    authors_json: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    publisher: Mapped[str | None] = mapped_column(String(255), nullable=True)
    publication_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    edition: Mapped[str | None] = mapped_column(String(50), nullable=True)
    language: Mapped[str] = mapped_column(String(50), nullable=False, default="English")
    isbn_or_issn: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    doi_or_urn: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    call_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    classification_scheme: Mapped[str] = mapped_column(String(50), nullable=False, default="DDC")
    resource_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default=LibraryResourceType.BOOK.value
    )
    subject_tags: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    keywords: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    abstract_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_digital: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    digital_access_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    document_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents_records.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    catalog_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=LibraryCatalogStatus.CATALOGED.value
    )
    total_copies_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    available_copies_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    @property
    def status(self) -> str:
        return self.catalog_status

    @status.setter
    def status(self, val: str) -> None:
        self.catalog_status = val

    __table_args__ = (
        UniqueConstraint("tenant_id", "catalog_code", name="uq_library_catalog_code_per_tenant"),
        Index("ix_library_catalog_lookup", "tenant_id", "resource_type", "catalog_status"),
        Index("ix_library_catalog_title", "tenant_id", "title"),
    )


class LibraryPhysicalCopy(TenantScopedModel):
    """Specific physical copy/volume with unique accession number."""

    __tablename__ = "library_physical_copies"

    catalog_item_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("library_catalog_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    owning_library_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("library_branches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    accession_number: Mapped[str] = mapped_column(String(100), nullable=False)
    barcode: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    shelf_location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    call_number_override: Mapped[str | None] = mapped_column(String(100), nullable=True)
    acquisition_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    acquisition_cost: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True, default=Decimal("0.00")
    )
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    condition_grade: Mapped[str] = mapped_column(
        String(50), nullable=False, default=LibraryCopyCondition.GOOD.value
    )
    circulation_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=LibraryCirculationStatus.AVAILABLE.value
    )
    is_reference_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_inventory_check_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "accession_number",
            name="uq_library_copy_accession_per_tenant",
        ),
        Index("ix_library_copies_lookup", "tenant_id", "owning_library_id", "circulation_status"),
    )

    @property
    def library_id(self) -> UUID:
        return self.owning_library_id

    @library_id.setter
    def library_id(self, value: UUID) -> None:
        self.owning_library_id = value

    @property
    def call_number(self) -> str | None:
        return self.call_number_override

    @call_number.setter
    def call_number(self, value: str | None) -> None:
        self.call_number_override = value


class LibraryMemberProfile(TenantScopedModel):
    """Institutional library patron profile."""

    __tablename__ = "library_member_profiles"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    membership_number: Mapped[str] = mapped_column(String(100), nullable=False)
    member_category: Mapped[str] = mapped_column(
        String(50), nullable=False, default=LibraryMemberCategory.STUDENT.value
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=LibraryMemberStatus.ACTIVE.value
    )
    valid_from: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    custom_borrow_limit_override: Mapped[int | None] = mapped_column(Integer, nullable=True)
    active_loans_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_historical_loans: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_outstanding_fines: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0.00")
    )
    suspension_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    suspended_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "user_id", name="uq_library_member_user_per_tenant"
        ),
        UniqueConstraint(
            "tenant_id",
            "membership_number",
            name="uq_library_member_number_per_tenant",
        ),
        Index("ix_library_members_status", "tenant_id", "status", "member_category"),
    )

    @property
    def current_active_loans(self) -> int:
        return self.active_loans_count

    @current_active_loans.setter
    def current_active_loans(self, value: int) -> None:
        self.active_loans_count = value

    @property
    def is_borrowing_suspended(self) -> bool:
        return self.status in (
            LibraryMemberStatus.SUSPENDED.value,
            "SUSPENDED",
            "SUSPENDED_FINES",
            "SUSPENDED_OVERDUE",
            "SUSPENDED_DISCIPLINARY",
            "RESTRICTED",
            "INACTIVE",
            "EXPIRED",
        )

    @is_borrowing_suspended.setter
    def is_borrowing_suspended(self, value: bool) -> None:
        if value:
            self.status = LibraryMemberStatus.SUSPENDED.value
        elif self.status in (LibraryMemberStatus.SUSPENDED.value, "SUSPENDED"):
            self.status = LibraryMemberStatus.ACTIVE.value


class LibraryCirculationLoan(TenantScopedModel):
    """Authoritative issue, loan, and return transaction."""

    __tablename__ = "library_circulation_loans"

    loan_reference_code: Mapped[str] = mapped_column(String(100), nullable=False)
    copy_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("library_physical_copies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    catalog_item_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("library_catalog_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    member_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("library_member_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    library_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("library_branches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    renewal_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_renewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    issued_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    returned_to_library_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("library_branches.id", ondelete="SET NULL"),
        nullable=True,
    )
    received_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=LibraryLoanStatus.ACTIVE.value
    )
    calculated_fine_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0.00")
    )
    is_fine_posted_to_finance: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "loan_reference_code",
            name="uq_library_loan_ref_per_tenant",
        ),
        Index("ix_library_loans_active", "tenant_id", "status", "due_date"),
    )


class LibraryReservation(TenantScopedModel):
    """Resource hold and reservation queue."""

    __tablename__ = "library_reservations"

    reservation_code: Mapped[str] = mapped_column(String(100), nullable=False)
    catalog_item_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("library_catalog_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    allocated_copy_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("library_physical_copies.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    member_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("library_member_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pickup_library_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("library_branches.id", ondelete="CASCADE"),
        nullable=False,
    )
    queue_position: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    priority_rank: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    reserved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    allocated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    pickup_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fulfilled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=LibraryReservationStatus.WAITING.value
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "reservation_code",
            name="uq_library_reservation_code_per_tenant",
        ),
        Index("ix_library_res_queue", "tenant_id", "catalog_item_id", "status", "queue_position"),
    )


class LibraryFineRecord(TenantScopedModel):
    """Overdue, damage, or replacement fee record."""

    __tablename__ = "library_fine_records"

    fine_reference_code: Mapped[str] = mapped_column(String(100), nullable=False)
    loan_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("library_circulation_loans.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    member_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("library_member_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fine_category: Mapped[str] = mapped_column(
        String(50), nullable=False, default=LibraryFineCategory.OVERDUE.value
    )
    base_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    waived_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0.00")
    )
    final_payable_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    fine_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=LibraryFineStatus.ESTIMATED.value
    )
    days_overdue: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    calculation_basis: Mapped[str | None] = mapped_column(String(255), nullable=True)
    finance_invoice_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )
    finance_payment_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    waiver_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    waived_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "fine_reference_code",
            name="uq_library_fine_ref_per_tenant",
        ),
        Index("ix_library_fines_member", "tenant_id", "member_id", "fine_status"),
    )


class LibraryAcquisitionRequest(TenantScopedModel):
    """Book/resource purchase recommendation and procurement tracking."""

    __tablename__ = "library_acquisition_requests"

    request_code: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(255), nullable=True)
    isbn_or_issn: Mapped[str | None] = mapped_column(String(50), nullable=True)
    requested_by_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    library_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("library_branches.id", ondelete="SET NULL"),
        nullable=True,
    )
    justification: Mapped[str | None] = mapped_column(Text, nullable=True)
    number_of_copies: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    estimated_unit_cost: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True, default=Decimal("0.00")
    )
    total_estimated_cost: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True, default=Decimal("0.00")
    )
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    approval_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=LibraryAcquisitionStatus.REQUESTED.value
    )
    approved_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    purchase_order_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    order_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    receipt_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    accession_numbers_created_json: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "request_code",
            name="uq_library_acq_code_per_tenant",
        ),
        Index("ix_library_acq_status", "tenant_id", "approval_status"),
    )


class LibrarySubscription(TenantScopedModel):
    """Journal, periodical, newspaper, or digital repository subscription."""

    __tablename__ = "library_subscriptions"

    subscription_code: Mapped[str] = mapped_column(String(100), nullable=False)
    publication_title: Mapped[str] = mapped_column(String(500), nullable=False)
    publisher_or_vendor: Mapped[str] = mapped_column(String(255), nullable=False)
    subscription_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default=LibrarySubscriptionType.PRINT_JOURNAL.value
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    renewal_deadline_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    frequency: Mapped[str] = mapped_column(String(50), nullable=False, default="MONTHLY")
    annual_subscription_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0.00")
    )
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    access_model: Mapped[str] = mapped_column(String(50), nullable=False, default="CAMPUS_WIDE")
    concurrent_user_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=LibrarySubscriptionStatus.ACTIVE.value
    )
    digital_access_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    access_credentials_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    issues_expected_count: Mapped[int] = mapped_column(Integer, nullable=False, default=12)
    issues_received_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "subscription_code",
            name="uq_library_sub_code_per_tenant",
        ),
        Index("ix_library_sub_status", "tenant_id", "status", "end_date"),
    )


class LibraryDigitalResourceAccess(TenantScopedModel):
    """Audit log of accessed or downloaded electronic library materials."""

    __tablename__ = "library_digital_resource_access"

    catalog_item_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("library_catalog_items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    subscription_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("library_subscriptions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    member_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("library_member_profiles.id", ondelete="SET NULL"),
        nullable=True,
    )
    access_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    access_type: Mapped[str] = mapped_column(String(50), nullable=False, default="VIEW_ONLINE")
    download_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    bytes_transferred: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    __table_args__ = (
        Index("ix_library_digital_access", "tenant_id", "user_id", "access_timestamp"),
    )


class LibraryInventoryAudit(TenantScopedModel):
    """Stock audit session and reconciliation."""

    __tablename__ = "library_inventory_audits"

    audit_code: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    library_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("library_branches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    location_section: Mapped[str | None] = mapped_column(String(100), nullable=True)
    audit_scope: Mapped[str] = mapped_column(String(50), nullable=False, default="FULL_LIBRARY")
    start_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=LibraryInventoryAuditStatus.PLANNED.value
    )
    auditor_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    total_expected_copies: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    verified_present_copies: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    missing_copies_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    damaged_copies_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    misplaced_copies_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reconciliation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "audit_code", name="uq_library_audit_code_per_tenant"
        ),
        Index("ix_library_audits_status", "tenant_id", "library_id", "status"),
    )


class LibraryInventoryAuditItem(TenantScopedModel):
    """Scanned physical copy finding in an inventory audit."""

    __tablename__ = "library_inventory_audit_items"

    audit_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("library_inventory_audits.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    copy_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("library_physical_copies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    accession_number: Mapped[str] = mapped_column(String(100), nullable=False)
    scanned_barcode: Mapped[str | None] = mapped_column(String(100), nullable=True)
    expected_status: Mapped[str] = mapped_column(String(50), nullable=False)
    scanned_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=LibraryAuditScanResult.PRESENT_ON_SHELF.value
    )
    shelf_location_found: Mapped[str | None] = mapped_column(String(100), nullable=True)
    discrepancy_resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    resolution_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    audited_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    audited_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "audit_id", "copy_id", name="uq_library_audit_item_per_audit"
        ),
        Index("ix_library_audit_items", "tenant_id", "audit_id", "scanned_status"),
    )
