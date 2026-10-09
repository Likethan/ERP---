# CampusOS — Cross-Domain Analytics & Builder

## Overview

The **CampusOS Intelligence Analytics** view (`/app/intelligence/analytics`) provides unified cross-domain metrics visualization and an interactive **Analytics Query Builder**. It enables academic planners, department heads, and executive leadership to correlate operational data across traditionally siloed modules (Academics, Attendance, Examinations, Finance, Placement, Infrastructure, Documents, and Campus Life).

---

## 1. Cross-Domain Telemetry Matrices

The analytics workspace provides pre-configured domain telemetry dashboards:

### Academic & Student Analytics
- Total enrollment trends by academic year and degree program.
- Departmental student distribution across undergraduate and postgraduate tracks.
- Course completion ratios and credit accumulation velocity.

### Attendance Analytics
- Institutional average attendance percentage by semester.
- Chronic shortage cohort distribution (<75% and <60%).
- Subject-wise absenteeism correlation with timetable time slots (e.g., morning vs. post-lunch sessions).

### Examination & Performance Analytics
- Semester GPA bell curve and grade distribution (O, A+, A, B+, B, C, F).
- Assessment pass percentage across core STEM courses.
- Internal evaluation vs. end-semester examination score variance.

### Finance Analytics
- Invoiced vs. collected revenue across tuition, hostel, transport, and examination fee heads.
- Outstanding balance ageing breakdown (<30 days, 31-60 days, >60 days).
- Scholarship and concession disbursement impact.

### Placement & Career Analytics
- Application-to-shortlist and shortlist-to-offer funnel velocity.
- Average, median, and highest CTC package trends by discipline.
- Top hiring recruiters and empanelled tier-1 tech firms.

### Campus, Infrastructure & Document Analytics
- Residential hall occupancy rates and room capacity utilization.
- Commuter bus circuit ridership and transport route optimization.
- Document verification backlog and average SLA turnaround times.

---

## 2. Lightweight Analytics Query Builder

The Analytics Builder is a pure client-side configuration interface allowing users to assemble custom cross-domain queries without SQL knowledge:

```text
┌────────────────────────────────────────────────────────────────────────┐
│  Configure Analytics Query                                            │
├───────────────────┬───────────────────┬─────────────────┬──────────────┤
│ Domain:           │ Metric:           │ Dimension:      │ Time Period: │
│ [ Attendance    ▼]│ [ Average Attend▼]│ [ Department  ▼]│ [ Current Sem▼│
└───────────────────┴───────────────────┴─────────────────┴──────────────┘
                                    ↓
                         [ Run Analytics Query ]
                                    ↓
┌────────────────────────────────────────────────────────────────────────┐
│  Result: Average Attendance by Department (Current Semester)           │
│                                                                        │
│  AI & Data Science           91.2%  ████████████████████               │
│  Computer Science            88.4%  █████████████████                  │
│  Information Technology      86.1%  ████████████████                   │
│  Electronics & Comm.         82.8%  ██████████████                     │
│  Mechanical Engg.            79.5%  ████████████                       │
│  Civil Engg.                 77.2%  ███████████                        │
└────────────────────────────────────────────────────────────────────────┘
```

### Supported Dimensions
- `Department`: Groups metrics by academic department.
- `Program`: Breaks down by B.Tech, M.Tech, MBA, MCA, etc.
- `Semester`: Compares performance across Semesters 1 through 8.
- `Status`: Aggregates by operational state (e.g. Paid, Partial, Overdue).
- `Month`: Visualizes month-over-month trends.

### Supported Time Ranges
- `Current Semester`
- `Previous Semester`
- `Current Academic Year`
- `Previous Academic Year`
- `Last 30 Days` / `Last 90 Days`

---

## 3. Saving & Exporting Analytics

- **Save View**: Saves the configured query and generated visualization directly into `/app/intelligence/saved` for rapid retrieval.
- **Export Summary**: Generates structured table data for executive reporting.
- **Audit Log**: Every analytics query execution is recorded in the AI Activity ledger (`/app/intelligence/activity`).
