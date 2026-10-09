"""Application and Business Observability Metrics for CampusOS.

Maintains in-memory counters, latency gauges, and operational indicators for
API traffic, database errors, authentication failures, rate-limiting, and AI execution.
"""

from collections import defaultdict
from datetime import UTC, datetime
import threading
from typing import Any


class MetricsCollector:
    """Thread-safe metrics aggregation engine."""

    def __init__(self):
        self._lock = threading.Lock()
        self._http_requests_total = defaultdict(int)
        self._http_errors_total = defaultdict(int)
        self._http_request_durations: list[float] = []
        self._db_errors_total = 0
        self._auth_failures_total = 0
        self._authorization_denied_total = 0
        self._rate_limit_events_total = 0
        self._background_jobs_total = defaultdict(int)
        self._ai_requests_total = 0
        self._ai_failures_total = 0
        self._ai_durations: list[float] = []
        self._started_at = datetime.now(UTC)

    def record_http_request(self, method: str, path: str, status_code: int, duration_seconds: float) -> None:
        """Record an incoming HTTP request execution."""
        with self._lock:
            # Group paths with common prefixes to prevent cardinality explosion
            route_group = self._group_route(path)
            key = f"{method}:{route_group}:{status_code}"
            self._http_requests_total[key] += 1
            if status_code >= 400:
                self._http_errors_total[f"{status_code}"] += 1

            self._http_request_durations.append(duration_seconds)
            if len(self._http_request_durations) > 1000:
                self._http_request_durations = self._http_request_durations[-1000:]

    def record_db_error(self) -> None:
        with self._lock:
            self._db_errors_total += 1

    def record_auth_failure(self) -> None:
        with self._lock:
            self._auth_failures_total += 1

    def record_authorization_denied(self) -> None:
        with self._lock:
            self._authorization_denied_total += 1

    def record_rate_limit_hit(self) -> None:
        with self._lock:
            self._rate_limit_events_total += 1

    def record_job_status(self, job_type: str, status: str) -> None:
        with self._lock:
            self._background_jobs_total[f"{job_type}:{status}"] += 1

    def record_ai_request(self, duration_seconds: float, success: bool = True) -> None:
        with self._lock:
            self._ai_requests_total += 1
            if not success:
                self._ai_failures_total += 1
            self._ai_durations.append(duration_seconds)
            if len(self._ai_durations) > 500:
                self._ai_durations = self._ai_durations[-500:]

    def get_snapshot(self) -> dict[str, Any]:
        """Generate comprehensive operational metrics summary."""
        with self._lock:
            durations = self._http_request_durations
            avg_duration_ms = (sum(durations) / len(durations) * 1000) if durations else 0.0
            max_duration_ms = (max(durations) * 1000) if durations else 0.0

            ai_durations = self._ai_durations
            avg_ai_ms = (sum(ai_durations) / len(ai_durations) * 1000) if ai_durations else 0.0

            uptime_seconds = (datetime.now(UTC) - self._started_at).total_seconds()

            return {
                "uptime_seconds": round(uptime_seconds, 2),
                "http": {
                    "total_requests": sum(self._http_requests_total.values()),
                    "total_errors": sum(self._http_errors_total.values()),
                    "avg_latency_ms": round(avg_duration_ms, 2),
                    "max_latency_ms": round(max_duration_ms, 2),
                    "status_breakdown": dict(self._http_errors_total),
                },
                "security": {
                    "auth_failures": self._auth_failures_total,
                    "authorization_denials": self._authorization_denied_total,
                    "rate_limit_events": self._rate_limit_events_total,
                },
                "database": {
                    "errors_total": self._db_errors_total,
                },
                "background_jobs": dict(self._background_jobs_total),
                "ai": {
                    "requests_total": self._ai_requests_total,
                    "failures_total": self._ai_failures_total,
                    "avg_latency_ms": round(avg_ai_ms, 2),
                },
            }

    def _group_route(self, path: str) -> str:
        """Coarsen paths to avoid high-cardinality metrics (e.g. /students/{id} -> /students/:id)."""
        parts = path.strip("/").split("/")
        if len(parts) > 2 and len(parts[-1]) >= 32:  # Likely a UUID
            parts[-1] = ":id"
        return "/" + "/".join(parts)

    def reset(self) -> None:
        """Reset metrics (used in testing)."""
        with self._lock:
            self._http_requests_total.clear()
            self._http_errors_total.clear()
            self._http_request_durations.clear()
            self._db_errors_total = 0
            self._auth_failures_total = 0
            self._authorization_denied_total = 0
            self._rate_limit_events_total = 0
            self._background_jobs_total.clear()
            self._ai_requests_total = 0
            self._ai_failures_total = 0
            self._ai_durations.clear()
            self._started_at = datetime.now(UTC)


metrics = MetricsCollector()
