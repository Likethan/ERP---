# CampusOS Performance Engineering, Capacity Planning & Scalability Architecture

## 1. Executive Summary & Core Principle

CampusOS operates on the principle: **One Campus. One System. One Source of Truth.**

As a multi-tenant enterprise ERP platform designed for higher education institutions ranging from 2,000 to 50,000+ students, CampusOS must handle heterogeneous workloads—from intense morning attendance bursts and examination registration rushes to long-running analytical query aggregations—while maintaining strict tenant isolation, zero data leaks, deterministic security boundaries, and consistent response times.

This document establishes:
1. Proposed Service Level Objectives (SLOs) and performance baselines.
2. Parameterized ERP workload profiles representing academic life cycles.
3. Database query indexing strategies and connection pool sizing formulas.
4. Tenant-isolated caching architectures with cache stampede protection.
5. Multi-tenant fairness controls, noisy-neighbor isolation, and graceful degradation runbooks.
6. Capacity planning methodologies for scaling institutions horizontally and vertically.

---

## 2. Proposed Service Level Objectives (SLOs)

All baseline targets below represent **proposed service objectives** for production deployment and are evaluated through repeatable benchmarks. Development and CI environments running single-core SQLite or containers differ from production clustered PostgreSQL and Redis deployments.

| Dimension | Target Objective | Critical Threshold (Alert) | Measurement Method |
| :--- | :--- | :--- | :--- |
| **API Read Latency (p50)** | $\le 40\text{ ms}$ | $> 100\text{ ms}$ | `TimingAndMetricsMiddleware` (excluding `/health*`) |
| **API Read Latency (p95)** | $\le 150\text{ ms}$ | $> 350\text{ ms}$ | In-memory percentile circular buffer / Prometheus |
| **API Read Latency (p99)** | $\le 350\text{ ms}$ | $> 800\text{ ms}$ | In-memory percentile circular buffer / Prometheus |
| **Transactional Write (p95)** | $\le 250\text{ ms}$ | $> 600\text{ ms}$ | Core mutations (attendance, mark entry, payments) |
| **Heavy Report / Export** | $\le 2.0\text{ s}$ or Async Job | $> 5.0\text{ s}$ (Synchronous) | Async job creation if execution estimate $> 1.5\text{ s}$ |
| **Error Rate (5xx)** | $< 0.05\%$ | $> 0.2\%$ | HTTP 5xx responses / total requests |
| **Timeout Rate (408/504)** | $< 0.01\%$ | $> 0.1\%$ | Aborted client requests or gateway timeouts |
| **DB Pool Saturation** | $\le 70\%$ peak | $> 85\%$ sustained ($> 60\text{s}$) | `checkedout_connections / pool_size` |
| **Cache Hit Ratio (Metadata)** | $\ge 85\%$ | $< 65\%$ | Hit count / (Hit count + Miss count) |
| **Background Outbox Lag** | $\le 3\text{ seconds}$ | $> 15\text{ seconds}$ | Max age of pending transactional outbox events |
| **Worker Concurrency Utilization** | $\le 75\%$ | $> 90\%$ sustained | Active async worker tasks / `WORKER_CONCURRENCY` |
| **Tenant Fairness Ratio** | $\le 1.5\times$ variation | $> 3.0\times$ degradation | Latency ratio between largest tenant and smallest tenant |

---

## 3. Parameterized Workload Profiles

Campus life follows distinct cyclic rhythms throughout the academic year. Rather than hard-coding institution counts or user populations, CampusOS models workloads using configurable parameters.

### 3.1 Normal Academic Day
- **Characteristics:** Steady, distributed read-heavy requests with low write concurrency.
- **RPS Profile:** 50–200 req/sec per 10,000 students.
- **Traffic Composition:** 75% reads (student profiles, notices, schedules), 15% transactional writes, 10% background jobs.

### 3.2 Morning Attendance Burst (8:30 AM – 9:30 AM)
- **Characteristics:** Rapid surge of faculty marking attendance simultaneously across hundreds of classroom sections.
- **Write Profile:** High write concurrency into `attendance_sessions` and `attendance_records`.
- **Target Bottleneck Mitigation:** Composite index `(tenant_id, course_offering_id, session_date)`, batch insert operations, read-committed transaction isolation, lock avoidance.

### 3.3 Examination Registration & Hall Ticket Surge
- **Characteristics:** Massive student concurrency attempting to verify course eligibility and download PDF hall tickets within a 48-hour window.
- **Traffic Composition:** 90% read/download, 10% registration state updates.
- **Target Bottleneck Mitigation:** Cached eligibility metadata (`tenant_cache`), pre-signed MinIO URLs for static PDF artifacts, tenant-level token bucket rate limits.

### 3.4 Examination Result Publication Rush
- **Characteristics:** Extreme spike in read queries immediately following notification broadcast ("Results Published").
- **Traffic Composition:** 98% reads on `examination_results`, student transcript views.
- **Target Bottleneck Mitigation:** Result caching by course and student, cache stampede locks (`async_single_flight`), read replicas for reporting queries.

### 3.5 Fee Payment & Semester Reconciliation
- **Characteristics:** High-value transactional integrity, strict write serialization for payment allocations and invoice adjustments. Zero tolerance for double-crediting.
- **Write Profile:** Pessimistic lock on `Invoice` rows during payment allocation, idempotent webhook ingestion from payment gateways.

### 3.6 Student & Faculty Directory Searches
- **Characteristics:** Ad-hoc partial string matching on names, roll numbers, emails, and department filters.
- **Target Bottleneck Mitigation:** Composite B-tree indexes on `(tenant_id, program_id, status)` and `(tenant_id, roll_number)`; frontend input debouncing (300ms) with `AbortController` cancellation.

### 3.7 Bulk Data Imports (Admissions & Academic Years)
- **Characteristics:** Administrators uploading CSV files with 1,000 to 10,000 student records or timetable structures.
- **Mitigation:** Asynchronous processing via `TenantJobRunner`, batch chunking (100 records per transaction), out-of-band progress reporting via WebSocket / notification.

### 3.8 Placement Drive Applications
- **Characteristics:** Concentrated application submissions for high-demand campus recruiting companies within strict deadlines.
- **Mitigation:** Atomic eligibility checks using indexed placement drives, background resume parsing and asynchronous notifications.

### 3.9 Heavy Report Generation & Analytics Aggregation
- **Characteristics:** Complex multi-table joins across historical attendance, exam marks, and financial balances for accreditation (NAAC, NIRF).
- **Mitigation:** Dedicated query timeout (15s), bounded page/export sizes (`MAX_EXPORT_ROWS=10000`), tenant concurrency limit (`TENANT_CONCURRENT_REPORTS_LIMIT=3`).

### 3.10 Large Document Uploads & Streaming Downloads
- **Characteristics:** High payload sizes (up to 25MB multipart), prolonged connection holding.
- **Mitigation:** Streaming directly to S3/MinIO via presigned URLs; payload size middleware enforcement; memory buffer isolation.

### 3.11 Multi-Institution SaaS Concurrency (Noisy Neighbor Defense)
- **Characteristics:** 50+ autonomous institutions on a shared infrastructure cluster. Institution A's sudden burst must not starve Institution B.
- **Mitigation:** Per-tenant sliding window rate limits, tenant-isolated connection budgets, prioritized worker queues.

---

## 4. Database Performance Architecture

### 4.1 Indexing Rationale (Migration 019)
Speculative indexing across all columns slows writes and inflates memory usage. Migration `019_enterprise_performance_indexes` applies targeted, evidence-based composite indexes:

1. **`people_students` (`idx_perf_students_tenant_prog_status`)**:
   - *Columns:* `(tenant_id, program_id, status)`
   - *Query Pattern:* Filter students by program and active status within tenant. Eliminates table scan across tens of thousands of student rows.
2. **`people_students` (`idx_perf_students_tenant_roll`)**:
   - *Columns:* `(tenant_id, roll_number)`
   - *Query Pattern:* Search by student roll number within tenant. Guarantees $O(\log N)$ index seek.
3. **`attendance_sessions` (`idx_perf_att_session_search`)**:
   - *Columns:* `(tenant_id, session_date, status)`
   - *Query Pattern:* Retrieval of daily attendance sessions by date and workflow status.
4. **`attendance_records` (`idx_perf_att_rec_student_date`)**:
   - *Columns:* `(tenant_id, student_id, created_at)`
   - *Query Pattern:* Student cumulative attendance percentage calculations and historical log retrieval.
5. **`finance_invoices` (`idx_perf_invoices_tenant_student_status`)**:
   - *Columns:* `(tenant_id, student_id, status)`
   - *Query Pattern:* Student billing dashboard, dues calculation, and unpaid balance queries.
6. **`finance_payments` (`idx_perf_payments_tenant_student_date`)**:
   - *Columns:* `(tenant_id, student_id, payment_date)`
   - *Query Pattern:* Payment history lookups and ledger statements.
7. **`campus_notifications` (`idx_perf_notif_tenant_recipient_unread`)**:
   - *Columns:* `(tenant_id, recipient_user_id, is_read, created_at)`
   - *Query Pattern:* User notification inbox badge queries and chronological feed filtering.

### 4.2 Query Patterns & Anti-Patterns
- **Eager Loading vs. Lazy Loading:** Async SQLAlchemy prohibits implicit lazy-loading. All required relations in read paths must be specified explicitly using `selectinload` or `joinedload`.
- **Projections:** When only summary metrics are needed (e.g. attendance percentage, fee balance), queries select specific columns or `func.count()`, bypassing ORM entity hydration overhead.
- **Deterministic Pagination:** Unbounded queries (`SELECT * FROM table`) are forbidden. All list endpoints enforce bounded page sizes (`MAX_PAGE_SIZE=100`) and deterministic ordering (`ORDER BY created_at DESC, id DESC`).

---

## 5. Connection Pools & Resource Capacity Planning

### 5.1 Connection Pool Sizing Formula
To prevent PostgreSQL `sorry, too many clients already` errors during unexpected traffic spikes:

$$\text{Total Connections} = (\text{API Instances} \times (\text{DB\_POOL\_SIZE} + \text{DB\_MAX\_OVERFLOW})) + (\text{Worker Replicas} \times \text{WORKER\_CONCURRENCY}) + \text{Superuser Reserved}$$

For a standard high-availability deployment:
- **API Instances:** 2 replicas $\times (20 + 10) = 60$ connections.
- **Worker Replicas:** 2 replicas $\times 5 = 10$ connections.
- **Monitoring & Migrations:** 10 connections.
- **Total PostgreSQL `max_connections` Required:** $\ge 80$ connections (Default system ceiling configured to 100).

### 5.2 Pool Saturation Safeguards
- `DB_POOL_TIMEOUT = 30`: Requests waiting $> 30\text{s}$ for a connection fail fast with a sanitized 500 rather than hanging indefinitely.
- `DB_POOL_RECYCLE = 1800`: Connections recycled every 30 minutes to eliminate stale or severed stateful connections.
- `pool_pre_ping = True`: SQLAlchemy sends a lightweight ping (`SELECT 1`) prior to handing connections to requests, transparently discarding dropped connections.

---

## 6. Safe, Tenant-Aware Caching Architecture

### 6.1 Cache Key Structure
Every cached key strictly follows the namespace format:
$$\text{tenant}:\{\text{tenant\_id}\}:\{\text{namespace}\}:\{\text{key}\}$$

Example:
- `tenant:439720e6-f139-434d-afd6-5d505202a506:academic_structure:departments_summary`
- `tenant:439720e6-f139-434d-afd6-5d505202a506:exam_term:terms_active`

### 6.2 Cache Stampede Prevention (Single-Flight Lock)
When a cold cache entry expires simultaneously for 500 concurrent students (e.g., examination timetable publication), a naive cache implementation queries the database 500 times.
CampusOS employs a single-flight mutex lock: only the first incoming request executes the database query; all other concurrent requests await the single in-flight resolution and read from the newly populated cache.

### 6.3 Redis Resiliency & Fallback
If the Redis cluster experiences network partitions or outages:
1. `TenantIsolatedCache` detects Redis connection exceptions without failing customer requests.
2. The engine falls back seamlessly to process-local in-memory caching or direct database read-through.
3. Errors are recorded in `metrics.record_cache_error()`, triggering operational alerts.

---

## 7. Multi-Tenant Fairness & Noisy-Neighbor Defense

1. **Client Identity Verification:** The rate limiter derives the tenant boundary strictly from validated JWT claims (`request.state.tenant`), never trusting arbitrary client-supplied HTTP headers.
2. **Per-Tenant Capacity Quota:** Each tenant is allocated a baseline of 1,200 requests/minute with a burst capacity of 200 requests. When exceeded, the platform returns HTTP 429 with `Retry-After: <seconds>`.
3. **Expensive Endpoint Throttling:** Report export, bulk sync, and intelligence endpoints maintain dedicated restrictive token buckets to prevent background queries from exhausting connection pools.
4. **Tenant Isolation Verification:** Tenant A's heavy export job runs in Tenant A's isolated job context and cannot lock tables or exhaust worker threads belonging to Tenant B.

---

## 8. Capacity Planning Workflow

When onboarding new institutions, operations engineers follow this capacity formula:

1. **Step 1: Estimate Concurrent User Peak ($U_{\text{peak}}$):**
   - Typically $20\%$ to $30\%$ of total student + faculty body.
   - For a 10,000 student campus: $U_{\text{peak}} \approx 2,500$ concurrent users.
2. **Step 2: Estimate Peak Request Rate ($R_{\text{peak}}$):**
   - Active user requests $\approx 0.1\text{ req/sec}$.
   - $R_{\text{peak}} \approx 2,500 \times 0.1 = 250\text{ RPS}$.
3. **Step 3: Provision API Workers:**
   - Single Uvicorn async worker handles $\approx 150\text{ RPS}$ of non-blocking I/O.
   - Required Uvicorn workers $= \lceil 250 / 150 \rceil + 1\text{ (headroom)} = 3\text{ workers}$.
4. **Step 4: Provision PostgreSQL RAM for Working Set:**
   - Active index working set $\approx 25\%$ of total database size.
   - Ensure PostgreSQL `shared_buffers` $\ge 25\%$ of system RAM and `effective_cache_size` $\ge 75\%$ of system RAM.

---

## 9. Operational Investigation Runbook

When performance degradation alerts fire:
1. **Check System Health:** Inspect `/health/ready` and `GET /api/v1/platform/performance`.
2. **Identify Slow Routes:** Review the top 10 slowest normalized routes in the performance API.
3. **Inspect DB Connection Saturation:** If `pool_saturation_pct` $> 85\%$, check active connections in PostgreSQL (`SELECT * FROM pg_stat_activity WHERE state = 'active'`).
4. **Evaluate Outbox Lag:** If outbox pending events $> 100$, verify worker process health (`campusos-worker`).
5. **Inspect Redis Latency:** If cache response time $> 5\text{ms}$, investigate network partitioning or Redis memory eviction.
