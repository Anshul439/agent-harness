from agent.loop import Agent
from agent.types import LLMResponse, ToolCall
from agent.tools import tools
from agent.workflow import run_task, _parse_output, SuiteResult


SAMPLE_OUTPUT = """
tests/test_foo.py::test_one PASSED                   [ 25%]
tests/test_foo.py::test_two FAILED                   [ 50%]
tests/test_bar.py::test_three PASSED                 [ 75%]
tests/test_bar.py::test_four FAILED                  [100%]
"""

def test_parse_output_counts_passed():
    result = _parse_output(SAMPLE_OUTPUT)
    assert len(result.passed) == 2

def test_parse_output_counts_failed():
    result = _parse_output(SAMPLE_OUTPUT)
    assert len(result.failed) == 2

def test_parse_output_extracts_names():
    result = _parse_output(SAMPLE_OUTPUT)
    assert "tests/test_foo.py::test_two" in result.failed
    assert "tests/test_foo.py::test_one" in result.passed

def test_parse_output_all_passing_when_no_failures():
    result = _parse_output("tests/test_foo.py::test_one PASSED  [ 100%]")
    assert result.all_passing is True

class NoopProvider:
    def send_message(self, message):
        return LLMResponse(text="I see no changes are needed.", tool_calls=[])
    def send_tool_results(self, results):
        return LLMResponse(text="done", tool_calls=[])


class FixingProvider:
    def send_message(self, message):
        return LLMResponse(
            text=None,
            tool_calls=[ToolCall(
                id="fix-1",
                name="edit_file",
                args={
                    "path": "example.py",
                    "old_text": '    return "failed"',
                    "new_text": '    return "login failed"',
                }
            )]
        )
    def send_tool_results(self, results):
        return LLMResponse(text="Fixed the login function.", tool_calls=[])


class BreakingProvider:
    def send_message(self, message):
        return LLMResponse(
            text=None,
            tool_calls=[ToolCall(
                id="break-1",
                name="edit_file",
                args={
                    "path": "example.py",
                    "old_text": '        return "logged in"',
                    "new_text": '        return "broken"',
                }
            )]
        )
    def send_tool_results(self, results):
        return LLMResponse(text="Done.", tool_calls=[])

def test_already_done_when_all_tests_pass(monkeypatch):
    calls = []

    class SpyProvider:
        def send_message(self, message):
            calls.append(message)
            return LLMResponse(text="done", tool_calls=[])
        def send_tool_results(self, results):
            return LLMResponse(text="done", tool_calls=[])

    from agent import workflow
    monkeypatch.setattr(workflow, "_run_tests", lambda: SuiteResult(
        passed=["tests/test_foo.py::test_one"],
        failed=[],
    ))

    agent = Agent(SpyProvider(), tools)
    result = run_task("fix something", agent)

    assert result.status == "already_done"
    assert calls == []


def test_success_when_agent_fixes_failing_test(monkeypatch):
    from agent import workflow
    from pathlib import Path

    example = Path("example.py")
    original = example.read_text()

    fake_baseline = SuiteResult(
        passed=["tests/test_examply.py::test_login_with_user"],
        failed=["tests/test_examply.py::test_login_without_user"],
    )
    fake_final = SuiteResult(
        passed=["tests/test_examply.py::test_login_with_user",
                "tests/test_examply.py::test_login_without_user"],
        failed=[],
    )

    call_count = [0]
    def fake_run_tests():
        call_count[0] += 1
        return fake_baseline if call_count[0] == 1 else fake_final

    monkeypatch.setattr(workflow, "_run_tests", fake_run_tests)

    try:
        agent = Agent(FixingProvider(), tools)
        result = run_task("fix the login function", agent)
        assert result.status == "success"
        assert result.final is not None
        assert '    return "login failed"' in example.read_text()
    finally:
        example.write_text(original)


def test_failure_when_agent_does_nothing(monkeypatch):
    from agent import workflow

    fake_baseline = SuiteResult(
        passed=["tests/test_foo.py::test_one"],
        failed=["tests/test_foo.py::test_two"],
    )
    fake_final = SuiteResult(
        passed=["tests/test_foo.py::test_one"],
        failed=["tests/test_foo.py::test_two"],
    )

    call_count = [0]
    def fake_run_tests():
        call_count[0] += 1
        return fake_baseline if call_count[0] == 1 else fake_final

    monkeypatch.setattr(workflow, "_run_tests", fake_run_tests)

    agent = Agent(NoopProvider(), tools)
    result = run_task("fix something", agent)

    assert result.status == "failure"


def test_regression_when_agent_breaks_passing_test(monkeypatch):
    from agent import workflow

    fake_baseline = SuiteResult(
        passed=["tests/test_foo.py::test_one", "tests/test_foo.py::test_two"],
        failed=["tests/test_foo.py::test_three"],
    )
    fake_final = SuiteResult(
        passed=["tests/test_foo.py::test_three"],
        failed=["tests/test_foo.py::test_one", "tests/test_foo.py::test_two"],
    )

    call_count = [0]
    def fake_run_tests():
        call_count[0] += 1
        return fake_baseline if call_count[0] == 1 else fake_final

    monkeypatch.setattr(workflow, "_run_tests", fake_run_tests)

    agent = Agent(NoopProvider(), tools)
    result = run_task("fix something", agent)

    assert result.status == "regression"
