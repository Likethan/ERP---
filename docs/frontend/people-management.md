# CampusOS — People Management Frontend Module Documentation

## 1. Primary Architecture & Domain Model

The **People Management Module** establishes the canonical master identity registry for CampusOS. All institutional personas—**Students, Academic Faculty, and Support Staff**—are managed with 360-degree comprehensive profiles and interconnected relational datasets.

### Canonical Structure
```
Tenant / Institution (CampusOS)
   │
   ├── Academic Departments (CSE, ECE, ME, AI-DS, etc.)
   │      │
   │      ├── Academic Faculty (Professors, Associate Profs, Asst Profs)
   │      │      ├── Workload Allocations (Weekly Lecture & Lab Hours)
   │      │      ├── Laboratory Designations (Venue, Batches, Capacities)
   │      │      └── Scholarly Output (Journals, Conferences, Patents)
   │      │
   │      ├── Non-Teaching Staff (Registrars, Bursars, Technicians, Wardens)
   │      │      ├── Shift Schedules (Morning, General, Evening, Night)
   │      │      └── Leave Workflows (Casual, Sick, Earned, Duty)
   │      │
   │      └── Academic Programs (B.Tech, M.Tech, Ph.D.)
   │             │
   │             └── Students (Cohorts, Semesters, Sections)
   │                    ├── Guardians (Structured Relationship Network)
   │                    ├── Document Vault (Identity, Transcripts, Verification)
   │                    ├── Academic Milestones (Progressions, Honors, Hackathons)
   │                    └── Connected Module Anchors (Attendance, Exam, Finance)
```

---

## 2. Route Inventory

| Route | Page Component | Description |
| :--- | :--- | :--- |
| `/app/people` | `PeopleOverviewPage` | Institutional People Master Hub; aggregate KPIs, department distribution, quick links. |
| `/app/students` | `StudentsDirectoryPage` | Enterprise Student Directory with reusable DataGrid, multi-facet filtering, bulk status updates. |
| `/app/students/[id]` | `Student360ProfilePage` | Full Student 360° Profile with 6 tabs: Bio, Academics & Milestones, Guardians, Document Vault, Timeline, Connected Engines. |
| `/app/faculty` | `FacultyDirectoryPage` | Enterprise Faculty Directory with department filters, designation breakdown, and quick stats. |
| `/app/faculty/[id]` | `Faculty360ProfilePage` | Full Faculty 360° Profile: Teaching Workload, Lab Designations, Research Publications & Patents. |
| `/app/staff` | `StaffDirectoryPage` | Non-Teaching Personnel Directory with shift mapping, employment terms, and department filters. |
| `/app/staff/[id]` | `Staff360ProfilePage` | Staff 360° Profile: Operational Shift Roster, Leave Management Workflow, Document Records, Timeline. |

---

## 3. Core Features & Capabilities

### 3.1 Student Management & Student 360 Profile
- **Enterprise DataGrid**: Full sorting, pagination, multi-column search, column visibility toggle, CSV/JSON export, and multi-row selection.
- **Bulk Actions**: Batch lifecycle updates across selected students (Active, On Leave, Suspended, Graduated).
- **Profile Header**: Avatar badges, current program, cohort year, semester, section, and contact badges.
- **Tabs**:
  1. **Overview & Bio**: Personal information, contact credentials, permanent address, admission quota, and registration identifiers.
  2. **Academics & Milestones**: CGPA, total credits, rank, course history, and chronological visual milestone tracker.
  3. **Guardians**: Structured family relationships (Father, Mother, Legal Guardian, Local Guardian, Emergency Contact) with phone, email, and occupation.
  4. **Document Vault**: Identity proofs, high-school certificates, entrance rank cards, and verified badges with document preview modal and Scrutiny actions (Verify / Reject).
  5. **Lifecycle Timeline**: Chronological log of enrollment, achievements, certifications, and institutional events.
  6. **Connected Engines**: Non-invasive integration hooks to Attendance Engine, Examination Results, Finance Invoicing, and Placements.

### 3.2 Faculty Management & Faculty 360 Profile
- **Workload Management**: Visual indicators for workload status (`BALANCED`, `UNDER_ALLOCATED`, `HIGH_ALLOCATION`), calculating weekly lecture hours, lab hours, and target hours.
- **Course Allocations**: Section, semester, student enrollment count, and credits for each assigned subject.
- **Laboratory Designations**: Venues, days of week, time slots, weekly hours, and student workstation capacities, with mock assignment and release actions.
- **Research & Publications**: Publication types (Journals, Conferences, Book Chapters, Patents, Workshops) with DOI linking, peer-review statuses, citation counts, and add/edit modals.

### 3.3 Non-Teaching Staff & Support Operations
- **Shift Management**: Shift allocations (`MORNING`, `GENERAL`, `EVENING`, `NIGHT`), start and end times, daily duration, and department coverage.
- **Leave Request & Workflow**: Casual, Sick, Earned, and Duty leave applications with approval/rejection review flows, reason logs, and leave balance tracking.
- **Departmental Roles**: Support for laboratory technicians, registrars, bursars, wardens, fleet managers, and security commanders.

### 3.4 Unified Search & Command Palette
- Global `Ctrl+K` command palette searches across Students, Faculty, and Staff through the canonical `peopleService.searchPeople()` endpoint.
- Returns name, roll/employee code, designation or program, department, and direct navigation links.

---

## 4. Role-Based Access Control (RBAC) Presentation

The module respects the CampusOS `useAuth()` context:

| Persona | Student Directory | Student 360 Actions | Faculty Directory | Faculty 360 Actions | Staff Directory | Staff 360 Actions |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Super Admin** | Full Read/Write | Status Change, Verify Docs, Add Milestone | Full Read/Write | Assign Labs, Add Pubs, Release Duty | Full Read/Write | Change Shift, Approve/Reject Leaves |
| **HOD** | Department Read/Write | Status Change, Verify Docs, Add Milestone | Department Read/Write | Assign Labs, Add Pubs, Release Duty | Department Read/Write | Change Shift, Approve/Reject Leaves |
| **Faculty** | Read-Only | View Records, Add Milestone | Directory View | Add own Publications | Read-Only | Read-Only |
| **Staff Member** | Read-Only | View Public Info | Directory View | Read-Only | Directory View | Apply for Leave |
| **Student** | Read-Only (Directory) | View Own Profile & Upload Docs (no Verify/Status Change) | Directory View | Read-Only | Directory View | Read-Only |
| **Accounts** | Read-Only | Read-Only Profile & Financial Summary | Directory View | Read-Only | Directory View | Read-Only |
| **Placement** | Read-Only | Read-Only Academic & Placement Summary | Directory View | Read-Only | Directory View | Read-Only |

---

## 5. Future Backend Integration Points

When migrating from mock services to FastAPI endpoints:
1. `GET /api/v1/students` ↔ `studentsService.list(params)`
2. `GET /api/v1/students/{id}` ↔ `studentsService.getById(id)`
3. `POST /api/v1/students/{id}/guardians` ↔ `guardiansService.addGuardian(studentId, data)`
4. `POST /api/v1/students/{id}/documents` ↔ `documentsService.uploadStudentDocument(studentId, data)`
5. `PATCH /api/v1/students/{id}/documents/{docId}/verify` ↔ `documentsService.verifyDocument(studentId, docId)`
6. `GET /api/v1/faculty/{id}/workload` ↔ `facultyService.getWorkload(facultyId)`
7. `POST /api/v1/faculty/{id}/publications` ↔ `facultyService.createPublication(facultyId, data)`
8. `POST /api/v1/staff/{id}/leaves` ↔ `staffService.createLeaveRequest(data)`
9. `PATCH /api/v1/staff/leaves/{id}/approve` ↔ `staffService.approveLeave(leaveId)`
10. `GET /api/v1/people/search?q={query}` ↔ `peopleService.searchPeople(query)`
