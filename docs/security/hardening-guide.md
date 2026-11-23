# CampusOS Security Architecture & Hardening Guide

## 1. Executive Summary

CampusOS is engineered according to **Zero Trust**, **Least Privilege**, and **Defense-in-Depth** principles. The backend enforces security invariants at every layer of the request lifecycle, ensuring multi-tenant isolation, cryptographic integrity, secret protection, and attack resistance prior to production deployment.

```text
Incoming Internet Request
      ↓
[Security Headers & Request Correlation] (nosniff, DENY, CSP, X-Request-ID)
      ↓
[Rate Limiting & Brute Force Defense] (Sliding Window, Category Limits, 429)
      ↓
[Payload Size Enforcement] (413 Payload Too Large)
      ↓
[CORS & Origin Validation] (Strict Origin Allowlist, No Wildcards in Prod)
      ↓
[Authentication & Session Validation] (Argon2id, JWT Cryptographic Verification)
      ↓
[Authoritative Tenant Resolution] (Active Membership, Status Checks: ACTIVE, SUSPENDED, ARCHIVED)
      ↓
[PBAC Authorization] (Fine-Grained Permission Enforcement)
      ↓
[Input Sanitization & Schema Validation] (Pydantic, Strict Pagination Upper Bounds)
      ↓
[Tenant-Scoped Domain Service & Repository] (Invariant tenant_id filtering)
      ↓
[Database Operations & Sanitization] (Bounded Pool, SQL Exception Sanitization)
      ↓
[Audit, Security Events & Observability] (Scrubbed Metadata, Metrics, Tracing)
```

---

## 2. Authentication & Credential Security

### Password Storage & Policy
- **Algorithm:** Argon2id via `passlib[argon2]`.
- **Complexity Requirements:** Minimum 8 characters, at least one uppercase letter, at least one lowercase letter, and at least one digit or special character.
- **Timing Attack Mitigation:** Dummy password verification with fixed Argon2 hash execution for non-existent users ensures equal CPU consumption, eliminating user enumeration via response latency.
- **Account Lockout:** 5 consecutive failed login attempts trigger a 15-minute temporary lockout (`ACCOUNT_LOCKED`) and record an `AUTH_BRUTE_FORCE_SUSPECTED` security alert.

### Token Architecture
- **Format:** Cryptographically signed JSON Web Tokens (JWT).
- **Algorithm:** Strictly enforced symmetric `HS256` (or configured algorithm). Unsigned tokens (`alg=none`) or algorithm confusion attempts are rejected.
- **Lifetimes:**
  - Access Token: 15 minutes (`ACCESS_TOKEN_EXPIRE_MINUTES`).
  - Refresh Token: 7 days (`REFRESH_TOKEN_EXPIRE_DAYS`).
- **Transport Channels:**
  - Web Browsers: Secure `HttpOnly`, `SameSite=Lax`, and `Secure` (in production) cookies.
  - Programmatic & Mobile: `Authorization: Bearer <token>` header.

### CSRF & CORS Defense
- **CSRF Strategy:** State-changing requests via cookies are protected by `SameSite=Lax` browser cookie boundaries and explicit CORS origin checks. Bearer token programmatic requests are stateless and immune to CSRF.
- **CORS Strategy:** Explicit allowlist (`CORS_ORIGINS`). Startup validation rejects wildcard `*` origins in production when credentials are enabled.

---

## 3. Authorization & PBAC

- **Architecture:** Policy-Based Access Control (PBAC). Every route specifies granular permission codes (e.g., `students.read`, `students.create`, `invoices.manage`).
- **Platform Separation:** Strict architectural wall between Platform Super Administrators (`/api/v1/platform/tenants`) and Institutional Tenant Administrators (`/api/v1/*`). Tenant administrators cannot elevate privileges to access platform APIs.

---

## 4. Multi-Tenant Boundary & Anti-Spoofing

- **Authoritative Server Resolution:** Tenant identity is extracted authoritatively from the verified JWT subject and database membership records.
- **Payload Spoofing Rejection:** Client-supplied `{"tenant_id": "other"}` in request bodies or query parameters cannot override server context.
- **Cross-Tenant Foreign Keys:** All entity relationships (e.g. Student → Program) validate that both entities share the active tenant ID, raising `CrossTenantRelationshipException` (`400 Bad Request`) on violation.
- **IDOR Protection:** Cross-tenant resource lookups return `404 Not Found` rather than `403`, preventing information leakage regarding resource existence.

---

## 5. HTTP Security Headers & Middlewares

The following headers are injected on all API responses:
- `X-Content-Type-Options: nosniff` (prevents MIME confusion attacks)
- `X-Frame-Options: DENY` (clickjacking protection)
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: geolocation=(), camera=(), microphone=()`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains` (enabled in production/HTTPS)
- `Content-Security-Policy: default-src 'self'; frame-ancestors 'none';` (strict frame restriction)

---

## 6. Rate Limiting & Resource Protection

- **Algorithm:** In-memory sliding window rate limiter (`SlidingWindowRateLimiter`).
- **Policy Tiering:**
  - Authentication (`/auth/login`, `/auth/forgot-password`): 10 req/min.
  - Search & Export endpoints: 30 req/min.
  - General API endpoints: 120 req/min.
  - AI & Intelligence queries: 60 req/min per user, 500 req/min per tenant.
- **Throttling Response:** Returns `429 Too Many Requests` with `Retry-After: <seconds>` header and `RATE_LIMIT_EXCEEDED` error envelope. Records `SECURITY_RATE_LIMIT` alert.

---

## 7. Request Payload & Size Limits

- **JSON Body Limit:** 2 MB (`MAX_JSON_BODY_BYTES`).
- **Multipart Upload Limit:** 25 MB (`MAX_MULTIPART_BYTES`).
- Payloads exceeding bounds return `413 Payload Too Large` via `PayloadSizeLimitMiddleware`.
- List endpoints enforce pagination upper bounds (`page_size <= 100` or `200`) preventing memory exhaustion.

---

## 8. Data Classification & Secret Redaction

| Classification | Examples | Handling & Protection |
| :--- | :--- | :--- |
| **Public** | Institution codes, catalog descriptions, health status | Unrestricted |
| **Internal** | Academic calendars, room numbers, course schedules | Authenticated tenant users |
| **Confidential** | Student grades, financial ledgers, placement offers | Authorized PBAC roles only |
| **Restricted** | Passwords, tokens, API keys, private certificates | Encrypted at rest, never logged, redacted in API errors |

### Centralized Sanitization Engine (`app.core.sanitizer`)
- `mask_sensitive_dict`: Recursively traverses data structures and redacts passwords, tokens, API keys, hashes, and credit cards with `[REDACTED]`.
- `mask_sensitive_string`: Redacts credentials embedded in database URLs and Bearer token headers.
- **Database Error Sanitizer:** Catches raw `SQLAlchemyError` / `DBAPIError` exceptions and strips internal table names, column structures, and SQL queries before returning a safe `DATABASE_ERROR` response with a traceable `request_id`.

---

## 9. File & Document Storage Security

- **Supported MIME Types:** PDF, JPEG, PNG, WEBP, DOCX, XLSX, TXT, CSV.
- **Integrity:** Mandatory SHA-256 content checksum computation.
- **Filename Sanitization:** `sanitize_filename` strips path separators (`/`, `\`), directory traversal patterns (`..`), null bytes (`\x00`), and control characters.
- **Partitioning:** Storage references strictly validate tenant key confinement (`tenants/{tenant_id}/...`). Path traversal outside the storage root raises `ValidationException`.

---

## 10. AI & Intelligence Engine Security

- **Approved Tool Registry:** Natural language assistant selects tools exclusively from a pre-approved registry. Direct arbitrary SQL queries or file access by AI is strictly impossible.
- **PBAC & Tenant Enforcement:** Every tool execution validates the user's active tenant and permission set before executing domain services.
- **Prompt Sanitization:** Queries exceeding 2000 characters are rejected. Output structures validate against strict Pydantic models.

---

## 11. Production Configuration Safeguards

The application lifespan calls `settings.validate_production_configuration()` upon startup:
- Fails startup if `ENVIRONMENT == "production"` and `DEBUG == True`.
- Fails startup if `SECRET_KEY` is a default placeholder or shorter than 32 characters.
- Fails startup if `CORS_ORIGINS` contains wildcard `*` with credentials enabled.
