# Attendance Management Engine Architecture

## 1. Subsystem Overview
The Attendance Management Engine in CampusOS provides an operational, high-throughput, audit-grade attendance registration and compliance subsystem. It directly binds institutional teaching activities to authoritative Step 5 academic structures without duplicating academic models.

```text
Academic Year
    └── Semester
          └── Section
                └── Course Offering
                      ├── Faculty Assignment (Authorized Instructors)
                      ├── Course Enrollment (Eligible Students)
                      └── Attendance Session (Class Registers)
                            └── Attendance Records (PRESENT / ABSENT / LATE / EXCUSED / ON_LEAVE)
```

## 2. Core Domain Entities

### AttendancePolicy
Configurable rules engine governing percentage calculations, thresholds, late penalties, and leave treatment.
- Hierarchical resolution: Course Offering -> Semester -> Program -> Department -> Institution Baseline.
- Versioned by `effective_from` and `effective_to` to preserve historical integrity.

### AttendanceSession
Represents one discrete instructional period or laboratory class.
- Bound to `CourseOffering`, `FacultyProfile`, `Section`, `AcademicYear`, and `Semester`.
- Origination: Instantiated from authoritative timetable slots (`/from-timetable`) or authorized manual scheduling.
- Lifecycle: `SCHEDULED -> OPEN -> MARKED -> LOCKED`.

### AttendanceRecord
The attendance status of one enrolled student for one teaching session.
- Database constraint: `UniqueConstraint("tenant_id", "session_id", "student_id")` prevents double marking.
- Statuses: `PRESENT`, `ABSENT`, `LATE`, `EXCUSED`, `ON_LEAVE`.

### StudentLeaveRequest
Student absence workflow with authorized review (`PENDING`, `APPROVED`, `REJECTED`, `CANCELLED`).
- Validates date ranges and prevents overlapping requests.
- Retrospective impact: Approving a leave request reconciles existing absences to `ON_LEAVE`.

### AttendanceCorrectionRequest
Supervised correction mechanism for locked sessions.
- Captures original status, requested mutation, justification, and approval notes.
- Only authorized HODs and Institution Admins can approve modifications.

### AttendanceAlert
Automated notification and risk tracking entity triggered when student attendance breaches warning (<80%) or critical (<65%) policy thresholds.

## 3. Calculation Methodology
Attendance percentages are dynamically computed from authoritative records:
```text
Attendance % = (Eligible Attended Sessions / Eligible Conducted Sessions) * 100
```
Where:
- **Eligible Conducted Sessions (Denominator)**: All sessions for the course with status `MARKED` or `LOCKED`. Cancelled sessions are excluded. If policy defines `exclude_excused_from_total = True`, excused sessions are deducted from denominator.
- **Eligible Attended Sessions (Numerator)**: `PRESENT` sessions + (`LATE` sessions * `late_weight`) + (`EXCUSED` sessions if policy permits) + (`ON_LEAVE` sessions if policy permits).

## 4. Security & Role Permissions
- `attendance:read`: Read sessions, student summaries, and rosters.
- `attendance:mark`: Open registers and submit bulk attendance records for authorized course offerings.
- `attendance:update`: Update unmarked session metadata.
- `attendance:lock`: Permanently lock attendance sessions.
- `attendance:correct`: Request a supervised correction on a locked session.
- `attendance:approve_correction`: Review and approve/reject correction requests (HOD / Admin).
- `leave:read`: View student leave applications.
- `leave:create`: Submit student leave requests.
- `leave:approve` / `leave:reject`: Review and approve/reject student leaves (HOD / Admin).
- `attendance_policy:read` / `attendance_policy:create` / `attendance_policy:update`: Configure attendance rules.
