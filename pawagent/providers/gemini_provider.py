from __future__ import annotations

import json
import logging
import mimetypes
import os
import time
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

_VIDEO_FILE_POLL_INTERVAL_SECONDS = 5
_VIDEO_FILE_MAX_POLLS = 60


class GeminiProvider(BaseProvider):
    def __init__(
        self,
        model: str = "gemini-2.5-flash",
        api_key: str | None = None,
        client: Any = None,
    ) -> None:
        self._model = model
        self._api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self._client = client

    def analyze_image(self, image: ImageInput, prompt: str) -> dict[str, object]:
        logger.debug("Gemini analyzing image: %s (model=%s)", image.path, self._model)
        client = self._get_client()
        image_part = self._build_image_part(image.path)
        try:
            response = client.models.generate_content(
                model=self._model,
                contents=[self._build_prompt(prompt), image_part],
                config={"response_mime_type": "application/json"},
            )
        except Exception as exc:
            raise ProviderExecutionError(f"Gemini request failed: {exc}") from exc
        output_text = getattr(response, "text", "")
        if not output_text:
            raise ProviderOutputParseError("Gemini response did not contain text output.")
        return self._parse_response(output_text)

    def analyze_video(self, video_path: str, prompt: str) -> dict[str, object]:
        path = Path(video_path)
        logger.debug("Gemini analyzing video: %s (model=%s)", path, self._model)
        client = self._get_client()
        try:
            uploaded = self._upload_video_file(client, path)
            video_file = self._wait_for_video_file(client, uploaded)
            response = client.models.generate_content(
                model=self._model,
                contents=[video_file, self._build_prompt(prompt)],
                config={"response_mime_type": "application/json"},
            )
        except ProviderExecutionError:
            raise
        except Exception as exc:
            raise ProviderExecutionError(f"Gemini video request failed: {exc}") from exc
        output_text = getattr(response, "text", "")
        if not output_text:
            raise ProviderOutputParseError("Gemini video response did not contain text output.")
        return self._parse_response(output_text)

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        if not self._api_key:
            raise ProviderAuthenticationError("GEMINI_API_KEY or GOOGLE_API_KEY is required for GeminiProvider.")

        from google import genai

        self._client = genai.Client(api_key=self._api_key)
        return self._client

    def _build_image_part(self, path: Path) -> object:
        image_bytes, mime_type = load_provider_image_bytes(path)

        try:
            from google.genai import types
        except ImportError:
            if self._client is not None and hasattr(self._client, "make_part_from_bytes"):
                return self._client.make_part_from_bytes(image_bytes, mime_type)
            raise

        return types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

    def _upload_video_file(self, client: Any, path: Path) -> Any:
        guessed_mime_type = mimetypes.guess_type(path.name)[0]
        if guessed_mime_type:
            try:
                return client.files.upload(file=path, config={"mime_type": guessed_mime_type})
            except TypeError:
                # Older SDK variants may not accept config for upload().
                return client.files.upload(file=path)
        return client.files.upload(file=path)

    def _wait_for_video_file(self, client: Any, uploaded: Any) -> Any:
        current = uploaded
        for _ in range(_VIDEO_FILE_MAX_POLLS):
            state_name = self._get_file_state_name(current)
            if state_name == "ACTIVE":
                return current
            if state_name in {"FAILED", "CANCELLED"}:
                raise ProviderExecutionError(f"Gemini video file processing ended in state {state_name}.")
            time.sleep(_VIDEO_FILE_POLL_INTERVAL_SECONDS)
            current = client.files.get(name=current.name)
        raise ProviderExecutionError("Gemini video file did not become ACTIVE before timeout.")

    def _get_file_state_name(self, file_obj: Any) -> str:
        state = getattr(file_obj, "state", None)
        if state is None:
            return ""
        if isinstance(state, str):
            return state.upper()
        name = getattr(state, "name", "")
        return str(name).upper()

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
            response = client.models.generate_content(
                model=self._model,
                contents=[self._build_expression_prompt(analysis=analysis, locale=locale, style=style)],
                config={"response_mime_type": "application/json"},
            )
        except Exception as exc:
            raise ProviderExecutionError(f"Gemini expression render failed: {exc}") from exc
        output_text = getattr(response, "text", "")
        if not output_text:
            raise ProviderOutputParseError("Gemini expression response did not contain text output.")
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
        raise ProviderExecutionError("GeminiProvider audio analysis is not implemented yet.")
