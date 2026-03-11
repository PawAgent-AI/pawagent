from __future__ import annotations

from pathlib import Path

from pawagent.core.unified_analysis import UnifiedMediaAnalysisService
from pawagent.memory.context_builder import build_context
from pawagent.memory.store import AnalysisStore
from pawagent.memory.summarizer import summarize_analysis
from pawagent.models.analysis import AnalysisResult
from pawagent.models.pet import Pet
from pawagent.personality.profiler import PersonalityProfiler
from pawagent.providers.base import BaseProvider


class PetEmotionAgent:
    def __init__(
        self,
        provider: BaseProvider,
        memory_store: AnalysisStore,
        profiler: PersonalityProfiler,
    ) -> None:
        self._memory_store = memory_store
        self._profiler = profiler
        self._analysis_service = UnifiedMediaAnalysisService(provider=provider, memory_store=memory_store)

    def analyze_image(self, image_path: Path, pet_id: str, pet_name: str, species: str) -> AnalysisResult:
        return self.analyze_media(path=image_path, pet_id=pet_id, pet_name=pet_name, species=species, modality="image")

    def analyze_media(self, path: Path, pet_id: str, pet_name: str, species: str, modality: str = "image") -> AnalysisResult:
        pet = Pet(pet_id=pet_id, name=pet_name, species=species)
        history = self._memory_store.get_recent_analysis(pet_id=pet_id)
        record = self._analysis_service.analyze(path=path, pet_id=pet_id, species=species, modality=modality)
        profile = self._profiler.get_profile(pet_id=pet_id)
        context = build_context(history)
        summary = summarize_analysis(pet=pet, mood=record.analysis.emotion, profile=profile, context=context)
        return AnalysisResult(pet=pet, analysis=record.analysis, personality=profile, summary=summary)


PetMoodAgent = PetEmotionAgent
