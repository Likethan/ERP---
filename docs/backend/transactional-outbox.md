# Transactional Outbox Pattern & Worker Reliability

## 1. Table Schema & Relational Design

The transactional outbox uses `workflow_outbox_events` (`app/models/workflow.py`), enriched with Step 27 metadata:

```sql
CREATE TABLE workflow_outbox_events (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE CASCADE,
    event_type VARCHAR(64) NOT NULL,
    schema_version VARCHAR(16) NOT NULL DEFAULT '1.0',
    aggregate_type VARCHAR(64) NOT NULL,
    aggregate_id VARCHAR(128) NOT NULL,
    payload JSONB,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    attempt_count INTEGER NOT NULL DEFAULT 0,
    available_at TIMESTAMP WITH TIME ZONE NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    correlation_id VARCHAR(128),
    causation_id VARCHAR(128),
    actor_id UUID REFERENCES people_users(id) ON DELETE SET NULL,
    actor_context JSONB DEFAULT '{}',
    producer VARCHAR(64) DEFAULT 'CORE',
    metadata_json JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_workflow_outbox_events_tenant_status_avail 
    ON workflow_outbox_events (tenant_id, status, available_at);
CREATE INDEX ix_workflow_outbox_events_status_avail 
    ON workflow_outbox_events (status, available_at);
CREATE INDEX ix_workflow_outbox_events_corr_id 
    ON workflow_outbox_events (correlation_id);
```

---

## 2. Polling, Concurrency & Locking Strategy

Outbox processing runs periodically in background workers (`app/worker.py`):

1. **Claiming Pending Events**:
   - Query: `WHERE status IN ('PENDING', 'FAILED') AND available_at <= NOW()`
   - Ordering: `ORDER BY available_at ASC`
   - Safe Concurrency: On PostgreSQL, uses `.with_for_update(skip_locked=True)` to prevent concurrent worker instances from double-claiming events.
   - Batch limits: Configurable batch size (default 50).

2. **Short Transaction Boundaries**:
   - The lock is acquired only to update state: `status = PROCESSING`, incrementing `attempt_count`.
   - The transaction is immediately committed. Locks are **never held across network requests or consumer execution**.

3. **Execution & Checkpointing**:
   - Each claimed event is processed through `ConsumerExecutionEngine.execute_consumer(...)`.
   - On completion across all registered consumers, event transitions to `PROCESSED`.

4. **Retry Backoff with Jitter**:
   - On transient failure, `attempt_count` increments and `available_at` is recalculated using bounded exponential backoff:
     $$\text{delay} = \min(2^{\text{attempt}} \times 2, 3600) + \text{jitter}(0, 2)$$
   - Status transitions to `FAILED` until `available_at` is reached.

5. **Terminal Failure & Dead-Letter Routing**:
   - When attempts exceed `max_retries` (default 5), status transitions to `DEAD_LETTER`.
   - An entry is durably saved in `event_dead_letters` containing the exact error trace, sanitized payload, and failure stage.

---

## 3. Retention & Archival

The cleanup task `cleanup_published_events(tenant_id, retention_days=30)`:
- Only deletes records where `status = PROCESSED` and `processed_at < NOW() - INTERVAL '30 days'`.
- **Never deletes** `PENDING`, `PROCESSING`, `FAILED`, or `DEAD_LETTER` events.
- Safely handles cascade deletion when an entire tenant is removed.
