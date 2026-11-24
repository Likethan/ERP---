"""CampusOS Enterprise Student Support, Counselling & Personal Development API Router (Step 59).

CampusOS Tagline: "One Campus. One System. One Source of Truth."
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_current_user, get_tenant_context, require_permission
from app.core.permissions import (
    COUNSELLING_APPOINTMENT_MANAGE,
    COUNSELLING_APPOINTMENT_READ,
    COUNSELLING_APPOINTMENT_REQUEST,
    COUNSELLING_CONFIDENTIAL_READ,
    COUNSELLING_CONFIDENTIAL_WRITE,
    DEVELOPMENT_PLAN_MANAGE,
    DEVELOPMENT_PLAN_READ,
    MENTOR_ASSIGNMENT_MANAGE,
    MENTOR_ASSIGNMENT_READ,
    MENTORING_SESSION_MANAGE,
    MENTORING_SESSION_PARTICIPATE,
    MENTORING_SESSION_READ,
    SUPPORT_CONFIG_MANAGE,
    SUPPORT_FOLLOWUP_MANAGE,
    SUPPORT_REFERRAL_CREATE,
    SUPPORT_REFERRAL_MANAGE,
    SUPPORT_REFERRAL_READ,
    SUPPORT_REPORT_READ,
)
from app.core.tenant import TenantContext
from app.models.people import User
from app.schemas.student_support import (
    ConfidentialCounsellingRecordCreate,
    ConfidentialCounsellingRecordResponse,
    CounsellingAppointmentCreate,
    CounsellingAppointmentResponse,
    CounsellingAppointmentUpdate,
    DevelopmentGoalCreate,
    DevelopmentGoalResponse,
    DevelopmentGoalUpdate,
    MentorAssignmentCreate,
    MentorAssignmentResponse,
    MentoringSessionCreate,
    MentoringSessionResponse,
    MentoringSessionUpdate,
    MentorReassignRequest,
    SessionAttendeeReflectionUpdate,
    SessionAttendeeResponse,
    StudentDevelopmentPlanCreate,
    StudentDevelopmentPlanResponse,
    StudentSupportTelemetryResponse,
    SupportAuditLogResponse,
    SupportFollowUpCreate,
    SupportFollowUpResponse,
    SupportFollowUpUpdate,
    SupportPolicyConfigResponse,
    SupportPolicyConfigUpdate,
    SupportReferralCreate,
    SupportReferralResponse,
    SupportReferralUpdate,
)
from app.services.student_support_service import StudentSupportService

student_support_router = APIRouter(prefix="/student-support", tags=["Student Support & Counselling"])


# =============================================================================
# 1. MENTOR ASSIGNMENTS & MENTEE DIRECTORY
# =============================================================================


@student_support_router.post(
    "/mentor-assignments",
    response_model=MentorAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_mentor_assignment(
    data: MentorAssignmentCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(MENTOR_ASSIGNMENT_MANAGE))],
) -> MentorAssignmentResponse:
    service = StudentSupportService(db, tenant_ctx.tenant_id)
    return await service.create_mentor_assignment(data)


@student_support_router.get(
    "/mentor-assignments",
    response_model=list[MentorAssignmentResponse],
)
async def list_mentor_assignments(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(MENTOR_ASSIGNMENT_READ))],
    mentor_user_id: UUID | None = Query(None),
    student_id: UUID | None = Query(None),
    status: str | None = Query(None),
    department_id: UUID | None = Query(None),
) -> list[MentorAssignmentResponse]:
    service = StudentSupportService(db, tenant_ctx.tenant_id)
    return await service.list_mentor_assignments(
        mentor_user_id=mentor_user_id,
        student_id=student_id,
        status=status,
        department_id=department_id,
    )


@student_support_router.post(
    "/mentor-assignments/{assignment_id}/reassign",
    response_model=MentorAssignmentResponse,
)
async def reassign_mentor(
    assignment_id: UUID,
    data: MentorReassignRequest,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(MENTOR_ASSIGNMENT_MANAGE))],
) -> MentorAssignmentResponse:
    service = StudentSupportService(db, tenant_ctx.tenant_id)
    return await service.reassign_mentor(assignment_id, data)


@student_support_router.get(
    "/mentees",
    response_model=list[MentorAssignmentResponse],
)
async def list_my_mentees(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[MentorAssignmentResponse]:
    """Returns mentees assigned to the currently authenticated faculty mentor."""
    service = StudentSupportService(db, tenant_ctx.tenant_id)
    return await service.list_mentor_assignments(
        mentor_user_id=current_user.id,
        status="ACTIVE",
    )


# =============================================================================
# 2. MENTORING SESSIONS & ATTENDANCE
# =============================================================================


@student_support_router.post(
    "/mentoring-sessions",
    response_model=MentoringSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def schedule_mentoring_session(
    data: MentoringSessionCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(MENTORING_SESSION_MANAGE))],
) -> MentoringSessionResponse:
    service = StudentSupportService(db, tenant_ctx.tenant_id)
    return await service.schedule_mentoring_session(data, current_user.id)


@student_support_router.get(
    "/mentoring-sessions",
    response_model=list[MentoringSessionResponse],
)
async def list_mentoring_sessions(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(MENTORING_SESSION_READ))],
    mentor_user_id: UUID | None = Query(None),
    student_id: UUID | None = Query(None),
    status: str | None = Query(None),
) -> list[MentoringSessionResponse]:
    service = StudentSupportService(db, tenant_ctx.tenant_id)
    return await service.list_mentoring_sessions(
        mentor_user_id=mentor_user_id,
        student_id=student_id,
        status=status,
    )


@student_support_router.patch(
    "/mentoring-sessions/{session_id}",
    response_model=MentoringSessionResponse,
)
async def update_mentoring_session(
    session_id: UUID,
    data: MentoringSessionUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(MENTORING_SESSION_MANAGE))],
) -> MentoringSessionResponse:
    service = StudentSupportService(db, tenant_ctx.tenant_id)
    return await service.update_mentoring_session(session_id, data)


@student_support_router.post(
    "/mentoring-sessions/{session_id}/attendees/{student_id}/reflection",
    response_model=SessionAttendeeResponse,
)
async def record_attendee_reflection(
    session_id: UUID,
    student_id: UUID,
    data: SessionAttendeeReflectionUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(MENTORING_SESSION_PARTICIPATE))],
) -> SessionAttendeeResponse:
    service = StudentSupportService(db, tenant_ctx.tenant_id)
    return await service.record_attendee_reflection(session_id, student_id, data)


# =============================================================================
# 3. COUNSELLING APPOINTMENTS
# =============================================================================


@student_support_router.post(
    "/counselling-appointments",
    response_model=CounsellingAppointmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def request_counselling_appointment(
    data: CounsellingAppointmentCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(COUNSELLING_APPOINTMENT_REQUEST))],
) -> CounsellingAppointmentResponse:
    service = StudentSupportService(db, tenant_ctx.tenant_id)
    return await service.request_counselling_appointment(data, current_user.id)


@student_support_router.get(
    "/counselling-appointments",
    response_model=list[CounsellingAppointmentResponse],
)
async def list_counselling_appointments(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(COUNSELLING_APPOINTMENT_READ))],
    student_id: UUID | None = Query(None),
    counsellor_user_id: UUID | None = Query(None),
    status: str | None = Query(None),
) -> list[CounsellingAppointmentResponse]:
    service = StudentSupportService(db, tenant_ctx.tenant_id)
    return await service.list_counselling_appointments(
        student_id=student_id,
        counsellor_user_id=counsellor_user_id,
        status=status,
    )


@student_support_router.patch(
    "/counselling-appointments/{appointment_id}",
    response_model=CounsellingAppointmentResponse,
)
async def update_counselling_appointment(
    appointment_id: UUID,
    data: CounsellingAppointmentUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(COUNSELLING_APPOINTMENT_MANAGE))],
) -> CounsellingAppointmentResponse:
    service = StudentSupportService(db, tenant_ctx.tenant_id)
    return await service.update_counselling_appointment(appointment_id, data)


# =============================================================================
# 4. STRICTLY CONFIDENTIAL COUNSELLING RECORDS
# =============================================================================


@student_support_router.post(
    "/counselling-records",
    response_model=ConfidentialCounsellingRecordResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_confidential_record(
    data: ConfidentialCounsellingRecordCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(COUNSELLING_CONFIDENTIAL_WRITE))],
) -> ConfidentialCounsellingRecordResponse:
    service = StudentSupportService(db, tenant_ctx.tenant_id)
    return await service.create_confidential_record(data, current_user.id)


@student_support_router.get(
    "/counselling-records/{record_id}",
    response_model=ConfidentialCounsellingRecordResponse,
)
async def get_confidential_record(
    record_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(COUNSELLING_CONFIDENTIAL_READ))],
) -> ConfidentialCounsellingRecordResponse:
    service = StudentSupportService(db, tenant_ctx.tenant_id)
    return await service.get_confidential_record(record_id, current_user.id)


# =============================================================================
# 5. STUDENT DEVELOPMENT PLANS (IDP)
# =============================================================================


@student_support_router.post(
    "/development-plans",
    response_model=StudentDevelopmentPlanResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_development_plan(
    data: StudentDevelopmentPlanCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(DEVELOPMENT_PLAN_MANAGE))],
) -> StudentDevelopmentPlanResponse:
    service = StudentSupportService(db, tenant_ctx.tenant_id)
    return await service.create_development_plan(data)


@student_support_router.get(
    "/development-plans",
    response_model=list[StudentDevelopmentPlanResponse],
)
async def list_development_plans(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(DEVELOPMENT_PLAN_READ))],
    student_id: UUID | None = Query(None),
    mentor_user_id: UUID | None = Query(None),
) -> list[StudentDevelopmentPlanResponse]:
    service = StudentSupportService(db, tenant_ctx.tenant_id)
    return await service.list_development_plans(
        student_id=student_id,
        mentor_user_id=mentor_user_id,
    )


@student_support_router.get(
    "/development-plans/{plan_id}",
    response_model=StudentDevelopmentPlanResponse,
)
async def get_development_plan(
    plan_id: UUID,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(DEVELOPMENT_PLAN_READ))],
) -> StudentDevelopmentPlanResponse:
    service = StudentSupportService(db, tenant_ctx.tenant_id)
    return await service.get_development_plan(plan_id)


@student_support_router.post(
    "/development-plans/{plan_id}/goals",
    response_model=DevelopmentGoalResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_goal_to_plan(
    plan_id: UUID,
    data: DevelopmentGoalCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(DEVELOPMENT_PLAN_MANAGE))],
) -> DevelopmentGoalResponse:
    service = StudentSupportService(db, tenant_ctx.tenant_id)
    return await service.add_goal_to_plan(plan_id, data)


@student_support_router.patch(
    "/development-plans/goals/{goal_id}",
    response_model=DevelopmentGoalResponse,
)
async def update_development_goal(
    goal_id: UUID,
    data: DevelopmentGoalUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(DEVELOPMENT_PLAN_READ))],
) -> DevelopmentGoalResponse:
    service = StudentSupportService(db, tenant_ctx.tenant_id)
    return await service.update_goal(goal_id, data)


# =============================================================================
# 6. SUPPORT REFERRALS & FOLLOW-UPS
# =============================================================================


@student_support_router.post(
    "/referrals",
    response_model=SupportReferralResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_support_referral(
    data: SupportReferralCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(SUPPORT_REFERRAL_CREATE))],
) -> SupportReferralResponse:
    service = StudentSupportService(db, tenant_ctx.tenant_id)
    return await service.create_support_referral(data, current_user.id)


@student_support_router.get(
    "/referrals",
    response_model=list[SupportReferralResponse],
)
async def list_support_referrals(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(SUPPORT_REFERRAL_READ))],
    student_id: UUID | None = Query(None),
    target_service: str | None = Query(None),
    status: str | None = Query(None),
) -> list[SupportReferralResponse]:
    service = StudentSupportService(db, tenant_ctx.tenant_id)
    return await service.list_support_referrals(
        student_id=student_id,
        target_service=target_service,
        status=status,
    )


@student_support_router.patch(
    "/referrals/{referral_id}",
    response_model=SupportReferralResponse,
)
async def update_support_referral(
    referral_id: UUID,
    data: SupportReferralUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(SUPPORT_REFERRAL_MANAGE))],
) -> SupportReferralResponse:
    service = StudentSupportService(db, tenant_ctx.tenant_id)
    return await service.update_support_referral(referral_id, data)


@student_support_router.post(
    "/follow-ups",
    response_model=SupportFollowUpResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_follow_up(
    data: SupportFollowUpCreate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(SUPPORT_FOLLOWUP_MANAGE))],
) -> SupportFollowUpResponse:
    service = StudentSupportService(db, tenant_ctx.tenant_id)
    return await service.create_follow_up(data)


@student_support_router.get(
    "/follow-ups",
    response_model=list[SupportFollowUpResponse],
)
async def list_follow_ups(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(SUPPORT_FOLLOWUP_MANAGE))],
    assigned_user_id: UUID | None = Query(None),
    status: str | None = Query(None),
) -> list[SupportFollowUpResponse]:
    service = StudentSupportService(db, tenant_ctx.tenant_id)
    return await service.list_follow_ups(
        assigned_user_id=assigned_user_id,
        status=status,
    )


@student_support_router.patch(
    "/follow-ups/{followup_id}",
    response_model=SupportFollowUpResponse,
)
async def update_follow_up(
    followup_id: UUID,
    data: SupportFollowUpUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(SUPPORT_FOLLOWUP_MANAGE))],
) -> SupportFollowUpResponse:
    service = StudentSupportService(db, tenant_ctx.tenant_id)
    return await service.update_follow_up(followup_id, data)


# =============================================================================
# 7. TELEMETRY, POLICY CONFIG & AUDIT LOGS
# =============================================================================


@student_support_router.get(
    "/reports",
    response_model=StudentSupportTelemetryResponse,
)
async def get_support_telemetry(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(SUPPORT_REPORT_READ))],
) -> StudentSupportTelemetryResponse:
    service = StudentSupportService(db, tenant_ctx.tenant_id)
    return await service.get_telemetry_metrics()


@student_support_router.get(
    "/config",
    response_model=SupportPolicyConfigResponse,
)
async def get_support_config(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(SUPPORT_CONFIG_MANAGE))],
) -> SupportPolicyConfigResponse:
    service = StudentSupportService(db, tenant_ctx.tenant_id)
    cfg = await service.get_or_create_config()
    return SupportPolicyConfigResponse.model_validate(cfg)


@student_support_router.patch(
    "/config",
    response_model=SupportPolicyConfigResponse,
)
async def update_support_config(
    data: SupportPolicyConfigUpdate,
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(SUPPORT_CONFIG_MANAGE))],
) -> SupportPolicyConfigResponse:
    service = StudentSupportService(db, tenant_ctx.tenant_id)
    return await service.update_config(data)


@student_support_router.get(
    "/audit-logs",
    response_model=list[SupportAuditLogResponse],
)
async def list_audit_logs(
    tenant_ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(require_permission(SUPPORT_REPORT_READ))],
    limit: int = Query(50, ge=1, le=200),
) -> list[SupportAuditLogResponse]:
    service = StudentSupportService(db, tenant_ctx.tenant_id)
    return await service.list_audit_logs(limit=limit)
