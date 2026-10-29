"""API router for Finance, Fees & Billing Engine."""

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import require_permission
from app.core.exceptions import ForbiddenException, PermissionDeniedException
from app.core.permissions import (
    ADJUSTMENTS_CREATE,
    FINANCE_MANAGE_FEE_STRUCTURES,
    FINANCE_READ,
    INVOICES_CANCEL,
    INVOICES_CREATE,
    INVOICES_ISSUE,
    INVOICES_READ,
    PAYMENTS_CREATE,
    PAYMENTS_READ,
    RECEIPTS_READ,
    REFUNDS_APPROVE,
    REFUNDS_CREATE,
    REFUNDS_PROCESS,
    SCHOLARSHIPS_CREATE,
    SCHOLARSHIPS_READ,
)
from app.models.core import AcademicYear, Program, Semester
from app.models.finance import (
    PaymentTransaction,
)
from app.models.people import StudentProfile as Student
from app.models.people import User
from app.schemas.common import ApiResponse
from app.schemas.finance import (
    FeeCategoryCreate,
    FeeCategoryResponse,
    FeeCategoryUpdate,
    FeeItemResponse,
    FeeStructureCreate,
    FeeStructureResponse,
    FinancialAdjustmentCreate,
    FinancialAdjustmentResponse,
    InvoiceCreate,
    InvoiceLineResponse,
    InvoiceResponse,
    PaymentAllocationResponse,
    PaymentCreate,
    PaymentResponse,
    ReceiptResponse,
    RefundCreate,
    RefundResponse,
    ScholarshipCreate,
    ScholarshipResponse,
    StudentFeeAssignmentCreate,
    StudentFeeAssignmentResponse,
    StudentFinancialSummary,
)
from app.services.finance_service import FinanceService

router = APIRouter(prefix="/finance", tags=["Finance & Billing"])


async def _resolve_student_id_for_user(db: AsyncSession, current_user: User) -> UUID | None:
    """Helper resolving student profile ID for logged in user."""
    stmt = select(Student.id).where(Student.user_id == current_user.id)
    return (await db.execute(stmt)).scalar_one_or_none()


# ---------------------------------------------------------------------------
# Fee Categories
# ---------------------------------------------------------------------------


@router.get("/fee-categories", response_model=ApiResponse[list[FeeCategoryResponse]])
async def list_fee_categories(
    is_active: bool | None = None,
    current_user: User = Depends(require_permission(FINANCE_READ)),
    db: AsyncSession = Depends(get_db_session),
):
    """List fee categories for the tenant."""
    categories = await FinanceService.list_categories(db, current_user.tenant_id, is_active)
    return ApiResponse(data=[FeeCategoryResponse.model_validate(c) for c in categories])


@router.post("/fee-categories", response_model=ApiResponse[FeeCategoryResponse], status_code=status.HTTP_201_CREATED)
async def create_fee_category(
    data: FeeCategoryCreate,
    current_user: User = Depends(require_permission(FINANCE_MANAGE_FEE_STRUCTURES)),
    db: AsyncSession = Depends(get_db_session),
):
    """Create a new institutional fee category."""
    category = await FinanceService.create_category(db, current_user.tenant_id, data, current_user.id)
    return ApiResponse(data=FeeCategoryResponse.model_validate(category))


@router.patch("/fee-categories/{category_id}", response_model=ApiResponse[FeeCategoryResponse])
async def update_fee_category(
    category_id: UUID,
    data: FeeCategoryUpdate,
    current_user: User = Depends(require_permission(FINANCE_MANAGE_FEE_STRUCTURES)),
    db: AsyncSession = Depends(get_db_session),
):
    """Update an existing fee category."""
    category = await FinanceService.update_category(db, current_user.tenant_id, category_id, data, current_user.id)
    return ApiResponse(data=FeeCategoryResponse.model_validate(category))


# ---------------------------------------------------------------------------
# Fee Structures
# ---------------------------------------------------------------------------


@router.get("/fee-structures", response_model=ApiResponse[list[FeeStructureResponse]])
async def list_fee_structures(
    program_id: UUID | None = None,
    academic_year_id: UUID | None = None,
    semester_id: UUID | None = None,
    status_filter: str | None = Query(None, alias="status"),
    current_user: User = Depends(require_permission(FINANCE_READ)),
    db: AsyncSession = Depends(get_db_session),
):
    """List fee structures with itemized heads."""
    structures = await FinanceService.list_fee_structures(
        db, current_user.tenant_id, program_id, academic_year_id, semester_id, status_filter
    )
    res_list: list[FeeStructureResponse] = []
    for s in structures:
        # Load aux names
        prog = (await db.execute(select(Program.name).where(Program.id == s.program_id))).scalar_one_or_none()
        ay = (await db.execute(select(AcademicYear.name).where(AcademicYear.id == s.academic_year_id))).scalar_one_or_none()
        sem = (await db.execute(select(Semester.name).where(Semester.id == s.semester_id))).scalar_one_or_none() if s.semester_id else None

        tot = sum((item.amount for item in s.items), Decimal("0.00"))
        items_res = [
            FeeItemResponse(
                id=item.id,
                fee_structure_id=item.fee_structure_id,
                category_id=item.category_id,
                category_name=None,
                name=item.name,
                amount=item.amount,
                is_optional=item.is_optional,
                sequence=item.sequence,
            )
            for item in sorted(s.items, key=lambda x: x.sequence)
        ]
        res_list.append(
            FeeStructureResponse(
                id=s.id,
                tenant_id=s.tenant_id,
                program_id=s.program_id,
                program_name=prog,
                academic_year_id=s.academic_year_id,
                academic_year_name=ay,
                semester_id=s.semester_id,
                semester_name=sem,
                batch_id=s.batch_id,
                quota_type=s.quota_type,
                name=s.name,
                status=s.status,
                version=s.version,
                total_amount=tot,
                items=items_res,
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
        )
    return ApiResponse(data=res_list)


@router.get("/fee-structures/{structure_id}", response_model=ApiResponse[FeeStructureResponse])
async def get_fee_structure(
    structure_id: UUID,
    current_user: User = Depends(require_permission(FINANCE_READ)),
    db: AsyncSession = Depends(get_db_session),
):
    """Get fee structure details."""
    s = await FinanceService.get_fee_structure(db, current_user.tenant_id, structure_id)
    prog = (await db.execute(select(Program.name).where(Program.id == s.program_id))).scalar_one_or_none()
    ay = (await db.execute(select(AcademicYear.name).where(AcademicYear.id == s.academic_year_id))).scalar_one_or_none()
    sem = (await db.execute(select(Semester.name).where(Semester.id == s.semester_id))).scalar_one_or_none() if s.semester_id else None
    tot = sum((item.amount for item in s.items), Decimal("0.00"))

    items_res = [
        FeeItemResponse(
            id=item.id,
            fee_structure_id=item.fee_structure_id,
            category_id=item.category_id,
            name=item.name,
            amount=item.amount,
            is_optional=item.is_optional,
            sequence=item.sequence,
        )
        for item in sorted(s.items, key=lambda x: x.sequence)
    ]
    return ApiResponse(
        data=FeeStructureResponse(
            id=s.id,
            tenant_id=s.tenant_id,
            program_id=s.program_id,
            program_name=prog,
            academic_year_id=s.academic_year_id,
            academic_year_name=ay,
            semester_id=s.semester_id,
            semester_name=sem,
            batch_id=s.batch_id,
            quota_type=s.quota_type,
            name=s.name,
            status=s.status,
            version=s.version,
            total_amount=tot,
            items=items_res,
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
    )


@router.post("/fee-structures", response_model=ApiResponse[FeeStructureResponse], status_code=status.HTTP_201_CREATED)
async def create_fee_structure(
    data: FeeStructureCreate,
    current_user: User = Depends(require_permission(FINANCE_MANAGE_FEE_STRUCTURES)),
    db: AsyncSession = Depends(get_db_session),
):
    """Create a new fee structure draft."""
    s = await FinanceService.create_fee_structure(db, current_user.tenant_id, data, current_user.id)
    return await get_fee_structure(s.id, current_user, db)


@router.post("/fee-structures/{structure_id}/approve", response_model=ApiResponse[FeeStructureResponse])
async def approve_fee_structure(
    structure_id: UUID,
    current_user: User = Depends(require_permission(FINANCE_MANAGE_FEE_STRUCTURES)),
    db: AsyncSession = Depends(get_db_session),
):
    """Approve a fee structure draft."""
    await FinanceService.approve_fee_structure(db, current_user.tenant_id, structure_id, current_user.id)
    return await get_fee_structure(structure_id, current_user, db)


@router.post("/fee-structures/{structure_id}/activate", response_model=ApiResponse[FeeStructureResponse])
async def activate_fee_structure(
    structure_id: UUID,
    current_user: User = Depends(require_permission(FINANCE_MANAGE_FEE_STRUCTURES)),
    db: AsyncSession = Depends(get_db_session),
):
    """Activate fee structure for billing."""
    await FinanceService.activate_fee_structure(db, current_user.tenant_id, structure_id, current_user.id)
    return await get_fee_structure(structure_id, current_user, db)


@router.post("/fee-structures/{structure_id}/retire", response_model=ApiResponse[FeeStructureResponse])
async def retire_fee_structure(
    structure_id: UUID,
    current_user: User = Depends(require_permission(FINANCE_MANAGE_FEE_STRUCTURES)),
    db: AsyncSession = Depends(get_db_session),
):
    """Retire fee structure from future billing."""
    await FinanceService.retire_fee_structure(db, current_user.tenant_id, structure_id, current_user.id)
    return await get_fee_structure(structure_id, current_user, db)


# ---------------------------------------------------------------------------
# Student Fee Assignments
# ---------------------------------------------------------------------------


@router.get("/students/{student_id}/fees", response_model=ApiResponse[list[StudentFeeAssignmentResponse]])
async def list_student_fees(
    student_id: UUID,
    current_user: User = Depends(require_permission(FINANCE_READ)),
    db: AsyncSession = Depends(get_db_session),
):
    """List fee structure assignments for a student."""
    # Privacy check for student users
    user_student_id = await _resolve_student_id_for_user(db, current_user)
    if user_student_id and user_student_id != student_id:
        raise ForbiddenException("Access restricted to own student fee profile.")

    assignments = await FinanceService.list_student_fee_assignments(db, current_user.tenant_id, student_id)
    res_list: list[StudentFeeAssignmentResponse] = []
    for a in assignments:
        tot = sum((item.amount for item in a.fee_structure.items), Decimal("0.00")) if a.fee_structure else Decimal("0.00")
        res_list.append(
            StudentFeeAssignmentResponse(
                id=a.id,
                tenant_id=a.tenant_id,
                student_id=a.student_id,
                fee_structure_id=a.fee_structure_id,
                fee_structure_name=a.fee_structure.name if a.fee_structure else None,
                academic_year_id=a.academic_year_id,
                semester_id=a.semester_id,
                status=a.status,
                assigned_date=a.assigned_date,
                remarks=a.remarks,
                total_amount=tot,
                created_at=a.created_at,
            )
        )
    return ApiResponse(data=res_list)


@router.post("/students/{student_id}/fees/assign", response_model=ApiResponse[StudentFeeAssignmentResponse], status_code=status.HTTP_201_CREATED)
async def assign_student_fee(
    student_id: UUID,
    data: StudentFeeAssignmentCreate,
    current_user: User = Depends(require_permission(FINANCE_MANAGE_FEE_STRUCTURES)),
    db: AsyncSession = Depends(get_db_session),
):
    """Assign an applicable fee structure to a student."""
    if data.student_id != student_id:
        data = StudentFeeAssignmentCreate(
            student_id=student_id,
            fee_structure_id=data.fee_structure_id,
            academic_year_id=data.academic_year_id,
            semester_id=data.semester_id,
            remarks=data.remarks,
        )
    assignment = await FinanceService.assign_student_fee(db, current_user.tenant_id, data, current_user.id)
    return ApiResponse(
        data=StudentFeeAssignmentResponse(
            id=assignment.id,
            tenant_id=assignment.tenant_id,
            student_id=assignment.student_id,
            fee_structure_id=assignment.fee_structure_id,
            fee_structure_name=assignment.fee_structure.name if assignment.fee_structure else None,
            academic_year_id=assignment.academic_year_id,
            semester_id=assignment.semester_id,
            status=assignment.status,
            assigned_date=assignment.assigned_date,
            remarks=assignment.remarks,
            total_amount=Decimal("0.00"),
            created_at=assignment.created_at,
        )
    )


# ---------------------------------------------------------------------------
# Invoices
# ---------------------------------------------------------------------------


def _map_invoice_response(inv) -> InvoiceResponse:
    lines = [
        InvoiceLineResponse(
            id=item.id,
            invoice_id=item.invoice_id,
            category_id=item.category_id,
            description=item.description,
            amount=item.amount,
            waived_amount=item.waived_amount,
        )
        for item in inv.items
    ]
    return InvoiceResponse(
        id=inv.id,
        tenant_id=inv.tenant_id,
        student_id=inv.student_id,
        academic_year_id=inv.academic_year_id,
        semester_id=inv.semester_id,
        invoice_number=inv.invoice_number,
        issue_date=inv.issue_date,
        due_date=inv.due_date,
        currency=inv.currency,
        gross_amount=inv.gross_amount,
        concession_amount=inv.concession_amount,
        adjustment_amount=inv.adjustment_amount,
        net_payable=inv.net_payable,
        paid_amount=inv.paid_amount,
        balance_amount=inv.balance_amount,
        status=inv.status,
        remarks=inv.remarks,
        is_overdue=inv.status == "OVERDUE",
        items=lines,
        created_at=inv.created_at,
        updated_at=inv.updated_at,
    )


@router.get("/invoices", response_model=ApiResponse[list[InvoiceResponse]])
async def list_invoices(
    student_id: UUID | None = None,
    academic_year_id: UUID | None = None,
    semester_id: UUID | None = None,
    status_filter: str | None = Query(None, alias="status"),
    is_overdue: bool | None = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(require_permission(INVOICES_READ)),
    db: AsyncSession = Depends(get_db_session),
):
    """List invoices with filtering and privacy gating."""
    # Student user privacy enforcement
    user_student_id = await _resolve_student_id_for_user(db, current_user)
    if user_student_id:
        student_id = user_student_id

    invoices, total = await FinanceService.list_invoices(
        db,
        current_user.tenant_id,
        student_id=student_id,
        academic_year_id=academic_year_id,
        semester_id=semester_id,
        status=status_filter,
        is_overdue=is_overdue,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(data=[_map_invoice_response(inv) for inv in invoices], metadata={"total": total})


@router.get("/invoices/{invoice_id}", response_model=ApiResponse[InvoiceResponse])
async def get_invoice(
    invoice_id: UUID,
    current_user: User = Depends(require_permission(INVOICES_READ)),
    db: AsyncSession = Depends(get_db_session),
):
    """Get invoice details with itemized lines."""
    inv = await FinanceService.get_invoice(db, current_user.tenant_id, invoice_id)

    # Privacy enforcement
    user_student_id = await _resolve_student_id_for_user(db, current_user)
    if user_student_id and user_student_id != inv.student_id:
        raise PermissionDeniedException("Access restricted to own invoice records.")

    return ApiResponse(data=_map_invoice_response(inv))


@router.post("/invoices", response_model=ApiResponse[InvoiceResponse], status_code=status.HTTP_201_CREATED)
async def create_invoice(
    data: InvoiceCreate,
    current_user: User = Depends(require_permission(INVOICES_CREATE)),
    db: AsyncSession = Depends(get_db_session),
):
    """Create a new billing invoice."""
    inv = await FinanceService.create_invoice(db, current_user.tenant_id, data, current_user.id)
    return ApiResponse(data=_map_invoice_response(inv))


@router.post("/invoices/{invoice_id}/issue", response_model=ApiResponse[InvoiceResponse])
async def issue_invoice(
    invoice_id: UUID,
    current_user: User = Depends(require_permission(INVOICES_ISSUE)),
    db: AsyncSession = Depends(get_db_session),
):
    """Issue a draft invoice, formally committing billing liability."""
    inv = await FinanceService.issue_invoice(db, current_user.tenant_id, invoice_id, current_user.id)
    return ApiResponse(data=_map_invoice_response(inv))


@router.post("/invoices/{invoice_id}/cancel", response_model=ApiResponse[InvoiceResponse])
async def cancel_invoice(
    invoice_id: UUID,
    current_user: User = Depends(require_permission(INVOICES_CANCEL)),
    db: AsyncSession = Depends(get_db_session),
):
    """Cancel an unpaid invoice without balance corruption."""
    inv = await FinanceService.cancel_invoice(db, current_user.tenant_id, invoice_id, current_user.id)
    return ApiResponse(data=_map_invoice_response(inv))


# ---------------------------------------------------------------------------
# Payments & Allocations
# ---------------------------------------------------------------------------


def _map_payment_response(p: PaymentTransaction) -> PaymentResponse:
    allocations = [
        PaymentAllocationResponse(
            id=a.id,
            payment_id=a.payment_id,
            invoice_id=a.invoice_id,
            invoice_number=a.invoice.invoice_number if a.invoice else None,
            allocated_amount=a.allocated_amount,
            allocated_at=a.allocated_at,
        )
        for a in p.allocations
    ]
    return PaymentResponse(
        id=p.id,
        tenant_id=p.tenant_id,
        student_id=p.student_id,
        payment_number=p.payment_number,
        transaction_reference=p.transaction_reference,
        payment_mode=p.payment_mode,
        gateway_provider=p.gateway_provider,
        gateway_transaction_id=p.gateway_transaction_id,
        payment_date=p.payment_date,
        amount=p.amount,
        currency=p.currency,
        status=p.status,
        received_by_user_id=p.received_by_user_id,
        remarks=p.remarks,
        allocations=allocations,
        receipt_number=p.receipt.receipt_number if p.receipt else None,
        receipt_id=p.receipt.id if p.receipt else None,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


@router.get("/payments", response_model=ApiResponse[list[PaymentResponse]])
async def list_payments(
    student_id: UUID | None = None,
    status_filter: str | None = Query(None, alias="status"),
    payment_mode: str | None = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(require_permission(PAYMENTS_READ)),
    db: AsyncSession = Depends(get_db_session),
):
    """List payments with filtering and privacy checks."""
    user_student_id = await _resolve_student_id_for_user(db, current_user)
    if user_student_id:
        student_id = user_student_id

    payments, total = await FinanceService.list_payments(
        db,
        current_user.tenant_id,
        student_id=student_id,
        status=status_filter,
        payment_mode=payment_mode,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(data=[_map_payment_response(p) for p in payments], metadata={"total": total})


@router.get("/payments/{payment_id}", response_model=ApiResponse[PaymentResponse])
async def get_payment(
    payment_id: UUID,
    current_user: User = Depends(require_permission(PAYMENTS_READ)),
    db: AsyncSession = Depends(get_db_session),
):
    """Get payment details."""
    p = await FinanceService.get_payment(db, current_user.tenant_id, payment_id)

    user_student_id = await _resolve_student_id_for_user(db, current_user)
    if user_student_id and user_student_id != p.student_id:
        raise PermissionDeniedException("Access restricted to own payment records.")

    return ApiResponse(data=_map_payment_response(p))


@router.post("/payments", response_model=ApiResponse[PaymentResponse], status_code=status.HTTP_201_CREATED)
async def record_payment(
    data: PaymentCreate,
    current_user: User = Depends(require_permission(PAYMENTS_CREATE)),
    db: AsyncSession = Depends(get_db_session),
):
    """Record an inward student payment transaction and allocate to invoice(s)."""
    p = await FinanceService.record_payment(db, current_user.tenant_id, data, current_user.id)
    return ApiResponse(data=_map_payment_response(p))


# ---------------------------------------------------------------------------
# Receipts
# ---------------------------------------------------------------------------


@router.get("/receipts", response_model=ApiResponse[list[ReceiptResponse]])
async def list_receipts(
    student_id: UUID | None = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(require_permission(RECEIPTS_READ)),
    db: AsyncSession = Depends(get_db_session),
):
    """List official payment receipts."""
    user_student_id = await _resolve_student_id_for_user(db, current_user)
    if user_student_id:
        student_id = user_student_id

    receipts, total = await FinanceService.list_receipts(
        db, current_user.tenant_id, student_id=student_id, limit=limit, offset=offset
    )

    res_list: list[ReceiptResponse] = []
    for r in receipts:
        inv_numbers = [
            a.invoice.invoice_number for a in r.payment.allocations if a.invoice and a.invoice.invoice_number
        ]
        res_list.append(
            ReceiptResponse(
                id=r.id,
                tenant_id=r.tenant_id,
                payment_id=r.payment_id,
                payment_number=r.payment.payment_number,
                receipt_number=r.receipt_number,
                student_id=r.payment.student_id,
                amount=r.payment.amount,
                currency=r.payment.currency,
                payment_mode=r.payment.payment_mode,
                transaction_reference=r.payment.transaction_reference,
                issue_date=r.issue_date,
                is_cancelled=r.is_cancelled,
                invoice_numbers=inv_numbers,
                created_at=r.created_at,
            )
        )
    return ApiResponse(data=res_list, metadata={"total": total})


@router.get("/receipts/{receipt_id}", response_model=ApiResponse[ReceiptResponse])
async def get_receipt(
    receipt_id: UUID,
    current_user: User = Depends(require_permission(RECEIPTS_READ)),
    db: AsyncSession = Depends(get_db_session),
):
    """Get official payment receipt."""
    r = await FinanceService.get_receipt(db, current_user.tenant_id, receipt_id)

    user_student_id = await _resolve_student_id_for_user(db, current_user)
    if user_student_id and user_student_id != r.payment.student_id:
        raise PermissionDeniedException("Access restricted to own receipt records.")

    inv_numbers = [
        a.invoice.invoice_number for a in r.payment.allocations if a.invoice and a.invoice.invoice_number
    ]
    return ApiResponse(
        data=ReceiptResponse(
            id=r.id,
            tenant_id=r.tenant_id,
            payment_id=r.payment_id,
            payment_number=r.payment.payment_number,
            receipt_number=r.receipt_number,
            student_id=r.payment.student_id,
            amount=r.payment.amount,
            currency=r.payment.currency,
            payment_mode=r.payment.payment_mode,
            transaction_reference=r.payment.transaction_reference,
            issue_date=r.issue_date,
            is_cancelled=r.is_cancelled,
            invoice_numbers=inv_numbers,
            created_at=r.created_at,
        )
    )


# ---------------------------------------------------------------------------
# Scholarships & Concessions
# ---------------------------------------------------------------------------


@router.get("/scholarships", response_model=ApiResponse[list[ScholarshipResponse]])
async def list_scholarships(
    student_id: UUID | None = None,
    academic_year_id: UUID | None = None,
    current_user: User = Depends(require_permission(SCHOLARSHIPS_READ)),
    db: AsyncSession = Depends(get_db_session),
):
    """List granted scholarships and fee waivers."""
    user_student_id = await _resolve_student_id_for_user(db, current_user)
    if user_student_id:
        student_id = user_student_id

    items = await FinanceService.list_scholarships(db, current_user.tenant_id, student_id, academic_year_id)
    return ApiResponse(
        data=[
            ScholarshipResponse(
                id=c.id,
                tenant_id=c.tenant_id,
                student_id=c.student_id,
                academic_year_id=c.academic_year_id,
                category_id=c.category_id,
                concession_name=c.concession_name,
                concession_type=c.concession_type,
                amount=c.amount,
                percentage=c.percentage,
                status=c.status,
                approved_by_user_id=c.approved_by_user_id,
                remarks=c.remarks,
                created_at=c.created_at,
            )
            for c in items
        ]
    )


@router.post("/scholarships", response_model=ApiResponse[ScholarshipResponse], status_code=status.HTTP_201_CREATED)
async def create_scholarship(
    data: ScholarshipCreate,
    current_user: User = Depends(require_permission(SCHOLARSHIPS_CREATE)),
    db: AsyncSession = Depends(get_db_session),
):
    """Award a scholarship or fee waiver to a student."""
    c = await FinanceService.create_scholarship(db, current_user.tenant_id, data, current_user.id)
    return ApiResponse(
        data=ScholarshipResponse(
            id=c.id,
            tenant_id=c.tenant_id,
            student_id=c.student_id,
            academic_year_id=c.academic_year_id,
            category_id=c.category_id,
            concession_name=c.concession_name,
            concession_type=c.concession_type,
            amount=c.amount,
            percentage=c.percentage,
            status=c.status,
            approved_by_user_id=c.approved_by_user_id,
            remarks=c.remarks,
            created_at=c.created_at,
        )
    )


# ---------------------------------------------------------------------------
# Financial Adjustments (Debit/Credit Notes)
# ---------------------------------------------------------------------------


@router.post("/adjustments", response_model=ApiResponse[FinancialAdjustmentResponse], status_code=status.HTTP_201_CREATED)
async def create_adjustment(
    data: FinancialAdjustmentCreate,
    current_user: User = Depends(require_permission(ADJUSTMENTS_CREATE)),
    db: AsyncSession = Depends(get_db_session),
):
    """Create a credit or debit note adjustment modifying invoice balance without destroying history."""
    adj = await FinanceService.create_adjustment(db, current_user.tenant_id, data, current_user.id)
    return ApiResponse(
        data=FinancialAdjustmentResponse(
            id=adj.id,
            tenant_id=adj.tenant_id,
            invoice_id=adj.invoice_id,
            adjustment_type=adj.adjustment_type,
            amount=adj.amount,
            reason=adj.reason,
            status=adj.status,
            requested_by_user_id=adj.requested_by_user_id,
            approved_by_user_id=adj.approved_by_user_id,
            created_at=adj.created_at,
        )
    )


# ---------------------------------------------------------------------------
# Refunds
# ---------------------------------------------------------------------------


@router.get("/refunds", response_model=ApiResponse[list[RefundResponse]])
async def list_refunds(
    payment_id: UUID | None = None,
    status_filter: str | None = Query(None, alias="status"),
    current_user: User = Depends(require_permission(FINANCE_READ)),
    db: AsyncSession = Depends(get_db_session),
):
    """List refund transactions."""
    refunds = await FinanceService.list_refunds(db, current_user.tenant_id, payment_id, status_filter)
    return ApiResponse(
        data=[
            RefundResponse(
                id=r.id,
                tenant_id=r.tenant_id,
                payment_id=r.payment_id,
                refund_amount=r.refund_amount,
                reason=r.reason,
                status=r.status,
                refund_mode=r.refund_mode,
                refund_reference=r.refund_reference,
                requested_by_user_id=r.requested_by_user_id,
                approved_by_user_id=r.approved_by_user_id,
                processed_at=r.processed_at,
                created_at=r.created_at,
            )
            for r in refunds
        ]
    )


@router.post("/refunds", response_model=ApiResponse[RefundResponse], status_code=status.HTTP_201_CREATED)
async def request_refund(
    data: RefundCreate,
    current_user: User = Depends(require_permission(REFUNDS_CREATE)),
    db: AsyncSession = Depends(get_db_session),
):
    """Initiate a fee refund request."""
    r = await FinanceService.request_refund(db, current_user.tenant_id, data, current_user.id)
    return ApiResponse(
        data=RefundResponse(
            id=r.id,
            tenant_id=r.tenant_id,
            payment_id=r.payment_id,
            refund_amount=r.refund_amount,
            reason=r.reason,
            status=r.status,
            refund_mode=r.refund_mode,
            refund_reference=r.refund_reference,
            requested_by_user_id=r.requested_by_user_id,
            approved_by_user_id=r.approved_by_user_id,
            processed_at=r.processed_at,
            created_at=r.created_at,
        )
    )


@router.post("/refunds/{refund_id}/approve", response_model=ApiResponse[RefundResponse])
async def approve_refund(
    refund_id: UUID,
    current_user: User = Depends(require_permission(REFUNDS_APPROVE)),
    db: AsyncSession = Depends(get_db_session),
):
    """Authorize a fee refund request."""
    r = await FinanceService.approve_refund(db, current_user.tenant_id, refund_id, current_user.id)
    return ApiResponse(
        data=RefundResponse(
            id=r.id,
            tenant_id=r.tenant_id,
            payment_id=r.payment_id,
            refund_amount=r.refund_amount,
            reason=r.reason,
            status=r.status,
            refund_mode=r.refund_mode,
            refund_reference=r.refund_reference,
            requested_by_user_id=r.requested_by_user_id,
            approved_by_user_id=r.approved_by_user_id,
            processed_at=r.processed_at,
            created_at=r.created_at,
        )
    )


@router.post("/refunds/{refund_id}/process", response_model=ApiResponse[RefundResponse])
async def process_refund(
    refund_id: UUID,
    refund_reference: str | None = None,
    current_user: User = Depends(require_permission(REFUNDS_PROCESS)),
    db: AsyncSession = Depends(get_db_session),
):
    """Process and disburse an authorized refund."""
    r = await FinanceService.process_refund(
        db, current_user.tenant_id, refund_id, refund_reference, current_user.id
    )
    return ApiResponse(
        data=RefundResponse(
            id=r.id,
            tenant_id=r.tenant_id,
            payment_id=r.payment_id,
            refund_amount=r.refund_amount,
            reason=r.reason,
            status=r.status,
            refund_mode=r.refund_mode,
            refund_reference=r.refund_reference,
            requested_by_user_id=r.requested_by_user_id,
            approved_by_user_id=r.approved_by_user_id,
            processed_at=r.processed_at,
            created_at=r.created_at,
        )
    )


# ---------------------------------------------------------------------------
# Telemetry & Student Statement
# ---------------------------------------------------------------------------


@router.get("/dashboard")
async def get_finance_dashboard(
    current_user: User = Depends(require_permission(FINANCE_READ)),
    db: AsyncSession = Depends(get_db_session),
):
    """Operational financial telemetry."""
    telemetry = await FinanceService.get_dashboard_telemetry(db, current_user.tenant_id)
    # Serialize responses
    return ApiResponse(
        data={
            "total_billed": telemetry["total_billed"],
            "total_collected": telemetry["total_collected"],
            "total_outstanding": telemetry["total_outstanding"],
            "total_overdue": telemetry["total_overdue"],
            "active_fee_structures_count": telemetry["active_fee_structures_count"],
            "pending_payments_count": telemetry["pending_payments_count"],
            "pending_refunds_count": telemetry["pending_refunds_count"],
            "total_scholarships_granted": telemetry["total_scholarships_granted"],
            "recent_invoices": [_map_invoice_response(inv) for inv in telemetry["recent_invoices"]],
            "recent_payments": [_map_payment_response(p) for p in telemetry["recent_payments"]],
        }
    )


@router.get("/students/{student_id}/statement", response_model=ApiResponse[StudentFinancialSummary])
async def get_student_statement(
    student_id: UUID,
    current_user: User = Depends(require_permission(FINANCE_READ)),
    db: AsyncSession = Depends(get_db_session),
):
    """Full financial ledger and statement of account for a student."""
    user_student_id = await _resolve_student_id_for_user(db, current_user)
    if user_student_id and user_student_id != student_id:
        raise PermissionDeniedException("Access restricted to own financial statement.")

    summary = await FinanceService.get_student_statement(db, current_user.tenant_id, student_id)
    return ApiResponse(
        data=StudentFinancialSummary(
            student_id=summary["student_id"],
            student_name=summary["student_name"],
            student_roll_number=summary["student_roll_number"],
            student_admission_number=summary["student_admission_number"],
            total_invoiced=summary["total_invoiced"],
            total_paid=summary["total_paid"],
            total_outstanding=summary["total_outstanding"],
            total_overdue=summary["total_overdue"],
            total_concessions=summary["total_concessions"],
            invoices=[_map_invoice_response(inv) for inv in summary["invoices"]],
            payments=[_map_payment_response(p) for p in summary["payments"]],
            scholarships=[
                ScholarshipResponse(
                    id=c.id,
                    tenant_id=c.tenant_id,
                    student_id=c.student_id,
                    academic_year_id=c.academic_year_id,
                    concession_name=c.concession_name,
                    concession_type=c.concession_type,
                    amount=c.amount,
                    percentage=c.percentage,
                    status=c.status,
                    created_at=c.created_at,
                )
                for c in summary["scholarships"]
            ],
        )
    )
