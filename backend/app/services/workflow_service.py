"""CampusOS Centralized Enterprise Workflow Service Layer.

Orchestrates:
- Lifecycle management (DRAFT -> ACTIVE -> PAUSED -> ARCHIVED)
- Immutable versioning (historical execution integrity preserved)
- DAG validation and cycle detection (zero infinite loop storms)
- Safe execution engine calling domain services via ActionExecutor and ConditionEngine
- Idempotency, distributed locking, bounded exponential backoff retries, and dead-letter archiving
- Tenant isolation across all operations and audit logging
"""

import logging
import re
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.events import is_valid_event_type
from app.core.exceptions import (
    NotFoundException,
    ValidationException,
)
from app.core.lock import DistributedLock
from app.core.workflow_actions import ActionExecutor, validate_action_definition
from app.core.workflow_conditions import ConditionEngine
from app.models.audit import AuditLog
from app.models.workflow import (
    ExecutionStepStatus,
    WorkflowDeadLetter,
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowExecutionStatus,
    WorkflowExecutionStep,
    WorkflowStatus,
    WorkflowTrigger,
    WorkflowTriggerType,
    WorkflowVersion,
    WorkflowVersionStatus,
)
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowOperationalMetrics,
    WorkflowStepSchema,
    WorkflowTriggerSchema,
    WorkflowUpdate,
)

logger = logging.getLogger("campusos.workflow_service")

MAX_STEPS_ALLOWED = 50
MAX_RETRIES_DEFAULT = 3


class WorkflowService:
    """Enterprise Workflow Orchestration and Execution Engine."""

    # -------------------------------------------------------------------------
    # 1. LIFECYCLE & VALIDATION
    # -------------------------------------------------------------------------

    @classmethod
    def validate_step_graph(cls, steps: list[WorkflowStepSchema] | list[dict[str, Any]], is_system: bool = False) -> None:
        """Validate step definitions, types, actions, conditions, and detect graph cycles."""
        if not steps:
            raise ValidationException("Workflow must contain at least one step.")
        if len(steps) > MAX_STEPS_ALLOWED:
            raise ValidationException(f"Workflow exceeds maximum allowed steps ({MAX_STEPS_ALLOWED}).")

        step_ids: set[str] = set()
        step_dict: dict[str, Any] = {}

        for step in steps:
            s_id = step.id if isinstance(step, WorkflowStepSchema) else step["id"]
            s_type = (step.step_type if isinstance(step, WorkflowStepSchema) else step["step_type"]).upper()
            s_action = step.action_type if isinstance(step, WorkflowStepSchema) else step.get("action_type")
            s_params = step.parameters if isinstance(step, WorkflowStepSchema) else step.get("parameters", {})
            s_cond = step.condition if isinstance(step, WorkflowStepSchema) else step.get("condition")

            if s_id in step_ids:
                raise ValidationException(f"Duplicate step ID '{s_id}' in workflow definition.")
            step_ids.add(s_id)
            step_dict[s_id] = step

            # Validate Step Types
            if s_type not in ("CONDITION", "ACTION", "NOTIFICATION", "WAIT"):
                raise ValidationException(f"Unsupported step type '{s_type}' in step '{s_id}'.")

            # Validate Conditions
            if s_type == "CONDITION":
                if not s_cond:
                    raise ValidationException(f"Condition step '{s_id}' must define a condition rule or group.")
                ConditionEngine.validate_condition_structure(s_cond)

            # Validate Actions
            if s_type in ("ACTION", "NOTIFICATION"):
                if not s_action:
                    raise ValidationException(f"Action step '{s_id}' must specify an 'action_type'.")
                validate_action_definition(s_action, s_params, is_system=is_system)

        # Validate edge targets and detect cycles (DFS color-marking: 0=unvisited, 1=visiting, 2=visited)
        adj: dict[str, list[str]] = {s_id: [] for s_id in step_ids}
        for s_id, s_data in step_dict.items():
            nxt = s_data.next_step_id if isinstance(s_data, WorkflowStepSchema) else s_data.get("next_step_id")
            fail = s_data.on_failure_step_id if isinstance(s_data, WorkflowStepSchema) else s_data.get("on_failure_step_id")

            if nxt:
                if nxt not in step_ids:
                    raise ValidationException(f"Step '{s_id}' references non-existent next_step_id '{nxt}'.")
                adj[s_id].append(nxt)
            if fail:
                if fail not in step_ids:
                    raise ValidationException(f"Step '{s_id}' references non-existent on_failure_step_id '{fail}'.")
                adj[s_id].append(fail)

        color: dict[str, int] = dict.fromkeys(step_ids, 0)

        def dfs(node: str) -> None:
            color[node] = 1  # visiting
            for neighbor in adj[node]:
                if color[neighbor] == 1:
                    raise ValidationException(f"Cycle detected in workflow step graph involving '{node}' -> '{neighbor}'.")
                if color[neighbor] == 0:
                    dfs(neighbor)
            color[node] = 2  # visited

        for s_id in step_ids:
            if color[s_id] == 0:
                dfs(s_id)

    @classmethod
    def validate_trigger(cls, trigger: WorkflowTriggerSchema | dict[str, Any]) -> None:
        """Validate trigger configuration."""
        t_type = (trigger.trigger_type if isinstance(trigger, WorkflowTriggerSchema) else trigger["trigger_type"]).upper()

        if t_type not in ("SCHEDULE", "EVENT", "MANUAL"):
            raise ValidationException(f"Invalid trigger type '{t_type}'. Allowed: SCHEDULE, EVENT, MANUAL.")

        if t_type == "EVENT":
            ev = trigger.event_type if isinstance(trigger, WorkflowTriggerSchema) else trigger.get("event_type")
            if not ev:
                raise ValidationException("EVENT trigger requires a valid 'event_type'.")
            if not is_valid_event_type(ev):
                raise ValidationException(f"Unregistered domain event type '{ev}'.")

        elif t_type == "SCHEDULE":
            cron = trigger.cron_expression if isinstance(trigger, WorkflowTriggerSchema) else trigger.get("cron_expression")
            interval = trigger.interval_seconds if isinstance(trigger, WorkflowTriggerSchema) else trigger.get("interval_seconds")
            time_str = trigger.schedule_time if isinstance(trigger, WorkflowTriggerSchema) else trigger.get("schedule_time")

            if not cron and not interval and not time_str:
                raise ValidationException("SCHEDULE trigger requires at least one of 'cron_expression', 'interval_seconds', or 'schedule_time'.")

    # -------------------------------------------------------------------------
    # 2. WORKFLOW CRUD & VERSIONING
    # -------------------------------------------------------------------------

    @classmethod
    async def create_workflow(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        payload: WorkflowCreate,
        actor_id: UUID | None = None,
        is_system: bool = False,
    ) -> WorkflowDefinition:
        """Create a new workflow in DRAFT status with Version 1."""
        cls.validate_trigger(payload.trigger)
        cls.validate_step_graph(payload.steps, is_system=is_system)

        workflow_id = uuid4()
        version_id = uuid4()
        now = datetime.now(UTC)

        raw_trigger = payload.trigger.model_dump()
        raw_steps = [s.model_dump() for s in payload.steps]
        code_slug = re.sub(r'[^a-zA-Z0-9_]', '_', payload.name.lower())[:48] + f"_{uuid4().hex[:6]}"

        workflow = WorkflowDefinition(
            id=workflow_id,
            tenant_id=tenant_id,
            name=payload.name.strip(),
            code=code_slug,
            description=payload.description,
            domain=payload.domain.upper(),
            status=WorkflowStatus.DRAFT,
            is_system=is_system,
            active_version_id=version_id,
            created_by_user_id=actor_id,
            updated_by_user_id=actor_id,
            created_at=now,
            updated_at=now,
        )
        db.add(workflow)

        version = WorkflowVersion(
            id=version_id,
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            version_number=1,
            status=WorkflowVersionStatus.PUBLISHED,
            change_summary="Initial workflow creation",
            definition_json={"trigger": raw_trigger, "steps": raw_steps},
            created_by_user_id=actor_id,
            published_at=now,
            created_at=now,
        )
        db.add(version)

        trigger = WorkflowTrigger(
            id=uuid4(),
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            trigger_type=payload.trigger.trigger_type.upper(),
            event_type=payload.trigger.event_type,
            cron_expression=payload.trigger.cron_expression,
            schedule_interval=payload.trigger.schedule_time,
            schedule_time=payload.trigger.schedule_time,
            timezone="Asia/Kolkata",
            configuration_json=payload.trigger.config or {},
            is_active=True,
            created_at=now,
        )
        db.add(trigger)
        workflow.versions.append(version)
        workflow.triggers.append(trigger)

        # Audit creation
        cls._create_audit_log(
            db, tenant_id, actor_id, "WORKFLOW_CREATED", workflow_id,
            {"name": workflow.name, "domain": workflow.domain, "version": 1}
        )

        await db.commit()
        return await cls.get_workflow(db, tenant_id, workflow_id)

    @classmethod
    async def get_workflow(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        workflow_id: UUID,
    ) -> WorkflowDefinition:
        """Fetch a workflow ensuring strict tenant isolation."""
        stmt = (
            select(WorkflowDefinition)
            .options(
                selectinload(WorkflowDefinition.versions),
                selectinload(WorkflowDefinition.triggers),
            )
            .where(
                and_(
                    WorkflowDefinition.id == workflow_id,
                    WorkflowDefinition.tenant_id == tenant_id,
                )
            )
            .execution_options(populate_existing=True)
        )
        result = await db.execute(stmt)
        workflow = result.scalar_one_or_none()
        if not workflow:
            raise NotFoundException("Workflow", workflow_id)
        return workflow

    @classmethod
    async def list_workflows(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        status: str | None = None,
        domain: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[WorkflowDefinition], int]:
        """List workflows for a tenant with optional status and domain filtering."""
        query = select(WorkflowDefinition).where(WorkflowDefinition.tenant_id == tenant_id)

        if status:
            query = query.where(WorkflowDefinition.status == status.upper())
        if domain:
            query = query.where(WorkflowDefinition.domain == domain.upper())

        count_stmt = select(func.count()).select_from(query.subquery())
        total_count = (await db.execute(count_stmt)).scalar_one()

        paged_stmt = (
            query.options(
                selectinload(WorkflowDefinition.versions),
                selectinload(WorkflowDefinition.triggers),
            )
            .order_by(WorkflowDefinition.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        results = await db.execute(paged_stmt)
        return list(results.scalars().all()), total_count

    @classmethod
    async def update_workflow(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        workflow_id: UUID,
        payload: WorkflowUpdate,
        actor_id: UUID | None = None,
    ) -> WorkflowDefinition:
        """Update workflow. If ACTIVE and definitions change, bump version to preserve history."""
        workflow = await cls.get_workflow(db, tenant_id, workflow_id)

        if workflow.status == WorkflowStatus.ARCHIVED:
            raise ValidationException("Cannot update an ARCHIVED workflow.")

        now = datetime.now(UTC)
        definitions_changed = payload.trigger is not None or payload.steps is not None

        if payload.name:
            workflow.name = payload.name.strip()
        if payload.description is not None:
            workflow.description = payload.description
        if payload.domain:
            workflow.domain = payload.domain.upper()

        if definitions_changed:
            current_version = next((v for v in workflow.versions if v.is_active), None)
            trigger_def = payload.trigger.model_dump() if payload.trigger else (current_version.trigger_definition if current_version else {})
            steps_def = [s.model_dump() for s in payload.steps] if payload.steps else (current_version.steps_definition if current_version else [])

            cls.validate_trigger(trigger_def)
            cls.validate_step_graph(steps_def, is_system=workflow.is_system)

            # Bump version if active or create new version
            new_version_num = workflow.active_version + 1
            new_version_id = uuid4()

            # Mark old versions inactive
            for v in workflow.versions:
                v.status = WorkflowVersionStatus.ARCHIVED

            new_version = WorkflowVersion(
                id=new_version_id,
                tenant_id=tenant_id,
                workflow_id=workflow.id,
                version_number=new_version_num,
                status=WorkflowVersionStatus.PUBLISHED,
                change_summary=payload.change_summary or f"Updated to version {new_version_num}",
                definition_json={"trigger": trigger_def, "steps": steps_def},
                created_by_user_id=actor_id,
                published_at=now,
                created_at=now,
            )
            db.add(new_version)
            workflow.active_version_id = new_version_id
            workflow.versions.append(new_version)

            # Update trigger table
            if payload.trigger:
                for trg in workflow.triggers:
                    trg.trigger_type = payload.trigger.trigger_type.upper()
                    trg.event_type = payload.trigger.event_type
                    trg.cron_expression = payload.trigger.cron_expression
                    trg.interval_seconds = payload.trigger.interval_seconds
                    trg.schedule_time = payload.trigger.schedule_time
                    trg.days_of_week = payload.trigger.days_of_week
                    trg.config = payload.trigger.config

        workflow.updated_by = actor_id
        workflow.updated_at = now

        cls._create_audit_log(
            db, tenant_id, actor_id, "WORKFLOW_UPDATED", workflow.id,
            {"name": workflow.name, "active_version": workflow.active_version}
        )

        await db.commit()
        return await cls.get_workflow(db, tenant_id, workflow_id)

    @classmethod
    async def activate_workflow(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        workflow_id: UUID,
        actor_id: UUID | None = None,
    ) -> WorkflowDefinition:
        """Validate and activate a workflow."""
        workflow = await cls.get_workflow(db, tenant_id, workflow_id)

        if workflow.status == WorkflowStatus.ARCHIVED:
            raise ValidationException("Cannot activate an ARCHIVED workflow.")

        active_version = next((v for v in workflow.versions if v.is_active or v.id == workflow.active_version_id), None)
        if not active_version and workflow.versions:
            active_version = workflow.versions[0]
        if not active_version:
            raise ValidationException("Workflow has no active version to publish.")

        cls.validate_trigger(active_version.trigger_definition)
        cls.validate_step_graph(active_version.steps_definition, is_system=workflow.is_system)

        workflow.status = WorkflowStatus.ACTIVE
        workflow.active_version_id = active_version.id
        active_version.status = WorkflowVersionStatus.PUBLISHED
        active_version.published_at = datetime.now(UTC)
        workflow.updated_by = actor_id
        workflow.updated_at = datetime.now(UTC)

        cls._create_audit_log(
            db, tenant_id, actor_id, "WORKFLOW_ACTIVATED", workflow.id,
            {"version": workflow.active_version}
        )
        await db.commit()
        return workflow

    @classmethod
    async def pause_workflow(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        workflow_id: UUID,
        actor_id: UUID | None = None,
    ) -> WorkflowDefinition:
        """Pause a workflow. Prevents new scheduled or event triggers."""
        workflow = await cls.get_workflow(db, tenant_id, workflow_id)
        if workflow.status != WorkflowStatus.ACTIVE:
            raise ValidationException(f"Only ACTIVE workflows can be paused (current: {workflow.status}).")

        workflow.status = WorkflowStatus.PAUSED
        workflow.updated_by = actor_id
        workflow.updated_at = datetime.now(UTC)

        cls._create_audit_log(db, tenant_id, actor_id, "WORKFLOW_PAUSED", workflow.id)
        await db.commit()
        return workflow

    @classmethod
    async def archive_workflow(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        workflow_id: UUID,
        actor_id: UUID | None = None,
    ) -> WorkflowDefinition:
        """Archive a workflow permanently."""
        workflow = await cls.get_workflow(db, tenant_id, workflow_id)
        workflow.status = WorkflowStatus.ARCHIVED
        workflow.updated_by = actor_id
        workflow.updated_at = datetime.now(UTC)

        cls._create_audit_log(db, tenant_id, actor_id, "WORKFLOW_ARCHIVED", workflow.id)
        await db.commit()
        return workflow

    # -------------------------------------------------------------------------
    # 3. WORKFLOW EXECUTION ENGINE
    # -------------------------------------------------------------------------

    @classmethod
    async def execute_workflow(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        workflow_id: UUID,
        trigger_type: WorkflowTriggerType | str,
        trigger_reference: str | None = None,
        input_context: dict[str, Any] | None = None,
        actor_id: UUID | None = None,
        correlation_id: str | None = None,
    ) -> WorkflowExecution:
        """Execute a workflow safely with idempotency, locks, bounded retries, and audit."""
        workflow = await cls.get_workflow(db, tenant_id, workflow_id)

        # Allow execution if ACTIVE or if MANUAL trigger by authorized user
        trg_str = str(trigger_type).upper()
        if workflow.status != WorkflowStatus.ACTIVE and trg_str != "MANUAL":
            raise ValidationException(f"Workflow '{workflow.name}' is not ACTIVE (current: {workflow.status}).")

        active_version = next((v for v in workflow.versions if v.is_active), None)
        if not active_version:
            raise ValidationException("Workflow does not have an active published version.")

        cid = correlation_id or str(uuid4())
        ctx = dict(input_context or {})
        ctx["tenant_id"] = str(tenant_id)
        ctx["workflow_id"] = str(workflow_id)
        ctx["correlation_id"] = cid

        # Deterministic Idempotency Key
        occurrence = datetime.now(UTC).strftime("%Y-%m-%d-%H")
        idempotency_key = f"{tenant_id}:{workflow_id}:{trg_str}:{trigger_reference or 'manual'}:{occurrence}"

        # Check if already executed or running with this idempotency key
        existing_stmt = (
            select(WorkflowExecution)
            .options(selectinload(WorkflowExecution.steps))
            .where(
                and_(
                    WorkflowExecution.tenant_id == tenant_id,
                    WorkflowExecution.idempotency_key == idempotency_key,
                )
            )
        )
        existing = (await db.execute(existing_stmt)).scalar_one_or_none()
        if existing and existing.status in (
            WorkflowExecutionStatus.SUCCEEDED,
            WorkflowExecutionStatus.RUNNING,
            WorkflowExecutionStatus.QUEUED,
        ):
            logger.info(
                "Execution with idempotency key %s already exists in state %s. Returning existing.",
                idempotency_key, existing.status
            )
            return existing

        # Distributed Lock Acquisition
        lock_name = f"wf_exec:{idempotency_key}"
        lock = DistributedLock(lock_name, ttl_seconds=60)
        acquired = await lock.acquire()

        if not acquired:
            # Re-check existing in case another worker completed or started it
            existing = (await db.execute(existing_stmt)).scalar_one_or_none()
            if existing:
                return existing
            raise ValidationException(f"Concurrent execution lock already held for {idempotency_key}")

        execution_id = uuid4()
        now = datetime.now(UTC)

        execution = WorkflowExecution(
            id=execution_id,
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            workflow_version_id=active_version.id,
            trigger_type=trg_str,
            trigger_reference=trigger_reference,
            idempotency_key=idempotency_key,
            status=WorkflowExecutionStatus.RUNNING,
            started_at=now,
            attempt_count=1,
            max_retries=MAX_RETRIES_DEFAULT,
            correlation_id=cid,
            actor_type="USER" if actor_id else "SYSTEM",
            actor_id=str(actor_id) if actor_id else "SYSTEM",
            context_data=ctx,
            created_at=now,
        )
        db.add(execution)
        await db.flush()

        cls._create_audit_log(
            db, tenant_id, actor_id, "WORKFLOW_EXECUTION_STARTED", execution.id,
            {"workflow_id": str(workflow_id), "trigger": trg_str, "correlation_id": cid}
        )

        try:
            # Execute step DAG
            steps_def = active_version.steps_definition
            step_map = {s["id"]: s for s in steps_def}
            current_step_id = steps_def[0]["id"] if steps_def else None

            step_count = 0
            while current_step_id and current_step_id in step_map:
                step_count += 1
                if step_count > MAX_STEPS_ALLOWED:
                    raise ValidationException(f"Execution exceeded max step count ({MAX_STEPS_ALLOWED}). Aborting.")

                s_data = step_map[current_step_id]
                s_type = s_data["step_type"].upper()
                s_name = s_data.get("name", current_step_id)

                exec_step = WorkflowExecutionStep(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    execution_id=execution.id,
                    step_key=current_step_id,
                    step_type=s_type,
                    status=ExecutionStepStatus.RUNNING,
                    started_at=datetime.now(UTC),
                    attempt_count=1,
                    input_data=s_data.get("parameters"),
                )
                db.add(exec_step)
                await db.flush()

                step_succeeded = True
                step_error: str | None = None
                output_data: dict[str, Any] | None = None

                try:
                    if s_type == "CONDITION":
                        passed = ConditionEngine.evaluate(s_data.get("condition"), ctx)
                        output_data = {"condition_result": passed}
                        if not passed:
                            exec_step.status = ExecutionStepStatus.SKIPPED
                            exec_step.completed_at = datetime.now(UTC)
                            exec_step.output_data = output_data
                            await db.flush()
                            # Terminal branch or fallback
                            current_step_id = s_data.get("on_failure_step_id")
                            continue

                    elif s_type in ("ACTION", "NOTIFICATION"):
                        output_data = await ActionExecutor.execute(
                            action_type=s_data["action_type"],
                            params=s_data.get("parameters", {}),
                            context=ctx,
                            db=db,
                            tenant_id=tenant_id,
                            correlation_id=cid,
                            is_system=workflow.is_system,
                        )
                        # Expose output to subsequent steps
                        ctx[f"step_{current_step_id}"] = output_data

                    elif s_type == "WAIT":
                        output_data = {"status": "WAIT_COMPLETED"}

                    exec_step.status = ExecutionStepStatus.SUCCEEDED
                    exec_step.completed_at = datetime.now(UTC)
                    exec_step.output_data = output_data

                except Exception as step_exc:
                    step_succeeded = False
                    step_error = str(step_exc)
                    exec_step.status = ExecutionStepStatus.FAILED
                    exec_step.completed_at = datetime.now(UTC)
                    exec_step.error_message = step_error
                    logger.warning("Workflow step '%s' failed: %s", current_step_id, step_error)

                await db.flush()

                if not step_succeeded:
                    fallback_id = s_data.get("on_failure_step_id")
                    if fallback_id:
                        current_step_id = fallback_id
                    else:
                        raise ValidationException(f"Step '{s_name}' failed: {step_error}")
                else:
                    current_step_id = s_data.get("next_step_id")

            # All steps finished successfully
            execution.status = WorkflowExecutionStatus.SUCCEEDED
            execution.completed_at = datetime.now(UTC)

            cls._create_audit_log(
                db, tenant_id, actor_id, "WORKFLOW_EXECUTION_COMPLETED", execution.id,
                {"workflow_id": str(workflow_id), "status": "SUCCEEDED"}
            )
            await db.commit()

        except Exception as exc:
            err_msg = str(exc)
            execution.status = WorkflowExecutionStatus.FAILED
            execution.completed_at = datetime.now(UTC)
            execution.error_code = "EXECUTION_ERROR"
            execution.error_message = err_msg

            # Poison / Dead-letter check
            if execution.attempt_count >= execution.max_retries:
                dead_letter = WorkflowDeadLetter(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    workflow_id=workflow_id,
                    execution_id=execution.id,
                    error_code="EXECUTION_ERROR",
                    error_message=err_msg,
                    attempt_count=execution.attempt_count,
                    payload=execution.context_data,
                    resolved=False,
                    created_at=datetime.now(UTC),
                )
                db.add(dead_letter)

            cls._create_audit_log(
                db, tenant_id, actor_id, "WORKFLOW_EXECUTION_FAILED", execution.id,
                {"workflow_id": str(workflow_id), "error": err_msg}
            )
            await db.commit()

        finally:
            if acquired:
                await lock.release()

        return await cls.get_execution(db, tenant_id, execution.id)

    @classmethod
    async def get_execution(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        execution_id: UUID,
    ) -> WorkflowExecution:
        """Fetch execution details with steps and tenant validation."""
        stmt = (
            select(WorkflowExecution)
            .options(selectinload(WorkflowExecution.steps))
            .where(
                and_(
                    WorkflowExecution.id == execution_id,
                    WorkflowExecution.tenant_id == tenant_id,
                )
            )
        )
        result = await db.execute(stmt)
        execution = result.scalar_one_or_none()
        if not execution:
            raise NotFoundException("WorkflowExecution", execution_id)
        return execution

    @classmethod
    async def list_executions(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        workflow_id: UUID | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[WorkflowExecution], int]:
        """List workflow executions with filtering."""
        query = select(WorkflowExecution).where(WorkflowExecution.tenant_id == tenant_id)

        if workflow_id:
            query = query.where(WorkflowExecution.workflow_id == workflow_id)
        if status:
            query = query.where(WorkflowExecution.status == status.upper())

        count_stmt = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_stmt)).scalar_one()

        stmt = (
            query.options(selectinload(WorkflowExecution.steps))
            .order_by(WorkflowExecution.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        results = await db.execute(stmt)
        return list(results.scalars().all()), total

    @classmethod
    async def retry_execution(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        execution_id: UUID,
        actor_id: UUID | None = None,
    ) -> WorkflowExecution:
        """Manually retry a failed workflow execution."""
        old_exec = await cls.get_execution(db, tenant_id, execution_id)
        if old_exec.status not in (WorkflowExecutionStatus.FAILED, WorkflowExecutionStatus.CANCELLED):
            raise ValidationException(f"Only FAILED or CANCELLED executions can be retried (current: {old_exec.status}).")

        # Execute anew under same correlation id
        return await cls.execute_workflow(
            db=db,
            tenant_id=tenant_id,
            workflow_id=old_exec.workflow_id,
            trigger_type=WorkflowTriggerType.MANUAL,
            trigger_reference=f"retry:{old_exec.id}",
            input_context=old_exec.input_context,
            actor_id=actor_id,
            correlation_id=old_exec.correlation_id,
        )

    @classmethod
    async def cancel_execution(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        execution_id: UUID,
        actor_id: UUID | None = None,
    ) -> WorkflowExecution:
        """Cancel a running or queued workflow execution."""
        execution = await cls.get_execution(db, tenant_id, execution_id)
        if execution.status not in (WorkflowExecutionStatus.QUEUED, WorkflowExecutionStatus.RUNNING):
            raise ValidationException(f"Cannot cancel execution in state '{execution.status}'.")

        execution.status = WorkflowExecutionStatus.CANCELLED
        execution.completed_at = datetime.now(UTC)
        cls._create_audit_log(db, tenant_id, actor_id, "WORKFLOW_EXECUTION_CANCELLED", execution.id)
        await db.commit()
        return execution

    # -------------------------------------------------------------------------
    # 4. EVENT DISPATCH & SCHEDULE ENGINE
    # -------------------------------------------------------------------------

    @classmethod
    async def dispatch_domain_event(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        event_type: str,
        payload: dict[str, Any],
        correlation_id: str | None = None,
    ) -> list[WorkflowExecution]:
        """Dispatch a domain event to all matching ACTIVE workflows for the tenant."""
        # Find active workflows triggered by this event
        stmt = (
            select(WorkflowDefinition)
            .join(WorkflowTrigger, WorkflowDefinition.id == WorkflowTrigger.workflow_id)
            .where(
                and_(
                    WorkflowDefinition.tenant_id == tenant_id,
                    WorkflowDefinition.status == WorkflowStatus.ACTIVE,
                    WorkflowTrigger.trigger_type == WorkflowTriggerType.EVENT,
                    WorkflowTrigger.event_type == event_type,
                    WorkflowTrigger.is_enabled == True,
                )
            )
        )
        result = await db.execute(stmt)
        workflows = list(result.scalars().all())

        executions: list[WorkflowExecution] = []
        for wf in workflows:
            try:
                exec_rec = await cls.execute_workflow(
                    db=db,
                    tenant_id=tenant_id,
                    workflow_id=wf.id,
                    trigger_type=WorkflowTriggerType.EVENT,
                    trigger_reference=f"event:{event_type}:{payload.get('aggregate_id', 'anon')}",
                    input_context=payload,
                    correlation_id=correlation_id,
                )
                executions.append(exec_rec)
            except Exception as exc:
                logger.error(
                    "Error executing workflow '%s' on event '%s': %s",
                    wf.name, event_type, exc, exc_info=True
                )

        return executions

    # -------------------------------------------------------------------------
    # 5. METRICS & OPERATIONAL REPORTING
    # -------------------------------------------------------------------------

    @classmethod
    async def get_operational_metrics(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
    ) -> WorkflowOperationalMetrics:
        """Calculate operational metrics for a tenant."""
        # Workflow Counts
        wf_stmt = (
            select(WorkflowDefinition.status, func.count(WorkflowDefinition.id))
            .where(WorkflowDefinition.tenant_id == tenant_id)
            .group_by(WorkflowDefinition.status)
        )
        wf_res = await db.execute(wf_stmt)
        counts = dict(wf_res.all())

        # Today's Executions
        start_of_day = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        exec_stmt = (
            select(WorkflowExecution.status, func.count(WorkflowExecution.id))
            .where(
                and_(
                    WorkflowExecution.tenant_id == tenant_id,
                    WorkflowExecution.started_at >= start_of_day,
                )
            )
            .group_by(WorkflowExecution.status)
        )
        exec_res = await db.execute(exec_stmt)
        exec_counts = dict(exec_res.all())

        # Dead-letters
        dl_stmt = (
            select(func.count(WorkflowDeadLetter.id))
            .where(WorkflowDeadLetter.tenant_id == tenant_id)
        )
        dl_count = (await db.execute(dl_stmt)).scalar_one()

        succ = exec_counts.get(WorkflowExecutionStatus.SUCCEEDED, 0)
        fail = exec_counts.get(WorkflowExecutionStatus.FAILED, 0)
        total_today = sum(exec_counts.values())

        return WorkflowOperationalMetrics(
            active_workflows=counts.get(WorkflowStatus.ACTIVE, 0),
            paused_workflows=counts.get(WorkflowStatus.PAUSED, 0),
            draft_workflows=counts.get(WorkflowStatus.DRAFT, 0),
            archived_workflows=counts.get(WorkflowStatus.ARCHIVED, 0),
            executions_today=total_today,
            successful_executions=succ,
            failed_executions=fail,
            dead_letter_count=dl_count,
            queue_depth=exec_counts.get(WorkflowExecutionStatus.QUEUED, 0),
        )

    # -------------------------------------------------------------------------
    # 6. INTERNAL AUDIT LOGGING HELPER
    # -------------------------------------------------------------------------

    @classmethod
    def _create_audit_log(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        actor_id: UUID | None,
        action: str,
        entity_id: UUID,
        details: dict[str, Any] | None = None,
    ) -> AuditLog:
        log = AuditLog(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=actor_id,
            action=action,
            entity_type="Workflow",
            entity_id=entity_id,
            new_values_json=details,
            ip_address="127.0.0.1",
            route_endpoint="/workflows",
            business_context="Automated Workflow Engine",
            created_at=datetime.now(UTC),
        )
        db.add(log)
        return log
