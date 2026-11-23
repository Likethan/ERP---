# CampusOS Enterprise Identity Architecture

## 1. Overview & Separation of Concerns

CampusOS establishes a strict separation between **Identity** (who the principal is) and **Authorization** (what capabilities the principal may exercise within a tenant boundary).

```
Identity Provider (Local / OIDC / OAuth2 / SAML)
       ↓
Cryptographic Authentication & Verification
       ↓
Identity Resolution & Tenant Scoping
       ↓
Account Lifecycle Enforcement (ACTIVE, SUSPENDED, DEPROVISIONED)
       ↓
First-Class Session Establishment (Token Family, IP Masking, Device Telemetry)
       ↓
RBAC / PBAC Permission Evaluation
       ↓
Governed Application Access
```

---

## 2. Principal Domain Model

The architecture decouples concepts that are frequently conflated in smaller applications:

| Concept | Entity | Description |
| :--- | :--- | :--- |
| **Identity** | `ExternalIdentity` | Federation mapping binding an external subject identifier (`sub`) and provider ID to an institutional account. |
| **User** | `User` | Core principal representation holding names, emails, and global lifecycle status. |
| **Account** | `Institution` & `TenantMembership` | The institutional context and role scopes granted to the user within a college/university. |
| **Session** | `IdentitySession` | First-class user session tracking refresh token families, device summaries, masked IP addresses, and activity. |
| **Credential** | `User.password_hash`, `MfaFactor` | Authentication secrets (Argon2id password hashes, encrypted TOTP secrets, recovery codes). |
| **Membership** | `TenantMembership` / `UserRoleAssignment` | Scoped tenant bindings and department/campus-level RBAC role assignments. |

---

## 3. Identity Provider Entities

Multi-tenant identity integrations are managed per tenant through `identity_providers`:

- **Types Supported**: `LOCAL`, `OIDC`, `OAUTH2`, `SAML` (abstraction ready for enterprise IdPs).
- **Lifecycle States**: `DRAFT` ➔ `CONFIGURED` ➔ `ACTIVE` ➔ `PAUSED` ➔ `DISABLED` ➔ `ERROR`.
- **Health Telemetry**: `HEALTHY`, `DEGRADED`, `MISCONFIGURED`, `UNAVAILABLE`, `UNKNOWN`.
- **Deny-by-Default Role Mapping**: Claims are mapped via `role_mapping` dictionaries. External groups never automatically grant elevated permissions or `SUPER_ADMIN` platform privileges.

---

## 4. Tenant Isolation

All identity providers, external federations, sessions, and tenant policies enforce strict multi-tenant boundaries:
- `tenant_id` is foreign-keyed to `core_institutions.id`.
- Tenant A administrators cannot list, inspect, activate, test, or modify identity configurations belonging to Tenant B.
- Unique constraints prevent duplicate provider slugs or external subjects within a single institution (`uq_idp_tenant_slug`, `uq_ext_identity_subject`).

---

## 5. Security & Governance Integration

- **Step 15 Security Integration**: All security events (`LOGIN_SUCCESS`, `LOGIN_FAILURE`, `TOKEN_FAMILY_REVOCATION`, `IDENTITY_LINKED`, `USER_DEPROVISIONED`) emit structured forensic records into `intelligence_audit_logs`.
- **Step 19 Governance Integration**: Controlled deprovisioning invalidates sessions and disables access while preserving academic, financial, and compliance records according to retention schedules.
- **Step 20 Safe Outbound HTTP**: All discovery endpoints and JWKS URIs are queried through `SafeHttpClient` with pre-request SSRF validation and private network filtering.
