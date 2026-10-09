# CampusOS Authentication Architecture

## 1. Authentication Mechanisms

CampusOS supports multiple authentication mechanisms:
1. **Local Institutional Credentials**: Institutional email and Argon2id-hashed passwords.
2. **Enterprise Single Sign-On (SSO)**: Federated identity authentication via OIDC or OAuth 2.0.
3. **Multi-Factor Authentication (MFA)**: Time-based One-Time Password (TOTP) under RFC 6238 with single-use recovery codes.
4. **Developer Application API Keys**: Cryptographic salted hash keys for external integrations (Step 21).

---

## 2. Local Password Security & Hashing

- **Algorithm**: `Argon2id` (memory-hard, resistant to GPU/ASIC brute-force attacks) via `passlib.handlers.argon2`.
- **Constant-Time Verification**: Constant-time dummy verification is executed on unknown users to prevent user enumeration via timing side-channels.
- **Tenant Password Complexity**:
  - Minimum length (default 8, configurable up to 128 characters).
  - Configurable flags for uppercase, lowercase, digits, and special characters.
  - Validation occurs before password hash calculation.

---

## 3. Account Lockout & Brute-Force Defense

Configurable per-tenant via `identity_tenant_policies`:
- `lockout_threshold`: Maximum failed login attempts before locking (default: 5).
- `lockout_duration_minutes`: Duration of temporary lock (default: 15 minutes).
- Account locking records an `ACCOUNT_LOCKED` audit event with IP and user agent.
- Successful authentication immediately clears the failure counter and resets `locked_until`.

---

## 4. Secure Password Reset Flow

Password resets follow a secure, non-disclosing protocol:
1. **Request**: `POST /api/v1/auth/forgot-password`
   - Generic response: `If the email exists, a password reset link has been dispatched.`
   - Never reveals whether an account exists.
2. **Token Generation**: Cryptographically secure URL-safe random token (32 bytes).
   - Plaintext token sent only to user email.
   - SHA-256 hash stored in `people_password_reset_tokens`.
   - Single-use, 1-hour expiration.
3. **Reset Execution**: `POST /api/v1/auth/reset-password`
   - Validates token hash and unexpired state.
   - Updates `password_hash` with Argon2id.
   - **Immediately invalidates all active sessions** across all devices.
   - Emits `PASSWORD_CHANGED` forensic audit record.
