"""Application and Business Observability Metrics for CampusOS.

Maintains in-memory counters, latency gauges, and operational indicators for
API traffic, database execution, cache efficiency, authentication, rate-limiting,
and background execution without exposing high-cardinality or sensitive data.
"""

from collections import defaultdict
from datetime import UTC, datetime
import math
import threading
from typing import Any
from uuid import UUID


class MetricsCollector:
    """Thread-safe enterprise metrics aggregation engine with percentiles and route analytics."""

    def __init__(self):
        self._lock = threading.Lock()
        self._http_requests_total = defaultdict(int)
        self._http_errors_total = defaultdict(int)
        self._http_request_durations: list[float] = []
        self._health_checks_total = 0
        self._request_sizes: list[int] = []
        self._response_sizes: list[int] = []

        # Route-level performance tracking: route -> {calls, total_duration, max_duration, errors, durations: list}
        self._route_stats: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "calls": 0,
                "total_duration": 0.0,
                "max_duration": 0.0,
                "errors": 0,
                "durations": [],
            }
        )

        # Database telemetry
        self._db_queries_total = 0
        self._db_errors_total = 0
        self._db_durations: list[float] = []

        # Cache telemetry
        self._cache_hits_total = 0
        self._cache_misses_total = 0
        self._cache_errors_total = 0
        self._cache_hits_by_namespace = defaultdict(int)

        # Security & platform counters
        self._auth_failures_total = 0
        self._authorization_denied_total = 0
        self._rate_limit_events_total = 0
        self._timeouts_total = 0

        # Multi-tenant aggregate activity (anonymized active tenant counter)
        self._active_tenants: set[str] = set()

        # Background processing
        self._background_jobs_total = defaultdict(int)
        self._outbox_pending_gauge = 0
        self._outbox_processed_total = 0

        # AI telemetry
        self._ai_requests_total = 0
        self._ai_failures_total = 0
        self._ai_durations: list[float] = []

        self._started_at = datetime.now(UTC)

    def record_http_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_seconds: float,
        route_template: str | None = None,
        request_size_bytes: int = 0,
        response_size_bytes: int = 0,
        tenant_id: UUID | None = None,
    ) -> None:
        """Record an incoming HTTP request execution with route normalization."""
        is_health = path in ("/health", "/health/live", "/health/ready")
        route_name = route_template or self._group_route(path)

        with self._lock:
            if is_health:
                self._health_checks_total += 1
                return

            key = f"{method}:{route_name}:{status_code}"
            self._http_requests_total[key] += 1

            if status_code >= 400:
                self._http_errors_total[f"{status_code}"] += 1
            if status_code in (408, 504):
                self._timeouts_total += 1

            # Business API latency buffer (capped at 2000 samples)
            self._http_request_durations.append(duration_seconds)
            if len(self._http_request_durations) > 2000:
                self._http_request_durations = self._http_request_durations[-2000:]

            # Route level aggregation
            r_stat = self._route_stats[f"{method} {route_name}"]
            r_stat["calls"] += 1
            r_stat["total_duration"] += duration_seconds
            if duration_seconds > r_stat["max_duration"]:
                r_stat["max_duration"] = duration_seconds
            if status_code >= 400:
                r_stat["errors"] += 1
            r_stat["durations"].append(duration_seconds)
            if len(r_stat["durations"]) > 500:
                r_stat["durations"] = r_stat["durations"][-500:]

            # Request & response sizes
            if request_size_bytes > 0:
                self._request_sizes.append(request_size_bytes)
                if len(self._request_sizes) > 500:
                    self._request_sizes = self._request_sizes[-500:]
            if response_size_bytes > 0:
                self._response_sizes.append(response_size_bytes)
                if len(self._response_sizes) > 500:
                    self._response_sizes = self._response_sizes[-500:]

            # Tenant anonymized aggregation
            if tenant_id:
                self._active_tenants.add(str(tenant_id))

    def record_db_query(self, duration_seconds: float) -> None:
        """Record execution of an asynchronous database query."""
        with self._lock:
            self._db_queries_total += 1
            self._db_durations.append(duration_seconds)
            if len(self._db_durations) > 1000:
                self._db_durations = self._db_durations[-1000:]

    def record_db_error(self) -> None:
        with self._lock:
            self._db_errors_total += 1

    def record_cache_hit(self, namespace: str = "general") -> None:
        with self._lock:
            self._cache_hits_total += 1
            self._cache_hits_by_namespace[namespace] += 1

    def record_cache_miss(self, namespace: str = "general") -> None:
        with self._lock:
            self._cache_misses_total += 1

    def record_cache_error(self) -> None:
        with self._lock:
            self._cache_errors_total += 1

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

    def record_outbox_metrics(self, pending_count: int, processed_batch: int = 0) -> None:
        with self._lock:
            self._outbox_pending_gauge = pending_count
            self._outbox_processed_total += processed_batch

    def record_ai_request(self, duration_seconds: float, success: bool = True) -> None:
        with self._lock:
            self._ai_requests_total += 1
            if not success:
                self._ai_failures_total += 1
            self._ai_durations.append(duration_seconds)
            if len(self._ai_durations) > 500:
                self._ai_durations = self._ai_durations[-500:]

    @staticmethod
    def _calculate_percentiles(durations: list[float]) -> dict[str, float]:
        """Compute p50, p90, p95, and p99 percentiles in milliseconds."""
        if not durations:
            return {"p50": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0}

        sorted_d = sorted(durations)
        n = len(sorted_d)

        def _p(pct: float) -> float:
            k = (n - 1) * (pct / 100.0)
            f = math.floor(k)
            c = math.ceil(k)
            if f == c:
                return sorted_d[int(k)] * 1000.0
            d0 = sorted_d[int(f)] * (c - k)
            d1 = sorted_d[int(c)] * (k - f)
            return (d0 + d1) * 1000.0

        return {
            "p50": round(_p(50), 2),
            "p90": round(_p(90), 2),
            "p95": round(_p(95), 2),
            "p99": round(_p(99), 2),
        }

    def get_slowest_routes(self, top_n: int = 10, limit: int | None = None) -> list[dict[str, Any]]:
        """Return top N slowest API routes sorted by average execution latency."""
        effective_limit = limit if limit is not None else top_n
        with self._lock:
            routes = []
            for route_name, stats in self._route_stats.items():
                calls = stats["calls"]
                if calls == 0:
                    continue
                avg_ms = (stats["total_duration"] / calls) * 1000.0
                max_ms = stats["max_duration"] * 1000.0
                pcts = self._calculate_percentiles(stats["durations"])
                routes.append(
                    {
                        "route": route_name,
                        "calls": calls,
                        "avg_latency_ms": round(avg_ms, 2),
                        "p95_latency_ms": pcts["p95"],
                        "max_latency_ms": round(max_ms, 2),
                        "errors": stats["errors"],
                    }
                )
            routes.sort(key=lambda r: r["avg_latency_ms"], reverse=True)
            return routes[:effective_limit]

    def get_snapshot(self) -> dict[str, Any]:
        """Generate comprehensive operational metrics summary."""
        with self._lock:
            durations = self._http_request_durations
            avg_duration_ms = (sum(durations) / len(durations) * 1000) if durations else 0.0
            max_duration_ms = (max(durations) * 1000) if durations else 0.0
            http_pcts = self._calculate_percentiles(durations)

            db_durations = self._db_durations
            avg_db_ms = (sum(db_durations) / len(db_durations) * 1000) if db_durations else 0.0
            db_pcts = self._calculate_percentiles(db_durations)

            ai_durations = self._ai_durations
            avg_ai_ms = (sum(ai_durations) / len(ai_durations) * 1000) if ai_durations else 0.0

            cache_total = self._cache_hits_total + self._cache_misses_total
            cache_hit_rate = round((self._cache_hits_total / cache_total * 100), 2) if cache_total > 0 else 100.0

            avg_req_bytes = int(sum(self._request_sizes) / len(self._request_sizes)) if self._request_sizes else 0
            avg_resp_bytes = int(sum(self._response_sizes) / len(self._response_sizes)) if self._response_sizes else 0

            uptime_seconds = (datetime.now(UTC) - self._started_at).total_seconds()

            return {
                "uptime_seconds": round(uptime_seconds, 2),
                "http": {
                    "total_requests": sum(self._http_requests_total.values()),
                    "total_errors": sum(self._http_errors_total.values()),
                    "health_checks_total": self._health_checks_total,
                    "avg_latency_ms": round(avg_duration_ms, 2),
                    "max_latency_ms": round(max_duration_ms, 2),
                    "percentiles_ms": http_pcts,
                    "status_breakdown": dict(self._http_errors_total),
                    "avg_request_size_bytes": avg_req_bytes,
                    "avg_response_size_bytes": avg_resp_bytes,
                },
                "security": {
                    "auth_failures": self._auth_failures_total,
                    "authorization_denials": self._authorization_denied_total,
                    "rate_limit_events": self._rate_limit_events_total,
                    "timeouts": self._timeouts_total,
                },
                "database": {
                    "queries_total": self._db_queries_total,
                    "errors_total": self._db_errors_total,
                    "avg_latency_ms": round(avg_db_ms, 2),
                    "percentiles_ms": db_pcts,
                },
                "cache": {
                    "hits_total": self._cache_hits_total,
                    "misses_total": self._cache_misses_total,
                    "errors_total": self._cache_errors_total,
                    "hit_rate_pct": cache_hit_rate,
                    "hits_by_namespace": dict(self._cache_hits_by_namespace),
                },
                "background_jobs": dict(self._background_jobs_total),
                "outbox": {
                    "pending_events_gauge": self._outbox_pending_gauge,
                    "processed_events_total": self._outbox_processed_total,
                },
                "multi_tenancy": {
                    "active_tenants_count": len(self._active_tenants),
                },
                "ai": {
                    "requests_total": self._ai_requests_total,
                    "failures_total": self._ai_failures_total,
                    "avg_latency_ms": round(avg_ai_ms, 2),
                },
            }

    def _group_route(self, path: str) -> str:
        """Coarsen paths to avoid high-cardinality metrics (e.g. /students/{id} -> /students/:id)."""
        parts = path.strip("/").split("/")
        cleaned = []
        for p in parts:
            if len(p) >= 32 or (p.isalnum() and any(c.isdigit() for c in p) and len(p) > 6):
                cleaned.append(":id")
            elif p.isdigit():
                cleaned.append(":id")
            else:
                cleaned.append(p)
        return "/" + "/".join(cleaned)

    def reset(self) -> None:
        """Reset metrics (used in testing)."""
        with self._lock:
            self._http_requests_total.clear()
            self._http_errors_total.clear()
            self._http_request_durations.clear()
            self._health_checks_total = 0
            self._request_sizes.clear()
            self._response_sizes.clear()
            self._route_stats.clear()
            self._db_queries_total = 0
            self._db_errors_total = 0
            self._db_durations.clear()
            self._cache_hits_total = 0
            self._cache_misses_total = 0
            self._cache_errors_total = 0
            self._cache_hits_by_namespace.clear()
            self._auth_failures_total = 0
            self._authorization_denied_total = 0
            self._rate_limit_events_total = 0
            self._timeouts_total = 0
            self._active_tenants.clear()
            self._background_jobs_total.clear()
            self._outbox_pending_gauge = 0
            self._outbox_processed_total = 0
            self._ai_requests_total = 0
            self._ai_failures_total = 0
            self._ai_durations.clear()
            self._started_at = datetime.now(UTC)


metrics = MetricsCollector()

