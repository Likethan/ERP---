"""Enterprise Academic Timetable, Resource Scheduling & Conflict Resolution REST API Router (Step 49).

CampusOS Tagline: "One Campus. One System. One Source of Truth."
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_current_user, get_tenant_context, require_permission
from app.core.permissions import (
    TIMETABLE_APPROVE,
    TIMETABLE_CHANGES_APPROVE,
    TIMETABLE_CHANGES_REQUEST,
    TIMETABLE_FACULTY_AVAILABILITY,
    TIMETABLE_GENERATE,
    TIMETABLE_MANAGE,
    TIMETABLE_PUBLISH,
    TIMETABLE_READ,
    TIMETABLE_REPORTS_READ,
    TIMETABLE_RESOURCES_MANAGE,
)
from app.core.tenant import TenantContext
from app.models.people import User
from app.schemas.timetable import (
    AcademicCalendarPeriodCreate,
    AcademicCalendarPeriodResponse,
    AttendanceReconciliationReport,
    FacultyAvailabilityCreate,
    FacultyAvailabilityResponse,
    FacultyWorkloadSummary,
    ResourceAvailabilityCheckRequest,
    ResourceAvailabilityResponse,
    ResourceMaintenanceWindowCreate,
    ResourceMaintenanceWindowResponse,
    ResourceReservationCreate,
    ResourceReservationResponse,
    ScheduleExceptionCreate,
    ScheduleExceptionResponse,
    TeachingPeriodConfigCreate,
    TeachingPeriodConfigResponse,
    TimetableAnalyticsResponse,
    TimetableChangeRequestCreate,
    TimetableChangeRequestResponse,
    TimetableChangeRequestReview,
    TimetableGenerationJobResponse,
    TimetableGenerationRequest,
    TimetableGridResponse,
    TimetableScheduleCloneRequest,
    TimetableScheduleCreate,
    TimetableScheduleResponse,
    TimetableSessionBatchCreate,
    TimetableSessionCreate,
    TimetableSessionResponse,
    TimetableSessionUpdate,
    TimetableValidationReport,
    TimetableVersionApproval,
    TimetableVersionCreate,
    TimetableVersionPublish,
    TimetableVersionResponse,
)
from app.services.timetable_service import TimetableService

router = APIRouter(prefix="/timetable", tags=["Timetable & Scheduling"])


# =============================================================================
# 1. SCHEDULES
# =============================================================================


@router.post(
    "/schedules",
    response_model=TimetableScheduleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create master timetable schedule",
    dependencies=[Depends(require_permission(TIMETABLE_MANAGE))],
)
async def create_schedule(
    payload: TimetableScheduleCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TimetableScheduleResponse:
    return await TimetableService.create_schedule(db, ctx.tenant_id, payload, current_user.id)


@router.get(
    "/schedules",
    response_model=list[TimetableScheduleResponse],
    summary="List timetable schedules with filters",
    dependencies=[Depends(require_permission(TIMETABLE_READ))],
)
async def list_schedules(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    academic_year_id: UUID | None = Query(None),
    semester_id: UUID | None = Query(None),
    campus_id: UUID | None = Query(None),
    department_id: UUID | None = Query(None),
    section_id: UUID | None = Query(None),
) -> list[TimetableScheduleResponse]:
    return await TimetableService.list_schedules(
        db, ctx.tenant_id, academic_year_id, semester_id, campus_id, department_id, section_id
    )


@router.get(
    "/schedules/{schedule_id}",
    response_model=TimetableScheduleResponse,
    summary="Get timetable schedule details",
    dependencies=[Depends(require_permission(TIMETABLE_READ))],
)
async def get_schedule(
    schedule_id: UUID,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TimetableScheduleResponse:
    return await TimetableService.get_schedule(db, ctx.tenant_id, schedule_id)


@router.post(
    "/schedules/{schedule_id}/clone",
    response_model=TimetableScheduleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Clone timetable schedule from previous term",
    dependencies=[Depends(require_permission(TIMETABLE_MANAGE))],
)
async def clone_schedule(
    schedule_id: UUID,
    payload: TimetableScheduleCloneRequest,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TimetableScheduleResponse:
    return await TimetableService.clone_schedule(db, ctx.tenant_id, schedule_id, payload, current_user.id)


# =============================================================================
# 2. VERSIONS
# =============================================================================


@router.post(
    "/schedules/{schedule_id}/versions",
    response_model=TimetableVersionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new draft version for a timetable schedule",
    dependencies=[Depends(require_permission(TIMETABLE_MANAGE))],
)
async def create_version(
    schedule_id: UUID,
    payload: TimetableVersionCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TimetableVersionResponse:
    return await TimetableService.create_version(db, ctx.tenant_id, schedule_id, payload, current_user.id)


@router.get(
    "/schedules/{schedule_id}/versions",
    response_model=list[TimetableVersionResponse],
    summary="List all versions for a timetable schedule",
    dependencies=[Depends(require_permission(TIMETABLE_READ))],
)
async def list_versions(
    schedule_id: UUID,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[TimetableVersionResponse]:
    return await TimetableService.list_versions(db, ctx.tenant_id, schedule_id)


@router.post(
    "/versions/{version_id}/review",
    response_model=TimetableVersionResponse,
    summary="Submit timetable draft version for academic review",
    dependencies=[Depends(require_permission(TIMETABLE_MANAGE))],
)
async def submit_version_for_review(
    version_id: UUID,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TimetableVersionResponse:
    return await TimetableService.submit_for_review(db, ctx.tenant_id, version_id, current_user.id)


@router.post(
    "/versions/{version_id}/approve",
    response_model=TimetableVersionResponse,
    summary="Approve or reject a timetable version",
    dependencies=[Depends(require_permission(TIMETABLE_APPROVE))],
)
async def approve_version(
    version_id: UUID,
    payload: TimetableVersionApproval,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TimetableVersionResponse:
    return await TimetableService.approve_version(db, ctx.tenant_id, version_id, payload, current_user.id)


@router.post(
    "/versions/{version_id}/publish",
    response_model=TimetableVersionResponse,
    summary="Publish approved timetable version and sync canonical slots",
    dependencies=[Depends(require_permission(TIMETABLE_PUBLISH))],
)
async def publish_version(
    version_id: UUID,
    payload: TimetableVersionPublish,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TimetableVersionResponse:
    return await TimetableService.publish_version(db, ctx.tenant_id, version_id, payload, current_user.id)


@router.get(
    "/versions/{version_id}/validate",
    response_model=TimetableValidationReport,
    summary="Validate timetable version and detect collisions",
    dependencies=[Depends(require_permission(TIMETABLE_READ))],
)
async def validate_version(
    version_id: UUID,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TimetableValidationReport:
    return await TimetableService.validate_version(db, ctx.tenant_id, version_id)


# =============================================================================
# 3. SESSIONS
# =============================================================================


@router.post(
    "/versions/{version_id}/sessions",
    response_model=TimetableSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create instructional session in a timetable version",
    dependencies=[Depends(require_permission(TIMETABLE_MANAGE))],
)
async def create_session(
    version_id: UUID,
    payload: TimetableSessionCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TimetableSessionResponse:
    return await TimetableService.create_session(db, ctx.tenant_id, version_id, payload)


@router.post(
    "/versions/{version_id}/sessions/batch",
    response_model=list[TimetableSessionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Batch create instructional sessions in a timetable version",
    dependencies=[Depends(require_permission(TIMETABLE_MANAGE))],
)
async def batch_create_sessions(
    version_id: UUID,
    payload: TimetableSessionBatchCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[TimetableSessionResponse]:
    return await TimetableService.batch_create_sessions(db, ctx.tenant_id, version_id, payload)


@router.patch(
    "/sessions/{session_id}",
    response_model=TimetableSessionResponse,
    summary="Update instructional session details",
    dependencies=[Depends(require_permission(TIMETABLE_MANAGE))],
)
async def update_session(
    session_id: UUID,
    payload: TimetableSessionUpdate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TimetableSessionResponse:
    return await TimetableService.update_session(db, ctx.tenant_id, session_id, payload)


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete instructional session",
    dependencies=[Depends(require_permission(TIMETABLE_MANAGE))],
)
async def delete_session(
    session_id: UUID,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    await TimetableService.delete_session(db, ctx.tenant_id, session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# =============================================================================
# 4. PERIODS, CALENDAR & EXCEPTIONS
# =============================================================================


@router.post(
    "/teaching-periods",
    response_model=TeachingPeriodConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Configure teaching days, period duration, and breaks",
    dependencies=[Depends(require_permission(TIMETABLE_MANAGE))],
)
async def create_teaching_period_config(
    payload: TeachingPeriodConfigCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TeachingPeriodConfigResponse:
    return await TimetableService.create_teaching_period_config(db, ctx.tenant_id, payload)


@router.post(
    "/calendar-periods",
    response_model=AcademicCalendarPeriodResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Define holidays, recesses, and exam periods",
    dependencies=[Depends(require_permission(TIMETABLE_MANAGE))],
)
async def create_calendar_period(
    payload: AcademicCalendarPeriodCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> AcademicCalendarPeriodResponse:
    return await TimetableService.create_calendar_period(db, ctx.tenant_id, payload)


@router.post(
    "/exceptions",
    response_model=ScheduleExceptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Define timetable exceptions and day swaps",
    dependencies=[Depends(require_permission(TIMETABLE_MANAGE))],
)
async def create_schedule_exception(
    payload: ScheduleExceptionCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ScheduleExceptionResponse:
    return await TimetableService.create_schedule_exception(db, ctx.tenant_id, payload)


# =============================================================================
# 5. FACULTY AVAILABILITY & WORKLOAD
# =============================================================================


@router.post(
    "/faculty-availability",
    response_model=FacultyAvailabilityResponse,
    status_code=status.HTTP_200_OK,
    summary="Configure faculty availability and workload constraints",
    dependencies=[Depends(require_permission(TIMETABLE_FACULTY_AVAILABILITY))],
)
async def set_faculty_availability(
    payload: FacultyAvailabilityCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> FacultyAvailabilityResponse:
    return await TimetableService.set_faculty_availability(db, ctx.tenant_id, payload)


@router.get(
    "/faculty-workload/{faculty_id}",
    response_model=FacultyWorkloadSummary,
    summary="Calculate faculty teaching workload summary",
    dependencies=[Depends(require_permission(TIMETABLE_READ))],
)
async def get_faculty_workload(
    faculty_id: UUID,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    version_id: UUID | None = Query(None),
) -> FacultyWorkloadSummary:
    return await TimetableService.get_faculty_workload(db, ctx.tenant_id, faculty_id, version_id)


# =============================================================================
# 6. RESOURCE RESERVATIONS & AVAILABILITY
# =============================================================================


@router.post(
    "/resources/reservations",
    response_model=ResourceReservationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Book room or laboratory resource reservation",
    dependencies=[Depends(require_permission(TIMETABLE_RESOURCES_MANAGE))],
)
async def create_reservation(
    payload: ResourceReservationCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ResourceReservationResponse:
    return await TimetableService.create_reservation(db, ctx.tenant_id, payload, current_user.id)


@router.post(
    "/resources/maintenance",
    response_model=ResourceMaintenanceWindowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Schedule facility maintenance window",
    dependencies=[Depends(require_permission(TIMETABLE_RESOURCES_MANAGE))],
)
async def create_maintenance_window(
    payload: ResourceMaintenanceWindowCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ResourceMaintenanceWindowResponse:
    return await TimetableService.create_maintenance_window(db, ctx.tenant_id, payload)


@router.post(
    "/resources/check-availability",
    response_model=ResourceAvailabilityResponse,
    summary="Check room availability and fetch alternative recommendations",
    dependencies=[Depends(require_permission(TIMETABLE_READ))],
)
async def check_room_availability(
    payload: ResourceAvailabilityCheckRequest,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ResourceAvailabilityResponse:
    return await TimetableService.check_room_availability(
        db,
        ctx.tenant_id,
        payload.room_id,
        payload.day_of_week,
        payload.start_time,
        payload.end_time,
        payload.exclude_session_id,
    )


# =============================================================================
# 7. GENERATION ENGINE
# =============================================================================


@router.post(
    "/generate",
    response_model=TimetableGenerationJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger automated constraint-based timetable generation",
    dependencies=[Depends(require_permission(TIMETABLE_GENERATE))],
)
async def generate_timetable(
    payload: TimetableGenerationRequest,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TimetableGenerationJobResponse:
    return await TimetableService.generate_timetable(db, ctx.tenant_id, payload, current_user.id)


# =============================================================================
# 8. CHANGE REQUESTS
# =============================================================================


@router.post(
    "/change-requests",
    response_model=TimetableChangeRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit timetable session change request",
    dependencies=[Depends(require_permission(TIMETABLE_CHANGES_REQUEST))],
)
async def create_change_request(
    payload: TimetableChangeRequestCreate,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TimetableChangeRequestResponse:
    return await TimetableService.create_change_request(db, ctx.tenant_id, payload, current_user.id)


@router.post(
    "/change-requests/{request_id}/review",
    response_model=TimetableChangeRequestResponse,
    summary="Approve or reject schedule change request and apply updates",
    dependencies=[Depends(require_permission(TIMETABLE_CHANGES_APPROVE))],
)
async def review_change_request(
    request_id: UUID,
    payload: TimetableChangeRequestReview,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TimetableChangeRequestResponse:
    return await TimetableService.review_change_request(db, ctx.tenant_id, request_id, payload, current_user.id)


# =============================================================================
# 9. GRID VIEWS & CALENDAR EXPORT
# =============================================================================


@router.get(
    "/views/section/{section_id}",
    response_model=TimetableGridResponse,
    summary="Get section/cohort weekly timetable grid",
    dependencies=[Depends(require_permission(TIMETABLE_READ))],
)
async def get_section_timetable_grid(
    section_id: UUID,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TimetableGridResponse:
    # Check if student view
    is_student = hasattr(current_user, "roles") and any(r.role.name == "STUDENT" for r in getattr(current_user, "roles", []))
    return await TimetableService.get_section_timetable_grid(db, ctx.tenant_id, section_id, is_student_view=is_student)


@router.get(
    "/views/faculty/{faculty_id}",
    response_model=TimetableGridResponse,
    summary="Get faculty weekly timetable grid",
    dependencies=[Depends(require_permission(TIMETABLE_READ))],
)
async def get_faculty_timetable_grid(
    faculty_id: UUID,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TimetableGridResponse:
    return await TimetableService.get_faculty_timetable_grid(db, ctx.tenant_id, faculty_id)


@router.get(
    "/views/room/{room_id}",
    response_model=TimetableGridResponse,
    summary="Get room weekly timetable grid",
    dependencies=[Depends(require_permission(TIMETABLE_READ))],
)
async def get_room_timetable_grid(
    room_id: UUID,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TimetableGridResponse:
    return await TimetableService.get_room_timetable_grid(db, ctx.tenant_id, room_id)


@router.get(
    "/calendar/export",
    summary="Export weekly timetable in iCalendar RFC 5545 (.ics) format",
    dependencies=[Depends(require_permission(TIMETABLE_READ))],
)
async def export_calendar(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    section_id: UUID | None = Query(None),
    faculty_id: UUID | None = Query(None),
    room_id: UUID | None = Query(None),
) -> Response:
    if section_id:
        grid = await TimetableService.get_section_timetable_grid(db, ctx.tenant_id, section_id)
    elif faculty_id:
        grid = await TimetableService.get_faculty_timetable_grid(db, ctx.tenant_id, faculty_id)
    elif room_id:
        grid = await TimetableService.get_room_timetable_grid(db, ctx.tenant_id, room_id)
    else:
        grid = TimetableGridResponse(
            view_type="EMPTY",
            entity_id=UUID("00000000-0000-0000-0000-000000000000"),
            entity_name="Empty Calendar",
            academic_year_id=UUID("00000000-0000-0000-0000-000000000000"),
            semester_id=UUID("00000000-0000-0000-0000-000000000000"),
            version_id=None,
            is_published=False,
            days=[],
        )

    ics_content = TimetableService.export_icalendar(grid)
    return Response(content=ics_content, media_type="text/calendar")


# =============================================================================
# 10. ATTENDANCE & ANALYTICS
# =============================================================================


@router.get(
    "/attendance/reconciliation",
    response_model=AttendanceReconciliationReport,
    summary="Reconcile scheduled sessions against recorded attendance",
    dependencies=[Depends(require_permission(TIMETABLE_READ))],
)
async def reconcile_attendance(
    section_id: UUID,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> AttendanceReconciliationReport:
    return await TimetableService.reconcile_attendance_sessions(db, ctx.tenant_id, section_id)


@router.get(
    "/analytics",
    response_model=TimetableAnalyticsResponse,
    summary="Get tenant timetable coverage, room utilization, and faculty workload analytics",
    dependencies=[Depends(require_permission(TIMETABLE_REPORTS_READ))],
)
async def get_analytics(
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> TimetableAnalyticsResponse:
    return await TimetableService.get_analytics(db, ctx.tenant_id)
