# CampusOS API Versioning & Evolution Strategy

## Overview

To protect institutional integrations and mobile applications from breaking changes, CampusOS follows an explicit, contract-driven versioning and deprecation model.

---

## 1. URI Path Versioning

All externally consumable APIs embed the major platform API version in the URL path:

```text
/api/v1/platform/v1/students
```

- **Prefix**: `/api/v1` denotes the CampusOS gateway generation.
- **Platform Subsystem**: `/platform/v1` defines the consumable platform API specification.

A breaking change in the public contract results in a new major version route:

```text
/api/v1/platform/v2/students
```

Minor backwards-compatible additions (such as new optional response fields) are introduced in-place within the current version without incrementing the URL major version.

---

## 2. API Operation Lifecycle

Each API operation registered in the **API Catalog** transitions through six lifecycle phases:

```text
  ┌───────┐      ┌─────────┐      ┌────────┐
  │ DRAFT │ ───► │ PREVIEW │ ───► │ ACTIVE │
  └───────┘      └─────────┘      └───┬────┘
                                      │
                                      ▼ (Deprecation announced)
                               ┌────────────┐
                               │ DEPRECATED │
                               └──────┬─────┘
                                      │
                                      ▼ (Sunset date reached)
                                 ┌────────┐
                                 │ SUNSET │
                                 └───┬────┘
                                     │
                                     ▼ (Endpoint disabled)
                                ┌─────────┐
                                │ RETIRED │
                                └─────────┘
```

1. **DRAFT**: Internal development and initial contract design.
2. **PREVIEW**: Sandboxed testing with selected pilot integration partners.
3. **ACTIVE**: Generally available (GA), fully supported, production grade.
4. **DEPRECATED**: Replacement version available; planned for eventual removal.
5. **SUNSET**: Hard cutoff date reached; non-critical traffic restricted.
6. **RETIRED**: Endpoint disabled and returns `410 Gone`.

---

## 3. RFC 8594 Standard Deprecation Headers

When a client calls an endpoint in `DEPRECATED` status, the gateway automatically injects standard HTTP deprecation headers:

```http
HTTP/1.1 200 OK
Content-Type: application/json
Deprecation: true
Sunset: Wed, 01 Jul 2026 00:00:00 GMT
Link: </api/v1/platform/v2/students>; rel="successor-version"
```

- **`Deprecation: true`**: Informs automated consumers that the endpoint is deprecated.
- **`Sunset`**: Specifies the exact UTC timestamp after which the endpoint will be turned off.
- **`Link: <successor>; rel="successor-version"`**: Points consumers directly to the successor endpoint.

---

## 4. API Changelogs

The platform exposes an official machine-readable changelog at `/api/v1/platform/changelog`. Each release records:

- Release date
- Non-breaking changes
- Breaking changes (if applicable to a new version)
- Deprecated operations
- Step-by-step migration notes
