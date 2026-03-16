from __future__ import annotations

import logging
import os
from base64 import b64encode
import json
from pathlib import Path
from typing import Any

from pawagent.core.images import load_provider_image_bytes
from pawagent.models.analysis import UnifiedAnalysisResult
from pawagent.models.media import ImageInput
from pawagent.providers.base import BaseProvider
from pawagent.providers.errors import ProviderAuthenticationError, ProviderExecutionError, ProviderOutputParseError
from pawagent.providers.parsing import normalize_expression_payload, normalize_unified_payload, parse_json_text
from pawagent.vision.prompts import STRUCTURED_MOOD_OUTPUT_INSTRUCTIONS

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseProvider):
    def __init__(
        self,
        model: str = "gpt-4.1-mini",
        api_key: str | None = None,
        client: Any = None,
    ) -> None:
        self._model = model
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._client = client

    def analyze_image(self, image: ImageInput, prompt: str) -> dict[str, object]:
        logger.debug("OpenAI analyzing image: %s (model=%s)", image.path, self._model)
        client = self._get_client()
        input_image = self._build_input_image(image.path)
        try:
            response = client.responses.create(
                model=self._model,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": self._build_prompt(prompt)},
                            input_image,
                        ],
                    }
                ],
            )
        except Exception as exc:
            raise ProviderExecutionError(f"OpenAI request failed: {exc}") from exc
        output_text = getattr(response, "output_text", "")
        if not output_text:
            raise ProviderOutputParseError("OpenAI response did not contain output_text.")
        return self._parse_response(output_text)

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        if not self._api_key:
            raise ProviderAuthenticationError("OPENAI_API_KEY is required for OpenAIProvider.")

        from openai import OpenAI

        self._client = OpenAI(api_key=self._api_key)
        return self._client

    def _build_input_image(self, path: Path) -> dict[str, str]:
        image_bytes, mime_type = load_provider_image_bytes(path)
        encoded = b64encode(image_bytes).decode("ascii")
        return {
            "type": "input_image",
            "image_url": f"data:{mime_type};base64,{encoded}",
        }

    def _build_prompt(self, prompt: str) -> str:
        return f"{prompt}\n\n{STRUCTURED_MOOD_OUTPUT_INSTRUCTIONS}"

    def _parse_response(self, output_text: str) -> dict[str, object]:
        return normalize_unified_payload(parse_json_text(output_text))

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
            response = client.responses.create(
                model=self._model,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": self._build_expression_prompt(analysis=analysis, locale=locale, style=style),
                            }
                        ],
                    }
                ],
            )
        except Exception as exc:
            raise ProviderExecutionError(f"OpenAI expression render failed: {exc}") from exc
        output_text = getattr(response, "output_text", "")
        if not output_text:
            raise ProviderOutputParseError("OpenAI expression response did not contain output_text.")
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
            "Do not introduce facts beyond the structured analysis. Keep wording stable and natural.\n"
            f"Analysis JSON: {payload}"
        )

    def analyze_audio(self, audio_path: str, prompt: str) -> dict[str, object]:
        del audio_path, prompt
        raise ProviderExecutionError("OpenAIProvider audio analysis is not implemented yet.")

    def analyze_video(self, video_path: str, prompt: str) -> dict[str, object]:
        del video_path, prompt
        raise ProviderExecutionError("OpenAIProvider video analysis is not implemented yet.")
