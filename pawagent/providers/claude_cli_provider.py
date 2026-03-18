from __future__ import annotations

import json
from pathlib import Path

from pawagent.models.analysis import UnifiedAnalysisResult
from pawagent.models.media import ImageInput
from pawagent.providers.cli_base import CliAgentProvider
from pawagent.providers.errors import ProviderExecutionError
from pawagent.providers.parsing import normalize_expression_payload, parse_json_text
from pawagent.vision.prompts import STRUCTURED_MOOD_OUTPUT_INSTRUCTIONS


class ClaudeCliProvider(CliAgentProvider):
    """Provider that shells out to the local ``claude`` CLI (Claude Code).

    Requires the ``claude`` binary to be installed and authenticated.
    Uses ``-p`` for non-interactive prompt mode and ``--output-format json``
    for structured JSON output.
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-6",
        claude_bin: str = "claude",
        runner=None,
    ) -> None:
        super().__init__(runner=runner)
        self._model = model
        self._claude_bin = claude_bin

    def build_command(self, image: ImageInput, prompt: str) -> list[str]:
        image_path = self.resolve_image_path(image)
        return [
            self._claude_bin,
            "--model",
            self._model,
            "--output-format",
            "json",
            "--allowedTools",
            "Read",
            "-p",
            self._build_prompt(prompt, image_path),
        ]

    def provider_label(self) -> str:
        return "Claude CLI provider"

    def _build_prompt(self, prompt: str, image_path: Path) -> str:
        return (
            f"{prompt}\n\n"
            f"Analyze the local image file at this absolute path: {image_path}\n"
            "You may read the file from the workspace if needed.\n\n"
            f"{STRUCTURED_MOOD_OUTPUT_INSTRUCTIONS}"
        )

    def read_output(self, result) -> str:
        stdout = result.stdout
        try:
            envelope = json.loads(stdout)
        except (json.JSONDecodeError, TypeError):
            return str(stdout)
        if isinstance(envelope, dict) and "result" in envelope:
            return str(envelope["result"])
        if isinstance(envelope, dict) and "response" in envelope:
            return str(envelope["response"])
        return str(stdout)

    def analyze_audio(self, audio_path: str, prompt: str) -> dict[str, object]:
        del audio_path, prompt
        raise ProviderExecutionError("Claude CLI provider audio analysis is not implemented yet.")

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
            self._claude_bin,
            "--model",
            self._model,
            "--output-format",
            "json",
            "-p",
            prompt,
        ]
        result = self._runner(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            message = result.stderr.strip() or result.stdout.strip() or self.default_error_message()
            raise ProviderExecutionError(f"{self.provider_label()} failed: {message}")
        output_text = self.read_output(result)
        return normalize_expression_payload(
            parse_json_text(output_text),
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
