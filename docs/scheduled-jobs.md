# CampusOS Scheduled Jobs & Batch Operations

## 1. Overview

CampusOS includes a dedicated production scheduler (`apps/api/app/scheduler.py`) running periodic maintenance tasks and evaluating scheduled workflows across all active institutions.

---

## 2. Distributed Execution & High Availability

In multi-instance deployments (e.g. Kubernetes, Docker Compose replicas), multiple scheduler containers may run concurrently. Single-execution semantics are guaranteed via `DistributedLock`:

```text
Scheduler Node 1 ──┐
                   ├──> DistributedLock("scheduler:workflow_schedules", TTL=60s)
Scheduler Node 2 ──┘        │
                            ├──> Acquired? Run job for all active tenants
                            └──> Locked? Skip tick safely
```

---

## 3. Timezone Awareness

CampusOS serves colleges across multiple timezones. Schedulers **never assume UTC** for tenant-facing schedules.

1. Each institution configured in `core_institutions` possesses a `default_timezone` (e.g., `Asia/Kolkata`, `America/New_York`).
2. When evaluating scheduled workflow triggers, the current local time is computed using `zoneinfo.ZoneInfo(tenant.timezone)`.
3. An institution workflow configured to run at `08:30` triggers at `08:30` in that college's local wall-clock time.
4. All database timestamps (`created_at`, `started_at`, `completed_at`) are stored in strict UTC.

---

## 4. Tenant Lifecycle Verification

The scheduler delegates tasks through `TenantJobRunner`:
- **ACTIVE Tenants:** Executed normally.
- **SUSPENDED Tenants:** Skipped by default to prevent resource consumption.
- **ARCHIVED Tenants:** Blocked and skipped.
- **Fault Isolation:** An unhandled error in Institution A never aborts or delays processing for Institution B.

---

## 5. Routine Maintenance Jobs

| Job Name | Frequency | Target | Description |
|---|---|---|---|
| `workflow_schedules` | Every 60s | All Active Tenants | Evaluates active `SCHEDULE` workflows in local timezone |
| `document_expiry` | Hourly | All Active Tenants | Identifies expiring student/staff records |
| `fee_overdue` | Hourly | All Active Tenants | Flags overdue student invoices and queues fee notices |
| `attendance_alerts` | Hourly | All Active Tenants | Recalculates low-attendance thresholds |
| `analytics_refresh` | Hourly | All Active Tenants | Rebuilds aggregated analytics summaries |
