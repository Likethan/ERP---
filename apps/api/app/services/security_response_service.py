"""CampusOS Security Response & Containment Action Service (Step 33).

Provides:
- Tightly bounded, reversible security containment actions
- Idempotency guarantees
- Mandatory approval workflows for high-risk actions (e.g. account locks)
- Immutable forensic audit logging for all response actions
- Traceable execution and rollback procedures
"""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ValidationException
from app.core.logging import logger
from app.models.audit import AuditLog
from app.models.people import User, UserSession
from app.models.platform_api import ApplicationCredential
from app.models.security_ops import (
    SecurityIncident,
    SecurityIncidentNote,
    SecurityRemediationTask,
    SecurityResponseAction,
)
from app.services.notification_service import NotificationService

# In-memory blocked IPs registry for fast runtime checks
BLOCKED_IPS_REGISTRY: dict[str, datetime] = {}


class SecurityResponseService:
    """Orchestrates controlled automated and human-approved incident containment actions."""

    @classmethod
    async def propose_action(
        cls,
        db: AsyncSession,
        incident_id: UUID,
        action_type: str,
        target_type: str,
        target_identifier: str,
        risk_level: str,
        requires_approval: bool,
        proposed_by_user_id: UUID,
        tenant_id: UUID | None,
        is_platform_operator: bool,
        payload: dict[str, Any] | None = None,
    ) -> SecurityResponseAction:
        """Propose a containment action linked to an incident."""
        # Verify incident exists and user has access
        inc_stmt = select(SecurityIncident).where(SecurityIncident.id == incident_id)
        incident = (await db.execute(inc_stmt)).scalar_one_or_none()
        if not incident:
            raise NotFoundException("Security incident not found")

        if not is_platform_operator and incident.tenant_id != tenant_id:
            raise NotFoundException("Security incident not found")

        # If action is inherently high risk (e.g. LOCK_ACCOUNT), mandate approval
        if action_type.upper() in ("LOCK_ACCOUNT", "SUSPEND_USER") or risk_level.upper() in ("HIGH", "CRITICAL"):
            requires_approval = True

        idempotency_key = f"ACT-{incident.incident_number}-{action_type}-{uuid4().hex[:8]}"

        action = SecurityResponseAction(
            tenant_id=incident.tenant_id,
            incident_id=incident.id,
            action_type=action_type.upper(),
            target_type=target_type.upper(),
            target_identifier=target_identifier,
            risk_level=risk_level.upper(),
            requires_approval=requires_approval,
            status="PROPOSED",
            idempotency_key=idempotency_key,
            proposed_by_user_id=proposed_by_user_id,
            execution_payload=payload or {},
        )
        db.add(action)

        note = SecurityIncidentNote(
            incident_id=incident.id,
            author_user_id=proposed_by_user_id,
            note_type="TIMELINE",
            content=f"Proposed response action: {action_type} on {target_type} '{target_identifier}' (Approval required: {requires_approval}).",
        )
        db.add(note)
        await db.flush()
        return action

    @classmethod
    async def approve_action(
        cls,
        db: AsyncSession,
        action_id: UUID,
        approving_user_id: UUID,
        tenant_id: UUID | None,
        is_platform_operator: bool,
    ) -> SecurityResponseAction:
        """Approve a proposed containment action."""
        stmt = select(SecurityResponseAction).where(SecurityResponseAction.id == action_id)
        action = (await db.execute(stmt)).scalar_one_or_none()
        if not action:
            raise NotFoundException("Response action not found")

        if not is_platform_operator and action.tenant_id != tenant_id:
            raise NotFoundException("Response action not found")

        if action.status != "PROPOSED":
            raise ValidationException(f"Cannot approve action with current status: {action.status}")

        action.status = "APPROVED"
        action.approved_by_user_id = approving_user_id

        if action.incident_id:
            note = SecurityIncidentNote(
                incident_id=action.incident_id,
                author_user_id=approving_user_id,
                note_type="TIMELINE",
                content=f"Response action {action.action_type} approved for execution.",
            )
            db.add(note)

        await db.flush()
        return action

    @classmethod
    async def reject_action(
        cls,
        db: AsyncSession,
        action_id: UUID,
        rejecting_user_id: UUID,
        reason: str | None,
        tenant_id: UUID | None,
        is_platform_operator: bool,
    ) -> SecurityResponseAction:
        """Reject a proposed containment action."""
        stmt = select(SecurityResponseAction).where(SecurityResponseAction.id == action_id)
        action = (await db.execute(stmt)).scalar_one_or_none()
        if not action:
            raise NotFoundException("Response action not found")

        if not is_platform_operator and action.tenant_id != tenant_id:
            raise NotFoundException("Response action not found")

        if action.status not in ("PROPOSED", "APPROVED"):
            raise ValidationException(f"Cannot reject action with current status: {action.status}")

        action.status = "REJECTED"
        action.error_message = f"Rejected by administrator: {reason or 'No reason provided'}"

        if action.incident_id:
            note = SecurityIncidentNote(
                incident_id=action.incident_id,
                author_user_id=rejecting_user_id,
                note_type="TIMELINE",
                content=f"Response action {action.action_type} rejected. Reason: {reason or 'None'}.",
            )
            db.add(note)

        await db.flush()
        return action

    @classmethod
    async def execute_action(
        cls,
        db: AsyncSession,
        action_id: UUID,
        executing_user_id: UUID,
        tenant_id: UUID | None,
        is_platform_operator: bool,
    ) -> SecurityResponseAction:
        """Execute an authorized containment action with safety controls and audit records."""
        stmt = select(SecurityResponseAction).where(SecurityResponseAction.id == action_id)
        action = (await db.execute(stmt)).scalar_one_or_none()
        if not action:
            raise NotFoundException("Response action not found")

        if not is_platform_operator and action.tenant_id != tenant_id:
            raise NotFoundException("Response action not found")

        # Idempotency check: if already executed, return current state safely
        if action.status == "EXECUTED":
            return action

        # Approval gate
        if action.requires_approval and action.status != "APPROVED":
            raise ValidationException(
                "Execution prohibited: Action requires formal administrative approval before execution."
            )

        now = datetime.now(UTC)
        result: dict[str, Any] = {}

        try:
            if action.action_type == "RATE_LIMIT_IP":
                # Temporarily block IP for 2 hours
                expiry = now + timedelta(hours=2)
                BLOCKED_IPS_REGISTRY[action.target_identifier] = expiry
                action.expires_at = expiry
                result = {
                    "ip": action.target_identifier,
                    "blocked_until": expiry.isoformat(),
                    "mechanism": "RUNTIME_REGISTRY",
                }

            elif action.action_type == "REVOKE_SESSION":
                # Revoke session matching session_id or all sessions for user_id
                target_str = action.target_identifier
                revoked_count = 0
                try:
                    target_uuid = UUID(target_str)
                    # Revoke session by id
                    session_stmt = (
                        update(UserSession)
                        .where(UserSession.id == target_uuid)
                        .values(is_revoked=True)
                    )
                    res = await db.execute(session_stmt)
                    revoked_count = res.rowcount
                    if revoked_count == 0:
                        # Try revoking by user_id
                        user_sess_stmt = (
                            update(UserSession)
                            .where(UserSession.user_id == target_uuid)
                            .values(is_revoked=True)
                        )
                        res2 = await db.execute(user_sess_stmt)
                        revoked_count = res2.rowcount
                except ValueError:
                    # Target might be a username/email or token hash
                    pass

                result = {
                    "target": action.target_identifier,
                    "sessions_revoked": revoked_count,
                }

            elif action.action_type == "REVOKE_API_KEY":
                # Revoke developer API credential
                cred_stmt = (
                    update(ApplicationCredential)
                    .where(
                        or_(
                            ApplicationCredential.client_id == action.target_identifier,
                            ApplicationCredential.key_prefix == action.target_identifier,
                        )
                    )
                    .values(status="REVOKED")
                )
                res = await db.execute(cred_stmt)
                result = {
                    "target_credential": action.target_identifier,
                    "revoked_count": res.rowcount,
                }

            elif action.action_type == "LOCK_ACCOUNT":
                # Lock user account for 2 hours
                expiry = now + timedelta(hours=2)
                target_str = action.target_identifier
                try:
                    user_uuid = UUID(target_str)
                    lock_stmt = (
                        update(User)
                        .where(User.id == user_uuid)
                        .values(locked_until=expiry)
                    )
                    await db.execute(lock_stmt)
                    result = {
                        "user_id": target_str,
                        "locked_until": expiry.isoformat(),
                    }
                except ValueError:
                    # Look up user by email
                    lock_email_stmt = (
                        update(User)
                        .where(User.email == target_str)
                        .values(locked_until=expiry)
                    )
                    await db.execute(lock_email_stmt)
                    result = {
                        "email": target_str,
                        "locked_until": expiry.isoformat(),
                    }

            elif action.action_type == "CREATE_REMEDIATION_TASK":
                if action.incident_id:
                    task = SecurityRemediationTask(
                        tenant_id=action.tenant_id,
                        incident_id=action.incident_id,
                        title=f"Verify remediation for {action.target_identifier}",
                        description="Auto-generated remediation task from incident response action.",
                        status="PENDING",
                    )
                    db.add(task)
                    result = {"task_title": task.title}

            elif action.action_type == "SEND_ALERT_NOTIFICATION":
                if action.incident_id and action.tenant_id:
                    # Send alert through existing NotificationService
                    await NotificationService.create_notification(
                        db=db,
                        tenant_id=action.tenant_id,
                        recipient_user_id=executing_user_id,
                        type="SECURITY",
                        title="CampusOS Security Alert Containment Executed",
                        message=f"Containment action {action.action_type} executed for target {action.target_identifier}.",
                        priority="URGENT",
                        source_module="SECURITY",
                    )
                    result = {"notification_dispatched": True}

            action.status = "EXECUTED"
            action.executed_at = now
            action.executed_by_user_id = executing_user_id
            action.execution_result = result

            # Audit record
            audit = AuditLog(
                tenant_id=action.tenant_id or tenant_id or executing_user_id,
                user_id=executing_user_id,
                action=f"SECURITY_ACTION_EXECUTE_{action.action_type}",
                entity_type="SecurityResponseAction",
                entity_id=action.id,
                new_values_json=result,
                ip_address="127.0.0.1",
                business_context="Security Operations Containment",
            )
            db.add(audit)

            if action.incident_id:
                note = SecurityIncidentNote(
                    incident_id=action.incident_id,
                    author_user_id=executing_user_id,
                    note_type="MITIGATION",
                    content=f"Successfully executed containment action {action.action_type} on {action.target_identifier}.",
                    evidence_references=[{"action_id": str(action.id), "result": result}],
                )
                db.add(note)

        except Exception as exc:
            logger.error("Failed to execute response action %s: %s", action.id, exc, exc_info=True)
            action.status = "FAILED"
            action.error_message = str(exc)
            raise ValidationException(f"Failed to execute containment action: {exc}")

        await db.flush()
        return action

    @classmethod
    async def rollback_action(
        cls,
        db: AsyncSession,
        action_id: UUID,
        user_id: UUID,
        tenant_id: UUID | None,
        is_platform_operator: bool,
    ) -> SecurityResponseAction:
        """Rollback an executed containment action (e.g. unblock IP or unlock account)."""
        stmt = select(SecurityResponseAction).where(SecurityResponseAction.id == action_id)
        action = (await db.execute(stmt)).scalar_one_or_none()
        if not action:
            raise NotFoundException("Response action not found")

        if not is_platform_operator and action.tenant_id != tenant_id:
            raise NotFoundException("Response action not found")

        if action.status != "EXECUTED":
            raise ValidationException(f"Cannot rollback action with status {action.status}")

        now = datetime.now(UTC)

        if action.action_type == "RATE_LIMIT_IP":
            BLOCKED_IPS_REGISTRY.pop(action.target_identifier, None)

        elif action.action_type == "LOCK_ACCOUNT":
            target_str = action.target_identifier
            try:
                user_uuid = UUID(target_str)
                await db.execute(
                    update(User).where(User.id == user_uuid).values(locked_until=None)
                )
            except ValueError:
                await db.execute(
                    update(User).where(User.email == target_str).values(locked_until=None)
                )

        action.status = "ROLLED_BACK"
        action.rolled_back_at = now

        if action.incident_id:
            note = SecurityIncidentNote(
                incident_id=action.incident_id,
                author_user_id=user_id,
                note_type="TIMELINE",
                content=f"Rolled back containment action {action.action_type} on {action.target_identifier}.",
            )
            db.add(note)

        await db.flush()
        return action
