from __future__ import annotations

from pathlib import Path

from pawagent.agents.behavior_agent import PetBehaviorAgent
from pawagent.agents.expression_agent import PetExpressionAgent
from pawagent.agents.mood_agent import PetEmotionAgent
from pawagent.agents.motivation_agent import PetMotivationAgent
from pawagent.expression.store import InMemoryExpressionLocalizationStore
from pawagent.memory.store import InMemoryAnalysisStore
from pawagent.personality.profiler import PersonalityProfiler


class _CountingProvider:
    def __init__(self) -> None:
        self.calls = 0
        self.render_calls = 0

    def analyze_image(self, image: object, prompt: str) -> dict[str, object]:
        del image, prompt
        self.calls += 1
        return {
            "emotion": {"label": "alert", "confidence": 0.84, "tags": ["focused"]},
            "behavior": {
                "label": "monitoring surroundings",
                "confidence": 0.81,
                "target": "environment",
                "notes": "Attentive posture directed outward.",
            },
            "motivation": {
                "label": "monitoring for change",
                "confidence": 0.62,
                "alternatives": ["checking environment"],
                "evidence": ["forward attention"],
                "uncertainty_note": "Trigger not visible.",
            },
            "expression": {
                "plain_text": "The pet appears alert and is monitoring the surroundings.",
                "pet_voice": "I am watching everything carefully right now.",
                "tone": "watchful",
                "grounded_in": ["forward attention"],
                "confidence": 0.74,
            },
            "evidence": ["forward attention"],
        }

    def render_expression(self, analysis, locale: str, style: str = "default") -> dict[str, object]:
        del style
        self.render_calls += 1
        return {
            "plain_text": "宠物看起来比较警觉，并且在留意周围环境。",
            "pet_voice": "我想先确认周围有没有变化。",
            "tone": analysis.expression.tone,
            "grounded_in": analysis.expression.grounded_in,
            "confidence": 0.74,
            "locale": locale,
            "source_language": "en",
            "style": "default",
        }


def test_task_views_reuse_cached_analysis_for_same_image() -> None:
    store = InMemoryAnalysisStore()
    provider = _CountingProvider()
    profiler = PersonalityProfiler(store)
    emotion_agent = PetEmotionAgent(provider=provider, memory_store=store, profiler=profiler)  # type: ignore[arg-type]
    behavior_agent = PetBehaviorAgent(provider=provider, memory_store=store, profiler=profiler)  # type: ignore[arg-type]
    motivation_agent = PetMotivationAgent(provider=provider, memory_store=store, profiler=profiler)  # type: ignore[arg-type]
    expression_agent = PetExpressionAgent(
        provider=provider,
        memory_store=store,
        profiler=profiler,
        localization_store=InMemoryExpressionLocalizationStore(),
    )  # type: ignore[arg-type]

    image_path = Path("same-image.jpg")
    emotion_agent.analyze_image(image_path=image_path, pet_id="pet-1", pet_name="Milo", species="dog")
    behavior = behavior_agent.analyze_image(image_path=image_path, pet_id="pet-1", pet_name="Milo", species="dog")
    motivation = motivation_agent.analyze_image(image_path=image_path, pet_id="pet-1", pet_name="Milo", species="dog")
    expression = expression_agent.express_image(
        image_path=image_path,
        pet_id="pet-1",
        pet_name="Milo",
        species="dog",
        locale="zh-CN",
    )

    assert provider.calls == 1
    assert provider.render_calls == 1
    assert behavior.label == "monitoring surroundings"
    assert motivation.label == "monitoring for change"
    assert expression.pet_voice == "我想先确认周围有没有变化。"
