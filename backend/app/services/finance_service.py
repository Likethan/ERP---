"""Finance, Fees & Billing Engine authoritative service layer."""

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    ConflictException,
    NotFoundException,
    ValidationException,
)
from app.models.audit import AuditLog
from app.models.core import AcademicYear, Program
from app.models.finance import (
    FeeCategory,
    FeeItem,
    FeeStructure,
    FinancialAdjustment,
    Invoice,
    InvoiceLineItem,
    PaymentAllocation,
    PaymentTransaction,
    Receipt,
    RefundTransaction,
    StudentFeeAssignment,
    StudentFeeConcession,
)
from app.models.people import StudentProfile as Student
from app.schemas.finance import (
    FeeCategoryCreate,
    FeeCategoryUpdate,
    FeeStructureCreate,
    FinancialAdjustmentCreate,
    InvoiceCreate,
    PaymentCreate,
    RefundCreate,
    ScholarshipCreate,
    StudentFeeAssignmentCreate,
)

DEFAULT_FEE_CATEGORIES = [
    {"code": "TUITION", "name": "Tuition Fee", "is_refundable": False, "description": "Core academic tuition charges"},
    {"code": "EXAMINATION", "name": "Examination Fee", "is_refundable": False, "description": "Semester exam evaluation charges"},
    {"code": "LIBRARY", "name": "Library Fee", "is_refundable": False, "description": "Library and digital resource charges"},
    {"code": "LABORATORY", "name": "Laboratory Fee", "is_refundable": False, "description": "Lab consumables and workshop charges"},
    {"code": "HOSTEL", "name": "Hostel Fee", "is_refundable": True, "description": "Hostel accommodation and boarding"},
    {"code": "TRANSPORT", "name": "Transport Fee", "is_refundable": True, "description": "Bus routes and transport facilities"},
    {"code": "SPORTS", "name": "Sports & Cultural Fee", "is_refundable": False, "description": "Athletic and cultural activities"},
    {"code": "REGISTRATION", "name": "Registration Fee", "is_refundable": False, "description": "One-time admission registration fee"},
    {"code": "OTHER", "name": "Miscellaneous Fee", "is_refundable": False, "description": "Other institution fees"},
]


class FinanceService:
    """Service layer managing fees, structures, invoices, payments, receipts, and refunds."""

    @staticmethod
    def _serialize_audit_values(val: Any) -> Any:
        if isinstance(val, dict):
            return {k: FinanceService._serialize_audit_values(v) for k, v in val.items()}
        elif isinstance(val, list):
            return [FinanceService._serialize_audit_values(v) for v in val]
        elif isinstance(val, Decimal):
            return str(val)
        elif isinstance(val, (date, datetime)):
            return val.isoformat()
        elif isinstance(val, UUID):
            return str(val)
        return val

    @staticmethod
    async def _log_audit(
        db: AsyncSession,
        tenant_id: UUID,
        actor_user_id: UUID | None,
        action: str,
        resource_type: str,
        resource_id: UUID,
        metadata: dict | None = None,
    ) -> None:
        """Create and persist an AuditLog entry."""
        serialized = FinanceService._serialize_audit_values(metadata) if metadata else None
        log_entry = AuditLog(
            tenant_id=tenant_id,
            user_id=actor_user_id,
            action=action,
            entity_type=resource_type,
            entity_id=resource_id,
            new_values_json=serialized or {},
            ip_address="127.0.0.1",
        )
        db.add(log_entry)
        await db.flush()

    # ---------------------------------------------------------------------------
    # Sequence Generators
    # ---------------------------------------------------------------------------

    @staticmethod
    async def generate_invoice_number(db: AsyncSession, tenant_id: UUID) -> str:
        """Generate human-readable sequence INV-YYYY-XXXXXX unique to tenant."""
        year = datetime.now(UTC).year
        stmt = (
            select(func.count(Invoice.id))
            .where(Invoice.tenant_id == tenant_id)
        )
        count = (await db.execute(stmt)).scalar() or 0
        seq = count + 1
        return f"INV-{year}-{seq:06d}"

    @staticmethod
    async def generate_payment_number(db: AsyncSession, tenant_id: UUID) -> str:
        """Generate human-readable sequence PAY-YYYY-XXXXXX unique to tenant."""
        year = datetime.now(UTC).year
        stmt = (
            select(func.count(PaymentTransaction.id))
            .where(PaymentTransaction.tenant_id == tenant_id)
        )
        count = (await db.execute(stmt)).scalar() or 0
        seq = count + 1
        return f"PAY-{year}-{seq:06d}"

    @staticmethod
    async def generate_receipt_number(db: AsyncSession, tenant_id: UUID) -> str:
        """Generate human-readable sequence RCP-YYYY-XXXXXX unique to tenant."""
        year = datetime.now(UTC).year
        stmt = (
            select(func.count(Receipt.id))
            .where(Receipt.tenant_id == tenant_id)
        )
        count = (await db.execute(stmt)).scalar() or 0
        seq = count + 1
        return f"RCP-{year}-{seq:06d}"

    # ---------------------------------------------------------------------------
    # Fee Categories
    # ---------------------------------------------------------------------------

    @classmethod
    async def ensure_default_categories(cls, db: AsyncSession, tenant_id: UUID) -> None:
        """Seed default institutional fee categories if none exist."""
        stmt = select(func.count(FeeCategory.id)).where(FeeCategory.tenant_id == tenant_id)
        count = (await db.execute(stmt)).scalar() or 0
        if count == 0:
            for item in DEFAULT_FEE_CATEGORIES:
                cat = FeeCategory(
                    tenant_id=tenant_id,
                    code=item["code"],
                    name=item["name"],
                    is_refundable=item["is_refundable"],
                    description=item["description"],
                    is_active=True,
                )
                db.add(cat)
            await db.commit()

    @classmethod
    async def list_categories(
        cls, db: AsyncSession, tenant_id: UUID, is_active: bool | None = None
    ) -> list[FeeCategory]:
        """List tenant fee categories."""
        await cls.ensure_default_categories(db, tenant_id)
        stmt = select(FeeCategory).where(FeeCategory.tenant_id == tenant_id)
        if is_active is not None:
            stmt = stmt.where(FeeCategory.is_active == is_active)
        stmt = stmt.order_by(FeeCategory.code)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def create_category(
        cls, db: AsyncSession, tenant_id: UUID, data: FeeCategoryCreate, current_user_id: UUID
    ) -> FeeCategory:
        """Create a new fee category."""
        code_clean = data.code.strip().upper()
        stmt = select(FeeCategory).where(
            and_(FeeCategory.tenant_id == tenant_id, FeeCategory.code == code_clean)
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            raise ConflictException(f"Fee category with code '{code_clean}' already exists.")

        category = FeeCategory(
            tenant_id=tenant_id,
            code=code_clean,
            name=data.name.strip(),
            description=data.description.strip() if data.description else None,
            is_refundable=data.is_refundable,
            is_active=data.is_active,
        )
        db.add(category)
        await db.commit()
        await db.refresh(category)

        await FinanceService._log_audit(
            db=db,
            tenant_id=tenant_id,
            actor_user_id=current_user_id,
            action="FEE_CATEGORY_CREATED",
            resource_type="FeeCategory",
            resource_id=category.id,
            metadata={"code": category.code, "name": category.name},
        )
        return category

    @classmethod
    async def update_category(
        cls, db: AsyncSession, tenant_id: UUID, category_id: UUID, data: FeeCategoryUpdate, current_user_id: UUID
    ) -> FeeCategory:
        """Update existing fee category."""
        stmt = select(FeeCategory).where(
            and_(FeeCategory.id == category_id, FeeCategory.tenant_id == tenant_id)
        )
        category = (await db.execute(stmt)).scalar_one_or_none()
        if not category:
            raise NotFoundException("FeeCategory", category_id)

        if data.name is not None:
            category.name = data.name.strip()
        if data.description is not None:
            category.description = data.description.strip()
        if data.is_refundable is not None:
            category.is_refundable = data.is_refundable
        if data.is_active is not None:
            category.is_active = data.is_active

        await db.commit()
        await db.refresh(category)

        await FinanceService._log_audit(
            db=db,
            tenant_id=tenant_id,
            actor_user_id=current_user_id,
            action="FEE_CATEGORY_UPDATED",
            resource_type="FeeCategory",
            resource_id=category.id,
            metadata={"code": category.code},
        )
        return category

    # ---------------------------------------------------------------------------
    # Fee Structures
    # ---------------------------------------------------------------------------

    @classmethod
    async def list_fee_structures(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        program_id: UUID | None = None,
        academic_year_id: UUID | None = None,
        semester_id: UUID | None = None,
        status: str | None = None,
    ) -> list[FeeStructure]:
        """List fee structures with associated program and year names."""
        stmt = (
            select(FeeStructure)
            .where(FeeStructure.tenant_id == tenant_id)
            .options(selectinload(FeeStructure.items))
        )
        if program_id:
            stmt = stmt.where(FeeStructure.program_id == program_id)
        if academic_year_id:
            stmt = stmt.where(FeeStructure.academic_year_id == academic_year_id)
        if semester_id:
            stmt = stmt.where(FeeStructure.semester_id == semester_id)
        if status:
            stmt = stmt.where(FeeStructure.status == status)

        stmt = stmt.order_by(desc(FeeStructure.created_at))
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def get_fee_structure(
        cls, db: AsyncSession, tenant_id: UUID, structure_id: UUID
    ) -> FeeStructure:
        """Fetch fee structure with lines."""
        stmt = (
            select(FeeStructure)
            .where(and_(FeeStructure.id == structure_id, FeeStructure.tenant_id == tenant_id))
            .options(selectinload(FeeStructure.items))
        )
        structure = (await db.execute(stmt)).scalar_one_or_none()
        if not structure:
            raise NotFoundException("FeeStructure", structure_id)
        return structure

    @classmethod
    async def create_fee_structure(
        cls, db: AsyncSession, tenant_id: UUID, data: FeeStructureCreate, current_user_id: UUID
    ) -> FeeStructure:
        """Create new fee structure with items."""
        # Verify program & academic year exist
        prog_stmt = select(Program).where(and_(Program.id == data.program_id, Program.tenant_id == tenant_id))
        if not (await db.execute(prog_stmt)).scalar_one_or_none():
            raise NotFoundException("Program", data.program_id)

        ay_stmt = select(AcademicYear).where(and_(AcademicYear.id == data.academic_year_id, AcademicYear.tenant_id == tenant_id))
        if not (await db.execute(ay_stmt)).scalar_one_or_none():
            raise NotFoundException("AcademicYear", data.academic_year_id)

        structure = FeeStructure(
            tenant_id=tenant_id,
            program_id=data.program_id,
            academic_year_id=data.academic_year_id,
            semester_id=data.semester_id,
            batch_id=data.batch_id,
            quota_type=data.quota_type.upper(),
            name=data.name.strip(),
            status="DRAFT",
            version=1,
        )
        db.add(structure)
        await db.flush()

        seq = 1
        for item in data.items:
            cat_stmt = select(FeeCategory).where(and_(FeeCategory.id == item.category_id, FeeCategory.tenant_id == tenant_id))
            if not (await db.execute(cat_stmt)).scalar_one_or_none():
                raise NotFoundException("FeeCategory", item.category_id)

            fee_item = FeeItem(
                fee_structure_id=structure.id,
                category_id=item.category_id,
                name=item.name.strip(),
                amount=Decimal(str(item.amount)),
                is_optional=item.is_optional,
                sequence=item.sequence or seq,
            )
            db.add(fee_item)
            seq += 1

        await db.commit()
        await db.refresh(structure)

        await FinanceService._log_audit(
            db=db,
            tenant_id=tenant_id,
            actor_user_id=current_user_id,
            action="FEE_STRUCTURE_CREATED",
            resource_type="FeeStructure",
            resource_id=structure.id,
            metadata={"name": structure.name, "quota_type": structure.quota_type},
        )
        return await cls.get_fee_structure(db, tenant_id, structure.id)

    @classmethod
    async def approve_fee_structure(
        cls, db: AsyncSession, tenant_id: UUID, structure_id: UUID, current_user_id: UUID
    ) -> FeeStructure:
        """Transition fee structure from DRAFT to APPROVED."""
        structure = await cls.get_fee_structure(db, tenant_id, structure_id)
        if structure.status not in ("DRAFT", "APPROVED"):
            raise ValidationException(f"Cannot approve fee structure in '{structure.status}' state.")

        structure.status = "APPROVED"
        await db.commit()
        await db.refresh(structure)

        await FinanceService._log_audit(
            db=db,
            tenant_id=tenant_id,
            actor_user_id=current_user_id,
            action="FEE_STRUCTURE_APPROVED",
            resource_type="FeeStructure",
            resource_id=structure.id,
            metadata={"name": structure.name},
        )
        return structure

    @classmethod
    async def activate_fee_structure(
        cls, db: AsyncSession, tenant_id: UUID, structure_id: UUID, current_user_id: UUID
    ) -> FeeStructure:
        """Activate fee structure for billing."""
        structure = await cls.get_fee_structure(db, tenant_id, structure_id)
        structure.status = "ACTIVE"
        await db.commit()
        await db.refresh(structure)

        await FinanceService._log_audit(
            db=db,
            tenant_id=tenant_id,
            actor_user_id=current_user_id,
            action="FEE_STRUCTURE_ACTIVATED",
            resource_type="FeeStructure",
            resource_id=structure.id,
            metadata={"name": structure.name},
        )
        return structure

    @classmethod
    async def retire_fee_structure(
        cls, db: AsyncSession, tenant_id: UUID, structure_id: UUID, current_user_id: UUID
    ) -> FeeStructure:
        """Retire fee structure from future billing."""
        structure = await cls.get_fee_structure(db, tenant_id, structure_id)
        structure.status = "RETIRED"
        await db.commit()
        await db.refresh(structure)

        await FinanceService._log_audit(
            db=db,
            tenant_id=tenant_id,
            actor_user_id=current_user_id,
            action="FEE_STRUCTURE_RETIRED",
            resource_type="FeeStructure",
            resource_id=structure.id,
            metadata={"name": structure.name},
        )
        return structure

    # ---------------------------------------------------------------------------
    # Student Fee Assignment
    # ---------------------------------------------------------------------------

    @classmethod
    async def assign_student_fee(
        cls, db: AsyncSession, tenant_id: UUID, data: StudentFeeAssignmentCreate, current_user_id: UUID
    ) -> StudentFeeAssignment:
        """Authoritatively bind a student to an applicable FeeStructure."""
        # Verify student exists
        s_stmt = select(Student).where(and_(Student.id == data.student_id, Student.tenant_id == tenant_id))
        student = (await db.execute(s_stmt)).scalar_one_or_none()
        if not student:
            raise NotFoundException("Student", data.student_id)

        # Verify fee structure exists
        structure = await cls.get_fee_structure(db, tenant_id, data.fee_structure_id)

        # Check existing assignment
        check_stmt = select(StudentFeeAssignment).where(
            and_(
                StudentFeeAssignment.tenant_id == tenant_id,
                StudentFeeAssignment.student_id == data.student_id,
                StudentFeeAssignment.academic_year_id == data.academic_year_id,
                StudentFeeAssignment.fee_structure_id == data.fee_structure_id,
            )
        )
        existing = (await db.execute(check_stmt)).scalar_one_or_none()
        if existing:
            raise ConflictException("Student already has this fee structure assigned for the academic year.")

        assignment = StudentFeeAssignment(
            tenant_id=tenant_id,
            student_id=data.student_id,
            fee_structure_id=data.fee_structure_id,
            academic_year_id=data.academic_year_id,
            semester_id=data.semester_id,
            status="ACTIVE",
            assigned_date=date.today(),
            remarks=data.remarks,
        )
        db.add(assignment)
        await db.commit()
        await db.refresh(assignment)

        await FinanceService._log_audit(
            db=db,
            tenant_id=tenant_id,
            actor_user_id=current_user_id,
            action="FEE_ASSIGNED",
            resource_type="StudentFeeAssignment",
            resource_id=assignment.id,
            metadata={"student_id": str(data.student_id), "fee_structure": structure.name},
        )
        stmt = (
            select(StudentFeeAssignment)
            .options(selectinload(StudentFeeAssignment.fee_structure))
            .where(StudentFeeAssignment.id == assignment.id)
        )
        return (await db.execute(stmt)).scalar_one()

    @classmethod
    async def list_student_fee_assignments(
        cls, db: AsyncSession, tenant_id: UUID, student_id: UUID
    ) -> list[StudentFeeAssignment]:
        """List fee assignments for a student."""
        stmt = (
            select(StudentFeeAssignment)
            .where(and_(StudentFeeAssignment.tenant_id == tenant_id, StudentFeeAssignment.student_id == student_id))
            .options(selectinload(StudentFeeAssignment.fee_structure).selectinload(FeeStructure.items))
            .order_by(desc(StudentFeeAssignment.created_at))
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    # ---------------------------------------------------------------------------
    # Invoices
    # ---------------------------------------------------------------------------

    @classmethod
    async def create_invoice(
        cls, db: AsyncSession, tenant_id: UUID, data: InvoiceCreate, current_user_id: UUID
    ) -> Invoice:
        """Create a new billing invoice with itemized line items and scholarship deductions."""
        # Verify student
        s_stmt = select(Student).where(and_(Student.id == data.student_id, Student.tenant_id == tenant_id))
        student = (await db.execute(s_stmt)).scalar_one_or_none()
        if not student:
            raise NotFoundException("Student", data.student_id)

        invoice_number = await cls.generate_invoice_number(db, tenant_id)

        invoice = Invoice(
            tenant_id=tenant_id,
            student_id=data.student_id,
            academic_year_id=data.academic_year_id,
            semester_id=data.semester_id,
            invoice_number=invoice_number,
            issue_date=date.today(),
            due_date=data.due_date,
            currency=data.currency or "INR",
            gross_amount=Decimal("0.00"),
            concession_amount=Decimal("0.00"),
            adjustment_amount=Decimal("0.00"),
            net_payable=Decimal("0.00"),
            paid_amount=Decimal("0.00"),
            balance_amount=Decimal("0.00"),
            status="DRAFT",
            remarks=data.remarks,
        )
        db.add(invoice)
        await db.flush()

        gross_sum = Decimal("0.00")

        # 1. Add line items from fee structure if provided
        if data.fee_structure_id:
            structure = await cls.get_fee_structure(db, tenant_id, data.fee_structure_id)
            for item in structure.items:
                line = InvoiceLineItem(
                    invoice_id=invoice.id,
                    category_id=item.category_id,
                    description=item.name,
                    amount=item.amount,
                    waived_amount=Decimal("0.00"),
                )
                db.add(line)
                gross_sum += item.amount

        # 2. Add custom items if provided
        if data.items:
            for item_data in data.items:
                line = InvoiceLineItem(
                    invoice_id=invoice.id,
                    category_id=item_data.category_id,
                    description=item_data.description.strip(),
                    amount=Decimal(str(item_data.amount)),
                    waived_amount=Decimal(str(item_data.waived_amount or "0.00")),
                )
                db.add(line)
                gross_sum += Decimal(str(item_data.amount))

        if gross_sum == 0:
            raise ValidationException("An invoice must contain at least one chargeable fee line item.")

        invoice.gross_amount = gross_sum

        # 3. Check and apply scholarships/concessions
        concession_sum = Decimal("0.00")
        if data.apply_scholarships:
            con_stmt = select(StudentFeeConcession).where(
                and_(
                    StudentFeeConcession.tenant_id == tenant_id,
                    StudentFeeConcession.student_id == data.student_id,
                    StudentFeeConcession.academic_year_id == data.academic_year_id,
                    StudentFeeConcession.status == "APPROVED",
                )
            )
            concessions = (await db.execute(con_stmt)).scalars().all()
            for con in concessions:
                concession_sum += con.amount

        # Concessions cannot exceed gross
        concession_sum = min(concession_sum, gross_sum)
        invoice.concession_amount = concession_sum
        invoice.net_payable = gross_sum - concession_sum
        invoice.balance_amount = invoice.net_payable

        await db.commit()
        await db.refresh(invoice)

        await FinanceService._log_audit(
            db=db,
            tenant_id=tenant_id,
            actor_user_id=current_user_id,
            action="INVOICE_CREATED",
            resource_type="Invoice",
            resource_id=invoice.id,
            metadata={"invoice_number": invoice.invoice_number, "net_payable": str(invoice.net_payable)},
        )
        return await cls.get_invoice(db, tenant_id, invoice.id)

    @classmethod
    async def issue_invoice(
        cls, db: AsyncSession, tenant_id: UUID, invoice_id: UUID, current_user_id: UUID
    ) -> Invoice:
        """Issue a draft invoice, formally committing billing liability."""
        invoice = await cls.get_invoice(db, tenant_id, invoice_id)
        if invoice.status != "DRAFT":
            raise ValidationException(f"Cannot issue invoice in '{invoice.status}' state.")

        invoice.status = "ISSUED"
        await db.commit()
        await db.refresh(invoice)

        await FinanceService._log_audit(
            db=db,
            tenant_id=tenant_id,
            actor_user_id=current_user_id,
            action="INVOICE_ISSUED",
            resource_type="Invoice",
            resource_id=invoice.id,
            metadata={"invoice_number": invoice.invoice_number, "net_payable": str(invoice.net_payable)},
        )
        return invoice

    @classmethod
    async def cancel_invoice(
        cls, db: AsyncSession, tenant_id: UUID, invoice_id: UUID, current_user_id: UUID
    ) -> Invoice:
        """Cancel an invoice provided no payments have been allocated."""
        invoice = await cls.get_invoice(db, tenant_id, invoice_id)
        if invoice.paid_amount > 0:
            raise ValidationException(
                "Cannot cancel invoice that has allocated payments. Reallocate or refund payments first."
            )
        if invoice.status == "CANCELLED":
            raise ValidationException("Invoice is already cancelled.")

        invoice.status = "CANCELLED"
        await db.commit()
        await db.refresh(invoice)

        await FinanceService._log_audit(
            db=db,
            tenant_id=tenant_id,
            actor_user_id=current_user_id,
            action="INVOICE_CANCELLED",
            resource_type="Invoice",
            resource_id=invoice.id,
            metadata={"invoice_number": invoice.invoice_number},
        )
        return invoice

    @classmethod
    async def get_invoice(
        cls, db: AsyncSession, tenant_id: UUID, invoice_id: UUID
    ) -> Invoice:
        """Fetch invoice with line items, allocations, and adjustments."""
        stmt = (
            select(Invoice)
            .where(and_(Invoice.id == invoice_id, Invoice.tenant_id == tenant_id))
            .options(
                selectinload(Invoice.items),
                selectinload(Invoice.allocations),
                selectinload(Invoice.adjustments),
            )
        )
        invoice = (await db.execute(stmt)).scalar_one_or_none()
        if not invoice:
            raise NotFoundException("Invoice", invoice_id)

        # Dynamic overdue calculation: only ISSUED invoices past due date become OVERDUE
        if invoice.status == "ISSUED" and invoice.due_date < date.today() and invoice.balance_amount > 0:
            invoice.status = "OVERDUE"

        return invoice

    @classmethod
    async def list_invoices(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        student_id: UUID | None = None,
        academic_year_id: UUID | None = None,
        semester_id: UUID | None = None,
        status: str | None = None,
        is_overdue: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Invoice], int]:
        """List tenant invoices with filters."""
        stmt = (
            select(Invoice)
            .where(Invoice.tenant_id == tenant_id)
            .options(selectinload(Invoice.items))
        )
        if student_id:
            stmt = stmt.where(Invoice.student_id == student_id)
        if academic_year_id:
            stmt = stmt.where(Invoice.academic_year_id == academic_year_id)
        if semester_id:
            stmt = stmt.where(Invoice.semester_id == semester_id)
        if status:
            stmt = stmt.where(Invoice.status == status)

        today = date.today()
        if is_overdue is True:
            stmt = stmt.where(
                and_(
                    Invoice.due_date < today,
                    Invoice.balance_amount > 0,
                    Invoice.status.notin_(["PAID", "CANCELLED"]),
                )
            )
        elif is_overdue is False:
            stmt = stmt.where(
                or_(
                    Invoice.due_date >= today,
                    Invoice.balance_amount == 0,
                )
            )

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(desc(Invoice.issue_date), desc(Invoice.created_at)).limit(limit).offset(offset)
        result = await db.execute(stmt)
        invoices = list(result.scalars().all())

        return invoices, total

    # ---------------------------------------------------------------------------
    # Payments & Allocations
    # ---------------------------------------------------------------------------

    @classmethod
    async def record_payment(
        cls, db: AsyncSession, tenant_id: UUID, data: PaymentCreate, current_user_id: UUID
    ) -> PaymentTransaction:
        """Record an inward student payment transaction and atomically allocate to invoice(s)."""
        # Verify student
        s_stmt = select(Student).where(and_(Student.id == data.student_id, Student.tenant_id == tenant_id))
        student = (await db.execute(s_stmt)).scalar_one_or_none()
        if not student:
            raise NotFoundException("Student", data.student_id)

        payment_amount = Decimal(str(data.amount))
        if payment_amount <= 0:
            raise ValidationException("Payment amount must be greater than zero.")

        # Check duplicate reference if provided
        ref_clean = data.transaction_reference.strip()
        ref_stmt = select(PaymentTransaction).where(
            and_(
                PaymentTransaction.tenant_id == tenant_id,
                PaymentTransaction.transaction_reference == ref_clean,
            )
        )
        if (await db.execute(ref_stmt)).scalar_one_or_none():
            raise ConflictException(f"Payment with transaction reference '{ref_clean}' has already been recorded.")

        payment_number = await cls.generate_payment_number(db, tenant_id)
        payment_date = data.payment_date or datetime.now(UTC)

        payment = PaymentTransaction(
            tenant_id=tenant_id,
            student_id=data.student_id,
            payment_number=payment_number,
            transaction_reference=ref_clean,
            payment_mode=data.payment_mode.upper(),
            gateway_provider=data.gateway_provider,
            gateway_transaction_id=data.gateway_transaction_id,
            payment_date=payment_date,
            amount=payment_amount,
            currency=data.currency or "INR",
            status="SUCCESS",
            received_by_user_id=current_user_id,
            remarks=data.remarks,
        )
        db.add(payment)
        await db.flush()

        # Handle Allocations
        total_allocated = Decimal("0.00")
        allocated_invoices: list[Invoice] = []

        if data.allocations:
            for item in data.allocations:
                alloc_amt = Decimal(str(item.amount))
                if alloc_amt <= 0:
                    raise ValidationException("Allocated amount must be greater than zero.")

                inv = await cls.get_invoice(db, tenant_id, item.invoice_id)
                if inv.student_id != data.student_id:
                    raise ValidationException("Invoice does not belong to the paying student.")
                if inv.status in ("DRAFT", "CANCELLED"):
                    raise ValidationException(f"Cannot allocate payment to invoice in '{inv.status}' state.")

                if alloc_amt > inv.balance_amount:
                    raise ValidationException(
                        f"Allocation amount ({alloc_amt}) exceeds invoice {inv.invoice_number} balance due ({inv.balance_amount})."
                    )

                # Deduct balance & increase paid
                inv.paid_amount += alloc_amt
                inv.balance_amount -= alloc_amt
                if inv.balance_amount == 0:
                    inv.status = "PAID"
                else:
                    inv.status = "PARTIALLY_PAID"

                allocation = PaymentAllocation(
                    payment_id=payment.id,
                    invoice_id=inv.id,
                    allocated_amount=alloc_amt,
                    allocated_at=datetime.now(UTC),
                )
                db.add(allocation)
                total_allocated += alloc_amt
                allocated_invoices.append(inv)

            if total_allocated > payment_amount:
                raise ValidationException(
                    f"Sum of allocations ({total_allocated}) exceeds payment amount ({payment_amount})."
                )

        # Generate official legal receipt upon payment
        receipt_number = await cls.generate_receipt_number(db, tenant_id)
        receipt = Receipt(
            tenant_id=tenant_id,
            payment_id=payment.id,
            receipt_number=receipt_number,
            issue_date=datetime.now(UTC),
            is_cancelled=False,
        )
        db.add(receipt)

        # Atomically emit domain event in active transaction
        try:
            from app.core.events import OutboxService
            first_inv = allocated_invoices[0].id if allocated_invoices else None
            await OutboxService.publish_event(
                db=db,
                tenant_id=tenant_id,
                event_type="finance.payment.confirmed",
                aggregate_type="Payment",
                aggregate_id=payment.id,
                payload={
                    "payment_id": str(payment.id),
                    "invoice_id": str(first_inv) if first_inv else None,
                    "student_id": str(data.student_id),
                    "amount": float(payment_amount),
                    "payment_method": data.payment_method,
                    "transaction_ref": payment.transaction_reference,
                },
                actor_id=current_user_id,
                producer="FINANCE_MODULE",
            )
        except Exception:
            pass

        await db.commit()
        await db.refresh(payment)

        # Audit events
        await FinanceService._log_audit(
            db=db,
            tenant_id=tenant_id,
            actor_user_id=current_user_id,
            action="PAYMENT_CREATED",
            resource_type="PaymentTransaction",
            resource_id=payment.id,
            metadata={"payment_number": payment.payment_number, "amount": str(payment.amount)},
        )
        if total_allocated > 0:
            await FinanceService._log_audit(
                db=db,
                tenant_id=tenant_id,
                actor_user_id=current_user_id,
                action="PAYMENT_ALLOCATED",
                resource_type="PaymentTransaction",
                resource_id=payment.id,
                metadata={"total_allocated": str(total_allocated)},
            )
        await FinanceService._log_audit(
            db=db,
            tenant_id=tenant_id,
            actor_user_id=current_user_id,
            action="RECEIPT_ISSUED",
            resource_type="Receipt",
            resource_id=receipt.id,
            metadata={"receipt_number": receipt.receipt_number, "amount": str(payment.amount)},
        )

        return await cls.get_payment(db, tenant_id, payment.id)

    @classmethod
    async def get_payment(
        cls, db: AsyncSession, tenant_id: UUID, payment_id: UUID
    ) -> PaymentTransaction:
        """Fetch payment with allocations and receipt."""
        stmt = (
            select(PaymentTransaction)
            .where(and_(PaymentTransaction.id == payment_id, PaymentTransaction.tenant_id == tenant_id))
            .options(
                selectinload(PaymentTransaction.allocations).selectinload(PaymentAllocation.invoice),
                selectinload(PaymentTransaction.receipt),
            )
        )
        payment = (await db.execute(stmt)).scalar_one_or_none()
        if not payment:
            raise NotFoundException("PaymentTransaction", payment_id)
        return payment

    @classmethod
    async def list_payments(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        student_id: UUID | None = None,
        status: str | None = None,
        payment_mode: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[PaymentTransaction], int]:
        """List payments with filters."""
        stmt = (
            select(PaymentTransaction)
            .where(PaymentTransaction.tenant_id == tenant_id)
            .options(
                selectinload(PaymentTransaction.allocations).selectinload(PaymentAllocation.invoice),
                selectinload(PaymentTransaction.receipt),
            )
        )
        if student_id:
            stmt = stmt.where(PaymentTransaction.student_id == student_id)
        if status:
            stmt = stmt.where(PaymentTransaction.status == status)
        if payment_mode:
            stmt = stmt.where(PaymentTransaction.payment_mode == payment_mode.upper())

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(desc(PaymentTransaction.payment_date), desc(PaymentTransaction.created_at)).limit(limit).offset(offset)
        result = await db.execute(stmt)
        return list(result.scalars().all()), total

    # ---------------------------------------------------------------------------
    # Receipts
    # ---------------------------------------------------------------------------

    @classmethod
    async def get_receipt(
        cls, db: AsyncSession, tenant_id: UUID, receipt_id: UUID
    ) -> Receipt:
        """Fetch official receipt."""
        stmt = (
            select(Receipt)
            .where(and_(Receipt.id == receipt_id, Receipt.tenant_id == tenant_id))
            .options(
                selectinload(Receipt.payment).selectinload(PaymentTransaction.allocations).selectinload(PaymentAllocation.invoice)
            )
        )
        receipt = (await db.execute(stmt)).scalar_one_or_none()
        if not receipt:
            raise NotFoundException("Receipt", receipt_id)
        return receipt

    @classmethod
    async def list_receipts(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        student_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Receipt], int]:
        """List official receipts."""
        stmt = (
            select(Receipt)
            .where(Receipt.tenant_id == tenant_id)
            .join(Receipt.payment)
            .options(
                selectinload(Receipt.payment).selectinload(PaymentTransaction.allocations).selectinload(PaymentAllocation.invoice)
            )
        )
        if student_id:
            stmt = stmt.where(PaymentTransaction.student_id == student_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await db.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(desc(Receipt.issue_date), desc(Receipt.created_at)).limit(limit).offset(offset)
        result = await db.execute(stmt)
        return list(result.scalars().all()), total

    # ---------------------------------------------------------------------------
    # Scholarships & Concessions
    # ---------------------------------------------------------------------------

    @classmethod
    async def create_scholarship(
        cls, db: AsyncSession, tenant_id: UUID, data: ScholarshipCreate, current_user_id: UUID
    ) -> StudentFeeConcession:
        """Award a scholarship or fee waiver to a student."""
        s_stmt = select(Student).where(and_(Student.id == data.student_id, Student.tenant_id == tenant_id))
        if not (await db.execute(s_stmt)).scalar_one_or_none():
            raise NotFoundException("Student", data.student_id)

        concession = StudentFeeConcession(
            tenant_id=tenant_id,
            student_id=data.student_id,
            academic_year_id=data.academic_year_id,
            category_id=data.category_id,
            concession_name=data.concession_name.strip(),
            concession_type=data.concession_type.upper(),
            amount=Decimal(str(data.amount)),
            percentage=Decimal(str(data.percentage)) if data.percentage is not None else None,
            status="APPROVED",
            approved_by_user_id=current_user_id,
            remarks=data.remarks,
        )
        db.add(concession)
        await db.commit()
        await db.refresh(concession)

        await FinanceService._log_audit(
            db=db,
            tenant_id=tenant_id,
            actor_user_id=current_user_id,
            action="SCHOLARSHIP_APPROVED",
            resource_type="StudentFeeConcession",
            resource_id=concession.id,
            metadata={"name": concession.concession_name, "amount": str(concession.amount)},
        )
        return concession

    @classmethod
    async def list_scholarships(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        student_id: UUID | None = None,
        academic_year_id: UUID | None = None,
    ) -> list[StudentFeeConcession]:
        """List scholarships granted."""
        stmt = select(StudentFeeConcession).where(StudentFeeConcession.tenant_id == tenant_id)
        if student_id:
            stmt = stmt.where(StudentFeeConcession.student_id == student_id)
        if academic_year_id:
            stmt = stmt.where(StudentFeeConcession.academic_year_id == academic_year_id)

        stmt = stmt.order_by(desc(StudentFeeConcession.created_at))
        result = await db.execute(stmt)
        return list(result.scalars().all())

    # ---------------------------------------------------------------------------
    # Financial Adjustments (Debit/Credit Notes)
    # ---------------------------------------------------------------------------

    @classmethod
    async def create_adjustment(
        cls, db: AsyncSession, tenant_id: UUID, data: FinancialAdjustmentCreate, current_user_id: UUID
    ) -> FinancialAdjustment:
        """Create an approved financial adjustment modifying invoice balance without destroying history."""
        invoice = await cls.get_invoice(db, tenant_id, data.invoice_id)
        if invoice.status == "CANCELLED":
            raise ValidationException("Cannot adjust a cancelled invoice.")

        adj_type = data.adjustment_type.upper()
        if adj_type not in ("CREDIT", "DEBIT"):
            raise ValidationException("Adjustment type must be either 'CREDIT' or 'DEBIT'.")

        adj_amount = Decimal(str(data.amount))
        if adj_amount <= 0:
            raise ValidationException("Adjustment amount must be greater than zero.")

        # If CREDIT, ensure it doesn't reduce balance below zero
        if adj_type == "CREDIT" and adj_amount > invoice.balance_amount:
            raise ValidationException(
                f"Credit adjustment amount ({adj_amount}) cannot exceed current invoice balance ({invoice.balance_amount})."
            )

        adjustment = FinancialAdjustment(
            tenant_id=tenant_id,
            invoice_id=invoice.id,
            adjustment_type=adj_type,
            amount=adj_amount,
            reason=data.reason.strip(),
            requested_by_user_id=current_user_id,
            approved_by_user_id=current_user_id,
            status="APPROVED",
        )
        db.add(adjustment)

        # Modify invoice balance
        if adj_type == "CREDIT":
            invoice.adjustment_amount += adj_amount
            invoice.net_payable -= adj_amount
            invoice.balance_amount -= adj_amount
            if invoice.balance_amount == 0 and invoice.status != "DRAFT":
                invoice.status = "PAID"
        elif adj_type == "DEBIT":
            invoice.adjustment_amount -= adj_amount
            invoice.net_payable += adj_amount
            invoice.balance_amount += adj_amount
            if invoice.status == "PAID":
                invoice.status = "PARTIALLY_PAID"

        await db.commit()
        await db.refresh(adjustment)

        await FinanceService._log_audit(
            db=db,
            tenant_id=tenant_id,
            actor_user_id=current_user_id,
            action="ADJUSTMENT_APPROVED",
            resource_type="FinancialAdjustment",
            resource_id=adjustment.id,
            metadata={"invoice_id": str(invoice.id), "type": adj_type, "amount": str(adj_amount)},
        )
        return adjustment

    # ---------------------------------------------------------------------------
    # Refunds
    # ---------------------------------------------------------------------------

    @classmethod
    async def request_refund(
        cls, db: AsyncSession, tenant_id: UUID, data: RefundCreate, current_user_id: UUID
    ) -> RefundTransaction:
        """Initiate a controlled refund request."""
        payment = await cls.get_payment(db, tenant_id, data.payment_id)
        if payment.status not in ("SUCCESS", "PARTIALLY_REFUNDED"):
            raise ValidationException(f"Cannot refund a payment with status '{payment.status}'.")

        refund_amt = Decimal(str(data.refund_amount))
        if refund_amt <= 0:
            raise ValidationException("Refund amount must be greater than zero.")

        # Calculate previous refunds
        ref_stmt = select(func.coalesce(func.sum(RefundTransaction.refund_amount), Decimal("0.00"))).where(
            and_(
                RefundTransaction.payment_id == payment.id,
                RefundTransaction.status.in_(["REQUESTED", "APPROVED", "PROCESSED"]),
            )
        )
        already_refunded = (await db.execute(ref_stmt)).scalar() or Decimal("0.00")
        available_refundable = payment.amount - already_refunded

        if refund_amt > available_refundable:
            raise ValidationException(
                f"Requested refund amount ({refund_amt}) exceeds refundable limit ({available_refundable})."
            )

        refund = RefundTransaction(
            tenant_id=tenant_id,
            payment_id=payment.id,
            refund_amount=refund_amt,
            reason=data.reason.strip(),
            requested_by_user_id=current_user_id,
            status="REQUESTED",
            refund_mode=data.refund_mode,
            refund_reference=data.refund_reference,
        )
        db.add(refund)
        await db.commit()
        await db.refresh(refund)

        await FinanceService._log_audit(
            db=db,
            tenant_id=tenant_id,
            actor_user_id=current_user_id,
            action="REFUND_REQUESTED",
            resource_type="RefundTransaction",
            resource_id=refund.id,
            metadata={"payment_id": str(payment.id), "amount": str(refund_amt)},
        )
        return refund

    @classmethod
    async def approve_refund(
        cls, db: AsyncSession, tenant_id: UUID, refund_id: UUID, current_user_id: UUID
    ) -> RefundTransaction:
        """Authorize refund request."""
        stmt = select(RefundTransaction).where(
            and_(RefundTransaction.id == refund_id, RefundTransaction.tenant_id == tenant_id)
        )
        refund = (await db.execute(stmt)).scalar_one_or_none()
        if not refund:
            raise NotFoundException("RefundTransaction", refund_id)
        if refund.status != "REQUESTED":
            raise ValidationException(f"Cannot approve refund in '{refund.status}' state.")

        refund.status = "APPROVED"
        refund.approved_by_user_id = current_user_id
        await db.commit()
        await db.refresh(refund)

        await FinanceService._log_audit(
            db=db,
            tenant_id=tenant_id,
            actor_user_id=current_user_id,
            action="REFUND_APPROVED",
            resource_type="RefundTransaction",
            resource_id=refund.id,
            metadata={"amount": str(refund.refund_amount)},
        )
        return refund

    @classmethod
    async def process_refund(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        refund_id: UUID,
        refund_reference: str | None,
        current_user_id: UUID,
    ) -> RefundTransaction:
        """Disburse authorized refund and update payment status."""
        stmt = select(RefundTransaction).where(
            and_(RefundTransaction.id == refund_id, RefundTransaction.tenant_id == tenant_id)
        )
        refund = (await db.execute(stmt)).scalar_one_or_none()
        if not refund:
            raise NotFoundException("RefundTransaction", refund_id)
        if refund.status != "APPROVED":
            raise ValidationException(f"Cannot process refund in '{refund.status}' state. Must be APPROVED first.")

        refund.status = "PROCESSED"
        refund.processed_at = datetime.now(UTC)
        if refund_reference:
            refund.refund_reference = refund_reference.strip()

        # Update payment transaction status
        payment = await cls.get_payment(db, tenant_id, refund.payment_id)
        ref_stmt = select(func.coalesce(func.sum(RefundTransaction.refund_amount), Decimal("0.00"))).where(
            and_(
                RefundTransaction.payment_id == payment.id,
                RefundTransaction.status == "PROCESSED",
            )
        )
        total_processed = (await db.execute(ref_stmt)).scalar() or Decimal("0.00")
        total_processed += refund.refund_amount

        if total_processed >= payment.amount:
            payment.status = "REFUNDED"
        else:
            payment.status = "PARTIALLY_REFUNDED"

        await db.commit()
        await db.refresh(refund)

        await FinanceService._log_audit(
            db=db,
            tenant_id=tenant_id,
            actor_user_id=current_user_id,
            action="REFUND_PROCESSED",
            resource_type="RefundTransaction",
            resource_id=refund.id,
            metadata={"amount": str(refund.refund_amount), "payment_status": payment.status},
        )
        return refund

    @classmethod
    async def list_refunds(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        payment_id: UUID | None = None,
        status: str | None = None,
    ) -> list[RefundTransaction]:
        """List refund transactions."""
        stmt = select(RefundTransaction).where(RefundTransaction.tenant_id == tenant_id)
        if payment_id:
            stmt = stmt.where(RefundTransaction.payment_id == payment_id)
        if status:
            stmt = stmt.where(RefundTransaction.status == status)

        stmt = stmt.order_by(desc(RefundTransaction.created_at))
        result = await db.execute(stmt)
        return list(result.scalars().all())

    # ---------------------------------------------------------------------------
    # Financial Analytics & Student Summary
    # ---------------------------------------------------------------------------

    @classmethod
    async def get_dashboard_telemetry(
        cls, db: AsyncSession, tenant_id: UUID
    ) -> dict:
        """Aggregated operational financial telemetry."""
        today = date.today()

        # Total billed (issued / paid invoices)
        billed_stmt = select(func.coalesce(func.sum(Invoice.net_payable), Decimal("0.00"))).where(
            and_(Invoice.tenant_id == tenant_id, Invoice.status != "CANCELLED")
        )
        total_billed = (await db.execute(billed_stmt)).scalar() or Decimal("0.00")

        # Total collected
        collected_stmt = select(func.coalesce(func.sum(PaymentTransaction.amount), Decimal("0.00"))).where(
            and_(PaymentTransaction.tenant_id == tenant_id, PaymentTransaction.status.in_(["SUCCESS", "PARTIALLY_REFUNDED"]))
        )
        total_collected = (await db.execute(collected_stmt)).scalar() or Decimal("0.00")

        # Total outstanding
        outstanding_stmt = select(func.coalesce(func.sum(Invoice.balance_amount), Decimal("0.00"))).where(
            and_(Invoice.tenant_id == tenant_id, Invoice.status != "CANCELLED")
        )
        total_outstanding = (await db.execute(outstanding_stmt)).scalar() or Decimal("0.00")

        # Total overdue
        overdue_stmt = select(func.coalesce(func.sum(Invoice.balance_amount), Decimal("0.00"))).where(
            and_(
                Invoice.tenant_id == tenant_id,
                Invoice.due_date < today,
                Invoice.balance_amount > 0,
                Invoice.status.notin_(["PAID", "CANCELLED"]),
            )
        )
        total_overdue = (await db.execute(overdue_stmt)).scalar() or Decimal("0.00")

        # Active fee structures count
        fs_count_stmt = select(func.count(FeeStructure.id)).where(
            and_(FeeStructure.tenant_id == tenant_id, FeeStructure.status == "ACTIVE")
        )
        active_fs = (await db.execute(fs_count_stmt)).scalar() or 0

        # Pending payments / refunds
        ref_count_stmt = select(func.count(RefundTransaction.id)).where(
            and_(RefundTransaction.tenant_id == tenant_id, RefundTransaction.status == "REQUESTED")
        )
        pending_refunds = (await db.execute(ref_count_stmt)).scalar() or 0

        # Total scholarships granted
        schol_stmt = select(func.coalesce(func.sum(StudentFeeConcession.amount), Decimal("0.00"))).where(
            and_(StudentFeeConcession.tenant_id == tenant_id, StudentFeeConcession.status == "APPROVED")
        )
        total_schol = (await db.execute(schol_stmt)).scalar() or Decimal("0.00")

        # Recent 5 invoices & payments
        recent_inv, _ = await cls.list_invoices(db, tenant_id, limit=5)
        recent_pay, _ = await cls.list_payments(db, tenant_id, limit=5)

        return {
            "total_billed": total_billed,
            "total_collected": total_collected,
            "total_outstanding": total_outstanding,
            "total_overdue": total_overdue,
            "active_fee_structures_count": active_fs,
            "pending_payments_count": 0,
            "pending_refunds_count": pending_refunds,
            "total_scholarships_granted": total_schol,
            "recent_invoices": recent_inv,
            "recent_payments": recent_pay,
        }

    @classmethod
    async def get_student_statement(
        cls, db: AsyncSession, tenant_id: UUID, student_id: UUID
    ) -> dict:
        """Full financial ledger and statement of account for a student."""
        s_stmt = select(Student).where(and_(Student.id == student_id, Student.tenant_id == tenant_id))
        student = (await db.execute(s_stmt)).scalar_one_or_none()
        if not student:
            raise NotFoundException("Student", student_id)

        invoices, _ = await cls.list_invoices(db, tenant_id, student_id=student_id, limit=100)
        payments, _ = await cls.list_payments(db, tenant_id, student_id=student_id, limit=100)
        scholarships = await cls.list_scholarships(db, tenant_id, student_id=student_id)

        total_invoiced = sum((inv.net_payable for inv in invoices if inv.status != "CANCELLED"), Decimal("0.00"))
        total_paid = sum((pay.amount for pay in payments if pay.status in ("SUCCESS", "PARTIALLY_REFUNDED")), Decimal("0.00"))
        total_outstanding = sum((inv.balance_amount for inv in invoices if inv.status != "CANCELLED"), Decimal("0.00"))
        today = date.today()
        total_overdue = sum(
            (inv.balance_amount for inv in invoices if inv.due_date < today and inv.balance_amount > 0 and inv.status != "CANCELLED"),
            Decimal("0.00"),
        )
        total_concessions = sum((s.amount for s in scholarships if s.status == "APPROVED"), Decimal("0.00"))

        return {
            "student_id": student.id,
            "student_name": f"{student.first_name} {student.last_name}",
            "student_roll_number": student.roll_number,
            "student_admission_number": student.admission_number,
            "total_invoiced": total_invoiced,
            "total_paid": total_paid,
            "total_outstanding": total_outstanding,
            "total_overdue": total_overdue,
            "total_concessions": total_concessions,
            "invoices": invoices,
            "payments": payments,
            "scholarships": scholarships,
        }
