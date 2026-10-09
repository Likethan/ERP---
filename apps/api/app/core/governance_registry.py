"""Data Classification & Sensitive Field Registry for CampusOS.

Provides standard institutional data classification taxonomy, masking strategies,
field-level privacy governance, and sanitization for logs, AI, and exports.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
import hashlib
import re
from typing import Any


class DataClassificationLevel(StrEnum):
    """Institutional data classification tiers."""
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"
    SENSITIVE = "SENSITIVE"


class MaskingStrategy(StrEnum):
    """Deterministic masking patterns for sensitive personal and financial data."""
    NONE = "NONE"
    FULL_MASK = "FULL_MASK"
    PARTIAL_MASK = "PARTIAL_MASK"
    EMAIL_MASK = "EMAIL_MASK"
    PHONE_MASK = "PHONE_MASK"
    IDENTIFIER_MASK = "IDENTIFIER_MASK"
    REDACT = "REDACT"
    HASH = "HASH"


@dataclass(frozen=True)
class SensitiveFieldDefinition:
    """Governance metadata for an entity attribute."""
    entity: str
    field: str
    classification: DataClassificationLevel
    masking_strategy: MaskingStrategy
    export_policy: str = "MASK"  # ALLOW, MASK, FORBIDDEN
    logging_policy: str = "REDACT"  # REDACT, MASK, ALLOW
    ai_visibility: bool = False
    allowed_roles: list[str] = field(default_factory=lambda: ["SUPER_ADMIN", "INSTITUTION_ADMIN"])


def mask_email(email_str: str) -> str:
    """Mask email address while preserving domain structure (e.g. u***@example.com)."""
    if not email_str or "@" not in email_str:
        return "[REDACTED_EMAIL]"
    parts = email_str.split("@", 1)
    user_part = parts[0]
    domain_part = parts[1]
    if len(user_part) <= 1:
        masked_user = "*"
    elif len(user_part) == 2:
        masked_user = f"{user_part[0]}*"
    else:
        masked_user = f"{user_part[0]}***{user_part[-1]}"
    return f"{masked_user}@{domain_part}"


def mask_phone(phone_str: str) -> str:
    """Mask phone number preserving last 4 digits (e.g. ******3210)."""
    clean = re.sub(r"[^\d+]", "", str(phone_str))
    if len(clean) <= 4:
        return "****"
    return f"{'*' * (len(clean) - 4)}{clean[-4:]}"


def mask_identifier(ident_str: str) -> str:
    """Mask national/institutional ID preserving last 4 characters (e.g. ********1234)."""
    s = str(ident_str).strip()
    if len(s) <= 4:
        return "****"
    return f"{'*' * (len(s) - 4)}{s[-4:]}"


def mask_partial(val_str: str) -> str:
    """Preserve first 2 and last 2 characters, masking middle with asterisks."""
    s = str(val_str).strip()
    if len(s) <= 4:
        return "****"
    return f"{s[:2]}{'*' * (len(s) - 4)}{s[-2:]}"


def mask_hash(val_str: str) -> str:
    """SHA-256 digest truncated for correlation without leaking plaintext."""
    digest = hashlib.sha256(str(val_str).encode("utf-8")).hexdigest()
    return f"sha256:{digest[:12]}..."


def apply_masking_strategy(val: Any, strategy: MaskingStrategy) -> Any:
    """Apply the chosen masking strategy to an attribute value."""
    if val is None:
        return None
    s_val = str(val)

    if strategy == MaskingStrategy.NONE:
        return val
    elif strategy == MaskingStrategy.EMAIL_MASK:
        return mask_email(s_val)
    elif strategy == MaskingStrategy.PHONE_MASK:
        return mask_phone(s_val)
    elif strategy == MaskingStrategy.IDENTIFIER_MASK:
        return mask_identifier(s_val)
    elif strategy == MaskingStrategy.PARTIAL_MASK:
        return mask_partial(s_val)
    elif strategy == MaskingStrategy.FULL_MASK:
        return "********"
    elif strategy == MaskingStrategy.REDACT:
        return "[REDACTED]"
    elif strategy == MaskingStrategy.HASH:
        return mask_hash(s_val)
    return "[REDACTED]"


# Central canonical sensitive field catalogue across CampusOS domains
SENSITIVE_FIELD_REGISTRY: dict[tuple[str, str], SensitiveFieldDefinition] = {
    # People & User Credentials
    ("User", "password_hash"): SensitiveFieldDefinition(
        "User", "password_hash", DataClassificationLevel.SENSITIVE, MaskingStrategy.REDACT, "FORBIDDEN", "REDACT", False, []
    ),
    ("User", "email"): SensitiveFieldDefinition(
        "User", "email", DataClassificationLevel.CONFIDENTIAL, MaskingStrategy.EMAIL_MASK, "MASK", "MASK", True, ["SUPER_ADMIN", "INSTITUTION_ADMIN", "DEPT_HEAD"]
    ),
    ("User", "phone_number"): SensitiveFieldDefinition(
        "User", "phone_number", DataClassificationLevel.CONFIDENTIAL, MaskingStrategy.PHONE_MASK, "MASK", "MASK", True, ["SUPER_ADMIN", "INSTITUTION_ADMIN"]
    ),
    ("StudentProfile", "emergency_contact_phone"): SensitiveFieldDefinition(
        "StudentProfile", "emergency_contact_phone", DataClassificationLevel.CONFIDENTIAL, MaskingStrategy.PHONE_MASK, "MASK", "MASK", False, ["SUPER_ADMIN", "INSTITUTION_ADMIN"]
    ),
    ("StudentProfile", "identification_number"): SensitiveFieldDefinition(
        "StudentProfile", "identification_number", DataClassificationLevel.RESTRICTED, MaskingStrategy.IDENTIFIER_MASK, "MASK", "REDACT", False, ["SUPER_ADMIN"]
    ),
    ("StudentProfile", "address_line1"): SensitiveFieldDefinition(
        "StudentProfile", "address_line1", DataClassificationLevel.RESTRICTED, MaskingStrategy.PARTIAL_MASK, "MASK", "REDACT", False, ["SUPER_ADMIN", "INSTITUTION_ADMIN"]
    ),

    # Finance
    ("PaymentTransaction", "gateway_reference"): SensitiveFieldDefinition(
        "PaymentTransaction", "gateway_reference", DataClassificationLevel.RESTRICTED, MaskingStrategy.PARTIAL_MASK, "ALLOW", "REDACT", True, ["SUPER_ADMIN", "INSTITUTION_ADMIN", "FINANCE_OFFICER"]
    ),
    ("PaymentTransaction", "card_last4"): SensitiveFieldDefinition(
        "PaymentTransaction", "card_last4", DataClassificationLevel.RESTRICTED, MaskingStrategy.PARTIAL_MASK, "ALLOW", "REDACT", False, ["SUPER_ADMIN", "FINANCE_OFFICER"]
    ),

    # Documents & Security
    ("Document", "storage_key"): SensitiveFieldDefinition(
        "Document", "storage_key", DataClassificationLevel.INTERNAL, MaskingStrategy.FULL_MASK, "FORBIDDEN", "REDACT", False, ["SUPER_ADMIN"]
    ),
    ("AuditLog", "ip_address"): SensitiveFieldDefinition(
        "AuditLog", "ip_address", DataClassificationLevel.INTERNAL, MaskingStrategy.PARTIAL_MASK, "ALLOW", "ALLOW", False, ["SUPER_ADMIN", "INSTITUTION_ADMIN"]
    ),
}

# General keyword-based fallback rules for unknown dictionary payloads
GENERIC_SENSITIVE_PATTERNS: dict[re.Pattern, MaskingStrategy] = {
    re.compile(r"password|secret|token|api_key|private_key|cvv|pin", re.I): MaskingStrategy.REDACT,
    re.compile(r"email", re.I): MaskingStrategy.EMAIL_MASK,
    re.compile(r"phone|mobile", re.I): MaskingStrategy.PHONE_MASK,
    re.compile(r"aadhaar|ssn|tax_id|identity|passport", re.I): MaskingStrategy.IDENTIFIER_MASK,
    re.compile(r"card_number|credit_card", re.I): MaskingStrategy.PARTIAL_MASK,
}


def sanitize_dict_for_roles(
    data: dict[str, Any],
    entity_name: str | None = None,
    user_roles: list[str] | None = None,
) -> dict[str, Any]:
    """Sanitizes dictionary attributes based on entity definitions and the requester's roles."""
    roles = user_roles or []
    is_super = "SUPER_ADMIN" in roles
    sanitized: dict[str, Any] = {}

    for k, v in data.items():
        if v is None:
            sanitized[k] = None
            continue

        field_def = SENSITIVE_FIELD_REGISTRY.get((entity_name or "", k)) if entity_name else None

        if field_def:
            # Check if user role is permitted unmasked view
            if is_super or any(r in field_def.allowed_roles for r in roles):
                sanitized[k] = v
            else:
                sanitized[k] = apply_masking_strategy(v, field_def.masking_strategy)
        else:
            # Fallback to generic pattern checks
            matched_strategy = None
            for pattern, strat in GENERIC_SENSITIVE_PATTERNS.items():
                if pattern.search(k):
                    matched_strategy = strat
                    break
            if matched_strategy and not is_super:
                sanitized[k] = apply_masking_strategy(v, matched_strategy)
            elif isinstance(v, Mapping):
                sanitized[k] = sanitize_dict_for_roles(dict(v), entity_name=None, user_roles=roles)
            elif isinstance(v, list):
                sanitized[k] = [
                    sanitize_dict_for_roles(dict(item), entity_name=None, user_roles=roles)
                    if isinstance(item, Mapping) else item
                    for item in v
                ]
            else:
                sanitized[k] = v

    return sanitized


def sanitize_payload_for_ai(data: Any, entity_name: str | None = None) -> Any:
    """Removes or masks sensitive information before context delivery to AI/LLM models."""
    if isinstance(data, Mapping):
        cleaned: dict[str, Any] = {}
        for k, v in data.items():
            field_def = SENSITIVE_FIELD_REGISTRY.get((entity_name or "", str(k))) if entity_name else None
            if field_def:
                if not field_def.ai_visibility:
                    continue  # Exclude completely from AI context
                cleaned[str(k)] = apply_masking_strategy(v, field_def.masking_strategy)
            else:
                # Check generic sensitive keys
                is_forbidden = any(
                    term in str(k).lower()
                    for term in ("password", "secret", "token", "key", "cvv", "hash", "session")
                )
                if is_forbidden:
                    continue
                cleaned[str(k)] = sanitize_payload_for_ai(v, entity_name=None)
        return cleaned
    elif isinstance(data, list):
        return [sanitize_payload_for_ai(x, entity_name=entity_name) for x in data]
    return data
