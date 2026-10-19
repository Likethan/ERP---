"""Enterprise Records Lifecycle, Retention, Archival & Legal Hold API Router (Step 41).

Provides secure, tenant-scoped endpoints for:
- Statutory and custom Record Categories
- Institutional Records Registry indexing & state machine transitions
- Versioned Retention Policies and immutable rule sets
- Cryptographic Archival Manifests, checksum verifications, and audited retrieval
- Administrative & Legal Holds with automatic precedence enforcement and release recalculations
- Controlled Disposition requests, two-person approvals, executions, and Certificates
- Operational scheduled sweeps and dashboard metrics
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_current_user, get_tenant_context, require_permission
from app.core.permissions import (
    RECORDS_ARCHIVE_EXECUTE_DOT,
    RECORDS_ARCHIVE_RETRIEVE_DOT,
    RECORDS_CREATE_DOT,
    RECORDS_DISPOSITION_APPROVE_DOT,
    RECORDS_DISPOSITION_EXECUTE_DOT,
    RECORDS_DISPOSITION_REQUEST_DOT,
    RECORDS_HOLD_CREATE_DOT,
    RECORDS_HOLD_MANAGE_DOT,
    RECORDS_HOLD_RELEASE_DOT,
    RECORDS_MANAGE_DOT,
    RECORDS_POLICY_MANAGE_DOT,
    RECORDS_POLICY_PUBLISH_DOT,
    RECORDS_READ_DOT,
)
from app.core.tenant import TenantContext
from app.models.people import User
from app.models.records_lifecycle import ScheduledRunType
from app.schemas.common import ApiResponse
from app.schemas.records_lifecycle import (
    RecordArchivalAccessLogCreate,
    RecordArchivalExecuteRequest,
    RecordArchivalRead,
    RecordCategoryCreate,
    RecordCategoryRead,
    RecordCategoryUpdate,
    RecordDispositionApproveRequest,
    RecordDispositionCertificateRead,
    RecordDispositionPreviewRequest,
    RecordDispositionPreviewResponse,
    RecordDispositionRejectRequest,
    RecordDispositionRequestCreate,
    RecordDispositionRequestRead,
    RecordLegalHoldCreate,
    RecordLegalHoldRead,
    RecordLegalHoldReleaseRequest,
    RecordLifecycleDashboardSummary,
    RecordLifecycleHistoryRead,
    RecordLifecycleTransitionRequest,
    RecordRegistryCreate,
    RecordRegistryRead,
    RetentionEvaluationResponse,
    RetentionPolicyCreate,
    RetentionPolicyPublishRequest,
    RetentionPolicyRead,
    RetentionPolicyUpdate,
    ScheduledLifecycleRunRead,
    ScheduledLifecycleRunTrigger,
)
from app.services.records_lifecycle_service import RecordsLifecycleService

records_lifecycle_router = APIRouter(prefix="/records", tags=["Records Lifecycle & Retention"])


# =============================================================================
# 1. RECORD CATEGORY ENDPOINTS
# =============================================================================


@records_lifecycle_router.get(
    "/categories",
    response_model=ApiResponse[list[RecordCategoryRead]],
    summary="List Institutional Record Categories",
)
async def list_categories(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RECORDS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    is_active: bool | None = Query(None, description="Filter by active status"),
):
    cats = await RecordsLifecycleService.list_categories(db, tenant_ctx.tenant_id, is_active=is_active)
    await db.commit()
    return ApiResponse(data=[RecordCategoryRead.model_validate(c) for c in cats])


@records_lifecycle_router.post(
    "/categories",
    response_model=ApiResponse[RecordCategoryRead],
    status_code=status.HTTP_201_CREATED,
    summary="Create Record Category",
)
async def create_category(
    payload: RecordCategoryCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RECORDS_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    cat = await RecordsLifecycleService.create_category(db, tenant_ctx.tenant_id, payload, actor_id=current_user.id)
    await db.commit()
    return ApiResponse(data=RecordCategoryRead.model_validate(cat))


@records_lifecycle_router.get(
    "/categories/{code_or_id}",
    response_model=ApiResponse[RecordCategoryRead],
    summary="Get Record Category Details",
)
async def get_category(
    code_or_id: str,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RECORDS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    try:
        cat_id = UUID(code_or_id)
        cat = await RecordsLifecycleService.get_category(db, tenant_ctx.tenant_id, cat_id)
    except ValueError:
        cat = await RecordsLifecycleService.get_category(db, tenant_ctx.tenant_id, code_or_id)
    return ApiResponse(data=RecordCategoryRead.model_validate(cat))


@records_lifecycle_router.patch(
    "/categories/{category_id}",
    response_model=ApiResponse[RecordCategoryRead],
    summary="Update Record Category",
)
async def update_category(
    category_id: UUID,
    payload: RecordCategoryUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RECORDS_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    cat = await RecordsLifecycleService.update_category(
        db, tenant_ctx.tenant_id, category_id, payload, actor_id=current_user.id
    )
    await db.commit()
    return ApiResponse(data=RecordCategoryRead.model_validate(cat))


# =============================================================================
# 2. RETENTION POLICY ENDPOINTS
# =============================================================================


@records_lifecycle_router.get(
    "/policies",
    response_model=ApiResponse[list[RetentionPolicyRead]],
    summary="List Retention Schedules",
)
async def list_retention_policies(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RECORDS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    category_code: str | None = Query(None, description="Filter by category code"),
    status: str | None = Query(None, description="Filter by policy status"),
):
    policies = await RecordsLifecycleService.list_retention_policies(
        db, tenant_ctx.tenant_id, category_code=category_code, status=status
    )
    return ApiResponse(data=[RetentionPolicyRead.model_validate(p) for p in policies])


@records_lifecycle_router.post(
    "/policies",
    response_model=ApiResponse[RetentionPolicyRead],
    status_code=status.HTTP_201_CREATED,
    summary="Create Draft Retention Policy",
)
async def create_retention_policy(
    payload: RetentionPolicyCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RECORDS_POLICY_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    policy = await RecordsLifecycleService.create_retention_policy(
        db, tenant_ctx.tenant_id, payload, actor_id=current_user.id
    )
    await db.commit()
    return ApiResponse(data=RetentionPolicyRead.model_validate(policy))


@records_lifecycle_router.get(
    "/policies/{policy_id}",
    response_model=ApiResponse[RetentionPolicyRead],
    summary="Get Retention Policy with Historical Versions",
)
async def get_retention_policy(
    policy_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RECORDS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    policy = await RecordsLifecycleService.get_retention_policy(db, tenant_ctx.tenant_id, policy_id)
    return ApiResponse(data=RetentionPolicyRead.model_validate(policy))


@records_lifecycle_router.post(
    "/policies/{policy_id}/publish",
    response_model=ApiResponse[RetentionPolicyRead],
    summary="Publish and Activate Retention Policy",
)
async def publish_retention_policy(
    policy_id: UUID,
    payload: RetentionPolicyPublishRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RECORDS_POLICY_PUBLISH_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    policy = await RecordsLifecycleService.publish_retention_policy(
        db, tenant_ctx.tenant_id, policy_id, payload, actor_id=current_user.id
    )
    await db.commit()
    return ApiResponse(data=RetentionPolicyRead.model_validate(policy))


@records_lifecycle_router.post(
    "/policies/{policy_id}/versions",
    response_model=ApiResponse[RetentionPolicyRead],
    status_code=status.HTTP_201_CREATED,
    summary="Create New Versioned Retention Policy Rule Set",
)
async def create_policy_version(
    policy_id: UUID,
    payload: RetentionPolicyUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RECORDS_POLICY_PUBLISH_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    change_summary: str = Query("Policy version increment", description="Audit change summary"),
):
    policy = await RecordsLifecycleService.create_policy_version(
        db, tenant_ctx.tenant_id, policy_id, payload, change_summary=change_summary, actor_id=current_user.id
    )
    await db.commit()
    return ApiResponse(data=RetentionPolicyRead.model_validate(policy))


# =============================================================================
# 3. RECORDS REGISTRY & LIFECYCLE STATE ENDPOINTS
# =============================================================================


@records_lifecycle_router.get(
    "/registry",
    response_model=ApiResponse[list[RecordRegistryRead]],
    summary="List Registered Institutional Records",
)
async def list_registry_records(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RECORDS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    category_code: str | None = Query(None, description="Category filter"),
    source_module: str | None = Query(None, description="Module filter"),
    lifecycle_state: str | None = Query(None, description="Lifecycle state filter"),
    is_held: bool | None = Query(None, description="Legal hold filter"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    records = await RecordsLifecycleService.list_records(
        db,
        tenant_ctx.tenant_id,
        category_code=category_code,
        source_module=source_module,
        lifecycle_state=lifecycle_state,
        is_held=is_held,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(data=[RecordRegistryRead.model_validate(r) for r in records])


@records_lifecycle_router.post(
    "/registry",
    response_model=ApiResponse[RecordRegistryRead],
    status_code=status.HTTP_201_CREATED,
    summary="Register Domain Record into Lifecycle Index",
)
async def register_record(
    payload: RecordRegistryCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RECORDS_CREATE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    record = await RecordsLifecycleService.register_record(
        db, tenant_ctx.tenant_id, payload, actor_id=current_user.id
    )
    await db.commit()
    return ApiResponse(data=RecordRegistryRead.model_validate(record))


@records_lifecycle_router.get(
    "/registry/{record_id}",
    response_model=ApiResponse[RecordRegistryRead],
    summary="Get Record Registry Details",
)
async def get_record(
    record_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RECORDS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    record = await RecordsLifecycleService.get_record(db, tenant_ctx.tenant_id, record_id)
    return ApiResponse(data=RecordRegistryRead.model_validate(record))


@records_lifecycle_router.get(
    "/registry/{record_id}/history",
    response_model=ApiResponse[list[RecordLifecycleHistoryRead]],
    summary="Get Record Lifecycle Transition Audit History",
)
async def get_record_history(
    record_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RECORDS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    history = await RecordsLifecycleService.get_record_history(db, tenant_ctx.tenant_id, record_id)
    return ApiResponse(data=[RecordLifecycleHistoryRead.model_validate(h) for h in history])


@records_lifecycle_router.post(
    "/registry/{record_id}/transition",
    response_model=ApiResponse[RecordRegistryRead],
    summary="Execute Controlled Record Lifecycle State Transition",
)
async def transition_record(
    record_id: UUID,
    payload: RecordLifecycleTransitionRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RECORDS_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    record = await RecordsLifecycleService.transition_record_state(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        record_id=record_id,
        payload=payload,
        trigger_action="MANUAL_API_TRANSITION",
        actor_id=current_user.id,
    )
    await db.commit()
    return ApiResponse(data=RecordRegistryRead.model_validate(record))


@records_lifecycle_router.post(
    "/registry/{record_id}/evaluate",
    response_model=ApiResponse[RetentionEvaluationResponse],
    summary="Evaluate Record Retention & Legal Hold Decision",
)
async def evaluate_record(
    record_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RECORDS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    eval_resp = await RecordsLifecycleService.evaluate_record_retention(db, tenant_ctx.tenant_id, record_id)
    return ApiResponse(data=eval_resp)


# =============================================================================
# 4. ARCHIVAL MANAGEMENT ENDPOINTS
# =============================================================================


@records_lifecycle_router.post(
    "/archival/execute",
    response_model=ApiResponse[RecordArchivalRead],
    status_code=status.HTTP_201_CREATED,
    summary="Archive Record to Cold Storage with Cryptographic Checksum",
)
async def execute_archival(
    payload: RecordArchivalExecuteRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RECORDS_ARCHIVE_EXECUTE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    archival = await RecordsLifecycleService.execute_archival(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        payload=payload,
        actor_id=current_user.id,
    )
    await db.commit()
    return ApiResponse(data=RecordArchivalRead.model_validate(archival))


@records_lifecycle_router.post(
    "/archival/manifests/{manifest_id}/retrieve",
    response_model=ApiResponse[RecordArchivalRead],
    summary="Audit and Retrieve Archived Record Manifest",
)
async def retrieve_archived_manifest(
    manifest_id: UUID,
    payload: RecordArchivalAccessLogCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RECORDS_ARCHIVE_RETRIEVE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    request: Request = None,
):
    client_ip = request.client.host if request and request.client else "127.0.0.1"
    manifest = await RecordsLifecycleService.retrieve_archived_record(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        manifest_id=manifest_id,
        access_type=payload.access_type,
        justification=payload.justification,
        actor_id=current_user.id,
        ip_address=client_ip,
    )
    await db.commit()
    return ApiResponse(data=RecordArchivalRead.model_validate(manifest))


@records_lifecycle_router.post(
    "/archival/manifests/{manifest_id}/restore",
    response_model=ApiResponse[RecordRegistryRead],
    summary="Restore Archived Record to Active Lifecycle State",
)
async def restore_archived_record(
    manifest_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RECORDS_ARCHIVE_EXECUTE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    justification: str = Query(..., description="Restoration justification"),
):
    record = await RecordsLifecycleService.restore_archived_record(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        manifest_id=manifest_id,
        justification=justification,
        actor_id=current_user.id,
    )
    await db.commit()
    return ApiResponse(data=RecordRegistryRead.model_validate(record))


# =============================================================================
# 5. LEGAL HOLD ENDPOINTS
# =============================================================================


@records_lifecycle_router.get(
    "/holds",
    response_model=ApiResponse[list[RecordLegalHoldRead]],
    summary="List Legal / Administrative Holds",
)
async def list_legal_holds(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RECORDS_HOLD_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status: str | None = Query(None, description="Filter by hold status"),
):
    holds = await RecordsLifecycleService.list_legal_holds(db, tenant_ctx.tenant_id, status=status)
    return ApiResponse(data=[RecordLegalHoldRead.model_validate(h) for h in holds])


@records_lifecycle_router.post(
    "/holds",
    response_model=ApiResponse[RecordLegalHoldRead],
    status_code=status.HTTP_201_CREATED,
    summary="Create Legal Hold and Enforce Preservation",
)
async def create_legal_hold(
    payload: RecordLegalHoldCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RECORDS_HOLD_CREATE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    hold = await RecordsLifecycleService.create_legal_hold(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        payload=payload,
        actor_id=current_user.id,
    )
    await db.commit()
    return ApiResponse(data=RecordLegalHoldRead.model_validate(hold))


@records_lifecycle_router.post(
    "/holds/{hold_id}/release",
    response_model=ApiResponse[RecordLegalHoldRead],
    summary="Release Legal Hold and Recalculate Retention Eligibility",
)
async def release_legal_hold(
    hold_id: UUID,
    payload: RecordLegalHoldReleaseRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RECORDS_HOLD_RELEASE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    hold = await RecordsLifecycleService.release_legal_hold(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        hold_id=hold_id,
        payload=payload,
        actor_id=current_user.id,
    )
    await db.commit()
    return ApiResponse(data=RecordLegalHoldRead.model_validate(hold))


# =============================================================================
# 6. DISPOSITION WORKFLOW & CERTIFICATES ENDPOINTS
# =============================================================================


@records_lifecycle_router.post(
    "/disposition/preview",
    response_model=ApiResponse[RecordDispositionPreviewResponse],
    summary="Dry-Run Preview of Records Qualifying for Disposition",
)
async def preview_disposition(
    payload: RecordDispositionPreviewRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RECORDS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    preview_resp = await RecordsLifecycleService.preview_disposition(db, tenant_ctx.tenant_id, payload)
    return ApiResponse(data=preview_resp)


@records_lifecycle_router.post(
    "/disposition/requests",
    response_model=ApiResponse[RecordDispositionRequestRead],
    status_code=status.HTTP_201_CREATED,
    summary="Submit Disposition Request for Administrative Review",
)
async def create_disposition_request(
    payload: RecordDispositionRequestCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RECORDS_DISPOSITION_REQUEST_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    disp_req = await RecordsLifecycleService.create_disposition_request(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        payload=payload,
        actor_id=current_user.id,
    )
    await db.commit()
    return ApiResponse(data=RecordDispositionRequestRead.model_validate(disp_req))


@records_lifecycle_router.post(
    "/disposition/requests/{request_id}/approve",
    response_model=ApiResponse[RecordDispositionRequestRead],
    summary="Formally Approve Disposition Request (Enforces Separation of Duties)",
)
async def approve_disposition_request(
    request_id: UUID,
    payload: RecordDispositionApproveRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RECORDS_DISPOSITION_APPROVE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    disp_req = await RecordsLifecycleService.approve_disposition_request(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        request_id=request_id,
        payload=payload,
        actor_id=current_user.id,
    )
    await db.commit()
    return ApiResponse(data=RecordDispositionRequestRead.model_validate(disp_req))


@records_lifecycle_router.post(
    "/disposition/requests/{request_id}/reject",
    response_model=ApiResponse[RecordDispositionRequestRead],
    summary="Reject Disposition Request",
)
async def reject_disposition_request(
    request_id: UUID,
    payload: RecordDispositionRejectRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RECORDS_DISPOSITION_APPROVE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    disp_req = await RecordsLifecycleService.reject_disposition_request(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        request_id=request_id,
        payload=payload,
        actor_id=current_user.id,
    )
    await db.commit()
    return ApiResponse(data=RecordDispositionRequestRead.model_validate(disp_req))


@records_lifecycle_router.post(
    "/disposition/requests/{request_id}/execute",
    response_model=ApiResponse[RecordDispositionCertificateRead],
    summary="Execute Approved Disposition and Issue Tamper-Evident Certificate",
)
async def execute_disposition(
    request_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RECORDS_DISPOSITION_EXECUTE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    cert = await RecordsLifecycleService.execute_disposition(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        request_id=request_id,
        actor_id=current_user.id,
    )
    await db.commit()
    return ApiResponse(data=RecordDispositionCertificateRead.model_validate(cert))


@records_lifecycle_router.get(
    "/disposition/certificates/{cert_id}",
    response_model=ApiResponse[RecordDispositionCertificateRead],
    summary="Get Disposition Certificate",
)
async def get_disposition_certificate(
    cert_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RECORDS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    cert = await RecordsLifecycleService.get_disposition_certificate(db, tenant_ctx.tenant_id, cert_id)
    return ApiResponse(data=RecordDispositionCertificateRead.model_validate(cert))


# =============================================================================
# 7. SCHEDULED SWEEPS & DASHBOARD ENDPOINTS
# =============================================================================


@records_lifecycle_router.post(
    "/scheduled/run",
    response_model=ApiResponse[ScheduledLifecycleRunRead],
    summary="Trigger Bounded Scheduled Lifecycle Processing Sweep",
)
async def trigger_scheduled_sweep(
    payload: ScheduledLifecycleRunTrigger,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RECORDS_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    run = await RecordsLifecycleService.run_scheduled_lifecycle_sweep(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        job_type=payload.job_type,
        batch_size=payload.batch_size,
    )
    await db.commit()
    return ApiResponse(data=ScheduledLifecycleRunRead.model_validate(run))


@records_lifecycle_router.get(
    "/dashboard/summary",
    response_model=ApiResponse[RecordLifecycleDashboardSummary],
    summary="Get Records Lifecycle Dashboard Summary Indicators",
)
async def get_dashboard_summary(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RECORDS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    summary = await RecordsLifecycleService.get_dashboard_summary(db, tenant_ctx.tenant_id)
    return ApiResponse(data=summary)
