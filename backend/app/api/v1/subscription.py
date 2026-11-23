"""Enterprise Customer Success, Subscription Lifecycle & SaaS Entitlements REST API Router (Step 38).

Enforces:
- Strict segregation between Platform SaaS Administration and Institution-level ERP Administration
- Tenant isolation: institutions can only view their own subscription, entitlements, and invoices
- PBAC validation: institutions can NEVER modify pricing, self-grant entitlements, or bypass limits
- Cryptographic payment webhook processing and audit trails
"""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db_session
from app.core.deps import (
    get_current_active_user,
    require_platform_admin,
)
from app.core.exceptions import (
    BadRequestException,
)
from app.models.core import Institution
from app.models.people import User
from app.models.subscription import (
    CustomerSuccessHealthSnapshot,
    SubscriptionInvoice,
    TenantSubscription,
)
from app.schemas.subscription import (
    CustomerSuccessHealthResponse,
    CustomerSuccessNoteCreateRequest,
    CustomerSuccessNoteResponse,
    CustomerSuccessTenantSummaryResponse,
    DowngradeImpactPreviewResponse,
    EffectiveEntitlementsResponse,
    EntitlementOverrideCreateRequest,
    EntitlementOverrideResponse,
    SubscriptionChangeRequestCreate,
    SubscriptionChangeRequestResponse,
    SubscriptionInvoiceResponse,
    SubscriptionPlanCreateRequest,
    SubscriptionPlanResponse,
    SubscriptionPlanUpdateRequest,
    SubscriptionQuotaStatusResponse,
    SubscriptionUsageEventResponse,
    SubscriptionUsageRecordRequest,
    SubscriptionWebhookPayload,
    TenantSubscriptionCreateRequest,
    TenantSubscriptionResponse,
    TenantSubscriptionTransitionRequest,
)
from app.services.subscription_service import SubscriptionService

router = APIRouter(tags=["Enterprise Subscriptions & Customer Success"])


# =============================================================================
# 1. PLATFORM SAAS ADMINISTRATION — PLANS
# =============================================================================


@router.post(
    "/platform/plans",
    response_model=SubscriptionPlanResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_subscription_plan(
    dto: SubscriptionPlanCreateRequest,
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SubscriptionPlanResponse:
    """Create a new commercial SaaS packaging plan tier (Platform Admins only)."""
    plan = await SubscriptionService.create_plan(db=db, dto=dto, actor_id=_admin.id)
    return SubscriptionPlanResponse.model_validate(plan)


@router.get(
    "/platform/plans",
    response_model=list[SubscriptionPlanResponse],
)
async def list_subscription_plans(
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[SubscriptionPlanResponse]:
    """List all configured subscription plans across the SaaS platform."""
    plans = await SubscriptionService.list_plans(
        db=db, status=status_filter, limit=limit, offset=offset
    )
    return [SubscriptionPlanResponse.model_validate(p) for p in plans]


@router.post(
    "/platform/plans/seed-defaults",
    response_model=list[SubscriptionPlanResponse],
)
async def seed_default_plans(
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[SubscriptionPlanResponse]:
    """Seed standard packaging plans (Starter, Professional, Enterprise) if uninitialized."""
    seeded = await SubscriptionService.seed_default_plans(db)
    return [SubscriptionPlanResponse.model_validate(p) for p in seeded]


@router.get(
    "/platform/plans/{plan_id}",
    response_model=SubscriptionPlanResponse,
)
async def get_subscription_plan(
    plan_id: UUID,
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SubscriptionPlanResponse:
    """Inspect subscription plan details by ID."""
    plan = await SubscriptionService.get_plan(db, plan_id)
    return SubscriptionPlanResponse.model_validate(plan)


@router.put(
    "/platform/plans/{plan_id}",
    response_model=SubscriptionPlanResponse,
)
async def update_subscription_plan(
    plan_id: UUID,
    dto: SubscriptionPlanUpdateRequest,
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SubscriptionPlanResponse:
    """Update a plan definition, incrementing version to preserve historical traceability."""
    plan = await SubscriptionService.update_plan(
        db=db, plan_id=plan_id, dto=dto, actor_id=_admin.id
    )
    return SubscriptionPlanResponse.model_validate(plan)


@router.post(
    "/platform/plans/{plan_id}/retire",
    response_model=SubscriptionPlanResponse,
)
async def retire_subscription_plan(
    plan_id: UUID,
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SubscriptionPlanResponse:
    """Retire a plan, preventing new signups while preserving active subscribers."""
    plan = await SubscriptionService.retire_plan(db=db, plan_id=plan_id, actor_id=_admin.id)
    return SubscriptionPlanResponse.model_validate(plan)


# =============================================================================
# 2. PLATFORM SAAS ADMINISTRATION — TENANT SUBSCRIPTIONS
# =============================================================================


@router.post(
    "/platform/subscriptions",
    response_model=TenantSubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_tenant_subscription(
    dto: TenantSubscriptionCreateRequest,
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TenantSubscriptionResponse:
    """Initialize an institutional commercial subscription and freeze plan snapshot."""
    sub = await SubscriptionService.create_subscription(
        db=db,
        tenant_id=dto.tenant_id,
        plan_id=dto.plan_id,
        billing_interval=dto.billing_interval,
        is_trial=dto.is_trial,
        custom_unit_price=dto.custom_unit_price,
        payment_method_id=dto.payment_method_id,
        actor_id=_admin.id,
        actor_email=_admin.email,
    )
    return TenantSubscriptionResponse.model_validate(sub)


@router.get(
    "/platform/subscriptions",
    response_model=list[TenantSubscriptionResponse],
)
async def list_tenant_subscriptions(
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[TenantSubscriptionResponse]:
    """Inspect all institutional subscriptions across the SaaS platform."""
    stmt = (
        select(TenantSubscription)
        .options(selectinload(TenantSubscription.plan))
        .order_by(desc(TenantSubscription.created_at))
        .offset(offset)
        .limit(limit)
    )
    if status_filter:
        stmt = stmt.where(TenantSubscription.status == status_filter.upper())
    res = await db.execute(stmt)
    return [TenantSubscriptionResponse.model_validate(s) for s in res.scalars().all()]


@router.get(
    "/platform/subscriptions/{tenant_id}",
    response_model=TenantSubscriptionResponse,
)
async def get_tenant_subscription(
    tenant_id: UUID,
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TenantSubscriptionResponse:
    """Fetch active subscription and frozen snapshot for a specific tenant."""
    sub = await SubscriptionService.get_active_subscription(db, tenant_id)
    return TenantSubscriptionResponse.model_validate(sub)


@router.post(
    "/platform/subscriptions/{tenant_id}/transition",
    response_model=TenantSubscriptionResponse,
)
async def transition_subscription_status(
    tenant_id: UUID,
    dto: TenantSubscriptionTransitionRequest,
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TenantSubscriptionResponse:
    """Execute authoritative subscription state machine transition."""
    sub = await SubscriptionService.transition_subscription_status(
        db=db,
        tenant_id=tenant_id,
        target_status=dto.target_status,
        reason=dto.reason,
        actor_id=_admin.id,
        actor_email=_admin.email,
        metadata_json=dto.metadata_json,
    )
    return TenantSubscriptionResponse.model_validate(sub)


@router.post(
    "/platform/subscriptions/{tenant_id}/renew",
    response_model=TenantSubscriptionResponse,
)
async def renew_tenant_subscription(
    tenant_id: UUID,
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TenantSubscriptionResponse:
    """Manually advance subscription period and generate renewal invoice."""
    sub = await SubscriptionService.renew_subscription(
        db=db,
        tenant_id=tenant_id,
        actor_id=_admin.id,
        actor_email=_admin.email,
    )
    return TenantSubscriptionResponse.model_validate(sub)


@router.post(
    "/platform/subscriptions/{tenant_id}/overrides",
    response_model=EntitlementOverrideResponse,
    status_code=status.HTTP_201_CREATED,
)
async def grant_entitlement_override(
    tenant_id: UUID,
    dto: EntitlementOverrideCreateRequest,
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> EntitlementOverrideResponse:
    """Authorize a time-limited capability or quota override for a tenant."""
    ov = await SubscriptionService.create_override(
        db=db,
        tenant_id=tenant_id,
        dto=dto,
        actor_id=_admin.id,
    )
    return EntitlementOverrideResponse.model_validate(ov)


@router.delete(
    "/platform/subscriptions/{tenant_id}/overrides/{override_id}",
    response_model=EntitlementOverrideResponse,
)
async def revoke_entitlement_override(
    tenant_id: UUID,
    override_id: UUID,
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> EntitlementOverrideResponse:
    """Revoke an active entitlement override before scheduled expiration."""
    ov = await SubscriptionService.revoke_override(
        db=db,
        tenant_id=tenant_id,
        override_id=override_id,
        actor_id=_admin.id,
    )
    return EntitlementOverrideResponse.model_validate(ov)


# =============================================================================
# 3. PLATFORM SAAS ADMINISTRATION — CUSTOMER SUCCESS
# =============================================================================


@router.get(
    "/platform/customer-success/summary",
    response_model=list[CustomerSuccessTenantSummaryResponse],
)
async def get_customer_success_summary(
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[CustomerSuccessTenantSummaryResponse]:
    """Overview of all institutional accounts, renewal horizons, and telemetry health indices."""
    t_stmt = select(Institution).order_by(Institution.legal_name.asc()).offset(offset).limit(limit)
    t_res = await db.execute(t_stmt)
    institutions = list(t_res.scalars().all())

    summaries = []
    for inst in institutions:
        sub = await SubscriptionService.get_active_subscription(db, inst.id)
        health = await SubscriptionService.recalculate_health(db, inst.id)

        signals = health.signals_json
        requires_attention = health.health_score < 65 or signals.get("days_until_renewal", 999) <= 30

        if status_filter and health.health_status != status_filter.upper():
            continue

        summaries.append(
            CustomerSuccessTenantSummaryResponse(
                tenant_id=inst.id,
                institution_code=inst.code,
                institution_name=inst.legal_name,
                plan_name=sub.plan.name if sub.plan else "Standard",
                subscription_status=sub.status,
                current_period_end=sub.current_period_end,
                days_until_renewal=signals.get("days_until_renewal", 0),
                health_score=health.health_score,
                health_status=health.health_status,
                open_critical_tickets=signals.get("open_critical_tickets", 0),
                utilization_pct=float(signals.get("avg_utilization_pct", 0.0)),
                adoption_pct=float(health.adoption_score),
                requires_attention=requires_attention,
            )
        )
    return summaries


@router.get(
    "/platform/customer-success/tenants/{tenant_id}/health",
    response_model=CustomerSuccessHealthResponse,
)
async def get_tenant_health(
    tenant_id: UUID,
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> CustomerSuccessHealthResponse:
    """Inspect latest composite health snapshot and operational telemetry."""
    stmt = (
        select(CustomerSuccessHealthSnapshot)
        .where(CustomerSuccessHealthSnapshot.tenant_id == tenant_id)
        .order_by(desc(CustomerSuccessHealthSnapshot.calculated_at))
    )
    res = await db.execute(stmt)
    snapshot = res.scalar_one_or_none()
    if not snapshot:
        snapshot = await SubscriptionService.recalculate_health(db, tenant_id)
    return CustomerSuccessHealthResponse.model_validate(snapshot)


@router.post(
    "/platform/customer-success/tenants/{tenant_id}/health/recalculate",
    response_model=CustomerSuccessHealthResponse,
)
async def recalculate_tenant_health(
    tenant_id: UUID,
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> CustomerSuccessHealthResponse:
    """Force an immediate recomputation of tenant customer success health score."""
    snapshot = await SubscriptionService.recalculate_health(db, tenant_id)
    return CustomerSuccessHealthResponse.model_validate(snapshot)


@router.get(
    "/platform/customer-success/tenants/{tenant_id}/notes",
    response_model=list[CustomerSuccessNoteResponse],
)
async def list_customer_notes(
    tenant_id: UUID,
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[CustomerSuccessNoteResponse]:
    """Fetch internal platform customer success notes (strictly hidden from tenant users)."""
    notes = await SubscriptionService.list_customer_notes(
        db=db, tenant_id=tenant_id, limit=limit, offset=offset
    )
    return [CustomerSuccessNoteResponse.model_validate(n) for n in notes]


@router.post(
    "/platform/customer-success/tenants/{tenant_id}/notes",
    response_model=CustomerSuccessNoteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_customer_note(
    tenant_id: UUID,
    dto: CustomerSuccessNoteCreateRequest,
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> CustomerSuccessNoteResponse:
    """Record a platform-internal customer success log entry."""
    note = await SubscriptionService.add_customer_note(
        db=db,
        tenant_id=tenant_id,
        author_id=_admin.id,
        author_email=_admin.email,
        note_type=dto.note_type,
        content=dto.content,
        is_pinned=dto.is_pinned,
    )
    return CustomerSuccessNoteResponse.model_validate(note)


# =============================================================================
# 4. INSTITUTION SELF-SERVICE (TENANT ADMINS)
# =============================================================================


@router.get(
    "/subscriptions/my",
    response_model=TenantSubscriptionResponse,
)
async def get_my_subscription(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TenantSubscriptionResponse:
    """View active subscription, renewal date, and plan details for the authenticated tenant."""
    if not current_user.tenant_id:
        raise BadRequestException("User has no active tenant context.")
    sub = await SubscriptionService.get_active_subscription(db, current_user.tenant_id)
    return TenantSubscriptionResponse.model_validate(sub)


@router.get(
    "/subscriptions/my/entitlements",
    response_model=EffectiveEntitlementsResponse,
)
async def get_my_effective_entitlements(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> EffectiveEntitlementsResponse:
    """Inspect effective module gates, feature capabilities, and resource allowances."""
    if not current_user.tenant_id:
        raise BadRequestException("User has no active tenant context.")
    ent = await SubscriptionService.get_effective_entitlements(db, current_user.tenant_id)
    return EffectiveEntitlementsResponse.model_validate(ent)


@router.get(
    "/subscriptions/my/quotas",
    response_model=list[SubscriptionQuotaStatusResponse],
)
async def get_my_quota_status(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[SubscriptionQuotaStatusResponse]:
    """Inspect resource usage, soft/hard limits, and remaining capacity."""
    if not current_user.tenant_id:
        raise BadRequestException("User has no active tenant context.")
    quotas = await SubscriptionService.get_quota_status(db, current_user.tenant_id)
    return [SubscriptionQuotaStatusResponse.model_validate(q) for q in quotas]


@router.get(
    "/subscriptions/my/invoices",
    response_model=list[SubscriptionInvoiceResponse],
)
async def list_my_invoices(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[SubscriptionInvoiceResponse]:
    """Retrieve billing history and downloadable SaaS subscription invoices."""
    if not current_user.tenant_id:
        raise BadRequestException("User has no active tenant context.")
    stmt = (
        select(SubscriptionInvoice)
        .where(SubscriptionInvoice.tenant_id == current_user.tenant_id)
        .order_by(desc(SubscriptionInvoice.billing_period_start))
        .offset(offset)
        .limit(limit)
    )
    res = await db.execute(stmt)
    return [SubscriptionInvoiceResponse.model_validate(i) for i in res.scalars().all()]


@router.post(
    "/subscriptions/my/preview-downgrade",
    response_model=DowngradeImpactPreviewResponse,
)
async def preview_downgrade_impact(
    target_plan_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> DowngradeImpactPreviewResponse:
    """Pre-flight capacity impact assessment for plan downgrade (non-destructive check)."""
    if not current_user.tenant_id:
        raise BadRequestException("User has no active tenant context.")
    preview = await SubscriptionService.preview_downgrade(
        db=db, tenant_id=current_user.tenant_id, target_plan_id=target_plan_id
    )
    return DowngradeImpactPreviewResponse.model_validate(preview)


@router.post(
    "/subscriptions/my/change-request",
    response_model=SubscriptionChangeRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_plan_change_request(
    dto: SubscriptionChangeRequestCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SubscriptionChangeRequestResponse:
    """Submit a formal plan upgrade or downgrade request for administrative review."""
    if not current_user.tenant_id:
        raise BadRequestException("User has no active tenant context.")
    req = await SubscriptionService.request_plan_change(
        db=db,
        tenant_id=current_user.tenant_id,
        target_plan_id=dto.target_plan_id,
        target_billing_interval=dto.target_billing_interval,
        effective_type=dto.effective_type,
        actor_id=current_user.id,
    )
    return SubscriptionChangeRequestResponse.model_validate(req)


# =============================================================================
# 5. USAGE METERING & WEBHOOK INGESTION
# =============================================================================


@router.post(
    "/subscriptions/usage/record",
    response_model=SubscriptionUsageEventResponse,
    status_code=status.HTTP_201_CREATED,
)
async def record_usage_event(
    dto: SubscriptionUsageRecordRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> SubscriptionUsageEventResponse:
    """Idempotently record metered resource consumption for the current tenant."""
    if not current_user.tenant_id:
        raise BadRequestException("User has no active tenant context.")
    event = await SubscriptionService.record_usage_event(
        db=db, tenant_id=current_user.tenant_id, dto=dto
    )
    return SubscriptionUsageEventResponse.model_validate(event)


@router.post(
    "/subscriptions/webhooks/{provider}",
    status_code=status.HTTP_200_OK,
)
async def process_payment_webhook(
    provider: str,
    payload: SubscriptionWebhookPayload,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    x_signature: str | None = Header(None, alias="X-Signature"),
) -> dict[str, Any]:
    """Process verified external payment gateway callback (Razorpay, Stripe, Mock)."""
    event = await SubscriptionService.process_webhook(
        db=db,
        provider=provider,
        event_id=payload.event_id,
        event_type=payload.event_type,
        payload_json=payload.model_dump(mode="json"),
        signature=x_signature,
    )
    return {"status": "SUCCESS", "event_id": event.event_id, "processed": True}
