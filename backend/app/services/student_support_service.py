"""Service Layer for Enterprise Student Counselling, Mentoring & Personal Development (Step 59).

Product Principle: "One Campus. One System. One Source of Truth."

Implements transactional business logic, strict confidentiality enforcement,
mentor workload quotas, conflict prevention, IDP progress calculations,
audit logging, and domain event dispatch.
"""

import logging
from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    ConflictException,
    NotFoundException,
    ValidationException,
)
from app.models.people import StudentProfile, User
from app.models.student_support import (
    ActionItemStatus,
    AppointmentStatus,
    ConfidentialCounsellingRecord,
    CounsellingAppointment,
    DevelopmentActionItem,
    DevelopmentGoal,
    FollowUpStatus,
    GoalStatus,
    MentorAssignment,
    MentorAssignmentStatus,
    MentorAssignmentType,
    MentoringSession,
    MentoringSessionAttendee,
    PlanStatus,
    ReferralStatus,
    SessionAttendanceStatus,
    SessionStatus,
    StudentDevelopmentPlan,
    SupportAuditAction,
    SupportAuditLog,
    SupportFollowUp,
    SupportPolicyConfig,
    SupportReferral,
)
from app.schemas.student_support import (
    ConfidentialCounsellingRecordCreate,
    ConfidentialCounsellingRecordResponse,
    CounsellingAppointmentCreate,
    CounsellingAppointmentResponse,
    CounsellingAppointmentUpdate,
    DevelopmentActionItemResponse,
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

logger = logging.getLogger("campusos.student_support")


class StudentSupportService:
    def __init__(self, db: AsyncSession, tenant_id: UUID) -> None:
        self.db = db
        self.tenant_id = tenant_id

    def _safe_dt(self, obj: Any, attr: str, fallback: datetime | None = None) -> datetime:
        try:
            val = getattr(obj, attr, None)
            if isinstance(val, datetime):
                return val
        except Exception:
            pass
        return fallback or datetime.now(UTC)

    # =========================================================================
    # POLICY CONFIG
    # =========================================================================

    async def get_or_create_config(self) -> SupportPolicyConfig:
        stmt = select(SupportPolicyConfig).where(SupportPolicyConfig.tenant_id == self.tenant_id)
        res = await self.db.execute(stmt)
        config = res.scalar_one_or_none()
        if not config:
            now = datetime.now(UTC)
            config = SupportPolicyConfig(
                tenant_id=self.tenant_id,
                created_at=now,
                updated_at=now,
            )
            self.db.add(config)
            await self.db.flush()
        return config

    async def update_config(self, data: SupportPolicyConfigUpdate) -> SupportPolicyConfigResponse:
        config = await self.get_or_create_config()
        if data.max_mentees_per_mentor is not None:
            config.max_mentees_per_mentor = data.max_mentees_per_mentor
        if data.allow_cross_department_mentors is not None:
            config.allow_cross_department_mentors = data.allow_cross_department_mentors
        if data.appointment_advance_booking_days is not None:
            config.appointment_advance_booking_days = data.appointment_advance_booking_days
        if data.appointment_cancellation_lead_hours is not None:
            config.appointment_cancellation_lead_hours = data.appointment_cancellation_lead_hours
        if data.default_session_duration_minutes is not None:
            config.default_session_duration_minutes = data.default_session_duration_minutes
        if data.enable_confidential_counselling is not None:
            config.enable_confidential_counselling = data.enable_confidential_counselling
        if data.require_student_consent_for_referral is not None:
            config.require_student_consent_for_referral = data.require_student_consent_for_referral
        config.updated_at = datetime.now(UTC)
        await self.db.flush()
        return SupportPolicyConfigResponse(
            id=config.id,
            tenant_id=config.tenant_id,
            max_mentees_per_mentor=config.max_mentees_per_mentor,
            allow_cross_department_mentors=config.allow_cross_department_mentors,
            appointment_advance_booking_days=config.appointment_advance_booking_days,
            appointment_cancellation_lead_hours=config.appointment_cancellation_lead_hours,
            default_session_duration_minutes=config.default_session_duration_minutes,
            enable_confidential_counselling=config.enable_confidential_counselling,
            require_student_consent_for_referral=config.require_student_consent_for_referral,
            created_at=getattr(config, "created_at", None) or datetime.now(UTC),
            updated_at=config.updated_at,
        )

    # =========================================================================
    # MENTOR ASSIGNMENT WORKFLOWS
    # =========================================================================

    async def create_mentor_assignment(self, data: MentorAssignmentCreate) -> MentorAssignmentResponse:
        # 1. Verify student exists
        student = await self.db.get(StudentProfile, data.student_id)
        if not student or student.tenant_id != self.tenant_id:
            raise NotFoundException("Student record not found in this institution")

        # 2. Verify mentor user exists
        mentor = await self.db.get(User, data.mentor_user_id)
        if not mentor:
            raise NotFoundException("Mentor faculty user not found")

        # 3. Prevent duplicate active assignment for student
        active_stmt = select(MentorAssignment).where(
            and_(
                MentorAssignment.tenant_id == self.tenant_id,
                MentorAssignment.student_id == data.student_id,
                MentorAssignment.status == MentorAssignmentStatus.ACTIVE.value,
            )
        )
        existing_active = (await self.db.execute(active_stmt)).scalar_one_or_none()
        if existing_active:
            raise ConflictException("Student already has an active faculty mentor assignment")

        # 4. Check mentor workload limit
        config = await self.get_or_create_config()
        workload_stmt = select(func.count(MentorAssignment.id)).where(
            and_(
                MentorAssignment.tenant_id == self.tenant_id,
                MentorAssignment.mentor_user_id == data.mentor_user_id,
                MentorAssignment.status == MentorAssignmentStatus.ACTIVE.value,
            )
        )
        current_workload = (await self.db.execute(workload_stmt)).scalar_one() or 0
        if current_workload >= config.max_mentees_per_mentor:
            raise ValidationException(
                f"Mentor has reached the maximum mentee workload limit ({config.max_mentees_per_mentor})"
            )

        # 5. Create assignment
        now = datetime.now(UTC)
        assignment = MentorAssignment(
            tenant_id=self.tenant_id,
            student_id=data.student_id,
            mentor_user_id=data.mentor_user_id,
            department_id=data.department_id,
            program_id=data.program_id,
            academic_year=data.academic_year,
            assignment_type=data.assignment_type.value,
            status=MentorAssignmentStatus.ACTIVE.value,
            assigned_date=data.assigned_date,
            notes=data.notes,
            created_at=now,
            updated_at=now,
        )
        self.db.add(assignment)
        await self.db.flush()

        # Build response with names
        student_user = await self.db.get(User, student.user_id)
        return MentorAssignmentResponse(
            id=assignment.id,
            tenant_id=assignment.tenant_id,
            student_id=assignment.student_id,
            mentor_user_id=assignment.mentor_user_id,
            department_id=assignment.department_id,
            program_id=assignment.program_id,
            academic_year=assignment.academic_year,
            assignment_type=assignment.assignment_type,
            status=assignment.status,
            assigned_date=assignment.assigned_date,
            end_date=assignment.end_date,
            notes=assignment.notes,
            reassigned_from_id=assignment.reassigned_from_id,
            reassignment_reason=assignment.reassignment_reason,
            student_name=f"{student_user.first_name} {student_user.last_name}" if student_user else None,
            student_roll=student.roll_number or student.admission_number,
            mentor_name=f"{mentor.first_name} {mentor.last_name}",
            mentor_email=mentor.email,
            created_at=self._safe_dt(assignment, "created_at", now),
            updated_at=self._safe_dt(assignment, "updated_at", now),
        )

    async def reassign_mentor(self, assignment_id: UUID, req: MentorReassignRequest) -> MentorAssignmentResponse:
        old_assignment = await self.db.get(MentorAssignment, assignment_id)
        if not old_assignment or old_assignment.tenant_id != self.tenant_id:
            raise NotFoundException("Mentor assignment not found")

        if old_assignment.status != MentorAssignmentStatus.ACTIVE.value:
            raise ValidationException("Cannot reassign an inactive or completed mentoring assignment")

        # Verify new mentor
        new_mentor = await self.db.get(User, req.new_mentor_user_id)
        if not new_mentor:
            raise NotFoundException("New mentor faculty user not found")

        now = datetime.now(UTC)
        # Mark old assignment as REASSIGNED
        old_assignment.status = MentorAssignmentStatus.REASSIGNED.value
        old_assignment.end_date = req.effective_date
        old_assignment.updated_at = now

        # Check workload on new mentor
        config = await self.get_or_create_config()
        workload_stmt = select(func.count(MentorAssignment.id)).where(
            and_(
                MentorAssignment.tenant_id == self.tenant_id,
                MentorAssignment.mentor_user_id == req.new_mentor_user_id,
                MentorAssignment.status == MentorAssignmentStatus.ACTIVE.value,
            )
        )
        current_workload = (await self.db.execute(workload_stmt)).scalar_one() or 0
        if current_workload >= config.max_mentees_per_mentor:
            raise ValidationException(
                f"New mentor has reached the maximum mentee workload limit ({config.max_mentees_per_mentor})"
            )

        # Create new assignment
        new_assignment = MentorAssignment(
            tenant_id=self.tenant_id,
            student_id=old_assignment.student_id,
            mentor_user_id=req.new_mentor_user_id,
            department_id=old_assignment.department_id,
            program_id=old_assignment.program_id,
            academic_year=old_assignment.academic_year,
            assignment_type=MentorAssignmentType.REASSIGNED.value,
            status=MentorAssignmentStatus.ACTIVE.value,
            assigned_date=req.effective_date,
            reassigned_from_id=old_assignment.id,
            reassignment_reason=req.reason,
            notes=f"Reassigned from previous mentor. Reason: {req.reason}",
            created_at=now,
            updated_at=now,
        )
        self.db.add(new_assignment)
        await self.db.flush()

        student = await self.db.get(StudentProfile, new_assignment.student_id)
        student_user = await self.db.get(User, student.user_id) if student else None

        return MentorAssignmentResponse(
            id=new_assignment.id,
            tenant_id=new_assignment.tenant_id,
            student_id=new_assignment.student_id,
            mentor_user_id=new_assignment.mentor_user_id,
            department_id=new_assignment.department_id,
            program_id=new_assignment.program_id,
            academic_year=new_assignment.academic_year,
            assignment_type=new_assignment.assignment_type,
            status=new_assignment.status,
            assigned_date=new_assignment.assigned_date,
            end_date=new_assignment.end_date,
            notes=new_assignment.notes,
            reassigned_from_id=new_assignment.reassigned_from_id,
            reassignment_reason=new_assignment.reassignment_reason,
            student_name=f"{student_user.first_name} {student_user.last_name}" if student_user else None,
            student_roll=student.roll_number if student else None,
            mentor_name=f"{new_mentor.first_name} {new_mentor.last_name}",
            mentor_email=new_mentor.email,
            created_at=self._safe_dt(new_assignment, "created_at", now),
            updated_at=self._safe_dt(new_assignment, "updated_at", now),
        )

    async def list_mentor_assignments(
        self,
        mentor_user_id: UUID | None = None,
        student_id: UUID | None = None,
        status: str | None = None,
        department_id: UUID | None = None,
    ) -> list[MentorAssignmentResponse]:
        stmt = (
            select(MentorAssignment, StudentProfile, User)
            .join(StudentProfile, MentorAssignment.student_id == StudentProfile.id)
            .join(User, MentorAssignment.mentor_user_id == User.id)
            .where(MentorAssignment.tenant_id == self.tenant_id)
        )
        if mentor_user_id:
            stmt = stmt.where(MentorAssignment.mentor_user_id == mentor_user_id)
        if student_id:
            stmt = stmt.where(MentorAssignment.student_id == student_id)
        if status:
            stmt = stmt.where(MentorAssignment.status == status)
        if department_id:
            stmt = stmt.where(MentorAssignment.department_id == department_id)

        stmt = stmt.order_by(MentorAssignment.assigned_date.desc())
        results = (await self.db.execute(stmt)).all()

        responses: list[MentorAssignmentResponse] = []
        for assignment, student, mentor in results:
            student_user = await self.db.get(User, student.user_id) if student else None
            responses.append(
                MentorAssignmentResponse(
                    id=assignment.id,
                    tenant_id=assignment.tenant_id,
                    student_id=assignment.student_id,
                    mentor_user_id=assignment.mentor_user_id,
                    department_id=assignment.department_id,
                    program_id=assignment.program_id,
                    academic_year=assignment.academic_year,
                    assignment_type=assignment.assignment_type,
                    status=assignment.status,
                    assigned_date=assignment.assigned_date,
                    end_date=assignment.end_date,
                    notes=assignment.notes,
                    reassigned_from_id=assignment.reassigned_from_id,
                    reassignment_reason=assignment.reassignment_reason,
                    student_name=f"{student_user.first_name} {student_user.last_name}" if student_user else None,
                    student_roll=student.roll_number or student.admission_number if student else None,
                    mentor_name=f"{mentor.first_name} {mentor.last_name}" if mentor else None,
                    mentor_email=mentor.email if mentor else None,
                    created_at=self._safe_dt(assignment, "created_at"),
                    updated_at=self._safe_dt(assignment, "updated_at"),
                )
            )
        return responses

    async def get_student_assigned_mentor(self, student_id: UUID) -> MentorAssignmentResponse | None:
        assignments = await self.list_mentor_assignments(
            student_id=student_id, status=MentorAssignmentStatus.ACTIVE.value
        )
        return assignments[0] if assignments else None

    # =========================================================================
    # MENTORING SESSIONS & ATTENDANCE
    # =========================================================================

    async def schedule_mentoring_session(
        self, data: MentoringSessionCreate, creator_user_id: UUID
    ) -> MentoringSessionResponse:
        now = datetime.now(UTC)
        session = MentoringSession(
            tenant_id=self.tenant_id,
            assignment_id=data.assignment_id,
            mentor_user_id=data.mentor_user_id,
            session_title=data.session_title,
            session_type=data.session_type.value,
            session_date=data.session_date,
            start_time=data.start_time,
            end_time=data.end_time,
            location_or_link=data.location_or_link,
            status=SessionStatus.SCHEDULED.value,
            summary=data.summary,
            action_items=data.action_items,
            follow_up_date=data.follow_up_date,
            created_by_user_id=creator_user_id,
            created_at=now,
            updated_at=now,
        )
        self.db.add(session)
        await self.db.flush()

        # Add attendees
        attendee_responses: list[SessionAttendeeResponse] = []
        for sid in data.attendee_student_ids:
            attendee = MentoringSessionAttendee(
                tenant_id=self.tenant_id,
                session_id=session.id,
                student_id=sid,
                attendance_status=SessionAttendanceStatus.PENDING.value,
                created_at=now,
                updated_at=now,
            )
            self.db.add(attendee)
            await self.db.flush()
            student = await self.db.get(StudentProfile, sid)
            s_user = await self.db.get(User, student.user_id) if student else None
            attendee_responses.append(
                SessionAttendeeResponse(
                    id=attendee.id,
                    session_id=session.id,
                    student_id=sid,
                    student_name=f"{s_user.first_name} {s_user.last_name}" if s_user else None,
                    attendance_status=attendee.attendance_status,
                )
            )

        mentor = await self.db.get(User, session.mentor_user_id)
        return MentoringSessionResponse(
            id=session.id,
            tenant_id=session.tenant_id,
            assignment_id=session.assignment_id,
            mentor_user_id=session.mentor_user_id,
            mentor_name=f"{mentor.first_name} {mentor.last_name}" if mentor else None,
            session_title=session.session_title,
            session_type=session.session_type,
            session_date=session.session_date,
            start_time=session.start_time,
            end_time=session.end_time,
            location_or_link=session.location_or_link,
            status=session.status,
            summary=session.summary,
            action_items=session.action_items,
            follow_up_date=session.follow_up_date,
            created_by_user_id=session.created_by_user_id,
            attendees=attendee_responses,
            created_at=self._safe_dt(session, "created_at", now),
            updated_at=self._safe_dt(session, "updated_at", now),
        )

    async def list_mentoring_sessions(
        self,
        mentor_user_id: UUID | None = None,
        student_id: UUID | None = None,
        status: str | None = None,
    ) -> list[MentoringSessionResponse]:
        stmt = (
            select(MentoringSession)
            .options(selectinload(MentoringSession.attendees))
            .where(MentoringSession.tenant_id == self.tenant_id)
        )
        if mentor_user_id:
            stmt = stmt.where(MentoringSession.mentor_user_id == mentor_user_id)
        if status:
            stmt = stmt.where(MentoringSession.status == status)
        if student_id:
            stmt = stmt.join(MentoringSessionAttendee, MentoringSession.id == MentoringSessionAttendee.session_id).where(
                MentoringSessionAttendee.student_id == student_id
            )

        stmt = stmt.order_by(MentoringSession.session_date.desc(), MentoringSession.start_time.desc())
        sessions = (await self.db.execute(stmt)).scalars().all()

        responses: list[MentoringSessionResponse] = []
        for s in sessions:
            mentor = await self.db.get(User, s.mentor_user_id)
            att_res: list[SessionAttendeeResponse] = []
            for a in s.attendees:
                st = await self.db.get(StudentProfile, a.student_id)
                su = await self.db.get(User, st.user_id) if st else None
                att_res.append(
                    SessionAttendeeResponse(
                        id=a.id,
                        session_id=a.session_id,
                        student_id=a.student_id,
                        student_name=f"{su.first_name} {su.last_name}" if su else None,
                        attendance_status=a.attendance_status,
                        student_feedback=a.student_feedback,
                        student_reflection=a.student_reflection,
                    )
                )
            responses.append(
                MentoringSessionResponse(
                    id=s.id,
                    tenant_id=s.tenant_id,
                    assignment_id=s.assignment_id,
                    mentor_user_id=s.mentor_user_id,
                    mentor_name=f"{mentor.first_name} {mentor.last_name}" if mentor else None,
                    session_title=s.session_title,
                    session_type=s.session_type,
                    session_date=s.session_date,
                    start_time=s.start_time,
                    end_time=s.end_time,
                    location_or_link=s.location_or_link,
                    status=s.status,
                    summary=s.summary,
                    action_items=s.action_items,
                    follow_up_date=s.follow_up_date,
                    created_by_user_id=s.created_by_user_id,
                    attendees=att_res,
                    created_at=self._safe_dt(s, "created_at"),
                    updated_at=self._safe_dt(s, "updated_at"),
                )
            )
        return responses

    async def update_mentoring_session(
        self, session_id: UUID, data: MentoringSessionUpdate
    ) -> MentoringSessionResponse:
        session = await self.db.get(MentoringSession, session_id)
        if not session or session.tenant_id != self.tenant_id:
            raise NotFoundException("Mentoring session not found")

        if data.session_title is not None:
            session.session_title = data.session_title
        if data.session_date is not None:
            session.session_date = data.session_date
        if data.start_time is not None:
            session.start_time = data.start_time
        if data.end_time is not None:
            session.end_time = data.end_time
        if data.location_or_link is not None:
            session.location_or_link = data.location_or_link
        if data.status is not None:
            session.status = data.status.value
        if data.summary is not None:
            session.summary = data.summary
        if data.action_items is not None:
            session.action_items = data.action_items
        if data.follow_up_date is not None:
            session.follow_up_date = data.follow_up_date

        session.updated_at = datetime.now(UTC)
        await self.db.flush()
        sessions = await self.list_mentoring_sessions()
        matched = [s for s in sessions if s.id == session_id]
        return matched[0]

    async def record_attendee_reflection(
        self, session_id: UUID, student_id: UUID, data: SessionAttendeeReflectionUpdate
    ) -> SessionAttendeeResponse:
        stmt = select(MentoringSessionAttendee).where(
            and_(
                MentoringSessionAttendee.tenant_id == self.tenant_id,
                MentoringSessionAttendee.session_id == session_id,
                MentoringSessionAttendee.student_id == student_id,
            )
        )
        attendee = (await self.db.execute(stmt)).scalar_one_or_none()
        if not attendee:
            raise NotFoundException("Session attendee record not found")

        if data.attendance_status is not None:
            attendee.attendance_status = data.attendance_status.value
        if data.student_feedback is not None:
            attendee.student_feedback = data.student_feedback
        if data.student_reflection is not None:
            attendee.student_reflection = data.student_reflection

        await self.db.flush()
        student = await self.db.get(StudentProfile, student_id)
        su = await self.db.get(User, student.user_id) if student else None
        return SessionAttendeeResponse(
            id=attendee.id,
            session_id=session_id,
            student_id=student_id,
            student_name=f"{su.first_name} {su.last_name}" if su else None,
            attendance_status=attendee.attendance_status,
            student_feedback=attendee.student_feedback,
            student_reflection=attendee.student_reflection,
        )

    # =========================================================================
    # COUNSELLING APPOINTMENT WORKFLOWS
    # =========================================================================

    async def request_counselling_appointment(
        self, data: CounsellingAppointmentCreate, booked_by_user_id: UUID
    ) -> CounsellingAppointmentResponse:
        # 1. Verify student exists
        student = await self.db.get(StudentProfile, data.student_id)
        if not student or student.tenant_id != self.tenant_id:
            raise NotFoundException("Student not found")

        # 2. Prevent overlapping appointments for same counsellor if assigned
        if data.counsellor_user_id:
            conflict_stmt = select(CounsellingAppointment).where(
                and_(
                    CounsellingAppointment.tenant_id == self.tenant_id,
                    CounsellingAppointment.counsellor_user_id == data.counsellor_user_id,
                    CounsellingAppointment.appointment_date == data.appointment_date,
                    CounsellingAppointment.status.in_([
                        AppointmentStatus.REQUESTED.value,
                        AppointmentStatus.CONFIRMED.value,
                        AppointmentStatus.CHECKED_IN.value,
                    ]),
                    or_(
                        and_(
                            CounsellingAppointment.start_time <= data.start_time,
                            CounsellingAppointment.end_time > data.start_time,
                        ),
                        and_(
                            CounsellingAppointment.start_time < data.end_time,
                            CounsellingAppointment.end_time >= data.end_time,
                        ),
                    ),
                )
            )
            conflict = (await self.db.execute(conflict_stmt)).scalar_one_or_none()
            if conflict:
                raise ConflictException("Counsellor has a conflicting appointment at this time")

        # 3. Create appointment
        now = datetime.now(UTC)
        appointment = CounsellingAppointment(
            tenant_id=self.tenant_id,
            student_id=data.student_id,
            counsellor_user_id=data.counsellor_user_id,
            category=data.category.value,
            appointment_date=data.appointment_date,
            start_time=data.start_time,
            end_time=data.end_time,
            duration_minutes=data.duration_minutes,
            mode=data.mode.value,
            venue_or_link=data.venue_or_link,
            status=AppointmentStatus.REQUESTED.value,
            request_reason=data.request_reason,
            booked_by_user_id=booked_by_user_id,
            is_confidential=True,
            created_at=now,
            updated_at=now,
        )
        self.db.add(appointment)
        await self.db.flush()

        su = await self.db.get(User, student.user_id) if student else None
        cu = await self.db.get(User, data.counsellor_user_id) if data.counsellor_user_id else None

        return CounsellingAppointmentResponse(
            id=appointment.id,
            tenant_id=appointment.tenant_id,
            student_id=appointment.student_id,
            student_name=f"{su.first_name} {su.last_name}" if su else None,
            counsellor_user_id=appointment.counsellor_user_id,
            counsellor_name=f"{cu.first_name} {cu.last_name}" if cu else None,
            category=appointment.category,
            appointment_date=appointment.appointment_date,
            start_time=appointment.start_time,
            end_time=appointment.end_time,
            duration_minutes=appointment.duration_minutes,
            mode=appointment.mode,
            venue_or_link=appointment.venue_or_link,
            status=appointment.status,
            request_reason=appointment.request_reason,
            booked_by_user_id=appointment.booked_by_user_id,
            is_confidential=appointment.is_confidential,
            has_confidential_notes=False,
            created_at=self._safe_dt(appointment, "created_at", now),
            updated_at=self._safe_dt(appointment, "updated_at", now),
        )

    async def list_counselling_appointments(
        self,
        student_id: UUID | None = None,
        counsellor_user_id: UUID | None = None,
        status: str | None = None,
    ) -> list[CounsellingAppointmentResponse]:
        stmt = (
            select(CounsellingAppointment)
            .options(selectinload(CounsellingAppointment.confidential_record))
            .where(CounsellingAppointment.tenant_id == self.tenant_id)
        )
        if student_id:
            stmt = stmt.where(CounsellingAppointment.student_id == student_id)
        if counsellor_user_id:
            stmt = stmt.where(CounsellingAppointment.counsellor_user_id == counsellor_user_id)
        if status:
            stmt = stmt.where(CounsellingAppointment.status == status)

        stmt = stmt.order_by(CounsellingAppointment.appointment_date.desc(), CounsellingAppointment.start_time.desc())
        appointments = (await self.db.execute(stmt)).scalars().all()

        responses: list[CounsellingAppointmentResponse] = []
        for appt in appointments:
            st = await self.db.get(StudentProfile, appt.student_id)
            su = await self.db.get(User, st.user_id) if st else None
            cu = await self.db.get(User, appt.counsellor_user_id) if appt.counsellor_user_id else None
            responses.append(
                CounsellingAppointmentResponse(
                    id=appt.id,
                    tenant_id=appt.tenant_id,
                    student_id=appt.student_id,
                    student_name=f"{su.first_name} {su.last_name}" if su else None,
                    counsellor_user_id=appt.counsellor_user_id,
                    counsellor_name=f"{cu.first_name} {cu.last_name}" if cu else None,
                    category=appt.category,
                    appointment_date=appt.appointment_date,
                    start_time=appt.start_time,
                    end_time=appt.end_time,
                    duration_minutes=appt.duration_minutes,
                    mode=appt.mode,
                    venue_or_link=appt.venue_or_link,
                    status=appt.status,
                    request_reason=appt.request_reason,
                    booked_by_user_id=appt.booked_by_user_id,
                    cancellation_reason=appt.cancellation_reason,
                    is_confidential=appt.is_confidential,
                    has_confidential_notes=appt.confidential_record is not None,
                    created_at=self._safe_dt(appt, "created_at"),
                    updated_at=self._safe_dt(appt, "updated_at"),
                )
            )
        return responses

    async def update_counselling_appointment(
        self, appointment_id: UUID, data: CounsellingAppointmentUpdate
    ) -> CounsellingAppointmentResponse:
        appt = await self.db.get(CounsellingAppointment, appointment_id)
        if not appt or appt.tenant_id != self.tenant_id:
            raise NotFoundException("Counselling appointment not found")

        if data.counsellor_user_id is not None:
            appt.counsellor_user_id = data.counsellor_user_id
        if data.category is not None:
            appt.category = data.category.value
        if data.appointment_date is not None:
            appt.appointment_date = data.appointment_date
        if data.start_time is not None:
            appt.start_time = data.start_time
        if data.end_time is not None:
            appt.end_time = data.end_time
        if data.duration_minutes is not None:
            appt.duration_minutes = data.duration_minutes
        if data.mode is not None:
            appt.mode = data.mode.value
        if data.venue_or_link is not None:
            appt.venue_or_link = data.venue_or_link
        if data.status is not None:
            appt.status = data.status.value
        if data.cancellation_reason is not None:
            appt.cancellation_reason = data.cancellation_reason

        now = datetime.now(UTC)
        appt.updated_at = now
        await self.db.flush()
        st = await self.db.get(StudentProfile, appt.student_id)
        su = await self.db.get(User, st.user_id) if st else None
        cu = await self.db.get(User, appt.counsellor_user_id) if appt.counsellor_user_id else None

        return CounsellingAppointmentResponse(
            id=appt.id,
            tenant_id=appt.tenant_id,
            student_id=appt.student_id,
            student_name=f"{su.first_name} {su.last_name}" if su else None,
            counsellor_user_id=appt.counsellor_user_id,
            counsellor_name=f"{cu.first_name} {cu.last_name}" if cu else None,
            category=appt.category,
            appointment_date=appt.appointment_date,
            start_time=appt.start_time,
            end_time=appt.end_time,
            duration_minutes=appt.duration_minutes,
            mode=appt.mode,
            venue_or_link=appt.venue_or_link,
            status=appt.status,
            request_reason=appt.request_reason,
            booked_by_user_id=appt.booked_by_user_id,
            cancellation_reason=appt.cancellation_reason,
            is_confidential=appt.is_confidential,
            has_confidential_notes=False,
            created_at=self._safe_dt(appt, "created_at", now),
            updated_at=now,
        )

    # =========================================================================
    # STRICT CONFIDENTIAL COUNSELLING RECORDS
    # =========================================================================

    async def create_confidential_record(
        self, data: ConfidentialCounsellingRecordCreate, counsellor_user_id: UUID
    ) -> ConfidentialCounsellingRecordResponse:
        # Check student
        student = await self.db.get(StudentProfile, data.student_id)
        if not student or student.tenant_id != self.tenant_id:
            raise NotFoundException("Student record not found")

        now = datetime.now(UTC)
        record = ConfidentialCounsellingRecord(
            tenant_id=self.tenant_id,
            appointment_id=data.appointment_id,
            student_id=data.student_id,
            counsellor_user_id=counsellor_user_id,
            session_notes_restricted=data.session_notes_restricted,
            intervention_type=data.intervention_type,
            clinical_observations=data.clinical_observations,
            follow_up_recommended=data.follow_up_recommended,
            follow_up_target_date=data.follow_up_target_date,
            consent_confirmed=data.consent_confirmed,
            access_count=1,
            last_accessed_at=now,
            created_at=now,
            updated_at=now,
        )
        self.db.add(record)
        await self.db.flush()

        # Audit log creation
        audit = SupportAuditLog(
            tenant_id=self.tenant_id,
            user_id=counsellor_user_id,
            action=SupportAuditAction.CREATE_CONFIDENTIAL_RECORD.value,
            resource_id=record.id,
            resource_type="CONFIDENTIAL_RECORD",
            created_at=now,
        )
        self.db.add(audit)
        await self.db.flush()

        su = await self.db.get(User, student.user_id) if student else None
        cu = await self.db.get(User, counsellor_user_id)

        return ConfidentialCounsellingRecordResponse(
            id=record.id,
            tenant_id=record.tenant_id,
            appointment_id=record.appointment_id,
            student_id=record.student_id,
            student_name=f"{su.first_name} {su.last_name}" if su else None,
            counsellor_user_id=record.counsellor_user_id,
            counsellor_name=f"{cu.first_name} {cu.last_name}" if cu else None,
            session_notes_restricted=record.session_notes_restricted,
            intervention_type=record.intervention_type,
            clinical_observations=record.clinical_observations,
            follow_up_recommended=record.follow_up_recommended,
            follow_up_target_date=record.follow_up_target_date,
            consent_confirmed=record.consent_confirmed,
            access_count=record.access_count,
            last_accessed_at=record.last_accessed_at,
            created_at=self._safe_dt(record, "created_at", now),
            updated_at=self._safe_dt(record, "updated_at", now),
        )

    async def get_confidential_record(
        self, record_id: UUID, accessor_user_id: UUID
    ) -> ConfidentialCounsellingRecordResponse:
        record = await self.db.get(ConfidentialCounsellingRecord, record_id)
        if not record or record.tenant_id != self.tenant_id:
            raise NotFoundException("Confidential counselling record not found")

        now = datetime.now(UTC)
        # Increment access count and log audit
        record.access_count += 1
        record.last_accessed_at = now
        record.updated_at = now

        audit = SupportAuditLog(
            tenant_id=self.tenant_id,
            user_id=accessor_user_id,
            action=SupportAuditAction.VIEW_CONFIDENTIAL_RECORD.value,
            resource_id=record.id,
            resource_type="CONFIDENTIAL_RECORD",
            created_at=now,
        )
        self.db.add(audit)
        await self.db.flush()

        st = await self.db.get(StudentProfile, record.student_id)
        su = await self.db.get(User, st.user_id) if st else None
        cu = await self.db.get(User, record.counsellor_user_id)

        return ConfidentialCounsellingRecordResponse(
            id=record.id,
            tenant_id=record.tenant_id,
            appointment_id=record.appointment_id,
            student_id=record.student_id,
            student_name=f"{su.first_name} {su.last_name}" if su else None,
            counsellor_user_id=record.counsellor_user_id,
            counsellor_name=f"{cu.first_name} {cu.last_name}" if cu else None,
            session_notes_restricted=record.session_notes_restricted,
            intervention_type=record.intervention_type,
            clinical_observations=record.clinical_observations,
            follow_up_recommended=record.follow_up_recommended,
            follow_up_target_date=record.follow_up_target_date,
            consent_confirmed=record.consent_confirmed,
            access_count=record.access_count,
            last_accessed_at=record.last_accessed_at,
            created_at=self._safe_dt(record, "created_at", now),
            updated_at=now,
        )

    # =========================================================================
    # STUDENT DEVELOPMENT PLANS (IDP)
    # =========================================================================

    async def create_development_plan(
        self, data: StudentDevelopmentPlanCreate
    ) -> StudentDevelopmentPlanResponse:
        now = datetime.now(UTC)
        plan = StudentDevelopmentPlan(
            tenant_id=self.tenant_id,
            student_id=data.student_id,
            mentor_user_id=data.mentor_user_id,
            title=data.title,
            academic_year=data.academic_year,
            status=PlanStatus.ACTIVE.value,
            overall_progress_pct=0,
            review_frequency=data.review_frequency,
            next_review_date=data.next_review_date,
            strengths_summary=data.strengths_summary,
            areas_for_growth=data.areas_for_growth,
            career_aspirations=data.career_aspirations,
            created_at=now,
            updated_at=now,
        )
        self.db.add(plan)
        await self.db.flush()

        # Add initial goals & action items if provided
        for g_in in data.goals:
            goal = DevelopmentGoal(
                tenant_id=self.tenant_id,
                plan_id=plan.id,
                category=g_in.category.value,
                title=g_in.title,
                description=g_in.description,
                target_date=g_in.target_date,
                status=GoalStatus.ACTIVE.value,
                progress_pct=0,
                measurable_milestones=g_in.measurable_milestones,
                mentor_notes=g_in.mentor_notes,
                created_at=now,
                updated_at=now,
            )
            self.db.add(goal)
            await self.db.flush()
            for act_in in g_in.action_items:
                action = DevelopmentActionItem(
                    tenant_id=self.tenant_id,
                    goal_id=goal.id,
                    title=act_in.title,
                    due_date=act_in.due_date,
                    status=ActionItemStatus.PENDING.value,
                    assigned_to_role=act_in.assigned_to_role,
                    created_at=now,
                    updated_at=now,
                )
                self.db.add(action)
                await self.db.flush()

        return await self.get_development_plan(plan.id)

    async def get_development_plan(self, plan_id: UUID) -> StudentDevelopmentPlanResponse:
        stmt = (
            select(StudentDevelopmentPlan)
            .options(
                selectinload(StudentDevelopmentPlan.goals).selectinload(DevelopmentGoal.action_items)
            )
            .where(
                and_(
                    StudentDevelopmentPlan.tenant_id == self.tenant_id,
                    StudentDevelopmentPlan.id == plan_id,
                )
            )
        )
        plan = (await self.db.execute(stmt)).scalar_one_or_none()
        if not plan:
            raise NotFoundException("Development plan not found")

        st = await self.db.get(StudentProfile, plan.student_id)
        su = await self.db.get(User, st.user_id) if st else None
        mu = await self.db.get(User, plan.mentor_user_id) if plan.mentor_user_id else None

        goals_res: list[DevelopmentGoalResponse] = []
        for g in plan.goals:
            act_res = [
                DevelopmentActionItemResponse(
                    id=a.id,
                    tenant_id=a.tenant_id,
                    goal_id=a.goal_id,
                    title=a.title,
                    due_date=a.due_date,
                    status=a.status,
                    assigned_to_role=a.assigned_to_role,
                    completed_at=a.completed_at,
                    created_at=self._safe_dt(a, "created_at"),
                    updated_at=self._safe_dt(a, "updated_at"),
                )
                for a in g.action_items
            ]
            goals_res.append(
                DevelopmentGoalResponse(
                    id=g.id,
                    tenant_id=g.tenant_id,
                    plan_id=g.plan_id,
                    category=g.category,
                    title=g.title,
                    description=g.description,
                    target_date=g.target_date,
                    status=g.status,
                    progress_pct=g.progress_pct,
                    measurable_milestones=g.measurable_milestones,
                    mentor_notes=g.mentor_notes,
                    student_reflection=g.student_reflection,
                    action_items=act_res,
                    created_at=self._safe_dt(g, "created_at"),
                    updated_at=self._safe_dt(g, "updated_at"),
                )
            )

        return StudentDevelopmentPlanResponse(
            id=plan.id,
            tenant_id=plan.tenant_id,
            student_id=plan.student_id,
            student_name=f"{su.first_name} {su.last_name}" if su else None,
            mentor_user_id=plan.mentor_user_id,
            mentor_name=f"{mu.first_name} {mu.last_name}" if mu else None,
            title=plan.title,
            academic_year=plan.academic_year,
            status=plan.status,
            overall_progress_pct=plan.overall_progress_pct,
            review_frequency=plan.review_frequency,
            last_reviewed_at=plan.last_reviewed_at,
            next_review_date=plan.next_review_date,
            strengths_summary=plan.strengths_summary,
            areas_for_growth=plan.areas_for_growth,
            career_aspirations=plan.career_aspirations,
            goals=goals_res,
            created_at=self._safe_dt(plan, "created_at"),
            updated_at=self._safe_dt(plan, "updated_at"),
        )

    async def list_development_plans(
        self, student_id: UUID | None = None, mentor_user_id: UUID | None = None
    ) -> list[StudentDevelopmentPlanResponse]:
        stmt = (
            select(StudentDevelopmentPlan.id)
            .where(StudentDevelopmentPlan.tenant_id == self.tenant_id)
        )
        if student_id:
            stmt = stmt.where(StudentDevelopmentPlan.student_id == student_id)
        if mentor_user_id:
            stmt = stmt.where(StudentDevelopmentPlan.mentor_user_id == mentor_user_id)

        stmt = stmt.order_by(StudentDevelopmentPlan.created_at.desc())
        plan_ids = (await self.db.execute(stmt)).scalars().all()

        results: list[StudentDevelopmentPlanResponse] = []
        for pid in plan_ids:
            results.append(await self.get_development_plan(pid))
        return results

    async def add_goal_to_plan(
        self, plan_id: UUID, data: DevelopmentGoalCreate
    ) -> DevelopmentGoalResponse:
        plan = await self.db.get(StudentDevelopmentPlan, plan_id)
        if not plan or plan.tenant_id != self.tenant_id:
            raise NotFoundException("Development plan not found")

        now = datetime.now(UTC)
        goal = DevelopmentGoal(
            tenant_id=self.tenant_id,
            plan_id=plan_id,
            category=data.category.value,
            title=data.title,
            description=data.description,
            target_date=data.target_date,
            status=GoalStatus.ACTIVE.value,
            progress_pct=0,
            measurable_milestones=data.measurable_milestones,
            mentor_notes=data.mentor_notes,
            created_at=now,
            updated_at=now,
        )
        self.db.add(goal)
        await self.db.flush()

        act_res: list[DevelopmentActionItemResponse] = []
        for act_in in data.action_items:
            action = DevelopmentActionItem(
                tenant_id=self.tenant_id,
                goal_id=goal.id,
                title=act_in.title,
                due_date=act_in.due_date,
                status=ActionItemStatus.PENDING.value,
                assigned_to_role=act_in.assigned_to_role,
                created_at=now,
                updated_at=now,
            )
            self.db.add(action)
            await self.db.flush()
            act_res.append(
                DevelopmentActionItemResponse(
                    id=action.id,
                    tenant_id=action.tenant_id,
                    goal_id=action.goal_id,
                    title=action.title,
                    due_date=action.due_date,
                    status=action.status,
                    assigned_to_role=action.assigned_to_role,
                    completed_at=action.completed_at,
                    created_at=self._safe_dt(action, "created_at", now),
                    updated_at=self._safe_dt(action, "updated_at", now),
                )
            )

        await self._recalculate_plan_progress(plan_id)

        return DevelopmentGoalResponse(
            id=goal.id,
            tenant_id=goal.tenant_id,
            plan_id=goal.plan_id,
            category=goal.category,
            title=goal.title,
            description=goal.description,
            target_date=goal.target_date,
            status=goal.status,
            progress_pct=goal.progress_pct,
            measurable_milestones=goal.measurable_milestones,
            mentor_notes=goal.mentor_notes,
            student_reflection=goal.student_reflection,
            action_items=act_res,
            created_at=self._safe_dt(goal, "created_at", now),
            updated_at=self._safe_dt(goal, "updated_at", now),
        )

    async def update_goal(
        self, goal_id: UUID, data: DevelopmentGoalUpdate
    ) -> DevelopmentGoalResponse:
        goal = await self.db.get(DevelopmentGoal, goal_id)
        if not goal or goal.tenant_id != self.tenant_id:
            raise NotFoundException("Goal not found")

        if data.title is not None:
            goal.title = data.title
        if data.description is not None:
            goal.description = data.description
        if data.target_date is not None:
            goal.target_date = data.target_date
        if data.status is not None:
            goal.status = data.status.value
        if data.progress_pct is not None:
            goal.progress_pct = data.progress_pct
            if goal.progress_pct == 100:
                goal.status = GoalStatus.COMPLETED.value
        if data.measurable_milestones is not None:
            goal.measurable_milestones = data.measurable_milestones
        if data.mentor_notes is not None:
            goal.mentor_notes = data.mentor_notes
        if data.student_reflection is not None:
            goal.student_reflection = data.student_reflection

        now = datetime.now(UTC)
        goal.updated_at = now
        await self.db.flush()
        await self._recalculate_plan_progress(goal.plan_id)

        # Fetch action items
        act_stmt = select(DevelopmentActionItem).where(
            DevelopmentActionItem.goal_id == goal.id
        )
        actions = (await self.db.execute(act_stmt)).scalars().all()
        act_res = [
            DevelopmentActionItemResponse(
                id=a.id,
                tenant_id=a.tenant_id,
                goal_id=a.goal_id,
                title=a.title,
                due_date=a.due_date,
                status=a.status,
                assigned_to_role=a.assigned_to_role,
                completed_at=a.completed_at,
                created_at=self._safe_dt(a, "created_at", now),
                updated_at=self._safe_dt(a, "updated_at", now),
            )
            for a in actions
        ]

        return DevelopmentGoalResponse(
            id=goal.id,
            tenant_id=goal.tenant_id,
            plan_id=goal.plan_id,
            category=goal.category,
            title=goal.title,
            description=goal.description,
            target_date=goal.target_date,
            status=goal.status,
            progress_pct=goal.progress_pct,
            measurable_milestones=goal.measurable_milestones,
            mentor_notes=goal.mentor_notes,
            student_reflection=goal.student_reflection,
            action_items=act_res,
            created_at=self._safe_dt(goal, "created_at", now),
            updated_at=now,
        )

    async def _recalculate_plan_progress(self, plan_id: UUID) -> None:
        plan = await self.db.get(StudentDevelopmentPlan, plan_id)
        if not plan:
            return
        goals_stmt = select(DevelopmentGoal.progress_pct).where(
            and_(
                DevelopmentGoal.plan_id == plan_id,
                DevelopmentGoal.tenant_id == self.tenant_id,
            )
        )
        percentages = (await self.db.execute(goals_stmt)).scalars().all()
        if percentages:
            avg_progress = int(sum(percentages) / len(percentages))
            plan.overall_progress_pct = avg_progress
            if avg_progress >= 100:
                plan.status = PlanStatus.COMPLETED.value
            plan.updated_at = datetime.now(UTC)
            await self.db.flush()

    # =========================================================================
    # SUPPORT REFERRALS & FOLLOW-UPS
    # =========================================================================

    async def create_support_referral(
        self, data: SupportReferralCreate, referring_user_id: UUID
    ) -> SupportReferralResponse:
        student = await self.db.get(StudentProfile, data.student_id)
        if not student or student.tenant_id != self.tenant_id:
            raise NotFoundException("Student not found")

        # Config check
        config = await self.get_or_create_config()
        if config.require_student_consent_for_referral and not data.consent_obtained:
            raise ValidationException("Student consent is required by institutional policy for support referrals")

        # Generate unique referral code
        now_year = date.today().year
        count_stmt = select(func.count(SupportReferral.id)).where(
            SupportReferral.tenant_id == self.tenant_id
        )
        seq_num = (await self.db.execute(count_stmt)).scalar_one() or 0
        referral_code = f"REF-{now_year}-{seq_num + 1:04d}"

        now = datetime.now(UTC)
        referral = SupportReferral(
            tenant_id=self.tenant_id,
            referral_code=referral_code,
            student_id=data.student_id,
            referring_user_id=referring_user_id,
            referring_role=data.referring_role,
            target_service=data.target_service.value,
            reason_category=data.reason_category.value,
            priority=data.priority.value,
            summary_notes=data.summary_notes,
            status=ReferralStatus.PENDING.value,
            assigned_staff_user_id=data.assigned_staff_user_id,
            consent_obtained=data.consent_obtained,
            created_at=now,
            updated_at=now,
        )
        self.db.add(referral)
        await self.db.flush()

        su = await self.db.get(User, student.user_id) if student else None
        ru = await self.db.get(User, referring_user_id)
        au = await self.db.get(User, data.assigned_staff_user_id) if data.assigned_staff_user_id else None

        return SupportReferralResponse(
            id=referral.id,
            tenant_id=referral.tenant_id,
            referral_code=referral.referral_code,
            student_id=referral.student_id,
            student_name=f"{su.first_name} {su.last_name}" if su else None,
            referring_user_id=referring_user_id,
            referring_user_name=f"{ru.first_name} {ru.last_name}" if ru else None,
            referring_role=referral.referring_role,
            target_service=referral.target_service,
            reason_category=referral.reason_category,
            priority=referral.priority,
            summary_notes=referral.summary_notes,
            status=referral.status,
            assigned_staff_user_id=referral.assigned_staff_user_id,
            assigned_staff_name=f"{au.first_name} {au.last_name}" if au else None,
            consent_obtained=referral.consent_obtained,
            outcome_notes=referral.outcome_notes,
            closed_at=referral.closed_at,
            follow_ups=[],
            created_at=self._safe_dt(referral, "created_at", now),
            updated_at=self._safe_dt(referral, "updated_at", now),
        )

    async def list_support_referrals(
        self,
        student_id: UUID | None = None,
        target_service: str | None = None,
        status: str | None = None,
    ) -> list[SupportReferralResponse]:
        stmt = (
            select(SupportReferral)
            .options(selectinload(SupportReferral.follow_ups))
            .where(SupportReferral.tenant_id == self.tenant_id)
        )
        if student_id:
            stmt = stmt.where(SupportReferral.student_id == student_id)
        if target_service:
            stmt = stmt.where(SupportReferral.target_service == target_service)
        if status:
            stmt = stmt.where(SupportReferral.status == status)

        stmt = stmt.order_by(SupportReferral.created_at.desc())
        referrals = (await self.db.execute(stmt)).scalars().all()

        responses: list[SupportReferralResponse] = []
        for ref in referrals:
            st = await self.db.get(StudentProfile, ref.student_id)
            su = await self.db.get(User, st.user_id) if st else None
            ru = await self.db.get(User, ref.referring_user_id)
            au = await self.db.get(User, ref.assigned_staff_user_id) if ref.assigned_staff_user_id else None
            f_res = [
                SupportFollowUpResponse(
                    id=f.id,
                    tenant_id=f.tenant_id,
                    referral_id=f.referral_id,
                    plan_id=f.plan_id,
                    appointment_id=f.appointment_id,
                    assigned_user_id=f.assigned_user_id,
                    assigned_user_name=None,
                    title=f.title,
                    due_date=f.due_date,
                    notes=f.notes,
                    status=f.status,
                    completed_at=f.completed_at,
                    created_at=self._safe_dt(f, "created_at"),
                    updated_at=self._safe_dt(f, "updated_at"),
                )
                for f in ref.follow_ups
            ]
            responses.append(
                SupportReferralResponse(
                    id=ref.id,
                    tenant_id=ref.tenant_id,
                    referral_code=ref.referral_code,
                    student_id=ref.student_id,
                    student_name=f"{su.first_name} {su.last_name}" if su else None,
                    referring_user_id=ref.referring_user_id,
                    referring_user_name=f"{ru.first_name} {ru.last_name}" if ru else None,
                    referring_role=ref.referring_role,
                    target_service=ref.target_service,
                    reason_category=ref.reason_category,
                    priority=ref.priority,
                    summary_notes=ref.summary_notes,
                    status=ref.status,
                    assigned_staff_user_id=ref.assigned_staff_user_id,
                    assigned_staff_name=f"{au.first_name} {au.last_name}" if au else None,
                    consent_obtained=ref.consent_obtained,
                    outcome_notes=ref.outcome_notes,
                    closed_at=ref.closed_at,
                    follow_ups=f_res,
                    created_at=self._safe_dt(ref, "created_at"),
                    updated_at=self._safe_dt(ref, "updated_at"),
                )
            )
        return responses

    async def update_support_referral(
        self, referral_id: UUID, data: SupportReferralUpdate
    ) -> SupportReferralResponse:
        ref = await self.db.get(SupportReferral, referral_id)
        if not ref or ref.tenant_id != self.tenant_id:
            raise NotFoundException("Support referral not found")

        now = datetime.now(UTC)
        if data.status is not None:
            ref.status = data.status.value
            if data.status in [ReferralStatus.COMPLETED, ReferralStatus.DECLINED, ReferralStatus.CANCELLED]:
                ref.closed_at = now
        if data.assigned_staff_user_id is not None:
            ref.assigned_staff_user_id = data.assigned_staff_user_id
        if data.outcome_notes is not None:
            ref.outcome_notes = data.outcome_notes

        ref.updated_at = now
        await self.db.flush()
        refs = await self.list_support_referrals()
        return [r for r in refs if r.id == referral_id][0]

    async def create_follow_up(self, data: SupportFollowUpCreate) -> SupportFollowUpResponse:
        now = datetime.now(UTC)
        followup = SupportFollowUp(
            tenant_id=self.tenant_id,
            referral_id=data.referral_id,
            plan_id=data.plan_id,
            appointment_id=data.appointment_id,
            assigned_user_id=data.assigned_user_id,
            title=data.title,
            due_date=data.due_date,
            notes=data.notes,
            status=FollowUpStatus.PENDING.value,
            created_at=now,
            updated_at=now,
        )
        self.db.add(followup)
        await self.db.flush()

        u = await self.db.get(User, data.assigned_user_id)
        return SupportFollowUpResponse(
            id=followup.id,
            tenant_id=followup.tenant_id,
            referral_id=followup.referral_id,
            plan_id=followup.plan_id,
            appointment_id=followup.appointment_id,
            assigned_user_id=followup.assigned_user_id,
            assigned_user_name=f"{u.first_name} {u.last_name}" if u else None,
            title=followup.title,
            due_date=followup.due_date,
            notes=followup.notes,
            status=followup.status,
            created_at=self._safe_dt(followup, "created_at", now),
            updated_at=self._safe_dt(followup, "updated_at", now),
        )

    async def list_follow_ups(
        self, assigned_user_id: UUID | None = None, status: str | None = None
    ) -> list[SupportFollowUpResponse]:
        stmt = select(SupportFollowUp).where(SupportFollowUp.tenant_id == self.tenant_id)
        if assigned_user_id:
            stmt = stmt.where(SupportFollowUp.assigned_user_id == assigned_user_id)
        if status:
            stmt = stmt.where(SupportFollowUp.status == status)

        stmt = stmt.order_by(SupportFollowUp.due_date.asc())
        followups = (await self.db.execute(stmt)).scalars().all()

        responses: list[SupportFollowUpResponse] = []
        for f in followups:
            u = await self.db.get(User, f.assigned_user_id)
            responses.append(
                SupportFollowUpResponse(
                    id=f.id,
                    tenant_id=f.tenant_id,
                    referral_id=f.referral_id,
                    plan_id=f.plan_id,
                    appointment_id=f.appointment_id,
                    assigned_user_id=f.assigned_user_id,
                    assigned_user_name=f"{u.first_name} {u.last_name}" if u else None,
                    title=f.title,
                    due_date=f.due_date,
                    notes=f.notes,
                    status=f.status,
                    completed_at=f.completed_at,
                    created_at=self._safe_dt(f, "created_at"),
                    updated_at=self._safe_dt(f, "updated_at"),
                )
            )
        return responses

    async def update_follow_up(
        self, followup_id: UUID, data: SupportFollowUpUpdate
    ) -> SupportFollowUpResponse:
        f = await self.db.get(SupportFollowUp, followup_id)
        if not f or f.tenant_id != self.tenant_id:
            raise NotFoundException("Follow-up not found")

        now = datetime.now(UTC)
        if data.title is not None:
            f.title = data.title
        if data.due_date is not None:
            f.due_date = data.due_date
        if data.notes is not None:
            f.notes = data.notes
        if data.status is not None:
            f.status = data.status
            if data.status == FollowUpStatus.COMPLETED.value:
                f.completed_at = now

        f.updated_at = now
        await self.db.flush()
        u = await self.db.get(User, f.assigned_user_id)
        return SupportFollowUpResponse(
            id=f.id,
            tenant_id=f.tenant_id,
            referral_id=f.referral_id,
            plan_id=f.plan_id,
            appointment_id=f.appointment_id,
            assigned_user_id=f.assigned_user_id,
            assigned_user_name=f"{u.first_name} {u.last_name}" if u else None,
            title=f.title,
            due_date=f.due_date,
            notes=f.notes,
            status=f.status,
            completed_at=f.completed_at,
            created_at=self._safe_dt(f, "created_at", now),
            updated_at=now,
        )

    # =========================================================================
    # AUDIT LOGS & PRIVACY-SAFE TELEMETRY
    # =========================================================================

    async def list_audit_logs(self, limit: int = 50) -> list[SupportAuditLogResponse]:
        stmt = (
            select(SupportAuditLog)
            .where(SupportAuditLog.tenant_id == self.tenant_id)
            .order_by(SupportAuditLog.created_at.desc())
            .limit(limit)
        )
        logs = (await self.db.execute(stmt)).scalars().all()
        responses: list[SupportAuditLogResponse] = []
        for l in logs:
            u = await self.db.get(User, l.user_id)
            responses.append(
                SupportAuditLogResponse(
                    id=l.id,
                    tenant_id=l.tenant_id,
                    user_id=l.user_id,
                    user_name=f"{u.first_name} {u.last_name}" if u else None,
                    action=l.action,
                    resource_id=l.resource_id,
                    resource_type=l.resource_type,
                    ip_address=l.ip_address,
                    user_agent=l.user_agent,
                    created_at=self._safe_dt(l, "created_at"),
                )
            )
        return responses

    async def get_telemetry_metrics(self) -> StudentSupportTelemetryResponse:
        """Aggregates metrics safely. Does NOT expose individual records or confidential session content."""
        # 1. Active mentor assignments
        active_assign_stmt = select(func.count(MentorAssignment.id)).where(
            and_(
                MentorAssignment.tenant_id == self.tenant_id,
                MentorAssignment.status == MentorAssignmentStatus.ACTIVE.value,
            )
        )
        total_active_assignments = (await self.db.execute(active_assign_stmt)).scalar_one() or 0

        # 2. Total students without active mentor
        total_students_stmt = select(func.count(StudentProfile.id)).where(
            StudentProfile.tenant_id == self.tenant_id
        )
        total_students = (await self.db.execute(total_students_stmt)).scalar_one() or 0
        unassigned = max(0, total_students - total_active_assignments)

        # 3. Sessions completed
        sessions_stmt = select(func.count(MentoringSession.id)).where(
            and_(
                MentoringSession.tenant_id == self.tenant_id,
                MentoringSession.status == SessionStatus.COMPLETED.value,
            )
        )
        sessions_completed = (await self.db.execute(sessions_stmt)).scalar_one() or 0

        # 4. Appointment utilization
        total_appts_stmt = select(func.count(CounsellingAppointment.id)).where(
            CounsellingAppointment.tenant_id == self.tenant_id
        )
        completed_appts_stmt = select(func.count(CounsellingAppointment.id)).where(
            and_(
                CounsellingAppointment.tenant_id == self.tenant_id,
                CounsellingAppointment.status.in_([
                    AppointmentStatus.COMPLETED.value,
                    AppointmentStatus.CHECKED_IN.value,
                ]),
            )
        )
        total_appts = (await self.db.execute(total_appts_stmt)).scalar_one() or 0
        completed_appts = (await self.db.execute(completed_appts_stmt)).scalar_one() or 0
        util_rate = round((completed_appts / total_appts * 100), 1) if total_appts > 0 else 0.0

        # 5. Pending referrals
        pending_ref_stmt = select(func.count(SupportReferral.id)).where(
            and_(
                SupportReferral.tenant_id == self.tenant_id,
                SupportReferral.status == ReferralStatus.PENDING.value,
            )
        )
        pending_refs = (await self.db.execute(pending_ref_stmt)).scalar_one() or 0

        # 6. Overdue follow ups
        today = date.today()
        overdue_stmt = select(func.count(SupportFollowUp.id)).where(
            and_(
                SupportFollowUp.tenant_id == self.tenant_id,
                SupportFollowUp.status != FollowUpStatus.COMPLETED.value,
                SupportFollowUp.due_date < today,
            )
        )
        overdue_followups = (await self.db.execute(overdue_stmt)).scalar_one() or 0

        # 7. Development plan completion rate
        total_plans_stmt = select(func.count(StudentDevelopmentPlan.id)).where(
            StudentDevelopmentPlan.tenant_id == self.tenant_id
        )
        completed_plans_stmt = select(func.count(StudentDevelopmentPlan.id)).where(
            and_(
                StudentDevelopmentPlan.tenant_id == self.tenant_id,
                StudentDevelopmentPlan.status == PlanStatus.COMPLETED.value,
            )
        )
        total_plans = (await self.db.execute(total_plans_stmt)).scalar_one() or 0
        completed_plans = (await self.db.execute(completed_plans_stmt)).scalar_one() or 0
        plan_comp_rate = round((completed_plans / total_plans * 100), 1) if total_plans > 0 else 0.0

        # 8. Referrals by target service
        ref_svc_stmt = select(
            SupportReferral.target_service, func.count(SupportReferral.id)
        ).where(SupportReferral.tenant_id == self.tenant_id).group_by(SupportReferral.target_service)
        ref_by_svc = dict((await self.db.execute(ref_svc_stmt)).all())

        # 9. Goals by category
        goals_cat_stmt = select(
            DevelopmentGoal.category, func.count(DevelopmentGoal.id)
        ).where(DevelopmentGoal.tenant_id == self.tenant_id).group_by(DevelopmentGoal.category)
        goals_by_cat = dict((await self.db.execute(goals_cat_stmt)).all())

        return StudentSupportTelemetryResponse(
            total_active_mentor_assignments=total_active_assignments,
            total_unassigned_students=unassigned,
            mentoring_sessions_completed_this_month=sessions_completed,
            appointment_utilization_rate_pct=util_rate,
            pending_support_referrals=pending_refs,
            overdue_follow_ups=overdue_followups,
            development_plan_completion_rate_pct=plan_comp_rate,
            referrals_by_service=ref_by_svc,
            goals_by_category=goals_by_cat,
        )
