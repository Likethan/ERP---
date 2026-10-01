import uuid
from datetime import date, time
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TenantScopedModel


class Subject(TenantScopedModel):
    """Canonical catalog definition of an academic course/subject."""

    __tablename__ = "academics_subjects"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_subjects_tenant_code"),)

    department_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_departments.id", ondelete="RESTRICT"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)  # e.g., "CS301"
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    credits: Mapped[Decimal] = mapped_column(Numeric(3, 1), default=3.0, nullable=False)
    lecture_hours: Mapped[int] = mapped_column(default=3, nullable=False)
    tutorial_hours: Mapped[int] = mapped_column(default=0, nullable=False)
    practical_hours: Mapped[int] = mapped_column(default=0, nullable=False)
    subject_type: Mapped[str] = mapped_column(
        String(32), default="THEORY", nullable=False
    )  # THEORY, PRACTICAL, LAB, PROJECT, ELECTIVE, SEMINAR, INTERNSHIP
    description: Mapped[str | None] = mapped_column("description", Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Compatibility alias
    @property
    def title(self) -> str:
        return self.name

    @title.setter
    def title(self, value: str) -> None:
        self.name = value

    @property
    def syllabus_summary(self) -> str | None:
        return self.description

    @syllabus_summary.setter
    def syllabus_summary(self, value: str | None) -> None:
        self.description = value

    department: Mapped["Department"] = relationship()  # noqa: F821
    offerings: Mapped[list["CourseOffering"]] = relationship(back_populates="subject")
    curriculum_subjects: Mapped[list["CurriculumSubject"]] = relationship(back_populates="subject")


class CurriculumScheme(TenantScopedModel):
    """Program curriculum framework bound to a statutory regulation with versioning."""

    __tablename__ = "academics_curriculums"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "program_id",
            "regulation_id",
            "version",
            name="uq_curriculum_scheme_version",
        ),
    )

    program_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_programs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    regulation_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_regulations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column("name", String(255), nullable=False)
    version: Mapped[int] = mapped_column(default=1, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="DRAFT", nullable=False
    )  # DRAFT, REVIEW, APPROVED, PUBLISHED, RETIRED
    total_credits: Mapped[Decimal] = mapped_column(Numeric(4, 1), default=160.0, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    @property
    def title(self) -> str:
        return self.name

    @title.setter
    def title(self, value: str) -> None:
        self.name = value

    program: Mapped["Program"] = relationship()  # noqa: F821
    regulation: Mapped["Regulation"] = relationship()  # noqa: F821
    subjects: Mapped[list["CurriculumSubject"]] = relationship(
        back_populates="curriculum", cascade="all, delete-orphan"
    )


class CurriculumSubject(Base):
    """Subject mapping into a curriculum scheme for a specific semester."""

    __tablename__ = "academics_curriculum_subjects"
    __table_args__ = (
        UniqueConstraint("curriculum_id", "subject_id", "semester_number", name="uq_curr_sub_term"),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    curriculum_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("academics_curriculums.id", ondelete="CASCADE"),
        nullable=False,
    )
    subject_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("academics_subjects.id", ondelete="RESTRICT"),
        nullable=False,
    )
    semester_number: Mapped[int] = mapped_column(nullable=False)
    category: Mapped[str] = mapped_column(
        String(32), default="CORE", nullable=False
    )  # CORE, PROFESSIONAL_ELECTIVE, OPEN_ELECTIVE, LAB, PROJECT, INTERNSHIP, FOUNDATION
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    elective_group: Mapped[str | None] = mapped_column(String(64), nullable=True)
    credits: Mapped[Decimal] = mapped_column(Numeric(3, 1), default=3.0, nullable=False)
    lecture_hours: Mapped[int] = mapped_column(default=3, nullable=False)
    tutorial_hours: Mapped[int] = mapped_column(default=0, nullable=False)
    practical_hours: Mapped[int] = mapped_column(default=0, nullable=False)

    @property
    def credits_override(self) -> Decimal:
        return self.credits

    @credits_override.setter
    def credits_override(self, val: Decimal | None) -> None:
        if val is not None:
            self.credits = val

    curriculum: Mapped["CurriculumScheme"] = relationship(back_populates="subjects")
    subject: Mapped["Subject"] = relationship(back_populates="curriculum_subjects")


class Classroom(TenantScopedModel):
    """Classroom or laboratory physical facility."""

    __tablename__ = "academics_rooms"
    __table_args__ = (
        UniqueConstraint("tenant_id", "building", "room_number", name="uq_rooms_tenant_bldg_room"),
    )

    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="SET NULL"),
        nullable=True,
    )
    building: Mapped[str] = mapped_column(String(128), nullable=False)
    room_number: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g. "LH-101"
    capacity: Mapped[int] = mapped_column(default=60, nullable=False)
    room_type: Mapped[str] = mapped_column(
        String(32), default="CLASSROOM", nullable=False
    )  # CLASSROOM, LECTURE_HALL, COMPUTER_LAB, SCIENCE_LAB, SEMINAR_HALL
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    campus: Mapped["Campus | None"] = relationship()  # noqa: F821


class TimeSlot(TenantScopedModel):
    """Institutional standardized class period / time slot."""

    __tablename__ = "academics_time_slots"
    __table_args__ = (
        UniqueConstraint("tenant_id", "slot_number", name="uq_time_slots_tenant_number"),
    )

    name: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g. "Period 1"
    slot_number: Mapped[int] = mapped_column(nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    slot_type: Mapped[str] = mapped_column(
        String(32), default="LECTURE", nullable=False
    )  # LECTURE, LAB, BREAK
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class CourseOffering(TenantScopedModel):
    """Classroom delivery of a subject in a specific term, department, and section."""

    __tablename__ = "academics_course_offerings"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "subject_id",
            "academic_year_id",
            "semester_id",
            "section_id",
            name="uq_course_offering_composite",
        ),
    )

    subject_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("academics_subjects.id", ondelete="RESTRICT"),
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
    section_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_sections.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32), default="PLANNED", nullable=False
    )  # PLANNED, OPEN, ACTIVE, COMPLETED, CANCELLED
    max_capacity: Mapped[int] = mapped_column(default=60, nullable=False)

    subject: Mapped["Subject"] = relationship(back_populates="offerings")
    academic_year: Mapped["AcademicYear"] = relationship()  # noqa: F821
    semester: Mapped["Semester"] = relationship()  # noqa: F821
    section: Mapped["Section"] = relationship()  # noqa: F821

    faculty_assignments: Mapped[list["CourseFacultyAssignment"]] = relationship(
        back_populates="course_offering", cascade="all, delete-orphan"
    )
    enrollments: Mapped[list["CourseEnrollment"]] = relationship(
        back_populates="course_offering", cascade="all, delete-orphan"
    )
    timetable_entries: Mapped[list["TimetableEntry"]] = relationship(
        back_populates="course_offering", cascade="all, delete-orphan"
    )


class CourseFacultyAssignment(TenantScopedModel):
    """Faculty instructional assignment to a course offering."""

    __tablename__ = "academics_course_faculty"
    __table_args__ = (
        UniqueConstraint(
            "course_offering_id", "faculty_id", name="uq_course_faculty_assignment"
        ),
    )

    course_offering_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("academics_course_offerings.id", ondelete="CASCADE"),
        nullable=False,
    )
    faculty_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_faculty.id", ondelete="RESTRICT"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(32), default="PRIMARY", nullable=False
    )  # PRIMARY, CO_FACULTY, LAB_INSTRUCTOR, TEACHING_ASSISTANT
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    course_offering: Mapped["CourseOffering"] = relationship(back_populates="faculty_assignments")
    faculty: Mapped["FacultyProfile"] = relationship()  # noqa: F821


class CourseEnrollment(TenantScopedModel):
    """Student registration in a course offering."""

    __tablename__ = "academics_course_enrollments"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "student_id", "course_offering_id", name="uq_course_enrollments_student"
        ),
    )

    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    course_offering_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("academics_course_offerings.id", ondelete="RESTRICT"),
        nullable=False,
    )
    enrollment_type: Mapped[str] = mapped_column(
        String(32), default="REGULAR", nullable=False
    )  # REGULAR, ELECTIVE, REPEAT, AUDIT
    status: Mapped[str] = mapped_column(
        String(32), default="ENROLLED", nullable=False
    )  # ENROLLED, DROPPED, WITHDRAWN, COMPLETED, FAILED
    enrollment_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    dropped_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    student: Mapped["StudentProfile"] = relationship()  # noqa: F821
    course_offering: Mapped["CourseOffering"] = relationship(back_populates="enrollments")


class TimetableEntry(TenantScopedModel):
    """Master schedule entry allocating a course offering, faculty, room, and time slot."""

    __tablename__ = "academics_timetable_slots"

    course_offering_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("academics_course_offerings.id", ondelete="CASCADE"),
        nullable=False,
    )
    section_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_sections.id", ondelete="RESTRICT"),
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
    faculty_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_faculty.id", ondelete="RESTRICT"),
        nullable=True,
    )
    room_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("academics_rooms.id", ondelete="SET NULL"),
        nullable=True,
    )
    time_slot_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("academics_time_slots.id", ondelete="RESTRICT"),
        nullable=False,
    )
    day_of_week: Mapped[int] = mapped_column(nullable=False)  # 1 = Monday, ..., 7 = Sunday
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    course_offering: Mapped["CourseOffering"] = relationship(back_populates="timetable_entries")
    section: Mapped["Section"] = relationship()  # noqa: F821
    faculty: Mapped["FacultyProfile | None"] = relationship()  # noqa: F821
    room: Mapped["Classroom | None"] = relationship()
    time_slot: Mapped["TimeSlot"] = relationship()


# Backward compatibility alias
TimetableSlot = TimetableEntry
