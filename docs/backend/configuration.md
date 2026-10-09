# Enterprise Configuration Engine

The **Enterprise Administration, Configuration & Policy Management Layer** provides a centralized control plane for configurable CampusOS behavior, allowing authorized administrators to configure institution-wide, campus-level, and tenant-level operational behavior without modifying application code or redeploying services.

---

## 1. Architectural Principles

- **Configuration as Controlled Data**: Business parameters are stored and versioned as typed data records rather than static configuration files or unvalidated JSON blobs.
- **Strict Typing & Schema Validation**: Each configuration parameter is defined by a `ConfigurationDefinition` that enforces data types (`string`, `integer`, `decimal`, `boolean`, `enum`, `percentage`, `currency`, `url`, `date`, `datetime`, `duration`, `json`), constraint boundaries (`min`, `max`, `min_length`, `max_length`), regex patterns, and allowed enumerations.
- **Multi-Tenant Isolation**: Every configuration override is strictly bound to a `tenant_id`. Cross-tenant reads and mutations are barred at database and service layers.
- **Hierarchical Inheritance Resolution**: Overrides resolve deterministically down a strict precedence hierarchy:
  ```
  Campus Override
        ↓
  Institution Override
        ↓
  Tenant Override
        ↓
  Platform Default
        ↓
  Definition Default
  ```
- **Auditable & Non-Destructive Versioning**: Every change writes a snapshot to `configuration_versions`. Historical versions are immutable. Rollbacks create a new version referencing the historical snapshot.
- **High-Performance In-Memory & Tenant-Safe Caching**: Effective configuration lookups are cached with tenant-namespaced keys and invalidated upon any mutation or rollback.

---

## 2. Configuration Scopes

| Scope | Description | Requirement |
|---|---|---|
| `PLATFORM` | System-wide global default across all tenants | `tenant_id = NULL` |
| `TENANT` | Tenant-wide baseline override for an entire university/organization | `tenant_id` required |
| `INSTITUTION` | Institution/College override within a multi-institution tenant | `tenant_id` and `institution_id` required |
| `CAMPUS` | Campus branch override within an institution | `tenant_id`, `institution_id`, and `campus_id` required |
| `MODULE` | Module-specific configuration scope | Specific to module lifecycle |

Scope combinations are strictly validated to prevent invalid pairings (e.g. specifying `campus_id` without a valid `institution_id`).

---

## 3. Configuration Definitions & Types

Every configurable setting is defined in `configuration_definitions`.

### Supported Data Types
- `string`: Text parameters with optional regex, min_length, max_length.
- `integer`: Whole numbers with min/max validation (e.g., `attendance.grace_percentage`).
- `decimal`: Floating-point numbers with min/max bounds.
- `boolean`: Boolean flags (`true`/`false`).
- `enum`: Restricted set of string values specified in `allowed_values`.
- `percentage`: Number between 0 and 100 (e.g., `attendance.minimum_percentage`).
- `currency`: 3-letter ISO-4217 currency code (e.g., `USD`, `INR`, `EUR`, `GBP`).
- `url`: Validated HTTP/HTTPS web address.
- `date` / `datetime`: ISO-formatted date/timestamp strings.
- `duration`: Positive integer indicating seconds or days.
- `json`: Structured JSON metadata with schema validation.

### Sensitivity Classifications
- `PUBLIC`: Safe for public branding or unauthenticated endpoints.
- `INTERNAL`: Default for institutional settings.
- `CONFIDENTIAL`: Accessible only to institutional administrators. Blocked from AI/Intelligence assistant tools.
- `RESTRICTED`: Highly sensitive operational keys. Requires strict authorization. Excluded from AI and export tools.

---

## 4. Effective Configuration Resolution

To retrieve the effective configuration value for a key in any operational context:

```python
from app.services.configuration_resolver import ConfigurationResolver

resolver = ConfigurationResolver(db_session)
effective = await resolver.resolve_effective(
    key="attendance.minimum_percentage",
    tenant_id=tenant_id,
    institution_id=institution_id,
    campus_id=campus_id,
    module="ATTENDANCE",
)

# effective.value: 75.0
# effective.source_scope: ConfigurationScope.TENANT
# effective.source_id: tenant_id
# effective.is_inherited: False
# effective.version: 1
```

The resolver verifies active dates (`effective_from <= now <= effective_until`) and active status before returning the value.

---

## 5. Preview, Impact Analysis & Dry-Run Validation

Before applying high-impact configuration changes, administrators can preview the change without modifying persistent storage:

- **Dry-run validation**: Validates proposed value against definition rules, types, and constraints.
- **Resolution comparison**: Compares current effective value with the proposed effective value.
- **Consumer impact radius**: Discovers all registered consumers and modules (e.g., `attendance.service`, `examination.service`, `finance.billing_engine`) registered in `configuration_dependencies`.

---

## 6. Change Management, Versioning & Rollback

### Change Lifecycle
1. **Validation**: Candidate value validated against `ConfigurationDefinition`.
2. **Persistence**: Value updated or created in `configuration_values`.
3. **Snapshot**: Version record created in `configuration_versions` with previous version reference, actor, reason, and change diff.
4. **Cache Invalidation**: Tenant-scoped cache evicted for the configuration key.
5. **Audit Logging**: Structured event emitted to `audit_logs` (e.g., `CONFIGURATION_UPDATED`).

### Rollback
Rollbacks never delete or mutate historical records. Restoring version `v1` from version `v2` creates version `v3` with:
- `change_summary`: "Rolled back to version 1: <reason>"
- `rollback_from_version`: 1
- `status`: `ACTIVE`
- Cache evicted and audit logged immediately.
