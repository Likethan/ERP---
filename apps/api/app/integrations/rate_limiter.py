"""Tenant and Connector-Aware Integration Rate Limiter.

Enforces:
- Sliding window throughput controls per connector and tenant.
- Burst limit and per-minute quotas preventing external API exhaustion and 429 penalties.
- Isolated fault domains: one tenant's heavy traffic cannot starve another tenant's connector.
"""

import threading
from collections import defaultdict
from datetime import UTC, datetime
from uuid import UUID

from app.core.exceptions import TooManyRequestsException


class ConnectorRateLimiter:
    """Sliding window rate limiter for external connector traffic."""

    def __init__(self):
        self._lock = threading.Lock()
        self._timestamps: dict[str, list[float]] = defaultdict(list)

    def is_allowed(
        self,
        tenant_id: UUID | str | None,
        connector_id: UUID | str,
        limit_per_minute: int = 120,
        burst_limit: int = 30,
        window_seconds: int = 60,
        now: float | None = None,
    ) -> tuple[bool, int]:
        """Check if request through connector is permitted under configured limits.

        Returns:
            (allowed: bool, retry_after_seconds: int)
        """
        current_ts = now if now is not None else datetime.now(UTC).timestamp()
        key = f"int_rl:{tenant_id}:{connector_id}"
        cutoff = current_ts - window_seconds

        with self._lock:
            history = [t for t in self._timestamps[key] if t > cutoff]

            # 1. Burst limit check (last 1 second)
            recent_second = [t for t in history if t > current_ts - 1.0]
            if len(recent_second) >= burst_limit:
                self._timestamps[key] = history
                return False, 1

            # 2. Per-window limit check
            if len(history) >= limit_per_minute:
                oldest = history[0]
                retry_after = max(1, int(oldest + window_seconds - current_ts))
                self._timestamps[key] = history
                return False, retry_after

            # Allowed
            history.append(current_ts)
            self._timestamps[key] = history
            return True, 0

    def check_or_raise(
        self,
        tenant_id: UUID | str | None,
        connector_id: UUID | str,
        limit_per_minute: int = 120,
        burst_limit: int = 30,
    ) -> None:
        """Convenience method raising TooManyRequestsException if throttled."""
        allowed, retry_after = self.is_allowed(
            tenant_id=tenant_id,
            connector_id=connector_id,
            limit_per_minute=limit_per_minute,
            burst_limit=burst_limit,
        )
        if not allowed:
            raise TooManyRequestsException(
                f"Connector rate limit exceeded. Retry after {retry_after} seconds."
            )

    def reset(self) -> None:
        """Clear rate limit counters (useful in unit tests)."""
        with self._lock:
            self._timestamps.clear()


connector_rate_limiter = ConnectorRateLimiter()
