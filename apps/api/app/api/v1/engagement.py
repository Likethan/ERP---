"""Enterprise Student Engagement, Community Service, Volunteering & Civic Impact Management API Router (Step 65).

CampusOS Principle: "One Campus. One System. One Source of Truth."
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_tenant_context, require_permission
from app.core.exceptions import NotFoundException
from app.core.permissions import (
    ENGAGEMENT_ANALYTICS_READ,
    ENGAGEMENT_APPLICATIONS_APPLY,
    ENGAGEMENT_APPLICATIONS_MANAGE,
    ENGAGEMENT_APPLICATIONS_READ,
    ENGAGEMENT_ATTENDANCE_RECORD,
    ENGAGEMENT_CERTIFICATES_ISSUE,
    ENGAGEMENT_CERTIFICATES_REVOKE,
    ENGAGEMENT_HOURS_SUBMIT,
    ENGAGEMENT_HOURS_VERIFY,
    ENGAGEMENT_OPPORTUNITIES_MANAGE,
    ENGAGEMENT_OPPORTUNITIES_READ,
    ENGAGEMENT_PARTNERS_MANAGE,
    ENGAGEMENT_PARTNERS_READ,
    ENGAGEMENT_PROGRAMS_APPROVE,
    ENGAGEMENT_PROGRAMS_MANAGE,
    ENGAGEMENT_PROGRAMS_READ,
    ENGAGEMENT_REFLECTIONS_REVIEW,
    ENGAGEMENT_REFLECTIONS_SUBMIT,
    ENGAGEMENT_SAFETY_MANAGE,
)
from app.core.tenant import TenantContext
from app.models.people import StudentProfile, User
from app.schemas.engagement import (
    AttendanceCheckInRequest,
    AttendanceCheckOutRequest,
    CommunityPartnerCreate,
    CommunityPartnerResponse,
    CommunityPartnerUpdate,
    EngagementCertificateIssueRequest,
    EngagementCertificateResponse,
    EngagementCertificateRevokeRequest,
    EngagementDashboardResponse,
    EngagementProgramCreate,
    EngagementProgramResponse,
    EngagementProgramTransitionRequest,
    EngagementProgramUpdate,
    ParticipationApplicationCreate,
    ParticipationApplicationResponse,
    ParticipationApplicationReviewRequest,
    ParticipationAttendanceResponse,
    ReflectionReviewRequest,
    ReflectionSubmissionResponse,
    ReflectionSubmitRequest,
    SafetyAcknowledgeRequest,
    SafetyAndConsentResponse,
    SafetyClearanceRequest,
    ServiceHourCorrectionRequest,
    ServiceHourResponse,
    ServiceHourSubmitRequest,
    ServiceHourVerifyRequest,
    ShiftAssignmentCreate,
    ShiftAssignmentResponse,
    VolunteerOpportunityCreate,
    VolunteerOpportunityResponse,
    VolunteerShiftCreate,
    VolunteerShiftResponse,
)
from app.services.engagement_service import EngagementService

engagement_router = APIRouter(prefix="/engagement", tags=["Enterprise Student Engagement & Civic Impact"])


async def resolve_student_id_for_user(
    db: AsyncSession, tenant_id: UUID, current_user: User, explicit_student_id: UUID | None = None
) -> UUID:
    """Helper resolving student profile ID from current user or explicit parameter."""
    if explicit_student_id:
        return explicit_student_id
    student = await db.scalar(
        select(StudentProfile).where(
            StudentProfile.tenant_id == tenant_id,
            StudentProfile.user_id == current_user.id,
        )
    )
    if not student:
        raise NotFoundException(
            "Student profile associated with this account could not be found. Please contact administration."
        )
    return student.id


# =============================================================================
# 1. DASHBOARD & ANALYTICS
# =============================================================================


@engagement_router.get(
    "/dashboard",
    response_model=EngagementDashboardResponse,
    summary="Civic Engagement & Community Service Dashboard Analytics",
)
async def get_dashboard_analytics(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ENGAGEMENT_ANALYTICS_READ))],
    campus_id: UUID | None = Query(None, description="Optional campus filter"),
    department_id: UUID | None = Query(None, description="Optional department filter"),
) -> EngagementDashboardResponse:
    service = EngagementService(db, tenant_ctx.tenant_id)
    return await service.get_dashboard_analytics(campus_id=campus_id, department_id=department_id)


# =============================================================================
# 2. COMMUNITY PARTNERS
# =============================================================================


@engagement_router.post(
    "/partners",
    response_model=CommunityPartnerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new community partner organization",
)
async def create_partner(
    data: CommunityPartnerCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ENGAGEMENT_PARTNERS_MANAGE))],
) -> CommunityPartnerResponse:
    service = EngagementService(db, tenant_ctx.tenant_id)
    return await service.create_partner(data, current_user.id)


@engagement_router.get(
    "/partners",
    response_model=list[CommunityPartnerResponse],
    summary="List community partners with status and search filters",
)
async def list_partners(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ENGAGEMENT_PARTNERS_READ))],
    partner_status: str | None = Query(None, alias="status"),
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[CommunityPartnerResponse]:
    service = EngagementService(db, tenant_ctx.tenant_id)
    return await service.list_partners(status=partner_status, search=search, limit=limit, offset=offset)


@engagement_router.get(
    "/partners/{partner_id}",
    response_model=CommunityPartnerResponse,
    summary="Get community partner details",
)
async def get_partner(
    partner_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ENGAGEMENT_PARTNERS_READ))],
) -> CommunityPartnerResponse:
    service = EngagementService(db, tenant_ctx.tenant_id)
    return await service.get_partner(partner_id)


@engagement_router.patch(
    "/partners/{partner_id}",
    response_model=CommunityPartnerResponse,
    summary="Update community partner record",
)
async def update_partner(
    partner_id: UUID,
    data: CommunityPartnerUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ENGAGEMENT_PARTNERS_MANAGE))],
) -> CommunityPartnerResponse:
    service = EngagementService(db, tenant_ctx.tenant_id)
    return await service.update_partner(partner_id, data)


# =============================================================================
# 3. ENGAGEMENT PROGRAMS
# =============================================================================


@engagement_router.post(
    "/programs",
    response_model=EngagementProgramResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new community engagement program draft",
)
async def create_program(
    data: EngagementProgramCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ENGAGEMENT_PROGRAMS_MANAGE))],
) -> EngagementProgramResponse:
    service = EngagementService(db, tenant_ctx.tenant_id)
    return await service.create_program(data, current_user.id)


@engagement_router.get(
    "/programs",
    response_model=list[EngagementProgramResponse],
    summary="List engagement programs with filtering",
)
async def list_programs(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ENGAGEMENT_PROGRAMS_READ))],
    category: str | None = Query(None),
    program_status: str | None = Query(None, alias="status"),
    department_id: UUID | None = Query(None),
    campus_id: UUID | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[EngagementProgramResponse]:
    service = EngagementService(db, tenant_ctx.tenant_id)
    return await service.list_programs(
        category=category,
        status=program_status,
        department_id=department_id,
        campus_id=campus_id,
        search=search,
        limit=limit,
        offset=offset,
    )


@engagement_router.get(
    "/programs/{program_id}",
    response_model=EngagementProgramResponse,
    summary="Get engagement program details",
)
async def get_program(
    program_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ENGAGEMENT_PROGRAMS_READ))],
) -> EngagementProgramResponse:
    service = EngagementService(db, tenant_ctx.tenant_id)
    return await service.get_program(program_id)


@engagement_router.patch(
    "/programs/{program_id}",
    response_model=EngagementProgramResponse,
    summary="Update engagement program details",
)
async def update_program(
    program_id: UUID,
    data: EngagementProgramUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ENGAGEMENT_PROGRAMS_MANAGE))],
) -> EngagementProgramResponse:
    service = EngagementService(db, tenant_ctx.tenant_id)
    return await service.update_program(program_id, data)


@engagement_router.post(
    "/programs/{program_id}/transition",
    response_model=EngagementProgramResponse,
    summary="Transition program lifecycle status (Approve, Publish, Complete, Cancel)",
)
async def transition_program_status(
    program_id: UUID,
    req: EngagementProgramTransitionRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ENGAGEMENT_PROGRAMS_APPROVE))],
) -> EngagementProgramResponse:
    service = EngagementService(db, tenant_ctx.tenant_id)
    return await service.transition_program_status(program_id, req, current_user.id)


# =============================================================================
# 4. VOLUNTEER OPPORTUNITIES
# =============================================================================


@engagement_router.post(
    "/opportunities",
    response_model=VolunteerOpportunityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new volunteering opportunity",
)
async def create_opportunity(
    data: VolunteerOpportunityCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ENGAGEMENT_OPPORTUNITIES_MANAGE))],
) -> VolunteerOpportunityResponse:
    service = EngagementService(db, tenant_ctx.tenant_id)
    return await service.create_opportunity(data, current_user.id)


@engagement_router.get(
    "/opportunities",
    response_model=list[VolunteerOpportunityResponse],
    summary="Browse and discover volunteering opportunities",
)
async def list_opportunities(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ENGAGEMENT_OPPORTUNITIES_READ))],
    program_id: UUID | None = Query(None),
    category: str | None = Query(None),
    opportunity_status: str | None = Query(None, alias="status"),
    delivery_mode: str | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[VolunteerOpportunityResponse]:
    service = EngagementService(db, tenant_ctx.tenant_id)
    return await service.list_opportunities(
        program_id=program_id,
        category=category,
        status=opportunity_status,
        delivery_mode=delivery_mode,
        search=search,
        limit=limit,
        offset=offset,
    )


@engagement_router.get(
    "/opportunities/{opportunity_id}",
    response_model=VolunteerOpportunityResponse,
    summary="Get volunteer opportunity details",
)
async def get_opportunity(
    opportunity_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ENGAGEMENT_OPPORTUNITIES_READ))],
) -> VolunteerOpportunityResponse:
    service = EngagementService(db, tenant_ctx.tenant_id)
    return await service.get_opportunity(opportunity_id)


# =============================================================================
# 5. PARTICIPATION APPLICATIONS
# =============================================================================


@engagement_router.post(
    "/applications",
    response_model=ParticipationApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Apply for a volunteering opportunity",
)
async def apply_to_opportunity(
    data: ParticipationApplicationCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ENGAGEMENT_APPLICATIONS_APPLY))],
    student_id: UUID | None = Query(None, description="Optional override for admin applications"),
) -> ParticipationApplicationResponse:
    service = EngagementService(db, tenant_ctx.tenant_id)
    resolved_student_id = await resolve_student_id_for_user(db, tenant_ctx.tenant_id, current_user, student_id)
    return await service.apply_to_opportunity(resolved_student_id, data)


@engagement_router.get(
    "/applications",
    response_model=list[ParticipationApplicationResponse],
    summary="List participation applications",
)
async def list_applications(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ENGAGEMENT_APPLICATIONS_READ))],
    opportunity_id: UUID | None = Query(None),
    program_id: UUID | None = Query(None),
    student_id: UUID | None = Query(None),
    application_status: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[ParticipationApplicationResponse]:
    service = EngagementService(db, tenant_ctx.tenant_id)
    return await service.list_applications(
        opportunity_id=opportunity_id,
        program_id=program_id,
        student_id=student_id,
        status=application_status,
        limit=limit,
        offset=offset,
    )


@engagement_router.post(
    "/applications/{application_id}/review",
    response_model=ParticipationApplicationResponse,
    summary="Coordinator review of student participation application",
)
async def review_application(
    application_id: UUID,
    req: ParticipationApplicationReviewRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ENGAGEMENT_APPLICATIONS_MANAGE))],
) -> ParticipationApplicationResponse:
    service = EngagementService(db, tenant_ctx.tenant_id)
    return await service.review_application(application_id, req, current_user.id)


@engagement_router.post(
    "/applications/{application_id}/withdraw",
    response_model=ParticipationApplicationResponse,
    summary="Withdraw participation application",
)
async def withdraw_application(
    application_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ENGAGEMENT_APPLICATIONS_APPLY))],
) -> ParticipationApplicationResponse:
    service = EngagementService(db, tenant_ctx.tenant_id)
    resolved_student_id = await resolve_student_id_for_user(db, tenant_ctx.tenant_id, current_user)
    return await service.withdraw_application(application_id, resolved_student_id)


# =============================================================================
# 6. SHIFTS & ROSTERS
# =============================================================================


@engagement_router.post(
    "/shifts",
    response_model=VolunteerShiftResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Schedule volunteer shift",
)
async def create_shift(
    data: VolunteerShiftCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ENGAGEMENT_OPPORTUNITIES_MANAGE))],
) -> VolunteerShiftResponse:
    service = EngagementService(db, tenant_ctx.tenant_id)
    return await service.create_shift(data)


@engagement_router.get(
    "/shifts",
    response_model=list[VolunteerShiftResponse],
    summary="List shifts for opportunity",
)
async def list_shifts(
    opportunity_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ENGAGEMENT_OPPORTUNITIES_READ))],
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[VolunteerShiftResponse]:
    service = EngagementService(db, tenant_ctx.tenant_id)
    return await service.list_shifts(opportunity_id=opportunity_id, limit=limit, offset=offset)


@engagement_router.post(
    "/shifts/assignments",
    response_model=ShiftAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Assign participant to a shift roster",
)
async def assign_student_to_shift(
    data: ShiftAssignmentCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ENGAGEMENT_OPPORTUNITIES_MANAGE))],
) -> ShiftAssignmentResponse:
    service = EngagementService(db, tenant_ctx.tenant_id)
    return await service.assign_student_to_shift(data)


# =============================================================================
# 7. ATTENDANCE & CHECK-IN
# =============================================================================


@engagement_router.post(
    "/attendance/check-in",
    response_model=ParticipationAttendanceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record participant session check-in",
)
async def check_in(
    req: AttendanceCheckInRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ENGAGEMENT_ATTENDANCE_RECORD))],
) -> ParticipationAttendanceResponse:
    service = EngagementService(db, tenant_ctx.tenant_id)
    return await service.check_in(req, current_user.id)


@engagement_router.post(
    "/attendance/{attendance_id}/check-out",
    response_model=ParticipationAttendanceResponse,
    summary="Record participant session check-out",
)
async def check_out(
    attendance_id: UUID,
    req: AttendanceCheckOutRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ENGAGEMENT_ATTENDANCE_RECORD))],
) -> ParticipationAttendanceResponse:
    service = EngagementService(db, tenant_ctx.tenant_id)
    return await service.check_out(attendance_id, req)


# =============================================================================
# 8. SERVICE HOURS LOGS & VERIFICATION
# =============================================================================


@engagement_router.post(
    "/service-hours",
    response_model=ServiceHourResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit service hours for verification",
)
async def submit_service_hours(
    data: ServiceHourSubmitRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ENGAGEMENT_HOURS_SUBMIT))],
    student_id: UUID | None = Query(None, description="Optional override for coordinator entry"),
) -> ServiceHourResponse:
    service = EngagementService(db, tenant_ctx.tenant_id)
    resolved_student_id = await resolve_student_id_for_user(db, tenant_ctx.tenant_id, current_user, student_id)
    return await service.submit_service_hours(resolved_student_id, data)


@engagement_router.get(
    "/service-hours",
    response_model=list[ServiceHourResponse],
    summary="List submitted and verified service hours",
)
async def list_service_hours(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ENGAGEMENT_APPLICATIONS_READ))],
    student_id: UUID | None = Query(None),
    program_id: UUID | None = Query(None),
    hour_status: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[ServiceHourResponse]:
    service = EngagementService(db, tenant_ctx.tenant_id)
    return await service.list_service_hours(
        student_id=student_id,
        program_id=program_id,
        status=hour_status,
        limit=limit,
        offset=offset,
    )


@engagement_router.post(
    "/service-hours/{service_hour_id}/verify",
    response_model=ServiceHourResponse,
    summary="Coordinator review & approval of service hours",
)
async def verify_service_hours(
    service_hour_id: UUID,
    req: ServiceHourVerifyRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ENGAGEMENT_HOURS_VERIFY))],
) -> ServiceHourResponse:
    service = EngagementService(db, tenant_ctx.tenant_id)
    return await service.verify_service_hours(service_hour_id, req, current_user.id)


@engagement_router.post(
    "/service-hours/{service_hour_id}/correct",
    response_model=ServiceHourResponse,
    summary="Correct verified hours with mandatory audit rationale",
)
async def correct_service_hours(
    service_hour_id: UUID,
    req: ServiceHourCorrectionRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ENGAGEMENT_HOURS_VERIFY))],
) -> ServiceHourResponse:
    service = EngagementService(db, tenant_ctx.tenant_id)
    return await service.correct_service_hours(service_hour_id, req, current_user.id)


# =============================================================================
# 9. REFLECTIONS & CIVIC IMPACT EVIDENCE
# =============================================================================


@engagement_router.post(
    "/reflections",
    response_model=ReflectionSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit student reflection and completion evidence",
)
async def submit_reflection(
    data: ReflectionSubmitRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ENGAGEMENT_REFLECTIONS_SUBMIT))],
    student_id: UUID | None = Query(None),
) -> ReflectionSubmissionResponse:
    service = EngagementService(db, tenant_ctx.tenant_id)
    resolved_student_id = await resolve_student_id_for_user(db, tenant_ctx.tenant_id, current_user, student_id)
    return await service.submit_reflection(resolved_student_id, data)


@engagement_router.post(
    "/reflections/{reflection_id}/review",
    response_model=ReflectionSubmissionResponse,
    summary="Review and grade student reflection submission",
)
async def review_reflection(
    reflection_id: UUID,
    req: ReflectionReviewRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ENGAGEMENT_REFLECTIONS_REVIEW))],
) -> ReflectionSubmissionResponse:
    service = EngagementService(db, tenant_ctx.tenant_id)
    return await service.review_reflection(reflection_id, req, current_user.id)


# =============================================================================
# 10. SAFETY, CONSENT & CLEARANCE
# =============================================================================


@engagement_router.post(
    "/safety/acknowledge",
    response_model=SafetyAndConsentResponse,
    summary="Student safety briefing & risk acknowledgment",
)
async def acknowledge_safety_and_consent(
    req: SafetyAcknowledgeRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ENGAGEMENT_APPLICATIONS_APPLY))],
) -> SafetyAndConsentResponse:
    service = EngagementService(db, tenant_ctx.tenant_id)
    resolved_student_id = await resolve_student_id_for_user(db, tenant_ctx.tenant_id, current_user)
    return await service.acknowledge_safety_and_consent(resolved_student_id, req)


@engagement_router.post(
    "/safety/{record_id}/clearance",
    response_model=SafetyAndConsentResponse,
    summary="Coordinator safety clearance confirmation",
)
async def set_coordinator_clearance(
    record_id: UUID,
    req: SafetyClearanceRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ENGAGEMENT_SAFETY_MANAGE))],
) -> SafetyAndConsentResponse:
    service = EngagementService(db, tenant_ctx.tenant_id)
    return await service.set_coordinator_clearance(record_id, req, current_user.id)


# =============================================================================
# 11. CO-CURRICULAR CERTIFICATES
# =============================================================================


@engagement_router.post(
    "/certificates",
    response_model=EngagementCertificateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Issue verifiable civic engagement certificate",
)
async def issue_certificate(
    req: EngagementCertificateIssueRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ENGAGEMENT_CERTIFICATES_ISSUE))],
) -> EngagementCertificateResponse:
    service = EngagementService(db, tenant_ctx.tenant_id)
    return await service.issue_certificate(req, current_user.id)


@engagement_router.get(
    "/certificates",
    response_model=list[EngagementCertificateResponse],
    summary="List issued engagement certificates",
)
async def list_certificates(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ENGAGEMENT_APPLICATIONS_READ))],
    student_id: UUID | None = Query(None),
    program_id: UUID | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[EngagementCertificateResponse]:
    service = EngagementService(db, tenant_ctx.tenant_id)
    return await service.list_certificates(
        student_id=student_id, program_id=program_id, limit=limit, offset=offset
    )


@engagement_router.post(
    "/certificates/{certificate_id}/revoke",
    response_model=EngagementCertificateResponse,
    summary="Revoke an engagement certificate",
)
async def revoke_certificate(
    certificate_id: UUID,
    req: EngagementCertificateRevokeRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(ENGAGEMENT_CERTIFICATES_REVOKE))],
) -> EngagementCertificateResponse:
    service = EngagementService(db, tenant_ctx.tenant_id)
    return await service.revoke_certificate(certificate_id, req, current_user.id)

