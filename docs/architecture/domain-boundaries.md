# CampusOS — Domain & Module Boundaries

A core architectural failure in legacy ERP systems is boundary pollution, where modules directly mutate each other's tables, creating spaghetti dependencies. CampusOS strictly enforces domain-driven boundaries across 11 discrete functional domains.

---

## 1. Domain Catalog & Boundary Responsibilities

```text
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│     Core     │◄────┤    People    │◄────┤  Academics   │
└──────▲───────┘     └──────▲───────┘     └──────▲───────┘
       │                    │                    │
       ├────────────────────┼────────────────────┤
       ▼                    ▼                    ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Attendance  │     │ Examination  │     │   Finance    │
└──────────────┘     └──────────────┘     └──────────────┘
       ▲                    ▲                    ▲
       ├────────────────────┼────────────────────┤
       ▼                    ▼                    ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Placement   │     │    Campus    │     │Infrastructure│
└──────────────┘     └──────────────┘     └──────────────┘
       ▲                    ▲                    ▲
       └────────────────────┼────────────────────┘
                            ▼
                     ┌──────────────┐
                     │ Intelligence │
                     └──────────────┘
```

### 1.1 Core Domain (`app/domains/core`)

- **Entities**: `Institution`, `Campus`, `Department`, `Program`, `AcademicYear`, `Semester`, `Section`.
- **Responsibilities**: Defines the foundational organizational hierarchy of the educational institution.
- **Boundaries**: Provides read-only organizational metadata to all downstream domains.

### 1.2 People Domain (`app/domains/people`)

- **Entities**: `User`, `Role`, `Permission`, `StudentProfile`, `FacultyProfile`, `StaffProfile`, `ParentProfile`.
- **Responsibilities**: Identity authentication, profile information, contact records, parent-student relationships.
- **Boundaries**: **Single Source of Truth** for humans. All other modules link via foreign keys (`student_id`, `faculty_id`).

### 1.3 Academics Domain (`app/domains/academics`)

- **Entities**: `Subject`, `Course`, `Curriculum`, `CourseEnrollment`, `TimetableSlot`.
- **Responsibilities**: Curriculum planning, syllabus management, course enrollments, class scheduling.
- **Boundaries**: Dictates which student is enrolled in which subject during which semester.

### 1.4 Attendance Domain (`app/domains/attendance`)

- **Entities**: `AttendanceSession`, `AttendanceRecord`, `StudentLeaveRequest`.
- **Responsibilities**: Class-by-class attendance capture, biometric sync, leave application & approval workflows, attendance aggregate calculations.
- **Boundaries**: Consumes `TimetableSlot` and `CourseEnrollment` to create attendance sessions.

### 1.5 Examination Domain (`app/domains/examination`)

- **Entities**: `ExamSchedule`, `Assessment`, `AssessmentMark`, `GradeScale`, `ExamResult`.
- **Responsibilities**: Internal assessments (IA/midterms), final university exams, grading rules, GPA/CGPA computation, grade card generation.
- **Boundaries**: Enforces prerequisites and calculates official academic standings.

### 1.6 Finance Domain (`app/domains/finance`)

- **Entities**: `FeeStructure`, `FeeCategory`, `FeeItem`, `StudentInvoice`, `PaymentTransaction`, `Receipt`, `Scholarship`.
- **Responsibilities**: Institutional fee setup, student billing schedules, payment gateway integration, concession tracking, automated fee receipts.
- **Boundaries**: Financial ledger is strictly immutable. Payments record audit trails with zero in-place mutations.

### 1.7 Placement Domain (`app/domains/placement`)

- **Entities**: `CorporatePartner`, `JobDrive`, `EligibilityRule`, `StudentApplication`, `InterviewRound`, `PlacementOffer`.
- **Responsibilities**: Campus recruitments, company onboarding, automated eligibility filtering (CGPA, backlogs, attendance), interview status pipelines.
- **Boundaries**: Queries academic and attendance metrics as read-only inputs for drive eligibility.

### 1.8 Campus Domain (`app/domains/campus`)

- **Entities**: `CampusEvent`, `Club`, `ClubMembership`, `InstitutionalAnnouncement`, `BroadcastNotification`.
- **Responsibilities**: Student clubs, extracurricular events, campus announcements, targeted push/email alerts.

### 1.9 Infrastructure Domain (`app/domains/infrastructure`)

- **Entities**: `Hostel`, `Room`, `BedAllocation`, `TransportRoute`, `Vehicle`, `RouteStop`.
- **Responsibilities**: Dormitory management, bed reservations, bus fleet tracking, transport pass issuance.

### 1.10 Documents Domain (`app/domains/documents`)

- **Entities**: `DocumentCategory`, `StudentDocument`, `CertificateTemplate`, `VerifiedCredential`.
- **Responsibilities**: Secure storage of admission documents, digital issuing of bonafide/transfer certificates, cryptographic verification.

### 1.11 Intelligence Domain (`app/domains/intelligence`)

- **Entities**: `AnalyticsSnapshot`, `AuditLog`, `AIToolDefinition`.
- **Responsibilities**: Executive business intelligence, attendance anomaly detection, dropout risk warnings, permission-governed AI assistant tool calling.

---

## 2. Cross-Domain Communication Rules

1. **No Direct Table Mutation**: A service in domain A must **never** write directly to a table owned by domain B.
2. **Explicit Service APIs**: Inter-domain data retrieval occurs through clearly defined Python service methods (e.g., `AcademicsService.get_student_enrollments(student_id)`).
3. **Idempotent Ingestion**: Data events (e.g., when a student enrolls in a course or makes a payment) are recorded idempotently.
