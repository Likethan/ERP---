# CampusOS — Database & Multi-Tenancy Strategy

A critical design requirement of CampusOS is that the system must initially operate cleanly for a single college while supporting a smooth evolution to a **multi-tenant SaaS platform** serving multiple institutions.

---

## 1. Multi-Tenancy Models Compared

| Approach                                     | Isolation Level            | Maintenance Overhead                           | Hardware Efficiency        | SaaS Scalability | CampusOS Fit                                                         |
| :------------------------------------------- | :------------------------- | :--------------------------------------------- | :------------------------- | :--------------- | :------------------------------------------------------------------- |
| **Database-per-Tenant**                      | Maximum                    | Extremely High (migrations across N DBs)       | Poor (idle resource waste) | Low              | Overkill for initial phase; reserved for enterprise dedicated tiers. |
| **Schema-per-Tenant**                        | High                       | Moderate (Alembic schema iteration complexity) | Moderate                   | Medium           | Viable phase 2 evolution.                                            |
| **Shared DB with Row-Level Isolation (RLS)** | High (with PostgreSQL RLS) | Low (single unified schema & migrations)       | Optimal                    | High             | **Chosen Baseline for CampusOS**                                     |

---

## 2. CampusOS Isolation Architecture

### 2.1 The `tenant_id` Principle

Every persistent entity that holds institution-specific data includes a mandatory `tenant_id: UUID` column referencing `core.institutions(id)`.

```sql
-- Architectural Blueprint for Tenant-Scoped Tables
CREATE TABLE people_students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE RESTRICT,
    user_id UUID NOT NULL REFERENCES people_users(id),
    admission_number VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_tenant_admission_number UNIQUE (tenant_id, admission_number)
);

CREATE INDEX idx_people_students_tenant ON people_students(tenant_id);
```

### 2.2 Dual-Layer Isolation Enforcement

To eliminate human error where a developer might forget a `WHERE tenant_id = :current_tenant` clause:

1. **Application Layer (SQLAlchemy Base Query Interceptor)**:
   - When an authenticated request enters FastAPI, the `tenant_id` is extracted from the user's validated JWT token.
   - The SQLAlchemy AsyncSession automatically applies a tenant filter to all SELECT, UPDATE, and DELETE operations.
2. **Database Layer (PostgreSQL Row-Level Security)**:
   - PostgreSQL RLS policies can be activated on tenant tables:
   ```sql
   ALTER TABLE people_students ENABLE ROW LEVEL SECURITY;
   CREATE POLICY tenant_isolation_policy ON people_students
       FOR ALL
       USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
   ```

### 2.3 Global vs Tenant Entities

- **Tenant-Scoped Entities**: Students, Faculty, Departments, Courses, Invoices, Attendance, Exams, Events.
- **Global Entities**: System Roles, System Permission definitions, Super Admin accounts, Platform Configuration flags.

---

## 3. Migration Safety

- All migrations created via Alembic must ensure indices on `(tenant_id, ...)` for composite unique constraints.
- Foreign keys between operational entities must never cross `tenant_id` boundaries.
