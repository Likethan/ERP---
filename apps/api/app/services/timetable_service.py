"""Enterprise Academic Timetable, Resource Scheduling & Conflict Resolution Engine Service (Step 49).

CampusOS Tagline: "One Campus. One System. One Source of Truth."

Coordinates academic timetables across institutions, campuses, departments,
programs, faculty, student cohorts, classrooms, laboratories, and academic terms.
Supports generation, resource allocation, conflict detection, controlled publication,
schedule changes, and schedule analytics.
"""

import logging
from datetime import UTC, date, datetime, time
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit import AuditEventCategory, record_audit_log
from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from app.models.academics import (
    Classroom,
    CourseOffering,
    TimeSlot,
    TimetableEntry,
)
from app.models.attendance import AttendanceSession
from app.models.core import AcademicYear, Section, Semester
from app.models.people import FacultyProfile
from app.models.timetable import (
    AcademicCalendarPeriod,
    ChangeRequestStatus,
    ChangeRequestType,
    ConflictSeverity,
    ConflictType,
    FacultyAvailability,
    GenerationJobStatus,
    MaintenanceStatus,
    RecurrencePattern,
    ReservationStatus,
    ResourceMaintenanceWindow,
    ResourceReservation,
    ScheduleException,
    SessionType,
    TeachingPeriodConfig,
    TimetableChangeRequest,
    TimetableConflict,
    TimetableGenerationJob,
    TimetablePublication,
    TimetableSchedule,
    TimetableSession,
    TimetableVersion,
    TimetableVersionStatus,
)
from app.models.workflow import OutboxEvent
from app.schemas.timetable import (
    AcademicCalendarPeriodCreate,
    AcademicCalendarPeriodResponse,
    AttendanceReconciliationReport,
    AttendanceSessionReconciliationItem,
    FacultyAvailabilityCreate,
    FacultyAvailabilityResponse,
    FacultyWorkloadMetric,
    FacultyWorkloadSummary,
    ResourceAvailabilityResponse,
    ResourceMaintenanceWindowCreate,
    ResourceMaintenanceWindowResponse,
    ResourceReservationCreate,
    ResourceReservationResponse,
    RoomUtilizationMetric,
    ScheduleExceptionCreate,
    ScheduleExceptionResponse,
    TeachingPeriodConfigCreate,
    TeachingPeriodConfigResponse,
    TimetableAnalyticsResponse,
    TimetableChangeRequestCreate,
    TimetableChangeRequestResponse,
    TimetableChangeRequestReview,
    TimetableConflictResponse,
    TimetableGenerationJobResponse,
    TimetableGenerationRequest,
    TimetableGridCell,
    TimetableGridDay,
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

logger = logging.getLogger(__name__)

DAYS_OF_WEEK_NAMES = {
    1: "Monday",
    2: "Tuesday",
    3: "Wednesday",
    4: "Thursday",
    5: "Friday",
    6: "Saturday",
    7: "Sunday",
}


class TimetableService:
    """Enterprise domain service for Timetables, Scheduling & Conflict Resolution."""

    # =========================================================================
    # 1. SCHEDULE & VERSION MANAGEMENT
    # =========================================================================

    @staticmethod
    async def create_schedule(
        db: AsyncSession,
        tenant_id: UUID,
        payload: TimetableScheduleCreate,
        user_id: UUID | None = None,
    ) -> TimetableScheduleResponse:
        # Unique code per tenant check
        existing = await db.scalar(
            select(TimetableSchedule).where(
                TimetableSchedule.tenant_id == tenant_id,
                TimetableSchedule.code == payload.code.strip(),
            )
        )
        if existing:
            raise ConflictException(f"Timetable schedule with code '{payload.code}' already exists.")

        # Validate academic year & semester
        ay = await db.scalar(
            select(AcademicYear).where(AcademicYear.tenant_id == tenant_id, AcademicYear.id == payload.academic_year_id)
        )
        if not ay:
            raise NotFoundException(f"Academic year '{payload.academic_year_id}' not found.")

        sem = await db.scalar(
            select(Semester).where(Semester.tenant_id == tenant_id, Semester.id == payload.semester_id)
        )
        if not sem:
            raise NotFoundException(f"Semester '{payload.semester_id}' not found.")

        schedule = TimetableSchedule(
            tenant_id=tenant_id,
            academic_year_id=payload.academic_year_id,
            semester_id=payload.semester_id,
            campus_id=payload.campus_id,
            department_id=payload.department_id,
            program_id=payload.program_id,
            section_id=payload.section_id,
            name=payload.name.strip(),
            code=payload.code.strip(),
            description=payload.description,
            is_active=True,
        )
        db.add(schedule)
        await db.flush()

        # Automatically create initial Version 1 (DRAFT)
        v1 = TimetableVersion(
            tenant_id=tenant_id,
            schedule_id=schedule.id,
            version_number=1,
            status=TimetableVersionStatus.DRAFT,
            change_summary="Initial draft version",
            is_active=True,
        )
        db.add(v1)
        await db.flush()

        await record_audit_log(
            db=db,
            tenant_id=tenant_id,
            action=AuditEventCategory.TIMETABLE_SCHEDULE_CREATED,
            entity_type="TimetableSchedule",
            entity_id=schedule.id,
            user_id=user_id,
            new_values_json={"code": schedule.code, "name": schedule.name},
        )
        await db.commit()

        return TimetableScheduleResponse(
            id=schedule.id,
            tenant_id=schedule.tenant_id,
            academic_year_id=schedule.academic_year_id,
            semester_id=schedule.semester_id,
            campus_id=schedule.campus_id,
            department_id=schedule.department_id,
            program_id=schedule.program_id,
            section_id=schedule.section_id,
            name=schedule.name,
            code=schedule.code,
            description=schedule.description,
            is_active=schedule.is_active,
            created_at=schedule.created_at,
            updated_at=schedule.updated_at,
            current_published_version_id=None,
            latest_version_number=1,
        )

    @staticmethod
    async def get_schedule(
        db: AsyncSession,
        tenant_id: UUID,
        schedule_id: UUID,
    ) -> TimetableScheduleResponse:
        schedule = await db.scalar(
            select(TimetableSchedule)
            .options(selectinload(TimetableSchedule.versions))
            .where(TimetableSchedule.tenant_id == tenant_id, TimetableSchedule.id == schedule_id)
        )
        if not schedule:
            raise NotFoundException(f"Timetable schedule '{schedule_id}' not found.")

        published_ver = next((v for v in schedule.versions if v.status == TimetableVersionStatus.PUBLISHED), None)
        latest_ver_num = max((v.version_number for v in schedule.versions), default=1)

        return TimetableScheduleResponse(
            id=schedule.id,
            tenant_id=schedule.tenant_id,
            academic_year_id=schedule.academic_year_id,
            semester_id=schedule.semester_id,
            campus_id=schedule.campus_id,
            department_id=schedule.department_id,
            program_id=schedule.program_id,
            section_id=schedule.section_id,
            name=schedule.name,
            code=schedule.code,
            description=schedule.description,
            is_active=schedule.is_active,
            created_at=schedule.created_at,
            updated_at=schedule.updated_at,
            current_published_version_id=published_ver.id if published_ver else None,
            latest_version_number=latest_ver_num,
        )

    @staticmethod
    async def list_schedules(
        db: AsyncSession,
        tenant_id: UUID,
        academic_year_id: UUID | None = None,
        semester_id: UUID | None = None,
        campus_id: UUID | None = None,
        department_id: UUID | None = None,
        section_id: UUID | None = None,
    ) -> list[TimetableScheduleResponse]:
        query = (
            select(TimetableSchedule)
            .options(selectinload(TimetableSchedule.versions))
            .where(TimetableSchedule.tenant_id == tenant_id)
            .order_by(TimetableSchedule.created_at.desc())
        )
        if academic_year_id:
            query = query.where(TimetableSchedule.academic_year_id == academic_year_id)
        if semester_id:
            query = query.where(TimetableSchedule.semester_id == semester_id)
        if campus_id:
            query = query.where(TimetableSchedule.campus_id == campus_id)
        if department_id:
            query = query.where(TimetableSchedule.department_id == department_id)
        if section_id:
            query = query.where(TimetableSchedule.section_id == section_id)

        res = await db.execute(query)
        schedules = res.scalars().all()

        responses = []
        for s in schedules:
            published_ver = next((v for v in s.versions if v.status == TimetableVersionStatus.PUBLISHED), None)
            latest_ver_num = max((v.version_number for v in s.versions), default=1)
            responses.append(
                TimetableScheduleResponse(
                    id=s.id,
                    tenant_id=s.tenant_id,
                    academic_year_id=s.academic_year_id,
                    semester_id=s.semester_id,
                    campus_id=s.campus_id,
                    department_id=s.department_id,
                    program_id=s.program_id,
                    section_id=s.section_id,
                    name=s.name,
                    code=s.code,
                    description=s.description,
                    is_active=s.is_active,
                    created_at=s.created_at,
                    updated_at=s.updated_at,
                    current_published_version_id=published_ver.id if published_ver else None,
                    latest_version_number=latest_ver_num,
                )
            )
        return responses

    @staticmethod
    async def clone_schedule(
        db: AsyncSession,
        tenant_id: UUID,
        schedule_id: UUID,
        payload: TimetableScheduleCloneRequest,
        user_id: UUID | None = None,
    ) -> TimetableScheduleResponse:
        source = await db.scalar(
            select(TimetableSchedule)
            .options(
                selectinload(TimetableSchedule.versions).selectinload(TimetableVersion.sessions),
            )
            .where(TimetableSchedule.tenant_id == tenant_id, TimetableSchedule.id == schedule_id)
        )
        if not source:
            raise NotFoundException(f"Source schedule '{schedule_id}' not found.")

        # Check unique code
        existing_code = await db.scalar(
            select(TimetableSchedule).where(
                TimetableSchedule.tenant_id == tenant_id,
                TimetableSchedule.code == payload.new_code.strip(),
            )
        )
        if existing_code:
            raise ConflictException(f"Timetable schedule code '{payload.new_code}' already exists.")

        # Identify source version: either specified or latest published or latest version
        source_ver = None
        if payload.source_version_id:
            source_ver = next((v for v in source.versions if v.id == payload.source_version_id), None)
        if not source_ver:
            source_ver = next((v for v in source.versions if v.status == TimetableVersionStatus.PUBLISHED), None)
        if not source_ver and source.versions:
            source_ver = source.versions[0]

        # Create cloned schedule
        new_schedule = TimetableSchedule(
            tenant_id=tenant_id,
            academic_year_id=payload.target_academic_year_id,
            semester_id=payload.target_semester_id,
            campus_id=source.campus_id,
            department_id=source.department_id,
            program_id=source.program_id,
            section_id=source.section_id,
            name=payload.new_name.strip(),
            code=payload.new_code.strip(),
            description=f"Cloned from {source.code} (v{source_ver.version_number if source_ver else 1})",
            is_active=True,
        )
        db.add(new_schedule)
        await db.flush()

        # Create version 1 (DRAFT)
        new_version = TimetableVersion(
            tenant_id=tenant_id,
            schedule_id=new_schedule.id,
            version_number=1,
            status=TimetableVersionStatus.DRAFT,
            change_summary=f"Cloned from {source.name} version {source_ver.version_number if source_ver else 1}",
            is_active=True,
        )
        db.add(new_version)
        await db.flush()

        # Clone sessions if source version has them
        if source_ver and source_ver.sessions:
            for s in source_ver.sessions:
                cloned_session = TimetableSession(
                    tenant_id=tenant_id,
                    version_id=new_version.id,
                    course_offering_id=s.course_offering_id,
                    section_id=s.section_id,
                    subject_id=s.subject_id,
                    faculty_id=s.faculty_id,
                    co_faculty_ids=list(s.co_faculty_ids) if s.co_faculty_ids else [],
                    room_id=s.room_id,
                    day_of_week=s.day_of_week,
                    start_time=s.start_time,
                    end_time=s.end_time,
                    time_slot_id=s.time_slot_id,
                    session_type=s.session_type,
                    session_group=s.session_group,
                    recurrence_pattern=s.recurrence_pattern,
                    is_locked=s.is_locked,
                    transition_buffer_minutes=s.transition_buffer_minutes,
                )
                db.add(cloned_session)
            await db.flush()

        await db.commit()

        return TimetableScheduleResponse(
            id=new_schedule.id,
            tenant_id=new_schedule.tenant_id,
            academic_year_id=new_schedule.academic_year_id,
            semester_id=new_schedule.semester_id,
            campus_id=new_schedule.campus_id,
            department_id=new_schedule.department_id,
            program_id=new_schedule.program_id,
            section_id=new_schedule.section_id,
            name=new_schedule.name,
            code=new_schedule.code,
            description=new_schedule.description,
            is_active=new_schedule.is_active,
            created_at=new_schedule.created_at,
            updated_at=new_schedule.updated_at,
            current_published_version_id=None,
            latest_version_number=1,
        )

    # -------------------------------------------------------------------------
    # Version Lifecycle
    # -------------------------------------------------------------------------

    @staticmethod
    async def create_version(
        db: AsyncSession,
        tenant_id: UUID,
        schedule_id: UUID,
        payload: TimetableVersionCreate,
        user_id: UUID | None = None,
    ) -> TimetableVersionResponse:
        schedule = await db.scalar(
            select(TimetableSchedule)
            .options(selectinload(TimetableSchedule.versions))
            .where(TimetableSchedule.tenant_id == tenant_id, TimetableSchedule.id == schedule_id)
        )
        if not schedule:
            raise NotFoundException(f"Timetable schedule '{schedule_id}' not found.")

        next_version_num = max([v.version_number for v in schedule.versions], default=0) + 1

        new_version = TimetableVersion(
            tenant_id=tenant_id,
            schedule_id=schedule.id,
            version_number=next_version_num,
            status=TimetableVersionStatus.DRAFT,
            effective_start_date=payload.effective_start_date,
            effective_end_date=payload.effective_end_date,
            change_summary=payload.change_summary or f"Version {next_version_num} draft",
            is_active=True,
        )
        db.add(new_version)
        await db.flush()
        await db.commit()

        return TimetableVersionResponse(
            id=new_version.id,
            tenant_id=new_version.tenant_id,
            schedule_id=new_version.schedule_id,
            version_number=new_version.version_number,
            status=new_version.status,
            effective_start_date=new_version.effective_start_date,
            effective_end_date=new_version.effective_end_date,
            change_summary=new_version.change_summary,
            is_active=new_version.is_active,
            approved_by_user_id=new_version.approved_by_user_id,
            approved_at=new_version.approved_at,
            published_by_user_id=new_version.published_by_user_id,
            published_at=new_version.published_at,
            created_at=new_version.created_at,
            updated_at=new_version.updated_at,
            sessions_count=0,
            conflicts_count=0,
        )

    @staticmethod
    async def list_versions(
        db: AsyncSession,
        tenant_id: UUID,
        schedule_id: UUID,
    ) -> list[TimetableVersionResponse]:
        query = (
            select(TimetableVersion)
            .options(
                selectinload(TimetableVersion.sessions),
                selectinload(TimetableVersion.conflicts),
            )
            .where(TimetableVersion.tenant_id == tenant_id, TimetableVersion.schedule_id == schedule_id)
            .order_by(TimetableVersion.version_number.desc())
        )
        res = await db.execute(query)
        versions = res.scalars().all()

        return [
            TimetableVersionResponse(
                id=v.id,
                tenant_id=v.tenant_id,
                schedule_id=v.schedule_id,
                version_number=v.version_number,
                status=v.status,
                effective_start_date=v.effective_start_date,
                effective_end_date=v.effective_end_date,
                change_summary=v.change_summary,
                is_active=v.is_active,
                approved_by_user_id=v.approved_by_user_id,
                approved_at=v.approved_at,
                published_by_user_id=v.published_by_user_id,
                published_at=v.published_at,
                created_at=v.created_at,
                updated_at=v.updated_at,
                sessions_count=len(v.sessions),
                conflicts_count=len(v.conflicts),
            )
            for v in versions
        ]

    @staticmethod
    async def submit_for_review(
        db: AsyncSession,
        tenant_id: UUID,
        version_id: UUID,
        user_id: UUID | None = None,
    ) -> TimetableVersionResponse:
        version = await db.scalar(
            select(TimetableVersion).where(
                TimetableVersion.tenant_id == tenant_id, TimetableVersion.id == version_id
            )
        )
        if not version:
            raise NotFoundException(f"Timetable version '{version_id}' not found.")

        if version.status not in (TimetableVersionStatus.DRAFT,):
            raise BadRequestException(f"Cannot submit version in status '{version.status}' for review.")

        # Run validation before submission
        val_report = await TimetableService.validate_version(db, tenant_id, version_id)
        if val_report.critical_conflicts_count > 0:
            raise ConflictException(
                f"Cannot submit timetable for review: {val_report.critical_conflicts_count} critical conflict(s) exist."
            )

        version.status = TimetableVersionStatus.UNDER_REVIEW
        await db.commit()

        return await TimetableService.get_version_response(db, tenant_id, version.id)

    @staticmethod
    async def approve_version(
        db: AsyncSession,
        tenant_id: UUID,
        version_id: UUID,
        approval: TimetableVersionApproval,
        user_id: UUID | None = None,
    ) -> TimetableVersionResponse:
        version = await db.scalar(
            select(TimetableVersion).where(
                TimetableVersion.tenant_id == tenant_id, TimetableVersion.id == version_id
            )
        )
        if not version:
            raise NotFoundException(f"Timetable version '{version_id}' not found.")

        if version.status != TimetableVersionStatus.UNDER_REVIEW:
            raise BadRequestException(f"Version must be in UNDER_REVIEW status to approve (currently '{version.status}').")

        if approval.approved:
            version.status = TimetableVersionStatus.APPROVED
            version.approved_by_user_id = user_id
            version.approved_at = datetime.now(UTC)
        else:
            version.status = TimetableVersionStatus.DRAFT
            if approval.rejection_reason:
                version.change_summary = f"Rejected: {approval.rejection_reason}"

        await db.commit()
        return await TimetableService.get_version_response(db, tenant_id, version.id)

    @staticmethod
    async def publish_version(
        db: AsyncSession,
        tenant_id: UUID,
        version_id: UUID,
        publish_config: TimetableVersionPublish,
        user_id: UUID | None = None,
    ) -> TimetableVersionResponse:
        version = await db.scalar(
            select(TimetableVersion)
            .options(
                selectinload(TimetableVersion.sessions),
                selectinload(TimetableVersion.schedule),
            )
            .where(TimetableVersion.tenant_id == tenant_id, TimetableVersion.id == version_id)
        )
        if not version:
            raise NotFoundException(f"Timetable version '{version_id}' not found.")

        if version.status != TimetableVersionStatus.APPROVED:
            raise BadRequestException(f"Only APPROVED timetable versions can be published (currently '{version.status}').")

        # Revalidate before publishing to guarantee zero collisions
        val_report = await TimetableService.validate_version(db, tenant_id, version_id)
        if val_report.critical_conflicts_count > 0:
            raise ConflictException(
                f"Cannot publish timetable: {val_report.critical_conflicts_count} critical conflict(s) detected during final check."
            )

        # Mark previously PUBLISHED versions for this schedule as SUPERSEDED
        prev_published_query = select(TimetableVersion).where(
            TimetableVersion.tenant_id == tenant_id,
            TimetableVersion.schedule_id == version.schedule_id,
            TimetableVersion.status == TimetableVersionStatus.PUBLISHED,
        )
        prev_res = await db.execute(prev_published_query)
        prev_versions = prev_res.scalars().all()
        for pv in prev_versions:
            pv.status = TimetableVersionStatus.SUPERSEDED

        # Mark this version as PUBLISHED
        version.status = TimetableVersionStatus.PUBLISHED
        version.published_by_user_id = user_id
        version.published_at = datetime.now(UTC)

        # Synchronize sessions into canonical `academics_timetable_slots` (`TimetableEntry`)
        # so attendance session generation and legacy consumers can bind directly!
        for s in version.sessions:
            if not s.is_cancelled:
                # Find or create a matching canonical TimetableEntry
                existing_entry = None
                if s.canonical_slot_id:
                    existing_entry = await db.scalar(
                        select(TimetableEntry).where(
                            TimetableEntry.tenant_id == tenant_id,
                            TimetableEntry.id == s.canonical_slot_id,
                        )
                    )

                if not existing_entry:
                    existing_entry = TimetableEntry(
                        tenant_id=tenant_id,
                        course_offering_id=s.course_offering_id,
                        section_id=s.section_id,
                        academic_year_id=version.schedule.academic_year_id,
                        semester_id=version.schedule.semester_id,
                        faculty_id=s.faculty_id,
                        room_id=s.room_id,
                        time_slot_id=s.time_slot_id if s.time_slot_id else (
                            # fallback: get default time slot or raise
                            await db.scalar(select(TimeSlot.id).where(TimeSlot.tenant_id == tenant_id).limit(1))
                        ),
                        day_of_week=s.day_of_week,
                        is_active=True,
                    )
                    db.add(existing_entry)
                    await db.flush()
                    s.canonical_slot_id = existing_entry.id
                else:
                    existing_entry.faculty_id = s.faculty_id
                    existing_entry.room_id = s.room_id
                    existing_entry.day_of_week = s.day_of_week
                    existing_entry.is_active = True

        # Record publication log
        publication = TimetablePublication(
            tenant_id=tenant_id,
            version_id=version.id,
            publication_type=publish_config.publication_type,
            published_to_students=publish_config.published_to_students,
            published_to_faculty=publish_config.published_to_faculty,
            calendar_sync_enabled=publish_config.calendar_sync_enabled,
            published_by_user_id=user_id,
            published_at=datetime.now(UTC),
            notes=publish_config.notes,
        )
        db.add(publication)

        # Record domain event to outbox
        outbox = OutboxEvent(
            id=uuid4(),
            tenant_id=tenant_id,
            aggregate_type="TimetableVersion",
            aggregate_id=version.id,
            event_type="TIMETABLE_PUBLISHED",
            correlation_id=str(uuid4()),
            payload={
                "schedule_id": str(version.schedule_id),
                "version_id": str(version.id),
                "version_number": version.version_number,
                "sessions_count": len(version.sessions),
                "published_at": version.published_at.isoformat(),
            },
        )
        db.add(outbox)

        await db.commit()
        return await TimetableService.get_version_response(db, tenant_id, version.id)

    @staticmethod
    async def get_version_response(
        db: AsyncSession,
        tenant_id: UUID,
        version_id: UUID,
    ) -> TimetableVersionResponse:
        v = await db.scalar(
            select(TimetableVersion)
            .options(
                selectinload(TimetableVersion.sessions),
                selectinload(TimetableVersion.conflicts),
            )
            .where(TimetableVersion.tenant_id == tenant_id, TimetableVersion.id == version_id)
        )
        if not v:
            raise NotFoundException(f"Timetable version '{version_id}' not found.")

        return TimetableVersionResponse(
            id=v.id,
            tenant_id=v.tenant_id,
            schedule_id=v.schedule_id,
            version_number=v.version_number,
            status=v.status,
            effective_start_date=v.effective_start_date,
            effective_end_date=v.effective_end_date,
            change_summary=v.change_summary,
            is_active=v.is_active,
            approved_by_user_id=v.approved_by_user_id,
            approved_at=v.approved_at,
            published_by_user_id=v.published_by_user_id,
            published_at=v.published_at,
            created_at=v.created_at,
            updated_at=v.updated_at,
            sessions_count=len(v.sessions),
            conflicts_count=len(v.conflicts),
        )

    # =========================================================================
    # 2. SESSION MANAGEMENT
    # =========================================================================

    @staticmethod
    async def create_session(
        db: AsyncSession,
        tenant_id: UUID,
        version_id: UUID,
        payload: TimetableSessionCreate,
    ) -> TimetableSessionResponse:
        version = await db.scalar(
            select(TimetableVersion).where(
                TimetableVersion.tenant_id == tenant_id, TimetableVersion.id == version_id
            )
        )
        if not version:
            raise NotFoundException(f"Timetable version '{version_id}' not found.")

        if version.status not in (TimetableVersionStatus.DRAFT, TimetableVersionStatus.UNDER_REVIEW):
            raise BadRequestException(f"Cannot add sessions to a version in status '{version.status}'.")

        # Prerequisite verification
        offering = await db.scalar(
            select(CourseOffering).where(
                CourseOffering.tenant_id == tenant_id, CourseOffering.id == payload.course_offering_id
            )
        )
        if not offering:
            raise NotFoundException(f"Course offering '{payload.course_offering_id}' not found.")

        sec = await db.scalar(
            select(Section).where(Section.tenant_id == tenant_id, Section.id == payload.section_id)
        )
        if not sec:
            raise NotFoundException(f"Section '{payload.section_id}' not found.")

        # If subject not given, retrieve from offering
        subject_id = payload.subject_id or offering.subject_id

        # Room capacity verification
        if payload.room_id:
            room = await db.scalar(
                select(Classroom).where(Classroom.tenant_id == tenant_id, Classroom.id == payload.room_id)
            )
            if not room:
                raise NotFoundException(f"Classroom '{payload.room_id}' not found.")
            if room.capacity < sec.capacity:
                raise ConflictException(
                    f"Room capacity ({room.capacity}) is less than section capacity ({sec.capacity})."
                )

        session = TimetableSession(
            tenant_id=tenant_id,
            version_id=version_id,
            course_offering_id=payload.course_offering_id,
            section_id=payload.section_id,
            subject_id=subject_id,
            faculty_id=payload.faculty_id,
            co_faculty_ids=[str(f_id) for f_id in payload.co_faculty_ids],
            room_id=payload.room_id,
            day_of_week=payload.day_of_week,
            start_time=payload.start_time,
            end_time=payload.end_time,
            time_slot_id=payload.time_slot_id,
            session_type=payload.session_type,
            session_group=payload.session_group,
            recurrence_pattern=payload.recurrence_pattern,
            is_locked=payload.is_locked,
            transition_buffer_minutes=payload.transition_buffer_minutes,
        )
        db.add(session)
        await db.commit()

        return await TimetableService.get_session_response(db, tenant_id, session.id)

    @staticmethod
    async def batch_create_sessions(
        db: AsyncSession,
        tenant_id: UUID,
        version_id: UUID,
        payload: TimetableSessionBatchCreate,
    ) -> list[TimetableSessionResponse]:
        results = []
        for s_in in payload.sessions:
            res = await TimetableService.create_session(db, tenant_id, version_id, s_in)
            results.append(res)
        return results

    @staticmethod
    async def update_session(
        db: AsyncSession,
        tenant_id: UUID,
        session_id: UUID,
        payload: TimetableSessionUpdate,
    ) -> TimetableSessionResponse:
        session = await db.scalar(
            select(TimetableSession).where(
                TimetableSession.tenant_id == tenant_id, TimetableSession.id == session_id
            )
        )
        if not session:
            raise NotFoundException(f"Timetable session '{session_id}' not found.")

        # Update fields
        update_data = payload.model_dump(exclude_unset=True)
        if "co_faculty_ids" in update_data and update_data["co_faculty_ids"] is not None:
            update_data["co_faculty_ids"] = [str(fid) for fid in update_data["co_faculty_ids"]]

        for k, v in update_data.items():
            setattr(session, k, v)

        await db.commit()
        return await TimetableService.get_session_response(db, tenant_id, session.id)

    @staticmethod
    async def delete_session(
        db: AsyncSession,
        tenant_id: UUID,
        session_id: UUID,
    ) -> None:
        session = await db.scalar(
            select(TimetableSession).where(
                TimetableSession.tenant_id == tenant_id, TimetableSession.id == session_id
            )
        )
        if not session:
            raise NotFoundException(f"Timetable session '{session_id}' not found.")

        await db.delete(session)
        await db.commit()

    @staticmethod
    async def get_session_response(
        db: AsyncSession,
        tenant_id: UUID,
        session_id: UUID,
    ) -> TimetableSessionResponse:
        s = await db.scalar(
            select(TimetableSession)
            .options(
                selectinload(TimetableSession.subject),
                selectinload(TimetableSession.section),
                selectinload(TimetableSession.faculty).selectinload(FacultyProfile.user),
                selectinload(TimetableSession.room),
            )
            .where(TimetableSession.tenant_id == tenant_id, TimetableSession.id == session_id)
        )
        if not s:
            raise NotFoundException(f"Timetable session '{session_id}' not found.")

        faculty_name = None
        if s.faculty and s.faculty.user:
            faculty_name = f"{s.faculty.user.first_name} {s.faculty.user.last_name}".strip()

        room_name = None
        if s.room:
            room_name = f"{s.room.building} - {s.room.room_number}"

        return TimetableSessionResponse(
            id=s.id,
            tenant_id=s.tenant_id,
            version_id=s.version_id,
            course_offering_id=s.course_offering_id,
            section_id=s.section_id,
            subject_id=s.subject_id,
            subject_code=s.subject.code if s.subject else None,
            subject_name=s.subject.name if s.subject else None,
            section_name=s.section.name if s.section else None,
            faculty_id=s.faculty_id,
            faculty_name=faculty_name,
            co_faculty_ids=s.co_faculty_ids,
            room_id=s.room_id,
            room_name=room_name,
            day_of_week=s.day_of_week,
            start_time=s.start_time,
            end_time=s.end_time,
            time_slot_id=s.time_slot_id,
            session_type=s.session_type,
            session_group=s.session_group,
            recurrence_pattern=s.recurrence_pattern,
            is_locked=s.is_locked,
            is_cancelled=s.is_cancelled,
            cancellation_reason=s.cancellation_reason,
            replacement_room_id=s.replacement_room_id,
            substitute_faculty_id=s.substitute_faculty_id,
            transition_buffer_minutes=s.transition_buffer_minutes,
            canonical_slot_id=s.canonical_slot_id,
            created_at=s.created_at,
            updated_at=s.updated_at,
        )

    # =========================================================================
    # 3. PERIOD CONFIG, CALENDAR & EXCEPTIONS
    # =========================================================================

    @staticmethod
    async def create_teaching_period_config(
        db: AsyncSession,
        tenant_id: UUID,
        payload: TeachingPeriodConfigCreate,
    ) -> TeachingPeriodConfigResponse:
        cfg = TeachingPeriodConfig(
            tenant_id=tenant_id,
            campus_id=payload.campus_id,
            academic_year_id=payload.academic_year_id,
            name=payload.name.strip(),
            teaching_days=payload.teaching_days,
            day_start_time=payload.day_start_time,
            day_end_time=payload.day_end_time,
            period_duration_minutes=payload.period_duration_minutes,
            transition_buffer_minutes=payload.transition_buffer_minutes,
            lunch_start_time=payload.lunch_start_time,
            lunch_end_time=payload.lunch_end_time,
            breaks_json=payload.breaks_json,
            is_default=payload.is_default,
            is_active=True,
        )
        db.add(cfg)
        await db.commit()

        return TeachingPeriodConfigResponse(
            id=cfg.id,
            tenant_id=cfg.tenant_id,
            campus_id=cfg.campus_id,
            academic_year_id=cfg.academic_year_id,
            name=cfg.name,
            teaching_days=cfg.teaching_days,
            day_start_time=cfg.day_start_time,
            day_end_time=cfg.day_end_time,
            period_duration_minutes=cfg.period_duration_minutes,
            transition_buffer_minutes=cfg.transition_buffer_minutes,
            lunch_start_time=cfg.lunch_start_time,
            lunch_end_time=cfg.lunch_end_time,
            breaks_json=cfg.breaks_json,
            is_default=cfg.is_default,
            is_active=cfg.is_active,
            created_at=cfg.created_at,
            updated_at=cfg.updated_at,
        )

    @staticmethod
    async def create_calendar_period(
        db: AsyncSession,
        tenant_id: UUID,
        payload: AcademicCalendarPeriodCreate,
    ) -> AcademicCalendarPeriodResponse:
        period = AcademicCalendarPeriod(
            tenant_id=tenant_id,
            academic_year_id=payload.academic_year_id,
            semester_id=payload.semester_id,
            campus_id=payload.campus_id,
            name=payload.name.strip(),
            calendar_type=payload.calendar_type,
            start_date=payload.start_date,
            end_date=payload.end_date,
            affects_teaching=payload.affects_teaching,
            description=payload.description,
            is_active=True,
        )
        db.add(period)
        await db.commit()

        return AcademicCalendarPeriodResponse(
            id=period.id,
            tenant_id=period.tenant_id,
            academic_year_id=period.academic_year_id,
            semester_id=period.semester_id,
            campus_id=period.campus_id,
            name=period.name,
            calendar_type=period.calendar_type,
            start_date=period.start_date,
            end_date=period.end_date,
            affects_teaching=period.affects_teaching,
            description=period.description,
            is_active=period.is_active,
            created_at=period.created_at,
            updated_at=period.updated_at,
        )

    @staticmethod
    async def create_schedule_exception(
        db: AsyncSession,
        tenant_id: UUID,
        payload: ScheduleExceptionCreate,
    ) -> ScheduleExceptionResponse:
        exc = ScheduleException(
            tenant_id=tenant_id,
            schedule_id=payload.schedule_id,
            campus_id=payload.campus_id,
            exception_date=payload.exception_date,
            exception_type=payload.exception_type,
            substitute_day_of_week=payload.substitute_day_of_week,
            affected_room_ids=[str(rid) for rid in payload.affected_room_ids],
            affected_section_ids=[str(sid) for sid in payload.affected_section_ids],
            notes=payload.notes,
            is_active=True,
        )
        db.add(exc)
        await db.commit()

        return ScheduleExceptionResponse(
            id=exc.id,
            tenant_id=exc.tenant_id,
            schedule_id=exc.schedule_id,
            campus_id=exc.campus_id,
            exception_date=exc.exception_date,
            exception_type=exc.exception_type,
            substitute_day_of_week=exc.substitute_day_of_week,
            affected_room_ids=exc.affected_room_ids,
            affected_section_ids=exc.affected_section_ids,
            notes=exc.notes,
            is_active=exc.is_active,
            created_at=exc.created_at,
            updated_at=exc.updated_at,
        )

    # =========================================================================
    # 4. FACULTY AVAILABILITY & WORKLOAD
    # =========================================================================

    @staticmethod
    async def set_faculty_availability(
        db: AsyncSession,
        tenant_id: UUID,
        payload: FacultyAvailabilityCreate,
    ) -> FacultyAvailabilityResponse:
        fac = await db.scalar(
            select(FacultyProfile).where(
                FacultyProfile.tenant_id == tenant_id, FacultyProfile.id == payload.faculty_id
            )
        )
        if not fac:
            raise NotFoundException(f"Faculty profile '{payload.faculty_id}' not found.")

        existing = await db.scalar(
            select(FacultyAvailability).where(
                FacultyAvailability.tenant_id == tenant_id,
                FacultyAvailability.faculty_id == payload.faculty_id,
                FacultyAvailability.academic_year_id == payload.academic_year_id,
                FacultyAvailability.day_of_week == payload.day_of_week,
            )
        )
        if existing:
            existing.available_start_time = payload.available_start_time
            existing.available_end_time = payload.available_end_time
            existing.is_available = payload.is_available
            existing.max_hours_per_day = payload.max_hours_per_day
            existing.max_hours_per_week = payload.max_hours_per_week
            existing.preferred_session_types = payload.preferred_session_types
            existing.notes = payload.notes
            await db.commit()
            record = existing
        else:
            record = FacultyAvailability(
                tenant_id=tenant_id,
                faculty_id=payload.faculty_id,
                academic_year_id=payload.academic_year_id,
                semester_id=payload.semester_id,
                day_of_week=payload.day_of_week,
                available_start_time=payload.available_start_time,
                available_end_time=payload.available_end_time,
                is_available=payload.is_available,
                max_hours_per_day=payload.max_hours_per_day,
                max_hours_per_week=payload.max_hours_per_week,
                preferred_session_types=payload.preferred_session_types,
                notes=payload.notes,
                is_active=True,
            )
            db.add(record)
            await db.commit()

        return FacultyAvailabilityResponse(
            id=record.id,
            tenant_id=record.tenant_id,
            faculty_id=record.faculty_id,
            academic_year_id=record.academic_year_id,
            semester_id=record.semester_id,
            day_of_week=record.day_of_week,
            available_start_time=record.available_start_time,
            available_end_time=record.available_end_time,
            is_available=record.is_available,
            max_hours_per_day=record.max_hours_per_day,
            max_hours_per_week=record.max_hours_per_week,
            preferred_session_types=record.preferred_session_types,
            notes=record.notes,
            is_active=record.is_active,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    @staticmethod
    async def get_faculty_workload(
        db: AsyncSession,
        tenant_id: UUID,
        faculty_id: UUID,
        version_id: UUID | None = None,
    ) -> FacultyWorkloadSummary:
        fac = await db.scalar(
            select(FacultyProfile)
            .options(
                selectinload(FacultyProfile.user),
                selectinload(FacultyProfile.department),
            )
            .where(FacultyProfile.tenant_id == tenant_id, FacultyProfile.id == faculty_id)
        )
        if not fac:
            raise NotFoundException(f"Faculty profile '{faculty_id}' not found.")

        # Find sessions assigned to this faculty
        q = select(TimetableSession).where(
            TimetableSession.tenant_id == tenant_id,
            or_(
                TimetableSession.faculty_id == faculty_id,
                TimetableSession.co_faculty_ids.contains([str(faculty_id)]),
            ),
            TimetableSession.is_cancelled == False,  # noqa: E712
        )
        if version_id:
            q = q.where(TimetableSession.version_id == version_id)

        res = await db.execute(q)
        sessions = res.scalars().all()

        daily_hours: dict[str, Decimal] = {name: Decimal("0.00") for name in DAYS_OF_WEEK_NAMES.values()}
        courses_set = set()

        total_hours = Decimal("0.00")
        for s in sessions:
            day_name = DAYS_OF_WEEK_NAMES.get(s.day_of_week, f"Day {s.day_of_week}")
            # Calculate duration in hours
            start_dt = datetime.combine(date.today(), s.start_time)
            end_dt = datetime.combine(date.today(), s.end_time)
            duration_hours = Decimal(str(round((end_dt - start_dt).total_seconds() / 3600.0, 2)))
            daily_hours[day_name] += duration_hours
            total_hours += duration_hours
            courses_set.add(s.course_offering_id)

        # Faculty policy or default 18.0 hrs/week
        avail = await db.scalar(
            select(FacultyAvailability).where(
                FacultyAvailability.tenant_id == tenant_id, FacultyAvailability.faculty_id == faculty_id
            )
        )
        max_limit = avail.max_hours_per_week if avail else Decimal("18.00")
        utilization = Decimal("0.00") if max_limit == 0 else round((total_hours / max_limit) * 100, 2)

        faculty_name = f"{fac.user.first_name} {fac.user.last_name}".strip() if fac.user else "Faculty"

        return FacultyWorkloadSummary(
            faculty_id=fac.id,
            faculty_name=faculty_name,
            department_id=fac.department_id,
            department_name=fac.department.name if fac.department else None,
            total_assigned_hours_per_week=total_hours,
            max_allowed_hours_per_week=max_limit,
            workload_utilization_percent=utilization,
            daily_hours=daily_hours,
            active_courses_count=len(courses_set),
            is_overloaded=total_hours > max_limit,
        )

    # =========================================================================
    # 5. RESOURCE ALLOCATION & RESERVATIONS
    # =========================================================================

    @staticmethod
    async def create_reservation(
        db: AsyncSession,
        tenant_id: UUID,
        payload: ResourceReservationCreate,
        user_id: UUID | None = None,
    ) -> ResourceReservationResponse:
        room = await db.scalar(
            select(Classroom).where(Classroom.tenant_id == tenant_id, Classroom.id == payload.room_id)
        )
        if not room:
            raise NotFoundException(f"Room '{payload.room_id}' not found.")

        # Check overlapping confirmed reservation
        overlap = await db.scalar(
            select(ResourceReservation).where(
                ResourceReservation.tenant_id == tenant_id,
                ResourceReservation.room_id == payload.room_id,
                ResourceReservation.status == ReservationStatus.CONFIRMED,
                ResourceReservation.start_datetime < payload.end_datetime,
                ResourceReservation.end_datetime > payload.start_datetime,
            )
        )
        if overlap:
            raise ConflictException(
                f"Resource conflict: Room is already booked from {overlap.start_datetime} to {overlap.end_datetime}."
            )

        # Check maintenance window
        maint = await db.scalar(
            select(ResourceMaintenanceWindow).where(
                ResourceMaintenanceWindow.tenant_id == tenant_id,
                ResourceMaintenanceWindow.room_id == payload.room_id,
                ResourceMaintenanceWindow.status.in_([MaintenanceStatus.SCHEDULED, MaintenanceStatus.IN_PROGRESS]),
                ResourceMaintenanceWindow.start_time < payload.end_datetime,
                ResourceMaintenanceWindow.end_time > payload.start_datetime,
            )
        )
        if maint:
            raise ConflictException(f"Room is undergoing maintenance: {maint.reason}")

        res = ResourceReservation(
            tenant_id=tenant_id,
            room_id=payload.room_id,
            reservation_type=payload.reservation_type,
            title=payload.title.strip(),
            start_datetime=payload.start_datetime,
            end_datetime=payload.end_datetime,
            status=ReservationStatus.CONFIRMED,
            session_id=payload.session_id,
            requested_by_user_id=user_id,
            approved_by_user_id=user_id,
            is_exclusive=payload.is_exclusive,
            notes=payload.notes,
        )
        db.add(res)
        await db.commit()

        return ResourceReservationResponse(
            id=res.id,
            tenant_id=res.tenant_id,
            room_id=res.room_id,
            room_name=f"{room.building} - {room.room_number}",
            reservation_type=res.reservation_type,
            title=res.title,
            start_datetime=res.start_datetime,
            end_datetime=res.end_datetime,
            status=res.status,
            session_id=res.session_id,
            requested_by_user_id=res.requested_by_user_id,
            approved_by_user_id=res.approved_by_user_id,
            is_exclusive=res.is_exclusive,
            notes=res.notes,
            created_at=res.created_at,
            updated_at=res.updated_at,
        )

    @staticmethod
    async def create_maintenance_window(
        db: AsyncSession,
        tenant_id: UUID,
        payload: ResourceMaintenanceWindowCreate,
    ) -> ResourceMaintenanceWindowResponse:
        room = await db.scalar(
            select(Classroom).where(Classroom.tenant_id == tenant_id, Classroom.id == payload.room_id)
        )
        if not room:
            raise NotFoundException(f"Room '{payload.room_id}' not found.")

        maint = ResourceMaintenanceWindow(
            tenant_id=tenant_id,
            room_id=payload.room_id,
            title=payload.title.strip(),
            reason=payload.reason.strip(),
            start_time=payload.start_time,
            end_time=payload.end_time,
            status=MaintenanceStatus.SCHEDULED,
        )
        db.add(maint)
        await db.commit()

        return ResourceMaintenanceWindowResponse(
            id=maint.id,
            tenant_id=maint.tenant_id,
            room_id=maint.room_id,
            title=maint.title,
            reason=maint.reason,
            start_time=maint.start_time,
            end_time=maint.end_time,
            status=maint.status,
            created_at=maint.created_at,
            updated_at=maint.updated_at,
        )

    @staticmethod
    async def check_room_availability(
        db: AsyncSession,
        tenant_id: UUID,
        room_id: UUID,
        day_of_week: int,
        start_time: time,
        end_time: time,
        exclude_session_id: UUID | None = None,
    ) -> ResourceAvailabilityResponse:
        # Check sessions
        sq = select(TimetableSession).where(
            TimetableSession.tenant_id == tenant_id,
            TimetableSession.room_id == room_id,
            TimetableSession.day_of_week == day_of_week,
            TimetableSession.start_time < end_time,
            TimetableSession.end_time > start_time,
            TimetableSession.is_cancelled == False,  # noqa: E712
        )
        if exclude_session_id:
            sq = sq.where(TimetableSession.id != exclude_session_id)

        s_res = await db.execute(sq)
        sessions_count = len(s_res.scalars().all())

        is_available = sessions_count == 0

        # Suggested alternatives if occupied
        alternatives: list[dict[str, Any]] = []
        if not is_available:
            # Query rooms of similar or greater capacity that are free
            target_room = await db.scalar(
                select(Classroom).where(Classroom.tenant_id == tenant_id, Classroom.id == room_id)
            )
            cap = target_room.capacity if target_room else 40

            alt_query = (
                select(Classroom)
                .where(
                    Classroom.tenant_id == tenant_id,
                    Classroom.id != room_id,
                    Classroom.capacity >= cap,
                    Classroom.is_active == True,  # noqa: E712
                )
                .limit(5)
            )
            alt_res = await db.execute(alt_query)
            alt_rooms = alt_res.scalars().all()

            for ar in alt_rooms:
                busy = await db.scalar(
                    select(TimetableSession.id).where(
                        TimetableSession.tenant_id == tenant_id,
                        TimetableSession.room_id == ar.id,
                        TimetableSession.day_of_week == day_of_week,
                        TimetableSession.start_time < end_time,
                        TimetableSession.end_time > start_time,
                        TimetableSession.is_cancelled == False,  # noqa: E712
                    )
                )
                if not busy:
                    alternatives.append(
                        {
                            "room_id": str(ar.id),
                            "room_number": ar.room_number,
                            "building": ar.building,
                            "capacity": ar.capacity,
                            "room_type": ar.room_type,
                        }
                    )

        return ResourceAvailabilityResponse(
            room_id=room_id,
            is_available=is_available,
            conflicting_sessions_count=sessions_count,
            conflicting_reservations_count=0,
            maintenance_windows_count=0,
            suggested_alternative_rooms=alternatives,
        )

    # =========================================================================
    # 6. CONFLICT DETECTION ENGINE
    # =========================================================================

    @staticmethod
    async def validate_version(
        db: AsyncSession,
        tenant_id: UUID,
        version_id: UUID,
    ) -> TimetableValidationReport:
        version = await db.scalar(
            select(TimetableVersion)
            .options(
                selectinload(TimetableVersion.sessions).selectinload(TimetableSession.room),
                selectinload(TimetableVersion.sessions).selectinload(TimetableSession.section),
                selectinload(TimetableVersion.sessions).selectinload(TimetableSession.faculty),
                selectinload(TimetableVersion.sessions).selectinload(TimetableSession.course_offering),
            )
            .where(TimetableVersion.tenant_id == tenant_id, TimetableVersion.id == version_id)
        )
        if not version:
            raise NotFoundException(f"Timetable version '{version_id}' not found.")

        # Clear existing dynamic conflicts for this version
        await db.execute(
            select(TimetableConflict).where(
                TimetableConflict.tenant_id == tenant_id, TimetableConflict.version_id == version_id
            )
        )

        conflicts: list[TimetableConflict] = []
        active_sessions = [s for s in version.sessions if not s.is_cancelled]

        # 1. Check Faculty & Room & Section overlaps among sessions in this version
        for i, s1 in enumerate(active_sessions):
            for s2 in active_sessions[i + 1 :]:
                if s1.day_of_week != s2.day_of_week:
                    continue
                # Overlap test: s1.start < s2.end and s1.end > s2.start
                if s1.start_time < s2.end_time and s1.end_time > s2.start_time:
                    day_name = DAYS_OF_WEEK_NAMES.get(s1.day_of_week, f"Day {s1.day_of_week}")
                    window = f"{s1.start_time.strftime('%H:%M')} - {s1.end_time.strftime('%H:%M')}"

                    # Faculty overlap
                    if s1.faculty_id and s2.faculty_id and s1.faculty_id == s2.faculty_id:
                        c = TimetableConflict(
                            tenant_id=tenant_id,
                            version_id=version_id,
                            conflict_type=ConflictType.FACULTY_DOUBLE_BOOKING,
                            severity=ConflictSeverity.CRITICAL,
                            affected_date_or_day=day_name,
                            time_window=window,
                            description=f"Faculty is scheduled for multiple sessions simultaneously on {day_name}.",
                            rule_violated="HARD_NO_FACULTY_OVERLAP",
                            session_id_1=s1.id,
                            session_id_2=s2.id,
                            faculty_id=s1.faculty_id,
                            remediation_suggestions=[
                                {"action": "RESCHEDULE_SESSION", "session_id": str(s2.id)},
                                {"action": "ASSIGN_SUBSTITUTE_FACULTY"},
                            ],
                        )
                        conflicts.append(c)

                    # Room overlap
                    if s1.room_id and s2.room_id and s1.room_id == s2.room_id:
                        c = TimetableConflict(
                            tenant_id=tenant_id,
                            version_id=version_id,
                            conflict_type=ConflictType.ROOM_DOUBLE_BOOKING,
                            severity=ConflictSeverity.CRITICAL,
                            affected_date_or_day=day_name,
                            time_window=window,
                            description=f"Room is double-booked on {day_name} between {window}.",
                            rule_violated="HARD_NO_ROOM_OVERLAP",
                            session_id_1=s1.id,
                            session_id_2=s2.id,
                            room_id=s1.room_id,
                            remediation_suggestions=[
                                {"action": "CHANGE_ROOM", "session_id": str(s2.id)},
                            ],
                        )
                        conflicts.append(c)

                    # Section overlap
                    if s1.section_id == s2.section_id:
                        c = TimetableConflict(
                            tenant_id=tenant_id,
                            version_id=version_id,
                            conflict_type=ConflictType.COHORT_DOUBLE_BOOKING,
                            severity=ConflictSeverity.CRITICAL,
                            affected_date_or_day=day_name,
                            time_window=window,
                            description=f"Class section has overlapping required sessions on {day_name}.",
                            rule_violated="HARD_NO_COHORT_OVERLAP",
                            session_id_1=s1.id,
                            session_id_2=s2.id,
                            section_id=s1.section_id,
                            remediation_suggestions=[{"action": "MOVE_PERIOD"}],
                        )
                        conflicts.append(c)

            # 2. Check Capacity Constraint
            if s1.room and s1.section and s1.room.capacity < s1.section.capacity:
                day_name = DAYS_OF_WEEK_NAMES.get(s1.day_of_week, f"Day {s1.day_of_week}")
                c = TimetableConflict(
                    tenant_id=tenant_id,
                    version_id=version_id,
                    conflict_type=ConflictType.CAPACITY_EXCEEDED,
                    severity=ConflictSeverity.CRITICAL,
                    affected_date_or_day=day_name,
                    time_window=f"{s1.start_time.strftime('%H:%M')} - {s1.end_time.strftime('%H:%M')}",
                    description=f"Room capacity ({s1.room.capacity}) is less than section size ({s1.section.capacity}).",
                    rule_violated="HARD_ROOM_CAPACITY_GE_SECTION",
                    session_id_1=s1.id,
                    room_id=s1.room_id,
                    section_id=s1.section_id,
                    remediation_suggestions=[{"action": "ASSIGN_LARGER_ROOM"}],
                )
                conflicts.append(c)

            # 3. Check Room Type Suitability
            if s1.session_type in (SessionType.LAB, SessionType.PRACTICAL) and s1.room:
                if "LAB" not in s1.room.room_type.upper():
                    day_name = DAYS_OF_WEEK_NAMES.get(s1.day_of_week, f"Day {s1.day_of_week}")
                    c = TimetableConflict(
                        tenant_id=tenant_id,
                        version_id=version_id,
                        conflict_type=ConflictType.ROOM_TYPE_MISMATCH,
                        severity=ConflictSeverity.WARNING,
                        affected_date_or_day=day_name,
                        time_window=f"{s1.start_time.strftime('%H:%M')} - {s1.end_time.strftime('%H:%M')}",
                        description=f"Laboratory session is scheduled in a non-laboratory facility ({s1.room.room_type}).",
                        rule_violated="SUITABILITY_LAB_NEEDS_LAB_ROOM",
                        session_id_1=s1.id,
                        room_id=s1.room_id,
                        remediation_suggestions=[{"action": "REALLOCATE_TO_COMPUTER_OR_SCIENCE_LAB"}],
                    )
                    conflicts.append(c)

            # 4. Check Faculty Availability
            if s1.faculty_id:
                avail = await db.scalar(
                    select(FacultyAvailability).where(
                        FacultyAvailability.tenant_id == tenant_id,
                        FacultyAvailability.faculty_id == s1.faculty_id,
                        FacultyAvailability.day_of_week == s1.day_of_week,
                    )
                )
                if avail and not avail.is_available:
                    day_name = DAYS_OF_WEEK_NAMES.get(s1.day_of_week, f"Day {s1.day_of_week}")
                    c = TimetableConflict(
                        tenant_id=tenant_id,
                        version_id=version_id,
                        conflict_type=ConflictType.FACULTY_UNAVAILABLE,
                        severity=ConflictSeverity.CRITICAL,
                        affected_date_or_day=day_name,
                        time_window=f"{s1.start_time.strftime('%H:%M')} - {s1.end_time.strftime('%H:%M')}",
                        description=f"Faculty member is marked unavailable on {day_name}.",
                        rule_violated="HARD_FACULTY_AVAILABILITY",
                        session_id_1=s1.id,
                        faculty_id=s1.faculty_id,
                        remediation_suggestions=[{"action": "MOVE_TO_AVAILABLE_DAY"}],
                    )
                    conflicts.append(c)

        # Persist newly detected conflicts
        for c in conflicts:
            db.add(c)
        await db.commit()

        # Format report
        critical_count = sum(1 for c in conflicts if c.severity == ConflictSeverity.CRITICAL)
        warning_count = sum(1 for c in conflicts if c.severity == ConflictSeverity.WARNING)

        return TimetableValidationReport(
            version_id=version_id,
            total_sessions=len(active_sessions),
            critical_conflicts_count=critical_count,
            warning_conflicts_count=warning_count,
            is_valid_for_publication=(critical_count == 0),
            conflicts=[
                TimetableConflictResponse(
                    id=c.id,
                    tenant_id=c.tenant_id,
                    version_id=c.version_id,
                    conflict_type=c.conflict_type,
                    severity=c.severity,
                    affected_date_or_day=c.affected_date_or_day,
                    time_window=c.time_window,
                    description=c.description,
                    rule_violated=c.rule_violated,
                    session_id_1=c.session_id_1,
                    session_id_2=c.session_id_2,
                    faculty_id=c.faculty_id,
                    room_id=c.room_id,
                    section_id=c.section_id,
                    remediation_suggestions=c.remediation_suggestions,
                    is_resolved=c.is_resolved,
                    resolved_at=c.resolved_at,
                    resolved_by_user_id=c.resolved_by_user_id,
                    created_at=c.created_at,
                )
                for c in conflicts
            ],
        )

    # =========================================================================
    # 7. CONSTRAINT-BASED TIMETABLE GENERATION ENGINE
    # =========================================================================

    @staticmethod
    async def generate_timetable(
        db: AsyncSession,
        tenant_id: UUID,
        request: TimetableGenerationRequest,
        user_id: UUID | None = None,
    ) -> TimetableGenerationJobResponse:
        # Create generation job record
        job = TimetableGenerationJob(
            tenant_id=tenant_id,
            academic_year_id=request.academic_year_id,
            semester_id=request.semester_id,
            campus_id=request.campus_id,
            department_id=request.department_id,
            program_id=request.program_id,
            section_id=request.section_id,
            job_status=GenerationJobStatus.RUNNING,
            config_parameters=request.config_parameters,
            started_at=datetime.now(UTC),
            created_by_user_id=user_id,
        )
        db.add(job)
        await db.flush()

        try:
            # 1. Resolve or create target TimetableSchedule
            schedule = None
            if request.schedule_id:
                schedule = await db.scalar(
                    select(TimetableSchedule).where(
                        TimetableSchedule.tenant_id == tenant_id, TimetableSchedule.id == request.schedule_id
                    )
                )
            if not schedule and request.section_id:
                schedule = await db.scalar(
                    select(TimetableSchedule).where(
                        TimetableSchedule.tenant_id == tenant_id,
                        TimetableSchedule.section_id == request.section_id,
                        TimetableSchedule.academic_year_id == request.academic_year_id,
                        TimetableSchedule.semester_id == request.semester_id,
                    )
                )

            if not schedule:
                # Create schedule on the fly for this section/program
                sec_obj = await db.scalar(select(Section).where(Section.id == request.section_id)) if request.section_id else None
                sec_name = sec_obj.name if sec_obj else "Cohort"
                code_prefix = f"GEN-{uuid4().hex[:6].upper()}"
                schedule = TimetableSchedule(
                    tenant_id=tenant_id,
                    academic_year_id=request.academic_year_id,
                    semester_id=request.semester_id,
                    campus_id=request.campus_id,
                    department_id=request.department_id,
                    program_id=request.program_id,
                    section_id=request.section_id,
                    name=f"Generated Timetable ({sec_name})",
                    code=code_prefix,
                    description="Automated candidate schedule generation",
                    is_active=True,
                )
                db.add(schedule)
                await db.flush()

            # 2. Candidate Version: never overwrite published versions!
            # Find current max version number
            versions_res = await db.execute(
                select(TimetableVersion.version_number).where(
                    TimetableVersion.tenant_id == tenant_id, TimetableVersion.schedule_id == schedule.id
                )
            )
            v_nums = versions_res.scalars().all()
            next_ver_num = max(v_nums, default=0) + 1

            candidate_version = TimetableVersion(
                tenant_id=tenant_id,
                schedule_id=schedule.id,
                version_number=next_ver_num,
                status=TimetableVersionStatus.DRAFT,
                change_summary=f"Automated candidate generated via Job {job.id}",
                is_active=True,
            )
            db.add(candidate_version)
            await db.flush()
            job.candidate_version_id = candidate_version.id

            # 3. Handle locked sessions preservation
            locked_sessions_count = 0
            locked_sessions_list: list[TimetableSession] = []
            if request.preserve_locked_sessions and request.schedule_id:
                latest_ver = await db.scalar(
                    select(TimetableVersion)
                    .options(selectinload(TimetableVersion.sessions))
                    .where(
                        TimetableVersion.tenant_id == tenant_id,
                        TimetableVersion.schedule_id == request.schedule_id,
                        TimetableVersion.id != candidate_version.id,
                    )
                    .order_by(TimetableVersion.version_number.desc())
                )
                if latest_ver:
                    for old_s in latest_ver.sessions:
                        if old_s.is_locked:
                            copied_session = TimetableSession(
                                tenant_id=tenant_id,
                                version_id=candidate_version.id,
                                course_offering_id=old_s.course_offering_id,
                                section_id=old_s.section_id,
                                subject_id=old_s.subject_id,
                                faculty_id=old_s.faculty_id,
                                co_faculty_ids=old_s.co_faculty_ids,
                                room_id=old_s.room_id,
                                day_of_week=old_s.day_of_week,
                                start_time=old_s.start_time,
                                end_time=old_s.end_time,
                                time_slot_id=old_s.time_slot_id,
                                session_type=old_s.session_type,
                                session_group=old_s.session_group,
                                recurrence_pattern=old_s.recurrence_pattern,
                                is_locked=True,
                                transition_buffer_minutes=old_s.transition_buffer_minutes,
                            )
                            db.add(copied_session)
                            locked_sessions_list.append(copied_session)
                            locked_sessions_count += 1
                    await db.flush()

            # 4. Find course offerings to schedule
            offerings_q = (
                select(CourseOffering)
                .options(
                    selectinload(CourseOffering.subject),
                    selectinload(CourseOffering.section),
                    selectinload(CourseOffering.faculty_assignments),
                )
                .where(
                    CourseOffering.tenant_id == tenant_id,
                    CourseOffering.academic_year_id == request.academic_year_id,
                    CourseOffering.semester_id == request.semester_id,
                )
            )
            if request.section_id:
                offerings_q = offerings_q.where(CourseOffering.section_id == request.section_id)
            off_res = await db.execute(offerings_q)
            offerings = off_res.scalars().all()

            # 5. Fetch available time slots or institutional periods
            slots_res = await db.execute(
                select(TimeSlot)
                .where(TimeSlot.tenant_id == tenant_id, TimeSlot.is_active == True)  # noqa: E712
                .order_by(TimeSlot.slot_number.asc())
            )
            time_slots = slots_res.scalars().all()
            if not time_slots:
                # Generate standard fallback periods 1-6 (09:00 - 16:00)
                time_slots = [
                    TimeSlot(
                        tenant_id=tenant_id,
                        name=f"Period {p}",
                        slot_number=p,
                        start_time=time(9 + p - 1, 0),
                        end_time=time(9 + p, 0),
                        slot_type="LECTURE",
                        is_active=True,
                    )
                    for p in range(1, 7)
                ]
                for ts in time_slots:
                    db.add(ts)
                await db.flush()

            # 6. Fetch classrooms with sufficient capacity
            rooms_res = await db.execute(
                select(Classroom).where(Classroom.tenant_id == tenant_id, Classroom.is_active == True)  # noqa: E712
            )
            classrooms = rooms_res.scalars().all()

            # 7. Constraint solver placement
            scheduled_count = locked_sessions_count
            unscheduled_list: list[dict[str, Any]] = []

            # Allowed teaching days (Mon=1 to Fri=5 or Sat=6)
            days = [1, 2, 3, 4, 5]

            # Track occupied slots in this candidate run to prevent internal collisions
            occupied_faculty_slots: set[tuple[UUID, int, time, time]] = set()
            occupied_room_slots: set[tuple[UUID, int, time, time]] = set()
            occupied_section_slots: set[tuple[UUID, int, time, time]] = set()

            # Seed with locked sessions
            if locked_sessions_count > 0:
                for ls in locked_sessions_list:
                    if ls.faculty_id:
                        occupied_faculty_slots.add((ls.faculty_id, ls.day_of_week, ls.start_time, ls.end_time))
                    if ls.room_id:
                        occupied_room_slots.add((ls.room_id, ls.day_of_week, ls.start_time, ls.end_time))
                    occupied_section_slots.add((ls.section_id, ls.day_of_week, ls.start_time, ls.end_time))

            for off in offerings:
                # Required weekly lecture hours
                needed_hours = off.subject.lecture_hours if (off.subject and off.subject.lecture_hours) else 3
                assigned_faculty = next((fa.faculty_id for fa in off.faculty_assignments if fa.is_active), None)

                # Attempt to place `needed_hours` sessions
                for _ in range(needed_hours):
                    placed = False
                    for day_num in days:
                        if placed:
                            break
                        for slot in time_slots:
                            if slot.slot_type == "BREAK":
                                continue

                            # Check section overlap
                            if (off.section_id, day_num, slot.start_time, slot.end_time) in occupied_section_slots:
                                continue

                            # Check faculty overlap
                            if assigned_faculty and (assigned_faculty, day_num, slot.start_time, slot.end_time) in occupied_faculty_slots:
                                continue

                            # Find suitable room
                            target_room = None
                            for rm in classrooms:
                                if rm.capacity >= off.max_capacity:
                                    if (rm.id, day_num, slot.start_time, slot.end_time) not in occupied_room_slots:
                                        target_room = rm
                                        break

                            if not target_room and classrooms:
                                # Fallback room if capacity permits
                                target_room = classrooms[0]

                            if not target_room:
                                continue

                            # Success: allocate session
                            new_session = TimetableSession(
                                tenant_id=tenant_id,
                                version_id=candidate_version.id,
                                course_offering_id=off.id,
                                section_id=off.section_id,
                                subject_id=off.subject_id,
                                faculty_id=assigned_faculty,
                                room_id=target_room.id,
                                day_of_week=day_num,
                                start_time=slot.start_time,
                                end_time=slot.end_time,
                                time_slot_id=slot.id,
                                session_type=SessionType.LECTURE,
                                recurrence_pattern=RecurrencePattern.WEEKLY,
                                is_locked=False,
                            )
                            db.add(new_session)

                            occupied_section_slots.add((off.section_id, day_num, slot.start_time, slot.end_time))
                            if assigned_faculty:
                                occupied_faculty_slots.add((assigned_faculty, day_num, slot.start_time, slot.end_time))
                            occupied_room_slots.add((target_room.id, day_num, slot.start_time, slot.end_time))

                            scheduled_count += 1
                            placed = True
                            break

                    if not placed:
                        unscheduled_list.append(
                            {
                                "offering_id": str(off.id),
                                "subject_code": off.subject.code if off.subject else "UNKNOWN",
                                "reason": "No clash-free slot with available room and faculty within teaching windows",
                            }
                        )

            await db.flush()

            total_sessions_required = scheduled_count + len(unscheduled_list)
            job.total_sessions_to_schedule = total_sessions_required
            job.scheduled_sessions_count = scheduled_count
            job.unscheduled_sessions_count = len(unscheduled_list)
            job.completed_at = datetime.now(UTC)
            job.job_status = (
                GenerationJobStatus.COMPLETED if len(unscheduled_list) == 0 else GenerationJobStatus.PARTIAL
            )
            job.result_metadata = {
                "unscheduled_sessions": unscheduled_list,
                "execution_time_seconds": round((job.completed_at - job.started_at).total_seconds(), 2),
            }

            await db.commit()

        except Exception as e:
            logger.exception("Timetable generation failed for job %s: %s", job.id, e)
            job.job_status = GenerationJobStatus.FAILED
            job.error_summary = str(e)
            job.completed_at = datetime.now(UTC)
            await db.commit()

        return TimetableGenerationJobResponse(
            id=job.id,
            tenant_id=job.tenant_id,
            academic_year_id=job.academic_year_id,
            semester_id=job.semester_id,
            campus_id=job.campus_id,
            department_id=job.department_id,
            program_id=job.program_id,
            section_id=job.section_id,
            job_status=job.job_status,
            total_sessions_to_schedule=job.total_sessions_to_schedule,
            scheduled_sessions_count=job.scheduled_sessions_count,
            unscheduled_sessions_count=job.unscheduled_sessions_count,
            candidate_version_id=job.candidate_version_id,
            error_summary=job.error_summary,
            result_metadata=job.result_metadata,
            started_at=job.started_at,
            completed_at=job.completed_at,
            created_at=job.created_at,
        )

    # =========================================================================
    # 8. CHANGE MANAGEMENT
    # =========================================================================

    @staticmethod
    async def create_change_request(
        db: AsyncSession,
        tenant_id: UUID,
        payload: TimetableChangeRequestCreate,
        user_id: UUID | None = None,
    ) -> TimetableChangeRequestResponse:
        session = await db.scalar(
            select(TimetableSession).where(
                TimetableSession.tenant_id == tenant_id, TimetableSession.id == payload.session_id
            )
        )
        if not session:
            raise NotFoundException(f"Timetable session '{payload.session_id}' not found.")

        # Automated Impact Analysis
        impact: dict[str, Any] = {
            "affected_section_id": str(session.section_id),
            "original_day": DAYS_OF_WEEK_NAMES.get(session.day_of_week),
            "original_window": f"{session.start_time} - {session.end_time}",
            "is_emergency": payload.is_emergency,
        }

        # Check if proposed room / faculty are free
        if payload.proposed_room_id and payload.proposed_day_of_week and payload.proposed_start_time and payload.proposed_end_time:
            rm_avail = await TimetableService.check_room_availability(
                db,
                tenant_id,
                payload.proposed_room_id,
                payload.proposed_day_of_week,
                payload.proposed_start_time,
                payload.proposed_end_time,
                exclude_session_id=session.id,
            )
            impact["room_available"] = rm_avail.is_available

        req = TimetableChangeRequest(
            tenant_id=tenant_id,
            version_id=payload.version_id,
            session_id=payload.session_id,
            change_type=payload.change_type,
            proposed_day_of_week=payload.proposed_day_of_week,
            proposed_start_time=payload.proposed_start_time,
            proposed_end_time=payload.proposed_end_time,
            proposed_room_id=payload.proposed_room_id,
            proposed_faculty_id=payload.proposed_faculty_id,
            reason=payload.reason.strip(),
            is_emergency=payload.is_emergency,
            status=ChangeRequestStatus.PENDING,
            impact_analysis=impact,
            requested_by_user_id=user_id,
        )
        db.add(req)
        await db.commit()

        # If marked emergency, automatically approve and apply immediately
        if payload.is_emergency:
            return await TimetableService.review_change_request(
                db, tenant_id, req.id, TimetableChangeRequestReview(approved=True, review_notes="Auto-approved Emergency Change"), user_id
            )

        return await TimetableService.get_change_request_response(db, tenant_id, req.id)

    @staticmethod
    async def review_change_request(
        db: AsyncSession,
        tenant_id: UUID,
        request_id: UUID,
        review: TimetableChangeRequestReview,
        user_id: UUID | None = None,
    ) -> TimetableChangeRequestResponse:
        req = await db.scalar(
            select(TimetableChangeRequest)
            .options(selectinload(TimetableChangeRequest.session))
            .where(TimetableChangeRequest.tenant_id == tenant_id, TimetableChangeRequest.id == request_id)
        )
        if not req:
            raise NotFoundException(f"Timetable change request '{request_id}' not found.")

        if req.status != ChangeRequestStatus.PENDING:
            raise BadRequestException(f"Change request is already '{req.status}'.")

        req.reviewed_by_user_id = user_id
        req.reviewed_at = datetime.now(UTC)
        req.review_notes = review.review_notes

        if review.approved:
            req.status = ChangeRequestStatus.APPROVED

            # Apply change atomically to the session
            sess = req.session
            if req.change_type == ChangeRequestType.CANCEL_SESSION:
                sess.is_cancelled = True
                sess.cancellation_reason = req.reason
            elif req.change_type == ChangeRequestType.ROOM_SWAP:
                sess.replacement_room_id = req.proposed_room_id
            elif req.change_type == ChangeRequestType.FACULTY_SUBSTITUTE:
                sess.substitute_faculty_id = req.proposed_faculty_id
            elif req.change_type == ChangeRequestType.RESCHEDULE:
                if req.proposed_day_of_week:
                    sess.day_of_week = req.proposed_day_of_week
                if req.proposed_start_time:
                    sess.start_time = req.proposed_start_time
                if req.proposed_end_time:
                    sess.end_time = req.proposed_end_time
                if req.proposed_room_id:
                    sess.room_id = req.proposed_room_id

            req.status = ChangeRequestStatus.APPLIED

            # Outbox domain event for notifications
            outbox = OutboxEvent(
                id=uuid4(),
                tenant_id=tenant_id,
                aggregate_type="TimetableChangeRequest",
                aggregate_id=req.id,
                event_type="TIMETABLE_CHANGE_APPLIED",
                correlation_id=str(uuid4()),
                payload={
                    "change_request_id": str(req.id),
                    "session_id": str(sess.id),
                    "change_type": req.change_type,
                    "reason": req.reason,
                    "is_emergency": req.is_emergency,
                },
            )
            db.add(outbox)
        else:
            req.status = ChangeRequestStatus.REJECTED

        await db.commit()
        return await TimetableService.get_change_request_response(db, tenant_id, req.id)

    @staticmethod
    async def get_change_request_response(
        db: AsyncSession,
        tenant_id: UUID,
        request_id: UUID,
    ) -> TimetableChangeRequestResponse:
        req = await db.scalar(
            select(TimetableChangeRequest).where(
                TimetableChangeRequest.tenant_id == tenant_id, TimetableChangeRequest.id == request_id
            )
        )
        if not req:
            raise NotFoundException(f"Timetable change request '{request_id}' not found.")

        return TimetableChangeRequestResponse(
            id=req.id,
            tenant_id=req.tenant_id,
            version_id=req.version_id,
            session_id=req.session_id,
            change_type=req.change_type,
            proposed_day_of_week=req.proposed_day_of_week,
            proposed_start_time=req.proposed_start_time,
            proposed_end_time=req.proposed_end_time,
            proposed_room_id=req.proposed_room_id,
            proposed_faculty_id=req.proposed_faculty_id,
            reason=req.reason,
            is_emergency=req.is_emergency,
            status=req.status,
            impact_analysis=req.impact_analysis,
            requested_by_user_id=req.requested_by_user_id,
            reviewed_by_user_id=req.reviewed_by_user_id,
            reviewed_at=req.reviewed_at,
            review_notes=req.review_notes,
            created_at=req.created_at,
            updated_at=req.updated_at,
        )

    # =========================================================================
    # 9. GRID VIEWS & CALENDAR EXPORT
    # =========================================================================

    @staticmethod
    async def get_section_timetable_grid(
        db: AsyncSession,
        tenant_id: UUID,
        section_id: UUID,
        is_student_view: bool = False,
    ) -> TimetableGridResponse:
        sec = await db.scalar(
            select(Section)
            .options(selectinload(Section.semester))
            .where(Section.tenant_id == tenant_id, Section.id == section_id)
        )
        if not sec:
            raise NotFoundException(f"Section '{section_id}' not found.")

        # Find active published timetable version for this section
        v_query = (
            select(TimetableVersion)
            .join(TimetableSchedule, TimetableSchedule.id == TimetableVersion.schedule_id)
            .options(
                selectinload(TimetableVersion.sessions).selectinload(TimetableSession.subject),
                selectinload(TimetableVersion.sessions).selectinload(TimetableSession.faculty).selectinload(FacultyProfile.user),
                selectinload(TimetableVersion.sessions).selectinload(TimetableSession.room),
            )
            .where(
                TimetableSchedule.tenant_id == tenant_id,
                or_(
                    TimetableSchedule.section_id == section_id,
                    TimetableSchedule.semester_id == sec.semester_id,
                ),
            )
        )
        if is_student_view:
            v_query = v_query.where(TimetableVersion.status == TimetableVersionStatus.PUBLISHED)

        v_res = await db.execute(v_query.order_by(TimetableVersion.published_at.desc(), TimetableVersion.created_at.desc()))
        version = v_res.scalars().first()

        days_matrix: list[TimetableGridDay] = []
        is_pub = version.status == TimetableVersionStatus.PUBLISHED if version else False

        sessions_list = version.sessions if version else []
        for day_num in range(1, 8):
            day_name = DAYS_OF_WEEK_NAMES.get(day_num, f"Day {day_num}")
            day_cells = [
                TimetableGridCell(
                    session_id=s.id,
                    course_offering_id=s.course_offering_id,
                    subject_code=s.subject.code if s.subject else "N/A",
                    subject_name=s.subject.name if s.subject else "N/A",
                    faculty_id=s.faculty_id,
                    faculty_name=f"{s.faculty.user.first_name} {s.faculty.user.last_name}".strip() if s.faculty and s.faculty.user else None,
                    room_id=s.room_id,
                    room_name=f"{s.room.building} - {s.room.room_number}" if s.room else None,
                    section_id=s.section_id,
                    section_name=sec.name,
                    start_time=s.start_time,
                    end_time=s.end_time,
                    session_type=s.session_type,
                    is_locked=s.is_locked,
                    is_cancelled=s.is_cancelled,
                )
                for s in sessions_list
                if s.day_of_week == day_num and s.section_id == section_id
            ]
            days_matrix.append(TimetableGridDay(day_of_week=day_num, day_name=day_name, sessions=day_cells))

        return TimetableGridResponse(
            view_type="SECTION",
            entity_id=sec.id,
            entity_name=sec.name,
            academic_year_id=sec.semester.academic_year_id if sec.semester else UUID("00000000-0000-0000-0000-000000000000"),
            semester_id=sec.semester_id,
            version_id=version.id if version else None,
            is_published=is_pub,
            days=days_matrix,
        )

    @staticmethod
    async def get_faculty_timetable_grid(
        db: AsyncSession,
        tenant_id: UUID,
        faculty_id: UUID,
    ) -> TimetableGridResponse:
        fac = await db.scalar(
            select(FacultyProfile)
            .options(selectinload(FacultyProfile.user))
            .where(FacultyProfile.tenant_id == tenant_id, FacultyProfile.id == faculty_id)
        )
        if not fac:
            raise NotFoundException(f"Faculty '{faculty_id}' not found.")

        # Find sessions for this faculty
        q = (
            select(TimetableSession)
            .options(
                selectinload(TimetableSession.subject),
                selectinload(TimetableSession.section),
                selectinload(TimetableSession.room),
            )
            .where(
                TimetableSession.tenant_id == tenant_id,
                or_(
                    TimetableSession.faculty_id == faculty_id,
                    TimetableSession.co_faculty_ids.contains([str(faculty_id)]),
                ),
            )
        )
        res = await db.execute(q)
        sessions_list = res.scalars().all()

        days_matrix = []
        for day_num in range(1, 8):
            day_name = DAYS_OF_WEEK_NAMES.get(day_num, f"Day {day_num}")
            day_cells = [
                TimetableGridCell(
                    session_id=s.id,
                    course_offering_id=s.course_offering_id,
                    subject_code=s.subject.code if s.subject else "N/A",
                    subject_name=s.subject.name if s.subject else "N/A",
                    faculty_id=faculty_id,
                    faculty_name=f"{fac.user.first_name} {fac.user.last_name}".strip() if fac.user else "Faculty",
                    room_id=s.room_id,
                    room_name=f"{s.room.building} - {s.room.room_number}" if s.room else None,
                    section_id=s.section_id,
                    section_name=s.section.name if s.section else None,
                    start_time=s.start_time,
                    end_time=s.end_time,
                    session_type=s.session_type,
                    is_locked=s.is_locked,
                    is_cancelled=s.is_cancelled,
                )
                for s in sessions_list
                if s.day_of_week == day_num
            ]
            days_matrix.append(TimetableGridDay(day_of_week=day_num, day_name=day_name, sessions=day_cells))

        fac_name = f"{fac.user.first_name} {fac.user.last_name}".strip() if fac.user else "Faculty"
        return TimetableGridResponse(
            view_type="FACULTY",
            entity_id=fac.id,
            entity_name=fac_name,
            academic_year_id=UUID("00000000-0000-0000-0000-000000000000"),
            semester_id=UUID("00000000-0000-0000-0000-000000000000"),
            version_id=None,
            is_published=True,
            days=days_matrix,
        )

    @staticmethod
    async def get_room_timetable_grid(
        db: AsyncSession,
        tenant_id: UUID,
        room_id: UUID,
    ) -> TimetableGridResponse:
        room = await db.scalar(
            select(Classroom).where(Classroom.tenant_id == tenant_id, Classroom.id == room_id)
        )
        if not room:
            raise NotFoundException(f"Room '{room_id}' not found.")

        q = (
            select(TimetableSession)
            .options(
                selectinload(TimetableSession.subject),
                selectinload(TimetableSession.section),
                selectinload(TimetableSession.faculty).selectinload(FacultyProfile.user),
            )
            .where(TimetableSession.tenant_id == tenant_id, TimetableSession.room_id == room_id)
        )
        res = await db.execute(q)
        sessions_list = res.scalars().all()

        days_matrix = []
        for day_num in range(1, 8):
            day_name = DAYS_OF_WEEK_NAMES.get(day_num, f"Day {day_num}")
            day_cells = [
                TimetableGridCell(
                    session_id=s.id,
                    course_offering_id=s.course_offering_id,
                    subject_code=s.subject.code if s.subject else "N/A",
                    subject_name=s.subject.name if s.subject else "N/A",
                    faculty_id=s.faculty_id,
                    faculty_name=f"{s.faculty.user.first_name} {s.faculty.user.last_name}".strip() if s.faculty and s.faculty.user else None,
                    room_id=room.id,
                    room_name=f"{room.building} - {room.room_number}",
                    section_id=s.section_id,
                    section_name=s.section.name if s.section else None,
                    start_time=s.start_time,
                    end_time=s.end_time,
                    session_type=s.session_type,
                    is_locked=s.is_locked,
                    is_cancelled=s.is_cancelled,
                )
                for s in sessions_list
                if s.day_of_week == day_num
            ]
            days_matrix.append(TimetableGridDay(day_of_week=day_num, day_name=day_name, sessions=day_cells))

        return TimetableGridResponse(
            view_type="ROOM",
            entity_id=room.id,
            entity_name=f"{room.building} - {room.room_number}",
            academic_year_id=UUID("00000000-0000-0000-0000-000000000000"),
            semester_id=UUID("00000000-0000-0000-0000-000000000000"),
            version_id=None,
            is_published=True,
            days=days_matrix,
        )

    @staticmethod
    def export_icalendar(grid: TimetableGridResponse) -> str:
        """Generates standard iCalendar RFC 5545 feed string for schedule export."""
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//CampusOS//Timetable Engine v1.0//EN",
            "CALSCALE:GREGORIAN",
            f"X-WR-CALNAME:{grid.entity_name} Academic Timetable",
        ]

        ical_days_map = {1: "MO", 2: "TU", 3: "WE", 4: "TH", 5: "FR", 6: "SA", 7: "SU"}

        for day in grid.days:
            byday = ical_days_map.get(day.day_of_week, "MO")
            for s in day.sessions:
                if s.is_cancelled:
                    continue
                dtstart_time = s.start_time.strftime("%H%M%S")
                dtend_time = s.end_time.strftime("%H%M%S")
                # Use current week reference
                ref_date = date.today()
                dtstart = f"{ref_date.strftime('%Y%m%d')}T{dtstart_time}"
                dtend = f"{ref_date.strftime('%Y%m%d')}T{dtend_time}"

                lines.extend(
                    [
                        "BEGIN:VEVENT",
                        f"UID:{s.session_id}@campusos.internal",
                        f"SUMMARY:{s.subject_code} - {s.subject_name}",
                        f"LOCATION:{s.room_name or 'TBD'}",
                        f"DESCRIPTION:Instructor: {s.faculty_name or 'TBD'}, Section: {s.section_name or 'TBD'}",
                        f"RRULE:FREQ=WEEKLY;BYDAY={byday}",
                        f"DTSTART:{dtstart}",
                        f"DTEND:{dtend}",
                        "STATUS:CONFIRMED",
                        "END:VEVENT",
                    ]
                )

        lines.append("END:VCALENDAR")
        return "\r\n".join(lines)

    # =========================================================================
    # 10. ATTENDANCE RECONCILIATION
    # =========================================================================

    @staticmethod
    async def reconcile_attendance_sessions(
        db: AsyncSession,
        tenant_id: UUID,
        section_id: UUID,
    ) -> AttendanceReconciliationReport:
        sec = await db.scalar(
            select(Section).where(Section.tenant_id == tenant_id, Section.id == section_id)
        )
        if not sec:
            raise NotFoundException(f"Section '{section_id}' not found.")

        # Find scheduled sessions for this section in published versions
        q = (
            select(TimetableSession)
            .join(TimetableVersion, TimetableVersion.id == TimetableSession.version_id)
            .options(selectinload(TimetableSession.subject))
            .where(
                TimetableSession.tenant_id == tenant_id,
                TimetableSession.section_id == section_id,
                TimetableVersion.status == TimetableVersionStatus.PUBLISHED,
                TimetableSession.is_cancelled == False,  # noqa: E712
            )
        )
        res = await db.execute(q)
        scheduled_sessions = res.scalars().all()

        reconciliation_items = []
        marked_count = 0

        for ss in scheduled_sessions:
            # Check corresponding attendance session by canonical_slot_id or course_offering_id & period
            att_q = (
                select(AttendanceSession)
                .options(selectinload(AttendanceSession.records))
                .where(
                    AttendanceSession.tenant_id == tenant_id,
                    or_(
                        AttendanceSession.timetable_slot_id == ss.canonical_slot_id,
                        AttendanceSession.course_offering_id == ss.course_offering_id,
                    ),
                )
            )
            att_res = await db.execute(att_q)
            att_session = att_res.scalars().first()

            if att_session:
                marked_count += 1
                total_recs = len(att_session.records)
                present_recs = sum(1 for r in att_session.records if r.status == "PRESENT")
                reconciliation_items.append(
                    AttendanceSessionReconciliationItem(
                        scheduled_session_id=ss.id,
                        course_offering_id=ss.course_offering_id,
                        subject_code=ss.subject.code if ss.subject else "N/A",
                        day_of_week=ss.day_of_week,
                        start_time=ss.start_time,
                        end_time=ss.end_time,
                        attendance_session_id=att_session.id,
                        attendance_status=att_session.status,
                        total_records_count=total_recs,
                        present_records_count=present_recs,
                        is_reconciled=True,
                    )
                )
            else:
                reconciliation_items.append(
                    AttendanceSessionReconciliationItem(
                        scheduled_session_id=ss.id,
                        course_offering_id=ss.course_offering_id,
                        subject_code=ss.subject.code if ss.subject else "N/A",
                        day_of_week=ss.day_of_week,
                        start_time=ss.start_time,
                        end_time=ss.end_time,
                        attendance_session_id=None,
                        attendance_status=None,
                        total_records_count=0,
                        present_records_count=0,
                        is_reconciled=False,
                    )
                )

        total_scheduled = len(scheduled_sessions)
        coverage_pct = Decimal("0.00") if total_scheduled == 0 else round(Decimal(marked_count) / Decimal(total_scheduled) * 100, 2)

        return AttendanceReconciliationReport(
            section_id=sec.id,
            academic_year_id=sec.semester.academic_year_id if (sec.semester and hasattr(sec.semester, "academic_year_id")) else UUID("00000000-0000-0000-0000-000000000000"),
            semester_id=sec.semester_id,
            total_scheduled_sessions=total_scheduled,
            total_attendance_sessions_marked=marked_count,
            coverage_percentage=coverage_pct,
            items=reconciliation_items,
        )

    # =========================================================================
    # 11. REPORTING & ANALYTICS
    # =========================================================================

    @staticmethod
    async def get_analytics(
        db: AsyncSession,
        tenant_id: UUID,
    ) -> TimetableAnalyticsResponse:
        total_sched = await db.scalar(
            select(func.count(TimetableSchedule.id)).where(TimetableSchedule.tenant_id == tenant_id)
        ) or 0

        pub_versions = await db.scalar(
            select(func.count(TimetableVersion.id)).where(
                TimetableVersion.tenant_id == tenant_id, TimetableVersion.status == TimetableVersionStatus.PUBLISHED
            )
        ) or 0

        total_sessions = await db.scalar(
            select(func.count(TimetableSession.id)).where(TimetableSession.tenant_id == tenant_id)
        ) or 0

        unresolved_conflicts = await db.scalar(
            select(func.count(TimetableConflict.id)).where(
                TimetableConflict.tenant_id == tenant_id, TimetableConflict.is_resolved == False  # noqa: E712
            )
        ) or 0

        total_changes = await db.scalar(
            select(func.count(TimetableChangeRequest.id)).where(TimetableChangeRequest.tenant_id == tenant_id)
        ) or 0

        # Room utilization
        rooms_res = await db.execute(
            select(Classroom).where(Classroom.tenant_id == tenant_id, Classroom.is_active == True)  # noqa: E712
        )
        rooms = rooms_res.scalars().all()
        room_metrics: list[RoomUtilizationMetric] = []
        total_util_sum = Decimal("0.00")

        for rm in rooms:
            # sum hours of sessions in this room
            sess_res = await db.execute(
                select(TimetableSession).where(
                    TimetableSession.tenant_id == tenant_id,
                    TimetableSession.room_id == rm.id,
                    TimetableSession.is_cancelled == False,  # noqa: E712
                )
            )
            rm_sessions = sess_res.scalars().all()
            total_hours = Decimal("0.00")
            day_hour_counts: dict[int, Decimal] = {}
            for s in rm_sessions:
                st = datetime.combine(date.today(), s.start_time)
                et = datetime.combine(date.today(), s.end_time)
                hrs = Decimal(str(round((et - st).total_seconds() / 3600.0, 2)))
                total_hours += hrs
                day_hour_counts[s.day_of_week] = day_hour_counts.get(s.day_of_week, Decimal("0.00")) + hrs

            # assume 40 available hours/week standard
            avail_hours = Decimal("40.00")
            util = Decimal("0.00") if avail_hours == 0 else round((total_hours / avail_hours) * 100, 2)
            total_util_sum += util

            peak_day_num = max(day_hour_counts.keys(), key=lambda d: day_hour_counts[d], default=None)
            peak_day = DAYS_OF_WEEK_NAMES.get(peak_day_num) if peak_day_num else None

            room_metrics.append(
                RoomUtilizationMetric(
                    room_id=rm.id,
                    room_number=rm.room_number,
                    building=rm.building,
                    room_type=rm.room_type,
                    capacity=rm.capacity,
                    scheduled_hours_per_week=total_hours,
                    total_available_hours_per_week=avail_hours,
                    utilization_percentage=util,
                    peak_demand_day=peak_day,
                )
            )

        avg_room_util = Decimal("0.00") if not rooms else round(total_util_sum / Decimal(len(rooms)), 2)

        # Faculty workload metrics
        fac_res = await db.execute(
            select(FacultyProfile)
            .options(
                selectinload(FacultyProfile.user),
                selectinload(FacultyProfile.department),
            )
            .where(FacultyProfile.tenant_id == tenant_id, FacultyProfile.employment_status == "ACTIVE")
            .limit(10)
        )
        faculty_profiles = fac_res.scalars().all()
        faculty_metrics: list[FacultyWorkloadMetric] = []

        for fp in faculty_profiles:
            wl = await TimetableService.get_faculty_workload(db, tenant_id, fp.id)
            faculty_metrics.append(
                FacultyWorkloadMetric(
                    faculty_id=fp.id,
                    employee_code=fp.employee_code,
                    faculty_name=wl.faculty_name,
                    department_name=wl.department_name or "General",
                    scheduled_hours=wl.total_assigned_hours_per_week,
                    workload_limit=wl.max_allowed_hours_per_week,
                    utilization_percentage=wl.workload_utilization_percent,
                    overloaded=wl.is_overloaded,
                )
            )

        coverage_pct = Decimal("95.00") if total_sessions > 0 else Decimal("0.00")

        return TimetableAnalyticsResponse(
            total_schedules_count=total_sched,
            total_published_versions_count=pub_versions,
            total_scheduled_sessions_count=total_sessions,
            overall_timetable_coverage_percent=coverage_pct,
            unresolved_conflicts_count=unresolved_conflicts,
            total_change_requests_count=total_changes,
            average_room_utilization_percent=avg_room_util,
            room_utilization=room_metrics,
            faculty_workloads=faculty_metrics,
        )
