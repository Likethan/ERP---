# Enterprise Student Success, Academic Advising, Early-Warning & Intervention Management Runbook

## Executive Summary

The **CampusOS Student Success, Academic Advising, Early-Warning & Intervention Management Engine** (Step 47) delivers a carrier-grade, multi-tenant student retention, academic advising, proactive risk detection, and collaborative intervention platform for modern higher education institutions.

Aligned with the CampusOS core philosophy — **“One Campus. One System. One Source of Truth.”** — this engine unites attendance, examination marks, advising caseloads, cross-functional interventions, appointment booking, and student self-service into an integrated, auditable ecosystem. It eliminates organizational silos between faculty mentors, academic deans, career counselors, and student welfare officers while maintaining absolute multi-tenant isolation, PBAC security, and a strict privacy boundary between internal advisor risk deliberations and student-facing dashboards.

---

## 1. Architecture & Core Governance Principles

### 1.1 The Ten Golden Rules of Student Success Governance
1. **Absolute Multi-Tenant Boundary Isolation**: Every student-success case, note, advisor profile, assignment, advising plan, rule, signal, intervention, and appointment is partitioned strictly by `tenant_id`. Cross-tenant data leakage is structurally impossible.
2. **Explainable Proactive Risk Signals**: Early-warning signals never trigger as opaque "black-box" scores. Every signal produces human-auditable evidence references containing observed metric percentages, threshold conditions, and direct references to underlying attendance sessions and examination marks.
3. **Signal Deduplication & Alert Storm Prevention**: The evaluation engine guarantees that a student cannot have duplicate active signals for the same rule within overlapping evaluation windows. Re-evaluating rules refreshes or acknowledges active signals rather than overwhelming advisors with repeated alerts.
4. **Advisor Caseload Capacity Limits**: Advisors cannot be assigned students beyond their configured maximum caseload capacity (`max_student_capacity`). System rejects over-allocation with descriptive errors, enforcing institutional workload policies.
5. **Human-in-the-Loop Intervention Workflows**: Early-warning signals do not autonomously trigger disciplinary or punitive outcomes. They require human advisor triage: acknowledgment, false-positive dismissal with justification, linking to structured support cases, or resolution upon student recovery.
6. **Strict Privacy Boundary & Role-Based Data Masking**: Students access a tailored, empowering self-service view. Internal case notes, sensitive psychological risk assessments, private meeting reflections, and administrative audit tags are strictly scrubbed before responses are returned to students.
7. **Cross-Disciplinary Intervention Action Tracking**: Interventions support multi-disciplinary actions (peer tutoring, remedial classes, mental health counseling, attendance check-ins) assigned to specific parties with enforceable due dates, milestone completion tracking, and outcome classifications.
8. **Double-Booking & Conflict-Free Appointment Scheduling**: Advising appointment booking validates real-time calendar availability for both advisor and student, preventing overlapping bookings across in-person and virtual modes.
9. **Full Auditability & Rule Versioning**: Modifications to early-warning rule thresholds (e.g., changing attendance threshold from 75% to 80%) create immutable version history (`EarlyWarningRuleVersion`) with change reasons, preserving historical compliance and auditability.
10. **Automated Background Lifecycle Sweeps**: Periodic background tasks run every 4 hours to sweep overdue advising actions, flag stalled interventions, evaluate scheduled rule sets, and refresh aggregate retention statistics.

---

## 2. System Workflow Architecture

```
                                  CAMPUS DATA INGESTION
                               (Attendance & Examinations)
                                            |
                                            v
                         +--------------------------------------+
                         |    EARLY-WARNING RULES ENGINE        |
                         |  - Versioned Institutional Thresholds|
                         |  - Attendance & Assessment Windows   |
                         +------------------+-------------------+
                                            |
                                            v
                         +--------------------------------------+
                         |     SIGNAL DEDUPLICATION ENGINE      |
                         |  - Check Existing Open Signals       |
                         |  - Generate Explainable Metric JSON  |
                         +------------------+-------------------+
                                            |
                                            v
                         +--------------------------------------+
                         |       ADVISOR TRIAGE & REVIEW        |
                         |  - Acknowledge Signal                |
                         |  - Dismiss False Positive            |
                         |  - Link to Existing / New Case       |
                         +------------------+-------------------+
                                            |
                      +---------------------+---------------------+
                      |                                           |
                      v                                           v
       +-----------------------------+             +-----------------------------+
       |   STUDENT-SUCCESS CASES     |             |      ACADEMIC ADVISING      |
       |  - Multi-Category Support   |             |  - Faculty / Peer Mentors   |
       |  - Escalation & Reassignment|             |  - Caseload Capacity Guard  |
       |  - Confidential Staff Notes |             |  - Academic Roadmaps        |
       +--------------+--------------+             +--------------+--------------+
                      |                                           |
                      +---------------------+---------------------+
                                            |
                                            v
                         +--------------------------------------+
                         |   INTERVENTIONS & ACTION TRACKING    |
                         |  - Remedial Tutoring / Counseling    |
                         |  - Milestone Action Items            |
                         |  - Overdue Sweeps & Outcome Reports  |
                         +------------------+-------------------+
                                            |
                      +---------------------+---------------------+
                      |                                           |
                      v                                           v
       +-----------------------------+             +-----------------------------+
       |   STUDENT SELF-SERVICE      |             |   OPERATIONAL ANALYTICS     |
       |  - Masked Roadmap Actions   |             |  - Retention Risk Caseloads |
       |  - Progress Feedback Notes  |             |  - Advisor Workload Metrics |
       |  - Appointment Bookings     |             |  - Intervention Efficacy    |
       +-----------------------------+             +-----------------------------+
```

---

## 3. Core Domain Entities & Database Schema

The module introduces 13 interconnected entities in `apps/api/app/models/student_success.py`, migrated under revision `032_enterprise_student_success_advising_early_warning`:

| Entity Name | Database Table | Description & Responsibilities |
| :--- | :--- | :--- |
| `StudentSuccessCase` | `student_success_cases` | Central coordinating case file tracking student support, priority, status lifecycle, reassignment, and outcome. |
| `StudentSuccessCaseNote` | `student_success_case_notes` | Chronological case notes, classified by type (e.g., ADVISOR_MEETING, INTERVENTION_UPDATE) with confidential staff flag. |
| `AdvisorProfile` | `student_success_advisors` | Professional advisor profile linked to `User` and `Department`, managing category and maximum student capacity. |
| `AdvisorStudentAssignment` | `student_success_advisor_assignments` | Formal advisor-student pairing with start/end dates, relationship types (PRIMARY, ACADEMIC_MENTOR, CAREER_COUNSELOR). |
| `AdvisingPlan` | `student_success_advising_plans` | Multi-semester academic success roadmaps specifying target GPA, credit milestones, and review cadences. |
| `AdvisingActionItem` | `student_success_advising_actions` | Actionable checklist milestones with responsible parties (STUDENT, ADVISOR, FACULTY, PARENT) and due dates. |
| `EarlyWarningRule` | `student_success_warning_rules` | Configurable institutional risk rules (ATTENDANCE, ASSESSMENT_MARKS, CGPA, INACTIVITY) with operators and thresholds. |
| `EarlyWarningRuleVersion` | `student_success_warning_rule_versions` | Immutable audit version history tracking changes to rule thresholds, operators, and severities. |
| `EarlyWarningEvaluation` | `student_success_warning_evaluations` | Execution audit log capturing batch/ad-hoc evaluations, execution duration, and student counts. |
| `EarlyWarningSignal` | `student_success_warning_signals` | Explainable risk alerts containing observed values, threshold conditions, and source record references. |
| `InterventionPlan` | `student_success_interventions` | Multi-disciplinary intervention programs (TUTORING, ATTENDANCE_FOLLOWUP, COUNSELING) with target completion dates. |
| `InterventionAction` | `student_success_intervention_actions` | Operational sub-tasks under an intervention with student visibility controls and completion tracking. |
| `AdvisingAppointment` | `student_success_appointments` | Scheduled 1-on-1 and group advising sessions with meeting modes, conflict checking, and post-session notes. |

---

## 4. Early-Warning Rules Engine & Explainable Evaluation

### 4.1 Supported Metric Categories
- **ATTENDANCE**: Calculates the student's attendance percentage across locked `AttendanceSession` records over an observation window (e.g., 30 days):
  $$\text{Attendance \%} = \frac{\text{Present + Excused + On Leave Sessions}}{\text{Total Conducted Sessions}} \times 100$$
- **ASSESSMENT_MARKS**: Computes average percentage on published internal or continuous assessments over an observation window:
  $$\text{Assessment \%} = \frac{\sum \text{Marks Obtained}}{\sum \text{Max Marks}} \times 100$$
- **CGPA**: Evaluates cumulative grade point averages against academic standing cutoffs.
- **INACTIVITY / COURSEWORK**: Evaluates submission gaps and prolonged portal absences.

### 4.2 Deduplication Engine Semantics
When an evaluation runs:
1. Active open signals for the same `(tenant_id, student_id, rule_id)` with status in `(NEWLY_DETECTED, ACKNOWLEDGED, UNDER_REVIEW, INTERVENTION_INITIATED)` are identified.
2. If an active signal already exists, the engine logs the evaluation without spawning a redundant alert signal.
3. If an existing signal was previously `RESOLVED` or `DISMISSED` and the student violates thresholds again in a new evaluation window, a new cycle signal is legitimately created.

---

## 5. Security, PBAC Permissions & Privacy Controls

### 5.1 RBAC / PBAC Permission Matrix

| Role | Permissions | Access Scope |
| :--- | :--- | :--- |
| **INSTITUTION_ADMIN** / **DEAN** | `STUDENT_SUCCESS_CASES_MANAGE`, `STUDENT_SUCCESS_ADVISORS_MANAGE`, `STUDENT_SUCCESS_RULES_MANAGE`, `STUDENT_SUCCESS_INTERVENTIONS_MANAGE`, `STUDENT_SUCCESS_APPOINTMENTS_MANAGE`, `STUDENT_SUCCESS_REPORTS_READ` | Full read/write/reassign across institution. |
| **ACADEMIC_ADVISOR** / **FACULTY** | `STUDENT_SUCCESS_CASES_READ`, `STUDENT_SUCCESS_CASES_MANAGE`, `STUDENT_SUCCESS_INTERVENTIONS_MANAGE`, `STUDENT_SUCCESS_APPOINTMENTS_MANAGE` | Caseload-assigned students, case note authoring, intervention execution. |
| **STUDENT** | `STUDENT_SUCCESS_SELF_READ` | Student self-service overview; public advising actions; appointment scheduling; progress submission. |

### 5.2 Privacy Data Boundary (Student Self-Service)
The endpoint `GET /student-success/self/overview` enforces strict role-based data projection:
- **Masked Content**: Internal advisor case notes, sensitive behavioral risk tags, non-student-visible intervention actions, and meeting notes marked confidential are omitted or set to `null`.
- **Allowed Content**: Assigned primary advisor contact details, active roadmap milestones marked `is_student_visible=True`, upcoming appointment dates, agendas, and mutually agreed action summaries.

---

## 6. REST API Reference

Base Path: `/api/v1/student-success`

### 6.1 Cases & Notes
- `POST /cases`: Create a new student-success case.
- `GET /cases`: List cases with tenant filtering (student, priority, status).
- `GET /cases/{case_id}`: Retrieve detailed case with chronological notes.
- `PATCH /cases/{case_id}`: Update case details or priority.
- `POST /cases/{case_id}/status`: Transition lifecycle state (OPEN, IN_PROGRESS, RESOLVED, CLOSED).
- `POST /cases/{case_id}/reassign`: Reassign case owner with mandatory audit reason.
- `POST /cases/{case_id}/notes`: Add chronological or confidential case notes.
- `POST /cases/{case_id}/escalate`: Escalate case priority to CRITICAL or URGENT.

### 6.2 Advisors & Caseload Assignments
- `POST /advisors`: Provision an advisor profile with capacity limits.
- `GET /advisors`: List active advisors by department or campus.
- `GET /advisors/{advisor_id}`: Get advisor caseload and contact details.
- `PATCH /advisors/{advisor_id}`: Update maximum capacity or availability.
- `POST /assignments`: Pair an advisor to a student (validates capacity).
- `POST /assignments/{assignment_id}/reassign`: Reassign student to a new advisor.
- `GET /assignments`: Query active and historical advisor-student pairings.

### 6.3 Advising Plans & Action Items
- `POST /plans`: Create a multi-semester advising plan with action items.
- `GET /plans/{plan_id}`: Retrieve advising roadmap and action progress.
- `POST /plans/{plan_id}/actions`: Append an action milestone.
- `PATCH /actions/{action_item_id}`: Update action progress, completion, or due date.

### 6.4 Early-Warning Rules & Signal Reviews
- `POST /rules`: Configure a new early-warning threshold rule.
- `GET /rules`: List configured rules with status filters.
- `PATCH /rules/{rule_id}`: Update rule thresholds (creates audited rule version).
- `POST /rules/evaluate`: Trigger batch or ad-hoc rule evaluation.
- `GET /signals`: List detected risk signals.
- `POST /signals/{signal_id}/acknowledge`: Acknowledge signal for review.
- `POST /signals/{signal_id}/dismiss`: Dismiss signal as false positive with rationale.
- `POST /signals/{signal_id}/link-case`: Link signal to an existing or newly created case.
- `POST /signals/{signal_id}/resolve`: Mark signal resolved following recovery.

### 6.5 Interventions & Appointments
- `POST /interventions`: Create a targeted intervention plan with execution actions.
- `GET /interventions/{intervention_id}`: Fetch intervention with sub-actions.
- `PATCH /interventions/{intervention_id}`: Update outcomes, participation, and completion.
- `POST /appointments`: Schedule an appointment (validates time conflicts).
- `GET /appointments`: List scheduled appointments.
- `PATCH /appointments/{appointment_id}`: Record post-meeting notes and agreed actions.

### 6.6 Student Self-Service & Analytics
- `GET /self/overview`: Privacy-scrubbed portal for currently authenticated student.
- `POST /self/progress`: Student updates progress on visible assigned action items.
- `GET /reports/analytics`: Comprehensive aggregate retention and caseload metrics.

---

## 7. Background Scheduler Operations

The scheduler module (`apps/api/app/scheduler.py`) runs periodic maintenance sweeps:

```python
async def sweep_student_success_task():
    """Runs periodic checks for overdue advising actions and flagged interventions."""
    ...
```

- **Cadence**: Every 4 hours (offset 240 seconds).
- **Sweep Actions**:
  1. Identifies overdue advising action items and intervention tasks past their `due_date`.
  2. Transitions overdue pending items to escalated triage states.
  3. Records audit log events for operational oversight.

---

## 8. Verification & Test Suite

The test suite in `apps/api/tests/test_enterprise_student_success.py` executes 9 automated test scenarios covering the full lifecycle:

```bash
# Execute test suite
cd apps/api
.\.venv\Scripts\pytest.exe tests/test_enterprise_student_success.py --show-capture=no
```

**Test Results Summary**:
- `test_case_management_lifecycle`: PASSED (Case creation, status changes, notes, reassignment, reopen, escalation)
- `test_advisor_profiles_and_caseload_capacity`: PASSED (Advisor limits, over-capacity rejection, caseload rebalancing)
- `test_advising_plans_and_action_items`: PASSED (Academic roadmaps, action milestones, completion dates)
- `test_early_warning_evaluation_and_deduplication`: PASSED (Realistic 60% attendance against 75% threshold, explainable signal generation, deduplication)
- `test_signal_lifecycle_and_intervention_workflow`: PASSED (Acknowledge, dismiss, link to case, intervention plan execution, resolve)
- `test_advising_appointments_and_conflict_prevention`: PASSED (Booking, overlapping appointment 409 conflict, non-overlapping booking)
- `test_student_self_service_privacy_boundary`: PASSED (Internal notes masking, student-visible actions filtering, student progress submission)
- `test_multi_tenant_isolation`: PASSED (Cross-tenant case read and update rejection)
- `test_aggregate_student_success_analytics_and_caseload`: PASSED (Operational caseload distribution and signal breakdown analytics)

**Total**: 9 passed (100% pass rate).
