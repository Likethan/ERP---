"""Subscription, Licensing & Feature Entitlement Service for CampusOS (Step 30).

Governs centralized entitlement validation, plan tiers, module access boundaries,
trial expirations, and auditable entitlement modifications.
"""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditEventCategory, build_audit_entry
from app.core.cache import tenant_cache
from app.core.exceptions import (
    EntitlementExceededException,
    FeatureNotEntitledException,
    NotFoundException,
)
from app.models.core import Institution
from app.models.platform_ops import (
    PlatformPlanTier,
    TenantEntitlement,
)
from app.schemas.platform_ops import TenantEntitlementUpdateRequest
from app.services.module_configuration_service import ModuleConfigurationService


class EntitlementService:
    """Authoritative service for plan packaging, feature gates, and licensing boundaries."""

    # Standard packaging tiers
    PLAN_DEFAULTS: dict[str, dict[str, Any]] = {
        PlatformPlanTier.FREE.value: {
            "max_users": 100,
            "max_campuses": 1,
            "max_storage_bytes": 5 * 1024 * 1024 * 1024,  # 5 GB
            "max_api_rpm": 60,
            "max_ai_tokens_monthly": 0,
            "enabled_modules": ["ACADEMICS", "ATTENDANCE"],
            "feature_entitlements": {
                "ai_assistant": False,
                "advanced_analytics": False,
                "sso_federation": False,
                "custom_webhooks": False,
                "sla_governance": False,
            },
        },
        PlatformPlanTier.STARTER.value: {
            "max_users": 500,
            "max_campuses": 2,
            "max_storage_bytes": 20 * 1024 * 1024 * 1024,  # 20 GB
            "max_api_rpm": 120,
            "max_ai_tokens_monthly": 100000,
            "enabled_modules": ["ACADEMICS", "ATTENDANCE", "EXAMINATION", "FINANCE", "DOCUMENTS"],
            "feature_entitlements": {
                "ai_assistant": True,
                "advanced_analytics": False,
                "sso_federation": False,
                "custom_webhooks": False,
                "sla_governance": False,
            },
        },
        PlatformPlanTier.PROFESSIONAL.value: {
            "max_users": 2500,
            "max_campuses": 5,
            "max_storage_bytes": 100 * 1024 * 1024 * 1024,  # 100 GB
            "max_api_rpm": 300,
            "max_ai_tokens_monthly": 1000000,
            "enabled_modules": [
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
            ],
            "feature_entitlements": {
                "ai_assistant": True,
                "advanced_analytics": True,
                "sso_federation": True,
                "custom_webhooks": True,
                "sla_governance": False,
            },
        },
        PlatformPlanTier.ENTERPRISE.value: {
            "max_users": 50000,
            "max_campuses": 50,
            "max_storage_bytes": 1024 * 1024 * 1024 * 1024,  # 1 TB
            "max_api_rpm": 1000,
            "max_ai_tokens_monthly": 10000000,
            "enabled_modules": ModuleConfigurationService.DEFAULT_MODULES,
            "feature_entitlements": {
                "ai_assistant": True,
                "advanced_analytics": True,
                "sso_federation": True,
                "custom_webhooks": True,
                "sla_governance": True,
                "case_management": True,
            },
        },
    }

    @classmethod
    async def get_or_create_entitlements(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        plan: str = PlatformPlanTier.ENTERPRISE.value,
        is_trial: bool = False,
        trial_days: int = 14,
    ) -> TenantEntitlement:
        """Fetch or initialize authoritative tenant entitlement configuration."""
        stmt = select(TenantEntitlement).where(TenantEntitlement.tenant_id == tenant_id)
        result = await db.execute(stmt)
        ent = result.scalar_one_or_none()
        if ent:
            return ent

        plan_key = plan.upper() if plan.upper() in cls.PLAN_DEFAULTS else PlatformPlanTier.ENTERPRISE.value
        defaults = cls.PLAN_DEFAULTS[plan_key]
        now = datetime.now(UTC)

        trial_ends_at = now + timedelta(days=trial_days) if is_trial else None
        grace_period_ends_at = trial_ends_at + timedelta(days=7) if is_trial else None

        ent = TenantEntitlement(
            tenant_id=tenant_id,
            plan=plan_key,
            max_users=defaults["max_users"],
            max_campuses=defaults["max_campuses"],
            max_storage_bytes=defaults["max_storage_bytes"],
            max_api_rpm=defaults["max_api_rpm"],
            max_ai_tokens_monthly=defaults["max_ai_tokens_monthly"],
            enabled_modules=list(defaults["enabled_modules"]),
            feature_entitlements=dict(defaults["feature_entitlements"]),
            is_trial=is_trial,
            trial_ends_at=trial_ends_at,
            grace_period_ends_at=grace_period_ends_at,
            custom_limits={},
        )
        db.add(ent)
        await db.flush()
        return ent

    @classmethod
    async def get_entitlements(cls, db: AsyncSession, tenant_id: UUID) -> TenantEntitlement:
        """Fetch tenant entitlements, creating default if not yet initialized."""
        # Check tenant exists
        t_stmt = select(Institution).where(Institution.id == tenant_id)
        t_res = await db.execute(t_stmt)
        tenant = t_res.scalar_one_or_none()
        if not tenant:
            raise NotFoundException("Tenant", tenant_id)

        plan = (tenant.plan or PlatformPlanTier.ENTERPRISE.value).upper()
        return await cls.get_or_create_entitlements(db, tenant_id, plan=plan)

    @classmethod
    async def update_entitlements(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        dto: TenantEntitlementUpdateRequest,
        actor_id: UUID | None = None,
    ) -> TenantEntitlement:
        """Apply administrative entitlement overrides and record forensic audit."""
        ent = await cls.get_entitlements(db, tenant_id)
        old_values = {
            "plan": ent.plan,
            "max_users": ent.max_users,
            "enabled_modules": ent.enabled_modules,
            "feature_entitlements": ent.feature_entitlements,
        }

        if dto.plan:
            plan_upper = dto.plan.upper()
            ent.plan = plan_upper
            # If switching plan and fields not explicitly overridden, adopt plan defaults
            if plan_upper in cls.PLAN_DEFAULTS:
                defaults = cls.PLAN_DEFAULTS[plan_upper]
                if dto.max_users is None:
                    ent.max_users = defaults["max_users"]
                if dto.max_campuses is None:
                    ent.max_campuses = defaults["max_campuses"]
                if dto.max_storage_bytes is None:
                    ent.max_storage_bytes = defaults["max_storage_bytes"]
                if dto.max_api_rpm is None:
                    ent.max_api_rpm = defaults["max_api_rpm"]
                if dto.max_ai_tokens_monthly is None:
                    ent.max_ai_tokens_monthly = defaults["max_ai_tokens_monthly"]
                if dto.enabled_modules is None:
                    ent.enabled_modules = list(defaults["enabled_modules"])
                if dto.feature_entitlements is None:
                    ent.feature_entitlements = dict(defaults["feature_entitlements"])

        if dto.max_users is not None:
            ent.max_users = dto.max_users
        if dto.max_campuses is not None:
            ent.max_campuses = dto.max_campuses
        if dto.max_storage_bytes is not None:
            ent.max_storage_bytes = dto.max_storage_bytes
        if dto.max_api_rpm is not None:
            ent.max_api_rpm = dto.max_api_rpm
        if dto.max_ai_tokens_monthly is not None:
            ent.max_ai_tokens_monthly = dto.max_ai_tokens_monthly
        if dto.enabled_modules is not None:
            ent.enabled_modules = [m.upper() for m in dto.enabled_modules]
        if dto.feature_entitlements is not None:
            ent.feature_entitlements = {**ent.feature_entitlements, **dto.feature_entitlements}
        if dto.custom_limits is not None:
            ent.custom_limits = {**ent.custom_limits, **dto.custom_limits}
        if dto.is_trial is not None:
            ent.is_trial = dto.is_trial
        if dto.trial_ends_at is not None:
            ent.trial_ends_at = dto.trial_ends_at
        if dto.grace_period_ends_at is not None:
            ent.grace_period_ends_at = dto.grace_period_ends_at

        ent.updated_by_id = actor_id

        # Update institution plan if plan was updated
        if dto.plan:
            inst_stmt = select(Institution).where(Institution.id == tenant_id)
            inst_res = await db.execute(inst_stmt)
            inst = inst_res.scalar_one_or_none()
            if inst:
                inst.plan = ent.plan

        new_values = {
            "plan": ent.plan,
            "max_users": ent.max_users,
            "enabled_modules": ent.enabled_modules,
            "feature_entitlements": ent.feature_entitlements,
        }

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.TENANT_ENTITLEMENT_UPDATED,
                entity_type="TenantEntitlement",
                entity_id=ent.id,
                user_id=actor_id,
                old_values_json=old_values,
                new_values_json=new_values,
                business_context=f"Tenant entitlements updated. Plan: {ent.plan}",
            )
        )

        await db.flush()
        await tenant_cache.invalidate_namespace(tenant_id, "entitlements")
        return ent

    @classmethod
    async def is_module_entitled(cls, db: AsyncSession, tenant_id: UUID, module_name: str) -> bool:
        """Check whether a specific module is entitled for this tenant."""
        ent = await cls.get_entitlements(db, tenant_id)
        return module_name.upper() in [m.upper() for m in ent.enabled_modules]

    @classmethod
    async def is_feature_entitled(cls, db: AsyncSession, tenant_id: UUID, feature_key: str) -> bool:
        """Check whether a specific feature flag is entitled under tenant plan."""
        ent = await cls.get_entitlements(db, tenant_id)
        return bool(ent.feature_entitlements.get(feature_key, False))

    @classmethod
    async def assert_module_entitled(cls, db: AsyncSession, tenant_id: UUID, module_name: str) -> None:
        """Enforce module entitlement, raising an explicit EntitlementExceededException if unavailable."""
        if not await cls.is_module_entitled(db, tenant_id, module_name):
            ent = await cls.get_entitlements(db, tenant_id)
            raise EntitlementExceededException(
                feature_or_module=module_name,
                plan=ent.plan,
                message=f"Module '{module_name}' is not entitled under your current '{ent.plan}' plan.",
            )

    @classmethod
    async def assert_feature_entitled(cls, db: AsyncSession, tenant_id: UUID, feature_key: str) -> None:
        """Enforce feature entitlement, raising FeatureNotEntitledException if disabled in plan."""
        if not await cls.is_feature_entitled(db, tenant_id, feature_key):
            ent = await cls.get_entitlements(db, tenant_id)
            raise FeatureNotEntitledException(feature_key=feature_key, plan=ent.plan)

    @classmethod
    async def evaluate_trial_status(cls, db: AsyncSession, tenant_id: UUID) -> dict[str, Any]:
        """Check trial expiration and grace period state."""
        ent = await cls.get_entitlements(db, tenant_id)
        if not ent.is_trial or not ent.trial_ends_at:
            return {"is_trial": False, "is_expired": False, "in_grace_period": False}

        now = datetime.now(UTC)
        trial_ends = ent.trial_ends_at if ent.trial_ends_at.tzinfo else ent.trial_ends_at.replace(tzinfo=UTC)
        is_expired = now > trial_ends

        in_grace = False
        if is_expired and ent.grace_period_ends_at:
            grace_ends = (
                ent.grace_period_ends_at
                if ent.grace_period_ends_at.tzinfo
                else ent.grace_period_ends_at.replace(tzinfo=UTC)
            )
            in_grace = now <= grace_ends

        days_remaining = max(0, (trial_ends - now).days) if not is_expired else 0

        return {
            "is_trial": True,
            "is_expired": is_expired,
            "in_grace_period": in_grace,
            "trial_ends_at": ent.trial_ends_at.isoformat(),
            "days_remaining": days_remaining,
        }
