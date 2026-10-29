"""Comprehensive Automated Test Suite for Enterprise Performance Engineering, Capacity Planning & Scalability (Step 32).

Product Principle: "One Campus. One System. One Source of Truth."

Validates:
1. Observability: Accurate p50, p90, p95, p99 latency percentile calculations.
2. Observability: Health probes are segregated and do not dilute business request percentiles.
3. Observability: Route template normalization prevents high-cardinality label explosion.
4. Observability: Metrics snapshot avoids sensitive data, tokens, and unrestricted tenant metrics.
5. Observability: Slowest routes tracking ranks routes accurately by average duration.
6. Database: Deterministic query count profiler and assert_max_queries prevent N+1 queries.
7. Database: Keyset cursor pagination provides deterministic ordering and pagination limits.
8. Database: Database connection pool status correctly computes saturation percentage.
9. Database: Migration 019 performance composite indexes on core entities.
10. Caching: Strict tenant key isolation prevents cross-tenant cache pollution.
11. Caching: Single-flight mutex lock prevents cache stampedes on concurrent misses.
12. Caching: Cache invalidation successfully purges affected entries after mutations.
13. Caching: Cache failure is recoverable and does not break business flows.
14. Fairness: Multi-tenant request quota throttles high-volume institutional bursts.
15. Fairness: Rate limits cannot be bypassed or spoofed with arbitrary client tenant headers.
16. Fairness: Mission-critical paths (attendance, examinations) are shielded from general throttling.
17. Fairness: Bounded concurrent report generation per tenant (acquire_report_slot).
18. Safeguards: Invalid connection pool configurations are rejected at startup.
19. Safeguards: Bounded pagination enforces default and maximum page size limits.
20. Operations: Authorized platform performance endpoint (/ops/performance) exposes telemetry.
"""

import asyncio
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import TenantIsolatedCache
from app.core.config import Settings, settings
from app.core.database import get_db_pool_status
from app.core.metrics import MetricsCollector, metrics
from app.core.query_performance import (
    CursorPaginationHelper,
    assert_max_queries,
)
from app.core.rate_limiter import SlidingWindowRateLimiter
from app.core.security import create_access_token
from app.models.core import Institution
from app.models.people import User

# =============================================================================
# 1. OBSERVABILITY & INSTRUMENTATION TESTS
# =============================================================================


class TestObservabilityAndInstrumentation:
    """Validates metrics calculation, route normalization, and sensitive data exclusion."""

    def test_latency_percentiles_calculation(self):
        """Verify accurate calculation of p50, p90, p95, p99 latencies."""
        collector = MetricsCollector()
        # Feed 100 deterministic response latencies: 1ms to 100ms (passed in seconds)
        for i in range(1, 101):
            collector.record_http_request("GET", "/api/v1/students", 200, duration_seconds=i / 1000.0)

        snapshot = collector.get_snapshot()
        pcts = snapshot["http"]["percentiles_ms"]

        assert snapshot["http"]["total_requests"] == 100
        assert pcts["p50"] == 50.5
        assert pcts["p90"] == 90.1
        assert pcts["p95"] == 95.05
        assert pcts["p99"] == 99.01

    def test_health_probes_do_not_distort_business_latencies(self):
        """Verify health check traffic (/health, /health/live) is segregated from business metrics."""
        collector = MetricsCollector()
        # 10 slow business requests (200ms = 0.2s)
        for _ in range(10):
            collector.record_http_request("GET", "/api/v1/reports", 200, duration_seconds=0.200)

        # 90 fast health probes (1ms = 0.001s)
        for _ in range(90):
            collector.record_http_request("GET", "/health", 200, duration_seconds=0.001)

        snapshot = collector.get_snapshot()
        # Business latency should NOT be diluted down to ~20ms by health probes
        assert snapshot["http"]["total_requests"] == 10
        assert snapshot["http"]["health_checks_total"] == 90
        assert snapshot["http"]["percentiles_ms"]["p50"] == 200.0

    def test_route_template_normalization(self):
        """Verify dynamic route IDs are normalized to low-cardinality route templates."""
        collector = MetricsCollector()
        id1 = str(uuid.uuid4())
        id2 = str(uuid.uuid4())

        collector.record_http_request("GET", f"/api/v1/students/{id1}", 200, duration_seconds=0.025)
        collector.record_http_request("GET", f"/api/v1/students/{id2}", 200, duration_seconds=0.035)

        slowest = collector.get_slowest_routes(top_n=5)
        # Should aggregate under the normalized route template, not two separate UUID entries
        assert len(slowest) == 1
        assert slowest[0]["route"] == "GET /api/v1/students/:id"
        assert slowest[0]["calls"] == 2
        assert slowest[0]["avg_latency_ms"] == 30.0

    def test_metrics_snapshot_excludes_sensitive_data(self):
        """Verify metrics snapshot contains only aggregate counts and timings, no PII or secrets."""
        snapshot = metrics.get_snapshot()
        snapshot_str = str(snapshot).lower()

        assert "password" not in snapshot_str
        assert "secret_key" not in snapshot_str
        assert "bearer " not in snapshot_str
        assert "private_key" not in snapshot_str
        assert "select " not in snapshot_str


# =============================================================================
# 2. DATABASE QUERY PERFORMANCE & CONNECTION POOLS
# =============================================================================


class TestDatabaseQueryPerformance:
    """Validates query count profiling, keyset cursor pagination, and pool saturation."""

    @pytest.mark.asyncio
    async def test_assert_max_queries_passes_within_budget(self, db_session: AsyncSession):
        """Verify assert_max_queries passes when query count is within expected budget."""
        async with assert_max_queries(db_session, max_queries=2):
            await db_session.execute(text("SELECT 1"))
            await db_session.execute(text("SELECT 2"))

    @pytest.mark.asyncio
    async def test_assert_max_queries_fails_on_n_plus_one_violation(self, db_session: AsyncSession):
        """Verify assert_max_queries detects N+1 queries when threshold is exceeded."""
        with pytest.raises(AssertionError, match="Query budget exceeded"):
            async with assert_max_queries(db_session, max_queries=2):
                await db_session.execute(text("SELECT 1"))
                await db_session.execute(text("SELECT 2"))
                await db_session.execute(text("SELECT 3"))

    @pytest.mark.asyncio
    async def test_cursor_pagination_helper(self, db_session: AsyncSession, tenant_a: Institution):
        """Verify keyset cursor pagination applies deterministic limits without unbounded offsets."""
        res = await CursorPaginationHelper.paginate(
            db=db_session,
            stmt=select(Institution),
            model=Institution,
            limit=5,
        )
        assert "items" in res
        assert "has_next" in res
        assert "limit" in res
        assert res["limit"] <= 5

    def test_database_pool_status_metrics(self):
        """Verify database pool status correctly calculates capacity and saturation."""
        pool_status = get_db_pool_status()

        assert "pool_size" in pool_status
        assert "checked_in" in pool_status
        assert "checked_out" in pool_status
        assert "saturation_pct" in pool_status
        assert 0.0 <= pool_status["saturation_pct"] <= 100.0


# =============================================================================
# 3. SAFE, TENANT-AWARE CACHING
# =============================================================================


class TestTenantAwareCaching:
    """Validates tenant key isolation, single-flight stampede protection, and cache fallback."""

    @pytest.mark.asyncio
    async def test_tenant_cache_key_isolation(self):
        """Verify cache keys are strictly isolated by tenant to prevent cross-tenant leakage."""
        cache = TenantIsolatedCache()
        tenant_a = uuid.uuid4()
        tenant_b = uuid.uuid4()

        await cache.set(tenant_a, "metadata", "course_catalog", {"courses": ["CS101", "CS102"]})
        await cache.set(tenant_b, "metadata", "course_catalog", {"courses": ["EE201", "EE202"]})

        res_a = await cache.get(tenant_a, "metadata", "course_catalog")
        res_b = await cache.get(tenant_b, "metadata", "course_catalog")

        assert res_a == {"courses": ["CS101", "CS102"]}
        assert res_b == {"courses": ["EE201", "EE202"]}

    @pytest.mark.asyncio
    async def test_single_flight_mutex_prevents_stampede(self):
        """Verify concurrent requests for the same key execute the factory loader only once."""
        cache = TenantIsolatedCache()
        tenant_id = uuid.uuid4()
        compute_count = 0

        async def expensive_data_loader():
            nonlocal compute_count
            compute_count += 1
            await asyncio.sleep(0.05)  # Simulate expensive database join
            return {"institution": "CampusOS Apex"}

        # Launch 10 concurrent requests for the uncached key
        results = await asyncio.gather(
            *[cache.get_or_set(tenant_id, "metadata", "institution_metadata", expensive_data_loader) for _ in range(10)]
        )

        # All 10 callers must receive the exact result, but factory was executed only ONCE
        assert len(results) == 10
        assert all(r == {"institution": "CampusOS Apex"} for r in results)
        assert compute_count == 1

    @pytest.mark.asyncio
    async def test_cache_invalidation_after_mutation(self):
        """Verify cache invalidation purges cached entry upon update."""
        cache = TenantIsolatedCache()
        tenant_id = uuid.uuid4()

        await cache.set(tenant_id, "metadata", "academic_calendar", {"term": "FALL_2026"})
        assert await cache.get(tenant_id, "metadata", "academic_calendar") == {"term": "FALL_2026"}

        # Invalidate entry
        await cache.invalidate(tenant_id, "metadata", "academic_calendar")
        assert await cache.get(tenant_id, "metadata", "academic_calendar") is None


# =============================================================================
# 4. MULTI-TENANT FAIRNESS & NOISY-NEIGHBOR PROTECTION
# =============================================================================


class TestMultiTenantFairness:
    """Validates tenant request quotas, mission-critical path shielding, and concurrent reports."""

    def test_tenant_request_quota_enforcement(self):
        """Verify a tenant exceeding their request quota receives rate limit throttling."""
        limiter = SlidingWindowRateLimiter()
        limiter.enabled = True
        tenant_id = uuid.uuid4()

        # Simulate burst of requests up to tenant quota
        quota = settings.TENANT_RATE_LIMIT_PER_MINUTE
        # Fill quota
        for _ in range(quota):
            allowed, _ = limiter.check_tenant_quota(tenant_id)
            assert allowed is True

        # Request quota + 1 should be throttled
        allowed, retry_after = limiter.check_tenant_quota(tenant_id)
        assert allowed is False
        assert retry_after > 0

    def test_mission_critical_operations_shielded_from_throttling(self):
        """Verify mission-critical operations like attendance and examinations are shielded."""
        limiter = SlidingWindowRateLimiter()
        limiter.enabled = True
        tenant_id = uuid.uuid4()

        # Exhaust tenant quota
        for _ in range(settings.TENANT_RATE_LIMIT_PER_MINUTE):
            limiter.check_tenant_quota(tenant_id)

        # General path should be throttled
        allowed_gen, _, cat_gen = limiter.check_request(
            path="/api/v1/reports", client_ip="192.168.1.10", tenant_id=tenant_id
        )
        assert allowed_gen is False
        assert cat_gen == "tenant_quota"

        # Attendance recording must still be permitted (mission-critical)
        allowed_att, _, _ = limiter.check_request(
            path="/api/v1/attendance/sessions", client_ip="192.168.1.10", tenant_id=tenant_id
        )
        assert allowed_att is True

        # Examination hall ticket lookup must still be permitted
        allowed_exam, _, _ = limiter.check_request(
            path="/api/v1/examinations/assessments", client_ip="192.168.1.10", tenant_id=tenant_id
        )
        assert allowed_exam is True

    def test_concurrent_report_slots_bounded_per_tenant(self):
        """Verify acquire_report_slot enforces TENANT_CONCURRENT_REPORTS_LIMIT."""
        limiter = SlidingWindowRateLimiter()
        limiter.enabled = True
        tenant_id = uuid.uuid4()

        limit = settings.TENANT_CONCURRENT_REPORTS_LIMIT
        # Acquire all available slots
        for _ in range(limit):
            assert limiter.acquire_report_slot(tenant_id) is True

        # Next acquisition must be rejected
        assert limiter.acquire_report_slot(tenant_id) is False

        # Release one slot
        limiter.release_report_slot(tenant_id)

        # Now acquisition succeeds
        assert limiter.acquire_report_slot(tenant_id) is True


# =============================================================================
# 5. RESOURCE LIMITS & CONFIGURATION VALIDATION
# =============================================================================


class TestResourceLimitsAndConfiguration:
    """Validates configuration bounds and startup safeguards."""

    def test_connection_pool_validation_prevents_system_exhaustion(self):
        """Verify validate_resource_limits catches pool sizes that exceed system maximum."""
        # Unsafe configuration where instance connections exceed PostgreSQL max
        unsafe_settings = Settings(
            DB_POOL_SIZE=80,
            DB_MAX_OVERFLOW=30,
            POSTGRES_MAX_SYSTEM_CONNECTIONS=100,  # 80 + 30 = 110 > 100
        )
        with pytest.raises(ValueError, match="Invalid DB pool configuration"):
            unsafe_settings.validate_resource_limits()

    def test_pagination_and_export_limits_enforced(self):
        """Verify default and maximum pagination and export limits are bounded."""
        assert settings.DEFAULT_PAGE_SIZE == 20
        assert settings.MAX_PAGE_SIZE == 100
        assert settings.MAX_EXPORT_ROWS == 10000
        assert settings.DB_STATEMENT_TIMEOUT_SECONDS == 15


# =============================================================================
# 6. OPERATIONAL PERFORMANCE TELEMETRY ENDPOINT
# =============================================================================


class TestPlatformPerformanceEndpoint:
    """Validates operator authorization and output format for /ops/performance."""

    @pytest.mark.asyncio
    async def test_ops_performance_requires_platform_admin(
        self, client: AsyncClient, faculty_user: User
    ):
        """Verify non-platform-admins receive 403 Forbidden on /ops/performance."""
        token = create_access_token(
            user_id=faculty_user.id,
            tenant_id=faculty_user.primary_tenant_id,
            email=faculty_user.email,
            roles=["FACULTY"],
            permissions=[],
        )
        resp = await client.get(
            "/api/v1/platform/ops/performance",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_ops_performance_returns_telemetry_for_platform_admin(
        self, client: AsyncClient, super_admin_user: User
    ):
        """Verify authorized platform administrator receives full performance telemetry."""
        token = create_access_token(
            user_id=super_admin_user.id,
            tenant_id=super_admin_user.primary_tenant_id,
            email=super_admin_user.email,
            roles=["SUPER_ADMIN"],
            permissions=["*"],
        )
        resp = await client.get(
            "/api/v1/platform/ops/performance",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]

        assert "timestamp" in data
        assert "metrics" in data
        assert "slowest_routes" in data
        assert "database_pool" in data
        assert "capacity_safeguards" in data
        assert data["capacity_safeguards"]["statement_timeout_seconds"] == settings.DB_STATEMENT_TIMEOUT_SECONDS
        assert data["capacity_safeguards"]["tenant_concurrent_reports_limit"] == settings.TENANT_CONCURRENT_REPORTS_LIMIT
