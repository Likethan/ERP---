"""SQLAlchemy Entities for Enterprise Academic Timetable, Resource Scheduling & Conflict Resolution (Step 49).

CampusOS Tagline: "One Campus. One System. One Source of Truth."

Coordinates academic timetables across institutions, campuses, departments,
programs, faculty, student cohorts, classrooms, laboratories, and academic terms.
Supports generation, resource allocation, conflict detection, controlled publication,
schedule changes, and schedule analytics.
"""

from datetime import date, datetime, time
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import TenantScopedModel

JSONB_COMPAT = JSON().with_variant(JSONB, "postgresql")


# -----------------------------------------------------------------------------
# 1. Enums
# -----------------------------------------------------------------------------


class TimetableVersionStatus(StrEnum):
    """Lifecycle status for a timetable schedule version."""

    DRAFT = "DRAFT"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"
    SUPERSEDED = "SUPERSEDED"
    ARCHIVED = "ARCHIVED"


class SessionType(StrEnum):
    """Academic session pedagogical category."""

    LECTURE = "LECTURE"
    TUTORIAL = "TUTORIAL"
    LAB = "LAB"
    PRACTICAL = "PRACTICAL"
    SEMINAR = "SEMINAR"
    WORKSHOP = "WORKSHOP"


class RecurrencePattern(StrEnum):
    """Recurring frequency of session."""

    WEEKLY = "WEEKLY"
    BIWEEKLY_ODD = "BIWEEKLY_ODD"
    BIWEEKLY_EVEN = "BIWEEKLY_EVEN"


class CalendarPeriodType(StrEnum):
    """Academic calendar period classification."""

    HOLIDAY = "HOLIDAY"
    EXAM_PERIOD = "EXAM_PERIOD"
    RECESS = "RECESS"
    SPECIAL_WORKING_DAY = "SPECIAL_WORKING_DAY"
    EVENT_CLOSURE = "EVENT_CLOSURE"


class ScheduleExceptionType(StrEnum):
    """Temporary calendar exception types."""

    HOLIDAY_CLOSURE = "HOLIDAY_CLOSURE"
    TIMETABLE_SWAP = "TIMETABLE_SWAP"
    SESSION_OVERRIDE = "SESSION_OVERRIDE"
    EVENT_RESERVATION = "EVENT_RESERVATION"


class ReservationType(StrEnum):
    """Physical space or equipment booking type."""

    TIMETABLE = "TIMETABLE"
    MAINTENANCE = "MAINTENANCE"
    CAMPUS_EVENT = "CAMPUS_EVENT"
    EXAMINATION = "EXAMINATION"
    AD_HOC = "AD_HOC"


class ReservationStatus(StrEnum):
    """Status of resource reservation."""

    CONFIRMED = "CONFIRMED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    CANCELLED = "CANCELLED"


class MaintenanceStatus(StrEnum):
    """Facility maintenance status."""

    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class GenerationJobStatus(StrEnum):
    """Status of constraint-based generation job."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ConflictSeverity(StrEnum):
    """Severity classification of detected schedule conflicts."""

    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


class ConflictType(StrEnum):
    """Taxonomy of detected scheduling collisions and violations."""

    FACULTY_DOUBLE_BOOKING = "FACULTY_DOUBLE_BOOKING"
    ROOM_DOUBLE_BOOKING = "ROOM_DOUBLE_BOOKING"
    COHORT_DOUBLE_BOOKING = "COHORT_DOUBLE_BOOKING"
    CAPACITY_EXCEEDED = "CAPACITY_EXCEEDED"
    FACULTY_UNAVAILABLE = "FACULTY_UNAVAILABLE"
    WORKLOAD_EXCEEDED = "WORKLOAD_EXCEEDED"
    ROOM_TYPE_MISMATCH = "ROOM_TYPE_MISMATCH"
    HOLIDAY_CONFLICT = "HOLIDAY_CONFLICT"
    MAINTENANCE_CONFLICT = "MAINTENANCE_CONFLICT"


class ChangeRequestType(StrEnum):
    """Action category of schedule change request."""

    RESCHEDULE = "RESCHEDULE"
    ROOM_SWAP = "ROOM_SWAP"
    FACULTY_SUBSTITUTE = "FACULTY_SUBSTITUTE"
    CANCEL_SESSION = "CANCEL_SESSION"
    ADD_SESSION = "ADD_SESSION"


class ChangeRequestStatus(StrEnum):
    """Workflow state of timetable change request."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    APPLIED = "APPLIED"
    CANCELLED = "CANCELLED"


class PublicationType(StrEnum):
    """Publication event classification."""

    INITIAL = "INITIAL"
    REVISION = "REVISION"
    EMERGENCY_UPDATE = "EMERGENCY_UPDATE"


# -----------------------------------------------------------------------------
# 2. Schedule Entities & Versioning
# -----------------------------------------------------------------------------


class TimetableSchedule(TenantScopedModel):
    """Master timetable container bound to academic year, semester, and scope."""

    __tablename__ = "timetable_schedules"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_timetable_schedules_tenant_code"),
        Index("ix_timetable_sched_tenant_sem", "tenant_id", "academic_year_id", "semester_id"),
        Index("ix_timetable_sched_tenant_sec", "tenant_id", "section_id"),
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
    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="SET NULL"),
        nullable=True,
    )
    department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    program_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_programs.id", ondelete="SET NULL"),
        nullable=True,
    )
    section_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_sections.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    academic_year = relationship("AcademicYear")
    semester = relationship("Semester")
    campus = relationship("Campus")
    department = relationship("Department")
    program = relationship("Program")
    section = relationship("Section")
    versions: Mapped[list["TimetableVersion"]] = relationship(
        back_populates="schedule", cascade="all, delete-orphan", order_by="TimetableVersion.version_number.desc()"
    )


class TimetableVersion(TenantScopedModel):
    """Immutable or staged version snapshot of a timetable schedule."""

    __tablename__ = "timetable_versions"
    __table_args__ = (
        UniqueConstraint("schedule_id", "version_number", name="uq_timetable_versions_sched_ver"),
        Index("ix_timetable_ver_tenant_status", "tenant_id", "status"),
        Index("ix_timetable_ver_schedule_status", "schedule_id", "status"),
    )

    schedule_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("timetable_schedules.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=TimetableVersionStatus.DRAFT, nullable=False
    )
    effective_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    approved_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    schedule: Mapped["TimetableSchedule"] = relationship(back_populates="versions")
    approved_by = relationship("User", foreign_keys=[approved_by_user_id])
    published_by = relationship("User", foreign_keys=[published_by_user_id])
    sessions: Mapped[list["TimetableSession"]] = relationship(
        back_populates="version", cascade="all, delete-orphan", order_by="TimetableSession.day_of_week, TimetableSession.start_time"
    )
    conflicts: Mapped[list["TimetableConflict"]] = relationship(
        back_populates="version", cascade="all, delete-orphan"
    )
    change_requests: Mapped[list["TimetableChangeRequest"]] = relationship(
        back_populates="version", cascade="all, delete-orphan"
    )


class TimetableSession(TenantScopedModel):
    """Discrete instructional session in a timetable version."""

    __tablename__ = "timetable_sessions"
    __table_args__ = (
        Index("ix_tt_sessions_tenant_day", "tenant_id", "day_of_week"),
        Index("ix_tt_sessions_tenant_room", "tenant_id", "room_id", "day_of_week"),
        Index("ix_tt_sessions_tenant_fac", "tenant_id", "faculty_id", "day_of_week"),
        Index("ix_tt_sessions_tenant_sec", "tenant_id", "section_id", "day_of_week"),
    )

    version_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("timetable_versions.id", ondelete="CASCADE"),
        nullable=False,
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
    subject_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("academics_subjects.id", ondelete="RESTRICT"),
        nullable=True,
    )
    faculty_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_faculty.id", ondelete="RESTRICT"),
        nullable=True,
    )
    co_faculty_ids: Mapped[list] = mapped_column(JSONB_COMPAT, default=list, nullable=False)
    room_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("academics_rooms.id", ondelete="SET NULL"),
        nullable=True,
    )
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 = Mon ... 7 = Sun
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    time_slot_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("academics_time_slots.id", ondelete="SET NULL"),
        nullable=True,
    )
    session_type: Mapped[str] = mapped_column(
        String(32), default=SessionType.LECTURE, nullable=False
    )
    session_group: Mapped[str | None] = mapped_column(String(64), nullable=True)  # e.g., "BATCH-A"
    recurrence_pattern: Mapped[str] = mapped_column(
        String(32), default=RecurrencePattern.WEEKLY, nullable=False
    )
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    replacement_room_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("academics_rooms.id", ondelete="SET NULL"),
        nullable=True,
    )
    substitute_faculty_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_faculty.id", ondelete="SET NULL"),
        nullable=True,
    )
    transition_buffer_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    canonical_slot_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("academics_timetable_slots.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    version: Mapped["TimetableVersion"] = relationship(back_populates="sessions")
    course_offering = relationship("CourseOffering")
    section = relationship("Section")
    subject = relationship("Subject")
    faculty = relationship("FacultyProfile", foreign_keys=[faculty_id])
    substitute_faculty = relationship("FacultyProfile", foreign_keys=[substitute_faculty_id])
    room = relationship("Classroom", foreign_keys=[room_id])
    replacement_room = relationship("Classroom", foreign_keys=[replacement_room_id])
    time_slot = relationship("TimeSlot")
    canonical_slot = relationship("TimetableEntry")


# -----------------------------------------------------------------------------
# 3. Calendar, Teaching Periods & Exceptions
# -----------------------------------------------------------------------------


class TeachingPeriodConfig(TenantScopedModel):
    """Institutional period, working hour, and break configuration."""

    __tablename__ = "timetable_teaching_periods"
    __table_args__ = (
        Index("ix_tt_periods_tenant_campus", "tenant_id", "campus_id"),
    )

    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="SET NULL"),
        nullable=True,
    )
    academic_year_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_academic_years.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    teaching_days: Mapped[list] = mapped_column(
        JSONB_COMPAT, default=lambda: [1, 2, 3, 4, 5, 6], nullable=False
    )
    day_start_time: Mapped[time] = mapped_column(Time, nullable=False)
    day_end_time: Mapped[time] = mapped_column(Time, nullable=False)
    period_duration_minutes: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    transition_buffer_minutes: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    lunch_start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    lunch_end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    breaks_json: Mapped[list] = mapped_column(JSONB_COMPAT, default=list, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    campus = relationship("Campus")
    academic_year = relationship("AcademicYear")


class AcademicCalendarPeriod(TenantScopedModel):
    """Institutional calendar milestones, holidays, recesses, and exam windows."""

    __tablename__ = "timetable_calendar_periods"
    __table_args__ = (
        Index("ix_tt_cal_tenant_dates", "tenant_id", "start_date", "end_date"),
    )

    academic_year_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_academic_years.id", ondelete="RESTRICT"),
        nullable=False,
    )
    semester_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_semesters.id", ondelete="SET NULL"),
        nullable=True,
    )
    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    calendar_type: Mapped[str] = mapped_column(
        String(32), default=CalendarPeriodType.HOLIDAY, nullable=False
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    affects_teaching: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    academic_year = relationship("AcademicYear")
    semester = relationship("Semester")
    campus = relationship("Campus")


class ScheduleException(TenantScopedModel):
    """Temporary date-specific schedule override or day swap."""

    __tablename__ = "timetable_schedule_exceptions"
    __table_args__ = (
        Index("ix_tt_exceptions_tenant_date", "tenant_id", "exception_date"),
    )

    schedule_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("timetable_schedules.id", ondelete="CASCADE"),
        nullable=True,
    )
    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="SET NULL"),
        nullable=True,
    )
    exception_date: Mapped[date] = mapped_column(Date, nullable=False)
    exception_type: Mapped[str] = mapped_column(
        String(32), default=ScheduleExceptionType.HOLIDAY_CLOSURE, nullable=False
    )
    substitute_day_of_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    affected_room_ids: Mapped[list] = mapped_column(JSONB_COMPAT, default=list, nullable=False)
    affected_section_ids: Mapped[list] = mapped_column(JSONB_COMPAT, default=list, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    schedule = relationship("TimetableSchedule")
    campus = relationship("Campus")


# -----------------------------------------------------------------------------
# 4. Faculty Availability & Workload
# -----------------------------------------------------------------------------


class FacultyAvailability(TenantScopedModel):
    """Faculty teaching availability windows and workload limits."""

    __tablename__ = "timetable_faculty_availability"
    __table_args__ = (
        Index("ix_tt_fac_avail_tenant_fac", "tenant_id", "faculty_id", "day_of_week"),
    )

    faculty_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_faculty.id", ondelete="CASCADE"),
        nullable=False,
    )
    academic_year_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_academic_years.id", ondelete="RESTRICT"),
        nullable=False,
    )
    semester_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_semesters.id", ondelete="RESTRICT"),
        nullable=True,
    )
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    available_start_time: Mapped[time] = mapped_column(Time, nullable=False)
    available_end_time: Mapped[time] = mapped_column(Time, nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    max_hours_per_day: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=Decimal("4.00"), nullable=False)
    max_hours_per_week: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=Decimal("18.00"), nullable=False)
    preferred_session_types: Mapped[list] = mapped_column(JSONB_COMPAT, default=list, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    faculty = relationship("FacultyProfile")
    academic_year = relationship("AcademicYear")
    semester = relationship("Semester")


# -----------------------------------------------------------------------------
# 5. Resource Reservations & Maintenance
# -----------------------------------------------------------------------------


class ResourceReservation(TenantScopedModel):
    """Physical room or laboratory exclusive reservation ledger."""

    __tablename__ = "timetable_resource_reservations"
    __table_args__ = (
        Index("ix_tt_res_tenant_room_dates", "tenant_id", "room_id", "start_datetime", "end_datetime"),
        Index("ix_tt_res_tenant_status", "tenant_id", "status"),
    )

    room_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("academics_rooms.id", ondelete="CASCADE"),
        nullable=False,
    )
    reservation_type: Mapped[str] = mapped_column(
        String(32), default=ReservationType.TIMETABLE, nullable=False
    )
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    start_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=ReservationStatus.CONFIRMED, nullable=False
    )
    session_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("timetable_sessions.id", ondelete="SET NULL"),
        nullable=True,
    )
    requested_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_exclusive: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    room = relationship("Classroom")
    session = relationship("TimetableSession")
    requested_by = relationship("User", foreign_keys=[requested_by_user_id])
    approved_by = relationship("User", foreign_keys=[approved_by_user_id])


class ResourceMaintenanceWindow(TenantScopedModel):
    """Facility maintenance or closure downtime window."""

    __tablename__ = "timetable_maintenance_windows"
    __table_args__ = (
        Index("ix_tt_maint_tenant_room", "tenant_id", "room_id", "start_time", "end_time"),
    )

    room_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("academics_rooms.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=MaintenanceStatus.SCHEDULED, nullable=False
    )

    room = relationship("Classroom")


# -----------------------------------------------------------------------------
# 6. Automated Generation & Conflicts
# -----------------------------------------------------------------------------


class TimetableGenerationJob(TenantScopedModel):
    """Asynchronous constraint-based timetable generation job record."""

    __tablename__ = "timetable_generation_jobs"
    __table_args__ = (
        Index("ix_tt_gen_tenant_status", "tenant_id", "job_status"),
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
    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="SET NULL"),
        nullable=True,
    )
    department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    program_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_programs.id", ondelete="SET NULL"),
        nullable=True,
    )
    section_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_sections.id", ondelete="SET NULL"),
        nullable=True,
    )
    job_status: Mapped[str] = mapped_column(
        String(32), default=GenerationJobStatus.PENDING, nullable=False
    )
    config_parameters: Mapped[dict] = mapped_column(JSONB_COMPAT, default=dict, nullable=False)
    total_sessions_to_schedule: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    scheduled_sessions_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unscheduled_sessions_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    candidate_version_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("timetable_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_metadata: Mapped[dict] = mapped_column(JSONB_COMPAT, default=dict, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    academic_year = relationship("AcademicYear")
    semester = relationship("Semester")
    campus = relationship("Campus")
    department = relationship("Department")
    program = relationship("Program")
    section = relationship("Section")
    candidate_version = relationship("TimetableVersion")
    created_by = relationship("User")


class TimetableConflict(TenantScopedModel):
    """Detected scheduling collision, rule violation, or capacity breach."""

    __tablename__ = "timetable_conflicts"
    __table_args__ = (
        Index("ix_tt_conflicts_tenant_ver", "tenant_id", "version_id"),
        Index("ix_tt_conflicts_tenant_sev", "tenant_id", "severity"),
    )

    version_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("timetable_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    conflict_type: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(
        String(16), default=ConflictSeverity.CRITICAL, nullable=False
    )
    affected_date_or_day: Mapped[str] = mapped_column(String(32), nullable=False)
    time_window: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    rule_violated: Mapped[str] = mapped_column(String(128), nullable=False)
    session_id_1: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("timetable_sessions.id", ondelete="SET NULL"),
        nullable=True,
    )
    session_id_2: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("timetable_sessions.id", ondelete="SET NULL"),
        nullable=True,
    )
    faculty_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_faculty.id", ondelete="SET NULL"),
        nullable=True,
    )
    room_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("academics_rooms.id", ondelete="SET NULL"),
        nullable=True,
    )
    section_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_sections.id", ondelete="SET NULL"),
        nullable=True,
    )
    remediation_suggestions: Mapped[list] = mapped_column(JSONB_COMPAT, default=list, nullable=False)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    version: Mapped["TimetableVersion"] = relationship(back_populates="conflicts")
    session_1 = relationship("TimetableSession", foreign_keys=[session_id_1])
    session_2 = relationship("TimetableSession", foreign_keys=[session_id_2])
    faculty = relationship("FacultyProfile", foreign_keys=[faculty_id])
    room = relationship("Classroom", foreign_keys=[room_id])
    section = relationship("Section", foreign_keys=[section_id])
    resolved_by = relationship("User", foreign_keys=[resolved_by_user_id])


# -----------------------------------------------------------------------------
# 7. Change Requests & Publications
# -----------------------------------------------------------------------------


class TimetableChangeRequest(TenantScopedModel):
    """Audited schedule change request with impact analysis."""

    __tablename__ = "timetable_change_requests"
    __table_args__ = (
        Index("ix_tt_change_tenant_ver", "tenant_id", "version_id"),
        Index("ix_tt_change_tenant_status", "tenant_id", "status"),
    )

    version_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("timetable_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    session_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("timetable_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    change_type: Mapped[str] = mapped_column(
        String(32), default=ChangeRequestType.RESCHEDULE, nullable=False
    )
    proposed_day_of_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    proposed_start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    proposed_end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    proposed_room_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("academics_rooms.id", ondelete="SET NULL"),
        nullable=True,
    )
    proposed_faculty_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_faculty.id", ondelete="SET NULL"),
        nullable=True,
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    is_emergency: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default=ChangeRequestStatus.PENDING, nullable=False
    )
    impact_analysis: Mapped[dict] = mapped_column(JSONB_COMPAT, default=dict, nullable=False)
    requested_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    version: Mapped["TimetableVersion"] = relationship(back_populates="change_requests")
    session = relationship("TimetableSession", foreign_keys=[session_id])
    proposed_room = relationship("Classroom", foreign_keys=[proposed_room_id])
    proposed_faculty = relationship("FacultyProfile", foreign_keys=[proposed_faculty_id])
    requested_by = relationship("User", foreign_keys=[requested_by_user_id])
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_user_id])


class TimetablePublication(TenantScopedModel):
    """Publication event and notification ledger."""

    __tablename__ = "timetable_publications"
    __table_args__ = (
        Index("ix_tt_pub_tenant_ver", "tenant_id", "version_id"),
    )

    version_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("timetable_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    publication_type: Mapped[str] = mapped_column(
        String(32), default=PublicationType.INITIAL, nullable=False
    )
    published_to_students: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    published_to_faculty: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    calendar_sync_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    published_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    version = relationship("TimetableVersion")
    published_by = relationship("User", foreign_keys=[published_by_user_id])
