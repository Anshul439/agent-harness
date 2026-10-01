import json

from groq import Groq

from agent.providers.base import LLMProvider
from agent.types import LLMResponse, ToolCall, ToolSpec


class GroqProvider(LLMProvider):

    def __init__(self, client: Groq, tools: dict[str, ToolSpec], model: str = "openai/gpt-oss-120b", system_prompt: str | None = None):
        self.client = client
        self.tools = tools
        self.model = model
        # Groq has no chat object — we manage history ourselves as a plain list.
        # System prompt, if given, is the first and only permanent entry.
        self.messages = []
        if system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})

    def send_message(self, message) -> LLMResponse:
        self.messages.append({"role": "user", "content": message})
        return self._complete()

    def send_tool_results(self, results) -> LLMResponse:
        for call, result in results:
            self.messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "name": call.name,
                "content": str(result),
            })
        return self._complete()

    def _complete(self) -> LLMResponse:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            tools=[_to_groq_tool(tool) for tool in self.tools.values()],
            tool_choice="auto",
        )

        message = response.choices[0].message

        self.messages.append(message)

        tool_calls = [
            ToolCall(
                id=call.id,
                name=call.function.name,
                args=json.loads(call.function.arguments or "{}"),
            )
            for call in (message.tool_calls or [])
        ]

        return LLMResponse(
            text=message.content,
            tool_calls=tool_calls,
        )


def _to_groq_tool(tool: ToolSpec) -> dict:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
        },
    }
