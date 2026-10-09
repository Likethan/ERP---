# CampusOS Multi-Factor Authentication (MFA)

## 1. MFA Architecture Overview

CampusOS implements a multi-factor authentication layer designed for high-assurance institutional environments.

```
User Authentication (Password / SSO)
       ↓
Check Tenant MFA Policy (`identity_tenant_policies`)
       ↓
MFA Required or Enrolled?
   ├── No ➔ Establish Session
   └── Yes ➔ Issue Ephemeral Challenge Token (`identity_mfa_challenges`)
             ↓
Prompt User for 6-digit TOTP or Emergency Recovery Code
             ↓
Validate Code
   ├── TOTP Verified (HMAC-SHA1 RFC 6238)
   └── Recovery Code Verified (Single-Use Hashed Match)
             ↓
Mark Session `is_mfa_verified = True`
             ↓
Grant Access
```

---

## 2. TOTP (Time-based One-Time Password)

- **Standard**: RFC 6238 (HMAC-SHA1, 30-second time-step, 6 digits).
- **Drift Tolerance**: Evaluates current time step `t`, plus `t - 1` and `t + 1` (tolerance window of ±30 seconds) to account for client device clock skew.
- **Secret Encryption**: Raw Base32 secrets are never stored in plaintext. They are encrypted using authenticated Fernet symmetric encryption (`SecretManager.encrypt_payload`) keyed to the institutional secret vault.
- **QR Code URI**: Generates standard `otpauth://totp/CampusOS:<email>?secret=<b32>&issuer=CampusOS` URIs compatible with Google Authenticator, Microsoft Authenticator, and 1Password.

---

## 3. Single-Use Emergency Recovery Codes

Upon TOTP enrollment, 8 alphanumeric 10-character recovery codes are generated:
- Displayed once to the user during enrollment.
- Plaintext codes are **never stored** in the database.
- SHA-256 hashes are persisted in `identity_mfa_recovery_codes`.
- When a recovery code is verified, it is marked `is_used = True` with a timestamp and can **never be reused**.

---

## 4. MFA Policy Enforcement Levels

Configured per tenant in `TenantIdentityPolicy.mfa_policy`:

| Policy Level | Behavior |
| :--- | :--- |
| `OPTIONAL` | Users may voluntarily opt into MFA. |
| `REQUIRED` | Mandatory for all users in the institution; users without MFA must enroll upon next login. |
| `REQUIRED_FOR_ADMIN` | Mandatory for administrative roles (`SUPER_ADMIN`, `INSTITUTION_ADMIN`, `ADMIN`). |
| `REQUIRED_FOR_HIGH_RISK_ACTION` | Prompts step-up challenge before high-risk mutations (credential rotation, finance administration, deprovisioning). |

---

## 5. Step-Up Authentication Flow

High-risk actions require verification of an active MFA challenge within the past 5 minutes:
1. Client calls `POST /api/v1/identity/mfa/challenge/verify` with `challenge_token` and `code`.
2. Server verifies the code, marks challenge `is_verified = True`.
3. Protected administrative endpoint verifies unexpired challenge state before executing mutation.
