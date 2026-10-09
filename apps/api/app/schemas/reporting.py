"""Reporting & Analytics Pydantic Request/Response Schemas for CampusOS."""

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FilterCondition(BaseModel):
    field: str = Field(..., description="Approved dataset dimension or attribute name")
    operator: str = Field(..., description="Comparison operator (=, !=, >, <, IN, BETWEEN, etc.)")
    value: Any = Field(None, description="Literal comparison value, list, or range")


class DateRangeFilter(BaseModel):
    preset: str | None = Field(
        None,
        description="Named date range preset: today, yesterday, this_week, this_month, last_30_days, last_90_days, custom",
    )
    start_date: date | None = Field(None, description="Start date for custom ranges (inclusive)")
    end_date: date | None = Field(None, description="End date for custom ranges (inclusive)")


class AcademicPeriodFilter(BaseModel):
    academic_year_id: UUID | None = None
    semester_id: UUID | None = None
    department_id: UUID | None = None
    program_id: UUID | None = None


class QuerySpecification(BaseModel):
    dataset: str = Field(..., description="Canonical dataset identifier (e.g. attendance, finance)")
    dimensions: list[str] = Field(default_factory=list, description="Categorical grouping dimensions")
    measures: list[str] = Field(..., min_length=1, description="Approved metrics to compute")
    filters: list[FilterCondition] = Field(default_factory=list, description="Filtering criteria")
    date_range: DateRangeFilter | None = None
    academic_period: AcademicPeriodFilter | None = None
    sort_by: str | None = None
    sort_desc: bool = False
    limit: int = Field(50, ge=1, le=10000, description="Max rows to return")
    offset: int = Field(0, ge=0, description="Pagination offset")


class ReportCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=128)
    description: str | None = None
    domain: str = Field(..., description="PEOPLE, ACADEMICS, ATTENDANCE, EXAMINATIONS, FINANCE, PLACEMENT, CAMPUS, INFRASTRUCTURE, DOCUMENTS, CROSS_DOMAIN")
    category: str = Field("OPERATIONAL", max_length=64)
    visibility: str = Field("ROLE", description="PRIVATE, ROLE, TENANT, SYSTEM")
    allowed_roles: list[str] = Field(default_factory=list)
    query_spec: QuerySpecification


class ReportUpdate(BaseModel):
    name: str | None = Field(None, min_length=3, max_length=128)
    description: str | None = None
    visibility: str | None = None
    allowed_roles: list[str] | None = None
    query_spec: QuerySpecification | None = None
    change_summary: str | None = Field(None, max_length=255)


class ReportVersionRead(BaseModel):
    id: UUID
    version_number: int
    change_summary: str | None
    query_spec_json: dict[str, Any]
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReportRead(BaseModel):
    id: UUID
    tenant_id: UUID | None
    name: str
    code: str
    description: str | None
    domain: str
    category: str
    status: str
    visibility: str
    is_system: bool
    allowed_roles: list[str]
    active_version: int
    active_version_id: UUID | None
    created_at: datetime
    updated_at: datetime
    versions: list[ReportVersionRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ReportExecutionRead(BaseModel):
    id: UUID
    tenant_id: UUID
    report_id: UUID | None
    report_version_id: UUID | None
    requested_by_user_id: UUID | None
    status: str
    row_count: int
    execution_time_ms: int
    error_code: str | None
    error_message: str | None
    correlation_id: str
    is_snapshot: bool
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReportExportRead(BaseModel):
    id: UUID
    tenant_id: UUID
    execution_id: UUID
    export_format: str
    storage_key: str
    filename: str
    mime_type: str
    file_size_bytes: int
    download_count: int
    expires_at: datetime
    created_at: datetime
    download_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class SavedReportCreate(BaseModel):
    report_id: UUID | None = None
    name: str = Field(..., min_length=3, max_length=128)
    description: str | None = None
    query_spec: QuerySpecification
    is_favorite: bool = False


class SavedReportRead(BaseModel):
    id: UUID
    tenant_id: UUID
    user_id: UUID
    report_id: UUID | None
    name: str
    description: str | None
    query_spec_json: dict[str, Any]
    is_favorite: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DatasetRead(BaseModel):
    dataset_id: str
    name: str
    domain: str
    description: str
    primary_entity: str
    allowed_dimensions: list[str]
    allowed_measures: list[str]
    allowed_filters: list[str]


class MetricRead(BaseModel):
    name: str
    label: str
    formula: str
    aggregation: str
    data_type: str
    description: str
    unit: str | None = None
    default_chart_type: str = "bar"


class DimensionRead(BaseModel):
    name: str
    label: str
    field_type: str
    description: str
    is_filterable: bool
    is_groupable: bool


class ChartSeries(BaseModel):
    name: str
    data: list[Any]
    color: str | None = "#4f46e5"


class TableData(BaseModel):
    headers: list[str]
    rows: list[list[Any]]
    total_rows: int = 0


class SourceProvenance(BaseModel):
    dataset: str
    measures: list[str]
    dimensions: list[str]
    reporting_period: str
    generated_at: str
    data_as_of: str
    tenant_id: str


class AnalyticsQueryResult(BaseModel):
    query: QuerySpecification
    title: str
    summary: str
    chart_type: str
    labels: list[str]
    datasets: list[ChartSeries]
    table_data: TableData
    provenance: SourceProvenance
    cached: bool = False
