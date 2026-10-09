# Provider Integrations & Adapters

## Channel Provider Abstraction

CampusOS uses provider-independent adapter interfaces (`app.integrations.adapters.notification`) allowing hot-swappable communication providers without altering core ERP business logic.

### Supported Channels

1. **IN_APP**:
   - Status: **Fully Implemented & Verified**.
   - Backed by internal `campus_notifications` inbox table.
   - Provides unread badges, mark-read, mark-all-read, deep-links, and category grouping.

2. **EMAIL**:
   - Status: **Adapter Interface Implemented / Unconfigured by Default**.
   - Base Adapter: `EmailProvider` / `GenericEmailAdapter`.
   - Production connectors: SMTP, SendGrid, Amazon SES.
   - Without configured connector credentials, reports `UNCONFIGURED_CHANNEL` or `UNCONFIGURED` status. Never fabricates fake external delivery.

3. **SMS**:
   - Status: **Adapter Interface Implemented / Unconfigured by Default**.
   - Base Adapter: `SmsProvider` / `GenericSmsAdapter`.
   - Production connectors: Twilio, Gupshup, Fast2SMS.
   - Reports unconfigured state honestly when credentials are not supplied.

4. **PUSH**:
   - Status: **Adapter Interface Implemented / Unconfigured by Default**.
   - Base Adapter: `PushProvider` / `GenericPushAdapter`.
   - Production connectors: Firebase Cloud Messaging (FCM), Apple APNs.

## Provider Health Monitoring

Institutional administrators can inspect provider connectivity and health status via `GET /api/v1/admin/notification-providers/health`:

- `HEALTHY`: Provider connector configured, credentials valid, latency acceptable.
- `DEGRADED`: Transient failures or elevated latencies detected.
- `UNHEALTHY`: Continuous authentication or upstream gateway errors.
- `UNCONFIGURED`: No connector configuration provided for the channel.

## Webhook Signatures & Status Updates

External providers report asynchronous delivery, bounce, and complaint events via authenticated webhooks:

- **Signature Verification**: Validates HMAC-SHA256 signatures (`verify_webhook_signature`) using tenant-specific provider secrets. Rejects unsigned or forged requests with HTTP 401.
- **Replay Protection**: Timestamps are checked with a maximum 300-second drift tolerance.
- **Idempotent Correlation**: Updates delivery records via `provider_message_id`.
- **Automatic Bounce Handling**: Automatically adds bounced email or invalid phone numbers to `notification_suppressions` to prevent future wasted dispatches.
