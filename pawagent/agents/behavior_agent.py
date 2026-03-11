from __future__ import annotations

from pathlib import Path

from pawagent.core.unified_analysis import UnifiedMediaAnalysisService
from pawagent.memory.store import AnalysisStore
from pawagent.models.behavior import BehaviorResult
from pawagent.personality.profiler import PersonalityProfiler
from pawagent.providers.base import BaseProvider


class PetBehaviorAgent:
    def __init__(
        self,
        provider: BaseProvider,
        memory_store: AnalysisStore,
        profiler: PersonalityProfiler,
    ) -> None:
        del profiler
        self._analysis_service = UnifiedMediaAnalysisService(provider=provider, memory_store=memory_store)

    def analyze_image(self, image_path: Path, pet_id: str, pet_name: str, species: str) -> BehaviorResult:
        return self.analyze_media(path=image_path, pet_id=pet_id, pet_name=pet_name, species=species, modality="image")

    def analyze_media(self, path: Path, pet_id: str, pet_name: str, species: str, modality: str = "image") -> BehaviorResult:
        del pet_name
        record = self._analysis_service.analyze(path=path, pet_id=pet_id, species=species, modality=modality)
        return record.analysis.behavior
