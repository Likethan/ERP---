"""CampusOS Enterprise International Relations, Student Exchange & Global Mobility API Router (Step 60).

CampusOS Tagline: "One Campus. One System. One Source of Truth."
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_current_user, get_tenant_context, require_permission
from app.core.permissions import (
    CREDIT_EQUIVALENCY_EVALUATE,
    CREDIT_EQUIVALENCY_READ,
    CREDIT_TRANSFER_APPROVE,
    FACULTY_MOBILITY_MANAGE,
    FACULTY_MOBILITY_READ,
    INTL_AGREEMENT_MANAGE,
    INTL_AGREEMENT_READ,
    INTL_CONFIG_MANAGE,
    INTL_PARTNER_MANAGE,
    INTL_PARTNER_READ,
    INTL_PROGRAM_MANAGE,
    INTL_PROGRAM_READ,
    INTL_REPORT_READ,
    MOBILITY_APPLICATION_APPLY,
    MOBILITY_APPLICATION_NOMINATE,
    MOBILITY_APPLICATION_READ,
    MOBILITY_APPLICATION_REVIEW,
    MOBILITY_DOCUMENT_VERIFY,
    MOBILITY_FUNDING_MANAGE,
    MOBILITY_INBOUND_MANAGE,
)
from app.core.tenant import TenantContext
from app.models.international import (
    AgreementScopeType,
    AgreementStatus,
    CreditEquivalencyStatus,
    CreditTransferStatus,
    FacultyMobilityDirection,
    FacultyMobilityStatus,
    InboundStudentStatus,
    MobilityApplicationStatus,
    MobilityDocumentVerificationStatus,
    MobilityFundingStatus,
    MobilityProgramType,
    PartnerCategory,
)
from app.models.people import User
from app.schemas.international import (
    AgreementAmendmentCreate,
    AgreementAmendmentResponse,
    CourseEquivalencyCreate,
    CourseEquivalencyEvaluationRequest,
    CourseEquivalencyResponse,
    CreditTransferApprovalRequest,
    CreditTransferRequestCreate,
    CreditTransferResponse,
    FacultyMobilityApprovalRequest,
    FacultyMobilityCreate,
    FacultyMobilityResponse,
    InboundOrientationCheckinRequest,
    InboundStudentCreate,
    InboundStudentResponse,
    InstitutionalAgreementCreate,
    InstitutionalAgreementResponse,
    InstitutionalAgreementUpdate,
    InternationalDashboardMetrics,
    InternationalPartnerCreate,
    InternationalPartnerResponse,
    InternationalPartnerUpdate,
    InternationalPolicyConfigCreateOrUpdate,
    InternationalPolicyConfigResponse,
    MobilityApplicationCreate,
    MobilityApplicationResponse,
    MobilityApplicationReviewRequest,
    MobilityDocumentCreate,
    MobilityDocumentResponse,
    MobilityDocumentVerifyRequest,
    MobilityFundingApprovalRequest,
    MobilityFundingRequestCreate,
    MobilityFundingRequestResponse,
    MobilityProgramCreate,
    MobilityProgramResponse,
    MobilityProgramUpdate,
    MobilityScholarshipCreate,
    MobilityScholarshipResponse,
    PartnerDecisionRequest,
    PartnerNominationRequest,
    PreDepartureUpdateRequest,
)
from app.services.international_service import InternationalService

international_router = APIRouter(prefix="/international-relations", tags=["International Relations & Global Mobility"])


# =============================================================================
# 0. CONFIG, TELEMETRY & SWEEP
# =============================================================================


@international_router.get(
    "/config",
    response_model=InternationalPolicyConfigResponse,
)
async def get_international_config(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(INTL_CONFIG_MANAGE))],
) -> InternationalPolicyConfigResponse:
    service = InternationalService(db, tenant_ctx.tenant_id)
    config = await service.get_or_create_config()
    return InternationalPolicyConfigResponse.model_validate(config)


@international_router.put(
    "/config",
    response_model=InternationalPolicyConfigResponse,
)
async def update_international_config(
    data: InternationalPolicyConfigCreateOrUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(INTL_CONFIG_MANAGE))],
) -> InternationalPolicyConfigResponse:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.update_config(data)


@international_router.get(
    "/metrics",
    response_model=InternationalDashboardMetrics,
)
async def get_dashboard_metrics(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(INTL_REPORT_READ))],
) -> InternationalDashboardMetrics:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.get_dashboard_metrics()


@international_router.post(
    "/sweep",
)
async def sweep_agreements_and_deadlines(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(INTL_CONFIG_MANAGE))],
) -> dict[str, int]:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.sweep_agreements_and_deadlines()


# =============================================================================
# 1. INTERNATIONAL PARTNERS
# =============================================================================


@international_router.post(
    "/partners",
    response_model=InternationalPartnerResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_partner(
    data: InternationalPartnerCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(INTL_PARTNER_MANAGE))],
) -> InternationalPartnerResponse:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.create_partner(data, current_user.id)


@international_router.get(
    "/partners",
    response_model=list[InternationalPartnerResponse],
)
async def list_partners(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(INTL_PARTNER_READ))],
    country_code: str | None = Query(None),
    category: PartnerCategory | None = Query(None),
    is_active: bool | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[InternationalPartnerResponse]:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.list_partners(
        country_code=country_code,
        category=category,
        is_active=is_active,
        search=search,
        limit=limit,
        offset=offset,
    )


@international_router.get(
    "/partners/{partner_id}",
    response_model=InternationalPartnerResponse,
)
async def get_partner(
    partner_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(INTL_PARTNER_READ))],
) -> InternationalPartnerResponse:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.get_partner(partner_id)


@international_router.put(
    "/partners/{partner_id}",
    response_model=InternationalPartnerResponse,
)
async def update_partner(
    partner_id: UUID,
    data: InternationalPartnerUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(INTL_PARTNER_MANAGE))],
) -> InternationalPartnerResponse:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.update_partner(partner_id, data)


# =============================================================================
# 2. INSTITUTIONAL AGREEMENTS & AMENDMENTS
# =============================================================================


@international_router.post(
    "/agreements",
    response_model=InstitutionalAgreementResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_agreement(
    data: InstitutionalAgreementCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(INTL_AGREEMENT_MANAGE))],
) -> InstitutionalAgreementResponse:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.create_agreement(data, current_user.id)


@international_router.get(
    "/agreements",
    response_model=list[InstitutionalAgreementResponse],
)
async def list_agreements(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(INTL_AGREEMENT_READ))],
    partner_id: UUID | None = Query(None),
    status_filter: AgreementStatus | None = Query(None, alias="status"),
    scope_type: AgreementScopeType | None = Query(None),
    expiring_soon: bool | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[InstitutionalAgreementResponse]:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.list_agreements(
        partner_id=partner_id,
        status=status_filter,
        scope_type=scope_type,
        expiring_soon=expiring_soon,
        limit=limit,
        offset=offset,
    )


@international_router.get(
    "/agreements/{agreement_id}",
    response_model=InstitutionalAgreementResponse,
)
async def get_agreement(
    agreement_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(INTL_AGREEMENT_READ))],
) -> InstitutionalAgreementResponse:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.get_agreement(agreement_id)


@international_router.put(
    "/agreements/{agreement_id}",
    response_model=InstitutionalAgreementResponse,
)
async def update_agreement(
    agreement_id: UUID,
    data: InstitutionalAgreementUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(INTL_AGREEMENT_MANAGE))],
) -> InstitutionalAgreementResponse:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.update_agreement(agreement_id, data, current_user.id)


@international_router.post(
    "/agreements/{agreement_id}/amendments",
    response_model=AgreementAmendmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_amendment(
    agreement_id: UUID,
    data: AgreementAmendmentCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(INTL_AGREEMENT_MANAGE))],
) -> AgreementAmendmentResponse:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.add_amendment(agreement_id, data, current_user.id)


@international_router.get(
    "/agreements/{agreement_id}/amendments",
    response_model=list[AgreementAmendmentResponse],
)
async def list_amendments(
    agreement_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(INTL_AGREEMENT_READ))],
) -> list[AgreementAmendmentResponse]:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.list_amendments(agreement_id)


# =============================================================================
# 3. MOBILITY PROGRAMS & APPLICATION CYCLES
# =============================================================================


@international_router.post(
    "/programs",
    response_model=MobilityProgramResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_program(
    data: MobilityProgramCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(INTL_PROGRAM_MANAGE))],
) -> MobilityProgramResponse:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.create_program(data, current_user.id)


@international_router.get(
    "/programs",
    response_model=list[MobilityProgramResponse],
)
async def list_programs(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(INTL_PROGRAM_READ))],
    is_published: bool | None = Query(None),
    program_type: MobilityProgramType | None = Query(None),
    partner_id: UUID | None = Query(None),
    department_id: UUID | None = Query(None),
    open_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[MobilityProgramResponse]:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.list_programs(
        is_published=is_published,
        program_type=program_type,
        partner_id=partner_id,
        department_id=department_id,
        open_only=open_only,
        limit=limit,
        offset=offset,
    )


@international_router.get(
    "/programs/{program_id}",
    response_model=MobilityProgramResponse,
)
async def get_program(
    program_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(INTL_PROGRAM_READ))],
) -> MobilityProgramResponse:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.get_program(program_id)


@international_router.put(
    "/programs/{program_id}",
    response_model=MobilityProgramResponse,
)
async def update_program(
    program_id: UUID,
    data: MobilityProgramUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(INTL_PROGRAM_MANAGE))],
) -> MobilityProgramResponse:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.update_program(program_id, data, current_user.id)


# =============================================================================
# 4. STUDENT MOBILITY APPLICATIONS & REVIEWS
# =============================================================================


@international_router.post(
    "/applications",
    response_model=MobilityApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_application(
    data: MobilityApplicationCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(MOBILITY_APPLICATION_APPLY))],
) -> MobilityApplicationResponse:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.create_application(data, current_user.id)


@international_router.get(
    "/applications",
    response_model=list[MobilityApplicationResponse],
)
async def list_applications(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(MOBILITY_APPLICATION_READ))],
    student_id: UUID | None = Query(None),
    program_id: UUID | None = Query(None),
    status_filter: MobilityApplicationStatus | None = Query(None, alias="status"),
    department_pending: bool = Query(False),
    intl_office_pending: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[MobilityApplicationResponse]:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.list_applications(
        student_id=student_id,
        program_id=program_id,
        status=status_filter,
        department_pending=department_pending,
        intl_office_pending=intl_office_pending,
        limit=limit,
        offset=offset,
    )


@international_router.get(
    "/applications/{application_id}",
    response_model=MobilityApplicationResponse,
)
async def get_application(
    application_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(MOBILITY_APPLICATION_READ))],
) -> MobilityApplicationResponse:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.get_application(application_id)


@international_router.post(
    "/applications/{application_id}/review",
    response_model=MobilityApplicationResponse,
)
async def review_application(
    application_id: UUID,
    data: MobilityApplicationReviewRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(MOBILITY_APPLICATION_REVIEW))],
) -> MobilityApplicationResponse:
    service = InternationalService(db, tenant_ctx.tenant_id)
    role = getattr(current_user, "role", "STAFF")
    return await service.review_application(application_id, data, current_user.id, role)


@international_router.post(
    "/applications/{application_id}/nominate",
    response_model=MobilityApplicationResponse,
)
async def nominate_to_partner(
    application_id: UUID,
    data: PartnerNominationRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(MOBILITY_APPLICATION_NOMINATE))],
) -> MobilityApplicationResponse:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.nominate_to_partner(application_id, data, current_user.id)


@international_router.post(
    "/applications/{application_id}/partner-decision",
    response_model=MobilityApplicationResponse,
)
async def record_partner_decision(
    application_id: UUID,
    data: PartnerDecisionRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(MOBILITY_APPLICATION_NOMINATE))],
) -> MobilityApplicationResponse:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.record_partner_decision(application_id, data, current_user.id)


@international_router.put(
    "/applications/{application_id}/pre-departure",
    response_model=MobilityApplicationResponse,
)
async def update_pre_departure(
    application_id: UUID,
    data: PreDepartureUpdateRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(MOBILITY_APPLICATION_APPLY))],
) -> MobilityApplicationResponse:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.update_pre_departure(application_id, data)


# =============================================================================
# 5. INBOUND INTERNATIONAL STUDENTS
# =============================================================================


@international_router.post(
    "/inbound-students",
    response_model=InboundStudentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_inbound_student(
    data: InboundStudentCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(MOBILITY_INBOUND_MANAGE))],
) -> InboundStudentResponse:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.create_inbound_student(data, current_user.id)


@international_router.get(
    "/inbound-students",
    response_model=list[InboundStudentResponse],
)
async def list_inbound_students(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(MOBILITY_INBOUND_MANAGE))],
    partner_id: UUID | None = Query(None),
    status_filter: InboundStudentStatus | None = Query(None, alias="status"),
    orientation_pending: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[InboundStudentResponse]:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.list_inbound_students(
        partner_id=partner_id,
        status=status_filter,
        orientation_pending=orientation_pending,
        limit=limit,
        offset=offset,
    )


@international_router.get(
    "/inbound-students/{inbound_id}",
    response_model=InboundStudentResponse,
)
async def get_inbound_student(
    inbound_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(MOBILITY_INBOUND_MANAGE))],
) -> InboundStudentResponse:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.get_inbound_student(inbound_id)


@international_router.post(
    "/inbound-students/{inbound_id}/checkin",
    response_model=InboundStudentResponse,
)
async def checkin_inbound_student(
    inbound_id: UUID,
    data: InboundOrientationCheckinRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(MOBILITY_INBOUND_MANAGE))],
) -> InboundStudentResponse:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.checkin_inbound_student(inbound_id, data)


# =============================================================================
# 6. FACULTY MOBILITY & VISITING SCHOLARS
# =============================================================================


@international_router.post(
    "/faculty-mobility",
    response_model=FacultyMobilityResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_faculty_mobility(
    data: FacultyMobilityCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(FACULTY_MOBILITY_MANAGE))],
) -> FacultyMobilityResponse:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.create_faculty_mobility(data, current_user.id)


@international_router.get(
    "/faculty-mobility",
    response_model=list[FacultyMobilityResponse],
)
async def list_faculty_mobilities(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(FACULTY_MOBILITY_READ))],
    direction: FacultyMobilityDirection | None = Query(None),
    partner_id: UUID | None = Query(None),
    status_filter: FacultyMobilityStatus | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[FacultyMobilityResponse]:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.list_faculty_mobilities(
        direction=direction,
        partner_id=partner_id,
        status=status_filter,
        limit=limit,
        offset=offset,
    )


@international_router.get(
    "/faculty-mobility/{mobility_id}",
    response_model=FacultyMobilityResponse,
)
async def get_faculty_mobility(
    mobility_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(FACULTY_MOBILITY_READ))],
) -> FacultyMobilityResponse:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.get_faculty_mobility(mobility_id)


@international_router.post(
    "/faculty-mobility/{mobility_id}/approve",
    response_model=FacultyMobilityResponse,
)
async def approve_faculty_mobility(
    mobility_id: UUID,
    data: FacultyMobilityApprovalRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(FACULTY_MOBILITY_MANAGE))],
) -> FacultyMobilityResponse:
    service = InternationalService(db, tenant_ctx.tenant_id)
    role = getattr(current_user, "role", "ADMIN")
    return await service.approve_faculty_mobility(mobility_id, data, current_user.id, role)


# =============================================================================
# 7. ACADEMIC CREDIT EQUIVALENCY & TRANSFERS
# =============================================================================


@international_router.post(
    "/course-equivalencies",
    response_model=CourseEquivalencyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_course_equivalency(
    data: CourseEquivalencyCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(CREDIT_EQUIVALENCY_EVALUATE))],
) -> CourseEquivalencyResponse:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.create_course_equivalency(data, current_user.id)


@international_router.get(
    "/course-equivalencies",
    response_model=list[CourseEquivalencyResponse],
)
async def list_course_equivalencies(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(CREDIT_EQUIVALENCY_READ))],
    partner_id: UUID | None = Query(None),
    department_id: UUID | None = Query(None),
    status_filter: CreditEquivalencyStatus | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[CourseEquivalencyResponse]:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.list_course_equivalencies(
        partner_id=partner_id,
        department_id=department_id,
        status=status_filter,
        limit=limit,
        offset=offset,
    )


@international_router.post(
    "/course-equivalencies/{mapping_id}/evaluate",
    response_model=CourseEquivalencyResponse,
)
async def evaluate_course_equivalency(
    mapping_id: UUID,
    data: CourseEquivalencyEvaluationRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(CREDIT_EQUIVALENCY_EVALUATE))],
) -> CourseEquivalencyResponse:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.evaluate_course_equivalency(mapping_id, data, current_user.id)


@international_router.post(
    "/credit-transfers",
    response_model=CreditTransferResponse,
    status_code=status.HTTP_201_CREATED,
)
async def request_credit_transfer(
    data: CreditTransferRequestCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(MOBILITY_APPLICATION_APPLY))],
) -> CreditTransferResponse:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.request_credit_transfer(data, current_user.id)


@international_router.get(
    "/credit-transfers",
    response_model=list[CreditTransferResponse],
)
async def list_credit_transfers(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(CREDIT_EQUIVALENCY_READ))],
    student_id: UUID | None = Query(None),
    application_id: UUID | None = Query(None),
    status_filter: CreditTransferStatus | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[CreditTransferResponse]:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.list_credit_transfers(
        student_id=student_id,
        application_id=application_id,
        status=status_filter,
        limit=limit,
        offset=offset,
    )


@international_router.post(
    "/credit-transfers/{transfer_id}/review",
    response_model=CreditTransferResponse,
)
async def review_credit_transfer(
    transfer_id: UUID,
    data: CreditTransferApprovalRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(CREDIT_TRANSFER_APPROVE))],
) -> CreditTransferResponse:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.review_credit_transfer(transfer_id, data, current_user.id)


# =============================================================================
# 8. MOBILITY DOCUMENTS
# =============================================================================


@international_router.post(
    "/documents",
    response_model=MobilityDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_document(
    data: MobilityDocumentCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> MobilityDocumentResponse:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.create_document(data, current_user.id)


@international_router.get(
    "/documents",
    response_model=list[MobilityDocumentResponse],
)
async def list_documents(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(MOBILITY_DOCUMENT_VERIFY))],
    application_id: UUID | None = Query(None),
    inbound_student_id: UUID | None = Query(None),
    faculty_mobility_id: UUID | None = Query(None),
    status_filter: MobilityDocumentVerificationStatus | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[MobilityDocumentResponse]:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.list_documents(
        application_id=application_id,
        inbound_student_id=inbound_student_id,
        faculty_mobility_id=faculty_mobility_id,
        verification_status=status_filter,
        limit=limit,
        offset=offset,
    )


@international_router.post(
    "/documents/{document_id}/verify",
    response_model=MobilityDocumentResponse,
)
async def verify_document(
    document_id: UUID,
    data: MobilityDocumentVerifyRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(MOBILITY_DOCUMENT_VERIFY))],
) -> MobilityDocumentResponse:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.verify_document(document_id, data, current_user.id)


# =============================================================================
# 9. SCHOLARSHIPS & MOBILITY FUNDING
# =============================================================================


@international_router.post(
    "/scholarships",
    response_model=MobilityScholarshipResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_scholarship(
    data: MobilityScholarshipCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(MOBILITY_FUNDING_MANAGE))],
) -> MobilityScholarshipResponse:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.create_scholarship(data, current_user.id)


@international_router.get(
    "/scholarships",
    response_model=list[MobilityScholarshipResponse],
)
async def list_scholarships(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(MOBILITY_FUNDING_MANAGE))],
    is_active: bool | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[MobilityScholarshipResponse]:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.list_scholarships(is_active=is_active, limit=limit, offset=offset)


@international_router.post(
    "/funding-requests",
    response_model=MobilityFundingRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_funding_request(
    data: MobilityFundingRequestCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(MOBILITY_APPLICATION_APPLY))],
) -> MobilityFundingRequestResponse:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.create_funding_request(data, current_user.id)


@international_router.get(
    "/funding-requests",
    response_model=list[MobilityFundingRequestResponse],
)
async def list_funding_requests(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(MOBILITY_FUNDING_MANAGE))],
    application_id: UUID | None = Query(None),
    status_filter: MobilityFundingStatus | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[MobilityFundingRequestResponse]:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.list_funding_requests(
        application_id=application_id, status=status_filter, limit=limit, offset=offset
    )


@international_router.post(
    "/funding-requests/{request_id}/approve",
    response_model=MobilityFundingRequestResponse,
)
async def approve_funding_request(
    request_id: UUID,
    data: MobilityFundingApprovalRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(MOBILITY_FUNDING_MANAGE))],
) -> MobilityFundingRequestResponse:
    service = InternationalService(db, tenant_ctx.tenant_id)
    return await service.approve_funding_request(request_id, data, current_user.id)
