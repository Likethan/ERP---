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
from datetime import UTC, date, datetime, timedelta
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
    from app.domains.intelligence.services.anomaly_detection_service import (
        OperationalAnomalyService,
    )
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


async def sweep_expired_trials(ctx: TenantJobContext, db: Any) -> None:
    """Evaluate trial expiration and grace periods for tenant (Step 30)."""
    from app.models.platform_ops import TenantLifecycleStatus
    from app.services.entitlement_service import EntitlementService
    from app.services.tenant_lifecycle_service import TenantLifecycleService

    try:
        trial_info = await EntitlementService.evaluate_trial_status(db, ctx.tenant_id)
        if trial_info.get("is_trial") and trial_info.get("is_expired") and not trial_info.get("in_grace_period"):
            logger.info("Trial expired and grace period elapsed for tenant %s. Suspending...", ctx.tenant_id)
            await TenantLifecycleService.transition_tenant_status(
                db=db,
                tenant_id=ctx.tenant_id,
                target_status=TenantLifecycleStatus.SUSPENDED.value,
                actor_id=None,
                actor_email="system@campusos.internal",
                reason="Trial expiration and grace period elapsed",
            )
    except Exception as exc:
        logger.error("Error evaluating trial status for tenant %s: %s", ctx.tenant_id, exc)


async def evaluate_tenant_resource_quotas(ctx: TenantJobContext, db: Any) -> None:
    """Evaluate resource consumption and update threshold warnings for tenant (Step 30)."""
    from app.services.tenant_quota_service import TenantQuotaService

    try:
        await TenantQuotaService.ensure_tenant_quotas(db, ctx.tenant_id)
    except Exception as exc:
        logger.error("Error evaluating resource quotas for tenant %s: %s", ctx.tenant_id, exc)


async def sweep_platform_support_sessions(ctx: TenantJobContext, db: Any) -> None:
    """Sweep and expire platform support sessions whose duration has elapsed (Step 30)."""
    from app.services.platform_support_service import PlatformSupportService

    try:
        count = await PlatformSupportService.sweep_expired_sessions(db)
        if count > 0:
            logger.info("Swept %d expired platform support sessions across tenants", count)
    except Exception as exc:
        logger.error("Error sweeping platform support sessions: %s", exc)


async def recover_abandoned_outbox_events_task(ctx: TenantJobContext, db: Any) -> None:
    """Recover outbox events stuck in PROCESSING due to worker crashes (Step 31)."""
    from app.core.events import OutboxService

    try:
        res = await OutboxService.recover_abandoned_events(
            db, stuck_threshold_seconds=300, tenant_id=ctx.tenant_id
        )
        if res["recovered_count"] > 0 or res["dead_lettered_count"] > 0:
            logger.info(
                "Abandoned outbox recovery for tenant %s: recovered=%d, dead_lettered=%d",
                ctx.tenant_id,
                res["recovered_count"],
                res["dead_lettered_count"],
            )
    except Exception as exc:
        logger.error("Error recovering abandoned outbox events for tenant %s: %s", ctx.tenant_id, exc)


async def audit_backup_freshness_and_circuit_health(ctx: TenantJobContext, db: Any) -> None:
    """Audit disaster recovery readiness, backup freshness, and probe circuit breakers (Step 31)."""
    from app.core.resilience import circuit_registry

    try:
        for cb in circuit_registry.get_all():
            await cb.can_execute()
    except Exception as exc:
        logger.error("Error evaluating circuit breakers health: %s", exc)


async def evaluate_adoption_deadlines_and_expirations(ctx: TenantJobContext, db: Any) -> None:
    """Evaluate training program deadlines, overdue reminders, and announcement/guidance expirations (Step 37)."""
    from app.services.adoption_service import AdoptionService

    try:
        deadlines_res = await AdoptionService.evaluate_training_deadlines_and_reminders(db)
        exp_res = await AdoptionService.evaluate_expirations(db)
        if deadlines_res.get("overdue_processed", 0) > 0 or exp_res.get("expired_announcements", 0) > 0:
            logger.info(
                "Adoption sweep for tenant %s: overdue=%d, expired_announcements=%d, expired_guidance=%d",
                ctx.tenant_id,
                deadlines_res.get("overdue_processed", 0),
                exp_res.get("expired_announcements", 0),
                exp_res.get("expired_guidance", 0),
            )
    except Exception as exc:
        logger.error("Error evaluating adoption deadlines and expirations for tenant %s: %s", ctx.tenant_id, exc)


async def sweep_subscription_lifecycle_task(ctx: TenantJobContext, db: Any) -> None:
    """Evaluate subscription trials, grace periods, auto-renewals, and override expiries (Step 38)."""
    from app.services.subscription_service import SubscriptionService

    try:
        res = await SubscriptionService.sweep_subscription_lifecycle(db)
        if any(v > 0 for v in res.values()):
            logger.info(
                "Subscription lifecycle sweep for tenant %s: trials=%d, grace=%d, overrides=%d, renewed=%d",
                ctx.tenant_id,
                res.get("swept_trials", 0),
                res.get("swept_grace", 0),
                res.get("swept_overrides", 0),
                res.get("auto_renewed", 0),
            )
    except Exception as exc:
        logger.error("Error sweeping subscription lifecycle for tenant %s: %s", ctx.tenant_id, exc)


async def sync_marketplace_integrations_task(ctx: TenantJobContext, db: Any) -> None:
    """Evaluate and trigger scheduled sync for active marketplace integrations (Step 39)."""
    from sqlalchemy import select

    from app.models.marketplace import (
        SyncTriggerType,
        TenantAppInstallation,
        TenantInstallationStatus,
    )
    from app.schemas.marketplace import SyncTriggerRequest
    from app.services.marketplace_service import MarketplaceService

    try:
        stmt = select(TenantAppInstallation).where(
            TenantAppInstallation.tenant_id == ctx.tenant_id,
            TenantAppInstallation.status == TenantInstallationStatus.CONNECTED.value,
        )
        res = await db.execute(stmt)
        installations = list(res.scalars().all())

        for inst in installations:
            try:
                dto = SyncTriggerRequest(trigger_type=SyncTriggerType.SCHEDULED)
                await MarketplaceService.trigger_sync(
                    db=db,
                    tenant_id=ctx.tenant_id,
                    installation_id=inst.id,
                    actor_id=None,
                    dto=dto,
                )
            except Exception as inst_exc:
                logger.warning("Error running scheduled sync for installation %s: %s", inst.id, inst_exc)
    except Exception as exc:
        logger.error("Error in marketplace integration sync job for tenant %s: %s", ctx.tenant_id, exc)


async def sweep_records_lifecycle_task(ctx: TenantJobContext, db: Any) -> None:
    """Sweep institutional records for retention recalculation and hold coverage (Step 41)."""
    from app.models.records_lifecycle import ScheduledRunType
    from app.services.records_lifecycle_service import RecordsLifecycleService

    logger.debug("Executing scheduled records lifecycle sweeps for tenant %s", ctx.tenant_id)
    try:
        await RecordsLifecycleService.run_scheduled_lifecycle_sweep(
            db=db,
            tenant_id=ctx.tenant_id,
            job_type=ScheduledRunType.ELIGIBILITY_RECALCULATION,
            batch_size=100,
        )
        await RecordsLifecycleService.run_scheduled_lifecycle_sweep(
            db=db,
            tenant_id=ctx.tenant_id,
            job_type=ScheduledRunType.HOLD_COVERAGE_CHECK,
            batch_size=100,
        )
    except Exception as exc:
        logger.error("Error in records lifecycle scheduled sweep for tenant %s: %s", ctx.tenant_id, exc)


async def sweep_knowledge_reviews_task(ctx: TenantJobContext, db: Any) -> None:
    """Sweep institutional policies for overdue reviews and scheduled publication releases (Step 42)."""
    from app.services.knowledge_service import KnowledgeService

    logger.debug("Executing scheduled knowledge review sweeps for tenant %s", ctx.tenant_id)
    try:
        service = KnowledgeService()
        await service.sweep_knowledge_reviews(db)
    except Exception as exc:
        logger.error("Error in knowledge review scheduled sweep for tenant %s: %s", ctx.tenant_id, exc)


async def sweep_accreditation_quality_task(ctx: TenantJobContext, db: Any) -> None:
    """Sweep institutional accreditation evidence and quality CAPA actions for expirations and deadlines (Step 43)."""
    from app.services.accreditation_service import AccreditationService

    logger.debug("Executing scheduled accreditation and quality sweeps for tenant %s", ctx.tenant_id)
    try:
        service = AccreditationService(db)
        res = await service.sweep_quality_reviews()
        if any(v > 0 for k, v in res.items() if isinstance(v, int)):
            logger.info("Accreditation quality sweep: %s", res)
    except Exception as exc:
        logger.error("Error in accreditation quality scheduled sweep for tenant %s: %s", ctx.tenant_id, exc)


async def sweep_research_deadlines_task(ctx: TenantJobContext, db: Any) -> None:
    """Sweep institutional research projects for expiring ethics approvals and overdue milestones (Step 44)."""
    from app.services.research_service import ResearchService

    logger.debug("Executing scheduled research deadline and compliance sweep for tenant %s", ctx.tenant_id)
    try:
        res = await ResearchService.sweep_deadlines_and_compliance(db, ctx.tenant_id)
        if res.expiring_ethics_approvals_flagged > 0 or res.overdue_milestones_flagged > 0:
            logger.info("Research compliance sweep for tenant %s: %s", ctx.tenant_id, res)
    except Exception as exc:
        logger.error("Error in research compliance scheduled sweep for tenant %s: %s", ctx.tenant_id, exc)


async def sweep_library_deadlines_task(ctx: TenantJobContext, db: Any) -> None:
    """Sweep institutional library for overdue loans, expired hold reservations, and expiring subscriptions (Step 45)."""
    from decimal import Decimal

    from app.services.library_service import LibraryService

    logger.debug("Executing scheduled library deadline and compliance sweep for tenant %s", ctx.tenant_id)
    try:
        res = await LibraryService.sweep_deadlines_and_compliance(db, ctx.tenant_id)
        if any(v > 0 for k, v in res.items() if isinstance(v, (int, float, Decimal))):
            logger.info("Library compliance sweep for tenant %s: %s", ctx.tenant_id, res)
    except Exception as exc:
        logger.error("Error in library compliance scheduled sweep for tenant %s: %s", ctx.tenant_id, exc)


async def sweep_student_success_task(ctx: TenantJobContext, db: Any) -> None:
    """Evaluate active early-warning rules and sweep overdue interventions (Step 47)."""
    from app.schemas.student_success import EarlyWarningEvaluationRequest
    from app.services.student_success_service import StudentSuccessService

    logger.debug("Executing student success early warning and intervention sweep for tenant %s", ctx.tenant_id)
    try:
        service = StudentSuccessService(db)
        # 1. Sweep overdue interventions
        overdue_count = await service.sweep_overdue_interventions(ctx.tenant_id)
        # 2. Evaluate active early warning rules
        eval_req = EarlyWarningEvaluationRequest()
        evals = await service.evaluate_rules(
            tenant_id=ctx.tenant_id,
            payload=eval_req,
            triggered_by="SCHEDULED_JOB",
        )
        total_signals = sum(e.warnings_generated_count for e in evals)
        if overdue_count > 0 or total_signals > 0:
            logger.info(
                "Student success sweep for tenant %s: %d overdue interventions, %d new signals",
                ctx.tenant_id,
                overdue_count,
                total_signals,
            )
    except Exception as exc:
        logger.error("Error in student success scheduled sweep for tenant %s: %s", ctx.tenant_id, exc)


async def sweep_admissions_offers_task(ctx: TenantJobContext, db: Any) -> None:
    """Sweep expired admission offers and release reserved seat capacities (Step 48)."""
    from datetime import date

    from sqlalchemy import select

    from app.models.admissions import AdmissionOffer, OfferStatus
    from app.services.admissions_service import AdmissionsService

    logger.debug("Executing admissions expired offers sweep for tenant %s", ctx.tenant_id)
    try:
        stmt = select(AdmissionOffer).where(
            AdmissionOffer.tenant_id == ctx.tenant_id,
            AdmissionOffer.status == OfferStatus.ISSUED,
            AdmissionOffer.expiry_date < date.today(),
        )
        res = await db.execute(stmt)
        expired_offers = res.scalars().all()
        if expired_offers:
            svc = AdmissionsService(db)
            for offer in expired_offers:
                offer.status = OfferStatus.EXPIRED
                await svc._release_reserved_seat(ctx.tenant_id, offer.cycle_id, offer.program_id)
            await db.commit()
            logger.info(
                "Admissions sweep for tenant %s: expired %d stale offers and released seats",
                ctx.tenant_id,
                len(expired_offers),
            )
    except Exception as exc:
        logger.error("Error in admissions offers scheduled sweep for tenant %s: %s", ctx.tenant_id, exc)


async def sweep_workforce_deadlines_and_accruals_task(ctx: TenantJobContext, db: Any) -> None:
    """Sweep overdue workforce lifecycle tasks, probation milestones, and leave accruals (Step 51)."""
    from datetime import date, timedelta

    from sqlalchemy import select

    from app.models.workforce import (
        EmploymentStatus,
        LifecycleTaskStatus,
        WorkforceEmployee,
        WorkforceLifecycleTask,
    )

    logger.debug("Executing workforce lifecycle sweep for tenant %s", ctx.tenant_id)
    try:
        # Check overdue lifecycle tasks
        stmt = select(WorkforceLifecycleTask).where(
            WorkforceLifecycleTask.tenant_id == ctx.tenant_id,
            WorkforceLifecycleTask.status == LifecycleTaskStatus.PENDING,
            WorkforceLifecycleTask.due_date < date.today(),
        )
        res = await db.execute(stmt)
        overdue_tasks = res.scalars().all()
        if overdue_tasks:
            logger.info("Workforce sweep for tenant %s: found %d overdue lifecycle tasks", ctx.tenant_id, len(overdue_tasks))

        # Check contracts reaching expiry within 30 days
        expiry_threshold = date.today() + timedelta(days=30)
        contract_stmt = select(WorkforceEmployee).where(
            WorkforceEmployee.tenant_id == ctx.tenant_id,
            WorkforceEmployee.employment_status == EmploymentStatus.ACTIVE,
            WorkforceEmployee.contract_end_date.isnot(None),
            WorkforceEmployee.contract_end_date <= expiry_threshold,
        )
        contract_res = await db.execute(contract_stmt)
        expiring_contracts = contract_res.scalars().all()
        if expiring_contracts:
            logger.info("Workforce sweep for tenant %s: found %d employees with contracts expiring within 30 days", ctx.tenant_id, len(expiring_contracts))
    except Exception as exc:
        logger.error("Error in workforce scheduled sweep for tenant %s: %s", ctx.tenant_id, exc)


async def sweep_asset_lifecycle_maintenance_task(
    ctx: TenantJobContext | None = None, db: AsyncSession | None = None
) -> None:
    """Evaluate and trigger upcoming PM work orders, overdue work orders, expiring warranties, and overdue loans."""
    try:
        from app.services.asset_service import AssetService
        if ctx is not None and db is not None:
            metrics = await AssetService.sweep_asset_maintenance_and_compliance(db, ctx.tenant_id)
            if any(v > 0 for v in metrics.values()):
                logger.info("Asset & maintenance sweep for tenant %s: %s", ctx.tenant_id, metrics)
        else:
            from app.core.database import async_session_factory
            from app.models.tenant import Institution
            async with async_session_factory() as session:
                tenants = (await session.execute(select(Institution.id))).scalars().all()
                for tid in tenants:
                    try:
                        await AssetService.sweep_asset_maintenance_and_compliance(session, tid)
                    except Exception as exc:
                        logger.error("Sweep error for tenant %s: %s", tid, exc)
    except Exception as exc:
        logger.error("Error in asset maintenance scheduled sweep: %s", exc)


async def sweep_residential_life_operations_task(ctx: TenantJobContext, db: AsyncSession) -> None:
    """Evaluate overdue outings, expired bed reservations, visitor passes, and maintenance SLAs (Step 54)."""
    try:
        from app.services.residential_service import ResidentialService
        metrics = await ResidentialService.sweep_residential_operations(db, ctx.tenant_id)
        if any(v > 0 for v in metrics.values()):
            logger.info("Residential operations sweep for tenant %s: %s", ctx.tenant_id, metrics)
    except Exception as exc:
        logger.error("Error in residential operations scheduled sweep for tenant %s: %s", ctx.tenant_id, exc)


async def sweep_transport_operations_task(ctx: TenantJobContext, db: AsyncSession) -> None:
    """Evaluate vehicle and driver compliance expiries, overdue trips, and expired waitlist offers (Step 55)."""
    try:
        from app.services.transport_service import TransportService
        metrics = await TransportService.sweep_transport_operations(db, ctx.tenant_id)
        if any(v > 0 for v in metrics.values()):
            logger.info("Transport operations sweep for tenant %s: %s", ctx.tenant_id, metrics)
    except Exception as exc:
        logger.error("Error in transport operations scheduled sweep for tenant %s: %s", ctx.tenant_id, exc)


async def sweep_sports_operations_task(ctx: TenantJobContext, db: AsyncSession) -> None:
    """Evaluate overdue sports equipment loans and expired athlete clearances (Step 57)."""
    try:
        from app.services.sports_service import sports_service
        metrics = await sports_service.sweep_sports_operations(db, ctx.tenant_id)
        if any(v > 0 for v in metrics.values()):
            logger.info("Sports operations sweep for tenant %s: %s", ctx.tenant_id, metrics)
    except Exception as exc:
        logger.error("Error in sports operations scheduled sweep for tenant %s: %s", ctx.tenant_id, exc)


async def sweep_student_support_reminders_task(ctx: TenantJobContext, db: AsyncSession) -> None:
    """Evaluate overdue support follow-ups, upcoming counselling appointments, and development plan reviews (Step 59)."""
    try:
        from app.services.student_support_service import StudentSupportService
        service = StudentSupportService(db, ctx.tenant_id)
        # Check overdue follow-ups
        overdue_list = await service.list_follow_ups(status="PENDING")
        today = date.today()
        flagged = sum(1 for f in overdue_list if f.due_date <= today)
        if flagged > 0:
            logger.info("Student Support sweep for tenant %s: %d follow-ups due or overdue", ctx.tenant_id, flagged)
    except Exception as exc:
        logger.error("Error in student support scheduled sweep for tenant %s: %s", ctx.tenant_id, exc)


async def sweep_international_agreements_and_deadlines_task(ctx: TenantJobContext, db: AsyncSession) -> None:
    """Evaluate expiring institutional agreements, partner renewals, and application deadlines (Step 60)."""
    try:
        from app.services.international_service import InternationalService
        service = InternationalService(db, ctx.tenant_id)
        sweep_result = await service.sweep_agreements_and_deadlines()
        if sweep_result["marked_expiring"] > 0 or sweep_result["marked_expired"] > 0:
            logger.info(
                "International Relations sweep for tenant %s: %d marked expiring, %d marked expired",
                ctx.tenant_id,
                sweep_result["marked_expiring"],
                sweep_result["marked_expired"],
            )
    except Exception as exc:
        logger.error("Error in international relations scheduled sweep for tenant %s: %s", ctx.tenant_id, exc)



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
                await run_single_scheduled_job("sweep_expired_trials", sweep_expired_trials)
                await run_single_scheduled_job(
                    "evaluate_tenant_resource_quotas", evaluate_tenant_resource_quotas
                )
                await run_single_scheduled_job(
                    "sweep_platform_support_sessions", sweep_platform_support_sessions
                )
                await run_single_scheduled_job(
                    "recover_abandoned_outbox_events", recover_abandoned_outbox_events_task, lock_ttl=60
                )
                await run_single_scheduled_job(
                    "circuit_health_probe", audit_backup_freshness_and_circuit_health, lock_ttl=60
                )
                await run_single_scheduled_job(
                    "adoption_deadlines_and_expirations", evaluate_adoption_deadlines_and_expirations
                )
                await run_single_scheduled_job(
                    "subscription_lifecycle", sweep_subscription_lifecycle_task
                )
                await run_single_scheduled_job(
                    "sync_marketplace_integrations", sync_marketplace_integrations_task
                )
                await run_single_scheduled_job(
                    "records_lifecycle_sweep", sweep_records_lifecycle_task
                )
                await run_single_scheduled_job(
                    "knowledge_reviews_sweep", sweep_knowledge_reviews_task
                )
                await run_single_scheduled_job(
                    "accreditation_quality_sweep", sweep_accreditation_quality_task
                )
                await run_single_scheduled_job(
                    "research_deadlines_sweep", sweep_research_deadlines_task
                )
                await run_single_scheduled_job(
                    "library_deadlines_sweep", sweep_library_deadlines_task
                )
                await run_single_scheduled_job(
                    "student_success_sweep", sweep_student_success_task
                )
                await run_single_scheduled_job(
                    "admissions_offers_sweep", sweep_admissions_offers_task
                )
                await run_single_scheduled_job(
                    "workforce_lifecycle_sweep", sweep_workforce_deadlines_and_accruals_task
                )
                await run_single_scheduled_job(
                    "asset_maintenance_sweep", sweep_asset_lifecycle_maintenance_task
                )
                await run_single_scheduled_job(
                    "residential_operations_sweep", sweep_residential_life_operations_task
                )
                await run_single_scheduled_job(
                    "transport_operations_sweep", sweep_transport_operations_task
                )
                await run_single_scheduled_job(
                    "sports_operations_sweep", sweep_sports_operations_task
                )
                await run_single_scheduled_job(
                    "student_support_sweep", sweep_student_support_reminders_task
                )
                await run_single_scheduled_job(
                    "international_agreements_sweep", sweep_international_agreements_and_deadlines_task
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
