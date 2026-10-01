# ADR-007: Curriculum and Academic Versioning

## Status

**Accepted**

## Context

Academic curricula in higher education evolve continuously:
- Autonomous colleges and universities revise regulations periodically (e.g., "Regulation 2019", "Regulation 2021", "Regulation 2025 (NEP)").
- Under Regulation 2021, "Data Structures" might be a 4-credit course in Semester 3 with course code `CS301`. Under Regulation 2025, it might become a 3-credit course with an integrated laboratory component in Semester 2 with course code `CS204`.
- Multiple student batches under different regulations study simultaneously on the same campus (e.g. 4th-year students under R2021, 1st-year students under R2025).

A flawed architectural model merges course definition, curriculum mapping, and active semester offerings into a single table. Under such a naive model, updating a subject's credits or semester breaks historical transcripts and GPA calculations for past batches.

## Decision

CampusOS rigorously separates curriculum design into four distinct layers:

```text
┌──────────────────────────────────────────────────────────────────┐
│ 1. Subject (Catalog)                                             │
│    Canonical intellectual topic (e.g. CS101: Data Structures)    │
└─────────────────────────────────┬────────────────────────────────┘
                                  │ Referenced by
                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│ 2. Curriculum Scheme (Regulation & Program Plan)                 │
│    Regulation (e.g. R2025) + Program (e.g. B.Tech CSE)           │
│    Mapping: Subject + Semester No. + Credits + Mandatory/Elective│
└─────────────────────────────────┬────────────────────────────────┘
                                  │ Cohort bound by
                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│ 3. Student Batch                                                 │
│    Admitted cohort (e.g. Class of 2024-2028) bound to Regulation │
└─────────────────────────────────┬────────────────────────────────┘
                                  │ Scheduled in
                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│ 4. Course Offering (Runtime Delivery)                            │
│    Subject + Academic Year + Semester + Section + Faculty        │
│    Actual classroom execution with enrollments & attendance      │
└──────────────────────────────────────────────────────────────────┘
```

1. **`academics_subjects` (Canonical Catalog)**:
   - Contains immutable definitions of academic subjects (subject code, canonical title, default lecture/tutorial/practical/credit hours).

2. **`academics_curriculums` & `academics_curriculum_subjects` (Plan of Study)**:
   - Binds a set of subjects to a specific `Program` and `Regulation`.
   - Specifies semester placement, elective group categorization, and specific credit overrides for that regulation.
   - An approved curriculum scheme is version-locked.

3. **`core_batches` (Student Cohort Mapping)**:
   - Each admitted batch (e.g., CSE 2024-2028) is explicitly linked to a `regulation_id`.
   - All graduation credit requirement checks and degree audit calculations execute against the batch's locked regulation.

4. **`academics_course_offerings` (Runtime Classroom Execution)**:
   - Represents the physical/virtual delivery of a subject in a specific `AcademicYear`, `Semester`, and `Section`.
   - Binds assigned faculty members, timetable slots, student course enrollments, attendance sessions, and internal assessment components.

## Consequences

### Positive
- Different student cohorts under R2019, R2021, and R2025 can study concurrently without any data conflicts.
- Updating syllabus topics or credit allocations for future batches has zero side effects on current or graduated students' transcripts.
- Accurate prerequisite enforcement, degree audit evaluation, and backlogs processing across differing academic regulations.

### Negative / Tradeoffs
- Requires querying through the curriculum mapping join to ascertain a student's graduation requirements.
- Administrative setup requires configuring both the curriculum scheme and the term course offerings.
