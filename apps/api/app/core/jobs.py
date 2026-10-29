"""Tenant-Aware Background Job and Scheduled Task Execution Framework.

Enforces:
- Explicit tenant context on every background task
- Lifecycle verification (suspended/archived tenants are skipped/blocked)
- Independent fault domains (a failure in Tenant A never impacts Tenant B)
- Request-independent contextvar propagation for downstream services
"""

import asyncio
import logging
import time
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, TypeVar
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.exceptions import (
    CampusOSException,
    NotFoundException,
    TenantArchivedException,
    TenantSuspendedException,
)
from app.core.metrics import metrics
from app.core.tenant import (
    TenantContext,
    set_current_tenant_context,
)
from app.models.core import Institution

logger = logging.getLogger("campusos.jobs")

T = TypeVar("T")


class JobStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    RETRYING = "RETRYING"


@dataclass(frozen=True)
class TenantJobContext:
    tenant_id: UUID
    code: str
    name: str
    status: str
    plan: str
    timezone: str


@dataclass
class JobExecutionRecord:
    job_id: UUID = field(default_factory=uuid4)
    job_name: str = "generic_task"
    tenant_id: UUID | None = None
    status: JobStatus = JobStatus.PENDING
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    duration_seconds: float = 0.0
    retry_count: int = 0
    error_code: str | None = None
    error_message: str | None = None



class TenantJobRunner:
    """Executes background jobs and scheduled tasks with guaranteed tenant isolation."""

    @classmethod
    async def run_tenant_job(
        cls,
        tenant_id: UUID,
        task_fn: Callable[[TenantJobContext, AsyncSession], Coroutine[Any, Any, T]],
        db: AsyncSession | None = None,
        allow_suspended: bool = False,
    ) -> T:
        """Execute a job within a specific tenant context after lifecycle verification."""
        if db is not None:
            return await cls._execute_tenant_job(tenant_id, task_fn, db, allow_suspended)

        async with AsyncSessionLocal() as session:
            return await cls._execute_tenant_job(tenant_id, task_fn, session, allow_suspended)

    @classmethod
    async def _execute_tenant_job(
        cls,
        tenant_id: UUID,
        task_fn: Callable[[TenantJobContext, AsyncSession], Coroutine[Any, Any, T]],
        db: AsyncSession,
        allow_suspended: bool = False,
    ) -> T:
        stmt = select(Institution).where(Institution.id == tenant_id)
        result = await db.execute(stmt)
        institution = result.scalar_one_or_none()

        if institution is None:
            raise NotFoundException("Tenant", tenant_id)

        status = (institution.status or "ACTIVE").upper()
        if not allow_suspended and status == "SUSPENDED":
            raise TenantSuspendedException(tenant_id)
        if status == "ARCHIVED" or not institution.is_active:
            raise TenantArchivedException(tenant_id)

        job_ctx = TenantJobContext(
            tenant_id=institution.id,
            code=institution.code,
            name=institution.legal_name,
            status=status,
            plan=institution.plan or "ENTERPRISE",
            timezone=institution.default_timezone or "Asia/Kolkata",
        )

        # Establish tenant context for any repository or service calls
        req_ctx = TenantContext(
            tenant_id=institution.id,
            code=institution.code,
            name=institution.legal_name,
            is_active=institution.is_active,
            tenant_status=status,
            slug=institution.slug,
            plan=institution.plan or "ENTERPRISE",
            timezone=institution.default_timezone or "Asia/Kolkata",
            currency=institution.currency_code or "INR",
            locale=institution.locale or "en-IN",
        )
        set_current_tenant_context(req_ctx)

        try:
            metrics.record_job_status("tenant_job", "RUNNING")
            outcome = await task_fn(job_ctx, db)
            metrics.record_job_status("tenant_job", "SUCCESS")
            return outcome
        except Exception:
            metrics.record_job_status("tenant_job", "FAILED")
            raise
        finally:
            set_current_tenant_context(None)

    @classmethod
    async def run_tenant_job_with_retry(
        cls,
        tenant_id: UUID,
        task_fn: Callable[[TenantJobContext, AsyncSession], Coroutine[Any, Any, T]],
        job_name: str = "generic_task",
        max_retries: int = 3,
        base_delay_seconds: float = 0.05,
        db: AsyncSession | None = None,
        allow_suspended: bool = False,
    ) -> tuple[T | None, JobExecutionRecord]:
        """Execute a tenant-scoped job with bounded exponential backoff for transient errors."""
        record = JobExecutionRecord(
            job_name=job_name,
            tenant_id=tenant_id,
            status=JobStatus.RUNNING,
            started_at=datetime.now(UTC),
        )
        start_t = time.perf_counter()

        for attempt in range(max_retries + 1):
            try:
                outcome = await cls.run_tenant_job(
                    tenant_id=tenant_id,
                    task_fn=task_fn,
                    db=db,
                    allow_suspended=allow_suspended,
                )
                record.status = JobStatus.SUCCESS
                record.completed_at = datetime.now(UTC)
                record.duration_seconds = time.perf_counter() - start_t
                record.retry_count = attempt
                return outcome, record
            except CampusOSException as exc:
                # Permanent business/authorization/tenant error: fail closed immediately without retry
                record.status = JobStatus.FAILED
                record.completed_at = datetime.now(UTC)
                record.duration_seconds = time.perf_counter() - start_t
                record.retry_count = attempt
                record.error_code = exc.code
                record.error_message = exc.message
                raise
            except Exception as exc:
                record.retry_count = attempt
                if attempt < max_retries:
                    record.status = JobStatus.RETRYING
                    metrics.record_job_status(job_name, "RETRYING")
                    delay = base_delay_seconds * (2 ** attempt)
                    await asyncio.sleep(delay)
                else:
                    record.status = JobStatus.FAILED
                    record.completed_at = datetime.now(UTC)
                    record.duration_seconds = time.perf_counter() - start_t
                    record.error_code = "TRANSIENT_FAILURE_EXHAUSTED"
                    record.error_message = str(exc)
                    raise


    @classmethod
    async def run_scheduled_job_for_all_active_tenants(
        cls,
        job_name: str,
        task_fn: Callable[[TenantJobContext, AsyncSession], Coroutine[Any, Any, None]],
    ) -> dict[str, Any]:
        """Execute scheduled recurring maintenance across all active tenants with independent fault domains."""
        results: dict[str, Any] = {"total": 0, "succeeded": 0, "failed": 0, "errors": {}}

        async with AsyncSessionLocal() as db:
            stmt = select(Institution).where(
                Institution.is_active.is_(True),
                Institution.status.in_(["ACTIVE", "TRIAL"]),
            )
            res = await db.execute(stmt)
            tenants = list(res.scalars().all())

        results["total"] = len(tenants)

        for tenant in tenants:
            try:
                await cls.run_tenant_job(tenant.id, task_fn)
                results["succeeded"] += 1
            except Exception as exc:
                results["failed"] += 1
                results["errors"][str(tenant.id)] = str(exc)
                logger.error(
                    "Scheduled job '%s' failed for tenant %s: %s",
                    job_name,
                    tenant.id,
                    exc,
                    exc_info=True,
                )

        return results
