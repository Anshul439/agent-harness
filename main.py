from dotenv import load_dotenv

from agent.loop import Agent
from agent.providers import get_provider
from agent.tools import tools
from agent.types import ProviderError, TurnLimitError


load_dotenv()

SYSTEM_PROMPT = """You are a coding agent working on a Python repository.

You have tools to read, search, list, and edit files, and to run the test suite.

Follow this workflow:
1. Read the relevant file(s) first to understand the current code.
2. Make the minimal edit needed to complete the task.
3. Run the tests to verify your change is correct.
4. Return a short summary of what you changed and whether tests passed.

Only edit files that are relevant to the task. Do not make unnecessary changes."""

provider = get_provider(tools, system_prompt=SYSTEM_PROMPT)

agent = Agent(provider, tools)

from rich.console import Console
console = Console(highlight=False)

try:
    result = agent.run(
        'Change the login function so that when user is falsy, it returns "login failed" instead of "failed".'
    )
    console.print(f"\n[bold]done.[/] {result}")
except TurnLimitError as e:
    console.print(f"\n[bold red]turn limit reached:[/] {e}")
except ProviderError as e:
    console.print(f"\n[bold red]provider error:[/] {e}")
