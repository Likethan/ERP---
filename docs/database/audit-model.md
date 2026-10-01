# CampusOS — Audit & Tamper-Resistance Architecture

## 1. Audit Principles

In an enterprise operating system managing official educational credentials, grading, and multi-million dollar cash flows, application logs in text files are insufficient for legal compliance and statutory accountability.

CampusOS mandates a **dedicated, database-level immutable audit trail** (`intelligence_audit_logs`).

---

## 2. The 9 Core Audit Dimensions

Every audit entry in CampusOS answers 9 fundamental forensic questions:

```text
┌─────────────────────────────────────────────────────────────┐
│                       CAMPUSOS AUDIT RECORD                 │
├───────────────────┬─────────────────────────────────────────┤
│ 1. WHO            │ Actor User ID, Role, IP Address, Client │
│ 2. WHAT           │ Action (CREATE, UPDATE, APPROVE, etc.)  │
│ 3. WHEN           │ High-precision UTC timestamp            │
│ 4. WHERE          │ API route, internal domain service      │
│ 5. WHICH ENTITY   │ Entity Class (e.g., SemesterExamResult) │
│ 6. WHICH RECORD   │ Entity Primary Key (UUIDv4)             │
│ 7. BEFORE         │ JSON snapshot of modified fields before │
│ 8. AFTER          │ JSON snapshot of modified fields after  │
│ 9. WHY / CONTEXT  │ Authorizing rationale, correlation ID   │
└───────────────────┴─────────────────────────────────────────┘
```

---

## 3. Schema Specification: `intelligence_audit_logs`

```sql
CREATE TABLE intelligence_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE RESTRICT,
    user_id UUID REFERENCES people_users(id) ON DELETE SET NULL,
    action VARCHAR(64) NOT NULL, -- CREATE, UPDATE, DELETE, PUBLISH, APPROVE, REVERSE
    entity_type VARCHAR(64) NOT NULL, -- e.g. StudentProfile, Invoice, Result
    entity_id UUID NOT NULL,
    old_values_json JSONB,
    new_values_json JSONB,
    ip_address VARCHAR(45) NOT NULL,
    user_agent TEXT,
    route_endpoint VARCHAR(255),
    correlation_id UUID NOT NULL,
    business_context TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Fast queries for entity history timelines
CREATE INDEX idx_audit_logs_entity ON intelligence_audit_logs(tenant_id, entity_type, entity_id, created_at DESC);

-- Fast queries for user activity trails
CREATE INDEX idx_audit_logs_user ON intelligence_audit_logs(tenant_id, user_id, created_at DESC);
```

---

## 4. Tamper Resistance and Immutability

1. **Database Revocation of UPDATE and DELETE**:
   ```sql
   -- Audit table permissions in PostgreSQL
   REVOKE UPDATE, DELETE, TRUNCATE ON intelligence_audit_logs FROM campusos_app_role;
   GRANT INSERT, SELECT ON intelligence_audit_logs FROM campusos_app_role;
   ```
2. **Strict Sanitization**:
   - The audit interceptor automatically redacts sensitive authentication credentials (password hashes, JWT tokens, MFA recovery codes) and payment card credentials before writing to `old_values_json` or `new_values_json`.
3. **Correlation ID Tracking**:
   - Every incoming HTTP request or background worker task generates a `correlation_id` (UUID). All database mutations and external calls participating in that transaction inherit this ID, enabling complete distributed tracing.
