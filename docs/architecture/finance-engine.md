# Finance, Fees & Billing Engine Architecture

## 1. Subsystem Overview
The Finance, Fees & Billing Engine transforms CampusOS into an operational enterprise business system. It provides authoritative management of institutional revenue cycles: fee structuring, cohort and student billing, payment recording, multi-invoice payment allocation, receipt generation, scholarship/concession discounts, financial adjustments, and refund disbursal.

```text
Fee Category Master (Tuition, Hostel, Exam, Lab, Transport)
       │
       ▼
Fee Structure (Versioned: DRAFT → APPROVED → ACTIVE → RETIRED)
       │
       ▼
Student Fee Assignment (Linked to Canonical Student, Program, Academic Year)
       │
       ▼
Student Invoice (INV-YYYY-XXXXXX) & Immutable Line Snapshots
       │
       ▼
Payment Transaction (PAY-YYYY-XXXXXX, Cash/Bank/UPI/Card/Cheque)
       │
       ▼
Payment Allocation (M:N Transactional Settle against Invoices & Line Items)
       │
       ▼
Official Receipt (RCP-YYYY-XXXXXX, Immutable Payment Voucher)
       │
       ▼
Authoritative Ledger Balance (Total Invoiced, Total Paid, Balance Due, Overdue)
```

## 2. Core Principles & Domain Boundaries
1. **Canonical Entity Consumption**: Reuses existing `Student`, `ParentGuardian`, `Program`, `AcademicYear`, and `Semester` entities. No parallel or duplicate student registries exist.
2. **Exact Monetary Precision**: All monetary values are modelled as `DECIMAL(12, 2)` in PostgreSQL/SQLite and handled using Python's `decimal.Decimal` with `ROUND_HALF_UP` quantization. Floating-point types are strictly forbidden.
3. **Financial Immutability**: Historical financial records are never modified in-place to "fix" discrepancies. Adjustments are executed via `FinancialAdjustment` (debit/credit notes), refunds via `RefundTransaction`, and corrections via formal reversal transactions.
4. **Decoupled Payments & Allocations**: Payments represent real money received. Inward funds can be allocated across multiple invoices or individual line items, supporting advance deposits and partial settlements.
5. **Human-Readable Controlled Sequences**: Documents use predictable, gap-resistant sequence formats: `INV-YYYY-XXXXXX`, `PAY-YYYY-XXXXXX`, `RCP-YYYY-XXXXXX`, `REF-YYYY-XXXXXX`, `ADJ-YYYY-XXXXXX`.
6. **Student Privacy & Tenant Isolation**: Multi-tenant boundaries ensure zero cross-institution data exposure. Student self-service portals restrict visibility strictly to the authenticated student's own records.

## 3. Financial Workflow & State Machines

### A. Fee Structure Lifecycle
```text
  [ DRAFT ] ──(Approve)──► [ APPROVED ] ──(Activate)──► [ ACTIVE ] ──(Retire)──► [ RETIRED ]
```
- In `DRAFT` status, administrators configure mandatory and optional fee items with target amounts.
- `APPROVED` freezes the structure items to preserve historical rate integrity.
- Only `ACTIVE` fee structures can be assigned to students or used to generate invoices.
- When superseded by a newer academic term's fee schedule, the structure transitions to `RETIRED`.

### B. Invoice State Machine & Overdue Derivation
```text
  [ DRAFT ] ──(Issue)──► [ ISSUED ] ──(Partial Payment)──► [ PARTIALLY_PAID ] ──(Full Settle)──► [ PAID ]
      │                     │                                    │
      └──(Cancel)           └──(Due Date Passed)                 └──(Due Date Passed)
                                   │                                    │
                                   ▼                                    ▼
                             (is_overdue = true)                  (is_overdue = true)
```
- **Dynamic Overdue State**: An invoice is overdue if and only if `status in ["ISSUED", "PARTIALLY_PAID"]` AND `due_date < current_date` AND `balance_due > 0`.
- Invoices in `DRAFT` or `CANCELLED` status are never marked overdue.

### C. Payment Allocation & Settle
```text
Payment Received (PAY-2026-000001: ₹100,000)
    │
    ├── Allocation 1: INV-2026-000010 (Tuition Line)  ──► ₹80,000  (Invoice Balance: ₹0 [PAID])
    │
    └── Allocation 2: INV-2026-000011 (Hostel Line)   ──► ₹20,000  (Invoice Balance: ₹30,000 [PARTIALLY_PAID])
    │
    ▼
Receipt Issued (RCP-2026-000001: ₹100,000)
```
- Transactional invariance guarantees:
  1. $\sum \text{allocated\_amount} \le \text{payment.amount}$
  2. $\text{allocated\_amount} \le \text{invoice.balance\_due}$

### D. Adjustments & Concessions
- **Scholarships / Concessions (`StudentFeeConcession`)**: Applied during or after invoice generation. Can be `PERCENTAGE` or `FIXED_AMOUNT`. Validated against maximum allowable caps.
- **Financial Adjustments (`FinancialAdjustment`)**:
  - `CREDIT`: Authorized reduction of amount owed (e.g. fee waiver, administrative correction). Reduces `balance_due`.
  - `DEBIT`: Authorized increase of amount owed (e.g. late fine, damages, omitted charges). Increases `total_amount` and `balance_due`.

### E. Refund Lifecycle
```text
  [ REQUESTED ] ──(Approve)──► [ APPROVED ] ──(Disburse)──► [ PROCESSED ]
        │
        └──(Reject)──► [ REJECTED ]
```
- Validated against payment headroom:
  $$\text{requested\_amount} \le \text{payment.amount} - \sum \text{prior\_processed\_refunds}$$

## 4. Derived Balances & Mathematical Formulas

$$\text{Subtotal} = \sum_{\text{lines}} \text{line.amount}$$

$$\text{Invoice Total} = \text{Subtotal} - \text{Total Discounts} + \sum \text{Debit Adjustments} - \sum \text{Credit Adjustments}$$

$$\text{Balance Due} = \text{Invoice Total} - \sum \text{Allocated Payments}$$

## 5. Future Extension Interfaces
The Finance Engine defines clean abstraction boundaries for future subsystems:
- **Online Payment Gateways**: Ready for Razorpay, Stripe, and BillDesk webhooks via `PaymentTransaction.external_reference` and `payment_gateway_metadata`.
- **UPI Deep-Linking**: QR-code and VPA intent generation ready using tenant virtual payment addresses.
- **Bank Statement Reconciliation**: Clean matching hooks using `PAY-YYYY-XXXXXX` and bank UTRs.
- **General Ledger & Double-Entry Accounting**: Fee categories and structure items map directly to Chart of Accounts (COA) codes.
- **Hostel & Transport Billing**: Can emit standalone or bundled invoices into the `Invoice` ledger without modifying the core billing schema.
