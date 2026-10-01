# Placement & Career Engine Architecture

The **Career & Placements Engine** in CampusOS is a domain subsystem engineered within the modular monolith architecture. It streamlines institutional campus recruitment campaigns by eliminating manual eligibility verification, synchronizing interview rounds, ensuring multi-tenant data isolation, and generating audit-ready accreditation reports.

---

## 1. Domain Component Overview

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        CampusOS Placement Domain                       │
├────────────────────────────────┬───────────────────────────────────────┤
│ Corporate Directory            │ Recruitment Drives & Job Roles        │
│ • Company Profiles & Tiers     │ • On-Campus, Virtual, Hybrid Drives   │
│ • Tier: DREAM, SUPER_DREAM,    │ • CTC, Vacancy, Skills & Job Specs    │
│   TIER_1, TIER_2, MASS         │ • Academic Year Scoping               │
│ • Corporate Contacts Directory │ • Sequential Drive Code Numbering     │
├────────────────────────────────┼───────────────────────────────────────┤
│ Deterministic Eligibility      │ Application & Interview Lifecycle     │
│ • Minimum & Maximum CGPA       │ • One-Click Verified Applications     │
│ • Backlog Auditing (Active=0)  │ • Strict Concurrency (No Duplicates)  │
│ • Attendance % Thresholds      │ • Multistage Interview Rounds         │
│ • Fee Balance Clearance Check  │ • Structured Interview Scoring        │
│ • JSON Audit Snapshot Minting  │ • Official Offer Issuance & Decision  │
└────────────────────────────────┴───────────────────────────────────────┘
```

---

## 2. Core Entities and Database Schema

### 2.1 Companies (`placement_companies`)
- **`id`**: UUID primary key.
- **`tenant_id`**: Strict institutional boundary.
- **`name`**, **`legal_name`**, **`industry`**, **`company_type`** (`PRODUCT`, `SERVICE`, `STARTUP`, `MNC`, `PSU`, `GOVT`).
- **`tier`**: Classification string (`DREAM`, `SUPER_DREAM`, `TIER_1`, `TIER_2`, `MASS`).
- **`website`**, **`headquarters_location`**, **`description`**, **`status`**.

### 2.2 Recruitment Drives (`placement_job_drives`)
- **`drive_code`**: Human-readable sequential code (`DRV-YYYY-XXXXXX`).
- **`company_id`**: Foreign key to `placement_companies`.
- **`academic_year_id`**: Scoped academic term.
- **`application_open_at`** & **`application_close_at`**: Timestamps defining active application windows.
- **`drive_date`**: Calendar date of event.
- **`mode`**: `ON_CAMPUS`, `OFF_CAMPUS`, `VIRTUAL`, `HYBRID`.
- **`status`**: `DRAFT`, `PUBLISHED`, `APPLICATIONS_OPEN`, `APPLICATIONS_CLOSED`, `SHORTLISTING`, `INTERVIEWING`, `OFFERS`, `CLOSED`, `CANCELLED`.

### 2.3 Job Positions (`placement_job_positions`)
- **`job_drive_id`**: Foreign key to `placement_job_drives`.
- **`title`**, **`employment_type`**, **`work_location`**, **`vacancy_count`**.
- **`ctc`**: Decimal representation of annual compensation.
- **`skills_json`**: Tagged competencies.

### 2.4 Eligibility Rules (`placement_eligibility_rules`)
- **`job_position_id`**: Foreign key to `placement_job_positions`.
- **`rule_type`**: Evaluated rule identifier (`CGPA_MINIMUM`, `BACKLOG_NONE`, `ATTENDANCE_MINIMUM`, `FEE_CLEARANCE`, `PROGRAM_ALLOWED`).
- **`operator`**: Comparison operator (`GTE`, `LTE`, `EQ`, `IN`, `NOT_IN`).
- **`value_json`**: Target comparison value.
- **`is_required`**: Boolean flag indicating mandatory gate.

### 2.5 Eligibility Snapshots (`placement_eligibility_snapshots`)
- Stores immutable JSON audit trails of evaluations (`rule_results_json`, `source_data_snapshot_json`).
- Prevents tampering or post-facto claims regarding student eligibility.

### 2.6 Applications (`placement_applications`)
- **`application_number`**: `APP-YYYY-XXXXXX`.
- **`student_id`** & **`job_position_id`**: Unique composite constraint.
- **`status`**: `APPLIED`, `SHORTLISTED`, `IN_REVIEW`, `REJECTED`, `WITHDRAWN`, `INTERVIEWING`, `SELECTED`, `OFFERED`, `ACCEPTED`, `DECLINED`.

### 2.7 Interview Rounds & Evaluations (`placement_interview_rounds`, `placement_interview_schedules`, `placement_interview_evaluations`)
- Tracks round progression (`APTITUDE`, `TECHNICAL`, `CODING`, `HR`, `FINAL`).
- Schedules have explicit times, interviewers, and meeting URLs or venue rooms.
- Evaluations record score, feedback, internal notes, and hiring recommendation.

### 2.8 Offers & Outcomes (`placement_offers`, `placement_outcomes`)
- Official offer issuance with `OFF-YYYY-XXXXXX` and expiration dates.
- Acceptance atomically transitions student availability to `PLACED` and records an accreditation `PlacementOutcome`.

---

## 3. Deterministic Eligibility Pipeline

```text
Student requests Eligibility / Application
                 ↓
Fetch Canonical Cross-Domain Data:
  • SemesterExamResult: calculate CGPA (Σ(grade_point * credits) / Σ credits)
  • SemesterExamResult: active backlogs (result_status = 'FAIL')
  • AttendanceSession: attendance percentage (PRESENT / TOTAL sessions)
  • StudentInvoice: overdue unpaid balances (status in ['ISSUED', 'OVERDUE'])
  • StudentProfile: program_code & department_code
                 ↓
Iterate Defined Eligibility Rules:
  • CGPA_MINIMUM: student_cgpa >= rule.value_json
  • BACKLOG_NONE: active_backlogs == 0
  • ATTENDANCE_MINIMUM: attendance_pct >= rule.value_json
  • FEE_CLEARANCE: overdue_invoices == 0
  • PROGRAM_ALLOWED: student_program in rule.value_json
                 ↓
Produce Eligibility Evaluation Response:
  • is_eligible: all mandatory rules pass
  • Mint PlacementEligibilitySnapshot
```

---

## 4. Multi-Tenant Boundary Enforcement

1. Every SQL query filters by `tenant_id == current_tenant.id`.
2. Cross-tenant access attempts immediately raise `TenantMismatchException` (HTTP 403).
3. Student endpoints strictly resolve candidate identities via authenticated session context (`current_user.id`), eliminating parameter tampering attacks.
