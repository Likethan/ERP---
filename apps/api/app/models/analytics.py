"""Enterprise Analytics & Business Intelligence Domain Models for CampusOS (Step 28).

Defines persistence structures for:
1. AnalyticsDailyMetric: Tenant-partitioned rollup & aggregate metrics by date & dimension.
2. AnalyticsMetricFreshness: Ingestion lag, last recalculation, and freshness status.
3. AnalyticsReconciliationFinding: Data-quality and reconciliation variance findings.
"""

from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    Date,
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TenantScopedModel


class MetricFreshnessStatus(StrEnum):
    FRESH = "FRESH"
    UPDATING = "UPDATING"
    STALE = "STALE"
    RECONCILING = "RECONCILING"
    ERROR = "ERROR"


class ReconciliationSeverity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ReconciliationStatus(StrEnum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    IGNORED = "IGNORED"


class AnalyticsDailyMetric(TenantScopedModel):
    """Daily rolled up aggregate metrics partitioned by tenant, metric, and dimension."""

    __tablename__ = "analytics_daily_metrics"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "metric_id",
            "metric_date",
            "dimension_type",
            "dimension_value",
            name="uq_analytics_daily_metric_slot",
        ),
        Index("ix_analytics_daily_tenant_metric_date", "tenant_id", "metric_id", "metric_date"),
        Index("ix_analytics_daily_dimension", "tenant_id", "dimension_type", "dimension_value"),
    )

    metric_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    metric_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    dimension_type: Mapped[str] = mapped_column(String(64), nullable=False, default="GLOBAL")
    dimension_value: Mapped[str] = mapped_column(String(128), nullable=False, default="ALL")
    value_numeric: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), nullable=False, default=Decimal("0.0000")
    )
    record_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)


class AnalyticsMetricFreshness(TenantScopedModel):
    """Tracks ingestion telemetry, last calculation time, and data freshness."""

    __tablename__ = "analytics_metric_freshness"
    __table_args__ = (
        UniqueConstraint("tenant_id", "metric_id", name="uq_analytics_metric_freshness"),
        Index("ix_analytics_freshness_tenant_status", "tenant_id", "status"),
    )

    metric_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    last_ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    last_recalculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    ingestion_lag_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source_event_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=MetricFreshnessStatus.FRESH,
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)


class AnalyticsReconciliationFinding(TenantScopedModel):
    """Audit and data-quality variance findings between operational source records and analytics."""

    __tablename__ = "analytics_reconciliation_findings"
    __table_args__ = (
        Index("ix_analytics_recon_tenant_severity", "tenant_id", "severity"),
        Index("ix_analytics_recon_tenant_status", "tenant_id", "resolution_status"),
        Index("ix_analytics_recon_rule_detected", "tenant_id", "rule_code", "detected_at"),
    )

    rule_code: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(
        String(16), nullable=False, default=ReconciliationSeverity.WARNING
    )
    metric_id: Mapped[str] = mapped_column(String(64), nullable=False)
    source_table: Mapped[str] = mapped_column(String(64), nullable=False)
    operational_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    analytics_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    discrepancy_delta: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    details_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    resolution_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=ReconciliationStatus.OPEN
    )
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
