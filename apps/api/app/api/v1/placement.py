"""Placement and Career Engine API Endpoints.

Provides REST interfaces for corporate partners, recruitment drives,
job positions, automated eligibility checks, applications, interviews,
offer management, and institutional placement analytics.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_current_active_user, get_tenant_context, require_permission
from app.core.exceptions import NotFoundException, PermissionDeniedException, ValidationException
from app.core.permissions import (
    PLACEMENT_ANALYTICS_READ,
    PLACEMENT_APPLICATIONS_READ,
    PLACEMENT_APPLICATIONS_REVIEW,
    PLACEMENT_APPLY_SELF,
    PLACEMENT_COMPANIES_MANAGE,
    PLACEMENT_COMPANIES_READ,
    PLACEMENT_DRIVES_MANAGE,
    PLACEMENT_DRIVES_READ,
    PLACEMENT_ELIGIBILITY_EVALUATE,
    PLACEMENT_INTERVIEWS_EVALUATE,
    PLACEMENT_INTERVIEWS_MANAGE,
    PLACEMENT_OFFERS_MANAGE,
    PLACEMENT_OFFERS_READ,
    PLACEMENT_OFFERS_RESPOND,
    PLACEMENT_OUTCOMES_MANAGE,
    PLACEMENT_POSITIONS_MANAGE,
    PLACEMENT_PROFILE_READ,
    PLACEMENT_PROFILE_UPDATE,
)
from app.core.tenant import TenantContext
from app.models.people import StudentProfile, User
from app.schemas.common import ApiResponse, PaginatedMeta, PaginatedResponse
from app.schemas.placement import (
    ApplicationHistoryResponse,
    ApplicationStatusUpdate,
    CompanyContactCreate,
    CompanyContactResponse,
    CompanyCreate,
    CompanyDetailResponse,
    CompanyResponse,
    CompanyUpdate,
    EligibilityEvaluationResponse,
    EligibilityRuleCreate,
    EligibilityRuleResponse,
    InterviewEvaluationCreate,
    InterviewEvaluationResponse,
    InterviewRoundCreate,
    InterviewRoundResponse,
    InterviewScheduleCreate,
    InterviewScheduleResponse,
    JobDriveCreate,
    JobDriveDetailResponse,
    JobDriveResponse,
    JobDriveUpdate,
    JobPositionCreate,
    JobPositionDetailResponse,
    JobPositionResponse,
    JobPositionUpdate,
    OfferDecisionRequest,
    PlacementAnalyticsSummary,
    PlacementApplicationCreate,
    PlacementApplicationResponse,
    PlacementOfferCreate,
    PlacementOfferResponse,
    PlacementOutcomeCreate,
    PlacementOutcomeResponse,
    StudentPlacementProfileResponse,
    StudentPlacementProfileUpdate,
)
from app.services.placement_service import PlacementService

router = APIRouter(prefix="/placement", tags=["Placement & Career Engine"])


# Helper to get student id for current user
async def _get_current_student_id(db: AsyncSession, tenant_id: UUID, user_id: UUID) -> UUID:
    student = await db.scalar(
        select(StudentProfile).where(
            StudentProfile.user_id == user_id,
            StudentProfile.tenant_id == tenant_id,
        )
    )
    if not student:
        raise NotFoundException("Student profile not found for current authenticated user.")
    return student.id


# =============================================================================
# 1. CORPORATE DIRECTORY & CONTACTS
# =============================================================================
@router.post(
    "/companies",
    response_model=ApiResponse[CompanyResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(PLACEMENT_COMPANIES_MANAGE))],
)
async def create_company(
    data: CompanyCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CompanyResponse]:
    """Register a new corporate recruiting partner."""
    company = await PlacementService.create_company(db, tenant.tenant_id, data)
    return ApiResponse(data=CompanyResponse.model_validate(company))


@router.get(
    "/companies",
    response_model=PaginatedResponse[CompanyResponse],
    dependencies=[Depends(require_permission(PLACEMENT_COMPANIES_READ))],
)
async def list_companies(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    industry: str | None = Query(None),
    tier: str | None = Query(None),
    status: str | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[CompanyResponse]:
    """List registered companies with filtering by tier and industry."""
    items, total = await PlacementService.list_companies(
        db, tenant.tenant_id, industry, tier, status, search, page, page_size
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return PaginatedResponse(
        data=[CompanyResponse.model_validate(c) for c in items],
        pagination=PaginatedMeta(
            page=page,
            page_size=page_size,
            total_records=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
    )


@router.get(
    "/companies/{company_id}",
    response_model=ApiResponse[CompanyDetailResponse],
    dependencies=[Depends(require_permission(PLACEMENT_COMPANIES_READ))],
)
async def get_company(
    company_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CompanyDetailResponse]:
    """Retrieve detailed company profile including corporate contacts."""
    company = await PlacementService.get_company(db, tenant.tenant_id, company_id)
    return ApiResponse(data=CompanyDetailResponse.model_validate(company))


@router.put(
    "/companies/{company_id}",
    response_model=ApiResponse[CompanyResponse],
    dependencies=[Depends(require_permission(PLACEMENT_COMPANIES_MANAGE))],
)
async def update_company(
    company_id: UUID,
    data: CompanyUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CompanyResponse]:
    """Update corporate profile information."""
    company = await PlacementService.update_company(db, tenant.tenant_id, company_id, data)
    return ApiResponse(data=CompanyResponse.model_validate(company))


@router.post(
    "/companies/{company_id}/contacts",
    response_model=ApiResponse[CompanyContactResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(PLACEMENT_COMPANIES_MANAGE))],
)
async def add_company_contact(
    company_id: UUID,
    data: CompanyContactCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CompanyContactResponse]:
    """Add a recruiter/HR contact to a company."""
    contact = await PlacementService.add_company_contact(db, tenant.tenant_id, company_id, data)
    return ApiResponse(data=CompanyContactResponse.model_validate(contact))


# =============================================================================
# 2. RECRUITMENT DRIVES & POSITIONS
# =============================================================================
@router.post(
    "/drives",
    response_model=ApiResponse[JobDriveResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(PLACEMENT_DRIVES_MANAGE))],
)
async def create_job_drive(
    data: JobDriveCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[JobDriveResponse]:
    """Schedule and configure a campus recruitment drive."""
    drive = await PlacementService.create_job_drive(db, tenant.tenant_id, current_user.id, data)
    return ApiResponse(data=JobDriveResponse.model_validate(drive))


@router.get(
    "/drives",
    response_model=PaginatedResponse[JobDriveResponse],
    dependencies=[Depends(require_permission(PLACEMENT_DRIVES_READ))],
)
async def list_job_drives(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    academic_year_id: UUID | None = Query(None),
    company_id: UUID | None = Query(None),
    status: str | None = Query(None),
    mode: str | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[JobDriveResponse]:
    """List recruitment drives."""
    items, total = await PlacementService.list_job_drives(
        db, tenant.tenant_id, academic_year_id, company_id, status, mode, search, page, page_size
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return PaginatedResponse(
        data=[JobDriveResponse.model_validate(d) for d in items],
        pagination=PaginatedMeta(
            page=page,
            page_size=page_size,
            total_records=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
    )


@router.get(
    "/drives/{drive_id}",
    response_model=ApiResponse[JobDriveDetailResponse],
    dependencies=[Depends(require_permission(PLACEMENT_DRIVES_READ))],
)
async def get_job_drive(
    drive_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[JobDriveDetailResponse]:
    """Retrieve full details of a recruitment drive including positions and rules."""
    drive = await PlacementService.get_job_drive(db, tenant.tenant_id, drive_id)
    return ApiResponse(data=JobDriveDetailResponse.model_validate(drive))


@router.put(
    "/drives/{drive_id}",
    response_model=ApiResponse[JobDriveResponse],
    dependencies=[Depends(require_permission(PLACEMENT_DRIVES_MANAGE))],
)
async def update_job_drive(
    drive_id: UUID,
    data: JobDriveUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[JobDriveResponse]:
    """Update drive schedule or metadata."""
    drive = await PlacementService.update_job_drive(db, tenant.tenant_id, drive_id, data)
    return ApiResponse(data=JobDriveResponse.model_validate(drive))


@router.post(
    "/drives/{drive_id}/status",
    response_model=ApiResponse[JobDriveResponse],
    dependencies=[Depends(require_permission(PLACEMENT_DRIVES_MANAGE))],
)
async def update_drive_status(
    drive_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    new_status: str = Query(...),
) -> ApiResponse[JobDriveResponse]:
    """Transition recruitment drive lifecycle status."""
    drive = await PlacementService.update_drive_status(db, tenant.tenant_id, drive_id, new_status)
    return ApiResponse(data=JobDriveResponse.model_validate(drive))


@router.post(
    "/drives/{drive_id}/positions",
    response_model=ApiResponse[JobPositionResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(PLACEMENT_POSITIONS_MANAGE))],
)
async def create_job_position(
    drive_id: UUID,
    data: JobPositionCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[JobPositionResponse]:
    """Add a job position to a recruitment drive."""
    pos = await PlacementService.create_job_position(db, tenant.tenant_id, drive_id, data)
    return ApiResponse(data=JobPositionResponse.model_validate(pos))


@router.get(
    "/positions/{position_id}",
    response_model=ApiResponse[JobPositionDetailResponse],
    dependencies=[Depends(require_permission(PLACEMENT_DRIVES_READ))],
)
async def get_job_position(
    position_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[JobPositionDetailResponse]:
    """Get position details and eligibility criteria."""
    pos = await PlacementService.get_job_position(db, tenant.tenant_id, position_id)
    return ApiResponse(data=JobPositionDetailResponse.model_validate(pos))


@router.post(
    "/positions/{position_id}/eligibility-rules",
    response_model=ApiResponse[EligibilityRuleResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(PLACEMENT_POSITIONS_MANAGE))],
)
async def add_eligibility_rule(
    position_id: UUID,
    data: EligibilityRuleCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[EligibilityRuleResponse]:
    """Configure an eligibility filter rule for a job position."""
    rule = await PlacementService.add_eligibility_rule(db, tenant.tenant_id, position_id, data)
    return ApiResponse(data=EligibilityRuleResponse.model_validate(rule))


# =============================================================================
# 3. DETERMINISTIC AUTOMATED ELIGIBILITY EVALUATION
# =============================================================================
@router.get(
    "/positions/{position_id}/my-eligibility",
    response_model=ApiResponse[EligibilityEvaluationResponse],
)
async def check_my_eligibility(
    position_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[EligibilityEvaluationResponse]:
    """Evaluate whether the logged-in student meets criteria for a position."""
    student_id = await _get_current_student_id(db, tenant.tenant_id, current_user.id)
    result = await PlacementService.evaluate_student_eligibility(
        db, tenant.tenant_id, student_id, position_id, current_user.id
    )
    return ApiResponse(data=result)


@router.post(
    "/positions/{position_id}/evaluate/{student_id}",
    response_model=ApiResponse[EligibilityEvaluationResponse],
    dependencies=[Depends(require_permission(PLACEMENT_ELIGIBILITY_EVALUATE))],
)
async def evaluate_student_eligibility(
    position_id: UUID,
    student_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[EligibilityEvaluationResponse]:
    """Placement Officer manual trigger of student eligibility evaluation."""
    result = await PlacementService.evaluate_student_eligibility(
        db, tenant.tenant_id, student_id, position_id, current_user.id
    )
    return ApiResponse(data=result)


# =============================================================================
# 4. STUDENT PLACEMENT PROFILE
# =============================================================================
@router.get(
    "/profile/me",
    response_model=ApiResponse[StudentPlacementProfileResponse],
)
async def get_my_placement_profile(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[StudentPlacementProfileResponse]:
    """Retrieve logged-in student's career placement profile."""
    student_id = await _get_current_student_id(db, tenant.tenant_id, current_user.id)
    profile = await PlacementService.get_or_create_student_placement_profile(
        db, tenant.tenant_id, student_id
    )
    return ApiResponse(data=StudentPlacementProfileResponse.model_validate(profile))


@router.put(
    "/profile/me",
    response_model=ApiResponse[StudentPlacementProfileResponse],
)
async def update_my_placement_profile(
    data: StudentPlacementProfileUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[StudentPlacementProfileResponse]:
    """Update career objective, skills, preferred roles, and resume link."""
    student_id = await _get_current_student_id(db, tenant.tenant_id, current_user.id)
    profile = await PlacementService.update_student_placement_profile(
        db, tenant.tenant_id, student_id, data
    )
    return ApiResponse(data=StudentPlacementProfileResponse.model_validate(profile))


@router.get(
    "/students/{student_id}/profile",
    response_model=ApiResponse[StudentPlacementProfileResponse],
    dependencies=[Depends(require_permission(PLACEMENT_APPLICATIONS_REVIEW))],
)
async def get_student_placement_profile(
    student_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[StudentPlacementProfileResponse]:
    """Placement Officer view of a candidate's placement profile."""
    profile = await PlacementService.get_or_create_student_placement_profile(
        db, tenant.tenant_id, student_id
    )
    return ApiResponse(data=StudentPlacementProfileResponse.model_validate(profile))


# =============================================================================
# 5. PLACEMENT APPLICATIONS
# =============================================================================
@router.post(
    "/applications",
    response_model=ApiResponse[PlacementApplicationResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(PLACEMENT_APPLY_SELF))],
)
async def apply_for_position(
    data: PlacementApplicationCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[PlacementApplicationResponse]:
    """Submit a formal application for an open recruitment position."""
    student_id = await _get_current_student_id(db, tenant.tenant_id, current_user.id)
    app = await PlacementService.apply_for_position(db, tenant.tenant_id, student_id, data)
    return ApiResponse(data=PlacementApplicationResponse.model_validate(app))


@router.get(
    "/applications/me",
    response_model=PaginatedResponse[PlacementApplicationResponse],
)
async def list_my_applications(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[PlacementApplicationResponse]:
    """List applications submitted by the logged-in student."""
    student_id = await _get_current_student_id(db, tenant.tenant_id, current_user.id)
    items, total = await PlacementService.list_applications(
        db, tenant.tenant_id, None, student_id, status, page, page_size
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return PaginatedResponse(
        data=[PlacementApplicationResponse.model_validate(a) for a in items],
        pagination=PaginatedMeta(
            page=page,
            page_size=page_size,
            total_records=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
    )


@router.get(
    "/applications",
    response_model=PaginatedResponse[PlacementApplicationResponse],
    dependencies=[Depends(require_permission(PLACEMENT_APPLICATIONS_REVIEW))],
)
async def list_applications(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    position_id: UUID | None = Query(None),
    student_id: UUID | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[PlacementApplicationResponse]:
    """Officer listing of applications with status filter."""
    items, total = await PlacementService.list_applications(
        db, tenant.tenant_id, position_id, student_id, status, page, page_size
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return PaginatedResponse(
        data=[PlacementApplicationResponse.model_validate(a) for a in items],
        pagination=PaginatedMeta(
            page=page,
            page_size=page_size,
            total_records=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
    )


@router.post(
    "/applications/{application_id}/status",
    response_model=ApiResponse[PlacementApplicationResponse],
    dependencies=[Depends(require_permission(PLACEMENT_APPLICATIONS_REVIEW))],
)
async def update_application_status(
    application_id: UUID,
    data: ApplicationStatusUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[PlacementApplicationResponse]:
    """Update application progression status (e.g. SHORTLISTED, SELECTED, REJECTED)."""
    app = await PlacementService.update_application_status(
        db, tenant.tenant_id, application_id, data, current_user.id
    )
    return ApiResponse(data=PlacementApplicationResponse.model_validate(app))


# =============================================================================
# 6. INTERVIEW PIPELINE & EVALUATIONS
# =============================================================================
@router.post(
    "/positions/{position_id}/interview-rounds",
    response_model=ApiResponse[InterviewRoundResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(PLACEMENT_INTERVIEWS_MANAGE))],
)
async def create_interview_round(
    position_id: UUID,
    data: InterviewRoundCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[InterviewRoundResponse]:
    """Create an assessment or interview round in the recruitment pipeline."""
    round_obj = await PlacementService.create_interview_round(
        db, tenant.tenant_id, position_id, data
    )
    return ApiResponse(data=InterviewRoundResponse.model_validate(round_obj))


@router.post(
    "/interviews/schedule",
    response_model=ApiResponse[InterviewScheduleResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(PLACEMENT_INTERVIEWS_MANAGE))],
)
async def schedule_interview(
    data: InterviewScheduleCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[InterviewScheduleResponse]:
    """Schedule an interview slot for an applicant."""
    schedule = await PlacementService.schedule_interview(db, tenant.tenant_id, data)
    return ApiResponse(data=InterviewScheduleResponse.model_validate(schedule))


@router.post(
    "/interviews/{schedule_id}/evaluate",
    response_model=ApiResponse[InterviewEvaluationResponse],
    dependencies=[Depends(require_permission(PLACEMENT_INTERVIEWS_EVALUATE))],
)
async def evaluate_interview(
    schedule_id: UUID,
    data: InterviewEvaluationCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[InterviewEvaluationResponse]:
    """Record scores, hiring recommendation, and feedback for an interview."""
    evaluation = await PlacementService.evaluate_interview(
        db, tenant.tenant_id, schedule_id, current_user.id, data
    )
    return ApiResponse(data=InterviewEvaluationResponse.model_validate(evaluation))


# =============================================================================
# 7. PLACEMENT OFFERS
# =============================================================================
@router.post(
    "/offers",
    response_model=ApiResponse[PlacementOfferResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(PLACEMENT_OFFERS_MANAGE))],
)
async def issue_placement_offer(
    data: PlacementOfferCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[PlacementOfferResponse]:
    """Issue a formal job offer to a selected candidate."""
    offer = await PlacementService.issue_placement_offer(db, tenant.tenant_id, data)
    return ApiResponse(data=PlacementOfferResponse.model_validate(offer))


@router.get(
    "/offers",
    response_model=PaginatedResponse[PlacementOfferResponse],
    dependencies=[Depends(require_permission(PLACEMENT_OFFERS_READ))],
)
async def list_offers(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    student_id: UUID | None = Query(None),
    company_id: UUID | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[PlacementOfferResponse]:
    """List issued employment offers."""
    items, total = await PlacementService.list_offers(
        db, tenant.tenant_id, student_id, company_id, status, page, page_size
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return PaginatedResponse(
        data=[PlacementOfferResponse.model_validate(o) for o in items],
        pagination=PaginatedMeta(
            page=page,
            page_size=page_size,
            total_records=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
    )


@router.get(
    "/offers/me",
    response_model=PaginatedResponse[PlacementOfferResponse],
)
async def list_my_offers(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResponse[PlacementOfferResponse]:
    """List offers issued to the current student."""
    student_id = await _get_current_student_id(db, tenant.tenant_id, current_user.id)
    items, total = await PlacementService.list_offers(
        db, tenant.tenant_id, student_id, None, status, page, page_size
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return PaginatedResponse(
        data=[PlacementOfferResponse.model_validate(o) for o in items],
        pagination=PaginatedMeta(
            page=page,
            page_size=page_size,
            total_records=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
    )


@router.post(
    "/offers/{offer_id}/respond",
    response_model=ApiResponse[PlacementOfferResponse],
    dependencies=[Depends(require_permission(PLACEMENT_OFFERS_RESPOND))],
)
async def respond_to_offer(
    offer_id: UUID,
    data: OfferDecisionRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[PlacementOfferResponse]:
    """Candidate formal acceptance or decline of an employment offer."""
    student_id = await _get_current_student_id(db, tenant.tenant_id, current_user.id)
    offer = await PlacementService.respond_to_offer(
        db, tenant.tenant_id, student_id, offer_id, data
    )
    return ApiResponse(data=PlacementOfferResponse.model_validate(offer))


# =============================================================================
# 8. OUTCOMES & INSTITUTIONAL ANALYTICS
# =============================================================================
@router.post(
    "/outcomes",
    response_model=ApiResponse[PlacementOutcomeResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(PLACEMENT_OUTCOMES_MANAGE))],
)
async def record_placement_outcome(
    data: PlacementOutcomeCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[PlacementOutcomeResponse]:
    """Record an official institutional placement milestone."""
    outcome = await PlacementService.record_placement_outcome(
        db, tenant.tenant_id, data, current_user.id
    )
    return ApiResponse(data=PlacementOutcomeResponse.model_validate(outcome))


@router.get(
    "/analytics",
    response_model=ApiResponse[PlacementAnalyticsSummary],
    dependencies=[Depends(require_permission(PLACEMENT_ANALYTICS_READ))],
)
async def get_placement_analytics(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    academic_year_id: UUID | None = Query(None),
) -> ApiResponse[PlacementAnalyticsSummary]:
    """Retrieve institutional placement metrics, CTC distributions, and recruitment summary."""
    stats = await PlacementService.get_placement_analytics(
        db, tenant.tenant_id, academic_year_id
    )
    return ApiResponse(data=stats)
