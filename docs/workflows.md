# CampusOS Workflows & Enterprise Automation

**Tagline:** One Campus. One System. One Source of Truth.  
**Architecture Layer:** Automated Operations & Workflow Orchestration (Step 17)

---

## 1. Overview

CampusOS Workflows provide a tenant-isolated, auditable, and idempotent orchestration engine to automate recurring operational processes across institution domains:
- **Attendance Alerts:** Automated detection and parent/student notifications for attendance shortage below 75%.
- **Finance Reminders:** Nightly scans for overdue student invoices and payment reminders without automated ledger alterations.
- **Document Expiry:** Proactive notices for mandatory student, faculty, and institutional verification records approaching expiration.
- **Placement Summaries:** Weekly recruitment drive summaries and interview alerts.

---

## 2. Core Principles & Safety Restrictions

Workflows are an **orchestration layer, not a security bypass**.

### Forbidden Operations
Under no circumstances may a workflow:
1. Execute arbitrary Python (`eval()`, `exec()`), arbitrary SQL, or shell scripts.
2. Make unrestricted HTTP requests.
3. Automatically approve high-impact actions (financial refunds, fee waivers, grade changes, certificate issuance).
4. Forge certificates or alter document verification statuses.
5. Bypass PBAC permissions or tenant boundaries.

### Safe Domain Interactions
- Actions call existing, tested domain services (`NotificationService`, `AlertService`, `AuditService`).
- Conditions use a typed, non-executable comparison engine.
- Every workflow execution is tenant-isolated, recorded in immutable audit logs, and guarded by distributed locks.

---

## 3. Workflow Lifecycle

```text
  [ DRAFT ] ──────────> [ ACTIVE ] <──────────> [ PAUSED ]
                            │
                            ▼
                       [ ARCHIVED ]
```

- **DRAFT:** New workflow definition being configured. Cannot be triggered by events or schedules.
- **ACTIVE:** Validated and published. Eligible for execution via Schedules, Domain Events, or Manual triggers.
- **PAUSED:** Temporarily suspended. No new scheduled or event executions are admitted; ongoing runs complete safely.
- **ARCHIVED:** Permanently retired. Read-only historical record.

---

## 4. Immutable Versioning

When an `ACTIVE` workflow definition is modified (trigger or steps changed):
1. The historical version remains unchanged in `workflow_versions` with `is_active = False`.
2. A new version record is created with `version = N + 1` and `is_active = True`.
3. In-flight executions continue executing against their resolved historical version.
4. New executions automatically use the newest published version.

---

## 5. API Reference

All routes are mounted under `/api/v1/workflows` and require explicit PBAC permissions:

| Method | Endpoint | Permission | Description |
|---|---|---|---|
| `GET` | `/api/v1/workflows` | `workflows.read` | List tenant workflows |
| `POST` | `/api/v1/workflows` | `workflows.create` | Create workflow in DRAFT status |
| `GET` | `/api/v1/workflows/{id}` | `workflows.read` | Fetch workflow details |
| `PATCH` | `/api/v1/workflows/{id}` | `workflows.update` | Update workflow / bump version |
| `POST` | `/api/v1/workflows/{id}/activate` | `workflows.activate` | Publish and activate workflow |
| `POST` | `/api/v1/workflows/{id}/pause` | `workflows.pause` | Pause active workflow |
| `POST` | `/api/v1/workflows/{id}/archive` | `workflows.archive` | Archive workflow |
| `POST` | `/api/v1/workflows/{id}/execute` | `workflows.execute` | Manual execution dispatch |
| `GET` | `/api/v1/workflows/{id}/versions` | `workflows.read` | Version history |
| `GET` | `/api/v1/workflows/{id}/executions` | `workflow_executions.read` | Execution history |
| `GET` | `/api/v1/workflows/events` | `workflows.read` | Central event registry |
| `GET` | `/api/v1/workflows/actions` | `workflows.read` | Central action registry |
| `GET` | `/api/v1/workflows/metrics` | `workflows.read` | Operational metrics |
