"""Centralized Tool Registry for CampusOS Intelligence Engine.

Maintains the strict allowlist of authorized domain tools, enforces PBAC checks
prior to execution, and guarantees no direct ORM or SQL execution by the AI layer.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    NotFoundException,
    PermissionDeniedException,
    ValidationException,
)
from app.domains.intelligence.tools.academics import ACADEMICS_TOOLS
from app.domains.intelligence.tools.attendance import ATTENDANCE_TOOLS
from app.domains.intelligence.tools.base import ToolDefinition
from app.domains.intelligence.tools.campus import CAMPUS_TOOLS
from app.domains.intelligence.tools.case_management import CASE_MANAGEMENT_TOOLS
from app.domains.intelligence.tools.configuration import CONFIGURATION_TOOLS
from app.domains.intelligence.tools.documents import DOCUMENTS_TOOLS
from app.domains.intelligence.tools.examinations import EXAMINATION_TOOLS
from app.domains.intelligence.tools.finance import FINANCE_TOOLS
from app.domains.intelligence.tools.infrastructure import INFRASTRUCTURE_TOOLS
from app.domains.intelligence.tools.master_data import MASTER_DATA_TOOLS
from app.domains.intelligence.tools.people import PEOPLE_TOOLS
from app.domains.intelligence.tools.placement import PLACEMENT_TOOLS
from app.models.people import User


class ToolRegistry:
    """Central registry of approved institutional domain tools."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}
        # Register all domain tool sets
        for tool in (
            PEOPLE_TOOLS
            + ACADEMICS_TOOLS
            + ATTENDANCE_TOOLS
            + EXAMINATION_TOOLS
            + FINANCE_TOOLS
            + PLACEMENT_TOOLS
            + CAMPUS_TOOLS
            + INFRASTRUCTURE_TOOLS
            + DOCUMENTS_TOOLS
            + CONFIGURATION_TOOLS
            + MASTER_DATA_TOOLS
            + CASE_MANAGEMENT_TOOLS
        ):
            self.register(tool)

    def register(self, tool: ToolDefinition) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def list_tools(self, user_permissions: set[str] | None = None) -> list[ToolDefinition]:
        """List all tools or filter by requesting user's permitted capabilities."""
        if user_permissions is None or "*" in user_permissions:
            return list(self._tools.values())

        permitted = []
        for tool in self._tools.values():
            if self._has_permission(tool, user_permissions):
                permitted.append(tool)
        return permitted

    def _has_permission(self, tool: ToolDefinition, user_permissions: set[str]) -> bool:
        if "*" in user_permissions:
            return True
        for req_perm in tool.required_permissions:
            alt_perm = req_perm.replace(":", ".") if ":" in req_perm else req_perm.replace(".", ":")
            if (
                req_perm in user_permissions
                or alt_perm in user_permissions
                or any(
                    p.endswith(f":{req_perm}")
                    or p.endswith(f"_{req_perm}")
                    or p == f"{tool.domain.lower()}:{req_perm}"
                    for p in user_permissions
                )
            ):
                continue
            return False
        return True

    async def execute(
        self,
        tool_name: str,
        db: AsyncSession,
        tenant_id: UUID,
        user: User,
        user_permissions: set[str],
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Permission-validated, sandboxed tool execution against domain services."""
        tool = self.get(tool_name)
        if not tool:
            raise NotFoundException(
                f"Tool '{tool_name}' is not an approved institutional domain tool."
            )

        # Tool Permission Engine check
        if not self._has_permission(tool, user_permissions):
            raise PermissionDeniedException(f"tool:{tool_name}:{tool.required_permissions[0]}")

        # Input parameter validation
        clean_params = params or {}
        # Reject raw SQL or shell injection attempts in parameter values
        for k, v in clean_params.items():
            if isinstance(v, str):
                v_lower = v.lower()
                if any(
                    x in v_lower
                    for x in [";--", "select *", "drop table", "union select", "exec(", "eval("]
                ):
                    raise ValidationException(f"Security validation failed on parameter '{k}'.")

        # Telemetry updates
        tool.execution_count += 1
        tool.last_used = datetime.now(UTC).isoformat()

        # Execute bound domain handler
        return await tool.handler(db, tenant_id, user, clean_params)


_global_registry = ToolRegistry()


def get_tool_registry() -> ToolRegistry:
    return _global_registry
