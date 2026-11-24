"""Enterprise Case Management and Human-in-the-Loop Orchestration Service (Step 25)."""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditEventCategory, build_audit_entry
from app.core.exceptions import (
    CaseAlreadyClosedException,
    CaseInvalidStatusException,
    CaseNotFoundException,
    CaseTypeNotFoundException,
    ConflictException,
    NotFoundException,
    ValidationException,
    WorkQueueNotFoundException,
)
from app.models.case_management import (
    Case,
    CaseAttachment,
    CaseComment,
    CaseRelationship,
    CaseStatus,
    CaseTimelineEvent,
    CaseTimelineEventType,
    CaseType,
    CommentVisibility,
    HumanDecision,
    QueueMember,
    TaskStatus,
    WorkQueue,
)
from app.models.configuration import NumberingResetFrequency
from app.models.workflow import WorkflowExecution, WorkflowExecutionStatus
from app.repositories.case_repository import CaseRepository
from app.schemas.case_management import (
    CaseAttachmentCreate,
    CaseCommentCreate,
    CaseCreate,
    CaseRelationshipCreate,
    CaseResolveRequest,
    CaseTypeCreate,
    CaseTypeUpdate,
    CaseUpdate,
    QueueMemberCreate,
    WorkQueueCreate,
    WorkQueueUpdate,
)
from app.schemas.configuration import NumberingSequenceCreate
from app.services.sequence_service import SequenceService

logger = logging.getLogger("campusos.case_service")


class CaseService:
    """Enterprise Operational Case Management Service."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CaseRepository(db)

    # -------------------------------------------------------------------------
    # 1. CASE TYPE OPERATIONS
    # -------------------------------------------------------------------------

    async def create_case_type(
        self, tenant_id: UUID, dto: CaseTypeCreate, actor_id: UUID | None = None
    ) -> CaseType:
        existing = await self.repo.get_case_type_by_code(tenant_id, dto.code)
        if existing and existing.tenant_id == tenant_id:
            raise ConflictException(f"Case type with code '{dto.code}' already exists.")

        case_type = CaseType(
            tenant_id=tenant_id,
            code=dto.code.upper(),
            name=dto.name,
            description=dto.description,
            module=dto.module.upper(),
            default_priority=dto.default_priority,
            default_queue_id=dto.default_queue_id,
            sla_hours=dto.sla_hours,
            requires_decision=dto.requires_decision,
            is_active=dto.is_active,
            is_system=False,
        )
        created = await self.repo.create_case_type(case_type)
        return created

    async def get_case_type(self, tenant_id: UUID, case_type_id: UUID) -> CaseType:
        ct = await self.repo.get_case_type_by_id(tenant_id, case_type_id)
        if not ct:
            raise CaseTypeNotFoundException(case_type_id)
        return ct

    async def list_case_types(
        self, tenant_id: UUID, module: str | None = None, is_active: bool | None = None
    ) -> list[CaseType]:
        return await self.repo.list_case_types(tenant_id, module=module, is_active=is_active)

    async def update_case_type(
        self, tenant_id: UUID, case_type_id: UUID, dto: CaseTypeUpdate
    ) -> CaseType:
        ct = await self.get_case_type(tenant_id, case_type_id)
        if dto.name is not None:
            ct.name = dto.name
        if dto.description is not None:
            ct.description = dto.description
        if dto.module is not None:
            ct.module = dto.module.upper()
        if dto.default_priority is not None:
            ct.default_priority = dto.default_priority
        if dto.default_queue_id is not None:
            ct.default_queue_id = dto.default_queue_id
        if dto.sla_hours is not None:
            ct.sla_hours = dto.sla_hours
        if dto.requires_decision is not None:
            ct.requires_decision = dto.requires_decision
        if dto.is_active is not None:
            ct.is_active = dto.is_active
        return await self.repo.update_case_type(ct)

    # -------------------------------------------------------------------------
    # 2. WORK QUEUE OPERATIONS
    # -------------------------------------------------------------------------

    async def create_work_queue(
        self, tenant_id: UUID, dto: WorkQueueCreate, actor_id: UUID | None = None
    ) -> WorkQueue:
        existing = await self.repo.get_queue_by_key(tenant_id, dto.key)
        if existing:
            raise ConflictException(f"Work queue with key '{dto.key}' already exists.")

        queue = WorkQueue(
            tenant_id=tenant_id,
            key=dto.key.upper(),
            name=dto.name,
            description=dto.description,
            module=dto.module.upper(),
            is_active=dto.is_active,
            assignment_policy=dto.assignment_policy,
            capacity=dto.capacity,
            supervisor_id=dto.supervisor_id,
            sla_hours=dto.sla_hours,
        )
        created = await self.repo.create_queue(queue)

        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.WORK_QUEUE_CREATED,
            entity_type="work_queue",
            entity_id=created.id,
            user_id=actor_id,
            new_values_json={"key": created.key, "name": created.name, "module": created.module},
            business_context=f"Work queue '{created.name}' created.",
        )
        self.db.add(audit)
        await self.db.flush()
        return created

    async def get_work_queue(self, tenant_id: UUID, queue_id: UUID) -> WorkQueue:
        q = await self.repo.get_queue_by_id(tenant_id, queue_id)
        if not q:
            raise WorkQueueNotFoundException(queue_id)
        return q

    async def list_work_queues(
        self, tenant_id: UUID, module: str | None = None, is_active: bool | None = None
    ) -> list[WorkQueue]:
        return await self.repo.list_queues(tenant_id, module=module, is_active=is_active)

    async def update_work_queue(
        self, tenant_id: UUID, queue_id: UUID, dto: WorkQueueUpdate, actor_id: UUID | None = None
    ) -> WorkQueue:
        q = await self.get_work_queue(tenant_id, queue_id)
        if dto.name is not None:
            q.name = dto.name
        if dto.description is not None:
            q.description = dto.description
        if dto.module is not None:
            q.module = dto.module.upper()
        if dto.is_active is not None:
            q.is_active = dto.is_active
        if dto.assignment_policy is not None:
            q.assignment_policy = dto.assignment_policy
        if dto.capacity is not None:
            q.capacity = dto.capacity
        if dto.supervisor_id is not None:
            q.supervisor_id = dto.supervisor_id
        if dto.sla_hours is not None:
            q.sla_hours = dto.sla_hours

        updated = await self.repo.update_queue(q)
        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.WORK_QUEUE_UPDATED,
            entity_type="work_queue",
            entity_id=updated.id,
            user_id=actor_id,
            new_values_json={"name": updated.name, "is_active": updated.is_active},
            business_context=f"Work queue '{updated.name}' updated.",
        )
        self.db.add(audit)
        await self.db.flush()
        return updated

    async def add_queue_member(
        self, tenant_id: UUID, queue_id: UUID, dto: QueueMemberCreate, actor_id: UUID | None = None
    ) -> QueueMember:
        await self.get_work_queue(tenant_id, queue_id)
        existing = await self.repo.get_queue_member(tenant_id, queue_id, dto.user_id)
        if existing:
            existing.is_supervisor = dto.is_supervisor
            existing.is_active = dto.is_active
            existing.max_active_tasks = dto.max_active_tasks
            await self.db.flush()
            return existing

        member = QueueMember(
            tenant_id=tenant_id,
            queue_id=queue_id,
            user_id=dto.user_id,
            is_supervisor=dto.is_supervisor,
            is_active=dto.is_active,
            max_active_tasks=dto.max_active_tasks,
        )
        created = await self.repo.add_queue_member(member)

        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.QUEUE_MEMBER_ADDED,
            entity_type="queue_member",
            entity_id=created.id,
            user_id=actor_id,
            new_values_json={"queue_id": str(queue_id), "user_id": str(dto.user_id)},
            business_context="Member added to queue.",
        )
        self.db.add(audit)
        await self.db.flush()
        return created

    async def remove_queue_member(
        self, tenant_id: UUID, queue_id: UUID, user_id: UUID, actor_id: UUID | None = None
    ) -> bool:
        removed = await self.repo.remove_queue_member(tenant_id, queue_id, user_id)
        if removed:
            audit = build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.QUEUE_MEMBER_REMOVED,
                entity_type="queue_member",
                entity_id=queue_id,
                user_id=actor_id,
                old_values_json={"user_id": str(user_id)},
                business_context="Member removed from queue.",
            )
            self.db.add(audit)
            await self.db.flush()
        return removed

    # -------------------------------------------------------------------------
    # 3. CASE LIFECYCLE OPERATIONS
    # -------------------------------------------------------------------------

    async def _generate_case_number(self, tenant_id: UUID) -> str:
        """Atomically generate sequential unique case number via SequenceService."""
        try:
            seq_resp = await SequenceService.generate_next_sequence_number(
                self.db, tenant_id, "case.number"
            )
            return seq_resp.generated_number
        except NotFoundException:
            # Idempotently initialize sequence definition if not present
            try:
                seq_create = NumberingSequenceCreate(
                    sequence_key="case.number",
                    name="Case Numbering Sequence",
                    prefix="CASE-",
                    pattern="{PREFIX}{YEAR}-{SEQ}",
                    padding=5,
                    step=1,
                    reset_frequency=NumberingResetFrequency.YEARLY,
                )
                await SequenceService.create_sequence(self.db, tenant_id, seq_create)
                seq_resp = await SequenceService.generate_next_sequence_number(
                    self.db, tenant_id, "case.number"
                )
                return seq_resp.generated_number
            except Exception:
                now_str = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
                return f"CASE-{now_str}"

    async def create_case(
        self, tenant_id: UUID, dto: CaseCreate, actor_id: UUID | None = None
    ) -> Case:
        # Validate or resolve Case Type
        case_type = await self.repo.get_case_type_by_code(tenant_id, dto.case_type_code)
        case_type_id = case_type.id if case_type else None

        # Resolve queue fallback if not provided
        assigned_queue = dto.assigned_queue_id
        if not assigned_queue and case_type and case_type.default_queue_id:
            assigned_queue = case_type.default_queue_id

        # Generate atomic unique case number
        case_number = await self._generate_case_number(tenant_id)

        case = Case(
            tenant_id=tenant_id,
            case_number=case_number,
            case_type_id=case_type_id,
            case_type_code=dto.case_type_code.upper(),
            title=dto.title,
            description=dto.description,
            priority=dto.priority,
            status=CaseStatus.OPEN,
            owner_id=dto.owner_id,
            assigned_queue_id=assigned_queue,
            subject_entity_type=dto.subject_entity_type,
            subject_entity_id=dto.subject_entity_id,
            created_by_id=actor_id,
            due_at=dto.due_at,
            metadata_json=dto.metadata_json or {},
        )
        created = await self.repo.create_case(case)

        # Record timeline event
        await self.repo.add_timeline_event(
            tenant_id=tenant_id,
            case_id=created.id,
            event_type=CaseTimelineEventType.CASE_CREATED,
            actor_id=actor_id,
            title=f"Case {created.case_number} created",
            details_json={"priority": created.priority, "case_type": created.case_type_code},
        )

        # Forensic audit record
        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.CASE_CREATED,
            entity_type="case",
            entity_id=created.id,
            user_id=actor_id,
            new_values_json={
                "case_number": created.case_number,
                "title": created.title,
                "priority": created.priority,
                "status": created.status,
            },
            business_context=f"Case {created.case_number} created.",
        )
        self.db.add(audit)
        await self.db.flush()

        # Initialize SLA clock
        from app.services.sla_service import SlaService

        sla_srv = SlaService(self.db)
        await sla_srv.initialize_case_sla(tenant_id, created, case_type)
        await self.db.refresh(created)

        return created

    async def get_case(self, tenant_id: UUID, case_id: UUID, for_update: bool = False) -> Case:
        case = await self.repo.get_case_by_id(tenant_id, case_id, for_update=for_update)
        if not case:
            raise CaseNotFoundException(case_id)
        return case

    async def get_case_by_number(self, tenant_id: UUID, case_number: str) -> Case:
        case = await self.repo.get_case_by_number(tenant_id, case_number)
        if not case:
            raise CaseNotFoundException(case_number)
        return case

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
        return await self.repo.list_cases(
            tenant_id=tenant_id,
            status=status,
            priority=priority,
            queue_id=queue_id,
            owner_id=owner_id,
            case_type_code=case_type_code,
            subject_entity_type=subject_entity_type,
            subject_entity_id=subject_entity_id,
            search=search,
            limit=limit,
            offset=offset,
        )

    async def update_case(
        self, tenant_id: UUID, case_id: UUID, dto: CaseUpdate, actor_id: UUID | None = None
    ) -> Case:
        case = await self.get_case(tenant_id, case_id, for_update=True)
        if case.status in [CaseStatus.CLOSED, CaseStatus.CANCELLED]:
            raise CaseAlreadyClosedException(case.case_number)

        old_priority = case.priority
        if dto.title is not None:
            case.title = dto.title
        if dto.description is not None:
            case.description = dto.description
        if dto.priority is not None and dto.priority != old_priority:
            case.priority = dto.priority
            await self.repo.add_timeline_event(
                tenant_id=tenant_id,
                case_id=case.id,
                event_type=CaseTimelineEventType.STATUS_CHANGED,
                actor_id=actor_id,
                title=f"Priority changed from {old_priority} to {dto.priority}",
                details_json={"old_priority": old_priority, "new_priority": dto.priority},
            )
            audit = build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.CASE_PRIORITY_CHANGED,
                entity_type="case",
                entity_id=case.id,
                user_id=actor_id,
                old_values_json={"priority": old_priority},
                new_values_json={"priority": dto.priority},
                business_context=f"Case {case.case_number} priority updated.",
            )
            self.db.add(audit)

        if dto.owner_id is not None:
            case.owner_id = dto.owner_id
        if dto.assigned_queue_id is not None:
            case.assigned_queue_id = dto.assigned_queue_id
        if dto.due_at is not None:
            case.due_at = dto.due_at
        if dto.metadata_json is not None:
            case.metadata_json.update(dto.metadata_json)

        await self.repo.update_case(case)
        await self.db.flush()
        await self.db.refresh(case)
        return case

    async def resolve_case(
        self, tenant_id: UUID, case_id: UUID, dto: CaseResolveRequest, actor_id: UUID | None = None
    ) -> Case:
        case = await self.get_case(tenant_id, case_id, for_update=True)
        if case.status in [CaseStatus.CLOSED, CaseStatus.CANCELLED]:
            raise CaseAlreadyClosedException(case.case_number)

        # Validate closure rules: check pending human tasks
        tasks, _ = await self.repo.list_tasks(tenant_id, case_id=case_id)
        pending_tasks = [
            t
            for t in tasks
            if t.status in [TaskStatus.PENDING, TaskStatus.CLAIMED, TaskStatus.IN_PROGRESS]
        ]
        if pending_tasks:
            msg = (
                f"Cannot resolve case: {len(pending_tasks)} "
                "human task(s) remain pending completion."
            )
            raise ValidationException(msg)

        now = datetime.now(UTC)
        case.status = CaseStatus.RESOLVED
        case.resolved_at = now
        case.resolution_reason = dto.resolution_reason
        case.resolution_notes = dto.resolution_notes

        await self.repo.add_timeline_event(
            tenant_id=tenant_id,
            case_id=case.id,
            event_type=CaseTimelineEventType.CASE_RESOLVED,
            actor_id=actor_id,
            title=f"Case resolved: {dto.resolution_reason}",
            details_json={"reason": dto.resolution_reason, "notes": dto.resolution_notes},
        )

        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.CASE_RESOLVED,
            entity_type="case",
            entity_id=case.id,
            user_id=actor_id,
            new_values_json={
                "status": CaseStatus.RESOLVED,
                "reason": dto.resolution_reason,
            },
            business_context=f"Case {case.case_number} resolved.",
        )
        self.db.add(audit)
        await self.db.flush()
        await self.db.refresh(case)
        return case

    async def close_case(
        self,
        tenant_id: UUID,
        case_id: UUID,
        closure_notes: str | None = None,
        actor_id: UUID | None = None,
    ) -> Case:
        case = await self.get_case(tenant_id, case_id, for_update=True)
        if case.status == CaseStatus.CLOSED:
            return case

        now = datetime.now(UTC)
        case.status = CaseStatus.CLOSED
        case.closed_at = now
        if closure_notes:
            case.resolution_notes = (
                case.resolution_notes or ""
            ) + f"\nClosure Notes: {closure_notes}"

        await self.repo.add_timeline_event(
            tenant_id=tenant_id,
            case_id=case.id,
            event_type=CaseTimelineEventType.CASE_CLOSED,
            actor_id=actor_id,
            title="Case closed",
            details_json={"closure_notes": closure_notes},
        )

        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.CASE_CLOSED,
            entity_type="case",
            entity_id=case.id,
            user_id=actor_id,
            new_values_json={"status": CaseStatus.CLOSED},
            business_context=f"Case {case.case_number} closed.",
        )
        self.db.add(audit)

        # Atomically emit domain event in active transaction
        try:
            from app.core.events import OutboxService
            await OutboxService.publish_event(
                db=self.db,
                tenant_id=tenant_id,
                event_type="workflow.case.completed",
                aggregate_type="Case",
                aggregate_id=case.id,
                payload={
                    "case_id": str(case.id),
                    "case_number": case.case_number,
                    "resolution": closure_notes or case.resolution_reason or "CLOSED",
                    "closed_by": str(actor_id) if actor_id else None,
                    "case_type": case.case_type_code,
                },
                actor_id=actor_id,
                producer="CASE_MANAGEMENT_MODULE",
            )
        except Exception:
            pass

        await self.repo.update_case(case)
        await self.db.flush()
        await self.db.refresh(case)
        return case

    async def reopen_case(
        self, tenant_id: UUID, case_id: UUID, reopen_reason: str, actor_id: UUID | None = None
    ) -> Case:
        case = await self.get_case(tenant_id, case_id, for_update=True)
        if case.status not in [CaseStatus.RESOLVED, CaseStatus.CLOSED]:
            raise CaseInvalidStatusException(
                f"Only RESOLVED or CLOSED cases can be reopened (current: {case.status})."
            )

        case.status = CaseStatus.REOPENED
        case.reopen_count += 1
        case.closed_at = None
        case.resolved_at = None

        await self.repo.add_timeline_event(
            tenant_id=tenant_id,
            case_id=case.id,
            event_type=CaseTimelineEventType.CASE_REOPENED,
            actor_id=actor_id,
            title=f"Case reopened: {reopen_reason}",
            details_json={"reason": reopen_reason, "reopen_count": case.reopen_count},
        )

        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.CASE_REOPENED,
            entity_type="case",
            entity_id=case.id,
            user_id=actor_id,
            new_values_json={"status": CaseStatus.REOPENED, "reason": reopen_reason},
            business_context=f"Case {case.case_number} reopened.",
        )
        self.db.add(audit)
        await self.db.flush()
        await self.db.refresh(case)
        return case

    # -------------------------------------------------------------------------
    # 4. CASE COMMENTS, ATTACHMENTS & RELATIONSHIPS
    # -------------------------------------------------------------------------

    async def add_comment(
        self, tenant_id: UUID, case_id: UUID, dto: CaseCommentCreate, author_id: UUID
    ) -> CaseComment:
        await self.get_case(tenant_id, case_id)
        comment = CaseComment(
            tenant_id=tenant_id,
            case_id=case_id,
            task_id=dto.task_id,
            author_id=author_id,
            content=dto.content,
            visibility=dto.visibility,
            metadata_json=dto.metadata_json,
        )
        created = await self.repo.add_comment(comment)

        await self.repo.add_timeline_event(
            tenant_id=tenant_id,
            case_id=case_id,
            task_id=dto.task_id,
            event_type=CaseTimelineEventType.COMMENT_ADDED,
            actor_id=author_id,
            title="Comment added to case",
            details_json={"visibility": dto.visibility},
        )

        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.CASE_COMMENT_ADDED,
            entity_type="case_comment",
            entity_id=created.id,
            user_id=author_id,
            new_values_json={"visibility": dto.visibility},
            business_context="Comment added to case.",
        )
        self.db.add(audit)
        await self.db.flush()
        return created

    async def list_comments(
        self, tenant_id: UUID, case_id: UUID, user_role: str | None = None
    ) -> list[CaseComment]:
        # Filter visibility according to caller role
        visibilities = [CommentVisibility.INTERNAL, CommentVisibility.CASE_PARTICIPANT]
        if user_role == "STUDENT":
            visibilities = [CommentVisibility.CASE_PARTICIPANT]
        elif user_role in ["SUPER_ADMIN", "INSTITUTION_ADMIN"]:
            visibilities.append(CommentVisibility.RESTRICTED)

        return await self.repo.list_comments(tenant_id, case_id, visibilities=visibilities)

    async def add_attachment(
        self, tenant_id: UUID, case_id: UUID, dto: CaseAttachmentCreate, uploader_id: UUID
    ) -> CaseAttachment:
        await self.get_case(tenant_id, case_id)
        att = CaseAttachment(
            tenant_id=tenant_id,
            case_id=case_id,
            task_id=dto.task_id,
            document_id=dto.document_id,
            attachment_type=dto.attachment_type,
            title=dto.title,
            visibility=dto.visibility,
            uploaded_by_id=uploader_id,
        )
        created = await self.repo.add_attachment(att)

        await self.repo.add_timeline_event(
            tenant_id=tenant_id,
            case_id=case_id,
            task_id=dto.task_id,
            event_type=CaseTimelineEventType.DOCUMENT_ATTACHED,
            actor_id=uploader_id,
            title=f"Document attached: {dto.title}",
            details_json={"document_id": str(dto.document_id), "type": dto.attachment_type},
        )

        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.CASE_ATTACHMENT_ADDED,
            entity_type="case_attachment",
            entity_id=created.id,
            user_id=uploader_id,
            new_values_json={"document_id": str(dto.document_id), "title": dto.title},
            business_context="Document attached to case.",
        )
        self.db.add(audit)
        await self.db.flush()
        return created

    async def list_attachments(self, tenant_id: UUID, case_id: UUID) -> list[CaseAttachment]:
        return await self.repo.list_attachments(tenant_id, case_id)

    async def create_relationship(
        self,
        tenant_id: UUID,
        source_case_id: UUID,
        dto: CaseRelationshipCreate,
        actor_id: UUID | None = None,
    ) -> CaseRelationship:
        if source_case_id == dto.target_case_id:
            raise ValidationException("A case cannot establish a relationship to itself.")

        await self.get_case(tenant_id, source_case_id)
        await self.get_case(tenant_id, dto.target_case_id)

        rel = CaseRelationship(
            tenant_id=tenant_id,
            source_case_id=source_case_id,
            target_case_id=dto.target_case_id,
            relationship_type=dto.relationship_type,
            notes=dto.notes,
            created_by_id=actor_id,
        )
        created = await self.repo.create_relationship(rel)

        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.CASE_RELATIONSHIP_CREATED,
            entity_type="case_relationship",
            entity_id=created.id,
            user_id=actor_id,
            new_values_json={
                "source_case_id": str(source_case_id),
                "target_case_id": str(dto.target_case_id),
                "relationship_type": dto.relationship_type,
            },
            business_context="Case relationship established.",
        )
        self.db.add(audit)
        await self.db.flush()
        return created

    async def list_relationships(self, tenant_id: UUID, case_id: UUID) -> list[CaseRelationship]:
        return await self.repo.list_relationships(tenant_id, case_id)

    async def get_timeline(self, tenant_id: UUID, case_id: UUID) -> list[CaseTimelineEvent]:
        await self.get_case(tenant_id, case_id)
        return await self.repo.list_timeline_events(tenant_id, case_id)

    # -------------------------------------------------------------------------
    # 5. HITL WORKFLOW BRIDGE TRANSITIONS
    # -------------------------------------------------------------------------

    async def transition_workflow_instance(
        self,
        tenant_id: UUID,
        execution_id: UUID,
        action: str,
        reason: str,
        target_step_key: str | None = None,
        task_id: UUID | None = None,
        actor_id: UUID | None = None,
        context_updates: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Bridge HITL decision into Step 17 workflow execution engine."""
        from sqlalchemy import select

        stmt = select(WorkflowExecution).where(
            WorkflowExecution.tenant_id == tenant_id,
            WorkflowExecution.id == execution_id,
        )
        res = await self.db.execute(stmt)
        execution = res.scalar_one_or_none()
        if not execution:
            raise NotFoundException("WorkflowExecution", execution_id)

        now = datetime.now(UTC)
        prev_status = execution.status

        # If action is an approval or completion
        if action in [HumanDecision.APPROVE, "APPROVE", "COMPLETE"]:
            execution.status = WorkflowExecutionStatus.SUCCEEDED
            execution.completed_at = now
        elif action in [HumanDecision.REJECT, "REJECT"]:
            execution.status = WorkflowExecutionStatus.FAILED
            execution.error_code = "HUMAN_REJECTED"
            execution.error_message = reason
            execution.completed_at = now
        elif action in [HumanDecision.ESCALATE, "ESCALATE"]:
            execution.status = WorkflowExecutionStatus.RUNNING
        else:
            execution.status = WorkflowExecutionStatus.WAITING

        if context_updates:
            current_ctx = execution.context_data or {}
            current_ctx.update(context_updates)
            execution.context_data = current_ctx

        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.CASE_STATUS_CHANGED,
            entity_type="workflow_execution",
            entity_id=execution.id,
            user_id=actor_id,
            old_values_json={"status": prev_status},
            new_values_json={"status": execution.status, "action": action, "reason": reason},
            business_context=f"HITL transition '{action}' on workflow execution {execution_id}.",
        )
        self.db.add(audit)
        await self.db.flush()

        return {
            "workflow_instance_id": execution.id,
            "previous_step": prev_status,
            "current_step": target_step_key or execution.status,
            "status": execution.status,
            "transitioned_at": now,
            "decision_recorded": action,
        }

    # -------------------------------------------------------------------------
    # 6. OPERATIONAL ANALYTICS
    # -------------------------------------------------------------------------

    async def get_analytics(self, tenant_id: UUID) -> dict[str, Any]:
        return await self.repo.get_case_analytics(tenant_id)
