# CampusOS API Traffic Control: Rate Limits & Quotas

## Overview

To protect institutional infrastructure and ensure fair resource allocation, CampusOS enforces two distinct traffic governance layers:

1. **Rate Limiting**: Controls request **velocity** (requests per second/minute/hour).
2. **Quota Governance**: Controls **aggregate volume** over daily and monthly billing/operational cycles.

---

## 1. Rate Limit Tiers

Rate limits are evaluated using an **in-memory sliding window algorithm** with timestamped counters. Limits are keyed to the `Application ID` (not the API key), ensuring that rotating or generating new credentials cannot bypass velocity thresholds.

| Rate Limit Tier | Requests / Sec | Requests / Min | Requests / Hour | Burst Allowance | Intended Consumer |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **DEFAULT** | 10 | 300 | 10,000 | 20 | Standard external partners |
| **PARTNER** | 50 | 1,500 | 50,000 | 100 | Verified institutional integrations |
| **ENTERPRISE**| 200 | 6,000 | 200,000 | 400 | High-throughput institutional bridges |
| **INTERNAL** | 1,000 | 30,000 | 1,000,000 | 2,000 | CampusOS native mobile/web microservices |

### Rate Limit Response Headers
Every external API response returns rate limit metadata:

```http
HTTP/1.1 200 OK
X-RateLimit-Limit-Minute: 300
X-RateLimit-Remaining-Minute: 284
X-RateLimit-Reset-Seconds: 38
```

When an application exceeds its limit, the gateway responds with `429 Too Many Requests`:

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Application has exceeded its rate limit of 300 requests per minute.",
    "details": {
      "retry_after_seconds": 22
    }
  }
}
```

---

## 2. Multi-Period Aggregate Quotas

While rate limits mitigate bursts and denial-of-service attempts, aggregate quotas control monthly bandwidth and resource utilization.

| Quota Tier | Daily Request Cap | Monthly Request Cap | Max Exports / Month | Webhooks / Month |
| :--- | :--- | :--- | :--- | :--- |
| **DEFAULT** | 10,000 | 250,000 | 10 | 50,000 |
| **PARTNER** | 100,000 | 2,500,000 | 100 | 500,000 |
| **ENTERPRISE**| 1,000,000 | 25,000,000 | 1,000 | 5,000,000 |
| **INTERNAL** | 10,000,000 | 250,000,000 | Unlimited | Unlimited |

### Quota State Machine
Each application's quota transitions through four operational states:

```text
       ┌───────────┐
       │ AVAILABLE │  (Usage < 80% of limit)
       └─────┬─────┘
             │
             ▼ (Usage >= 80%)
       ┌───────────┐
       │  WARNING  │  (Notification dispatched, requests still accepted)
       └─────┬─────┘
             │
             ▼ (Usage >= 100%)
       ┌───────────┐
       │ EXCEEDED  │  (Requests rejected with 429 QUOTA_EXCEEDED)
       └─────┬─────┘
             │
             ▼ (Administrative lock)
       ┌───────────┐
       │ SUSPENDED │  (Traffic blocked until billing/admin review)
       └───────────┘
```

When usage reaches `WARNING` status (80%), an automated event is emitted, alerting the institutional administrator.

---

## 3. Scheduled Background Jobs

The platform schedules recurring background jobs for maintenance:

- **`api.usage.aggregate`**: Periodically rolls up raw request telemetry into hourly and daily summary records.
- **`api.quota.reset`**: Resets daily usage counters at midnight UTC and monthly counters on the 1st of each calendar month.
- **`api.credential.expiry`**: Marks expired grace-period credentials as `REVOKED`.
- **`api.usage.cleanup`**: Prunes detailed request logs older than the tenant retention window (default 90 days).
