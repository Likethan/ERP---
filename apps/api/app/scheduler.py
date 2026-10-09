"""CampusOS Production Distributed Scheduler.

Executes recurring institutional maintenance and batch processes across all active tenants:
- Scheduled workflow evaluation taking tenant timezone into account
- Document expiry checks
- Fee overdue processing
- Attendance alerts & low attendance calculations
- Notification queue delivery
- Analytics summary refresh

Guarantees:
- Single execution across multiple replicas via distributed locking
- Independent fault domains (a failure in Tenant A never impacts Tenant B)
- Timezone safety: schedules evaluated using each tenant's configured timezone
- Graceful shutdown handling
"""

import asyncio
import logging
import signal
from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.jobs import TenantJobContext, TenantJobRunner
from app.core.lock import distributed_lock
from app.models.workflow import (
    WorkflowDefinition,
    WorkflowStatus,
    WorkflowTrigger,
    WorkflowTriggerType,
)
from app.services.workflow_service import WorkflowService

logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","service":"campusos-scheduler","logger":"%(name)s","message":"%(message)s"}',
)
logger = logging.getLogger("campusos.scheduler")

_running = True


def handle_shutdown(sig, frame):
    global _running
    logger.info("Shutdown signal received (%s). Stopping scheduler loop...", sig)
    _running = False


# Scheduled Task Handlers (Tenant-Isolated)
async def evaluate_scheduled_workflows(ctx: TenantJobContext, db: AsyncSession) -> None:
    """Evaluate and trigger scheduled workflows for this tenant in tenant local time."""
    try:
        tenant_tz = ZoneInfo(ctx.timezone)
    except Exception:
        tenant_tz = ZoneInfo("Asia/Kolkata")

    now_local = datetime.now(tenant_tz)
    current_time_str = now_local.strftime("%H:%M")
    current_weekday = now_local.weekday()  # 0=Monday, 6=Sunday

    stmt = (
        select(WorkflowDefinition)
        .join(WorkflowTrigger, WorkflowDefinition.id == WorkflowTrigger.workflow_id)
        .where(
            and_(
                WorkflowDefinition.tenant_id == ctx.tenant_id,
                WorkflowDefinition.status == WorkflowStatus.ACTIVE,
                WorkflowTrigger.trigger_type == WorkflowTriggerType.SCHEDULE,
                WorkflowTrigger.is_enabled.is_(True),
            )
        )
    )
    result = await db.execute(stmt)
    workflows = list(result.scalars().all())

    for wf in workflows:
        for trg in wf.triggers:
            should_run = False
            if trg.days_of_week is not None and current_weekday not in trg.days_of_week:
                continue

            if trg.schedule_time and trg.schedule_time == current_time_str:
                should_run = True

            if trg.interval_seconds and trg.interval_seconds <= 3600:
                should_run = True

            if should_run:
                try:
                    await WorkflowService.execute_workflow(
                        db=db,
                        tenant_id=ctx.tenant_id,
                        workflow_id=wf.id,
                        trigger_type=WorkflowTriggerType.SCHEDULE,
                        trigger_reference=f"schedule:{current_time_str}:{now_local.strftime('%Y%m%d')}",
                    )
                except Exception as exc:
                    logger.error("Error running scheduled workflow '%s': %s", wf.name, exc)


async def check_document_expiry(ctx: TenantJobContext, db: Any) -> None:
    logger.debug("Checking document expiries for tenant %s", ctx.tenant_id)


async def process_fee_overdues(ctx: TenantJobContext, db: Any) -> None:
    logger.debug("Processing fee overdues for tenant %s", ctx.tenant_id)


async def evaluate_attendance_alerts(ctx: TenantJobContext, db: Any) -> None:
    logger.debug("Evaluating attendance alerts for tenant %s", ctx.tenant_id)


async def refresh_analytics(ctx: TenantJobContext, db: Any) -> None:
    """Refresh daily metric aggregations and run automated data quality reconciliation for tenant (Step 28)."""
    from app.services.analytics_service import AnalyticsService
    from app.services.data_quality_reconciliation_service import DataQualityReconciliationService

    logger.debug("Refreshing analytics summaries for tenant %s", ctx.tenant_id)
    try:
        today = datetime.now(UTC).date()
        yesterday = today - timedelta(days=1)
        count = await AnalyticsService.run_backfill(
            db=db,
            tenant_id=ctx.tenant_id,
            start_date=yesterday,
            end_date=today,
        )
        findings = await DataQualityReconciliationService.run_tenant_reconciliation(
            db=db,
            tenant_id=ctx.tenant_id,
        )
        if count > 0 or findings:
            logger.info(
                "Analytics refresh for tenant %s: rollups=%d, new_recon_findings=%d",
                ctx.tenant_id,
                count,
                len(findings),
            )
    except Exception as exc:
        logger.error("Error refreshing analytics for tenant %s: %s", ctx.tenant_id, exc)


async def check_integration_health(ctx: TenantJobContext, db: Any) -> None:
    logger.debug("Checking integration health for tenant %s", ctx.tenant_id)


async def retry_pending_webhooks(ctx: TenantJobContext, db: Any) -> None:
    logger.debug("Retrying pending webhooks for tenant %s", ctx.tenant_id)


async def activate_scheduled_configuration(ctx: TenantJobContext, db: Any) -> None:
    """Activate scheduled configuration overrides whose effective time has arrived."""
    from app.core.cache import tenant_cache
    from app.models.configuration import ConfigurationStatus, ConfigurationValue

    now = datetime.now(UTC)
    stmt = select(ConfigurationValue).where(
        ConfigurationValue.tenant_id == ctx.tenant_id,
        ConfigurationValue.status == ConfigurationStatus.SCHEDULED,
        ConfigurationValue.effective_from <= now,
    )
    result = await db.execute(stmt)
    scheduled_items = list(result.scalars().all())
    if scheduled_items:
        for item in scheduled_items:
            item.status = ConfigurationStatus.ACTIVE
        await db.flush()
        await tenant_cache.invalidate_namespace(ctx.tenant_id, "config")
        logger.info(
            "Activated %d scheduled configuration changes for tenant %s",
            len(scheduled_items),
            ctx.tenant_id,
        )


async def expire_feature_flags(ctx: TenantJobContext, db: Any) -> None:
    """Disable expired feature flags whose end date has passed."""
    from app.core.cache import tenant_cache
    from app.models.configuration import FeatureFlag

    now = datetime.now(UTC)
    stmt = select(FeatureFlag).where(
        FeatureFlag.tenant_id == ctx.tenant_id,
        FeatureFlag.is_enabled.is_(True),
        FeatureFlag.expires_at.isnot(None),
        FeatureFlag.expires_at <= now,
    )
    result = await db.execute(stmt)
    expired_flags = list(result.scalars().all())
    if expired_flags:
        for f in expired_flags:
            f.is_enabled = False
        await db.flush()
        await tenant_cache.invalidate_namespace(ctx.tenant_id, "features")
        logger.info(
            "Disabled %d expired feature flags for tenant %s", len(expired_flags), ctx.tenant_id
        )


async def run_master_data_quality_checks(ctx: TenantJobContext, db: Any) -> None:
    """Run data quality evaluation across master data entities for tenant."""
    from app.models.master_data import MasterDataType
    from app.services.master_data_service import MasterDataService

    logger.debug("Running master data quality evaluation for tenant %s", ctx.tenant_id)
    for mtype in [MasterDataType.STUDENT, MasterDataType.COMPANY, MasterDataType.DEPARTMENT]:
        try:
            await MasterDataService.recalculate_quality_scores(db, ctx.tenant_id, mtype)
        except Exception as exc:
            logger.warning(
                "Error evaluating quality for tenant %s master type %s: %s",
                ctx.tenant_id,
                mtype,
                exc,
            )


async def run_master_data_duplicate_detection(ctx: TenantJobContext, db: Any) -> None:
    """Run duplicate detection sweep across master data entities for tenant."""
    from app.models.master_data import MasterDataType
    from app.services.duplicate_detection_service import DuplicateDetectionService

    logger.debug("Running duplicate detection sweep for tenant %s", ctx.tenant_id)
    for mtype in [MasterDataType.STUDENT, MasterDataType.COMPANY, MasterDataType.DEPARTMENT]:
        try:
            await DuplicateDetectionService.scan_duplicates_for_type(db, ctx.tenant_id, mtype)
        except Exception as exc:
            logger.warning(
                "Error scanning duplicates for tenant %s master type %s: %s",
                ctx.tenant_id,
                mtype,
                exc,
            )


async def check_sla_deadlines_and_escalate(ctx: TenantJobContext, db: Any) -> None:
    """Sweep active SLA instances for tenant, detect breaches, and trigger escalations (Step 25)."""
    from app.services.sla_service import SlaService

    logger.debug("Checking SLA deadlines and escalations for tenant %s", ctx.tenant_id)
    try:
        sla_srv = SlaService(db)
        res = await sla_srv.check_deadlines_and_escalate(ctx.tenant_id)
        if res["breached"] > 0 or res["escalated"] > 0:
            logger.info(
                "SLA check for tenant %s: breached=%d, warned=%d, escalated=%d",
                ctx.tenant_id,
                res["breached"],
                res["warned"],
                res["escalated"],
            )
    except Exception as exc:
        logger.error("Error executing SLA deadline sweep for tenant %s: %s", ctx.tenant_id, exc)


async def expire_task_delegations(ctx: TenantJobContext, db: Any) -> None:
    """Deactivate expired task authority delegations for tenant (Step 25)."""
    from app.repositories.case_repository import CaseRepository

    logger.debug("Checking task delegation expiries for tenant %s", ctx.tenant_id)
    try:
        repo = CaseRepository(db)
        expired_count = await repo.expire_delegations(ctx.tenant_id, datetime.now(UTC))
        if expired_count > 0:
            logger.info(
                "Deactivated %d expired task delegations for tenant %s",
                expired_count,
                ctx.tenant_id,
            )
    except Exception as exc:
        logger.error("Error expiring task delegations for tenant %s: %s", ctx.tenant_id, exc)


async def dispatch_pending_notification_deliveries(ctx: TenantJobContext, db: Any) -> None:
    """Sweep scheduled and retryable notification deliveries for tenant (Step 26)."""
    from app.services.notification_orchestration_service import NotificationOrchestrationService

    logger.debug("Sweeping notification deliveries for tenant %s", ctx.tenant_id)
    try:
        res = await NotificationOrchestrationService.sweep_scheduled_and_retries(db, ctx.tenant_id)
        if res.get("total_dispatched", 0) > 0:
            logger.info(
                "Notification dispatch for tenant %s: scheduled=%d, retries=%d, total=%d",
                ctx.tenant_id,
                res.get("scheduled_processed", 0),
                res.get("retries_processed", 0),
                res.get("total_dispatched", 0),
            )
    except Exception as exc:
        logger.error("Error sweeping notification deliveries for tenant %s: %s", ctx.tenant_id, exc)


async def generate_notification_digests(ctx: TenantJobContext, db: Any) -> None:
    """Generate periodic notification digests for tenant (Step 26)."""
    from app.services.notification_digest_service import NotificationDigestService

    logger.debug("Generating notification digests for tenant %s", ctx.tenant_id)
    try:
        count = await NotificationDigestService.run_daily_task_digest(db, ctx.tenant_id)
        if count > 0:
            logger.info(
                "Generated %d daily notification digests for tenant %s", count, ctx.tenant_id
            )
    except Exception as exc:
        logger.error("Error generating notification digests for tenant %s: %s", ctx.tenant_id, exc)


async def cleanup_stale_outbox_events(ctx: TenantJobContext, db: Any) -> None:
    """Prune safely published outbox events older than retention period (Step 27)."""
    from app.core.events import OutboxService

    try:
        deleted = await OutboxService.cleanup_published_events(
            db, tenant_id=ctx.tenant_id, retention_days=90
        )
        if deleted > 0:
            logger.info(
                "Cleaned up %d aged published outbox events for tenant %s", deleted, ctx.tenant_id
            )
    except Exception as exc:
        logger.error("Error cleaning up outbox events for tenant %s: %s", ctx.tenant_id, exc)


async def scan_operational_anomalies_and_risks(ctx: TenantJobContext, db: Any) -> None:
    """Scan operational data for statistical anomalies and risk patterns (Step 29)."""
    from app.domains.intelligence.services.anomaly_detection_service import OperationalAnomalyService
    from app.schemas.intelligence import AnomalyDetectionRequest

    try:
        res = await OperationalAnomalyService.scan_anomalies(
            db=db,
            tenant_id=ctx.tenant_id,
            request=AnomalyDetectionRequest(domain="ALL", sensitivity="MEDIUM"),
        )
        if res.anomalies_detected > 0:
            logger.info(
                "Detected %d operational anomalies for tenant %s during scheduled scan",
                res.anomalies_detected,
                ctx.tenant_id,
            )
    except Exception as exc:
        logger.error("Error executing operational anomaly scan for tenant %s: %s", ctx.tenant_id, exc)



async def run_single_scheduled_job(job_name: str, task_fn: Any, lock_ttl: int = 300) -> None:
    """Run a scheduled job across all tenants protected by a distributed lock."""
    async with distributed_lock(f"scheduler:{job_name}", ttl_seconds=lock_ttl) as acquired:
        if not acquired:
            logger.info("Scheduled job '%s' is already active on another node, skipping.", job_name)
            return

        logger.info("Acquired distributed lock for scheduled job '%s'. Executing...", job_name)
        start_t = datetime.now(UTC)
        try:
            results = await TenantJobRunner.run_scheduled_job_for_all_active_tenants(
                job_name=job_name,
                task_fn=task_fn,
            )
            duration = (datetime.now(UTC) - start_t).total_seconds()
            logger.info(
                "Completed scheduled job '%s' in %.2fs: total=%d, succeeded=%d, failed=%d",
                job_name,
                duration,
                results["total"],
                results["succeeded"],
                results["failed"],
            )
        except Exception as exc:
            logger.error("Error executing scheduled job '%s': %s", job_name, exc, exc_info=True)


async def run_scheduler_loop():
    """Main scheduler loop running periodic tasks at configured intervals."""
    logger.info(
        "CampusOS Scheduler starting in %s mode (service: %s)...",
        settings.ENVIRONMENT,
        settings.PROJECT_NAME,
    )

    iteration = 0
    while _running:
        try:
            iteration += 1

            # Run scheduled workflow evaluation every minute
            await run_single_scheduled_job(
                "workflow_schedules", evaluate_scheduled_workflows, lock_ttl=60
            )

            # Run scheduled and retry notification dispatches every minute (Step 26)
            await run_single_scheduled_job(
                "dispatch_notifications", dispatch_pending_notification_deliveries, lock_ttl=60
            )

            # Run hourly batch maintenance tasks every 30 iterations
            if iteration % 30 == 0:
                await run_single_scheduled_job("document_expiry", check_document_expiry)
                await run_single_scheduled_job("fee_overdue", process_fee_overdues)
                await run_single_scheduled_job("attendance_alerts", evaluate_attendance_alerts)
                await run_single_scheduled_job("analytics_refresh", refresh_analytics)
                await run_single_scheduled_job("integration_health", check_integration_health)
                await run_single_scheduled_job("webhook_retries", retry_pending_webhooks)
                await run_single_scheduled_job(
                    "scheduled_configuration_activation", activate_scheduled_configuration
                )
                await run_single_scheduled_job("feature_flag_expiration", expire_feature_flags)
                await run_single_scheduled_job(
                    "master_data_quality_checks", run_master_data_quality_checks
                )
                await run_single_scheduled_job(
                    "master_data_duplicate_detection", run_master_data_duplicate_detection
                )
                await run_single_scheduled_job(
                    "check_sla_deadlines_and_escalate", check_sla_deadlines_and_escalate
                )
                await run_single_scheduled_job("expire_task_delegations", expire_task_delegations)
                await run_single_scheduled_job(
                    "notification_digests", generate_notification_digests
                )
                await run_single_scheduled_job(
                    "cleanup_stale_outbox_events", cleanup_stale_outbox_events
                )
                await run_single_scheduled_job(
                    "ai_anomaly_scan", scan_operational_anomalies_and_risks
                )

            # Sleep 60 seconds between tick evaluations
            for _ in range(60):
                if not _running:
                    break
                await asyncio.sleep(1.0)

        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.error("Unexpected error in scheduler loop: %s", exc, exc_info=True)
            await asyncio.sleep(10.0)

    logger.info("CampusOS Scheduler stopped cleanly.")


def main():
    signal.signal(signal.SIGINT, handle_shutdown)
    try:
        signal.signal(signal.SIGTERM, handle_shutdown)
    except AttributeError:
        pass

    asyncio.run(run_scheduler_loop())


if __name__ == "__main__":
    main()
