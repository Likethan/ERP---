# CampusOS API Platform Architecture & Developer Subsystem

## Overview

The **CampusOS API Platform** transforms the multi-tenant Campus Operating System into an extensible, secure platform. It allows institutional administrators, mobile clients, external ERPs, partner systems, and trusted developers to safely consume approved institutional capabilities without bypassing core governance, authorization, or multi-tenant boundaries.

The platform distinguishes between **internal administrative APIs** and **externally consumable APIs**, ensuring that internal endpoints are never exposed by default (`INTERNAL_ONLY`).

---

## 1. High-Level Gateway Architecture

External calls enter through the CampusOS API Platform Gateway, passing through a multi-tier pipeline before reaching domain business services:

```text
       API Consumer / External Application
                        │
                        ▼ (X-API-Key / Bearer Token)
   ┌────────────────────────────────────────────────┐
   │ 1. Credential Authentication & HMAC Validation │
   └────────────────────┬───────────────────────────┘
                        │
   ┌────────────────────▼───────────────────────────┐
   │ 2. Application Lifecycle & IP Firewall Check   │
   │    (ACTIVE / APPROVED status, CIDR allowlist)  │
   └────────────────────┬───────────────────────────┘
                        │
   ┌────────────────────▼───────────────────────────┐
   │ 3. Tenant Boundary & Lifecycle Resolution      │
   │    (Enforce Tenant Isolation, Active Status)   │
   └────────────────────┬───────────────────────────┘
                        │
   ┌────────────────────▼───────────────────────────┐
   │ 4. Capability Scope Validation                 │
   │    (Atomic Scope Resolution via ScopeRegistry) │
   └────────────────────┬───────────────────────────┘
                        │
   ┌────────────────────▼───────────────────────────┐
   │ 5. Application Owner PBAC / RBAC Verification  │
   │    (Scope can never exceed owner privileges)   │
   └────────────────────┬───────────────────────────┘
                        │
   ┌────────────────────▼───────────────────────────┐
   │ 6. Velocity Rate Limiting (Sliding Window)     │
   │    (Tier-based per second/min/hour limits)     │
   └────────────────────┬───────────────────────────┘
                        │
   ┌────────────────────▼───────────────────────────┐
   │ 7. Aggregate Quota Tracking (Daily / Monthly)  │
   │    (Available, Warning, Exceeded, Suspended)   │
   └────────────────────┬───────────────────────────┘
                        │
   ┌────────────────────▼───────────────────────────┐
   │ 8. Domain API Service Execution                │
   │    (Governance Masking & Idempotency Engine)   │
   └────────────────────┬───────────────────────────┘
                        │
   ┌────────────────────▼───────────────────────────┐
   │ 9. Privacy-Aware Telemetry & Usage Metering    │
   │    (Anonymized IPs, No Secrets/PII in Logs)    │
   └────────────────────────────────────────────────┘
```

---

## 2. Platform Directory Structure

```text
apps/api/app/platform_api/
├── auth.py              # Cryptographic key generation, HMAC hashing, rotation grace validation
├── catalog.py           # Catalog definitions, operation metadata, changelog management
├── dependencies.py      # Dependency injection pipeline (require_api_consumer)
├── idempotency.py       # Distributed idempotency engine for mutation endpoints
├── jobs.py              # Scheduled background workers (quota resets, metric rollups, pruning)
├── models.py            # SQLAlchemy models for applications, credentials, scopes, telemetry
├── quotas.py            # Aggregate quota consumption and state machine
├── rate_limits.py       # Sliding-window rate limiting engine with burst controls
├── schemas.py           # Strict Pydantic v2 validation contracts for public and admin schemas
├── scopes.py            # Canonical capability scope registry and ScopeResolver
├── service.py           # Application management service and approval workflows
├── usage.py             # Privacy-preserving usage recording and telemetry analytics
└── routers/
    ├── analytics.py     # Administrative usage analytics and percentile latencies
    ├── applications.py  # Application registration and lifecycle management
    ├── catalog.py       # Public API product catalog and changelog endpoints
    ├── credentials.py   # Secure API key generation, rotation, and revocation
    ├── health.py        # Tiered readiness, authentication, and database health checks
    ├── scopes.py        # Scope registry discovery and grant administration
    └── domain/          # Public Consumable Domain APIs (/api/v1/platform/v1/...)
        ├── academics.py    # Courses, curricula, programs
        ├── attendance.py   # Daily attendance records and summaries
        ├── events.py       # Campus events and student registrations
        ├── examinations.py # Assessments, schedules, results
        ├── finance.py      # Invoices, fee balances, idempotent payments
        └── students.py     # Student records with field-level governance masking
```

---

## 3. Core Capabilities

1. **Self-Contained Application Lifecycle**: Applications progress from `DRAFT` to `PENDING_APPROVAL`, `APPROVED`, `ACTIVE`, `SUSPENDED`, `REVOKED`, or `ARCHIVED`.
2. **Zero Plaintext Secrets**: Keys and secrets are shown only once upon generation. Only cryptographically salted HMAC fingerprints are persisted.
3. **Overlapping Credential Rotation**: Zero-downtime rotation with dual-active grace periods (default 24h to 72h).
4. **Defense-in-Depth Authorization**: Scopes map strictly to capabilities; an API key cannot exercise any action that the underlying human or system owner cannot perform via PBAC.
5. **Multi-Period Quota Governance**: Daily and monthly aggregate quotas prevent resource exhaustion and data scraping.
6. **Strict Idempotency Guarantees**: Mutation operations (such as payment processing) require an `Idempotency-Key` header with payload-hash verification and deterministic replay.
7. **Transparent Deprecation Standards**: Adheres to RFC 8594 `Deprecation`, `Sunset`, and `Link` headers for graceful API lifecycle evolutions.
