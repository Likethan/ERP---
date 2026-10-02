# CampusOS — Academic Management Frontend Module Documentation

## 1. Primary Architecture & Domain Model

The **Academic Management Module** establishes the core educational spine for CampusOS. It provides an institutional operating platform that models the full hierarchical continuum of academic operations:

```
Institution (CampusOS)
   │
   ├── Campus (Main Campus, City Campus)
   │      │
   ├── Department (Computer Science, Electronics, AI & Data Science)
   │      │
   │      ├── Academic Programs (B.Tech Computer Science, B.Tech AI-DS)
   │      │      │
   │      │      └── Curriculum Schemes (Regulations: R-2024, R-2025, R-2026)
   │      │             │
   │      │             ├── Semester Structures (Semesters 1 through 8)
   │      │             │      ├── Core Subjects (Theory, Practical, Lab, Seminars)
   │      │             │      └── Elective Groups (Program Electives, Open Electives)
   │      │             │
   │      │             └── Subject Catalog (Master Subject Definitions, L-T-P-C Credits)
   │      │
   │      └── Academic Term (Academic Year 2025-2026 ➔ Odd Semester)
   │             │
   │             ├── Section Cohorts (Sections A, B, C)
   │             │
   │             ├── Course Offerings (Subject + Section + Term)
   │             │      │
   │             │      ├── Faculty Assignments (Primary, Co-Faculty, Lab Instructors)
   │             │      │
   │             │      ├── Student Course Enrollments (Core Auto-Cohort + Choice Electives)
   │             │      │
   │             │      └── Timetable Schedule (Master Time Slots, Venues, Collision Matrix)
```

This ensures a fully relational, cohesive experience where course offerings, faculty workloads, student study paths, and scheduling dynamically link back to canonical department and persona identities from People Management.

---

## 2. Route Inventory

| Route | Page Component | Description |
| :--- | :--- | :--- |
| `/app/academics` | `AcademicHubPage` | Central Academic Operations Hub; service-backed metrics, conflict alerts, quick navigations, live offerings monitor. |
| `/app/academics/subjects` | `SubjectsDirectoryPage` | Enterprise Subject Catalog with DataGrid, L-T-P-C credit filters, type/category filters, and modal subject creation. |
| `/app/academics/subjects/[id]` | `SubjectDetailViewPage` | 360° Subject Profile with 5 tabs: Overview, Curriculum Usage, Course Offerings Roster, Faculty Instructors, Lifecycle History. |
| `/app/academics/curricula` | `CurriculaDirectoryPage` | Regulation & Scheme Directory with DataGrid, version tracking, status indicators, and scheme creation modal. |
| `/app/academics/curricula/[id]` | `CurriculumDetailPage` | Interactive Curriculum Builder with semester structuring, drag/add/remove subjects, elective baskets, validation engine, and version audit. |
| `/app/academics/course-offerings` | `CourseOfferingsDirectoryPage` | Term Course Offerings Directory with DataGrid, multi-facet filtering, and guided 5-step Creation Wizard. |
| `/app/academics/course-offerings/[id]` | `CourseOfferingDetailPage` | Course Offering 360° View: Overview, Faculty Staffing with duplicate validation, Enrolled Cohort Roster, Timetable Schedule. |
| `/app/academics/enrollments` | `EnrollmentsDirectoryPage` | Student Course Enrollment Directory with DataGrid, Bulk Section Cohort Registration wizard, and Choice-Based Elective Selection workflow. |
| `/app/academics/timetable` | `TimetableManagementPage` | Master Timetable Matrix with 8-period weekly grid, Day/Section/Faculty/Room filter views, conflict visualizer, and Period Entry Editor. |

---

## 3. Core Features & Capabilities

### 3.1 Academic Operations Hub (`/app/academics`)
- **Real Service-Backed KPIs**: Displays active academic year (`2025-2026`), current semester (`Odd / Semester 3 & 5`), active subjects (`148`), active offerings (`42`), enrolled students (`1,840`), faculty instructors (`78`), and detected scheduling conflicts (`2`).
- **Conflict & Operational Health Banner**: Surface unresolved timetable collisions (e.g. room double-booking or faculty overlap) with direct jump links to the scheduling matrix.
- **Workflow Shortcuts**: Quick cards to Subject Catalog, Curriculum Schemes, Course Offerings, Student Enrollments, and Timetable Matrix.
- **Live Offerings Preview**: High-priority table of current term course offerings with capacity meters and instructor status.

### 3.2 Subject Catalog & Management (`/app/academics/subjects`)
- **Enterprise DataGrid Integration**: Sorting, paginating, searching across Subject Code and Name, multi-attribute filtering (Department, Subject Type, Category, Credits, Status).
- **L-T-P-C Architecture**: Explicit breakdown of Lecture (L), Tutorial (T), and Practical (P) hours alongside calculated total credit points.
- **Subject Creation Modal**: Controlled reactive form validating subject code uniqueness, title, department assignment, contact hours, and credit calculation.
- **Bulk Actions**: Batch activation, deactivation, or archiving of selected subjects.

### 3.3 Subject 360° Profile (`/app/academics/subjects/[id]`)
- **Overview Tab**: Full identity card, syllabus summary, prerequisite rules, and contact hour allocation meters.
- **Curriculum Usage Tab**: Dynamic list of all approved/published curriculum regulations that incorporate this subject across programs.
- **Course Offerings Tab**: Historical and active term offerings of this subject, section allocations, enrolled student counts, and status.
- **Faculty Instructors Tab**: Canonical faculty members from People Management assigned to teach this subject with assigned lecture/lab hours.
- **Academic Lifecycle History Tab**: Chronological audit trail of syllabus revisions, credit adjustments, and board-of-studies approvals.

### 3.4 Curriculum Schemes & Versioning (`/app/academics/curricula`)
- **Multi-Version Regulations**: Explicit support for concurrent regulation schemes (e.g. *R-2024*, *R-2025*, *R-2026*) without overwriting historical academic records.
- **Status Lifecycle**: `Draft` ➔ `Under Review` ➔ `Approved` ➔ `Published` ➔ `Retired`.
- **Active Version Indicator**: Clear visual badges communicating the currently operational scheme for each program.

### 3.5 Interactive Curriculum Builder (`/app/academics/curricula/[id]`)
- **Semester Structure**: Dynamic accordions for Semesters 1 through 8 showing core subjects, credits, contact hours, and running credit tallies.
- **Subject Assignment & Removal**: Modal catalog picker to search and assign subjects to target semesters with real-time credit updates.
- **Elective Group Management**: Creation and configuration of elective baskets (e.g. *Professional Elective I*, *Open Elective II*) with min/max selection constraints.
- **Frontend Validation Engine**: Real-time preliminary sanity checks flagging:
  - Duplicate subjects across multiple semesters
  - Empty semesters lacking assigned subjects
  - Credit variance or missing elective group definitions
- **Publication Workflow**: One-click publication workflow that locks approved schemes for live term course offerings.

### 3.6 Course Offerings & 5-Step Guided Wizard (`/app/academics/course-offerings`)
- **Concept**: Materializes a Subject into an operational class for an Academic Year, Semester, and Section.
- **Guided Creation Stepper**:
  - *Step 1: Academic Period* — Academic Year & Semester selector.
  - *Step 2: Subject & Section* — Program, Subject from catalog, and Target Section.
  - *Step 3: Faculty Staffing* — Assign Primary Instructor, Co-Instructor, or Lab Faculty from People Management with weekly hours.
  - *Step 4: Review & Configuration* — Maximum student capacity, venue preference, and summary verification.
  - *Step 5: Confirmation* — Service mutation creating the offering and opening student enrollment.

### 3.7 Course Offering Detail (`/app/academics/course-offerings/[id]`)
- **Offering Header**: Subject code, title, section, academic term, enrollment capacity progress bar, and status badge.
- **Faculty Staffing Card**: Faculty allocation cards with role tags (`Primary`, `Co-Faculty`, `Lab`), weekly contact hours, and direct faculty assignment form with duplicate assignment prevention.
- **Enrolled Student Roster**: Canonical student list with roll numbers, enrollment dates, and status.
- **Scheduled Timetable Periods**: Weekly periods allocated to this offering with room numbers and day-of-week slots.

### 3.8 Student Course Enrollment & Elective Selection (`/app/academics/enrollments`)
- **Bulk Cohort Enrollment**: One-click batch enrollment of entire student sections (e.g. all 65 students of Section A) into core subjects for their current semester.
- **Choice-Based Elective Selection (CBES)**: Student elective portal allowing students or academic advisors to select preferred electives from configured elective baskets with prerequisite checks and seat availability indicators.
- **Enrollment Status Lifecycle**: `Pending` ➔ `Enrolled` ➔ `Dropped` ➔ `Completed` ➔ `Withdrawn`.

### 3.9 Timetable Management & Conflict Visualizer (`/app/academics/timetable`)
- **Weekly Matrix Grid**: 8 canonical time slots across Monday through Saturday (including designated lunch breaks).
- **Multi-Perspective Filters**:
  - *By Section*: View weekly class schedule for Section A, B, or C.
  - *By Faculty*: View weekly teaching schedule for a selected professor to verify workload and free periods.
  - *By Room*: View venue occupancy (e.g. LH-101, CS-Lab-2) to prevent room contention.
  - *Day View vs. Week View*: Mobile-responsive single day focus or desktop full week matrix.
- **Collision Detection Engine**: Visual red outline and conflict alert badges indicating faculty double-booking or room scheduling clashes.
- **Period Entry Editor**: Modal to create, edit, or delete scheduled timetable entries with immediate reactive collision recalculation.

---

## 4. Role-Based Access Control (RBAC) Presentation

The Academic module interacts with the CampusOS `useAuth()` role context:

| Persona | Subject Catalog | Curriculum Builder | Course Offerings | Faculty Staffing | Enrollments | Timetable Matrix |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Super Admin** | Full Read/Write | Full Read/Write / Publish | Full Read/Write | Full Assignment | Full Read/Write / Bulk | Full Read/Write / Reschedule |
| **HOD** | Department Read/Write | Department Schemes | Department Offerings | Department Faculty Staffing | Department Oversight | Department Timetable Editor |
| **Faculty** | Read-Only | Read-Only | View Assigned Courses | View Assigned Hours | View Enrolled Cohort | View Personal Teaching Schedule |
| **Student** | Read-Only Catalog | View Program Scheme | View Available Courses | Read-Only | Select Electives / View Enrolled | View Personal Section Schedule |
| **Accounts** | Read-Only | Read-Only | Read-Only Offerings | Read-Only | Read-Only (Fee Audit) | Read-Only |
| **Placement** | Read-Only | Read-Only Schemes | Read-Only Offerings | Read-Only | Read-Only (Eligibility) | Read-Only |

---

## 5. Non-Invasive Cross-Module Integration

The Academic Management module seamlessly consumes canonical identity structures established in People Management:
- **Faculty Records**: Populated from `staffService.list()` and `facultyService.list()`, ensuring consistent names, employee codes, departments, and avatars.
- **Student Records**: Populated from `studentsService.list()`, binding enrolled cohorts directly to their active academic programs and sections.
- **Department Entities**: Standardized across CSE, ECE, ME, and AI-DS departments.
- **Zero Backend Infiltration**: Operates purely on the frontend mock adapter and TypeScript contracts, ready for future FastAPI endpoints.
