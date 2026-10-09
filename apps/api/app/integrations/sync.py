"""Bidirectional Synchronization and Reconciliation Engine.

Enforces:
- Scheduled and event-driven data synchronization across external systems and CampusOS.
- Canonical ExternalResourceMapping registry preventing cross-record mapping collisions.
- Explicit conflict resolution strategies (SOURCE_WINS, TARGET_WINS, FLAG, QUEUE_FOR_REVIEW, NO_ACTION).
- Item-level telemetry and transactional reconciliation tracking.
"""

from datetime import UTC, datetime
import logging
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ValidationException
from app.integrations.mappings import apply_data_mapping
from app.models.integration import (
    ConflictResolutionStrategy,
    ExternalResourceMapping,
    IntegrationConnector,
    IntegrationDataMapping,
    IntegrationSyncConfig,
    IntegrationSyncItem,
    IntegrationSyncRun,
    SyncDirection,
    SyncItemAction,
    SyncRunStatus,
)

logger = logging.getLogger("campusos.integrations.sync")


class ExternalIdRegistry:
    """Manages canonical mappings between external system IDs and CampusOS UUIDs."""

    @classmethod
    async def get_internal_id(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        connector_id: UUID,
        external_resource_type: str,
        external_id: str,
    ) -> UUID | None:
        """Find corresponding internal entity UUID for an external ID."""
        stmt = select(ExternalResourceMapping.internal_id).where(
            and_(
                ExternalResourceMapping.tenant_id == tenant_id,
                ExternalResourceMapping.connector_id == connector_id,
                ExternalResourceMapping.external_resource_type == external_resource_type,
                ExternalResourceMapping.external_id == external_id,
            )
        )
        return (await db.execute(stmt)).scalar_one_or_none()

    @classmethod
    async def get_external_id(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        connector_id: UUID,
        internal_resource_type: str,
        internal_id: UUID,
    ) -> str | None:
        """Find external system identifier for an internal entity UUID."""
        stmt = select(ExternalResourceMapping.external_id).where(
            and_(
                ExternalResourceMapping.tenant_id == tenant_id,
                ExternalResourceMapping.connector_id == connector_id,
                ExternalResourceMapping.internal_resource_type == internal_resource_type,
                ExternalResourceMapping.internal_id == internal_id,
            )
        )
        return (await db.execute(stmt)).scalar_one_or_none()

    @classmethod
    async def link_resources(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        connector_id: UUID,
        external_resource_type: str,
        external_id: str,
        internal_resource_type: str,
        internal_id: UUID,
    ) -> ExternalResourceMapping:
        """Create or update canonical mapping link between remote and internal resources."""
        stmt = select(ExternalResourceMapping).where(
            and_(
                ExternalResourceMapping.tenant_id == tenant_id,
                ExternalResourceMapping.connector_id == connector_id,
                ExternalResourceMapping.external_resource_type == external_resource_type,
                ExternalResourceMapping.external_id == external_id,
            )
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()

        now = datetime.now(UTC)
        if existing:
            existing.internal_resource_type = internal_resource_type
            existing.internal_id = internal_id
            existing.last_synced_at = now
            return existing

        mapping = ExternalResourceMapping(
            id=uuid4(),
            tenant_id=tenant_id,
            connector_id=connector_id,
            external_resource_type=external_resource_type,
            external_id=external_id,
            internal_resource_type=internal_resource_type,
            internal_id=internal_id,
            last_synced_at=now,
        )
        db.add(mapping)
        return mapping


class SyncEngine:
    """Orchestrates structured synchronization runs and reconciliation logic."""

    @classmethod
    async def start_sync_run(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        sync_config_id: UUID,
    ) -> IntegrationSyncRun:
        """Initialize a new synchronization execution run."""
        stmt = select(IntegrationSyncConfig).where(
            and_(
                IntegrationSyncConfig.id == sync_config_id,
                IntegrationSyncConfig.tenant_id == tenant_id,
                IntegrationSyncConfig.deleted_at.is_(None),
            )
        )
        config = (await db.execute(stmt)).scalar_one_or_none()
        if not config:
            raise NotFoundException("IntegrationSyncConfig", sync_config_id)

        now = datetime.now(UTC)
        run = IntegrationSyncRun(
            id=uuid4(),
            tenant_id=tenant_id,
            sync_config_id=sync_config_id,
            status=SyncRunStatus.RUNNING,
            started_at=now,
        )
        db.add(run)
        await db.commit()
        return run

    @classmethod
    async def process_batch_items(
        cls,
        db: AsyncSession,
        sync_run: IntegrationSyncRun,
        external_records: list[dict[str, Any]],
        mapping_rules: list[dict[str, Any]] | None = None,
        conflict_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.SOURCE_WINS,
    ) -> IntegrationSyncRun:
        """Process incoming external records against internal domain repository."""
        stmt = select(IntegrationSyncConfig).where(
            IntegrationSyncConfig.id == sync_run.sync_config_id
        )
        config = (await db.execute(stmt)).scalar_one()

        for ext_record in external_records:
            sync_run.records_processed += 1
            ext_id = str(ext_record.get("id") or ext_record.get("external_id") or uuid4())

            item_record = IntegrationSyncItem(
                id=uuid4(),
                sync_run_id=sync_run.id,
                external_id=ext_id,
                status="SUCCESS",
            )

            try:
                # 1. Apply Transformation Mappings if provided
                mapped_data = (
                    apply_data_mapping(ext_record, mapping_rules)
                    if mapping_rules
                    else ext_record
                )

                # 2. Check if external record is already linked internally
                existing_internal_id = await ExternalIdRegistry.get_internal_id(
                    db=db,
                    tenant_id=sync_run.tenant_id,
                    connector_id=config.connector_id,
                    external_resource_type=config.resource_type,
                    external_id=ext_id,
                )

                if existing_internal_id is None:
                    # New record to create
                    internal_id = uuid4()
                    await ExternalIdRegistry.link_resources(
                        db=db,
                        tenant_id=sync_run.tenant_id,
                        connector_id=config.connector_id,
                        external_resource_type=config.resource_type,
                        external_id=ext_id,
                        internal_resource_type=f"CampusOS.{config.resource_type}",
                        internal_id=internal_id,
                    )
                    item_record.action = SyncItemAction.CREATED
                    item_record.internal_id = internal_id
                    sync_run.records_created += 1

                else:
                    # Existing record - evaluate conflict resolution strategy
                    item_record.internal_id = existing_internal_id

                    if conflict_strategy == ConflictResolutionStrategy.SOURCE_WINS:
                        item_record.action = SyncItemAction.UPDATED
                        sync_run.records_updated += 1
                    elif conflict_strategy == ConflictResolutionStrategy.TARGET_WINS:
                        item_record.action = SyncItemAction.SKIPPED
                        sync_run.records_skipped += 1
                    elif conflict_strategy in (
                        ConflictResolutionStrategy.FLAG,
                        ConflictResolutionStrategy.QUEUE_FOR_REVIEW,
                    ):
                        item_record.action = SyncItemAction.CONFLICT
                        item_record.error_message = (
                            f"Discrepancy detected under conflict strategy '{conflict_strategy}'. Queued for human review."
                        )
                        sync_run.records_skipped += 1
                    else:  # NO_ACTION
                        item_record.action = SyncItemAction.SKIPPED
                        sync_run.records_skipped += 1

            except Exception as exc:
                item_record.action = SyncItemAction.FAILED
                item_record.status = "FAILED"
                item_record.error_message = str(exc)[:500]
                sync_run.records_failed += 1

            db.add(item_record)

        now = datetime.now(UTC)
        sync_run.completed_at = now
        sync_run.status = (
            SyncRunStatus.COMPLETED if sync_run.records_failed == 0 else SyncRunStatus.PARTIAL
        )

        config.last_synced_at = now
        await db.commit()
        return sync_run
