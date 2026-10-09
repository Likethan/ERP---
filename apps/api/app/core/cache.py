"""Tenant-Isolated Caching Engine for Multi-Tenant SaaS.

Enforces strict key namespacing: `tenant:{tenant_id}:{namespace}:{key}`.
Guarantees that cached items (analytics, profiles, AI context, search queries)
never leak across tenant boundaries and invalidation strictly isolates tenants.
"""

from datetime import datetime, timezone
import json
from typing import Any
from uuid import UUID


class TenantIsolatedCache:
    """In-memory and Redis-ready cache wrapper enforcing tenant-level partitioning."""

    def __init__(self):
        self._store: dict[str, tuple[Any, datetime | None]] = {}

    @staticmethod
    def build_key(tenant_id: UUID, namespace: str, key: str) -> str:
        """Construct deterministic, tenant-isolated cache key."""
        clean_ns = namespace.strip().replace(":", "_")
        clean_key = str(key).strip()
        return f"tenant:{tenant_id}:{clean_ns}:{clean_key}"

    async def get(self, tenant_id: UUID, namespace: str, key: str) -> Any | None:
        """Fetch cached item. Returns None if expired or non-existent."""
        full_key = self.build_key(tenant_id, namespace, key)
        record = self._store.get(full_key)
        if record is None:
            return None

        val, expires_at = record
        if expires_at is not None and datetime.now(timezone.utc) > expires_at:
            del self._store[full_key]
            return None
        return val

    async def set(
        self,
        tenant_id: UUID,
        namespace: str,
        key: str,
        value: Any,
        ttl_seconds: int | None = 300,
    ) -> None:
        """Store value with tenant-isolated key and optional expiration."""
        full_key = self.build_key(tenant_id, namespace, key)
        expires_at = (
            datetime.fromtimestamp(datetime.now(timezone.utc).timestamp() + ttl_seconds, tz=timezone.utc)
            if ttl_seconds
            else None
        )
        self._store[full_key] = (value, expires_at)

    async def delete(self, tenant_id: UUID, namespace: str, key: str) -> bool:
        """Evict a specific tenant item from cache."""
        full_key = self.build_key(tenant_id, namespace, key)
        if full_key in self._store:
            del self._store[full_key]
            return True
        return False

    async def invalidate_namespace(self, tenant_id: UUID, namespace: str) -> int:
        """Evict all cached entries under a specific namespace for one tenant only."""
        prefix = f"tenant:{tenant_id}:{namespace.strip().replace(':', '_')}:"
        matching = [k for k in self._store if k.startswith(prefix)]
        for k in matching:
            del self._store[k]
        return len(matching)

    async def invalidate_tenant(self, tenant_id: UUID) -> int:
        """Evict all cache entries for an entire tenant (e.g. upon suspension or bulk updates)."""
        prefix = f"tenant:{tenant_id}:"
        matching = [k for k in self._store if k.startswith(prefix)]
        for k in matching:
            del self._store[k]
        return len(matching)

    def clear(self) -> None:
        """Flush store (used primarily in test suites)."""
        self._store.clear()


# Canonical singleton cache instance
tenant_cache = TenantIsolatedCache()


def get_tenant_cache() -> TenantIsolatedCache:
    """Dependency injector for tenant cache."""
    return tenant_cache
