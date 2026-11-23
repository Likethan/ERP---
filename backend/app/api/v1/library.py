"""Enterprise Institutional Library, Learning Resources & Knowledge Access Management API Router (Step 45)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_current_user, get_tenant_context, require_permission
from app.core.permissions import (
    LIBRARY_ACQUISITIONS_MANAGE_DOT,
    LIBRARY_ACQUISITIONS_REQUEST_DOT,
    LIBRARY_ANALYTICS_READ_DOT,
    LIBRARY_AUDIT_MANAGE_DOT,
    LIBRARY_BRANCHES_MANAGE_DOT,
    LIBRARY_CATALOG_MANAGE_DOT,
    LIBRARY_CATALOG_READ_DOT,
    LIBRARY_CIRCULATION_ISSUE_DOT,
    LIBRARY_COPIES_MANAGE_DOT,
    LIBRARY_DIGITAL_ACCESS_DOT,
    LIBRARY_FINES_MANAGE_DOT,
    LIBRARY_FINES_WAIVE_DOT,
    LIBRARY_MEMBERS_MANAGE_DOT,
    LIBRARY_MEMBERS_READ_DOT,
    LIBRARY_SUBSCRIPTIONS_MANAGE_DOT,
)
from app.core.tenant import TenantContext
from app.models.library import (
    LibraryAcquisitionStatus,
    LibraryBranchStatus,
    LibraryCatalogStatus,
    LibraryCirculationStatus,
    LibraryCopyCondition,
    LibraryFineStatus,
    LibraryInventoryAuditStatus,
    LibraryLoanStatus,
    LibraryMemberCategory,
    LibraryMemberStatus,
    LibraryReservationStatus,
    LibraryResourceType,
    LibrarySubscriptionStatus,
)
from app.models.people import User
from app.schemas.common import ApiResponse
from app.schemas.library import (
    LibraryAcquisitionReceiveRequest,
    LibraryAcquisitionRequestCreate,
    LibraryAcquisitionRequestListResponse,
    LibraryAcquisitionRequestResponse,
    LibraryAcquisitionReviewRequest,
    LibraryAnalyticsSummaryResponse,
    LibraryBranchCreate,
    LibraryBranchListResponse,
    LibraryBranchResponse,
    LibraryBranchUpdate,
    LibraryCatalogItemCreate,
    LibraryCatalogItemListResponse,
    LibraryCatalogItemResponse,
    LibraryCatalogItemUpdate,
    LibraryCirculationLoanListResponse,
    LibraryCirculationLoanResponse,
    LibraryDeadlineSweepResponse,
    LibraryDigitalAccessTokenResponse,
    LibraryDigitalResourceAccessListResponse,
    LibraryDigitalResourceAccessLogResponse,
    LibraryFineManualAssessmentRequest,
    LibraryFinePostToFinanceRequest,
    LibraryFineRecordListResponse,
    LibraryFineRecordResponse,
    LibraryFineWaiverRequest,
    LibraryInventoryAuditCreate,
    LibraryInventoryAuditItemResponse,
    LibraryInventoryAuditListResponse,
    LibraryInventoryAuditReconcileRequest,
    LibraryInventoryAuditResponse,
    LibraryInventoryAuditScanRecordRequest,
    LibraryLendingPolicyCreate,
    LibraryLendingPolicyListResponse,
    LibraryLendingPolicyResponse,
    LibraryLendingPolicyUpdate,
    LibraryLoanCheckoutRequest,
    LibraryLoanRenewRequest,
    LibraryLoanReturnRequest,
    LibraryMemberProfileCreate,
    LibraryMemberProfileListResponse,
    LibraryMemberProfileResponse,
    LibraryMemberProfileUpdate,
    LibraryPhysicalCopyCreate,
    LibraryPhysicalCopyListResponse,
    LibraryPhysicalCopyResponse,
    LibraryPhysicalCopyUpdate,
    LibraryReservationCancelRequest,
    LibraryReservationCreate,
    LibraryReservationListResponse,
    LibraryReservationResponse,
    LibrarySubscriptionCreate,
    LibrarySubscriptionListResponse,
    LibrarySubscriptionResponse,
    LibrarySubscriptionUpdate,
)
from app.services.library_service import LibraryService

library_router = APIRouter(prefix="/library", tags=["library"])


# =============================================================================
# 1. LIBRARY BRANCHES
# =============================================================================


@library_router.post(
    "/branches",
    response_model=ApiResponse[LibraryBranchResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(LIBRARY_BRANCHES_MANAGE_DOT))],
)
async def create_branch(
    data: LibraryBranchCreate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[LibraryBranchResponse]:
    """Create a new institutional library branch."""
    branch = await LibraryService.create_branch(
        db, tenant_ctx.tenant_id, data, current_user.id
    )
    return ApiResponse(data=LibraryBranchResponse.model_validate(branch))


@library_router.get(
    "/branches",
    response_model=ApiResponse[LibraryBranchListResponse],
    dependencies=[Depends(require_permission(LIBRARY_CATALOG_READ_DOT))],
)
async def list_branches(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    campus_id: UUID | None = Query(None),
    status_filter: LibraryBranchStatus | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> ApiResponse[LibraryBranchListResponse]:
    """List library branches within the tenant."""
    items, total = await LibraryService.list_branches(
        db,
        tenant_ctx.tenant_id,
        campus_id=campus_id,
        status_filter=status_filter.value if status_filter else None,
        skip=skip,
        limit=limit,
    )
    return ApiResponse(
        data=LibraryBranchListResponse(
            items=[LibraryBranchResponse.model_validate(i) for i in items],
            total=total,
        )
    )


@library_router.get(
    "/branches/{branch_id}",
    response_model=ApiResponse[LibraryBranchResponse],
    dependencies=[Depends(require_permission(LIBRARY_CATALOG_READ_DOT))],
)
async def get_branch(
    branch_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
) -> ApiResponse[LibraryBranchResponse]:
    """Get single library branch details."""
    branch = await LibraryService.get_branch(db, tenant_ctx.tenant_id, branch_id)
    return ApiResponse(data=LibraryBranchResponse.model_validate(branch))


@library_router.put(
    "/branches/{branch_id}",
    response_model=ApiResponse[LibraryBranchResponse],
    dependencies=[Depends(require_permission(LIBRARY_BRANCHES_MANAGE_DOT))],
)
async def update_branch(
    branch_id: UUID,
    data: LibraryBranchUpdate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[LibraryBranchResponse]:
    """Update library branch configuration."""
    branch = await LibraryService.update_branch(
        db, tenant_ctx.tenant_id, branch_id, data, current_user.id
    )
    return ApiResponse(data=LibraryBranchResponse.model_validate(branch))


# =============================================================================
# 2. LENDING POLICIES
# =============================================================================


@library_router.post(
    "/policies",
    response_model=ApiResponse[LibraryLendingPolicyResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(LIBRARY_BRANCHES_MANAGE_DOT))],
)
async def create_lending_policy(
    data: LibraryLendingPolicyCreate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[LibraryLendingPolicyResponse]:
    """Create a new library circulation and lending policy rule."""
    policy = await LibraryService.create_policy(
        db, tenant_ctx.tenant_id, data, current_user.id
    )
    return ApiResponse(data=LibraryLendingPolicyResponse.model_validate(policy))


@library_router.get(
    "/policies",
    response_model=ApiResponse[LibraryLendingPolicyListResponse],
    dependencies=[Depends(require_permission(LIBRARY_CATALOG_READ_DOT))],
)
async def list_lending_policies(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    library_id: UUID | None = Query(None),
    member_category: LibraryMemberCategory | None = Query(None),
    resource_type: LibraryResourceType | None = Query(None),
) -> ApiResponse[LibraryLendingPolicyListResponse]:
    """List configured library lending policies."""
    items = await LibraryService.list_policies(
        db,
        tenant_ctx.tenant_id,
        library_id=library_id,
        member_category=member_category.value if member_category else None,
        resource_type=resource_type.value if resource_type else None,
    )
    return ApiResponse(
        data=LibraryLendingPolicyListResponse(
            items=[LibraryLendingPolicyResponse.model_validate(p) for p in items],
            total=len(items),
        )
    )


@library_router.put(
    "/policies/{policy_id}",
    response_model=ApiResponse[LibraryLendingPolicyResponse],
    dependencies=[Depends(require_permission(LIBRARY_BRANCHES_MANAGE_DOT))],
)
async def update_lending_policy(
    policy_id: UUID,
    data: LibraryLendingPolicyUpdate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[LibraryLendingPolicyResponse]:
    """Update a lending policy configuration."""
    policy = await LibraryService.update_policy(
        db, tenant_ctx.tenant_id, policy_id, data, current_user.id
    )
    return ApiResponse(data=LibraryLendingPolicyResponse.model_validate(policy))


# =============================================================================
# 3. RESOURCE CATALOG & BIBLIOGRAPHIC RECORDS
# =============================================================================


@library_router.post(
    "/catalog",
    response_model=ApiResponse[LibraryCatalogItemResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(LIBRARY_CATALOG_MANAGE_DOT))],
)
async def create_catalog_item(
    data: LibraryCatalogItemCreate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[LibraryCatalogItemResponse]:
    """Create a new bibliographic catalog resource record with duplicate detection."""
    item = await LibraryService.create_catalog_item(
        db, tenant_ctx.tenant_id, data, current_user.id
    )
    return ApiResponse(data=LibraryCatalogItemResponse.model_validate(item))


@library_router.get(
    "/catalog",
    response_model=ApiResponse[LibraryCatalogItemListResponse],
    dependencies=[Depends(require_permission(LIBRARY_CATALOG_READ_DOT))],
)
async def search_catalog(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    q: str | None = Query(None, description="Search query across title, authors, ISBN, subject"),
    resource_type: LibraryResourceType | None = Query(None),
    status_filter: LibraryCatalogStatus | None = Query(None, alias="status"),
    is_digital: bool | None = Query(None),
    primary_language: str | None = Query(None),
    subject_classification: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> ApiResponse[LibraryCatalogItemListResponse]:
    """Search and filter institutional resource catalog."""
    items, total = await LibraryService.list_catalog_items(
        db,
        tenant_ctx.tenant_id,
        q=q,
        resource_type=resource_type.value if resource_type else None,
        status_filter=status_filter.value if status_filter else None,
        is_digital=is_digital,
        primary_language=primary_language,
        subject_classification=subject_classification,
        skip=skip,
        limit=limit,
    )
    return ApiResponse(
        data=LibraryCatalogItemListResponse(
            items=[LibraryCatalogItemResponse.model_validate(i) for i in items],
            total=total,
        )
    )


@library_router.get(
    "/catalog/{item_id}",
    response_model=ApiResponse[LibraryCatalogItemResponse],
    dependencies=[Depends(require_permission(LIBRARY_CATALOG_READ_DOT))],
)
async def get_catalog_item(
    item_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
) -> ApiResponse[LibraryCatalogItemResponse]:
    """Get single catalog item metadata."""
    item = await LibraryService.get_catalog_item(db, tenant_ctx.tenant_id, item_id)
    return ApiResponse(data=LibraryCatalogItemResponse.model_validate(item))


@library_router.put(
    "/catalog/{item_id}",
    response_model=ApiResponse[LibraryCatalogItemResponse],
    dependencies=[Depends(require_permission(LIBRARY_CATALOG_MANAGE_DOT))],
)
async def update_catalog_item(
    item_id: UUID,
    data: LibraryCatalogItemUpdate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[LibraryCatalogItemResponse]:
    """Update catalog item metadata."""
    item = await LibraryService.update_catalog_item(
        db, tenant_ctx.tenant_id, item_id, data, current_user.id
    )
    return ApiResponse(data=LibraryCatalogItemResponse.model_validate(item))


# =============================================================================
# 4. PHYSICAL INVENTORY & COPIES
# =============================================================================


@library_router.post(
    "/copies",
    response_model=ApiResponse[LibraryPhysicalCopyResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(LIBRARY_COPIES_MANAGE_DOT))],
)
async def create_physical_copy(
    data: LibraryPhysicalCopyCreate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[LibraryPhysicalCopyResponse]:
    """Register a new physical copy with accession uniqueness verification."""
    copy = await LibraryService.create_physical_copy(
        db, tenant_ctx.tenant_id, data, current_user.id
    )
    return ApiResponse(data=LibraryPhysicalCopyResponse.model_validate(copy))


@library_router.get(
    "/copies",
    response_model=ApiResponse[LibraryPhysicalCopyListResponse],
    dependencies=[Depends(require_permission(LIBRARY_CATALOG_READ_DOT))],
)
async def list_physical_copies(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    catalog_item_id: UUID | None = Query(None),
    library_id: UUID | None = Query(None),
    circulation_status: LibraryCirculationStatus | None = Query(None),
    condition_grade: LibraryCopyCondition | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> ApiResponse[LibraryPhysicalCopyListResponse]:
    """List physical copies by catalog item, library branch, or availability."""
    items, total = await LibraryService.list_physical_copies(
        db,
        tenant_ctx.tenant_id,
        catalog_item_id=catalog_item_id,
        library_id=library_id,
        circulation_status=circulation_status.value if circulation_status else None,
        condition_grade=condition_grade.value if condition_grade else None,
        skip=skip,
        limit=limit,
    )
    return ApiResponse(
        data=LibraryPhysicalCopyListResponse(
            items=[LibraryPhysicalCopyResponse.model_validate(c) for c in items],
            total=total,
        )
    )


@library_router.get(
    "/copies/{copy_id}",
    response_model=ApiResponse[LibraryPhysicalCopyResponse],
    dependencies=[Depends(require_permission(LIBRARY_CATALOG_READ_DOT))],
)
async def get_physical_copy(
    copy_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
) -> ApiResponse[LibraryPhysicalCopyResponse]:
    """Get single physical copy inventory details."""
    copy = await LibraryService.get_physical_copy(db, tenant_ctx.tenant_id, copy_id)
    return ApiResponse(data=LibraryPhysicalCopyResponse.model_validate(copy))


@library_router.put(
    "/copies/{copy_id}",
    response_model=ApiResponse[LibraryPhysicalCopyResponse],
    dependencies=[Depends(require_permission(LIBRARY_COPIES_MANAGE_DOT))],
)
async def update_physical_copy(
    copy_id: UUID,
    data: LibraryPhysicalCopyUpdate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[LibraryPhysicalCopyResponse]:
    """Update physical copy status, location, or condition grade."""
    copy = await LibraryService.update_physical_copy(
        db, tenant_ctx.tenant_id, copy_id, data, current_user.id
    )
    return ApiResponse(data=LibraryPhysicalCopyResponse.model_validate(copy))


# =============================================================================
# 5. MEMBER PROFILES & ELIGIBILITY
# =============================================================================


@library_router.post(
    "/members",
    response_model=ApiResponse[LibraryMemberProfileResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(LIBRARY_MEMBERS_MANAGE_DOT))],
)
async def create_member(
    data: LibraryMemberProfileCreate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[LibraryMemberProfileResponse]:
    """Register or activate a library membership profile for a user."""
    member = await LibraryService.create_member(
        db, tenant_ctx.tenant_id, data, current_user.id
    )
    return ApiResponse(data=LibraryMemberProfileResponse.model_validate(member))


@library_router.get(
    "/members",
    response_model=ApiResponse[LibraryMemberProfileListResponse],
    dependencies=[Depends(require_permission(LIBRARY_MEMBERS_READ_DOT))],
)
async def list_members(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    q: str | None = Query(None, description="Search membership card number"),
    member_category: LibraryMemberCategory | None = Query(None),
    status_filter: LibraryMemberStatus | None = Query(None, alias="status"),
    home_library_id: UUID | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> ApiResponse[LibraryMemberProfileListResponse]:
    """List library membership records with search and status filtering."""
    items, total = await LibraryService.list_members(
        db,
        tenant_ctx.tenant_id,
        q=q,
        member_category=member_category.value if member_category else None,
        status_filter=status_filter.value if status_filter else None,
        home_library_id=home_library_id,
        skip=skip,
        limit=limit,
    )
    return ApiResponse(
        data=LibraryMemberProfileListResponse(
            items=[LibraryMemberProfileResponse.model_validate(m) for m in items],
            total=total,
        )
    )


@library_router.get(
    "/members/me",
    response_model=ApiResponse[LibraryMemberProfileResponse | None],
)
async def get_my_member_profile(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[LibraryMemberProfileResponse | None]:
    """Get the authenticated caller's library membership profile."""
    member = await LibraryService.get_member_by_user_id(
        db, tenant_ctx.tenant_id, current_user.id
    )
    return ApiResponse(
        data=LibraryMemberProfileResponse.model_validate(member) if member else None
    )


@library_router.get(
    "/members/{member_id}",
    response_model=ApiResponse[LibraryMemberProfileResponse],
    dependencies=[Depends(require_permission(LIBRARY_MEMBERS_READ_DOT))],
)
async def get_member(
    member_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
) -> ApiResponse[LibraryMemberProfileResponse]:
    """Get single library member profile."""
    member = await LibraryService.get_member(db, tenant_ctx.tenant_id, member_id)
    return ApiResponse(data=LibraryMemberProfileResponse.model_validate(member))


@library_router.put(
    "/members/{member_id}",
    response_model=ApiResponse[LibraryMemberProfileResponse],
    dependencies=[Depends(require_permission(LIBRARY_MEMBERS_MANAGE_DOT))],
)
async def update_member(
    member_id: UUID,
    data: LibraryMemberProfileUpdate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[LibraryMemberProfileResponse]:
    """Update library member category, borrowing privilege, or status."""
    member = await LibraryService.update_member(
        db, tenant_ctx.tenant_id, member_id, data, current_user.id
    )
    return ApiResponse(data=LibraryMemberProfileResponse.model_validate(member))


# =============================================================================
# 6. CIRCULATION & LENDING
# =============================================================================


@library_router.post(
    "/circulation/checkout",
    response_model=ApiResponse[LibraryCirculationLoanResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(LIBRARY_CIRCULATION_ISSUE_DOT))],
)
async def checkout_loan(
    data: LibraryLoanCheckoutRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[LibraryCirculationLoanResponse]:
    """Issue/checkout a physical copy to a verified library member."""
    loan = await LibraryService.checkout_copy(
        db, tenant_ctx.tenant_id, data, current_user.id
    )
    return ApiResponse(data=LibraryCirculationLoanResponse.model_validate(loan))


@library_router.post(
    "/circulation/loans/{loan_id}/return",
    response_model=ApiResponse[LibraryCirculationLoanResponse],
    dependencies=[Depends(require_permission(LIBRARY_CIRCULATION_ISSUE_DOT))],
)
async def return_loan(
    loan_id: UUID,
    data: LibraryLoanReturnRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[LibraryCirculationLoanResponse]:
    """Check-in/return an issued copy, assess overdue fines, and trigger reservation queue."""
    loan = await LibraryService.return_copy(
        db, tenant_ctx.tenant_id, loan_id, data, current_user.id
    )
    return ApiResponse(data=LibraryCirculationLoanResponse.model_validate(loan))


@library_router.post(
    "/circulation/loans/{loan_id}/renew",
    response_model=ApiResponse[LibraryCirculationLoanResponse],
)
async def renew_loan(
    loan_id: UUID,
    data: LibraryLoanRenewRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[LibraryCirculationLoanResponse]:
    """Renew an active loan if within renewal policy limits and no hold requests."""
    # Validate permission: either circulation operator or self-renew
    loan = await LibraryService.renew_loan(
        db, tenant_ctx.tenant_id, loan_id, data, current_user.id
    )
    return ApiResponse(data=LibraryCirculationLoanResponse.model_validate(loan))


@library_router.get(
    "/circulation/loans",
    response_model=ApiResponse[LibraryCirculationLoanListResponse],
    dependencies=[Depends(require_permission(LIBRARY_CIRCULATION_ISSUE_DOT))],
)
async def list_loans(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    member_id: UUID | None = Query(None),
    copy_id: UUID | None = Query(None),
    library_id: UUID | None = Query(None),
    status_filter: LibraryLoanStatus | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> ApiResponse[LibraryCirculationLoanListResponse]:
    """List circulation loans with filtering by member, copy, library, and status."""
    items, total = await LibraryService.list_loans(
        db,
        tenant_ctx.tenant_id,
        member_id=member_id,
        copy_id=copy_id,
        library_id=library_id,
        status_filter=status_filter.value if status_filter else None,
        skip=skip,
        limit=limit,
    )
    return ApiResponse(
        data=LibraryCirculationLoanListResponse(
            items=[LibraryCirculationLoanResponse.model_validate(l) for l in items],
            total=total,
        )
    )


@library_router.get(
    "/circulation/my-loans",
    response_model=ApiResponse[LibraryCirculationLoanListResponse],
)
async def list_my_loans(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    status_filter: LibraryLoanStatus | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> ApiResponse[LibraryCirculationLoanListResponse]:
    """List authenticated caller's active and historical loans."""
    items, total = await LibraryService.list_my_loans(
        db,
        tenant_ctx.tenant_id,
        current_user.id,
        status_filter=status_filter.value if status_filter else None,
        skip=skip,
        limit=limit,
    )
    return ApiResponse(
        data=LibraryCirculationLoanListResponse(
            items=[LibraryCirculationLoanResponse.model_validate(l) for l in items],
            total=total,
        )
    )


@library_router.get(
    "/circulation/loans/{loan_id}",
    response_model=ApiResponse[LibraryCirculationLoanResponse],
    dependencies=[Depends(require_permission(LIBRARY_CIRCULATION_ISSUE_DOT))],
)
async def get_loan(
    loan_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
) -> ApiResponse[LibraryCirculationLoanResponse]:
    """Get single loan transaction details."""
    loan = await LibraryService.get_loan(db, tenant_ctx.tenant_id, loan_id)
    return ApiResponse(data=LibraryCirculationLoanResponse.model_validate(loan))


# =============================================================================
# 7. RESERVATIONS & HOLD QUEUE
# =============================================================================


@library_router.post(
    "/reservations",
    response_model=ApiResponse[LibraryReservationResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_reservation(
    data: LibraryReservationCreate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[LibraryReservationResponse]:
    """Place a hold reservation on a catalog resource or physical copy."""
    reservation = await LibraryService.create_reservation(
        db, tenant_ctx.tenant_id, data, current_user.id
    )
    return ApiResponse(data=LibraryReservationResponse.model_validate(reservation))


@library_router.get(
    "/reservations",
    response_model=ApiResponse[LibraryReservationListResponse],
    dependencies=[Depends(require_permission(LIBRARY_CIRCULATION_ISSUE_DOT))],
)
async def list_reservations(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    catalog_item_id: UUID | None = Query(None),
    member_id: UUID | None = Query(None),
    library_id: UUID | None = Query(None),
    status_filter: LibraryReservationStatus | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> ApiResponse[LibraryReservationListResponse]:
    """List reservations with priority ordering and queue position."""
    items, total = await LibraryService.list_reservations(
        db,
        tenant_ctx.tenant_id,
        catalog_item_id=catalog_item_id,
        member_id=member_id,
        library_id=library_id,
        status_filter=status_filter.value if status_filter else None,
        skip=skip,
        limit=limit,
    )
    return ApiResponse(
        data=LibraryReservationListResponse(
            items=[LibraryReservationResponse.model_validate(r) for r in items],
            total=total,
        )
    )


@library_router.get(
    "/reservations/my-reservations",
    response_model=ApiResponse[LibraryReservationListResponse],
)
async def list_my_reservations(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    status_filter: LibraryReservationStatus | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> ApiResponse[LibraryReservationListResponse]:
    """List authenticated user's hold reservations."""
    items, total = await LibraryService.list_my_reservations(
        db,
        tenant_ctx.tenant_id,
        current_user.id,
        status_filter=status_filter.value if status_filter else None,
        skip=skip,
        limit=limit,
    )
    return ApiResponse(
        data=LibraryReservationListResponse(
            items=[LibraryReservationResponse.model_validate(r) for r in items],
            total=total,
        )
    )


@library_router.post(
    "/reservations/{reservation_id}/cancel",
    response_model=ApiResponse[LibraryReservationResponse],
)
async def cancel_reservation(
    reservation_id: UUID,
    data: LibraryReservationCancelRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[LibraryReservationResponse]:
    """Cancel a hold reservation and release allocated copy if held."""
    reservation = await LibraryService.cancel_reservation(
        db, tenant_ctx.tenant_id, reservation_id, data, current_user.id
    )
    return ApiResponse(data=LibraryReservationResponse.model_validate(reservation))


# =============================================================================
# 8. FINES & OBLIGATIONS
# =============================================================================


@library_router.post(
    "/fines",
    response_model=ApiResponse[LibraryFineRecordResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(LIBRARY_FINES_MANAGE_DOT))],
)
async def assess_fine(
    data: LibraryFineManualAssessmentRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[LibraryFineRecordResponse]:
    """Assess a fine (lost item, damage, or overdue fee) on a member."""
    fine = await LibraryService.assess_fine(
        db, tenant_ctx.tenant_id, data, current_user.id
    )
    return ApiResponse(data=LibraryFineRecordResponse.model_validate(fine))


@library_router.get(
    "/fines",
    response_model=ApiResponse[LibraryFineRecordListResponse],
    dependencies=[Depends(require_permission(LIBRARY_FINES_MANAGE_DOT))],
)
async def list_fines(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    member_id: UUID | None = Query(None),
    status_filter: LibraryFineStatus | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> ApiResponse[LibraryFineRecordListResponse]:
    """List library fine assessments and balances."""
    items, total = await LibraryService.list_fines(
        db,
        tenant_ctx.tenant_id,
        member_id=member_id,
        status_filter=status_filter.value if status_filter else None,
        skip=skip,
        limit=limit,
    )
    return ApiResponse(
        data=LibraryFineRecordListResponse(
            items=[LibraryFineRecordResponse.model_validate(f) for f in items],
            total=total,
        )
    )


@library_router.get(
    "/fines/my-fines",
    response_model=ApiResponse[LibraryFineRecordListResponse],
)
async def list_my_fines(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    status_filter: LibraryFineStatus | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> ApiResponse[LibraryFineRecordListResponse]:
    """List authenticated user's fines and obligations."""
    items, total = await LibraryService.list_my_fines(
        db,
        tenant_ctx.tenant_id,
        current_user.id,
        status_filter=status_filter.value if status_filter else None,
        skip=skip,
        limit=limit,
    )
    return ApiResponse(
        data=LibraryFineRecordListResponse(
            items=[LibraryFineRecordResponse.model_validate(f) for f in items],
            total=total,
        )
    )


@library_router.post(
    "/fines/{fine_id}/waive",
    response_model=ApiResponse[LibraryFineRecordResponse],
    dependencies=[Depends(require_permission(LIBRARY_FINES_WAIVE_DOT))],
)
async def waive_fine(
    fine_id: UUID,
    data: LibraryFineWaiverRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[LibraryFineRecordResponse]:
    """Waive part or all of a library fine with auditable justification."""
    fine = await LibraryService.waive_fine(
        db, tenant_ctx.tenant_id, fine_id, data, current_user.id
    )
    return ApiResponse(data=LibraryFineRecordResponse.model_validate(fine))


@library_router.post(
    "/fines/{fine_id}/post-to-finance",
    response_model=ApiResponse[LibraryFineRecordResponse],
    dependencies=[Depends(require_permission(LIBRARY_FINES_MANAGE_DOT))],
)
async def post_fine_to_finance(
    fine_id: UUID,
    data: LibraryFinePostToFinanceRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[LibraryFineRecordResponse]:
    """Post an assessed library fine to authoritative Finance module invoice."""
    fine = await LibraryService.post_fine_to_finance(
        db, tenant_ctx.tenant_id, fine_id, data, current_user.id
    )
    return ApiResponse(data=LibraryFineRecordResponse.model_validate(fine))


# =============================================================================
# 9. ACQUISITIONS & PROCUREMENT
# =============================================================================


@library_router.post(
    "/acquisitions",
    response_model=ApiResponse[LibraryAcquisitionRequestResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(LIBRARY_ACQUISITIONS_REQUEST_DOT))],
)
async def create_acquisition_request(
    data: LibraryAcquisitionRequestCreate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[LibraryAcquisitionRequestResponse]:
    """Submit a new library book/resource acquisition purchase request."""
    acq = await LibraryService.create_acquisition_request(
        db, tenant_ctx.tenant_id, data, current_user.id
    )
    return ApiResponse(data=LibraryAcquisitionRequestResponse.model_validate(acq))


@library_router.get(
    "/acquisitions",
    response_model=ApiResponse[LibraryAcquisitionRequestListResponse],
    dependencies=[Depends(require_permission(LIBRARY_ACQUISITIONS_REQUEST_DOT))],
)
async def list_acquisitions(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    library_id: UUID | None = Query(None),
    status_filter: LibraryAcquisitionStatus | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> ApiResponse[LibraryAcquisitionRequestListResponse]:
    """List acquisition requests and procurement statuses."""
    items, total = await LibraryService.list_acquisition_requests(
        db,
        tenant_ctx.tenant_id,
        library_id=library_id,
        status_filter=status_filter.value if status_filter else None,
        skip=skip,
        limit=limit,
    )
    return ApiResponse(
        data=LibraryAcquisitionRequestListResponse(
            items=[LibraryAcquisitionRequestResponse.model_validate(a) for a in items],
            total=total,
        )
    )


@library_router.post(
    "/acquisitions/{acquisition_id}/review",
    response_model=ApiResponse[LibraryAcquisitionRequestResponse],
    dependencies=[Depends(require_permission(LIBRARY_ACQUISITIONS_MANAGE_DOT))],
)
async def review_acquisition(
    acquisition_id: UUID,
    data: LibraryAcquisitionReviewRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[LibraryAcquisitionRequestResponse]:
    """Approve or reject an acquisition request."""
    acq = await LibraryService.review_acquisition_request(
        db, tenant_ctx.tenant_id, acquisition_id, data, current_user.id
    )
    return ApiResponse(data=LibraryAcquisitionRequestResponse.model_validate(acq))


@library_router.post(
    "/acquisitions/{acquisition_id}/receive",
    response_model=ApiResponse[LibraryAcquisitionRequestResponse],
    dependencies=[Depends(require_permission(LIBRARY_ACQUISITIONS_MANAGE_DOT))],
)
async def receive_acquisition(
    acquisition_id: UUID,
    data: LibraryAcquisitionReceiveRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[LibraryAcquisitionRequestResponse]:
    """Record receipt of ordered copies and trigger automatic accessioning."""
    acq = await LibraryService.receive_acquisition(
        db, tenant_ctx.tenant_id, acquisition_id, data, current_user.id
    )
    return ApiResponse(data=LibraryAcquisitionRequestResponse.model_validate(acq))


# =============================================================================
# 10. PERIODICALS & SUBSCRIPTIONS
# =============================================================================


@library_router.post(
    "/subscriptions",
    response_model=ApiResponse[LibrarySubscriptionResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(LIBRARY_SUBSCRIPTIONS_MANAGE_DOT))],
)
async def create_subscription(
    data: LibrarySubscriptionCreate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[LibrarySubscriptionResponse]:
    """Register a new journal, magazine, or e-resource subscription."""
    sub = await LibraryService.create_subscription(
        db, tenant_ctx.tenant_id, data, current_user.id
    )
    return ApiResponse(data=LibrarySubscriptionResponse.model_validate(sub))


@library_router.get(
    "/subscriptions",
    response_model=ApiResponse[LibrarySubscriptionListResponse],
    dependencies=[Depends(require_permission(LIBRARY_SUBSCRIPTIONS_MANAGE_DOT))],
)
async def list_subscriptions(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    library_id: UUID | None = Query(None),
    status_filter: LibrarySubscriptionStatus | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> ApiResponse[LibrarySubscriptionListResponse]:
    """List subscriptions with renewal deadlines."""
    items, total = await LibraryService.list_subscriptions(
        db,
        tenant_ctx.tenant_id,
        library_id=library_id,
        status_filter=status_filter.value if status_filter else None,
        skip=skip,
        limit=limit,
    )
    return ApiResponse(
        data=LibrarySubscriptionListResponse(
            items=[LibrarySubscriptionResponse.model_validate(s) for s in items],
            total=total,
        )
    )


@library_router.put(
    "/subscriptions/{subscription_id}",
    response_model=ApiResponse[LibrarySubscriptionResponse],
    dependencies=[Depends(require_permission(LIBRARY_SUBSCRIPTIONS_MANAGE_DOT))],
)
async def update_subscription(
    subscription_id: UUID,
    data: LibrarySubscriptionUpdate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[LibrarySubscriptionResponse]:
    """Update subscription term, received issues count, or renewal status."""
    sub = await LibraryService.update_subscription(
        db, tenant_ctx.tenant_id, subscription_id, data, current_user.id
    )
    return ApiResponse(data=LibrarySubscriptionResponse.model_validate(sub))


# =============================================================================
# 11. DIGITAL RESOURCE ACCESS & CONTROL
# =============================================================================


@library_router.post(
    "/digital-access/{catalog_item_id}/token",
    response_model=ApiResponse[LibraryDigitalAccessTokenResponse],
    dependencies=[Depends(require_permission(LIBRARY_DIGITAL_ACCESS_DOT))],
)
async def generate_digital_access_token(
    catalog_item_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[LibraryDigitalAccessTokenResponse]:
    """Verify digital access eligibility and generate secure, expiring access token."""
    res = await LibraryService.generate_digital_access_token(
        db, tenant_ctx.tenant_id, catalog_item_id, current_user.id
    )
    return ApiResponse(data=LibraryDigitalAccessTokenResponse(**res))


@library_router.get(
    "/digital-access/logs",
    response_model=ApiResponse[LibraryDigitalResourceAccessListResponse],
    dependencies=[Depends(require_permission(LIBRARY_BRANCHES_MANAGE_DOT))],
)
async def list_digital_access_logs(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    catalog_item_id: UUID | None = Query(None),
    user_id: UUID | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> ApiResponse[LibraryDigitalResourceAccessListResponse]:
    """List digital resource access audit logs."""
    items, total = await LibraryService.list_digital_access_logs(
        db,
        tenant_ctx.tenant_id,
        catalog_item_id=catalog_item_id,
        user_id=user_id,
        skip=skip,
        limit=limit,
    )
    return ApiResponse(
        data=LibraryDigitalResourceAccessListResponse(
            items=[LibraryDigitalResourceAccessLogResponse.model_validate(l) for l in items],
            total=total,
        )
    )


# =============================================================================
# 12. INVENTORY VERIFICATION & STOCK AUDITS
# =============================================================================


@library_router.post(
    "/inventory-audits",
    response_model=ApiResponse[LibraryInventoryAuditResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(LIBRARY_AUDIT_MANAGE_DOT))],
)
async def create_inventory_audit(
    data: LibraryInventoryAuditCreate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[LibraryInventoryAuditResponse]:
    """Create a stock verification audit and capture expected inventory snapshot."""
    audit = await LibraryService.create_inventory_audit(
        db, tenant_ctx.tenant_id, data, current_user.id
    )
    return ApiResponse(data=LibraryInventoryAuditResponse.model_validate(audit))


@library_router.get(
    "/inventory-audits",
    response_model=ApiResponse[LibraryInventoryAuditListResponse],
    dependencies=[Depends(require_permission(LIBRARY_AUDIT_MANAGE_DOT))],
)
async def list_inventory_audits(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    library_id: UUID | None = Query(None),
    status_filter: LibraryInventoryAuditStatus | None = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> ApiResponse[LibraryInventoryAuditListResponse]:
    """List inventory verification audits."""
    items, total = await LibraryService.list_inventory_audits(
        db,
        tenant_ctx.tenant_id,
        library_id=library_id,
        status_filter=status_filter.value if status_filter else None,
        skip=skip,
        limit=limit,
    )
    return ApiResponse(
        data=LibraryInventoryAuditListResponse(
            items=[LibraryInventoryAuditResponse.model_validate(a) for a in items],
            total=total,
        )
    )


@library_router.get(
    "/inventory-audits/{audit_id}",
    response_model=ApiResponse[LibraryInventoryAuditResponse],
    dependencies=[Depends(require_permission(LIBRARY_AUDIT_MANAGE_DOT))],
)
async def get_inventory_audit(
    audit_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
) -> ApiResponse[LibraryInventoryAuditResponse]:
    """Get single inventory audit with discrepancy summary."""
    audit = await LibraryService.get_inventory_audit(db, tenant_ctx.tenant_id, audit_id)
    return ApiResponse(data=LibraryInventoryAuditResponse.model_validate(audit))


@library_router.post(
    "/inventory-audits/{audit_id}/record-scan",
    response_model=ApiResponse[LibraryInventoryAuditItemResponse],
    dependencies=[Depends(require_permission(LIBRARY_AUDIT_MANAGE_DOT))],
)
async def record_audit_scan(
    audit_id: UUID,
    data: LibraryInventoryAuditScanRecordRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[LibraryInventoryAuditItemResponse]:
    """Record observed physical copy scan during stock verification."""
    item = await LibraryService.record_audit_scan(
        db, tenant_ctx.tenant_id, audit_id, data, current_user.id
    )
    return ApiResponse(data=LibraryInventoryAuditItemResponse.model_validate(item))


@library_router.post(
    "/inventory-audits/{audit_id}/reconcile",
    response_model=ApiResponse[LibraryInventoryAuditResponse],
    dependencies=[Depends(require_permission(LIBRARY_AUDIT_MANAGE_DOT))],
)
async def reconcile_inventory_audit(
    audit_id: UUID,
    data: LibraryInventoryAuditReconcileRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[LibraryInventoryAuditResponse]:
    """Reconcile and close an inventory audit with authorized reviewer sign-off."""
    audit = await LibraryService.reconcile_inventory_audit(
        db, tenant_ctx.tenant_id, audit_id, data, current_user.id
    )
    return ApiResponse(data=LibraryInventoryAuditResponse.model_validate(audit))


# =============================================================================
# 13. ANALYTICS & COMPLIANCE SWEEP
# =============================================================================


@library_router.get(
    "/analytics/summary",
    response_model=ApiResponse[LibraryAnalyticsSummaryResponse],
    dependencies=[Depends(require_permission(LIBRARY_ANALYTICS_READ_DOT))],
)
async def get_analytics_summary(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
) -> ApiResponse[LibraryAnalyticsSummaryResponse]:
    """Get high-level institutional library metrics, circulation rates, and audit statuses."""
    summary = await LibraryService.get_analytics_summary(db, tenant_ctx.tenant_id)
    return ApiResponse(data=LibraryAnalyticsSummaryResponse(**summary))


@library_router.post(
    "/compliance/sweep",
    response_model=ApiResponse[LibraryDeadlineSweepResponse],
    dependencies=[Depends(require_permission(LIBRARY_BRANCHES_MANAGE_DOT))],
)
async def trigger_compliance_sweep(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
) -> ApiResponse[LibraryDeadlineSweepResponse]:
    """Manually trigger library compliance sweep for overdue loans and expired holds."""
    res = await LibraryService.sweep_deadlines_and_compliance(db, tenant_ctx.tenant_id)
    return ApiResponse(data=LibraryDeadlineSweepResponse(**res))
