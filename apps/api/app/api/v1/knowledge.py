"""Enterprise Institutional Knowledge Base, Policy Library & Controlled Knowledge API Router (Step 42)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_current_user, get_tenant_context, require_permission
from app.core.permissions import (
    KNOWLEDGE_ACKNOWLEDGE_DOT,
    KNOWLEDGE_APPROVE_DOT,
    KNOWLEDGE_ATTESTATION_READ_DOT,
    KNOWLEDGE_CREATE_DOT,
    KNOWLEDGE_MANAGE_DOT,
    KNOWLEDGE_PUBLISH_DOT,
    KNOWLEDGE_READ_DOT,
    KNOWLEDGE_RETIRE_DOT,
    KNOWLEDGE_REVIEW_DOT,
)
from app.core.tenant import TenantContext
from app.models.people import User
from app.schemas.common import ApiResponse
from app.schemas.knowledge import (
    KnowledgeAcknowledgementRequirementCreate,
    KnowledgeAcknowledgementRequirementResponse,
    KnowledgeAttestationComplianceReport,
    KnowledgeCategoryCreate,
    KnowledgeCategoryResponse,
    KnowledgeCategoryUpdate,
    KnowledgeDraftValidationResult,
    KnowledgeGovernanceSummary,
    KnowledgeItemCreate,
    KnowledgeItemDraftUpdate,
    KnowledgeItemMetadataUpdate,
    KnowledgeItemResponse,
    KnowledgeItemVersionDetail,
    KnowledgePublishRequest,
    KnowledgeRelationshipCreate,
    KnowledgeRelationshipResponse,
    KnowledgeRetireRequest,
    KnowledgeReviewActionRequest,
    KnowledgeReviewSubmitRequest,
    KnowledgeSchedulePublicationRequest,
    KnowledgeSearchFilter,
    KnowledgeSearchResponse,
    KnowledgeUserAcknowledgementCreate,
    KnowledgeUserAcknowledgementResponse,
)
from app.services.knowledge_service import KnowledgeService

knowledge_router = APIRouter(prefix="/knowledge", tags=["Institutional Knowledge & Policies"])
service = KnowledgeService()


# =============================================================================
# 1. KNOWLEDGE CATEGORIES
# =============================================================================


@knowledge_router.get(
    "/categories",
    response_model=ApiResponse[list[KnowledgeCategoryResponse]],
    summary="List Institutional Knowledge Categories",
)
async def list_categories(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(KNOWLEDGE_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    cats = await service.list_categories(db, tenant_ctx.tenant_id)
    await db.commit()
    return ApiResponse(data=[KnowledgeCategoryResponse.model_validate(c) for c in cats])


@knowledge_router.post(
    "/categories",
    response_model=ApiResponse[KnowledgeCategoryResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Institutional Knowledge Category",
)
async def create_category(
    payload: KnowledgeCategoryCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(KNOWLEDGE_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    cat = await service.create_category(db, tenant_ctx.tenant_id, payload)
    await db.commit()
    return ApiResponse(data=KnowledgeCategoryResponse.model_validate(cat))


@knowledge_router.patch(
    "/categories/{category_id}",
    response_model=ApiResponse[KnowledgeCategoryResponse],
    summary="Update Knowledge Category",
)
async def update_category(
    category_id: UUID,
    payload: KnowledgeCategoryUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(KNOWLEDGE_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    cat = await service.update_category(db, tenant_ctx.tenant_id, category_id, payload)
    await db.commit()
    return ApiResponse(data=KnowledgeCategoryResponse.model_validate(cat))


# =============================================================================
# 2. KNOWLEDGE ITEMS & SEARCH
# =============================================================================


@knowledge_router.get(
    "/items",
    response_model=ApiResponse[KnowledgeSearchResponse],
    summary="Search & Filter Knowledge Items and Policies",
)
async def search_items(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(KNOWLEDGE_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    q: str | None = Query(None, description="Search term across title, summary, content"),
    categories: list[str] | None = Query(None, description="Filter category codes"),
    scopes: list[str] | None = Query(None, description="Filter scope types"),
    statuses: list[str] | None = Query(None, description="Filter item statuses"),
    campus_id: UUID | None = Query(None, description="Campus filter"),
    department_id: UUID | None = Query(None, description="Department filter"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    filters = KnowledgeSearchFilter(
        query=q,
        category_codes=categories,
        scope_types=scopes,
        statuses=statuses,
        campus_id=campus_id,
        department_id=department_id,
        page=page,
        page_size=page_size,
    )
    items, total = await service.search_knowledge(db, tenant_ctx.tenant_id, filters, actor=current_user)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return ApiResponse(
        data=KnowledgeSearchResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


@knowledge_router.post(
    "/items",
    response_model=ApiResponse[KnowledgeItemResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Draft Knowledge Item",
)
async def create_item(
    payload: KnowledgeItemCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(KNOWLEDGE_CREATE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    item = await service.create_item(db, tenant_ctx.tenant_id, actor=current_user, payload=payload)
    await db.commit()
    # Reload with relationships
    loaded = await service.get_item(db, tenant_ctx.tenant_id, item.id, actor=current_user)
    return ApiResponse(data=KnowledgeItemResponse.model_validate(loaded))


@knowledge_router.get(
    "/items/{item_id}",
    response_model=ApiResponse[KnowledgeItemResponse],
    summary="Get Knowledge Item Details",
)
async def get_item(
    item_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(KNOWLEDGE_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    item = await service.get_item(db, tenant_ctx.tenant_id, item_id, actor=current_user)
    return ApiResponse(data=KnowledgeItemResponse.model_validate(item))


@knowledge_router.put(
    "/items/{item_id}/draft",
    response_model=ApiResponse[KnowledgeItemResponse],
    summary="Save Working Draft with Optimistic Concurrency Control",
)
async def update_draft(
    item_id: UUID,
    payload: KnowledgeItemDraftUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(KNOWLEDGE_CREATE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    item = await service.update_draft(db, tenant_ctx.tenant_id, item_id, actor=current_user, payload=payload)
    await db.commit()
    loaded = await service.get_item(db, tenant_ctx.tenant_id, item.id, actor=current_user)
    return ApiResponse(data=KnowledgeItemResponse.model_validate(loaded))


@knowledge_router.post(
    "/items/{item_id}/validate",
    response_model=ApiResponse[KnowledgeDraftValidationResult],
    summary="Validate Working Draft Content and Preview",
)
async def validate_draft(
    item_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(KNOWLEDGE_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    result = await service.validate_draft(db, tenant_ctx.tenant_id, item_id, actor=current_user)
    return ApiResponse(data=result)


@knowledge_router.patch(
    "/items/{item_id}/metadata",
    response_model=ApiResponse[KnowledgeItemResponse],
    summary="Update Knowledge Item Metadata & Scopes",
)
async def update_metadata(
    item_id: UUID,
    payload: KnowledgeItemMetadataUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(KNOWLEDGE_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    item = await service.update_metadata(db, tenant_ctx.tenant_id, item_id, actor=current_user, payload=payload)
    await db.commit()
    loaded = await service.get_item(db, tenant_ctx.tenant_id, item.id, actor=current_user)
    return ApiResponse(data=KnowledgeItemResponse.model_validate(loaded))


# =============================================================================
# 3. REVIEW & APPROVAL WORKFLOW
# =============================================================================


@knowledge_router.post(
    "/items/{item_id}/submit-review",
    response_model=ApiResponse[KnowledgeItemResponse],
    summary="Submit Draft for Editorial Review",
)
async def submit_for_review(
    item_id: UUID,
    payload: KnowledgeReviewSubmitRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(KNOWLEDGE_CREATE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    item = await service.submit_for_review(db, tenant_ctx.tenant_id, item_id, actor=current_user, payload=payload)
    await db.commit()
    loaded = await service.get_item(db, tenant_ctx.tenant_id, item.id, actor=current_user)
    return ApiResponse(data=KnowledgeItemResponse.model_validate(loaded))


@knowledge_router.post(
    "/items/{item_id}/review",
    response_model=ApiResponse[KnowledgeItemResponse],
    summary="Record Editorial Review Decision (Separation of Duties Enforced)",
)
async def review_action(
    item_id: UUID,
    payload: KnowledgeReviewActionRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(KNOWLEDGE_REVIEW_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    item = await service.review_action(db, tenant_ctx.tenant_id, item_id, actor=current_user, payload=payload)
    await db.commit()
    loaded = await service.get_item(db, tenant_ctx.tenant_id, item.id, actor=current_user)
    return ApiResponse(data=KnowledgeItemResponse.model_validate(loaded))


# =============================================================================
# 4. PUBLICATION, SCHEDULING & RETIREMENT
# =============================================================================


@knowledge_router.post(
    "/items/{item_id}/publish",
    response_model=ApiResponse[KnowledgeItemVersionDetail],
    summary="Publish Approved Knowledge Item (Generates Immutable Version)",
)
async def publish_item(
    item_id: UUID,
    payload: KnowledgePublishRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(KNOWLEDGE_PUBLISH_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    ver = await service.publish_item(db, tenant_ctx.tenant_id, item_id, actor=current_user, payload=payload)
    await db.commit()
    return ApiResponse(data=KnowledgeItemVersionDetail.model_validate(ver))


@knowledge_router.post(
    "/items/{item_id}/schedule",
    response_model=ApiResponse[KnowledgeItemResponse],
    summary="Schedule Future Publication of Approved Item",
)
async def schedule_publication(
    item_id: UUID,
    payload: KnowledgeSchedulePublicationRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(KNOWLEDGE_PUBLISH_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    item = await service.schedule_publication(db, tenant_ctx.tenant_id, item_id, actor=current_user, payload=payload)
    await db.commit()
    loaded = await service.get_item(db, tenant_ctx.tenant_id, item.id, actor=current_user)
    return ApiResponse(data=KnowledgeItemResponse.model_validate(loaded))


@knowledge_router.post(
    "/items/{item_id}/cancel-schedule",
    response_model=ApiResponse[KnowledgeItemResponse],
    summary="Cancel Scheduled Publication",
)
async def cancel_scheduled_publication(
    item_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(KNOWLEDGE_PUBLISH_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    item = await service.cancel_scheduled_publication(db, tenant_ctx.tenant_id, item_id, actor=current_user)
    await db.commit()
    loaded = await service.get_item(db, tenant_ctx.tenant_id, item.id, actor=current_user)
    return ApiResponse(data=KnowledgeItemResponse.model_validate(loaded))


@knowledge_router.post(
    "/items/{item_id}/retire",
    response_model=ApiResponse[KnowledgeItemResponse],
    summary="Retire Knowledge Item or Policy",
)
async def retire_item(
    item_id: UUID,
    payload: KnowledgeRetireRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(KNOWLEDGE_RETIRE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    item = await service.retire_item(db, tenant_ctx.tenant_id, item_id, actor=current_user, payload=payload)
    await db.commit()
    loaded = await service.get_item(db, tenant_ctx.tenant_id, item.id, actor=current_user)
    return ApiResponse(data=KnowledgeItemResponse.model_validate(loaded))


# =============================================================================
# 5. VERSIONS & IMMUTABLE HISTORY
# =============================================================================


@knowledge_router.get(
    "/items/{item_id}/versions",
    response_model=ApiResponse[list[KnowledgeItemVersionDetail]],
    summary="List Immutable Historical Versions of Knowledge Item",
)
async def list_versions(
    item_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(KNOWLEDGE_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    versions = await service.get_version_history(db, tenant_ctx.tenant_id, item_id, actor=current_user)
    return ApiResponse(data=[KnowledgeItemVersionDetail.model_validate(v) for v in versions])


@knowledge_router.get(
    "/items/{item_id}/versions/{version_number}",
    response_model=ApiResponse[KnowledgeItemVersionDetail],
    summary="Retrieve Exact Immutable Version Snapshot",
)
async def get_version(
    item_id: UUID,
    version_number: int,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(KNOWLEDGE_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    ver = await service.get_version(db, tenant_ctx.tenant_id, item_id, version_number, actor=current_user)
    return ApiResponse(data=KnowledgeItemVersionDetail.model_validate(ver))


# =============================================================================
# 6. RELATIONSHIPS & EXPLORER
# =============================================================================


@knowledge_router.get(
    "/items/{item_id}/relationships",
    response_model=ApiResponse[list[KnowledgeRelationshipResponse]],
    summary="List Explicit Knowledge Relationships",
)
async def list_relationships(
    item_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(KNOWLEDGE_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    rels = await service.list_relationships(db, tenant_ctx.tenant_id, item_id)
    return ApiResponse(data=[KnowledgeRelationshipResponse.model_validate(r) for r in rels])


@knowledge_router.post(
    "/items/{item_id}/relationships",
    response_model=ApiResponse[KnowledgeRelationshipResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Add Knowledge Relationship with Cycle Prevention",
)
async def add_relationship(
    item_id: UUID,
    payload: KnowledgeRelationshipCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(KNOWLEDGE_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    rel = await service.add_relationship(
        db,
        tenant_ctx.tenant_id,
        source_id=item_id,
        target_id=payload.target_item_id,
        rel_type=payload.relationship_type,
        description=payload.description,
    )
    await db.commit()
    return ApiResponse(data=KnowledgeRelationshipResponse.model_validate(rel))


# =============================================================================
# 7. ATTESTATIONS & ACKNOWLEDGEMENTS
# =============================================================================


@knowledge_router.post(
    "/items/{item_id}/acknowledgement-requirements",
    response_model=ApiResponse[KnowledgeAcknowledgementRequirementResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Configure Mandatory Policy Attestation Audience",
)
async def configure_acknowledgement_requirement(
    item_id: UUID,
    payload: KnowledgeAcknowledgementRequirementCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(KNOWLEDGE_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    req = await service.configure_acknowledgement_requirement(
        db, tenant_ctx.tenant_id, item_id, actor=current_user, payload=payload
    )
    await db.commit()
    return ApiResponse(data=KnowledgeAcknowledgementRequirementResponse.model_validate(req))


@knowledge_router.post(
    "/items/{item_id}/acknowledge",
    response_model=ApiResponse[KnowledgeUserAcknowledgementResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Submit User Policy Attestation (Exact Version)",
)
async def acknowledge_item(
    item_id: UUID,
    payload: KnowledgeUserAcknowledgementCreate,
    request: Request,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(KNOWLEDGE_ACKNOWLEDGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    client_ip = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent")
    ack = await service.acknowledge_item(
        db,
        tenant_ctx.tenant_id,
        item_id=item_id,
        actor=current_user,
        payload=payload,
        ip_address=client_ip,
        user_agent=user_agent,
    )
    await db.commit()
    return ApiResponse(data=KnowledgeUserAcknowledgementResponse.model_validate(ack))


@knowledge_router.get(
    "/items/{item_id}/attestation-report/{version_number}",
    response_model=ApiResponse[KnowledgeAttestationComplianceReport],
    summary="View Policy Attestation Compliance Report",
)
async def get_attestation_report(
    item_id: UUID,
    version_number: int,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(KNOWLEDGE_ATTESTATION_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    report_dict = await service.get_attestation_report(db, tenant_ctx.tenant_id, item_id, version_number)
    return ApiResponse(data=KnowledgeAttestationComplianceReport.model_validate(report_dict))


# =============================================================================
# 8. GOVERNANCE SUMMARY
# =============================================================================


@knowledge_router.get(
    "/governance/summary",
    response_model=ApiResponse[KnowledgeGovernanceSummary],
    summary="Get Institutional Knowledge Governance Summary Metrics",
)
async def get_governance_summary(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(KNOWLEDGE_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    summary = await service.get_governance_summary(db, tenant_ctx.tenant_id)
    return ApiResponse(data=KnowledgeGovernanceSummary.model_validate(summary))
