"""Step 36: Enterprise Customer Support, Service Desk & SLA Management Test Suite.

Validates:
1. Support Teams & Category-Based Automated Routing
2. Support Ticket Intake & SLA Policy Initialization
3. State Machine & Guarded Lifecycle Transitions
4. SLA Clock Pausing, Resumption, and Deadline Extension
5. Customer Auto-Resume upon Public Reply
6. Assignment, Reassignment, and Tier Escalation
7. Zero-Trust Segregation of Public Replies vs. Confidential Internal Notes
8. Customer Satisfaction (CSAT) Rating and Validation
9. Incident and Knowledge-Base Article Correlation
10. Strict Multi-Tenant Isolation
11. REST API Endpoints and Authorization Controls
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    PermissionDeniedException,
    ValidationException,
)
from app.core.permissions import DEFAULT_ROLE_PERMISSIONS
from app.core.security import ACCESS_TOKEN_COOKIE_NAME, create_access_token
from app.models.core import Institution
from app.models.people import User
from app.models.support import (
    SupportCategory,
    SupportMessageType,
    SupportPriority,
    SupportRequestType,
    SupportSlaState,
    SupportTicketStatus,
)
from app.schemas.support import (
    SupportTicketArticleLinkRequest,
    SupportTicketAssignRequest,
    SupportTicketCloseRequest,
    SupportTicketCreateRequest,
    SupportTicketCsatRequest,
    SupportTicketEscalateRequest,
    SupportTicketIncidentLinkRequest,
    SupportTicketMessageCreateRequest,
    SupportTicketReopenRequest,
    SupportTicketResolveRequest,
    SupportTicketTransitionRequest,
)
from app.services.support_service import SupportService, ensure_utc


def make_auth_headers(
    user: User,
    tenant_id: uuid.UUID,
    role_name: str = "INSTITUTION_ADMIN",
    custom_permissions: list[str] | None = None,
) -> dict[str, str]:
    """Helper to generate JWT bearer and cookie authorization headers."""
    perms = (
        custom_permissions
        if custom_permissions is not None
        else DEFAULT_ROLE_PERMISSIONS.get(role_name, [])
    )
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


# =============================================================================
# 1. SUPPORT TEAMS & CATEGORY ROUTING
# =============================================================================


@pytest.mark.asyncio
async def test_support_teams_seeding(db_session: AsyncSession, tenant_a: Institution):
    """Verify standard support teams are seeded for routing."""
    teams = await SupportService.get_or_seed_default_teams(db_session, tenant_a.id)
    await db_session.commit()

    team_codes = {t.code for t in teams}
    assert "TIER_1_OPS" in team_codes
    assert "BURSAR_FINANCE" in team_codes
    assert "ACAD_OPERATIONS" in team_codes
    assert "SECURITY_IDENTITY" in team_codes
    assert "PLATFORM_SRE" in team_codes


@pytest.mark.asyncio
async def test_category_routing_resolution(db_session: AsyncSession, tenant_a: Institution):
    """Verify intelligent category-to-team routing."""
    # Finance & Fees -> BURSAR_FINANCE
    t_fin = await SupportService.resolve_team_for_category(
        db_session, SupportCategory.FINANCE_FEES.value, tenant_a.id
    )
    assert t_fin.code == "BURSAR_FINANCE"

    # Account Access -> SECURITY_IDENTITY
    t_sec = await SupportService.resolve_team_for_category(
        db_session, SupportCategory.ACCOUNT_ACCESS.value, tenant_a.id
    )
    assert t_sec.code == "SECURITY_IDENTITY"

    # Academic Config -> ACAD_OPERATIONS
    t_acad = await SupportService.resolve_team_for_category(
        db_session, SupportCategory.ACADEMIC_CONFIG.value, tenant_a.id
    )
    assert t_acad.code == "ACAD_OPERATIONS"

    # AI Features -> PLATFORM_SRE
    t_sre = await SupportService.resolve_team_for_category(
        db_session, SupportCategory.AI_FEATURES.value, tenant_a.id
    )
    assert t_sre.code == "PLATFORM_SRE"

    # General / Unknown -> TIER_1_OPS fallback
    t_gen = await SupportService.resolve_team_for_category(
        db_session, SupportCategory.GENERAL_ASSISTANCE.value, tenant_a.id
    )
    assert t_gen.code == "TIER_1_OPS"


# =============================================================================
# 2. TICKET INTAKE & SLA INITIALIZATION
# =============================================================================


@pytest.mark.asyncio
async def test_ticket_creation_and_sla_initialization(
    db_session: AsyncSession, tenant_a: Institution, faculty_user: User
):
    """Verify ticket intake creates unique ticket number, routes team, and sets SLA deadlines."""
    payload = SupportTicketCreateRequest(
        subject="Grade Submission Portal Error 500",
        description="Faculty encountering 500 Internal Server Error when posting final marks for CS-101.",
        category=SupportCategory.EXAMINATIONS.value,
        request_type=SupportRequestType.INCIDENT.value,
        priority=SupportPriority.HIGH.value,
        related_erp_module="EXAMINATIONS",
    )

    ticket = await SupportService.create_ticket(
        db=db_session,
        requester=faculty_user,
        tenant_id=tenant_a.id,
        payload=payload,
    )
    await db_session.commit()

    assert ticket.ticket_number.startswith("TICK-")
    assert ticket.status == SupportTicketStatus.NEW.value
    assert ticket.priority == SupportPriority.HIGH.value
    assert ticket.assigned_team_name == "Academic Operations Support"
    assert ticket.response_due_at is not None
    assert ticket.resolution_due_at is not None
    assert ticket.sla_response_status == SupportSlaState.ON_TRACK.value
    assert ticket.sla_resolution_status == SupportSlaState.ON_TRACK.value

    # High priority default: 60m response, 480m resolution
    expected_response = ensure_utc(ticket.created_at) + timedelta(minutes=60)
    assert abs((ensure_utc(ticket.response_due_at) - expected_response).total_seconds()) < 60


# =============================================================================
# 3. STATE MACHINE & GUARDED LIFECYCLE TRANSITIONS
# =============================================================================


@pytest.mark.asyncio
async def test_valid_lifecycle_progression(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verify valid progression: NEW -> TRIAGED -> ASSIGNED -> IN_PROGRESS -> RESOLVED -> CLOSED."""
    payload = SupportTicketCreateRequest(
        subject="Student Attendance Sync Discrepancy",
        description="Biometric device attendance not populating for Section B.",
        category=SupportCategory.ATTENDANCE.value,
        request_type=SupportRequestType.SERVICE_REQUEST.value,
        priority=SupportPriority.MEDIUM.value,
    )
    ticket = await SupportService.create_ticket(db_session, tenant_admin_a, tenant_a.id, payload)
    await db_session.commit()

    # 1. NEW -> TRIAGED
    ticket = await SupportService.transition_status(
        db=db_session,
        ticket_id=ticket.id,
        payload=SupportTicketTransitionRequest(
            target_status=SupportTicketStatus.TRIAGED.value,
            reason="Triage review completed by operations lead.",
        ),
        actor=tenant_admin_a,
    )
    assert ticket.status == SupportTicketStatus.TRIAGED.value

    # 2. TRIAGED -> ASSIGNED
    ticket = await SupportService.transition_status(
        db=db_session,
        ticket_id=ticket.id,
        payload=SupportTicketTransitionRequest(
            target_status=SupportTicketStatus.ASSIGNED.value,
            reason="Assigned to attendance technical specialist.",
        ),
        actor=tenant_admin_a,
    )
    assert ticket.status == SupportTicketStatus.ASSIGNED.value

    # 3. ASSIGNED -> IN_PROGRESS
    ticket = await SupportService.transition_status(
        db=db_session,
        ticket_id=ticket.id,
        payload=SupportTicketTransitionRequest(
            target_status=SupportTicketStatus.IN_PROGRESS.value,
            reason="Engineer started investigating webhook logs.",
        ),
        actor=tenant_admin_a,
    )
    assert ticket.status == SupportTicketStatus.IN_PROGRESS.value

    # 4. IN_PROGRESS -> RESOLVED
    ticket = await SupportService.resolve_ticket(
        db=db_session,
        ticket_id=ticket.id,
        payload=SupportTicketResolveRequest(
            resolution_summary="Biometric sync worker restarted and sync pipeline cleared.",
        ),
        actor=tenant_admin_a,
    )
    assert ticket.status == SupportTicketStatus.RESOLVED.value
    assert ticket.resolved_at is not None
    assert ticket.sla_resolution_status == SupportSlaState.MET.value

    # 5. RESOLVED -> CLOSED
    ticket = await SupportService.close_ticket(
        db=db_session,
        ticket_id=ticket.id,
        payload=SupportTicketCloseRequest(closure_reason="Confirmed working with requester."),
        actor=tenant_admin_a,
    )
    assert ticket.status == SupportTicketStatus.CLOSED.value
    assert ticket.closed_at is not None


@pytest.mark.asyncio
async def test_invalid_lifecycle_transition_rejected(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verify invalid state transitions fail with ValidationException."""
    payload = SupportTicketCreateRequest(
        subject="Fee Payment Gateway Gateway Timeout",
        description="Timeout during semester fee settlement.",
        category=SupportCategory.FINANCE_FEES.value,
        priority=SupportPriority.URGENT.value,
    )
    ticket = await SupportService.create_ticket(db_session, tenant_admin_a, tenant_a.id, payload)
    await db_session.commit()

    # Direct jump NEW -> RESOLVED is invalid (must be triaged/assigned/in_progress)
    with pytest.raises(ValidationException):
        await SupportService.transition_status(
            db=db_session,
            ticket_id=ticket.id,
            payload=SupportTicketTransitionRequest(
                target_status=SupportTicketStatus.RESOLVED.value,
                reason="Premature resolution attempt",
            ),
            actor=tenant_admin_a,
        )

    # Direct jump NEW -> CLOSED is invalid
    with pytest.raises(ValidationException):
        await SupportService.transition_status(
            db=db_session,
            ticket_id=ticket.id,
            payload=SupportTicketTransitionRequest(
                target_status=SupportTicketStatus.CLOSED.value,
                reason="Premature closure attempt",
            ),
            actor=tenant_admin_a,
        )


# =============================================================================
# 4. SLA CLOCK PAUSING, RESUMPTION & CUSTOMER AUTO-RESUME
# =============================================================================


@pytest.mark.asyncio
async def test_sla_clock_pausing_and_resumption(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verify clock pauses in WAITING_FOR_REQUESTER and extends resolution deadline upon resumption."""
    payload = SupportTicketCreateRequest(
        subject="Student Identity Verification",
        description="Awaiting student enrollment proof copy.",
        category=SupportCategory.ACCOUNT_ACCESS.value,
        priority=SupportPriority.MEDIUM.value,
    )
    ticket = await SupportService.create_ticket(db_session, tenant_admin_a, tenant_a.id, payload)
    # Transition to IN_PROGRESS
    ticket = await SupportService.transition_status(
        db=db_session,
        ticket_id=ticket.id,
        payload=SupportTicketTransitionRequest(
            target_status=SupportTicketStatus.IN_PROGRESS.value,
            reason="Investigation started.",
        ),
        actor=tenant_admin_a,
    )
    await db_session.commit()

    original_resolution_due = ticket.resolution_due_at

    # Transition to WAITING_FOR_REQUESTER -> Clock pauses
    ticket = await SupportService.transition_status(
        db=db_session,
        ticket_id=ticket.id,
        payload=SupportTicketTransitionRequest(
            target_status=SupportTicketStatus.WAITING_FOR_REQUESTER.value,
            reason="Requested proof of enrollment from student.",
        ),
        actor=tenant_admin_a,
    )
    assert ticket.status == SupportTicketStatus.WAITING_FOR_REQUESTER.value
    assert ticket.sla_paused_at is not None
    assert ticket.sla_resolution_status == SupportSlaState.PAUSED.value

    # Simulate paused time of 30 minutes
    ticket.sla_paused_at = ticket.sla_paused_at - timedelta(minutes=30)
    await db_session.commit()

    # Resuming back to IN_PROGRESS -> Clock unpauses and deadline is extended by >= 30m
    ticket = await SupportService.transition_status(
        db=db_session,
        ticket_id=ticket.id,
        payload=SupportTicketTransitionRequest(
            target_status=SupportTicketStatus.IN_PROGRESS.value,
            reason="Customer provided documentation.",
        ),
        actor=tenant_admin_a,
    )
    assert ticket.status == SupportTicketStatus.IN_PROGRESS.value
    assert ticket.sla_paused_at is None
    assert ticket.sla_resolution_status == SupportSlaState.ON_TRACK.value
    assert ensure_utc(ticket.resolution_due_at) > ensure_utc(original_resolution_due)
    assert ticket.sla_total_paused_minutes >= 30


@pytest.mark.asyncio
async def test_customer_reply_auto_resumes_waiting_ticket(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User, faculty_user: User
):
    """Verify customer posting a public reply automatically moves ticket from WAITING_FOR_REQUESTER to IN_PROGRESS."""
    payload = SupportTicketCreateRequest(
        subject="Placement Cell Registration Link Broken",
        description="Students cannot upload resumes.",
        category=SupportCategory.PLACEMENTS.value,
        priority=SupportPriority.HIGH.value,
    )
    ticket = await SupportService.create_ticket(db_session, faculty_user, tenant_a.id, payload)
    # Move to WAITING_FOR_REQUESTER
    ticket.status = SupportTicketStatus.WAITING_FOR_REQUESTER.value
    ticket.sla_paused_at = datetime.now(UTC)
    await db_session.commit()

    # Requester replies with clarification
    msg = await SupportService.add_message(
        db=db_session,
        ticket_id=ticket.id,
        payload=SupportTicketMessageCreateRequest(
            message_type=SupportMessageType.PUBLIC_REPLY.value,
            body="I have attached the screenshot of the error modal.",
        ),
        actor=faculty_user,
    )
    await db_session.commit()

    # Refresh ticket
    await db_session.refresh(ticket)
    assert ticket.status == SupportTicketStatus.IN_PROGRESS.value
    assert ticket.sla_paused_at is None


# =============================================================================
# 5. ASSIGNMENT & TIER ESCALATION
# =============================================================================


@pytest.mark.asyncio
async def test_ticket_assignment_and_reassignment(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User, faculty_user: User
):
    """Verify manual assignment to an agent and support team."""
    payload = SupportTicketCreateRequest(
        subject="Hostel Room Allocation Inconsistency",
        description="Two students assigned to the same room in Hall 3.",
        category=SupportCategory.CAMPUS_OPERATIONS.value,
        priority=SupportPriority.MEDIUM.value,
    )
    ticket = await SupportService.create_ticket(db_session, faculty_user, tenant_a.id, payload)
    await db_session.commit()

    teams = await SupportService.get_or_seed_default_teams(db_session, tenant_a.id)
    target_team = teams[0]

    # Assign to team and agent
    ticket = await SupportService.assign_ticket(
        db=db_session,
        ticket_id=ticket.id,
        payload=SupportTicketAssignRequest(
            assigned_team_id=target_team.id,
            assigned_agent_id=tenant_admin_a.id,
            assignment_notes="Assigned to lead facilities coordinator.",
        ),
        actor=tenant_admin_a,
    )
    assert ticket.assigned_agent_id == tenant_admin_a.id
    assert ticket.assigned_agent_email == tenant_admin_a.email
    assert ticket.assigned_team_id == target_team.id


@pytest.mark.asyncio
async def test_ticket_escalation_workflow(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verify tier escalation with audit reason."""
    payload = SupportTicketCreateRequest(
        subject="Payment Reconciliation Gateway Mismatch",
        description="Daily bank settlement variance of INR 2,40,000.",
        category=SupportCategory.FINANCE_FEES.value,
        priority=SupportPriority.HIGH.value,
    )
    ticket = await SupportService.create_ticket(db_session, tenant_admin_a, tenant_a.id, payload)
    # Move to IN_PROGRESS
    ticket.status = SupportTicketStatus.IN_PROGRESS.value
    await db_session.commit()

    # Escalate to higher tier
    ticket = await SupportService.escalate_ticket(
        db=db_session,
        ticket_id=ticket.id,
        payload=SupportTicketEscalateRequest(
            escalation_reason="Banking webhook signature mismatch requires SRE integration inspection.",
        ),
        actor=tenant_admin_a,
    )
    assert ticket.status == SupportTicketStatus.ESCALATED.value
    assert ticket.escalation_level >= 1
    assert ticket.escalation_reason is not None


# =============================================================================
# 6. COMMUNICATION & ZERO-TRUST INTERNAL NOTES SEGREGATION
# =============================================================================


@pytest.mark.asyncio
async def test_public_reply_vs_internal_note_segregation(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
    faculty_user: User,
):
    """Verify internal notes are strictly hidden from requesters and non-support cannot post notes."""
    payload = SupportTicketCreateRequest(
        subject="Course Prerequisite Override Issue",
        description="Student cannot enroll in Advanced ML despite completing prerequisites.",
        category=SupportCategory.ACADEMIC_CONFIG.value,
        priority=SupportPriority.MEDIUM.value,
    )
    ticket = await SupportService.create_ticket(db_session, faculty_user, tenant_a.id, payload)
    await db_session.commit()

    # 1. Support agent posts an INTERNAL NOTE
    note = await SupportService.add_message(
        db=db_session,
        ticket_id=ticket.id,
        payload=SupportTicketMessageCreateRequest(
            message_type=SupportMessageType.INTERNAL_NOTE.value,
            body="CONFIDENTIAL: Student transcript shows incomplete prerequisite CS-201 from Fall 2025.",
        ),
        actor=tenant_admin_a,
    )
    assert note.message_type == SupportMessageType.INTERNAL_NOTE.value

    # 2. Support agent posts a PUBLIC REPLY
    reply = await SupportService.add_message(
        db=db_session,
        ticket_id=ticket.id,
        payload=SupportTicketMessageCreateRequest(
            message_type=SupportMessageType.PUBLIC_REPLY.value,
            body="Hello Professor, we are reviewing the prerequisite records with the registrar.",
        ),
        actor=tenant_admin_a,
    )
    assert reply.message_type == SupportMessageType.PUBLIC_REPLY.value
    await db_session.commit()

    # 3. Requester (faculty_user) retrieves ticket -> internal note is STRIPPED
    ticket_as_requester = await SupportService.get_ticket(
        db=db_session,
        ticket_id=ticket.id,
        current_user=faculty_user,
        can_view_internal_notes=False,
    )
    message_bodies = [m.body for m in ticket_as_requester.messages]
    assert any("Hello Professor" in b for b in message_bodies)
    assert not any("CONFIDENTIAL" in b for b in message_bodies)

    # 4. Support agent retrieves ticket -> sees BOTH messages
    ticket_as_agent = await SupportService.get_ticket(
        db=db_session,
        ticket_id=ticket.id,
        current_user=tenant_admin_a,
        can_view_internal_notes=True,
    )
    agent_msg_bodies = [m.body for m in ticket_as_agent.messages]
    assert any("CONFIDENTIAL" in b for b in agent_msg_bodies)
    assert any("Hello Professor" in b for b in agent_msg_bodies)

    # 5. Requester attempts to post an INTERNAL NOTE -> DENIED
    with pytest.raises(PermissionDeniedException):
        await SupportService.add_message(
            db=db_session,
            ticket_id=ticket.id,
            payload=SupportTicketMessageCreateRequest(
                message_type=SupportMessageType.INTERNAL_NOTE.value,
                body="Attempting unauthorized internal note posting.",
            ),
            actor=faculty_user,
        )


# =============================================================================
# 7. RESOLUTION, CSAT & REOPENING
# =============================================================================


@pytest.mark.asyncio
async def test_resolution_and_csat_workflow(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
    faculty_user: User,
):
    """Verify resolution, CSAT submission, and reopening workflow."""
    payload = SupportTicketCreateRequest(
        subject="Library Fine Waiver Request",
        description="Book returned during campus closure; fine mistakenly accrued.",
        category=SupportCategory.DOCUMENTS_RECORDS.value,
        priority=SupportPriority.LOW.value,
    )
    ticket = await SupportService.create_ticket(db_session, faculty_user, tenant_a.id, payload)
    # Move to IN_PROGRESS
    ticket.status = SupportTicketStatus.IN_PROGRESS.value
    await db_session.commit()

    # CSAT on open ticket is rejected
    with pytest.raises(ValidationException):
        await SupportService.submit_csat(
            db=db_session,
            ticket_id=ticket.id,
            payload=SupportTicketCsatRequest(rating=5, feedback="Premature rating"),
            actor=faculty_user,
        )

    # Resolve ticket
    ticket = await SupportService.resolve_ticket(
        db=db_session,
        ticket_id=ticket.id,
        payload=SupportTicketResolveRequest(
            resolution_summary="Late fee waived per campus closure policy.",
        ),
        actor=tenant_admin_a,
    )
    assert ticket.status == SupportTicketStatus.RESOLVED.value

    # Submit valid CSAT rating
    ticket = await SupportService.submit_csat(
        db=db_session,
        ticket_id=ticket.id,
        payload=SupportTicketCsatRequest(
            rating=5,
            feedback="Prompt resolution and excellent support by the bursar desk!",
        ),
        actor=faculty_user,
    )
    assert ticket.csat_rating == 5
    assert ticket.csat_feedback is not None
    assert ticket.csat_submitted_at is not None

    # Reopening ticket requires reason (enforced by Pydantic min_length=5)
    # Reopen ticket with reason succeeds
    ticket = await SupportService.reopen_ticket(
        db=db_session,
        ticket_id=ticket.id,
        payload=SupportTicketReopenRequest(
            reopen_reason="Fee deduction still visible in student billing portal.",
        ),
        actor=faculty_user,
    )
    assert ticket.status == SupportTicketStatus.REOPENED.value
    assert ticket.reopen_count == 1
    assert ticket.resolved_at is None


# =============================================================================
# 8. INCIDENT & ARTICLE CORRELATION
# =============================================================================


@pytest.mark.asyncio
async def test_incident_and_article_linking(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    """Verify linking support ticket to an operational incident and knowledge base article."""
    payload = SupportTicketCreateRequest(
        subject="Cloud Storage S3 Upload Failures",
        description="Students unable to upload project PDF files.",
        category=SupportCategory.DOCUMENTS_RECORDS.value,
        priority=SupportPriority.HIGH.value,
    )
    ticket = await SupportService.create_ticket(db_session, tenant_admin_a, tenant_a.id, payload)
    await db_session.commit()

    # Link incident
    ticket = await SupportService.link_incident(
        db=db_session,
        ticket_id=ticket.id,
        payload=SupportTicketIncidentLinkRequest(
            related_incident_id="INC-2026-S3-DEGRADATION",
        ),
        actor=tenant_admin_a,
    )
    assert ticket.related_incident_id == "INC-2026-S3-DEGRADATION"

    # Link knowledge base article
    link = await SupportService.link_article(
        db=db_session,
        ticket_id=ticket.id,
        payload=SupportTicketArticleLinkRequest(
            article_id="ART-101",
            article_title="Fixing S3 Presigned URL Upload Failures",
            article_url="https://kb.campusos.internal/articles/s3-presigned-urls",
            relevance_score=0.95,
        ),
        actor=tenant_admin_a,
    )
    assert link.article_title == "Fixing S3 Presigned URL Upload Failures"
    assert link.relevance_score == 0.95


# =============================================================================
# 9. MULTI-TENANT ISOLATION
# =============================================================================


@pytest.mark.asyncio
async def test_multi_tenant_isolation_enforcement(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_b: Institution,
    tenant_admin_a: User,
    tenant_admin_b: User,
    faculty_user: User,
    user_b: User,
):
    """Verify strict tenant boundaries: Tenant B users cannot view or manipulate Tenant A tickets."""
    payload = SupportTicketCreateRequest(
        subject="Confidential Tenant A Academic Audit Issue",
        description="Internal accreditation review logs.",
        category=SupportCategory.REPORTS_ANALYTICS.value,
        priority=SupportPriority.MEDIUM.value,
    )
    ticket_a = await SupportService.create_ticket(db_session, faculty_user, tenant_a.id, payload)
    await db_session.commit()

    # Tenant B Admin attempts to read Tenant A ticket -> DENIED
    with pytest.raises(PermissionDeniedException):
        await SupportService.get_ticket(
            db=db_session,
            ticket_id=ticket_a.id,
            current_user=tenant_admin_b,
            can_view_internal_notes=True,
        )

    # Tenant B regular user attempts to read Tenant A ticket -> DENIED
    with pytest.raises(PermissionDeniedException):
        await SupportService.get_ticket(
            db=db_session,
            ticket_id=ticket_a.id,
            current_user=user_b,
            can_view_internal_notes=False,
        )

    # Tenant B Admin attempts to transition Tenant A ticket -> DENIED
    with pytest.raises(PermissionDeniedException):
        await SupportService.transition_status(
            db=db_session,
            ticket_id=ticket_a.id,
            payload=SupportTicketTransitionRequest(
                target_status=SupportTicketStatus.IN_PROGRESS.value,
                reason="Unauthorized cross-tenant transition",
            ),
            actor=tenant_admin_b,
        )


# =============================================================================
# 10. REST API INTEGRATION
# =============================================================================


@pytest.mark.asyncio
async def test_api_ticket_full_lifecycle(
    client: AsyncClient,
    super_admin_user: User,
    tenant_a: Institution,
    faculty_user: User,
    db_session: AsyncSession,
):
    """Verify end-to-end support ticket operations via FastAPI REST endpoints."""
    faculty_headers = make_auth_headers(faculty_user, tenant_a.id, "FACULTY", ["faculty:read", "faculty:write"])
    admin_headers = make_auth_headers(super_admin_user, tenant_a.id, "SUPER_ADMIN", ["*"])

    # 1. Create ticket via API
    resp = await client.post(
        "/api/v1/support/tickets",
        headers=faculty_headers,
        json={
            "subject": "REST API Test: Grade Submission Glitch",
            "description": "Faculty unable to finalize marks for semester exams.",
            "category": "EXAMINATIONS",
            "request_type": "INCIDENT",
            "priority": "HIGH",
            "related_erp_module": "EXAMINATIONS",
        },
    )
    assert resp.status_code == 201, resp.text
    ticket_data = resp.json()
    ticket_id = ticket_data["id"]
    assert ticket_data["status"] == "NEW"
    assert ticket_data["ticket_number"].startswith("TICK-")

    # 2. List tickets
    list_resp = await client.get("/api/v1/support/tickets", headers=faculty_headers)
    assert list_resp.status_code == 200
    assert any(t["id"] == ticket_id for t in list_resp.json()["items"])

    # 3. Transition ticket to IN_PROGRESS via Admin
    trans_resp = await client.post(
        f"/api/v1/support/tickets/{ticket_id}/transition",
        headers=admin_headers,
        json={"target_status": "IN_PROGRESS", "reason": "Investigation initiated by SRE desk."},
    )
    assert trans_resp.status_code == 200
    assert trans_resp.json()["status"] == "IN_PROGRESS"

    # 4. Support Admin posts internal note
    note_resp = await client.post(
        f"/api/v1/support/tickets/{ticket_id}/messages",
        headers=admin_headers,
        json={
            "message_type": "INTERNAL_NOTE",
            "body": "Backend database lock detected on exams table. Running deadlock clear.",
        },
    )
    assert note_resp.status_code == 201

    # 5. Support Admin posts public reply
    reply_resp = await client.post(
        f"/api/v1/support/tickets/{ticket_id}/messages",
        headers=admin_headers,
        json={
            "message_type": "PUBLIC_REPLY",
            "body": "The grade submission database lock has been resolved. Please retry.",
        },
    )
    assert reply_resp.status_code == 201

    # 6. Faculty fetches ticket: internal note MUST NOT be visible!
    detail_resp = await client.get(f"/api/v1/support/tickets/{ticket_id}", headers=faculty_headers)
    assert detail_resp.status_code == 200
    messages = detail_resp.json()["messages"]
    assert len(messages) == 1
    assert "resolved. Please retry" in messages[0]["body"]
    assert not any("Backend database lock" in m["body"] for m in messages)

    # 7. Resolve ticket
    res_resp = await client.post(
        f"/api/v1/support/tickets/{ticket_id}/resolve",
        headers=admin_headers,
        json={
            "resolution_summary": "Deadlock cleared and marks updated successfully.",
        },
    )
    assert res_resp.status_code == 200
    assert res_resp.json()["status"] == "RESOLVED"

    # 8. Submit CSAT rating via faculty
    csat_resp = await client.post(
        f"/api/v1/support/tickets/{ticket_id}/csat",
        headers=faculty_headers,
        json={
            "rating": 5,
            "feedback": "Super quick response, thank you team!",
        },
    )
    assert csat_resp.status_code == 200
    assert csat_resp.json()["csat_rating"] == 5

    # 9. Fetch Analytics
    analytics_resp = await client.get("/api/v1/support/analytics", headers=admin_headers)
    assert analytics_resp.status_code == 200
    metrics = analytics_resp.json()
    assert metrics["total_tickets"] >= 1
    assert metrics["resolved_tickets"] >= 1
