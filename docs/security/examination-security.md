# Examination Security, Tenant Isolation & Privacy

## 1. Multi-Tenancy Isolation
Every examination entity contains `tenant_id`:
- `grade_scales`, `exam_terms`, `assessments`, `exam_schedules`, `exam_eligibilities`, `student_assessment_marks`, `mark_correction_requests`, and `semester_exam_results`.
- Every SQL query and ORM filter explicitly restricts results to `tenant_id == current_user.tenant_id`.
- Cross-tenant access attempts immediately fail with HTTP 404 (or HTTP 403 where applicable), preventing information leakage.

## 2. Student Privacy & Unpublished Result Shielding
Academic evaluation results are strictly confidential until officially released:
- In `GET /api/v1/examinations/results`, if the requesting user holds the `STUDENT` role, the backend automatically enforces `publication_status == "PUBLISHED"`. Draft, finalized, or reviewed results are invisible.
- In `GET /api/v1/examinations/transcripts/...`, students can only query their own transcript (`target_student.user_id == current_user.id`). Any attempt to access another student's transcript raises HTTP 403 Forbidden.
- Transcripts reject generation unless results for the term have been published (`publication_status == "PUBLISHED"`).

## 3. Immutability & Supervised Correction Governance
- Once an assessment is finalized (`is_finalized = true`), direct marks mutation via `POST /assessments/{id}/marks/bulk` is rejected with `ValidationException` (`HTTP 422: Cannot enter or modify marks for a finalized assessment`).
- All changes must flow through `MarkCorrectionRequest`, which records requester, old mark, new mark, justification, approval notes, and reviewer ID.
- Approvals emit high-priority audit log events (`MARK_CORRECTION_APPROVED`, `ASSESSMENT_FINALIZED`, `RESULT_PUBLISHED`).

## 4. Permission Matrix
| Role | Examinations | Assessments | Marks Entry | Corrections | Finalization | Results | Publication |
|---|---|---|---|---|---|---|---|
| Institution Admin | Read, Create, Update | Full Control | Full Control | Approve | Full Control | Full Control | Full Control |
| Academic Admin | Read, Create, Update | Full Control | Full Control | Approve | Full Control | Full Control | Full Control |
| HOD | Read, Create | Full Control | Enter, Update | Approve | Finalize | Read, Finalize | Publish |
| Faculty | Read | Read, Create | Enter, Update | Request | Read | Read | - |
| Student | Read Schedules | - | - | - | - | Read (Published Only) | - |
