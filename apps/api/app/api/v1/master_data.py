"""Enterprise Master Data Management & Data Quality API Endpoints (Step 24)."""

from math import ceil
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_tenant_context, require_permission
from app.core.permissions import (
    MASTER_DATA_APPROVE,
    MASTER_DATA_CORRECT,
    MASTER_DATA_DEFINITION_MANAGE,
    MASTER_DATA_MERGE,
    MASTER_DATA_QUALITY_MANAGE,
    MASTER_DATA_READ,
    MASTER_DATA_REFERENCE_MANAGE,
    MASTER_DATA_VALIDATE,
)
from app.core.tenant import TenantContext
from app.models.master_data import (
    DuplicateStatus,
    QualityIssueStatus,
    QualitySeverity,
)
from app.models.people import User
from app.schemas.common import ApiResponse, PaginatedMeta, PaginatedResponse
from app.schemas.master_data import (
    DataQualityIssueResponse,
    DataQualityIssueUpdate,
    DataQualityRuleCreate,
    DataQualityRuleResponse,
    DataQualityRuleUpdate,
    DataQualitySummaryResponse,
    DataQualityValidateRequest,
    DataQualityValidateResponse,
    DuplicateCandidateResponse,
    DuplicateCandidateReviewRequest,
    DuplicateDetectRequest,
    MasterDataCorrectionCreate,
    MasterDataCorrectionResponse,
    MasterDataCorrectionReviewRequest,
    MasterDataDefinitionCreate,
    MasterDataDefinitionResponse,
    MasterDataDefinitionUpdate,
    MasterDataLineageCreate,
    MasterDataLineageResponse,
    MasterDataMergeRequest,
    MasterDataMergeResponse,
    MasterDataMergeRollbackRequest,
    ReferenceDataDefinitionCreate,
    ReferenceDataDefinitionResponse,
    ReferenceDataValueCreate,
    ReferenceDataValueResponse,
    ReferenceDataValueUpdate,
)
from app.services.duplicate_detection_service import DuplicateDetectionService
from app.services.master_data_service import MasterDataService
from app.services.merge_service import MergeService

router = APIRouter(prefix="/master-data", tags=["Master Data Management & Data Quality"])


# =============================================================================
# 1. MASTER DATA DEFINITIONS
# =============================================================================


@router.get(
    "/definitions",
    response_model=ApiResponse[list[MasterDataDefinitionResponse]],
    summary="List all registered master data governance definitions",
)
async def list_master_data_definitions(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(MASTER_DATA_READ))],
    is_active: bool | None = Query(None),
) -> ApiResponse[list[MasterDataDefinitionResponse]]:
    definitions = await MasterDataService.list_definitions(db, is_active=is_active)
    return ApiResponse(data=[MasterDataDefinitionResponse.model_validate(d) for d in definitions])


@router.get(
    "/definitions/{key}",
    response_model=ApiResponse[MasterDataDefinitionResponse],
    summary="Get master data definition details by key",
)
async def get_master_data_definition(
    key: str,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(MASTER_DATA_READ))],
) -> ApiResponse[MasterDataDefinitionResponse]:
    defn = await MasterDataService.get_definition(db, key)
    return ApiResponse(data=MasterDataDefinitionResponse.model_validate(defn))


@router.post(
    "/definitions",
    response_model=ApiResponse[MasterDataDefinitionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new master data governance entity definition",
)
async def create_master_data_definition(
    payload: MasterDataDefinitionCreate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(MASTER_DATA_DEFINITION_MANAGE))],
) -> ApiResponse[MasterDataDefinitionResponse]:
    defn = await MasterDataService.create_definition(db, payload, actor_id=user.id)
    return ApiResponse(data=MasterDataDefinitionResponse.model_validate(defn))


@router.patch(
    "/definitions/{key}",
    response_model=ApiResponse[MasterDataDefinitionResponse],
    summary="Update master data governance definition settings",
)
async def update_master_data_definition(
    key: str,
    payload: MasterDataDefinitionUpdate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(MASTER_DATA_DEFINITION_MANAGE))],
) -> ApiResponse[MasterDataDefinitionResponse]:
    defn = await MasterDataService.update_definition(db, key, payload, actor_id=user.id)
    return ApiResponse(data=MasterDataDefinitionResponse.model_validate(defn))


# =============================================================================
# 2. REFERENCE DATA DEFINITIONS & VALUES
# =============================================================================


@router.get(
    "/reference-data/definitions",
    response_model=ApiResponse[list[ReferenceDataDefinitionResponse]],
    summary="List controlled reference data categories",
)
async def list_reference_definitions(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(MASTER_DATA_READ))],
) -> ApiResponse[list[ReferenceDataDefinitionResponse]]:
    defs = await MasterDataService.list_reference_definitions(db)
    return ApiResponse(data=[ReferenceDataDefinitionResponse.model_validate(d) for d in defs])


@router.post(
    "/reference-data/definitions",
    response_model=ApiResponse[ReferenceDataDefinitionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new controlled reference category",
)
async def create_reference_definition(
    payload: ReferenceDataDefinitionCreate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(MASTER_DATA_REFERENCE_MANAGE))],
) -> ApiResponse[ReferenceDataDefinitionResponse]:
    ref_def = await MasterDataService.create_reference_definition(db, payload)
    return ApiResponse(data=ReferenceDataDefinitionResponse.model_validate(ref_def))


@router.get(
    "/reference-data",
    response_model=ApiResponse[list[ReferenceDataValueResponse]],
    summary="List tenant controlled reference values",
)
async def list_reference_values(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(MASTER_DATA_READ))],
    category: str | None = Query(None),
    is_active: bool | None = Query(None),
) -> ApiResponse[list[ReferenceDataValueResponse]]:
    vals = await MasterDataService.list_reference_values(
        db, tenant.tenant_id, category=category, is_active=is_active
    )
    return ApiResponse(data=[ReferenceDataValueResponse.model_validate(v) for v in vals])


@router.get(
    "/reference-data/values",
    response_model=ApiResponse[list[ReferenceDataValueResponse]],
    summary="List tenant controlled reference values (values alias)",
    include_in_schema=False,
)
async def list_reference_values_alias(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(MASTER_DATA_READ))],
    category: str | None = Query(None),
    is_active: bool | None = Query(None),
) -> ApiResponse[list[ReferenceDataValueResponse]]:
    return await list_reference_values(tenant, db, user, category, is_active)


@router.post(
    "/reference-data",
    response_model=ApiResponse[ReferenceDataValueResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Add a controlled reference value",
)
async def create_reference_value(
    payload: ReferenceDataValueCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(MASTER_DATA_REFERENCE_MANAGE))],
) -> ApiResponse[ReferenceDataValueResponse]:
    val = await MasterDataService.create_reference_value(
        db, tenant.tenant_id, payload, actor_id=user.id
    )
    return ApiResponse(data=ReferenceDataValueResponse.model_validate(val))


@router.post(
    "/reference-data/values",
    response_model=ApiResponse[ReferenceDataValueResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Add a controlled reference value (values alias)",
    include_in_schema=False,
)
async def create_reference_value_alias(
    payload: ReferenceDataValueCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(MASTER_DATA_REFERENCE_MANAGE))],
) -> ApiResponse[ReferenceDataValueResponse]:
    return await create_reference_value(payload, tenant, db, user)


@router.patch(
    "/reference-data/{id}",
    response_model=ApiResponse[ReferenceDataValueResponse],
    summary="Update a controlled reference value",
)
async def update_reference_value(
    id: UUID,
    payload: ReferenceDataValueUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(MASTER_DATA_REFERENCE_MANAGE))],
) -> ApiResponse[ReferenceDataValueResponse]:
    val = await MasterDataService.update_reference_value(
        db, tenant.tenant_id, id, payload, actor_id=user.id
    )
    return ApiResponse(data=ReferenceDataValueResponse.model_validate(val))


@router.delete(
    "/reference-data/{id}",
    response_model=ApiResponse[dict[str, Any]],
    summary="Delete a non-system controlled reference value",
)
async def delete_reference_value(
    id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(MASTER_DATA_REFERENCE_MANAGE))],
) -> ApiResponse[dict[str, Any]]:
    deleted = await MasterDataService.delete_reference_value(
        db, tenant.tenant_id, id, actor_id=user.id
    )
    return ApiResponse(data={"deleted": deleted, "id": id})


@router.delete(
    "/reference-data/values/{id}",
    response_model=ApiResponse[dict[str, Any]],
    summary="Delete a non-system controlled reference value (values alias)",
    include_in_schema=False,
)
async def delete_reference_value_alias(
    id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(MASTER_DATA_REFERENCE_MANAGE))],
) -> ApiResponse[dict[str, Any]]:
    return await delete_reference_value(id, tenant, db, user)


# =============================================================================
# 3. DATA QUALITY RULES & VALIDATION
# =============================================================================


@router.get(
    "/rules",
    response_model=ApiResponse[list[DataQualityRuleResponse]],
    summary="List data quality validation rules for tenant",
)
async def list_quality_rules(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(MASTER_DATA_READ))],
    master_type: str | None = Query(None),
    is_active: bool | None = Query(None),
) -> ApiResponse[list[DataQualityRuleResponse]]:
    rules = await MasterDataService.list_quality_rules(
        db, tenant.tenant_id, master_type=master_type, is_active=is_active
    )
    return ApiResponse(data=[DataQualityRuleResponse.model_validate(r) for r in rules])


@router.post(
    "/rules",
    response_model=ApiResponse[DataQualityRuleResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a configurable data quality validation rule",
)
async def create_quality_rule(
    payload: DataQualityRuleCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(MASTER_DATA_QUALITY_MANAGE))],
) -> ApiResponse[DataQualityRuleResponse]:
    rule = await MasterDataService.create_quality_rule(
        db, tenant.tenant_id, payload, actor_id=user.id
    )
    return ApiResponse(data=DataQualityRuleResponse.model_validate(rule))


@router.patch(
    "/rules/{id}",
    response_model=ApiResponse[DataQualityRuleResponse],
    summary="Update a data quality validation rule",
)
async def update_quality_rule(
    id: UUID,
    payload: DataQualityRuleUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(MASTER_DATA_QUALITY_MANAGE))],
) -> ApiResponse[DataQualityRuleResponse]:
    rule = await MasterDataService.update_quality_rule(
        db, tenant.tenant_id, id, payload, actor_id=user.id
    )
    return ApiResponse(data=DataQualityRuleResponse.model_validate(rule))


@router.post(
    "/validate",
    response_model=ApiResponse[DataQualityValidateResponse],
    summary="Evaluate active quality rules against a data payload on-demand",
)
async def validate_record(
    payload: DataQualityValidateRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(MASTER_DATA_VALIDATE))],
) -> ApiResponse[DataQualityValidateResponse]:
    res = await MasterDataService.validate_record(
        db=db,
        tenant_id=tenant.tenant_id,
        master_type=payload.master_type,
        payload=payload.payload,
        record_id=payload.record_id,
    )
    return ApiResponse(data=res)


# =============================================================================
# 4. QUALITY SUMMARY & ISSUES QUEUE
# =============================================================================


@router.get(
    "/quality/summary",
    response_model=ApiResponse[DataQualitySummaryResponse],
    summary="Retrieve high-level data quality dashboard analytics",
)
async def get_quality_summary(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(MASTER_DATA_READ))],
) -> ApiResponse[DataQualitySummaryResponse]:
    summary = await MasterDataService.get_quality_summary(db, tenant.tenant_id)
    return ApiResponse(data=summary)


@router.get(
    "/quality/issues",
    response_model=PaginatedResponse[DataQualityIssueResponse],
    summary="List data quality defects in the stewardship queue",
)
async def list_quality_issues(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(MASTER_DATA_READ))],
    master_type: str | None = Query(None),
    status_filter: QualityIssueStatus | None = Query(None, alias="status"),
    severity: QualitySeverity | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
) -> PaginatedResponse[DataQualityIssueResponse]:
    offset = (page - 1) * page_size
    issues, total = await MasterDataService.list_quality_issues(
        db,
        tenant.tenant_id,
        master_type=master_type,
        status=status_filter.value if status_filter else None,
        severity=severity.value if severity else None,
        limit=page_size,
        offset=offset,
    )
    meta = PaginatedMeta(
        total_items=total,
        total_pages=ceil(total / page_size) if total > 0 else 1,
        current_page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        data=[DataQualityIssueResponse.model_validate(i) for i in issues], meta=meta
    )


@router.get(
    "/quality/issues/{id}",
    response_model=ApiResponse[DataQualityIssueResponse],
    summary="Get single data quality defect detail by ID",
)
async def get_quality_issue(
    id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(MASTER_DATA_READ))],
) -> ApiResponse[DataQualityIssueResponse]:
    issue = await MasterDataService.get_quality_issue(db, tenant.tenant_id, id)
    return ApiResponse(data=DataQualityIssueResponse.model_validate(issue))


@router.patch(
    "/quality/issues/{id}",
    response_model=ApiResponse[DataQualityIssueResponse],
    summary="Update status, assign steward, or add resolution notes to quality issue",
)
async def update_quality_issue(
    id: UUID,
    payload: DataQualityIssueUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(MASTER_DATA_QUALITY_MANAGE))],
) -> ApiResponse[DataQualityIssueResponse]:
    issue = await MasterDataService.update_quality_issue(
        db,
        tenant.tenant_id,
        id,
        status=payload.status,
        assigned_to=payload.assigned_to,
        notes=payload.resolution_notes,
        actor_id=user.id,
    )
    return ApiResponse(data=DataQualityIssueResponse.model_validate(issue))


# =============================================================================
# 5. DUPLICATE DETECTION & CANDIDATES
# =============================================================================


@router.post(
    "/duplicates/detect",
    response_model=ApiResponse[list[DuplicateCandidateResponse]],
    summary="Run deterministic duplicate matching on a master data category",
)
async def detect_duplicates(
    payload: DuplicateDetectRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(MASTER_DATA_VALIDATE))],
) -> ApiResponse[list[DuplicateCandidateResponse]]:
    candidates = await DuplicateDetectionService.detect_duplicates(
        db=db,
        tenant_id=tenant.tenant_id,
        master_type=payload.master_type,
        limit=payload.limit,
    )
    return ApiResponse(data=[DuplicateCandidateResponse.model_validate(c) for c in candidates])


@router.get(
    "/duplicates",
    response_model=PaginatedResponse[DuplicateCandidateResponse],
    summary="List duplicate candidate pairs awaiting stewardship resolution",
)
async def list_duplicate_candidates(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(MASTER_DATA_READ))],
    master_type: str | None = Query(None),
    status_filter: DuplicateStatus | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
) -> PaginatedResponse[DuplicateCandidateResponse]:
    offset = (page - 1) * page_size
    cands, total = await MasterDataService.list_duplicate_candidates(
        db,
        tenant.tenant_id,
        master_type=master_type,
        status=status_filter.value if status_filter else None,
        limit=page_size,
        offset=offset,
    )
    meta = PaginatedMeta(
        total_items=total,
        total_pages=ceil(total / page_size) if total > 0 else 1,
        current_page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        data=[DuplicateCandidateResponse.model_validate(c) for c in cands], meta=meta
    )


@router.get(
    "/duplicates/{id}",
    response_model=ApiResponse[DuplicateCandidateResponse],
    summary="Get duplicate candidate pair details by ID",
)
async def get_duplicate_candidate(
    id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(MASTER_DATA_READ))],
) -> ApiResponse[DuplicateCandidateResponse]:
    cand = await MasterDataService.get_duplicate_candidate(db, tenant.tenant_id, id)
    return ApiResponse(data=DuplicateCandidateResponse.model_validate(cand))


@router.post(
    "/duplicates/{id}/review",
    response_model=ApiResponse[DuplicateCandidateResponse],
    summary="Steward resolution for duplicate candidate pair (confirm or dismiss)",
)
async def review_duplicate_candidate(
    id: UUID,
    payload: DuplicateCandidateReviewRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(MASTER_DATA_QUALITY_MANAGE))],
) -> ApiResponse[DuplicateCandidateResponse]:
    cand = await DuplicateDetectionService.review_candidate(
        db=db,
        tenant_id=tenant.tenant_id,
        candidate_id=id,
        status=payload.status,
        reviewer_id=user.id,
        notes=payload.notes,
    )
    return ApiResponse(data=DuplicateCandidateResponse.model_validate(cand))


@router.post(
    "/duplicates/{id}/confirm",
    response_model=ApiResponse[DuplicateCandidateResponse],
    summary="Confirm a duplicate candidate pair",
)
async def confirm_duplicate_candidate(
    id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(MASTER_DATA_QUALITY_MANAGE))],
) -> ApiResponse[DuplicateCandidateResponse]:
    cand = await DuplicateDetectionService.review_candidate(
        db=db,
        tenant_id=tenant.tenant_id,
        candidate_id=id,
        status=DuplicateStatus.CONFIRMED_DUPLICATE,
        reviewer_id=user.id,
    )
    return ApiResponse(data=DuplicateCandidateResponse.model_validate(cand))


@router.post(
    "/duplicates/{id}/dismiss",
    response_model=ApiResponse[DuplicateCandidateResponse],
    summary="Dismiss a duplicate candidate pair (not duplicate)",
)
async def dismiss_duplicate_candidate(
    id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(MASTER_DATA_QUALITY_MANAGE))],
) -> ApiResponse[DuplicateCandidateResponse]:
    cand = await DuplicateDetectionService.review_candidate(
        db=db,
        tenant_id=tenant.tenant_id,
        candidate_id=id,
        status=DuplicateStatus.NOT_DUPLICATE,
        reviewer_id=user.id,
    )
    return ApiResponse(data=DuplicateCandidateResponse.model_validate(cand))


# =============================================================================
# 6. MERGE WORKFLOW
# =============================================================================


@router.post(
    "/merge",
    response_model=ApiResponse[MasterDataMergeResponse],
    status_code=status.HTTP_200_OK,
    summary="Execute controlled duplicate merge with relationship reassignment",
)
async def execute_merge(
    payload: MasterDataMergeRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(MASTER_DATA_MERGE))],
) -> ApiResponse[MasterDataMergeResponse]:
    merge_op = await MergeService.execute_merge(
        db=db,
        tenant_id=tenant.tenant_id,
        master_type=payload.master_type,
        survivor_record_id=payload.survivor_record_id,
        merged_record_id=payload.merged_record_id,
        survivorship_rule=payload.survivorship_rule,
        field_decisions=payload.field_decisions,
        reason=payload.reason,
        actor_id=user.id,
    )
    return ApiResponse(
        data=MasterDataMergeResponse(
            operation_id=merge_op.id,
            tenant_id=merge_op.tenant_id,
            master_type=merge_op.master_type,
            survivor_record_id=merge_op.survivor_record_id,
            merged_record_id=merge_op.merged_record_id,
            survivorship_rule=merge_op.survivorship_rule,
            reassigned_counts=merge_op.reassigned_counts_json or {},
            status=merge_op.status,
            is_reversible=merge_op.is_reversible,
            created_at=merge_op.created_at,
        )
    )


@router.post(
    "/duplicates/merge",
    response_model=ApiResponse[MasterDataMergeResponse],
    status_code=status.HTTP_200_OK,
    summary="Execute duplicate merge (duplicates alias)",
    include_in_schema=False,
)
async def execute_duplicates_merge(
    payload: MasterDataMergeRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(MASTER_DATA_MERGE))],
) -> ApiResponse[MasterDataMergeResponse]:
    return await execute_merge(payload, tenant, db, user)


@router.post(
    "/duplicates/{id}/merge",
    response_model=ApiResponse[MasterDataMergeResponse],
    status_code=status.HTTP_200_OK,
    summary="Execute duplicate merge by candidate ID",
)
async def execute_candidate_merge(
    id: UUID,
    payload: MasterDataMergeRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(MASTER_DATA_MERGE))],
) -> ApiResponse[MasterDataMergeResponse]:
    return await execute_merge(payload, tenant, db, user)


@router.post(
    "/merge/{id}/rollback",
    response_model=ApiResponse[dict[str, Any]],
    summary="Roll back a previously completed master data merge operation",
)
async def rollback_merge(
    id: UUID,
    payload: MasterDataMergeRollbackRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(MASTER_DATA_MERGE))],
) -> ApiResponse[dict[str, Any]]:
    rolled_back_op = await MergeService.rollback_merge(
        db=db,
        tenant_id=tenant.tenant_id,
        operation_id=id,
        reason=payload.reason,
        actor_id=user.id,
    )
    return ApiResponse(
        data={
            "operation_id": rolled_back_op.id,
            "status": rolled_back_op.status,
            "rolled_back_at": rolled_back_op.rolled_back_at,
            "reason": rolled_back_op.rollback_reason,
        }
    )


# =============================================================================
# 7. CORRECTIONS & LINEAGE
# =============================================================================


@router.post(
    "/corrections",
    response_model=ApiResponse[MasterDataCorrectionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Propose master data attribute correction for stewardship review",
)
async def create_correction(
    payload: MasterDataCorrectionCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(MASTER_DATA_CORRECT))],
) -> ApiResponse[MasterDataCorrectionResponse]:
    corr = await MasterDataService.create_correction(
        db, tenant.tenant_id, payload, actor_id=user.id
    )
    return ApiResponse(data=MasterDataCorrectionResponse.model_validate(corr))


@router.post(
    "/corrections/{id}/review",
    response_model=ApiResponse[MasterDataCorrectionResponse],
    summary="Review and apply or reject a master data correction request",
)
async def review_correction(
    id: UUID,
    payload: MasterDataCorrectionReviewRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(MASTER_DATA_APPROVE))],
) -> ApiResponse[MasterDataCorrectionResponse]:
    corr = await MasterDataService.review_correction(
        db,
        tenant.tenant_id,
        id,
        decision=payload.decision,
        notes=payload.notes,
        reviewer_id=user.id,
    )
    return ApiResponse(data=MasterDataCorrectionResponse.model_validate(corr))


@router.get(
    "/lineage/{master_type}/{record_id}",
    response_model=ApiResponse[list[MasterDataLineageResponse]],
    summary="Retrieve provenance and modification lineage for a master record",
)
async def get_record_lineage(
    master_type: str,
    record_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(MASTER_DATA_READ))],
) -> ApiResponse[list[MasterDataLineageResponse]]:
    lineage = await MasterDataService.get_lineage(db, tenant.tenant_id, master_type, record_id)
    return ApiResponse(data=[MasterDataLineageResponse.model_validate(lin) for lin in lineage])


@router.post(
    "/lineage",
    response_model=ApiResponse[MasterDataLineageResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Record provenance metadata for a master record mutation or ingestion",
)
async def record_lineage(
    payload: MasterDataLineageCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[User, Depends(require_permission(MASTER_DATA_CORRECT))],
) -> ApiResponse[MasterDataLineageResponse]:
    lineage = await MasterDataService.record_lineage(
        db, tenant.tenant_id, payload, actor_id=user.id
    )
    return ApiResponse(data=MasterDataLineageResponse.model_validate(lineage))
