# CampusOS API Platform Application Lifecycle & Governance

## Overview

Applications consuming the CampusOS API platform progress through a controlled administrative lifecycle to ensure compliance with institutional data governance policies.

---

## 1. Application Lifecycle States

```text
       ┌───────────┐
       │   DRAFT   │  (Initial registration by developer or admin)
       └─────┬─────┘
             │
             ▼ (Submit for review)
   ┌───────────────────┐
   │ PENDING_APPROVAL  │  (Awaiting institutional review)
   └─────┬───────┬─────┘
         │       │
(Approve)│       │(Reject)
         ▼       ▼
   ┌──────────┐ ┌──────────┐
   │ APPROVED │ │ REJECTED │
   └─────┬────┘ └──────────┘
         │
         ▼ (Generate credentials & activate)
   ┌──────────┐
   │  ACTIVE  │  (Can invoke approved APIs)
   └─────┬────┘
         │
    ┌────┴───────────────┐
    ▼                    ▼
┌───────────┐      ┌───────────┐
│ SUSPENDED │      │  REVOKED  │
└───────────┘      └───────────┘
```

### State Definitions
- **`DRAFT`**: Developer is configuring application metadata and requested capability scopes. The application cannot make API calls.
- **`PENDING_APPROVAL`**: Submitted for institutional review. High-risk scopes are flagged for compliance approval.
- **`APPROVED`**: Granted approval by an Institutional Administrator or Platform Security Officer.
- **`ACTIVE`**: Credentials have been provisioned and the application is actively consuming platform APIs.
- **`SUSPENDED`**: Temporarily frozen due to security anomalies, quota exhaustion, or administrative review. All API requests receive `403 APPLICATION_SUSPENDED`.
- **`REVOKED`**: Permanently terminated. Credentials are revoked and access is blocked (`403 APPLICATION_REVOKED`).
- **`ARCHIVED`**: Soft-deleted historical record preserved for audit and compliance.

---

## 2. Institutional Ownership & Responsibilities

1. **Explicit Owner**: Every `DeveloperApplication` must specify an `owner_id` pointing to an active user account in the institution. Anonymous applications are disallowed.
2. **Environment Isolation**: Applications are tagged as `DEVELOPMENT`, `STAGING`, or `PRODUCTION`. Production credentials cannot authenticate against sandbox environments and vice-versa.
3. **Audit Trails**: Every state change (approval, rejection, suspension, credential generation) emits an audit event linking:
   - `tenant_id`
   - `application_id`
   - `action`
   - `actor_id`
   - `reason`
