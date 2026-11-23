# Enterprise Institutional Knowledge Base, Policy Library & Controlled Knowledge Management Runbook

## Executive Summary

The **CampusOS Enterprise Institutional Knowledge Base & Policy Library** (Step 42) provides universities, colleges, and higher-education multi-campus consortia with a robust, controlled knowledge governance engine. It ensures that every institutional policy, standard operating procedure (SOP), academic regulation, circular, manual, and handbook is authored, reviewed, approved, published, versioned, attested to, and retired under rigorous regulatory controls.

---

## 1. Architecture & Core Governance Principles

### 1.1 The Golden Rules of Institutional Knowledge
1. **Clear Attribution & Ownership**: Every knowledge item has a designated primary owner, responsible reviewer, and institutional scope.
2. **Strict Separation of Duties**: The author or last modifying editor of a policy/SOP is strictly prohibited from approving their own submission. An independent reviewer or authorized compliance officer must approve each stage.
3. **Optimistic Concurrency Control**: All draft updates enforce `lock_version` matching to guarantee that concurrent edits by multiple committee members do not overwrite each other.
4. **Immutable Published Versions**: Once published, a version snapshot is permanently immutable. Minor updates, section modifications, or overhauls require drafting and publishing a new SemVer version (`PATCH`, `MINOR`, or `MAJOR`).
5. **Exact-Version Attestations**: Policy acknowledgements are cryptographically bound to the specific version number active at the time of user attestation, preventing compliance disputes when policies evolve.
6. **Directed Relationship Graph with Cycle Prevention**: Relationships (`SUPERSEDES`, `IMPLEMENTS`, `REFERENCES`, `DEPENDS_ON`, `ANNOUNCES`) are validated via Depth-First Search (DFS) to prevent cyclic circular dependencies.
7. **Step 41 Records Lifecycle Integration**: Superseded, retired, or archived policies integrate directly with the Step 41 Records Lifecycle & Retention engine, adhering to UGC/AICTE statutory retention schedules.

```
                           +---------------------------+
                           |   DRAFT AUTHORING         |
                           |   - Lock Version Control  |
                           |   - Markdown Content      |
                           +-------------+-------------+
                                         |
                                         | Submit for Review
                                         v
                           +---------------------------+
                           |   MULTI-STAGE REVIEW      |
                           |   - Separation of Duties  |
                           |   - Committee Stages      |
                           +-------------+-------------+
                                         |
                                         | Approval
                                         v
                           +---------------------------+
                           |   APPROVED STATE          |
                           |   - Cleared by Reviewer   |
                           +-------------+-------------+
                                         |
                                         | Formal Release
                                         v
                           +---------------------------+
                           |   PUBLISHED SNAPSHOT      | <-------+
                           |   - Immutable Version     |         |
                           |   - SemVer Numbering      |         |
                           +-------------+-------------+         |
                                         |                       |
                     +-------------------+-------------------+   | Superseded By
                     |                                       |   | New Policy
                     v                                       v   |
          +-----------------------+              +---------------+--+----+
          | MANDATORY ATTESTATION |              | SUPERSEDED / RETIRED  |
          | - Exact-version bind  |              | - Records Retention   |
          | - IP & Time Logged    |              | - Step 41 Disposition |
          +-----------------------+              +-----------------------+
```

---

## 2. Statutory Knowledge Classification Authorities

CampusOS ships with 14 pre-seeded statutory classification categories adhering to National Education Policy (NEP), University Grants Commission (UGC), All India Council for Technical Education (AICTE), and international accreditation benchmarks:

| Category Code | Category Name | Default Review Cycle | Requires Approval | Requires Attestation |
| :--- | :--- | :--- | :--- | :--- |
| `ACADEMIC_REGULATION` | Academic Regulations & Ordinances | 12 Months | Yes | Yes |
| `EXAMINATION_SOP` | Examination & Evaluation SOPs | 12 Months | Yes | Yes |
| `ADMISSION_POLICY` | Student Admissions & Enrollment Policy | 12 Months | Yes | No |
| `STUDENT_CONDUCT` | Student Conduct, Disciplinary & Anti-Ragging | 12 Months | Yes | Yes |
| `FACULTY_GOVERNANCE` | Faculty Governance, Tenure & Ethics | 24 Months | Yes | Yes |
| `HR_COMPENSATION` | HR, Staffing, Leave & Compensation | 12 Months | Yes | No |
| `FINANCE_PROCUREMENT` | Finance, Grants, Audits & Procurement | 12 Months | Yes | No |
| `RESEARCH_ETHICS` | Research Ethics, Grants & Intellectual Property | 24 Months | Yes | Yes |
| `CAMPUS_SAFETY` | Campus Safety, Health & Crisis Response | 12 Months | Yes | Yes |
| `IT_CYBERSECURITY` | IT, Cybersecurity & Acceptable Use Policy | 12 Months | Yes | Yes |
| `CAMPUS_OPERATIONS` | Campus Facilities & Operational Manuals | 24 Months | Yes | No |
| `CIRCULARS_DIRECTIVES` | Executive Circulars & Statutory Directives | 6 Months | Yes | No |
| `ACCREDITATION_QA` | Accreditation & Internal Quality Assurance (IQAC) | 12 Months | Yes | No |
| `STUDENT_HANDBOOK` | Student, Scholar & Resident Handbooks | 12 Months | Yes | No |

---

## 3. Policy & SOP Lifecycle State Machine

| State | Allowed Transitions | Description |
| :--- | :--- | :--- |
| `DRAFT` | `SUBMITTED`, `RETIRED` | Author editing mode. Optimistic locking enforced via `lock_version`. |
| `SUBMITTED` | `IN_REVIEW`, `DRAFT` | Item submitted to editorial queue; awaits stage reviewer assignment. |
| `IN_REVIEW` | `APPROVED`, `CHANGES_REQUESTED`, `REJECTED` | Active stage evaluation. Author cannot approve (Separation of Duties). |
| `CHANGES_REQUESTED` | `DRAFT` | Reviewer requested adjustments; returned to author with critique notes. |
| `APPROVED` | `PUBLISHED`, `SCHEDULED` | Clearance granted. Ready for formal versioned release. |
| `SCHEDULED` | `PUBLISHED`, `RETIRED` | Approved for publication on a designated future date. |
| `PUBLISHED` | `SUPERSEDED`, `RETIRED` | Active institutional document. Immutable snapshot generated. |
| `SUPERSEDED` | `ARCHIVED` | Replaced by a successor policy version or replacement item. |
| `RETIRED` | `ARCHIVED` | Withdrawn from institutional operation; retained for archival audit. |

---

## 4. Operational Runbooks

### Runbook 1: Authoring & Drafting a New Policy or SOP
1. Navigate to **Knowledge & Policies** console (`/app/knowledge`) -> **Policy & SOP Editor** tab.
2. Enter the **Document Code** (e.g., `POL-ACAD-2026-001`), **Title**, **Category**, and **Executive Summary**.
3. Select the **Visibility Scope**:
   - `INSTITUTION`: All faculty, staff, and students across all campuses.
   - `CAMPUS`: Limited to a specific regional campus.
   - `DEPARTMENT`: Limited to faculty/students within a specified academic department.
   - `ROLE`: Restricted to specific user roles (e.g., `FACULTY`, `WARDEN`).
   - `RESTRICTED`: Accessible strictly to institutional leadership and designated officers.
4. Compose the policy body in GitHub Flavored Markdown.
5. Click **Validate & Preview** to test AST HTML sanitization, word count, and heading structure.
6. Click **Create Knowledge Item**. The item is saved in `DRAFT` state with `lock_version = 1`.

### Runbook 2: Multi-Stage Editorial Review (Enforcing Separation of Duties)
1. In the **Knowledge Library**, locate the draft item and click **Submit**.
2. Authorized reviewers (e.g., Dean of Academics, Registrar, IQAC Coordinator) navigate to the **Review & Approval Queue** tab.
3. The queue displays the document, submission notes, and author identity:
   - If the logged-in user is the author or last editor, the action button is disabled with the warning:  
     `⚠️ Separation of Duties Guard: You are registered as the author of this item. Approval must be performed by another authorized officer.`
4. An independent reviewer selects **Conduct Review**:
   - Decision: `APPROVED`, `CHANGES_REQUESTED`, or `REJECTED`.
   - Records compulsory editorial comments and clicks **Confirm Decision**.
5. Once all stages are approved, the document transitions to `APPROVED`.

### Runbook 3: Publishing an Immutable Version Snapshot
1. On the **Review & Approval Queue** tab under **Approved Items Ready for Formal Publication**, click **Publish Snapshot**.
2. Select the SemVer bump type:
   - `PATCH`: Editorial typo fixes or minor clause clarifications.
   - `MINOR`: New section additions or updated procedural workflows.
   - `MAJOR`: Comprehensive policy repeal, restructuring, or overhaul.
3. Enter official release notes and click **Publish Snapshot**.
4. The system:
   - Creates an immutable record in `knowledge_item_versions`.
   - Records the snapshot hash, author ID, reviewer ID, publisher ID, and timestamps.
   - If the item was configured with mandatory acknowledgement, generates compliance requirement tracking records.
   - If superseding a previous document, marks the predecessor as `SUPERSEDED` and establishes the directed relationship.

### Runbook 4: Mandatory Policy Attestation by Staff & Students
1. For policies flagged with `requires_acknowledgement = true`, members of the target audience see the **Attest** badge.
2. Clicking **Attest to This Policy** launches the confirmation modal.
3. The user reviews the exact version text and checks:
   - `"I confirm that I have read, understood, and agree to abide by the provisions of this institutional document."`
4. Clicking **Submit Attestation** registers:
   - `item_id` and exact `version_number`
   - `user_id`
   - Client IP address and User Agent
   - ISO-8601 UTC timestamp
5. Institutional administrators track live compliance rates on the **Mandatory Attestations & Compliance** tab.

### Runbook 5: Cross-Referencing & Cycle Prevention
1. Open the **Governance & Relationships** tab and click **+ Link Knowledge Items**.
2. Select the **Source Document**, **Relationship Type** (`SUPERSEDES`, `IMPLEMENTS`, `REFERENCES`, `DEPENDS_ON`, `ANNOUNCES`), and **Target Document**.
3. The system executes a graph traversal (DFS) across all relationships:
   - If establishing the link would cause a cyclic dependency (e.g., A -> B -> C -> A), the transaction is aborted with `400 Bad Request: KnowledgeCycleDetectedException`.

### Runbook 6: Scheduled Review Sweeps
1. Policies approaching their `review_by_date` or statutory review expiration trigger automated notifications.
2. The background sweep task runs automatically on the schedule configured in `scheduler.py` (daily at 02:30 UTC), or manually via:
   - Web Console: **Trigger Review Sweep** button.
   - API: `POST /api/v1/knowledge/scheduler/sweep`.
3. Overdue items are flagged, notifications dispatched to responsible reviewers, and audit entries recorded.

---

## 5. Security & Access Control Matrix

| Role | Browse Published | Author Drafts | Edit Drafts | Review & Approve | Publish Snapshots | Manage Categories & Sweeps | Attest / Acknowledge |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `SUPER_ADMIN` | Yes | Yes | Yes | Yes* | Yes | Yes | Yes |
| `ADMIN` | Yes | Yes | Yes | Yes* | Yes | Yes | Yes |
| `PRINCIPAL` / `DEAN` | Yes | Yes | Yes | Yes* | Yes | Yes | Yes |
| `HOD` | Yes (Dept) | Yes | Yes | Yes* | No | No | Yes |
| `FACULTY` | Yes (Public/Faculty) | Yes (Dept) | Own Drafts | No | No | No | Yes |
| `STAFF` | Yes (Public/Staff) | No | No | No | No | No | Yes |
| `STUDENT` | Yes (Public/Student)| No | No | No | No | No | Yes |

*\*Subject to Separation of Duties: Users cannot approve items they authored.*

---

## 6. Audit Logging & Verification

Every action in the Knowledge Base engine records a tamper-evident entry in the unified audit log:

- `KNOWLEDGE_ITEM_CREATED`: Document initialized.
- `KNOWLEDGE_DRAFT_UPDATED`: Content modified with lock version check.
- `KNOWLEDGE_SUBMITTED_FOR_REVIEW`: Queued for editorial decision.
- `KNOWLEDGE_REVIEW_DECISION`: Stage evaluation with reviewer comments.
- `KNOWLEDGE_PUBLISHED`: Immutable snapshot released.
- `KNOWLEDGE_SUPERSEDED`: Predecessor superseded by successor.
- `KNOWLEDGE_ATTESTATION_RECORDED`: User exact-version acknowledgement.
- `KNOWLEDGE_RELATIONSHIP_CREATED`: Directed link established with cycle check.
- `KNOWLEDGE_REVIEW_SWEEP_EXECUTED`: Scheduled expiration sweep executed.

---

## 7. Emergency Troubleshooting

### Issue 1: `KnowledgeOptimisticLockException (409 Conflict)`
- **Symptom**: Author receives "The knowledge item was modified by another user or session."
- **Root Cause**: The client submitted a draft update with a stale `lock_version`.
- **Resolution**: Reload the latest draft from the server to inspect the latest content, reconcile modifications, and submit with the updated `lock_version`.

### Issue 2: `KnowledgeSeparationOfDutiesException (403 Forbidden)`
- **Symptom**: Reviewer receives "Author cannot approve their own knowledge item."
- **Root Cause**: Separation of duties governance prohibits self-approval.
- **Resolution**: Have an independent designated reviewer, Dean, or Principal sign off on the stage.

### Issue 3: `KnowledgeCycleDetectedException (400 Bad Request)`
- **Symptom**: Establishing a directed link fails with cyclic graph warning.
- **Root Cause**: The proposed link would create an infinite circular dependency loop.
- **Resolution**: Inspect the existing relationship chain for the items in the Governance explorer and remove the redundant conflicting reference.
