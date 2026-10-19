"""Enterprise Institutional Accreditation, Quality Assurance & Continuous Improvement API Router (Step 43)."""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_current_user, get_tenant_context, require_permission
from app.core.permissions import (
    ACCREDITATION_APPROVE_DOT,
    ACCREDITATION_ASSESS_DOT,
    ACCREDITATION_AUDIT_MANAGE_DOT,
    ACCREDITATION_CAPA_MANAGE_DOT,
    ACCREDITATION_CRITERIA_MANAGE_DOT,
    ACCREDITATION_EVIDENCE_MANAGE_DOT,
    ACCREDITATION_EVIDENCE_VERIFY_DOT,
    ACCREDITATION_FRAMEWORK_MANAGE_DOT,
    ACCREDITATION_IMPROVEMENT_MANAGE_DOT,
    ACCREDITATION_INDICATOR_MANAGE_DOT,
    ACCREDITATION_READ_DOT,
    ACCREDITATION_REPORT_EXPORT_DOT,
)
from app.core.tenant import TenantContext
from app.models.people import User
from app.schemas.accreditation import (
    AccreditationCriterionCreate,
    AccreditationCriterionResponse,
    AccreditationCriterionUpdate,
    AccreditationCycleCreate,
    AccreditationCycleResponse,
    AccreditationCycleUpdate,
    AccreditationDashboardSummary,
    AccreditationEvidenceCreate,
    AccreditationEvidenceMapCreate,
    AccreditationEvidenceMapResponse,
    AccreditationEvidenceResponse,
    AccreditationEvidenceVerify,
    AccreditationFrameworkCreate,
    AccreditationFrameworkPublish,
    AccreditationFrameworkResponse,
    AccreditationFrameworkUpdate,
    AccreditationFrameworkVersionResponse,
    AccreditationReadinessResponse,
    CriterionAssessmentDraftUpdate,
    CriterionAssessmentResponse,
    CriterionAssessmentReview,
    CriterionAssessmentSubmit,
    QualityAuditChecklistItemCreate,
    QualityAuditChecklistItemResponse,
    QualityAuditFinalize,
    QualityAuditProgramCreate,
    QualityAuditProgramResponse,
    QualityCAPAClose,
    QualityCAPACreate,
    QualityCAPAResponse,
    QualityFindingCreate,
    QualityFindingResponse,
    QualityImprovementPlanCreate,
    QualityImprovementPlanResponse,
    QualityImprovementPlanUpdate,
    QualityIndicatorCreate,
    QualityIndicatorObservationCreate,
    QualityIndicatorObservationResponse,
    QualityIndicatorResponse,
    QualityIndicatorUpdate,
)
from app.schemas.common import ApiResponse
from app.services.accreditation_service import AccreditationService

accreditation_router = APIRouter(prefix="/accreditation", tags=["Institutional Accreditation & Quality Assurance"])


# =============================================================================
# 1. ACCREDITATION FRAMEWORKS
# =============================================================================


@accreditation_router.get(
    "/frameworks",
    response_model=ApiResponse[list[AccreditationFrameworkResponse]],
    summary="List Accreditation Frameworks",
)
async def list_frameworks(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status: str | None = None,
    framework_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    service = AccreditationService(db)
    fws = await service.list_frameworks(
        tenant_ctx.tenant_id, status=status, framework_type=framework_type, limit=limit, offset=offset
    )
    return ApiResponse(data=[AccreditationFrameworkResponse.model_validate(f) for f in fws])


@accreditation_router.post(
    "/frameworks",
    response_model=ApiResponse[AccreditationFrameworkResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Accreditation Framework",
)
async def create_framework(
    payload: AccreditationFrameworkCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_FRAMEWORK_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = AccreditationService(db)
    fw = await service.create_framework(tenant_ctx.tenant_id, payload, current_user.id)
    return ApiResponse(data=AccreditationFrameworkResponse.model_validate(fw))


@accreditation_router.post(
    "/frameworks/seed-defaults",
    response_model=ApiResponse[list[AccreditationFrameworkResponse]],
    summary="Seed Standard Statutory Framework Templates (NAAC, NBA, ISO)",
)
async def seed_default_frameworks(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_FRAMEWORK_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = AccreditationService(db)
    seeded = await service.seed_default_frameworks_if_empty(tenant_ctx.tenant_id, current_user.id)
    return ApiResponse(data=[AccreditationFrameworkResponse.model_validate(f) for f in seeded])


@accreditation_router.get(
    "/frameworks/{framework_id}",
    response_model=ApiResponse[AccreditationFrameworkResponse],
    summary="Get Accreditation Framework by ID",
)
async def get_framework(
    framework_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = AccreditationService(db)
    fw = await service.get_framework(tenant_ctx.tenant_id, framework_id)
    return ApiResponse(data=AccreditationFrameworkResponse.model_validate(fw))


@accreditation_router.put(
    "/frameworks/{framework_id}",
    response_model=ApiResponse[AccreditationFrameworkResponse],
    summary="Update Accreditation Framework",
)
async def update_framework(
    framework_id: UUID,
    payload: AccreditationFrameworkUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_FRAMEWORK_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = AccreditationService(db)
    fw = await service.update_framework(tenant_ctx.tenant_id, framework_id, payload, current_user.id)
    return ApiResponse(data=AccreditationFrameworkResponse.model_validate(fw))


@accreditation_router.post(
    "/frameworks/{framework_id}/publish",
    response_model=ApiResponse[AccreditationFrameworkVersionResponse],
    summary="Publish Immutable Version Snapshot of Framework",
)
async def publish_framework(
    framework_id: UUID,
    payload: AccreditationFrameworkPublish,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_FRAMEWORK_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = AccreditationService(db)
    ver = await service.publish_framework_version(tenant_ctx.tenant_id, framework_id, payload, current_user.id)
    return ApiResponse(data=AccreditationFrameworkVersionResponse.model_validate(ver))


# =============================================================================
# 2. CRITERIA HIERARCHY
# =============================================================================


@accreditation_router.get(
    "/frameworks/{framework_id}/criteria",
    response_model=ApiResponse[list[AccreditationCriterionResponse]],
    summary="List Criteria for Framework",
)
async def list_criteria(
    framework_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    parent_id: UUID | None = None,
):
    service = AccreditationService(db)
    criteria = await service.list_criteria(tenant_ctx.tenant_id, framework_id, parent_id=parent_id)
    return ApiResponse(data=[AccreditationCriterionResponse.model_validate(c) for c in criteria])


@accreditation_router.post(
    "/frameworks/{framework_id}/criteria",
    response_model=ApiResponse[AccreditationCriterionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Criterion or Subcriterion",
)
async def create_criterion(
    framework_id: UUID,
    payload: AccreditationCriterionCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_CRITERIA_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = AccreditationService(db)
    crit = await service.create_criterion(tenant_ctx.tenant_id, framework_id, payload, current_user.id)
    return ApiResponse(data=AccreditationCriterionResponse.model_validate(crit))


@accreditation_router.get(
    "/criteria/{criterion_id}",
    response_model=ApiResponse[AccreditationCriterionResponse],
    summary="Get Criterion Details",
)
async def get_criterion(
    criterion_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = AccreditationService(db)
    crit = await service.get_criterion(tenant_ctx.tenant_id, criterion_id)
    return ApiResponse(data=AccreditationCriterionResponse.model_validate(crit))


@accreditation_router.put(
    "/criteria/{criterion_id}",
    response_model=ApiResponse[AccreditationCriterionResponse],
    summary="Update Criterion",
)
async def update_criterion(
    criterion_id: UUID,
    payload: AccreditationCriterionUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_CRITERIA_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = AccreditationService(db)
    crit = await service.update_criterion(tenant_ctx.tenant_id, criterion_id, payload, current_user.id)
    return ApiResponse(data=AccreditationCriterionResponse.model_validate(crit))


# =============================================================================
# 3. ASSESSMENT CYCLES & CRITERION ASSESSMENTS
# =============================================================================


@accreditation_router.get(
    "/cycles",
    response_model=ApiResponse[list[AccreditationCycleResponse]],
    summary="List Assessment Cycles",
)
async def list_cycles(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    framework_id: UUID | None = None,
):
    service = AccreditationService(db)
    cycles = await service.list_assessment_cycles(tenant_ctx.tenant_id, framework_id=framework_id)
    return ApiResponse(data=[AccreditationCycleResponse.model_validate(c) for c in cycles])


@accreditation_router.post(
    "/cycles",
    response_model=ApiResponse[AccreditationCycleResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Assessment Cycle with Auto-Initialized Criteria",
)
async def create_cycle(
    payload: AccreditationCycleCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_FRAMEWORK_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = AccreditationService(db)
    cycle = await service.create_assessment_cycle(tenant_ctx.tenant_id, payload, current_user.id)
    return ApiResponse(data=AccreditationCycleResponse.model_validate(cycle))


@accreditation_router.get(
    "/cycles/{cycle_id}",
    response_model=ApiResponse[AccreditationCycleResponse],
    summary="Get Assessment Cycle Details",
)
async def get_cycle(
    cycle_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = AccreditationService(db)
    cycle = await service.get_assessment_cycle(tenant_ctx.tenant_id, cycle_id)
    return ApiResponse(data=AccreditationCycleResponse.model_validate(cycle))


@accreditation_router.get(
    "/cycles/{cycle_id}/assessments",
    response_model=ApiResponse[list[CriterionAssessmentResponse]],
    summary="List Criterion Assessments for Cycle",
)
async def list_cycle_assessments(
    cycle_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status: str | None = None,
):
    service = AccreditationService(db)
    assessments = await service.list_criterion_assessments(tenant_ctx.tenant_id, cycle_id, status=status)
    return ApiResponse(data=[CriterionAssessmentResponse.model_validate(a) for a in assessments])


@accreditation_router.get(
    "/assessments/{assessment_id}",
    response_model=ApiResponse[CriterionAssessmentResponse],
    summary="Get Criterion Assessment Details",
)
async def get_assessment(
    assessment_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = AccreditationService(db)
    assess = await service.get_criterion_assessment(tenant_ctx.tenant_id, assessment_id)
    return ApiResponse(data=CriterionAssessmentResponse.model_validate(assess))


@accreditation_router.put(
    "/assessments/{assessment_id}/draft",
    response_model=ApiResponse[CriterionAssessmentResponse],
    summary="Update Draft Criterion Assessment with Optimistic Concurrency",
)
async def update_assessment_draft(
    assessment_id: UUID,
    payload: CriterionAssessmentDraftUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_ASSESS_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = AccreditationService(db)
    assess = await service.update_criterion_assessment_draft(
        tenant_ctx.tenant_id, assessment_id, payload, current_user.id
    )
    return ApiResponse(data=CriterionAssessmentResponse.model_validate(assess))


@accreditation_router.post(
    "/assessments/{assessment_id}/submit",
    response_model=ApiResponse[CriterionAssessmentResponse],
    summary="Submit Assessment for Independent Review",
)
async def submit_assessment(
    assessment_id: UUID,
    payload: CriterionAssessmentSubmit,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_ASSESS_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = AccreditationService(db)
    assess = await service.submit_criterion_assessment(
        tenant_ctx.tenant_id, assessment_id, payload, current_user.id
    )
    return ApiResponse(data=CriterionAssessmentResponse.model_validate(assess))


@accreditation_router.post(
    "/assessments/{assessment_id}/review",
    response_model=ApiResponse[CriterionAssessmentResponse],
    summary="Conduct Independent Review of Assessment (Separation of Duties Enforced)",
)
async def review_assessment(
    assessment_id: UUID,
    payload: CriterionAssessmentReview,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_APPROVE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = AccreditationService(db)
    assess = await service.review_criterion_assessment(
        tenant_ctx.tenant_id, assessment_id, payload, current_user.id
    )
    return ApiResponse(data=CriterionAssessmentResponse.model_validate(assess))


# =============================================================================
# 4. EVIDENCE REPOSITORY & TRACEABILITY
# =============================================================================


@accreditation_router.get(
    "/evidences",
    response_model=ApiResponse[list[AccreditationEvidenceResponse]],
    summary="List Evidence Records",
)
async def list_evidences(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    category: str | None = None,
    verification_status: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    service = AccreditationService(db)
    evids = await service.list_evidences(
        tenant_ctx.tenant_id, category=category, verification_status=verification_status, limit=limit, offset=offset
    )
    return ApiResponse(data=[AccreditationEvidenceResponse.model_validate(e) for e in evids])


@accreditation_router.post(
    "/evidences",
    response_model=ApiResponse[AccreditationEvidenceResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Evidence Record with Document/Record Linkage",
)
async def create_evidence(
    payload: AccreditationEvidenceCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_EVIDENCE_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = AccreditationService(db)
    evid = await service.create_evidence(tenant_ctx.tenant_id, payload, current_user.id)
    return ApiResponse(data=AccreditationEvidenceResponse.model_validate(evid))


@accreditation_router.get(
    "/evidences/{evidence_id}",
    response_model=ApiResponse[AccreditationEvidenceResponse],
    summary="Get Evidence Record by ID",
)
async def get_evidence(
    evidence_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = AccreditationService(db)
    evid = await service.get_evidence(tenant_ctx.tenant_id, evidence_id)
    return ApiResponse(data=AccreditationEvidenceResponse.model_validate(evid))


@accreditation_router.post(
    "/evidences/{evidence_id}/verify",
    response_model=ApiResponse[AccreditationEvidenceResponse],
    summary="Record Verification Decision for Evidence Item",
)
async def verify_evidence(
    evidence_id: UUID,
    payload: AccreditationEvidenceVerify,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_EVIDENCE_VERIFY_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = AccreditationService(db)
    evid = await service.verify_evidence(tenant_ctx.tenant_id, evidence_id, payload, current_user.id)
    return ApiResponse(data=AccreditationEvidenceResponse.model_validate(evid))


@accreditation_router.post(
    "/assessments/{assessment_id}/evidence-maps",
    response_model=ApiResponse[AccreditationEvidenceMapResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Map Evidence Record to Criterion Assessment (Supports Cross-Criteria Reuse)",
)
async def map_evidence_to_assessment(
    assessment_id: UUID,
    payload: AccreditationEvidenceMapCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_EVIDENCE_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = AccreditationService(db)
    mapping = await service.map_evidence_to_assessment(
        tenant_ctx.tenant_id, assessment_id, payload.evidence_id, payload.relevance_remarks, current_user.id
    )
    return ApiResponse(data=AccreditationEvidenceMapResponse.model_validate(mapping))


# =============================================================================
# 5. QUALITY INDICATORS & OBSERVATIONS
# =============================================================================


@accreditation_router.get(
    "/indicators",
    response_model=ApiResponse[list[QualityIndicatorResponse]],
    summary="List Quality Indicators (KPIs)",
)
async def list_indicators(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    category: str | None = None,
):
    service = AccreditationService(db)
    qis = await service.list_indicators(tenant_ctx.tenant_id, category=category)
    return ApiResponse(data=[QualityIndicatorResponse.model_validate(q) for q in qis])


@accreditation_router.post(
    "/indicators",
    response_model=ApiResponse[QualityIndicatorResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Quality Indicator",
)
async def create_indicator(
    payload: QualityIndicatorCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_INDICATOR_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = AccreditationService(db)
    qi = await service.create_indicator(tenant_ctx.tenant_id, payload, current_user.id)
    return ApiResponse(data=QualityIndicatorResponse.model_validate(qi))


@accreditation_router.get(
    "/indicators/{indicator_id}",
    response_model=ApiResponse[QualityIndicatorResponse],
    summary="Get Quality Indicator Details",
)
async def get_indicator(
    indicator_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = AccreditationService(db)
    qi = await service.get_indicator(tenant_ctx.tenant_id, indicator_id)
    return ApiResponse(data=QualityIndicatorResponse.model_validate(qi))


@accreditation_router.post(
    "/indicators/{indicator_id}/observations",
    response_model=ApiResponse[QualityIndicatorObservationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Record Quality Metric Observation with Completeness & Outlier Validations",
)
async def record_observation(
    indicator_id: UUID,
    payload: QualityIndicatorObservationCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_INDICATOR_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = AccreditationService(db)
    obs = await service.record_observation(tenant_ctx.tenant_id, indicator_id, payload, current_user.id)
    return ApiResponse(data=QualityIndicatorObservationResponse.model_validate(obs))


# =============================================================================
# 6. INTERNAL QUALITY AUDITS
# =============================================================================


@accreditation_router.get(
    "/audits",
    response_model=ApiResponse[list[QualityAuditProgramResponse]],
    summary="List Quality Audit Programs",
)
async def list_audits(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status: str | None = None,
):
    service = AccreditationService(db)
    audits = await service.list_audit_programs(tenant_ctx.tenant_id, status=status)
    return ApiResponse(data=[QualityAuditProgramResponse.model_validate(a) for a in audits])


@accreditation_router.post(
    "/audits",
    response_model=ApiResponse[QualityAuditProgramResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Schedule Internal Quality Audit Program",
)
async def create_audit(
    payload: QualityAuditProgramCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_AUDIT_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = AccreditationService(db)
    audit = await service.create_audit_program(tenant_ctx.tenant_id, payload, current_user.id)
    return ApiResponse(data=QualityAuditProgramResponse.model_validate(audit))


@accreditation_router.get(
    "/audits/{program_id}",
    response_model=ApiResponse[QualityAuditProgramResponse],
    summary="Get Quality Audit Details",
)
async def get_audit(
    program_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = AccreditationService(db)
    audit = await service.get_audit_program(tenant_ctx.tenant_id, program_id)
    return ApiResponse(data=QualityAuditProgramResponse.model_validate(audit))


@accreditation_router.post(
    "/audits/{program_id}/checklists",
    response_model=ApiResponse[QualityAuditChecklistItemResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Add Checklist Item to Audit Program",
)
async def add_audit_checklist_item(
    program_id: UUID,
    payload: QualityAuditChecklistItemCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_AUDIT_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = AccreditationService(db)
    item = await service.add_audit_checklist_item(tenant_ctx.tenant_id, program_id, payload, current_user.id)
    return ApiResponse(data=QualityAuditChecklistItemResponse.model_validate(item))


@accreditation_router.post(
    "/audits/{program_id}/finalize",
    response_model=ApiResponse[QualityAuditProgramResponse],
    summary="Finalize and Lock Audit Report (Permanently Immutable)",
)
async def finalize_audit(
    program_id: UUID,
    payload: QualityAuditFinalize,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_AUDIT_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = AccreditationService(db)
    audit = await service.finalize_audit_report(tenant_ctx.tenant_id, program_id, payload, current_user.id)
    return ApiResponse(data=QualityAuditProgramResponse.model_validate(audit))


# =============================================================================
# 7. FINDINGS & CORRECTIVE ACTIONS (CAPA)
# =============================================================================


@accreditation_router.get(
    "/findings",
    response_model=ApiResponse[list[QualityFindingResponse]],
    summary="List Quality Findings & Compliance Gaps",
)
async def list_findings(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status: str | None = None,
    severity: str | None = None,
):
    service = AccreditationService(db)
    findings = await service.list_findings(tenant_ctx.tenant_id, status=status, severity=severity)
    return ApiResponse(data=[QualityFindingResponse.model_validate(f) for f in findings])


@accreditation_router.post(
    "/findings",
    response_model=ApiResponse[QualityFindingResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Log Compliance Finding or Audit Gap",
)
async def create_finding(
    payload: QualityFindingCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_CAPA_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = AccreditationService(db)
    finding = await service.create_finding(tenant_ctx.tenant_id, payload, current_user.id)
    return ApiResponse(data=QualityFindingResponse.model_validate(finding))


@accreditation_router.post(
    "/findings/{finding_id}/actions",
    response_model=ApiResponse[QualityCAPAResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Initiate Corrective / Preventive Action (CAPA) for Finding",
)
async def create_corrective_action(
    finding_id: UUID,
    payload: QualityCAPACreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_CAPA_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = AccreditationService(db)
    capa = await service.create_corrective_action(tenant_ctx.tenant_id, finding_id, payload, current_user.id)
    return ApiResponse(data=QualityCAPAResponse.model_validate(capa))


@accreditation_router.post(
    "/actions/{action_id}/close",
    response_model=ApiResponse[QualityCAPAResponse],
    summary="Verify and Close Corrective Action (Separation of Duties Enforced)",
)
async def close_corrective_action(
    action_id: UUID,
    payload: QualityCAPAClose,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_CAPA_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = AccreditationService(db)
    capa = await service.close_corrective_action(tenant_ctx.tenant_id, action_id, payload, current_user.id)
    return ApiResponse(data=QualityCAPAResponse.model_validate(capa))


# =============================================================================
# 8. CONTINUOUS QUALITY IMPROVEMENT (CQI)
# =============================================================================


@accreditation_router.get(
    "/improvement-plans",
    response_model=ApiResponse[list[QualityImprovementPlanResponse]],
    summary="List Continuous Quality Improvement (CQI) Plans",
)
async def list_improvement_plans(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status: str | None = None,
):
    service = AccreditationService(db)
    plans = await service.list_improvement_plans(tenant_ctx.tenant_id, status=status)
    return ApiResponse(data=[QualityImprovementPlanResponse.model_validate(p) for p in plans])


@accreditation_router.post(
    "/improvement-plans",
    response_model=ApiResponse[QualityImprovementPlanResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Continuous Quality Improvement Plan",
)
async def create_improvement_plan(
    payload: QualityImprovementPlanCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_IMPROVEMENT_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = AccreditationService(db)
    plan = await service.create_improvement_plan(tenant_ctx.tenant_id, payload, current_user.id)
    return ApiResponse(data=QualityImprovementPlanResponse.model_validate(plan))


# =============================================================================
# 9. ACCREDITATION READINESS & DASHBOARD
# =============================================================================


@accreditation_router.post(
    "/cycles/{cycle_id}/readiness/calculate",
    response_model=ApiResponse[AccreditationReadinessResponse],
    summary="Calculate Point-in-Time Accreditation Readiness Snapshot & Gap Analysis",
)
async def calculate_readiness(
    cycle_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = AccreditationService(db)
    snapshot = await service.calculate_readiness_snapshot(tenant_ctx.tenant_id, cycle_id, current_user.id)
    return ApiResponse(data=AccreditationReadinessResponse.model_validate(snapshot))


@accreditation_router.get(
    "/dashboard/summary",
    response_model=ApiResponse[AccreditationDashboardSummary],
    summary="Get Accreditation & Quality Assurance Dashboard Summary KPIs",
)
async def get_dashboard_summary(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_READ_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = AccreditationService(db)
    summary_data = await service.get_dashboard_summary(tenant_ctx.tenant_id)
    return ApiResponse(data=summary_data)


@accreditation_router.post(
    "/scheduler/sweep",
    response_model=ApiResponse[dict[str, Any]],
    summary="Trigger Quality Assurance Review Sweep (Flags Expired Evidence & Overdue CAPA)",
)
async def trigger_quality_sweep(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACCREDITATION_FRAMEWORK_MANAGE_DOT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
):
    service = AccreditationService(db)
    sweep_results = await service.sweep_quality_reviews()
    return ApiResponse(data=sweep_results)
