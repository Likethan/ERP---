# CampusOS Identity Provisioning & Lifecycle Governance

## 1. User Provisioning Modes

Institutional identity provisioning is controlled by `TenantIdentityPolicy.provisioning_mode`:

| Mode | Behavior |
| :--- | :--- |
| `JUST_IN_TIME` | Users successfully authenticated via a configured IdP are automatically provisioned on first login if their email domain is allowed. |
| `INVITATION_ONLY` | Self-provisioning is blocked; an administrator or invitation token is required before federated authentication is permitted. |
| `PRE_PROVISIONED` | Accounts must be pre-created by registrar/HR integration; only existing users can link external identity. |
| `DISABLED` | External provisioning is completely prohibited. |

---

## 2. Just-in-Time (JIT) Provisioning Flow

```
External SSO Authentication
       ↓
Extract Validated Claims (`sub`, `email`, `name`, `roles`)
       ↓
Domain Authorization Check
   └── Is email domain in `allowed_email_domains`? ➔ REJECT if unauthorized
       ↓
Account Lookup
   ├── Existing ExternalIdentity Found? ➔ Log in existing user
   ├── Existing User with same email Found? ➔ Safe Account Linking Challenge
   └── No Existing User Found:
       ↓
Provision New User Entity (`people_users`)
   ├── Generate UUID, name, email
   ├── Dummy unmatchable password hash ("EXTERNAL_FEDERATED_SSO_IDENTITY")
   └── Set status = ACTIVE
       ↓
Assign Institutional Role (`people_user_roles`)
   ├── Map external group via provider `role_mapping`
   └── Default fallback: STUDENT
       ↓
Create ExternalIdentity Mapping (`identity_external_identities`)
       ↓
Establish First-Class IdentitySession & Emit Audit Record
```

---

## 3. Account Lifecycle States

CampusOS enforces formal lifecycle state transitions:

```
[INVITED] ➔ [PENDING] ➔ [ACTIVE] ➔ [SUSPENDED] ➔ [DISABLED] ➔ [DEPROVISIONED]
                           ↑           │
                           └───────────┘ (Reactivation)
```

- Users in `SUSPENDED`, `DISABLED`, or `DEPROVISIONED` states are strictly rejected from both local and SSO authentication.

---

## 4. Controlled Deprovisioning & Records Governance (Step 19)

When a student graduates or a faculty member leaves the institution:
1. Administrator calls `EnterpriseIdentityService.deprovision_user(tenant_id, user_id, reason)`.
2. User status is transitioned to `DEPROVISIONED` and `is_active = False`.
3. **Immediate Revocation**: All active sessions across all devices are immediately revoked.
4. **Credential Invalidation**: All registered MFA factors are deactivated.
5. **Governed Record Preservation**: Academic transcripts, degree certificates, examination results, fee invoices, and audit logs are **NEVER deleted**. They remain bound to the institution under Step 19 retention schedules.
6. A forensic `USER_DEPROVISIONED` audit record is created.
