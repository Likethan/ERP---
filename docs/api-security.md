# CampusOS API Platform Security & Threat Mitigation

## Overview

The CampusOS API platform is built to defend against common API vulnerabilities, multi-tenant leakage, credential compromise, and privilege escalation.

---

## 1. Threat Matrix & Defense Controls

| Threat Vector | Mitigation Architecture | Verification Test |
| :--- | :--- | :--- |
| **Insecure Direct Object References (IDOR)** | Tenant filter is injected at the database level (`where tenant_id == consumer.tenant_id`). Resource queries in Tenant A can never return data belonging to Tenant B. | `test_cross_tenant_idor_prevention` |
| **Scope Escalation** | Scopes are validated using `ScopeResolver`. Requesting `students.read` does not permit `finance.write` or `students.write`. High-risk scopes require explicit approval. | `test_scope_escalation_blocked` |
| **Credential Replay / Forgery** | Plaintext keys are never stored. Salted HMAC comparison is performed using constant-time algorithms. Revoked and expired credentials fail authentication immediately. | `test_revoked_key_rejected` |
| **Cross-Tenant Credential Substitution** | Credentials belong to an application, which is bound to a specific tenant ID. The resolved tenant context is locked to the credential's owning institution. | `test_cross_tenant_idor_prevention` |
| **Secret Disclosure / Mass Assignment** | Read responses use strict Pydantic schemas. Plaintext secrets are omitted from all GET requests. Internal ORM attributes (`password_hash`, `salt`) are never serialized. | `test_credential_secret_never_exposed_on_read` |
| **Rate-Limit / Quota Bypass** | Rate limits and quotas are tracked per `Application ID`. Creating multiple keys for the same application does not reset or increase limits. | `test_rate_limit_sliding_window_enforcement` |
| **Concurrent Mutation Replay** | Sensitive mutations require an `Idempotency-Key` header with request hashing. Duplicate calls replay cached results without re-executing logic; concurrent calls yield `409 Conflict`. | `test_payment_idempotency_enforcement` |
| **Personally Identifiable Information (PII) Leakage**| The gateway applies automated masking (`mask_email`, `mask_phone`) to student and faculty contact details. | `test_full_gateway_flow_students_api` |

---

## 2. Privacy-Aware Telemetry

Usage logging adheres strictly to the Data Governance and Privacy guidelines established in Step 19:

1. **No Sensitive Payloads**: Request and response bodies are **never** logged by default.
2. **Credential Sanitization**: The gateway strips `Authorization`, `X-API-Key`, and cookie headers prior to recording telemetry.
3. **IP Anonymization**: Client IP addresses are truncated to `/24` (IPv4) or `/48` (IPv6) before persistence in analytics tables.
4. **Aggregate Metric Computation**: Raw request logs are rolled up into hourly aggregates (`requests_total`, `latency_avg`, `p95`, `p99`, `status_breakdown`) and pruned according to the institutional retention window.

---

## 3. Strict Input & Output Serialization

Internal SQLAlchemy ORM models are never returned directly to external callers. Every domain endpoint produces explicit `Public*Response` DTO models:

- `PublicStudentResponse`
- `PublicCourseResponse`
- `PublicAttendanceRecord`
- `PublicExamResultSummary`
- `PublicInvoiceResponse`
- `PublicPaymentResponse`

Internal operational fields (e.g. `audit_trail`, `created_by`, `internal_notes`, `db_version`) are stripped at the serialization boundary.
