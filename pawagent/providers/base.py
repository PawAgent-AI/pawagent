from __future__ import annotations

from abc import ABC, abstractmethod

from pawagent.models.analysis import UnifiedAnalysisResult
from pawagent.models.media import ImageInput


class BaseProvider(ABC):
    @abstractmethod
    def analyze_image(self, image: ImageInput, prompt: str) -> dict[str, object]:
        raise NotImplementedError

    def analyze_audio(self, audio_path: str, prompt: str) -> dict[str, object]:
        raise NotImplementedError("Audio analysis is not implemented for this provider.")

    def analyze_video(self, video_path: str, prompt: str) -> dict[str, object]:
        raise NotImplementedError("Video analysis is not implemented for this provider.")

    def render_expression(
        self,
        analysis: UnifiedAnalysisResult,
        locale: str,
        style: str = "default",
    ) -> dict[str, object]:
        del analysis, locale, style
        raise NotImplementedError("Expression rendering is not implemented for this provider.")
