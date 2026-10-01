# ADR-011: Financial Domain Architecture, Fee Lifecycle, Exact Monetary Precision, and Audit Immutability

## Status
Accepted

## Context
Educational institutions require robust, legally compliant financial operations covering fee structuring, cohort billing, payment receipting, scholarship deductions, and refund disbursal. Many campus systems treat student billing as a simple CRUD attribute (`student.fee_due = 50000; student.paid = 50000;`) which fails in enterprise environments because:
1. Historical financial transactions are corrupted whenever fee structures or concessions change.
2. Floating-point arithmetic introduces silent rounding discrepancies in ledgers and tax reports.
3. Payments are naively assumed to be 1:1 with invoices, breaking split payments, advance deposits, and consolidated vouchers.
4. Overdue status is stored statically, becoming stale without batch jobs or manual triggers.
5. Corrections are handled by mutating past payments or invoice totals rather than issuing formal debit/credit notes.
6. Lack of tenant-scoped human-readable numbering complicates official external auditing and tax compliance.

## Decision
We architected the CampusOS Finance, Fees & Billing Engine as an authoritative financial subsystem adhering to strict financial accounting principles:

```text
Fee Category
      ↓
Fee Structure (Draft → Approved → Active → Retired)
      ↓
Student Fee Assignment (with Scholarships / Concessions)
      ↓
Student Invoice (INV-YYYY-XXXXXX)
      ↓
Invoice Lines (Immutable Fee Item Snapshots)
      ↓
Payment Transaction (PAY-YYYY-XXXXXX)
      ↓
Payment Allocation (Many-to-Many Transactional Settle)
      ↓
Official Receipt (RCP-YYYY-XXXXXX)
      ↓
Derived Outstanding Balance
```

### 1. Authoritative Domain Consumption
The Finance Engine directly consumes canonical institutional and academic entities:
- **Tenant & Institution**: Multi-tenant boundaries and institutional currency settings (`currency_code: INR`, `currency_symbol: ₹`, `decimal_precision: 2`).
- **Academic Context**: Academic Years, Semesters, Programs, and Student Categories govern Fee Structure eligibility.
- **Students & Guardians**: Canonical student profiles receive assignments, concessions, invoices, and receipts.

### 2. Exact Monetary Precision
All currency values are strictly modelled as `DECIMAL(12, 2)` (or `NUMERIC(12, 2)`) across Postgres/SQLite, SQLAlchemy ORM models, and Pydantic schemas. Frontend calculations are treated solely as advisory UI previews; the backend Python service layer computes all line totals, discount applications, payment allocations, and balances using Python's exact `decimal.Decimal` module with explicit `ROUND_HALF_UP` quantization.

### 3. Fee Structure Versioning & Historical Immutability
Fee structures progress through a controlled state machine:
`DRAFT` → `APPROVED` → `ACTIVE` → `RETIRED`.
- Fee structures in `DRAFT` can be edited and configured with mandatory or optional fee items.
- Once `APPROVED` or `ACTIVE`, structure line amounts are locked.
- Invoicing a student creates an immutable snapshot (`InvoiceLineItem`) recording the exact fee item name, category, and rate at the moment of billing. Future fee structure modifications or item rate increases never alter already generated invoices.

### 4. Controlled Sequential Numbering
Financial documents require predictable, gap-resistant human-readable sequences rather than opaque UUIDs:
- **Invoices**: `INV-YYYY-000001`
- **Payments**: `PAY-YYYY-000001`
- **Receipts**: `RCP-YYYY-000001`
- **Adjustments**: `ADJ-YYYY-000001`
- **Refunds**: `REF-YYYY-000001`
Sequences are generated transactionally within the tenant and fiscal year context.

### 5. Multi-Invoice Payment Allocation & Transactional Invariance
A payment transaction represents real monetary inflow (Cash, Bank Transfer, UPI, Cheque, Card, DD). Payments are decoupled from invoices via `PaymentAllocation`:
- A single payment can settle multiple invoices or specific line items.
- Over-allocation is prevented at the database and service layer: `sum(allocations) <= payment.amount`.
- Invoices cannot be over-allocated: `sum(allocations) <= invoice.balance_due`.
- Allocations automatically update invoice status (`PARTIALLY_PAID` or `PAID`) and trigger immediate generation of an immutable `Receipt`.

### 6. Dynamic Overdue Calculation
Invoice overdue status is dynamically derived:
$$\text{is\_overdue} \iff \text{status} \in \{\text{ISSUED}, \text{PARTIALLY\_PAID}\} \land \text{due\_date} < \text{current\_date} \land \text{balance\_due} > 0$$
Draft or cancelled invoices are never marked overdue.

### 7. Non-Destructive Accounting Corrections
Direct modification of past financial entries is prohibited:
- **Billing adjustments**: Recorded as `FinancialAdjustment` with type `CREDIT` (reducing invoice balance) or `DEBIT` (increasing invoice balance), complete with audit reason, requester, and approver.
- **Refunds**: Follow a three-step lifecycle (`REQUESTED` → `APPROVED` → `PROCESSED`), strictly validated to ensure `refund_amount <= (payment.amount - sum(prior_refunds))`.

### 8. Granular RBAC and Student Privacy
19 granular permissions govern the financial subsystem. Student users are restricted to viewing only their own invoices, payments, receipts, and scholarships (`student_id == current_user.student_id`), while cross-tenant queries return HTTP 404 or 403.

## Consequences
- Guaranteed zero rounding discrepancies across fee collections, balance inquiries, and financial statements.
- Complete regulatory and statutory audit trail compliance for financial audits and NAAC/UGC reviews.
- Provides clean extensibility for future Payment Gateway integrations (Razorpay, Stripe), Bank Reconciliation, and General Ledger export without breaking core entities.
