from dotenv import load_dotenv

from agent.loop import Agent
from agent.providers import get_provider
from agent.tools import tools


load_dotenv()

provider = get_provider(tools)

agent = Agent(provider, tools)

result = agent.run(
    'Change the login function so that when user is falsy, it returns "login failed" instead of "failed".'
)

from rich.console import Console
console = Console(highlight=False)
console.print(f"\n[bold]done.[/] {result}")
