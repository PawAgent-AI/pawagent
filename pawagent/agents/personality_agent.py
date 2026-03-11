from __future__ import annotations

from pawagent.memory.store import AnalysisStore
from pawagent.models.personality import PersonalityProfile
from pawagent.personality.profiler import PersonalityProfiler


class PetPersonalityAgent:
    def __init__(self, memory_store: AnalysisStore, profiler: PersonalityProfiler) -> None:
        self._memory_store = memory_store
        self._profiler = profiler

    def get_profile(self, pet_id: str) -> PersonalityProfile:
        self._memory_store.get_recent_analysis(pet_id=pet_id, limit=1)
        return self._profiler.get_profile(pet_id=pet_id)
