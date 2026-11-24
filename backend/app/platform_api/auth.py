"""Cryptographic Credential Management & API Key Security (Step 21).

Enforces:
- Cryptographically secure API keys with environment-specific prefixes (cos_live_, cos_stag_, cos_dev_)
- One-way salted HMAC hashing (raw secrets are never stored in DB or returned after creation)
- Timing-attack resistant hash verification
- Safe credential rotation with overlapping grace periods
- Immediate revocation enforcement and expiration checks
"""

import hashlib
import hmac
import secrets
from datetime import UTC, datetime
from typing import Final

from app.core.config import settings
from app.platform_api.models import (
    ApplicationCredential,
    ApplicationEnvironment,
    CredentialStatus,
)

_PREFIX_MAP: Final[dict[str, str]] = {
    ApplicationEnvironment.PRODUCTION.value: "cos_live_",
    ApplicationEnvironment.STAGING.value: "cos_stag_",
    ApplicationEnvironment.DEVELOPMENT.value: "cos_dev_",
}


def compute_secret_hash(raw_secret: str) -> str:
    """Compute HMAC-SHA256 digest of secret using server secret key."""
    key_bytes = settings.SECRET_KEY.encode("utf-8")
    secret_bytes = raw_secret.encode("utf-8")
    return hmac.new(key_bytes, secret_bytes, hashlib.sha256).hexdigest()


def verify_credential_secret(raw_secret: str, stored_hash: str) -> bool:
    """Constant-time verification of raw secret against stored HMAC hash."""
    expected_hash = compute_secret_hash(raw_secret)
    return hmac.compare_digest(expected_hash, stored_hash)


def generate_api_key_credentials(
    environment: str = ApplicationEnvironment.DEVELOPMENT.value,
) -> tuple[str, str, str, str]:
    """Generate high-entropy client identifier and secret key.

    Returns:
        (client_id, raw_secret, key_prefix, secret_hash)
    """
    client_id = f"cos_app_{secrets.token_hex(8)}"
    prefix = _PREFIX_MAP.get(environment.upper(), "cos_dev_")
    random_part = secrets.token_urlsafe(32)
    raw_secret = f"{prefix}{random_part}"
    key_prefix = raw_secret[:12]
    secret_hash = compute_secret_hash(raw_secret)

    return client_id, raw_secret, key_prefix, secret_hash


def is_credential_valid_for_auth(cred: ApplicationCredential) -> tuple[bool, str]:
    """Inspect credential lifecycle status and validity timestamps.

    Returns:
        (is_valid: bool, reason: str)
    """
    now = datetime.now(UTC)

    # 1. Revoked status
    if cred.status == CredentialStatus.REVOKED.value:
        return False, "Credential has been revoked."

    # 2. Expired status
    if cred.status == CredentialStatus.EXPIRED.value:
        return False, "Credential has expired."

    # 3. Explicit expiration timestamp
    if cred.expires_at:
        # Normalize timezone if needed
        exp = cred.expires_at if cred.expires_at.tzinfo else cred.expires_at.replace(tzinfo=UTC)
        if now > exp:
            return False, "Credential expiration timestamp has passed."

    # 4. Active status
    if cred.status == CredentialStatus.ACTIVE.value:
        return True, "ACTIVE"

    # 5. Rotating status (must be within grace period)
    if cred.status == CredentialStatus.ROTATING.value:
        if not cred.grace_period_expires_at:
            return False, "Rotating credential lacks grace period window."
        grace_exp = (
            cred.grace_period_expires_at
            if cred.grace_period_expires_at.tzinfo
            else cred.grace_period_expires_at.replace(tzinfo=UTC)
        )
        if now <= grace_exp:
            return True, "ROTATING_GRACE_PERIOD"
        return False, "Rotation grace period window has elapsed."

    return False, f"Unknown credential status '{cred.status}'."
