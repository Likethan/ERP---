# Enterprise Academic Timetable, Resource Scheduling & Conflict Resolution Engine Runbook

## Executive Summary

The **CampusOS Timetable, Academic Scheduling, Resource Allocation & Conflict Resolution Engine** (Step 49) provides a unified, production-ready academic scheduling and campus resource orchestration platform.

Aligned with the CampusOS core doctrine — **“One Campus. One System. One Source of Truth.”** — this module coordinates academic timetables across institutions, campuses, departments, programs, faculty, student cohorts, classrooms, laboratories, and academic terms. The engine enables automated constraint-based candidate timetable generation, exclusive resource allocation, multi-factor conflict detection, formal review and publication workflows, controlled change management with impact analysis, RFC 5545 calendar integration, attendance reconciliation, and comprehensive schedule analytics.

> [!NOTE]
> CampusOS contains an Examination & Assessment module with dedicated exam scheduling. This engine manages regular academic term schedules, recurring class sessions, and shared campus resource reservations while ensuring strict separation from exam-specific scheduling.

---

## 1. Architecture & Governance Principles

### 1.1 The Ten Golden Rules of Timetable Governance
1. **Absolute Multi-Tenant Boundary Isolation**: Every timetable schedule, version, session, teaching period, calendar exception, faculty availability record, resource reservation, maintenance window, generation job, conflict report, and change request is scoped strictly by `tenant_id`. Cross-tenant querying or reservation creation is blocked at both database and service layers.
2. **Immutable Published Timetable History**: Once a timetable version is `PUBLISHED`, its sessions cannot be silently overwritten or modified in-place. All subsequent modifications must occur via formal `TimetableChangeRequest` workflows or by staging a new `DRAFT` version that supersedes the prior version upon approval and publication.
3. **Automated Candidate Schedule Isolation**: Constraint-based timetable generation runs always output candidate schedules to isolated `DRAFT` timetable versions. They never mutate or overwrite active, published schedules.
4. **Locked-Session Preservation**: Authorized schedule administrators can lock individual sessions. The constraint solver guarantees that locked sessions are copied verbatim and preserved in their assigned day, time, room, and faculty slots during re-generation.
5. **Multi-Factor Conflict Detection**: Scheduling conflicts (faculty double-booking, room overlap, student cohort clash, room under-capacity, laboratory equipment mismatch, faculty availability violation, holiday collision) are systematically evaluated and surfaced with severity, affected resources, and remediation recommendations.
6. **Exclusive Resource Allocation & Concurrency Safeguards**: Classrooms, auditoriums, and laboratories enforce exclusive reservations. Concurrent booking attempts for overlapping intervals are rejected atomically with `ConflictException` (HTTP 409).
7. **Resource Maintenance & Downtime Windows**: Active maintenance windows on facilities automatically block conflicting session allocations and reservation attempts.
8. **Historical Attendance Preservation**: Schedule modifications and cancellations preserve historical attendance logs (`attendance_sessions` and `attendance_records`). A class cancellation or room move does not rewrite previously recorded student attendance.
9. **Controlled Audience Visibility**: Student-facing endpoints only expose sessions belonging to active, `PUBLISHED` timetable versions. In-flight drafts, candidate versions under review, and unapproved changes remain strictly isolated to authorized academic planners.
10. **Forensic Auditability & Outbox Event Emission**: All schedule creations, version approvals, publications, change approvals, emergency overrides, and resource reservations emit immutable audit logs (`AuditEventCategory.TIMETABLE_*`) and transactional outbox events for downstream notifications.

---

## 2. Domain Data Architecture

```
                               +-----------------------------+
                               |      TimetableSchedule      |
                               +-----------------------------+
                                              | 1
                                              |
                                              | *
                               +-----------------------------+
                               |      TimetableVersion       |<---------+
                               | (Draft, Approved, Published)|          |
                               +-----------------------------+          | candidate_version_id
                                       | 1           | 1                |
                                       |             |                  |
                                       | *           | *                |
                     +-------------------+   +--------------------+     |
                     | TimetableSession  |   | TimetableConflict  |     |
                     +-------------------+   +--------------------+     |
                               |                                        |
               +---------------+---------------+                        |
               |                               |                        |
               v                               v                        |
+------------------------------+ +------------------------------+       |
|    TimetableChangeRequest    | |   TimetableGenerationJob     |-------+
+------------------------------+ +------------------------------+

               +------------------------------+ +------------------------------+
               |     ResourceReservation      | |  ResourceMaintenanceWindow   |
               +------------------------------+ +------------------------------+

               +------------------------------+ +------------------------------+
               |     TeachingPeriodConfig     | |    AcademicCalendarPeriod    |
               +------------------------------+ +------------------------------+

               +------------------------------+ +------------------------------+
               |     FacultyAvailability      | |      ScheduleException       |
               +------------------------------+ +------------------------------+
```

### 2.1 Entity Inventory

| Entity | Database Table | Purpose |
| :--- | :--- | :--- |
| `TimetableSchedule` | `timetable_schedules` | Master schedule container associated with academic year, semester, section/program/department/campus. |
| `TimetableVersion` | `timetable_versions` | Versioned snapshot of the timetable supporting `DRAFT`, `UNDER_REVIEW`, `APPROVED`, `PUBLISHED`, `SUPERSEDED`, and `ARCHIVED` states. |
| `TimetableSession` | `timetable_sessions` | Individual teaching or lab session linking course offering, faculty, room, day of week, start/end time, and lock flag. Synchronizes to canonical `academics_timetable_slots` upon publication. |
| `TeachingPeriodConfig` | `timetable_teaching_periods` | Institutional bell schedule and period template (e.g. Period 1: 09:00-10:00, Lunch: 12:00-13:00). |
| `AcademicCalendarPeriod` | `timetable_calendar_periods` | Defines teaching terms, exam periods, breaks, and holiday ranges. |
| `ScheduleException` | `timetable_schedule_exceptions` | Campus-level calendar exceptions (closures, weather emergencies, makeup days, adjusted bell schedules). |
| `FacultyAvailability` | `timetable_faculty_availability` | Faculty weekly availability windows, preferred days, max daily/weekly teaching hours, and blackout windows. |
| `ResourceReservation` | `timetable_resource_reservations` | Exclusive ad-hoc room and equipment reservations for seminars, makeup classes, meetings, or student events. |
| `ResourceMaintenanceWindow` | `timetable_maintenance_windows` | Scheduled downtime intervals preventing room or facility utilization. |
| `TimetableGenerationJob` | `timetable_generation_jobs` | Tracks asynchronous constraint-solving generation executions, statistics, and metadata. |
| `TimetableConflict` | `timetable_conflicts` | Persisted conflict detection logs with severity, constraint violated, and remediation hints. |
| `TimetableChangeRequest` | `timetable_change_requests` | Formal requests to reschedule, move, swap faculty, or cancel sessions with impact analysis and approval tracking. |
| `TimetablePublication` | `timetable_publications` | Audit log of publication events, target audience, notification dispatch flags, and release notes. |

---

## 3. Constraint-Based Timetable Generation Engine

### 3.1 Constraints Considered
The generation solver (`TimetableService.generate_timetable`) coordinates multi-dimensional scheduling requirements:

- **Hard Constraints (Never relaxed)**:
  - Faculty clash prevention: No instructor can teach two sessions simultaneously.
  - Room double-booking prevention: Exclusive facilities cannot host overlapping sessions.
  - Cohort/section collision prevention: A student section cannot have overlapping mandatory classes.
  - Resource maintenance windows: Facilities under maintenance are excluded from scheduling.
  - Institutional holidays & schedule exceptions: Sessions cannot fall on blacklisted calendar dates.
  - Room capacity check: Room capacity must be greater than or equal to section/offering enrollment.
  - Room type suitability: Laboratory and practical courses require lab/workshop facilities.
- **Soft Constraints & Preferences**:
  - Maximum faculty teaching hours per day/week.
  - Preserved locked sessions: Existing locked sessions are seeded first and kept immutable.
  - Spread of subject lectures across distinct days of the week.

### 3.2 Algorithm Workflow
1. **Candidate Staging**: Creates a fresh `TimetableVersion` in `DRAFT` state with an incremented version number.
2. **Locked Session Seeding**: Copies all `is_locked=True` sessions from the latest existing version into the candidate version, pre-populating occupancy maps.
3. **Offering Retrieval**: Queries active course offerings for the targeted academic term and section, calculating required weekly lecture hours.
4. **Slot & Room Matching**: Iterates over configured time slots and teaching days (Mon-Fri), evaluating room capacity and clash-free availability for faculty and student cohort.
5. **Partial Solution Support**: If complete conflict-free placement is impossible, the engine records scheduled sessions, marks the job as `PARTIAL`, and documents unplaced subjects with specific constraint reasons in `job.result_metadata`.
6. **Review Before Publication**: Planners can inspect candidate versions, make manual adjustments, and validate conflicts before initiating formal review or publication.

---

## 4. Conflict Detection & Resolution Workflow

### 4.1 Conflict Taxonomy

| Conflict Type | Severity | Condition Triggered | Remediation Suggestion |
| :--- | :--- | :--- | :--- |
| `FACULTY_CLASH` | `CRITICAL` | Faculty member assigned to overlapping sessions in same or different schedules. | Reassign one session to co-faculty or shift time slot. |
| `ROOM_DOUBLE_BOOKED` | `CRITICAL` | Facility assigned to multiple sessions or reservations at the same time. | Move session to alternate vacant room of suitable capacity. |
| `COHORT_OVERLAP` | `HIGH` | Same student section scheduled for simultaneous lectures. | Reschedule conflicting session to an open period. |
| `CAPACITY_EXCEEDED` | `MEDIUM` | Section enrollment exceeds room seating capacity. | Reassign session to a larger hall or split section. |
| `FACULTY_UNAVAILABLE` | `HIGH` | Session scheduled during faculty blackout window or approved leave. | Shift session to faculty available window or assign substitute. |
| `MAINTENANCE_COLLISION`| `CRITICAL` | Session scheduled during confirmed facility maintenance downtime. | Select alternate operational facility. |
| `ROOM_UNSUITABLE` | `HIGH` | Laboratory course scheduled in standard classroom (or vice versa). | Relocate session to an approved laboratory resource. |
| `HOLIDAY_COLLISION` | `HIGH` | Session falls on an active institutional holiday or campus closure. | Reschedule to an approved makeup teaching day. |

---

## 5. Timetable Change Management

After a timetable is approved and published, changes must follow an audited lifecycle:

```
  +-------------------------------------------------------+
  |                   CHANGE REQUEST                      |
  |  (RESCHEDULE / CANCEL / ROOM_SWAP / FACULTY_SWAP)     |
  +-------------------------------------------------------+
                             |
                             v
  +-------------------------------------------------------+
  |                   IMPACT ANALYSIS                     |
  | (Checks conflicts, capacity, and affected audiences)  |
  +-------------------------------------------------------+
                             |
              +--------------+--------------+
              |                             |
              v                             v
    [NORMAL APPROVAL]              [EMERGENCY OVERRIDE]
 (HOD / Admin signs off)         (Authorized Planner signs off
              |                    with mandatory reason & audit)
              |                             |
              +--------------+--------------+
                             |
                             v
  +-------------------------------------------------------+
  |                  ATOMIC APPLICATION                   |
  |  - Updates session day/time/room/faculty              |
  |  - Updates linked canonical TimetableEntry            |
  |  - Preserves historical attendance records            |
  |  - Emits TIMETABLE_CHANGE_APPLIED outbox event        |
  +-------------------------------------------------------+
```

---

## 6. Attendance Integration & Record Preservation

CampusOS `AttendanceSession` records represent historical teaching occurrences linked via `timetable_slot_id` (foreign key to `academics_timetable_slots.id`).

1. **Canonical Slot Synchronization**: When a `TimetableVersion` is published, `TimetableService.publish_version` updates or creates corresponding `TimetableEntry` records in `academics_timetable_slots` and assigns `canonical_slot_id` to each session.
2. **Zero Historical Mutation**: Rescheduling, modifying, or cancelling a timetable session updates future scheduling only. Existing `attendance_sessions` and `attendance_records` retain their original dates, slot associations, and attendance states.
3. **Attendance Reconciliation Metric**: `GET /api/v1/timetable/attendance/reconciliation` calculates scheduled versus recorded teaching sessions for every section, identifying coverage percentages and unrecorded periods.

---

## 7. Role-Based Access Control (RBAC)

| Role | Permissions Assigned | Capabilities |
| :--- | :--- | :--- |
| `SUPER_ADMIN` | All `timetable:*` permissions | Complete system control, tenant-wide configuration, overrides, and audits. |
| `INSTITUTION_ADMIN` | All `timetable:*` permissions | Academic scheduling, version approvals, publications, conflict management, reporting. |
| `HOD` | `timetable:read`, `timetable:manage`, `timetable:generate`, `timetable:approve`, `timetable:changes:request`, `timetable:changes:approve`, `timetable:reports:read` | Department timetable authoring, candidate generation, change approvals, department grid views. |
| `FACULTY` | `timetable:read`, `timetable:faculty:availability`, `timetable:changes:request` | Personal teaching schedule view, iCalendar feed sync, availability setting, change requests. |
| `STUDENT` | `timetable:student:self:read` | View published cohort timetable, iCalendar feed export, room locations. |

---

## 8. API Endpoint Inventory

The module exposes 32 REST endpoints under `/api/v1/timetable`:

### Master Schedules & Versioning
- `POST /api/v1/timetable/schedules`: Create master timetable schedule.
- `GET /api/v1/timetable/schedules`: List tenant timetable schedules with filters.
- `GET /api/v1/timetable/schedules/{schedule_id}`: Retrieve timetable schedule by ID.
- `POST /api/v1/timetable/schedules/{schedule_id}/clone`: Clone schedule to a new term.
- `POST /api/v1/timetable/schedules/{schedule_id}/versions`: Create a manual draft version.
- `GET /api/v1/timetable/schedules/{schedule_id}/versions`: List versions for a schedule.
- `GET /api/v1/timetable/versions/{version_id}`: Get version details and sessions.
- `POST /api/v1/timetable/versions/{version_id}/submit-review`: Submit draft for review.
- `POST /api/v1/timetable/versions/{version_id}/approve`: Approve or reject staged version.
- `POST /api/v1/timetable/versions/{version_id}/publish`: Formally publish version to students and faculty.

### Sessions & Grid Views
- `POST /api/v1/timetable/versions/{version_id}/sessions`: Create session in draft version.
- `POST /api/v1/timetable/versions/{version_id}/sessions/batch`: Batch create sessions.
- `PUT /api/v1/timetable/sessions/{session_id}`: Update session details.
- `DELETE /api/v1/timetable/sessions/{session_id}`: Delete session from draft version.
- `GET /api/v1/timetable/grid/section/{section_id}`: Section/cohort timetable matrix.
- `GET /api/v1/timetable/grid/faculty/{faculty_id}`: Faculty individual teaching matrix.
- `GET /api/v1/timetable/grid/room/{room_id}`: Classroom/lab utilization grid.
- `GET /api/v1/timetable/export/ical`: RFC 5545 iCalendar (`.ics`) feed for students and faculty.

### Automated Generation & Conflicts
- `POST /api/v1/timetable/generate`: Launch constraint-based candidate schedule generation.
- `GET /api/v1/timetable/generate/jobs/{job_id}`: Query generation job execution status.
- `POST /api/v1/timetable/conflicts/detect`: Execute multi-factor conflict detection run.
- `GET /api/v1/timetable/conflicts/{schedule_id}`: List persisted conflicts for a schedule.

### Resource Reservations & Maintenance
- `POST /api/v1/timetable/resources/reservations`: Create exclusive resource reservation.
- `DELETE /api/v1/timetable/resources/reservations/{reservation_id}`: Cancel reservation.
- `POST /api/v1/timetable/resources/maintenance`: Register facility maintenance downtime window.

### Faculty Availability & Calendar
- `POST /api/v1/timetable/faculty/availability`: Configure faculty availability windows.
- `GET /api/v1/timetable/faculty/{faculty_id}/workload`: Retrieve faculty teaching workload metric.
- `POST /api/v1/timetable/config/teaching-periods`: Configure institutional teaching periods.
- `POST /api/v1/timetable/config/calendar-periods`: Define academic calendar and term windows.
- `POST /api/v1/timetable/config/exceptions`: Add institutional calendar exceptions/closures.

### Change Management & Analytics
- `POST /api/v1/timetable/changes/requests`: Submit formal schedule change request.
- `POST /api/v1/timetable/changes/requests/{request_id}/review`: Approve/reject change request.
- `GET /api/v1/timetable/attendance/reconciliation`: Reconcile scheduled sessions vs marked attendance.
- `GET /api/v1/timetable/reports/analytics`: Tenant-level timetable analytics and utilization metrics.

---

## 9. Verification & Operational Testing

### 9.1 Database Migration Verification
```bash
.venv\Scripts\pytest.exe tests/test_enterprise_database_migrations.py
```
*Result: 5 passed (100%).*

### 9.2 Timetable Engine Verification Suite
```bash
.venv\Scripts\pytest.exe tests/test_enterprise_timetable_scheduling.py
```
*Result: 10 passed (100%).*

### 9.3 Code Quality & Linting
```bash
.venv\Scripts\ruff.exe check app/models/timetable.py app/schemas/timetable.py app/services/timetable_service.py app/api/v1/timetable.py tests/test_enterprise_timetable_scheduling.py
```
*Result: All checks passed (0 errors).*

### 9.4 OpenAPI & Application Startup
```bash
.venv\Scripts\python.exe -c "from app.main import app; schema = app.openapi(); print('OpenAPI Version:', schema.get('openapi')); print('Timetable endpoints:', len([p for p in schema.get('paths', {}) if 'timetable' in p]))"
```
*Result: OpenAPI 3.1.0 generated successfully with 32 timetable endpoints.*
