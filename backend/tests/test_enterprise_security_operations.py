"""Comprehensive Automated Test Suite for Enterprise Security Operations, Threat Detection & Incident Response (Step 33).

Product Principle: "Detect early. Investigate safely. Respond deliberately. Preserve evidence."

Validates all 18 core Step 33 requirements:
1. Threat detection rule registry integrity and explainable deterministic heuristics.
2. Event normalization and threshold evaluation (below vs at threshold).
3. Deduplication and alert storm suppression on recurring detection fingerprints.
4. Cross-tenant boundary access attempt detection (RULE-TENANT-001).
5. Distributed credential stuffing detection across multiple accounts (RULE-AUTH-002).
6. Suspicious administrative privilege escalation detection (RULE-PRIV-001).
7. Permission denial spike detection (RULE-AUTHZ-001).
8. Valid incident lifecycle state machine transitions (NEW -> TRIAGED -> INVESTIGATING -> ... -> CLOSED).
9. Invalid lifecycle transitions rejected with ValidationException.
10. Incident reopening workflow (CLOSED -> REOPENED -> INVESTIGATING).
11. Responder assignment and append-only investigation timeline notes.
12. Post-incident remediation task creation and status tracking.
13. Response action approval requirement on high-risk containment actions.
14. Response action execution, idempotency, and audit trail generation.
15. Response action safe rollback procedure.
16. Strict tenant isolation on incident queries and details access.
17. Platform operator authorized cross-tenant visibility.
18. Security Operations Center (SOC) real-time overview metrics and rule tuning.
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ValidationException
from app.core.permissions import (
    DEFAULT_ROLE_PERMISSIONS,
)
from app.core.security import ACCESS_TOKEN_COOKIE_NAME, create_access_token
from app.core.threat_detection import (
    STANDARD_RULES,
    NormalizedSecurityEvent,
    threat_engine,
)
from app.models.audit import AuditLog
from app.models.core import Institution
from app.models.people import User
from app.models.security_ops import (
    SecurityIncident,
    SecurityResponseAction,
)
from app.services.security_ops_service import SecurityOpsService
from app.services.security_response_service import (
    BLOCKED_IPS_REGISTRY,
    SecurityResponseService,
)


def make_auth_headers(
    user: User,
    tenant_id: uuid.UUID | None,
    role_name: str = "INSTITUTION_ADMIN",
    custom_permissions: list[str] | None = None,
) -> dict[str, str]:
    """Generate authorization headers & cookies for authenticated API requests."""
    perms = (
        custom_permissions
        if custom_permissions is not None
        else DEFAULT_ROLE_PERMISSIONS.get(role_name, [])
    )
    token = create_access_token(
        user_id=user.id,
        tenant_id=tenant_id or user.primary_tenant_id,
        email=user.email,
        roles=[role_name],
        permissions=perms,
    )
    return {
        "Authorization": f"Bearer {token}",
        "Cookie": f"{ACCESS_TOKEN_COOKIE_NAME}={token}",
    }


# =============================================================================
# 1. THREAT DETECTION ENGINE & RULES (Tests 1-7)
# =============================================================================


@pytest.mark.asyncio
async def test_threat_detection_rules_integrity():
    """Test 1: Verify all standard deterministic detection rules are registered with valid schemas."""
    expected_rules = [
        "RULE-AUTH-001",
        "RULE-AUTH-002",
        "RULE-TENANT-001",
        "RULE-AUTHZ-001",
        "RULE-PRIV-001",
        "RULE-API-001",
        "RULE-DATA-001",
        "RULE-INTEG-001",
        "RULE-DOC-001",
    ]
    for r_id in expected_rules:
        assert r_id in STANDARD_RULES, f"Missing required rule {r_id}"
        rule = STANDARD_RULES[r_id]
        assert rule.rule_id == r_id
        assert rule.threshold >= 1
        assert rule.evaluation_window_seconds >= 60
        assert rule.severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW")


@pytest.mark.asyncio
async def test_event_normalization_and_threshold_boundaries(
    db_session: AsyncSession,
    tenant_a: Institution,
):
    """Test 2: Verify events below threshold do not trigger alerts; reaching threshold triggers detection."""
    threat_engine.clear()
    ip = "192.168.1.50"
    target_email = "student@apextech.edu"

    # Send 4 login failures (threshold is 5 for RULE-AUTH-001)
    for _ in range(4):
        event = NormalizedSecurityEvent(
            event_type="AUTH_LOGIN_FAILED",
            detection_source="AUTH_GATEWAY",
            tenant_id=tenant_a.id,
            ip_address=ip,
            details={"email": target_email},
        )
        det = await threat_engine.process_event(db_session, event)
        assert det is None, "Detection should not trigger before threshold"

    # Send 5th login failure -> threshold reached
    event5 = NormalizedSecurityEvent(
        event_type="AUTH_LOGIN_FAILED",
        detection_source="AUTH_GATEWAY",
        tenant_id=tenant_a.id,
        ip_address=ip,
        details={"email": target_email},
    )
    det5 = await threat_engine.process_event(db_session, event5)
    assert det5 is not None, "Detection must trigger upon reaching threshold"
    assert det5.rule_id == "RULE-AUTH-001"
    assert det5.severity == "HIGH"
    assert det5.incident_id is not None, "High severity detection must create/link incident"

    # Verify incident created
    inc_stmt = select(SecurityIncident).where(SecurityIncident.id == det5.incident_id)
    incident = (await db_session.execute(inc_stmt)).scalar_one()
    assert incident.incident_number.startswith("SEC-")
    assert incident.status == "NEW"


@pytest.mark.asyncio
async def test_detection_deduplication_storm_prevention(
    db_session: AsyncSession,
    tenant_a: Institution,
):
    """Test 3: Repeated events with same fingerprint increment occurrence count rather than spamming incidents."""
    threat_engine.clear()
    ip = "10.0.0.99"

    # Trigger initial detection
    for _ in range(5):
        event = NormalizedSecurityEvent(
            event_type="AUTH_LOGIN_FAILED",
            detection_source="AUTH_GATEWAY",
            tenant_id=tenant_a.id,
            ip_address=ip,
            details={"email": "victim@apextech.edu"},
        )
        det = await threat_engine.process_event(db_session, event)

    assert det is not None
    original_detection_id = det.id
    original_incident_id = det.incident_id

    # Emit 5 more failures with identical fingerprint
    for _ in range(5):
        event = NormalizedSecurityEvent(
            event_type="AUTH_LOGIN_FAILED",
            detection_source="AUTH_GATEWAY",
            tenant_id=tenant_a.id,
            ip_address=ip,
            details={"email": "victim@apextech.edu"},
        )
        updated_det = await threat_engine.process_event(db_session, event)

    assert updated_det.id == original_detection_id
    assert updated_det.incident_id == original_incident_id
    assert updated_det.occurrence_count >= 6, "Occurrence count should increment without creating new detections"


@pytest.mark.asyncio
async def test_cross_tenant_detection_triggers_critical_incident(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_b: Institution,
):
    """Test 4: Cross-tenant boundary attempt triggers critical incident with proposed session revocation."""
    threat_engine.clear()
    actor_user_id = str(uuid.uuid4())

    event = NormalizedSecurityEvent(
        event_type="CROSS_TENANT_ATTEMPT",
        detection_source="AUTH_GATEWAY",
        tenant_id=tenant_a.id,
        actor_id=actor_user_id,
        target_resource_type="StudentProfile",
        target_resource_id=str(uuid.uuid4()),
        ip_address="203.0.113.15",
        details={
            "actor_tenant": str(tenant_a.id),
            "target_tenant": str(tenant_b.id),
        },
    )

    det = await threat_engine.process_event(db_session, event)
    assert det is not None
    assert det.rule_id == "RULE-TENANT-001"
    assert det.severity == "CRITICAL"
    assert det.confidence == "CONFIRMED"

    # Verify incident and proposed action
    inc_stmt = select(SecurityIncident).where(SecurityIncident.id == det.incident_id)
    incident = (await db_session.execute(inc_stmt)).scalar_one()
    assert incident.severity == "CRITICAL"

    action_stmt = select(SecurityResponseAction).where(SecurityResponseAction.incident_id == incident.id)
    action = (await db_session.execute(action_stmt)).scalar_one()
    assert action.action_type == "REVOKE_SESSION"
    assert action.status == "PROPOSED"


@pytest.mark.asyncio
async def test_credential_stuffing_detection(
    db_session: AsyncSession,
    tenant_a: Institution,
):
    """Test 5: Single IP probing multiple distinct accounts triggers distributed credential stuffing alert."""
    threat_engine.clear()
    attacker_ip = "198.51.100.22"

    accounts = ["admin@apextech.edu", "finance@apextech.edu", "registrar@apextech.edu"]
    det = None
    for acc in accounts:
        event = NormalizedSecurityEvent(
            event_type="AUTH_LOGIN_FAILED",
            detection_source="AUTH_GATEWAY",
            tenant_id=tenant_a.id,
            ip_address=attacker_ip,
            details={"email": acc},
        )
        det = await threat_engine.process_event(db_session, event)

    assert det is not None
    assert det.rule_id == "RULE-AUTH-002"
    assert det.severity == "CRITICAL"


@pytest.mark.asyncio
async def test_privilege_escalation_detection(
    db_session: AsyncSession,
    tenant_a: Institution,
):
    """Test 6: Suspicious administrative role assignment triggers privilege escalation detection."""
    threat_engine.clear()
    actor_id = str(uuid.uuid4())

    event = NormalizedSecurityEvent(
        event_type="PRIVILEGE_ESCALATION_SUSPECTED",
        detection_source="AUDIT_MONITOR",
        tenant_id=tenant_a.id,
        actor_id=actor_id,
        target_resource_type="RoleAssignment",
        ip_address="10.10.10.10",
        details={"assigned_role": "SUPER_ADMIN"},
    )
    det = await threat_engine.process_event(db_session, event)
    assert det is not None
    assert det.rule_id == "RULE-PRIV-001"
    assert det.severity == "HIGH"


@pytest.mark.asyncio
async def test_permission_denial_spike_detection(
    db_session: AsyncSession,
    tenant_a: Institution,
):
    """Test 7: Repeated 403 authorization failures trigger permission denial spike detection."""
    threat_engine.clear()
    actor_id = str(uuid.uuid4())

    det = None
    for _ in range(10):
        event = NormalizedSecurityEvent(
            event_type="PERMISSION_DENIED_SPIKE",
            detection_source="API_GATEWAY",
            tenant_id=tenant_a.id,
            actor_id=actor_id,
            ip_address="172.16.0.5",
            details={"route": "/api/v1/finance/invoices"},
        )
        det = await threat_engine.process_event(db_session, event)

    assert det is not None
    assert det.rule_id == "RULE-AUTHZ-001"
    assert det.occurrence_count == 10


# =============================================================================
# 2. INCIDENT LIFECYCLE & INVESTIGATION (Tests 8-12)
# =============================================================================


@pytest.mark.asyncio
async def test_incident_valid_lifecycle_transitions(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Test 8: Validate the full incident lifecycle state machine transitions."""
    incident = SecurityIncident(
        tenant_id=tenant_a.id,
        incident_number="SEC-2026-9001",
        title="Test Lifecycle Incident",
        description="Testing valid state transitions",
        severity="HIGH",
        status="NEW",
    )
    db_session.add(incident)
    await db_session.commit()

    # NEW -> TRIAGED
    inc1 = await SecurityOpsService.transition_status(
        db_session, incident.id, "TRIAGED", tenant_admin_a.id, tenant_a.id, is_platform_operator=False
    )
    assert inc1.status == "TRIAGED"
    assert inc1.triaged_at is not None

    # TRIAGED -> INVESTIGATING
    inc2 = await SecurityOpsService.transition_status(
        db_session, incident.id, "INVESTIGATING", tenant_admin_a.id, tenant_a.id, is_platform_operator=False
    )
    assert inc2.status == "INVESTIGATING"

    # INVESTIGATING -> CONTAINED
    inc3 = await SecurityOpsService.transition_status(
        db_session, incident.id, "CONTAINED", tenant_admin_a.id, tenant_a.id, is_platform_operator=False
    )
    assert inc3.status == "CONTAINED"
    assert inc3.contained_at is not None

    # CONTAINED -> REMEDIATING
    inc4 = await SecurityOpsService.transition_status(
        db_session, incident.id, "REMEDIATING", tenant_admin_a.id, tenant_a.id, is_platform_operator=False
    )
    assert inc4.status == "REMEDIATING"

    # REMEDIATING -> RESOLVED
    inc5 = await SecurityOpsService.transition_status(
        db_session, incident.id, "RESOLVED", tenant_admin_a.id, tenant_a.id, is_platform_operator=False, reason="TRUE_POSITIVE_RESOLVED"
    )
    assert inc5.status == "RESOLVED"
    assert inc5.resolved_at is not None
    assert inc5.resolution_reason == "TRUE_POSITIVE_RESOLVED"

    # RESOLVED -> CLOSED
    inc6 = await SecurityOpsService.transition_status(
        db_session, incident.id, "CLOSED", tenant_admin_a.id, tenant_a.id, is_platform_operator=False, closure_summary="Verified and secured"
    )
    assert inc6.status == "CLOSED"
    assert inc6.closed_at is not None
    assert inc6.closure_summary == "Verified and secured"


@pytest.mark.asyncio
async def test_incident_invalid_lifecycle_transition_rejected(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Test 9: Invalid state jumps (e.g. NEW -> RESOLVED) are strictly rejected with ValidationException."""
    incident = SecurityIncident(
        tenant_id=tenant_a.id,
        incident_number="SEC-2026-9002",
        title="Invalid Jump Incident",
        description="Testing rejection of illegal state jumps",
        severity="MEDIUM",
        status="NEW",
    )
    db_session.add(incident)
    await db_session.commit()

    with pytest.raises(ValidationException) as exc_info:
        await SecurityOpsService.transition_status(
            db_session, incident.id, "RESOLVED", tenant_admin_a.id, tenant_a.id, is_platform_operator=False
        )
    assert "Invalid status transition" in str(exc_info.value)


@pytest.mark.asyncio
async def test_incident_reopen_workflow(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Test 10: Closed or resolved incident can be reopened with documented reason."""
    incident = SecurityIncident(
        tenant_id=tenant_a.id,
        incident_number="SEC-2026-9003",
        title="Reopen Incident",
        description="Testing reopen transition",
        severity="MEDIUM",
        status="CLOSED",
        closed_at=datetime.now(UTC),
    )
    db_session.add(incident)
    await db_session.commit()

    # CLOSED -> REOPENED
    reopened = await SecurityOpsService.transition_status(
        db_session, incident.id, "REOPENED", tenant_admin_a.id, tenant_a.id, is_platform_operator=False, reason="Recurrent breach detected"
    )
    assert reopened.status == "REOPENED"
    assert reopened.closed_at is None

    # REOPENED -> INVESTIGATING
    inv = await SecurityOpsService.transition_status(
        db_session, incident.id, "INVESTIGATING", tenant_admin_a.id, tenant_a.id, is_platform_operator=False
    )
    assert inv.status == "INVESTIGATING"


@pytest.mark.asyncio
async def test_responder_assignment_and_investigation_notes(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
    super_admin_user: User,
):
    """Test 11: Verify responder assignment and append-only investigation timeline notes."""
    incident = SecurityIncident(
        tenant_id=tenant_a.id,
        incident_number="SEC-2026-9004",
        title="Investigation Notes Incident",
        description="Testing forensic timeline notes",
        severity="HIGH",
        status="INVESTIGATING",
    )
    db_session.add(incident)
    await db_session.commit()

    # Assign responder
    assigned = await SecurityOpsService.assign_responder(
        db_session, incident.id, tenant_admin_a.id, super_admin_user.id, tenant_a.id, is_platform_operator=True
    )
    assert assigned.assigned_to_user_id == tenant_admin_a.id

    # Add forensic investigation note
    note = await SecurityOpsService.add_note(
        db_session,
        incident_id=incident.id,
        author_user_id=tenant_admin_a.id,
        content="Analyzed reverse proxy logs. Source IP correlates with known tor exit node.",
        note_type="INVESTIGATION",
        evidence_references=[{"ip": "185.220.101.5", "asn": "AS208323"}],
        tenant_id=tenant_a.id,
        is_platform_operator=False,
    )
    assert note.id is not None
    assert note.note_type == "INVESTIGATION"
    assert len(note.evidence_references) == 1


@pytest.mark.asyncio
async def test_remediation_task_creation_and_completion(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Test 12: Create remediation task and update to COMPLETED."""
    incident = SecurityIncident(
        tenant_id=tenant_a.id,
        incident_number="SEC-2026-9005",
        title="Remediation Task Incident",
        description="Testing remediation tasks",
        severity="MEDIUM",
        status="REMEDIATING",
    )
    db_session.add(incident)
    await db_session.commit()

    task = await SecurityOpsService.create_remediation_task(
        db_session,
        incident_id=incident.id,
        title="Rotate affected database connection pool credentials",
        description="Verify old secret is rejected",
        assigned_to_user_id=tenant_admin_a.id,
        due_at=datetime.now(UTC) + timedelta(days=2),
        actor_user_id=tenant_admin_a.id,
        tenant_id=tenant_a.id,
        is_platform_operator=False,
    )
    assert task.status == "PENDING"
    assert task.completed_at is None

    # Complete task
    completed_task = await SecurityOpsService.update_remediation_task_status(
        db_session,
        task_id=task.id,
        new_status="COMPLETED",
        actor_user_id=tenant_admin_a.id,
        tenant_id=tenant_a.id,
        is_platform_operator=False,
    )
    assert completed_task.status == "COMPLETED"
    assert completed_task.completed_at is not None


# =============================================================================
# 3. RESPONSE ACTIONS & SAFETY CONTROLS (Tests 13-15)
# =============================================================================


@pytest.mark.asyncio
async def test_response_action_approval_gate_and_execution(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Test 13: High-risk action (LOCK_ACCOUNT) mandates approval; unapproved execution is blocked."""
    incident = SecurityIncident(
        tenant_id=tenant_a.id,
        incident_number="SEC-2026-9006",
        title="Action Approval Test Incident",
        description="Testing approval safeguards",
        severity="HIGH",
        status="INVESTIGATING",
    )
    db_session.add(incident)
    await db_session.commit()

    # Propose high-risk LOCK_ACCOUNT action
    action = await SecurityResponseService.propose_action(
        db=db_session,
        incident_id=incident.id,
        action_type="LOCK_ACCOUNT",
        target_type="USER",
        target_identifier=str(tenant_admin_a.id),
        risk_level="HIGH",
        requires_approval=True,
        proposed_by_user_id=tenant_admin_a.id,
        tenant_id=tenant_a.id,
        is_platform_operator=False,
    )
    assert action.status == "PROPOSED"
    assert action.requires_approval is True

    # Attempt execution while still PROPOSED -> must raise ValidationException
    with pytest.raises(ValidationException) as exc_info:
        await SecurityResponseService.execute_action(
            db=db_session,
            action_id=action.id,
            executing_user_id=tenant_admin_a.id,
            tenant_id=tenant_a.id,
            is_platform_operator=False,
        )
    assert "requires formal administrative approval" in str(exc_info.value)

    # Approve action
    approved_action = await SecurityResponseService.approve_action(
        db=db_session,
        action_id=action.id,
        approving_user_id=tenant_admin_a.id,
        tenant_id=tenant_a.id,
        is_platform_operator=False,
    )
    assert approved_action.status == "APPROVED"

    # Now execute -> must succeed
    executed_action = await SecurityResponseService.execute_action(
        db=db_session,
        action_id=action.id,
        executing_user_id=tenant_admin_a.id,
        tenant_id=tenant_a.id,
        is_platform_operator=False,
    )
    assert executed_action.status == "EXECUTED"
    assert executed_action.executed_at is not None

    # Verify target user was locked
    await db_session.refresh(tenant_admin_a)
    assert tenant_admin_a.locked_until is not None

    # Verify audit log was recorded
    audit_stmt = select(AuditLog).where(
        AuditLog.action == "SECURITY_ACTION_EXECUTE_LOCK_ACCOUNT"
    )
    audit = (await db_session.execute(audit_stmt)).scalar_one_or_none()
    assert audit is not None


@pytest.mark.asyncio
async def test_response_action_idempotency(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Test 14: Repeated execution of an already executed action is idempotent and safe."""
    incident = SecurityIncident(
        tenant_id=tenant_a.id,
        incident_number="SEC-2026-9007",
        title="Idempotent Action Incident",
        description="Testing idempotency",
        severity="MEDIUM",
        status="CONTAINED",
    )
    db_session.add(incident)
    await db_session.commit()

    action = await SecurityResponseService.propose_action(
        db=db_session,
        incident_id=incident.id,
        action_type="RATE_LIMIT_IP",
        target_type="IP",
        target_identifier="198.51.100.77",
        risk_level="LOW",
        requires_approval=False,
        proposed_by_user_id=tenant_admin_a.id,
        tenant_id=tenant_a.id,
        is_platform_operator=False,
    )

    first_exec = await SecurityResponseService.execute_action(
        db_session, action.id, tenant_admin_a.id, tenant_a.id, is_platform_operator=False
    )
    assert first_exec.status == "EXECUTED"
    first_time = first_exec.executed_at

    # Second execution call -> returns cleanly without error
    second_exec = await SecurityResponseService.execute_action(
        db_session, action.id, tenant_admin_a.id, tenant_a.id, is_platform_operator=False
    )
    assert second_exec.status == "EXECUTED"
    assert second_exec.executed_at == first_time


@pytest.mark.asyncio
async def test_response_action_rollback(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Test 15: Executed containment action (RATE_LIMIT_IP) can be rolled back safely."""
    incident = SecurityIncident(
        tenant_id=tenant_a.id,
        incident_number="SEC-2026-9008",
        title="Rollback Action Incident",
        description="Testing rollback",
        severity="LOW",
        status="INVESTIGATING",
    )
    db_session.add(incident)
    await db_session.commit()

    ip = "192.0.2.11"
    action = await SecurityResponseService.propose_action(
        db=db_session,
        incident_id=incident.id,
        action_type="RATE_LIMIT_IP",
        target_type="IP",
        target_identifier=ip,
        risk_level="LOW",
        requires_approval=False,
        proposed_by_user_id=tenant_admin_a.id,
        tenant_id=tenant_a.id,
        is_platform_operator=False,
    )
    await SecurityResponseService.execute_action(
        db_session, action.id, tenant_admin_a.id, tenant_a.id, is_platform_operator=False
    )
    assert ip in BLOCKED_IPS_REGISTRY

    # Rollback action
    rolled_back = await SecurityResponseService.rollback_action(
        db_session, action.id, tenant_admin_a.id, tenant_a.id, is_platform_operator=False
    )
    assert rolled_back.status == "ROLLED_BACK"
    assert ip not in BLOCKED_IPS_REGISTRY


# =============================================================================
# 4. TENANT ISOLATION & PBAC ACCESS (Tests 16-18)
# =============================================================================


@pytest.mark.asyncio
async def test_strict_tenant_isolation_on_incidents(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_b: Institution,
    tenant_admin_a: User,
    tenant_admin_b: User,
):
    """Test 16: Institution Admin can only access their tenant's incidents; cross-tenant read is blocked."""
    inc_a = SecurityIncident(
        tenant_id=tenant_a.id,
        incident_number="SEC-2026-A001",
        title="Tenant A Incident",
        description="Confidential incident in Institution A",
        severity="HIGH",
        status="NEW",
    )
    inc_b = SecurityIncident(
        tenant_id=tenant_b.id,
        incident_number="SEC-2026-B001",
        title="Tenant B Incident",
        description="Confidential incident in Institution B",
        severity="HIGH",
        status="NEW",
    )
    db_session.add_all([inc_a, inc_b])
    await db_session.commit()

    # Tenant A admin queries incidents -> sees ONLY Tenant A
    items_a, total_a = await SecurityOpsService.list_incidents(
        db_session, tenant_id=tenant_a.id, is_platform_operator=False
    )
    inc_numbers_a = [i.incident_number for i in items_a]
    assert "SEC-2026-A001" in inc_numbers_a
    assert "SEC-2026-B001" not in inc_numbers_a

    # Tenant A admin attempts direct ID lookup of Tenant B incident -> raises NotFoundException
    with pytest.raises(NotFoundException):
        await SecurityOpsService.get_incident(
            db_session, inc_b.id, tenant_id=tenant_a.id, is_platform_operator=False
        )


@pytest.mark.asyncio
async def test_platform_operator_cross_tenant_access(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_b: Institution,
    super_admin_user: User,
):
    """Test 17: Platform Operator can view incidents across tenants."""
    inc_a = SecurityIncident(
        tenant_id=tenant_a.id,
        incident_number="SEC-2026-A002",
        title="Tenant A Platform Incident",
        description="Tenant A issue",
        severity="MEDIUM",
        status="NEW",
    )
    inc_b = SecurityIncident(
        tenant_id=tenant_b.id,
        incident_number="SEC-2026-B002",
        title="Tenant B Platform Incident",
        description="Tenant B issue",
        severity="MEDIUM",
        status="NEW",
    )
    db_session.add_all([inc_a, inc_b])
    await db_session.commit()

    items, total = await SecurityOpsService.list_incidents(
        db_session, tenant_id=None, is_platform_operator=True
    )
    inc_numbers = [i.incident_number for i in items]
    assert "SEC-2026-A002" in inc_numbers
    assert "SEC-2026-B002" in inc_numbers

    # Direct access to both succeeds
    res_a = await SecurityOpsService.get_incident(
        db_session, inc_a.id, tenant_id=None, is_platform_operator=True
    )
    res_b = await SecurityOpsService.get_incident(
        db_session, inc_b.id, tenant_id=None, is_platform_operator=True
    )
    assert res_a.id == inc_a.id
    assert res_b.id == inc_b.id


@pytest.mark.asyncio
async def test_soc_overview_and_api_endpoints(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    """Test 18: Verify REST API endpoints and SOC overview metrics aggregation."""
    # Seed an incident and detection in tenant_a
    inc = SecurityIncident(
        tenant_id=tenant_a.id,
        incident_number="SEC-2026-API01",
        title="API Test Incident",
        description="Testing REST APIs",
        severity="CRITICAL",
        status="NEW",
    )
    db_session.add(inc)
    await db_session.commit()

    headers = make_auth_headers(
        tenant_admin_a,
        tenant_a.id,
        role_name="INSTITUTION_ADMIN",
    )

    # 1. GET /api/v1/security/overview
    resp_overview = await client.get("/api/v1/security/overview", headers=headers)
    assert resp_overview.status_code == 200
    data_ov = resp_overview.json()
    assert "critical_incidents" in data_ov
    assert data_ov["critical_incidents"] >= 1

    # 2. GET /api/v1/security/incidents
    resp_list = await client.get("/api/v1/security/incidents", headers=headers)
    assert resp_list.status_code == 200
    data_list = resp_list.json()
    assert data_list["total"] >= 1
    assert any(i["incident_number"] == "SEC-2026-API01" for i in data_list["items"])

    # 3. POST /api/v1/security/incidents/{id}/status
    resp_status = await client.post(
        f"/api/v1/security/incidents/{inc.id}/status",
        headers=headers,
        json={"status": "TRIAGED", "reason": "Triaged by security lead"},
    )
    assert resp_status.status_code == 200
    assert resp_status.json()["status"] == "TRIAGED"

    # 4. POST /api/v1/security/actions/propose
    resp_act = await client.post(
        "/api/v1/security/actions/propose",
        headers=headers,
        json={
            "incident_id": str(inc.id),
            "action_type": "RATE_LIMIT_IP",
            "target_type": "IP",
            "target_identifier": "192.0.2.99",
            "risk_level": "LOW",
            "requires_approval": False,
        },
    )
    assert resp_act.status_code == 201
    act_data = resp_act.json()
    assert act_data["status"] == "PROPOSED"
