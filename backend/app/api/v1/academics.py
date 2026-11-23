"""Academic management endpoints: Subjects, Curricula, Offerings, Enrollments, Timetable."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_tenant_context, require_permission
from app.core.permissions import (
    ACADEMICS_COURSES_MANAGE,
    ACADEMICS_COURSES_READ,
    ACADEMICS_CURRICULUM_MANAGE,
    ACADEMICS_CURRICULUM_PUBLISH,
    ACADEMICS_CURRICULUM_READ,
    ACADEMICS_ENROLLMENTS_MANAGE,
    ACADEMICS_ENROLLMENTS_READ,
    ACADEMICS_ROOMS_MANAGE,
    ACADEMICS_ROOMS_READ,
    ACADEMICS_SUBJECTS_MANAGE,
    ACADEMICS_SUBJECTS_READ,
    ACADEMICS_TIMETABLE_MANAGE,
    ACADEMICS_TIMETABLE_READ,
)
from app.core.tenant import TenantContext
from app.models.people import User
from app.schemas.academics import (
    ClassroomCreateRequest,
    ClassroomResponse,
    CourseBatchEnrollRequest,
    CourseEnrollmentCreateRequest,
    CourseEnrollmentResponse,
    CourseFacultyAssignmentCreateRequest,
    CourseOfferingCreateRequest,
    CourseOfferingDetailResponse,
    CourseOfferingResponse,
    CourseOfferingStatusTransitionRequest,
    CurriculumCreateRequest,
    CurriculumDetailResponse,
    CurriculumResponse,
    CurriculumSubjectCreateRequest,
    CurriculumUpdateRequest,
    SubjectCreateRequest,
    SubjectResponse,
    SubjectUpdateRequest,
    TimeSlotCreateRequest,
    TimeSlotResponse,
    TimetableEntryCreateRequest,
    TimetableEntryResponse,
    TimetableEntryUpdateRequest,
    TimetableSectionGridResponse,
)
from app.schemas.common import ApiResponse
from app.services.academic_service import AcademicService

router = APIRouter(prefix="/academics", tags=["Academic Engine"])


# -----------------------------------------------------------------------------
# 1. SUBJECTS
# -----------------------------------------------------------------------------
@router.get("/subjects", response_model=ApiResponse[list[SubjectResponse]])
async def list_subjects(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACADEMICS_SUBJECTS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    department_id: UUID | None = Query(None),
    subject_type: str | None = Query(None),
    search: str | None = Query(None),
    is_active: bool | None = Query(None),
) -> ApiResponse[list[SubjectResponse]]:
    subjects = await AcademicService.list_subjects(
        db,
        tenant.tenant_id,
        department_id=department_id,
        subject_type=subject_type,
        search=search,
        is_active=is_active,
    )
    return ApiResponse(data=subjects)


@router.post(
    "/subjects",
    response_model=ApiResponse[SubjectResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_subject(
    payload: SubjectCreateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACADEMICS_SUBJECTS_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[SubjectResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    sub = await AcademicService.create_subject(
        db, tenant.tenant_id, payload, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=sub)


@router.get("/subjects/{subject_id}", response_model=ApiResponse[SubjectResponse])
async def get_subject(
    subject_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACADEMICS_SUBJECTS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[SubjectResponse]:
    sub = await AcademicService.get_subject_response(db, tenant.tenant_id, subject_id)
    return ApiResponse(data=sub)


@router.patch("/subjects/{subject_id}", response_model=ApiResponse[SubjectResponse])
async def update_subject(
    subject_id: UUID,
    payload: SubjectUpdateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACADEMICS_SUBJECTS_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[SubjectResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    sub = await AcademicService.update_subject(
        db, tenant.tenant_id, subject_id, payload, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=sub)


# -----------------------------------------------------------------------------
# 2. CURRICULUM SCHEMES & SUBJECTS
# -----------------------------------------------------------------------------
@router.get("/curricula", response_model=ApiResponse[list[CurriculumResponse]])
async def list_curricula(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACADEMICS_CURRICULUM_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    program_id: UUID | None = Query(None),
    regulation_id: UUID | None = Query(None),
    status: str | None = Query(None),
) -> ApiResponse[list[CurriculumResponse]]:
    curricula = await AcademicService.list_curricula(
        db, tenant.tenant_id, program_id=program_id, regulation_id=regulation_id, status=status
    )
    return ApiResponse(data=curricula)


@router.post(
    "/curricula",
    response_model=ApiResponse[CurriculumDetailResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_curriculum(
    payload: CurriculumCreateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACADEMICS_CURRICULUM_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CurriculumDetailResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    c = await AcademicService.create_curriculum(
        db, tenant.tenant_id, payload, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=c)


@router.get("/curricula/{curriculum_id}", response_model=ApiResponse[CurriculumDetailResponse])
async def get_curriculum(
    curriculum_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACADEMICS_CURRICULUM_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CurriculumDetailResponse]:
    c = await AcademicService.get_curriculum_detail(db, tenant.tenant_id, curriculum_id)
    return ApiResponse(data=c)


@router.patch("/curricula/{curriculum_id}", response_model=ApiResponse[CurriculumDetailResponse])
async def update_curriculum(
    curriculum_id: UUID,
    payload: CurriculumUpdateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACADEMICS_CURRICULUM_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CurriculumDetailResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    c = await AcademicService.update_curriculum(
        db, tenant.tenant_id, curriculum_id, payload, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=c)


@router.post(
    "/curricula/{curriculum_id}/subjects", response_model=ApiResponse[CurriculumDetailResponse]
)
async def add_curriculum_subject(
    curriculum_id: UUID,
    payload: CurriculumSubjectCreateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACADEMICS_CURRICULUM_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CurriculumDetailResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    c = await AcademicService.add_curriculum_subject(
        db, tenant.tenant_id, curriculum_id, payload, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=c)


@router.delete(
    "/curricula/{curriculum_id}/subjects/{subject_id}",
    response_model=ApiResponse[CurriculumDetailResponse],
)
async def remove_curriculum_subject(
    curriculum_id: UUID,
    subject_id: UUID,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACADEMICS_CURRICULUM_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CurriculumDetailResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    c = await AcademicService.remove_curriculum_subject(
        db, tenant.tenant_id, curriculum_id, subject_id, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=c)


@router.post(
    "/curricula/{curriculum_id}/publish", response_model=ApiResponse[CurriculumDetailResponse]
)
async def publish_curriculum(
    curriculum_id: UUID,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACADEMICS_CURRICULUM_PUBLISH))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CurriculumDetailResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    c = await AcademicService.publish_curriculum(
        db, tenant.tenant_id, curriculum_id, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=c)


# -----------------------------------------------------------------------------
# 3. CLASSROOMS & TIME SLOTS
# -----------------------------------------------------------------------------
@router.get("/rooms", response_model=ApiResponse[list[ClassroomResponse]])
async def list_rooms(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACADEMICS_ROOMS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    campus_id: UUID | None = Query(None),
    is_active: bool | None = Query(None),
) -> ApiResponse[list[ClassroomResponse]]:
    rooms = await AcademicService.list_rooms(
        db, tenant.tenant_id, campus_id=campus_id, is_active=is_active
    )
    return ApiResponse(data=rooms)


@router.post(
    "/rooms",
    response_model=ApiResponse[ClassroomResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_room(
    payload: ClassroomCreateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACADEMICS_ROOMS_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[ClassroomResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    room = await AcademicService.create_room(
        db, tenant.tenant_id, payload, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=room)


@router.get("/time-slots", response_model=ApiResponse[list[TimeSlotResponse]])
async def list_time_slots(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACADEMICS_TIMETABLE_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    is_active: bool | None = Query(None),
) -> ApiResponse[list[TimeSlotResponse]]:
    slots = await AcademicService.list_time_slots(db, tenant.tenant_id, is_active=is_active)
    return ApiResponse(data=slots)


@router.post(
    "/time-slots",
    response_model=ApiResponse[TimeSlotResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_time_slot(
    payload: TimeSlotCreateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACADEMICS_TIMETABLE_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[TimeSlotResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    slot = await AcademicService.create_time_slot(
        db, tenant.tenant_id, payload, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=slot)


# -----------------------------------------------------------------------------
# 4. COURSE OFFERINGS & FACULTY ASSIGNMENTS
# -----------------------------------------------------------------------------
@router.get("/course-offerings", response_model=ApiResponse[list[CourseOfferingResponse]])
async def list_course_offerings(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACADEMICS_COURSES_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    academic_year_id: UUID | None = Query(None),
    semester_id: UUID | None = Query(None),
    section_id: UUID | None = Query(None),
    subject_id: UUID | None = Query(None),
    status: str | None = Query(None),
    search: str | None = Query(None),
) -> ApiResponse[list[CourseOfferingResponse]]:
    offerings = await AcademicService.list_offerings(
        db,
        tenant.tenant_id,
        academic_year_id=academic_year_id,
        semester_id=semester_id,
        section_id=section_id,
        subject_id=subject_id,
        status=status,
        search=search,
    )
    return ApiResponse(data=offerings)


@router.post(
    "/course-offerings",
    response_model=ApiResponse[CourseOfferingDetailResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_course_offering(
    payload: CourseOfferingCreateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACADEMICS_COURSES_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CourseOfferingDetailResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    offering = await AcademicService.create_offering(
        db, tenant.tenant_id, payload, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=offering)


@router.get(
    "/course-offerings/{offering_id}", response_model=ApiResponse[CourseOfferingDetailResponse]
)
async def get_course_offering(
    offering_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACADEMICS_COURSES_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CourseOfferingDetailResponse]:
    offering = await AcademicService.get_offering_detail(db, tenant.tenant_id, offering_id)
    return ApiResponse(data=offering)


@router.patch(
    "/course-offerings/{offering_id}/status",
    response_model=ApiResponse[CourseOfferingDetailResponse],
)
async def transition_offering_status(
    offering_id: UUID,
    payload: CourseOfferingStatusTransitionRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACADEMICS_COURSES_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CourseOfferingDetailResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    offering = await AcademicService.transition_offering_status(
        db, tenant.tenant_id, offering_id, payload.status, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=offering)


@router.post(
    "/course-offerings/{offering_id}/faculty",
    response_model=ApiResponse[CourseOfferingDetailResponse],
)
async def assign_faculty_to_offering(
    offering_id: UUID,
    payload: CourseFacultyAssignmentCreateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACADEMICS_COURSES_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CourseOfferingDetailResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    offering = await AcademicService.assign_faculty(
        db, tenant.tenant_id, offering_id, payload, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=offering)


@router.delete(
    "/course-offerings/{offering_id}/faculty/{faculty_id}",
    response_model=ApiResponse[CourseOfferingDetailResponse],
)
async def unassign_faculty_from_offering(
    offering_id: UUID,
    faculty_id: UUID,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACADEMICS_COURSES_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CourseOfferingDetailResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    offering = await AcademicService.unassign_faculty(
        db, tenant.tenant_id, offering_id, faculty_id, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=offering)


# -----------------------------------------------------------------------------
# 5. STUDENT COURSE ENROLLMENTS
# -----------------------------------------------------------------------------
@router.get(
    "/course-offerings/{offering_id}/students",
    response_model=ApiResponse[list[CourseEnrollmentResponse]],
)
async def list_course_students(
    offering_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACADEMICS_ENROLLMENTS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status: str | None = Query(None),
) -> ApiResponse[list[CourseEnrollmentResponse]]:
    students = await AcademicService.list_enrolled_students(
        db, tenant.tenant_id, offering_id, status=status
    )
    return ApiResponse(data=students)


@router.post(
    "/course-offerings/{offering_id}/students",
    response_model=ApiResponse[CourseEnrollmentResponse],
    status_code=status.HTTP_201_CREATED,
)
async def enroll_student(
    offering_id: UUID,
    payload: CourseEnrollmentCreateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACADEMICS_ENROLLMENTS_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CourseEnrollmentResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    enrollment = await AcademicService.enroll_student(
        db, tenant.tenant_id, offering_id, payload, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=enrollment)


@router.post(
    "/course-offerings/{offering_id}/students/batch-enroll",
    response_model=ApiResponse[dict[str, int]],
)
async def batch_enroll_section_students(
    offering_id: UUID,
    payload: CourseBatchEnrollRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACADEMICS_ENROLLMENTS_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[dict[str, int]]:
    ip = request.client.host if request.client else "127.0.0.1"
    count = await AcademicService.batch_enroll_section(
        db, tenant.tenant_id, offering_id, payload, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data={"enrolled_count": count})


@router.delete(
    "/course-offerings/{offering_id}/students/{student_id}",
    response_model=ApiResponse[dict[str, str]],
)
async def withdraw_student_from_offering(
    offering_id: UUID,
    student_id: UUID,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACADEMICS_ENROLLMENTS_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[dict[str, str]]:
    ip = request.client.host if request.client else "127.0.0.1"
    await AcademicService.withdraw_student(
        db, tenant.tenant_id, offering_id, student_id, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data={"message": "Student successfully withdrawn from course offering"})


# -----------------------------------------------------------------------------
# 6. TIMETABLE
# -----------------------------------------------------------------------------
@router.get("/timetable", response_model=ApiResponse[list[TimetableEntryResponse]])
async def list_timetable(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACADEMICS_TIMETABLE_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    section_id: UUID | None = Query(None),
    faculty_id: UUID | None = Query(None),
    room_id: UUID | None = Query(None),
    academic_year_id: UUID | None = Query(None),
    semester_id: UUID | None = Query(None),
    day_of_week: int | None = Query(None),
) -> ApiResponse[list[TimetableEntryResponse]]:
    entries = await AcademicService.list_timetable_entries(
        db,
        tenant.tenant_id,
        section_id=section_id,
        faculty_id=faculty_id,
        room_id=room_id,
        academic_year_id=academic_year_id,
        semester_id=semester_id,
        day_of_week=day_of_week,
    )
    return ApiResponse(data=entries)


@router.get("/timetable/grid", response_model=ApiResponse[TimetableSectionGridResponse])
async def get_section_timetable_grid(
    section_id: UUID,
    academic_year_id: UUID,
    semester_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACADEMICS_TIMETABLE_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[TimetableSectionGridResponse]:
    grid = await AcademicService.get_section_timetable_grid(
        db,
        tenant.tenant_id,
        section_id=section_id,
        academic_year_id=academic_year_id,
        semester_id=semester_id,
    )
    return ApiResponse(data=grid)


@router.post(
    "/timetable",
    response_model=ApiResponse[TimetableEntryResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_timetable_entry(
    payload: TimetableEntryCreateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACADEMICS_TIMETABLE_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[TimetableEntryResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    entry = await AcademicService.create_timetable_entry(
        db, tenant.tenant_id, payload, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=entry)


@router.patch("/timetable/{entry_id}", response_model=ApiResponse[TimetableEntryResponse])
async def update_timetable_entry(
    entry_id: UUID,
    payload: TimetableEntryUpdateRequest,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACADEMICS_TIMETABLE_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[TimetableEntryResponse]:
    ip = request.client.host if request.client else "127.0.0.1"
    entry = await AcademicService.update_timetable_entry(
        db, tenant.tenant_id, entry_id, payload, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data=entry)


@router.delete("/timetable/{entry_id}", response_model=ApiResponse[dict[str, str]])
async def delete_timetable_entry(
    entry_id: UUID,
    request: Request,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ACADEMICS_TIMETABLE_MANAGE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[dict[str, str]]:
    ip = request.client.host if request.client else "127.0.0.1"
    await AcademicService.delete_timetable_entry(
        db, tenant.tenant_id, entry_id, user_id=current_user.id, ip_address=ip
    )
    return ApiResponse(data={"message": "Timetable entry deleted successfully"})
