# CampusOS — Core Institution & People Architecture

## 1. Executive Summary & Design Principles

CampusOS establishes a strict **single-source-of-truth** architecture for all institutional and human entities. Rather than duplicating student, faculty, and departmental definitions across individual operational modules (such as Attendance, Examination, Finance, or Placement), every downstream module in the ERP references the canonical entities defined in this Core + People foundation.

```
Institution
    ↓
Campus (Branch / Location)
    ↓
Department
    ↓
Program (Degree Curriculum)
    ↓
Academic Structure (Academic Year → Semester → Regulation → Batch → Section)

User (Identity / Authentication / RBAC)
    ├── StudentProfile (Academic Cohort, Identifiers, Enrollment Ledger)
    ├── FacultyProfile (Department, Designation, HOD Assignment, Credentials)
    ├── StaffProfile (Central / Departmental Administrative & Technical Support)
    └── GuardianProfile (Family, Emergency Contacts)
```

---

## 2. Core Institutional Domain

### 2.1 Institution & Multi-Campus Hierarchy
- **Institution (`core_institutions`)**: Root administrative identity for the accredited college or university. Bound to `tenant_id` and tracks legal name, code, contact information, website, timezone, and operational status.
- **Campus (`core_campuses`)**: Physical branch or geographic location. A tenant can operate a single campus or multiple campuses under the same institutional governing body. All campus operations are strictly isolated by `tenant_id`.

### 2.2 Department & Canonical HOD Relationship
- **Department (`core_departments`)**: Academic and organizational division (e.g. *Computer Science & Engineering*, *AI & Data Science*).
- **Head of Department (HOD)**: Explicitly linked to a canonical `FacultyProfile` (`head_of_department_id` foreign key) which in turn resolves to the faculty member's `User` record.
  - *No duplicate identity*: The system never stores detached strings such as `hod_name` or `hod_email`.
  - Bidirectional ORM relations allow direct navigation from Department to HOD and from Faculty to HOD status.

### 2.3 Programs & Academic Structure
- **Program (`core_programs`)**: Formal degree curriculum (e.g. *B.E. Computer Science and Engineering*). Linked to a primary academic department, degree level (`UG`, `PG`, `DOCTORAL`), duration in years, total semesters, and graduation credit requirements.
- **Regulation (`core_regulations`)**: Choice Based Credit System (CBCS) or university curriculum framework (e.g., `R2021`, `R2023`).
- **Academic Year (`core_academic_years`)**: Calendar boundaries (e.g., `2024-2025`) with explicit `start_date`, `end_date`, and a unique `is_current` active designation.
- **Semester (`core_semesters`)**: Operational academic terms under an academic year (`semester_number`, `term_type` ODD/EVEN/SUMMER, date ranges).
- **Batch (`core_batches`)**: Student cohort admitted in a specific calendar year under a governing regulation (e.g., `2024-2028 Cohort`).
- **Section (`core_sections`)**: Academic grouping for class delivery (e.g. `Section A`, `Section B`) scoped uniquely within a `(tenant_id, program_id, batch_id, semester_id, name)` composite constraint.

---

## 3. Canonical People Domain

### 3.1 Single Login & Identity Architecture
All persons in CampusOS map to a single authentication identity in `people_users` created during Step 3.
- `User` handles authentication credentials (Argon2id password hashes), active sessions, MFA, and role assignments (`STUDENT`, `FACULTY`, `STAFF`, `INSTITUTION_ADMIN`).
- Distinct profile records expand `User` without polluting authentication:
  - `StudentProfile`
  - `FacultyProfile`
  - `StaffProfile`
  - `GuardianProfile`

### 3.2 Canonical Student Profile & Identifiers
`StudentProfile` represents the student's legal and academic relationship with the institution.
- **Institutional Identifiers**:
  - `admission_number`: Mandatory, unique per tenant.
  - `roll_number`: Institutional or departmental roll identifier (e.g., `25CS101`).
  - `registration_number`: University or state examination board registration number.
- **Demographics & Privacy**: Date of birth, gender, blood group, emergency contact details.
- **Current Affiliation**: Program, Batch, Current Semester, Current Section.

### 3.3 Student Lifecycle State Machine
CampusOS prohibits arbitrary status manipulation through a validated state transition engine:

```
[APPLIED] ──→ [ADMITTED] ──→ [ACTIVE] ──┬──→ [SUSPENDED] ──→ [ACTIVE]
                                        ├──→ [ON_LEAVE]   ──→ [ACTIVE]
                                        ├──→ [GRADUATED]  ──→ [ALUMNI]
                                        └──→ [WITHDRAWN]
```

- Every transition triggers an immutable audit entry in `StudentStatusHistory` (`people_student_status_history`), capturing:
  - `from_status`
  - `to_status`
  - `reason` (mandatory textual justification)
  - `authorized_by_user_id` (authorizing staff/admin user)
  - `effective_date` and timestamp

### 3.4 Non-Destructive Academic History
Historical progression across terms is preserved in `StudentEnrollmentHistory` (`people_student_enrollments`).
When a student moves from Semester 1 Section A to Semester 2 Section B, existing records are retained with start and end dates. This guarantees that past attendance registers, marks sheets, and fee invoices remain tied to the exact historical section and semester without data corruption.

---

## 4. Downstream Integration Contract

Future CampusOS modules integrate directly via canonical foreign keys:

| Downstream Module | Target Entity | Foreign Key Reference | Description |
|:---|:---|:---|:---|
| **Module 5: Attendance** | `StudentProfile` | `student_id` | Class session attendance, biometrics, leave balances |
| **Module 5: Timetable** | `FacultyProfile` | `faculty_id` | Teaching workload, section allocations, slot assignments |
| **Module 6: Examinations** | `StudentProfile` | `student_id` | Exam hall tickets, subject registrations, grades, GPA |
| **Module 7: Finance** | `StudentProfile` | `student_id` | Student fee demands, concession vouchers, payment receipts |
| **Module 9: Placement** | `StudentProfile` | `student_id` | Drive eligibility filters, resume links, placement offers |

No downstream module is permitted to create independent student or faculty tables.
