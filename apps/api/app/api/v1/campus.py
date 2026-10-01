"""Campus Events, Clubs, Communication, and Notification Engine API Endpoints.

Provides REST interfaces for event scheduling, venue conflict detection, student registrations,
check-in attendance, club lifecycle & membership, targeted announcements, and notification center.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.deps import get_current_active_user, get_tenant_context, require_permission
from app.core.exceptions import PermissionDeniedException, ValidationException
from app.core.permissions import (
    ANNOUNCEMENTS_ARCHIVE,
    ANNOUNCEMENTS_CREATE,
    ANNOUNCEMENTS_PUBLISH,
    ANNOUNCEMENTS_READ,
    ANNOUNCEMENTS_UPDATE,
    CLUBS_APPROVE,
    CLUBS_CREATE,
    CLUBS_MANAGE_MEMBERSHIPS,
    CLUBS_READ,
    CLUBS_SELF_MANAGE_MEMBERSHIP,
    CLUBS_SELF_READ,
    CLUBS_SELF_REQUEST_MEMBERSHIP,
    CLUBS_UPDATE,
    EVENTS_CANCEL,
    EVENTS_CREATE,
    EVENTS_MANAGE_ATTENDANCE,
    EVENTS_MANAGE_REGISTRATIONS,
    EVENTS_PUBLISH,
    EVENTS_READ,
    EVENTS_SELF_MANAGE_REGISTRATION,
    EVENTS_SELF_REGISTER,
    EVENTS_UPDATE,
    NOTIFICATIONS_MANAGE,
    NOTIFICATIONS_MANAGE_PREFERENCES,
    NOTIFICATIONS_READ,
    NOTIFICATIONS_SELF_MANAGE_PREFERENCES,
    NOTIFICATIONS_SELF_READ,
)
from app.core.tenant import TenantContext
from app.models.people import StudentProfile, User
from app.schemas.campus import (
    AnnouncementAudienceItem,
    AnnouncementCreate,
    AnnouncementResponse,
    AnnouncementUpdate,
    AudiencePreviewRequest,
    AudiencePreviewResponse,
    CampusDashboardStats,
    ClubCreate,
    ClubDetailResponse,
    ClubMembershipRequest,
    ClubMembershipResponse,
    ClubMembershipReview,
    ClubResponse,
    ClubStatusTransition,
    ClubUpdate,
    EventCategoryCreate,
    EventCategoryResponse,
    EventCategoryUpdate,
    EventCheckInRequest,
    EventCheckInResponse,
    EventCreate,
    EventDetailResponse,
    EventQRCheckInRequest,
    EventQRTokenResponse,
    EventRegistrationCancel,
    EventRegistrationCreate,
    EventRegistrationResponse,
    EventResponse,
    EventUpdate,
    EventVenueCreate,
    EventVenueResponse,
    EventVenueUpdate,
    NotificationListResponse,
    NotificationPreferenceItem,
    NotificationPreferenceUpdate,
    NotificationResponse,
    UnreadCountResponse,
)
from app.schemas.common import ApiResponse
from app.services.campus_service import CampusService
from app.services.notification_service import NotificationService

router = APIRouter(tags=["Campus Events, Clubs & Communication"])


# =============================================================================
# 0. DASHBOARD TELEMETRY
# =============================================================================
@router.get("/campus/dashboard", response_model=ApiResponse[CampusDashboardStats])
async def get_campus_dashboard(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[CampusDashboardStats]:
    """Retrieve authoritative metrics for Campus Events, Clubs, and Announcements."""
    stats = await CampusService.get_dashboard_metrics(db, tenant.tenant_id, current_user.id)
    return ApiResponse(data=CampusDashboardStats(**stats))


# =============================================================================
# 1. EVENT CATEGORIES
# =============================================================================
@router.get("/event-categories", response_model=ApiResponse[list[EventCategoryResponse]])
async def list_event_categories(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    active_only: bool = Query(False),
) -> ApiResponse[list[EventCategoryResponse]]:
    """List event taxonomy categories configured for this institution."""
    categories = await CampusService.list_categories(db, tenant.tenant_id, active_only=active_only)
    return ApiResponse(data=[EventCategoryResponse.model_validate(c) for c in categories])


@router.post(
    "/event-categories",
    response_model=ApiResponse[EventCategoryResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_event_category(
    payload: EventCategoryCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(EVENTS_CREATE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[EventCategoryResponse]:
    """Create a new configurable event category."""
    cat = await CampusService.create_category(db, tenant.tenant_id, payload, current_user.id)
    return ApiResponse(data=EventCategoryResponse.model_validate(cat))


@router.patch("/event-categories/{category_id}", response_model=ApiResponse[EventCategoryResponse])
async def update_event_category(
    category_id: UUID,
    payload: EventCategoryUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(EVENTS_UPDATE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[EventCategoryResponse]:
    """Update event category attributes or status."""
    cat = await CampusService.update_category(db, tenant.tenant_id, category_id, payload, current_user.id)
    return ApiResponse(data=EventCategoryResponse.model_validate(cat))


# =============================================================================
# 2. EVENT VENUES
# =============================================================================
@router.get("/event-venues", response_model=ApiResponse[list[EventVenueResponse]])
async def list_event_venues(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    campus_id: UUID | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
) -> ApiResponse[list[EventVenueResponse]]:
    """List physical campus halls, auditoriums, and venues."""
    venues = await CampusService.list_venues(db, tenant.tenant_id, campus_id=campus_id, status=status_filter)
    return ApiResponse(data=[EventVenueResponse.model_validate(v) for v in venues])


@router.post(
    "/event-venues",
    response_model=ApiResponse[EventVenueResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_event_venue(
    payload: EventVenueCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(EVENTS_CREATE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[EventVenueResponse]:
    """Register a new venue with capacity limits on a campus."""
    venue = await CampusService.create_venue(db, tenant.tenant_id, payload, current_user.id)
    return ApiResponse(data=EventVenueResponse.model_validate(venue))


@router.patch("/event-venues/{venue_id}", response_model=ApiResponse[EventVenueResponse])
async def update_event_venue(
    venue_id: UUID,
    payload: EventVenueUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(EVENTS_UPDATE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[EventVenueResponse]:
    """Update venue capacity or maintenance status."""
    venue = await CampusService.update_venue(db, tenant.tenant_id, venue_id, payload, current_user.id)
    return ApiResponse(data=EventVenueResponse.model_validate(venue))


# =============================================================================
# 3. CAMPUS EVENTS
# =============================================================================
@router.get("/events", response_model=ApiResponse[dict])
async def list_events(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    campus_id: UUID | None = Query(None),
    category_id: UUID | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    organizer_type: str | None = Query(None),
    organizer_id: UUID | None = Query(None),
    search: str | None = Query(None),
    upcoming_only: bool = Query(False),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
) -> ApiResponse[dict]:
    """Search and browse campus events with participant statistics."""
    result = await CampusService.list_events(
        db,
        tenant.tenant_id,
        campus_id=campus_id,
        category_id=category_id,
        status=status_filter,
        organizer_type=organizer_type,
        organizer_id=organizer_id,
        search=search,
        upcoming_only=upcoming_only,
        page=page,
        limit=limit,
    )
    result["items"] = [EventResponse.model_validate(e) for e in result["items"]]
    return ApiResponse(data=result)


@router.post(
    "/events",
    response_model=ApiResponse[EventResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_event(
    payload: EventCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(EVENTS_CREATE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[EventResponse]:
    """Create a campus event with venue conflict detection and capacity validation."""
    event = await CampusService.create_event(db, tenant.tenant_id, payload, current_user.id)
    return ApiResponse(data=EventResponse.model_validate(event))


@router.get("/events/{event_id}", response_model=ApiResponse[EventDetailResponse])
async def get_event_detail(
    event_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[EventDetailResponse]:
    """Retrieve event details, venue info, and user's registration status."""
    event = await CampusService.get_event_detail(db, tenant.tenant_id, event_id, current_user=current_user)
    resp = EventDetailResponse.model_validate(event)
    if event.category:
        resp.category_name = event.category.name
    if event.venue_rel:
        resp.venue_details = EventVenueResponse.model_validate(event.venue_rel)
    if hasattr(event, "user_registration_status"):
        resp.user_registration_status = event.user_registration_status
        resp.user_registration_id = event.user_registration_id
    return ApiResponse(data=resp)


@router.patch("/events/{event_id}", response_model=ApiResponse[EventResponse])
async def update_event(
    event_id: UUID,
    payload: EventUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(EVENTS_UPDATE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[EventResponse]:
    """Update event schedules, capacity, or metadata."""
    event = await CampusService.update_event(db, tenant.tenant_id, event_id, payload, current_user.id)
    return ApiResponse(data=EventResponse.model_validate(event))


@router.post("/events/{event_id}/publish", response_model=ApiResponse[EventResponse])
async def publish_event(
    event_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(EVENTS_PUBLISH))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[EventResponse]:
    """Publish an event, opening registration window and notifying participants."""
    event = await CampusService.publish_event(db, tenant.tenant_id, event_id, current_user.id)
    return ApiResponse(data=EventResponse.model_validate(event))


@router.post("/events/{event_id}/cancel", response_model=ApiResponse[EventResponse])
async def cancel_event(
    event_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(EVENTS_CANCEL))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    reason: str | None = Query(None),
) -> ApiResponse[EventResponse]:
    """Cancel an event and all active student registrations with notification."""
    event = await CampusService.cancel_event(db, tenant.tenant_id, event_id, current_user.id, reason=reason)
    return ApiResponse(data=EventResponse.model_validate(event))


# =============================================================================
# 4. EVENT REGISTRATION WORKFLOW
# =============================================================================
@router.post(
    "/events/{event_id}/register",
    response_model=ApiResponse[EventRegistrationResponse],
    status_code=status.HTTP_201_CREATED,
)
async def register_for_event(
    event_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    payload: EventRegistrationCreate | None = None,
) -> ApiResponse[EventRegistrationResponse]:
    """Register for an event (self-registration or staff on-behalf)."""
    target_student_id: UUID | None = None

    if payload and payload.student_id:
        # Staff registering a student
        target_student_id = payload.student_id
    else:
        # Self registration: resolve student profile for current user
        student = (
            await db.execute(
                select(StudentProfile).where(
                    and_(
                        StudentProfile.tenant_id == tenant.tenant_id,
                        StudentProfile.user_id == current_user.id,
                    )
                )
            )
        ).scalar_one_or_none()
        if not student:
            raise ValidationException("Only enrolled students can register for campus events.")
        target_student_id = student.id

    registration = await CampusService.register_student_for_event(
        db, tenant.tenant_id, event_id, target_student_id, current_user.id
    )

    resp = EventRegistrationResponse.model_validate(registration)
    # Populate student info
    st = await db.get(StudentProfile, target_student_id)
    if st:
        resp.student_roll_number = st.roll_number
        if st.user_id:
            u = await db.get(User, st.user_id)
            if u:
                resp.student_name = f"{u.first_name} {u.last_name}"
                resp.student_email = u.email

    return ApiResponse(data=resp)


@router.post("/events/{event_id}/cancel-registration", response_model=ApiResponse[EventRegistrationResponse])
async def cancel_event_registration(
    event_id: UUID,
    payload: EventRegistrationCancel,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    registration_id: UUID | None = Query(None),
) -> ApiResponse[EventRegistrationResponse]:
    """Cancel event registration."""
    # Find registration if not explicitly given
    if not registration_id:
        student = (
            await db.execute(
                select(StudentProfile).where(
                    and_(
                        StudentProfile.tenant_id == tenant.tenant_id,
                        StudentProfile.user_id == current_user.id,
                    )
                )
            )
        ).scalar_one_or_none()
        if not student:
            raise ValidationException("Student profile not found.")

        reg = (
            await db.execute(
                select(EventRegistration).where(
                    and_(
                        EventRegistration.event_id == event_id,
                        EventRegistration.student_id == student.id,
                        EventRegistration.status.in_(["REGISTERED", "CONFIRMED", "WAITLISTED"]),
                    )
                )
            )
        ).scalar_one_or_none()
        if not reg:
            raise NotFoundException("Active EventRegistration", event_id)
        registration_id = reg.id

    reg = await CampusService.cancel_registration(
        db, tenant.tenant_id, registration_id, current_user.id, payload
    )
    return ApiResponse(data=EventRegistrationResponse.model_validate(reg))


@router.get("/events/{event_id}/registrations", response_model=ApiResponse[dict])
async def list_event_registrations(
    event_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(EVENTS_READ))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
) -> ApiResponse[dict]:
    """List registered participants for an event with attendance statuses."""
    result = await CampusService.list_event_registrations(
        db, tenant.tenant_id, event_id, status=status_filter, page=page, limit=limit
    )

    items = []
    for r in result["items"]:
        item = EventRegistrationResponse.model_validate(r)
        if r.student:
            item.student_roll_number = r.student.roll_number
            if r.student.user:
                item.student_name = f"{r.student.user.first_name} {r.student.user.last_name}"
                item.student_email = r.student.user.email
        items.append(item)

    result["items"] = items
    return ApiResponse(data=result)


# =============================================================================
# 5. EVENT ATTENDANCE & CHECK-IN
# =============================================================================
@router.post(
    "/events/{event_id}/check-in",
    response_model=ApiResponse[EventCheckInResponse],
    status_code=status.HTTP_201_CREATED,
)
async def check_in_student(
    event_id: UUID,
    payload: EventCheckInRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(EVENTS_MANAGE_ATTENDANCE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[EventCheckInResponse]:
    """Manual or barcode check-in for a registered student."""
    att = await CampusService.check_in_student(
        db, tenant.tenant_id, event_id, payload, current_user.id
    )
    resp = EventCheckInResponse.model_validate(att)
    st = await db.get(StudentProfile, att.student_id)
    if st:
        resp.student_roll_number = st.roll_number
        if st.user_id:
            u = await db.get(User, st.user_id)
            if u:
                resp.student_name = f"{u.first_name} {u.last_name}"
    return ApiResponse(data=resp)


@router.post("/events/{event_id}/undo-check-in", response_model=ApiResponse[dict])
async def undo_check_in(
    event_id: UUID,
    student_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(EVENTS_MANAGE_ATTENDANCE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[dict]:
    """Undo mistaken event check-in with supervisor permission."""
    await CampusService.undo_check_in(db, tenant.tenant_id, event_id, student_id, current_user.id)
    return ApiResponse(data={"message": "Event check-in reverted successfully."})


@router.get("/events/{event_id}/qr-token", response_model=ApiResponse[EventQRTokenResponse])
async def get_event_qr_token(
    event_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(EVENTS_MANAGE_ATTENDANCE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    duration_seconds: int = Query(300, ge=60, le=1800),
) -> ApiResponse[EventQRTokenResponse]:
    """Generate a temporary signed QR check-in token for venue display."""
    token_data = CampusService.generate_event_qr_token(
        tenant.tenant_id, event_id, duration_seconds=duration_seconds
    )
    return ApiResponse(data=EventQRTokenResponse(**token_data))


@router.post(
    "/events/{event_id}/qr-check-in",
    response_model=ApiResponse[EventCheckInResponse],
    status_code=status.HTTP_201_CREATED,
)
async def qr_check_in(
    event_id: UUID,
    payload: EventQRCheckInRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[EventCheckInResponse]:
    """Authenticated student scans venue QR token to mark attendance."""
    att = await CampusService.verify_and_check_in_qr(
        db, tenant.tenant_id, payload.qr_token, current_user.id
    )
    return ApiResponse(data=EventCheckInResponse.model_validate(att))


# =============================================================================
# 6. CLUB MANAGEMENT
# =============================================================================
@router.get("/clubs", response_model=ApiResponse[dict])
async def list_clubs(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    campus_id: UUID | None = Query(None),
    category: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
) -> ApiResponse[dict]:
    """List collegiate clubs and organizations."""
    result = await CampusService.list_clubs(
        db,
        tenant.tenant_id,
        campus_id=campus_id,
        category=category,
        status=status_filter,
        search=search,
        page=page,
        limit=limit,
    )
    result["items"] = [ClubResponse.model_validate(c) for c in result["items"]]
    return ApiResponse(data=result)


@router.post(
    "/clubs",
    response_model=ApiResponse[ClubResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_club(
    payload: ClubCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[ClubResponse]:
    """Found or propose a new student club."""
    is_staff_or_admin = any(
        ur.role and ur.role.name in ("SUPER_ADMIN", "INSTITUTION_ADMIN", "PRINCIPAL", "HOD", "FACULTY")
        for ur in current_user.roles
    )
    club = await CampusService.create_club(
        db, tenant.tenant_id, payload, current_user.id, is_admin_or_faculty=is_staff_or_admin
    )
    return ApiResponse(data=ClubResponse.model_validate(club))


@router.get("/clubs/{club_id}", response_model=ApiResponse[ClubDetailResponse])
async def get_club_detail(
    club_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[ClubDetailResponse]:
    """Get club details, leadership, and current user's membership standing."""
    club = await db.get(Club, club_id)
    if not club or club.tenant_id != tenant.tenant_id:
        raise NotFoundException("Club", club_id)

    resp = ClubDetailResponse.model_validate(club)

    # Check student membership
    student = (
        await db.execute(
            select(StudentProfile).where(
                and_(
                    StudentProfile.tenant_id == tenant.tenant_id,
                    StudentProfile.user_id == current_user.id,
                )
            )
        )
    ).scalar_one_or_none()
    if student:
        mem = (
            await db.execute(
                select(ClubMembership).where(
                    and_(ClubMembership.club_id == club_id, ClubMembership.student_id == student.id)
                )
            )
        ).scalar_one_or_none()
        if mem:
            resp.user_membership_status = mem.status
            resp.user_membership_role = mem.role

    return ApiResponse(data=resp)


@router.post("/clubs/{club_id}/approve", response_model=ApiResponse[ClubResponse])
async def approve_club(
    club_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CLUBS_APPROVE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[ClubResponse]:
    """Approve a pending student club proposal."""
    club = await CampusService.approve_club(db, tenant.tenant_id, club_id, current_user.id)
    return ApiResponse(data=ClubResponse.model_validate(club))


# =============================================================================
# 7. CLUB MEMBERSHIP
# =============================================================================
@router.post(
    "/clubs/{club_id}/membership",
    response_model=ApiResponse[ClubMembershipResponse],
    status_code=status.HTTP_201_CREATED,
)
async def request_club_membership(
    club_id: UUID,
    payload: ClubMembershipRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[ClubMembershipResponse]:
    """Student submits request to join a club."""
    student = (
        await db.execute(
            select(StudentProfile).where(
                and_(
                    StudentProfile.tenant_id == tenant.tenant_id,
                    StudentProfile.user_id == current_user.id,
                )
            )
        )
    ).scalar_one_or_none()
    if not student:
        raise ValidationException("Only registered students can apply for club membership.")

    membership = await CampusService.request_club_membership(
        db, tenant.tenant_id, club_id, student.id, payload, current_user.id
    )
    return ApiResponse(data=ClubMembershipResponse.model_validate(membership))


@router.delete("/clubs/{club_id}/membership", response_model=ApiResponse[dict])
async def leave_club(
    club_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[dict]:
    """Student leaves a club."""
    student = (
        await db.execute(
            select(StudentProfile).where(
                and_(
                    StudentProfile.tenant_id == tenant.tenant_id,
                    StudentProfile.user_id == current_user.id,
                )
            )
        )
    ).scalar_one_or_none()
    if not student:
        raise ValidationException("Student profile not found.")

    await CampusService.leave_club(db, tenant.tenant_id, club_id, student.id, current_user.id)
    return ApiResponse(data={"message": "Left club successfully."})


@router.get("/clubs/{club_id}/members", response_model=ApiResponse[dict])
async def list_club_members(
    club_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
) -> ApiResponse[dict]:
    """List members and leaders of a club."""
    result = await CampusService.list_club_members(
        db, tenant.tenant_id, club_id, status=status_filter, page=page, limit=limit
    )
    items = []
    for m in result["items"]:
        item = ClubMembershipResponse.model_validate(m)
        if m.student:
            item.student_roll_number = m.student.roll_number
            if m.student.user:
                item.student_name = f"{m.student.user.first_name} {m.student.user.last_name}"
                item.student_email = m.student.user.email
        items.append(item)
    result["items"] = items
    return ApiResponse(data=result)


@router.patch("/clubs/{club_id}/members/{membership_id}", response_model=ApiResponse[ClubMembershipResponse])
async def review_club_membership(
    club_id: UUID,
    membership_id: UUID,
    payload: ClubMembershipReview,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(CLUBS_MANAGE_MEMBERSHIPS))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[ClubMembershipResponse]:
    """Approve or reject a club membership request."""
    membership = await CampusService.review_club_membership(
        db, tenant.tenant_id, membership_id, payload, current_user.id
    )
    return ApiResponse(data=ClubMembershipResponse.model_validate(membership))


# =============================================================================
# 8. ANNOUNCEMENTS & TARGETED COMMUNICATION
# =============================================================================
@router.get("/announcements", response_model=ApiResponse[dict])
async def list_announcements(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    priority: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
) -> ApiResponse[dict]:
    """List institutional announcements."""
    result = await CampusService.list_announcements(
        db,
        tenant.tenant_id,
        priority=priority,
        status=status_filter,
        search=search,
        page=page,
        limit=limit,
    )
    items = []
    for a in result["items"]:
        item = AnnouncementResponse.model_validate(a)
        if a.created_by:
            item.created_by_name = f"{a.created_by.first_name} {a.created_by.last_name}"
        if a.published_by:
            item.published_by_name = f"{a.published_by.first_name} {a.published_by.last_name}"
        item.audiences = [
            AnnouncementAudienceItem(
                target_type=aud.target_type,
                target_id=aud.target_id,
                filter_metadata=aud.filter_metadata,
            )
            for aud in a.audiences
        ]
        items.append(item)

    result["items"] = items
    return ApiResponse(data=result)


@router.post(
    "/announcements",
    response_model=ApiResponse[AnnouncementResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_announcement(
    payload: AnnouncementCreate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ANNOUNCEMENTS_CREATE))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AnnouncementResponse]:
    """Draft and broadcast a targeted institutional announcement."""
    ann = await CampusService.create_announcement(db, tenant.tenant_id, payload, current_user.id)
    return ApiResponse(data=AnnouncementResponse.model_validate(ann))


@router.post("/announcements/audience-preview", response_model=ApiResponse[AudiencePreviewResponse])
async def preview_announcement_audience(
    payload: AudiencePreviewRequest,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AudiencePreviewResponse]:
    """Preview resolved recipient count and sample audience before publishing."""
    preview = await CampusService.preview_audience(db, tenant.tenant_id, payload.audiences)
    return ApiResponse(data=preview)


@router.post("/announcements/{announcement_id}/publish", response_model=ApiResponse[AnnouncementResponse])
async def publish_announcement(
    announcement_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(require_permission(ANNOUNCEMENTS_PUBLISH))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[AnnouncementResponse]:
    """Publish announcement and dispatch in-app notifications in batch."""
    ann = await CampusService.publish_announcement(db, tenant.tenant_id, announcement_id, current_user.id)
    return ApiResponse(data=AnnouncementResponse.model_validate(ann))


# =============================================================================
# 9. NOTIFICATION CENTER & PREFERENCES
# =============================================================================
@router.get("/notifications", response_model=ApiResponse[NotificationListResponse])
async def list_notifications(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    unread_only: bool = Query(False),
    notification_type: str | None = Query(None, alias="type"),
    source_module: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
) -> ApiResponse[NotificationListResponse]:
    """Get authenticated user's notification inbox."""
    res = await NotificationService.get_user_notifications(
        db,
        tenant.tenant_id,
        current_user.id,
        unread_only=unread_only,
        notification_type=notification_type,
        source_module=source_module,
        page=page,
        limit=limit,
    )
    return ApiResponse(data=NotificationListResponse(**res))


@router.get("/notifications/unread-count", response_model=ApiResponse[UnreadCountResponse])
async def get_notification_unread_count(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[UnreadCountResponse]:
    """Get count of unread notifications for badge display."""
    count = await NotificationService.get_unread_count(db, tenant.tenant_id, current_user.id)
    return ApiResponse(data=UnreadCountResponse(unread_count=count))


@router.patch("/notifications/{notification_id}/read", response_model=ApiResponse[NotificationResponse])
async def mark_notification_read(
    notification_id: UUID,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[NotificationResponse]:
    """Mark a notification as read."""
    notif = await NotificationService.mark_as_read(
        db, tenant.tenant_id, current_user.id, notification_id
    )
    return ApiResponse(data=NotificationResponse.model_validate(notif))


@router.post("/notifications/read-all", response_model=ApiResponse[dict])
async def mark_all_notifications_read(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[dict]:
    """Mark all inbox notifications as read."""
    count = await NotificationService.mark_all_as_read(db, tenant.tenant_id, current_user.id)
    return ApiResponse(data={"message": f"Marked {count} notifications as read."})


@router.get("/notifications/preferences", response_model=ApiResponse[list[NotificationPreferenceItem]])
async def get_notification_preferences(
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[list[NotificationPreferenceItem]]:
    """Get current user's notification channel preferences."""
    prefs = await NotificationService.get_user_preferences(db, tenant.tenant_id, current_user.id)
    return ApiResponse(data=prefs)


@router.put("/notifications/preferences", response_model=ApiResponse[list[NotificationPreferenceItem]])
async def update_notification_preferences(
    payload: NotificationPreferenceUpdate,
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> ApiResponse[list[NotificationPreferenceItem]]:
    """Update current user's notification channel preferences."""
    prefs = await NotificationService.update_user_preferences(
        db, tenant.tenant_id, current_user.id, payload
    )
    return ApiResponse(data=prefs)
