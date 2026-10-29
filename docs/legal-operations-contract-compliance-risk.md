# CampusOS — Step 62: Enterprise Legal Affairs, Contract Lifecycle, Policy Compliance & Institutional Risk Management

**Product Identity:** One Campus. One System. One Source of Truth.  
**Module Scope:** Institutional Legal Operations, Contract Lifecycle Management (CLM), Contractual Commitments & Obligations, Restricted Institutional Legal Matters, Policy & Procedure Governance, Statutory & Accreditation Compliance Tracking, and Enterprise Institutional Risk Management.

---

## 1. Executive Summary & Domain Boundaries

CampusOS Step 62 centralizes enterprise legal affairs and contract operations for higher education institutions into a single, highly auditable workspace. It bridges academic leadership, procurement offices, sponsored research directors, institutional compliance officers, general counsel, and university executive leadership.

### Clear Boundary Separation
- **Not a competing document repository:** Reuses existing CampusOS document services and controlled version records; stores metadata, audit records, and document references.
- **Not a pseudo-signature engine:** Never falsely claims CampusOS performed digital signatures. Verified methods include `EXTERNAL_DIGITAL_SUITE_CONFIRMED` (DocuSign/Adobe Sign envelope references), `WET_SIGNATURE_CONFIRMED` (countersigned physical execution scans), and `BOARD_RESOLUTION_CONFIRMED` (governing board seals).
- **Not automated legal advice:** Provides administrative workflow and compliance recordkeeping without substituting qualified attorney analysis or automatic legal certification.
- **Preserves Step 19 & Step 41 Legal Holds & Retention:** Any contract, matter, or policy under active legal hold cannot be deleted or purged.

---

## 2. Core Capabilities & Architecture

### A. Contract Lifecycle Management (CLM)
State Machine Progression:
```
DRAFT
  │
  ▼
INTERNAL_REVIEW
  │
  ▼
DEPARTMENT_APPROVAL
  │
  ▼
LEGAL_REVIEW
  │
  ▼
AUTHORIZED_APPROVAL
  │
  ▼
READY_FOR_EXECUTION
  │
  ▼
EXECUTED (Verified External / Wet Signatures)
  │
  ▼
ACTIVE
  ├──► EXPIRING (Automated Notice Window) ──► RENEWED / EXPIRED / TERMINATED
  └──► ON_HOLD / ARCHIVED
```
- **Supported Categories:**
  - `VENDOR_PROCUREMENT` (reusing Step 50 purchase orders & master agreements)
  - `EMPLOYMENT_CONSULTING`
  - `SERVICE_LEVEL_AGREEMENT`
  - `STUDENT_SERVICE`
  - `RESEARCH_SPONSORED_PROJECT` (reusing Step 44 & Step 61 grants and research projects)
  - `INDUSTRY_COLLABORATION`
  - `DATA_PROCESSING_PRIVACY`
  - `FACILITY_USE_PARTNERSHIP`
  - `INTERNATIONAL_INSTITUTIONAL` (reusing Step 60 international partnerships)
  - `OTHER_INSTITUTIONAL`
- **Contract Amendments:** Formal numbered addenda (`amendment_number`, `summary`, `effective_date`, `financial_value_delta`) updating base contracts with audit history.

### B. Contract Obligations & Commitments Register
- Tracks deliverables, reporting deadlines, insurance certificates (COIs), payment milestones, SLA commitments, renewal windows, and audit rights.
- **Statuses:** `PENDING`, `IN_PROGRESS`, `UNDER_REVIEW`, `OVERDUE`, `COMPLETED`, `WAIVED`.
- **Enforced Governance:**
  - Completing an obligation requires evidence references and completion notes.
  - Waiving an obligation requires executive/counsel rationale and records an immutable audit entry.
  - Automated detection of overdue dates with multi-level escalation (`escalation_level`).

### C. Restricted Institutional Legal Matters
- Restricted register for contract disputes, supplier disputes, employment grievances, regulatory inquiries, litigation, outside counsel engagements, and formal legal opinions.
- **Strict Confidentiality & Work-Product Privilege:**
  - Marked `RESTRICTED` / `ATTORNEY_CLIENT_PRIVILEGED`.
  - Filtered out from general search, unauthorized exports, and unprivileged dashboards.
  - Resource-level permission check: `LEGAL_MATTERS_CONFIDENTIAL` required to view privileged work-product notes.
  - Access to confidential notes generates a dedicated security audit log: `LEGAL_MATTER_CONFIDENTIAL_ACCESSED`.

### D. Institutional Policy & Procedure Governance
- Extends the Step 42 controlled policy library.
- Covers Academic, Student Conduct, Faculty/Staff, Information Security, Financial, and Research Ethics policies.
- **Lifecycle:** `DRAFT` → `UNDER_REVIEW` → `APPROVED` → `PUBLISHED` → `SUPERSEDED` → `RETIRED`.
- Tracks mandatory digital attestations and annual acknowledgments.
- Only published policies represent active institutional law; drafts are restricted to authorized reviewers.

### E. Statutory & Accreditation Compliance Tracking
- Frameworks: Accreditation (NECHE, SACSCOC, etc.), FERPA, Title IX, Clery Act, Research Ethics, ADA Accessibility, OSHA, Financial Aid (Title IV HEA).
- Statuses: `NOT_ASSESSED`, `IN_PROGRESS`, `EVIDENCE_REQUIRED`, `UNDER_REVIEW`, `COMPLIANT`, `PARTIALLY_COMPLIANT`, `NON_COMPLIANT`, `REMEDIATION_IN_PROGRESS`, `CLOSED`.
- Corrective Action Plans (CAP): Assigns remediation owners, target completion dates, and tracks audit progress.

### F. Enterprise Institutional Risk Register
- Quantitative 5×5 Enterprise Scoring Matrix:
  $$\text{Score} = \text{Likelihood (1–5)} \times \text{Impact (1–5)}$$
  - **CRITICAL:** Score 16–25 (Mandatory executive escalation and active continuous monitoring)
  - **HIGH:** Score 10–15 (Senior leadership review; active mitigation within 30 days)
  - **MEDIUM:** Score 5–9 (Department-level management and scheduled periodic review)
  - **LOW:** Score 1–4 (Manageable under standard institutional controls)
- **Inherent vs. Residual Risk:** Compares pre-mitigation risk against post-mitigation residual score.
- **Executive Acceptance:** Formal recording of accepted residual risk by the Board Audit Committee or Provost with mandatory documented rationale.

### G. Idempotent Automated Renewal & Expiry Engine
- Scheduled sweep (`POST /api/v1/legal-operations/automation/renewal-sweep`) scanning:
  1. Active contracts within notice window $\to$ flags as `EXPIRING`.
  2. Expired active contracts $\to$ flags as `EXPIRED`.
  3. Pending obligations past due $\to$ flags as `OVERDUE` and increments escalation.
  4. Dispatches notifications to owners and supervisors without duplicate alerts.

---

## 3. Database Architecture & Alembic Migration

- **Migration Revision:** `046_enterprise_legal_affairs_contract_lifecycle_compliance_risk`
- **Down Revision:** `045_enterprise_research_collaboration_portfolio_grants`
- **Tables Created:**
  1. `institutional_contracts` (Master contract records, counterparty, values, dates, status, approval chain JSON)
  2. `contract_amendments` (Numbered addenda and financial deltas linked to contracts)
  3. `contract_obligations` (Deliverables, SLA commitments, COIs, completion evidence, waivers)
  4. `institutional_legal_matters` (Restricted cases, external counsel, opposing party, confidential work-product notes)
  5. `institutional_compliance_obligations` (Statutory mandates, governing authorities, review frequencies, CAPs)
  6. `institutional_risks` (5×5 matrix scores, inherent & residual evaluations, mitigation plans, executive acceptances)

---

## 4. API Endpoints (`/api/v1/legal-operations/...`)

| Method | Endpoint | Description | Required Permission |
|---|---|---|---|
| `GET` | `/dashboard` | Aggregated legal telemetry and KPI metrics | `LEGAL_OPERATIONS_READ` |
| `GET` | `/contracts` | Search and filter institutional contracts | `LEGAL_CONTRACTS_READ` |
| `POST` | `/contracts` | Create contract draft | `LEGAL_CONTRACTS_MANAGE` |
| `GET` | `/contracts/{id}` | Get full contract details with obligations & amendments | `LEGAL_CONTRACTS_READ` |
| `PATCH` | `/contracts/{id}` | Update contract parameters | `LEGAL_CONTRACTS_MANAGE` |
| `POST` | `/contracts/{id}/transition` | Advance contract lifecycle stage | `LEGAL_CONTRACTS_APPROVE` |
| `POST` | `/contracts/{id}/execute` | Record verified external execution | `LEGAL_CONTRACTS_EXECUTE` |
| `POST` | `/contracts/{id}/amendments` | Record contract amendment | `LEGAL_CONTRACTS_MANAGE` |
| `GET` | `/obligations` | Filter contractual obligations | `LEGAL_OBLIGATIONS_READ` |
| `POST` | `/obligations` | Register new contract obligation | `LEGAL_OBLIGATIONS_MANAGE` |
| `POST` | `/obligations/{id}/complete` | Verify and complete obligation with evidence | `LEGAL_OBLIGATIONS_MANAGE` |
| `POST` | `/obligations/{id}/waive` | Formally waive obligation with legal rationale | `LEGAL_OBLIGATIONS_MANAGE` |
| `GET` | `/matters` | List restricted legal matters (notes redacted) | `LEGAL_MATTERS_READ` |
| `POST` | `/matters` | Open new restricted legal matter | `LEGAL_MATTERS_MANAGE` |
| `GET` | `/matters/{id}` | Retrieve matter (includes notes if authorized) | `LEGAL_MATTERS_READ` |
| `PATCH` | `/matters/{id}` | Update matter status, settlement, or notes | `LEGAL_MATTERS_MANAGE` |
| `GET` | `/compliance` | List statutory compliance requirements | `LEGAL_COMPLIANCE_READ` |
| `POST` | `/compliance` | Register new statutory requirement | `LEGAL_COMPLIANCE_MANAGE` |
| `POST` | `/compliance/{id}/assess` | Record compliance assessment & CAP | `LEGAL_COMPLIANCE_MANAGE` |
| `GET` | `/risks` | List enterprise risk items | `LEGAL_RISKS_READ` |
| `POST` | `/risks` | Create 5x5 quantitative risk assessment | `LEGAL_RISKS_MANAGE` |
| `PATCH` | `/risks/{id}` | Update risk assessment or mitigation | `LEGAL_RISKS_MANAGE` |
| `POST` | `/risks/{id}/accept` | Formally accept residual risk with executive rationale | `LEGAL_RISKS_MANAGE` |
| `POST` | `/automation/renewal-sweep` | Execute idempotent expiration and renewal sweep | `LEGAL_CONTRACTS_MANAGE` |

---

## 5. Security & Access Control

1. **Multi-Tenancy:** Enforced on every single database query via `tenant_id` filtering.
2. **Confidentiality:** Work-product notes in `institutional_legal_matters` are automatically stripped unless the requesting user possesses `LEGAL_MATTERS_CONFIDENTIAL` clearance.
3. **Audit Trails:** All consequential actions (creation, transitions, verified executions, waivers, confidential access) record immutable audit entries in `core_audit_logs`.

---

## 6. Verification Results

### Backend Automated Test Suite (`apps/api/tests/test_enterprise_legal_operations_step62.py`)
```bash
& .venv/Scripts/python.exe -m pytest tests/test_enterprise_legal_operations_step62.py --show-capture=no
```
**Outcome:** **8 passed in 8.98s**
- `test_contract_lifecycle_end_to_end`: PASS
- `test_execution_confirmation_with_audit`: PASS
- `test_obligation_lifecycle_and_waiver`: PASS
- `test_restricted_legal_matter_confidentiality`: PASS
- `test_policy_governance_lifecycle`: PASS
- `test_compliance_assessment_and_remediation`: PASS
- `test_5x5_risk_matrix_scoring_and_residual_acceptance`: PASS
- `test_idempotent_renewal_and_expiry_sweep`: PASS

### Frontend Unit Test Suite (`apps/web/src/__tests__/legal-module.test.ts`)
```bash
npx tsx apps/web/src/__tests__/legal-module.test.ts
```
**Outcome:** **10 passed, 0 failed**
- Lifecycle transitions: PASS
- Legal and Authorized approval transitions: PASS
- Terminal and Reversal transitions: PASS
- Risk Matrix 5×5 Scoring (Critical, High, Medium, Low): PASS
- Obligations overdue and aggregate health metrics: PASS
- Presentation formatters and execution method labeling: PASS
