# ADR-010: Examination & Assessment Engine Architecture

## Status
Accepted

## Context
In higher education institutions, examinations and academic evaluations form the authoritative legal record of student attainment, qualification, and accreditation eligibility. Many enterprise systems compromise academic integrity by:
1. Conflating scheduled exam events with individual assessment components.
2. Hardcoding grading scales into user interfaces or client scripts.
3. Allowing arbitrary mark overwrites on finalized student registers without audit trails.
4. Exposing preliminary or draft marks to students prior to official publication by the Controller of Examinations.
5. Duplicating canonical academic entities (Students, Courses, Semesters) into a disconnected "Exam Module."
6. Failing to check attendance prerequisites established by statutory university regulations.

## Decision
We architected the CampusOS Examination & Assessment Engine as an authoritative academic subsystem with strict end-to-end lifecycle integrity:

```text
Course Offering
      ↓
Assessment Configuration (Weightage <= 100%)
      ↓
Assessment Component
      ↓
Exam Schedule & Conflict Detection
      ↓
Exam Eligibility Snapshot (Step 6 Attendance Engine)
      ↓
Class Roster Marks Entry (Numeric & Non-numeric)
      ↓
Assessment Finalization (Lock)
      ↓
Automated Grade & Result Calculation (10-Point Scale)
      ↓
Controlled Result Publication
```

### 1. Authoritative Domain Consumption
The Examination Engine does NOT create shadow academic models. It directly consumes canonical entities:
- Course Offering & Course Enrollment (from Step 5)
- Student & Faculty Profiles (from Step 4)
- Academic Year, Semester, and Section (from Step 4)
- Attendance Policies & Summary Records (from Step 6)

### 2. Multi-Component Assessment Structure & Weightage Validation
A course offering defines a composite evaluation plan (e.g. Internal 1, Internal 2, Assignment, End Semester). The system mathematically validates cumulative weightages:
- Cumulative weightage must not exceed 100.0%.
- Individual components record sequence, max marks, passing marks, weightage percent, and evaluation type (`INTERNAL`, `MIDTERM`, `ASSIGNMENT`, `LAB`, `END_SEMESTER`, etc.).

### 3. Exam Scheduling & Tri-Factor Conflict Prevention
Scheduled examination papers specify date, time window, room, invigilator, and course offering. The engine executes real-time collision detection:
- **Room Conflict**: Prevents double-booking a physical hall/room for overlapping time slots.
- **Student Conflict**: Detects if any enrolled student in the course offering is already scheduled for another exam at that time.
- **Invigilator Conflict**: Prevents assigning faculty to concurrent exam duties.

### 4. Step 6 Attendance Integration & Historical Eligibility Snapshot
Eligibility is computed by consuming `AttendanceService.resolve_effective_policy` and `AttendanceService.get_course_offering_summary`. The resulting assessment eligibility is snapshotted:
- Preserves historical truth: future attendance recalculations do not silently mutate an already finalized examination eligibility decision.
- Supports authorized administrative override with mandatory audit reasoning.

### 5. Atomic Bulk Marks Entry & State Transitions
Marks entry operates on class rosters via atomic database transactions:
- Validates marks range: `0 <= marks <= max_marks`.
- Supports non-numeric outcomes: `ABSENT`, `NOT_ATTEMPTED`, `WITHHELD`, `MALPRACTICE`.
- Supports progressive draft saving (`is_draft: true`) versus formal submission.

### 6. Supervised Audited Corrections for Finalized Marks
Once an assessment is finalized (`is_finalized = true`), row scores are immutable to direct updates. Any revision must proceed through `MarkCorrectionRequest`:
- Records old marks, proposed new marks, old status, new status, requester, reason, reviewer, approval notes, and timestamp.
- Upon administrative approval, ledger values update and an immutable audit event (`MARK_CORRECTION_APPROVED`) is emitted.

### 7. Configurable 10-Point UGC Grading Scale
The grading scale (`GradeScale`) is fully configurable per institution/tenant, seeded by default with the UGC standard:
- `O` (Outstanding): 90–100%, GP 10.0
- `A+` (Excellent): 80–89%, GP 9.0
- `A` (Very Good): 70–79%, GP 8.0
- `B+` (Good): 60–69%, GP 7.0
- `B` (Above Average): 55–59%, GP 6.0
- `C` (Average): 50–54%, GP 5.0
- `F` (Fail): <50%, GP 0.0

### 8. Controlled Publication & Strict Student Data Privacy
Student self-service endpoints (`GET /api/v1/examinations/results`, `GET /api/v1/examinations/transcripts/...`) enforce:
- Only results with `publication_status == "PUBLISHED"` are returned to students.
- Draft, reviewed, and finalized but unpublished results are completely shielded.
- Cross-student access is prohibited (HTTP 403 Forbidden).

## Consequences
- Guarantees zero data discrepancies between Academic, Attendance, and Examination engines.
- Provides cryptographic-grade auditability for university accreditation inspections.
- Lays the exact mathematical foundation for future Transcript Generation, Cumulative CGPA, Academic Risk Detection, and Graduation Audits without structural redesign.
