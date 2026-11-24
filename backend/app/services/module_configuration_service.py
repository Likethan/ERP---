"""Module Activation, Maintenance Mode & Capability Enforcement Service for CampusOS (Step 23)."""

from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditEventCategory, build_audit_entry
from app.core.cache import tenant_cache
from app.core.database import get_db_session
from app.core.deps import get_tenant_context
from app.core.exceptions import ModuleDisabledException, ModuleMaintenanceException
from app.core.tenant import TenantContext
from app.models.configuration import ModuleConfiguration
from app.repositories.configuration_repository import ConfigurationRepository
from app.schemas.configuration import ModuleConfigurationUpdate


class ModuleConfigurationService:
    """Manages ERP module activation, feature sets, and maintenance windows per tenant."""

    DEFAULT_MODULES = [
        "ACADEMICS",
        "ATTENDANCE",
        "EXAMINATION",
        "FINANCE",
        "PLACEMENT",
        "CAMPUS",
        "INFRASTRUCTURE",
        "DOCUMENTS",
        "INTELLIGENCE",
        "INTEGRATIONS",
        "API_PLATFORM",
        "IDENTITY",
    ]

    @classmethod
    async def get_module_config(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        module: str,
    ) -> ModuleConfiguration:
        repo = ConfigurationRepository(db)
        mod_upper = module.upper()
        config = await repo.get_module_config(tenant_id, mod_upper)
        if not config:
            # Default to enabled if record hasn't been instantiated yet
            config = ModuleConfiguration(
                tenant_id=tenant_id,
                module=mod_upper,
                is_enabled=True,
                enabled_features=[],
                maintenance_mode=False,
                maintenance_message=None,
                custom_settings={},
            )
            config = await repo.upsert_module_config(config)
        return config

    @classmethod
    async def list_module_configs(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
    ) -> list[ModuleConfiguration]:
        repo = ConfigurationRepository(db)
        existing = {m.module: m for m in await repo.list_module_configs(tenant_id)}

        # Ensure all standard modules exist for tenant
        result = []
        for mod_name in cls.DEFAULT_MODULES:
            if mod_name in existing:
                result.append(existing[mod_name])
            else:
                new_cfg = ModuleConfiguration(
                    tenant_id=tenant_id,
                    module=mod_name,
                    is_enabled=True,
                    enabled_features=[],
                    maintenance_mode=False,
                    maintenance_message=None,
                    custom_settings={},
                )
                await repo.upsert_module_config(new_cfg)
                result.append(new_cfg)

        return result

    @classmethod
    async def update_module_config(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        module: str,
        dto: ModuleConfigurationUpdate,
        actor_id: UUID | None = None,
    ) -> ModuleConfiguration:
        repo = ConfigurationRepository(db)
        mod_upper = module.upper()
        config = await repo.get_module_config(tenant_id, mod_upper)
        if not config:
            config = ModuleConfiguration(
                tenant_id=tenant_id,
                module=mod_upper,
                is_enabled=True,
                enabled_features=[],
                maintenance_mode=False,
                maintenance_message=None,
                custom_settings={},
            )

        old_state = {"is_enabled": config.is_enabled, "maintenance_mode": config.maintenance_mode}

        if dto.is_enabled is not None:
            config.is_enabled = dto.is_enabled
        if dto.enabled_features is not None:
            config.enabled_features = dto.enabled_features
        if dto.maintenance_mode is not None:
            config.maintenance_mode = dto.maintenance_mode
        if dto.maintenance_message is not None:
            config.maintenance_message = dto.maintenance_message
        if dto.custom_settings is not None:
            config.custom_settings = dto.custom_settings

        config.updated_by_id = actor_id
        saved_config = await repo.upsert_module_config(config)

        # Invalidate cache
        await tenant_cache.invalidate_namespace(tenant_id, "modules")

        # Audit
        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.MODULE_UPDATED,
            entity_type="module_configuration",
            entity_id=saved_config.id,
            user_id=actor_id,
            old_values_json=old_state,
            new_values_json={
                "is_enabled": config.is_enabled,
                "maintenance_mode": config.maintenance_mode,
            },
            business_context=f"Module '{mod_upper}' configuration updated.",
        )
        db.add(audit)
        await db.flush()

        return saved_config

    @classmethod
    async def verify_module_accessible(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        module: str,
    ) -> None:
        """Verify module is enabled and not in maintenance mode. Raises if inactive."""
        config = await cls.get_module_config(db, tenant_id, module)
        if not config.is_enabled:
            raise ModuleDisabledException(module.upper())
        if config.maintenance_mode:
            raise ModuleMaintenanceException(module.upper(), config.maintenance_message)


def require_module_enabled(module_name: str) -> Callable:
    """FastAPI Dependency factory enforcing module availability for tenant."""

    async def _module_guard(
        tenant: Annotated[TenantContext, Depends(get_tenant_context)],
        db: Annotated[AsyncSession, Depends(get_db_session)],
    ) -> None:
        await ModuleConfigurationService.verify_module_accessible(
            db=db,
            tenant_id=tenant.tenant_id,
            module=module_name,
        )

    return _module_guard
