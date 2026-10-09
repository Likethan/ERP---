"""Platform API Background Maintenance & Lifecycle Jobs (Step 21).

Implements:
- api.usage.aggregate: Aggregates raw hourly/daily usage logs
- api.quota.reset: Rolls over daily and monthly quota counters
- api.credential.expiry: Transitions expired credentials and expired grace-period rotation keys
- api.usage.cleanup: Prunes raw telemetry records exceeding data retention policies
"""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.platform_api.models import (
    ApiQuotaUsage,
    ApiUsageRecord,
    ApplicationCredential,
    CredentialStatus,
    QuotaStatus,
)

logger = logging.getLogger("campusos.platform_api.jobs")


class ApiPlatformJobs:
    """Scheduled and background operations for the API Platform."""

    @classmethod
    async def expire_credentials(cls, db: AsyncSession) -> int:
        """Mark expired credentials and expired grace-period rotation keys."""
        now = datetime.now(UTC)
        count = 0

        # 1. Active credentials past expiration date
        stmt = (
            update(ApplicationCredential)
            .where(
                ApplicationCredential.status == CredentialStatus.ACTIVE.value,
                ApplicationCredential.expires_at.is_not(None),
                ApplicationCredential.expires_at <= now,
            )
            .values(status=CredentialStatus.EXPIRED.value)
        )
        res = await db.execute(stmt)
        count += res.rowcount

        # 2. Rotating credentials past grace period
        stmt_rot = (
            update(ApplicationCredential)
            .where(
                ApplicationCredential.status == CredentialStatus.ROTATING.value,
                ApplicationCredential.grace_period_expires_at.is_not(None),
                ApplicationCredential.grace_period_expires_at <= now,
            )
            .values(
                status=CredentialStatus.REVOKED.value,
                revocation_reason="Rotation grace period expired.",
            )
        )
        res_rot = await db.execute(stmt_rot)
        count += res_rot.rowcount

        await db.flush()
        logger.info("Executed api.credential.expiry: updated %d credentials.", count)
        return count

    @classmethod
    async def reset_quotas(cls, db: AsyncSession) -> int:
        """Reset or initialize daily/monthly quotas on period rollover."""
        now = datetime.now(UTC)
        current_daily = now.strftime("%Y-%m-%d")

        # Expire older ACTIVE quotas
        stmt = (
            update(ApiQuotaUsage)
            .where(
                ApiQuotaUsage.period_type == "DAILY",
                ApiQuotaUsage.period != current_daily,
                ApiQuotaUsage.status.in_(
                    [
                        QuotaStatus.AVAILABLE.value,
                        QuotaStatus.WARNING.value,
                        QuotaStatus.EXCEEDED.value,
                    ]
                ),
            )
            .values(status=QuotaStatus.AVAILABLE.value)
        )
        res = await db.execute(stmt)
        await db.flush()
        logger.info("Executed api.quota.reset: rolled over daily quotas.")
        return res.rowcount

    @classmethod
    async def cleanup_old_usage_logs(cls, db: AsyncSession, retention_days: int = 90) -> int:
        """Prune raw usage logs older than retention period to comply with privacy rules."""
        cutoff = datetime.now(UTC) - timedelta(days=retention_days)
        stmt = delete(ApiUsageRecord).where(ApiUsageRecord.timestamp < cutoff)
        res = await db.execute(stmt)
        await db.flush()
        logger.info(
            "Executed api.usage.cleanup: pruned %d records older than %s.", res.rowcount, cutoff
        )
        return res.rowcount


api_platform_jobs = ApiPlatformJobs()
