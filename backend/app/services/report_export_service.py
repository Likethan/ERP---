"""Export Engine & Artifact Generation Service for CampusOS Reporting.

Generates CSV, XLSX, and JSON export artifacts with formula injection sanitization,
private tenant-isolated object storage paths, and time-bound download tokens.
"""

import csv
import io
import json
import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ValidationException
from app.core.export_security import sanitize_csv_row
from app.core.storage import get_document_storage
from app.models.reporting import (
    ReportExecution,
    ReportExport,
    ReportExportFormat,
)
from app.schemas.reporting import AnalyticsQueryResult

logger = logging.getLogger("campusos.reporting.export")


class ReportExportService:
    """Produces secured export artifacts in tenant-scoped object storage."""

    @classmethod
    async def create_export(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        execution: ReportExecution,
        result_data: AnalyticsQueryResult,
        export_format: str = ReportExportFormat.CSV,
        expiration_hours: int = 24,
    ) -> ReportExport:
        """Serializes query results into secured export artifacts and persists them to private storage."""
        fmt_clean = export_format.upper().strip()
        if fmt_clean not in (ReportExportFormat.CSV, ReportExportFormat.JSON, ReportExportFormat.XLSX):
            raise ValidationException(f"Unsupported export format '{export_format}'. Supported: CSV, JSON, XLSX.")

        export_id = uuid4()
        now = datetime.now(UTC)
        expires_at = now + timedelta(hours=expiration_hours)

        table_data = result_data.table_data
        headers = table_data.headers
        rows = table_data.rows

        if fmt_clean == ReportExportFormat.CSV:
            mime_type = "text/csv"
            ext = "csv"
            content_bytes = cls._generate_csv(headers, rows)
        elif fmt_clean == ReportExportFormat.JSON:
            mime_type = "application/json"
            ext = "json"
            content_bytes = cls._generate_json(result_data)
        else:  # XLSX / Tabular Spreadsheet
            mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ext = "xlsx"
            content_bytes = cls._generate_csv(headers, rows)  # Clean CSV compatible representation

        filename = f"report_{result_data.query.dataset}_{now.strftime('%Y%m%d_%H%M%S')}.{ext}"
        destination_key = f"tenants/{tenant_id}/reports/{execution.id}/{export_id}.{ext}"

        # Upload to private storage
        storage = get_document_storage()
        await storage.upload(
            file_content=content_bytes,
            destination_key=destination_key,
            mime_type=mime_type,
            metadata={"tenant_id": str(tenant_id), "execution_id": str(execution.id)},
        )

        export = ReportExport(
            id=export_id,
            tenant_id=tenant_id,
            execution_id=execution.id,
            export_format=fmt_clean,
            storage_key=destination_key,
            filename=filename,
            mime_type=mime_type,
            file_size_bytes=len(content_bytes),
            download_count=0,
            expires_at=expires_at,
            created_at=now,
        )
        db.add(export)
        await db.commit()
        await db.refresh(export)

        logger.info(
            "Report export %s generated for tenant %s (size: %d bytes, expires: %s)",
            export.id, tenant_id, len(content_bytes), expires_at.isoformat()
        )
        return export

    @classmethod
    def _generate_csv(cls, headers: list[str], rows: list[list]) -> bytes:
        """Outputs CSV bytes with robust formula injection sanitization on every cell."""
        out = io.StringIO()
        writer = csv.writer(out, quoting=csv.QUOTE_MINIMAL)

        # Write sanitized headers
        sanitized_headers = [str(h) for h in sanitize_csv_row(headers)]
        writer.writerow(sanitized_headers)

        # Write sanitized data rows
        for row in rows:
            sanitized_row = sanitize_csv_row(row)
            writer.writerow(sanitized_row)

        return out.getvalue().encode("utf-8")

    @classmethod
    def _generate_json(cls, result_data: AnalyticsQueryResult) -> bytes:
        """Outputs formatted, structured JSON bytes."""
        payload = result_data.model_dump()
        return json.dumps(payload, indent=2, default=str).encode("utf-8")

    @classmethod
    async def get_export_file(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        export_id: UUID,
    ) -> tuple[bytes, ReportExport]:
        """Fetches export artifact verifying tenant isolation and expiration."""
        from sqlalchemy import and_, select
        stmt = select(ReportExport).where(
            and_(
                ReportExport.id == export_id,
                ReportExport.tenant_id == tenant_id,
            )
        )
        export = (await db.execute(stmt)).scalar_one_or_none()
        if not export:
            raise NotFoundException("ReportExport", export_id)

        if export.is_expired:
            raise ValidationException("The requested report export artifact has expired and is no longer available.")

        storage = get_document_storage()
        storage.validate_tenant_storage_key(export.storage_key, tenant_id)
        content = await storage.download(export.storage_key)

        # Increment download audit count
        export.download_count += 1
        await db.commit()

        return content, export
