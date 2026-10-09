# Idempotent Event Consumer Framework

## 1. Overview & Architecture

To achieve safe at-least-once message processing without duplicate side effects, CampusOS implements an idempotent consumer architecture (`app/core/event_consumer.py`).

Each consumer tracks execution state per event in `event_consumer_checkpoints`:

```sql
CREATE TABLE event_consumer_checkpoints (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES core_institutions(id) ON DELETE CASCADE,
    consumer_name VARCHAR(128) NOT NULL,
    event_id UUID NOT NULL REFERENCES workflow_outbox_events(id) ON DELETE CASCADE,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    attempt_count INTEGER NOT NULL DEFAULT 1,
    processed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    error_message TEXT,
    is_retryable BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX uq_consumer_event_checkpoint 
    ON event_consumer_checkpoints (tenant_id, consumer_name, event_id);
```

---

## 2. Deduplication & Idempotency Rules

When an event is dispatched to consumer $C$:

1. **Check Existing Checkpoint**:
   - If checkpoint status is `PROCESSED`: Event is skipped immediately without re-executing consumer logic.
   - If checkpoint status is `FAILED` and `is_retryable = False` (poison pill): Event is skipped immediately.
   - If no checkpoint exists or status is retryable `FAILED`: Consumer executes.

2. **Poison Pill Suppression**:
   - Consumers raising `NonRetryableConsumerError` are marked `is_retryable = False`.
   - The engine logs the error and suppresses infinite retry loops on malformed messages.

3. **Duration & Metric Tracking**:
   - Checkpoints record `duration_ms` using high-precision timers, providing observability into consumer performance.

---

## 3. Built-in Registered Consumers

| Consumer Name | Subscribed Events | Responsibility |
|---|---|---|
| `NotificationEventConsumer` | Student enrollment, low attendance, exam results, payments, placement offers, certificates, case updates | Coordinates tenant communication channels (email, SMS, WhatsApp, push) via `NotificationOrchestrationService` |
| `WorkflowEventConsumer` | Core domain events, SLA breaches, case escalations, failed deliveries | Dispatches events to active tenant workflows configured with matching triggers via `WorkflowService` |
| `AuditTrailConsumer` | Wildcard `*` | Records asynchronous tenant audit trails in `audit_logs` without impacting the hot path |

---

## 4. Registering Custom Consumers

Consumers inherit from `BaseDomainEventConsumer` and are registered in `ConsumerRegistry`:

```python
from app.core.event_consumer import BaseDomainEventConsumer, ConsumerResult, ConsumerRegistry
from app.core.events import DomainEventEnvelope
from app.models.event import ConsumerCheckpointStatus

class CustomInventoryConsumer(BaseDomainEventConsumer):
    @property
    def consumer_name(self) -> str:
        return "CustomInventoryConsumer"

    @property
    def subscribed_events(self) -> list[str]:
        return ["hostel.asset.allocated", "library.book.issued"]

    async def handle_event(self, envelope: DomainEventEnvelope, db: AsyncSession) -> ConsumerResult:
        # Business logic here
        return ConsumerResult(status=ConsumerCheckpointStatus.PROCESSED)

# Register at application startup:
ConsumerRegistry.register(CustomInventoryConsumer())
```
