"""Comprehensive Test Suite for Campus Events, Clubs, Announcements, and Notification Engine."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash
from app.models.campus import (
    EventCategory,
    EventVenue,
    Notification,
)
from app.models.core import Campus, Department, Institution, Program
from app.models.people import Role, StudentProfile, User, UserRoleAssignment


@pytest.fixture
async def campus_setup(
    db_session: AsyncSession, tenant_a: Institution, tenant_b: Institution
):
    """Setup campus, department, program, student, and venue fixtures."""
    uid = uuid.uuid4().hex[:6]

    # Campus A
    campus_a = Campus(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        code=f"CAMP-A-{uid}",
        name=f"Main Campus {uid}",
        address="100 Technology Rd",
        city="Coimbatore",
        is_active=True,
    )
    db_session.add(campus_a)

    # Department A
    dept_a = Department(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        campus_id=campus_a.id,
        code=f"CSE-{uid}",
        name="Computer Science & Engineering",
        department_type="ACADEMIC",
        is_active=True,
    )
    db_session.add(dept_a)

    # Program A
    prog_a = Program(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        department_id=dept_a.id,
        code=f"BTECH-CSE-{uid}",
        name="B.Tech Computer Science",
        degree_level="UNDERGRADUATE",
        duration_years=4,
        total_semesters=8,
        is_active=True,
    )
    db_session.add(prog_a)

    # Venue A
    venue_a = EventVenue(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        campus_id=campus_a.id,
        code=f"AUD-{uid}",
        name="Main Auditorium",
        building="Sir CV Raman Block",
        floor="Ground",
        capacity=500,
        status="ACTIVE",
    )
    db_session.add(venue_a)

    # Category A
    cat_a = EventCategory(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        code=f"HACKATHON-{uid}",
        name="Hackathons & Competitions",
        description="Coding contests",
        is_active=True,
    )
    db_session.add(cat_a)

    # Student User & Profile
    student_user = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"student_{uid}@campusos.internal",
        phone_number="+919876500001",
        password_hash=get_password_hash("StudentPass123!"),
        status="ACTIVE",
        first_name="Ada",
        last_name="Lovelace",
    )
    db_session.add(student_user)
    await db_session.flush()

    student_role = (
        await db_session.execute(select(Role).where(Role.name == "STUDENT"))
    ).scalar_one_or_none()
    if student_role:
        db_session.add(
            UserRoleAssignment(
                id=uuid.uuid4(),
                tenant_id=tenant_a.id,
                user_id=student_user.id,
                role_id=student_role.id,
            )
        )

    # Batch mock for student profile
    from app.models.core import Batch, Regulation
    reg = Regulation(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        code=f"R2026-{uid}",
        title="Regulation 2026",
        effective_year=2026,
    )
    db_session.add(reg)
    await db_session.flush()

    batch = Batch(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        program_id=prog_a.id,
        regulation_id=reg.id,
        name=f"Batch 2026-2030 {uid}",
        admission_year=2026,
        graduation_year=2030,
        is_active=True,
    )
    db_session.add(batch)
    await db_session.flush()

    student_profile = StudentProfile(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        user_id=student_user.id,
        admission_number=f"ADM-{uid}",
        registration_number=f"REG-{uid}",
        roll_number=f"26CSE{uid[:3].upper()}",
        date_of_birth=datetime(2004, 1, 1).date(),
        gender="FEMALE",
        status="ACTIVE",
        admission_date=datetime(2026, 8, 1).date(),
        expected_graduation_date=datetime(2030, 5, 31).date(),
        program_id=prog_a.id,
        batch_id=batch.id,
    )
    db_session.add(student_profile)

    await db_session.commit()

    return {
        "campus": campus_a,
        "dept": dept_a,
        "program": prog_a,
        "venue": venue_a,
        "category": cat_a,
        "student_user": student_user,
        "student_profile": student_profile,
    }


def auth_headers(user: User, tenant_id: uuid.UUID) -> dict:
    """Generate authorization headers for authenticated API requests."""
    token = create_access_token(
        user_id=user.id,
        tenant_id=tenant_id,
        email=user.email,
        roles=["SUPER_ADMIN"],
        permissions=[],
    )
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# 1. EVENT MANAGEMENT TESTS
# =============================================================================
@pytest.mark.asyncio
async def test_event_lifecycle_and_venue_conflict(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
    super_admin_user: User,
    campus_setup: dict,
):
    headers = auth_headers(super_admin_user, tenant_a.id)
    venue = campus_setup["venue"]
    category = campus_setup["category"]
    campus = campus_setup["campus"]

    now = datetime.now(UTC)
    start_time = now + timedelta(days=2, hours=10)
    end_time = now + timedelta(days=2, hours=12)

    # 1. Create Event 1 at Venue
    create_payload = {
        "campus_id": str(campus.id),
        "category_id": str(category.id),
        "title": "AI & Cloud Summit 2026",
        "description": "Annual technical symposium",
        "organizer_type": "CAMPUS",
        "start_at": start_time.isoformat(),
        "end_at": end_time.isoformat(),
        "venue_id": str(venue.id),
        "capacity": 300,
        "requires_registration": True,
        "requires_attendance": True,
    }
    res1 = await client.post("/api/v1/events", json=create_payload, headers=headers)
    assert res1.status_code == 201
    event1 = res1.json()["data"]
    assert event1["title"] == "AI & Cloud Summit 2026"
    assert event1["status"] == "DRAFT"

    # 2. Publish Event 1
    res_pub = await client.post(f"/api/v1/events/{event1['id']}/publish", headers=headers)
    assert res_pub.status_code == 200
    assert res_pub.json()["data"]["status"] in ("PUBLISHED", "REGISTRATION_OPEN")

    # 3. Create Overlapping Event at Same Venue -> Expect Conflict Validation
    overlap_payload = {
        "campus_id": str(campus.id),
        "category_id": str(category.id),
        "title": "Conflicting Workshop",
        "start_at": (start_time + timedelta(minutes=30)).isoformat(),
        "end_at": (end_time + timedelta(minutes=60)).isoformat(),
        "venue_id": str(venue.id),
        "capacity": 100,
    }
    res_conflict = await client.post("/api/v1/events", json=overlap_payload, headers=headers)
    assert res_conflict.status_code == 422
    assert "Venue conflict" in res_conflict.json()["error"]["message"]

    # 4. Capacity exceeding venue maximum capacity -> Expect Validation
    over_capacity_payload = {
        "campus_id": str(campus.id),
        "category_id": str(category.id),
        "title": "Mega Gathering",
        "start_at": (now + timedelta(days=5)).isoformat(),
        "end_at": (now + timedelta(days=5, hours=3)).isoformat(),
        "venue_id": str(venue.id),
        "capacity": 2000,  # Venue max is 500
    }
    res_cap = await client.post("/api/v1/events", json=over_capacity_payload, headers=headers)
    assert res_cap.status_code == 422
    assert "exceeds venue maximum capacity" in res_cap.json()["error"]["message"]


# =============================================================================
# 2. EVENT REGISTRATION & ATTENDANCE TESTS
# =============================================================================
@pytest.mark.asyncio
async def test_event_registration_and_check_in_flow(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
    super_admin_user: User,
    campus_setup: dict,
):
    admin_hdr = auth_headers(super_admin_user, tenant_a.id)
    student_user = campus_setup["student_user"]
    student_hdr = auth_headers(student_user, tenant_a.id)
    campus = campus_setup["campus"]
    venue = campus_setup["venue"]

    now = datetime.now(UTC)
    # 1. Create and publish event
    ev_payload = {
        "campus_id": str(campus.id),
        "title": "Robotics Championship",
        "start_at": (now + timedelta(days=3)).isoformat(),
        "end_at": (now + timedelta(days=3, hours=4)).isoformat(),
        "venue_id": str(venue.id),
        "capacity": 50,
        "requires_registration": True,
        "requires_attendance": True,
    }
    res_ev = await client.post("/api/v1/events", json=ev_payload, headers=admin_hdr)
    assert res_ev.status_code == 201
    event_id = res_ev.json()["data"]["id"]

    await client.post(f"/api/v1/events/{event_id}/publish", headers=admin_hdr)

    # 2. Student self-registration
    res_reg = await client.post(f"/api/v1/events/{event_id}/register", headers=student_hdr)
    assert res_reg.status_code == 201
    reg_data = res_reg.json()["data"]
    assert reg_data["status"] == "REGISTERED"
    reg_code = reg_data["registration_code"]

    # Verify notification sent to student
    notif_stmt = select(Notification).where(
        Notification.recipient_user_id == student_user.id
    )
    notif = (await db_session.execute(notif_stmt)).scalar_one_or_none()
    assert notif is not None
    assert "Registration Confirmed" in notif.title

    # 3. Duplicate registration prevention
    res_dup = await client.post(f"/api/v1/events/{event_id}/register", headers=student_hdr)
    assert res_dup.status_code in (400, 409, 422)

    # 4. Check-in student by staff/admin using registration code
    checkin_payload = {
        "registration_code": reg_code,
        "verification_method": "MANUAL",
        "remarks": "ID card verified",
    }
    res_chk = await client.post(
        f"/api/v1/events/{event_id}/check-in", json=checkin_payload, headers=admin_hdr
    )
    assert res_chk.status_code == 201
    chk_data = res_chk.json()["data"]
    assert chk_data["attendance_status"] == "PRESENT"

    # 5. Prevent duplicate check-in
    res_dup_chk = await client.post(
        f"/api/v1/events/{event_id}/check-in", json=checkin_payload, headers=admin_hdr
    )
    assert res_dup_chk.status_code in (400, 409, 422)

    # 6. Undo check-in
    res_undo = await client.post(
        f"/api/v1/events/{event_id}/undo-check-in?student_id={campus_setup['student_profile'].id}",
        headers=admin_hdr,
    )
    assert res_undo.status_code == 200

    # 7. QR Token Generation & Verification Check-In
    res_qr = await client.get(f"/api/v1/events/{event_id}/qr-token", headers=admin_hdr)
    assert res_qr.status_code == 200
    qr_token = res_qr.json()["data"]["qr_token"]

    # Student checks in via QR token
    res_qr_chk = await client.post(
        f"/api/v1/events/{event_id}/qr-check-in",
        json={"qr_token": qr_token},
        headers=student_hdr,
    )
    assert res_qr_chk.status_code == 201
    assert res_qr_chk.json()["data"]["verification_method"] == "QR"


# =============================================================================
# 3. CLUB MANAGEMENT & WORKFLOW TESTS
# =============================================================================
@pytest.mark.asyncio
async def test_club_creation_and_membership_workflow(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
    super_admin_user: User,
    campus_setup: dict,
):
    admin_hdr = auth_headers(super_admin_user, tenant_a.id)
    student_user = campus_setup["student_user"]
    student_profile = campus_setup["student_profile"]
    student_hdr = auth_headers(student_user, tenant_a.id)
    uid = uuid.uuid4().hex[:6]

    # 1. Student proposes a club -> PENDING_APPROVAL
    club_payload = {
        "code": f"AI-SOC-{uid}",
        "name": f"Artificial Intelligence Society {uid}",
        "category": "TECHNICAL",
        "description": "Advancing machine intelligence research",
        "student_lead_id": str(student_profile.id),
    }
    res_club = await client.post("/api/v1/clubs", json=club_payload, headers=student_hdr)
    assert res_club.status_code == 201
    club_id = res_club.json()["data"]["id"]
    assert res_club.json()["data"]["status"] == "PENDING_APPROVAL"

    # 2. Administrator approves the club -> ACTIVE
    res_app = await client.post(f"/api/v1/clubs/{club_id}/approve", headers=admin_hdr)
    assert res_app.status_code == 200
    assert res_app.json()["data"]["status"] == "ACTIVE"

    # 3. Create a second student to request membership
    s2_user = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"member_{uid}@campusos.internal",
        phone_number="+919876500002",
        password_hash=get_password_hash("MemberPass123!"),
        status="ACTIVE",
        first_name="Charles",
        last_name="Babbage",
    )
    db_session.add(s2_user)
    await db_session.flush()

    s2_profile = StudentProfile(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        user_id=s2_user.id,
        admission_number=f"ADM2-{uid}",
        registration_number=f"REG2-{uid}",
        roll_number=f"26CSE2{uid[:2].upper()}",
        date_of_birth=datetime(2004, 2, 2).date(),
        gender="MALE",
        status="ACTIVE",
        admission_date=datetime(2026, 8, 1).date(),
        expected_graduation_date=datetime(2030, 5, 31).date(),
        program_id=campus_setup["program"].id,
        batch_id=campus_setup["student_profile"].batch_id,
    )
    db_session.add(s2_profile)
    await db_session.commit()

    s2_hdr = auth_headers(s2_user, tenant_a.id)

    # Student 2 requests membership
    res_mem = await client.post(
        f"/api/v1/clubs/{club_id}/membership",
        json={"role": "MEMBER"},
        headers=s2_hdr,
    )
    assert res_mem.status_code == 201
    mem_id = res_mem.json()["data"]["id"]
    assert res_mem.json()["data"]["status"] == "PENDING"

    # Admin reviews and approves membership
    res_review = await client.patch(
        f"/api/v1/clubs/{club_id}/members/{mem_id}",
        json={"status": "ACTIVE", "role": "EVENT_COORDINATOR"},
        headers=admin_hdr,
    )
    assert res_review.status_code == 200
    assert res_review.json()["data"]["status"] == "ACTIVE"
    assert res_review.json()["data"]["role"] == "EVENT_COORDINATOR"


# =============================================================================
# 4. ANNOUNCEMENTS & TARGETED NOTIFICATIONS TESTS
# =============================================================================
@pytest.mark.asyncio
async def test_announcements_audience_and_batch_notifications(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
    super_admin_user: User,
    campus_setup: dict,
):
    admin_hdr = auth_headers(super_admin_user, tenant_a.id)
    student_user = campus_setup["student_user"]
    dept = campus_setup["dept"]

    # 1. Preview Audience
    preview_req = {
        "audiences": [
            {"target_type": "DEPARTMENT", "target_id": str(dept.id)},
            {"target_type": "ALL_STUDENTS"},
        ]
    }
    res_prev = await client.post(
        "/api/v1/announcements/audience-preview", json=preview_req, headers=admin_hdr
    )
    assert res_prev.status_code == 200
    prev_data = res_prev.json()["data"]
    assert prev_data["total_recipients"] >= 1
    assert prev_data["students_count"] >= 1

    # 2. Create and Publish Announcement
    ann_payload = {
        "title": "Semester 7 Project Review Schedule",
        "summary": "Mandatory project presentation dates announced",
        "content": "All students must submit documentation before Friday.",
        "priority": "HIGH",
        "status": "PUBLISHED",
        "audiences": [{"target_type": "ALL_STUDENTS"}],
    }
    res_ann = await client.post(
        "/api/v1/announcements", json=ann_payload, headers=admin_hdr
    )
    assert res_ann.status_code == 201
    ann_data = res_ann.json()["data"]
    assert ann_data["status"] == "PUBLISHED"

    # 3. Verify notification delivery to student
    s_hdr = auth_headers(student_user, tenant_a.id)
    res_notif = await client.get("/api/v1/notifications?unread_only=true", headers=s_hdr)
    assert res_notif.status_code == 200
    notifs = res_notif.json()["data"]["items"]
    assert len(notifs) >= 1
    target_notif = next(
        (n for n in notifs if "Semester 7 Project Review" in n["title"]), None
    )
    assert target_notif is not None

    # 4. Mark notification read
    notif_id = target_notif["id"]
    res_read = await client.patch(f"/api/v1/notifications/{notif_id}/read", headers=s_hdr)
    assert res_read.status_code == 200
    assert res_read.json()["data"]["is_read"] is True

    # 5. Notification Preferences
    res_pref = await client.get("/api/v1/notifications/preferences", headers=s_hdr)
    assert res_pref.status_code == 200
    prefs = res_pref.json()["data"]
    assert len(prefs) >= 5

    # Update preferences: disable EVENTS email
    res_up_pref = await client.put(
        "/api/v1/notifications/preferences",
        json={"preferences": [{"category": "EVENTS", "channel": "EMAIL", "is_enabled": False}]},
        headers=s_hdr,
    )
    assert res_up_pref.status_code == 200
