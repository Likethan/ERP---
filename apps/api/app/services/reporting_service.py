"""Enterprise Reporting & Analytics Orchestration Service for CampusOS.

Manages report lifecycle, immutable versioning, synchronous/asynchronous executions,
tenant-partitioned caching, snapshot preservation, and forensic audit logging.
"""

from datetime import UTC, datetime
import hashlib
import json
import logging
import re
import time
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit import build_audit_entry
from app.core.cache import TenantIsolatedCache
from app.core.exceptions import (
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.core.reporting_registry import validate_query_specification
from app.models.people import Role, User, UserRoleAssignment
from app.models.reporting import (
    ReportDefinition,
    ReportExecution,
    ReportExecutionStatus,
    ReportStatus,
    ReportVersion,
    ReportVisibility,
    SavedReport,
)
from app.schemas.reporting import (
    AnalyticsQueryResult,
    QuerySpecification,
    ReportCreate,
    ReportUpdate,
    SavedReportCreate,
)
from app.services.reporting_engine import ReportingEngine

logger = logging.getLogger("campusos.reporting.service")

# Global tenant-isolated cache instance
analytics_cache = TenantIsolatedCache()


class ReportingService:
    """Orchestrates Report Definitions, Versions, Executions, and Caching."""

    @classmethod
    def _create_audit_log(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        actor_id: UUID | None,
        action: str,
        entity_id: UUID,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Helper to safely record an audit log."""
        try:
            entry = build_audit_entry(
                tenant_id=tenant_id,
                user_id=actor_id,
                action=action,
                entity_type="Report",
                entity_id=entity_id,
                new_values_json=details,
            )
            db.add(entry)
        except Exception as exc:
            logger.warning("Audit logging failed in ReportingService: %s", exc)

    @classmethod
    async def create_report(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        payload: ReportCreate,
        actor_id: UUID | None = None,
        is_system: bool = False,
    ) -> ReportDefinition:
        """Creates a report definition with initial Version 1 and validates query specification."""
        raw_query_spec = payload.query_spec.model_dump()
        validate_query_specification(raw_query_spec)

        report_id = uuid4()
        version_id = uuid4()
        now = datetime.now(UTC)

        slug = re.sub(r'[^a-zA-Z0-9_]', '_', payload.name.lower())[:48] + f"_{uuid4().hex[:6]}"

        report = ReportDefinition(
            id=report_id,
            tenant_id=tenant_id,
            name=payload.name.strip(),
            code=slug,
            description=payload.description,
            domain=payload.domain.upper(),
            category=payload.category,
            status=ReportStatus.ACTIVE,
            visibility=payload.visibility.upper(),
            is_system=is_system,
            allowed_roles=payload.allowed_roles or [],
            active_version_id=version_id,
            created_by_user_id=actor_id,
            updated_by_user_id=actor_id,
            created_at=now,
            updated_at=now,
        )
        db.add(report)

        version = ReportVersion(
            id=version_id,
            tenant_id=tenant_id,
            report_id=report_id,
            version_number=1,
            change_summary="Initial report creation",
            query_spec_json=raw_query_spec,
            created_by_user_id=actor_id,
            is_active=True,
            created_at=now,
        )
        db.add(version)
        report.versions.append(version)

        cls._create_audit_log(
            db, tenant_id, actor_id, "REPORT_CREATED", report_id,
            {"name": report.name, "domain": report.domain, "version": 1}
        )

        await db.commit()
        return await cls.get_report(db, tenant_id, report_id)

    @classmethod
    async def get_report(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        report_id: UUID,
    ) -> ReportDefinition:
        """Fetch report ensuring strict tenant scoping."""
        stmt = (
            select(ReportDefinition)
            .options(
                selectinload(ReportDefinition.versions),
                selectinload(ReportDefinition.executions),
            )
            .where(
                and_(
                    ReportDefinition.id == report_id,
                    or_(
                        ReportDefinition.tenant_id == tenant_id,
                        ReportDefinition.is_system == True,
                    ),
                )
            )
            .execution_options(populate_existing=True)
        )
        result = await db.execute(stmt)
        report = result.scalar_one_or_none()
        if not report:
            raise NotFoundException("ReportDefinition", report_id)
        return report

    @classmethod
    async def list_reports(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        domain: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ReportDefinition], int]:
        """List reports for a tenant with pagination and optional domain filtering."""
        query = select(ReportDefinition).where(
            or_(
                ReportDefinition.tenant_id == tenant_id,
                ReportDefinition.is_system == True,
            )
        )
        if domain:
            query = query.where(ReportDefinition.domain == domain.upper())
        if status:
            query = query.where(ReportDefinition.status == status.upper())

        count_stmt = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_stmt)).scalar_one()

        paged_stmt = (
            query.options(
                selectinload(ReportDefinition.versions),
            )
            .order_by(ReportDefinition.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        results = await db.execute(paged_stmt)
        return list(results.scalars().all()), total

    @classmethod
    async def update_report(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        report_id: UUID,
        payload: ReportUpdate,
        actor_id: UUID | None = None,
    ) -> ReportDefinition:
        """Updates report metadata, and bumps version if query_spec is modified."""
        report = await cls.get_report(db, tenant_id, report_id)
        now = datetime.now(UTC)

        if payload.name is not None:
            report.name = payload.name.strip()
        if payload.description is not None:
            report.description = payload.description
        if payload.visibility is not None:
            report.visibility = payload.visibility.upper()
        if payload.allowed_roles is not None:
            report.allowed_roles = payload.allowed_roles

        if payload.query_spec:
            raw_query_spec = payload.query_spec.model_dump()
            validate_query_specification(raw_query_spec)

            new_version_num = report.active_version + 1
            new_version_id = uuid4()

            for v in report.versions:
                v.is_active = False

            new_version = ReportVersion(
                id=new_version_id,
                tenant_id=tenant_id,
                report_id=report.id,
                version_number=new_version_num,
                change_summary=payload.change_summary or f"Updated to version {new_version_num}",
                query_spec_json=raw_query_spec,
                created_by_user_id=actor_id,
                is_active=True,
                created_at=now,
            )
            db.add(new_version)
            report.active_version_id = new_version_id
            report.versions.append(new_version)

        report.updated_by_user_id = actor_id
        report.updated_at = now

        cls._create_audit_log(
            db, tenant_id, actor_id, "REPORT_UPDATED", report.id,
            {"name": report.name, "active_version": report.active_version}
        )

        await db.commit()
        return await cls.get_report(db, tenant_id, report_id)

    @classmethod
    async def execute_report(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        report_id: UUID,
        user: User,
        version_number: int | None = None,
        bypass_cache: bool = False,
        is_snapshot: bool = False,
    ) -> tuple[AnalyticsQueryResult, ReportExecution]:
        """Executes a report version, utilizing tenant-isolated caching where valid."""
        report = await cls.get_report(db, tenant_id, report_id)

        # Enforce role visibility
        user_roles: list[str] = []
        if "roles" in user.__dict__:
            user_roles = [r.role.name for r in user.roles if r and getattr(r, "role", None)]
        else:
            role_stmt = (
                select(Role.name)
                .join(UserRoleAssignment, UserRoleAssignment.role_id == Role.id)
                .where(
                    and_(
                        UserRoleAssignment.user_id == user.id,
                        UserRoleAssignment.tenant_id == tenant_id,
                    )
                )
            )
            user_roles = list((await db.execute(role_stmt)).scalars().all())

        is_admin = "SUPER_ADMIN" in user_roles or "INSTITUTION_ADMIN" in user_roles
        if report.allowed_roles and not is_admin:
            if not any(r in report.allowed_roles for r in user_roles):
                raise ForbiddenException(f"You do not have the required role to execute report '{report.name}'.")

        # Resolve target version
        if version_number:
            target_version = next((v for v in report.versions if v.version_number == version_number), None)
            if not target_version:
                raise NotFoundException(f"ReportVersion {version_number} for Report", report_id)
        else:
            target_version = next((v for v in report.versions if v.is_active), None)
            if not target_version:
                target_version = report.versions[0] if report.versions else None

        if not target_version:
            raise ValidationException("No valid report version found to execute.")

        query_spec = QuerySpecification(**target_version.query_spec)
        now = datetime.now(UTC)
        execution_id = uuid4()
        cid = str(uuid4())

        execution = ReportExecution(
            id=execution_id,
            tenant_id=tenant_id,
            report_id=report.id,
            report_version_id=target_version.id,
            requested_by_user_id=user.id,
            status=ReportExecutionStatus.RUNNING,
            query_spec_snapshot=target_version.query_spec,
            row_count=0,
            execution_time_ms=0,
            correlation_id=cid,
            is_snapshot=is_snapshot,
            started_at=now,
            created_at=now,
        )
        db.add(execution)
        await db.commit()

        # Cache check
        query_hash = hashlib.sha256(json.dumps(target_version.query_spec, sort_keys=True).encode()).hexdigest()[:16]
        cache_key = f"{report.id}:{target_version.version_number}:{query_hash}"

        cached_data = None
        if not bypass_cache and not is_snapshot:
            cached_data = await analytics_cache.get(tenant_id, "reports", cache_key)

        start_time = time.perf_counter()
        if cached_data:
            result = AnalyticsQueryResult(**cached_data)
            result.cached = True
            execution_time = int((time.perf_counter() - start_time) * 1000)
            execution.status = ReportExecutionStatus.SUCCEEDED
            execution.row_count = result.table_data.total_rows
            execution.execution_time_ms = execution_time
            execution.completed_at = datetime.now(UTC)
            await db.commit()
            return result, execution

        # Execute Query
        try:
            result = await ReportingEngine.execute_query(db, tenant_id, user, query_spec)
            execution_time = int((time.perf_counter() - start_time) * 1000)

            execution.status = ReportExecutionStatus.SUCCEEDED
            execution.row_count = result.table_data.total_rows
            execution.execution_time_ms = execution_time
            execution.completed_at = datetime.now(UTC)

            if is_snapshot:
                execution.snapshot_data = result.model_dump()

            await db.commit()

            # Cache successful result for 300 seconds
            if not is_snapshot:
                await analytics_cache.set(tenant_id, "reports", cache_key, result.model_dump(), ttl_seconds=300)

            cls._create_audit_log(
                db, tenant_id, user.id, "REPORT_EXECUTED", report.id,
                {"rows": result.table_data.total_rows, "duration_ms": execution_time}
            )
            return result, execution

        except Exception as exc:
            logger.error("Report execution %s failed: %s", execution_id, exc, exc_info=True)
            execution.status = ReportExecutionStatus.FAILED
            execution.error_code = "QUERY_EXECUTION_ERROR"
            execution.error_message = str(exc)
            execution.completed_at = datetime.now(UTC)
            await db.commit()
            raise

    @classmethod
    async def execute_adhoc_query(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        user: User,
        spec: QuerySpecification,
        bypass_cache: bool = False,
    ) -> tuple[AnalyticsQueryResult, ReportExecution]:
        """Runs an ad-hoc query specification without a preexisting report definition."""
        now = datetime.now(UTC)
        execution_id = uuid4()
        cid = str(uuid4())

        execution = ReportExecution(
            id=execution_id,
            tenant_id=tenant_id,
            report_id=None,
            report_version_id=None,
            requested_by_user_id=user.id,
            status=ReportExecutionStatus.RUNNING,
            query_spec_snapshot=spec.model_dump(),
            row_count=0,
            execution_time_ms=0,
            correlation_id=cid,
            is_snapshot=False,
            started_at=now,
            created_at=now,
        )
        db.add(execution)
        await db.commit()

        start_time = time.perf_counter()
        query_hash = hashlib.sha256(json.dumps(spec.model_dump(), sort_keys=True, default=str).encode()).hexdigest()[:16]
        cache_key = f"adhoc:{spec.dataset}:{query_hash}"

        cached_data = None
        if not bypass_cache:
            cached_data = await analytics_cache.get(tenant_id, "analytics", cache_key)

        if cached_data:
            result = AnalyticsQueryResult(**cached_data)
            result.cached = True
            execution_time = int((time.perf_counter() - start_time) * 1000)
            execution.status = ReportExecutionStatus.SUCCEEDED
            execution.row_count = result.table_data.total_rows
            execution.execution_time_ms = execution_time
            execution.completed_at = datetime.now(UTC)
            await db.commit()
            return result, execution

        try:
            result = await ReportingEngine.execute_query(db, tenant_id, user, spec)
            execution_time = int((time.perf_counter() - start_time) * 1000)

            execution.status = ReportExecutionStatus.SUCCEEDED
            execution.row_count = result.table_data.total_rows
            execution.execution_time_ms = execution_time
            execution.completed_at = datetime.now(UTC)
            await db.commit()

            await analytics_cache.set(tenant_id, "analytics", cache_key, result.model_dump(), ttl_seconds=180)
            return result, execution

        except Exception as exc:
            logger.error("Adhoc analytics query failed: %s", exc, exc_info=True)
            execution.status = ReportExecutionStatus.FAILED
            execution.error_code = "ANALYTICS_QUERY_FAILED"
            execution.error_message = str(exc)
            execution.completed_at = datetime.now(UTC)
            await db.commit()
            raise

    @classmethod
    async def cancel_execution(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        execution_id: UUID,
        actor_id: UUID | None = None,
    ) -> ReportExecution:
        """Cancels a pending or running report execution."""
        stmt = select(ReportExecution).where(
            and_(
                ReportExecution.id == execution_id,
                ReportExecution.tenant_id == tenant_id,
            )
        )
        execution = (await db.execute(stmt)).scalar_one_or_none()
        if not execution:
            raise NotFoundException("ReportExecution", execution_id)

        if execution.status in (ReportExecutionStatus.SUCCEEDED, ReportExecutionStatus.FAILED):
            raise ValidationException(f"Cannot cancel execution in terminal status '{execution.status}'.")

        execution.status = ReportExecutionStatus.CANCELLED
        execution.completed_at = datetime.now(UTC)
        cls._create_audit_log(db, tenant_id, actor_id, "REPORT_EXECUTION_CANCELLED", execution.id)
        await db.commit()
        return execution

    @classmethod
    async def save_user_report(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        payload: SavedReportCreate,
    ) -> SavedReport:
        """Saves a personalized query configuration."""
        raw_spec = payload.query_spec.model_dump()
        validate_query_specification(raw_spec)

        saved = SavedReport(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            report_id=payload.report_id,
            name=payload.name.strip(),
            description=payload.description,
            query_spec_json=raw_spec,
            is_favorite=payload.is_favorite,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        db.add(saved)
        await db.commit()
        await db.refresh(saved)
        return saved

    @classmethod
    async def list_saved_reports(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
    ) -> list[SavedReport]:
        """Lists saved reports for the authenticated user in the tenant."""
        stmt = (
            select(SavedReport)
            .where(
                and_(
                    SavedReport.tenant_id == tenant_id,
                    SavedReport.user_id == user_id,
                )
            )
            .order_by(SavedReport.created_at.desc())
        )
        return list((await db.execute(stmt)).scalars().all())
