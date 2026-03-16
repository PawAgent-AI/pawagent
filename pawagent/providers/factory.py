from __future__ import annotations

from pawagent.providers.base import BaseProvider
from pawagent.providers.claude_provider import ClaudeProvider
from pawagent.providers.codex_provider import CodexProvider
from pawagent.providers.gemini_provider import GeminiProvider
from pawagent.providers.gemini_cli_provider import GeminiCliProvider
from pawagent.providers.mock_provider import MockProvider
from pawagent.providers.openai_provider import OpenAIProvider


def build_provider(
    provider_name: str,
    openai_model: str,
    codex_model: str,
    gemini_model: str,
    claude_model: str = "claude-sonnet-4-6",
) -> BaseProvider:
    if provider_name == "mock":
        return MockProvider()
    if provider_name == "openai":
        return OpenAIProvider(model=openai_model)
    if provider_name == "gemini":
        return GeminiProvider(model=gemini_model)
    if provider_name == "gemini-cli":
        return GeminiCliProvider(model=gemini_model)
    if provider_name == "codex":
        return CodexProvider(model=codex_model)
    if provider_name == "claude":
        return ClaudeProvider(model=claude_model)
    raise ValueError(f"Unsupported provider: {provider_name}")
