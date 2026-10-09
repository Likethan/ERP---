# CampusOS Workflow Engine Architecture

## 1. Engine Architecture

```text
                    CampusOS Core Services
                              │
                              ▼
                     Workflow Definition
                              │
                              ▼
                     Trigger Engine
               (Schedule / Event / Manual)
                              │
                              ▼
                     Execution Dispatcher
                   (Idempotency & Locks)
                              │
                              ▼
                     Workflow Runner
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
      Condition Engine  Action Executor   Forensic Audit
       (Zero Eval AST)  (Domain Services)   (AuditLog)
            │                 │
            └────────┬────────┘
                     ▼
             Execution Step Log
                     │
         (Success / Bounded Retry / Dead-Letter)
```

---

## 2. Condition Evaluation Engine

CampusOS strictly prohibits arbitrary code execution. The condition engine (`app/core/workflow_conditions.py`) evaluates JSON conditions against structured execution contexts.

### Supported Operators
- Equality: `==`, `!=`
- Comparison: `>`, `>=`, `<`, `<=`
- Membership: `IN`, `NOT_IN`
- Nullability: `IS_NULL`, `IS_NOT_NULL`
- String/Collection: `CONTAINS`

### Example Condition Definition
```json
{
  "all": [
    { "field": "percentage", "operator": "<", "value": 75 },
    { "field": "total_classes", "operator": ">=", "value": 10 }
  ]
}
```

---

## 3. Action Registry

Workflow actions (`app/core/workflow_actions.py`) dispatch strictly to existing domain services:

1. **`SEND_NOTIFICATION`**: Calls `NotificationService.create_notification` with deterministic deduplication keys.
2. **`CREATE_ALERT`**: Persists operational alerts to `intelligence_alerts`.
3. **`CREATE_AUDIT_EVENT`**: Writes immutable records to forensic audit logs.
4. **`QUEUE_DOCUMENT_EXPIRY_CHECK`**: Scans expiring documents within the tenant.
5. **`QUEUE_FEE_REMINDER`**: Identifies overdue fee invoices safely without ledger mutation.
6. **`QUEUE_ATTENDANCE_ALERT_CHECK`**: Scans attendance shortages below policy threshold.
7. **`GENERATE_REPORT_SUMMARY`**: Aggregates statistical summaries.

---

## 4. Concurrency & Idempotency Strategy

- **Idempotency Key:** Built deterministically from `tenant_id:workflow_id:trigger_type:trigger_ref:occurrence`.
- **Distributed Locking:** Leverages `DistributedLock` (backed by Redis with in-memory fallback) to guarantee only one replica processes a given workflow occurrence.
- **Duplicate Suppression:** If an execution with the idempotency key is already running or succeeded, subsequent calls immediately return the existing execution.

---

## 5. Retry Policy & Dead-Letter Handling

- **Retry Limit:** Default maximum 3 attempts per execution.
- **Backoff:** Bounded exponential backoff with jitter.
- **Permanent Error Classification:** Non-retryable errors (validation errors, permission rejections, missing entities) fail immediately without consuming worker capacity.
- **Dead-Letter Archiving:** When an execution exhausts its retry budget, a record is created in `workflow_dead_letters` preserving `failure_reason`, `last_error`, `attempt_count`, and chronological timestamps for administrative investigation.
