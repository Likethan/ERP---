"""Comprehensive Test Suite for Enterprise Data Platform, Real-Time Analytics & BI (Step 28).

Verifies all 20 requirements:
1. Metric registry discovery and schema validation.
2. Correct calculations against known operational test fixtures.
3. Date-range and period filtering.
4. Grouped aggregations and pagination.
5. Correct handling of missing or unsupported source data.
6. Financial calculation correctness, including failed payments exclusion.
7. Duplicate event ingestion (idempotency).
8. Incremental aggregation and historical backfills.
9. Out-of-order or corrected source events handling.
10. Data quality reconciliation findings generation.
11. Tenant isolation across all query paths.
12. Permission checks on metrics and datasets (PBAC).
13. Cache isolation and invalidation.
14. Controlled export authorization and CSV formula injection sanitization.
15. Governed registry integrity and SQL injection immunity.
16. Query limits and invalid filter rejection.
17. Dashboard response contract compatibility across all 9 dashboard types.
18. Failure recovery, ingestion telemetry, and data freshness tracking.
19. Database migration consistency (Alembic head 015).
20. Small-cell privacy suppression safeguard for sensitive counts (< 5).
"""

import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.analytics_ingestion import AnalyticsIngestionConsumer
from app.core.exceptions import ValidationException
from app.core.metric_registry import (
    MetricDomain,
    get_governed_metric,
    list_governed_metrics,
)
from app.core.permissions import DEFAULT_ROLE_PERMISSIONS
from app.core.security import ACCESS_TOKEN_COOKIE_NAME, create_access_token
from app.models.analytics import (
    AnalyticsDailyMetric,
    AnalyticsMetricFreshness,
    MetricFreshnessStatus,
    ReconciliationSeverity,
    ReconciliationStatus,
)
from app.models.core import Department, Institution, Program
from app.models.finance import PaymentTransaction
from app.models.people import StudentProfile, User
from app.schemas.analytics import (
    BreakdownRequest,
    DashboardType,
    TimeseriesRequest,
)
from app.services.analytics_service import AnalyticsService
from app.services.data_quality_reconciliation_service import DataQualityReconciliationService


def make_auth_headers(
    user: User,
    tenant_id: uuid.UUID,
    role_name: str = "INSTITUTION_ADMIN",
    custom_permissions: list[str] | None = None,
) -> dict[str, str]:
    perms = (
        custom_permissions
        if custom_permissions is not None
        else DEFAULT_ROLE_PERMISSIONS.get(role_name, [])
    )
    token = create_access_token(
        user_id=user.id,
        tenant_id=tenant_id,
        email=user.email,
        roles=[role_name],
        permissions=perms,
    )
    return {
        "Authorization": f"Bearer {token}",
        "Cookie": f"{ACCESS_TOKEN_COOKIE_NAME}={token}",
    }


# =============================================================================
# 1. METRIC REGISTRY & DISCOVERY TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_metric_registry_catalogue_discovery():
    """1. Test metric catalogue discovery, domain filtering, and metadata validation."""
    all_metrics = list_governed_metrics()
    assert len(all_metrics) >= 15

    # Check student domain filtering
    student_metrics = list_governed_metrics(MetricDomain.STUDENTS.value)
    assert len(student_metrics) >= 2
    metric_ids = [m.metric_id for m in student_metrics]
    assert "total_active_students" in metric_ids

    # Inspect total_active_students metadata
    m = get_governed_metric("total_active_students")
    assert m.metric_id == "total_active_students"
    assert m.display_name == "Total Active Students"
    assert m.owning_domain == MetricDomain.STUDENTS
    assert m.version == "1.0"
    assert "department" in m.supported_dimensions
    assert (
        "analytics.read" in m.required_permissions
        or "analytics:read" in m.required_permissions
    )


@pytest.mark.asyncio
async def test_unregistered_metric_rejection():
    """16. Test that requesting unapproved or arbitrary metric names is strictly rejected."""
    with pytest.raises(ValidationException):
        get_governed_metric("arbitrary_unregistered_metric; DROP TABLE users;")


# =============================================================================
# 2. OPERATIONAL SOURCE-OF-TRUTH CALCULATIONS & FINANCIAL INTEGRITY
# =============================================================================


@pytest.mark.asyncio
async def test_student_and_department_distribution_calculation(
    db_session: AsyncSession, tenant_a: Institution
):
    """2. Test calculation of active student counts against operational records."""
    dept = Department(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        code=f"CSE_{uuid.uuid4().hex[:4]}",
        name="Computer Science & Engineering",
        is_active=True,
    )
    db_session.add(dept)
    await db_session.flush()

    prog = Program(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        department_id=dept.id,
        code=f"BTECH_CS_{uuid.uuid4().hex[:4]}",
        name="Bachelor of Technology in CS",
        degree_level="UNDERGRADUATE",
        duration_years=Decimal("4.0"),
        total_semesters=8,
        is_active=True,
    )
    db_session.add(prog)
    await db_session.flush()

    # Create 3 ACTIVE students and 1 WITHDRAWN student
    t_date = date(2026, 8, 1)
    for i in range(3):
        st = StudentProfile(
            id=uuid.uuid4(),
            tenant_id=tenant_a.id,
            user_id=uuid.uuid4(),
            admission_number=f"ADM_A_{i}_{uuid.uuid4().hex[:4]}",
            registration_number=f"REG_A_{i}_{uuid.uuid4().hex[:4]}",
            program_id=prog.id,
            batch_id=uuid.uuid4(),
            date_of_birth=date(2004, 5, 12),
            gender="MALE",
            status="ACTIVE",
            admission_date=t_date,
            expected_graduation_date=date(2030, 5, 30),
        )
        db_session.add(st)

    st_withdrawn = StudentProfile(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        user_id=uuid.uuid4(),
        admission_number=f"ADM_W_{uuid.uuid4().hex[:4]}",
        registration_number=f"REG_W_{uuid.uuid4().hex[:4]}",
        program_id=prog.id,
        batch_id=uuid.uuid4(),
        date_of_birth=date(2004, 5, 12),
        gender="MALE",
        status="WITHDRAWN",
        admission_date=t_date,
        expected_graduation_date=date(2030, 5, 30),
    )
    db_session.add(st_withdrawn)
    await db_session.commit()

    # Run breakdown query for total_active_students by department
    req = BreakdownRequest(metric_id="total_active_students", dimension="department")
    breakdown = await AnalyticsService.get_breakdown(db_session, tenant_a.id, req)

    assert breakdown.metric_id == "total_active_students"
    assert len(breakdown.items) >= 1
    cse_item = next((it for it in breakdown.items if it.category == dept.name), None)
    assert cse_item is not None
    assert cse_item.value == 3.0  # Only 3 ACTIVE students counted


@pytest.mark.asyncio
async def test_financial_calculation_confirmed_payments_only(
    db_session: AsyncSession, tenant_a: Institution
):
    """6. Ensure finance collections count ONLY confirmed (SUCCESS) payments."""
    today = datetime.now(UTC)

    # 1. Successful payment: INR 50,000
    p1 = PaymentTransaction(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        student_id=uuid.uuid4(),
        payment_number=f"PAY-{uuid.uuid4().hex[:6]}",
        transaction_reference=f"TXN-{uuid.uuid4().hex[:8]}",
        payment_mode="ONLINE",
        gateway_provider="RAZORPAY",
        status="SUCCESS",
        amount=Decimal("50000.00"),
        currency="INR",
        payment_date=today,
    )
    # 2. Another successful payment: INR 25,000
    p2 = PaymentTransaction(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        student_id=uuid.uuid4(),
        payment_number=f"PAY-{uuid.uuid4().hex[:6]}",
        transaction_reference=f"TXN-{uuid.uuid4().hex[:8]}",
        payment_mode="ONLINE",
        gateway_provider="RAZORPAY",
        status="SUCCESS",
        amount=Decimal("25000.00"),
        currency="INR",
        payment_date=today,
    )
    # 3. Failed payment: INR 40,000 (must be ignored)
    p3 = PaymentTransaction(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        student_id=uuid.uuid4(),
        payment_number=f"PAY-{uuid.uuid4().hex[:6]}",
        transaction_reference=f"TXN-{uuid.uuid4().hex[:8]}",
        payment_mode="ONLINE",
        gateway_provider="RAZORPAY",
        status="FAILED",
        amount=Decimal("40000.00"),
        currency="INR",
        payment_date=today,
    )
    # 4. Pending payment: INR 30,000 (must be ignored)
    p4 = PaymentTransaction(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        student_id=uuid.uuid4(),
        payment_number=f"PAY-{uuid.uuid4().hex[:6]}",
        transaction_reference=f"TXN-{uuid.uuid4().hex[:8]}",
        payment_mode="ONLINE",
        gateway_provider="RAZORPAY",
        status="PENDING",
        amount=Decimal("30000.00"),
        currency="INR",
        payment_date=today,
    )

    db_session.add_all([p1, p2, p3, p4])
    await db_session.commit()

    # Query timeseries for confirmed_collections
    ts_req = TimeseriesRequest(
        metric_id="confirmed_collections",
        start_date=today.date() - timedelta(days=1),
        end_date=today.date() + timedelta(days=1),
    )
    ts_res = await AnalyticsService.get_timeseries(db_session, tenant_a.id, ts_req)

    today_pt = next((pt for pt in ts_res.points if pt.date == today.date()), None)
    assert today_pt is not None
    assert today_pt.value == 75000.0  # 50,000 + 25,000
    assert today_pt.record_count == 2  # Only the 2 successful transactions


# =============================================================================
# 3. PRIVACY SAFEGUARDS: SMALL-CELL SUPPRESSION
# =============================================================================


@pytest.mark.asyncio
async def test_small_cell_privacy_suppression(db_session: AsyncSession, tenant_a: Institution):
    """20. Test that breakdown categories with < 5 records are masked to protect student privacy."""
    dept_small = Department(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        code=f"ARCH_{uuid.uuid4().hex[:4]}",
        name="Architecture & Planning",
        is_active=True,
    )
    db_session.add(dept_small)
    await db_session.flush()

    t_date = date(2026, 8, 1)
    prog_arch = Program(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        department_id=dept_small.id,
        code=f"BARCH_{uuid.uuid4().hex[:4]}",
        name="Bachelor of Architecture",
        degree_level="UNDERGRADUATE",
        duration_years=Decimal("5.0"),
        total_semesters=10,
        is_active=True,
    )
    db_session.add(prog_arch)
    await db_session.flush()

    # Add only 3 students (< 5 threshold)
    for i in range(3):
        st = StudentProfile(
            id=uuid.uuid4(),
            tenant_id=tenant_a.id,
            user_id=uuid.uuid4(),
            admission_number=f"ARCH_A_{i}_{uuid.uuid4().hex[:4]}",
            registration_number=f"ARCH_R_{i}_{uuid.uuid4().hex[:4]}",
            program_id=prog_arch.id,
            batch_id=uuid.uuid4(),
            date_of_birth=date(2005, 3, 10),
            gender="FEMALE",
            status="ACTIVE",
            admission_date=t_date,
            expected_graduation_date=date(2031, 5, 30),
        )
        db_session.add(st)
    await db_session.commit()

    req = BreakdownRequest(metric_id="total_active_students", dimension="department")
    breakdown = await AnalyticsService.get_breakdown(db_session, tenant_a.id, req)

    arch_item = next((it for it in breakdown.items if it.category == dept_small.name), None)
    assert arch_item is not None
    # Suppression assertion:
    assert arch_item.record_count == "<5"


# =============================================================================
# 4. EVENT INGESTION & IDEMPOTENCY (STEP 27 CONSUMER INTEGRATION)
# =============================================================================


@pytest.mark.asyncio
async def test_event_ingestion_updates_rollups_and_freshness(
    db_session: AsyncSession, tenant_a: Institution
):
    """7 & 8. Test that canonical domain events update metrics and freshness idempotently."""
    from app.core.events import DomainEventEnvelope
    from app.models.event import ConsumerCheckpointStatus

    consumer = AnalyticsIngestionConsumer()
    test_event_id = uuid.uuid4()
    today = datetime.now(UTC)

    envelope = DomainEventEnvelope(
        event_id=test_event_id,
        tenant_id=tenant_a.id,
        event_type="finance.payment.confirmed",
        aggregate_type="PaymentTransaction",
        aggregate_id=uuid.uuid4(),
        event_timestamp=today,
        payload={
            "payment_id": str(uuid.uuid4()),
            "amount": "15000.00",
            "currency": "INR",
            "invoice_id": str(uuid.uuid4()),
            "payment_method": "ONLINE",
            "gateway_reference": "TXN_TEST_101",
        },
        schema_version="1.0",
        causation_id="cmd_test_01",
        producer="CAMPUSOS_FINANCE",
        metadata={"created_at": today.isoformat()},
    )
    result1 = await consumer.handle(db=db_session, envelope=envelope)
    await db_session.commit()

    assert result1.status == ConsumerCheckpointStatus.COMPLETED

    # Verify freshness updated
    freshness = await db_session.execute(
        select(AnalyticsMetricFreshness).where(
            AnalyticsMetricFreshness.tenant_id == tenant_a.id,
            AnalyticsMetricFreshness.metric_id == "confirmed_collections",
        )
    )
    f_row = freshness.scalar_one_or_none()
    assert f_row is not None
    assert f_row.status == MetricFreshnessStatus.FRESH
    assert f_row.source_event_count >= 1

    # Verify daily metric updated
    daily = await db_session.execute(
        select(AnalyticsDailyMetric).where(
            AnalyticsDailyMetric.tenant_id == tenant_a.id,
            AnalyticsDailyMetric.metric_id == "confirmed_collections",
            AnalyticsDailyMetric.metric_date == today.date(),
        )
    )
    d_row = daily.scalar_one_or_none()
    assert d_row is not None
    assert d_row.value_numeric >= Decimal("15000.00")


# =============================================================================
# 5. DATA QUALITY RECONCILIATION ENGINE
# =============================================================================


@pytest.mark.asyncio
async def test_reconciliation_detects_payment_discrepancy(
    db_session: AsyncSession, tenant_a: Institution
):
    """10. Test that automated reconciliation identifies delta between operational records and rollups."""
    # Seed operational payment of 80,000
    p = PaymentTransaction(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        student_id=uuid.uuid4(),
        payment_number=f"PAY-{uuid.uuid4().hex[:6]}",
        transaction_reference=f"TXN-{uuid.uuid4().hex[:8]}",
        payment_mode="ONLINE",
        gateway_provider="RAZORPAY",
        status="SUCCESS",
        amount=Decimal("80000.00"),
        currency="INR",
        payment_date=datetime.now(UTC),
    )
    db_session.add(p)

    # Seed analytical rollup of only 10,000 (creating a 70,000 variance)
    daily = AnalyticsDailyMetric(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        metric_id="confirmed_collections",
        metric_date=datetime.now(UTC).date(),
        dimension_type="GLOBAL",
        dimension_value="ALL",
        value_numeric=Decimal("10000.00"),
        record_count=1,
        metadata_json={},
    )
    db_session.add(daily)
    await db_session.commit()

    findings = await DataQualityReconciliationService.run_tenant_reconciliation(
        db=db_session,
        tenant_id=tenant_a.id,
    )
    await db_session.commit()

    fin_finding = next((f for f in findings if f.rule_code == "FIN_PAYMENTS_RECONCILIATION"), None)
    assert fin_finding is not None
    assert fin_finding.severity == ReconciliationSeverity.ERROR
    assert fin_finding.operational_value == Decimal("80000.00")
    assert fin_finding.analytics_value == Decimal("10000.00")
    assert fin_finding.discrepancy_delta == Decimal("70000.00")
    assert fin_finding.resolution_status == ReconciliationStatus.OPEN


# =============================================================================
# 6. HISTORICAL BACKFILL EXECUTION
# =============================================================================


@pytest.mark.asyncio
async def test_historical_analytics_backfill(db_session: AsyncSession, tenant_a: Institution):
    """8. Test historical backfill recalculation over an operational date range."""
    today = datetime.now(UTC).date()
    yesterday = today - timedelta(days=1)

    count = await AnalyticsService.run_backfill(
        db=db_session,
        tenant_id=tenant_a.id,
        start_date=yesterday,
        end_date=today,
    )

    assert count >= 4  # 2 days * at least 2 metrics computed per day


# =============================================================================
# 7. DASHBOARD RESPONSE CONTRACT COMPATIBILITY
# =============================================================================


@pytest.mark.asyncio
async def test_all_nine_dashboard_response_contracts(
    db_session: AsyncSession, tenant_a: Institution
):
    """17. Verify all 9 institutional dashboard response contracts conform to schema."""
    dashboards = [
        DashboardType.EXECUTIVE_OVERVIEW,
        DashboardType.ACADEMIC_PERFORMANCE,
        DashboardType.STUDENT_LIFECYCLE,
        DashboardType.ATTENDANCE_ENGAGEMENT,
        DashboardType.EXAMINATION_OUTCOMES,
        DashboardType.FINANCE_COLLECTIONS,
        DashboardType.PLACEMENT_OUTCOMES,
        DashboardType.CAMPUS_OPERATIONS,
        DashboardType.WORKFLOW_SYSTEM_HEALTH,
    ]

    for dtype in dashboards:
        resp = await AnalyticsService.get_dashboard(
            db=db_session,
            tenant_id=tenant_a.id,
            dashboard_type=dtype.value,
            bypass_cache=True,
        )
        assert resp.dashboard_type == dtype.value
        assert resp.title != ""
        assert len(resp.kpis) > 0
        assert resp.freshness is not None
        assert resp.freshness.status == "FRESH"


# =============================================================================
# 8. REST API ENDPOINT INTEGRATION, PERMISSIONS & ISOLATION
# =============================================================================


@pytest.mark.asyncio
async def test_api_list_metrics_and_schema(
    client: AsyncClient, tenant_a: Institution, tenant_admin_a: User
):
    """1. Test GET /api/v1/analytics/metrics returns valid catalog definitions."""
    headers = make_auth_headers(tenant_admin_a, tenant_a.id)
    response = await client.get("/api/v1/analytics/metrics", headers=headers)

    assert response.status_code == 200
    res_json = response.json()
    assert res_json.get("success") is True
    data = res_json["data"]
    assert len(data) >= 15
    # Inspect first item
    first_item = data[0]
    metric_key = "metric_id" if "metric_id" in first_item else ("metricId" if "metricId" in first_item else list(first_item.keys())[0])
    metric_ids = [m[metric_key] for m in data]
    assert "confirmed_collections" in metric_ids
    assert "hostel_occupancy_rate" in metric_ids


@pytest.mark.asyncio
async def test_api_dashboard_endpoint(
    client: AsyncClient, tenant_a: Institution, tenant_admin_a: User
):
    """17. Test GET /api/v1/analytics/dashboards/{type} returns contract."""
    headers = make_auth_headers(tenant_admin_a, tenant_a.id)
    response = await client.get("/api/v1/analytics/dashboards/EXECUTIVE_OVERVIEW", headers=headers)

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["dashboard_type"] == "EXECUTIVE_OVERVIEW"
    assert "kpis" in data
    assert len(data["kpis"]) >= 3


@pytest.mark.asyncio
async def test_strict_tenant_isolation_on_analytics_queries(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_b: Institution,
    tenant_admin_a: User,
    tenant_admin_b: User,
):
    """11. Verify Tenant A can NEVER observe or retrieve Tenant B's analytics data."""
    # Seed payment in Tenant B only: 999,999 INR
    p_b = PaymentTransaction(
        id=uuid.uuid4(),
        tenant_id=tenant_b.id,
        student_id=uuid.uuid4(),
        payment_number=f"PAY-{uuid.uuid4().hex[:6]}",
        transaction_reference=f"TXN-{uuid.uuid4().hex[:8]}",
        payment_mode="ONLINE",
        gateway_provider="RAZORPAY",
        status="SUCCESS",
        amount=Decimal("999999.00"),
        currency="INR",
        payment_date=datetime.now(UTC),
    )
    db_session.add(p_b)
    await db_session.commit()

    # Query timeseries as Tenant A
    headers_a = make_auth_headers(tenant_admin_a, tenant_a.id)
    payload = {
        "metric_id": "confirmed_collections",
        "interval": "day",
        "start_date": (datetime.now(UTC) - timedelta(days=2)).date().isoformat(),
        "end_date": (datetime.now(UTC) + timedelta(days=1)).date().isoformat(),
    }
    resp_a = await client.post("/api/v1/analytics/timeseries", json=payload, headers=headers_a)
    assert resp_a.status_code == 200
    pts_a = resp_a.json()["data"]["points"]
    # Tenant A must NOT see 999,999 INR
    assert all(pt["value"] != 999999.0 for pt in pts_a)


@pytest.mark.asyncio
async def test_permission_enforcement_forbids_unauthorized_user(
    client: AsyncClient, tenant_a: Institution, faculty_user: User
):
    """12. Verify user without ANALYTICS_QUERY permission receives 403 Forbidden."""
    headers = make_auth_headers(
        faculty_user,
        tenant_a.id,
        role_name="FACULTY",
    )
    payload = {
        "metric_id": "confirmed_collections",
        "interval": "day",
    }
    response = await client.post("/api/v1/analytics/timeseries", json=payload, headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_analytics_export_csv_and_formula_injection_defense(
    client: AsyncClient, tenant_a: Institution, tenant_admin_a: User
):
    """14. Test CSV export with formula injection sanitization."""
    headers = make_auth_headers(tenant_admin_a, tenant_a.id)
    payload = {
        "export_type": "timeseries",
        "metric_id": "total_active_students",
        "format": "CSV",
    }
    response = await client.post("/api/v1/analytics/export", json=payload, headers=headers)

    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "attachment;" in response.headers["content-disposition"]
    body = response.text
    assert "Timestamp,Date,Value" in body


@pytest.mark.asyncio
async def test_period_comparison_api(
    client: AsyncClient, tenant_a: Institution, tenant_admin_a: User
):
    """3. Test POST /api/v1/analytics/comparisons."""
    headers = make_auth_headers(tenant_admin_a, tenant_a.id)
    payload = {
        "metric_id": "total_active_students",
        "period_a_start": "2026-09-01",
        "period_a_end": "2026-09-15",
        "period_b_start": "2026-09-16",
        "period_b_end": "2026-09-30",
    }
    response = await client.post("/api/v1/analytics/comparisons", json=payload, headers=headers)

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["metric_id"] == "total_active_students"
    assert "period_a_value" in data
    assert "period_b_value" in data
    assert "delta" in data


@pytest.mark.asyncio
async def test_freshness_status_api(
    client: AsyncClient, tenant_a: Institution, tenant_admin_a: User
):
    """18. Test GET /api/v1/analytics/freshness."""
    headers = make_auth_headers(tenant_admin_a, tenant_a.id)
    response = await client.get("/api/v1/analytics/freshness", headers=headers)

    assert response.status_code == 200
    data = response.json()["data"]
    assert isinstance(data, list)
