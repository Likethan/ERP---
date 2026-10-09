"""Allowlisted Data Mapping & Transformation Engine.

Enforces:
- Strict allowlist of pure, deterministic data transformations.
- Complete prohibition of arbitrary code execution, eval(), or dynamic syntax.
- Schema alignment between external payload models and CampusOS domain schemas.
- Validation, default fallback, and safe field extraction.
"""

from collections.abc import Callable
from datetime import date, datetime
from enum import StrEnum
import re
from typing import Any

from app.core.exceptions import ValidationException


class TransformationType(StrEnum):
    NONE = "NONE"
    TRIM = "TRIM"
    UPPERCASE = "UPPERCASE"
    LOWERCASE = "LOWERCASE"
    TITLECASE = "TITLECASE"
    TO_STRING = "TO_STRING"
    TO_INT = "TO_INT"
    TO_FLOAT = "TO_FLOAT"
    TO_BOOLEAN = "TO_BOOLEAN"
    ISO_DATE = "ISO_DATE"
    PHONE_E164 = "PHONE_E164"
    SPLIT_FIRST = "SPLIT_FIRST"
    SPLIT_LAST = "SPLIT_LAST"
    COALESCE = "COALESCE"
    MAP_VALUE = "MAP_VALUE"


def _transform_trim(val: Any, _: dict[str, Any]) -> Any:
    return str(val).strip() if val is not None else None


def _transform_uppercase(val: Any, _: dict[str, Any]) -> Any:
    return str(val).upper() if val is not None else None


def _transform_lowercase(val: Any, _: dict[str, Any]) -> Any:
    return str(val).lower() if val is not None else None


def _transform_titlecase(val: Any, _: dict[str, Any]) -> Any:
    return str(val).title() if val is not None else None


def _transform_to_string(val: Any, _: dict[str, Any]) -> Any:
    return str(val) if val is not None else None


def _transform_to_int(val: Any, _: dict[str, Any]) -> Any:
    if val is None or val == "":
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError) as exc:
        raise ValidationException(f"Cannot transform '{val}' to integer: {exc}") from exc


def _transform_to_float(val: Any, _: dict[str, Any]) -> Any:
    if val is None or val == "":
        return None
    try:
        return float(val)
    except (ValueError, TypeError) as exc:
        raise ValidationException(f"Cannot transform '{val}' to float: {exc}") from exc


def _transform_to_boolean(val: Any, _: dict[str, Any]) -> Any:
    if val is None:
        return False
    if isinstance(val, bool):
        return val
    s = str(val).strip().lower()
    return s in ("true", "1", "yes", "y", "t", "active")


def _transform_iso_date(val: Any, _: dict[str, Any]) -> Any:
    if val is None or val == "":
        return None
    if isinstance(val, (date, datetime)):
        return val.isoformat()
    s = str(val).strip()
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt.isoformat()
    except Exception:
        # Fallback date parsing
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y"):
            try:
                return datetime.strptime(s, fmt).date().isoformat()
            except ValueError:
                pass
        raise ValidationException(f"Unrecognized date format for '{val}'")


def _transform_phone_e164(val: Any, _: dict[str, Any]) -> Any:
    if val is None or val == "":
        return None
    clean = re.sub(r"[^\d+]", "", str(val))
    if not clean.startswith("+"):
        clean = "+91" + clean.lstrip("0")  # Default India code if unspecified
    return clean


def _transform_split_first(val: Any, params: dict[str, Any]) -> Any:
    if val is None:
        return None
    sep = params.get("delimiter", " ")
    parts = str(val).split(sep, 1)
    return parts[0].strip() if parts else None


def _transform_split_last(val: Any, params: dict[str, Any]) -> Any:
    if val is None:
        return None
    sep = params.get("delimiter", " ")
    parts = str(val).rsplit(sep, 1)
    return parts[-1].strip() if parts else None


def _transform_map_value(val: Any, params: dict[str, Any]) -> Any:
    if val is None:
        return params.get("default")
    value_map = params.get("value_map", {})
    return value_map.get(str(val), params.get("default", val))


TRANSFORMATION_REGISTRY: dict[TransformationType, Callable[[Any, dict[str, Any]], Any]] = {
    TransformationType.NONE: lambda v, _: v,
    TransformationType.TRIM: _transform_trim,
    TransformationType.UPPERCASE: _transform_uppercase,
    TransformationType.LOWERCASE: _transform_lowercase,
    TransformationType.TITLECASE: _transform_titlecase,
    TransformationType.TO_STRING: _transform_to_string,
    TransformationType.TO_INT: _transform_to_int,
    TransformationType.TO_FLOAT: _transform_to_float,
    TransformationType.TO_BOOLEAN: _transform_to_boolean,
    TransformationType.ISO_DATE: _transform_iso_date,
    TransformationType.PHONE_E164: _transform_phone_e164,
    TransformationType.SPLIT_FIRST: _transform_split_first,
    TransformationType.SPLIT_LAST: _transform_split_last,
    TransformationType.COALESCE: lambda v, p: v if v is not None else p.get("fallback"),
    TransformationType.MAP_VALUE: _transform_map_value,
}


def _get_nested_field(data: dict[str, Any], path: str) -> Any:
    """Extract value using dot-notation path (e.g. 'contact.email')."""
    parts = path.split(".")
    curr: Any = data
    for part in parts:
        if isinstance(curr, dict) and part in curr:
            curr = curr[part]
        else:
            return None
    return curr


def apply_data_mapping(
    source_record: dict[str, Any],
    rules: list[dict[str, Any]],
) -> dict[str, Any]:
    """Execute allowlisted mapping rules against source dictionary.

    Rule Structure:
    {
        "source_field": "external_name",
        "target_field": "full_name",
        "transformation": "TITLECASE",
        "transformation_params": {},
        "required": True,
        "default": "Default Value",
        "validation_regex": "^[a-zA-Z ]+$"
    }
    """
    mapped_target: dict[str, Any] = {}

    for rule in rules:
        source_field = rule.get("source_field")
        target_field = rule.get("target_field")
        if not source_field or not target_field:
            continue

        raw_val = _get_nested_field(source_record, source_field)

        # Handle missing / default values
        if raw_val is None or raw_val == "":
            if rule.get("default") is not None:
                raw_val = rule.get("default")
            elif rule.get("required", False):
                raise ValidationException(
                    f"Required field '{source_field}' (mapping to '{target_field}') is missing in source payload."
                )

        # Apply allowlisted transformation
        tr_type_str = (rule.get("transformation") or "NONE").upper()
        try:
            tr_type = TransformationType(tr_type_str)
        except ValueError:
            raise ValidationException(
                f"Unsupported transformation type '{tr_type_str}'. Allowed: {[t.value for t in TransformationType]}"
            )

        fn = TRANSFORMATION_REGISTRY[tr_type]
        params = rule.get("transformation_params") or {}
        transformed_val = fn(raw_val, params)

        # Validate against regex if configured
        val_regex = rule.get("validation_regex")
        if val_regex and transformed_val is not None:
            if not re.match(val_regex, str(transformed_val)):
                raise ValidationException(
                    f"Value '{transformed_val}' for '{target_field}' does not match validation regex '{val_regex}'."
                )

        mapped_target[target_field] = transformed_val

    return mapped_target
