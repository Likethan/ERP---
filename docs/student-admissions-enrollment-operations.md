# Enterprise Student Admissions, Enrollment & Onboarding Orchestration Runbook

## Executive Summary

The **CampusOS Student Admissions, Enrollment & Onboarding Orchestration Engine** (Step 48) delivers a high-capacity, multi-tenant admissions and enrollment management platform for modern collegiate institutions and universities.

Aligned with the CampusOS core doctrine — **“One Campus. One System. One Source of Truth.”** — this module unifies applicant registration, program preferences, multi-tier document verification, versioned academic eligibility evaluations, quota-governed merit ranking and seat allocations, binding offer management with over-allocation guards, idempotent enrollment orchestration to canonical student profiles, and institutional post-enrollment onboarding checklists into a single, cohesive, end-to-end operational backbone.

---

## 1. Architecture & Core Governance Principles

### 1.1 The Ten Golden Rules of Admissions & Enrollment Governance
1. **Absolute Multi-Tenant Boundary Isolation**: Every admissions cycle, applicant profile, application, program preference, document upload, review, eligibility rule, seat allocation, selection run, offer, enrollment workflow, and onboarding task is partitioned strictly by `tenant_id`. Cross-tenant data visibility or manipulation is architecturally prohibited.
2. **Duplicate Applicant Prevention & Intelligent Merging**: Incoming applicants undergo automatic fuzzy and exact deduplication against phone number and national identity numbers (`national_id_number`). Duplicate candidate submissions are detected and support automated or administrator-reviewed merging preserving application histories.
3. **Application Lifecycle & Controlled Correction Windows**: After formal submission, applications become immutable against unauthorized applicant tampering. Institutions can grant time-limited, audited correction windows (e.g. 48 hours) for legitimate applicant corrections or document updates before evaluation.
4. **Multi-Stage Document Verification Workflow**: Admissions verification supports independent reviewers verifying individual document requirements (e.g. 10th marksheet, 12th certificate, transfer certificates, category affidavits) with verification timestamps, reviewer identity, and structured rejection reasons.
5. **Explainable Versioned Eligibility Rules**: Eligibility rules (minimum aggregate percentage, qualifying exam scores, mandatory subjects) are versioned. Automated evaluation runs store exact observed percentages, pass/fail status, and criteria traces ensuring total auditability and transparency.
6. **Quota & Category-Governed Seat Allocation Runs**: Selection runs evaluate eligible applicants ranked by qualifying merit percentages across categories (GENERAL, OBC, SC, ST, EWS, MANAGEMENT, SPORTS, NRI). Over-allocation is strictly prohibited via real-time capacity guards.
7. **Time-Limited Admission Offers & Seat Reservation**: Admission offers feature enforceable expiry deadlines. While an offer is pending acceptance (`ISSUED`), the associated seat is reserved. If the candidate declines or the offer expires, the seat is automatically released back to the unallocated pool.
8. **Idempotent Enrollment Orchestration to Canonical Records**: When an applicant accepts an offer and completes initial fee payment, enrollment orchestration idempotently creates the canonical `User` account, `StudentProfile`, roll number, and `STUDENT` role binding. Subsequent trigger attempts return the existing enrolled record without duplicate student creation.
9. **Post-Enrollment Institutional Onboarding Checklists**: Upon successful enrollment, an institutional onboarding checklist is spawned containing configurable tasks across IT account activation, document physical verification, hostel allotment, library membership, and orientation attendance.
10. **Full Audit Logging & Comprehensive Analytics**: All cycle status changes, applicant merges, application submissions, reviewer decisions, selection publications, offer responses, and enrollment completions are recorded to the system audit trail (`AuditEventCategory.ADMISSIONS_*`), powering real-time admission funnel analytics.

---

## 2. System Workflow Architecture

```
                                  APPLICANT REGISTRATION
                              (Duplicate Check: Phone / ID)
                                            |
                                            v
                                 APPLICATION SUBMISSION
                             (Program Choices & Documents)
                                            |
                                            v
                                 DOCUMENT VERIFICATION
                           (Reviewer Approvals / Rejections)
                                            |
                                            v
                              AUTOMATED ELIGIBILITY ENGINE
                            (Versioned Rule Score Evaluation)
                                            |
                                            v
                               SEAT ALLOCATION & SELECTION
                            (Merit Ranking by Quota / Category)
                                            |
                                            v
                                  OFFER ISSUANCE & EXPIRY
                              (Seat Capacity Reservation)
                                            |
                                 +----------+----------+
                                 |                     |
                                 v                     v
                             ACCEPTED               DECLINED / EXPIRED
                                 |                     |
                                 v                     v
                       ENROLLMENT ORCHESTRATION    (Seat Released)
                     (Creates User & StudentProfile)
                                 |
                                 v
                        ONBOARDING CHECKLIST
                     (IT, Hostel, Library Tasks)
```

---

## 3. Core Database Entities

| Entity Model | Table Name | Purpose & Lifecycle Description |
|:---|:---|:---|
| `AdmissionCycle` | `admissions_cycles` | Academic admission cycles (DRAFT -> OPEN -> CLOSED -> ARCHIVED) with application, document, and offer deadlines. |
| `ApplicantProfile` | `admissions_applicants` | Prospective candidate identity with verified email/phone, duplicate tracking, and merge linkage. |
| `AdmissionApplication` | `admissions_applications` | Formal candidate application tracking status (DRAFT -> SUBMITTED -> UNDER_REVIEW -> SHORTLISTED -> OFFERED -> ENROLLED -> WITHDRAWN / REJECTED). |
| `ApplicationProgramChoice` | `admissions_program_choices` | Ranked program preference order (1, 2, 3...) per candidate application. |
| `ApplicationDocumentRequirement` | `admissions_document_requirements` | Configurable mandatory or optional document types required per cycle/program. |
| `ApplicationDocument` | `admissions_documents` | Uploaded document verification record (PENDING -> VERIFIED -> REJECTED). |
| `AdmissionEligibilityRule` | `admissions_eligibility_rules` | Versioned rule definition specifying cutoffs, qualifying exams, and scoring thresholds. |
| `EligibilityEvaluation` | `admissions_eligibility_evaluations` | Explainable result of rule evaluation with observed scores and decision trace. |
| `ApplicationReview` | `admissions_reviews` | Faculty / admissions committee member evaluations, scores, and recommendations. |
| `SeatAllocation` | `admissions_seat_allocations` | Category-wise sanctioned, reserved, allocated, and remaining seat capacities per program. |
| `SelectionRun` | `admissions_selection_runs` | Executed merit list generation and ranking runs (DRAFT -> PUBLISHED -> ARCHIVED). |
| `SelectionResult` | `admissions_selection_results` | Individual candidate ranking rank, merit score, allocated choice, and selection status. |
| `AdmissionOffer` | `admissions_offers` | Formal offer letter issuance, fee requirements, expiry date, and candidate response tracking. |
| `EnrollmentWorkflow` | `admissions_enrollment_workflows` | Idempotent student matriculation workflow bridging application to canonical student profile. |
| `OnboardingChecklist` | `admissions_onboarding_checklists` | Master institutional onboarding checklist per enrolled candidate. |
| `OnboardingTask` | `admissions_onboarding_tasks` | Individual tasks across academic, administrative, IT, library, and facilities departments. |

---

## 4. API Endpoints Reference

All endpoints are hosted under `/api/v1/admissions` and require tenant authentication and role-based permissions (`admissions:*`).

### 4.1 Admission Cycles
- `POST /api/v1/admissions/cycles` — Create a new admissions cycle.
- `GET /api/v1/admissions/cycles` — List cycles with status and academic year filtering.
- `GET /api/v1/admissions/cycles/{cycle_id}` — Get cycle details by ID.
- `PATCH /api/v1/admissions/cycles/{cycle_id}` — Update cycle settings and deadlines.
- `POST /api/v1/admissions/cycles/{cycle_id}/transition` — Transition cycle lifecycle status.

### 4.2 Applicant Profiles & Applications
- `POST /api/v1/admissions/applicants` — Register candidate profile with duplicate detection.
- `POST /api/v1/admissions/applicants/merge` — Merge duplicate applicant profiles.
- `POST /api/v1/admissions/applications` — Create candidate application with program choices.
- `GET /api/v1/admissions/applications` — List applications with cycle, program, and status filters.
- `GET /api/v1/admissions/applications/{application_id}` — Get complete application dossier.
- `PATCH /api/v1/admissions/applications/{application_id}` — Update draft or open-window application.
- `POST /api/v1/admissions/applications/{application_id}/submit` — Formally submit application.
- `POST /api/v1/admissions/applications/{application_id}/withdraw` — Candidate withdraws application.
- `POST /api/v1/admissions/applications/{application_id}/reopen` — Grant time-limited correction window.

### 4.3 Document Requirements & Verification
- `POST /api/v1/admissions/document-requirements` — Define document requirement rules.
- `GET /api/v1/admissions/document-requirements` — List requirements for cycle/program.
- `POST /api/v1/admissions/applications/{application_id}/documents` — Upload application document.
- `PATCH /api/v1/admissions/documents/{document_id}/verify` — Verify or reject uploaded document.

### 4.4 Eligibility & Reviewer Evaluations
- `POST /api/v1/admissions/eligibility-rules` — Create versioned eligibility rule.
- `GET /api/v1/admissions/eligibility-rules` — List eligibility rules.
- `POST /api/v1/admissions/applications/{application_id}/evaluate-eligibility` — Run rule evaluation.
- `POST /api/v1/admissions/applications/{application_id}/reviews` — Submit committee review score.

### 4.5 Seat Allocations & Selection Runs
- `POST /api/v1/admissions/seat-allocations` — Configure quota seat matrix for program.
- `GET /api/v1/admissions/seat-allocations` — View seat allocation status and capacity.
- `POST /api/v1/admissions/selection-runs` — Execute merit-ranking selection run.
- `GET /api/v1/admissions/selection-runs/{run_id}` — View selection run and ranked list.
- `POST /api/v1/admissions/selection-runs/{run_id}/publish` — Publish selection results.

### 4.6 Offers, Enrollment & Onboarding
- `POST /api/v1/admissions/offers` — Issue admission offer with reserved seat guard.
- `POST /api/v1/admissions/offers/{offer_id}/respond` — Accept or decline issued offer.
- `POST /api/v1/admissions/enrollments` — Orchestrate idempotent canonical student enrollment.
- `GET /api/v1/admissions/onboarding/{checklist_id}` — Retrieve student onboarding checklist.
- `PATCH /api/v1/admissions/onboarding/tasks/{task_id}` — Update task status and verification.
- `GET /api/v1/admissions/analytics/funnel` — Get cycle admission funnel analytics.

---

## 5. Security & Multi-Tenancy Assurance

1. **PBAC Verification**: Access to cycle management, review scoring, selection publishing, and enrollment orchestration requires specific permissions (`admissions:manage_cycles`, `admissions:review_applications`, `admissions:run_selection`, `admissions:orchestrate_enrollment`).
2. **Applicant Scoping**: Candidates only access their personal applications, offers, and onboarding checklists.
3. **Tenant Boundary Guarantee**: Every database query includes `tenant_id == ctx.tenant_id`. Cross-tenant record references raise immediate `404 Not Found` exceptions.
4. **Idempotent Operations**: Repeated execution of selection runs or enrollment orchestrations safely yields stable state transitions without corrupting capacities or spawning orphaned student records.
