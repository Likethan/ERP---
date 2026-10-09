# Enterprise Administration & Control Plane

The **Enterprise Administration Layer** provides institutional and platform administrators with centralized operational controls over modules, sequences, configuration definitions, and governance policies.

---

## 1. Module Enablement & Maintenance Modes

CampusOS allows modular license activation per tenant across core pillars:
- `ACADEMICS`, `ATTENDANCE`, `EXAMINATION`, `FINANCE`, `PLACEMENT`
- `CAMPUS`, `INFRASTRUCTURE`, `DOCUMENTS`, `INTELLIGENCE`

### Module States & Maintenance
Each module can be in one of the following states:
- `is_enabled`: When `false`, all API endpoints guarding this module return `403 ModuleDisabledException`.
- `in_maintenance`: When `true`, all non-superadmin access is rejected with `503 ModuleMaintenanceException`, including a customized maintenance message and optional estimated completion time.

### FastAPI Route Guard Dependency
```python
from app.services.module_configuration_service import require_module_enabled

@router.get("/attendance/roster", dependencies=[Depends(require_module_enabled("ATTENDANCE"))])
async def get_roster():
    ...
```

---

## 2. Numbering & Sequence Management

Enterprise institutions require standardized, sequential identifiers for regulatory and financial documents:
- Student Admission Numbers: `ADM-{YEAR}-{SEQ}`
- Invoices: `INV-{YYYY}-{SEQ}`
- Payment Receipts: `RCP-{YYYY}-{SEQ}`
- Degrees & Certificates: `CERT-{YYYY}-{SEQ}`
- Applications: `APP-{YYYY}-{SEQ}`

### Concurrency-Safe Atomic Generation
Numbering sequences utilize PostgreSQL row-level locks (`SELECT ... FOR UPDATE`) inside atomic database transactions to ensure:
- **Zero Duplicates Under High Concurrency**: Parallel requests lock the sequence row in serialization order.
- **Configurable Padding & Step**: Configurable step size and padding (e.g. `INV-2026-000042`).
- **Periodic Resets**: Automatic sequence reset on yearly (`YEARLY`), monthly (`MONTHLY`), or daily (`DAILY`) boundaries.

---

## 3. Administration REST API Endpoints

All admin endpoints reside under the `/api/v1/admin` namespace and require appropriate permissions:

### Configuration Management
| Method | Endpoint | Permission | Description |
|---|---|---|---|
| `GET` | `/api/v1/admin/configuration` | `configuration:read` | List configuration values |
| `GET` | `/api/v1/admin/configuration/effective` | `configuration:read` | Resolve effective configuration |
| `POST` | `/api/v1/admin/configuration/validate` | `configuration:read` | Dry-run validation |
| `POST` | `/api/v1/admin/configuration/preview` | `configuration:preview` | Impact analysis & preview |
| `GET` | `/api/v1/admin/configuration/versions` | `configuration:read` | List historical versions |
| `GET` | `/api/v1/admin/configuration/versions/{id}` | `configuration:read` | Retrieve version snapshot |
| `GET` | `/api/v1/admin/configuration/{key}` | `configuration:read` | Get configuration definition & value |
| `POST` | `/api/v1/admin/configuration` | `configuration:create` | Create configuration override |
| `PATCH` | `/api/v1/admin/configuration/{key}` | `configuration:update` | Update configuration value |
| `DELETE` | `/api/v1/admin/configuration/{key}` | `configuration:delete` | Remove configuration override |
| `POST` | `/api/v1/admin/configuration/{key}/rollback` | `configuration:rollback` | Roll back to prior version |

### Policies
| Method | Endpoint | Permission | Description |
|---|---|---|---|
| `GET` | `/api/v1/admin/policies` | `policy:read` | List active policies |
| `GET` | `/api/v1/admin/policies/{key}` | `policy:read` | Get policy details |
| `POST` | `/api/v1/admin/policies` | `policy:manage` | Create policy rule |
| `PATCH` | `/api/v1/admin/policies/{key}` | `policy:manage` | Update policy rule |
| `POST` | `/api/v1/admin/policies/{key}/evaluate`| `policy:read` | Test evaluate policy |

### Feature Flags
| Method | Endpoint | Permission | Description |
|---|---|---|---|
| `GET` | `/api/v1/admin/features` | `feature_flag:read` | List feature flags |
| `GET` | `/api/v1/admin/features/{key}` | `feature_flag:read` | Get feature flag details |
| `PATCH` | `/api/v1/admin/features/{key}` | `feature_flag:manage` | Toggle/update flag |

### Modules
| Method | Endpoint | Permission | Description |
|---|---|---|---|
| `GET` | `/api/v1/admin/modules` | `module:read` | List module states |
| `PATCH` | `/api/v1/admin/modules/{module}` | `module:manage` | Enable/disable module |

### Numbering Sequences
| Method | Endpoint | Permission | Description |
|---|---|---|---|
| `GET` | `/api/v1/admin/sequences` | `sequence:read` | List numbering sequences |
| `GET` | `/api/v1/admin/sequences/{key}` | `sequence:read` | Get sequence definition |
| `PATCH` | `/api/v1/admin/sequences/{key}` | `sequence:manage` | Update sequence parameters |

---

## 4. RBAC & Granular Permissions

| Permission | Role Assignment | Description |
|---|---|---|
| `configuration:read` | `SUPER_ADMIN`, `INSTITUTION_ADMIN` | View configuration and effective values |
| `configuration:create` | `SUPER_ADMIN`, `INSTITUTION_ADMIN` | Create overrides |
| `configuration:update` | `SUPER_ADMIN`, `INSTITUTION_ADMIN` | Modify overrides |
| `configuration:delete` | `SUPER_ADMIN`, `INSTITUTION_ADMIN` | Delete overrides |
| `configuration:rollback`| `SUPER_ADMIN` | Restore previous versions |
| `configuration:preview` | `SUPER_ADMIN`, `INSTITUTION_ADMIN` | Dry-run preview and impact analysis |
| `policy:read` | `SUPER_ADMIN`, `INSTITUTION_ADMIN` | View policy rules and evaluate |
| `policy:manage` | `SUPER_ADMIN` | Create and modify business policies |
| `feature_flag:read` | `SUPER_ADMIN`, `INSTITUTION_ADMIN` | View feature flags |
| `feature_flag:manage` | `SUPER_ADMIN` | Modify feature flags and rollouts |
| `module:read` | `SUPER_ADMIN`, `INSTITUTION_ADMIN` | View module status |
| `module:manage` | `SUPER_ADMIN` | Enable/disable modules & maintenance |
| `sequence:read` | `SUPER_ADMIN`, `INSTITUTION_ADMIN` | View numbering sequences |
| `sequence:manage` | `SUPER_ADMIN` | Configure prefixes and sequence bounds |

---

## 5. Background Operations & Maintenance

The CampusOS job scheduler periodically runs:
1. `activate_scheduled_configuration`: Promotes scheduled configuration changes whose `effective_from` timestamp has arrived, updating status to `ACTIVE`.
2. `expire_feature_flags`: Auto-disables feature flags whose `expires_at` timestamp has passed.
