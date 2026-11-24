"""Platform Administration Router: Multi-tenant SaaS lifecycle, operations & governance APIs.

Restricted exclusively to Platform Administrators and authorized platform operators.
Tenant Administrators and regular users have NO access to these endpoints.
"""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import require_platform_admin
from app.models.core import Institution
from app.models.people import User
from app.schemas.common import ApiResponse
from app.schemas.core import (
    TenantCreateRequest,
    TenantResponse,
    TenantStatusUpdateRequest,
)
from app.schemas.platform_ops import (
    PlatformOperationalHealthResponse,
    PlatformSupportSessionCreateRequest,
    PlatformSupportSessionResponse,
    TenantDeletionExecuteRequest,
    TenantDeletionPlanResponse,
    TenantDeletionPreviewResponse,
    TenantEntitlementResponse,
    TenantEntitlementUpdateRequest,
    TenantLifecycleTransitionRequest,
    TenantLifecycleTransitionResponse,
    TenantOnboardRequest,
    TenantProvisioningStatusResponse,
    TenantQuotaOverrideRequest,
    TenantQuotaSummaryResponse,
)
from app.services.entitlement_service import EntitlementService
from app.services.platform_health_service import PlatformHealthService
from app.services.platform_support_service import PlatformSupportService
from app.services.tenant_governance_lifecycle_service import (
    TenantGovernanceLifecycleService,
)
from app.services.tenant_lifecycle_service import TenantLifecycleService
from app.services.tenant_provisioning_service import TenantProvisioningService
from app.services.tenant_quota_service import TenantQuotaService

router = APIRouter(prefix="/platform", tags=["Platform Administration"])


# =============================================================================
# 1. TENANT DIRECTORY & ONBOARDING
# =============================================================================


@router.get("/tenants", response_model=list[TenantResponse])
async def list_all_tenants(
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status_filter: str | None = Query(None, alias="status"),
    plan_filter: str | None = Query(None, alias="plan"),
    search: str | None = Query(None, alias="search"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[TenantResponse]:
    """List all institutions/tenants across the entire SaaS platform with filtering."""
    stmt = select(Institution)
    if status_filter:
        stmt = stmt.where(Institution.status == status_filter.upper())
    if plan_filter:
        stmt = stmt.where(Institution.plan == plan_filter.upper())
    if search:
        s_pattern = f"%{search.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Institution.code).like(s_pattern),
                func.lower(Institution.legal_name).like(s_pattern),
                func.lower(Institution.short_name).like(s_pattern),
                func.lower(Institution.contact_email).like(s_pattern),
            )
        )
    stmt = stmt.order_by(desc(Institution.created_at)).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant_by_id(
    tenant_id: UUID,
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TenantResponse:
    """Retrieve full operational profile for a specific tenant across the platform."""
    return await TenantLifecycleService.get_tenant_by_id(db, tenant_id)


@router.post("/tenants", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    data: TenantOnboardRequest | TenantCreateRequest,
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TenantResponse:
    """Transactionally provision and onboard a new SaaS institution tenant."""
    if isinstance(data, TenantCreateRequest):
        onboard_dto = TenantOnboardRequest(
            code=data.code,
            slug=data.slug,
            legal_name=data.legal_name,
            short_name=data.short_name,
            plan=data.plan,
            contact_email=data.contact_email,
            contact_phone=data.contact_phone,
            address_line1=data.address_line1,
            city=data.city,
            state=data.state,
            postal_code=data.postal_code,
            country=data.country,
            default_timezone=data.default_timezone,
            currency_code=data.currency_code,
            locale=data.locale,
            admin_email=data.contact_email,
        )
    else:
        onboard_dto = data

    tenant, _ = await TenantProvisioningService.provision_tenant(
        db=db, data=onboard_dto, actor_id=_admin.id
    )
    return tenant


@router.patch("/tenants/{tenant_id}/status", response_model=TenantResponse)
async def update_tenant_status(
    tenant_id: UUID,
    payload: TenantStatusUpdateRequest,
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TenantResponse:
    """Legacy endpoint: Transition tenant operational status via lifecycle service."""
    tenant, _ = await TenantLifecycleService.transition_tenant_status(
        db=db,
        tenant_id=tenant_id,
        target_status=payload.status,
        actor_id=_admin.id,
        actor_email=_admin.email,
        reason=payload.reason or f"Status changed to {payload.status}",
    )
    return tenant


# =============================================================================
# 2. LIFECYCLE STATE MACHINE & TRANSITIONS
# =============================================================================


@router.post(
    "/tenants/{tenant_id}/lifecycle/transition",
    response_model=TenantLifecycleTransitionResponse,
)
async def transition_tenant_lifecycle(
    tenant_id: UUID,
    payload: TenantLifecycleTransitionRequest,
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TenantLifecycleTransitionResponse:
    """Execute a guarded, transactional state machine transition in tenant lifecycle."""
    _, transition = await TenantLifecycleService.transition_tenant_status(
        db=db,
        tenant_id=tenant_id,
        target_status=payload.target_status,
        actor_id=_admin.id,
        actor_email=_admin.email,
        reason=payload.reason,
        correlation_id=payload.correlation_id,
        metadata=payload.metadata,
    )
    return TenantLifecycleTransitionResponse.model_validate(transition)


@router.get(
    "/tenants/{tenant_id}/lifecycle/history",
    response_model=list[TenantLifecycleTransitionResponse],
)
async def get_tenant_lifecycle_history(
    tenant_id: UUID,
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[TenantLifecycleTransitionResponse]:
    """Retrieve full chronological audit history of tenant lifecycle transitions."""
    transitions = await TenantLifecycleService.get_lifecycle_history(
        db=db, tenant_id=tenant_id, limit=limit, offset=offset
    )
    return [TenantLifecycleTransitionResponse.model_validate(t) for t in transitions]


# =============================================================================
# 3. PROVISIONING PIPELINE TRACKING & RETRY
# =============================================================================


@router.get(
    "/tenants/{tenant_id}/provision/status",
    response_model=TenantProvisioningStatusResponse,
)
async def get_tenant_provisioning_status(
    tenant_id: UUID,
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TenantProvisioningStatusResponse:
    """Inspect detailed stage-by-stage status of the tenant onboarding pipeline."""
    return await TenantProvisioningService.get_provisioning_status(db=db, tenant_id=tenant_id)


@router.post(
    "/tenants/{tenant_id}/provision/retry",
    response_model=TenantProvisioningStatusResponse,
)
async def retry_tenant_provisioning(
    tenant_id: UUID,
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TenantProvisioningStatusResponse:
    """Idempotently resume a partially completed or failed tenant onboarding pipeline."""
    return await TenantProvisioningService.retry_provisioning(
        db=db, tenant_id=tenant_id, actor_id=_admin.id
    )


# =============================================================================
# 4. SUBSCRIPTION, LICENSING & FEATURE ENTITLEMENTS
# =============================================================================


@router.get(
    "/tenants/{tenant_id}/entitlements",
    response_model=TenantEntitlementResponse,
)
async def get_tenant_entitlements(
    tenant_id: UUID,
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TenantEntitlementResponse:
    """Inspect current commercial plan, module gates, and feature entitlements for a tenant."""
    ent = await EntitlementService.get_entitlements(db=db, tenant_id=tenant_id)
    return TenantEntitlementResponse.model_validate(ent)


@router.put(
    "/tenants/{tenant_id}/entitlements",
    response_model=TenantEntitlementResponse,
)
async def update_tenant_entitlements(
    tenant_id: UUID,
    dto: TenantEntitlementUpdateRequest,
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TenantEntitlementResponse:
    """Update commercial plan or apply granular feature and quota entitlements."""
    ent = await EntitlementService.update_entitlements(
        db=db, tenant_id=tenant_id, dto=dto, actor_id=_admin.id
    )
    return TenantEntitlementResponse.model_validate(ent)


# =============================================================================
# 5. TENANT QUOTAS & RESOURCE GOVERNANCE
# =============================================================================


@router.get(
    "/tenants/{tenant_id}/quotas",
    response_model=TenantQuotaSummaryResponse,
)
async def get_tenant_quotas(
    tenant_id: UUID,
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TenantQuotaSummaryResponse:
    """Inspect resource consumption, soft/hard limits, and warning threshold states."""
    return await TenantQuotaService.get_quota_summary(db=db, tenant_id=tenant_id)


@router.post(
    "/tenants/{tenant_id}/quotas/override",
    response_model=dict[str, Any],
)
async def override_tenant_quota(
    tenant_id: UUID,
    dto: TenantQuotaOverrideRequest,
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, Any]:
    """Apply administrative override to an institutional resource quota limit."""
    quota = await TenantQuotaService.override_quota(
        db=db, tenant_id=tenant_id, dto=dto, actor_id=_admin.id
    )
    return {
        "tenant_id": str(tenant_id),
        "resource_type": quota.resource_type,
        "hard_limit": quota.hard_limit,
        "soft_limit": quota.soft_limit,
        "warning_threshold_percent": quota.warning_threshold_percent,
        "status": "updated",
    }


# =============================================================================
# 6. CONTROLLED PLATFORM SUPPORT ACCESS
# =============================================================================


@router.post(
    "/tenants/{tenant_id}/support-access",
    response_model=PlatformSupportSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_support_session(
    tenant_id: UUID,
    dto: PlatformSupportSessionCreateRequest,
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> PlatformSupportSessionResponse:
    """Establish a time-limited, purpose-justified, and audited support delegation session."""
    session = await PlatformSupportService.create_support_session(
        db=db,
        tenant_id=tenant_id,
        operator_user_id=_admin.id,
        reason=dto.reason,
        duration_hours=dto.duration_hours,
        ticket_reference=dto.ticket_reference,
        permissions_scope=dto.permissions_scope,
    )
    return PlatformSupportSessionResponse.model_validate(session)


@router.delete(
    "/tenants/{tenant_id}/support-access/{session_id}",
    response_model=PlatformSupportSessionResponse,
)
async def revoke_support_session(
    tenant_id: UUID,
    session_id: UUID,
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    reason: str = Query("Manual administrative revocation", alias="reason"),
) -> PlatformSupportSessionResponse:
    """Immediately revoke an active platform support session."""
    session = await PlatformSupportService.revoke_support_session(
        db=db, session_id=session_id, revoked_by_id=_admin.id, reason=reason
    )
    return PlatformSupportSessionResponse.model_validate(session)


@router.get(
    "/tenants/{tenant_id}/support-access/history",
    response_model=list[PlatformSupportSessionResponse],
)
async def list_support_sessions_history(
    tenant_id: UUID,
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[PlatformSupportSessionResponse]:
    """Retrieve historical support access records for audit compliance."""
    sessions = await PlatformSupportService.list_support_sessions(
        db=db, tenant_id=tenant_id, limit=limit, offset=offset
    )
    return [PlatformSupportSessionResponse.model_validate(s) for s in sessions]


# =============================================================================
# 7. RETENTION, DEACTIVATION & DELETION GOVERNANCE
# =============================================================================


@router.get(
    "/tenants/{tenant_id}/deletion-preview",
    response_model=TenantDeletionPreviewResponse,
)
async def preview_tenant_deletion(
    tenant_id: UUID,
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TenantDeletionPreviewResponse:
    """Perform pre-flight compliance hold analysis and compute deletion impact."""
    return await TenantGovernanceLifecycleService.evaluate_deletion_eligibility(
        db=db, tenant_id=tenant_id
    )


@router.post(
    "/tenants/{tenant_id}/deletion",
    response_model=TenantDeletionPlanResponse,
)
async def execute_tenant_deletion(
    tenant_id: UUID,
    payload: TenantDeletionExecuteRequest,
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TenantDeletionPlanResponse:
    """Schedule or execute guarded institutional decommissioning."""
    return await TenantGovernanceLifecycleService.execute_decommissioning_plan(
        db=db,
        tenant_id=tenant_id,
        actor_id=_admin.id,
        actor_email=_admin.email,
        confirmation_code=payload.confirmation_code,
        reason=payload.reason,
        force_override_holds=payload.force_override_holds,
    )


# =============================================================================
# 8. PLATFORM OPERATIONS HEALTH & TELEMETRY
# =============================================================================


@router.get(
    "/ops/health",
    response_model=PlatformOperationalHealthResponse,
)
async def get_platform_operations_health(
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> PlatformOperationalHealthResponse:
    """Deep operator health check across database, outbox, workers, and queues."""
    return await PlatformHealthService.get_platform_health_overview(db=db)


@router.get(
    "/ops/performance",
    summary="Platform Performance & Capacity Telemetry",
)
async def get_platform_performance(
    _admin: Annotated[User, Depends(require_platform_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[dict[str, Any]]:
    """Retrieve aggregate performance telemetry, slowest routes, latency percentiles, and database connection pool saturation."""
    from datetime import UTC, datetime

    from app.core.config import settings
    from app.core.database import get_db_pool_status
    from app.core.metrics import metrics

    db_pool = get_db_pool_status()

    data = {
        "timestamp": datetime.now(UTC).isoformat(),
        "metrics": metrics.get_snapshot(),
        "slowest_routes": metrics.get_slowest_routes(limit=10),
        "database_pool": db_pool,
        "capacity_safeguards": {
            "statement_timeout_seconds": settings.DB_STATEMENT_TIMEOUT_SECONDS,
            "max_system_connections": settings.POSTGRES_MAX_SYSTEM_CONNECTIONS,
            "db_pool_size": settings.DB_POOL_SIZE,
            "db_max_overflow": settings.DB_MAX_OVERFLOW,
            "tenant_rate_limit_per_minute": settings.TENANT_RATE_LIMIT_PER_MINUTE,
            "tenant_burst_limit": settings.TENANT_BURST_LIMIT,
            "tenant_concurrent_reports_limit": settings.TENANT_CONCURRENT_REPORTS_LIMIT,
            "default_page_size": settings.DEFAULT_PAGE_SIZE,
            "max_page_size": settings.MAX_PAGE_SIZE,
            "max_export_rows": settings.MAX_EXPORT_ROWS,
            "worker_concurrency": settings.WORKER_CONCURRENCY,
        },
    }
    return ApiResponse(data=data)

