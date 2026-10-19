"""Enterprise Institutional Library, Learning Resources & Knowledge Access Service (Step 45).

Encapsulates complete domain logic for:
- Library branch administration, multi-branch hierarchies, operating schedules
- Configurable lending policies per member category and resource type
- Bibliographic catalog management, duplicate detection, and resource tagging
- Physical copy inventory with unique accessioning, barcodes, and condition grades
- Member profiles, borrowing limits, active loan tracking, and suspension enforcement
- Circulation engine: checkout, check-in returns, due date calculations, renewals
- Resource reservation queues, hold allocations, pickup deadlines, and priority waitlists
- Overdue calculations, fine assessments, and authorized fine waivers
- Acquisitions procurement requests, approvals, receipt tracking, and accessioning
- Periodicals, e-journal subscriptions, and renewal tracking
- Controlled digital resource access logging and token generation
- Physical stock verification audits, scanning, and discrepancy reconciliation
- Live analytics KPIs and automated compliance/deadline sweeps
"""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import String, cast, delete, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditEventCategory, create_audit_entry
from app.core.exceptions import (
    LibraryAcquisitionNotFoundException,
    LibraryActiveLoansOutstandingException,
    LibraryAuditNotFoundException,
    LibraryBorrowLimitExceededException,
    LibraryBranchNotFoundException,
    LibraryCatalogItemNotFoundException,
    LibraryCopyNotFoundException,
    LibraryCopyUnavailableException,
    LibraryDigitalAccessRestrictedException,
    LibraryDuplicateAccessionException,
    LibraryFineNotFoundException,
    LibraryFineWaiverUnauthorizedException,
    LibraryInvalidRenewalException,
    LibraryLoanNotFoundException,
    LibraryMemberNotFoundException,
    LibraryMemberSuspendedException,
    LibraryReservationConflictException,
    LibraryReservationNotFoundException,
    LibrarySubscriptionNotFoundException,
)
from app.models.library import (
    LibraryAcquisitionRequest,
    LibraryAcquisitionStatus,
    LibraryAuditScanResult,
    LibraryBranch,
    LibraryBranchStatus,
    LibraryCatalogItem,
    LibraryCatalogStatus,
    LibraryCirculationLoan,
    LibraryCirculationStatus,
    LibraryCopyCondition,
    LibraryDigitalResourceAccess,
    LibraryFineCategory,
    LibraryFineRecord,
    LibraryFineStatus,
    LibraryInventoryAudit,
    LibraryInventoryAuditItem,
    LibraryInventoryAuditStatus,
    LibraryLendingPolicy,
    LibraryLoanStatus,
    LibraryMemberCategory,
    LibraryMemberProfile,
    LibraryMemberStatus,
    LibraryPhysicalCopy,
    LibraryReservation,
    LibraryReservationStatus,
    LibraryResourceType,
    LibrarySubscription,
    LibrarySubscriptionStatus,
    LibrarySubscriptionType,
)
from app.models.people import User
from app.schemas.library import (
    LibraryAcquisitionApprovalRequest,
    LibraryAcquisitionCreate,
    LibraryAcquisitionReceiveRequest,
    LibraryBranchCreate,
    LibraryBranchUpdate,
    LibraryCatalogItemCreate,
    LibraryCatalogItemUpdate,
    LibraryDigitalResourceAccessLogRequest,
    LibraryFineAssessRequest,
    LibraryFineWaiveRequest,
    LibraryInventoryAuditCreate,
    LibraryInventoryAuditItemScanRequest,
    LibraryInventoryAuditReconcileRequest,
    LibraryLendingPolicyCreate,
    LibraryLendingPolicyUpdate,
    LibraryLoanIssueRequest,
    LibraryLoanRenewRequest,
    LibraryLoanReturnRequest,
    LibraryMemberProfileCreate,
    LibraryMemberProfileUpdate,
    LibraryPhysicalCopyCreate,
    LibraryPhysicalCopyUpdate,
    LibraryReservationCancelRequest,
    LibraryReservationCreate,
    LibrarySubscriptionCreate,
    LibrarySubscriptionUpdate,
)


class LibraryService:
    """Production service for Enterprise Library, Learning Resources & Knowledge Access."""

    # =========================================================================
    # 1. LIBRARY BRANCHES
    # =========================================================================

    @classmethod
    async def create_branch(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        data: LibraryBranchCreate,
        current_user_id: UUID,
    ) -> LibraryBranch:
        """Create a new library branch or learning resource centre."""
        existing = await db.scalar(
            select(LibraryBranch).where(
                LibraryBranch.tenant_id == tenant_id,
                LibraryBranch.branch_code == data.branch_code,
            )
        )
        if existing:
            raise LibraryDuplicateAccessionException(
                f"Branch code '{data.branch_code}' already exists in this institution."
            )

        branch = LibraryBranch(
            tenant_id=tenant_id,
            branch_code=data.branch_code,
            name=data.name,
            description=data.description,
            campus_id=data.campus_id,
            department_id=data.department_id,
            location_building=data.location_building,
            location_floor=data.location_floor,
            contact_email=data.contact_email,
            contact_phone=data.contact_phone,
            operating_hours_json=data.operating_hours_json,
            closure_dates_json=data.closure_dates_json,
            head_librarian_user_id=data.head_librarian_user_id,
            status=data.status.value if hasattr(data.status, "value") else str(data.status),
            is_active=data.is_active,
            metadata_json=dict(data.metadata_json or {}),
        )
        db.add(branch)
        await db.flush()

        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            user_id=current_user_id,
            action=AuditEventCategory.LIBRARY_BRANCH_CREATED,
            entity_type="library_branch",
            entity_id=branch.id,
            new_values_json={"branch_code": branch.branch_code, "name": branch.name},
        )
        return branch

    @classmethod
    async def update_branch(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        branch_id: UUID,
        data: LibraryBranchUpdate,
        current_user_id: UUID,
    ) -> LibraryBranch:
        """Update branch details, schedules, or head librarian."""
        branch = await cls.get_branch(db, tenant_id, branch_id)
        update_dict = data.model_dump(exclude_unset=True)

        for key, val in update_dict.items():
            if val is not None:
                if key == "status" and hasattr(val, "value"):
                    setattr(branch, key, val.value)
                else:
                    setattr(branch, key, val)

        await db.flush()
        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            user_id=current_user_id,
            action=AuditEventCategory.LIBRARY_BRANCH_UPDATED,
            entity_type="library_branch",
            entity_id=branch.id,
            new_values_json={"updated_fields": list(update_dict.keys())},
        )
        return branch

    @classmethod
    async def get_branch(
        cls, db: AsyncSession, tenant_id: UUID, branch_id: UUID
    ) -> LibraryBranch:
        """Retrieve library branch by ID."""
        branch = await db.scalar(
            select(LibraryBranch).where(
                LibraryBranch.tenant_id == tenant_id, LibraryBranch.id == branch_id
            )
        )
        if not branch:
            raise LibraryBranchNotFoundException(str(branch_id))
        return branch

    @classmethod
    async def list_branches(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        skip: int = 0,
        limit: int = 50,
        status: str | None = None,
        status_filter: str | None = None,
        campus_id: UUID | None = None,
        **kwargs: Any,
    ) -> tuple[list[LibraryBranch], int]:
        """List library branches with optional campus and status filter."""
        st = status_filter or status
        query = select(LibraryBranch).where(LibraryBranch.tenant_id == tenant_id)
        if campus_id:
            query = query.where(LibraryBranch.campus_id == campus_id)
        if st and st != "ALL":
            query = query.where(LibraryBranch.status == st)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.scalar(count_query)) or 0

        query = query.order_by(LibraryBranch.branch_code).offset(skip).limit(limit)
        items = list(await db.scalars(query))
        return items, total

    # =========================================================================
    # 2. LENDING POLICIES
    # =========================================================================

    @classmethod
    async def create_lending_policy(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        data: LibraryLendingPolicyCreate,
        current_user_id: UUID,
    ) -> LibraryLendingPolicy:
        """Configure lending rules for a user category and resource type."""
        mem_cat = data.member_category.value if hasattr(data.member_category, "value") else str(data.member_category)
        res_type = data.resource_type.value if hasattr(data.resource_type, "value") else str(data.resource_type)

        policy = LibraryLendingPolicy(
            tenant_id=tenant_id,
            policy_code=data.policy_code,
            name=data.name,
            member_category=mem_cat,
            resource_type=res_type,
            max_borrow_limit=data.max_borrow_limit,
            loan_duration_days=data.loan_duration_days,
            renewal_limit=data.renewal_limit,
            fine_daily_rate=data.fine_daily_rate,
            fine_grace_period_days=data.fine_grace_period_days,
            max_fine_limit=data.max_fine_limit,
            is_reservation_allowed=data.is_reservation_allowed,
            reservation_queue_limit=data.reservation_queue_limit,
            is_overnight_only=data.is_overnight_only,
            is_active=data.is_active,
            metadata_json=dict(data.metadata_json or {}),
        )
        db.add(policy)
        await db.flush()

        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            user_id=current_user_id,
            action=AuditEventCategory.LIBRARY_POLICY_CONFIGURED,
            entity_type="library_lending_policy",
            entity_id=policy.id,
            new_values_json={"policy_code": policy.policy_code, "category": mem_cat},
        )
        return policy

    @classmethod
    async def get_effective_policy(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        member_category: str,
        resource_type: str,
    ) -> LibraryLendingPolicy:
        """Find the matching active policy or return an active institutional default."""
        policy = await db.scalar(
            select(LibraryLendingPolicy).where(
                LibraryLendingPolicy.tenant_id == tenant_id,
                LibraryLendingPolicy.member_category == member_category,
                LibraryLendingPolicy.resource_type == resource_type,
                LibraryLendingPolicy.is_active.is_(True),
            )
        )
        if not policy:
            # Fallback to category default
            policy = await db.scalar(
                select(LibraryLendingPolicy).where(
                    LibraryLendingPolicy.tenant_id == tenant_id,
                    LibraryLendingPolicy.member_category == member_category,
                    LibraryLendingPolicy.is_active.is_(True),
                )
            )
        if not policy:
            # Construct a safe transient default policy
            policy = LibraryLendingPolicy(
                tenant_id=tenant_id,
                policy_code="DEFAULT-FALLBACK",
                name="Default Fallback Lending Policy",
                member_category=member_category,
                resource_type=resource_type,
                max_borrow_limit=4,
                loan_duration_days=14,
                renewal_limit=2,
                fine_daily_rate=Decimal("1.00"),
                fine_grace_period_days=1,
                max_fine_limit=Decimal("50.00"),
                is_reservation_allowed=True,
                reservation_queue_limit=2,
                is_overnight_only=False,
                is_active=True,
                metadata_json={},
            )
        return policy

    @classmethod
    async def list_lending_policies(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        library_id: UUID | None = None,
        member_category: str | None = None,
        resource_type: str | None = None,
        **kwargs: Any,
    ) -> list[LibraryLendingPolicy]:
        """List all configured lending policies for this tenant with optional filters."""
        query = select(LibraryLendingPolicy).where(LibraryLendingPolicy.tenant_id == tenant_id)
        if library_id:
            query = query.where(
                or_(
                    LibraryLendingPolicy.library_id == library_id,
                    LibraryLendingPolicy.library_id.is_(None),
                )
            )
        if member_category and member_category != "ALL":
            query = query.where(LibraryLendingPolicy.member_category == member_category)
        if resource_type and resource_type != "ALL":
            query = query.where(LibraryLendingPolicy.resource_type == resource_type)

        return list(
            await db.scalars(
                query.order_by(LibraryLendingPolicy.member_category, LibraryLendingPolicy.resource_type)
            )
        )

    # =========================================================================
    # 3. CATALOG RECORDS
    # =========================================================================

    @classmethod
    async def create_catalog_item(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        data: LibraryCatalogItemCreate,
        current_user_id: UUID,
    ) -> LibraryCatalogItem:
        """Register a bibliographic catalog record with duplicate check."""
        # Check duplicate catalog code
        existing = await db.scalar(
            select(LibraryCatalogItem).where(
                LibraryCatalogItem.tenant_id == tenant_id,
                LibraryCatalogItem.catalog_code == data.catalog_code,
            )
        )
        if existing:
            return existing

        # Check duplicate ISBN if present
        if data.isbn_or_issn:
            dup_isbn = await db.scalar(
                select(LibraryCatalogItem).where(
                    LibraryCatalogItem.tenant_id == tenant_id,
                    LibraryCatalogItem.isbn_or_issn == data.isbn_or_issn,
                )
            )
            if dup_isbn:
                return dup_isbn

        res_type = data.resource_type.value if hasattr(data.resource_type, "value") else str(data.resource_type)

        item = LibraryCatalogItem(
            tenant_id=tenant_id,
            catalog_code=data.catalog_code,
            title=data.title,
            subtitle=data.subtitle,
            authors_json=data.authors_json,
            publisher=data.publisher,
            publication_year=data.publication_year,
            edition=data.edition,
            language=data.language,
            isbn_or_issn=data.isbn_or_issn,
            doi_or_urn=data.doi_or_urn,
            call_number=data.call_number,
            classification_scheme=data.classification_scheme,
            resource_type=res_type,
            subject_tags=data.subject_tags,
            keywords=data.keywords,
            abstract_description=data.abstract_description,
            is_digital=data.is_digital,
            digital_access_url=data.digital_access_url,
            document_id=data.document_id,
            catalog_status=LibraryCatalogStatus.CATALOGED.value,
            total_copies_count=0,
            available_copies_count=0,
            metadata_json=dict(data.metadata_json or {}),
        )
        db.add(item)
        await db.flush()

        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            user_id=current_user_id,
            action=AuditEventCategory.LIBRARY_CATALOG_CREATED,
            entity_type="library_catalog_item",
            entity_id=item.id,
            new_values_json={"catalog_code": item.catalog_code, "title": item.title},
        )
        return item

    @classmethod
    async def update_catalog_item(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        item_id: UUID,
        data: LibraryCatalogItemUpdate,
        current_user_id: UUID,
    ) -> LibraryCatalogItem:
        """Update catalog metadata or digital link."""
        item = await cls.get_catalog_item(db, tenant_id, item_id)
        update_dict = data.model_dump(exclude_unset=True)

        for key, val in update_dict.items():
            if val is not None:
                if key in ("resource_type", "catalog_status") and hasattr(val, "value"):
                    setattr(item, key, val.value)
                else:
                    setattr(item, key, val)

        await db.flush()
        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            user_id=current_user_id,
            action=AuditEventCategory.LIBRARY_CATALOG_UPDATED,
            entity_type="library_catalog_item",
            entity_id=item.id,
            new_values_json={"updated_fields": list(update_dict.keys())},
        )
        return item

    @classmethod
    async def get_catalog_item(
        cls, db: AsyncSession, tenant_id: UUID, item_id: UUID
    ) -> LibraryCatalogItem:
        """Retrieve catalog item by ID."""
        item = await db.scalar(
            select(LibraryCatalogItem).where(
                LibraryCatalogItem.tenant_id == tenant_id, LibraryCatalogItem.id == item_id
            )
        )
        if not item:
            raise LibraryCatalogItemNotFoundException(str(item_id))
        return item

    @classmethod
    async def list_catalog_items(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        search: str | None = None,
        q: str | None = None,
        resource_type: str | None = None,
        catalog_status: str | None = None,
        status_filter: str | None = None,
        is_digital: bool | None = None,
        primary_language: str | None = None,
        subject_classification: str | None = None,
        skip: int = 0,
        limit: int = 50,
        **kwargs: Any,
    ) -> tuple[list[LibraryCatalogItem], int]:
        """Search and list bibliographic items."""
        query = select(LibraryCatalogItem).where(LibraryCatalogItem.tenant_id == tenant_id)

        term = q or search
        if term:
            search_pat = f"%{term.strip()}%"
            query = query.where(
                or_(
                    LibraryCatalogItem.title.ilike(search_pat),
                    LibraryCatalogItem.catalog_code.ilike(search_pat),
                    LibraryCatalogItem.isbn_or_issn.ilike(search_pat),
                    LibraryCatalogItem.publisher.ilike(search_pat),
                    LibraryCatalogItem.call_number.ilike(search_pat),
                )
            )

        if resource_type and resource_type != "ALL":
            query = query.where(LibraryCatalogItem.resource_type == resource_type)

        st = status_filter or catalog_status
        if st and st != "ALL":
            query = query.where(LibraryCatalogItem.catalog_status == st)

        if is_digital is not None:
            query = query.where(LibraryCatalogItem.is_digital == is_digital)

        if primary_language:
            query = query.where(LibraryCatalogItem.primary_language == primary_language)

        if subject_classification:
            query = query.where(LibraryCatalogItem.subject_classification.ilike(f"%{subject_classification}%"))

        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.scalar(count_query)) or 0

        query = query.order_by(LibraryCatalogItem.title).offset(skip).limit(limit)
        items = list(await db.scalars(query))
        return items, total

    # =========================================================================
    # 4. PHYSICAL COPIES
    # =========================================================================

    @classmethod
    async def register_physical_copy(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        data: LibraryPhysicalCopyCreate,
        current_user_id: UUID,
    ) -> LibraryPhysicalCopy:
        """Accession a physical volume and associate with a catalog item."""
        # Verify catalog item exists
        catalog_item = await cls.get_catalog_item(db, tenant_id, data.catalog_item_id)
        # Verify owning branch exists
        await cls.get_branch(db, tenant_id, data.owning_library_id)

        # Check unique accession number
        existing = await db.scalar(
            select(LibraryPhysicalCopy).where(
                LibraryPhysicalCopy.tenant_id == tenant_id,
                LibraryPhysicalCopy.accession_number == data.accession_number,
            )
        )
        if existing:
            raise LibraryDuplicateAccessionException(data.accession_number)

        circ_status = data.circulation_status.value if hasattr(data.circulation_status, "value") else str(data.circulation_status)
        cond_grade = data.condition_grade.value if hasattr(data.condition_grade, "value") else str(data.condition_grade)

        copy = LibraryPhysicalCopy(
            tenant_id=tenant_id,
            catalog_item_id=data.catalog_item_id,
            owning_library_id=data.owning_library_id,
            accession_number=data.accession_number,
            barcode=data.barcode or data.accession_number,
            shelf_location=data.shelf_location,
            call_number_override=data.call_number_override,
            acquisition_date=data.acquisition_date,
            acquisition_cost=data.acquisition_cost,
            currency=data.currency,
            condition_grade=cond_grade,
            circulation_status=circ_status,
            is_reference_only=data.is_reference_only,
            last_inventory_check_date=date.today(),
            notes=data.notes,
            metadata_json=dict(data.metadata_json or {}),
        )
        db.add(copy)

        # Increment catalog item copy counts
        catalog_item.total_copies_count += 1
        if circ_status == LibraryCirculationStatus.AVAILABLE.value:
            catalog_item.available_copies_count += 1

        await db.flush()

        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            user_id=current_user_id,
            action=AuditEventCategory.LIBRARY_COPY_REGISTERED,
            entity_type="library_physical_copy",
            entity_id=copy.id,
            new_values_json={
                "accession_number": copy.accession_number,
                "catalog_item_id": str(catalog_item.id),
            },
        )
        return copy

    @classmethod
    async def update_physical_copy(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        copy_id: UUID,
        data: LibraryPhysicalCopyUpdate,
        current_user_id: UUID,
    ) -> LibraryPhysicalCopy:
        """Update copy location, condition, or inventory verification status."""
        copy = await cls.get_physical_copy(db, tenant_id, copy_id)
        catalog_item = await cls.get_catalog_item(db, tenant_id, copy.catalog_item_id)
        update_dict = data.model_dump(exclude_unset=True)

        old_status = copy.circulation_status

        for key, val in update_dict.items():
            if val is not None:
                if key in ("condition_grade", "circulation_status") and hasattr(val, "value"):
                    setattr(copy, key, val.value)
                else:
                    setattr(copy, key, val)

        # Reconcile catalog available counts if status changed
        if copy.circulation_status != old_status:
            if old_status == LibraryCirculationStatus.AVAILABLE.value and copy.circulation_status != LibraryCirculationStatus.AVAILABLE.value:
                catalog_item.available_copies_count = max(0, catalog_item.available_copies_count - 1)
            elif old_status != LibraryCirculationStatus.AVAILABLE.value and copy.circulation_status == LibraryCirculationStatus.AVAILABLE.value:
                catalog_item.available_copies_count += 1

        await db.flush()
        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            user_id=current_user_id,
            action=AuditEventCategory.LIBRARY_COPY_UPDATED,
            entity_type="library_physical_copy",
            entity_id=copy.id,
            new_values_json={"updated_fields": list(update_dict.keys())},
        )
        return copy

    @classmethod
    async def get_physical_copy(
        cls, db: AsyncSession, tenant_id: UUID, copy_id: UUID
    ) -> LibraryPhysicalCopy:
        """Retrieve physical copy by ID."""
        copy = await db.scalar(
            select(LibraryPhysicalCopy).where(
                LibraryPhysicalCopy.tenant_id == tenant_id, LibraryPhysicalCopy.id == copy_id
            )
        )
        if not copy:
            raise LibraryCopyNotFoundException(str(copy_id))
        return copy

    @classmethod
    async def list_physical_copies(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        catalog_item_id: UUID | None = None,
        library_id: UUID | None = None,
        circulation_status: str | None = None,
        condition_grade: str | None = None,
        skip: int = 0,
        limit: int = 50,
        **kwargs: Any,
    ) -> tuple[list[LibraryPhysicalCopy], int]:
        """List physical copies with optional filters."""
        query = select(LibraryPhysicalCopy).where(LibraryPhysicalCopy.tenant_id == tenant_id)

        if catalog_item_id:
            query = query.where(LibraryPhysicalCopy.catalog_item_id == catalog_item_id)
        if library_id:
            query = query.where(LibraryPhysicalCopy.owning_library_id == library_id)
        if circulation_status and circulation_status != "ALL":
            query = query.where(LibraryPhysicalCopy.circulation_status == circulation_status)
        if condition_grade and condition_grade != "ALL":
            query = query.where(LibraryPhysicalCopy.condition_grade == condition_grade)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.scalar(count_query)) or 0

        query = query.order_by(LibraryPhysicalCopy.accession_number).offset(skip).limit(limit)
        items = list(await db.scalars(query))
        return items, total

    # =========================================================================
    # 5. MEMBER PROFILES
    # =========================================================================

    @classmethod
    async def enroll_member(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        data: LibraryMemberProfileCreate,
        current_user_id: UUID,
    ) -> LibraryMemberProfile:
        """Enroll or activate patron library membership."""
        # Verify user exists
        user = await db.scalar(
            select(User).where(User.id == data.user_id)
        )
        if not user:
            raise LibraryMemberNotFoundException(f"User '{data.user_id}' does not exist.")

        # Check existing membership
        existing = await db.scalar(
            select(LibraryMemberProfile).where(
                LibraryMemberProfile.tenant_id == tenant_id,
                or_(
                    LibraryMemberProfile.user_id == data.user_id,
                    LibraryMemberProfile.membership_number == data.membership_number,
                ),
            )
        )
        if existing:
            return existing

        cat_val = data.member_category.value if hasattr(data.member_category, "value") else str(data.member_category)
        status_val = data.status.value if hasattr(data.status, "value") else str(data.status)

        member = LibraryMemberProfile(
            tenant_id=tenant_id,
            user_id=data.user_id,
            membership_number=data.membership_number,
            member_category=cat_val,
            status=status_val,
            valid_from=data.valid_from,
            valid_until=data.valid_until,
            custom_borrow_limit_override=data.custom_borrow_limit_override,
            active_loans_count=0,
            total_historical_loans=0,
            current_outstanding_fines=Decimal("0.00"),
            metadata_json=dict(data.metadata_json or {}),
        )
        db.add(member)
        await db.flush()

        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            user_id=current_user_id,
            action=AuditEventCategory.LIBRARY_MEMBER_ENROLLED,
            entity_type="library_member_profile",
            entity_id=member.id,
            new_values_json={"membership_number": member.membership_number, "user_id": str(user.id)},
        )
        return member

    @classmethod
    async def get_member(
        cls, db: AsyncSession, tenant_id: UUID, member_id_or_user_id: UUID
    ) -> LibraryMemberProfile:
        """Get library member profile by member ID or user ID."""
        member = await db.scalar(
            select(LibraryMemberProfile).where(
                LibraryMemberProfile.tenant_id == tenant_id,
                or_(
                    LibraryMemberProfile.id == member_id_or_user_id,
                    LibraryMemberProfile.user_id == member_id_or_user_id,
                ),
            )
        )
        if not member:
            raise LibraryMemberNotFoundException(str(member_id_or_user_id))
        return member

    @classmethod
    async def update_member(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        member_id: UUID,
        data: LibraryMemberProfileUpdate,
        current_user_id: UUID,
    ) -> LibraryMemberProfile:
        """Update member status, valid dates, or apply suspensions."""
        member = await cls.get_member(db, tenant_id, member_id)
        update_dict = data.model_dump(exclude_unset=True)

        for key, val in update_dict.items():
            if val is not None:
                if key in ("member_category", "status") and hasattr(val, "value"):
                    setattr(member, key, val.value)
                else:
                    setattr(member, key, val)

        await db.flush()
        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            user_id=current_user_id,
            action=AuditEventCategory.LIBRARY_MEMBER_UPDATED,
            entity_type="library_member_profile",
            entity_id=member.id,
            new_values_json={"updated_fields": list(update_dict.keys())},
        )
        return member

    @classmethod
    async def list_members(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        search: str | None = None,
        q: str | None = None,
        member_category: str | None = None,
        status: str | None = None,
        status_filter: str | None = None,
        home_library_id: UUID | None = None,
        skip: int = 0,
        limit: int = 50,
        **kwargs: Any,
    ) -> tuple[list[LibraryMemberProfile], int]:
        """List patrons with filtering."""
        query = select(LibraryMemberProfile).where(LibraryMemberProfile.tenant_id == tenant_id)

        term = q or search
        if term:
            query = query.where(LibraryMemberProfile.membership_number.ilike(f"%{term.strip()}%"))
        if member_category and member_category != "ALL":
            query = query.where(LibraryMemberProfile.member_category == member_category)
        st = status_filter or status
        if st and st != "ALL":
            query = query.where(LibraryMemberProfile.status == st)
        if home_library_id:
            query = query.where(LibraryMemberProfile.home_library_id == home_library_id)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.scalar(count_query)) or 0

        query = query.order_by(LibraryMemberProfile.membership_number).offset(skip).limit(limit)
        items = list(await db.scalars(query))
        return items, total

    # =========================================================================
    # 6. CIRCULATION & LENDING ENGINE
    # =========================================================================

    @classmethod
    async def checkout_loan(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        data: LibraryLoanIssueRequest,
        staff_user_id: UUID,
    ) -> LibraryCirculationLoan:
        """Issue and checkout a physical resource to a library member."""
        # 1. Fetch and validate member
        target_member = data.member_id or data.user_id
        member = await cls.get_member(db, tenant_id, target_member)
        if member.status != LibraryMemberStatus.ACTIVE.value or member.is_borrowing_suspended:
            raise LibraryMemberSuspendedException(
                member_name=member.membership_number,
                status_str=member.status,
                reason=member.suspension_reason,
            )

        # 2. Check overdue loan restrictions
        overdue_count = await db.scalar(
            select(func.count(LibraryCirculationLoan.id)).where(
                LibraryCirculationLoan.tenant_id == tenant_id,
                LibraryCirculationLoan.member_id == member.id,
                LibraryCirculationLoan.status == LibraryLoanStatus.ACTIVE.value,
                LibraryCirculationLoan.due_date < date.today(),
            )
        )
        if overdue_count and overdue_count > 0:
            raise LibraryActiveLoansOutstandingException(
                member_name=member.membership_number, overdue_count=overdue_count
            )

        # 3. Fetch physical copy and catalog item
        copy = await cls.get_physical_copy(db, tenant_id, data.copy_id)
        catalog_item = await cls.get_catalog_item(db, tenant_id, copy.catalog_item_id)

        # 4. Check copy availability (must be AVAILABLE or ON_HOLD allocated to this member)
        if copy.circulation_status != LibraryCirculationStatus.AVAILABLE.value:
            # Check if it was allocated to this member via reservation
            allocated_res = await db.scalar(
                select(LibraryReservation).where(
                    LibraryReservation.tenant_id == tenant_id,
                    LibraryReservation.allocated_copy_id == copy.id,
                    LibraryReservation.member_id == member.id,
                    LibraryReservation.status == LibraryReservationStatus.ALLOCATED_PENDING_PICKUP.value,
                )
            )
            if not allocated_res:
                raise LibraryCopyUnavailableException(
                    copy_ref=copy.accession_number, current_status=copy.circulation_status
                )
            # Fulfill the reservation
            allocated_res.status = LibraryReservationStatus.FULFILLED.value
            allocated_res.fulfilled_at = datetime.now(UTC)

        # 5. Check lending policy and borrowing limit
        policy = await cls.get_effective_policy(
            db, tenant_id, member.member_category, catalog_item.resource_type
        )
        max_limit = member.custom_borrow_limit_override or policy.max_borrow_limit
        if member.active_loans_count >= max_limit:
            raise LibraryBorrowLimitExceededException(
                member_name=member.membership_number,
                active_count=member.active_loans_count,
                max_limit=max_limit,
            )

        # 6. Calculate due date
        loan_days = getattr(data, "loan_days_override", None) or policy.loan_duration_days
        computed_due_date = data.due_date or (date.today() + timedelta(days=loan_days))

        # 7. Create circulation loan transaction
        loan_code = f"LN-{datetime.now(UTC).strftime('%Y%m')}-{str(uuid4())[:8].upper()}"
        loan_user_id = data.user_id or member.user_id
        loan_library_id = data.library_id or copy.owning_library_id
        loan = LibraryCirculationLoan(
            tenant_id=tenant_id,
            loan_reference_code=loan_code,
            copy_id=copy.id,
            catalog_item_id=catalog_item.id,
            member_id=member.id,
            user_id=loan_user_id,
            library_id=loan_library_id,
            issued_at=datetime.now(UTC),
            due_date=computed_due_date,
            renewal_count=0,
            issued_by_user_id=staff_user_id,
            status=LibraryLoanStatus.ACTIVE.value,
            calculated_fine_amount=Decimal("0.00"),
            is_fine_posted_to_finance=False,
            notes=data.notes,
            metadata_json={},
        )
        db.add(loan)

        # 8. Mutate copy & member counts
        copy.circulation_status = LibraryCirculationStatus.CHECKED_OUT.value
        catalog_item.available_copies_count = max(0, catalog_item.available_copies_count - 1)
        member.active_loans_count += 1
        member.total_historical_loans += 1

        await db.flush()

        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            user_id=staff_user_id,
            action=AuditEventCategory.LIBRARY_LOAN_CHECKOUT,
            entity_type="library_circulation_loan",
            entity_id=loan.id,
            new_values_json={
                "loan_reference": loan.loan_reference_code,
                "accession_number": copy.accession_number,
                "due_date": computed_due_date.isoformat(),
            },
        )
        return loan

    @classmethod
    async def return_loan(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        loan_id: UUID,
        data: LibraryLoanReturnRequest,
        staff_user_id: UUID,
    ) -> LibraryCirculationLoan:
        """Process check-in return of a physical copy and allocate to reservation if waiting."""
        loan = await db.scalar(
            select(LibraryCirculationLoan).where(
                LibraryCirculationLoan.tenant_id == tenant_id, LibraryCirculationLoan.id == loan_id
            )
        )
        if not loan:
            raise LibraryLoanNotFoundException(str(loan_id))

        if loan.status != LibraryLoanStatus.ACTIVE.value:
            return loan

        copy = await cls.get_physical_copy(db, tenant_id, loan.copy_id)
        catalog_item = await cls.get_catalog_item(db, tenant_id, copy.catalog_item_id)
        member = await cls.get_member(db, tenant_id, loan.member_id)

        now = datetime.now(UTC)
        loan.returned_at = now
        loan.returned_to_library_id = data.returned_to_library_id or loan.library_id
        loan.received_by_user_id = staff_user_id
        loan.status = LibraryLoanStatus.RETURNED.value

        # Calculate overdue fine if returned late
        overdue_days = (now.date() - loan.due_date).days
        if overdue_days > 0:
            policy = await cls.get_effective_policy(
                db, tenant_id, member.member_category, catalog_item.resource_type
            )
            billable_days = max(0, overdue_days - policy.fine_grace_period_days)
            if billable_days > 0:
                fine_amount = min(
                    policy.max_fine_limit,
                    Decimal(str(billable_days)) * policy.fine_daily_rate,
                )
                loan.calculated_fine_amount = fine_amount
                # Generate fine record
                fine_code = f"FN-{datetime.now(UTC).strftime('%Y%m')}-{str(uuid4())[:8].upper()}"
                fine = LibraryFineRecord(
                    tenant_id=tenant_id,
                    fine_reference_code=fine_code,
                    loan_id=loan.id,
                    member_id=member.id,
                    user_id=member.user_id,
                    fine_category=LibraryFineCategory.OVERDUE.value,
                    base_amount=fine_amount,
                    waived_amount=Decimal("0.00"),
                    final_payable_amount=fine_amount,
                    currency="USD",
                    fine_status=LibraryFineStatus.ESTIMATED.value,
                    days_overdue=overdue_days,
                    calculation_basis=f"{billable_days} billable days @ {policy.fine_daily_rate}/day",
                    metadata_json={},
                )
                db.add(fine)
                member.current_outstanding_fines += fine_amount

        # Update condition grade if provided
        if data.condition_grade:
            copy.condition_grade = (
                data.condition_grade.value
                if hasattr(data.condition_grade, "value")
                else str(data.condition_grade)
            )

        # Check reservation hold queue for this catalog item
        next_res = await db.scalar(
            select(LibraryReservation)
            .where(
                LibraryReservation.tenant_id == tenant_id,
                LibraryReservation.catalog_item_id == catalog_item.id,
                LibraryReservation.status == LibraryReservationStatus.WAITING.value,
            )
            .order_by(LibraryReservation.priority_rank.desc(), LibraryReservation.queue_position.asc())
        )

        if next_res:
            # Allocate to next patron
            next_res.status = LibraryReservationStatus.ALLOCATED_PENDING_PICKUP.value
            next_res.allocated_copy_id = copy.id
            next_res.allocated_at = now
            next_res.pickup_deadline = now + timedelta(days=3)
            copy.circulation_status = LibraryCirculationStatus.RESERVED.value
        else:
            copy.circulation_status = LibraryCirculationStatus.AVAILABLE.value
            catalog_item.available_copies_count += 1

        member.active_loans_count = max(0, member.active_loans_count - 1)

        await db.flush()

        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            user_id=staff_user_id,
            action=AuditEventCategory.LIBRARY_LOAN_RETURN,
            entity_type="library_circulation_loan",
            entity_id=loan.id,
            new_values_json={
                "returned_at": now.isoformat(),
                "overdue_days": overdue_days,
                "fine_amount": str(loan.calculated_fine_amount),
            },
        )
        return loan

    @classmethod
    async def renew_loan(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        loan_id: UUID,
        data: LibraryLoanRenewRequest,
        actor_user_id: UUID,
    ) -> LibraryCirculationLoan:
        """Extend loan due date if within limits and no active hold conflicts."""
        loan = await db.scalar(
            select(LibraryCirculationLoan).where(
                LibraryCirculationLoan.tenant_id == tenant_id, LibraryCirculationLoan.id == loan_id
            )
        )
        if not loan:
            raise LibraryLoanNotFoundException(str(loan_id))

        if loan.status != LibraryLoanStatus.ACTIVE.value:
            raise LibraryInvalidRenewalException("Loan is not currently active.")

        copy = await cls.get_physical_copy(db, tenant_id, loan.copy_id)
        catalog_item = await cls.get_catalog_item(db, tenant_id, copy.catalog_item_id)
        member = await cls.get_member(db, tenant_id, loan.member_id)

        policy = await cls.get_effective_policy(
            db, tenant_id, member.member_category, catalog_item.resource_type
        )

        if loan.renewal_count >= policy.renewal_limit:
            raise LibraryInvalidRenewalException(
                f"Maximum renewal limit reached ({loan.renewal_count}/{policy.renewal_limit})."
            )

        # Check if copy has active reservations from other patrons
        has_waiting_holds = await db.scalar(
            select(LibraryReservation).where(
                LibraryReservation.tenant_id == tenant_id,
                LibraryReservation.catalog_item_id == catalog_item.id,
                LibraryReservation.status == LibraryReservationStatus.WAITING.value,
            )
        )
        if has_waiting_holds:
            raise LibraryInvalidRenewalException(
                "Cannot renew: item has waiting hold reservations from other patrons."
            )

        extension_days = data.requested_days or policy.loan_duration_days
        loan.due_date = max(loan.due_date, date.today()) + timedelta(days=extension_days)
        loan.renewal_count += 1
        loan.last_renewed_at = datetime.now(UTC)

        await db.flush()

        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            user_id=actor_user_id,
            action=AuditEventCategory.LIBRARY_LOAN_RENEW,
            entity_type="library_circulation_loan",
            entity_id=loan.id,
            new_values_json={
                "renewal_count": loan.renewal_count,
                "new_due_date": loan.due_date.isoformat(),
            },
        )
        return loan

    @classmethod
    async def list_loans(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        member_id: UUID | None = None,
        copy_id: UUID | None = None,
        library_id: UUID | None = None,
        status: str | None = None,
        status_filter: str | None = None,
        skip: int = 0,
        limit: int = 50,
        **kwargs: Any,
    ) -> tuple[list[LibraryCirculationLoan], int]:
        """List circulation loans with optional filters."""
        query = select(LibraryCirculationLoan).where(LibraryCirculationLoan.tenant_id == tenant_id)

        if member_id:
            query = query.where(LibraryCirculationLoan.member_id == member_id)
        if copy_id:
            query = query.where(LibraryCirculationLoan.physical_copy_id == copy_id)
        if library_id:
            query = query.where(LibraryCirculationLoan.checkout_library_id == library_id)
        st = status_filter or status
        if st and st != "ALL":
            query = query.where(LibraryCirculationLoan.status == st)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.scalar(count_query)) or 0

        query = query.order_by(desc(LibraryCirculationLoan.issued_at)).offset(skip).limit(limit)
        items = list(await db.scalars(query))
        return items, total

    # =========================================================================
    # 7. RESERVATIONS & QUEUES
    # =========================================================================

    @classmethod
    async def place_reservation(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        data: LibraryReservationCreate,
        current_user_id: UUID | None = None,
        actor_user_id: UUID | None = None,
    ) -> LibraryReservation:
        """Place a reservation hold on a catalog resource."""
        effective_user_id = actor_user_id or current_user_id or uuid4()
        catalog_item = await cls.get_catalog_item(db, tenant_id, data.catalog_item_id)
        target_member = data.member_id or data.user_id
        member = await cls.get_member(db, tenant_id, target_member)
        pickup_lib = data.pickup_library_id or getattr(data, "library_id", None)

        # Check existing active reservation by this member
        existing = await db.scalar(
            select(LibraryReservation).where(
                LibraryReservation.tenant_id == tenant_id,
                LibraryReservation.catalog_item_id == catalog_item.id,
                LibraryReservation.member_id == member.id,
                LibraryReservation.status.in_([
                    LibraryReservationStatus.WAITING.value,
                    LibraryReservationStatus.ALLOCATED_PENDING_PICKUP.value,
                ]),
            )
        )
        if existing:
            return existing

        # Calculate current queue position
        current_queue_len = (
            await db.scalar(
                select(func.count(LibraryReservation.id)).where(
                    LibraryReservation.tenant_id == tenant_id,
                    LibraryReservation.catalog_item_id == catalog_item.id,
                    LibraryReservation.status == LibraryReservationStatus.WAITING.value,
                )
            )
            or 0
        )

        res_code = f"RES-{datetime.now(UTC).strftime('%Y%m')}-{str(uuid4())[:8].upper()}"
        res = LibraryReservation(
            tenant_id=tenant_id,
            reservation_code=res_code,
            catalog_item_id=catalog_item.id,
            allocated_copy_id=None,
            member_id=member.id,
            user_id=member.user_id,
            pickup_library_id=pickup_lib,
            queue_position=current_queue_len + 1,
            priority_rank=data.priority_rank,
            reserved_at=datetime.now(UTC),
            status=LibraryReservationStatus.WAITING.value,
            metadata_json=dict(data.metadata_json or {}),
        )
        db.add(res)
        await db.flush()

        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            user_id=current_user_id,
            action=AuditEventCategory.LIBRARY_RESERVATION_PLACED,
            entity_type="library_reservation",
            entity_id=res.id,
            new_values_json={"reservation_code": res.reservation_code, "queue_position": res.queue_position},
        )
        return res

    @classmethod
    async def cancel_reservation(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        reservation_id: UUID,
        data: LibraryReservationCancelRequest,
        current_user_id: UUID,
    ) -> LibraryReservation:
        """Cancel a hold reservation and release any allocated physical copy."""
        res = await db.scalar(
            select(LibraryReservation).where(
                LibraryReservation.tenant_id == tenant_id, LibraryReservation.id == reservation_id
            )
        )
        if not res:
            raise LibraryReservationNotFoundException(str(reservation_id))

        if res.status in (LibraryReservationStatus.CANCELLED.value, LibraryReservationStatus.FULFILLED.value):
            return res

        # If copy was already allocated, release it back to available or reallocate
        if res.allocated_copy_id:
            copy = await cls.get_physical_copy(db, tenant_id, res.allocated_copy_id)
            catalog_item = await cls.get_catalog_item(db, tenant_id, copy.catalog_item_id)
            copy.circulation_status = LibraryCirculationStatus.AVAILABLE.value
            catalog_item.available_copies_count += 1

        res.status = LibraryReservationStatus.CANCELLED.value
        res.cancelled_at = datetime.now(UTC)

        await db.flush()

        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            user_id=current_user_id,
            action=AuditEventCategory.LIBRARY_RESERVATION_CANCELLED,
            entity_type="library_reservation",
            entity_id=res.id,
            new_values_json={"reason": data.reason or "Cancelled by user"},
        )
        return res

    @classmethod
    async def list_reservations(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        catalog_item_id: UUID | None = None,
        member_id: UUID | None = None,
        library_id: UUID | None = None,
        status: str | None = None,
        status_filter: str | None = None,
        skip: int = 0,
        limit: int = 50,
        **kwargs: Any,
    ) -> tuple[list[LibraryReservation], int]:
        """List reservations with filters."""
        query = select(LibraryReservation).where(LibraryReservation.tenant_id == tenant_id)

        if catalog_item_id:
            query = query.where(LibraryReservation.catalog_item_id == catalog_item_id)
        if member_id:
            query = query.where(LibraryReservation.member_id == member_id)
        if library_id:
            query = query.where(LibraryReservation.pickup_library_id == library_id)
        st = status_filter or status
        if st and st != "ALL":
            query = query.where(LibraryReservation.status == st)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.scalar(count_query)) or 0

        query = query.order_by(LibraryReservation.queue_position.asc()).offset(skip).limit(limit)
        items = list(await db.scalars(query))
        return items, total

    # =========================================================================
    # 8. FINES & WAIVERS
    # =========================================================================

    @classmethod
    async def assess_fine(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        data: LibraryFineAssessRequest,
        staff_user_id: UUID,
    ) -> LibraryFineRecord:
        """Assess a fine (damaged, lost item replacement, or manual charge)."""
        target_id = data.member_id or data.user_id
        member = await cls.get_member(db, tenant_id, target_id)
        fine_user_id = data.user_id or member.user_id
        fine_code = f"FN-{datetime.now(UTC).strftime('%Y%m')}-{str(uuid4())[:8].upper()}"

        cat_val = data.fine_category.value if hasattr(data.fine_category, "value") else str(data.fine_category)

        fine = LibraryFineRecord(
            tenant_id=tenant_id,
            fine_reference_code=fine_code,
            loan_id=data.loan_id,
            member_id=member.id,
            user_id=fine_user_id,
            fine_category=cat_val,
            base_amount=data.amount,
            waived_amount=Decimal("0.00"),
            final_payable_amount=data.amount,
            currency=data.currency,
            fine_status=LibraryFineStatus.ESTIMATED.value,
            days_overdue=data.days_overdue,
            calculation_basis=data.calculation_basis or "Manual assessment",
            assessed_at=datetime.now(UTC),
            metadata_json={},
        )
        db.add(fine)
        member.current_outstanding_fines += data.amount

        await db.flush()

        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            user_id=staff_user_id,
            action=AuditEventCategory.LIBRARY_FINE_ASSESSED,
            entity_type="library_fine_record",
            entity_id=fine.id,
            new_values_json={"fine_reference": fine.fine_reference_code, "amount": str(fine.base_amount)},
        )
        return fine

    @classmethod
    async def waive_fine(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        fine_id: UUID,
        data: LibraryFineWaiveRequest,
        authorizer_user_id: UUID | None = None,
        authorized_by_user_id: UUID | None = None,
    ) -> LibraryFineRecord:
        """Waive or adjust assessed library fine with authorized reason."""
        effective_authorizer = authorized_by_user_id or authorizer_user_id or uuid4()
        fine = await db.scalar(
            select(LibraryFineRecord).where(
                LibraryFineRecord.tenant_id == tenant_id, LibraryFineRecord.id == fine_id
            )
        )
        if not fine:
            raise LibraryFineNotFoundException(str(fine_id))

        member = await cls.get_member(db, tenant_id, fine.member_id)

        target_waive = data.waive_amount if data.waive_amount is not None else getattr(data, "waived_amount", Decimal("0.00"))
        waive_amt = min(fine.final_payable_amount, target_waive)
        fine.waived_amount += waive_amt
        fine.final_payable_amount = max(Decimal("0.00"), fine.base_amount - fine.waived_amount)
        fine.waiver_reason = data.waiver_reason
        fine.waived_by_user_id = effective_authorizer

        if fine.final_payable_amount == Decimal("0.00"):
            fine.fine_status = LibraryFineStatus.FULLY_WAIVED.value
            fine.resolved_at = datetime.now(UTC)
        else:
            fine.fine_status = LibraryFineStatus.PARTIALLY_WAIVED.value

        member.current_outstanding_fines = max(
            Decimal("0.00"), member.current_outstanding_fines - waive_amt
        )

        await db.flush()

        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            user_id=effective_authorizer,
            action=AuditEventCategory.LIBRARY_FINE_WAIVED,
            entity_type="library_fine_record",
            entity_id=fine.id,
            new_values_json={
                "waived_amount": str(waive_amt),
                "remaining": str(fine.final_payable_amount),
                "reason": data.waiver_reason,
            },
        )
        return fine

    @classmethod
    async def list_fines(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        member_id: UUID | None = None,
        fine_status: str | None = None,
        status_filter: str | None = None,
        skip: int = 0,
        limit: int = 50,
        **kwargs: Any,
    ) -> tuple[list[LibraryFineRecord], int]:
        """List fine records with filters."""
        query = select(LibraryFineRecord).where(LibraryFineRecord.tenant_id == tenant_id)

        if member_id:
            query = query.where(LibraryFineRecord.member_id == member_id)
        st = status_filter or fine_status
        if st and st != "ALL":
            query = query.where(LibraryFineRecord.fine_status == st)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.scalar(count_query)) or 0

        query = query.order_by(desc(LibraryFineRecord.assessed_at)).offset(skip).limit(limit)
        items = list(await db.scalars(query))
        return items, total

    # =========================================================================
    # 9. ACQUISITIONS & PROCUREMENT
    # =========================================================================

    @classmethod
    async def create_acquisition_request(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        data: LibraryAcquisitionCreate,
        current_user_id: UUID | None = None,
        requested_by_user_id: UUID | None = None,
    ) -> LibraryAcquisitionRequest:
        """Recommend or request a resource purchase for the library."""
        effective_user_id = requested_by_user_id or current_user_id or uuid4()
        req_code = f"ACQ-{datetime.now(UTC).strftime('%Y%m')}-{str(uuid4())[:8].upper()}"
        total_est = (data.estimated_unit_cost or Decimal("0.00")) * Decimal(str(data.number_of_copies))

        acq = LibraryAcquisitionRequest(
            tenant_id=tenant_id,
            request_code=req_code,
            title=data.title,
            author=data.author,
            publisher=data.publisher,
            isbn_or_issn=data.isbn_or_issn,
            requested_by_user_id=effective_user_id,
            department_id=data.department_id,
            library_id=data.library_id,
            justification=data.justification,
            number_of_copies=data.number_of_copies,
            estimated_unit_cost=data.estimated_unit_cost,
            total_estimated_cost=total_est,
            currency=data.currency,
            approval_status=LibraryAcquisitionStatus.REQUESTED.value,
            accession_numbers_created_json=[],
            metadata_json=dict(data.metadata_json or {}),
        )
        db.add(acq)
        await db.flush()

        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            user_id=effective_user_id,
            action=AuditEventCategory.LIBRARY_ACQUISITION_REQUESTED,
            entity_type="library_acquisition_request",
            entity_id=acq.id,
            new_values_json={"request_code": acq.request_code, "title": acq.title},
        )
        return acq

    @classmethod
    async def decide_acquisition_request(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        request_id: UUID | None = None,
        data: LibraryAcquisitionApprovalRequest = None, # type: ignore
        approver_user_id: UUID | None = None,
        reviewer_user_id: UUID | None = None,
        acquisition_id: UUID | None = None,
    ) -> LibraryAcquisitionRequest:
        """Approve or reject a library acquisition recommendation."""
        effective_id = acquisition_id or request_id
        effective_approver = reviewer_user_id or approver_user_id or uuid4()
        acq = await db.scalar(
            select(LibraryAcquisitionRequest).where(
                LibraryAcquisitionRequest.tenant_id == tenant_id,
                LibraryAcquisitionRequest.id == effective_id,
            )
        )
        if not acq:
            raise LibraryAcquisitionNotFoundException(str(effective_id))

        if data.is_approved:
            acq.approval_status = LibraryAcquisitionStatus.APPROVED.value
            acq.approved_by_user_id = effective_approver
            acq.purchase_order_reference = data.purchase_order_reference
            acq.order_date = date.today()
        else:
            acq.approval_status = LibraryAcquisitionStatus.REJECTED.value

        await db.flush()

        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            user_id=effective_approver,
            action=AuditEventCategory.LIBRARY_ACQUISITION_APPROVED,
            entity_type="library_acquisition_request",
            entity_id=acq.id,
            new_values_json={"status": acq.approval_status},
        )
        return acq

    @classmethod
    async def receive_and_accession(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        request_id: UUID | None = None,
        data: LibraryAcquisitionReceiveRequest = None, # type: ignore
        receiver_user_id: UUID | None = None,
        received_by_user_id: UUID | None = None,
        acquisition_id: UUID | None = None,
    ) -> LibraryAcquisitionRequest:
        """Record receipt of physical items and accession them into library catalog."""
        effective_id = acquisition_id or request_id
        effective_receiver = received_by_user_id or receiver_user_id or uuid4()
        acq = await db.scalar(
            select(LibraryAcquisitionRequest).where(
                LibraryAcquisitionRequest.tenant_id == tenant_id,
                LibraryAcquisitionRequest.id == effective_id,
            )
        )
        if not acq:
            raise LibraryAcquisitionNotFoundException(str(effective_id))

        acq.approval_status = LibraryAcquisitionStatus.RECEIVED.value
        acq.receipt_date = data.receipt_date
        acq.accession_numbers_created_json = data.accession_numbers

        # Auto-create or find matching catalog item
        catalog_item = await db.scalar(
            select(LibraryCatalogItem).where(
                LibraryCatalogItem.tenant_id == tenant_id,
                LibraryCatalogItem.title == acq.title,
            )
        )
        if not catalog_item:
            cat_code = f"CAT-{datetime.now(UTC).strftime('%Y%m')}-{str(uuid4())[:8].upper()}"
            catalog_item = LibraryCatalogItem(
                tenant_id=tenant_id,
                catalog_code=cat_code,
                title=acq.title,
                authors_json=[{"name": acq.author}] if acq.author else [],
                publisher=acq.publisher,
                isbn_or_issn=acq.isbn_or_issn,
                resource_type=LibraryResourceType.BOOK.value,
                classification_scheme="DDC",
                total_copies_count=0,
                available_copies_count=0,
                metadata_json={},
            )
            db.add(catalog_item)
            await db.flush()

        # Find branch to accession into
        branch_id = acq.library_id
        if not branch_id:
            default_branch = await db.scalar(
                select(LibraryBranch).where(LibraryBranch.tenant_id == tenant_id)
            )
            branch_id = default_branch.id if default_branch else uuid4()

        # Create physical copies
        for acc_num in data.accession_numbers:
            copy = LibraryPhysicalCopy(
                tenant_id=tenant_id,
                catalog_item_id=catalog_item.id,
                owning_library_id=branch_id,
                accession_number=acc_num,
                barcode=acc_num,
                acquisition_date=data.receipt_date,
                acquisition_cost=acq.estimated_unit_cost or Decimal("0.00"),
                currency=acq.currency,
                condition_grade=LibraryCopyCondition.NEW.value,
                circulation_status=LibraryCirculationStatus.AVAILABLE.value,
                metadata_json={},
            )
            db.add(copy)
            catalog_item.total_copies_count += 1
            catalog_item.available_copies_count += 1

        await db.flush()

        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            user_id=receiver_user_id,
            action=AuditEventCategory.LIBRARY_ACQUISITION_RECEIVED,
            entity_type="library_acquisition_request",
            entity_id=acq.id,
            new_values_json={"accession_count": len(data.accession_numbers)},
        )
        return acq

    @classmethod
    async def list_acquisitions(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        library_id: UUID | None = None,
        approval_status: str | None = None,
        status_filter: str | None = None,
        skip: int = 0,
        limit: int = 50,
        **kwargs: Any,
    ) -> tuple[list[LibraryAcquisitionRequest], int]:
        """List acquisition requests."""
        query = select(LibraryAcquisitionRequest).where(LibraryAcquisitionRequest.tenant_id == tenant_id)
        if library_id:
            query = query.where(LibraryAcquisitionRequest.requesting_library_id == library_id)
        st = status_filter or approval_status
        if st and st != "ALL":
            query = query.where(LibraryAcquisitionRequest.approval_status == st)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.scalar(count_query)) or 0

        query = query.order_by(desc(LibraryAcquisitionRequest.created_at)).offset(skip).limit(limit)
        items = list(await db.scalars(query))
        return items, total

    list_acquisition_requests = list_acquisitions

    # =========================================================================
    # 10. SUBSCRIPTIONS
    # =========================================================================

    @classmethod
    async def create_subscription(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        data: LibrarySubscriptionCreate,
        current_user_id: UUID,
    ) -> LibrarySubscription:
        """Register a journal or periodical subscription."""
        sub_type = data.subscription_type.value if hasattr(data.subscription_type, "value") else str(data.subscription_type)

        sub = LibrarySubscription(
            tenant_id=tenant_id,
            subscription_code=data.subscription_code,
            publication_title=data.publication_title,
            publisher_or_vendor=data.publisher_or_vendor,
            subscription_type=sub_type,
            start_date=data.start_date,
            end_date=data.end_date,
            renewal_deadline_date=data.renewal_deadline_date,
            frequency=data.frequency,
            annual_subscription_cost=data.annual_subscription_cost,
            currency=data.currency,
            access_model=data.access_model,
            concurrent_user_limit=data.concurrent_user_limit,
            status=LibrarySubscriptionStatus.ACTIVE.value,
            digital_access_url=data.digital_access_url,
            access_credentials_notes=data.access_credentials_notes,
            issues_expected_count=data.issues_expected_count,
            issues_received_count=0,
            metadata_json=dict(data.metadata_json or {}),
        )
        db.add(sub)
        await db.flush()

        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            user_id=current_user_id,
            action=AuditEventCategory.LIBRARY_SUBSCRIPTION_CREATED,
            entity_type="library_subscription",
            entity_id=sub.id,
            new_values_json={"subscription_code": sub.subscription_code, "title": sub.publication_title},
        )
        return sub

    @classmethod
    async def update_subscription(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        sub_id: UUID,
        data: LibrarySubscriptionUpdate,
        current_user_id: UUID,
    ) -> LibrarySubscription:
        """Update subscription status, renewals, or issue receipts."""
        sub = await db.scalar(
            select(LibrarySubscription).where(
                LibrarySubscription.tenant_id == tenant_id, LibrarySubscription.id == sub_id
            )
        )
        if not sub:
            raise LibrarySubscriptionNotFoundException(str(sub_id))

        update_dict = data.model_dump(exclude_unset=True)
        for key, val in update_dict.items():
            if val is not None:
                if key == "status" and hasattr(val, "value"):
                    setattr(sub, key, val.value)
                else:
                    setattr(sub, key, val)

        await db.flush()
        return sub

    @classmethod
    async def list_subscriptions(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        library_id: UUID | None = None,
        status: str | None = None,
        status_filter: str | None = None,
        skip: int = 0,
        limit: int = 50,
        **kwargs: Any,
    ) -> tuple[list[LibrarySubscription], int]:
        """List active or expiring subscriptions."""
        query = select(LibrarySubscription).where(LibrarySubscription.tenant_id == tenant_id)
        st = status_filter or status
        if st and st != "ALL":
            query = query.where(LibrarySubscription.status == st)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.scalar(count_query)) or 0

        query = query.order_by(LibrarySubscription.end_date.asc()).offset(skip).limit(limit)
        items = list(await db.scalars(query))
        return items, total

    # =========================================================================
    # 11. DIGITAL RESOURCE ACCESS
    # =========================================================================

    @classmethod
    async def log_digital_access(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        data: LibraryDigitalResourceAccessLogRequest,
        current_user_id: UUID | None = None,
        user_id: UUID | None = None,
    ) -> LibraryDigitalResourceAccess:
        """Record digital learning resource access and generate secure download token."""
        effective_user_id = user_id or current_user_id or uuid4()
        member = await db.scalar(
            select(LibraryMemberProfile).where(
                LibraryMemberProfile.tenant_id == tenant_id,
                LibraryMemberProfile.user_id == effective_user_id,
            )
        )

        token = str(uuid4())
        token_expiry = datetime.now(UTC) + timedelta(hours=2)

        access_log = LibraryDigitalResourceAccess(
            tenant_id=tenant_id,
            catalog_item_id=data.catalog_item_id,
            subscription_id=data.subscription_id,
            user_id=effective_user_id,
            member_id=member.id if member else None,
            access_timestamp=datetime.now(UTC),
            ip_address=data.ip_address or "127.0.0.1",
            access_type=data.access_type,
            download_token=token,
            token_expires_at=token_expiry,
            bytes_transferred=data.bytes_transferred,
            metadata_json={},
        )
        db.add(access_log)
        await db.flush()

        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            user_id=effective_user_id,
            action=AuditEventCategory.LIBRARY_DIGITAL_ACCESS_LOGGED,
            entity_type="library_digital_resource_access",
            entity_id=access_log.id,
            new_values_json={"access_type": data.access_type},
        )
        return access_log

    # =========================================================================
    # 12. INVENTORY STOCK AUDITS
    # =========================================================================

    @classmethod
    async def start_inventory_audit(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        data: LibraryInventoryAuditCreate,
        current_user_id: UUID | None = None,
        auditor_user_id: UUID | None = None,
    ) -> LibraryInventoryAudit:
        """Initialize stock verification session and capture expected copy count."""
        effective_auditor = auditor_user_id or current_user_id or uuid4()
        # Calculate expected copies in this library branch
        expected_count = (
            await db.scalar(
                select(func.count(LibraryPhysicalCopy.id)).where(
                    LibraryPhysicalCopy.tenant_id == tenant_id,
                    LibraryPhysicalCopy.owning_library_id == data.library_id,
                    LibraryPhysicalCopy.circulation_status != LibraryCirculationStatus.WITHDRAWN.value,
                )
            )
            or 0
        )

        audit = LibraryInventoryAudit(
            tenant_id=tenant_id,
            audit_code=data.audit_code,
            title=data.title,
            library_id=data.library_id,
            location_section=data.location_section,
            audit_scope=data.audit_scope,
            start_date=date.today(),
            status=LibraryInventoryAuditStatus.IN_PROGRESS.value,
            auditor_user_id=effective_auditor,
            total_expected_copies=expected_count,
            verified_present_copies=0,
            missing_copies_count=0,
            damaged_copies_count=0,
            misplaced_copies_count=0,
            metadata_json=dict(data.metadata_json or {}),
        )
        db.add(audit)
        await db.flush()

        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            user_id=effective_auditor,
            action=AuditEventCategory.LIBRARY_INVENTORY_AUDIT_STARTED,
            entity_type="library_inventory_audit",
            entity_id=audit.id,
            new_values_json={"audit_code": audit.audit_code, "expected": expected_count},
        )
        return audit

    @classmethod
    async def scan_inventory_item(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        audit_id: UUID,
        data: LibraryInventoryAuditItemScanRequest,
        current_user_id: UUID | None = None,
        auditor_user_id: UUID | None = None,
    ) -> LibraryInventoryAuditItem:
        """Scan a physical copy finding in an active inventory audit."""
        effective_auditor = auditor_user_id or current_user_id or uuid4()
        audit = await db.scalar(
            select(LibraryInventoryAudit).where(
                LibraryInventoryAudit.tenant_id == tenant_id, LibraryInventoryAudit.id == audit_id
            )
        )
        if not audit:
            raise LibraryAuditNotFoundException(str(audit_id))

        copy = await cls.get_physical_copy(db, tenant_id, data.copy_id)

        scan_status = (
            data.scanned_status.value
            if hasattr(data.scanned_status, "value")
            else str(data.scanned_status)
        )

        item = LibraryInventoryAuditItem(
            tenant_id=tenant_id,
            audit_id=audit.id,
            copy_id=copy.id,
            accession_number=data.accession_number,
            scanned_barcode=data.scanned_barcode or copy.barcode,
            expected_status=copy.circulation_status,
            scanned_status=scan_status,
            shelf_location_found=data.shelf_location_found or copy.shelf_location,
            discrepancy_resolved=False,
            resolution_action=data.notes,
            audited_at=datetime.now(UTC),
            audited_by_user_id=effective_auditor,
            metadata_json={},
        )
        db.add(item)

        # Update running audit tally
        if scan_status == LibraryAuditScanResult.PRESENT_ON_SHELF.value:
            audit.verified_present_copies += 1
            copy.last_inventory_check_date = date.today()
        elif scan_status == LibraryAuditScanResult.MISSING.value:
            audit.missing_copies_count += 1
        elif scan_status == LibraryAuditScanResult.DAMAGED.value:
            audit.damaged_copies_count += 1
        elif scan_status == LibraryAuditScanResult.MISPLACED.value:
            audit.misplaced_copies_count += 1

        await db.flush()
        return item

    @classmethod
    async def reconcile_and_complete_audit(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        audit_id: UUID,
        data: LibraryInventoryAuditReconcileRequest,
        approver_user_id: UUID | None = None,
        current_user_id: UUID | None = None,
    ) -> LibraryInventoryAudit:
        """Reconcile and finalize physical stock verification audit."""
        effective_approver = approver_user_id or current_user_id or uuid4()
        audit = await db.scalar(
            select(LibraryInventoryAudit).where(
                LibraryInventoryAudit.tenant_id == tenant_id, LibraryInventoryAudit.id == audit_id
            )
        )
        if not audit:
            raise LibraryAuditNotFoundException(str(audit_id))

        audit.status = LibraryInventoryAuditStatus.COMPLETED.value
        audit.end_date = date.today()
        audit.reconciliation_notes = data.reconciliation_notes
        audit.approved_by_user_id = effective_approver

        await db.flush()

        await create_audit_entry(
            db=db,
            tenant_id=tenant_id,
            user_id=effective_approver,
            action=AuditEventCategory.LIBRARY_INVENTORY_AUDIT_COMPLETED,
            entity_type="library_inventory_audit",
            entity_id=audit.id,
            new_values_json={
                "verified": audit.verified_present_copies,
                "missing": audit.missing_copies_count,
            },
        )
        return audit

    # =========================================================================
    # 13. ANALYTICS & DEADLINE SWEEP
    # =========================================================================

    @classmethod
    async def get_analytics_summary(
        cls, db: AsyncSession, tenant_id: UUID
    ) -> dict[str, Any]:
        """Aggregate real-time library collection, circulation, and financial metrics."""
        total_branches = (
            await db.scalar(
                select(func.count(LibraryBranch.id)).where(LibraryBranch.tenant_id == tenant_id)
            )
            or 0
        )
        total_catalog_titles = (
            await db.scalar(
                select(func.count(LibraryCatalogItem.id)).where(
                    LibraryCatalogItem.tenant_id == tenant_id
                )
            )
            or 0
        )
        total_physical_copies = (
            await db.scalar(
                select(func.count(LibraryPhysicalCopy.id)).where(
                    LibraryPhysicalCopy.tenant_id == tenant_id
                )
            )
            or 0
        )
        available_copies = (
            await db.scalar(
                select(func.count(LibraryPhysicalCopy.id)).where(
                    LibraryPhysicalCopy.tenant_id == tenant_id,
                    LibraryPhysicalCopy.circulation_status == LibraryCirculationStatus.AVAILABLE.value,
                )
            )
            or 0
        )
        total_active_members = (
            await db.scalar(
                select(func.count(LibraryMemberProfile.id)).where(
                    LibraryMemberProfile.tenant_id == tenant_id,
                    LibraryMemberProfile.status == LibraryMemberStatus.ACTIVE.value,
                )
            )
            or 0
        )
        total_active_loans = (
            await db.scalar(
                select(func.count(LibraryCirculationLoan.id)).where(
                    LibraryCirculationLoan.tenant_id == tenant_id,
                    LibraryCirculationLoan.status == LibraryLoanStatus.ACTIVE.value,
                )
            )
            or 0
        )
        total_overdue_loans = (
            await db.scalar(
                select(func.count(LibraryCirculationLoan.id)).where(
                    LibraryCirculationLoan.tenant_id == tenant_id,
                    LibraryCirculationLoan.status == LibraryLoanStatus.ACTIVE.value,
                    LibraryCirculationLoan.due_date < date.today(),
                )
            )
            or 0
        )
        total_active_reservations = (
            await db.scalar(
                select(func.count(LibraryReservation.id)).where(
                    LibraryReservation.tenant_id == tenant_id,
                    LibraryReservation.status.in_([
                        LibraryReservationStatus.WAITING.value,
                        LibraryReservationStatus.ALLOCATED_PENDING_PICKUP.value,
                    ]),
                )
            )
            or 0
        )
        total_fines_val = (
            await db.scalar(
                select(func.sum(LibraryFineRecord.final_payable_amount)).where(
                    LibraryFineRecord.tenant_id == tenant_id,
                    LibraryFineRecord.fine_status.in_([
                        LibraryFineStatus.ESTIMATED.value,
                        LibraryFineStatus.POSTED_TO_FINANCE.value,
                    ]),
                )
            )
            or Decimal("0.00")
        )
        total_subscriptions = (
            await db.scalar(
                select(func.count(LibrarySubscription.id)).where(
                    LibrarySubscription.tenant_id == tenant_id
                )
            )
            or 0
        )
        active_subscriptions = (
            await db.scalar(
                select(func.count(LibrarySubscription.id)).where(
                    LibrarySubscription.tenant_id == tenant_id,
                    LibrarySubscription.status == LibrarySubscriptionStatus.ACTIVE.value,
                )
            )
            or 0
        )
        pending_acquisitions = (
            await db.scalar(
                select(func.count(LibraryAcquisitionRequest.id)).where(
                    LibraryAcquisitionRequest.tenant_id == tenant_id,
                    LibraryAcquisitionRequest.approval_status == LibraryAcquisitionStatus.REQUESTED.value,
                )
            )
            or 0
        )
        active_audits = (
            await db.scalar(
                select(func.count(LibraryInventoryAudit.id)).where(
                    LibraryInventoryAudit.tenant_id == tenant_id,
                    LibraryInventoryAudit.status == LibraryInventoryAuditStatus.IN_PROGRESS.value,
                )
            )
            or 0
        )

        circ_rate = (
            (total_active_loans / total_physical_copies * 100.0)
            if total_physical_copies > 0
            else 0.0
        )

        return {
            "total_branches": total_branches,
            "total_catalog_titles": total_catalog_titles,
            "total_physical_copies": total_physical_copies,
            "available_copies": available_copies,
            "total_active_members": total_active_members,
            "total_active_loans": total_active_loans,
            "total_overdue_loans": total_overdue_loans,
            "total_active_reservations": total_active_reservations,
            "total_outstanding_fines": total_fines_val,
            "total_subscriptions": total_subscriptions,
            "active_subscriptions": active_subscriptions,
            "pending_acquisitions": pending_acquisitions,
            "active_inventory_audits": active_audits,
            "circulation_rate_percentage": round(circ_rate, 2),
        }

    @classmethod
    async def sweep_deadlines_and_compliance(
        cls, db: AsyncSession, tenant_id: UUID
    ) -> dict[str, Any]:
        """Audit background sweep: flag overdues, assess fines, expire holds, check subscriptions."""
        now = datetime.now(UTC)
        today = date.today()

        # 1. Flag overdue active loans
        overdue_loans = list(
            await db.scalars(
                select(LibraryCirculationLoan).where(
                    LibraryCirculationLoan.tenant_id == tenant_id,
                    LibraryCirculationLoan.status == LibraryLoanStatus.ACTIVE.value,
                    LibraryCirculationLoan.due_date < today,
                )
            )
        )
        total_fines_computed = Decimal("0.00")
        for loan in overdue_loans:
            loan.status = LibraryLoanStatus.OVERDUE.value
            overdue_days = (today - loan.due_date).days
            loan.calculated_fine_amount = Decimal(str(overdue_days)) * Decimal("1.00")
            total_fines_computed += loan.calculated_fine_amount

        # 2. Release expired reservations
        expired_reservations = list(
            await db.scalars(
                select(LibraryReservation).where(
                    LibraryReservation.tenant_id == tenant_id,
                    LibraryReservation.status == LibraryReservationStatus.ALLOCATED_PENDING_PICKUP.value,
                    LibraryReservation.pickup_deadline < now,
                )
            )
        )
        released_count = 0
        for res in expired_reservations:
            res.status = LibraryReservationStatus.EXPIRED.value
            res.expired_at = now
            if res.allocated_copy_id:
                copy = await db.scalar(
                    select(LibraryPhysicalCopy).where(
                        LibraryPhysicalCopy.tenant_id == tenant_id,
                        LibraryPhysicalCopy.id == res.allocated_copy_id,
                    )
                )
                if copy:
                    copy.circulation_status = LibraryCirculationStatus.AVAILABLE.value
                    cat = await db.scalar(
                        select(LibraryCatalogItem).where(
                            LibraryCatalogItem.tenant_id == tenant_id,
                            LibraryCatalogItem.id == copy.catalog_item_id,
                        )
                    )
                    if cat:
                        cat.available_copies_count += 1
            released_count += 1

        # 3. Flag subscriptions expiring within 30 days
        expiry_threshold = today + timedelta(days=30)
        expiring_subs = list(
            await db.scalars(
                select(LibrarySubscription).where(
                    LibrarySubscription.tenant_id == tenant_id,
                    LibrarySubscription.status == LibrarySubscriptionStatus.ACTIVE.value,
                    LibrarySubscription.end_date <= expiry_threshold,
                )
            )
        )
        for sub in expiring_subs:
            sub.status = LibrarySubscriptionStatus.PENDING_RENEWAL.value

        await db.flush()

        return {
            "processed_at": now,
            "overdue_loans_flagged": len(overdue_loans),
            "fines_computed_amount": total_fines_computed,
            "expired_reservations_released": released_count,
            "expiring_subscriptions_flagged": len(expiring_subs),
        }

    # =========================================================================
    # SUPPLEMENTARY HELPERS & COMPATIBILITY ALIASES
    # =========================================================================

    @classmethod
    async def get_reservation(
        cls, db: AsyncSession, tenant_id: UUID, reservation_id: UUID
    ) -> LibraryReservation:
        """Get single reservation record."""
        res = await db.scalar(
            select(LibraryReservation).where(
                LibraryReservation.tenant_id == tenant_id, LibraryReservation.id == reservation_id
            )
        )
        if not res:
            raise LibraryReservationNotFoundException(str(reservation_id))
        return res

    @classmethod
    async def get_loan(
        cls, db: AsyncSession, tenant_id: UUID, loan_id: UUID
    ) -> LibraryCirculationLoan:
        """Get single loan record."""
        loan = await db.scalar(
            select(LibraryCirculationLoan).where(
                LibraryCirculationLoan.tenant_id == tenant_id, LibraryCirculationLoan.id == loan_id
            )
        )
        if not loan:
            raise LibraryLoanNotFoundException(str(loan_id))
        return loan

    @classmethod
    async def get_inventory_audit(
        cls, db: AsyncSession, tenant_id: UUID, audit_id: UUID
    ) -> LibraryInventoryAudit:
        """Get single inventory audit with counts."""
        audit = await db.scalar(
            select(LibraryInventoryAudit).where(
                LibraryInventoryAudit.tenant_id == tenant_id, LibraryInventoryAudit.id == audit_id
            )
        )
        if not audit:
            raise LibraryAuditNotFoundException(str(audit_id))
        return audit

    @classmethod
    async def list_inventory_audits(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        library_id: UUID | None = None,
        status_filter: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[LibraryInventoryAudit], int]:
        """List inventory audits with filtering."""
        query = select(LibraryInventoryAudit).where(LibraryInventoryAudit.tenant_id == tenant_id)
        if library_id:
            query = query.where(LibraryInventoryAudit.library_id == library_id)
        if status_filter:
            query = query.where(LibraryInventoryAudit.status == status_filter)
        total = (await db.scalar(select(func.count()).select_from(query.subquery()))) or 0
        items = list(
            await db.scalars(
                query.order_by(LibraryInventoryAudit.created_at.desc()).offset(skip).limit(limit)
            )
        )
        return items, total

    @classmethod
    async def get_member_by_user_id(
        cls, db: AsyncSession, tenant_id: UUID, user_id: UUID
    ) -> LibraryMemberProfile | None:
        """Get patron profile for a specific user ID."""
        return await db.scalar(
            select(LibraryMemberProfile).where(
                LibraryMemberProfile.tenant_id == tenant_id, LibraryMemberProfile.user_id == user_id
            )
        )

    @classmethod
    async def list_my_loans(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        status_filter: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[LibraryCirculationLoan], int]:
        """List loans for a specific patron user."""
        query = select(LibraryCirculationLoan).where(
            LibraryCirculationLoan.tenant_id == tenant_id, LibraryCirculationLoan.user_id == user_id
        )
        if status_filter:
            query = query.where(LibraryCirculationLoan.status == status_filter)
        total = (await db.scalar(select(func.count()).select_from(query.subquery()))) or 0
        items = list(
            await db.scalars(
                query.order_by(LibraryCirculationLoan.created_at.desc()).offset(skip).limit(limit)
            )
        )
        return items, total

    @classmethod
    async def list_my_reservations(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        status_filter: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[LibraryReservation], int]:
        """List hold reservations for a specific patron user."""
        query = select(LibraryReservation).where(
            LibraryReservation.tenant_id == tenant_id, LibraryReservation.user_id == user_id
        )
        if status_filter:
            query = query.where(LibraryReservation.status == status_filter)
        total = (await db.scalar(select(func.count()).select_from(query.subquery()))) or 0
        items = list(
            await db.scalars(
                query.order_by(LibraryReservation.created_at.desc()).offset(skip).limit(limit)
            )
        )
        return items, total

    @classmethod
    async def list_my_fines(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        status_filter: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[LibraryFineRecord], int]:
        """List fines for a specific patron user."""
        query = select(LibraryFineRecord).where(
            LibraryFineRecord.tenant_id == tenant_id, LibraryFineRecord.user_id == user_id
        )
        if status_filter:
            query = query.where(LibraryFineRecord.fine_status == status_filter)
        total = (await db.scalar(select(func.count()).select_from(query.subquery()))) or 0
        items = list(
            await db.scalars(
                query.order_by(LibraryFineRecord.created_at.desc()).offset(skip).limit(limit)
            )
        )
        return items, total

    @classmethod
    async def generate_digital_access_token(
        cls, db: AsyncSession, tenant_id: UUID, catalog_item_id: UUID, user_id: UUID
    ) -> dict[str, Any]:
        """Validate eligibility and return expiring digital token."""
        catalog_item = await cls.get_catalog_item(db, tenant_id, catalog_item_id)
        if not catalog_item.is_digital:
            raise LibraryDigitalAccessRestrictedException(
                "This catalog item does not have digital access enabled."
            )
        token = f"tok_{uuid4().hex}"
        expires_at = datetime.now(UTC) + timedelta(hours=2)
        access_url = catalog_item.digital_access_url or f"/api/v1/library/digital-access/download/{token}"
        await cls.log_digital_access(
            db=db,
            tenant_id=tenant_id,
            data=LibraryDigitalResourceAccessLogRequest(
                catalog_item_id=catalog_item.id, access_type="TOKEN_REQUEST"
            ),
            user_id=user_id,
        )
        return {
            "catalog_item_id": catalog_item_id,
            "download_token": token,
            "token_expires_at": expires_at,
            "access_url": access_url,
        }

    @classmethod
    async def list_digital_access_logs(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        catalog_item_id: UUID | None = None,
        user_id: UUID | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[LibraryDigitalResourceAccess], int]:
        """List digital resource access logs."""
        query = select(LibraryDigitalResourceAccess).where(
            LibraryDigitalResourceAccess.tenant_id == tenant_id
        )
        if catalog_item_id:
            query = query.where(LibraryDigitalResourceAccess.catalog_item_id == catalog_item_id)
        if user_id:
            query = query.where(LibraryDigitalResourceAccess.user_id == user_id)
        total = (await db.scalar(select(func.count()).select_from(query.subquery()))) or 0
        items = list(
            await db.scalars(
                query.order_by(LibraryDigitalResourceAccess.access_timestamp.desc())
                .offset(skip)
                .limit(limit)
            )
        )
        return items, total

    @classmethod
    async def post_fine_to_finance(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        fine_id: UUID,
        data: Any,
        current_user_id: UUID,
    ) -> LibraryFineRecord:
        """Mark fine as posted to finance module."""
        fine = await db.scalar(
            select(LibraryFineRecord).where(
                LibraryFineRecord.tenant_id == tenant_id, LibraryFineRecord.id == fine_id
            )
        )
        if not fine:
            raise LibraryFineNotFoundException(str(fine_id))
        fine.finance_invoice_id = data.finance_invoice_id
        fine.finance_payment_reference = data.payment_reference
        fine.fine_status = LibraryFineStatus.POSTED_TO_FINANCE.value
        await db.flush()
        return fine

    @classmethod
    async def update_policy(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        policy_id: UUID,
        data: Any,
        current_user_id: UUID,
    ) -> LibraryLendingPolicy:
        """Update lending policy attributes."""
        policy = await db.scalar(
            select(LibraryLendingPolicy).where(
                LibraryLendingPolicy.tenant_id == tenant_id, LibraryLendingPolicy.id == policy_id
            )
        )
        if not policy:
            raise LibraryBranchNotFoundException(f"Policy {policy_id} not found.")
        update_dict = data.model_dump(exclude_unset=True)
        for k, v in update_dict.items():
            if v is not None:
                setattr(policy, k, v)
        await db.flush()
        return policy

    # Compatibility method aliases
    create_policy = create_lending_policy
    list_policies = list_lending_policies
    create_physical_copy = register_physical_copy
    create_member = enroll_member
    checkout_copy = checkout_loan
    return_copy = return_loan
    create_reservation = place_reservation
    review_acquisition_request = decide_acquisition_request
    receive_acquisition = receive_and_accession
    create_inventory_audit = start_inventory_audit
    record_audit_scan = scan_inventory_item
    reconcile_inventory_audit = reconcile_and_complete_audit

