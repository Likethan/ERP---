# CampusOS — Authentication, Identity & Role-Based Access Control Specification

## 1. Executive Summary

This document specifies the production security foundation for CampusOS ERP, establishing the identity, authentication, session management, and authorization subsystem.

CampusOS adopts a **Zero-Trust, Multi-Tenant Defense-in-Depth** architecture:
- Passwords are encrypted using **Argon2id**.
- Client credentials and tokens are dispatched exclusively via **HttpOnly, SameSite=Lax, Secure** cookies.
- Authorization is governed by fine-grained **Policy-Based Access Control (PBAC)** mapped to institutional **Roles**.
- Multi-tenant isolation is enforced at the request lifecycle boundary using cryptographic validation and context isolation.

---

## 2. Authentication Model

### 2.1 The Authentication Flow
```text
Client submits POST /api/v1/auth/login
  ↓
Normalize email & retrieve user by unique email
  ↓ (If user not found: perform dummy Argon2id verification to prevent timing attacks)
Verify account status (check if LOCKED, SUSPENDED, DISABLED, or INVITED)
  ↓
Verify password against stored Argon2id hash
  ↓ (On failure: increment failed_login_attempts; lock account for 15 mins after 5 failures)
Reset failed_login_attempts to 0 & update last_login_at
  ↓
Generate short-lived JWT Access Token (15 min expiry)
Generate cryptographically random 64-char Refresh Token (7 day expiry)
  ↓
Store SHA-256 hash of refresh token in people_user_sessions
Record forensic LOGIN_SUCCESS audit log entry in intelligence_audit_logs
  ↓
Dispatch tokens via HttpOnly cookies (campusos_access_token & campusos_refresh_token)
Return safe user representation (no passwords, no hashes, no token strings)
```

### 2.2 Password Security & Cryptography
- **Algorithm**: Argon2id (`passlib[argon2]`).
- **Parameters**: `m=65536` (64 MB), `t=3` iterations, `p=4` threads.
- **Complexity Policy**:
  - Minimum 8 characters.
  - At least one uppercase ASCII character (`A-Z`).
  - At least one lowercase ASCII character (`a-z`).
  - At least one digit or special symbol (`0-9` or `!@#$%^&*()_+-=[]{}|;:,.<>?`).
- **Timing-Attack Mitigation**:
  When a non-existent email is targeted, `AuthService` executes `verify_password("dummy", _DUMMY_ARGON2_HASH)` against a pre-compiled, valid Argon2id hash. This consumes identical CPU time, preventing attackers from enumerating valid institutional accounts.

### 2.3 Account Lifecycle State Machine
```text
           ┌───────────┐
           │  INVITED  │
           └─────┬─────┘
                 │ (Accept Invitation & Set Password)
                 ▼
           ┌───────────┐  5 Failed Attempts   ┌───────────┐
      ┌───►│  ACTIVE   ├─────────────────────►│  LOCKED   │
      │    └─────┬─────┘                      └─────┬─────┘
      │          │                                  │
      │          │ (Admin or Policy)                │ (Lockout expires or Admin unlock)
      │          ▼                                  ▼
      │    ┌───────────┐                      ┌───────────┐
      └────┤ SUSPENDED │                      │  ACTIVE   │
           └─────┬─────┘                      └───────────┘
                 │
                 ▼
           ┌───────────┐
           │ DISABLED  │
           └───────────┘
```

Valid Transitions:
- `INVITED` → `ACTIVE`: Activated upon credential initialization.
- `ACTIVE` → `LOCKED`: Automatically triggered when `failed_login_attempts >= 5`. Unlocks automatically after 15 minutes or via institutional administrator action.
- `ACTIVE` → `SUSPENDED`: Triggered by student/faculty disciplinary suspension or financial hold.
- `SUSPENDED` → `ACTIVE`: Reinstated by registrar or institutional authority.
- `ACTIVE` | `SUSPENDED` → `DISABLED`: Permanent deactivation upon graduation, faculty retirement, or expulsion.

---

## 3. Session & Token Strategy

### 3.1 Cookie Specifications
| Cookie Name | Scope | Lifetime | Flags |
| :--- | :--- | :--- | :--- |
| `campusos_access_token` | Path `/` | 15 minutes | `HttpOnly`, `SameSite=Lax`, `Secure` (prod) |
| `campusos_refresh_token` | Path `/` | 7 days | `HttpOnly`, `SameSite=Lax`, `Secure` (prod) |

### 3.2 Token Storage Rule
> [!CAUTION]
> Under no circumstances may client-side JavaScript store authentication tokens in `localStorage` or `sessionStorage`. Browser-accessible storage is vulnerable to token theft via Cross-Site Scripting (XSS). HttpOnly cookies cannot be read by JavaScript.

### 3.3 Server-Side Session Tracking (`people_user_sessions`)
- Every issued refresh token is hashed using `SHA-256` before persistence.
- Logging out (`POST /api/v1/auth/logout`) sets `is_revoked = True` for the active session.
- Changing passwords (`POST /api/v1/auth/change-password`) invalidates **all active sessions** for that user across all devices.

---

## 4. Identity & Person Decoupling

In CampusOS, authentication credentials belong strictly to the canonical `User` entity (`people_users`):
```text
              User (people_users)
                 │ (1:1 / 1:Many)
        ┌────────┼────────┬────────┐
        ▼        ▼        ▼        ▼
     Student  Faculty   Staff   Guardian
     Profile  Profile  Profile  Profile
```
- A person does not have separate logins for their student and staff personas.
- The `User` represents the identity; institutional roles and profiles represent the capacity in which they interact with the institution.

---

## 5. Policy-Based Access Control (PBAC)

### 5.1 Permission Format
Permissions are atomic, structured strings conforming to:
```text
{domain}:{resource}:{action}
```
Examples:
- `academics:courses:read`
- `academics:courses:manage`
- `attendance:records:write`
- `attendance:corrections:approve`
- `examination:marks:write`
- `finance:invoices:create`
- `finance:payments:record`
- `placement:drives:manage`
- `audit:logs:read`

### 5.2 System Roles & Permission Bundles
System roles provide standard templates:
- `SUPER_ADMIN`: Wildcard access to all capabilities across the enterprise.
- `PRINCIPAL`: Institutional oversight across academics, attendance, examinations, and analytics.
- `HOD`: Departmental authority over curriculum, course scheduling, faculty assignments, and attendance disputes.
- `FACULTY`: Course delivery, marks entry, and student attendance recording.
- `ACCOUNTS`: Billing invoice creation, manual fee collection, ledger reconciliation.
- `PLACEMENT_OFFICER`: Corporate directory management, job drives, application review.
- `STUDENT`: Self-service course enrollment, attendance viewing, fee payment, placement application.
- `PARENT`: Guardian oversight of student attendance and financial invoices.

### 5.3 Backend Authorization Enforcers
FastAPI routes declare declarative authorization dependencies:
```python
@router.post("/payments", response_model=ApiResponse[PaymentResponse])
async def record_payment(
    payload: RecordPaymentRequest,
    user: Annotated[User, Depends(require_permission("finance:payments:record"))],
    tenant: Annotated[TenantContext, Depends(get_current_tenant_context)],
):
    ...
```

---

## 6. Multi-Tenant Isolation & Request Scoping

### 6.1 Tenant Resolution Invariant
```text
Incoming HTTP Request
  ↓
Extract JWT from campusos_access_token cookie
  ↓
Verify cryptographic signature with platform secret
  ↓
Resolve user and validate account status
  ↓
Extract tenant_id from token payload (or fallback to user.primary_tenant_id)
  ↓
Query core_institutions to ensure tenant exists and is active
  ↓
Initialize Thread/Coroutine-Safe Request TenantContext
```

### 6.2 Preventing Tenant Spoofing
- Clients **cannot** send an arbitrary `tenant_id` query parameter or header to switch tenant contexts.
- All database queries for tenant-scoped models (`TenantScopedModel`) are bound to the verified `request.state.tenant.tenant_id`.

---

## 7. Super Admin Special Governance
- Super Admin accounts are global or multi-tenant system administrators.
- Rather than a blanket `if role == "SUPER_ADMIN": pass` bypass in business logic, `SUPER_ADMIN` holds wildcard permissions (`*`) evaluated by `require_permission`.
- Cross-tenant actions generate dedicated forensic `AuditLog` records detailing the actor, target tenant ID, and reason code.

---

## 8. Forensic Auditability
The following authentication events produce immutable entries in `intelligence_audit_logs`:
- `LOGIN_SUCCESS`
- `LOGIN_FAILURE`
- `LOGOUT`
- `PASSWORD_CHANGED`
- `PASSWORD_RESET_REQUESTED`
- `PASSWORD_RESET_COMPLETED`
- `ACCOUNT_LOCKED`
- `ACCOUNT_UNLOCKED`

Audit logs record actor ID, tenant ID, action code, client IP address, user agent, and timestamp.
