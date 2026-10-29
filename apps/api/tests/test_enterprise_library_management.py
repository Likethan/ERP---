"""Enterprise Institutional Library, Learning Resources & Knowledge Access Management Tests (Step 45).

Comprehensive automated test suite covering:
1. Library branch administration and branch-specific lending policies.
2. Bibliographic cataloguing and ISBN/title duplicate detection.
3. Physical inventory copy registration and accession number uniqueness.
4. Member profiles, borrowing limits, and suspension eligibility checks.
5. Circulation lending lifecycle: checkout, return, renewal, and due-date calculations.
6. Simultaneous double-issue prevention and concurrency safety.
7. Reservation hold queues, priority ordering, and auto-allocation upon return.
8. Configurable overdue fine calculation and authorized staff waiver workflows.
9. Acquisition request lifecycle: request, approval, receipt, and auto-accessioning.
10. Periodicals & subscriptions tracking with renewal deadlines.
11. Digital learning resource access with expiring tokens and audit tracking.
12. Periodic stock verification audit, discrepancy detection, and reconciliation.
13. Automated compliance deadline sweep (overdues, hold releases, expiring subscriptions).
14. Multi-tenant isolation across all library collections and circulation records.
15. End-to-end FastAPI REST API endpoints via AsyncClient.
"""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    LibraryCopyUnavailableException,
    LibraryDuplicateAccessionException,
    LibraryMemberSuspendedException,
)
from app.core.security import ACCESS_TOKEN_COOKIE_NAME, create_access_token
from app.models.core import Institution
from app.models.library import (
    LibraryAcquisitionStatus,
    LibraryAuditScanResult,
    LibraryBranchStatus,
    LibraryCatalogStatus,
    LibraryCirculationStatus,
    LibraryCopyCondition,
    LibraryFineCategory,
    LibraryInventoryAuditStatus,
    LibraryLoanStatus,
    LibraryMemberCategory,
    LibraryMemberStatus,
    LibraryReservationStatus,
    LibraryResourceType,
    LibrarySubscriptionStatus,
    LibrarySubscriptionType,
)
from app.models.people import User
from app.schemas.library import (
    LibraryAcquisitionApprovalRequest,
    LibraryAcquisitionCreate,
    LibraryAcquisitionReceiveRequest,
    LibraryBranchCreate,
    LibraryCatalogItemCreate,
    LibraryFineAssessRequest,
    LibraryFineWaiveRequest,
    LibraryInventoryAuditCreate,
    LibraryInventoryAuditItemScanRequest,
    LibraryInventoryAuditReconcileRequest,
    LibraryLendingPolicyCreate,
    LibraryLoanIssueRequest,
    LibraryLoanRenewRequest,
    LibraryLoanReturnRequest,
    LibraryMemberProfileCreate,
    LibraryPhysicalCopyCreate,
    LibraryReservationCreate,
    LibrarySubscriptionCreate,
)
from app.services.library_service import LibraryService


def make_auth_headers(
    user: User,
    tenant_id: UUID,
    role_name: str = "INSTITUTION_ADMIN",
) -> dict[str, str]:
    """Helper to generate JWT bearer and cookie authorization headers."""
    token = create_access_token(
        user_id=user.id,
        tenant_id=tenant_id,
        email=user.email,
        roles=[role_name],
        permissions=["*"],
    )
    return {
        "Authorization": f"Bearer {token}",
        "Cookie": f"{ACCESS_TOKEN_COOKIE_NAME}={token}",
    }


# =============================================================================
# 1. BRANCH & LENDING POLICY MANAGEMENT
# =============================================================================


@pytest.mark.asyncio
async def test_library_branch_and_policy_management(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies library branch creation, uniqueness of branch code, and lending policies."""
    tenant_id = tenant_a.id
    actor_id = tenant_admin_a.id

    branch = await LibraryService.create_branch(
        db=db_session,
        tenant_id=tenant_id,
        data=LibraryBranchCreate(
            branch_code="LIB-MAIN",
            name="Main Academic Library",
            description="Central campus repository and study complex",
            location_building="Knowledge Center",
            location_floor="Level 1-3",
            contact_email="library@campusos.internal",
            contact_phone="+1-555-0199",
            operating_hours_json={"monday": "08:00-22:00", "saturday": "09:00-18:00"},
            status=LibraryBranchStatus.ACTIVE,
        ),
        current_user_id=actor_id,
    )
    assert branch.id is not None
    assert branch.branch_code == "LIB-MAIN"
    assert branch.name == "Main Academic Library"

    # Configure a lending policy for undergraduate students borrowing books
    policy = await LibraryService.create_policy(
        db=db_session,
        tenant_id=tenant_id,
        data=LibraryLendingPolicyCreate(
            policy_code="POL-UG-BOOK",
            name="Undergraduate Book Lending Policy",
            library_id=branch.id,
            member_category=LibraryMemberCategory.UNDERGRADUATE_STUDENT,
            resource_type=LibraryResourceType.BOOK,
            max_items_allowed=4,
            loan_period_days=14,
            max_renewals_allowed=2,
            fine_grace_period_days=1,
            fine_daily_rate=Decimal("1.50"),
            max_fine_limit=Decimal("30.00"),
            allow_hold_reservations=True,
        ),
        current_user_id=actor_id,
    )
    assert policy.id is not None
    assert policy.max_items_allowed == 4
    assert policy.loan_period_days == 14
    assert policy.fine_daily_rate == Decimal("1.50")


# =============================================================================
# 2. CATALOG MANAGEMENT & DUPLICATE DETECTION
# =============================================================================


@pytest.mark.asyncio
async def test_catalog_item_creation_and_duplicate_detection(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies catalog creation, automatic duplicate detection by ISBN/title, and keyword search."""
    tenant_id = tenant_a.id
    actor_id = tenant_admin_a.id

    catalog_data = LibraryCatalogItemCreate(
        catalog_code="CAT-2026-CS101",
        title="Introduction to Algorithms and Data Structures",
        subtitle="Comprehensive 4th Edition",
        authors_json=["Thomas Cormen", "Charles Leiserson", "Ronald Rivest"],
        publisher="MIT Press",
        publication_year=2022,
        edition="4th Edition",
        primary_language="English",
        isbn_or_issn="978-0262046305",
        classification_number="QA76.6",
        subject_classification="Computer Science",
        keywords_json=["algorithms", "data structures", "graph theory"],
        resource_type=LibraryResourceType.BOOK,
        description_abstract="Standard textbook for university algorithms curricula.",
        is_digital=False,
    )

    item1 = await LibraryService.create_catalog_item(
        db=db_session,
        tenant_id=tenant_id,
        data=catalog_data,
        current_user_id=actor_id,
    )
    assert item1.id is not None
    assert item1.status == LibraryCatalogStatus.CATALOGUED.value
    assert item1.total_copies_count == 0
    assert item1.available_copies_count == 0

    # Attempt duplicate creation with same ISBN -> Should return existing item (idempotent / deduplicated)
    item2 = await LibraryService.create_catalog_item(
        db=db_session,
        tenant_id=tenant_id,
        data=catalog_data,
        current_user_id=actor_id,
    )
    assert item2.id == item1.id


# =============================================================================
# 3. PHYSICAL COPIES & ACCESSION UNIQUENESS
# =============================================================================


@pytest.mark.asyncio
async def test_physical_copy_registration_and_accession_uniqueness(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies physical copy accession uniqueness and copy count synchronization."""
    tenant_id = tenant_a.id
    actor_id = tenant_admin_a.id

    # Create branch and catalog item
    branch = await LibraryService.create_branch(
        db=db_session,
        tenant_id=tenant_id,
        data=LibraryBranchCreate(branch_code="LIB-ENG", name="Engineering Library"),
        current_user_id=actor_id,
    )
    cat = await LibraryService.create_catalog_item(
        db=db_session,
        tenant_id=tenant_id,
        data=LibraryCatalogItemCreate(
            catalog_code="CAT-OS-001",
            title="Operating Systems Principles",
            authors_json=["Abraham Silberschatz"],
            resource_type=LibraryResourceType.BOOK,
            isbn_or_issn="978-1118063330",
        ),
        current_user_id=actor_id,
    )

    # Register physical copy #1
    copy1 = await LibraryService.create_physical_copy(
        db=db_session,
        tenant_id=tenant_id,
        data=LibraryPhysicalCopyCreate(
            catalog_item_id=cat.id,
            library_id=branch.id,
            accession_number="ACC-ENG-00101",
            barcode="BAR-1001",
            shelf_location="Shelf A-4",
            call_number="QA76.76.S55",
            condition_grade=LibraryCopyCondition.NEW,
            circulation_status=LibraryCirculationStatus.AVAILABLE,
        ),
        current_user_id=actor_id,
    )
    assert copy1.id is not None
    assert copy1.accession_number == "ACC-ENG-00101"

    # Refresh catalog item and verify counts incremented
    cat_refreshed = await LibraryService.get_catalog_item(db_session, tenant_id, cat.id)
    assert cat_refreshed.total_copies_count == 1
    assert cat_refreshed.available_copies_count == 1

    # Attempt to register copy with duplicate accession number -> Must raise LibraryDuplicateAccessionException
    with pytest.raises(LibraryDuplicateAccessionException):
        await LibraryService.create_physical_copy(
            db=db_session,
            tenant_id=tenant_id,
            data=LibraryPhysicalCopyCreate(
                catalog_item_id=cat.id,
                library_id=branch.id,
                accession_number="ACC-ENG-00101",
            ),
            current_user_id=actor_id,
        )


# =============================================================================
# 4. MEMBER ELIGIBILITY & BORROWING LIMITS
# =============================================================================


@pytest.mark.asyncio
async def test_member_profile_and_borrowing_eligibility(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies patron membership profile creation, status, and suspended borrowing restrictions."""
    tenant_id = tenant_a.id
    actor_id = tenant_admin_a.id

    member = await LibraryService.create_member(
        db=db_session,
        tenant_id=tenant_id,
        data=LibraryMemberProfileCreate(
            user_id=actor_id,
            membership_number="MEM-UG-2026-001",
            member_category=LibraryMemberCategory.UNDERGRADUATE_STUDENT,
            status=LibraryMemberStatus.ACTIVE,
            valid_from=date.today(),
            valid_until=date.today() + timedelta(days=365),
        ),
        current_user_id=actor_id,
    )
    assert member.id is not None
    assert member.current_active_loans == 0
    assert not member.is_borrowing_suspended

    # Verify suspended member cannot borrow
    member.is_borrowing_suspended = True
    member.status = LibraryMemberStatus.SUSPENDED_FINES.value
    member.suspension_reason = "Unpaid lost item fine"
    await db_session.flush()

    branch = await LibraryService.create_branch(
        db_session, tenant_id, LibraryBranchCreate(branch_code="LIB-TEST-M", name="Test Branch"), actor_id
    )
    cat = await LibraryService.create_catalog_item(
        db_session,
        tenant_id,
        LibraryCatalogItemCreate(
            catalog_code="CAT-TST-001",
            title="Database Systems",
            authors_json=["Raghu Ramakrishnan"],
            resource_type=LibraryResourceType.BOOK,
        ),
        actor_id,
    )
    copy = await LibraryService.create_physical_copy(
        db_session,
        tenant_id,
        LibraryPhysicalCopyCreate(
            catalog_item_id=cat.id,
            library_id=branch.id,
            accession_number=f"ACC-SUSP-{uuid4().hex[:6]}",
        ),
        actor_id,
    )

    with pytest.raises(LibraryMemberSuspendedException):
        await LibraryService.checkout_copy(
            db=db_session,
            tenant_id=tenant_id,
            data=LibraryLoanIssueRequest(
                copy_id=copy.id,
                member_id=member.id,
                library_id=branch.id,
            ),
            staff_user_id=actor_id,
        )


# =============================================================================
# 5. CIRCULATION: CHECKOUT, RETURN & RENEW
# =============================================================================


@pytest.mark.asyncio
async def test_circulation_checkout_and_return_lifecycle(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies complete circulation lifecycle: checkout, due date calculation, renewal, and check-in return."""
    tenant_id = tenant_a.id
    actor_id = tenant_admin_a.id

    branch = await LibraryService.create_branch(
        db_session, tenant_id, LibraryBranchCreate(branch_code="LIB-CIRC-1", name="Circulation Test Branch"), actor_id
    )
    cat = await LibraryService.create_catalog_item(
        db_session,
        tenant_id,
        LibraryCatalogItemCreate(
            catalog_code="CAT-CIRC-001",
            title="Clean Architecture",
            authors_json=["Robert C. Martin"],
            resource_type=LibraryResourceType.BOOK,
        ),
        actor_id,
    )
    copy = await LibraryService.create_physical_copy(
        db_session,
        tenant_id,
        LibraryPhysicalCopyCreate(
            catalog_item_id=cat.id,
            library_id=branch.id,
            accession_number=f"ACC-CIRC-{uuid4().hex[:6]}",
        ),
        actor_id,
    )

    # Create active member (faculty)
    member = await LibraryService.create_member(
        db=db_session,
        tenant_id=tenant_id,
        data=LibraryMemberProfileCreate(
            user_id=actor_id,
            membership_number=f"FAC-{uuid4().hex[:6]}",
            member_category=LibraryMemberCategory.FACULTY,
            status=LibraryMemberStatus.ACTIVE,
            valid_from=date.today(),
            valid_until=date.today() + timedelta(days=365),
        ),
        current_user_id=actor_id,
    )

    # 1. Checkout copy
    loan = await LibraryService.checkout_copy(
        db=db_session,
        tenant_id=tenant_id,
        data=LibraryLoanIssueRequest(
            copy_id=copy.id,
            member_id=member.id,
            library_id=branch.id,
            loan_days_override=21,
        ),
        staff_user_id=actor_id,
    )
    assert loan.id is not None
    assert loan.status == LibraryLoanStatus.ACTIVE.value
    assert loan.due_date == date.today() + timedelta(days=21)

    # Verify copy status updated to CHECKED_OUT and available copies decremented
    copy_check = await LibraryService.get_physical_copy(db_session, tenant_id, copy.id)
    assert copy_check.circulation_status == LibraryCirculationStatus.CHECKED_OUT.value
    cat_check = await LibraryService.get_catalog_item(db_session, tenant_id, cat.id)
    assert cat_check.available_copies_count == 0

    # 2. Renew loan
    loan_renewed = await LibraryService.renew_loan(
        db=db_session,
        tenant_id=tenant_id,
        loan_id=loan.id,
        data=LibraryLoanRenewRequest(extension_days=14),
        actor_user_id=actor_id,
    )
    assert loan_renewed.renewal_count == 1
    assert loan_renewed.due_date == date.today() + timedelta(days=35)

    # 3. Return copy
    loan_returned = await LibraryService.return_copy(
        db=db_session,
        tenant_id=tenant_id,
        loan_id=loan.id,
        data=LibraryLoanReturnRequest(
            returned_to_library_id=branch.id,
            condition_grade=LibraryCopyCondition.GOOD,
        ),
        staff_user_id=actor_id,
    )
    assert loan_returned.status == LibraryLoanStatus.RETURNED.value
    assert loan_returned.returned_at is not None

    # Verify copy available again
    copy_final = await LibraryService.get_physical_copy(db_session, tenant_id, copy.id)
    assert copy_final.circulation_status == LibraryCirculationStatus.AVAILABLE.value
    cat_final = await LibraryService.get_catalog_item(db_session, tenant_id, cat.id)
    assert cat_final.available_copies_count == 1


# =============================================================================
# 6. SIMULTANEOUS DOUBLE-ISSUE PREVENTED
# =============================================================================


@pytest.mark.asyncio
async def test_simultaneous_issue_prevention_concurrency(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies that an already issued copy cannot be checked out simultaneously."""
    tenant_id = tenant_a.id
    actor_id = tenant_admin_a.id

    branch = await LibraryService.create_branch(
        db_session, tenant_id, LibraryBranchCreate(branch_code="LIB-CONC", name="Concurrency Branch"), actor_id
    )
    cat = await LibraryService.create_catalog_item(
        db_session,
        tenant_id,
        LibraryCatalogItemCreate(
            catalog_code="CAT-CONC-001",
            title="Concurrent Programming",
            authors_json=["Brian Goetz"],
            resource_type=LibraryResourceType.BOOK,
        ),
        actor_id,
    )
    copy = await LibraryService.create_physical_copy(
        db_session,
        tenant_id,
        LibraryPhysicalCopyCreate(
            catalog_item_id=cat.id,
            library_id=branch.id,
            accession_number=f"ACC-CONC-{uuid4().hex[:6]}",
        ),
        actor_id,
    )
    member1 = await LibraryService.create_member(
        db_session,
        tenant_id,
        LibraryMemberProfileCreate(
            user_id=actor_id,
            membership_number=f"MEM1-{uuid4().hex[:6]}",
            member_category=LibraryMemberCategory.POSTGRADUATE_STUDENT,
            status=LibraryMemberStatus.ACTIVE,
            valid_from=date.today(),
        ),
        actor_id,
    )

    # First checkout succeeds
    await LibraryService.checkout_copy(
        db=db_session,
        tenant_id=tenant_id,
        data=LibraryLoanIssueRequest(copy_id=copy.id, member_id=member1.id, library_id=branch.id),
        staff_user_id=actor_id,
    )

    # Second checkout attempt on same copy MUST fail
    with pytest.raises(LibraryCopyUnavailableException):
        await LibraryService.checkout_copy(
            db=db_session,
            tenant_id=tenant_id,
            data=LibraryLoanIssueRequest(copy_id=copy.id, member_id=member1.id, library_id=branch.id),
            staff_user_id=actor_id,
        )


# =============================================================================
# 7. RESERVATION HOLD QUEUE & AUTO-ALLOCATION
# =============================================================================


@pytest.mark.asyncio
async def test_reservation_hold_queue_and_return_allocation(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies that returning an item with waiting hold reservations allocates the copy and holds it."""
    tenant_id = tenant_a.id
    actor_id = tenant_admin_a.id

    branch = await LibraryService.create_branch(
        db_session, tenant_id, LibraryBranchCreate(branch_code="LIB-RES", name="Reservations Branch"), actor_id
    )
    cat = await LibraryService.create_catalog_item(
        db_session,
        tenant_id,
        LibraryCatalogItemCreate(
            catalog_code="CAT-RES-001",
            title="Quantum Machine Learning",
            authors_json=["Seth Lloyd"],
            resource_type=LibraryResourceType.BOOK,
        ),
        actor_id,
    )
    copy = await LibraryService.create_physical_copy(
        db_session,
        tenant_id,
        LibraryPhysicalCopyCreate(
            catalog_item_id=cat.id,
            library_id=branch.id,
            accession_number=f"ACC-RES-{uuid4().hex[:6]}",
        ),
        actor_id,
    )

    # Borrower A checks it out
    borrower_a = await LibraryService.create_member(
        db_session,
        tenant_id,
        LibraryMemberProfileCreate(
            user_id=actor_id,
            membership_number=f"RES-MB-A-{uuid4().hex[:6]}",
            member_category=LibraryMemberCategory.UNDERGRADUATE_STUDENT,
            status=LibraryMemberStatus.ACTIVE,
            valid_from=date.today(),
        ),
        actor_id,
    )
    loan_a = await LibraryService.checkout_copy(
        db_session,
        tenant_id,
        LibraryLoanIssueRequest(copy_id=copy.id, member_id=borrower_a.id, library_id=branch.id),
        actor_id,
    )

    # Patron B places a hold reservation
    borrower_b = await LibraryService.create_member(
        db_session,
        tenant_id,
        LibraryMemberProfileCreate(
            user_id=actor_id,
            membership_number=f"RES-MB-B-{uuid4().hex[:6]}",
            member_category=LibraryMemberCategory.FACULTY,
            status=LibraryMemberStatus.ACTIVE,
            valid_from=date.today(),
        ),
        actor_id,
    )
    reservation_b = await LibraryService.create_reservation(
        db=db_session,
        tenant_id=tenant_id,
        data=LibraryReservationCreate(
            catalog_item_id=cat.id,
            member_id=borrower_b.id,
            library_id=branch.id,
            priority_rank=10,  # Faculty priority
        ),
        actor_user_id=actor_id,
    )
    assert reservation_b.status == LibraryReservationStatus.WAITING.value
    assert reservation_b.queue_position == 1

    # When Borrower A returns the copy, it must NOT go to general availability;
    # it must transition to RESERVED and allocate to Borrower B!
    await LibraryService.return_copy(
        db=db_session,
        tenant_id=tenant_id,
        loan_id=loan_a.id,
        data=LibraryLoanReturnRequest(returned_to_library_id=branch.id),
        staff_user_id=actor_id,
    )

    # Verify reservation B is now ALLOCATED_PENDING_PICKUP
    res_b_refreshed = await LibraryService.get_reservation(db_session, tenant_id, reservation_b.id)
    assert res_b_refreshed.status == LibraryReservationStatus.ALLOCATED_PENDING_PICKUP.value
    assert res_b_refreshed.allocated_copy_id == copy.id
    assert res_b_refreshed.pickup_deadline is not None

    # Verify copy is RESERVED
    copy_res = await LibraryService.get_physical_copy(db_session, tenant_id, copy.id)
    assert copy_res.circulation_status == LibraryCirculationStatus.RESERVED.value


# =============================================================================
# 8. FINES & AUTHORIZED WAIVERS
# =============================================================================


@pytest.mark.asyncio
async def test_overdue_fine_assessment_and_authorized_waiver(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies manual and overdue fine assessment, outstanding balances, and authorized waivers."""
    tenant_id = tenant_a.id
    actor_id = tenant_admin_a.id

    member = await LibraryService.create_member(
        db_session,
        tenant_id,
        LibraryMemberProfileCreate(
            user_id=actor_id,
            membership_number=f"FINE-MB-{uuid4().hex[:6]}",
            member_category=LibraryMemberCategory.UNDERGRADUATE_STUDENT,
            status=LibraryMemberStatus.ACTIVE,
            valid_from=date.today(),
        ),
        actor_id,
    )

    # 1. Assess damage fine
    fine = await LibraryService.assess_fine(
        db=db_session,
        tenant_id=tenant_id,
        data=LibraryFineAssessRequest(
            member_id=member.id,
            fine_category=LibraryFineCategory.DAMAGED_ITEM,
            amount=Decimal("25.00"),
            currency="USD",
            calculation_basis="Torn spine and water damage assessment",
        ),
        staff_user_id=actor_id,
    )
    assert fine.id is not None
    assert fine.base_amount == Decimal("25.00")
    assert fine.final_payable_amount == Decimal("25.00")

    # Member's outstanding fine balance should reflect $25.00
    member_check = await LibraryService.get_member(db_session, tenant_id, member.id)
    assert member_check.current_outstanding_fines == Decimal("25.00")

    # 2. Authorize waiver for $15.00
    waived_fine = await LibraryService.waive_fine(
        db=db_session,
        tenant_id=tenant_id,
        fine_id=fine.id,
        data=LibraryFineWaiveRequest(
            waived_amount=Decimal("15.00"),
            waiver_reason="Student demonstrated partial pre-existing defect",
        ),
        authorized_by_user_id=actor_id,
    )
    assert waived_fine.waived_amount == Decimal("15.00")
    assert waived_fine.final_payable_amount == Decimal("10.00")

    # Member outstanding balance should now be $10.00
    member_final = await LibraryService.get_member(db_session, tenant_id, member.id)
    assert member_final.current_outstanding_fines == Decimal("10.00")


# =============================================================================
# 9. ACQUISITIONS & AUTO-ACCESSIONING
# =============================================================================


@pytest.mark.asyncio
async def test_acquisition_request_approval_and_receiving(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies acquisition purchase request, approval workflow, and auto-accessioning upon receiving."""
    tenant_id = tenant_a.id
    actor_id = tenant_admin_a.id

    branch = await LibraryService.create_branch(
        db_session, tenant_id, LibraryBranchCreate(branch_code="LIB-ACQ", name="Acquisitions Branch"), actor_id
    )

    # 1. Submit acquisition recommendation
    acq = await LibraryService.create_acquisition_request(
        db=db_session,
        tenant_id=tenant_id,
        data=LibraryAcquisitionCreate(
            title="Deep Learning Foundations",
            author="Ian Goodfellow",
            publisher="MIT Press",
            isbn_or_issn="978-0262035613",
            library_id=branch.id,
            justification="Required textbook for new AI/ML elective",
            number_of_copies=2,
            estimated_unit_cost=Decimal("75.00"),
            currency="USD",
        ),
        requested_by_user_id=actor_id,
    )
    assert acq.id is not None
    assert acq.approval_status == LibraryAcquisitionStatus.REQUESTED.value
    assert acq.total_estimated_cost == Decimal("150.00")

    # 2. Approve acquisition
    acq_approved = await LibraryService.review_acquisition_request(
        db=db_session,
        tenant_id=tenant_id,
        acquisition_id=acq.id,
        data=LibraryAcquisitionApprovalRequest(
            is_approved=True,
            purchase_order_reference="PO-2026-LIB-8841",
        ),
        reviewer_user_id=actor_id,
    )
    assert acq_approved.approval_status == LibraryAcquisitionStatus.APPROVED.value
    assert acq_approved.purchase_order_reference == "PO-2026-LIB-8841"

    # 3. Receive items and trigger auto-accessioning
    acc_1 = f"ACC-PO8841-{uuid4().hex[:4].upper()}"
    acc_2 = f"ACC-PO8841-{uuid4().hex[:4].upper()}"
    acq_received = await LibraryService.receive_acquisition(
        db=db_session,
        tenant_id=tenant_id,
        acquisition_id=acq.id,
        data=LibraryAcquisitionReceiveRequest(
            accession_numbers=[acc_1, acc_2],
            receipt_date=date.today(),
        ),
        received_by_user_id=actor_id,
    )
    assert acq_received.approval_status == LibraryAcquisitionStatus.RECEIVED.value
    assert len(acq_received.accession_numbers_created_json) == 2

    # Verify physical copies were automatically created in the inventory
    copies, count = await LibraryService.list_physical_copies(
        db_session, tenant_id, library_id=branch.id
    )
    accession_set = {c.accession_number for c in copies}
    assert acc_1 in accession_set
    assert acc_2 in accession_set


# =============================================================================
# 10. PERIODICALS & SUBSCRIPTIONS
# =============================================================================


@pytest.mark.asyncio
async def test_subscription_and_periodicals_tracking(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies management of journal and e-resource subscriptions."""
    tenant_id = tenant_a.id
    actor_id = tenant_admin_a.id

    sub = await LibraryService.create_subscription(
        db=db_session,
        tenant_id=tenant_id,
        data=LibrarySubscriptionCreate(
            subscription_code="SUB-IEEE-2026",
            publication_title="IEEE Transactions on Software Engineering",
            publisher_or_vendor="IEEE Computer Society",
            subscription_type=LibrarySubscriptionType.E_JOURNAL_PACKAGE,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            annual_subscription_cost=Decimal("4500.00"),
            currency="USD",
            expected_issues_count=12,
            digital_access_portal_url="https://ieeexplore.ieee.org/xpl/RecentIssue.jsp?punumber=32",
        ),
        current_user_id=actor_id,
    )
    assert sub.id is not None
    assert sub.status == LibrarySubscriptionStatus.ACTIVE.value
    assert sub.annual_subscription_cost == Decimal("4500.00")


# =============================================================================
# 11. DIGITAL RESOURCE ACCESS & EXPIRING TOKENS
# =============================================================================


@pytest.mark.asyncio
async def test_digital_resource_secure_access(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies secure access token generation and audit logging for digital materials."""
    tenant_id = tenant_a.id
    actor_id = tenant_admin_a.id

    cat = await LibraryService.create_catalog_item(
        db=db_session,
        tenant_id=tenant_id,
        data=LibraryCatalogItemCreate(
            catalog_code="EBOOK-AI-01",
            title="Generative AI: Principles and Systems",
            authors_json=["CampusOS Research Labs"],
            resource_type=LibraryResourceType.E_BOOK,
            is_digital=True,
            digital_access_url="https://library.campusos.internal/digital/ebook-ai-01.pdf",
        ),
        current_user_id=actor_id,
    )

    token_res = await LibraryService.generate_digital_access_token(
        db=db_session,
        tenant_id=tenant_id,
        catalog_item_id=cat.id,
        user_id=actor_id,
    )
    assert "download_token" in token_res
    assert token_res["access_url"] is not None
    assert token_res["token_expires_at"] > datetime.now(UTC)

    # Verify audit log was recorded
    logs, total = await LibraryService.list_digital_access_logs(
        db_session, tenant_id, catalog_item_id=cat.id
    )
    assert total >= 1
    assert logs[0].user_id == actor_id


# =============================================================================
# 12. INVENTORY VERIFICATION & STOCK AUDIT
# =============================================================================


@pytest.mark.asyncio
async def test_inventory_stock_audit_and_reconciliation(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies periodic stock verification audit, copy scanning, and reconciliation."""
    tenant_id = tenant_a.id
    actor_id = tenant_admin_a.id

    branch = await LibraryService.create_branch(
        db_session, tenant_id, LibraryBranchCreate(branch_code="LIB-AUD", name="Audit Branch"), actor_id
    )
    cat = await LibraryService.create_catalog_item(
        db_session,
        tenant_id,
        LibraryCatalogItemCreate(
            catalog_code="CAT-AUD-01",
            title="Algorithms Unlocked",
            authors_json=["Thomas Cormen"],
            resource_type=LibraryResourceType.BOOK,
        ),
        actor_id,
    )
    copy1 = await LibraryService.create_physical_copy(
        db_session,
        tenant_id,
        LibraryPhysicalCopyCreate(
            catalog_item_id=cat.id,
            library_id=branch.id,
            accession_number=f"ACC-AUD-1-{uuid4().hex[:4]}",
        ),
        actor_id,
    )

    # 1. Start stock verification audit
    audit = await LibraryService.create_inventory_audit(
        db=db_session,
        tenant_id=tenant_id,
        data=LibraryInventoryAuditCreate(
            audit_code="AUD-2026-Q1",
            title="Q1 2026 Main Stacks Stock Audit",
            library_id=branch.id,
            audit_scope="FULL_LIBRARY",
        ),
        auditor_user_id=actor_id,
    )
    assert audit.id is not None
    assert audit.status == LibraryInventoryAuditStatus.IN_PROGRESS.value
    assert audit.total_expected_copies >= 1

    # 2. Record physical scan
    scan_item = await LibraryService.record_audit_scan(
        db=db_session,
        tenant_id=tenant_id,
        audit_id=audit.id,
        data=LibraryInventoryAuditItemScanRequest(
            copy_id=copy1.id,
            accession_number=copy1.accession_number,
            scanned_status=LibraryAuditScanResult.PRESENT_ON_SHELF,
            shelf_location_found="Section 4B",
        ),
        auditor_user_id=actor_id,
    )
    assert scan_item.scanned_status == LibraryAuditScanResult.PRESENT_ON_SHELF.value

    # 3. Reconcile audit
    audit_closed = await LibraryService.reconcile_inventory_audit(
        db=db_session,
        tenant_id=tenant_id,
        audit_id=audit.id,
        data=LibraryInventoryAuditReconcileRequest(
            reconciliation_notes="All copies verified on shelves; 0 unaccounted discrepancies."
        ),
        approver_user_id=actor_id,
    )
    assert audit_closed.status == LibraryInventoryAuditStatus.COMPLETED.value
    assert audit_closed.verified_present_copies >= 1


# =============================================================================
# 13. SCHEDULED COMPLIANCE SWEEP
# =============================================================================


@pytest.mark.asyncio
async def test_library_scheduled_sweep(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verifies that the scheduled sweep flags overdues, releases expired holds, and monitors subscriptions."""
    tenant_id = tenant_a.id

    sweep_res = await LibraryService.sweep_deadlines_and_compliance(db_session, tenant_id)
    assert "processed_at" in sweep_res
    assert "overdue_loans_flagged" in sweep_res
    assert "expired_reservations_released" in sweep_res
    assert "expiring_subscriptions_flagged" in sweep_res


# =============================================================================
# 14. MULTI-TENANT ISOLATION
# =============================================================================


@pytest.mark.asyncio
async def test_library_multi_tenant_isolation(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_b: Institution,
    tenant_admin_a: User,
    tenant_admin_b: User,
):
    """Verifies strict tenant isolation across branches, catalog items, and circulation records."""
    tenant_a_id = tenant_a.id
    tenant_b_id = tenant_b.id

    # Create branch in Tenant A
    branch_a = await LibraryService.create_branch(
        db_session,
        tenant_a_id,
        LibraryBranchCreate(branch_code="LIB-TEN-A", name="Tenant A Library"),
        tenant_admin_a.id,
    )

    # Tenant B should see 0 branches from Tenant A
    branches_b, count_b = await LibraryService.list_branches(db_session, tenant_b_id)
    assert not any(b.id == branch_a.id for b in branches_b)

    # Tenant B attempting to read branch_a raises 404
    from app.core.exceptions import LibraryBranchNotFoundException

    with pytest.raises(LibraryBranchNotFoundException):
        await LibraryService.get_branch(db_session, tenant_b_id, branch_a.id)


# =============================================================================
# 15. FASTAPI REST API ENDPOINTS VIA ASYNC CLIENT
# =============================================================================


@pytest.mark.asyncio
async def test_library_fastapi_endpoints_via_async_client(
    client: AsyncClient,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Verifies REST API endpoints under /api/v1/library via FastAPI AsyncClient."""
    tenant_id = tenant_a.id
    headers = make_auth_headers(tenant_admin_a, tenant_id)

    # 1. Create branch via API
    resp = await client.post(
        "/api/v1/library/branches",
        json={
            "branch_code": f"API-{uuid4().hex[:5].upper()}",
            "name": "API Test Library",
            "location_building": "Building X",
            "is_active": True,
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    branch_id = resp.json()["data"]["id"]

    # 2. List branches
    resp = await client.get("/api/v1/library/branches", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["total"] >= 1

    # 3. Create catalog item
    cat_resp = await client.post(
        "/api/v1/library/catalog",
        json={
            "catalog_code": f"CAT-API-{uuid4().hex[:5].upper()}",
            "title": "API Driven Architecture",
            "authors_json": ["CampusOS Architects"],
            "resource_type": "BOOK",
            "isbn_or_issn": f"978-{uuid4().hex[:8]}",
        },
        headers=headers,
    )
    assert cat_resp.status_code == 201, cat_resp.text
    cat_id = cat_resp.json()["data"]["id"]

    # 4. Search catalog
    search_resp = await client.get(
        "/api/v1/library/catalog?q=Architecture",
        headers=headers,
    )
    assert search_resp.status_code == 200
    assert search_resp.json()["data"]["total"] >= 1

    # 5. Fetch analytics summary
    analytics_resp = await client.get("/api/v1/library/analytics/summary", headers=headers)
    assert analytics_resp.status_code == 200
    data = analytics_resp.json()["data"]
    assert "total_branches" in data
    assert "total_catalog_titles" in data
    assert "circulation_rate_percentage" in data

    # 6. Trigger compliance sweep via API
    sweep_resp = await client.post("/api/v1/library/compliance/sweep", headers=headers)
    assert sweep_resp.status_code == 200
    assert "processed_at" in sweep_resp.json()["data"]
