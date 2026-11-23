"""Enterprise AI Prompt Injection Defense, Safety Guard & PII Sanitizer.

Enforces zero-trust input/output validation, prompt injection pattern detection,
sensitive PII redaction, and strict query parameter allowlisting.
"""

import re
from typing import Any

from app.core.exceptions import ValidationException


class PromptGuard:
    """Multi-layer safety firewall defending against prompt injection and data exfiltration."""

    # Malicious injection patterns
    INJECTION_PATTERNS = [
        re.compile(
            r"ignore\s+(all\s+)?(previous\s+|prior\s+|above\s+|system\s+)*instructions?",
            re.IGNORECASE,
        ),
        re.compile(
            r"disregard\s+(all\s+)?(previous\s+|prior\s+|system\s+)*prompts?",
            re.IGNORECASE,
        ),
        re.compile(
            r"you\s+are\s+now\s+in\s+(developer|unrestricted|god|dan)\s+mode", re.IGNORECASE
        ),
        re.compile(r"reveal\s+(your\s+)?system\s+prompt", re.IGNORECASE),
        re.compile(
            r"what\s+are\s+your\s+(hidden|internal|system)\s+instructions\??", re.IGNORECASE
        ),
        re.compile(r"print\s+(your\s+)?(initial|system)\s+prompt", re.IGNORECASE),
        re.compile(r"(reveal|print|show)\s+.*?(system|initial)\s+prompt", re.IGNORECASE),
        re.compile(r"(drop|alter|delete|truncate)\s+table\s+", re.IGNORECASE),
        re.compile(r"union\s+select\s+", re.IGNORECASE),
        re.compile(r"exec(\s+|\()", re.IGNORECASE),
        re.compile(r"<script.*?>.*?</script>", re.IGNORECASE),
        re.compile(r"bypass\s+all\s+(security|authorization|rules)", re.IGNORECASE),
        re.compile(r"reveal\s+.*?(secret|key|password|credential)", re.IGNORECASE),
    ]

    # PII patterns for redaction
    PHONE_REGEX = re.compile(
        r"(\+?\d{1,4}[-.\s]?)?(\(?\d{2,5}\)?[-.\s]?)?\d{3,5}[-.\s]?\d{4,5}|\b\d{10}\b"
    )
    AADHAAR_REGEX = re.compile(r"\b\d{4}\s\d{4}\s\d{4}\b")
    EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

    @classmethod
    def inspect_and_sanitize_query(cls, text: str) -> str:
        """Inspect query for adversarial prompt injection patterns. Raises ValidationException if malicious."""
        cleaned = text.strip()
        if not cleaned:
            raise ValidationException("Query string cannot be empty.")

        for pattern in cls.INJECTION_PATTERNS:
            if pattern.search(cleaned):
                raise ValidationException(
                    "Security validation failed: The input contains potentially adversarial or prohibited prompt instructions."
                )

        return cleaned

    @classmethod
    def redact_pii(cls, text: str) -> str:
        """Redact sensitive personally identifiable numbers and contact details before context insertion."""
        redacted = cls.AADHAAR_REGEX.sub("[NATIONAL_ID_REDACTED]", text)
        redacted = cls.PHONE_REGEX.sub("[PHONE_REDACTED]", redacted)
        return redacted

    @classmethod
    def validate_tool_parameters(cls, tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
        """Verify tool arguments contain no raw SQL, code injection, or directory traversal."""
        sanitized = {}
        for k, v in params.items():
            if isinstance(v, str):
                val = v.strip()
                if ";" in val or "--" in val or "/*" in val:
                    raise ValidationException(
                        f"Invalid parameter value for '{k}': dangerous characters detected."
                    )
                if "../" in val or "..\\" in val:
                    raise ValidationException(
                        f"Invalid parameter value for '{k}': directory traversal attempt."
                    )
                sanitized[k] = val
            else:
                sanitized[k] = v
        return sanitized
