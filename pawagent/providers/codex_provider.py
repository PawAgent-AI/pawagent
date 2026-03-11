from __future__ import annotations

import json
import tempfile
from pathlib import Path

from pawagent.models.analysis import UnifiedAnalysisResult
from pawagent.models.media import ImageInput
from pawagent.providers.cli_base import CliAgentProvider
from pawagent.providers.errors import ProviderExecutionError
from pawagent.providers.parsing import normalize_expression_payload, parse_json_text
from pawagent.vision.prompts import CODEX_MOOD_OUTPUT_INSTRUCTIONS


class CodexProvider(CliAgentProvider):
    def __init__(
        self,
        model: str = "gpt-5.4",
        codex_bin: str = "codex",
        runner=None,
    ) -> None:
        super().__init__(runner=runner)
        self._model = model
        self._codex_bin = codex_bin
        self._output_path: Path | None = None

    def build_command(self, image: ImageInput, prompt: str) -> list[str]:
        tmp_path = Path(tempfile.mkdtemp(prefix="pawagent-codex-"))
        schema_path = tmp_path / "output_schema.json"
        self._output_path = tmp_path / "result.json"
        schema_path.write_text(json.dumps(self._output_schema(), indent=2), encoding="utf-8")

        return [
            self._codex_bin,
            "exec",
            "--model",
            self._model,
            "--color",
            "never",
            "--sandbox",
            "read-only",
            "--skip-git-repo-check",
            "--image",
            str(image.path),
            "--output-schema",
            str(schema_path),
            "--output-last-message",
            str(self._output_path),
            self._build_prompt(prompt),
        ]

    def read_output(self, result) -> str:
        del result
        if self._output_path is None or not self._output_path.exists():
            raise RuntimeError("Codex provider did not produce an output file.")
        return self._output_path.read_text(encoding="utf-8")

    def provider_label(self) -> str:
        return "Codex provider"

    def _build_prompt(self, prompt: str) -> str:
        return f"{prompt}\n\n{CODEX_MOOD_OUTPUT_INSTRUCTIONS}"

    def _output_schema(self) -> dict[str, object]:
        return {
            "type": "object",
            "additionalProperties": False,
            "required": ["emotion", "behavior", "motivation", "expression", "evidence"],
            "properties": {
                "emotion": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["label", "confidence"],
                    "properties": {
                        "label": {"type": "string"},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        "arousal": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "alternatives": {"type": "array", "items": {"type": "string"}},
                        "evidence": {"type": "array", "items": {"type": "string"}},
                        "uncertainty_note": {"type": "string"},
                    },
                },
                "behavior": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["label", "confidence"],
                    "properties": {
                        "label": {"type": "string"},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        "target": {"type": "string"},
                        "intensity": {"type": "string"},
                        "evidence": {"type": "array", "items": {"type": "string"}},
                        "alternatives": {"type": "array", "items": {"type": "string"}},
                        "uncertainty_note": {"type": "string"},
                        "notes": {"type": "string"},
                    },
                },
                "motivation": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["label", "confidence"],
                    "properties": {
                        "label": {"type": "string"},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        "alternatives": {"type": "array", "items": {"type": "string"}},
                        "evidence": {"type": "array", "items": {"type": "string"}},
                        "uncertainty_note": {"type": "string"},
                    },
                },
                "expression": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["plain_text", "pet_voice", "confidence"],
                    "properties": {
                        "plain_text": {"type": "string"},
                        "pet_voice": {"type": "string"},
                        "tone": {"type": "string"},
                        "grounded_in": {"type": "array", "items": {"type": "string"}},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    },
                },
                "evidence": {"type": "array", "items": {"type": "string"}},
            },
        }

    def analyze_audio(self, audio_path: str, prompt: str) -> dict[str, object]:
        del audio_path, prompt
        raise ProviderExecutionError("Codex provider audio analysis is not implemented yet.")

    def analyze_video(self, video_path: str, prompt: str) -> dict[str, object]:
        del video_path, prompt
        raise ProviderExecutionError("Codex provider video analysis is not implemented yet.")

    def render_expression(
        self,
        analysis: UnifiedAnalysisResult,
        locale: str,
        style: str = "default",
    ) -> dict[str, object]:
        if locale.lower().startswith("en"):
            return analysis.expression.model_dump(mode="json")

        tmp_path = Path(tempfile.mkdtemp(prefix="pawagent-codex-expression-"))
        schema_path = tmp_path / "expression_schema.json"
        output_path = tmp_path / "expression_result.json"
        schema_path.write_text(json.dumps(self._expression_schema(), indent=2), encoding="utf-8")
        command = [
            self._codex_bin,
            "exec",
            "--model",
            self._model,
            "--color",
            "never",
            "--sandbox",
            "read-only",
            "--skip-git-repo-check",
            "--output-schema",
            str(schema_path),
            "--output-last-message",
            str(output_path),
            self._build_expression_prompt(analysis=analysis, locale=locale, style=style),
        ]
        result = self._runner(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            message = result.stderr.strip() or result.stdout.strip() or self.default_error_message()
            raise ProviderExecutionError(f"{self.provider_label()} failed: {message}")
        if not output_path.exists():
            raise ProviderExecutionError("Codex provider did not produce an expression output file.")
        return normalize_expression_payload(
            parse_json_text(output_path.read_text(encoding="utf-8")),
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
            "Keep wording stable and natural. Do not introduce new facts.\n"
            f"Analysis JSON: {payload}"
        )

    def _expression_schema(self) -> dict[str, object]:
        return {
            "type": "object",
            "additionalProperties": False,
            "required": ["plain_text", "pet_voice", "confidence", "locale", "source_language", "style"],
            "properties": {
                "plain_text": {"type": "string"},
                "pet_voice": {"type": "string"},
                "tone": {"type": "string"},
                "grounded_in": {"type": "array", "items": {"type": "string"}},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "locale": {"type": "string"},
                "source_language": {"type": "string"},
                "style": {"type": "string"},
            },
        }
