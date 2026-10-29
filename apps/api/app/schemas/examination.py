"""Examination and Assessment Engine Pydantic Schemas.

Type-safe request and response envelopes matching TypeScript models for
assessments, weightage, exam schedules, conflicts, student eligibility,
marks rosters, grade scales, and published results.
"""

from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# -----------------------------------------------------------------------------
# GRADE SCALE SCHEMAS
# -----------------------------------------------------------------------------
class GradeScaleItemCreate(BaseModel):
    grade_letter: str = Field(..., max_length=8)
    grade_point: Decimal = Field(..., ge=0, le=10)
    min_mark_percent: Decimal = Field(..., ge=0, le=100)
    max_mark_percent: Decimal = Field(..., ge=0, le=100)
    is_passing: bool = True
    description: str | None = None


class GradeScaleItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    grade_scale_id: UUID
    grade_letter: str
    grade_point: Decimal
    min_mark_percent: Decimal
    max_mark_percent: Decimal
    is_passing: bool
    description: str | None = None


class GradeScaleCreateRequest(BaseModel):
    name: str = Field(..., max_length=64)
    description: str | None = None
    is_default: bool = False
    items: list[GradeScaleItemCreate] = Field(default_factory=list)


class GradeScaleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    description: str | None = None
    is_default: bool
    items: list[GradeScaleItemResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


# -----------------------------------------------------------------------------
# EXAMINATION TERM / CYCLE SCHEMAS
# -----------------------------------------------------------------------------
class ExamTermCreateRequest(BaseModel):
    academic_year_id: UUID
    semester_id: UUID
    name: str = Field(..., max_length=128)
    exam_type: str = Field("END_SEMESTER", max_length=32)
    start_date: date
    end_date: date
    status: str = Field("DRAFT", max_length=32)


class ExamTermResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    academic_year_id: UUID
    academic_year_name: str | None = None
    semester_id: UUID
    semester_name: str | None = None
    name: str
    exam_type: str
    start_date: date
    end_date: date
    status: str
    created_at: datetime
    updated_at: datetime


# -----------------------------------------------------------------------------
# ASSESSMENT SCHEMAS
# -----------------------------------------------------------------------------
class AssessmentCreateRequest(BaseModel):
    course_offering_id: UUID
    exam_term_id: UUID | None = None
    title: str = Field(..., max_length=128)
    assessment_type: str = Field("INTERNAL", max_length=32)
    sequence: int = Field(1, ge=1, le=50)
    max_marks: Decimal = Field(Decimal("100.00"), ge=1, le=1000)
    passing_marks: Decimal = Field(Decimal("40.00"), ge=0, le=1000)
    weightage_percent: Decimal = Field(..., ge=0, le=100)
    description: str | None = None
    status: str = Field("CONFIGURED", max_length=32)


class AssessmentUpdateRequest(BaseModel):
    title: str | None = Field(None, max_length=128)
    assessment_type: str | None = Field(None, max_length=32)
    sequence: int | None = Field(None, ge=1, le=50)
    max_marks: Decimal | None = Field(None, ge=1, le=1000)
    passing_marks: Decimal | None = Field(None, ge=0, le=1000)
    weightage_percent: Decimal | None = Field(None, ge=0, le=100)
    description: str | None = None
    status: str | None = Field(None, max_length=32)


class AssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    course_offering_id: UUID
    course_code: str | None = None
    course_name: str | None = None
    section_name: str | None = None
    exam_term_id: UUID | None = None
    exam_term_name: str | None = None
    title: str
    assessment_type: str
    sequence: int
    max_marks: Decimal
    passing_marks: Decimal
    weightage_percent: Decimal
    description: str | None = None
    status: str
    is_finalized: bool
    finalized_at: datetime | None = None
    total_enrolled: int = 0
    total_marks_entered: int = 0
    created_at: datetime
    updated_at: datetime


class CourseAssessmentStructureResponse(BaseModel):
    course_offering_id: UUID
    course_code: str
    course_name: str
    total_weightage_percent: Decimal
    is_weightage_valid: bool
    assessments: list[AssessmentResponse] = Field(default_factory=list)


# -----------------------------------------------------------------------------
# EXAM SCHEDULE SCHEMAS & CONFLICTS
# -----------------------------------------------------------------------------
class ExamScheduleCreateRequest(BaseModel):
    assessment_id: UUID
    exam_date: date
    start_time: time
    end_time: time
    room_id: UUID | None = None
    room_identifier: str = Field(..., max_length=64)
    invigilator_faculty_id: UUID | None = None
    status: str = Field("SCHEDULED", max_length=32)


class ExamScheduleUpdateRequest(BaseModel):
    exam_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    room_id: UUID | None = None
    room_identifier: str | None = Field(None, max_length=64)
    invigilator_faculty_id: UUID | None = None
    status: str | None = Field(None, max_length=32)


class ExamScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    assessment_id: UUID
    assessment_title: str | None = None
    course_offering_id: UUID
    course_code: str | None = None
    course_name: str | None = None
    section_name: str | None = None
    exam_term_id: UUID | None = None
    exam_date: date
    start_time: str
    end_time: str
    room_id: UUID | None = None
    room_identifier: str
    invigilator_faculty_id: UUID | None = None
    invigilator_name: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime


class ExamConflictCheckResponse(BaseModel):
    has_conflict: bool
    conflict_type: str | None = None  # ROOM_CONFLICT, STUDENT_CONFLICT, INVIGILATOR_CONFLICT
    conflicting_schedules: list[ExamScheduleResponse] = Field(default_factory=list)
    message: str | None = None


# -----------------------------------------------------------------------------
# EXAM ELIGIBILITY SCHEMAS
# -----------------------------------------------------------------------------
class ExamEligibilityEvaluateRequest(BaseModel):
    course_offering_id: UUID
    exam_term_id: UUID
    minimum_attendance_threshold: Decimal | None = None  # If omitted, resolved via Step 6 policy


class ExamEligibilityOverrideRequest(BaseModel):
    eligibility_status: str = Field(..., max_length=32)  # ELIGIBLE, CONDONATION_REQUIRED, etc.
    override_reason: str = Field(..., min_length=5)


class ExamEligibilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    exam_term_id: UUID
    course_offering_id: UUID
    course_code: str | None = None
    course_name: str | None = None
    student_id: UUID
    student_name: str | None = None
    student_roll_number: str | None = None
    student_admission_number: str | None = None
    eligibility_status: str
    attendance_percentage: Decimal | None = None
    minimum_required_percentage: Decimal | None = None
    reason: str | None = None
    is_overridden: bool
    override_reason: str | None = None
    evaluated_at: datetime


# -----------------------------------------------------------------------------
# MARKS ENTRY & ROSTER SCHEMAS
# -----------------------------------------------------------------------------
class StudentMarkItem(BaseModel):
    student_id: UUID
    marks_obtained: Decimal | None = None
    status: str = Field("PRESENT", max_length=32)  # PRESENT, ABSENT, NOT_ATTEMPTED, WITHHELD, MALPRACTICE
    remarks: str | None = None


class AssessmentBulkMarksSubmitRequest(BaseModel):
    marks: list[StudentMarkItem]
    finalize: bool = False


class StudentMarkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    assessment_id: UUID
    student_id: UUID
    student_name: str | None = None
    student_roll_number: str | None = None
    student_admission_number: str | None = None
    marks_obtained: Decimal | None = None
    status: str
    is_absent: bool
    moderated_marks: Decimal | None = None
    remarks: str | None = None
    is_finalized: bool
    finalized_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class AssessmentMarksRosterResponse(BaseModel):
    assessment: AssessmentResponse
    roster: list[StudentMarkResponse] = Field(default_factory=list)
    total_students: int = 0
    total_entered: int = 0
    total_absent: int = 0
    average_marks: Decimal | None = None
    highest_marks: Decimal | None = None
    lowest_marks: Decimal | None = None


# -----------------------------------------------------------------------------
# MARK CORRECTION SCHEMAS
# -----------------------------------------------------------------------------
class MarkCorrectionCreateRequest(BaseModel):
    mark_id: UUID
    new_marks: Decimal | None = None
    new_status: str = Field("PRESENT", max_length=32)
    reason: str = Field(..., min_length=5)


class MarkCorrectionReviewRequest(BaseModel):
    approval_notes: str | None = None


class MarkCorrectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    mark_id: UUID
    assessment_id: UUID
    assessment_title: str | None = None
    student_id: UUID
    student_name: str | None = None
    student_roll_number: str | None = None
    old_marks: Decimal | None = None
    new_marks: Decimal | None = None
    old_status: str
    new_status: str
    reason: str
    requested_by_user_id: UUID
    requested_by_name: str | None = None
    approved_by_user_id: UUID | None = None
    approved_by_name: str | None = None
    approval_status: str
    approval_notes: str | None = None
    reviewed_at: datetime | None = None
    created_at: datetime


# -----------------------------------------------------------------------------
# RESULTS & TRANSCRIPTS SCHEMAS
# -----------------------------------------------------------------------------
class SemesterResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    student_id: UUID
    student_name: str | None = None
    student_roll_number: str | None = None
    student_admission_number: str | None = None
    course_offering_id: UUID
    course_code: str | None = None
    course_name: str | None = None
    credits: Decimal | None = None
    exam_term_id: UUID
    exam_term_name: str | None = None
    internal_marks: Decimal
    external_marks: Decimal
    total_marks: Decimal
    grade_letter: str
    grade_point: Decimal
    credits_earned: Decimal
    result_status: str  # PASS, FAIL, ABSENT, WITHHELD, MALPRACTICE
    publication_status: str  # DRAFT, UNDER_REVIEW, FINALIZED, PUBLISHED
    finalized_at: datetime | None = None
    published_at: datetime | None = None
    created_at: datetime


class StudentSemesterTranscript(BaseModel):
    student_id: UUID
    student_name: str
    student_roll_number: str | None = None
    student_admission_number: str
    program_name: str | None = None
    semester_name: str | None = None
    exam_term_id: UUID
    exam_term_name: str
    results: list[SemesterResultResponse] = Field(default_factory=list)
    total_credits_registered: Decimal
    total_credits_earned: Decimal
    semester_gpa: Decimal | None = None
    overall_status: str  # PASS, PROMOTED, DETAINED


class ResultFinalizeRequest(BaseModel):
    course_offering_id: UUID
    exam_term_id: UUID
    grade_scale_id: UUID | None = None  # If omitted, default institutional grade scale used


class ResultPublishRequest(BaseModel):
    exam_term_id: UUID
    course_offering_id: UUID | None = None  # If omitted, publishes all finalized results for exam term


# -----------------------------------------------------------------------------
# EXAMINATION DASHBOARD SCHEMAS
# -----------------------------------------------------------------------------
class ExaminationDashboardResponse(BaseModel):
    active_terms_count: int = 0
    total_assessments_configured: int = 0
    assessments_pending_marks: int = 0
    assessments_finalized: int = 0
    upcoming_exam_schedules_count: int = 0
    results_awaiting_publication_count: int = 0
    total_published_results_count: int = 0
    pending_mark_corrections_count: int = 0
    recent_assessments: list[AssessmentResponse] = Field(default_factory=list)
    upcoming_schedules: list[ExamScheduleResponse] = Field(default_factory=list)
