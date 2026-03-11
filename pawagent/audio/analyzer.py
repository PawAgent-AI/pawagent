from __future__ import annotations

from pathlib import Path

from pawagent.models.analysis import ExpressionResult, MotivationResult, UnifiedAnalysisResult
from pawagent.models.behavior import BehaviorResult
from pawagent.models.mood import MoodResult
from pawagent.providers.base import BaseProvider
from pawagent.vision.prompts import AUDIO_ANALYSIS_PROMPT


class AudioAnalyzer:
    def __init__(self, provider: BaseProvider) -> None:
        self._provider = provider

    def analyze(self, path: Path) -> UnifiedAnalysisResult:
        raw = self._provider.analyze_audio(str(path), AUDIO_ANALYSIS_PROMPT)
        return UnifiedAnalysisResult(
            emotion=MoodResult(
                primary=str(raw["emotion"]["label"]),
                confidence=float(raw["emotion"]["confidence"]),
                arousal=str(raw["emotion"].get("arousal", "")),
                tags=[str(tag) for tag in raw["emotion"].get("tags", [])],
                alternatives=[str(item) for item in raw["emotion"].get("alternatives", [])],
                evidence=[str(item) for item in raw["emotion"].get("evidence", [])],
                uncertainty_note=str(raw["emotion"].get("uncertainty_note", "")),
            ),
            behavior=BehaviorResult(
                label=str(raw["behavior"]["label"]),
                confidence=float(raw["behavior"]["confidence"]),
                target=str(raw["behavior"].get("target", "")),
                intensity=str(raw["behavior"].get("intensity", "")),
                evidence=[str(item) for item in raw["behavior"].get("evidence", [])],
                alternatives=[str(item) for item in raw["behavior"].get("alternatives", [])],
                uncertainty_note=str(raw["behavior"].get("uncertainty_note", "")),
                notes=str(raw["behavior"].get("notes", "")),
            ),
            motivation=MotivationResult(
                label=str(raw["motivation"]["label"]),
                confidence=float(raw["motivation"]["confidence"]),
                alternatives=[str(item) for item in raw["motivation"].get("alternatives", [])],
                evidence=[str(item) for item in raw["motivation"].get("evidence", [])],
                uncertainty_note=str(raw["motivation"].get("uncertainty_note", "")),
            ),
            expression=ExpressionResult(
                plain_text=str(raw["expression"].get("plain_text", raw["expression"].get("text", ""))),
                pet_voice=str(raw["expression"].get("pet_voice", raw["expression"].get("text", ""))),
                tone=str(raw["expression"].get("tone", "")),
                grounded_in=[str(item) for item in raw["expression"].get("grounded_in", [])],
                confidence=float(raw["expression"]["confidence"]),
            ),
            evidence=[str(item) for item in raw.get("evidence", [])],
        )
