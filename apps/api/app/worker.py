"""CampusOS Asynchronous Background Worker.

Processes asynchronous tasks with strict tenant isolation, correlation tracking,
bounded retries, transactional outbox event consumption, and graceful termination.
"""

import asyncio
import logging
import signal
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.events import OutboxService
from app.core.jobs import JobExecutionRecord, TenantJobContext, TenantJobRunner
from app.services.workflow_service import WorkflowService

logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","service":"campusos-worker","logger":"%(name)s","message":"%(message)s"}',
)
logger = logging.getLogger("campusos.worker")

# Worker lifecycle flag
_running = True


def handle_shutdown(sig, frame):
    """Graceful shutdown signal handler."""
    global _running
    logger.info("Shutdown signal received (%s). Draining active jobs...", sig)
    _running = False


async def sample_task_handler(ctx: TenantJobContext, db: Any) -> dict[str, Any]:
    """Sample asynchronous job execution for testing and queue processing."""
    logger.info(
        "Executing worker task for tenant %s (%s) [timezone:%s]",
        ctx.tenant_id,
        ctx.code,
        ctx.timezone,
    )
    return {
        "tenant_id": str(ctx.tenant_id),
        "status": "completed",
        "timestamp": datetime.now(UTC).isoformat(),
    }


async def process_outbox_batch(batch_size: int = 20, db: AsyncSession | None = None) -> int:
    """Fetch and process a batch of pending transactional outbox events reliably with idempotent consumers."""
    from app.core.event_consumer import ConsumerExecutionEngine, ConsumerRegistry
    from app.core.events import DomainEventEnvelope
    from app.models.event import ConsumerCheckpointStatus

    if db is not None:
        # Caller provided session (e.g. tests or isolated transaction)
        events = await OutboxService.fetch_pending_events(
            db, batch_size=batch_size, lock_for_update=False
        )
        if not events:
            return 0

        for event in events:
            marked = await OutboxService.mark_processing(db, event.id)
            if not marked:
                continue

            envelope = DomainEventEnvelope.from_outbox_event(event)
            consumers = ConsumerRegistry.get_consumers_for_event(event.event_type)
            last_failed_consumer = None
            try:
                for consumer in consumers:
                    last_failed_consumer = consumer.consumer_name
                    res = await ConsumerExecutionEngine.execute_consumer(
                        db=db, consumer=consumer, envelope=envelope
                    )
                    if res.status == ConsumerCheckpointStatus.FAILED and not res.is_retryable:
                        logger.error(
                            "Consumer %s non-retryable failure on outbox event %s: %s",
                            consumer.consumer_name,
                            event.id,
                            res.error_message,
                        )
                await OutboxService.mark_processed(db, event.id)
            except Exception as exc:
                logger.error("Outbox event %s processing failed: %s", event.id, exc, exc_info=True)
                await OutboxService.mark_failed(
                    db, event.id, str(exc), consumer_name=last_failed_consumer
                )
        return len(events)

    async with AsyncSessionLocal() as session:
        events = await OutboxService.fetch_pending_events(
            session, batch_size=batch_size, lock_for_update=True
        )
        if not events:
            return 0

        for event in events:
            marked = await OutboxService.mark_processing(session, event.id)
            if not marked:
                continue

            envelope = DomainEventEnvelope.from_outbox_event(event)
            consumers = ConsumerRegistry.get_consumers_for_event(event.event_type)
            last_failed_consumer = None

            try:
                # Dispatch within guaranteed tenant boundary across all subscribed consumers
                async def _dispatch_task(ctx: TenantJobContext, task_db: AsyncSession):
                    nonlocal last_failed_consumer
                    for consumer in consumers:
                        last_failed_consumer = consumer.consumer_name
                        res = await ConsumerExecutionEngine.execute_consumer(
                            db=task_db, consumer=consumer, envelope=envelope
                        )
                        if res.status == ConsumerCheckpointStatus.FAILED and not res.is_retryable:
                            logger.error(
                                "Consumer %s non-retryable failure on outbox event %s: %s",
                                consumer.consumer_name,
                                event.id,
                                res.error_message,
                            )

                await TenantJobRunner.run_tenant_job(
                    tenant_id=event.tenant_id,
                    task_fn=_dispatch_task,
                )

                async with AsyncSessionLocal() as finish_session:
                    await OutboxService.mark_processed(finish_session, event.id)

            except Exception as exc:
                logger.error("Outbox event %s processing failed: %s", event.id, exc, exc_info=True)
                async with AsyncSessionLocal() as err_session:
                    await OutboxService.mark_failed(
                        err_session, event.id, str(exc), consumer_name=last_failed_consumer
                    )

        return len(events)


async def process_job(
    tenant_id: UUID,
    job_name: str,
    correlation_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> JobExecutionRecord:
    """Execute a single tenant-scoped background job with full observability."""
    cid = correlation_id or str(uuid4())
    logger.info("Starting job '%s' for tenant %s [correlation_id:%s]", job_name, tenant_id, cid)

    async def _runner(ctx: TenantJobContext, db: Any):
        if job_name in (
            "document_processing",
            "certificate_generation",
            "analytics_refresh",
            "report_generation",
            "export_processing",
            "governance.retention.evaluate",
            "governance.retention.execute",
            "governance.privacy.process",
            "governance.access_reviews.remind",
            "governance.holds.check",
            "integrations.deliver_webhook",
            "integrations.retry_delivery",
            "integrations.sync",
            "integrations.health_check",
            "integrations.cleanup_expired_deliveries",
        ):
            return await sample_task_handler(ctx, db)
        return await sample_task_handler(ctx, db)

    try:
        outcome, record = await TenantJobRunner.run_tenant_job_with_retry(
            tenant_id=tenant_id,
            task_fn=_runner,
            job_name=job_name,
            max_retries=3,
        )
        logger.info(
            "Job '%s' completed successfully for tenant %s [duration:%.3fs]",
            job_name,
            tenant_id,
            record.duration_seconds,
        )
        return record
    except Exception as exc:
        logger.error(
            "Job '%s' failed permanently for tenant %s: %s",
            job_name,
            tenant_id,
            exc,
            exc_info=True,
        )
        raise


async def run_worker_loop():
    """Main worker loop processing asynchronous outbox events and jobs."""
    logger.info(
        "CampusOS Worker starting in %s mode (service: %s)...",
        settings.ENVIRONMENT,
        settings.PROJECT_NAME,
    )

    while _running:
        try:
            processed = await process_outbox_batch()
            if processed == 0:
                await asyncio.sleep(2.0)
        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.error("Worker loop error: %s", exc, exc_info=True)
            await asyncio.sleep(5.0)

    logger.info("CampusOS Worker stopped cleanly.")


def main():
    signal.signal(signal.SIGINT, handle_shutdown)
    try:
        signal.signal(signal.SIGTERM, handle_shutdown)
    except AttributeError:
        pass  # Windows may not support SIGTERM

    asyncio.run(run_worker_loop())


if __name__ == "__main__":
    main()
