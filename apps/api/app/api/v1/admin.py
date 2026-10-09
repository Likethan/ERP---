"""Enterprise Administration, Configuration & Policy Management API Endpoints (Step 23)."""

from math import ceil
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_current_user, get_tenant_context, require_permission
from app.core.permissions import (
    CONFIGURATION_DELETE,
    CONFIGURATION_PREVIEW,
    CONFIGURATION_READ,
    CONFIGURATION_ROLLBACK,
    CONFIGURATION_UPDATE,
    FEATURE_FLAG_MANAGE,
    FEATURE_FLAG_READ,
    MODULE_MANAGE,
    MODULE_READ,
    POLICY_MANAGE,
    POLICY_READ,
    SEQUENCE_MANAGE,
    SEQUENCE_READ,
)
from app.core.tenant import TenantContext
from app.models.configuration import ConfigurationDataType, ConfigurationScope
from app.models.people import User
from app.repositories.configuration_repository import ConfigurationRepository
from app.schemas.common import ApiResponse, PaginatedMeta, PaginatedResponse
from app.schemas.configuration import (
    ConfigurationDefinitionResponse,
    ConfigurationDependencyResponse,
    ConfigurationEffectiveResponse,
    ConfigurationPreviewRequest,
    ConfigurationPreviewResponse,
    ConfigurationRollbackRequest,
    ConfigurationValidateRequest,
    ConfigurationValidateResponse,
    ConfigurationValueCreate,
    ConfigurationValueResponse,
    ConfigurationValueUpdate,
    ConfigurationVersionResponse,
    FeatureFlagCreate,
    FeatureFlagEvaluateRequest,
    FeatureFlagEvaluateResponse,
    FeatureFlagResponse,
    FeatureFlagUpdate,
    ModuleConfigurationResponse,
    ModuleConfigurationUpdate,
    NumberingSequenceCreate,
    NumberingSequenceResponse,
    NumberingSequenceUpdate,
    PolicyCreate,
    PolicyEvaluateRequest,
    PolicyEvaluateResponse,
    PolicyResponse,
    PolicyUpdate,
    SequenceGenerateResponse,
)
from app.services.configuration_preview_service import ConfigurationPreviewService
from app.services.configuration_resolver import ConfigurationResolver
from app.services.configuration_service import ConfigurationService
from app.services.configuration_validation_service import ConfigurationValidationService
from app.services.configuration_version_service import ConfigurationVersionService
from app.services.feature_flag_service import FeatureFlagService
from app.services.module_configuration_service import ModuleConfigurationService
from app.services.policy_service import PolicyService
from app.services.sequence_service import SequenceService

router = APIRouter(prefix="/admin", tags=["Enterprise Administration & Configuration"])


# =============================================================================
# 1. CONFIGURATION SPECIAL ENDPOINTS (MUST PRECEDE /configuration/{key})
# =============================================================================


@router.get(
    "/configuration/effective",
    response_model=ApiResponse[list[ConfigurationEffectiveResponse]],
    summary="Get effective configuration resolving inheritance hierarchy",
)
async def get_effective_configuration(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(CONFIGURATION_READ))],
    module: str | None = Query(None, description="Filter by module"),
    campus_id: UUID | None = Query(None, description="Resolve campus-specific overrides"),
) -> ApiResponse[list[ConfigurationEffectiveResponse]]:
    items = await ConfigurationResolver.list_effective_configs(
        db=db,
        tenant_id=tenant.tenant_id,
        module=module,
        campus_id=campus_id,
    )
    return ApiResponse(data=items)


@router.post(
    "/configuration/validate",
    response_model=ApiResponse[ConfigurationValidateResponse],
    summary="Dry-run validate a configuration value against schema rules",
)
async def validate_configuration(
    payload: ConfigurationValidateRequest,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(CONFIGURATION_READ))],
) -> ApiResponse[ConfigurationValidateResponse]:
    definition = await ConfigurationService.get_definition(db, payload.key)
    valid, errors = ConfigurationValidationService.validate(definition, payload.value)
    return ApiResponse(
        data=ConfigurationValidateResponse(
            valid=valid,
            key=payload.key,
            data_type=ConfigurationDataType(definition.data_type),
            errors=errors,
        )
    )


@router.post(
    "/configuration/preview",
    response_model=ApiResponse[ConfigurationPreviewResponse],
    summary="Preview effective configuration change and impact radius analysis",
)
async def preview_configuration_change(
    payload: ConfigurationPreviewRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(CONFIGURATION_PREVIEW))],
) -> ApiResponse[ConfigurationPreviewResponse]:
    preview = await ConfigurationPreviewService.preview_change(
        db=db,
        tenant_id=tenant.tenant_id,
        request=payload,
    )
    return ApiResponse(data=preview)


@router.get(
    "/configuration/versions",
    response_model=ApiResponse[list[ConfigurationVersionResponse]],
    summary="List historical configuration versions and changes",
)
async def list_configuration_versions(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(CONFIGURATION_READ))],
    key: str | None = Query(None, description="Filter by configuration key"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> ApiResponse[list[ConfigurationVersionResponse]]:
    repo = ConfigurationRepository(db)
    definition_id = None
    if key:
        defn = await repo.get_definition_by_key(key)
        if defn:
            definition_id = defn.id
    versions = await repo.list_versions(
        definition_id=definition_id,
        tenant_id=tenant.tenant_id,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(data=[ConfigurationVersionResponse.model_validate(v) for v in versions])


@router.get(
    "/configuration/versions/{id}",
    response_model=ApiResponse[ConfigurationVersionResponse],
    summary="Get configuration version snapshot detail",
)
async def get_configuration_version_detail(
    id: UUID,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(CONFIGURATION_READ))],
) -> ApiResponse[ConfigurationVersionResponse]:
    repo = ConfigurationRepository(db)
    version = await repo.get_version(id)
    if not version:
        from app.core.exceptions import NotFoundException

        raise NotFoundException("ConfigurationVersion", id)
    return ApiResponse(data=ConfigurationVersionResponse.model_validate(version))


# =============================================================================
# 2. CONFIGURATION CRUD & PARAMETERIZED ROUTES
# =============================================================================


@router.get(
    "/configuration",
    response_model=PaginatedResponse[ConfigurationDefinitionResponse],
    summary="List all configurable system definitions",
)
async def list_configuration_definitions(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(CONFIGURATION_READ))],
    category: str | None = Query(None),
    module: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> PaginatedResponse[ConfigurationDefinitionResponse]:
    offset = (page - 1) * page_size
    items, total = await ConfigurationService.list_definitions(
        db=db,
        category=category,
        module=module,
        limit=page_size,
        offset=offset,
    )
    total_pages = ceil(total / page_size) if total > 0 else 1
    return PaginatedResponse(
        data=[ConfigurationDefinitionResponse.model_validate(i) for i in items],
        pagination=PaginatedMeta(
            page=page,
            page_size=page_size,
            total_records=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
    )


@router.post(
    "/configuration",
    response_model=ApiResponse[ConfigurationValueResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Set or override a configuration parameter for the tenant",
)
async def set_configuration(
    payload: ConfigurationValueCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(CONFIGURATION_UPDATE))],
) -> ApiResponse[ConfigurationValueResponse]:
    val = await ConfigurationService.set_configuration_value(
        db=db,
        tenant_id=tenant.tenant_id,
        dto=payload,
        actor_id=user.id,
        actor_email=user.email,
    )
    return ApiResponse(data=ConfigurationValueResponse.model_validate(val))


@router.get(
    "/configuration/{key}",
    response_model=ApiResponse[ConfigurationEffectiveResponse],
    summary="Get active effective configuration for a specific parameter key",
)
async def get_configuration_by_key(
    key: str,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(CONFIGURATION_READ))],
    campus_id: UUID | None = Query(None),
) -> ApiResponse[ConfigurationEffectiveResponse]:
    eff = await ConfigurationResolver.get_effective_config(
        db=db,
        tenant_id=tenant.tenant_id,
        key=key,
        campus_id=campus_id,
        use_cache=True,
    )
    return ApiResponse(data=eff)


@router.patch(
    "/configuration/{key}",
    response_model=ApiResponse[ConfigurationValueResponse],
    summary="Update an existing configuration parameter value",
)
async def update_configuration_value(
    key: str,
    payload: ConfigurationValueUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(CONFIGURATION_UPDATE))],
    campus_id: UUID | None = Query(None),
) -> ApiResponse[ConfigurationValueResponse]:
    val = await ConfigurationService.set_configuration_value(
        db=db,
        tenant_id=tenant.tenant_id,
        dto=ConfigurationValueCreate(
            key=key,
            value=payload.value,
            campus_id=campus_id,
            reason=payload.reason,
            effective_from=payload.effective_from,
            effective_until=payload.effective_until,
        ),
        actor_id=user.id,
        actor_email=user.email,
    )
    return ApiResponse(data=ConfigurationValueResponse.model_validate(val))


@router.delete(
    "/configuration/{key}",
    response_model=ApiResponse[dict[str, Any]],
    summary="Remove a tenant/campus override, reverting to inherited configuration",
)
async def delete_configuration_override(
    key: str,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(CONFIGURATION_DELETE))],
    campus_id: UUID | None = Query(None),
) -> ApiResponse[dict[str, Any]]:
    scope_type = ConfigurationScope.CAMPUS if campus_id else ConfigurationScope.TENANT
    deleted = await ConfigurationService.delete_configuration_value(
        db=db,
        tenant_id=tenant.tenant_id,
        key=key,
        scope_type=scope_type,
        campus_id=campus_id,
        actor_id=user.id,
    )
    return ApiResponse(data={"deleted": deleted, "key": key, "reverted_to": "INHERITED_PARENT"})


@router.post(
    "/configuration/{key}/rollback",
    response_model=ApiResponse[ConfigurationValueResponse],
    summary="Rollback configuration parameter to a historical snapshot",
)
async def rollback_configuration(
    key: str,
    payload: ConfigurationRollbackRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(CONFIGURATION_ROLLBACK))],
    campus_id: UUID | None = Query(None),
) -> ApiResponse[ConfigurationValueResponse]:
    val = await ConfigurationVersionService.rollback(
        db=db,
        tenant_id=tenant.tenant_id,
        key=key,
        target_version_number=payload.target_version_number,
        target_version_id=payload.target_version_id,
        actor_id=user.id,
        actor_email=user.email,
        reason=payload.reason,
        campus_id=campus_id,
    )
    return ApiResponse(data=ConfigurationValueResponse.model_validate(val))


# =============================================================================
# 3. BUSINESS POLICIES
# =============================================================================


@router.get(
    "/policies",
    response_model=ApiResponse[list[PolicyResponse]],
    summary="List all tenant business policies",
)
async def list_policies(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(POLICY_READ))],
    module: str | None = Query(None),
    status: str | None = Query(None),
) -> ApiResponse[list[PolicyResponse]]:
    policies = await PolicyService.list_policies(
        db=db,
        tenant_id=tenant.tenant_id,
        module=module,
        status=status,
    )
    return ApiResponse(data=[PolicyResponse.model_validate(p) for p in policies])


@router.post(
    "/policies",
    response_model=ApiResponse[PolicyResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new business policy",
)
async def create_policy(
    payload: PolicyCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(POLICY_MANAGE))],
) -> ApiResponse[PolicyResponse]:
    policy = await PolicyService.create_policy(
        db=db,
        tenant_id=tenant.tenant_id,
        dto=payload,
        actor_id=user.id,
    )
    return ApiResponse(data=PolicyResponse.model_validate(policy))


@router.get(
    "/policies/{key}",
    response_model=ApiResponse[PolicyResponse],
    summary="Get business policy details by key",
)
async def get_policy(
    key: str,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(POLICY_READ))],
    campus_id: UUID | None = Query(None),
) -> ApiResponse[PolicyResponse]:
    policy = await PolicyService.get_policy(
        db=db,
        tenant_id=tenant.tenant_id,
        policy_key=key,
        campus_id=campus_id,
    )
    return ApiResponse(data=PolicyResponse.model_validate(policy))


@router.patch(
    "/policies/{key}",
    response_model=ApiResponse[PolicyResponse],
    summary="Update an existing business policy",
)
async def update_policy(
    key: str,
    payload: PolicyUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(POLICY_MANAGE))],
    campus_id: UUID | None = Query(None),
) -> ApiResponse[PolicyResponse]:
    policy = await PolicyService.update_policy(
        db=db,
        tenant_id=tenant.tenant_id,
        policy_key=key,
        dto=payload,
        actor_id=user.id,
        campus_id=campus_id,
    )
    return ApiResponse(data=PolicyResponse.model_validate(policy))


@router.post(
    "/policies/{key}/evaluate",
    response_model=ApiResponse[PolicyEvaluateResponse],
    summary="Evaluate a business policy against input context",
)
async def evaluate_policy(
    key: str,
    payload: PolicyEvaluateRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(POLICY_READ))],
) -> ApiResponse[PolicyEvaluateResponse]:
    result = await PolicyService.evaluate_policy(
        db=db,
        tenant_id=tenant.tenant_id,
        policy_key=key,
        context=payload.context,
        campus_id=payload.campus_id,
    )
    return ApiResponse(data=result)


# =============================================================================
# 4. FEATURE FLAGS
# =============================================================================


@router.get(
    "/features",
    response_model=ApiResponse[list[FeatureFlagResponse]],
    summary="List tenant feature flags",
)
async def list_features(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(FEATURE_FLAG_READ))],
    module: str | None = Query(None),
) -> ApiResponse[list[FeatureFlagResponse]]:
    flags = await FeatureFlagService.list_feature_flags(
        db=db,
        tenant_id=tenant.tenant_id,
        module=module,
    )
    return ApiResponse(data=[FeatureFlagResponse.model_validate(f) for f in flags])


@router.post(
    "/features",
    response_model=ApiResponse[FeatureFlagResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new feature flag",
)
async def create_feature_flag(
    payload: FeatureFlagCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(FEATURE_FLAG_MANAGE))],
) -> ApiResponse[FeatureFlagResponse]:
    flag = await FeatureFlagService.create_feature_flag(
        db=db,
        tenant_id=tenant.tenant_id,
        dto=payload,
        actor_id=user.id,
    )
    return ApiResponse(data=FeatureFlagResponse.model_validate(flag))


@router.get(
    "/features/{key}",
    response_model=ApiResponse[FeatureFlagResponse],
    summary="Get feature flag details by key",
)
async def get_feature_flag(
    key: str,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(FEATURE_FLAG_READ))],
) -> ApiResponse[FeatureFlagResponse]:
    flag = await FeatureFlagService.get_feature_flag(
        db=db,
        tenant_id=tenant.tenant_id,
        key=key,
    )
    return ApiResponse(data=FeatureFlagResponse.model_validate(flag))


@router.patch(
    "/features/{key}",
    response_model=ApiResponse[FeatureFlagResponse],
    summary="Update feature flag state, rollout percentage, or targeting",
)
async def update_feature_flag(
    key: str,
    payload: FeatureFlagUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(FEATURE_FLAG_MANAGE))],
) -> ApiResponse[FeatureFlagResponse]:
    flag = await FeatureFlagService.update_feature_flag(
        db=db,
        tenant_id=tenant.tenant_id,
        key=key,
        dto=payload,
        actor_id=user.id,
    )
    return ApiResponse(data=FeatureFlagResponse.model_validate(flag))


@router.post(
    "/features/{key}/evaluate",
    response_model=ApiResponse[FeatureFlagEvaluateResponse],
    summary="Evaluate if a feature is enabled for given user, roles, and environment",
)
async def evaluate_feature_flag(
    key: str,
    payload: FeatureFlagEvaluateRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[FeatureFlagEvaluateResponse]:
    # Default to caller's identity if payload parameters omitted
    user_id = payload.user_id or user.id
    roles = payload.roles or [ur.role.name for ur in user.roles if ur.role]
    eval_result = await FeatureFlagService.evaluate_feature_flag(
        db=db,
        tenant_id=tenant.tenant_id,
        key=key,
        user_id=user_id,
        roles=roles,
        environment=payload.environment,
    )
    return ApiResponse(data=eval_result)


# =============================================================================
# 5. MODULE CONFIGURATION & ENABLEMENT
# =============================================================================


@router.get(
    "/modules",
    response_model=ApiResponse[list[ModuleConfigurationResponse]],
    summary="List all module activation and maintenance states",
)
async def list_modules(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(MODULE_READ))],
) -> ApiResponse[list[ModuleConfigurationResponse]]:
    modules = await ModuleConfigurationService.list_module_configs(
        db=db,
        tenant_id=tenant.tenant_id,
    )
    return ApiResponse(data=[ModuleConfigurationResponse.model_validate(m) for m in modules])


@router.patch(
    "/modules/{module}",
    response_model=ApiResponse[ModuleConfigurationResponse],
    summary="Toggle module enablement, features, or maintenance mode",
)
async def update_module_configuration(
    module: str,
    payload: ModuleConfigurationUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(MODULE_MANAGE))],
) -> ApiResponse[ModuleConfigurationResponse]:
    cfg = await ModuleConfigurationService.update_module_config(
        db=db,
        tenant_id=tenant.tenant_id,
        module=module,
        dto=payload,
        actor_id=user.id,
    )
    return ApiResponse(data=ModuleConfigurationResponse.model_validate(cfg))


# =============================================================================
# 6. NUMBERING SEQUENCES
# =============================================================================


@router.get(
    "/sequences",
    response_model=ApiResponse[list[NumberingSequenceResponse]],
    summary="List tenant numbering sequences",
)
async def list_sequences(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(SEQUENCE_READ))],
) -> ApiResponse[list[NumberingSequenceResponse]]:
    sequences = await SequenceService.list_sequences(
        db=db,
        tenant_id=tenant.tenant_id,
    )
    return ApiResponse(data=[NumberingSequenceResponse.model_validate(s) for s in sequences])


@router.post(
    "/sequences",
    response_model=ApiResponse[NumberingSequenceResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new numbering sequence pattern",
)
async def create_sequence(
    payload: NumberingSequenceCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(SEQUENCE_MANAGE))],
) -> ApiResponse[NumberingSequenceResponse]:
    seq = await SequenceService.create_sequence(
        db=db,
        tenant_id=tenant.tenant_id,
        dto=payload,
    )
    return ApiResponse(data=NumberingSequenceResponse.model_validate(seq))


@router.get(
    "/sequences/{key}",
    response_model=ApiResponse[NumberingSequenceResponse],
    summary="Get numbering sequence pattern detail by key",
)
async def get_sequence(
    key: str,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(SEQUENCE_READ))],
) -> ApiResponse[NumberingSequenceResponse]:
    seq = await SequenceService.get_sequence(
        db=db,
        tenant_id=tenant.tenant_id,
        sequence_key=key,
    )
    return ApiResponse(data=NumberingSequenceResponse.model_validate(seq))


@router.patch(
    "/sequences/{key}",
    response_model=ApiResponse[NumberingSequenceResponse],
    summary="Update numbering sequence formatting or reset rules",
)
async def update_sequence(
    key: str,
    payload: NumberingSequenceUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(SEQUENCE_MANAGE))],
) -> ApiResponse[NumberingSequenceResponse]:
    seq = await SequenceService.update_sequence(
        db=db,
        tenant_id=tenant.tenant_id,
        sequence_key=key,
        dto=payload,
        actor_id=user.id,
    )
    return ApiResponse(data=NumberingSequenceResponse.model_validate(seq))


@router.post(
    "/sequences/{key}/next",
    response_model=ApiResponse[SequenceGenerateResponse],
    summary="Atomically generate the next sequential identifier",
)
async def generate_next_sequence(
    key: str,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(SEQUENCE_MANAGE))],
) -> ApiResponse[SequenceGenerateResponse]:
    gen_result = await SequenceService.generate_next_sequence_number(
        db=db,
        tenant_id=tenant.tenant_id,
        sequence_key=key,
    )
    return ApiResponse(data=gen_result)


# =============================================================================
# 7. DEPENDENCY REGISTRY
# =============================================================================


@router.get(
    "/dependencies",
    response_model=ApiResponse[list[ConfigurationDependencyResponse]],
    summary="List all registered configuration consumer dependencies",
)
async def list_configuration_dependencies(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(CONFIGURATION_READ))],
    key: str | None = Query(None),
    module: str | None = Query(None),
) -> ApiResponse[list[ConfigurationDependencyResponse]]:
    repo = ConfigurationRepository(db)
    deps = await repo.list_dependencies(key=key, module=module)
    return ApiResponse(data=[ConfigurationDependencyResponse.model_validate(d) for d in deps])
