# Attendance Domain (`app/domains/attendance`)

## Purpose

Records lecture attendance, laboratory sessions, biometric hardware logs, and student leave workflows.

## Key Entities

- `AttendanceSession` (Period/Lecture slot)
- `AttendanceRecord` (Student status: PRESENT, ABSENT, EXCUSED, LATE)
- `StudentLeaveRequest` (Medical / On-Duty / Personal leave)

## Boundaries & Constraints

- Pulls session schedules from `Academics:TimetableSlot`.
- Pulls enrolled students from `Academics:CourseEnrollment`.
- Exposes attendance statistics as read-only feeds to Examination (for hall ticket clearance) and Placement (for drive eligibility).
