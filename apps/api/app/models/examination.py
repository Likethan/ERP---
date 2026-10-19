"""Examination and Assessment Engine Models.

Authoritative domain models for examination cycles, course assessments, weightage,
scheduling, conflict detection, exam eligibility snapshots, bulk marks,
grade scales, and published results.
"""

from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
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
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, BaseModel, TenantScopedModel


class GradeScale(TenantScopedModel):
    """Institutional grading scale framework (e.g. 10-Point UGC Scale)."""

    __tablename__ = "examination_grade_scales"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_grade_scales_tenant_name"),
        Index("ix_grade_scales_tenant_active", "tenant_id", "is_default"),
    )

    name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    items: Mapped[list["GradeScaleItem"]] = relationship(
        back_populates="grade_scale", cascade="all, delete-orphan", order_by="desc(GradeScaleItem.min_mark_percent)"
    )


class GradeScaleItem(BaseModel):
    """Specific grade band definition within a grade scale."""

    __tablename__ = "examination_grade_items"
    __table_args__ = (
        UniqueConstraint("grade_scale_id", "grade_letter", name="uq_grade_scale_item_letter"),
    )

    grade_scale_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("examination_grade_scales.id", ondelete="CASCADE"),

        nullable=False,
    )
    grade_letter: Mapped[str] = mapped_column(String(8), nullable=False)  # O, A+, A, B+, B, C, F
    grade_point: Mapped[Decimal] = mapped_column(Numeric(3, 1), nullable=False)  # 10.0, 9.0, etc.
    min_mark_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    max_mark_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    is_passing: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(64), nullable=True)  # Outstanding, etc.

    grade_scale: Mapped["GradeScale"] = relationship(back_populates="items")


class ExamTerm(TenantScopedModel):
    """Formal examination cycle (e.g., End Semester Nov/Dec 2026)."""

    __tablename__ = "examination_terms"
    __table_args__ = (
        UniqueConstraint("tenant_id", "academic_year_id", "name", name="uq_exam_terms_year_name"),
        Index("ix_exam_terms_tenant_status", "tenant_id", "status"),
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
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    exam_type: Mapped[str] = mapped_column(
        String(32), default="END_SEMESTER", nullable=False
    )  # INTERNAL_ASSESSMENT, END_SEMESTER, SUPPLEMENTARY, LAB_EXAM, MODEL_EXAM
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="DRAFT", nullable=False
    )  # DRAFT, SCHEDULED, IN_PROGRESS, EVALUATION, COMPLETED, PUBLISHED

    academic_year = relationship("AcademicYear")
    semester = relationship("Semester")
    assessments: Mapped[list["Assessment"]] = relationship(back_populates="exam_term")
    schedules: Mapped[list["ExamSchedule"]] = relationship(back_populates="exam_term")


class Assessment(TenantScopedModel):
    """Evaluation component within a course offering (CIA 1, Final Exam, Lab)."""

    __tablename__ = "examination_assessments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "course_offering_id", "title", name="uq_assessment_course_title"),
        Index("ix_assessments_tenant_course", "tenant_id", "course_offering_id"),
        Index("ix_assessments_tenant_status", "tenant_id", "status"),
    )

    course_offering_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("academics_course_offerings.id", ondelete="RESTRICT"),
        nullable=False,
    )
    exam_term_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("examination_terms.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    assessment_type: Mapped[str] = mapped_column(
        String(32), default="INTERNAL", nullable=False
    )  # INTERNAL, ASSIGNMENT, QUIZ, LAB, PRACTICAL, MODEL_EXAM, MIDTERM, END_SEMESTER, PROJECT, VIVA
    sequence: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_marks: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=100.00, nullable=False)
    passing_marks: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=40.00, nullable=False)
    weightage_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=20.00, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default="CONFIGURED", nullable=False
    )  # DRAFT, CONFIGURED, OPEN, MARKS_ENTRY, UNDER_REVIEW, FINALIZED, PUBLISHED
    is_finalized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finalized_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    course_offering = relationship("CourseOffering")
    exam_term: Mapped["ExamTerm | None"] = relationship(back_populates="assessments")
    marks: Mapped[list["StudentAssessmentMark"]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan"
    )
    schedule: Mapped["ExamSchedule | None"] = relationship(
        back_populates="assessment", uselist=False, cascade="all, delete-orphan"
    )


class ExamSchedule(TenantScopedModel):
    """Scheduled examination paper event with room and invigilator assignments."""

    __tablename__ = "examination_schedules"
    __table_args__ = (
        Index("ix_schedules_tenant_date", "tenant_id", "exam_date"),
        Index("ix_schedules_tenant_room_date", "tenant_id", "room_identifier", "exam_date"),
        Index("ix_schedules_tenant_course_date", "tenant_id", "course_offering_id", "exam_date"),
    )

    assessment_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("examination_assessments.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    course_offering_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("academics_course_offerings.id", ondelete="RESTRICT"),
        nullable=False,
    )
    exam_term_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("examination_terms.id", ondelete="SET NULL"),
        nullable=True,
    )
    exam_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    room_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("academics_rooms.id", ondelete="SET NULL"),
        nullable=True,
    )
    room_identifier: Mapped[str] = mapped_column(String(64), nullable=False)
    invigilator_faculty_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_faculty.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32), default="SCHEDULED", nullable=False
    )  # SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED

    assessment: Mapped["Assessment"] = relationship(back_populates="schedule")
    course_offering = relationship("CourseOffering")
    exam_term: Mapped["ExamTerm | None"] = relationship(back_populates="schedules")
    invigilator = relationship("FacultyProfile")
    room = relationship("Classroom")


class ExamEligibility(TenantScopedModel):
    """Snapshot evaluation of student eligibility for an examination cycle."""

    __tablename__ = "examination_eligibility"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "exam_term_id",
            "course_offering_id",
            "student_id",
            name="uq_exam_eligibility_student",
        ),
        Index("ix_eligibility_tenant_student", "tenant_id", "student_id"),
        Index("ix_eligibility_tenant_course", "tenant_id", "course_offering_id"),
    )

    exam_term_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("examination_terms.id", ondelete="RESTRICT"),
        nullable=False,
    )
    course_offering_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("academics_course_offerings.id", ondelete="RESTRICT"),
        nullable=False,
    )
    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    eligibility_status: Mapped[str] = mapped_column(
        String(32), default="ELIGIBLE", nullable=False
    )  # ELIGIBLE, CONDONATION_REQUIRED, DETAINED_ATTENDANCE, DETAINED_ACADEMIC, DISBARRED
    attendance_percentage: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    minimum_required_percentage: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_overridden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    override_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    overridden_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    evaluated_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    student = relationship("StudentProfile")
    course_offering = relationship("CourseOffering")
    exam_term = relationship("ExamTerm")


class StudentAssessmentMark(TenantScopedModel):
    """Raw scored marks for an individual student in an assessment."""

    __tablename__ = "examination_student_marks"
    __table_args__ = (
        UniqueConstraint("tenant_id", "assessment_id", "student_id", name="uq_assessment_student_mark"),
        Index("ix_marks_tenant_assessment", "tenant_id", "assessment_id"),
        Index("ix_marks_tenant_student", "tenant_id", "student_id"),
        Index("idx_perf_marks_tenant_assess_status", "tenant_id", "assessment_id", "status"),
    )

    assessment_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("examination_assessments.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    marks_obtained: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default="PRESENT", nullable=False
    )  # PRESENT, ABSENT, NOT_ATTEMPTED, WITHHELD, MALPRACTICE
    is_absent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    evaluated_by_faculty_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_faculty.id", ondelete="SET NULL"),
        nullable=True,
    )
    moderated_marks: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_finalized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    assessment: Mapped["Assessment"] = relationship(back_populates="marks")
    student = relationship("StudentProfile")
    evaluator = relationship("FacultyProfile")


class MarkCorrectionRequest(TenantScopedModel):
    """Formal audit-tracked correction request for finalized assessment marks."""

    __tablename__ = "examination_mark_corrections"
    __table_args__ = (
        Index("ix_mark_corrections_tenant_status", "tenant_id", "approval_status"),
        Index("ix_mark_corrections_tenant_student", "tenant_id", "student_id"),
    )

    mark_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("examination_student_marks.id", ondelete="CASCADE"),
        nullable=False,
    )
    assessment_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("examination_assessments.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    old_marks: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    new_marks: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    old_status: Mapped[str] = mapped_column(String(32), nullable=False)
    new_status: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    requested_by_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    approved_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approval_status: Mapped[str] = mapped_column(
        String(32), default="PENDING", nullable=False
    )  # PENDING, APPROVED, REJECTED
    approval_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    mark = relationship("StudentAssessmentMark")
    student = relationship("StudentProfile")
    assessment = relationship("Assessment")
    requested_by = relationship("User", foreign_keys=[requested_by_user_id])
    approved_by = relationship("User", foreign_keys=[approved_by_user_id])


class SemesterExamResult(TenantScopedModel):
    """Official published semester transcript result per student per course offering."""

    __tablename__ = "examination_results"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "student_id",
            "course_offering_id",
            "exam_term_id",
            name="uq_exam_results_composite",
        ),
        Index("ix_results_tenant_student", "tenant_id", "student_id"),
        Index("ix_results_tenant_course", "tenant_id", "course_offering_id"),
        Index("ix_results_tenant_pub_status", "tenant_id", "publication_status"),
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
    exam_term_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("examination_terms.id", ondelete="RESTRICT"),
        nullable=False,
    )
    internal_marks: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0.00, nullable=False)
    external_marks: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0.00, nullable=False)
    total_marks: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0.00, nullable=False)
    grade_letter: Mapped[str] = mapped_column(String(8), nullable=False)
    grade_point: Mapped[Decimal] = mapped_column(Numeric(3, 1), nullable=False)
    credits_earned: Mapped[Decimal] = mapped_column(Numeric(3, 1), nullable=False)
    result_status: Mapped[str] = mapped_column(
        String(32), default="PASS", nullable=False
    )  # PASS, FAIL, ABSENT, WITHHELD, MALPRACTICE, INCOMPLETE
    publication_status: Mapped[str] = mapped_column(
        String(32), default="DRAFT", nullable=False
    )  # DRAFT, UNDER_REVIEW, FINALIZED, PUBLISHED
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finalized_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    student = relationship("StudentProfile")
    course_offering = relationship("CourseOffering")
    exam_term = relationship("ExamTerm")


class ResultCorrectionAudit(TenantScopedModel):
    """Audit-tracked correction record for post-publication grade adjustments."""

    __tablename__ = "examination_corrections"
    __table_args__ = (
        Index("ix_res_corr_tenant_result", "tenant_id", "result_id"),
    )

    result_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("examination_results.id", ondelete="RESTRICT"),
        nullable=False,
    )
    old_grade_letter: Mapped[str] = mapped_column(String(8), nullable=False)
    new_grade_letter: Mapped[str] = mapped_column(String(8), nullable=False)
    old_total_marks: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    new_total_marks: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    authorized_by_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    result: Mapped["SemesterExamResult"] = relationship()
    authorized_by = relationship("User")
