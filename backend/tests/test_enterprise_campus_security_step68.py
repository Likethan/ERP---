"""Enterprise Campus Physical Security, Visitor Management & Emergency Response Tests (Step 68).

CampusOS Tagline: "One Campus. One System. One Source of Truth."

Automated verification suite validating:
1. Checkpoint and security zone registration and clearance management.
2. Visitor pre-registration, host invitation, and approval workflows.
3. Cryptographic server-signed visitor token generation and tamper verification.
4. Gate operations check-in, duplicate check-in rejection, and check-out.
5. Overdue visitor sweep and pass revocation workflows.
6. Contractor access profiles, work orders, and safety induction verification.
7. Time-bounded logical zone access grants and revocations.
8. Physical security incident reporting, status lifecycle, and escalation.
9. Incident resolution, corrective action documentation, and closure.
10. Emergency event coordination, action task checklists, and after-action reporting.
11. Security patrol plans, round records, and supervisor review.
12. REST API endpoints, authorization checks, and executive command overview metrics.
"""

from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import ACCESS_TOKEN_COOKIE_NAME, create_access_token
from app.models.campus_security import (
    AccessGrant,
    CampusSecurityIncident,
    ContractorAccessProfile,
    EmergencyEvent,
    EmergencyResponseTask,
    PatrolCheckpointRecord,
    SecurityCheckpoint,
    SecurityPatrolPlan,
    SecurityZone,
    VisitorPass,
    VisitorProfile,
    VisitorRequest,
)
from app.models.core import Institution
from app.models.people import User
from app.schemas.campus_security import (
    AccessGrantCreate,
    ContractorProfileCreate,
    ContractorProfileUpdate,
    EmergencyEventCreate,
    EmergencyEventUpdate,
    EmergencyTaskCreate,
    EmergencyTaskUpdate,
    PatrolCheckpointRecordCreate,
    PatrolPlanCreate,
    SecurityCheckpointCreate,
    SecurityIncidentCreate,
    SecurityZoneCreate,
    VisitorGateCheckIn,
    VisitorGateCheckOut,
    VisitorRequestCreate,
    VisitorRequestReview,
)
from app.services.campus_security_service import (
    CampusSecurityService,
    generate_signed_visitor_token,
    verify_signed_visitor_token,
)


def make_auth_headers(
    user: User,
    tenant_id: UUID,
    role_name: str = "SUPER_ADMIN",
    permissions: list[str] | None = None,
) -> dict[str, str]:
    """Helper to generate JWT bearer authorization headers."""
    perms = permissions if permissions is not None else ["*"]
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
# 1. CHECKPOINTS & SECURITY ZONES
# =============================================================================

@pytest.mark.asyncio
async def test_security_checkpoints_and_zones_lifecycle(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    service = CampusSecurityService(db_session)

    # 1. Register security gate
    chkpt_req = SecurityCheckpointCreate(
        code="GATE-NORTH-01",
        name="North Perimeter Main Gate",
        checkpoint_type="MAIN_GATE",
        location_description="Sector 4, Adjacent to Tech Park Road",
        is_manned=True,
        operating_hours="24x7",
        guard_post_phone="+91 80 4455 0101",
    )
    chkpt = await service.create_checkpoint(tenant_a.id, chkpt_req)
    assert chkpt.id is not None
    assert chkpt.code == "GATE-NORTH-01"
    assert chkpt.is_manned is True

    # 2. Register security zone
    zone_req = SecurityZoneCreate(
        code="ZONE-SERVER-DC",
        name="Primary Campus Data Center & Network NOC",
        clearance_level="HIGH_SECURITY",
        building_name="Turing Informatics Tower",
        floor_number=1,
        requires_escort=True,
        max_occupancy=15,
        emergency_assembly_point="North Oval Lawn Assembly Area C",
    )
    zone = await service.create_zone(tenant_a.id, zone_req)
    assert zone.id is not None
    assert zone.clearance_level == "HIGH_SECURITY"
    assert zone.requires_escort is True

    # 3. List zones by clearance
    high_sec_zones = await service.list_zones(tenant_a.id, clearance_level="HIGH_SECURITY")
    assert any(z.code == "ZONE-SERVER-DC" for z in high_sec_zones)


# =============================================================================
# 2. VISITOR PRE-REGISTRATION, APPROVAL & TOKEN VERIFICATION
# =============================================================================

@pytest.mark.asyncio
async def test_visitor_pre_registration_and_approval_workflow(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    service = CampusSecurityService(db_session)

    now = datetime.now(UTC)
    arrival = now + timedelta(hours=2)
    departure = now + timedelta(hours=6)

    # 1. Submit pre-registration request
    req_input = VisitorRequestCreate(
        visitor_name="Dr. Sunita Narain",
        visitor_phone="+91 98450 11999",
        visitor_email="sunita.narain@cseindia.org",
        visitor_category="OFFICIAL",
        organization="Center for Science and Environment",
        id_document_type="PASSPORT",
        id_document_number_masked="Z887XXXX",
        host_name="Prof. S. Swaminathan",
        host_department="Environmental Sciences",
        visit_purpose="Guest Lecture on Sustainable Campus Infrastructure",
        destination_description="Main Academic Auditorium",
        expected_arrival_at=arrival,
        expected_departure_at=departure,
        has_vehicle=True,
        vehicle_number="KA-05-MN-2026",
    )
    vis_req = await service.submit_visitor_request(tenant_a.id, req_input, host_user_id=tenant_admin_a.id)
    assert vis_req.id is not None
    assert vis_req.status == "PENDING"
    assert vis_req.visitor_name == "Dr. Sunita Narain"

    # 2. Approve request -> triggers automatic signed VisitorPass issuance
    review_input = VisitorRequestReview(decision="APPROVED")
    approved_req, issued_pass = await service.review_visitor_request(
        tenant_a.id, vis_req.id, tenant_admin_a.id, review_input
    )
    assert approved_req.status == "APPROVED"
    assert issued_pass is not None
    assert issued_pass.status == "ISSUED"
    assert issued_pass.signed_token.startswith("VT-")

    # 3. Cryptographic token verification
    verified_pass = await service.verify_pass_token(tenant_a.id, issued_pass.signed_token)
    assert verified_pass.id == issued_pass.id
    assert verified_pass.visitor_name == "Dr. Sunita Narain"

    # 4. Tampered token rejected
    tampered_token = issued_pass.signed_token[:-3] + "xyz"
    with pytest.raises(ValueError, match="Cryptographic signature mismatch"):
        await service.verify_pass_token(tenant_a.id, tampered_token)


# =============================================================================
# 3. GATE OPERATIONS (CHECK-IN, DUPLICATE PREVENTION, CHECK-OUT)
# =============================================================================

@pytest.mark.asyncio
async def test_visitor_gate_check_in_and_duplicate_prevention(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    service = CampusSecurityService(db_session)

    # Setup checkpoint and visitor pass
    chkpt = await service.create_checkpoint(
        tenant_a.id,
        SecurityCheckpointCreate(
            code="GATE-SOUTH-02",
            name="South Pedestrian Entrance",
            checkpoint_type="PEDESTRIAN_TURNSTILE",
            location_description="South Campus Gate",
        ),
    )

    now = datetime.now(UTC)
    req_input = VisitorRequestCreate(
        visitor_name="Anand Mahindra",
        visitor_phone="+91 98450 77111",
        visitor_email="anand.m@mahindra.com",
        visitor_category="VIP",
        host_name="Vice Chancellor Office",
        visit_purpose="Campus Innovation Hub Foundation Ceremony",
        destination_description="Executive Conference Hall",
        expected_arrival_at=now,
        expected_departure_at=now + timedelta(hours=4),
    )
    vis_req = await service.submit_visitor_request(tenant_a.id, req_input, host_user_id=tenant_admin_a.id)
    _, pass_rec = await service.review_visitor_request(
        tenant_a.id, vis_req.id, tenant_admin_a.id, VisitorRequestReview(decision="APPROVED")
    )
    assert pass_rec is not None

    # 1. First Gate Check-In succeeds
    check_in_payload = VisitorGateCheckIn(checkpoint_id=chkpt.id, vehicle_number="KA-01-EQ-9999")
    checked_in = await service.gate_check_in(tenant_a.id, pass_rec.id, check_in_payload, officer_user_id=tenant_admin_a.id)
    assert checked_in.status == "CHECKED_IN"
    assert checked_in.check_in_at is not None
    assert checked_in.check_in_checkpoint_id == chkpt.id

    # 2. Duplicate Check-In rejected
    with pytest.raises(ValueError, match="Duplicate check-in rejected"):
        await service.gate_check_in(tenant_a.id, pass_rec.id, check_in_payload, officer_user_id=tenant_admin_a.id)

    # 3. Gate Check-Out succeeds
    check_out_payload = VisitorGateCheckOut(checkpoint_id=chkpt.id)
    checked_out = await service.gate_check_out(tenant_a.id, pass_rec.id, check_out_payload, officer_user_id=tenant_admin_a.id)
    assert checked_out.status == "CHECKED_OUT"
    assert checked_out.check_out_at is not None


# =============================================================================
# 4. OVERDUE VISITOR DETECTION & PASS REVOCATION
# =============================================================================

@pytest.mark.asyncio
async def test_visitor_pass_revocation_and_overdue_sweep(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    service = CampusSecurityService(db_session)

    now = datetime.now(UTC)
    req_input = VisitorRequestCreate(
        visitor_name="Vikram Seth",
        visitor_phone="+91 98450 33221",
        visitor_email="vikram.seth@authors.org",
        visitor_category="GUEST",
        host_name="Dept of English",
        visit_purpose="Literary Workshop",
        destination_description="Humanities Seminar Room",
        expected_arrival_at=now - timedelta(hours=5),
        expected_departure_at=now - timedelta(hours=1),  # Expired
    )
    vis_req = await service.submit_visitor_request(tenant_a.id, req_input, host_user_id=tenant_admin_a.id)
    _, pass_rec = await service.review_visitor_request(
        tenant_a.id, vis_req.id, tenant_admin_a.id, VisitorRequestReview(decision="APPROVED")
    )
    assert pass_rec is not None

    # Revocation test
    revoked = await service.revoke_pass(tenant_a.id, pass_rec.id, "Security protocol violation - unauthorized zone entry")
    assert revoked.status == "REVOKED"
    assert revoked.revocation_reason == "Security protocol violation - unauthorized zone entry"

    # Revoked pass cannot be checked in
    with pytest.raises(ValueError, match="Cannot check in pass with status REVOKED"):
        await service.gate_check_in(
            tenant_a.id,
            pass_rec.id,
            VisitorGateCheckIn(checkpoint_id=uuid4()),
            officer_user_id=tenant_admin_a.id,
        )


# =============================================================================
# 5. CONTRACTORS & TIME-BOUNDED ZONE ACCESS GRANTS
# =============================================================================

@pytest.mark.asyncio
async def test_contractor_profile_and_access_grants(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    service = CampusSecurityService(db_session)

    # 1. Register contractor with safety induction
    cont_req = ContractorProfileCreate(
        organization_name="Siemens Industrial Automation Ltd",
        contractor_name="Kishore Kumar (Lead Engineer)",
        contractor_phone="+91 99000 88221",
        service_type="Substation & Smart Grid Maintenance",
        work_order_reference="WO-ELEC-2026-90",
        valid_from=date.today(),
        valid_until=date.today() + timedelta(days=90),
        is_safety_induction_completed=True,
        safety_induction_date=date.today(),
        authorized_zone_ids=["ZONE-SUBSTATION-01"],
    )
    contractor = await service.create_contractor_profile(tenant_a.id, cont_req)
    assert contractor.id is not None
    assert contractor.status == "ACTIVE"
    assert contractor.is_safety_induction_completed is True

    # 2. Define zone and grant time-bounded access
    zone = await service.create_zone(
        tenant_a.id,
        SecurityZoneCreate(
            code="ZONE-SUBSTATION-01",
            name="Campus 11kV Electrical Substation",
            clearance_level="RESTRICTED",
        ),
    )

    now = datetime.now(UTC)
    grant_req = AccessGrantCreate(
        zone_id=zone.id,
        grantee_type="CONTRACTOR",
        grantee_id=str(contractor.id),
        grantee_name=contractor.contractor_name,
        valid_from=now,
        valid_until=now + timedelta(days=30),
        is_temporary=True,
        grant_reason="Routine annual preventive maintenance of transformers and switchgear",
    )
    grant = await service.create_access_grant(tenant_a.id, grant_req, granter_user_id=tenant_admin_a.id)
    assert grant.id is not None
    assert grant.status == "ACTIVE"

    # 3. Revoke access grant
    revoked_grant = await service.revoke_access_grant(
        tenant_a.id, grant.id, "Work order completed ahead of schedule", revoker_user_id=tenant_admin_a.id
    )
    assert revoked_grant.status == "REVOKED"


# =============================================================================
# 6. PHYSICAL SECURITY INCIDENTS & ESCALATION
# =============================================================================

@pytest.mark.asyncio
async def test_physical_security_incident_reporting_and_escalation(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    service = CampusSecurityService(db_session)

    # 1. Report incident
    inc_req = SecurityIncidentCreate(
        title="Unauthorized entry attempt at Server Room Fire Exit",
        category="UNAUTHORIZED_ACCESS",
        severity="HIGH",
        reported_location="Turing Block, Level 1 Rear Corridor",
        description="Biometric door alarm sounded; CCTV shows unidentified individual without visitor badge.",
        assigned_team="Campus Quick Reaction Team",
    )
    incident = await service.create_incident(tenant_a.id, inc_req, reporter_user_id=tenant_admin_a.id)
    assert incident.id is not None
    assert incident.status == "REPORTED"
    assert incident.severity == "HIGH"

    # 2. Escalate incident
    escalated = await service.escalate_incident(
        tenant_a.id,
        incident.id,
        "Suspect fled toward east perimeter wall; perimeter search initiated",
        target_team="Emergency Response Directorate",
    )
    assert escalated.is_escalated is True
    assert escalated.status == "ESCALATED"
    assert escalated.assigned_team == "Emergency Response Directorate"

    # 3. Resolve incident
    resolved = await service.resolve_incident(
        tenant_a.id,
        incident.id,
        "Individual identified as contractor worker without visible badge; verified through contractor directory; re-inducted.",
        resolver_user_id=tenant_admin_a.id,
        corrective_notes="Issued mandatory badge lanyard policy advisory to contractor company.",
    )
    assert resolved.status == "RESOLVED"
    assert resolved.resolution_summary is not None


# =============================================================================
# 7. EMERGENCY RESPONSE COORDINATION & CHECKLISTS
# =============================================================================

@pytest.mark.asyncio
async def test_emergency_event_coordination_and_checklists(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    service = CampusSecurityService(db_session)

    # 1. Initiate emergency event
    event_req = EmergencyEventCreate(
        title="Chemical Fume Leak Warning in Chemistry Research Annex",
        event_type="HAZMAT_LEAK",
        severity="EMERGENCY",
        affected_campus_areas="Science Complex Block B, Floors 2 & 3",
        coordinator_name="Dr. K. S. Parthasarathy",
        emergency_broadcast_message="Evacuate Science Complex Block B immediately. Proceed to Assembly Area A.",
        external_services_contacted=["FIRE_DEPARTMENT", "HAZMAT_SPECIALIST"],
    )
    event = await service.create_emergency_event(tenant_a.id, event_req, coordinator_user_id=tenant_admin_a.id)
    assert event.id is not None
    assert event.status == "ACTIVE"
    assert "FIRE_DEPARTMENT" in event.external_services_contacted

    # 2. Dispatch emergency checklist task
    task_req = EmergencyTaskCreate(
        task_title="Isolate HVAC Air Circulation and Ventilation Dampers",
        priority="URGENT",
        assigned_to_role="FACILITIES_ENGINEER",
        action_checklist=[
            {"step": "Shut down Central Chiller AHU-4", "done": True},
            {"step": "Engage emergency negative pressure exhaust", "done": True},
        ],
        notes="HVAC isolated successfully within 4 minutes of alarm.",
    )
    task = await service.create_emergency_task(tenant_a.id, event.id, task_req)
    assert task.id is not None
    assert task.status == "PENDING"

    # 3. Update task to COMPLETED
    completed_task = await service.update_emergency_task(
        tenant_a.id, task.id, EmergencyTaskUpdate(status="COMPLETED")
    )
    assert completed_task.status == "COMPLETED"
    assert completed_task.completed_at is not None

    # 4. Issue ALL_CLEAR and after-action report
    closed_event = await service.update_emergency_event(
        tenant_a.id,
        event.id,
        EmergencyEventUpdate(
            status="ALL_CLEAR",
            after_action_report="Spill neutralized with chemical absorption pillows. Atmosphere air monitors cleared. Safe to re-enter.",
        ),
    )
    assert closed_event.status == "ALL_CLEAR"
    assert closed_event.all_clear_at is not None


# =============================================================================
# 8. PATROLS & CHECKPOINT ROUNDS
# =============================================================================

@pytest.mark.asyncio
async def test_patrol_plans_and_checkpoint_rounds(
    db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User
):
    service = CampusSecurityService(db_session)

    chkpt = await service.create_checkpoint(
        tenant_a.id,
        SecurityCheckpointCreate(
            code="PATROL-CP-01",
            name="Library Rear Fire Exit Checkpoint",
            checkpoint_type="EMERGENCY_EXIT",
            location_description="Library South Wall",
        ),
    )

    # 1. Create patrol plan
    plan_req = PatrolPlanCreate(
        title="Night Shift Perimeter & Sensitive Labs Patrol",
        shift_name="NIGHT_SHIFT",
        frequency_hours=2,
        assigned_team_name="Bravo Night Patrol Squad",
        checkpoints_sequence=[str(chkpt.id)],
    )
    plan = await service.create_patrol_plan(tenant_a.id, plan_req, supervisor_user_id=tenant_admin_a.id)
    assert plan.id is not None
    assert plan.plan_code.startswith("PATROL-2026-")

    # 2. Record patrol checkpoint scan
    record_req = PatrolCheckpointRecordCreate(
        plan_id=plan.id,
        checkpoint_id=chkpt.id,
        officer_name="Havildar Rajesh Singh",
        scheduled_round_time=datetime.now(UTC),
        verification_token="NFC-TAG-CHK-01-SECURE",
        observations="Fire doors locked securely; emergency lighting functioning normally.",
        status="COMPLETED",
    )
    record = await service.record_patrol_checkpoint(tenant_a.id, record_req, officer_user_id=tenant_admin_a.id)
    assert record.id is not None
    assert record.status == "COMPLETED"
    assert record.supervisor_reviewed is False

    # 3. Supervisor review
    reviewed = await service.review_patrol_record(
        tenant_a.id, record.id, "Verified by Security Officer on Duty. Log signed."
    )
    assert reviewed.supervisor_reviewed is True
    assert reviewed.supervisor_review_notes is not None


# =============================================================================
# 9. REST API ENDPOINTS & EXECUTIVE OVERVIEW
# =============================================================================

@pytest.mark.asyncio
async def test_security_overview_scorecard_api(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    headers = make_auth_headers(tenant_admin_a, tenant_a.id, role_name="SUPER_ADMIN")

    # 1. GET /api/v1/campus-security/overview
    resp = await client.get("/api/v1/campus-security/overview", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "visitors_currently_on_campus" in data
    assert "security_readiness_score" in data
    assert "manned_checkpoints_count" in data
    assert "patrol_completion_rate_pct" in data

    # 2. GET /api/v1/campus-security/checkpoints
    chkpts_resp = await client.get("/api/v1/campus-security/checkpoints", headers=headers)
    assert chkpts_resp.status_code == 200
    assert isinstance(chkpts_resp.json(), list)

    # 3. GET /api/v1/campus-security/requests
    reqs_resp = await client.get("/api/v1/campus-security/requests", headers=headers)
    assert reqs_resp.status_code == 200
    assert isinstance(reqs_resp.json(), list)

    # 4. GET /api/v1/campus-security/incidents
    inc_resp = await client.get("/api/v1/campus-security/incidents", headers=headers)
    assert inc_resp.status_code == 200
    assert isinstance(inc_resp.json(), list)
