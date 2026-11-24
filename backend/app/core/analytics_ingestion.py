"""Enterprise Analytics Ingestion Pipeline & Event Consumer (Step 28).

Integrates with Step 27 Domain Event Backbone to provide idempotent, near-real-time
analytical rollups and freshness tracking without duplicate counting or operational table locks.
"""

import logging
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import TenantIsolatedCache
from app.core.event_consumer import (
    BaseDomainEventConsumer,
    ConsumerRegistry,
    ConsumerResult,
)
from app.core.events import DomainEventEnvelope, normalize_event_type
from app.models.analytics import (
    AnalyticsDailyMetric,
    AnalyticsMetricFreshness,
    MetricFreshnessStatus,
)
from app.models.event import ConsumerCheckpointStatus

logger = logging.getLogger("campusos.analytics.ingestion")

# Module cache instance
_cache = TenantIsolatedCache()


# Mapping of event types to affected metric IDs
EVENT_METRIC_MAP: dict[str, list[str]] = {
    "student.enrollment.created": [
        "total_active_students",
        "student_enrollment_trend",
        "enrollment_completion_rate",
    ],
    "STUDENT_ENROLLED": [
        "total_active_students",
        "student_enrollment_trend",
        "enrollment_completion_rate",
    ],
    "attendance.session.finalized": [
        "attendance_percentage",
        "session_completion_rate",
        "attendance_trend",
    ],
    "ATTENDANCE_MARKED": [
        "attendance_percentage",
        "session_completion_rate",
        "attendance_trend",
    ],
    "attendance.low_threshold": [
        "low_attendance_count",
    ],
    "ATTENDANCE_THRESHOLD_REACHED": [
        "low_attendance_count",
    ],
    "examination.results.published": [
        "pass_percentage",
        "average_examination_score",
        "results_publication_status",
        "grade_distribution_summary",
    ],
    "EXAM_RESULT_PUBLISHED": [
        "pass_percentage",
        "average_examination_score",
        "results_publication_status",
        "grade_distribution_summary",
    ],
    "finance.payment.confirmed": [
        "confirmed_collections",
        "total_outstanding",
        "fee_collection_rate",
    ],
    "PAYMENT_RECEIVED": [
        "confirmed_collections",
        "total_outstanding",
        "fee_collection_rate",
    ],
    "placement.offer.created": [
        "placement_offers",
        "placed_students",
        "placement_rate",
        "average_salary_package",
    ],
    "PLACEMENT_OFFER_ACCEPTED": [
        "placement_offers",
        "placed_students",
        "placement_rate",
        "average_salary_package",
    ],
    "document.certificate.issued": [
        "certificate_issuance_rate",
    ],
    "CERTIFICATE_ISSUED": [
        "certificate_issuance_rate",
    ],
    "workflow.case.completed": [
        "workflow_throughput_rate",
    ],
    "CASE_COMPLETED": [
        "workflow_throughput_rate",
    ],
}


class AnalyticsIngestionConsumer(BaseDomainEventConsumer):
    """Consumer that receives committed domain events and updates analytics rollups and freshness."""

    @property
    def consumer_name(self) -> str:
        return "AnalyticsIngestionConsumer"

    @property
    def supported_event_types(self) -> list[str]:
        return list(EVENT_METRIC_MAP.keys())

    async def handle(self, db: AsyncSession, envelope: DomainEventEnvelope) -> ConsumerResult:
        ev_norm = envelope.event_type
        affected_metrics = EVENT_METRIC_MAP.get(ev_norm, [])
        if not affected_metrics:
            # Check normalized
            try:
                canon = normalize_event_type(ev_norm)
                affected_metrics = EVENT_METRIC_MAP.get(canon.value, [])
            except Exception:
                pass

        if not affected_metrics:
            return ConsumerResult(status=ConsumerCheckpointStatus.COMPLETED)

        now = datetime.now(UTC)
        occurred = (
            getattr(envelope, "event_timestamp", None)
            or getattr(envelope, "occurred_at", None)
            or now
        )
        event_date = occurred.date()
        tenant_id = envelope.tenant_id
        payload = envelope.payload or {}

        try:
            # 1. Update Metric Freshness for all affected metrics
            for metric_id in affected_metrics:
                freshness_stmt = select(AnalyticsMetricFreshness).where(
                    and_(
                        AnalyticsMetricFreshness.tenant_id == tenant_id,
                        AnalyticsMetricFreshness.metric_id == metric_id,
                    )
                )
                res = await db.execute(freshness_stmt)
                freshness = res.scalar_one_or_none()

                if not freshness:
                    freshness = AnalyticsMetricFreshness(
                        tenant_id=tenant_id,
                        metric_id=metric_id,
                        last_ingested_at=now,
                        last_recalculated_at=now,
                        ingestion_lag_seconds=max(0, int((now - occurred).total_seconds())),
                        source_event_count=1,
                        status=MetricFreshnessStatus.FRESH,
                    )
                    db.add(freshness)
                else:
                    freshness.last_ingested_at = now
                    freshness.last_recalculated_at = now
                    freshness.source_event_count += 1
                    freshness.ingestion_lag_seconds = max(0, int((now - occurred).total_seconds()))
                    freshness.status = MetricFreshnessStatus.FRESH

            # 2. Increment Daily Rollups
            await self._increment_daily_rollups(db, tenant_id, ev_norm, event_date, payload)

            # 3. Invalidate Tenant Analytics Cache
            await _cache.invalidate_namespace(tenant_id, "analytics")
            await _cache.invalidate_namespace(tenant_id, "dashboard")

            return ConsumerResult(
                status=ConsumerCheckpointStatus.COMPLETED,
                metadata={
                    "affected_metrics": affected_metrics,
                    "event_date": event_date.isoformat(),
                },
            )
        except Exception as exc:
            logger.error(
                "Analytics ingestion failed for event %s (tenant %s): %s",
                envelope.event_id,
                tenant_id,
                exc,
                exc_info=True,
            )
            return ConsumerResult(
                status=ConsumerCheckpointStatus.FAILED,
                error_message=str(exc),
                is_retryable=True,
            )

    async def _increment_daily_rollups(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        event_type: str,
        event_date: date,
        payload: dict[str, Any],
    ) -> None:
        """Increment daily aggregation metrics based on specific event data."""
        # Determine delta values
        metric_deltas: list[tuple[str, Decimal, int]] = []

        if "payment" in event_type or "PAYMENT" in event_type:
            raw_amt = payload.get("amount", 0)
            try:
                amt = Decimal(str(raw_amt))
            except Exception:
                amt = Decimal("0.00")
            metric_deltas.append(("confirmed_collections", amt, 1))

        elif "enrollment" in event_type or "ENROLLED" in event_type:
            metric_deltas.append(("student_enrollment_trend", Decimal("1.00"), 1))

        elif "offer" in event_type or "OFFER" in event_type:
            metric_deltas.append(("placement_offers", Decimal("1.00"), 1))
            metric_deltas.append(("placed_students", Decimal("1.00"), 1))

        elif "certificate" in event_type or "CERTIFICATE" in event_type:
            metric_deltas.append(("certificate_issuance_rate", Decimal("1.00"), 1))

        elif "case" in event_type or "CASE" in event_type:
            metric_deltas.append(("workflow_throughput_rate", Decimal("1.00"), 1))

        elif "attendance" in event_type or "ATTENDANCE" in event_type:
            metric_deltas.append(("session_completion_rate", Decimal("1.00"), 1))

        # Upsert into AnalyticsDailyMetric
        for metric_id, delta_val, count_inc in metric_deltas:
            stmt = select(AnalyticsDailyMetric).where(
                and_(
                    AnalyticsDailyMetric.tenant_id == tenant_id,
                    AnalyticsDailyMetric.metric_id == metric_id,
                    AnalyticsDailyMetric.metric_date == event_date,
                    AnalyticsDailyMetric.dimension_type == "GLOBAL",
                    AnalyticsDailyMetric.dimension_value == "ALL",
                )
            )
            res = await db.execute(stmt)
            rollup = res.scalar_one_or_none()

            if not rollup:
                rollup = AnalyticsDailyMetric(
                    tenant_id=tenant_id,
                    metric_id=metric_id,
                    metric_date=event_date,
                    dimension_type="GLOBAL",
                    dimension_value="ALL",
                    value_numeric=delta_val,
                    record_count=count_inc,
                    metadata_json={"last_increment": str(delta_val)},
                )
                db.add(rollup)
            else:
                rollup.value_numeric = rollup.value_numeric + delta_val
                rollup.record_count += count_inc


# Auto-register consumer with Step 27 ConsumerRegistry
ConsumerRegistry.register(AnalyticsIngestionConsumer())
