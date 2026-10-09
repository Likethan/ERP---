"""Enterprise Administration and Configuration Orchestration Service for CampusOS (Step 23)."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditEventCategory, build_audit_entry
from app.core.cache import tenant_cache
from app.core.exceptions import (
    ConfigurationNotFoundException,
    ConfigurationScopeInvalidException,
)
from app.models.configuration import (
    ConfigurationDefinition,
    ConfigurationScope,
    ConfigurationStatus,
    ConfigurationValue,
)
from app.repositories.configuration_repository import ConfigurationRepository
from app.schemas.configuration import (
    ConfigurationDefinitionCreate,
    ConfigurationValueCreate,
)
from app.services.configuration_validation_service import ConfigurationValidationService
from app.services.configuration_version_service import ConfigurationVersionService


class ConfigurationService:
    """Centralized orchestrator for configuration definitions, overrides, and lifecycle."""

    @classmethod
    async def get_definition(cls, db: AsyncSession, key: str) -> ConfigurationDefinition:
        repo = ConfigurationRepository(db)
        defn = await repo.get_definition_by_key(key)
        if not defn:
            raise ConfigurationNotFoundException(key)
        return defn

    @classmethod
    async def list_definitions(
        cls,
        db: AsyncSession,
        category: str | None = None,
        module: str | None = None,
        is_active: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[ConfigurationDefinition], int]:
        repo = ConfigurationRepository(db)
        return await repo.list_definitions(
            category=category, module=module, is_active=is_active, limit=limit, offset=offset
        )

    @classmethod
    async def create_definition(
        cls,
        db: AsyncSession,
        dto: ConfigurationDefinitionCreate,
        actor_id: UUID | None = None,
    ) -> ConfigurationDefinition:
        repo = ConfigurationRepository(db)

        # Validate default value against validation schema
        dummy_defn = ConfigurationDefinition(
            key=dto.key,
            name=dto.name,
            category=dto.category,
            module=dto.module,
            data_type=dto.data_type,
            default_value=dto.default_value,
            validation_schema=dto.validation_schema,
            allowed_values=dto.allowed_values,
        )
        if dto.default_value is not None:
            ConfigurationValidationService.validate_or_raise(dummy_defn, dto.default_value)

        defn = ConfigurationDefinition(
            key=dto.key,
            name=dto.name,
            description=dto.description,
            category=dto.category,
            module=dto.module,
            data_type=dto.data_type,
            default_value=dto.default_value,
            validation_schema=dto.validation_schema,
            allowed_values=dto.allowed_values,
            sensitivity=dto.sensitivity,
            scope=dto.scope,
            is_editable=dto.is_editable,
            is_restart_required=dto.is_restart_required,
            is_feature_flag=dto.is_feature_flag,
            is_active=dto.is_active,
        )
        return await repo.create_definition(defn)

    @classmethod
    async def set_configuration_value(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        dto: ConfigurationValueCreate,
        actor_id: UUID | None = None,
        actor_email: str | None = None,
    ) -> ConfigurationValue:
        """Create or update a configuration override with strict validation and version tracking."""
        repo = ConfigurationRepository(db)

        # 1. Resolve Definition
        definition: ConfigurationDefinition | None = None
        if dto.configuration_definition_id:
            definition = await repo.get_definition_by_id(dto.configuration_definition_id)
        elif dto.key:
            definition = await repo.get_definition_by_key(dto.key)

        if not definition:
            raise ConfigurationNotFoundException(dto.key or str(dto.configuration_definition_id))

        # 2. Centralized Validation
        ConfigurationValidationService.validate_or_raise(definition, dto.value)

        # 3. Scope validation
        if dto.scope_type == ConfigurationScope.CAMPUS and not dto.campus_id:
            raise ConfigurationScopeInvalidException(
                "Campus ID is mandatory for CAMPUS-scoped configuration."
            )

        # 4. Fetch Existing Value or Instantiate
        existing_val = await repo.get_value(
            definition_id=definition.id,
            tenant_id=tenant_id,
            scope_type=dto.scope_type,
            campus_id=dto.campus_id,
        )

        old_value_payload = None
        if existing_val:
            old_value_payload = existing_val.value
            prev_version = existing_val.version
            existing_val.version += 1
            existing_val.value = dto.value
            existing_val.effective_from = dto.effective_from or datetime.now(UTC)
            existing_val.effective_until = dto.effective_until
            existing_val.updated_by_id = actor_id
            target_val = existing_val
        else:
            prev_version = None
            target_val = ConfigurationValue(
                configuration_definition_id=definition.id,
                tenant_id=tenant_id,
                institution_id=dto.institution_id or tenant_id,
                campus_id=dto.campus_id,
                scope_type=dto.scope_type,
                value=dto.value,
                source=f"{dto.scope_type}_OVERRIDE",
                version=1,
                status=ConfigurationStatus.ACTIVE,
                effective_from=dto.effective_from or datetime.now(UTC),
                effective_until=dto.effective_until,
                created_by_id=actor_id,
                updated_by_id=actor_id,
            )
            db.add(target_val)
            await db.flush()

        # 5. Record Version
        await ConfigurationVersionService.record_version(
            db=db,
            definition=definition,
            value_record=target_val,
            actor_id=actor_id,
            actor_email=actor_email,
            reason=dto.reason,
            previous_version=prev_version,
        )

        # 6. Invalidate Tenant Cache
        await tenant_cache.invalidate_namespace(tenant_id, "config")

        # 7. Audit Log
        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.CONFIGURATION_UPDATED
            if existing_val
            else AuditEventCategory.CONFIGURATION_CREATED,
            entity_type="configuration_value",
            entity_id=target_val.id,
            user_id=actor_id,
            old_values_json={"value": old_value_payload} if old_value_payload is not None else None,
            new_values_json={
                "value": dto.value,
                "version": target_val.version,
                "scope": dto.scope_type,
            },
            business_context=(
                f"Configuration '{definition.key}' updated to version {target_val.version}."
            ),
        )
        db.add(audit)
        await db.flush()

        return target_val

    @classmethod
    async def delete_configuration_value(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        key: str,
        scope_type: ConfigurationScope = ConfigurationScope.TENANT,
        campus_id: UUID | None = None,
        actor_id: UUID | None = None,
    ) -> bool:
        """Remove a configuration override, reverting behavior to the inherited parent level."""
        repo = ConfigurationRepository(db)
        definition = await repo.get_definition_by_key(key)
        if not definition:
            raise ConfigurationNotFoundException(key)

        val_record = await repo.get_value(
            definition_id=definition.id,
            tenant_id=tenant_id,
            scope_type=scope_type,
            campus_id=campus_id,
        )
        if not val_record:
            return False

        await repo.delete_value(val_record.id)

        # Invalidate cache
        await tenant_cache.invalidate_namespace(tenant_id, "config")

        # Audit
        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.CONFIGURATION_DELETED,
            entity_type="configuration_value",
            entity_id=val_record.id,
            user_id=actor_id,
            old_values_json={"value": val_record.value, "scope": scope_type},
            business_context=(
                f"Configuration override for '{key}' deleted, reverted to defaults."
            ),
        )
        db.add(audit)
        await db.flush()

        return True
