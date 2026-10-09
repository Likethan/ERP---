"""CampusOS Enterprise Integration & Interoperability Layer API Router.

Exposes:
- Connector registry, lifecycle operations, and diagnostic test probes
- Provider directory
- Encrypted secrets management
- Outbound webhook subscriptions, delivery tracking, and manual replay
- Bidirectional synchronization specifications and execution telemetry
- Integration health and forensic sanitized telemetry logs
- Inbound webhook receivers with HMAC validation and replay deduplication
"""

from typing import Annotated, Any
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Header,
    Query,
    Request,
    Response,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import (
    get_current_active_user,
    get_current_user,
    require_permission,
    resolve_user_permissions,
)
from app.core.exceptions import NotFoundException, ValidationException
from app.core.tenant import get_optional_tenant_context
from app.integrations.health import IntegrationHealthService
from app.integrations.webhooks import InboundWebhookReceiver
from app.models.integration import (
    ConnectorStatus,
    IntegrationHealth,
    IntegrationWebhookDelivery,
)
from app.models.people import User
from app.schemas.integration import (
    ConnectorCreate,
    ConnectorResponse,
    ConnectorTestResult,
    ConnectorUpdate,
    CredentialCreate,
    CredentialResponse,
    DataMappingCreate,
    DataMappingResponse,
    DataMappingUpdate,
    IntegrationHealthResponse,
    IntegrationLogResponse,
    ProviderResponse,
    SyncConfigCreate,
    SyncConfigResponse,
    SyncConfigUpdate,
    SyncRunResponse,
    WebhookDeliveryResponse,
    WebhookSubscriptionCreate,
    WebhookSubscriptionResponse,
    WebhookSubscriptionUpdate,
)
from app.services.integration_service import IntegrationService

router = APIRouter(prefix="/integrations", tags=["Enterprise Integrations & Interoperability"])


# -----------------------------------------------------------------------------
# 1. PROVIDERS
# -----------------------------------------------------------------------------
@router.get("/providers", response_model=list[ProviderResponse])
async def list_integration_providers(
    current_user: Annotated[User, Depends(require_permission("integrations.read"))],
) -> list[ProviderResponse]:
    """Retrieve all supported external integration driver definitions."""
    return IntegrationService.list_providers()


# -----------------------------------------------------------------------------
# 2. CREDENTIALS
# -----------------------------------------------------------------------------
@router.post("/credentials", response_model=CredentialResponse, status_code=status.HTTP_201_CREATED)
async def create_credential(
    data: CredentialCreate,
    request: Request,
    current_user: Annotated[User, Depends(require_permission("integrations.credentials.manage"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> CredentialResponse:
    """Store encrypted credential vault entry."""
    tenant_ctx = getattr(request.state, "tenant", None)
    tenant_id = tenant_ctx.tenant_id if tenant_ctx else None
    user_roles = {ur.role.name for ur in current_user.roles if ur.role}
    is_super = "SUPER_ADMIN" in user_roles

    return await IntegrationService.create_credential(
        db=db,
        tenant_id=tenant_id,
        data=data,
        user_id=current_user.id,
        is_super_admin=is_super,
    )


@router.get("/credentials", response_model=list[CredentialResponse])
async def list_credentials(
    request: Request,
    current_user: Annotated[User, Depends(require_permission("integrations.credentials.manage"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[CredentialResponse]:
    """List credential references with masked previews (never raw secrets)."""
    tenant_ctx = getattr(request.state, "tenant", None)
    tenant_id = tenant_ctx.tenant_id if tenant_ctx else None
    user_roles = {ur.role.name for ur in current_user.roles if ur.role}
    is_super = "SUPER_ADMIN" in user_roles

    return await IntegrationService.list_credentials(
        db=db,
        tenant_id=tenant_id,
        is_super_admin=is_super,
    )


# -----------------------------------------------------------------------------
# 3. CONNECTORS
# -----------------------------------------------------------------------------
@router.post("/connectors", response_model=ConnectorResponse, status_code=status.HTTP_201_CREATED)
async def create_connector(
    data: ConnectorCreate,
    request: Request,
    current_user: Annotated[User, Depends(require_permission("integrations.connectors.manage"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ConnectorResponse:
    """Register a new external connector."""
    tenant_ctx = getattr(request.state, "tenant", None)
    tenant_id = tenant_ctx.tenant_id if tenant_ctx else None
    user_roles = {ur.role.name for ur in current_user.roles if ur.role}
    is_super = "SUPER_ADMIN" in user_roles

    return await IntegrationService.create_connector(
        db=db,
        tenant_id=tenant_id,
        data=data,
        user_id=current_user.id,
        is_super_admin=is_super,
    )


@router.get("/connectors", response_model=list[ConnectorResponse])
async def list_connectors(
    request: Request,
    current_user: Annotated[User, Depends(require_permission("integrations.connectors.read"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status: str | None = Query(None, description="Filter by status (e.g. ACTIVE, DRAFT)"),
    provider_key: str | None = Query(None, description="Filter by provider key"),
) -> list[ConnectorResponse]:
    """List connectors for the active tenant."""
    tenant_ctx = getattr(request.state, "tenant", None)
    tenant_id = tenant_ctx.tenant_id if tenant_ctx else None
    user_roles = {ur.role.name for ur in current_user.roles if ur.role}
    is_super = "SUPER_ADMIN" in user_roles

    return await IntegrationService.list_connectors(
        db=db,
        tenant_id=tenant_id,
        is_super_admin=is_super,
        status=status,
        provider_key=provider_key,
    )


@router.get("/connectors/{connector_id}", response_model=ConnectorResponse)
async def get_connector(
    connector_id: UUID,
    request: Request,
    current_user: Annotated[User, Depends(require_permission("integrations.connectors.read"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ConnectorResponse:
    """Fetch connector details."""
    tenant_ctx = getattr(request.state, "tenant", None)
    tenant_id = tenant_ctx.tenant_id if tenant_ctx else None
    return await IntegrationService.get_connector(
        db=db,
        tenant_id=tenant_id,
        connector_id=connector_id,
    )


@router.patch("/connectors/{connector_id}", response_model=ConnectorResponse)
async def update_connector(
    connector_id: UUID,
    data: ConnectorUpdate,
    request: Request,
    current_user: Annotated[User, Depends(require_permission("integrations.connectors.manage"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ConnectorResponse:
    """Update connector configuration or allowed domains."""
    tenant_ctx = getattr(request.state, "tenant", None)
    tenant_id = tenant_ctx.tenant_id if tenant_ctx else None
    return await IntegrationService.update_connector(
        db=db,
        tenant_id=tenant_id,
        connector_id=connector_id,
        data=data,
        user_id=current_user.id,
    )


@router.post("/connectors/{connector_id}/activate", response_model=ConnectorResponse)
async def activate_connector(
    connector_id: UUID,
    request: Request,
    current_user: Annotated[User, Depends(require_permission("integrations.connectors.manage"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ConnectorResponse:
    """Transition connector to ACTIVE state."""
    tenant_ctx = getattr(request.state, "tenant", None)
    tenant_id = tenant_ctx.tenant_id if tenant_ctx else None
    return await IntegrationService.transition_status(
        db=db,
        tenant_id=tenant_id,
        connector_id=connector_id,
        target_status=ConnectorStatus.ACTIVE,
        user_id=current_user.id,
    )


@router.post("/connectors/{connector_id}/pause", response_model=ConnectorResponse)
async def pause_connector(
    connector_id: UUID,
    request: Request,
    current_user: Annotated[User, Depends(require_permission("integrations.connectors.manage"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ConnectorResponse:
    """Transition connector to PAUSED state."""
    tenant_ctx = getattr(request.state, "tenant", None)
    tenant_id = tenant_ctx.tenant_id if tenant_ctx else None
    return await IntegrationService.transition_status(
        db=db,
        tenant_id=tenant_id,
        connector_id=connector_id,
        target_status=ConnectorStatus.PAUSED,
        user_id=current_user.id,
    )


@router.post("/connectors/{connector_id}/disable", response_model=ConnectorResponse)
async def disable_connector(
    connector_id: UUID,
    request: Request,
    current_user: Annotated[User, Depends(require_permission("integrations.connectors.manage"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ConnectorResponse:
    """Transition connector to DISABLED state."""
    tenant_ctx = getattr(request.state, "tenant", None)
    tenant_id = tenant_ctx.tenant_id if tenant_ctx else None
    return await IntegrationService.transition_status(
        db=db,
        tenant_id=tenant_id,
        connector_id=connector_id,
        target_status=ConnectorStatus.DISABLED,
        user_id=current_user.id,
    )


@router.post("/connectors/{connector_id}/test", response_model=ConnectorTestResult)
async def test_connector(
    connector_id: UUID,
    request: Request,
    current_user: Annotated[User, Depends(require_permission("integrations.connectors.test"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ConnectorTestResult:
    """Run an active diagnostic ping test on the connector."""
    tenant_ctx = getattr(request.state, "tenant", None)
    tenant_id = tenant_ctx.tenant_id if tenant_ctx else None
    return await IntegrationService.test_connector(
        db=db,
        tenant_id=tenant_id,
        connector_id=connector_id,
        user_id=current_user.id,
        allow_private_networks_for_tests=True,
    )


# -----------------------------------------------------------------------------
# 4. WEBHOOKS
# -----------------------------------------------------------------------------
@router.post("/webhooks", response_model=WebhookSubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook_subscription(
    data: WebhookSubscriptionCreate,
    request: Request,
    current_user: Annotated[User, Depends(require_permission("integrations.webhooks.manage"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> WebhookSubscriptionResponse:
    """Register an outbound webhook subscription."""
    tenant_ctx = getattr(request.state, "tenant", None)
    if not tenant_ctx:
        raise ValidationException("Tenant context required.")
    return await IntegrationService.create_webhook_subscription(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        data=data,
        user_id=current_user.id,
    )


@router.get("/webhooks", response_model=list[WebhookSubscriptionResponse])
async def list_webhook_subscriptions(
    request: Request,
    current_user: Annotated[User, Depends(require_permission("integrations.webhooks.read"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[WebhookSubscriptionResponse]:
    """List webhook subscriptions for active tenant."""
    tenant_ctx = getattr(request.state, "tenant", None)
    if not tenant_ctx:
        raise ValidationException("Tenant context required.")
    return await IntegrationService.list_webhook_subscriptions(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
    )


@router.get("/webhooks/{subscription_id}", response_model=WebhookSubscriptionResponse)
async def get_webhook_subscription(
    subscription_id: UUID,
    request: Request,
    current_user: Annotated[User, Depends(require_permission("integrations.webhooks.read"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> WebhookSubscriptionResponse:
    """Fetch webhook subscription by ID."""
    tenant_ctx = getattr(request.state, "tenant", None)
    if not tenant_ctx:
        raise ValidationException("Tenant context required.")
    return await IntegrationService.get_webhook_subscription(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        subscription_id=subscription_id,
    )


@router.patch("/webhooks/{subscription_id}", response_model=WebhookSubscriptionResponse)
async def update_webhook_subscription(
    subscription_id: UUID,
    data: WebhookSubscriptionUpdate,
    request: Request,
    current_user: Annotated[User, Depends(require_permission("integrations.webhooks.manage"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> WebhookSubscriptionResponse:
    """Update webhook subscription endpoint or events."""
    tenant_ctx = getattr(request.state, "tenant", None)
    if not tenant_ctx:
        raise ValidationException("Tenant context required.")
    return await IntegrationService.update_webhook_subscription(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        subscription_id=subscription_id,
        data=data,
        user_id=current_user.id,
    )


@router.delete("/webhooks/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook_subscription(
    subscription_id: UUID,
    request: Request,
    current_user: Annotated[User, Depends(require_permission("integrations.webhooks.manage"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    """Soft-delete webhook subscription."""
    tenant_ctx = getattr(request.state, "tenant", None)
    if not tenant_ctx:
        raise ValidationException("Tenant context required.")
    await IntegrationService.delete_webhook_subscription(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        subscription_id=subscription_id,
        user_id=current_user.id,
    )


# -----------------------------------------------------------------------------
# 5. DELIVERIES
# -----------------------------------------------------------------------------
@router.get("/deliveries", response_model=list[WebhookDeliveryResponse])
async def list_deliveries(
    request: Request,
    current_user: Annotated[User, Depends(require_permission("integrations.webhooks.read"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status: str | None = Query(None, description="Filter delivery status (e.g. DELIVERED, RETRYING, DEAD_LETTER)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[WebhookDeliveryResponse]:
    """List outbound webhook deliveries."""
    tenant_ctx = getattr(request.state, "tenant", None)
    if not tenant_ctx:
        raise ValidationException("Tenant context required.")
    return await IntegrationService.list_webhook_deliveries(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.get("/deliveries/{delivery_id}", response_model=WebhookDeliveryResponse)
async def get_delivery(
    delivery_id: UUID,
    request: Request,
    current_user: Annotated[User, Depends(require_permission("integrations.webhooks.read"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> WebhookDeliveryResponse:
    """Fetch specific delivery record."""
    tenant_ctx = getattr(request.state, "tenant", None)
    if not tenant_ctx:
        raise ValidationException("Tenant context required.")
    stmt = select(IntegrationWebhookDelivery).where(
        IntegrationWebhookDelivery.id == delivery_id,
        IntegrationWebhookDelivery.tenant_id == tenant_ctx.tenant_id,
    )
    delivery = (await db.execute(stmt)).scalar_one_or_none()
    if not delivery:
        raise NotFoundException("IntegrationWebhookDelivery", delivery_id)
    return delivery


@router.post("/deliveries/{delivery_id}/retry", response_model=WebhookDeliveryResponse)
async def retry_delivery(
    delivery_id: UUID,
    request: Request,
    current_user: Annotated[User, Depends(require_permission("integrations.deliveries.retry"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> WebhookDeliveryResponse:
    """Manually replay a failed or dead-letter webhook delivery."""
    tenant_ctx = getattr(request.state, "tenant", None)
    if not tenant_ctx:
        raise ValidationException("Tenant context required.")
    return await IntegrationService.retry_webhook_delivery(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        delivery_id=delivery_id,
        user_id=current_user.id,
    )


# -----------------------------------------------------------------------------
# 6. DATA MAPPINGS
# -----------------------------------------------------------------------------
@router.post("/mappings", response_model=DataMappingResponse, status_code=status.HTTP_201_CREATED)
async def create_data_mapping(
    data: DataMappingCreate,
    request: Request,
    current_user: Annotated[User, Depends(require_permission("integrations.sync.manage"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> DataMappingResponse:
    """Create allowlisted data transformation mapping."""
    tenant_ctx = getattr(request.state, "tenant", None)
    if not tenant_ctx:
        raise ValidationException("Tenant context required.")
    return await IntegrationService.create_data_mapping(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        data=data,
        user_id=current_user.id,
    )


@router.get("/mappings", response_model=list[DataMappingResponse])
async def list_data_mappings(
    request: Request,
    current_user: Annotated[User, Depends(require_permission("integrations.sync.read"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[DataMappingResponse]:
    """List data mappings for tenant."""
    tenant_ctx = getattr(request.state, "tenant", None)
    if not tenant_ctx:
        raise ValidationException("Tenant context required.")
    return await IntegrationService.list_data_mappings(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
    )


# -----------------------------------------------------------------------------
# 7. SYNCHRONIZATION
# -----------------------------------------------------------------------------
@router.post("/syncs", response_model=SyncConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_sync_config(
    data: SyncConfigCreate,
    request: Request,
    current_user: Annotated[User, Depends(require_permission("integrations.sync.manage"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SyncConfigResponse:
    """Configure dataset synchronization."""
    tenant_ctx = getattr(request.state, "tenant", None)
    if not tenant_ctx:
        raise ValidationException("Tenant context required.")
    return await IntegrationService.create_sync_config(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        data=data,
        user_id=current_user.id,
    )


@router.get("/syncs", response_model=list[SyncConfigResponse])
async def list_sync_configs(
    request: Request,
    current_user: Annotated[User, Depends(require_permission("integrations.sync.read"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[SyncConfigResponse]:
    """List synchronization specifications."""
    tenant_ctx = getattr(request.state, "tenant", None)
    if not tenant_ctx:
        raise ValidationException("Tenant context required.")
    return await IntegrationService.list_sync_configs(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
    )


@router.post("/syncs/{sync_id}/run", response_model=SyncRunResponse)
async def trigger_sync(
    sync_id: UUID,
    request: Request,
    current_user: Annotated[User, Depends(require_permission("integrations.sync.execute"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SyncRunResponse:
    """Trigger manual execution of a synchronization run."""
    tenant_ctx = getattr(request.state, "tenant", None)
    if not tenant_ctx:
        raise ValidationException("Tenant context required.")
    return await IntegrationService.trigger_sync_run(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        sync_config_id=sync_id,
        user_id=current_user.id,
    )


@router.get("/syncs/{sync_id}/runs", response_model=list[SyncRunResponse])
async def list_sync_runs(
    sync_id: UUID,
    request: Request,
    current_user: Annotated[User, Depends(require_permission("integrations.sync.read"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[SyncRunResponse]:
    """List execution history for a synchronization specification."""
    tenant_ctx = getattr(request.state, "tenant", None)
    if not tenant_ctx:
        raise ValidationException("Tenant context required.")
    return await IntegrationService.list_sync_runs(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        sync_config_id=sync_id,
    )


# -----------------------------------------------------------------------------
# 8. HEALTH & LOGS
# -----------------------------------------------------------------------------
@router.get("/health", response_model=list[IntegrationHealthResponse])
async def get_integration_health(
    request: Request,
    current_user: Annotated[User, Depends(require_permission("integrations.health.read"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[IntegrationHealthResponse]:
    """Retrieve connector health telemetry."""
    tenant_ctx = getattr(request.state, "tenant", None)
    tenant_id = tenant_ctx.tenant_id if tenant_ctx else None
    user_roles = {ur.role.name for ur in current_user.roles if ur.role}
    is_super = "SUPER_ADMIN" in user_roles

    conditions = []
    if not (is_super and tenant_id is None):
        conditions.append(IntegrationHealth.tenant_id == tenant_id)

    stmt = select(IntegrationHealth).where(and_(*conditions) if conditions else True)
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.get("/logs", response_model=list[IntegrationLogResponse])
async def list_integration_logs(
    request: Request,
    current_user: Annotated[User, Depends(require_permission("integrations.logs.read"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    connector_id: UUID | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[IntegrationLogResponse]:
    """List sanitized forensic integration logs."""
    tenant_ctx = getattr(request.state, "tenant", None)
    tenant_id = tenant_ctx.tenant_id if tenant_ctx else None
    user_roles = {ur.role.name for ur in current_user.roles if ur.role}
    is_super = "SUPER_ADMIN" in user_roles

    return await IntegrationService.list_integration_logs(
        db=db,
        tenant_id=tenant_id,
        is_super_admin=is_super,
        connector_id=connector_id,
        limit=limit,
        offset=offset,
    )


# -----------------------------------------------------------------------------
# 9. INBOUND WEBHOOK RECEIVER (Authenticated via HMAC)
# -----------------------------------------------------------------------------
@router.post("/webhooks/inbound/{provider_key}/{connector_id}", status_code=status.HTTP_200_OK)
async def receive_inbound_webhook(
    provider_key: str,
    connector_id: UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, Any]:
    """Receive and process inbound webhooks from external systems.

    Authenticates strictly via connector identity, HMAC signature, and replay timestamp.
    """
    body_bytes = await request.body()
    headers_dict = {k.lower(): v for k, v in request.headers.items()}

    return await InboundWebhookReceiver.process_inbound_request(
        db=db,
        provider_key=provider_key,
        connector_id=connector_id,
        raw_body=body_bytes,
        headers=headers_dict,
    )
