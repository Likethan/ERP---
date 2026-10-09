"""Distributed Locking Framework for CampusOS Multi-Instance Deployments.

Provides Redis-backed distributed locks with non-blocking acquisition, TTL safety,
token-based release validation (to prevent releasing locks owned by other workers),
and graceful fallback to in-memory locks for local development and offline test suites.
"""

import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.core.config import settings

logger = logging.getLogger("campusos.lock")

# In-memory fallback lock table for local/test environments
_in_memory_locks: dict[str, tuple[str, datetime]] = {}
_memory_lock = asyncio.Lock()


class DistributedLock:
    """Distributed lock ensuring single execution across multiple API/worker replicas."""

    def __init__(self, name: str, ttl_seconds: int = 60):
        self.name = f"campusos:lock:{name}"
        self.ttl_seconds = ttl_seconds
        self.token = str(uuid4())
        self._acquired = False
        self._redis_client = None

    async def _get_redis_client(self):
        if self._redis_client is None:
            try:
                import redis.asyncio as aioredis
                self._redis_client = aioredis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=2.0,
                    socket_timeout=2.0,
                )
            except Exception as exc:
                logger.debug("Redis client init failed (%s), using memory lock fallback.", exc)
                self._redis_client = None
        return self._redis_client

    async def acquire(self) -> bool:
        """Attempt to acquire the lock. Returns True if acquired, False otherwise."""
        # 1. Attempt Redis lock if available
        try:
            client = await self._get_redis_client()
            if client is not None:
                # SET key token NX EX ttl
                res = await client.set(self.name, self.token, nx=True, ex=self.ttl_seconds)
                if res:
                    self._acquired = True
                    return True
                return False
        except Exception as exc:
            logger.warning(
                "Redis lock error on '%s': %s. Falling back to memory lock.", self.name, exc
            )

        # 2. In-memory fallback
        async with _memory_lock:
            now = datetime.now(UTC)
            current = _in_memory_locks.get(self.name)
            if current is not None:
                token, expires_at = current
                if now < expires_at:
                    return False  # Lock still active
            # Lock is absent or expired
            expires_at = now + timedelta(seconds=self.ttl_seconds)
            _in_memory_locks[self.name] = (self.token, expires_at)
            self._acquired = True
            return True

    async def release(self) -> None:
        """Release lock only if current instance still owns it."""
        if not self._acquired:
            return

        # 1. Try Redis release with safe token verification
        try:
            client = await self._get_redis_client()
            if client is not None:
                # Lua script to release only if value matches token
                lua_script = """
                if redis.call("get", KEYS[1]) == ARGV[1] then
                    return redis.call("del", KEYS[1])
                else
                    return 0
                end
                """
                await client.eval(lua_script, 1, self.name, self.token)
                self._acquired = False
                return
        except Exception as exc:
            logger.debug("Redis release failed (%s), checking memory fallback.", exc)

        # 2. In-memory fallback release
        async with _memory_lock:
            current = _in_memory_locks.get(self.name)
            if current and current[0] == self.token:
                _in_memory_locks.pop(self.name, None)
        self._acquired = False

    async def close(self) -> None:
        """Clean up Redis client resources."""
        if self._redis_client is not None:
            try:
                await self._redis_client.aclose()
            except Exception:
                pass
            self._redis_client = None


@asynccontextmanager
async def distributed_lock(name: str, ttl_seconds: int = 60) -> AsyncGenerator[bool, None]:
    """Context manager for distributed locking.

    Usage:
        async with distributed_lock("job_fee_overdue", ttl_seconds=120) as acquired:
            if not acquired:
                logger.info("Task already running on another worker, skipping.")
                return
            await execute_task()
    """
    lock = DistributedLock(name, ttl_seconds=ttl_seconds)
    acquired = await lock.acquire()
    try:
        yield acquired
    finally:
        if acquired:
            await lock.release()
        await lock.close()
