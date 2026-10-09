"""Read-Only Case Management & HITL Operations Tools for Intelligence Layer (Step 25)."""

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import CASES_READ
from app.domains.intelligence.tools.base import ToolDefinition
from app.models.people import User
from app.services.case_service import CaseService


async def handle_get_case_analytics_summary(
    db: AsyncSession,
    tenant_id: UUID,
    user: User,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Safe read-only handler fetching institutional case and task performance analytics."""
    try:
        service = CaseService(db)
        metrics = await service.get_analytics(tenant_id=tenant_id)
        return {
            "total_cases": metrics["total_cases"],
            "open_cases": metrics["open_cases"],
            "in_progress_cases": metrics["in_progress_cases"],
            "escalated_cases": metrics["escalated_cases"],
            "resolved_cases": metrics["resolved_cases"],
            "closed_cases": metrics["closed_cases"],
            "sla_compliance_rate": metrics["sla_compliance_rate"],
            "sla_breaches_total": metrics["sla_breaches_total"],
            "avg_resolution_time_hours": metrics["avg_resolution_time_hours"],
            "total_human_tasks": metrics["total_human_tasks"],
            "cases_by_priority": metrics["cases_by_priority"],
            "cases_by_status": metrics["cases_by_status"],
        }
    except Exception as exc:
        return {"error": str(exc)}


async def handle_get_queue_summary(
    db: AsyncSession,
    tenant_id: UUID,
    user: User,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Safe read-only handler returning operational work queues and member counts."""
    try:
        service = CaseService(db)
        queues = await service.list_work_queues(tenant_id=tenant_id)
        return {
            "queues_count": len(queues),
            "queues": [
                {
                    "key": q.key,
                    "name": q.name,
                    "module": q.module,
                    "is_active": q.is_active,
                    "members_count": len(q.members),
                }
                for q in queues
            ],
        }
    except Exception as exc:
        return {"error": str(exc)}


CASE_MANAGEMENT_TOOLS = [
    ToolDefinition(
        name="get_case_analytics_summary",
        domain="CASES",
        description="Query case metrics, SLA compliance rate, and operational workload.",
        required_permissions=[CASES_READ],
        parameters=[],
        handler=handle_get_case_analytics_summary,
    ),
    ToolDefinition(
        name="get_work_queues_summary",
        domain="CASES",
        description="Query operational work queues and operator capacity.",
        required_permissions=[CASES_READ],
        parameters=[],
        handler=handle_get_queue_summary,
    ),
]
