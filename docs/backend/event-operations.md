# Event Operations, Monitoring & Administration API

## 1. Overview & Permissions

CampusOS provides administrative APIs under `/api/v1/admin/events` for inspecting, managing, retrying, and replaying domain events.

All endpoints require strict multi-tenant authorization (`TenantContext`) and RBAC/PBAC permissions:

| Permission | Scope | Allowed Roles | Description |
|---|---|---|---|
| `DOMAIN_EVENTS_READ` | Tenant | `INSTITUTION_ADMIN` | List and inspect outbox events and dead-letter records |
| `DOMAIN_EVENTS_RETRY` | Tenant | `INSTITUTION_ADMIN` | Manually trigger retry for failed or dead-letter events |
| `DOMAIN_EVENTS_REPLAY` | Tenant | `INSTITUTION_ADMIN` | Clear consumer checkpoints and re-queue processed events |
| `DOMAIN_EVENTS_CONSUMERS_MANAGE` | Tenant | `INSTITUTION_ADMIN` | Inspect consumer registrations and checkpoints |
| `DOMAIN_EVENTS_METRICS_READ` | Tenant | `INSTITUTION_ADMIN` | Access backlog size, failure rate, and oldest pending latency |

---

## 2. API Endpoints Reference

### 2.1 Outbox Inspection
- `GET /api/v1/admin/events/outbox`
  - Query filters: `status`, `event_type`, `aggregate_type`, `correlation_id`, `from_date`, `to_date`, `skip`, `limit`.
  - Response: Paginated list of `OutboxEventResponse` with redacted payloads.
- `GET /api/v1/admin/events/outbox/{event_id}`
  - Response: Detailed event envelope including attempt history, error message, and associated dead-letter record if present.

### 2.2 Operational Retry & Replay
- `POST /api/v1/admin/events/outbox/{event_id}/retry`
  - Resets a `FAILED` or `DEAD_LETTER` event to `PENDING` with `available_at = NOW()`.
  - Audited with action `DOMAIN_EVENT_RETRY`.
- `POST /api/v1/admin/events/outbox/{event_id}/replay`
  - Body: `{"consumer_names": ["NotificationEventConsumer"]}` (or omit for all).
  - Deletes checkpoints for specified consumers and resets event status to `PENDING`.
  - Audited with action `DOMAIN_EVENT_REPLAY`.

### 2.3 Dead-Letter Review
- `GET /api/v1/admin/events/dead-letters`
  - Query filters: `event_id`, `skip`, `limit`.
  - Returns `EventDeadLetterResponse` with stack trace summaries and error contexts.

### 2.4 Consumer Health & Registration
- `GET /api/v1/admin/events/consumers`
  - Returns registered consumer classes, their subscribed events, and total execution stats.
- `GET /api/v1/admin/events/consumers/{consumer_name}/checkpoints`
  - Returns recent deduplication checkpoints, execution status, and processing duration for a consumer.

### 2.5 Health & Metrics
- `GET /api/v1/admin/events/metrics`
  - Returns operational health metrics:
    - `pending_count`: Current backlog of unprocessed events.
    - `processing_count`: In-flight events currently claimed.
    - `failed_count`: Events in retry backoff.
    - `dead_letter_count`: Events exhausted in dead-letter state.
    - `oldest_pending_seconds`: Age of the oldest unprocessed event in seconds.
    - `total_published_count`: Total events successfully processed.

---

## 3. Worker Execution Commands

### Local Development / Background Worker
```bash
# Run worker loop in apps/api directory
cd apps/api
python -m app.worker
```

### Scheduled Maintenance Job
The outbox cleanup job runs every hour via APScheduler:
```python
scheduler.add_job(
    cleanup_stale_outbox_events,
    IntervalTrigger(hours=1),
    id="cleanup_stale_outbox_events",
    name="Cleanup old published outbox events (30+ days)",
    replace_existing=True,
)
```
