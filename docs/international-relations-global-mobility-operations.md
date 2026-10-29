# CampusOS International Relations, Student Exchange & Global Mobility Operations Runbook
**Product:** CampusOS  
**Tagline:** "One Campus. One System. One Source of Truth."  
**Module:** Enterprise International Relations, Student Exchange, Study Abroad & Global Mobility Management (Step 60)

---

## 1. Executive Summary & Architecture

The **CampusOS International Relations, Student Exchange & Global Mobility Module** establishes an institutional-grade, multi-tenant enterprise framework for higher education global engagement. Designed under the core product philosophy of **"One Campus. One System. One Source of Truth."**, this module eliminates disjointed spreadsheets, uncoordinated MoUs, untracked outbound student safety risks, and arbitrary credit conversions by unifying all global mobility functions into a single system of record.

### Key Functional Pillars

1. **International Partner Registry & Agreement Governance:** Centralized institutional directory of accredited global partner universities, research institutions, and consortia with lifecycle tracking for Memoranda of Understanding (MoUs), bilateral student exchange accords, and dual-degree articulation agreements.
2. **Automated MoU Expiry & Deadline Sweeps:** Daily scheduler sweep flagging agreements approaching expiration (configurable warning window, default 90 days) and transitioning expired agreements while archiving active programs.
3. **Multi-Stage Student Exchange Workflows:** Departmental review, international office review, partner nominations, and partner admission recording with automated academic prerequisite checks (CGPA and minimum credits).
4. **Outbound Risk & Pre-Departure Verification:** Structured safety compliance (passports, visas, emergency medical insurance, travel briefings, and consular registrations) required prior to departure.
5. **Inbound Exchange Scholar Onboarding:** Management of incoming international scholars from home university nomination through visa approvals, campus arrival, and mandatory orientation check-in.
6. **Faculty & Visiting Scholar Mobility:** Dual-level administrative approvals (Department Head / HOD followed by Vice President / Executive) for visiting professorships, research sabbaticals, and guest lectures.
7. **Strictly Non-Automated Credit Transfer Governance:** Course equivalency catalogs maintained by academic departments, with student credit recognition governed strictly by Academic Council / Committee resolution reference—prohibiting error-prone automated credit conversions.
8. **Mobility Grants & Finance Ledger Integration:** Institutional travel subsidies and scholarships linked directly to enterprise finance disbursement vouchers, avoiding parallel ledgers.
9. **Administrative Bio-Data Safeguards:** Secure storage and verification of passports, visas, and health insurance with explicit compliance safeguards (no automated immigration advice).

---

## 2. Architectural Boundaries & Data Flow

```
+---------------------------------------------------------------------------------------------------------+
|                                        CAMPUSOS MODULAR MONOLITH                                        |
|                                                                                                         |
|  [ Academic Affairs ]      [ Student Portals ]      [ Faculty Portals ]      [ Finance & Accounting ]   |
|            |                        |                        |                          |               |
|            v                        v                        v                          v               |
|  +---------------------------------------------------------------------------------------------------+  |
|  |                    ENTERPRISE INTERNATIONAL RELATIONS & MOBILITY DOMAIN                           |  |
|  |                                                                                                   |  |
|  |  +---------------------------+   +---------------------------+   +-----------------------------+  |  |
|  |  |  Partner Registry & MoUs  |   |  Exchange Programs & Caps |   |  Global Mobility Telemetry  |  |  |
|  |  |  - Active/Expiring MoUs   |   |  - Fall/Spring Cycles     |   |  - Reciprocity Ratios       |  |  |
|  |  |  - Scope Amendments       |   |  - CGPA/Credit Quotas     |   |  - Country Breakdowns       |  |  |
|  |  +---------------------------+   +---------------------------+   +-----------------------------+  |  |
|  |                                                |                                                  |  |
|  |            +-----------------------------------+-----------------------------------+              |  |
|  |            |                                                                       |              |  |
|  |            v                                                                       v              |  |
|  |  +-----------------------------------+                   +-----------------------------------+    |  |
|  |  |   STUDENT MOBILITY WORKFLOW       |                   |    INBOUND & FACULTY EXCHANGE     |    |  |
|  |  |  1. Student Application (SOP)     |                   |  - Inbound Scholar Onboarding     |    |  |
|  |  |  2. Eligibility Check (CGPA/Cred) |                   |  - Mandatory Orientation Check-in |    |  |
|  |  |  3. Department HOD Review         |                   |  - Dual HOD + VP Faculty Approval |    |  |
|  |  |  4. Intl Office Review            |                   +-----------------------------------+    |  |
|  |  |  5. Host Partner Nomination       |                                     |                      |  |
|  |  |  6. Partner Admission Decision    |                                     |                      |  |
|  |  |  7. Pre-Departure Safety Audit    |                                     |                      |  |
|  |  |  8. Active Overseas Mobility      |                                     |                      |  |
|  |  +-----------------------------------+                                     |                      |  |
|  |                    |                                                       |                      |  |
|  |                    v                                                       v                      |  |
|  |  +---------------------------------------------------------------------------------------------+  |  |
|  |  |                       GOVERNED CREDIT & FINANCIAL AUDIT BOUNDARY                            |  |  |
|  |  |                                                                                             |  |  |
|  |  |  - Course Equivalency Catalog (Dept Approved)                                              |  |  |
|  |  |  - Credit Transfer: STRICTLY Academic Council Review Ref (Non-Automated)                    |  |  |
|  |  |  - Travel Grants & Scholarships: Linked directly to Enterprise Finance Disbursement Vouchers|  |  |
|  |  |  - Passport / Visa Reference: Administrative records ONLY (Zero Automated Immigration Advice)|  |
|  |  +---------------------------------------------------------------------------------------------+  |  |
|  +---------------------------------------------------------------------------------------------------+  |
+---------------------------------------------------------------------------------------------------------+
```

---

## 3. Database Models & Schema Topology

All models are isolated by `tenant_id` and maintain strict referential integrity with canonical users, students, departments, and programs:

| Model Class | Table Name | Purpose & Cardinality |
| :--- | :--- | :--- |
| `InternationalPartner` | `ir_partners` | Global institution registry (Name, ISO country code, website, contact details). |
| `InstitutionalAgreement` | `ir_agreements` | MoUs, Student Exchange Accords, and Dual-Degree treaties with renewal warning windows. |
| `AgreementAmendment` | `ir_agreement_amendments` | Immutable audit log of scope extensions, term adjustments, and additions. |
| `MobilityProgram` | `ir_mobility_programs` | Specific exchange opportunities, semester terms, seats quota, and eligibility rules. |
| `MobilityApplication` | `ir_applications` | Student mobility dossiers, SOPs, course proposals, and eligibility validation. |
| `ApplicationReviewHistory` | `ir_application_reviews` | Multi-stage review audit trail (Department, International Office, Dean). |
| `InboundStudentProfile` | `ir_inbound_students` | Incoming international students, visa references, and mandatory orientation check-in. |
| `FacultyMobilityRecord` | `ir_faculty_mobilities` | Visiting professors and outbound fellowships requiring dual HOD and VP approvals. |
| `CourseEquivalencyMapping` | `ir_course_equivalencies` | Departmental mapping of external course syllabi to internal degree requirements. |
| `CreditTransferRequest` | `ir_credit_transfers` | Formal external credit transfers certified by Academic Council resolution references. |
| `MobilityDocument` | `ir_documents` | Verification tracking for passports, visas, health insurance, and transcripts. |
| `MobilityScholarship` | `ir_scholarships` | Institutional and consortium travel grant schemes and quotas. |
| `MobilityFundingRequest` | `ir_funding_requests` | Student funding requests linked to enterprise finance disbursement vouchers. |
| `InternationalPolicyConfig` | `ir_policy_configs` | Tenant-level operational parameters (warning days, approval gates, orientation rules). |

---

## 4. Operational Workflows & Governance Guarantees

### 4.1 MoU Lifecycle & Proactive Renewal Sweep
1. **Creation & Status:** Agreements begin in `DRAFT` or `ACTIVE` with `effective_start_date`, `effective_end_date`, and `renewal_warning_days` (default 90).
2. **Scheduler Execution:** Scheduled background task `sweep_international_agreements_and_deadlines_task` evaluates all agreements across tenants daily:
   - Agreements within `renewal_warning_days` transition to `EXPIRING` with domain event `INTERNATIONAL_AGREEMENT_EXPIRING` dispatched.
   - Agreements past `effective_end_date` transition to `EXPIRED` with domain event `INTERNATIONAL_AGREEMENT_EXPIRED` dispatched.
3. **Audit Amendments:** Any extension or scope modification must be registered as an `AgreementAmendment` preserving original legal parameters.

### 4.2 Multi-Stage Student Mobility Application Workflow
1. **Prerequisite Check:** Upon submission, the service verifies student CGPA and completed credits against program requirements. If below threshold, application is flagged as failed.
2. **Department Review:** Academic HOD reviews proposed course syllabus and submits `APPROVE`, `REJECT`, `RETURN`, or `ESCALATE`.
3. **International Office Review:** Verifies capacity, institutional reciprocity balance, and conducts formal nomination.
4. **Partner Nomination & Admission:** Official dossier sent to partner university. Host partner decision (`ACCEPTED` or `REJECTED`) is recorded.
5. **Pre-Departure Clearance:** Mandatory 5-point checklist verified:
   - Flight ticket booked & confirmed
   - Host institution accommodation finalized
   - Comprehensive international health & evacuation insurance verified
   - Pre-departure cultural & safety briefing attended
   - Consular registration completed
6. **Active Mobility:** Upon clearance, status shifts to `ACTIVE_MOBILITY`.

### 4.3 Strictly Non-Automated Credit Recognition Governance
1. **Equivalency Prerequisite:** Foreign courses must be pre-evaluated and mapped to department course units via `CourseEquivalencyMapping`.
2. **Official Transcript Submission:** Student submits sealed transcript and host syllabus documentation.
3. **Academic Council Ratification:** System enforces that credit transfers can **never be automated**. Every `CreditTransferRequest` must be manually reviewed and approved with a recorded `academic_council_approval_reference` (e.g., `AC-RES-2026-089`).

### 4.4 Financial Integration & Mobility Scholarships
1. **Direct Disbursement Vouchers:** When a student mobility grant or travel subsidy is approved, the system generates or links to a canonical `finance_disbursement_ref` (e.g., `FIN-DISB-2026-904`).
2. **Single Source of Truth:** No parallel ledger is maintained. The transaction links directly to the enterprise accounts payable and disbursement ledger.

### 4.5 Inbound Scholar Onboarding & Orientation Check-in
1. **Nomination & Admission:** Host department allocates faculty mentor and campus privileges.
2. **Mandatory Check-in:** Upon campus arrival, international office completes orientation verification (visa validation, accommodation check-in, campus smart-card issuance).
3. **Privilege Activation:** Status updates to `ORIENTATION_COMPLETED`, unlocking library, computing, and laboratory access.

---

## 5. Security & Multi-Tenant Isolation

1. **Tenant Isolation:** Every database query filters by `tenant_id` from the authenticated JWT session.
2. **Permission Guardrails:** Granular permissions defined in `apps/api/app/core/permissions.py`:
   - `INTERNATIONAL_PARTNER_READ` / `WRITE`
   - `INTERNATIONAL_AGREEMENT_READ` / `WRITE`
   - `MOBILITY_PROGRAM_READ` / `WRITE`
   - `MOBILITY_APPLICATION_READ` / `WRITE`
   - `MOBILITY_APPLICATION_REVIEW`
   - `MOBILITY_NOMINATION_MANAGE`
   - `INBOUND_EXCHANGE_MANAGE`
   - `FACULTY_MOBILITY_READ` / `WRITE` / `APPROVE`
   - `COURSE_EQUIVALENCY_MANAGE`
   - `CREDIT_TRANSFER_COUNCIL_APPROVE`
   - `MOBILITY_DOCUMENT_VERIFY`
   - `MOBILITY_SCHOLARSHIP_MANAGE`
   - `INTERNATIONAL_POLICY_CONFIG`
3. **Administrative Safeguards:**
   - Passport and visa reference numbers are strictly administrative audit references.
   - The platform strictly disclaims automated immigration advice or legal visa counseling.

---

## 6. Verification & Test Evidence

### Backend Test Suite (`apps/api/tests/test_enterprise_international_relations.py`)
- **Framework:** Pytest with Async SQLite in-memory test runner.
- **Pass Rate:** **13/13 tests passed (100%) in 7.88s**.
- **Coverage Highlights:**
  1. Complete partner registry and MoU lifecycle with agreement amendments.
  2. Scheduled MoU expiry warning sweep and deadline processor.
  3. Mobility program creation with academic department and seat constraints.
  4. Student application submission and eligibility enforcement (CGPA/credits).
  5. Multi-stage review workflow (Department approval, nomination, partner acceptance).
  6. Pre-departure checklist completion and active mobility transition.
  7. Inbound student registration, hostel allocation, and orientation check-in.
  8. Faculty mobility workflow with dual HOD and VP approvals.
  9. Course equivalency evaluation and departmental activation.
  10. Academic Council governed credit transfer approval with resolution reference.
  11. Mobility scholarship creation and travel funding request disbursement.
  12. Compliance document upload and administrative verification audit.
  13. Dashboard metrics telemetry aggregation and reciprocity calculation.

### Frontend Test Suite (`apps/web/src/__tests__/international-module.test.ts`)
- **Framework:** Direct Node/TSX execution harness.
- **Pass Rate:** **50/50 tests passed (100%)**.
- **Typecheck:** `tsc --noEmit` (**0 errors, 100% clean**).
- **Coverage Highlights:**
  1. Dashboard metrics telemetry (partners, agreements, inbound/outbound counts).
  2. Institutional policy configuration and runtime policy parameter updates.
  3. Partner registry directory, search filters, and new institution creation.
  4. Institutional agreements, active/expiring statuses, and scope amendments.
  5. Mobility programs catalog, academic terms, and quota constraints.
  6. Application submission, SOP handling, and departmental review transitions.
  7. Partner nominations and official host university acceptance logging.
  8. Outbound pre-departure safety checklist verification.
  9. Inbound scholar directory and mandatory orientation check-in.
  10. Faculty sabbatical fellowship submission and dual HOD/VP approvals.
  11. Course equivalency syllabus matching and degree articulation.
  12. Committee credit transfer approval backed by Academic Council resolutions.
  13. Travel grants and scholarships linked to finance disbursement vouchers.
  14. Compliance document auditing and bio-data administrative safeguards.
  15. Data integrity verification confirming canonical user and student identity models.

---

## 7. Operational Checklist & Runbook

| Frequency | Task | Responsible Team | Verification Command / Metric |
| :--- | :--- | :--- | :--- |
| **Daily** | MoU Renewal & Deadline Sweep | Background Scheduler | `sweep_international_agreements_and_deadlines_task` |
| **Weekly** | Application Review Queue Clearance | Department HODs & Intl Office | `/app/international/applications/review` queue count |
| **Weekly** | Document Verification Backlog Audit | International Relations Officers | `/app/international/documents` pending list |
| **Monthly** | Exchange Reciprocity Ratio Audit | Dean of International Affairs | `/app/international/analytics` reciprocity ratio |
| **Semester** | Academic Council Credit Ratification | Academic Council Committee | `/app/international/credit-transfer` resolution audit |
| **Semester** | Finance Ledger Grant Reconciliation | Finance & Accounting | `/app/international/scholarships` disbursement voucher log |
