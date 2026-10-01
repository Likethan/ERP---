# Examination & Assessment Engine Architecture

## 1. Subsystem Overview
The Examination & Assessment Engine is the authoritative academic evaluation subsystem of CampusOS. It governs the end-to-end lifecycle from course component configuration and examination scheduling through to marks entry, supervised revisions, automated grade mapping, and controlled result publication.

```text
Course Offering (Step 5)
       │
       ▼
Assessment Configuration (Weights <= 100%)
       │
       ▼
Exam Scheduling & Conflict Detection (Room, Student, Invigilator)
       │
       ▼
Attendance Eligibility Snapshot (Consuming Step 6 Policy & Summary)
       │
       ▼
Class Roster Marks Entry & Drafts
       │
       ▼
Assessment Finalization (Record Lock)
       │
       ▼
Grade & GPA Calculation (10-Point UGC Scale)
       │
       ▼
Official Result Publication (Student Portal Visibility)
```

## 2. Core Principles & Domain Boundaries
1. **Canonical Academic Binding**: Examination models reference the canonical Course Offering, Course Enrollment, Student, Faculty, and Academic Year records. No duplicate academic entities exist.
2. **Component Modularity**: A Course Offering may define arbitrary assessment components (`INTERNAL`, `MIDTERM`, `ASSIGNMENT`, `LAB`, `END_SEMESTER`, `PROJECT`, `VIVA`).
3. **Mathematical Weightage Safety**: Total configured weightage across components for a course cannot exceed 100.0%.
4. **Attendance Integration**: Minimum attendance criteria are evaluated dynamically against active policies in the Attendance Engine and recorded as an immutable snapshot.
5. **Supervised Correction Workflow**: Locked marks cannot be silently modified. Changes require a `MarkCorrectionRequest` with justification and authorized sign-off.
6. **Student Data Shielding**: Unpublished results are strictly protected from student self-service queries at the database query level.

## 3. Component Interaction Diagram

```text
┌─────────────────────────────────────────────────────────────┐
│                       Course Offering                       │
└──────────────┬───────────────────────────────┬──────────────┘
               │                               │
               ▼                               ▼
    ┌──────────────────────┐        ┌──────────────────────┐
    │ Attendance Engine    │        │ Assessment Component │
    │ (Step 6 Sessions &   │        │ (Sequence, Max Marks,│
    │  Condonation Policy) │        │  Passing, Weight %)  │
    └──────────┬───────────┘        └──────────┬───────────┘
               │                               │
               ▼                               ▼
    ┌──────────────────────┐        ┌──────────────────────┐
    │ Exam Eligibility     │        │ Exam Schedule        │
    │ Snapshot             │        │ (Room, Time, Faculty,│
    │                      │        │  Conflict Detection) │
    └──────────┬───────────┘        └──────────┬───────────┘
               │                               │
               └───────────────┬───────────────┘
                               ▼
                    ┌──────────────────────┐
                    │ Student Marks Roster │
                    │ (Numeric, ABSENT,    │
                    │  WITHHELD, MALPRAC)  │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Grade Engine         │
                    │ (10-Pt UGC Scale)    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Semester Exam Result │
                    │ (DRAFT -> PUBLISHED) │
                    └──────────────────────┘
```

## 4. GPA & Transcript Extension Foundation
The engine models `SemesterExamResult` with:
- `credits`
- `grade_point`
- `credits_earned`
- `result_status` (`PASS`, `FAIL`, `ABSENT`, `WITHHELD`)
- `publication_status` (`DRAFT`, `FINALIZED`, `PUBLISHED`)

`StudentSemesterTranscript` computes:
```text
Semester GPA = Sum(Credits * Grade Point for passing courses) / Sum(Credits Registered)
```
This foundation seamlessly supports future Cumulative GPA (CGPA), University Rank Lists, and Degree Award verifications.
