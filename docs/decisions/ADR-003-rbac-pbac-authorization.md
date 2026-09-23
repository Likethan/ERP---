# ADR-003: Authorization Strategy — Hybrid RBAC + PBAC

## Status

**Accepted**

## Context

Educational institutions have complex, overlapping organizational responsibilities:

- A Professor might be a Faculty member in Civil Engineering, an HOD of a special department, and the Head of the Campus Anti-Ragging Committee.
- An Accounts Clerk might need permission to issue receipts, but not to configure institutional fee structures.
- Simple role checks (e.g. `if user.role == 'FACULTY'`) fail as soon as permissions diverge or custom roles are created.

## Decision

CampusOS implements a **Hybrid Role-Based and Permission-Based Access Control (RBAC + PBAC)** model:

1. **Atomic Permissions**: Fine-grained permissions defined as strings in the format `domain:resource:action` (e.g., `attendance:records:write`, `finance:invoices:approve`).
2. **Roles as Permission Sets**: Standard roles (`SUPER_ADMIN`, `PRINCIPAL`, `HOD`, `FACULTY`, `ACCOUNTS`, `PLACEMENT_OFFICER`, `STUDENT`, `PARENT`) are collections of permissions.
3. **Custom Institution Roles**: Institutions can define custom roles and grant bespoke permission sets.
4. **Backend Enforcement**: Route handlers check atomic permissions via dependency injection (`require_permission("...")`), never hardcoded role names.
5. **Zero Client Trust**: Frontend UI hides buttons for UX convenience, but all security is strictly enforced at the backend gateway.

## Consequences

### Positive

- Total flexibility to handle institutional edge cases and custom administrative delegations.
- Reusable, auditable permission guards across all endpoints.
- Clear alignment with the Principle of Least Privilege.

### Negative / Tradeoffs

- Slight overhead in permission resolution during authentication (mitigated by caching user permission sets in the Redis session or JWT claims).
