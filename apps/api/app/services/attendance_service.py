"""Attendance Management Engine Service.

Handles attendance policy, timetable-driven session generation, bulk roster marking,
locked session immutability, audit logging, student leave workflows, attendance corrections,
dynamic attendance percentage aggregation, and low-attendance alerts.
"""

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    ConflictException,
    NotFoundException,
    PermissionDeniedException,
    ValidationException,
)
from app.models.academics import (
    CourseEnrollment,
    CourseFacultyAssignment,
    CourseOffering,
    Subject,
    TimetableEntry,
)
from app.models.attendance import (
    AttendanceAlert,
    AttendanceCorrectionRequest,
    AttendancePolicy,
    AttendanceRecord,
    AttendanceSession,
    StudentLeaveRequest,
)
from app.models.audit import AuditLog
from app.models.core import AcademicYear, Section, Semester
from app.models.people import FacultyProfile, StudentProfile, User
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
    AttendanceRosterStudentItem,
    AttendanceSessionCreateRequest,
    AttendanceSessionDetailResponse,
    AttendanceSessionFromTimetableRequest,
    AttendanceSessionResponse,
    AttendanceSessionUpdateRequest,
    CourseOfferingAttendanceSummary,
    CourseOfferingStudentAttendanceItem,
    LowAttendanceStudentItem,
    StudentCourseAttendanceSummary,
    StudentLeaveCreateRequest,
    StudentLeaveResponse,
    StudentLeaveReviewRequest,
    StudentOverallAttendanceSummary,
)


class AttendanceService:
    # -------------------------------------------------------------------------
    # AUDIT LOG HELPER
    # -------------------------------------------------------------------------
    @staticmethod
    def _serialize_audit_values(val: Any) -> Any:
        if isinstance(val, dict):
            return {k: AttendanceService._serialize_audit_values(v) for k, v in val.items()}
        elif isinstance(val, list):
            return [AttendanceService._serialize_audit_values(v) for v in val]
        elif isinstance(val, Decimal):
            return float(val)
        elif isinstance(val, (date, datetime)):
            return val.isoformat()
        elif isinstance(val, UUID):
            return str(val)
        return val

    @classmethod
    def _create_audit(
        cls,
        tenant_id: UUID,
        user_id: UUID | None,
        action: str,
        entity_type: str,
        entity_id: UUID,
        details: dict[str, Any] | None = None,
        ip_address: str = "127.0.0.1",
        business_context: str | None = None,
    ) -> AuditLog:
        serialized_details = cls._serialize_audit_values(details) if details else None
        return AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            new_values_json=serialized_details,
            ip_address=ip_address or "127.0.0.1",
            business_context=business_context,
        )

    # -------------------------------------------------------------------------
    # 1. ATTENDANCE POLICY MANAGEMENT & RESOLUTION
    # -------------------------------------------------------------------------
    @classmethod
    async def create_policy(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        payload: AttendancePolicyCreateRequest,
        user_id: UUID | None,
        ip_address: str = "127.0.0.1",
    ) -> AttendancePolicyResponse:
        policy = AttendancePolicy(
            tenant_id=tenant_id,
            name=payload.name,
            department_id=payload.department_id,
            program_id=payload.program_id,
            academic_year_id=payload.academic_year_id,
            semester_id=payload.semester_id,
            course_offering_id=payload.course_offering_id,
            minimum_percentage=payload.minimum_percentage,
            warning_threshold_percentage=payload.warning_threshold_percentage,
            critical_threshold_percentage=payload.critical_threshold_percentage,
            condonation_percentage=payload.condonation_percentage,
            late_grace_minutes=payload.late_grace_minutes,
            late_weight=payload.late_weight,
            excused_counts_as_present=payload.excused_counts_as_present,
            on_leave_counts_as_present=payload.on_leave_counts_as_present,
            exclude_excused_from_total=payload.exclude_excused_from_total,
            effective_from=payload.effective_from,
            effective_to=payload.effective_to,
            status=payload.status,
            is_active=True,
        )
        db.add(policy)
        await db.flush()

        audit = cls._create_audit(
            tenant_id=tenant_id,
            user_id=user_id,
            action="ATTENDANCE_POLICY_CREATED",
            entity_type="attendance_policy",
            entity_id=policy.id,
            details={"name": policy.name, "min": float(policy.minimum_percentage)},
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()
        await db.refresh(policy)
        return AttendancePolicyResponse.model_validate(policy)

    @classmethod
    async def update_policy(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        policy_id: UUID,
        payload: AttendancePolicyUpdateRequest,
        user_id: UUID | None,
        ip_address: str = "127.0.0.1",
    ) -> AttendancePolicyResponse:
        stmt = select(AttendancePolicy).where(
            AttendancePolicy.id == policy_id,
            AttendancePolicy.tenant_id == tenant_id,
        )
        res = await db.execute(stmt)
        policy = res.scalar_one_or_none()
        if not policy:
            raise NotFoundException("AttendancePolicy", policy_id)

        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(policy, key, value)

        audit = cls._create_audit(
            tenant_id=tenant_id,
            user_id=user_id,
            action="ATTENDANCE_POLICY_UPDATED",
            entity_type="attendance_policy",
            entity_id=policy.id,
            details=update_data,
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()
        await db.refresh(policy)
        return AttendancePolicyResponse.model_validate(policy)

    @classmethod
    async def list_policies(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
    ) -> list[AttendancePolicyResponse]:
        stmt = (
            select(AttendancePolicy)
            .where(AttendancePolicy.tenant_id == tenant_id)
            .order_by(AttendancePolicy.created_at.desc())
        )
        res = await db.execute(stmt)
        policies = res.scalars().all()
        return [AttendancePolicyResponse.model_validate(p) for p in policies]

    @classmethod
    async def resolve_effective_policy(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        course_offering_id: UUID | None = None,
        semester_id: UUID | None = None,
        program_id: UUID | None = None,
        department_id: UUID | None = None,
    ) -> AttendancePolicy:
        """Resolve attendance policy following specificity precedence."""
        # 1. Course Offering level
        if course_offering_id:
            stmt = select(AttendancePolicy).where(
                AttendancePolicy.tenant_id == tenant_id,
                AttendancePolicy.course_offering_id == course_offering_id,
                AttendancePolicy.is_active.is_(True),
            )
            res = await db.execute(stmt)
            p = res.scalar_one_or_none()
            if p:
                return p

        # 2. Semester level
        if semester_id:
            stmt = select(AttendancePolicy).where(
                AttendancePolicy.tenant_id == tenant_id,
                AttendancePolicy.semester_id == semester_id,
                AttendancePolicy.is_active.is_(True),
            )
            res = await db.execute(stmt)
            p = res.scalar_one_or_none()
            if p:
                return p

        # 3. Program level
        if program_id:
            stmt = select(AttendancePolicy).where(
                AttendancePolicy.tenant_id == tenant_id,
                AttendancePolicy.program_id == program_id,
                AttendancePolicy.is_active.is_(True),
            )
            res = await db.execute(stmt)
            p = res.scalar_one_or_none()
            if p:
                return p

        # 4. Department level
        if department_id:
            stmt = select(AttendancePolicy).where(
                AttendancePolicy.tenant_id == tenant_id,
                AttendancePolicy.department_id == department_id,
                AttendancePolicy.is_active.is_(True),
            )
            res = await db.execute(stmt)
            p = res.scalar_one_or_none()
            if p:
                return p

        # 5. Institutional default
        stmt = (
            select(AttendancePolicy)
            .where(
                AttendancePolicy.tenant_id == tenant_id,
                AttendancePolicy.course_offering_id.is_(None),
                AttendancePolicy.semester_id.is_(None),
                AttendancePolicy.program_id.is_(None),
                AttendancePolicy.department_id.is_(None),
                AttendancePolicy.is_active.is_(True),
            )
            .order_by(AttendancePolicy.created_at.desc())
        )
        res = await db.execute(stmt)
        p = res.scalar_one_or_none()
        if p:
            return p

        # 6. Fallback in-memory policy
        return AttendancePolicy(
            tenant_id=tenant_id,
            name="Default Standard Policy",
            minimum_percentage=Decimal("75.00"),
            warning_threshold_percentage=Decimal("80.00"),
            critical_threshold_percentage=Decimal("65.00"),
            condonation_percentage=Decimal("65.00"),
            late_grace_minutes=10,
            late_weight=Decimal("1.00"),
            excused_counts_as_present=True,
            on_leave_counts_as_present=False,
            exclude_excused_from_total=False,
            is_active=True,
            status="ACTIVE",
        )

    # -------------------------------------------------------------------------
    # 2. ATTENDANCE SESSIONS & TIMETABLE INTEGRATION
    # -------------------------------------------------------------------------
    @classmethod
    async def create_session(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        payload: AttendanceSessionCreateRequest,
        user_id: UUID | None,
        ip_address: str = "127.0.0.1",
        skip_faculty_check: bool = False,
    ) -> AttendanceSessionResponse:
        # 1. Validate course offering
        offering_stmt = (
            select(CourseOffering)
            .options(
                selectinload(CourseOffering.academic_year),
                selectinload(CourseOffering.semester),
                selectinload(CourseOffering.faculty_assignments),
            )
            .where(
                CourseOffering.id == payload.course_offering_id,
                CourseOffering.tenant_id == tenant_id,
            )
        )
        offering_res = await db.execute(offering_stmt)
        offering = offering_res.scalar_one_or_none()
        if not offering:
            raise NotFoundException("CourseOffering", payload.course_offering_id)

        if offering.status == "CANCELLED":
            raise ValidationException("Cannot schedule an attendance session for a cancelled course offering.")

        # 2. Section validation
        if offering.section_id != payload.section_id:
            raise ValidationException("Section does not match the course offering's designated cohort section.")

        # 3. Academic period date validation
        acad_year = offering.academic_year
        if acad_year:
            if payload.session_date < acad_year.start_date or payload.session_date > acad_year.end_date:
                raise ValidationException(
                    f"Session date {payload.session_date} is outside Academic Year period "
                    f"({acad_year.start_date} to {acad_year.end_date})."
                )

        semester = offering.semester
        if semester and semester.start_date and semester.end_date:
            if payload.session_date < semester.start_date or payload.session_date > semester.end_date:
                raise ValidationException(
                    f"Session date {payload.session_date} is outside Semester period "
                    f"({semester.start_date} to {semester.end_date})."
                )

        # 4. Faculty authorization check
        if not skip_faculty_check:
            assigned_faculty_ids = {fa.faculty_id for fa in offering.faculty_assignments if fa.is_active}
            if payload.faculty_id not in assigned_faculty_ids:
                raise ValidationException(
                    f"Faculty member {payload.faculty_id} is not assigned to course offering {offering.id}."
                )

        # 5. Duplicate slot check
        dup_stmt = select(AttendanceSession).where(
            AttendanceSession.tenant_id == tenant_id,
            AttendanceSession.course_offering_id == payload.course_offering_id,
            AttendanceSession.session_date == payload.session_date,
            AttendanceSession.period_number == payload.period_number,
        )
        dup_res = await db.execute(dup_stmt)
        if dup_res.scalar_one_or_none():
            raise ConflictException(
                "AttendanceSession",
                "period_number",
                f"{payload.period_number} on {payload.session_date}",
            )

        session = AttendanceSession(
            tenant_id=tenant_id,
            course_offering_id=payload.course_offering_id,
            section_id=payload.section_id,
            faculty_id=payload.faculty_id,
            academic_year_id=payload.academic_year_id or offering.academic_year_id,
            semester_id=payload.semester_id or offering.semester_id,
            timetable_slot_id=payload.timetable_slot_id,
            room_id=payload.room_id,
            time_slot_id=payload.time_slot_id,
            session_date=payload.session_date,
            period_number=payload.period_number,
            start_time=payload.start_time,
            end_time=payload.end_time,
            session_type=payload.session_type,
            status="SCHEDULED",
            topic=payload.topic,
        )
        db.add(session)
        await db.flush()

        audit = cls._create_audit(
            tenant_id=tenant_id,
            user_id=user_id,
            action="ATTENDANCE_SESSION_CREATED",
            entity_type="attendance_session",
            entity_id=session.id,
            details={
                "course_offering_id": str(session.course_offering_id),
                "date": session.session_date.isoformat(),
                "period": session.period_number,
            },
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()

        return await cls.get_session_response(db, tenant_id, session.id)

    @classmethod
    async def create_session_from_timetable(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        payload: AttendanceSessionFromTimetableRequest,
        user_id: UUID | None,
        ip_address: str = "127.0.0.1",
    ) -> AttendanceSessionResponse:
        stmt = (
            select(TimetableEntry)
            .options(
                selectinload(TimetableEntry.time_slot),
                selectinload(TimetableEntry.course_offering),
            )
            .where(
                TimetableEntry.id == payload.timetable_entry_id,
                TimetableEntry.tenant_id == tenant_id,
            )
        )
        res = await db.execute(stmt)
        tt_entry = res.scalar_one_or_none()
        if not tt_entry:
            raise NotFoundException("TimetableEntry", payload.timetable_entry_id)

        if not tt_entry.is_active:
            raise ValidationException("Cannot instantiate attendance session from an inactive timetable entry.")

        # Period number from slot_number
        period_number = tt_entry.time_slot.slot_number if tt_entry.time_slot else 1

        # Check if session already exists
        existing_stmt = select(AttendanceSession).where(
            AttendanceSession.tenant_id == tenant_id,
            AttendanceSession.course_offering_id == tt_entry.course_offering_id,
            AttendanceSession.session_date == payload.session_date,
            AttendanceSession.period_number == period_number,
        )
        existing_res = await db.execute(existing_stmt)
        existing_session = existing_res.scalar_one_or_none()
        if existing_session:
            return await cls.get_session_response(db, tenant_id, existing_session.id)

        # Fallback faculty: primary faculty on offering or tt_entry.faculty_id
        faculty_id = tt_entry.faculty_id
        if not faculty_id:
            # Pick primary faculty from course offering
            assign_stmt = select(CourseFacultyAssignment).where(
                CourseFacultyAssignment.course_offering_id == tt_entry.course_offering_id,
                CourseFacultyAssignment.is_active.is_(True),
            )
            assign_res = await db.execute(assign_stmt)
            assignment = assign_res.scalars().first()
            if assignment:
                faculty_id = assignment.faculty_id
            else:
                raise ValidationException("No active faculty assigned to this timetable entry or course offering.")

        session_create_req = AttendanceSessionCreateRequest(
            course_offering_id=tt_entry.course_offering_id,
            section_id=tt_entry.section_id,
            faculty_id=faculty_id,
            academic_year_id=tt_entry.academic_year_id,
            semester_id=tt_entry.semester_id,
            session_date=payload.session_date,
            period_number=period_number,
            session_type="LECTURE",
            timetable_slot_id=tt_entry.id,
            room_id=tt_entry.room_id,
            time_slot_id=tt_entry.time_slot_id,
            start_time=tt_entry.time_slot.start_time if tt_entry.time_slot else None,
            end_time=tt_entry.time_slot.end_time if tt_entry.time_slot else None,
            topic=payload.topic,
        )

        return await cls.create_session(
            db, tenant_id, session_create_req, user_id=user_id, ip_address=ip_address, skip_faculty_check=True
        )

    @classmethod
    async def open_session(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        session_id: UUID,
        user_id: UUID | None,
        ip_address: str = "127.0.0.1",
    ) -> AttendanceSessionResponse:
        stmt = select(AttendanceSession).where(
            AttendanceSession.id == session_id,
            AttendanceSession.tenant_id == tenant_id,
        )
        res = await db.execute(stmt)
        session = res.scalar_one_or_none()
        if not session:
            raise NotFoundException("AttendanceSession", session_id)

        if session.status == "LOCKED":
            raise ValidationException("Cannot open a session that has already been locked.")
        if session.status == "CANCELLED":
            raise ValidationException("Cannot open a cancelled attendance session.")

        session.status = "OPEN"
        audit = cls._create_audit(
            tenant_id=tenant_id,
            user_id=user_id,
            action="ATTENDANCE_SESSION_OPENED",
            entity_type="attendance_session",
            entity_id=session.id,
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()

        return await cls.get_session_response(db, tenant_id, session.id)

    @classmethod
    async def lock_session(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        session_id: UUID,
        user_id: UUID | None,
        ip_address: str = "127.0.0.1",
    ) -> AttendanceSessionResponse:
        stmt = select(AttendanceSession).where(
            AttendanceSession.id == session_id,
            AttendanceSession.tenant_id == tenant_id,
        )
        res = await db.execute(stmt)
        session = res.scalar_one_or_none()
        if not session:
            raise NotFoundException("AttendanceSession", session_id)

        if session.status == "LOCKED":
            return await cls.get_session_response(db, tenant_id, session.id)

        session.status = "LOCKED"
        session.locked_at = datetime.now(UTC)
        session.locked_by_user_id = user_id

        audit = cls._create_audit(
            tenant_id=tenant_id,
            user_id=user_id,
            action="ATTENDANCE_LOCKED",
            entity_type="attendance_session",
            entity_id=session.id,
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()

        return await cls.get_session_response(db, tenant_id, session.id)

    @classmethod
    async def update_session(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        session_id: UUID,
        payload: AttendanceSessionUpdateRequest,
        user_id: UUID | None,
        ip_address: str = "127.0.0.1",
    ) -> AttendanceSessionResponse:
        stmt = select(AttendanceSession).where(
            AttendanceSession.id == session_id,
            AttendanceSession.tenant_id == tenant_id,
        )
        res = await db.execute(stmt)
        session = res.scalar_one_or_none()
        if not session:
            raise NotFoundException("AttendanceSession", session_id)

        if session.status == "LOCKED":
            raise ValidationException("Cannot edit metadata of a locked attendance session.")

        update_data = payload.model_dump(exclude_unset=True)
        for k, v in update_data.items():
            setattr(session, k, v)

        audit = cls._create_audit(
            tenant_id=tenant_id,
            user_id=user_id,
            action="ATTENDANCE_SESSION_UPDATED",
            entity_type="attendance_session",
            entity_id=session.id,
            details=update_data,
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()

        return await cls.get_session_response(db, tenant_id, session.id)

    @classmethod
    async def get_session_response(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        session_id: UUID,
    ) -> AttendanceSessionResponse:
        stmt = (
            select(AttendanceSession)
            .options(
                selectinload(AttendanceSession.course_offering).selectinload(CourseOffering.subject),
                selectinload(AttendanceSession.section),
                selectinload(AttendanceSession.faculty).selectinload(FacultyProfile.user),
                selectinload(AttendanceSession.room),
                selectinload(AttendanceSession.records),
            )
            .where(
                AttendanceSession.id == session_id,
                AttendanceSession.tenant_id == tenant_id,
            )
        )
        res = await db.execute(stmt)
        s = res.scalar_one_or_none()
        if not s:
            raise NotFoundException("AttendanceSession", session_id)

        # Count records
        p_count = sum(1 for r in s.records if r.status == "PRESENT")
        a_count = sum(1 for r in s.records if r.status == "ABSENT")
        l_count = sum(1 for r in s.records if r.status == "LATE")
        e_count = sum(1 for r in s.records if r.status == "EXCUSED")
        ol_count = sum(1 for r in s.records if r.status == "ON_LEAVE")
        tot_records = len(s.records)

        # If records not yet created, count active enrollments
        enrolled_count = tot_records
        if tot_records == 0:
            enr_stmt = select(func.count(CourseEnrollment.id)).where(
                CourseEnrollment.course_offering_id == s.course_offering_id,
                CourseEnrollment.status == "ENROLLED",
            )
            enr_res = await db.execute(enr_stmt)
            enrolled_count = enr_res.scalar() or 0

        course_code = s.course_offering.subject.code if s.course_offering and s.course_offering.subject else None
        course_name = s.course_offering.subject.name if s.course_offering and s.course_offering.subject else None
        section_name = s.section.name if s.section else None
        faculty_name = (
            f"{s.faculty.user.first_name} {s.faculty.user.last_name}"
            if s.faculty and s.faculty.user
            else None
        )
        room_name = s.room.name if s.room else None

        return AttendanceSessionResponse(
            id=s.id,
            tenant_id=s.tenant_id,
            course_offering_id=s.course_offering_id,
            course_code=course_code,
            course_name=course_name,
            section_id=s.section_id,
            section_name=section_name,
            faculty_id=s.faculty_id,
            faculty_name=faculty_name,
            academic_year_id=s.academic_year_id,
            semester_id=s.semester_id,
            session_date=s.session_date,
            period_number=s.period_number,
            session_type=s.session_type,
            status=s.status,
            topic=s.topic,
            start_time=s.start_time,
            end_time=s.end_time,
            room_id=s.room_id,
            room_name=room_name,
            timetable_slot_id=s.timetable_slot_id,
            total_enrolled=enrolled_count,
            total_present=p_count,
            total_absent=a_count,
            total_late=l_count,
            total_excused=e_count,
            total_on_leave=ol_count,
            submitted_at=s.submitted_at,
            locked_at=s.locked_at,
            locked_by_user_id=s.locked_by_user_id,
            created_at=s.created_at,
            updated_at=s.updated_at,
        )

    @classmethod
    async def list_sessions(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        session_date: date | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        course_offering_id: UUID | None = None,
        faculty_id: UUID | None = None,
        section_id: UUID | None = None,
        semester_id: UUID | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[AttendanceSessionResponse], int]:
        filters = [AttendanceSession.tenant_id == tenant_id]

        if session_date:
            filters.append(AttendanceSession.session_date == session_date)
        if start_date:
            filters.append(AttendanceSession.session_date >= start_date)
        if end_date:
            filters.append(AttendanceSession.session_date <= end_date)
        if course_offering_id:
            filters.append(AttendanceSession.course_offering_id == course_offering_id)
        if faculty_id:
            filters.append(AttendanceSession.faculty_id == faculty_id)
        if section_id:
            filters.append(AttendanceSession.section_id == section_id)
        if semester_id:
            filters.append(AttendanceSession.semester_id == semester_id)
        if status:
            filters.append(AttendanceSession.status == status)

        count_stmt = select(func.count(AttendanceSession.id)).where(and_(*filters))
        count_res = await db.execute(count_stmt)
        total_records = count_res.scalar() or 0

        stmt = (
            select(AttendanceSession)
            .options(
                selectinload(AttendanceSession.course_offering).selectinload(CourseOffering.subject),
                selectinload(AttendanceSession.section),
                selectinload(AttendanceSession.faculty).selectinload(FacultyProfile.user),
                selectinload(AttendanceSession.room),
                selectinload(AttendanceSession.records),
            )
            .where(and_(*filters))
            .order_by(AttendanceSession.session_date.desc(), AttendanceSession.period_number.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        res = await db.execute(stmt)
        sessions = res.scalars().all()

        responses = []
        for s in sessions:
            p_count = sum(1 for r in s.records if r.status == "PRESENT")
            a_count = sum(1 for r in s.records if r.status == "ABSENT")
            l_count = sum(1 for r in s.records if r.status == "LATE")
            e_count = sum(1 for r in s.records if r.status == "EXCUSED")
            ol_count = sum(1 for r in s.records if r.status == "ON_LEAVE")
            tot_records = len(s.records)

            course_code = s.course_offering.subject.code if s.course_offering and s.course_offering.subject else None
            course_name = s.course_offering.subject.name if s.course_offering and s.course_offering.subject else None
            section_name = s.section.name if s.section else None
            faculty_name = (
                f"{s.faculty.user.first_name} {s.faculty.user.last_name}"
                if s.faculty and s.faculty.user
                else None
            )
            room_name = s.room.name if s.room else None

            responses.append(
                AttendanceSessionResponse(
                    id=s.id,
                    tenant_id=s.tenant_id,
                    course_offering_id=s.course_offering_id,
                    course_code=course_code,
                    course_name=course_name,
                    section_id=s.section_id,
                    section_name=section_name,
                    faculty_id=s.faculty_id,
                    faculty_name=faculty_name,
                    academic_year_id=s.academic_year_id,
                    semester_id=s.semester_id,
                    session_date=s.session_date,
                    period_number=s.period_number,
                    session_type=s.session_type,
                    status=s.status,
                    topic=s.topic,
                    start_time=s.start_time,
                    end_time=s.end_time,
                    room_id=s.room_id,
                    room_name=room_name,
                    timetable_slot_id=s.timetable_slot_id,
                    total_enrolled=tot_records,
                    total_present=p_count,
                    total_absent=a_count,
                    total_late=l_count,
                    total_excused=e_count,
                    total_on_leave=ol_count,
                    submitted_at=s.submitted_at,
                    locked_at=s.locked_at,
                    locked_by_user_id=s.locked_by_user_id,
                    created_at=s.created_at,
                    updated_at=s.updated_at,
                )
            )

        return responses, total_records

    @classmethod
    async def get_session_detail(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        session_id: UUID,
    ) -> AttendanceSessionDetailResponse:
        session_resp = await cls.get_session_response(db, tenant_id, session_id)

        # 1. Fetch course enrollments for this offering
        enrollment_stmt = (
            select(CourseEnrollment)
            .options(
                selectinload(CourseEnrollment.student).selectinload(StudentProfile.user)
            )
            .where(
                CourseEnrollment.course_offering_id == session_resp.course_offering_id,
                CourseEnrollment.status == "ENROLLED",
            )
            .order_by(CourseEnrollment.student_id)
        )
        enr_res = await db.execute(enrollment_stmt)
        enrollments = enr_res.scalars().all()

        # 2. Fetch existing records for this session
        records_stmt = (
            select(AttendanceRecord)
            .options(
                selectinload(AttendanceRecord.student).selectinload(StudentProfile.user)
            )
            .where(
                AttendanceRecord.session_id == session_id,
                AttendanceRecord.tenant_id == tenant_id,
            )
        )
        rec_res = await db.execute(records_stmt)
        records = rec_res.scalars().all()
        records_by_student = {r.student_id: r for r in records}

        # 3. Fetch approved leaves covering session date for enrolled students
        student_ids = [e.student_id for e in enrollments]
        leave_stmt = select(StudentLeaveRequest).where(
            StudentLeaveRequest.tenant_id == tenant_id,
            StudentLeaveRequest.student_id.in_(student_ids),
            StudentLeaveRequest.status == "APPROVED",
            StudentLeaveRequest.start_date <= session_resp.session_date,
            StudentLeaveRequest.end_date >= session_resp.session_date,
        )
        leave_res = await db.execute(leave_stmt)
        leaves_by_student = {l.student_id: l for l in leave_res.scalars().all()}

        roster_items: list[AttendanceRosterStudentItem] = []
        for enr in enrollments:
            stud = enr.student
            existing_rec = records_by_student.get(enr.student_id)
            approved_leave = leaves_by_student.get(enr.student_id)

            curr_status = existing_rec.status if existing_rec else None
            remarks = existing_rec.remarks if existing_rec else None

            # If not yet marked, default to ON_LEAVE if approved leave exists, else PRESENT
            if curr_status is None:
                curr_status = "ON_LEAVE" if approved_leave else "PRESENT"

            roster_items.append(
                AttendanceRosterStudentItem(
                    student_id=stud.id,
                    roll_number=stud.roll_number,
                    admission_number=stud.admission_number,
                    student_name=f"{stud.first_name} {stud.last_name}",
                    enrollment_status=enr.status,
                    current_status=curr_status,
                    remarks=remarks,
                    has_approved_leave=bool(approved_leave),
                    leave_reason=approved_leave.reason if approved_leave else None,
                )
            )

        # Sort roster alphabetically by roll_number or student_name
        roster_items.sort(key=lambda x: (x.roll_number or "", x.student_name))

        record_responses = []
        for r in records:
            s_name = f"{r.student.first_name} {r.student.last_name}" if r.student else None
            r_num = r.student.roll_number if r.student else None
            a_num = r.student.admission_number if r.student else None
            record_responses.append(
                AttendanceRecordResponse(
                    id=r.id,
                    session_id=r.session_id,
                    student_id=r.student_id,
                    student_roll_number=r_num,
                    student_admission_number=a_num,
                    student_name=s_name,
                    status=r.status,
                    remarks=r.remarks,
                    recorded_by_user_id=r.recorded_by_user_id,
                    has_approved_leave=r.student_id in leaves_by_student,
                    created_at=r.created_at,
                    updated_at=r.updated_at,
                )
            )

        return AttendanceSessionDetailResponse(
            session=session_resp,
            roster=roster_items,
            records=record_responses,
        )

    # -------------------------------------------------------------------------
    # 3. BULK ATTENDANCE RECORDING & IMMUTABILITY
    # -------------------------------------------------------------------------
    @classmethod
    async def submit_bulk_records(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        session_id: UUID,
        payload: AttendanceRecordBulkSubmitRequest,
        user_id: UUID,
        ip_address: str = "127.0.0.1",
        faculty_user: User | None = None,
    ) -> AttendanceSessionResponse:
        # 1. Fetch and validate session
        stmt = (
            select(AttendanceSession)
            .options(
                selectinload(AttendanceSession.course_offering).selectinload(CourseOffering.faculty_assignments),
            )
            .where(
                AttendanceSession.id == session_id,
                AttendanceSession.tenant_id == tenant_id,
            )
        )
        res = await db.execute(stmt)
        session = res.scalar_one_or_none()
        if not session:
            raise NotFoundException("AttendanceSession", session_id)

        # 2. Immutability guard
        if session.status == "LOCKED":
            raise ValidationException(
                "Attendance session is locked. Ordinary modifications are forbidden; "
                "submit an attendance correction request."
            )
        if session.status == "CANCELLED":
            raise ValidationException("Cannot mark attendance for a cancelled session.")

        # 3. Faculty authorization check
        if faculty_user:
            user_roles = {ur.role.name for ur in faculty_user.roles if ur.role}
            is_admin_or_hod = bool({"SUPER_ADMIN", "INSTITUTION_ADMIN", "PRINCIPAL", "HOD"} & user_roles)
            if not is_admin_or_hod:
                # User must be an assigned faculty profile
                fac_stmt = select(FacultyProfile).where(
                    FacultyProfile.user_id == faculty_user.id,
                    FacultyProfile.tenant_id == tenant_id,
                )
                fac_res = await db.execute(fac_stmt)
                fac_profile = fac_res.scalar_one_or_none()
                if not fac_profile:
                    raise PermissionDeniedException("attendance:mark")

                assigned_faculty_ids = {
                    fa.faculty_id
                    for fa in session.course_offering.faculty_assignments
                    if fa.is_active
                }
                if fac_profile.id not in assigned_faculty_ids and session.faculty_id != fac_profile.id:
                    raise PermissionDeniedException(
                        f"Faculty member {fac_profile.id} is not authorized to submit attendance "
                        f"for course offering {session.course_offering_id}."
                    )

        # 4. Check for payload internal duplicates
        seen_student_ids: set[UUID] = set()
        for item in payload.records:
            if item.student_id in seen_student_ids:
                raise ValidationException(f"Duplicate student_id '{item.student_id}' in attendance payload.")
            seen_student_ids.add(item.student_id)

        # 5. Validate that all submitted students are actively enrolled in this course offering
        enrolled_stmt = select(CourseEnrollment.student_id).where(
            CourseEnrollment.course_offering_id == session.course_offering_id,
            CourseEnrollment.status == "ENROLLED",
        )
        enrolled_res = await db.execute(enrolled_stmt)
        valid_enrolled_student_ids = set(enrolled_res.scalars().all())

        for s_id in seen_student_ids:
            if s_id not in valid_enrolled_student_ids:
                raise ValidationException(
                    f"Student '{s_id}' is not enrolled in course offering {session.course_offering_id}."
                )

        # 6. Fetch existing records for upsert
        rec_stmt = select(AttendanceRecord).where(
            AttendanceRecord.session_id == session_id,
        )
        rec_res = await db.execute(rec_stmt)
        existing_records_by_student = {r.student_id: r for r in rec_res.scalars().all()}

        allowed_statuses = {"PRESENT", "ABSENT", "LATE", "EXCUSED", "ON_LEAVE"}
        records_to_add = []

        for item in payload.records:
            if item.status not in allowed_statuses:
                raise ValidationException(f"Invalid attendance status '{item.status}'.")

            if item.student_id in existing_records_by_student:
                record = existing_records_by_student[item.student_id]
                record.status = item.status
                record.remarks = item.remarks
                record.recorded_by_user_id = user_id
            else:
                record = AttendanceRecord(
                    tenant_id=tenant_id,
                    session_id=session_id,
                    student_id=item.student_id,
                    status=item.status,
                    remarks=item.remarks,
                    recorded_by_user_id=user_id,
                )
                records_to_add.append(record)

        if records_to_add:
            db.add_all(records_to_add)

        # 7. Update session status
        session.status = "MARKED"
        session.submitted_at = datetime.now(UTC)

        if payload.auto_lock:
            session.status = "LOCKED"
            session.locked_at = datetime.now(UTC)
            session.locked_by_user_id = user_id

        # 8. Audit log
        audit = cls._create_audit(
            tenant_id=tenant_id,
            user_id=user_id,
            action="ATTENDANCE_MARKED",
            entity_type="attendance_session",
            entity_id=session.id,
            details={
                "records_count": len(payload.records),
                "auto_lock": payload.auto_lock,
            },
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()

        return await cls.get_session_response(db, tenant_id, session.id)

    @classmethod
    async def update_single_record(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        record_id: UUID,
        payload: AttendanceRecordUpdateRequest,
        user_id: UUID,
        ip_address: str = "127.0.0.1",
    ) -> AttendanceRecordResponse:
        stmt = (
            select(AttendanceRecord)
            .options(
                selectinload(AttendanceRecord.session),
                selectinload(AttendanceRecord.student).selectinload(StudentProfile.user),
            )
            .where(
                AttendanceRecord.id == record_id,
                AttendanceRecord.tenant_id == tenant_id,
            )
        )
        res = await db.execute(stmt)
        record = res.scalar_one_or_none()
        if not record:
            raise NotFoundException("AttendanceRecord", record_id)

        if record.session.status == "LOCKED":
            raise ValidationException(
                "Session is locked. Direct modifications are not permitted; "
                "submit an attendance correction request."
            )

        allowed_statuses = {"PRESENT", "ABSENT", "LATE", "EXCUSED", "ON_LEAVE"}
        if payload.status not in allowed_statuses:
            raise ValidationException(f"Invalid attendance status '{payload.status}'.")

        old_status = record.status
        record.status = payload.status
        if payload.remarks is not None:
            record.remarks = payload.remarks
        record.recorded_by_user_id = user_id

        audit = cls._create_audit(
            tenant_id=tenant_id,
            user_id=user_id,
            action="ATTENDANCE_RECORD_UPDATED",
            entity_type="attendance_record",
            entity_id=record.id,
            details={"old_status": old_status, "new_status": record.status},
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()
        await db.refresh(record)

        return AttendanceRecordResponse(
            id=record.id,
            session_id=record.session_id,
            student_id=record.student_id,
            student_roll_number=record.student.roll_number if record.student else None,
            student_admission_number=record.student.admission_number if record.student else None,
            student_name=f"{record.student.first_name} {record.student.last_name}" if record.student else None,
            status=record.status,
            remarks=record.remarks,
            recorded_by_user_id=record.recorded_by_user_id,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    # -------------------------------------------------------------------------
    # 4. ATTENDANCE AGGREGATION & SUMMARY ENGINE
    # -------------------------------------------------------------------------
    @classmethod
    async def get_student_summary(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        student_id: UUID,
        semester_id: UUID | None = None,
    ) -> StudentOverallAttendanceSummary:
        # 1. Fetch student
        stud_stmt = (
            select(StudentProfile)
            .options(
                selectinload(StudentProfile.user),
                selectinload(StudentProfile.program),
                selectinload(StudentProfile.current_section),
            )
            .where(
                StudentProfile.id == student_id,
                StudentProfile.tenant_id == tenant_id,
            )
        )
        stud_res = await db.execute(stud_stmt)
        student = stud_res.scalar_one_or_none()
        if not student:
            raise NotFoundException("StudentProfile", student_id)

        # 2. Fetch enrolled courses
        enr_filters = [
            CourseEnrollment.student_id == student_id,
            CourseEnrollment.tenant_id == tenant_id,
            CourseEnrollment.status == "ENROLLED",
        ]
        if semester_id:
            enr_filters.append(CourseOffering.semester_id == semester_id)

        enr_stmt = (
            select(CourseEnrollment)
            .join(CourseOffering, CourseEnrollment.course_offering_id == CourseOffering.id)
            .options(
                selectinload(CourseEnrollment.course_offering)
                .selectinload(CourseOffering.subject),
                selectinload(CourseEnrollment.course_offering)
                .selectinload(CourseOffering.faculty_assignments)
                .selectinload(CourseFacultyAssignment.faculty)
                .selectinload(FacultyProfile.user),
            )
            .where(and_(*enr_filters))
        )
        enr_res = await db.execute(enr_stmt)
        enrollments = enr_res.scalars().all()

        courses_summary: list[StudentCourseAttendanceSummary] = []
        total_conducted_all = 0
        total_attended_all = Decimal("0.00")

        # Fallback default policy for overall minimum
        default_policy = await cls.resolve_effective_policy(db, tenant_id)

        for enr in enrollments:
            offering = enr.course_offering
            policy = await cls.resolve_effective_policy(
                db,
                tenant_id,
                course_offering_id=offering.id,
                semester_id=offering.semester_id,
                program_id=student.program_id,
            )

            # Fetch all conducted sessions for this offering
            sess_stmt = (
                select(AttendanceSession)
                .where(
                    AttendanceSession.course_offering_id == offering.id,
                    AttendanceSession.tenant_id == tenant_id,
                    AttendanceSession.status.in_(["MARKED", "LOCKED"]),
                )
            )
            sess_res = await db.execute(sess_stmt)
            conducted_sessions = sess_res.scalars().all()
            conducted_session_ids = [s.id for s in conducted_sessions]
            total_conducted = len(conducted_session_ids)

            # Fetch records for this student in these sessions
            if conducted_session_ids:
                rec_stmt = select(AttendanceRecord).where(
                    AttendanceRecord.session_id.in_(conducted_session_ids),
                    AttendanceRecord.student_id == student_id,
                )
                rec_res = await db.execute(rec_stmt)
                records = rec_res.scalars().all()
            else:
                records = []

            p_cnt = sum(1 for r in records if r.status == "PRESENT")
            a_cnt = sum(1 for r in records if r.status == "ABSENT")
            l_cnt = sum(1 for r in records if r.status == "LATE")
            e_cnt = sum(1 for r in records if r.status == "EXCUSED")
            ol_cnt = sum(1 for r in records if r.status == "ON_LEAVE")

            # Determine denominator (eligible sessions)
            eligible_sessions = total_conducted
            if policy.exclude_excused_from_total:
                eligible_sessions -= e_cnt

            # Determine numerator (attended sessions)
            attended = Decimal(p_cnt) + (Decimal(l_cnt) * policy.late_weight)
            if policy.excused_counts_as_present:
                attended += Decimal(e_cnt)
            if policy.on_leave_counts_as_present:
                attended += Decimal(ol_cnt)

            if eligible_sessions > 0:
                pct = round((attended / Decimal(eligible_sessions)) * Decimal(100), 2)
            else:
                pct = Decimal("100.00")

            if pct < policy.critical_threshold_percentage:
                course_status = "CRITICAL"
            elif pct < policy.minimum_percentage:
                course_status = "WARNING"
            else:
                course_status = "NORMAL"

            # Primary faculty name
            primary_fac_name = None
            for fa in offering.faculty_assignments:
                if fa.is_active and fa.faculty and fa.faculty.user:
                    primary_fac_name = f"{fa.faculty.user.first_name} {fa.faculty.user.last_name}"
                    break

            courses_summary.append(
                StudentCourseAttendanceSummary(
                    course_offering_id=offering.id,
                    subject_code=offering.subject.code,
                    subject_name=offering.subject.name,
                    credits=offering.subject.credits,
                    faculty_name=primary_fac_name,
                    total_conducted=total_conducted,
                    attended_sessions=attended,
                    present_count=p_cnt,
                    absent_count=a_cnt,
                    late_count=l_cnt,
                    excused_count=e_cnt,
                    leave_count=ol_cnt,
                    attendance_percentage=pct,
                    minimum_required_percentage=policy.minimum_percentage,
                    status=course_status,
                )
            )

            total_conducted_all += total_conducted
            total_attended_all += attended

        if total_conducted_all > 0:
            overall_pct = round((total_attended_all / Decimal(total_conducted_all)) * Decimal(100), 2)
        else:
            overall_pct = Decimal("100.00")

        if overall_pct < default_policy.critical_threshold_percentage:
            overall_status = "CRITICAL"
        elif overall_pct < default_policy.minimum_percentage:
            overall_status = "WARNING"
        else:
            overall_status = "NORMAL"

        # 3. Recent 10 attendance records
        recent_stmt = (
            select(AttendanceRecord)
            .join(AttendanceSession, AttendanceRecord.session_id == AttendanceSession.id)
            .options(
                selectinload(AttendanceRecord.session)
                .selectinload(AttendanceSession.course_offering)
                .selectinload(CourseOffering.subject)
            )
            .where(
                AttendanceRecord.student_id == student_id,
                AttendanceRecord.tenant_id == tenant_id,
            )
            .order_by(AttendanceSession.session_date.desc(), AttendanceSession.period_number.desc())
            .limit(10)
        )
        recent_res = await db.execute(recent_stmt)
        recent_records = recent_res.scalars().all()

        recent_responses = [
            AttendanceRecordResponse(
                id=r.id,
                session_id=r.session_id,
                student_id=r.student_id,
                student_name=f"{student.first_name} {student.last_name}",
                student_roll_number=student.roll_number,
                student_admission_number=student.admission_number,
                status=r.status,
                remarks=r.remarks,
                recorded_by_user_id=r.recorded_by_user_id,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in recent_records
        ]

        # 4. Fetch unresolved alerts
        alert_stmt = (
            select(AttendanceAlert)
            .options(
                selectinload(AttendanceAlert.course_offering).selectinload(CourseOffering.subject)
            )
            .where(
                AttendanceAlert.student_id == student_id,
                AttendanceAlert.tenant_id == tenant_id,
                AttendanceAlert.is_resolved.is_(False),
            )
            .order_by(AttendanceAlert.created_at.desc())
        )
        alert_res = await db.execute(alert_stmt)
        alerts = alert_res.scalars().all()
        alert_responses = []
        for a in alerts:
            c_name = a.course_offering.subject.name if a.course_offering and a.course_offering.subject else None
            alert_responses.append(
                AttendanceAlertResponse(
                    id=a.id,
                    student_id=a.student_id,
                    student_name=f"{student.first_name} {student.last_name}",
                    student_roll_number=student.roll_number,
                    course_offering_id=a.course_offering_id,
                    course_name=c_name,
                    alert_type=a.alert_type,
                    severity=a.severity,
                    attendance_percentage=a.attendance_percentage,
                    threshold_percentage=a.threshold_percentage,
                    message=a.message,
                    is_resolved=a.is_resolved,
                    resolved_at=a.resolved_at,
                    created_at=a.created_at,
                )
            )

        return StudentOverallAttendanceSummary(
            student_id=student.id,
            student_name=f"{student.first_name} {student.last_name}",
            admission_number=student.admission_number,
            roll_number=student.roll_number,
            program_name=student.program.name if student.program else None,
            section_name=student.current_section.name if student.current_section else None,
            total_conducted_sessions=total_conducted_all,
            total_attended_sessions=total_attended_all,
            overall_percentage=overall_pct,
            minimum_required_percentage=default_policy.minimum_percentage,
            status=overall_status,
            courses=courses_summary,
            recent_records=recent_responses,
            alerts=alert_responses,
        )

    @classmethod
    async def get_course_offering_summary(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        course_offering_id: UUID,
    ) -> CourseOfferingAttendanceSummary:
        # 1. Fetch course offering
        offering_stmt = (
            select(CourseOffering)
            .options(
                selectinload(CourseOffering.subject),
                selectinload(CourseOffering.section),
                selectinload(CourseOffering.faculty_assignments)
                .selectinload(CourseFacultyAssignment.faculty)
                .selectinload(FacultyProfile.user),
            )
            .where(
                CourseOffering.id == course_offering_id,
                CourseOffering.tenant_id == tenant_id,
            )
        )
        offering_res = await db.execute(offering_stmt)
        offering = offering_res.scalar_one_or_none()
        if not offering:
            raise NotFoundException("CourseOffering", course_offering_id)

        policy = await cls.resolve_effective_policy(
            db,
            tenant_id,
            course_offering_id=offering.id,
            semester_id=offering.semester_id,
        )

        # 2. Fetch conducted sessions
        sess_stmt = select(AttendanceSession).where(
            AttendanceSession.course_offering_id == course_offering_id,
            AttendanceSession.tenant_id == tenant_id,
            AttendanceSession.status.in_(["MARKED", "LOCKED"]),
        )
        sess_res = await db.execute(sess_stmt)
        conducted_sessions = sess_res.scalars().all()
        session_ids = [s.id for s in conducted_sessions]
        total_conducted = len(session_ids)

        # 3. Fetch all enrolled students
        enr_stmt = (
            select(CourseEnrollment)
            .options(
                selectinload(CourseEnrollment.student).selectinload(StudentProfile.user)
            )
            .where(
                CourseEnrollment.course_offering_id == course_offering_id,
                CourseEnrollment.status == "ENROLLED",
            )
            .order_by(CourseEnrollment.student_id)
        )
        enr_res = await db.execute(enr_stmt)
        enrollments = enr_res.scalars().all()

        # 4. Fetch all records for this course's conducted sessions
        if session_ids:
            rec_stmt = select(AttendanceRecord).where(
                AttendanceRecord.session_id.in_(session_ids),
                AttendanceRecord.tenant_id == tenant_id,
            )
            rec_res = await db.execute(rec_stmt)
            records = rec_res.scalars().all()
        else:
            records = []

        # Group records by student_id
        records_by_student: dict[UUID, list[AttendanceRecord]] = {}
        for r in records:
            records_by_student.setdefault(r.student_id, []).append(r)

        students_summary: list[CourseOfferingStudentAttendanceItem] = []
        students_below = 0
        total_pct_sum = Decimal("0.00")

        for enr in enrollments:
            stud = enr.student
            stud_recs = records_by_student.get(stud.id, [])

            p_cnt = sum(1 for r in stud_recs if r.status == "PRESENT")
            a_cnt = sum(1 for r in stud_recs if r.status == "ABSENT")
            l_cnt = sum(1 for r in stud_recs if r.status == "LATE")
            e_cnt = sum(1 for r in stud_recs if r.status == "EXCUSED")
            ol_cnt = sum(1 for r in stud_recs if r.status == "ON_LEAVE")

            eligible = total_conducted
            if policy.exclude_excused_from_total:
                eligible -= e_cnt

            attended = Decimal(p_cnt) + (Decimal(l_cnt) * policy.late_weight)
            if policy.excused_counts_as_present:
                attended += Decimal(e_cnt)
            if policy.on_leave_counts_as_present:
                attended += Decimal(ol_cnt)

            if eligible > 0:
                pct = round((attended / Decimal(eligible)) * Decimal(100), 2)
            else:
                pct = Decimal("100.00")

            total_pct_sum += pct

            if pct < policy.critical_threshold_percentage:
                s_status = "CRITICAL"
                students_below += 1
            elif pct < policy.minimum_percentage:
                s_status = "WARNING"
                students_below += 1
            else:
                s_status = "NORMAL"

            students_summary.append(
                CourseOfferingStudentAttendanceItem(
                    student_id=stud.id,
                    student_name=f"{stud.first_name} {stud.last_name}",
                    admission_number=stud.admission_number,
                    roll_number=stud.roll_number,
                    total_conducted=total_conducted,
                    attended_sessions=attended,
                    present_count=p_cnt,
                    absent_count=a_cnt,
                    late_count=l_cnt,
                    excused_count=e_cnt,
                    leave_count=ol_cnt,
                    attendance_percentage=pct,
                    status=s_status,
                )
            )

        students_summary.sort(key=lambda x: (x.roll_number or "", x.student_name))

        avg_pct = (
            round(total_pct_sum / Decimal(len(enrollments)), 2)
            if enrollments
            else Decimal("100.00")
        )

        primary_fac_name = None
        for fa in offering.faculty_assignments:
            if fa.is_active and fa.faculty and fa.faculty.user:
                primary_fac_name = f"{fa.faculty.user.first_name} {fa.faculty.user.last_name}"
                break

        return CourseOfferingAttendanceSummary(
            course_offering_id=offering.id,
            subject_code=offering.subject.code,
            subject_name=offering.subject.name,
            section_name=offering.section.name,
            faculty_name=primary_fac_name,
            total_sessions_conducted=total_conducted,
            total_enrolled_students=len(enrollments),
            average_attendance_percentage=avg_pct,
            students_below_minimum=students_below,
            minimum_percentage=policy.minimum_percentage,
            students=students_summary,
        )

    # -------------------------------------------------------------------------
    # 5. LOW ATTENDANCE DETECTION & ALERTS
    # -------------------------------------------------------------------------
    @classmethod
    async def evaluate_low_attendance_and_generate_alerts(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        course_offering_id: UUID | None = None,
    ) -> list[LowAttendanceStudentItem]:
        """Detect students falling below warning/critical thresholds and generate alerts."""
        offering_filters = [
            CourseOffering.tenant_id == tenant_id,
            CourseOffering.status == "ACTIVE",
        ]
        if course_offering_id:
            offering_filters.append(CourseOffering.id == course_offering_id)

        offerings_res = await db.execute(select(CourseOffering).where(and_(*offering_filters)))
        offerings = offerings_res.scalars().all()

        low_attendance_items: list[LowAttendanceStudentItem] = []

        for offering in offerings:
            summary = await cls.get_course_offering_summary(db, tenant_id, offering.id)

            # Avoid false positives if fewer than 3 classes conducted
            if summary.total_sessions_conducted < 3:
                continue

            policy = await cls.resolve_effective_policy(
                db, tenant_id, course_offering_id=offering.id
            )

            for stud_stat in summary.students:
                if stud_stat.attendance_percentage < policy.minimum_percentage:
                    severity = (
                        "CRITICAL"
                        if stud_stat.attendance_percentage < policy.critical_threshold_percentage
                        else "WARNING"
                    )
                    alert_type = (
                        "LOW_ATTENDANCE_CRITICAL"
                        if severity == "CRITICAL"
                        else "LOW_ATTENDANCE_WARNING"
                    )

                    # Look up active alert
                    alert_stmt = select(AttendanceAlert).where(
                        AttendanceAlert.tenant_id == tenant_id,
                        AttendanceAlert.student_id == stud_stat.student_id,
                        AttendanceAlert.course_offering_id == offering.id,
                        AttendanceAlert.is_resolved.is_(False),
                    )
                    alert_res = await db.execute(alert_stmt)
                    existing_alert = alert_res.scalar_one_or_none()

                    msg = (
                        f"Student attendance in {summary.subject_code} ({summary.subject_name}) is "
                        f"{stud_stat.attendance_percentage}% (Required: {policy.minimum_percentage}%)."
                    )

                    if existing_alert:
                        existing_alert.attendance_percentage = Decimal(str(stud_stat.attendance_percentage))
                        existing_alert.severity = severity
                        existing_alert.alert_type = alert_type
                        existing_alert.message = msg
                    else:
                        new_alert = AttendanceAlert(
                            tenant_id=tenant_id,
                            student_id=stud_stat.student_id,
                            course_offering_id=offering.id,
                            alert_type=alert_type,
                            severity=severity,
                            attendance_percentage=Decimal(str(stud_stat.attendance_percentage)),
                            threshold_percentage=policy.minimum_percentage,
                            message=msg,
                            is_resolved=False,
                        )
                        db.add(new_alert)

                    low_attendance_items.append(
                        LowAttendanceStudentItem(
                            student_id=stud_stat.student_id,
                            student_name=stud_stat.student_name,
                            admission_number=stud_stat.admission_number,
                            roll_number=stud_stat.roll_number,
                            program_name=None,
                            section_name=summary.section_name,
                            course_offering_id=offering.id,
                            course_code=summary.subject_code,
                            course_name=summary.subject_name,
                            total_conducted=stud_stat.total_conducted,
                            attended_sessions=stud_stat.attended_sessions,
                            attendance_percentage=stud_stat.attendance_percentage,
                            threshold_percentage=policy.minimum_percentage,
                            status=severity,
                        )
                    )
                else:
                    # If student recovered attendance, resolve existing alert
                    resolve_stmt = select(AttendanceAlert).where(
                        AttendanceAlert.tenant_id == tenant_id,
                        AttendanceAlert.student_id == stud_stat.student_id,
                        AttendanceAlert.course_offering_id == offering.id,
                        AttendanceAlert.is_resolved.is_(False),
                    )
                    resolve_res = await db.execute(resolve_stmt)
                    open_alert = resolve_res.scalar_one_or_none()
                    if open_alert:
                        open_alert.is_resolved = True
                        open_alert.resolved_at = datetime.now(UTC)

        await db.commit()
        return low_attendance_items

    # -------------------------------------------------------------------------
    # 6. STUDENT LEAVE MANAGEMENT WORKFLOW
    # -------------------------------------------------------------------------
    @classmethod
    async def create_leave_request(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        payload: StudentLeaveCreateRequest,
        user_id: UUID,
        ip_address: str = "127.0.0.1",
    ) -> StudentLeaveResponse:
        # 1. Validate student
        stud_stmt = (
            select(StudentProfile)
            .options(selectinload(StudentProfile.user))
            .where(
                StudentProfile.id == payload.student_id,
                StudentProfile.tenant_id == tenant_id,
            )
        )
        stud_res = await db.execute(stud_stmt)
        student = stud_res.scalar_one_or_none()
        if not student:
            raise NotFoundException("StudentProfile", payload.student_id)

        # 2. Date checks
        if payload.start_date > payload.end_date:
            raise ValidationException("Leave start date cannot be later than end date.")

        # 3. Overlap check: ensure no active PENDING or APPROVED leave request overlaps
        overlap_stmt = select(StudentLeaveRequest).where(
            StudentLeaveRequest.tenant_id == tenant_id,
            StudentLeaveRequest.student_id == payload.student_id,
            StudentLeaveRequest.status.in_(["PENDING", "APPROVED"]),
            StudentLeaveRequest.start_date <= payload.end_date,
            StudentLeaveRequest.end_date >= payload.start_date,
        )
        overlap_res = await db.execute(overlap_stmt)
        if overlap_res.scalar_one_or_none():
            raise ConflictException(
                "A pending or approved leave request already overlaps with the requested date range."
            )

        leave = StudentLeaveRequest(
            tenant_id=tenant_id,
            student_id=payload.student_id,
            leave_type=payload.leave_type,
            start_date=payload.start_date,
            end_date=payload.end_date,
            reason=payload.reason,
            proof_storage_key=payload.proof_storage_key,
            status="PENDING",
        )
        db.add(leave)
        await db.flush()

        audit = cls._create_audit(
            tenant_id=tenant_id,
            user_id=user_id,
            action="LEAVE_REQUESTED",
            entity_type="student_leave",
            entity_id=leave.id,
            details={
                "student_id": str(leave.student_id),
                "start": leave.start_date.isoformat(),
                "end": leave.end_date.isoformat(),
            },
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()
        await db.refresh(leave)

        days_cnt = (leave.end_date - leave.start_date).days + 1
        return StudentLeaveResponse(
            id=leave.id,
            tenant_id=leave.tenant_id,
            student_id=leave.student_id,
            student_name=f"{student.first_name} {student.last_name}",
            student_roll_number=student.roll_number,
            student_admission_number=student.admission_number,
            leave_type=leave.leave_type,
            start_date=leave.start_date,
            end_date=leave.end_date,
            days_count=days_cnt,
            reason=leave.reason,
            proof_storage_key=leave.proof_storage_key,
            status=leave.status,
            reviewed_by_user_id=None,
            reviewed_by_name=None,
            reviewed_at=None,
            review_notes=None,
            created_at=leave.created_at,
        )

    @classmethod
    async def review_leave_request(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        leave_id: UUID,
        action: str,  # "APPROVE" or "REJECT"
        payload: StudentLeaveReviewRequest,
        reviewer_user_id: UUID,
        ip_address: str = "127.0.0.1",
    ) -> StudentLeaveResponse:
        stmt = (
            select(StudentLeaveRequest)
            .options(
                selectinload(StudentLeaveRequest.student).selectinload(StudentProfile.user),
                selectinload(StudentLeaveRequest.reviewed_by),
            )
            .where(
                StudentLeaveRequest.id == leave_id,
                StudentLeaveRequest.tenant_id == tenant_id,
            )
        )
        res = await db.execute(stmt)
        leave = res.scalar_one_or_none()
        if not leave:
            raise NotFoundException("StudentLeaveRequest", leave_id)

        if leave.status != "PENDING":
            raise ValidationException(f"Leave request is already in status '{leave.status}'.")

        reviewer_stmt = select(User).where(User.id == reviewer_user_id)
        reviewer_res = await db.execute(reviewer_stmt)
        reviewer = reviewer_res.scalar_one_or_none()

        if action == "APPROVE":
            leave.status = "APPROVED"
            audit_action = "LEAVE_APPROVED"

            # Attendance Impact: update any ABSENT records during this period to ON_LEAVE
            impact_stmt = (
                select(AttendanceRecord)
                .join(AttendanceSession, AttendanceRecord.session_id == AttendanceSession.id)
                .where(
                    AttendanceRecord.tenant_id == tenant_id,
                    AttendanceRecord.student_id == leave.student_id,
                    AttendanceSession.session_date >= leave.start_date,
                    AttendanceSession.session_date <= leave.end_date,
                    AttendanceRecord.status == "ABSENT",
                )
            )
            impact_res = await db.execute(impact_stmt)
            absent_records = impact_res.scalars().all()
            for r in absent_records:
                r.status = "ON_LEAVE"
                r.remarks = f"Leave approved: {leave.reason[:30]}"
        elif action == "REJECT":
            leave.status = "REJECTED"
            audit_action = "LEAVE_REJECTED"
        else:
            raise ValidationException(f"Invalid review action '{action}'.")

        leave.reviewed_by_user_id = reviewer_user_id
        leave.reviewed_at = datetime.now(UTC)
        leave.review_notes = payload.review_notes

        audit = cls._create_audit(
            tenant_id=tenant_id,
            user_id=reviewer_user_id,
            action=audit_action,
            entity_type="student_leave",
            entity_id=leave.id,
            details={"action": action, "notes": payload.review_notes},
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()
        await db.refresh(leave)

        student = leave.student
        days_cnt = (leave.end_date - leave.start_date).days + 1
        reviewer_name = f"{reviewer.first_name} {reviewer.last_name}" if reviewer else None

        return StudentLeaveResponse(
            id=leave.id,
            tenant_id=leave.tenant_id,
            student_id=leave.student_id,
            student_name=f"{student.first_name} {student.last_name}" if student else None,
            student_roll_number=student.roll_number if student else None,
            student_admission_number=student.admission_number if student else None,
            leave_type=leave.leave_type,
            start_date=leave.start_date,
            end_date=leave.end_date,
            days_count=days_cnt,
            reason=leave.reason,
            proof_storage_key=leave.proof_storage_key,
            status=leave.status,
            reviewed_by_user_id=leave.reviewed_by_user_id,
            reviewed_by_name=reviewer_name,
            reviewed_at=leave.reviewed_at,
            review_notes=leave.review_notes,
            created_at=leave.created_at,
        )

    @classmethod
    async def list_leaves(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        student_id: UUID | None = None,
        status: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[StudentLeaveResponse], int]:
        filters = [StudentLeaveRequest.tenant_id == tenant_id]
        if student_id:
            filters.append(StudentLeaveRequest.student_id == student_id)
        if status:
            filters.append(StudentLeaveRequest.status == status)
        if start_date:
            filters.append(StudentLeaveRequest.start_date >= start_date)
        if end_date:
            filters.append(StudentLeaveRequest.end_date <= end_date)

        count_stmt = select(func.count(StudentLeaveRequest.id)).where(and_(*filters))
        count_res = await db.execute(count_stmt)
        total = count_res.scalar() or 0

        stmt = (
            select(StudentLeaveRequest)
            .options(
                selectinload(StudentLeaveRequest.student).selectinload(StudentProfile.user),
                selectinload(StudentLeaveRequest.reviewed_by),
            )
            .where(and_(*filters))
            .order_by(StudentLeaveRequest.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        res = await db.execute(stmt)
        leaves = res.scalars().all()

        responses = []
        for l in leaves:
            s_name = f"{l.student.first_name} {l.student.last_name}" if l.student else None
            r_name = f"{l.reviewed_by.first_name} {l.reviewed_by.last_name}" if l.reviewed_by else None
            days_cnt = (l.end_date - l.start_date).days + 1
            responses.append(
                StudentLeaveResponse(
                    id=l.id,
                    tenant_id=l.tenant_id,
                    student_id=l.student_id,
                    student_name=s_name,
                    student_roll_number=l.student.roll_number if l.student else None,
                    student_admission_number=l.student.admission_number if l.student else None,
                    leave_type=l.leave_type,
                    start_date=l.start_date,
                    end_date=l.end_date,
                    days_count=days_cnt,
                    reason=l.reason,
                    proof_storage_key=l.proof_storage_key,
                    status=l.status,
                    reviewed_by_user_id=l.reviewed_by_user_id,
                    reviewed_by_name=r_name,
                    reviewed_at=l.reviewed_at,
                    review_notes=l.review_notes,
                    created_at=l.created_at,
                )
            )

        return responses, total

    # -------------------------------------------------------------------------
    # 7. ATTENDANCE CORRECTION WORKFLOW (LOCKED REGISTER REVISION)
    # -------------------------------------------------------------------------
    @classmethod
    async def create_correction_request(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        payload: AttendanceCorrectionCreateRequest,
        requested_by_user_id: UUID,
        ip_address: str = "127.0.0.1",
    ) -> AttendanceCorrectionResponse:
        rec_stmt = (
            select(AttendanceRecord)
            .options(
                selectinload(AttendanceRecord.session)
                .selectinload(AttendanceSession.course_offering)
                .selectinload(CourseOffering.subject),
                selectinload(AttendanceRecord.student).selectinload(StudentProfile.user),
            )
            .where(
                AttendanceRecord.id == payload.attendance_record_id,
                AttendanceRecord.tenant_id == tenant_id,
            )
        )
        rec_res = await db.execute(rec_stmt)
        record = rec_res.scalar_one_or_none()
        if not record:
            raise NotFoundException("AttendanceRecord", payload.attendance_record_id)

        allowed_statuses = {"PRESENT", "ABSENT", "LATE", "EXCUSED", "ON_LEAVE"}
        if payload.requested_status not in allowed_statuses:
            raise ValidationException(f"Invalid requested status '{payload.requested_status}'.")

        if record.status == payload.requested_status:
            raise ValidationException("Requested status is identical to current attendance status.")

        # Check for duplicate pending correction on this record
        dup_stmt = select(AttendanceCorrectionRequest).where(
            AttendanceCorrectionRequest.attendance_record_id == record.id,
            AttendanceCorrectionRequest.approval_status == "PENDING",
        )
        dup_res = await db.execute(dup_stmt)
        if dup_res.scalar_one_or_none():
            raise ConflictException("A correction request for this attendance record is already pending.")

        correction = AttendanceCorrectionRequest(
            tenant_id=tenant_id,
            attendance_record_id=record.id,
            previous_status=record.status,
            requested_status=payload.requested_status,
            reason=payload.reason,
            requested_by_user_id=requested_by_user_id,
            approval_status="PENDING",
        )
        db.add(correction)
        await db.flush()

        audit = cls._create_audit(
            tenant_id=tenant_id,
            user_id=requested_by_user_id,
            action="ATTENDANCE_CORRECTION_REQUESTED",
            entity_type="attendance_correction",
            entity_id=correction.id,
            details={
                "record_id": str(record.id),
                "from": record.status,
                "to": payload.requested_status,
            },
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()
        await db.refresh(correction)

        user_stmt = select(User).where(User.id == requested_by_user_id)
        u_res = await db.execute(user_stmt)
        req_user = u_res.scalar_one_or_none()
        req_name = f"{req_user.first_name} {req_user.last_name}" if req_user else None

        course_code = (
            record.session.course_offering.subject.code
            if record.session.course_offering and record.session.course_offering.subject
            else None
        )
        course_name = (
            record.session.course_offering.subject.name
            if record.session.course_offering and record.session.course_offering.subject
            else None
        )

        return AttendanceCorrectionResponse(
            id=correction.id,
            tenant_id=correction.tenant_id,
            attendance_record_id=correction.attendance_record_id,
            session_id=record.session_id,
            session_date=record.session.session_date,
            course_code=course_code,
            course_name=course_name,
            student_id=record.student_id,
            student_name=f"{record.student.first_name} {record.student.last_name}" if record.student else None,
            student_roll_number=record.student.roll_number if record.student else None,
            previous_status=correction.previous_status,
            requested_status=correction.requested_status,
            reason=correction.reason,
            requested_by_user_id=correction.requested_by_user_id,
            requested_by_name=req_name,
            approved_by_user_id=None,
            approved_by_name=None,
            approval_status=correction.approval_status,
            approval_notes=None,
            reviewed_at=None,
            created_at=correction.created_at,
        )

    @classmethod
    async def review_correction_request(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        correction_id: UUID,
        action: str,  # "APPROVE" or "REJECT"
        payload: AttendanceCorrectionReviewRequest,
        reviewer_user_id: UUID,
        ip_address: str = "127.0.0.1",
    ) -> AttendanceCorrectionResponse:
        stmt = (
            select(AttendanceCorrectionRequest)
            .options(
                selectinload(AttendanceCorrectionRequest.record)
                .selectinload(AttendanceRecord.session)
                .selectinload(AttendanceSession.course_offering)
                .selectinload(CourseOffering.subject),
                selectinload(AttendanceCorrectionRequest.record)
                .selectinload(AttendanceRecord.student)
                .selectinload(StudentProfile.user),
                selectinload(AttendanceCorrectionRequest.requested_by),
                selectinload(AttendanceCorrectionRequest.approved_by),
            )
            .where(
                AttendanceCorrectionRequest.id == correction_id,
                AttendanceCorrectionRequest.tenant_id == tenant_id,
            )
        )
        res = await db.execute(stmt)
        corr = res.scalar_one_or_none()
        if not corr:
            raise NotFoundException("AttendanceCorrectionRequest", correction_id)

        if corr.approval_status != "PENDING":
            raise ValidationException(f"Correction request is already in status '{corr.approval_status}'.")

        reviewer_stmt = select(User).where(User.id == reviewer_user_id)
        rev_res = await db.execute(reviewer_stmt)
        reviewer = rev_res.scalar_one_or_none()

        if action == "APPROVE":
            corr.approval_status = "APPROVED"
            corr.record.status = corr.requested_status
            corr.record.remarks = (
                f"Corrected via approval: {corr.reason[:30]}"
            )
            audit_action = "ATTENDANCE_CORRECTION_APPROVED"
        elif action == "REJECT":
            corr.approval_status = "REJECTED"
            audit_action = "ATTENDANCE_CORRECTION_REJECTED"
        else:
            raise ValidationException(f"Invalid review action '{action}'.")

        corr.approved_by_user_id = reviewer_user_id
        corr.reviewed_at = datetime.now(UTC)
        corr.approval_notes = payload.approval_notes

        audit = cls._create_audit(
            tenant_id=tenant_id,
            user_id=reviewer_user_id,
            action=audit_action,
            entity_type="attendance_correction",
            entity_id=corr.id,
            details={
                "action": action,
                "previous_status": corr.previous_status,
                "new_status": corr.record.status,
            },
            ip_address=ip_address,
        )
        db.add(audit)
        await db.commit()
        await db.refresh(corr)

        record = corr.record
        req_user = corr.requested_by
        req_name = f"{req_user.first_name} {req_user.last_name}" if req_user else None
        rev_name = f"{reviewer.first_name} {reviewer.last_name}" if reviewer else None

        course_code = (
            record.session.course_offering.subject.code
            if record.session.course_offering and record.session.course_offering.subject
            else None
        )
        course_name = (
            record.session.course_offering.subject.name
            if record.session.course_offering and record.session.course_offering.subject
            else None
        )

        return AttendanceCorrectionResponse(
            id=corr.id,
            tenant_id=corr.tenant_id,
            attendance_record_id=corr.attendance_record_id,
            session_id=record.session_id,
            session_date=record.session.session_date,
            course_code=course_code,
            course_name=course_name,
            student_id=record.student_id,
            student_name=f"{record.student.first_name} {record.student.last_name}" if record.student else None,
            student_roll_number=record.student.roll_number if record.student else None,
            previous_status=corr.previous_status,
            requested_status=corr.requested_status,
            reason=corr.reason,
            requested_by_user_id=corr.requested_by_user_id,
            requested_by_name=req_name,
            approved_by_user_id=corr.approved_by_user_id,
            approved_by_name=rev_name,
            approval_status=corr.approval_status,
            approval_notes=corr.approval_notes,
            reviewed_at=corr.reviewed_at,
            created_at=corr.created_at,
        )

    @classmethod
    async def list_corrections(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        status: str | None = None,
        course_offering_id: UUID | None = None,
        student_id: UUID | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[AttendanceCorrectionResponse], int]:
        filters = [AttendanceCorrectionRequest.tenant_id == tenant_id]
        if status:
            filters.append(AttendanceCorrectionRequest.approval_status == status)

        stmt = (
            select(AttendanceCorrectionRequest)
            .join(AttendanceRecord, AttendanceCorrectionRequest.attendance_record_id == AttendanceRecord.id)
            .join(AttendanceSession, AttendanceRecord.session_id == AttendanceSession.id)
            .options(
                selectinload(AttendanceCorrectionRequest.record)
                .selectinload(AttendanceRecord.session)
                .selectinload(AttendanceSession.course_offering)
                .selectinload(CourseOffering.subject),
                selectinload(AttendanceCorrectionRequest.record)
                .selectinload(AttendanceRecord.student)
                .selectinload(StudentProfile.user),
                selectinload(AttendanceCorrectionRequest.requested_by),
                selectinload(AttendanceCorrectionRequest.approved_by),
            )
            .where(and_(*filters))
        )
        if course_offering_id:
            stmt = stmt.where(AttendanceSession.course_offering_id == course_offering_id)
        if student_id:
            stmt = stmt.where(AttendanceRecord.student_id == student_id)

        # Count
        count_stmt = select(func.count(AttendanceCorrectionRequest.id)).where(and_(*filters))
        count_res = await db.execute(count_stmt)
        total = count_res.scalar() or 0

        stmt = stmt.order_by(AttendanceCorrectionRequest.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        res = await db.execute(stmt)
        corrections = res.scalars().all()

        responses = []
        for c in corrections:
            rec = c.record
            req_u = c.requested_by
            app_u = c.approved_by
            req_name = f"{req_u.first_name} {req_u.last_name}" if req_u else None
            app_name = f"{app_u.first_name} {app_u.last_name}" if app_u else None
            course_code = (
                rec.session.course_offering.subject.code
                if rec and rec.session and rec.session.course_offering and rec.session.course_offering.subject
                else None
            )
            course_name = (
                rec.session.course_offering.subject.name
                if rec and rec.session and rec.session.course_offering and rec.session.course_offering.subject
                else None
            )

            responses.append(
                AttendanceCorrectionResponse(
                    id=c.id,
                    tenant_id=c.tenant_id,
                    attendance_record_id=c.attendance_record_id,
                    session_id=rec.session_id,
                    session_date=rec.session.session_date,
                    course_code=course_code,
                    course_name=course_name,
                    student_id=rec.student_id,
                    student_name=f"{rec.student.first_name} {rec.student.last_name}" if rec.student else None,
                    student_roll_number=rec.student.roll_number if rec.student else None,
                    previous_status=c.previous_status,
                    requested_status=c.requested_status,
                    reason=c.reason,
                    requested_by_user_id=c.requested_by_user_id,
                    requested_by_name=req_name,
                    approved_by_user_id=c.approved_by_user_id,
                    approved_by_name=app_name,
                    approval_status=c.approval_status,
                    approval_notes=c.approval_notes,
                    reviewed_at=c.reviewed_at,
                    created_at=c.created_at,
                )
            )

        return responses, total

    # -------------------------------------------------------------------------
    # 8. ATTENDANCE DASHBOARD
    # -------------------------------------------------------------------------
    @classmethod
    async def get_dashboard_metrics(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        today_date: date | None = None,
        faculty_id: UUID | None = None,
    ) -> AttendanceDashboardResponse:
        current_date = today_date or date.today()

        # Today's sessions
        sess_filters = [
            AttendanceSession.tenant_id == tenant_id,
            AttendanceSession.session_date == current_date,
        ]
        if faculty_id:
            sess_filters.append(AttendanceSession.faculty_id == faculty_id)

        t_stmt = select(AttendanceSession).where(and_(*sess_filters))
        t_res = await db.execute(t_stmt)
        today_sessions = t_res.scalars().all()

        total_today = len(today_sessions)
        marked_today = sum(1 for s in today_sessions if s.status in ("MARKED", "LOCKED"))
        pending_today = total_today - marked_today

        # Pending leave requests
        leave_stmt = select(func.count(StudentLeaveRequest.id)).where(
            StudentLeaveRequest.tenant_id == tenant_id,
            StudentLeaveRequest.status == "PENDING",
        )
        leave_res = await db.execute(leave_stmt)
        pending_leaves = leave_res.scalar() or 0

        # Pending corrections
        corr_stmt = select(func.count(AttendanceCorrectionRequest.id)).where(
            AttendanceCorrectionRequest.tenant_id == tenant_id,
            AttendanceCorrectionRequest.approval_status == "PENDING",
        )
        corr_res = await db.execute(corr_stmt)
        pending_corrs = corr_res.scalar() or 0

        # Unresolved low attendance alerts
        alert_stmt = select(func.count(AttendanceAlert.id)).where(
            AttendanceAlert.tenant_id == tenant_id,
            AttendanceAlert.is_resolved.is_(False),
        )
        alert_res = await db.execute(alert_stmt)
        low_att_count = alert_res.scalar() or 0

        # Recent 5 sessions
        recent_sessions, _ = await cls.list_sessions(
            db, tenant_id, faculty_id=faculty_id, page=1, page_size=5
        )

        # Average attendance % calculation across all records marked in tenant
        pct_stmt = select(
            func.count(AttendanceRecord.id),
            func.sum(
                case(
                    (AttendanceRecord.status == "PRESENT", 1),
                    (AttendanceRecord.status == "EXCUSED", 1),
                    else_=0,
                )
            ),
        ).where(AttendanceRecord.tenant_id == tenant_id)
        pct_res = await db.execute(pct_stmt)
        row = pct_res.first()
        total_recs = row[0] if row else 0
        present_recs = row[1] if row and row[1] else 0

        if total_recs > 0:
            avg_pct = round((Decimal(present_recs) / Decimal(total_recs)) * Decimal(100), 2)
        else:
            avg_pct = Decimal("100.00")

        return AttendanceDashboardResponse(
            today_sessions_count=total_today,
            today_sessions_marked=marked_today,
            today_sessions_pending=pending_today,
            total_students_low_attendance=low_att_count,
            average_attendance_percentage=avg_pct,
            pending_leave_requests_count=pending_leaves,
            pending_corrections_count=pending_corrs,
            recent_sessions=recent_sessions,
        )
