# Enterprise Institutional Research, Innovation, Grants & Intellectual Property Management Runbook

## Executive Summary

The **CampusOS Enterprise Institutional Research, Innovation, Grants & Intellectual Property Management Engine** (Step 44) provides higher education institutions, research universities, medical colleges, and polytechnics with an end-to-end statutory research governance and administration platform. It enables institutions to oversee the entire research lifecycle: project formulation, peer and ethics reviews, sponsored grant discovery and internal clearance, external agency award reconciliation, itemized budget control, deliverable and milestone monitoring, scholarly publication cataloging, and confidential invention disclosure/patent commercialization.

---

## 1. Architecture & Core Governance Principles

### 1.1 The Golden Rules of Research Administration
1. **Traceable Ownership & Authorized Roles**: Every research project must have an authoritative Principal Investigator (PI), defined co-investigators, and authorized participants with explicit access scopes (`FULL`, `CONTRIBUTOR`, `VIEW_ONLY`).
2. **Separation of Duties in Grant Clearance**: The Principal Investigator (or co-investigators) cannot conduct the institutional review or approve their own sponsored grant applications. An independent research dean, department chair, or sponsored programs officer must review and clear submissions.
3. **Award Allocation Ceilings & Financial Reconciliation**: The sum of allocated budget line items across itemized budget plans cannot exceed the total grant award amount. Disbursed and actual expenditures can never drive remaining grant cash balances below zero.
4. **Mandatory Ethics Review for Project Activation**: Projects flagged with `requires_ethics_approval = True` cannot transition to `ACTIVE` status without at least one formally `APPROVED` institutional ethics clearance (e.g., IRB, Animal Care/IACUC, Biosafety/IBC).
5. **Milestone Integrity & Project Closure**: A project cannot be transitioned to `COMPLETED` if any milestone flagged with `is_mandatory_for_closure = True` remains uncompleted or unverified. Milestone completions require an independent verifier.
6. **Multi-Tier IP Confidentiality**: Invention disclosures and patent filings enforce three strict confidentiality tiers (`INTERNAL_CONFIDENTIAL`, `STRICTLY_CONFIDENTIAL`, `PUBLIC_DISCLOSURE`) to preserve patentability and protect institutional trade secrets prior to statutory patent filing.
7. **Immutable Audit Trail**: All state transitions, team member additions, grant submissions, budget revisions, ethics determinations, and risk adjustments emit structured, immutable audit log entries.

```
                           +--------------------------------------+
                           |   RESEARCH FUNDING OPPORTUNITIES     |
                           |   - NSF, NIH, Horizon Europe, Industry|
                           |   - Closing Date & Eligibility Match |
                           +------------------+-------------------+
                                              |
                                              | Solicits
                                              v
                           +--------------------------------------+
                           |     SPONSORED GRANT APPLICATION      |
                           |  - Work Packages & Proposed Budget   |
                           |  - Institutional Clearance Review    |
                           |  - Separation of Duties (Non-PI)     |
                           +------------------+-------------------+
                                              |
                                              | Awarded
                                              v
                           +--------------------------------------+
                           |          GRANT AWARD & CASH          |
                           |  - Award Total & Disbursement Schedule|
                           |  - Allocation Ceiling Enforcement    |
                           +------------------+-------------------+
                                              |
                                              | Funds
                                              v
                           +--------------------------------------+
                           |      INSTITUTIONAL RESEARCH PROJECT  |
                           |  - PI Ownership & Team Roster        |
                           |  - Lifecycle State Machine           |
                           +--------+--------------------+--------+
                                    |                    |
                 +------------------+                    +------------------+
                 |                                                          |
                 v                                                          v
    +---------------------------+                              +---------------------------+
    | ETHICS & REGULATORY       |                              | RECONCILED ITEM BUDGETS   |
    | - IRB / IACUC / Biosafety |                              | - Versioned Plans         |
    | - Expiration Tracking     |                              | - Category-level Ceilings |
    | - Active Gatekeeper       |                              | - Expenditure Recording   |
    |                           |                              +-------------+-------------+
    +-------------+-------------+                                            |
                  |                                                          |
                  v                                                          v
    +---------------------------+                              +---------------------------+
    | MILESTONES & DELIVERABLES |                              | PROJECT RISKS & AUDIT     |
    | - Mandatory Closure Gates |                              | - Likelihood x Impact     |
    | - Independent Verifier    |                              | - Mitigation Tracking     |
    +-------------+-------------+                              +-------------+-------------+
                  |                                                          |
                  +-------------------------+--------------------------------+
                                            |
                                            v
                           +--------------------------------------+
                           |    SCHOLARLY OUTPUTS & PATENTS       |
                           |  - Publications & DOI Verification   |
                           |  - Confidential Invention Disclosures|
                           |  - Institutional Ownership %         |
                           |  - Patent Filing & Licensing Revenue |
                           +--------------------------------------+
```

---

## 2. Research Project Lifecycle State Machine

Projects progress through formal, audited states. Transitions require administrative authorization and record transition rationale:

```
[DRAFT] -----------> [SUBMITTED] -----------> [UNDER_REVIEW]
                         |                          |
                         v                          v
                     [DRAFT]                   [APPROVED]
                                                    |
                                                    | (Ethics clearance verified)
                                                    v
                                                [ACTIVE]
                                               /   |    \
                                              /    |     \
                                             v     v      v
                                   [COMPLETED] [SUSPENDED] [TERMINATED]
```

### 2.1 State Definitions & Transition Rules

| State | Allowed Next States | Prerequisites & Enforcement Rules |
| :--- | :--- | :--- |
| `DRAFT` | `SUBMITTED` | Project code, title, domain, PI, and proposed budget must be valid. |
| `SUBMITTED` | `UNDER_REVIEW`, `DRAFT` | Project formally lodged with Research Office or Department Chair. |
| `UNDER_REVIEW` | `APPROVED`, `DRAFT`, `TERMINATED` | Evaluated by Academic Research Committee. Cannot be approved by PI. |
| `APPROVED` | `ACTIVE`, `DRAFT` | If `requires_ethics_approval == True`, at least one approved ethics certificate must exist. |
| `ACTIVE` | `COMPLETED`, `SUSPENDED`, `TERMINATED` | Work actively progressing; budget expenditures and milestones can be recorded. |
| `COMPLETED` | *Terminal State* | All mandatory milestones (`is_mandatory_for_closure == True`) must be completed (`100%`) and verified. |
| `SUSPENDED` | `ACTIVE`, `TERMINATED` | Placed on administrative or compliance hold (e.g., pending ethics re-certification). |
| `TERMINATED` | *Terminal State* | Terminated due to grant cancellation, investigator departure, or regulatory order. |

---

## 3. Separation of Duties Matrix

To ensure regulatory compliance, statutory integrity, and prevention of fraud or conflicts of interest, CampusOS enforces role-based separation:

| Action / Operation | Principal Investigator (PI) | Co-Investigator / Member | Research Dean / Reviewer | Finance / Grants Officer |
| :--- | :---: | :---: | :---: | :---: |
| Create Project Draft | ✅ | ✅ | ✅ | ❌ |
| Submit Project for Review | ✅ | ❌ | ❌ | ❌ |
| Approve Project Proposal | ❌ (Strictly Prohibited) | ❌ | ✅ | ❌ |
| Submit Sponsored Grant Application | ✅ | ✅ | ❌ | ❌ |
| Internal Clearance of Grant Application | ❌ (Strictly Prohibited) | ❌ | ✅ | ✅ |
| Record Grant Award & Allocation | ❌ | ❌ | ❌ | ✅ |
| Revise Itemized Budget Plan | ✅ (Request) | ❌ | ❌ | ✅ (Approve) |
| Issue Ethics / IRB Approval | ❌ (Strictly Prohibited) | ❌ | ✅ (IRB Chair Only) | ❌ |
| Verify Deliverable / Milestone | ❌ (Self-check barred) | ❌ | ✅ | ❌ |
| Register Confidential Invention Disclosure | ✅ | ✅ | ✅ | ❌ |

---

## 4. Sponsored Grants & Financial Allocation Governance

### 4.1 Grant Award Financial Invariants
1. **Allocation Ceiling**:
   $$\sum \text{allocated\_amount}(\text{budget\_items}) \le \text{award\_amount}$$
2. **Remaining Grant Balance**:
   $$\text{remaining\_balance} = \text{received\_amount} - \text{spent\_amount} \ge 0$$
3. **Disbursement Schedule**: Every award tracks tranche disbursements with planned date, milestone trigger, received status, and remittance reference.

### 4.2 Itemized Budget Plans & Revisions
- Budgets are organized by standard expenditure categories:
  - `PERSONNEL` (Postdocs, research assistants, graduate stipends)
  - `EQUIPMENT` (Lab machinery, servers, specialized scientific hardware)
  - `CONSUMABLES` (Reagents, chemicals, lab disposables)
  - `TRAVEL` (Fieldwork, academic conferences)
  - `OVERHEAD` (Indirect institutional facilities and administrative costs)
  - `SUBCONTRACT` (External testing, specialist partner contracts)
- Revisions increment `version_number`, log `revision_reason`, require authorized `approved_by_user_id`, and immediately update the project's aggregate financial commitments.

---

## 5. Regulatory Ethics & Compliance Workflows

### 5.1 Ethics Review Categories
- **Institutional Review Board (IRB) / Human Participants**: Required for surveys involving identifiable data, behavioural studies, and clinical protocols.
- **Institutional Animal Care and Use Committee (IACUC)**: Mandatory for all vertebrate animal experimentation, housing, and breeding protocols.
- **Institutional Biosafety Committee (IBC)**: Mandatory for recombinant DNA, pathogens, biological toxins, and gene therapy vectors.
- **Export Control & Dual-Use Clearance**: Required for sensitive technology items subject to EAR/ITAR regulations.
- **Conflict of Interest (COI)**: Disclosures required for commercial affiliations, equity holdings, or consulting agreements.

### 5.2 Automated Compliance & Deadline Sweep
The system provides an automated scheduled sweep endpoint (`POST /api/v1/research/compliance/sweep-deadlines`):
- **Expiring Ethics Approvals**: Scans approvals expiring within 30 days and flags renewal requirements.
- **Overdue Deliverables**: Scans uncompleted milestones with `planned_date < today` and raises alerts.
- **Closing Opportunities**: Identifies funding solicitations closing within 14 days and notifies department researchers.

---

## 6. Scholarly Outputs & Intellectual Property (IP)

### 6.1 Publication Cataloging
- Supports standard scholarly output types: `JOURNAL_ARTICLE`, `CONFERENCE_PAPER`, `BOOK_CHAPTER`, `RESEARCH_DATASET`, `PATENT_GRANT`, `SOFTWARE_TOOL`.
- Captures DOIs, URNs, citation counts, open-access status, and funding agency grant acknowledgements.
- Research office verification (`is_verified = True`) marks publication records authoritative for institutional accreditation (e.g., NAAC Criterion 3, NBA, NIRF).

### 6.2 Invention Disclosures & Patents
- **Confidentiality Control**:
  - `INTERNAL_CONFIDENTIAL`: Accessible by named inventors, department chairs, and technology transfer officers.
  - `STRICTLY_CONFIDENTIAL`: Accessible strictly by named inventors and patent legal counsel.
  - `PUBLIC_DISCLOSURE`: Unrestricted access post-publication or statutory patent publication.
- **Institutional Ownership**: Records institutional vs. inventor equity split percentage (e.g., 60% university, 40% inventors).
- **Statutory Tracking**: Tracks provisional applications, PCT international phases, national stage filings, examination grants, and commercialization licensing revenue.

---

## 7. Security, Permissions & Multi-Tenancy

### 7.1 Multi-Tenant Isolation
All 13 research database tables implement `tenant_id` foreign keys with B-tree indices and automated schema migration. All queries in `ResearchService` strictly scope access to the requestor's authenticated tenant context.

### 7.2 Fine-Grained RBAC Permissions
| Permission String | Scope & Allowed Operations | Typical Assigned Roles |
| :--- | :--- | :--- |
| `research:view` | Read projects, funding opportunities, publications, milestones | Faculty, Students, Staff |
| `research:create` | Create projects, grant applications, outputs, disclosures | Faculty Researchers, PIs |
| `research:manage` | Status transitions, team rosters, milestone approvals | Research Deans, Department Chairs |
| `research:finance` | Grant awards, itemized budgets, expenditure reconciliation | Grants & Finance Officers |
| `research:ethics` | Ethics applications, review decisions, compliance sweeps | IRB / IACUC Committee Members |
| `research:ip` | Invention disclosures, patent filings, commercial licensing | Tech Transfer Officers, IP Counsel |

---

## 8. REST API Reference

| Endpoint | Method | Purpose | Required Permission |
| :--- | :---: | :--- | :--- |
| `/api/v1/research/projects` | `POST` | Register new institutional research project | `research:create` |
| `/api/v1/research/projects` | `GET` | List projects with domain/status filtering | `research:view` |
| `/api/v1/research/projects/{id}` | `GET` | Retrieve complete project record with PI info | `research:view` |
| `/api/v1/research/projects/{id}/transition` | `POST` | Execute audited state transition | `research:manage` |
| `/api/v1/research/projects/{id}/team` | `POST` | Add investigator or external collaborator | `research:manage` |
| `/api/v1/research/opportunities` | `POST` | Catalog new funding agency opportunity / RFP | `research:manage` |
| `/api/v1/research/opportunities` | `GET` | List active funding solicitations | `research:view` |
| `/api/v1/research/grant-applications` | `POST` | Lodge sponsored grant application | `research:create` |
| `/api/v1/research/grant-applications/{id}/internal-review` | `POST` | Independent institutional review & clearance | `research:manage` |
| `/api/v1/research/grant-applications/{id}/external-submission` | `POST` | Record external submission reference | `research:manage` |
| `/api/v1/research/awards` | `POST` | Record formal grant award from agency | `research:finance` |
| `/api/v1/research/projects/{id}/budget-plans` | `POST` | Create or revise itemized budget plan | `research:finance` |
| `/api/v1/research/projects/{id}/milestones` | `POST` | Define deliverable or work milestone | `research:create` |
| `/api/v1/research/milestones/{id}/complete` | `POST` | Complete & verify milestone deliverable | `research:manage` |
| `/api/v1/research/projects/{id}/ethics-approvals` | `POST` | Issue IRB / ethics compliance determination | `research:ethics` |
| `/api/v1/research/outputs` | `POST` | Catalog scholarly publication or dataset | `research:create` |
| `/api/v1/research/intellectual-property` | `POST` | Register confidential invention disclosure | `research:ip` |
| `/api/v1/research/analytics/summary` | `GET` | Compute live research performance metrics | `research:view` |
| `/api/v1/research/compliance/sweep-deadlines` | `POST` | Trigger automated compliance & deadline audit | `research:manage` |

---

## 9. Operational Troubleshooting

| Symptom | Probable Cause | Corrective Action |
| :--- | :--- | :--- |
| `Cannot activate project RES-XXX without an approved ethics clearance.` | Project has `requires_ethics_approval = True` but no approved ethics certificate. | Submit ethics review via `/projects/{id}/ethics-approvals` with status `APPROVED`. |
| `Cannot transition project to COMPLETED while mandatory milestones remain incomplete.` | One or more mandatory milestones have status != `COMPLETED` or completion < 100%. | Complete and verify all mandatory deliverables via `/milestones/{id}/complete`. |
| `Principal Investigator cannot conduct internal institutional review of their own grant application.` | Reviewer user ID matches `principal_investigator_id`. | Assign an independent reviewer (Department Chair, Research Dean). |
| `Total allocated budget ($X) exceeds award ceiling ($Y).` | Itemized budget plan proposed allocations exceed grant award amount. | Reduce category budget allocations or request supplemental grant award. |
| `Disclosures not showing up in console.` | Filtered by confidentiality or permission scope. | Ensure the user has `research:ip` or is a named inventor on the disclosure. |
