"""Application-level sliding-window rate limiter for Intelligence queries."""

import time
from collections import defaultdict
from uuid import UUID

from app.core.config import settings
from app.core.exceptions import CampusOSException


class RateLimitExceededException(CampusOSException):
    def __init__(
        self, message: str = "AI rate limit exceeded. Please wait before submitting more queries."
    ):
        super().__init__(status_code=429, code="RATE_LIMIT_EXCEEDED", message=message)


class RateLimitService:
    """In-memory sliding window rate limiter per user and per tenant."""

    def __init__(self) -> None:
        self._user_timestamps: dict[UUID, list[float]] = defaultdict(list)
        self._tenant_timestamps: dict[UUID, list[float]] = defaultdict(list)

    def check_and_record(self, tenant_id: UUID, user_id: UUID) -> None:
        now = time.time()
        window_seconds = 60.0

        # Clean old timestamps
        user_ts = [t for t in self._user_timestamps[user_id] if now - t < window_seconds]
        tenant_ts = [t for t in self._tenant_timestamps[tenant_id] if now - t < window_seconds]

        # Enforce User Rate Limit
        if len(user_ts) >= settings.AI_RATE_LIMIT_PER_MINUTE_USER:
            raise RateLimitExceededException(
                f"User AI query rate limit exceeded ({settings.AI_RATE_LIMIT_PER_MINUTE_USER} queries/min)."
            )

        # Enforce Tenant Rate Limit
        if len(tenant_ts) >= settings.AI_RATE_LIMIT_PER_MINUTE_TENANT:
            raise RateLimitExceededException(
                f"Institution AI query capacity exceeded ({settings.AI_RATE_LIMIT_PER_MINUTE_TENANT} queries/min)."
            )

        # Record invocation
        user_ts.append(now)
        tenant_ts.append(now)
        self._user_timestamps[user_id] = user_ts
        self._tenant_timestamps[tenant_id] = tenant_ts


_global_rate_limiter = RateLimitService()


def get_rate_limiter() -> RateLimitService:
    return _global_rate_limiter
