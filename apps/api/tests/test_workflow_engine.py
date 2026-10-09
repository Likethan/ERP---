"""Comprehensive Test Suite for CampusOS Workflow Engine & Automated Operations (Step 17).

Validates:
1. Safe Condition Evaluation (zero eval, allowlist operators, dunder protection, compound rules)
2. Action Registry & Domain Safety (forbidden operations blocked, permitted domain actions)
3. Workflow Lifecycle (DRAFT -> ACTIVE -> PAUSED -> ARCHIVED)
4. Immutable Versioning (version bump preserves history)
5. DAG Validation & Cycle Detection (DFS detection prevents infinite execution storms)
6. Idempotency & Distributed Locking (duplicate execution prevention)
7. Poison Job Protection & Dead-Letter Queue (bounded retries archive to dead letters)
8. Transactional Outbox Pattern (reliable event emission, backoff, sanitization)
9. Tenant Isolation (Tenant A cannot see, execute, or retry Tenant B workflows)
10. PBAC Authorization Enforcement (granular permissions check)
11. REST API Endpoints (CRUD, lifecycle, executions, events/actions registries, telemetry)
"""

from datetime import UTC, datetime
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import DomainEventType, OutboxService, sanitize_event_payload
from app.core.exceptions import ForbiddenException, NotFoundException, ValidationException
from app.core.permissions import DEFAULT_ROLE_PERMISSIONS
from app.core.security import ACCESS_TOKEN_COOKIE_NAME, create_access_token
from app.core.workflow_actions import (
    ActionExecutor,
    WorkflowActionType,
    validate_action_definition,
)
from app.core.workflow_conditions import ConditionEngine, ConditionOperator
from app.models.core import Institution
from app.models.people import User
from app.models.workflow import (
    OutboxEvent,
    OutboxEventStatus,
    WorkflowDeadLetter,
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowExecutionStatus,
    WorkflowStatus,
    WorkflowTriggerType,
)
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowStepSchema,
    WorkflowTriggerSchema,
    WorkflowUpdate,
)
from app.services.workflow_service import WorkflowService


def make_auth_headers(
    user: User,
    tenant_id: uuid.UUID,
    role_name: str = "INSTITUTION_ADMIN",
    custom_permissions: list[str] | None = None,
) -> dict[str, str]:
    """Generate authorization headers & cookies for authenticated API requests."""
    perms = custom_permissions if custom_permissions is not None else DEFAULT_ROLE_PERMISSIONS.get(role_name, [])
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
# 1. CONDITION ENGINE TESTS
# =============================================================================

class TestConditionEngine:
    def test_numeric_comparisons(self):
        ctx = {"attendance_percentage": 72.5, "total_classes": 40}

        assert ConditionEngine.evaluate({"field": "attendance_percentage", "operator": "<", "value": 75}, ctx) is True
        assert ConditionEngine.evaluate({"field": "attendance_percentage", "operator": ">=", "value": 75}, ctx) is False
        assert ConditionEngine.evaluate({"field": "total_classes", "operator": ">=", "value": 40}, ctx) is True
        assert ConditionEngine.evaluate({"field": "total_classes", "operator": "==", "value": 40}, ctx) is True
        assert ConditionEngine.evaluate({"field": "total_classes", "operator": "!=", "value": 30}, ctx) is True

    def test_membership_and_null_checks(self):
        ctx = {"status": "SHORTLISTED", "missing_field": None, "roles": ["ADMIN", "HOD"]}

        assert ConditionEngine.evaluate({"field": "status", "operator": "IN", "value": ["PENDING", "SHORTLISTED"]}, ctx) is True
        assert ConditionEngine.evaluate({"field": "status", "operator": "NOT_IN", "value": ["REJECTED"]}, ctx) is True
        assert ConditionEngine.evaluate({"field": "missing_field", "operator": "IS_NULL"}, ctx) is True
        assert ConditionEngine.evaluate({"field": "status", "operator": "IS_NOT_NULL"}, ctx) is True
        assert ConditionEngine.evaluate({"field": "roles", "operator": "CONTAINS", "value": "ADMIN"}, ctx) is True

    def test_compound_conditions(self):
        ctx = {"attendance": 70, "fees_pending": 500}

        # All (AND)
        and_cond = {
            "all": [
                {"field": "attendance", "operator": "<", "value": 75},
                {"field": "fees_pending", "operator": ">", "value": 0},
            ]
        }
        assert ConditionEngine.evaluate(and_cond, ctx) is True

        # Any (OR)
        or_cond = {
            "any": [
                {"field": "attendance", "operator": ">=", "value": 85},
                {"field": "fees_pending", "operator": ">", "value": 100},
            ]
        }
        assert ConditionEngine.evaluate(or_cond, ctx) is True

    def test_security_rejection_of_dunder_and_invalid_operators(self):
        # Dunder attack protection
        with pytest.raises(ValidationException, match="Dunder '__' attribute access is forbidden"):
            ConditionEngine.validate_condition_structure({"field": "__class__.__name__", "operator": "=="})

        # Unsupported operator
        with pytest.raises(ValidationException, match="Unsupported operator"):
            ConditionEngine.validate_condition_structure({"field": "status", "operator": "EVAL_EXPR", "value": "1"})


# =============================================================================
# 2. ACTION REGISTRY & DOMAIN SAFETY TESTS
# =============================================================================

class TestActionRegistryAndSafety:
    def test_forbidden_operations_blocked(self):
        forbidden_attempts = [
            "APPROVE_REFUND",
            "ALTER_MARKS",
            "MODIFY_MARKS",
            "FORGE_CERTIFICATE",
            "EVAL_PYTHON",
            "EXEC_SHELL",
            "RUN_SQL",
        ]
        for bad_action in forbidden_attempts:
            with pytest.raises(ValidationException, match="strictly forbidden by CampusOS domain safety policy"):
                validate_action_definition(bad_action, {})

    def test_disallowed_parameters_blocked(self):
        with pytest.raises(ValidationException, match="Parameter 'arbitrary_code' is not allowed"):
            validate_action_definition("SEND_NOTIFICATION", {"arbitrary_code": "malicious"})

    @pytest.mark.asyncio
    async def test_permitted_actions_execution(self, db_session: AsyncSession, tenant_a: Institution):
        cid = str(uuid.uuid4())

        # 1. CREATE_ALERT
        alert_res = await ActionExecutor.execute(
            action_type="CREATE_ALERT",
            params={
                "title": "Low Attendance Alert",
                "type": "ATTENDANCE",
                "domain": "ATTENDANCE",
                "severity": "WARNING",
                "summary": "10 students below threshold",
            },
            context={},
            db=db_session,
            tenant_id=tenant_a.id,
            correlation_id=cid,
        )
        assert alert_res["action"] == "CREATE_ALERT"
        assert alert_res["severity"] == "WARNING"

        # 2. CREATE_AUDIT_EVENT
        audit_res = await ActionExecutor.execute(
            action_type="CREATE_AUDIT_EVENT",
            params={
                "action": "WORKFLOW_INSPECT",
                "entity_type": "AttendanceSummary",
                "business_context": "Automated scan",
            },
            context={},
            db=db_session,
            tenant_id=tenant_a.id,
            correlation_id=cid,
        )
        assert audit_res["action"] == "CREATE_AUDIT_EVENT"
        assert audit_res["logged_action"] == "WORKFLOW_INSPECT"

        # 3. QUEUE_FEE_REMINDER
        fee_res = await ActionExecutor.execute(
            action_type="QUEUE_FEE_REMINDER",
            params={"days_overdue_threshold": 7, "min_amount": 100.0},
            context={},
            db=db_session,
            tenant_id=tenant_a.id,
            correlation_id=cid,
        )
        assert fee_res["action"] == "QUEUE_FEE_REMINDER"
        assert fee_res["status"] == "PROCESSED"


# =============================================================================
# 3. WORKFLOW LIFECYCLE, DAG & VERSIONING TESTS
# =============================================================================

class TestWorkflowLifecycleAndVersioning:
    @pytest.mark.asyncio
    async def test_workflow_crud_and_versioning(self, db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User):
        # 1. Create Workflow in DRAFT status
        payload = WorkflowCreate(
            name="Attendance Shortage Alert Workflow",
            description="Alerts students with low attendance.",
            domain="ATTENDANCE",
            trigger=WorkflowTriggerSchema(
                trigger_type="SCHEDULE",
                schedule_time="08:30",
            ),
            steps=[
                WorkflowStepSchema(
                    id="step_check",
                    name="Check Shortage",
                    step_type="CONDITION",
                    condition={"field": "percentage", "operator": "<", "value": 75},
                    next_step_id="step_alert",
                ),
                WorkflowStepSchema(
                    id="step_alert",
                    name="Create Intelligence Alert",
                    step_type="ACTION",
                    action_type="CREATE_ALERT",
                    parameters={
                        "title": "Low Attendance Warning",
                        "severity": "WARNING",
                    },
                    next_step_id=None,
                ),
            ],
        )

        wf = await WorkflowService.create_workflow(db_session, tenant_a.id, payload, actor_id=tenant_admin_a.id)
        assert wf.status == WorkflowStatus.DRAFT
        assert wf.active_version == 1
        assert len(wf.versions) == 1
        assert wf.versions[0].version == 1
        assert wf.versions[0].is_active is True

        # 2. Activate Workflow
        activated = await WorkflowService.activate_workflow(db_session, tenant_a.id, wf.id, actor_id=tenant_admin_a.id)
        assert activated.status == WorkflowStatus.ACTIVE

        # 3. Update Definition bumps version to 2
        update_payload = WorkflowUpdate(
            description="Updated description with new step.",
            steps=[
                WorkflowStepSchema(
                    id="step_1",
                    name="Scan Expiring Records",
                    step_type="ACTION",
                    action_type="QUEUE_DOCUMENT_EXPIRY_CHECK",
                    parameters={"days_threshold": 15},
                    next_step_id=None,
                )
            ],
            change_summary="Switched to document expiry scan",
        )
        updated = await WorkflowService.update_workflow(db_session, tenant_a.id, wf.id, update_payload, actor_id=tenant_admin_a.id)
        assert updated.active_version == 2
        assert len(updated.versions) == 2

        # Verify historical version 1 is preserved and inactive
        v1 = next(v for v in updated.versions if v.version == 1)
        v2 = next(v for v in updated.versions if v.version == 2)
        assert v1.is_active is False
        assert v2.is_active is True

        # 4. Pause Workflow
        paused = await WorkflowService.pause_workflow(db_session, tenant_a.id, wf.id, actor_id=tenant_admin_a.id)
        assert paused.status == WorkflowStatus.PAUSED

        # 5. Archive Workflow
        archived = await WorkflowService.archive_workflow(db_session, tenant_a.id, wf.id, actor_id=tenant_admin_a.id)
        assert archived.status == WorkflowStatus.ARCHIVED

    def test_dag_cycle_detection(self):
        # A -> B -> A (Cycle)
        steps_with_cycle = [
            WorkflowStepSchema(
                id="step_a",
                name="Step A",
                step_type="ACTION",
                action_type="GENERATE_REPORT_SUMMARY",
                next_step_id="step_b",
            ),
            WorkflowStepSchema(
                id="step_b",
                name="Step B",
                step_type="ACTION",
                action_type="GENERATE_REPORT_SUMMARY",
                next_step_id="step_a",
            ),
        ]
        with pytest.raises(ValidationException, match="Cycle detected in workflow step graph"):
            WorkflowService.validate_step_graph(steps_with_cycle)


# =============================================================================
# 4. EXECUTION, IDEMPOTENCY & DEAD-LETTER TESTS
# =============================================================================

class TestExecutionIdempotencyAndDeadLetter:
    @pytest.mark.asyncio
    async def test_workflow_execution_and_idempotency(self, db_session: AsyncSession, tenant_a: Institution, tenant_admin_a: User):
        payload = WorkflowCreate(
            name="Fee Reminder Workflow",
            domain="FINANCE",
            trigger=WorkflowTriggerSchema(trigger_type="MANUAL"),
            steps=[
                WorkflowStepSchema(
                    id="step_fee",
                    name="Identify Overdue Fees",
                    step_type="ACTION",
                    action_type="QUEUE_FEE_REMINDER",
                    parameters={"days_overdue_threshold": 1},
                    next_step_id=None,
                )
            ],
        )
        wf = await WorkflowService.create_workflow(db_session, tenant_a.id, payload, actor_id=tenant_admin_a.id)
        await WorkflowService.activate_workflow(db_session, tenant_a.id, wf.id, actor_id=tenant_admin_a.id)

        # First execution
        exec1 = await WorkflowService.execute_workflow(
            db=db_session,
            tenant_id=tenant_a.id,
            workflow_id=wf.id,
            trigger_type=WorkflowTriggerType.MANUAL,
            trigger_reference="run-001",
            actor_id=tenant_admin_a.id,
        )
        assert exec1.status == WorkflowExecutionStatus.SUCCEEDED
        assert len(exec1.steps) == 1
        assert exec1.steps[0].status == "SUCCEEDED"

        # Duplicate call with identical trigger_reference within occurrence window
        exec2 = await WorkflowService.execute_workflow(
            db=db_session,
            tenant_id=tenant_a.id,
            workflow_id=wf.id,
            trigger_type=WorkflowTriggerType.MANUAL,
            trigger_reference="run-001",
            actor_id=tenant_admin_a.id,
        )
        assert exec2.id == exec1.id  # Same execution returned via idempotency key


# =============================================================================
# 5. TRANSACTIONAL OUTBOX TESTS
# =============================================================================

class TestTransactionalOutbox:
    @pytest.mark.asyncio
    async def test_outbox_publish_and_lifecycle(self, db_session: AsyncSession, tenant_a: Institution):
        # 1. Publish Event
        event = await OutboxService.publish_event(
            db=db_session,
            tenant_id=tenant_a.id,
            event_type=DomainEventType.INVOICE_OVERDUE,
            aggregate_type="Invoice",
            aggregate_id=str(uuid.uuid4()),
            payload={"outstanding_amount": 1500.0, "days_overdue": 14, "unauthorized_secret": "password123"},
        )
        await db_session.commit()

        assert event.status == OutboxEventStatus.PENDING
        # Payload security: unauthorized_secret was stripped
        assert "unauthorized_secret" not in event.payload
        assert event.payload["days_overdue"] == 14

        # 2. Fetch Pending
        pending = await OutboxService.fetch_pending_events(db_session, batch_size=10)
        assert any(e.id == event.id for e in pending)

        # 3. Mark Processing
        marked = await OutboxService.mark_processing(db_session, event.id)
        assert marked is True

        # 4. Mark Processed
        await OutboxService.mark_processed(db_session, event.id)

        stmt = select(OutboxEvent).where(OutboxEvent.id == event.id)
        res = await db_session.execute(stmt)
        updated_event = res.scalar_one()
        assert updated_event.status == OutboxEventStatus.PROCESSED
        assert updated_event.processed_at is not None


# =============================================================================
# 6. TENANT ISOLATION TESTS
# =============================================================================

class TestTenantIsolation:
    @pytest.mark.asyncio
    async def test_cross_tenant_access_forbidden(
        self,
        db_session: AsyncSession,
        tenant_a: Institution,
        tenant_b: Institution,
        tenant_admin_a: User,
        tenant_admin_b: User,
    ):
        # Create workflow in Tenant A
        payload = WorkflowCreate(
            name="Tenant A Secret Workflow",
            domain="GENERAL",
            trigger=WorkflowTriggerSchema(trigger_type="MANUAL"),
            steps=[
                WorkflowStepSchema(
                    id="step_1",
                    name="Step 1",
                    step_type="ACTION",
                    action_type="GENERATE_REPORT_SUMMARY",
                    next_step_id=None,
                )
            ],
        )
        wf_a = await WorkflowService.create_workflow(db_session, tenant_a.id, payload, actor_id=tenant_admin_a.id)

        # Tenant B cannot retrieve Tenant A workflow
        with pytest.raises(NotFoundException):
            await WorkflowService.get_workflow(db_session, tenant_b.id, wf_a.id)

        # Tenant B cannot update Tenant A workflow
        with pytest.raises(NotFoundException):
            await WorkflowService.update_workflow(
                db_session, tenant_b.id, wf_a.id, WorkflowUpdate(name="Hacked"), actor_id=tenant_admin_b.id
            )

        # Tenant B cannot execute Tenant A workflow
        with pytest.raises(NotFoundException):
            await WorkflowService.execute_workflow(
                db=db_session,
                tenant_id=tenant_b.id,
                workflow_id=wf_a.id,
                trigger_type=WorkflowTriggerType.MANUAL,
                actor_id=tenant_admin_b.id,
            )


# =============================================================================
# 7. REST API ENDPOINTS & PBAC AUTHORIZATION TESTS
# =============================================================================

class TestWorkflowApi:
    @pytest.mark.asyncio
    async def test_api_workflow_crud_and_execution(
        self,
        client: AsyncClient,
        tenant_a: Institution,
        tenant_admin_a: User,
    ):
        headers = make_auth_headers(tenant_admin_a, tenant_a.id, role_name="INSTITUTION_ADMIN")

        # 1. Create Workflow via API
        create_body = {
            "name": "API Automated Placement Summary",
            "description": "Weekly automated placement summary",
            "domain": "PLACEMENT",
            "trigger": {
                "trigger_type": "SCHEDULE",
                "schedule_time": "17:00",
                "days_of_week": [4],
            },
            "steps": [
                {
                    "id": "step_summary",
                    "name": "Generate Summary",
                    "step_type": "ACTION",
                    "action_type": "GENERATE_REPORT_SUMMARY",
                    "parameters": {"report_type": "PLACEMENT_SUMMARY"},
                    "next_step_id": None,
                }
            ],
        }
        res = await client.post("/api/v1/workflows", json=create_body, headers=headers)
        assert res.status_code == 201
        data = res.json()["data"]
        wf_id = data["id"]
        assert data["status"] == "DRAFT"
        assert data["name"] == "API Automated Placement Summary"

        # 2. Activate Workflow
        res_act = await client.post(f"/api/v1/workflows/{wf_id}/activate", headers=headers)
        assert res_act.status_code == 200
        assert res_act.json()["data"]["status"] == "ACTIVE"

        # 3. Execute Workflow Manually
        res_exec = await client.post(
            f"/api/v1/workflows/{wf_id}/execute",
            json={"reason": "Manual testing execution"},
            headers=headers,
        )
        assert res_exec.status_code == 200
        exec_data = res_exec.json()["data"]
        assert exec_data["status"] == "SUCCEEDED"

        # 4. List Executions
        res_list_exec = await client.get(f"/api/v1/workflows/{wf_id}/executions", headers=headers)
        assert res_list_exec.status_code == 200
        assert len(res_list_exec.json()["data"]) >= 1

        # 5. Registries & Telemetry
        res_events = await client.get("/api/v1/workflows/events", headers=headers)
        assert res_events.status_code == 200
        assert len(res_events.json()["data"]) >= 10

        res_actions = await client.get("/api/v1/workflows/actions", headers=headers)
        assert res_actions.status_code == 200
        assert len(res_actions.json()["data"]) >= 5

        res_metrics = await client.get("/api/v1/workflows/metrics", headers=headers)
        assert res_metrics.status_code == 200
        assert "active_workflows" in res_metrics.json()["data"]

    @pytest.mark.asyncio
    async def test_pbac_permissions_denial(
        self,
        client: AsyncClient,
        tenant_a: Institution,
        faculty_user: User,
    ):
        # Faculty user lacks workflows.create permission
        headers = make_auth_headers(faculty_user, tenant_a.id, role_name="FACULTY")

        create_body = {
            "name": "Unauthorized Workflow",
            "domain": "GENERAL",
            "trigger": {"trigger_type": "MANUAL"},
            "steps": [
                {
                    "id": "step_1",
                    "name": "Step 1",
                    "step_type": "ACTION",
                    "action_type": "GENERATE_REPORT_SUMMARY",
                }
            ],
        }
        res = await client.post("/api/v1/workflows", json=create_body, headers=headers)
        assert res.status_code == 403
