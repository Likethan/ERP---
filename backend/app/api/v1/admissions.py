"""Admissions, Enrollment & Onboarding Orchestration REST API Router (Step 48)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_current_user, get_tenant_context, require_permission
from app.core.permissions import (
    ADMISSIONS_APPLICANT_MANAGE,
    ADMISSIONS_APPLICANT_READ,
    ADMISSIONS_APPLICATION_MANAGE,
    ADMISSIONS_APPLICATION_READ,
    ADMISSIONS_CYCLE_MANAGE,
    ADMISSIONS_CYCLE_READ,
    ADMISSIONS_DOCUMENT_VERIFY,
    ADMISSIONS_ELIGIBILITY_EVALUATE,
    ADMISSIONS_ENROLLMENT_ORCHESTRATE,
    ADMISSIONS_OFFERS_MANAGE,
    ADMISSIONS_ONBOARDING_MANAGE,
    ADMISSIONS_REPORTS_READ,
    ADMISSIONS_REVIEW_MANAGE,
    ADMISSIONS_SELECTION_MANAGE,
)
from app.core.tenant import TenantContext
from app.models.people import User
from app.schemas.admissions import (
    AdmissionApplicationCreate,
    AdmissionApplicationResponse,
    AdmissionApplicationUpdate,
    AdmissionCycleCreate,
    AdmissionCycleResponse,
    AdmissionCycleUpdate,
    AdmissionOfferCreate,
    AdmissionOfferRespond,
    AdmissionOfferResponse,
    AdmissionOfferRevoke,
    AdmissionsAnalyticsResponse,
    ApplicantMergeRequest,
    ApplicantProfileCreate,
    ApplicantProfileResponse,
    ApplicantProfileUpdate,
    ApplicationDocumentRequirementCreate,
    ApplicationDocumentRequirementResponse,
    ApplicationDocumentResponse,
    ApplicationDocumentUpload,
    ApplicationDocumentVerify,
    ApplicationReopenRequest,
    ApplicationReviewCreate,
    ApplicationReviewResponse,
    ApplicationStatusTransition,
    ApplicationWithdrawRequest,
    EligibilityEvaluationRequest,
    EligibilityEvaluationResponse,
    EligibilityRuleCreate,
    EligibilityRuleResponse,
    EligibilityRuleUpdate,
    EnrollmentWorkflowInitiate,
    EnrollmentWorkflowResponse,
    OnboardingChecklistResponse,
    OnboardingTaskResponse,
    OnboardingTaskUpdate,
    SeatAllocationCreate,
    SeatAllocationResponse,
    SeatAllocationUpdate,
    SelectionRunCreate,
    SelectionRunResponse,
)
from app.schemas.common import ApiResponse
from app.services.admissions_service import AdmissionsService

router = APIRouter(prefix="/admissions", tags=["Admissions & Enrollment"])


# =============================================================================
# 1. ADMISSION CYCLES
# =============================================================================


@router.post(
    "/cycles",
    response_model=ApiResponse[AdmissionCycleResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(ADMISSIONS_CYCLE_MANAGE))],
)
async def create_admission_cycle(
    payload: AdmissionCycleCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AdmissionCycleResponse]:
    svc = AdmissionsService(db)
    cycle = await svc.create_cycle(tenant_ctx.tenant_id, payload, current_user.id)
    return ApiResponse(data=AdmissionCycleResponse.model_validate(cycle))


@router.get(
    "/cycles",
    response_model=ApiResponse[list[AdmissionCycleResponse]],
    dependencies=[Depends(require_permission(ADMISSIONS_CYCLE_READ))],
)
async def list_admission_cycles(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status: str | None = Query(None),
) -> ApiResponse[list[AdmissionCycleResponse]]:
    svc = AdmissionsService(db)
    cycles = await svc.list_cycles(tenant_ctx.tenant_id, status=status)
    return ApiResponse(data=[AdmissionCycleResponse.model_validate(c) for c in cycles])


@router.get(
    "/cycles/{cycle_id}",
    response_model=ApiResponse[AdmissionCycleResponse],
    dependencies=[Depends(require_permission(ADMISSIONS_CYCLE_READ))],
)
async def get_admission_cycle(
    cycle_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AdmissionCycleResponse]:
    svc = AdmissionsService(db)
    cycle = await svc.get_cycle(tenant_ctx.tenant_id, cycle_id)
    return ApiResponse(data=AdmissionCycleResponse.model_validate(cycle))


@router.patch(
    "/cycles/{cycle_id}",
    response_model=ApiResponse[AdmissionCycleResponse],
    dependencies=[Depends(require_permission(ADMISSIONS_CYCLE_MANAGE))],
)
async def update_admission_cycle(
    cycle_id: UUID,
    payload: AdmissionCycleUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AdmissionCycleResponse]:
    svc = AdmissionsService(db)
    cycle = await svc.update_cycle(tenant_ctx.tenant_id, cycle_id, payload, current_user.id)
    return ApiResponse(data=AdmissionCycleResponse.model_validate(cycle))


# =============================================================================
# 2. APPLICANT PROFILES
# =============================================================================


@router.post(
    "/applicants",
    response_model=ApiResponse[ApplicantProfileResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(ADMISSIONS_APPLICANT_MANAGE))],
)
async def register_applicant(
    payload: ApplicantProfileCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[ApplicantProfileResponse]:
    svc = AdmissionsService(db)
    applicant = await svc.register_applicant(tenant_ctx.tenant_id, payload, current_user.id)
    return ApiResponse(data=ApplicantProfileResponse.model_validate(applicant))


@router.get(
    "/applicants",
    response_model=ApiResponse[list[ApplicantProfileResponse]],
    dependencies=[Depends(require_permission(ADMISSIONS_APPLICANT_READ))],
)
async def list_applicants(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    search: str | None = Query(None),
) -> ApiResponse[list[ApplicantProfileResponse]]:
    svc = AdmissionsService(db)
    applicants = await svc.list_applicants(tenant_ctx.tenant_id, search=search)
    return ApiResponse(data=[ApplicantProfileResponse.model_validate(a) for a in applicants])


@router.get(
    "/applicants/{applicant_id}",
    response_model=ApiResponse[ApplicantProfileResponse],
    dependencies=[Depends(require_permission(ADMISSIONS_APPLICANT_READ))],
)
async def get_applicant(
    applicant_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[ApplicantProfileResponse]:
    svc = AdmissionsService(db)
    applicant = await svc.get_applicant(tenant_ctx.tenant_id, applicant_id)
    return ApiResponse(data=ApplicantProfileResponse.model_validate(applicant))


@router.patch(
    "/applicants/{applicant_id}",
    response_model=ApiResponse[ApplicantProfileResponse],
    dependencies=[Depends(require_permission(ADMISSIONS_APPLICANT_MANAGE))],
)
async def update_applicant(
    applicant_id: UUID,
    payload: ApplicantProfileUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[ApplicantProfileResponse]:
    svc = AdmissionsService(db)
    applicant = await svc.update_applicant(tenant_ctx.tenant_id, applicant_id, payload, current_user.id)
    return ApiResponse(data=ApplicantProfileResponse.model_validate(applicant))


@router.post(
    "/applicants/{applicant_id}/merge",
    response_model=ApiResponse[ApplicantProfileResponse],
    dependencies=[Depends(require_permission(ADMISSIONS_APPLICANT_MANAGE))],
)
async def merge_applicant(
    applicant_id: UUID,
    payload: ApplicantMergeRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[ApplicantProfileResponse]:
    svc = AdmissionsService(db)
    target = await svc.merge_applicants(
        tenant_ctx.tenant_id,
        source_applicant_id=applicant_id,
        target_applicant_id=payload.target_applicant_id,
        reason=payload.merge_reason,
        author_id=current_user.id,
    )
    return ApiResponse(data=ApplicantProfileResponse.model_validate(target))


# =============================================================================
# 3. APPLICATIONS WORKFLOW
# =============================================================================


@router.post(
    "/applications",
    response_model=ApiResponse[AdmissionApplicationResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(ADMISSIONS_APPLICATION_MANAGE))],
)
async def create_application(
    payload: AdmissionApplicationCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AdmissionApplicationResponse]:
    svc = AdmissionsService(db)
    application = await svc.create_application(tenant_ctx.tenant_id, payload, current_user.id)
    return ApiResponse(data=AdmissionApplicationResponse.model_validate(application))


@router.get(
    "/applications",
    response_model=ApiResponse[list[AdmissionApplicationResponse]],
    dependencies=[Depends(require_permission(ADMISSIONS_APPLICATION_READ))],
)
async def list_applications(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    cycle_id: UUID | None = Query(None),
    program_id: UUID | None = Query(None),
    status: str | None = Query(None),
) -> ApiResponse[list[AdmissionApplicationResponse]]:
    svc = AdmissionsService(db)
    apps = await svc.list_applications(
        tenant_ctx.tenant_id, cycle_id=cycle_id, program_id=program_id, status=status
    )
    return ApiResponse(data=[AdmissionApplicationResponse.model_validate(a) for a in apps])


@router.get(
    "/applications/{application_id}",
    response_model=ApiResponse[AdmissionApplicationResponse],
    dependencies=[Depends(require_permission(ADMISSIONS_APPLICATION_READ))],
)
async def get_application(
    application_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AdmissionApplicationResponse]:
    svc = AdmissionsService(db)
    application = await svc.get_application(tenant_ctx.tenant_id, application_id)
    return ApiResponse(data=AdmissionApplicationResponse.model_validate(application))


@router.patch(
    "/applications/{application_id}",
    response_model=ApiResponse[AdmissionApplicationResponse],
    dependencies=[Depends(require_permission(ADMISSIONS_APPLICATION_MANAGE))],
)
async def update_application(
    application_id: UUID,
    payload: AdmissionApplicationUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AdmissionApplicationResponse]:
    svc = AdmissionsService(db)
    application = await svc.update_application(
        tenant_ctx.tenant_id, application_id, payload, current_user.id
    )
    return ApiResponse(data=AdmissionApplicationResponse.model_validate(application))


@router.post(
    "/applications/{application_id}/submit",
    response_model=ApiResponse[AdmissionApplicationResponse],
    dependencies=[Depends(require_permission(ADMISSIONS_APPLICATION_MANAGE))],
)
async def submit_application(
    application_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AdmissionApplicationResponse]:
    svc = AdmissionsService(db)
    application = await svc.submit_application(
        tenant_ctx.tenant_id, application_id, current_user.id
    )
    return ApiResponse(data=AdmissionApplicationResponse.model_validate(application))


@router.post(
    "/applications/{application_id}/status",
    response_model=ApiResponse[AdmissionApplicationResponse],
    dependencies=[Depends(require_permission(ADMISSIONS_APPLICATION_MANAGE))],
)
async def transition_application_status(
    application_id: UUID,
    payload: ApplicationStatusTransition,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AdmissionApplicationResponse]:
    svc = AdmissionsService(db)
    application = await svc.transition_application_status(
        tenant_ctx.tenant_id, application_id, payload, current_user.id
    )
    return ApiResponse(data=AdmissionApplicationResponse.model_validate(application))


@router.post(
    "/applications/{application_id}/withdraw",
    response_model=ApiResponse[AdmissionApplicationResponse],
    dependencies=[Depends(require_permission(ADMISSIONS_APPLICATION_MANAGE))],
)
async def withdraw_application(
    application_id: UUID,
    payload: ApplicationWithdrawRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AdmissionApplicationResponse]:
    svc = AdmissionsService(db)
    application = await svc.withdraw_application(
        tenant_ctx.tenant_id, application_id, payload.withdrawal_reason, current_user.id
    )
    return ApiResponse(data=AdmissionApplicationResponse.model_validate(application))


@router.post(
    "/applications/{application_id}/reopen",
    response_model=ApiResponse[AdmissionApplicationResponse],
    dependencies=[Depends(require_permission(ADMISSIONS_APPLICATION_MANAGE))],
)
async def reopen_application(
    application_id: UUID,
    payload: ApplicationReopenRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AdmissionApplicationResponse]:
    svc = AdmissionsService(db)
    application = await svc.reopen_application(
        tenant_ctx.tenant_id,
        application_id,
        payload.reopening_reason,
        payload.correction_window_hours,
        current_user.id,
    )
    return ApiResponse(data=AdmissionApplicationResponse.model_validate(application))


# =============================================================================
# 4. DOCUMENTS & VERIFICATION
# =============================================================================


@router.post(
    "/document-requirements",
    response_model=ApiResponse[ApplicationDocumentRequirementResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(ADMISSIONS_APPLICATION_MANAGE))],
)
async def create_document_requirement(
    payload: ApplicationDocumentRequirementCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[ApplicationDocumentRequirementResponse]:
    svc = AdmissionsService(db)
    req = await svc.create_document_requirement(tenant_ctx.tenant_id, payload, current_user.id)
    return ApiResponse(data=ApplicationDocumentRequirementResponse.model_validate(req))


@router.get(
    "/document-requirements",
    response_model=ApiResponse[list[ApplicationDocumentRequirementResponse]],
    dependencies=[Depends(require_permission(ADMISSIONS_APPLICATION_READ))],
)
async def list_document_requirements(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    cycle_id: UUID | None = Query(None),
    program_id: UUID | None = Query(None),
) -> ApiResponse[list[ApplicationDocumentRequirementResponse]]:
    svc = AdmissionsService(db)
    reqs = await svc.list_document_requirements(
        tenant_ctx.tenant_id, cycle_id=cycle_id, program_id=program_id
    )
    return ApiResponse(data=[ApplicationDocumentRequirementResponse.model_validate(r) for r in reqs])


@router.post(
    "/applications/{application_id}/documents",
    response_model=ApiResponse[ApplicationDocumentResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(ADMISSIONS_APPLICATION_MANAGE))],
)
async def upload_application_document(
    application_id: UUID,
    payload: ApplicationDocumentUpload,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[ApplicationDocumentResponse]:
    svc = AdmissionsService(db)
    doc = await svc.upload_document(tenant_ctx.tenant_id, application_id, payload, current_user.id)
    return ApiResponse(data=ApplicationDocumentResponse.model_validate(doc))


@router.post(
    "/documents/{document_id}/verify",
    response_model=ApiResponse[ApplicationDocumentResponse],
    dependencies=[Depends(require_permission(ADMISSIONS_DOCUMENT_VERIFY))],
)
async def verify_application_document(
    document_id: UUID,
    payload: ApplicationDocumentVerify,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[ApplicationDocumentResponse]:
    svc = AdmissionsService(db)
    doc = await svc.verify_document(tenant_ctx.tenant_id, document_id, payload, current_user.id)
    return ApiResponse(data=ApplicationDocumentResponse.model_validate(doc))


# =============================================================================
# 5. ELIGIBILITY RULES & EVALUATION
# =============================================================================


@router.post(
    "/eligibility-rules",
    response_model=ApiResponse[EligibilityRuleResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(ADMISSIONS_ELIGIBILITY_EVALUATE))],
)
async def create_eligibility_rule(
    payload: EligibilityRuleCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[EligibilityRuleResponse]:
    svc = AdmissionsService(db)
    rule = await svc.create_eligibility_rule(tenant_ctx.tenant_id, payload, current_user.id)
    return ApiResponse(data=EligibilityRuleResponse.model_validate(rule))


@router.get(
    "/eligibility-rules",
    response_model=ApiResponse[list[EligibilityRuleResponse]],
    dependencies=[Depends(require_permission(ADMISSIONS_ELIGIBILITY_EVALUATE))],
)
async def list_eligibility_rules(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    cycle_id: UUID | None = Query(None),
    program_id: UUID | None = Query(None),
) -> ApiResponse[list[EligibilityRuleResponse]]:
    svc = AdmissionsService(db)
    rules = await svc.list_eligibility_rules(
        tenant_ctx.tenant_id, cycle_id=cycle_id, program_id=program_id
    )
    return ApiResponse(data=[EligibilityRuleResponse.model_validate(r) for r in rules])


@router.patch(
    "/eligibility-rules/{rule_id}",
    response_model=ApiResponse[EligibilityRuleResponse],
    dependencies=[Depends(require_permission(ADMISSIONS_ELIGIBILITY_EVALUATE))],
)
async def update_eligibility_rule(
    rule_id: UUID,
    payload: EligibilityRuleUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[EligibilityRuleResponse]:
    svc = AdmissionsService(db)
    rule = await svc.update_eligibility_rule(tenant_ctx.tenant_id, rule_id, payload, current_user.id)
    return ApiResponse(data=EligibilityRuleResponse.model_validate(rule))


@router.post(
    "/applications/{application_id}/evaluate-eligibility",
    response_model=ApiResponse[EligibilityEvaluationResponse],
    dependencies=[Depends(require_permission(ADMISSIONS_ELIGIBILITY_EVALUATE))],
)
async def evaluate_eligibility(
    application_id: UUID,
    payload: EligibilityEvaluationRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[EligibilityEvaluationResponse]:
    svc = AdmissionsService(db)
    eval_res = await svc.evaluate_eligibility(
        tenant_ctx.tenant_id, application_id, payload.rule_id, current_user.id
    )
    return ApiResponse(data=EligibilityEvaluationResponse.model_validate(eval_res))


@router.post(
    "/applications/{application_id}/reviews",
    response_model=ApiResponse[ApplicationReviewResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(ADMISSIONS_REVIEW_MANAGE))],
)
async def create_application_review(
    application_id: UUID,
    payload: ApplicationReviewCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[ApplicationReviewResponse]:
    svc = AdmissionsService(db)
    review = await svc.create_application_review(
        tenant_ctx.tenant_id, application_id, payload, current_user.id
    )
    return ApiResponse(data=ApplicationReviewResponse.model_validate(review))


# =============================================================================
# 6. SEAT ALLOCATION & SELECTION RUNS
# =============================================================================


@router.post(
    "/seat-allocations",
    response_model=ApiResponse[SeatAllocationResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(ADMISSIONS_SELECTION_MANAGE))],
)
async def create_seat_allocation(
    payload: SeatAllocationCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[SeatAllocationResponse]:
    svc = AdmissionsService(db)
    alloc = await svc.create_seat_allocation(tenant_ctx.tenant_id, payload, current_user.id)
    resp = SeatAllocationResponse.model_validate(alloc)
    resp.available_seats = max(0, alloc.total_capacity - alloc.reserved_seats - alloc.confirmed_seats)
    return ApiResponse(data=resp)


@router.get(
    "/seat-allocations",
    response_model=ApiResponse[SeatAllocationResponse],
    dependencies=[Depends(require_permission(ADMISSIONS_SELECTION_MANAGE))],
)
async def get_seat_allocation(
    cycle_id: UUID,
    program_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    campus_id: UUID | None = Query(None),
    admission_category: str = Query("GENERAL"),
) -> ApiResponse[SeatAllocationResponse]:
    svc = AdmissionsService(db)
    alloc = await svc.get_seat_allocation(
        tenant_ctx.tenant_id, cycle_id, program_id, campus_id, admission_category
    )
    resp = SeatAllocationResponse.model_validate(alloc)
    resp.available_seats = max(0, alloc.total_capacity - alloc.reserved_seats - alloc.confirmed_seats)
    return ApiResponse(data=resp)


@router.patch(
    "/seat-allocations/{allocation_id}",
    response_model=ApiResponse[SeatAllocationResponse],
    dependencies=[Depends(require_permission(ADMISSIONS_SELECTION_MANAGE))],
)
async def update_seat_allocation(
    allocation_id: UUID,
    payload: SeatAllocationUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[SeatAllocationResponse]:
    svc = AdmissionsService(db)
    alloc = await svc.update_seat_allocation(
        tenant_ctx.tenant_id, allocation_id, payload, current_user.id
    )
    resp = SeatAllocationResponse.model_validate(alloc)
    resp.available_seats = max(0, alloc.total_capacity - alloc.reserved_seats - alloc.confirmed_seats)
    return ApiResponse(data=resp)


@router.post(
    "/selection-runs",
    response_model=ApiResponse[SelectionRunResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(ADMISSIONS_SELECTION_MANAGE))],
)
async def create_selection_run(
    payload: SelectionRunCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[SelectionRunResponse]:
    svc = AdmissionsService(db)
    run = await svc.create_selection_run(tenant_ctx.tenant_id, payload, current_user.id)
    return ApiResponse(data=SelectionRunResponse.model_validate(run))


@router.post(
    "/selection-runs/{run_id}/publish",
    response_model=ApiResponse[SelectionRunResponse],
    dependencies=[Depends(require_permission(ADMISSIONS_SELECTION_MANAGE))],
)
async def publish_selection_run(
    run_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[SelectionRunResponse]:
    svc = AdmissionsService(db)
    run = await svc.approve_and_publish_selection(tenant_ctx.tenant_id, run_id, current_user.id)
    return ApiResponse(data=SelectionRunResponse.model_validate(run))


# =============================================================================
# 7. ADMISSION OFFERS
# =============================================================================


@router.post(
    "/offers",
    response_model=ApiResponse[AdmissionOfferResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(ADMISSIONS_OFFERS_MANAGE))],
)
async def issue_admission_offer(
    payload: AdmissionOfferCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AdmissionOfferResponse]:
    svc = AdmissionsService(db)
    offer = await svc.issue_admission_offer(tenant_ctx.tenant_id, payload, current_user.id)
    return ApiResponse(data=AdmissionOfferResponse.model_validate(offer))


@router.post(
    "/offers/{offer_id}/respond",
    response_model=ApiResponse[AdmissionOfferResponse],
    dependencies=[Depends(require_permission(ADMISSIONS_OFFERS_MANAGE))],
)
async def respond_to_offer(
    offer_id: UUID,
    payload: AdmissionOfferRespond,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AdmissionOfferResponse]:
    svc = AdmissionsService(db)
    offer = await svc.respond_to_offer(
        tenant_ctx.tenant_id, offer_id, payload.accept, payload.decline_reason, current_user.id
    )
    return ApiResponse(data=AdmissionOfferResponse.model_validate(offer))


@router.post(
    "/offers/{offer_id}/revoke",
    response_model=ApiResponse[AdmissionOfferResponse],
    dependencies=[Depends(require_permission(ADMISSIONS_OFFERS_MANAGE))],
)
async def revoke_offer(
    offer_id: UUID,
    payload: AdmissionOfferRevoke,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AdmissionOfferResponse]:
    svc = AdmissionsService(db)
    offer = await svc.revoke_offer(tenant_ctx.tenant_id, offer_id, payload.revocation_reason, current_user.id)
    return ApiResponse(data=AdmissionOfferResponse.model_validate(offer))


# =============================================================================
# 8. ENROLLMENT ORCHESTRATION
# =============================================================================


@router.post(
    "/enrollment/orchestrate",
    response_model=ApiResponse[EnrollmentWorkflowResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(ADMISSIONS_ENROLLMENT_ORCHESTRATE))],
)
async def orchestrate_enrollment(
    payload: EnrollmentWorkflowInitiate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[EnrollmentWorkflowResponse]:
    svc = AdmissionsService(db)
    workflow = await svc.orchestrate_enrollment(tenant_ctx.tenant_id, payload, current_user.id)
    return ApiResponse(data=EnrollmentWorkflowResponse.model_validate(workflow))


# =============================================================================
# 9. ONBOARDING
# =============================================================================


@router.get(
    "/onboarding/students/{student_id}",
    response_model=ApiResponse[OnboardingChecklistResponse],
    dependencies=[Depends(require_permission(ADMISSIONS_ONBOARDING_MANAGE))],
)
async def get_student_onboarding_checklist(
    student_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[OnboardingChecklistResponse]:
    svc = AdmissionsService(db)
    chk = await svc.get_student_onboarding(tenant_ctx.tenant_id, student_id)
    return ApiResponse(data=OnboardingChecklistResponse.model_validate(chk))


@router.patch(
    "/onboarding/tasks/{task_id}",
    response_model=ApiResponse[OnboardingTaskResponse],
    dependencies=[Depends(require_permission(ADMISSIONS_ONBOARDING_MANAGE))],
)
async def update_onboarding_task(
    task_id: UUID,
    payload: OnboardingTaskUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[OnboardingTaskResponse]:
    svc = AdmissionsService(db)
    task = await svc.update_onboarding_task(tenant_ctx.tenant_id, task_id, payload, current_user.id)
    return ApiResponse(data=OnboardingTaskResponse.model_validate(task))


# =============================================================================
# 10. AGGREGATE ANALYTICS
# =============================================================================


@router.get(
    "/analytics",
    response_model=ApiResponse[AdmissionsAnalyticsResponse],
    dependencies=[Depends(require_permission(ADMISSIONS_REPORTS_READ))],
)
async def get_admissions_analytics(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AdmissionsAnalyticsResponse]:
    svc = AdmissionsService(db)
    analytics = await svc.get_admissions_analytics(tenant_ctx.tenant_id)
    return ApiResponse(data=AdmissionsAnalyticsResponse.model_validate(analytics))
