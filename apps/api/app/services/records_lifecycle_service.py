"""Enterprise Records Lifecycle, Retention, Archival & Legal Hold Domain Service (Step 41).

Central domain service orchestrating:
- Automated Record Category seeding and catalog management
- Centralized Records Registry indexing authoritative domain records without redundant sensitive copies
- Retention policy authoring, versioning, publication, and rule evaluation
- 12-state controlled Record Lifecycle State Machine with audit histories
- Cryptographic archival manifests, SHA-256 checksum verification, and audited retrieval
- High-precedence Administrative and Legal Holds, scope matching, and hold release recalculation
- Controlled disposition workflow with dry-run previews, separation of duties, and Certificates
- Bounded batch scheduled lifecycle sweeps with operational metrics
"""

from datetime import UTC, datetime, timedelta
import hashlib
import json
import logging
import secrets
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit import AuditEventCategory, build_audit_entry
from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    DispositionApprovalRequiredException,
    InvalidRecordLifecycleTransitionException,
    LegalHoldActiveException,
    NotFoundException,
    PermissionDeniedException,
    RecordArchivalException,
    RecordCategoryNotFoundException,
    RecordNotFoundException,
    RetentionPolicyNotFoundException,
    ValidationException,
)
from app.core.storage import get_document_storage
from app.models.academics import CourseEnrollment
from app.models.documents import Document
from app.models.finance import Invoice
from app.models.infrastructure import HostelAllocation
from app.models.records_lifecycle import (
    ArchivalStatus,
    DispositionItemStatus,
    DispositionMethod,
    DispositionRequestStatus,
    LegalHoldScope,
    LegalHoldStatus,
    PolicyScope,
    RecordArchivalAccessLog,
    RecordArchivalRecord,
    RecordCategory,
    RecordDispositionCertificate,
    RecordDispositionItem,
    RecordDispositionRequest,
    RecordLegalHold,
    RecordLegalHoldAssociation,
    RecordLifecycleHistory,
    RecordLifecycleScheduledRun,
    RecordLifecycleState,
    RecordRegistryEntry,
    RetentionPolicyDefinition,
    RetentionPolicyStatus,
    RetentionPolicyVersionRecord,
    RetentionTriggerEvent,
    RetentionUnit,
    ScheduledRunStatus,
    ScheduledRunType,
)
from app.schemas.records_lifecycle import (
    RecordArchivalExecuteRequest,
    RecordCategoryCreate,
    RecordCategoryUpdate,
    RecordDispositionApproveRequest,
    RecordDispositionPreviewItem,
    RecordDispositionPreviewRequest,
    RecordDispositionPreviewResponse,
    RecordDispositionRejectRequest,
    RecordDispositionRequestCreate,
    RecordLegalHoldCreate,
    RecordLegalHoldReleaseRequest,
    RecordLifecycleDashboardSummary,
    RecordLifecycleTransitionRequest,
    RecordRegistryCreate,
    RetentionEvaluationResponse,
    RetentionPolicyCreate,
    RetentionPolicyPublishRequest,
    RetentionPolicyUpdate,
)

logger = logging.getLogger("campusos.records_lifecycle")


class RecordsLifecycleService:
    """Enterprise domain service for Records Lifecycle, Retention, Archival and Legal Holds."""

    # =========================================================================
    # 1. RECORD CATEGORY CATALOG & SEEDING
    # =========================================================================

    DEFAULT_CATEGORIES = [
        {
            "code": "STUDENT_ACADEMIC",
            "name": "Student Academic Records & Transcripts",
            "description": "Permanent academic performance, semester transcripts, degrees, and certificates.",
            "confidentiality": "CONFIDENTIAL",
            "default_retention_years": 30,
            "statutory_authority": "UGC / AICTE Academic Ordinances",
        },
        {
            "code": "STUDENT_ADMISSION",
            "name": "Student Admissions & Enrolment Files",
            "description": "Application forms, identity verification, qualification certificates, and quota claims.",
            "confidentiality": "CONFIDENTIAL",
            "default_retention_years": 10,
            "statutory_authority": "Directorate of Technical Education",
        },
        {
            "code": "ATTENDANCE_EXAMS",
            "name": "Attendance Registers & Examination Marks",
            "description": "Course session registers, internal assessment evaluations, and raw examination scores.",
            "confidentiality": "INTERNAL",
            "default_retention_years": 5,
            "statutory_authority": "University Examination Regulations",
        },
        {
            "code": "FINANCE_ACCOUNTING",
            "name": "Financial Ledgers, Invoices & Fee Receipts",
            "description": "Fee structures, student invoices, payment receipts, fee refunds, and bank reconciliation files.",
            "confidentiality": "RESTRICTED",
            "default_retention_years": 8,
            "statutory_authority": "Income Tax Act / CAG Statutory Audit",
        },
        {
            "code": "EMPLOYEE_HR",
            "name": "Faculty & Staff Employment Records",
            "description": "Staff appointments, promotions, service registers, leave balances, and appraisals.",
            "confidentiality": "RESTRICTED",
            "default_retention_years": 10,
            "statutory_authority": "EPFO / Labor Ministry Statutory Mandates",
        },
        {
            "code": "GOVERNANCE_ADMIN",
            "name": "Institutional Governance & Senate Minutes",
            "description": "Governing body proceedings, Academic Council resolutions, board charters, and affiliations.",
            "confidentiality": "INTERNAL",
            "default_retention_years": 50,
            "statutory_authority": "Institution Charter & Trust Statutes",
        },
        {
            "code": "CONTRACTS_COMPLIANCE",
            "name": "Legal Contracts, Vendor Agreements & Approvals",
            "description": "Procurement agreements, software licenses, statutory approvals, and campus leases.",
            "confidentiality": "RESTRICTED",
            "default_retention_years": 7,
            "statutory_authority": "Indian Contract Act & Statutory Compliance",
        },
        {
            "code": "PLACEMENT_INTERNSHIP",
            "name": "Career Placement & Internship Outcomes",
            "description": "Placement drive rosters, company offer letters, internship certificates, and CTC records.",
            "confidentiality": "INTERNAL",
            "default_retention_years": 5,
            "statutory_authority": "Institutional Career Services Policy",
        },
        {
            "code": "GENERAL_DOCUMENTS",
            "name": "General Institutional Documents & Circulars",
            "description": "Administrative circulars, event permissions, campus notices, and general correspondence.",
            "confidentiality": "INTERNAL",
            "default_retention_years": 3,
            "statutory_authority": "Institutional Office Manual",
        },
    ]

    @classmethod
    async def seed_default_categories(cls, db: AsyncSession, tenant_id: UUID) -> list[RecordCategory]:
        """Seeds standard statutory institutional record categories if not already present."""
        existing = await db.scalars(select(RecordCategory).where(RecordCategory.tenant_id == tenant_id))
        existing_codes = {c.code for c in existing}

        seeded: list[RecordCategory] = []
        now = datetime.now(UTC)
        for cat in cls.DEFAULT_CATEGORIES:
            if cat["code"] not in existing_codes:
                record_cat = RecordCategory(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    code=cat["code"],
                    name=cat["name"],
                    description=cat["description"],
                    confidentiality=cat["confidentiality"],
                    default_retention_years=cat["default_retention_years"],
                    statutory_authority=cat["statutory_authority"],
                    is_active=True,
                    metadata_json={},
                    created_at=now,
                    updated_at=now,
                )
                db.add(record_cat)
                seeded.append(record_cat)

        if seeded:
            await db.flush()
        return seeded

    @classmethod
    async def list_categories(
        cls, db: AsyncSession, tenant_id: UUID, is_active: bool | None = None
    ) -> list[RecordCategory]:
        """Lists record categories for tenant, auto-seeding default categories if empty."""
        stmt = select(RecordCategory).where(RecordCategory.tenant_id == tenant_id)
        if is_active is not None:
            stmt = stmt.where(RecordCategory.is_active == is_active)
        stmt = stmt.order_by(RecordCategory.code.asc())
        categories = list((await db.scalars(stmt)).all())

        if not categories:
            await cls.seed_default_categories(db, tenant_id)
            categories = list((await db.scalars(stmt)).all())

        return categories

    @classmethod
    async def get_category(cls, db: AsyncSession, tenant_id: UUID, code_or_id: str | UUID) -> RecordCategory:
        """Fetch category by UUID or alphanumeric code ensuring strict tenant isolation."""
        if isinstance(code_or_id, UUID):
            stmt = select(RecordCategory).where(and_(RecordCategory.id == code_or_id, RecordCategory.tenant_id == tenant_id))
        else:
            stmt = select(RecordCategory).where(
                and_(RecordCategory.code == str(code_or_id).upper().strip(), RecordCategory.tenant_id == tenant_id)
            )
        category = (await db.scalars(stmt)).first()
        if not category:
            await cls.seed_default_categories(db, tenant_id)
            category = (await db.scalars(stmt)).first()
        if not category:
            raise RecordCategoryNotFoundException(code_or_id)
        return category

    @classmethod
    async def create_category(
        cls, db: AsyncSession, tenant_id: UUID, payload: RecordCategoryCreate, actor_id: UUID | None = None
    ) -> RecordCategory:
        """Create a custom institutional record category."""
        clean_code = payload.code.upper().strip()
        existing = await db.scalar(
            select(RecordCategory).where(and_(RecordCategory.tenant_id == tenant_id, RecordCategory.code == clean_code))
        )
        if existing:
            raise ConflictException(f"Record category with code '{clean_code}' already exists in this institution.")

        now = datetime.now(UTC)
        category = RecordCategory(
            id=uuid4(),
            tenant_id=tenant_id,
            code=clean_code,
            name=payload.name.strip(),
            description=payload.description,
            confidentiality=payload.confidentiality.upper(),
            default_retention_years=payload.default_retention_years,
            statutory_authority=payload.statutory_authority,
            is_active=payload.is_active,
            metadata_json=payload.metadata_json or {},
            created_at=now,
            updated_at=now,
        )
        db.add(category)
        await db.flush()
        await db.refresh(category)
        return category

    @classmethod
    async def update_category(
        cls, db: AsyncSession, tenant_id: UUID, category_id: UUID, payload: RecordCategoryUpdate, actor_id: UUID | None = None
    ) -> RecordCategory:
        """Update record category parameters."""
        category = await cls.get_category(db, tenant_id, category_id)
        if payload.name is not None:
            category.name = payload.name.strip()
        if payload.description is not None:
            category.description = payload.description
        if payload.confidentiality is not None:
            category.confidentiality = payload.confidentiality.upper()
        if payload.default_retention_years is not None:
            category.default_retention_years = payload.default_retention_years
        if payload.statutory_authority is not None:
            category.statutory_authority = payload.statutory_authority
        if payload.is_active is not None:
            category.is_active = payload.is_active
        if payload.metadata_json is not None:
            category.metadata_json = payload.metadata_json

        category.updated_at = datetime.now(UTC)
        await db.flush()
        await db.refresh(category)
        return category

    # =========================================================================
    # 2. RETENTION POLICY SPECIFICATIONS & VERSIONING
    # =========================================================================

    @classmethod
    async def create_retention_policy(
        cls, db: AsyncSession, tenant_id: UUID, payload: RetentionPolicyCreate, actor_id: UUID | None = None
    ) -> RetentionPolicyDefinition:
        """Create a new versioned institutional retention policy in DRAFT status."""
        clean_code = payload.code.upper().strip()
        existing = await db.scalar(
            select(RetentionPolicyDefinition).where(
                and_(RetentionPolicyDefinition.tenant_id == tenant_id, RetentionPolicyDefinition.code == clean_code)
            )
        )
        if existing:
            raise ConflictException(f"Retention policy with code '{clean_code}' already exists.")

        # Validate category exists
        await cls.get_category(db, tenant_id, payload.category_code)

        now = datetime.now(UTC)
        policy_id = uuid4()
        policy = RetentionPolicyDefinition(
            id=policy_id,
            tenant_id=tenant_id,
            code=clean_code,
            name=payload.name.strip(),
            description=payload.description,
            category_code=payload.category_code.upper().strip(),
            scope=payload.scope,
            scope_target=payload.scope_target,
            retention_duration=payload.retention_duration,
            retention_unit=payload.retention_unit,
            trigger_event=payload.trigger_event,
            review_required=payload.review_required,
            archive_required=payload.archive_required,
            disposition_method=payload.disposition_method,
            approval_required=payload.approval_required,
            effective_from=payload.effective_from or now,
            effective_until=payload.effective_until,
            status=RetentionPolicyStatus.DRAFT,
            current_version=1,
            owner_user_id=actor_id,
            metadata_json=payload.metadata_json or {},
            created_at=now,
            updated_at=now,
        )
        db.add(policy)

        # Initial draft version record
        version = RetentionPolicyVersionRecord(
            id=uuid4(),
            tenant_id=tenant_id,
            policy_id=policy_id,
            version_number=1,
            status=RetentionPolicyStatus.DRAFT,
            rules_json={
                "retention_duration": policy.retention_duration,
                "retention_unit": policy.retention_unit,
                "trigger_event": policy.trigger_event,
                "disposition_method": policy.disposition_method,
                "review_required": policy.review_required,
                "archive_required": policy.archive_required,
                "approval_required": policy.approval_required,
            },
            change_summary="Initial policy authoring",
            effective_from=policy.effective_from,
            effective_until=policy.effective_until,
            created_by_user_id=actor_id,
            created_at=now,
            updated_at=now,
        )
        policy.versions.append(version)
        db.add(version)

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.RETENTION_POLICY_CREATED,
                entity_type="RetentionPolicyDefinition",
                entity_id=policy.id,
                user_id=actor_id,
                new_values_json={"code": clean_code, "category": policy.category_code, "version": 1},
            )
        )

        await db.flush()
        await db.refresh(policy)
        return policy

    @classmethod
    async def publish_retention_policy(
        cls, db: AsyncSession, tenant_id: UUID, policy_id: UUID, payload: RetentionPolicyPublishRequest, actor_id: UUID | None = None
    ) -> RetentionPolicyDefinition:
        """Formally publishes and activates a retention policy, creating an immutable published version."""
        stmt = (
            select(RetentionPolicyDefinition)
            .options(selectinload(RetentionPolicyDefinition.versions))
            .where(and_(RetentionPolicyDefinition.id == policy_id, RetentionPolicyDefinition.tenant_id == tenant_id))
        )
        policy = (await db.scalars(stmt)).first()
        if not policy:
            raise RetentionPolicyNotFoundException(policy_id)

        now = datetime.now(UTC)
        policy.status = RetentionPolicyStatus.PUBLISHED
        policy.approved_by_user_id = actor_id
        policy.approved_at = now
        policy.updated_at = now

        # Update latest version to PUBLISHED
        latest_version = max(policy.versions, key=lambda v: v.version_number, default=None)
        if latest_version:
            latest_version.status = RetentionPolicyStatus.PUBLISHED
            latest_version.change_summary = payload.change_summary
            latest_version.updated_at = now

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.RETENTION_POLICY_PUBLISHED,
                entity_type="RetentionPolicyDefinition",
                entity_id=policy.id,
                user_id=actor_id,
                new_values_json={"code": policy.code, "version": policy.current_version, "summary": payload.change_summary},
            )
        )

        await db.flush()
        await db.refresh(policy)
        return policy

    @classmethod
    async def create_policy_version(
        cls, db: AsyncSession, tenant_id: UUID, policy_id: UUID, payload: RetentionPolicyUpdate, change_summary: str, actor_id: UUID | None = None
    ) -> RetentionPolicyDefinition:
        """Creates a new version of an existing retention policy, preserving historical versions."""
        stmt = (
            select(RetentionPolicyDefinition)
            .options(selectinload(RetentionPolicyDefinition.versions))
            .where(and_(RetentionPolicyDefinition.id == policy_id, RetentionPolicyDefinition.tenant_id == tenant_id))
        )
        policy = (await db.scalars(stmt)).first()
        if not policy:
            raise RetentionPolicyNotFoundException(policy_id)

        now = datetime.now(UTC)
        # Apply field updates
        if payload.name is not None:
            policy.name = payload.name.strip()
        if payload.description is not None:
            policy.description = payload.description
        if payload.retention_duration is not None:
            policy.retention_duration = payload.retention_duration
        if payload.retention_unit is not None:
            policy.retention_unit = payload.retention_unit
        if payload.trigger_event is not None:
            policy.trigger_event = payload.trigger_event
        if payload.review_required is not None:
            policy.review_required = payload.review_required
        if payload.archive_required is not None:
            policy.archive_required = payload.archive_required
        if payload.disposition_method is not None:
            policy.disposition_method = payload.disposition_method
        if payload.approval_required is not None:
            policy.approval_required = payload.approval_required
        if payload.effective_until is not None:
            policy.effective_until = payload.effective_until
        if payload.metadata_json is not None:
            policy.metadata_json = payload.metadata_json

        next_version = policy.current_version + 1
        policy.current_version = next_version
        policy.status = RetentionPolicyStatus.PUBLISHED
        policy.approved_by_user_id = actor_id
        policy.approved_at = now
        policy.updated_at = now

        # Add new immutable version record
        version = RetentionPolicyVersionRecord(
            id=uuid4(),
            tenant_id=tenant_id,
            policy_id=policy.id,
            version_number=next_version,
            status=RetentionPolicyStatus.PUBLISHED,
            rules_json={
                "retention_duration": policy.retention_duration,
                "retention_unit": policy.retention_unit,
                "trigger_event": policy.trigger_event,
                "disposition_method": policy.disposition_method,
                "review_required": policy.review_required,
                "archive_required": policy.archive_required,
                "approval_required": policy.approval_required,
            },
            change_summary=change_summary,
            effective_from=now,
            created_by_user_id=actor_id,
            created_at=now,
            updated_at=now,
        )
        policy.versions.append(version)
        db.add(version)

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.RETENTION_POLICY_PUBLISHED,
                entity_type="RetentionPolicyDefinition",
                entity_id=policy.id,
                user_id=actor_id,
                new_values_json={"code": policy.code, "version": next_version, "summary": change_summary},
            )
        )

        await db.flush()
        return await cls.get_retention_policy(db, tenant_id, policy_id)

    @classmethod
    async def list_retention_policies(
        cls, db: AsyncSession, tenant_id: UUID, category_code: str | None = None, status: str | None = None
    ) -> list[RetentionPolicyDefinition]:
        """Lists retention policies for tenant with optional category/status filters."""
        stmt = (
            select(RetentionPolicyDefinition)
            .options(selectinload(RetentionPolicyDefinition.versions))
            .where(RetentionPolicyDefinition.tenant_id == tenant_id)
        )
        if category_code:
            stmt = stmt.where(RetentionPolicyDefinition.category_code == category_code.upper().strip())
        if status:
            stmt = stmt.where(RetentionPolicyDefinition.status == status.upper().strip())
        stmt = stmt.order_by(RetentionPolicyDefinition.code.asc())
        return list((await db.scalars(stmt)).all())

    @classmethod
    async def get_retention_policy(cls, db: AsyncSession, tenant_id: UUID, policy_id: UUID) -> RetentionPolicyDefinition:
        """Fetch policy by ID ensuring strict tenant scoping."""
        stmt = (
            select(RetentionPolicyDefinition)
            .options(selectinload(RetentionPolicyDefinition.versions))
            .where(and_(RetentionPolicyDefinition.id == policy_id, RetentionPolicyDefinition.tenant_id == tenant_id))
        )
        policy = (await db.scalars(stmt)).first()
        if not policy:
            raise RetentionPolicyNotFoundException(policy_id)
        return policy

    # =========================================================================
    # 3. RECORDS REGISTRY INDEXING & REGISTRATION
    # =========================================================================

    @classmethod
    async def register_record(
        cls, db: AsyncSession, tenant_id: UUID, payload: RecordRegistryCreate, actor_id: UUID | None = None
    ) -> RecordRegistryEntry:
        """Registers an authoritative institutional record into the centralized lifecycle registry.

        Stores references and metadata without copying sensitive payload contents.
        Auto-calculates retention review/eligibility dates and links active legal holds.
        """
        clean_cat = payload.category_code.upper().strip()
        clean_module = payload.source_module.lower().strip()

        # Check existing registration
        existing = await db.scalar(
            select(RecordRegistryEntry).where(
                and_(
                    RecordRegistryEntry.tenant_id == tenant_id,
                    RecordRegistryEntry.source_module == clean_module,
                    RecordRegistryEntry.source_record_id == payload.source_record_id,
                )
            )
        )
        if existing:
            return existing

        now = datetime.now(UTC)
        category = await cls.get_category(db, tenant_id, clean_cat)

        # Generate unique record identifier: REC-{YEAR}-{HEX8}
        record_number = f"REC-{now.year}-{secrets.token_hex(4).upper()}"

        record_created_at = payload.record_created_at or now
        retention_start_date = payload.retention_start_date or record_created_at
        if record_created_at.tzinfo is None:
            record_created_at = record_created_at.replace(tzinfo=UTC)
        if retention_start_date.tzinfo is None:
            retention_start_date = retention_start_date.replace(tzinfo=UTC)

        # Match applicable active retention policy
        policy = await db.scalar(
            select(RetentionPolicyDefinition).where(
                and_(
                    RetentionPolicyDefinition.tenant_id == tenant_id,
                    RetentionPolicyDefinition.category_code == clean_cat,
                    RetentionPolicyDefinition.status == RetentionPolicyStatus.PUBLISHED,
                )
            )
        )

        calculated_eligibility_date: datetime | None = None
        calculated_review_date: datetime | None = None
        lifecycle_state = RecordLifecycleState.ACTIVE
        policy_id: UUID | None = None
        policy_version: int | None = None

        if policy:
            policy_id = policy.id
            policy_version = policy.current_version
            # Calculate deadline
            days = cls._calculate_duration_days(policy.retention_duration, policy.retention_unit)
            calculated_eligibility_date = retention_start_date + timedelta(days=days)
            # Review date: 30 days prior to eligibility date or same day if duration <= 30
            review_offset = min(30, max(1, days // 10))
            calculated_review_date = calculated_eligibility_date - timedelta(days=review_offset)

            if now >= calculated_eligibility_date:
                lifecycle_state = RecordLifecycleState.DISPOSITION_ELIGIBLE
            elif now >= calculated_review_date and policy.review_required:
                lifecycle_state = RecordLifecycleState.REVIEW_REQUIRED
            else:
                lifecycle_state = RecordLifecycleState.RETENTION_IN_PROGRESS
        else:
            # Safety fail-safe: Missing policy halts automated destruction
            lifecycle_state = RecordLifecycleState.REVIEW_REQUIRED

        # Create record entry
        entry = RecordRegistryEntry(
            id=uuid4(),
            tenant_id=tenant_id,
            record_number=record_number,
            category_id=category.id,
            category_code=clean_cat,
            source_module=clean_module,
            source_record_id=payload.source_record_id,
            source_reference=payload.source_reference,
            title=payload.title.strip(),
            description=payload.description,
            owner_user_id=payload.owner_user_id,
            owner_department_id=payload.owner_department_id,
            responsible_department=payload.responsible_department,
            confidentiality_level=payload.confidentiality_level.upper(),
            lifecycle_state=lifecycle_state,
            policy_id=policy_id,
            policy_version=policy_version,
            record_created_at=record_created_at,
            retention_start_date=retention_start_date,
            calculated_review_date=calculated_review_date,
            calculated_eligibility_date=calculated_eligibility_date,
            is_held=False,
            active_hold_count=0,
            storage_reference=payload.storage_reference,
            checksum_sha256=payload.checksum_sha256,
            metadata_json=payload.metadata_json or {},
            created_at=now,
            updated_at=now,
        )
        db.add(entry)

        # Initial history transition
        history = RecordLifecycleHistory(
            id=uuid4(),
            tenant_id=tenant_id,
            record_id=entry.id,
            from_state=RecordLifecycleState.ACTIVE,
            to_state=lifecycle_state,
            trigger_action="INITIAL_REGISTRATION",
            reason="Record registered into central lifecycle index.",
            actor_user_id=actor_id,
            actor_role="SYSTEM",
            metadata_json={"source_module": clean_module, "source_id": str(payload.source_record_id)},
            created_at=now,
            updated_at=now,
        )
        db.add(history)

        # Check applicable active legal holds
        await cls._apply_matching_active_holds(db, tenant_id, entry)

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.RECORD_REGISTERED,
                entity_type="RecordRegistryEntry",
                entity_id=entry.id,
                user_id=actor_id,
                new_values_json={"record_number": record_number, "module": clean_module, "state": entry.lifecycle_state},
            )
        )

        await db.flush()
        await db.refresh(entry)
        return entry

    @classmethod
    async def get_record(cls, db: AsyncSession, tenant_id: UUID, record_id: UUID) -> RecordRegistryEntry:
        """Fetch record registry entry by UUID ensuring strict tenant scoping."""
        stmt = select(RecordRegistryEntry).where(
            and_(RecordRegistryEntry.id == record_id, RecordRegistryEntry.tenant_id == tenant_id)
        )
        record = (await db.scalars(stmt)).first()
        if not record:
            raise RecordNotFoundException(record_id)
        return record

    @classmethod
    async def list_records(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        category_code: str | None = None,
        source_module: str | None = None,
        lifecycle_state: str | None = None,
        is_held: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[RecordRegistryEntry]:
        """List paginated records with multi-criteria filtering."""
        stmt = select(RecordRegistryEntry).where(RecordRegistryEntry.tenant_id == tenant_id)
        if category_code:
            stmt = stmt.where(RecordRegistryEntry.category_code == category_code.upper().strip())
        if source_module:
            stmt = stmt.where(RecordRegistryEntry.source_module == source_module.lower().strip())
        if lifecycle_state:
            stmt = stmt.where(RecordRegistryEntry.lifecycle_state == lifecycle_state.upper().strip())
        if is_held is not None:
            stmt = stmt.where(RecordRegistryEntry.is_held == is_held)

        stmt = stmt.order_by(RecordRegistryEntry.record_created_at.desc()).limit(limit).offset(offset)
        return list((await db.scalars(stmt)).all())

    @classmethod
    async def get_record_history(
        cls, db: AsyncSession, tenant_id: UUID, record_id: UUID
    ) -> list[RecordLifecycleHistory]:
        """Fetch complete lifecycle transition history for a record."""
        # Ensure record exists in tenant
        await cls.get_record(db, tenant_id, record_id)

        stmt = (
            select(RecordLifecycleHistory)
            .where(and_(RecordLifecycleHistory.tenant_id == tenant_id, RecordLifecycleHistory.record_id == record_id))
            .order_by(RecordLifecycleHistory.created_at.desc())
        )
        return list((await db.scalars(stmt)).all())

    # =========================================================================
    # 4. LIFECYCLE STATE MACHINE & TRANSITIONS
    # =========================================================================

    VALID_TRANSITIONS: dict[RecordLifecycleState, set[RecordLifecycleState]] = {
        RecordLifecycleState.ACTIVE: {
            RecordLifecycleState.RETENTION_PENDING,
            RecordLifecycleState.RETENTION_IN_PROGRESS,
            RecordLifecycleState.REVIEW_REQUIRED,
            RecordLifecycleState.ELIGIBLE_FOR_ARCHIVAL,
            RecordLifecycleState.ARCHIVED,
            RecordLifecycleState.LEGAL_HOLD,
        },
        RecordLifecycleState.RETENTION_PENDING: {
            RecordLifecycleState.RETENTION_IN_PROGRESS,
            RecordLifecycleState.REVIEW_REQUIRED,
            RecordLifecycleState.LEGAL_HOLD,
        },
        RecordLifecycleState.RETENTION_IN_PROGRESS: {
            RecordLifecycleState.ELIGIBLE_FOR_ARCHIVAL,
            RecordLifecycleState.ARCHIVED,
            RecordLifecycleState.DISPOSITION_ELIGIBLE,
            RecordLifecycleState.REVIEW_REQUIRED,
            RecordLifecycleState.LEGAL_HOLD,
        },
        RecordLifecycleState.REVIEW_REQUIRED: {
            RecordLifecycleState.ACTIVE,
            RecordLifecycleState.RETENTION_IN_PROGRESS,
            RecordLifecycleState.ELIGIBLE_FOR_ARCHIVAL,
            RecordLifecycleState.ARCHIVED,
            RecordLifecycleState.DISPOSITION_ELIGIBLE,
            RecordLifecycleState.REVIEW_BLOCKED,
            RecordLifecycleState.LEGAL_HOLD,
        },
        RecordLifecycleState.ELIGIBLE_FOR_ARCHIVAL: {
            RecordLifecycleState.ARCHIVED,
            RecordLifecycleState.REVIEW_REQUIRED,
            RecordLifecycleState.LEGAL_HOLD,
        },
        RecordLifecycleState.ARCHIVED: {
            RecordLifecycleState.DISPOSITION_ELIGIBLE,
            RecordLifecycleState.ACTIVE,  # Restoration
            RecordLifecycleState.REVIEW_REQUIRED,
            RecordLifecycleState.LEGAL_HOLD,
        },
        RecordLifecycleState.DISPOSITION_ELIGIBLE: {
            RecordLifecycleState.DISPOSITION_PENDING_APPROVAL,
            RecordLifecycleState.REVIEW_REQUIRED,
            RecordLifecycleState.LEGAL_HOLD,
        },
        RecordLifecycleState.DISPOSITION_PENDING_APPROVAL: {
            RecordLifecycleState.DISPOSITION_APPROVED,
            RecordLifecycleState.DISPOSITION_ELIGIBLE,  # Rejection
            RecordLifecycleState.REVIEW_REQUIRED,
            RecordLifecycleState.LEGAL_HOLD,
        },
        RecordLifecycleState.DISPOSITION_APPROVED: {
            RecordLifecycleState.DISPOSITION_COMPLETED,
            RecordLifecycleState.REVIEW_BLOCKED,
            RecordLifecycleState.LEGAL_HOLD,
        },
        RecordLifecycleState.DISPOSITION_COMPLETED: set(),  # Terminal state
        RecordLifecycleState.LEGAL_HOLD: {
            RecordLifecycleState.ACTIVE,
            RecordLifecycleState.RETENTION_IN_PROGRESS,
            RecordLifecycleState.ARCHIVED,
            RecordLifecycleState.DISPOSITION_ELIGIBLE,
            RecordLifecycleState.REVIEW_REQUIRED,
        },
        RecordLifecycleState.REVIEW_BLOCKED: {
            RecordLifecycleState.REVIEW_REQUIRED,
            RecordLifecycleState.ACTIVE,
            RecordLifecycleState.LEGAL_HOLD,
        },
    }

    @classmethod
    async def transition_record_state(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        record_id: UUID,
        payload: RecordLifecycleTransitionRequest,
        trigger_action: str = "MANUAL_TRANSITION",
        actor_id: UUID | None = None,
        actor_role: str | None = None,
    ) -> RecordRegistryEntry:
        """Transitions record lifecycle state with validation, legal hold checks, and audit history."""
        record = await cls.get_record(db, tenant_id, record_id)
        current = record.lifecycle_state
        target = payload.target_state

        if current == target:
            return record

        # Rule: Terminal state cannot be transitioned
        if current == RecordLifecycleState.DISPOSITION_COMPLETED:
            raise InvalidRecordLifecycleTransitionException(current, target, "Record is already permanently disposed.")

        # Rule: Active legal holds unconditionally block transitions toward disposition
        if record.is_held and target in {
            RecordLifecycleState.DISPOSITION_ELIGIBLE,
            RecordLifecycleState.DISPOSITION_PENDING_APPROVAL,
            RecordLifecycleState.DISPOSITION_APPROVED,
            RecordLifecycleState.DISPOSITION_COMPLETED,
        }:
            raise LegalHoldActiveException("Active Legal Hold", reason="Disposition is strictly prohibited while record is held.")

        # Rule: Validate state machine edge
        allowed = cls.VALID_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise InvalidRecordLifecycleTransitionException(
                current, target, f"Valid transitions from '{current}' are: {', '.join(sorted(allowed))}."
            )

        now = datetime.now(UTC)
        record.lifecycle_state = target
        record.updated_at = now

        if target == RecordLifecycleState.ARCHIVED:
            record.archived_at = now
        elif target == RecordLifecycleState.DISPOSITION_COMPLETED:
            record.disposed_at = now

        # Record history
        history = RecordLifecycleHistory(
            id=uuid4(),
            tenant_id=tenant_id,
            record_id=record.id,
            from_state=current,
            to_state=target,
            trigger_action=trigger_action,
            reason=payload.reason,
            actor_user_id=actor_id,
            actor_role=actor_role or "ADMIN",
            metadata_json=payload.metadata_json or {},
            created_at=now,
            updated_at=now,
        )
        db.add(history)

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.RECORD_LIFECYCLE_TRANSITION,
                entity_type="RecordRegistryEntry",
                entity_id=record.id,
                user_id=actor_id,
                new_values_json={"from": current, "to": target, "reason": payload.reason},
            )
        )

        await db.flush()
        await db.refresh(record)
        return record

    # =========================================================================
    # 5. RETENTION EVALUATION & SAFE DISPOSITION PREVIEW
    # =========================================================================

    @classmethod
    async def evaluate_record_retention(
        cls, db: AsyncSession, tenant_id: UUID, record_id: UUID
    ) -> RetentionEvaluationResponse:
        """Evaluates retention decision for a record, checking policies, legal holds, and dependencies."""
        record = await cls.get_record(db, tenant_id, record_id)
        now = datetime.now(UTC)

        hold_reasons: list[str] = []
        if record.is_held:
            # Query active holds
            stmt = (
                select(RecordLegalHold)
                .join(RecordLegalHoldAssociation, RecordLegalHold.id == RecordLegalHoldAssociation.hold_id)
                .where(
                    and_(
                        RecordLegalHoldAssociation.record_id == record_id,
                        RecordLegalHoldAssociation.tenant_id == tenant_id,
                        RecordLegalHold.status == LegalHoldStatus.ACTIVE,
                    )
                )
            )
            holds = (await db.scalars(stmt)).all()
            hold_reasons = [f"Hold '{h.name}' (Case: {h.case_reference or 'N/A'}): {h.reason}" for h in holds]

        # Fetch active published policy
        policy = await db.scalar(
            select(RetentionPolicyDefinition).where(
                and_(
                    RetentionPolicyDefinition.tenant_id == tenant_id,
                    RetentionPolicyDefinition.category_code == record.category_code,
                    RetentionPolicyDefinition.status == RetentionPolicyStatus.PUBLISHED,
                )
            )
        )

        has_dep, dep_reasons = await cls.check_cross_domain_dependencies(
            db, tenant_id, record.source_module, record.source_record_id
        )

        if record.is_held:
            return RetentionEvaluationResponse(
                record_id=record.id,
                record_number=record.record_number,
                current_state=record.lifecycle_state,
                recommended_state=RecordLifecycleState.LEGAL_HOLD,
                is_held=True,
                hold_reasons=hold_reasons,
                policy_id=policy.id if policy else None,
                policy_code=policy.code if policy else None,
                policy_version=policy.current_version if policy else None,
                retention_start_date=record.retention_start_date,
                calculated_eligibility_date=record.calculated_eligibility_date,
                is_eligible_for_disposition=False,
                is_eligible_for_archival=False,
                disposition_method=policy.disposition_method if policy else None,
                has_dependency_block=has_dep,
                dependency_reasons=dep_reasons,
                evaluation_summary="HOLD_ACTIVE: Record is subject to an active legal hold. Disposition is blocked.",
            )

        if not policy:
            return RetentionEvaluationResponse(
                record_id=record.id,
                record_number=record.record_number,
                current_state=record.lifecycle_state,
                recommended_state=RecordLifecycleState.REVIEW_REQUIRED,
                is_held=False,
                hold_reasons=[],
                policy_id=None,
                policy_code=None,
                policy_version=None,
                retention_start_date=record.retention_start_date,
                calculated_eligibility_date=None,
                is_eligible_for_disposition=False,
                is_eligible_for_archival=False,
                disposition_method=None,
                has_dependency_block=has_dep,
                dependency_reasons=dep_reasons,
                evaluation_summary="NO_ACTIVE_POLICY: No published retention policy found. Automatic disposition halted.",
            )

        base_date = record.retention_start_date or record.record_created_at
        if base_date.tzinfo is None:
            base_date = base_date.replace(tzinfo=UTC)
        duration_days = cls._calculate_duration_days(policy.retention_duration, policy.retention_unit)
        eligibility_date = base_date + timedelta(days=duration_days)
        if eligibility_date.tzinfo is None:
            eligibility_date = eligibility_date.replace(tzinfo=UTC)

        is_eligible_disp = now >= eligibility_date
        is_eligible_arch = policy.archive_required and record.lifecycle_state != RecordLifecycleState.ARCHIVED

        if is_eligible_disp and has_dep:
            recommended = RecordLifecycleState.REVIEW_BLOCKED
            summary = f"DEPENDENCY_BLOCKED: Retention period ended, but active dependencies prevent disposition: {'; '.join(dep_reasons)}"
        elif is_eligible_disp:
            recommended = RecordLifecycleState.DISPOSITION_ELIGIBLE
            summary = f"DISPOSITION_ELIGIBLE: Record reached retention maturity on {eligibility_date.strftime('%Y-%m-%d')}."
        elif is_eligible_arch:
            recommended = RecordLifecycleState.ELIGIBLE_FOR_ARCHIVAL
            summary = "ELIGIBLE_FOR_ARCHIVAL: Record requires cold storage archival."
        else:
            recommended = RecordLifecycleState.RETENTION_IN_PROGRESS
            summary = f"RETENTION_ACTIVE: Record is within statutory retention period until {eligibility_date.strftime('%Y-%m-%d')}."

        return RetentionEvaluationResponse(
            record_id=record.id,
            record_number=record.record_number,
            current_state=record.lifecycle_state,
            recommended_state=recommended,
            is_held=False,
            hold_reasons=[],
            policy_id=policy.id,
            policy_code=policy.code,
            policy_version=policy.current_version,
            retention_start_date=record.retention_start_date,
            calculated_eligibility_date=eligibility_date,
            is_eligible_for_disposition=is_eligible_disp and not has_dep,
            is_eligible_for_archival=is_eligible_arch,
            disposition_method=policy.disposition_method,
            has_dependency_block=has_dep,
            dependency_reasons=dep_reasons,
            evaluation_summary=summary,
        )

    @classmethod
    async def preview_disposition(
        cls, db: AsyncSession, tenant_id: UUID, payload: RecordDispositionPreviewRequest
    ) -> RecordDispositionPreviewResponse:
        """Executes a dry-run preview identifying qualifying records without performing destructive actions."""
        stmt = select(RecordRegistryEntry).where(RecordRegistryEntry.tenant_id == tenant_id)
        if payload.category_code:
            stmt = stmt.where(RecordRegistryEntry.category_code == payload.category_code.upper().strip())
        if payload.policy_id:
            stmt = stmt.where(RecordRegistryEntry.policy_id == payload.policy_id)

        records = list((await db.scalars(stmt)).all())
        preview_items: list[RecordDispositionPreviewItem] = []

        eligible_count = 0
        blocked_hold_count = 0
        blocked_dep_count = 0

        for r in records:
            evaluation = await cls.evaluate_record_retention(db, tenant_id, r.id)
            if evaluation.is_held:
                blocked_hold_count += 1
            elif evaluation.has_dependency_block:
                blocked_dep_count += 1
            elif evaluation.is_eligible_for_disposition:
                eligible_count += 1

            preview_items.append(
                RecordDispositionPreviewItem(
                    record_id=r.id,
                    record_number=r.record_number,
                    title=r.title,
                    category_code=r.category_code,
                    current_state=r.lifecycle_state,
                    calculated_eligibility_date=evaluation.calculated_eligibility_date,
                    is_held=evaluation.is_held,
                    hold_reason=evaluation.hold_reasons[0] if evaluation.hold_reasons else None,
                    has_dependency_block=evaluation.has_dependency_block,
                    dependency_reason=evaluation.dependency_reasons[0] if evaluation.dependency_reasons else None,
                    eligible_for_disposition=evaluation.is_eligible_for_disposition,
                    recommended_method=evaluation.disposition_method or DispositionMethod.ANONYMIZE,
                )
            )

        return RecordDispositionPreviewResponse(
            total_records_analyzed=len(records),
            eligible_count=eligible_count,
            blocked_by_hold_count=blocked_hold_count,
            blocked_by_dependency_count=blocked_dep_count,
            records=preview_items,
        )

    @classmethod
    async def check_cross_domain_dependencies(
        cls, db: AsyncSession, tenant_id: UUID, module: str, record_id: UUID
    ) -> tuple[bool, list[str]]:
        """Inspects dependent active operational domain records that prevent disposition."""
        clean_mod = module.lower().strip()
        reasons: list[str] = []

        if clean_mod in ("students", "student"):
            # Active course enrollments
            active_enr = await db.scalar(
                select(CourseEnrollment).where(
                    and_(
                        CourseEnrollment.tenant_id == tenant_id,
                        CourseEnrollment.student_id == record_id,
                        CourseEnrollment.status == "ENROLLED",
                    )
                )
            )
            if active_enr:
                reasons.append("Student currently holds active course enrollments.")

            # Outstanding fees or open invoices
            unpaid_inv = await db.scalar(
                select(Invoice).where(
                    and_(
                        Invoice.tenant_id == tenant_id,
                        Invoice.student_id == record_id,
                        Invoice.status.in_(["ISSUED", "PARTIALLY_PAID", "OVERDUE"]),
                    )
                )
            )
            if unpaid_inv:
                reasons.append(f"Student has outstanding financial invoice ({unpaid_inv.invoice_number}).")

            # Active hostel allocations
            active_hostel = await db.scalar(
                select(HostelAllocation).where(
                    and_(
                        HostelAllocation.tenant_id == tenant_id,
                        HostelAllocation.student_id == record_id,
                        HostelAllocation.status == "ACTIVE",
                    )
                )
            )
            if active_hostel:
                reasons.append("Student occupies an active hostel bed allocation.")

        elif clean_mod in ("documents", "document"):
            doc = await db.scalar(
                select(Document).where(and_(Document.tenant_id == tenant_id, Document.id == record_id))
            )
            if doc and doc.status == "UNDER_REVIEW":
                reasons.append("Document is currently pending institutional verification.")

        return len(reasons) > 0, reasons

    # =========================================================================
    # 6. ARCHIVAL MANAGEMENT & CRYPTOGRAPHIC INTEGRITY
    # =========================================================================

    @classmethod
    async def execute_archival(
        cls, db: AsyncSession, tenant_id: UUID, payload: RecordArchivalExecuteRequest, actor_id: UUID | None = None
    ) -> RecordArchivalRecord:
        """Executes cryptographic archival of an institutional record into secure cold storage tier."""
        record = await cls.get_record(db, tenant_id, payload.record_id)

        # Check existing manifest
        existing = await db.scalar(
            select(RecordArchivalRecord).where(
                and_(RecordArchivalRecord.tenant_id == tenant_id, RecordArchivalRecord.record_id == record.id)
            )
        )
        if existing and existing.status == ArchivalStatus.STORED:
            return existing

        now = datetime.now(UTC)
        manifest_num = f"ARCH-{now.year}-{secrets.token_hex(4).upper()}"
        archive_storage_key = f"archives/{tenant_id}/{record.category_code}/{record.record_number}.arc"

        # Compute cryptographic checksum
        payload_to_hash = f"{tenant_id}:{record.record_number}:{record.source_module}:{record.source_record_id}:{now.isoformat()}"
        sha256_hash = hashlib.sha256(payload_to_hash.encode()).hexdigest()

        # Upload archive manifest descriptor into DocumentStorage
        storage = get_document_storage()
        try:
            manifest_descriptor = json.dumps(
                {
                    "manifest_number": manifest_num,
                    "record_number": record.record_number,
                    "title": record.title,
                    "category": record.category_code,
                    "checksum": sha256_hash,
                    "archived_at": now.isoformat(),
                    "archived_by": str(actor_id) if actor_id else "SYSTEM",
                    "justification": payload.justification,
                }
            ).encode("utf-8")

            await storage.upload(
                file_content=manifest_descriptor,
                destination_key=archive_storage_key,
                mime_type="text/plain",
            )
        except Exception as exc:
            logger.error("Failed to write archival manifest to storage: %s", exc)
            raise RecordArchivalException(f"Failed to write archival file to storage: {exc}")

        archival_record = RecordArchivalRecord(
            id=uuid4(),
            tenant_id=tenant_id,
            manifest_number=manifest_num,
            record_id=record.id,
            archive_location=payload.archive_location,
            archive_storage_key=archive_storage_key,
            original_storage_key=record.storage_reference,
            checksum_sha256=sha256_hash,
            verified_checksum=sha256_hash,
            file_size_bytes=len(manifest_descriptor),
            status=ArchivalStatus.STORED,
            archived_by_user_id=actor_id,
            archived_at=now,
            retrieval_count=0,
            metadata_json={"justification": payload.justification},
            created_at=now,
            updated_at=now,
        )
        db.add(archival_record)

        # Transition record state
        if record.lifecycle_state != RecordLifecycleState.LEGAL_HOLD:
            record.lifecycle_state = RecordLifecycleState.ARCHIVED
        record.archived_at = now
        record.storage_reference = archive_storage_key
        record.checksum_sha256 = sha256_hash
        record.updated_at = now

        db.add(
            RecordLifecycleHistory(
                id=uuid4(),
                tenant_id=tenant_id,
                record_id=record.id,
                from_state=record.lifecycle_state,
                to_state=RecordLifecycleState.ARCHIVED if not record.is_held else RecordLifecycleState.LEGAL_HOLD,
                trigger_action="ARCHIVAL_EXECUTION",
                reason=payload.justification,
                actor_user_id=actor_id,
                actor_role="ARCHIVIST",
                metadata_json={"manifest_number": manifest_num, "checksum": sha256_hash},
                created_at=now,
                updated_at=now,
            )
        )

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.RECORD_ARCHIVED,
                entity_type="RecordArchivalRecord",
                entity_id=archival_record.id,
                user_id=actor_id,
                new_values_json={"manifest": manifest_num, "checksum": sha256_hash},
            )
        )

        await db.flush()
        await db.refresh(archival_record)
        return archival_record

    @classmethod
    async def retrieve_archived_record(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        manifest_id: UUID,
        access_type: str,
        justification: str,
        actor_id: UUID,
        ip_address: str | None = None,
    ) -> RecordArchivalRecord:
        """Logs audited access to an archived institutional record manifest."""
        stmt = select(RecordArchivalRecord).where(
            and_(RecordArchivalRecord.id == manifest_id, RecordArchivalRecord.tenant_id == tenant_id)
        )
        manifest = (await db.scalars(stmt)).first()
        if not manifest:
            raise NotFoundException("RecordArchivalRecord", manifest_id)

        now = datetime.now(UTC)
        manifest.retrieval_count += 1
        manifest.last_retrieved_at = now
        manifest.updated_at = now

        log = RecordArchivalAccessLog(
            id=uuid4(),
            tenant_id=tenant_id,
            manifest_id=manifest.id,
            user_id=actor_id,
            access_type=access_type.upper().strip(),
            justification=justification.strip(),
            ip_address=ip_address,
            accessed_at=now,
            created_at=now,
            updated_at=now,
        )
        db.add(log)

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.RECORD_ARCHIVE_RETRIEVED,
                entity_type="RecordArchivalRecord",
                entity_id=manifest.id,
                user_id=actor_id,
                new_values_json={"manifest_number": manifest.manifest_number, "access_type": access_type},
            )
        )

        await db.flush()
        await db.refresh(manifest)
        return manifest

    @classmethod
    async def restore_archived_record(
        cls, db: AsyncSession, tenant_id: UUID, manifest_id: UUID, justification: str, actor_id: UUID | None = None
    ) -> RecordRegistryEntry:
        """Restores an archived record back to active operational use when authorized."""
        stmt = select(RecordArchivalRecord).where(
            and_(RecordArchivalRecord.id == manifest_id, RecordArchivalRecord.tenant_id == tenant_id)
        )
        manifest = (await db.scalars(stmt)).first()
        if not manifest:
            raise NotFoundException("RecordArchivalRecord", manifest_id)

        record = await cls.get_record(db, tenant_id, manifest.record_id)
        now = datetime.now(UTC)

        manifest.status = ArchivalStatus.RESTORED
        manifest.updated_at = now

        record.lifecycle_state = RecordLifecycleState.ACTIVE
        record.updated_at = now

        db.add(
            RecordLifecycleHistory(
                id=uuid4(),
                tenant_id=tenant_id,
                record_id=record.id,
                from_state=RecordLifecycleState.ARCHIVED,
                to_state=RecordLifecycleState.ACTIVE,
                trigger_action="ARCHIVAL_RESTORATION",
                reason=justification,
                actor_user_id=actor_id,
                actor_role="ADMIN",
                metadata_json={"manifest_number": manifest.manifest_number},
                created_at=now,
                updated_at=now,
            )
        )

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.RECORD_RESTORED,
                entity_type="RecordRegistryEntry",
                entity_id=record.id,
                user_id=actor_id,
                new_values_json={"record_number": record.record_number, "manifest": manifest.manifest_number},
            )
        )

        await db.flush()
        await db.refresh(record)
        return record

    # =========================================================================
    # 7. LEGAL HOLD MANAGEMENT
    # =========================================================================

    @classmethod
    async def create_legal_hold(
        cls, db: AsyncSession, tenant_id: UUID, payload: RecordLegalHoldCreate, actor_id: UUID | None = None
    ) -> RecordLegalHold:
        """Places a high-precedence administrative or legal hold across scoped institutional records."""
        now = datetime.now(UTC)
        hold_num = f"HOLD-{now.year}-{secrets.token_hex(4).upper()}"

        hold = RecordLegalHold(
            id=uuid4(),
            tenant_id=tenant_id,
            hold_number=hold_num,
            name=payload.name.strip(),
            case_reference=payload.case_reference.strip() if payload.case_reference else None,
            reason=payload.reason.strip(),
            hold_authority=payload.hold_authority,
            scope_type=payload.scope_type,
            scope_value=payload.scope_value,
            status=LegalHoldStatus.ACTIVE,
            owner_user_id=actor_id,
            custodians_json=payload.custodians_json or [],
            effective_from=now,
            review_date=payload.review_date,
            records_count=0,
            metadata_json=payload.metadata_json or {},
            created_at=now,
            updated_at=now,
        )
        db.add(hold)

        # Match scoped records
        matching_records = await cls._find_records_matching_scope(
            db, tenant_id, payload.scope_type, payload.scope_value
        )

        for rec in matching_records:
            rec.is_held = True
            rec.active_hold_count += 1
            rec.updated_at = now

            # If record was in disposition pipeline, immediately halt disposition
            if rec.lifecycle_state in {
                RecordLifecycleState.DISPOSITION_ELIGIBLE,
                RecordLifecycleState.DISPOSITION_PENDING_APPROVAL,
                RecordLifecycleState.DISPOSITION_APPROVED,
            }:
                db.add(
                    RecordLifecycleHistory(
                        id=uuid4(),
                        tenant_id=tenant_id,
                        record_id=rec.id,
                        from_state=rec.lifecycle_state,
                        to_state=RecordLifecycleState.LEGAL_HOLD,
                        trigger_action="HOLD_ENFORCEMENT",
                        reason=f"Disposition halted due to Legal Hold '{hold.name}' (Case: {hold.case_reference or 'N/A'}).",
                        actor_user_id=actor_id,
                        actor_role="COMPLIANCE_OFFICER",
                        metadata_json={"hold_number": hold_num},
                        created_at=now,
                        updated_at=now,
                    )
                )
                rec.lifecycle_state = RecordLifecycleState.LEGAL_HOLD

            assoc = RecordLegalHoldAssociation(
                id=uuid4(),
                tenant_id=tenant_id,
                hold_id=hold.id,
                record_id=rec.id,
                status="ACTIVE",
                applied_at=now,
                applied_by_user_id=actor_id,
                created_at=now,
                updated_at=now,
            )
            db.add(assoc)

        hold.records_count = len(matching_records)

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.LEGAL_HOLD_CREATED,
                entity_type="RecordLegalHold",
                entity_id=hold.id,
                user_id=actor_id,
                new_values_json={"hold_number": hold_num, "name": hold.name, "records_count": hold.records_count},
            )
        )

        await db.flush()
        await db.refresh(hold)
        return hold

    @classmethod
    async def release_legal_hold(
        cls, db: AsyncSession, tenant_id: UUID, hold_id: UUID, payload: RecordLegalHoldReleaseRequest, actor_id: UUID | None = None
    ) -> RecordLegalHold:
        """Releases an active legal hold and triggers fresh retention eligibility recalculation for affected records."""
        stmt = select(RecordLegalHold).where(
            and_(RecordLegalHold.id == hold_id, RecordLegalHold.tenant_id == tenant_id)
        )
        hold = (await db.scalars(stmt)).first()
        if not hold:
            raise NotFoundException("RecordLegalHold", hold_id)

        if hold.status != LegalHoldStatus.ACTIVE:
            raise ConflictException(f"Legal hold is already {hold.status}.")

        now = datetime.now(UTC)
        hold.status = LegalHoldStatus.RELEASED
        hold.released_at = now
        hold.released_by_user_id = actor_id
        hold.release_reason = payload.release_reason.strip()
        hold.updated_at = now

        # Update associations and release records
        assoc_stmt = select(RecordLegalHoldAssociation).where(
            and_(RecordLegalHoldAssociation.hold_id == hold.id, RecordLegalHoldAssociation.tenant_id == tenant_id)
        )
        associations = list((await db.scalars(assoc_stmt)).all())

        for assoc in associations:
            assoc.status = "RELEASED"
            assoc.released_at = now
            assoc.released_by_user_id = actor_id
            assoc.updated_at = now

            record = await cls.get_record(db, tenant_id, assoc.record_id)
            record.active_hold_count = max(0, record.active_hold_count - 1)
            if record.active_hold_count == 0:
                record.is_held = False
                # Recalculate fresh eligibility (Do NOT automatically destroy records)
                evaluation = await cls.evaluate_record_retention(db, tenant_id, record.id)
                new_state = evaluation.recommended_state

                db.add(
                    RecordLifecycleHistory(
                        id=uuid4(),
                        tenant_id=tenant_id,
                        record_id=record.id,
                        from_state=record.lifecycle_state,
                        to_state=new_state,
                        trigger_action="HOLD_RELEASE_RECALCULATION",
                        reason=f"Legal hold '{hold.name}' released. Fresh eligibility evaluated: {evaluation.evaluation_summary}",
                        actor_user_id=actor_id,
                        actor_role="COMPLIANCE_OFFICER",
                        metadata_json={"released_hold_number": hold.hold_number},
                        created_at=now,
                        updated_at=now,
                    )
                )
                record.lifecycle_state = new_state
                record.updated_at = now

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.LEGAL_HOLD_RELEASED,
                entity_type="RecordLegalHold",
                entity_id=hold.id,
                user_id=actor_id,
                new_values_json={"hold_number": hold.hold_number, "reason": hold.release_reason},
            )
        )

        await db.flush()
        await db.refresh(hold)
        return hold

    @classmethod
    async def list_legal_holds(
        cls, db: AsyncSession, tenant_id: UUID, status: str | None = None
    ) -> list[RecordLegalHold]:
        """Lists legal holds for the tenant."""
        stmt = select(RecordLegalHold).where(RecordLegalHold.tenant_id == tenant_id)
        if status:
            stmt = stmt.where(RecordLegalHold.status == status.upper().strip())
        stmt = stmt.order_by(RecordLegalHold.created_at.desc())
        return list((await db.scalars(stmt)).all())

    # =========================================================================
    # 8. CONTROLLED DISPOSITION WORKFLOW & CERTIFICATES
    # =========================================================================

    @classmethod
    async def create_disposition_request(
        cls, db: AsyncSession, tenant_id: UUID, payload: RecordDispositionRequestCreate, actor_id: UUID
    ) -> RecordDispositionRequest:
        """Creates a formal disposition request for batch authorization and execution."""
        now = datetime.now(UTC)
        req_num = f"DISP-{now.year}-{secrets.token_hex(4).upper()}"

        eligible_records: list[RecordRegistryEntry] = []
        for r_id in payload.record_ids:
            record = await cls.get_record(db, tenant_id, r_id)
            if record.is_held:
                raise LegalHoldActiveException(f"Record {record.record_number} is under active legal hold.")
            eligible_records.append(record)

        request = RecordDispositionRequest(
            id=uuid4(),
            tenant_id=tenant_id,
            request_number=req_num,
            policy_id=payload.policy_id,
            category_code=payload.category_code,
            requested_disposition_method=payload.requested_disposition_method,
            status=DispositionRequestStatus.PENDING_REVIEW,
            records_count=len(eligible_records),
            preview_stats_json={"eligible": len(eligible_records)},
            justification=payload.justification.strip(),
            requested_by_user_id=actor_id,
            created_at=now,
            updated_at=now,
        )
        db.add(request)

        for rec in eligible_records:
            item = RecordDispositionItem(
                id=uuid4(),
                tenant_id=tenant_id,
                request_id=request.id,
                record_id=rec.id,
                status=DispositionItemStatus.ELIGIBLE,
                created_at=now,
                updated_at=now,
            )
            db.add(item)

            # Move record to DISPOSITION_PENDING_APPROVAL
            await cls.transition_record_state(
                db=db,
                tenant_id=tenant_id,
                record_id=rec.id,
                payload=RecordLifecycleTransitionRequest(
                    target_state=RecordLifecycleState.DISPOSITION_PENDING_APPROVAL,
                    reason=f"Included in Disposition Request {req_num}.",
                ),
                trigger_action="DISPOSITION_REQUESTED",
                actor_id=actor_id,
            )

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.DISPOSITION_REQUESTED,
                entity_type="RecordDispositionRequest",
                entity_id=request.id,
                user_id=actor_id,
                new_values_json={"request_number": req_num, "records_count": request.records_count},
            )
        )

        await db.flush()
        await db.refresh(request)
        return request

    @classmethod
    async def approve_disposition_request(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        request_id: UUID,
        payload: RecordDispositionApproveRequest,
        actor_id: UUID,
    ) -> RecordDispositionRequest:
        """Approves a disposition request enforcing strict two-person separation of duties."""
        stmt = (
            select(RecordDispositionRequest)
            .options(selectinload(RecordDispositionRequest.items))
            .where(and_(RecordDispositionRequest.id == request_id, RecordDispositionRequest.tenant_id == tenant_id))
        )
        request = (await db.scalars(stmt)).first()
        if not request:
            raise NotFoundException("RecordDispositionRequest", request_id)

        if request.status != DispositionRequestStatus.PENDING_REVIEW:
            raise ConflictException(f"Cannot approve disposition request with status '{request.status}'.")

        # SEPARATION OF DUTIES ENFORCEMENT: Requester cannot approve their own disposition request!
        if request.requested_by_user_id == actor_id:
            raise DispositionApprovalRequiredException(
                "Separation of Duties Violation: You cannot approve a disposition request authored by yourself."
            )

        now = datetime.now(UTC)
        request.status = DispositionRequestStatus.APPROVED
        request.approved_by_user_id = actor_id
        request.approved_at = now
        request.reviewed_by_user_id = actor_id
        request.reviewed_at = now
        request.updated_at = now

        for item in request.items:
            await cls.transition_record_state(
                db=db,
                tenant_id=tenant_id,
                record_id=item.record_id,
                payload=RecordLifecycleTransitionRequest(
                    target_state=RecordLifecycleState.DISPOSITION_APPROVED,
                    reason=f"Approved under Disposition Request {request.request_number}.",
                ),
                trigger_action="DISPOSITION_APPROVED",
                actor_id=actor_id,
            )

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.DISPOSITION_APPROVED,
                entity_type="RecordDispositionRequest",
                entity_id=request.id,
                user_id=actor_id,
                new_values_json={"request_number": request.request_number, "approved_by": str(actor_id)},
            )
        )

        await db.flush()
        await db.refresh(request)
        return request

    @classmethod
    async def reject_disposition_request(
        cls, db: AsyncSession, tenant_id: UUID, request_id: UUID, payload: RecordDispositionRejectRequest, actor_id: UUID
    ) -> RecordDispositionRequest:
        """Rejects a disposition request and returns records back to DISPOSITION_ELIGIBLE state."""
        stmt = (
            select(RecordDispositionRequest)
            .options(selectinload(RecordDispositionRequest.items))
            .where(and_(RecordDispositionRequest.id == request_id, RecordDispositionRequest.tenant_id == tenant_id))
        )
        request = (await db.scalars(stmt)).first()
        if not request:
            raise NotFoundException("RecordDispositionRequest", request_id)

        now = datetime.now(UTC)
        request.status = DispositionRequestStatus.REJECTED
        request.rejection_reason = payload.rejection_reason.strip()
        request.reviewed_by_user_id = actor_id
        request.reviewed_at = now
        request.updated_at = now

        for item in request.items:
            await cls.transition_record_state(
                db=db,
                tenant_id=tenant_id,
                record_id=item.record_id,
                payload=RecordLifecycleTransitionRequest(
                    target_state=RecordLifecycleState.DISPOSITION_ELIGIBLE,
                    reason=f"Rejected in Disposition Request {request.request_number}: {payload.rejection_reason}",
                ),
                trigger_action="DISPOSITION_REJECTED",
                actor_id=actor_id,
            )

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.DISPOSITION_REJECTED,
                entity_type="RecordDispositionRequest",
                entity_id=request.id,
                user_id=actor_id,
                new_values_json={"request_number": request.request_number, "reason": payload.rejection_reason},
            )
        )

        await db.flush()
        await db.refresh(request)
        return request

    @classmethod
    async def execute_disposition(
        cls, db: AsyncSession, tenant_id: UUID, request_id: UUID, actor_id: UUID
    ) -> RecordDispositionCertificate:
        """Executes authorized record disposition, purges/anonymizes records, and issues a tamper-evident Certificate."""
        stmt = (
            select(RecordDispositionRequest)
            .options(selectinload(RecordDispositionRequest.items))
            .where(and_(RecordDispositionRequest.id == request_id, RecordDispositionRequest.tenant_id == tenant_id))
        )
        request = (await db.scalars(stmt)).first()
        if not request:
            raise NotFoundException("RecordDispositionRequest", request_id)

        if request.status != DispositionRequestStatus.APPROVED:
            raise ConflictException(f"Cannot execute disposition on request with status '{request.status}'. Approval is required.")

        now = datetime.now(UTC)
        request.status = DispositionRequestStatus.EXECUTING
        request.updated_at = now

        destroyed_count = 0
        anonymized_count = 0
        archived_count = 0
        manifest_tokens: list[str] = []

        storage = get_document_storage()

        for item in request.items:
            record = await cls.get_record(db, tenant_id, item.record_id)

            # Safeguard: Re-verify legal hold right before destruction
            if record.is_held:
                item.status = DispositionItemStatus.BLOCKED_HOLD
                item.error_message = "Blocked by active legal hold placed after approval."
                continue

            # Execute method
            method = request.requested_disposition_method
            if method == DispositionMethod.SECURE_DELETE:
                if record.storage_reference:
                    try:
                        await storage.delete(record.storage_reference)
                    except Exception as e:
                        logger.warning("Could not delete physical storage key %s: %s", record.storage_reference, e)
                record.storage_reference = None
                record.title = "[RECORD PERMANENTLY DESTROYED]"
                record.description = None
                destroyed_count += 1
            elif method == DispositionMethod.ANONYMIZE:
                record.title = f"[ANONYMIZED RECORD {record.record_number}]"
                record.description = "Identifiable institutional metadata anonymized under retention disposition."
                record.metadata_json = {"anonymized": True, "anonymized_at": now.isoformat()}
                anonymized_count += 1
            elif method == DispositionMethod.PERMANENT_ARCHIVE:
                archived_count += 1

            record.lifecycle_state = RecordLifecycleState.DISPOSITION_COMPLETED
            record.disposed_at = now
            record.updated_at = now

            item.status = DispositionItemStatus.EXECUTED
            item.disposed_at = now
            item.updated_at = now

            manifest_tokens.append(f"{record.record_number}:{record.id}")

            db.add(
                RecordLifecycleHistory(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    record_id=record.id,
                    from_state=RecordLifecycleState.DISPOSITION_APPROVED,
                    to_state=RecordLifecycleState.DISPOSITION_COMPLETED,
                    trigger_action="DISPOSITION_EXECUTION",
                    reason=f"Disposition completed via {method} under Certificate.",
                    actor_user_id=actor_id,
                    actor_role="DISPOSITION_OFFICER",
                    created_at=now,
                    updated_at=now,
                )
            )

        # Cryptographic certificate hash of all disposed records
        manifest_digest = hashlib.sha256(";".join(sorted(manifest_tokens)).encode()).hexdigest()
        cert_num = f"CERT-DISP-{now.year}-{secrets.token_hex(4).upper()}"

        certificate = RecordDispositionCertificate(
            id=uuid4(),
            tenant_id=tenant_id,
            certificate_number=cert_num,
            request_id=request.id,
            disposition_method=request.requested_disposition_method,
            total_records_destroyed=destroyed_count,
            total_records_anonymized=anonymized_count,
            total_records_archived=archived_count,
            disposition_manifest_hash=manifest_digest,
            executed_by_user_id=actor_id,
            approved_by_user_id=request.approved_by_user_id or actor_id,
            executed_at=now,
            certificate_metadata_json={
                "request_number": request.request_number,
                "justification": request.justification,
                "total_items": len(manifest_tokens),
            },
            created_at=now,
            updated_at=now,
        )
        db.add(certificate)

        request.status = DispositionRequestStatus.COMPLETED
        request.updated_at = now

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.DISPOSITION_EXECUTED,
                entity_type="RecordDispositionCertificate",
                entity_id=certificate.id,
                user_id=actor_id,
                new_values_json={"certificate_number": cert_num, "hash": manifest_digest, "total_executed": len(manifest_tokens)},
            )
        )

        await db.flush()
        await db.refresh(certificate)
        return certificate

    @classmethod
    async def get_disposition_certificate(
        cls, db: AsyncSession, tenant_id: UUID, cert_id: UUID
    ) -> RecordDispositionCertificate:
        """Fetch disposition certificate by ID."""
        stmt = select(RecordDispositionCertificate).where(
            and_(RecordDispositionCertificate.id == cert_id, RecordDispositionCertificate.tenant_id == tenant_id)
        )
        cert = (await db.scalars(stmt)).first()
        if not cert:
            raise NotFoundException("RecordDispositionCertificate", cert_id)
        return cert

    # =========================================================================
    # 9. SCHEDULED LIFECYCLE PROCESSING & BACKGROUND SWEEPS
    # =========================================================================

    @classmethod
    async def run_scheduled_lifecycle_sweep(
        cls, db: AsyncSession, tenant_id: UUID, job_type: ScheduledRunType, batch_size: int = 100
    ) -> RecordLifecycleScheduledRun:
        """Executes bounded, idempotent lifecycle processing sweeps across institutional records."""
        now = datetime.now(UTC)
        run = RecordLifecycleScheduledRun(
            id=uuid4(),
            tenant_id=tenant_id,
            job_type=job_type,
            status=ScheduledRunStatus.RUNNING,
            records_evaluated=0,
            records_transitioned=0,
            records_flagged_review=0,
            records_blocked=0,
            started_at=now,
            created_at=now,
            updated_at=now,
        )
        db.add(run)

        try:
            if job_type == ScheduledRunType.ELIGIBILITY_RECALCULATION:
                # Sweep records in ACTIVE or RETENTION_IN_PROGRESS
                stmt = (
                    select(RecordRegistryEntry)
                    .where(
                        and_(
                            RecordRegistryEntry.tenant_id == tenant_id,
                            RecordRegistryEntry.lifecycle_state.in_(
                                [RecordLifecycleState.ACTIVE, RecordLifecycleState.RETENTION_IN_PROGRESS]
                            ),
                        )
                    )
                    .limit(batch_size)
                )
                records = list((await db.scalars(stmt)).all())
                run.records_evaluated = len(records)

                for r in records:
                    eval_resp = await cls.evaluate_record_retention(db, tenant_id, r.id)
                    if eval_resp.recommended_state != r.lifecycle_state:
                        await cls.transition_record_state(
                            db=db,
                            tenant_id=tenant_id,
                            record_id=r.id,
                            payload=RecordLifecycleTransitionRequest(
                                target_state=eval_resp.recommended_state,
                                reason=f"Scheduled sweep transition: {eval_resp.evaluation_summary}",
                            ),
                            trigger_action="SCHEDULED_RECALCULATION",
                        )
                        run.records_transitioned += 1
                        if eval_resp.recommended_state == RecordLifecycleState.REVIEW_REQUIRED:
                            run.records_flagged_review += 1
                        elif eval_resp.is_held or eval_resp.has_dependency_block:
                            run.records_blocked += 1

            elif job_type == ScheduledRunType.HOLD_COVERAGE_CHECK:
                # Sweep active holds and apply to any newly created un-held matching records
                holds_stmt = select(RecordLegalHold).where(
                    and_(RecordLegalHold.tenant_id == tenant_id, RecordLegalHold.status == LegalHoldStatus.ACTIVE)
                )
                active_holds = list((await db.scalars(holds_stmt)).all())
                for h in active_holds:
                    unheld = await cls._find_records_matching_scope(db, tenant_id, h.scope_type, h.scope_value)
                    for rec in unheld:
                        run.records_evaluated += 1
                        # Check if already associated
                        assoc_exists = await db.scalar(
                            select(RecordLegalHoldAssociation).where(
                                and_(
                                    RecordLegalHoldAssociation.hold_id == h.id,
                                    RecordLegalHoldAssociation.record_id == rec.id,
                                    RecordLegalHoldAssociation.status == "ACTIVE",
                                )
                            )
                        )
                        if not assoc_exists:
                            rec.is_held = True
                            rec.active_hold_count += 1
                            rec.updated_at = now
                            db.add(
                                RecordLegalHoldAssociation(
                                    id=uuid4(),
                                    tenant_id=tenant_id,
                                    hold_id=h.id,
                                    record_id=rec.id,
                                    status="ACTIVE",
                                    applied_at=now,
                                    created_at=now,
                                    updated_at=now,
                                )
                            )
                            run.records_transitioned += 1

            run.status = ScheduledRunStatus.COMPLETED
            run.completed_at = datetime.now(UTC)
            run.summary_json = {
                "evaluated": run.records_evaluated,
                "transitioned": run.records_transitioned,
                "flagged_review": run.records_flagged_review,
                "blocked": run.records_blocked,
            }
        except Exception as exc:
            logger.error("Scheduled lifecycle run failed: %s", exc)
            run.status = ScheduledRunStatus.FAILED
            run.completed_at = datetime.now(UTC)
            run.error_message = str(exc)

        await db.flush()
        await db.refresh(run)
        return run

    @classmethod
    async def get_dashboard_summary(cls, db: AsyncSession, tenant_id: UUID) -> RecordLifecycleDashboardSummary:
        """Aggregates high-level telemetry indicators for tenant records lifecycle overview."""
        # Query record counts by lifecycle state
        state_counts_query = (
            select(RecordRegistryEntry.lifecycle_state, func.count(RecordRegistryEntry.id))
            .where(RecordRegistryEntry.tenant_id == tenant_id)
            .group_by(RecordRegistryEntry.lifecycle_state)
        )
        state_map = dict(list((await db.execute(state_counts_query)).all()))

        active_holds_count = await db.scalar(
            select(func.count(RecordLegalHold.id)).where(
                and_(RecordLegalHold.tenant_id == tenant_id, RecordLegalHold.status == LegalHoldStatus.ACTIVE)
            )
        ) or 0

        published_policies_count = await db.scalar(
            select(func.count(RetentionPolicyDefinition.id)).where(
                and_(
                    RetentionPolicyDefinition.tenant_id == tenant_id,
                    RetentionPolicyDefinition.status == RetentionPolicyStatus.PUBLISHED,
                )
            )
        ) or 0

        pending_disp_count = await db.scalar(
            select(func.count(RecordDispositionRequest.id)).where(
                and_(
                    RecordDispositionRequest.tenant_id == tenant_id,
                    RecordDispositionRequest.status == DispositionRequestStatus.PENDING_REVIEW,
                )
            )
        ) or 0

        total_records = sum(state_map.values())
        return RecordLifecycleDashboardSummary(
            total_records=total_records,
            active_records=state_map.get(RecordLifecycleState.ACTIVE, 0),
            retention_pending_records=state_map.get(RecordLifecycleState.RETENTION_PENDING, 0),
            archived_records=state_map.get(RecordLifecycleState.ARCHIVED, 0),
            legal_hold_records=state_map.get(RecordLifecycleState.LEGAL_HOLD, 0),
            disposition_eligible_records=state_map.get(RecordLifecycleState.DISPOSITION_ELIGIBLE, 0),
            review_required_records=state_map.get(RecordLifecycleState.REVIEW_REQUIRED, 0),
            active_holds_count=active_holds_count,
            published_policies_count=published_policies_count,
            pending_disposition_requests_count=pending_disp_count,
        )

    # =========================================================================
    # INTERNAL HELPERS
    # =========================================================================

    @staticmethod
    def _calculate_duration_days(duration: int, unit: RetentionUnit) -> int:
        if unit == RetentionUnit.DAYS:
            return duration
        elif unit == RetentionUnit.MONTHS:
            return duration * 30
        elif unit == RetentionUnit.YEARS:
            return duration * 365
        elif unit == RetentionUnit.PERMANENT:
            return 365000  # ~1000 years
        return duration * 365

    @classmethod
    async def _apply_matching_active_holds(
        cls, db: AsyncSession, tenant_id: UUID, record: RecordRegistryEntry
    ) -> None:
        """Matches active legal holds against a registered record and links them."""
        stmt = select(RecordLegalHold).where(
            and_(RecordLegalHold.tenant_id == tenant_id, RecordLegalHold.status == LegalHoldStatus.ACTIVE)
        )
        active_holds = (await db.scalars(stmt)).all()
        now = datetime.now(UTC)

        for hold in active_holds:
            matches = False
            if hold.scope_type == LegalHoldScope.ALL:
                matches = True
            elif hold.scope_type == LegalHoldScope.CATEGORY and hold.scope_value == record.category_code:
                matches = True
            elif hold.scope_type == LegalHoldScope.MODULE and hold.scope_value == record.source_module:
                matches = True
            elif hold.scope_type == LegalHoldScope.SPECIFIC_RECORD and hold.scope_value == str(record.id):
                matches = True

            if matches:
                record.is_held = True
                record.active_hold_count += 1
                record.lifecycle_state = RecordLifecycleState.LEGAL_HOLD
                db.add(
                    RecordLegalHoldAssociation(
                        id=uuid4(),
                        tenant_id=tenant_id,
                        hold_id=hold.id,
                        record_id=record.id,
                        status="ACTIVE",
                        applied_at=now,
                        created_at=now,
                        updated_at=now,
                    )
                )

    @classmethod
    async def _find_records_matching_scope(
        cls, db: AsyncSession, tenant_id: UUID, scope_type: LegalHoldScope, scope_value: str | None
    ) -> list[RecordRegistryEntry]:
        """Resolves registered records matching a legal hold scope."""
        stmt = select(RecordRegistryEntry).where(RecordRegistryEntry.tenant_id == tenant_id)
        if scope_type == LegalHoldScope.ALL:
            pass
        elif scope_type == LegalHoldScope.CATEGORY and scope_value:
            stmt = stmt.where(RecordRegistryEntry.category_code == scope_value.upper().strip())
        elif scope_type == LegalHoldScope.MODULE and scope_value:
            stmt = stmt.where(RecordRegistryEntry.source_module == scope_value.lower().strip())
        elif scope_type == LegalHoldScope.SPECIFIC_RECORD and scope_value:
            try:
                rec_uuid = UUID(scope_value)
                stmt = stmt.where(RecordRegistryEntry.id == rec_uuid)
            except ValueError:
                stmt = stmt.where(RecordRegistryEntry.record_number == scope_value.strip())
        elif scope_type == LegalHoldScope.DEPARTMENT and scope_value:
            try:
                dept_uuid = UUID(scope_value)
                stmt = stmt.where(RecordRegistryEntry.owner_department_id == dept_uuid)
            except ValueError:
                stmt = stmt.where(RecordRegistryEntry.responsible_department == scope_value.strip())

        return list((await db.scalars(stmt)).all())
