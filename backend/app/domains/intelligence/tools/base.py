"""Base tool abstractions and registry metadata."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.people import User


@dataclass
class ToolParameter:
    name: str
    type: str  # "string", "integer", "number", "boolean", "array"
    required: bool
    description: str
    default: Any = None


@dataclass
class ToolDefinition:
    """Explicitly registered institutional domain tool."""

    name: str
    domain: str  # "PEOPLE", "ACADEMICS", "ATTENDANCE", "EXAMINATIONS", "FINANCE", "PLACEMENT", "CAMPUS", "INFRASTRUCTURE", "DOCUMENTS"
    description: str
    required_permissions: list[str]
    handler: Callable[[AsyncSession, UUID, User, dict[str, Any]], Awaitable[dict[str, Any]]]
    parameters: list[ToolParameter] = field(default_factory=list)
    sensitivity_level: str = "INTERNAL"  # "PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"
    max_results: int = 50
    status: str = "ACTIVE"
    execution_count: int = 0
    last_used: str = "Never"
