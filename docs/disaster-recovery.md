# CampusOS Disaster Recovery Plan

Product Identity: **CampusOS — The operating system for modern colleges.**  
Tagline: **One Campus. One System. One Source of Truth.**

---

## 1. Objectives & Metrics

| Metric | Target | Definition |
| :--- | :--- | :--- |
| **RPO (Recovery Point Objective)** | **< 1 hour** (automated snapshot) / **< 5 min** (WAL replication) | Maximum allowable data loss in disaster scenarios. |
| **RTO (Recovery Time Objective)** | **< 30 minutes** (service restoration) | Maximum allowable time to restore full platform operations. |

---

## 2. Failure Scenarios & Response Runbooks

### Scenario 1: Primary Database Failure (PostgreSQL Crash / Corruption)
- **Detection:**
  - `/health/ready` probe returns HTTP 503 (`checks: {database: down}`).
  - PagerDuty/Slack alert triggered by `db_errors_total` spike.
- **Immediate Action:**
  1. Verify host server status and container health: `docker compose logs -f postgres`.
  2. Attempt local database service restart: `docker compose restart postgres`.
- **Recovery:**
  - If managed RDS/Cloud SQL: Trigger Multi-AZ automatic failover.
  - If standalone server failure: Provision a new database instance and execute restore:
    ```bash
    python scripts/restore_verify.py \
      --backup-file /opt/backups/latest.dump \
      --sandbox-db campusos_db
    ```
- **Verification:**
  - Query health probe: `curl -s https://api.campus.edu/health/ready | jq .`
  - Verify row counts on critical tables (`students`, `invoices`, `institutions`).
- **Communication:**
  - Post status update on institutional dashboard: *"Database undergoing maintenance; expected resolution 20 minutes."*
- **Post-Incident Review:** Document root cause (OOM, storage exhaustion, hardware fault), restore time, and WAL archive lag.

---

### Scenario 2: Redis Failure (Cache & Lock Outage)
- **Detection:**
  - Log entries showing Redis connection timeouts.
  - Rate limiting fallbacks to memory mode; distributed locks gracefully fallback.
- **Immediate Action:**
  - Inspect Redis memory usage: `redis-cli info memory`.
  - Restart Redis container: `docker compose restart redis`.
- **Recovery:**
  - Flush non-essential cache keys if memory full: `redis-cli flushall async`.
  - Redis data is ephemeral (cache and locks); application survives Redis restarts without data corruption.
- **Verification:**
  - `redis-cli ping` returns `PONG`.
  - Scheduler acquires locks cleanly.
- **Communication:**
  - Internal notification to ops team; no external tenant communication required unless session state affected.

---

### Scenario 3: API Service Failure (FastAPI Crash / Unhandled Loop)
- **Detection:**
  - Reverse proxy returns HTTP 502 Bad Gateway.
  - Container healthchecks fail `/health/live`.
- **Immediate Action:**
  - Docker Compose automatically restarts failing replicas (`restart: always`).
  - Check container stderr: `docker compose logs --tail 200 api`.
- **Recovery:**
  - If caused by bad code release: Roll back to previous image tag immediately.
  - If caused by resource exhaustion: Scale API replicas:
    ```bash
    docker compose up -d --scale api=4
    ```
- **Verification:**
  - Run deployment smoke test: `python scripts/smoke_test.py --api-url http://localhost:8000`.

---

### Scenario 4: Frontend Web Failure (Next.js SSR Crash)
- **Detection:**
  - Browser visits return HTTP 500 or timeout.
  - Cloudflare/UptimeRobot alerts on root domain.
- **Immediate Action:**
  - Inspect Next.js standalone process logs: `docker compose logs web`.
  - Verify backend API availability (`curl https://api.campus.edu/health`).
- **Recovery:**
  - Restart frontend containers: `docker compose restart web`.
  - If recent deployment caused fatal client bundle: Roll back to previous Web image.
- **Verification:**
  - Verify Next.js index and dynamic routes respond with HTTP 200.

---

### Scenario 5: Object Storage Outage (S3 / MinIO Unavailable)
- **Detection:**
  - Document uploads and certificate generation fail with storage timeout.
- **Immediate Action:**
  - Verify S3 bucket access credentials and endpoint connectivity.
- **Recovery:**
  - For MinIO: Restart MinIO container and verify volume mounts.
  - For Cloud S3: Verify AWS/Cloudflare service status and failover to replica bucket in secondary region.
- **Verification:**
  - Upload test document via storage test script and verify presigned download URL generation.

---

### Scenario 6: Secret or Credential Compromise
- **Detection:**
  - Leaked API key detected in logs or reported via security disclosure.
- **Immediate Action:**
  1. Revoke the compromised secret immediately in the cloud provider console.
  2. Rotate `SECRET_KEY` in `.env.production`.
  3. Invalidate all active user JWT sessions:
     - Clear Redis session tokens.
     - Increment user token version or reset session revocation table.
- **Recovery:**
  - Rolling restart of all API and worker instances to pick up new secrets.
- **Verification:**
  - Old tokens rejected with HTTP 401 Unauthorized; new logins succeed.
- **Post-Incident Review:** Audit cloud audit trails to verify if compromised credentials were used to export data.

---

### Scenario 7: Destructive Migration or Bad Deployment
- **Detection:**
  - Schema error or database constraint failures immediately following release.
- **Immediate Action:**
  - Halt deployment pipeline immediately.
- **Recovery:**
  - Roll back application containers to previous stable version.
  - If migration was backward-compatible, leave schema intact.
  - If migration caused data corruption, restore from pre-deployment snapshot to sandbox database, extract corrupted tables, and patch.
- **Verification:**
  - Run full test suite against staging; run smoke tests against production.
