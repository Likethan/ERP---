"""Deterministic Effective Configuration Resolver for CampusOS (Step 23)."""

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import tenant_cache
from app.core.exceptions import ConfigurationNotFoundException
from app.models.configuration import (
    ConfigurationDataType,
    ConfigurationScope,
    ConfigurationSensitivity,
    ConfigurationStatus,
)
from app.repositories.configuration_repository import ConfigurationRepository
from app.schemas.configuration import ConfigurationEffectiveResponse


class ConfigurationResolver:
    """Calculates deterministic effective configuration respecting the inheritance hierarchy:

    Campus override
        ↓
    Institution override
        ↓
    Tenant override
        ↓
    Platform default
        ↓
    Definition default
    """

    @classmethod
    async def get_effective_config(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        key: str,
        campus_id: UUID | None = None,
        institution_id: UUID | None = None,
        use_cache: bool = True,
    ) -> ConfigurationEffectiveResponse:
        repo = ConfigurationRepository(db)

        # 1. Check cache first
        cache_key = f"{key}:{campus_id or 'none'}"
        if use_cache:
            cached_data = await tenant_cache.get(tenant_id, "config", cache_key)
            if cached_data is not None:
                return ConfigurationEffectiveResponse(**cached_data)

        # 2. Retrieve Definition
        definition = await repo.get_definition_by_key(key)
        if not definition:
            raise ConfigurationNotFoundException(key)

        # Fetch all candidate values for this definition
        raw_values = await repo.list_raw_values_for_definition(definition.id, tenant_id=tenant_id)
        active_values = [v for v in raw_values if v.status == ConfigurationStatus.ACTIVE]

        effective_value: Any = None
        source_scope: str = "DEFINITION_DEFAULT"
        source_id: UUID | None = None
        source_version: int | None = None
        effective_from = None
        is_override = False

        # Resolution Step 1: Campus Override
        campus_match = None
        if campus_id is not None:
            campus_match = next(
                (
                    v
                    for v in active_values
                    if v.scope_type == ConfigurationScope.CAMPUS and v.campus_id == campus_id
                ),
                None,
            )

        # Resolution Step 2: Institution Override
        institution_match = None
        if institution_id is not None:
            institution_match = next(
                (
                    v
                    for v in active_values
                    if v.scope_type == ConfigurationScope.INSTITUTION
                    and v.institution_id == institution_id
                ),
                None,
            )

        # Resolution Step 3: Tenant Override
        tenant_match = next(
            (
                v
                for v in active_values
                if v.scope_type == ConfigurationScope.TENANT
                and v.tenant_id == tenant_id
                and v.campus_id is None
            ),
            None,
        )

        # Resolution Step 4: Platform Override / Default
        platform_match = next(
            (
                v
                for v in active_values
                if v.scope_type == ConfigurationScope.PLATFORM and v.tenant_id is None
            ),
            None,
        )

        if campus_match:
            effective_value = campus_match.value
            source_scope = ConfigurationScope.CAMPUS
            source_id = campus_match.id
            source_version = campus_match.version
            effective_from = campus_match.effective_from
            is_override = True
        elif institution_match:
            effective_value = institution_match.value
            source_scope = ConfigurationScope.INSTITUTION
            source_id = institution_match.id
            source_version = institution_match.version
            effective_from = institution_match.effective_from
            is_override = True
        elif tenant_match:
            effective_value = tenant_match.value
            source_scope = ConfigurationScope.TENANT
            source_id = tenant_match.id
            source_version = tenant_match.version
            effective_from = tenant_match.effective_from
            is_override = True
        elif platform_match:
            effective_value = platform_match.value
            source_scope = ConfigurationScope.PLATFORM
            source_id = platform_match.id
            source_version = platform_match.version
            effective_from = platform_match.effective_from
            is_override = False
        else:
            effective_value = definition.default_value
            source_scope = "DEFINITION_DEFAULT"
            source_id = definition.id
            source_version = 1
            effective_from = definition.created_at
            is_override = False

        result = ConfigurationEffectiveResponse(
            key=definition.key,
            value=effective_value,
            data_type=ConfigurationDataType(definition.data_type),
            source_scope=source_scope,
            source_id=source_id,
            configuration_version=source_version,
            is_override=is_override,
            effective_from=effective_from,
            sensitivity=ConfigurationSensitivity(definition.sensitivity),
        )

        # Cache resolution result (5 minutes ttl)
        if use_cache:
            await tenant_cache.set(
                tenant_id, "config", cache_key, result.model_dump(), ttl_seconds=300
            )

        return result

    @classmethod
    async def list_effective_configs(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        module: str | None = None,
        campus_id: UUID | None = None,
    ) -> list[ConfigurationEffectiveResponse]:
        """Resolve all effective configurations for a tenant (and optional module/campus)."""
        repo = ConfigurationRepository(db)
        definitions, _ = await repo.list_definitions(module=module, is_active=True, limit=500)

        results = []
        for defn in definitions:
            eff = await cls.get_effective_config(
                db=db,
                tenant_id=tenant_id,
                key=defn.key,
                campus_id=campus_id,
                use_cache=True,
            )
            results.append(eff)
        return results

    @classmethod
    async def get_effective_value(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        key: str,
        default: Any = None,
        campus_id: UUID | None = None,
    ) -> Any:
        """Convenience method for domain services to fetch only the raw effective value."""
        try:
            eff = await cls.get_effective_config(
                db=db,
                tenant_id=tenant_id,
                key=key,
                campus_id=campus_id,
                use_cache=True,
            )
            return eff.value if eff.value is not None else default
        except ConfigurationNotFoundException:
            return default
