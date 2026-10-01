from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# --- Institution ---
class InstitutionUpdateRequest(BaseModel):
    legal_name: str | None = Field(None, min_length=2, max_length=255)
    short_name: str | None = Field(None, min_length=2, max_length=64)
    website: str | None = Field(None, max_length=255)
    contact_email: str | None = Field(None, max_length=255)
    contact_phone: str | None = Field(None, max_length=32)
    address_line1: str | None = Field(None, max_length=255)
    city: str | None = Field(None, max_length=100)
    state: str | None = Field(None, max_length=100)
    postal_code: str | None = Field(None, max_length=32)
    country: str | None = Field(None, max_length=100)
    default_timezone: str | None = Field(None, max_length=64)
    currency_code: str | None = Field(None, max_length=8)


class InstitutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    legal_name: str
    short_name: str
    website: str | None
    contact_email: str
    contact_phone: str
    address_line1: str
    city: str
    state: str
    postal_code: str
    country: str
    default_timezone: str
    currency_code: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


# --- Campus ---
class CampusCreateRequest(BaseModel):
    code: str = Field(..., min_length=2, max_length=32)
    name: str = Field(..., min_length=2, max_length=255)
    address: str = Field(..., min_length=3)
    city: str = Field(..., min_length=2, max_length=100)


class CampusUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=255)
    address: str | None = Field(None, min_length=3)
    city: str | None = Field(None, min_length=2, max_length=100)
    is_active: bool | None = None


class CampusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    code: str
    name: str
    address: str
    city: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


# --- Department ---
class DepartmentCreateRequest(BaseModel):
    code: str = Field(..., min_length=2, max_length=32)
    name: str = Field(..., min_length=2, max_length=255)
    department_type: str = Field("ACADEMIC", max_length=32)
    campus_id: UUID | None = None
    hod_user_id: UUID | None = None


class DepartmentUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=255)
    department_type: str | None = Field(None, max_length=32)
    campus_id: UUID | None = None
    hod_user_id: UUID | None = None
    is_active: bool | None = None


class DepartmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    campus_id: UUID | None
    code: str
    name: str
    department_type: str
    hod_user_id: UUID | None
    hod_name: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# --- Program ---
class ProgramCreateRequest(BaseModel):
    department_id: UUID
    code: str = Field(..., min_length=2, max_length=32)
    name: str = Field(..., min_length=2, max_length=255)
    degree_level: str = Field(..., max_length=32)  # UG, PG, DOCTORAL
    duration_years: Decimal = Field(default=Decimal("4.0"))
    total_semesters: int = Field(default=8, ge=1, le=12)
    required_credits: int = Field(default=160, ge=1)


class ProgramUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=255)
    degree_level: str | None = Field(None, max_length=32)
    duration_years: Decimal | None = None
    total_semesters: int | None = Field(None, ge=1, le=12)
    required_credits: int | None = Field(None, ge=1)
    is_active: bool | None = None


class ProgramResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    department_id: UUID
    department_name: str | None = None
    code: str
    name: str
    degree_level: str
    duration_years: Decimal
    total_semesters: int
    required_credits: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


# --- Regulation ---
class RegulationCreateRequest(BaseModel):
    code: str = Field(..., min_length=2, max_length=32)
    title: str = Field(..., min_length=2, max_length=255)
    effective_year: int = Field(..., ge=2000, le=2100)
    description: str | None = None


class RegulationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    code: str
    title: str
    effective_year: int
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# --- Academic Year ---
class AcademicYearCreateRequest(BaseModel):
    name: str = Field(..., min_length=4, max_length=32)  # e.g., "2025-2026"
    start_date: date
    end_date: date
    is_current: bool = False


class AcademicYearResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    start_date: date
    end_date: date
    is_current: bool
    created_at: datetime
    updated_at: datetime


# --- Semester ---
class SemesterCreateRequest(BaseModel):
    academic_year_id: UUID
    name: str = Field(..., min_length=2, max_length=64)
    semester_number: int = Field(..., ge=1, le=12)
    term_type: str = Field(..., max_length=16)  # ODD, EVEN, SUMMER
    start_date: date
    end_date: date
    is_active: bool = False


class SemesterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    academic_year_id: UUID
    name: str
    semester_number: int
    term_type: str
    start_date: date
    end_date: date
    is_active: bool
    created_at: datetime
    updated_at: datetime


# --- Batch ---
class BatchCreateRequest(BaseModel):
    program_id: UUID
    regulation_id: UUID
    name: str = Field(..., min_length=2, max_length=64)  # e.g., "CSE 2024-2028"
    admission_year: int = Field(..., ge=2000, le=2100)
    graduation_year: int = Field(..., ge=2000, le=2100)


class BatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    program_id: UUID
    regulation_id: UUID
    name: str
    admission_year: int
    graduation_year: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


# --- Section ---
class SectionCreateRequest(BaseModel):
    program_id: UUID
    batch_id: UUID
    semester_id: UUID
    name: str = Field(..., min_length=1, max_length=32)  # e.g., "A", "B"
    capacity: int = Field(default=60, ge=1, le=300)


class SectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    program_id: UUID
    batch_id: UUID
    semester_id: UUID
    name: str
    capacity: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
