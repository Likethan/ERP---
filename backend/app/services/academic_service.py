"""Academic domain business logic service.

Covers:
- Subject Master
- Curriculum Versioning & Publishing
- Classrooms & Time Slots
- Course Offerings & Lifecycles
- Faculty Assignments
- Student Course Enrollments (Single & Section Batch)
- Timetable Engine with Multi-Dimensional Conflict Detection (Faculty, Section, Room)
"""

import uuid
from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.models.academics import (
    Classroom,
    CourseEnrollment,
    CourseFacultyAssignment,
    CourseOffering,
    CurriculumScheme,
    CurriculumSubject,
    Subject,
    TimeSlot,
    TimetableEntry,
)
from app.models.audit import AuditLog
from app.models.core import AcademicYear, Department, Program, Regulation, Section, Semester
from app.models.people import FacultyProfile, StudentProfile
from app.schemas.academics import (
    ClassroomCreateRequest,
    ClassroomResponse,
    CourseBatchEnrollRequest,
    CourseEnrollmentCreateRequest,
    CourseEnrollmentResponse,
    CourseFacultyAssignmentCreateRequest,
    CourseFacultyAssignmentResponse,
    CourseOfferingCreateRequest,
    CourseOfferingDetailResponse,
    CourseOfferingResponse,
    CurriculumCreateRequest,
    CurriculumDetailResponse,
    CurriculumResponse,
    CurriculumSubjectCreateRequest,
    CurriculumSubjectResponse,
    CurriculumUpdateRequest,
    SubjectCreateRequest,
    SubjectResponse,
    SubjectUpdateRequest,
    TimeSlotCreateRequest,
    TimeSlotResponse,
    TimetableEntryCreateRequest,
    TimetableEntryResponse,
    TimetableEntryUpdateRequest,
    TimetableGridCell,
    TimetableGridDay,
    TimetableSectionGridResponse,
)

DAYS_OF_WEEK_NAMES = {
    1: "Monday",
    2: "Tuesday",
    3: "Wednesday",
    4: "Thursday",
    5: "Friday",
    6: "Saturday",
    7: "Sunday",
}

VALID_OFFERING_STATUS_TRANSITIONS: dict[str, set[str]] = {
    "PLANNED": {"OPEN", "CANCELLED"},
    "OPEN": {"ACTIVE", "CANCELLED"},
    "ACTIVE": {"COMPLETED", "CANCELLED"},
    "COMPLETED": set(),
    "CANCELLED": set(),
}


class AcademicService:
    @staticmethod
    def _create_audit(
        tenant_id: UUID,
        user_id: UUID | None,
        action: str,
        entity_type: str,
        entity_id: UUID,
        details: dict | None = None,
        ip_address: str = "127.0.0.1",
        business_context: str | None = None,
    ) -> AuditLog:
        return AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            new_values_json=details,
            ip_address=ip_address or "127.0.0.1",
            business_context=business_context,
        )

    # -------------------------------------------------------------------------
    # 1. SUBJECT MASTER
    # -------------------------------------------------------------------------
    @staticmethod
    async def list_subjects(
        db: AsyncSession,
        tenant_id: UUID,
        department_id: UUID | None = None,
        subject_type: str | None = None,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> list[SubjectResponse]:
        query = (
            select(Subject)
            .options(selectinload(Subject.department))
            .where(Subject.tenant_id == tenant_id)
            .order_by(Subject.code.asc())
        )

        if department_id:
            query = query.where(Subject.department_id == department_id)
        if subject_type:
            query = query.where(Subject.subject_type == subject_type.upper())
        if is_active is not None:
            query = query.where(Subject.is_active == is_active)
        if search:
            pattern = f"%{search.strip()}%"
            query = query.where((Subject.code.ilike(pattern)) | (Subject.name.ilike(pattern)))

        result = await db.execute(query)
        subjects = result.scalars().all()

        return [
            SubjectResponse(
                id=s.id,
                tenant_id=s.tenant_id,
                department_id=s.department_id,
                department_name=s.department.name if s.department else None,
                code=s.code,
                name=s.name,
                credits=s.credits,
                lecture_hours=s.lecture_hours,
                tutorial_hours=s.tutorial_hours,
                practical_hours=s.practical_hours,
                subject_type=s.subject_type,
                description=s.description,
                is_active=s.is_active,
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
            for s in subjects
        ]

    @staticmethod
    async def get_subject_response(
        db: AsyncSession, tenant_id: UUID, subject_id: UUID
    ) -> SubjectResponse:
        query = (
            select(Subject)
            .options(selectinload(Subject.department))
            .where(Subject.tenant_id == tenant_id, Subject.id == subject_id)
        )
        res = await db.execute(query)
        subject = res.scalar_one_or_none()
        if not subject:
            raise NotFoundException(f"Subject '{subject_id}' not found")

        return SubjectResponse(
            id=subject.id,
            tenant_id=subject.tenant_id,
            department_id=subject.department_id,
            department_name=subject.department.name if subject.department else None,
            code=subject.code,
            name=subject.name,
            credits=subject.credits,
            lecture_hours=subject.lecture_hours,
            tutorial_hours=subject.tutorial_hours,
            practical_hours=subject.practical_hours,
            subject_type=subject.subject_type,
            description=subject.description,
            is_active=subject.is_active,
            created_at=subject.created_at,
            updated_at=subject.updated_at,
        )

    @staticmethod
    async def create_subject(
        db: AsyncSession,
        tenant_id: UUID,
        payload: SubjectCreateRequest,
        user_id: UUID,
        ip_address: str,
    ) -> SubjectResponse:
        # Check department exists
        dept = await db.scalar(
            select(Department).where(
                Department.tenant_id == tenant_id, Department.id == payload.department_id
            )
        )
        if not dept:
            raise NotFoundException(f"Department '{payload.department_id}' not found")

        # Check unique code
        code_clean = payload.code.strip().upper()
        existing = await db.scalar(
            select(Subject).where(Subject.tenant_id == tenant_id, Subject.code == code_clean)
        )
        if existing:
            raise ConflictException(f"Subject with code '{code_clean}' already exists")

        subject = Subject(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            department_id=payload.department_id,
            code=code_clean,
            name=payload.name.strip(),
            credits=payload.credits,
            lecture_hours=payload.lecture_hours,
            tutorial_hours=payload.tutorial_hours,
            practical_hours=payload.practical_hours,
            subject_type=payload.subject_type.upper(),
            description=payload.description.strip() if payload.description else None,
            is_active=payload.is_active,
        )
        db.add(subject)
        await db.flush()

        audit = AcademicService._create_audit(
            tenant_id=tenant_id,
            user_id=user_id,
            action="SUBJECT_CREATED",
            entity_type="Subject",
            entity_id=subject.id,
            details={"code": subject.code, "name": subject.name},
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()

        return await AcademicService.get_subject_response(db, tenant_id, subject.id)

    @staticmethod
    async def update_subject(
        db: AsyncSession,
        tenant_id: UUID,
        subject_id: UUID,
        payload: SubjectUpdateRequest,
        user_id: UUID,
        ip_address: str,
    ) -> SubjectResponse:
        subject = await db.scalar(
            select(Subject).where(Subject.tenant_id == tenant_id, Subject.id == subject_id)
        )
        if not subject:
            raise NotFoundException(f"Subject '{subject_id}' not found")

        if payload.name is not None:
            subject.name = payload.name.strip()
        if payload.credits is not None:
            subject.credits = payload.credits
        if payload.lecture_hours is not None:
            subject.lecture_hours = payload.lecture_hours
        if payload.tutorial_hours is not None:
            subject.tutorial_hours = payload.tutorial_hours
        if payload.practical_hours is not None:
            subject.practical_hours = payload.practical_hours
        if payload.subject_type is not None:
            subject.subject_type = payload.subject_type.upper()
        if payload.description is not None:
            subject.description = payload.description.strip() if payload.description else None
        if payload.is_active is not None:
            subject.is_active = payload.is_active

        audit = AcademicService._create_audit(
            tenant_id=tenant_id,
            user_id=user_id,
            action="SUBJECT_UPDATED",
            entity_type="Subject",
            entity_id=subject.id,
            details={"code": subject.code},
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()

        return await AcademicService.get_subject_response(db, tenant_id, subject.id)

    # -------------------------------------------------------------------------
    # 2. CURRICULUM SCHEMES & CURRICULUM SUBJECTS
    # -------------------------------------------------------------------------
    @staticmethod
    async def list_curricula(
        db: AsyncSession,
        tenant_id: UUID,
        program_id: UUID | None = None,
        regulation_id: UUID | None = None,
        status: str | None = None,
    ) -> list[CurriculumResponse]:
        query = (
            select(CurriculumScheme)
            .options(
                selectinload(CurriculumScheme.program),
                selectinload(CurriculumScheme.regulation),
                selectinload(CurriculumScheme.subjects),
            )
            .where(CurriculumScheme.tenant_id == tenant_id)
            .order_by(CurriculumScheme.version.desc(), CurriculumScheme.created_at.desc())
        )
        if program_id:
            query = query.where(CurriculumScheme.program_id == program_id)
        if regulation_id:
            query = query.where(CurriculumScheme.regulation_id == regulation_id)
        if status:
            query = query.where(CurriculumScheme.status == status.upper())

        result = await db.execute(query)
        curricula = result.scalars().all()

        return [
            CurriculumResponse(
                id=c.id,
                tenant_id=c.tenant_id,
                program_id=c.program_id,
                program_name=c.program.name if c.program else None,
                program_code=c.program.code if c.program else None,
                regulation_id=c.regulation_id,
                regulation_code=c.regulation.code if c.regulation else None,
                name=c.name,
                version=c.version,
                status=c.status,
                total_credits=c.total_credits,
                description=c.description,
                is_locked=c.is_locked,
                subjects_count=len(c.subjects),
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in curricula
        ]

    @staticmethod
    async def get_curriculum_detail(
        db: AsyncSession, tenant_id: UUID, curriculum_id: UUID
    ) -> CurriculumDetailResponse:
        query = (
            select(CurriculumScheme)
            .options(
                selectinload(CurriculumScheme.program),
                selectinload(CurriculumScheme.regulation),
                selectinload(CurriculumScheme.subjects).selectinload(CurriculumSubject.subject),
            )
            .where(CurriculumScheme.tenant_id == tenant_id, CurriculumScheme.id == curriculum_id)
        )
        res = await db.execute(query)
        c = res.scalar_one_or_none()
        if not c:
            raise NotFoundException(f"Curriculum '{curriculum_id}' not found")

        sorted_subjects = sorted(c.subjects, key=lambda s: (s.semester_number, s.category))

        sub_responses = [
            CurriculumSubjectResponse(
                id=s.id,
                curriculum_id=s.curriculum_id,
                subject_id=s.subject_id,
                subject_code=s.subject.code if s.subject else None,
                subject_name=s.subject.name if s.subject else None,
                semester_number=s.semester_number,
                category=s.category,
                is_mandatory=s.is_mandatory,
                elective_group=s.elective_group,
                credits=s.credits,
                lecture_hours=s.lecture_hours,
                tutorial_hours=s.tutorial_hours,
                practical_hours=s.practical_hours,
            )
            for s in sorted_subjects
        ]

        return CurriculumDetailResponse(
            id=c.id,
            tenant_id=c.tenant_id,
            program_id=c.program_id,
            program_name=c.program.name if c.program else None,
            program_code=c.program.code if c.program else None,
            regulation_id=c.regulation_id,
            regulation_code=c.regulation.code if c.regulation else None,
            name=c.name,
            version=c.version,
            status=c.status,
            total_credits=c.total_credits,
            description=c.description,
            is_locked=c.is_locked,
            subjects_count=len(c.subjects),
            subjects=sub_responses,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )

    @staticmethod
    async def create_curriculum(
        db: AsyncSession,
        tenant_id: UUID,
        payload: CurriculumCreateRequest,
        user_id: UUID,
        ip_address: str,
    ) -> CurriculumDetailResponse:
        # Check program and regulation
        prog = await db.scalar(
            select(Program).where(Program.tenant_id == tenant_id, Program.id == payload.program_id)
        )
        if not prog:
            raise NotFoundException(f"Program '{payload.program_id}' not found")

        reg = await db.scalar(
            select(Regulation).where(
                Regulation.tenant_id == tenant_id, Regulation.id == payload.regulation_id
            )
        )
        if not reg:
            raise NotFoundException(f"Regulation '{payload.regulation_id}' not found")

        # Check duplicate version
        existing = await db.scalar(
            select(CurriculumScheme).where(
                CurriculumScheme.tenant_id == tenant_id,
                CurriculumScheme.program_id == payload.program_id,
                CurriculumScheme.regulation_id == payload.regulation_id,
                CurriculumScheme.version == payload.version,
            )
        )
        if existing:
            raise ConflictException(
                f"Curriculum version {payload.version} already exists for this program and "
                "regulation"
            )

        curriculum = CurriculumScheme(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            program_id=payload.program_id,
            regulation_id=payload.regulation_id,
            name=payload.name.strip(),
            version=payload.version,
            status="DRAFT",
            total_credits=payload.total_credits,
            description=payload.description.strip() if payload.description else None,
            is_locked=False,
        )
        db.add(curriculum)
        await db.flush()

        audit = AcademicService._create_audit(
            tenant_id=tenant_id,
            user_id=user_id,
            action="CURRICULUM_CREATED",
            entity_type="CurriculumScheme",
            entity_id=curriculum.id,
            details={"name": curriculum.name, "version": curriculum.version},
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()

        return await AcademicService.get_curriculum_detail(db, tenant_id, curriculum.id)

    @staticmethod
    async def update_curriculum(
        db: AsyncSession,
        tenant_id: UUID,
        curriculum_id: UUID,
        payload: CurriculumUpdateRequest,
        user_id: UUID,
        ip_address: str,
    ) -> CurriculumDetailResponse:
        c = await db.scalar(
            select(CurriculumScheme).where(
                CurriculumScheme.tenant_id == tenant_id, CurriculumScheme.id == curriculum_id
            )
        )
        if not c:
            raise NotFoundException(f"Curriculum '{curriculum_id}' not found")

        if c.is_locked:
            raise ValidationException("Cannot modify a locked/published curriculum scheme")

        if payload.name is not None:
            c.name = payload.name.strip()
        if payload.total_credits is not None:
            c.total_credits = payload.total_credits
        if payload.description is not None:
            c.description = payload.description.strip() if payload.description else None

        audit = AcademicService._create_audit(
            tenant_id=tenant_id,
            user_id=user_id,
            action="CURRICULUM_UPDATED",
            entity_type="CurriculumScheme",
            entity_id=c.id,
            details={"name": c.name},
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()

        return await AcademicService.get_curriculum_detail(db, tenant_id, c.id)

    @staticmethod
    async def add_curriculum_subject(
        db: AsyncSession,
        tenant_id: UUID,
        curriculum_id: UUID,
        payload: CurriculumSubjectCreateRequest,
        user_id: UUID,
        ip_address: str,
    ) -> CurriculumDetailResponse:
        c = await db.scalar(
            select(CurriculumScheme).where(
                CurriculumScheme.tenant_id == tenant_id, CurriculumScheme.id == curriculum_id
            )
        )
        if not c:
            raise NotFoundException(f"Curriculum '{curriculum_id}' not found")

        if c.is_locked:
            raise ValidationException("Cannot add subjects to a published or locked curriculum")

        # Verify subject belongs to tenant
        subj = await db.scalar(
            select(Subject).where(Subject.tenant_id == tenant_id, Subject.id == payload.subject_id)
        )
        if not subj:
            raise NotFoundException(f"Subject '{payload.subject_id}' not found")

        # Check duplicate in same semester
        existing = await db.scalar(
            select(CurriculumSubject).where(
                CurriculumSubject.curriculum_id == curriculum_id,
                CurriculumSubject.subject_id == payload.subject_id,
                CurriculumSubject.semester_number == payload.semester_number,
            )
        )
        if existing:
            raise ConflictException(
                f"Subject '{subj.code}' is already mapped to Semester {payload.semester_number} "
                "in this curriculum"
            )

        mapping = CurriculumSubject(
            id=uuid.uuid4(),
            curriculum_id=curriculum_id,
            subject_id=payload.subject_id,
            semester_number=payload.semester_number,
            category=payload.category.upper(),
            is_mandatory=payload.is_mandatory,
            elective_group=payload.elective_group.strip() if payload.elective_group else None,
            credits=payload.credits,
            lecture_hours=payload.lecture_hours,
            tutorial_hours=payload.tutorial_hours,
            practical_hours=payload.practical_hours,
        )
        db.add(mapping)
        await db.flush()

        audit = AcademicService._create_audit(
            tenant_id=tenant_id,
            user_id=user_id,
            action="CURRICULUM_SUBJECT_ADDED",
            entity_type="CurriculumSubject",
            entity_id=mapping.id,
            details={"curriculum_id": str(curriculum_id), "subject_code": subj.code},
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()

        return await AcademicService.get_curriculum_detail(db, tenant_id, curriculum_id)

    @staticmethod
    async def remove_curriculum_subject(
        db: AsyncSession,
        tenant_id: UUID,
        curriculum_id: UUID,
        subject_id: UUID,
        user_id: UUID,
        ip_address: str,
    ) -> CurriculumDetailResponse:
        c = await db.scalar(
            select(CurriculumScheme).where(
                CurriculumScheme.tenant_id == tenant_id, CurriculumScheme.id == curriculum_id
            )
        )
        if not c:
            raise NotFoundException(f"Curriculum '{curriculum_id}' not found")

        if c.is_locked:
            raise ValidationException(
                "Cannot remove subjects from a published or locked curriculum"
            )

        mapping = await db.scalar(
            select(CurriculumSubject).where(
                CurriculumSubject.curriculum_id == curriculum_id,
                CurriculumSubject.subject_id == subject_id,
            )
        )
        if not mapping:
            raise NotFoundException("Subject mapping not found in this curriculum")

        await db.delete(mapping)
        audit = AcademicService._create_audit(
            tenant_id=tenant_id,
            user_id=user_id,
            action="CURRICULUM_SUBJECT_REMOVED",
            entity_type="CurriculumSubject",
            entity_id=mapping.id,
            details={"curriculum_id": str(curriculum_id), "subject_id": str(subject_id)},
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()

        return await AcademicService.get_curriculum_detail(db, tenant_id, curriculum_id)

    @staticmethod
    async def publish_curriculum(
        db: AsyncSession,
        tenant_id: UUID,
        curriculum_id: UUID,
        user_id: UUID,
        ip_address: str,
    ) -> CurriculumDetailResponse:
        c = await db.scalar(
            select(CurriculumScheme).where(
                CurriculumScheme.tenant_id == tenant_id, CurriculumScheme.id == curriculum_id
            )
        )
        if not c:
            raise NotFoundException(f"Curriculum '{curriculum_id}' not found")

        # Verify has subjects
        count = await db.scalar(
            select(func.count(CurriculumSubject.id)).where(
                CurriculumSubject.curriculum_id == curriculum_id
            )
        )
        if not count or count == 0:
            raise ValidationException("Cannot publish an empty curriculum scheme without subjects")

        c.status = "PUBLISHED"
        c.is_locked = True

        audit = AcademicService._create_audit(
            tenant_id=tenant_id,
            user_id=user_id,
            action="CURRICULUM_PUBLISHED",
            entity_type="CurriculumScheme",
            entity_id=c.id,
            details={"name": c.name, "version": c.version},
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()

        return await AcademicService.get_curriculum_detail(db, tenant_id, c.id)

    # -------------------------------------------------------------------------
    # 3. CLASSROOMS & TIME SLOTS
    # -------------------------------------------------------------------------
    @staticmethod
    async def list_rooms(
        db: AsyncSession,
        tenant_id: UUID,
        campus_id: UUID | None = None,
        is_active: bool | None = None,
    ) -> list[ClassroomResponse]:
        query = (
            select(Classroom)
            .options(selectinload(Classroom.campus))
            .where(Classroom.tenant_id == tenant_id)
            .order_by(Classroom.building.asc(), Classroom.room_number.asc())
        )
        if campus_id:
            query = query.where(Classroom.campus_id == campus_id)
        if is_active is not None:
            query = query.where(Classroom.is_active == is_active)

        res = await db.execute(query)
        rooms = res.scalars().all()
        return [
            ClassroomResponse(
                id=r.id,
                tenant_id=r.tenant_id,
                campus_id=r.campus_id,
                campus_name=r.campus.name if r.campus else None,
                building=r.building,
                room_number=r.room_number,
                capacity=r.capacity,
                room_type=r.room_type,
                is_active=r.is_active,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in rooms
        ]

    @staticmethod
    async def create_room(
        db: AsyncSession,
        tenant_id: UUID,
        payload: ClassroomCreateRequest,
        user_id: UUID,
        ip_address: str,
    ) -> ClassroomResponse:
        bldg_clean = payload.building.strip()
        room_clean = payload.room_number.strip().upper()

        existing = await db.scalar(
            select(Classroom).where(
                Classroom.tenant_id == tenant_id,
                Classroom.building == bldg_clean,
                Classroom.room_number == room_clean,
            )
        )
        if existing:
            raise ConflictException(
                f"Room '{room_clean}' in building '{bldg_clean}' already exists"
            )

        room = Classroom(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            campus_id=payload.campus_id,
            building=bldg_clean,
            room_number=room_clean,
            capacity=payload.capacity,
            room_type=payload.room_type.upper(),
            is_active=payload.is_active,
        )
        db.add(room)
        await db.flush()

        audit = AcademicService._create_audit(
            tenant_id=tenant_id,
            user_id=user_id,
            action="ROOM_CREATED",
            entity_type="Classroom",
            entity_id=room.id,
            details={"room_number": room.room_number, "building": room.building},
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()

        # Reload with campus
        reloaded = await db.scalar(
            select(Classroom)
            .options(selectinload(Classroom.campus))
            .where(Classroom.id == room.id)
        )
        return ClassroomResponse(
            id=reloaded.id,
            tenant_id=reloaded.tenant_id,
            campus_id=reloaded.campus_id,
            campus_name=reloaded.campus.name if reloaded.campus else None,
            building=reloaded.building,
            room_number=reloaded.room_number,
            capacity=reloaded.capacity,
            room_type=reloaded.room_type,
            is_active=reloaded.is_active,
            created_at=reloaded.created_at,
            updated_at=reloaded.updated_at,
        )

    @staticmethod
    async def list_time_slots(
        db: AsyncSession, tenant_id: UUID, is_active: bool | None = None
    ) -> list[TimeSlotResponse]:
        query = (
            select(TimeSlot)
            .where(TimeSlot.tenant_id == tenant_id)
            .order_by(TimeSlot.slot_number.asc())
        )
        if is_active is not None:
            query = query.where(TimeSlot.is_active == is_active)

        res = await db.execute(query)
        slots = res.scalars().all()
        return [TimeSlotResponse.model_validate(s) for s in slots]

    @staticmethod
    async def create_time_slot(
        db: AsyncSession,
        tenant_id: UUID,
        payload: TimeSlotCreateRequest,
        user_id: UUID,
        ip_address: str,
    ) -> TimeSlotResponse:
        existing = await db.scalar(
            select(TimeSlot).where(
                TimeSlot.tenant_id == tenant_id, TimeSlot.slot_number == payload.slot_number
            )
        )
        if existing:
            raise ConflictException(f"Time slot #{payload.slot_number} already exists")

        if payload.start_time >= payload.end_time:
            raise ValidationException("Slot start time must precede end time")

        slot = TimeSlot(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            name=payload.name.strip(),
            slot_number=payload.slot_number,
            start_time=payload.start_time,
            end_time=payload.end_time,
            slot_type=payload.slot_type.upper(),
            is_active=payload.is_active,
        )
        db.add(slot)
        await db.flush()

        audit = AcademicService._create_audit(
            tenant_id=tenant_id,
            user_id=user_id,
            action="TIME_SLOT_CREATED",
            entity_type="TimeSlot",
            entity_id=slot.id,
            details={"name": slot.name, "slot_number": slot.slot_number},
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()

        return TimeSlotResponse.model_validate(slot)

    # -------------------------------------------------------------------------
    # 4. COURSE OFFERINGS & LIFECYCLE
    # -------------------------------------------------------------------------
    @staticmethod
    async def list_offerings(
        db: AsyncSession,
        tenant_id: UUID,
        academic_year_id: UUID | None = None,
        semester_id: UUID | None = None,
        section_id: UUID | None = None,
        subject_id: UUID | None = None,
        status: str | None = None,
        search: str | None = None,
    ) -> list[CourseOfferingResponse]:
        query = (
            select(CourseOffering)
            .options(
                selectinload(CourseOffering.subject),
                selectinload(CourseOffering.academic_year),
                selectinload(CourseOffering.semester),
                selectinload(CourseOffering.section).selectinload(Section.program),
                selectinload(CourseOffering.enrollments),
                selectinload(CourseOffering.faculty_assignments)
                .selectinload(CourseFacultyAssignment.faculty)
                .selectinload(FacultyProfile.user),
            )
            .where(CourseOffering.tenant_id == tenant_id)
            .order_by(CourseOffering.created_at.desc())
        )

        if academic_year_id:
            query = query.where(CourseOffering.academic_year_id == academic_year_id)
        if semester_id:
            query = query.where(CourseOffering.semester_id == semester_id)
        if section_id:
            query = query.where(CourseOffering.section_id == section_id)
        if subject_id:
            query = query.where(CourseOffering.subject_id == subject_id)
        if status:
            query = query.where(CourseOffering.status == status.upper())

        res = await db.execute(query)
        offerings = res.scalars().all()

        responses: list[CourseOfferingResponse] = []
        for o in offerings:
            primary_fac = next((fa for fa in o.faculty_assignments if fa.role == "PRIMARY"), None)
            prim_name = None
            if primary_fac and primary_fac.faculty and primary_fac.faculty.user:
                u = primary_fac.faculty.user
                prim_name = f"{u.first_name} {u.last_name}"

            active_enrolled = len([e for e in o.enrollments if e.status == "ENROLLED"])

            if search:
                pat = search.strip().lower()
                subj_match = o.subject and (
                    pat in o.subject.code.lower() or pat in o.subject.name.lower()
                )
                fac_match = prim_name and pat in prim_name.lower()
                if not (subj_match or fac_match):
                    continue

            responses.append(
                CourseOfferingResponse(
                    id=o.id,
                    tenant_id=o.tenant_id,
                    subject_id=o.subject_id,
                    subject_code=o.subject.code if o.subject else None,
                    subject_name=o.subject.name if o.subject else None,
                    subject_credits=o.subject.credits if o.subject else None,
                    academic_year_id=o.academic_year_id,
                    academic_year_name=o.academic_year.name if o.academic_year else None,
                    semester_id=o.semester_id,
                    semester_name=o.semester.name if o.semester else None,
                    section_id=o.section_id,
                    section_name=o.section.name if o.section else None,
                    program_name=o.section.program.name
                    if (o.section and o.section.program)
                    else None,
                    status=o.status,
                    max_capacity=o.max_capacity,
                    enrolled_count=active_enrolled,
                    primary_faculty_name=prim_name,
                    created_at=o.created_at,
                    updated_at=o.updated_at,
                )
            )

        return responses

    @staticmethod
    async def get_offering_detail(
        db: AsyncSession, tenant_id: UUID, offering_id: UUID
    ) -> CourseOfferingDetailResponse:
        query = (
            select(CourseOffering)
            .options(
                selectinload(CourseOffering.subject),
                selectinload(CourseOffering.academic_year),
                selectinload(CourseOffering.semester),
                selectinload(CourseOffering.section).selectinload(Section.program),
                selectinload(CourseOffering.enrollments),
                selectinload(CourseOffering.faculty_assignments)
                .selectinload(CourseFacultyAssignment.faculty)
                .selectinload(FacultyProfile.user),
            )
            .where(CourseOffering.tenant_id == tenant_id, CourseOffering.id == offering_id)
        )
        res = await db.execute(query)
        o = res.scalar_one_or_none()
        if not o:
            raise NotFoundException(f"Course offering '{offering_id}' not found")

        primary_fac = next((fa for fa in o.faculty_assignments if fa.role == "PRIMARY"), None)
        prim_name = None
        if primary_fac and primary_fac.faculty and primary_fac.faculty.user:
            u = primary_fac.faculty.user
            prim_name = f"{u.first_name} {u.last_name}"

        active_enrolled = len([e for e in o.enrollments if e.status == "ENROLLED"])

        fac_assignments = [
            CourseFacultyAssignmentResponse(
                id=fa.id,
                course_offering_id=fa.course_offering_id,
                faculty_id=fa.faculty_id,
                faculty_name=f"{fa.faculty.user.first_name} {fa.faculty.user.last_name}"
                if (fa.faculty and fa.faculty.user)
                else None,
                faculty_employee_code=fa.faculty.employee_code if fa.faculty else None,
                role=fa.role,
                start_date=fa.start_date,
                end_date=fa.end_date,
                is_active=fa.is_active,
            )
            for fa in o.faculty_assignments
        ]

        return CourseOfferingDetailResponse(
            id=o.id,
            tenant_id=o.tenant_id,
            subject_id=o.subject_id,
            subject_code=o.subject.code if o.subject else None,
            subject_name=o.subject.name if o.subject else None,
            subject_credits=o.subject.credits if o.subject else None,
            academic_year_id=o.academic_year_id,
            academic_year_name=o.academic_year.name if o.academic_year else None,
            semester_id=o.semester_id,
            semester_name=o.semester.name if o.semester else None,
            section_id=o.section_id,
            section_name=o.section.name if o.section else None,
            program_name=o.section.program.name if (o.section and o.section.program) else None,
            status=o.status,
            max_capacity=o.max_capacity,
            enrolled_count=active_enrolled,
            primary_faculty_name=prim_name,
            faculty_assignments=fac_assignments,
            created_at=o.created_at,
            updated_at=o.updated_at,
        )

    @staticmethod
    async def create_offering(
        db: AsyncSession,
        tenant_id: UUID,
        payload: CourseOfferingCreateRequest,
        user_id: UUID,
        ip_address: str,
    ) -> CourseOfferingDetailResponse:
        # Check prerequisites
        subj = await db.scalar(
            select(Subject).where(Subject.tenant_id == tenant_id, Subject.id == payload.subject_id)
        )
        if not subj:
            raise NotFoundException(f"Subject '{payload.subject_id}' not found")

        ay = await db.scalar(
            select(AcademicYear).where(
                AcademicYear.tenant_id == tenant_id, AcademicYear.id == payload.academic_year_id
            )
        )
        if not ay:
            raise NotFoundException(f"Academic year '{payload.academic_year_id}' not found")

        sem = await db.scalar(
            select(Semester).where(
                Semester.tenant_id == tenant_id, Semester.id == payload.semester_id
            )
        )
        if not sem:
            raise NotFoundException(f"Semester '{payload.semester_id}' not found")

        sec = await db.scalar(
            select(Section).where(Section.tenant_id == tenant_id, Section.id == payload.section_id)
        )
        if not sec:
            raise NotFoundException(f"Section '{payload.section_id}' not found")

        # Verify composite uniqueness
        existing = await db.scalar(
            select(CourseOffering).where(
                CourseOffering.tenant_id == tenant_id,
                CourseOffering.subject_id == payload.subject_id,
                CourseOffering.academic_year_id == payload.academic_year_id,
                CourseOffering.semester_id == payload.semester_id,
                CourseOffering.section_id == payload.section_id,
            )
        )
        if existing:
            raise ConflictException(
                "A course offering for this subject, academic year, semester, and section "
                "already exists"
            )

        offering = CourseOffering(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            subject_id=payload.subject_id,
            academic_year_id=payload.academic_year_id,
            semester_id=payload.semester_id,
            section_id=payload.section_id,
            status=payload.status.upper(),
            max_capacity=payload.max_capacity,
        )
        db.add(offering)
        await db.flush()

        audit = AcademicService._create_audit(
            tenant_id=tenant_id,
            user_id=user_id,
            action="COURSE_OFFERING_CREATED",
            entity_type="CourseOffering",
            entity_id=offering.id,
            details={"subject_code": subj.code, "status": offering.status},
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()

        return await AcademicService.get_offering_detail(db, tenant_id, offering.id)

    @staticmethod
    async def transition_offering_status(
        db: AsyncSession,
        tenant_id: UUID,
        offering_id: UUID,
        new_status: str,
        user_id: UUID,
        ip_address: str,
    ) -> CourseOfferingDetailResponse:
        o = await db.scalar(
            select(CourseOffering).where(
                CourseOffering.tenant_id == tenant_id, CourseOffering.id == offering_id
            )
        )
        if not o:
            raise NotFoundException(f"Course offering '{offering_id}' not found")

        status_clean = new_status.strip().upper()
        allowed = VALID_OFFERING_STATUS_TRANSITIONS.get(o.status, set())
        if status_clean not in allowed:
            raise ValidationException(
                f"Invalid offering status transition from '{o.status}' to '{status_clean}'"
            )

        old_status = o.status
        o.status = status_clean

        audit = AcademicService._create_audit(
            tenant_id=tenant_id,
            user_id=user_id,
            action="COURSE_OFFERING_STATUS_CHANGED",
            entity_type="CourseOffering",
            entity_id=o.id,
            details={"from_status": old_status, "to_status": status_clean},
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()

        return await AcademicService.get_offering_detail(db, tenant_id, o.id)

    # -------------------------------------------------------------------------
    # 5. FACULTY ASSIGNMENTS
    # -------------------------------------------------------------------------
    @staticmethod
    async def assign_faculty(
        db: AsyncSession,
        tenant_id: UUID,
        offering_id: UUID,
        payload: CourseFacultyAssignmentCreateRequest,
        user_id: UUID,
        ip_address: str,
    ) -> CourseOfferingDetailResponse:
        o = await db.scalar(
            select(CourseOffering).where(
                CourseOffering.tenant_id == tenant_id, CourseOffering.id == offering_id
            )
        )
        if not o:
            raise NotFoundException(f"Course offering '{offering_id}' not found")

        fac = await db.scalar(
            select(FacultyProfile).where(
                FacultyProfile.tenant_id == tenant_id, FacultyProfile.id == payload.faculty_id
            )
        )
        if not fac:
            raise NotFoundException(f"Faculty member '{payload.faculty_id}' not found")

        existing = await db.scalar(
            select(CourseFacultyAssignment).where(
                CourseFacultyAssignment.course_offering_id == offering_id,
                CourseFacultyAssignment.faculty_id == payload.faculty_id,
            )
        )
        if existing:
            raise ConflictException(
                "This faculty member is already assigned to this course offering"
            )

        assignment = CourseFacultyAssignment(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            course_offering_id=offering_id,
            faculty_id=payload.faculty_id,
            role=payload.role.upper(),
            start_date=payload.start_date or date.today(),
            end_date=payload.end_date,
            is_active=True,
        )
        db.add(assignment)
        await db.flush()

        audit = AcademicService._create_audit(
            tenant_id=tenant_id,
            user_id=user_id,
            action="FACULTY_ASSIGNED",
            entity_type="CourseFacultyAssignment",
            entity_id=assignment.id,
            details={
                "offering_id": str(offering_id),
                "faculty_code": fac.employee_code,
                "role": assignment.role,
            },
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()

        return await AcademicService.get_offering_detail(db, tenant_id, offering_id)

    @staticmethod
    async def unassign_faculty(
        db: AsyncSession,
        tenant_id: UUID,
        offering_id: UUID,
        faculty_id: UUID,
        user_id: UUID,
        ip_address: str,
    ) -> CourseOfferingDetailResponse:
        assignment = await db.scalar(
            select(CourseFacultyAssignment).where(
                CourseFacultyAssignment.tenant_id == tenant_id,
                CourseFacultyAssignment.course_offering_id == offering_id,
                CourseFacultyAssignment.faculty_id == faculty_id,
            )
        )
        if not assignment:
            raise NotFoundException("Faculty assignment not found")

        await db.delete(assignment)

        audit = AcademicService._create_audit(
            tenant_id=tenant_id,
            user_id=user_id,
            action="FACULTY_UNASSIGNED",
            entity_type="CourseFacultyAssignment",
            entity_id=assignment.id,
            details={"offering_id": str(offering_id), "faculty_id": str(faculty_id)},
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()

        return await AcademicService.get_offering_detail(db, tenant_id, offering_id)

    # -------------------------------------------------------------------------
    # 6. STUDENT COURSE ENROLLMENTS
    # -------------------------------------------------------------------------
    @staticmethod
    async def list_enrolled_students(
        db: AsyncSession,
        tenant_id: UUID,
        offering_id: UUID,
        status: str | None = None,
    ) -> list[CourseEnrollmentResponse]:
        query = (
            select(CourseEnrollment)
            .options(
                selectinload(CourseEnrollment.student).selectinload(StudentProfile.user)
            )
            .where(
                CourseEnrollment.tenant_id == tenant_id,
                CourseEnrollment.course_offering_id == offering_id,
            )
            .order_by(CourseEnrollment.enrollment_date.asc())
        )
        if status:
            query = query.where(CourseEnrollment.status == status.upper())

        res = await db.execute(query)
        enrollments = res.scalars().all()

        return [
            CourseEnrollmentResponse(
                id=e.id,
                tenant_id=e.tenant_id,
                student_id=e.student_id,
                student_name=f"{e.student.user.first_name} {e.student.user.last_name}"
                if (e.student and e.student.user)
                else None,
                student_roll_number=e.student.roll_number if e.student else None,
                student_admission_number=e.student.admission_number if e.student else None,
                course_offering_id=e.course_offering_id,
                enrollment_type=e.enrollment_type,
                status=e.status,
                enrollment_date=e.enrollment_date,
                dropped_date=e.dropped_date,
                created_at=e.created_at,
                updated_at=e.updated_at,
            )
            for e in enrollments
        ]

    @staticmethod
    async def enroll_student(
        db: AsyncSession,
        tenant_id: UUID,
        offering_id: UUID,
        payload: CourseEnrollmentCreateRequest,
        user_id: UUID,
        ip_address: str,
    ) -> CourseEnrollmentResponse:
        o = await db.scalar(
            select(CourseOffering).where(
                CourseOffering.tenant_id == tenant_id, CourseOffering.id == offering_id
            )
        )
        if not o:
            raise NotFoundException(f"Course offering '{offering_id}' not found")

        if o.status not in ("PLANNED", "OPEN", "ACTIVE"):
            raise ValidationException(
                f"Cannot enroll students into offering in '{o.status}' status"
            )

        # Check student
        student = await db.scalar(
            select(StudentProfile)
            .options(selectinload(StudentProfile.user))
            .where(
                StudentProfile.tenant_id == tenant_id, StudentProfile.id == payload.student_id
            )
        )
        if not student:
            raise NotFoundException(f"Student '{payload.student_id}' not found")

        # Check duplicate
        existing = await db.scalar(
            select(CourseEnrollment).where(
                CourseEnrollment.tenant_id == tenant_id,
                CourseEnrollment.course_offering_id == offering_id,
                CourseEnrollment.student_id == payload.student_id,
            )
        )
        if existing:
            raise ConflictException("Student is already enrolled in this course offering")

        enrollment = CourseEnrollment(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            student_id=payload.student_id,
            course_offering_id=offering_id,
            enrollment_type=payload.enrollment_type.upper(),
            status="ENROLLED",
            enrollment_date=date.today(),
        )
        db.add(enrollment)
        await db.flush()

        audit = AcademicService._create_audit(
            tenant_id=tenant_id,
            user_id=user_id,
            action="STUDENT_ENROLLED",
            entity_type="CourseEnrollment",
            entity_id=enrollment.id,
            details={
                "offering_id": str(offering_id),
                "student_admission_number": student.admission_number,
            },
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()

        return CourseEnrollmentResponse(
            id=enrollment.id,
            tenant_id=enrollment.tenant_id,
            student_id=enrollment.student_id,
            student_name=f"{student.user.first_name} {student.user.last_name}"
            if (student and student.user)
            else None,
            student_roll_number=student.roll_number,
            student_admission_number=student.admission_number,
            course_offering_id=enrollment.course_offering_id,
            enrollment_type=enrollment.enrollment_type,
            status=enrollment.status,
            enrollment_date=enrollment.enrollment_date,
            dropped_date=enrollment.dropped_date,
            created_at=enrollment.created_at,
            updated_at=enrollment.updated_at,
        )

    @staticmethod
    async def batch_enroll_section(
        db: AsyncSession,
        tenant_id: UUID,
        offering_id: UUID,
        payload: CourseBatchEnrollRequest,
        user_id: UUID,
        ip_address: str,
    ) -> int:
        o = await db.scalar(
            select(CourseOffering).where(
                CourseOffering.tenant_id == tenant_id, CourseOffering.id == offering_id
            )
        )
        if not o:
            raise NotFoundException(f"Course offering '{offering_id}' not found")

        # Query all active students in section
        students = (
            (
                await db.execute(
                    select(StudentProfile).where(
                        StudentProfile.tenant_id == tenant_id,
                        StudentProfile.current_section_id == payload.section_id,
                        StudentProfile.status.in_(["ACTIVE", "ADMITTED"]),
                    )
                )
            )
            .scalars()
            .all()
        )

        enrolled_count = 0
        for s in students:
            # Check if enrolled
            exists = await db.scalar(
                select(CourseEnrollment).where(
                    CourseEnrollment.tenant_id == tenant_id,
                    CourseEnrollment.course_offering_id == offering_id,
                    CourseEnrollment.student_id == s.id,
                )
            )
            if not exists:
                enrollment = CourseEnrollment(
                    tenant_id=tenant_id,
                    student_id=s.id,
                    course_offering_id=offering_id,
                    enrollment_type=payload.enrollment_type.upper(),
                    status="ENROLLED",
                    enrollment_date=date.today(),
                )
                db.add(enrollment)
                enrolled_count += 1

        if enrolled_count > 0:
            audit = AcademicService._create_audit(
                tenant_id=tenant_id,
                user_id=user_id,
                action="SECTION_BATCH_ENROLLED",
                entity_type="CourseOffering",
                entity_id=offering_id,
                details={"section_id": str(payload.section_id), "count": enrolled_count},
                ip_address=ip_address,
            )
            db.add(audit)
            await db.commit()

        return enrolled_count

    @staticmethod
    async def withdraw_student(
        db: AsyncSession,
        tenant_id: UUID,
        offering_id: UUID,
        student_id: UUID,
        user_id: UUID,
        ip_address: str,
    ) -> None:
        enrollment = await db.scalar(
            select(CourseEnrollment).where(
                CourseEnrollment.tenant_id == tenant_id,
                CourseEnrollment.course_offering_id == offering_id,
                CourseEnrollment.student_id == student_id,
            )
        )
        if not enrollment:
            raise NotFoundException("Student is not enrolled in this course offering")

        enrollment.status = "WITHDRAWN"
        enrollment.dropped_date = date.today()

        audit = AcademicService._create_audit(
            tenant_id=tenant_id,
            user_id=user_id,
            action="STUDENT_WITHDRAWN",
            entity_type="CourseEnrollment",
            entity_id=enrollment.id,
            details={"offering_id": str(offering_id), "student_id": str(student_id)},
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()

    # -------------------------------------------------------------------------
    # 7. TIMETABLE ENGINE WITH MULTI-DIMENSIONAL CONFLICT DETECTION
    # -------------------------------------------------------------------------
    @staticmethod
    async def validate_timetable_clash(
        db: AsyncSession,
        tenant_id: UUID,
        academic_year_id: UUID,
        semester_id: UUID,
        day_of_week: int,
        time_slot_id: UUID,
        section_id: UUID,
        faculty_id: UUID | None,
        room_id: UUID | None,
        exclude_entry_id: UUID | None = None,
    ) -> None:
        """Enforces:

        1. Section Conflict: Section cannot have 2 classes at same day & slot
        2. Faculty Conflict: Faculty cannot teach 2 classes at same day & slot
        3. Room Conflict: Room cannot host 2 classes at same day & slot
        """
        # 1. Section Clash
        sec_q = select(TimetableEntry).where(
            TimetableEntry.tenant_id == tenant_id,
            TimetableEntry.academic_year_id == academic_year_id,
            TimetableEntry.semester_id == semester_id,
            TimetableEntry.day_of_week == day_of_week,
            TimetableEntry.time_slot_id == time_slot_id,
            TimetableEntry.section_id == section_id,
            TimetableEntry.is_active == True,  # noqa: E712
        )
        if exclude_entry_id:
            sec_q = sec_q.where(TimetableEntry.id != exclude_entry_id)

        sec_conflict = await db.scalar(sec_q)
        if sec_conflict:
            day_name = DAYS_OF_WEEK_NAMES.get(day_of_week, f"Day {day_of_week}")
            raise ConflictException(
                f"Schedule Conflict: Class section is already scheduled for a class on {day_name} "
                "during this period."
            )

        # 2. Faculty Clash
        if faculty_id:
            fac_q = select(TimetableEntry).where(
                TimetableEntry.tenant_id == tenant_id,
                TimetableEntry.academic_year_id == academic_year_id,
                TimetableEntry.semester_id == semester_id,
                TimetableEntry.day_of_week == day_of_week,
                TimetableEntry.time_slot_id == time_slot_id,
                TimetableEntry.faculty_id == faculty_id,
                TimetableEntry.is_active == True,  # noqa: E712
            )
            if exclude_entry_id:
                fac_q = fac_q.where(TimetableEntry.id != exclude_entry_id)

            fac_conflict = await db.scalar(fac_q)
            if fac_conflict:
                day_name = DAYS_OF_WEEK_NAMES.get(day_of_week, f"Day {day_of_week}")
                raise ConflictException(
                    f"Faculty Conflict: The assigned instructor is already teaching another class "
                    f"on {day_name} during this period."
                )

        # 3. Room Clash
        if room_id:
            room_q = select(TimetableEntry).where(
                TimetableEntry.tenant_id == tenant_id,
                TimetableEntry.academic_year_id == academic_year_id,
                TimetableEntry.semester_id == semester_id,
                TimetableEntry.day_of_week == day_of_week,
                TimetableEntry.time_slot_id == time_slot_id,
                TimetableEntry.room_id == room_id,
                TimetableEntry.is_active == True,  # noqa: E712
            )
            if exclude_entry_id:
                room_q = room_q.where(TimetableEntry.id != exclude_entry_id)

            room_conflict = await db.scalar(room_q)
            if room_conflict:
                day_name = DAYS_OF_WEEK_NAMES.get(day_of_week, f"Day {day_of_week}")
                raise ConflictException(
                    f"Room Conflict: The selected room is already booked on {day_name} "
                    "during this period."
                )

    @staticmethod
    async def list_timetable_entries(
        db: AsyncSession,
        tenant_id: UUID,
        section_id: UUID | None = None,
        faculty_id: UUID | None = None,
        room_id: UUID | None = None,
        academic_year_id: UUID | None = None,
        semester_id: UUID | None = None,
        day_of_week: int | None = None,
    ) -> list[TimetableEntryResponse]:
        query = (
            select(TimetableEntry)
            .options(
                selectinload(TimetableEntry.course_offering).selectinload(CourseOffering.subject),
                selectinload(TimetableEntry.section),
                selectinload(TimetableEntry.faculty).selectinload(FacultyProfile.user),
                selectinload(TimetableEntry.room),
                selectinload(TimetableEntry.time_slot),
            )
            .where(TimetableEntry.tenant_id == tenant_id)
            .order_by(TimetableEntry.day_of_week.asc())
        )

        if section_id:
            query = query.where(TimetableEntry.section_id == section_id)
        if faculty_id:
            query = query.where(TimetableEntry.faculty_id == faculty_id)
        if room_id:
            query = query.where(TimetableEntry.room_id == room_id)
        if academic_year_id:
            query = query.where(TimetableEntry.academic_year_id == academic_year_id)
        if semester_id:
            query = query.where(TimetableEntry.semester_id == semester_id)
        if day_of_week:
            query = query.where(TimetableEntry.day_of_week == day_of_week)

        res = await db.execute(query)
        entries = res.scalars().all()

        return [
            TimetableEntryResponse(
                id=e.id,
                tenant_id=e.tenant_id,
                course_offering_id=e.course_offering_id,
                subject_code=e.course_offering.subject.code
                if (e.course_offering and e.course_offering.subject)
                else None,
                subject_name=e.course_offering.subject.name
                if (e.course_offering and e.course_offering.subject)
                else None,
                section_id=e.section_id,
                section_name=e.section.name if e.section else None,
                academic_year_id=e.academic_year_id,
                semester_id=e.semester_id,
                faculty_id=e.faculty_id,
                faculty_name=f"{e.faculty.user.first_name} {e.faculty.user.last_name}"
                if (e.faculty and e.faculty.user)
                else None,
                room_id=e.room_id,
                room_name=f"{e.room.building} - {e.room.room_number}" if e.room else None,
                time_slot_id=e.time_slot_id,
                time_slot_name=e.time_slot.name if e.time_slot else None,
                time_slot_start=e.time_slot.start_time if e.time_slot else None,
                time_slot_end=e.time_slot.end_time if e.time_slot else None,
                day_of_week=e.day_of_week,
                is_active=e.is_active,
                created_at=e.created_at,
                updated_at=e.updated_at,
            )
            for e in entries
        ]

    @staticmethod
    async def get_section_timetable_grid(
        db: AsyncSession,
        tenant_id: UUID,
        section_id: UUID,
        academic_year_id: UUID,
        semester_id: UUID,
    ) -> TimetableSectionGridResponse:
        sec = await db.scalar(
            select(Section).where(Section.tenant_id == tenant_id, Section.id == section_id)
        )
        if not sec:
            raise NotFoundException(f"Section '{section_id}' not found")

        slots_resp = await AcademicService.list_time_slots(db, tenant_id, is_active=True)

        entries = await AcademicService.list_timetable_entries(
            db,
            tenant_id,
            section_id=section_id,
            academic_year_id=academic_year_id,
            semester_id=semester_id,
        )

        # Build day matrix (1=Monday to 6=Saturday)
        days_matrix: list[TimetableGridDay] = []
        for day_num in range(1, 7):
            day_name = DAYS_OF_WEEK_NAMES.get(day_num, f"Day {day_num}")
            day_slots: dict[str, TimetableGridCell | None] = {}

            for slot in slots_resp:
                matching_entry = next(
                    (
                        e
                        for e in entries
                        if e.day_of_week == day_num and e.time_slot_id == slot.id and e.is_active
                    ),
                    None,
                )
                if matching_entry:
                    day_slots[str(slot.id)] = TimetableGridCell(
                        entry_id=matching_entry.id,
                        course_offering_id=matching_entry.course_offering_id,
                        subject_code=matching_entry.subject_code or "",
                        subject_name=matching_entry.subject_name or "",
                        faculty_name=matching_entry.faculty_name,
                        room_name=matching_entry.room_name,
                        time_slot_id=slot.id,
                    )
                else:
                    day_slots[str(slot.id)] = None

            days_matrix.append(
                TimetableGridDay(day_of_week=day_num, day_name=day_name, slots=day_slots)
            )

        return TimetableSectionGridResponse(
            section_id=section_id,
            section_name=sec.name,
            academic_year_id=academic_year_id,
            semester_id=semester_id,
            time_slots=slots_resp,
            days=days_matrix,
        )

    @staticmethod
    async def create_timetable_entry(
        db: AsyncSession,
        tenant_id: UUID,
        payload: TimetableEntryCreateRequest,
        user_id: UUID,
        ip_address: str,
    ) -> TimetableEntryResponse:
        # Check prerequisites
        o = await db.scalar(
            select(CourseOffering).where(
                CourseOffering.tenant_id == tenant_id,
                CourseOffering.id == payload.course_offering_id,
            )
        )
        if not o:
            raise NotFoundException(f"Course offering '{payload.course_offering_id}' not found")

        # Conflict Detection Validation
        await AcademicService.validate_timetable_clash(
            db=db,
            tenant_id=tenant_id,
            academic_year_id=payload.academic_year_id,
            semester_id=payload.semester_id,
            day_of_week=payload.day_of_week,
            time_slot_id=payload.time_slot_id,
            section_id=payload.section_id,
            faculty_id=payload.faculty_id,
            room_id=payload.room_id,
        )

        entry = TimetableEntry(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            course_offering_id=payload.course_offering_id,
            section_id=payload.section_id,
            academic_year_id=payload.academic_year_id,
            semester_id=payload.semester_id,
            time_slot_id=payload.time_slot_id,
            day_of_week=payload.day_of_week,
            faculty_id=payload.faculty_id,
            room_id=payload.room_id,
            is_active=True,
        )
        db.add(entry)
        await db.flush()

        audit = AcademicService._create_audit(
            tenant_id=tenant_id,
            user_id=user_id,
            action="TIMETABLE_ENTRY_CREATED",
            entity_type="TimetableEntry",
            entity_id=entry.id,
            details={
                "offering_id": str(payload.course_offering_id),
                "section_id": str(payload.section_id),
                "day": payload.day_of_week,
            },
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()

        # Fetch and return populated
        entries = await AcademicService.list_timetable_entries(db, tenant_id)
        created = next(e for e in entries if e.id == entry.id)
        return created

    @staticmethod
    async def update_timetable_entry(
        db: AsyncSession,
        tenant_id: UUID,
        entry_id: UUID,
        payload: TimetableEntryUpdateRequest,
        user_id: UUID,
        ip_address: str,
    ) -> TimetableEntryResponse:
        entry = await db.scalar(
            select(TimetableEntry).where(
                TimetableEntry.tenant_id == tenant_id, TimetableEntry.id == entry_id
            )
        )
        if not entry:
            raise NotFoundException(f"Timetable entry '{entry_id}' not found")

        target_faculty = payload.faculty_id if payload.faculty_id is not None else entry.faculty_id
        target_room = payload.room_id if payload.room_id is not None else entry.room_id
        target_slot = (
            payload.time_slot_id if payload.time_slot_id is not None else entry.time_slot_id
        )
        target_day = payload.day_of_week if payload.day_of_week is not None else entry.day_of_week

        # Re-validate clashes with updated parameters
        await AcademicService.validate_timetable_clash(
            db=db,
            tenant_id=tenant_id,
            academic_year_id=entry.academic_year_id,
            semester_id=entry.semester_id,
            day_of_week=target_day,
            time_slot_id=target_slot,
            section_id=entry.section_id,
            faculty_id=target_faculty,
            room_id=target_room,
            exclude_entry_id=entry.id,
        )

        if payload.faculty_id is not None:
            entry.faculty_id = payload.faculty_id
        if payload.room_id is not None:
            entry.room_id = payload.room_id
        if payload.time_slot_id is not None:
            entry.time_slot_id = payload.time_slot_id
        if payload.day_of_week is not None:
            entry.day_of_week = payload.day_of_week
        if payload.is_active is not None:
            entry.is_active = payload.is_active

        audit = AcademicService._create_audit(
            tenant_id=tenant_id,
            user_id=user_id,
            action="TIMETABLE_ENTRY_UPDATED",
            entity_type="TimetableEntry",
            entity_id=entry.id,
            details={"entry_id": str(entry.id)},
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()

        entries = await AcademicService.list_timetable_entries(db, tenant_id)
        updated = next(e for e in entries if e.id == entry.id)
        return updated

    @staticmethod
    async def delete_timetable_entry(
        db: AsyncSession,
        tenant_id: UUID,
        entry_id: UUID,
        user_id: UUID,
        ip_address: str,
    ) -> None:
        entry = await db.scalar(
            select(TimetableEntry).where(
                TimetableEntry.tenant_id == tenant_id, TimetableEntry.id == entry_id
            )
        )
        if not entry:
            raise NotFoundException(f"Timetable entry '{entry_id}' not found")

        await db.delete(entry)

        audit = AcademicService._create_audit(
            tenant_id=tenant_id,
            user_id=user_id,
            action="TIMETABLE_ENTRY_DELETED",
            entity_type="TimetableEntry",
            entity_id=entry.id,
            details={"entry_id": str(entry_id)},
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()
