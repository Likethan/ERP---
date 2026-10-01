"""Campus Events, Clubs, and Announcements Core Service Layer.

Implements production-grade event scheduling, venue conflict detection, capacity checks,
student self-registration, event check-in/attendance, club lifecycle governance,
membership workflows, targeted announcement audience resolution, and dashboard metrics.
"""

import hashlib
import hmac
import time
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.exceptions import (
    ConflictException,
    NotFoundException,
    PermissionDeniedException,
    ValidationException,
)


def _normalize_dt(dt: datetime | None) -> datetime | None:
    """Ensure datetime is UTC timezone-aware for consistent cross-database comparisons."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt
from app.models.audit import AuditLog
from app.models.campus import (
    AnnouncementAudience,
    CampusAnnouncement,
    CampusEvent,
    Club,
    ClubMembership,
    EventAttendance,
    EventCategory,
    EventRegistration,
    EventVenue,
    Notification,
)
from app.models.core import Campus, Department, Program, Section, Semester
from app.models.people import FacultyProfile, StaffProfile, StudentProfile, User
from app.schemas.campus import (
    AnnouncementAudienceItem,
    AnnouncementCreate,
    AnnouncementUpdate,
    AudiencePreviewResponse,
    ClubCreate,
    ClubMembershipRequest,
    ClubMembershipReview,
    ClubUpdate,
    EventCategoryCreate,
    EventCategoryUpdate,
    EventCheckInRequest,
    EventCreate,
    EventRegistrationCancel,
    EventUpdate,
    EventVenueCreate,
    EventVenueUpdate,
)
from app.services.notification_service import NotificationService


class CampusService:
    """Comprehensive service governing Campus Events, Clubs, and Communication."""

    @staticmethod
    def _create_audit(
        tenant_id: UUID,
        user_id: UUID | None,
        action: str,
        entity_type: str,
        entity_id: UUID,
        details: dict | None = None,
    ) -> AuditLog:
        return AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            new_values_json=details,
            ip_address="127.0.0.1",
            business_context="Campus Domain",
        )

    # =========================================================================
    # 1. EVENT CATEGORIES
    # =========================================================================
    @classmethod
    async def list_categories(
        cls, db: AsyncSession, tenant_id: UUID, active_only: bool = False
    ) -> list[EventCategory]:
        conditions = [EventCategory.tenant_id == tenant_id]
        if active_only:
            conditions.append(EventCategory.is_active.is_(True))
        stmt = select(EventCategory).where(and_(*conditions)).order_by(EventCategory.name.asc())
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @classmethod
    async def create_category(
        cls, db: AsyncSession, tenant_id: UUID, data: EventCategoryCreate, user_id: UUID
    ) -> EventCategory:
        # Check duplicate code
        exist_stmt = select(EventCategory).where(
            and_(
                EventCategory.tenant_id == tenant_id,
                EventCategory.code == data.code.upper(),
            )
        )
        if (await db.execute(exist_stmt)).scalar_one_or_none():
            raise ConflictException(f"Category code '{data.code}' already exists.")

        cat = EventCategory(
            id=uuid4(),
            tenant_id=tenant_id,
            code=data.code.upper(),
            name=data.name,
            description=data.description,
            is_active=data.is_active,
        )
        db.add(cat)
        db.add(
            cls._create_audit(
                tenant_id, user_id, "EVENT_CATEGORY_CREATED", "EventCategory", cat.id, {"code": cat.code}
            )
        )
        await db.commit()
        await db.refresh(cat)
        return cat

    @classmethod
    async def update_category(
        cls, db: AsyncSession, tenant_id: UUID, category_id: UUID, data: EventCategoryUpdate, user_id: UUID
    ) -> EventCategory:
        stmt = select(EventCategory).where(
            and_(EventCategory.id == category_id, EventCategory.tenant_id == tenant_id)
        )
        cat = (await db.execute(stmt)).scalar_one_or_none()
        if not cat:
            raise NotFoundException("EventCategory", category_id)

        if data.name is not None:
            cat.name = data.name
        if data.description is not None:
            cat.description = data.description
        if data.is_active is not None:
            cat.is_active = data.is_active

        db.add(
            cls._create_audit(
                tenant_id, user_id, "EVENT_CATEGORY_UPDATED", "EventCategory", cat.id, {"name": cat.name}
            )
        )
        await db.commit()
        await db.refresh(cat)
        return cat

    # =========================================================================
    # 2. EVENT VENUES & CONFLICT DETECTION
    # =========================================================================
    @classmethod
    async def list_venues(
        cls, db: AsyncSession, tenant_id: UUID, campus_id: UUID | None = None, status: str | None = None
    ) -> list[EventVenue]:
        conditions = [EventVenue.tenant_id == tenant_id]
        if campus_id:
            conditions.append(EventVenue.campus_id == campus_id)
        if status:
            conditions.append(EventVenue.status == status.upper())
        stmt = select(EventVenue).where(and_(*conditions)).order_by(EventVenue.name.asc())
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @classmethod
    async def create_venue(
        cls, db: AsyncSession, tenant_id: UUID, data: EventVenueCreate, user_id: UUID
    ) -> EventVenue:
        # Verify campus belongs to tenant
        campus = await db.get(Campus, data.campus_id)
        if not campus or campus.tenant_id != tenant_id:
            raise ValidationException("Invalid campus selected for venue.")

        # Check unique code within campus
        exist_stmt = select(EventVenue).where(
            and_(
                EventVenue.tenant_id == tenant_id,
                EventVenue.campus_id == data.campus_id,
                EventVenue.code == data.code.upper(),
            )
        )
        if (await db.execute(exist_stmt)).scalar_one_or_none():
            raise ConflictException(f"Venue code '{data.code}' already exists on this campus.")

        venue = EventVenue(
            id=uuid4(),
            tenant_id=tenant_id,
            campus_id=data.campus_id,
            name=data.name,
            code=data.code.upper(),
            building=data.building,
            floor=data.floor,
            capacity=data.capacity,
            location_description=data.location_description,
            status=data.status.upper(),
        )
        db.add(venue)
        db.add(
            cls._create_audit(
                tenant_id, user_id, "EVENT_VENUE_CREATED", "EventVenue", venue.id, {"name": venue.name}
            )
        )
        await db.commit()
        await db.refresh(venue)
        return venue

    @classmethod
    async def update_venue(
        cls, db: AsyncSession, tenant_id: UUID, venue_id: UUID, data: EventVenueUpdate, user_id: UUID
    ) -> EventVenue:
        stmt = select(EventVenue).where(and_(EventVenue.id == venue_id, EventVenue.tenant_id == tenant_id))
        venue = (await db.execute(stmt)).scalar_one_or_none()
        if not venue:
            raise NotFoundException("EventVenue", venue_id)

        if data.name is not None:
            venue.name = data.name
        if data.code is not None:
            venue.code = data.code.upper()
        if data.building is not None:
            venue.building = data.building
        if data.floor is not None:
            venue.floor = data.floor
        if data.capacity is not None:
            venue.capacity = data.capacity
        if data.location_description is not None:
            venue.location_description = data.location_description
        if data.status is not None:
            venue.status = data.status.upper()

        db.add(
            cls._create_audit(
                tenant_id, user_id, "EVENT_VENUE_UPDATED", "EventVenue", venue.id, {"status": venue.status}
            )
        )
        await db.commit()
        await db.refresh(venue)
        return venue

    @classmethod
    async def validate_venue_conflict(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        venue_id: UUID,
        start_at: datetime,
        end_at: datetime,
        exclude_event_id: UUID | None = None,
    ) -> None:
        """Enforces that no two non-cancelled events overlap at the same venue."""
        conditions = [
            CampusEvent.tenant_id == tenant_id,
            CampusEvent.venue_id == venue_id,
            CampusEvent.status.notin_(["CANCELLED", "ARCHIVED"]),
            # Overlap: (existing.start < new.end) AND (existing.end > new.start)
            CampusEvent.start_at < end_at,
            CampusEvent.end_at > start_at,
        ]
        if exclude_event_id:
            conditions.append(CampusEvent.id != exclude_event_id)

        conflict_stmt = select(CampusEvent).where(and_(*conditions))
        conflict = (await db.execute(conflict_stmt)).scalar_one_or_none()
        if conflict:
            raise ValidationException(
                f"Venue conflict: Venue is already booked for '{conflict.title}' "
                f"from {conflict.start_at.strftime('%Y-%m-%d %H:%M')} to {conflict.end_at.strftime('%Y-%m-%d %H:%M')}."
            )

    # =========================================================================
    # 3. CAMPUS EVENTS LIFECYCLE
    # =========================================================================
    @classmethod
    async def create_event(
        cls, db: AsyncSession, tenant_id: UUID, data: EventCreate, user_id: UUID
    ) -> CampusEvent:
        if data.start_at >= data.end_at:
            raise ValidationException("Event start time must precede end time.")

        if data.registration_open_at and data.registration_close_at:
            if data.registration_open_at >= data.registration_close_at:
                raise ValidationException("Registration open time must precede close time.")
            if data.registration_close_at > data.start_at:
                raise ValidationException("Registration must close before or when the event starts.")

        # Validate Campus
        campus = await db.get(Campus, data.campus_id)
        if not campus or campus.tenant_id != tenant_id:
            raise ValidationException("Invalid campus specified.")

        # Venue Conflict & Capacity Checks
        venue: EventVenue | None = None
        if data.venue_id:
            venue = await db.get(EventVenue, data.venue_id)
            if not venue or venue.tenant_id != tenant_id:
                raise ValidationException("Specified venue does not exist.")
            if venue.campus_id != data.campus_id:
                raise ValidationException("Venue does not belong to the selected campus.")
            if venue.status != "ACTIVE":
                raise ValidationException(f"Venue '{venue.name}' is currently {venue.status}.")

            # Validate capacity
            if data.capacity and data.capacity > venue.capacity:
                raise ValidationException(
                    f"Requested event capacity ({data.capacity}) exceeds venue maximum capacity ({venue.capacity})."
                )

            # Check overlap
            await cls.validate_venue_conflict(
                db, tenant_id, data.venue_id, data.start_at, data.end_at
            )

        # Generate unique slug
        base_slug = data.slug or data.title.lower().replace(" ", "-").replace("/", "-")
        clean_slug = "".join(c for c in base_slug if c.isalnum() or c == "-").strip("-")
        slug = clean_slug
        count = 1
        while True:
            exist_slug = (
                await db.execute(
                    select(CampusEvent).where(
                        and_(CampusEvent.tenant_id == tenant_id, CampusEvent.slug == slug)
                    )
                )
            ).scalar_one_or_none()
            if not exist_slug:
                break
            slug = f"{clean_slug}-{count}"
            count += 1

        event = CampusEvent(
            id=uuid4(),
            tenant_id=tenant_id,
            campus_id=data.campus_id,
            category_id=data.category_id,
            title=data.title,
            slug=slug,
            description=data.description,
            organizer_type=data.organizer_type.upper(),
            organizer_id=data.organizer_id,
            department_id=data.department_id,
            club_id=data.club_id,
            start_at=data.start_at,
            end_at=data.end_at,
            registration_open_at=data.registration_open_at,
            registration_close_at=data.registration_close_at,
            venue_id=data.venue_id,
            venue_name=data.venue_name or (venue.name if venue else None),
            capacity=data.capacity or (venue.capacity if venue else None),
            status="DRAFT",
            visibility=data.visibility.upper(),
            requires_registration=data.requires_registration,
            requires_attendance=data.requires_attendance,
            target_filter_json=data.target_filter_json,
            created_by_user_id=user_id,
        )
        db.add(event)
        db.add(
            cls._create_audit(
                tenant_id, user_id, "EVENT_CREATED", "CampusEvent", event.id, {"title": event.title}
            )
        )
        await db.commit()
        await db.refresh(event)
        return event

    @classmethod
    async def update_event(
        cls, db: AsyncSession, tenant_id: UUID, event_id: UUID, data: EventUpdate, user_id: UUID
    ) -> CampusEvent:
        stmt = select(CampusEvent).where(
            and_(CampusEvent.id == event_id, CampusEvent.tenant_id == tenant_id)
        )
        event = (await db.execute(stmt)).scalar_one_or_none()
        if not event:
            raise NotFoundException("CampusEvent", event_id)

        new_start = data.start_at or event.start_at
        new_end = data.end_at or event.end_at
        if new_start >= new_end:
            raise ValidationException("Event start time must precede end time.")

        new_venue_id = data.venue_id if data.venue_id is not None else event.venue_id

        # Re-check venue conflict if time or venue changed
        if new_venue_id:
            venue = await db.get(EventVenue, new_venue_id)
            if not venue or venue.tenant_id != tenant_id:
                raise ValidationException("Specified venue does not exist.")
            new_capacity = data.capacity if data.capacity is not None else event.capacity
            if new_capacity and new_capacity > venue.capacity:
                raise ValidationException(
                    f"Requested capacity ({new_capacity}) exceeds venue limit ({venue.capacity})."
                )
            if (
                data.start_at is not None
                or data.end_at is not None
                or data.venue_id is not None
            ):
                await cls.validate_venue_conflict(
                    db, tenant_id, new_venue_id, new_start, new_end, exclude_event_id=event.id
                )

        if data.title is not None:
            event.title = data.title
        if data.description is not None:
            event.description = data.description
        if data.category_id is not None:
            event.category_id = data.category_id
        if data.organizer_type is not None:
            event.organizer_type = data.organizer_type.upper()
        if data.organizer_id is not None:
            event.organizer_id = data.organizer_id
        if data.department_id is not None:
            event.department_id = data.department_id
        if data.club_id is not None:
            event.club_id = data.club_id
        if data.start_at is not None:
            event.start_at = data.start_at
        if data.end_at is not None:
            event.end_at = data.end_at
        if data.registration_open_at is not None:
            event.registration_open_at = data.registration_open_at
        if data.registration_close_at is not None:
            event.registration_close_at = data.registration_close_at
        if data.venue_id is not None:
            event.venue_id = data.venue_id
        if data.venue_name is not None:
            event.venue_name = data.venue_name
        if data.capacity is not None:
            event.capacity = data.capacity
        if data.visibility is not None:
            event.visibility = data.visibility.upper()
        if data.requires_registration is not None:
            event.requires_registration = data.requires_registration
        if data.requires_attendance is not None:
            event.requires_attendance = data.requires_attendance
        if data.target_filter_json is not None:
            event.target_filter_json = data.target_filter_json
        if data.status is not None:
            event.status = data.status.upper()

        db.add(
            cls._create_audit(
                tenant_id, user_id, "EVENT_UPDATED", "CampusEvent", event.id, {"title": event.title}
            )
        )
        await db.commit()
        await db.refresh(event)
        return event

    @classmethod
    async def publish_event(
        cls, db: AsyncSession, tenant_id: UUID, event_id: UUID, user_id: UUID
    ) -> CampusEvent:
        stmt = select(CampusEvent).where(
            and_(CampusEvent.id == event_id, CampusEvent.tenant_id == tenant_id)
        )
        event = (await db.execute(stmt)).scalar_one_or_none()
        if not event:
            raise NotFoundException("CampusEvent", event_id)

        now = datetime.now(UTC)
        # Determine status: REGISTRATION_OPEN if window is active, else PUBLISHED
        new_status = "PUBLISHED"
        if event.requires_registration:
            if event.registration_open_at and event.registration_close_at:
                if event.registration_open_at <= now <= event.registration_close_at:
                    new_status = "REGISTRATION_OPEN"
            else:
                new_status = "REGISTRATION_OPEN"

        event.status = new_status
        db.add(
            cls._create_audit(
                tenant_id, user_id, "EVENT_PUBLISHED", "CampusEvent", event.id, {"status": new_status}
            )
        )
        await db.commit()
        await db.refresh(event)
        return event

    @classmethod
    async def cancel_event(
        cls, db: AsyncSession, tenant_id: UUID, event_id: UUID, user_id: UUID, reason: str | None = None
    ) -> CampusEvent:
        stmt = select(CampusEvent).where(
            and_(CampusEvent.id == event_id, CampusEvent.tenant_id == tenant_id)
        )
        event = (await db.execute(stmt)).scalar_one_or_none()
        if not event:
            raise NotFoundException("CampusEvent", event_id)

        now = datetime.now(UTC)
        event.status = "CANCELLED"

        # Update registrations
        await db.execute(
            update(EventRegistration)
            .where(
                and_(
                    EventRegistration.event_id == event_id,
                    EventRegistration.status.in_(["REGISTERED", "CONFIRMED", "WAITLISTED"]),
                )
            )
            .values(
                status="CANCELLED",
                cancelled_at=now,
                cancellation_reason=reason or "Event was cancelled by organizer.",
            )
        )

        db.add(
            cls._create_audit(
                tenant_id, user_id, "EVENT_CANCELLED", "CampusEvent", event.id, {"reason": reason}
            )
        )
        await db.commit()
        await db.refresh(event)
        return event

    @classmethod
    async def list_events(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        campus_id: UUID | None = None,
        category_id: UUID | None = None,
        status: str | None = None,
        organizer_type: str | None = None,
        organizer_id: UUID | None = None,
        search: str | None = None,
        upcoming_only: bool = False,
        page: int = 1,
        limit: int = 20,
    ) -> dict:
        conditions = [CampusEvent.tenant_id == tenant_id]

        if campus_id:
            conditions.append(CampusEvent.campus_id == campus_id)
        if category_id:
            conditions.append(CampusEvent.category_id == category_id)
        if status:
            conditions.append(CampusEvent.status == status.upper())
        if organizer_type:
            conditions.append(CampusEvent.organizer_type == organizer_type.upper())
        if organizer_id:
            conditions.append(CampusEvent.organizer_id == organizer_id)
        if upcoming_only:
            conditions.append(CampusEvent.start_at >= datetime.now(UTC))
        if search:
            search_pattern = f"%{search}%"
            conditions.append(
                or_(
                    CampusEvent.title.ilike(search_pattern),
                    CampusEvent.description.ilike(search_pattern),
                    CampusEvent.venue_name.ilike(search_pattern),
                )
            )

        total_stmt = select(func.count(CampusEvent.id)).where(and_(*conditions))
        total = (await db.execute(total_stmt)).scalar() or 0

        offset = (page - 1) * limit
        stmt = (
            select(CampusEvent)
            .where(and_(*conditions))
            .order_by(CampusEvent.start_at.asc())
            .offset(offset)
            .limit(limit)
        )
        events = (await db.execute(stmt)).scalars().all()

        # Gather counts
        event_ids = [e.id for e in events]
        reg_counts = {}
        att_counts = {}
        if event_ids:
            reg_stmt = (
                select(EventRegistration.event_id, func.count(EventRegistration.id))
                .where(
                    and_(
                        EventRegistration.event_id.in_(event_ids),
                        EventRegistration.status.in_(["REGISTERED", "CONFIRMED", "ATTENDED"]),
                    )
                )
                .group_by(EventRegistration.event_id)
            )
            reg_counts = dict((await db.execute(reg_stmt)).all())

            att_stmt = (
                select(EventAttendance.event_id, func.count(EventAttendance.id))
                .where(EventAttendance.event_id.in_(event_ids))
                .group_by(EventAttendance.event_id)
            )
            att_counts = dict((await db.execute(att_stmt)).all())

        items = []
        for e in events:
            e.registered_count = reg_counts.get(e.id, 0)
            e.attended_count = att_counts.get(e.id, 0)
            items.append(e)

        return {"items": items, "total": total, "page": page, "limit": limit}

    @classmethod
    async def get_event_detail(
        cls, db: AsyncSession, tenant_id: UUID, event_id: UUID, current_user: User | None = None
    ) -> CampusEvent:
        stmt = (
            select(CampusEvent)
            .options(
                selectinload(CampusEvent.category),
                selectinload(CampusEvent.venue_rel),
                selectinload(CampusEvent.club),
            )
            .where(and_(CampusEvent.id == event_id, CampusEvent.tenant_id == tenant_id))
        )
        event = (await db.execute(stmt)).scalar_one_or_none()
        if not event:
            raise NotFoundException("CampusEvent", event_id)

        # Compute registration count
        reg_count_stmt = select(func.count(EventRegistration.id)).where(
            and_(
                EventRegistration.event_id == event_id,
                EventRegistration.status.in_(["REGISTERED", "CONFIRMED", "ATTENDED"]),
            )
        )
        event.registered_count = (await db.execute(reg_count_stmt)).scalar() or 0

        att_count_stmt = select(func.count(EventAttendance.id)).where(
            EventAttendance.event_id == event_id
        )
        event.attended_count = (await db.execute(att_count_stmt)).scalar() or 0

        # Check user registration status
        event.user_registration_status = None
        event.user_registration_id = None
        if current_user:
            student_stmt = select(StudentProfile).where(
                and_(
                    StudentProfile.tenant_id == tenant_id,
                    StudentProfile.user_id == current_user.id,
                )
            )
            student = (await db.execute(student_stmt)).scalar_one_or_none()
            if student:
                reg_stmt = select(EventRegistration).where(
                    and_(
                        EventRegistration.event_id == event_id,
                        EventRegistration.student_id == student.id,
                    )
                )
                user_reg = (await db.execute(reg_stmt)).scalar_one_or_none()
                if user_reg:
                    event.user_registration_status = user_reg.status
                    event.user_registration_id = user_reg.id

        return event

    # =========================================================================
    # 4. EVENT REGISTRATION WORKFLOW
    # =========================================================================
    @classmethod
    async def register_student_for_event(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        event_id: UUID,
        student_id: UUID,
        registered_by_user_id: UUID,
    ) -> EventRegistration:
        """Atomically registers an eligible student for an event."""
        # 1. Load Event
        event = await db.get(CampusEvent, event_id)
        if not event or event.tenant_id != tenant_id:
            raise NotFoundException("CampusEvent", event_id)

        # 2. Check Event Status
        if event.status not in ("PUBLISHED", "REGISTRATION_OPEN"):
            raise ValidationException(
                f"Event '{event.title}' is not open for registration (status: {event.status})."
            )

        # 3. Check Registration Window
        now = datetime.now(UTC)
        reg_open = _normalize_dt(event.registration_open_at)
        reg_close = _normalize_dt(event.registration_close_at)
        evt_start = _normalize_dt(event.start_at)

        if reg_open and now < reg_open:
            raise ValidationException(
                f"Registration has not opened yet. Opens on {reg_open.strftime('%Y-%m-%d %H:%M')}."
            )
        if reg_close and now > reg_close:
            raise ValidationException("Registration for this event has closed.")
        if evt_start and now > evt_start:
            raise ValidationException("Cannot register for an event that has already started.")

        # 4. Validate Student Profile
        student = await db.get(StudentProfile, student_id)
        if not student or student.tenant_id != tenant_id:
            raise NotFoundException("StudentProfile", student_id)
        if student.status not in ("ACTIVE", "ADMITTED"):
            raise ValidationException(f"Student account is not active (status: {student.status}).")

        # 5. Check Eligibility Restrictions (target_filter_json)
        if event.target_filter_json and isinstance(event.target_filter_json, dict):
            allowed_dept_ids = event.target_filter_json.get("department_ids")
            if allowed_dept_ids:
                # Resolve student's department via program
                prog = await db.get(Program, student.program_id)
                if not prog or str(prog.department_id) not in [str(d) for d in allowed_dept_ids]:
                    raise ValidationException("Student is not in an eligible department for this event.")

            allowed_prog_ids = event.target_filter_json.get("program_ids")
            if allowed_prog_ids and str(student.program_id) not in [str(p) for p in allowed_prog_ids]:
                raise ValidationException("Student program is not eligible for this event.")

        # 6. Prevent Duplicate Registration
        existing_stmt = select(EventRegistration).where(
            and_(
                EventRegistration.event_id == event_id,
                EventRegistration.student_id == student_id,
            )
        )
        existing = (await db.execute(existing_stmt)).scalar_one_or_none()
        if existing:
            if existing.status in ("REGISTERED", "CONFIRMED", "WAITLISTED", "ATTENDED"):
                raise ConflictException(
                    f"Student is already registered for this event with status '{existing.status}'."
                )
            elif existing.status == "CANCELLED":
                # Re-activate previously cancelled registration
                existing.status = "REGISTERED"
                existing.cancelled_at = None
                existing.cancellation_reason = None
                existing.registered_at = now
                await db.commit()
                await db.refresh(existing)
                return existing

        # 7. Check Capacity
        target_status = "REGISTERED"
        if event.capacity:
            count_stmt = select(func.count(EventRegistration.id)).where(
                and_(
                    EventRegistration.event_id == event_id,
                    EventRegistration.status.in_(["REGISTERED", "CONFIRMED"]),
                )
            )
            current_count = (await db.execute(count_stmt)).scalar() or 0
            if current_count >= event.capacity:
                raise ValidationException(
                    f"Event capacity limit ({event.capacity}) has been reached. Registration is full."
                )

        # 8. Create Registration
        reg_code = f"REG-{event.slug[:8].upper()}-{uuid4().hex[:6].upper()}"
        registration = EventRegistration(
            id=uuid4(),
            tenant_id=tenant_id,
            event_id=event_id,
            student_id=student_id,
            registration_code=reg_code,
            registered_at=now,
            status=target_status,
            attended=False,
        )
        db.add(registration)

        # 9. Audit & In-App Notification
        db.add(
            cls._create_audit(
                tenant_id,
                registered_by_user_id,
                "EVENT_REGISTRATION_CREATED",
                "EventRegistration",
                registration.id,
                {"event_title": event.title, "registration_code": reg_code},
            )
        )

        # Notify student
        if student.user_id:
            await NotificationService.create_notification(
                db=db,
                tenant_id=tenant_id,
                recipient_user_id=student.user_id,
                type="EVENT",
                title=f"Registration Confirmed: {event.title}",
                message=f"You are registered for '{event.title}' scheduled for {event.start_at.strftime('%b %d, %Y at %I:%M %p')}. Registration Code: {reg_code}",
                priority="NORMAL",
                action_url=f"/app/events/{event.id}",
                source_module="EVENTS",
                source_entity_type="CampusEvent",
                source_entity_id=event.id,
                deduplication_key=f"event_reg_{event.id}_{student.id}",
            )

        await db.commit()
        await db.refresh(registration)
        return registration

    @classmethod
    async def cancel_registration(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        registration_id: UUID,
        user_id: UUID,
        data: EventRegistrationCancel,
        is_staff: bool = False,
    ) -> EventRegistration:
        reg = await db.get(EventRegistration, registration_id)
        if not reg or reg.tenant_id != tenant_id:
            raise NotFoundException("EventRegistration", registration_id)

        # Verify authorization
        student = await db.get(StudentProfile, reg.student_id)
        if not is_staff and (not student or student.user_id != user_id):
            raise PermissionDeniedException("events:self_manage_registration")

        event = await db.get(CampusEvent, reg.event_id)
        if event and event.status == "COMPLETED":
            raise ValidationException("Cannot cancel registration for a completed event.")

        now = datetime.now(UTC)
        reg.status = "CANCELLED"
        reg.cancelled_at = now
        reg.cancellation_reason = data.cancellation_reason or "Cancelled by student"

        db.add(
            cls._create_audit(
                tenant_id, user_id, "EVENT_REGISTRATION_CANCELLED", "EventRegistration", reg.id
            )
        )
        await db.commit()
        await db.refresh(reg)
        return reg

    @classmethod
    async def list_event_registrations(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        event_id: UUID,
        status: str | None = None,
        page: int = 1,
        limit: int = 50,
    ) -> dict:
        conditions = [
            EventRegistration.tenant_id == tenant_id,
            EventRegistration.event_id == event_id,
        ]
        if status:
            conditions.append(EventRegistration.status == status.upper())

        total = (
            await db.execute(select(func.count(EventRegistration.id)).where(and_(*conditions)))
        ).scalar() or 0

        offset = (page - 1) * limit
        stmt = (
            select(EventRegistration)
            .options(selectinload(EventRegistration.student).selectinload(StudentProfile.user))
            .where(and_(*conditions))
            .order_by(EventRegistration.registered_at.asc())
            .offset(offset)
            .limit(limit)
        )
        registrations = (await db.execute(stmt)).scalars().all()

        return {"items": registrations, "total": total, "page": page, "limit": limit}

    # =========================================================================
    # 5. EVENT ATTENDANCE & CHECK-IN ENGINE
    # =========================================================================
    @classmethod
    async def check_in_student(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        event_id: UUID,
        data: EventCheckInRequest,
        marked_by_user_id: UUID,
    ) -> EventAttendance:
        """Mark physical presence and participation for a registered student."""
        # 1. Resolve student and registration
        reg_stmt = select(EventRegistration).where(
            and_(
                EventRegistration.event_id == event_id,
                EventRegistration.tenant_id == tenant_id,
            )
        )
        if data.registration_code:
            reg_stmt = reg_stmt.where(
                EventRegistration.registration_code == data.registration_code.strip()
            )
        elif data.student_id:
            reg_stmt = reg_stmt.where(EventRegistration.student_id == data.student_id)
        else:
            raise ValidationException("Either student_id or registration_code must be provided.")

        registration = (await db.execute(reg_stmt)).scalar_one_or_none()
        if not registration:
            raise NotFoundException("EventRegistration for this student", event_id)

        if registration.status == "CANCELLED":
            raise ValidationException("Cannot check in: Registration was cancelled.")

        # 2. Check duplicate attendance
        att_stmt = select(EventAttendance).where(
            and_(
                EventAttendance.event_id == event_id,
                EventAttendance.student_id == registration.student_id,
            )
        )
        existing_att = (await db.execute(att_stmt)).scalar_one_or_none()
        if existing_att:
            raise ConflictException(
                f"Student has already been checked in at {existing_att.checked_in_at.strftime('%H:%M:%S')}."
            )

        now = datetime.now(UTC)
        attendance = EventAttendance(
            id=uuid4(),
            tenant_id=tenant_id,
            event_id=event_id,
            registration_id=registration.id,
            student_id=registration.student_id,
            checked_in_at=now,
            attendance_status="PRESENT",
            marked_by_user_id=marked_by_user_id,
            verification_method=data.verification_method.upper(),
            remarks=data.remarks,
        )
        db.add(attendance)

        # Update registration status
        registration.status = "ATTENDED"
        registration.attended = True

        db.add(
            cls._create_audit(
                tenant_id,
                marked_by_user_id,
                "EVENT_ATTENDANCE_MARKED",
                "EventAttendance",
                attendance.id,
                {"method": data.verification_method, "student_id": str(registration.student_id)},
            )
        )

        await db.commit()
        await db.refresh(attendance)
        return attendance

    @classmethod
    async def undo_check_in(
        cls, db: AsyncSession, tenant_id: UUID, event_id: UUID, student_id: UUID, user_id: UUID
    ) -> None:
        """Revert mistaken event check-in with supervisor permission."""
        att_stmt = select(EventAttendance).where(
            and_(
                EventAttendance.event_id == event_id,
                EventAttendance.student_id == student_id,
                EventAttendance.tenant_id == tenant_id,
            )
        )
        attendance = (await db.execute(att_stmt)).scalar_one_or_none()
        if not attendance:
            raise NotFoundException("EventAttendance", student_id)

        reg_stmt = select(EventRegistration).where(
            and_(
                EventRegistration.event_id == event_id,
                EventRegistration.student_id == student_id,
            )
        )
        registration = (await db.execute(reg_stmt)).scalar_one_or_none()
        if registration:
            registration.status = "REGISTERED"
            registration.attended = False

        await db.delete(attendance)
        db.add(
            cls._create_audit(
                tenant_id, user_id, "EVENT_ATTENDANCE_REVERTED", "EventAttendance", attendance.id
            )
        )
        await db.commit()

    @classmethod
    def generate_event_qr_token(
        cls, tenant_id: UUID, event_id: UUID, duration_seconds: int = 300
    ) -> dict:
        """Generates a cryptographically signed, short-lived QR check-in token."""
        expires_at = int(time.time()) + duration_seconds
        payload = f"{tenant_id}:{event_id}:{expires_at}:{uuid4().hex[:8]}"
        secret = settings.SECRET_KEY.encode("utf-8")
        signature = hmac.new(secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()
        token = f"{payload}:{signature}"
        return {
            "qr_token": token,
            "event_id": event_id,
            "expires_at": datetime.fromtimestamp(expires_at, UTC),
            "valid_duration_seconds": duration_seconds,
        }

    @classmethod
    async def verify_and_check_in_qr(
        cls, db: AsyncSession, tenant_id: UUID, token: str, student_user_id: UUID
    ) -> EventAttendance:
        """Validates temporary QR token and checks in authenticated student."""
        parts = token.split(":")
        if len(parts) != 5:
            raise ValidationException("Malformed QR check-in token.")

        token_tenant_id, token_event_id, expires_at_str, nonce, signature = parts
        if token_tenant_id != str(tenant_id):
            raise ValidationException("Invalid tenant binding in QR token.")

        expires_at = int(expires_at_str)
        if time.time() > expires_at:
            raise ValidationException("QR check-in token has expired. Please refresh the QR code.")

        payload = f"{token_tenant_id}:{token_event_id}:{expires_at_str}:{nonce}"
        secret = settings.SECRET_KEY.encode("utf-8")
        expected_sig = hmac.new(secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            raise ValidationException("Invalid QR token signature.")

        # Find StudentProfile for this user
        student = (
            await db.execute(
                select(StudentProfile).where(
                    and_(
                        StudentProfile.tenant_id == tenant_id,
                        StudentProfile.user_id == student_user_id,
                    )
                )
            )
        ).scalar_one_or_none()
        if not student:
            raise ValidationException("Only registered students can check in via QR code.")

        event_id = UUID(token_event_id)
        req = EventCheckInRequest(
            student_id=student.id,
            verification_method="QR",
            remarks="Verified via short-lived QR token",
        )
        return await cls.check_in_student(
            db=db,
            tenant_id=tenant_id,
            event_id=event_id,
            data=req,
            marked_by_user_id=student_user_id,
        )

    # =========================================================================
    # 6. CLUB MANAGEMENT & LIFECYCLE
    # =========================================================================
    @classmethod
    async def list_clubs(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        campus_id: UUID | None = None,
        category: str | None = None,
        status: str | None = None,
        search: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> dict:
        conditions = [Club.tenant_id == tenant_id]
        if campus_id:
            conditions.append(Club.campus_id == campus_id)
        if category:
            conditions.append(Club.category == category.upper())
        if status:
            conditions.append(Club.status == status.upper())
        if search:
            search_pat = f"%{search}%"
            conditions.append(or_(Club.name.ilike(search_pat), Club.description.ilike(search_pat)))

        total = (await db.execute(select(func.count(Club.id)).where(and_(*conditions)))).scalar() or 0

        offset = (page - 1) * limit
        stmt = (
            select(Club)
            .options(
                selectinload(Club.faculty_advisor).selectinload(FacultyProfile.user),
                selectinload(Club.student_lead).selectinload(StudentProfile.user),
            )
            .where(and_(*conditions))
            .order_by(Club.name.asc())
            .offset(offset)
            .limit(limit)
        )
        clubs = (await db.execute(stmt)).scalars().all()

        # Members and events counts
        club_ids = [c.id for c in clubs]
        member_counts = {}
        event_counts = {}
        if club_ids:
            mem_stmt = (
                select(ClubMembership.club_id, func.count(ClubMembership.id))
                .where(
                    and_(
                        ClubMembership.club_id.in_(club_ids),
                        ClubMembership.status == "ACTIVE",
                    )
                )
                .group_by(ClubMembership.club_id)
            )
            member_counts = dict((await db.execute(mem_stmt)).all())

            ev_stmt = (
                select(CampusEvent.club_id, func.count(CampusEvent.id))
                .where(CampusEvent.club_id.in_(club_ids))
                .group_by(CampusEvent.club_id)
            )
            event_counts = dict((await db.execute(ev_stmt)).all())

        for c in clubs:
            c.members_count = member_counts.get(c.id, 0)
            c.events_count = event_counts.get(c.id, 0)
            if c.faculty_advisor and c.faculty_advisor.user:
                c.faculty_advisor_name = f"{c.faculty_advisor.user.first_name} {c.faculty_advisor.user.last_name}"
            if c.student_lead and c.student_lead.user:
                c.student_lead_name = f"{c.student_lead.user.first_name} {c.student_lead.user.last_name}"

        return {"items": clubs, "total": total, "page": page, "limit": limit}

    @classmethod
    async def create_club(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        data: ClubCreate,
        creator_user_id: UUID,
        is_admin_or_faculty: bool = False,
    ) -> Club:
        # Check unique code
        exist_code = (
            await db.execute(
                select(Club).where(and_(Club.tenant_id == tenant_id, Club.code == data.code.upper()))
            )
        ).scalar_one_or_none()
        if exist_code:
            raise ConflictException(f"Club with code '{data.code}' already exists.")

        # Generate slug
        base_slug = data.slug or data.name.lower().replace(" ", "-")
        slug = "".join(c for c in base_slug if c.isalnum() or c == "-").strip("-")

        # Initial status: PENDING_APPROVAL for students, ACTIVE for staff/admin
        initial_status = "ACTIVE" if is_admin_or_faculty else "PENDING_APPROVAL"

        now = datetime.now(UTC)
        club = Club(
            id=uuid4(),
            tenant_id=tenant_id,
            campus_id=data.campus_id,
            code=data.code.upper(),
            name=data.name,
            slug=slug,
            category=data.category.upper(),
            description=data.description,
            logo_document_id=data.logo_document_id,
            faculty_advisor_id=data.faculty_advisor_id,
            student_lead_id=data.student_lead_id,
            status=initial_status,
            is_active=True,
            created_by_user_id=creator_user_id,
            approved_by_user_id=creator_user_id if is_admin_or_faculty else None,
            approved_at=now if is_admin_or_faculty else None,
        )
        db.add(club)

        # If created by student, add as LEAD / PRESIDENT membership
        if not is_admin_or_faculty and data.student_lead_id:
            membership = ClubMembership(
                id=uuid4(),
                tenant_id=tenant_id,
                club_id=club.id,
                student_id=data.student_lead_id,
                role="PRESIDENT",
                status="ACTIVE",
                joined_at=now,
                is_active=True,
            )
            db.add(membership)

        db.add(
            cls._create_audit(
                tenant_id, creator_user_id, "CLUB_CREATED", "Club", club.id, {"status": initial_status}
            )
        )
        await db.commit()
        await db.refresh(club)
        return club

    @classmethod
    async def approve_club(
        cls, db: AsyncSession, tenant_id: UUID, club_id: UUID, user_id: UUID
    ) -> Club:
        club = await db.get(Club, club_id)
        if not club or club.tenant_id != tenant_id:
            raise NotFoundException("Club", club_id)

        now = datetime.now(UTC)
        club.status = "ACTIVE"
        club.approved_by_user_id = user_id
        club.approved_at = now

        db.add(cls._create_audit(tenant_id, user_id, "CLUB_APPROVED", "Club", club.id))

        # Notify creator
        if club.created_by_user_id:
            await NotificationService.create_notification(
                db=db,
                tenant_id=tenant_id,
                recipient_user_id=club.created_by_user_id,
                type="CLUB",
                title=f"Club Approved: {club.name}",
                message=f"Congratulations! Your student club '{club.name}' has been officially approved and is now active.",
                priority="HIGH",
                action_url=f"/app/clubs/{club.id}",
                source_module="CLUBS",
                source_entity_type="Club",
                source_entity_id=club.id,
            )

        await db.commit()
        await db.refresh(club)
        return club

    # =========================================================================
    # 7. CLUB MEMBERSHIP WORKFLOW
    # =========================================================================
    @classmethod
    async def request_club_membership(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        club_id: UUID,
        student_id: UUID,
        data: ClubMembershipRequest,
        actor_user_id: UUID,
    ) -> ClubMembership:
        club = await db.get(Club, club_id)
        if not club or club.tenant_id != tenant_id:
            raise NotFoundException("Club", club_id)
        if club.status != "ACTIVE":
            raise ValidationException(f"Cannot join club with status '{club.status}'.")

        exist_stmt = select(ClubMembership).where(
            and_(ClubMembership.club_id == club_id, ClubMembership.student_id == student_id)
        )
        existing = (await db.execute(exist_stmt)).scalar_one_or_none()
        now = datetime.now(UTC)

        if existing:
            if existing.status == "ACTIVE":
                raise ConflictException("Student is already an active member of this club.")
            elif existing.status == "PENDING":
                raise ConflictException("Membership request is already pending approval.")
            else:
                existing.status = "PENDING"
                existing.role = data.role.upper()
                existing.joined_at = None
                existing.left_at = None
                existing.rejection_reason = None
                await db.commit()
                await db.refresh(existing)
                return existing

        membership = ClubMembership(
            id=uuid4(),
            tenant_id=tenant_id,
            club_id=club_id,
            student_id=student_id,
            role=data.role.upper(),
            status="PENDING",
            is_active=True,
        )
        db.add(membership)
        db.add(
            cls._create_audit(
                tenant_id, actor_user_id, "CLUB_MEMBERSHIP_REQUESTED", "ClubMembership", membership.id
            )
        )
        await db.commit()
        await db.refresh(membership)
        return membership

    @classmethod
    async def review_club_membership(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        membership_id: UUID,
        data: ClubMembershipReview,
        reviewer_user_id: UUID,
    ) -> ClubMembership:
        membership = await db.get(ClubMembership, membership_id)
        if not membership or membership.tenant_id != tenant_id:
            raise NotFoundException("ClubMembership", membership_id)

        now = datetime.now(UTC)
        new_status = data.status.upper()
        if new_status not in ("ACTIVE", "REJECTED"):
            raise ValidationException("Review status must be ACTIVE or REJECTED.")

        membership.status = new_status
        membership.approved_by_user_id = reviewer_user_id
        membership.approved_at = now
        if data.role:
            membership.role = data.role.upper()

        if new_status == "ACTIVE":
            membership.joined_at = now
            membership.rejection_reason = None
        else:
            membership.rejection_reason = data.rejection_reason or "Membership request declined."

        # Notify student
        student = await db.get(StudentProfile, membership.student_id)
        club = await db.get(Club, membership.club_id)
        if student and student.user_id and club:
            verb = "Approved" if new_status == "ACTIVE" else "Declined"
            await NotificationService.create_notification(
                db=db,
                tenant_id=tenant_id,
                recipient_user_id=student.user_id,
                type="CLUB",
                title=f"Club Membership {verb}: {club.name}",
                message=f"Your membership request for '{club.name}' was {verb.lower()}.",
                priority="NORMAL",
                action_url=f"/app/clubs/{club.id}",
                source_module="CLUBS",
                source_entity_type="Club",
                source_entity_id=club.id,
            )

        db.add(
            cls._create_audit(
                tenant_id,
                reviewer_user_id,
                f"CLUB_MEMBERSHIP_{new_status}",
                "ClubMembership",
                membership.id,
            )
        )
        await db.commit()
        await db.refresh(membership)
        return membership

    @classmethod
    async def leave_club(
        cls, db: AsyncSession, tenant_id: UUID, club_id: UUID, student_id: UUID, actor_user_id: UUID
    ) -> None:
        stmt = select(ClubMembership).where(
            and_(
                ClubMembership.club_id == club_id,
                ClubMembership.student_id == student_id,
                ClubMembership.tenant_id == tenant_id,
            )
        )
        membership = (await db.execute(stmt)).scalar_one_or_none()
        if not membership:
            raise NotFoundException("ClubMembership", student_id)

        now = datetime.now(UTC)
        membership.status = "LEFT"
        membership.left_at = now
        membership.is_active = False

        db.add(
            cls._create_audit(
                tenant_id, actor_user_id, "CLUB_MEMBERSHIP_LEFT", "ClubMembership", membership.id
            )
        )
        await db.commit()

    @classmethod
    async def list_club_members(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        club_id: UUID,
        status: str | None = None,
        page: int = 1,
        limit: int = 50,
    ) -> dict:
        conditions = [ClubMembership.tenant_id == tenant_id, ClubMembership.club_id == club_id]
        if status:
            conditions.append(ClubMembership.status == status.upper())

        total = (await db.execute(select(func.count(ClubMembership.id)).where(and_(*conditions)))).scalar() or 0
        offset = (page - 1) * limit
        stmt = (
            select(ClubMembership)
            .options(selectinload(ClubMembership.student).selectinload(StudentProfile.user))
            .where(and_(*conditions))
            .order_by(ClubMembership.created_at.asc())
            .offset(offset)
            .limit(limit)
        )
        members = (await db.execute(stmt)).scalars().all()
        return {"items": members, "total": total, "page": page, "limit": limit}

    # =========================================================================
    # 8. ANNOUNCEMENT & AUDIENCE TARGETING ENGINE
    # =========================================================================
    @classmethod
    async def resolve_audience_user_ids(
        cls, db: AsyncSession, tenant_id: UUID, audiences: list[AnnouncementAudienceItem]
    ) -> set[UUID]:
        """Resolves target audience criteria into unique user identifiers for dispatch."""
        user_ids: set[UUID] = set()

        for aud in audiences:
            target_type = aud.target_type.upper()

            if target_type == "ALL_USERS":
                u_stmt = select(User.id).where(
                    and_(User.primary_tenant_id == tenant_id, User.is_active.is_(True))
                )
                user_ids.update((await db.execute(u_stmt)).scalars().all())

            elif target_type == "ALL_STUDENTS":
                s_stmt = select(StudentProfile.user_id).where(
                    and_(StudentProfile.tenant_id == tenant_id, StudentProfile.status == "ACTIVE")
                )
                user_ids.update((await db.execute(s_stmt)).scalars().all())

            elif target_type == "ALL_FACULTY":
                f_stmt = select(FacultyProfile.user_id).where(
                    and_(FacultyProfile.tenant_id == tenant_id, FacultyProfile.employment_status == "ACTIVE")
                )
                user_ids.update((await db.execute(f_stmt)).scalars().all())

            elif target_type == "ALL_STAFF":
                st_stmt = select(StaffProfile.user_id).where(
                    and_(StaffProfile.tenant_id == tenant_id, StaffProfile.is_active.is_(True))
                )
                user_ids.update((await db.execute(st_stmt)).scalars().all())

            elif target_type == "DEPARTMENT" and aud.target_id:
                # Faculty in this department
                fac_stmt = select(FacultyProfile.user_id).where(
                    and_(
                        FacultyProfile.tenant_id == tenant_id,
                        FacultyProfile.department_id == aud.target_id,
                        FacultyProfile.employment_status == "ACTIVE",
                    )
                )
                user_ids.update((await db.execute(fac_stmt)).scalars().all())

                # Students in programs under this department
                stud_stmt = (
                    select(StudentProfile.user_id)
                    .join(Program, StudentProfile.program_id == Program.id)
                    .where(
                        and_(
                            StudentProfile.tenant_id == tenant_id,
                            Program.department_id == aud.target_id,
                            StudentProfile.status == "ACTIVE",
                        )
                    )
                )
                user_ids.update((await db.execute(stud_stmt)).scalars().all())

            elif target_type == "PROGRAM" and aud.target_id:
                stud_stmt = select(StudentProfile.user_id).where(
                    and_(
                        StudentProfile.tenant_id == tenant_id,
                        StudentProfile.program_id == aud.target_id,
                        StudentProfile.status == "ACTIVE",
                    )
                )
                user_ids.update((await db.execute(stud_stmt)).scalars().all())

            elif target_type == "SECTION" and aud.target_id:
                stud_stmt = select(StudentProfile.user_id).where(
                    and_(
                        StudentProfile.tenant_id == tenant_id,
                        StudentProfile.current_section_id == aud.target_id,
                        StudentProfile.status == "ACTIVE",
                    )
                )
                user_ids.update((await db.execute(stud_stmt)).scalars().all())

            elif target_type == "CLUB" and aud.target_id:
                mem_stmt = (
                    select(StudentProfile.user_id)
                    .join(ClubMembership, StudentProfile.id == ClubMembership.student_id)
                    .where(
                        and_(
                            ClubMembership.club_id == aud.target_id,
                            ClubMembership.status == "ACTIVE",
                        )
                    )
                )
                user_ids.update((await db.execute(mem_stmt)).scalars().all())

            elif target_type == "INDIVIDUAL_USERS" and aud.target_id:
                user_ids.add(aud.target_id)

        return user_ids

    @classmethod
    async def preview_audience(
        cls, db: AsyncSession, tenant_id: UUID, audiences: list[AnnouncementAudienceItem]
    ) -> AudiencePreviewResponse:
        """Computes recipient breakdown and preview list for targeting configuration."""
        resolved_uids = await cls.resolve_audience_user_ids(db, tenant_id, audiences)
        if not resolved_uids:
            return AudiencePreviewResponse(
                total_recipients=0,
                students_count=0,
                faculty_count=0,
                staff_count=0,
                sample_recipients=[],
            )

        uid_list = list(resolved_uids)
        # Count students
        s_count = (
            await db.execute(
                select(func.count(StudentProfile.id)).where(StudentProfile.user_id.in_(uid_list))
            )
        ).scalar() or 0

        # Count faculty
        f_count = (
            await db.execute(
                select(func.count(FacultyProfile.id)).where(FacultyProfile.user_id.in_(uid_list))
            )
        ).scalar() or 0

        # Count staff
        st_count = (
            await db.execute(
                select(func.count(StaffProfile.id)).where(StaffProfile.user_id.in_(uid_list))
            )
        ).scalar() or 0

        # Sample preview
        sample_users = (
            await db.execute(
                select(User).where(User.id.in_(uid_list[:5]))
            )
        ).scalars().all()

        samples = [
            {"name": f"{u.first_name} {u.last_name}", "email": u.email, "role": u.status}
            for u in sample_users
        ]

        return AudiencePreviewResponse(
            total_recipients=len(resolved_uids),
            students_count=s_count,
            faculty_count=f_count,
            staff_count=st_count,
            sample_recipients=samples,
        )

    @classmethod
    async def create_announcement(
        cls, db: AsyncSession, tenant_id: UUID, data: AnnouncementCreate, user_id: UUID
    ) -> CampusAnnouncement:
        now = datetime.now(UTC)
        publish_at = data.publish_at or now

        announcement = CampusAnnouncement(
            id=uuid4(),
            tenant_id=tenant_id,
            title=data.title,
            summary=data.summary,
            content=data.content,
            priority=data.priority.upper(),
            status=data.status.upper(),
            publish_at=publish_at,
            expires_at=data.expires_at,
            is_pinned=data.is_pinned,
            created_by_user_id=user_id,
            published_by_user_id=user_id if data.status.upper() == "PUBLISHED" else None,
            published_at=now if data.status.upper() == "PUBLISHED" else None,
        )
        db.add(announcement)

        # Add audience criteria
        for aud in data.audiences:
            db.add(
                AnnouncementAudience(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    announcement_id=announcement.id,
                    target_type=aud.target_type.upper(),
                    target_id=aud.target_id,
                    filter_metadata=aud.filter_metadata,
                )
            )

        db.add(
            cls._create_audit(
                tenant_id, user_id, "ANNOUNCEMENT_CREATED", "CampusAnnouncement", announcement.id
            )
        )
        await db.flush()

        # If published immediately, dispatch notifications in bulk
        if announcement.status == "PUBLISHED":
            recipient_uids = await cls.resolve_audience_user_ids(db, tenant_id, data.audiences)
            if recipient_uids:
                await NotificationService.create_bulk_notifications(
                    db=db,
                    tenant_id=tenant_id,
                    recipient_user_ids=list(recipient_uids),
                    type="ANNOUNCEMENT",
                    title=f"Announcement: {announcement.title}",
                    message=announcement.summary or announcement.content[:160],
                    priority=announcement.priority,
                    action_url=f"/app/announcements/{announcement.id}",
                    source_module="ANNOUNCEMENTS",
                    source_entity_type="CampusAnnouncement",
                    source_entity_id=announcement.id,
                )

        await db.commit()
        loaded_ann = (
            await db.execute(
                select(CampusAnnouncement)
                .options(selectinload(CampusAnnouncement.audiences))
                .where(CampusAnnouncement.id == announcement.id)
            )
        ).scalar_one()
        return loaded_ann

    @classmethod
    async def publish_announcement(
        cls, db: AsyncSession, tenant_id: UUID, announcement_id: UUID, user_id: UUID
    ) -> CampusAnnouncement:
        stmt = (
            select(CampusAnnouncement)
            .options(selectinload(CampusAnnouncement.audiences))
            .where(
                and_(
                    CampusAnnouncement.id == announcement_id,
                    CampusAnnouncement.tenant_id == tenant_id,
                )
            )
        )
        ann = (await db.execute(stmt)).scalar_one_or_none()
        if not ann:
            raise NotFoundException("CampusAnnouncement", announcement_id)

        now = datetime.now(UTC)
        ann.status = "PUBLISHED"
        ann.published_by_user_id = user_id
        ann.published_at = now

        # Convert audiences to schema items
        aud_items = [
            AnnouncementAudienceItem(
                target_type=a.target_type, target_id=a.target_id, filter_metadata=a.filter_metadata
            )
            for a in ann.audiences
        ]

        # Bulk fanout
        recipient_uids = await cls.resolve_audience_user_ids(db, tenant_id, aud_items)
        if recipient_uids:
            await NotificationService.create_bulk_notifications(
                db=db,
                tenant_id=tenant_id,
                recipient_user_ids=list(recipient_uids),
                type="ANNOUNCEMENT",
                title=f"Announcement: {ann.title}",
                message=ann.summary or ann.content[:160],
                priority=ann.priority,
                action_url=f"/app/announcements/{ann.id}",
                source_module="ANNOUNCEMENTS",
                source_entity_type="CampusAnnouncement",
                source_entity_id=ann.id,
            )

        db.add(
            cls._create_audit(
                tenant_id, user_id, "ANNOUNCEMENT_PUBLISHED", "CampusAnnouncement", ann.id
            )
        )
        await db.commit()
        loaded_ann = (
            await db.execute(
                select(CampusAnnouncement)
                .options(selectinload(CampusAnnouncement.audiences))
                .where(CampusAnnouncement.id == ann.id)
            )
        ).scalar_one()
        return loaded_ann

    @classmethod
    async def list_announcements(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        priority: str | None = None,
        status: str | None = None,
        search: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> dict:
        conditions = [CampusAnnouncement.tenant_id == tenant_id]
        if priority:
            conditions.append(CampusAnnouncement.priority == priority.upper())
        if status:
            conditions.append(CampusAnnouncement.status == status.upper())
        if search:
            search_pat = f"%{search}%"
            conditions.append(
                or_(
                    CampusAnnouncement.title.ilike(search_pat),
                    CampusAnnouncement.content.ilike(search_pat),
                )
            )

        total = (await db.execute(select(func.count(CampusAnnouncement.id)).where(and_(*conditions)))).scalar() or 0
        offset = (page - 1) * limit
        stmt = (
            select(CampusAnnouncement)
            .options(
                selectinload(CampusAnnouncement.audiences),
                selectinload(CampusAnnouncement.created_by),
                selectinload(CampusAnnouncement.published_by),
            )
            .where(and_(*conditions))
            .order_by(CampusAnnouncement.is_pinned.desc(), CampusAnnouncement.publish_at.desc())
            .offset(offset)
            .limit(limit)
        )
        announcements = (await db.execute(stmt)).scalars().all()
        return {"items": announcements, "total": total, "page": page, "limit": limit}

    # =========================================================================
    # 9. CAMPUS DASHBOARD
    # =========================================================================
    @classmethod
    async def get_dashboard_metrics(
        cls, db: AsyncSession, tenant_id: UUID, user_id: UUID
    ) -> dict:
        now = datetime.now(UTC)
        start_of_month = datetime(now.year, now.month, 1, tzinfo=UTC)

        # 1. Upcoming events count
        upcoming_events_stmt = select(func.count(CampusEvent.id)).where(
            and_(
                CampusEvent.tenant_id == tenant_id,
                CampusEvent.start_at >= now,
                CampusEvent.status.notin_(["CANCELLED", "ARCHIVED", "DRAFT"]),
            )
        )
        upcoming_events_count = (await db.execute(upcoming_events_stmt)).scalar() or 0

        # 2. Open registrations count
        open_reg_stmt = select(func.count(CampusEvent.id)).where(
            and_(
                CampusEvent.tenant_id == tenant_id,
                CampusEvent.status.in_(["PUBLISHED", "REGISTRATION_OPEN"]),
                CampusEvent.start_at >= now,
            )
        )
        open_reg_count = (await db.execute(open_reg_stmt)).scalar() or 0

        # 3. Registered participants
        reg_stmt = select(func.count(EventRegistration.id)).where(
            and_(
                EventRegistration.tenant_id == tenant_id,
                EventRegistration.status.in_(["REGISTERED", "CONFIRMED", "ATTENDED"]),
            )
        )
        registered_participants_count = (await db.execute(reg_stmt)).scalar() or 0

        # 4. Active clubs count
        active_clubs_stmt = select(func.count(Club.id)).where(
            and_(Club.tenant_id == tenant_id, Club.status == "ACTIVE")
        )
        active_clubs_count = (await db.execute(active_clubs_stmt)).scalar() or 0

        # 5. Pending club requests
        pending_clubs_stmt = select(func.count(Club.id)).where(
            and_(Club.tenant_id == tenant_id, Club.status == "PENDING_APPROVAL")
        )
        pending_club_requests_count = (await db.execute(pending_clubs_stmt)).scalar() or 0

        # 6. Published announcements
        published_ann_stmt = select(func.count(CampusAnnouncement.id)).where(
            and_(CampusAnnouncement.tenant_id == tenant_id, CampusAnnouncement.status == "PUBLISHED")
        )
        published_announcements_count = (await db.execute(published_ann_stmt)).scalar() or 0

        # 7. Unread notifications for this user
        unread_notif_count = await NotificationService.get_unread_count(db, tenant_id, user_id)

        # 8. Events this month
        events_month_stmt = select(func.count(CampusEvent.id)).where(
            and_(
                CampusEvent.tenant_id == tenant_id,
                CampusEvent.start_at >= start_of_month,
                CampusEvent.status.notin_(["CANCELLED", "ARCHIVED"]),
            )
        )
        events_this_month_count = (await db.execute(events_month_stmt)).scalar() or 0

        return {
            "upcoming_events_count": upcoming_events_count,
            "open_registrations_count": open_reg_count,
            "registered_participants_count": registered_participants_count,
            "active_clubs_count": active_clubs_count,
            "pending_club_requests_count": pending_club_requests_count,
            "published_announcements_count": published_announcements_count,
            "unread_notifications_count": unread_notif_count,
            "events_this_month_count": events_this_month_count,
        }
