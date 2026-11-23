# CampusOS Observability, Metrics & Health Monitoring Architecture

## 1. Observability Pillars

CampusOS implements the three standard pillars of operational observability:
1. **Structured Logging:** Context-correlated, secret-scrubbed application logs.
2. **Operational Metrics:** In-memory high-throughput counters, gauges, and latency trackers.
3. **Traceability:** Unique `X-Request-ID` correlation across HTTP lifecycles, background jobs, and database exceptions.

---

## 2. Structured Logging

Application logs are formatted through `StructuredLogFormatter`:
```text
2026-10-05 19:15:20 [INFO] [campusos] [req:8a1d7f6b-3e5c-4a9f-a83d-3b5e4a8f9c1d] User authentication successful: user=123 tenant=456 duration_ms=42
```
Key capabilities:
- **Automatic Request Correlation:** Injected via `RequestCorrelationMiddleware` and preserved in async tasks via Python `contextvars.ContextVar`.
- **Sensitive String Scrubbing:** Automatically detects and redacts passwords in database connection strings and Bearer tokens in headers.
- **Log Level Discipline:** Controlled by `settings.ENVIRONMENT`. Production environments run strictly on `INFO` or higher to eliminate noise and prevent debug-level data leaks.

---

## 3. Application Metrics Architecture (`MetricsCollector`)

The in-memory metrics engine collects real-time indicators across five operational domains:

### HTTP Traffic & Latency
- `total_requests`: Monitored by HTTP method, status code, and coarsened route prefix.
- `total_errors`: Breakdown by status code (`400`, `401`, `403`, `404`, `422`, `429`, `500`, `503`).
- `avg_latency_ms` & `max_latency_ms`: Rolling 1,000-request window latency gauge.

### Security Indicators
- `auth_failures`: Total consecutive login failures and credential rejection count.
- `authorization_denials`: Total 403 Forbidden permission denials.
- `rate_limit_events`: Total 429 Too Many Requests rate-limiting events.

### Database Health
- `errors_total`: Count of SQLAlchemy/DBAPI connection or integrity failures.

### Background Jobs
- Execution status breakdown: `PENDING`, `RUNNING`, `SUCCESS`, `FAILED`, `RETRYING`.

### AI & Intelligence
- `requests_total`: AI queries orchestrated.
- `failures_total`: Provider or tool execution errors.
- `avg_latency_ms`: Natural language and domain tool latency.

---

## 4. Health Probes & Monitoring Endpoints

### 1. Root Liveness Probe (`GET /health/live`)
- **Purpose:** Verifies that the FastAPI process is active, accepting sockets, and not deadlocked.
- **Response:**
  ```json
  {
    "success": true,
    "data": {
      "status": "healthy",
      "service": "CampusOS API",
      "version": "0.1.0",
      "environment": "production",
      "checks": { "process": "alive" }
    }
  }
  ```

### 2. Root Readiness Probe (`GET /health/ready`)
- **Purpose:** Verifies that external infrastructure dependencies (PostgreSQL database, Redis cache) are ready to accept traffic.
- **Action:** Executes `SELECT 1` on database connection pool.
- **Response (Operational):** HTTP 200 OK.
- **Response (Degraded / DB Down):** HTTP 503 Service Unavailable with `checks: {"database": "down"}`.

### 3. Operational Metrics (`GET /metrics`)
- **Purpose:** Exposes comprehensive JSON telemetry snapshot for monitoring agents or Prometheus exporters.

---

## 5. Operations Dashboard Contract

Recommended operations dashboard panels:

| Panel | Metric Key | Alert Threshold | Severity |
| :--- | :--- | :--- | :--- |
| **API Error Spike** | `http.status_breakdown.500` | > 10 errors / minute | HIGH |
| **Database Pool Exhaustion** | `database.errors_total` | > 5 errors / minute | CRITICAL |
| **Brute-Force Spike** | `security.auth_failures` | > 20 failures / 5 min | HIGH |
| **Rate Limit Breach** | `security.rate_limit_events` | > 50 events / minute | MEDIUM |
| **High API Latency** | `http.avg_latency_ms` | > 500 ms sustained 5 min | MEDIUM |
| **Job Retries Exhausted** | `background_jobs.*:FAILED` | > 3 failures / hour | HIGH |
| **AI Outage** | `ai.failures_total` | > 5 failures / 5 min | MEDIUM |
