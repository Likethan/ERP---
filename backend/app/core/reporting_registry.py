"""Controlled Dataset, Metric & Dimension Registry for CampusOS Reporting.

Defines all permissible reporting datasets, authoritative metric formulas,
canonical dimensions, and filter validation rules.
Strictly prevents arbitrary database querying, raw table access, or formula divergence.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from app.core.exceptions import ValidationException


class FilterOperator(StrEnum):
    EQUALS = "="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    GREATER_THAN_OR_EQUAL = ">="
    LESS_THAN = "<"
    LESS_THAN_OR_EQUAL = "<="
    IN = "IN"
    NOT_IN = "NOT_IN"
    BETWEEN = "BETWEEN"
    IS_NULL = "IS_NULL"
    IS_NOT_NULL = "IS_NOT_NULL"
    CONTAINS = "CONTAINS"
    STARTS_WITH = "STARTS_WITH"


ALLOWED_FILTER_OPERATORS = frozenset(op.value for op in FilterOperator)


@dataclass(frozen=True)
class DimensionDefinition:
    name: str
    label: str
    field_type: str  # string, number, date, boolean, uuid
    description: str
    is_filterable: bool = True
    is_groupable: bool = True


@dataclass(frozen=True)
class MeasureDefinition:
    name: str
    label: str
    formula: str
    aggregation: str  # COUNT, SUM, AVG, RATIO, PERCENTAGE, MIN, MAX
    data_type: str  # integer, decimal, percentage, currency
    description: str
    unit: str | None = None
    default_chart_type: str = "bar"


@dataclass(frozen=True)
class DatasetDefinition:
    dataset_id: str
    name: str
    domain: str
    description: str
    primary_entity: str
    allowed_dimensions: tuple[str, ...]
    allowed_measures: tuple[str, ...]
    allowed_filters: tuple[str, ...]
    required_permissions: tuple[str, ...]
    sensitive_fields: tuple[str, ...] = (
        "password_hash",
        "tokens",
        "secret",
        "private_key",
        "bank_account",
    )


# -----------------------------------------------------------------------------
# Canonical Metric Definitions (Single-Source-of-Truth Formulas)
# -----------------------------------------------------------------------------

METRIC_REGISTRY: dict[str, MeasureDefinition] = {
    # People Metrics
    "total_students": MeasureDefinition(
        name="total_students",
        label="Total Admitted Students",
        formula="COUNT(DISTINCT student.id)",
        aggregation="COUNT",
        data_type="integer",
        description="Total number of students with an active record in the institution.",
    ),
    "active_students": MeasureDefinition(
        name="active_students",
        label="Active Students",
        formula="COUNT(DISTINCT student.id WHERE student.status = 'ACTIVE')",
        aggregation="COUNT",
        data_type="integer",
        description="Students currently enrolled and active in their academic programs.",
    ),
    "faculty_count": MeasureDefinition(
        name="faculty_count",
        label="Faculty Headcount",
        formula="COUNT(DISTINCT faculty.id WHERE faculty.employment_status = 'ACTIVE')",
        aggregation="COUNT",
        data_type="integer",
        description="Total active teaching and instructional faculty members.",
    ),
    "student_faculty_ratio": MeasureDefinition(
        name="student_faculty_ratio",
        label="Student to Faculty Ratio",
        formula="active_students / faculty_count",
        aggregation="RATIO",
        data_type="decimal",
        description="Institutional academic mentor-mentee capacity ratio.",
    ),
    # Attendance Metrics
    "attendance_percentage": MeasureDefinition(
        name="attendance_percentage",
        label="Average Attendance Rate",
        formula="(SUM(CASE WHEN record.status IN ('PRESENT', 'EXCUSED') THEN 1.0 WHEN record.status = 'LATE' THEN 0.5 ELSE 0 END) / COUNT(record.id)) * 100",
        aggregation="PERCENTAGE",
        data_type="percentage",
        unit="%",
        description="Authoritative campus-wide or cohort-level attendance percentage.",
    ),
    "total_sessions": MeasureDefinition(
        name="total_sessions",
        label="Total Conducted Sessions",
        formula="COUNT(DISTINCT session.id WHERE session.status = 'COMPLETED')",
        aggregation="COUNT",
        data_type="integer",
        description="Total instructional class sessions conducted and finalized.",
    ),
    "students_below_threshold": MeasureDefinition(
        name="students_below_threshold",
        label="Students with Low Attendance (<75%)",
        formula="COUNT(DISTINCT student.id HAVING attendance_percentage < 75.0)",
        aggregation="COUNT",
        data_type="integer",
        description="Students at risk of examination debarment due to shortage.",
    ),
    # Examination Metrics
    "pass_percentage": MeasureDefinition(
        name="pass_percentage",
        label="Examination Pass Rate",
        formula="(COUNT(DISTINCT result.student_id WHERE result.result_status = 'PASS') / COUNT(DISTINCT result.student_id)) * 100",
        aggregation="PERCENTAGE",
        data_type="percentage",
        unit="%",
        description="Percentage of candidate students passing registered assessments.",
    ),
    "average_score": MeasureDefinition(
        name="average_score",
        label="Average Examination Score",
        formula="AVG(score.marks_obtained)",
        aggregation="AVG",
        data_type="decimal",
        description="Mean score achieved across evaluated assessments.",
    ),
    "total_candidates": MeasureDefinition(
        name="total_candidates",
        label="Evaluated Candidates",
        formula="COUNT(DISTINCT result.student_id)",
        aggregation="COUNT",
        data_type="integer",
        description="Total number of students evaluated in assessments.",
    ),
    # Finance Metrics
    "total_invoiced": MeasureDefinition(
        name="total_invoiced",
        label="Total Billed / Invoiced Amount",
        formula="SUM(invoice.net_payable)",
        aggregation="SUM",
        data_type="currency",
        unit="INR",
        description="Total institutional tuition and auxiliary fees billed to students.",
    ),
    "total_collected": MeasureDefinition(
        name="total_collected",
        label="Total Collections Received",
        formula="SUM(payment.amount WHERE payment.status = 'SUCCESS')",
        aggregation="SUM",
        data_type="currency",
        unit="INR",
        description="Gross fee revenue collected and cleared through financial gateways.",
    ),
    "total_outstanding": MeasureDefinition(
        name="total_outstanding",
        label="Total Pending / Outstanding Fees",
        formula="SUM(invoice.balance_amount WHERE invoice.status IN ('ISSUED', 'PARTIALLY_PAID', 'OVERDUE'))",
        aggregation="SUM",
        data_type="currency",
        unit="INR",
        description="Uncollected balance across active student cohorts.",
    ),
    "fee_collection_rate": MeasureDefinition(
        name="fee_collection_rate",
        label="Fee Collection Efficiency",
        formula="(total_collected / total_invoiced) * 100",
        aggregation="PERCENTAGE",
        data_type="percentage",
        unit="%",
        description="Percentage of billed institutional fees successfully collected.",
    ),
    "overdue_amount": MeasureDefinition(
        name="overdue_amount",
        label="Overdue Invoiced Amount",
        formula="SUM(invoice.balance_amount WHERE invoice.due_date < CURRENT_DATE AND invoice.balance_amount > 0)",
        aggregation="SUM",
        data_type="currency",
        unit="INR",
        description="Total outstanding payments that have passed their payment due date.",
    ),
    # Placement Metrics
    "eligible_students": MeasureDefinition(
        name="eligible_students",
        label="Placement Eligible Students",
        formula="COUNT(DISTINCT student.id WHERE student.status = 'ACTIVE')",
        aggregation="COUNT",
        data_type="integer",
        description="Graduating students meeting minimum criteria for recruitment drives.",
    ),
    "placement_offers": MeasureDefinition(
        name="placement_offers",
        label="Total Placement Offers",
        formula="COUNT(DISTINCT offer.id WHERE offer.status IN ('OFFERED', 'ACCEPTED'))",
        aggregation="COUNT",
        data_type="integer",
        description="Total job offers extended by campus recruitment partners.",
    ),
    "placed_students": MeasureDefinition(
        name="placed_students",
        label="Placed Students",
        formula="COUNT(DISTINCT application.student_id WHERE application.status IN ('OFFERED', 'ACCEPTED'))",
        aggregation="COUNT",
        data_type="integer",
        description="Unique student headcount with at least one confirmed job offer.",
    ),
    "placement_rate": MeasureDefinition(
        name="placement_rate",
        label="Placement Conversion Rate",
        formula="(placed_students / eligible_students) * 100",
        aggregation="PERCENTAGE",
        data_type="percentage",
        unit="%",
        description="Percentage of eligible graduating students successfully placed.",
    ),
    # Infrastructure Metrics
    "hostel_occupancy_rate": MeasureDefinition(
        name="hostel_occupancy_rate",
        label="Hostel Bed Occupancy Rate",
        formula="(COUNT(bed.id WHERE bed.is_occupied = true) / COUNT(bed.id)) * 100",
        aggregation="PERCENTAGE",
        data_type="percentage",
        unit="%",
        description="Residential campus accommodation capacity utilization percentage.",
    ),
    "open_maintenance_requests": MeasureDefinition(
        name="open_maintenance_requests",
        label="Open Facility Maintenance Requests",
        formula="COUNT(DISTINCT request.id WHERE request.status IN ('OPEN', 'IN_PROGRESS'))",
        aggregation="COUNT",
        data_type="integer",
        description="Active campus infrastructure issues awaiting resolution.",
    ),
    # Documents Metrics
    "document_compliance_rate": MeasureDefinition(
        name="document_compliance_rate",
        label="Document Verification Compliance",
        formula="(COUNT(doc.id WHERE doc.verification_status = 'VERIFIED') / COUNT(doc.id)) * 100",
        aggregation="PERCENTAGE",
        data_type="percentage",
        unit="%",
        description="Percentage of mandatory student identity/academic documents verified.",
    ),
    "pending_verifications": MeasureDefinition(
        name="pending_verifications",
        label="Pending Document Verifications",
        formula="COUNT(DISTINCT doc.id WHERE doc.verification_status = 'PENDING')",
        aggregation="COUNT",
        data_type="integer",
        description="Submissions queued in the document officer verification desk.",
    ),
    # Campus Events Metrics
    "total_events": MeasureDefinition(
        name="total_events",
        label="Total Campus Events",
        formula="COUNT(DISTINCT event.id)",
        aggregation="COUNT",
        data_type="integer",
        description="Total student club, departmental, and institutional campus events.",
    ),
    "event_registrations": MeasureDefinition(
        name="event_registrations",
        label="Event Attendance Registrations",
        formula="COUNT(DISTINCT registration.id)",
        aggregation="COUNT",
        data_type="integer",
        description="Total attendee registrations logged across campus events.",
    ),
}


# -----------------------------------------------------------------------------
# Canonical Dimensions Registry
# -----------------------------------------------------------------------------

DIMENSION_REGISTRY: dict[str, DimensionDefinition] = {
    "department": DimensionDefinition(
        name="department",
        label="Department",
        field_type="string",
        description="Academic or administrative department name or code.",
    ),
    "program": DimensionDefinition(
        name="program",
        label="Degree Program",
        field_type="string",
        description="Academic degree program (e.g. B.Tech Computer Science).",
    ),
    "academic_year": DimensionDefinition(
        name="academic_year",
        label="Academic Year",
        field_type="string",
        description="Academic calendar cycle (e.g. 2025-2026).",
    ),
    "semester": DimensionDefinition(
        name="semester",
        label="Curriculum Semester",
        field_type="string",
        description="Curriculum term or semester sequence (e.g. Semester 4).",
    ),
    "batch": DimensionDefinition(
        name="batch",
        label="Student Batch / Cohort",
        field_type="string",
        description="Admission cohort year (e.g. Class of 2026).",
    ),
    "gender": DimensionDefinition(
        name="gender",
        label="Gender",
        field_type="string",
        description="Student demographic gender classification.",
    ),
    "student_status": DimensionDefinition(
        name="student_status",
        label="Student Enrollment Status",
        field_type="string",
        description="Enrollment state (ADMITTED, ACTIVE, GRADUATED, ON_LEAVE).",
    ),
    "course": DimensionDefinition(
        name="course",
        label="Academic Course / Subject",
        field_type="string",
        description="Subject code and course title.",
    ),
    "faculty": DimensionDefinition(
        name="faculty",
        label="Instructional Faculty Member",
        field_type="string",
        description="Assigned instructor or course coordinator name.",
    ),
    "date": DimensionDefinition(
        name="date",
        label="Calendar Date",
        field_type="date",
        description="Specific transaction, session, or record event date.",
    ),
    "month": DimensionDefinition(
        name="month",
        label="Calendar Month",
        field_type="string",
        description="Aggregated calendar month.",
    ),
    "fee_category": DimensionDefinition(
        name="fee_category",
        label="Fee Category",
        field_type="string",
        description="Institutional billing category (Tuition, Hostel, Transport).",
    ),
    "payment_mode": DimensionDefinition(
        name="payment_mode",
        label="Payment Instrument Mode",
        field_type="string",
        description="Channel used for settlement (UPI, CASH, CARD, NETBANKING).",
    ),
    "company": DimensionDefinition(
        name="company",
        label="Placement Partner Organization",
        field_type="string",
        description="Corporate hiring company name.",
    ),
    "hostel": DimensionDefinition(
        name="hostel",
        label="Hostel Block",
        field_type="string",
        description="Campus residential hall or accommodation block.",
    ),
    "document_category": DimensionDefinition(
        name="document_category",
        label="Document Classification Category",
        field_type="string",
        description="Type of credential or record (Identity, Academic, Certificate).",
    ),
}


# -----------------------------------------------------------------------------
# Controlled Dataset Definitions
# -----------------------------------------------------------------------------

DATASET_REGISTRY: dict[str, DatasetDefinition] = {
    "students": DatasetDefinition(
        dataset_id="students",
        name="Student Admissions & Demographics",
        domain="PEOPLE",
        description="Demographics, admissions, enrollments, and academic standing of students.",
        primary_entity="StudentProfile",
        allowed_dimensions=("department", "program", "batch", "semester", "gender", "student_status"),
        allowed_measures=("total_students", "active_students"),
        allowed_filters=("department", "program", "batch", "semester", "gender", "student_status", "admission_date"),
        required_permissions=("people.students.read", "reports.read"),
    ),
    "faculty": DatasetDefinition(
        dataset_id="faculty",
        name="Faculty & Academic Staffing",
        domain="PEOPLE",
        description="Instructional staff, designations, department staffing, and qualifications.",
        primary_entity="FacultyProfile",
        allowed_dimensions=("department",),
        allowed_measures=("faculty_count",),
        allowed_filters=("department", "employment_status", "designation"),
        required_permissions=("people.faculty.read", "reports.read"),
    ),
    "attendance": DatasetDefinition(
        dataset_id="attendance",
        name="Attendance & Class Participation",
        domain="ATTENDANCE",
        description="Curricular session attendance, absence ratios, and policy threshold compliance.",
        primary_entity="AttendanceRecord",
        allowed_dimensions=("department", "program", "semester", "course", "faculty", "date", "month"),
        allowed_measures=("attendance_percentage", "total_sessions", "students_below_threshold"),
        allowed_filters=("department", "program", "semester", "course", "faculty", "date", "month", "status"),
        required_permissions=("attendance.read", "reports.read"),
    ),
    "examinations": DatasetDefinition(
        dataset_id="examinations",
        name="Examinations & Academic Assessment",
        domain="EXAMINATIONS",
        description="Examination performances, pass/fail ratios, grade distributions, and assessment averages.",
        primary_entity="ExamResult",
        allowed_dimensions=("department", "program", "semester", "course"),
        allowed_measures=("pass_percentage", "average_score", "total_candidates"),
        allowed_filters=("department", "program", "semester", "course", "result_status", "grade"),
        required_permissions=("examinations.read", "reports.read"),
    ),
    "finance": DatasetDefinition(
        dataset_id="finance",
        name="Tuition Billing & Fee Collections",
        domain="FINANCE",
        description="Student invoices, transaction collections, balances, overdue debts, and concessions.",
        primary_entity="Invoice",
        allowed_dimensions=("academic_year", "semester", "fee_category", "payment_mode", "date", "month"),
        allowed_measures=("total_invoiced", "total_collected", "total_outstanding", "fee_collection_rate", "overdue_amount"),
        allowed_filters=("academic_year", "semester", "fee_category", "payment_mode", "date", "month", "status"),
        required_permissions=("finance.read", "reports.read"),
    ),
    "placement": DatasetDefinition(
        dataset_id="placement",
        name="Campus Recruitment & Placement",
        domain="PLACEMENT",
        description="Placement drives, candidate eligibility, interviews, job offers, and conversion rates.",
        primary_entity="PlacementOffer",
        allowed_dimensions=("company", "department", "academic_year"),
        allowed_measures=("eligible_students", "placement_offers", "placed_students", "placement_rate"),
        allowed_filters=("company", "department", "academic_year", "status"),
        required_permissions=("placement.read", "reports.read"),
    ),
    "campus_events": DatasetDefinition(
        dataset_id="campus_events",
        name="Campus Events & Club Engagement",
        domain="CAMPUS",
        description="Co-curricular events, student club activities, registrations, and attendance.",
        primary_entity="CampusEvent",
        allowed_dimensions=("department", "date", "month"),
        allowed_measures=("total_events", "event_registrations"),
        allowed_filters=("department", "date", "month", "status"),
        required_permissions=("campus.read", "reports.read"),
    ),
    "infrastructure": DatasetDefinition(
        dataset_id="infrastructure",
        name="Hostel & Campus Facilities",
        domain="INFRASTRUCTURE",
        description="Hostel bed occupancy, room allocations, transport routes, and maintenance work orders.",
        primary_entity="HostelAllocation",
        allowed_dimensions=("hostel",),
        allowed_measures=("hostel_occupancy_rate", "open_maintenance_requests"),
        allowed_filters=("hostel", "status"),
        required_permissions=("infrastructure.read", "reports.read"),
    ),
    "documents": DatasetDefinition(
        dataset_id="documents",
        name="Student Documents & Verification Desk",
        domain="DOCUMENTS",
        description="Institutional digital documents, student identity records, certificate issuances, and compliance.",
        primary_entity="Document",
        allowed_dimensions=("document_category",),
        allowed_measures=("document_compliance_rate", "pending_verifications"),
        allowed_filters=("document_category", "verification_status"),
        required_permissions=("documents.read", "reports.read"),
    ),
    "cross_domain_student_success": DatasetDefinition(
        dataset_id="cross_domain_student_success",
        name="Cross-Domain Student Success & Performance",
        domain="CROSS_DOMAIN",
        description="Multi-domain synthesis linking attendance participation, examination results, and career outcomes.",
        primary_entity="StudentProfile",
        allowed_dimensions=("department", "program", "semester"),
        allowed_measures=("attendance_percentage", "pass_percentage", "placement_rate"),
        allowed_filters=("department", "program", "semester", "academic_year"),
        required_permissions=("reports.read", "analytics.read"),
    ),
}


def validate_query_specification(query_spec: dict[str, Any]) -> None:
    """Strictly validates a structured query specification against canonical registries."""
    dataset_id = query_spec.get("dataset")
    if not dataset_id or not isinstance(dataset_id, str):
        raise ValidationException("Field 'dataset' is required in query specification.")

    dataset = DATASET_REGISTRY.get(dataset_id.lower().strip())
    if not dataset:
        raise ValidationException(
            f"Dataset '{dataset_id}' does not exist. Allowed datasets: {list(DATASET_REGISTRY.keys())}"
        )

    # Validate requested dimensions
    dimensions = query_spec.get("dimensions", [])
    if not isinstance(dimensions, list):
        raise ValidationException("Field 'dimensions' must be a list of strings.")

    for dim in dimensions:
        dim_clean = str(dim).lower().strip()
        if dim_clean not in dataset.allowed_dimensions:
            raise ValidationException(
                f"Dimension '{dim}' is not allowed for dataset '{dataset_id}'. Allowed: {list(dataset.allowed_dimensions)}"
            )

    # Validate requested measures
    measures = query_spec.get("measures", [])
    if not isinstance(measures, list) or not measures:
        raise ValidationException("Field 'measures' must be a non-empty list of approved measures.")

    for meas in measures:
        meas_clean = str(meas).lower().strip()
        if meas_clean not in dataset.allowed_measures:
            raise ValidationException(
                f"Measure '{meas}' is not allowed for dataset '{dataset_id}'. Allowed: {list(dataset.allowed_measures)}"
            )

    # Validate filters
    filters = query_spec.get("filters", [])
    if not isinstance(filters, list):
        raise ValidationException("Field 'filters' must be a list of filter condition objects.")

    for flt in filters:
        if not isinstance(flt, dict):
            raise ValidationException("Each filter item must be an object with 'field', 'operator', and 'value'.")
        flt_field = flt.get("field")
        flt_op = flt.get("operator")

        if not flt_field or not isinstance(flt_field, str):
            raise ValidationException("Filter object requires a 'field' string.")
        if flt_field.lower().strip() not in dataset.allowed_filters:
            raise ValidationException(
                f"Filter field '{flt_field}' is not allowed for dataset '{dataset_id}'. Allowed: {list(dataset.allowed_filters)}"
            )

        if not flt_op or str(flt_op).upper() not in ALLOWED_FILTER_OPERATORS:
            raise ValidationException(
                f"Filter operator '{flt_op}' is not supported. Allowed: {sorted(ALLOWED_FILTER_OPERATORS)}"
            )

    # Validate sort field
    sort_by = query_spec.get("sort_by")
    if sort_by:
        sort_clean = str(sort_by).lower().strip()
        all_allowed_fields = set(dataset.allowed_dimensions) | set(dataset.allowed_measures)
        if sort_clean not in all_allowed_fields:
            raise ValidationException(
                f"Sort field '{sort_by}' is not in the allowed dimensions or measures."
            )

    # Validate pagination limits
    limit = query_spec.get("limit", 50)
    if not isinstance(limit, int) or limit < 1 or limit > 10000:
        raise ValidationException("Query 'limit' must be an integer between 1 and 10000.")
