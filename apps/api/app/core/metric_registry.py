"""Governed Metric Registry for CampusOS Enterprise Data Platform (Step 28).

Defines authoritative, single-source-of-truth metadata, formulas, dimensions,
permissions, and refresh expectations for all analytical metrics across CampusOS domains.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from app.core.exceptions import ValidationException


class MetricDomain(StrEnum):
    STUDENTS = "STUDENTS"
    ACADEMICS = "ACADEMICS"
    ATTENDANCE = "ATTENDANCE"
    EXAMINATIONS = "EXAMINATIONS"
    FINANCE = "FINANCE"
    PLACEMENT = "PLACEMENT"
    OPERATIONS = "OPERATIONS"
    SYSTEM = "SYSTEM"


class AggregationType(StrEnum):
    COUNT = "COUNT"
    SUM = "SUM"
    AVG = "AVG"
    PERCENTAGE = "PERCENTAGE"
    RATIO = "RATIO"


class RefreshStrategy(StrEnum):
    REAL_TIME = "REAL_TIME"
    NEAR_REAL_TIME = "NEAR_REAL_TIME"
    HOURLY = "HOURLY"
    DAILY = "DAILY"


@dataclass(frozen=True)
class GovernedMetricDefinition:
    """Metadata and governance contract for an authoritative institutional metric."""

    metric_id: str
    display_name: str
    description: str
    owning_domain: MetricDomain
    formula_description: str
    aggregation_type: AggregationType
    data_type: str  # integer, decimal, percentage, currency
    unit: str | None = None
    supported_dimensions: tuple[str, ...] = (
        "department",
        "program",
        "campus",
        "date",
        "academic_year",
        "semester",
    )
    supported_filters: tuple[str, ...] = (
        "date_range",
        "academic_year_id",
        "department_id",
        "program_id",
        "status",
    )
    required_permissions: tuple[str, ...] = ("analytics.read",)
    refresh_strategy: RefreshStrategy = RefreshStrategy.NEAR_REAL_TIME
    freshness_expectation_seconds: int = 300  # 5 minutes
    version: str = "1.0"
    is_active: bool = True
    is_sensitive: bool = False  # Triggers small-cell suppression when True


GOVERNED_METRIC_REGISTRY: Final[dict[str, GovernedMetricDefinition]] = {
    # -------------------------------------------------------------------------
    # 1. STUDENTS & ACADEMICS
    # -------------------------------------------------------------------------
    "total_active_students": GovernedMetricDefinition(
        metric_id="total_active_students",
        display_name="Total Active Students",
        description="Headcount of students with ACTIVE status in an academic program.",
        owning_domain=MetricDomain.STUDENTS,
        formula_description="COUNT(DISTINCT student.id WHERE student.status = 'ACTIVE')",
        aggregation_type=AggregationType.COUNT,
        data_type="integer",
        unit="students",
        refresh_strategy=RefreshStrategy.NEAR_REAL_TIME,
    ),
    "student_enrollment_trend": GovernedMetricDefinition(
        metric_id="student_enrollment_trend",
        display_name="Student Enrollment Trend",
        description="Time-series count of new student enrollments registered per period.",
        owning_domain=MetricDomain.ACADEMICS,
        formula_description="COUNT(DISTINCT enrollment.id WHERE enrollment.status = 'ENROLLED')",
        aggregation_type=AggregationType.COUNT,
        data_type="integer",
        unit="enrollments",
        refresh_strategy=RefreshStrategy.NEAR_REAL_TIME,
    ),
    "department_student_distribution": GovernedMetricDefinition(
        metric_id="department_student_distribution",
        display_name="Department Student Distribution",
        description="Active student headcount distribution across academic departments.",
        owning_domain=MetricDomain.ACADEMICS,
        formula_description="COUNT(DISTINCT student.id) GROUP BY department.id",
        aggregation_type=AggregationType.COUNT,
        data_type="integer",
        unit="students",
    ),
    "program_student_distribution": GovernedMetricDefinition(
        metric_id="program_student_distribution",
        display_name="Program Student Distribution",
        description="Active student headcount distribution across degree programs.",
        owning_domain=MetricDomain.ACADEMICS,
        formula_description="COUNT(DISTINCT student.id) GROUP BY program.id",
        aggregation_type=AggregationType.COUNT,
        data_type="integer",
        unit="students",
    ),
    "student_retention_rate": GovernedMetricDefinition(
        metric_id="student_retention_rate",
        display_name="Student Retention Rate",
        description="Percentage of cohort students progressing to next academic term.",
        owning_domain=MetricDomain.STUDENTS,
        formula_description="(active_continuing_students / total_initial_cohort) * 100",
        aggregation_type=AggregationType.PERCENTAGE,
        data_type="percentage",
        unit="%",
        refresh_strategy=RefreshStrategy.DAILY,
    ),
    "enrollment_completion_rate": GovernedMetricDefinition(
        metric_id="enrollment_completion_rate",
        display_name="Enrollment Completion Rate",
        description="Percentage of enrolled course offerings successfully completed.",
        owning_domain=MetricDomain.ACADEMICS,
        formula_description="(COUNT(completed_enrollments) / COUNT(total_enrollments)) * 100",
        aggregation_type=AggregationType.PERCENTAGE,
        data_type="percentage",
        unit="%",
        refresh_strategy=RefreshStrategy.HOURLY,
    ),
    # -------------------------------------------------------------------------
    # 2. ATTENDANCE & ENGAGEMENT
    # -------------------------------------------------------------------------
    "attendance_percentage": GovernedMetricDefinition(
        metric_id="attendance_percentage",
        display_name="Average Attendance Percentage",
        description="Authoritative percentage of class sessions attended by students.",
        owning_domain=MetricDomain.ATTENDANCE,
        formula_description="(SUM(PRESENT + EXCUSED + 0.5*LATE) / COUNT(records)) * 100",
        aggregation_type=AggregationType.PERCENTAGE,
        data_type="percentage",
        unit="%",
        refresh_strategy=RefreshStrategy.NEAR_REAL_TIME,
    ),
    "low_attendance_count": GovernedMetricDefinition(
        metric_id="low_attendance_count",
        display_name="Low Attendance Students (<75%)",
        description="Students with cumulative term attendance below 75% threshold.",
        owning_domain=MetricDomain.ATTENDANCE,
        formula_description="COUNT(DISTINCT student.id WHERE attendance_percentage < 75.0)",
        aggregation_type=AggregationType.COUNT,
        data_type="integer",
        unit="students",
        refresh_strategy=RefreshStrategy.NEAR_REAL_TIME,
    ),
    "session_completion_rate": GovernedMetricDefinition(
        metric_id="session_completion_rate",
        display_name="Session Completion Rate",
        description="Percentage of scheduled class periods marked and locked by faculty.",
        owning_domain=MetricDomain.ATTENDANCE,
        formula_description="(COUNT(status IN ('COMPLETED', 'LOCKED')) / COUNT(sessions)) * 100",
        aggregation_type=AggregationType.PERCENTAGE,
        data_type="percentage",
        unit="%",
        refresh_strategy=RefreshStrategy.NEAR_REAL_TIME,
    ),
    "attendance_trend": GovernedMetricDefinition(
        metric_id="attendance_trend",
        display_name="Attendance Trend Over Time",
        description="Time-series progression of average attendance rate.",
        owning_domain=MetricDomain.ATTENDANCE,
        formula_description="AVG(daily_attendance_percentage) GROUP BY date",
        aggregation_type=AggregationType.PERCENTAGE,
        data_type="percentage",
        unit="%",
    ),
    # -------------------------------------------------------------------------
    # 3. EXAMINATIONS & EVALUATIONS
    # -------------------------------------------------------------------------
    "exam_participation_rate": GovernedMetricDefinition(
        metric_id="exam_participation_rate",
        display_name="Examination Participation Rate",
        description="Percentage of enrolled students taking scheduled examinations.",
        owning_domain=MetricDomain.EXAMINATIONS,
        formula_description="(COUNT(DISTINCT evaluated_students) / COUNT(eligible_students)) * 100",
        aggregation_type=AggregationType.PERCENTAGE,
        data_type="percentage",
        unit="%",
        refresh_strategy=RefreshStrategy.HOURLY,
    ),
    "pass_percentage": GovernedMetricDefinition(
        metric_id="pass_percentage",
        display_name="Examination Pass Rate",
        description="Percentage of evaluated candidates achieving passing grade.",
        owning_domain=MetricDomain.EXAMINATIONS,
        formula_description="(COUNT(results WHERE status = 'PASS') / COUNT(results)) * 100",
        aggregation_type=AggregationType.PERCENTAGE,
        data_type="percentage",
        unit="%",
        refresh_strategy=RefreshStrategy.NEAR_REAL_TIME,
    ),
    "average_examination_score": GovernedMetricDefinition(
        metric_id="average_examination_score",
        display_name="Average Examination Score",
        description="Mean score percentage across all evaluated assessments.",
        owning_domain=MetricDomain.EXAMINATIONS,
        formula_description="AVG((marks_obtained / max_marks) * 100)",
        aggregation_type=AggregationType.AVG,
        data_type="decimal",
        unit="%",
        refresh_strategy=RefreshStrategy.NEAR_REAL_TIME,
    ),
    "results_publication_status": GovernedMetricDefinition(
        metric_id="results_publication_status",
        display_name="Results Publication Status",
        description="Percentage of assessments with results officially approved and published.",
        owning_domain=MetricDomain.EXAMINATIONS,
        formula_description="(COUNT(assessments WHERE is_published = true) / COUNT(assessments)) * 100",
        aggregation_type=AggregationType.PERCENTAGE,
        data_type="percentage",
        unit="%",
    ),
    "grade_distribution_summary": GovernedMetricDefinition(
        metric_id="grade_distribution_summary",
        display_name="Grade Distribution Summary",
        description="Distribution of letter grades awarded across semester exam results.",
        owning_domain=MetricDomain.EXAMINATIONS,
        formula_description="COUNT(results) GROUP BY grade",
        aggregation_type=AggregationType.COUNT,
        data_type="integer",
        unit="results",
    ),
    # -------------------------------------------------------------------------
    # 4. FINANCE & COLLECTIONS (Confirmed Transactions Only)
    # -------------------------------------------------------------------------
    "total_invoiced": GovernedMetricDefinition(
        metric_id="total_invoiced",
        display_name="Total Invoiced Fees",
        description="Gross net fee amount billed across institutional student accounts.",
        owning_domain=MetricDomain.FINANCE,
        formula_description="SUM(invoice.net_payable WHERE invoice.status != 'CANCELLED')",
        aggregation_type=AggregationType.SUM,
        data_type="currency",
        unit="INR",
        refresh_strategy=RefreshStrategy.NEAR_REAL_TIME,
    ),
    "confirmed_collections": GovernedMetricDefinition(
        metric_id="confirmed_collections",
        display_name="Confirmed Collections",
        description="Total confirmed fee payments cleared (SUCCESS status only).",
        owning_domain=MetricDomain.FINANCE,
        formula_description="SUM(payment.amount WHERE payment.status = 'SUCCESS')",
        aggregation_type=AggregationType.SUM,
        data_type="currency",
        unit="INR",
        refresh_strategy=RefreshStrategy.NEAR_REAL_TIME,
    ),
    "total_outstanding": GovernedMetricDefinition(
        metric_id="total_outstanding",
        display_name="Total Outstanding Dues",
        description="Unpaid balance across student fee invoices.",
        owning_domain=MetricDomain.FINANCE,
        formula_description="SUM(invoice.balance_amount WHERE invoice.status IN ('ISSUED', 'PARTIALLY_PAID', 'OVERDUE'))",
        aggregation_type=AggregationType.SUM,
        data_type="currency",
        unit="INR",
        refresh_strategy=RefreshStrategy.NEAR_REAL_TIME,
    ),
    "fee_collection_rate": GovernedMetricDefinition(
        metric_id="fee_collection_rate",
        display_name="Fee Collection Rate",
        description="Ratio of confirmed collections to total net invoiced amount.",
        owning_domain=MetricDomain.FINANCE,
        formula_description="(confirmed_collections / total_invoiced) * 100",
        aggregation_type=AggregationType.PERCENTAGE,
        data_type="percentage",
        unit="%",
        refresh_strategy=RefreshStrategy.NEAR_REAL_TIME,
    ),
    "overdue_amount": GovernedMetricDefinition(
        metric_id="overdue_amount",
        display_name="Overdue Fee Amount",
        description="Total balance past the payment due date.",
        owning_domain=MetricDomain.FINANCE,
        formula_description="SUM(invoice.balance_amount WHERE due_date < NOW() AND balance_amount > 0)",
        aggregation_type=AggregationType.SUM,
        data_type="currency",
        unit="INR",
        refresh_strategy=RefreshStrategy.HOURLY,
    ),
    "scholarship_distribution": GovernedMetricDefinition(
        metric_id="scholarship_distribution",
        display_name="Scholarships & Concessions Awarded",
        description="Total institutional concessions and merit waivers granted.",
        owning_domain=MetricDomain.FINANCE,
        formula_description="SUM(concession.concession_amount WHERE status = 'APPROVED')",
        aggregation_type=AggregationType.SUM,
        data_type="currency",
        unit="INR",
        is_sensitive=True,
    ),
    "reconciliation_variance": GovernedMetricDefinition(
        metric_id="reconciliation_variance",
        display_name="Finance Reconciliation Variance",
        description="Variance between ledger allocations and gateway transaction sums.",
        owning_domain=MetricDomain.FINANCE,
        formula_description="ABS(SUM(allocated_payments) - SUM(gateway_confirmed_payments))",
        aggregation_type=AggregationType.SUM,
        data_type="currency",
        unit="INR",
        refresh_strategy=RefreshStrategy.HOURLY,
    ),
    # -------------------------------------------------------------------------
    # 5. PLACEMENTS & CAREER
    # -------------------------------------------------------------------------
    "eligible_students": GovernedMetricDefinition(
        metric_id="eligible_students",
        display_name="Placement Eligible Students",
        description="Graduating students meeting corporate eligibility standards.",
        owning_domain=MetricDomain.PLACEMENT,
        formula_description="COUNT(DISTINCT student.id WHERE student.status = 'ACTIVE' AND graduation_year = current_year)",
        aggregation_type=AggregationType.COUNT,
        data_type="integer",
        unit="students",
    ),
    "placement_applications": GovernedMetricDefinition(
        metric_id="placement_applications",
        display_name="Placement Applications",
        description="Total recruitment applications submitted across active campus drives.",
        owning_domain=MetricDomain.PLACEMENT,
        formula_description="COUNT(DISTINCT application.id)",
        aggregation_type=AggregationType.COUNT,
        data_type="integer",
        unit="applications",
    ),
    "placement_offers": GovernedMetricDefinition(
        metric_id="placement_offers",
        display_name="Total Placement Offers",
        description="Total job offers extended to student candidates.",
        owning_domain=MetricDomain.PLACEMENT,
        formula_description="COUNT(DISTINCT offer.id WHERE offer.status IN ('OFFERED', 'ACCEPTED'))",
        aggregation_type=AggregationType.COUNT,
        data_type="integer",
        unit="offers",
        refresh_strategy=RefreshStrategy.NEAR_REAL_TIME,
    ),
    "placed_students": GovernedMetricDefinition(
        metric_id="placed_students",
        display_name="Placed Student Headcount",
        description="Unique graduating students with at least one confirmed job offer.",
        owning_domain=MetricDomain.PLACEMENT,
        formula_description="COUNT(DISTINCT application.student_id WHERE application.status IN ('OFFERED', 'ACCEPTED'))",
        aggregation_type=AggregationType.COUNT,
        data_type="integer",
        unit="students",
        refresh_strategy=RefreshStrategy.NEAR_REAL_TIME,
    ),
    "placement_rate": GovernedMetricDefinition(
        metric_id="placement_rate",
        display_name="Placement Conversion Rate",
        description="Percentage of eligible graduating students with confirmed offers.",
        owning_domain=MetricDomain.PLACEMENT,
        formula_description="(placed_students / eligible_students) * 100",
        aggregation_type=AggregationType.PERCENTAGE,
        data_type="percentage",
        unit="%",
        refresh_strategy=RefreshStrategy.NEAR_REAL_TIME,
    ),
    "participating_employers": GovernedMetricDefinition(
        metric_id="participating_employers",
        display_name="Participating Corporate Employers",
        description="Count of active partner companies participating in campus recruitment drives.",
        owning_domain=MetricDomain.PLACEMENT,
        formula_description="COUNT(DISTINCT company.id WHERE company.is_active = true)",
        aggregation_type=AggregationType.COUNT,
        data_type="integer",
        unit="companies",
    ),
    "average_salary_package": GovernedMetricDefinition(
        metric_id="average_salary_package",
        display_name="Average CTC Package (LPA)",
        description="Mean annual CTC package offered across placed students (authorized data only).",
        owning_domain=MetricDomain.PLACEMENT,
        formula_description="AVG(offer.base_salary_amount WHERE offer.status = 'ACCEPTED')",
        aggregation_type=AggregationType.AVG,
        data_type="currency",
        unit="INR",
        is_sensitive=True,
    ),
    # -------------------------------------------------------------------------
    # 6. CAMPUS OPERATIONS & INFRASTRUCTURE
    # -------------------------------------------------------------------------
    "hostel_occupancy_rate": GovernedMetricDefinition(
        metric_id="hostel_occupancy_rate",
        display_name="Hostel Bed Occupancy Rate",
        description="Percentage of operational residential beds allocated to students.",
        owning_domain=MetricDomain.OPERATIONS,
        formula_description="(COUNT(bed WHERE is_occupied = true) / COUNT(bed)) * 100",
        aggregation_type=AggregationType.PERCENTAGE,
        data_type="percentage",
        unit="%",
        refresh_strategy=RefreshStrategy.HOURLY,
    ),
    "transport_utilization_rate": GovernedMetricDefinition(
        metric_id="transport_utilization_rate",
        display_name="Campus Transport Utilization",
        description="Percentage of transport fleet passenger capacity utilized.",
        owning_domain=MetricDomain.OPERATIONS,
        formula_description="(COUNT(allocated_passengers) / SUM(route_bus_capacity)) * 100",
        aggregation_type=AggregationType.PERCENTAGE,
        data_type="percentage",
        unit="%",
    ),
    "maintenance_resolution_hours": GovernedMetricDefinition(
        metric_id="maintenance_resolution_hours",
        display_name="Mean Maintenance Resolution Time",
        description="Average hours taken from ticket submission to verified completion.",
        owning_domain=MetricDomain.OPERATIONS,
        formula_description="AVG(EXTRACT(EPOCH FROM (completed_at - created_at)) / 3600)",
        aggregation_type=AggregationType.AVG,
        data_type="decimal",
        unit="hours",
    ),
    "event_participation_count": GovernedMetricDefinition(
        metric_id="event_participation_count",
        display_name="Campus Event Registrations",
        description="Total student attendance registrations across campus events.",
        owning_domain=MetricDomain.OPERATIONS,
        formula_description="COUNT(DISTINCT registration.id)",
        aggregation_type=AggregationType.COUNT,
        data_type="integer",
        unit="attendees",
    ),
    "certificate_issuance_rate": GovernedMetricDefinition(
        metric_id="certificate_issuance_rate",
        display_name="Certificate Issuance Throughput",
        description="Count of digital academic certificates generated and issued.",
        owning_domain=MetricDomain.OPERATIONS,
        formula_description="COUNT(DISTINCT certificate.id WHERE certificate.status = 'ISSUED')",
        aggregation_type=AggregationType.COUNT,
        data_type="integer",
        unit="certificates",
        refresh_strategy=RefreshStrategy.NEAR_REAL_TIME,
    ),
    "workflow_throughput_rate": GovernedMetricDefinition(
        metric_id="workflow_throughput_rate",
        display_name="Case Management Throughput",
        description="Total cases and human tasks completed within configured SLA.",
        owning_domain=MetricDomain.SYSTEM,
        formula_description="COUNT(cases WHERE status = 'CLOSED') + COUNT(tasks WHERE status = 'COMPLETED')",
        aggregation_type=AggregationType.COUNT,
        data_type="integer",
        unit="cases",
        refresh_strategy=RefreshStrategy.NEAR_REAL_TIME,
    ),
}


METRIC_ALIASES: Final[dict[str, str]] = {
    "finance.total_collections": "confirmed_collections",
    "students.active_count": "total_active_students",
    "students.enrollment_trend": "student_enrollment_trend",
    "attendance.average_percentage": "overall_attendance_percentage",
    "attendance.low_attendance_count": "students_below_attendance_threshold",
    "examinations.pass_rate": "pass_percentage",
    "examinations.average_gpa": "average_examination_score",
    "placements.placement_rate": "placement_offer_rate",
    "operations.hostel_occupancy": "hostel_occupancy_rate",
    "finance.invoiced_total": "total_invoiced",
    "finance.outstanding_balance": "total_outstanding",
}


def get_governed_metric(metric_id: str) -> GovernedMetricDefinition:
    """Retrieve governed metric definition or raise ValidationException."""
    clean_id = metric_id.lower().strip()
    resolved_id = METRIC_ALIASES.get(clean_id, clean_id)
    if resolved_id not in GOVERNED_METRIC_REGISTRY:
        raise ValidationException(
            f"Metric '{metric_id}' is not in Governed Metric Registry. "
            f"Allowed: {sorted(GOVERNED_METRIC_REGISTRY.keys())}"
        )
    return GOVERNED_METRIC_REGISTRY[resolved_id]


class _MetricRegistryAccessor:
    @staticmethod
    def get(metric_id: str) -> GovernedMetricDefinition | None:
        clean_id = metric_id.lower().strip()
        resolved_id = METRIC_ALIASES.get(clean_id, clean_id)
        return GOVERNED_METRIC_REGISTRY.get(resolved_id)

    @staticmethod
    def list(domain: str | None = None) -> list[GovernedMetricDefinition]:
        return list_governed_metrics(domain)


def get_metric_registry() -> _MetricRegistryAccessor:
    """Helper returning metric registry accessor."""
    return _MetricRegistryAccessor()


def list_governed_metrics(domain: str | None = None) -> list[GovernedMetricDefinition]:
    """List all active governed metrics optionally filtered by domain."""
    metrics = list(GOVERNED_METRIC_REGISTRY.values())
    if domain:
        d_clean = domain.upper().strip()
        metrics = [m for m in metrics if m.owning_domain == d_clean]
    return metrics


def validate_metric_id(metric_id: str) -> None:
    """Validate that metric_id exists in registry."""
    get_governed_metric(metric_id)

