"""Enterprise Service Level Agreement (SLA) & Escalation Service (Step 25)."""

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditEventCategory, build_audit_entry
from app.core.exceptions import ConflictException, SlaPolicyNotFoundException
from app.models.case_management import (
    Case,
    CasePriority,
    CaseStatus,
    CaseTimelineEventType,
    CaseType,
    HumanTask,
    SlaInstance,
    SlaPolicy,
    SlaStatus,
    TaskStatus,
)
from app.repositories.case_repository import CaseRepository
from app.schemas.case_management import SlaPolicyCreate, SlaPolicyUpdate

logger = logging.getLogger("campusos.sla_service")

# Standard priority target fallback durations (in minutes)
PRIORITY_FALLBACK_MINUTES = {
    CasePriority.URGENT: 240,  # 4 hours
    CasePriority.HIGH: 480,  # 8 hours
    CasePriority.NORMAL: 2880,  # 48 hours (2 days)
    CasePriority.LOW: 4320,  # 72 hours (3 days)
}


def _ensure_utc(dt: datetime) -> datetime:
    """Ensure datetime has timezone UTC to allow safe comparison and subtraction."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


class SlaService:
    """Service managing SLA Policies, Clocks, Breach Detection, and Escalation."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CaseRepository(db)

    # -------------------------------------------------------------------------
    # 1. SLA POLICIES CRUD
    # -------------------------------------------------------------------------

    async def create_sla_policy(
        self, tenant_id: UUID, dto: SlaPolicyCreate, actor_id: UUID | None = None
    ) -> SlaPolicy:
        existing = await self.repo.find_matching_sla_policy(
            tenant_id, dto.module, dto.priority, dto.case_type_code
        )
        if existing and existing.case_type_code == dto.case_type_code:
            raise ConflictException(
                "An SLA policy with identical module, priority, and case type already exists."
            )

        policy = SlaPolicy(
            tenant_id=tenant_id,
            name=dto.name,
            module=dto.module.upper(),
            case_type_code=dto.case_type_code.upper() if dto.case_type_code else None,
            priority=dto.priority,
            target_duration_minutes=dto.target_duration_minutes,
            warning_threshold_percentage=dto.warning_threshold_percentage,
            business_hours_only=dto.business_hours_only,
            business_start_hour=dto.business_start_hour,
            business_end_hour=dto.business_end_hour,
            escalation_queue_id=dto.escalation_queue_id,
            escalation_role=dto.escalation_role,
            is_active=dto.is_active,
        )
        created = await self.repo.create_sla_policy(policy)

        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.SLA_POLICY_CREATED,
            entity_type="sla_policy",
            entity_id=created.id,
            user_id=actor_id,
            new_values_json={
                "name": created.name,
                "target_minutes": created.target_duration_minutes,
                "priority": created.priority,
            },
            business_context=f"SLA policy '{created.name}' created.",
        )
        self.db.add(audit)
        await self.db.flush()
        return created

    async def get_sla_policy(self, tenant_id: UUID, policy_id: UUID) -> SlaPolicy:
        policy = await self.repo.get_sla_policy(tenant_id, policy_id)
        if not policy:
            raise SlaPolicyNotFoundException(policy_id)
        return policy

    async def list_sla_policies(
        self, tenant_id: UUID, module: str | None = None, is_active: bool | None = None
    ) -> list[SlaPolicy]:
        return await self.repo.list_sla_policies(tenant_id, module=module, is_active=is_active)

    async def update_sla_policy(
        self, tenant_id: UUID, policy_id: UUID, dto: SlaPolicyUpdate, actor_id: UUID | None = None
    ) -> SlaPolicy:
        p = await self.get_sla_policy(tenant_id, policy_id)
        if dto.name is not None:
            p.name = dto.name
        if dto.target_duration_minutes is not None:
            p.target_duration_minutes = dto.target_duration_minutes
        if dto.warning_threshold_percentage is not None:
            p.warning_threshold_percentage = dto.warning_threshold_percentage
        if dto.business_hours_only is not None:
            p.business_hours_only = dto.business_hours_only
        if dto.business_start_hour is not None:
            p.business_start_hour = dto.business_start_hour
        if dto.business_end_hour is not None:
            p.business_end_hour = dto.business_end_hour
        if dto.escalation_queue_id is not None:
            p.escalation_queue_id = dto.escalation_queue_id
        if dto.escalation_role is not None:
            p.escalation_role = dto.escalation_role
        if dto.is_active is not None:
            p.is_active = dto.is_active

        updated = await self.repo.update_sla_policy(p)
        await self.db.flush()
        return updated

    # -------------------------------------------------------------------------
    # 2. SLA INSTANCE CLOCK INITIALIZATION
    # -------------------------------------------------------------------------

    async def initialize_case_sla(
        self, tenant_id: UUID, case: Case, case_type: CaseType | None = None
    ) -> SlaInstance:
        """Initialize operational SLA instance clock for a new case."""
        now = datetime.now(UTC)
        module = case_type.module if case_type else "GENERAL"
        policy = await self.repo.find_matching_sla_policy(
            tenant_id, module=module, priority=case.priority, case_type_code=case.case_type_code
        )

        if policy:
            target_minutes = policy.target_duration_minutes
            warn_pct = policy.warning_threshold_percentage
            policy_id = policy.id
        elif case_type and case_type.sla_hours:
            target_minutes = case_type.sla_hours * 60
            warn_pct = 75
            policy_id = None
        else:
            target_minutes = PRIORITY_FALLBACK_MINUTES.get(case.priority, 2880)
            warn_pct = 75
            policy_id = None

        due_at = case.due_at or (now + timedelta(minutes=target_minutes))
        warning_minutes = int(target_minutes * (warn_pct / 100.0))
        warning_at = now + timedelta(minutes=warning_minutes)

        if not case.due_at:
            case.due_at = due_at

        instance = SlaInstance(
            tenant_id=tenant_id,
            sla_policy_id=policy_id,
            case_id=case.id,
            task_id=None,
            started_at=now,
            due_at=due_at,
            warning_at=warning_at,
            status=SlaStatus.ON_TRACK,
            breached=False,
            escalated=False,
        )
        created = await self.repo.create_sla_instance(instance)
        return created

    async def initialize_task_sla(self, tenant_id: UUID, task: HumanTask) -> SlaInstance:
        """Initialize operational SLA instance clock for a human task."""
        now = datetime.now(UTC)
        policy = await self.repo.find_matching_sla_policy(
            tenant_id, module="GENERAL", priority=task.priority
        )

        target_minutes = (
            policy.target_duration_minutes
            if policy
            else PRIORITY_FALLBACK_MINUTES.get(task.priority, 1440)
        )
        warn_pct = policy.warning_threshold_percentage if policy else 75

        due_at = task.due_at or (now + timedelta(minutes=target_minutes))
        warning_at = now + timedelta(minutes=int(target_minutes * (warn_pct / 100.0)))

        if not task.due_at:
            task.due_at = due_at

        instance = SlaInstance(
            tenant_id=tenant_id,
            sla_policy_id=policy.id if policy else None,
            case_id=task.case_id,
            task_id=task.id,
            started_at=now,
            due_at=due_at,
            warning_at=warning_at,
            status=SlaStatus.ON_TRACK,
            breached=False,
            escalated=False,
        )
        return await self.repo.create_sla_instance(instance)

    async def mark_task_sla_completed(self, tenant_id: UUID, task_id: UUID) -> None:
        inst = await self.repo.get_sla_instance_by_task(tenant_id, task_id)
        if inst and inst.status in [SlaStatus.ON_TRACK, SlaStatus.AT_RISK]:
            now = datetime.now(UTC)
            inst.completed_at = now
            inst.status = SlaStatus.MET
            started = _ensure_utc(inst.started_at)
            inst.elapsed_minutes = int((now - started).total_seconds() / 60.0)
            await self.db.flush()

    async def mark_case_sla_completed(self, tenant_id: UUID, case_id: UUID) -> None:
        inst = await self.repo.get_sla_instance_by_case(tenant_id, case_id)
        if inst and inst.status in [SlaStatus.ON_TRACK, SlaStatus.AT_RISK]:
            now = datetime.now(UTC)
            inst.completed_at = now
            inst.status = SlaStatus.MET
            started = _ensure_utc(inst.started_at)
            inst.elapsed_minutes = int((now - started).total_seconds() / 60.0)
            await self.db.flush()

    # -------------------------------------------------------------------------
    # 3. BACKGROUND SWEEP & ESCALATION
    # -------------------------------------------------------------------------

    async def check_deadlines_and_escalate(self, tenant_id: UUID) -> dict[str, int]:
        """Sweep active SLA instances, detect breaches, and trigger escalations."""
        now = datetime.now(UTC)
        instances = await self.repo.list_active_sla_instances(tenant_id)

        breached_count = 0
        warning_count = 0
        escalated_count = 0

        for inst in instances:
            due_at = _ensure_utc(inst.due_at)
            warning_at = _ensure_utc(inst.warning_at) if inst.warning_at else None

            # Check Breach
            if now >= due_at:
                inst.status = SlaStatus.BREACHED
                inst.breached = True
                breached_count += 1

                # Update associated Case if any
                if inst.case_id:
                    case = await self.repo.get_case_by_id(tenant_id, inst.case_id, for_update=True)
                    if case and case.status not in [CaseStatus.RESOLVED, CaseStatus.CLOSED]:
                        case.sla_breached = True
                        case.status = CaseStatus.ESCALATED
                        await self.repo.add_timeline_event(
                            tenant_id=tenant_id,
                            case_id=case.id,
                            event_type=CaseTimelineEventType.ESCALATED,
                            title=f"SLA breached on case {case.case_number}. Escalated.",
                            details_json={
                                "due_at": due_at.isoformat(),
                                "breached_at": now.isoformat(),
                            },
                        )

                        # Queue escalation if policy defines an escalation queue
                        if inst.sla_policy_id:
                            pol = await self.repo.get_sla_policy(tenant_id, inst.sla_policy_id)
                            if pol and pol.escalation_queue_id:
                                case.assigned_queue_id = pol.escalation_queue_id

                        inst.escalated = True
                        inst.escalated_at = now
                        escalated_count += 1

                # Update associated Task if any
                if inst.task_id:
                    task = await self.repo.get_task_by_id(tenant_id, inst.task_id, for_update=True)
                    if task and task.status not in [TaskStatus.COMPLETED, TaskStatus.REJECTED]:
                        task.sla_breached = True
                        task.status = TaskStatus.ESCALATED
                        await self.repo.add_timeline_event(
                            tenant_id=tenant_id,
                            case_id=task.case_id,
                            task_id=task.id,
                            event_type=CaseTimelineEventType.ESCALATED,
                            title=f"SLA breached on task: {task.title}",
                            details_json={"due_at": due_at.isoformat()},
                        )

                audit = build_audit_entry(
                    tenant_id=tenant_id,
                    action=AuditEventCategory.SLA_BREACHED,
                    entity_type="sla_instance",
                    entity_id=inst.id,
                    new_values_json={"status": SlaStatus.BREACHED, "due_at": due_at.isoformat()},
                    business_context="SLA breach threshold reached.",
                )
                self.db.add(audit)

            # Check Warning
            elif warning_at and now >= warning_at:
                if inst.status != SlaStatus.AT_RISK:
                    inst.status = SlaStatus.AT_RISK
                    warning_count += 1

        await self.db.flush()
        return {
            "breached": breached_count,
            "warned": warning_count,
            "escalated": escalated_count,
        }
