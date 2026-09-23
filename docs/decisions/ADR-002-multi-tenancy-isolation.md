# ADR-002: Multi-Tenancy Strategy — Row-Level Isolation with RLS

## Status

**Accepted**

## Context

CampusOS must initially support a single college while having a clear, zero-rewrite architecture for expanding into a multi-tenant SaaS platform hosting hundreds of institutions.

The primary multi-tenancy models are:

1. **Database-per-Tenant**: Highest physical isolation, but extreme operational overhead when managing migrations, connection pools, and cost for small-to-medium institutions.
2. **Schema-per-Tenant**: Moderate isolation, but high complexity in Alembic migrations and connection management.
3. **Shared Database with Row-Level Isolation (`tenant_id`)**: Highest hardware efficiency, single unified schema and migration path, but requires rigorous query filtering.

## Decision

We select **Shared Database with Row-Level Isolation (`tenant_id`)**, enhanced with PostgreSQL **Row-Level Security (RLS)** and SQLAlchemy automatic tenant filtering hooks.

- Every operational table contains a `tenant_id: UUID` foreign key referencing `core.institutions(id)`.
- All unique constraints across tenant tables must be composite: `UNIQUE(tenant_id, business_key)`.
- Global models (system permissions, platform configurations) are tenant-agnostic.
- As the platform grows, enterprise clients with strict sovereign regulatory mandates can be routed to dedicated databases using tenant router middleware without altering domain application code.

## Consequences

### Positive

- Unified schema and single-command database migrations via Alembic.
- Optimal database connection pooling and resource utilization.
- Rapid tenant onboarding (inserting a tenant record without provisioning new database servers).

### Negative / Tradeoffs

- Accidental cross-tenant leakage is theoretically possible if developers execute raw SQL bypassing ORM filters (mitigated by strict prohibition of raw SQL and database-level RLS policies).
