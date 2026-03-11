from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pawagent.agents.personality_agent import PetPersonalityAgent
from pawagent.memory.store import InMemoryAnalysisStore
from pawagent.models.analysis import AnalysisRecord, ExpressionResult, MotivationResult, UnifiedAnalysisResult
from pawagent.models.behavior import BehaviorResult
from pawagent.models.mood import MoodResult
from pawagent.personality.profiler import PersonalityProfiler


def main() -> None:
    store = InMemoryAnalysisStore()
    store.add_record(
        AnalysisRecord(
            pet_id="demo-pet",
            content_hash="hash-playful",
            source_path="playful.jpg",
            analysis=UnifiedAnalysisResult(
                emotion=MoodResult(primary="playful", confidence=0.91, tags=["engaged"]),
                behavior=BehaviorResult(label="seeking interaction", confidence=0.86),
                motivation=MotivationResult(label="seeking engagement", confidence=0.8),
                expression=ExpressionResult(
                    plain_text="The pet appears playful and engaged.",
                    pet_voice="I want to keep playing.",
                    confidence=0.74,
                ),
            ),
        )
    )
    store.add_record(
        AnalysisRecord(
            pet_id="demo-pet",
            content_hash="hash-curious",
            source_path="curious.jpg",
            analysis=UnifiedAnalysisResult(
                emotion=MoodResult(primary="curious", confidence=0.78, tags=["observant"]),
                behavior=BehaviorResult(label="observing", confidence=0.72),
                motivation=MotivationResult(label="understanding the environment", confidence=0.68),
                expression=ExpressionResult(
                    plain_text="The pet appears curious and observant.",
                    pet_voice="I am checking this out.",
                    confidence=0.7,
                ),
            ),
        )
    )
    agent = PetPersonalityAgent(memory_store=store, profiler=PersonalityProfiler(store))
    profile = agent.get_profile("demo-pet")
    print(profile.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
