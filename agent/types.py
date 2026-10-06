from dataclasses import dataclass
from typing import Any, Callable


class TurnLimitError(RuntimeError):
    """Raised when the agent loop exceeds its maximum allowed turns."""
    pass


class ProviderError(RuntimeError):
    """Raised when the LLM provider fails and does not recover after a retry."""
    pass


@dataclass
class ToolCall:
    id: str
    name: str
    args: dict[str, Any]


@dataclass
class LLMResponse:
    text: str | None
    tool_calls: list[ToolCall]


@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]
    func: Callable
