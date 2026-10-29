# Enterprise Research Collaboration, Project Portfolio, Grants & Sponsored Research Management (Step 61)

## Executive Summary

**CampusOS — One Campus. One System. One Source of Truth.**

Step 61 extends CampusOS's institutional research foundation (Step 44) into a unified enterprise research administration workspace. It bridges faculty-led, student, departmental, interdisciplinary, industry-sponsored, government, and international collaborative research portfolios into an integrated operational engine.

Key operational boundaries preserved:
- **Finance as Source of Truth**: Project budget planning and expenditure reconciliation coordinates directly with the central institutional general ledger without creating a parallel accounting ledger or fabricating phantom transactions.
- **Explainable Health Diagnostics**: Project health indices are calculated using deterministic, documented rules (overdue milestones, burn rate percentages, compliance renewal windows, unmitigated high risks), strictly forbidding opaque or fabricated AI scores.
- **Separation of Duties & Institutional Approval**: Grant proposals cannot be reviewed or institutionally approved by the Principal Investigator; external sponsor approval is never assumed until a verified sponsor award decision is recorded.
- **Closure Blocking**: Projects cannot transition to `CLOSED` until all mandatory milestones are independently accepted by authorized reviewers.

---

## 1. Domain Architecture & Integration

```
 +----------------------------------------------------------------------------------+
 |                          CAMPUSOS UNIFIED RESEARCH PORTFOLIO                     |
 | Faculty • Interdisciplinary • Student • Industry • Government • International   |
 +----------------------------------------+-----------------------------------------+
                                          |
        +---------------------------------+---------------------------------+
        |                                                                   |
        v                                                                   v
+-------------------------------+                               +-------------------------------+
|  GRANT OPPORTUNITY REGISTRY   |                               |  PROPOSAL WORKSPACE LIFECYCLE |
|  - Saved Opportunities        |                               |  - Draft & Work Packages      |
|  - Expressions of Interest    |                               |  - Institutional Clearance    |
|  - Deadline Sweep Dispatch    |                               |  - External Agency Confirm    |
+---------------+---------------+                               |  - Verified Sponsor Decision  |
                |                                               +---------------+---------------+
                +-------------------------------+-------------------------------+
                                                |
                                                v
                               +---------------------------------+
                               |  SPONSORED RESEARCH AGREEMENTS  |
                               |  - Contract Tranches / Milestones
                               |  - Deliverables & Renewals      |
                               |  - Audited Contract Amendments  |
                               +----------------+----------------+
                                                |
        +---------------------------------------+---------------------------------------+
        |                                       |                                       |
        v                                       v                                       v
+-------------------------------+   +-------------------------------+   +-------------------------------+
| BUDGET & LEDGER COORDINATION  |   | MILESTONES & ACCEPTANCE QUEUE |   | ETHICS & COMPLIANCE CLEARANCE |
| - Personnel, Equip, Supplies  |   | - Independent Review Queue    |   | - IRB, IACUC, Biosafety (IBC) |
| - Finance Ledger Reconciled   |   | - Acceptance Criteria Checks  |   | - Protocol Expiration Alerts  |
| - Audited Reallocations       |   | - Project Closure Blocker     |   | - Safety Lock on Expired      |
+-------------------------------+   +-------------------------------+   +-------------------------------+
```

---

## 2. API Endpoints

All endpoints are scoped under `/api/v1/research/` and require tenant authentication and role-based permissions:

| Endpoint | Method | Permission | Summary |
|---|---|---|---|
| `/projects` | GET, POST | `research.projects.read / manage` | List with advanced filtering (search, status, domain, PI) & create research projects |
| `/projects/{id}` | GET, PATCH | `research.projects.read / manage` | Get project & update core parameters |
| `/projects/{id}/health` | GET | `research.projects.read` | Get explainable, rule-based project health diagnostic |
| `/projects/{id}/details` | GET | `research.projects.read` | 360-degree aggregated dossier (milestones, team, budgets, ethics, IP, risks) |
| `/projects/{id}/transition` | POST | `research.projects.transition` | Lifecycle state transition with mandatory closure blocker validation |
| `/opportunities` | GET, POST | `research.projects.read / manage` | Search funding opportunity catalog & register opportunities |
| `/opportunities/{id}/save` | POST | `research.projects.read` | Bookmark/save funding opportunity for current user |
| `/opportunities/{id}/eoi` | POST | `research.grants.apply` | Record Expression of Interest (EOI) with prospective budget |
| `/grants/applications` | GET, POST | `research.projects.read / grants.apply` | Proposal workspace and draft submission |
| `/grants/applications/{id}/review` | POST | `research.grants.approve` | Record internal institutional review (enforces non-PI separation of duties) |
| `/grants/applications/{id}/confirm-submission` | POST | `research.grants.apply` | Confirm external agency submission with portal tracking reference |
| `/grants/applications/{id}/sponsor-decision` | POST | `research.grants.approve` | Record verified sponsor decision and optionally generate award agreement |
| `/agreements` | GET, POST | `research.projects.read / awards.manage` | List sponsored agreements and execute contracts with disbursement tranches |
| `/agreements/{id}/amendments` | POST | `research.awards.manage` | Record audited contract amendment with date extension and budget adjustment |
| `/budgets` | GET, POST | `research.projects.read / budgets.manage` | Itemized cost allocations across projects (personnel, equipment, supplies) |
| `/budgets/{id}/revise` | POST | `research.budgets.manage` | Audited budget revision with justification and version increment |
| `/budgets/projects/{id}/financial-summary` | GET | `research.projects.read` | Reconciled financial summary against central finance ledger |
| `/milestones` | GET, POST | `research.projects.read / projects.manage` | Cross-project milestone calendar & deliverable registration |
| `/milestones/{id}/verify` | POST | `research.projects.transition` | Independent deliverable acceptance review |
| `/ethics` | GET, POST | `research.projects.read / projects.manage` | Institutional ethics protocol registry (IRB, IACUC, IBC) |
| `/ethics/{id}/decide` | POST | `research.ethics.review` | Record official ethics committee determination (APPROVED, CHANGES_REQUIRED) |
| `/outputs` | GET, POST | `research.projects.read / outputs.manage` | Catalog publications and scholarly outputs |
| `/outputs/{id}/verify` | POST | `research.outputs.verify` | Confirm bibliographic and DOI indexing |
| `/ip/disclosures` | GET, POST | `research.projects.read / ip.manage` | Confidential invention disclosures and patent tracking |
| `/team/users/{id}/workload` | GET | `research.projects.read` | Compute researcher FTE workload and active project roster |
| `/team/my-projects` | GET | Authenticated User | Current user's active research projects and allocation |
| `/analytics/summary` | GET | `research.analytics.read` | Institutional research performance dashboard |
| `/analytics/sweep` | POST | `research.projects.transition` | Trigger scheduled compliance sweep for deadlines & expired ethics |

---

## 3. Database Changes & Migrations

- **Migration**: `apps/api/migrations/versions/045_enterprise_research_collaboration_portfolio_grants.py`
- **Revision Head**: `045_enterprise_research_collaboration_portfolio_grants (head)`
- **Schema Extensions**:
  - `research_projects`: Added `requires_ethics_approval`, `collaboration_type`, `risk_level`, `is_confidential`.
  - `research_funding_opportunities`: Added `is_saved_by_users_json`, `expressions_of_interest_json`, `last_verified_at`.
  - `research_grant_applications`: Added `sponsor_decision`, `sponsor_decision_date`, `sponsor_feedback`, `external_submitted_at`.
  - `research_grant_awards`: Added `amendments_json`, `scope_of_work`, `deliverables_json`, `payment_milestones_json`.
  - `research_milestones`: Added `is_mandatory_for_closure`, `verified_by_user_id`, `verified_at`, `verification_notes`.
  - `research_ethics_approvals`: Added `approval_type`, `decision_rationale`, `conditions_and_restrictions`.
  - `research_team_members`: Added `allocation_percentage`, `workload_fte`.

---

## 4. Role & Permission Matrix

| Role | Permitted Research Capabilities | Governance Constraints |
|---|---|---|
| **Student / Scholar** | View assigned projects, submit milestone progress, view compliance tasks | Read-only access to unassigned projects; no proposal or budget approval authority |
| **Faculty / PI** | Create proposals, manage project teams, submit deliverables, log risks | Cannot approve own grant proposals (enforces separation of duties); cannot close projects without verification |
| **Head of Department (HOD)** | Review departmental proposals, approve departmental clearances, monitor workload | Scoped to departmental projects and faculty allocations |
| **Vice Principal / Leadership** | Institutional grant approval, portfolio performance analytics, institutional budget sign-off | Oversees university-wide compliance and funding pipelines |
| **Research Administrator** | Manage grant opportunities, execute sponsor agreements, oversee IRB/IACUC ethics queues, trigger sweeps | Full lifecycle coordination authority across opportunities, awards, and compliance |
| **Finance Staff** | Reconcile awards, review itemized budget allocations, audit cost category burn | Financial oversight without permission to alter scientific scope or research methodology |

---

## 5. Verification Commands & Test Outcomes

### Backend Test Execution
```powershell
& "apps/api/.venv/Scripts/python.exe" -m pytest tests/test_enterprise_research_collaboration_step61.py tests/test_enterprise_research_management.py -v
```
**Outcome**: **21 passed, 0 failed in 17.22s**.

### Frontend Unit & Rule Verification
```powershell
npx tsx apps/web/src/__tests__/research-module.test.ts
```
**Outcome**: **Passed: 39, Failed: 0**.

### Authentication Portal Prerequisite Verification
```powershell
npx tsx apps/web/src/__tests__/auth-login-portal.test.ts
```
**Outcome**: **Passed: 65, Failed: 0**.

### Frontend TypeScript Compilation
```powershell
npx tsc --noEmit -p apps/web/tsconfig.json
```
**Outcome**: **0 errors (Exit code 0)**.
