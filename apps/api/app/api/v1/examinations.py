"""Examination and Assessment Engine Endpoints.

Implements the authoritative academic assessment subsystem of CampusOS:
Grade Scales -> Exam Terms -> Assessments -> Exam Schedules -> Eligibility ->
Marks Roster & Bulk Entry -> Corrections -> Grade & GPA Calculation -> Results & Publication.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_tenant_context, require_permission
from app.core.exceptions import PermissionDeniedException
from app.core.permissions import (
    ASSESSMENTS_CREATE,
    ASSESSMENTS_FINALIZE,
    ASSESSMENTS_READ,
    ASSESSMENTS_UPDATE,
    ELIGIBILITY_EVALUATE,
    ELIGIBILITY_OVERRIDE,
    ELIGIBILITY_READ,
    EXAMINATIONS_CREATE,
    EXAMINATIONS_READ,
    EXAMINATIONS_UPDATE,
    GRADE_SCALES_MANAGE,
    GRADE_SCALES_READ,
    MARKS_CORRECT,
    MARKS_ENTER,
    MARKS_FINALIZE,
    MARKS_READ,
    RESULTS_FINALIZE,
    RESULTS_PUBLISH,
    RESULTS_READ,
)
from app.core.tenant import TenantContext
from app.models.people import StudentProfile, User
from app.schemas.common import ApiResponse
from app.schemas.examination import (
    AssessmentBulkMarksSubmitRequest,
    AssessmentCreateRequest,
    AssessmentMarksRosterResponse,
    AssessmentResponse,
    AssessmentUpdateRequest,
    CourseAssessmentStructureResponse,
    ExamConflictCheckResponse,
    ExamEligibilityEvaluateRequest,
    ExamEligibilityOverrideRequest,
    ExamEligibilityResponse,
    ExaminationDashboardResponse,
    ExamScheduleCreateRequest,
    ExamScheduleResponse,
    ExamScheduleUpdateRequest,
    ExamTermCreateRequest,
    ExamTermResponse,
    GradeScaleCreateRequest,
    GradeScaleResponse,
    MarkCorrectionCreateRequest,
    MarkCorrectionResponse,
    MarkCorrectionReviewRequest,
    ResultFinalizeRequest,
    ResultPublishRequest,
    SemesterResultResponse,
    StudentSemesterTranscript,
)
from app.services.examination_service import ExaminationService

router = APIRouter(prefix="/examinations", tags=["Examination Engine"])


async def _resolve_student_profile(
    db: AsyncSession, tenant_id: UUID, user_id: UUID
) -> StudentProfile | None:
    """Helper to find student profile for the current user."""
    stmt = select(StudentProfile).where(
        StudentProfile.user_id == user_id,
        StudentProfile.tenant_id == tenant_id,
    )
    res = await db.execute(stmt)
    return res.scalar_one_or_none()


def _is_pure_student(user: User) -> bool:
    """Determine if user has only student role without elevated admin/faculty roles."""
    user_roles = {ur.role.name for ur in user.roles if ur.role}
    elevated = {"SUPER_ADMIN", "INSTITUTION_ADMIN", "PRINCIPAL", "HOD", "EXAMINATION_OFFICER", "FACULTY", "STAFF"}
    return "STUDENT" in user_roles and not bool(elevated & user_roles)


# -----------------------------------------------------------------------------
# 1. DASHBOARD & TELEMETRY
# -----------------------------------------------------------------------------
@router.get("/dashboard", response_model=ApiResponse[ExaminationDashboardResponse])
async def get_examination_dashboard(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(EXAMINATIONS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[ExaminationDashboardResponse]:
    """Get authoritative metrics and telemetry for the examination operations hub."""
    dashboard = await ExaminationService.get_dashboard_telemetry(db, tenant.tenant_id)
    return ApiResponse(data=dashboard)


# -----------------------------------------------------------------------------
# 2. GRADE SCALES
# -----------------------------------------------------------------------------
@router.get("/grade-scales", response_model=ApiResponse[list[GradeScaleResponse]])
async def list_grade_scales(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(GRADE_SCALES_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[list[GradeScaleResponse]]:
    """List all grading scales defined for this tenant."""
    scales = await ExaminationService.list_grade_scales(db, tenant.tenant_id)
    return ApiResponse(data=scales)


@router.post(
    "/grade-scales",
    response_model=ApiResponse[GradeScaleResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_grade_scale(
    payload: GradeScaleCreateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(GRADE_SCALES_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[GradeScaleResponse]:
    """Create a new grading scale (e.g. 10-point UGC, Absolute, Relative)."""
    ip = request.client.host if request.client else "127.0.0.1"
    scale = await ExaminationService.create_grade_scale(
        db, tenant.tenant_id, payload, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=scale)


# -----------------------------------------------------------------------------
# 3. EXAMINATION TERMS / CYCLES
# -----------------------------------------------------------------------------
@router.get("/terms", response_model=ApiResponse[list[ExamTermResponse]])
async def list_exam_terms(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(EXAMINATIONS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    academic_year_id: UUID | None = None,
    semester_id: UUID | None = None,
) -> ApiResponse[list[ExamTermResponse]]:
    """List examination terms with optional academic year and semester filtering."""
    terms = await ExaminationService.list_exam_terms(
        db,
        tenant.tenant_id,
        academic_year_id=academic_year_id,
        semester_id=semester_id,
    )
    return ApiResponse(data=terms)


@router.post(
    "/terms",
    response_model=ApiResponse[ExamTermResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_exam_term(
    payload: ExamTermCreateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(EXAMINATIONS_CREATE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[ExamTermResponse]:
    """Define a major examination cycle (e.g. Nov/Dec 2026 End-Semester Examinations)."""
    ip = request.client.host if request.client else "127.0.0.1"
    term = await ExaminationService.create_exam_term(
        db, tenant.tenant_id, payload, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=term)


# -----------------------------------------------------------------------------
# 4. ASSESSMENTS & COURSE ASSESSMENT STRUCTURE
# -----------------------------------------------------------------------------
@router.get("/assessments", response_model=ApiResponse[list[AssessmentResponse]])
async def list_assessments(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ASSESSMENTS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    course_offering_id: UUID | None = None,
    exam_term_id: UUID | None = None,
    assessment_type: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
) -> ApiResponse[list[AssessmentResponse]]:
    """List assessments configured across course offerings."""
    assessments = await ExaminationService.list_assessments(
        db,
        tenant.tenant_id,
        course_offering_id=course_offering_id,
        exam_term_id=exam_term_id,
        status=status_filter,
    )
    return ApiResponse(data=assessments)


@router.post(
    "/assessments",
    response_model=ApiResponse[AssessmentResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_assessment(
    payload: AssessmentCreateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ASSESSMENTS_CREATE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AssessmentResponse]:
    """Create an assessment component with weightage validation (cumulative <= 100%)."""
    ip = request.client.host if request.client else "127.0.0.1"
    assessment = await ExaminationService.create_assessment(
        db, tenant.tenant_id, payload, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=assessment)


@router.get("/assessments/{assessment_id}", response_model=ApiResponse[AssessmentResponse])
async def get_assessment(
    assessment_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ASSESSMENTS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AssessmentResponse]:
    """Fetch assessment detail by ID."""
    assessment = await ExaminationService.get_assessment(db, tenant.tenant_id, assessment_id)
    return ApiResponse(data=assessment)


@router.patch("/assessments/{assessment_id}", response_model=ApiResponse[AssessmentResponse])
async def update_assessment(
    assessment_id: UUID,
    payload: AssessmentUpdateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ASSESSMENTS_UPDATE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AssessmentResponse]:
    """Update assessment configuration (locked if finalized)."""
    ip = request.client.host if request.client else "127.0.0.1"
    assessment = await ExaminationService.update_assessment(
        db,
        tenant.tenant_id,
        assessment_id,
        payload,
        user_id=current_user.id,
        ip_address=ip,
    )
    return ApiResponse(data=assessment)


@router.post("/assessments/{assessment_id}/finalize", response_model=ApiResponse[AssessmentResponse])
async def finalize_assessment(
    assessment_id: UUID,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ASSESSMENTS_FINALIZE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AssessmentResponse]:
    """Finalize assessment and lock marks against standard edits."""
    ip = request.client.host if request.client else "127.0.0.1"
    assessment = await ExaminationService.finalize_assessment(
        db, tenant.tenant_id, assessment_id, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=assessment)


@router.get(
    "/course-offerings/{course_offering_id}/structure",
    response_model=ApiResponse[CourseAssessmentStructureResponse],
)
async def get_course_assessment_structure(
    course_offering_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ASSESSMENTS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CourseAssessmentStructureResponse]:
    """Fetch complete assessment scheme and cumulative weightage for a course offering."""
    structure = await ExaminationService.get_course_assessment_structure(
        db, tenant.tenant_id, course_offering_id
    )
    return ApiResponse(data=structure)


# -----------------------------------------------------------------------------
# 5. EXAM SCHEDULES & CONFLICT DETECTION
# -----------------------------------------------------------------------------
@router.get("/schedules", response_model=ApiResponse[list[ExamScheduleResponse]])
async def list_exam_schedules(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(EXAMINATIONS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    exam_term_id: UUID | None = None,
    course_offering_id: UUID | None = None,
    invigilator_id: UUID | None = None,
    room_id: UUID | None = None,
) -> ApiResponse[list[ExamScheduleResponse]]:
    """List examination timetable schedules."""
    schedules = await ExaminationService.list_exam_schedules(
        db,
        tenant.tenant_id,
        exam_term_id=exam_term_id,
        course_offering_id=course_offering_id,
    )
    return ApiResponse(data=schedules)


@router.post(
    "/schedules",
    response_model=ApiResponse[ExamScheduleResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_exam_schedule(
    payload: ExamScheduleCreateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(EXAMINATIONS_CREATE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[ExamScheduleResponse]:
    """Create exam schedule with strict conflict detection (Room, Student simultaneous, Invigilator)."""
    ip = request.client.host if request.client else "127.0.0.1"
    schedule = await ExaminationService.create_exam_schedule(
        db, tenant.tenant_id, payload, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=schedule)


@router.patch("/schedules/{schedule_id}", response_model=ApiResponse[ExamScheduleResponse])
async def update_exam_schedule(
    schedule_id: UUID,
    payload: ExamScheduleUpdateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(EXAMINATIONS_UPDATE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[ExamScheduleResponse]:
    """Update exam schedule with conflict re-validation."""
    ip = request.client.host if request.client else "127.0.0.1"
    schedule = await ExaminationService.update_exam_schedule(
        db,
        tenant.tenant_id,
        schedule_id,
        payload,
        user_id=current_user.id,
        ip_address=ip,
    )
    return ApiResponse(data=schedule)


@router.post("/schedules/check-conflict", response_model=ApiResponse[ExamConflictCheckResponse])
async def check_exam_conflict(
    payload: ExamScheduleCreateRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(EXAMINATIONS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[ExamConflictCheckResponse]:
    """Dry-run conflict check for candidate exam schedule without persisting."""
    asmt = await ExaminationService.get_assessment(db, tenant.tenant_id, payload.assessment_id)
    conflict = await ExaminationService.check_schedule_conflicts(
        db,
        tenant.tenant_id,
        course_offering_id=asmt.course_offering_id,
        exam_date=payload.exam_date,
        start_time=payload.start_time,
        end_time=payload.end_time,
        room_identifier=payload.room_identifier,
        invigilator_faculty_id=payload.invigilator_faculty_id,
    )
    return ApiResponse(data=conflict)


# -----------------------------------------------------------------------------
# 6. EXAM ELIGIBILITY (CONSUMING STEP 6 ATTENDANCE ENGINE)
# -----------------------------------------------------------------------------
@router.get(
    "/course-offerings/{course_offering_id}/eligibility",
    response_model=ApiResponse[list[ExamEligibilityResponse]],
)
async def get_course_eligibility_roster(
    course_offering_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ELIGIBILITY_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    exam_term_id: UUID | None = None,
) -> ApiResponse[list[ExamEligibilityResponse]]:
    """Retrieve historical eligibility snapshot for students in a course offering."""
    roster = await ExaminationService.get_course_eligibility(
        db, tenant.tenant_id, course_offering_id, exam_term_id=exam_term_id
    )
    return ApiResponse(data=roster)


@router.post(
    "/course-offerings/{course_offering_id}/eligibility/evaluate",
    response_model=ApiResponse[list[ExamEligibilityResponse]],
)
async def evaluate_course_eligibility(
    course_offering_id: UUID,
    payload: ExamEligibilityEvaluateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ELIGIBILITY_EVALUATE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[list[ExamEligibilityResponse]]:
    """Snapshot and evaluate student exam eligibility directly from Step 6 Attendance thresholds."""
    evaluated = await ExaminationService.evaluate_course_eligibility(
        db,
        tenant.tenant_id,
        course_offering_id=course_offering_id,
        exam_term_id=payload.exam_term_id,
        minimum_attendance_threshold=payload.minimum_attendance_threshold,
        evaluator_user_id=current_user.id,
    )
    return ApiResponse(data=evaluated)


@router.post(
    "/eligibility/{eligibility_id}/override",
    response_model=ApiResponse[ExamEligibilityResponse],
)
async def override_exam_eligibility(
    eligibility_id: UUID,
    payload: ExamEligibilityOverrideRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ELIGIBILITY_OVERRIDE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[ExamEligibilityResponse]:
    """Provide authorized institutional condonation or exemption override with audit reason."""
    ip = request.client.host if request.client else "127.0.0.1"
    updated = await ExaminationService.override_eligibility(
        db,
        tenant.tenant_id,
        eligibility_id=eligibility_id,
        payload=payload,
        authorizer_user_id=current_user.id,
        ip_address=ip,
    )
    return ApiResponse(data=updated)


# -----------------------------------------------------------------------------
# 7. MARKS ENTRY, BULK SUBMISSION & ROSTER
# -----------------------------------------------------------------------------
@router.get("/assessments/{assessment_id}/marks", response_model=ApiResponse[AssessmentMarksRosterResponse])
async def get_assessment_marks_roster(
    assessment_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(MARKS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AssessmentMarksRosterResponse]:
    """Retrieve full class marks roster with enrollment verification and statistics."""
    roster = await ExaminationService.get_assessment_marks_roster(db, tenant.tenant_id, assessment_id)
    return ApiResponse(data=roster)


@router.post("/assessments/{assessment_id}/marks/bulk", response_model=ApiResponse[AssessmentMarksRosterResponse])
async def bulk_submit_assessment_marks(
    assessment_id: UUID,
    payload: AssessmentBulkMarksSubmitRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(MARKS_ENTER))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AssessmentMarksRosterResponse]:
    """Bulk upsert class marks with range validation, non-numeric status support, and optional finalization."""
    ip = request.client.host if request.client else "127.0.0.1"
    await ExaminationService.submit_bulk_marks(
        db,
        tenant.tenant_id,
        assessment_id=assessment_id,
        payload=payload,
        user_id=current_user.id,
        ip_address=ip,
    )
    roster = await ExaminationService.get_assessment_marks_roster(db, tenant.tenant_id, assessment_id)
    return ApiResponse(data=roster)


# -----------------------------------------------------------------------------
# 8. MARK CORRECTIONS (SUPERVISED AUDITED WORKFLOW FOR LOCKED MARKS)
# -----------------------------------------------------------------------------
@router.post(
    "/marks/corrections",
    response_model=ApiResponse[MarkCorrectionResponse],
    status_code=status.HTTP_201_CREATED,
)
async def request_mark_correction(
    payload: MarkCorrectionCreateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(MARKS_CORRECT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[MarkCorrectionResponse]:
    """Submit a formal mark correction request for a finalized/locked mark."""
    ip = request.client.host if request.client else "127.0.0.1"
    correction = await ExaminationService.request_mark_correction(
        db, tenant.tenant_id, payload, requester_user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=correction)


@router.get("/marks/corrections", response_model=ApiResponse[list[MarkCorrectionResponse]])
async def list_mark_corrections(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(MARKS_CORRECT))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status_filter: str | None = Query(None, alias="status"),
) -> ApiResponse[list[MarkCorrectionResponse]]:
    """List pending or audited mark correction requests."""
    corrections = await ExaminationService.list_mark_corrections(
        db, tenant.tenant_id, status=status_filter
    )
    return ApiResponse(data=corrections)


@router.post("/marks/corrections/{correction_id}/approve", response_model=ApiResponse[MarkCorrectionResponse])
async def approve_mark_correction(
    correction_id: UUID,
    payload: MarkCorrectionReviewRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(MARKS_FINALIZE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[MarkCorrectionResponse]:
    """Approve correction, atomically updating the locked mark and recording an immutable audit trail."""
    ip = request.client.host if request.client else "127.0.0.1"
    reviewed = await ExaminationService.review_mark_correction(
        db,
        tenant.tenant_id,
        correction_id=correction_id,
        action="APPROVE",
        payload=payload,
        reviewer_user_id=current_user.id,
        ip_address=ip,
    )
    return ApiResponse(data=reviewed)


@router.post("/marks/corrections/{correction_id}/reject", response_model=ApiResponse[MarkCorrectionResponse])
async def reject_mark_correction(
    correction_id: UUID,
    payload: MarkCorrectionReviewRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(MARKS_FINALIZE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[MarkCorrectionResponse]:
    """Reject correction request."""
    ip = request.client.host if request.client else "127.0.0.1"
    reviewed = await ExaminationService.review_mark_correction(
        db,
        tenant.tenant_id,
        correction_id=correction_id,
        action="REJECT",
        payload=payload,
        reviewer_user_id=current_user.id,
        ip_address=ip,
    )
    return ApiResponse(data=reviewed)


# -----------------------------------------------------------------------------
# 9. GRADE CALCULATION, RESULTS FINALIZATION & CONTROLLED PUBLICATION
# -----------------------------------------------------------------------------
@router.post("/results/finalize", response_model=ApiResponse[list[SemesterResultResponse]])
async def finalize_course_results(
    payload: ResultFinalizeRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESULTS_FINALIZE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[list[SemesterResultResponse]]:
    """Compute weighted scores, assign letter grades/grade points, and finalize results in controlled draft."""
    ip = request.client.host if request.client else "127.0.0.1"
    results = await ExaminationService.calculate_and_finalize_results(
        db,
        tenant.tenant_id,
        course_offering_id=payload.course_offering_id,
        exam_term_id=payload.exam_term_id,
        grade_scale_id=payload.grade_scale_id,
        authorizer_user_id=current_user.id,
        ip_address=ip,
    )
    return ApiResponse(data=results)


@router.post("/results/publish", response_model=ApiResponse[dict[str, int]])
async def publish_results(
    payload: ResultPublishRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESULTS_PUBLISH))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[dict[str, int]]:
    """Transition finalized results from internal review to PUBLISHED, making them visible to students."""
    ip = request.client.host if request.client else "127.0.0.1"
    count = await ExaminationService.publish_results(
        db,
        tenant.tenant_id,
        exam_term_id=payload.exam_term_id,
        course_offering_id=payload.course_offering_id,
        publisher_user_id=current_user.id,
        ip_address=ip,
    )
    return ApiResponse(data={"published_count": count})


@router.get("/results", response_model=ApiResponse[list[SemesterResultResponse]])
async def list_results(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESULTS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    student_id: UUID | None = None,
    course_offering_id: UUID | None = None,
    exam_term_id: UUID | None = None,
) -> ApiResponse[list[SemesterResultResponse]]:
    """Fetch academic results.

    SECURITY CRITICAL:
    - Pure students can ONLY view their own records.
    - Pure students NEVER see unpublished, draft, or under-review marks.
    """
    is_student = _is_pure_student(current_user)
    target_student_id = student_id

    if is_student:
        student_profile = await _resolve_student_profile(db, tenant.tenant_id, current_user.id)
        if not student_profile:
            raise PermissionDeniedException("results:read (no student profile associated)")
        if target_student_id and target_student_id != student_profile.id:
            raise PermissionDeniedException("results:read (cannot view other student results)")
        target_student_id = student_profile.id

    results = await ExaminationService.get_results(
        db,
        tenant.tenant_id,
        student_id=target_student_id,
        course_offering_id=course_offering_id,
        exam_term_id=exam_term_id,
        is_student_request=is_student,
    )
    return ApiResponse(data=results)


@router.get(
    "/students/{student_id}/transcript",
    response_model=ApiResponse[StudentSemesterTranscript],
)
async def get_student_transcript(
    student_id: UUID,
    exam_term_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(RESULTS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[StudentSemesterTranscript]:
    """Fetch official semester grade report and GPA calculation for a student.

    Enforces student isolation and unpublished record masking.
    """
    is_student = _is_pure_student(current_user)
    if is_student:
        student_profile = await _resolve_student_profile(db, tenant.tenant_id, current_user.id)
        if not student_profile or student_profile.id != student_id:
            raise PermissionDeniedException("results:read (unauthorized student transcript access)")

    transcript = await ExaminationService.get_student_transcript(
        db,
        tenant.tenant_id,
        student_id=student_id,
        exam_term_id=exam_term_id,
        is_student_request=is_student,
    )
    return ApiResponse(data=transcript)
