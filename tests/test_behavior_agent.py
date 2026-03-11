from __future__ import annotations

from pathlib import Path

from pawagent.agents.behavior_agent import PetBehaviorAgent
from pawagent.memory.store import InMemoryAnalysisStore
from pawagent.models.analysis import AnalysisRecord, ExpressionResult, MotivationResult, UnifiedAnalysisResult
from pawagent.models.behavior import BehaviorResult
from pawagent.models.mood import MoodResult
from pawagent.personality.profiler import PersonalityProfiler
from pawagent.providers.mock_provider import MockProvider


def test_behavior_agent_infers_behavior_from_mood_and_context() -> None:
    store = InMemoryAnalysisStore()
    store.add_record(
        AnalysisRecord(
            pet_id="pet-1",
            content_hash="hash-1",
            source_path="curious.jpg",
            analysis=UnifiedAnalysisResult(
                emotion=MoodResult(primary="curious", confidence=0.7, tags=["observant"]),
                behavior=BehaviorResult(label="observing", confidence=0.72, notes="Investigative posture."),
                motivation=MotivationResult(
                    label="understanding the environment",
                    confidence=0.66,
                    alternatives=["checking novelty"],
                    evidence=["steady gaze"],
                    uncertainty_note="Single image limits stronger inference.",
                ),
                expression=ExpressionResult(
                    plain_text="The pet appears curious and is observing the environment.",
                    pet_voice="I am checking this out.",
                    tone="curious",
                    grounded_in=["steady gaze"],
                    confidence=0.69,
                ),
                evidence=["steady gaze"],
            ),
        )
    )
    profiler = PersonalityProfiler(store)
    agent = PetBehaviorAgent(provider=MockProvider(), memory_store=store, profiler=profiler)

    result = agent.analyze_image(
        image_path=Path("park-play-session.jpg"),
        pet_id="pet-1",
        pet_name="Milo",
        species="dog",
    )

    assert result.label == "seeking interaction"
    assert result.confidence > 0.8
    assert result.notes
