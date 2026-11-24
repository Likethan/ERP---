"""Configuration Change Preview & Dry-Run Evaluation Service for CampusOS (Step 23)."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConfigurationNotFoundException
from app.repositories.configuration_repository import ConfigurationRepository
from app.schemas.configuration import ConfigurationPreviewRequest, ConfigurationPreviewResponse
from app.services.configuration_impact_service import ConfigurationImpactService
from app.services.configuration_resolver import ConfigurationResolver
from app.services.configuration_validation_service import ConfigurationValidationService


class ConfigurationPreviewService:
    """Computes non-destructive preview and impact analysis of proposed configuration mutations."""

    @classmethod
    async def preview_change(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        request: ConfigurationPreviewRequest,
    ) -> ConfigurationPreviewResponse:
        repo = ConfigurationRepository(db)
        definition = await repo.get_definition_by_key(request.key)
        if not definition:
            raise ConfigurationNotFoundException(request.key)

        # 1. Fetch Current Effective Configuration
        current_eff = await ConfigurationResolver.get_effective_config(
            db=db,
            tenant_id=tenant_id,
            key=request.key,
            campus_id=request.campus_id,
            use_cache=False,
        )

        # 2. Dry-Run Validation
        is_valid, validation_errors = ConfigurationValidationService.validate(
            definition=definition,
            value=request.proposed_value,
        )

        # 3. Calculate Impacted Consumers
        impacted_consumers = await ConfigurationImpactService.get_impacted_consumers(
            db=db,
            configuration_key=request.key,
        )

        restart_required = definition.is_restart_required or any(
            c.is_restart_required for c in impacted_consumers
        )

        return ConfigurationPreviewResponse(
            key=request.key,
            current_value=current_eff.value,
            proposed_value=request.proposed_value,
            validation_status=is_valid,
            validation_errors=validation_errors,
            current_source=current_eff.source_scope,
            target_scope=request.scope_type,
            impacted_consumers=impacted_consumers,
            restart_required=restart_required,
        )
