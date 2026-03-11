from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pawagent.agents.mood_agent import PetMoodAgent
from pawagent.memory.store import InMemoryAnalysisStore
from pawagent.personality.profiler import PersonalityProfiler
from pawagent.providers.mock_provider import MockProvider


def main() -> None:
    store = InMemoryAnalysisStore()
    profiler = PersonalityProfiler(store)
    agent = PetMoodAgent(provider=MockProvider(), memory_store=store, profiler=profiler)
    result = agent.analyze_image(
        image_path=Path("happy-dog.jpg"),
        pet_id="demo-pet",
        pet_name="Milo",
        species="dog",
    )
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
