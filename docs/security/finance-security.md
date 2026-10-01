# Finance Subsystem Security Architecture & Controls

## 1. Threat Model & Security Posture
Financial records represent legal and regulatory liabilities. The CampusOS Finance Engine enforces zero-trust controls against:
1. **Balance Tampering**: Preventing arbitrary direct updates to `student.balance` or `invoice.total`.
2. **Cross-Tenant Data Leakage**: Ensuring Tenant A cannot view, bill, or allocate funds to Tenant B.
3. **Over-Allocation & Double Dipping**: Validating payment allocations transactionally to prevent applying more funds than were actually received.
4. **Illegal Refunds**: Enforcing a strict three-phase approval lifecycle where refunded amounts cannot exceed remaining payment headroom.
5. **Student Privacy Exposure**: Preventing any student from querying peer invoices, balances, or payment histories.

## 2. Multi-Tenant Isolation
All financial entities (`FeeCategory`, `FeeStructure`, `StudentFeeAssignment`, `StudentFeeConcession`, `Invoice`, `PaymentTransaction`, `Receipt`, `FinancialAdjustment`, `RefundTransaction`) are scoped by `tenant_id`:
- Every database query automatically filters on `tenant_id == current_user.tenant_id`.
- Sequence numbers (`INV-YYYY-XXXXXX`, `PAY-YYYY-XXXXXX`, etc.) are partitioned by tenant, ensuring uniqueness within institutional bounds without cross-tenant collisions.
- Cross-tenant access attempts return HTTP 404 or HTTP 403 and trigger security audit events.

## 3. RBAC / PBAC Permission Matrix

| Permission Code | Description | Authorized Roles (Default) |
| :--- | :--- | :--- |
| `finance:read` | Read fee structures, statements, and financial telemetry | `ACCOUNTS_MANAGER`, `ACCOUNTS_CLERK`, `ADMIN`, `SUPER_ADMIN` |
| `finance:manage_fee_structures` | Create, configure, approve, and activate fee structures | `ACCOUNTS_MANAGER`, `ADMIN`, `SUPER_ADMIN` |
| `invoices:read` | View student invoices and line items | `ACCOUNTS_MANAGER`, `ACCOUNTS_CLERK`, `ADMIN`, `STUDENT` (own only) |
| `invoices:create` | Generate draft invoices from active fee structures | `ACCOUNTS_MANAGER`, `ACCOUNTS_CLERK`, `ADMIN` |
| `invoices:issue` | Issue invoices, locking lines and initiating due status | `ACCOUNTS_MANAGER`, `ADMIN` |
| `invoices:cancel` | Void unpaid invoices with mandatory justification | `ACCOUNTS_MANAGER`, `ADMIN` |
| `payments:read` | View payment transactions and settlement allocations | `ACCOUNTS_MANAGER`, `ACCOUNTS_CLERK`, `ADMIN`, `STUDENT` (own only) |
| `payments:create` | Record inward payments and execute allocations | `ACCOUNTS_MANAGER`, `ACCOUNTS_CLERK`, `ADMIN` |
| `payments:confirm` | Confirm gateway or bank cleared payments | `ACCOUNTS_MANAGER`, `ADMIN` |
| `receipts:read` | View and print official payment receipts | `ACCOUNTS_MANAGER`, `ACCOUNTS_CLERK`, `ADMIN`, `STUDENT` (own only) |
| `receipts:issue` | Issue formal stamped payment vouchers | `ACCOUNTS_MANAGER`, `ACCOUNTS_CLERK`, `ADMIN` |
| `scholarships:read` | View scholarships, concessions, and fee waivers | `ACCOUNTS_MANAGER`, `ACCOUNTS_CLERK`, `ADMIN`, `STUDENT` (own only) |
| `scholarships:create` | Define and award scholarships to students | `ACCOUNTS_MANAGER`, `ADMIN` |
| `scholarships:approve` | Authorize scholarship discount applications | `ADMIN`, `SUPER_ADMIN` |
| `adjustments:create` | Issue debit or credit notes against invoices | `ACCOUNTS_MANAGER`, `ADMIN` |
| `adjustments:approve` | Formally approve ledger adjustments | `ADMIN`, `SUPER_ADMIN` |
| `refunds:create` | Submit refund requests for overpayment or cancellation | `ACCOUNTS_MANAGER`, `ACCOUNTS_CLERK`, `ADMIN` |
| `refunds:approve` | Authorize refund eligibility | `ACCOUNTS_MANAGER`, `ADMIN` |
| `refunds:process` | Disburse refund and record external reference | `ACCOUNTS_MANAGER`, `ADMIN` |

## 4. Student Financial Privacy
- When a student authenticates, queries to `/api/v1/finance/invoices`, `/payments`, and `/receipts` automatically append `student_id == current_user.student_id`.
- Attempting to query another student's invoice ID or receipt returns HTTP 403 Forbidden.
- The student portal endpoint `/api/v1/finance/students/me/statement` provides a self-service view of their personal billing ledger, payments, active concessions, and outstanding balance without administrative metadata.

## 5. Payment Credential Protection
The CampusOS Finance Engine complies with standard PCI-DSS guidelines for enterprise software:
- Non-cash payment records only store non-sensitive external references (Bank UTR number, UPI transaction reference, Cheque number, Demand Draft number).
- Full credit/debit card numbers, CVVs, PINs, OTPs, or online banking passwords are NEVER ingested, transmitted, or stored.

## 6. Audit & Non-Destructive Accounting
Financial operations emit structured audit logs (`AuditLog`):
- `FEE_STRUCTURE_CREATED`, `FEE_STRUCTURE_APPROVED`, `FEE_STRUCTURE_ACTIVATED`, `FEE_STRUCTURE_RETIRED`
- `FEE_ASSIGNED`
- `INVOICE_GENERATED`, `INVOICE_ISSUED`, `INVOICE_CANCELLED`
- `PAYMENT_RECORDED`, `PAYMENT_ALLOCATED`, `RECEIPT_ISSUED`
- `SCHOLARSHIP_GRANTED`
- `FINANCIAL_ADJUSTMENT_CREATED`
- `REFUND_REQUESTED`, `REFUND_APPROVED`, `REFUND_PROCESSED`
Every audit record stores the actor ID, tenant ID, entity type, timestamp, IP address, and payload snapshot.
