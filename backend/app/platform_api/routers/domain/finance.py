"""External Consumable Finance API with Idempotency Guarantees (Platform v1).

Enforces:
- Scope: finance.read (invoices) and finance.write (payments)
- Underlying PBAC: finance:invoices:read and finance:payments:create
- Mandatory Idempotency-Key header for POST /payments
- Atomic payment record and invoice balance reduction
- Usage metering telemetry
"""

import secrets
import time
from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.exceptions import NotFoundException, ValidationException
from app.models.finance import Invoice, PaymentAllocation, PaymentTransaction
from app.platform_api.dependencies import (
    ApiConsumerContext,
    require_api_consumer,
)
from app.platform_api.idempotency import idempotency_engine
from app.platform_api.schemas import (
    PublicInvoiceResponse,
    PublicPaymentCreate,
    PublicPaymentResponse,
)
from app.platform_api.scopes import SCOPE_FINANCE_READ, SCOPE_FINANCE_WRITE
from app.platform_api.usage import usage_metering_service

router = APIRouter(prefix="/platform/v1/finance", tags=["Platform API - Finance"])


@router.get("/invoices", response_model=list[PublicInvoiceResponse])
async def list_invoices(
    request: Request,
    consumer: Annotated[
        ApiConsumerContext,
        Depends(
            require_api_consumer(
                required_scope=SCOPE_FINANCE_READ, required_permission="finance:invoices:read"
            )
        ),
    ],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    student_id: UUID | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
) -> list[PublicInvoiceResponse]:
    """Retrieve student fee invoices and current balances due."""
    start_time = time.perf_counter()

    stmt = select(Invoice).where(Invoice.tenant_id == consumer.tenant_id).limit(limit)
    if student_id:
        stmt = stmt.where(Invoice.student_id == student_id)
    if status:
        stmt = stmt.where(Invoice.status == status.upper())

    res = await db.execute(stmt)
    invoices = res.scalars().all()

    items = [
        PublicInvoiceResponse(
            id=inv.id,
            invoice_number=inv.invoice_number,
            student_id=inv.student_id,
            total_amount=float(inv.net_payable),
            balance_due=float(inv.balance_amount),
            due_date=str(inv.due_date),
            status=inv.status,
        )
        for inv in invoices
    ]

    latency_ms = (time.perf_counter() - start_time) * 1000
    await usage_metering_service.record_usage(
        db=db,
        tenant_id=consumer.tenant_id,
        application_id=consumer.application_id,
        credential_id=consumer.credential_id,
        method="GET",
        path="/api/v1/platform/v1/finance/invoices",
        version="v1",
        status_code=200,
        latency_ms=latency_ms,
        correlation_id=request.headers.get("X-Correlation-ID"),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )

    return items


@router.post("/payments", response_model=PublicPaymentResponse, status_code=status.HTTP_201_CREATED)
async def record_payment(
    body: PublicPaymentCreate,
    request: Request,
    consumer: Annotated[
        ApiConsumerContext,
        Depends(
            require_api_consumer(
                required_scope=SCOPE_FINANCE_WRITE, required_permission="finance:payments:record"
            )
        ),
    ],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    x_idempotency_key: Annotated[str | None, Header(alias="X-Idempotency-Key")] = None,
) -> PublicPaymentResponse:
    """Record a payment transaction with mandatory idempotency enforcement."""
    effective_idem_key = idempotency_key or x_idempotency_key
    if not effective_idem_key or not effective_idem_key.strip():
        raise ValidationException("Header 'Idempotency-Key' is mandatory for payment mutations.")

    effective_idem_key = effective_idem_key.strip()
    endpoint = "/api/v1/platform/v1/finance/payments"

    # 1. Idempotency Check & Lock
    is_cached, cached_code, cached_body = await idempotency_engine.prepare_idempotent_request(
        db=db,
        tenant_id=consumer.tenant_id,
        application_id=consumer.application_id,
        idempotency_key=effective_idem_key,
        endpoint=endpoint,
        payload=body.model_dump(),
    )
    if is_cached and cached_body:
        return PublicPaymentResponse(**cached_body)

    start_time = time.perf_counter()

    # 2. Verify Invoice
    inv_stmt = select(Invoice).where(
        Invoice.tenant_id == consumer.tenant_id,
        Invoice.id == body.invoice_id,
    )
    inv_res = await db.execute(inv_stmt)
    invoice = inv_res.scalar_one_or_none()
    if not invoice:
        raise NotFoundException("Invoice", body.invoice_id)

    # 3. Create Payment Transaction
    payment_amt = Decimal(str(body.amount))
    now = datetime.now(UTC)
    pay_number = f"PAY-{now.year}-{secrets.token_hex(4).upper()}"

    payment = PaymentTransaction(
        tenant_id=consumer.tenant_id,
        student_id=invoice.student_id,
        payment_number=pay_number,
        transaction_reference=body.transaction_reference,
        payment_mode=body.payment_method.upper(),
        payment_date=now,
        amount=payment_amt,
        currency="INR",
        status="SUCCESS",
        received_by_user_id=consumer.owner.id,
        remarks=body.notes or "Processed via Enterprise API Platform",
    )
    db.add(payment)
    await db.flush()

    # Create Allocation
    allocation = PaymentAllocation(
        payment_id=payment.id,
        invoice_id=invoice.id,
        allocated_amount=payment_amt,
        allocated_at=now,
    )
    db.add(allocation)

    # Update Invoice Balance
    invoice.paid_amount += payment_amt
    invoice.balance_amount = max(Decimal("0.00"), invoice.balance_amount - payment_amt)
    if invoice.balance_amount == Decimal("0.00"):
        invoice.status = "PAID"
    else:
        invoice.status = "PARTIALLY_PAID"

    await db.flush()

    response_data = PublicPaymentResponse(
        id=payment.id,
        receipt_number=pay_number,
        invoice_id=invoice.id,
        amount=float(payment_amt),
        status="SUCCESS",
        transaction_reference=body.transaction_reference,
        transaction_date=now,
    )

    # 4. Complete Idempotency Record
    await idempotency_engine.complete_idempotent_request(
        db=db,
        tenant_id=consumer.tenant_id,
        application_id=consumer.application_id,
        idempotency_key=effective_idem_key,
        status_code=201,
        response_body=response_data.model_dump(),
    )

    latency_ms = (time.perf_counter() - start_time) * 1000
    await usage_metering_service.record_usage(
        db=db,
        tenant_id=consumer.tenant_id,
        application_id=consumer.application_id,
        credential_id=consumer.credential_id,
        method="POST",
        path=endpoint,
        version="v1",
        status_code=201,
        latency_ms=latency_ms,
        correlation_id=request.headers.get("X-Correlation-ID"),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )

    return response_data
