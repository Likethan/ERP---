"""Database Query Performance Engineering, Keyset Pagination & Query Count Profiling.

Provides tools for detecting N+1 regressions, profiling database round-trips,
and executing stable, deterministic cursor-based pagination across high-volume ERP datasets.
"""

import contextlib
import time
from typing import Any, TypeVar
from uuid import UUID

from sqlalchemy import Select, asc, desc, event, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.metrics import metrics
from app.models.base import TenantScopedModel

T = TypeVar("T", bound=TenantScopedModel)


class QueryCountProfiler:
    """Thread-safe and async-safe profiler that counts and measures executed SQL queries.

    Usage:
        async with QueryCountProfiler(db) as profiler:
            results = await db.execute(...)
        assert profiler.count <= 2, f"N+1 regression: executed {profiler.count} queries"
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.count: int = 0
        self.queries: list[dict[str, Any]] = []
        self._start_time: float = 0.0
        self._elapsed: float = 0.0
        self._sync_session: Session = session.sync_session

    def _before_cursor_execute(
        self, conn, cursor, statement, parameters, context, executemany
    ):
        start = time.perf_counter()
        context._query_start_time = start

    def _after_cursor_execute(
        self, conn, cursor, statement, parameters, context, executemany
    ):
        start = getattr(context, "_query_start_time", time.perf_counter())
        duration = time.perf_counter() - start
        self.count += 1
        self.queries.append(
            {
                "statement": statement,
                "duration_ms": round(duration * 1000.0, 3),
            }
        )
        try:
            metrics.record_db_query(duration)
        except Exception:
            pass

    async def __aenter__(self):
        self.count = 0
        self.queries.clear()
        self._start_time = time.perf_counter()
        bind = self.session.bind
        self._target_engine = getattr(bind, "sync_engine", bind)
        event.listen(
            self._target_engine,
            "before_cursor_execute",
            self._before_cursor_execute,
        )
        event.listen(
            self._target_engine,
            "after_cursor_execute",
            self._after_cursor_execute,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._elapsed = time.perf_counter() - self._start_time
        if hasattr(self, "_target_engine"):
            try:
                event.remove(
                    self._target_engine,
                    "before_cursor_execute",
                    self._before_cursor_execute,
                )
                event.remove(
                    self._target_engine,
                    "after_cursor_execute",
                    self._after_cursor_execute,
                )
            except Exception:
                pass


@contextlib.asynccontextmanager
async def assert_max_queries(session: AsyncSession, max_queries: int):
    """Context manager asserting that code block does not exceed maximum allowable database queries."""
    async with QueryCountProfiler(session) as profiler:
        yield profiler
    if profiler.count > max_queries:
        statements = "\n---\n".join(q["statement"] for q in profiler.queries)
        raise AssertionError(
            f"Query budget exceeded! Expected at most {max_queries} queries, "
            f"but executed {profiler.count}:\n{statements}"
        )


class CursorPaginationHelper:
    """Executes deterministic keyset / cursor pagination to eliminate offset degradation.

    Guarantees:
    - Stable sorting: primary key is always the deterministic tie-breaker.
    - Bound page sizes: limit is capped at settings.MAX_PAGE_SIZE.
    - No unbounded full table scans.
    """

    @classmethod
    async def paginate(
        cls,
        db: AsyncSession,
        stmt: Select[tuple[T]],
        model: type[T],
        cursor_id: UUID | None = None,
        limit: int = 20,
        order: str = "desc",
    ) -> dict[str, Any]:
        """Apply bounded cursor pagination to a SQLAlchemy Select statement."""
        # Enforce bounded page size
        bounded_limit = min(max(1, limit), settings.MAX_PAGE_SIZE)

        # Order column: model.created_at if available, else model.id
        has_created_at = hasattr(model, "created_at")

        if order.lower() == "asc":
            if has_created_at:
                stmt = stmt.order_by(asc(model.created_at), asc(model.id))
            else:
                stmt = stmt.order_by(asc(model.id))
        else:
            if has_created_at:
                stmt = stmt.order_by(desc(model.created_at), desc(model.id))
            else:
                stmt = stmt.order_by(desc(model.id))

        # Apply cursor filter if provided
        if cursor_id is not None:
            # Look up cursor reference record
            cursor_stmt = select(model).where(model.id == cursor_id)
            cursor_rec = (await db.execute(cursor_stmt)).scalar_one_or_none()
            if cursor_rec is not None:
                if has_created_at:
                    cursor_created = cursor_rec.created_at
                    if order.lower() == "asc":
                        stmt = stmt.where(
                            (model.created_at > cursor_created)
                            | ((model.created_at == cursor_created) & (model.id > cursor_id))
                        )
                    else:
                        stmt = stmt.where(
                            (model.created_at < cursor_created)
                            | ((model.created_at == cursor_created) & (model.id < cursor_id))
                        )
                else:
                    if order.lower() == "asc":
                        stmt = stmt.where(model.id > cursor_id)
                    else:
                        stmt = stmt.where(model.id < cursor_id)

        # Fetch limit + 1 to detect has_next_page
        stmt = stmt.limit(bounded_limit + 1)
        result = await db.execute(stmt)
        items = list(result.scalars().all())

        has_next = len(items) > bounded_limit
        if has_next:
            items = items[:bounded_limit]

        next_cursor = str(items[-1].id) if items and has_next else None

        return {
            "items": items,
            "has_next": has_next,
            "next_cursor": next_cursor,
            "limit": bounded_limit,
        }
