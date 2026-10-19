# Enterprise Institutional Accreditation, Quality Assurance & Continuous Improvement Runbook

## Executive Summary

The **CampusOS Enterprise Institutional Accreditation & Quality Assurance Engine** (Step 43) provides universities, colleges, and polytechnics with an end-to-end statutory accreditation management platform. It enables institutions to configure multi-tier accreditation frameworks (e.g., NAAC, NBA, ISO-21001, NIRF, ABET), track assessment cycles, evaluate criteria rubrics, link verified evidence documents, monitor institutional KPIs, conduct internal quality audits, enforce corrective and preventive actions (CAPA), and compute transparent institutional readiness scores.

---

## 1. Architecture & Core Governance Principles

### 1.1 The Golden Rules of Quality Assurance
1. **Traceable Quality Claims**: Every assessment score and quality claim is strictly linked to assessment criteria, supporting evidence, accountable owner, and audit history.
2. **Separation of Duties**: The primary assessor or criterion owner is strictly barred from approving their own assessment submission. An independent peer reviewer or IQAC director must review and approve submissions.
3. **Optimistic Concurrency Control**: All draft updates enforce `lock_version` checking, ensuring concurrent evaluations by committee members do not result in lost updates.
4. **Audit Report Immutability**: Once an internal quality audit report is finalized, it is locked as permanently immutable (`is_immutable = True`). Any subsequent changes require formal addendum tracking.
5. **Separation of Duties on CAPA Closure**: A corrective action owner cannot verify or close their own CAPA. Verification and closure decisions require an independent quality auditor.
6. **Data Quality Integrity**: Quality indicators monitor observation completeness (percentage of reporting units reporting on time) and flag outliers, ensuring institutional metrics reflect dependable data.
7. **Transparent Readiness Index**: Institutional readiness percentage is calculated from weighted criteria completion, verified evidence ratio, audit conformance, and KPI target achievement, with automatic deductions for unresolved critical risk findings.

```
                           +--------------------------------------+
                           |  ACCREDITATION FRAMEWORK & CRITERIA  |
                           |  - NAAC, NBA, ISO-21001, Internal    |
                           |  - Version Snapshots (v1.0, v2.0...) |
                           +------------------+-------------------+
                                              |
                                              | Instantiates
                                              v
                           +--------------------------------------+
                           |      ASSESSMENT CYCLE (e.g. SSR)     |
                           |  - Auto-initializes Criterion Drafts |
                           +------------------+-------------------+
                                              |
                     +------------------------+------------------------+
                     |                                                 |
                     v                                                 v
        +---------------------------+                    +---------------------------+
        | CRITERION ASSESSMENT      |                    | EVIDENCE REPOSITORY       |
        | - Score & Rubric Eval     |                    | - Linked to Criteria      |
        | - Lock Version Check      | <================= | - Peer Verification       |
        | - Separation of Duties    |                    | - Expiration Tracking     |
        +-------------+-------------+                    +---------------------------+
                      |
                      | Submit & Independent Review
                      v
        +---------------------------+
        | APPROVED CRITERION        |
        +-------------+-------------+
                      |
         +------------+------------+
         |                         |
         v                         v
+------------------+     +-------------------+     +----------------------------------+
| QUALITY KPIS     |     | INTERNAL AUDITS   |     | READINESS ENGINE                 |
| - Time Series    |     | - Checklists      |     | - Weighted Criteria Score        |
| - Data Quality   |     | - CAPA Lifecycle  | ==> | - Evidence Verification Ratio    |
| - Outlier Alert  |     | - Finalized Lock  |     | - Critical Penalty Deductions    |
+------------------+     +-------------------+     +----------------------------------+
```

---

## 2. Statutory Framework Templates

CampusOS seeds statutory framework templates adhering to National Assessment and Accreditation Council (NAAC), National Board of Accreditation (NBA), and International Organization for Standardization (ISO) guidelines:

| Framework Code | Issuing Body | Scope | Criteria Count | Max Score | Scoring Model |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `NAAC-UNIV-TEMPLATE` | NAAC India | University / College | 7 Core Criteria | 1000.0 | Weighted Scale |
| `NBA-TIER-1-TEMPLATE` | NBA India | Engineering Tier 1 | 9 Program Criteria | 1000.0 | Weighted Scale |
| `ISO-21001-TEMPLATE` | ISO / EOMS | Educational Org | 7 Quality Clauses | 35.0 | Clause Rating |
| Custom Internal | Internal IQAC | Institution / Campus | Configurable | Configurable | Numeric / Rubric |

### 2.1 Standard NAAC Criteria Hierarchy
- **Criterion 1**: Curricular Aspects (Weight: 150)
- **Criterion 2**: Teaching-Learning & Evaluation (Weight: 200)
- **Criterion 3**: Research, Innovations & Extension (Weight: 250)
- **Criterion 4**: Infrastructure & Learning Resources (Weight: 100)
- **Criterion 5**: Student Support & Progression (Weight: 100)
- **Criterion 6**: Governance, Leadership & Management (Weight: 100)
- **Criterion 7**: Institutional Values & Best Practices (Weight: 100)

---

## 3. Assessment & Review Workflow

### 3.1 Draft Authoring
- Assessors evaluate assigned criteria against institutional benchmarks.
- Evaluation includes numeric `score`, `maturity_level` (Level 1 Initial to Level 5 Optimizing), `executive_summary`, `findings`, `strengths`, `weaknesses`, and `recommendations`.
- If a criterion does not apply (e.g. standalone undergraduate college without doctoral programs), `not_applicable_reason` must be provided.
- Each draft save validates `lock_version`. If a concurrent user has modified the record, `AccreditationOptimisticLockException` (HTTP 409) is returned.

### 3.2 Submission & Separation of Duties
- When draft evaluation is complete, assessor submits via `POST /assessments/{id}/submit`.
- Review and approval must be performed by an independent peer or IQAC officer via `POST /assessments/{id}/review`.
- If `assessor_id == actor_id` or `accountable_owner_id == actor_id`, the system raises `AccreditationSeparationOfDutiesException` (HTTP 403), barring self-approval.

---

## 4. Evidence Repository & Provenance

### 4.1 Verification Lifecycle
1. **UNVERIFIED**: Evidence uploaded or cataloged with validity dates and provenance metadata.
2. **VERIFIED**: Independent quality officer inspects certified archive stamps or registrar signatures and approves.
3. **REJECTED**: Insufficient documentation or provenance conflict.
4. **EXPIRED**: Past `valid_until` date. Flagged automatically by scheduled background sweep.

### 4.2 Evidence Categories
- `POLICY_SOP`: Approved institutional policies and standard operating procedures.
- `GOVERNANCE_MINUTES`: Board of Studies (BoS), Academic Council, and Governing Body resolutions.
- `EXAM_RECORD`: Examination committee evaluations, pass percentages, moderation logs.
- `FACULTY_CREDENTIAL`: Doctoral degrees, patents, journal publications, FDP certifications.
- `INFRASTRUCTURE_AUDIT`: Laboratory safety, green campus, barrier-free access audits.
- `SURVEY_FEEDBACK`: Student Satisfaction Surveys (SSS), alumni feedback, employer ratings.

---

## 5. Quality Indicators (KPIs) & Data Quality

Quality indicators monitor time-series performance across semesters or academic years:
- **Completeness Checking**: If observation `data_completeness_pct < 90.0%`, status is flagged as `WARNING_INCOMPLETE` with diagnostic notes detailing missing reporting units.
- **Outlier Detection**: If observed values deviate statistically from historic trends, status is flagged as `WARNING_STALE` / outlier.
- **Verified Status**: Observations with 100% data completeness and no anomalies achieve `EXCELLENT` data quality status.

---

## 6. Internal Audits & CAPA Resolution

### 6.1 Audit Execution
1. Internal audit programs (`QualityAuditProgram`) are scheduled by IQAC for academic, administrative, or ISO surveillance scopes.
2. Lead auditors assess checklists against statutory criteria.
3. Upon completion, the audit report is finalized via `POST /audits/{id}/finalize`.
4. Finalization permanently sets `is_immutable = True`. Any attempt to edit or add checklist items raises `AccreditationAuditFinalizedException` (HTTP 400).

### 6.2 Corrective and Preventive Actions (CAPA)
1. Audit non-conformances generate `QualityFinding` records with assigned severity (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
2. CAPA actions are proposed with preventive measures, target dates, and verification criteria.
3. Responsible owner executes corrective measures.
4. An independent quality officer verifies evidence and registers closure (`CLOSED_EFFECTIVE` or `REJECTED_FURTHER_ACTION`). The action owner cannot self-close their own CAPA.

---

## 7. Automated Scheduled Tasks & Sweeps

The background scheduler runs `sweep_quality_reviews()` hourly:
1. **Flag Expired Evidence**: Identifies all active evidence records where `valid_until < NOW()` and sets `is_expired = True`, updating status to `EXPIRED`.
2. **Flag Overdue Findings**: Finds open findings exceeding `target_resolution_date` and escalates status to `OVERDUE`.
3. **Flag Overdue CAPAs**: Identifies in-progress corrective actions past `due_date` and flags them for IQAC escalation.

---

## 8. Verification & Operations Command Cheatsheet

### 8.1 Execute Pytest Test Suite
```bash
# In apps/api
.venv\Scripts\pytest.exe tests\test_enterprise_accreditation.py -v -p no:logging
```

### 8.2 Verify Knowledge Base Regression
```bash
# In apps/api
.venv\Scripts\pytest.exe tests\test_enterprise_knowledge_base.py -v -p no:logging
```

### 8.3 Verify Frontend Next.js Build
```bash
# In apps/web
npm run build
```

### 8.4 Trigger Manual Scheduled Sweep via API
```bash
curl -X POST http://localhost:8000/api/v1/accreditation/scheduler/sweep \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```

### 8.5 Trigger Framework Seeding via API
```bash
curl -X POST http://localhost:8000/api/v1/accreditation/frameworks/seed-defaults \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```
