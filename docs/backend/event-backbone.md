# Enterprise Domain Event Backbone & Architecture

## 1. Overview & Architectural Philosophy

CampusOS implements a durable, multi-tenant enterprise domain event backbone built upon the **Transactional Outbox Pattern** and an **Idempotent Consumer Framework**. This architecture guarantees that domain state changes (e.g., student enrollment, exam publication, fee payment confirmation, case closure) and their corresponding domain events commit atomically in the same database transaction.

### Guarantees
- **At-Least-Once Delivery**: Events are durably persisted before emission. Process crashes or network drops cannot cause lost events.
- **Idempotent Consumption**: Every consumer maintains durable per-consumer execution checkpoints (`event_consumer_checkpoints`). Re-delivering or replaying an event does not trigger duplicate side-effects.
- **Strict Multi-Tenant Isolation**: Outbox records, consumer checkpoints, dead-letters, and administrative actions are strictly scoped by `tenant_id`. Cross-tenant data leakage is prevented at database query and API gateway levels.
- **Zero In-Memory Single Points of Failure**: The transactional outbox in PostgreSQL/SQLAlchemy is the authoritative source of truth.

---

## 2. Event Envelope Contract & Schema Versioning

Every event conforms to the versioned `DomainEventEnvelope` contract:

```json
{
  "event_id": "8d351c5e-1005-4655-bbb3-be110766d951",
  "event_type": "finance.payment.confirmed",
  "schema_version": "1.0",
  "tenant_id": "b15b04c5-6f4c-4165-b1df-f48cfb08fbb8",
  "aggregate_type": "Payment",
  "aggregate_id": "01234567-89ab-cdef-0123-456789abcdef",
  "occurred_at": "2026-10-09T14:30:00Z",
  "correlation_id": "req-987234-abcd",
  "causation_id": "evt-81234-prev",
  "actor_id": "c1234567-89ab-cdef-0123-456789abcdef",
  "actor_context": {
    "role": "FINANCE_OFFICER",
    "ip_address": "192.168.1.10"
  },
  "producer": "FINANCE_MODULE",
  "payload": {
    "payment_id": "01234567-89ab-cdef-0123-456789abcdef",
    "invoice_id": "23456789-abcd-ef01-2345-6789abcdef01",
    "amount": "15000.00",
    "currency": "INR",
    "payment_method": "ONLINE",
    "transaction_reference": "TXN_78912345"
  },
  "metadata": {
    "environment": "production"
  }
}
```

### Schema Version Policy
- Schema versions follow SemVer string conventions (`1.0`, `1.1`).
- The system supports `SUPPORTED_SCHEMA_VERSIONS = {"1.0"}`.
- Backward compatibility: Adding non-breaking optional fields increments minor version. Breaking payload schema modifications increment major versions.
- Unsupported schema versions are safely rejected with `ValidationException` during emission and ingestion.

---

## 3. Canonical Event Registry & Aliases

CampusOS maintains a centralized registry of domain events in `app/core/events.py`. Events support both dot-notated canonical names and backward-compatible uppercase enum identifiers:

| Canonical Dot Name | Uppercase Alias | Aggregate Type | Source Module |
|---|---|---|---|
| `student.enrollment.created` | `STUDENT_ENROLLED` | `CourseEnrollment` | `academics` |
| `attendance.session.finalized` | `ATTENDANCE_MARKED` | `AttendanceSession` | `attendance` |
| `attendance.low_threshold` | `ATTENDANCE_THRESHOLD_REACHED` | `AttendanceSummary` | `attendance` |
| `examination.results.published` | `EXAM_RESULT_PUBLISHED` | `Assessment` | `examinations` |
| `finance.payment.confirmed` | `PAYMENT_RECEIVED` | `Payment` | `finance` |
| `finance.payment.failed` | `FINANCE_PAYMENT_FAILED` | `Payment` | `finance` |
| `placement.offer.created` | `PLACEMENT_OFFER_ACCEPTED` | `PlacementOffer` | `placement` |
| `document.certificate.issued` | `CERTIFICATE_ISSUED` | `Document` | `documents` |
| `workflow.case.completed` | `CASE_COMPLETED` | `Case` | `case_management` |
| `notification.delivery.failed` | `NOTIFICATION_DELIVERY_FAILED` | `NotificationDelivery` | `notifications` |

Unregistered or arbitrary event names cannot be emitted or consumed; doing so raises `ValidationException`.

---

## 4. Transactional Emission Pattern

Domain services emit events using `OutboxService.publish_event` **within their active database transaction without committing**:

```python
# Inside Domain Service (e.g., CaseService.close_case)
case.status = CaseStatus.CLOSED
case.closed_at = datetime.now(UTC)

# Atomically insert Outbox record
await OutboxService.publish_event(
    db=self.db,
    tenant_id=tenant_id,
    event_type="workflow.case.completed",
    aggregate_type="Case",
    aggregate_id=case.id,
    payload={
        "case_id": str(case.id),
        "case_number": case.case_number,
        "resolution": "Resolved",
    },
    actor_id=actor_id,
    producer="CASE_MANAGEMENT_MODULE",
)

# Active transaction commits BOTH case entity update AND outbox event
await self.db.commit()
```

If the domain operation or transaction aborts, the outbox record is rolled back automatically. No phantom events can ever be emitted.
