# CampusOS Session Security & Token Rotation

## 1. First-Class IdentitySession Model

CampusOS tracks active user sessions in `identity_user_sessions`:

| Field | Purpose |
| :--- | :--- |
| `session_identifier` | Unique, non-sequential session ID (e.g., `sess_4b7f...`). |
| `refresh_token_family_id` | UUID grouping rotated tokens issued across a single login chain. |
| `refresh_token_hash` | SHA-256 digest of the currently active refresh token. |
| `status` | `ACTIVE`, `EXPIRED`, `REVOKED`, `LOCKED`. |
| `ip_address_masked` | Anonymized IP (e.g. `192.168.1.xxx` or `2001:db8::xxxx`) for UI display. |
| `ip_address_hash` | SHA-256 digest of raw IP for forensic matching without storing plain PII. |
| `device_summary` | Non-invasive user-agent summary (e.g. `Chrome on Windows`, `Safari on iOS`). |
| `is_mfa_verified` | True if multi-factor authentication was verified for this session. |
| `last_activity_at` | Updated on every token rotation or session access. |
| `expires_at` | Hard session expiration timestamp. |

---

## 2. Refresh Token Family Rotation & Reuse Detection

CampusOS uses **Refresh Token Rotation with Automatic Reuse Detection** to protect against token theft and replay attacks:

```
Step 1: Normal Rotation
User presents Refresh Token A
       ↓
Server validates hash(A) == session.refresh_token_hash
       ↓
Server invalidates Token A, issues Token B
       ↓
session.refresh_token_hash updated to hash(B)

Step 2: Replay Attack
Attacker intercepts and submits expired Token A
       ↓
Server detects hash(A) mismatch against active session hash(B)
       ↓
SUSPECTED TOKEN THEFT DETECTED
       ↓
Server immediately revokes ALL sessions in refresh_token_family_id
       ↓
Emits TOKEN_FAMILY_REVOCATION security audit event
       ↓
Raises AuthenticationException (all sessions terminated)
```

---

## 3. Session Governance & Timeouts

Per-tenant settings in `identity_tenant_policies`:
- **Session Duration**: Absolute maximum lifespan (default: 24 hours / 1440 minutes).
- **Idle Timeout**: Maximum permitted inactivity between requests (default: 2 hours / 120 minutes). If `last_activity_at + idle_timeout < now`, session is marked `EXPIRED`.
- **Maximum Concurrent Sessions**: Default 5 active sessions per user. If exceeded, the oldest active session is automatically revoked with reason `MAX_CONCURRENT_SESSIONS_EXCEEDED`.

---

## 4. Session Revocation APIs

- `GET /api/v1/identity/sessions`: Lists active sessions with device summary, masked IP, creation time, and `is_current` flag.
- `POST /api/v1/identity/sessions/{id}/revoke`: Invalidate specific session. Standard users may revoke their own sessions; administrators may revoke any session in their tenant.
- `POST /api/v1/identity/sessions/revoke-all`: Terminates all active sessions for the user across all devices.
- Password change and controlled deprovisioning automatically revoke all active user sessions.
