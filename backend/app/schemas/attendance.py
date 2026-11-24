"""Pydantic schemas for the Attendance Management Engine."""

from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


# -----------------------------------------------------------------------------
# 1. ATTENDANCE POLICY SCHEMAS
# -----------------------------------------------------------------------------
class AttendancePolicyCreateRequest(BaseModel):
    name: str = Field(default="Institutional Standard Policy", max_length=128)
    department_id: UUID | None = None
    program_id: UUID | None = None
    academic_year_id: UUID | None = None
    semester_id: UUID | None = None
    course_offering_id: UUID | None = None

    minimum_percentage: Decimal = Field(default=Decimal("75.00"), ge=0, le=100)
    warning_threshold_percentage: Decimal = Field(default=Decimal("80.00"), ge=0, le=100)
    critical_threshold_percentage: Decimal = Field(default=Decimal("65.00"), ge=0, le=100)
    condonation_percentage: Decimal = Field(default=Decimal("65.00"), ge=0, le=100)

    late_grace_minutes: int = Field(default=10, ge=0, le=120)
    late_weight: Decimal = Field(default=Decimal("1.00"), ge=0, le=1)
    excused_counts_as_present: bool = True
    on_leave_counts_as_present: bool = False
    exclude_excused_from_total: bool = False

    effective_from: date | None = None
    effective_to: date | None = None
    status: str = Field(default="ACTIVE")


class AttendancePolicyUpdateRequest(BaseModel):
    name: str | None = Field(default=None, max_length=128)
    minimum_percentage: Decimal | None = Field(default=None, ge=0, le=100)
    warning_threshold_percentage: Decimal | None = Field(default=None, ge=0, le=100)
    critical_threshold_percentage: Decimal | None = Field(default=None, ge=0, le=100)
    condonation_percentage: Decimal | None = Field(default=None, ge=0, le=100)

    late_grace_minutes: int | None = Field(default=None, ge=0, le=120)
    late_weight: Decimal | None = Field(default=None, ge=0, le=1)
    excused_counts_as_present: bool | None = None
    on_leave_counts_as_present: bool | None = None
    exclude_excused_from_total: bool | None = None

    effective_from: date | None = None
    effective_to: date | None = None
    status: str | None = None
    is_active: bool | None = None


class AttendancePolicyResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    department_id: UUID | None
    program_id: UUID | None
    academic_year_id: UUID | None
    semester_id: UUID | None
    course_offering_id: UUID | None

    minimum_percentage: Decimal
    warning_threshold_percentage: Decimal
    critical_threshold_percentage: Decimal
    condonation_percentage: Decimal

    late_grace_minutes: int
    late_weight: Decimal
    excused_counts_as_present: bool
    on_leave_counts_as_present: bool
    exclude_excused_from_total: bool

    effective_from: date | None
    effective_to: date | None
    status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------------------------
# 2. ATTENDANCE SESSION SCHEMAS
# -----------------------------------------------------------------------------
class AttendanceSessionCreateRequest(BaseModel):
    course_offering_id: UUID
    section_id: UUID
    faculty_id: UUID
    academic_year_id: UUID | None = None
    semester_id: UUID | None = None
    session_date: date
    period_number: int = Field(ge=1, le=20)
    session_type: str = Field(default="LECTURE")  # LECTURE, LAB, TUTORIAL, REMEDIAL
    timetable_slot_id: UUID | None = None
    room_id: UUID | None = None
    time_slot_id: UUID | None = None
    start_time: time | None = None
    end_time: time | None = None
    topic: str | None = Field(default=None, max_length=255)


class AttendanceSessionFromTimetableRequest(BaseModel):
    timetable_entry_id: UUID
    session_date: date
    topic: str | None = Field(default=None, max_length=255)


class AttendanceSessionUpdateRequest(BaseModel):
    topic: str | None = Field(default=None, max_length=255)
    session_type: str | None = None
    room_id: UUID | None = None
    faculty_id: UUID | None = None


class AttendanceSessionResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    course_offering_id: UUID
    course_code: str | None = None
    course_name: str | None = None
    section_id: UUID
    section_name: str | None = None
    faculty_id: UUID
    faculty_name: str | None = None
    academic_year_id: UUID
    semester_id: UUID
    session_date: date
    period_number: int
    session_type: str
    status: str  # SCHEDULED, OPEN, MARKED, LOCKED, CANCELLED
    topic: str | None = None
    start_time: time | None = None
    end_time: time | None = None
    room_id: UUID | None = None
    room_name: str | None = None
    timetable_slot_id: UUID | None = None

    total_enrolled: int = 0
    total_present: int = 0
    total_absent: int = 0
    total_late: int = 0
    total_excused: int = 0
    total_on_leave: int = 0

    submitted_at: datetime | None = None
    locked_at: datetime | None = None
    locked_by_user_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------------------------
# 3. ATTENDANCE RECORD SCHEMAS
# -----------------------------------------------------------------------------
class AttendanceRecordResponse(BaseModel):
    id: UUID
    session_id: UUID
    student_id: UUID
    student_roll_number: str | None = None
    student_admission_number: str | None = None
    student_name: str | None = None
    status: str  # PRESENT, ABSENT, LATE, EXCUSED, ON_LEAVE
    remarks: str | None = None
    recorded_by_user_id: UUID
    has_approved_leave: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AttendanceRecordBulkItem(BaseModel):
    student_id: UUID
    status: str = Field(default="PRESENT")  # PRESENT, ABSENT, LATE, EXCUSED, ON_LEAVE
    remarks: str | None = Field(default=None, max_length=255)


class AttendanceRecordBulkSubmitRequest(BaseModel):
    records: list[AttendanceRecordBulkItem]
    auto_lock: bool = False


class AttendanceRecordUpdateRequest(BaseModel):
    status: str
    remarks: str | None = Field(default=None, max_length=255)


class AttendanceRosterStudentItem(BaseModel):
    student_id: UUID
    roll_number: str | None = None
    admission_number: str
    student_name: str
    enrollment_status: str
    current_status: str | None = None  # Existing marked status, or default
    remarks: str | None = None
    has_approved_leave: bool = False
    leave_reason: str | None = None


class AttendanceSessionDetailResponse(BaseModel):
    session: AttendanceSessionResponse
    roster: list[AttendanceRosterStudentItem]
    records: list[AttendanceRecordResponse]


# -----------------------------------------------------------------------------
# 4. STUDENT & COURSE ATTENDANCE SUMMARY SCHEMAS
# -----------------------------------------------------------------------------
class StudentCourseAttendanceSummary(BaseModel):
    course_offering_id: UUID
    subject_code: str
    subject_name: str
    credits: Decimal | float
    faculty_name: str | None = None
    total_conducted: int
    attended_sessions: Decimal | float
    present_count: int
    absent_count: int
    late_count: int
    excused_count: int
    leave_count: int
    attendance_percentage: Decimal | float
    minimum_required_percentage: Decimal | float
    status: str  # NORMAL, WARNING, CRITICAL


class StudentOverallAttendanceSummary(BaseModel):
    student_id: UUID
    student_name: str
    admission_number: str
    roll_number: str | None = None
    program_name: str | None = None
    section_name: str | None = None
    total_conducted_sessions: int
    total_attended_sessions: Decimal | float
    overall_percentage: Decimal | float
    minimum_required_percentage: Decimal | float
    status: str  # NORMAL, WARNING, CRITICAL
    courses: list[StudentCourseAttendanceSummary]
    recent_records: list[AttendanceRecordResponse]
    alerts: list["AttendanceAlertResponse"] = Field(default_factory=list)


class CourseOfferingStudentAttendanceItem(BaseModel):
    student_id: UUID
    student_name: str
    admission_number: str
    roll_number: str | None = None
    total_conducted: int
    attended_sessions: Decimal | float
    present_count: int
    absent_count: int
    late_count: int
    excused_count: int
    leave_count: int
    attendance_percentage: Decimal | float
    status: str  # NORMAL, WARNING, CRITICAL


class CourseOfferingAttendanceSummary(BaseModel):
    course_offering_id: UUID
    subject_code: str
    subject_name: str
    section_name: str
    faculty_name: str | None = None
    total_sessions_conducted: int
    total_enrolled_students: int
    average_attendance_percentage: Decimal | float
    students_below_minimum: int
    minimum_percentage: Decimal | float
    students: list[CourseOfferingStudentAttendanceItem]


# -----------------------------------------------------------------------------
# 5. STUDENT LEAVE SCHEMAS
# -----------------------------------------------------------------------------
class StudentLeaveCreateRequest(BaseModel):
    student_id: UUID
    leave_type: str = Field(default="CASUAL")  # MEDICAL, CASUAL, ON_DUTY, SPORTS, OTHER
    start_date: date
    end_date: date
    reason: str = Field(min_length=3, max_length=1000)
    proof_storage_key: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def validate_dates(self) -> "StudentLeaveCreateRequest":
        if self.start_date > self.end_date:
            raise ValueError("Start date must be earlier than or equal to end date.")
        return self


class StudentLeaveReviewRequest(BaseModel):
    review_notes: str | None = Field(default=None, max_length=1000)


class StudentLeaveResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    student_id: UUID
    student_name: str | None = None
    student_roll_number: str | None = None
    student_admission_number: str | None = None
    leave_type: str
    start_date: date
    end_date: date
    days_count: int
    reason: str
    proof_storage_key: str | None = None
    status: str  # PENDING, APPROVED, REJECTED, CANCELLED
    reviewed_by_user_id: UUID | None = None
    reviewed_by_name: str | None = None
    reviewed_at: datetime | None = None
    review_notes: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------------------------
# 6. ATTENDANCE CORRECTION SCHEMAS
# -----------------------------------------------------------------------------
class AttendanceCorrectionCreateRequest(BaseModel):
    attendance_record_id: UUID
    requested_status: str  # PRESENT, ABSENT, LATE, EXCUSED, ON_LEAVE
    reason: str = Field(min_length=3, max_length=1000)


class AttendanceCorrectionReviewRequest(BaseModel):
    approval_notes: str | None = Field(default=None, max_length=1000)


class AttendanceCorrectionResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    attendance_record_id: UUID
    session_id: UUID
    session_date: date
    course_code: str | None = None
    course_name: str | None = None
    student_id: UUID
    student_name: str | None = None
    student_roll_number: str | None = None
    previous_status: str
    requested_status: str
    reason: str
    requested_by_user_id: UUID
    requested_by_name: str | None = None
    approved_by_user_id: UUID | None = None
    approved_by_name: str | None = None
    approval_status: str  # PENDING, APPROVED, REJECTED
    approval_notes: str | None = None
    reviewed_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------------------------
# 7. ATTENDANCE ALERT & DASHBOARD SCHEMAS
# -----------------------------------------------------------------------------
class AttendanceAlertResponse(BaseModel):
    id: UUID
    student_id: UUID
    student_name: str | None = None
    student_roll_number: str | None = None
    course_offering_id: UUID | None = None
    course_name: str | None = None
    alert_type: str
    severity: str  # INFO, WARNING, CRITICAL
    attendance_percentage: Decimal | None = None
    threshold_percentage: Decimal | None = None
    message: str
    is_resolved: bool
    resolved_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LowAttendanceStudentItem(BaseModel):
    student_id: UUID
    student_name: str
    admission_number: str
    roll_number: str | None = None
    program_name: str | None = None
    section_name: str | None = None
    course_offering_id: UUID
    course_code: str
    course_name: str
    total_conducted: int
    attended_sessions: Decimal | float
    attendance_percentage: Decimal | float
    threshold_percentage: Decimal | float
    status: str  # WARNING, CRITICAL


class AttendanceDashboardResponse(BaseModel):
    today_sessions_count: int
    today_sessions_marked: int
    today_sessions_pending: int
    total_students_low_attendance: int
    average_attendance_percentage: Decimal | float
    pending_leave_requests_count: int
    pending_corrections_count: int
    recent_sessions: list[AttendanceSessionResponse]
