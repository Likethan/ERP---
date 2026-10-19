"""Campus Events, Clubs, Communication, and Notification Domain Models.

Enterprise models for campus events, categories, physical venues, registrations,
event check-in and attendance, student clubs, memberships, institutional announcements,
targeted audience mapping, unified notification inbox, delivery tracking, and user preferences.
"""

from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, BaseModel, TenantScopedModel

# Cross-dialect JSON type for PostgreSQL JSONB and SQLite JSON
JSONType = JSONB().with_variant(Text, "sqlite")


class EventCategory(TenantScopedModel):
    """Configurable event category taxonomy (Technical, Cultural, Sports, Workshop, etc.)."""

    __tablename__ = "campus_event_categories"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_campus_event_cat_tenant_code"),
        Index("ix_campus_event_cat_tenant_active", "tenant_id", "is_active"),
    )

    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    events: Mapped[list["CampusEvent"]] = relationship(back_populates="category")


class EventVenue(TenantScopedModel):
    """Reusable physical venue or hall located on a campus."""

    __tablename__ = "campus_event_venues"
    __table_args__ = (
        UniqueConstraint("tenant_id", "campus_id", "code", name="uq_campus_venues_tenant_campus_code"),
        Index("ix_campus_venues_tenant_status", "tenant_id", "status"),
    )

    campus_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    building: Mapped[str] = mapped_column(String(128), nullable=False)
    floor: Mapped[str | None] = mapped_column(String(32), nullable=True)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    location_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default="ACTIVE", nullable=False
    )  # ACTIVE, MAINTENANCE, INACTIVE

    campus = relationship("Campus")
    events: Mapped[list["CampusEvent"]] = relationship(back_populates="venue_rel")


class CampusEvent(TenantScopedModel):
    """Campus symposium, workshop, hackathon, cultural fest, or student gathering."""

    __tablename__ = "campus_events"
    __table_args__ = (
        UniqueConstraint("tenant_id", "slug", name="uq_campus_events_tenant_slug"),
        Index("ix_campus_events_tenant_status", "tenant_id", "status"),
        Index("ix_campus_events_tenant_dates", "tenant_id", "start_at", "end_at"),
        Index("ix_campus_events_tenant_campus", "tenant_id", "campus_id"),
    )

    campus_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="CASCADE"),
        nullable=False,
    )
    category_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("campus_event_categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    organizer_type: Mapped[str] = mapped_column(
        String(32), default="INSTITUTION", nullable=False
    )  # INSTITUTION, CAMPUS, DEPARTMENT, CLUB, PLACEMENT, STUDENT_ORG, OTHER
    organizer_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    club_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("campus_clubs.id", ondelete="SET NULL"),
        nullable=True,
    )
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    registration_open_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    registration_close_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    venue_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("campus_event_venues.id", ondelete="SET NULL"),
        nullable=True,
    )
    venue_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default="DRAFT", nullable=False
    )  # DRAFT, PUBLISHED, REGISTRATION_OPEN, REGISTRATION_CLOSED, ONGOING, COMPLETED, CANCELLED, ARCHIVED
    visibility: Mapped[str] = mapped_column(
        String(32), default="CAMPUS", nullable=False
    )  # PUBLIC, INSTITUTION, CAMPUS, DEPARTMENT, PROGRAM, SECTION, CLUB, PRIVATE
    requires_registration: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    requires_attendance: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    target_filter_json: Mapped[dict | list | None] = mapped_column(JSONType, nullable=True)
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Backward compatibility properties
    @property
    def start_time(self) -> datetime:
        return self.start_at

    @property
    def end_time(self) -> datetime:
        return self.end_at

    @property
    def venue(self) -> str:
        if self.venue_name:
            return self.venue_name
        return "Auditorium / Campus Grounds"

    @property
    def event_type(self) -> str:
        return self.organizer_type

    @property
    def is_public(self) -> bool:
        return self.visibility in ("PUBLIC", "INSTITUTION", "CAMPUS")

    campus = relationship("Campus")
    category: Mapped["EventCategory | None"] = relationship(back_populates="events")
    venue_rel: Mapped["EventVenue | None"] = relationship(back_populates="events", foreign_keys=[venue_id])
    club: Mapped["Club | None"] = relationship(back_populates="events")
    department = relationship("Department")
    created_by = relationship("User")
    registrations: Mapped[list["EventRegistration"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )
    attendances: Mapped[list["EventAttendance"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )


# Alias
Event = CampusEvent


class EventRegistration(TenantScopedModel):
    """Participant registration and attendance record for a campus event."""

    __tablename__ = "campus_event_registrations"
    __table_args__ = (
        UniqueConstraint("event_id", "student_id", name="uq_event_registration_student"),
        Index("ix_campus_registrations_tenant_event", "tenant_id", "event_id", "status"),
        Index("ix_campus_registrations_tenant_student", "tenant_id", "student_id"),
    )

    event_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("campus_events.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="CASCADE"),
        nullable=False,
    )
    registration_code: Mapped[str] = mapped_column(String(64), nullable=False)
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="REGISTERED", nullable=False
    )  # REGISTERED, WAITLISTED, CONFIRMED, CANCELLED, ATTENDED, NO_SHOW
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    attended: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    event: Mapped["CampusEvent"] = relationship(back_populates="registrations")
    student = relationship("StudentProfile")
    attendance: Mapped["EventAttendance | None"] = relationship(
        back_populates="registration", uselist=False
    )


class EventAttendance(TenantScopedModel):
    """Event attendance and participation verification (distinct from academic attendance)."""

    __tablename__ = "campus_event_attendances"
    __table_args__ = (
        UniqueConstraint("event_id", "student_id", name="uq_event_attendance_student"),
        Index("ix_campus_attendance_tenant_event", "tenant_id", "event_id"),
        Index("ix_campus_attendance_tenant_student", "tenant_id", "student_id"),
    )

    event_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("campus_events.id", ondelete="CASCADE"),
        nullable=False,
    )
    registration_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("campus_event_registrations.id", ondelete="SET NULL"),
        nullable=True,
    )
    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="CASCADE"),
        nullable=False,
    )
    checked_in_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    checked_out_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attendance_status: Mapped[str] = mapped_column(
        String(32), default="PRESENT", nullable=False
    )  # PRESENT, LATE, EXCUSED, LEFT_EARLY
    marked_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    verification_method: Mapped[str] = mapped_column(
        String(32), default="MANUAL", nullable=False
    )  # MANUAL, QR, NFC, IMPORT, OTHER
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    event: Mapped["CampusEvent"] = relationship(back_populates="attendances")
    registration: Mapped["EventRegistration | None"] = relationship(back_populates="attendance")
    student = relationship("StudentProfile")
    marked_by = relationship("User")


class Club(TenantScopedModel):
    """Student club or co-curricular organization."""

    __tablename__ = "campus_clubs"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_clubs_tenant_code"),
        Index("ix_campus_clubs_tenant_status", "tenant_id", "status"),
        Index("ix_campus_clubs_tenant_category", "tenant_id", "category"),
    )

    campus_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core_campuses.id", ondelete="SET NULL"),
        nullable=True,
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(
        String(32), default="TECHNICAL", nullable=False
    )  # TECHNICAL, CULTURAL, SPORTS, SOCIAL, ACADEMIC, ENTREPRENEURSHIP, LITERARY, OTHER
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    logo_document_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    faculty_advisor_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_faculty.id", ondelete="SET NULL"),
        nullable=True,
    )
    student_lead_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32), default="ACTIVE", nullable=False
    )  # DRAFT, PENDING_APPROVAL, ACTIVE, SUSPENDED, ARCHIVED
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    campus = relationship("Campus")
    faculty_advisor = relationship("FacultyProfile")
    student_lead = relationship("StudentProfile")
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    approved_by = relationship("User", foreign_keys=[approved_by_user_id])
    memberships: Mapped[list["ClubMembership"]] = relationship(
        back_populates="club", cascade="all, delete-orphan"
    )
    events: Mapped[list["CampusEvent"]] = relationship(back_populates="club")


class ClubMembership(TenantScopedModel):
    """Student membership and leadership within a collegiate club."""

    __tablename__ = "campus_club_memberships"
    __table_args__ = (
        UniqueConstraint("club_id", "student_id", name="uq_campus_club_membership_student"),
        Index("ix_campus_club_memberships_tenant_club", "tenant_id", "club_id", "status"),
        Index("ix_campus_club_memberships_tenant_student", "tenant_id", "student_id"),
    )

    club_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("campus_clubs.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_students.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(32), default="MEMBER", nullable=False
    )  # MEMBER, PRESIDENT, VICE_PRESIDENT, SECRETARY, TREASURER, EVENT_COORDINATOR, OTHER
    status: Mapped[str] = mapped_column(
        String(32), default="ACTIVE", nullable=False
    )  # PENDING, ACTIVE, REJECTED, SUSPENDED, LEFT
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    @property
    def joined_date(self) -> date:
        if self.joined_at:
            return self.joined_at.date()
        return self.created_at.date()

    club: Mapped["Club"] = relationship(back_populates="memberships")
    student = relationship("StudentProfile")
    approved_by = relationship("User")


class CampusAnnouncement(TenantScopedModel):
    """Institutional targeted broadcast notice."""

    __tablename__ = "campus_announcements"
    __table_args__ = (
        Index("ix_campus_announcements_tenant_status", "tenant_id", "status", "publish_at"),
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(
        String(16), default="NORMAL", nullable=False
    )  # LOW, NORMAL, HIGH, URGENT
    status: Mapped[str] = mapped_column(
        String(32), default="PUBLISHED", nullable=False
    )  # DRAFT, SCHEDULED, PUBLISHED, EXPIRED, ARCHIVED, CANCELLED
    publish_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    published_by_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Legacy support
    target_audience_type: Mapped[str] = mapped_column(String(32), default="ALL", nullable=False)
    target_filter_json: Mapped[dict | None] = mapped_column(JSONType, nullable=True)

    created_by = relationship("User", foreign_keys=[created_by_user_id])
    published_by = relationship("User", foreign_keys=[published_by_user_id])
    audiences: Mapped[list["AnnouncementAudience"]] = relationship(
        back_populates="announcement", cascade="all, delete-orphan"
    )


# Alias
Announcement = CampusAnnouncement


class AnnouncementAudience(TenantScopedModel):
    """Granular targeted audience criteria for a campus announcement."""

    __tablename__ = "campus_announcement_audiences"
    __table_args__ = (
        Index("ix_campus_audiences_announcement", "announcement_id", "target_type"),
    )

    announcement_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("campus_announcements.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_type: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # ALL_USERS, ALL_STUDENTS, ALL_FACULTY, ALL_STAFF, CAMPUS, DEPARTMENT, PROGRAM, ACADEMIC_YEAR, SEMESTER, SECTION, CLUB, INDIVIDUAL_USERS
    target_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    filter_metadata: Mapped[dict | list | None] = mapped_column(JSONType, nullable=True)

    announcement: Mapped["CampusAnnouncement"] = relationship(back_populates="audiences")


class Notification(TenantScopedModel):
    """Personalized user inbox notification item."""

    __tablename__ = "campus_notifications"
    __table_args__ = (
        Index("ix_campus_notif_tenant_user_read", "tenant_id", "recipient_user_id", "is_read"),
        Index("ix_campus_notif_tenant_user_created", "tenant_id", "recipient_user_id", "created_at"),
        Index("ix_campus_notif_dedup", "deduplication_key"),
        Index("idx_perf_notif_tenant_recipient_unread", "tenant_id", "recipient_user_id", "is_read", "created_at"),
    )

    recipient_user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="CASCADE"),
        nullable=False,
    )
    announcement_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("campus_announcements.id", ondelete="SET NULL"),
        nullable=True,
    )
    type: Mapped[str] = mapped_column(
        String(32), default="SYSTEM", nullable=False
    )  # SYSTEM, ANNOUNCEMENT, EVENT, ACADEMIC, ATTENDANCE, EXAMINATION, FINANCE, PLACEMENT, CLUB, SECURITY, OTHER
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(
        String(16), default="NORMAL", nullable=False
    )  # LOW, NORMAL, HIGH, URGENT
    action_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_module: Mapped[str] = mapped_column(
        String(32), default="SYSTEM", nullable=False
    )  # ATTENDANCE, EXAMINATION, FINANCE, PLACEMENT, EVENTS, CLUBS, ANNOUNCEMENTS, SYSTEM, SECURITY, OTHER
    source_entity_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_entity_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    deduplication_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    channel: Mapped[str] = mapped_column(
        String(16), default="IN_APP", nullable=False
    )  # IN_APP, EMAIL, SMS, PUSH
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Compatibility alias for user_id
    @hybrid_property
    def user_id(self) -> UUID:
        return self.recipient_user_id

    @user_id.setter
    def user_id(self, val: UUID) -> None:
        self.recipient_user_id = val

    @hybrid_property
    def notification_type(self) -> str:
        return self.type

    @notification_type.setter
    def notification_type(self, val: str) -> None:
        self.type = val

    recipient = relationship("User", foreign_keys=[recipient_user_id])
    announcement = relationship("CampusAnnouncement", foreign_keys=[announcement_id])
    deliveries: Mapped[list["NotificationDelivery"]] = relationship(
        back_populates="notification", cascade="all, delete-orphan"
    )


class NotificationDelivery(TenantScopedModel):
    """Delivery log and dispatch status for specific notification channels."""

    __tablename__ = "campus_notification_deliveries"
    __table_args__ = (
        Index("ix_campus_deliveries_notification_channel", "notification_id", "channel"),
        Index("ix_campus_deliveries_tenant_status", "tenant_id", "status"),
        Index("ix_campus_deliveries_tenant_scheduled", "tenant_id", "status", "scheduled_at"),
        Index("ix_campus_deliveries_idempotency", "tenant_id", "idempotency_key"),
        Index("ix_campus_deliveries_event", "tenant_id", "event_id"),
    )

    notification_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("campus_notifications.id", ondelete="CASCADE"),
        nullable=True,
    )
    event_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("notification_events.id", ondelete="SET NULL"),
        nullable=True,
    )
    recipient_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    template_version_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("notification_template_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    channel: Mapped[str] = mapped_column(
        String(16), default="IN_APP", nullable=False
    )  # IN_APP, EMAIL, PUSH, SMS
    status: Mapped[str] = mapped_column(
        String(32), default="PENDING", nullable=False
    )  # PENDING, SCHEDULED, PROCESSING, SUBMITTED, DELIVERED, RETRY_WAIT, FAILED, SUPPRESSED, CANCELLED, READ
    provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    provider_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_classification: Mapped[str | None] = mapped_column(String(64), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    suppression_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rendered_subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rendered_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | list | None] = mapped_column(JSONType, nullable=True)

    notification: Mapped["Notification | None"] = relationship(back_populates="deliveries")
    recipient = relationship("User", foreign_keys=[recipient_user_id])
    template_version = relationship("NotificationTemplateVersion", foreign_keys=[template_version_id])
    event = relationship("NotificationEvent", foreign_keys=[event_id])
    attempts: Mapped[list["NotificationDeliveryAttempt"]] = relationship(
        "NotificationDeliveryAttempt",
        back_populates="delivery",
        cascade="all, delete-orphan",
        order_by="NotificationDeliveryAttempt.attempt_number",
        lazy="selectin",
    )


class NotificationPreference(TenantScopedModel):
    """User channel delivery preferences per notification category."""

    __tablename__ = "campus_notification_preferences"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "user_id", "category", "channel",
            name="uq_campus_notif_pref_user_cat_chan",
        ),
        Index("ix_campus_preferences_user", "tenant_id", "user_id"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people_users.id", ondelete="CASCADE"),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # ACADEMIC, ATTENDANCE, FINANCE, PLACEMENT, EVENTS, CLUBS, ANNOUNCEMENTS
    channel: Mapped[str] = mapped_column(
        String(16), default="IN_APP", nullable=False
    )  # IN_APP, EMAIL, PUSH, SMS
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user = relationship("User")
