# CampusOS Enterprise Disaster Recovery & Business Continuity Runbooks

**Product Vision:** One Campus. One System. One Source of Truth.  
**Classification:** Internal Operational Runbook — Highly Privileged  
**Version:** 1.0 (Step 31)

---

## Reliability Objectives Summary

| Dimension | Target | Operational Standard |
|---|---|---|
| **Availability SLA** | **99.9%** | Measured monthly, excluding scheduled maintenance |
| **RTO Tier 1 (Critical)** | **<= 15 minutes** | Auth, Core Institution & People, Tenant Directory |
| **RTO Tier 2 (Essential)** | **<= 60 minutes** | Academic Records, Attendance, Exams, Finance, Documents |
| **RTO Tier 3 (Degradable)** | **<= 240 minutes** | Analytics, AI Intelligence, External Notifications |
| **RPO (Database)** | **<= 60 minutes** | Point-in-time recovery & scheduled snapshot archives |
| **RPO (Documents)** | **<= 24 hours** | Object storage replication & daily audit |
| **Outbox Max Delay** | **<= 300 seconds** | Transactional outbox event dispatch latency threshold |
| **Notification Max Delay**| **<= 60 seconds** | High-priority SMS/Email transactional delivery buffer |

---

## Runbook 1: PostgreSQL Outage & Database Failover

### 1. Detection Signals
- Prometheus alert: `PostgreSQLDown` or `DatabaseConnectionPoolExhausted`.
- Application `/health/ready` endpoint returns HTTP 503 (`database: down`).
- API logs flooded with `OperationalError: connection to server on socket failed` or `asyncpg.exceptions.CannotConnectNowError`.

### 2. Severity Classification
- **SEV-1 (CRITICAL)**: Total platform downtime.

### 3. Immediate Containment
- Nginx ingress retains incoming traffic with 502/503 retry-after headers; stops forwarding queries that might overload reconnect buffers.
- Pause background scheduler jobs to prevent connection thrashing:
  ```bash
  docker compose stop scheduler
  ```

### 4. Required Permissions & Prerequisites
- Platform Super Administrator access.
- SSH / Bastion access to database host or cloud PostgreSQL console.
- Docker or Kubernetes cluster administrative privileges.

### 5. Step-by-Step Recovery Commands
1. **Assess Primary Database Container / Service:**
   ```bash
   docker compose ps postgres
   docker compose logs --tail=100 postgres
   ```
2. **Attempt Clean Service Restart (Transient Lock / Crash):**
   ```bash
   docker compose restart postgres
   ```
3. **Verify Database Readiness:**
   ```bash
   docker compose exec postgres pg_isready -h localhost -p 5432 -U campusos_user
   ```
4. **If Primary Node Corrupted / Hardware Failure (Replica Promotion):**
   - Promote read-replica / standby node:
     ```bash
     pg_ctl promote -D /var/lib/postgresql/data
     ```
   - Update `DATABASE_URL` in `.env` or secret manager to point to promoted replica host.
5. **Restart API Services & Re-evaluate Readiness:**
   ```bash
   docker compose restart api worker scheduler
   curl -I http://localhost:8000/health/ready
   ```

### 6. Verification Checks
- `curl http://localhost:8000/health/ready` returns HTTP 200 with `"status": "healthy"`.
- Run health diagnostics:
  ```bash
  curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/api/v1/platform/reliability/status
  ```

### 7. Rollback or Abort Criteria
- If promoted replica reports WAL fork or data divergence, abort immediate restart; proceed to Runbook 2 (Database Corruption & PITR).

### 8. Post-Recovery Reconciliation
- Check transactional outbox for stuck processing events:
  ```bash
  curl -X POST -H "Authorization: Bearer <TOKEN>" http://localhost:8000/api/v1/platform/reliability/outbox/recover-abandoned
  ```

### 9. Communication & Escalation
- Escalate to Lead Infrastructure Architect if primary fails to recover within 10 minutes.
- Publish status incident update to institutional administrators.

---

## Runbook 2: Database Corruption & Point-in-Time Recovery

### 1. Detection Signals
- PostgreSQL log errors: `could not read block ... in file`, `invalid page in block`, or index corruption `ERROR: index ... contains corrupted page`.
- Application queries aborting with checksum failure.

### 2. Severity Classification
- **SEV-1 (CRITICAL)**.

### 3. Immediate Containment
- Immediately set API to read-only or maintenance mode to prevent writing corrupted transactions:
  ```bash
  docker compose stop api worker scheduler
  ```

### 4. Step-by-Step Recovery Commands
1. **Locate Latest Verified Known-Good Backup:**
   ```bash
   python scripts/backup.py --retention 30
   ls -lat ./backups/campusos_*.dump
   ```
2. **Execute Restore Verification in Isolated Sandbox Target:**
   ```bash
   python scripts/restore_verify.py --backup ./backups/campusos_db_<LATEST>.dump --sandbox-db campusos_recovery_sandbox
   ```
3. **Verify Integrity & Zero-Orphan Isolation:**
   Ensure `RestoreVerificationService` confirms `isolation_check_passed` and table counts match expectations.
4. **Drain Production Database & Apply Recovery Archive:**
   ```bash
   dropdb -h localhost -U campusos_user campusos_db_corrupted
   createdb -h localhost -U campusos_user campusos_db
   pg_restore -h localhost -U campusos_user -d campusos_db -v ./backups/campusos_db_<LATEST>.dump
   ```
5. **Run Alembic Migrations to Ensure Schema Alignment:**
   ```bash
   alembic upgrade head
   ```

### 5. Verification Checks
- Run sanity queries across canonical tables: `core_institutions`, `people_users`, `academic_programs`.
- Restart services:
  ```bash
  docker compose start api worker scheduler
  ```

---

## Runbook 3: Accidental Institutional Data Deletion

### 1. Detection Signals
- Institution administrator reports missing departmental, student, or financial records.
- Audit log shows unexpected bulk DELETE or soft-deletion actions.

### 2. Severity Classification
- **SEV-2 (HIGH)** for single-tenant data loss; **SEV-1** if cross-tenant.

### 3. Recovery Procedure
1. **Check Soft-Deletion Tables:**
   CampusOS uses `SoftDeleteMixin` (`deleted_at`) for core entities (`core_campuses`, `core_departments`, `documents_records`, `people_users`).
   Inspect soft-deleted records:
   ```sql
   SELECT id, name, deleted_at FROM core_departments WHERE tenant_id = '<TENANT_ID>' AND deleted_at IS NOT NULL;
   ```
2. **Recover via Soft-Deletion Restoration:**
   ```sql
   UPDATE core_departments SET deleted_at = NULL WHERE tenant_id = '<TENANT_ID>' AND deleted_at >= NOW() - INTERVAL '2 hours';
   ```
3. **If Hard-Deleted:**
   - Restore latest backup into isolated sandbox:
     ```bash
     python scripts/restore_verify.py --backup ./backups/<LATEST>.dump --sandbox-db campusos_extract_sandbox
     ```
   - Extract only the targeted tenant's records using `pg_dump --data-only -t ...` with WHERE tenant_id filter.
   - Insert extracted records back into production.

---

## Runbook 4: Failed Deployment & Application Rollback

### 1. Detection Signals
- Post-deployment health check failures on `/health/ready`.
- Spike in HTTP 500 errors or unhandled exception rates > 1%.
- Container crash loops (`CrashLoopBackOff`).

### 2. Severity Classification
- **SEV-1** or **SEV-2**.

### 3. Recovery Procedure (Expand-and-Contract Migration Safety)
1. **Identify Previous Stable Release Artifact / Container Tag:**
   ```bash
   git log -n 5 --oneline
   ```
2. **Validate Migration Reversibility:**
   - Check if current migration has destructive drops (`downgrade()` in migration).
   - If schema used expand-and-contract (additive columns only), application rollback does NOT require database downgrade.
3. **Rollback Container Image / Deployment Tag:**
   ```bash
   docker compose pull api:v<PREVIOUS_STABLE>
   docker compose up -d --no-deps api worker
   ```
4. **Verify Application Readiness:**
   ```bash
   curl -I http://localhost:8000/health/ready
   ```

---

## Runbook 5: Unavailable Object Storage (MinIO / S3)

### 1. Detection Signals
- S3 / MinIO circuit breaker trips: `s3_object_storage` state becomes `OPEN`.
- Document upload endpoints return HTTP 503 (`Object storage temporarily degraded`).
- Database records remain consistent; file contents buffered or rejected cleanly.

### 2. Severity Classification
- **SEV-2 (HIGH)** — ERP operates in degraded mode; non-document modules remain functional.

### 3. Recovery Procedure
1. Check storage container / service status:
   ```bash
   docker compose ps minio
   docker compose logs --tail=50 minio
   ```
2. Restart object storage daemon:
   ```bash
   docker compose restart minio
   ```
3. Run storage integrity audit via API:
   ```bash
   curl -X POST -H "Authorization: Bearer <TOKEN>" http://localhost:8000/api/v1/platform/reliability/storage/audit
   ```
4. Reset circuit breaker once storage endpoints respond to probes:
   ```bash
   curl -X POST -H "Authorization: Bearer <TOKEN>" http://localhost:8000/api/v1/platform/reliability/circuit-breakers/s3_object_storage/reset \
     -H "Content-Type: application/json" -d '{"reason": "MinIO container restored and responsive"}'
   ```

---

## Runbook 6: Redis or Distributed Cache Failure

### 1. Detection Signals
- Logs show `redis.exceptions.ConnectionError: Error connecting to redis:6379`.
- Distributed lock acquisition fails or tenant cache falls back to database queries.

### 2. Severity Classification
- **SEV-2 (HIGH)** — System degrades gracefully: cache bypasses to direct database queries.

### 3. Recovery Procedure
1. Inspect Redis status:
   ```bash
   docker compose ps redis
   docker compose logs --tail=50 redis
   ```
2. Restart Redis container:
   ```bash
   docker compose restart redis
   ```
3. Verify Redis ping:
   ```bash
   docker compose exec redis redis-cli ping
   ```
   Expected response: `PONG`.

---

## Runbook 7: Background Worker Outage & Abandoned Outbox Recovery

### 1. Detection Signals
- Outbox processing delay exceeds 300 seconds (`MAX_OUTBOX_QUEUE_DELAY_SECONDS`).
- Worker container exited or hung during event execution.
- Events accumulate in `status = 'PROCESSING'` without being marked `PROCESSED`.

### 2. Severity Classification
- **SEV-2 (HIGH)**.

### 3. Recovery Procedure
1. Restart worker replicas:
   ```bash
   docker compose restart worker
   ```
2. Trigger automated recovery of abandoned events (stuck > 300s):
   ```bash
   curl -X POST -H "Authorization: Bearer <TOKEN>" \
     "http://localhost:8000/api/v1/platform/reliability/outbox/recover-abandoned?stuck_threshold_seconds=300"
   ```
3. Verify queue lag recovery:
   ```bash
   curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/api/v1/platform/reliability/status
   ```
   Check that `outbox_queue_healthy` returns `true`.

---

## Runbook 8: Event Backlog Growth & Consumer Throttling

### 1. Detection Signals
- Outbox `pending_count` exceeds 5,000 events.
- Consumer lag alert triggers on `AuditTrailConsumer` or `NotificationEventConsumer`.

### 2. Recovery Procedure
1. Scale worker concurrency:
   ```bash
   docker compose up -d --scale worker=4
   ```
2. Check for Poison Pill events routing to Dead Letter:
   ```sql
   SELECT event_type, failure_reason, count(*) FROM event_dead_letters WHERE is_resolved = false GROUP BY event_type, failure_reason;
   ```
3. Resolve dead letters after fixing underlying consumer bug:
   ```bash
   curl -X POST -H "Authorization: Bearer <TOKEN>" http://localhost:8000/api/v1/events/dead-letter/<DLQ_ID>/retry
   ```

---

## Runbook 9: Notification Provider Outage (Email / SMS)

### 1. Detection Signals
- Provider circuit breakers trip: `notification_email_provider` or `notification_sms_provider` state is `OPEN`.
- Notification deliveries transition to `FAILED` or buffer in `SCHEDULED` state.

### 2. Degraded Mode Operation
- CampusOS notification engine automatically halts outbound HTTP spamming when the circuit trips.
- Deliveries are safely held in the database with bounded exponential retry delays.
- Core operations (grades, attendance, fees) proceed without error.

### 3. Recovery Procedure
1. Check third-party status page (e.g., SendGrid, Twilio, AWS SES).
2. Once upstream provider resolves their incident, reset circuit breaker:
   ```bash
   curl -X POST -H "Authorization: Bearer <TOKEN>" http://localhost:8000/api/v1/platform/reliability/circuit-breakers/notification_email_provider/reset \
     -H "Content-Type: application/json" -d '{"reason": "Upstream SMTP restored"}'
   ```
3. Trigger notification delivery sweep:
   Scheduler automatically sweeps retryable notifications on the next minute tick.

---

## Runbook 10: Compromised Credentials & Secret Rotation

### 1. Detection Signals
- Security alert: API key, JWT secret, database password, or provider secret committed or leaked.

### 2. Severity Classification
- **SEV-1 (CRITICAL)**.

### 3. Emergency Secret Rotation Steps
1. **Rotate JWT Secret Key (`SECRET_KEY`):**
   - Invalidate all existing sessions immediately:
     ```sql
     UPDATE people_user_sessions SET is_active = false, terminated_at = NOW();
     ```
   - Generate new cryptographic secret:
     ```bash
     openssl rand -hex 32
     ```
   - Update `SECRET_KEY` in environment config and restart API.
2. **Rotate Database Password (`POSTGRES_PASSWORD`):**
   ```sql
   ALTER USER campusos_user WITH PASSWORD '<NEW_STRONG_PASSWORD>';
   ```
   - Update `.env` / secret manager with new connection string.
   - Restart all backend containers (`api`, `worker`, `scheduler`).
3. **Rotate Integration & Storage Keys:**
   - Update MinIO / S3 access credentials.
   - Re-attach rotated credentials via Platform API.

---

## Runbook 11: Multi-Tenant Data Leakage or Isolation Incident

### 1. Detection Signals
- Automated isolation check query fails: orphan or cross-tenant records detected.
- User reports seeing another institution's department, student, or fee records.
- Security event logged: `CROSS_TENANT_RELATIONSHIP_PROHIBITED`.

### 2. Severity Classification
- **SEV-1 (CRITICAL)**.

### 3. Immediate Containment
1. **Terminate Active Sessions for Impacted Tenant:**
   ```sql
   UPDATE people_user_sessions SET is_active = false WHERE tenant_id = '<SUSPECT_TENANT_ID>';
   ```
2. **Temporarily Suspend Compromised Tenant via Platform API:**
   ```bash
   curl -X POST -H "Authorization: Bearer <TOKEN>" http://localhost:8000/api/v1/platform/tenants/<TENANT_ID>/transition \
     -H "Content-Type: application/json" \
     -d '{"target_status": "SUSPENDED", "reason": "Emergency containment of suspected isolation anomaly"}'
   ```
3. **Execute Zero-Orphan Isolation Integrity Audit:**
   ```sql
   SELECT count(*) FROM people_student_profiles WHERE tenant_id NOT IN (SELECT id FROM core_institutions);
   ```
4. **Audit Intelligence & Access Logs:**
   ```sql
   SELECT * FROM intelligence_audit_logs WHERE tenant_id = '<TENANT_ID>' ORDER BY created_at DESC LIMIT 100;
   ```
5. **Rectify & Re-enable:**
   - Patch query or repository filtering bug.
   - Run full test suite: `pytest apps/api/tests/test_saas_isolation.py`.
   - Reactivate tenant once containment and integrity verification are confirmed.
