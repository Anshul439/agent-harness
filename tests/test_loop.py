import pytest

from agent.loop import Agent
from agent.tools import tools
from agent.types import LLMResponse, ToolCall, TurnLimitError


class LoopingProvider:
    """Always returns a tool call — never finishes. Simulates a stuck model."""

    def send_message(self, message):
        return LLMResponse(
            text=None,
            tool_calls=[ToolCall(id="x", name="list_files", args={})],
        )

    def send_tool_results(self, results):
        return LLMResponse(
            text=None,
            tool_calls=[ToolCall(id="x", name="list_files", args={})],
        )


class FinishingProvider:
    """Returns one tool call, then finishes cleanly."""

    def send_message(self, message):
        return LLMResponse(
            text=None,
            tool_calls=[ToolCall(id="x", name="list_files", args={})],
        )

    def send_tool_results(self, results):
        return LLMResponse(text="done", tool_calls=[])


def test_turn_limit_is_enforced():
    agent = Agent(LoopingProvider(), tools, max_turns=3)
    with pytest.raises(TurnLimitError):
        agent.run("loop forever")


def test_normal_run_completes_within_limit():
    agent = Agent(FinishingProvider(), tools, max_turns=25)
    result = agent.run("do one thing then finish")
    assert result == "done"


def test_custom_max_turns_is_respected():
    """A limit of 1 should fire after the first tool-call turn."""
    agent = Agent(LoopingProvider(), tools, max_turns=1)
    with pytest.raises(TurnLimitError):
        agent.run("loop forever")
