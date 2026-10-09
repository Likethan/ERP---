"""Comprehensive Test Suite for Enterprise Workflow, Case Management & HITL Operations Layer.

Step 25 implementation.
Covers:
1. Case Types CRUD and validation.
2. Work Queues and membership assignment.
3. Case creation, atomic sequence numbering, and lifecycle.
4. Concurrency-safe human task claiming, release, and reassignments.
5. Task completion, authoritative decision recording, and resulting transitions.
6. Temporary authority delegation and validity window verification.
7. SLA policies, runtime clocks, breach detection, and automated escalation.
8. Case comments with visibility scoping and document attachments.
9. Cross-case linking and relationship semantics.
10. Case resolution requirements, closure, and controlled reopening.
11. Multi-tenant SaaS isolation and PBAC authorization enforcement.
12. Operational case analytics and health metrics.
13. Intelligence layer read-only case tools integration.
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    DelegationInvalidException,
    TaskAlreadyCompletedException,
)
from app.core.permissions import DEFAULT_ROLE_PERMISSIONS
from app.core.security import ACCESS_TOKEN_COOKIE_NAME, create_access_token
from app.domains.intelligence.tools.case_management import (
    handle_get_case_analytics_summary,
    handle_get_queue_summary,
)
from app.models.case_management import (
    CasePriority,
    CaseStatus,
    HumanDecision,
    SlaStatus,
    TaskStatus,
    TaskType,
)
from app.models.core import Institution
from app.models.people import User
from app.models.workflow import (
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowExecutionStatus,
    WorkflowVersion,
)
from app.schemas.case_management import (
    CaseCreate,
    SlaPolicyCreate,
    TaskCompleteRequest,
    TaskCreate,
    TaskDelegationCreate,
)
from app.services.case_service import CaseService
from app.services.sla_service import SlaService
from app.services.task_service import TaskService


def make_auth_headers(
    user: User,
    tenant_id: uuid.UUID,
    role_name: str = "INSTITUTION_ADMIN",
    custom_permissions: list[str] | None = None,
) -> dict[str, str]:
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
# 1. CASE TYPES CRUD
# =============================================================================


@pytest.mark.asyncio
async def test_case_types_crud(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    headers = make_auth_headers(tenant_admin_a, tenant_a.id)

    # 1. Create Case Type
    code = f"DISCIPLINE_{uuid.uuid4().hex[:6]}".upper()
    create_payload = {
        "code": code,
        "name": "Student Disciplinary Hearing",
        "description": "Formal institutional discipline proceedings",
        "module": "STUDENTS",
        "default_priority": "HIGH",
        "sla_hours": 24,
        "requires_decision": True,
        "is_active": True,
    }
    resp = await client.post("/api/v1/case-types", json=create_payload, headers=headers)
    assert resp.status_code == 201
    created = resp.json()["data"]
    assert created["code"] == code
    assert created["sla_hours"] == 24
    case_type_id = created["id"]

    # 2. List Case Types
    list_resp = await client.get("/api/v1/case-types?module=STUDENTS", headers=headers)
    assert list_resp.status_code == 200
    types = list_resp.json()["data"]
    assert any(t["code"] == code for t in types)

    # 3. Update Case Type
    update_payload = {"sla_hours": 48, "default_priority": "URGENT"}
    patch_resp = await client.patch(
        f"/api/v1/case-types/{case_type_id}", json=update_payload, headers=headers
    )
    assert patch_resp.status_code == 200
    updated = patch_resp.json()["data"]
    assert updated["sla_hours"] == 48
    assert updated["default_priority"] == "URGENT"


# =============================================================================
# 2. WORK QUEUES & MEMBERS
# =============================================================================


@pytest.mark.asyncio
async def test_work_queues_and_members(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
    faculty_user: User,
):
    headers = make_auth_headers(tenant_admin_a, tenant_a.id)

    # 1. Create Work Queue
    q_key = f"LEGAL_DESK_{uuid.uuid4().hex[:6]}".upper()
    q_payload = {
        "key": q_key,
        "name": "Institutional Legal & Compliance Desk",
        "description": "Compliance inquiries and legal reviews",
        "module": "GENERAL",
        "is_active": True,
        "assignment_policy": "ROUND_ROBIN",
        "capacity": 50,
        "sla_hours": 24,
    }
    resp = await client.post("/api/v1/queues", json=q_payload, headers=headers)
    assert resp.status_code == 201
    queue = resp.json()["data"]
    queue_id = queue["id"]
    assert queue["key"] == q_key
    assert queue["assignment_policy"] == "ROUND_ROBIN"

    # 2. Add Member to Queue
    mem_payload = {
        "user_id": str(faculty_user.id),
        "is_supervisor": True,
        "max_active_tasks": 15,
    }
    mem_resp = await client.post(
        f"/api/v1/queues/{queue_id}/members", json=mem_payload, headers=headers
    )
    assert mem_resp.status_code == 201
    member = mem_resp.json()["data"]
    assert member["is_supervisor"] is True
    assert member["max_active_tasks"] == 15

    # 3. Get Queue Detail
    get_resp = await client.get(f"/api/v1/queues/{queue_id}", headers=headers)
    assert get_resp.status_code == 200
    q_detail = get_resp.json()["data"]
    assert len(q_detail["members"]) >= 1

    # 4. Remove Member
    del_resp = await client.delete(
        f"/api/v1/queues/{queue_id}/members/{faculty_user.id}", headers=headers
    )
    assert del_resp.status_code == 200
    assert del_resp.json()["data"]["removed"] is True


# =============================================================================
# 3. CASE CREATION & ATOMIC NUMBERING
# =============================================================================


@pytest.mark.asyncio
async def test_case_creation_and_numbering(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    headers = make_auth_headers(tenant_admin_a, tenant_a.id)

    payload = {
        "case_type_code": "DOCUMENT_VERIFICATION",
        "title": "Admissions 12th Grade Marksheet Verification",
        "description": "Student submitted HSC certificate for authenticity check",
        "priority": "HIGH",
        "subject_entity_type": "student",
        "subject_entity_id": str(uuid.uuid4()),
        "metadata_json": {"academic_year": "2026-2027"},
    }
    resp = await client.post("/api/v1/cases", json=payload, headers=headers)
    assert resp.status_code == 201
    case = resp.json()["data"]

    assert case["case_number"].startswith("CASE-")
    assert case["status"] == "OPEN"
    assert case["priority"] == "HIGH"
    assert case["due_at"] is not None

    case_id = case["id"]

    # Verify timeline event created
    timeline_resp = await client.get(f"/api/v1/cases/{case_id}/timeline", headers=headers)
    assert timeline_resp.status_code == 200
    events = timeline_resp.json()["data"]
    assert any(e["event_type"] == "CASE_CREATED" for e in events)


# =============================================================================
# 4. CASE LIFECYCLE: RESOLUTION, CLOSURE, AND REOPENING
# =============================================================================


@pytest.mark.asyncio
async def test_case_lifecycle_resolve_and_reopen(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    headers = make_auth_headers(tenant_admin_a, tenant_a.id)
    case_service = CaseService(db_session)
    task_service = TaskService(db_session)

    # 1. Create Case
    case = await case_service.create_case(
        tenant_a.id,
        CaseCreate(
            case_type_code="FEE_REFUND",
            title="Library Deposit Refund Claim",
            priority=CasePriority.NORMAL,
        ),
        actor_id=tenant_admin_a.id,
    )

    # 2. Add Human Task to case
    task = await task_service.create_task(
        tenant_a.id,
        TaskCreate(
            case_id=case.id,
            title="Audit library dues clearance",
            task_type=TaskType.REVIEW,
        ),
        actor_id=tenant_admin_a.id,
    )

    # 3. Attempt to resolve case before task completion -> must fail validation
    resolve_payload = {
        "resolution_reason": "Refund approved and paid",
        "resolution_notes": "All dues cleared and receipt issued",
    }
    bad_resolve = await client.post(
        f"/api/v1/cases/{case.id}/resolve", json=resolve_payload, headers=headers
    )
    assert bad_resolve.status_code == 422
    err_body = bad_resolve.json()
    err_msg = (
        err_body.get("error", {}).get("message", "")
        if isinstance(err_body.get("error"), dict)
        else err_body.get("message", "")
    )
    assert "human task(s) remain pending" in err_msg

    # 4. Complete Human Task with explicit decision
    await task_service.complete_task(
        tenant_a.id,
        task.id,
        actor_id=tenant_admin_a.id,
        dto=TaskCompleteRequest(
            decision=HumanDecision.APPROVE,
            reason="Confirmed no overdue books in library catalog",
        ),
    )

    # 5. Now resolve case -> should succeed
    resolve_resp = await client.post(
        f"/api/v1/cases/{case.id}/resolve", json=resolve_payload, headers=headers
    )
    assert resolve_resp.status_code == 200
    resolved = resolve_resp.json()["data"]
    assert resolved["status"] == "RESOLVED"
    assert resolved["resolution_reason"] == "Refund approved and paid"

    # 6. Close Case
    close_resp = await client.post(
        f"/api/v1/cases/{case.id}/close?closure_notes=Audit+verified", headers=headers
    )
    assert close_resp.status_code == 200
    assert close_resp.json()["data"]["status"] == "CLOSED"

    # 7. Reopen Case
    reopen_payload = {"reopen_reason": "Student disputed refund amount recalculation"}
    reopen_resp = await client.post(
        f"/api/v1/cases/{case.id}/reopen", json=reopen_payload, headers=headers
    )
    assert reopen_resp.status_code == 200
    reopened = reopen_resp.json()["data"]
    assert reopened["status"] == "REOPENED"
    assert reopened["reopen_count"] == 1


# =============================================================================
# 5. CASE COMMENTS & ATTACHMENTS
# =============================================================================


@pytest.mark.asyncio
async def test_case_comments_and_attachments(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    headers = make_auth_headers(tenant_admin_a, tenant_a.id)
    case_service = CaseService(db_session)

    case = await case_service.create_case(
        tenant_a.id,
        CaseCreate(
            case_type_code="GENERAL_ADMINISTRATION",
            title="Classroom Air Conditioning Repair",
            priority=CasePriority.NORMAL,
        ),
        actor_id=tenant_admin_a.id,
    )

    # 1. Add Internal Comment
    comment_payload = {
        "content": "Facilities supervisor dispatched technician to Block B-201.",
        "visibility": "INTERNAL",
    }
    c_resp = await client.post(
        f"/api/v1/cases/{case.id}/comments", json=comment_payload, headers=headers
    )
    assert c_resp.status_code == 201
    assert c_resp.json()["data"]["visibility"] == "INTERNAL"

    # 2. List Comments
    list_c = await client.get(f"/api/v1/cases/{case.id}/comments", headers=headers)
    assert list_c.status_code == 200
    comments = list_c.json()["data"]
    assert len(comments) >= 1

    # 3. Add Attachment Reference
    dummy_doc_id = uuid.uuid4()
    att_payload = {
        "document_id": str(dummy_doc_id),
        "attachment_type": "INSPECTION_PHOTO",
        "title": "HVAC compressor inspection log",
        "visibility": "INTERNAL",
    }
    a_resp = await client.post(
        f"/api/v1/cases/{case.id}/attachments", json=att_payload, headers=headers
    )
    assert a_resp.status_code == 201
    att = a_resp.json()["data"]
    assert att["title"] == "HVAC compressor inspection log"

    # 4. List Attachments
    list_a = await client.get(f"/api/v1/cases/{case.id}/attachments", headers=headers)
    assert list_a.status_code == 200
    assert len(list_a.json()["data"]) >= 1


# =============================================================================
# 6. CASE RELATIONSHIPS
# =============================================================================


@pytest.mark.asyncio
async def test_case_relationships(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    headers = make_auth_headers(tenant_admin_a, tenant_a.id)
    case_service = CaseService(db_session)

    case1 = await case_service.create_case(
        tenant_a.id,
        CaseCreate(case_type_code="HOSTEL_COMPLAINT", title="Room 101 Water Leakage"),
        actor_id=tenant_admin_a.id,
    )
    case2 = await case_service.create_case(
        tenant_a.id,
        CaseCreate(case_type_code="HOSTEL_COMPLAINT", title="Room 101 Duplicate Leakage Complaint"),
        actor_id=tenant_admin_a.id,
    )

    # 1. Establish Duplicate Relationship
    rel_payload = {
        "target_case_id": str(case2.id),
        "relationship_type": "DUPLICATE_OF",
        "notes": "Second complaint filed by roommate",
    }
    rel_resp = await client.post(
        f"/api/v1/cases/{case1.id}/relationships", json=rel_payload, headers=headers
    )
    assert rel_resp.status_code == 201
    rel = rel_resp.json()["data"]
    assert rel["relationship_type"] == "DUPLICATE_OF"

    # 2. Verify Cannot establish self-relationship
    bad_rel = {
        "target_case_id": str(case1.id),
        "relationship_type": "RELATED_TO",
    }
    bad_resp = await client.post(
        f"/api/v1/cases/{case1.id}/relationships", json=bad_rel, headers=headers
    )
    assert bad_resp.status_code == 422
    err_body = bad_resp.json()
    err_msg = (
        err_body.get("error", {}).get("message", "")
        if isinstance(err_body.get("error"), dict)
        else err_body.get("message", "")
    )
    assert "cannot establish a relationship to itself" in err_msg


# =============================================================================
# 7. CONCURRENCY-SAFE TASK CLAIMING, RELEASE & COMPLETION
# =============================================================================


@pytest.mark.asyncio
async def test_task_claim_concurrency_race(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
    faculty_user: User,
):
    case_service = CaseService(db_session)
    task_service = TaskService(db_session)

    case = await case_service.create_case(
        tenant_a.id,
        CaseCreate(case_type_code="EXAM_MARK_CORRECTION", title="CS101 Grade Revaluation"),
        actor_id=tenant_admin_a.id,
    )
    task = await task_service.create_task(
        tenant_a.id,
        TaskCreate(
            case_id=case.id,
            title="Recheck question 4 rubric",
            task_type=TaskType.REVIEW,
        ),
        actor_id=tenant_admin_a.id,
    )

    # Operator A claims task
    claimed = await task_service.claim_task(tenant_a.id, task.id, user_id=tenant_admin_a.id)
    assert claimed.status == TaskStatus.CLAIMED
    assert claimed.assigned_user_id == tenant_admin_a.id

    # Operator B concurrently attempts to claim -> must fail with
    # TaskAlreadyClaimedException (HTTP 409)
    headers_b = make_auth_headers(faculty_user, tenant_a.id)
    race_resp = await client.post(f"/api/v1/tasks/{task.id}/claim", headers=headers_b)
    assert race_resp.status_code == 409
    err_body = race_resp.json()
    err_msg = (
        err_body.get("error", {}).get("message", "")
        if isinstance(err_body.get("error"), dict)
        else err_body.get("message", "")
    )
    assert "already been claimed" in err_msg

    # Operator A releases task
    released = await task_service.release_task(
        tenant_a.id, task.id, user_id=tenant_admin_a.id, reason="Delegating to another instructor"
    )
    assert released.status == TaskStatus.PENDING
    assert released.assigned_user_id is None

    # Now Operator B can claim cleanly
    claimed_b = await task_service.claim_task(tenant_a.id, task.id, user_id=faculty_user.id)
    assert claimed_b.status == TaskStatus.CLAIMED
    assert claimed_b.assigned_user_id == faculty_user.id

    # Operator B completes task with DECISION
    complete_dto = TaskCompleteRequest(
        decision=HumanDecision.APPROVE,
        reason="Answer script reviewed; added 2 marks for algorithm efficiency",
        evidence_reference="DOC-EXAM-REV-491",
        resulting_transition="APPROVED",
    )
    completed = await task_service.complete_task(
        tenant_a.id, task.id, actor_id=faculty_user.id, dto=complete_dto
    )
    assert completed.status == TaskStatus.COMPLETED
    assert completed.completed_by_id == faculty_user.id

    # Trying to claim or complete an already finished task must fail
    with pytest.raises(TaskAlreadyCompletedException):
        await task_service.claim_task(tenant_a.id, task.id, user_id=tenant_admin_a.id)


# =============================================================================
# 8. TASK REASSIGNMENT & DELEGATIONS
# =============================================================================


@pytest.mark.asyncio
async def test_task_reassignment_and_delegation(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
    faculty_user: User,
):
    headers = make_auth_headers(tenant_admin_a, tenant_a.id)
    case_service = CaseService(db_session)
    task_service = TaskService(db_session)

    case = await case_service.create_case(
        tenant_a.id,
        CaseCreate(case_type_code="PLACEMENT_REVIEW", title="Offer Letter Verification"),
        actor_id=tenant_admin_a.id,
    )
    task = await task_service.create_task(
        tenant_a.id,
        TaskCreate(
            case_id=case.id,
            title="Verify corporate CTC breakup",
            task_type=TaskType.REVIEW,
        ),
        actor_id=tenant_admin_a.id,
    )

    # 1. Reassign Task to faculty user
    reassign_payload = {
        "new_user_id": str(faculty_user.id),
        "reason": "Department faculty coordinator assigned for verification",
    }
    r_resp = await client.post(
        f"/api/v1/tasks/{task.id}/reassign", json=reassign_payload, headers=headers
    )
    assert r_resp.status_code == 200
    reassigned = r_resp.json()["data"]
    assert reassigned["assigned_user_id"] == str(faculty_user.id)
    assert reassigned["status"] == "CLAIMED"

    # 2. Create Authority Delegation
    now = datetime.now(UTC)
    del_payload = {
        "delegatee_user_id": str(faculty_user.id),
        "scope_module": "PLACEMENT",
        "valid_from": now.isoformat(),
        "valid_until": (now + timedelta(days=7)).isoformat(),
        "reason": "Annual leave coverage",
    }
    del_resp = await client.post("/api/v1/tasks/delegations", json=del_payload, headers=headers)
    assert del_resp.status_code == 201
    delegation = del_resp.json()["data"]
    assert delegation["is_active"] is True

    # Verify delegation access check
    has_access = await task_service.verify_delegated_access(
        tenant_a.id,
        delegator_id=tenant_admin_a.id,
        user_id=faculty_user.id,
        module="PLACEMENT",
    )
    assert has_access is True

    # 3. Verify Invalid Delegation (end before start) rejected
    with pytest.raises(DelegationInvalidException):
        await task_service.create_delegation(
            tenant_a.id,
            delegator_id=tenant_admin_a.id,
            dto=TaskDelegationCreate(
                delegatee_user_id=faculty_user.id,
                valid_from=now,
                valid_until=now - timedelta(hours=1),
            ),
        )


# =============================================================================
# 9. SLA POLICIES, CLOCK INITIALIZATION & ESCALATION SWEEP
# =============================================================================


@pytest.mark.asyncio
async def test_sla_policy_and_breach_escalation(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    sla_service = SlaService(db_session)
    case_service = CaseService(db_session)

    # 1. Create SLA Policy
    policy = await sla_service.create_sla_policy(
        tenant_a.id,
        SlaPolicyCreate(
            name="Urgent Safety SLA",
            module="HOSTEL",
            priority=CasePriority.URGENT,
            target_duration_minutes=60,
            warning_threshold_percentage=50,
            business_hours_only=False,
        ),
        actor_id=tenant_admin_a.id,
    )
    assert policy.target_duration_minutes == 60

    # 2. Create Case with URGENT priority
    case = await case_service.create_case(
        tenant_a.id,
        CaseCreate(
            case_type_code="HOSTEL_COMPLAINT",
            title="Main Wing Power Outage",
            priority=CasePriority.URGENT,
        ),
        actor_id=tenant_admin_a.id,
    )

    # Fetch SLA instance initialized for case
    sla_inst = await case_service.repo.get_sla_instance_by_case(tenant_a.id, case.id)
    assert sla_inst is not None
    assert sla_inst.status == SlaStatus.ON_TRACK
    assert sla_inst.breached is False

    # Simulate past deadline (breach)
    sla_inst.due_at = datetime.now(UTC) - timedelta(minutes=10)
    await db_session.flush()

    # 3. Run background SLA deadline check
    sweep_result = await sla_service.check_deadlines_and_escalate(tenant_a.id)
    assert sweep_result["breached"] >= 1
    assert sweep_result["escalated"] >= 1

    # Verify Case transitioned to ESCALATED
    refreshed_case = await case_service.get_case(tenant_a.id, case.id)
    assert refreshed_case.status == CaseStatus.ESCALATED
    assert refreshed_case.sla_breached is True


# =============================================================================
# 10. MULTI-TENANT SAAS ISOLATION
# =============================================================================


@pytest.mark.asyncio
async def test_cross_tenant_isolation(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_b: Institution,
    tenant_admin_a: User,
    tenant_admin_b: User,
):
    case_service = CaseService(db_session)

    # Tenant A creates a case
    case_a = await case_service.create_case(
        tenant_a.id,
        CaseCreate(
            case_type_code="STUDENT_SUPPORT",
            title="Confidential Academic Counseling Record",
            priority=CasePriority.HIGH,
        ),
        actor_id=tenant_admin_a.id,
    )

    # Tenant B attempts to read Tenant A's case via API -> must return 404
    headers_b = make_auth_headers(tenant_admin_b, tenant_b.id)
    cross_resp = await client.get(f"/api/v1/cases/{case_a.id}", headers=headers_b)
    assert cross_resp.status_code == 404

    # Tenant B attempts to resolve Tenant A's case -> must return 404
    cross_resolve = await client.post(
        f"/api/v1/cases/{case_a.id}/resolve",
        json={"resolution_reason": "Hacked", "resolution_notes": "Cross tenant breach attempt"},
        headers=headers_b,
    )
    assert cross_resolve.status_code == 404


# =============================================================================
# 11. CASE OPERATIONAL ANALYTICS
# =============================================================================


@pytest.mark.asyncio
async def test_case_analytics_api(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    headers = make_auth_headers(tenant_admin_a, tenant_a.id)
    case_service = CaseService(db_session)

    # Seed cases in various states
    await case_service.create_case(
        tenant_a.id,
        CaseCreate(
            case_type_code="GENERAL_ADMINISTRATION", title="Audit 1", priority=CasePriority.LOW
        ),
        actor_id=tenant_admin_a.id,
    )
    await case_service.create_case(
        tenant_a.id,
        CaseCreate(
            case_type_code="GENERAL_ADMINISTRATION", title="Audit 2", priority=CasePriority.HIGH
        ),
        actor_id=tenant_admin_a.id,
    )

    resp = await client.get("/api/v1/cases/analytics", headers=headers)
    assert resp.status_code == 200
    analytics = resp.json()["data"]

    assert analytics["total_cases"] >= 2
    assert "open_cases" in analytics
    assert "sla_compliance_rate" in analytics
    assert "cases_by_priority" in analytics
    assert "cases_by_status" in analytics


# =============================================================================
# 12. WORKFLOW INSTANCE HITL TRANSITION BRIDGE
# =============================================================================


@pytest.mark.asyncio
async def test_workflow_instance_transition_bridge(
    client: AsyncClient,
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    headers = make_auth_headers(tenant_admin_a, tenant_a.id)

    # 1. Create a dummy WorkflowDefinition & Execution
    wf_def = WorkflowDefinition(
        tenant_id=tenant_a.id,
        name="Student Leave Multi-tier Approval",
        code=f"LEAVE_APP_{uuid.uuid4().hex[:6]}",
        domain="ATTENDANCE",
    )
    db_session.add(wf_def)
    await db_session.flush()

    wf_ver = WorkflowVersion(
        tenant_id=tenant_a.id,
        workflow_id=wf_def.id,
        version_number=1,
        definition_json={"steps": []},
    )
    db_session.add(wf_ver)
    await db_session.flush()

    execution = WorkflowExecution(
        tenant_id=tenant_a.id,
        workflow_id=wf_def.id,
        workflow_version_id=wf_ver.id,
        trigger_type="MANUAL",
        idempotency_key=f"idemp_{uuid.uuid4().hex}",
        status=WorkflowExecutionStatus.WAITING,
        correlation_id=str(uuid.uuid4()),
    )
    db_session.add(execution)
    await db_session.commit()

    # 2. Bridge HITL Decision via Transition Endpoint
    transition_payload = {
        "action": "APPROVE",
        "reason": "Department Chair confirmed medical certificate authenticity",
        "target_step_key": "APPROVED",
        "context_updates": {"medical_verified": True},
    }
    resp = await client.post(
        f"/api/v1/workflow-instances/{execution.id}/transition",
        json=transition_payload,
        headers=headers,
    )
    assert resp.status_code == 200
    res_data = resp.json()["data"]
    assert res_data["status"] == "SUCCEEDED"
    assert res_data["decision_recorded"] == "APPROVE"


# =============================================================================
# 13. INTELLIGENCE LAYER CASE MANAGEMENT TOOLS
# =============================================================================


@pytest.mark.asyncio
async def test_intelligence_tools_integration(
    db_session: AsyncSession,
    tenant_a: Institution,
    tenant_admin_a: User,
):
    # 1. Summary tool
    res_analytics = await handle_get_case_analytics_summary(
        db=db_session,
        tenant_id=tenant_a.id,
        user=tenant_admin_a,
        params={},
    )
    assert "total_cases" in res_analytics
    assert "sla_compliance_rate" in res_analytics

    # 2. Queue summary tool
    res_queues = await handle_get_queue_summary(
        db=db_session,
        tenant_id=tenant_a.id,
        user=tenant_admin_a,
        params={},
    )
    assert "queues_count" in res_queues
    assert isinstance(res_queues["queues"], list)
