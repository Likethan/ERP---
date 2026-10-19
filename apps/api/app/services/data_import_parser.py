"""Secure File Parser and Intake Engine for CampusOS Data Import (Step 40).

Enforces:
- Untrusted input sanitization
- CSV and XLSX parsing with zero formula execution (openpyxl data_only=True)
- Formula injection escaping for CSV/XLSX export/reporting
- Memory bounds and file size limit checks (default 25MB max)
- Encoding auto-detection (UTF-8, UTF-8-SIG, Latin-1)
- Header extraction and deduplication detection
"""

import csv
import io
import re
from typing import Any, BinaryIO, Generator

from app.core.exceptions import ValidationException

MAX_IMPORT_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB
MAX_IMPORT_RECORD_COUNT = 50000  # 50k rows maximum per single batch job


def escape_formula_injection(value: Any) -> Any:
    """Neutralize potential CSV/spreadsheet formula injection attacks.

    Prepends a single quote if string begins with =, +, -, @, tab, or carriage return.
    """
    if not isinstance(value, str):
        return value
    if value and value[0] in ("=", "+", "-", "@", "\t", "\r"):
        return f"'{value}"
    return value


def sanitize_cell_value(val: Any) -> Any:
    """Sanitize raw extracted cell value."""
    if val is None:
        return ""
    if isinstance(val, str):
        # Strip null bytes and non-printable control characters except newline and tab
        cleaned = "".join(ch for ch in val if ch in ("\n", "\r", "\t") or ord(ch) >= 32)
        return cleaned.strip()
    return val


class DataImportParser:
    """Secure, streaming-capable parser for CSV and XLSX structured files."""

    escape_formula_injection = staticmethod(escape_formula_injection)

    @classmethod
    def parse_file(
        cls,
        file_bytes: bytes,
        file_format: str,
        max_rows: int = MAX_IMPORT_RECORD_COUNT,
    ) -> tuple[list[str], list[dict[str, Any]]]:
        """Parse binary content into headers and list of row dicts.

        Returns:
            tuple of (headers, list of row records with row_number and data)
        """
        if len(file_bytes) > MAX_IMPORT_FILE_SIZE_BYTES:
            raise ValidationException(
                f"File size {len(file_bytes)} bytes exceeds maximum allowed limit of {MAX_IMPORT_FILE_SIZE_BYTES} bytes (25 MB)."
            )

        fmt = file_format.upper().strip().lstrip(".")
        if fmt == "CSV":
            return cls._parse_csv(file_bytes, max_rows)
        elif fmt in ("XLSX", "XLS"):
            return cls._parse_xlsx(file_bytes, max_rows)
        else:
            raise ValidationException(
                f"Unsupported file format '{file_format}'. Supported formats are CSV and XLSX."
            )

    @classmethod
    def _parse_csv(
        cls,
        file_bytes: bytes,
        max_rows: int,
    ) -> tuple[list[str], list[dict[str, Any]]]:
        """Safely parse CSV content with multiple encoding attempts."""
        # Attempt UTF-8, then UTF-8-SIG, then Latin-1
        text_content: str | None = None
        for enc in ("utf-8-sig", "utf-8", "latin-1"):
            try:
                text_content = file_bytes.decode(enc)
                break
            except UnicodeDecodeError:
                continue

        if text_content is None:
            raise ValidationException("Unable to decode CSV file. Ensure it is encoded in valid UTF-8.")

        # Determine delimiter by sniffing first 2048 bytes
        sample = text_content[:4096]
        delimiter = ","
        try:
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample, delimiters=[",", ";", "\t", "|"])
            delimiter = dialect.delimiter
        except Exception:
            delimiter = ","

        f_io = io.StringIO(text_content)
        reader = csv.reader(f_io, delimiter=delimiter)

        try:
            raw_headers = next(reader, None)
        except Exception as exc:
            raise ValidationException(f"Malformed CSV file structure: {str(exc)}")

        if not raw_headers:
            raise ValidationException("CSV file is empty or missing header row.")

        # Clean and validate headers
        headers: list[str] = [sanitize_cell_value(h) for h in raw_headers if h is not None]
        headers = [h for h in headers if h]  # Remove empty trailing headers

        if not headers:
            raise ValidationException("CSV file contains no valid column headers.")

        # Check duplicate headers
        seen_headers = set()
        duplicates = set()
        for h in headers:
            h_lower = h.lower()
            if h_lower in seen_headers:
                duplicates.add(h)
            seen_headers.add(h_lower)
        if duplicates:
            raise ValidationException(f"Duplicate headers detected in CSV file: {', '.join(duplicates)}.")

        records: list[dict[str, Any]] = []
        row_num = 1  # Header was row 1, data rows start at row 2

        for row in reader:
            row_num += 1
            if not row or all(not str(cell).strip() for cell in row):
                continue  # Skip empty lines

            if len(records) >= max_rows:
                raise ValidationException(
                    f"File exceeds maximum allowed records limit of {max_rows} rows."
                )

            # Map fields safely
            row_dict: dict[str, Any] = {}
            for idx, header in enumerate(headers):
                val = row[idx] if idx < len(row) else ""
                row_dict[header] = sanitize_cell_value(val)

            records.append({
                "row_number": row_num,
                "data": row_dict,
            })

        if not records:
            raise ValidationException("CSV file contains headers but no data rows.")

        return headers, records

    @classmethod
    def _parse_xlsx(
        cls,
        file_bytes: bytes,
        max_rows: int,
    ) -> tuple[list[str], list[dict[str, Any]]]:
        """Safely parse Excel .xlsx content using openpyxl without formula or macro execution."""
        try:
            import openpyxl
        except ImportError:
            raise ValidationException("XLSX parsing requires openpyxl package.")

        f_io = io.BytesIO(file_bytes)
        try:
            # data_only=True ensures values are returned instead of formula strings
            # read_only=True ensures bounded memory usage for large spreadsheets
            wb = openpyxl.load_workbook(f_io, data_only=True, read_only=True)
        except Exception as exc:
            raise ValidationException(f"Malformed or encrypted Excel spreadsheet: {str(exc)}")

        sheet = wb.active
        if sheet is None:
            raise ValidationException("Excel file contains no active worksheet.")

        headers: list[str] = []
        records: list[dict[str, Any]] = []
        row_num = 0

        try:
            for row in sheet.iter_rows(values_only=True):
                row_num += 1
                if row_num == 1:
                    # Header row
                    raw_headers = [sanitize_cell_value(c) for c in row if c is not None]
                    headers = [h for h in raw_headers if h]
                    if not headers:
                        raise ValidationException("Excel worksheet contains no valid column headers.")

                    # Check duplicate headers
                    seen_headers = set()
                    duplicates = set()
                    for h in headers:
                        h_lower = h.lower()
                        if h_lower in seen_headers:
                            duplicates.add(h)
                        seen_headers.add(h_lower)
                    if duplicates:
                        raise ValidationException(f"Duplicate headers detected in Excel worksheet: {', '.join(duplicates)}.")
                    continue

                if not row or all(c is None or str(c).strip() == "" for c in row):
                    continue  # Skip blank rows

                if len(records) >= max_rows:
                    raise ValidationException(
                        f"Worksheet exceeds maximum allowed records limit of {max_rows} rows."
                    )

                row_dict: dict[str, Any] = {}
                for idx, header in enumerate(headers):
                    val = row[idx] if idx < len(row) else None
                    row_dict[header] = sanitize_cell_value(val)

                records.append({
                    "row_number": row_num,
                    "data": row_dict,
                })
        finally:
            wb.close()

        if not records:
            raise ValidationException("Excel worksheet contains headers but no data rows.")

        return headers, records

    @classmethod
    def generate_error_report_csv(cls, error_records: list[dict[str, Any]]) -> str:
        """Generate sanitized CSV error report with formula injection escaping."""
        output = io.StringIO()
        fieldnames = [
            "row_number",
            "matching_key",
            "field_name",
            "error_code",
            "error_message",
            "suggested_fix",
            "status",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()

        for rec in error_records:
            row_num = rec.get("row_number", "")
            matching_key = escape_formula_injection(rec.get("matching_key", ""))
            status = rec.get("status", "FAILED")

            errors = rec.get("errors", [])
            if not errors:
                writer.writerow({
                    "row_number": row_num,
                    "matching_key": matching_key,
                    "field_name": "",
                    "error_code": "UNKNOWN_ERROR",
                    "error_message": escape_formula_injection(rec.get("message", "Processing error")),
                    "suggested_fix": "Review row data against template constraints.",
                    "status": status,
                })
            else:
                for err in errors:
                    writer.writerow({
                        "row_number": row_num,
                        "matching_key": matching_key,
                        "field_name": escape_formula_injection(err.get("field", "")),
                        "error_code": escape_formula_injection(err.get("code", "")),
                        "error_message": escape_formula_injection(err.get("message", "")),
                        "suggested_fix": escape_formula_injection(err.get("suggested_fix", "Correct field format")),
                        "status": status,
                    })

        return output.getvalue()
