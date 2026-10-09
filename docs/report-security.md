# CampusOS Reporting Security & Tenant Isolation

## Multi-Tenant Isolation
- All database queries constructed by `ReportingEngine` automatically enforce `table.tenant_id == tenant_id`.
- The `tenant_id` is extracted strictly from the verified session context (`TenantContext`), never from client query parameters.
- Cross-tenant querying is strictly prohibited for standard accounts; platform administrators must execute through explicit platform-scoped adapters.

## SQL & Expression Injection Defenses
- Zero arbitrary SQL input: queries are built purely using SQLAlchemy ORM and Core expression abstractions.
- All filter field names, operators, and dimensions are strictly checked against frozen sets in `DATASET_REGISTRY` before statement construction.
- No `eval()`, `exec()`, or Python reflection is utilized in filter parsing.

## Tenant-Partitioned Caching
- Redis and in-memory caches partition keys by tenant namespace:
  `tenant:{tenant_id}:reports:{report_id}:{version}:{query_hash}`
- Cache reads for Tenant A can never retrieve cached data belonging to Tenant B under any circumstance.
