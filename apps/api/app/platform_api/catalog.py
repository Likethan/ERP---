"""API Product Catalog, Classifications & Version Lifecycle Management (Step 21).

Enforces:
- Explicit API classification: endpoints default to INTERNAL_ONLY and require explicit promotion.
- Catalog definitions for consumable domain APIs (Students, Academics, Attendance, Examinations, Finance, Events).
- Strict API versioning (/api/v1/platform/v1/...) and deprecation lifecycle headers (Deprecation, Sunset, Link).
- Version changelog tracking.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Final

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.platform_api.models import (
    ApiChangelog,
    ApiClassification,
    ApiLifecycleStatus,
    ApiOperation,
    ApiProduct,
)
from app.platform_api.scopes import (
    SCOPE_ACADEMICS_READ,
    SCOPE_ATTENDANCE_READ,
    SCOPE_EVENTS_READ,
    SCOPE_EXAMINATIONS_READ,
    SCOPE_FINANCE_READ,
    SCOPE_FINANCE_WRITE,
    SCOPE_STUDENTS_READ,
)


@dataclass(frozen=True)
class CatalogOperationDef:
    method: str
    path: str
    version: str
    summary: str
    description: str
    scope_required: str
    classification: str
    rate_limit_policy: str = "DEFAULT"
    governance_policy: str = "STANDARD"
    status: str = ApiLifecycleStatus.ACTIVE.value
    deprecated_at: datetime | None = None
    sunset_at: datetime | None = None
    replacement_path: str | None = None
    migration_notes: str | None = None


@dataclass(frozen=True)
class CatalogProductDef:
    code: str
    name: str
    description: str
    version: str
    status: str
    operations: list[CatalogOperationDef] = field(default_factory=list)


# -----------------------------------------------------------------------------
# Canonical Catalog Definitions
# -----------------------------------------------------------------------------

CATALOG_PRODUCTS: Final[list[CatalogProductDef]] = [
    CatalogProductDef(
        code="students",
        name="Students API",
        description="Access institutional student directories, enrollments, and profiles",
        version="v1",
        status=ApiLifecycleStatus.ACTIVE.value,
        operations=[
            CatalogOperationDef(
                method="GET",
                path="/api/v1/platform/v1/students",
                version="v1",
                summary="List student directory with cursor pagination and field governance",
                description="Returns allowlisted student attributes with sensitive PII masked",
                scope_required=SCOPE_STUDENTS_READ,
                classification=ApiClassification.PARTNER_API.value,
            ),
            CatalogOperationDef(
                method="GET",
                path="/api/v1/platform/v1/students/{id}",
                version="v1",
                summary="Get student details by ID",
                description="Fetch single student record governed by field masking policies",
                scope_required=SCOPE_STUDENTS_READ,
                classification=ApiClassification.PARTNER_API.value,
            ),
        ],
    ),
    CatalogProductDef(
        code="academics",
        name="Academics API",
        description="Query curriculum schemes, courses, and syllabus structures",
        version="v1",
        status=ApiLifecycleStatus.ACTIVE.value,
        operations=[
            CatalogOperationDef(
                method="GET",
                path="/api/v1/platform/v1/courses",
                version="v1",
                summary="List academic courses",
                description="Retrieve course offerings, credit allocations, and descriptions",
                scope_required=SCOPE_ACADEMICS_READ,
                classification=ApiClassification.PUBLIC_READ.value,
            ),
            CatalogOperationDef(
                method="GET",
                path="/api/v1/platform/v1/curriculum",
                version="v1",
                summary="Get curriculum schemes",
                description="Retrieve program curriculum regulations and credit structures",
                scope_required=SCOPE_ACADEMICS_READ,
                classification=ApiClassification.PUBLIC_READ.value,
            ),
        ],
    ),
    CatalogProductDef(
        code="attendance",
        name="Attendance API",
        description="Query attendance logs and student compliance statistics",
        version="v1",
        status=ApiLifecycleStatus.ACTIVE.value,
        operations=[
            CatalogOperationDef(
                method="GET",
                path="/api/v1/platform/v1/attendance",
                version="v1",
                summary="Query attendance records",
                description="Returns student attendance sessions with date filtering",
                scope_required=SCOPE_ATTENDANCE_READ,
                classification=ApiClassification.TENANT_API.value,
            ),
        ],
    ),
    CatalogProductDef(
        code="examinations",
        name="Examinations API",
        description="Read published assessment marks, grades, and GPA results",
        version="v1",
        status=ApiLifecycleStatus.ACTIVE.value,
        operations=[
            CatalogOperationDef(
                method="GET",
                path="/api/v1/platform/v1/examinations/results",
                version="v1",
                summary="Query student exam results",
                description="Retrieve published semester examination grades and marks",
                scope_required=SCOPE_EXAMINATIONS_READ,
                classification=ApiClassification.TENANT_API.value,
            ),
        ],
    ),
    CatalogProductDef(
        code="finance",
        name="Finance API",
        description="Inspect student fee invoices and record payments with idempotency",
        version="v1",
        status=ApiLifecycleStatus.ACTIVE.value,
        operations=[
            CatalogOperationDef(
                method="GET",
                path="/api/v1/platform/v1/finance/invoices",
                version="v1",
                summary="List student fee invoices",
                description="Query invoice line items, balances due, and payment status",
                scope_required=SCOPE_FINANCE_READ,
                classification=ApiClassification.TENANT_API.value,
            ),
            CatalogOperationDef(
                method="POST",
                path="/api/v1/platform/v1/finance/payments",
                version="v1",
                summary="Record payment transaction",
                description="Atomic payment submission requiring Idempotency-Key header",
                scope_required=SCOPE_FINANCE_WRITE,
                classification=ApiClassification.TENANT_API.value,
            ),
        ],
    ),
    CatalogProductDef(
        code="events",
        name="Campus Events API",
        description="Discover public campus events, student club activities, and schedules",
        version="v1",
        status=ApiLifecycleStatus.ACTIVE.value,
        operations=[
            CatalogOperationDef(
                method="GET",
                path="/api/v1/platform/v1/events",
                version="v1",
                summary="List campus events",
                description="Returns public calendar of verified institutional events",
                scope_required=SCOPE_EVENTS_READ,
                classification=ApiClassification.PUBLIC_READ.value,
            ),
        ],
    ),
]


class CatalogService:
    """Manages the API product catalog, operation classifications, and changelogs."""

    @classmethod
    async def seed_catalog_idempotently(cls, db: AsyncSession) -> None:
        """Seed API products, operations, and changelog records into the database."""
        for prod_def in CATALOG_PRODUCTS:
            stmt = select(ApiProduct).where(ApiProduct.code == prod_def.code)
            res = await db.execute(stmt)
            product = res.scalar_one_or_none()

            if not product:
                product = ApiProduct(
                    code=prod_def.code,
                    name=prod_def.name,
                    description=prod_def.description,
                    version=prod_def.version,
                    status=prod_def.status,
                )
                db.add(product)
                await db.flush()

            for op_def in prod_def.operations:
                op_stmt = select(ApiOperation).where(
                    ApiOperation.method == op_def.method,
                    ApiOperation.path == op_def.path,
                    ApiOperation.version == op_def.version,
                )
                op_res = await db.execute(op_stmt)
                operation = op_res.scalar_one_or_none()

                if not operation:
                    operation = ApiOperation(
                        product_id=product.id,
                        method=op_def.method,
                        path=op_def.path,
                        version=op_def.version,
                        summary=op_def.summary,
                        description=op_def.description,
                        scope_required=op_def.scope_required,
                        classification=op_def.classification,
                        rate_limit_policy=op_def.rate_limit_policy,
                        governance_policy=op_def.governance_policy,
                        status=op_def.status,
                        deprecated_at=op_def.deprecated_at,
                        sunset_at=op_def.sunset_at,
                        replacement_path=op_def.replacement_path,
                        migration_notes=op_def.migration_notes,
                    )
                    db.add(operation)

        # Seed initial changelog
        changelog_stmt = select(ApiChangelog).where(ApiChangelog.version == "v1.0.0")
        ch_res = await db.execute(changelog_stmt)
        if not ch_res.scalar_one_or_none():
            changelog = ApiChangelog(
                version="v1.0.0",
                release_date=datetime.now(UTC),
                changes=[
                    "Initial release of CampusOS Enterprise API Platform (Step 21)",
                    "Introduced Students, Academics, Attendance, Examinations, Finance, and Events public APIs",
                    "Added cryptographically secure API keys, safe rotation, and application scoping",
                    "Integrated multi-period quotas and sliding-window rate limiting",
                ],
                breaking_changes=[],
                deprecated_operations=[],
                migration_notes="Base platform API release. All external endpoints versioned under /api/v1/platform/v1/.",
            )
            db.add(changelog)

        await db.flush()

    @classmethod
    async def get_operation_metadata(
        cls, db: AsyncSession, method: str, path: str, version: str = "v1"
    ) -> ApiOperation | None:
        """Lookup operation definition to check classification, scope, and deprecation."""
        stmt = select(ApiOperation).where(
            ApiOperation.method == method.upper(),
            ApiOperation.path == path,
            ApiOperation.version == version,
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()


catalog_service = CatalogService()
