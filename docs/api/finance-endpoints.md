# Finance, Fees & Billing API Endpoints

All endpoints are prefixed with `/api/v1/finance`.

## 1. Fee Categories
- `GET /api/v1/finance/fee-categories` — List configured institutional fee categories. Requires `finance:read`.
- `POST /api/v1/finance/fee-categories` — Create fee category (e.g. `TUITION`, `HOSTEL`, `TRANSPORT`). Requires `finance:manage_fee_structures`.

## 2. Fee Structures & Items
- `GET /api/v1/finance/fee-structures` — List fee structures with optional filters (`program_id`, `academic_year_id`, `status`). Requires `finance:read`.
- `POST /api/v1/finance/fee-structures` — Create draft fee structure. Requires `finance:manage_fee_structures`.
- `GET /api/v1/finance/fee-structures/{id}` — Get single fee structure with all item components. Requires `finance:read`.
- `POST /api/v1/finance/fee-structures/{id}/items` — Add chargeable item component to draft fee structure. Requires `finance:manage_fee_structures`.
- `POST /api/v1/finance/fee-structures/{id}/approve` — Approve fee structure, freezing item amounts. Requires `finance:manage_fee_structures`.
- `POST /api/v1/finance/fee-structures/{id}/activate` — Activate fee structure for billing. Requires `finance:manage_fee_structures`.
- `POST /api/v1/finance/fee-structures/{id}/retire` — Retire fee structure from active billing. Requires `finance:manage_fee_structures`.

## 3. Student Fee Assignments & Concessions
- `POST /api/v1/finance/students/assign` — Assign a student to an active fee structure. Requires `finance:manage_fee_structures`.
- `GET /api/v1/finance/students/{student_id}/assignments` — Get fee assignments for a student. Requires `finance:read`.
- `POST /api/v1/finance/concessions` — Grant scholarship, fee concession, or waiver. Requires `scholarships:create`.
- `GET /api/v1/finance/concessions` — List granted concessions with optional student filter. Requires `scholarships:read`.

## 4. Invoices & Billing
- `POST /api/v1/finance/invoices/generate` — Generate student invoice with item snapshots and approved scholarship deductions. Requires `invoices:create`.
- `GET /api/v1/finance/invoices` — List invoices (supports `student_id`, `status`, `is_overdue`, pagination). Enforces student privacy isolation. Requires `invoices:read`.
- `GET /api/v1/finance/invoices/{id}` — Get detailed invoice with line items, allocations, adjustments, and balance. Requires `invoices:read`.
- `POST /api/v1/finance/invoices/{id}/issue` — Issue draft invoice, enabling payment collection. Requires `invoices:issue`.
- `POST /api/v1/finance/invoices/{id}/cancel` — Cancel unpaid invoice with mandatory audit reason. Requires `invoices:cancel`.

## 5. Payments, Allocations & Receipts
- `POST /api/v1/finance/payments` — Record inward payment and transactionally allocate against invoice(s), auto-generating receipt. Requires `payments:create`.
- `GET /api/v1/finance/payments` — List payment transactions. Enforces student privacy isolation. Requires `payments:read`.
- `GET /api/v1/finance/payments/{id}` — Get payment details and allocations. Requires `payments:read`.
- `GET /api/v1/finance/receipts` — List issued payment receipts. Enforces student privacy isolation. Requires `receipts:read`.
- `GET /api/v1/finance/receipts/{id}` — Get official receipt by ID. Requires `receipts:read`.
- `GET /api/v1/finance/receipts/by-number/{receipt_number}` — Get official receipt by receipt number (e.g. `RCP-2026-000001`). Requires `receipts:read`.

## 6. Financial Adjustments & Refunds
- `POST /api/v1/finance/adjustments` — Issue credit or debit note against an invoice. Requires `adjustments:create`.
- `POST /api/v1/finance/refunds` — Request a payment refund. Requires `refunds:create`.
- `POST /api/v1/finance/refunds/{id}/approve` — Approve pending refund. Requires `refunds:approve`.
- `POST /api/v1/finance/refunds/{id}/process` — Process and disburse refund with bank reference. Requires `refunds:process`.
- `GET /api/v1/finance/refunds` — List refund requests. Requires `refunds:create`.

## 7. Dashboards & Financial Statements
- `GET /api/v1/finance/dashboard` — Accounts operational telemetry (total billed, collected, overdue, pending payments, refund requests). Requires `finance:read`.
- `GET /api/v1/finance/students/me/statement` — Authenticated student personal financial statement (invoices, payments, receipts, concessions, net outstanding). Accessible by any authenticated student.
- `GET /api/v1/finance/students/{student_id}/statement` — Authoritative student financial statement for accounts staff. Requires `finance:read`.
