# Attendance Management Security Architecture

## 1. Multi-Tenant Isolation
Tenant isolation is enforced strictly on every attendance query, session creation, bulk record insertion, leave approval, and correction request.
- All attendance entities (`AttendancePolicy`, `AttendanceSession`, `AttendanceRecord`, `StudentLeaveRequest`, `AttendanceCorrectionRequest`, `AttendanceAlert`) inherit from `TenantScopedModel`.
- Every SQL operation filters by `tenant_id == current_user.tenant_id`.
- Foreign key references (e.g. `student_id`, `course_offering_id`, `faculty_id`) are explicitly verified server-side to ensure they belong to the requesting tenant before persisting records. Cross-tenant references trigger `404 Not Found` or `422 Unprocessable Content`.

## 2. Faculty Authorization
Frontend-only controls are never trusted. When a user submits an attendance register:
```text
User -> FacultyProfile -> CourseFacultyAssignment -> CourseOffering -> AttendanceSession
```
- If a user has `FACULTY` role, the backend verifies that `assignment.faculty_id == user.faculty_id` or that the faculty is an authorized instructor for the course offering.
- Faculty cannot mark attendance for another instructor's course offering unless they possess administrative privileges (`INSTITUTION_ADMIN` or `HOD`).

## 3. Session Immutability & Anti-Tamper Protection
Once an attendance session is transitioned to `LOCKED`:
- Ordinary updates (`PATCH /records/{id}` or `POST /records/bulk`) are blocked with `HTTP 409 Conflict: Attendance session is locked and cannot be modified`.
- Database-level triggers and service layer invariants mandate that any status mutation must proceed through the `AttendanceCorrectionRequest` pipeline.
- Corrections require higher-level oversight (`attendance:approve_correction`), ensuring no instructor can unilaterally retroactively alter attendance.

## 4. Enrollment Roster Validation
Before records are inserted:
- The backend queries active `CourseEnrollment` records for the specific `CourseOffering`.
- Any `student_id` in the bulk payload not actively enrolled in the course offering is rejected with `HTTP 422 Unprocessable Content: Student is not enrolled in this course offering`.
- Duplicate student submissions within the same payload are rejected.

## 5. Audit Logging Trail
Every state change produces an immutable audit record in `intelligence_audit_logs`:
- `ATTENDANCE_SESSION_CREATED`
- `ATTENDANCE_SESSION_OPENED`
- `ATTENDANCE_MARKED`
- `ATTENDANCE_LOCKED`
- `ATTENDANCE_CORRECTION_REQUESTED`
- `ATTENDANCE_CORRECTION_APPROVED`
- `ATTENDANCE_CORRECTION_REJECTED`
- `LEAVE_REQUESTED`
- `LEAVE_APPROVED`
- `LEAVE_REJECTED`

Each audit log captures: `tenant_id`, `user_id`, `action`, `entity_type`, `entity_id`, IP address, and serialized state changes.
