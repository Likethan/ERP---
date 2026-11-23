# CampusOS Report Export Architecture

## Export Artifacts
The CampusOS reporting engine supports CSV, XLSX, and JSON export formats with enterprise security hardening:
- **Private Object Storage**: Exports are uploaded to tenant-isolated storage keys:
  `tenants/{tenant_id}/reports/{execution_id}/{export_id}.{format}`
- **Temporary Download References**: Exports include a strict expiration timestamp (default 24 hours), after which download requests are rejected.
- **Download Audit**: Each download access increments `download_count` and triggers an audit log.

## Formula Injection (CSV / Spreadsheet Injection) Protection
To prevent dynamic formula execution when export files are opened in Microsoft Excel, LibreOffice Calc, or Google Sheets:
- All cell values starting with `= `, `+`, `-`, `@`, `\t`, or `\r` are automatically prefixed with a single quotation mark (`'`).
- This renders malicious formulas as plain text literals without interfering with numerical analysis.
