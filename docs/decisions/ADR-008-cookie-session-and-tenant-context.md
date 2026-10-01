# ADR-008: HttpOnly Cookie Sessions, Argon2id Security, and Request-Scoped Tenant Isolation

## Status
**Accepted**

## Context
CampusOS is an enterprise operating system for higher education institutions that governs confidential student records, financial transactions, examination results, and institutional assets. An authentication and authorization architecture is required that provides:

1. **Robust Browser Security**: Complete protection against token theft via Cross-Site Scripting (XSS).
2. **State-of-the-Art Credential Storage**: Resilience against GPU-accelerated brute force and offline dictionary attacks.
3. **Rigorous Multi-Tenant Isolation**: Elimination of cross-tenant data leakage or tenant impersonation.
4. **Session Revocation**: Ability to invalidate sessions instantly upon logout, password change, or administrative lockout.
5. **Decoupled Identity and Person Profiles**: Unified user accounts capable of binding to multiple personas (student, faculty, staff, guardian).

## Decision

### 1. Argon2id Password Hashing
We adopt **Argon2id** (the winner of the Password Hashing Competition) as the canonical password hashing algorithm via `passlib[argon2]`:
- Memory cost: 65,536 KiB (64 MB)
- Time cost: 3 iterations
- Parallelism: 4 threads
- Constant-time verification is enforced. For non-existent accounts during login, a pre-computed dummy Argon2id hash is verified to ensure identical CPU consumption and prevent timing-attack account enumeration.

### 2. Session & Token Strategy: HttpOnly Cookies with Server Tracking
Authentication tokens are never stored in browser `localStorage` or `sessionStorage`:
- **Access Token**: Short-lived JSON Web Token (15-minute expiration) carrying user UUID, primary tenant UUID, and cryptographic signature (`HS256`).
- **Refresh Session**: Long-lived opaque token (7-day expiration) hashed with SHA-256 and tracked in the `people_user_sessions` database table.
- **Cookie Security Parameters**:
  - `HttpOnly`: Inaccessible to client JavaScript.
  - `SameSite=Lax`: Mitigates Cross-Site Request Forgery (CSRF).
  - `Secure`: Transmitted only over HTTPS in production environments.
  - `Path=/`: Uniformly available across API endpoints.
- **Session Revocation**: Logging out or changing passwords immediately marks database sessions as revoked (`is_revoked=True`), invalidating any future refresh attempts.

### 3. Identity vs. Profile Decoupling
We enforce the single canonical identity pattern:
- `people_users` contains only authentication, security status (`INVITED`, `ACTIVE`, `SUSPENDED`, `LOCKED`, `DISABLED`), failed login counters, and credentials.
- Institutional domain profiles (`StudentProfile`, `FacultyProfile`, `StaffProfile`, `GuardianProfile`) reference `User.id` via foreign keys.
- A single person can transition from Student to Faculty or Alum without creating multiple authentication accounts.

### 4. Policy-Based Access Control (PBAC)
- Permissions are atomic strings formatted as `domain:resource:action` (e.g., `academics:courses:read`, `finance:invoices:create`).
- Roles (`people_roles`) act as named collections of permissions mapped through `people_role_permissions`.
- User role assignments (`people_user_roles`) support institutional hierarchy (optional `campus_id` and `department_id` scoping).
- Route dependencies (`require_permission`, `require_permissions`) enforce authorization at the backend gateway. Client-side UI checks are strictly treated as cosmetic UX conveniences.

### 5. Multi-Tenant Context Resolution
- The incoming client's tenant context is derived strictly from the verified JWT payload and validated against the database.
- A client-supplied `tenant_id` header or body parameter is **never trusted** without cryptographic validation.
- Request-scoped state is managed via Python `ContextVar` (`TenantContext`), ensuring thread-safe, coroutine-safe database filtering.

## Consequences
- **Positive**:
  - XSS attacks cannot extract session credentials.
  - Session revocation is immediate and enforceable from the server.
  - Constant-time verification prevents username enumeration.
  - PBAC granularity allows fine-grained role assignment without schema mutations.
- **Negative / Trade-offs**:
  - Server-side session tracking incurs a database query during refresh token rotation.
  - Cross-domain API deployment requires proper CORS `Access-Control-Allow-Credentials: true` and synchronized cookie domain settings.
