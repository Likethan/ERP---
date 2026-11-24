"""Enterprise Analytics & Business Intelligence REST API (Step 28).

Provides authorized endpoints for:
- Metric catalogue introspection and metadata
- Pre-built executive and domain dashboards
- Multi-dimensional timeseries, breakdowns, and period comparisons
- Automated data-quality reconciliation findings
- Controlled historical backfill execution
- Secure export artifact generation
"""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_tenant_context, require_permission
from app.core.metric_registry import get_governed_metric
from app.core.permissions import (
    ANALYTICS_EXPORT_DOT,
    ANALYTICS_MANAGE_DOT,
    ANALYTICS_QUERY_DOT,
    ANALYTICS_READ_DOT,
    ANALYTICS_RECONCILE_DOT,
)
from app.core.tenant import TenantContext
from app.models.people import User
from app.schemas.analytics import (
    AnalyticsExportRequest,
    BackfillRequest,
    BackfillResponse,
    BreakdownRequest,
    BreakdownResponse,
    ComparisonRequest,
    ComparisonResponse,
    DashboardResponse,
    GovernedMetricRead,
    MetricFreshnessRead,
    ReconciliationFindingResponse,
    TimeseriesRequest,
    TimeseriesResponse,
)
from app.schemas.common import ApiResponse
from app.services.analytics_service import AnalyticsService
from app.services.data_quality_reconciliation_service import DataQualityReconciliationService

analytics_router = APIRouter(prefix="/analytics", tags=["Enterprise Analytics"])


# =============================================================================
# 1. METRIC CATALOGUE
# =============================================================================


@analytics_router.get(
    "/metrics",
    response_model=ApiResponse[list[GovernedMetricRead]],
    summary="List Governed Metric Catalogue",
)
async def list_metrics(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ANALYTICS_READ_DOT))],
    domain: str | None = Query(None, description="Filter by domain"),
):
    metrics = AnalyticsService.get_catalogue(domain)
    return ApiResponse(
        data=[
            GovernedMetricRead(
                metric_id=m.metric_id,
                display_name=m.display_name,
                description=m.description,
                owning_domain=m.owning_domain.value,
                formula_description=m.formula_description,
                aggregation_type=m.aggregation_type.value,
                data_type=m.data_type,
                unit=m.unit,
                supported_dimensions=list(m.supported_dimensions),
                supported_filters=list(m.supported_filters),
                required_permissions=list(m.required_permissions),
                refresh_strategy=m.refresh_strategy.value,
                freshness_expectation_seconds=m.freshness_expectation_seconds,
                version=m.version,
                is_active=m.is_active,
                is_sensitive=m.is_sensitive,
            )
            for m in metrics
        ]
    )


@analytics_router.get(
    "/metrics/{metric_id}",
    response_model=ApiResponse[GovernedMetricRead],
    summary="Get Governed Metric Definition",
)
async def get_metric_definition(
    metric_id: str,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ANALYTICS_READ_DOT))],
):
    m = get_governed_metric(metric_id)
    return ApiResponse(
        data=GovernedMetricRead(
            metric_id=m.metric_id,
            display_name=m.display_name,
            description=m.description,
            owning_domain=m.owning_domain.value,
            formula_description=m.formula_description,
            aggregation_type=m.aggregation_type.value,
            data_type=m.data_type,
            unit=m.unit,
            supported_dimensions=list(m.supported_dimensions),
            supported_filters=list(m.supported_filters),
            required_permissions=list(m.required_permissions),
            refresh_strategy=m.refresh_strategy.value,
            freshness_expectation_seconds=m.freshness_expectation_seconds,
            version=m.version,
            is_active=m.is_active,
            is_sensitive=m.is_sensitive,
        )
    )


# =============================================================================
# 2. DASHBOARD CONTRACTS
# =============================================================================


@analytics_router.get(
    "/dashboards/{dashboard_type}",
    response_model=ApiResponse[DashboardResponse],
    summary="Get Standardized Enterprise Dashboard",
)
async def get_dashboard(
    dashboard_type: str,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ANALYTICS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    start_date: date | None = Query(None, description="Start date for custom range"),
    end_date: date | None = Query(None, description="End date for custom range"),
    bypass_cache: bool = Query(False, description="Force fresh computation"),
):
    resp = await AnalyticsService.get_dashboard(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        dashboard_type=dashboard_type,
        start_date=start_date,
        end_date=end_date,
        bypass_cache=bypass_cache,
    )
    return ApiResponse(data=resp)


# =============================================================================
# 3. MULTI-DIMENSIONAL QUERIES & BREAKDOWNS
# =============================================================================


@analytics_router.post(
    "/timeseries",
    response_model=ApiResponse[TimeseriesResponse],
    summary="Query Metric Time-Series Points",
)
async def query_timeseries(
    req: TimeseriesRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ANALYTICS_QUERY_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    resp = await AnalyticsService.get_timeseries(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        req=req,
    )
    return ApiResponse(data=resp)


@analytics_router.post(
    "/breakdowns",
    response_model=ApiResponse[BreakdownResponse],
    summary="Query Grouped Dimensional Breakdown",
)
async def query_breakdown(
    req: BreakdownRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ANALYTICS_QUERY_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    resp = await AnalyticsService.get_breakdown(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        req=req,
    )
    return ApiResponse(data=resp)


@analytics_router.post(
    "/comparisons",
    response_model=ApiResponse[ComparisonResponse],
    summary="Compare Metric Across Time Periods",
)
async def query_comparison(
    req: ComparisonRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ANALYTICS_QUERY_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    resp = await AnalyticsService.get_comparison(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        req=req,
    )
    return ApiResponse(data=resp)


# =============================================================================
# 4. DATA FRESHNESS & QUALITY RECONCILIATION
# =============================================================================


@analytics_router.get(
    "/freshness",
    response_model=ApiResponse[list[MetricFreshnessRead]],
    summary="List Metric Freshness Status",
)
async def get_freshness_telemetry(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ANALYTICS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    rows = await AnalyticsService.list_freshness_status(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
    )
    return ApiResponse(data=rows)


@analytics_router.get(
    "/reconciliation",
    response_model=ApiResponse[list[ReconciliationFindingResponse]],
    summary="List Data Quality Reconciliation Findings",
)
async def list_reconciliation_findings(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ANALYTICS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status: str | None = Query(None, description="OPEN, RESOLVED, ACKNOWLEDGED"),
    severity: str | None = Query(None, description="INFO, WARNING, ERROR, CRITICAL"),
):
    findings = await DataQualityReconciliationService.list_findings(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        status=status,
        severity=severity,
    )
    return ApiResponse(
        data=[
            ReconciliationFindingResponse(
                id=f.id,
                rule_code=f.rule_code,
                severity=f.severity,
                metric_id=f.metric_id,
                source_table=f.source_table,
                operational_value=float(f.operational_value)
                if f.operational_value is not None
                else None,
                analytics_value=float(f.analytics_value) if f.analytics_value is not None else None,
                discrepancy_delta=float(f.discrepancy_delta)
                if f.discrepancy_delta is not None
                else None,
                details=f.details_json or {},
                resolution_status=f.resolution_status,
                detected_at=f.detected_at,
                resolved_at=f.resolved_at,
            )
            for f in findings
        ]
    )


@analytics_router.post(
    "/reconciliation/run",
    response_model=ApiResponse[list[ReconciliationFindingResponse]],
    summary="Trigger Automated Data Quality Reconciliation Run",
)
async def run_reconciliation(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ANALYTICS_RECONCILE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    findings = await DataQualityReconciliationService.run_tenant_reconciliation(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
    )
    return ApiResponse(
        data=[
            ReconciliationFindingResponse(
                id=f.id,
                rule_code=f.rule_code,
                severity=f.severity,
                metric_id=f.metric_id,
                source_table=f.source_table,
                operational_value=float(f.operational_value)
                if f.operational_value is not None
                else None,
                analytics_value=float(f.analytics_value) if f.analytics_value is not None else None,
                discrepancy_delta=float(f.discrepancy_delta)
                if f.discrepancy_delta is not None
                else None,
                details=f.details_json or {},
                resolution_status=f.resolution_status,
                detected_at=f.detected_at,
                resolved_at=f.resolved_at,
            )
            for f in findings
        ]
    )


# =============================================================================
# 5. CONTROLLED HISTORICAL BACKFILL
# =============================================================================


@analytics_router.post(
    "/backfill",
    response_model=ApiResponse[BackfillResponse],
    summary="Trigger Historical Analytics Backfill",
)
async def trigger_backfill(
    req: BackfillRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ANALYTICS_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    count = await AnalyticsService.run_backfill(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        start_date=req.start_date,
        end_date=req.end_date,
        metric_ids=req.metric_ids,
    )
    return ApiResponse(
        data=BackfillResponse(
            success=True,
            tenant_id=tenant_ctx.tenant_id,
            records_computed=count,
            message=f"Successfully backfilled {count} daily metrics records from {req.start_date} to {req.end_date}.",
        )
    )


# =============================================================================
# 6. CONTROLLED ANALYTICS DATA EXPORTS
# =============================================================================


@analytics_router.post(
    "/export",
    summary="Export Analytics Dataset as CSV or JSON",
)
async def export_analytics(
    req: AnalyticsExportRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ANALYTICS_EXPORT_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    import csv
    import io

    from app.core.exceptions import ValidationException
    from app.core.export_security import sanitize_csv_row

    fmt = req.format.upper().strip()
    if fmt not in ("CSV", "JSON"):
        raise ValidationException(f"Unsupported format '{req.format}'. Supported: CSV, JSON.")

    if req.export_type == "breakdown":
        breakdown_res = await AnalyticsService.get_breakdown(
            db=db,
            tenant_id=tenant_ctx.tenant_id,
            req=BreakdownRequest(
                metric_id=req.metric_id,
                dimension=req.dimension or "department",
                start_date=req.start_date,
                end_date=req.end_date,
                limit=req.limit,
            ),
        )
        if fmt == "JSON":
            content = breakdown_res.model_dump_json(indent=2)
            media_type = "application/json"
            ext = "json"
        else:
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Dimension", "Category", "Value", "RecordCount", "SharePct"])
            for itm in breakdown_res.items:
                row = sanitize_csv_row(
                    [itm.dimension, itm.category, itm.value, itm.record_count, itm.share_pct]
                )
                writer.writerow(row)
            content = output.getvalue()
            media_type = "text/csv"
            ext = "csv"
    else:
        # Default to timeseries
        ts_res = await AnalyticsService.get_timeseries(
            db=db,
            tenant_id=tenant_ctx.tenant_id,
            req=TimeseriesRequest(
                metric_id=req.metric_id,
                interval=req.interval,
                start_date=req.start_date,
                end_date=req.end_date,
                department_id=req.department_id,
                program_id=req.program_id,
                campus_id=req.campus_id,
            ),
        )
        if fmt == "JSON":
            content = ts_res.model_dump_json(indent=2)
            media_type = "application/json"
            ext = "json"
        else:
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Timestamp", "Date", "Value", "PreviousPeriodValue", "RecordCount"])
            for pt in ts_res.points:
                row = sanitize_csv_row(
                    [
                        pt.timestamp,
                        pt.date.isoformat(),
                        pt.value,
                        pt.previous_period_value or "",
                        pt.record_count,
                    ]
                )
                writer.writerow(row)
            content = output.getvalue()
            media_type = "text/csv"
            ext = "csv"

    filename = f"analytics_{req.metric_id}_{date.today().isoformat()}.{ext}"
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
