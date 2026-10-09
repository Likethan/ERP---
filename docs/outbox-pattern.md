# CampusOS Transactional Outbox Pattern

## 1. Problem Statement

In distributed and event-driven architectures, publishing an event directly over a network queue or message broker before committing the database transaction can lead to ghost events (event published, but DB transaction rolls back). Conversely, committing the database transaction and then attempting to publish the event can result in lost events (DB committed, but network/process crashes before event publication).

---

## 2. Transactional Outbox Solution

CampusOS uses the **Transactional Outbox Pattern** to ensure zero event loss and strict atomicity between state mutations and event publication:

```text
Domain Service Operation (e.g., mark attendance, issue invoice)
         │
         ▼
Active DB Transaction
   ├── 1. Apply database changes (INSERT/UPDATE domain entities)
   └── 2. Insert OutboxEvent (status = PENDING)
         │
         ▼
     COMMIT
         │
         ▼
Outbox Worker Loop (`app/worker.py`)
   ├── 1. Poll `outbox_events` WHERE status = PENDING AND available_at <= NOW()
   ├── 2. Atomically mark status = PROCESSING
   ├── 3. Dispatch to `WorkflowService.dispatch_domain_event()` inside `TenantJobRunner`
   └── 4. On success: mark PROCESSED (with timestamp)
          On failure: calculate exponential backoff retry; if max retries reached -> DEAD_LETTER
```

---

## 3. Database Schema (`outbox_events`)

```sql
CREATE TABLE outbox_events (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES core_institutions(id),
    event_type VARCHAR(64) NOT NULL,
    aggregate_type VARCHAR(64) NOT NULL,
    aggregate_id VARCHAR(128) NOT NULL,
    payload JSONB,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    attempt_count INTEGER NOT NULL DEFAULT 0,
    available_at TIMESTAMP WITH TIME ZONE NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

Indexes:
- `idx_outbox_pending_available (status, available_at)`
- `idx_outbox_tenant_event (tenant_id, event_type)`

---

## 4. Failure Recovery & Dead-Letter State

- If a worker crashes while processing an event, the event can be recovered after a timeout.
- Failed dispatch attempts increment `attempt_count` and compute an exponential backoff delay:
  $$\text{delay} = \min(3600, 2^{\text{attempt}} \times 10) \text{ seconds}$$
- When `attempt_count >= max_retries` (default 5), the event status transitions to `DEAD_LETTER` for forensic inspection without blocking subsequent events.
