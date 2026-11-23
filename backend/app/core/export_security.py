"""Export and CSV formula injection protection for CampusOS.

Prevents formula injection attacks (CSV Injection / DDE execution) when export
files containing user-provided names, codes, or text are opened in spreadsheet software.
"""

from typing import Any

FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def sanitize_csv_field(value: Any) -> Any:
    """Sanitize a single CSV cell value to neutralize spreadsheet formula execution."""
    if not isinstance(value, str):
        return value

    if not value:
        return value

    trimmed = value.lstrip(" ")
    if value.startswith(FORMULA_PREFIXES) or (trimmed and trimmed.startswith(FORMULA_PREFIXES)):
        return f"'{value}"

    return value


def sanitize_csv_row(row: list[Any] | dict[str, Any]) -> list[Any] | dict[str, Any]:
    """Sanitize all fields in an export row dictionary or list."""
    if isinstance(row, dict):
        return {k: sanitize_csv_field(v) for k, v in row.items()}
    elif isinstance(row, list):
        return [sanitize_csv_field(v) for v in row]
    return row
