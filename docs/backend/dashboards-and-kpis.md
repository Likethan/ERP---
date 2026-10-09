# Enterprise Dashboard Response Contracts & BI APIs (Step 28)

## 1. Overview

CampusOS standardizes all executive, academic, administrative, and operational dashboards into a single, strongly-typed JSON schema contract. This enables high-performance frontend visualization without ad-hoc API sprawl.

All dashboard responses implement the `DashboardResponse` schema contract in `app/schemas/analytics.py`.

---

## 2. Universal Dashboard Contract (`DashboardResponse`)

```typescript
interface DashboardResponse {
  dashboard_type: DashboardType;
  title: string;
  description?: string;
  kpi_cards: KpiCard[];
  timeseries: Record<string, TimeseriesPoint[]>;
  breakdowns: Record<string, CategoryBreakdown[]>;
  freshness: DataFreshnessInfo;
  warnings: string[];
}

interface KpiCard {
  id: string;
  title: string;
  current_value: number;
  previous_value?: number;
  change_percentage?: number;
  trend?: "UP" | "DOWN" | "NEUTRAL";
  unit?: string;
  format_type: "NUMBER" | "PERCENTAGE" | "CURRENCY" | "DECIMAL";
  is_positive_good: boolean;
}

interface TimeseriesPoint {
  date: string; // ISO 8601 YYYY-MM-DD
  value: number;
  label?: string;
}

interface CategoryBreakdown {
  category: string;
  value: number;
  percentage?: number;
  record_count?: string; // May be "<5" when small-cell privacy applies
}

interface DataFreshnessInfo {
  last_updated_at: string;
  lag_seconds: number;
  status: "FRESH" | "UPDATING" | "STALE" | "RECONCILING" | "ERROR";
  source_event_count: number;
}
```

---

## 3. Supported Dashboard Types

CampusOS provides 9 production dashboard endpoints via `GET /api/v1/analytics/dashboards/{dashboard_type}`:

### 3.1 `EXECUTIVE_OVERVIEW`
- **Target Audience**: Vice Chancellor, Board of Trustees, Principals.
- **KPIs**: Total Active Students, Institutional Attendance Rate, Confirmed Collections (INR), Exam Pass Rate.
- **Visualizations**: 30-day fee collections trend, Department distribution breakdown.
- **Required Permission**: `analytics.read`

### 3.2 `ACADEMIC_PERFORMANCE`
- **Target Audience**: Deans, Academic Directors, Heads of Departments.
- **KPIs**: Overall Exam Pass Rate, Average SGPA/CGPA, Academic Retention Rate, Low Attendance Student Count.
- **Visualizations**: Exam pass rate historical timeseries, GPA distribution.
- **Required Permission**: `analytics.read`

### 3.3 `STUDENT_LIFECYCLE`
- **Target Audience**: Registrar, Admissions Office.
- **KPIs**: Total Active Students, Admissions Current Cycle, Progression Rate, Retention Rate.
- **Visualizations**: Enrollment trend, Departmental cohort distribution.
- **Required Permission**: `analytics.read`

### 3.4 `ATTENDANCE_ENGAGEMENT`
- **Target Audience**: Faculty Advisors, Student Affairs, Deans.
- **KPIs**: Average Attendance Rate, Low Attendance Students (<75%), Finalized Sessions Rate.
- **Visualizations**: 14-day attendance rate trend, Attendance status distribution (Present/Late/Absent).
- **Required Permission**: `attendance.reports.read`

### 3.5 `EXAMINATION_OUTCOMES`
- **Target Audience**: Controller of Examinations (CoE).
- **KPIs**: Pass Rate, Average Institutional GPA, Exam Participation Rate.
- **Visualizations**: Pass rate trend by semester, Grade breakdown.
- **Required Permission**: `examinations.results.read`

### 3.6 `FINANCE_COLLECTIONS`
- **Target Audience**: Chief Financial Officer, Bursar, Accounts Head.
- **KPIs**: Total Confirmed Collections, Total Invoiced Amount, Total Outstanding Receivables, Collection Efficiency (%).
- **Visualizations**: Daily collections timeseries, Payment method breakdown.
- **Required Permission**: `finance.reports.read`

### 3.7 `PLACEMENT_OUTCOMES`
- **Target Audience**: Training & Placement Officer (TPO), Corporate Relations.
- **KPIs**: Campus Placement Rate, Accepted Offers Count, Average Salary Package (LPA).
- **Visualizations**: Placement offer velocity, CTC tier breakdown.
- **Required Permission**: `placements.reports.read`

### 3.8 `CAMPUS_OPERATIONS`
- **Target Audience**: Chief Operating Officer, Estate Officer, Hostel Wardens.
- **KPIs**: Hostel Occupancy Rate, Certificates Issued Count, Maintenance Resolution Rate.
- **Visualizations**: Daily certificate issuance timeseries, Hostel block occupancy.
- **Required Permission**: `analytics.read`

### 3.9 `WORKFLOW_SYSTEM_HEALTH`
- **Target Audience**: IT Administrators, Operations Leads.
- **KPIs**: Case SLA Resolution Rate, Open Workflow Cases, Ingestion Checkpoints, Ingestion Lag (Seconds).
- **Visualizations**: Ingestion velocity timeseries, Ingestion consumer status.
- **Required Permission**: `analytics.manage`

---

## 4. Query & Analytics Exploration APIs

Beyond pre-assembled dashboards, the engine provides 4 slice-and-dice query endpoints:

### 4.1 Timeseries Trend (`POST /api/v1/analytics/timeseries`)
Allows querying metric timeseries with grouping intervals (`DAY`, `WEEK`, `MONTH`):
```json
{
  "metric_id": "finance.total_collections",
  "start_date": "2026-09-01",
  "end_date": "2026-09-30",
  "interval": "DAY"
}
```

### 4.2 Categorical Breakdown (`POST /api/v1/analytics/breakdowns`)
Allows slicing a metric across an allowed dimension:
```json
{
  "metric_id": "students.active_count",
  "dimension": "DEPARTMENT",
  "limit": 10
}
```
*Note: Any breakdown category with count between 1 and 4 will automatically have its count masked to `"<5"` for privacy preservation.*

### 4.3 Period Comparison (`POST /api/v1/analytics/comparisons`)
Computes absolute delta and percentage change between two discrete date windows:
```json
{
  "metric_id": "finance.total_collections",
  "primary_start": "2026-09-01",
  "primary_end": "2026-09-30",
  "compare_start": "2026-08-01",
  "compare_end": "2026-08-31"
}
```

### 4.4 Governed Export Engine (`POST /api/v1/analytics/export`)
Generates server-side streaming CSV or JSON exports:
```json
{
  "export_type": "DASHBOARD",
  "dashboard_type": "FINANCE_COLLECTIONS",
  "format": "CSV"
}
```
- Formula-sanitized against Excel/Sheets CSV injection.
- Audited with request context.
- Guarded by `analytics.export` permission.
