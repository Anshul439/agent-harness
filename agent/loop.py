import inspect
import json
import time

from rich.console import Console

from agent.types import ProviderError, TurnLimitError

console = Console(highlight=False)


class Agent:

    def __init__(self, provider, tools, max_turns: int = 25):
        self.provider = provider
        self.tools = tools
        self.max_turns = max_turns

    def run(self, task):
        response = self._call_provider(self.provider.send_message, task)

        turns = 0
        while response.tool_calls:
            turns += 1
            if turns > self.max_turns:
                raise TurnLimitError(
                    f"Agent exceeded {self.max_turns} turns without finishing. "
                    "The model may be stuck in a loop."
                )

            results = []

            for call in response.tool_calls:

                args_str = " ".join(f"{k}={json.dumps(v)}" for k, v in call.args.items())
                console.print(f"[bold]→[/] [cyan]{call.name}[/] [dim]{args_str}[/]")

                result = self._execute(call)

                is_error = isinstance(result, str) and result.startswith("Error")
                for line in str(result).splitlines():
                    console.print(f"  [red]{line}[/]" if is_error else f"  [dim]{line}[/]")

                results.append((call, result))

            response = self._call_provider(self.provider.send_tool_results, results)

        return response.text

    def _call_provider(self, fn, *args):
        """Call fn(*args). On failure, wait 5 s and retry once, then raise ProviderError."""
        try:
            return fn(*args)
        except Exception as error:
            console.print(f"  [yellow]provider error:[/] {error}")
            console.print(f"  [yellow]retrying in 5 s...[/]")
            time.sleep(5)
            try:
                return fn(*args)
            except Exception as retry_error:
                raise ProviderError(
                    f"Provider failed after retry: {retry_error}"
                ) from retry_error

    def _execute(self, call):
        """Run a tool call safely. Any failure becomes text the model can read."""

        tool = self.tools.get(call.name)

        if tool is None:
            return (
                f"Error: unknown tool '{call.name}'. "
                f"Available: {', '.join(self.tools)}"
            )

        try:
            inspect.signature(tool.func).bind(**call.args)
            return tool.func(**call.args)

        except TypeError as error:
            return f"Error: bad arguments for '{call.name}': {error}"

        except Exception as error:
            return f"Error: '{call.name}' failed: {error}"
