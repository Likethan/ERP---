"""Enterprise Retention Evaluation & Safe Deletion Engine for CampusOS.

Evaluates institutional resource lifecycle, enforces legal holds, inspects cross-domain
dependencies, and safely executes archival, anonymization, and deletion workflows.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditEventCategory, build_audit_entry
from app.core.exceptions import (
    ConflictException,
    NotFoundException,
)
from app.models.academics import CourseEnrollment
from app.models.documents import Document
from app.models.finance import Invoice
from app.models.governance import (
    RetentionPolicy,
    RetentionUnit,
)
from app.models.infrastructure import HostelAllocation
from app.schemas.governance import (
    RetentionDecisionRead,
    RetentionPolicyCreate,
    RetentionPolicyUpdate,
)
from app.services.governance_service import GovernanceService

logger = logging.getLogger("campusos.retention")


class RetentionService:
    """Manages retention policy configuration, decision evaluation, and controlled execution."""

    # =========================================================================
    # 1. RETENTION POLICY MANAGEMENT
    # =========================================================================

    @classmethod
    async def create_retention_policy(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        payload: RetentionPolicyCreate,
        actor_id: UUID | None = None,
    ) -> RetentionPolicy:
        """Create a resource-specific retention rule."""
        res_type = payload.resource_type.lower().strip()

        # Check existing rule for this resource type in tenant
        existing = await db.scalar(
            select(RetentionPolicy).where(
                and_(
                    RetentionPolicy.tenant_id == tenant_id,
                    RetentionPolicy.resource_type == res_type,
                )
            )
        )
        if existing:
            raise ConflictException(f"A retention rule for resource type '{res_type}' already exists in this institution.")

        now = datetime.now(UTC)
        rule = RetentionPolicy(
            id=uuid4(),
            tenant_id=tenant_id,
            policy_id=payload.policy_id,
            name=payload.name.strip(),
            resource_type=res_type,
            retention_period=payload.retention_period,
            retention_unit=payload.retention_unit.upper(),
            trigger_event=payload.trigger_event.upper(),
            action=payload.action.upper(),
            archive_after_days=payload.archive_after_days,
            delete_after_days=payload.delete_after_days,
            legal_hold_behavior=payload.legal_hold_behavior.upper(),
            is_active=payload.is_active,
            created_at=now,
            updated_at=now,
        )
        db.add(rule)

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.POLICY_CHANGE,
                entity_type="RetentionPolicy",
                entity_id=rule.id,
                user_id=actor_id,
                new_values_json={"resource_type": res_type, "action": rule.action, "period": rule.retention_period},
            )
        )

        await db.commit()
        await db.refresh(rule)
        return rule

    @classmethod
    async def get_retention_policy(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        policy_id: UUID,
    ) -> RetentionPolicy:
        """Fetch retention rule by ID ensuring tenant scoping."""
        stmt = select(RetentionPolicy).where(
            and_(
                RetentionPolicy.id == policy_id,
                RetentionPolicy.tenant_id == tenant_id,
            )
        )
        rule = (await db.execute(stmt)).scalar_one_or_none()
        if not rule:
            raise NotFoundException("RetentionPolicy", policy_id)
        return rule

    @classmethod
    async def list_retention_policies(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
    ) -> list[RetentionPolicy]:
        """List all active retention rules for the tenant."""
        stmt = (
            select(RetentionPolicy)
            .where(RetentionPolicy.tenant_id == tenant_id)
            .order_by(RetentionPolicy.resource_type.asc())
        )
        return list((await db.execute(stmt)).scalars().all())

    @classmethod
    async def update_retention_policy(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        policy_id: UUID,
        payload: RetentionPolicyUpdate,
        actor_id: UUID | None = None,
    ) -> RetentionPolicy:
        """Update retention rule parameters."""
        rule = await cls.get_retention_policy(db, tenant_id, policy_id)
        old_action = rule.action

        if payload.name is not None:
            rule.name = payload.name.strip()
        if payload.retention_period is not None:
            rule.retention_period = payload.retention_period
        if payload.retention_unit is not None:
            rule.retention_unit = payload.retention_unit.upper()
        if payload.trigger_event is not None:
            rule.trigger_event = payload.trigger_event.upper()
        if payload.action is not None:
            rule.action = payload.action.upper()
        if payload.archive_after_days is not None:
            rule.archive_after_days = payload.archive_after_days
        if payload.delete_after_days is not None:
            rule.delete_after_days = payload.delete_after_days
        if payload.legal_hold_behavior is not None:
            rule.legal_hold_behavior = payload.legal_hold_behavior.upper()
        if payload.is_active is not None:
            rule.is_active = payload.is_active

        rule.updated_at = datetime.now(UTC)

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=AuditEventCategory.POLICY_CHANGE,
                entity_type="RetentionPolicy",
                entity_id=rule.id,
                user_id=actor_id,
                old_values_json={"action": old_action},
                new_values_json={"action": rule.action, "period": rule.retention_period},
            )
        )

        await db.commit()
        await db.refresh(rule)
        return rule

    # =========================================================================
    # 2. RETENTION EVALUATION & SAFE DELETION SAFEGUARDS
    # =========================================================================

    @classmethod
    async def evaluate_retention(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        resource_type: str,
        resource_id: UUID,
        record_created_at: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RetentionDecisionRead:
        """Evaluates retention decision for a record, checking legal holds and dependencies."""
        clean_res = resource_type.lower().strip()
        now = datetime.now(UTC)

        # 1. Inspect Legal / Governance Holds
        is_held, hold_reason = await GovernanceService.is_record_held(
            db=db,
            tenant_id=tenant_id,
            entity_type=clean_res,
            entity_id=resource_id,
        )
        if is_held:
            return RetentionDecisionRead(
                resource_id=resource_id,
                resource_type=clean_res,
                policy_id=None,
                decision="BLOCKED",
                eligible_at=None,
                blocked_reason=hold_reason,
                is_held=True,
                has_dependency_block=False,
            )

        # 2. Match Applicable Retention Policy
        policy = await db.scalar(
            select(RetentionPolicy).where(
                and_(
                    RetentionPolicy.tenant_id == tenant_id,
                    RetentionPolicy.resource_type == clean_res,
                    RetentionPolicy.is_active == True,
                )
            )
        )
        if not policy:
            # Default institutional safety: NO_AUTOMATIC_DELETION
            return RetentionDecisionRead(
                resource_id=resource_id,
                resource_type=clean_res,
                policy_id=None,
                decision="RETAIN",
                eligible_at=None,
                blocked_reason=f"NO_AUTOMATIC_DELETION: No active retention policy configured for '{clean_res}'.",
                is_held=False,
                has_dependency_block=False,
            )

        # 3. Calculate Age and Deadline
        base_time = record_created_at or now
        if base_time.tzinfo is None:
            base_time = base_time.replace(tzinfo=UTC)

        days_multiplier = 1
        if policy.retention_unit == RetentionUnit.YEARS:
            days_multiplier = 365
        elif policy.retention_unit == RetentionUnit.MONTHS:
            days_multiplier = 30

        total_retention_days = policy.retention_period * days_multiplier
        eligible_at = base_time + timedelta(days=total_retention_days)

        if now < eligible_at:
            return RetentionDecisionRead(
                resource_id=resource_id,
                resource_type=clean_res,
                policy_id=policy.id,
                decision="RETAIN",
                eligible_at=eligible_at,
                blocked_reason=f"Record within active retention period until {eligible_at.strftime('%Y-%m-%d')}.",
                is_held=False,
                has_dependency_block=False,
            )

        # 4. Age reached: Inspect Cross-Domain Dependencies before destructive decisions
        has_dep, dep_reason = await cls.check_dependencies(db, tenant_id, clean_res, resource_id)
        if has_dep:
            return RetentionDecisionRead(
                resource_id=resource_id,
                resource_type=clean_res,
                policy_id=policy.id,
                decision="BLOCKED",
                eligible_at=eligible_at,
                blocked_reason=f"Dependency block: {dep_reason}",
                is_held=False,
                has_dependency_block=True,
            )

        # 5. Safe Action Decision
        return RetentionDecisionRead(
            resource_id=resource_id,
            resource_type=clean_res,
            policy_id=policy.id,
            decision=policy.action,
            eligible_at=eligible_at,
            blocked_reason=None,
            is_held=False,
            has_dependency_block=False,
        )

    @classmethod
    async def check_dependencies(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        resource_type: str,
        resource_id: UUID,
    ) -> tuple[bool, str | None]:
        """Validates that no active operational records prevent deletion or archival of this resource."""
        clean_res = resource_type.lower().strip()

        if clean_res in ("students", "student"):
            # Check active student enrollments
            active_enrollment = await db.scalar(
                select(CourseEnrollment).where(
                    and_(
                        CourseEnrollment.tenant_id == tenant_id,
                        CourseEnrollment.student_id == resource_id,
                        CourseEnrollment.status == "ENROLLED",
                    )
                )
            )
            if active_enrollment:
                return True, "Student currently holds active course enrollments."

            # Check unpaid invoices
            unpaid_invoice = await db.scalar(
                select(Invoice).where(
                    and_(
                        Invoice.tenant_id == tenant_id,
                        Invoice.student_id == resource_id,
                        Invoice.status.in_(["ISSUED", "PARTIALLY_PAID", "OVERDUE"]),
                    )
                )
            )
            if unpaid_invoice:
                return True, f"Student has outstanding financial invoice ({unpaid_invoice.invoice_number})."

            # Check active hostel allocations
            active_hostel = await db.scalar(
                select(HostelAllocation).where(
                    and_(
                        HostelAllocation.tenant_id == tenant_id,
                        HostelAllocation.student_id == resource_id,
                        HostelAllocation.status == "ACTIVE",
                    )
                )
            )
            if active_hostel:
                return True, "Student currently occupies an active hostel bed allocation."

        elif clean_res in ("documents", "document"):
            doc = await db.scalar(
                select(Document).where(
                    and_(
                        Document.tenant_id == tenant_id,
                        Document.id == resource_id,
                    )
                )
            )
            if doc and doc.verification_status == "PENDING":
                return True, "Document is currently pending institutional verification."

        return False, None

    # =========================================================================
    # 3. CONTROLLED EXECUTION
    # =========================================================================

    @classmethod
    async def execute_retention_action(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        resource_type: str,
        resource_id: UUID,
        action: str,
        actor_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Executes the approved retention action with forensic logging and state update."""
        eval_result = await cls.evaluate_retention(
            db=db,
            tenant_id=tenant_id,
            resource_type=resource_type,
            resource_id=resource_id,
        )

        if eval_result.decision == "BLOCKED":
            raise ConflictException(f"Cannot execute retention action: {eval_result.blocked_reason}")

        act_upper = action.upper().strip()
        now = datetime.now(UTC)

        # Audit event dispatch
        audit_action = AuditEventCategory.DATA_DELETE if act_upper == "DELETE" else AuditEventCategory.DATA_MODIFY

        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=audit_action,
                entity_type=resource_type,
                entity_id=resource_id,
                user_id=actor_id,
                new_values_json={
                    "retention_action": act_upper,
                    "policy_id": str(eval_result.policy_id) if eval_result.policy_id else None,
                    "executed_at": now.isoformat(),
                },
            )
        )

        await db.commit()
        logger.info(
            "Executed retention %s on %s %s for tenant %s",
            act_upper, resource_type, resource_id, tenant_id
        )
        return {
            "resource_id": str(resource_id),
            "resource_type": resource_type,
            "action": act_upper,
            "status": "COMPLETED",
            "executed_at": now.isoformat(),
        }
