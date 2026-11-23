"""Controlled Feature Flag Evaluation and Management Service for CampusOS (Step 23)."""

import hashlib
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditEventCategory, build_audit_entry
from app.core.cache import tenant_cache
from app.core.config import settings
from app.core.exceptions import NotFoundException
from app.models.configuration import FeatureFlag
from app.repositories.configuration_repository import ConfigurationRepository
from app.schemas.configuration import (
    FeatureFlagCreate,
    FeatureFlagEvaluateResponse,
    FeatureFlagUpdate,
)


class FeatureFlagService:
    """Manages tenant feature flags with environment targeting and deterministic rollouts."""

    @classmethod
    async def get_feature_flag(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        key: str,
    ) -> FeatureFlag:
        repo = ConfigurationRepository(db)
        flag = await repo.get_feature_flag(key=key, tenant_id=tenant_id)
        if not flag:
            raise NotFoundException("FeatureFlag", key)
        return flag

    @classmethod
    async def list_feature_flags(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        module: str | None = None,
    ) -> list[FeatureFlag]:
        repo = ConfigurationRepository(db)
        return await repo.list_feature_flags(tenant_id=tenant_id, module=module)

    @classmethod
    async def create_feature_flag(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        dto: FeatureFlagCreate,
        actor_id: UUID | None = None,
    ) -> FeatureFlag:
        repo = ConfigurationRepository(db)

        flag = FeatureFlag(
            tenant_id=tenant_id,
            key=dto.key,
            name=dto.name,
            description=dto.description,
            module=dto.module,
            is_enabled=dto.is_enabled,
            rollout_percentage=dto.rollout_percentage,
            target_roles=dto.target_roles,
            target_users=dto.target_users,
            environment=dto.environment,
            effective_from=dto.effective_from,
            expires_at=dto.expires_at,
            created_by_id=actor_id,
            updated_by_id=actor_id,
        )
        created_flag = await repo.create_feature_flag(flag)

        # Invalidate cache
        await tenant_cache.invalidate_namespace(tenant_id, "features")

        # Audit
        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.FEATURE_FLAG_CREATED,
            entity_type="feature_flag",
            entity_id=created_flag.id,
            user_id=actor_id,
            new_values_json={
                "key": dto.key,
                "is_enabled": dto.is_enabled,
                "rollout": dto.rollout_percentage,
            },
            business_context=f"Feature flag '{dto.key}' created.",
        )
        db.add(audit)
        await db.flush()

        return created_flag

    @classmethod
    async def update_feature_flag(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        key: str,
        dto: FeatureFlagUpdate,
        actor_id: UUID | None = None,
    ) -> FeatureFlag:
        repo = ConfigurationRepository(db)
        flag = await repo.get_feature_flag(key=key, tenant_id=tenant_id)
        if not flag:
            raise NotFoundException("FeatureFlag", key)

        old_state = {"is_enabled": flag.is_enabled, "rollout_percentage": flag.rollout_percentage}

        if dto.name is not None:
            flag.name = dto.name
        if dto.description is not None:
            flag.description = dto.description
        if dto.is_enabled is not None:
            flag.is_enabled = dto.is_enabled
        if dto.rollout_percentage is not None:
            flag.rollout_percentage = dto.rollout_percentage
        if dto.target_roles is not None:
            flag.target_roles = dto.target_roles
        if dto.target_users is not None:
            flag.target_users = dto.target_users
        if dto.environment is not None:
            flag.environment = dto.environment
        if dto.effective_from is not None:
            flag.effective_from = dto.effective_from
        if dto.expires_at is not None:
            flag.expires_at = dto.expires_at

        flag.updated_by_id = actor_id

        # Invalidate cache
        await tenant_cache.invalidate_namespace(tenant_id, "features")

        # Audit
        audit = build_audit_entry(
            tenant_id=tenant_id,
            action=AuditEventCategory.FEATURE_FLAG_UPDATED,
            entity_type="feature_flag",
            entity_id=flag.id,
            user_id=actor_id,
            old_values_json=old_state,
            new_values_json={
                "is_enabled": flag.is_enabled,
                "rollout_percentage": flag.rollout_percentage,
            },
            business_context=f"Feature flag '{key}' updated.",
        )
        db.add(audit)
        await db.flush()

        return flag

    @classmethod
    async def evaluate_feature_flag(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        key: str,
        user_id: UUID | None = None,
        roles: list[str] | None = None,
        environment: str | None = None,
    ) -> FeatureFlagEvaluateResponse:
        repo = ConfigurationRepository(db)
        flag = await repo.get_feature_flag(key=key, tenant_id=tenant_id)

        if not flag:
            return FeatureFlagEvaluateResponse(
                key=key,
                is_enabled=False,
                reason="Feature flag does not exist (defaulting to disabled).",
            )

        if not flag.is_enabled:
            return FeatureFlagEvaluateResponse(
                key=key,
                is_enabled=False,
                reason="Feature flag is explicitly disabled.",
            )

        # Environment check
        raw_env = environment or getattr(settings, "ENVIRONMENT", "production") or "production"
        current_env = str(raw_env).upper()
        if flag.environment != "ALL" and flag.environment.upper() != current_env:
            return FeatureFlagEvaluateResponse(
                key=key,
                is_enabled=False,
                reason=(
                    f"Restricted to environment '{flag.environment}', current is '{current_env}'."
                ),
            )

        # Date window check
        now = datetime.now(UTC)
        eff_from = (
            flag.effective_from.replace(tzinfo=UTC)
            if (flag.effective_from and flag.effective_from.tzinfo is None)
            else flag.effective_from
        )
        exp_at = (
            flag.expires_at.replace(tzinfo=UTC)
            if (flag.expires_at and flag.expires_at.tzinfo is None)
            else flag.expires_at
        )

        if eff_from and now < eff_from:
            return FeatureFlagEvaluateResponse(
                key=key,
                is_enabled=False,
                reason="Feature flag effective start date is in the future.",
            )
        if exp_at and now > exp_at:
            return FeatureFlagEvaluateResponse(
                key=key,
                is_enabled=False,
                reason="Feature flag has expired.",
            )

        # Explicit user targeting
        if flag.target_users and user_id:
            user_str = str(user_id)
            if user_str in flag.target_users:
                return FeatureFlagEvaluateResponse(
                    key=key,
                    is_enabled=True,
                    reason="User explicitly targeted.",
                )

        # Explicit role targeting
        if flag.target_roles and roles:
            matching_roles = set(roles).intersection(set(flag.target_roles))
            if matching_roles:
                return FeatureFlagEvaluateResponse(
                    key=key,
                    is_enabled=True,
                    reason=f"Role(s) {list(matching_roles)} explicitly targeted.",
                )

        # Rollout percentage evaluation
        if flag.rollout_percentage == 100:
            return FeatureFlagEvaluateResponse(
                key=key,
                is_enabled=True,
                reason="100% rollout enabled.",
            )

        if flag.rollout_percentage == 0:
            return FeatureFlagEvaluateResponse(
                key=key,
                is_enabled=False,
                reason="0% rollout (disabled for non-targeted users).",
            )

        # Deterministic hashing
        seed = f"{flag.key}:{user_id or tenant_id}"
        hash_val = int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16) % 100
        is_bucket_enabled = hash_val < flag.rollout_percentage

        symbol = "<=" if is_bucket_enabled else ">"
        return FeatureFlagEvaluateResponse(
            key=key,
            is_enabled=is_bucket_enabled,
            reason=f"Rollout bucket {hash_val}% {symbol} {flag.rollout_percentage}%.",
        )
