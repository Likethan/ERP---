"""Tenant isolation validation helpers for cross-tenant FK and payload protection."""

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import CrossTenantRelationshipException, NotFoundException
from app.models.base import TenantScopedModel


async def validate_tenant_entity_ownership(
    db: AsyncSession,
    tenant_id: UUID,
    entity_model: type,
    entity_id: UUID | None,
    allow_null: bool = True,
) -> None:
    """Validate that a referenced entity exists and belongs strictly to the given tenant.

    Raises:
        NotFoundException: If the entity does not exist at all or belongs to another tenant.
        CrossTenantRelationshipException: If the entity belongs to another tenant (for explicit security checks).
    """
    if entity_id is None:
        if not allow_null:
            raise CrossTenantRelationshipException(
                f"Missing required relationship entity for {entity_model.__name__}"
            )
        return

    # Check if entity is tenant-scoped
    if hasattr(entity_model, "tenant_id"):
        stmt = select(entity_model.tenant_id).where(entity_model.id == entity_id)
        result = await db.execute(stmt)
        record_tenant_id = result.scalar_one_or_none()

        if record_tenant_id is None:
            raise NotFoundException(entity_model.__name__, entity_id)

        if record_tenant_id != tenant_id:
            raise CrossTenantRelationshipException(
                f"Cross-tenant reference violation: {entity_model.__name__} {entity_id} "
                f"belongs to tenant {record_tenant_id}, not active tenant {tenant_id}."
            )


async def validate_entities_same_tenant(
    db: AsyncSession,
    tenant_id: UUID,
    *entity_pairs: tuple[type, UUID | None],
) -> None:
    """Batch validate that all foreign entity references belong to the given tenant context.

    Usage:
        await validate_entities_same_tenant(
            db,
            tenant_id,
            (Department, data.department_id),
            (Program, data.program_id),
        )
    """
    for model_cls, entity_id in entity_pairs:
        await validate_tenant_entity_ownership(db, tenant_id, model_cls, entity_id)
