"""Enterprise Human Task Orchestration and Decision Service (Step 25)."""

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditEventCategory, build_audit_entry
from app.core.exceptions import (
    DelegationInvalidException,
    NotFoundException,
    TaskAlreadyClaimedException,
    TaskAlreadyCompletedException,
    TaskAssignmentException,
    TaskNotClaimedException,
    TaskNotFoundException,
)
from app.models.case_management import (
    CaseTimelineEventType,
    HumanDecision,
    HumanTask,
    TaskDecision,
    TaskDelegation,
    TaskStatus,
)
from app.repositories.case_repository import CaseRepository
from app.schemas.case_management import (
    TaskCompleteRequest,
    TaskCreate,
    TaskDelegationCreate,
    TaskReassignRequest,
)

logger = logging.getLogger("campusos.task_service")


class TaskService:
    """Service managing Human Tasks, Exclusive Claims, Decisions, and Delegations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CaseRepository(db)

    # -------------------------------------------------------------------------
    # 1. TASK CRUD OPERATIONS
    # -------------------------------------------------------------------------

    async def create_task(
        self, tenant_id: UUID, dto: TaskCreate, actor_id: UUID | None = None
    ) -> HumanTask:
        case = await self.repo.get_case_by_id(tenant_id, dto.case_id)
        if not case:
            raise NotFoundException("Case", dto.case_id)

        task = HumanTask(
            tenant_id=tenant_id,
            case_id=dto.case_id,
            workflow_execution_id=dto.workflow_execution_id or case.workflow_execution_id,
            step_key=dto.step_key,
            title=dto.title,
            description=dto.description,
            task_type=dto.task_type,
            status=TaskStatus.PENDING,
            priority=dto.priority,
            assigned_user_id=dto.assigned_user_id,
            assigned_role=dto.assigned_role,
            assigned_queue_id=dto.assigned_queue_id or case.assigned_queue_id,
            due_at=dto.due_at or case.due_at,
            input_context_json=dto.input_context_json,
        )
        created = await self.repo.create_task(task)

        # Record timeline event
        await self.repo.add_timeline_event(
            tenant_id=tenant_id,
            case_id=dto.case_id,
            task_id=created.id,
            event_type=CaseTimelineEventType.TASK_CREATED,
            actor_id=actor_id,
            title=f"Task created: {created.title}",
            details_json={"task_type": created.task_type, "priority": created.priority},
        )

        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.TASK_CREATED,
            entity_type="human_task",
            entity_id=created.id,
            user_id=actor_id,
            new_values_json={
                "title": created.title,
                "case_id": str(created.case_id),
                "task_type": created.task_type,
            },
            business_context=f"Human task '{created.title}' created.",
        )
        self.db.add(audit)
        await self.db.flush()

        # Initialize SLA clock for task
        from app.services.sla_service import SlaService

        sla_srv = SlaService(self.db)
        await sla_srv.initialize_task_sla(tenant_id, created)
        await self.db.refresh(created)

        return created

    async def get_task(self, tenant_id: UUID, task_id: UUID, for_update: bool = False) -> HumanTask:
        task = await self.repo.get_task_by_id(tenant_id, task_id, for_update=for_update)
        if not task:
            raise TaskNotFoundException(task_id)
        return task

    async def list_tasks(
        self,
        tenant_id: UUID,
        case_id: UUID | None = None,
        status: str | None = None,
        priority: str | None = None,
        assigned_user_id: UUID | None = None,
        assigned_queue_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[HumanTask], int]:
        return await self.repo.list_tasks(
            tenant_id=tenant_id,
            case_id=case_id,
            status=status,
            priority=priority,
            assigned_user_id=assigned_user_id,
            assigned_queue_id=assigned_queue_id,
            limit=limit,
            offset=offset,
        )

    # -------------------------------------------------------------------------
    # 2. ATOMIC CLAIM & RELEASE (CONCURRENCY PROTECTED)
    # -------------------------------------------------------------------------

    async def claim_task(self, tenant_id: UUID, task_id: UUID, user_id: UUID) -> HumanTask:
        """Atomically claim an exclusive task preventing race conditions."""
        task = await self.repo.claim_task_atomic(tenant_id, task_id, user_id)
        if not task:
            # Inspect existing state to raise precise descriptive exception
            existing = await self.get_task(tenant_id, task_id)
            if existing.status in [TaskStatus.COMPLETED, TaskStatus.REJECTED, TaskStatus.CANCELLED]:
                raise TaskAlreadyCompletedException(task_id, existing.status)
            if existing.assigned_user_id and existing.assigned_user_id != user_id:
                raise TaskAlreadyClaimedException(task_id, existing.assigned_user_id)
            raise TaskAssignmentException(
                f"Task '{task_id}' cannot be claimed in status '{existing.status}'."
            )

        await self.repo.add_timeline_event(
            tenant_id=tenant_id,
            case_id=task.case_id,
            task_id=task.id,
            event_type=CaseTimelineEventType.TASK_CLAIMED,
            actor_id=user_id,
            title=f"Task claimed: {task.title}",
            details_json={"claimed_by": str(user_id)},
        )

        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.TASK_CLAIMED,
            entity_type="human_task",
            entity_id=task.id,
            user_id=user_id,
            new_values_json={"status": TaskStatus.CLAIMED, "assigned_user_id": str(user_id)},
            business_context=f"Task '{task.title}' claimed by user.",
        )
        self.db.add(audit)
        await self.db.flush()
        return task

    async def release_task(
        self, tenant_id: UUID, task_id: UUID, user_id: UUID, reason: str | None = None
    ) -> HumanTask:
        """Atomically release a claimed task back to the pending queue."""
        task = await self.repo.release_task_atomic(tenant_id, task_id, user_id)
        if not task:
            existing = await self.get_task(tenant_id, task_id)
            if existing.status not in [TaskStatus.CLAIMED, TaskStatus.IN_PROGRESS]:
                raise TaskNotClaimedException(task_id)
            if existing.assigned_user_id != user_id:
                raise TaskAssignmentException("Only the user who claimed the task may release it.")
            raise TaskAssignmentException(f"Cannot release task '{task_id}'.")

        await self.repo.add_timeline_event(
            tenant_id=tenant_id,
            case_id=task.case_id,
            task_id=task.id,
            event_type=CaseTimelineEventType.TASK_RELEASED,
            actor_id=user_id,
            title=f"Task released: {task.title}",
            details_json={"reason": reason},
        )

        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.TASK_RELEASED,
            entity_type="human_task",
            entity_id=task.id,
            user_id=user_id,
            new_values_json={"status": TaskStatus.PENDING, "reason": reason},
            business_context=f"Task '{task.title}' released back to queue.",
        )
        self.db.add(audit)
        await self.db.flush()
        return task

    async def reassign_task(
        self, tenant_id: UUID, task_id: UUID, actor_id: UUID, dto: TaskReassignRequest
    ) -> HumanTask:
        task = await self.get_task(tenant_id, task_id, for_update=True)
        if task.status in [TaskStatus.COMPLETED, TaskStatus.REJECTED, TaskStatus.CANCELLED]:
            raise TaskAlreadyCompletedException(task_id, task.status)

        old_user = task.assigned_user_id
        old_queue = task.assigned_queue_id

        if dto.new_user_id is not None:
            task.assigned_user_id = dto.new_user_id
            task.status = TaskStatus.CLAIMED
        elif dto.new_queue_id is not None:
            task.assigned_queue_id = dto.new_queue_id
            task.assigned_user_id = None
            task.status = TaskStatus.PENDING

        await self.repo.update_task(task)

        await self.repo.add_timeline_event(
            tenant_id=tenant_id,
            case_id=task.case_id,
            task_id=task.id,
            event_type=CaseTimelineEventType.TASK_ASSIGNED,
            actor_id=actor_id,
            title=f"Task reassigned: {dto.reason}",
            details_json={
                "old_user": str(old_user) if old_user else None,
                "new_user": str(dto.new_user_id) if dto.new_user_id else None,
                "old_queue": str(old_queue) if old_queue else None,
                "new_queue": str(dto.new_queue_id) if dto.new_queue_id else None,
                "reason": dto.reason,
            },
        )

        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.TASK_REASSIGNED,
            entity_type="human_task",
            entity_id=task.id,
            user_id=actor_id,
            new_values_json={
                "assigned_user_id": str(task.assigned_user_id) if task.assigned_user_id else None,
                "assigned_queue_id": str(task.assigned_queue_id)
                if task.assigned_queue_id
                else None,
                "reason": dto.reason,
            },
            business_context=f"Task '{task.title}' reassigned.",
        )
        self.db.add(audit)
        await self.db.flush()
        return task

    # -------------------------------------------------------------------------
    # 3. TASK DECISION & COMPLETION
    # -------------------------------------------------------------------------

    async def complete_task(
        self, tenant_id: UUID, task_id: UUID, actor_id: UUID, dto: TaskCompleteRequest
    ) -> HumanTask:
        """Record authoritative human decision and complete task atomically."""
        terminal_status = (
            TaskStatus.REJECTED if dto.decision == HumanDecision.REJECT else TaskStatus.COMPLETED
        )

        completed_task = await self.repo.complete_task_atomic(
            tenant_id=tenant_id,
            task_id=task_id,
            user_id=actor_id,
            status=terminal_status,
            output_result=dto.output_result_json,
        )
        if not completed_task:
            existing = await self.get_task(tenant_id, task_id)
            raise TaskAlreadyCompletedException(task_id, existing.status)

        # Record human decision entity
        decision = TaskDecision(
            tenant_id=tenant_id,
            task_id=completed_task.id,
            case_id=completed_task.case_id,
            actor_id=actor_id,
            decision=dto.decision,
            reason=dto.reason,
            notes=dto.notes,
            evidence_reference=dto.evidence_reference,
            resulting_transition=dto.resulting_transition,
            metadata_json=dto.output_result_json,
        )
        await self.repo.record_decision(decision)

        # Record timeline event
        await self.repo.add_timeline_event(
            tenant_id=tenant_id,
            case_id=completed_task.case_id,
            task_id=completed_task.id,
            event_type=CaseTimelineEventType.DECISION_MADE,
            actor_id=actor_id,
            title=f"Decision '{dto.decision}' recorded on task: {completed_task.title}",
            details_json={
                "decision": dto.decision,
                "reason": dto.reason,
                "evidence": dto.evidence_reference,
                "transition": dto.resulting_transition,
            },
        )

        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.TASK_DECISION_RECORDED,
            entity_type="task_decision",
            entity_id=decision.id,
            user_id=actor_id,
            new_values_json={
                "decision": dto.decision,
                "reason": dto.reason,
                "task_id": str(completed_task.id),
            },
            business_context=f"Decision '{dto.decision}' recorded on task.",
        )
        self.db.add(audit)
        await self.db.flush()

        # Mark SLA instance completed if present
        from app.services.sla_service import SlaService

        sla_srv = SlaService(self.db)
        await sla_srv.mark_task_sla_completed(tenant_id, completed_task.id)

        # Bridge decision to workflow execution if linked
        if completed_task.workflow_execution_id and dto.resulting_transition:
            from app.services.case_service import CaseService

            case_srv = CaseService(self.db)
            await case_srv.transition_workflow_instance(
                tenant_id=tenant_id,
                execution_id=completed_task.workflow_execution_id,
                action=dto.decision,
                reason=dto.reason,
                target_step_key=dto.resulting_transition,
                task_id=completed_task.id,
                actor_id=actor_id,
            )

        return completed_task

    # -------------------------------------------------------------------------
    # 4. DELEGATIONS
    # -------------------------------------------------------------------------

    async def create_delegation(
        self, tenant_id: UUID, delegator_id: UUID, dto: TaskDelegationCreate
    ) -> TaskDelegation:
        if dto.valid_until <= dto.valid_from:
            raise DelegationInvalidException("Delegation 'valid_until' must be after 'valid_from'.")
        if delegator_id == dto.delegatee_user_id:
            raise DelegationInvalidException("Cannot delegate authority to oneself.")

        delegation = TaskDelegation(
            tenant_id=tenant_id,
            delegator_user_id=delegator_id,
            delegatee_user_id=dto.delegatee_user_id,
            scope_module=dto.scope_module.upper() if dto.scope_module else None,
            valid_from=dto.valid_from,
            valid_until=dto.valid_until,
            reason=dto.reason,
            is_active=True,
        )
        created = await self.repo.create_delegation(delegation)

        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.DELEGATION_CREATED,
            entity_type="task_delegation",
            entity_id=created.id,
            user_id=delegator_id,
            new_values_json={
                "delegatee_user_id": str(dto.delegatee_user_id),
                "valid_from": dto.valid_from.isoformat(),
                "valid_until": dto.valid_until.isoformat(),
            },
            business_context="Task delegation created.",
        )
        self.db.add(audit)
        await self.db.flush()
        return created

    async def list_delegations(
        self, tenant_id: UUID, user_id: UUID | None = None, is_active: bool | None = None
    ) -> list[TaskDelegation]:
        return await self.repo.list_delegations(tenant_id, user_id=user_id, is_active=is_active)

    async def verify_delegated_access(
        self, tenant_id: UUID, delegator_id: UUID, user_id: UUID, module: str | None = None
    ) -> bool:
        """Check if user_id currently holds valid delegated authority for delegator_id."""
        if delegator_id == user_id:
            return True
        delegation = await self.repo.get_active_delegation(
            tenant_id, delegator_id, user_id, module=module
        )
        return delegation is not None
