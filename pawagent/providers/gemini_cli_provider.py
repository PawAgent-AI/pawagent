from __future__ import annotations

from pathlib import Path

import json

from pawagent.models.analysis import UnifiedAnalysisResult
from pawagent.models.media import ImageInput
from pawagent.providers.cli_base import CliAgentProvider
from pawagent.providers.errors import ProviderExecutionError
from pawagent.providers.parsing import normalize_expression_payload, parse_json_text


class GeminiCliProvider(CliAgentProvider):
    def __init__(
        self,
        model: str = "gemini-2.5-flash",
        gemini_bin: str = "gemini",
        runner=None,
    ) -> None:
        super().__init__(runner=runner)
        self._model = model
        self._gemini_bin = gemini_bin

    def build_command(self, image: ImageInput, prompt: str) -> list[str]:
        image_path = self.resolve_image_path(image)
        return [
            self._gemini_bin,
            "--model",
            self._model,
            "--prompt",
            self._build_prompt(prompt, image_path),
            "--output-format",
            "json",
            "--approval-mode",
            "plan",
            "--include-directories",
            str(image_path.parent),
        ]

    def provider_label(self) -> str:
        return "Gemini CLI provider"

    def _build_prompt(self, prompt: str, image_path: Path) -> str:
        return (
            f"{prompt}\n\n"
            f"Analyze the local image file at this absolute path: {image_path}\n"
            "You may read the file from the workspace if needed."
        )

    def analyze_audio(self, audio_path: str, prompt: str) -> dict[str, object]:
        del audio_path, prompt
        raise ProviderExecutionError("Gemini CLI provider audio analysis is not implemented yet.")

    def analyze_video(self, video_path: str, prompt: str) -> dict[str, object]:
        return super().analyze_video(video_path, prompt)

    def render_expression(
        self,
        analysis: UnifiedAnalysisResult,
        locale: str,
        style: str = "default",
    ) -> dict[str, object]:
        if locale.lower().startswith("en"):
            return analysis.expression.model_dump(mode="json")
        prompt = self._build_expression_prompt(analysis=analysis, locale=locale, style=style)
        command = [
            self._gemini_bin,
            "--model",
            self._model,
            "--prompt",
            prompt,
            "--output-format",
            "json",
            "--approval-mode",
            "plan",
        ]
        result = self._runner(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            message = result.stderr.strip() or result.stdout.strip() or self.default_error_message()
            raise ProviderExecutionError(f"{self.provider_label()} failed: {message}")
        return normalize_expression_payload(
            parse_json_text(result.stdout),
            default_grounding=analysis.expression.grounded_in or analysis.evidence,
            default_locale=locale,
            default_style=style,
        )

    def _build_expression_prompt(self, analysis: UnifiedAnalysisResult, locale: str, style: str) -> str:
        payload = json.dumps(analysis.model_dump(mode="json"), ensure_ascii=True)
        return (
            "Render the pet expression into the requested locale using only the provided structured analysis.\n"
            f"Target locale: {locale}\n"
            f"Style: {style}\n"
            "Return JSON only with this exact schema: "
            '{"plain_text":"string","pet_voice":"string","tone":"string","grounded_in":["string"],'
            '"confidence":0.0,"locale":"string","source_language":"string","style":"string"}\n'
            "Do not introduce new facts beyond the analysis.\n"
            f"Analysis JSON: {payload}"
        )
