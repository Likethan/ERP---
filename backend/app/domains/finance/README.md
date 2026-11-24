# Finance Domain (`app/domains/finance`)

## Purpose

Directs fee catalogs, tuition structures, student invoices, payment gateway reconciliation, scholarships, concessions, and formal receipts.

## Key Entities

- `FeeStructure`
- `FeeCategory` / `FeeItem`
- `StudentInvoice`
- `PaymentTransaction`
- `Receipt`
- `ScholarshipGrant`

## Boundaries & Constraints

- Immutable ledger: Financial transactions cannot be updated in-place; cancellations must be handled via credit notes / reversal entries.
- Exposes fee clearance status to Examination and Placement modules.
