from __future__ import annotations

from pathlib import Path

from pawagent.core.content_hash import compute_content_hash
from pawagent.memory.store import AnalysisStore
from pawagent.models.analysis import AnalysisRecord
from pawagent.providers.base import BaseProvider
from pawagent.video.analyzer import VideoAnalyzer
from pawagent.vision.analyzer import VisionAnalyzer


ANALYSIS_VERSIONS = {
    "image": "unified_image_v1",
    "video": "unified_video_v1",
}
PROMPT_VERSIONS = {
    "image": "unified_image_v1",
    "video": "unified_video_v1",
}


class UnifiedMediaAnalysisService:
    def __init__(self, provider: BaseProvider, memory_store: AnalysisStore) -> None:
        self._provider = provider
        self._memory_store = memory_store
        self._vision = VisionAnalyzer(provider)
        self._video = VideoAnalyzer(provider)

    def analyze(self, path: Path, pet_id: str, species: str, modality: str = "image") -> AnalysisRecord:
        normalized_modality = modality.strip().lower()
        if normalized_modality not in ANALYSIS_VERSIONS:
            raise ValueError(f"Unsupported modality: {modality}")

        content_hash = compute_content_hash(path)
        analysis_version = ANALYSIS_VERSIONS[normalized_modality]
        cached = self._memory_store.get_cached_analysis(content_hash=content_hash, analysis_version=analysis_version)
        if cached is not None:
            if cached.pet_id != pet_id:
                cached = cached.model_copy(update={"pet_id": pet_id, "source_path": str(path)})
                self._memory_store.add_record(cached)
            return cached

        if normalized_modality == "image":
            analysis = self._vision.analyze(image_path=path, species=species)
        else:
            analysis = self._video.analyze(path=path, species=species)
        record = AnalysisRecord(
            pet_id=pet_id,
            content_hash=content_hash,
            source_path=str(path),
            source_modality=normalized_modality,
            analysis=analysis,
            provider=self._provider.__class__.__name__,
            model=getattr(self._provider, "_model", ""),
            analysis_version=analysis_version,
            prompt_version=PROMPT_VERSIONS[normalized_modality],
            metadata={"species": species, "modality": normalized_modality},
        )
        self._memory_store.add_record(record)
        return record


UnifiedImageAnalysisService = UnifiedMediaAnalysisService
