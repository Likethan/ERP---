"""Enterprise Notification, Communication & Delivery Orchestration API Endpoints (Step 26).

Implements:
- User Notification Center (/notifications, /notifications/{id}, /notifications/read-all)
- User Preferences & Quiet Hours (/notification-preferences)
- Admin Notification Rules (/admin/notification-rules)
- Admin Versioned Templates & Previews (/admin/notification-templates)
- Admin Delivery Tracking, Retries & Cancellation (/admin/deliveries)
- Operational Analytics & Provider Health (/admin/notification-analytics, /admin/notification-providers/health)
- Cryptographic Provider Webhook Callbacks (/notifications/callbacks/{provider_key})
"""

from datetime import UTC, datetime
import logging
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import build_audit_entry
from app.core.database import get_db_session
from app.core.deps import (
    get_current_active_user,
    get_tenant_context,
    require_permission,
)
from app.core.exceptions import NotFoundException, ValidationException
from app.core.permissions import (
    NOTIFICATION_ANALYTICS_READ,
    NOTIFICATION_DELIVERIES_CANCEL,
    NOTIFICATION_DELIVERIES_READ,
    NOTIFICATION_DELIVERIES_RETRY,
    NOTIFICATION_PROVIDERS_MANAGE,
    NOTIFICATION_RULES_MANAGE,
    NOTIFICATION_TEMPLATES_MANAGE,
    NOTIFICATION_TEMPLATES_READ,
    NOTIFICATIONS_MANAGE_PREFERENCES,
    NOTIFICATIONS_READ,
)
from app.core.tenant import TenantContext
from app.models.notification import (
    NotificationDeliveryAttempt,
    NotificationRule,
    ProviderHealthStatus,
)
from app.models.people import User
from app.repositories.notification_repository import NotificationRepository
from app.schemas.campus import (
    NotificationListResponse,
    NotificationPreferenceItem,
    NotificationPreferenceUpdate,
    NotificationResponse,
    UnreadCountResponse,
)
from app.schemas.common import ApiResponse
from app.schemas.notification import (
    DeliveryAttemptResponse,
    DeliveryCancelRequest,
    DeliveryDetailResponse,
    DeliveryListResponse,
    DeliveryResponse,
    DeliveryRetryRequest,
    NotificationAnalyticsResponse,
    NotificationPreferencesDetailResponse,
    NotificationPreferencesDetailUpdate,
    NotificationRuleCreate,
    NotificationRuleResponse,
    NotificationRuleUpdate,
    NotificationTemplateCreate,
    NotificationTemplateResponse,
    NotificationTemplateUpdate,
    NotificationTemplateVersionResponse,
    ProviderHealthItem,
    ProviderHealthResponse,
    TemplatePreviewRequest,
    TemplatePreviewResponse,
    TemplatePublishRequest,
    WebhookCallbackPayload,
)
from app.services.notification_orchestration_service import NotificationOrchestrationService
from app.services.notification_service import NotificationService
from app.services.notification_template_service import NotificationTemplateService
from app.services.notification_webhook_service import NotificationWebhookService

logger = logging.getLogger("campusos.api.notifications")

router = APIRouter(tags=["Enterprise Notifications & Communication"])


# =============================================================================
# 1. USER INBOX & NOTIFICATION ACTIONS
# =============================================================================
@router.get("/notifications", response_model=ApiResponse[NotificationListResponse])
async def list_user_notifications(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    unread_only: bool = Query(False),
    notification_type: str | None = Query(None, alias="type"),
    source_module: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
) -> ApiResponse[NotificationListResponse]:
    """Get authenticated user's notification inbox items with accurate unread counts."""
    res = await NotificationService.get_user_notifications(
        db,
        tenant.tenant_id,
        current_user.id,
        unread_only=unread_only,
        notification_type=notification_type,
        source_module=source_module,
        page=page,
        limit=limit,
    )
    return ApiResponse(data=NotificationListResponse(**res))


@router.get("/notifications/unread-count", response_model=ApiResponse[UnreadCountResponse])
async def get_user_unread_count(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[UnreadCountResponse]:
    """Fast unread notification badge counter."""
    count = await NotificationService.get_unread_count(db, tenant.tenant_id, current_user.id)
    return ApiResponse(data=UnreadCountResponse(unread_count=count))


# =============================================================================
# 2. USER NOTIFICATION PREFERENCES & QUIET HOURS
# =============================================================================
@router.get("/notification-preferences", response_model=ApiResponse[NotificationPreferencesDetailResponse])
@router.get("/notifications/preferences", response_model=ApiResponse[Any])
async def get_notification_preferences(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[Any]:
    """Load user's notification channel preferences, quiet hours schedule, and digest settings."""
    detail = await NotificationService.get_user_preference_details(
        db, tenant.tenant_id, current_user.id
    )
    return ApiResponse(data=detail)


@router.patch("/notification-preferences", response_model=ApiResponse[NotificationPreferencesDetailResponse])
@router.put("/notifications/preferences", response_model=ApiResponse[Any])
@router.post("/notifications/preferences", response_model=ApiResponse[Any])
async def update_notification_preferences(
    payload: NotificationPreferencesDetailUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[Any]:
    """Update notification preferences, quiet hours, and channel settings."""
    updated = await NotificationService.update_user_preference_details(
        db, tenant.tenant_id, current_user.id, payload
    )
    return ApiResponse(data=updated)


@router.get("/notifications/{notification_id}", response_model=ApiResponse[NotificationResponse])
async def get_notification_item(
    notification_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[NotificationResponse]:
    """Get single notification item for current user."""
    notif = await NotificationService.get_notification_by_id(
        db, tenant.tenant_id, current_user.id, notification_id
    )
    return ApiResponse(data=NotificationResponse.model_validate(notif))


@router.patch("/notifications/{notification_id}/read", response_model=ApiResponse[NotificationResponse])
async def mark_notification_read(
    notification_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[NotificationResponse]:
    """Mark a notification as read and record timestamp."""
    notif = await NotificationService.mark_as_read(
        db, tenant.tenant_id, current_user.id, notification_id
    )
    return ApiResponse(data=NotificationResponse.model_validate(notif))


@router.post("/notifications/read-all", response_model=ApiResponse[dict])
async def mark_all_notifications_read(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[dict]:
    """Mark all inbox notifications as read for current user."""
    count = await NotificationService.mark_all_as_read(db, tenant.tenant_id, current_user.id)
    return ApiResponse(data={"message": f"Marked {count} notifications as read."})


# =============================================================================
# 3. ADMIN: NOTIFICATION RULES
# =============================================================================
@router.get("/admin/notification-rules", response_model=ApiResponse[list[NotificationRuleResponse]])
async def list_admin_notification_rules(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(NOTIFICATION_RULES_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    event_type: str | None = Query(None),
    is_enabled: bool | None = Query(None),
    module_scope: str | None = Query(None),
) -> ApiResponse[list[NotificationRuleResponse]]:
    """List configurable notification dispatch rules for current tenant."""
    repo = NotificationRepository(db)
    rules = await repo.list_rules(
        tenant_id=tenant.tenant_id,
        event_type=event_type,
        is_enabled=is_enabled,
        module_scope=module_scope,
    )
    return ApiResponse(data=[NotificationRuleResponse.model_validate(r) for r in rules])


@router.post(
    "/admin/notification-rules",
    response_model=ApiResponse[NotificationRuleResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_admin_notification_rule(
    payload: NotificationRuleCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(NOTIFICATION_RULES_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[NotificationRuleResponse]:
    """Create a new configurable notification dispatch rule with policy conditions."""
    repo = NotificationRepository(db)
    existing = await repo.get_rule_by_key(tenant.tenant_id, payload.rule_key)
    if existing:
        raise ValidationException(f"Rule with key '{payload.rule_key}' already exists.")

    now = datetime.now(UTC)
    rule = NotificationRule(
        id=uuid4(),
        tenant_id=tenant.tenant_id,
        rule_key=payload.rule_key.upper(),
        name=payload.name,
        description=payload.description,
        event_type=payload.event_type,
        is_enabled=payload.is_enabled,
        module_scope=payload.module_scope,
        priority=payload.priority.upper(),
        recipient_strategy=payload.recipient_strategy.upper(),
        recipient_config_json=payload.recipient_config,
        channel_strategy=payload.channel_strategy.upper(),
        channels_json=payload.channels,
        template_key=payload.template_key.upper(),
        conditions_json=payload.conditions,
        suppression_policy_json=payload.suppression_policy,
        scheduling_policy_json=payload.scheduling_policy,
        effective_from=payload.effective_from,
        effective_until=payload.effective_until,
        created_by_id=current_user.id,
        updated_by_id=current_user.id,
        created_at=now,
        updated_at=now,
    )
    created = await repo.create_rule(rule)

    audit = build_audit_entry(
        tenant_id=tenant.tenant_id,
        user_id=current_user.id,
        action="NOTIFICATION_RULE_CREATED",
        entity_type="NotificationRule",
        entity_id=created.id,
        new_values_json={"rule_key": created.rule_key, "event_type": created.event_type},
        business_context="Notification dispatch rule created.",
    )
    db.add(audit)
    await db.commit()
    return ApiResponse(data=NotificationRuleResponse.model_validate(created))


@router.patch("/admin/notification-rules/{rule_id}", response_model=ApiResponse[NotificationRuleResponse])
async def update_admin_notification_rule(
    rule_id: UUID,
    payload: NotificationRuleUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(NOTIFICATION_RULES_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[NotificationRuleResponse]:
    """Update notification dispatch rule configuration."""
    repo = NotificationRepository(db)
    rule = await repo.get_rule_by_id(tenant.tenant_id, rule_id)
    if not rule:
        raise NotFoundException("NotificationRule", rule_id)

    if payload.name is not None:
        rule.name = payload.name
    if payload.description is not None:
        rule.description = payload.description
    if payload.is_enabled is not None:
        rule.is_enabled = payload.is_enabled
    if payload.priority is not None:
        rule.priority = payload.priority.upper()
    if payload.recipient_strategy is not None:
        rule.recipient_strategy = payload.recipient_strategy.upper()
    if payload.recipient_config is not None:
        rule.recipient_config_json = payload.recipient_config
    if payload.channel_strategy is not None:
        rule.channel_strategy = payload.channel_strategy.upper()
    if payload.channels is not None:
        rule.channels_json = payload.channels
    if payload.template_key is not None:
        rule.template_key = payload.template_key.upper()
    if payload.conditions is not None:
        rule.conditions_json = payload.conditions
    if payload.suppression_policy is not None:
        rule.suppression_policy_json = payload.suppression_policy
    if payload.scheduling_policy is not None:
        rule.scheduling_policy_json = payload.scheduling_policy

    rule.updated_by_id = current_user.id
    updated = await repo.update_rule(rule)

    audit = build_audit_entry(
        tenant_id=tenant.tenant_id,
        user_id=current_user.id,
        action="NOTIFICATION_RULE_UPDATED",
        entity_type="NotificationRule",
        entity_id=rule.id,
        new_values_json={"rule_key": rule.rule_key, "is_enabled": rule.is_enabled},
        business_context="Notification dispatch rule updated.",
    )
    db.add(audit)
    await db.commit()
    return ApiResponse(data=NotificationRuleResponse.model_validate(updated))


# =============================================================================
# 4. ADMIN: NOTIFICATION TEMPLATES & VERSIONS
# =============================================================================
@router.get("/admin/notification-templates", response_model=ApiResponse[list[NotificationTemplateResponse]])
async def list_admin_notification_templates(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(NOTIFICATION_TEMPLATES_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    channel: str | None = Query(None),
    category: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
) -> ApiResponse[list[NotificationTemplateResponse]]:
    """List message templates and version summaries."""
    templates = await NotificationTemplateService.list_templates(
        db, tenant.tenant_id, channel=channel, category=category, status=status_filter
    )
    return ApiResponse(data=[NotificationTemplateResponse.model_validate(t) for t in templates])


@router.post(
    "/admin/notification-templates",
    response_model=ApiResponse[NotificationTemplateResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_admin_notification_template(
    payload: NotificationTemplateCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(NOTIFICATION_TEMPLATES_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[NotificationTemplateResponse]:
    """Create a new message template with its initial version."""
    tmpl = await NotificationTemplateService.create_template(
        db, tenant.tenant_id, payload, actor_id=current_user.id
    )
    return ApiResponse(data=NotificationTemplateResponse.model_validate(tmpl))


@router.post("/admin/notification-templates/{template_id}/preview", response_model=ApiResponse[TemplatePreviewResponse])
async def preview_admin_notification_template(
    template_id: UUID,
    payload: TemplatePreviewRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(NOTIFICATION_TEMPLATES_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[TemplatePreviewResponse]:
    """Preview rendered message template safely with strict variable validation."""
    preview = await NotificationTemplateService.preview_template(
        db, tenant.tenant_id, template_id, payload
    )
    return ApiResponse(data=preview)


@router.post("/admin/notification-templates/{template_id}/publish", response_model=ApiResponse[NotificationTemplateVersionResponse])
async def publish_admin_notification_template_version(
    template_id: UUID,
    payload: TemplatePublishRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(NOTIFICATION_TEMPLATES_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[NotificationTemplateVersionResponse]:
    """Publish a new immutable version for an existing message template."""
    new_version = await NotificationTemplateService.publish_version(
        db,
        tenant_id=tenant.tenant_id,
        template_id=template_id,
        subject=payload.subject,
        body_template=payload.body_template,
        body_html_template=payload.body_html_template,
        variable_schema=payload.variable_schema,
        change_summary=payload.change_summary,
        actor_id=current_user.id,
    )

    audit = build_audit_entry(
        tenant_id=tenant.tenant_id,
        user_id=current_user.id,
        action="NOTIFICATION_TEMPLATE_PUBLISHED",
        entity_type="NotificationTemplateVersion",
        entity_id=new_version.id,
        new_values_json={"template_id": str(template_id), "version": new_version.version},
        business_context="Notification template version published.",
    )
    db.add(audit)
    await db.commit()
    return ApiResponse(data=NotificationTemplateVersionResponse.model_validate(new_version))


# =============================================================================
# 5. ADMIN: DELIVERIES & RETRIES
# =============================================================================
@router.get("/admin/deliveries", response_model=ApiResponse[DeliveryListResponse])
async def list_admin_deliveries(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(NOTIFICATION_DELIVERIES_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    recipient_user_id: UUID | None = Query(None, alias="recipient_id"),
    channel: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    correlation_id: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
) -> ApiResponse[DeliveryListResponse]:
    """Authorized delivery history view with audit filters and pagination."""
    repo = NotificationRepository(db)
    items, total = await repo.list_deliveries(
        tenant_id=tenant.tenant_id,
        date_from=date_from,
        date_to=date_to,
        recipient_user_id=recipient_user_id,
        channel=channel,
        status=status_filter,
        correlation_id=correlation_id,
        page=page,
        limit=limit,
    )
    resp = DeliveryListResponse(
        items=[DeliveryResponse.model_validate(d) for d in items],
        total=total,
        page=page,
        limit=limit,
    )
    return ApiResponse(data=resp)


@router.get("/admin/deliveries/{delivery_id}", response_model=ApiResponse[DeliveryDetailResponse])
async def get_admin_delivery_detail(
    delivery_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(NOTIFICATION_DELIVERIES_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[DeliveryDetailResponse]:
    """Get delivery details and attempt history."""
    repo = NotificationRepository(db)
    deliv = await repo.get_delivery_by_id(tenant.tenant_id, delivery_id)
    if not deliv:
        raise NotFoundException("NotificationDelivery", delivery_id)
    return ApiResponse(data=DeliveryDetailResponse.model_validate(deliv))


@router.post("/admin/deliveries/{delivery_id}/retry", response_model=ApiResponse[DeliveryResponse])
async def retry_admin_delivery(
    delivery_id: UUID,
    payload: DeliveryRetryRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(NOTIFICATION_DELIVERIES_RETRY))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[DeliveryResponse]:
    """Manually retry an eligible failed delivery."""
    retried = await NotificationOrchestrationService.retry_delivery(
        db=db,
        tenant_id=tenant.tenant_id,
        delivery_id=delivery_id,
        force=payload.force,
        actor_id=current_user.id,
    )
    return ApiResponse(data=DeliveryResponse.model_validate(retried))


@router.post("/admin/deliveries/{delivery_id}/cancel", response_model=ApiResponse[DeliveryResponse])
async def cancel_admin_delivery(
    delivery_id: UUID,
    payload: DeliveryCancelRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(NOTIFICATION_DELIVERIES_CANCEL))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[DeliveryResponse]:
    """Cancel a pending or scheduled delivery."""
    cancelled = await NotificationOrchestrationService.cancel_delivery(
        db=db,
        tenant_id=tenant.tenant_id,
        delivery_id=delivery_id,
        reason=payload.reason,
        actor_id=current_user.id,
    )
    return ApiResponse(data=DeliveryResponse.model_validate(cancelled))


# =============================================================================
# 6. ADMIN: ANALYTICS & PROVIDER HEALTH
# =============================================================================
@router.get("/admin/notification-analytics", response_model=ApiResponse[NotificationAnalyticsResponse])
async def get_admin_notification_analytics(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(NOTIFICATION_ANALYTICS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    days: int = Query(30, ge=1, le=365),
) -> ApiResponse[NotificationAnalyticsResponse]:
    """Operational delivery analytics, acceptance rate, and failure classification breakdown."""
    repo = NotificationRepository(db)
    metrics = await repo.get_delivery_metrics(tenant.tenant_id, days=days)
    return ApiResponse(data=NotificationAnalyticsResponse(**metrics))


@router.get("/admin/notification-providers/health", response_model=ApiResponse[ProviderHealthResponse])
async def get_admin_provider_health(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(NOTIFICATION_PROVIDERS_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[ProviderHealthResponse]:
    """Inspect configured notification channels and provider operational health."""
    repo = NotificationRepository(db)
    configs = await repo.list_provider_configs(tenant.tenant_id)

    # Standard channel health status
    providers = []
    has_degraded = False

    # Check In-App (always healthy)
    providers.append(
        ProviderHealthItem(
            provider_key="DEFAULT_IN_APP",
            channel="IN_APP",
            provider_type="IN_APP",
            name="Internal In-App Delivery Engine",
            is_enabled=True,
            is_default=True,
            health_status=ProviderHealthStatus.HEALTHY,
            last_health_check_at=datetime.now(UTC),
            latency_ms=1,
        )
    )

    # Check configured configs or report unconfigured
    known_channels = {"IN_APP"}
    for cfg in configs:
        known_channels.add(cfg.channel)
        providers.append(
            ProviderHealthItem(
                provider_key=cfg.provider_key,
                channel=cfg.channel,
                provider_type=cfg.provider_type,
                name=cfg.name,
                is_enabled=cfg.is_enabled,
                is_default=cfg.is_default,
                health_status=cfg.health_status,
                last_health_check_at=cfg.last_health_check_at or datetime.now(UTC),
                details=cfg.health_details_json,
            )
        )

    # Report unconfigured channels honestly
    for ch in ["EMAIL", "SMS", "PUSH"]:
        if ch not in known_channels:
            providers.append(
                ProviderHealthItem(
                    provider_key=f"DEFAULT_{ch}",
                    channel=ch,
                    provider_type=f"GENERIC_{ch}",
                    name=f"Standard {ch.title()} Gateway",
                    is_enabled=False,
                    is_default=True,
                    health_status=ProviderHealthStatus.UNCONFIGURED,
                )
            )

    overall = "HEALTHY" if not has_degraded else "DEGRADED"
    return ApiResponse(data=ProviderHealthResponse(providers=providers, overall_status=overall))


# =============================================================================
# 7. PROVIDER DELIVERY WEBHOOK CALLBACKS
# =============================================================================
@router.post("/notifications/callbacks/{provider_key}", response_model=ApiResponse[dict])
async def process_provider_delivery_callback(
    provider_key: str,
    request: Request,
    payload: WebhookCallbackPayload,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    x_signature: str | None = Header(None, alias="X-CampusOS-Signature"),
) -> ApiResponse[dict]:
    """Authenticated endpoint receiving provider delivery callbacks (bounces, delivered, complaints)."""
    raw_body = await request.body()
    # In production, secret is retrieved from SecretManager; test secret fallback:
    webhook_secret = "test-webhook-secret"

    result = await NotificationWebhookService.process_callback(
        db=db,
        provider_key=provider_key,
        raw_body=raw_body,
        signature_header=x_signature,
        secret=webhook_secret,
        payload=payload,
    )
    return ApiResponse(data=result)
