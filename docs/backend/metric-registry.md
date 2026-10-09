# Governed Metric Registry Catalogue (Step 28)

## 1. Overview

The CampusOS **Governed Metric Registry** (`app/core/metric_registry.py`) is the centralized, immutable catalogue of all authorized business intelligence metrics and institutional Key Performance Indicators (KPIs).

Every metric in CampusOS is governed by:
- **Identifier**: Stable, dot-delimited string (e.g. `students.active_count`).
- **Display Name & Description**: Human-readable explanation of business meaning.
- **Owning Domain**: Domain authority (`STUDENTS`, `ACADEMICS`, `ATTENDANCE`, `EXAMINATIONS`, `FINANCE`, `PLACEMENTS`, `OPERATIONS`, `WORKFLOWS`).
- **Calculation Formula**: Mathematical definition based exclusively on authoritative operational tables.
- **Refresh Strategy**: Real-time (`REAL_TIME`), near-real-time event-driven (`NEAR_REAL_TIME`), or daily scheduled (`DAILY_ROLLUP`).
- **Supported Dimensions**: Whitelist of allowed grouping attributes.
- **Required PBAC Permission**: Server-enforced permission check.
- **Sensitivity & Privacy**: Identifies PII risks and enforces small-cell suppression rules.

---

## 2. Metric Catalogue by Domain

### 2.1 Students & Academics

| Metric ID | Display Name | Unit | Formula | Refresh Strategy | Required Permission |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `students.active_count` | Total Active Students | `COUNT` | `COUNT(DISTINCT StudentProfile.id) WHERE status = 'ACTIVE'` | `NEAR_REAL_TIME` | `analytics.read` |
| `students.enrollment_trend` | New Enrollments Trend | `COUNT` | `COUNT(DISTINCT Enrollment.id) GROUP BY enrollment_date` | `NEAR_REAL_TIME` | `analytics.read` |
| `academics.retention_rate` | Student Retention Rate | `PERCENTAGE` | `(ContinuingStudents / TotalCohortSize) * 100` | `DAILY_ROLLUP` | `analytics.query` |
| `academics.progression_rate` | Academic Progression Rate | `PERCENTAGE` | `(ProgressedStudents / EnrolledStudents) * 100` | `DAILY_ROLLUP` | `analytics.query` |
| `academics.department_distribution` | Student Count by Department | `COUNT` | `COUNT(StudentProfile.id) GROUP BY Department.name` | `DAILY_ROLLUP` | `analytics.read` |

### 2.2 Attendance

| Metric ID | Display Name | Unit | Formula | Refresh Strategy | Required Permission |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `attendance.average_percentage` | Institutional Attendance Rate | `PERCENTAGE` | `(SUM(PresentOrLate) / SUM(TotalRecords)) * 100` | `NEAR_REAL_TIME` | `attendance.reports.read` |
| `attendance.low_attendance_count` | Students with Low Attendance | `COUNT` | `COUNT(DISTINCT student_id) WHERE student_attendance_pct < 75.0` | `DAILY_ROLLUP` | `attendance.reports.read` |
| `attendance.session_completion_rate` | Completed Attendance Sessions | `PERCENTAGE` | `(FinalizedSessions / TotalScheduledSessions) * 100` | `DAILY_ROLLUP` | `attendance.read` |

### 2.3 Examinations

| Metric ID | Display Name | Unit | Formula | Refresh Strategy | Required Permission |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `examinations.pass_rate` | Examination Pass Rate | `PERCENTAGE` | `(PassedStudentCount / TotalAppearedCount) * 100` | `NEAR_REAL_TIME` | `examinations.results.read` |
| `examinations.average_gpa` | Institutional Average SGPA/CGPA | `DECIMAL` | `AVG(calculated_sgpa) WHERE status = 'PUBLISHED'` | `NEAR_REAL_TIME` | `examinations.results.read` |
| `examinations.participation_rate` | Exam Participation Rate | `PERCENTAGE` | `(AppearedExams / RegisteredExams) * 100` | `DAILY_ROLLUP` | `examinations.read` |

### 2.4 Finance & Collections (Confirmed Records Only)

> [!IMPORTANT]
> **Single Source of Truth Rule**:
> Financial metrics evaluate strictly confirmed transactions (`status == 'SUCCESS'`). Pending, failed, initiated, or unverified transactions are never included in collections.

| Metric ID | Display Name | Unit | Formula | Refresh Strategy | Required Permission |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `finance.total_collections` | Total Confirmed Collections | `CURRENCY` | `SUM(PaymentTransaction.amount) WHERE status = 'SUCCESS'` | `NEAR_REAL_TIME` | `finance.reports.read` |
| `finance.invoiced_total` | Total Invoiced Amount | `CURRENCY` | `SUM(StudentFeeInvoice.total_amount) WHERE status != 'CANCELLED'` | `DAILY_ROLLUP` | `finance.reports.read` |
| `finance.outstanding_balance` | Total Outstanding Receivables | `CURRENCY` | `SUM(StudentFeeInvoice.balance_amount) WHERE status IN ('ISSUED', 'PARTIALLY_PAID')` | `DAILY_ROLLUP` | `finance.reports.read` |
| `finance.collection_efficiency` | Fee Collection Efficiency | `PERCENTAGE` | `(ConfirmedCollections / InvoicedTotal) * 100` | `DAILY_ROLLUP` | `finance.reports.read` |

### 2.5 Placements

| Metric ID | Display Name | Unit | Formula | Refresh Strategy | Required Permission |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `placements.placement_rate` | Campus Placement Rate | `PERCENTAGE` | `(PlacedStudentsCount / EligibleRegisteredStudents) * 100` | `NEAR_REAL_TIME` | `placements.reports.read` |
| `placements.active_offers_count` | Total Offers Extended | `COUNT` | `COUNT(DISTINCT PlacementOffer.id) WHERE status = 'ACCEPTED'` | `NEAR_REAL_TIME` | `placements.read` |
| `placements.average_salary` | Average Salary Package (LPA) | `CURRENCY` | `AVG(ctc_amount) WHERE status = 'ACCEPTED' AND verified = TRUE` | `DAILY_ROLLUP` | `placements.reports.read` |

### 2.6 Operations & Workflows

| Metric ID | Display Name | Unit | Formula | Refresh Strategy | Required Permission |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `operations.hostel_occupancy` | Hostel Occupancy Rate | `PERCENTAGE` | `(AllocatedBeds / TotalHostelBeds) * 100` | `DAILY_ROLLUP` | `hostel.reports.read` |
| `operations.certificates_issued` | Processed Certificates Count | `COUNT` | `COUNT(DocumentCertificate.id) WHERE status = 'ISSUED'` | `NEAR_REAL_TIME` | `documents.read` |
| `workflows.case_resolution_rate` | SLA Resolution Rate | `PERCENTAGE` | `(ResolvedWithinSLA / TotalResolvedCases) * 100` | `DAILY_ROLLUP` | `workflows.manage` |

---

## 3. Metric Definition Schema

In Python, every governed metric is registered using the `GovernedMetricDefinition` model:

```python
GovernedMetricDefinition(
    metric_id="finance.total_collections",
    name="Total Confirmed Collections",
    domain=AnalyticsDomain.FINANCE,
    formula="SUM(PaymentTransaction.amount) WHERE status = 'SUCCESS'",
    description="Total confirmed fee collections across all payment methods. Excludes pending or failed transactions.",
    unit="CURRENCY",
    format_type="CURRENCY",
    refresh_strategy=RefreshStrategy.NEAR_REAL_TIME,
    supported_dimensions=["PAYMENT_METHOD", "FEE_HEAD", "ACADEMIC_YEAR", "CAMPUS"],
    required_permission="finance.reports.read",
    is_pii_sensitive=False,
    small_cell_masking=False,
)
```

---

## 4. Querying the Metric Catalogue

### `GET /api/v1/analytics/metrics`
Retrieve all authorized metrics for the current user's role:
```json
[
  {
    "metric_id": "students.active_count",
    "name": "Total Active Students",
    "domain": "STUDENTS",
    "unit": "COUNT",
    "format_type": "NUMBER",
    "refresh_strategy": "NEAR_REAL_TIME",
    "supported_dimensions": ["DEPARTMENT", "PROGRAM", "SEMESTER", "CAMPUS"],
    "required_permission": "analytics.read"
  }
]
```

### `GET /api/v1/analytics/metrics/{metric_id}`
Retrieve in-depth governance metadata including calculation formula, sensitivity, and supported dimensions.
