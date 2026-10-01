"""Attendance Management Engine Endpoints."""

import math
from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_tenant_context, require_permission
from app.core.exceptions import PermissionDeniedException
from app.core.permissions import (
    ATTENDANCE_APPROVE_CORRECTION,
    ATTENDANCE_CORRECT,
    ATTENDANCE_LOCK,
    ATTENDANCE_MARK,
    ATTENDANCE_POLICY_CREATE,
    ATTENDANCE_POLICY_READ,
    ATTENDANCE_POLICY_UPDATE,
    ATTENDANCE_READ,
    LEAVE_APPROVE,
    LEAVE_CREATE,
    LEAVE_READ,
    LEAVE_REJECT,
)
from app.core.tenant import TenantContext
from app.models.people import StudentProfile, User
from app.schemas.attendance import (
    AttendanceCorrectionCreateRequest,
    AttendanceCorrectionResponse,
    AttendanceCorrectionReviewRequest,
    AttendanceDashboardResponse,
    AttendancePolicyCreateRequest,
    AttendancePolicyResponse,
    AttendancePolicyUpdateRequest,
    AttendanceRecordBulkSubmitRequest,
    AttendanceRecordResponse,
    AttendanceRecordUpdateRequest,
    AttendanceSessionCreateRequest,
    AttendanceSessionDetailResponse,
    AttendanceSessionFromTimetableRequest,
    AttendanceSessionResponse,
    AttendanceSessionUpdateRequest,
    CourseOfferingAttendanceSummary,
    LowAttendanceStudentItem,
    StudentLeaveCreateRequest,
    StudentLeaveResponse,
    StudentLeaveReviewRequest,
    StudentOverallAttendanceSummary,
)
from app.schemas.common import ApiResponse, PaginatedMeta, PaginatedResponse
from app.services.attendance_service import AttendanceService

router = APIRouter(prefix="/attendance", tags=["Attendance Engine"])


# -----------------------------------------------------------------------------
# 1. POLICIES
# -----------------------------------------------------------------------------
@router.get("/policies", response_model=ApiResponse[list[AttendancePolicyResponse]])
async def list_attendance_policies(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ATTENDANCE_POLICY_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[list[AttendancePolicyResponse]]:
    policies = await AttendanceService.list_policies(db, tenant.tenant_id)
    return ApiResponse(data=policies)


@router.post(
    "/policies",
    response_model=ApiResponse[AttendancePolicyResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_attendance_policy(
    payload: AttendancePolicyCreateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ATTENDANCE_POLICY_CREATE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AttendancePolicyResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    policy = await AttendanceService.create_policy(
        db, tenant.tenant_id, payload, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=policy)


@router.patch("/policies/{policy_id}", response_model=ApiResponse[AttendancePolicyResponse])
async def update_attendance_policy(
    policy_id: UUID,
    payload: AttendancePolicyUpdateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ATTENDANCE_POLICY_UPDATE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AttendancePolicyResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    policy = await AttendanceService.update_policy(
        db, tenant.tenant_id, policy_id, payload, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=policy)


# -----------------------------------------------------------------------------
# 2. SESSIONS
# -----------------------------------------------------------------------------
@router.get("/sessions", response_model=PaginatedResponse[AttendanceSessionResponse])
async def list_attendance_sessions(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ATTENDANCE_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    session_date: date | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    course_offering_id: UUID | None = Query(None),
    faculty_id: UUID | None = Query(None),
    section_id: UUID | None = Query(None),
    semester_id: UUID | None = Query(None),
    session_status: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> PaginatedResponse[AttendanceSessionResponse]:
    sessions, total = await AttendanceService.list_sessions(
        db,
        tenant.tenant_id,
        session_date=session_date,
        start_date=start_date,
        end_date=end_date,
        course_offering_id=course_offering_id,
        faculty_id=faculty_id,
        section_id=section_id,
        semester_id=semester_id,
        status=session_status,
        page=page,
        page_size=page_size,
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    return PaginatedResponse(
        data=sessions,
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
    "/sessions",
    response_model=ApiResponse[AttendanceSessionResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_attendance_session(
    payload: AttendanceSessionCreateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ATTENDANCE_MARK))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AttendanceSessionResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    session = await AttendanceService.create_session(
        db, tenant.tenant_id, payload, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=session)


@router.post(
    "/sessions/from-timetable",
    response_model=ApiResponse[AttendanceSessionResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_attendance_session_from_timetable(
    payload: AttendanceSessionFromTimetableRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ATTENDANCE_MARK))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AttendanceSessionResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    session = await AttendanceService.create_session_from_timetable(
        db, tenant.tenant_id, payload, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=session)


@router.get("/sessions/{session_id}", response_model=ApiResponse[AttendanceSessionDetailResponse])
async def get_attendance_session_detail(
    session_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ATTENDANCE_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AttendanceSessionDetailResponse]:
    detail = await AttendanceService.get_session_detail(db, tenant.tenant_id, session_id)
    return ApiResponse(data=detail)


@router.patch("/sessions/{session_id}", response_model=ApiResponse[AttendanceSessionResponse])
async def update_attendance_session(
    session_id: UUID,
    payload: AttendanceSessionUpdateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ATTENDANCE_MARK))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AttendanceSessionResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    session = await AttendanceService.update_session(
        db, tenant.tenant_id, session_id, payload, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=session)


@router.post("/sessions/{session_id}/open", response_model=ApiResponse[AttendanceSessionResponse])
async def open_attendance_session(
    session_id: UUID,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ATTENDANCE_MARK))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AttendanceSessionResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    session = await AttendanceService.open_session(
        db, tenant.tenant_id, session_id, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=session)


@router.post("/sessions/{session_id}/lock", response_model=ApiResponse[AttendanceSessionResponse])
async def lock_attendance_session(
    session_id: UUID,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ATTENDANCE_LOCK))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AttendanceSessionResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    session = await AttendanceService.lock_session(
        db, tenant.tenant_id, session_id, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=session)


# -----------------------------------------------------------------------------
# 3. ATTENDANCE RECORDS (BULK & SINGLE)
# -----------------------------------------------------------------------------
@router.get("/sessions/{session_id}/records", response_model=ApiResponse[list[AttendanceRecordResponse]])
async def get_session_records(
    session_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ATTENDANCE_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[list[AttendanceRecordResponse]]:
    detail = await AttendanceService.get_session_detail(db, tenant.tenant_id, session_id)
    return ApiResponse(data=detail.records)


@router.post("/sessions/{session_id}/records/bulk", response_model=ApiResponse[AttendanceSessionResponse])
async def submit_bulk_attendance(
    session_id: UUID,
    payload: AttendanceRecordBulkSubmitRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ATTENDANCE_MARK))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AttendanceSessionResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    session = await AttendanceService.submit_bulk_records(
        db,
        tenant.tenant_id,
        session_id,
        payload,
        user_id=current_user.id,
        ip_address=ip,
        faculty_user=current_user,
    )
    return ApiResponse(data=session)


@router.patch("/records/{record_id}", response_model=ApiResponse[AttendanceRecordResponse])
async def update_single_attendance_record(
    record_id: UUID,
    payload: AttendanceRecordUpdateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ATTENDANCE_MARK))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AttendanceRecordResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    record = await AttendanceService.update_single_record(
        db, tenant.tenant_id, record_id, payload, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=record)


# -----------------------------------------------------------------------------
# 4. SUMMARIES (STUDENT & COURSE OFFERING)
# -----------------------------------------------------------------------------
@router.get("/students/me/summary", response_model=ApiResponse[StudentOverallAttendanceSummary])
async def get_my_attendance_summary(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ATTENDANCE_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    semester_id: UUID | None = Query(None),
) -> ApiResponse[StudentOverallAttendanceSummary]:
    # Look up student profile associated with current_user
    stud_stmt = select(StudentProfile).where(
        StudentProfile.user_id == current_user.id,
        StudentProfile.tenant_id == tenant.tenant_id,
    )
    stud_res = await db.execute(stud_stmt)
    student = stud_res.scalar_one_or_none()
    if not student:
        raise PermissionDeniedException("attendance:read")

    summary = await AttendanceService.get_student_summary(
        db, tenant.tenant_id, student.id, semester_id=semester_id
    )
    return ApiResponse(data=summary)


@router.get("/students/{student_id}/summary", response_model=ApiResponse[StudentOverallAttendanceSummary])
async def get_student_attendance_summary(
    student_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ATTENDANCE_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    semester_id: UUID | None = Query(None),
) -> ApiResponse[StudentOverallAttendanceSummary]:
    # Enforce student privacy: if user has STUDENT role, can only access own record
    user_roles = {ur.role.name for ur in current_user.roles if ur.role}
    if "STUDENT" in user_roles and not bool({"SUPER_ADMIN", "INSTITUTION_ADMIN", "PRINCIPAL", "HOD", "FACULTY"} & user_roles):
        stud_stmt = select(StudentProfile).where(
            StudentProfile.user_id == current_user.id,
            StudentProfile.tenant_id == tenant.tenant_id,
        )
        stud_res = await db.execute(stud_stmt)
        my_student = stud_res.scalar_one_or_none()
        if not my_student or my_student.id != student_id:
            raise PermissionDeniedException("attendance:read")

    summary = await AttendanceService.get_student_summary(
        db, tenant.tenant_id, student_id, semester_id=semester_id
    )
    return ApiResponse(data=summary)


@router.get("/course-offerings/{course_offering_id}/summary", response_model=ApiResponse[CourseOfferingAttendanceSummary])
async def get_course_offering_attendance_summary(
    course_offering_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ATTENDANCE_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CourseOfferingAttendanceSummary]:
    summary = await AttendanceService.get_course_offering_summary(
        db, tenant.tenant_id, course_offering_id
    )
    return ApiResponse(data=summary)


# -----------------------------------------------------------------------------
# 5. STUDENT LEAVE REQUESTS
# -----------------------------------------------------------------------------
@router.get("/leaves", response_model=PaginatedResponse[StudentLeaveResponse])
async def list_leave_requests(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(LEAVE_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    student_id: UUID | None = Query(None),
    leave_status: str | None = Query(None, alias="status"),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> PaginatedResponse[StudentLeaveResponse]:
    # If caller is student, limit to own records
    user_roles = {ur.role.name for ur in current_user.roles if ur.role}
    if "STUDENT" in user_roles and not bool({"SUPER_ADMIN", "INSTITUTION_ADMIN", "PRINCIPAL", "HOD", "FACULTY"} & user_roles):
        stud_stmt = select(StudentProfile).where(
            StudentProfile.user_id == current_user.id,
            StudentProfile.tenant_id == tenant.tenant_id,
        )
        stud_res = await db.execute(stud_stmt)
        my_student = stud_res.scalar_one_or_none()
        if my_student:
            student_id = my_student.id

    leaves, total = await AttendanceService.list_leaves(
        db,
        tenant.tenant_id,
        student_id=student_id,
        status=leave_status,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    return PaginatedResponse(
        data=leaves,
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
    "/leaves",
    response_model=ApiResponse[StudentLeaveResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_leave_request(
    payload: StudentLeaveCreateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(LEAVE_CREATE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[StudentLeaveResponse]:
    # Students can only apply for themselves
    user_roles = {ur.role.name for ur in current_user.roles if ur.role}
    if "STUDENT" in user_roles and not bool({"SUPER_ADMIN", "INSTITUTION_ADMIN", "PRINCIPAL", "HOD"} & user_roles):
        stud_stmt = select(StudentProfile).where(
            StudentProfile.user_id == current_user.id,
            StudentProfile.tenant_id == tenant.tenant_id,
        )
        stud_res = await db.execute(stud_stmt)
        my_student = stud_res.scalar_one_or_none()
        if not my_student or my_student.id != payload.student_id:
            raise PermissionDeniedException("leave:create")

    ip = request.client.host if request.client else "127.0.0.1"
    leave = await AttendanceService.create_leave_request(
        db, tenant.tenant_id, payload, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=leave)


@router.post("/leaves/{leave_id}/approve", response_model=ApiResponse[StudentLeaveResponse])
async def approve_leave_request(
    leave_id: UUID,
    payload: StudentLeaveReviewRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(LEAVE_APPROVE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[StudentLeaveResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    leave = await AttendanceService.review_leave_request(
        db,
        tenant.tenant_id,
        leave_id,
        action="APPROVE",
        payload=payload,
        reviewer_user_id=current_user.id,
        ip_address=ip,
    )
    return ApiResponse(data=leave)


@router.post("/leaves/{leave_id}/reject", response_model=ApiResponse[StudentLeaveResponse])
async def reject_leave_request(
    leave_id: UUID,
    payload: StudentLeaveReviewRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(LEAVE_REJECT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[StudentLeaveResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    leave = await AttendanceService.review_leave_request(
        db,
        tenant.tenant_id,
        leave_id,
        action="REJECT",
        payload=payload,
        reviewer_user_id=current_user.id,
        ip_address=ip,
    )
    return ApiResponse(data=leave)


# -----------------------------------------------------------------------------
# 6. ATTENDANCE CORRECTIONS
# -----------------------------------------------------------------------------
@router.get("/corrections", response_model=PaginatedResponse[AttendanceCorrectionResponse])
async def list_attendance_corrections(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ATTENDANCE_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    correction_status: str | None = Query(None, alias="status"),
    course_offering_id: UUID | None = Query(None),
    student_id: UUID | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> PaginatedResponse[AttendanceCorrectionResponse]:
    corrections, total = await AttendanceService.list_corrections(
        db,
        tenant.tenant_id,
        status=correction_status,
        course_offering_id=course_offering_id,
        student_id=student_id,
        page=page,
        page_size=page_size,
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    return PaginatedResponse(
        data=corrections,
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
    "/corrections",
    response_model=ApiResponse[AttendanceCorrectionResponse],
    status_code=status.HTTP_201_CREATED,
)
async def request_attendance_correction(
    payload: AttendanceCorrectionCreateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ATTENDANCE_CORRECT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AttendanceCorrectionResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    correction = await AttendanceService.create_correction_request(
        db, tenant.tenant_id, payload, requested_by_user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=correction)


@router.post("/corrections/{correction_id}/approve", response_model=ApiResponse[AttendanceCorrectionResponse])
async def approve_attendance_correction(
    correction_id: UUID,
    payload: AttendanceCorrectionReviewRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ATTENDANCE_APPROVE_CORRECTION))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AttendanceCorrectionResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    correction = await AttendanceService.review_correction_request(
        db,
        tenant.tenant_id,
        correction_id,
        action="APPROVE",
        payload=payload,
        reviewer_user_id=current_user.id,
        ip_address=ip,
    )
    return ApiResponse(data=correction)


@router.post("/corrections/{correction_id}/reject", response_model=ApiResponse[AttendanceCorrectionResponse])
async def reject_attendance_correction(
    correction_id: UUID,
    payload: AttendanceCorrectionReviewRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ATTENDANCE_APPROVE_CORRECTION))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AttendanceCorrectionResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    correction = await AttendanceService.review_correction_request(
        db,
        tenant.tenant_id,
        correction_id,
        action="REJECT",
        payload=payload,
        reviewer_user_id=current_user.id,
        ip_address=ip,
    )
    return ApiResponse(data=correction)


# -----------------------------------------------------------------------------
# 7. DASHBOARD & LOW ATTENDANCE INTELLIGENCE
# -----------------------------------------------------------------------------
@router.get("/dashboard", response_model=ApiResponse[AttendanceDashboardResponse])
async def get_attendance_dashboard(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ATTENDANCE_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    today_date: date | None = Query(None),
) -> ApiResponse[AttendanceDashboardResponse]:
    dashboard = await AttendanceService.get_dashboard_metrics(
        db, tenant.tenant_id, today_date=today_date
    )
    return ApiResponse(data=dashboard)


@router.get("/low-attendance", response_model=ApiResponse[list[LowAttendanceStudentItem]])
async def get_low_attendance_students(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ATTENDANCE_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    course_offering_id: UUID | None = Query(None),
) -> ApiResponse[list[LowAttendanceStudentItem]]:
    items = await AttendanceService.evaluate_low_attendance_and_generate_alerts(
        db, tenant.tenant_id, course_offering_id=course_offering_id
    )
    return ApiResponse(data=items)
