import subprocess
from dataclasses import dataclass, field

from rich.console import Console

from agent.loop import Agent
from agent.tools import ROOT

console = Console(highlight=False)

@dataclass
class SuiteResult:
    passed: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)

    @property
    def all_passing(self) -> bool:
        return len(self.failed) == 0


@dataclass
class TaskResult:
    status: str          # "already_done" | "success" | "failure" | "regression"
    message: str
    baseline: SuiteResult
    final: SuiteResult | None = None
    agent_output: str | None = None

def _run_tests() -> SuiteResult:
    """Run pytest with verbose output and return parsed results."""
    result = subprocess.run(
        ["pytest", "-v", "--tb=no"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return _parse_output(result.stdout + result.stderr)


def _parse_output(output: str) -> SuiteResult:
    """Parse pytest -v output into passed and failed test names."""
    passed = []
    failed = []

    for line in output.splitlines():
        if " PASSED" in line:
            name = line.split(" PASSED")[0].strip()
            passed.append(name)
        elif " FAILED" in line:
            name = line.split(" FAILED")[0].strip()
            failed.append(name)

    return SuiteResult(passed=passed, failed=failed)

def run_task(task: str, agent: Agent) -> TaskResult:
    """Run tests before and after the agent, skipping when already passing."""
    console.print("\n[bold]◆ pre-flight[/] running tests...")
    baseline = _run_tests()

    if baseline.all_passing:
        console.print("  [green]all tests pass — task already complete[/]")
        return TaskResult(
            status="already_done",
            message="All tests passed before the agent ran. Nothing to do.",
            baseline=baseline,
        )

    console.print(f"  [yellow]{len(baseline.failed)} test(s) failing:[/]")
    for name in baseline.failed:
        console.print(f"    [red]✗[/] {name}")

    failing_list = "\n".join(f"- {name}" for name in baseline.failed)
    full_task = (
        f"{task}\n\n"
        f"The following tests are currently failing — fix them:\n{failing_list}"
    )

    console.print("\n[bold]◆ running agent[/]")
    agent_output = agent.run(full_task)

    console.print("\n[bold]◆ post-flight[/] verifying changes...")
    final = _run_tests()

    newly_passing = set(baseline.failed) - set(final.failed)
    regressions = set(baseline.passed) - set(final.passed)

    if regressions:
        console.print(f"  [bold red]regression — {len(regressions)} test(s) broken:[/]")
        for name in regressions:
            console.print(f"    [red]✗[/] {name}")
        return TaskResult(
            status="regression",
            message=f"Agent introduced {len(regressions)} regression(s).",
            baseline=baseline,
            final=final,
            agent_output=agent_output,
        )

    if not newly_passing:
        console.print("  [red]no previously failing tests were fixed[/]")
        return TaskResult(
            status="failure",
            message="Agent ran but did not fix any of the failing tests.",
            baseline=baseline,
            final=final,
            agent_output=agent_output,
        )

    console.print(f"  [green]✓ fixed {len(newly_passing)} test(s)[/]")
    return TaskResult(
        status="success",
        message=f"Fixed {len(newly_passing)} test(s). {len(final.failed)} still failing.",
        baseline=baseline,
        final=final,
        agent_output=agent_output,
    )
