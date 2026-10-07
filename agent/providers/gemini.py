from google.genai import types

from agent.providers.base import LLMProvider
from agent.types import LLMResponse, ToolCall, ToolSpec


class GeminiProvider(LLMProvider):

    def __init__(self, client, tools: dict[str, ToolSpec], model: str = "gemini-3.8-flash", system_prompt: str | None = None):
        self.client = client  # hold reference so it isn't garbage collected
        config = {
            "tools": [
                _to_gemini_tool(tool)
                for tool in tools.values()
            ],
            "automatic_function_calling": {
                "disable": True
            },
        }
        if system_prompt:
            config["system_instruction"] = system_prompt
        self.chat = client.chats.create(model=model, config=config)

    def send_message(self, message) -> LLMResponse:
        response = self.chat.send_message(message)
        return _parse_response(response)

    def send_tool_results(self, results) -> LLMResponse:
        # Package all tool results into a single user turn and send them together.
        # Gemini expects one Content with multiple function-response parts.
        parts = [
            types.Part.from_function_response(
                name=call.name,
                response={"result": result},
            )
            for call, result in results
        ]

        response = self.chat.send_message(parts)

        return _parse_response(response)


def _parse_response(response) -> LLMResponse:
    """Walk all parts — collect text and every function call."""
    text_parts = []
    tool_calls = []

    for index, part in enumerate(response.candidates[0].content.parts):
        if part.function_call:
            fc = part.function_call
            tool_calls.append(
                ToolCall(
                    # Gemini returns an id on newer models; fall back to a stable name.
                    id=fc.id or f"gemini-call-{index}",
                    name=fc.name,
                    args=dict(fc.args or {}),
                )
            )
        elif part.text:
            text_parts.append(part.text)

    return LLMResponse(
        text="".join(text_parts) or None,
        tool_calls=tool_calls,
    )


def _to_gemini_tool(tool: ToolSpec) -> types.Tool:
    return types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name=tool.name,
                description=tool.description,
                parameters=tool.parameters,
            )
        ]
    )
