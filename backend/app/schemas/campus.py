"""Pydantic request and response schemas for Campus Events, Clubs, Announcements, and Notifications."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# -----------------------------------------------------------------------------
# 1. EVENT CATEGORIES
# -----------------------------------------------------------------------------
class EventCategoryCreate(BaseModel):
    code: str = Field(..., max_length=32, examples=["TECHNICAL"])
    name: str = Field(..., max_length=128, examples=["Technical & Engineering"])
    description: str | None = None
    is_active: bool = True


class EventCategoryUpdate(BaseModel):
    name: str | None = Field(None, max_length=128)
    description: str | None = None
    is_active: bool | None = None


class EventCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    code: str
    name: str
    description: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# -----------------------------------------------------------------------------
# 2. EVENT VENUES
# -----------------------------------------------------------------------------
class EventVenueCreate(BaseModel):
    campus_id: UUID
    name: str = Field(..., max_length=128, examples=["Main Auditorium"])
    code: str = Field(..., max_length=32, examples=["AUD-01"])
    building: str = Field(..., max_length=128, examples=["Admin Block"])
    floor: str | None = Field(None, max_length=32, examples=["Ground Floor"])
    capacity: int = Field(..., ge=1, examples=[1000])
    location_description: str | None = None
    status: str = Field("ACTIVE", examples=["ACTIVE", "MAINTENANCE", "INACTIVE"])


class EventVenueUpdate(BaseModel):
    name: str | None = Field(None, max_length=128)
    code: str | None = Field(None, max_length=32)
    building: str | None = Field(None, max_length=128)
    floor: str | None = Field(None, max_length=32)
    capacity: int | None = Field(None, ge=1)
    location_description: str | None = None
    status: str | None = None


class EventVenueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    campus_id: UUID
    name: str
    code: str
    building: str
    floor: str | None = None
    capacity: int
    location_description: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime


# -----------------------------------------------------------------------------
# 3. CAMPUS EVENTS
# -----------------------------------------------------------------------------
class EventCreate(BaseModel):
    campus_id: UUID
    category_id: UUID | None = None
    title: str = Field(..., max_length=255, examples=["National Hackathon 2026"])
    slug: str | None = Field(None, max_length=255, examples=["national-hackathon-2026"])
    description: str | None = None
    organizer_type: str = Field("INSTITUTION", examples=["INSTITUTION", "CAMPUS", "DEPARTMENT", "CLUB", "PLACEMENT", "STUDENT_ORG"])
    organizer_id: UUID | None = None
    department_id: UUID | None = None
    club_id: UUID | None = None
    start_at: datetime
    end_at: datetime
    registration_open_at: datetime | None = None
    registration_close_at: datetime | None = None
    venue_id: UUID | None = None
    venue_name: str | None = Field(None, max_length=128)
    capacity: int | None = Field(None, ge=1)
    visibility: str = Field("CAMPUS", examples=["PUBLIC", "INSTITUTION", "CAMPUS", "DEPARTMENT", "PROGRAM", "SECTION", "CLUB", "PRIVATE"])
    requires_registration: bool = True
    requires_attendance: bool = True
    target_filter_json: dict | list | None = None


class EventUpdate(BaseModel):
    category_id: UUID | None = None
    title: str | None = Field(None, max_length=255)
    description: str | None = None
    organizer_type: str | None = None
    organizer_id: UUID | None = None
    department_id: UUID | None = None
    club_id: UUID | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    registration_open_at: datetime | None = None
    registration_close_at: datetime | None = None
    venue_id: UUID | None = None
    venue_name: str | None = None
    capacity: int | None = Field(None, ge=1)
    visibility: str | None = None
    requires_registration: bool | None = None
    requires_attendance: bool | None = None
    target_filter_json: dict | list | None = None
    status: str | None = None


class EventStatusTransition(BaseModel):
    status: str = Field(..., examples=["PUBLISHED", "REGISTRATION_OPEN", "CANCELLED", "COMPLETED"])
    reason: str | None = None


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    campus_id: UUID
    category_id: UUID | None = None
    title: str
    slug: str
    description: str | None = None
    organizer_type: str
    organizer_id: UUID | None = None
    department_id: UUID | None = None
    club_id: UUID | None = None
    start_at: datetime
    end_at: datetime
    registration_open_at: datetime | None = None
    registration_close_at: datetime | None = None
    venue_id: UUID | None = None
    venue_name: str | None = None
    capacity: int | None = None
    status: str
    visibility: str
    requires_registration: bool
    requires_attendance: bool
    target_filter_json: dict | list | None = None
    created_by_user_id: UUID | None = None
    registered_count: int = 0
    attended_count: int = 0
    created_at: datetime
    updated_at: datetime


class EventDetailResponse(EventResponse):
    category_name: str | None = None
    venue_details: EventVenueResponse | None = None
    organizer_name: str | None = None
    user_registration_status: str | None = None  # None, REGISTERED, ATTENDED, CANCELLED, etc.
    user_registration_id: UUID | None = None


# -----------------------------------------------------------------------------
# 4. EVENT REGISTRATION
# -----------------------------------------------------------------------------
class EventRegistrationCreate(BaseModel):
    student_id: UUID | None = None  # Optional when registering self; required if staff registers student


class EventRegistrationCancel(BaseModel):
    cancellation_reason: str | None = None


class EventRegistrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    event_id: UUID
    student_id: UUID
    registration_code: str
    registered_at: datetime
    status: str
    cancelled_at: datetime | None = None
    cancellation_reason: str | None = None
    attended: bool = False
    student_name: str | None = None
    student_roll_number: str | None = None
    student_email: str | None = None
    event_title: str | None = None
    created_at: datetime


# -----------------------------------------------------------------------------
# 5. EVENT ATTENDANCE & CHECK-IN
# -----------------------------------------------------------------------------
class EventCheckInRequest(BaseModel):
    student_id: UUID | None = None
    registration_code: str | None = None
    verification_method: str = Field("MANUAL", examples=["MANUAL", "QR", "NFC"])
    remarks: str | None = None


class EventCheckInResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    event_id: UUID
    student_id: UUID
    checked_in_at: datetime
    attendance_status: str
    verification_method: str
    student_name: str | None = None
    student_roll_number: str | None = None
    remarks: str | None = None


class EventQRTokenResponse(BaseModel):
    event_id: UUID
    qr_token: str
    expires_at: datetime
    valid_duration_seconds: int


class EventQRCheckInRequest(BaseModel):
    qr_token: str


# -----------------------------------------------------------------------------
# 6. CLUBS & ORGANIZATIONS
# -----------------------------------------------------------------------------
class ClubCreate(BaseModel):
    campus_id: UUID | None = None
    code: str = Field(..., max_length=32, examples=["CODING-CLUB"])
    name: str = Field(..., max_length=128, examples=["Campus Coding Society"])
    slug: str | None = Field(None, max_length=128)
    category: str = Field("TECHNICAL", examples=["TECHNICAL", "CULTURAL", "SPORTS", "SOCIAL", "ACADEMIC", "ENTREPRENEURSHIP", "LITERARY", "OTHER"])
    description: str | None = None
    logo_document_id: UUID | None = None
    faculty_advisor_id: UUID | None = None
    student_lead_id: UUID | None = None


class ClubUpdate(BaseModel):
    campus_id: UUID | None = None
    name: str | None = Field(None, max_length=128)
    slug: str | None = Field(None, max_length=128)
    category: str | None = None
    description: str | None = None
    logo_document_id: UUID | None = None
    faculty_advisor_id: UUID | None = None
    student_lead_id: UUID | None = None
    is_active: bool | None = None


class ClubStatusTransition(BaseModel):
    status: str = Field(..., examples=["ACTIVE", "SUSPENDED", "ARCHIVED"])
    reason: str | None = None


class ClubResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    campus_id: UUID | None = None
    code: str
    name: str
    slug: str
    category: str
    description: str | None = None
    logo_document_id: UUID | None = None
    faculty_advisor_id: UUID | None = None
    faculty_advisor_name: str | None = None
    student_lead_id: UUID | None = None
    student_lead_name: str | None = None
    status: str
    is_active: bool
    members_count: int = 0
    events_count: int = 0
    created_at: datetime
    updated_at: datetime


class ClubDetailResponse(ClubResponse):
    user_membership_status: str | None = None  # None, PENDING, ACTIVE, REJECTED, LEFT
    user_membership_role: str | None = None


# -----------------------------------------------------------------------------
# 7. CLUB MEMBERSHIP
# -----------------------------------------------------------------------------
class ClubMembershipRequest(BaseModel):
    role: str = Field("MEMBER", examples=["MEMBER", "EVENT_COORDINATOR", "SECRETARY"])


class ClubMembershipReview(BaseModel):
    status: str = Field(..., examples=["ACTIVE", "REJECTED"])
    role: str | None = Field(None, examples=["MEMBER", "PRESIDENT", "VICE_PRESIDENT", "SECRETARY", "TREASURER", "EVENT_COORDINATOR"])
    rejection_reason: str | None = None


class ClubMembershipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    club_id: UUID
    student_id: UUID
    role: str
    status: str
    joined_at: datetime | None = None
    left_at: datetime | None = None
    rejection_reason: str | None = None
    student_name: str | None = None
    student_roll_number: str | None = None
    student_email: str | None = None
    approved_by_name: str | None = None
    created_at: datetime


# -----------------------------------------------------------------------------
# 8. ANNOUNCEMENTS & TARGETED AUDIENCES
# -----------------------------------------------------------------------------
class AnnouncementAudienceItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    target_type: str = Field(
        ...,
        examples=[
            "ALL_USERS", "ALL_STUDENTS", "ALL_FACULTY", "ALL_STAFF",
            "CAMPUS", "DEPARTMENT", "PROGRAM", "ACADEMIC_YEAR",
            "SEMESTER", "SECTION", "CLUB", "INDIVIDUAL_USERS"
        ]
    )
    target_id: UUID | None = None
    filter_metadata: dict | list | None = None


class AnnouncementCreate(BaseModel):
    title: str = Field(..., max_length=255, examples=["Campus Holiday Notice"])
    summary: str | None = None
    content: str
    priority: str = Field("NORMAL", examples=["LOW", "NORMAL", "HIGH", "URGENT"])
    status: str = Field("PUBLISHED", examples=["DRAFT", "SCHEDULED", "PUBLISHED"])
    publish_at: datetime | None = None
    expires_at: datetime | None = None
    is_pinned: bool = False
    audiences: list[AnnouncementAudienceItem] = Field(default_factory=lambda: [AnnouncementAudienceItem(target_type="ALL_USERS")])


class AnnouncementUpdate(BaseModel):
    title: str | None = Field(None, max_length=255)
    summary: str | None = None
    content: str | None = None
    priority: str | None = None
    status: str | None = None
    publish_at: datetime | None = None
    expires_at: datetime | None = None
    is_pinned: bool | None = None
    audiences: list[AnnouncementAudienceItem] | None = None


class AnnouncementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    title: str
    summary: str | None = None
    content: str
    priority: str
    status: str
    publish_at: datetime
    expires_at: datetime | None = None
    is_pinned: bool
    created_by_user_id: UUID
    created_by_name: str | None = None
    published_by_name: str | None = None
    published_at: datetime | None = None
    audiences: list[AnnouncementAudienceItem] = []
    estimated_recipients: int = 0
    created_at: datetime
    updated_at: datetime


class AudiencePreviewRequest(BaseModel):
    audiences: list[AnnouncementAudienceItem]


class AudiencePreviewResponse(BaseModel):
    total_recipients: int
    students_count: int
    faculty_count: int
    staff_count: int
    sample_recipients: list[dict]  # list of {"name": str, "email": str, "role": str}


# -----------------------------------------------------------------------------
# 9. NOTIFICATIONS & PREFERENCES
# -----------------------------------------------------------------------------
class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    recipient_user_id: UUID
    type: str
    title: str
    message: str
    priority: str
    action_url: str | None = None
    source_module: str
    source_entity_type: str | None = None
    source_entity_id: UUID | None = None
    channel: str = "IN_APP"
    is_read: bool
    read_at: datetime | None = None
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    unread_count: int
    total: int
    page: int
    limit: int


class UnreadCountResponse(BaseModel):
    unread_count: int


class NotificationPreferenceItem(BaseModel):
    category: str = Field(..., examples=["ACADEMIC", "ATTENDANCE", "FINANCE", "PLACEMENT", "EVENTS", "CLUBS", "ANNOUNCEMENTS"])
    channel: str = Field("IN_APP", examples=["IN_APP", "EMAIL", "PUSH", "SMS"])
    is_enabled: bool = True
    is_mandatory: bool = False  # E.g. SECURITY and SYSTEM cannot be disabled


class NotificationPreferenceUpdate(BaseModel):
    preferences: list[NotificationPreferenceItem]


# -----------------------------------------------------------------------------
# 10. CAMPUS DASHBOARD
# -----------------------------------------------------------------------------
class CampusDashboardStats(BaseModel):
    upcoming_events_count: int
    open_registrations_count: int
    registered_participants_count: int
    active_clubs_count: int
    pending_club_requests_count: int
    published_announcements_count: int
    unread_notifications_count: int
    events_this_month_count: int
