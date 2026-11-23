"""Centralized Configuration Validation Engine for CampusOS (Step 23)."""

import re
from datetime import date, datetime
from typing import Any
from urllib.parse import urlparse

from app.core.exceptions import ConfigurationInvalidException
from app.models.configuration import ConfigurationDataType, ConfigurationDefinition


class ConfigurationValidationService:
    """Centralized validation engine validating typed configuration against constraints."""

    ISO_CURRENCIES = {
        "INR",
        "USD",
        "EUR",
        "GBP",
        "AUD",
        "CAD",
        "SGD",
        "JPY",
        "AED",
        "SAR",
        "CHF",
        "CNY",
        "NZD",
    }

    @classmethod
    def validate(
        cls,
        definition: ConfigurationDefinition,
        value: Any,
    ) -> tuple[bool, list[str]]:
        """Validate a proposed configuration value against definition constraints."""
        errors: list[str] = []

        if value is None:
            schema = definition.validation_schema or {}
            if schema.get("required", False):
                errors.append(f"Value for '{definition.key}' is required and cannot be null.")
            return len(errors) == 0, errors

        dt = definition.data_type

        # 1. Type and Range Checks
        if dt == ConfigurationDataType.STRING:
            if not isinstance(value, str):
                errors.append(
                    f"Expected string value for '{definition.key}', got {type(value).__name__}."
                )
            else:
                schema = definition.validation_schema or {}
                if "min_length" in schema and len(value) < schema["min_length"]:
                    errors.append(
                        f"Length of '{definition.key}' must be at least {schema['min_length']}."
                    )
                if "max_length" in schema and len(value) > schema["max_length"]:
                    errors.append(
                        f"Length of '{definition.key}' cannot exceed {schema['max_length']}."
                    )
                if "regex" in schema and not re.match(schema["regex"], value):
                    errors.append(
                        f"Value '{value}' for '{definition.key}' does not match required pattern."
                    )

        elif dt == ConfigurationDataType.INTEGER:
            if not isinstance(value, int) or isinstance(value, bool):
                errors.append(
                    f"Expected integer value for '{definition.key}', got {type(value).__name__}."
                )
            else:
                schema = definition.validation_schema or {}
                if "min" in schema and value < schema["min"]:
                    errors.append(f"Value of '{definition.key}' must be at least {schema['min']}.")
                if "max" in schema and value > schema["max"]:
                    errors.append(f"Value of '{definition.key}' cannot exceed {schema['max']}.")

        elif dt == ConfigurationDataType.DECIMAL:
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                errors.append(
                    f"Expected numeric value for '{definition.key}', got {type(value).__name__}."
                )
            else:
                schema = definition.validation_schema or {}
                if "min" in schema and value < schema["min"]:
                    errors.append(f"Value of '{definition.key}' must be at least {schema['min']}.")
                if "max" in schema and value > schema["max"]:
                    errors.append(f"Value of '{definition.key}' cannot exceed {schema['max']}.")

        elif dt == ConfigurationDataType.BOOLEAN:
            if not isinstance(value, bool):
                errors.append(
                    f"Expected boolean for '{definition.key}', got {type(value).__name__}."
                )

        elif dt == ConfigurationDataType.PERCENTAGE:
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                errors.append(
                    f"Expected percentage for '{definition.key}', got {type(value).__name__}."
                )
            else:
                if value < 0 or value > 100:
                    errors.append(f"Percentage for '{definition.key}' must be between 0 and 100.")

        elif dt == ConfigurationDataType.CURRENCY:
            if not isinstance(value, str):
                errors.append(
                    f"Expected currency for '{definition.key}', got {type(value).__name__}."
                )
            else:
                val_upper = value.strip().upper()
                if len(val_upper) != 3 or val_upper not in cls.ISO_CURRENCIES:
                    errors.append(
                        f"Currency code '{value}' is not a recognized 3-letter currency (e.g. INR)."
                    )

        elif dt == ConfigurationDataType.ENUM:
            allowed = definition.allowed_values or []
            schema = definition.validation_schema or {}
            if "allowed_values" in schema:
                allowed = schema["allowed_values"]
            if allowed and value not in allowed:
                errors.append(f"Value '{value}' for '{definition.key}' must be one of {allowed}.")

        elif dt == ConfigurationDataType.URL:
            if not isinstance(value, str):
                errors.append(
                    f"Expected URL string for '{definition.key}', got {type(value).__name__}."
                )
            else:
                try:
                    parsed = urlparse(value)
                    if not (parsed.scheme in ("http", "https") and parsed.netloc):
                        errors.append(
                            f"Value '{value}' for '{definition.key}' is not a valid HTTP/HTTPS URL."
                        )
                except Exception:
                    errors.append(f"Invalid URL formatting for '{definition.key}'.")

        elif dt == ConfigurationDataType.DATE:
            if isinstance(value, str):
                try:
                    date.fromisoformat(value)
                except ValueError:
                    errors.append(
                        f"Expected ISO date (YYYY-MM-DD) for '{definition.key}', got '{value}'."
                    )
            elif not isinstance(value, date):
                errors.append(f"Expected date for '{definition.key}'.")

        elif dt == ConfigurationDataType.DATETIME:
            if isinstance(value, str):
                try:
                    datetime.fromisoformat(value)
                except ValueError:
                    errors.append(f"Expected ISO datetime for '{definition.key}', got '{value}'.")
            elif not isinstance(value, datetime):
                errors.append(f"Expected datetime for '{definition.key}'.")

        elif dt == ConfigurationDataType.DURATION:
            if not isinstance(value, (int, str)):
                errors.append(
                    f"Expected duration in seconds (int) or duration string for '{definition.key}'."
                )

        elif dt == ConfigurationDataType.JSON:
            if not isinstance(value, (dict, list)):
                errors.append(f"Expected structured JSON object or list for '{definition.key}'.")

        return len(errors) == 0, errors

    @classmethod
    def validate_or_raise(
        cls,
        definition: ConfigurationDefinition,
        value: Any,
    ) -> None:
        """Validate a proposed configuration value or raise ConfigurationInvalidException."""
        valid, errors = cls.validate(definition, value)
        if not valid:
            msg = f"Validation failed for configuration '{definition.key}': {'; '.join(errors)}"
            raise ConfigurationInvalidException(
                message=msg,
                details=[{"field": definition.key, "error": err} for err in errors],
            )
