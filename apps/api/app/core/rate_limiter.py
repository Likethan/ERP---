"""Tenant-aware and Client-aware Rate Limiting engine for CampusOS.

Protects authentication endpoints, AI inference, file uploads, and public APIs
against brute-force, denial-of-service, and resource exhaustion.
"""

from collections import defaultdict
from datetime import UTC, datetime
import threading
from typing import Any

from app.core.config import settings
from app.core.metrics import metrics
from app.core.security_events import security_events


class SlidingWindowRateLimiter:
    """In-memory sliding window rate limiter with per-route tiering and tenant fairness."""

    def __init__(self):
        self._lock = threading.Lock()
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._active_reports: dict[str, int] = defaultdict(int)
        self.enabled = settings.RATE_LIMIT_ENABLED
        self.enabled_for_tests = False

    def is_allowed(
        self,
        key: str,
        limit_per_minute: int,
        endpoint_category: str = "general",
        window_seconds: int = 60,
    ) -> tuple[bool, int]:
        """Check if request within the sliding window is permitted.

        Returns:
            (allowed: bool, retry_after_seconds: int)
        """
        if not self.enabled:
            return True, 0

        now = datetime.now(UTC).timestamp()
        cutoff = now - window_seconds

        with self._lock:
            # Clean expired timestamps for this key
            timestamps = [t for t in self._requests[key] if t > cutoff]

            if len(timestamps) >= limit_per_minute:
                oldest = timestamps[0]
                retry_after = max(1, int(oldest + window_seconds - now))
                self._requests[key] = timestamps
                metrics.record_rate_limit_hit()
                return False, retry_after

            timestamps.append(now)
            self._requests[key] = timestamps
            return True, 0

    def check_tenant_quota(self, tenant_id: Any) -> tuple[bool, int]:
        """Check aggregate tenant-wide request quota to prevent noisy-neighbor degradation."""
        if not self.enabled or not tenant_id:
            return True, 0

        key = f"rl:tenant_quota:{tenant_id}"
        limit = settings.TENANT_RATE_LIMIT_PER_MINUTE
        return self.is_allowed(key, limit, endpoint_category="tenant_quota")

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

    def check_request(
        self,
        path: str,
        client_ip: str,
        tenant_id: Any = None,
        user_id: Any = None,
    ) -> tuple[bool, int, str]:
        """Determine rate limit policy based on route sensitivity, tenant quota, and client identity."""
        if not self.enabled:
            return True, 0, "general"

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
                return False, retry_after, "tenant_quota"

        # 2. Determine route category & limit
        if "/auth/login" in normalized_path or "/auth/forgot-password" in normalized_path:
            category = "auth"
            limit = settings.RATE_LIMIT_AUTH_PER_MINUTE
        elif "/intelligence/" in normalized_path or "/ai/" in normalized_path:
            category = "ai"
            limit = settings.AI_RATE_LIMIT_PER_MINUTE_USER
        elif "/export" in normalized_path or "/search" in normalized_path:
            category = "export"
            limit = settings.RATE_LIMIT_BURST_MAX
        else:
            category = "general"
            limit = settings.RATE_LIMIT_DEFAULT_PER_MINUTE

        # Derive rate limit key (prefer authenticated tenant:user over plain IP)
        if tenant_id and user_id:
            key = f"rl:{tenant_id}:{user_id}:{category}"
        elif tenant_id:
            key = f"rl:{tenant_id}:{client_ip}:{category}"
        else:
            key = f"rl:ip:{client_ip}:{category}"

        allowed, retry_after = self.is_allowed(key, limit, endpoint_category=category)
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

        return allowed, retry_after, category

    def reset(self) -> None:
        """Reset rate limiter state (useful in test suites)."""
        with self._lock:
            self._requests.clear()
            self._active_reports.clear()


rate_limiter = SlidingWindowRateLimiter()

