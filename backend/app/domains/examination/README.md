# Examination Domain (`app/domains/examination`)

## Purpose

Manages internal assessments, semester-end examinations, invigilation duties, mark entry, grade scale computation, and report card generation.

## Key Entities

- `ExamSchedule`
- `Assessment` (Continuous Internal Evaluation / University Exam)
- `AssessmentMark`
- `GradeScale` (Absolute / Relative grading)
- `ExamResult` (Semester GPA / Cumulative CGPA)

## Boundaries & Constraints

- Validates student eligibility against Attendance thresholds and Finance fee clearance before issuing hall tickets.
- Academic results are published as immutable historical records.
