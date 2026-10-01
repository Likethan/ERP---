<USER_REQUEST>
# CAMPUSOS — MASTER FRONTEND PRODUCT BUILD

## PROJECT

You are working on **CampusOS**.

**Product:** College Operating System / Enterprise Campus ERP
**Tagline:** **One Campus. One System. One Source of Truth.**

CampusOS is intended to become a production-grade digital operating system for modern colleges.

It should connect:

* Institution management
* Students
* Faculty
* Staff
* Academics
* Attendance
* Examinations
* Results
* Finance
* Placements
* Events
* Clubs
* Communication
* Notifications
* Hostel
* Transport
* Documents
* Campus intelligence
* AI assistance

The backend architecture has already been planned in previous implementation stages.

However, we are now changing development strategy.

---

# IMPORTANT STRATEGY CHANGE

## STOP BACKEND FEATURE DEVELOPMENT FOR NOW.

From this point forward, the primary objective is to build the **entire CampusOS frontend product experience first**.

Do NOT continue implementing backend business modules during this phase.

Do NOT spend this phase implementing:

* PostgreSQL business logic
* SQLAlchemy domain implementations
* Alembic migrations for new modules
* FastAPI business services
* Payment gateway integrations
* Real email/SMS integrations
* Real AI backend
* Real notification infrastructure
* Production object-storage implementation
* Advanced Redis infrastructure
* External integrations

The backend architecture already exists as the future integration target.

The frontend must now become the **complete visual, interaction, workflow, and API-contract specification of CampusOS**.

Later we will connect the real backend to this frontend.

---

# CORE OBJECTIVE

Build a **complete, production-quality frontend system** for CampusOS.

This is NOT a prototype.

This is NOT a collection of static mockup pages.

This is NOT a generic admin dashboard template.

This must behave like a real enterprise SaaS product.

Every major module must have:

* real navigation
* realistic data structures
* functional interactions
* forms
* validation
* tables
* filters
* search
* sorting
* pagination
* drawers
* dialogs
* confirmation flows
* detail pages
* status states
* loading states
* empty states
* error states
* success states
* responsive layouts
* role-aware experiences
* realistic workflows
* reusable components
* future API compatibility

Use mock/service data only where the backend is not yet connected.

The frontend architecture must make replacing mock services with real APIs straightforward.

---

# FIRST ACTION — INSPECT THE EXISTING PROJECT

Before writing code:

1. Inspect the complete repository.
2. Inspect the existing frontend.
3. Inspect the existing backend architecture.
4. Inspect all documentation.
5. Inspect previous domain decisions.
6. Inspect existing components.
7. Inspect existing routes.
8. Inspect existing styling.
9. Inspect existing dependencies.
10. Inspect existing authentication foundations.
11. Inspect existing API/client abstractions.
12. Identify what can be reused.
13. Identify what must be refactored.
14. Identify broken or incomplete frontend foundations.

Do NOT blindly replace existing work.

Preserve useful architecture.

Refactor only where necessary.

---

# FRONTEND TECHNOLOGY

Use the existing frontend stack if it already matches the architecture.

The intended frontend stack is:

* Next.js
* TypeScript
* App Router
* Tailwind CSS
* shadcn/ui
* Lucide icons
* Framer Motion where appropriate

Use strict TypeScript.

Avoid unnecessary dependencies.

Do not introduce a second UI framework.

Do not introduce Bootstrap.

Do not introduce Material UI.

Do not introduce another CSS framework.

---

# PRODUCT DESIGN DIRECTION

CampusOS must look like a **premium enterprise operating system**, not a college website.

The visual language should communicate:

* serious
* intelligent
* modern
* reliable
* structured
* premium
* technical
* institutional
* scalable

Avoid generic AI-generated dashboard aesthetics.

Avoid:

* excessive gradients
* excessive glassmorphism
* giant rounded cards everywhere
* random glowing effects
* unnecessary neon colors
* oversized typography
* decorative UI with no purpose
* excessive animations
* template-looking dashboards
* meaningless charts
* fake metrics
* visual clutter

Use visual hierarchy instead.

The interface should feel closer to a sophisticated enterprise platform than a generic student portal.

---

# DESIGN SYSTEM

Create or formalize a centralized CampusOS design system.

Define reusable tokens for:

## Typography

Establish:

* display
* heading
* section heading
* body
* caption
* label
* table
* metadata

Use consistent typography hierarchy.

---

## Colors

Create semantic tokens rather than scattering raw colors throughout components.

Examples:

* background
* foreground
* muted
* border
* card
* primary
* secondary
* success
* warning
* destructive
* info

Status colors must be consistent throughout the entire application.

---

# SPACING

Create consistent spacing rules.

Do not manually invent spacing values on every page.

---

# COMPONENT SYSTEM

Create reusable components for:

### Navigation

* Sidebar
* Topbar
* Breadcrumbs
* Mobile navigation
* User menu
* Command palette

### Layout

* Page shell
* Page header
* Section header
* Content container
* Split layouts
* Detail layouts

### Data

* Data table
* Pagination
* Search
* Filter bar
* Filter chips
* Sort controls
* Column visibility
* Bulk selection
* Bulk actions

### Forms

* Text input
* Number input
* Select
* Multi-select
* Date picker
* Date range
* Combobox
* File upload
* Textarea
* Form sections
* Form validation
* Form footer

### Feedback

* Toast
* Alert
* Banner
* Confirmation dialog
* Error state
* Empty state
* Loading skeleton
* Success state

### Navigation / interaction

* Tabs
* Dropdowns
* Context menus
* Drawers
* Dialogs
* Stepper
* Timeline

### Status

* Status badge
* Progress indicator
* Activity indicator
* Health indicator

### Dashboard

* KPI card
* Chart container
* Metric comparison
* Activity feed
* Quick action panel

Every component should be reusable.

---

# APPLICATION SHELL

Build the main authenticated CampusOS application shell.

Structure:

```text
CampusOS
│
├── Sidebar
│
├── Top Navigation
│
│   ├── Breadcrumbs
│   ├── Search / Command Palette
│   ├── Notifications
│   └── User Menu
│
└── Main Content
```

The shell must support:

* desktop
* tablet
* mobile
* collapsible sidebar
* responsive navigation
* nested routes
* breadcrumbs
* active navigation states
* role-aware navigation
* permission-aware navigation

---

# SIDEBAR INFORMATION ARCHITECTURE

Create a clear navigation hierarchy.

Suggested structure:

```text
OVERVIEW

Dashboard


PEOPLE

Students
Faculty
Staff
Parents / Guardians


ACADEMICS

Programs
Academic Years
Semesters
Sections
Subjects
Curriculum
Course Offerings
Enrollments
Timetable


ATTENDANCE

Attendance Dashboard
Sessions
Attendance Records
Leaves
Corrections


EXAMINATIONS

Assessments
Examinations
Schedules
Eligibility
Marks
Results


FINANCE

Finance Dashboard
Fee Structures
Student Fees
Invoices
Payments
Receipts
Scholarships
Refunds


PLACEMENT

Placement Dashboard
Companies
Job Drives
Eligibility
Applications
Interviews
Offers
Outcomes


CAMPUS

Events
Clubs
Announcements
Notifications


INFRASTRUCTURE

Hostel
Rooms
Allocations
Hostel Leave
Complaints

Transport
Vehicles
Drivers
Routes
Students


DOCUMENTS

Document Vault
Requests
Templates
Certificates
Verification


INTELLIGENCE

Campus Intelligence
AI Assistant


SYSTEM

Users
Roles
Permissions
Audit Logs
Settings
```

Do not blindly expose every item to every role.

The navigation must eventually be permission-aware.

---

# COMMAND PALETTE

Implement a global command palette.

Users should be able to search and navigate quickly.

Example:

```text
Search CampusOS...

Students
Faculty
Courses
Attendance
Invoices
Placement Drives
Events
Documents
Settings
```

Support keyboard interaction.

Example:

```text
⌘ / Ctrl + K
```

The command palette should be extensible.

---

# GLOBAL SEARCH FOUNDATION

Create a frontend search abstraction capable of eventually searching:

* students
* faculty
* courses
* companies
* events
* invoices
* documents
* placements

For now, use mock/service data.

Do NOT implement unrestricted client-side searching across everything.

Create a clean abstraction that can later call:

```text
/api/v1/search
```

or domain-specific APIs.

---

# DASHBOARD FOUNDATION

Build a real CampusOS dashboard framework.

Do not hard-code one dashboard for every user.

The dashboard should be role-aware.

---

# STUDENT DASHBOARD

The student dashboard should surface:

* attendance summary
* today's timetable
* upcoming examinations
* pending fees
* placement opportunities
* upcoming events
* notifications
* documents
* academic performance
* quick actions

Use realistic mock data.

Every card should lead somewhere meaningful.

Do not create decorative cards that do nothing.

---

# FACULTY DASHBOARD

Show:

* today's classes
* pending attendance
* upcoming assessments
* assigned courses
* student alerts
* announcements
* timetable
* recent activity

---

# HOD DASHBOARD

Show:

* department student count
* faculty overview
* attendance trends
* academic performance
* pending approvals
* placement activity
* departmental events
* alerts

---

# ACCOUNTS DASHBOARD

Show:

* total billed
* collected
* outstanding
* overdue
* pending payments
* scholarships
* refunds
* recent transactions

Use mock data until backend integration.

---

# PLACEMENT DASHBOARD

Show:

* active companies
* active drives
* applications
* shortlisted students
* interviews
* offers
* placed students
* placement statistics

---

# ADMIN DASHBOARD

Show institutional-level information.

Do not fabricate meaningless statistics.

Create clearly structured mock data with a service layer.

---

# MODULE 1 — PEOPLE

Build complete frontend workflows for:

## Students

Routes:

```text
/app/students
/app/students/[id]
```

Features:

* student table
* search
* filtering
* sorting
* pagination
* status filters
* department filter
* program filter
* academic year filter
* section filter
* student creation
* student editing
* student detail
* enrollment information
* academic information
* attendance summary
* finance summary
* placement summary
* documents
* activity timeline

Student detail must become the central student record.

Do NOT create separate fake student records inside other modules.

---

# FACULTY

Routes:

```text
/app/faculty
/app/faculty/[id]
```

Include:

* faculty list
* departments
* designation
* assigned subjects
* course offerings
* timetable
* attendance responsibility
* assessments
* profile
* documents

---

# STAFF

Build:

```text
/app/staff
/app/staff/[id]
```

---

# PARENTS / GUARDIANS

Build appropriate views and relationships.

---

# MODULE 2 — ACADEMICS

Build complete frontend pipelines.

## Programs

```text
/app/academics/programs
```

## Academic Years

```text
/app/academics/academic-years
```

## Semesters

```text
/app/academics/semesters
```

## Sections

```text
/app/academics/sections
```

## Subjects

```text
/app/academics/subjects
/app/academics/subjects/[id]
```

Include:

* subject code
* name
* credits
* type
* hours
* department
* status

---

# CURRICULUM

Build a real curriculum builder.

Routes:

```text
/app/academics/curricula
/app/academics/curricula/[id]
```

Include:

* curriculum metadata
* version
* semester structure
* subjects
* credits
* elective groups
* publishing state
* version history

Build the UI so it resembles an actual curriculum management system.

---

# COURSE OFFERINGS

Build:

```text
/app/academics/course-offerings
/app/academics/course-offerings/[id]
```

Flow:

```text
Subject
↓
Academic Year
↓
Semester
↓
Section
↓
Course Offering
↓
Faculty Assignment
↓
Student Enrollment
```

---

# TIMETABLE

Build:

```text
/app/academics/timetable
```

Support:

* day
* time
* room
* faculty
* section
* subject
* course

Create a high-quality timetable interface.

---

# MODULE 3 — ATTENDANCE

Build the complete frontend workflow.

```text
Course
↓
Attendance Session
↓
Student List
↓
Mark Attendance
↓
Submit
↓
Attendance Summary
```

Routes:

```text
/app/attendance
/app/attendance/sessions
/app/attendance/sessions/[id]
/app/attendance/students/[id]
/app/attendance/leaves
/app/attendance/corrections
```

Include:

* attendance dashboard
* session creation
* attendance marking interface
* present/absent states
* bulk actions
* attendance history
* percentage
* leave workflow
* correction workflow
* low attendance warnings

Do not implement QR/biometric functionality yet.

---

# MODULE 4 — EXAMINATIONS

Build:

```text
/app/examinations
/app/examinations/assessments
/app/examinations/schedules
/app/examinations/eligibility
/app/examinations/marks
/app/examinations/results
```

Pipeline:

```text
Assessment
↓
Exam
↓
Eligibility
↓
Marks
↓
Grade
↓
Result
↓
Publication
```

Build:

* assessment creation
* assessment configuration
* examination scheduling
* eligibility view
* marks entry grid
* bulk marks entry
* validation states
* grade preview
* result preview
* result finalization UI
* result publication UI
* student result page

---

# MODULE 5 — FINANCE

Build:

```text
/app/finance
/app/finance/fee-structures
/app/finance/student-fees
/app/finance/invoices
/app/finance/payments
/app/finance/receipts
/app/finance/scholarships
/app/finance/refunds
```

Pipeline:

```text
Fee Structure
↓
Student Fee Assignment
↓
Invoice
↓
Payment
↓
Allocation
↓
Receipt
```

Build realistic financial interfaces.

Important:

Do NOT create fake payment gateway functionality.

The frontend should only represent the future payment workflow.

---

# MODULE 6 — PLACEMENT

Build:

```text
/app/placements
/app/placements/companies
/app/placements/drives
/app/placements/eligibility
/app/placements/applications
/app/placements/interviews
/app/placements/offers
/app/placements/outcomes
```

Pipeline:

```text
Company
↓
Job Drive
↓
Eligibility
↓
Application
↓
Shortlisting
↓
Interview
↓
Offer
↓
Outcome
```

Include:

* company profiles
* job positions
* eligibility rules
* student eligibility
* applications
* shortlist
* interview scheduling
* interview results
* offers
* placement outcome

---

# MODULE 7 — EVENTS & CLUBS

Build:

```text
/app/events
/app/events/[id]

/app/clubs
/app/clubs/[id]

/app/announcements
/app/notifications
```

Events should support:

* draft
* publish
* registration
* capacity
* waitlist
* attendance
* completion
* cancellation

Clubs:

* club profile
* members
* membership
* events
* announcements

---

# MODULE 8 — HOSTEL

Build:

```text
/app/hostel
/app/hostel/hostels
/app/hostel/rooms
/app/hostel/allocations
/app/hostel/leaves
/app/hostel/complaints
```

Visualize:

```text
Hostel
↓
Block
↓
Floor
↓
Room
↓
Bed
↓
Student
```

Build room/bed allocation workflows.

---

# MODULE 9 — TRANSPORT

Build:

```text
/app/transport
/app/transport/vehicles
/app/transport/drivers
/app/transport/routes
/app/transport/students
```

Pipeline:

```text
Route
↓
Stops
↓
Vehicle
↓
Driver
↓
Student Allocation
```

Build a clean transport management experience.

Do not implement live GPS yet.

---

# MODULE 10 — DOCUMENTS

Build:

```text
/app/documents
/app/documents/my
/app/documents/requests
/app/documents/templates
/app/documents/certificates
```

Features:

* document vault
* upload UI
* metadata
* document categories
* version history
* request document
* approval workflow
* certificate issuance UI
* verification interface

Do not build real object storage yet.

Use a mock storage service abstraction.

---

# MODULE 11 — NOTIFICATIONS

Build a central notification experience.

Include:

* notification center
* unread count
* read/unread
* notification categories
* notification preferences
* notification detail
* announcement delivery

The frontend should be designed so future modules can push notifications through one central system.

---

# MODULE 12 — INTELLIGENCE / AI

Create the frontend experience only.

Routes:

```text
/app/intelligence
/app/ai
```

Build:

### Campus Intelligence

* KPI overview
* trends
* operational insights
* anomaly indicators
* reports

### AI Assistant

Create a premium conversational interface.

The AI must eventually be permission-aware.

For now:

**DO NOT implement a real AI backend.**

Create:

```text
AI Service Interface
        ↓
Mock AI Provider
        ↓
Future Real AI Provider
```

The UI should demonstrate the future experience without pretending that real intelligence exists.

---

# ROLE EXPERIENCES

Create a role abstraction.

At minimum support:

```text
ADMIN
SUPER_ADMIN
FACULTY
HOD
STAFF
ACCOUNTS
PLACEMENT_OFFICER
STUDENT
PARENT
```

The frontend should support:

```text
role
+
permissions
+
navigation
+
page access
+
action visibility
```

Do NOT rely on frontend permissions for security.

Frontend permissions are purely UX.

Backend authorization will remain authoritative later.

---

# MOCK DATA ARCHITECTURE

This is extremely important.

Do NOT scatter mock data directly inside React components.

Bad:

```ts
const students = [...]
```

inside a page.

Instead create:

```text
src/
├── services/
│   ├── students.service.ts
│   ├── faculty.service.ts
│   ├── academics.service.ts
│   ├── attendance.service.ts
│   ├── examinations.service.ts
│   ├── finance.service.ts
│   ├── placements.service.ts
│   ├── events.service.ts
│   ├── hostel.service.ts
│   ├── transport.service.ts
│   └── documents.service.ts
│
├── mocks/
│   ├── students.mock.ts
│   ├── faculty.mock.ts
│   ├── academics.mock.ts
│   ├── attendance.mock.ts
│   ├── examinations.mock.ts
│   ├── finance.mock.ts
│   ├── placements.mock.ts
│   ├── events.mock.ts
│   ├── hostel.mock.ts
│   ├── transport.mock.ts
│   └── documents.mock.ts
```

Pages must consume services.

---

# API CONTRACT ARCHITECTURE

Design the frontend as if the backend already exists.

Create API service interfaces such as:

```ts
studentService.list()
studentService.getById(id)
studentService.create(data)
studentService.update(id, data)
```

Similarly:

```ts
attendanceService.getSessions()
attendanceService.createSession()
attendanceService.getStudentAttendance()
attendanceService.submitAttendance()
```

and equivalent services for all domains.

The service implementation can currently use mock data.

Later we replace the implementation with HTTP requests.

The UI should not need to change.

---

# TYPES

Create centralized domain types.

Examples:

```text
Student
Faculty
Staff
Department
Program
AcademicYear
Semester
Section
Subject
Curriculum
CourseOffering
CourseEnrollment
AttendanceSession
AttendanceRecord
Assessment
Examination
ExamSchedule
Mark
Result
FeeStructure
Invoice
Payment
Receipt
Company
JobDrive
Application
Interview
Offer
Event
Club
Notification
Hostel
Room
Bed
TransportRoute
Vehicle
Driver
Document
Certificate
```

Do not duplicate the same entity with slightly different shapes across modules unless there is a clear view-model reason.

---

# FORMS

Every major creation/edit flow must have:

* validation
* required fields
* error messages
* disabled submit state
* loading state
* success state
* cancellation
* confirmation where destructive
* realistic validation

Do not create forms that simply submit and disappear.

---

# TABLES

Enterprise tables must support:

* search
* filtering
* sorting
* pagination
* row actions
* bulk selection where appropriate
* column visibility where useful
* responsive behavior

Use realistic table density.

---

# DETAIL PAGES

Major entities need detail pages.

For example:

```text
Student
├── Overview
├── Academics
├── Attendance
├── Finance
├── Placement
├── Documents
└── Activity
```

The same philosophy should be applied to:

* faculty
* company
* job drive
* course
* invoice
* event
* hostel
* document

---

# STATES

Every major page must account for:

### Loading

Use skeletons.

### Empty

Explain what is missing and provide an appropriate action.

### Error

Show a useful recovery action.

### Success

Give meaningful feedback.

### Permission denied

Explain that the user does not have access.

### Not found

Provide navigation back to the relevant module.

Do not leave blank screens.

---

# RESPONSIVE DESIGN

The frontend must work on:

* desktop
* laptop
* tablet
* mobile

However, do not simply stack every desktop component vertically.

Design mobile experiences intentionally.

Tables may become:

* horizontal scroll
* condensed cards
* detail drawers

depending on context.

---

# ANIMATION

Use animation carefully.

CampusOS is enterprise software.

Use animation for:

* page transitions
* dialogs
* drawers
* dropdowns
* navigation
* loading
* state changes
* meaningful feedback

Do not turn every component into an animation showcase.

Animation must improve usability.

---

# ACCESSIBILITY

Implement:

* keyboard navigation
* visible focus states
* semantic HTML
* ARIA where necessary
* accessible dialogs
* accessible forms
* sufficient contrast
* screen-reader-friendly labels

Do not treat accessibility as optional.

---

# SECURITY UX

Even though backend security is postponed, the frontend should be designed around secure behavior.

Never:

* expose secrets
* place tokens in localStorage unnecessarily
* expose internal storage paths
* expose database IDs unnecessarily in UI
* assume frontend permissions are security
* expose sensitive document URLs permanently

Prepare abstractions for secure backend integration.

---

# DATA FLOW

Use a predictable frontend architecture.

Preferred conceptual structure:

```text
Page
 ↓
Feature Component
 ↓
Service
 ↓
API / Mock Adapter
 ↓
Future Backend
```

Avoid:

```text
Page
 ↓
random fetch()
 ↓
inline transformation
 ↓
component state
```

everywhere.

---

# URL / ROUTING ARCHITECTURE

Use meaningful routes.

Example:

```text
/app
/app/students
/app/students/[id]

/app/academics
/app/academics/subjects
/app/academics/subjects/[id]

/app/attendance
/app/attendance/sessions
/app/attendance/sessions/[id]

/app/examinations
/app/examinations/results

/app/finance
/app/finance/invoices/[id]

/app/placements
/app/placements/drives/[id]

/app/events
/app/events/[id]

/app/hostel
/app/transport

/app/documents
/app/documents/[id]

/app/intelligence
/app/ai
```

Do not create meaningless route structures.

---

# FRONTEND PIPELINE PRINCIPLE

Every module should have a visible lifecycle.

For example:

## Academic

```text
Program
→ Curriculum
→ Subject
→ Course Offering
→ Faculty
→ Enrollment
→ Timetable
```

## Attendance

```text
Course
→ Session
→ Attendance
→ Summary
→ Alert
```

## Examination

```text
Assessment
→ Examination
→ Eligibility
→ Marks
→ Grade
→ Result
→ Publication
```

## Finance

```text
Fee Structure
→ Assignment
→ Invoice
→ Payment
→ Receipt
```

## Placement

```text
Company
→ Drive
→ Eligibility
→ Application
→ Shortlist
→ Interview
→ Offer
→ Outcome
```

The UI should make these relationships understandable.

---

# CROSS-MODULE NAVIGATION

CampusOS should feel like one connected system.

For example:

Opening a student should allow navigation to:

```text
Student
├── Academic
├── Attendance
├── Exams
├── Finance
├── Placement
├── Documents
└── Events
```

Opening a course should allow:

```text
Course
├── Faculty
├── Students
├── Timetable
├── Attendance
└── Assessments
```

Opening a company should allow:

```text
Company
├── Jobs
├── Drives
├── Applications
├── Interviews
└── Offers
```

Do not build isolated modules.

---

# REALISTIC DEMO DATA

Create enough coherent mock data to make the application feel alive.

For example:

* multiple departments
* multiple programs
* multiple academic years
* multiple semesters
* multiple sections
* realistic subjects
* students
* faculty
* companies
* job drives
* invoices
* events
* hostels
* transport routes
* documents

The relationships must be internally consistent.

Do NOT use random lorem ipsum data.

Do NOT use obviously fake names such as:

```text
John Doe
Test User
Lorem Ipsum
Company XYZ
```

Use realistic institutional data.

But clearly keep it as mock/demo data.

---

# DO NOT FAKE BACKEND FUNCTIONALITY

If a feature is not actually implemented, do not pretend it is.

For example:

Bad:

```text
"Payment successful"
```

when no payment system exists.

Instead:

```text
Demo payment workflow
```

or clearly separate mock behavior.

The same applies to:

* AI
* notifications
* certificates
* file storage
* authentication
* analytics

---

# TESTING

Add frontend tests where appropriate.

At minimum validate:

* navigation
* critical forms
* service layer
* role-aware navigation
* major workflows
* important components
* route rendering

Also ensure:

```text
npm run lint
npm run build
```

work successfully.

Fix all TypeScript errors.

Do not leave:

```text
any
```

everywhere just to make compilation pass.

---

# CODE QUALITY

Follow:

* strict TypeScript
* reusable components
* clear naming
* small focused components
* domain-oriented folders
* no giant page components
* no duplicated business UI
* no magic constants
* no random styling
* no dead code
* no unused dependencies

Keep the architecture understandable.

---

# PERFORMANCE

Avoid unnecessary:

* client components
* global state
* re-renders
* huge bundle dependencies
* duplicate data fetching

Use server components where appropriate.

Use client components only when interaction requires them.

Do not sacrifice architecture merely to make implementation faster.

---

# DOCUMENTATION

Create/update:

```text
docs/frontend/
```

Include:

```text
architecture.md
design-system.md
routing.md
role-experiences.md
api-contracts.md
mock-data.md
frontend-roadmap.md
```

Document major architectural decisions.

---

# IMPLEMENTATION ORDER

Do NOT attempt to create all 100+ screens randomly.

Implement systematically in this order:

## PHASE A — FOUNDATION

1. Design tokens
2. Global styling
3. Component system
4. App shell
5. Sidebar
6. Topbar
7. Command palette
8. Breadcrumbs
9. Responsive navigation
10. Toast/dialog/drawer system
11. Loading/error/empty states

---

## PHASE B — CORE EXPERIENCE

12. Dashboard framework
13. Role system
14. Mock service architecture
15. Domain types
16. API contracts
17. Global search
18. Notification center

---

## PHASE C — PEOPLE

19. Students
20. Student detail
21. Faculty
22. Faculty detail
23. Staff
24. Parents

---

## PHASE D — ACADEMICS

25. Programs
26. Academic years
27. Semesters
28. Sections
29. Subjects
30. Curriculum
31. Course offerings
32. Faculty assignments
33. Enrollments
34. Timetable

---

## PHASE E — ATTENDANCE

35. Dashboard
36. Sessions
37. Mark attendance
38. Student attendance
39. Leaves
40. Corrections

---

## PHASE F — EXAMINATIONS

41. Assessments
42. Examinations
43. Schedules
44. Eligibility
45. Marks
46. Results

---

## PHASE G — FINANCE

47. Finance dashboard
48. Fee structures
49. Student fees
50. Invoices
51. Payments
52. Receipts
53. Scholarships
54. Refunds

---

## PHASE H — PLACEMENT

55. Companies
56. Drives
57. Eligibility
58. Applications
59. Interviews
60. Offers
61. Outcomes

---

## PHASE I — CAMPUS

62. Events
63. Event detail
64. Clubs
65. Club detail
66. Announcements
67. Notifications

---

## PHASE J — INFRASTRUCTURE

68. Hostel
69. Rooms
70. Allocations
71. Leave
72. Complaints
73. Transport
74. Vehicles
75. Drivers
76. Routes
77. Student transport

---

## PHASE K — DOCUMENTS

78. Document vault
79. Document detail
80. Requests
81. Templates
82. Certificates
83. Verification

---

## PHASE L — INTELLIGENCE

84. Campus intelligence
85. Analytics views
86. AI assistant interface

---

# IMPORTANT IMPLEMENTATION RULE

Do not create every page as a separate disconnected task.

Create reusable patterns first.

For example:

```text
EntityListPage
EntityDetailPage
EntityForm
EntityStatus
EntityActivity
EntityFilters
```

where appropriate.

Then reuse them across domains.

But do NOT over-generalize everything into one giant generic component.

Generalize only where the UI patterns are genuinely shared.

---

# VISUAL QUALITY BAR

Before considering a page complete, ask:

1. Does this look like enterprise software?
2. Is the information hierarchy obvious?
3. Can a user understand what to do next?
4. Are actions discoverable?
5. Are states handled?
6. Does the page work on mobile?
7. Does it use the CampusOS design system?
8. Does it avoid unnecessary decoration?
9. Does it feel connected to the rest of the system?
10. Could this realistically be shown as a serious SaaS product?

If the answer is no, improve it.

---

# CRITICAL: DO NOT BUILD EVERYTHING IN ONE PASS

Although this is the master frontend specification, implementation must remain incremental.

Start with:

```text
FOUNDATION
↓
APP SHELL
↓
DESIGN SYSTEM
↓
MOCK/API ARCHITECTURE
↓
DASHBOARD
↓
PEOPLE
↓
ACADEMICS
↓
ATTENDANCE
↓
EXAMINATIONS
↓
FINANCE
↓
PLACEMENT
↓
CAMPUS
↓
INFRASTRUCTURE
↓
DOCUMENTS
↓
INTELLIGENCE
```

Complete each phase properly before moving to the next.

Do not create 100 incomplete screens just to claim that all modules exist.

---

# DEFINITION OF DONE FOR EACH MODULE

A module is considered complete only when it has:

* routes
* navigation
* list page
* search
* filtering
* detail page
* create flow where applicable
* edit flow where applicable
* delete/archive flow where applicable
* validation
* loading state
* empty state
* error state
* success feedback
* responsive layout
* mock/service integration
* coherent mock data
* role-aware actions
* reusable components
* API contract
* documentation
* basic tests

---

# FINAL REQUIREMENT

The final frontend should feel like one unified product:

```text
                 CAMPUSOS
                    │
       ┌────────────┼────────────┐
       │            │            │
     PEOPLE      ACADEMICS    OPERATIONS
       │            │            │
       │        ATTENDANCE     FINANCE
       │        EXAMS          PLACEMENT
       │        RESULTS        EVENTS
       │                       HOSTEL
       │                       TRANSPORT
       │                       DOCUMENTS
       │
       └──────────── INTELLIGENCE
                         │
                    AI ASSISTANT
```

Every domain should connect back to the same canonical entities.

The Student record must remain one Student record.

The Faculty record must remain one Faculty record.

The Course/Subject must remain one canonical academic entity.

Do not duplicate entities simply because different modules need different views.

---

# BACKEND INTEGRATION PREPARATION

When frontend development is complete, the future integration should conceptually become:

```text
CURRENT

Page
 ↓
Service
 ↓
Mock Adapter


FUTURE

Page
 ↓
Service
 ↓
HTTP/API Adapter
 ↓
FastAPI
 ↓
Domain Service
 ↓
PostgreSQL
```

The UI should not need a major rewrite when this happens.

That is a core architectural requirement.

---

# FINAL STOP CONDITION

When beginning this task:

1. Inspect the existing project.
2. Preserve useful existing work.
3. Establish/refactor the frontend foundation.
4. Build the design system.
5. Build the application shell.
6. Build the service/mock/API contract architecture.
7. Begin implementing the frontend roadmap in order.
8. Verify each completed phase.
9. Run lint/type checking/build.
10. Fix discovered issues.
11. Document the work.

Do NOT return a huge list claiming everything is complete if it is not.

Report exactly:

```text
Frontend phase completed:
Files created:
Files modified:
Routes implemented:
Components created:
Services created:
Mock domains implemented:
Tests:
Build status:
Known issues:
Next frontend phase:
```

Most importantly:

**Do not start backend implementation again.**

**Do not automatically move to another backend step.**

**The current mission is to turn CampusOS into a complete, polished, connected frontend product that can later be powered by the already-planned FastAPI/PostgreSQL backend.**

</USER_REQUEST>
<ADDITIONAL_METADATA>
The current local time is: 2026-09-30T23:07:58+05:30.

The user's current state is as follows:
Active Document: c:\Users\Likethan KJ\Documents\project\VSB ERP\apps\api\app\models\__init__.py (LANGUAGE_PYTHON)
Cursor is on line: 1
Other open documents:
- c:\Users\Likethan KJ\Documents\project\VSB ERP\docs\product\roadmap.md (LANGUAGE_MARKDOWN)
- c:\Users\Likethan KJ\Documents\project\VSB ERP\apps\web\src\app\app\placement\page.tsx (LANGUAGE_TSX)
- c:\Users\Likethan KJ\Documents\project\VSB ERP\apps\web\src\app\app\notifications\page.tsx (LANGUAGE_TSX)
- c:\Users\Likethan KJ\Documents\project\VSB ERP\apps\web\src\app\app\clubs\[id]\page.tsx (LANGUAGE_TSX)
- c:\Users\Likethan KJ\Documents\project\VSB ERP\apps\api\app\api\v1\router.py (LANGUAGE_PYTHON)
</ADDITIONAL_METADATA>
<USER_SETTINGS_CHANGE>
The user changed setting `Model Selection` from None to Gemini 3.8 Flash (High). No need to comment on this change if the user doesn't ask about it. If reporting what model you are, please use a human readable name instead of the exact string.
</USER_SETTINGS_CHANGE>