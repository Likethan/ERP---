"""Configuration Versioning and Safe Rollback Service for CampusOS (Step 23)."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditEventCategory, build_audit_entry
from app.core.cache import tenant_cache
from app.core.exceptions import (
    ConfigurationNotFoundException,
    ConfigurationRollbackNotAllowedException,
)
from app.models.configuration import (
    ConfigurationDefinition,
    ConfigurationStatus,
    ConfigurationValue,
    ConfigurationVersion,
)
from app.repositories.configuration_repository import ConfigurationRepository
from app.services.configuration_validation_service import ConfigurationValidationService


class ConfigurationVersionService:
    """Manages historical configuration snapshots and non-destructive rollbacks."""

    @classmethod
    async def record_version(
        cls,
        db: AsyncSession,
        definition: ConfigurationDefinition,
        value_record: ConfigurationValue,
        actor_id: UUID | None = None,
        actor_email: str | None = None,
        reason: str | None = None,
        previous_version: int | None = None,
        rollback_reference: UUID | None = None,
    ) -> ConfigurationVersion:
        repo = ConfigurationRepository(db)

        version = ConfigurationVersion(
            tenant_id=value_record.tenant_id,
            configuration_definition_id=definition.id,
            configuration_value_id=value_record.id,
            version_number=value_record.version,
            previous_version=previous_version,
            value=value_record.value,
            change_summary=reason or f"Updated {definition.key} to version {value_record.version}",
            changed_fields=[definition.key],
            actor_id=actor_id,
            actor_email=actor_email,
            reason=reason,
            status=value_record.status,
            effective_from=value_record.effective_from,
            rollback_reference=rollback_reference,
        )
        return await repo.create_version(version)

    @classmethod
    async def rollback(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        key: str,
        target_version_number: int | None = None,
        target_version_id: UUID | None = None,
        actor_id: UUID | None = None,
        actor_email: str | None = None,
        reason: str = "Administrative rollback",
        campus_id: UUID | None = None,
    ) -> ConfigurationValue:
        repo = ConfigurationRepository(db)

        # 1. Locate Definition
        definition = await repo.get_definition_by_key(key)
        if not definition:
            raise ConfigurationNotFoundException(key)

        # 2. Locate Target Historical Version
        target_version: ConfigurationVersion | None = None
        if target_version_id is not None:
            target_version = await repo.get_version(target_version_id)
        elif target_version_number is not None:
            target_version = await repo.get_version_by_number(
                definition_id=definition.id,
                version_number=target_version_number,
                tenant_id=tenant_id,
            )

        if not target_version:
            raise ConfigurationRollbackNotAllowedException(
                f"Historical version for '{key}' could not be found to restore."
            )

        # 3. Locate Active Value Record to Rollback
        scope_type = "CAMPUS" if campus_id else "TENANT"
        val_record = await repo.get_value(
            definition_id=definition.id,
            tenant_id=tenant_id,
            scope_type=scope_type,
            campus_id=campus_id,
        )
        if not val_record:
            raise ConfigurationRollbackNotAllowedException(
                f"No active configuration override exists to rollback for '{key}'."
            )

        # 4. Validate Restored Value Against Current Schema
        ConfigurationValidationService.validate_or_raise(definition, target_version.value)

        # 5. Non-Destructive Version Increment
        old_val = val_record.value
        prev_version_num = val_record.version
        new_version_num = prev_version_num + 1

        val_record.value = target_version.value
        val_record.version = new_version_num
        val_record.status = ConfigurationStatus.ACTIVE
        val_record.effective_from = datetime.now(UTC)
        val_record.updated_by_id = actor_id

        # 6. Record New Version Snapshot With Rollback Reference
        await cls.record_version(
            db=db,
            definition=definition,
            value_record=val_record,
            actor_id=actor_id,
            actor_email=actor_email,
            reason=f"Rollback to version {target_version.version_number}: {reason}",
            previous_version=prev_version_num,
            rollback_reference=target_version.id,
        )

        # 7. Invalidate Tenant Cache
        await tenant_cache.invalidate_namespace(tenant_id, "config")

        # 8. Forensic Audit Log Entry
        audit_log = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.CONFIGURATION_ROLLEDBACK,
            entity_type="configuration_value",
            entity_id=val_record.id,
            user_id=actor_id,
            old_values_json={"version": prev_version_num, "value": old_val},
            new_values_json={
                "version": new_version_num,
                "value": target_version.value,
                "restored_from": str(target_version.id),
            },
            business_context=(
                f"Configuration '{key}' rolled back to version {target_version.version_number}."
            ),
        )
        db.add(audit_log)
        await db.flush()

        return val_record
