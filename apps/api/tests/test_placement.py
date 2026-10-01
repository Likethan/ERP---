"""Comprehensive Test Suite for Placement and Career Engine."""

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import DEFAULT_ROLE_PERMISSIONS
from app.core.security import ACCESS_TOKEN_COOKIE_NAME, create_access_token, get_password_hash
from app.models.core import AcademicYear, Batch, Campus, Department, Institution, Program, Regulation
from app.models.examination import SemesterExamResult
from app.models.people import Role, StudentProfile, User, UserRoleAssignment
from app.models.placement import (
    PlacementOffer,
    PlacementOutcome,
)


def make_auth_headers(user: User, tenant_id: uuid.UUID, role_name: str) -> dict:
    """Generate authorization headers & cookies for authenticated API requests."""
    perms = DEFAULT_ROLE_PERMISSIONS.get(role_name, [])
    token = create_access_token(
        user_id=user.id,
        tenant_id=tenant_id,
        email=user.email,
        roles=[role_name],
        permissions=perms,
    )
    return {
        "Authorization": f"Bearer {token}",
        "Cookie": f"{ACCESS_TOKEN_COOKIE_NAME}={token}",
    }


@pytest.fixture
async def placement_setup(
    db_session: AsyncSession, tenant_a: Institution, tenant_b: Institution
):
    """Setup campus, program, academic year, student profile with examination results."""
    uid = uuid.uuid4().hex[:6]

    # Academic Year
    ay = AcademicYear(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        name=f"2026-2027 {uid}",
        start_date=date(2026, 6, 1),
        end_date=date(2027, 5, 31),
        is_current=True,
    )
    db_session.add(ay)

    # Campus & Dept & Program
    campus = Campus(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        code=f"CAMP-{uid}",
        name="Main Campus",
        address="Tech Park",
        city="Coimbatore",
        is_active=True,
    )
    db_session.add(campus)

    dept = Department(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        campus_id=campus.id,
        code=f"CSE-{uid}",
        name="Computer Science",
        department_type="ACADEMIC",
        is_active=True,
    )
    db_session.add(dept)

    prog = Program(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        department_id=dept.id,
        code=f"BTECH-CSE-{uid}",
        name="B.Tech Computer Science",
        degree_level="UNDERGRADUATE",
        duration_years=4,
        total_semesters=8,
        is_active=True,
    )
    db_session.add(prog)

    reg = Regulation(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        code=f"R2023-{uid}",
        title=f"Regulation 2023 {uid}",
        effective_year=2023,
        is_active=True,
    )
    db_session.add(reg)

    batch = Batch(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        program_id=prog.id,
        regulation_id=reg.id,
        name=f"Batch 2023-2027 {uid}",
        admission_year=2023,
        graduation_year=2027,
        is_active=True,
    )
    db_session.add(batch)

    # Student User
    student_user = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"candidate_{uid}@apextech.edu",
        phone_number="+919876501111",
        password_hash=get_password_hash("StudentPass123!"),
        status="ACTIVE",
        first_name="Radha",
        last_name="Krishnan",
    )
    db_session.add(student_user)
    await db_session.flush()

    # Assign STUDENT role
    role_res = await db_session.execute(select(Role).where(Role.name == "STUDENT"))
    student_role = role_res.scalar_one_or_none()
    if student_role:
        db_session.add(
            UserRoleAssignment(
                id=uuid.uuid4(),
                tenant_id=tenant_a.id,
                user_id=student_user.id,
                role_id=student_role.id,
            )
        )

    # Student Profile
    student_profile = StudentProfile(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        user_id=student_user.id,
        admission_number=f"ADM-{uid}",
        roll_number=f"23CSE{uid[:3]}",
        date_of_birth=date(2005, 5, 15),
        gender="FEMALE",
        status="ACTIVE",
        admission_date=date(2023, 8, 1),
        expected_graduation_date=date(2027, 5, 30),
        program_id=prog.id,
        batch_id=batch.id,
    )
    db_session.add(student_profile)

    # Placement Officer User
    officer_user = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_a.id,
        email=f"placement_officer_{uid}@apextech.edu",
        phone_number="+919876502222",
        password_hash=get_password_hash("OfficerPass123!"),
        status="ACTIVE",
        first_name="Placement",
        last_name="Director",
    )
    db_session.add(officer_user)
    await db_session.flush()

    role_res = await db_session.execute(select(Role).where(Role.name == "PLACEMENT_OFFICER"))
    officer_role = role_res.scalar_one_or_none()
    if officer_role:
        db_session.add(
            UserRoleAssignment(
                id=uuid.uuid4(),
                tenant_id=tenant_a.id,
                user_id=officer_user.id,
                role_id=officer_role.id,
            )
        )

    await db_session.commit()
    await db_session.refresh(student_profile)

    student_headers = make_auth_headers(student_user, tenant_a.id, "STUDENT")
    officer_headers = make_auth_headers(officer_user, tenant_a.id, "PLACEMENT_OFFICER")

    return {
        "tenant_a": tenant_a,
        "tenant_b": tenant_b,
        "academic_year": ay,
        "program": prog,
        "department": dept,
        "student_user": student_user,
        "student_profile": student_profile,
        "student_headers": student_headers,
        "officer_user": officer_user,
        "officer_headers": officer_headers,
    }


@pytest.mark.asyncio
async def test_company_and_contact_lifecycle(
    client: AsyncClient,
    placement_setup: dict,
):
    """Verify company registration, contact management, and search filtering."""
    officer_headers = placement_setup["officer_headers"]

    # 1. Create Company
    comp_payload = {
        "name": "Acme Robotics Corp",
        "legal_name": "Acme Robotics Technologies Pvt Ltd",
        "industry": "Robotics & AI",
        "company_type": "PRODUCT",
        "tier": "TIER_1",
        "website": "https://acmerobotics.com",
        "headquarters_location": "Bengaluru",
        "status": "ACTIVE",
        "contacts": [
            {
                "name": "Rajesh Kumar",
                "email": "rajesh@acmerobotics.com",
                "phone": "+919988776655",
                "designation": "Head of University Hiring",
                "is_primary": True,
            }
        ],
    }
    res = await client.post(
        "/api/v1/placement/companies",
        json=comp_payload,
        headers=officer_headers,
    )
    assert res.status_code == 201, res.text
    comp_data = res.json()["data"]
    comp_id = comp_data["id"]
    assert comp_data["name"] == "Acme Robotics Corp"
    assert comp_data["tier"] == "TIER_1"

    # 2. Get Company Details
    res_get = await client.get(
        f"/api/v1/placement/companies/{comp_id}",
        headers=officer_headers,
    )
    assert res_get.status_code == 200
    detail = res_get.json()["data"]
    assert len(detail["contacts"]) == 1
    assert detail["contacts"][0]["name"] == "Rajesh Kumar"

    # 3. Add Secondary Contact
    contact_payload = {
        "name": "Priya Sharma",
        "email": "priya@acmerobotics.com",
        "phone": "+919988776656",
        "designation": "Campus Recruiter",
        "is_primary": False,
    }
    res_contact = await client.post(
        f"/api/v1/placement/companies/{comp_id}/contacts",
        json=contact_payload,
        headers=officer_headers,
    )
    assert res_contact.status_code == 201

    # 4. List Companies with Filter
    res_list = await client.get(
        "/api/v1/placement/companies?tier=TIER_1&search=Acme",
        headers=officer_headers,
    )
    assert res_list.status_code == 200
    items = res_list.json()["data"]
    assert any(c["id"] == comp_id for c in items)


@pytest.mark.asyncio
async def test_job_drive_and_positions_creation(
    client: AsyncClient,
    placement_setup: dict,
):
    """Verify recruitment drive scheduling, position creation, and status transitions."""
    officer_headers = placement_setup["officer_headers"]
    ay = placement_setup["academic_year"]

    # Create Company first
    comp_res = await client.post(
        "/api/v1/placement/companies",
        json={
            "name": "Google Cloud",
            "industry": "Cloud Computing",
            "tier": "DREAM",
        },
        headers=officer_headers,
    )
    company_id = comp_res.json()["data"]["id"]

    now = datetime.now(timezone.utc)
    drive_payload = {
        "company_id": company_id,
        "academic_year_id": str(ay.id),
        "title": "Google Cloud Campus Drive 2026",
        "description": "Annual graduate recruitment for engineering and analytics",
        "application_open_at": (now - timedelta(days=1)).isoformat(),
        "application_close_at": (now + timedelta(days=10)).isoformat(),
        "drive_date": (date.today() + timedelta(days=15)).isoformat(),
        "mode": "ON_CAMPUS",
        "status": "DRAFT",
        "positions": [
            {
                "title": "Cloud Software Engineer",
                "employment_type": "FULL_TIME",
                "vacancy_count": 5,
                "ctc": "2400000.00",
                "skills_json": ["Go", "Python", "Kubernetes"],
                "eligibility_rules": [
                    {
                        "rule_type": "CGPA_MINIMUM",
                        "operator": "GTE",
                        "value_json": 8.0,
                        "is_required": True,
                        "sequence": 1,
                    },
                    {
                        "rule_type": "BACKLOG_NONE",
                        "operator": "EQ",
                        "value_json": 0,
                        "is_required": True,
                        "sequence": 2,
                    },
                ],
            }
        ],
    }

    res_drive = await client.post(
        "/api/v1/placement/drives",
        json=drive_payload,
        headers=officer_headers,
    )
    assert res_drive.status_code == 201, res_drive.text
    drive_data = res_drive.json()["data"]
    drive_id = drive_data["id"]
    assert drive_data["drive_code"].startswith("DRV-")
    assert drive_data["status"] == "DRAFT"

    # Status Transition: DRAFT -> PUBLISHED -> APPLICATIONS_OPEN
    res_pub = await client.post(
        f"/api/v1/placement/drives/{drive_id}/status?new_status=PUBLISHED",
        headers=officer_headers,
    )
    assert res_pub.status_code == 200
    assert res_pub.json()["data"]["status"] == "PUBLISHED"

    res_open = await client.post(
        f"/api/v1/placement/drives/{drive_id}/status?new_status=APPLICATIONS_OPEN",
        headers=officer_headers,
    )
    assert res_open.status_code == 200
    assert res_open.json()["data"]["status"] == "APPLICATIONS_OPEN"

    # Check Drive Detail
    res_detail = await client.get(
        f"/api/v1/placement/drives/{drive_id}",
        headers=officer_headers,
    )
    assert res_detail.status_code == 200
    d_detail = res_detail.json()["data"]
    assert len(d_detail["positions"]) == 1
    assert d_detail["positions"][0]["title"] == "Cloud Software Engineer"
    assert len(d_detail["positions"][0]["eligibility_rules"]) == 2


@pytest.mark.asyncio
async def test_automated_eligibility_and_application_workflow(
    client: AsyncClient,
    placement_setup: dict,
    db_session: AsyncSession,
):
    """Verify automated eligibility rule evaluation (pass & fail) and application lifecycle."""
    officer_headers = placement_setup["officer_headers"]
    student_headers = placement_setup["student_headers"]
    student_profile = placement_setup["student_profile"]
    prog = placement_setup["program"]
    ay = placement_setup["academic_year"]

    # 1. Company and Drive with 2 positions (Position 1: CGPA >= 7.0, Position 2: CGPA >= 9.5)
    comp_res = await client.post(
        "/api/v1/placement/companies",
        json={"name": "Microsoft India", "industry": "Software", "tier": "DREAM"},
        headers=officer_headers,
    )
    comp_id = comp_res.json()["data"]["id"]

    now = datetime.now(timezone.utc)
    drive_res = await client.post(
        "/api/v1/placement/drives",
        json={
            "company_id": comp_id,
            "academic_year_id": str(ay.id),
            "title": "Microsoft Campus Recruitment",
            "application_open_at": (now - timedelta(days=1)).isoformat(),
            "application_close_at": (now + timedelta(days=5)).isoformat(),
            "drive_date": (date.today() + timedelta(days=10)).isoformat(),
            "status": "APPLICATIONS_OPEN",
            "positions": [
                {
                    "title": "Software Engineer (Eligible)",
                    "ctc": "1800000.00",
                    "eligibility_rules": [
                        {
                            "rule_type": "CGPA_MINIMUM",
                            "operator": "GTE",
                            "value_json": 7.0,
                            "is_required": True,
                        },
                        {
                            "rule_type": "PROGRAM_ALLOWED",
                            "operator": "IN",
                            "value_json": [prog.code],
                            "is_required": True,
                        },
                    ],
                },
                {
                    "title": "Research Scientist (High CGPA Bar)",
                    "ctc": "3500000.00",
                    "eligibility_rules": [
                        {
                            "rule_type": "CGPA_MINIMUM",
                            "operator": "GTE",
                            "value_json": 9.5,
                            "is_required": True,
                        }
                    ],
                },
            ],
        },
        headers=officer_headers,
    )
    drive_detail = (
        await client.get(
            f"/api/v1/placement/drives/{drive_res.json()['data']['id']}",
            headers=officer_headers,
        )
    ).json()["data"]

    pos_eligible = next(p for p in drive_detail["positions"] if "Eligible" in p["title"])
    pos_high_bar = next(p for p in drive_detail["positions"] if "High CGPA" in p["title"])

    # 2. Add published SemesterExamResult for student to achieve CGPA 8.5
    exam_res = SemesterExamResult(
        id=uuid.uuid4(),
        tenant_id=placement_setup["tenant_a"].id,
        student_id=student_profile.id,
        course_offering_id=uuid.uuid4(),
        exam_term_id=uuid.uuid4(),
        grade_letter="A",
        grade_point=Decimal("8.5"),
        credits_earned=Decimal("20.0"),
        result_status="PASS",
        publication_status="PUBLISHED",
    )
    db_session.add(exam_res)
    await db_session.commit()

    # 3. Check Eligibility via API as student
    res_elig1 = await client.get(
        f"/api/v1/placement/positions/{pos_eligible['id']}/my-eligibility",
        headers=student_headers,
    )
    assert res_elig1.status_code == 200
    elig1_data = res_elig1.json()["data"]
    assert elig1_data["is_eligible"] is True
    assert elig1_data["source_data_snapshot"]["cgpa"] == 8.5

    # Check High Bar (CGPA 8.5 < 9.5 -> False)
    res_elig2 = await client.get(
        f"/api/v1/placement/positions/{pos_high_bar['id']}/my-eligibility",
        headers=student_headers,
    )
    assert res_elig2.status_code == 200
    elig2_data = res_elig2.json()["data"]
    assert elig2_data["is_eligible"] is False

    # 4. Attempt to apply for High Bar role -> Expect 422 Validation Error
    fail_app = await client.post(
        "/api/v1/placement/applications",
        json={"job_position_id": pos_high_bar["id"]},
        headers=student_headers,
    )
    assert fail_app.status_code == 422
    assert "does not satisfy eligibility criteria" in fail_app.json()["error"]["message"]

    # 5. Successfully apply for Eligible position
    app_res = await client.post(
        "/api/v1/placement/applications",
        json={"job_position_id": pos_eligible["id"]},
        headers=student_headers,
    )
    assert app_res.status_code == 201
    app_data = app_res.json()["data"]
    app_id = app_data["id"]
    assert app_data["status"] == "APPLIED"
    assert app_data["application_number"].startswith("APP-")

    # 6. Prevent Duplicate Application
    dup_res = await client.post(
        "/api/v1/placement/applications",
        json={"job_position_id": pos_eligible["id"]},
        headers=student_headers,
    )
    assert dup_res.status_code == 409

    # 7. Student checks their applications
    my_apps = await client.get(
        "/api/v1/placement/applications/me",
        headers=student_headers,
    )
    assert my_apps.status_code == 200
    assert any(a["id"] == app_id for a in my_apps.json()["data"])

    # 8. Placement Officer updates application status to SHORTLISTED
    status_update = await client.post(
        f"/api/v1/placement/applications/{app_id}/status",
        json={"to_status": "SHORTLISTED", "reason": "Candidate cleared resume screening"},
        headers=officer_headers,
    )
    assert status_update.status_code == 200
    assert status_update.json()["data"]["status"] == "SHORTLISTED"


@pytest.mark.asyncio
async def test_interview_pipeline_and_offer_lifecycle(
    client: AsyncClient,
    placement_setup: dict,
    db_session: AsyncSession,
):
    """Verify interview scheduling, evaluation scoring, offer issuance, and candidate acceptance."""
    officer_headers = placement_setup["officer_headers"]
    student_headers = placement_setup["student_headers"]
    student_profile = placement_setup["student_profile"]
    ay = placement_setup["academic_year"]

    # Setup Company & Drive & Position
    comp_res = await client.post(
        "/api/v1/placement/companies",
        json={"name": "Amazon Web Services", "industry": "Cloud", "tier": "SUPER_DREAM"},
        headers=officer_headers,
    )
    comp_id = comp_res.json()["data"]["id"]

    now = datetime.now(timezone.utc)
    drive_res = await client.post(
        "/api/v1/placement/drives",
        json={
            "company_id": comp_id,
            "academic_year_id": str(ay.id),
            "title": "AWS SDE Drive 2026",
            "application_open_at": (now - timedelta(days=1)).isoformat(),
            "application_close_at": (now + timedelta(days=5)).isoformat(),
            "drive_date": (date.today() + timedelta(days=7)).isoformat(),
            "status": "APPLICATIONS_OPEN",
            "positions": [
                {
                    "title": "SDE-1",
                    "ctc": "2800000.00",
                    "eligibility_rules": [],
                }
            ],
        },
        headers=officer_headers,
    )
    drive_detail = (
        await client.get(
            f"/api/v1/placement/drives/{drive_res.json()['data']['id']}",
            headers=officer_headers,
        )
    ).json()["data"]
    pos_id = drive_detail["positions"][0]["id"]

    # Student Applies
    app_res = await client.post(
        "/api/v1/placement/applications",
        json={"job_position_id": pos_id},
        headers=student_headers,
    )
    app_id = app_res.json()["data"]["id"]

    # 1. Create Interview Round
    round_res = await client.post(
        f"/api/v1/placement/positions/{pos_id}/interview-rounds",
        json={
            "name": "Technical Problem Solving & DSA",
            "sequence": 1,
            "round_type": "TECHNICAL",
        },
        headers=officer_headers,
    )
    assert round_res.status_code == 201
    round_id = round_res.json()["data"]["id"]

    # 2. Schedule Interview Slot
    sched_res = await client.post(
        "/api/v1/placement/interviews/schedule",
        json={
            "interview_round_id": round_id,
            "application_id": app_id,
            "scheduled_at": (now + timedelta(days=2)).isoformat(),
            "duration_minutes": 45,
            "meeting_url": "https://meet.campusos.internal/aws-sde-round1",
            "interviewer": "Senior SDE Amazon",
        },
        headers=officer_headers,
    )
    assert sched_res.status_code == 201
    sched_id = sched_res.json()["data"]["id"]

    # 3. Submit Evaluation (Pass + STRONG_HIRE)
    eval_res = await client.post(
        f"/api/v1/placement/interviews/{sched_id}/evaluate",
        json={
            "result": "PASS",
            "score": "9.2",
            "recommendation": "STRONG_HIRE",
            "feedback": "Exceptional clarity on algorithms and concurrency control.",
            "internal_notes": "Candidate would be a stellar fit for high-throughput distributed systems.",
        },
        headers=officer_headers,
    )
    assert eval_res.status_code == 200
    assert eval_res.json()["data"]["result"] == "PASS"

    # Application should now be SELECTED
    app_check = (
        await client.get(
            f"/api/v1/placement/applications?position_id={pos_id}",
            headers=officer_headers,
        )
    ).json()["data"][0]
    assert app_check["status"] == "SELECTED"

    # 4. Issue Formal Placement Offer
    offer_res = await client.post(
        "/api/v1/placement/offers",
        json={
            "student_id": str(student_profile.id),
            "job_position_id": pos_id,
            "company_id": comp_id,
            "placement_application_id": app_id,
            "offer_date": date.today().isoformat(),
            "designation": "Software Development Engineer 1",
            "ctc": "2800000.00",
            "currency": "INR",
            "work_location": "Hyderabad",
            "joining_date": date(2027, 7, 1).isoformat(),
            "employment_type": "FULL_TIME",
            "offer_expiry_date": (date.today() + timedelta(days=14)).isoformat(),
        },
        headers=officer_headers,
    )
    assert offer_res.status_code == 201, offer_res.text
    offer_data = offer_res.json()["data"]
    offer_id = offer_data["id"]
    assert offer_data["status"] == "ISSUED"
    assert offer_data["offer_number"].startswith("OFF-")

    # 5. Student views my offers
    student_offers = await client.get(
        "/api/v1/placement/offers/me",
        headers=student_headers,
    )
    assert student_offers.status_code == 200
    assert len(student_offers.json()["data"]) == 1

    # 6. Student ACCEPTS Offer
    accept_res = await client.post(
        f"/api/v1/placement/offers/{offer_id}/respond",
        json={"decision": "ACCEPT"},
        headers=student_headers,
    )
    assert accept_res.status_code == 200
    assert accept_res.json()["data"]["status"] == "ACCEPTED"

    # 7. Verify Student Availability Status is PLACED & Outcome Exists
    prof_res = await client.get(
        "/api/v1/placement/profile/me",
        headers=student_headers,
    )
    assert prof_res.status_code == 200
    assert prof_res.json()["data"]["availability_status"] == "PLACED"

    outcome = await db_session.scalar(
        select(PlacementOutcome).where(
            PlacementOutcome.student_id == student_profile.id,
            PlacementOutcome.accepted_offer_id == uuid.UUID(offer_id),
        )
    )
    assert outcome is not None
    assert outcome.outcome == "PLACED"
    assert outcome.ctc == Decimal("2800000.00")

    # 8. Check Analytics Telemetry
    analytics_res = await client.get(
        f"/api/v1/placement/analytics?academic_year_id={ay.id}",
        headers=officer_headers,
    )
    assert analytics_res.status_code == 200
    stats = analytics_res.json()["data"]
    assert stats["placed_students"] >= 1
    assert stats["highest_ctc"] >= 2800000.0
    assert stats["total_offers"] >= 1


@pytest.mark.asyncio
async def test_cross_tenant_isolation_placement(
    client: AsyncClient,
    placement_setup: dict,
    db_session: AsyncSession,
):
    """Verify strict multi-tenancy isolation between Tenant A and Tenant B in Placements."""
    officer_headers = placement_setup["officer_headers"]
    tenant_b = placement_setup["tenant_b"]

    # Create user in Tenant B
    uid = uuid.uuid4().hex[:6]
    user_b = User(
        id=uuid.uuid4(),
        primary_tenant_id=tenant_b.id,
        email=f"officer_b_{uid}@beaconuni.edu",
        phone_number="+919876509999",
        password_hash=get_password_hash("BeaconPass123!"),
        status="ACTIVE",
        first_name="Beacon",
        last_name="Placement",
    )
    db_session.add(user_b)
    await db_session.flush()

    role_res = await db_session.execute(select(Role).where(Role.name == "PLACEMENT_OFFICER"))
    officer_role = role_res.scalar_one_or_none()
    if officer_role:
        db_session.add(
            UserRoleAssignment(
                id=uuid.uuid4(),
                tenant_id=tenant_b.id,
                user_id=user_b.id,
                role_id=officer_role.id,
            )
        )
    await db_session.commit()

    headers_b = make_auth_headers(user_b, tenant_b.id, "PLACEMENT_OFFICER")

    # Officer A creates company in Tenant A
    res_a = await client.post(
        "/api/v1/placement/companies",
        json={"name": "Tesla Energy", "industry": "Renewables", "tier": "TIER_1"},
        headers=officer_headers,
    )
    comp_a_id = res_a.json()["data"]["id"]

    # Officer B searches companies -> Should NOT see Tesla Energy
    res_b_list = await client.get(
        "/api/v1/placement/companies?search=Tesla",
        headers=headers_b,
    )
    assert res_b_list.status_code == 200
    assert len(res_b_list.json()["data"]) == 0

    # Officer B direct access to comp_a_id -> Expect 404 Not Found
    res_b_get = await client.get(
        f"/api/v1/placement/companies/{comp_a_id}",
        headers=headers_b,
    )
    assert res_b_get.status_code == 404
