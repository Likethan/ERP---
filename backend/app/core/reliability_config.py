"""Configurable Enterprise Reliability Objectives & Service Criticality Definitions (Step 31).

Product Vision: "One Campus. One System. One Source of Truth."

Codifies operational objectives:
- Target Availability SLA
- Recovery Time Objectives (RTO) across service tiers
- Recovery Point Objectives (RPO) across storage domains
- Backup schedules & retention rules
- Maximum acceptable queue-processing delay
- Service criticality catalog with degraded mode mappings
"""

from datetime import UTC, datetime
from typing import Final

from app.schemas.reliability import (
    ReliabilityObjectivesResponse,
    ServiceCriticalityTier,
    ServiceReliabilityTierInfo,
)

# Target Availability SLA (excluding planned maintenance windows)
TARGET_AVAILABILITY_SLA_PERCENT: Final[float] = 99.9

# Recovery Time Objectives (Minutes)
RTO_TIER_1_MINUTES: Final[int] = 15    # Auth, Core Identity & Tenant Directory
RTO_TIER_2_MINUTES: Final[int] = 60    # Academic Records, Attendance, Exams, Finance
RTO_TIER_3_MINUTES: Final[int] = 240   # Analytics, AI Services, Notifications

# Recovery Point Objectives (Minutes / Hours)
RPO_DATABASE_MINUTES: Final[int] = 60  # Point-in-time / hourly snapshots
RPO_DOCUMENTS_HOURS: Final[int] = 24   # Object storage daily replication

# Operational Schedules
BACKUP_SCHEDULE_CRON: Final[str] = "0 2 * * *"  # Nightly at 02:00 UTC
BACKUP_FREQUENCY_DESCRIPTION: Final[str] = "Nightly automated full pg_dump at 02:00 UTC"
BACKUP_RETENTION_DAYS: Final[int] = 30
RESTORE_VERIFICATION_FREQUENCY: Final[str] = "Weekly automated restore test to isolated sandbox"

# Queue Lag Objectives
MAX_OUTBOX_QUEUE_DELAY_SECONDS: Final[int] = 300       # 5 minutes max latency
MAX_NOTIFICATION_QUEUE_DELAY_SECONDS: Final[int] = 60  # 1 minute max delivery buffer

# Service Criticality Catalog
SERVICE_CRITICALITY_CATALOG: Final[list[ServiceReliabilityTierInfo]] = [
    ServiceReliabilityTierInfo(
        service_name="Authentication & Authorization",
        criticality_tier=ServiceCriticalityTier.TIER_1_CRITICAL,
        rto_minutes=RTO_TIER_1_MINUTES,
        rpo_minutes=0,
        degraded_behavior="No degradation permitted; multi-replica failover required",
        must_remain_operational=True,
    ),
    ServiceReliabilityTierInfo(
        service_name="Core Institution & People Management",
        criticality_tier=ServiceCriticalityTier.TIER_1_CRITICAL,
        rto_minutes=RTO_TIER_1_MINUTES,
        rpo_minutes=RPO_DATABASE_MINUTES,
        degraded_behavior="Read-only fallback if write replicas unavailable",
        must_remain_operational=True,
    ),
    ServiceReliabilityTierInfo(
        service_name="Academic Records & Curricula",
        criticality_tier=ServiceCriticalityTier.TIER_2_ESSENTIAL,
        rto_minutes=RTO_TIER_2_MINUTES,
        rpo_minutes=RPO_DATABASE_MINUTES,
        degraded_behavior="Enrollment and grade entry deferred; cached catalog viewing",
        must_remain_operational=False,
    ),
    ServiceReliabilityTierInfo(
        service_name="Attendance & Examinations",
        criticality_tier=ServiceCriticalityTier.TIER_2_ESSENTIAL,
        rto_minutes=RTO_TIER_2_MINUTES,
        rpo_minutes=RPO_DATABASE_MINUTES,
        degraded_behavior="Offline/edge attendance sync queued; exam submission buffered",
        must_remain_operational=False,
    ),
    ServiceReliabilityTierInfo(
        service_name="Finance & Payment Records",
        criticality_tier=ServiceCriticalityTier.TIER_2_ESSENTIAL,
        rto_minutes=RTO_TIER_2_MINUTES,
        rpo_minutes=RPO_DATABASE_MINUTES,
        degraded_behavior="Strict idempotency enforcement; webhooks buffered in outbox; no blind retry",
        must_remain_operational=False,
    ),
    ServiceReliabilityTierInfo(
        service_name="Documents & Digital Records",
        criticality_tier=ServiceCriticalityTier.TIER_2_ESSENTIAL,
        rto_minutes=RTO_TIER_2_MINUTES,
        rpo_minutes=RPO_DOCUMENTS_HOURS * 60,
        degraded_behavior="Object storage errors return clean 503; db metadata retained",
        must_remain_operational=False,
    ),
    ServiceReliabilityTierInfo(
        service_name="Workflows & Domain Event Processing",
        criticality_tier=ServiceCriticalityTier.TIER_2_ESSENTIAL,
        rto_minutes=RTO_TIER_2_MINUTES,
        rpo_minutes=RPO_DATABASE_MINUTES,
        degraded_behavior="Outbox holds pending events durably; workers self-heal upon restart",
        must_remain_operational=False,
    ),
    ServiceReliabilityTierInfo(
        service_name="Notifications & External Integrations",
        criticality_tier=ServiceCriticalityTier.TIER_3_DEGRADABLE,
        rto_minutes=RTO_TIER_3_MINUTES,
        rpo_minutes=RPO_DATABASE_MINUTES,
        degraded_behavior="Circuit breaker trips on downstream failure; messages stay queued",
        must_remain_operational=False,
    ),
    ServiceReliabilityTierInfo(
        service_name="Analytics, Business Intelligence & AI",
        criticality_tier=ServiceCriticalityTier.TIER_3_DEGRADABLE,
        rto_minutes=RTO_TIER_3_MINUTES,
        rpo_minutes=RPO_DATABASE_MINUTES,
        degraded_behavior="AI provider returns 503; analytics displays last successful refresh time",
        must_remain_operational=False,
    ),
]


def get_reliability_objectives() -> ReliabilityObjectivesResponse:
    """Return the structured reliability objectives and service criticality catalog."""
    return ReliabilityObjectivesResponse(
        availability_sla_percent=TARGET_AVAILABILITY_SLA_PERCENT,
        rto_tier_1_minutes=RTO_TIER_1_MINUTES,
        rto_tier_2_minutes=RTO_TIER_2_MINUTES,
        rto_tier_3_minutes=RTO_TIER_3_MINUTES,
        rpo_database_minutes=RPO_DATABASE_MINUTES,
        rpo_documents_hours=RPO_DOCUMENTS_HOURS,
        backup_frequency=BACKUP_FREQUENCY_DESCRIPTION,
        backup_retention_days=BACKUP_RETENTION_DAYS,
        restore_verification_frequency=RESTORE_VERIFICATION_FREQUENCY,
        max_outbox_queue_delay_seconds=MAX_OUTBOX_QUEUE_DELAY_SECONDS,
        max_notification_queue_delay_seconds=MAX_NOTIFICATION_QUEUE_DELAY_SECONDS,
        services=SERVICE_CRITICALITY_CATALOG,
    )


def evaluate_backup_freshness(last_backup_time: datetime | None) -> tuple[str, float | None]:
    """Evaluate backup age against RPO policy.

    Returns:
        (freshness_status, age_hours)
        - FRESH: backup completed within 26 hours (daily schedule + 2h margin)
        - WARNING: backup between 26 and 48 hours old
        - CRITICAL: backup older than 48 hours
        - NO_BACKUPS: no successful backups recorded
    """
    if last_backup_time is None:
        return "NO_BACKUPS", None

    now = datetime.now(UTC)
    if last_backup_time.tzinfo is None:
        last_backup_time = last_backup_time.replace(tzinfo=UTC)

    age_hours = (now - last_backup_time).total_seconds() / 3600.0

    if age_hours <= 26.0:
        return "FRESH", round(age_hours, 2)
    elif age_hours <= 48.0:
        return "WARNING", round(age_hours, 2)
    else:
        return "CRITICAL", round(age_hours, 2)
