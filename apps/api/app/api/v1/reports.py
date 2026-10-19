"""Enterprise Reporting & Analytics REST API Endpoints.

Provides tenant-partitioned, permission-governed reporting services:
- Report Definition CRUD & Version History
- Controlled Execution Engine with Caching and Snapshots
- Export Artifact Generation (CSV, XLSX, JSON) with formula injection protection
- Dataset, Metric, and Dimension Registries Introspection
- Ad-hoc Cross-Domain Analytics Queries
"""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_tenant_context, require_permission
from app.core.permissions import (
    ANALYTICS_EXPORT_DOT,
    ANALYTICS_QUERY_DOT,
    ANALYTICS_READ_DOT,
    REPORTS_CREATE_DOT,
    REPORTS_DELETE_DOT,
    REPORTS_EXECUTE_DOT,
    REPORTS_EXPORT_DOT,
    REPORTS_READ_DOT,
    REPORTS_UPDATE_DOT,
)
from app.core.reporting_registry import (
    DATASET_REGISTRY,
    DIMENSION_REGISTRY,
    METRIC_REGISTRY,
)
from app.core.tenant import TenantContext
from app.models.people import User
from app.schemas.common import ApiResponse, PaginatedMeta, PaginatedResponse
from app.schemas.reporting import (
    AnalyticsQueryResult,
    DatasetRead,
    DimensionRead,
    MetricRead,
    QuerySpecification,
    ReportCreate,
    ReportExecutionRead,
    ReportExportRead,
    ReportRead,
    ReportUpdate,
    ReportVersionRead,
    SavedReportCreate,
    SavedReportRead,
)
from app.services.report_export_service import ReportExportService
from app.services.reporting_service import ReportingService

reports_router = APIRouter(tags=["Reporting & Analytics"])


# =============================================================================
# 1. REPORT DEFINITIONS & VERSIONING
# =============================================================================

@reports_router.get(
    "/reports",
    response_model=PaginatedResponse[ReportRead],
    summary="List Report Definitions",
)
async def list_reports(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(REPORTS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    domain: str | None = Query(None, description="Filter by domain"),
    status: str | None = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    offset = (page - 1) * page_size
    items, total = await ReportingService.list_reports(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        domain=domain,
        status=status,
        limit=page_size,
        offset=offset,
    )
    total_pages = (total + page_size - 1) // page_size if total else 0
    return PaginatedResponse(
        data=[ReportRead.model_validate(r) for r in items],
        pagination=PaginatedMeta(
            page=page,
            page_size=page_size,
            total_records=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
    )


@reports_router.post(
    "/reports",
    response_model=ApiResponse[ReportRead],
    status_code=status.HTTP_201_CREATED,
    summary="Create Report Definition",
)
async def create_report(
    payload: ReportCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(REPORTS_CREATE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    report = await ReportingService.create_report(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        payload=payload,
        actor_id=current_user.id,
    )
    return ApiResponse(data=ReportRead.model_validate(report))


@reports_router.get(
    "/reports/{report_id}",
    response_model=ApiResponse[ReportRead],
    summary="Get Report Definition",
)
async def get_report(
    report_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(REPORTS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    report = await ReportingService.get_report(db, tenant_ctx.tenant_id, report_id)
    return ApiResponse(data=ReportRead.model_validate(report))


@reports_router.patch(
    "/reports/{report_id}",
    response_model=ApiResponse[ReportRead],
    summary="Update Report Definition or Query Spec",
)
async def update_report(
    report_id: UUID,
    payload: ReportUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(REPORTS_UPDATE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    report = await ReportingService.update_report(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        report_id=report_id,
        payload=payload,
        actor_id=current_user.id,
    )
    return ApiResponse(data=ReportRead.model_validate(report))


@reports_router.get(
    "/reports/{report_id}/versions",
    response_model=ApiResponse[list[ReportVersionRead]],
    summary="Get Report Version History",
)
async def get_report_versions(
    report_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(REPORTS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    report = await ReportingService.get_report(db, tenant_ctx.tenant_id, report_id)
    return ApiResponse(data=[ReportVersionRead.model_validate(v) for v in report.versions])


# =============================================================================
# 2. REPORT EXECUTION & SNAPSHOTS
# =============================================================================

from app.core.config import settings
from app.core.exceptions import CampusOSException
from app.core.rate_limiter import rate_limiter

@reports_router.post(
    "/reports/{report_id}/execute",
    response_model=ApiResponse[dict[str, Any]],
    summary="Execute Report (Synchronous or Snapshot)",
)
async def execute_report(
    report_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(REPORTS_EXECUTE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    version: int | None = Query(None, description="Specific version number to execute"),
    bypass_cache: bool = Query(False, description="Force fresh recalculation"),
    is_snapshot: bool = Query(False, description="Persist result as immutable audit snapshot"),
):
    if not rate_limiter.acquire_report_slot(tenant_ctx.tenant_id):
        raise CampusOSException(
            code="CONCURRENT_REPORTS_EXCEEDED",
            message=(
                f"Tenant has reached the maximum limit of {settings.TENANT_CONCURRENT_REPORTS_LIMIT} "
                "concurrent report executions. Please retry once active reports complete."
            ),
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )
    try:
        result, execution = await ReportingService.execute_report(
            db=db,
            tenant_id=tenant_ctx.tenant_id,
            report_id=report_id,
            user=current_user,
            version_number=version,
            bypass_cache=bypass_cache,
            is_snapshot=is_snapshot,
        )
        return ApiResponse(
            data={
                "execution": ReportExecutionRead.model_validate(execution),
                "result": result.model_dump(),
            }
        )
    finally:
        rate_limiter.release_report_slot(tenant_ctx.tenant_id)


@reports_router.get(
    "/report-executions/{execution_id}",
    response_model=ApiResponse[ReportExecutionRead],
    summary="Get Report Execution Status",
)
async def get_execution_status(
    execution_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(REPORTS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    from sqlalchemy import and_, select
    from app.core.exceptions import NotFoundException
    from app.models.reporting import ReportExecution
    stmt = select(ReportExecution).where(
        and_(
            ReportExecution.id == execution_id,
            ReportExecution.tenant_id == tenant_ctx.tenant_id,
        )
    )
    execution = (await db.execute(stmt)).scalar_one_or_none()
    if not execution:
        raise NotFoundException("ReportExecution", execution_id)
    return ApiResponse(data=ReportExecutionRead.model_validate(execution))


@reports_router.post(
    "/report-executions/{execution_id}/cancel",
    response_model=ApiResponse[ReportExecutionRead],
    summary="Cancel Report Execution",
)
async def cancel_execution(
    execution_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(REPORTS_UPDATE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    cancelled = await ReportingService.cancel_execution(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        execution_id=execution_id,
        actor_id=current_user.id,
    )
    return ApiResponse(data=ReportExecutionRead.model_validate(cancelled))


# =============================================================================
# 3. EXPORTS & DOWNLOADS
# =============================================================================

@reports_router.post(
    "/report-executions/{execution_id}/export",
    response_model=ApiResponse[ReportExportRead],
    status_code=status.HTTP_201_CREATED,
    summary="Generate Export Artifact (CSV, XLSX, JSON)",
)
async def create_export(
    execution_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(REPORTS_EXPORT_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    export_format: str = Query("CSV", description="Export format: CSV, XLSX, JSON"),
):
    from sqlalchemy import and_, select
    from app.core.exceptions import NotFoundException
    from app.models.reporting import ReportExecution
    stmt = select(ReportExecution).where(
        and_(
            ReportExecution.id == execution_id,
            ReportExecution.tenant_id == tenant_ctx.tenant_id,
        )
    )
    execution = (await db.execute(stmt)).scalar_one_or_none()
    if not execution:
        raise NotFoundException("ReportExecution", execution_id)

    # Re-run query specification or load snapshot data to produce export
    query_spec = QuerySpecification(**execution.query_spec_snapshot)
    result = await ReportingService.execute_adhoc_query(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        user=current_user,
        spec=query_spec,
    )

    export = await ReportExportService.create_export(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        execution=execution,
        result_data=result[0],
        export_format=export_format,
    )
    export_dto = ReportExportRead.model_validate(export)
    export_dto.download_url = f"/api/v1/report-exports/{export.id}/download"
    return ApiResponse(data=export_dto)


@reports_router.get(
    "/report-exports/{export_id}/download",
    summary="Download Export File Artifact",
)
async def download_export_file(
    export_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(REPORTS_EXPORT_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    content, export = await ReportExportService.get_export_file(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        export_id=export_id,
    )
    return Response(
        content=content,
        media_type=export.mime_type,
        headers={"Content-Disposition": f'attachment; filename="{export.filename}"'},
    )


# =============================================================================
# 4. USER SAVED REPORTS
# =============================================================================

@reports_router.get(
    "/reports/saved",
    response_model=ApiResponse[list[SavedReportRead]],
    summary="List Saved Reports for User",
)
async def list_saved_reports(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(REPORTS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    saved = await ReportingService.list_saved_reports(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        user_id=current_user.id,
    )
    return ApiResponse(data=[SavedReportRead.model_validate(s) for s in saved])


@reports_router.post(
    "/reports/saved",
    response_model=ApiResponse[SavedReportRead],
    status_code=status.HTTP_201_CREATED,
    summary="Save Report Configuration",
)
async def save_user_report(
    payload: SavedReportCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(REPORTS_CREATE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    saved = await ReportingService.save_user_report(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        user_id=current_user.id,
        payload=payload,
    )
    return ApiResponse(data=SavedReportRead.model_validate(saved))


# =============================================================================
# 5. REGISTRY INTROSPECTION
# =============================================================================

@reports_router.get(
    "/datasets",
    response_model=ApiResponse[list[DatasetRead]],
    summary="List Authorized Datasets",
)
async def list_datasets(
    current_user: Annotated[User, Depends(require_permission(REPORTS_READ_DOT))],
):
    items = [
        DatasetRead(
            dataset_id=ds.dataset_id,
            name=ds.name,
            domain=ds.domain,
            description=ds.description,
            primary_entity=ds.primary_entity,
            allowed_dimensions=list(ds.allowed_dimensions),
            allowed_measures=list(ds.allowed_measures),
            allowed_filters=list(ds.allowed_filters),
        )
        for ds in DATASET_REGISTRY.values()
    ]
    return ApiResponse(data=items)


@reports_router.get(
    "/metrics",
    response_model=ApiResponse[list[MetricRead]],
    summary="List Authoritative Metrics",
)
async def list_metrics(
    current_user: Annotated[User, Depends(require_permission(REPORTS_READ_DOT))],
):
    items = [
        MetricRead(
            name=m.name,
            label=m.label,
            formula=m.formula,
            aggregation=m.aggregation,
            data_type=m.data_type,
            description=m.description,
            unit=m.unit,
            default_chart_type=m.default_chart_type,
        )
        for m in METRIC_REGISTRY.values()
    ]
    return ApiResponse(data=items)


@reports_router.get(
    "/dimensions",
    response_model=ApiResponse[list[DimensionRead]],
    summary="List Canonical Dimensions",
)
async def list_dimensions(
    current_user: Annotated[User, Depends(require_permission(REPORTS_READ_DOT))],
):
    items = [
        DimensionRead(
            name=d.name,
            label=d.label,
            field_type=d.field_type,
            description=d.description,
            is_filterable=d.is_filterable,
            is_groupable=d.is_groupable,
        )
        for d in DIMENSION_REGISTRY.values()
    ]
    return ApiResponse(data=items)


# =============================================================================
# 6. AD-HOC ANALYTICS QUERIES
# =============================================================================

@reports_router.post(
    "/analytics/query",
    response_model=ApiResponse[AnalyticsQueryResult],
    summary="Run Ad-Hoc Analytics Query",
)
async def query_analytics(
    payload: QuerySpecification,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ANALYTICS_QUERY_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    bypass_cache: bool = Query(False, description="Bypass cache for freshly computed values"),
):
    result, _ = await ReportingService.execute_adhoc_query(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        user=current_user,
        spec=payload,
        bypass_cache=bypass_cache,
    )
    return ApiResponse(data=result)


@reports_router.get(
    "/analytics/metrics/{metric_name}",
    response_model=ApiResponse[AnalyticsQueryResult],
    summary="Get Quick Metric Summary by Department",
)
async def get_metric_summary(
    metric_name: str,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ANALYTICS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    from app.core.exceptions import ValidationException
    m_clean = metric_name.lower().strip()
    if m_clean not in METRIC_REGISTRY:
        raise ValidationException(f"Metric '{metric_name}' is not registered. Allowed: {list(METRIC_REGISTRY.keys())}")

    # Map metric to dataset
    dataset_name = "students"
    if "attendance" in m_clean:
        dataset_name = "attendance"
    elif "pass" in m_clean or "score" in m_clean:
        dataset_name = "examinations"
    elif "invoice" in m_clean or "collected" in m_clean or "fee" in m_clean or "overdue" in m_clean:
        dataset_name = "finance"
    elif "placement" in m_clean or "offer" in m_clean:
        dataset_name = "placement"
    elif "hostel" in m_clean or "maintenance" in m_clean:
        dataset_name = "infrastructure"
    elif "doc" in m_clean:
        dataset_name = "documents"

    spec = QuerySpecification(
        dataset=dataset_name,
        dimensions=["department"] if "department" in DATASET_REGISTRY[dataset_name].allowed_dimensions else [],
        measures=[m_clean],
    )
    result, _ = await ReportingService.execute_adhoc_query(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        user=current_user,
        spec=spec,
    )
    return ApiResponse(data=result)
