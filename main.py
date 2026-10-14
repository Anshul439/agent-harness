from dotenv import load_dotenv
from rich.console import Console

from agent.loop import Agent
from agent.providers import get_provider
from agent.tools import tools
from agent.types import ProviderError, TurnLimitError
from agent.workflow import run_task

load_dotenv()

console = Console(highlight=False)

SYSTEM_PROMPT = """You are a coding agent working on a Python repository.

You have EXACTLY these tools — do not call any others, and do not add parameters not listed:
  read_file(path)                          — read a file's full contents
  search_files(query, extension="")        — search file contents, returns matches with context lines
  list_files(directory=".")               — list files in a directory
  edit_file(path, old_text, new_text)      — replace the first occurrence of old_text in a file
  create_file(path, content)               — create a new file
  run_tests()                              — run the pytest test suite

Follow this workflow:
1. Search or read the relevant file(s) to understand the current code.
2. Make the minimal edit needed to complete the task.
3. Run the tests to verify your change is correct.
4. Return a short summary of what you changed and whether tests passed.

If you verify that all tests already pass and the task is already complete, say so and stop.
Only edit files that are relevant to the task. Do not make unnecessary changes."""

TASK = 'Change the login function so that when user is falsy, it returns "login failed" instead of "failed".'

provider = get_provider(tools, system_prompt=SYSTEM_PROMPT)
agent = Agent(provider, tools)

try:
    result = run_task(TASK, agent)
    console.print(f"\n[bold]status:[/] {result.status}")
    console.print(f"[bold]message:[/] {result.message}")
except TurnLimitError as e:
    console.print(f"\n[bold red]turn limit reached:[/] {e}")
except ProviderError as e:
    console.print(f"\n[bold red]provider error:[/] {e}")
