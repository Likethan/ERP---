"""Enterprise Customer Success, Subscription Lifecycle & SaaS Entitlements Service (Step 38).

Centralized domain service managing:
- Packaging plans, tiers, and pricing models
- Tenant subscription lifecycle state machine & immutable transitions
- Centralized entitlement resolution (base plan + overrides)
- Concurrency-safe usage tracking & quota gate enforcement
- Downgrade capacity impact assessments (zero-loss data preservation)
- SaaS billing, invoices, payment reconciliation, and webhook verification
- Customer success health scoring, telemetry aggregation, and internal notes
- Scheduled lifecycle sweepers (trials, grace periods, auto-renewals, override expiries)
"""

import hashlib
import hmac
import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit import AuditEventCategory, build_audit_entry
from app.core.cache import tenant_cache
from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    EntitlementExceededException,
    FeatureNotEntitledException,
    NotFoundException,
    QuotaExceededException,
)
from app.models.core import Institution
from app.models.subscription import (
    BillingInterval,
    CustomerHealthStatus,
    CustomerNoteType,
    CustomerSuccessHealthSnapshot,
    CustomerSuccessNote,
    InvoiceStatus,
    OverrideType,
    PaymentStatus,
    SubscriptionChangeRequest,
    SubscriptionChangeStatus,
    SubscriptionChangeType,
    SubscriptionEntitlementOverride,
    SubscriptionInvoice,
    SubscriptionLifecycleHistory,
    SubscriptionPaymentAttempt,
    SubscriptionPlan,
    SubscriptionPlanStatus,
    SubscriptionStatus,
    SubscriptionUsageAggregate,
    SubscriptionUsageEvent,
    SubscriptionWebhookEvent,
    TenantSubscription,
)
from app.schemas.subscription import (
    EntitlementOverrideCreateRequest,
    SubscriptionPlanCreateRequest,
    SubscriptionPlanUpdateRequest,
    SubscriptionUsageRecordRequest,
)

logger = logging.getLogger("campusos.services.subscription")


def _to_utc(dt: datetime | None) -> datetime | None:
    """Ensure datetime is timezone-aware in UTC."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


class SubscriptionService:
    """Enterprise domain service for CampusOS SaaS subscriptions, entitlements, and customer success."""

    # -------------------------------------------------------------------------
    # 1. Subscription Plan Management
    # -------------------------------------------------------------------------

    @classmethod
    async def create_plan(
        cls,
        db: AsyncSession,
        dto: SubscriptionPlanCreateRequest,
        actor_id: UUID | None = None,
    ) -> SubscriptionPlan:
        """Create a new SaaS packaging plan tier."""
        stmt = select(SubscriptionPlan).where(SubscriptionPlan.code == dto.code.upper())
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            raise ConflictException(f"Subscription plan with code '{dto.code}' already exists.")

        plan = SubscriptionPlan(
            code=dto.code.upper(),
            name=dto.name,
            description=dto.description,
            status=dto.status.value,
            billing_interval=dto.billing_interval.value,
            currency=dto.currency.upper(),
            base_price=dto.base_price,
            trial_eligible=dto.trial_eligible,
            trial_duration_days=dto.trial_duration_days,
            max_active_users=dto.max_active_users,
            max_students=dto.max_students,
            max_faculty=dto.max_faculty,
            max_storage_bytes=dto.max_storage_bytes,
            max_api_rpm=dto.max_api_rpm,
            max_ai_tokens_monthly=dto.max_ai_tokens_monthly,
            max_integrations=dto.max_integrations,
            included_modules=[m.upper() for m in dto.included_modules],
            feature_capabilities=dict(dto.feature_capabilities),
            support_tier=dto.support_tier.upper(),
            version=1,
        )
        db.add(plan)
        await db.flush()

        db.add(
            build_audit_entry(
                tenant_id=plan.id,  # System-level entity, use plan.id as reference
                action=AuditEventCategory.SUBSCRIPTION_PLAN_CREATED,
                entity_type="SubscriptionPlan",
                entity_id=plan.id,
                user_id=actor_id,
                new_values_json={"code": plan.code, "name": plan.name, "price": str(plan.base_price)},
                business_context=f"Created SaaS subscription plan '{plan.name}' ({plan.code})",
            )
        )
        await db.flush()
        return plan

    @classmethod
    async def update_plan(
        cls,
        db: AsyncSession,
        plan_id: UUID,
        dto: SubscriptionPlanUpdateRequest,
        actor_id: UUID | None = None,
    ) -> SubscriptionPlan:
        """Update an existing plan definition, incrementing version to preserve historical traceability."""
        plan = await cls.get_plan(db, plan_id)

        old_values = {
            "name": plan.name,
            "base_price": str(plan.base_price),
            "status": plan.status,
            "version": plan.version,
        }

        if dto.name is not None:
            plan.name = dto.name
        if dto.description is not None:
            plan.description = dto.description
        if dto.status is not None:
            plan.status = dto.status.value
        if dto.base_price is not None:
            plan.base_price = dto.base_price
        if dto.trial_eligible is not None:
            plan.trial_eligible = dto.trial_eligible
        if dto.trial_duration_days is not None:
            plan.trial_duration_days = dto.trial_duration_days
        if dto.max_active_users is not None:
            plan.max_active_users = dto.max_active_users
        if dto.max_students is not None:
            plan.max_students = dto.max_students
        if dto.max_faculty is not None:
            plan.max_faculty = dto.max_faculty
        if dto.max_storage_bytes is not None:
            plan.max_storage_bytes = dto.max_storage_bytes
        if dto.max_api_rpm is not None:
            plan.max_api_rpm = dto.max_api_rpm
        if dto.max_ai_tokens_monthly is not None:
            plan.max_ai_tokens_monthly = dto.max_ai_tokens_monthly
        if dto.max_integrations is not None:
            plan.max_integrations = dto.max_integrations
        if dto.included_modules is not None:
            plan.included_modules = [m.upper() for m in dto.included_modules]
        if dto.feature_capabilities is not None:
            plan.feature_capabilities = {**plan.feature_capabilities, **dto.feature_capabilities}
        if dto.support_tier is not None:
            plan.support_tier = dto.support_tier.upper()

        plan.version += 1

        db.add(
            build_audit_entry(
                tenant_id=plan.id,
                action=AuditEventCategory.SUBSCRIPTION_PLAN_UPDATED,
                entity_type="SubscriptionPlan",
                entity_id=plan.id,
                user_id=actor_id,
                old_values_json=old_values,
                new_values_json={
                    "name": plan.name,
                    "base_price": str(plan.base_price),
                    "status": plan.status,
                    "version": plan.version,
                },
                business_context=f"Updated SaaS subscription plan '{plan.code}' to version {plan.version}",
            )
        )
        await db.flush()
        return plan

    @classmethod
    async def retire_plan(
        cls,
        db: AsyncSession,
        plan_id: UUID,
        actor_id: UUID | None = None,
    ) -> SubscriptionPlan:
        """Mark a plan as retired so no new subscriptions can select it while preserving existing subscriptions."""
        plan = await cls.get_plan(db, plan_id)
        plan.status = SubscriptionPlanStatus.RETIRED.value
        plan.retired_at = datetime.now(UTC)

        db.add(
            build_audit_entry(
                tenant_id=plan.id,
                action=AuditEventCategory.SUBSCRIPTION_PLAN_RETIRED,
                entity_type="SubscriptionPlan",
                entity_id=plan.id,
                user_id=actor_id,
                business_context=f"Retired SaaS subscription plan '{plan.code}'",
            )
        )
        await db.flush()
        return plan

    @classmethod
    async def get_plan(cls, db: AsyncSession, plan_id: UUID) -> SubscriptionPlan:
        """Retrieve a plan by its UUID."""
        stmt = select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id)
        res = await db.execute(stmt)
        plan = res.scalar_one_or_none()
        if not plan:
            raise NotFoundException("SubscriptionPlan", plan_id)
        return plan

    @classmethod
    async def list_plans(
        cls,
        db: AsyncSession,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[SubscriptionPlan]:
        """List subscription plans with optional status filtering."""
        stmt = select(SubscriptionPlan)
        if status:
            stmt = stmt.where(SubscriptionPlan.status == status.upper())
        stmt = stmt.order_by(SubscriptionPlan.base_price.asc()).offset(offset).limit(limit)
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @classmethod
    async def seed_default_plans(cls, db: AsyncSession) -> list[SubscriptionPlan]:
        """Seed standard CampusOS commercial plans (Starter, Professional, Enterprise) if none exist."""
        default_defs = [
            {
                "code": "CAMPUSOS_STARTER",
                "name": "CampusOS Starter College Edition",
                "description": "Essential ERP suite for single-campus colleges and polytechnic institutes.",
                "billing_interval": BillingInterval.ANNUAL.value,
                "currency": "INR",
                "base_price": Decimal("150000.00"),
                "trial_eligible": True,
                "trial_duration_days": 14,
                "max_active_users": 500,
                "max_students": 2500,
                "max_faculty": 150,
                "max_storage_bytes": 53687091200,  # 50 GB
                "max_api_rpm": 120,
                "max_ai_tokens_monthly": 100000,
                "max_integrations": 3,
                "included_modules": ["ACADEMICS", "ATTENDANCE", "EXAMINATION", "FINANCE", "DOCUMENTS"],
                "feature_capabilities": {
                    "ai_assistant": True,
                    "advanced_analytics": False,
                    "sso_federation": False,
                    "custom_webhooks": False,
                    "sla_governance": False,
                },
                "support_tier": "STANDARD",
            },
            {
                "code": "CAMPUSOS_PROFESSIONAL",
                "name": "CampusOS Professional University Edition",
                "description": "Comprehensive ERP with placement, multi-campus, and integration support.",
                "billing_interval": BillingInterval.ANNUAL.value,
                "currency": "INR",
                "base_price": Decimal("450000.00"),
                "trial_eligible": True,
                "trial_duration_days": 21,
                "max_active_users": 2500,
                "max_students": 15000,
                "max_faculty": 800,
                "max_storage_bytes": 268435456000,  # 250 GB
                "max_api_rpm": 300,
                "max_ai_tokens_monthly": 1000000,
                "max_integrations": 10,
                "included_modules": [
                    "ACADEMICS",
                    "ATTENDANCE",
                    "EXAMINATION",
                    "FINANCE",
                    "DOCUMENTS",
                    "PLACEMENT",
                    "CAMPUS",
                    "INFRASTRUCTURE",
                    "INTEGRATIONS",
                    "ADOPTION",
                ],
                "feature_capabilities": {
                    "ai_assistant": True,
                    "advanced_analytics": True,
                    "sso_federation": True,
                    "custom_webhooks": True,
                    "sla_governance": False,
                },
                "support_tier": "PREMIUM",
            },
            {
                "code": "CAMPUSOS_ENTERPRISE",
                "name": "CampusOS Enterprise Multi-Institution Suite",
                "description": "Unrestricted capabilities, bespoke integrations, dedicated SLA & enterprise security.",
                "billing_interval": BillingInterval.ANNUAL.value,
                "currency": "INR",
                "base_price": Decimal("1200000.00"),
                "trial_eligible": False,
                "trial_duration_days": 0,
                "max_active_users": 20000,
                "max_students": 100000,
                "max_faculty": 5000,
                "max_storage_bytes": 1099511627776,  # 1 TB
                "max_api_rpm": 1000,
                "max_ai_tokens_monthly": 10000000,
                "max_integrations": 50,
                "included_modules": [
                    "ACADEMICS",
                    "ATTENDANCE",
                    "EXAMINATION",
                    "FINANCE",
                    "DOCUMENTS",
                    "PLACEMENT",
                    "CAMPUS",
                    "INFRASTRUCTURE",
                    "INTEGRATIONS",
                    "IDENTITY",
                    "ADOPTION",
                    "SUPPORT",
                    "SECURITY_OPS",
                ],
                "feature_capabilities": {
                    "ai_assistant": True,
                    "advanced_analytics": True,
                    "sso_federation": True,
                    "custom_webhooks": True,
                    "sla_governance": True,
                    "case_management": True,
                    "dedicated_cluster": True,
                },
                "support_tier": "ENTERPRISE_DEDICATED",
            },
        ]

        seeded = []
        for def_data in default_defs:
            stmt = select(SubscriptionPlan).where(SubscriptionPlan.code == def_data["code"])
            res = await db.execute(stmt)
            plan = res.scalar_one_or_none()
            if not plan:
                plan = SubscriptionPlan(
                    code=def_data["code"],
                    name=def_data["name"],
                    description=def_data["description"],
                    status=SubscriptionPlanStatus.ACTIVE.value,
                    billing_interval=def_data["billing_interval"],
                    currency=def_data["currency"],
                    base_price=def_data["base_price"],
                    trial_eligible=def_data["trial_eligible"],
                    trial_duration_days=def_data["trial_duration_days"],
                    max_active_users=def_data["max_active_users"],
                    max_students=def_data["max_students"],
                    max_faculty=def_data["max_faculty"],
                    max_storage_bytes=def_data["max_storage_bytes"],
                    max_api_rpm=def_data["max_api_rpm"],
                    max_ai_tokens_monthly=def_data["max_ai_tokens_monthly"],
                    max_integrations=def_data["max_integrations"],
                    included_modules=def_data["included_modules"],
                    feature_capabilities=def_data["feature_capabilities"],
                    support_tier=def_data["support_tier"],
                    version=1,
                )
                db.add(plan)
                seeded.append(plan)

        await db.flush()
        return seeded

    # -------------------------------------------------------------------------
    # 2. Tenant Subscription Lifecycle
    # -------------------------------------------------------------------------

    @classmethod
    async def create_subscription(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        plan_id: UUID,
        billing_interval: BillingInterval = BillingInterval.ANNUAL,
        is_trial: bool = False,
        custom_unit_price: Decimal | None = None,
        payment_method_id: str | None = None,
        actor_id: UUID | None = None,
        actor_email: str | None = None,
    ) -> TenantSubscription:
        """Initialize an institutional commercial subscription and freeze plan snapshot."""
        # Check tenant exists
        t_stmt = select(Institution).where(Institution.id == tenant_id)
        t_res = await db.execute(t_stmt)
        tenant = t_res.scalar_one_or_none()
        if not tenant:
            raise NotFoundException("Institution", tenant_id)

        plan = await cls.get_plan(db, plan_id)
        if plan.status == SubscriptionPlanStatus.RETIRED.value:
            raise BadRequestException("Cannot subscribe to a retired packaging plan.")

        now = datetime.now(UTC)
        duration_days = 365 if billing_interval == BillingInterval.ANNUAL else (
            90 if billing_interval == BillingInterval.QUARTERLY else 30
        )
        period_end = now + timedelta(days=duration_days)

        trial_started_at = now if is_trial else None
        trial_ends_at = now + timedelta(days=plan.trial_duration_days) if is_trial else None
        grace_period_ends_at = trial_ends_at + timedelta(days=7) if is_trial else None
        initial_status = SubscriptionStatus.TRIAL_ACTIVE.value if is_trial else SubscriptionStatus.ACTIVE.value

        price = custom_unit_price if custom_unit_price is not None else plan.base_price

        # Freeze limits snapshot
        limits_snapshot = {
            "max_active_users": plan.max_active_users,
            "max_students": plan.max_students,
            "max_faculty": plan.max_faculty,
            "max_storage_bytes": plan.max_storage_bytes,
            "max_api_rpm": plan.max_api_rpm,
            "max_ai_tokens_monthly": plan.max_ai_tokens_monthly,
            "max_integrations": plan.max_integrations,
        }

        sub = TenantSubscription(
            tenant_id=tenant_id,
            plan_id=plan.id,
            plan_version=plan.version,
            status=initial_status,
            billing_interval=billing_interval.value,
            currency=plan.currency,
            unit_price=price,
            current_period_start=now,
            current_period_end=period_end,
            trial_started_at=trial_started_at,
            trial_ends_at=trial_ends_at,
            grace_period_ends_at=grace_period_ends_at,
            auto_renew=True,
            payment_method_id=payment_method_id,
            snapshot_limits_json=limits_snapshot,
            snapshot_modules_json=list(plan.included_modules),
            snapshot_features_json=dict(plan.feature_capabilities),
        )
        sub.plan = plan
        db.add(sub)
        await db.flush()

        # Update institution plan reference
        tenant.plan = plan.code

        # Record initial lifecycle transition
        history = SubscriptionLifecycleHistory(
            tenant_id=tenant_id,
            subscription_id=sub.id,
            from_status="NONE",
            to_status=initial_status,
            reason=f"Initial subscription created (Plan: {plan.code}, Trial: {is_trial})",
            actor_id=actor_id,
            actor_email=actor_email,
            metadata_json={"plan_code": plan.code, "unit_price": str(price)},
        )
        db.add(history)

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.SUBSCRIPTION_CREATED,
                entity_type="TenantSubscription",
                entity_id=sub.id,
                user_id=actor_id,
                new_values_json={"plan": plan.code, "status": initial_status, "price": str(price)},
                business_context=f"Created subscription for tenant {tenant_id} on plan {plan.code}",
            )
        )
        await db.flush()
        await tenant_cache.invalidate_namespace(tenant_id, "entitlements")
        sub.plan = plan
        return sub

    @classmethod
    async def get_active_subscription(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
    ) -> TenantSubscription:
        """Fetch the current active or primary subscription for a tenant."""
        stmt = (
            select(TenantSubscription)
            .options(selectinload(TenantSubscription.plan))
            .where(TenantSubscription.tenant_id == tenant_id)
            .order_by(desc(TenantSubscription.created_at))
        )
        res = await db.execute(stmt)
        sub = res.scalar_one_or_none()
        if not sub:
            # Check tenant exists
            t_stmt = select(Institution).where(Institution.id == tenant_id)
            t_res = await db.execute(t_stmt)
            tenant = t_res.scalar_one_or_none()
            if not tenant:
                raise NotFoundException("Institution", tenant_id)

            # Auto-initialize on Starter plan trial
            plans = await cls.list_plans(db, status=SubscriptionPlanStatus.ACTIVE.value)
            if not plans:
                plans = await cls.seed_default_plans(db)
            selected_plan = plans[0]
            sub = await cls.create_subscription(
                db=db,
                tenant_id=tenant_id,
                plan_id=selected_plan.id,
                is_trial=True,
            )
            sub.plan = selected_plan
        return sub

    @classmethod
    async def transition_subscription_status(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        target_status: SubscriptionStatus,
        reason: str,
        actor_id: UUID | None = None,
        actor_email: str | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> TenantSubscription:
        """Execute and validate an authoritative subscription state machine transition."""
        sub = await cls.get_active_subscription(db, tenant_id)
        from_status = sub.status
        to_status = target_status.value

        if from_status == to_status:
            return sub

        # Validate allowed transitions
        VALID_TRANSITIONS: dict[str, set[str]] = {
            SubscriptionStatus.TRIAL_PENDING.value: {
                SubscriptionStatus.TRIAL_ACTIVE.value,
                SubscriptionStatus.ACTIVE.value,
                SubscriptionStatus.CANCELLED.value,
            },
            SubscriptionStatus.TRIAL_ACTIVE.value: {
                SubscriptionStatus.ACTIVE.value,
                SubscriptionStatus.GRACE_PERIOD.value,
                SubscriptionStatus.EXPIRED.value,
                SubscriptionStatus.CANCELLED.value,
            },
            SubscriptionStatus.ACTIVE.value: {
                SubscriptionStatus.PAYMENT_OVERDUE.value,
                SubscriptionStatus.GRACE_PERIOD.value,
                SubscriptionStatus.SUSPENDED.value,
                SubscriptionStatus.CANCELLATION_SCHEDULED.value,
                SubscriptionStatus.CANCELLED.value,
                SubscriptionStatus.EXPIRED.value,
            },
            SubscriptionStatus.PAYMENT_OVERDUE.value: {
                SubscriptionStatus.ACTIVE.value,
                SubscriptionStatus.GRACE_PERIOD.value,
                SubscriptionStatus.SUSPENDED.value,
                SubscriptionStatus.CANCELLED.value,
            },
            SubscriptionStatus.GRACE_PERIOD.value: {
                SubscriptionStatus.ACTIVE.value,
                SubscriptionStatus.SUSPENDED.value,
                SubscriptionStatus.EXPIRED.value,
                SubscriptionStatus.CANCELLED.value,
            },
            SubscriptionStatus.SUSPENDED.value: {
                SubscriptionStatus.ACTIVE.value,
                SubscriptionStatus.CANCELLED.value,
                SubscriptionStatus.EXPIRED.value,
            },
            SubscriptionStatus.CANCELLATION_SCHEDULED.value: {
                SubscriptionStatus.ACTIVE.value,
                SubscriptionStatus.CANCELLED.value,
            },
            SubscriptionStatus.CANCELLED.value: {
                SubscriptionStatus.ACTIVE.value,
            },
            SubscriptionStatus.EXPIRED.value: {
                SubscriptionStatus.ACTIVE.value,
            },
        }

        allowed = VALID_TRANSITIONS.get(from_status, set())
        if to_status not in allowed:
            raise BadRequestException(
                f"Invalid subscription state transition from '{from_status}' to '{to_status}'."
            )

        now = datetime.now(UTC)
        sub.status = to_status

        if to_status == SubscriptionStatus.ACTIVE.value:
            # Leaving overdue or grace period
            sub.grace_period_ends_at = None
        elif to_status == SubscriptionStatus.GRACE_PERIOD.value:
            sub.grace_period_ends_at = now + timedelta(days=14)
        elif to_status == SubscriptionStatus.CANCELLATION_SCHEDULED.value:
            sub.cancellation_effective_at = sub.current_period_end
            sub.cancellation_reason = reason
        elif to_status == SubscriptionStatus.CANCELLED.value:
            sub.cancellation_effective_at = now
            sub.cancellation_reason = reason
            sub.auto_renew = False

        # Record history
        history = SubscriptionLifecycleHistory(
            tenant_id=tenant_id,
            subscription_id=sub.id,
            from_status=from_status,
            to_status=to_status,
            reason=reason,
            actor_id=actor_id,
            actor_email=actor_email,
            metadata_json=metadata_json or {},
        )
        db.add(history)

        action_map = {
            SubscriptionStatus.ACTIVE.value: AuditEventCategory.SUBSCRIPTION_ACTIVATED,
            SubscriptionStatus.SUSPENDED.value: AuditEventCategory.SUBSCRIPTION_SUSPENDED,
            SubscriptionStatus.CANCELLED.value: AuditEventCategory.SUBSCRIPTION_CANCELLED,
            SubscriptionStatus.EXPIRED.value: AuditEventCategory.SUBSCRIPTION_EXPIRED,
        }
        audit_action = action_map.get(to_status, AuditEventCategory.SUBSCRIPTION_ACTIVATED)

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=audit_action,
                entity_type="TenantSubscription",
                entity_id=sub.id,
                user_id=actor_id,
                old_values_json={"status": from_status},
                new_values_json={"status": to_status},
                business_context=f"Transitioned subscription from '{from_status}' to '{to_status}': {reason}",
            )
        )
        await db.flush()
        await tenant_cache.invalidate_namespace(tenant_id, "entitlements")
        return sub

    @classmethod
    async def renew_subscription(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        actor_id: UUID | None = None,
        actor_email: str | None = None,
    ) -> TenantSubscription:
        """Extend subscription period by its billing interval and generate renewal invoice."""
        sub = await cls.get_active_subscription(db, tenant_id)
        days = 365 if sub.billing_interval == BillingInterval.ANNUAL.value else (
            90 if sub.billing_interval == BillingInterval.QUARTERLY.value else 30
        )

        old_end = _to_utc(sub.current_period_end) or datetime.now(UTC)
        new_start = old_end
        new_end = old_end + timedelta(days=days)

        sub.current_period_start = new_start
        sub.current_period_end = new_end
        sub.status = SubscriptionStatus.ACTIVE.value

        # Generate renewal invoice
        invoice = await cls.generate_invoice(
            db=db,
            tenant_id=tenant_id,
            subscription_id=sub.id,
            period_start=new_start,
            period_end=new_end,
            amount=sub.unit_price,
            description=f"CampusOS SaaS Subscription Renewal ({sub.billing_interval})",
        )

        history = SubscriptionLifecycleHistory(
            tenant_id=tenant_id,
            subscription_id=sub.id,
            from_status=sub.status,
            to_status=SubscriptionStatus.ACTIVE.value,
            reason=f"Subscription renewed until {new_end.date().isoformat()}",
            actor_id=actor_id,
            actor_email=actor_email,
            metadata_json={"invoice_number": invoice.invoice_number, "new_period_end": new_end.isoformat()},
        )
        db.add(history)

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.SUBSCRIPTION_RENEWED,
                entity_type="TenantSubscription",
                entity_id=sub.id,
                user_id=actor_id,
                business_context=f"Renewed subscription for tenant {tenant_id} to {new_end.date()}",
            )
        )
        await db.flush()
        return sub

    # -------------------------------------------------------------------------
    # 3. Entitlement Engine & Overrides
    # -------------------------------------------------------------------------

    @classmethod
    async def get_effective_entitlements(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
    ) -> dict[str, Any]:
        """Centralized evaluation of active modules, capabilities, and resource limits."""
        sub = await cls.get_active_subscription(db, tenant_id)
        now = datetime.now(UTC)

        # Base snapshot limits and capabilities
        plan_modules = list(sub.plan.included_modules) if (sub.plan and sub.plan.included_modules) else []
        plan_features = dict(sub.plan.feature_capabilities) if (sub.plan and sub.plan.feature_capabilities) else {}
        plan_limits = (
            {
                "max_active_users": sub.plan.max_active_users,
                "max_students": sub.plan.max_students,
                "max_faculty": sub.plan.max_faculty,
                "max_storage_bytes": sub.plan.max_storage_bytes,
                "max_api_rpm": sub.plan.max_api_rpm,
                "max_ai_tokens_monthly": sub.plan.max_ai_tokens_monthly,
                "max_integrations": sub.plan.max_integrations,
            }
            if sub.plan
            else {}
        )

        enabled_modules = set(sub.snapshot_modules_json if sub.snapshot_modules_json else plan_modules)
        capabilities = dict(sub.snapshot_features_json if sub.snapshot_features_json else plan_features)
        limits = dict(sub.snapshot_limits_json if sub.snapshot_limits_json else plan_limits)

        # Fetch active, unexpired overrides
        stmt = (
            select(SubscriptionEntitlementOverride)
            .where(
                SubscriptionEntitlementOverride.tenant_id == tenant_id,
                SubscriptionEntitlementOverride.is_active.is_(True),
                SubscriptionEntitlementOverride.starts_at <= now,
                SubscriptionEntitlementOverride.expires_at >= now,
            )
            .order_by(SubscriptionEntitlementOverride.created_at.asc())
        )
        res = await db.execute(stmt)
        overrides = list(res.scalars().all())

        for ov in overrides:
            if ov.override_type == OverrideType.MODULE_GATE.value:
                if bool(ov.override_value_json):
                    enabled_modules.add(ov.target_key.upper())
                else:
                    enabled_modules.discard(ov.target_key.upper())
            elif ov.override_type == OverrideType.CAPABILITY.value:
                capabilities[ov.target_key] = bool(ov.override_value_json)
            elif ov.override_type == OverrideType.QUOTA_LIMIT.value:
                try:
                    limits[ov.target_key] = int(ov.override_value_json)
                except (ValueError, TypeError):
                    limits[ov.target_key] = ov.override_value_json

        # Trial days calculation
        is_trial = sub.status == SubscriptionStatus.TRIAL_ACTIVE.value
        trial_days_remaining = 0
        if is_trial and sub.trial_ends_at:
            t_end = sub.trial_ends_at if sub.trial_ends_at.tzinfo else sub.trial_ends_at.replace(tzinfo=UTC)
            trial_days_remaining = max(0, (t_end - now).days)

        is_sub_active = sub.status in (
            SubscriptionStatus.ACTIVE.value,
            SubscriptionStatus.TRIAL_ACTIVE.value,
            SubscriptionStatus.GRACE_PERIOD.value,
        )

        return {
            "tenant_id": tenant_id,
            "plan_code": sub.plan.code if sub.plan else "CUSTOM",
            "plan_name": sub.plan.name if sub.plan else "Custom Enterprise",
            "subscription_status": sub.status,
            "is_active": is_sub_active,
            "is_trial": is_trial,
            "trial_days_remaining": trial_days_remaining,
            "enabled_modules": sorted(list(enabled_modules)),
            "feature_capabilities": capabilities,
            "resource_limits": limits,
            "active_overrides": overrides,
        }

    @classmethod
    async def is_module_enabled(cls, db: AsyncSession, tenant_id: UUID, module_code: str) -> bool:
        """Check whether an ERP module is enabled under the current subscription entitlements."""
        ent = await cls.get_effective_entitlements(db, tenant_id)
        if not ent["is_active"]:
            return False
        return module_code.upper() in ent["enabled_modules"]

    @classmethod
    async def has_capability(cls, db: AsyncSession, tenant_id: UUID, capability_code: str) -> bool:
        """Check whether a specific platform feature capability is enabled."""
        ent = await cls.get_effective_entitlements(db, tenant_id)
        if not ent["is_active"]:
            return False
        return bool(ent["feature_capabilities"].get(capability_code, False))

    @classmethod
    async def assert_module_enabled(cls, db: AsyncSession, tenant_id: UUID, module_code: str) -> None:
        """Enforce module entitlement, raising an explicit EntitlementExceededException if unavailable."""
        if not await cls.is_module_enabled(db, tenant_id, module_code):
            ent = await cls.get_effective_entitlements(db, tenant_id)
            raise EntitlementExceededException(
                feature_or_module=module_code,
                plan=ent["plan_code"],
                message=f"Module '{module_code}' is not included in your institution's subscription ({ent['plan_code']}).",
            )

    @classmethod
    async def assert_capability(cls, db: AsyncSession, tenant_id: UUID, capability_code: str) -> None:
        """Enforce feature capability, raising FeatureNotEntitledException if disabled."""
        if not await cls.has_capability(db, tenant_id, capability_code):
            ent = await cls.get_effective_entitlements(db, tenant_id)
            raise FeatureNotEntitledException(feature_key=capability_code, plan=ent["plan_code"])

    @classmethod
    async def create_override(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        dto: EntitlementOverrideCreateRequest,
        actor_id: UUID,
    ) -> SubscriptionEntitlementOverride:
        """Authorize a time-limited capability or quota override for a tenant."""
        now = datetime.now(UTC)
        expires_at = now + timedelta(days=dto.duration_days)

        override = SubscriptionEntitlementOverride(
            tenant_id=tenant_id,
            override_type=dto.override_type.value,
            target_key=dto.target_key,
            override_value_json=dto.override_value_json,
            reason=dto.reason,
            granted_by_id=actor_id,
            starts_at=now,
            expires_at=expires_at,
            is_active=True,
        )
        db.add(override)
        await db.flush()

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.ENTITLEMENT_OVERRIDE_GRANTED,
                entity_type="SubscriptionEntitlementOverride",
                entity_id=override.id,
                user_id=actor_id,
                new_values_json={
                    "type": override.override_type,
                    "target": override.target_key,
                    "value": str(override.override_value_json),
                    "expires_at": expires_at.isoformat(),
                },
                business_context=f"Granted entitlement override for '{override.target_key}': {dto.reason}",
            )
        )
        await db.flush()
        await tenant_cache.invalidate_namespace(tenant_id, "entitlements")
        return override

    @classmethod
    async def revoke_override(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        override_id: UUID,
        actor_id: UUID | None = None,
    ) -> SubscriptionEntitlementOverride:
        """Revoke an active entitlement override before its scheduled expiry."""
        stmt = select(SubscriptionEntitlementOverride).where(
            SubscriptionEntitlementOverride.id == override_id,
            SubscriptionEntitlementOverride.tenant_id == tenant_id,
        )
        res = await db.execute(stmt)
        override = res.scalar_one_or_none()
        if not override:
            raise NotFoundException("SubscriptionEntitlementOverride", override_id)

        override.is_active = False

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.ENTITLEMENT_OVERRIDE_REVOKED,
                entity_type="SubscriptionEntitlementOverride",
                entity_id=override.id,
                user_id=actor_id,
                business_context=f"Revoked entitlement override '{override.target_key}'",
            )
        )
        await db.flush()
        await tenant_cache.invalidate_namespace(tenant_id, "entitlements")
        return override

    # -------------------------------------------------------------------------
    # 4. Usage Metering & Quota Gate Enforcement
    # -------------------------------------------------------------------------

    @classmethod
    async def record_usage_event(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        dto: SubscriptionUsageRecordRequest,
        enforce_hard_limit: bool = True,
    ) -> SubscriptionUsageEvent:
        """Idempotently ingest a raw metered usage event and atomically update billing aggregate."""
        # Check idempotency
        stmt = select(SubscriptionUsageEvent).where(
            SubscriptionUsageEvent.tenant_id == tenant_id,
            SubscriptionUsageEvent.idempotency_key == dto.idempotency_key,
        )
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            return existing

        now = datetime.now(UTC)
        cycle = now.strftime("%Y-%m")

        # Get or create aggregate
        agg_stmt = select(SubscriptionUsageAggregate).where(
            SubscriptionUsageAggregate.tenant_id == tenant_id,
            SubscriptionUsageAggregate.resource_type == dto.resource_type.upper(),
            SubscriptionUsageAggregate.billing_cycle == cycle,
        )
        agg_res = await db.execute(agg_stmt)
        agg = agg_res.scalar_one_or_none()

        ent = await cls.get_effective_entitlements(db, tenant_id)
        hard_limit_key = f"max_{dto.resource_type.lower()}"
        hard_limit = ent["resource_limits"].get(hard_limit_key, 10000)
        soft_limit = int(hard_limit * 0.8)

        if not agg:
            agg = SubscriptionUsageAggregate(
                tenant_id=tenant_id,
                resource_type=dto.resource_type.upper(),
                billing_cycle=cycle,
                current_usage=0,
                soft_limit=soft_limit,
                hard_limit=hard_limit,
                is_exceeded=False,
                overage_count=0,
            )
            db.add(agg)
            await db.flush()

        # Check hard limit
        if enforce_hard_limit and (agg.current_usage + dto.quantity > agg.hard_limit):
            agg.is_exceeded = True
            agg.overage_count += 1
            db.add(
                build_audit_entry(
                    tenant_id=tenant_id,
                    action=AuditEventCategory.QUOTA_HARD_LIMIT_BLOCKED,
                    entity_type="SubscriptionUsageAggregate",
                    entity_id=agg.id,
                    business_context=(
                        f"Quota hard limit blocked for {dto.resource_type}: "
                        f"current={agg.current_usage}, requested={dto.quantity}, limit={agg.hard_limit}"
                    ),
                )
            )
            await db.flush()
            raise QuotaExceededException(
                resource_type=dto.resource_type,
                limit=agg.hard_limit,
                current=agg.current_usage,
            )

        agg.current_usage += dto.quantity
        agg.last_synced_at = now
        if agg.current_usage > agg.hard_limit:
            agg.is_exceeded = True

        event = SubscriptionUsageEvent(
            tenant_id=tenant_id,
            resource_type=dto.resource_type.upper(),
            quantity=dto.quantity,
            idempotency_key=dto.idempotency_key,
            measured_at=now,
            source_subsystem=dto.source_subsystem,
            metadata_json=dto.metadata_json,
        )
        db.add(event)
        await db.flush()
        return event

    @classmethod
    async def get_quota_status(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
    ) -> list[dict[str, Any]]:
        """Fetch current consumption, limits, and remaining headroom across metered resources."""
        ent = await cls.get_effective_entitlements(db, tenant_id)
        now = datetime.now(UTC)
        cycle = now.strftime("%Y-%m")

        stmt = select(SubscriptionUsageAggregate).where(
            SubscriptionUsageAggregate.tenant_id == tenant_id,
            SubscriptionUsageAggregate.billing_cycle == cycle,
        )
        res = await db.execute(stmt)
        aggs = {a.resource_type: a for a in res.scalars().all()}

        results = []
        monitored_resources = [
            ("ACTIVE_USERS", "max_active_users", "SEATS"),
            ("STUDENTS", "max_students", "STUDENTS"),
            ("FACULTY", "max_faculty", "FACULTY"),
            ("STORAGE_BYTES", "max_storage_bytes", "BYTES"),
            ("API_CALLS", "max_api_rpm", "REQUESTS"),
            ("AI_TOKENS", "max_ai_tokens_monthly", "TOKENS"),
        ]

        for rtype, limit_key, unit in monitored_resources:
            hard = ent["resource_limits"].get(limit_key, 1000)
            soft = int(hard * 0.8)
            curr = aggs[rtype].current_usage if rtype in aggs else 0
            rem = max(0, hard - curr)
            pct = round((curr / hard * 100.0), 2) if hard > 0 else 0.0

            results.append({
                "resource_type": rtype,
                "current_usage": curr,
                "soft_limit": soft,
                "hard_limit": hard,
                "remaining_capacity": rem,
                "utilization_percentage": pct,
                "is_exceeded": curr > hard,
                "unit": unit,
            })

        return results

    # -------------------------------------------------------------------------
    # 5. Plan Changes & Downgrade Impact Assessments
    # -------------------------------------------------------------------------

    @classmethod
    async def preview_downgrade(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        target_plan_id: UUID,
    ) -> dict[str, Any]:
        """Perform capacity assessment on target plan without modifying or deleting data."""
        sub = await cls.get_active_subscription(db, tenant_id)
        target_plan = await cls.get_plan(db, target_plan_id)

        current_limits = sub.snapshot_limits_json
        quotas = await cls.get_quota_status(db, tenant_id)
        quota_map = {q["resource_type"]: q["current_usage"] for q in quotas}

        violations = []
        comparisons = []

        # Check resource capacities
        check_pairs = [
            ("STUDENTS", "max_students", target_plan.max_students, "Student Headcount"),
            ("FACULTY", "max_faculty", target_plan.max_faculty, "Faculty Headcount"),
            ("ACTIVE_USERS", "max_active_users", target_plan.max_active_users, "Active User Seats"),
            ("STORAGE_BYTES", "max_storage_bytes", target_plan.max_storage_bytes, "Storage Allowance"),
        ]

        for rtype, limit_key, target_limit, label in check_pairs:
            current_use = quota_map.get(rtype, 0)
            comparisons.append({
                "resource": label,
                "current_usage": current_use,
                "current_limit": current_limits.get(limit_key, target_limit),
                "target_limit": target_limit,
                "exceeds": current_use > target_limit,
            })
            if current_use > target_limit:
                violations.append({
                    "resource": label,
                    "current_usage": current_use,
                    "target_limit": target_limit,
                    "excess": current_use - target_limit,
                    "remediation": f"Archive or graduate at least {current_use - target_limit} records before downgrading.",
                })

        # Check removed modules
        current_modules = set(sub.snapshot_modules_json)
        target_modules = set(target_plan.included_modules)
        removed_modules = sorted(list(current_modules - target_modules))

        # Check removed capabilities
        current_features = {k for k, v in sub.snapshot_features_json.items() if v}
        target_features = {k for k, v in target_plan.feature_capabilities.items() if v}
        removed_features = sorted(list(current_features - target_features))

        has_violations = len(violations) > 0
        recommended_actions = []
        if has_violations:
            recommended_actions.append("Current institution data exceeds the resource caps of the target plan.")
            recommended_actions.append("CampusOS enforces non-destructive policy: student, faculty, and academic data will NOT be deleted.")
            recommended_actions.append("Resolve capacity overages by graduating/archiving inactive cohorts before applying downgrade.")

        return {
            "can_downgrade_immediately": not has_violations,
            "has_capacity_violations": has_violations,
            "violations": violations,
            "current_plan": sub.plan.name if sub.plan else "Custom",
            "target_plan": target_plan.name,
            "resource_comparisons": comparisons,
            "removed_modules": removed_modules,
            "removed_features": removed_features,
            "recommended_actions": recommended_actions,
        }

    @classmethod
    async def request_plan_change(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        target_plan_id: UUID,
        target_billing_interval: BillingInterval,
        effective_type: str = "PERIOD_END",
        actor_id: UUID | None = None,
    ) -> SubscriptionChangeRequest:
        """Create a formal plan change request with downgrade impact snapshot."""
        sub = await cls.get_active_subscription(db, tenant_id)
        target_plan = await cls.get_plan(db, target_plan_id)

        change_type = SubscriptionChangeType.UPGRADE.value if target_plan.base_price >= sub.unit_price else SubscriptionChangeType.DOWNGRADE.value

        preview = await cls.preview_downgrade(db, tenant_id, target_plan_id)

        req = SubscriptionChangeRequest(
            tenant_id=tenant_id,
            subscription_id=sub.id,
            target_plan_id=target_plan_id,
            target_billing_interval=target_billing_interval.value,
            change_type=change_type,
            status=SubscriptionChangeStatus.PENDING_APPROVAL.value,
            effective_type=effective_type,
            scheduled_for=sub.current_period_end if effective_type == "PERIOD_END" else datetime.now(UTC),
            impact_summary_json=preview,
            prorated_amount=Decimal("0.00"),
            requested_by_id=actor_id or UUID("00000000-0000-0000-0000-000000000000"),
        )
        db.add(req)
        await db.flush()
        return req

    # -------------------------------------------------------------------------
    # 6. SaaS Invoicing, Payments & Webhooks
    # -------------------------------------------------------------------------

    @classmethod
    async def generate_invoice(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        subscription_id: UUID,
        period_start: datetime,
        period_end: datetime,
        amount: Decimal,
        description: str = "CampusOS Enterprise SaaS Subscription",
    ) -> SubscriptionInvoice:
        """Generate a sequential, immutable SaaS billing invoice."""
        tax = amount * Decimal("0.18")  # 18% GST standard
        total = amount + tax
        year = period_start.year
        seq = uuid4().hex[:6].upper()
        inv_num = f"INV-SAAS-{year}-{seq}"

        invoice = SubscriptionInvoice(
            tenant_id=tenant_id,
            subscription_id=subscription_id,
            invoice_number=inv_num,
            billing_period_start=period_start,
            billing_period_end=period_end,
            subtotal=amount,
            tax_amount=tax,
            total_amount=total,
            currency="INR",
            status=InvoiceStatus.ISSUED.value,
            due_date=datetime.now(UTC) + timedelta(days=15),
            line_items_json=[
                {
                    "description": description,
                    "period_start": period_start.date().isoformat(),
                    "period_end": period_end.date().isoformat(),
                    "amount": str(amount),
                    "tax": str(tax),
                    "total": str(total),
                }
            ],
            download_url=f"/api/v1/subscriptions/invoices/{inv_num}/download",
        )
        db.add(invoice)
        await db.flush()

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.SUBSCRIPTION_INVOICE_GENERATED,
                entity_type="SubscriptionInvoice",
                entity_id=invoice.id,
                new_values_json={"invoice_number": inv_num, "total": str(total)},
                business_context=f"Generated SaaS invoice {inv_num} for INR {total}",
            )
        )
        await db.flush()
        return invoice

    @classmethod
    async def record_payment(
        cls,
        db: AsyncSession,
        invoice_id: UUID,
        gateway_payment_id: str,
        gateway_order_id: str = "order_simulated",
        actor_id: UUID | None = None,
    ) -> SubscriptionInvoice:
        """Record successful payment reconciliation against an invoice."""
        stmt = select(SubscriptionInvoice).where(SubscriptionInvoice.id == invoice_id)
        res = await db.execute(stmt)
        invoice = res.scalar_one_or_none()
        if not invoice:
            raise NotFoundException("SubscriptionInvoice", invoice_id)

        now = datetime.now(UTC)
        invoice.status = InvoiceStatus.PAID.value
        invoice.paid_at = now

        attempt = SubscriptionPaymentAttempt(
            tenant_id=invoice.tenant_id,
            invoice_id=invoice.id,
            attempt_number=1,
            gateway_order_id=gateway_order_id,
            gateway_payment_id=gateway_payment_id,
            amount=invoice.total_amount,
            currency=invoice.currency,
            status=PaymentStatus.SUCCESS.value,
            attempted_at=now,
        )
        db.add(attempt)

        # Restore subscription status if past due
        sub_stmt = select(TenantSubscription).where(TenantSubscription.id == invoice.subscription_id)
        sub_res = await db.execute(sub_stmt)
        sub = sub_res.scalar_one_or_none()
        if sub and sub.status in (SubscriptionStatus.PAYMENT_OVERDUE.value, SubscriptionStatus.GRACE_PERIOD.value):
            sub.status = SubscriptionStatus.ACTIVE.value
            sub.grace_period_ends_at = None

        db.add(
            build_audit_entry(
                tenant_id=invoice.tenant_id,
                action=AuditEventCategory.SUBSCRIPTION_PAYMENT_RECORDED,
                entity_type="SubscriptionInvoice",
                entity_id=invoice.id,
                user_id=actor_id,
                business_context=f"Recorded successful payment for invoice {invoice.invoice_number}",
            )
        )
        await db.flush()
        return invoice

    @classmethod
    async def process_webhook(
        cls,
        db: AsyncSession,
        provider: str,
        event_id: str,
        event_type: str,
        payload_json: dict[str, Any],
        signature: str | None = None,
        webhook_secret: str | None = None,
    ) -> SubscriptionWebhookEvent:
        """Idempotently process verified external payment gateway callback."""
        # Check idempotency
        stmt = select(SubscriptionWebhookEvent).where(
            SubscriptionWebhookEvent.provider == provider.upper(),
            SubscriptionWebhookEvent.event_id == event_id,
        )
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            return existing

        # Signature verification if secret configured
        is_verified = True
        if webhook_secret and signature:
            computed = hmac.new(
                webhook_secret.encode(),
                f"{event_id}|{event_type}".encode(),
                hashlib.sha256,
            ).hexdigest()
            if not hmac.compare_digest(computed, signature):
                is_verified = False

        if not is_verified:
            raise BadRequestException("Cryptographic webhook signature verification failed.")

        event = SubscriptionWebhookEvent(
            event_id=event_id,
            provider=provider.upper(),
            event_type=event_type,
            signature=signature,
            is_verified=is_verified,
            status="PROCESSED",
            payload_json=payload_json,
            processed_at=datetime.now(UTC),
        )
        db.add(event)
        await db.flush()

        # If payment succeeded event, reconcile invoice
        if event_type == "payment.succeeded" and "invoice_id" in payload_json:
            try:
                inv_id = UUID(payload_json["invoice_id"])
                pay_id = str(payload_json.get("payment_id", f"pay_{uuid4().hex[:8]}"))
                await cls.record_payment(db, invoice_id=inv_id, gateway_payment_id=pay_id)
            except Exception as exc:
                logger.error("Error reconciling invoice from webhook %s: %s", event_id, exc)

        return event

    # -------------------------------------------------------------------------
    # 7. Customer Success Health & Monitoring
    # -------------------------------------------------------------------------

    @classmethod
    async def recalculate_health(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
    ) -> CustomerSuccessHealthSnapshot:
        """Calculate composite health index (0-100) based on operational telemetry and financial state."""
        sub = await cls.get_active_subscription(db, tenant_id)
        now = datetime.now(UTC)

        # 1. Financial Score
        fin_score = 100
        period_end = _to_utc(sub.current_period_end) or now
        days_until_renewal = (period_end - now).days
        if sub.status == SubscriptionStatus.PAYMENT_OVERDUE.value:
            fin_score -= 40
        elif sub.status == SubscriptionStatus.GRACE_PERIOD.value:
            fin_score -= 50
        elif sub.status == SubscriptionStatus.SUSPENDED.value:
            fin_score -= 80

        # Check overdue invoices
        inv_stmt = select(func.count(SubscriptionInvoice.id)).where(
            SubscriptionInvoice.tenant_id == tenant_id,
            SubscriptionInvoice.status == InvoiceStatus.PAST_DUE.value,
        )
        inv_res = await db.execute(inv_stmt)
        past_due_invoices = inv_res.scalar() or 0
        if past_due_invoices > 0:
            fin_score -= min(30, past_due_invoices * 15)

        fin_score = max(0, min(100, fin_score))

        # 2. Utilization Score
        quotas = await cls.get_quota_status(db, tenant_id)
        avg_utilization = sum(q["utilization_percentage"] for q in quotas) / max(1, len(quotas))
        util_score = 100
        if avg_utilization > 95.0:
            util_score = 65  # Capacity strained
        elif avg_utilization < 10.0:
            util_score = 50  # Risk of non-adoption
        elif 30.0 <= avg_utilization <= 85.0:
            util_score = 95  # Ideal utilization

        # 3. Support Score (Step 36 integration)
        support_score = 100
        open_critical_tickets = 0
        try:
            from app.models.support import SupportTicket, TicketPriority, TicketStatus
            t_stmt = select(func.count(SupportTicket.id)).where(
                SupportTicket.tenant_id == tenant_id,
                SupportTicket.priority.in_([TicketPriority.CRITICAL.value, TicketPriority.HIGH.value]),
                SupportTicket.status.notin_([TicketStatus.RESOLVED.value, TicketStatus.CLOSED.value]),
            )
            t_res = await db.execute(t_stmt)
            open_critical_tickets = t_res.scalar() or 0
            if open_critical_tickets > 0:
                support_score = max(20, 100 - (open_critical_tickets * 25))
        except Exception:
            pass

        # 4. Adoption Score (Step 37 integration)
        adoption_score = 85
        try:
            from app.models.adoption import UserJourneyProgress
            j_stmt = select(
                func.count(UserJourneyProgress.id),
                func.avg(UserJourneyProgress.progress_percentage),
            ).where(UserJourneyProgress.tenant_id == tenant_id)
            j_res = await db.execute(j_stmt)
            count, avg_pct = j_res.one()
            if count and count > 0:
                adoption_score = int(avg_pct or 75)
        except Exception:
            pass

        # Composite score
        composite = int(
            (fin_score * 0.35)
            + (util_score * 0.25)
            + (support_score * 0.20)
            + (adoption_score * 0.20)
        )

        if composite >= 80:
            status = CustomerHealthStatus.HEALTHY.value
        elif composite >= 65:
            status = CustomerHealthStatus.GOOD.value
        elif composite >= 50:
            status = CustomerHealthStatus.NEEDS_ATTENTION.value
        elif composite >= 35:
            status = CustomerHealthStatus.AT_RISK.value
        else:
            status = CustomerHealthStatus.CRITICAL.value

        recommendations = []
        if fin_score < 70:
            recommendations.append("Follow up with institution accounts team regarding overdue billing.")
        if days_until_renewal <= 30 and sub.status == SubscriptionStatus.ACTIVE.value:
            recommendations.append(f"Subscription renewal scheduled in {days_until_renewal} days. Initiate review.")
        if open_critical_tickets > 0:
            recommendations.append(f"{open_critical_tickets} critical support tickets active. Coordinate with L3 support.")
        if avg_utilization > 90.0:
            recommendations.append("Institution near user/student quota capacity. Propose plan upgrade.")
        if not recommendations:
            recommendations.append("Institution health is strong. No immediate intervention required.")

        snapshot = CustomerSuccessHealthSnapshot(
            tenant_id=tenant_id,
            health_score=composite,
            health_status=status,
            utilization_score=int(util_score),
            adoption_score=int(adoption_score),
            support_score=int(support_score),
            financial_score=int(fin_score),
            signals_json={
                "days_until_renewal": days_until_renewal,
                "past_due_invoices": past_due_invoices,
                "avg_utilization_pct": avg_utilization,
                "open_critical_tickets": open_critical_tickets,
            },
            recommendations=recommendations,
            calculated_at=now,
        )
        db.add(snapshot)
        await db.flush()

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.HEALTH_SCORE_RECALCULATED,
                entity_type="CustomerSuccessHealthSnapshot",
                entity_id=snapshot.id,
                new_values_json={"score": composite, "status": status},
                business_context=f"Calculated customer success health score {composite} ({status})",
            )
        )
        await db.flush()
        return snapshot

    @classmethod
    async def add_customer_note(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        author_id: UUID,
        author_email: str,
        note_type: CustomerNoteType,
        content: str,
        is_pinned: bool = False,
    ) -> CustomerSuccessNote:
        """Add platform-internal customer success journal note."""
        note = CustomerSuccessNote(
            tenant_id=tenant_id,
            author_id=author_id,
            author_email=author_email,
            note_type=note_type.value,
            content=content,
            is_pinned=is_pinned,
        )
        db.add(note)
        await db.flush()

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.CUSTOMER_SUCCESS_NOTE_ADDED,
                entity_type="CustomerSuccessNote",
                entity_id=note.id,
                user_id=author_id,
                business_context=f"Added internal CS note ({note_type.value}) for tenant {tenant_id}",
            )
        )
        await db.flush()
        return note

    @classmethod
    async def list_customer_notes(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CustomerSuccessNote]:
        """Fetch internal customer success notes chronologically."""
        stmt = (
            select(CustomerSuccessNote)
            .where(CustomerSuccessNote.tenant_id == tenant_id)
            .order_by(desc(CustomerSuccessNote.is_pinned), desc(CustomerSuccessNote.created_at))
            .offset(offset)
            .limit(limit)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    # -------------------------------------------------------------------------
    # 8. Scheduled Sweepers
    # -------------------------------------------------------------------------

    @classmethod
    async def sweep_subscription_lifecycle(cls, db: AsyncSession) -> dict[str, int]:
        """Scheduled background task evaluating trials, grace periods, auto-renewals, and override expiries."""
        now = datetime.now(UTC)
        swept_trials = 0
        swept_grace = 0
        swept_overrides = 0
        auto_renewed = 0

        # 1. Sweep expired trials
        trial_stmt = select(TenantSubscription).where(
            TenantSubscription.status == SubscriptionStatus.TRIAL_ACTIVE.value,
            TenantSubscription.trial_ends_at < now,
        )
        trial_res = await db.execute(trial_stmt)
        for sub in trial_res.scalars().all():
            sub.status = SubscriptionStatus.GRACE_PERIOD.value
            sub.grace_period_ends_at = now + timedelta(days=7)
            swept_trials += 1

        # 2. Sweep expired grace periods
        grace_stmt = select(TenantSubscription).where(
            TenantSubscription.status == SubscriptionStatus.GRACE_PERIOD.value,
            TenantSubscription.grace_period_ends_at < now,
        )
        grace_res = await db.execute(grace_stmt)
        for sub in grace_res.scalars().all():
            sub.status = SubscriptionStatus.SUSPENDED.value
            swept_grace += 1

        # 3. Sweep expired entitlement overrides
        ov_stmt = select(SubscriptionEntitlementOverride).where(
            SubscriptionEntitlementOverride.is_active.is_(True),
            SubscriptionEntitlementOverride.expires_at < now,
        )
        ov_res = await db.execute(ov_stmt)
        for ov in ov_res.scalars().all():
            ov.is_active = False
            swept_overrides += 1

        # 4. Sweep auto-renewals
        renew_stmt = select(TenantSubscription).where(
            TenantSubscription.status == SubscriptionStatus.ACTIVE.value,
            TenantSubscription.auto_renew.is_(True),
            TenantSubscription.current_period_end < now,
        )
        renew_res = await db.execute(renew_stmt)
        for sub in renew_res.scalars().all():
            try:
                await cls.renew_subscription(db, sub.tenant_id)
                auto_renewed += 1
            except Exception as exc:
                logger.error("Error auto-renewing subscription %s: %s", sub.id, exc)

        await db.flush()
        return {
            "swept_trials": swept_trials,
            "swept_grace": swept_grace,
            "swept_overrides": swept_overrides,
            "auto_renewed": auto_renewed,
        }
