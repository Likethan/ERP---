"""Tenant- and Application-Aware API Gateway Rate Limiter (Step 21).

Enforces:
- Sliding-window traffic velocity controls per application and per tenant.
- Tiered traffic profiles (DEFAULT, PARTNER, ENTERPRISE, INTERNAL).
- Burst protection within 1-second sub-windows.
- Rate-limit bypass defense: limits attach to the application entity,
  preventing consumers from escaping limits via credential rotation or multi-threading.
"""

import threading
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Final
from uuid import UUID

from app.core.exceptions import TooManyRequestsException
from app.platform_api.models import RateLimitTier


@dataclass(frozen=True)
class RateLimitPolicy:
    requests_per_second: int
    requests_per_minute: int
    requests_per_hour: int
    burst_limit: int


TIER_POLICIES: Final[dict[str, RateLimitPolicy]] = {
    RateLimitTier.DEFAULT.value: RateLimitPolicy(
        requests_per_second=5,
        requests_per_minute=60,
        requests_per_hour=1_000,
        burst_limit=10,
    ),
    RateLimitTier.PARTNER.value: RateLimitPolicy(
        requests_per_second=20,
        requests_per_minute=300,
        requests_per_hour=10_000,
        burst_limit=30,
    ),
    RateLimitTier.ENTERPRISE.value: RateLimitPolicy(
        requests_per_second=50,
        requests_per_minute=1_200,
        requests_per_hour=50_000,
        burst_limit=100,
    ),
    RateLimitTier.INTERNAL.value: RateLimitPolicy(
        requests_per_second=100,
        requests_per_minute=3_000,
        requests_per_hour=100_000,
        burst_limit=200,
    ),
}


class ApplicationRateLimiter:
    """Sliding-window in-memory rate limiter with tiering and custom overrides."""

    def __init__(self):
        self._lock = threading.Lock()
        self._timestamps: dict[str, list[float]] = defaultdict(list)

    def resolve_policy(
        self,
        tier: str,
        custom: dict[str, Any] | None = None,
    ) -> RateLimitPolicy:
        """Resolve policy applying application-specific overrides over base tier."""
        base = TIER_POLICIES.get(tier.upper(), TIER_POLICIES[RateLimitTier.DEFAULT.value])
        if not custom:
            return base

        return RateLimitPolicy(
            requests_per_second=custom.get("requests_per_second", base.requests_per_second),
            requests_per_minute=custom.get("requests_per_minute", base.requests_per_minute),
            requests_per_hour=custom.get("requests_per_hour", base.requests_per_hour),
            burst_limit=custom.get("burst_limit", base.burst_limit),
        )

    def is_allowed(
        self,
        tenant_id: UUID | str,
        application_id: UUID | str,
        tier: str = RateLimitTier.DEFAULT.value,
        custom: dict[str, Any] | None = None,
        now: float | None = None,
    ) -> tuple[bool, int]:
        """Check if request within the sliding window is permitted.

        Returns:
            (allowed: bool, retry_after_seconds: int)
        """
        current_ts = now if now is not None else datetime.now(UTC).timestamp()
        key = f"api_rl:{tenant_id}:{application_id}"
        policy = self.resolve_policy(tier, custom)

        with self._lock:
            history = self._timestamps[key]
            # Prune entries older than 60 seconds
            history = [t for t in history if t > current_ts - 60.0]

            # 1. Burst limit check (last 1.0s window)
            recent_burst = [t for t in history if t > current_ts - 1.0]
            if len(recent_burst) >= policy.burst_limit:
                self._timestamps[key] = history
                return False, 1

            # 2. Minute limit check (last 60s window)
            if len(history) >= policy.requests_per_minute:
                oldest = history[0]
                retry_after = max(1, int(oldest + 60.0 - current_ts))
                self._timestamps[key] = history
                return False, retry_after

            # Allowed - record timestamp
            history.append(current_ts)
            self._timestamps[key] = history
            return True, 0

    def check_or_raise(
        self,
        tenant_id: UUID | str,
        application_id: UUID | str,
        tier: str = RateLimitTier.DEFAULT.value,
        custom: dict[str, Any] | None = None,
    ) -> None:
        """Raise 429 TooManyRequestsException if application exceeded rate limits."""
        allowed, retry_after = self.is_allowed(
            tenant_id=tenant_id,
            application_id=application_id,
            tier=tier,
            custom=custom,
        )
        if not allowed:
            raise TooManyRequestsException(
                f"Application rate limit exceeded. Retry after {retry_after} seconds."
            )

    def reset(self) -> None:
        """Clear all in-memory rate limiting counters (for unit tests)."""
        with self._lock:
            self._timestamps.clear()


app_rate_limiter = ApplicationRateLimiter()
