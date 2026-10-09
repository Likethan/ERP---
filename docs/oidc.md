# CampusOS OpenID Connect (OIDC) Integration

## 1. Provider Discovery & Outbound SSRF Protection

OIDC provider discovery fetches `/.well-known/openid-configuration` to dynamically configure endpoints:
- `authorization_endpoint`
- `token_endpoint`
- `userinfo_endpoint`
- `jwks_uri`

All discovery calls are routed through `SafeHttpClient.request()`:
- **SSRF Defense**: Loopback addresses (`127.0.0.1`, `localhost`), link-local IPs (`169.254.169.254`), private RFC 1918 subnets, and cloud metadata hosts (`metadata.google.internal`) are blocked.
- **TLS Requirement**: In production, only HTTPS endpoints are permitted.
- **Payload Boundaries**: Outbound responses are capped at 5 MB to prevent memory exhaustion attacks.

---

## 2. JWKS Management & Key Caching

JSON Web Key Sets (JWKS) are retrieved from `jwks_uri`:
- **In-Memory Cache**: Cached with a 1-hour TTL (`JWKS_CACHE_TTL_SECONDS = 3600.0`).
- **Key Rotation**: If an unknown `kid` is encountered, cache invalidation forces an updated fetch.
- Outbound fetch executes with strict 8-second timeouts.

---

## 3. ID Token Cryptographic Verification Rules

When evaluating federated ID tokens, `OidcService.validate_id_token_claims()` enforces strict cryptographic checks:

```
Unverified Header
       ↓
Check Algorithm: alg == 'none' ?  ➔ REJECT (AuthenticationException)
       ↓
Check Algorithm: unsupported alg ? ➔ REJECT
       ↓
Validate Claims
       ↓
Issuer Check: iss == provider.issuer_url ? ➔ REJECT on mismatch
       ↓
Audience Check: aud contains provider.client_id ? ➔ REJECT on mismatch
       ↓
Expiry Check: exp > current_utc_timestamp ? ➔ REJECT on expiration
       ↓
Nonce Check: nonce == session_nonce ? ➔ REJECT on replay mismatch
```

### Protection Against `alg=none` Attacks
CampusOS explicitly forbids unsigned tokens:
```python
alg = unverified_headers.get("alg")
if not alg or alg.lower() == "none":
    raise AuthenticationException("ID token specifies insecure 'none' algorithm. Rejected.")
```

---

## 4. Claim & Role Mapping

### Attribute Mapping
Institutional IdP claims are mapped into CampusOS user properties:
```json
{
  "subject": "sub",
  "email": "email",
  "display_name": "name",
  "first_name": "given_name",
  "last_name": "family_name"
}
```

### Deny-by-Default Role Mapping
External groups (`groups`, `roles`, `realm_access.roles`) are mapped via `provider.role_mapping`:
- Any claim group not explicitly present in `role_mapping` is dropped.
- **Privilege Escalation Defense**: External claims mapping to `SUPER_ADMIN` are stripped automatically to prevent external identity providers from acquiring system root access.
