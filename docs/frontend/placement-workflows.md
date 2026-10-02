# CampusOS — Placement Workflows & Operations

## 1. Overview

CampusOS Placement replaces informal recruiter coordination and spreadsheet tracking with unified, state-machine-governed recruitment workflows. Every state transition is recorded with timestamped audit entries (`timeline`), preserving institutional integrity.

---

## 2. Core Workflows

### 2.1 Corporate Partner Lifecycle
```text
PROSPECT ──(Onboard & Sign MoU)──► ACTIVE ──(Inactivity / Non-hiring)──► INACTIVE
                                       │
                                       └──(Breach of Terms / Blacklist)──► BLACKLISTED
```
- **Rule**: Historical company records are never deleted; lifecycle state changes preserve recruitment analytics.
- **Tiers**: `TIER_1` (Dream/Super Dream, CTC ≥ 14 LPA), `TIER_2` (Core/Standard, 6–14 LPA), `TIER_3` (Mass/Mass Core, < 6 LPA).

---

### 2.2 7-Step Guided Job Drive Creation Workflow
When a placement officer launches a campus recruitment drive, the guided workflow navigates through 7 sequential phases:

```text
Step 1: Company Selection
  ├── Select from verified active corporate partners
  └── Review historical recruitment tier and contacts

Step 2: Drive Logistics & Details
  ├── Drive Title & Event Code
  ├── Drive Type (ON_CAMPUS / OFF_CAMPUS / VIRTUAL / POOLED)
  ├── Venue / Laboratory Allocation
  ├── Application Deadline
  └── Scheduled Drive Date

Step 3: Positions Configuration
  ├── Add 1 to N distinct Job Positions
  ├── Department / Function designation
  └── Expected vacancies count

Step 4: Academic Eligibility Rules
  ├── Target Programs (e.g., B.Tech CSE, IT, ECE)
  ├── Target Departments
  ├── Graduation Year Cohort (e.g., 2026)
  ├── Minimum CGPA Cutoff (e.g., 7.50)
  ├── Maximum Active Backlogs (e.g., 0)
  └── Minimum Attendance Gate (e.g., 75%)

Step 5: Compensation Slabs
  ├── Annual CTC (LPA)
  ├── Fixed Base Salary (LPA)
  ├── Performance Variable Incentive (LPA)
  └── Internship Monthly Stipend (if conversion track)

Step 6: Comprehensive Review
  └── Full read-only audit preview of all 5 configured dimensions

Step 7: Deliberate Save as DRAFT
  └── Initialized in DRAFT state. Must be explicitly published into OPEN by Placement Directorate.
```

---

### 2.3 Student Application Workflow
```text
Eligible Drive in Student Portal
        ↓
Inspect Position Details & Compensation
        ↓
Eligibility Snapshot Validation (Automatic rule verification)
        ↓
Review Verified Resume Dossier
        ↓
Explicit Confirmation Dialog
        ↓
Application Created (Status: SUBMITTED, Stage: APPLICATION)
```
- **Duplicate Protection**: A student cannot submit multiple applications to the same position/drive.
- **Read-Only Lock**: Once submitted, candidates cannot modify application records or alter academic snapshots.

---

### 2.4 Candidate Shortlisting Workflow
1. Placement officer filters applicants by drive, CGPA range, department, and technical skills.
2. Candidate eligibility snapshots and verified resume status are reviewed.
3. Batch selection action triggers `shortlistApplications`:
   - Application status updates to `SHORTLISTED`.
   - Current stage advances to `TECHNICAL` interview.
   - Student placement profile `shortlistsCount` increments.
4. Candidates not advancing can be rejected with mandatory institutional rejection reason logged in audit history.

---

### 2.5 Multi-Round Interview Workflow
```text
Schedule Round (SCREENING, APTITUDE, TECHNICAL, MANAGERIAL, HR, FINAL)
        ↓
Status: SCHEDULED
        ├── Reschedule (Captures new date, time, actor, and documented justification)
        └── Panel Interview Session
                ↓
Structured 4-Dimension Evaluation Form:
  - Technical Skills Rating (1–5)
  - Communication Rating (1–5)
  - Problem Solving Rating (1–5)
  - Role Fit Rating (1–5)
  - Overall Recommendation (STRONG_HIRE, HIRE, WEAK_HIRE, REJECT)
  - Qualitative Strengths & Improvement Areas
        ↓
Status: COMPLETED
```

---

### 2.6 Corporate Offer & Decision Desk
```text
Selected in Final Interview Round
        ↓
Placement Directorate Releases Formal Offer
  ├── CTC, Base Salary, Variable, Stipend
  ├── Posting Location & Joining Date
  └── Response Deadline (Countdown timer)
        ↓
Status: RELEASED
        │
        ├── Candidate ACCEPTS Offer
        │     ├── Application status transitions to SELECTED
        │     ├── Student Profile marked as PLACED
        │     └── Auto-syncs to Institutional Outcomes Ledger
        │
        └── Candidate DECLINES Offer
              ├── Captures documented reason (Higher Studies / Competitive Offer)
              └── Offer marked as DECLINED (Candidate remains in placement pool)
```

---

### 2.7 Placement Outcome Confirmation
```text
Candidate Accepts Offer
        ↓
Pending Verification
        ↓
Placement Directorate Audits Signed Offer Letter
        ↓
Outcome Status Confirmed as PLACED
  ├── Verifies corporate partner, position, package, joining date
  └── Published to official institutional placement records
```
- **Rule**: Offer release $\ne$ automatic final placement. Outcomes require verified acceptance or deliberate administrative confirmation.
