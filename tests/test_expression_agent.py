from __future__ import annotations

from pathlib import Path

from pawagent.agents.expression_agent import PetExpressionAgent
from pawagent.expression.store import InMemoryExpressionLocalizationStore
from pawagent.memory.store import InMemoryAnalysisStore
from pawagent.personality.profiler import PersonalityProfiler
from pawagent.providers.mock_provider import MockProvider


def test_expression_agent_builds_pet_facing_expression() -> None:
    store = InMemoryAnalysisStore()
    profiler = PersonalityProfiler(store)
    agent = PetExpressionAgent(
        provider=MockProvider(),
        memory_store=store,
        profiler=profiler,
        localization_store=InMemoryExpressionLocalizationStore(),
    )

    result = agent.express_image(
        image_path=Path("sleepy-cat.jpg"),
        pet_id="pet-4",
        pet_name="Luna",
        species="cat",
    )

    assert result.pet_voice == "I feel comfortable and want to rest."
    assert result.plain_text == "The pet appears comfortable and is likely resting."
    assert result.tone == "calm"


def test_expression_agent_renders_and_caches_localized_expression() -> None:
    class _CountingProvider(MockProvider):
        def __init__(self) -> None:
            self.render_calls = 0

        def render_expression(self, analysis, locale: str, style: str = "default") -> dict[str, object]:
            self.render_calls += 1
            return super().render_expression(analysis, locale=locale, style=style)

    store = InMemoryAnalysisStore()
    profiler = PersonalityProfiler(store)
    provider = _CountingProvider()
    localization_store = InMemoryExpressionLocalizationStore()
    agent = PetExpressionAgent(
        provider=provider,
        memory_store=store,
        profiler=profiler,
        localization_store=localization_store,
    )

    first = agent.express_image(
        image_path=Path("sleepy-cat.jpg"),
        pet_id="pet-4",
        pet_name="Luna",
        species="cat",
        locale="zh-CN",
    )
    second = agent.express_image(
        image_path=Path("sleepy-cat.jpg"),
        pet_id="pet-4",
        pet_name="Luna",
        species="cat",
        locale="zh-CN",
    )

    assert provider.render_calls == 1
    assert first.locale == "zh-CN"
    assert "宠物看起来比较放松" in first.plain_text
    assert second.pet_voice == first.pet_voice
