import os

from agent.providers.base import LLMProvider


def get_provider(tools, name: str | None = None, system_prompt: str | None = None) -> LLMProvider:
    """Return the right provider based on LLM_PROVIDER env var (or explicit name)."""

    name = (name or os.getenv("LLM_PROVIDER") or "gemini").lower()

    model = os.getenv("LLM_MODEL")

    if name == "gemini":
        from google import genai
        from agent.providers.gemini import GeminiProvider

        client = genai.Client()
        return GeminiProvider(client, tools, model=model or "gemini-3.8-flash", system_prompt=system_prompt)

    if name == "groq":
        from groq import Groq
        from agent.providers.groq import GroqProvider

        client = Groq()
        return GroqProvider(client, tools, model=model or "openai/gpt-oss-120b", system_prompt=system_prompt)

    raise ValueError(f"Unknown provider: {name!r}. Choose 'gemini' or 'groq'.")
