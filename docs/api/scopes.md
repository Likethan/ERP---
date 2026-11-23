# CampusOS API Capability Scopes & PBAC Integration

## Overview

The CampusOS API Platform uses a **Capability Scope Registry** to enforce fine-grained authorization. Unlike monolithic API keys that grant blanket administrative rights, each external application is granted a tailored subset of scopes.

---

## 1. Scope Registry Specifications

Scopes adhere to the standard `{domain}.{action}` notation.

| Scope Code | Category | Risk Level | Description | Requires Approval |
| :--- | :--- | :--- | :--- | :--- |
| `students.read` | Student Data | Standard | Read basic student roster and directory details | No |
| `students.write` | Student Data | **High Risk** | Create or modify student profile records | **Yes** |
| `faculty.read` | HR & People | Standard | Read academic faculty member directory | No |
| `staff.read` | HR & People | Standard | Read institutional staff profiles | No |
| `academics.read` | Academics | Standard | Read courses, syllabi, programs, and curricula | No |
| `attendance.read`| Attendance | Standard | View student attendance registers and summaries | No |
| `examinations.read`| Assessment | Standard | View examination schedules, papers, and grades | No |
| `finance.read` | Finance | Standard | View student fee invoices and balance sheets | No |
| `finance.write` | Finance | **High Risk** | Post payment collections, ledger adjustments | **Yes** |
| `placement.read` | Placement | Standard | Read active recruitment drives, company listings | No |
| `events.read` | Campus Life | Standard | Read public and campus-wide events calendar | No |
| `events.write` | Campus Life | Standard | Create event entries and manage attendance | No |
| `documents.read`| Records | Standard | Read published digital certificates and records | No |
| `documents.write`| Records | **High Risk** | Upload, verify, or generate formal certificates | **Yes** |
| `reports.read` | Analytics | Standard | Query standard aggregated institutional reports | No |
| `analytics.read`| Analytics | Standard | Access analytical and dimensional KPIs | No |
| `notifications.send`| Comms | **High Risk** | Trigger SMS/Email notifications to students | **Yes** |

---

## 2. Scope Hierarchy & Non-Inheritance Rule

> [!IMPORTANT]
> **No Implicit Write-to-Read Inheritance**:
> Granting `finance.write` **does not** automatically grant `finance.read`. Each capability represents an independent authorization domain. If an application requires both reading invoices and posting payments, both scopes must be explicitly requested and granted.

The centralized `ScopeResolver` validates exact scope matches and handles controlled aliases without granting unintended side-effects.

---

## 3. High-Risk Scope Governance

Scopes flagged as **High Risk** (`is_high_risk: True`) enforce a strict approval gate:

1. When an application requests a high-risk scope (e.g. `finance.write`, `documents.write`, `notifications.send`), the grant enters `PENDING_APPROVAL` status.
2. Only an authorized **Institutional Administrator** or **Platform Security Admin** can approve the grant.
3. The platform audit log records:
   - `approver_id`
   - `approved_at`
   - `reason`

---

## 4. Dual-Layer Authorization: Scope + PBAC Defense-in-Depth

The API platform enforces a dual-layer security check:

```text
                  API Gateway Request
                          │
            ┌─────────────▼─────────────┐
            │ Layer 1: Scope Evaluation │
            │   Does App have Scope?    │
            └─────────────┬─────────────┘
                          │ (YES)
            ┌─────────────▼─────────────┐
            │  Layer 2: PBAC Validation │
            │ Does App Owner have PBAC? │
            └─────────────┬─────────────┘
                          │ (YES)
                 Dispatch to Handler
```

Even if an application has been granted `students.read`, the request is **rejected with 403 Forbidden** if the application's registered owner account does not possess the underlying permission (`people:students:read`). This prevents rogue service accounts from bypassing institutional role hierarchies.
