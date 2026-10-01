# Finance Engine Database Schema & Data Integrity

## 1. Schema Overview
The Finance Engine database schema enforces enterprise financial accounting rules: exact decimal precision, immutable historical document snapshots, transactional many-to-many payment allocations, and human-readable sequence numbering scoped by tenant.

```text
┌──────────────────┐       1:N       ┌──────────────────┐
│  fee_categories  │◄────────────────┤   fee_items      │
└──────────────────┘                 └────────┬─────────┘
                                              │ N:1
                                              ▼
┌──────────────────┐       1:N       ┌──────────────────┐
│  academic_years  │◄────────────────┤  fee_structures  │
└──────────────────┘                 └────────┬─────────┘
                                              │ 1:N
                                              ▼
                                     ┌─────────────────────────┐
                                     │ student_fee_assignments │
                                     └────────┬────────────────┘
                                              │ 1:N
                                              ▼
┌───────────────────────────┐ 1:N    ┌─────────────────────────┐
│  student_fee_concessions  │◄───────┤        invoices         │
└───────────────────────────┘        └────────┬─────────┬──────┘
                                          1:N │         │ 1:N
                                              ▼         ▼
┌───────────────────────────┐        ┌─────────────┐   ┌───────────────────────────┐
│   payment_allocations     │◄───────┤invoice_lines│   │   financial_adjustments   │
└─────────────┬─────────────┘        └─────────────┘   └───────────────────────────┘
              │ N:1
              ▼
┌───────────────────────────┐       1:1       ┌───────────────────────────┐
│   payment_transactions    ├────────────────►│         receipts          │
└─────────────┬─────────────┘                 └───────────────────────────┘
              │ 1:N
              ▼
┌───────────────────────────┐
│    refund_transactions    │
└───────────────────────────┘
```

## 2. Table Definitions

### A. `fee_categories`
Classification master for institutional fee items.
- `id` (UUID, PK)
- `tenant_id` (UUID, FK -> tenants.id, indexed)
- `code` (VARCHAR(50), NOT NULL) — e.g. `TUITION`, `HOSTEL`, `TRANSPORT`, `EXAMINATION`, `LIBRARY`, `LABORATORY`
- `name` (VARCHAR(150), NOT NULL)
- `description` (TEXT, nullable)
- `is_system` (BOOLEAN, default: false)
- `is_active` (BOOLEAN, default: true)
- Unique: `(tenant_id, code)`

### B. `fee_structures`
Term-specific fee schedules with lifecycle governance.
- `id` (UUID, PK)
- `tenant_id` (UUID, FK -> tenants.id, indexed)
- `name` (VARCHAR(200), NOT NULL)
- `program_id` (UUID, FK -> programs.id, nullable)
- `academic_year_id` (UUID, FK -> academic_years.id, NOT NULL, indexed)
- `semester_id` (UUID, FK -> semesters.id, nullable)
- `student_category` (VARCHAR(50), nullable) — e.g. `REGULAR`, `MANAGEMENT_QUOTA`, `INTERNATIONAL`
- `currency_code` (VARCHAR(3), default: 'INR')
- `total_amount` (DECIMAL(12, 2), default: 0.00)
- `status` (VARCHAR(20), default: 'DRAFT') — `DRAFT`, `APPROVED`, `ACTIVE`, `RETIRED`
- `approved_by_id` (UUID, FK -> users.id, nullable)
- `approved_at` (TIMESTAMPTZ, nullable)
- `version` (INT, default: 1)
- Indexes: `(tenant_id, academic_year_id, status)`

### C. `fee_items`
Chargeable components attached to a fee structure.
- `id` (UUID, PK)
- `fee_structure_id` (UUID, FK -> fee_structures.id ON DELETE CASCADE, NOT NULL)
- `fee_category_id` (UUID, FK -> fee_categories.id, NOT NULL)
- `name` (VARCHAR(150), NOT NULL)
- `amount` (DECIMAL(12, 2), NOT NULL)
- `is_mandatory` (BOOLEAN, default: true)
- `sequence_order` (INT, default: 1)
- `due_offset_days` (INT, default: 30)

### D. `student_fee_assignments`
Binds an eligible student to an active fee structure.
- `id` (UUID, PK)
- `tenant_id` (UUID, FK -> tenants.id, indexed)
- `student_id` (UUID, FK -> students.id, NOT NULL, indexed)
- `fee_structure_id` (UUID, FK -> fee_structures.id, NOT NULL)
- `academic_year_id` (UUID, FK -> academic_years.id, NOT NULL)
- `semester_id` (UUID, FK -> semesters.id, nullable)
- `status` (VARCHAR(20), default: 'ACTIVE') — `PENDING`, `ACTIVE`, `COMPLETED`, `CANCELLED`
- `assigned_at` (TIMESTAMPTZ, default: now)
- Unique: `(tenant_id, student_id, fee_structure_id, academic_year_id)`

### E. `student_fee_concessions`
Institutional scholarships, merit discounts, and fee waivers.
- `id` (UUID, PK)
- `tenant_id` (UUID, FK -> tenants.id, indexed)
- `student_id` (UUID, FK -> students.id, NOT NULL, indexed)
- `academic_year_id` (UUID, FK -> academic_years.id, NOT NULL)
- `name` (VARCHAR(150), NOT NULL) — e.g. "Merit Scholarship 50%", "Sports Concession"
- `concession_type` (VARCHAR(20), NOT NULL) — `PERCENTAGE`, `FIXED_AMOUNT`, `FULL_WAIVER`
- `rate_value` (DECIMAL(12, 2), NOT NULL)
- `max_amount` (DECIMAL(12, 2), nullable)
- `fee_category_id` (UUID, FK -> fee_categories.id, nullable) — null applies across invoice subtotal
- `status` (VARCHAR(20), default: 'APPROVED') — `REQUESTED`, `APPROVED`, `REVOKED`
- `approved_by_id` (UUID, FK -> users.id, nullable)
- `reason` (TEXT, NOT NULL)

### F. `invoices`
Formal billing documents with snapshot totals and derived balances.
- `id` (UUID, PK)
- `tenant_id` (UUID, FK -> tenants.id, indexed)
- `invoice_number` (VARCHAR(50), NOT NULL) — e.g. `INV-2026-000001`
- `student_id` (UUID, FK -> students.id, NOT NULL, indexed)
- `academic_year_id` (UUID, FK -> academic_years.id, NOT NULL)
- `semester_id` (UUID, FK -> semesters.id, nullable)
- `fee_structure_id` (UUID, FK -> fee_structures.id, nullable)
- `issue_date` (DATE, NOT NULL)
- `due_date` (DATE, NOT NULL, indexed)
- `currency_code` (VARCHAR(3), default: 'INR')
- `subtotal` (DECIMAL(12, 2), NOT NULL)
- `discount_amount` (DECIMAL(12, 2), default: 0.00)
- `adjustment_amount` (DECIMAL(12, 2), default: 0.00)
- `total_amount` (DECIMAL(12, 2), NOT NULL)
- `paid_amount` (DECIMAL(12, 2), default: 0.00)
- `balance_due` (DECIMAL(12, 2), NOT NULL)
- `status` (VARCHAR(20), default: 'DRAFT') — `DRAFT`, `ISSUED`, `PARTIALLY_PAID`, `PAID`, `CANCELLED`
- `is_overdue` (BOOLEAN, default: false, indexed)
- Unique: `(tenant_id, invoice_number)`
- Composite Indexes: `(tenant_id, student_id)`, `(tenant_id, status)`, `(tenant_id, due_date)`

### G. `invoice_line_items`
Frozen snapshot of chargeable items at invoice generation time.
- `id` (UUID, PK)
- `invoice_id` (UUID, FK -> invoices.id ON DELETE CASCADE, NOT NULL)
- `fee_category_id` (UUID, FK -> fee_categories.id, NOT NULL)
- `fee_item_name` (VARCHAR(150), NOT NULL)
- `amount` (DECIMAL(12, 2), NOT NULL)
- `paid_amount` (DECIMAL(12, 2), default: 0.00)
- `sequence_order` (INT, default: 1)

### H. `payment_transactions`
Inward financial instruments received by the institution.
- `id` (UUID, PK)
- `tenant_id` (UUID, FK -> tenants.id, indexed)
- `payment_number` (VARCHAR(50), NOT NULL) — e.g. `PAY-2026-000001`
- `student_id` (UUID, FK -> students.id, NOT NULL, indexed)
- `amount` (DECIMAL(12, 2), NOT NULL)
- `currency_code` (VARCHAR(3), default: 'INR')
- `payment_date` (DATE, NOT NULL)
- `payment_method` (VARCHAR(30), NOT NULL) — `CASH`, `BANK_TRANSFER`, `UPI`, `CHEQUE`, `CARD`, `DEMAND_DRAFT`, `ONLINE_GATEWAY`
- `external_reference` (VARCHAR(100), nullable) — UTR, Cheque No, Transaction ID (CVV/PIN strictly forbidden)
- `status` (VARCHAR(20), default: 'SUCCESS') — `PENDING`, `SUCCESS`, `FAILED`, `CANCELLED`, `REFUNDED`, `PARTIALLY_REFUNDED`
- `received_by_id` (UUID, FK -> users.id, NOT NULL)
- `notes` (TEXT, nullable)
- Unique: `(tenant_id, payment_number)`

### I. `payment_allocations`
Many-to-many settlement link between payments and invoices.
- `id` (UUID, PK)
- `payment_id` (UUID, FK -> payment_transactions.id ON DELETE CASCADE, NOT NULL)
- `invoice_id` (UUID, FK -> invoices.id, NOT NULL)
- `invoice_line_item_id` (UUID, FK -> invoice_line_items.id, nullable)
- `allocated_amount` (DECIMAL(12, 2), NOT NULL)
- `allocated_at` (TIMESTAMPTZ, default: now)

### J. `receipts`
Immutable official payment voucher acknowledging payment.
- `id` (UUID, PK)
- `tenant_id` (UUID, FK -> tenants.id, indexed)
- `receipt_number` (VARCHAR(50), NOT NULL) — e.g. `RCP-2026-000001`
- `payment_id` (UUID, FK -> payment_transactions.id, NOT NULL, unique)
- `student_id` (UUID, FK -> students.id, NOT NULL, indexed)
- `amount` (DECIMAL(12, 2), NOT NULL)
- `currency_code` (VARCHAR(3), default: 'INR')
- `receipt_date` (DATE, NOT NULL)
- `issued_by_id` (UUID, FK -> users.id, NOT NULL)
- Unique: `(tenant_id, receipt_number)`

### K. `financial_adjustments`
Formal debit/credit notes for ledger corrections.
- `id` (UUID, PK)
- `tenant_id` (UUID, FK -> tenants.id, indexed)
- `adjustment_number` (VARCHAR(50), NOT NULL) — e.g. `ADJ-2026-000001`
- `invoice_id` (UUID, FK -> invoices.id, NOT NULL)
- `adjustment_type` (VARCHAR(10), NOT NULL) — `CREDIT`, `DEBIT`
- `amount` (DECIMAL(12, 2), NOT NULL)
- `reason` (TEXT, NOT NULL)
- `status` (VARCHAR(20), default: 'APPROVED') — `PENDING`, `APPROVED`, `REJECTED`
- `requested_by_id` (UUID, FK -> users.id, NOT NULL)
- `approved_by_id` (UUID, FK -> users.id, nullable)
- `approved_at` (TIMESTAMPTZ, nullable)
- Unique: `(tenant_id, adjustment_number)`

### L. `refund_transactions`
Audited money returns linked to original payments.
- `id` (UUID, PK)
- `tenant_id` (UUID, FK -> tenants.id, indexed)
- `refund_number` (VARCHAR(50), NOT NULL) — e.g. `REF-2026-000001`
- `payment_id` (UUID, FK -> payment_transactions.id, NOT NULL)
- `student_id` (UUID, FK -> students.id, NOT NULL, indexed)
- `amount` (DECIMAL(12, 2), NOT NULL)
- `reason` (TEXT, NOT NULL)
- `status` (VARCHAR(20), default: 'REQUESTED') — `REQUESTED`, `APPROVED`, `PROCESSED`, `REJECTED`, `CANCELLED`
- `requested_by_id` (UUID, FK -> users.id, NOT NULL)
- `approved_by_id` (UUID, FK -> users.id, nullable)
- `processed_by_id` (UUID, FK -> users.id, nullable)
- `processed_at` (TIMESTAMPTZ, nullable)
- `refund_reference` (VARCHAR(100), nullable)
- Unique: `(tenant_id, refund_number)`
