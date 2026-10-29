from datetime import date, datetime, time
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantScopedModel

if TYPE_CHECKING:
    from app.models.academics import Classroom, CourseOffering, TimeSlot, TimetableEntry
    from app.models.core import AcademicYear, Section, Semester
    from app.models.people import FacultyProfile, StudentProfile, User


class AttendancePolicy(TenantScopedModel):
    """Institutional, departmental, or course-specific attendance threshold policy."""

    __tablename__ = "attendance_policies"
    __table_args__ = (
        Index("ix_att_policy_tenant_scope", "tenant_id", "department_id", "program_id", "course_offering_id"),
    )

    name: Mapped[str] = mapped_column(String(128), default="Institutional Standard Policy", nullable=False)
    department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_departments.id", ondelete="RESTRICT"),
        nullable=True,
    )
    program_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_programs.id", ondelete="RESTRICT"),
        nullable=True,
    )
    academic_year_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_academic_years.id", ondelete="RESTRICT"),
        nullable=True,
    )
    semester_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_semesters.id", ondelete="RESTRICT"),
        nullable=True,
    )
    course_offering_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("academics_course_offerings.id", ondelete="RESTRICT"),
        nullable=True,
    )

    # Threshold percentages
    minimum_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=75.00, nullable=False
    )
    warning_threshold_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=80.00, nullable=False
    )
    critical_threshold_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=65.00, nullable=False
    )
    condonation_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=65.00, nullable=False
    )

    # Calculation behavior
    late_grace_minutes: Mapped[int] = mapped_column(default=10, nullable=False)
    late_weight: Mapped[Decimal] = mapped_column(
        Numeric(3, 2), default=1.00, nullable=False
    )  # 1.00 = counts as full present, 0.50 = half session
    excused_counts_as_present: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    on_leave_counts_as_present: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    exclude_excused_from_total: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Policy Lifecycle & Versioning
    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)  # ACTIVE, ARCHIVED, DRAFT
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class AttendanceSession(TenantScopedModel):
    """Instructional class period during which attendance is captured."""

    __tablename__ = "attendance_sessions"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "course_offering_id",
            "session_date",
            "period_number",
            name="uq_attendance_session_slot",
        ),
        Index("ix_att_session_course_date", "tenant_id", "course_offering_id", "session_date"),
        Index("ix_att_session_faculty_date", "tenant_id", "faculty_id", "session_date"),
        Index("ix_att_session_section_date", "tenant_id", "section_id", "session_date"),
        Index("ix_att_session_status", "tenant_id", "status"),
        Index("idx_perf_att_session_search", "tenant_id", "session_date", "status"),
    )

    course_offering_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("academics_course_offerings.id", ondelete="RESTRICT"),
        nullable=False,
    )
    section_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_sections.id", ondelete="RESTRICT"),
        nullable=False,
    )
    faculty_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_faculty.id", ondelete="RESTRICT"),
        nullable=False,
    )
    academic_year_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_academic_years.id", ondelete="RESTRICT"),
        nullable=False,
    )
    semester_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_semesters.id", ondelete="RESTRICT"),
        nullable=False,
    )
    timetable_slot_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("academics_timetable_slots.id", ondelete="SET NULL"),
        nullable=True,
    )
    room_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("academics_rooms.id", ondelete="SET NULL"),
        nullable=True,
    )
    time_slot_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("academics_time_slots.id", ondelete="SET NULL"),
        nullable=True,
    )
    session_date: Mapped[date] = mapped_column(Date, nullable=False)
    period_number: Mapped[int] = mapped_column(nullable=False)
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    session_type: Mapped[str] = mapped_column(
        String(32), default="LECTURE", nullable=False
    )  # LECTURE, LAB, TUTORIAL, REMEDIAL
    status: Mapped[str] = mapped_column(
        String(32), default="SCHEDULED", nullable=False
    )  # SCHEDULED, OPEN, MARKED, LOCKED, CANCELLED
    topic: Mapped[str | None] = mapped_column(String(255), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    locked_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    course_offering: Mapped["CourseOffering"] = relationship()
    section: Mapped["Section"] = relationship()
    faculty: Mapped["FacultyProfile"] = relationship()
    academic_year: Mapped["AcademicYear"] = relationship()
    semester: Mapped["Semester"] = relationship()
    room: Mapped["Classroom | None"] = relationship()
    time_slot: Mapped["TimeSlot | None"] = relationship()
    timetable_slot: Mapped["TimetableEntry | None"] = relationship()
    records: Mapped[list["AttendanceRecord"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class AttendanceRecord(TenantScopedModel):
    """Atomic presence log for a student in a session."""

    __tablename__ = "attendance_records"
    __table_args__ = (
        UniqueConstraint("session_id", "student_id", name="uq_attendance_record_student"),
        Index("ix_att_rec_student_status", "tenant_id", "student_id", "status"),
        Index("ix_att_rec_session", "session_id"),
        Index("idx_perf_att_rec_student_date", "tenant_id", "student_id", "created_at"),
    )

    session_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("attendance_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32), default="PRESENT", nullable=False
    )  # PRESENT, ABSENT, LATE, EXCUSED, ON_LEAVE
    remarks: Mapped[str | None] = mapped_column(String(255), nullable=True)
    recorded_by_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    session: Mapped["AttendanceSession"] = relationship(back_populates="records")
    student: Mapped["StudentProfile"] = relationship()
    recorded_by: Mapped["User"] = relationship()
    corrections: Mapped[list["AttendanceCorrectionRequest"]] = relationship(
        back_populates="record", cascade="all, delete-orphan"
    )


class AttendanceCorrectionRequest(TenantScopedModel):
    """Audit-backed supervisor correction workflow for locked attendance."""

    __tablename__ = "attendance_corrections"
    __table_args__ = (
        Index("ix_att_correction_record", "tenant_id", "attendance_record_id"),
        Index("ix_att_correction_status", "tenant_id", "approval_status"),
    )

    attendance_record_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("attendance_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    previous_status: Mapped[str] = mapped_column(String(32), nullable=False)
    requested_status: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    requested_by_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    approved_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    approval_status: Mapped[str] = mapped_column(
        String(32), default="PENDING", nullable=False
    )  # PENDING, APPROVED, REJECTED
    approval_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    record: Mapped["AttendanceRecord"] = relationship(back_populates="corrections")
    requested_by: Mapped["User"] = relationship(foreign_keys=[requested_by_user_id])
    approved_by: Mapped["User | None"] = relationship(foreign_keys=[approved_by_user_id])


class StudentLeaveRequest(TenantScopedModel):
    """Student formal leave application."""

    __tablename__ = "attendance_leave_requests"
    __table_args__ = (
        Index("ix_att_leave_student_dates", "tenant_id", "student_id", "start_date", "end_date"),
        Index("ix_att_leave_status", "tenant_id", "status"),
    )

    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    leave_type: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # MEDICAL, CASUAL, ON_DUTY, SPORTS, OTHER
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    proof_storage_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default="PENDING", nullable=False
    )  # PENDING, APPROVED, REJECTED, CANCELLED
    reviewed_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    student: Mapped["StudentProfile"] = relationship()
    reviewed_by: Mapped["User | None"] = relationship(foreign_keys=[reviewed_by_user_id])


class AttendanceAlert(TenantScopedModel):
    """Generated notification/event caused by attendance conditions (low attendance, consecutive absence)."""

    __tablename__ = "attendance_alerts"
    __table_args__ = (
        Index("ix_att_alert_student", "tenant_id", "student_id", "is_resolved"),
    )

    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="CASCADE"),
        nullable=False,
    )
    course_offering_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("academics_course_offerings.id", ondelete="CASCADE"),
        nullable=True,
    )
    alert_type: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # LOW_ATTENDANCE_WARNING, LOW_ATTENDANCE_CRITICAL, CONSECUTIVE_ABSENCE, SESSION_MISSED
    severity: Mapped[str] = mapped_column(
        String(32), default="WARNING", nullable=False
    )  # INFO, WARNING, CRITICAL
    attendance_percentage: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    threshold_percentage: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    student: Mapped["StudentProfile"] = relationship()
    course_offering: Mapped["CourseOffering | None"] = relationship()
