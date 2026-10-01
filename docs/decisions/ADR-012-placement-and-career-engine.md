# ADR-012: Placement & Career Engine, Deterministic Automated Eligibility, and Offer Lifecycle

## Status
Accepted

## Context
Higher education institutions face significant challenges managing campus recruitment campaigns:
1. **Manual Eligibility Verification**: Placement cells historically spend weeks reconciling spreadsheets against examination records, attendance thresholds, backlog registries, and fee payment statuses. This error-prone process leads to ineligible student placement, disqualifications from corporate recruiters, and student grievances.
2. **Multiple Round Coordination**: Recruitment drives encompass multiple sequential evaluation stages (Aptitude, Coding, Technical Interviews, HR), each requiring scheduling, interviewer assignment, scoring, and candidate promotion.
3. **Offer Clashing & Dream Offer Policies**: Without systematic offer tracking and placement status updating, students hold multiple offers simultaneously, denying opportunities to unplaced peers. Institutions enforce strict tier-based policies (e.g., standard vs. dream vs. super-dream offers).
4. **Institutional Outcome Auditing**: Accreditation bodies (NAAC, NIRF, NBA) mandate tamper-evident documentation of corporate recruitment, including offer letters, CTC distributions, department placement percentages, and gender/cohort equity metrics.

## Decision
We engineered the CampusOS Career & Placements Engine as a first-class domain subsystem within the modular monolith.

```text
Corporate Partner (Tier: DREAM / TIER_1 / MASS)
       ↓
Recruitment Drive (On-Campus / Virtual / Hybrid)
       ↓
Job Position (CTC, Vacancies, Skill Tags)
       ↓
Deterministic Eligibility Rules (CGPA, Backlogs, Attendance, Fee Clearance)
       ↓
Automated Eligibility Snapshot (JSON Audit Trail)
       ↓
Placement Application (APP-YYYY-XXXXXX)
       ↓
Interview Rounds & Schedules (Evaluations & Recommendations)
       ↓
Placement Offer (OFF-YYYY-XXXXXX)
       ↓
Offer Decision (ACCEPT / DECLINE) → Student Status to PLACED → PlacementOutcome
```

### 1. Corporate Directory & Role Management
- Companies are registered with tier categories (`DREAM`, `SUPER_DREAM`, `TIER_1`, `TIER_2`, `MASS`), industry classification, website, and multi-contact rosters.
- Recruitment drives belong to an academic year, have strict opening and closing timestamps, and host multiple job positions with designated CTC and vacancy limits.

### 2. Deterministic Eligibility Evaluation Engine
- Eligibility is evaluated deterministically by the authoritative backend engine (`PlacementService.evaluate_student_eligibility`).
- The evaluation engine runs across standard and extensible rule types:
  - `CGPA_MINIMUM` / `CGPA_MAXIMUM`: Evaluated against canonical published semester exam records (`SemesterExamResult`).
  - `BACKLOG_NONE` / `BACKLOG_MAXIMUM`: Computes active failed course offerings.
  - `ATTENDANCE_MINIMUM`: Calculates overall attendance percentage across attendance sessions.
  - `FEE_CLEARANCE`: Verifies absence of overdue unpaid tuition invoices.
  - `PROGRAM_ALLOWED` / `PROGRAM_EXCLUDED`: Validates student enrolled degree program.
  - `GRADUATION_YEAR`: Compares student expected passing batch against drive parameters.
- Each evaluation produces an immutable `PlacementEligibilitySnapshot` containing rule-by-rule results (`expected`, `actual`, `passed`) and the source data snapshot.

### 3. Application Lifecycle & Strict Concurrency
- Students can apply only during active application windows (`APPLICATIONS_OPEN` status and within `application_open_at` to `application_close_at`).
- An application is rejected if `is_eligible` evaluates to `False`.
- Duplicate applications for the same job position are prevented via unique database constraints (`uq_placement_app_position_student`).
- Applications track chronological status transitions (`APPLIED` → `SHORTLISTED` → `INTERVIEWING` → `SELECTED` → `OFFERED` → `ACCEPTED`).

### 4. Interview Scheduling & Multistage Scoring
- Each job position configures sequential interview rounds (`APTITUDE`, `TECHNICAL`, `CODING`, `HR`, `FINAL`).
- Candidates receive specific interview schedules with timestamps, durations, and physical/virtual locations.
- Interviewers record quantitative scores, qualitative feedback, and hiring recommendations (`STRONG_HIRE`, `HIRE`, `NO_HIRE`).

### 5. Official Offer Issuance & Student Status Transition
- Placement officers issue formal offers linked to applications, with explicit offer expiry deadlines.
- When a student accepts an offer:
  1. The offer status transitions to `ACCEPTED`.
  2. Any competing pending offers or open applications are flagged or reconciled per institutional policy.
  3. The student's placement profile availability is set to `PLACED`.
  4. An authoritative `PlacementOutcome` record is minted for accreditation auditing.

### 6. Institutional Career Analytics
- The engine aggregates real-time placement stats: placement percentage, average/median/highest CTC, tier distribution, department-wise placement velocities, and top recruiter leaderboards.

## Consequences
- **Positive**: Eliminates manual eligibility errors, prevents favoritism or unqualified student applications, ensures verifiable accreditation audits, and provides modern dashboard workflows for both students and placement officers.
- **Trade-offs**: Cross-domain queries (exam results, attendance, fee balances) require indexed lookups or database views. Handled via optimized targeted queries within the domain boundary.
