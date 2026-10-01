# ADR-006: Financial Ledger and Transaction Integrity

## Status

**Accepted**

## Context

Financial management in educational institutions handles multi-million dollar annual fee operations comprising tuition, laboratory, examination, transport, hostel, caution deposits, scholarships, and third-party bank payments.

Common failure modes in legacy ERPs include:
- Mutable in-place balance updates (e.g. `UPDATE students SET balance = balance - 50000`).
- Overwriting or updating invoice amounts after issuance.
- Deleting erroneous payments or receipts to "fix" accounts, corrupting accounting ledgers.
- Lack of explicit attribution between payment lump sums and specific invoice fee heads.

## Decision

CampusOS implements an **immutable, double-entry-inspired transaction ledger architecture**:

1. **Immutable Invoicing**:
   - Invoices (`finance_invoices`) and line items (`finance_invoice_line_items`) are generated for specific academic terms and fee structures.
   - Once an invoice is marked `ISSUED`, its line item amounts and total payable become strictly immutable.
   - Any legitimate reduction in fees (e.g. late scholarship grant, merit concession, fee waiver) is applied via an explicit `FinancialAdjustment` (Credit Note) referencing the invoice, preserving the original billing history.

2. **Decoupled Payment Ingestion and Allocation**:
   - A `PaymentTransaction` captures the physical or electronic receipt of capital (transaction reference, bank transaction ID, gateway payload hash, payment mode, amount, timestamp, status).
   - Capital allocations to debts are modeled via a dedicated join entity: `PaymentAllocation`.
   - A single payment can be allocated across multiple invoices (e.g. paying tuition and hostel fee in a single bank transfer), or a single invoice can be settled across multiple installments.
   - **Invariant**: The sum of `PaymentAllocation.allocated_amount` for any payment cannot exceed `PaymentTransaction.amount`.
   - **Invariant**: The sum of allocations and credit adjustments for any invoice cannot exceed `Invoice.total_amount`.

3. **Receipt Generation**:
   - Official institutional receipts (`finance_receipts`) are sequentially numbered, cryptographically signed, and generated only after a `PaymentTransaction` transitions to `SUCCESS`.
   - Receipts are immutable and permanent financial artifacts.

4. **Refund and Reversal Governance**:
   - Payments are never deleted. If an erroneous payment was recorded or a student withdraws admission, a formal `RefundTransaction` is generated, linking to the original payment, requiring supervisory approval, and issuing a debit note against the institution's ledger.

## Consequences

### Positive
- Total financial auditability: zero discrepancy between bank statements, student ledgers, and institutional revenue reports.
- Prevents fraud and unauthorized cash handling: all changes leave tamper-evident transactional footprints.
- Supports complex installment billing, split payments, scholarship sponsorships, and partial waivers without corrupting baseline fee structures.

### Negative / Tradeoffs
- Higher table count and write overhead during payment capture (requires atomic multi-table transaction spanning `PaymentTransaction`, `PaymentAllocation`, `Invoice` balance updates, and `Receipt`).
- Ledger reconciliation requires sum queries across allocation and adjustment tables.
