"""Pydantic Request & Response Schemas for Institutional Library & Learning Resources (Step 45)."""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.library import (
    LibraryAcquisitionStatus,
    LibraryAuditScanResult,
    LibraryBranchStatus,
    LibraryCatalogStatus,
    LibraryCirculationStatus,
    LibraryCopyCondition,
    LibraryFineCategory,
    LibraryFineStatus,
    LibraryInventoryAuditStatus,
    LibraryLoanStatus,
    LibraryMemberCategory,
    LibraryMemberStatus,
    LibraryReservationStatus,
    LibraryResourceType,
    LibrarySubscriptionStatus,
    LibrarySubscriptionType,
)


# =============================================================================
# 1. LIBRARY BRANCH SCHEMAS
# =============================================================================


class LibraryBranchCreate(BaseModel):
    branch_code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=255)
    description: str | None = None
    campus_id: UUID | None = None
    department_id: UUID | None = None
    location_building: str | None = None
    location_floor: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    operating_hours_json: dict[str, Any] = Field(default_factory=dict)
    closure_dates_json: list[Any] = Field(default_factory=list)
    head_librarian_user_id: UUID | None = None
    status: LibraryBranchStatus = LibraryBranchStatus.ACTIVE
    is_active: bool = True
    metadata_json: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)


class LibraryBranchUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    location_building: str | None = None
    location_floor: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    operating_hours_json: dict[str, Any] | None = None
    closure_dates_json: list[Any] | None = None
    head_librarian_user_id: UUID | None = None
    status: LibraryBranchStatus | None = None
    is_active: bool | None = None
    metadata_json: dict[str, Any] | None = None


class LibraryBranchResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    branch_code: str
    name: str
    description: str | None
    campus_id: UUID | None
    department_id: UUID | None
    location_building: str | None
    location_floor: str | None
    contact_email: str | None
    contact_phone: str | None
    operating_hours_json: dict[str, Any]
    closure_dates_json: list[Any]
    head_librarian_user_id: UUID | None
    status: str
    is_active: bool
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LibraryBranchListResponse(BaseModel):
    items: list[LibraryBranchResponse]
    total: int


# =============================================================================
# 2. LENDING POLICY SCHEMAS
# =============================================================================


class LibraryLendingPolicyCreate(BaseModel):
    policy_code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=255)
    library_id: UUID | None = None
    member_category: LibraryMemberCategory = LibraryMemberCategory.STUDENT
    resource_type: LibraryResourceType = LibraryResourceType.BOOK
    max_borrow_limit: int = Field(default=4, ge=1, le=50)
    loan_duration_days: int = Field(default=14, ge=1, le=365)
    renewal_limit: int = Field(default=2, ge=0, le=10)
    max_items_allowed: int | None = None
    loan_period_days: int | None = None
    max_renewals_allowed: int | None = None
    fine_daily_rate: Decimal = Field(default=Decimal("1.00"), ge=Decimal("0.00"))
    fine_grace_period_days: int = Field(default=1, ge=0)
    max_fine_limit: Decimal = Field(default=Decimal("50.00"), ge=Decimal("0.00"))
    is_reservation_allowed: bool = True
    allow_hold_reservations: bool | None = None
    reservation_queue_limit: int = Field(default=2, ge=1)
    is_overnight_only: bool = False
    is_active: bool = True
    metadata_json: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def sync_aliases(self) -> "LibraryLendingPolicyCreate":
        if self.max_items_allowed is not None:
            self.max_borrow_limit = self.max_items_allowed
        if self.loan_period_days is not None:
            self.loan_duration_days = self.loan_period_days
        if self.max_renewals_allowed is not None:
            self.renewal_limit = self.max_renewals_allowed
        if self.allow_hold_reservations is not None:
            self.is_reservation_allowed = self.allow_hold_reservations
        return self


class LibraryLendingPolicyUpdate(BaseModel):
    name: str | None = None
    max_borrow_limit: int | None = None
    loan_duration_days: int | None = None
    renewal_limit: int | None = None
    fine_daily_rate: Decimal | None = None
    fine_grace_period_days: int | None = None
    max_fine_limit: Decimal | None = None
    is_reservation_allowed: bool | None = None
    is_active: bool | None = None
    metadata_json: dict[str, Any] | None = None


class LibraryLendingPolicyResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    policy_code: str
    name: str
    member_category: str
    resource_type: str
    max_borrow_limit: int
    loan_duration_days: int
    renewal_limit: int
    fine_daily_rate: Decimal
    fine_grace_period_days: int
    max_fine_limit: Decimal
    is_reservation_allowed: bool
    reservation_queue_limit: int
    is_overnight_only: bool
    is_active: bool
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 3. CATALOG ITEM SCHEMAS
# =============================================================================


class LibraryCatalogItemCreate(BaseModel):
    catalog_code: str = Field(..., min_length=2, max_length=50)
    title: str = Field(..., min_length=2, max_length=500)
    subtitle: str | None = None
    authors_json: list[Any] = Field(default_factory=list)
    publisher: str | None = None
    publication_year: int | None = None
    edition: str | None = None
    language: str = "English"
    isbn_or_issn: str | None = None
    doi_or_urn: str | None = None
    call_number: str | None = None
    classification_scheme: str = "DDC"
    resource_type: LibraryResourceType = LibraryResourceType.BOOK
    subject_tags: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    abstract_description: str | None = None
    is_digital: bool = False
    digital_access_url: str | None = None
    document_id: UUID | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class LibraryCatalogItemUpdate(BaseModel):
    title: str | None = None
    subtitle: str | None = None
    authors_json: list[Any] | None = None
    publisher: str | None = None
    publication_year: int | None = None
    edition: str | None = None
    isbn_or_issn: str | None = None
    doi_or_urn: str | None = None
    call_number: str | None = None
    resource_type: LibraryResourceType | None = None
    subject_tags: list[str] | None = None
    keywords: list[str] | None = None
    abstract_description: str | None = None
    is_digital: bool | None = None
    digital_access_url: str | None = None
    document_id: UUID | None = None
    catalog_status: LibraryCatalogStatus | None = None
    metadata_json: dict[str, Any] | None = None


class LibraryCatalogItemResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    catalog_code: str
    title: str
    subtitle: str | None
    authors_json: list[Any]
    publisher: str | None
    publication_year: int | None
    edition: str | None
    language: str
    isbn_or_issn: str | None
    doi_or_urn: str | None
    call_number: str | None
    classification_scheme: str
    resource_type: str
    subject_tags: list[Any]
    keywords: list[Any]
    abstract_description: str | None
    is_digital: bool
    digital_access_url: str | None
    document_id: UUID | None
    catalog_status: str
    total_copies_count: int
    available_copies_count: int
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LibraryCatalogItemListResponse(BaseModel):
    items: list[LibraryCatalogItemResponse]
    total: int


# =============================================================================
# 4. PHYSICAL COPY SCHEMAS
# =============================================================================


class LibraryPhysicalCopyCreate(BaseModel):
    catalog_item_id: UUID
    owning_library_id: UUID | None = None
    library_id: UUID | None = None
    accession_number: str = Field(..., min_length=2, max_length=100)
    barcode: str | None = None
    shelf_location: str | None = None
    call_number: str | None = None
    call_number_override: str | None = None
    acquisition_date: date = Field(default_factory=date.today)
    acquisition_cost: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    currency: str = "USD"
    condition_grade: LibraryCopyCondition = LibraryCopyCondition.GOOD
    circulation_status: LibraryCirculationStatus = LibraryCirculationStatus.AVAILABLE
    is_reference_only: bool = False
    notes: str | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def resolve_fields(self) -> "LibraryPhysicalCopyCreate":
        if self.owning_library_id is None and self.library_id is not None:
            self.owning_library_id = self.library_id
        elif self.owning_library_id is None:
            raise ValueError("Either owning_library_id or library_id must be provided")
        if self.call_number_override is None and self.call_number is not None:
            self.call_number_override = self.call_number
        return self


class LibraryPhysicalCopyUpdate(BaseModel):
    owning_library_id: UUID | None = None
    barcode: str | None = None
    shelf_location: str | None = None
    call_number_override: str | None = None
    condition_grade: LibraryCopyCondition | None = None
    circulation_status: LibraryCirculationStatus | None = None
    is_reference_only: bool | None = None
    notes: str | None = None
    metadata_json: dict[str, Any] | None = None


class LibraryPhysicalCopyResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    catalog_item_id: UUID
    owning_library_id: UUID
    accession_number: str
    barcode: str | None
    shelf_location: str | None
    call_number_override: str | None
    acquisition_date: date | None
    acquisition_cost: Decimal | None
    currency: str
    condition_grade: str
    circulation_status: str
    is_reference_only: bool
    last_inventory_check_date: date | None
    notes: str | None
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LibraryPhysicalCopyListResponse(BaseModel):
    items: list[LibraryPhysicalCopyResponse]
    total: int


# =============================================================================
# 5. MEMBER PROFILE SCHEMAS
# =============================================================================


class LibraryMemberProfileCreate(BaseModel):
    user_id: UUID
    membership_number: str = Field(..., min_length=2, max_length=100)
    member_category: LibraryMemberCategory = LibraryMemberCategory.STUDENT
    status: LibraryMemberStatus = LibraryMemberStatus.ACTIVE
    valid_from: date = Field(default_factory=date.today)
    valid_until: date | None = Field(
        default_factory=lambda: date.today() + timedelta(days=365)
    )
    custom_borrow_limit_override: int | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class LibraryMemberProfileUpdate(BaseModel):
    member_category: LibraryMemberCategory | None = None
    status: LibraryMemberStatus | None = None
    valid_until: date | None = None
    custom_borrow_limit_override: int | None = None
    suspension_reason: str | None = None
    suspended_until: date | None = None
    metadata_json: dict[str, Any] | None = None


class LibraryMemberProfileResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    user_id: UUID
    membership_number: str
    member_category: str
    status: str
    valid_from: date
    valid_until: date | None
    custom_borrow_limit_override: int | None
    active_loans_count: int
    total_historical_loans: int
    current_outstanding_fines: Decimal
    suspension_reason: str | None
    suspended_until: date | None
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LibraryMemberListResponse(BaseModel):
    items: list[LibraryMemberProfileResponse]
    total: int


# =============================================================================
# 6. CIRCULATION & LOAN SCHEMAS
# =============================================================================


class LibraryLoanIssueRequest(BaseModel):
    copy_id: UUID
    user_id: UUID | None = None
    member_id: UUID | None = None
    library_id: UUID | None = None
    loan_days_override: int | None = None
    due_date: date | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def validate_user_or_member(self) -> "LibraryLoanIssueRequest":
        if not self.user_id and not self.member_id:
            raise ValueError("Either user_id or member_id must be provided")
        return self


class LibraryLoanReturnRequest(BaseModel):
    returned_to_library_id: UUID | None = None
    condition_grade: LibraryCopyCondition | None = None
    notes: str | None = None


class LibraryLoanRenewRequest(BaseModel):
    requested_days: int | None = None
    extension_days: int | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def sync_extension_days(self) -> "LibraryLoanRenewRequest":
        if self.requested_days is None and self.extension_days is not None:
            self.requested_days = self.extension_days
        elif self.extension_days is None and self.requested_days is not None:
            self.extension_days = self.requested_days
        return self


class LibraryCirculationLoanResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    loan_reference_code: str
    copy_id: UUID
    catalog_item_id: UUID
    member_id: UUID
    user_id: UUID
    library_id: UUID
    issued_at: datetime
    due_date: date
    returned_at: datetime | None
    renewal_count: int
    last_renewed_at: datetime | None
    issued_by_user_id: UUID | None
    returned_to_library_id: UUID | None
    received_by_user_id: UUID | None
    status: str
    calculated_fine_amount: Decimal
    is_fine_posted_to_finance: bool
    notes: str | None
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LibraryCirculationLoanListResponse(BaseModel):
    items: list[LibraryCirculationLoanResponse]
    total: int


# =============================================================================
# 7. RESERVATION SCHEMAS
# =============================================================================


class LibraryReservationCreate(BaseModel):
    catalog_item_id: UUID
    user_id: UUID | None = None
    member_id: UUID | None = None
    pickup_library_id: UUID | None = None
    library_id: UUID | None = None
    priority_rank: int = 10
    metadata_json: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def resolve_fields(self) -> "LibraryReservationCreate":
        if not self.user_id and not self.member_id:
            raise ValueError("Either user_id or member_id must be provided")
        if self.pickup_library_id is None and self.library_id is not None:
            self.pickup_library_id = self.library_id
        elif self.pickup_library_id is None:
            raise ValueError("Either pickup_library_id or library_id must be provided")
        return self


class LibraryReservationCancelRequest(BaseModel):
    reason: str | None = None


class LibraryReservationResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    reservation_code: str
    catalog_item_id: UUID
    allocated_copy_id: UUID | None
    member_id: UUID
    user_id: UUID
    pickup_library_id: UUID
    queue_position: int
    priority_rank: int
    reserved_at: datetime
    allocated_at: datetime | None
    pickup_deadline: datetime | None
    fulfilled_at: datetime | None
    cancelled_at: datetime | None
    expired_at: datetime | None
    status: str
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LibraryReservationListResponse(BaseModel):
    items: list[LibraryReservationResponse]
    total: int


# =============================================================================
# 8. FINE SCHEMAS
# =============================================================================


class LibraryFineAssessRequest(BaseModel):
    loan_id: UUID | None = None
    user_id: UUID | None = None
    member_id: UUID | None = None
    fine_category: LibraryFineCategory = LibraryFineCategory.OVERDUE
    amount: Decimal = Field(..., ge=Decimal("0.01"))
    currency: str = "USD"
    calculation_basis: str | None = None
    days_overdue: int = 0

    @model_validator(mode="after")
    def resolve_user_or_member(self) -> "LibraryFineAssessRequest":
        if not self.user_id and not self.member_id:
            raise ValueError("Either user_id or member_id must be provided")
        return self


class LibraryFineWaiveRequest(BaseModel):
    waive_amount: Decimal | None = None
    waived_amount: Decimal | None = None
    waiver_reason: str = Field(..., min_length=3)

    @model_validator(mode="after")
    def resolve_waived_amount(self) -> "LibraryFineWaiveRequest":
        if self.waive_amount is None and self.waived_amount is not None:
            self.waive_amount = self.waived_amount
        elif self.waive_amount is None:
            raise ValueError("Either waive_amount or waived_amount is required")
        return self


class LibraryFineRecordResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    fine_reference_code: str
    loan_id: UUID | None
    member_id: UUID
    user_id: UUID
    fine_category: str
    base_amount: Decimal
    waived_amount: Decimal
    final_payable_amount: Decimal
    currency: str
    fine_status: str
    days_overdue: int
    calculation_basis: str | None
    finance_invoice_id: UUID | None
    finance_payment_reference: str | None
    waiver_reason: str | None
    waived_by_user_id: UUID | None
    assessed_at: datetime
    resolved_at: datetime | None
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LibraryFineRecordListResponse(BaseModel):
    items: list[LibraryFineRecordResponse]
    total: int


# =============================================================================
# 9. ACQUISITION SCHEMAS
# =============================================================================


class LibraryAcquisitionCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=500)
    author: str | None = None
    publisher: str | None = None
    isbn_or_issn: str | None = None
    department_id: UUID | None = None
    library_id: UUID | None = None
    justification: str | None = None
    number_of_copies: int = Field(default=1, ge=1)
    estimated_unit_cost: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    currency: str = "USD"
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class LibraryAcquisitionApprovalRequest(BaseModel):
    is_approved: bool
    rejection_reason: str | None = None
    purchase_order_reference: str | None = None


class LibraryAcquisitionReceiveRequest(BaseModel):
    accession_numbers: list[str] = Field(..., min_length=1)
    receipt_date: date = Field(default_factory=date.today)


class LibraryAcquisitionResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    request_code: str
    title: str
    author: str | None
    publisher: str | None
    isbn_or_issn: str | None
    requested_by_user_id: UUID
    department_id: UUID | None
    library_id: UUID | None
    justification: str | None
    number_of_copies: int
    estimated_unit_cost: Decimal | None
    total_estimated_cost: Decimal | None
    currency: str
    approval_status: str
    approved_by_user_id: UUID | None
    purchase_order_reference: str | None
    order_date: date | None
    receipt_date: date | None
    accession_numbers_created_json: list[Any]
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LibraryAcquisitionListResponse(BaseModel):
    items: list[LibraryAcquisitionResponse]
    total: int


# =============================================================================
# 10. SUBSCRIPTION SCHEMAS
# =============================================================================


class LibrarySubscriptionCreate(BaseModel):
    subscription_code: str = Field(..., min_length=2, max_length=100)
    publication_title: str = Field(..., min_length=2, max_length=500)
    publisher_or_vendor: str = Field(..., min_length=2, max_length=255)
    subscription_type: LibrarySubscriptionType = LibrarySubscriptionType.PRINT_JOURNAL
    start_date: date = Field(default_factory=date.today)
    end_date: date = Field(
        default_factory=lambda: date.today() + timedelta(days=365)
    )
    renewal_deadline_date: date | None = None
    frequency: str = "MONTHLY"
    annual_subscription_cost: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    currency: str = "USD"
    access_model: str = "CAMPUS_WIDE"
    concurrent_user_limit: int | None = None
    digital_access_url: str | None = None
    digital_access_portal_url: str | None = None
    access_credentials_notes: str | None = None
    issues_expected_count: int = 12
    expected_issues_count: int | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def resolve_fields(self) -> "LibrarySubscriptionCreate":
        if self.expected_issues_count is not None:
            self.issues_expected_count = self.expected_issues_count
        if self.digital_access_portal_url is not None and not self.digital_access_url:
            self.digital_access_url = self.digital_access_portal_url
        return self


class LibrarySubscriptionUpdate(BaseModel):
    end_date: date | None = None
    renewal_deadline_date: date | None = None
    annual_subscription_cost: Decimal | None = None
    status: LibrarySubscriptionStatus | None = None
    issues_received_count: int | None = None
    digital_access_url: str | None = None
    metadata_json: dict[str, Any] | None = None


class LibrarySubscriptionResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    subscription_code: str
    publication_title: str
    publisher_or_vendor: str
    subscription_type: str
    start_date: date
    end_date: date
    renewal_deadline_date: date | None
    frequency: str
    annual_subscription_cost: Decimal
    currency: str
    access_model: str
    concurrent_user_limit: int | None
    status: str
    digital_access_url: str | None
    access_credentials_notes: str | None
    issues_expected_count: int
    issues_received_count: int
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LibrarySubscriptionListResponse(BaseModel):
    items: list[LibrarySubscriptionResponse]
    total: int


# =============================================================================
# 11. DIGITAL RESOURCE ACCESS SCHEMAS
# =============================================================================


class LibraryDigitalResourceAccessLogRequest(BaseModel):
    catalog_item_id: UUID | None = None
    subscription_id: UUID | None = None
    access_type: str = "VIEW_ONLINE"
    ip_address: str | None = None
    bytes_transferred: int = 0


class LibraryDigitalResourceAccessResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    catalog_item_id: UUID | None
    subscription_id: UUID | None
    user_id: UUID
    member_id: UUID | None
    access_timestamp: datetime
    ip_address: str | None
    access_type: str
    download_token: str | None
    token_expires_at: datetime | None
    bytes_transferred: int
    metadata_json: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# 12. INVENTORY AUDIT SCHEMAS
# =============================================================================


class LibraryInventoryAuditCreate(BaseModel):
    audit_code: str = Field(..., min_length=2, max_length=100)
    title: str = Field(..., min_length=2, max_length=255)
    library_id: UUID
    location_section: str | None = None
    audit_scope: str = "FULL_LIBRARY"
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class LibraryInventoryAuditItemScanRequest(BaseModel):
    copy_id: UUID
    accession_number: str
    scanned_barcode: str | None = None
    scanned_status: LibraryAuditScanResult = LibraryAuditScanResult.PRESENT_ON_SHELF
    shelf_location_found: str | None = None
    notes: str | None = None


class LibraryInventoryAuditReconcileRequest(BaseModel):
    reconciliation_notes: str = Field(..., min_length=3)


class LibraryInventoryAuditResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    audit_code: str
    title: str
    library_id: UUID
    location_section: str | None
    audit_scope: str
    start_date: date
    end_date: date | None
    status: str
    auditor_user_id: UUID | None
    total_expected_copies: int
    verified_present_copies: int
    missing_copies_count: int
    damaged_copies_count: int
    misplaced_copies_count: int
    reconciliation_notes: str | None
    approved_by_user_id: UUID | None
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LibraryInventoryAuditItemResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    audit_id: UUID
    copy_id: UUID
    accession_number: str
    scanned_barcode: str | None
    expected_status: str
    scanned_status: str
    shelf_location_found: str | None
    discrepancy_resolved: bool
    resolution_action: str | None
    audited_at: datetime
    audited_by_user_id: UUID | None
    metadata_json: dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


class LibraryInventoryAuditListResponse(BaseModel):
    items: list[LibraryInventoryAuditResponse]
    total: int


# =============================================================================
# 13. ANALYTICS & DEADLINE SWEEP SCHEMAS
# =============================================================================


class LibraryAnalyticsSummaryResponse(BaseModel):
    total_branches: int
    total_catalog_titles: int
    total_physical_copies: int
    available_copies: int
    total_active_members: int
    total_active_loans: int
    total_overdue_loans: int
    total_active_reservations: int
    total_outstanding_fines: Decimal
    total_subscriptions: int
    active_subscriptions: int
    pending_acquisitions: int
    active_inventory_audits: int
    circulation_rate_percentage: float


class LibraryDeadlineSweepResponse(BaseModel):
    processed_at: datetime
    overdue_loans_flagged: int
    fines_computed_amount: Decimal
    expired_reservations_released: int
    expiring_subscriptions_flagged: int


# =============================================================================
# SUPPLEMENTARY SCHEMAS & CONVENIENCE ALIASES
# =============================================================================


class LibraryDigitalAccessTokenResponse(BaseModel):
    catalog_item_id: UUID
    download_token: str
    token_expires_at: datetime
    access_url: str


class LibraryDigitalResourceAccessListResponse(BaseModel):
    items: list[LibraryDigitalResourceAccessResponse]
    total: int


class LibraryLendingPolicyListResponse(BaseModel):
    items: list[LibraryLendingPolicyResponse]
    total: int


class LibraryFinePostToFinanceRequest(BaseModel):
    finance_invoice_id: UUID
    payment_reference: str | None = None


# Type aliases for alternative naming conventions
LibraryDigitalResourceAccessLogResponse = LibraryDigitalResourceAccessResponse
LibraryMemberProfileListResponse = LibraryMemberListResponse
LibraryLoanCheckoutRequest = LibraryLoanIssueRequest
LibraryFineManualAssessmentRequest = LibraryFineAssessRequest
LibraryFineWaiverRequest = LibraryFineWaiveRequest
LibraryAcquisitionRequestCreate = LibraryAcquisitionCreate
LibraryAcquisitionReviewRequest = LibraryAcquisitionApprovalRequest
LibraryAcquisitionRequestResponse = LibraryAcquisitionResponse
LibraryAcquisitionRequestListResponse = LibraryAcquisitionListResponse
LibraryInventoryAuditScanRecordRequest = LibraryInventoryAuditItemScanRequest

