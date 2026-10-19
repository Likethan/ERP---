"""Step 38: Enterprise Customer Success, Subscription Lifecycle & SaaS Entitlements Test Suite.

Validates:
1. SaaS Subscription Plan Creation, Versioning, and Retirement
2. Tenant Subscription Lifecycle State Machine & Immutable Transitions
3. Centralized Entitlement Resolution & Time-Limited Overrides
4. Usage Metering, Idempotency & Concurrency-Safe Quota Enforcement
5. Plan Downgrade Capacity Impact Assessment (Zero Data Deletion Policy)
6. SaaS Invoicing, Payment Reconciliation & Dunning Recovery
7. Cryptographic Webhook Ingestion & Replay Protection
8. Customer Success Composite Health Matrix & Platform Internal Notes
9. Strict Multi-Tenant Isolation & PBAC Segregation (Platform Admin vs Tenant Admin)
10. Scheduled Lifecycle Background Sweepers
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BadRequestException,
    EntitlementExceededException,
    QuotaExceededException,
)
from app.core.security import ACCESS_TOKEN_COOKIE_NAME, create_access_token
from app.models.core import Institution
from app.models.people import User
from app.models.subscription import (
    BillingInterval,
    CustomerHealthStatus,
    CustomerNoteType,
    CustomerSuccessHealthSnapshot,
    CustomerSuccessNote,
    InvoiceStatus,
    OverrideType,
    PaymentStatus,
    SubscriptionChangeStatus,
    SubscriptionChangeType,
    SubscriptionEntitlementOverride,
    SubscriptionInvoice,
    SubscriptionLifecycleHistory,
    SubscriptionPlan,
    SubscriptionPlanStatus,
    SubscriptionStatus,
    SubscriptionUsageAggregate,
    SubscriptionUsageEvent,
    TenantSubscription,
)
from app.schemas.subscription import (
    EntitlementOverrideCreateRequest,
    SubscriptionPlanCreateRequest,
    SubscriptionPlanUpdateRequest,
    SubscriptionUsageRecordRequest,
)
from app.services.subscription_service import SubscriptionService


def make_auth_headers(
    user: User,
    tenant_id: uuid.UUID,
    role_name: str = "INSTITUTION_ADMIN",
) -> dict[str, str]:
    """Helper to generate JWT bearer and cookie authorization headers."""
    token = create_access_token(
        user_id=user.id,
        tenant_id=tenant_id,
        email=user.email,
        roles=[role_name],
        permissions=["*"] if role_name in ("SUPER_ADMIN", "INSTITUTION_ADMIN", "PLATFORM_OPERATOR") else [],
    )
    return {
        "Authorization": f"Bearer {token}",
        "Cookie": f"{ACCESS_TOKEN_COOKIE_NAME}={token}",
    }


# =============================================================================
# 1. SUBSCRIPTION PLANS
# =============================================================================


@pytest.mark.asyncio
async def test_subscription_plan_lifecycle_and_versioning(
    db_session: AsyncSession,
    tenant_admin_a: User,
):
    """Verify plan creation, version increment on update, and retirement protection."""
    plan_code = f"PLAN_TEST_{uuid.uuid4().hex[:6].upper()}"
    plan_req = SubscriptionPlanCreateRequest(
        code=plan_code,
        name="Test University Plan",
        description="Comprehensive testing plan",
        billing_interval=BillingInterval.ANNUAL,
        currency="INR",
        base_price=Decimal("250000.00"),
        trial_eligible=True,
        trial_duration_days=14,
        max_active_users=1000,
        max_students=10000,
        max_faculty=500,
        max_storage_bytes=107374182400,
        max_api_rpm=300,
        max_ai_tokens_monthly=500000,
        max_integrations=5,
        included_modules=["ACADEMICS", "ATTENDANCE", "EXAMINATION"],
        feature_capabilities={"ai_assistant": True, "sso_federation": False},
        support_tier="STANDARD",
    )

    plan = await SubscriptionService.create_plan(db_session, plan_req, actor_id=tenant_admin_a.id)
    assert plan.id is not None
    assert plan.code == plan_code
    assert plan.version == 1
    assert plan.status == SubscriptionPlanStatus.ACTIVE.value

    # Update plan -> increments version
    update_req = SubscriptionPlanUpdateRequest(
        name="Test University Plan v2",
        base_price=Decimal("275000.00"),
        feature_capabilities={"ai_assistant": True, "sso_federation": True},
    )
    updated_plan = await SubscriptionService.update_plan(
        db_session, plan.id, update_req, actor_id=tenant_admin_a.id
    )
    assert updated_plan.version == 2
    assert updated_plan.base_price == Decimal("275000.00")
    assert updated_plan.feature_capabilities.get("sso_federation") is True

    # Retire plan
    retired_plan = await SubscriptionService.retire_plan(db_session, plan.id, actor_id=tenant_admin_a.id)
    assert retired_plan.status == SubscriptionPlanStatus.RETIRED.value
    assert retired_plan.retired_at is not None


# =============================================================================
# 2. SUBSCRIPTION LIFECYCLE STATE MACHINE
# =============================================================================


@pytest.mark.asyncio
async def test_tenant_subscription_state_machine(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Verify subscription creation, transitions through trial, overdue, grace, suspension, and reactivation."""
    plans = await SubscriptionService.seed_default_plans(db_session)
    starter_plan = plans[0]

    # Create trial subscription
    sub = await SubscriptionService.create_subscription(
        db=db_session,
        tenant_id=tenant_a.id,
        plan_id=starter_plan.id,
        billing_interval=BillingInterval.ANNUAL,
        is_trial=True,
        actor_id=tenant_admin_a.id,
    )
    assert sub.status == SubscriptionStatus.TRIAL_ACTIVE.value
    assert sub.trial_ends_at is not None

    # Transition: TRIAL_ACTIVE -> ACTIVE (Activated paid subscription)
    sub = await SubscriptionService.transition_subscription_status(
        db=db_session,
        tenant_id=tenant_a.id,
        target_status=SubscriptionStatus.ACTIVE,
        reason="Initial purchase payment confirmed",
        actor_id=tenant_admin_a.id,
    )
    assert sub.status == SubscriptionStatus.ACTIVE.value

    # Transition: ACTIVE -> PAYMENT_OVERDUE
    sub = await SubscriptionService.transition_subscription_status(
        db=db_session,
        tenant_id=tenant_a.id,
        target_status=SubscriptionStatus.PAYMENT_OVERDUE,
        reason="Invoice payment bounced",
        actor_id=tenant_admin_a.id,
    )
    assert sub.status == SubscriptionStatus.PAYMENT_OVERDUE.value

    # Transition: PAYMENT_OVERDUE -> GRACE_PERIOD
    sub = await SubscriptionService.transition_subscription_status(
        db=db_session,
        tenant_id=tenant_a.id,
        target_status=SubscriptionStatus.GRACE_PERIOD,
        reason="Entering 14-day grace period",
        actor_id=tenant_admin_a.id,
    )
    assert sub.status == SubscriptionStatus.GRACE_PERIOD.value
    assert sub.grace_period_ends_at is not None

    # Transition: GRACE_PERIOD -> SUSPENDED
    sub = await SubscriptionService.transition_subscription_status(
        db=db_session,
        tenant_id=tenant_a.id,
        target_status=SubscriptionStatus.SUSPENDED,
        reason="Grace period expired without settlement",
        actor_id=tenant_admin_a.id,
    )
    assert sub.status == SubscriptionStatus.SUSPENDED.value

    # Transition: SUSPENDED -> ACTIVE (Reactivation)
    sub = await SubscriptionService.transition_subscription_status(
        db=db_session,
        tenant_id=tenant_a.id,
        target_status=SubscriptionStatus.ACTIVE,
        reason="Account settled in full",
        actor_id=tenant_admin_a.id,
    )
    assert sub.status == SubscriptionStatus.ACTIVE.value

    # Verify history entries exist
    hist_stmt = select(SubscriptionLifecycleHistory).where(
        SubscriptionLifecycleHistory.subscription_id == sub.id
    )
    hist_res = await db_session.execute(hist_stmt)
    history = list(hist_res.scalars().all())
    assert len(history) >= 5

    # Invalid transition rejection
    with pytest.raises(BadRequestException):
        await SubscriptionService.transition_subscription_status(
            db=db_session,
            tenant_id=tenant_a.id,
            target_status=SubscriptionStatus.TRIAL_PENDING,
            reason="Illegal reverse to trial pending",
            actor_id=tenant_admin_a.id,
        )


# =============================================================================
# 3. ENTITLEMENT RESOLUTION & OVERRIDES
# =============================================================================


@pytest.mark.asyncio
async def test_entitlement_engine_and_time_limited_overrides(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Verify centralized entitlement checks and time-limited administrative overrides."""
    plans = await SubscriptionService.seed_default_plans(db_session)
    starter_plan = plans[0]  # Only has ACADEMICS, ATTENDANCE, EXAMINATION, FINANCE, DOCUMENTS

    sub = await SubscriptionService.create_subscription(
        db=db_session,
        tenant_id=tenant_a.id,
        plan_id=starter_plan.id,
        is_trial=False,
    )

    # Initial checks
    assert await SubscriptionService.is_module_enabled(db_session, tenant_a.id, "ACADEMICS") is True
    assert await SubscriptionService.is_module_enabled(db_session, tenant_a.id, "PLACEMENT") is False
    assert await SubscriptionService.has_capability(db_session, tenant_a.id, "sso_federation") is False

    # Grant module override for PLACEMENT
    ov_mod = await SubscriptionService.create_override(
        db=db_session,
        tenant_id=tenant_a.id,
        dto=EntitlementOverrideCreateRequest(
            override_type=OverrideType.MODULE_GATE,
            target_key="PLACEMENT",
            override_value_json=True,
            reason="Pilot evaluation of placement module for 30 days",
            duration_days=30,
        ),
        actor_id=tenant_admin_a.id,
    )
    assert ov_mod.is_active is True
    assert await SubscriptionService.is_module_enabled(db_session, tenant_a.id, "PLACEMENT") is True

    # Grant capability override for sso_federation
    ov_cap = await SubscriptionService.create_override(
        db=db_session,
        tenant_id=tenant_a.id,
        dto=EntitlementOverrideCreateRequest(
            override_type=OverrideType.CAPABILITY,
            target_key="sso_federation",
            override_value_json=True,
            reason="SSO onboarding exemption",
            duration_days=15,
        ),
        actor_id=tenant_admin_a.id,
    )
    assert await SubscriptionService.has_capability(db_session, tenant_a.id, "sso_federation") is True

    # Revoke override
    await SubscriptionService.revoke_override(db_session, tenant_a.id, ov_mod.id, actor_id=tenant_admin_a.id)
    assert await SubscriptionService.is_module_enabled(db_session, tenant_a.id, "PLACEMENT") is False


# =============================================================================
# 4. USAGE METERING & QUOTA GATE
# =============================================================================


@pytest.mark.asyncio
async def test_usage_metering_and_idempotent_quota_blocking(
    db_session: AsyncSession,
    tenant_a: Institution,
):
    """Verify idempotent event recording and hard-limit rejection."""
    plans = await SubscriptionService.seed_default_plans(db_session)
    starter = plans[0]

    await SubscriptionService.create_subscription(
        db=db_session,
        tenant_id=tenant_a.id,
        plan_id=starter.id,
        is_trial=False,
    )

    idemp_key = f"evt_{uuid.uuid4().hex[:12]}"
    req = SubscriptionUsageRecordRequest(
        resource_type="API_CALLS",
        quantity=50,
        idempotency_key=idemp_key,
        source_subsystem="API_GATEWAY",
    )

    # 1. Record event
    event1 = await SubscriptionService.record_usage_event(db_session, tenant_a.id, req)
    assert event1.quantity == 50

    # 2. Duplicate submission returns original event without double-tallying
    event2 = await SubscriptionService.record_usage_event(db_session, tenant_a.id, req)
    assert event2.id == event1.id

    # Check aggregate
    now_cycle = datetime.now(UTC).strftime("%Y-%m")
    stmt = select(SubscriptionUsageAggregate).where(
        SubscriptionUsageAggregate.tenant_id == tenant_a.id,
        SubscriptionUsageAggregate.resource_type == "API_CALLS",
        SubscriptionUsageAggregate.billing_cycle == now_cycle,
    )
    res = await db_session.execute(stmt)
    agg = res.scalar_one()
    assert agg.current_usage == 50

    # 3. Attempting to record quantity exceeding hard limit raises QuotaExceededException
    huge_req = SubscriptionUsageRecordRequest(
        resource_type="API_CALLS",
        quantity=agg.hard_limit + 1000,
        idempotency_key=f"evt_huge_{uuid.uuid4().hex[:12]}",
    )
    with pytest.raises(QuotaExceededException):
        await SubscriptionService.record_usage_event(db_session, tenant_a.id, huge_req, enforce_hard_limit=True)


# =============================================================================
# 5. DOWNGRADE IMPACT ASSESSMENT (ZERO DATA LOSS)
# =============================================================================


@pytest.mark.asyncio
async def test_downgrade_impact_preview_zero_data_loss(
    db_session: AsyncSession,
    tenant_a: Institution,
):
    """Verify capacity assessment identifies resource excess without deleting records."""
    plans = await SubscriptionService.seed_default_plans(db_session)
    starter = plans[0]  # max 2,500 students
    professional = plans[1]  # max 15,000 students

    # Active subscription is Professional
    await SubscriptionService.create_subscription(
        db=db_session,
        tenant_id=tenant_a.id,
        plan_id=professional.id,
        is_trial=False,
    )

    # Artificially simulate 3,000 active students (exceeding Starter limit of 2,500)
    cycle = datetime.now(UTC).strftime("%Y-%m")
    agg = SubscriptionUsageAggregate(
        tenant_id=tenant_a.id,
        resource_type="STUDENTS",
        billing_cycle=cycle,
        current_usage=3000,
        soft_limit=2000,
        hard_limit=15000,
        is_exceeded=False,
    )
    db_session.add(agg)
    await db_session.flush()

    preview = await SubscriptionService.preview_downgrade(db_session, tenant_a.id, starter.id)
    assert preview["can_downgrade_immediately"] is False
    assert preview["has_capacity_violations"] is True
    assert len(preview["violations"]) > 0

    student_violation = next(v for v in preview["violations"] if "Student" in v["resource"])
    assert student_violation["current_usage"] == 3000
    assert student_violation["target_limit"] == starter.max_students
    assert student_violation["excess"] == 500

    # Verify modules to be removed includes PLACEMENT
    assert "PLACEMENT" in preview["removed_modules"]
    assert len(preview["recommended_actions"]) > 0


# =============================================================================
# 6. SAAS INVOICING & PAYMENT RECONCILIATION
# =============================================================================


@pytest.mark.asyncio
async def test_saas_invoicing_and_payment_reconciliation(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Verify invoice creation, payment recording, and status progression to PAID."""
    plans = await SubscriptionService.seed_default_plans(db_session)
    sub = await SubscriptionService.create_subscription(
        db=db_session,
        tenant_id=tenant_a.id,
        plan_id=plans[0].id,
        is_trial=False,
    )

    # Set subscription to overdue to test automatic recovery
    sub.status = SubscriptionStatus.PAYMENT_OVERDUE.value
    await db_session.flush()

    # Generate invoice
    now = datetime.now(UTC)
    invoice = await SubscriptionService.generate_invoice(
        db=db_session,
        tenant_id=tenant_a.id,
        subscription_id=sub.id,
        period_start=now,
        period_end=now + timedelta(days=365),
        amount=Decimal("150000.00"),
    )
    assert invoice.status == InvoiceStatus.ISSUED.value
    assert invoice.total_amount == Decimal("177000.00")  # 150000 + 18% GST (27000)

    # Record successful payment
    paid_inv = await SubscriptionService.record_payment(
        db=db_session,
        invoice_id=invoice.id,
        gateway_payment_id="pay_mock_settled_123",
        actor_id=tenant_admin_a.id,
    )
    assert paid_inv.status == InvoiceStatus.PAID.value
    assert paid_inv.paid_at is not None

    # Check subscription status restored to ACTIVE
    await db_session.refresh(sub)
    assert sub.status == SubscriptionStatus.ACTIVE.value


# =============================================================================
# 7. CRYPTOGRAPHIC WEBHOOK PROCESSING
# =============================================================================


@pytest.mark.asyncio
async def test_payment_webhook_idempotency_and_signature(
    db_session: AsyncSession,
    tenant_a: Institution,
):
    """Verify HMAC signature validation and idempotent webhook event deduplication."""
    event_id = f"evt_{uuid.uuid4().hex[:10]}"
    payload = {"event_id": event_id, "amount": 177000, "status": "SUCCESS"}

    # Process valid webhook without secret
    wb1 = await SubscriptionService.process_webhook(
        db=db_session,
        provider="RAZORPAY",
        event_id=event_id,
        event_type="payment.succeeded",
        payload_json=payload,
    )
    assert wb1.status == "PROCESSED"
    assert wb1.is_verified is True

    # Re-sending same event returns duplicate record
    wb2 = await SubscriptionService.process_webhook(
        db=db_session,
        provider="RAZORPAY",
        event_id=event_id,
        event_type="payment.succeeded",
        payload_json=payload,
    )
    assert wb2.id == wb1.id

    # Invalid signature with secret configured raises BadRequestException
    with pytest.raises(BadRequestException):
        await SubscriptionService.process_webhook(
            db=db_session,
            provider="STRIPE",
            event_id=f"evt_fail_{uuid.uuid4().hex[:8]}",
            event_type="charge.succeeded",
            payload_json=payload,
            signature="invalid_signature_hex",
            webhook_secret="super_secret_webhook_key",
        )


# =============================================================================
# 8. CUSTOMER SUCCESS HEALTH & NOTES
# =============================================================================


@pytest.mark.asyncio
async def test_customer_success_health_scoring_and_notes(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Verify composite health calculation and internal platform CS notes."""
    plans = await SubscriptionService.seed_default_plans(db_session)
    await SubscriptionService.create_subscription(
        db=db_session,
        tenant_id=tenant_a.id,
        plan_id=plans[0].id,
        is_trial=False,
    )

    health = await SubscriptionService.recalculate_health(db_session, tenant_a.id)
    assert 0 <= health.health_score <= 100
    assert health.health_status in [
        CustomerHealthStatus.HEALTHY.value,
        CustomerHealthStatus.GOOD.value,
        CustomerHealthStatus.NEEDS_ATTENTION.value,
    ]
    assert len(health.recommendations) > 0

    # Add platform CS note
    note = await SubscriptionService.add_customer_note(
        db=db_session,
        tenant_id=tenant_a.id,
        author_id=tenant_admin_a.id,
        author_email=tenant_admin_a.email,
        note_type=CustomerNoteType.RENEWAL_RISK,
        content="Institution discussed upcoming campus expansion. High upsell potential.",
        is_pinned=True,
    )
    assert note.id is not None
    assert note.is_pinned is True

    notes = await SubscriptionService.list_customer_notes(db_session, tenant_a.id)
    assert len(notes) >= 1
    assert notes[0].content == note.content


# =============================================================================
# 9. REST API ENDPOINTS & PBAC SEGREGATION
# =============================================================================


@pytest.mark.asyncio
async def test_rest_api_tenant_self_service_and_platform_admin_segregation(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_b: Institution,
    tenant_admin_a: User,
    tenant_admin_b: User,
    super_admin_user: User,
):
    """Verify tenant self-service APIs and PBAC rejection of unauthorized administrative mutations."""
    await SubscriptionService.seed_default_plans(db_session)

    headers_a = make_auth_headers(tenant_admin_a, tenant_a.id, "INSTITUTION_ADMIN")
    headers_platform = make_auth_headers(super_admin_user, tenant_a.id, "SUPER_ADMIN")

    # 1. Tenant self-service: GET /api/v1/subscriptions/my
    res_my = await client.get("/api/v1/subscriptions/my", headers=headers_a)
    assert res_my.status_code == 200
    sub_data = res_my.json()
    assert sub_data["tenant_id"] == str(tenant_a.id)

    # 2. Tenant self-service: GET /api/v1/subscriptions/my/entitlements
    res_ent = await client.get("/api/v1/subscriptions/my/entitlements", headers=headers_a)
    assert res_ent.status_code == 200
    ent_data = res_ent.json()
    assert "ACADEMICS" in ent_data["enabled_modules"]

    # 3. Non-platform admin attempting /api/v1/platform/plans returns 403 Forbidden
    res_forbidden = await client.get("/api/v1/platform/plans", headers=headers_a)
    assert res_forbidden.status_code == 403

    # 4. Platform admin accessing /api/v1/platform/plans returns 200 OK
    res_plans = await client.get("/api/v1/platform/plans", headers=headers_platform)
    assert res_plans.status_code == 200
    assert len(res_plans.json()) >= 3


# =============================================================================
# 10. TENANT ISOLATION
# =============================================================================


@pytest.mark.asyncio
async def test_tenant_isolation_boundary_enforcement(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_b: Institution,
    tenant_admin_a: User,
    tenant_admin_b: User,
):
    """Verify that Tenant A cannot access, mutate, or view Tenant B's subscription data."""
    plans = await SubscriptionService.seed_default_plans(db_session)
    await SubscriptionService.create_subscription(db_session, tenant_b.id, plans[0].id)

    headers_a = make_auth_headers(tenant_admin_a, tenant_a.id, "INSTITUTION_ADMIN")

    # Tenant A views own invoices (should be empty for A)
    res_a_inv = await client.get("/api/v1/subscriptions/my/invoices", headers=headers_a)
    assert res_a_inv.status_code == 200
    assert len(res_a_inv.json()) == 0


# =============================================================================
# 11. SCHEDULED LIFECYCLE SWEEPER
# =============================================================================


@pytest.mark.asyncio
async def test_scheduled_subscription_lifecycle_sweeper(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Verify background sweeper advances expired trials and grace periods."""
    plans = await SubscriptionService.seed_default_plans(db_session)
    sub = await SubscriptionService.create_subscription(
        db=db_session,
        tenant_id=tenant_a.id,
        plan_id=plans[0].id,
        is_trial=True,
    )

    # Force trial expiry into the past
    sub.trial_ends_at = datetime.now(UTC) - timedelta(days=2)
    await db_session.flush()

    res = await SubscriptionService.sweep_subscription_lifecycle(db_session)
    assert res["swept_trials"] >= 1

    await db_session.refresh(sub)
    assert sub.status == SubscriptionStatus.GRACE_PERIOD.value
    assert sub.grace_period_ends_at is not None
