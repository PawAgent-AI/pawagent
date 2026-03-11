from __future__ import annotations

from pawagent.agents.personality_agent import PetPersonalityAgent
from pawagent.memory.store import InMemoryAnalysisStore
from pawagent.models.analysis import AnalysisRecord, ExpressionResult, MotivationResult, UnifiedAnalysisResult
from pawagent.models.behavior import BehaviorResult
from pawagent.models.mood import MoodResult
from pawagent.personality.profiler import PersonalityProfiler
from pawagent.personality.store import InMemoryPersonalityProfileStore


def test_personality_agent_returns_profile_from_history() -> None:
    store = InMemoryAnalysisStore()
    profile_store = InMemoryPersonalityProfileStore()
    store.add_record(
        AnalysisRecord(
            pet_id="pet-9",
            content_hash="hash-a",
            source_path="play-a.jpg",
            analysis=UnifiedAnalysisResult(
                emotion=MoodResult(primary="playful", confidence=0.92, tags=["engaged"]),
                behavior=BehaviorResult(label="seeking interaction", confidence=0.86, notes="Actively social."),
                motivation=MotivationResult(
                    label="seeking engagement",
                    confidence=0.81,
                    alternatives=["wants play"],
                    evidence=["active stance"],
                    uncertainty_note="Single image limits specificity.",
                ),
                expression=ExpressionResult(
                    plain_text="The pet appears playful and is actively seeking interaction.",
                    pet_voice="I want to play with you right now.",
                    tone="eager",
                    grounded_in=["active stance"],
                    confidence=0.78,
                ),
                evidence=["active stance"],
            ),
        )
    )
    store.add_record(
        AnalysisRecord(
            pet_id="pet-9",
            content_hash="hash-b",
            source_path="play-b.jpg",
            analysis=UnifiedAnalysisResult(
                emotion=MoodResult(primary="playful", confidence=0.89, tags=["active"]),
                behavior=BehaviorResult(label="seeking interaction", confidence=0.83, notes="Play solicitation."),
                motivation=MotivationResult(
                    label="seeking engagement",
                    confidence=0.79,
                    alternatives=["wants continued play"],
                    evidence=["open posture"],
                    uncertainty_note="Single image limits specificity.",
                ),
                expression=ExpressionResult(
                    plain_text="The pet appears playful and remains engaged in interaction.",
                    pet_voice="Let's keep playing.",
                    tone="eager",
                    grounded_in=["open posture"],
                    confidence=0.74,
                ),
                evidence=["open posture"],
            ),
        )
    )

    agent = PetPersonalityAgent(
        memory_store=store,
        profiler=PersonalityProfiler(store, profile_store=profile_store),
    )
    profile = agent.get_profile("pet-9")
    traits = {trait.name: trait.value for trait in profile.traits}

    assert profile.pet_id == "pet-9"
    assert traits["energy_level"] >= 0.89
    assert traits["playfulness"] >= 0.9
    snapshot = profile_store.get_snapshot("pet-9")
    assert snapshot is not None
    assert snapshot.based_on_record_count == 2
