# Enterprise Human Tasks & Work Queues (Step 25)

## Overview
A **Human Task** represents an actionable item requiring institutional judgment, review, approval, or data entry by an authorized university operator.

## Task Lifecycle
```text
PENDING -> CLAIMED -> IN_PROGRESS -> COMPLETED / REJECTED
   ↑          ↓
   └── RELEASED
```

## Concurrency-Safe Claiming & Release
- **Exclusive Claiming**: Tasks are claimed using atomic SQL conditional updates:
  ```sql
  UPDATE human_tasks
  SET status = 'CLAIMED', assigned_user_id = :user_id, claimed_at = :now
  WHERE tenant_id = :tenant_id AND id = :task_id AND status = 'PENDING'
    AND (assigned_user_id IS NULL OR assigned_user_id = :user_id)
  RETURNING id;
  ```
  If another operator concurrently claims the task, the second claim fails atomically and returns `TASK_ALREADY_CLAIMED` (HTTP 409 Conflict).
- **Atomic Release**: Claimed tasks can be released back to the queue only by the claiming operator.

## Human Decisions (`task_decisions`)
Decisions must be explicit and immutable. Allowed values:
- `APPROVE`: Authorize action and proceed.
- `REJECT`: Turn down request with mandatory reason.
- `REQUEST_CORRECTION`: Return to student/submitter with guidance.
- `RETURN`: Send back to previous reviewer.
- `ESCALATE`: Escalate to supervisor or higher-tier queue.
- `DEFER`: Postpone decision for additional information.

Every decision captures:
- Actor ID & timestamp
- Decision type & mandatory justification reason
- Optional evidence references and resulting workflow transition

## Temporary Delegations (`task_delegations`)
Operators can establish time-bounded authority delegations:
- `delegator_user_id` -> `delegatee_user_id`
- `valid_from` to `valid_until`
- Optional module scoping (`scope_module`)
- Delegations automatically expire via background scheduler.
