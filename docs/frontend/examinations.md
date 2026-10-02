# CampusOS Examination & Assessment Frontend Architecture

## 1. Overview & Pipeline Philosophy

The CampusOS Examination & Assessment module provides an enterprise-grade academic evaluation backbone for higher education institutions. Operating strictly under the **Frontend-First** architecture (`Page → Component → Service → Mock Adapter → Future FastAPI API`), the module implements a robust, continuous evaluation pipeline with zero modifications to the existing FastAPI backend.

### End-to-End Evaluation Workflow

```text
Course Offering (Academics)
          ↓
Assessment Scheme Configuration
          ↓
Assessment Components & Weightages
          ↓
Central Examination Cycles
          ↓
Exam Timetable & Room Scheduling (with real-time conflict detection)
          ↓
Student Eligibility & Attendance Gate (75% threshold with HOD condonation)
          ↓
Marks Entry Matrix (Numeric bounds, ABSENT, MALPRACTICE, WITHHELD)
          ↓
Supervised Mark Corrections (Immutable audit trail & HOD sign-off)
          ↓
Assessment Marks Finalization Lock
          ↓
UGC 10-Point CBCS Grade Calculation
          ↓
Course Result Compilation
          ↓
Cohort Result Finalization
          ↓
Administrative Result Publication Batches (deliberate release & revocation)
```

---

## 2. Route Inventory

| Route | Subsystem | Description | Primary Users |
| :--- | :--- | :--- | :--- |
| `/app/examinations` | Operations Hub | High-level metrics, active cycles, debarment attention banner, grade distribution | COE, HOD, Admin |
| `/app/examinations/assessments` | Schemes Ledger | Course evaluation schemes, multi-component builder, weightage validation | Faculty, HOD, COE |
| `/app/examinations/assessments/[id]` | Scheme 360° | Component weights, cohort scoring status, lifecycle audit timeline | Faculty, HOD |
| `/app/examinations/schedules` | Exam Timetable | Conflict-aware timetable roster, 6-step guided scheduling wizard | COE, Exam Cell |
| `/app/examinations/schedules/[id]` | Schedule Detail | Room capacity, assigned invigilator, candidate roster, collision audit | Exam Cell, Invigilators |
| `/app/examinations/eligibility` | Attendance Gate | 75% attendance evaluation ledger, condonation review & exception audit | HOD, COE, Dean |
| `/app/examinations/marks` | Scoring Matrix | High-speed marks entry, draft auto-save, non-numeric flags, lock guard | Faculty, Evaluators |
| `/app/examinations/results` | Results Ledger | CBCS grades, weighted scores, cohort finalization modal, scale reference | COE, HOD, Admin |
| `/app/examinations/results/[id]` | Result 360° | Candidate result transcript breakdown, GPA, credits, publication timeline | Student, Advisor, COE |
| `/app/examinations/publications` | Publications | Batches ledger, Academic Senate ratification release, deliberate revocation | COE, Academic Registrar |
| `/app/examinations/reports` | Multi-Format Reports | Export-ready audit reports (completion, rosters, schedules, eligibility, CSV) | COE, HOD, Auditors |

---

## 3. Entity Continuity Across Modules

No duplicate entities were created. The module integrates seamlessly with foundational CampusOS entities:

- **People**:
  - `Student`: `id`, `name`, `rollNumber`, `department`, `semester`, `section`
  - `Faculty`: `id`, `name`, `department`, `designation`
- **Academics**:
  - `CourseOffering`: `id`, `courseCode`, `courseName`, `semester`, `section`, `credits`
  - `AcademicYear` & `Semester`: Session term references (`2026-2027`, `Semester 5`)
- **Attendance**:
  - `AttendanceSummary`: Real-time session attendance percentages feed directly into the eligibility evaluation gate (`75.0%` statutory threshold).

---

## 4. Role-Based Access Control (RBAC) Matrix

| Operation / Capability | SUPER_ADMIN / COE | HOD | FACULTY | STUDENT |
| :--- | :---: | :---: | :---: | :---: |
| View Examination Hub & Telemetry | Full Institutional | Departmental | Assigned Courses | Personal Enrolled |
| Configure Assessment Schemes | Yes | Yes (Dept) | View Only | No |
| Create / Edit Exam Schedules | Yes | Yes (Dept) | View Assigned | View Enrolled |
| Review Eligibility / Condonations | Yes | Yes (Dept) | No | View Own Status |
| Enter / Draft Assessment Marks | Yes | Read Only | Yes (Assigned) | No |
| Finalize Assessment Scheme | Yes | Yes (Dept) | Yes (Course Owner) | No |
| Request Mark Correction Petition | Yes | Yes | Yes (Assigned) | No |
| Approve / Reject Mark Corrections | Yes | Yes (Authoritative) | No | No |
| Finalize Course / Cohort Results | Yes | Yes (Dept) | No | No |
| Deliberately Publish Result Batches | Yes (Exclusive) | No | No | No |
| Revoke Published Result Batches | Yes (Exclusive) | No | No | No |
| View Published Result Transcripts | Yes | Yes | Yes | Yes (Own Only) |
| View Unpublished / Draft Results | Yes | Yes | Yes | Strictly Prohibited |

---

## 5. Mock Adapter Isolation & Backend Readiness

All client components communicate through `examinationsService`, an in-memory reactive mock adapter. The service contracts mirror standard FastAPI REST conventions:
- Strict `ApiResponse<T>` envelope
- Standard query filtering parameters (`examinationId`, `department`, `semester`, `search`)
- Pure calculation helper separation (`grading-calculator.ts`)
- Zero DOM/component mutation of internal data arrays

When FastAPI examination endpoints and SQLAlchemy tables are provisioned in future milestones, the frontend code will remain completely untouched; only the service layer fetch targets will switch from local memory to remote HTTP endpoints.
