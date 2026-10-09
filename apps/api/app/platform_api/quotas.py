"""Aggregate Multi-Period API Quotas & Abuse Prevention (Step 21).

Enforces:
- Daily and monthly aggregate consumption caps per application and tenant.
- Quota states: AVAILABLE (<80%), WARNING (>=80%), EXCEEDED (>=100%), SUSPENDED.
- Anti-bypass protection: Quotas track strictly against the application entity,
  preventing quota circumvention through credential generation or parallel workers.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Final
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import CampusOSException
from app.platform_api.models import (
    ApiQuotaUsage,
    DeveloperApplication,
    QuotaStatus,
    QuotaTier,
)


class QuotaExceededException(CampusOSException):
    def __init__(self, message: str = "Application aggregate API quota has been exceeded."):
        super().__init__(
            status_code=429,
            code="QUOTA_EXCEEDED",
            message=message,
        )


@dataclass(frozen=True)
class QuotaPolicy:
    daily_requests: int
    monthly_requests: int
    daily_exports: int
    daily_webhooks: int


TIER_QUOTA_POLICIES: Final[dict[str, QuotaPolicy]] = {
    QuotaTier.DEFAULT.value: QuotaPolicy(
        daily_requests=10_000,
        monthly_requests=200_000,
        daily_exports=50,
        daily_webhooks=1_000,
    ),
    QuotaTier.PARTNER.value: QuotaPolicy(
        daily_requests=50_000,
        monthly_requests=1_000_000,
        daily_exports=200,
        daily_webhooks=10_000,
    ),
    QuotaTier.ENTERPRISE.value: QuotaPolicy(
        daily_requests=200_000,
        monthly_requests=5_000_000,
        daily_exports=1_000,
        daily_webhooks=50_000,
    ),
    QuotaTier.INTERNAL.value: QuotaPolicy(
        daily_requests=1_000_000,
        monthly_requests=25_000_000,
        daily_exports=5_000,
        daily_webhooks=200_000,
    ),
}


class QuotaService:
    """Manages multi-period aggregate quota consumption and lifecycle states."""

    @classmethod
    def resolve_policy(
        cls,
        tier: str,
        custom: dict[str, Any] | None = None,
    ) -> QuotaPolicy:
        """Resolve effective quota policy applying custom overrides if present."""
        base = TIER_QUOTA_POLICIES.get(tier.upper(), TIER_QUOTA_POLICIES[QuotaTier.DEFAULT.value])
        if not custom:
            return base

        return QuotaPolicy(
            daily_requests=custom.get("daily_requests", base.daily_requests),
            monthly_requests=custom.get("monthly_requests", base.monthly_requests),
            daily_exports=custom.get("daily_exports", base.daily_exports),
            daily_webhooks=custom.get("daily_webhooks", base.daily_webhooks),
        )

    @classmethod
    async def get_or_create_usage(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        application_id: UUID,
        period: str,
        period_type: str,
    ) -> ApiQuotaUsage:
        """Retrieve or initialize period tracking record."""
        stmt = select(ApiQuotaUsage).where(
            ApiQuotaUsage.tenant_id == tenant_id,
            ApiQuotaUsage.application_id == application_id,
            ApiQuotaUsage.period == period,
            ApiQuotaUsage.period_type == period_type,
        )
        res = await db.execute(stmt)
        record = res.scalar_one_or_none()
        if not record:
            record = ApiQuotaUsage(
                tenant_id=tenant_id,
                application_id=application_id,
                period=period,
                period_type=period_type,
                requests_count=0,
                data_exports_count=0,
                webhook_deliveries_count=0,
                status=QuotaStatus.AVAILABLE.value,
            )
            db.add(record)
            await db.flush()
        return record

    @classmethod
    async def check_and_consume(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        application: DeveloperApplication,
        units: int = 1,
        is_export: bool = False,
        is_webhook: bool = False,
    ) -> None:
        """Evaluate quota status and record consumption.

        Raises QuotaExceededException if daily or monthly limits are exceeded.
        """
        if application.quota_status == QuotaStatus.SUSPENDED.value:
            raise QuotaExceededException("Application quota access is suspended by administration.")

        policy = cls.resolve_policy(application.quota_tier, application.quota_custom)
        now = datetime.now(UTC)
        daily_period = now.strftime("%Y-%m-%d")
        monthly_period = now.strftime("%Y-%m")

        # 1. Daily tracking
        daily = await cls.get_or_create_usage(db, tenant_id, application.id, daily_period, "DAILY")
        if daily.requests_count + units > policy.daily_requests:
            daily.status = QuotaStatus.EXCEEDED.value
            application.quota_status = QuotaStatus.EXCEEDED.value
            await db.flush()
            raise QuotaExceededException(
                f"Application daily API request quota ({policy.daily_requests}) exceeded."
            )

        # 2. Monthly tracking
        monthly = await cls.get_or_create_usage(
            db, tenant_id, application.id, monthly_period, "MONTHLY"
        )
        if monthly.requests_count + units > policy.monthly_requests:
            monthly.status = QuotaStatus.EXCEEDED.value
            application.quota_status = QuotaStatus.EXCEEDED.value
            await db.flush()
            raise QuotaExceededException(
                f"Application monthly API request quota ({policy.monthly_requests}) exceeded."
            )

        # 3. Export limit check
        if is_export and (daily.data_exports_count + 1 > policy.daily_exports):
            raise QuotaExceededException(
                f"Application daily data export quota ({policy.daily_exports}) exceeded."
            )

        # Increment counters
        daily.requests_count += units
        monthly.requests_count += units
        if is_export:
            daily.data_exports_count += 1
            monthly.data_exports_count += 1
        if is_webhook:
            daily.webhook_deliveries_count += 1
            monthly.webhook_deliveries_count += 1

        # Evaluate Warning status (>= 80%)
        daily_ratio = daily.requests_count / max(1, policy.daily_requests)
        monthly_ratio = monthly.requests_count / max(1, policy.monthly_requests)
        if daily_ratio >= 0.8 or monthly_ratio >= 0.8:
            daily.status = QuotaStatus.WARNING.value
            application.quota_status = QuotaStatus.WARNING.value
        else:
            daily.status = QuotaStatus.AVAILABLE.value
            application.quota_status = QuotaStatus.AVAILABLE.value

        await db.flush()


quota_service = QuotaService()
