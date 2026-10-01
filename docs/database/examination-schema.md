# Examination Engine Database Schema

## 1. Schema Tables

### `grade_scales` & `grade_scale_items`
Defines configurable grading rubrics per institution/tenant.
- `id` (UUID, PK)
- `tenant_id` (UUID, FK -> `tenants.id`, indexed)
- `name` (VARCHAR)
- `is_default` (BOOLEAN)
- `grade_scale_items`:
  - `id` (UUID, PK)
  - `grade_scale_id` (UUID, FK -> `grade_scales.id`)
  - `grade_letter` (VARCHAR)
  - `grade_point` (NUMERIC)
  - `min_mark_percent` (NUMERIC)
  - `max_mark_percent` (NUMERIC)
  - `is_passing` (BOOLEAN)

### `exam_terms`
Represents an examination cycle/session (e.g. End Semester Nov 2026).
- `id` (UUID, PK)
- `tenant_id` (UUID, FK -> `tenants.id`, indexed)
- `academic_year_id` (UUID, FK -> `academic_years.id`, indexed)
- `semester_id` (UUID, FK -> `semesters.id`, indexed)
- `name` (VARCHAR)
- `exam_type` (VARCHAR)
- `start_date` / `end_date` (DATE)
- `status` (VARCHAR: `DRAFT`, `SCHEDULED`, `ONGOING`, `CONCLUDED`, `RESULTS_PUBLISHED`)

### `assessments`
Authoritative assessment component under a Course Offering.
- `id` (UUID, PK)
- `tenant_id` (UUID, FK -> `tenants.id`, indexed)
- `course_offering_id` (UUID, FK -> `course_offerings.id`, indexed)
- `exam_term_id` (UUID, FK -> `exam_terms.id`, nullable)
- `title` (VARCHAR)
- `assessment_type` (VARCHAR: `INTERNAL`, `MIDTERM`, `ASSIGNMENT`, `LAB`, `END_SEMESTER`, etc.)
- `sequence` (INTEGER)
- `max_marks` (NUMERIC)
- `passing_marks` (NUMERIC)
- `weightage_percent` (NUMERIC)
- `is_finalized` (BOOLEAN)
- `finalized_at` (TIMESTAMP)

### `exam_schedules`
Defines physical time/room assignment for scheduled examination papers.
- `id` (UUID, PK)
- `tenant_id` (UUID, FK -> `tenants.id`, indexed)
- `assessment_id` (UUID, FK -> `assessments.id`, indexed)
- `course_offering_id` (UUID, FK -> `course_offerings.id`, indexed)
- `exam_term_id` (UUID, FK -> `exam_terms.id`, nullable)
- `exam_date` (DATE)
- `start_time` / `end_time` (VARCHAR / TIME)
- `room_identifier` (VARCHAR)
- `invigilator_faculty_id` (UUID, FK -> `faculty.id`, nullable)
- `status` (VARCHAR: `SCHEDULED`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`, `RESCHEDULED`)

### `exam_eligibilities`
Captures historical eligibility evaluation at a point in time based on Step 6 attendance.
- `id` (UUID, PK)
- `tenant_id` (UUID, FK -> `tenants.id`, indexed)
- `exam_term_id` (UUID, FK -> `exam_terms.id`, indexed)
- `course_offering_id` (UUID, FK -> `course_offerings.id`, indexed)
- `student_id` (UUID, FK -> `students.id`, indexed)
- `eligibility_status` (VARCHAR: `ELIGIBLE`, `ATTENDANCE_SHORTAGE`, `CONDONATION_ALLOWED`, `DISBARRED`)
- `attendance_percentage` (NUMERIC)
- `is_overridden` (BOOLEAN)
- `evaluated_at` (TIMESTAMP)

### `student_assessment_marks`
Student scores for a given assessment component.
- `id` (UUID, PK)
- `tenant_id` (UUID, FK -> `tenants.id`, indexed)
- `assessment_id` (UUID, FK -> `assessments.id`, indexed)
- `student_id` (UUID, FK -> `students.id`, indexed)
- `marks_obtained` (NUMERIC, nullable)
- `status` (VARCHAR: `PRESENT`, `ABSENT`, `NOT_ATTEMPTED`, `WITHHELD`, `MALPRACTICE`)
- `is_absent` (BOOLEAN)
- `is_finalized` (BOOLEAN)
- `finalized_at` (TIMESTAMP)
- Unique constraint: `(assessment_id, student_id)`

### `mark_correction_requests`
Supervised adjustment ledger for locked marks.
- `id` (UUID, PK)
- `tenant_id` (UUID, FK -> `tenants.id`, indexed)
- `mark_id` (UUID, FK -> `student_assessment_marks.id`, indexed)
- `old_marks` / `new_marks` (NUMERIC)
- `old_status` / `new_status` (VARCHAR)
- `reason` (TEXT)
- `requested_by_user_id` (UUID, FK -> `users.id`)
- `approved_by_user_id` (UUID, FK -> `users.id`, nullable)
- `approval_status` (VARCHAR: `PENDING`, `APPROVED`, `REJECTED`)
- `approval_notes` (TEXT)

### `semester_exam_results`
Calculated course outcome for a student.
- `id` (UUID, PK)
- `tenant_id` (UUID, FK -> `tenants.id`, indexed)
- `student_id` (UUID, FK -> `students.id`, indexed)
- `course_offering_id` (UUID, FK -> `course_offerings.id`, indexed)
- `exam_term_id` (UUID, FK -> `exam_terms.id`, indexed)
- `internal_marks` (NUMERIC)
- `external_marks` (NUMERIC)
- `total_marks` (NUMERIC)
- `grade_letter` (VARCHAR)
- `grade_point` (NUMERIC)
- `credits_earned` (NUMERIC)
- `result_status` (VARCHAR: `PASS`, `FAIL`, `ABSENT`, `WITHHELD`)
- `publication_status` (VARCHAR: `DRAFT`, `UNDER_REVIEW`, `FINALIZED`, `PUBLISHED`)
- Unique constraint: `(student_id, course_offering_id, exam_term_id)`
