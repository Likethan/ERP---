"""Authoritative Analytics Aggregation Engine for Intelligence.

Delegates canonical metric computations directly to the Enterprise Reporting Layer
while preserving the Intelligence query and response contract.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException
from app.models.people import User
from app.schemas.intelligence import AnalyticsQueryRequest, AnalyticsResultResponse, ChartDataset
from app.schemas.reporting import QuerySpecification
from app.services.reporting_engine import ReportingEngine

ALLOWED_METRICS = {
    "attendance_rate": "Average Attendance Rate (%)",
    "attendance_percentage": "Average Attendance Rate (%)",
    "pass_rate": "Examination Pass Rate (%)",
    "fee_collection_rate": "Fee Collection Efficiency (%)",
    "placement_rate": "Placement Offer Conversion (%)",
    "hostel_occupancy_rate": "Residential Hostel Bed Occupancy (%)",
    "document_compliance_rate": "Document Verification Compliance (%)",
}

ALLOWED_DIMENSIONS = {
    "department": "Academic Department",
    "program": "Degree Program",
    "semester": "Curriculum Semester",
    "month": "Calendar Month",
}

METRIC_TO_DATASET: dict[str, tuple[str, str]] = {
    "attendance_rate": ("attendance", "attendance_percentage"),
    "attendance_percentage": ("attendance", "attendance_percentage"),
    "pass_rate": ("examinations", "pass_percentage"),
    "fee_collection_rate": ("finance", "total_invoiced"),
    "placement_rate": ("placement", "placement_rate"),
    "hostel_occupancy_rate": ("infrastructure", "hostel_occupancy_rate"),
    "document_compliance_rate": ("documents", "document_compliance_rate"),
}


class AnalyticsService:
    """Computes cross-domain institutional analytics across allowlisted dimensions via ReportingEngine."""

    @classmethod
    async def execute_query(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        user: User,
        query: AnalyticsQueryRequest,
    ) -> AnalyticsResultResponse:
        metric = query.metric.lower().strip()
        dimension = query.dimension.lower().strip()

        if metric not in ALLOWED_METRICS:
            raise BadRequestException(
                f"Metric '{metric}' is not permitted. Allowed metrics: {list(ALLOWED_METRICS.keys())}"
            )

        if dimension not in ALLOWED_DIMENSIONS:
            raise BadRequestException(
                f"Dimension '{dimension}' is not permitted. Allowed dimensions: {list(ALLOWED_DIMENSIONS.keys())}"
            )

        dataset_id, measure_id = METRIC_TO_DATASET.get(
            metric, ("attendance", "attendance_percentage")
        )

        spec = QuerySpecification(
            dataset=dataset_id,
            dimensions=[dimension],
            measures=[measure_id],
        )

        engine_result = await ReportingEngine.execute_query(db, tenant_id, user, spec)

        chart_datasets = [
            ChartDataset(
                name=ds.name,
                data=ds.data,
                color=ds.color or "#4f46e5",
            )
            for ds in engine_result.datasets
        ]

        return AnalyticsResultResponse(
            query=query,
            title=engine_result.title,
            summary=engine_result.summary,
            chart_type=engine_result.chart_type,
            labels=engine_result.labels,
            datasets=chart_datasets,
            table_data={
                "headers": engine_result.table_data.headers,
                "rows": engine_result.table_data.rows,
            },
        )
