"""Natural-Language Institutional Analytics Service (Step 29).

Bridges conversational inquiries directly to the Governed Metric Registry (Step 28)
and Analytics Query Engine. Strictly prohibits raw SQL execution, enforcing compile-time
allowlists, server-side PBAC, and explainability provenance.
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PermissionDeniedException, ValidationException
from app.core.metric_registry import get_metric_registry
from app.domains.intelligence.governance.safety import PromptGuard
from app.models.people import User
from app.schemas.analytics import TimeseriesRequest
from app.schemas.intelligence import NLAnalyticsQueryRequest, NLAnalyticsResponse
from app.services.analytics_service import AnalyticsService


class NLAnalyticsService:
    """Translates natural language questions into governed analytics queries."""

    # Intent to Governed Metric mapping
    INTENT_METRIC_MAP = [
        # Finance queries
        (
            ("fee", "collection", "revenue", "payment", "finance", "outstanding"),
            "finance.total_collections",
            "FINANCE_COLLECTIONS_TREND",
        ),
        # Attendance queries
        (
            ("attendance", "present", "absent", "shortage"),
            "attendance.average_percentage",
            "ATTENDANCE_OVERVIEW",
        ),
        # Examination queries
        (
            ("exam", "result", "grade", "gpa", "pass rate", "marks"),
            "examinations.pass_rate",
            "EXAMINATION_PERFORMANCE",
        ),
        # Student / Enrollment queries
        (
            ("student", "enrollment", "admission", "department", "headcount"),
            "students.active_count",
            "STUDENT_HEADCOUNT_DISTRIBUTION",
        ),
        # Placement queries
        (
            ("placement", "offer", "salary", "job", "recruiter", "ctc"),
            "placements.placement_rate",
            "PLACEMENT_OUTCOMES_SUMMARY",
        ),
        # Operations queries
        (
            ("hostel", "maintenance", "certificate", "operations"),
            "operations.hostel_occupancy",
            "CAMPUS_OPERATIONS_HEALTH",
        ),
    ]

    @classmethod
    async def process_analytics_query(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        user: User,
        user_permissions: set[str],
        request: NLAnalyticsQueryRequest,
    ) -> NLAnalyticsResponse:
        """Execute permission-validated analytical inquiry mapped exclusively to approved metrics."""
        # 1. Inspect for adversarial prompt injection
        sanitized_query = PromptGuard.inspect_and_sanitize_query(request.query)
        q_lower = sanitized_query.lower()

        # 2. Map query intent to a Governed Metric
        selected_metric_id = None
        detected_intent = "GENERAL_ANALYTICS"

        for keywords, metric_id, intent_name in cls.INTENT_METRIC_MAP:
            if any(kw in q_lower for kw in keywords):
                selected_metric_id = metric_id
                detected_intent = intent_name
                break

        if not selected_metric_id:
            # Default to students active count if ambiguous
            selected_metric_id = "students.active_count"
            detected_intent = "STUDENT_HEADCOUNT_DISTRIBUTION"

        # 3. Retrieve Metric Definition from Governed Registry
        registry = get_metric_registry()
        metric_def = registry.get(selected_metric_id)
        if not metric_def:
            raise ValidationException(f"Governed metric '{selected_metric_id}' is not registered.")

        # 4. Enforce PBAC Permission Checks
        is_admin = (
            "*" in user_permissions
            or "SUPER_ADMIN" in user_permissions
            or "INSTITUTION_ADMIN" in user_permissions
        )
        has_perm = is_admin

        if not has_perm:
            # Check domain-specific permissions
            if metric_def.owning_domain == "FINANCE":
                if any(
                    p in user_permissions
                    for p in [
                        "finance.reports.read",
                        "finance:reports:read",
                        "finance.read",
                        "finance:read",
                        "analytics.read",
                        "analytics:read",
                    ]
                ):
                    has_perm = True
            elif metric_def.owning_domain == "ATTENDANCE":
                if any(
                    p in user_permissions
                    for p in [
                        "attendance.reports.read",
                        "attendance:reports:read",
                        "attendance.read",
                        "attendance:read",
                        "analytics.read",
                        "analytics:read",
                    ]
                ):
                    has_perm = True
            elif metric_def.owning_domain == "EXAMINATIONS":
                if any(
                    p in user_permissions
                    for p in [
                        "examinations.results.read",
                        "examinations:results:read",
                        "examinations.read",
                        "examinations:read",
                        "analytics.read",
                        "analytics:read",
                    ]
                ):
                    has_perm = True
            else:
                if any(
                    p in user_permissions
                    for p in [
                        "analytics.read",
                        "analytics:read",
                        "analytics.query",
                        "analytics:query",
                    ]
                ):
                    has_perm = True

        if not has_perm:
            raise PermissionDeniedException(
                f"Access denied: You do not have the required permission to query metric '{selected_metric_id}'."
            )

        # 5. Fetch Authoritative Analytical Rollup via AnalyticsService
        now = datetime.now(UTC)
        end_date = now.date()
        start_date = end_date.replace(day=1)  # Month-to-date

        ts_req = TimeseriesRequest(
            metric_id=selected_metric_id,
            start_date=start_date,
            end_date=end_date,
            interval="DAY",
        )
        ts_res = await AnalyticsService.get_timeseries(db, tenant_id, ts_req)

        # Compute summary metric
        points = ts_res.points
        primary_val = points[-1].value if points else 0.0

        # Construct explainable response summary
        unit_str = metric_def.unit or "units"
        summary_text = (
            f"Analysis of '{metric_def.display_name}' ({selected_metric_id}) for the current period shows "
            f"a value of {primary_val:,.2f} {unit_str}. Derived strictly from authoritative "
            f"PostgreSQL tables using formula: {metric_def.formula_description}."
        )

        limitations = [
            "Analytical totals reflect confirmed ledger records only.",
            f"Refresh cadence: {metric_def.refresh_strategy.value}.",
        ]

        return NLAnalyticsResponse(
            query=sanitized_query,
            interpretedIntent=detected_intent,
            metricId=metric_def.metric_id,
            metricName=metric_def.display_name,
            owningDomain=str(metric_def.owning_domain.value),
            formulaUsed=metric_def.formula_description,
            summary=summary_text,
            primaryValue=float(primary_val),
            unit=unit_str,
            formatType=metric_def.data_type,
            timeseries=[p.model_dump() for p in points],
            breakdowns=[],
            dataFreshness="REAL_TIME"
            if metric_def.refresh_strategy.value == "REAL_TIME"
            else "NEAR_REAL_TIME",
            reportingPeriod=f"{start_date.isoformat()} to {end_date.isoformat()}",
            limitations=limitations,
            warnings=[],
        )
