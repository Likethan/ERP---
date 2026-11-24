"""CampusOS Enterprise Procurement, Vendor Management, Purchase Orders & Inventory Control Service (Step 50).

CampusOS Tagline: "One Campus. One System. One Source of Truth."
"""

import logging
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit import AuditEventCategory, record_audit_log
from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from app.models.procurement import (
    AmendmentStatus,
    AwardDecision,
    GoodsReceipt,
    GoodsReceiptLine,
    GoodsReceiptStatus,
    InternalRequestStatus,
    InternalStockRequest,
    InternalStockRequestLine,
    InventoryItem,
    InventoryLocation,
    InvoiceMatchStatus,
    MovementType,
    PurchaseOrder,
    PurchaseOrderAmendment,
    PurchaseOrderLine,
    PurchaseOrderStatus,
    PurchaseRequisition,
    PurchaseRequisitionLine,
    QualityInspectionStatus,
    QuotationEvaluation,
    QuotationRequest,
    QuotationStatus,
    RequisitionStatus,
    RfqStatus,
    StockBalance,
    StockMovement,
    SupplierInvoiceMatch,
    Vendor,
    VendorContact,
    VendorPerformanceReview,
    VendorQuotation,
    VendorReturn,
    VendorStatus,
)
from app.models.workflow import OutboxEvent
from app.schemas.procurement import (
    GoodsReceiptCreate,
    InternalStockRequestCreate,
    InternalStockRequestFulfillRequest,
    InventoryItemCreate,
    InventoryItemUpdate,
    InventoryLocationCreate,
    InventoryLocationUpdate,
    InventoryValuationReport,
    ProcurementSummaryReport,
    PurchaseOrderAmendmentCreate,
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    PurchaseRequisitionApprovalRequest,
    PurchaseRequisitionCreate,
    PurchaseRequisitionUpdate,
    QualityInspectionRecordRequest,
    QuotationEvaluationCreate,
    QuotationRequestCreate,
    QuotationRequestUpdate,
    StockMovementCreate,
    StockTransferRequest,
    SupplierInvoiceMatchCreate,
    SupplierInvoiceMatchOverrideRequest,
    VendorContactCreate,
    VendorContactUpdate,
    VendorCreate,
    VendorDuplicateCheckRequest,
    VendorDuplicateCheckResponse,
    VendorDuplicateMatch,
    VendorPerformanceReviewCreate,
    VendorQuotationCreate,
    VendorReturnCreate,
    VendorReturnStatusUpdateRequest,
    VendorStatusTransitionRequest,
    VendorUpdate,
)

logger = logging.getLogger(__name__)


class ProcurementService:
    """Core domain service orchestrating Enterprise Procurement, Vendor Management & Inventory Control."""

    # =========================================================================
    # 1. VENDOR & SUPPLIER MANAGEMENT
    # =========================================================================

    async def create_vendor(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        payload: VendorCreate,
        user_id: UUID,
    ) -> Vendor:
        # Check code uniqueness
        stmt = select(Vendor).where(
            Vendor.tenant_id == tenant_id,
            Vendor.code == payload.code,
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            raise ConflictException("Vendor", "code", payload.code)

        vendor = Vendor(
            tenant_id=tenant_id,
            code=payload.code,
            name=payload.name,
            legal_name=payload.legal_name,
            category=payload.category,
            classification=payload.classification,
            status=VendorStatus.PENDING,
            tax_identifier=payload.tax_identifier,
            email=payload.email,
            phone=payload.phone,
            website=payload.website,
            address_line1=payload.address_line1,
            address_line2=payload.address_line2,
            city=payload.city,
            state=payload.state,
            postal_code=payload.postal_code,
            country=payload.country,
            payment_terms_days=payload.payment_terms_days,
            rating_score=Decimal("5.00"),
            is_verified=False,
            documents_json=payload.documents_json,
            bank_details_masked=payload.bank_details_masked,
            metadata_json=payload.metadata_json,
        )
        db.add(vendor)
        await db.flush()

        for c in payload.contacts:
            contact = VendorContact(
                tenant_id=tenant_id,
                vendor_id=vendor.id,
                name=c.name,
                designation=c.designation,
                email=c.email,
                phone=c.phone,
                is_primary=c.is_primary,
            )
            db.add(contact)

        await record_audit_log(
            db=db,
            tenant_id=tenant_id,
            action=AuditEventCategory.PROCUREMENT_VENDOR_REGISTERED,
            entity_type="Vendor",
            entity_id=vendor.id,
            user_id=user_id,
            new_values_json={"code": vendor.code, "legal_name": vendor.legal_name},
        )

        outbox = OutboxEvent(
            id=uuid4(),
            tenant_id=tenant_id,
            aggregate_type="Vendor",
            aggregate_id=vendor.id,
            event_type="VENDOR_REGISTERED",
            correlation_id=str(uuid4()),
            payload={"code": vendor.code, "legal_name": vendor.legal_name, "category": vendor.category},
        )
        db.add(outbox)

        await db.commit()
        return await self.get_vendor(db, tenant_id, vendor.id)

    async def get_vendor(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        vendor_id: UUID,
    ) -> Vendor:
        stmt = (
            select(Vendor)
            .options(
                selectinload(Vendor.contacts),
                selectinload(Vendor.reviews),
            )
            .where(
                Vendor.tenant_id == tenant_id,
                Vendor.id == vendor_id,
            )
        )
        vendor = (await db.execute(stmt)).scalar_one_or_none()
        if not vendor:
            raise NotFoundException("Vendor", vendor_id)
        return vendor

    async def list_vendors(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        category: str | None = None,
        status: str | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Vendor], int]:
        stmt = select(Vendor).where(Vendor.tenant_id == tenant_id)
        if category:
            stmt = stmt.where(Vendor.category == category)
        if status:
            stmt = stmt.where(Vendor.status == status)
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Vendor.name.ilike(pattern),
                    Vendor.legal_name.ilike(pattern),
                    Vendor.code.ilike(pattern),
                    Vendor.tax_identifier.ilike(pattern),
                )
            )

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_count = (await db.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(Vendor.created_at.desc()).offset(skip).limit(limit)
        vendors = (await db.execute(stmt)).scalars().all()
        return list(vendors), total_count

    async def update_vendor(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        vendor_id: UUID,
        payload: VendorUpdate,
        user_id: UUID,
    ) -> Vendor:
        vendor = await self.get_vendor(db, tenant_id, vendor_id)
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(vendor, field, value)

        await record_audit_log(
            db=db,
            tenant_id=tenant_id,
            action=AuditEventCategory.PROCUREMENT_VENDOR_UPDATED,
            entity_type="Vendor",
            entity_id=vendor.id,
            user_id=user_id,
            new_values_json=update_data,
        )
        await db.commit()
        return vendor

    async def transition_vendor_status(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        vendor_id: UUID,
        payload: VendorStatusTransitionRequest,
        user_id: UUID,
    ) -> Vendor:
        vendor = await self.get_vendor(db, tenant_id, vendor_id)
        old_status = vendor.status
        vendor.status = payload.status

        if payload.status == VendorStatus.APPROVED:
            vendor.is_verified = True
            vendor.verified_at = datetime.now(UTC)
            vendor.verified_by = user_id
            audit_action = AuditEventCategory.PROCUREMENT_VENDOR_APPROVED
        elif payload.status == VendorStatus.SUSPENDED:
            audit_action = AuditEventCategory.PROCUREMENT_VENDOR_SUSPENDED
        else:
            audit_action = AuditEventCategory.PROCUREMENT_VENDOR_UPDATED

        await record_audit_log(
            db=db,
            tenant_id=tenant_id,
            action=audit_action,
            entity_type="Vendor",
            entity_id=vendor.id,
            user_id=user_id,
            old_values_json={"status": old_status},
            new_values_json={"status": payload.status, "reason": payload.reason},
        )
        await db.commit()
        return vendor

    async def check_vendor_duplicates(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        payload: VendorDuplicateCheckRequest,
    ) -> VendorDuplicateCheckResponse:
        matches: list[VendorDuplicateMatch] = []
        stmt = select(Vendor).where(Vendor.tenant_id == tenant_id)
        vendors = (await db.execute(stmt)).scalars().all()

        target_name = payload.legal_name.strip().lower()
        target_tax = payload.tax_identifier.strip().lower() if payload.tax_identifier else None
        target_email = payload.email.strip().lower() if payload.email else None

        for v in vendors:
            matched_fields = []
            score = 0.0

            if target_tax and v.tax_identifier and v.tax_identifier.strip().lower() == target_tax:
                matched_fields.append("tax_identifier")
                score += 0.9

            if target_email and v.email.strip().lower() == target_email:
                matched_fields.append("email")
                score += 0.7

            v_legal = v.legal_name.strip().lower()
            if target_name == v_legal:
                matched_fields.append("legal_name_exact")
                score += 0.8
            elif target_name in v_legal or v_legal in target_name:
                matched_fields.append("legal_name_partial")
                score += 0.4

            if matched_fields:
                normalized_score = min(score, 1.0)
                matches.append(
                    VendorDuplicateMatch(
                        vendor_id=v.id,
                        code=v.code,
                        name=v.name,
                        legal_name=v.legal_name,
                        tax_identifier=v.tax_identifier,
                        email=v.email,
                        similarity_score=round(normalized_score, 2),
                        matched_on=matched_fields,
                    )
                )

        matches.sort(key=lambda x: x.similarity_score, reverse=True)
        return VendorDuplicateCheckResponse(
            has_potential_duplicates=len(matches) > 0,
            matches=matches,
        )

    async def add_vendor_contact(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        vendor_id: UUID,
        payload: VendorContactCreate,
        user_id: UUID,
    ) -> VendorContact:
        await self.get_vendor(db, tenant_id, vendor_id)
        if payload.is_primary:
            stmt = select(VendorContact).where(
                VendorContact.tenant_id == tenant_id,
                VendorContact.vendor_id == vendor_id,
                VendorContact.is_primary.is_(True),
            )
            primaries = (await db.execute(stmt)).scalars().all()
            for p in primaries:
                p.is_primary = False

        contact = VendorContact(
            tenant_id=tenant_id,
            vendor_id=vendor_id,
            name=payload.name,
            designation=payload.designation,
            email=payload.email,
            phone=payload.phone,
            is_primary=payload.is_primary,
        )
        db.add(contact)
        await db.commit()
        await db.refresh(contact)
        return contact

    async def update_vendor_contact(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        vendor_id: UUID,
        contact_id: UUID,
        payload: VendorContactUpdate,
        user_id: UUID,
    ) -> VendorContact:
        stmt = select(VendorContact).where(
            VendorContact.tenant_id == tenant_id,
            VendorContact.vendor_id == vendor_id,
            VendorContact.id == contact_id,
        )
        contact = (await db.execute(stmt)).scalar_one_or_none()
        if not contact:
            raise NotFoundException("VendorContact", contact_id)

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(contact, field, value)

        await db.commit()
        await db.refresh(contact)
        return contact

    async def create_vendor_performance_review(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        vendor_id: UUID,
        payload: VendorPerformanceReviewCreate,
        user_id: UUID,
    ) -> VendorPerformanceReview:
        vendor = await self.get_vendor(db, tenant_id, vendor_id)

        avg_score = round(
            Decimal(payload.delivery_score + payload.quality_score + payload.pricing_score) / Decimal("3.0"),
            2,
        )
        review = VendorPerformanceReview(
            tenant_id=tenant_id,
            vendor_id=vendor_id,
            review_date=payload.review_date,
            reviewer_id=user_id,
            delivery_score=payload.delivery_score,
            quality_score=payload.quality_score,
            pricing_score=payload.pricing_score,
            overall_score=avg_score,
            comments=payload.comments,
            recommendation=payload.recommendation,
        )
        db.add(review)

        # Update vendor's overall rating score
        stmt = select(func.avg(VendorPerformanceReview.overall_score)).where(
            VendorPerformanceReview.tenant_id == tenant_id,
            VendorPerformanceReview.vendor_id == vendor_id,
        )
        current_avg = (await db.execute(stmt)).scalar() or avg_score
        vendor.rating_score = round(Decimal(str(current_avg)), 2)

        await record_audit_log(
            db=db,
            tenant_id=tenant_id,
            action=AuditEventCategory.PROCUREMENT_VENDOR_UPDATED,
            entity_type="VendorPerformanceReview",
            entity_id=vendor_id,
            user_id=user_id,
            new_values_json={"overall_score": float(avg_score), "recommendation": payload.recommendation},
        )
        await db.commit()
        await db.refresh(review)
        return review

    # =========================================================================
    # 2. PURCHASE REQUISITIONS
    # =========================================================================

    async def create_requisition(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        payload: PurchaseRequisitionCreate,
        user_id: UUID,
    ) -> PurchaseRequisition:
        # Check uniqueness of requisition_number
        stmt = select(PurchaseRequisition).where(
            PurchaseRequisition.tenant_id == tenant_id,
            PurchaseRequisition.requisition_number == payload.requisition_number,
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            raise ConflictException("PurchaseRequisition", "requisition_number", payload.requisition_number)

        total_estimated = Decimal("0.00")
        line_models = []
        for line in payload.lines:
            line_total = round(line.quantity_requested * line.estimated_unit_price, 2)
            total_estimated += line_total
            line_models.append(
                PurchaseRequisitionLine(
                    tenant_id=tenant_id,
                    item_id=line.item_id,
                    item_description=line.item_description,
                    unit_of_measure=line.unit_of_measure,
                    quantity_requested=line.quantity_requested,
                    estimated_unit_price=line.estimated_unit_price,
                    estimated_total_price=line_total,
                    quantity_ordered=Decimal("0.00"),
                    quantity_fulfilled=Decimal("0.00"),
                    specifications=line.specifications,
                )
            )

        requisition = PurchaseRequisition(
            tenant_id=tenant_id,
            requisition_number=payload.requisition_number,
            department_id=payload.department_id,
            campus_id=payload.campus_id,
            requestor_id=user_id,
            title=payload.title,
            justification=payload.justification,
            category=payload.category,
            priority=payload.priority,
            status=RequisitionStatus.SUBMITTED,
            required_date=payload.required_date,
            delivery_location=payload.delivery_location,
            estimated_total_amount=total_estimated,
            currency=payload.currency,
            budget_code=payload.budget_code,
            notes=payload.notes,
            lines=line_models,
        )
        db.add(requisition)
        await db.flush()

        await record_audit_log(
            db=db,
            tenant_id=tenant_id,
            action=AuditEventCategory.PROCUREMENT_REQUISITION_CREATED,
            entity_type="PurchaseRequisition",
            entity_id=requisition.id,
            user_id=user_id,
            new_values_json={
                "requisition_number": requisition.requisition_number,
                "estimated_total_amount": float(total_estimated),
            },
        )

        outbox = OutboxEvent(
            id=uuid4(),
            tenant_id=tenant_id,
            aggregate_type="PurchaseRequisition",
            aggregate_id=requisition.id,
            event_type="REQUISITION_SUBMITTED",
            correlation_id=str(uuid4()),
            payload={
                "requisition_number": requisition.requisition_number,
                "department_id": str(requisition.department_id),
                "estimated_total_amount": float(total_estimated),
            },
        )
        db.add(outbox)
        await db.commit()
        return await self.get_requisition(db, tenant_id, requisition.id)

    async def get_requisition(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        requisition_id: UUID,
    ) -> PurchaseRequisition:
        stmt = (
            select(PurchaseRequisition)
            .options(selectinload(PurchaseRequisition.lines))
            .where(
                PurchaseRequisition.tenant_id == tenant_id,
                PurchaseRequisition.id == requisition_id,
            )
        )
        req = (await db.execute(stmt)).scalar_one_or_none()
        if not req:
            raise NotFoundException("PurchaseRequisition", requisition_id)
        return req

    async def list_requisitions(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        department_id: UUID | None = None,
        campus_id: UUID | None = None,
        status: str | None = None,
        priority: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[PurchaseRequisition], int]:
        stmt = select(PurchaseRequisition).where(PurchaseRequisition.tenant_id == tenant_id)
        if department_id:
            stmt = stmt.where(PurchaseRequisition.department_id == department_id)
        if campus_id:
            stmt = stmt.where(PurchaseRequisition.campus_id == campus_id)
        if status:
            stmt = stmt.where(PurchaseRequisition.status == status)
        if priority:
            stmt = stmt.where(PurchaseRequisition.priority == priority)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_count = (await db.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(PurchaseRequisition.created_at.desc()).offset(skip).limit(limit)
        requisitions = (await db.execute(stmt)).scalars().all()
        return list(requisitions), total_count

    async def update_requisition(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        requisition_id: UUID,
        payload: PurchaseRequisitionUpdate,
        user_id: UUID,
    ) -> PurchaseRequisition:
        req = await self.get_requisition(db, tenant_id, requisition_id)
        if req.status not in (RequisitionStatus.DRAFT, RequisitionStatus.RETURNED_FOR_CORRECTION):
            raise BadRequestException("Only DRAFT or RETURNED_FOR_CORRECTION requisitions can be edited.")

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(req, field, value)

        await db.commit()
        return req

    async def review_requisition(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        requisition_id: UUID,
        payload: PurchaseRequisitionApprovalRequest,
        user_id: UUID,
    ) -> PurchaseRequisition:
        req = await self.get_requisition(db, tenant_id, requisition_id)
        if req.status not in (RequisitionStatus.SUBMITTED, RequisitionStatus.UNDER_REVIEW):
            raise BadRequestException(f"Cannot review requisition currently in status '{req.status}'.")

        if payload.action == "APPROVE":
            req.status = RequisitionStatus.APPROVED
            req.approved_by_id = user_id
            req.approved_at = datetime.now(UTC)
            req.rejection_reason = None
            audit_action = AuditEventCategory.PROCUREMENT_REQUISITION_APPROVED
            outbox_event = "REQUISITION_APPROVED"
        elif payload.action == "REJECT":
            req.status = RequisitionStatus.REJECTED
            req.rejection_reason = payload.comments
            audit_action = AuditEventCategory.PROCUREMENT_REQUISITION_REJECTED
            outbox_event = "REQUISITION_REJECTED"
        else:  # RETURN_FOR_CORRECTION
            req.status = RequisitionStatus.RETURNED_FOR_CORRECTION
            req.rejection_reason = payload.comments
            audit_action = AuditEventCategory.PROCUREMENT_REQUISITION_UPDATED
            outbox_event = "REQUISITION_RETURNED"

        await record_audit_log(
            db=db,
            tenant_id=tenant_id,
            action=audit_action,
            entity_type="PurchaseRequisition",
            entity_id=req.id,
            user_id=user_id,
            new_values_json={"action": payload.action, "comments": payload.comments},
        )

        outbox = OutboxEvent(
            id=uuid4(),
            tenant_id=tenant_id,
            aggregate_type="PurchaseRequisition",
            aggregate_id=req.id,
            event_type=outbox_event,
            correlation_id=str(uuid4()),
            payload={"requisition_number": req.requisition_number, "action": payload.action},
        )
        db.add(outbox)

        await db.commit()
        return req

    # =========================================================================
    # 3. REQUEST FOR QUOTATION (RFQ) & QUOTATIONS
    # =========================================================================

    async def create_rfq(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        payload: QuotationRequestCreate,
        user_id: UUID,
    ) -> QuotationRequest:
        stmt = select(QuotationRequest).where(
            QuotationRequest.tenant_id == tenant_id,
            QuotationRequest.rfq_number == payload.rfq_number,
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            raise ConflictException("QuotationRequest", "rfq_number", payload.rfq_number)

        # Requisition must exist
        await self.get_requisition(db, tenant_id, payload.requisition_id)

        rfq = QuotationRequest(
            tenant_id=tenant_id,
            rfq_number=payload.rfq_number,
            requisition_id=payload.requisition_id,
            title=payload.title,
            deadline_date=payload.deadline_date,
            status=RfqStatus.PUBLISHED,
            evaluation_criteria_json=payload.evaluation_criteria_json,
            notes=payload.notes,
        )
        db.add(rfq)
        await db.flush()

        await record_audit_log(
            db=db,
            tenant_id=tenant_id,
            action=AuditEventCategory.PROCUREMENT_RFQ_CREATED,
            entity_type="QuotationRequest",
            entity_id=rfq.id,
            user_id=user_id,
            new_values_json={"rfq_number": rfq.rfq_number, "title": rfq.title},
        )
        await db.commit()
        return await self.get_rfq(db, tenant_id, rfq.id)

    async def get_rfq(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        rfq_id: UUID,
    ) -> QuotationRequest:
        stmt = (
            select(QuotationRequest)
            .options(
                selectinload(QuotationRequest.quotations),
                selectinload(QuotationRequest.evaluations),
            )
            .where(
                QuotationRequest.tenant_id == tenant_id,
                QuotationRequest.id == rfq_id,
            )
        )
        rfq = (await db.execute(stmt)).scalar_one_or_none()
        if not rfq:
            raise NotFoundException("QuotationRequest", rfq_id)
        return rfq

    async def list_rfqs(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[QuotationRequest], int]:
        stmt = select(QuotationRequest).where(QuotationRequest.tenant_id == tenant_id)
        if status:
            stmt = stmt.where(QuotationRequest.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_count = (await db.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(QuotationRequest.created_at.desc()).offset(skip).limit(limit)
        rfqs = (await db.execute(stmt)).scalars().all()
        return list(rfqs), total_count

    async def update_rfq(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        rfq_id: UUID,
        payload: QuotationRequestUpdate,
        user_id: UUID,
    ) -> QuotationRequest:
        rfq = await self.get_rfq(db, tenant_id, rfq_id)
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(rfq, field, value)

        await db.commit()
        return rfq

    async def submit_vendor_quotation(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        payload: VendorQuotationCreate,
        user_id: UUID,
    ) -> VendorQuotation:
        rfq = await self.get_rfq(db, tenant_id, payload.rfq_id)
        if rfq.status not in (RfqStatus.PUBLISHED, RfqStatus.DRAFT):
            raise BadRequestException("Cannot submit quotation to an RFQ that is closed or evaluated.")

        vendor = await self.get_vendor(db, tenant_id, payload.vendor_id)
        if vendor.status == VendorStatus.SUSPENDED:
            raise BadRequestException("Suspended vendors cannot submit quotations.")

        quotation = VendorQuotation(
            tenant_id=tenant_id,
            rfq_id=payload.rfq_id,
            vendor_id=payload.vendor_id,
            quotation_reference=payload.quotation_reference,
            submission_date=payload.submission_date,
            validity_until=payload.validity_until,
            total_quoted_amount=payload.total_quoted_amount,
            delivery_lead_days=payload.delivery_lead_days,
            warranty_months=payload.warranty_months,
            payment_terms=payload.payment_terms,
            document_storage_key=payload.document_storage_key,
            status=QuotationStatus.SUBMITTED,
            evaluation_score=Decimal("0.00"),
        )
        db.add(quotation)
        await db.flush()

        await record_audit_log(
            db=db,
            tenant_id=tenant_id,
            action=AuditEventCategory.PROCUREMENT_QUOTATION_SUBMITTED,
            entity_type="VendorQuotation",
            entity_id=quotation.id,
            user_id=user_id,
            new_values_json={
                "rfq_id": str(payload.rfq_id),
                "vendor_id": str(payload.vendor_id),
                "total_quoted_amount": float(payload.total_quoted_amount),
            },
        )
        await db.commit()
        await db.refresh(quotation)
        return quotation

    async def evaluate_quotation(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        payload: QuotationEvaluationCreate,
        user_id: UUID,
    ) -> QuotationEvaluation:
        rfq = await self.get_rfq(db, tenant_id, payload.rfq_id)

        # Compute composite evaluation score based on weights
        weights = rfq.evaluation_criteria_json or {"price_weight": 0.5, "quality_weight": 0.3, "delivery_weight": 0.2}
        pw = Decimal(str(weights.get("price_weight", 0.5)))
        qw = Decimal(str(weights.get("quality_weight", 0.3)))
        dw = Decimal(str(weights.get("delivery_weight", 0.2)))

        price_score = Decimal(str(payload.scoring_details_json.get("price_score", 80)))
        quality_score = Decimal(str(payload.scoring_details_json.get("quality_score", 80)))
        delivery_score = Decimal(str(payload.scoring_details_json.get("delivery_score", 80)))

        composite_score = round(
            (price_score * pw) + (quality_score * qw) + (delivery_score * dw),
            2,
        )

        evaluation = QuotationEvaluation(
            tenant_id=tenant_id,
            rfq_id=payload.rfq_id,
            evaluator_id=user_id,
            evaluation_date=payload.evaluation_date,
            scoring_details_json=payload.scoring_details_json,
            recommended_vendor_id=payload.recommended_vendor_id,
            award_decision=payload.award_decision,
            single_source_justification=payload.single_source_justification,
        )
        db.add(evaluation)
        await db.flush()

        # Update matching vendor quotations
        if payload.recommended_vendor_id:
            stmt = select(VendorQuotation).where(
                VendorQuotation.tenant_id == tenant_id,
                VendorQuotation.rfq_id == payload.rfq_id,
                VendorQuotation.vendor_id == payload.recommended_vendor_id,
            )
            v_quotation = (await db.execute(stmt)).scalar_one_or_none()
            if v_quotation:
                v_quotation.evaluation_score = composite_score
                if payload.award_decision == AwardDecision.AWARDED:
                    v_quotation.status = QuotationStatus.ACCEPTED

        rfq.status = RfqStatus.EVALUATED

        await record_audit_log(
            db=db,
            tenant_id=tenant_id,
            action=AuditEventCategory.PROCUREMENT_QUOTATION_EVALUATED,
            entity_type="QuotationEvaluation",
            entity_id=evaluation.id,
            user_id=user_id,
            new_values_json={
                "award_decision": payload.award_decision,
                "composite_score": float(composite_score),
            },
        )
        await db.commit()
        await db.refresh(evaluation)
        return evaluation

    # =========================================================================
    # 4. PURCHASE ORDERS & AMENDMENTS
    # =========================================================================

    async def create_purchase_order(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        payload: PurchaseOrderCreate,
        user_id: UUID,
    ) -> PurchaseOrder:
        stmt = select(PurchaseOrder).where(
            PurchaseOrder.tenant_id == tenant_id,
            PurchaseOrder.po_number == payload.po_number,
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            raise ConflictException("PurchaseOrder", "po_number", payload.po_number)

        vendor = await self.get_vendor(db, tenant_id, payload.vendor_id)
        if vendor.status != VendorStatus.APPROVED:
            raise BadRequestException("Purchase order can only be issued to an APPROVED vendor.")

        subtotal = Decimal("0.00")
        total_tax = Decimal("0.00")
        line_models = []

        for line in payload.lines:
            line_subtotal = round(line.quantity_ordered * line.unit_price, 2)
            line_tax = (
                line.tax_amount
                if line.tax_amount > 0
                else round(line_subtotal * (line.tax_rate / Decimal("100.0")), 2)
            )
            line_total = round(line_subtotal + line_tax, 2)
            subtotal += line_subtotal
            total_tax += line_tax

            line_models.append(
                PurchaseOrderLine(
                    tenant_id=tenant_id,
                    requisition_line_id=line.requisition_line_id,
                    item_id=line.item_id,
                    item_description=line.item_description,
                    unit_of_measure=line.unit_of_measure,
                    quantity_ordered=line.quantity_ordered,
                    quantity_received=Decimal("0.00"),
                    quantity_accepted=Decimal("0.00"),
                    quantity_rejected=Decimal("0.00"),
                    quantity_invoiced=Decimal("0.00"),
                    unit_price=line.unit_price,
                    tax_rate=line.tax_rate,
                    tax_amount=line_tax,
                    total_price=line_total,
                )
            )

        total_amount = round(subtotal + total_tax - payload.discount_amount, 2)

        po = PurchaseOrder(
            tenant_id=tenant_id,
            po_number=payload.po_number,
            requisition_id=payload.requisition_id,
            rfq_id=payload.rfq_id,
            vendor_id=payload.vendor_id,
            vendor_quotation_id=payload.vendor_quotation_id,
            campus_id=payload.campus_id,
            status=PurchaseOrderStatus.DRAFT,
            order_date=payload.order_date,
            expected_delivery_date=payload.expected_delivery_date,
            delivery_address=payload.delivery_address,
            billing_address=payload.billing_address,
            payment_terms=payload.payment_terms,
            currency=payload.currency,
            subtotal=subtotal,
            tax_amount=total_tax,
            discount_amount=payload.discount_amount,
            total_amount=total_amount,
            version_number=1,
            metadata_json=payload.metadata_json,
            lines=line_models,
        )
        db.add(po)
        await db.flush()

        # Update requisition lines ordered quantities if linked
        if payload.requisition_id:
            req = await self.get_requisition(db, tenant_id, payload.requisition_id)
            for po_line in line_models:
                if po_line.requisition_line_id:
                    for req_line in req.lines:
                        if req_line.id == po_line.requisition_line_id:
                            req_line.quantity_ordered += po_line.quantity_ordered
            req.status = RequisitionStatus.PARTIALLY_FULFILLED

        await record_audit_log(
            db=db,
            tenant_id=tenant_id,
            action=AuditEventCategory.PROCUREMENT_ORDER_CREATED,
            entity_type="PurchaseOrder",
            entity_id=po.id,
            user_id=user_id,
            new_values_json={"po_number": po.po_number, "total_amount": float(total_amount)},
        )

        outbox = OutboxEvent(
            id=uuid4(),
            tenant_id=tenant_id,
            aggregate_type="PurchaseOrder",
            aggregate_id=po.id,
            event_type="PURCHASE_ORDER_CREATED",
            correlation_id=str(uuid4()),
            payload={"po_number": po.po_number, "total_amount": float(total_amount), "vendor_id": str(po.vendor_id)},
        )
        db.add(outbox)
        await db.commit()
        return await self.get_purchase_order(db, tenant_id, po.id)

    async def get_purchase_order(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        po_id: UUID,
    ) -> PurchaseOrder:
        stmt = (
            select(PurchaseOrder)
            .options(
                selectinload(PurchaseOrder.lines),
                selectinload(PurchaseOrder.amendments),
            )
            .where(
                PurchaseOrder.tenant_id == tenant_id,
                PurchaseOrder.id == po_id,
            )
        )
        po = (await db.execute(stmt)).scalar_one_or_none()
        if not po:
            raise NotFoundException("PurchaseOrder", po_id)
        return po

    async def list_purchase_orders(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        vendor_id: UUID | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[PurchaseOrder], int]:
        stmt = select(PurchaseOrder).where(PurchaseOrder.tenant_id == tenant_id)
        if vendor_id:
            stmt = stmt.where(PurchaseOrder.vendor_id == vendor_id)
        if status:
            stmt = stmt.where(PurchaseOrder.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_count = (await db.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(PurchaseOrder.created_at.desc()).offset(skip).limit(limit)
        orders = (await db.execute(stmt)).scalars().all()
        return list(orders), total_count

    async def update_purchase_order(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        po_id: UUID,
        payload: PurchaseOrderUpdate,
        user_id: UUID,
    ) -> PurchaseOrder:
        po = await self.get_purchase_order(db, tenant_id, po_id)
        if po.status != PurchaseOrderStatus.DRAFT:
            raise BadRequestException("Cannot directly edit issued purchase order; create an authorized amendment.")

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(po, field, value)

        await db.commit()
        return po

    async def issue_purchase_order(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        po_id: UUID,
        user_id: UUID,
    ) -> PurchaseOrder:
        po = await self.get_purchase_order(db, tenant_id, po_id)
        if po.status != PurchaseOrderStatus.DRAFT:
            raise BadRequestException(f"Only DRAFT purchase orders can be issued. Current status: {po.status}")

        po.status = PurchaseOrderStatus.ISSUED
        po.issued_by_id = user_id
        po.issued_at = datetime.now(UTC)
        po.approved_by_id = user_id
        po.approved_at = datetime.now(UTC)

        await record_audit_log(
            db=db,
            tenant_id=tenant_id,
            action=AuditEventCategory.PROCUREMENT_ORDER_ISSUED,
            entity_type="PurchaseOrder",
            entity_id=po.id,
            user_id=user_id,
            new_values_json={"status": PurchaseOrderStatus.ISSUED},
        )

        outbox = OutboxEvent(
            id=uuid4(),
            tenant_id=tenant_id,
            aggregate_type="PurchaseOrder",
            aggregate_id=po.id,
            event_type="PURCHASE_ORDER_ISSUED",
            correlation_id=str(uuid4()),
            payload={"po_number": po.po_number, "issued_at": po.issued_at.isoformat()},
        )
        db.add(outbox)
        await db.commit()
        return po

    async def create_po_amendment(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        po_id: UUID,
        payload: PurchaseOrderAmendmentCreate,
        user_id: UUID,
    ) -> PurchaseOrderAmendment:
        po = await self.get_purchase_order(db, tenant_id, po_id)
        if po.status in (PurchaseOrderStatus.CANCELLED, PurchaseOrderStatus.CLOSED):
            raise BadRequestException(f"Cannot amend purchase order in status '{po.status}'.")

        next_amendment_num = len(po.amendments) + 1
        amendment = PurchaseOrderAmendment(
            tenant_id=tenant_id,
            po_id=po_id,
            amendment_number=next_amendment_num,
            reason=payload.reason,
            changes_json=payload.changes_json,
            requested_by_id=user_id,
            approved_by_id=user_id,
            approved_at=datetime.now(UTC),
            status=AmendmentStatus.APPROVED,
        )
        db.add(amendment)

        po.version_number += 1
        po.revision_notes = payload.reason

        await record_audit_log(
            db=db,
            tenant_id=tenant_id,
            action=AuditEventCategory.PROCUREMENT_ORDER_AMENDED,
            entity_type="PurchaseOrderAmendment",
            entity_id=po.id,
            user_id=user_id,
            new_values_json={"amendment_number": next_amendment_num, "reason": payload.reason},
        )
        await db.commit()
        await db.refresh(amendment)
        return amendment

    async def close_purchase_order(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        po_id: UUID,
        user_id: UUID,
    ) -> PurchaseOrder:
        po = await self.get_purchase_order(db, tenant_id, po_id)
        po.status = PurchaseOrderStatus.CLOSED

        await record_audit_log(
            db=db,
            tenant_id=tenant_id,
            action=AuditEventCategory.PROCUREMENT_ORDER_UPDATED,
            entity_type="PurchaseOrder",
            entity_id=po.id,
            user_id=user_id,
            new_values_json={"status": PurchaseOrderStatus.CLOSED},
        )
        await db.commit()
        return po

    async def cancel_purchase_order(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        po_id: UUID,
        user_id: UUID,
    ) -> PurchaseOrder:
        po = await self.get_purchase_order(db, tenant_id, po_id)
        po.status = PurchaseOrderStatus.CANCELLED

        await record_audit_log(
            db=db,
            tenant_id=tenant_id,
            action=AuditEventCategory.PROCUREMENT_ORDER_CANCELLED,
            entity_type="PurchaseOrder",
            entity_id=po.id,
            user_id=user_id,
            new_values_json={"status": PurchaseOrderStatus.CANCELLED},
        )
        await db.commit()
        return po

    # =========================================================================
    # 5. GOODS RECEIPT & QUALITY INSPECTION
    # =========================================================================

    async def create_goods_receipt(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        payload: GoodsReceiptCreate,
        user_id: UUID,
    ) -> GoodsReceipt:
        stmt = select(GoodsReceipt).where(
            GoodsReceipt.tenant_id == tenant_id,
            GoodsReceipt.grn_number == payload.grn_number,
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            raise ConflictException("GoodsReceipt", "grn_number", payload.grn_number)

        po = await self.get_purchase_order(db, tenant_id, payload.po_id)
        if po.status not in (
            PurchaseOrderStatus.ISSUED,
            PurchaseOrderStatus.ACKNOWLEDGED,
            PurchaseOrderStatus.PARTIALLY_DELIVERED,
        ):
            raise BadRequestException(f"Cannot receive goods for purchase order in status '{po.status}'.")

        po_lines_map = {line.id: line for line in po.lines}
        grn_lines = []

        for line_in in payload.lines:
            po_line = po_lines_map.get(line_in.po_line_id)
            if not po_line:
                raise NotFoundException("PurchaseOrderLine", line_in.po_line_id)

            # Prevent over-receipt
            if (po_line.quantity_received + line_in.quantity_received) > po_line.quantity_ordered:
                raise BadRequestException(
                    f"Receipt quantity {line_in.quantity_received} exceeds remaining order balance. "
                    f"Ordered: {po_line.quantity_ordered}, Already Received: {po_line.quantity_received}"
                )

            po_line.quantity_received += line_in.quantity_received
            po_line.quantity_accepted += line_in.quantity_accepted
            po_line.quantity_rejected += line_in.quantity_rejected

            grn_lines.append(
                GoodsReceiptLine(
                    tenant_id=tenant_id,
                    po_line_id=line_in.po_line_id,
                    item_id=line_in.item_id or po_line.item_id,
                    item_description=line_in.item_description,
                    unit_of_measure=line_in.unit_of_measure,
                    quantity_received=line_in.quantity_received,
                    quantity_accepted=line_in.quantity_accepted,
                    quantity_rejected=line_in.quantity_rejected,
                    rejection_reason=line_in.rejection_reason,
                    batch_lot_number=line_in.batch_lot_number,
                    expiry_date=line_in.expiry_date,
                )
            )

        # Evaluate PO status
        all_delivered = all(line.quantity_received >= line.quantity_ordered for line in po.lines)
        po.status = PurchaseOrderStatus.DELIVERED if all_delivered else PurchaseOrderStatus.PARTIALLY_DELIVERED

        grn = GoodsReceipt(
            tenant_id=tenant_id,
            grn_number=payload.grn_number,
            po_id=payload.po_id,
            vendor_id=payload.vendor_id,
            receipt_date=payload.receipt_date,
            received_by_id=user_id,
            carrier_name=payload.carrier_name,
            tracking_number=payload.tracking_number,
            delivery_note_reference=payload.delivery_note_reference,
            status=GoodsReceiptStatus.RECEIVED,
            storage_location_id=payload.storage_location_id,
            inspection_notes=payload.inspection_notes,
            quality_status=QualityInspectionStatus.PENDING,
            lines=grn_lines,
        )
        db.add(grn)
        await db.flush()

        await record_audit_log(
            db=db,
            tenant_id=tenant_id,
            action=AuditEventCategory.PROCUREMENT_GOODS_RECEIVED,
            entity_type="GoodsReceipt",
            entity_id=grn.id,
            user_id=user_id,
            new_values_json={"grn_number": grn.grn_number, "po_id": str(po.id)},
        )

        outbox = OutboxEvent(
            id=uuid4(),
            tenant_id=tenant_id,
            aggregate_type="GoodsReceipt",
            aggregate_id=grn.id,
            event_type="GOODS_RECEIVED",
            correlation_id=str(uuid4()),
            payload={"grn_number": grn.grn_number, "po_number": po.po_number},
        )
        db.add(outbox)
        await db.commit()
        return await self.get_goods_receipt(db, tenant_id, grn.id)

    async def get_goods_receipt(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        grn_id: UUID,
    ) -> GoodsReceipt:
        stmt = (
            select(GoodsReceipt)
            .options(selectinload(GoodsReceipt.lines))
            .where(
                GoodsReceipt.tenant_id == tenant_id,
                GoodsReceipt.id == grn_id,
            )
        )
        grn = (await db.execute(stmt)).scalar_one_or_none()
        if not grn:
            raise NotFoundException("GoodsReceipt", grn_id)
        return grn

    async def list_goods_receipts(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        po_id: UUID | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[GoodsReceipt], int]:
        stmt = select(GoodsReceipt).where(GoodsReceipt.tenant_id == tenant_id)
        if po_id:
            stmt = stmt.where(GoodsReceipt.po_id == po_id)
        if status:
            stmt = stmt.where(GoodsReceipt.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_count = (await db.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(GoodsReceipt.created_at.desc()).offset(skip).limit(limit)
        receipts = (await db.execute(stmt)).scalars().all()
        return list(receipts), total_count

    async def record_quality_inspection(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        grn_id: UUID,
        payload: QualityInspectionRecordRequest,
        user_id: UUID,
    ) -> GoodsReceipt:
        grn = await self.get_goods_receipt(db, tenant_id, grn_id)
        grn.quality_status = payload.quality_status
        grn.inspection_notes = payload.inspection_notes
        grn.inspected_by_id = user_id
        grn.inspected_at = datetime.now(UTC)

        if payload.quality_status == QualityInspectionStatus.PASSED:
            grn.status = GoodsReceiptStatus.ACCEPTED
        elif payload.quality_status == QualityInspectionStatus.FAILED:
            grn.status = GoodsReceiptStatus.REJECTED
        else:
            grn.status = GoodsReceiptStatus.PARTIALLY_ACCEPTED

        await record_audit_log(
            db=db,
            tenant_id=tenant_id,
            action=AuditEventCategory.PROCUREMENT_GOODS_INSPECTED,
            entity_type="GoodsReceipt",
            entity_id=grn.id,
            user_id=user_id,
            new_values_json={"quality_status": grn.quality_status, "status": grn.status},
        )
        await db.commit()
        return grn

    # =========================================================================
    # 6. INVENTORY LOCATIONS, ITEMS, BALANCES & MOVEMENTS
    # =========================================================================

    async def create_location(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        payload: InventoryLocationCreate,
        user_id: UUID,
    ) -> InventoryLocation:
        stmt = select(InventoryLocation).where(
            InventoryLocation.tenant_id == tenant_id,
            InventoryLocation.code == payload.code,
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            raise ConflictException("InventoryLocation", "code", payload.code)

        location = InventoryLocation(
            tenant_id=tenant_id,
            campus_id=payload.campus_id,
            code=payload.code,
            name=payload.name,
            type=payload.type,
            is_active=True,
        )
        db.add(location)
        await db.commit()
        await db.refresh(location)
        return location

    async def get_location(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        loc_id: UUID,
    ) -> InventoryLocation:
        stmt = select(InventoryLocation).where(
            InventoryLocation.tenant_id == tenant_id,
            InventoryLocation.id == loc_id,
        )
        loc = (await db.execute(stmt)).scalar_one_or_none()
        if not loc:
            raise NotFoundException("InventoryLocation", loc_id)
        return loc

    async def list_locations(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        campus_id: UUID | None = None,
        loc_type: str | None = None,
    ) -> list[InventoryLocation]:
        stmt = select(InventoryLocation).where(InventoryLocation.tenant_id == tenant_id)
        if campus_id:
            stmt = stmt.where(InventoryLocation.campus_id == campus_id)
        if loc_type:
            stmt = stmt.where(InventoryLocation.type == loc_type)

        return list((await db.execute(stmt)).scalars().all())

    async def update_location(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        loc_id: UUID,
        payload: InventoryLocationUpdate,
        user_id: UUID,
    ) -> InventoryLocation:
        loc = await self.get_location(db, tenant_id, loc_id)
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(loc, field, value)
        await db.commit()
        return loc

    async def create_item(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        payload: InventoryItemCreate,
        user_id: UUID,
    ) -> InventoryItem:
        stmt = select(InventoryItem).where(
            InventoryItem.tenant_id == tenant_id,
            InventoryItem.sku == payload.sku,
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            raise ConflictException("InventoryItem", "sku", payload.sku)

        item = InventoryItem(
            tenant_id=tenant_id,
            sku=payload.sku,
            name=payload.name,
            category=payload.category,
            unit_of_measure=payload.unit_of_measure,
            unit_price_average=payload.unit_price_average,
            reorder_threshold=payload.reorder_threshold,
            reorder_quantity=payload.reorder_quantity,
            is_active=True,
        )
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item

    async def get_item(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        item_id: UUID,
    ) -> InventoryItem:
        stmt = select(InventoryItem).where(
            InventoryItem.tenant_id == tenant_id,
            InventoryItem.id == item_id,
        )
        item = (await db.execute(stmt)).scalar_one_or_none()
        if not item:
            raise NotFoundException("InventoryItem", item_id)
        return item

    async def list_items(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        category: str | None = None,
        is_active: bool | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[InventoryItem], int]:
        stmt = select(InventoryItem).where(InventoryItem.tenant_id == tenant_id)
        if category:
            stmt = stmt.where(InventoryItem.category == category)
        if is_active is not None:
            stmt = stmt.where(InventoryItem.is_active == is_active)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_count = (await db.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(InventoryItem.sku.asc()).offset(skip).limit(limit)
        items = (await db.execute(stmt)).scalars().all()
        return list(items), total_count

    async def update_item(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        item_id: UUID,
        payload: InventoryItemUpdate,
        user_id: UUID,
    ) -> InventoryItem:
        item = await self.get_item(db, tenant_id, item_id)
        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(item, field, value)
        await db.commit()
        return item

    async def get_or_create_stock_balance(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        item_id: UUID,
        location_id: UUID,
    ) -> StockBalance:
        stmt = select(StockBalance).where(
            StockBalance.tenant_id == tenant_id,
            StockBalance.item_id == item_id,
            StockBalance.location_id == location_id,
        )
        balance = (await db.execute(stmt)).scalar_one_or_none()
        if not balance:
            balance = StockBalance(
                tenant_id=tenant_id,
                item_id=item_id,
                location_id=location_id,
                quantity_on_hand=Decimal("0.00"),
                quantity_reserved=Decimal("0.00"),
                quantity_available=Decimal("0.00"),
                quantity_in_transit=Decimal("0.00"),
            )
            db.add(balance)
            await db.flush()
        return balance

    async def list_stock_balances(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        item_id: UUID | None = None,
        location_id: UUID | None = None,
    ) -> list[StockBalance]:
        stmt = select(StockBalance).where(StockBalance.tenant_id == tenant_id)
        if item_id:
            stmt = stmt.where(StockBalance.item_id == item_id)
        if location_id:
            stmt = stmt.where(StockBalance.location_id == location_id)
        return list((await db.execute(stmt)).scalars().all())

    async def record_stock_movement(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        payload: StockMovementCreate,
        user_id: UUID,
    ) -> StockMovement:
        stmt = select(StockMovement).where(
            StockMovement.tenant_id == tenant_id,
            StockMovement.movement_number == payload.movement_number,
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            raise ConflictException("StockMovement", "movement_number", payload.movement_number)

        # Process movement on balances
        if payload.movement_type == MovementType.RECEIPT:
            if not payload.destination_location_id:
                raise BadRequestException("RECEIPT movement requires destination_location_id.")
            dst_bal = await self.get_or_create_stock_balance(
                db, tenant_id, payload.item_id, payload.destination_location_id
            )
            dst_bal.quantity_on_hand += payload.quantity
            dst_bal.quantity_available += payload.quantity
            dst_bal.last_reconciled_at = datetime.now(UTC)
            audit_action = AuditEventCategory.PROCUREMENT_STOCK_ADJUSTED

        elif payload.movement_type in (MovementType.ISSUE, MovementType.RETURN_TO_VENDOR):
            if not payload.source_location_id:
                raise BadRequestException("ISSUE movement requires source_location_id.")
            src_bal = await self.get_or_create_stock_balance(
                db, tenant_id, payload.item_id, payload.source_location_id
            )
            if src_bal.quantity_available < payload.quantity:
                raise BadRequestException(
                    f"Insufficient stock to issue. Available: {src_bal.quantity_available}, requested: {payload.quantity}"
                )
            src_bal.quantity_on_hand -= payload.quantity
            src_bal.quantity_available -= payload.quantity
            src_bal.last_reconciled_at = datetime.now(UTC)
            audit_action = AuditEventCategory.PROCUREMENT_STOCK_ISSUED

        elif payload.movement_type == MovementType.ADJUSTMENT:
            target_loc = payload.destination_location_id or payload.source_location_id
            if not target_loc:
                raise BadRequestException("ADJUSTMENT movement requires a location.")
            bal = await self.get_or_create_stock_balance(db, tenant_id, payload.item_id, target_loc)
            bal.quantity_on_hand += payload.quantity
            bal.quantity_available += payload.quantity
            bal.last_reconciled_at = datetime.now(UTC)
            audit_action = AuditEventCategory.PROCUREMENT_STOCK_ADJUSTED

        else:
            audit_action = AuditEventCategory.PROCUREMENT_STOCK_ADJUSTED

        total_value = round(payload.quantity * payload.unit_cost, 2)
        movement = StockMovement(
            tenant_id=tenant_id,
            movement_number=payload.movement_number,
            item_id=payload.item_id,
            movement_type=payload.movement_type,
            source_location_id=payload.source_location_id,
            destination_location_id=payload.destination_location_id,
            quantity=payload.quantity,
            unit_cost=payload.unit_cost,
            total_value=total_value,
            reference_type=payload.reference_type,
            reference_id=payload.reference_id,
            performed_by_id=user_id,
            timestamp=datetime.now(UTC),
            notes=payload.notes,
        )
        db.add(movement)
        await db.flush()

        await record_audit_log(
            db=db,
            tenant_id=tenant_id,
            action=audit_action,
            entity_type="StockMovement",
            entity_id=movement.id,
            user_id=user_id,
            new_values_json={
                "movement_number": movement.movement_number,
                "movement_type": movement.movement_type,
                "quantity": float(movement.quantity),
            },
        )
        await db.commit()
        await db.refresh(movement)
        return movement

    async def transfer_stock(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        payload: StockTransferRequest,
        user_id: UUID,
    ) -> StockMovement:
        if payload.source_location_id == payload.destination_location_id:
            raise BadRequestException("Source and destination locations cannot be the same.")

        src_bal = await self.get_or_create_stock_balance(
            db, tenant_id, payload.item_id, payload.source_location_id
        )
        if src_bal.quantity_available < payload.quantity:
            raise BadRequestException(
                f"Insufficient stock for transfer. Available: {src_bal.quantity_available}, requested: {payload.quantity}"
            )

        dst_bal = await self.get_or_create_stock_balance(
            db, tenant_id, payload.item_id, payload.destination_location_id
        )

        src_bal.quantity_on_hand -= payload.quantity
        src_bal.quantity_available -= payload.quantity

        dst_bal.quantity_on_hand += payload.quantity
        dst_bal.quantity_available += payload.quantity

        movement = StockMovement(
            tenant_id=tenant_id,
            movement_number=payload.movement_number,
            item_id=payload.item_id,
            movement_type=MovementType.TRANSFER_OUT,
            source_location_id=payload.source_location_id,
            destination_location_id=payload.destination_location_id,
            quantity=payload.quantity,
            unit_cost=Decimal("0.00"),
            total_value=Decimal("0.00"),
            reference_type="INTER_STORE_TRANSFER",
            reference_id=None,
            performed_by_id=user_id,
            timestamp=datetime.now(UTC),
            notes=payload.notes,
        )
        db.add(movement)
        await db.flush()

        await record_audit_log(
            db=db,
            tenant_id=tenant_id,
            action=AuditEventCategory.PROCUREMENT_STOCK_TRANSFERRED,
            entity_type="StockMovement",
            entity_id=movement.id,
            user_id=user_id,
            new_values_json={
                "source_location_id": str(payload.source_location_id),
                "destination_location_id": str(payload.destination_location_id),
                "quantity": float(payload.quantity),
            },
        )
        await db.commit()
        await db.refresh(movement)
        return movement

    # =========================================================================
    # 7. INTERNAL STOCK REQUESTS
    # =========================================================================

    async def create_internal_stock_request(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        payload: InternalStockRequestCreate,
        user_id: UUID,
    ) -> InternalStockRequest:
        stmt = select(InternalStockRequest).where(
            InternalStockRequest.tenant_id == tenant_id,
            InternalStockRequest.request_number == payload.request_number,
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            raise ConflictException("InternalStockRequest", "request_number", payload.request_number)

        line_models = [
            InternalStockRequestLine(
                tenant_id=tenant_id,
                item_id=line.item_id,
                quantity_requested=line.quantity_requested,
                quantity_issued=Decimal("0.00"),
            )
            for line in payload.lines
        ]

        internal_req = InternalStockRequest(
            tenant_id=tenant_id,
            request_number=payload.request_number,
            department_id=payload.department_id,
            requestor_id=user_id,
            location_id=payload.location_id,
            status=InternalRequestStatus.PENDING,
            required_date=payload.required_date,
            notes=payload.notes,
            lines=line_models,
        )
        db.add(internal_req)
        await db.flush()

        await record_audit_log(
            db=db,
            tenant_id=tenant_id,
            action=AuditEventCategory.PROCUREMENT_STOCK_ADJUSTED,
            entity_type="InternalStockRequest",
            entity_id=internal_req.id,
            user_id=user_id,
            new_values_json={"request_number": internal_req.request_number},
        )
        await db.commit()
        return await self.get_internal_stock_request(db, tenant_id, internal_req.id)

    async def get_internal_stock_request(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        request_id: UUID,
    ) -> InternalStockRequest:
        stmt = (
            select(InternalStockRequest)
            .options(selectinload(InternalStockRequest.lines))
            .where(
                InternalStockRequest.tenant_id == tenant_id,
                InternalStockRequest.id == request_id,
            )
        )
        req = (await db.execute(stmt)).scalar_one_or_none()
        if not req:
            raise NotFoundException("InternalStockRequest", request_id)
        return req

    async def list_internal_stock_requests(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        department_id: UUID | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[InternalStockRequest], int]:
        stmt = select(InternalStockRequest).where(InternalStockRequest.tenant_id == tenant_id)
        if department_id:
            stmt = stmt.where(InternalStockRequest.department_id == department_id)
        if status:
            stmt = stmt.where(InternalStockRequest.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_count = (await db.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(InternalStockRequest.created_at.desc()).offset(skip).limit(limit)
        reqs = (await db.execute(stmt)).scalars().all()
        return list(reqs), total_count

    async def approve_internal_stock_request(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        request_id: UUID,
        user_id: UUID,
    ) -> InternalStockRequest:
        req = await self.get_internal_stock_request(db, tenant_id, request_id)
        if req.status != InternalRequestStatus.PENDING:
            raise BadRequestException(f"Cannot approve internal request in status '{req.status}'.")

        # Reserve quantities if available
        for line in req.lines:
            bal = await self.get_or_create_stock_balance(db, tenant_id, line.item_id, req.location_id)
            if bal.quantity_available >= line.quantity_requested:
                bal.quantity_available -= line.quantity_requested
                bal.quantity_reserved += line.quantity_requested

        req.status = InternalRequestStatus.APPROVED
        req.approved_by_id = user_id
        req.approved_at = datetime.now(UTC)

        await record_audit_log(
            db=db,
            tenant_id=tenant_id,
            action=AuditEventCategory.PROCUREMENT_STOCK_ADJUSTED,
            entity_type="InternalStockRequest",
            entity_id=req.id,
            user_id=user_id,
            new_values_json={"status": InternalRequestStatus.APPROVED},
        )
        await db.commit()
        return req

    async def fulfill_internal_stock_request(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        request_id: UUID,
        payload: InternalStockRequestFulfillRequest,
        user_id: UUID,
    ) -> InternalStockRequest:
        req = await self.get_internal_stock_request(db, tenant_id, request_id)
        if req.status not in (InternalRequestStatus.APPROVED, InternalRequestStatus.PARTIALLY_FULFILLED):
            raise BadRequestException("Internal request must be APPROVED to be fulfilled.")

        lines_map = {line.id: line for line in req.lines}

        for fulfill in payload.line_fulfillments:
            line_id = UUID(fulfill["line_id"]) if isinstance(fulfill["line_id"], str) else fulfill["line_id"]
            qty = Decimal(str(fulfill["quantity_to_issue"]))
            line = lines_map.get(line_id)
            if not line:
                continue

            bal = await self.get_or_create_stock_balance(db, tenant_id, line.item_id, req.location_id)
            # Release reservation and issue
            bal.quantity_reserved = max(Decimal("0.00"), bal.quantity_reserved - qty)
            bal.quantity_on_hand = max(Decimal("0.00"), bal.quantity_on_hand - qty)
            line.quantity_issued += qty

            # Record issue movement
            movement = StockMovement(
                tenant_id=tenant_id,
                movement_number=f"MOV-ISR-{uuid4().hex[:8].upper()}",
                item_id=line.item_id,
                movement_type=MovementType.ISSUE,
                source_location_id=req.location_id,
                destination_location_id=None,
                quantity=qty,
                unit_cost=Decimal("0.00"),
                total_value=Decimal("0.00"),
                reference_type="INTERNAL_REQUEST",
                reference_id=req.id,
                performed_by_id=user_id,
                timestamp=datetime.now(UTC),
                notes=f"Issued against ISR {req.request_number}",
            )
            db.add(movement)

        all_fulfilled = all(line.quantity_issued >= line.quantity_requested for line in req.lines)
        req.status = InternalRequestStatus.FULFILLED if all_fulfilled else InternalRequestStatus.PARTIALLY_FULFILLED

        await record_audit_log(
            db=db,
            tenant_id=tenant_id,
            action=AuditEventCategory.PROCUREMENT_STOCK_ISSUED,
            entity_type="InternalStockRequest",
            entity_id=req.id,
            user_id=user_id,
            new_values_json={"status": req.status},
        )
        await db.commit()
        return req

    # =========================================================================
    # 8. THREE-WAY INVOICE MATCHING
    # =========================================================================

    async def create_invoice_match(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        payload: SupplierInvoiceMatchCreate,
        user_id: UUID,
    ) -> SupplierInvoiceMatch:
        stmt = select(SupplierInvoiceMatch).where(
            SupplierInvoiceMatch.tenant_id == tenant_id,
            SupplierInvoiceMatch.match_reference == payload.match_reference,
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            raise ConflictException("SupplierInvoiceMatch", "match_reference", payload.match_reference)

        po = await self.get_purchase_order(db, tenant_id, payload.po_id)
        grn = await self.get_goods_receipt(db, tenant_id, payload.grn_id)

        if po.vendor_id != grn.vendor_id:
            raise BadRequestException("Purchase order and goods receipt vendor mismatch.")

        po_amount = po.total_amount
        received_amount = Decimal("0.00")
        po_lines_map = {l.id: l for l in po.lines}

        for grn_line in grn.lines:
            po_line = po_lines_map.get(grn_line.po_line_id)
            if po_line:
                received_amount += round(grn_line.quantity_accepted * po_line.unit_price, 2)

        # Calculate variances
        price_variance = abs(payload.invoice_amount - po_amount)
        po_qty = sum(l.quantity_ordered for l in po.lines)
        rcv_qty = sum(l.quantity_accepted for l in grn.lines)
        quantity_variance = abs(po_qty - rcv_qty)

        # Check tolerances
        max_allowed_price_variance = po_amount * (payload.price_tolerance_pct / Decimal("100.0"))
        max_allowed_qty_variance = po_qty * (payload.quantity_tolerance_pct / Decimal("100.0"))

        if price_variance > max_allowed_price_variance:
            status = InvoiceMatchStatus.PRICE_DISCREPANCY
        elif quantity_variance > max_allowed_qty_variance:
            status = InvoiceMatchStatus.QUANTITY_DISCREPANCY
        else:
            status = InvoiceMatchStatus.MATCHED

        match_record = SupplierInvoiceMatch(
            tenant_id=tenant_id,
            match_reference=payload.match_reference,
            po_id=payload.po_id,
            grn_id=payload.grn_id,
            invoice_reference_number=payload.invoice_reference_number,
            invoice_date=payload.invoice_date,
            invoice_amount=payload.invoice_amount,
            po_amount=po_amount,
            received_amount=received_amount,
            quantity_variance=quantity_variance,
            price_variance=price_variance,
            status=status,
            matched_by_id=user_id,
            matched_at=datetime.now(UTC),
            variance_notes=payload.variance_notes,
        )
        db.add(match_record)
        await db.flush()

        await record_audit_log(
            db=db,
            tenant_id=tenant_id,
            action=AuditEventCategory.PROCUREMENT_INVOICE_MATCHED,
            entity_type="SupplierInvoiceMatch",
            entity_id=match_record.id,
            user_id=user_id,
            new_values_json={
                "match_reference": match_record.match_reference,
                "status": match_record.status,
                "price_variance": float(price_variance),
            },
        )

        outbox = OutboxEvent(
            id=uuid4(),
            tenant_id=tenant_id,
            aggregate_type="SupplierInvoiceMatch",
            aggregate_id=match_record.id,
            event_type="INVOICE_MATCH_RECORDED",
            correlation_id=str(uuid4()),
            payload={
                "match_reference": match_record.match_reference,
                "status": match_record.status,
                "invoice_reference_number": match_record.invoice_reference_number,
            },
        )
        db.add(outbox)
        await db.commit()
        await db.refresh(match_record)
        return match_record

    async def override_invoice_match_discrepancy(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        match_id: UUID,
        payload: SupplierInvoiceMatchOverrideRequest,
        user_id: UUID,
    ) -> SupplierInvoiceMatch:
        stmt = select(SupplierInvoiceMatch).where(
            SupplierInvoiceMatch.tenant_id == tenant_id,
            SupplierInvoiceMatch.id == match_id,
        )
        match_rec = (await db.execute(stmt)).scalar_one_or_none()
        if not match_rec:
            raise NotFoundException("SupplierInvoiceMatch", match_id)

        if match_rec.status not in (
            InvoiceMatchStatus.PRICE_DISCREPANCY,
            InvoiceMatchStatus.QUANTITY_DISCREPANCY,
        ):
            raise BadRequestException(f"Cannot override match in status '{match_rec.status}'.")

        match_rec.status = InvoiceMatchStatus.OVERRIDE_APPROVED
        match_rec.override_reason = payload.override_reason
        match_rec.override_approved_by_id = user_id

        await record_audit_log(
            db=db,
            tenant_id=tenant_id,
            action=AuditEventCategory.PROCUREMENT_INVOICE_MATCHED,
            entity_type="SupplierInvoiceMatch",
            entity_id=match_rec.id,
            user_id=user_id,
            new_values_json={"override_reason": payload.override_reason, "status": InvoiceMatchStatus.OVERRIDE_APPROVED},
        )
        await db.commit()
        return match_rec

    async def get_invoice_match(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        match_id: UUID,
    ) -> SupplierInvoiceMatch:
        stmt = select(SupplierInvoiceMatch).where(
            SupplierInvoiceMatch.tenant_id == tenant_id,
            SupplierInvoiceMatch.id == match_id,
        )
        match_rec = (await db.execute(stmt)).scalar_one_or_none()
        if not match_rec:
            raise NotFoundException("SupplierInvoiceMatch", match_id)
        return match_rec

    async def list_invoice_matches(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[SupplierInvoiceMatch], int]:
        stmt = select(SupplierInvoiceMatch).where(SupplierInvoiceMatch.tenant_id == tenant_id)
        if status:
            stmt = stmt.where(SupplierInvoiceMatch.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_count = (await db.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(SupplierInvoiceMatch.created_at.desc()).offset(skip).limit(limit)
        matches = (await db.execute(stmt)).scalars().all()
        return list(matches), total_count

    # =========================================================================
    # 9. VENDOR RETURNS (RTV)
    # =========================================================================

    async def create_vendor_return(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        payload: VendorReturnCreate,
        user_id: UUID,
    ) -> VendorReturn:
        stmt = select(VendorReturn).where(
            VendorReturn.tenant_id == tenant_id,
            VendorReturn.return_number == payload.return_number,
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            raise ConflictException("VendorReturn", "return_number", payload.return_number)

        v_return = VendorReturn(
            tenant_id=tenant_id,
            return_number=payload.return_number,
            po_id=payload.po_id,
            grn_id=payload.grn_id,
            vendor_id=payload.vendor_id,
            item_id=payload.item_id,
            quantity=payload.quantity,
            reason=payload.reason,
            status=VendorReturn.status.default.arg if hasattr(VendorReturn.status, "default") else "REQUESTED",
            resolution_type=payload.resolution_type,
            resolution_reference=payload.resolution_reference,
            credit_note_amount=payload.credit_note_amount,
            created_by_id=user_id,
        )
        db.add(v_return)
        await db.flush()

        await record_audit_log(
            db=db,
            tenant_id=tenant_id,
            action=AuditEventCategory.PROCUREMENT_RETURN_CREATED,
            entity_type="VendorReturn",
            entity_id=v_return.id,
            user_id=user_id,
            new_values_json={"return_number": v_return.return_number, "quantity": float(v_return.quantity)},
        )
        await db.commit()
        await db.refresh(v_return)
        return v_return

    async def update_vendor_return_status(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        return_id: UUID,
        payload: VendorReturnStatusUpdateRequest,
        user_id: UUID,
    ) -> VendorReturn:
        stmt = select(VendorReturn).where(
            VendorReturn.tenant_id == tenant_id,
            VendorReturn.id == return_id,
        )
        ret = (await db.execute(stmt)).scalar_one_or_none()
        if not ret:
            raise NotFoundException("VendorReturn", return_id)

        ret.status = payload.status
        if payload.resolution_reference is not None:
            ret.resolution_reference = payload.resolution_reference
        if payload.credit_note_amount is not None:
            ret.credit_note_amount = payload.credit_note_amount

        await db.commit()
        return ret

    async def get_vendor_return(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        return_id: UUID,
    ) -> VendorReturn:
        stmt = select(VendorReturn).where(
            VendorReturn.tenant_id == tenant_id,
            VendorReturn.id == return_id,
        )
        ret = (await db.execute(stmt)).scalar_one_or_none()
        if not ret:
            raise NotFoundException("VendorReturn", return_id)
        return ret

    async def list_vendor_returns(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[VendorReturn], int]:
        stmt = select(VendorReturn).where(VendorReturn.tenant_id == tenant_id)
        if status:
            stmt = stmt.where(VendorReturn.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_count = (await db.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(VendorReturn.created_at.desc()).offset(skip).limit(limit)
        returns = (await db.execute(stmt)).scalars().all()
        return list(returns), total_count

    # =========================================================================
    # 10. PROCUREMENT & INVENTORY ANALYTICS
    # =========================================================================

    async def get_procurement_summary(
        self,
        db: AsyncSession,
        tenant_id: UUID,
    ) -> ProcurementSummaryReport:
        # Total and active approved vendors
        total_vendors = (
            await db.execute(select(func.count(Vendor.id)).where(Vendor.tenant_id == tenant_id))
        ).scalar() or 0

        active_vendors = (
            await db.execute(
                select(func.count(Vendor.id)).where(
                    Vendor.tenant_id == tenant_id,
                    Vendor.status == VendorStatus.APPROVED,
                )
            )
        ).scalar() or 0

        # Pending and approved requisitions
        pending_reqs = (
            await db.execute(
                select(func.count(PurchaseRequisition.id)).where(
                    PurchaseRequisition.tenant_id == tenant_id,
                    PurchaseRequisition.status.in_([RequisitionStatus.SUBMITTED, RequisitionStatus.UNDER_REVIEW]),
                )
            )
        ).scalar() or 0

        approved_req_val = (
            await db.execute(
                select(func.coalesce(func.sum(PurchaseRequisition.estimated_total_amount), Decimal("0.00"))).where(
                    PurchaseRequisition.tenant_id == tenant_id,
                    PurchaseRequisition.status == RequisitionStatus.APPROVED,
                )
            )
        ).scalar() or Decimal("0.00")

        # Open and closed POs
        open_pos_count = (
            await db.execute(
                select(func.count(PurchaseOrder.id)).where(
                    PurchaseOrder.tenant_id == tenant_id,
                    PurchaseOrder.status.in_(
                        [
                            PurchaseOrderStatus.ISSUED,
                            PurchaseOrderStatus.ACKNOWLEDGED,
                            PurchaseOrderStatus.PARTIALLY_DELIVERED,
                        ]
                    ),
                )
            )
        ).scalar() or 0

        open_pos_val = (
            await db.execute(
                select(func.coalesce(func.sum(PurchaseOrder.total_amount), Decimal("0.00"))).where(
                    PurchaseOrder.tenant_id == tenant_id,
                    PurchaseOrder.status.in_(
                        [
                            PurchaseOrderStatus.ISSUED,
                            PurchaseOrderStatus.ACKNOWLEDGED,
                            PurchaseOrderStatus.PARTIALLY_DELIVERED,
                        ]
                    ),
                )
            )
        ).scalar() or Decimal("0.00")

        closed_pos_val = (
            await db.execute(
                select(func.coalesce(func.sum(PurchaseOrder.total_amount), Decimal("0.00"))).where(
                    PurchaseOrder.tenant_id == tenant_id,
                    PurchaseOrder.status == PurchaseOrderStatus.CLOSED,
                )
            )
        ).scalar() or Decimal("0.00")

        # Goods receipts count
        grns_count = (
            await db.execute(select(func.count(GoodsReceipt.id)).where(GoodsReceipt.tenant_id == tenant_id))
        ).scalar() or 0

        # Matched vs discrepancy invoices
        matched_invoices = (
            await db.execute(
                select(func.count(SupplierInvoiceMatch.id)).where(
                    SupplierInvoiceMatch.tenant_id == tenant_id,
                    SupplierInvoiceMatch.status == InvoiceMatchStatus.MATCHED,
                )
            )
        ).scalar() or 0

        discrepancy_invoices = (
            await db.execute(
                select(func.count(SupplierInvoiceMatch.id)).where(
                    SupplierInvoiceMatch.tenant_id == tenant_id,
                    SupplierInvoiceMatch.status.in_(
                        [
                            InvoiceMatchStatus.PRICE_DISCREPANCY,
                            InvoiceMatchStatus.QUANTITY_DISCREPANCY,
                        ]
                    ),
                )
            )
        ).scalar() or 0

        return ProcurementSummaryReport(
            total_vendors_count=total_vendors,
            active_approved_vendors_count=active_vendors,
            pending_requisitions_count=pending_reqs,
            approved_requisitions_value=Decimal(str(approved_req_val)),
            open_purchase_orders_count=open_pos_count,
            open_purchase_orders_value=Decimal(str(open_pos_val)),
            closed_purchase_orders_value=Decimal(str(closed_pos_val)),
            goods_receipts_count=grns_count,
            matched_invoices_count=matched_invoices,
            discrepancy_invoices_count=discrepancy_invoices,
        )

    async def get_inventory_valuation(
        self,
        db: AsyncSession,
        tenant_id: UUID,
    ) -> InventoryValuationReport:
        total_items = (
            await db.execute(select(func.count(InventoryItem.id)).where(InventoryItem.tenant_id == tenant_id))
        ).scalar() or 0

        total_locations = (
            await db.execute(select(func.count(InventoryLocation.id)).where(InventoryLocation.tenant_id == tenant_id))
        ).scalar() or 0

        # Items by category
        cat_stmt = (
            select(InventoryItem.category, func.count(InventoryItem.id))
            .where(InventoryItem.tenant_id == tenant_id)
            .group_by(InventoryItem.category)
        )
        cat_counts = dict((await db.execute(cat_stmt)).all())

        # Total valuation = sum(quantity_on_hand * unit_price_average)
        val_stmt = (
            select(
                func.coalesce(
                    func.sum(StockBalance.quantity_on_hand * InventoryItem.unit_price_average),
                    Decimal("0.00"),
                )
            )
            .join(InventoryItem, StockBalance.item_id == InventoryItem.id)
            .where(StockBalance.tenant_id == tenant_id)
        )
        total_valuation = (await db.execute(val_stmt)).scalar() or Decimal("0.00")

        # Low stock items: items whose total on-hand <= reorder_threshold
        low_stock_stmt = (
            select(func.count(InventoryItem.id))
            .join(StockBalance, StockBalance.item_id == InventoryItem.id, isouter=True)
            .where(InventoryItem.tenant_id == tenant_id)
            .group_by(InventoryItem.id, InventoryItem.reorder_threshold)
            .having(func.coalesce(func.sum(StockBalance.quantity_on_hand), Decimal("0.00")) <= InventoryItem.reorder_threshold)
        )
        low_stock_items = len((await db.execute(low_stock_stmt)).all())

        return InventoryValuationReport(
            total_items_count=total_items,
            low_stock_items_count=low_stock_items,
            total_inventory_valuation=Decimal(str(total_valuation)),
            total_locations_count=total_locations,
            items_by_category=cat_counts,
        )


procurement_service = ProcurementService()
