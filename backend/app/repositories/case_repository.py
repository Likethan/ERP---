"""Persistence Repository Layer for Enterprise Workflow, Case Management & HITL Operations.

Step 25 implementation.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.case_management import (
    Case,
    CaseAttachment,
    CaseComment,
    CaseRelationship,
    CaseStatus,
    CaseTimelineEvent,
    CaseType,
    HumanTask,
    QueueMember,
    SlaInstance,
    SlaPolicy,
    SlaStatus,
    TaskDecision,
    TaskDelegation,
    TaskStatus,
    WorkQueue,
)


class CaseRepository:
    """Repository handling persistence for Cases, Tasks, Queues, SLA, and HITL operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # -------------------------------------------------------------------------
    # 1. CASE TYPES
    # -------------------------------------------------------------------------

    async def get_case_type_by_id(
        self, tenant_id: UUID | None, case_type_id: UUID
    ) -> CaseType | None:
        stmt = select(CaseType).where(
            CaseType.id == case_type_id,
            CaseType.deleted_at.is_(None),
            or_(CaseType.tenant_id == tenant_id, CaseType.tenant_id.is_(None)),
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_case_type_by_code(self, tenant_id: UUID | None, code: str) -> CaseType | None:
        stmt = (
            select(CaseType)
            .where(
                CaseType.code == code.upper(),
                CaseType.deleted_at.is_(None),
                or_(CaseType.tenant_id == tenant_id, CaseType.tenant_id.is_(None)),
            )
            .order_by(CaseType.tenant_id.desc().nullslast())
        )
        res = await self.db.execute(stmt)
        return res.scalars().first()

    async def list_case_types(
        self, tenant_id: UUID, module: str | None = None, is_active: bool | None = None
    ) -> list[CaseType]:
        stmt = select(CaseType).where(
            CaseType.deleted_at.is_(None),
            or_(CaseType.tenant_id == tenant_id, CaseType.tenant_id.is_(None)),
        )
        if module:
            stmt = stmt.where(CaseType.module == module.upper())
        if is_active is not None:
            stmt = stmt.where(CaseType.is_active == is_active)
        stmt = stmt.order_by(CaseType.name)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create_case_type(self, case_type: CaseType) -> CaseType:
        self.db.add(case_type)
        await self.db.flush()
        await self.db.refresh(case_type)
        return case_type

    async def update_case_type(self, case_type: CaseType) -> CaseType:
        await self.db.flush()
        await self.db.refresh(case_type)
        return case_type

    # -------------------------------------------------------------------------
    # 2. WORK QUEUES & MEMBERS
    # -------------------------------------------------------------------------

    async def get_queue_by_id(self, tenant_id: UUID, queue_id: UUID) -> WorkQueue | None:
        stmt = (
            select(WorkQueue)
            .where(WorkQueue.tenant_id == tenant_id, WorkQueue.id == queue_id)
            .options(selectinload(WorkQueue.members))
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_queue_by_key(self, tenant_id: UUID, key: str) -> WorkQueue | None:
        stmt = (
            select(WorkQueue)
            .where(WorkQueue.tenant_id == tenant_id, WorkQueue.key == key)
            .options(selectinload(WorkQueue.members))
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_queues(
        self, tenant_id: UUID, module: str | None = None, is_active: bool | None = None
    ) -> list[WorkQueue]:
        stmt = (
            select(WorkQueue)
            .where(WorkQueue.tenant_id == tenant_id)
            .options(selectinload(WorkQueue.members))
        )
        if module:
            stmt = stmt.where(WorkQueue.module == module.upper())
        if is_active is not None:
            stmt = stmt.where(WorkQueue.is_active == is_active)
        stmt = stmt.order_by(WorkQueue.name)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create_queue(self, queue: WorkQueue) -> WorkQueue:
        self.db.add(queue)
        await self.db.flush()
        await self.db.refresh(queue)
        return queue

    async def update_queue(self, queue: WorkQueue) -> WorkQueue:
        await self.db.flush()
        await self.db.refresh(queue)
        return queue

    async def get_queue_member(
        self, tenant_id: UUID, queue_id: UUID, user_id: UUID
    ) -> QueueMember | None:
        stmt = select(QueueMember).where(
            QueueMember.tenant_id == tenant_id,
            QueueMember.queue_id == queue_id,
            QueueMember.user_id == user_id,
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def add_queue_member(self, member: QueueMember) -> QueueMember:
        self.db.add(member)
        await self.db.flush()
        await self.db.refresh(member)
        return member

    async def remove_queue_member(self, tenant_id: UUID, queue_id: UUID, user_id: UUID) -> bool:
        stmt = delete(QueueMember).where(
            QueueMember.tenant_id == tenant_id,
            QueueMember.queue_id == queue_id,
            QueueMember.user_id == user_id,
        )
        res = await self.db.execute(stmt)
        await self.db.flush()
        return res.rowcount > 0

    # -------------------------------------------------------------------------
    # 3. CASES
    # -------------------------------------------------------------------------

    async def get_case_by_id(
        self, tenant_id: UUID, case_id: UUID, for_update: bool = False
    ) -> Case | None:
        stmt = (
            select(Case)
            .where(Case.tenant_id == tenant_id, Case.id == case_id, Case.deleted_at.is_(None))
            .options(
                selectinload(Case.tasks),
                selectinload(Case.comments),
                selectinload(Case.timeline_events),
                selectinload(Case.attachments),
            )
        )
        if for_update:
            stmt = stmt.with_for_update()
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_case_by_number(self, tenant_id: UUID, case_number: str) -> Case | None:
        stmt = (
            select(Case)
            .where(
                Case.tenant_id == tenant_id,
                Case.case_number == case_number,
                Case.deleted_at.is_(None),
            )
            .options(
                selectinload(Case.tasks),
                selectinload(Case.comments),
                selectinload(Case.timeline_events),
                selectinload(Case.attachments),
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_cases(
        self,
        tenant_id: UUID,
        status: str | None = None,
        priority: str | None = None,
        queue_id: UUID | None = None,
        owner_id: UUID | None = None,
        case_type_code: str | None = None,
        subject_entity_type: str | None = None,
        subject_entity_id: UUID | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Case], int]:
        base_where = [Case.tenant_id == tenant_id, Case.deleted_at.is_(None)]

        if status:
            base_where.append(Case.status == status)
        if priority:
            base_where.append(Case.priority == priority)
        if queue_id:
            base_where.append(Case.assigned_queue_id == queue_id)
        if owner_id:
            base_where.append(Case.owner_id == owner_id)
        if case_type_code:
            base_where.append(Case.case_type_code == case_type_code.upper())
        if subject_entity_type:
            base_where.append(Case.subject_entity_type == subject_entity_type)
        if subject_entity_id:
            base_where.append(Case.subject_entity_id == subject_entity_id)
        if search:
            search_clause = or_(
                Case.title.ilike(f"%{search}%"),
                Case.case_number.ilike(f"%{search}%"),
                Case.description.ilike(f"%{search}%"),
            )
            base_where.append(search_clause)

        count_stmt = select(func.count(Case.id)).where(and_(*base_where))
        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar_one()

        stmt = (
            select(Case)
            .where(and_(*base_where))
            .options(selectinload(Case.tasks))
            .order_by(Case.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all()), total

    async def create_case(self, case: Case) -> Case:
        self.db.add(case)
        await self.db.flush()
        await self.db.refresh(case)
        return case

    async def update_case(self, case: Case) -> Case:
        await self.db.flush()
        await self.db.refresh(case)
        return case

    # -------------------------------------------------------------------------
    # 4. CASE RELATIONSHIPS, COMMENTS, ATTACHMENTS & TIMELINE
    # -------------------------------------------------------------------------

    async def create_relationship(self, rel: CaseRelationship) -> CaseRelationship:
        self.db.add(rel)
        await self.db.flush()
        await self.db.refresh(rel)
        return rel

    async def list_relationships(self, tenant_id: UUID, case_id: UUID) -> list[CaseRelationship]:
        stmt = (
            select(CaseRelationship)
            .where(
                CaseRelationship.tenant_id == tenant_id,
                or_(
                    CaseRelationship.source_case_id == case_id,
                    CaseRelationship.target_case_id == case_id,
                ),
            )
            .order_by(CaseRelationship.created_at.desc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def add_comment(self, comment: CaseComment) -> CaseComment:
        self.db.add(comment)
        await self.db.flush()
        await self.db.refresh(comment)
        return comment

    async def list_comments(
        self,
        tenant_id: UUID,
        case_id: UUID,
        visibilities: list[str] | None = None,
    ) -> list[CaseComment]:
        stmt = select(CaseComment).where(
            CaseComment.tenant_id == tenant_id,
            CaseComment.case_id == case_id,
        )
        if visibilities:
            stmt = stmt.where(CaseComment.visibility.in_(visibilities))
        stmt = stmt.order_by(CaseComment.created_at.asc())
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def add_attachment(self, att: CaseAttachment) -> CaseAttachment:
        self.db.add(att)
        await self.db.flush()
        await self.db.refresh(att)
        return att

    async def list_attachments(self, tenant_id: UUID, case_id: UUID) -> list[CaseAttachment]:
        stmt = (
            select(CaseAttachment)
            .where(
                CaseAttachment.tenant_id == tenant_id,
                CaseAttachment.case_id == case_id,
            )
            .order_by(CaseAttachment.created_at.desc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def add_timeline_event(
        self,
        tenant_id: UUID,
        case_id: UUID,
        event_type: str,
        title: str,
        actor_id: UUID | None = None,
        task_id: UUID | None = None,
        details_json: dict[str, Any] | None = None,
    ) -> CaseTimelineEvent:
        event = CaseTimelineEvent(
            tenant_id=tenant_id,
            case_id=case_id,
            task_id=task_id,
            event_type=event_type,
            actor_id=actor_id,
            title=title,
            details_json=details_json or {},
            occurred_at=datetime.now(UTC),
        )
        self.db.add(event)
        await self.db.flush()
        await self.db.refresh(event)
        return event

    async def list_timeline_events(self, tenant_id: UUID, case_id: UUID) -> list[CaseTimelineEvent]:
        stmt = (
            select(CaseTimelineEvent)
            .where(
                CaseTimelineEvent.tenant_id == tenant_id,
                CaseTimelineEvent.case_id == case_id,
            )
            .order_by(CaseTimelineEvent.occurred_at.asc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    # -------------------------------------------------------------------------
    # 5. HUMAN TASKS & DECISIONS
    # -------------------------------------------------------------------------

    async def get_task_by_id(
        self, tenant_id: UUID, task_id: UUID, for_update: bool = False
    ) -> HumanTask | None:
        stmt = (
            select(HumanTask)
            .where(
                HumanTask.tenant_id == tenant_id,
                HumanTask.id == task_id,
                HumanTask.deleted_at.is_(None),
            )
            .options(
                selectinload(HumanTask.decisions),
                selectinload(HumanTask.comments),
            )
        )
        if for_update:
            stmt = stmt.with_for_update()
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

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
        base_where = [HumanTask.tenant_id == tenant_id, HumanTask.deleted_at.is_(None)]
        if case_id:
            base_where.append(HumanTask.case_id == case_id)
        if status:
            base_where.append(HumanTask.status == status)
        if priority:
            base_where.append(HumanTask.priority == priority)
        if assigned_user_id:
            base_where.append(HumanTask.assigned_user_id == assigned_user_id)
        if assigned_queue_id:
            base_where.append(HumanTask.assigned_queue_id == assigned_queue_id)

        count_stmt = select(func.count(HumanTask.id)).where(and_(*base_where))
        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar_one()

        stmt = (
            select(HumanTask)
            .where(and_(*base_where))
            .options(selectinload(HumanTask.decisions))
            .order_by(HumanTask.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all()), total

    async def create_task(self, task: HumanTask) -> HumanTask:
        self.db.add(task)
        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def update_task(self, task: HumanTask) -> HumanTask:
        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def claim_task_atomic(
        self, tenant_id: UUID, task_id: UUID, user_id: UUID
    ) -> HumanTask | None:
        """Atomically claim a task under concurrency protection."""
        now = datetime.now(UTC)
        stmt = (
            update(HumanTask)
            .where(
                HumanTask.tenant_id == tenant_id,
                HumanTask.id == task_id,
                HumanTask.deleted_at.is_(None),
                HumanTask.status == TaskStatus.PENDING,
                or_(
                    HumanTask.assigned_user_id.is_(None),
                    HumanTask.assigned_user_id == user_id,
                ),
            )
            .values(
                status=TaskStatus.CLAIMED,
                assigned_user_id=user_id,
                claimed_at=now,
                updated_at=now,
            )
            .returning(HumanTask.id)
        )
        res = await self.db.execute(stmt)
        updated_id = res.scalar_one_or_none()
        if not updated_id:
            return None
        await self.db.flush()
        task = await self.get_task_by_id(tenant_id, task_id)
        if task:
            await self.db.refresh(task)
        return task

    async def release_task_atomic(
        self, tenant_id: UUID, task_id: UUID, user_id: UUID
    ) -> HumanTask | None:
        """Atomically release a claimed task back to the queue/pending status."""
        now = datetime.now(UTC)
        stmt = (
            update(HumanTask)
            .where(
                HumanTask.tenant_id == tenant_id,
                HumanTask.id == task_id,
                HumanTask.deleted_at.is_(None),
                HumanTask.status.in_([TaskStatus.CLAIMED, TaskStatus.IN_PROGRESS]),
                HumanTask.assigned_user_id == user_id,
            )
            .values(
                status=TaskStatus.PENDING,
                assigned_user_id=None,
                claimed_at=None,
                updated_at=now,
            )
            .returning(HumanTask.id)
        )
        res = await self.db.execute(stmt)
        updated_id = res.scalar_one_or_none()
        if not updated_id:
            return None
        await self.db.flush()
        task = await self.get_task_by_id(tenant_id, task_id)
        if task:
            await self.db.refresh(task)
        return task

    async def complete_task_atomic(
        self,
        tenant_id: UUID,
        task_id: UUID,
        user_id: UUID,
        status: TaskStatus = TaskStatus.COMPLETED,
        output_result: dict[str, Any] | None = None,
    ) -> HumanTask | None:
        """Atomically complete a task preventing concurrent double completions."""
        now = datetime.now(UTC)
        stmt = (
            update(HumanTask)
            .where(
                HumanTask.tenant_id == tenant_id,
                HumanTask.id == task_id,
                HumanTask.deleted_at.is_(None),
                HumanTask.status.in_(
                    [TaskStatus.CLAIMED, TaskStatus.IN_PROGRESS, TaskStatus.PENDING]
                ),
            )
            .values(
                status=status,
                completed_at=now,
                completed_by_id=user_id,
                output_result_json=output_result,
                updated_at=now,
            )
            .returning(HumanTask.id)
        )
        res = await self.db.execute(stmt)
        updated_id = res.scalar_one_or_none()
        if not updated_id:
            return None
        await self.db.flush()
        task = await self.get_task_by_id(tenant_id, task_id)
        if task:
            await self.db.refresh(task)
        return task

    async def record_decision(self, decision: TaskDecision) -> TaskDecision:
        self.db.add(decision)
        await self.db.flush()
        await self.db.refresh(decision)
        return decision

    async def list_decisions(self, tenant_id: UUID, task_id: UUID) -> list[TaskDecision]:
        stmt = (
            select(TaskDecision)
            .where(
                TaskDecision.tenant_id == tenant_id,
                TaskDecision.task_id == task_id,
            )
            .order_by(TaskDecision.created_at.asc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    # -------------------------------------------------------------------------
    # 6. DELEGATIONS
    # -------------------------------------------------------------------------

    async def create_delegation(self, delegation: TaskDelegation) -> TaskDelegation:
        self.db.add(delegation)
        await self.db.flush()
        await self.db.refresh(delegation)
        return delegation

    async def get_active_delegation(
        self,
        tenant_id: UUID,
        delegator_id: UUID,
        delegatee_id: UUID,
        module: str | None = None,
    ) -> TaskDelegation | None:
        now = datetime.now(UTC)
        stmt = select(TaskDelegation).where(
            TaskDelegation.tenant_id == tenant_id,
            TaskDelegation.delegator_user_id == delegator_id,
            TaskDelegation.delegatee_user_id == delegatee_id,
            TaskDelegation.is_active.is_(True),
            TaskDelegation.valid_from <= now,
            TaskDelegation.valid_until >= now,
        )
        if module:
            stmt = stmt.where(
                or_(
                    TaskDelegation.scope_module == module.upper(),
                    TaskDelegation.scope_module.is_(None),
                )
            )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_delegations(
        self, tenant_id: UUID, user_id: UUID | None = None, is_active: bool | None = None
    ) -> list[TaskDelegation]:
        stmt = select(TaskDelegation).where(TaskDelegation.tenant_id == tenant_id)
        if user_id:
            stmt = stmt.where(
                or_(
                    TaskDelegation.delegator_user_id == user_id,
                    TaskDelegation.delegatee_user_id == user_id,
                )
            )
        if is_active is not None:
            stmt = stmt.where(TaskDelegation.is_active == is_active)
        stmt = stmt.order_by(TaskDelegation.valid_from.desc())
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def expire_delegations(self, tenant_id: UUID, as_of: datetime) -> int:
        stmt = (
            update(TaskDelegation)
            .where(
                TaskDelegation.tenant_id == tenant_id,
                TaskDelegation.is_active.is_(True),
                TaskDelegation.valid_until <= as_of,
            )
            .values(is_active=False, updated_at=as_of)
        )
        res = await self.db.execute(stmt)
        await self.db.flush()
        return res.rowcount

    # -------------------------------------------------------------------------
    # 7. SLA POLICIES & INSTANCES
    # -------------------------------------------------------------------------

    async def get_sla_policy(self, tenant_id: UUID, policy_id: UUID) -> SlaPolicy | None:
        stmt = select(SlaPolicy).where(SlaPolicy.tenant_id == tenant_id, SlaPolicy.id == policy_id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def find_matching_sla_policy(
        self,
        tenant_id: UUID,
        module: str,
        priority: str,
        case_type_code: str | None = None,
    ) -> SlaPolicy | None:
        stmt = select(SlaPolicy).where(
            SlaPolicy.tenant_id == tenant_id,
            SlaPolicy.is_active.is_(True),
            SlaPolicy.priority == priority,
            or_(SlaPolicy.module == module.upper(), SlaPolicy.module == "GENERAL"),
        )
        if case_type_code:
            stmt = stmt.order_by(
                SlaPolicy.case_type_code.desc().nullslast(),
                SlaPolicy.module.desc(),
            )
        else:
            stmt = stmt.order_by(SlaPolicy.module.desc())
        res = await self.db.execute(stmt)
        return res.scalars().first()

    async def list_sla_policies(
        self, tenant_id: UUID, module: str | None = None, is_active: bool | None = None
    ) -> list[SlaPolicy]:
        stmt = select(SlaPolicy).where(SlaPolicy.tenant_id == tenant_id)
        if module:
            stmt = stmt.where(SlaPolicy.module == module.upper())
        if is_active is not None:
            stmt = stmt.where(SlaPolicy.is_active == is_active)
        stmt = stmt.order_by(SlaPolicy.name)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create_sla_policy(self, policy: SlaPolicy) -> SlaPolicy:
        self.db.add(policy)
        await self.db.flush()
        await self.db.refresh(policy)
        return policy

    async def update_sla_policy(self, policy: SlaPolicy) -> SlaPolicy:
        await self.db.flush()
        await self.db.refresh(policy)
        return policy

    async def create_sla_instance(self, instance: SlaInstance) -> SlaInstance:
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def get_sla_instance_by_case(self, tenant_id: UUID, case_id: UUID) -> SlaInstance | None:
        stmt = (
            select(SlaInstance)
            .where(SlaInstance.tenant_id == tenant_id, SlaInstance.case_id == case_id)
            .order_by(SlaInstance.created_at.desc())
        )
        res = await self.db.execute(stmt)
        return res.scalars().first()

    async def get_sla_instance_by_task(self, tenant_id: UUID, task_id: UUID) -> SlaInstance | None:
        stmt = (
            select(SlaInstance)
            .where(SlaInstance.tenant_id == tenant_id, SlaInstance.task_id == task_id)
            .order_by(SlaInstance.created_at.desc())
        )
        res = await self.db.execute(stmt)
        return res.scalars().first()

    async def list_active_sla_instances(self, tenant_id: UUID) -> list[SlaInstance]:
        stmt = (
            select(SlaInstance)
            .where(
                SlaInstance.tenant_id == tenant_id,
                SlaInstance.status.in_([SlaStatus.ON_TRACK, SlaStatus.AT_RISK]),
            )
            .order_by(SlaInstance.due_at.asc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    # -------------------------------------------------------------------------
    # 8. CASE ANALYTICS & OPERATIONAL METRICS
    # -------------------------------------------------------------------------

    async def get_case_analytics(self, tenant_id: UUID) -> dict[str, Any]:
        """Compute operational case and task performance analytics for reporting."""
        # Case counts by status
        status_stmt = (
            select(Case.status, func.count(Case.id))
            .where(Case.tenant_id == tenant_id, Case.deleted_at.is_(None))
            .group_by(Case.status)
        )
        status_res = await self.db.execute(status_stmt)
        cases_by_status = {row[0]: row[1] for row in status_res.all()}

        # Case counts by priority
        prio_stmt = (
            select(Case.priority, func.count(Case.id))
            .where(Case.tenant_id == tenant_id, Case.deleted_at.is_(None))
            .group_by(Case.priority)
        )
        prio_res = await self.db.execute(prio_stmt)
        cases_by_priority = {row[0]: row[1] for row in prio_res.all()}

        # Case counts by module (via CaseType or prefix)
        type_stmt = (
            select(Case.case_type_code, func.count(Case.id))
            .where(Case.tenant_id == tenant_id, Case.deleted_at.is_(None))
            .group_by(Case.case_type_code)
        )
        type_res = await self.db.execute(type_stmt)
        cases_by_module = {row[0]: row[1] for row in type_res.all()}

        # Cases by queue
        queue_stmt = (
            select(WorkQueue.name, func.count(Case.id))
            .join(Case, Case.assigned_queue_id == WorkQueue.id)
            .where(Case.tenant_id == tenant_id, Case.deleted_at.is_(None))
            .group_by(WorkQueue.name)
        )
        queue_res = await self.db.execute(queue_stmt)
        cases_by_queue = {row[0]: row[1] for row in queue_res.all()}

        # Task counts by status
        task_stmt = (
            select(HumanTask.status, func.count(HumanTask.id))
            .where(HumanTask.tenant_id == tenant_id, HumanTask.deleted_at.is_(None))
            .group_by(HumanTask.status)
        )
        task_res = await self.db.execute(task_stmt)
        tasks_by_status = {row[0]: row[1] for row in task_res.all()}

        # Total counts
        total_cases = sum(cases_by_status.values())
        open_cases = cases_by_status.get(CaseStatus.OPEN, 0)
        in_progress_cases = cases_by_status.get(CaseStatus.IN_PROGRESS, 0)
        waiting_cases = cases_by_status.get(CaseStatus.WAITING, 0)
        escalated_cases = cases_by_status.get(CaseStatus.ESCALATED, 0)
        resolved_cases = cases_by_status.get(CaseStatus.RESOLVED, 0)
        closed_cases = cases_by_status.get(CaseStatus.CLOSED, 0)
        total_tasks = sum(tasks_by_status.values())

        # SLA Breaches
        breach_stmt = select(func.count(SlaInstance.id)).where(
            SlaInstance.tenant_id == tenant_id, SlaInstance.breached.is_(True)
        )
        breach_res = await self.db.execute(breach_stmt)
        sla_breaches_total = breach_res.scalar_one()

        total_sla_stmt = select(func.count(SlaInstance.id)).where(
            SlaInstance.tenant_id == tenant_id
        )
        total_sla_res = await self.db.execute(total_sla_stmt)
        total_slas = total_sla_res.scalar_one()

        sla_compliance_rate = (
            round(((total_slas - sla_breaches_total) / total_slas) * 100, 2)
            if total_slas > 0
            else 100.0
        )

        escalation_rate = (
            round((escalated_cases / total_cases) * 100, 2) if total_cases > 0 else 0.0
        )

        # Average resolution time in hours
        avg_res_stmt = select(
            func.avg(func.extract("epoch", Case.resolved_at - Case.created_at) / 3600.0)
        ).where(
            Case.tenant_id == tenant_id,
            Case.resolved_at.isnot(None),
            Case.deleted_at.is_(None),
        )
        avg_res = await self.db.execute(avg_res_stmt)
        avg_hours = avg_res.scalar_one()
        avg_resolution_time_hours = round(float(avg_hours), 2) if avg_hours else 0.0

        return {
            "tenant_id": tenant_id,
            "open_cases": open_cases,
            "in_progress_cases": in_progress_cases,
            "waiting_cases": waiting_cases,
            "escalated_cases": escalated_cases,
            "resolved_cases": resolved_cases,
            "closed_cases": closed_cases,
            "total_cases": total_cases,
            "avg_resolution_time_hours": avg_resolution_time_hours,
            "sla_compliance_rate": sla_compliance_rate,
            "sla_breaches_total": sla_breaches_total,
            "cases_by_priority": cases_by_priority,
            "cases_by_status": cases_by_status,
            "cases_by_module": cases_by_module,
            "cases_by_queue": cases_by_queue,
            "tasks_by_status": tasks_by_status,
            "escalation_rate": escalation_rate,
            "reassignment_count": 0,
            "total_human_tasks": total_tasks,
        }
