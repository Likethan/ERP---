"""Enterprise Data Governance, Privacy & Compliance Router for CampusOS.

Provides secure, tenant-scoped endpoints for:
- Data classification & sensitive field inspection
- Governance policy lifecycle & versioning
- Retention policy management & evaluation
- Legal / administrative holds
- Privacy / Subject Access Requests, export downloads, and corrections
- Privileged access review campaigns and decisions
- Governance summary indicators
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_tenant_context, require_permission
from app.core.governance_registry import (
    SENSITIVE_FIELD_REGISTRY,
    DataClassificationLevel,
)
from app.core.permissions import (
    GOVERNANCE_ACCESS_REVIEWS_MANAGE_DOT,
    GOVERNANCE_ACCESS_REVIEWS_READ_DOT,
    GOVERNANCE_CLASSIFICATION_READ_DOT,
    GOVERNANCE_HOLDS_MANAGE_DOT,
    GOVERNANCE_HOLDS_READ_DOT,
    GOVERNANCE_POLICIES_MANAGE_DOT,
    GOVERNANCE_POLICIES_READ_DOT,
    GOVERNANCE_PRIVACY_CREATE_DOT,
    GOVERNANCE_PRIVACY_EXECUTE_DOT,
    GOVERNANCE_PRIVACY_READ_DOT,
    GOVERNANCE_PRIVACY_REVIEW_DOT,
    GOVERNANCE_READ_DOT,
    GOVERNANCE_RETENTION_EXECUTE_DOT,
    GOVERNANCE_RETENTION_MANAGE_DOT,
    GOVERNANCE_RETENTION_READ_DOT,
)
from app.core.tenant import TenantContext
from app.models.people import User
from app.schemas.common import ApiResponse
from app.schemas.governance import (
    AccessReviewCreate,
    AccessReviewItemDecide,
    AccessReviewItemRead,
    AccessReviewRead,
    ClassificationTierRead,
    GovernanceHoldCreate,
    GovernanceHoldRead,
    GovernanceHoldRelease,
    GovernancePolicyCreate,
    GovernancePolicyRead,
    GovernancePolicyUpdate,
    GovernancePolicyVersionCreate,
    GovernancePolicyVersionRead,
    GovernanceSummaryRead,
    PrivacyRequestCreate,
    PrivacyRequestRead,
    PrivacyRequestReview,
    RetentionDecisionRead,
    RetentionEvaluationRequest,
    RetentionPolicyCreate,
    RetentionPolicyRead,
    RetentionPolicyUpdate,
    SensitiveFieldRead,
)
from app.services.governance_service import GovernanceService
from app.services.privacy_service import PrivacyService
from app.services.retention_service import RetentionService

governance_router = APIRouter(prefix="/governance", tags=["Data Governance & Privacy"])


# =============================================================================
# 1. DATA CLASSIFICATION & SENSITIVE FIELDS
# =============================================================================

@governance_router.get(
    "/classifications",
    response_model=ApiResponse[list[ClassificationTierRead]],
    summary="List Institutional Data Classification Tiers",
)
async def list_classification_tiers(
    current_user: Annotated[User, Depends(require_permission(GOVERNANCE_CLASSIFICATION_READ_DOT))],
):
    tiers = [
        ClassificationTierRead(
            level=DataClassificationLevel.PUBLIC,
            description="Freely accessible public institutional information, course catalog, campus maps.",
            example_entities=["Subject", "Department", "CampusEvent"],
        ),
        ClassificationTierRead(
            level=DataClassificationLevel.INTERNAL,
            description="General institutional operational records restricted to campus members.",
            example_entities=["Section", "Timetable", "Classroom"],
        ),
        ClassificationTierRead(
            level=DataClassificationLevel.CONFIDENTIAL,
            description="Personal data and private records requiring explicit authorization to access.",
            example_entities=["User.email", "User.phone_number", "AttendanceRecord"],
        ),
        ClassificationTierRead(
            level=DataClassificationLevel.RESTRICTED,
            description="Highly regulated personal, financial, and disciplinary records.",
            example_entities=["Invoice", "PaymentTransaction", "StudentProfile.identification_number"],
        ),
        ClassificationTierRead(
            level=DataClassificationLevel.SENSITIVE,
            description="Critical authentication secrets, credentials, and cryptographic tokens.",
            example_entities=["User.password_hash", "PasswordResetToken", "SessionToken"],
        ),
    ]
    return ApiResponse(data=tiers)


@governance_router.get(
    "/sensitive-fields",
    response_model=ApiResponse[list[SensitiveFieldRead]],
    summary="List Registered Sensitive Fields and Masking Policies",
)
async def list_sensitive_fields(
    current_user: Annotated[User, Depends(require_permission(GOVERNANCE_CLASSIFICATION_READ_DOT))],
):
    items = [
        SensitiveFieldRead(
            entity=def_.entity,
            field=def_.field,
            classification=def_.classification,
            masking_strategy=def_.masking_strategy,
            export_policy=def_.export_policy,
            logging_policy=def_.logging_policy,
            ai_visibility=def_.ai_visibility,
            allowed_roles=def_.allowed_roles,
        )
        for def_ in SENSITIVE_FIELD_REGISTRY.values()
    ]
    return ApiResponse(data=items)


# =============================================================================
# 2. GOVERNANCE POLICIES & VERSIONS
# =============================================================================

@governance_router.get(
    "/policies",
    response_model=ApiResponse[list[GovernancePolicyRead]],
    summary="List Governance Policies",
)
async def list_policies(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(GOVERNANCE_POLICIES_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    category: str | None = Query(None, description="Filter by category"),
    status: str | None = Query(None, description="Filter by status"),
):
    policies = await GovernanceService.list_policies(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        category=category,
        status=status,
    )
    return ApiResponse(data=[GovernancePolicyRead.model_validate(p) for p in policies])


@governance_router.post(
    "/policies",
    response_model=ApiResponse[GovernancePolicyRead],
    status_code=status.HTTP_201_CREATED,
    summary="Create Governance Policy",
)
async def create_policy(
    payload: GovernancePolicyCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(GOVERNANCE_POLICIES_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    policy = await GovernanceService.create_policy(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        payload=payload,
        actor_id=current_user.id,
    )
    return ApiResponse(data=GovernancePolicyRead.model_validate(policy))


@governance_router.get(
    "/policies/{policy_id}",
    response_model=ApiResponse[GovernancePolicyRead],
    summary="Get Governance Policy with Versions",
)
async def get_policy(
    policy_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(GOVERNANCE_POLICIES_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    policy = await GovernanceService.get_policy(db, tenant_ctx.tenant_id, policy_id)
    return ApiResponse(data=GovernancePolicyRead.model_validate(policy))


@governance_router.patch(
    "/policies/{policy_id}",
    response_model=ApiResponse[GovernancePolicyRead],
    summary="Update Governance Policy Metadata",
)
async def update_policy(
    policy_id: UUID,
    payload: GovernancePolicyUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(GOVERNANCE_POLICIES_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    policy = await GovernanceService.update_policy(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        policy_id=policy_id,
        payload=payload,
        actor_id=current_user.id,
    )
    return ApiResponse(data=GovernancePolicyRead.model_validate(policy))


@governance_router.post(
    "/policies/{policy_id}/versions",
    response_model=ApiResponse[GovernancePolicyVersionRead],
    status_code=status.HTTP_201_CREATED,
    summary="Create New Immutable Policy Version",
)
async def create_policy_version(
    policy_id: UUID,
    payload: GovernancePolicyVersionCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(GOVERNANCE_POLICIES_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    version = await GovernanceService.create_policy_version(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        policy_id=policy_id,
        payload=payload,
        actor_id=current_user.id,
    )
    return ApiResponse(data=GovernancePolicyVersionRead.model_validate(version))


# =============================================================================
# 3. RETENTION POLICIES & EVALUATION
# =============================================================================

@governance_router.get(
    "/retention/policies",
    response_model=ApiResponse[list[RetentionPolicyRead]],
    summary="List Retention Schedules",
)
async def list_retention_policies(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(GOVERNANCE_RETENTION_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    rules = await RetentionService.list_retention_policies(db, tenant_ctx.tenant_id)
    return ApiResponse(data=[RetentionPolicyRead.model_validate(r) for r in rules])


@governance_router.post(
    "/retention/policies",
    response_model=ApiResponse[RetentionPolicyRead],
    status_code=status.HTTP_201_CREATED,
    summary="Create Retention Schedule",
)
async def create_retention_policy(
    payload: RetentionPolicyCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(GOVERNANCE_RETENTION_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    rule = await RetentionService.create_retention_policy(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        payload=payload,
        actor_id=current_user.id,
    )
    return ApiResponse(data=RetentionPolicyRead.model_validate(rule))


@governance_router.get(
    "/retention/policies/{policy_id}",
    response_model=ApiResponse[RetentionPolicyRead],
    summary="Get Retention Schedule",
)
async def get_retention_policy(
    policy_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(GOVERNANCE_RETENTION_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    rule = await RetentionService.get_retention_policy(db, tenant_ctx.tenant_id, policy_id)
    return ApiResponse(data=RetentionPolicyRead.model_validate(rule))


@governance_router.patch(
    "/retention/policies/{policy_id}",
    response_model=ApiResponse[RetentionPolicyRead],
    summary="Update Retention Schedule",
)
async def update_retention_policy(
    policy_id: UUID,
    payload: RetentionPolicyUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(GOVERNANCE_RETENTION_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    rule = await RetentionService.update_retention_policy(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        policy_id=policy_id,
        payload=payload,
        actor_id=current_user.id,
    )
    return ApiResponse(data=RetentionPolicyRead.model_validate(rule))


@governance_router.post(
    "/retention/evaluate",
    response_model=ApiResponse[RetentionDecisionRead],
    summary="Ad-Hoc Retention & Legal Hold Evaluation",
)
async def evaluate_retention(
    payload: RetentionEvaluationRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(GOVERNANCE_RETENTION_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    decision = await RetentionService.evaluate_retention(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        resource_type=payload.resource_type,
        resource_id=payload.resource_id,
        record_created_at=payload.record_created_at,
        metadata=payload.metadata,
    )
    return ApiResponse(data=decision)


@governance_router.post(
    "/retention/execute",
    response_model=ApiResponse[dict],
    summary="Controlled Execution of Retention Action",
)
async def execute_retention_action(
    resource_type: str = Query(..., description="Resource type e.g. students, documents"),
    resource_id: UUID = Query(..., description="Target record UUID"),
    action: str = Query("ARCHIVE", description="Action: ARCHIVE, ANONYMIZE, DELETE"),
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)] = None,
    current_user: Annotated[User, Depends(require_permission(GOVERNANCE_RETENTION_EXECUTE_DOT))] = None,
    db: Annotated[AsyncSession, Depends(get_db_session)] = None,
):
    res = await RetentionService.execute_retention_action(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
        actor_id=current_user.id,
    )
    return ApiResponse(data=res)


# =============================================================================
# 4. LEGAL / GOVERNANCE HOLDS
# =============================================================================

@governance_router.get(
    "/holds",
    response_model=ApiResponse[list[GovernanceHoldRead]],
    summary="List Legal / Governance Holds",
)
async def list_holds(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(GOVERNANCE_HOLDS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status: str | None = Query(None, description="Filter by status: ACTIVE, RELEASED, EXPIRED"),
    entity_type: str | None = Query(None, description="Filter by target entity type"),
):
    holds = await GovernanceService.list_holds(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        status=status,
        entity_type=entity_type,
    )
    return ApiResponse(data=[GovernanceHoldRead.model_validate(h) for h in holds])


@governance_router.post(
    "/holds",
    response_model=ApiResponse[GovernanceHoldRead],
    status_code=status.HTTP_201_CREATED,
    summary="Place Legal / Governance Hold",
)
async def create_hold(
    payload: GovernanceHoldCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(GOVERNANCE_HOLDS_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    hold = await GovernanceService.create_hold(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        payload=payload,
        actor_id=current_user.id,
    )
    return ApiResponse(data=GovernanceHoldRead.model_validate(hold))


@governance_router.post(
    "/holds/{hold_id}/release",
    response_model=ApiResponse[GovernanceHoldRead],
    summary="Release Legal / Governance Hold",
)
async def release_hold(
    hold_id: UUID,
    payload: GovernanceHoldRelease,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(GOVERNANCE_HOLDS_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    hold = await GovernanceService.release_hold(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        hold_id=hold_id,
        payload=payload,
        actor_id=current_user.id,
    )
    return ApiResponse(data=GovernanceHoldRead.model_validate(hold))


# =============================================================================
# 5. PRIVACY / DATA SUBJECT REQUESTS
# =============================================================================

@governance_router.get(
    "/privacy/requests",
    response_model=ApiResponse[list[PrivacyRequestRead]],
    summary="List Privacy / Subject Access Requests",
)
async def list_privacy_requests(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(GOVERNANCE_PRIVACY_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status: str | None = Query(None, description="Filter by status"),
    request_type: str | None = Query(None, description="Filter by type: ACCESS, EXPORT, CORRECTION, DELETION"),
):
    requests = await PrivacyService.list_requests(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        status=status,
        request_type=request_type,
    )
    return ApiResponse(data=[PrivacyRequestRead.model_validate(r) for r in requests])


@governance_router.post(
    "/privacy/requests",
    response_model=ApiResponse[PrivacyRequestRead],
    status_code=status.HTTP_201_CREATED,
    summary="Submit Privacy / Subject Request",
)
async def submit_privacy_request(
    payload: PrivacyRequestCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(GOVERNANCE_PRIVACY_CREATE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    req = await PrivacyService.submit_request(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        payload=payload,
        actor_id=current_user.id,
    )
    return ApiResponse(data=PrivacyRequestRead.model_validate(req))


@governance_router.get(
    "/privacy/requests/{request_id}",
    response_model=ApiResponse[PrivacyRequestRead],
    summary="Get Privacy Request Details and Actions",
)
async def get_privacy_request(
    request_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(GOVERNANCE_PRIVACY_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    req = await PrivacyService.get_request(db, tenant_ctx.tenant_id, request_id)
    return ApiResponse(data=PrivacyRequestRead.model_validate(req))


@governance_router.post(
    "/privacy/requests/{request_id}/approve",
    response_model=ApiResponse[PrivacyRequestRead],
    summary="Approve Privacy Request",
)
async def approve_privacy_request(
    request_id: UUID,
    payload: PrivacyRequestReview,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(GOVERNANCE_PRIVACY_REVIEW_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    payload.status = "APPROVED"
    req = await PrivacyService.review_request(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        request_id=request_id,
        payload=payload,
        reviewer_id=current_user.id,
    )
    return ApiResponse(data=PrivacyRequestRead.model_validate(req))


@governance_router.post(
    "/privacy/requests/{request_id}/reject",
    response_model=ApiResponse[PrivacyRequestRead],
    summary="Reject Privacy Request",
)
async def reject_privacy_request(
    request_id: UUID,
    payload: PrivacyRequestReview,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(GOVERNANCE_PRIVACY_REVIEW_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    payload.status = "REJECTED"
    req = await PrivacyService.review_request(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        request_id=request_id,
        payload=payload,
        reviewer_id=current_user.id,
    )
    return ApiResponse(data=PrivacyRequestRead.model_validate(req))


@governance_router.post(
    "/privacy/requests/{request_id}/execute",
    response_model=ApiResponse[PrivacyRequestRead],
    summary="Execute Approved Privacy Request",
)
async def execute_privacy_request(
    request_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(GOVERNANCE_PRIVACY_EXECUTE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    req = await PrivacyService.execute_request(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        request_id=request_id,
        actor_id=current_user.id,
    )
    return ApiResponse(data=PrivacyRequestRead.model_validate(req))


@governance_router.get(
    "/privacy/requests/{request_id}/download",
    summary="Download Privacy Export Artifact",
)
async def download_privacy_export(
    request_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(GOVERNANCE_PRIVACY_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    content, filename = await PrivacyService.get_privacy_export_file(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        request_id=request_id,
        actor_id=current_user.id,
    )
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# =============================================================================
# 6. ACCESS REVIEWS
# =============================================================================

@governance_router.get(
    "/access-reviews",
    response_model=ApiResponse[list[AccessReviewRead]],
    summary="List Access Review Campaigns",
)
async def list_access_reviews(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(GOVERNANCE_ACCESS_REVIEWS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status: str | None = Query(None, description="Filter by status"),
):
    reviews = await GovernanceService.list_access_reviews(db, tenant_ctx.tenant_id, status=status)
    return ApiResponse(data=[AccessReviewRead.model_validate(r) for r in reviews])


@governance_router.post(
    "/access-reviews",
    response_model=ApiResponse[AccessReviewRead],
    status_code=status.HTTP_201_CREATED,
    summary="Create Access Review Campaign",
)
async def create_access_review(
    payload: AccessReviewCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(GOVERNANCE_ACCESS_REVIEWS_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    review = await GovernanceService.create_access_review(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        payload=payload,
        actor_id=current_user.id,
    )
    return ApiResponse(data=AccessReviewRead.model_validate(review))


@governance_router.get(
    "/access-reviews/{review_id}",
    response_model=ApiResponse[AccessReviewRead],
    summary="Get Access Review with Evaluation Items",
)
async def get_access_review(
    review_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(GOVERNANCE_ACCESS_REVIEWS_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    review = await GovernanceService.get_access_review(db, tenant_ctx.tenant_id, review_id)
    return ApiResponse(data=AccessReviewRead.model_validate(review))


@governance_router.post(
    "/access-reviews/{review_id}/items/{item_id}/decide",
    response_model=ApiResponse[AccessReviewItemRead],
    summary="Record Decision on Access Review Item",
)
async def decide_access_review_item(
    review_id: UUID,
    item_id: UUID,
    payload: AccessReviewItemDecide,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(GOVERNANCE_ACCESS_REVIEWS_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    item = await GovernanceService.decide_access_review_item(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        review_id=review_id,
        item_id=item_id,
        payload=payload,
        actor_id=current_user.id,
    )
    return ApiResponse(data=AccessReviewItemRead.model_validate(item))


@governance_router.post(
    "/access-reviews/{review_id}/complete",
    response_model=ApiResponse[AccessReviewRead],
    summary="Complete Access Review Campaign",
)
async def complete_access_review(
    review_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(GOVERNANCE_ACCESS_REVIEWS_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    review = await GovernanceService.complete_access_review(
        db=db,
        tenant_id=tenant_ctx.tenant_id,
        review_id=review_id,
        actor_id=current_user.id,
    )
    return ApiResponse(data=AccessReviewRead.model_validate(review))


# =============================================================================
# 7. GOVERNANCE SUMMARY & HEALTH
# =============================================================================

@governance_router.get(
    "/summary",
    response_model=ApiResponse[GovernanceSummaryRead],
    summary="Institutional Governance Summary & Telemetry",
)
async def get_governance_summary(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(GOVERNANCE_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    summary = await GovernanceService.get_governance_summary(db, tenant_ctx.tenant_id)
    return ApiResponse(data=summary)


@governance_router.get(
    "/health",
    response_model=ApiResponse[dict],
    summary="Governance Engine Health & Readiness",
)
async def governance_health(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(GOVERNANCE_READ_DOT))],
):
    return ApiResponse(
        data={
            "status": "healthy",
            "module": "Enterprise Data Governance & Privacy",
            "classification_registry_entries": len(SENSITIVE_FIELD_REGISTRY),
            "tenant_id": str(tenant_ctx.tenant_id),
        }
    )
