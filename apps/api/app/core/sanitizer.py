"""Data sanitization and sensitive field redaction engine for CampusOS.

Ensures that passwords, tokens, API keys, and sensitive institutional records
are never leaked in structured logs, exceptions, audit records, or API responses.
"""

import re
from collections.abc import Mapping
from typing import Any

SENSITIVE_FIELD_NAMES: set[str] = {
    "password",
    "password_hash",
    "hashed_password",
    "old_password",
    "new_password",
    "confirm_password",
    "plain_password",
    "token",
    "access_token",
    "refresh_token",
    "secret",
    "secret_key",
    "api_key",
    "authorization",
    "cookie",
    "set-cookie",
    "credit_card",
    "card_number",
    "cvv",
    "cvc",
    "payment_reference",
    "private_key",
    "jwt",
    "bearer",
}

REDACTED_PLACEHOLDER = "[REDACTED]"

# Regular expressions for URL credential masking and token patterns
_DB_URL_REGEX = re.compile(r"(://[^:]+:)([^@]+)(@)")
_BEARER_REGEX = re.compile(r"(Bearer\s+)[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE)


def is_sensitive_key(key: str) -> bool:
    """Check if a dictionary key represents sensitive security or identity data."""
    normalized = key.lower().replace("-", "_").strip()
    return any(sens in normalized for sens in SENSITIVE_FIELD_NAMES)


def mask_sensitive_dict(data: Any, mask_value: str = REDACTED_PLACEHOLDER) -> Any:
    """Recursively redact sensitive key-value pairs from dictionary/list hierarchies."""
    if isinstance(data, Mapping):
        sanitized: dict[str, Any] = {}
        for k, v in data.items():
            str_key = str(k)
            if is_sensitive_key(str_key):
                sanitized[str_key] = mask_value
            elif isinstance(v, (Mapping, list, tuple)):
                sanitized[str_key] = mask_sensitive_dict(v, mask_value=mask_value)
            else:
                sanitized[str_key] = v
        return sanitized
    elif isinstance(data, (list, tuple)):
        return [mask_sensitive_dict(item, mask_value=mask_value) for item in data]
    return data


def mask_sensitive_string(text: str) -> str:
    """Mask credentials in connection strings, Bearer tokens, or raw text."""
    if not isinstance(text, str):
        return text
    # Mask database passwords: postgresql://user:PASSWORD@host -> postgresql://user:[REDACTED]@host
    text = _DB_URL_REGEX.sub(r"\1[REDACTED]\3", text)
    # Mask bearer tokens: Bearer eyJ... -> Bearer [REDACTED]
    text = _BEARER_REGEX.sub(r"\1[REDACTED]", text)
    return text


def safe_metadata(metadata: dict[str, Any] | None) -> dict[str, Any] | None:
    """Prepare a safe dictionary for audit logs or error payload metadata."""
    if not metadata:
        return None
    return mask_sensitive_dict(metadata)
