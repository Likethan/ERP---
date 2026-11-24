"""Background Jobs and Maintenance Tasks for Enterprise Identity Layer (Step 22).

Includes:
- cleanup_expired_sessions: Mark sessions whose hard expiry has elapsed as EXPIRED
- cleanup_expired_challenges: Purge expired MFA challenges and account link requests
- run_identity_provider_health_checks: Periodically monitor active OIDC/OAuth IdP endpoints
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.identity.models import (
    AccountLinkRequest,
    IdentityProvider,
    IdentityProviderStatus,
    IdentitySession,
    MfaChallenge,
    SessionStatus,
)
from app.identity.service import EnterpriseIdentityService

logger = logging.getLogger("campusos.identity.jobs")


async def cleanup_expired_sessions(db: AsyncSession) -> int:
    """Transition past-expiry sessions from ACTIVE to EXPIRED."""
    now = datetime.now(UTC)
    stmt = (
        update(IdentitySession)
        .where(
            IdentitySession.status == SessionStatus.ACTIVE.value,
            IdentitySession.expires_at <= now,
        )
        .values(
            status=SessionStatus.EXPIRED.value,
            revocation_reason="LIFETIME_EXPIRATION",
        )
    )
    res = await db.execute(stmt)
    await db.commit()
    count = res.rowcount
    if count > 0:
        logger.info("Marked %d expired identity sessions as EXPIRED.", count)
    return count


async def cleanup_expired_challenges(db: AsyncSession) -> int:
    """Delete expired ephemeral MFA challenges and uncompleted link requests."""
    now = datetime.now(UTC)

    # 1. MFA challenges
    mfa_stmt = delete(MfaChallenge).where(MfaChallenge.expires_at <= now)
    mfa_res = await db.execute(mfa_stmt)

    # 2. Account link requests
    link_stmt = delete(AccountLinkRequest).where(
        AccountLinkRequest.expires_at <= now,
        AccountLinkRequest.is_completed.is_(False),
    )
    link_res = await db.execute(link_stmt)

    await db.commit()
    total_cleaned = mfa_res.rowcount + link_res.rowcount
    if total_cleaned > 0:
        logger.info("Purged %d expired identity challenges/requests.", total_cleaned)
    return total_cleaned


async def run_identity_provider_health_checks(db: AsyncSession, tenant_id: UUID | None = None) -> int:
    """Execute health checks against active external identity providers."""
    stmt = select(IdentityProvider).where(
        IdentityProvider.status == IdentityProviderStatus.ACTIVE.value
    )
    if tenant_id:
        stmt = stmt.where(IdentityProvider.tenant_id == tenant_id)

    res = await db.execute(stmt)
    providers = res.scalars().all()

    checked_count = 0
    for p in providers:
        try:
            await EnterpriseIdentityService.test_provider_connectivity(
                db, p.tenant_id, p.id
            )
            checked_count += 1
        except Exception as exc:
            logger.error("Health check error for provider %s: %s", p.id, exc)

    return checked_count
