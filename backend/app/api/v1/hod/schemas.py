"""Pydantic request payloads for the HOD Portal API."""

from pydantic import BaseModel, Field


class ApprovalActionPayload(BaseModel):
    action: str = Field(..., description="APPROVE, REJECT, or REQUEST_INFO")
    remarks: str | None = Field(None, description="HOD remarks or additional instructions")


class MarkCorrectionPayload(BaseModel):
    student_id: str
    assessment_id: str
    course_code: str
    original_mark: float
    requested_mark: float
    reason: str



class EventCreatePayload(BaseModel):
    """Payload to create a new department event."""
    title: str = Field(..., min_length=3)
    description: str = Field(..., min_length=5)
    category: str = Field(
        ...,
        description="Workshop, Symposium, Hackathon, Guest Lecture, FDP, Industrial Visit, Seminar, Club Activity, Conference, Meeting, Other",
    )
    start_date: str
    end_date: str | None = None
    start_time: str | None = "09:30 AM"
    end_time: str | None = "04:30 PM"
    venue: str
    faculty_coordinator: str
    student_coordinator: str | None = None
    target_audience: str = "All CSE Students"
    expected_participants: int = 100
    budget: float = 0.0


class EventReportPayload(BaseModel):
    """Payload for submitting an event completion report."""
    actual_participants: int
    outcomes: str
    report_url: str | None = None
    photos_count: int = 0
    completion_remarks: str


class ReportGeneratePayload(BaseModel):
    """Payload to request statutory department reports."""
    category: str = Field(
        ...,
        description="STUDENT, FACULTY, ATTENDANCE, ACADEMIC, TIMETABLE, PLACEMENT, EVENTS",
    )
    report_type: str
    academic_year: str = "2025-2026"
    semester: str | None = "ODD"
    section: str | None = "ALL"
    start_date: str | None = None
    end_date: str | None = None


class AchievementCreatePayload(BaseModel):
    """Payload to record new department achievement."""
    title: str = Field(..., min_length=3)
    description: str = Field(..., min_length=5)
    category: str = Field(
        ...,
        description="ACADEMIC, RESEARCH, AWARDS, HACKATHON, TECHNICAL_COMPETITION, SPORTS, CERTIFICATION, PROJECT, INNOVATION, CONFERENCE",
    )
    recipient_name: str
    recipient_type: str = Field(..., description="STUDENT or FACULTY")
    recipient_id: str
    achievement_date: str
    academic_year: str = "2025-2026"
    event_or_organization: str
    certificate_url: str | None = None


class AccreditationDocumentCreatePayload(BaseModel):
    """Payload to register an accreditation document."""
    title: str = Field(..., min_length=3)
    criterion: str = Field(
        ...,
        description="CRITERION_1, CRITERION_2, CRITERION_3, CRITERION_4, CRITERION_5",
    )
    academic_year: str = "2025-2026"
    description: str
    file_name: str
    file_type: str = "PDF"
    file_size_kb: int = 500
    uploaded_by: str | None = None


