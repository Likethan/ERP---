# Notification Operations, Observability & Runbook

## Operational Overview

This guide details operations, background worker maintenance, monitoring metrics, permissions, and troubleshooting procedures for the CampusOS Notification & Communication Layer.

## Background Jobs & Workers

The CampusOS background scheduler (`app/scheduler.py`) manages recurring notification processing:

1. **Pending & Retry Dispatch Sweep (`dispatch_pending_notification_deliveries`)**:
   - Frequency: Every minute.
   - Action: Sweeps deliveries in `SCHEDULED` status whose `scheduled_at <= now()`, and deliveries in `RETRY_WAIT` whose backoff interval has elapsed.
   - Dispatches via provider adapters and updates delivery attempt counters.

2. **Daily Batch Digests (`generate_notification_digests`)**:
   - Frequency: Scheduled hourly (runs once daily per tenant).
   - Action: Aggregates pending human tasks and unread operational alerts for users who have enabled `digest_enabled=True`.
   - Records execution in `notification_digest_runs` with unique `(tenant_id, digest_type, period)` constraints to prevent duplicate notifications.

## RBAC Permissions

| Permission | Description | Assigned Roles |
| :--- | :--- | :--- |
| `notification.read` | View personal inbox notifications | All Authenticated Users |
| `notification.manage_preferences` | Update notification preferences & quiet hours | All Authenticated Users |
| `notification_template.read` | View notification templates and versions | `INSTITUTION_ADMIN`, `SYSTEM_ADMIN` |
| `notification_template.manage` | Create, update, preview, publish templates | `INSTITUTION_ADMIN`, `SYSTEM_ADMIN` |
| `notification_rule.manage` | Configure event rules, channels, conditions | `INSTITUTION_ADMIN`, `SYSTEM_ADMIN` |
| `notification_delivery.read` | Access delivery history, logs, and attempts | `INSTITUTION_ADMIN`, `SYSTEM_ADMIN` |
| `notification_delivery.retry` | Trigger manual retry for eligible deliveries | `INSTITUTION_ADMIN`, `SYSTEM_ADMIN` |
| `notification_delivery.cancel` | Cancel scheduled or retrying deliveries | `INSTITUTION_ADMIN`, `SYSTEM_ADMIN` |
| `notification_analytics.read` | Access notification analytics & metrics | `INSTITUTION_ADMIN`, `SYSTEM_ADMIN` |
| `notification_provider.manage` | Configure connectors and provider settings | `INSTITUTION_ADMIN`, `SYSTEM_ADMIN` |

## Observability & Metrics API

Administrative analytics endpoint (`GET /api/v1/admin/notification-analytics`) provides institutional metrics:

- `total_notifications`: Count of generated inbox notifications.
- `total_deliveries`: Count of attempted deliveries across all channels.
- `deliveries_by_channel`: Channel distribution (`IN_APP`, `EMAIL`, `SMS`, `PUSH`).
- `deliveries_by_status`: Status breakdown (`DELIVERED`, `SUBMITTED`, `FAILED`, `SUPPRESSED`).
- `acceptance_rate_percentage`: Percentage of deliveries accepted by providers.
- `confirmed_delivery_rate_percentage`: Percentage of confirmed recipient receipts.
- `total_retries`: Number of retried delivery attempts.
- `total_suppressed`: Number of suppressed messages.
- `top_failure_reasons`: Frequency breakdown of failure classifications.

## Troubleshooting & Common Runbook Scenarios

### 1. Delivery Stuck in `SCHEDULED`
- **Cause**: User is in quiet hours or event scheduling policy specifies future execution.
- **Verification**: Check `delivery.scheduled_at` and `UserNotificationProfile.quiet_hours_end`.
- **Resolution**: Delivery will automatically dispatch once quiet hours elapse. Urgent alerts must use `priority="URGENT"` to bypass quiet hours.

### 2. Message Marked as `SUPPRESSED`
- **Cause**: Recipient bounced previously (`BOUNCE`), lodged spam complaint (`COMPLAINT`), or opted out of category in `NotificationPreference`.
- **Verification**: Query `notification_suppressions` for the recipient's identifier.
- **Resolution**: If resolved, an authorized administrator can deactivate the suppression entry in the suppression registry.

### 3. Provider Returns `UNCONFIGURED_CHANNEL`
- **Cause**: Tenant has enabled a notification channel (e.g., SMS or Email) without configuring a connector in `core_integration_connectors`.
- **Verification**: Check `GET /api/v1/admin/notification-providers/health`.
- **Resolution**: Register the appropriate connector credentials or route the event rule through supported channels (`IN_APP`).
