"""LLM Provider abstraction and response contracts.

Enables vendor-agnostic integration with zero vendor hard-coding.
"""

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class LLMResponse:
    content: str
    structured_blocks: list[dict[str, Any]] = field(default_factory=list)
    suggested_actions: list[dict[str, Any]] = field(default_factory=list)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    model: str = "mock"
    provider: str = "mock"
    token_usage: dict[str, int] = field(
        default_factory=lambda: {"prompt_tokens": 120, "completion_tokens": 80, "total_tokens": 200}
    )
    latency_ms: int = 45


class LLMProvider(Protocol):
    """Protocol contract for multi-vendor LLM provider implementations."""

    async def generate(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> LLMResponse:
        """Execute model generation given conversational context and tool descriptors."""
        ...
