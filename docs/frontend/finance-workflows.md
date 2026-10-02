# CampusOS — Finance Workflows & Lifecycle State Machines

This document details the end-to-end operational workflows for fee lifecycle governance, student fee assignment, invoicing, payment allocation, receipting, scholarship distribution, and refunds.

---

## 1. Fee Structure Governance Lifecycle

Fee structures undergo strict academic and financial governance before being applied to students.

```mermaid
stateDiagram-v2
    [*] --> DRAFT: Create in 6-Step Wizard
    DRAFT --> PENDING_APPROVAL: Submit for Approval
    PENDING_APPROVAL --> APPROVED: Senate / Finance Council Sign-off
    PENDING_APPROVAL --> DRAFT: Rejected / Request Modifications
    APPROVED --> ACTIVE: Activate for Billing
    ACTIVE --> RETIRED: Academic Year / Curriculum Superseded
    RETIRED --> [*]
```

### State Definitions & Permitted Actions:
- **DRAFT**: Editable by Finance Officer. Components, heads, and applicability can be freely modified. Not applicable to students.
- **PENDING_APPROVAL**: Locked from routine edits. Displayed in Academic Senate / Dean Finance approval queue.
- **APPROVED**: Formally ratified. Awaiting academic term start.
- **ACTIVE**: In production. Available for student fee assignments and automatic cohort billing.
- **RETIRED**: Archived. Preserved for historical auditing and transcript verification. Cannot receive new student assignments.

---

## 2. Invoicing, Payments & Double-Entry Allocation Flow

The central revenue cycle moves through deterministic stages:

```text
1. Fee Structure (ACTIVE)
       │
       ▼
2. Student Fee Assignment
       ├── (-) Verified Scholarship Concession
       ├── (-) Institutional Early Bird Waiver
       ▼
3. Invoice Generation
       ├── Status: ISSUED
       ├── Net Payable = Gross - Scholarship - Discount - Adjustment
       ├── Outstanding Balance = Net Payable
       ▼
4. Inbound Payment Received (Bank / UPI / Cash)
       ├── Status: SUCCESS
       ├── Allocation Engine:
       │     Allocate to Invoice Lines (Priority: Tuition > Exam > Lab > Other)
       │     Invoice Paid Amount += Allocation
       │     Invoice Outstanding -= Allocation
       │     Status: PARTIALLY_PAID or PAID
       ▼
5. Instant Legal Receipt Generation
       ├── Receipt Voucher: REC-YYYY-XXXXX
       ├── Numeric Amount: ₹XX,XXX.00
       ├── Verified Words: "Rupees ... Only"
       └── Dual Verification Hash
```

### Invariant Rules:
1. Payments cannot exceed the invoice's remaining `outstandingBalance`.
2. Every successful payment produces exactly one immutable `Receipt`.
3. Invoices with `paidAmount > 0` cannot be directly deleted or cancelled; they require an explicit credit adjustment or formal refund petition.

---

## 3. Scholarship Application & Concession Workflow

Scholarships provide controlled tuition reductions based on merit, quota, or sports excellence:

```mermaid
sequenceDiagram
    autonumber
    actor Admin as Accounts Officer / Dean
    actor Student as Student
    participant System as Finance Engine
    participant Invoice as Student Invoice

    Admin->>System: Register Scholarship Scheme (e.g. 20% capped at ₹25k)
    Admin->>System: Approve Scheme (Status: APPROVED)
    Student->>Admin: Submit Verification Credentials
    Admin->>System: Assign Student to Scholarship
    System->>Invoice: Compute Net Payable with Cap
    Note over Invoice: Net = Gross - min(Gross * Rate, Cap)
    System-->>Student: Issue Adjusted Net Invoice
```

---

## 4. Refund & Disbursement Workflow

Institutional refunds manage the reimbursement of caution deposits, excess fees, or cancelled enrollments:

```mermaid
stateDiagram-v2
    [*] --> REQUESTED: Student / Officer Petitions Refund
    REQUESTED --> UNDER_REVIEW: Accounts Officer Verifies Receipts & Bank Details
    UNDER_REVIEW --> APPROVED: Sanctioned with Approved Amount
    UNDER_REVIEW --> REJECTED: Ineligible / Insufficient Claims
    APPROVED --> PROCESSED: Electronic Disbursement via NEFT/RTGS
    PROCESSED --> [*]
    REJECTED --> [*]
```

### Controls & Audit Integrity:
- Every refund links to the original `Invoice` and `Payment` transaction reference.
- Approved amount cannot exceed the original payment's captured amount.
- Rejection requires an explicit justification stored in the immutable timeline.
- The `PROCESSED` state records the precise electronic disbursement timestamp and officer identity.
