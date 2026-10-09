# CampusOS Enterprise Single Sign-On (SSO)

## 1. SSO Architecture Overview

CampusOS provides native support for tenant-configured identity providers, allowing educational institutions to federate student and faculty logins with existing identity services (Google Workspace for Education, Microsoft Entra ID / Office 365, Keycloak, Okta, and Shibboleth/InCommon SAML).

```
Client App
   ↓  1. GET /api/v1/identity/federation/providers/{id}/authorize
CampusOS Backend
   ↓  2. Return authorization_url + signed state
Client Redirects to External IdP
   ↓  3. User Authenticates at IdP
Client Redirected back with code
   ↓  4. POST /api/v1/identity/federation/callback
CampusOS Backend
   ↓  5. Outbound token exchange (SafeHttpClient with SSRF defense)
   ↓  6. Cryptographic token validation & claim mapping
   ↓  7. User resolution or JIT provisioning
   ↓  8. Establish IdentitySession & issue short-lived JWT access token
Client Logged In
```

---

## 2. Supported Protocols & Abstractions

| Protocol | Implementation Status | Description |
| :--- | :--- | :--- |
| **OIDC** | Fully Operational | OpenID Connect 1.0 discovery, token validation, JWKS caching, and claim mapping. |
| **OAuth 2.0** | Fully Operational | Standard authorization code flow with client credential authentication. |
| **SAML 2.0** | Enterprise Abstraction Ready | `SamlFederationProvider` and `SamlConfiguration` abstractions defining AuthnRequest generation, attribute mapping, and Single Logout (SLO) contracts ready for XML-DSig/SAML2 binding. |
| **LOCAL** | Fully Operational | Native CampusOS credentials with Argon2id and configurable password complexity. |

---

## 3. Account Linking vs. Account Takeover Prevention

Automatic account linking based solely on email matching (`external_email == existing_email`) is **strictly forbidden** unless the tenant policy explicitly configures verified institutional domain auto-linking.

For existing accounts:
1. User logs in with primary institutional credentials.
2. User initiates linking via `POST /api/v1/identity/identities/link/initiate`.
3. CampusOS issues a time-limited (15-minute) cryptographic link challenge token.
4. User confirms linking via `POST /api/v1/identity/identities/link/confirm` with current password verification.
5. This prevents malicious third-party IdPs from claiming ownership of pre-existing accounts.

---

## 4. Single Logout (SLO)

- **Local Logout**: `POST /api/v1/auth/logout` invalidates the active `IdentitySession` and clears HTTP cookies.
- **Global Logout**: `POST /api/v1/identity/sessions/revoke-all` revokes all active sessions across all devices.
- **Federated SLO Abstraction**: `SamlFederationProvider.handle_single_logout` prepares SLO payloads for institutional identity logout endpoints where configured.
