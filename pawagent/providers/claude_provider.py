from __future__ import annotations

import logging
import os
from base64 import b64encode
import json
from pathlib import Path

from pawagent.core.images import load_provider_image_bytes
from pawagent.models.analysis import UnifiedAnalysisResult
from pawagent.models.media import ImageInput
from pawagent.providers.base import BaseProvider
from pawagent.providers.errors import ProviderAuthenticationError, ProviderExecutionError, ProviderOutputParseError
from pawagent.providers.parsing import normalize_expression_payload, normalize_unified_payload, parse_json_text
from pawagent.vision.prompts import STRUCTURED_MOOD_OUTPUT_INSTRUCTIONS

logger = logging.getLogger(__name__)


class ClaudeProvider(BaseProvider):
    def __init__(
        self,
        model: str = "claude-sonnet-4-6",
        api_key: str | None = None,
        client: object | None = None,
    ) -> None:
        self._model = model
        self._api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self._client = client

    def analyze_image(self, image: ImageInput, prompt: str) -> dict[str, object]:
        logger.debug("Claude analyzing image: %s (model=%s)", image.path, self._model)
        client = self._get_client()
        image_data, media_type = self._encode_image(image.path)
        try:
            response = client.messages.create(
                model=self._model,
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_data,
                                },
                            },
                            {"type": "text", "text": self._build_prompt(prompt)},
                        ],
                    }
                ],
            )
        except Exception as exc:
            raise ProviderExecutionError(f"Claude request failed: {exc}") from exc
        output_text = self._extract_text(response)
        if not output_text:
            raise ProviderOutputParseError("Claude response did not contain text output.")
        return self._parse_response(output_text)

    def render_expression(
        self,
        analysis: UnifiedAnalysisResult,
        locale: str,
        style: str = "default",
    ) -> dict[str, object]:
        if locale.lower().startswith("en"):
            return analysis.expression.model_dump(mode="json")
        client = self._get_client()
        try:
            response = client.messages.create(
                model=self._model,
                max_tokens=2048,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": self._build_expression_prompt(analysis=analysis, locale=locale, style=style),
                            }
                        ],
                    }
                ],
            )
        except Exception as exc:
            raise ProviderExecutionError(f"Claude expression render failed: {exc}") from exc
        output_text = self._extract_text(response)
        if not output_text:
            raise ProviderOutputParseError("Claude expression response did not contain text output.")
        return normalize_expression_payload(
            parse_json_text(output_text),
            default_grounding=analysis.expression.grounded_in or analysis.evidence,
            default_locale=locale,
            default_style=style,
        )

    def analyze_audio(self, audio_path: str, prompt: str) -> dict[str, object]:
        del audio_path, prompt
        raise ProviderExecutionError("ClaudeProvider audio analysis is not implemented yet.")

    def analyze_video(self, video_path: str, prompt: str) -> dict[str, object]:
        del video_path, prompt
        raise ProviderExecutionError("ClaudeProvider video analysis is not implemented yet.")

    def _get_client(self) -> object:
        if self._client is not None:
            return self._client
        if not self._api_key:
            raise ProviderAuthenticationError("ANTHROPIC_API_KEY is required for ClaudeProvider.")

        import anthropic

        self._client = anthropic.Anthropic(api_key=self._api_key)
        return self._client

    def _encode_image(self, path: Path) -> tuple[str, str]:
        image_bytes, mime_type = load_provider_image_bytes(path)
        encoded = b64encode(image_bytes).decode("ascii")
        return encoded, mime_type

    def _build_prompt(self, prompt: str) -> str:
        return f"{prompt}\n\n{STRUCTURED_MOOD_OUTPUT_INSTRUCTIONS}"

    def _parse_response(self, output_text: str) -> dict[str, object]:
        return normalize_unified_payload(parse_json_text(output_text))

    def _extract_text(self, response: object) -> str:
        content = getattr(response, "content", [])
        for block in content:
            if getattr(block, "type", None) == "text":
                return getattr(block, "text", "")
        return ""

    def _build_expression_prompt(self, analysis: UnifiedAnalysisResult, locale: str, style: str) -> str:
        payload = json.dumps(analysis.model_dump(mode="json"), ensure_ascii=True)
        return (
            "Render the pet expression into the requested locale using only the provided structured analysis.\n"
            f"Target locale: {locale}\n"
            f"Style: {style}\n"
            "Return JSON only with this exact schema: "
            '{"plain_text":"string","pet_voice":"string","tone":"string","grounded_in":["string"],'
            '"confidence":0.0,"locale":"string","source_language":"string","style":"string"}\n'
            "Do not introduce facts beyond the structured analysis. Keep wording stable and natural.\n"
            f"Analysis JSON: {payload}"
        )
