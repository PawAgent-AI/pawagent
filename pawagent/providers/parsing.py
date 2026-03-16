from __future__ import annotations

import json
from typing import Any

from pawagent.providers.errors import ProviderOutputParseError


def parse_json_text(output_text: str) -> dict[str, Any]:
    cleaned = output_text.strip()
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        return extract_embedded_json(cleaned)
    if "response" in payload and isinstance(payload["response"], str):
        return extract_embedded_json(payload["response"])
    return payload


def extract_embedded_json(text: str) -> dict[str, Any]:
    candidate = text.strip()
    if candidate.startswith("```"):
        candidate = candidate.removeprefix("```json").removeprefix("```").strip()
        if candidate.endswith("```"):
            candidate = candidate[:-3].strip()
    try:
        return json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise ProviderOutputParseError(f"Provider output was not valid JSON: {exc}") from exc


def normalize_mood_payload(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return {
            "mood": str(payload["mood"]),
            "confidence": float(payload["confidence"]),
            "tags": [str(tag) for tag in payload.get("tags", [])],
            "reason": str(payload.get("reason", "")),
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise ProviderOutputParseError(f"Provider output did not match expected mood schema: {exc}") from exc


def normalize_unified_payload(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        species = payload.get("species", {})
        emotion = payload["emotion"]
        behavior = payload["behavior"]
        motivation = payload["motivation"]
        expression = payload["expression"]
        evidence = payload.get("evidence", [])
        if not isinstance(species, dict) or not isinstance(emotion, dict) or not isinstance(behavior, dict) or not isinstance(motivation, dict) or not isinstance(expression, dict):
            raise TypeError("species, emotion, behavior, motivation, and expression must be objects")
        return {
            "species": {
                "requested_species": str(species.get("requested_species", "")),
                "observed_species": str(species.get("observed_species", "other")),
                "confidence": float(species.get("confidence", 0.0)),
                "used_framework": str(species.get("used_framework", species.get("observed_species", "other"))),
                "mismatch_warning": str(species.get("mismatch_warning", "")),
            },
            "emotion": {
                "label": str(emotion["label"]),
                "confidence": float(emotion["confidence"]),
                "arousal": str(emotion.get("arousal", "")),
                "tags": [str(tag) for tag in emotion.get("tags", [])],
                "alternatives": [str(item) for item in emotion.get("alternatives", [])],
                "evidence": [str(item) for item in emotion.get("evidence", payload.get("evidence", []))],
                "uncertainty_note": str(emotion.get("uncertainty_note", "")),
            },
            "behavior": {
                "label": str(behavior["label"]),
                "confidence": float(behavior["confidence"]),
                "target": str(behavior.get("target", "")),
                "intensity": str(behavior.get("intensity", "")),
                "evidence": [str(item) for item in behavior.get("evidence", payload.get("evidence", []))],
                "alternatives": [str(item) for item in behavior.get("alternatives", [])],
                "uncertainty_note": str(behavior.get("uncertainty_note", "")),
                "notes": str(behavior.get("notes", "")),
            },
            "motivation": {
                "label": str(motivation["label"]),
                "confidence": float(motivation["confidence"]),
                "alternatives": [str(item) for item in motivation.get("alternatives", [])],
                "evidence": [str(item) for item in motivation.get("evidence", payload.get("evidence", []))],
                "uncertainty_note": str(motivation.get("uncertainty_note", "")),
            },
            "expression": {
                "plain_text": str(expression.get("plain_text", expression.get("text", ""))),
                "pet_voice": str(expression.get("pet_voice", expression.get("text", ""))),
                "tone": str(expression.get("tone", "")),
                "grounded_in": [str(item) for item in expression.get("grounded_in", payload.get("evidence", []))],
                "confidence": float(expression["confidence"]),
            },
            "evidence": [str(item) for item in evidence],
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise ProviderOutputParseError(f"Provider output did not match expected unified schema: {exc}") from exc


def normalize_expression_payload(
    payload: dict[str, Any],
    *,
    default_grounding: list[str] | None = None,
    default_locale: str = "en",
    default_style: str = "default",
) -> dict[str, Any]:
    grounding = default_grounding or []
    try:
        return {
            "plain_text": str(payload.get("plain_text", payload.get("text", ""))),
            "pet_voice": str(payload.get("pet_voice", payload.get("text", ""))),
            "tone": str(payload.get("tone", "")),
            "grounded_in": [str(item) for item in payload.get("grounded_in", grounding)],
            "confidence": float(payload["confidence"]),
            "locale": str(payload.get("locale", default_locale)),
            "source_language": str(payload.get("source_language", "en")),
            "style": str(payload.get("style", default_style)),
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise ProviderOutputParseError(f"Provider output did not match expected expression schema: {exc}") from exc
