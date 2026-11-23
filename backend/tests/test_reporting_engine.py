"""Comprehensive Test Suite for CampusOS Step 18 — Enterprise Reporting & Analytics.

Tests:
1. Dataset, Metric, and Dimension Registries & Specification Validation
2. ReportingEngine Domain Aggregations & Canonical Formula Integrity
3. Report Definition CRUD, Immutable Versioning, and DAG Preservations
4. Report Execution, Tenant-Partitioned Caching & Snapshots
5. Report Export Service, Storage Isolation & Formula Injection Defense
6. Tenant Scoping, Cross-Tenant Isolation & PBAC Authorization
7. Reporting and Analytics API Endpoints
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ValidationException
from app.core.export_security import sanitize_csv_field
from app.core.permissions import DEFAULT_ROLE_PERMISSIONS
from app.core.reporting_registry import (
    DATASET_REGISTRY,
    METRIC_REGISTRY,
    validate_query_specification,
)
from app.core.security import ACCESS_TOKEN_COOKIE_NAME, create_access_token
from app.models.core import Institution
from app.models.people import User
from app.models.reporting import (
    ReportExecutionStatus,
    ReportExportFormat,
    ReportStatus,
)
from app.schemas.reporting import (
    QuerySpecification,
    ReportCreate,
    ReportUpdate,
)
from app.services.report_export_service import ReportExportService
from app.services.reporting_engine import ReportingEngine
from app.services.reporting_service import ReportingService, analytics_cache


def make_auth_headers(
    user: User,
    tenant_id: uuid.UUID,
    role_name: str = "INSTITUTION_ADMIN",
    custom_permissions: list[str] | None = None,
) -> dict[str, str]:
    perms = custom_permissions if custom_permissions is not None else DEFAULT_ROLE_PERMISSIONS.get(role_name, [])
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
# 1. DATASET, METRIC & QUERY SPECIFICATION VALIDATION TESTS
# =============================================================================

class TestDatasetAndMetricRegistries:
    def test_canonical_datasets_registered(self):
        expected_datasets = {
            "students",
            "faculty",
            "attendance",
            "examinations",
            "finance",
            "placement",
            "campus_events",
            "infrastructure",
            "documents",
            "cross_domain_student_success",
        }
        for ds in expected_datasets:
            assert ds in DATASET_REGISTRY
            dataset_def = DATASET_REGISTRY[ds]
            assert len(dataset_def.allowed_dimensions) > 0
            assert len(dataset_def.allowed_measures) > 0
            assert len(dataset_def.allowed_filters) > 0

    def test_canonical_metrics_registered(self):
        expected_metrics = [
            "total_students",
            "attendance_percentage",
            "pass_percentage",
            "total_invoiced",
            "total_collected",
            "total_outstanding",
            "fee_collection_rate",
            "placement_rate",
            "hostel_occupancy_rate",
            "document_compliance_rate",
        ]
        for m in expected_metrics:
            assert m in METRIC_REGISTRY
            metric_def = METRIC_REGISTRY[m]
            assert metric_def.formula is not None
            assert metric_def.aggregation in ("COUNT", "SUM", "AVG", "RATIO", "PERCENTAGE")

    def test_query_spec_validation_success(self):
        valid_spec = {
            "dataset": "attendance",
            "dimensions": ["department"],
            "measures": ["attendance_percentage"],
            "filters": [{"field": "department", "operator": "=", "value": "CSE"}],
            "limit": 50,
        }
        # Should not raise
        validate_query_specification(valid_spec)

    def test_query_spec_validation_rejections(self):
        # 1. Unknown dataset
        with pytest.raises(ValidationException, match="Dataset 'unknown_dataset' does not exist"):
            validate_query_specification({"dataset": "unknown_dataset", "measures": ["count"]})

        # 2. Disallowed dimension
        with pytest.raises(ValidationException, match="Dimension 'credit_card' is not allowed"):
            validate_query_specification({
                "dataset": "students",
                "dimensions": ["credit_card"],
                "measures": ["total_students"],
            })

        # 3. Disallowed measure
        with pytest.raises(ValidationException, match="Measure 'hack_database' is not allowed"):
            validate_query_specification({
                "dataset": "finance",
                "dimensions": ["academic_year"],
                "measures": ["hack_database"],
            })

        # 4. Disallowed filter operator
        with pytest.raises(ValidationException, match="Filter operator 'EXEC_SQL' is not supported"):
            validate_query_specification({
                "dataset": "attendance",
                "measures": ["attendance_percentage"],
                "filters": [{"field": "department", "operator": "EXEC_SQL", "value": "x"}],
            })

        # 5. Invalid limit
        with pytest.raises(ValidationException, match="Query 'limit' must be an integer between 1 and 10000"):
            validate_query_specification({
                "dataset": "students",
                "measures": ["total_students"],
                "limit": 50000,
            })


# =============================================================================
# 2. REPORTING ENGINE DOMAIN AGGREGATIONS TESTS
# =============================================================================

class TestReportingEngineAggregations:
    @pytest.mark.asyncio
    async def test_students_query_execution(self, db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User):
        spec = QuerySpecification(
            dataset="students",
            dimensions=["department"],
            measures=["total_students", "active_students"],
        )
        res = await ReportingEngine.execute_query(db_session, tenant_a.id, tenant_admin_a, spec)
        assert res.title.startswith("Student Headcount")
        assert len(res.labels) > 0
        assert len(res.datasets) == 2
        assert res.table_data.total_rows > 0

    @pytest.mark.asyncio
    async def test_attendance_query_execution(self, db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User):
        spec = QuerySpecification(
            dataset="attendance",
            dimensions=["department"],
            measures=["attendance_percentage"],
        )
        res = await ReportingEngine.execute_query(db_session, tenant_a.id, tenant_admin_a, spec)
        assert "Attendance" in res.title
        assert len(res.labels) > 0
        assert len(res.datasets[0].data) == len(res.labels)
        # All percentages bounded between 0 and 100
        for val in res.datasets[0].data:
            assert 0.0 <= float(val) <= 100.0

    @pytest.mark.asyncio
    async def test_finance_query_execution(self, db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User):
        spec = QuerySpecification(
            dataset="finance",
            measures=["total_invoiced", "total_collected", "total_outstanding", "fee_collection_rate"],
        )
        res = await ReportingEngine.execute_query(db_session, tenant_a.id, tenant_admin_a, spec)
        assert "Billing & Collection" in res.title
        assert len(res.table_data.rows) >= 4
        # Provenance returned
        assert res.provenance.dataset == "finance"
        assert res.provenance.tenant_id == str(tenant_a.id)

    @pytest.mark.asyncio
    async def test_cross_domain_synthesis(self, db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User):
        spec = QuerySpecification(
            dataset="cross_domain_student_success",
            dimensions=["department"],
            measures=["attendance_percentage", "pass_percentage", "placement_rate"],
        )
        res = await ReportingEngine.execute_query(db_session, tenant_a.id, tenant_admin_a, spec)
        assert len(res.datasets) == 3
        assert res.datasets[0].name.startswith("Attendance")
        assert res.datasets[1].name.startswith("Pass Rate")
        assert res.datasets[2].name.startswith("Placement Rate")


# =============================================================================
# 3. REPORT DEFINITION LIFECYCLE & VERSIONING TESTS
# =============================================================================

class TestReportDefinitionLifecycleAndVersioning:
    @pytest.mark.asyncio
    async def test_report_crud_and_version_bump(self, db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User):
        # 1. Create Report Definition (Initial Version 1)
        payload = ReportCreate(
            name="Department Attendance Summary",
            description="Daily departmental attendance breakdown",
            domain="ATTENDANCE",
            category="OPERATIONAL",
            visibility="ROLE",
            allowed_roles=["INSTITUTION_ADMIN", "HOD"],
            query_spec=QuerySpecification(
                dataset="attendance",
                dimensions=["department"],
                measures=["attendance_percentage"],
            ),
        )
        report = await ReportingService.create_report(
            db=db_session,
            tenant_id=tenant_a.id,
            payload=payload,
            actor_id=tenant_admin_a.id,
        )

        assert report.status == ReportStatus.ACTIVE
        assert report.active_version == 1
        assert len(report.versions) == 1
        assert report.versions[0].version_number == 1
        assert report.versions[0].is_active is True

        # 2. Update Query Spec bumps version to 2
        update_payload = ReportUpdate(
            description="Updated to include student counts",
            query_spec=QuerySpecification(
                dataset="attendance",
                dimensions=["department"],
                measures=["attendance_percentage", "total_sessions"],
            ),
            change_summary="Added total sessions measure",
        )
        updated = await ReportingService.update_report(
            db=db_session,
            tenant_id=tenant_a.id,
            report_id=report.id,
            payload=update_payload,
            actor_id=tenant_admin_a.id,
        )

        assert updated.active_version == 2
        assert len(updated.versions) == 2
        v1 = next(v for v in updated.versions if v.version_number == 1)
        v2 = next(v for v in updated.versions if v.version_number == 2)
        assert v1.is_active is False
        assert v2.is_active is True
        assert v2.change_summary == "Added total sessions measure"


# =============================================================================
# 4. REPORT EXECUTION, CACHING & SNAPSHOTS TESTS
# =============================================================================

class TestReportExecutionAndCaching:
    @pytest.mark.asyncio
    async def test_report_execution_and_caching(self, db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User):
        # Create report
        payload = ReportCreate(
            name="Fee Collections Overview",
            domain="FINANCE",
            query_spec=QuerySpecification(
                dataset="finance",
                measures=["total_invoiced", "total_collected"],
            ),
        )
        report = await ReportingService.create_report(db_session, tenant_a.id, payload, actor_id=tenant_admin_a.id)

        # First execution (computes and caches)
        res1, exec1 = await ReportingService.execute_report(
            db=db_session,
            tenant_id=tenant_a.id,
            report_id=report.id,
            user=tenant_admin_a,
            bypass_cache=True,
        )
        assert exec1.status == ReportExecutionStatus.SUCCEEDED
        assert exec1.row_count > 0
        assert res1.cached is False

        # Second execution (hits cache)
        res2, exec2 = await ReportingService.execute_report(
            db=db_session,
            tenant_id=tenant_a.id,
            report_id=report.id,
            user=tenant_admin_a,
            bypass_cache=False,
        )
        assert exec2.status == ReportExecutionStatus.SUCCEEDED
        assert res2.cached is True

    @pytest.mark.asyncio
    async def test_immutable_report_snapshot(self, db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User):
        payload = ReportCreate(
            name="Annual Exam Outcomes",
            domain="EXAMINATIONS",
            query_spec=QuerySpecification(
                dataset="examinations",
                dimensions=["department"],
                measures=["pass_percentage"],
            ),
        )
        report = await ReportingService.create_report(db_session, tenant_a.id, payload, actor_id=tenant_admin_a.id)

        # Snapshot execution
        res, exec_rec = await ReportingService.execute_report(
            db=db_session,
            tenant_id=tenant_a.id,
            report_id=report.id,
            user=tenant_admin_a,
            is_snapshot=True,
        )
        assert exec_rec.is_snapshot is True
        assert exec_rec.snapshot_data is not None
        assert "labels" in exec_rec.snapshot_data
        assert "datasets" in exec_rec.snapshot_data


# =============================================================================
# 5. REPORT EXPORT & FORMULA INJECTION DEFENSE TESTS
# =============================================================================

class TestReportExportAndFormulaSanitization:
    def test_csv_formula_injection_defense(self):
        dangerous_payloads = [
            "=cmd|' /C calc'!A0",
            "+1+2",
            "-5+10",
            "@SUM(1,2)",
            "\tTAB_ATTACK",
            "\rCR_ATTACK",
        ]
        for val in dangerous_payloads:
            sanitized = sanitize_csv_field(val)
            assert sanitized.startswith("'"), f"Dangerous formula '{val}' was not escaped with leading quote!"

        safe_val = "Computer Science"
        assert sanitize_csv_field(safe_val) == "Computer Science"

    @pytest.mark.asyncio
    async def test_export_generation_and_download(self, db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User):
        payload = ReportCreate(
            name="Placement Report for Export",
            domain="PLACEMENT",
            query_spec=QuerySpecification(
                dataset="placement",
                dimensions=["department"],
                measures=["placement_offers"],
            ),
        )
        report = await ReportingService.create_report(db_session, tenant_a.id, payload, actor_id=tenant_admin_a.id)
        result, execution = await ReportingService.execute_report(db_session, tenant_a.id, report.id, tenant_admin_a)

        # Create CSV Export
        export = await ReportExportService.create_export(
            db=db_session,
            tenant_id=tenant_a.id,
            execution=execution,
            result_data=result,
            export_format=ReportExportFormat.CSV,
        )
        assert export.export_format == "CSV"
        assert export.file_size_bytes > 0
        assert export.download_count == 0

        # Download Export
        file_bytes, fetched_export = await ReportExportService.get_export_file(
            db=db_session,
            tenant_id=tenant_a.id,
            export_id=export.id,
        )
        assert len(file_bytes) == export.file_size_bytes
        assert fetched_export.download_count == 1
        assert b"Department" in file_bytes


# =============================================================================
# 6. TENANT ISOLATION & AUTHORIZATION TESTS
# =============================================================================

class TestTenantIsolationAndSecurity:
    @pytest.mark.asyncio
    async def test_cross_tenant_report_isolation(
        self, db_session: AsyncSession, tenant_a: Institution, tenant_b: Institution, tenant_admin_a: User
    ):
        # Create report in Tenant A
        payload = ReportCreate(
            name="Confidential Tenant A Finance",
            domain="FINANCE",
            query_spec=QuerySpecification(
                dataset="finance",
                measures=["total_invoiced"],
            ),
        )
        report_a = await ReportingService.create_report(db_session, tenant_a.id, payload, actor_id=tenant_admin_a.id)

        # Tenant B attempt to get report -> NotFoundException
        with pytest.raises(NotFoundException):
            await ReportingService.get_report(db_session, tenant_b.id, report_a.id)

    @pytest.mark.asyncio
    async def test_tenant_partitioned_cache_isolation(self, tenant_a: Institution, tenant_b: Institution):
        cache_key = "test_metric_hash"
        data_a = {"tenant": "A", "val": 100}
        data_b = {"tenant": "B", "val": 200}

        await analytics_cache.set(tenant_a.id, "reports", cache_key, data_a)
        await analytics_cache.set(tenant_b.id, "reports", cache_key, data_b)

        fetched_a = await analytics_cache.get(tenant_a.id, "reports", cache_key)
        fetched_b = await analytics_cache.get(tenant_b.id, "reports", cache_key)

        assert fetched_a["tenant"] == "A"
        assert fetched_b["tenant"] == "B"
        assert fetched_a != fetched_b


# =============================================================================
# 7. REPORTING API ENDPOINTS TESTS
# =============================================================================

class TestReportingAPIEndpoints:
    @pytest.mark.asyncio
    async def test_api_report_lifecycle_and_execution(
        self, client: AsyncClient, tenant_a: Institution, tenant_admin_a: User
    ):
        headers = make_auth_headers(tenant_admin_a, tenant_a.id)

        # 1. Create Report via API
        create_payload = {
            "name": "API Faculty Report",
            "domain": "PEOPLE",
            "category": "STAFFING",
            "visibility": "ROLE",
            "allowed_roles": ["INSTITUTION_ADMIN"],
            "query_spec": {
                "dataset": "faculty",
                "dimensions": ["department"],
                "measures": ["faculty_count"],
            },
        }
        res = await client.post("/api/v1/reports", json=create_payload, headers=headers)
        assert res.status_code == 201
        report_data = res.json()["data"]
        report_id = report_data["id"]

        # 2. List Reports
        list_res = await client.get("/api/v1/reports", headers=headers)
        assert list_res.status_code == 200
        items = list_res.json()["data"]
        assert any(r["id"] == report_id for r in items)

        # 3. Execute Report
        exec_res = await client.post(f"/api/v1/reports/{report_id}/execute", headers=headers)
        assert exec_res.status_code == 200
        exec_body = exec_res.json()["data"]
        assert exec_body["execution"]["status"] == "SUCCEEDED"
        assert "result" in exec_body
        assert exec_body["result"]["title"].startswith("Faculty Staffing")

        # 4. Introspect Registries
        ds_res = await client.get("/api/v1/datasets", headers=headers)
        assert ds_res.status_code == 200
        assert len(ds_res.json()["data"]) >= 10

        metrics_res = await client.get("/api/v1/metrics", headers=headers)
        assert metrics_res.status_code == 200
        assert len(metrics_res.json()["data"]) >= 15

        # 5. Ad-Hoc Analytics Query
        adhoc_res = await client.post(
            "/api/v1/analytics/query",
            json={
                "dataset": "attendance",
                "dimensions": ["department"],
                "measures": ["attendance_percentage"],
            },
            headers=headers,
        )
        assert adhoc_res.status_code == 200
        assert "Attendance" in adhoc_res.json()["data"]["title"]
