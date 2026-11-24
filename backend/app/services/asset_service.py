"""CampusOS Enterprise Asset Lifecycle, Maintenance, Facilities & Equipment Management Service (Step 53).

CampusOS Tagline: "One Campus. One System. One Source of Truth."
"""

import logging
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit import record_audit_log
from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from app.models.assets import (
    Asset,
    AssetAssignment,
    AssetAuditCampaign,
    AssetAuditItem,
    AssetCategory,
    AssetCondition,
    AssetDepreciationSchedule,
    AssetLifecycleEvent,
    AssetLifecycleState,
    AssetOperationalStatus,
    AssetRetirementRequest,
    AssetTransfer,
    AssetWarrantyContract,
    AssignmentStatus,
    AuditCampaignStatus,
    AuditReconciliationStatus,
    AuditVerificationStatus,
    ContractStatus,
    InspectionActionTaken,
    InspectionOutcome,
    InspectionRecord,
    InspectionTemplate,
    MaintenanceOrderStatus,
    MaintenanceOrderType,
    MaintenancePlan,
    MaintenancePriority,
    MaintenanceWorkOrder,
    PartConsumptionStatus,
    RetirementRequestStatus,
    TransferStatus,
    WarrantyClaim,
    WarrantyClaimStatus,
    WorkOrderPartConsumption,
)
from app.models.procurement import (
    InventoryItem,
    MovementType,
    StockBalance,
    StockMovement,
)
from app.models.workflow import OutboxEvent
from app.schemas.assets import (
    AssetAssignmentCreate,
    AssetBulkCreateRequest,
    AssetBulkCreateResponse,
    AssetCategoryCreate,
    AssetCategoryUpdate,
    AssetCreate,
    AssetLifecycleTransitionRequest,
    AssetRetirementRequestCreate,
    AssetTransferCreate,
    AssetUpdate,
    InspectionTemplateCreate,
    MaintenancePlanCreate,
    MaintenanceWorkOrderCloseRequest,
    MaintenanceWorkOrderCreate,
    MaintenanceWorkOrderUpdate,
    PartReservationRequest,
)

logger = logging.getLogger("campusos.assets")

# Validated lifecycle state machine allowed transitions
LIFECYCLE_TRANSITIONS: dict[str, list[str]] = {
    AssetLifecycleState.REQUESTED: [
        AssetLifecycleState.ORDERED,
        AssetLifecycleState.RECEIVED,
        AssetLifecycleState.RETIRED,
    ],
    AssetLifecycleState.ORDERED: [
        AssetLifecycleState.RECEIVED,
        AssetLifecycleState.REQUESTED,
    ],
    AssetLifecycleState.RECEIVED: [
        AssetLifecycleState.UNDER_INSPECTION,
        AssetLifecycleState.COMMISSIONED,
        AssetLifecycleState.DAMAGED,
    ],
    AssetLifecycleState.UNDER_INSPECTION: [
        AssetLifecycleState.COMMISSIONED,
        AssetLifecycleState.DAMAGED,
        AssetLifecycleState.RETIRED,
    ],
    AssetLifecycleState.COMMISSIONED: [
        AssetLifecycleState.IN_SERVICE,
        AssetLifecycleState.TEMPORARILY_UNAVAILABLE,
    ],
    AssetLifecycleState.IN_SERVICE: [
        AssetLifecycleState.UNDER_MAINTENANCE,
        AssetLifecycleState.TEMPORARILY_UNAVAILABLE,
        AssetLifecycleState.LOST_OR_MISSING,
        AssetLifecycleState.DAMAGED,
        AssetLifecycleState.PENDING_DISPOSAL,
        AssetLifecycleState.RETIRED,
    ],
    AssetLifecycleState.UNDER_MAINTENANCE: [
        AssetLifecycleState.IN_SERVICE,
        AssetLifecycleState.TEMPORARILY_UNAVAILABLE,
        AssetLifecycleState.DAMAGED,
        AssetLifecycleState.PENDING_DISPOSAL,
        AssetLifecycleState.RETIRED,
    ],
    AssetLifecycleState.TEMPORARILY_UNAVAILABLE: [
        AssetLifecycleState.IN_SERVICE,
        AssetLifecycleState.UNDER_MAINTENANCE,
        AssetLifecycleState.DAMAGED,
        AssetLifecycleState.LOST_OR_MISSING,
        AssetLifecycleState.PENDING_DISPOSAL,
        AssetLifecycleState.RETIRED,
    ],
    AssetLifecycleState.LOST_OR_MISSING: [
        AssetLifecycleState.IN_SERVICE,
        AssetLifecycleState.UNDER_MAINTENANCE,
        AssetLifecycleState.DAMAGED,
        AssetLifecycleState.PENDING_DISPOSAL,
        AssetLifecycleState.RETIRED,
    ],
    AssetLifecycleState.DAMAGED: [
        AssetLifecycleState.UNDER_MAINTENANCE,
        AssetLifecycleState.PENDING_DISPOSAL,
        AssetLifecycleState.RETIRED,
    ],
    AssetLifecycleState.PENDING_DISPOSAL: [
        AssetLifecycleState.DISPOSED,
        AssetLifecycleState.IN_SERVICE,
        AssetLifecycleState.RETIRED,
    ],
    AssetLifecycleState.RETIRED: [
        AssetLifecycleState.PENDING_DISPOSAL,
        AssetLifecycleState.DISPOSED,
    ],
    AssetLifecycleState.DISPOSED: [],  # Terminal
}


class AssetService:
    """Enterprise domain service orchestrating institutional asset lifecycle, maintenance & facilities."""

    # =========================================================================
    # 1. ASSET CATEGORIES
    # =========================================================================

    @staticmethod
    async def list_categories(
        db: AsyncSession, tenant_id: UUID, is_active: bool | None = None
    ) -> list[AssetCategory]:
        stmt = select(AssetCategory).where(AssetCategory.tenant_id == tenant_id)
        if is_active is not None:
            stmt = stmt.where(AssetCategory.is_active == is_active)
        stmt = stmt.order_by(AssetCategory.name.asc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_category(db: AsyncSession, tenant_id: UUID, category_id: UUID) -> AssetCategory:
        stmt = select(AssetCategory).where(
            and_(AssetCategory.tenant_id == tenant_id, AssetCategory.id == category_id)
        )
        result = await db.execute(stmt)
        category = result.scalar_one_or_none()
        if not category:
            raise NotFoundException(f"Asset category {category_id} not found.")
        return category

    @staticmethod
    async def create_category(
        db: AsyncSession, tenant_id: UUID, payload: AssetCategoryCreate, current_user_id: UUID | None = None
    ) -> AssetCategory:
        existing = await db.execute(
            select(AssetCategory).where(
                and_(AssetCategory.tenant_id == tenant_id, AssetCategory.code == payload.code.strip().upper())
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictException(f"Asset category code '{payload.code}' already exists.")

        category = AssetCategory(
            id=uuid4(),
            tenant_id=tenant_id,
            code=payload.code.strip().upper(),
            name=payload.name.strip(),
            description=payload.description,
            category_type=payload.category_type,
            is_active=payload.is_active,
            requires_serial_number=payload.requires_serial_number,
            requires_custodian_acknowledgement=payload.requires_custodian_acknowledgement,
            default_inspection_interval_days=payload.default_inspection_interval_days,
            default_maintenance_interval_days=payload.default_maintenance_interval_days,
            default_criticality=payload.default_criticality,
            default_depreciation_method=payload.default_depreciation_method,
            default_useful_life_months=payload.default_useful_life_months,
            default_salvage_value_percent=payload.default_salvage_value_percent,
            policy_schema=payload.policy_schema,
            assignment_restrictions=payload.assignment_restrictions,
        )
        db.add(category)
        await db.commit()
        await db.refresh(category)
        return category

    @staticmethod
    async def update_category(
        db: AsyncSession, tenant_id: UUID, category_id: UUID, payload: AssetCategoryUpdate
    ) -> AssetCategory:
        category = await AssetService.get_category(db, tenant_id, category_id)
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(category, field, value)
        await db.commit()
        await db.refresh(category)
        return category

    # =========================================================================
    # 2. ASSET REGISTRY & BULK REGISTRATION
    # =========================================================================

    @staticmethod
    async def generate_asset_tag(db: AsyncSession, tenant_id: UUID) -> str:
        current_year = date.today().year
        prefix = f"AST-{current_year}-"
        stmt = (
            select(func.count(Asset.id))
            .where(and_(Asset.tenant_id == tenant_id, Asset.asset_tag.like(f"{prefix}%")))
        )
        count = (await db.execute(stmt)).scalar() or 0
        return f"{prefix}{count + 1:05d}"

    @staticmethod
    async def list_assets(
        db: AsyncSession,
        tenant_id: UUID,
        category_id: UUID | None = None,
        lifecycle_state: str | None = None,
        operational_status: str | None = None,
        campus_id: UUID | None = None,
        department_id: UUID | None = None,
        custodian_id: UUID | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Asset]:
        stmt = (
            select(Asset)
            .options(selectinload(Asset.category))
            .where(Asset.tenant_id == tenant_id)
        )
        if category_id:
            stmt = stmt.where(Asset.category_id == category_id)
        if lifecycle_state:
            stmt = stmt.where(Asset.lifecycle_state == lifecycle_state)
        if operational_status:
            stmt = stmt.where(Asset.operational_status == operational_status)
        if campus_id:
            stmt = stmt.where(Asset.campus_id == campus_id)
        if department_id:
            stmt = stmt.where(Asset.department_id == department_id)
        if custodian_id:
            stmt = stmt.where(Asset.current_custodian_id == custodian_id)
        if search:
            q = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Asset.asset_tag.ilike(q),
                    Asset.name.ilike(q),
                    Asset.serial_number.ilike(q),
                    Asset.make.ilike(q),
                    Asset.model.ilike(q),
                )
            )
        stmt = stmt.order_by(Asset.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_asset(db: AsyncSession, tenant_id: UUID, asset_id: UUID) -> Asset:
        stmt = (
            select(Asset)
            .options(
                selectinload(Asset.category),
                selectinload(Asset.assignments),
                selectinload(Asset.work_orders),
                selectinload(Asset.inspections),
                selectinload(Asset.warranty_contracts),
                selectinload(Asset.lifecycle_history),
                selectinload(Asset.depreciation_schedules),
            )
            .where(and_(Asset.tenant_id == tenant_id, Asset.id == asset_id))
        )
        result = await db.execute(stmt)
        asset = result.scalar_one_or_none()
        if not asset:
            raise NotFoundException(f"Asset {asset_id} not found.")
        return asset

    @staticmethod
    async def create_asset(
        db: AsyncSession, tenant_id: UUID, payload: AssetCreate, current_user_id: UUID
    ) -> Asset:
        category = await AssetService.get_category(db, tenant_id, payload.category_id)

        # Enforce serial number policy if configured
        if category.requires_serial_number and not payload.serial_number:
            raise BadRequestException(f"Category '{category.name}' requires a serial number.")

        tag = payload.asset_tag or await AssetService.generate_asset_tag(db, tenant_id)
        # Duplicate tag check
        existing_tag = await db.execute(
            select(Asset).where(and_(Asset.tenant_id == tenant_id, Asset.asset_tag == tag))
        )
        if existing_tag.scalar_one_or_none():
            raise ConflictException(f"Asset tag '{tag}' already exists in tenant.")

        # Duplicate serial check if provided
        if payload.serial_number:
            existing_serial = await db.execute(
                select(Asset).where(
                    and_(
                        Asset.tenant_id == tenant_id,
                        Asset.category_id == category.id,
                        Asset.serial_number == payload.serial_number.strip(),
                    )
                )
            )
            if existing_serial.scalar_one_or_none():
                raise ConflictException(
                    f"Asset with serial number '{payload.serial_number}' already exists in category '{category.name}'."
                )

        now = datetime.now(UTC)
        next_maint = (
            payload.acquisition_date + timedelta(days=category.default_maintenance_interval_days)
            if category.default_maintenance_interval_days
            else None
        )
        next_insp = (
            payload.acquisition_date + timedelta(days=category.default_inspection_interval_days)
            if category.default_inspection_interval_days
            else None
        )

        asset = Asset(
            id=uuid4(),
            tenant_id=tenant_id,
            asset_tag=tag,
            name=payload.name.strip(),
            description=payload.description,
            category_id=category.id,
            asset_type=payload.asset_type,
            make=payload.make,
            model=payload.model,
            serial_number=payload.serial_number.strip() if payload.serial_number else None,
            manufacturer=payload.manufacturer,
            barcode_data=payload.barcode_data or tag,
            acquisition_date=payload.acquisition_date,
            acquisition_cost=payload.acquisition_cost,
            currency=payload.currency,
            source=payload.source,
            supplier_vendor_id=payload.supplier_vendor_id,
            purchase_order_id=payload.purchase_order_id,
            purchase_order_line_id=payload.purchase_order_line_id,
            goods_receipt_id=payload.goods_receipt_id,
            invoice_reference=payload.invoice_reference,
            campus_id=payload.campus_id,
            building=payload.building,
            floor=payload.floor,
            room_number=payload.room_number,
            location_description=payload.location_description,
            department_id=payload.department_id,
            current_custodian_id=payload.current_custodian_id,
            condition=payload.condition,
            operational_status=payload.operational_status,
            criticality=payload.criticality or category.default_criticality,
            usage_classification=payload.usage_classification,
            lifecycle_state=payload.lifecycle_state,
            is_restricted=payload.is_restricted,
            restriction_reason=payload.restriction_reason,
            warranty_start_date=payload.warranty_start_date,
            warranty_end_date=payload.warranty_end_date,
            next_maintenance_due=next_maint,
            next_inspection_due=next_insp,
            depreciation_method=payload.depreciation_method or category.default_depreciation_method,
            useful_life_months=payload.useful_life_months or category.default_useful_life_months,
            salvage_value=payload.salvage_value or (payload.acquisition_cost * (category.default_salvage_value_percent / Decimal("100"))),
            accumulated_depreciation=Decimal("0.00"),
            current_book_value=payload.acquisition_cost,
            image_keys=payload.image_keys,
            document_references=payload.document_references,
            custom_attributes=payload.custom_attributes,
        )
        db.add(asset)

        # Outbox event
        outbox = OutboxEvent(
            id=uuid4(),
            tenant_id=tenant_id,
            event_type="asset.registered",
            aggregate_type="Asset",
            aggregate_id=asset.id,
            correlation_id=str(uuid4()),
            payload={
                "asset_tag": asset.asset_tag,
                "name": asset.name,
                "category_id": str(asset.category_id),
                "acquisition_cost": str(asset.acquisition_cost),
            },
            created_at=now,
        )
        db.add(outbox)

        await record_audit_log(
            db=db,
            tenant_id=tenant_id,
            user_id=current_user_id,
            action="CREATE",
            entity_type="Asset",
            entity_id=asset.id,
            new_values_json={"asset_tag": asset.asset_tag, "name": asset.name},
        )

        await db.commit()
        await db.refresh(asset)
        return asset

    @staticmethod
    async def update_asset(
        db: AsyncSession, tenant_id: UUID, asset_id: UUID, payload: AssetUpdate, current_user_id: UUID
    ) -> Asset:
        asset = await AssetService.get_asset(db, tenant_id, asset_id)

        # Prevent editing if retired or disposed
        if asset.lifecycle_state in [AssetLifecycleState.RETIRED, AssetLifecycleState.DISPOSED]:
            raise BadRequestException(
                f"Asset is in terminal state '{asset.lifecycle_state}' and cannot be modified."
            )

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(asset, field, value)

        await record_audit_log(
            db=db,
            tenant_id=tenant_id,
            user_id=current_user_id,
            action="UPDATE",
            entity_type="Asset",
            entity_id=asset.id,
            new_values_json=update_data,
        )

        await db.commit()
        await db.refresh(asset)
        return asset

    @staticmethod
    async def bulk_create_assets(
        db: AsyncSession, tenant_id: UUID, payload: AssetBulkCreateRequest, current_user_id: UUID
    ) -> AssetBulkCreateResponse:
        created = []
        errors = []
        skipped = 0

        for item in payload.assets:
            try:
                # Create in sub-transaction / savepoint
                asset = await AssetService.create_asset(db, tenant_id, item, current_user_id)
                created.append(asset)
            except Exception as exc:
                skipped += 1
                errors.append(f"Asset '{item.name}': {str(exc)}")
                await db.rollback()

        return AssetBulkCreateResponse(
            created_count=len(created),
            skipped_count=skipped,
            errors=errors,
            created_assets=created,
        )

    # =========================================================================
    # 3. ASSET LIFECYCLE STATE MACHINE
    # =========================================================================

    @staticmethod
    async def transition_lifecycle(
        db: AsyncSession,
        tenant_id: UUID,
        asset_id: UUID,
        payload: AssetLifecycleTransitionRequest,
        current_user_id: UUID,
    ) -> Asset:
        asset = await AssetService.get_asset(db, tenant_id, asset_id)
        current_state = asset.lifecycle_state
        target_state = payload.to_state.strip().upper()

        if current_state == target_state:
            return asset

        allowed = LIFECYCLE_TRANSITIONS.get(current_state, [])
        if target_state not in allowed:
            raise BadRequestException(
                f"Cannot transition asset lifecycle from '{current_state}' to '{target_state}'. Allowed: {allowed}"
            )

        # Sensitive transition checks
        if target_state in [AssetLifecycleState.PENDING_DISPOSAL, AssetLifecycleState.DISPOSED]:
            # Verify open work orders
            open_wo = await db.execute(
                select(func.count(MaintenanceWorkOrder.id)).where(
                    and_(
                        MaintenanceWorkOrder.tenant_id == tenant_id,
                        MaintenanceWorkOrder.asset_id == asset_id,
                        MaintenanceWorkOrder.status.not_in([MaintenanceOrderStatus.CLOSED, MaintenanceOrderStatus.CANCELLED]),
                    )
                )
            )
            if (open_wo.scalar() or 0) > 0:
                raise BadRequestException("Cannot dispose asset while active maintenance work orders are unresolved.")

            # Verify active assignments
            active_assign = await db.execute(
                select(func.count(AssetAssignment.id)).where(
                    and_(
                        AssetAssignment.tenant_id == tenant_id,
                        AssetAssignment.asset_id == asset_id,
                        AssetAssignment.status.in_([AssignmentStatus.ACTIVE, AssignmentStatus.PENDING_ACKNOWLEDGEMENT]),
                    )
                )
            )
            if (active_assign.scalar() or 0) > 0:
                raise BadRequestException("Cannot dispose asset while active custody assignments remain unreturned.")

        now = datetime.now(UTC)
        asset.lifecycle_state = target_state

        # Update operational status appropriately
        if target_state == AssetLifecycleState.UNDER_MAINTENANCE:
            asset.operational_status = AssetOperationalStatus.IN_MAINTENANCE
        elif target_state in [AssetLifecycleState.DAMAGED, AssetLifecycleState.LOST_OR_MISSING]:
            asset.operational_status = AssetOperationalStatus.NON_OPERATIONAL
        elif target_state in [AssetLifecycleState.RETIRED, AssetLifecycleState.DISPOSED]:
            asset.operational_status = AssetOperationalStatus.DECOMMISSIONED

        # Record event
        event = AssetLifecycleEvent(
            id=uuid4(),
            tenant_id=tenant_id,
            asset_id=asset.id,
            from_state=current_state,
            to_state=target_state,
            reason=payload.reason,
            supporting_documents=payload.supporting_documents,
            actor_id=current_user_id,
            performed_at=now,
            metadata_json=payload.metadata_json,
        )
        db.add(event)

        # Emit outbox event
        outbox = OutboxEvent(
            id=uuid4(),
            tenant_id=tenant_id,
            event_type="asset.lifecycle.transitioned",
            aggregate_type="Asset",
            aggregate_id=asset.id,
            correlation_id=str(uuid4()),
            payload={
                "asset_tag": asset.asset_tag,
                "from_state": current_state,
                "to_state": target_state,
                "reason": payload.reason,
            },
            created_at=now,
        )
        db.add(outbox)

        await record_audit_log(
            db=db,
            tenant_id=tenant_id,
            user_id=current_user_id,
            action="TRANSITION_LIFECYCLE",
            entity_type="Asset",
            entity_id=asset.id,
            new_values_json={"from": current_state, "to": target_state, "reason": payload.reason},
        )

        await db.commit()
        await db.refresh(asset)
        return asset

    # =========================================================================
    # 4. ASSET ASSIGNMENT & CUSTODY MANAGEMENT
    # =========================================================================

    @staticmethod
    async def assign_asset(
        db: AsyncSession, tenant_id: UUID, asset_id: UUID, payload: AssetAssignmentCreate, current_user_id: UUID
    ) -> AssetAssignment:
        asset = await AssetService.get_asset(db, tenant_id, asset_id)

        # Validate assignment eligibility
        if asset.lifecycle_state in [
            AssetLifecycleState.LOST_OR_MISSING,
            AssetLifecycleState.DAMAGED,
            AssetLifecycleState.PENDING_DISPOSAL,
            AssetLifecycleState.RETIRED,
            AssetLifecycleState.DISPOSED,
        ]:
            raise BadRequestException(f"Cannot assign asset in lifecycle state '{asset.lifecycle_state}'.")

        if asset.is_restricted:
            raise BadRequestException(f"Cannot assign restricted asset: {asset.restriction_reason}")

        # Check existing active assignment; prevent multiple simultaneous custodians
        active_stmt = select(AssetAssignment).where(
            and_(
                AssetAssignment.tenant_id == tenant_id,
                AssetAssignment.asset_id == asset_id,
                AssetAssignment.status.in_([AssignmentStatus.ACTIVE, AssignmentStatus.PENDING_ACKNOWLEDGEMENT]),
            )
        )
        active_res = await db.execute(active_stmt)
        active_assignments = active_res.scalars().all()
        if active_assignments:
            raise ConflictException(
                "Asset already has an active custody assignment. Return or reassign current custody first."
            )

        status = AssignmentStatus.PENDING_ACKNOWLEDGEMENT if payload.acknowledgement_required else AssignmentStatus.ACTIVE

        assignment = AssetAssignment(
            id=uuid4(),
            tenant_id=tenant_id,
            asset_id=asset.id,
            assignment_type=payload.assignment_type,
            custodian_id=payload.custodian_id,
            department_id=payload.department_id,
            campus_id=payload.campus_id or asset.campus_id,
            location_details=payload.location_details,
            effective_date=payload.effective_date,
            expected_return_date=payload.expected_return_date,
            status=status,
            acknowledgement_required=payload.acknowledgement_required,
            assigned_by_id=current_user_id,
            condition_at_assignment=payload.condition_at_assignment,
            handover_notes=payload.handover_notes,
            supporting_evidence=payload.supporting_evidence,
        )
        db.add(assignment)

        # Update Asset current custodian and department
        asset.current_custodian_id = payload.custodian_id
        if payload.department_id:
            asset.department_id = payload.department_id
        if payload.campus_id:
            asset.campus_id = payload.campus_id

        await record_audit_log(
            db=db,
            tenant_id=tenant_id,
            user_id=current_user_id,
            action="ASSIGN_CUSTODY",
            entity_type="Asset",
            entity_id=asset.id,
            new_values_json={"custodian_id": str(payload.custodian_id), "status": status},
        )

        await db.commit()
        await db.refresh(assignment)
        return assignment

    @staticmethod
    async def acknowledge_assignment(
        db: AsyncSession, tenant_id: UUID, assignment_id: UUID, current_user_id: UUID, notes: str | None = None
    ) -> AssetAssignment:
        stmt = select(AssetAssignment).where(
            and_(AssetAssignment.tenant_id == tenant_id, AssetAssignment.id == assignment_id)
        )
        res = await db.execute(stmt)
        assignment = res.scalar_one_or_none()
        if not assignment:
            raise NotFoundException(f"Assignment {assignment_id} not found.")

        if assignment.status != AssignmentStatus.PENDING_ACKNOWLEDGEMENT:
            raise BadRequestException(f"Assignment status is '{assignment.status}', not awaiting acknowledgement.")

        assignment.status = AssignmentStatus.ACTIVE
        assignment.acknowledged_at = datetime.now(UTC)
        assignment.acknowledgement_notes = notes

        await db.commit()
        await db.refresh(assignment)
        return assignment

    @staticmethod
    async def return_assignment(
        db: AsyncSession,
        tenant_id: UUID,
        assignment_id: UUID,
        return_date: date,
        condition_at_return: str,
        current_user_id: UUID,
        handover_notes: str | None = None,
        evidence: list[dict[str, Any]] | None = None,
    ) -> AssetAssignment:
        stmt = select(AssetAssignment).where(
            and_(AssetAssignment.tenant_id == tenant_id, AssetAssignment.id == assignment_id)
        )
        res = await db.execute(stmt)
        assignment = res.scalar_one_or_none()
        if not assignment:
            raise NotFoundException(f"Assignment {assignment_id} not found.")

        if assignment.status not in [AssignmentStatus.ACTIVE, AssignmentStatus.PENDING_ACKNOWLEDGEMENT, AssignmentStatus.OVERDUE]:
            raise BadRequestException(f"Cannot return assignment with status '{assignment.status}'.")

        assignment.actual_return_date = return_date
        assignment.status = AssignmentStatus.RETURNED
        assignment.condition_at_return = condition_at_return
        if handover_notes:
            assignment.handover_notes = handover_notes
        if evidence:
            assignment.supporting_evidence.extend(evidence)

        # Clear custodian on Asset
        asset = await AssetService.get_asset(db, tenant_id, assignment.asset_id)
        asset.current_custodian_id = None
        asset.condition = condition_at_return

        await db.commit()
        await db.refresh(assignment)
        return assignment

    @staticmethod
    async def transfer_asset(
        db: AsyncSession, tenant_id: UUID, asset_id: UUID, payload: AssetTransferCreate, current_user_id: UUID
    ) -> AssetTransfer:
        asset = await AssetService.get_asset(db, tenant_id, asset_id)

        # Prevent transfer if retired or disposed
        if asset.lifecycle_state in [AssetLifecycleState.RETIRED, AssetLifecycleState.DISPOSED]:
            raise BadRequestException(f"Cannot transfer asset in terminal state '{asset.lifecycle_state}'.")

        current_year = date.today().year
        transfer_count = (
            await db.execute(
                select(func.count(AssetTransfer.id)).where(
                    and_(AssetTransfer.tenant_id == tenant_id, AssetTransfer.transfer_number.like(f"TRF-{current_year}-%"))
                )
            )
        ).scalar() or 0
        transfer_num = f"TRF-{current_year}-{transfer_count + 1:04d}"

        transfer = AssetTransfer(
            id=uuid4(),
            tenant_id=tenant_id,
            transfer_number=transfer_num,
            asset_id=asset.id,
            from_campus_id=asset.campus_id,
            from_department_id=asset.department_id,
            from_custodian_id=asset.current_custodian_id,
            to_campus_id=payload.to_campus_id,
            to_department_id=payload.to_department_id,
            to_custodian_id=payload.to_custodian_id,
            transfer_reason=payload.transfer_reason,
            status=TransferStatus.PENDING_DISPATCH,
            initiated_by_id=current_user_id,
            dispatch_notes=payload.dispatch_notes,
        )
        db.add(transfer)
        await db.commit()
        await db.refresh(transfer)
        return transfer

    @staticmethod
    async def process_transfer_action(
        db: AsyncSession, tenant_id: UUID, transfer_id: UUID, action: str, current_user_id: UUID, notes: str | None = None
    ) -> AssetTransfer:
        stmt = select(AssetTransfer).where(
            and_(AssetTransfer.tenant_id == tenant_id, AssetTransfer.id == transfer_id)
        )
        res = await db.execute(stmt)
        transfer = res.scalar_one_or_none()
        if not transfer:
            raise NotFoundException(f"Transfer {transfer_id} not found.")

        now = datetime.now(UTC)
        act = action.strip().upper()

        if act == "APPROVE":
            if transfer.status != TransferStatus.REQUESTED:
                raise BadRequestException(f"Cannot approve transfer with status '{transfer.status}'.")
            transfer.status = TransferStatus.APPROVED
            transfer.approved_by_id = current_user_id
            transfer.approved_at = now

        elif act == "DISPATCH":
            if transfer.status not in (TransferStatus.PENDING_DISPATCH, TransferStatus.APPROVED):
                raise BadRequestException(f"Cannot dispatch transfer with status '{transfer.status}'.")
            transfer.status = TransferStatus.IN_TRANSIT
            transfer.in_transit_at = now
            if notes:
                transfer.dispatch_notes = notes
            # Asset marked temporarily unavailable while in transit
            asset = await AssetService.get_asset(db, tenant_id, transfer.asset_id)
            asset.lifecycle_state = AssetLifecycleState.TEMPORARILY_UNAVAILABLE

        elif act == "RECEIVE":
            if transfer.status != TransferStatus.IN_TRANSIT:
                raise BadRequestException(f"Cannot receive transfer with status '{transfer.status}'.")
            transfer.status = TransferStatus.COMPLETED
            transfer.completed_at = now
            transfer.received_by_id = current_user_id
            if notes:
                transfer.acceptance_notes = notes

            # Authoritative Asset update
            asset = await AssetService.get_asset(db, tenant_id, transfer.asset_id)
            if transfer.to_campus_id:
                asset.campus_id = transfer.to_campus_id
            if transfer.to_department_id:
                asset.department_id = transfer.to_department_id
            if transfer.to_custodian_id:
                asset.current_custodian_id = transfer.to_custodian_id
            asset.lifecycle_state = AssetLifecycleState.IN_SERVICE

        elif act == "REJECT":
            transfer.status = TransferStatus.REJECTED
            transfer.rejection_reason = notes or "Rejected by reviewer."

        elif act == "CANCEL":
            transfer.status = TransferStatus.CANCELLED

        await db.commit()
        await db.refresh(transfer)
        return transfer

    # =========================================================================
    # 5. PREVENTIVE & CORRECTIVE MAINTENANCE
    # =========================================================================

    @staticmethod
    async def create_maintenance_plan(
        db: AsyncSession, tenant_id: UUID, payload: MaintenancePlanCreate, current_user_id: UUID | None = None
    ) -> MaintenancePlan:
        plan_code = payload.plan_code or f"PM-PLAN-{uuid4().hex[:6].upper()}"
        plan = MaintenancePlan(
            id=uuid4(),
            tenant_id=tenant_id,
            plan_code=plan_code,
            title=payload.title.strip(),
            description=payload.description,
            category_id=payload.category_id,
            asset_id=payload.asset_id,
            campus_id=payload.campus_id,
            department_id=payload.department_id,
            interval_days=payload.interval_days,
            estimated_duration_hours=payload.estimated_duration_hours,
            checklist=payload.checklist,
            assigned_technician_id=payload.assigned_technician_id,
            preferred_vendor_id=payload.preferred_vendor_id,
            is_active=payload.is_active,
        )
        db.add(plan)
        await db.commit()
        await db.refresh(plan)
        return plan

    @staticmethod
    async def list_maintenance_plans(
        db: AsyncSession, tenant_id: UUID, category_id: UUID | None = None
    ) -> list[MaintenancePlan]:
        stmt = select(MaintenancePlan).where(MaintenancePlan.tenant_id == tenant_id)
        if category_id:
            stmt = stmt.where(MaintenancePlan.category_id == category_id)
        stmt = stmt.order_by(MaintenancePlan.title.asc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create_work_order(
        db: AsyncSession, tenant_id: UUID, payload: MaintenanceWorkOrderCreate, current_user_id: UUID
    ) -> MaintenanceWorkOrder:
        asset = await AssetService.get_asset(db, tenant_id, payload.asset_id)

        # Generate Work Order Number
        current_year = date.today().year
        count_wo = (
            await db.execute(
                select(func.count(MaintenanceWorkOrder.id)).where(
                    and_(
                        MaintenanceWorkOrder.tenant_id == tenant_id,
                        MaintenanceWorkOrder.work_order_number.like(f"WO-{current_year}-%"),
                    )
                )
            )
        ).scalar() or 0
        wo_number = f"WO-{current_year}-{count_wo + 1:04d}"

        # If corrective/emergency or urgent/high priority, transition asset state
        if (
            payload.order_type in (MaintenanceOrderType.CORRECTIVE, MaintenanceOrderType.EMERGENCY)
            or payload.priority in ("HIGH", "URGENT", MaintenancePriority.HIGH, MaintenancePriority.URGENT)
        ):
            asset.lifecycle_state = AssetLifecycleState.UNDER_MAINTENANCE
            asset.operational_status = AssetOperationalStatus.IN_MAINTENANCE

        wo = MaintenanceWorkOrder(
            id=uuid4(),
            tenant_id=tenant_id,
            work_order_number=wo_number,
            asset_id=asset.id,
            plan_id=payload.plan_id,
            order_type=payload.order_type,
            priority=payload.priority,
            severity=payload.severity,
            operational_impact=payload.operational_impact,
            status=MaintenanceOrderStatus.REPORTED,
            reported_by_id=current_user_id,
            reported_symptoms=payload.reported_symptoms.strip(),
            scheduled_start_date=payload.scheduled_start_date,
            scheduled_end_date=payload.scheduled_end_date,
            assigned_technician_id=payload.assigned_technician_id,
            vendor_id=payload.vendor_id,
            estimated_cost=payload.estimated_cost,
            verification_required=payload.verification_required,
        )
        db.add(wo)

        # Outbox event
        outbox = OutboxEvent(
            id=uuid4(),
            tenant_id=tenant_id,
            event_type="asset.maintenance.created",
            aggregate_type="MaintenanceWorkOrder",
            aggregate_id=wo.id,
            correlation_id=str(uuid4()),
            payload={
                "work_order_number": wo.work_order_number,
                "asset_id": str(asset.id),
                "order_type": wo.order_type,
                "priority": wo.priority,
            },
            created_at=datetime.now(UTC),
        )
        db.add(outbox)

        await db.commit()
        await db.refresh(wo)
        return wo

    @staticmethod
    async def list_work_orders(
        db: AsyncSession,
        tenant_id: UUID,
        asset_id: UUID | None = None,
        status: str | None = None,
        priority: str | None = None,
        technician_id: UUID | None = None,
    ) -> list[MaintenanceWorkOrder]:
        stmt = (
            select(MaintenanceWorkOrder)
            .options(selectinload(MaintenanceWorkOrder.parts_consumed))
            .where(MaintenanceWorkOrder.tenant_id == tenant_id)
        )
        if asset_id:
            stmt = stmt.where(MaintenanceWorkOrder.asset_id == asset_id)
        if status:
            stmt = stmt.where(MaintenanceWorkOrder.status == status)
        if priority:
            stmt = stmt.where(MaintenanceWorkOrder.priority == priority)
        if technician_id:
            stmt = stmt.where(MaintenanceWorkOrder.assigned_technician_id == technician_id)
        stmt = stmt.order_by(MaintenanceWorkOrder.created_at.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_work_order(db: AsyncSession, tenant_id: UUID, work_order_id: UUID) -> MaintenanceWorkOrder:
        stmt = (
            select(MaintenanceWorkOrder)
            .options(selectinload(MaintenanceWorkOrder.parts_consumed))
            .where(and_(MaintenanceWorkOrder.tenant_id == tenant_id, MaintenanceWorkOrder.id == work_order_id))
        )
        res = await db.execute(stmt)
        wo = res.scalar_one_or_none()
        if not wo:
            raise NotFoundException(f"Work order {work_order_id} not found.")
        return wo

    @staticmethod
    async def update_work_order(
        db: AsyncSession,
        tenant_id: UUID,
        work_order_id: UUID,
        payload: MaintenanceWorkOrderUpdate,
        current_user_id: UUID,
    ) -> MaintenanceWorkOrder:
        wo = await AssetService.get_work_order(db, tenant_id, work_order_id)
        update_data = payload.model_dump(exclude_unset=True)

        # Track execution timestamp
        if payload.status == MaintenanceOrderStatus.IN_PROGRESS and not wo.actual_start_at:
            wo.actual_start_at = datetime.now(UTC)

        for field, value in update_data.items():
            setattr(wo, field, value)

        await db.commit()
        await db.refresh(wo)
        return wo

    @staticmethod
    async def close_work_order(
        db: AsyncSession,
        tenant_id: UUID,
        work_order_id: UUID,
        payload: MaintenanceWorkOrderCloseRequest,
        current_user_id: UUID,
    ) -> MaintenanceWorkOrder:
        wo = await AssetService.get_work_order(db, tenant_id, work_order_id)
        if wo.status in [MaintenanceOrderStatus.CLOSED, MaintenanceOrderStatus.CANCELLED]:
            raise BadRequestException(f"Work order is already in status '{wo.status}'.")

        now = datetime.now(UTC)
        wo.diagnosis = payload.diagnosis
        wo.repair_actions = payload.repair_actions
        wo.downtime_hours = payload.downtime_hours
        wo.labor_hours = payload.labor_hours
        wo.labor_cost = payload.labor_cost
        wo.service_charges = payload.service_charges
        wo.total_cost = wo.parts_cost + payload.labor_cost + payload.service_charges
        wo.completed_at = now
        wo.checklist_results = payload.checklist_results
        wo.attachments = payload.attachments

        if wo.verification_required:
            wo.status = MaintenanceOrderStatus.COMPLETED
        else:
            wo.status = MaintenanceOrderStatus.CLOSED
            wo.closed_at = now

        # Update Asset maintenance milestone
        asset = await AssetService.get_asset(db, tenant_id, wo.asset_id)
        asset.last_maintained_at = now
        if wo.plan_id:
            plan = (await db.execute(select(MaintenancePlan).where(MaintenancePlan.id == wo.plan_id))).scalar_one_or_none()
            if plan:
                asset.next_maintenance_due = date.today() + timedelta(days=plan.interval_days)

        # Return asset to service if not restricted by safety violation
        if not asset.is_restricted and asset.lifecycle_state == AssetLifecycleState.UNDER_MAINTENANCE:
            asset.lifecycle_state = AssetLifecycleState.IN_SERVICE
            asset.operational_status = AssetOperationalStatus.OPERATIONAL

        await db.commit()
        await db.refresh(wo)
        return wo

    @staticmethod
    async def verify_work_order(
        db: AsyncSession, tenant_id: UUID, work_order_id: UUID, notes: str | None, current_user_id: UUID
    ) -> MaintenanceWorkOrder:
        wo = await AssetService.get_work_order(db, tenant_id, work_order_id)
        if wo.status != MaintenanceOrderStatus.COMPLETED:
            raise BadRequestException(f"Work order status is '{wo.status}', not awaiting verification.")

        now = datetime.now(UTC)
        wo.status = MaintenanceOrderStatus.CLOSED
        wo.verified_by_id = current_user_id
        wo.verified_at = now
        wo.closed_at = now
        wo.verification_notes = notes

        await db.commit()
        await db.refresh(wo)
        return wo

    @staticmethod
    async def reopen_work_order(
        db: AsyncSession, tenant_id: UUID, work_order_id: UUID, reopen_reason: str, current_user_id: UUID
    ) -> MaintenanceWorkOrder:
        wo = await AssetService.get_work_order(db, tenant_id, work_order_id)
        if wo.status != MaintenanceOrderStatus.CLOSED:
            raise BadRequestException(f"Only closed work orders can be reopened. Current status: '{wo.status}'.")

        wo.status = MaintenanceOrderStatus.IN_PROGRESS
        wo.reopen_reason = reopen_reason
        wo.closed_at = None

        asset = await AssetService.get_asset(db, tenant_id, wo.asset_id)
        asset.lifecycle_state = AssetLifecycleState.UNDER_MAINTENANCE
        asset.operational_status = AssetOperationalStatus.IN_MAINTENANCE

        await db.commit()
        await db.refresh(wo)
        return wo

    # =========================================================================
    # 6. SPARE PARTS & INVENTORY INTEGRATION
    # =========================================================================

    @staticmethod
    async def reserve_work_order_part(
        db: AsyncSession, tenant_id: UUID, work_order_id: UUID, payload: PartReservationRequest, current_user_id: UUID
    ) -> WorkOrderPartConsumption:
        wo = await AssetService.get_work_order(db, tenant_id, work_order_id)
        if wo.status in [MaintenanceOrderStatus.CLOSED, MaintenanceOrderStatus.CANCELLED]:
            raise BadRequestException(f"Cannot reserve parts for work order with status '{wo.status}'.")

        # Check stock balance
        stmt = select(StockBalance).where(
            and_(
                StockBalance.tenant_id == tenant_id,
                StockBalance.item_id == payload.inventory_item_id,
                StockBalance.location_id == payload.inventory_location_id,
            )
        )
        res = await db.execute(stmt)
        balance = res.scalar_one_or_none()
        if not balance or balance.quantity_available < payload.quantity:
            avail = balance.quantity_available if balance else Decimal("0.00")
            raise BadRequestException(
                f"Insufficient stock available. Requested: {payload.quantity}, Available: {avail}."
            )

        # Fetch item unit price
        item = (
            await db.execute(select(InventoryItem).where(InventoryItem.id == payload.inventory_item_id))
        ).scalar_one_or_none()
        unit_cost = item.unit_price_average if item else Decimal("0.00")

        # Reserve quantity
        balance.quantity_reserved += payload.quantity
        balance.quantity_available -= payload.quantity

        part_res = WorkOrderPartConsumption(
            id=uuid4(),
            tenant_id=tenant_id,
            work_order_id=wo.id,
            inventory_item_id=payload.inventory_item_id,
            inventory_location_id=payload.inventory_location_id,
            quantity_reserved=payload.quantity,
            quantity_consumed=Decimal("0.00"),
            quantity_returned=Decimal("0.00"),
            unit_cost=unit_cost,
            total_cost=Decimal("0.00"),
            status=PartConsumptionStatus.RESERVED,
        )
        db.add(part_res)
        await db.commit()
        await db.refresh(part_res)
        return part_res

    @staticmethod
    async def consume_work_order_part(
        db: AsyncSession,
        tenant_id: UUID,
        part_consumption_id: UUID,
        quantity_to_consume: Decimal,
        current_user_id: UUID,
    ) -> WorkOrderPartConsumption:
        stmt = select(WorkOrderPartConsumption).where(
            and_(WorkOrderPartConsumption.tenant_id == tenant_id, WorkOrderPartConsumption.id == part_consumption_id)
        )
        res = await db.execute(stmt)
        pc = res.scalar_one_or_none()
        if not pc:
            raise NotFoundException(f"Part consumption record {part_consumption_id} not found.")

        if pc.status != PartConsumptionStatus.RESERVED:
            raise BadRequestException(f"Part status is '{pc.status}', cannot consume.")

        if quantity_to_consume > pc.quantity_reserved:
            raise BadRequestException(
                f"Cannot consume more than reserved quantity ({pc.quantity_reserved})."
            )

        # Update Stock Balance
        stmt_bal = select(StockBalance).where(
            and_(
                StockBalance.tenant_id == tenant_id,
                StockBalance.item_id == pc.inventory_item_id,
                StockBalance.location_id == pc.inventory_location_id,
            )
        )
        balance = (await db.execute(stmt_bal)).scalar_one_or_none()
        if balance:
            balance.quantity_on_hand -= quantity_to_consume
            balance.quantity_reserved -= quantity_to_consume

        # Record immutable Stock Movement
        now = datetime.now(UTC)
        current_year = date.today().year
        count_mov = (
            await db.execute(
                select(func.count(StockMovement.id)).where(StockMovement.tenant_id == tenant_id)
            )
        ).scalar() or 0
        mov_num = f"MOV-{current_year}-{count_mov + 1:05d}"

        total_value = quantity_to_consume * pc.unit_cost
        movement = StockMovement(
            id=uuid4(),
            tenant_id=tenant_id,
            movement_number=mov_num,
            item_id=pc.inventory_item_id,
            movement_type=MovementType.CONSUMPTION if hasattr(MovementType, "CONSUMPTION") else "MAINTENANCE_CONSUMPTION",
            source_location_id=pc.inventory_location_id,
            destination_location_id=None,
            quantity=quantity_to_consume,
            unit_cost=pc.unit_cost,
            total_value=total_value,
            reference_type="MAINTENANCE_WORK_ORDER",
            reference_id=pc.work_order_id,
            performed_by_id=current_user_id,
            timestamp=now,
            notes=f"Maintenance consumption for work order {pc.work_order_id}",
        )
        db.add(movement)

        # Update Part Consumption record
        pc.quantity_consumed = quantity_to_consume
        pc.total_cost = total_value
        pc.status = PartConsumptionStatus.CONSUMED
        pc.stock_movement_id = movement.id
        pc.consumed_at = now

        # Update Work Order total cost
        wo = await AssetService.get_work_order(db, tenant_id, pc.work_order_id)
        wo.parts_cost += total_value
        wo.total_cost += total_value

        await db.commit()
        await db.refresh(pc)
        return pc

    # =========================================================================
    # 7. INSPECTIONS, SAFETY & REGULATORY COMPLIANCE
    # =========================================================================

    @staticmethod
    async def create_inspection_template(
        db: AsyncSession, tenant_id: UUID, payload: InspectionTemplateCreate, current_user_id: UUID | None = None
    ) -> InspectionTemplate:
        template = InspectionTemplate(
            id=uuid4(),
            tenant_id=tenant_id,
            code=payload.code.strip().upper(),
            title=payload.title.strip(),
            description=payload.description,
            category_id=payload.category_id,
            frequency_days=payload.frequency_days,
            checklist_items=payload.checklist_items,
            is_mandatory=payload.is_mandatory,
            is_active=payload.is_active,
        )
        db.add(template)
        await db.commit()
        await db.refresh(template)
        return template

    @staticmethod
    async def list_inspection_templates(
        db: AsyncSession, tenant_id: UUID, category_id: UUID | None = None
    ) -> list[InspectionTemplate]:
        stmt = select(InspectionTemplate).where(InspectionTemplate.tenant_id == tenant_id)
        if category_id:
            stmt = stmt.where(InspectionTemplate.category_id == category_id)
        stmt = stmt.order_by(InspectionTemplate.title.asc())
        return list((await db.execute(stmt)).scalars().all())

    @staticmethod
    async def record_inspection(
        db: AsyncSession, tenant_id: UUID, *args: Any, **kwargs: Any
    ) -> InspectionRecord:
        if len(args) == 2:
            payload = args[0]
            current_user_id = args[1]
        elif len(args) >= 3:
            payload = args[1]
            current_user_id = args[2]
        else:
            payload = kwargs.get("payload")
            current_user_id = kwargs.get("current_user_id")

        asset = await AssetService.get_asset(db, tenant_id, payload.asset_id)

        current_year = date.today().year
        count_insp = (
            await db.execute(
                select(func.count(InspectionRecord.id)).where(
                    and_(
                        InspectionRecord.tenant_id == tenant_id,
                        InspectionRecord.inspection_number.like(f"INS-{current_year}-%"),
                    )
                )
            )
        ).scalar() or 0
        insp_number = f"INS-{current_year}-{count_insp + 1:04d}"

        action = payload.action_taken

        # Safety Enforcement: Critical inspection failures restrict the asset!
        if payload.overall_outcome == InspectionOutcome.FAIL or payload.safety_risk_detected:
            action = payload.action_taken or InspectionActionTaken.OPERATIONAL_RESTRICTION
            asset.is_restricted = True
            asset.restriction_reason = payload.findings_summary or "Critical safety inspection failure."
            asset.operational_status = AssetOperationalStatus.RESTRICTED
            asset.condition = AssetCondition.POOR
        else:
            asset.last_inspected_at = datetime.now(UTC)
            # Fetch template for next interval
            if payload.template_id:
                tpl = (await db.execute(select(InspectionTemplate).where(InspectionTemplate.id == payload.template_id))).scalar_one_or_none()
                if tpl:
                    asset.next_inspection_due = payload.inspection_date + timedelta(days=tpl.frequency_days)

        record = InspectionRecord(
            id=uuid4(),
            tenant_id=tenant_id,
            inspection_number=insp_number,
            asset_id=asset.id,
            template_id=payload.template_id,
            inspector_id=current_user_id,
            inspection_date=payload.inspection_date,
            overall_outcome=payload.overall_outcome,
            safety_risk_detected=payload.safety_risk_detected,
            action_taken=action,
            checklist_results=payload.checklist_results,
            findings_summary=payload.findings_summary,
            corrective_action_required=payload.corrective_action_required,
            corrective_action_due_date=payload.corrective_action_due_date,
            corrective_action_owner_id=payload.corrective_action_owner_id,
            corrective_action_status=payload.corrective_action_status,
            evidence_attachments=payload.evidence_attachments,
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return record

    # =========================================================================
    # 8. WARRANTIES & SERVICE CONTRACTS
    # =========================================================================

    @staticmethod
    async def create_warranty_contract(
        db: AsyncSession, tenant_id: UUID, *args: Any, **kwargs: Any
    ) -> AssetWarrantyContract:
        if len(args) == 1:
            payload = args[0]
        elif len(args) >= 2:
            payload = args[1]
        else:
            payload = kwargs.get("payload")

        asset_id = getattr(payload, "asset_id", None) or (args[0] if len(args) >= 2 else None)
        contract = AssetWarrantyContract(
            id=uuid4(),
            tenant_id=tenant_id,
            asset_id=asset_id,
            vendor_id=getattr(payload, "vendor_id", None),
            contract_type=getattr(payload, "contract_type", "WARRANTY"),
            contract_number=payload.contract_number,
            provider_name=payload.provider_name,
            start_date=payload.start_date,
            end_date=payload.end_date,
            coverage_terms=payload.coverage_terms,
            exclusions=getattr(payload, "exclusions", []),
            sla_response_hours=payload.sla_response_hours,
            cost=getattr(payload, "cost", Decimal("0.00")),
            status=getattr(payload, "status", "ACTIVE"),
            renewal_reminder_days=getattr(payload, "renewal_reminder_days", 30),
            documents=getattr(payload, "documents", []),
        )
        db.add(contract)

        # Update asset warranty dates
        if asset_id:
            asset = await AssetService.get_asset(db, tenant_id, asset_id)
            asset.warranty_start_date = payload.start_date
            asset.warranty_end_date = payload.end_date

        await db.commit()
        await db.refresh(contract)
        return contract

    @staticmethod
    async def create_warranty_claim(
        db: AsyncSession, tenant_id: UUID, *args: Any, **kwargs: Any
    ) -> WarrantyClaim:
        if len(args) == 2:
            payload = args[0]
            current_user_id = args[1]
        elif len(args) >= 3:
            payload = args[1]
            current_user_id = args[2]
        else:
            payload = kwargs.get("payload")
            current_user_id = kwargs.get("current_user_id")

        current_year = date.today().year
        count_clm = (
            await db.execute(
                select(func.count(WarrantyClaim.id)).where(
                    and_(
                        WarrantyClaim.tenant_id == tenant_id,
                        WarrantyClaim.claim_number.like(f"CLM-{current_year}-%"),
                    )
                )
            )
        ).scalar() or 0
        claim_num = f"CLM-{current_year}-{count_clm + 1:04d}"

        # Fetch contract
        contract = (
            await db.execute(select(AssetWarrantyContract).where(AssetWarrantyContract.id == payload.contract_id))
        ).scalar_one_or_none()
        if not contract:
            raise NotFoundException(f"Warranty contract {payload.contract_id} not found.")

        claim = WarrantyClaim(
            id=uuid4(),
            tenant_id=tenant_id,
            claim_number=claim_num,
            contract_id=contract.id,
            asset_id=contract.asset_id,
            incident_date=getattr(payload, "incident_date", None) or date.today(),
            issue_description=payload.issue_description,
            vendor_ticket_reference=payload.vendor_ticket_reference,
            status=WarrantyClaimStatus.FILED,
            supporting_evidence=getattr(payload, "supporting_evidence", None) or [],
        )
        db.add(claim)
        await db.commit()
        await db.refresh(claim)
        return claim

    # =========================================================================
    # 9. DEPRECIATION & FINANCIAL INTEGRATION
    # =========================================================================

    @staticmethod
    async def calculate_depreciation_period(
        db: AsyncSession,
        tenant_id: UUID,
        *args: Any,
        **kwargs: Any,
    ) -> list[AssetDepreciationSchedule]:
        if len(args) > 0 and hasattr(args[0], "fiscal_year"):
            req = args[0]
            fiscal_year = req.fiscal_year
            period_name = req.period_name
            period_start_date = req.period_start_date
            period_end_date = req.period_end_date
            asset_id = getattr(req, "asset_id", None)
        elif "payload" in kwargs:
            req = kwargs["payload"]
            fiscal_year = req.fiscal_year
            period_name = req.period_name
            period_start_date = req.period_start_date
            period_end_date = req.period_end_date
            asset_id = getattr(req, "asset_id", None)
        else:
            fiscal_year = args[0] if len(args) > 0 else kwargs.get("fiscal_year")
            period_name = args[1] if len(args) > 1 else kwargs.get("period_name")
            period_start_date = args[2] if len(args) > 2 else kwargs.get("period_start_date")
            period_end_date = args[3] if len(args) > 3 else kwargs.get("period_end_date")
            asset_id = args[4] if len(args) > 4 else kwargs.get("asset_id")

        # Query active assets
        if asset_id:
            stmt = select(Asset).where(
                and_(
                    Asset.tenant_id == tenant_id,
                    Asset.id == asset_id,
                    Asset.lifecycle_state != AssetLifecycleState.DISPOSED,
                )
            )
        else:
            stmt = select(Asset).where(
                and_(
                    Asset.tenant_id == tenant_id,
                    Asset.lifecycle_state.notin_([AssetLifecycleState.DISPOSED, AssetLifecycleState.REQUESTED]),
                )
            )

        assets = (await db.execute(stmt)).scalars().all()
        schedules = []

        for ast in assets:
            # Check existing schedule for this period
            existing = await db.execute(
                select(AssetDepreciationSchedule).where(
                    and_(
                        AssetDepreciationSchedule.tenant_id == tenant_id,
                        AssetDepreciationSchedule.asset_id == ast.id,
                        AssetDepreciationSchedule.fiscal_year == fiscal_year,
                        AssetDepreciationSchedule.period_name == period_name,
                    )
                )
            )
            if existing.scalar_one_or_none():
                continue

            opening_val = ast.current_book_value
            if opening_val <= ast.salvage_value or ast.useful_life_months <= 0:
                continue

            # Monthly Straight-Line Depreciation
            depreciable_base = ast.acquisition_cost - ast.salvage_value
            monthly_rate = depreciable_base / Decimal(ast.useful_life_months)

            # Cap depreciation to not fall below salvage value
            depr_amount = min(monthly_rate, opening_val - ast.salvage_value)
            closing_val = opening_val - depr_amount

            schedule = AssetDepreciationSchedule(
                id=uuid4(),
                tenant_id=tenant_id,
                asset_id=ast.id,
                fiscal_year=fiscal_year,
                period_name=period_name,
                period_start_date=period_start_date,
                period_end_date=period_end_date,
                opening_book_value=opening_val.quantize(Decimal("0.01")),
                depreciation_amount=depr_amount.quantize(Decimal("0.01")),
                closing_book_value=closing_val.quantize(Decimal("0.01")),
                is_posted=False,
            )
            db.add(schedule)
            schedules.append(schedule)

        await db.commit()
        return schedules

    @staticmethod
    async def post_depreciation_to_finance(
        db: AsyncSession,
        tenant_id: UUID,
        schedule_ids: list[UUID],
        journal_entry_ref: str | None,
        current_user_id: UUID,
    ) -> tuple[int, Decimal, str]:
        stmt = select(AssetDepreciationSchedule).where(
            and_(
                AssetDepreciationSchedule.tenant_id == tenant_id,
                AssetDepreciationSchedule.id.in_(schedule_ids),
                AssetDepreciationSchedule.is_posted.is_(False),
            )
        )
        schedules = (await db.execute(stmt)).scalars().all()
        if not schedules:
            raise BadRequestException("No unposted depreciation schedules found for specified IDs.")

        now = datetime.now(UTC)
        total_depr = Decimal("0.00")
        ref = journal_entry_ref or f"JE-DEPR-{date.today().year}-{uuid4().hex[:6].upper()}"

        for s in schedules:
            s.is_posted = True
            s.posted_at = now
            s.posted_by_id = current_user_id
            s.journal_entry_reference = ref
            total_depr += s.depreciation_amount

            # Update master Asset record
            ast = await AssetService.get_asset(db, tenant_id, s.asset_id)
            ast.accumulated_depreciation += s.depreciation_amount
            ast.current_book_value = s.closing_book_value
            ast.last_depreciated_date = s.period_end_date

        await db.commit()
        return len(schedules), total_depr, ref

    # =========================================================================
    # 10. PHYSICAL AUDITS & ASSET VERIFICATION
    # =========================================================================

    @staticmethod
    async def create_audit_campaign(
        db: AsyncSession, tenant_id: UUID, payload: Any, current_user_id: UUID
    ) -> AssetAuditCampaign:
        code = payload.campaign_code or f"AUD-{date.today().year}-{uuid4().hex[:4].upper()}"
        # Count scoped assets
        stmt = select(func.count(Asset.id)).where(Asset.tenant_id == tenant_id)
        if payload.campus_id:
            stmt = stmt.where(Asset.campus_id == payload.campus_id)
        if payload.department_id:
            stmt = stmt.where(Asset.department_id == payload.department_id)
        if payload.category_id:
            stmt = stmt.where(Asset.category_id == payload.category_id)
        scoped_count = (await db.execute(stmt)).scalar() or 0

        campaign = AssetAuditCampaign(
            id=uuid4(),
            tenant_id=tenant_id,
            campaign_code=code,
            title=payload.title.strip(),
            description=payload.description,
            campus_id=payload.campus_id,
            building=payload.building,
            department_id=payload.department_id,
            category_id=payload.category_id,
            start_date=payload.start_date,
            end_date=payload.end_date,
            status=AuditCampaignStatus.IN_PROGRESS,
            lead_auditor_id=payload.lead_auditor_id,
            total_assets_scoped=scoped_count,
            total_verified=0,
            total_discrepancies=0,
        )
        db.add(campaign)
        await db.commit()
        await db.refresh(campaign)
        return campaign

    @staticmethod
    async def record_audit_scan(
        db: AsyncSession, tenant_id: UUID, campaign_id: UUID, payload: Any, current_user_id: UUID
    ) -> AssetAuditItem:
        campaign = (
            await db.execute(
                select(AssetAuditCampaign).where(
                    and_(AssetAuditCampaign.tenant_id == tenant_id, AssetAuditCampaign.id == campaign_id)
                )
            )
        ).scalar_one_or_none()
        if not campaign:
            raise NotFoundException(f"Audit campaign {campaign_id} not found.")

        # Find asset by tag
        tag = payload.scanned_tag.strip().upper()
        ast = (
            await db.execute(
                select(Asset).where(and_(Asset.tenant_id == tenant_id, Asset.asset_tag == tag))
            )
        ).scalar_one_or_none()

        now = datetime.now(UTC)
        is_discrepancy = False

        if not ast:
            status = AuditVerificationStatus.UNREGISTERED_FOUND
            is_discrepancy = True
            expected_campus = None
            expected_bldg = None
            expected_room = None
            expected_cust = None
            expected_cond = None
        else:
            expected_campus = ast.campus_id
            expected_bldg = ast.building
            expected_room = ast.room_number
            expected_cust = ast.current_custodian_id
            expected_cond = ast.condition

            # Compare actual vs expected
            if payload.actual_campus_id and payload.actual_campus_id != ast.campus_id:
                status = AuditVerificationStatus.RELOCATED
                is_discrepancy = True
            elif payload.actual_custodian_id and payload.actual_custodian_id != ast.current_custodian_id:
                status = AuditVerificationStatus.CUSTODIAN_MISMATCH
                is_discrepancy = True
            elif payload.actual_condition and payload.actual_condition != ast.condition:
                status = AuditVerificationStatus.CONDITION_CHANGED
                is_discrepancy = True
            else:
                status = AuditVerificationStatus.VERIFIED_MATCH

        audit_item = AssetAuditItem(
            id=uuid4(),
            tenant_id=tenant_id,
            campaign_id=campaign.id,
            asset_id=ast.id if ast else None,
            scanned_tag=tag,
            verification_status=status,
            expected_campus_id=expected_campus,
            actual_campus_id=payload.actual_campus_id,
            expected_building=expected_bldg,
            actual_building=payload.actual_building,
            expected_room=expected_room,
            actual_room=payload.actual_room,
            expected_custodian_id=expected_cust,
            actual_custodian_id=payload.actual_custodian_id,
            expected_condition=expected_cond,
            actual_condition=payload.actual_condition,
            verified_by_id=current_user_id,
            verified_at=now,
            reconciliation_status=AuditReconciliationStatus.PENDING if is_discrepancy else AuditReconciliationStatus.RESOLVED,
            evidence_attachments=payload.evidence_attachments,
        )
        db.add(audit_item)

        campaign.total_verified += 1
        if is_discrepancy:
            campaign.total_discrepancies += 1

        await db.commit()
        await db.refresh(audit_item)
        return audit_item

    # =========================================================================
    # 11. ASSET RETIREMENT & DISPOSAL
    # =========================================================================

    @staticmethod
    async def request_retirement(
        db: AsyncSession, tenant_id: UUID, payload: AssetRetirementRequestCreate, current_user_id: UUID
    ) -> AssetRetirementRequest:
        asset = await AssetService.get_asset(db, tenant_id, payload.asset_id)

        # Pre-retirement checks: Active maintenance or active assignments block disposal!
        open_wo = (
            await db.execute(
                select(func.count(MaintenanceWorkOrder.id)).where(
                    and_(
                        MaintenanceWorkOrder.tenant_id == tenant_id,
                        MaintenanceWorkOrder.asset_id == asset.id,
                        MaintenanceWorkOrder.status.not_in([MaintenanceOrderStatus.CLOSED, MaintenanceOrderStatus.CANCELLED]),
                    )
                )
            )
        ).scalar() or 0
        if open_wo > 0:
            raise BadRequestException(
                "Cannot request retirement while active maintenance work orders are unresolved."
            )

        active_custody = (
            await db.execute(
                select(func.count(AssetAssignment.id)).where(
                    and_(
                        AssetAssignment.tenant_id == tenant_id,
                        AssetAssignment.asset_id == asset.id,
                        AssetAssignment.status.in_([AssignmentStatus.ACTIVE, AssignmentStatus.PENDING_ACKNOWLEDGEMENT]),
                    )
                )
            )
        ).scalar() or 0
        if active_custody > 0:
            raise BadRequestException(
                "Cannot request retirement while asset custody is still actively assigned to a custodian."
            )

        current_year = date.today().year
        count_ret = (
            await db.execute(
                select(func.count(AssetRetirementRequest.id)).where(
                    and_(
                        AssetRetirementRequest.tenant_id == tenant_id,
                        AssetRetirementRequest.request_number.like(f"RET-{current_year}-%"),
                    )
                )
            )
        ).scalar() or 0
        req_num = f"RET-{current_year}-{count_ret + 1:04d}"

        req = AssetRetirementRequest(
            id=uuid4(),
            tenant_id=tenant_id,
            request_number=req_num,
            asset_id=asset.id,
            requested_by_id=current_user_id,
            retirement_reason=payload.retirement_reason,
            disposal_method=payload.disposal_method,
            technical_assessment_notes=payload.technical_assessment_notes.strip(),
            estimated_residual_value=payload.estimated_residual_value,
            actual_realized_value=Decimal("0.00"),
            status=RetirementRequestStatus.SUBMITTED,
            reconciliation_checks_passed=True,
        )
        db.add(req)

        # Update Asset state to PENDING_DISPOSAL
        asset.lifecycle_state = AssetLifecycleState.PENDING_DISPOSAL

        await db.commit()
        await db.refresh(req)
        return req

    @staticmethod
    async def approve_retirement(
        db: AsyncSession, tenant_id: UUID, request_id: UUID, action: str, notes: str | None, current_user_id: UUID
    ) -> AssetRetirementRequest:
        stmt = select(AssetRetirementRequest).where(
            and_(AssetRetirementRequest.tenant_id == tenant_id, AssetRetirementRequest.id == request_id)
        )
        req = (await db.execute(stmt)).scalar_one_or_none()
        if not req:
            raise NotFoundException(f"Retirement request {request_id} not found.")

        act = action.strip().upper()
        asset = await AssetService.get_asset(db, tenant_id, req.asset_id)
        now = datetime.now(UTC)

        if act == "APPROVE":
            req.status = RetirementRequestStatus.APPROVED
            req.approved_by_id = current_user_id
            req.approved_at = now
            asset.lifecycle_state = AssetLifecycleState.RETIRED
        elif act == "REJECT":
            req.status = RetirementRequestStatus.REJECTED
            asset.lifecycle_state = AssetLifecycleState.IN_SERVICE

        await db.commit()
        await db.refresh(req)
        return req

    @staticmethod
    async def execute_disposal(
        db: AsyncSession, tenant_id: UUID, request_id: UUID, payload: Any, current_user_id: UUID
    ) -> AssetRetirementRequest:
        stmt = select(AssetRetirementRequest).where(
            and_(AssetRetirementRequest.tenant_id == tenant_id, AssetRetirementRequest.id == request_id)
        )
        req = (await db.execute(stmt)).scalar_one_or_none()
        if not req:
            raise NotFoundException(f"Retirement request {request_id} not found.")

        if req.status != RetirementRequestStatus.APPROVED:
            raise BadRequestException(f"Retirement request status is '{req.status}', must be APPROVED.")

        now = datetime.now(UTC)
        req.status = RetirementRequestStatus.DISPOSED
        req.actual_realized_value = payload.actual_realized_value
        req.data_wiped = payload.data_wiped
        req.data_wipe_certificate_url = payload.data_wipe_certificate_url
        req.disposal_certificate_url = payload.disposal_certificate_url
        req.completed_at = now

        asset = await AssetService.get_asset(db, tenant_id, req.asset_id)
        asset.lifecycle_state = AssetLifecycleState.DISPOSED
        asset.operational_status = AssetOperationalStatus.DECOMMISSIONED

        # Record terminal lifecycle event
        event = AssetLifecycleEvent(
            id=uuid4(),
            tenant_id=tenant_id,
            asset_id=asset.id,
            from_state=AssetLifecycleState.RETIRED,
            to_state=AssetLifecycleState.DISPOSED,
            reason=f"Certified disposal completed via {req.disposal_method}.",
            supporting_documents=[{"disposal_certificate": req.disposal_certificate_url}] if req.disposal_certificate_url else [],
            actor_id=current_user_id,
            performed_at=now,
            metadata_json={"realized_value": str(req.actual_realized_value)},
        )
        db.add(event)

        await db.commit()
        await db.refresh(req)
        return req

    # =========================================================================
    # 12. REPORTING & ANALYTICS
    # =========================================================================

    @staticmethod
    async def get_summary_analytics(db: AsyncSession, tenant_id: UUID) -> dict[str, Any]:
        stmt = select(Asset).where(Asset.tenant_id == tenant_id)
        assets = (await db.execute(stmt)).scalars().all()

        total_assets = len(assets)
        total_acq = sum((a.acquisition_cost for a in assets), Decimal("0.00"))
        total_book = sum((a.current_book_value for a in assets), Decimal("0.00"))
        total_depr = sum((a.accumulated_depreciation for a in assets), Decimal("0.00"))

        by_state: dict[str, int] = {}
        by_cat: dict[str, int] = {}
        by_crit: dict[str, int] = {}
        by_cond: dict[str, int] = {}
        missing_damaged = 0
        restricted = 0

        for a in assets:
            by_state[a.lifecycle_state] = by_state.get(a.lifecycle_state, 0) + 1
            by_cat[str(a.category_id)] = by_cat.get(str(a.category_id), 0) + 1
            by_crit[a.criticality] = by_crit.get(a.criticality, 0) + 1
            by_cond[a.condition] = by_cond.get(a.condition, 0) + 1

            if a.lifecycle_state in [AssetLifecycleState.LOST_OR_MISSING, AssetLifecycleState.DAMAGED]:
                missing_damaged += 1
            if a.is_restricted:
                restricted += 1

        return {
            "total_assets": total_assets,
            "total_acquisition_value": total_acq,
            "total_current_book_value": total_book,
            "total_accumulated_depreciation": total_depr,
            "assets_by_lifecycle_state": by_state,
            "assets_by_category": by_cat,
            "assets_by_criticality": by_crit,
            "assets_by_condition": by_cond,
            "missing_or_damaged_count": missing_damaged,
            "restricted_assets_count": restricted,
        }

    # =========================================================================
    # 13. BACKGROUND JOBS & SWEEPS
    # =========================================================================

    @staticmethod
    async def sweep_asset_maintenance_and_compliance(db: AsyncSession, tenant_id: UUID) -> dict[str, int]:
        """Tenant-isolated, idempotent background sweep for upcoming PM, overdue work orders, expiring warranties, and overdue loans."""
        today = date.today()
        now = datetime.now(UTC)
        metrics = {
            "pm_orders_generated": 0,
            "overdue_work_orders": 0,
            "expiring_warranties": 0,
            "overdue_loans": 0,
        }

        # 1. Check upcoming preventive maintenance
        stmt_pm = select(MaintenancePlan).where(
            and_(
                MaintenancePlan.tenant_id == tenant_id,
                MaintenancePlan.is_active.is_(True),
                MaintenancePlan.asset_id.is_not(None),
            )
        )
        plans = (await db.execute(stmt_pm)).scalars().all()
        for p in plans:
            ast = (await db.execute(select(Asset).where(Asset.id == p.asset_id))).scalar_one_or_none()
            if ast and ast.next_maintenance_due and ast.next_maintenance_due <= (today + timedelta(days=7)):
                # Check if open order already exists
                open_order = await db.execute(
                    select(MaintenanceWorkOrder).where(
                        and_(
                            MaintenanceWorkOrder.tenant_id == tenant_id,
                            MaintenanceWorkOrder.asset_id == ast.id,
                            MaintenanceWorkOrder.plan_id == p.id,
                            MaintenanceWorkOrder.status.notin_([MaintenanceOrderStatus.CLOSED, MaintenanceOrderStatus.CANCELLED]),
                        )
                    )
                )
                if not open_order.scalar_one_or_none():
                    current_year = today.year
                    count_wo = (
                        await db.execute(
                            select(func.count(MaintenanceWorkOrder.id)).where(
                                and_(
                                    MaintenanceWorkOrder.tenant_id == tenant_id,
                                    MaintenanceWorkOrder.work_order_number.like(f"WO-{current_year}-%"),
                                )
                            )
                        )
                    ).scalar() or 0
                    wo = MaintenanceWorkOrder(
                        id=uuid4(),
                        tenant_id=tenant_id,
                        work_order_number=f"WO-{current_year}-{count_wo + 1:04d}",
                        asset_id=ast.id,
                        plan_id=p.id,
                        order_type=MaintenanceOrderType.PREVENTIVE,
                        priority="MEDIUM",
                        severity="MINOR",
                        operational_impact="NO_IMPACT",
                        status=MaintenanceOrderStatus.SCHEDULED,
                        reported_by_id=p.assigned_technician_id or ast.id,
                        reported_symptoms=f"Scheduled preventive maintenance: {p.title}",
                        scheduled_start_date=ast.next_maintenance_due,
                        scheduled_end_date=ast.next_maintenance_due,
                        assigned_technician_id=p.assigned_technician_id,
                    )
                    db.add(wo)
                    metrics["pm_orders_generated"] += 1

        # 2. Check overdue work orders
        stmt_overdue = select(MaintenanceWorkOrder).where(
            and_(
                MaintenanceWorkOrder.tenant_id == tenant_id,
                MaintenanceWorkOrder.scheduled_end_date < today,
                MaintenanceWorkOrder.status.notin_([MaintenanceOrderStatus.CLOSED, MaintenanceOrderStatus.CANCELLED, MaintenanceOrderStatus.COMPLETED]),
            )
        )
        overdue_orders = (await db.execute(stmt_overdue)).scalars().all()
        metrics["overdue_work_orders"] = len(overdue_orders)

        # 3. Check expiring warranties
        stmt_warr = select(AssetWarrantyContract).where(
            and_(
                AssetWarrantyContract.tenant_id == tenant_id,
                AssetWarrantyContract.status == ContractStatus.ACTIVE,
                AssetWarrantyContract.end_date <= (today + timedelta(days=30)),
            )
        )
        expiring_contracts = (await db.execute(stmt_warr)).scalars().all()
        metrics["expiring_warranties"] = len(expiring_contracts)

        # 4. Check overdue loans
        stmt_loans = select(AssetAssignment).where(
            and_(
                AssetAssignment.tenant_id == tenant_id,
                AssetAssignment.status == AssignmentStatus.ACTIVE,
                AssetAssignment.expected_return_date < today,
            )
        )
        loans = (await db.execute(stmt_loans)).scalars().all()
        for loan in loans:
            loan.status = AssignmentStatus.OVERDUE
            metrics["overdue_loans"] += 1

        await db.commit()
        return metrics


asset_service = AssetService()
