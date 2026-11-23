# CampusOS Forensic Audit Logging & Integrity Architecture

## 1. Objective & Design Principles

CampusOS maintains a tamper-evident, immutable forensic audit trail recording all security-relevant, financial, academic, and administrative actions across all 11 ERP modules.

Each audit record answers:
- **WHO:** `user_id` of the authenticated actor (or `None` for unauthenticated system events).
- **WHAT:** `action` drawn strictly from the canonical `AuditEventCategory` taxonomy.
- **WHEN:** `created_at` timestamp in UTC with microsecond precision.
- **WHERE:** `ip_address`, `user_agent`, and `route_endpoint`.
- **WHICH ENTITY & RECORD:** `entity_type` and `entity_id`.
- **BEFORE & AFTER:** `old_values_json` and `new_values_json` with sensitive values scrubbed.
- **WHY:** `business_context` explaining operational rationale.
- **CORRELATION:** `correlation_id` matching the incoming `X-Request-ID`.

---

## 2. Standard Event Taxonomy (`AuditEventCategory`)

CampusOS standardizes audit events into canonical categories:

### Identity & Authentication
- `AUTH_LOGIN`: Successful user authentication session establishment.
- `AUTH_LOGIN_FAILED`: Failed authentication attempt.
- `AUTH_LOGOUT`: Session termination and cookie revocation.
- `AUTH_REFRESH`: Token rotation and refresh.
- `AUTH_PASSWORD_CHANGED`: Direct password change by authenticated user.
- `AUTH_PASSWORD_RESET`: Password reset completed via reset token.

### User & Permission Governance
- `USER_CREATED`: New institutional staff, faculty, or student account provisioned.
- `USER_UPDATED`: Profile or status changes.
- `USER_SUSPENDED`: User access revoked or locked.
- `ROLE_CHANGED`: Role assignment or elevation.
- `PERMISSION_CHANGED`: Atomic PBAC permission assignment modified.

### People Domain
- `STUDENT_CREATED`: Student enrolled or registered.
- `STUDENT_UPDATED`: Profile or academic standing update.

### Documents & Certificates
- `DOCUMENT_UPLOADED`: New document stored with SHA-256 digest.
- `DOCUMENT_VERIFIED`: Administrative verification approval.
- `DOCUMENT_REJECTED`: Verification rejection with mandatory rationale.
- `DOCUMENT_REVOKED`: Previously approved document revoked.
- `CERTIFICATE_ISSUED`: Institutional certificate or diploma generated.
- `CERTIFICATE_REVOKED`: Certificate invalidated.

### Academics & Examinations
- `EXAM_FINALIZED`: Examination results approved and finalized.
- `EXAM_PUBLISHED`: Results published to student portal.
- `EXAM_REVOKED`: Examination evaluation amended or retracted.

### Finance & Billing
- `INVOICE_CREATED`: Institutional invoice generated.
- `PAYMENT_RECORDED`: Fee payment transaction processed.
- `REFUND_CREATED`: Financial refund processed.

### Career & Placement
- `PLACEMENT_UPDATED`: Placement offer, status, or drive updated.

### AI & Intelligence
- `AI_QUERY`: Natural language query orchestrated.
- `AI_TOOL_EXECUTED`: Domain tool executed by intelligence assistant.

### SaaS Tenant Lifecycle
- `TENANT_CREATED`: New institutional tenant provisioned.
- `TENANT_SUSPENDED`: Institution access suspended.
- `TENANT_ARCHIVED`: Institution access blocked and marked for retention.

### Security Incidents
- `SECURITY_RATE_LIMIT`: Throttling threshold breached.
- `SECURITY_ACCESS_DENIED`: Unauthorized permission or cross-tenant attempt.
- `SECURITY_CSRF_FAILURE`: Origin mismatch or forbidden cross-origin mutation.

---

## 3. Sensitive Payload Masking

The audit engine automatically routes all `old_values_json`, `new_values_json`, and `business_context` dictionaries through `mask_sensitive_dict()`:
- Passwords (`password`, `password_hash`, `hashed_password`) are replaced with `"[REDACTED]"`.
- Tokens (`token`, `access_token`, `refresh_token`, `jwt`) are replaced with `"[REDACTED]"`.
- Financial credentials (`card_number`, `cvv`, `payment_reference`) are sanitized.
- Plaintext secrets never enter the database audit log.

---

## 4. Immutability & Access Control

- **Database-Level Immutability:** Audit tables have no application-level `DELETE` or `UPDATE` routes. Once written, an audit log row cannot be altered.
- **Tenant Isolation:** Tenant administrators can only query audit logs where `tenant_id == current_tenant.id`. Cross-tenant audit querying is blocked at the repository level.
- **Platform Audits:** Global platform events (e.g. tenant provisioning) have `tenant_id = NULL` and are accessible solely by Platform Super Administrators with `platform:tenants:manage` permission.

---

## 5. Retention & Archival Policies

| Environment | Active Log Retention | Archival Cold Storage |
| :--- | :--- | :--- |
| **Development** | 7 days | Not archived |
| **Staging** | 30 days | Optional snapshot |
| **Production** | 365 days (hot DB) | 7 years (encrypted S3/GCS parquet) |

Retention cleanup is managed via scheduled platform operations (`TenantJobRunner`), never through direct API mutations.
