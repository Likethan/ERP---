"""Tenant-aware and Client-aware Rate Limiting engine for CampusOS.

Protects authentication endpoints, AI inference, file uploads, and public APIs
against brute-force, denial-of-service, and resource exhaustion.
Enforces standard RFC/IETF rate limit headers (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset, Retry-After).
"""

from __future__ import annotations

import threading
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from app.core.config import settings
from app.core.metrics import metrics
from app.core.security_events import security_events


class RateLimitDecision(tuple):
    """Immutable rate limit evaluation result that unpacks as (allowed, retry_after, category)
    for 100% backwards compatibility with legacy call sites and tests, while exposing
    rich attributes for RFC/IETF response headers.
    """

    allowed: bool
    retry_after: int
    category: str
    limit: int
    remaining: int
    reset_epoch: int

    def __new__(
        cls,
        allowed: bool,
        retry_after: int,
        category: str,
        limit: int = 120,
        remaining: int = 120,
        reset_epoch: int = 0,
    ):
        instance = super().__new__(cls, (allowed, retry_after, category))
        instance.allowed = allowed
        instance.retry_after = retry_after
        instance.category = category
        instance.limit = limit
        instance.remaining = remaining
        instance.reset_epoch = reset_epoch
        return instance


class SlidingWindowRateLimiter:
    """In-memory sliding window rate limiter with per-route tiering, standard headers, and tenant fairness."""

    def __init__(self):
        self._lock = threading.Lock()
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._active_reports: dict[str, int] = defaultdict(int)
        self.enabled = settings.RATE_LIMIT_ENABLED
        self.enabled_for_tests = False

    def evaluate(
        self,
        key: str,
        limit_per_minute: int,
        endpoint_category: str = "general",
        window_seconds: int = 60,
    ) -> tuple[bool, int, int, int]:
        """Evaluate request against sliding window and consume one slot if permitted.

        Returns:
            (allowed: bool, retry_after: int, remaining: int, reset_epoch: int)
        """
        now = datetime.now(UTC).timestamp()
        cutoff = now - window_seconds
        default_reset = int(now + window_seconds)

        if not self.enabled:
            return True, 0, limit_per_minute, default_reset

        with self._lock:
            # Clean expired timestamps for this key
            timestamps = [t for t in self._requests[key] if t > cutoff]

            if len(timestamps) >= limit_per_minute:
                oldest = timestamps[0]
                retry_after = max(1, int(oldest + window_seconds - now))
                reset_epoch = int(oldest + window_seconds)
                self._requests[key] = timestamps
                metrics.record_rate_limit_hit()
                return False, retry_after, 0, reset_epoch

            timestamps.append(now)
            self._requests[key] = timestamps
            remaining = max(0, limit_per_minute - len(timestamps))
            reset_epoch = int(timestamps[0] + window_seconds)
            return True, 0, remaining, reset_epoch

    def is_allowed(
        self,
        key: str,
        limit_per_minute: int,
        endpoint_category: str = "general",
        window_seconds: int = 60,
    ) -> tuple[bool, int]:
        """Legacy helper checking if request within the sliding window is permitted.

        Returns:
            (allowed: bool, retry_after_seconds: int)
        """
        allowed, retry_after, _, _ = self.evaluate(
            key, limit_per_minute, endpoint_category, window_seconds
        )
        return allowed, retry_after

    def check_tenant_quota(self, tenant_id: Any) -> tuple[bool, int]:
        """Check aggregate tenant-wide request quota to prevent noisy-neighbor degradation."""
        if not self.enabled or not tenant_id:
            return True, 0

        key = f"rl:tenant_quota:{tenant_id}"
        limit = settings.TENANT_RATE_LIMIT_PER_MINUTE
        allowed, retry_after, _, _ = self.evaluate(key, limit, endpoint_category="tenant_quota")
        return allowed, retry_after

    def acquire_report_slot(self, tenant_id: Any) -> bool:
        """Acquire a concurrent report execution slot for the tenant.

        Returns:
            True if slot acquired, False if concurrent report limit reached.
        """
        if not self.enabled or not tenant_id:
            return True

        with self._lock:
            current = self._active_reports[str(tenant_id)]
            if current >= settings.TENANT_CONCURRENT_REPORTS_LIMIT:
                return False
            self._active_reports[str(tenant_id)] = current + 1
            return True

    def release_report_slot(self, tenant_id: Any) -> None:
        """Release a concurrent report execution slot for the tenant."""
        if not tenant_id:
            return

        with self._lock:
            current = self._active_reports[str(tenant_id)]
            if current > 0:
                self._active_reports[str(tenant_id)] = current - 1

    def resolve_category_and_limit(self, path: str) -> tuple[str, int]:
        """Classify route sensitivity and assign category limit."""
        normalized_path = path.lower()
        if "/auth/login" in normalized_path or "/auth/forgot-password" in normalized_path or "/auth/reset-password" in normalized_path:
            return "auth", settings.RATE_LIMIT_AUTH_PER_MINUTE
        if "/intelligence/" in normalized_path or "/ai/" in normalized_path:
            return "ai", settings.AI_RATE_LIMIT_PER_MINUTE_USER
        if "/export" in normalized_path or "/search" in normalized_path or "/reports/generate" in normalized_path:
            return "export", settings.RATE_LIMIT_BURST_MAX
        return "general", settings.RATE_LIMIT_DEFAULT_PER_MINUTE

    def derive_key(
        self,
        category: str,
        client_ip: str,
        tenant_id: Any = None,
        user_id: Any = None,
    ) -> str:
        """Derive structured cache key for rate limiter."""
        if tenant_id and user_id:
            return f"rl:{tenant_id}:{user_id}:{category}"
        if tenant_id:
            return f"rl:{tenant_id}:{client_ip}:{category}"
        return f"rl:ip:{client_ip}:{category}"

    def check_request(
        self,
        path: str,
        client_ip: str,
        tenant_id: Any = None,
        user_id: Any = None,
    ) -> RateLimitDecision:
        """Determine rate limit policy based on route sensitivity, tenant quota, and client identity."""
        if not self.enabled:
            now = int(datetime.now(UTC).timestamp())
            return RateLimitDecision(
                allowed=True,
                retry_after=0,
                category="general",
                limit=settings.RATE_LIMIT_DEFAULT_PER_MINUTE,
                remaining=settings.RATE_LIMIT_DEFAULT_PER_MINUTE,
                reset_epoch=now + 60,
            )

        normalized_path = path.lower()

        # 1. Multi-Tenant Fair-Share Check (Noisy Neighbor Protection)
        # Attendance and examination operations are protected mission-critical paths.
        is_mission_critical = (
            "/attendance" in normalized_path or "/examination" in normalized_path
        )
        if tenant_id and not is_mission_critical:
            tenant_allowed, retry_after = self.check_tenant_quota(tenant_id)
            if not tenant_allowed:
                security_events.record_event(
                    event_type="SECURITY_RATE_LIMIT",
                    severity="HIGH",
                    tenant_id=tenant_id,
                    user_id=user_id,
                    ip_address=client_ip,
                    details={
                        "path": path,
                        "category": "tenant_quota",
                        "limit_per_minute": settings.TENANT_RATE_LIMIT_PER_MINUTE,
                        "retry_after_seconds": retry_after,
                    },
                )
                now_epoch = int(datetime.now(UTC).timestamp())
                return RateLimitDecision(
                    allowed=False,
                    retry_after=retry_after,
                    category="tenant_quota",
                    limit=settings.TENANT_RATE_LIMIT_PER_MINUTE,
                    remaining=0,
                    reset_epoch=now_epoch + retry_after,
                )

        # 2. Determine route category & limit
        category, limit = self.resolve_category_and_limit(path)
        key = self.derive_key(category, client_ip, tenant_id, user_id)

        allowed, retry_after, remaining, reset_epoch = self.evaluate(
            key, limit, endpoint_category=category
        )

        if not allowed:
            security_events.record_event(
                event_type="SECURITY_RATE_LIMIT",
                severity="MEDIUM",
                tenant_id=tenant_id,
                user_id=user_id,
                ip_address=client_ip,
                details={
                    "path": path,
                    "category": category,
                    "limit_per_minute": limit,
                    "retry_after_seconds": retry_after,
                },
            )

        return RateLimitDecision(
            allowed=allowed,
            retry_after=retry_after,
            category=category,
            limit=limit,
            remaining=remaining,
            reset_epoch=reset_epoch,
        )

    def get_status(
        self,
        path: str,
        client_ip: str,
        tenant_id: Any = None,
        user_id: Any = None,
        window_seconds: int = 60,
    ) -> dict[str, Any]:
        """Inspect current rate limit quota and remaining requests without consuming a request slot."""
        category, limit = self.resolve_category_and_limit(path)
        key = self.derive_key(category, client_ip, tenant_id, user_id)
        now = datetime.now(UTC).timestamp()
        cutoff = now - window_seconds

        with self._lock:
            timestamps = [t for t in self._requests[key] if t > cutoff]
            current_count = len(timestamps)
            remaining = max(0, limit - current_count)
            reset_epoch = int((timestamps[0] if timestamps else now) + window_seconds)
            retry_after = max(0, int(timestamps[0] + window_seconds - now)) if current_count >= limit else 0

        return {
            "category": category,
            "limit": limit,
            "remaining": remaining,
            "reset_epoch": reset_epoch,
            "retry_after": retry_after,
            "window_seconds": window_seconds,
            "client_ip": client_ip,
            "tenant_id": str(tenant_id) if tenant_id else None,
            "user_id": str(user_id) if user_id else None,
        }

    def reset(self) -> None:
        """Reset rate limiter state (useful in test suites)."""
        with self._lock:
            self._requests.clear()
            self._active_reports.clear()


rate_limiter = SlidingWindowRateLimiter()
