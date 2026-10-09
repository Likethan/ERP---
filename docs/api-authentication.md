# CampusOS API Platform Authentication & Credential Architecture

## Overview

The CampusOS API platform employs a zero-trust, environment-isolated credential model designed for machine-to-machine (M2M) and third-party integration workflows.

---

## 1. Credential Structure & Generation

CampusOS credentials follow a cryptographically secure, high-entropy structure:

```text
{prefix}_{env}_{public_id}_{random_secret}
```

- **Prefix**: `cos` (CampusOS)
- **Environment**: `dev`, `stg`, or `live`
- **Public ID**: 12 hexadecimal characters identifying the credential entity
- **Secret**: 32 cryptographically secure base64url random bytes (256-bit entropy)

### Example API Key
```text
cos_live_4f1c9d2b8e3a_V1x9aZ_0pK-qR7uWsTxY3nM9bLvCdEfG
```

---

## 2. Zero-Plaintext Secret Storage

1. **One-Time Disclosure**: When an API key or client secret is generated, the full raw token is returned **exactly once** in the creation response.
2. **Salted HMAC Fingerprinting**: CampusOS hashes the secret using HMAC-SHA256 with a cluster-wide secret salt.
3. **Database Records**: Only the key prefix (`cos_live_4f1c9d2b8e3a`) and the cryptographic `secret_hash` are persisted.
4. **Read Masking**: All read endpoints (`GET /platform/applications/{id}/credentials`) omit plaintext secrets and provide only metadata:
   - `client_id`
   - `key_prefix`
   - `environment`
   - `status`
   - `created_at`
   - `last_used_at`
   - `expires_at`

---

## 3. Zero-Downtime Credential Rotation

Rotating production credentials in active consumer pipelines must not cause service disruption. CampusOS implements an automated **Dual-Active Grace Window**:

```text
1. Administrator calls POST /platform/applications/{id}/credentials/{cred_id}/rotate
                             │
                             ▼
2. Platform generates NEW credential (status: ACTIVE)
   - Discloses raw secret to administrator once
                             │
                             ▼
3. Platform transitions OLD credential to ROTATING
   - Sets grace_period_expires_at = now() + overlap_hours (e.g. 24h - 72h)
                             │
                             ▼
4. During Grace Window:
   - Requests with OLD key are accepted
   - Requests with NEW key are accepted
                             │
                             ▼
5. Consumer migrates to NEW credential in their pipeline
                             │
                             ▼
6. Background job (or manual call) marks OLD credential as REVOKED
```

Any attempt to authenticate with a revoked or expired credential immediately yields `401 Unauthorized`.

---

## 4. IP Firewalling & Network Allowlisting

Applications can configure CIDR or IP allowlists in `allowed_ips`:

```json
{
  "allowed_ips": ["198.51.100.14", "203.0.113.0/24"]
}
```

If configured, incoming requests with source IPs not matching the allowlist receive `403 IP_FORBIDDEN` before reaching any business logic or quota counters.

---

## 5. Machine-to-Machine OAuth2 Readiness

CampusOS provides native data models for future OAuth2 Authorization Server flows:

- `client_id` and hashed `client_secret`
- Registered `redirect_uris`
- Authorization code grant and client credentials grant support
- Scoped token exchanges
