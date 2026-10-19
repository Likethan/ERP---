"""CampusOS Security Operations & Incident Management Service (Step 33).

Provides:
- Tenant-isolated security incident lifecycle management
- Valid state machine transitions with forensic audit trail
- Responder assignment, investigation notes, and remediation tasks
- Real-time Security Operations Center (SOC) dashboard metrics
- Server-side threat detection rule configuration
"""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundException, ValidationException
from app.core.logging import logger
from app.models.audit import AuditLog
from app.models.security_ops import (
    SecurityDetection,
    SecurityDetectionRuleConfig,
    SecurityIncident,
    SecurityIncidentNote,
    SecurityRemediationTask,
    SecurityResponseAction,
)

# Valid state machine transitions
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "NEW": {"TRIAGED", "INVESTIGATING", "CLOSED"},
    "TRIAGED": {"INVESTIGATING", "CLOSED"},
    "INVESTIGATING": {"CONTAINED", "REMEDIATING", "RESOLVED", "CLOSED"},
    "CONTAINED": {"REMEDIATING", "INVESTIGATING", "RESOLVED", "CLOSED"},
    "REMEDIATING": {"RESOLVED", "INVESTIGATING", "CLOSED"},
    "RESOLVED": {"CLOSED", "REOPENED"},
    "CLOSED": {"REOPENED"},
    "REOPENED": {"INVESTIGATING", "TRIAGED"},
}


class SecurityOpsService:
    """Enterprise Security Operations and Incident Management Service."""

    # -------------------------------------------------------------------------
    # 1. INCIDENTS MANAGEMENT
    # -------------------------------------------------------------------------
    @classmethod
    async def list_incidents(
        cls,
        db: AsyncSession,
        tenant_id: UUID | None,
        is_platform_operator: bool,
        status: str | None = None,
        severity: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[SecurityIncident], int]:
        """List security incidents respecting strict tenant isolation."""
        stmt = select(SecurityIncident)
        count_stmt = select(func.count(SecurityIncident.id))

        filters = []
        if not is_platform_operator:
            # Tenant isolation: strictly filter by tenant_id
            if tenant_id is None:
                return [], 0
            filters.append(SecurityIncident.tenant_id == tenant_id)
        else:
            # Platform operator can optionally filter by tenant_id
            if tenant_id is not None:
                filters.append(SecurityIncident.tenant_id == tenant_id)

        if status:
            filters.append(SecurityIncident.status == status.upper())
        if severity:
            filters.append(SecurityIncident.severity == severity.upper())

        if filters:
            stmt = stmt.where(and_(*filters))
            count_stmt = count_stmt.where(and_(*filters))

        total = (await db.execute(count_stmt)).scalar() or 0
        stmt = stmt.order_by(SecurityIncident.created_at.desc()).offset(skip).limit(limit)
        results = (await db.execute(stmt)).scalars().all()
        return list(results), total

    @classmethod
    async def get_incident(
        cls,
        db: AsyncSession,
        incident_id: UUID,
        tenant_id: UUID | None,
        is_platform_operator: bool,
    ) -> SecurityIncident:
        """Retrieve full incident details with notes, detections, actions, and tasks."""
        stmt = (
            select(SecurityIncident)
            .where(SecurityIncident.id == incident_id)
            .options(
                selectinload(SecurityIncident.detections),
                selectinload(SecurityIncident.notes),
                selectinload(SecurityIncident.actions),
                selectinload(SecurityIncident.remediation_tasks),
            )
        )
        incident = (await db.execute(stmt)).scalar_one_or_none()
        if not incident:
            raise NotFoundException("Security incident not found")

        # Tenant boundary check
        if not is_platform_operator and incident.tenant_id != tenant_id:
            raise NotFoundException("Security incident not found")

        return incident

    @classmethod
    async def transition_status(
        cls,
        db: AsyncSession,
        incident_id: UUID,
        new_status: str,
        user_id: UUID,
        tenant_id: UUID | None,
        is_platform_operator: bool,
        reason: str | None = None,
        closure_summary: str | None = None,
    ) -> SecurityIncident:
        """Execute validated state machine transition for an incident."""
        incident = await cls.get_incident(db, incident_id, tenant_id, is_platform_operator)
        current_status = incident.status.upper()
        target_status = new_status.upper()

        if target_status not in ALLOWED_TRANSITIONS.get(current_status, set()):
            raise ValidationException(
                f"Invalid status transition from {current_status} to {target_status}. "
                f"Permitted next states: {', '.join(ALLOWED_TRANSITIONS.get(current_status, set()))}"
            )

        now = datetime.now(UTC)
        incident.status = target_status

        # Set lifecycle timestamps
        if target_status == "TRIAGED" and not incident.triaged_at:
            incident.triaged_at = now
        elif target_status == "CONTAINED" and not incident.contained_at:
            incident.contained_at = now
        elif target_status == "RESOLVED":
            incident.resolved_at = now
            incident.resolved_by_user_id = user_id
            if reason:
                incident.resolution_reason = reason
        elif target_status == "CLOSED":
            incident.closed_at = now
            if closure_summary:
                incident.closure_summary = closure_summary
        elif target_status == "REOPENED":
            incident.resolved_at = None
            incident.closed_at = None

        # Add append-only chronological transition note
        note_content = f"Status transitioned from {current_status} to {target_status}."
        if reason:
            note_content += f" Reason: {reason}."
        if closure_summary:
            note_content += f" Closure Summary: {closure_summary}."

        note = SecurityIncidentNote(
            incident_id=incident.id,
            author_user_id=user_id,
            note_type="STATUS_CHANGE",
            content=note_content,
        )
        db.add(note)

        # Audit record
        audit = AuditLog(
            tenant_id=incident.tenant_id or tenant_id or incident.id,
            user_id=user_id,
            action="SECURITY_INCIDENT_STATUS_CHANGE",
            entity_type="SecurityIncident",
            entity_id=incident.id,
            old_values_json={"status": current_status},
            new_values_json={"status": target_status, "reason": reason},
            ip_address="127.0.0.1",
            business_context="Security Operations Center",
        )
        db.add(audit)
        await db.flush()
        return await cls.get_incident(db, incident.id, tenant_id, is_platform_operator)

    @classmethod
    async def assign_responder(
        cls,
        db: AsyncSession,
        incident_id: UUID,
        assigned_to_user_id: UUID | None,
        actor_user_id: UUID,
        tenant_id: UUID | None,
        is_platform_operator: bool,
    ) -> SecurityIncident:
        """Assign or reassign an incident responder."""
        incident = await cls.get_incident(db, incident_id, tenant_id, is_platform_operator)
        old_assignee = incident.assigned_to_user_id
        incident.assigned_to_user_id = assigned_to_user_id

        note = SecurityIncidentNote(
            incident_id=incident.id,
            author_user_id=actor_user_id,
            note_type="TIMELINE",
            content=f"Incident assigned to user {assigned_to_user_id or 'Unassigned'}.",
        )
        db.add(note)
        await db.flush()
        return await cls.get_incident(db, incident.id, tenant_id, is_platform_operator)

    @classmethod
    async def add_note(
        cls,
        db: AsyncSession,
        incident_id: UUID,
        author_user_id: UUID,
        content: str,
        note_type: str = "INVESTIGATION",
        evidence_references: list[dict[str, Any]] | None = None,
        tenant_id: UUID | None = None,
        is_platform_operator: bool = False,
    ) -> SecurityIncidentNote:
        """Add forensic investigation note to an incident."""
        incident = await cls.get_incident(db, incident_id, tenant_id, is_platform_operator)
        note = SecurityIncidentNote(
            incident_id=incident.id,
            author_user_id=author_user_id,
            note_type=note_type.upper(),
            content=content,
            evidence_references=evidence_references or [],
        )
        db.add(note)
        await db.flush()
        return note

    # -------------------------------------------------------------------------
    # 2. REMEDIATION TASKS
    # -------------------------------------------------------------------------
    @classmethod
    async def create_remediation_task(
        cls,
        db: AsyncSession,
        incident_id: UUID,
        title: str,
        description: str | None,
        assigned_to_user_id: UUID | None,
        due_at: datetime | None,
        actor_user_id: UUID,
        tenant_id: UUID | None,
        is_platform_operator: bool,
    ) -> SecurityRemediationTask:
        """Create a verification remediation task linked to an incident."""
        incident = await cls.get_incident(db, incident_id, tenant_id, is_platform_operator)
        task = SecurityRemediationTask(
            tenant_id=incident.tenant_id,
            incident_id=incident.id,
            title=title,
            description=description,
            assigned_to_user_id=assigned_to_user_id,
            due_at=due_at,
            status="PENDING",
        )
        db.add(task)

        note = SecurityIncidentNote(
            incident_id=incident.id,
            author_user_id=actor_user_id,
            note_type="TIMELINE",
            content=f"Created remediation task: '{title}'.",
        )
        db.add(note)
        await db.flush()
        return task

    @classmethod
    async def update_remediation_task_status(
        cls,
        db: AsyncSession,
        task_id: UUID,
        new_status: str,
        actor_user_id: UUID,
        tenant_id: UUID | None,
        is_platform_operator: bool,
    ) -> SecurityRemediationTask:
        """Update remediation task status (PENDING, IN_PROGRESS, COMPLETED, CANCELLED)."""
        stmt = select(SecurityRemediationTask).where(SecurityRemediationTask.id == task_id)
        task = (await db.execute(stmt)).scalar_one_or_none()
        if not task:
            raise NotFoundException("Remediation task not found")

        if not is_platform_operator and task.tenant_id != tenant_id:
            raise NotFoundException("Remediation task not found")

        valid_states = {"PENDING", "IN_PROGRESS", "COMPLETED", "CANCELLED"}
        target = new_status.upper()
        if target not in valid_states:
            raise ValidationException(f"Invalid task status: {new_status}. Allowed: {valid_states}")

        task.status = target
        if target == "COMPLETED":
            task.completed_at = datetime.now(UTC)

        await db.flush()
        return task

    # -------------------------------------------------------------------------
    # 3. DETECTIONS & SOC OVERVIEW
    # -------------------------------------------------------------------------
    @classmethod
    async def list_detections(
        cls,
        db: AsyncSession,
        tenant_id: UUID | None,
        is_platform_operator: bool,
        rule_id: str | None = None,
        severity: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[SecurityDetection], int]:
        """Query security detections with tenant isolation."""
        stmt = select(SecurityDetection)
        count_stmt = select(func.count(SecurityDetection.id))

        filters = []
        if not is_platform_operator:
            if tenant_id is None:
                return [], 0
            filters.append(SecurityDetection.tenant_id == tenant_id)
        else:
            if tenant_id is not None:
                filters.append(SecurityDetection.tenant_id == tenant_id)

        if rule_id:
            filters.append(SecurityDetection.rule_id == rule_id)
        if severity:
            filters.append(SecurityDetection.severity == severity.upper())

        if filters:
            stmt = stmt.where(and_(*filters))
            count_stmt = count_stmt.where(and_(*filters))

        total = (await db.execute(count_stmt)).scalar() or 0
        stmt = stmt.order_by(SecurityDetection.last_seen_at.desc()).offset(skip).limit(limit)
        results = (await db.execute(stmt)).scalars().all()
        return list(results), total

    @classmethod
    async def get_soc_overview(
        cls,
        db: AsyncSession,
        tenant_id: UUID | None,
        is_platform_operator: bool,
    ) -> dict[str, Any]:
        """Aggregate operational Security Operations Center metrics."""
        inc_filters = []
        det_filters = []
        act_filters = []

        if not is_platform_operator:
            inc_filters.append(SecurityIncident.tenant_id == tenant_id)
            det_filters.append(SecurityDetection.tenant_id == tenant_id)
            act_filters.append(SecurityResponseAction.tenant_id == tenant_id)

        # 1. Open incidents by severity
        open_statuses = ["NEW", "TRIAGED", "INVESTIGATING", "CONTAINED", "REMEDIATING"]
        inc_stmt = (
            select(SecurityIncident.severity, func.count(SecurityIncident.id))
            .where(
                and_(
                    SecurityIncident.status.in_(open_statuses),
                    *inc_filters,
                )
            )
            .group_by(SecurityIncident.severity)
        )
        sev_counts = dict((await db.execute(inc_stmt)).all())

        # 2. Total active detections in last 24 hours
        yesterday = datetime.now(UTC) - timedelta(hours=24)
        det_stmt = select(func.count(SecurityDetection.id)).where(
            and_(
                SecurityDetection.last_seen_at >= yesterday,
                *det_filters,
            )
        )
        recent_detections = (await db.execute(det_stmt)).scalar() or 0

        # 3. Actions pending approval
        act_stmt = select(func.count(SecurityResponseAction.id)).where(
            and_(
                SecurityResponseAction.status == "PROPOSED",
                SecurityResponseAction.requires_approval == True,
                *act_filters,
            )
        )
        pending_actions = (await db.execute(act_stmt)).scalar() or 0

        # 4. Oldest unresolved incident age in hours
        oldest_stmt = (
            select(SecurityIncident.created_at)
            .where(
                and_(
                    SecurityIncident.status.in_(open_statuses),
                    *inc_filters,
                )
            )
            .order_by(SecurityIncident.created_at.asc())
            .limit(1)
        )
        oldest_created = (await db.execute(oldest_stmt)).scalar_one_or_none()
        oldest_age_hours = 0.0
        if oldest_created:
            if oldest_created.tzinfo is None:
                oldest_created = oldest_created.replace(tzinfo=UTC)
            oldest_age_hours = max(
                0.0,
                (datetime.now(UTC) - oldest_created).total_seconds() / 3600.0,
            )

        return {
            "critical_incidents": sev_counts.get("CRITICAL", 0),
            "high_incidents": sev_counts.get("HIGH", 0),
            "medium_incidents": sev_counts.get("MEDIUM", 0),
            "low_incidents": sev_counts.get("LOW", 0),
            "recent_detections_24h": recent_detections,
            "pending_action_approvals": pending_actions,
            "oldest_unresolved_hours": round(oldest_age_hours, 1),
            "timestamp": datetime.now(UTC).isoformat(),
        }

    # -------------------------------------------------------------------------
    # 4. DETECTION RULES CONFIGURATION
    # -------------------------------------------------------------------------
    @classmethod
    async def list_rules(cls, db: AsyncSession) -> list[SecurityDetectionRuleConfig]:
        """List configured threat detection rules."""
        stmt = select(SecurityDetectionRuleConfig).order_by(SecurityDetectionRuleConfig.rule_id.asc())
        return list((await db.execute(stmt)).scalars().all())

    @classmethod
    async def configure_rule(
        cls,
        db: AsyncSession,
        rule_id: str,
        is_enabled: bool | None = None,
        threshold: int | None = None,
        evaluation_window_seconds: int | None = None,
        severity: str | None = None,
    ) -> SecurityDetectionRuleConfig:
        """Update or create server-side rule configuration."""
        stmt = select(SecurityDetectionRuleConfig).where(SecurityDetectionRuleConfig.rule_id == rule_id)
        config = (await db.execute(stmt)).scalar_one_or_none()
        if not config:
            raise NotFoundException(f"Detection rule configuration '{rule_id}' not found")

        if is_enabled is not None:
            config.is_enabled = is_enabled
        if threshold is not None:
            config.threshold = threshold
        if evaluation_window_seconds is not None:
            config.evaluation_window_seconds = evaluation_window_seconds
        if severity is not None:
            config.severity = severity.upper()

        await db.flush()
        return config
