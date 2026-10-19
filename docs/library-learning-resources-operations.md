# Enterprise Library, Learning Resources & Knowledge Access Management Runbook

## Executive Summary

The **CampusOS Enterprise Library, Learning Resources & Knowledge Access Management Engine** (Step 45) provides higher education institutions, autonomous universities, research institutes, and multi-campus colleges with a carrier-grade, multi-tenant academic library automation system. It orchestrates the full spectrum of institutional learning resource operations: multi-branch administration, cataloging adhering to Anglo-American Cataloguing Rules / Resource Description and Access (AACR2/RDA), barcode/RFID physical copy accessioning, patron membership management with category-specific borrowing limits, concurrent-safe circulation desk operations, automated FIFO and priority hold queues, dynamic fine computation with audited waiver controls, department-sponsored acquisition pipelines, serial/periodical subscription monitoring, secure expiring digital access tokens, and annual physical stock verification audits with discrepancy reconciliation.

---

## 1. Architecture & Core Governance Principles

### 1.1 The Ten Golden Rules of Enterprise Library Governance
1. **Absolute Multi-Tenant Boundary Isolation**: Every library branch, catalog record, physical copy, loan, reservation, fine, acquisition, subscription, and stock audit is partitioned strictly by `tenant_id`. Cross-tenant queries are blocked at both database and service layers.
2. **Deterministic Lending Policy Precedence**: Lending limits (maximum concurrent loans, loan duration in days, grace periods, daily fine rates, and maximum renewal counts) are resolved via a strict policy hierarchy: (Branch + Member Category + Resource Type) > (Global Institution + Member Category + Resource Type) > Default Category Baseline.
3. **Concurrency-Safe Circulation Checkout**: Physical copies must be locked during checkout using database row-level locking (`with_for_update()`) to prevent simultaneous issuance of the same accession number to two concurrent patrons.
4. **Zero-Eligibility Lending Restriction**: Patrons with accumulated unpaid fines exceeding institutional fine ceilings or with overdue loans exceeding maximum allowable thresholds are immediately blocked from borrowing additional physical resources until reconciled.
5. **Automated Return Allocation to Waitlist Queues**: When an issued physical copy is checked in, the circulation engine automatically checks for active hold reservations on that catalog title. If a reservation is pending, the copy is immediately transitioned to `ON_HOLD`, allocated to the highest-priority patron, and placed in a 48-hour pickup window.
6. **Immutable Fine Ledger & Authorized Waiver Auditing**: Overdue and damage fines are immutable historical financial records. Partial or full waivers cannot be granted anonymously; every waiver requires an authorized staff user ID, a statutory justification note, and generates a structured audit log entry.
7. **Departmental Acquisition Separation of Duties**: Faculty members who initiate resource acquisition purchase requests cannot conduct the administrative review or approve their own purchase requests. An authorized librarian or dean must review and approve before procurement orders are issued.
8. **Automatic Inventory Accessioning upon Receipt**: When ordered acquisition items are physically received by the receiving branch, the library engine automatically creates physical copy records with sequential accession numbers, sets their circulation status to `AVAILABLE`, and records the acquisition as `RECEIVED`.
9. **Secure Expiring Digital Access Tokens**: Access to digital textbooks, copyrighted journals, and restricted institutional databases is governed by time-limited (2-hour) cryptographic download tokens. Every digital access event is logged with patron ID, IP address, and timestamp.
10. **Statutory Annual Stock Verification & Reconciliation**: Annual stock verification audits enforce strict discrepancy tracking between expected catalog copies and observed physical scans. Closing an audit requires sign-off from an authorized senior librarian, producing a reconcilable report of verified, missing, and misplaced assets.

---

## 2. System Workflow Architecture

```
                            +-----------------------------------+
                            |     INSTITUTIONAL LIBRARY BRANCH  |
                            |   - Central LRC, Engg, Medical    |
                            |   - Operating Hours & Floor Plans |
                            +-----------------+-----------------+
                                              |
                                              | Configures
                                              v
                            +-----------------------------------+
                            |       LENDING & CIRCULATION       |
                            |       HIERARCHICAL POLICIES       |
                            |   - Max Books, Days, Fine Rates   |
                            +-----------------+-----------------+
                                              |
                                              | Governs
                                              v
                            +-----------------------------------+
                            |       BIBLIOGRAPHIC CATALOG       |
                            |   - Books, Journals, E-Resources  |
                            |   - Dewey / LC Classification     |
                            +-----------------+-----------------+
                                              |
                        +---------------------+---------------------+
                        |                                           |
                        v                                           v
         +-----------------------------+             +-----------------------------+
         |     PHYSICAL INVENTORY      |             |    DIGITAL LEARNING ACCESS  |
         |  - Accession Number / RFID  |             |  - E-Books & Open Access    |
         |  - Shelf / Rack Location    |             |  - Expiring Auth Tokens     |
         |  - Mint, Good, Damaged      |             |  - Access Audit Logging     |
         +--------------+--------------+             +-----------------------------+
                        |
                        | Circulates
                        v
         +-----------------------------+
         |      CIRCULATION DESK       |
         |  - Row-Locked Checkout      |
         |  - Real-Time Due Dates      |
         |  - Renewal Quota Enforced   |
         +--------------+--------------+
                        |
           +------------+------------+
           |                         |
           v                         v
+---------------------+   +---------------------+
|   CHECK-IN RETURN   |   |   HOLD QUEUE & WAIT |
| - Damage Assessment |   | - Priority Weight   |
| - Daily Fine Calc   |   | - 48h Pickup Window |
| - Allocate to Hold  |   | - Auto Allocation   |
+----------+----------+   +---------------------+
           |
           v
+---------------------+
|    FINES & LEDGER   |
| - Unpaid / Paid     |
| - Authorized Waiver |
| - Finance Sync      |
+---------------------+
```

---

## 3. Database Schema & Entities

The library subsystem is composed of 13 SQLAlchemy models in `apps/api/app/models/library.py`:

| Model Name | Table Name | Purpose & Lifecycle |
|:---|:---|:---|
| `LibraryBranch` | `library_branches` | Campus library facilities, learning resource centres, departmental stacks, and operating schedules. |
| `LibraryLendingPolicy` | `library_lending_policies` | Matrix rules defining max simultaneous loans, loan period, grace periods, daily fine amounts, and max renewals. |
| `LibraryCatalogItem` | `library_catalog_items` | AACR2/RDA bibliographic metadata records (title, authors, ISBN/ISSN, Dewey decimal class, LC call number). |
| `LibraryPhysicalCopy` | `library_physical_copies` | Individual inventory copies with unique accession numbers, barcodes, RFID tags, condition grades, and circulation states. |
| `LibraryMemberProfile` | `library_member_profiles` | Borrower cards for students, faculty, research scholars, and external alumni with borrowing allowances and suspension flags. |
| `LibraryCirculationLoan` | `library_circulation_loans` | Active and historical checkout transactions with precise due dates, check-in timestamps, renewal counts, and returning branches. |
| `LibraryReservation` | `library_reservations` | Priority waitlist queues for checked-out or reserved items with automated allocation upon copy check-in. |
| `LibraryFineRecord` | `library_fine_records` | Penalty assessments for overdue loans, lost materials, or physical damages, with support for authorized waivers. |
| `LibraryAcquisitionRequest` | `library_acquisition_requests` | Purchase suggestions, departmental endorsements, procurement statuses, and receiving/accessioning tracking. |
| `LibrarySubscription` | `library_subscriptions` | Periodicals, journals, magazines, and e-resource package licenses with vendor contacts, renewal deadlines, and portal URLs. |
| `LibraryDigitalResourceAccess`| `library_digital_resource_access` | Audit log recording digital textbook, article, and dataset downloads with expiring cryptographic tokens. |
| `LibraryInventoryAudit` | `library_inventory_audits` | Physical stock verification campaigns tracking expected vs scanned counts, missing copies, and reconciliations. |
| `LibraryInventoryAuditItem` | `library_inventory_audit_items` | Individual accession scan results during stock audits (VERIFIED, MISPLACED, DAMAGED, SURPLUS). |

---

## 4. Standard Operating Procedures (SOPs)

### SOP 01: Branch & Policy Provisioning
- **Purpose**: Establish physical learning centres and borrowing rules.
- **Role Required**: `library.branches.manage`
- **Steps**:
  1. Navigate to `/app/library` > **Overview** > **+ Add Branch**.
  2. Input unique `branch_code`, facility name, campus ID, building, and operating hours.
  3. Configure lending policy rules under `/api/v1/library/policies` for each member category (`STUDENT`, `FACULTY`, `RESEARCH_SCHOLAR`, `STAFF`) and resource type (`BOOK`, `REFERENCE_ONLY`, `JOURNAL_BOUND`, `RESERVE_COLLECTION`).
  4. Ensure `REFERENCE_ONLY` materials have `max_loan_duration_days = 0` to prevent removal from library reading rooms.

### SOP 02: Bibliographic OPAC Cataloging
- **Purpose**: Index physical books, e-books, multimedia, and bound periodicals.
- **Role Required**: `library.catalog.manage`
- **Steps**:
  1. Navigate to `/app/library` > **OPAC Catalog** > **Add Catalog Title**.
  2. Enter bibliographic details: Title, Authors, Publisher, Publication Year, Language, and Subject Classification.
  3. Provide standard identifiers: ISBN-10/13 or ISSN, Dewey Decimal classification, and Library of Congress call numbers.
  4. If adding a digital asset, toggle **Enable Digital E-Resource Access** and provide the secure storage URI.

### SOP 03: Barcode & RFID Physical Accessioning
- **Purpose**: Register physical book copies in library stacks.
- **Role Required**: `library.copies.manage`
- **Steps**:
  1. From the catalog title detail or **Physical Inventory** tab, click **Register Physical Copy**.
  2. Specify the unique accession number (e.g., `ACC-2026-0042`) or scan the physical barcode/RFID sticker.
  3. Select the owning branch, specify stack and shelf location, and record the initial condition (`NEW` or `GOOD`).

### SOP 04: Circulation Desk (Check-Out, Return & Renewal)
- **Purpose**: Manage day-to-day borrowing, renewals, and resource check-ins.
- **Role Required**: `library.circulation.issue` / `library.circulation.return`
- **Steps**:
  1. **Check Out**:
     - Click **Circulation Checkout** on the header or **Circulation Desk** tab.
     - Scan the physical copy accession number and patron membership card.
     - The engine validates borrowing limits, overdue books, and fine thresholds. If eligible, it locks the copy row and records the loan with an automated due date based on the lending policy.
  2. **Renewal**:
     - In the loans table, locate the active loan and click **Renew**.
     - Renewal is permitted only if current renewal count is below policy limit and no hold reservation exists on the catalog title.
  3. **Check In / Return**:
     - Click **Check In** on the loan record.
     - Inspect physical book condition. If damaged, input the assessed damage fine.
     - If overdue, the system automatically computes daily penalty fines and appends a fine record to the patron ledger.
     - If reservations exist, the book status becomes `ON_HOLD` and the highest-priority patron is notified with a 48-hour pickup deadline.

### SOP 05: Hold Queue Management
- **Purpose**: Manage waitlists for high-demand course textbooks.
- **Role Required**: `library.circulation.reserve`
- **Steps**:
  1. Patrons can place holds via OPAC or library desk.
  2. The system inserts the patron into the queue, ranking by priority level (e.g., Research Scholars > Undergrads) and request timestamp.
  3. When an allocated copy is not collected within the pickup window, the scheduled compliance sweep marks the reservation `EXPIRED` and re-allocates the copy to the next waiting patron.

### SOP 06: Fine Assessment & Audited Waiver
- **Purpose**: Reconcile student/faculty overdue charges and lost item penalties.
- **Role Required**: `library.fines.manage` (assess) / `library.fines.waive` (waive)
- **Steps**:
  1. View patron balances under **Fines & Waivers**.
  2. To waive a fine, an authorized supervisor clicks **Waive Fine**.
  3. Enter the waiver amount and official statutory justification (e.g., Medical hospitalization pardon).
  4. The waiver is logged in the immutable audit log and the patron's accumulated balance is updated.

### SOP 07: Annual Physical Stock Verification & Stock Audits
- **Purpose**: Conduct physical stock taking and identify missing or misplaced volumes.
- **Role Required**: `library.audit.manage`
- **Steps**:
  1. Navigate to **Stock Audits** > **Initiate Stock Audit**.
  2. Select the branch and stacks to be audited. The system snapshots all expected physical copies.
  3. Stock auditors use barcode/RFID wands to scan items on the shelves via **Scan Accession**.
  4. Once scanning is complete, click **Reconcile Audit**. The system compiles:
     - `total_verified_copies`
     - `total_missing_copies`
     - `total_discrepant_copies`
  5. The library director reviews the reconciliation report and submits sign-off notes to close the audit.

---

## 5. Scheduled Background Jobs

The library module includes an automated compliance sweep task registered in `apps/api/app/scheduler.py`:

- **Job Name**: `sweep_library_deadlines_task`
- **Interval**: Runs every 60 minutes (or triggered on demand via `POST /api/v1/library/compliance/sweep`).
- **Operations Performed**:
  1. **Overdue Loan Fine Assessment**: Identifies active loans past their due date (taking grace period into account) and calculates daily overdue fines.
  2. **Hold Queue Expiration**: Finds allocated reservations whose pickup window (e.g., 48 hours) has lapsed, marks them `EXPIRED`, and triggers reallocation to the next queue position.
  3. **Subscription Renewal Reminders**: Flags journal and database subscriptions expiring within 30 days.

---

## 6. Security, Permissions & Access Control

| Permission Key | Permitted Roles | Functionality Covered |
|:---|:---|:---|
| `library.branches.manage` | `SUPER_ADMIN`, `LIBRARIAN` | Create/update branches, operating hours, compliance sweep. |
| `library.catalog.read` | `ALL_AUTHENTICATED` | Search OPAC, view bibliographic details, check branch availability. |
| `library.catalog.manage` | `LIBRARIAN`, `CATALOGER` | Create/edit catalog items, classify via Dewey/LC, manage digital links. |
| `library.copies.manage` | `LIBRARIAN`, `CIRCULATION_STAFF` | Accession physical copies, print barcode stickers, update condition. |
| `library.members.read` | `LIBRARIAN`, `STAFF` | Search patron directory, inspect borrowing history. |
| `library.members.manage` | `LIBRARIAN`, `REGISTRAR` | Enroll patrons, update category, suspend/restore borrowing rights. |
| `library.circulation.issue` | `CIRCULATION_STAFF`, `LIBRARIAN` | Check out physical books to patrons, renew loans. |
| `library.circulation.return`| `CIRCULATION_STAFF`, `LIBRARIAN` | Check in returned books, inspect damages, trigger hold queues. |
| `library.circulation.reserve`| `ALL_AUTHENTICATED` | Place hold requests on checked-out titles. |
| `library.fines.manage` | `LIBRARIAN`, `ACCOUNTS` | Assess fines, post fine invoices to campus finance module. |
| `library.fines.waive` | `HEAD_LIBRARIAN`, `DEAN` | Authorize partial or complete fee waivers with written justification. |
| `library.acquisitions.request`| `FACULTY`, `HOD`, `LIBRARIAN` | Submit book/resource acquisition purchase requests. |
| `library.acquisitions.manage` | `HEAD_LIBRARIAN`, `PURCHASING` | Review, approve/reject purchase requests, receive and auto-accession. |
| `library.subscriptions.manage`| `HEAD_LIBRARIAN` | Manage print journals, e-journal packages, and database licenses. |
| `library.digital.access` | `STUDENT`, `FACULTY`, `RESEARCHER`| Generate expiring tokens for copyright-protected digital books. |
| `library.audit.manage` | `LIBRARIAN`, `INTERNAL_AUDITOR` | Initiate stock audits, scan accessions, reconcile missing copies. |
| `library.analytics.read` | `SUPER_ADMIN`, `DEAN`, `LIBRARIAN` | Access circulation rate metrics, OPAC search trends, and audit summaries. |

---

## 7. Verification & Compliance Sign-Off

- **Automated Test Suite**: `apps/api/tests/test_enterprise_library_management.py` (15/15 passing).
- **Frontend Console**: `apps/web/src/app/app/library/page.tsx` (10-tab glassmorphic interface).
- **Multi-Tenant Guarantee**: Enforced by `tenant_id` database foreign keys and row-level tenant context resolution.
- **Statutory Audit Trail**: 16 dedicated audit event categories recording all administrative actions.
