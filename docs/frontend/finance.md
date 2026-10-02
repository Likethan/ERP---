# CampusOS — Finance, Fees & Billing Frontend Architecture

## 1. Architectural Overview

The **Finance, Fees & Billing** module establishes an enterprise financial operating system for higher education institutions within CampusOS. It implements an auditable, deterministic, double-entry financial ledger model on the frontend while maintaining absolute isolation from backend storage and real-world payment networks.

### Layered Architecture
```text
┌────────────────────────────────────────────────────────┐
│ UI Pages & Workflows (Next.js 15 App Router)            │
│ (/app/finance/*, DataGrids, Modals, Wizards, Reports)  │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ Pure Calculation Engine (Deterministic Financial Math) │
│ (financial-calculator.ts: Pure integer minor arithmetic)│
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ Finance Service Interface (finance.service.ts)         │
│ (Typed TypeScript API Service with async contracts)    │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ In-Memory Reactive Mock Adapter (finance.mock.ts)      │
│ (Stateful relational store with cross-entity sync)     │
└──────────────────────────┬─────────────────────────────┘
                           │
                     [Future FastAPI]
                 (Zero touches in Phase)
```

---

## 2. Core Entities & Financial Domain Model

| Entity | Purpose | Key Attributes |
| :--- | :--- | :--- |
| **FeeCategory** | Classification of institutional charges | `id`, `code`, `name`, `type`, `isTaxable`, `isRefundable`, `status` |
| **FeeItem** | Reusable catalog pricing components | `id`, `categoryId`, `code`, `name`, `amount`, `isOptional`, `isRefundable` |
| **FeeStructure** | Program & semester fee specification | `id`, `code`, `name`, `program`, `semester`, `components[]`, `grossTotal`, `status` |
| **StudentFeeAssignment** | Binding of a student to a FeeStructure | `id`, `studentId`, `feeStructureId`, `grossAmount`, `scholarshipDiscount`, `netPayable` |
| **Invoice** | Official bill issued to student | `id`, `invoiceNumber`, `studentId`, `lines[]`, `grossAmount`, `discountAmount`, `netPayable`, `paidAmount`, `outstandingBalance`, `status` |
| **Payment** | Inbound financial transaction | `id`, `transactionRef`, `studentId`, `invoiceId`, `amount`, `allocatedAmount`, `unallocatedAmount`, `paymentMethod`, `status` |
| **PaymentAllocation** | Double-entry allocation of payment | `id`, `paymentId`, `invoiceId`, `allocatedAmount`, `allocatedAt` |
| **Receipt** | Official legal monetary voucher | `id`, `receiptNumber`, `paymentId`, `studentId`, `amount`, `amountInWords`, `issuedAt`, `issuedBy` |
| **Scholarship** | Financial concession or merit scheme | `id`, `code`, `name`, `discountType`, `value`, `maxDiscountAmount`, `status` |
| **FinancialAdjustment** | Post-billing credit/debit modification | `id`, `invoiceId`, `type`, `amount`, `reason`, `approvedBy` |
| **Refund** | Reimbursement petition & disbursement | `id`, `refundNumber`, `studentId`, `invoiceId`, `paymentId`, `requestedAmount`, `approvedAmount`, `status` |

---

## 3. Financial Submodule Directory & Routing

All routes exist under `/app/finance/*` and are integrated into the primary application navigation sidebar:

1. **Operations Dashboard (`/app/finance`)**:
   - Executive KPIs: Gross Billed, Total Collected, Total Outstanding, Total Overdue, Collection Rate.
   - 6 Operational Action Queues: Pending Payments, Overdue Invoices, Refund Requests, Scholarship Approvals, Unallocated Float, Issued Receipts.
   - Debt Aging Distribution Bar: Real-time segmentation across 5 standard aging delinquency buckets.
   - Personalized Student Experience: "My Finance" tab with student dues, invoices, and vouchers.

2. **Fee Categories (`/app/finance/fee-categories`)**:
   - Enterprise DataGrid with sorting, filtering, and status toggle.
   - Create and Edit modals with taxable and refundable policy flags.

3. **Fee Structures (`/app/finance/fee-structures`)**:
   - 6-step guided wizard for creating structured semester fees.
   - Lifecycle state machine: `DRAFT` → `PENDING_APPROVAL` → `APPROVED` → `ACTIVE` → `RETIRED`.

4. **Fee Structure 360° Profile (`/app/finance/fee-structures/[id]`)**:
   - Overview, fee breakdown items, enrolled students cohort ledger, and audit history.
   - Governance action triggers for Academic Senate submission, approval, and activation.

5. **Student Fee Assignments (`/app/finance/assignments`)**:
   - Ledger of individual fee allocations.
   - Single student assignment with automatic scholarship reduction.
   - Bulk cohort assignment by academic program, batch, and semester.

6. **Invoices Ledger (`/app/finance/invoices`)**:
   - Enterprise DataGrid with search, status filters, and multi-criteria date ranges.
   - Quick invoice generator modal.

7. **Official Invoice Detail (`/app/finance/invoices/[id]`)**:
   - Print-ready invoice document with institutional header.
   - Line items table with taxable sub-breakdowns.
   - Guided record payment modal with strict balance bounds checking.
   - Invoice cancellation modal with audit justification.

8. **Payments Ledger (`/app/finance/payments`)**:
   - Real-time transaction ledger with multi-channel filtering (`UPI`, `BANK_TRANSFER`, `CASH`, `CARD`, `CHEQUE`).
   - Guided payment record modal with automatic allocation.

9. **Payment Detail Audit (`/app/finance/payments/[id]`)**:
   - Bank reference / UTR tracking, invoice link, allocations breakdown, and audit timeline.

10. **Receipts Ledger & Official Receipt (`/app/finance/receipts`, `/app/finance/receipts/[id]`)**:
    - Legal money receipt with official voucher sequence (`REC-YYYY-XXXXX`).
    - Amount in numbers and generated text words, payment mode, cashier signature block, and browser print trigger.

11. **Scholarships & Concessions (`/app/finance/scholarships`, `/app/finance/scholarships/[id]`)**:
    - Schemes ledger (Percentage vs Fixed, maximum caps).
    - Detail profile with recipient students ledger, total disbursements, and approval workflow.

12. **Refunds Ledger & Review (`/app/finance/refunds`, `/app/finance/refunds/[id]`)**:
    - Multi-stage refund lifecycle: `REQUESTED` → `UNDER_REVIEW` → `APPROVED` / `REJECTED` → `PROCESSED`.
    - Sanctioned amount override, reviewer notes, and electronic disbursement trigger.

13. **Financial Reports & Audit (`/app/finance/reports`)**:
    - 5 report templates: Collection Summary, Outstanding Invoices, Aging Debt Analysis, Payment Methods Breakdown, Scholarship Utilization.
    - Searchable preview table and client-side RFC 4180 CSV export.
