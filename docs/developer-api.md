# CampusOS Developer Portal & External API Reference

## Introduction

The **CampusOS Developer Platform** provides structured access to university operational data and transaction workflows. All externally consumable endpoints are published under the prefix:

```text
/api/v1/platform/v1/
```

Access requires an authorized `DeveloperApplication`, approved capability scopes, and valid API credentials.

---

## 1. Authentication

All requests to `/api/v1/platform/v1/*` must present valid credentials using one of the following methods:

### Option A: Header API Key (Recommended)
```http
GET /api/v1/platform/v1/students HTTP/1.1
Host: api.campusos.internal
X-API-Key: cos_live_a1b2c3d4e5f6...
```

### Option B: Authorization Bearer
```http
GET /api/v1/platform/v1/students HTTP/1.1
Host: api.campusos.internal
Authorization: Bearer cos_live_a1b2c3d4e5f6...
```

> **Security Note:** Never pass API keys or client secrets via URL query parameters. Requests with tokens in query strings are rejected immediately.

---

## 2. API Product Catalog

The platform categorizes APIs into modular **API Products**. Use `/api/v1/platform/catalog` to inspect products, routes, and required scopes.

| Product | Base Route | Core Scopes | Description |
| :--- | :--- | :--- | :--- |
| **Students API** | `/api/v1/platform/v1/students` | `students.read` | Student directory, enrollment details, governance masking |
| **Academics API** | `/api/v1/platform/v1/academics` | `academics.read` | Course catalogs, curricula, subject structures |
| **Attendance API** | `/api/v1/platform/v1/attendance` | `attendance.read` | Daily session records, attendance statuses |
| **Examinations API** | `/api/v1/platform/v1/examinations` | `examinations.read` | Schedules, assessments, validated score summaries |
| **Finance API** | `/api/v1/platform/v1/finance` | `finance.read`, `finance.write` | Fee invoices, balances, idempotent payment recording |
| **Campus Events API**| `/api/v1/platform/v1/events` | `events.read`, `events.write` | Event schedules, venue bookings, attendee registration |

---

## 3. Standard Request & Response Patterns

### Pagination (Cursor-based)
List endpoints enforce cursor pagination to prevent denial of service and memory exhaustion:

```http
GET /api/v1/platform/v1/students?limit=25&cursor=ADM-2024-00120 HTTP/1.1
```

Response format:
```json
{
  "items": [...],
  "next_cursor": "ADM-2024-00145",
  "has_more": true,
  "total_count": null
}
```

### Field-Level Privacy Masking
Sensitive fields are governed by CampusOS Data Governance policies. For unmasked access, dedicated high-risk permissions must be granted to the application owner.

Example masked student output:
```json
{
  "id": "e2a1b4c6-...",
  "student_id": "ADM-2024-00120",
  "first_name": "Alice",
  "last_name": "Johnson",
  "email": "a***e@apextech.edu",
  "phone_number": "+91******3299",
  "status": "ACTIVE",
  "enrollment_date": "2022-08-01"
}
```

---

## 4. Mutation Idempotency

All destructive or financially significant endpoints (e.g. `POST /api/v1/platform/v1/finance/payments`) require the `Idempotency-Key` HTTP header:

```http
POST /api/v1/platform/v1/finance/payments HTTP/1.1
X-API-Key: cos_live_...
Idempotency-Key: pay-txn-uuid-8829-11
Content-Type: application/json

{
  "invoice_id": "b3e0c7a2-...",
  "amount": 2500.00,
  "payment_method": "UPI",
  "transaction_reference": "TXN-UPI-9948271"
}
```

- **First Attempt**: Request is processed and result is committed.
- **Subsequent Identical Attempts**: Original cached response (e.g. `201 Created` with receipt) is returned without re-executing business logic.
- **Concurrent In-Flight Attempts**: Server responds with `409 Conflict`.
- **Key Reused with Changed Payload**: Server responds with `422 Unprocessable Content`.

---

## 5. Standard Error Format

The API Platform emits consistent, sanitized RFC 7807 compliant JSON error structures:

```json
{
  "error": {
    "code": "INSUFFICIENT_SCOPE",
    "message": "Application does not have granted capability scope 'finance.write'.",
    "details": {
      "required_scope": "finance.write"
    },
    "request_id": "req-c1d4-..."
  }
}
```
Internal error traces, stack traces, and SQL expressions are stripped before transmission.
