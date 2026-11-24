"""Enterprise Marketplace, App Integrations & Extensibility Ecosystem REST API (Step 39).

Enforces:
- Strict segregation between Platform Marketplace Administration and Institution-level App Connections
- Tenant isolation: institutions only manage their own integration connections and credentials
- Cryptographic credential protection: raw secrets are vaulted via SecretManager and never returned in APIs
- Step 38 Subscription Entitlement enforcement: max_integrations quotas and module enablement
- Authenticated HMAC inbound webhooks with connector signature verification
"""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import (
    get_current_active_user,
    require_platform_admin,
)
from app.core.exceptions import (
    BadRequestException,
)
from app.models.marketplace import (
    TenantAppInstallation,
)
from app.models.people import User
from app.schemas.marketplace import (
    ConflictResolutionRequest,
    IntegrationDataConflictResponse,
    MarketplaceAppCreateRequest,
    MarketplaceAppResponse,
    MarketplaceAppUpdateRequest,
    MarketplaceSyncRunResponse,
    SyncTriggerRequest,
    TenantAppInstallationCreateRequest,
    TenantAppInstallationResponse,
    TenantAppInstallationUpdateRequest,
    TestConnectivityResponse,
    WebhookIngestResult,
)
from app.services.marketplace_service import MarketplaceService

router = APIRouter(tags=["Enterprise Marketplace & Integrations"])


def _serialize_installation(inst: TenantAppInstallation) -> TenantAppInstallationResponse:
    """Helper to cleanly serialize installation with joined app fields without exposing secrets."""
    app_code = inst.app.code if inst.app else None
    app_name = inst.app.name if inst.app else None
    app_category = inst.app.category if inst.app else None

    # Mask any configuration secrets if present
    safe_config = dict(inst.configuration)
    for sensitive_key in ("api_key", "token", "client_secret", "secret", "password"):
        if sensitive_key in safe_config:
            val = str(safe_config[sensitive_key])
            safe_config[sensitive_key] = f"{val[:3]}...{val[-2:]}" if len(val) > 5 else "****"

    return TenantAppInstallationResponse(
        id=inst.id,
        tenant_id=inst.tenant_id,
        app_id=inst.app_id,
        app_version_id=inst.app_version_id,
        app_code=app_code,
        app_name=app_name,
        app_category=app_category,
        display_name=inst.display_name,
        status=inst.status,
        connection_method=inst.connection_method,
        enabled_capabilities=inst.enabled_capabilities or [],
        authorized_scopes=inst.authorized_scopes or [],
        configuration=safe_config,
        field_mappings=inst.field_mappings or {},
        sync_direction=inst.sync_direction,
        conflict_policy=inst.conflict_policy,
        credential_id=inst.credential_id,
        has_credentials=inst.credential_id is not None,
        health_status=inst.health_status,
        health_details=inst.health_details or {},
        last_health_check_at=inst.last_health_check_at,
        consecutive_failure_count=inst.consecutive_failure_count,
        last_successful_sync_at=inst.last_successful_sync_at,
        last_failure_at=inst.last_failure_at,
        last_error_summary=inst.last_error_summary,
        connected_at=inst.connected_at,
        disconnected_at=inst.disconnected_at,
        created_at=inst.created_at,
        updated_at=inst.updated_at,
    )


# =============================================================================
# 1. PLATFORM SAAS ADMINISTRATION — CATALOG & HEALTH
# =============================================================================


@router.post(
    "/platform/marketplace/apps",
    response_model=MarketplaceAppResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_marketplace_app(
    dto: MarketplaceAppCreateRequest,
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> MarketplaceAppResponse:
    """Register a new integration in the marketplace catalog (Platform Admins only)."""
    app = await MarketplaceService.create_app(db=db, dto=dto, actor_id=_admin.id)
    return MarketplaceAppResponse.model_validate(app)


@router.get(
    "/platform/marketplace/apps",
    response_model=list[MarketplaceAppResponse],
)
async def list_all_marketplace_apps(
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    category: str | None = Query(None),
    status: str | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[MarketplaceAppResponse]:
    """List all marketplace catalog entries across all publication states (Platform Admins only)."""
    apps = await MarketplaceService.list_catalog(
        db=db,
        category=category,
        search=search,
        status=status,
        is_platform_admin=True,
        limit=limit,
        offset=offset,
    )
    return [MarketplaceAppResponse.model_validate(a) for a in apps]


@router.put(
    "/platform/marketplace/apps/{app_id}",
    response_model=MarketplaceAppResponse,
)
async def update_marketplace_app(
    app_id: UUID,
    dto: MarketplaceAppUpdateRequest,
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> MarketplaceAppResponse:
    """Update catalog entry definition and metadata."""
    app = await MarketplaceService.update_app(db=db, app_id=app_id, dto=dto, actor_id=_admin.id)
    return MarketplaceAppResponse.model_validate(app)


@router.post(
    "/platform/marketplace/apps/{app_id}/approve",
    response_model=MarketplaceAppResponse,
)
async def approve_marketplace_app(
    app_id: UUID,
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> MarketplaceAppResponse:
    """Approve a verified marketplace integration."""
    app = await MarketplaceService.approve_app(db=db, app_id=app_id, actor_id=_admin.id)
    return MarketplaceAppResponse.model_validate(app)


@router.post(
    "/platform/marketplace/apps/{app_id}/publish",
    response_model=MarketplaceAppResponse,
)
async def publish_marketplace_app(
    app_id: UUID,
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> MarketplaceAppResponse:
    """Publish an approved integration to all institutions."""
    app = await MarketplaceService.publish_app(db=db, app_id=app_id, actor_id=_admin.id)
    return MarketplaceAppResponse.model_validate(app)


@router.post(
    "/platform/marketplace/apps/{app_id}/deprecate",
    response_model=MarketplaceAppResponse,
)
async def deprecate_marketplace_app(
    app_id: UUID,
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    notice: str = Query("Deprecated in favor of updated connector version"),
) -> MarketplaceAppResponse:
    """Deprecate an app while keeping existing connections operational."""
    app = await MarketplaceService.deprecate_app(db=db, app_id=app_id, deprecation_notice=notice, actor_id=_admin.id)
    return MarketplaceAppResponse.model_validate(app)


@router.post(
    "/platform/marketplace/seed",
    response_model=list[MarketplaceAppResponse],
)
async def seed_default_marketplace_apps(
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[MarketplaceAppResponse]:
    """Seed certified production connectors (Canvas LMS, Moodle, Zoom, Razorpay, Biometric, DigiLocker)."""
    seeded = await MarketplaceService.seed_default_marketplace_apps(db)
    return [MarketplaceAppResponse.model_validate(a) for a in seeded]


@router.get(
    "/platform/marketplace/health",
)
async def get_platform_marketplace_health(
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, Any]:
    """Inspect platform-wide integration health and execution rates."""
    return await MarketplaceService.get_platform_integration_health(db)


# =============================================================================
# 2. INSTITUTION SELF-SERVICE — MARKETPLACE CATALOG DISCOVERY
# =============================================================================


@router.get(
    "/marketplace/apps",
    response_model=list[MarketplaceAppResponse],
)
async def list_marketplace_catalog(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    category: str | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[MarketplaceAppResponse]:
    """Browse approved and published marketplace integrations for the institution."""
    apps = await MarketplaceService.list_catalog(
        db=db,
        category=category,
        search=search,
        is_platform_admin=False,
        limit=limit,
        offset=offset,
    )
    return [MarketplaceAppResponse.model_validate(a) for a in apps]


@router.get(
    "/marketplace/apps/{app_id}",
    response_model=MarketplaceAppResponse,
)
async def get_marketplace_app(
    app_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> MarketplaceAppResponse:
    """Inspect integration specifications, required permissions, and configuration schema."""
    app = await MarketplaceService.get_app_by_id(db, app_id)
    return MarketplaceAppResponse.model_validate(app)


# =============================================================================
# 3. TENANT APP INSTALLATION & CONNECTION MANAGEMENT
# =============================================================================


@router.post(
    "/integrations/connections",
    response_model=TenantAppInstallationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def install_integration_app(
    dto: TenantAppInstallationCreateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TenantAppInstallationResponse:
    """Connect an approved marketplace app. Validates subscription entitlements and quota limits."""
    if not current_user.tenant_id:
        raise BadRequestException("User has no active tenant context.")

    inst = await MarketplaceService.install_app(
        db=db,
        tenant_id=current_user.tenant_id,
        actor_id=current_user.id,
        dto=dto,
    )
    # Refresh to ensure app relationship is loaded
    inst_loaded = await MarketplaceService.get_installation(db, current_user.tenant_id, inst.id)
    return _serialize_installation(inst_loaded)


@router.get(
    "/integrations/connections",
    response_model=list[TenantAppInstallationResponse],
)
async def list_my_connections(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[TenantAppInstallationResponse]:
    """List connected applications for the current institution."""
    if not current_user.tenant_id:
        raise BadRequestException("User has no active tenant context.")

    installations = await MarketplaceService.list_installations(
        db=db,
        tenant_id=current_user.tenant_id,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    return [_serialize_installation(inst) for inst in installations]


@router.get(
    "/integrations/connections/{installation_id}",
    response_model=TenantAppInstallationResponse,
)
async def get_connection_details(
    installation_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TenantAppInstallationResponse:
    """Inspect connection metadata, configuration, and health status (credentials are never exposed)."""
    if not current_user.tenant_id:
        raise BadRequestException("User has no active tenant context.")

    inst = await MarketplaceService.get_installation(db, current_user.tenant_id, installation_id)
    return _serialize_installation(inst)


@router.put(
    "/integrations/connections/{installation_id}",
    response_model=TenantAppInstallationResponse,
)
async def update_connection_configuration(
    installation_id: UUID,
    dto: TenantAppInstallationUpdateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TenantAppInstallationResponse:
    """Update connection parameters, field mappings, or rotate vaulted credentials."""
    if not current_user.tenant_id:
        raise BadRequestException("User has no active tenant context.")

    inst = await MarketplaceService.update_installation_config(
        db=db,
        tenant_id=current_user.tenant_id,
        installation_id=installation_id,
        actor_id=current_user.id,
        dto=dto,
    )
    return _serialize_installation(inst)


@router.post(
    "/integrations/connections/{installation_id}/test",
    response_model=TestConnectivityResponse,
)
async def test_connection_connectivity(
    installation_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TestConnectivityResponse:
    """Execute live connectivity probe against external endpoint."""
    if not current_user.tenant_id:
        raise BadRequestException("User has no active tenant context.")

    return await MarketplaceService.test_connectivity(
        db=db,
        tenant_id=current_user.tenant_id,
        installation_id=installation_id,
    )


@router.post(
    "/integrations/connections/{installation_id}/pause",
    response_model=TenantAppInstallationResponse,
)
async def pause_connection_sync(
    installation_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    reason: str = Query("Paused by administrator"),
) -> TenantAppInstallationResponse:
    """Temporarily pause data synchronization for an integration."""
    if not current_user.tenant_id:
        raise BadRequestException("User has no active tenant context.")

    inst = await MarketplaceService.pause_sync(
        db=db,
        tenant_id=current_user.tenant_id,
        installation_id=installation_id,
        actor_id=current_user.id,
        reason=reason,
    )
    return _serialize_installation(inst)


@router.post(
    "/integrations/connections/{installation_id}/resume",
    response_model=TenantAppInstallationResponse,
)
async def resume_connection_sync(
    installation_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TenantAppInstallationResponse:
    """Resume data synchronization for a paused integration."""
    if not current_user.tenant_id:
        raise BadRequestException("User has no active tenant context.")

    inst = await MarketplaceService.resume_sync(
        db=db,
        tenant_id=current_user.tenant_id,
        installation_id=installation_id,
        actor_id=current_user.id,
    )
    return _serialize_installation(inst)


@router.post(
    "/integrations/connections/{installation_id}/disconnect",
    response_model=TenantAppInstallationResponse,
)
async def disconnect_integration(
    installation_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    reason: str = Query("Disconnected by administrator"),
) -> TenantAppInstallationResponse:
    """Safely disconnect integration and detach vaulted credentials while keeping history."""
    if not current_user.tenant_id:
        raise BadRequestException("User has no active tenant context.")

    inst = await MarketplaceService.disconnect_app(
        db=db,
        tenant_id=current_user.tenant_id,
        installation_id=installation_id,
        actor_id=current_user.id,
        reason=reason,
    )
    return _serialize_installation(inst)


# =============================================================================
# 4. SYNCHRONIZATION ENGINE & EXECUTION TELEMETRY
# =============================================================================


@router.post(
    "/integrations/connections/{installation_id}/sync",
    response_model=MarketplaceSyncRunResponse,
)
async def trigger_connection_sync(
    installation_id: UUID,
    dto: SyncTriggerRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> MarketplaceSyncRunResponse:
    """Manually trigger a sync run for an active connection."""
    if not current_user.tenant_id:
        raise BadRequestException("User has no active tenant context.")

    run = await MarketplaceService.trigger_sync(
        db=db,
        tenant_id=current_user.tenant_id,
        installation_id=installation_id,
        actor_id=current_user.id,
        dto=dto,
    )
    return MarketplaceSyncRunResponse.model_validate(run)


@router.get(
    "/integrations/connections/{installation_id}/sync-runs",
    response_model=list[MarketplaceSyncRunResponse],
)
async def list_connection_sync_runs(
    installation_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[MarketplaceSyncRunResponse]:
    """Retrieve synchronization history, batch processing stats, and error summaries."""
    if not current_user.tenant_id:
        raise BadRequestException("User has no active tenant context.")

    runs = await MarketplaceService.list_sync_runs(
        db=db,
        tenant_id=current_user.tenant_id,
        installation_id=installation_id,
        limit=limit,
        offset=offset,
    )
    return [MarketplaceSyncRunResponse.model_validate(r) for r in runs]


# =============================================================================
# 5. DATA CONFLICT GOVERNANCE
# =============================================================================


@router.get(
    "/integrations/conflicts",
    response_model=list[IntegrationDataConflictResponse],
)
async def list_integration_conflicts(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    installation_id: UUID | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[IntegrationDataConflictResponse]:
    """List open data synchronization discrepancies requiring institutional review."""
    if not current_user.tenant_id:
        raise BadRequestException("User has no active tenant context.")

    conflicts = await MarketplaceService.list_conflicts(
        db=db,
        tenant_id=current_user.tenant_id,
        installation_id=installation_id,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    return [IntegrationDataConflictResponse.model_validate(c) for c in conflicts]


@router.post(
    "/integrations/conflicts/{conflict_id}/resolve",
    response_model=IntegrationDataConflictResponse,
)
async def resolve_integration_conflict(
    conflict_id: UUID,
    dto: ConflictResolutionRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> IntegrationDataConflictResponse:
    """Apply approved resolution policy (CampusOS Authoritative, Provider Authoritative, or Custom Payload)."""
    if not current_user.tenant_id:
        raise BadRequestException("User has no active tenant context.")

    conflict = await MarketplaceService.resolve_conflict(
        db=db,
        tenant_id=current_user.tenant_id,
        conflict_id=conflict_id,
        actor_id=current_user.id,
        dto=dto,
    )
    return IntegrationDataConflictResponse.model_validate(conflict)


# =============================================================================
# 6. INBOUND WEBHOOK GATEWAY (EXTERNAL PROVIDERS)
# =============================================================================


@router.post(
    "/integrations/webhooks/{app_code}/{tenant_id}",
    response_model=WebhookIngestResult,
    status_code=status.HTTP_200_OK,
)
async def receive_provider_webhook(
    app_code: str,
    tenant_id: UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> WebhookIngestResult:
    """Public authenticated endpoint for receiving provider webhooks. Verifies cryptographic signature."""
    raw_body = await request.body()
    headers_dict = dict(request.headers)

    return await MarketplaceService.handle_inbound_webhook(
        db=db,
        app_code=app_code,
        tenant_id=tenant_id,
        payload_bytes=raw_body,
        headers=headers_dict,
    )
