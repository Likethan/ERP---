"""Enterprise Object Storage & Document Recovery Service (Step 31).

Product Vision: "One Campus. One System. One Source of Truth."

Guarantees:
- Audits document records against underlying object/filesystem storage
- Detects missing files (database references to nonexistent storage objects)
- Detects orphaned files (unreferenced files lingering on storage)
- Preserves tenant isolation and least-privilege access
- Never logs private document contents or sensitive URLs
"""

import logging
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditEventCategory, build_audit_entry
from app.models.documents import Document
from app.models.reliability import PlatformStorageAuditRecord, StorageAuditStatus

logger = logging.getLogger("campusos.storage_recovery")


class StorageRecoveryService:
    """Service for storage integrity inspection, reconciliation, and disaster recovery."""

    DEFAULT_STORAGE_DIR = Path("./storage/documents")

    @classmethod
    async def audit_storage_integrity(
        cls,
        db: AsyncSession,
        storage_base_dir: Path | None = None,
        tenant_id: UUID | None = None,
        user_id: UUID | None = None,
    ) -> PlatformStorageAuditRecord:
        """Scan document database records and storage objects to identify discrepancies."""
        start_time = time.perf_counter()
        now = datetime.now(UTC)
        base_dir = storage_base_dir or cls.DEFAULT_STORAGE_DIR
        base_dir.mkdir(parents=True, exist_ok=True)

        record = PlatformStorageAuditRecord(
            id=uuid4(),
            status=StorageAuditStatus.RUNNING,
            total_db_records=0,
            total_storage_files=0,
            missing_files_count=0,
            orphaned_files_count=0,
            missing_file_keys=[],
            orphaned_file_keys=[],
            started_at=now,
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)

        try:
            # 1. Fetch DB records
            stmt = select(Document.file_reference).where(
                Document.file_reference.isnot(None),
                Document.deleted_at.is_(None),
            )
            if tenant_id:
                stmt = stmt.where(Document.tenant_id == tenant_id)

            res = await db.execute(stmt)
            db_refs = {ref for ref in res.scalars().all() if ref}

            # 2. Enumerate physical storage objects
            physical_files: set[str] = set()
            if base_dir.exists():
                for root, _, files in os.walk(base_dir):
                    for f in files:
                        full_p = Path(root) / f
                        try:
                            rel_p = str(full_p.relative_to(base_dir)).replace("\\", "/")
                            physical_files.add(rel_p)
                        except ValueError:
                            physical_files.add(f)

            # 3. Detect discrepancies
            missing_files = []
            for ref in db_refs:
                ref_norm = ref.replace("\\", "/").lstrip("/")
                # Check both relative to base_dir and exact existence
                if not (base_dir / ref_norm).exists() and not Path(ref).exists() and ref_norm not in physical_files:
                    missing_files.append(ref_norm)

            orphaned_files = []
            for pf in physical_files:
                if pf not in db_refs and f"/{pf}" not in db_refs:
                    orphaned_files.append(pf)

            duration = time.perf_counter() - start_time

            record.status = StorageAuditStatus.COMPLETED
            record.total_db_records = len(db_refs)
            record.total_storage_files = len(physical_files)
            record.missing_files_count = len(missing_files)
            record.orphaned_files_count = len(orphaned_files)
            record.missing_file_keys = missing_files[:100]  # Store bounded sample
            record.orphaned_file_keys = orphaned_files[:100]
            record.completed_at = datetime.now(UTC)
            record.duration_seconds = round(duration, 2)

            system_tenant_id = UUID("00000000-0000-0000-0000-000000000000")
            audit_entry = build_audit_entry(
                tenant_id=system_tenant_id,
                action=AuditEventCategory.STORAGE_INTEGRITY_AUDITED,
                entity_type="platform_storage_audit",
                entity_id=record.id,
                user_id=user_id,
                new_values_json={
                    "total_db_records": len(db_refs),
                    "total_storage_files": len(physical_files),
                    "missing_files_count": len(missing_files),
                    "orphaned_files_count": len(orphaned_files),
                },
            )
            db.add(audit_entry)
            await db.commit()
            await db.refresh(record)

            logger.info(
                "Storage audit completed in %.2fs: db=%d, storage=%d, missing=%d, orphaned=%d",
                duration,
                len(db_refs),
                len(physical_files),
                len(missing_files),
                len(orphaned_files),
            )
            return record

        except Exception as exc:
            duration = time.perf_counter() - start_time
            record.status = StorageAuditStatus.FAILED
            record.error_message = str(exc)[:1000]
            record.completed_at = datetime.now(UTC)
            record.duration_seconds = round(duration, 2)
            await db.commit()
            await db.refresh(record)
            raise
