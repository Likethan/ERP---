"""Business Policy Management and Evaluation Service for CampusOS (Step 23)."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditEventCategory, build_audit_entry
from app.core.cache import tenant_cache
from app.core.exceptions import PolicyEvaluationFailedException, PolicyNotFoundException
from app.models.configuration import (
    ConfigurationPolicy,
    ConfigurationPolicyVersion,
    PolicyStatus,
)
from app.repositories.configuration_repository import ConfigurationRepository
from app.schemas.configuration import (
    PolicyCreate,
    PolicyEvaluateResponse,
    PolicyUpdate,
)
from app.services.policy_evaluator import PolicyEvaluator


class PolicyService:
    """Manages operational business rules, versioning, and deterministic policy evaluation."""

    @classmethod
    async def get_policy(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        policy_key: str,
        campus_id: UUID | None = None,
    ) -> ConfigurationPolicy:
        repo = ConfigurationRepository(db)
        policy = await repo.get_policy(
            policy_key=policy_key, tenant_id=tenant_id, campus_id=campus_id
        )
        if not policy:
            raise PolicyNotFoundException(policy_key)
        return policy

    @classmethod
    async def list_policies(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        module: str | None = None,
        status: str | None = None,
    ) -> list[ConfigurationPolicy]:
        repo = ConfigurationRepository(db)
        return await repo.list_policies(tenant_id=tenant_id, module=module, status=status)

    @classmethod
    async def create_policy(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        dto: PolicyCreate,
        actor_id: UUID | None = None,
    ) -> ConfigurationPolicy:
        repo = ConfigurationRepository(db)

        policy = ConfigurationPolicy(
            tenant_id=tenant_id,
            policy_key=dto.policy_key,
            name=dto.name,
            description=dto.description,
            module=dto.module,
            scope=dto.scope,
            campus_id=dto.campus_id,
            conditions=dto.conditions,
            actions=dto.actions,
            priority=dto.priority,
            status=dto.status,
            version=1,
            effective_from=dto.effective_from or datetime.now(UTC),
            effective_until=dto.effective_until,
            created_by_id=actor_id,
            updated_by_id=actor_id,
        )
        created_policy = await repo.create_policy(policy)

        # Snapshot initial version
        version = ConfigurationPolicyVersion(
            tenant_id=tenant_id,
            policy_id=created_policy.id,
            policy_key=created_policy.policy_key,
            version_number=1,
            conditions=created_policy.conditions,
            actions=created_policy.actions,
            change_summary="Initial policy creation",
            actor_id=actor_id,
        )
        await repo.create_policy_version(version)

        # Invalidate cache
        await tenant_cache.invalidate_namespace(tenant_id, "policies")

        # Audit
        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.POLICY_CREATED,
            entity_type="configuration_policy",
            entity_id=created_policy.id,
            user_id=actor_id,
            new_values_json={"policy_key": dto.policy_key, "module": dto.module},
            business_context=f"Business policy '{dto.policy_key}' created.",
        )
        db.add(audit)
        await db.flush()

        return created_policy

    @classmethod
    async def update_policy(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        policy_key: str,
        dto: PolicyUpdate,
        actor_id: UUID | None = None,
        campus_id: UUID | None = None,
    ) -> ConfigurationPolicy:
        repo = ConfigurationRepository(db)
        policy = await repo.get_policy(
            policy_key=policy_key, tenant_id=tenant_id, campus_id=campus_id
        )
        if not policy:
            raise PolicyNotFoundException(policy_key)

        old_conditions = policy.conditions
        old_actions = policy.actions

        if dto.name is not None:
            policy.name = dto.name
        if dto.description is not None:
            policy.description = dto.description
        if dto.conditions is not None:
            policy.conditions = dto.conditions
        if dto.actions is not None:
            policy.actions = dto.actions
        if dto.priority is not None:
            policy.priority = dto.priority
        if dto.status is not None:
            policy.status = dto.status
        if dto.effective_from is not None:
            policy.effective_from = dto.effective_from
        if dto.effective_until is not None:
            policy.effective_until = dto.effective_until

        policy.version += 1
        policy.updated_by_id = actor_id

        # Snapshot version
        version = ConfigurationPolicyVersion(
            tenant_id=tenant_id,
            policy_id=policy.id,
            policy_key=policy.policy_key,
            version_number=policy.version,
            conditions=policy.conditions,
            actions=policy.actions,
            change_summary=dto.reason or f"Updated policy to version {policy.version}",
            actor_id=actor_id,
            reason=dto.reason,
        )
        await repo.create_policy_version(version)

        # Invalidate cache
        await tenant_cache.invalidate_namespace(tenant_id, "policies")

        # Audit
        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.POLICY_UPDATED,
            entity_type="configuration_policy",
            entity_id=policy.id,
            user_id=actor_id,
            old_values_json={"conditions": old_conditions, "actions": old_actions},
            new_values_json={
                "conditions": policy.conditions,
                "actions": policy.actions,
                "version": policy.version,
            },
            business_context=f"Business policy '{policy_key}' updated to version {policy.version}.",
        )
        db.add(audit)
        await db.flush()

        return policy

    @classmethod
    async def evaluate_policy(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        policy_key: str,
        context: dict[str, Any],
        campus_id: UUID | None = None,
    ) -> PolicyEvaluateResponse:
        """Evaluate a business policy against provided operational context."""
        repo = ConfigurationRepository(db)
        policy = await repo.get_policy(
            policy_key=policy_key, tenant_id=tenant_id, campus_id=campus_id
        )
        if not policy:
            raise PolicyNotFoundException(policy_key)

        if policy.status != PolicyStatus.ACTIVE:
            raise PolicyEvaluationFailedException(
                f"Policy '{policy_key}' is not active (current status: {policy.status})."
            )

        now = datetime.now(UTC)
        eff_from = (
            policy.effective_from.replace(tzinfo=UTC)
            if (policy.effective_from and policy.effective_from.tzinfo is None)
            else policy.effective_from
        )
        eff_until = (
            policy.effective_until.replace(tzinfo=UTC)
            if (policy.effective_until and policy.effective_until.tzinfo is None)
            else policy.effective_until
        )

        if eff_from and now < eff_from:
            raise PolicyEvaluationFailedException(
                f"Policy '{policy_key}' has not taken effect yet."
            )
        if eff_until and now > eff_until:
            raise PolicyEvaluationFailedException(f"Policy '{policy_key}' has expired.")

        decision, matched_count = PolicyEvaluator.evaluate_policy_rules(
            conditions=policy.conditions,
            context=context,
        )

        return PolicyEvaluateResponse(
            policy=policy.policy_key,
            decision=decision,
            actions=policy.actions if decision else {},
            matched_conditions=matched_count,
            total_conditions=len(policy.conditions),
            version=policy.version,
            evaluation_context=context,
        )
