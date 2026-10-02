# CampusOS — Attendance Management Frontend Module Documentation

## 1. Primary Architecture & Domain Model

The **Attendance Management Module** connects institutional academic structures with daily classroom delivery, providing a complete, operational, and audited attendance lifecycle:

```text
Academic Structure (Institution → Department → Program → Semester)
        ↓
Course Offering (Subject + Faculty + Section + Term)
        ↓
Faculty Assignment & Enrolled Students Cohort
        ↓
Attendance Session (Date, Period Slot, Room, Status, Capacity)
        ↓
Attendance Records ([Present], [Absent], [Late], [Excused])
        ↓
Attendance Summary & Calculation Engine (Weighted Attendance %, Recovery Sessions)
        ↓
Attendance Alerts (Warning <80%, Critical <65%, Shortage Banners)
        ↓
Leave & Supervised Correction Workflow (HOD Sign-off, Audit Timeline, Status Sync)
```

### Canonical Entity Reuse (No Duplication)
This module strictly reuses canonical domain models established across previous phases:
- **People Management**: `Student`, `Faculty`, `Department`, `Section`
- **Academic Management**: `CourseOffering`, `AcademicSubject`, `AcademicYear`, `Semester`, `TimetablePeriod`

---

## 2. Route Inventory

| Route | Page Component | Description |
| :--- | :--- | :--- |
| `/app/attendance` | `AttendanceHubPage` | Central Attendance Operations Hub with real service-backed KPIs, shortage alert banner, module navigation cards, department & semester distribution charts, and recovery projections. |
| `/app/attendance/sessions` | `AttendanceSessionsPage` | Enterprise DataGrid of lecture periods, multi-facet filters (Date, Dept, Section, Faculty, Status), and New Session Scheduling Modal. |
| `/app/attendance/sessions/[id]` | `AttendanceSessionDetailPage` | High-speed attendance recording matrix (`[Present] [Absent] [Late] [Excused]`), live percentage meter, unsaved changes banner, audit log timeline, and correction dialog. |
| `/app/attendance/records` | `AttendanceRecordsPage` | Complete cross-session attendance ledger with multi-attribute filtering, student roll lookup, and CSV export. |
| `/app/attendance/students` | `AttendanceStudentsPage` | Student attendance directory DataGrid with risk indicators (`HEALTHY`, `WARNING`, `CRITICAL`), shortage KPI metrics, and direct links to Student 360°. |
| `/app/attendance/students/[id]` | `StudentAttendanceDetailPage` | Student Attendance 360° Profile: aggregate attendance, course breakdown table, weekly trend curve, and condonation status. |
| `/app/attendance/courses` | `AttendanceCoursesPage` | Course offerings directory with delivered sessions count, average attendance rate, and at-risk student counts. |
| `/app/attendance/courses/[id]` | `CourseAttendanceDetailPage` | Course-level delivery statistics, syllabus session breakdown, and enrolled student attendance roster. |
| `/app/attendance/policies` | `AttendancePoliciesPage` | Configurable attendance policy editor (minimum threshold, warning threshold, late arrival weighting, condonation rules, and approval requirements). |
| `/app/attendance/leaves` | `AttendanceLeavesPage` | Student leave application directory with supporting document review, filter by status, and HOD approval/rejection modal. |
| `/app/attendance/corrections` | `AttendanceCorrectionsPage` | Supervised attendance correction requests ledger with chronological audit history and HOD sign-off. |
| `/app/attendance/reports` | `AttendanceReportsPage` | Multi-format institutional report compiler (Student, Course, Department, Low-Attendance, Session logs) with client-side CSV generator. |

---

## 3. Core Operational Features

### 3.1 Operations Dashboard (`/app/attendance`)
- **Service-Derived KPIs**: Aggregates institutional attendance (e.g. 84.6%), students below 75% threshold (18), sessions conducted today (48), pending registers (6), pending corrections (4), and pending leaves (7).
- **Critical Shortage Banner**: Automatically surfaces students falling below the 65% critical examination bar, calculating consecutive periods required to restore 75% eligibility.
- **Visual Analytics**: Operational department-wise bar breakdown and semester-wise attendance trends derived reactively from mock data.
- **Workflow Navigation**: Direct access cards to Sessions, Records, Students, Courses, Policies, Leaves, Corrections, and Reports.

### 3.2 High-Speed Session Recording (`/app/attendance/sessions/[id]`)
- **Keyboard-Optimized Marking**: One-click and keyboard toggles for `[Present]`, `[Absent]`, `[Late]`, and `[Excused]`.
- **Bulk Quick Actions**: "Mark All Present", "Mark All Absent", and search-filter within roster.
- **Live Calculation**: Instant recalculation of session attendance percentage, present count, absent count, and late count before committing.
- **Unsaved Changes Guard**: Visual warning banner and reset/discard buttons to prevent accidental navigation loss.
- **Signed Audit Trail**: Timeline showing session creation, attendance opening, roster submission, and correction actions with timestamps and actor identities.

### 3.3 Supervised Attendance Corrections (`/app/attendance/corrections`)
- **Zero Silent Overwrites**: Faculty submit correction requests specifying original status, requested status, and academic rationale.
- **HOD Approval Gate**: HOD or Administrator reviews notes and approves/rejects the request.
- **Synchronized Ledger Update**: Upon approval, the underlying session roster entry is automatically patched and the audit timeline logs the reviewer name and timestamp.

### 3.4 Leave & Condonation Workflow (`/app/attendance/leaves`)
- **Leave Categorization**: Medical, Sports / Cultural, Official On-Duty (OD), and Personal Casual leaves.
- **Percentage Exemption**: Approved leaves designate affected sessions as `EXCUSED`, preventing detrimental impact on university examination eligibility.
- **Audit Logging**: Captures submission timestamp, faculty reviewer notes, and formal approval stamp.

---

## 4. Role Experiences & Permissions

| Role | Permitted Capabilities & Views |
| :--- | :--- |
| **Administrator** | Full institutional attendance overview, policy configuration, system-wide reports, and final condonation overrides. |
| **HOD** | Department attendance dashboard, course offering attendance monitoring, approval/rejection of leave requests and faculty correction requests. |
| **Faculty** | Daily lecture schedule, taking and saving attendance rosters for assigned course offerings, initiating correction requests with justifications. |
| **Student** | Personal attendance percentage, course-wise breakdown, weekly trend curve, low-attendance warnings, and leave request submission. |

---

## 5. Verification & Quality Gates

- **Unit Test Suite**: 58 automated tests in `src/__tests__/attendance-module.test.ts` (100% PASS).
- **TypeScript**: `tsc --noEmit` exits with code 0 without any type violations.
- **Linter**: `next lint` passes without errors.
- **Regressions**: Verified zero regressions in People Management (all tests pass) and Academic Management (all 42 tests pass).
- **Backend Integrity**: ZERO backend files touched.
