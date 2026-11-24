# Academics Domain (`app/domains/academics`)

## Purpose

Governs syllabus, curriculum, course offerings, student enrollments, faculty course allocations, and timetable schedules.

## Key Entities

- `Subject` / `Course`
- `Curriculum`
- `CourseEnrollment`
- `FacultyAllocation`
- `TimetableSlot`

## Boundaries & Constraints

- Serves as the authority for class schedules used by the Attendance module.
- Serves as the authority for course enrollments used by Examinations for mark recording.
