# CampusOS — Domain Model Specification

## 1. Domain Vision and Modeling Philosophy

CampusOS is architected not as an administrative silo, but as an **operating system for higher education institutions**. In legacy college ERPs, departments, examinations, attendance registers, and fees exist in separate databases with divergent student identifiers. CampusOS eliminates this with a unified, cohesive domain model grounded in:

> **"One Campus. One System. One Source of Truth."**

---

## 2. Domain Hierarchy and Bounded Contexts

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        CORE ORGANIZATIONAL ANCHOR                      │
│     Institution ──► Campus ──► Department ──► Program ──► Section      │
│          ▲               ▲           ▲                                 │
│          │               │           │                                 │
│          │ (Tenant)      │ (Scope)   │ (Scope)                         │
├──────────┴───────────────┴───────────┴─────────────────────────────────┤
│                             PEOPLE DOMAIN                              │
│       User (AuthN) ────► Profiles (Student, Faculty, Staff, Parent)   │
│             │                                                          │
│             └──────────► Scoped Roles & PBAC Permissions               │
├────────────────────────────────────────────────────────────────────────┤
│                          OPERATIONAL DOMAINS                           │
│  ┌──────────────┐     ┌──────────────┐     ┌────────────────────────┐  │
│  │  Academics   │     │  Attendance  │     │      Examination       │  │
│  │ (Curriculum, │     │  (Sessions,  │     │(Assessments, CIA, End- │  │
│  │  Offerings)  │     │   Records)   │     │  Semester, Published)  │  │
│  └──────┬───────┘     └──────┬───────┘     └───────────┬────────────┘  │
│         │                    │                         │               │
│         ▼                    ▼                         ▼               │
│  ┌──────────────┐     ┌──────────────┐     ┌────────────────────────┐  │
│  │   Finance    │     │  Placement   │     │     Infrastructure     │  │
│  │ (Invoices,   │     │   (Drives,   │     │   (Hostel Allocation,  │  │
│  │  Payments)   │     │    Offers)   │     │  Transport Allocation) │  │
│  └──────────────┘     └──────────────┘     └────────────────────────┘  │
│  ┌──────────────┐     ┌──────────────┐     ┌────────────────────────┐  │
│  │    Campus    │     │  Documents   │     │  Audit & Intelligence  │  │
│  │ (Clubs,      │     │(Storage Meta,│     │   (Immutable Ledger,   │  │
│  │  Events)     │     │ Certificates)│     │     AI Guardrails)     │  │
│  └──────────────┘     └──────────────┘     └────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Deep-Dive Domain Specifications

### 3.1 Domain 1 — Core Organizational Domain

Higher education institutions rarely follow a pure linear tree. CampusOS models the real-world operational reality:
- **`Institution`**: The top-level legal entity and tenant boundary (`tenant_id`). Governs institutional code, branding, default timezone, statutory affiliation, and currency.
- **`Campus`**: Physical branch or site (e.g., "Main Campus", "South City Campus", "Offshore Center"). Owns physical buildings, rooms, hostels, and vehicle fleets.
- **`Department`**: Academic or administrative unit (e.g., "Department of Computer Science & Engineering"). Can be anchored to an institution and maintain academic presence across multiple campuses.
- **`Program`**: Formal degree curriculum (e.g., "B.Tech Computer Science & Engineering", "M.Sc Data Science", "MBA"). Belongs to an academic department; specifies degree type, duration (years), total semester count, and graduation credit requirements.
- **`Regulation` / `CurriculumScheme`**: Statutory academic framework (e.g., "R2021 Autonomous", "R2025 NEP"). Binds academic requirements to cohorts.
- **`Batch`**: Admitted cohort (e.g., "Batch of 2024-2028"). Binds a specific `Program` to a statutory `Regulation`.
- **`AcademicYear`**: Calendar academic operational period (e.g., "2024-2025") with clear start and end dates.
- **`Semester` / `AcademicTerm`**: Discrete teaching term (e.g., "Odd Semester 2024", "Semester 5"). Binds to an `AcademicYear` with start, end, and instructional census dates.
- **`Section`**: Student cohort grouping within a semester (e.g., "CSE-5A", "CSE-5B"). Binds to a `Program`, `Semester`, and `Batch`.

---

### 3.2 Domain 2 — People & Identity Domain

Identity is architecturally split into **Authentication Account** and **Institutional Profiles**:

#### Authentication Account
- **`User` (`people_users`)**: Canonical login record. Owns email, phone number, Argon2id password hash, MFA secrets, active flag, and audit metadata.

#### Institutional Profiles
1. **`StudentProfile` (`people_students`)**:
   - Primary institutional key for learners.
   - Holds statutory identifiers: `admission_number`, `registration_number`, `roll_number`.
   - Personal demographic data: names, date of birth, gender, blood group, citizenship, emergency contacts.
   - Current academic pointers: `batch_id`, `program_id`, `current_semester_id`, `current_section_id`.
   - Lifecycle state: `APPLIED -> ADMITTED -> ACTIVE -> SUSPENDED -> ON_LEAVE -> GRADUATED -> WITHDRAWN -> ALUMNI`.
2. **`FacultyProfile` (`people_faculty`)**:
   - Employee record for instructional and research staff.
   - Holds `employee_code`, `department_id`, `designation` (Professor, Assistant Professor, Lecturer), `qualification`, `specialization`, `joining_date`, `is_hod`, `employment_status`.
3. **`StaffProfile` (`people_staff`)**:
   - Non-teaching administrative and operational staff (Registrar, Accounts, Hostel Wardens, Bus Drivers).
4. **`GuardianProfile` (`people_guardians`)**:
   - Parents and legal sponsors. Holds contact details, relationship type, occupation, and financial sponsorship indicators.
5. **`StudentGuardianRelationship` (`people_student_guardians`)**:
   - Links student to guardians with flags: `is_primary`, `emergency_priority`, `can_pickup_from_hostel`.

#### Historical Academic Identity Preservation
- **`StudentEnrollmentHistory` (`people_student_semester_enrollments`)**:
  - Whenever a student progresses into a new semester, changes section, or repeats a term, an immutable row is generated: `(student_id, academic_year_id, semester_id, section_id, enrollment_status, start_date, completion_date)`.
  - Guarantees historical query fidelity: querying "Who was in Section 3A in Autumn 2023?" yields absolute truth even if students transferred in 2024.
- **`StudentStatusHistory` (`people_student_status_history`)**:
  - Full audit log of student lifecycle transitions with timestamp, previous state, new state, authorizing officer, and business justification.

---

### 3.3 Domain 3 — Authorization Domain (PBAC + Scoped RBAC)

CampusOS avoids hardcoded role checks (`if role == 'admin'`). Authorization is enforced via:
- **`Permission` (`people_permissions`)**: Atomic action strings (`domain:resource:action`), e.g., `students:read`, `attendance:records:write`, `finance:invoices:approve`.
- **`Role` (`people_roles`)**: Named bundle of permissions. Can be system-level (immutable) or tenant-custom.
- **`RolePermission` (`people_role_permissions`)**: Many-to-many junction between roles and permissions.
- **`UserRoleAssignment` (`people_user_roles`)**: Maps a user to a role with optional hierarchical scoping:
  - `tenant_id` (mandatory)
  - `campus_id` (optional: restricts authority to a specific campus)
  - `department_id` (optional: restricts authority to a specific department)

---

### 3.4 Domain 4 — Academics Domain

Separates canonical syllabus from runtime classroom execution:
- **`Subject` (`academics_subjects`)**: Canonical intellectual topic (e.g. `CS301: Data Structures & Algorithms`). Stores credits, lecture/tutorial/practical/self-study hours, subject type (THEORY, LAB, INTEGRATED, ELECTIVE).
- **`CurriculumScheme` (`academics_curriculums`)**: Program curriculum governed by a `Regulation`.
- **`CurriculumSubject` (`academics_curriculum_subjects`)**: Binds a `Subject` into a `CurriculumScheme` for a given semester number, specifying mandatory vs elective status, elective group, and regulation-specific credit rules.
- **`CourseOffering` (`academics_course_offerings`)**: Concrete operational delivery of a subject for an `AcademicYear`, `Semester`, and `Section`.
- **`CourseFacultyAssignment` (`academics_course_faculty`)**: Maps faculty members to offerings with roles (`PRIMARY_INSTRUCTOR`, `CO_INSTRUCTOR`, `LAB_ASSISTANT`).
- **`CourseEnrollment` (`academics_course_enrollments`)**: Individual student registration in an offering (`REGULAR`, `REPEAT`, `ARREAR`, `AUDIT`).
- **`TimetableSlot` (`academics_timetable_slots`)**: Weekly schedule slot (`day_of_week`, `period_number`, `start_time`, `end_time`, `room_id`, `faculty_id`).

---

### 3.5 Domain 5 — Attendance Domain

High-throughput, tamper-evident class attendance:
- **`AttendancePolicy` (`attendance_policies`)**: Institutional rules per department/program (minimum required percentage, usually 75% or 80%; late arrival grace window; on-duty credit rules).
- **`AttendanceSession` (`attendance_sessions`)**: An individual lecture, lab, or tutorial period created from a timetable slot or manually. Status transitions: `OPEN -> SUBMITTED -> LOCKED`.
- **`AttendanceRecord` (`attendance_records`)**: Student-level status: `PRESENT`, `ABSENT`, `LATE`, `EXCUSED`, `ON_DUTY`.
- **`AttendanceCorrectionRequest` (`attendance_corrections`)**: Controlled correction workflow when an instructor or student disputes a mark after lock. Requires justification and HOD approval.
- **`StudentLeaveRequest` (`attendance_leave_requests`)**: Medical, casual, or institutional on-duty leave applications with proof document references and multi-level approval.
- **Derivability**: Official attendance percentage is dynamically derived from `AttendanceRecord` counts. Materialized summary tables (`StudentAttendanceSummary`) serve as performance read-caches only.

---

### 3.6 Domain 6 — Examination & Grading Domain

Academic evaluation requires uncompromised data integrity:
- **`GradeScale` (`examination_grade_scales`)** & **`GradeScaleItem` (`examination_grade_items`)**: Defines letter grades, GPA points, percentage ranges, and passing criteria (e.g., 10-point UGC scale).
- **`ExamTerm` (`examination_terms`)**: Examination cycle (e.g. "End Semester Examinations Nov 2024", "Internal Assessment Cycle 1").
- **`Assessment` (`examination_assessments`)**: Component evaluation (CIA 1, CIA 2, Assignment, Model Exam, University Theory, Practical Viva). Stores max marks and syllabus weightage.
- **`ExamSchedule` (`examination_schedules`)**: Date, session, examination hall/room, invigilator assignments.
- **`StudentAssessmentMark` (`examination_student_marks`)**: Raw marks scored, presence status (`is_absent`), evaluator ID, moderation marks, and remarks.
- **`SemesterExamResult` (`examination_results`)**: Official semester transcript result per student per course offering. Includes internal marks, external marks, final grade letter, grade point, credits earned, and pass/fail standing.
- **Immutability Barrier**: Once `SemesterExamResult` is updated to `PUBLISHED`, direct SQL updates are disabled. Any subsequent adjustment is executed via `examination_corrections` with approval by the Controller of Examinations.

---

### 3.7 Domain 7 — Finance & Billing Domain

Real-world institutional billing modeled as an immutable double-entry ledger:
- **`FeeCategory` (`finance_fee_categories`)**: Tuition, Hostel, Transport, Examination, Lab, Caution Deposit, Library, Alumni Fund.
- **`FeeStructure` (`finance_fee_structures`)**: Academic fee matrix for a `Program`, `AcademicYear`, `Batch`, and admission quota (Government, Management, NRI, Lateral Entry).
- **`FeeItem` (`finance_fee_items`)**: Line items within a structure (amount, due dates, mandatory flag).
- **`StudentFeeConcession` (`finance_concessions`)**: Merit scholarships, economic waivers, or sibling concessions linked to specific fee categories.
- **`Invoice` (`finance_invoices`)**: Institutional billing statement issued to a student. Contains human-readable `invoice_number`, term, total billed, concession credits, net payable, total paid, and balance. States: `DRAFT -> ISSUED -> PARTIALLY_PAID -> PAID -> OVERDUE -> CANCELLED`.
- **`InvoiceLineItem` (`finance_invoice_items`)**: Specific fee head on an invoice.
- **`PaymentTransaction` (`finance_payments`)**: Physical or digital inflow of capital. Records bank reference, payment gateway token, mode (`CASH`, `CHEQUE`, `DD`, `NEFT_RTGS`, `UPI`, `PAYMENT_GATEWAY`), gross amount, and status (`INITIATED -> SUCCESS -> FAILED -> REVERSED`).
- **`PaymentAllocation` (`finance_allocations`)**: Explicit mapping between a successful `PaymentTransaction` and an `Invoice` (and line item). Guarantees that payments cannot be over-allocated.
- **`Receipt` (`finance_receipts`)**: Sequentially numbered, legal receipt generated upon successful payment allocation.
- **`RefundTransaction` (`finance_refunds`)**: Controlled cash or bank refund with approval signatures.
- **`FinancialAdjustment` (`finance_adjustments`)**: Debit or credit notes for billing corrections without mutating existing invoices.

---

### 3.8 Domain 8 — Placement & Corporate Relations Domain

Recruitment pipeline tracking from corporate outreach to offer acceptance:
- **`Company` (`placement_companies`)**: Corporate recruiter profile, industry sector, tier rating, website.
- **`CompanyContact` (`placement_contacts`)**: HR recruiter contact info and campus hiring history.
- **`JobDrive` (`placement_drives`)**: Recruitment event for an `AcademicYear` (`ON_CAMPUS`, `POOLED`, `OFF_CAMPUS`, `VIRTUAL`).
- **`JobPosition` (`placement_positions`)**: Job profile, title, CTC (LPA), monthly stipend, location, service agreement/bond terms.
- **`PlacementEligibilityRule` (`placement_eligibility_rules`)**: Automated rule engine: min CGPA, max active backlogs, max historical backlogs, minimum attendance %, allowable departments/programs.
- **`PlacementApplication` (`placement_applications`)**: Student application to a position. States: `APPLIED -> ELIGIBLE -> SHORTLISTED -> IN_SELECTION -> OFFERED -> REJECTED -> WITHDRAWN`.
- **`InterviewRound` (`placement_interview_rounds`)**: Sequential hiring stages (Online Assessment, Coding Test, Technical Round 1, Technical Round 2, HR Interview).
- **`InterviewRoundResult` (`placement_interview_results`)**: Round scores and progression decisions (`CLEARED`, `ELIMINATED`, `ON_HOLD`).
- **`PlacementOffer` (`placement_offers`)**: Formal employment offer tracking CTC, offer letter storage key, validity deadline, and student decision (`PENDING`, `ACCEPTED`, `REJECTED`, `RENEGED`).

---

### 3.9 Domain 9 — Campus Community & Events Domain

Institutional social fabric and communication:
- **`Club` (`campus_clubs`)**: Student societies, technical chapters (IEEE, ACM), cultural and sports bodies.
- **`ClubMembership` (`campus_club_memberships`)**: Historical and active student memberships and leadership positions (`MEMBER`, `EXECUTIVE`, `LEAD`, `PRESIDENT`).
- **`CampusEvent` (`campus_events`)**: Workshops, symposiums, hackathons, guest lectures, cultural fests.
- **`EventRegistration` (`campus_event_registrations`)**: Participant registrations, attendance check-ins, certificate issuance links.
- **`CampusAnnouncement` (`campus_announcements`)**: Broadcast notices with audience targeting parameters (all campus, specific department, program, semester, section, or role).
- **`Notification` (`campus_notifications`)**: Personal notification inbox instances delivered across channels (`IN_APP`, `EMAIL`, `SMS`, `PUSH`).

---

### 3.10 Domain 10 — Infrastructure Logistics Domain (Hostel & Transport)

Resource allocation and safety:

#### Hostel Logistics
- `Hostel` (`infrastructure_hostels`): Residential facility (gender type, warden user ID, campus ID).
- `HostelBlock`, `HostelFloor`, `HostelRoom`, `HostelBed`: Physical hierarchy down to individual beds.
- `HostelAllocation` (`infrastructure_hostel_allocations`): Historical and active bed assignments (`check_in_date`, `check_out_date`, status `ALLOCATED -> VACATED -> CANCELLED`).
- `HostelLeavePass` (`infrastructure_hostel_passes`): Outing and home leave passes with parental consent tracking and biometric check-in/out timestamps.
- `HostelComplaint` (`infrastructure_hostel_complaints`): Maintenance ticketing (plumbing, electrical, hygiene, Wi-Fi) with resolution SLA tracking.

#### Transport Logistics
- `TransportVehicle` (`infrastructure_vehicles`): Fleet buses and vans (registration number, seating capacity, fitness certificate dates).
- `TransportDriver` (`infrastructure_drivers`): Driver licenses and emergency contacts.
- `TransportRoute` (`infrastructure_routes`): Route itineraries connecting campus to municipal neighborhoods.
- `TransportStop` (`infrastructure_stops`): Ordered stops along a route with pickup/drop timetables and fee tiers.
- `TransportAllocation` (`infrastructure_transport_allocations`): Student/staff bus passes linked to specific stops, academic years, and fee structures.

---

### 3.11 Domain 11 — Documents & Audit Domain

Non-relational binary decoupling and institutional accountability:

#### Documents Management
- Relational tables store metadata only: file name, MIME type, size, SHA-256 checksum, S3/MinIO bucket, and storage key.
- `DocumentCategory` (`documents_categories`): Admission records, government IDs, transfer certificates, fee receipts, examination transcripts.
- `StorageDocument` (`documents_storage_records`): Canonical document metadata record.
- `StudentDocumentRecord` (`documents_student_records`) & `FacultyDocumentRecord` (`documents_faculty_records`): Links documents to students/faculty with verification status (`PENDING -> VERIFIED -> REJECTED`), verifier ID, and rejection remarks.
- `CertificateTemplate` (`documents_certificate_templates`): Jinja/HTML templates for bonafide, study, and course completion certificates.
- `IssuedCertificate` (`documents_issued_certificates`): Cryptographically hashed, verifiable certificates issued to students.

#### Audit Trail
- `AuditLog` (`intelligence_audit_logs`): Immutable audit record answering WHO, WHAT, WHEN, WHERE, WHICH ENTITY, WHICH RECORD, BEFORE JSON, AFTER JSON, and BUSINESS CONTEXT.
