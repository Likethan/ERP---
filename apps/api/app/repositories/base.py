"""Canonical base repository with automatic tenant scoping and protection against cross-tenant leaks."""

from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import CrossTenantRelationshipException, NotFoundException
from app.core.tenant import get_current_tenant_context
from app.models.base import TenantScopedModel

ModelType = TypeVar("ModelType", bound=TenantScopedModel)


class TenantScopedRepository(Generic[ModelType]):
    """Generic repository enforcing strict tenant isolation across all DB operations.

    Ensures:
    - Reads are strictly scoped to the tenant
    - Writes automatically set tenant_id from server context, ignoring client spoofing
    - Updates and deletes cannot touch other tenants' records
    - Cross-tenant foreign keys are verified before association
    """

    def __init__(self, db: AsyncSession, model: type[ModelType], tenant_id: UUID | None = None):
        self.db = db
        self.model = model
        if tenant_id is not None:
            self._tenant_id = tenant_id
        else:
            self._tenant_id = get_current_tenant_context().tenant_id

    @property
    def tenant_id(self) -> UUID:
        return self._tenant_id

    async def get(self, id: UUID) -> ModelType | None:
        """Fetch record by ID scoped strictly to active tenant."""
        stmt = select(self.model).where(
            self.model.id == id,
            self.model.tenant_id == self.tenant_id,
        )
        if hasattr(self.model, "is_deleted"):
            stmt = stmt.where(self.model.is_deleted.is_(False))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_404(self, id: UUID, resource_name: str | None = None) -> ModelType:
        """Fetch record by ID or raise NotFoundException (prevents existence probing)."""
        instance = await self.get(id)
        if instance is None:
            raise NotFoundException(resource_name or self.model.__name__, id)
        return instance

    async def list(
        self,
        *criteria: Any,
        offset: int = 0,
        limit: int = 100,
        order_by: Any = None,
        include_deleted: bool = False,
    ) -> list[ModelType]:
        """List tenant records with optional criteria, pagination, and sorting."""
        stmt = select(self.model).where(self.model.tenant_id == self.tenant_id)
        if hasattr(self.model, "is_deleted") and not include_deleted:
            stmt = stmt.where(self.model.is_deleted.is_(False))
        if criteria:
            stmt = stmt.where(*criteria)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count(self, *criteria: Any, include_deleted: bool = False) -> int:
        """Count tenant records matching optional criteria."""
        stmt = (
            select(func.count())
            .select_from(self.model)
            .where(self.model.tenant_id == self.tenant_id)
        )
        if hasattr(self.model, "is_deleted") and not include_deleted:
            stmt = stmt.where(self.model.is_deleted.is_(False))
        if criteria:
            stmt = stmt.where(*criteria)
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def exists(self, id: UUID) -> bool:
        """Check if record exists within tenant boundary."""
        stmt = (
            select(func.count(1))
            .select_from(self.model)
            .where(self.model.id == id, self.model.tenant_id == self.tenant_id)
        )
        if hasattr(self.model, "is_deleted"):
            stmt = stmt.where(self.model.is_deleted.is_(False))
        result = await self.db.execute(stmt)
        return bool(result.scalar())

    async def create(self, **data: Any) -> ModelType:
        """Create new record with authoritative server-side tenant_id, ignoring client payload."""
        # Force authoritative tenant context
        data["tenant_id"] = self.tenant_id
        instance = self.model(**data)
        self.db.add(instance)
        await self.db.flush()
        return instance

    async def update(self, id: UUID, **data: Any) -> ModelType:
        """Update existing tenant record. Strips any attempt to mutate tenant_id."""
        instance = await self.get_or_404(id)
        # Prevent mutating tenant_id or primary key
        data.pop("tenant_id", None)
        data.pop("id", None)
        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        await self.db.flush()
        return instance

    async def delete(self, id: UUID, soft: bool = True) -> bool:
        """Delete tenant record (soft-delete if supported, else physical)."""
        instance = await self.get(id)
        if instance is None:
            return False

        if soft and hasattr(instance, "is_deleted"):
            instance.is_deleted = True
            if hasattr(instance, "deleted_at"):
                instance.deleted_at = func.now()
        else:
            await self.db.delete(instance)
        await self.db.flush()
        return True

    async def validate_foreign_entity(
        self,
        foreign_model: type[TenantScopedModel],
        foreign_id: UUID | None,
        allow_null: bool = True,
    ) -> None:
        """Verify foreign entity belongs strictly to current tenant boundary."""
        if foreign_id is None:
            if not allow_null:
                raise CrossTenantRelationshipException(
                    f"Relationship requirement violated: {foreign_model.__name__} cannot be null."
                )
            return

        stmt = select(foreign_model.tenant_id).where(foreign_model.id == foreign_id)
        result = await self.db.execute(stmt)
        target_tenant_id = result.scalar_one_or_none()
        if target_tenant_id is None:
            raise NotFoundException(foreign_model.__name__, foreign_id)
        if target_tenant_id != self.tenant_id:
            raise CrossTenantRelationshipException(
                f"Cross-tenant foreign key violation: {foreign_model.__name__} {foreign_id} "
                f"belongs to tenant {target_tenant_id}, not {self.tenant_id}"
            )
