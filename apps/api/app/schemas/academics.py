from datetime import date, datetime, time
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# --- Subject Schemas ---
VALID_SUBJECT_TYPES = {
    "THEORY",
    "PRACTICAL",
    "LAB",
    "PROJECT",
    "ELECTIVE",
    "SEMINAR",
    "INTERNSHIP",
}


class SubjectCreateRequest(BaseModel):
    department_id: UUID
    code: str = Field(..., min_length=2, max_length=32)
    name: str = Field(..., min_length=2, max_length=255)
    credits: Decimal = Field(default=Decimal("3.0"), ge=0, le=30)
    lecture_hours: int = Field(default=3, ge=0, le=20)
    tutorial_hours: int = Field(default=0, ge=0, le=20)
    practical_hours: int = Field(default=0, ge=0, le=20)
    subject_type: str = Field(default="THEORY", max_length=32)
    description: str | None = None
    is_active: bool = True


class SubjectUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=255)
    credits: Decimal | None = Field(None, ge=0, le=30)
    lecture_hours: int | None = Field(None, ge=0, le=20)
    tutorial_hours: int | None = Field(None, ge=0, le=20)
    practical_hours: int | None = Field(None, ge=0, le=20)
    subject_type: str | None = Field(None, max_length=32)
    description: str | None = None
    is_active: bool | None = None


class SubjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    department_id: UUID
    department_name: str | None = None
    code: str
    name: str
    credits: Decimal
    lecture_hours: int
    tutorial_hours: int
    practical_hours: int
    subject_type: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# --- Curriculum Schemas ---
class CurriculumCreateRequest(BaseModel):
    program_id: UUID
    regulation_id: UUID
    name: str = Field(..., min_length=2, max_length=255)
    version: int = Field(default=1, ge=1, le=50)
    total_credits: Decimal = Field(default=Decimal("160.0"), ge=0, le=300)
    description: str | None = None


class CurriculumUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=255)
    total_credits: Decimal | None = Field(None, ge=0, le=300)
    description: str | None = None


class CurriculumSubjectCreateRequest(BaseModel):
    subject_id: UUID
    semester_number: int = Field(..., ge=1, le=12)
    category: str = Field(default="CORE", max_length=32)
    is_mandatory: bool = True
    elective_group: str | None = Field(None, max_length=64)
    credits: Decimal = Field(default=Decimal("3.0"), ge=0, le=30)
    lecture_hours: int = Field(default=3, ge=0, le=20)
    tutorial_hours: int = Field(default=0, ge=0, le=20)
    practical_hours: int = Field(default=0, ge=0, le=20)


class CurriculumSubjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    curriculum_id: UUID
    subject_id: UUID
    subject_code: str | None = None
    subject_name: str | None = None
    semester_number: int
    category: str
    is_mandatory: bool
    elective_group: str | None
    credits: Decimal
    lecture_hours: int
    tutorial_hours: int
    practical_hours: int


class CurriculumResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    program_id: UUID
    program_name: str | None = None
    program_code: str | None = None
    regulation_id: UUID
    regulation_code: str | None = None
    name: str
    version: int
    status: str
    total_credits: Decimal
    description: str | None
    is_locked: bool
    subjects_count: int = 0
    created_at: datetime
    updated_at: datetime


class CurriculumDetailResponse(CurriculumResponse):
    subjects: list[CurriculumSubjectResponse] = Field(default_factory=list)


# --- Classroom / Room Schemas ---
class ClassroomCreateRequest(BaseModel):
    campus_id: UUID | None = None
    building: str = Field(..., min_length=1, max_length=128)
    room_number: str = Field(..., min_length=1, max_length=64)
    capacity: int = Field(default=60, ge=1, le=1000)
    room_type: str = Field(default="CLASSROOM", max_length=32)
    is_active: bool = True


class ClassroomResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    campus_id: UUID | None
    campus_name: str | None = None
    building: str
    room_number: str
    capacity: int
    room_type: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


# --- Time Slot Schemas ---
class TimeSlotCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    slot_number: int = Field(..., ge=1, le=100)
    start_time: time
    end_time: time
    slot_type: str = Field(default="LECTURE", max_length=32)
    is_active: bool = True


class TimeSlotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    slot_number: int
    start_time: time
    end_time: time
    slot_type: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


# --- Course Offering Schemas ---
VALID_OFFERING_STATUSES = {"PLANNED", "OPEN", "ACTIVE", "COMPLETED", "CANCELLED"}


class CourseOfferingCreateRequest(BaseModel):
    subject_id: UUID
    academic_year_id: UUID
    semester_id: UUID
    section_id: UUID
    max_capacity: int = Field(default=60, ge=1, le=300)
    status: str = Field(default="PLANNED", max_length=32)


class CourseOfferingStatusTransitionRequest(BaseModel):
    status: str = Field(..., max_length=32)


class CourseFacultyAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    course_offering_id: UUID
    faculty_id: UUID
    faculty_name: str | None = None
    faculty_employee_code: str | None = None
    role: str
    start_date: date | None
    end_date: date | None
    is_active: bool


class CourseFacultyAssignmentCreateRequest(BaseModel):
    faculty_id: UUID
    role: str = Field(default="PRIMARY", max_length=32)
    start_date: date | None = None
    end_date: date | None = None


class CourseOfferingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    subject_id: UUID
    subject_code: str | None = None
    subject_name: str | None = None
    subject_credits: Decimal | None = None
    academic_year_id: UUID
    academic_year_name: str | None = None
    semester_id: UUID
    semester_name: str | None = None
    section_id: UUID
    section_name: str | None = None
    program_name: str | None = None
    status: str
    max_capacity: int
    enrolled_count: int = 0
    primary_faculty_name: str | None = None
    created_at: datetime
    updated_at: datetime


class CourseOfferingDetailResponse(CourseOfferingResponse):
    faculty_assignments: list[CourseFacultyAssignmentResponse] = Field(default_factory=list)


# --- Student Course Enrollment Schemas ---
class CourseEnrollmentCreateRequest(BaseModel):
    student_id: UUID
    enrollment_type: str = Field(default="REGULAR", max_length=32)


class CourseBatchEnrollRequest(BaseModel):
    section_id: UUID
    enrollment_type: str = Field(default="REGULAR", max_length=32)


class CourseEnrollmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    student_id: UUID
    student_name: str | None = None
    student_roll_number: str | None = None
    student_admission_number: str | None = None
    course_offering_id: UUID
    enrollment_type: str
    status: str
    enrollment_date: date
    dropped_date: date | None
    created_at: datetime
    updated_at: datetime


# --- Timetable Schemas ---
class TimetableEntryCreateRequest(BaseModel):
    course_offering_id: UUID
    section_id: UUID
    academic_year_id: UUID
    semester_id: UUID
    time_slot_id: UUID
    day_of_week: int = Field(..., ge=1, le=7)  # 1=Mon, 7=Sun
    faculty_id: UUID | None = None
    room_id: UUID | None = None


class TimetableEntryUpdateRequest(BaseModel):
    faculty_id: UUID | None = None
    room_id: UUID | None = None
    time_slot_id: UUID | None = None
    day_of_week: int | None = Field(None, ge=1, le=7)
    is_active: bool | None = None


class TimetableEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    course_offering_id: UUID
    subject_code: str | None = None
    subject_name: str | None = None
    section_id: UUID
    section_name: str | None = None
    academic_year_id: UUID
    semester_id: UUID
    faculty_id: UUID | None
    faculty_name: str | None = None
    room_id: UUID | None
    room_name: str | None = None
    time_slot_id: UUID
    time_slot_name: str | None = None
    time_slot_start: time | None = None
    time_slot_end: time | None = None
    day_of_week: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TimetableGridCell(BaseModel):
    entry_id: UUID
    course_offering_id: UUID
    subject_code: str
    subject_name: str
    faculty_name: str | None
    room_name: str | None
    time_slot_id: UUID


class TimetableGridDay(BaseModel):
    day_of_week: int
    day_name: str
    slots: dict[str, TimetableGridCell | None] = Field(default_factory=dict)


class TimetableSectionGridResponse(BaseModel):
    section_id: UUID
    section_name: str
    academic_year_id: UUID
    semester_id: UUID
    time_slots: list[TimeSlotResponse]
    days: list[TimetableGridDay]
