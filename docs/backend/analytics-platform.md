# Enterprise Data Platform & Analytics Architecture (Step 28)

## 1. Overview & Architectural Philosophy

CampusOS is a multi-tenant university ERP built around the foundational axiom:
> **One Campus. One System. One Source of Truth.**

The **Enterprise Data Platform, Real-Time Analytics & Business Intelligence Engine** provides governed, near-real-time business intelligence and institutional reporting across all university domains without ever compromising operational data integrity or violating tenant boundaries.

### Core Architectural Guarantees
1. **Single Source of Truth**: Analytical rollups and caches are derived views. They never become an independent or conflicting source of truth for financial transactions, attendance records, academic enrollments, or examination grades.
2. **Strict Multi-Tenant Isolation**: Analytical metrics, timeseries rollups, cache keys, data reconciliation findings, and report exports are strictly partitioned by `tenant_id`.
3. **Idempotent Near-Real-Time Ingestion**: Driven by the Step 27 Transactional Outbox and Domain Event Backbone, domain events update analytical aggregations idempotently with durable checkpointing.
4. **Governed Metric Registry**: Every institutional KPI is defined with formal formulas, owning domains, freshness SLAs, required PBAC permissions, and sensitivity ratings.
5. **Privacy Safeguards**: Small-cell privacy suppression masks cohort counts where $0 < N < 5$ (rendered as `"<5"`) to prevent demographic or cohort re-identification.
6. **Zero Raw SQL Injection**: Query filters, dimensions, metrics, and sort orders are validated against strict compile-time allowlists. Arbitrary user SQL is completely forbidden.

---

## 2. Analytics Tier Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Operational ERP Modules                         │
│  (Students, Academics, Attendance, Examinations, Finance, Placements)  │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                    Transactional Outbox (PostgreSQL)
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     Domain Event Backbone (Step 27)                    │
│   (student.enrollment.created, finance.payment.confirmed, etc.)        │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│              AnalyticsIngestionConsumer (app.core.analytics_ingestion) │
│  - Idempotent Event Deduplication & Checkpointing                     │
│  - Incremental Rollups into analytics_daily_metrics                    │
│  - Freshness & Telemetry Updates in analytics_metric_freshness         │
│  - Targeted Cache Invalidation                                         │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                       Analytical Storage Layer                         │
│  - analytics_daily_metrics (Daily aggregate rollups by dimension)      │
│  - analytics_metric_freshness (SLA tracking, lag, event telemetry)     │
│  - analytics_reconciliation_findings (Discrepancy audit findings)      │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   Analytics Service & Query API                        │
│  - Governed Metric Registry Validation (app.core.metric_registry)      │
│  - PBAC Authorization & Small-Cell Privacy Masking (<5)                │
│  - 9 Enterprise Dashboard Contracts (/api/v1/analytics/dashboards/*)   │
│  - Sanitized CSV & JSON Exports (/api/v1/analytics/export)             │
│  - Automated Reconciliation Engine (app.services.data_quality_...)     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Database Schema

The analytics platform introduces three dedicated relational tables via Alembic migration `015_enterprise_data_platform_analytics`:

### 3.1 `analytics_daily_metrics`
Persists pre-aggregated daily summaries partitioned by tenant and dimension:
- `id` (`UUID`, PK)
- `tenant_id` (`UUID`, indexed, non-null)
- `metric_id` (`VARCHAR(100)`, indexed, non-null)
- `metric_date` (`DATE`, indexed, non-null)
- `dimension_type` (`VARCHAR(50)`, default `'OVERALL'`)
- `dimension_value` (`VARCHAR(100)`, default `'ALL'`)
- `metric_value` (`NUMERIC(14, 4)`, non-null)
- `record_count` (`INTEGER`, default `1`)
- `metadata_json` (`JSONB`, nullable)
- `created_at`, `updated_at` (`TIMESTAMPTZ`)
- **Unique Constraint**: `uq_analytics_daily_metric (tenant_id, metric_id, metric_date, dimension_type, dimension_value)`

### 3.2 `analytics_metric_freshness`
Tracks data freshness, processing lag, and ingestion telemetry per metric:
- `id` (`UUID`, PK)
- `tenant_id` (`UUID`, indexed, non-null)
- `metric_id` (`VARCHAR(100)`, indexed, non-null)
- `last_updated_at` (`TIMESTAMPTZ`, non-null)
- `last_event_timestamp` (`TIMESTAMPTZ`, nullable)
- `lag_seconds` (`INTEGER`, default `0`)
- `status` (`VARCHAR(30)`: `FRESH`, `UPDATING`, `STALE`, `RECONCILING`, `ERROR`)
- `source_event_count` (`INTEGER`, default `0`)
- `error_message` (`TEXT`, nullable)
- **Unique Constraint**: `uq_analytics_metric_freshness (tenant_id, metric_id)`

### 3.3 `analytics_reconciliation_findings`
Maintains audit logs of automated data-quality discrepancy checks:
- `id` (`UUID`, PK)
- `tenant_id` (`UUID`, indexed, non-null)
- `rule_code` (`VARCHAR(100)`, non-null)
- `severity` (`VARCHAR(20)`: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFO`)
- `affected_metric` (`VARCHAR(100)`, non-null)
- `operational_value` (`NUMERIC(14, 4)`, nullable)
- `analytical_value` (`NUMERIC(14, 4)`, nullable)
- `variance` (`NUMERIC(14, 4)`, nullable)
- `variance_pct` (`NUMERIC(8, 4)`, nullable)
- `details` (`JSONB`, nullable)
- `status` (`VARCHAR(30)`: `OPEN`, `ACKNOWLEDGED`, `RESOLVED`, `FALSE_POSITIVE`)
- `detected_at`, `resolved_at` (`TIMESTAMPTZ`)

---

## 4. Event Ingestion Pipeline

The `AnalyticsIngestionConsumer` inherits from `BaseDomainEventConsumer` (Step 27) and is registered in `ConsumerRegistry`:
- **Consumer ID**: `analytics_ingestion_consumer`
- **Subscribed Events**:
  - `student.enrollment.created`
  - `student.profile.updated`
  - `attendance.session.finalized`
  - `examination.results.published`
  - `finance.payment.confirmed`
  - `placement.offer.created`
  - `document.certificate.issued`
  - `workflow.case.completed`

### Ingestion Properties
- **Idempotence**: Tracked via `event_consumer_checkpoints`. Redelivered events are recognized and do not double-increment metrics.
- **Immediate Upsert**: Aggregates for the event date are incremented in `analytics_daily_metrics` via atomic database upsert.
- **Freshness Telemetry**: `AnalyticsMetricFreshness` is updated with lag calculation relative to UTC `datetime.now()`.
- **Cache Eviction**: In-memory and Redis caches for the tenant and owning domain are invalidated on write.

---

## 5. Security, PBAC & Privacy

### 5.1 Permissions
All analytics endpoints are guarded by granular permissions defined in `app/core/permissions.py`:
- `analytics.read` / `analytics:read`: View dashboard overviews and freshness status.
- `analytics.query` / `analytics:query`: Execute timeseries, breakdown, and comparison queries.
- `analytics.export` / `analytics:export`: Request CSV or JSON exports of analytical datasets.
- `analytics.manage` / `analytics:manage`: Reconfigure metric registry definitions and view system health.
- `analytics.reconcile` / `analytics:reconcile`: Trigger data reconciliation scans and review findings.
- `analytics.backfill` / `analytics:backfill`: Trigger historical operational rollups.

### 5.2 Small-Cell Privacy Suppression
To comply with student privacy policies (e.g. FERPA, digital data protection laws), any grouped demographic or departmental metric breakdown returning a count between 1 and 4 is suppressed:
- Metric value is clamped.
- `record_count` in response JSON is rendered as `"<5"`.
- Prevents deduction of individual student identities in small cohort sizes.

### 5.3 Export Formula Injection Sanitization
All CSV export generation cleans values beginning with `=, +, -, @, \t, \r` by prepending a single quote `'`, preventing spreadsheet formula injection when opened in Microsoft Excel or Google Sheets.

---

## 6. Scheduled Jobs & Background Tasks

The scheduler (`app/scheduler.py`) runs the periodic job `refresh_analytics` configured to:
1. Iterate across all active tenants.
2. Execute historical rollups for active academic metrics.
3. Run the automated data quality reconciliation engine (`DataQualityReconciliationService`).
4. Log and persist any discrepancy findings in `analytics_reconciliation_findings`.
