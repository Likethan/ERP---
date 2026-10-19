"""Tenant Operational Lifecycle State Machine Service for CampusOS (Step 30).

Governs institutional lifecycle transitions, state transition guards,
concurrency safety, idempotent updates, and comprehensive audit history.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditEventCategory, build_audit_entry
from app.core.cache import tenant_cache
from app.core.events import DomainEventEnvelope, OutboxService
from app.core.exceptions import (
    ConflictException,
    InvalidLifecycleTransitionException,
    NotFoundException,
)
from app.models.core import Institution
from app.models.platform_ops import (
    TenantLifecycleStatus,
    TenantLifecycleTransition,
    TenantProvisioningOperation,
    TenantProvisioningStage,
    TenantProvisioningStatus,
)


class TenantLifecycleService:
    """Manages transactional state machine transitions for SaaS tenants."""

    VALID_TRANSITIONS: dict[str, set[str]] = {
        TenantLifecycleStatus.PROVISIONING.value: {
            TenantLifecycleStatus.TRIAL.value,
            TenantLifecycleStatus.ACTIVE.value,
            TenantLifecycleStatus.DEACTIVATED.value,
        },
        TenantLifecycleStatus.TRIAL.value: {
            TenantLifecycleStatus.ACTIVE.value,
            TenantLifecycleStatus.SUSPENDED.value,
            TenantLifecycleStatus.DEACTIVATION_PENDING.value,
            TenantLifecycleStatus.ARCHIVED.value,
        },
        TenantLifecycleStatus.ACTIVE.value: {
            TenantLifecycleStatus.SUSPENDED.value,
            TenantLifecycleStatus.DEACTIVATION_PENDING.value,
            TenantLifecycleStatus.ARCHIVED.value,
        },
        TenantLifecycleStatus.SUSPENDED.value: {
            TenantLifecycleStatus.ACTIVE.value,
            TenantLifecycleStatus.DEACTIVATION_PENDING.value,
            TenantLifecycleStatus.DELETION_PENDING.value,
            TenantLifecycleStatus.ARCHIVED.value,
        },
        TenantLifecycleStatus.DEACTIVATION_PENDING.value: {
            TenantLifecycleStatus.ACTIVE.value,
            TenantLifecycleStatus.DEACTIVATED.value,
            TenantLifecycleStatus.ARCHIVED.value,
        },
        TenantLifecycleStatus.DEACTIVATED.value: {
            TenantLifecycleStatus.ACTIVE.value,
            TenantLifecycleStatus.DELETION_PENDING.value,
            TenantLifecycleStatus.ARCHIVED.value,
        },
        TenantLifecycleStatus.DELETION_PENDING.value: {
            TenantLifecycleStatus.DEACTIVATED.value,
            TenantLifecycleStatus.DELETED.value,
        },
        TenantLifecycleStatus.ARCHIVED.value: {
            TenantLifecycleStatus.ACTIVE.value,
            TenantLifecycleStatus.DELETION_PENDING.value,
        },
        TenantLifecycleStatus.DELETED.value: set(),  # Terminal state
    }

    @classmethod
    async def get_tenant_by_id(cls, db: AsyncSession, tenant_id: UUID) -> Institution:
        """Fetch institution tenant by primary key."""
        stmt = select(Institution).where(Institution.id == tenant_id)
        result = await db.execute(stmt)
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise NotFoundException("Tenant", tenant_id)
        return tenant

    @classmethod
    async def transition_tenant_status(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        target_status: str,
        actor_id: UUID | None,
        actor_email: str | None,
        reason: str,
        correlation_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[Institution, TenantLifecycleTransition]:
        """Execute a guarded, transactional, and audited tenant lifecycle state transition."""
        target_status_upper = target_status.upper()
        corr_uuid = correlation_id if isinstance(correlation_id, UUID) else (UUID(str(correlation_id)) if correlation_id else uuid4())
        corr_str = str(corr_uuid)
        now = datetime.now(UTC)

        stmt = select(Institution).where(Institution.id == tenant_id).with_for_update()
        result = await db.execute(stmt)
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise NotFoundException("Tenant", tenant_id)

        current_status = (tenant.status or TenantLifecycleStatus.ACTIVE.value).upper()

        # Idempotency check: if already in requested state, return gracefully
        if current_status == target_status_upper:
            recent_stmt = (
                select(TenantLifecycleTransition)
                .where(TenantLifecycleTransition.tenant_id == tenant_id)
                .order_by(desc(TenantLifecycleTransition.created_at))
                .limit(1)
            )
            recent_res = await db.execute(recent_stmt)
            existing_trans = recent_res.scalar_one_or_none()
            if not existing_trans:
                existing_trans = TenantLifecycleTransition(
                    tenant_id=tenant_id,
                    from_status=current_status,
                    to_status=current_status,
                    actor_id=actor_id,
                    actor_email=actor_email,
                    reason=f"Idempotent state confirmation: {reason}",
                    correlation_id=corr_uuid,
                    metadata_json=metadata or {},
                )
                db.add(existing_trans)
                await db.flush()
                await db.refresh(existing_trans)
            await db.refresh(tenant)
            return tenant, existing_trans

        # Validate transition matrix
        allowed_targets = cls.VALID_TRANSITIONS.get(current_status, set())
        if target_status_upper not in allowed_targets:
            raise InvalidLifecycleTransitionException(
                from_status=current_status,
                to_status=target_status_upper,
                reason=f"Permitted transitions from '{current_status}' are: {', '.join(sorted(allowed_targets)) or 'None'}",
            )

        # Transition guard: PROVISIONING -> ACTIVE requires completed onboarding readiness
        if current_status == TenantLifecycleStatus.PROVISIONING.value and target_status_upper == TenantLifecycleStatus.ACTIVE.value:
            prov_stmt = select(TenantProvisioningOperation).where(
                TenantProvisioningOperation.tenant_id == tenant_id,
                TenantProvisioningOperation.stage == TenantProvisioningStage.COMPLETED.value,
                TenantProvisioningOperation.status == TenantProvisioningStatus.COMPLETED.value,
            )
            prov_res = await db.execute(prov_stmt)
            if not prov_res.scalar_one_or_none():
                raise InvalidLifecycleTransitionException(
                    from_status=current_status,
                    to_status=target_status_upper,
                    reason="Mandatory provisioning stages have not completed successfully.",
                )

        # Apply state changes to Institution
        old_status = tenant.status
        tenant.status = target_status_upper

        if target_status_upper == TenantLifecycleStatus.SUSPENDED.value:
            tenant.suspended_at = now
        elif target_status_upper in (
            TenantLifecycleStatus.DEACTIVATED.value,
            TenantLifecycleStatus.DELETION_PENDING.value,
            TenantLifecycleStatus.DELETED.value,
            TenantLifecycleStatus.ARCHIVED.value,
        ):
            tenant.deleted_at = now
            tenant.is_active = False
        elif target_status_upper in (
            TenantLifecycleStatus.ACTIVE.value,
            TenantLifecycleStatus.TRIAL.value,
        ):
            tenant.suspended_at = None
            tenant.deleted_at = None
            tenant.is_active = True

        # Record transition history
        transition = TenantLifecycleTransition(
            tenant_id=tenant_id,
            from_status=old_status,
            to_status=target_status_upper,
            actor_id=actor_id,
            actor_email=actor_email,
            reason=reason,
            correlation_id=corr_uuid,
            metadata_json=metadata or {},
        )
        db.add(transition)

        # Outbox event publication
        try:
            outbox_event = DomainEventEnvelope.create(
                event_type="tenant.lifecycle.transitioned",
                tenant_id=tenant_id,
                payload={
                    "tenant_id": str(tenant_id),
                    "tenant_code": tenant.code,
                    "old_status": old_status,
                    "new_status": target_status_upper,
                    "reason": reason,
                    "actor_id": str(actor_id) if actor_id else None,
                },
                correlation_id=corr_str,
                aggregate_type="Institution",
                aggregate_id=tenant_id,
            )
            await OutboxService.create_event(db, outbox_event)
        except Exception as ev_err:
            logger.warning("Failed to emit outbox event for tenant lifecycle transition: %s", ev_err)

        # Centralized forensic audit
        audit_action = (
            AuditEventCategory.TENANT_SUSPENDED
            if target_status_upper == TenantLifecycleStatus.SUSPENDED.value
            else AuditEventCategory.TENANT_REACTIVATED
            if target_status_upper in (TenantLifecycleStatus.ACTIVE.value, TenantLifecycleStatus.TRIAL.value)
            else AuditEventCategory.TENANT_DEACTIVATED
            if target_status_upper in (TenantLifecycleStatus.DEACTIVATED.value, TenantLifecycleStatus.ARCHIVED.value)
            else AuditEventCategory.TENANT_LIFECYCLE_TRANSITION
        )
        db.add(
            build_audit_entry(
                tenant_id=tenant_id,
                action=audit_action,
                entity_type="Tenant",
                entity_id=tenant_id,
                user_id=actor_id,
                old_values_json={"status": old_status},
                new_values_json={"status": target_status_upper},
                business_context=f"Tenant lifecycle transitioned from {old_status} to {target_status_upper}. Reason: {reason}",
                correlation_id=corr_uuid,
            )
        )

        await db.flush()
        await db.refresh(tenant)
        await db.refresh(transition)
        await tenant_cache.invalidate_tenant(tenant_id)

        return tenant, transition

    @classmethod
    async def get_lifecycle_history(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TenantLifecycleTransition]:
        """Retrieve audit history of lifecycle transitions for a specific tenant."""
        stmt = (
            select(TenantLifecycleTransition)
            .where(TenantLifecycleTransition.tenant_id == tenant_id)
            .order_by(desc(TenantLifecycleTransition.created_at))
            .offset(offset)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())
