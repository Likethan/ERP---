# CampusOS — Security Architecture

Security in CampusOS is designed with a **Zero-Trust** posture. Every incoming request is authenticated, authorization is checked against granular permissions, and tenant isolation is mathematically enforced.

---

## 1. Authentication Engine

### 1.1 Web Session Management

- **Token Delivery**: Short-lived JSON Web Tokens (Access Tokens, 15 min lifetime) stored in `HttpOnly`, `SameSite=Lax`, `Secure` cookies. This mitigates Cross-Site Scripting (XSS) token exfiltration.
- **Refresh Flow**: Long-lived Refresh Tokens (7-day lifetime) stored in separate restricted-path cookies, with automatic rotation upon issuance to detect replay attacks.
- **Password Security**: Passwords are saved using **Argon2id** (memory cost 65536, iterations 3, parallelism 4), resilient against GPU and ASIC cracking.

### 1.2 Programmatic / API Tokens

- Biometric machines, payment webhooks, and third-party integrations authenticate using high-entropy API keys (`cos_live_...`) with SHA-256 storage and IP restriction options.

---

## 2. Authorization: Hybrid RBAC + PBAC

Permissions are modeled as explicit action tuples:

`{domain}:{resource}:{action}`

Examples:

- `academics:courses:create`
- `attendance:records:write`
- `finance:invoices:approve`
- `people:students:view_sensitive`

### 2.1 Role-to-Permission Mapping

A **Role** (e.g., `FACULTY`, `HOD`, `ACCOUNTS`) is simply a bundle of atomic permissions. When a user requests an endpoint, the system checks whether the user's assigned roles or direct grants contain the required permission:

```python
# In FastAPI Router:
@router.post("/courses", response_model=ApiResponse[CourseResponse])
async def create_course(
    payload: CreateCourseRequest,
    current_user: Annotated[User, Depends(require_permission("academics:courses:create"))],
    tenant: Annotated[TenantContext, Depends(get_current_tenant)],
):
    ...
```

### 2.2 Golden Rule: Zero Client-Side Trust

> [!IMPORTANT]
> **Client-side permission checks are purely visual.** Hiding a "Delete Invoice" button in the React UI is a convenience for the user. The backend API route **strictly enforces** `require_permission("finance:invoices:delete")` on every incoming HTTP call.

---

## 3. Defense-in-Depth Checklist

| Threat Vector                         | Mitigation Strategy in CampusOS                                                                                                                 |
| :------------------------------------ | :---------------------------------------------------------------------------------------------------------------------------------------------- |
| **SQL Injection**                     | Parameterized queries exclusively via SQLAlchemy 2.0 ORM; raw string SQL is forbidden.                                                          |
| **Cross-Tenant Data Leakage**         | Tenant ID extracted strictly from cryptographically verified token; PostgreSQL RLS as database guardrail.                                       |
| **Brute Force & Credential Stuffing** | Redis-backed sliding-window rate limiting on `/api/v1/auth/login` (5 attempts per minute per IP/account).                                       |
| **CSRF Attacks**                      | SameSite cookie policy combined with custom header validation (`X-Requested-With` or CSRF token).                                               |
| **Sensitive Data Exposure**           | Pydantic response models filter out sensitive fields (password hashes, bank details, SSN/Aadhar) by default.                                    |
| **Audit Non-Repudiation**             | Administrative and financial actions generate immutable audit trail entries containing actor ID, IP address, timestamp, and before/after diffs. |
