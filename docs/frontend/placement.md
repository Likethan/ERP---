# CampusOS — Placement Management Architecture

## 1. Executive Overview

The **Placement Management** module within CampusOS delivers an enterprise-grade corporate career operations center that unifies placement officers, candidate students, corporate recruiters, department HODs, and administrators into a synchronized recruitment pipeline.

Following the core CampusOS academic sequence:
```text
People → Academics → Attendance → Examinations → Finance → Placement
```

The Placement module bridges institutional academic achievement with career outcomes, enforcing strict eligibility criteria, multi-stage interview scheduling, CTC compensation packages, and auditable outcome confirmations.

---

## 2. Architectural Scope & Boundaries

### Absolute Frontend-Only Guarantee
- **Zero Backend Business Logic**: No endpoints, database models, migrations, or persistence services were modified or introduced in `apps/api`.
- **API Continuity**: The interface strictly adheres to future REST endpoint contracts (`/api/v1/placement/*`).
- **Reactive Mock Adapter**: Implemented in `apps/web/src/services/placement.service.ts` backed by stateful in-memory collections that maintain relational integrity between canonical students, corporate partners, job drives, position rules, applications, evaluations, offers, and placement outcomes.

---

## 3. End-to-End Recruitment Pipeline

CampusOS Placement orchestrates the complete corporate recruitment lifecycle:

```text
Student Placement Profile
        ↓
Corporate Partner Onboarding (TIER_1 / TIER_2 / PROSPECT)
        ↓
Campus Recruitment Drive (DRAFT → UPCOMING → OPEN → CLOSED → COMPLETED)
        ↓
Job Position & Compensation Slabs (CTC, Base, Variable, Stipend)
        ↓
Configurable Eligibility Rules (Programs, Graduation Year, CGPA, Backlogs, Skills)
        ↓
Automated Eligibility Snapshot (Rule-by-rule evaluation cards)
        ↓
Candidate Application Submission (Profile, Resume, Verification)
        ↓
Department / Officer Candidate Shortlisting
        ↓
Multi-Round Interview Process (SCREENING, APTITUDE, TECHNICAL, MANAGERIAL, HR, FINAL)
        ↓
Structured Panel Evaluation (Technical, Communication, Problem Solving, Role Fit)
        ↓
Formal Corporate Offer Release (CTC Breakdown, Response Deadline)
        ↓
Candidate Decision (Acceptance / Decline Desk)
        ↓
Placement Outcome Confirmation (Audit Ledger: PLACED, IN_PROCESS, NOT_PLACED, DEFERRED)
```

---

## 4. Route Inventory

| Route Path | Description | Access Role |
| :--- | :--- | :--- |
| `/app/placement` | Placement Operations Dashboard & Student "My Placement" Portal | Admin, Officer, HOD, Student |
| `/app/placement/students` | Enterprise Student Placement Profiles DataGrid & Filters | Placement Officer, HOD, Admin |
| `/app/placement/students/[id]` | Student Placement 360° Dossier (8 tabbed views, resume verification) | Placement Officer, HOD, Student (own) |
| `/app/placement/companies` | Corporate Partner Directory & Onboarding Management | Placement Officer, Admin |
| `/app/placement/companies/[id]` | Corporate Partner 360° Profile (Contacts, Drives, Offers) | Placement Officer, Admin |
| `/app/placement/drives` | Job Drives DataGrid & 7-Step Guided Creation Workflow | Placement Officer, Admin |
| `/app/placement/drives/[id]` | Job Drive Operations Center (Governance, Applicants, Rounds) | Placement Officer, Admin |
| `/app/placement/positions` | Job Positions Catalog & Cutoff Configurations | Placement Officer, Admin |
| `/app/placement/applications` | Applications DataGrid, Multi-Criteria Filters & Shortlisting Desk | Placement Officer, HOD |
| `/app/placement/applications/[id]` | Application Detail, Eligibility Snapshot & Authority Override | Placement Officer, HOD |
| `/app/placement/interviews` | Interviews Schedule DataGrid & Interview Scheduling Modal | Placement Officer, Coordinator |
| `/app/placement/interviews/[id]` | Interview Detail, Panel Coordinates, Evaluation & Rescheduling | Placement Officer, Panelist |
| `/app/placement/offers` | Formal Corporate Offers Ledger & Release Offer Modal | Placement Officer, Admin |
| `/app/placement/offers/[id]` | Offer Dossier, CTC Breakdown, Student Acceptance / Decline Desk | Placement Officer, Student |
| `/app/placement/outcomes` | Final Institutional Placement Outcomes Ledger & Confirmation Modal | Placement Officer, Admin |
| `/app/placement/reports` | Multi-View Placement Intelligence & RFC 4180 CSV Export | Placement Officer, HOD, Admin |

---

## 5. Canonical Entity Continuity

The placement module preserves complete continuity with existing CampusOS entities:
- **Canonical Students**: Directly consumes students from People and Academics modules (`std-001` Aarav Patel, `std-002` Priya Sundaram, `std-003` Rohan Verghese, `std-004` Ananya Deshmukh, `std-005` Vikramaditya Rao).
- **Academic Context**: Consumes Programs, Departments, Graduation Years (2026 / 2027), CGPAs, Backlogs, and Attendance Percentages.
- **Examinations**: Evaluates cumulative grade performance without creating duplicate grading records.
- **Documents**: Interfaces with resume document states (`NOT_UPLOADED`, `UPLOADED`, `UNDER_REVIEW`, `VERIFIED`, `REJECTED`).
- **Global Search**: Command palette indexing resolves company names, drive titles, position codes, application codes, and offer codes.

---

## 6. Known Limitations (Frontend Scope)
1. **Mock In-Memory Storage**: State updates (new offers, drives, applications) persist in browser memory during the session and reset upon full hard page reloads.
2. **Resume Storage**: Resume upload is simulated with verified status workflows; no binary blob storage or S3 buckets are connected on the backend.
3. **External Job Boards**: No third-party API sync with LinkedIn, Naukri, or ATS integrations as per explicit specifications.
