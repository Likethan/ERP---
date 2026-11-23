from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# --- Student Lifecycle Statuses ---
VALID_STUDENT_STATUSES = {
    "APPLIED",
    "ADMITTED",
    "ACTIVE",
    "SUSPENDED",
    "ON_LEAVE",
    "GRADUATED",
    "WITHDRAWN",
    "ALUMNI",
}

# Permissible transitions: key -> set of valid next states
ALLOWED_STATUS_TRANSITIONS: dict[str, set[str]] = {
    "APPLIED": {"ADMITTED", "WITHDRAWN"},
    "ADMITTED": {"ACTIVE", "WITHDRAWN"},
    "ACTIVE": {"SUSPENDED", "ON_LEAVE", "GRADUATED", "WITHDRAWN"},
    "SUSPENDED": {"ACTIVE", "WITHDRAWN"},
    "ON_LEAVE": {"ACTIVE", "WITHDRAWN"},
    "GRADUATED": {"ALUMNI"},
    "WITHDRAWN": set(),
    "ALUMNI": set(),
}


# --- Student Requests & Responses ---
class StudentCreateRequest(BaseModel):
    # User Account attributes
    email: EmailStr
    password: str = Field(default="Welcome@123", min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone_number: str | None = Field(None, max_length=32)

    # Student Profile attributes
    admission_number: str = Field(..., min_length=2, max_length=64)
    registration_number: str | None = Field(None, max_length=64)
    roll_number: str | None = Field(None, max_length=64)
    date_of_birth: date
    gender: str = Field(..., pattern="^(MALE|FEMALE|OTHER)$")
    blood_group: str | None = Field(None, max_length=8)
    admission_date: date = Field(default_factory=date.today)
    expected_graduation_date: date

    # Institutional Relationships
    program_id: UUID
    batch_id: UUID
    current_semester_id: UUID | None = None
    current_section_id: UUID | None = None

    # Emergency Contact
    emergency_contact_name: str | None = Field(None, max_length=128)
    emergency_contact_phone: str | None = Field(None, max_length=32)


class StudentUpdateRequest(BaseModel):
    registration_number: str | None = Field(None, max_length=64)
    roll_number: str | None = Field(None, max_length=64)
    blood_group: str | None = Field(None, max_length=8)
    current_semester_id: UUID | None = None
    current_section_id: UUID | None = None
    emergency_contact_name: str | None = Field(None, max_length=128)
    emergency_contact_phone: str | None = Field(None, max_length=32)


class StudentStatusTransitionRequest(BaseModel):
    to_status: str = Field(..., min_length=2, max_length=32)
    reason: str = Field(..., min_length=3)
    effective_date: date = Field(default_factory=date.today)


class StudentEnrollmentHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    academic_year_id: UUID
    semester_id: UUID
    section_id: UUID
    roll_number_snapshot: str | None
    status: str
    start_date: date
    end_date: date | None


class StudentStatusHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    from_status: str
    to_status: str
    reason: str
    authorized_by_user_id: UUID
    effective_date: date
    created_at: datetime


class StudentSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    tenant_id: UUID
    admission_number: str
    registration_number: str | None
    roll_number: str | None
    first_name: str
    last_name: str
    email: str
    gender: str
    status: str
    program_id: UUID
    program_name: str | None = None
    program_code: str | None = None
    batch_id: UUID
    batch_name: str | None = None
    current_semester_id: UUID | None
    current_section_id: UUID | None
    current_section_name: str | None = None
    created_at: datetime


class StudentDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    tenant_id: UUID
    admission_number: str
    registration_number: str | None
    roll_number: str | None
    first_name: str
    last_name: str
    email: str
    phone_number: str | None
    date_of_birth: date
    gender: str
    blood_group: str | None
    status: str
    admission_date: date
    expected_graduation_date: date
    actual_graduation_date: date | None
    program_id: UUID
    program_name: str | None = None
    program_code: str | None = None
    batch_id: UUID
    batch_name: str | None = None
    current_semester_id: UUID | None
    current_section_id: UUID | None
    current_section_name: str | None = None
    emergency_contact_name: str | None
    emergency_contact_phone: str | None
    enrollment_history: list[StudentEnrollmentHistoryResponse] = Field(default_factory=list)
    status_history: list[StudentStatusHistoryResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


# --- Faculty Requests & Responses ---
class FacultyCreateRequest(BaseModel):
    # User Account attributes
    email: EmailStr
    password: str = Field(default="Faculty@123", min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone_number: str | None = Field(None, max_length=32)

    # Faculty Profile attributes
    employee_code: str = Field(..., min_length=2, max_length=64)
    department_id: UUID
    designation: str = Field(..., min_length=2, max_length=128)  # Professor, Asst Professor, etc.
    highest_qualification: str = Field(..., min_length=2, max_length=128)  # Ph.D, M.Tech, etc.
    specialization: str | None = None
    joining_date: date = Field(default_factory=date.today)
    is_hod: bool = False
    employment_status: str = Field("ACTIVE", max_length=32)


class FacultyUpdateRequest(BaseModel):
    designation: str | None = Field(None, min_length=2, max_length=128)
    highest_qualification: str | None = Field(None, min_length=2, max_length=128)
    specialization: str | None = None
    department_id: UUID | None = None
    is_hod: bool | None = None
    employment_status: str | None = Field(None, max_length=32)


class FacultyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    tenant_id: UUID
    employee_code: str
    department_id: UUID
    department_name: str | None = None
    first_name: str
    last_name: str
    email: str
    phone_number: str | None
    designation: str
    highest_qualification: str
    specialization: str | None
    joining_date: date
    is_hod: bool
    employment_status: str
    created_at: datetime
    updated_at: datetime


# --- Staff Requests & Responses ---
class StaffCreateRequest(BaseModel):
    # User Account attributes
    email: EmailStr
    password: str = Field(default="Staff@123", min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone_number: str | None = Field(None, max_length=32)

    # Staff Profile attributes
    employee_code: str = Field(..., min_length=2, max_length=64)
    department_id: UUID | None = None
    designation: str = Field(..., min_length=2, max_length=128)
    employment_type: str = Field("FULL_TIME", max_length=32)
    is_active: bool = True


class StaffUpdateRequest(BaseModel):
    designation: str | None = Field(None, min_length=2, max_length=128)
    department_id: UUID | None = None
    employment_type: str | None = Field(None, max_length=32)
    is_active: bool | None = None


class StaffResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    tenant_id: UUID
    employee_code: str
    department_id: UUID | None
    department_name: str | None = None
    first_name: str
    last_name: str
    email: str
    phone_number: str | None
    designation: str
    employment_type: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


# --- Guardian Requests & Responses ---
class GuardianCreateRequest(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr | None = None
    phone_number: str = Field(..., min_length=7, max_length=32)
    occupation: str | None = Field(None, max_length=128)
    annual_income: Decimal | None = None
    address: str | None = None
    relationship_type: str = Field("FATHER", max_length=32)  # FATHER, MOTHER, LEGAL_GUARDIAN
    is_primary: bool = False
    can_pickup: bool = True


class GuardianResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    first_name: str
    last_name: str
    email: str | None
    phone_number: str
    occupation: str | None
    address: str | None
    created_at: datetime
