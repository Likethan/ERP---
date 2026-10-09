# CampusOS Identity Provider Operations & Administration

## 1. Identity Provider Lifecycle & States

Identity providers transition through a strict state machine:

```
[DRAFT] ➔ (Configure & Validate) ➔ [ACTIVE] ➔ (Pause / Admin Intervention) ➔ [PAUSED]
   │                                  │                                          │
   └── (Configuration Error) ➔ [ERROR] └── (Decommission) ➔ [DISABLED] ◄─────────┘
```

- **DRAFT**: Initial creation. Client secrets and endpoints configured.
- **ACTIVE**: Validated and enabled for institutional login.
- **PAUSED**: Temporarily suspended during maintenance without deleting configuration.
- **DISABLED**: Decommissioned. No authentication requests routed to this provider.

---

## 2. Health Monitoring & Connectivity Testing

Administrators can test provider reachability on-demand via:
`POST /api/v1/identity/providers/{id}/test`

The system evaluates:
1. Issuer OpenID configuration discovery endpoint (`/.well-known/openid-configuration`).
2. JWKS public key endpoint (`jwks_uri`).
3. Authorization endpoint reachability.

Each check records latency, status codes, and updates `provider.health_status` (`HEALTHY`, `DEGRADED`, `UNAVAILABLE`).

---

## 3. Background Maintenance Tasks

Executed periodically via Celery / APScheduler / Cron:

| Job Name | Frequency | Description |
| :--- | :--- | :--- |
| `cleanup_expired_sessions` | Every 15 mins | Marks sessions with `expires_at <= now` as `EXPIRED`. |
| `cleanup_expired_challenges` | Every 10 mins | Purges expired MFA challenges and uncompleted account link requests. |
| `run_identity_provider_health_checks` | Every hour | Pings active external OIDC/OAuth providers to detect degradation. |

---

## 4. Observability & Telemetry (Step 15 Integration)

Metrics emitted for Grafana/Prometheus:
- `identity_login_attempts_total{method="local|oidc|oauth2", status="success|failure"}`
- `identity_token_replay_attacks_total{tenant_id="..."}`
- `identity_active_sessions_gauge{tenant_id="..."}`
- `identity_mfa_challenges_total{factor="totp|recovery", result="verified|failed"}`
- `identity_provider_health_status{provider_id="...", status="healthy|degraded|unavailable"}`

**Non-Disclosure Guarantee**: Credentials, tokens, client secrets, TOTP keys, and authorization headers are **never** logged or emitted into metrics.

---

## 5. Troubleshooting Common Issues

### Issue 1: "ID token issuer mismatch"
- **Cause**: The `iss` claim in the ID token does not match `provider.issuer_url`.
- **Resolution**: Ensure trailing slashes match exactly between CampusOS provider settings and the IdP's advertised issuer.

### Issue 2: "ID token specifies insecure 'none' algorithm"
- **Cause**: A misconfigured or hostile IdP is issuing unsigned tokens.
- **Resolution**: Configure the IdP to sign with `RS256` or `ES256`. CampusOS strictly rejects `alg=none`.

### Issue 3: "Token reuse detected. All sessions in this family have been revoked."
- **Cause**: An outdated or already-rotated refresh token was submitted, indicating a potential token interception.
- **Resolution**: The user must log in again to establish a new session family.
