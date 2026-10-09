# Notification Delivery Tracking, Retries & Suppression

## Delivery Model

Each notification dispatch is recorded in `campus_notification_deliveries` (`NotificationDelivery`):

- `id`: Unique delivery identifier.
- `tenant_id`: Mandatory tenant scope.
- `notification_id`: Parent in-app notification ID (for IN_APP deliveries).
- `event_id`: Reference to originating `NotificationEvent`.
- `recipient_user_id`: Target recipient user ID.
- `channel`: Channel used (`IN_APP`, `EMAIL`, `SMS`, `PUSH`).
- `status`: Delivery status.
- `provider`: Provider key used for dispatch.
- `provider_message_id`: External message ID returned by upstream provider.
- `attempt_count`: Current count of attempts.
- `scheduled_at`: Future dispatch time for quiet hours or deferred delivery.
- `idempotency_key`: Unique constraint preventing duplicate dispatches.
- `failure_classification`: Categorized failure reason.
- `suppression_reason`: Reason if message was suppressed.

## Delivery Status Lifecycle

```text
       ┌───────────► SCHEDULED (Quiet Hours / Deferral)
       │                 │
PENDING────────► PROCESSING ──► SUBMITTED (Provider Accepted) ──► DELIVERED (Confirmed)
       │                 │
       │                 ├──► RETRY_WAIT (Transient Failure)
       │                 │         │
       │                 │         └────────► PROCESSING (Backoff Elapsed)
       │                 │
       │                 └──► FAILED (Permanent Error / Retries Exhausted)
       │
       └────────► SUPPRESSED (User Opt-out, Bounce Registry, Policy)
```

## Idempotency & Duplicate Prevention

Duplicate dispatches caused by duplicate domain events or worker restarts are prevented by unique composite idempotency keys:

```text
idempotency_key = "{tenant_id}:{event_type}:{source_entity_id}:{recipient_id}:{channel}"
```

A repeated domain event will not generate duplicate deliveries unless the notification rule explicitly allows repetitive instances.

## Exponential Backoff Retry Policy

Transient failures (timeouts, network errors, upstream 5xx, rate limits) are scheduled for retry with exponential backoff:

```text
delay_seconds = min(initial_interval * (backoff_multiplier ^ (attempt_count - 1)), max_interval)
```

- **Initial Interval**: 60 seconds.
- **Backoff Multiplier**: 2.0.
- **Max Interval**: 3600 seconds (1 hour).
- **Max Attempts**: 3 attempts by default.

When max attempts are exhausted, the delivery transitions to `FAILED` with failure classification `PERMANENT` or `TIMEOUT`.

## Quiet Hours & Timezone Scheduling

- Users configure quiet hours (e.g. 22:00 to 07:00) with their local timezone in `UserNotificationProfile`.
- When an event arrives during quiet hours, messages with priority `NORMAL` or `LOW` are placed in `SCHEDULED` status with `scheduled_at` set to the exact end of quiet hours in user local time converted to UTC.
- Urgent security or mandatory notifications bypass quiet hours and deliver immediately.
- The background scheduler executes `dispatch_pending_notification_deliveries` every minute to sweep scheduled deliveries when their wake-up time arrives.

## Suppression Registry

Deliveries are evaluated against `notification_suppressions`:

- **BOUNCE**: Created automatically upon receiving permanent bounce webhooks from email/SMS providers.
- **COMPLAINT**: Created when spam complaint webhooks are reported.
- **USER_OPT_OUT**: When a user opts out of non-mandatory notification categories or specific channels.
- **POLICY_SUPPRESSED**: Institutional or regulatory suppression overrides.

Active suppression records prevent dispatch attempts and record `DeliveryStatus.SUPPRESSED` with the specific suppression reason.
