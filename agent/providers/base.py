from abc import ABC, abstractmethod

from agent.types import LLMResponse, ToolCall


class LLMProvider(ABC):

    @abstractmethod
    def send_message(self, message) -> LLMResponse:
        pass

    @abstractmethod
    def send_tool_results(
        self,
        results: list[tuple[ToolCall, object]],
    ) -> LLMResponse:
        pass
