"""Enterprise Normalization Utilities & Privacy Masking (Step 24).

Provides deterministic sanitization and standardization for text, codes, emails,
phone numbers, and web domains used in duplicate matching and quality validation,
without destroying or overwriting raw canonical user inputs.
"""

import re
import unicodedata
from urllib.parse import urlparse


class NormalizationService:
    """Centralized normalization and privacy masking service for master data."""

    @staticmethod
    def normalize_text(val: str | None) -> str:
        """Strip, lowercase, normalize unicode characters, punctuation, and whitespace."""
        if not val:
            return ""
        # Standardize ampersands to 'and'
        val = val.replace("&", " and ")
        # Unicode normalization (NFKD decomposes accented glyphs)
        normalized = unicodedata.normalize("NFKD", val)
        ascii_text = normalized.encode("ascii", "ignore").decode("utf-8")
        # Strip punctuation symbols replacing with spaces
        clean_punct = re.sub(r"[^\w\s]", " ", ascii_text)
        # Collapse multiple spaces and trim
        cleaned = re.sub(r"\s+", " ", clean_punct).strip().lower()
        return cleaned

    @staticmethod
    def normalize_code(val: str | None) -> str:
        """Standardize identifiers, codes, and roll numbers (alphanumeric uppercase)."""
        if not val:
            return ""
        # Remove spaces, dashes, dots, underscores, uppercase
        cleaned = re.sub(r"[\s\-_.]+", "", str(val)).strip().upper()
        return cleaned

    @staticmethod
    def normalize_email(val: str | None) -> str:
        """Lowercase, strip whitespace, and normalize email address."""
        if not val:
            return ""
        email = val.strip().lower()
        if "@" not in email:
            return email
        local_part, domain = email.split("@", 1)
        # Remove trailing/leading dots in domain
        domain = domain.strip(".")
        return f"{local_part}@{domain}"

    @staticmethod
    def normalize_phone(val: str | None) -> str:
        """Extract digits and normalize phone number format."""
        if not val:
            return ""
        digits = re.sub(r"\D", "", str(val))
        # If starts with '91' and length 12, extract 10 digits
        if len(digits) == 12 and digits.startswith("91"):
            digits = digits[2:]
        elif len(digits) > 10 and digits.startswith("0"):
            digits = digits.lstrip("0")
        return digits

    @staticmethod
    def normalize_domain(val: str | None) -> str:
        """Extract root hostname from URL or domain string, stripping www and protocols."""
        if not val:
            return ""
        cleaned = val.strip().lower()
        if not cleaned.startswith(("http://", "https://")):
            cleaned = "http://" + cleaned
        try:
            parsed = urlparse(cleaned)
            hostname = parsed.hostname or ""
            if hostname.startswith("www."):
                hostname = hostname[4:]
            return hostname.strip()
        except Exception:
            return re.sub(r"^(https?://)?(www\.)?", "", val.strip().lower()).split("/")[0]

    # -------------------------------------------------------------------------
    # Privacy Masking
    # -------------------------------------------------------------------------

    @staticmethod
    def mask_email(email: str | None) -> str:
        """Produce safe masked representation of email (e.g. j***e@domain.com)."""
        if not email or "@" not in email:
            return "***"
        local, domain = email.split("@", 1)
        if len(local) <= 2:
            masked_local = local[0] + "*"
        else:
            masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
        return f"{masked_local}@{domain}"

    @staticmethod
    def mask_phone(phone: str | None) -> str:
        """Produce safe masked representation of phone number (e.g. +91******1234)."""
        if not phone:
            return "***"
        clean = re.sub(r"\D", "", str(phone))
        if len(clean) <= 4:
            return "****"
        if len(clean) == 12 and clean.startswith("91"):
            clean_10 = clean[2:]
            return f"+91{'*' * 6}{clean_10[-4:]}"
        if len(clean) == 10:
            return f"+91{'*' * 6}{clean[-4:]}"
        masked = "*" * (len(clean) - 4) + clean[-4:]
        return masked


mask_email = NormalizationService.mask_email
mask_phone = NormalizationService.mask_phone
