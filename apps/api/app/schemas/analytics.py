"""Enterprise Analytics & Business Intelligence Pydantic Schemas (Step 28).

Defines presentation contracts, dashboard structures, metric discovery catalogues,
reconciliation models, and time-series query structures consumed by CampusOS dashboards.
"""

from datetime import date, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DashboardType(StrEnum):
    EXECUTIVE_OVERVIEW = "EXECUTIVE_OVERVIEW"
    ACADEMIC_PERFORMANCE = "ACADEMIC_PERFORMANCE"
    STUDENT_LIFECYCLE = "STUDENT_LIFECYCLE"
    ATTENDANCE_ENGAGEMENT = "ATTENDANCE_ENGAGEMENT"
    EXAMINATION_OUTCOMES = "EXAMINATION_OUTCOMES"
    FINANCE_COLLECTIONS = "FINANCE_COLLECTIONS"
    PLACEMENT_OUTCOMES = "PLACEMENT_OUTCOMES"
    CAMPUS_OPERATIONS = "CAMPUS_OPERATIONS"
    WORKFLOW_SYSTEM_HEALTH = "WORKFLOW_SYSTEM_HEALTH"


class TrendDirection(StrEnum):
    UP = "UP"
    DOWN = "DOWN"
    FLAT = "FLAT"


class KpiCard(BaseModel):
    metric_id: str
    label: str
    value: float | int | str
    unit: str | None = None
    previous_value: float | int | str | None = None
    change_pct: float | None = None
    trend_direction: TrendDirection = TrendDirection.FLAT
    description: str | None = None


class TimeseriesPoint(BaseModel):
    timestamp: str
    date: date
    value: float
    previous_period_value: float | None = None
    record_count: int = 0


class CategoryBreakdown(BaseModel):
    dimension: str
    category: str
    value: float
    record_count: int | str  # May be "<5" if masked for small-cell privacy
    share_pct: float


class DataFreshnessInfo(BaseModel):
    last_updated_at: datetime
    is_realtime: bool = True
    lag_seconds: int = 0
    status: str = "FRESH"


class DashboardResponse(BaseModel):
    dashboard_type: str
    title: str
    period_label: str
    kpis: list[KpiCard]
    charts: dict[str, list[TimeseriesPoint]] = Field(default_factory=dict)
    breakdowns: dict[str, list[CategoryBreakdown]] = Field(default_factory=dict)
    freshness: DataFreshnessInfo
    quality_warnings: list[str] = Field(default_factory=list)


class TimeseriesRequest(BaseModel):
    metric_id: str
    interval: str = Field("day", description="'day', 'week', or 'month'")
    start_date: date | None = None
    end_date: date | None = None
    department_id: UUID | None = None
    program_id: UUID | None = None
    campus_id: UUID | None = None


class TimeseriesResponse(BaseModel):
    metric_id: str
    display_name: str
    unit: str | None = None
    interval: str
    points: list[TimeseriesPoint]


class BreakdownRequest(BaseModel):
    metric_id: str
    dimension: str = Field(..., description="'department', 'program', 'campus', 'status'")
    start_date: date | None = None
    end_date: date | None = None
    limit: int = Field(50, ge=1, le=100)


class BreakdownResponse(BaseModel):
    metric_id: str
    dimension: str
    items: list[CategoryBreakdown]


class ComparisonRequest(BaseModel):
    metric_id: str
    period_a_start: date
    period_a_end: date
    period_b_start: date
    period_b_end: date


class ComparisonResponse(BaseModel):
    metric_id: str
    period_a_label: str
    period_a_value: float
    period_b_label: str
    period_b_value: float
    delta: float
    change_pct: float | None = None


class GovernedMetricRead(BaseModel):
    metric_id: str
    display_name: str
    description: str
    owning_domain: str
    formula_description: str
    aggregation_type: str
    data_type: str
    unit: str | None = None
    supported_dimensions: list[str]
    supported_filters: list[str]
    required_permissions: list[str]
    refresh_strategy: str
    freshness_expectation_seconds: int
    version: str
    is_active: bool
    is_sensitive: bool


class MetricFreshnessRead(BaseModel):
    metric_id: str
    last_ingested_at: datetime
    last_recalculated_at: datetime
    ingestion_lag_seconds: int
    source_event_count: int
    status: str
    last_error: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ReconciliationFindingResponse(BaseModel):
    id: UUID
    rule_code: str
    severity: str
    metric_id: str
    source_table: str
    operational_value: float | None = None
    analytics_value: float | None = None
    discrepancy_delta: float | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    resolution_status: str
    detected_at: datetime
    resolved_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class BackfillRequest(BaseModel):
    start_date: date
    end_date: date
    metric_ids: list[str] | None = None


class BackfillResponse(BaseModel):
    success: bool
    tenant_id: UUID
    records_computed: int
    message: str


class AnalyticsExportRequest(BaseModel):
    export_type: str = Field("timeseries", description="'timeseries' or 'breakdown'")
    metric_id: str
    format: str = Field("CSV", description="'CSV' or 'JSON'")
    # Timeseries parameters:
    interval: str = "day"
    start_date: date | None = None
    end_date: date | None = None
    department_id: UUID | None = None
    program_id: UUID | None = None
    campus_id: UUID | None = None
    # Breakdown parameters:
    dimension: str = "department"
    limit: int = Field(50, ge=1, le=100)
