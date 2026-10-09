# Enterprise Master Data Management (MDM) Architecture

CampusOS implements a centralized, multi-tenant Master Data Management (MDM) and Data Quality control plane designed to govern shared institutional concepts across domains without disrupting domain ownership.

---

## 1. Core Principles

1. **Single Source of Truth**: Each master concept retains a single authoritative domain owner:
   - **Student Identity**: People domain (`people_students`)
   - **Department / Program**: Core Academics domain (`core_departments`, `core_programs`)
   - **Faculty / Staff**: People domain (`people_faculty`, `people_staff`)
   - **Recruitment Companies**: Placement domain (`placement_companies`)
   - **Fee Categories**: Finance domain (`finance_fee_categories`)
   - **Document Categories**: Digital Records domain (`document_categories`)
2. **Non-Invasive Governance**: MDM maintains canonical schemas, quality rules, and stewardship workflows *referencing* domain tables rather than creating duplicate copies of institutional rows.
3. **Strict Multi-Tenant Isolation**: All reference data, quality issues, duplicate candidate pairs, merge operations, and audit lineage records are strictly partitioned by `tenant_id` at the database level.
4. **Deterministic Auditing**: All merges, corrections, rule modifications, and stewardship transitions generate immutable forensic records in the central CampusOS audit trail.

---

## 2. Master Data Registry

Governed entity types are registered in `master_data_definitions`:

| Master Type | Owning Domain | Steward Role | Sensitivity | Duplicate Detection | Merge Supported | Authoritative Table |
|---|---|---|---|---|---|---|
| `STUDENT` | People | `STUDENT_ADMINISTRATOR` | `RESTRICTED` | Yes | Yes | `people_students` |
| `FACULTY` | People | `FACULTY_ADMINISTRATOR` | `RESTRICTED` | No | No | `people_faculty` |
| `STAFF` | People | `STAFF_ADMINISTRATOR` | `RESTRICTED` | No | No | `people_staff` |
| `DEPARTMENT` | Academics | `ACADEMIC_ADMINISTRATOR` | `INTERNAL` | Yes | Yes | `core_departments` |
| `PROGRAM` | Academics | `ACADEMIC_ADMINISTRATOR` | `INTERNAL` | No | No | `core_programs` |
| `COMPANY` | Placement | `PLACEMENT_OFFICER` | `CONFIDENTIAL` | Yes | Yes | `placement_companies` |
| `FEE_CATEGORY` | Finance | `FINANCE_ADMINISTRATOR` | `INTERNAL` | No | No | `finance_fee_categories` |
| `DOCUMENT_CATEGORY` | Documents | `RECORDS_OFFICER` | `INTERNAL` | No | No | `document_categories` |

---

## 3. Reference Data Architecture

Controlled reference values represent tenant-administered enumerations and codes that require runtime flexibility without violating relational database semantics:

- **Reference Definitions** (`reference_data_definitions`):
  - Categories: `PAYMENT_METHOD`, `GENDER`, `BLOOD_GROUP`, `ACADEMIC_STATUS`
  - System protected categories have `is_system = True`.
- **Reference Values** (`reference_data_values`):
  - Tenant-scoped controlled codes (`CASH`, `UPI`, `CARD`, `BANK_TRANSFER`, etc.)
  - System values (`is_system = True`) cannot be physically deleted by tenant administrators; they can only be deactivated (`is_active = False`) to preserve historical referential integrity.
  - Multi-tenant unique constraint: `uq_ref_val_tenant_cat_code` on `(tenant_id, category, code)`.

---

## 4. Master Data Lineage & Provenance

Every master record tracks its origin and modification history through `master_data_lineage`:
- **Lineage Sources**: `MANUAL`, `IMPORT`, `API`, `INTEGRATION`, `SYSTEM`, `MIGRATION`, `MERGE`
- **Tracked Metadata**:
  - `source_record_id`: External legacy ID or sync key
  - `imported_at`: Ingestion timestamp
  - `last_verified_at`: Steward verification timestamp
  - `modified_by`: Identity UUID of the modifying user
  - `modification_source`: Integration channel or API caller

---

## 5. Security & Access Control

MDM operations are protected by fine-grained PBAC permissions:

- `master_data:read`: View definitions, reference data, and quality summaries
- `master_data:validate`: Run on-demand quality evaluation dry-runs
- `master_data:correct`: Propose field-level data corrections
- `master_data:merge`: Execute controlled record merges and rollbacks
- `master_data:approve`: Review and approve correction proposals
- `master_data:reference_manage`: Manage tenant reference codes
- `master_data:quality_manage`: Manage validation rules and remediate quality issues
- `master_data:definition_manage`: Configure master data catalog definitions
