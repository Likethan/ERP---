"""Tenant Resource Governance & Quota Management Service for CampusOS (Step 30).

Provides centralized tracking, concurrency-safe limit enforcement, advisory warning
threshold notifications, and administrative quota adjustments.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditEventCategory, build_audit_entry
from app.core.events import DomainEventEnvelope, OutboxService
from app.core.exceptions import (
    NotFoundException,
    QuotaExceededException,
)
from app.models.platform_ops import (
    TenantEntitlement,
    TenantResourceQuotaUsage,
    TenantResourceType,
)
from app.schemas.platform_ops import (
    TenantQuotaItemResponse,
    TenantQuotaOverrideRequest,
    TenantQuotaSummaryResponse,
)
from app.services.entitlement_service import EntitlementService


class TenantQuotaService:
    """Centralized governance for multi-tenant resource quotas and consumption."""

    RESOURCE_CONFIGS = {
        TenantResourceType.ACTIVE_USERS.value: {
            "unit": "COUNT",
            "entitlement_key": "max_users",
            "default_hard": 10000,
        },
        TenantResourceType.CAMPUS_COUNT.value: {
            "unit": "COUNT",
            "entitlement_key": "max_campuses",
            "default_hard": 10,
        },
        TenantResourceType.STORAGE_BYTES.value: {
            "unit": "BYTES",
            "entitlement_key": "max_storage_bytes",
            "default_hard": 107374182400,
        },
        TenantResourceType.API_CALLS_MONTHLY.value: {
            "unit": "REQUESTS",
            "entitlement_key": "max_api_rpm",
            "default_hard": 1000000,
        },
        TenantResourceType.AI_TOKENS_MONTHLY.value: {
            "unit": "TOKENS",
            "entitlement_key": "max_ai_tokens_monthly",
            "default_hard": 1000000,
        },
        TenantResourceType.ENABLED_MODULES.value: {
            "unit": "MODULES",
            "entitlement_key": None,
            "default_hard": 15,
        },
    }

    @classmethod
    async def ensure_tenant_quotas(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
    ) -> list[TenantResourceQuotaUsage]:
        """Ensure all standard resource quota rows exist for a tenant."""
        ent = await EntitlementService.get_entitlements(db, tenant_id)

        stmt = select(TenantResourceQuotaUsage).where(
            TenantResourceQuotaUsage.tenant_id == tenant_id
        )
        res = await db.execute(stmt)
        existing = {q.resource_type: q for q in res.scalars().all()}

        results = []
        for rtype, conf in cls.RESOURCE_CONFIGS.items():
            if rtype in existing:
                results.append(existing[rtype])
                continue

            hard_limit = conf["default_hard"]
            if conf["entitlement_key"] and hasattr(ent, conf["entitlement_key"]):
                hard_limit = getattr(ent, conf["entitlement_key"])

            soft_limit = int(hard_limit * 0.8)
            quota = TenantResourceQuotaUsage(
                tenant_id=tenant_id,
                resource_type=rtype,
                current_usage=0,
                soft_limit=soft_limit,
                hard_limit=hard_limit,
                unit=conf["unit"],
                warning_threshold_percent=80,
                is_exceeded=False,
            )
            db.add(quota)
            results.append(quota)

        await db.flush()
        return results

    @classmethod
    async def get_quota_summary(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
    ) -> TenantQuotaSummaryResponse:
        """Retrieve aggregated resource consumption and threshold status."""
        quotas = await cls.ensure_tenant_quotas(db, tenant_id)
        items = []

        for q in quotas:
            pct = round((q.current_usage / max(q.hard_limit, 1)) * 100.0, 2)
            is_warning = pct >= q.warning_threshold_percent
            is_exceeded = q.current_usage >= q.hard_limit

            items.append(
                TenantQuotaItemResponse(
                    resource_type=q.resource_type,
                    current_usage=q.current_usage,
                    soft_limit=q.soft_limit,
                    hard_limit=q.hard_limit,
                    unit=q.unit,
                    percentage_used=pct,
                    is_exceeded=is_exceeded,
                    is_warning=is_warning,
                    warning_threshold_percent=q.warning_threshold_percent,
                )
            )

        return TenantQuotaSummaryResponse(tenant_id=tenant_id, quotas=items)

    @classmethod
    async def check_and_consume_quota(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        resource_type: str,
        amount: int = 1,
    ) -> None:
        """Atomically validate capacity and reserve quota units under concurrency protection."""
        await cls.ensure_tenant_quotas(db, tenant_id)

        stmt = (
            select(TenantResourceQuotaUsage)
            .where(
                TenantResourceQuotaUsage.tenant_id == tenant_id,
                TenantResourceQuotaUsage.resource_type == resource_type,
            )
            .with_for_update()
        )
        res = await db.execute(stmt)
        quota = res.scalar_one_or_none()
        if not quota:
            return

        new_usage = quota.current_usage + amount

        # Hard limit validation
        if quota.hard_limit > 0 and new_usage > quota.hard_limit:
            quota.is_exceeded = True
            await db.flush()
            raise QuotaExceededException(
                resource_type=resource_type,
                current=new_usage,
                limit=quota.hard_limit,
            )

        quota.current_usage = new_usage
        quota.is_exceeded = False

        # Advisory warning threshold trigger (emitted once when threshold crossed)
        if quota.hard_limit > 0 and new_usage >= quota.soft_limit and not quota.warning_sent_at:
            quota.warning_sent_at = datetime.now(UTC)
            try:
                event = DomainEventEnvelope.create(
                    event_type="tenant.quota.threshold_warning",
                    tenant_id=tenant_id,
                    payload={
                        "tenant_id": str(tenant_id),
                        "resource_type": resource_type,
                        "current_usage": new_usage,
                        "soft_limit": quota.soft_limit,
                        "hard_limit": quota.hard_limit,
                        "unit": quota.unit,
                    },
                    aggregate_type="TenantResourceQuotaUsage",
                    aggregate_id=quota.id,
                )
                await OutboxService.create_event(db, event)
            except Exception as ev_err:
                logger.warning("Failed to emit outbox event for quota warning: %s", ev_err)

        await db.flush()

    @classmethod
    async def record_usage(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        resource_type: str,
        current_value: int,
    ) -> TenantResourceQuotaUsage:
        """Synchronize calculated metric measurement into quota usage tracking."""
        await cls.ensure_tenant_quotas(db, tenant_id)

        stmt = (
            select(TenantResourceQuotaUsage)
            .where(
                TenantResourceQuotaUsage.tenant_id == tenant_id,
                TenantResourceQuotaUsage.resource_type == resource_type,
            )
            .with_for_update()
        )
        res = await db.execute(stmt)
        quota = res.scalar_one_or_none()
        if quota:
            quota.current_usage = current_value
            quota.is_exceeded = bool(quota.hard_limit > 0 and current_value > quota.hard_limit)
            await db.flush()
            return quota

        raise NotFoundException("Quota", resource_type)

    @classmethod
    async def override_quota(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        dto: TenantQuotaOverrideRequest,
        actor_id: UUID | None = None,
    ) -> TenantResourceQuotaUsage:
        """Update quota limits with explicit audit logging."""
        await cls.ensure_tenant_quotas(db, tenant_id)

        stmt = select(TenantResourceQuotaUsage).where(
            TenantResourceQuotaUsage.tenant_id == tenant_id,
            TenantResourceQuotaUsage.resource_type == dto.resource_type,
        )
        res = await db.execute(stmt)
        quota = res.scalar_one_or_none()
        if not quota:
            raise NotFoundException("Quota", dto.resource_type)

        old_limits = {
            "hard_limit": quota.hard_limit,
            "soft_limit": quota.soft_limit,
            "warning_threshold_percent": quota.warning_threshold_percent,
        }

        quota.hard_limit = dto.hard_limit
        quota.warning_threshold_percent = dto.warning_threshold_percent
        quota.soft_limit = (
            dto.soft_limit
            if dto.soft_limit is not None
            else int(dto.hard_limit * (dto.warning_threshold_percent / 100.0))
        )
        quota.is_exceeded = bool(dto.hard_limit > 0 and quota.current_usage > dto.hard_limit)
        quota.warning_sent_at = None

        new_limits = {
            "hard_limit": quota.hard_limit,
            "soft_limit": quota.soft_limit,
            "warning_threshold_percent": quota.warning_threshold_percent,
        }

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.TENANT_QUOTA_OVERRIDE,
                entity_type="TenantResourceQuotaUsage",
                entity_id=quota.id,
                user_id=actor_id,
                old_values_json=old_limits,
                new_values_json=new_limits,
                business_context=f"Quota override applied to {dto.resource_type}: hard={dto.hard_limit}",
            )
        )

        await db.flush()
        return quota
