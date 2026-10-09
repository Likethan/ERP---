# CampusOS Production Security Checklist

A comprehensive verification checklist for enterprise college ERP deployment. Every item must be audited and verified before declaring production readiness.

---

## 1. Secrets & Credentials Management
- [x] **No hardcoded secrets:** Zero API keys, passwords, JWT secrets, or cloud tokens committed to source code or git history.
- [x] **Environment variable externalization:** All sensitive credentials injected via platform secret managers or root-protected `.env.production`.
- [x] **No secrets in container images:** Dockerfiles use multi-stage builds and exclude `.env` files via `.dockerignore`.
- [x] **No private secrets in frontend bundles:** Only `NEXT_PUBLIC_*` variables are exposed to client-side code; all database, Redis, AI, and JWT secrets remain strictly server-side.
- [x] **Cryptographic strength:** `SECRET_KEY` is a 32+ character high-entropy random string generated via cryptographic PRNG.

---

## 2. Network, TLS & Transport Security
- [x] **Strict HTTPS enforcement:** All HTTP traffic automatically redirected to HTTPS (port 443).
- [x] **HTTP Strict Transport Security (HSTS):** `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload` enabled.
- [x] **TLS configuration:** TLS 1.2 and 1.3 only; weak ciphers disabled.
- [x] **Reverse proxy headers:** Nginx / cloud load balancer terminates TLS and passes validated `X-Forwarded-Proto`, `X-Forwarded-For`, and `X-Request-ID` headers.

---

## 3. Cookie & Session Security
- [x] **`Secure` flag:** All authentication and session cookies marked `Secure=True` in production.
- [x] **`HttpOnly` flag:** Refresh tokens and session tokens inaccessible to client-side JavaScript.
- [x] **`SameSite` attribute:** Set to `Lax` (or `Strict`) to mitigate Cross-Site Request Forgery (CSRF).
- [x] **Token lifetimes:** Access tokens expire within 15 minutes; refresh tokens expire within 7 days and support server-side revocation.

---

## 4. CORS & Cross-Origin Controls
- [x] **Explicit origin whitelist:** `CORS_ORIGINS` explicitly lists allowed frontend origins (e.g., `["https://app.campus.edu"]`).
- [x] **No wildcard with credentials:** Wildcard `*` origin strictly rejected when `allow_credentials=True`.
- [x] **No localhost in production:** Startup validation rejects development origins (`localhost`, `127.0.0.1`) in production mode.

---

## 5. Security Headers
- [x] `X-Frame-Options: SAMEORIGIN` (prevents clickjacking).
- [x] `X-Content-Type-Options: nosniff` (prevents MIME sniffing).
- [x] `Referrer-Policy: strict-origin-when-cross-origin`.
- [x] `Permissions-Policy: camera=(), microphone=(), geolocation=()`.
- [x] Content Security Policy (CSP) tailored for Next.js and API endpoints.

---

## 6. Authentication & RBAC / PBAC
- [x] **Password hashing:** Cryptographically strong password hashing using Argon2id / bcrypt with individual salts.
- [x] **Brute-force protection:** Rate limiting applied to `/api/v1/auth/login` (maximum 10 requests per minute per IP/account).
- [x] **Server-side authorization:** Every route guarded by permission dependency checks (`require_permission(...)`), never trusting client-asserted roles.
- [x] **Failed attempt tracking:** Repeated failed authentication attempts trigger security alerts and automated account locking.

---

## 7. Multi-Tenant SaaS Isolation
- [x] **Request-scoped context:** Tenant identity resolved from validated JWT claims and propagated via Python `ContextVar`.
- [x] **Tenant repository enforcement:** All database queries automatically filter by `institution_id == current_tenant.id`.
- [x] **Cross-tenant relationship prohibition:** Foreign keys across different tenant boundaries are rejected at the application and schema levels.
- [x] **Tenant cache partition:** Redis cache keys prefixed with `tenant:{tenant_id}:{namespace}:{key}`.
- [x] **Tenant storage partition:** File paths strictly structured as `tenants/{tenant_id}/{module}/{year}/{file_id}.ext`.

---

## 8. Database & Migration Security
- [x] **Connection pooling:** SQLAlchemy configured with explicit `pool_size=25`, `max_overflow=15`, `pool_timeout=30`, `pool_recycle=1800`.
- [x] **Statement timeout:** Long-running queries bounded by statement timeout (30 seconds) to prevent Denial of Service.
- [x] **Controlled migrations:** Alembic migrations executed as dedicated pre-deployment steps (`scripts/migrate.py run`), never silently during application server boot.
- [x] **Sanitized SQL errors:** Raw database errors caught and sanitized in exception handlers to prevent schema leakage.

---

## 9. Object Storage & Upload Security
- [x] **Private bucket:** Object storage buckets are entirely private; direct public internet access is prohibited.
- [x] **Short-lived signed URLs:** Client downloads use temporary presigned URLs expiring within 300 seconds.
- [x] **MIME type verification:** File headers validated against expected document signatures.
- [x] **Path traversal prevention:** Filenames sanitized to prevent directory traversal (`../`).
- [x] **Payload limits:** Maximum upload size strictly enforced (25 MB for multipart, 2 MB for JSON).

---

## 10. Container & Execution Security
- [x] **Non-root execution:** Containers run as unprivileged users (`campusos:campusos` UID 10001, `nextjs:nodejs` UID 10001).
- [x] **Minimal base images:** Python 3.11-slim and Node 20-alpine.
- [x] **Deterministic dependencies:** Pinned lockfiles (`package-lock.json`, `requirements.txt`).
- [x] **Resource limits:** CPU and memory quotas enforced via Docker Compose / container orchestrator.

---

## 11. Observability, Logging & Audit
- [x] **Structured JSON logs:** Logs formatted as machine-readable JSON with ISO timestamps and log levels.
- [x] **Secret redaction:** Passwords, tokens, cookies, and document contents scrubbed from log statements.
- [x] **Request correlation:** `X-Request-ID` propagated through API, services, database queries, and background tasks.
- [x] **Liveness & readiness probes:** `/health/live` and `/health/ready` endpoints exposed for monitoring without leaking internal state.
