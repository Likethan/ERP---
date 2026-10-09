"""Request-scoped tenant context management."""

from contextvars import ContextVar
from dataclasses import dataclass
from uuid import UUID

from app.core.exceptions import TenantMismatchException


@dataclass(frozen=True)
class TenantContext:
    tenant_id: UUID
    code: str
    name: str
    is_active: bool = True
    user_id: UUID | None = None
    roles: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()
    tenant_status: str = "ACTIVE"
    slug: str | None = None
    plan: str = "ENTERPRISE"
    timezone: str = "Asia/Kolkata"
    currency: str = "INR"
    locale: str = "en-IN"

    @property
    def is_operational(self) -> bool:
        """Check if tenant is in normal operating mode (ACTIVE or TRIAL)."""
        return self.is_active and self.tenant_status in ("ACTIVE", "TRIAL")

    @property
    def is_suspended(self) -> bool:
        return self.tenant_status == "SUSPENDED"

    @property
    def is_archived(self) -> bool:
        return self.tenant_status == "ARCHIVED" or not self.is_active


_current_tenant_context: ContextVar[TenantContext | None] = ContextVar(
    "current_tenant_context", default=None
)


def set_current_tenant_context(tenant: TenantContext | None) -> None:
    """Set the tenant context for the current request execution context."""
    _current_tenant_context.set(tenant)


def get_current_tenant_context() -> TenantContext:
    """Retrieve the current request's tenant context.

    Raises:
        TenantMismatchException: If no tenant context is established.
    """
    tenant = _current_tenant_context.get()
    if tenant is None:
        raise TenantMismatchException()
    return tenant


def get_optional_tenant_context() -> TenantContext | None:
    """Retrieve the current request's tenant context, or None if unauthenticated."""
    return _current_tenant_context.get()
