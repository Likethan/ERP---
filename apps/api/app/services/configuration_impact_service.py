"""Configuration Dependency & Impact Analysis Service for CampusOS (Step 23)."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.configuration import ConfigurationDependency, DependencyCriticality
from app.repositories.configuration_repository import ConfigurationRepository
from app.schemas.configuration import ImpactedConsumer


class ConfigurationImpactService:
    """Provides dependency mapping and impact radius analysis when modifying configuration."""

    @classmethod
    async def get_impacted_consumers(
        cls,
        db: AsyncSession,
        configuration_key: str,
    ) -> list[ImpactedConsumer]:
        """Fetch all registered module and system consumers dependent on this key."""
        repo = ConfigurationRepository(db)
        deps = await repo.list_dependencies(key=configuration_key)
        return [
            ImpactedConsumer(
                consumer_module=d.consumer_module,
                consumer_component=d.consumer_component,
                impact_description=d.impact_description,
                criticality=DependencyCriticality(d.criticality),
                is_restart_required=d.is_restart_required,
            )
            for d in deps
        ]

    @classmethod
    async def register_dependency(
        cls,
        db: AsyncSession,
        configuration_key: str,
        consumer_module: str,
        consumer_component: str,
        impact_description: str,
        criticality: DependencyCriticality = DependencyCriticality.MEDIUM,
        is_restart_required: bool = False,
    ) -> ConfigurationDependency:
        """Register a consuming component into the dependency registry."""
        repo = ConfigurationRepository(db)
        dep = ConfigurationDependency(
            configuration_key=configuration_key,
            consumer_module=consumer_module,
            consumer_component=consumer_component,
            impact_description=impact_description,
            criticality=criticality,
            is_restart_required=is_restart_required,
        )
        return await repo.create_dependency(dep)
