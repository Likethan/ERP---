# CampusOS Environment Variable & Configuration Strategy

Product Identity: **CampusOS — The operating system for modern colleges.**  
Tagline: **One Campus. One System. One Source of Truth.**

---

## 1. Environment Classification

CampusOS recognizes three distinct operating environments:

```text
development  --> Local developer workstations, SQLite / local Docker, hot reload, verbose debug.
staging      --> Staging environment mimicking production, isolated test databases, full sanitization.
production   --> Hardened multi-tenant live campus deployments. Strict fail-fast security constraints.
```

---

## 2. Configuration Validation Rules (Fail-Fast)

When `ENVIRONMENT=production`, the application server will **refuse to boot** if any of the following conditions are met:
1. `SECRET_KEY` is not set or matches any insecure default template string.
2. `SECRET_KEY` length is less than 32 characters.
3. `DEBUG` is set to `true`.
4. `CORS_ORIGINS` contains wildcard `'*'` or localhost addresses (`localhost`, `127.0.0.1`).
5. `COOKIE_SECURE` is set to `false`.

---

## 3. Backend Environment Variables Reference

| Variable Name | Type | Example (Production) | Description |
| :--- | :--- | :--- | :--- |
| `ENVIRONMENT` | string | `production` | Active deployment tier (`development`, `staging`, `production`). |
| `DEBUG` | boolean | `false` | Enable/disable debug traces. Must be `false` in production. |
| `PROJECT_NAME` | string | `CampusOS API` | API service identifier displayed in probes. |
| `VERSION` | string | `0.1.0` | Application release version. |
| `SECRET_KEY` | string | *Secret (64 hex chars)* | Cryptographic HMAC secret for signing tokens. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | integer | `15` | Lifetime of user access tokens. |
| `REFRESH_TOKEN_EXPIRE_DAYS` | integer | `7` | Lifetime of user refresh tokens. |
| `DATABASE_URL` | string | `postgresql+asyncpg://...` | Connection URI for PostgreSQL database. |
| `DB_POOL_SIZE` | integer | `25` | Base connection pool size. |
| `DB_MAX_OVERFLOW` | integer | `15` | Maximum overflow connection count. |
| `DB_POOL_TIMEOUT` | integer | `30` | Connection checkout timeout in seconds. |
| `DB_POOL_RECYCLE` | integer | `1800` | Connection recycle period in seconds. |
| `REDIS_URL` | string | `rediss://:auth@redis:6379/0` | Connection URI for Redis (supports TLS `rediss://`). |
| `CORS_ORIGINS` | JSON list | `["https://app.campus.edu"]` | Whitelisted cross-origin domains. |
| `STORAGE_PROVIDER` | string | `s3` | Object storage engine (`minio`, `s3`, `mock`). |
| `STORAGE_REGION` | string | `us-east-1` | Cloud storage region. |
| `STORAGE_ENDPOINT` | string | `s3.us-east-1.amazonaws.com` | Storage host endpoint. |
| `STORAGE_BUCKET_NAME` | string | `campusos-documents-prod` | Dedicated document storage bucket. |
| `STORAGE_ACCESS_KEY` | string | *Secret* | IAM user access key. |
| `STORAGE_SECRET_KEY` | string | *Secret* | IAM user secret access key. |
| `STORAGE_USE_SSL` | boolean | `true` | Enforce HTTPS for object storage operations. |
| `AI_PROVIDER` | string | `mock` / `openai` | Intelligence LLM provider. |
| `RATE_LIMIT_ENABLED` | boolean | `true` | Enforce sliding-window rate limiting. |

---

## 4. Frontend Environment Variables (`apps/web`)

Only variables prefixed with `NEXT_PUBLIC_` are baked into client-side JavaScript bundles:

| Variable Name | Scope | Production Example | Description |
| :--- | :--- | :--- | :--- |
| `NEXT_PUBLIC_API_URL` | Client & Server | `https://api.campus.edu` | Base URL used by browser code to reach the backend API. |
| `NODE_ENV` | Server | `production` | Node.js runtime environment. |
| `PORT` | Server | `3000` | Port for Next.js standalone HTTP listener. |
| `NEXT_TELEMETRY_DISABLED` | Server | `1` | Opt out of Next.js telemetry. |

### Strict Prohibition
Never prefix the following with `NEXT_PUBLIC_`:
- `DATABASE_URL`
- `REDIS_URL`
- `SECRET_KEY`
- `STORAGE_SECRET_KEY`
- Cloud provider access credentials
