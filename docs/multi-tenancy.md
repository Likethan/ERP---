# CampusOS Multi-Tenant SaaS Architecture & Tenant Isolation

## 1. Architectural Overview

CampusOS is architected as a high-density, multi-tenant Software-as-a-Service (SaaS) platform engineered to serve multiple universities, colleges, and educational polytechnics from a shared application and database layer.

The architecture enforces tenant isolation across all 11 ERP domains:
1. **Foundation & Core Organizational Hierarchy**
2. **People & Role-Based Access Control (RBAC/PBAC)**
3. **Academics & Curricular Governance**
4. **Attendance Management & Absence Policies**
5. **Examinations, Marks Roster & Grading Scales**
6. **Finance, Fee Structures & Invoicing**
7. **Career & Placement Drives**
8. **Campus Life, Clubs, Events & Announcements**
9. **Infrastructure, Hostels & Transportation**
10. **Documents & Digital Records Engine**
11. **Intelligence & AI Decision Engine**

---

## 2. Request Lifecycle & Authentication Boundary

Every incoming request passes through an immutable, server-authoritative pipeline:

```text
HTTP Request (Headers / HttpOnly Cookie)
              ↓
    JWT Token Decoding
              ↓
  Authoritative User Lookup
              ↓
  Tenant Membership Verification (User.primary_tenant_id / TenantMembership)
              ↓
    Tenant Lifecycle Status Check (ACTIVE, TRIAL, SUSPENDED, ARCHIVED)
              ↓
Request-Scoped TenantContext Established (ContextVar + request.state.tenant)
              ↓
      PBAC Authorization (Permissions & Roles)
              ↓
    Repository Layer (TenantScopedRepository)
              ↓
  Tenant-Scoped Database Query (WHERE tenant_id = :current_tenant_id)
```

### Server Authority vs. Payload Spoofing
- Client-supplied payload keys such as `{"tenant_id": "other-tenant"}` are **strictly ignored and stripped**.
- Repositories automatically override or populate `tenant_id` from the server's cryptographic context.
- Tokens requesting a `tenant_id` without confirmed active membership raise `AuthenticationException` immediately.

---

## 3. Canonical Tenant & Membership Models

### Canonical Tenant Entity (`Institution` / `Tenant`)
Located in `core_institutions`:
- `id`: UUID (Primary Key)
- `code`: Unique institutional identifier (e.g. `INST-APEX-01`)
- `slug`: URL-friendly institutional identifier (e.g. `apex-tech`)
- `legal_name`: Registered statutory legal name
- `short_name`: Display brand name
- `status`: Operational state (`ACTIVE`, `TRIAL`, `SUSPENDED`, `ARCHIVED`)
- `plan`: SaaS tier (`FREE`, `STARTER`, `PROFESSIONAL`, `ENTERPRISE`)
- `default_timezone`: IANA timezone string (e.g. `Asia/Kolkata`)
- `currency_code`: Standard ISO-4217 code (e.g. `INR`)
- `locale`: Localization code (e.g. `en-IN`)
- `suspended_at`: Timestamp of suspension
- `deleted_at`: Soft-deletion / archival timestamp

### Multi-Tenant Membership Entity (`TenantMembership`)
Located in `core_tenant_memberships`:
- `id`: UUID
- `tenant_id`: UUID (FK to `core_institutions.id`, ondelete `CASCADE`)
- `user_id`: UUID (FK to `people_users.id`, ondelete `CASCADE`)
- `status`: Membership status (`ACTIVE`, `INVITED`, `SUSPENDED`, `REMOVED`)
- `role_scope`: Tenant-specific scope (`INSTITUTION_ADMIN`, `FACULTY`, `STUDENT`)
- `joined_at`: Timestamp
- `UniqueConstraint("tenant_id", "user_id")`

---

## 4. Tenant Context Object (`TenantContext`)

Located in `app.core.tenant`:

```python
@dataclass(frozen=True)
class TenantContext:
    tenant_id: UUID
    code: str
    name: str
    is_active: bool = True
    user_id: UUID | None = None
    roles: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()
    tenant_status: str = "ACTIVE"
    slug: str | None = None
    plan: str = "ENTERPRISE"
    timezone: str = "Asia/Kolkata"
    currency: str = "INR"
    locale: str = "en-IN"

    @property
    def is_operational(self) -> bool:
        return self.is_active and self.tenant_status in ("ACTIVE", "TRIAL")

    @property
    def is_suspended(self) -> bool:
        return self.tenant_status == "SUSPENDED"

    @property
    def is_archived(self) -> bool:
        return self.tenant_status == "ARCHIVED" or not self.is_active
```

---

## 5. Repository Layer & Tenant Scoping

### `TenantScopedRepository[ModelType]`
Located in `app.repositories.base`:
- **Read Scoping**: `select(Model).where(Model.id == id, Model.tenant_id == current_tenant_id)`
- **List Scoping**: Automatic filter injection `WHERE tenant_id == current_tenant_id`
- **Create Scoping**: Injects authoritative `tenant_id`, discarding any payload-supplied values.
- **Update / Delete Scoping**: Verified prior to mutation; forbids touching other tenants' records.
- **Uniform 404 Behavior**: Attempting to query an ID belonging to Tenant B from Tenant A produces `404 Not Found`, eliminating information leakage and entity presence probing.

### Cross-Tenant Foreign Key (FK) Protection
Helper located in `app.core.tenant_validation`:
- `validate_entities_same_tenant(db, tenant_id, (Department, dept_id), (Program, prog_id))`
- Validates that parent and child models belong strictly to the identical `tenant_id`.
- Rejects cross-tenant entity linkage with `CrossTenantRelationshipException`.

---

## 6. Tenant-Isolated Caching Engine

Located in `app.core.cache`:
- Key format: `tenant:{tenant_id}:{namespace}:{key}`
- Prevents cross-tenant cache hits or cache stampedes.
- Tenant-scoped invalidation: `invalidate_tenant(tenant_id)` and `invalidate_namespace(tenant_id, namespace)`.

---

## 7. Tenant-Isolated Storage Abstraction

Located in `app.core.storage`:
- Storage keys partitioned under: `tenants/{tenant_id}/{category}/{filename}`
- Strict path sanitization prevents directory traversal attacks (`..` or root escaping).
- Validated via `validate_tenant_storage_key(storage_key, tenant_id)`.

---

## 8. Tenant-Aware Background Task Framework

Located in `app.core.jobs`:
- Jobs encapsulate explicit `TenantJobContext(tenant_id, code, name, status, plan, timezone)`.
- Pre-execution lifecycle checks skip `SUSPENDED` or `ARCHIVED` institutions.
- Multi-tenant schedulers execute across tenants with independent fault boundaries: failure in Tenant A never halts processing for Tenant B.

---

## 9. Platform Administration vs. Tenant Administration

CampusOS enforces strict role and boundary separation:

| Dimension | Tenant Administrator | Platform Administrator |
|---|---|---|
| **Role Code** | `INSTITUTION_ADMIN` | `SUPER_ADMIN` |
| **API Boundary** | `/api/v1/*` (scoped to `tenant_id`) | `/api/v1/platform/*` |
| **Permissions** | Domain operations (students, fees, attendance) | Platform lifecycle, SaaS provisioning, tenant suspension |
| **Cross-Tenant Access** | **Strictly Prohibited** (403/404) | Permitted for global governance & health |
| **Platform Routes** | Returns `403 Forbidden` | Returns `200/201` |

---

## 10. Multi-Tenant Audit Log Isolation

Located in `app.models.audit.AuditLog`:
- Every audit record records `tenant_id`, `user_id`, `action`, `entity_type`, `entity_id`, and `created_at`.
- Tenant administrators query exclusively their own audit records.
- Platform events omit `tenant_id` only when genuinely system-wide.

---

## 11. Domain Tenant Isolation Audit Matrix

| Module | Tenant Scoped | Repository Safe | FK Protected | Cache Isolated | Storage Isolated |
|---|:---:|:---:|:---:|:---:|:---:|
| **Foundation & Core** | Yes | Yes | Yes | Yes | N/A |
| **People & RBAC** | Yes | Yes | Yes | Yes | Yes |
| **Academics** | Yes | Yes | Yes | Yes | N/A |
| **Attendance** | Yes | Yes | Yes | Yes | N/A |
| **Examination** | Yes | Yes | Yes | Yes | N/A |
| **Finance** | Yes | Yes | Yes | Yes | N/A |
| **Placement** | Yes | Yes | Yes | Yes | Yes |
| **Campus Life** | Yes | Yes | Yes | Yes | Yes |
| **Infrastructure** | Yes | Yes | Yes | Yes | N/A |
| **Documents** | Yes | Yes | Yes | Yes | Yes |
| **Intelligence & AI** | Yes | Yes | Yes | Yes | N/A |

---

## 12. Future PostgreSQL Row-Level Security (RLS) Strategy

The schema and architecture have been built to seamlessly adopt PostgreSQL Row-Level Security:

### Application Session Variable Pattern
Before issuing database statements, set the PostgreSQL session variable:
```sql
SET LOCAL app.current_tenant_id = 'cdd6c7be-c46d-4d90-bd04-78033a8bf354';
```

### PostgreSQL RLS Policy Pattern
```sql
ALTER TABLE people_students ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_policy ON people_students
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
```

Because every tenant-owned model in CampusOS already inherits from `TenantScopedModel` with non-null indexed `tenant_id`, RLS can be activated at the database level with zero structural refactoring.
