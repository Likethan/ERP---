# Core Domain (`app/domains/core`)

## Purpose

Manages the institutional and academic organizational hierarchy.

## Key Entities

- `Institution` (Top-level tenant)
- `Campus`
- `Department`
- `Program` (Degree/Discipline)
- `AcademicYear`
- `Semester`
- `Section`

## Boundaries & Constraints

- Provides read-only organizational metadata to all downstream operational domains.
- Downstream domains must never mutate Core tables directly.
