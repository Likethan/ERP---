# Examination & Assessment API Endpoints

All endpoints are prefixed with `/api/v1/examinations`.

## 1. Grade Scales
- `GET /api/v1/examinations/grade-scales` — List tenant grade scales. Requires `examinations:read`.
- `POST /api/v1/examinations/grade-scales` — Create custom grade scale. Requires `examinations:create`.

## 2. Exam Terms
- `GET /api/v1/examinations/terms` — List terms. Requires `examinations:read`.
- `POST /api/v1/examinations/terms` — Create exam term. Requires `examinations:create`.

## 3. Assessments
- `GET /api/v1/examinations/assessments` — List assessments with optional `course_offering_id`, `status`. Requires `assessments:read`.
- `GET /api/v1/examinations/assessments/{id}` — Get single assessment component. Requires `assessments:read`.
- `POST /api/v1/examinations/assessments` — Create assessment component (validates cumulative weightage <= 100%). Requires `assessments:create`.
- `GET /api/v1/examinations/assessments/structure/{course_offering_id}` — Get composite assessment breakdown and weightage sum. Requires `assessments:read`.
- `POST /api/v1/examinations/assessments/{id}/finalize` — Finalize assessment and lock marks. Requires `assessments:finalize`.

## 4. Exam Schedules & Conflict Detection
- `GET /api/v1/examinations/schedules` — List schedules. Requires `examinations:read`.
- `POST /api/v1/examinations/schedules` — Create schedule (enforces room & student conflict detection). Requires `examinations:create`.
- `PATCH /api/v1/examinations/schedules/{id}` — Update schedule. Requires `examinations:update`.
- `POST /api/v1/examinations/schedules/check-conflicts` — Dry-run conflict detection API. Requires `examinations:read`.

## 5. Exam Eligibility
- `POST /api/v1/examinations/course-offerings/{id}/evaluate-eligibility` — Generate eligibility snapshot from Attendance Engine. Requires `examinations:read`.
- `GET /api/v1/examinations/course-offerings/{id}/eligibility` — Get student eligibility list for course. Requires `examinations:read`.
- `POST /api/v1/examinations/eligibility/{id}/override` — Supervised administrative override of attendance eligibility. Requires `examinations:update`.

## 6. Marks Roster & Supervised Corrections
- `GET /api/v1/examinations/assessments/{id}/marks` — Get class roster marks. Requires `marks:read`.
- `POST /api/v1/examinations/assessments/{id}/marks/bulk` — Atomic class roster marks entry (Draft or Final). Requires `marks:enter`.
- `POST /api/v1/examinations/marks/{id}/correction` — Request audited correction on locked mark. Requires `marks:correct`.
- `GET /api/v1/examinations/marks/corrections` — List pending corrections. Requires `marks:read`.
- `POST /api/v1/examinations/marks/corrections/{id}/approve` — Approve correction and update mark. Requires `marks:finalize`.

## 7. Results & Publication
- `POST /api/v1/examinations/results/calculate-course/{course_offering_id}` — Calculate student results using configured grade scale. Requires `results:finalize`.
- `GET /api/v1/examinations/results` — List results (enforces student privacy gating). Requires `results:read`.
- `GET /api/v1/examinations/results/{id}` — Get single result. Requires `results:read`.
- `POST /api/v1/examinations/results/{id}/finalize` — Finalize result. Requires `results:finalize`.
- `POST /api/v1/examinations/results/publish-course/{course_offering_id}` — Publish course results to students. Requires `results:publish`.
- `GET /api/v1/examinations/transcripts/student/{student_id}/term/{exam_term_id}` — Official semester GPA transcript. Requires `results:read`.
- `GET /api/v1/examinations/dashboard` — Operational KPI telemetry. Requires `examinations:read`.
