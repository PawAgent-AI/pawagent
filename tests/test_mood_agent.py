from __future__ import annotations

from pathlib import Path

from pawagent.agents.mood_agent import PetMoodAgent
from pawagent.memory.store import InMemoryAnalysisStore
from pawagent.personality.profiler import PersonalityProfiler
from pawagent.providers.mock_provider import MockProvider


def test_mood_agent_analyzes_image_and_persists_history() -> None:
    store = InMemoryAnalysisStore()
    profiler = PersonalityProfiler(store)
    agent = PetMoodAgent(provider=MockProvider(), memory_store=store, profiler=profiler)

    result = agent.analyze_image(
        image_path=Path("happy-dog.jpg"),
        pet_id="pet-1",
        pet_name="Milo",
        species="dog",
    )

    assert result.mood.primary == "playful"
    assert result.mood.arousal == "high"
    assert result.behavior.label == "seeking interaction"
    assert result.personality.pet_id == "pet-1"
    assert "Milo appears playful" in result.summary
    assert len(store.get_recent_analysis("pet-1")) == 1
