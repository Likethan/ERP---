# ADR-009: Attendance Management Engine Architecture

## Status
Accepted

## Context
In higher education ERP systems, attendance is often naively reduced to a simple percentage counter or a disconnected spreadsheet. However, attendance in an authoritative institutional ERP represents a legally auditable academic record with critical downstream dependencies on:
1. Examination eligibility (mandatory minimum thresholds, e.g., 75%, condonation limits).
2. Accreditation audits (NBA, NAAC, ABET, AICTE instructional hour compliance).
3. Student progression and early warning risk telemetry.
4. Financial aid compliance and guardian communication.

Naively implementing attendance without strict binding to authoritative academic contexts creates catastrophic data anomalies:
- Phantom attendance marked for students who dropped or withdrew from a course.
- Arbitrary classes recorded without course offering or timetable correlation.
- Faculty marking registers for sections they are not authorized to teach.
- Historical percentages silently changing when roster enrollments shift retrospectively.
- Unaudited retroactive edits directly modifying locked records.

## Decision
We architected the CampusOS Attendance Management Engine under the following principles:

### 1. Authoritative Academic Binding
Attendance does NOT construct its own academic universe. Every teaching session (`AttendanceSession`) strictly references the canonical entities established in Step 4 and Step 5:
`Tenant -> Academic Year -> Semester -> Course Offering -> Faculty Assignment -> Course Enrollment -> Attendance Session -> Attendance Record`.

### 2. Session Lifecycle & Strict Immutability
Sessions follow a finite state machine:
`SCHEDULED -> OPEN -> MARKED -> LOCKED` (or `CANCELLED`).
- `SCHEDULED`: Instantiated from authoritative timetable slots or authorized manual creation.
- `OPEN`: Register opened by the assigned faculty instructor.
- `MARKED`: Student attendance statuses recorded in bulk within an atomic database transaction.
- `LOCKED`: Session is permanently sealed. Direct row updates (`UPDATE attendance_records`) are prohibited at the service layer and database level. Any change MUST flow through the formal `AttendanceCorrectionRequest` supervised workflow.

### 3. Hierarchical Attendance Policies
Attendance thresholds are never hardcoded. Instead, an `AttendancePolicy` resolution engine evaluates rules according to specificity:
`Course Offering -> Semester -> Program -> Department -> Institution Baseline`.
Policies define:
- Minimum required percentage (default 75%).
- Warning threshold percentage (default 80%).
- Critical shortage threshold percentage (default 65%).
- Condonation eligibility limit (default 65%).
- Late arrival grace period and credit weighting (e.g. 0.5 present credit).
- Leave treatment (excused vs counted as present vs excluded from denominator).
- Effective date ranges for historical calculation reproducibility.

### 4. Dynamic Percentage Derivation
Attendance percentage is NEVER stored as an editable column. It is dynamically computed from authoritative records:
```text
Attendance % = (Eligible Attended Sessions / Eligible Conducted Sessions) * 100
```
This guarantees mathematical reproducibility and prevents stale cached counters.

### 5. Automated Leave Reconciliation
`StudentLeaveRequest` models formal absence workflows (`SICK`, `CASUAL`, `DUTY`, `MEDICAL`, `BEREAVEMENT`). Upon authorized review (`APPROVE`), historical absence records within the date range are retrospectively reconciled to `ON_LEAVE` with an immutable audit entry (`LEAVE_APPROVED`), preventing attendance penalties.

### 6. Supervised Locked Corrections
When mistakes occur in locked sessions, faculty submit an `AttendanceCorrectionRequest`. Authorized HODs or Institution Admins review the request (`APPROVE`/`REJECT`). Upon approval, the target record is updated, and an audit entry (`ATTENDANCE_CORRECTION_APPROVED`) captures previous status, new status, reviewer ID, rationale, and timestamp.

## Consequences

### Positive
- **Tamper-Evident Integrity**: Locked registers prevent unauthorized retrospective modifications.
- **Accreditation Ready**: Direct linkage between timetable slots, course offerings, and conducted registers provides verifiable instructional hour verification.
- **Role Isolation**: Faculty can only mark their assigned course offerings. HODs oversee departmental registers. Students view transparent subject breakdowns.
- **Auditability**: Every transition (`ATTENDANCE_SESSION_CREATED`, `OPEN`, `MARKED`, `LOCKED`, `CORRECTION_REQUESTED`, `CORRECTION_APPROVED`, `LEAVE_APPROVED`) is logged in the tenant-scoped audit journal.

### Negative / Trade-Offs
- Faculty cannot edit locked sessions directly; they must file a correction request. This adds deliberate friction to preserve academic governance.
- Dynamic percentage calculation requires indexed aggregation queries. This is mitigated through composite database indexes on `(tenant_id, course_offering_id, session_date)` and `(tenant_id, student_id, status)`.
