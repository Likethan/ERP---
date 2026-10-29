"""Pydantic v2 Schemas for Enterprise Academic Timetable, Resource Scheduling & Conflict Resolution (Step 49).

CampusOS Tagline: "One Campus. One System. One Source of Truth."
"""

from datetime import date, datetime, time
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.timetable import (
    CalendarPeriodType,
    ChangeRequestType,
    PublicationType,
    RecurrencePattern,
    ReservationStatus,
    ReservationType,
    ScheduleExceptionType,
    SessionType,
)

# =============================================================================
# 1. TIMETABLE SCHEDULES & VERSIONS
# =============================================================================


class TimetableScheduleCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    academic_year_id: UUID
    semester_id: UUID
    campus_id: UUID | None = None
    department_id: UUID | None = None
    program_id: UUID | None = None
    section_id: UUID | None = None
    name: str = Field(..., max_length=128)
    code: str = Field(..., max_length=32, description="Unique code within tenant, e.g. TT-2026-CSE-S5")
    description: str | None = None


class TimetableScheduleUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class TimetableScheduleCloneRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    target_academic_year_id: UUID
    target_semester_id: UUID
    new_code: str = Field(..., max_length=32)
    new_name: str = Field(..., max_length=128)
    source_version_id: UUID | None = None


class TimetableScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    academic_year_id: UUID
    semester_id: UUID
    campus_id: UUID | None
    department_id: UUID | None
    program_id: UUID | None
    section_id: UUID | None
    name: str
    code: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    current_published_version_id: UUID | None = None
    latest_version_number: int = 1


class TimetableVersionCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    effective_start_date: date | None = None
    effective_end_date: date | None = None
    change_summary: str | None = None


class TimetableVersionUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    effective_start_date: date | None = None
    effective_end_date: date | None = None
    change_summary: str | None = None
    is_active: bool | None = None


class TimetableVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    schedule_id: UUID
    version_number: int
    status: str
    effective_start_date: date | None
    effective_end_date: date | None
    change_summary: str | None
    is_active: bool
    approved_by_user_id: UUID | None
    approved_at: datetime | None
    published_by_user_id: UUID | None
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime
    sessions_count: int = 0
    conflicts_count: int = 0


class TimetableVersionSubmitReview(BaseModel):
    notes: str | None = None


class TimetableVersionApproval(BaseModel):
    approved: bool = True
    rejection_reason: str | None = None


class TimetableVersionPublish(BaseModel):
    publication_type: PublicationType = PublicationType.INITIAL
    published_to_students: bool = True
    published_to_faculty: bool = True
    calendar_sync_enabled: bool = True
    notes: str | None = None


# =============================================================================
# 2. SESSIONS
# =============================================================================


class TimetableSessionCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    course_offering_id: UUID
    section_id: UUID
    subject_id: UUID | None = None
    faculty_id: UUID | None = None
    co_faculty_ids: list[UUID] = Field(default_factory=list)
    room_id: UUID | None = None
    day_of_week: int = Field(..., ge=1, le=7, description="1=Monday ... 7=Sunday")
    start_time: time
    end_time: time
    time_slot_id: UUID | None = None
    session_type: SessionType = SessionType.LECTURE
    session_group: str | None = None
    recurrence_pattern: RecurrencePattern = RecurrencePattern.WEEKLY
    is_locked: bool = False
    transition_buffer_minutes: int = 0


class TimetableSessionUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    course_offering_id: UUID | None = None
    section_id: UUID | None = None
    subject_id: UUID | None = None
    faculty_id: UUID | None = None
    co_faculty_ids: list[UUID] | None = None
    room_id: UUID | None = None
    day_of_week: int | None = Field(None, ge=1, le=7)
    start_time: time | None = None
    end_time: time | None = None
    time_slot_id: UUID | None = None
    session_type: SessionType | None = None
    session_group: str | None = None
    recurrence_pattern: RecurrencePattern | None = None
    is_locked: bool | None = None
    is_cancelled: bool | None = None
    cancellation_reason: str | None = None
    replacement_room_id: UUID | None = None
    substitute_faculty_id: UUID | None = None
    transition_buffer_minutes: int | None = None


class TimetableSessionBatchCreate(BaseModel):
    sessions: list[TimetableSessionCreate]


class TimetableSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    version_id: UUID
    course_offering_id: UUID
    section_id: UUID
    subject_id: UUID | None
    subject_code: str | None = None
    subject_name: str | None = None
    section_name: str | None = None
    faculty_id: UUID | None
    faculty_name: str | None = None
    co_faculty_ids: list[str] = Field(default_factory=list)
    room_id: UUID | None
    room_name: str | None = None
    day_of_week: int
    start_time: time
    end_time: time
    time_slot_id: UUID | None
    session_type: str
    session_group: str | None
    recurrence_pattern: str
    is_locked: bool
    is_cancelled: bool
    cancellation_reason: str | None
    replacement_room_id: UUID | None
    substitute_faculty_id: UUID | None
    transition_buffer_minutes: int
    canonical_slot_id: UUID | None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 3. PERIOD CONFIG, CALENDAR & EXCEPTIONS
# =============================================================================


class TeachingPeriodConfigCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., max_length=128)
    campus_id: UUID | None = None
    academic_year_id: UUID | None = None
    teaching_days: list[int] = Field(default_factory=lambda: [1, 2, 3, 4, 5, 6])
    day_start_time: time
    day_end_time: time
    period_duration_minutes: int = 50
    transition_buffer_minutes: int = 10
    lunch_start_time: time | None = None
    lunch_end_time: time | None = None
    breaks_json: list[dict[str, Any]] = Field(default_factory=list)
    is_default: bool = True


class TeachingPeriodConfigUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str | None = None
    teaching_days: list[int] | None = None
    day_start_time: time | None = None
    day_end_time: time | None = None
    period_duration_minutes: int | None = None
    transition_buffer_minutes: int | None = None
    lunch_start_time: time | None = None
    lunch_end_time: time | None = None
    breaks_json: list[dict[str, Any]] | None = None
    is_default: bool | None = None
    is_active: bool | None = None


class TeachingPeriodConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    campus_id: UUID | None
    academic_year_id: UUID | None
    name: str
    teaching_days: list[int]
    day_start_time: time
    day_end_time: time
    period_duration_minutes: int
    transition_buffer_minutes: int
    lunch_start_time: time | None
    lunch_end_time: time | None
    breaks_json: list[dict[str, Any]]
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AcademicCalendarPeriodCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    academic_year_id: UUID
    name: str = Field(..., max_length=128)
    calendar_type: CalendarPeriodType = CalendarPeriodType.HOLIDAY
    start_date: date
    end_date: date
    semester_id: UUID | None = None
    campus_id: UUID | None = None
    affects_teaching: bool = True
    description: str | None = None


class AcademicCalendarPeriodUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str | None = None
    calendar_type: CalendarPeriodType | None = None
    start_date: date | None = None
    end_date: date | None = None
    affects_teaching: bool | None = None
    description: str | None = None
    is_active: bool | None = None


class AcademicCalendarPeriodResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    academic_year_id: UUID
    semester_id: UUID | None
    campus_id: UUID | None
    name: str
    calendar_type: str
    start_date: date
    end_date: date
    affects_teaching: bool
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ScheduleExceptionCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    exception_date: date
    exception_type: ScheduleExceptionType = ScheduleExceptionType.HOLIDAY_CLOSURE
    schedule_id: UUID | None = None
    campus_id: UUID | None = None
    substitute_day_of_week: int | None = Field(None, ge=1, le=7)
    affected_room_ids: list[UUID] = Field(default_factory=list)
    affected_section_ids: list[UUID] = Field(default_factory=list)
    notes: str | None = None


class ScheduleExceptionUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    exception_type: ScheduleExceptionType | None = None
    substitute_day_of_week: int | None = None
    affected_room_ids: list[UUID] | None = None
    affected_section_ids: list[UUID] | None = None
    notes: str | None = None
    is_active: bool | None = None


class ScheduleExceptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    schedule_id: UUID | None
    campus_id: UUID | None
    exception_date: date
    exception_type: str
    substitute_day_of_week: int | None
    affected_room_ids: list[str]
    affected_section_ids: list[str]
    notes: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# =============================================================================
# 4. FACULTY AVAILABILITY & WORKLOAD
# =============================================================================


class FacultyAvailabilityCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    faculty_id: UUID
    academic_year_id: UUID
    semester_id: UUID | None = None
    day_of_week: int = Field(..., ge=1, le=7)
    available_start_time: time
    available_end_time: time
    is_available: bool = True
    max_hours_per_day: Decimal = Decimal("4.00")
    max_hours_per_week: Decimal = Decimal("18.00")
    preferred_session_types: list[str] = Field(default_factory=list)
    notes: str | None = None


class FacultyAvailabilityUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    available_start_time: time | None = None
    available_end_time: time | None = None
    is_available: bool | None = None
    max_hours_per_day: Decimal | None = None
    max_hours_per_week: Decimal | None = None
    preferred_session_types: list[str] | None = None
    notes: str | None = None
    is_active: bool | None = None


class FacultyAvailabilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    faculty_id: UUID
    academic_year_id: UUID
    semester_id: UUID | None
    day_of_week: int
    available_start_time: time
    available_end_time: time
    is_available: bool
    max_hours_per_day: Decimal
    max_hours_per_week: Decimal
    preferred_session_types: list[str]
    notes: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class FacultyWorkloadSummary(BaseModel):
    faculty_id: UUID
    faculty_name: str
    department_id: UUID | None
    department_name: str | None
    total_assigned_hours_per_week: Decimal
    max_allowed_hours_per_week: Decimal
    workload_utilization_percent: Decimal
    daily_hours: dict[str, Decimal]  # "Monday": 3.0, etc.
    active_courses_count: int
    is_overloaded: bool


# =============================================================================
# 5. RESOURCE RESERVATIONS & MAINTENANCE
# =============================================================================


class ResourceReservationCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    room_id: UUID
    title: str = Field(..., max_length=128)
    start_datetime: datetime
    end_datetime: datetime
    reservation_type: ReservationType = ReservationType.TIMETABLE
    session_id: UUID | None = None
    is_exclusive: bool = True
    notes: str | None = None


class ResourceReservationUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str | None = None
    start_datetime: datetime | None = None
    end_datetime: datetime | None = None
    status: ReservationStatus | None = None
    notes: str | None = None


class ResourceReservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    room_id: UUID
    room_name: str | None = None
    reservation_type: str
    title: str
    start_datetime: datetime
    end_datetime: datetime
    status: str
    session_id: UUID | None
    requested_by_user_id: UUID | None
    approved_by_user_id: UUID | None
    is_exclusive: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime


class ResourceMaintenanceWindowCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    room_id: UUID
    title: str = Field(..., max_length=128)
    reason: str
    start_time: datetime
    end_time: datetime


class ResourceMaintenanceWindowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    room_id: UUID
    title: str
    reason: str
    start_time: datetime
    end_time: datetime
    status: str
    created_at: datetime
    updated_at: datetime


class ResourceAvailabilityCheckRequest(BaseModel):
    room_id: UUID
    day_of_week: int
    start_time: time
    end_time: time
    exclude_session_id: UUID | None = None


class ResourceAvailabilityResponse(BaseModel):
    room_id: UUID
    is_available: bool
    conflicting_sessions_count: int
    conflicting_reservations_count: int
    maintenance_windows_count: int
    suggested_alternative_rooms: list[dict[str, Any]] = Field(default_factory=list)


# =============================================================================
# 6. GENERATION & CONFLICT RESOLUTION
# =============================================================================


class TimetableGenerationRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    academic_year_id: UUID
    semester_id: UUID
    campus_id: UUID | None = None
    department_id: UUID | None = None
    program_id: UUID | None = None
    section_id: UUID | None = None
    schedule_id: UUID | None = None
    preserve_locked_sessions: bool = True
    max_daily_faculty_hours: Decimal = Decimal("4.00")
    config_parameters: dict[str, Any] = Field(default_factory=dict)


class TimetableGenerationJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    academic_year_id: UUID
    semester_id: UUID
    campus_id: UUID | None
    department_id: UUID | None
    program_id: UUID | None
    section_id: UUID | None
    job_status: str
    total_sessions_to_schedule: int
    scheduled_sessions_count: int
    unscheduled_sessions_count: int
    candidate_version_id: UUID | None
    error_summary: str | None
    result_metadata: dict[str, Any]
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class TimetableConflictResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    version_id: UUID
    conflict_type: str
    severity: str
    affected_date_or_day: str
    time_window: str
    description: str
    rule_violated: str
    session_id_1: UUID | None
    session_id_2: UUID | None
    faculty_id: UUID | None
    room_id: UUID | None
    section_id: UUID | None
    remediation_suggestions: list[dict[str, Any]]
    is_resolved: bool
    resolved_at: datetime | None
    resolved_by_user_id: UUID | None
    created_at: datetime


class TimetableConflictResolveRequest(BaseModel):
    resolution_notes: str | None = None


class TimetableValidationReport(BaseModel):
    version_id: UUID
    total_sessions: int
    critical_conflicts_count: int
    warning_conflicts_count: int
    is_valid_for_publication: bool
    conflicts: list[TimetableConflictResponse]


# =============================================================================
# 7. CHANGE MANAGEMENT & PUBLICATION
# =============================================================================


class TimetableChangeRequestCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    version_id: UUID
    session_id: UUID
    change_type: ChangeRequestType = ChangeRequestType.RESCHEDULE
    proposed_day_of_week: int | None = Field(None, ge=1, le=7)
    proposed_start_time: time | None = None
    proposed_end_time: time | None = None
    proposed_room_id: UUID | None = None
    proposed_faculty_id: UUID | None = None
    reason: str
    is_emergency: bool = False


class TimetableChangeRequestReview(BaseModel):
    approved: bool
    review_notes: str | None = None


class TimetableChangeRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    version_id: UUID
    session_id: UUID
    change_type: str
    proposed_day_of_week: int | None
    proposed_start_time: time | None
    proposed_end_time: time | None
    proposed_room_id: UUID | None
    proposed_faculty_id: UUID | None
    reason: str
    is_emergency: bool
    status: str
    impact_analysis: dict[str, Any]
    requested_by_user_id: UUID | None
    reviewed_by_user_id: UUID | None
    reviewed_at: datetime | None
    review_notes: str | None
    created_at: datetime
    updated_at: datetime


class TimetablePublicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    version_id: UUID
    publication_type: str
    published_to_students: bool
    published_to_faculty: bool
    calendar_sync_enabled: bool
    published_by_user_id: UUID | None
    published_at: datetime
    notes: str | None


# =============================================================================
# 8. GRID VIEWS & EXPORT
# =============================================================================


class TimetableGridCell(BaseModel):
    session_id: UUID
    course_offering_id: UUID
    subject_code: str
    subject_name: str
    faculty_id: UUID | None = None
    faculty_name: str | None = None
    room_id: UUID | None = None
    room_name: str | None = None
    section_id: UUID
    section_name: str | None = None
    start_time: time
    end_time: time
    session_type: str
    is_locked: bool = False
    is_cancelled: bool = False


class TimetableGridDay(BaseModel):
    day_of_week: int
    day_name: str
    sessions: list[TimetableGridCell]


class TimetableGridResponse(BaseModel):
    view_type: str  # "SECTION", "FACULTY", "ROOM"
    entity_id: UUID
    entity_name: str
    academic_year_id: UUID
    semester_id: UUID
    version_id: UUID | None
    is_published: bool
    days: list[TimetableGridDay]


# =============================================================================
# 9. ATTENDANCE RECONCILIATION & ANALYTICS
# =============================================================================


class AttendanceSessionReconciliationItem(BaseModel):
    scheduled_session_id: UUID
    course_offering_id: UUID
    subject_code: str
    day_of_week: int
    start_time: time
    end_time: time
    attendance_session_id: UUID | None
    attendance_status: str | None
    total_records_count: int
    present_records_count: int
    is_reconciled: bool


class AttendanceReconciliationReport(BaseModel):
    section_id: UUID
    academic_year_id: UUID
    semester_id: UUID
    total_scheduled_sessions: int
    total_attendance_sessions_marked: int
    coverage_percentage: Decimal
    items: list[AttendanceSessionReconciliationItem]


class RoomUtilizationMetric(BaseModel):
    room_id: UUID
    room_number: str
    building: str
    room_type: str
    capacity: int
    scheduled_hours_per_week: Decimal
    total_available_hours_per_week: Decimal
    utilization_percentage: Decimal
    peak_demand_day: str | None


class FacultyWorkloadMetric(BaseModel):
    faculty_id: UUID
    employee_code: str
    faculty_name: str
    department_name: str
    scheduled_hours: Decimal
    workload_limit: Decimal
    utilization_percentage: Decimal
    overloaded: bool


class TimetableAnalyticsResponse(BaseModel):
    total_schedules_count: int
    total_published_versions_count: int
    total_scheduled_sessions_count: int
    overall_timetable_coverage_percent: Decimal
    unresolved_conflicts_count: int
    total_change_requests_count: int
    average_room_utilization_percent: Decimal
    room_utilization: list[RoomUtilizationMetric]
    faculty_workloads: list[FacultyWorkloadMetric]
