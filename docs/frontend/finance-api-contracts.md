# CampusOS — Finance Service API Contracts (Future FastAPI Specifications)

This document formalizes the TypeScript service interfaces implemented by `finance.service.ts` into expected future FastAPI REST endpoints, JSON payloads, and HTTP status codes.

---

## 1. Fee Categories & Catalog

### `GET /api/v1/finance/fee-categories`
- **Description**: Returns all fee categories.
- **Response**: `200 OK`
```json
{
  "success": true,
  "data": [
    {
      "id": "cat-tuition",
      "code": "CAT-TUI",
      "name": "Tuition Fee",
      "type": "TUITION",
      "description": "Core instructional and academic laboratory charges",
      "isTaxable": false,
      "isRefundable": true,
      "status": "ACTIVE",
      "createdAt": "2026-01-10T09:00:00Z"
    }
  ]
}
```

### `POST /api/v1/finance/fee-categories`
- **Description**: Create a new institutional fee category.
- **Request Body**:
```json
{
  "code": "CAT-HOSTEL",
  "name": "Hostel & Residence Fee",
  "type": "HOSTEL",
  "description": "Accommodation and utility charges",
  "isTaxable": false,
  "isRefundable": true
}
```
- **Response**: `201 Created`

### `PATCH /api/v1/finance/fee-categories/{id}/status`
- **Description**: Toggle status between `ACTIVE` and `INACTIVE`.
- **Response**: `200 OK`

---

## 2. Fee Structures & Approval Lifecycle

### `GET /api/v1/finance/fee-structures`
- **Query Parameters**: `program`, `academicYear`, `semester`, `status`.
- **Response**: `200 OK` — Array of `FeeStructure`.

### `POST /api/v1/finance/fee-structures`
- **Request Body**:
```json
{
  "code": "FS-BTECH-CSE-2026-S5",
  "name": "B.Tech CSE Sem 5 Standard Fee 2026",
  "program": "B.Tech Computer Science & Engineering",
  "department": "Computer Science & Engineering",
  "academicYear": "2026-2027",
  "semester": 5,
  "components": [
    { "title": "Tuition & Academics", "categoryName": "Tuition Fee", "amount": 65000, "isMandatory": true },
    { "title": "Examination Fee", "categoryName": "Examination Fee", "amount": 2500, "isMandatory": true }
  ],
  "grossTotal": 67500
}
```
- **Response**: `201 Created` (`status: "DRAFT"`)

### `POST /api/v1/finance/fee-structures/{id}/submit`
- **Transitions**: `DRAFT` → `PENDING_APPROVAL`.

### `POST /api/v1/finance/fee-structures/{id}/approve`
- **Transitions**: `PENDING_APPROVAL` → `APPROVED`.

### `POST /api/v1/finance/fee-structures/{id}/activate`
- **Transitions**: `APPROVED` → `ACTIVE`.

### `POST /api/v1/finance/fee-structures/{id}/retire`
- **Transitions**: `ACTIVE` → `RETIRED`.

---

## 3. Student Fee Assignments

### `GET /api/v1/finance/assignments`
- **Query Parameters**: `studentId`, `feeStructureId`, `status`.
- **Response**: `200 OK` — Array of `StudentFeeAssignment`.

### `POST /api/v1/finance/assignments`
- **Request Body**:
```json
{
  "studentId": "std-001",
  "feeStructureId": "fs-btech-cse-s5",
  "scholarshipId": "sch-merit-25",
  "notes": "Academic merit scholarship applied"
}
```
- **Response**: `201 Created`

### `POST /api/v1/finance/assignments/bulk`
- **Request Body**:
```json
{
  "feeStructureId": "fs-btech-cse-s5",
  "studentIds": ["std-001", "std-002", "std-003"]
}
```
- **Response**: `200 OK` with counts of assigned students.

---

## 4. Invoices & Billing Ledger

### `GET /api/v1/finance/invoices`
- **Query Parameters**: `studentId`, `status`, `search`, `fromDate`, `toDate`.
- **Response**: `200 OK` — Array of `Invoice`.

### `POST /api/v1/finance/invoices`
- **Request Body**:
```json
{
  "studentId": "std-001",
  "studentName": "Aarav Patel",
  "program": "B.Tech Computer Science & Engineering",
  "department": "Computer Science & Engineering",
  "semester": 5,
  "dueDate": "2026-10-31",
  "grossAmount": 87500
}
```
- **Response**: `201 Created` (`status: "ISSUED"`)

### `POST /api/v1/finance/invoices/{id}/cancel`
- **Request Body**:
```json
{
  "reason": "Student transferred to another branch"
}
```
- **Response**: `200 OK` (`status: "CANCELLED"`)

---

## 5. Payments, Allocations & Receipts

### `GET /api/v1/finance/payments`
- **Query Parameters**: `studentId`, `invoiceId`, `paymentMethod`, `status`.
- **Response**: `200 OK` — Array of `Payment`.

### `POST /api/v1/finance/payments`
- **Request Body**:
```json
{
  "studentId": "std-001",
  "invoiceId": "inv-2026-001",
  "amount": 25000,
  "paymentMethod": "UPI",
  "referenceNumber": "UPI/20261015/09812",
  "bankName": "HDFC Bank",
  "notes": "First installment paid"
}
```
- **Validation**: `amount > 0` and `amount <= invoice.outstandingBalance`.
- **Side Effects**: Automatically generates a `PaymentAllocation`, increments `invoice.paidAmount`, decrements `invoice.outstandingBalance`, updates `invoice.status` to `PARTIALLY_PAID` or `PAID`, and automatically generates a `Receipt`.
- **Response**: `201 Created`

### `GET /api/v1/finance/receipts`
- **Response**: `200 OK` — Array of `Receipt`.

### `GET /api/v1/finance/receipts/{id}`
- **Response**: `200 OK` — Single `Receipt` with full voucher formatting.

---

## 6. Scholarships & Concessions

### `GET /api/v1/finance/scholarships`
- **Response**: `200 OK` — Array of `Scholarship`.

### `POST /api/v1/finance/scholarships`
- **Request Body**:
```json
{
  "code": "SCH-SPORTS-50",
  "name": "State Sports Excellence Award",
  "type": "SPORTS",
  "description": "50% tuition discount for university athletes",
  "discountType": "PERCENTAGE",
  "value": 50,
  "maxDiscountAmount": 40000,
  "eligibilityCriteria": "National/State representation",
  "academicYear": "2026-2027"
}
```
- **Response**: `201 Created`

---

## 7. Refunds & Reimbursements

### `GET /api/v1/finance/refunds`
- **Response**: `200 OK` — Array of `Refund`.

### `POST /api/v1/finance/refunds`
- **Request Body**:
```json
{
  "studentId": "std-002",
  "invoiceId": "inv-2026-002",
  "paymentId": "pay-2026-002",
  "requestedAmount": 5000,
  "reason": "Hostel room deposit refund upon room vacancy"
}
```
- **Response**: `201 Created` (`status: "REQUESTED"`)

### `POST /api/v1/finance/refunds/{id}/review`
- **Request Body**:
```json
{
  "action": "APPROVE",
  "approvedAmount": 5000,
  "reviewerNotes": "Verified clearance from hostel warden"
}
```
- **Response**: `200 OK` (`status: "APPROVED"`)

### `POST /api/v1/finance/refunds/{id}/process`
- **Description**: Triggers final electronic bank transfer disbursement.
- **Response**: `200 OK` (`status: "PROCESSED"`)

---

## 8. Financial Intelligence & Reporting

### `GET /api/v1/finance/dashboard-summary`
- **Response**: `200 OK` returning `FinanceDashboardSummary` with KPI totals, debt aging distribution, collection trends, program outstandings, operational queues, and activity stream.

### `POST /api/v1/finance/reports`
- **Request Body**:
```json
{
  "reportType": "AGING",
  "startDate": "2026-01-01",
  "endDate": "2026-12-31"
}
```
- **Response**: `200 OK` returning columnar dataset for CSV export and audit analysis.
