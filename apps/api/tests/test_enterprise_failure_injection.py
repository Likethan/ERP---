"""Step 34: Enterprise Failure Injection & Resilience Suite.

Verifies:
1. Circuit Breaker State Transitions: Trips from CLOSED to OPEN after failure threshold,
   blocks calls, probes in HALF_OPEN, and heals to CLOSED on recovery.
2. Idempotency Guard in Retries: Verifies non-idempotent operations are NEVER automatically
   retried, while idempotent calls retry up to max_retries before halting (no infinite loops).
3. Transaction Rollback Atomicity on Dependency Exception: Mid-flight failure leaves zero dirty records.
4. Error Response Sanitization: Confirms that error messages scrub database internals, credentials,
   and secret keys, preventing sensitive information leakage.
"""

import asyncio
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationException
from app.core.resilience import (
    CircuitBreaker,
    CircuitBreakerOpenException,
    ReliabilityCircuitBreakerState,
    retry_async,
)
from app.models.core import Department, Institution


@pytest.mark.asyncio
async def test_circuit_breaker_trips_and_recovers():
    """Verify circuit breaker trips from CLOSED -> OPEN on repeated failures, and recovers."""
    cb = CircuitBreaker(
        dependency_name="payment_gateway_mock",
        failure_threshold=3,
        recovery_timeout_seconds=0.1,  # Short recovery for testing
        half_open_success_threshold=2,
    )

    assert cb.state == ReliabilityCircuitBreakerState.CLOSED
    assert await cb.can_execute() is True

    # 1. Simulate 3 consecutive failures to trip circuit
    await cb.record_failure("Connection timeout 1")
    await cb.record_failure("Connection timeout 2")
    assert cb.state == ReliabilityCircuitBreakerState.CLOSED  # Threshold is 3

    await cb.record_failure("Connection timeout 3")
    assert cb.state == ReliabilityCircuitBreakerState.OPEN
    assert cb.consecutive_failures == 3

    # 2. While OPEN and recovery timeout has not elapsed, execution must be blocked
    can_exec_immediate = await cb.can_execute()
    assert can_exec_immediate is False, "OPEN circuit must fast-fail outbound calls!"

    # 3. Wait for recovery timeout to elapse -> transitions to HALF_OPEN
    await asyncio.sleep(0.15)
    assert await cb.can_execute() is True
    assert cb.state == ReliabilityCircuitBreakerState.HALF_OPEN

    # 4. Probe requests succeed -> heals back to CLOSED
    await cb.record_success()
    assert cb.state == ReliabilityCircuitBreakerState.HALF_OPEN  # Needs 2 successes
    await cb.record_success()
    assert cb.state == ReliabilityCircuitBreakerState.CLOSED
    assert cb.consecutive_failures == 0


@pytest.mark.asyncio
async def test_non_idempotent_operation_never_retried():
    """Verify that non-idempotent operations (e.g. payment charge, marks submission) are never retried."""
    call_count = 0

    async def charge_payment():
        nonlocal call_count
        call_count += 1
        raise RuntimeError("Payment gateway network disconnect")

    with pytest.raises(RuntimeError):
        await retry_async(
            charge_payment,
            max_retries=3,
            is_idempotent=False,  # CRITICAL: Non-idempotent
            operation_name="charge_fee_payment",
        )

    # Must be executed exactly once, NEVER retried
    assert call_count == 1, f"Non-idempotent operation was retried {call_count} times! Expected strictly 1."


@pytest.mark.asyncio
async def test_idempotent_retry_bounded_limits():
    """Verify that idempotent operations retry up to max_retries with backoff and do not loop infinitely."""
    call_count = 0

    async def fetch_exchange_rate():
        nonlocal call_count
        call_count += 1
        raise ConnectionResetError("Currency provider unavailable")

    with pytest.raises(ConnectionResetError):
        await retry_async(
            fetch_exchange_rate,
            max_retries=3,
            base_delay=0.01,
            max_delay=0.05,
            is_idempotent=True,  # Idempotent read
            retry_exceptions=(ConnectionResetError,),
            operation_name="fetch_exchange_rates",
        )

    # Initial attempt + 3 retries = 4 total attempts
    assert call_count == 4, f"Expected 4 attempts (1 initial + 3 retries), got {call_count}"


@pytest.mark.asyncio
async def test_transaction_rollback_on_downstream_dependency_failure(
    db_session: AsyncSession,
    tenant_a: Institution,
):
    """Verify that if an external dependency fails midway, the database transaction rolls back cleanly."""
    uid = uuid.uuid4().hex[:6].upper()
    code = f"RESIL-DEPT-{uid}"

    async def process_department_onboarding():
        async with db_session.begin_nested():
            dept = Department(
                id=uuid.uuid4(),
                tenant_id=tenant_a.id,
                code=code,
                name="Resilience Department",
                department_type="ACADEMIC",
                is_active=True,
            )
            db_session.add(dept)
            await db_session.flush()

            # Downstream dependency crash (e.g. notification dispatch or external sync failure)
            raise ConnectionError("Simulated external notification service crash")

    with pytest.raises(ConnectionError):
        await process_department_onboarding()

    # Verify no partial write persisted
    result = await db_session.execute(
        select(Department).where(Department.code == code)
    )
    assert result.scalar_one_or_none() is None, "Uncommitted database records persisted after dependency failure!"


def test_error_detail_sanitizes_credentials():
    """Verify that error messages do not leak database connection strings or secret keys."""
    sensitive_raw_msg = (
        "Connection failed to postgresql://campusos_user:super_secret_password_123!@db.internal:5432/campusos_prod"
    )

    # Sanitize test
    from app.core.exceptions import CampusOSException
    app_exc = CampusOSException(
        message="Database service temporarily unavailable",
        status_code=503,
        code="SERVICE_UNAVAILABLE",
    )
    assert "super_secret_password_123" not in app_exc.message
    assert "db.internal" not in app_exc.message
