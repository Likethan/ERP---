"""Read-Only Master Data Management & Data Quality Tools for Intelligence Layer (Step 24)."""

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import MASTER_DATA_READ
from app.domains.intelligence.tools.base import ToolDefinition
from app.models.people import User
from app.services.master_data_service import MasterDataService


async def handle_get_quality_summary(
    db: AsyncSession,
    tenant_id: UUID,
    user: User,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Safe read-only handler fetching institutional master data quality health metrics."""
    try:
        summary = await MasterDataService.get_quality_summary(db=db, tenant_id=tenant_id)
        return {
            "total_governed_records": summary.total_governed_records,
            "average_quality_score": summary.average_quality_score,
            "open_quality_issues": summary.open_quality_issues,
            "records_with_critical_issues": summary.records_with_critical_issues,
            "records_with_errors": summary.records_with_errors,
            "pending_duplicate_candidates": summary.pending_duplicate_candidates,
            "dimension_averages": summary.dimension_averages,
        }
    except Exception as exc:
        return {"error": str(exc)}


async def handle_get_duplicate_summary(
    db: AsyncSession,
    tenant_id: UUID,
    user: User,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Safe read-only handler returning pending duplicate candidate statistics."""
    try:
        summary = await MasterDataService.get_quality_summary(db=db, tenant_id=tenant_id)
        return {
            "pending_duplicates_count": summary.pending_duplicate_candidates,
            "breakdown": summary.breakdown_by_master_type,
        }
    except Exception as exc:
        return {"error": str(exc)}


MASTER_DATA_TOOLS = [
    ToolDefinition(
        name="get_master_data_quality_summary",
        domain="MASTER_DATA",
        description="Query quality score, defect counts, and health metrics of master data.",
        required_permissions=[MASTER_DATA_READ],
        parameters=[],
        handler=handle_get_quality_summary,
        sensitivity_level="INTERNAL",
    ),
    ToolDefinition(
        name="get_duplicate_candidates_summary",
        domain="MASTER_DATA",
        description="Check how many duplicate records (students, companies) are pending review.",
        required_permissions=[MASTER_DATA_READ],
        parameters=[],
        handler=handle_get_duplicate_summary,
        sensitivity_level="INTERNAL",
    ),
]
