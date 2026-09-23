# People Domain (`app/domains/people`)

## Purpose

The single source of truth for all human entities, authentication identities, role definitions, and permission grants.

## Key Entities

- `User` (Global login and credentials)
- `Role`
- `Permission`
- `StudentProfile` (Unified student record)
- `FacultyProfile`
- `StaffProfile`
- `ParentProfile`
- `ParentStudentRelation`

## Boundaries & Constraints

- **CRITICAL**: The StudentProfile is the sole record of student identity. Modules such as Attendance, Finance, Examinations, and Placements MUST reference `people_students.id` via foreign keys and NEVER duplicate student profile tables.
