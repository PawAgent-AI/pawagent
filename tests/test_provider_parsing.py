from __future__ import annotations

from pawagent.providers.errors import ProviderOutputParseError
from pawagent.providers.parsing import extract_embedded_json, normalize_unified_payload, parse_json_text


def test_parse_json_text_supports_response_wrapped_payload() -> None:
    payload = parse_json_text(
        '{"response":"```json\\n{\\"emotion\\":{\\"label\\":\\"playful\\",\\"confidence\\":0.91,\\"arousal\\":\\"high\\",\\"tags\\":[\\"engaged\\"],\\"alternatives\\":[\\"excited\\"],\\"evidence\\":[\\"loose posture\\"],\\"uncertainty_note\\":\\"\\"},\\"behavior\\":{\\"label\\":\\"seeking interaction\\",\\"confidence\\":0.82,\\"target\\":\\"human\\",\\"intensity\\":\\"high\\",\\"evidence\\":[\\"open posture\\"],\\"alternatives\\":[\\"playing\\"],\\"uncertainty_note\\":\\"\\" ,\\"notes\\":\\"Open posture\\"},\\"motivation\\":{\\"label\\":\\"seeking engagement\\",\\"confidence\\":0.77,\\"alternatives\\":[\\"wants play\\"],\\"evidence\\":[\\"open posture\\"],\\"uncertainty_note\\":\\"\\"},\\"expression\\":{\\"plain_text\\":\\"The pet appears playful and is actively seeking interaction.\\",\\"pet_voice\\":\\"I want to play.\\",\\"tone\\":\\"eager\\",\\"grounded_in\\":[\\"loose posture\\"],\\"confidence\\":0.72},\\"evidence\\":[\\"loose posture\\"]}\\n```"}'
    )

    assert payload["emotion"]["label"] == "playful"
    assert payload["behavior"]["label"] == "seeking interaction"


def test_extract_embedded_json_supports_markdown_fences() -> None:
    payload = extract_embedded_json(
        '```json\n{"emotion":{"label":"relaxed","confidence":0.88,"arousal":"low","tags":["calm"],"alternatives":["tired"],"evidence":["eyes half closed"],"uncertainty_note":"Relaxed and tired can overlap."},"behavior":{"label":"resting","confidence":0.85,"target":"self","intensity":"low","evidence":["settled posture"],"alternatives":["settling"],"uncertainty_note":"Static image limits duration certainty.","notes":"Settled posture"},"motivation":{"label":"wants rest","confidence":0.79,"alternatives":["wants low stimulation"],"evidence":["eyes half closed"],"uncertainty_note":"Single frame limits duration certainty."},"expression":{"plain_text":"The pet appears comfortable and is likely resting.","pet_voice":"I feel comfortable and want to rest.","tone":"calm","grounded_in":["eyes half closed"],"confidence":0.8},"evidence":["eyes half closed"]}\n```'
    )

    assert payload["emotion"]["label"] == "relaxed"


def test_normalize_unified_payload_coerces_output_shape() -> None:
    normalized = normalize_unified_payload(
        {
            "emotion": {
                "label": "alert",
                "confidence": "0.84",
                "arousal": "medium",
                "tags": ["focused"],
                "alternatives": ["curious"],
                "evidence": ["ears forward"],
                "uncertainty_note": "Could also be curiosity.",
            },
            "behavior": {
                "label": "monitoring surroundings",
                "confidence": "0.8",
                "target": "environment",
                "intensity": "moderate",
                "evidence": ["ears forward"],
                "alternatives": ["observing"],
                "uncertainty_note": "Short observation window.",
                "notes": "Ears forward",
            },
            "motivation": {
                "label": "monitoring for change",
                "confidence": "0.61",
                "alternatives": ["checking environment"],
                "evidence": ["ears forward"],
                "uncertainty_note": "Trigger not visible.",
            },
            "expression": {
                "plain_text": "The pet appears alert and is monitoring the surroundings.",
                "pet_voice": "I am watching everything carefully right now.",
                "tone": "watchful",
                "grounded_in": ["ears forward"],
                "confidence": "0.74",
            },
            "evidence": ["ears forward"],
        }
    )

    assert normalized == {
        "species": {
            "requested_species": "",
            "observed_species": "other",
            "confidence": 0.0,
            "used_framework": "other",
            "mismatch_warning": "",
        },
        "emotion": {
            "label": "alert",
            "confidence": 0.84,
            "arousal": "medium",
            "tags": ["focused"],
            "alternatives": ["curious"],
            "evidence": ["ears forward"],
            "uncertainty_note": "Could also be curiosity.",
        },
        "behavior": {
            "label": "monitoring surroundings",
            "confidence": 0.8,
            "target": "environment",
            "intensity": "moderate",
            "evidence": ["ears forward"],
            "alternatives": ["observing"],
            "uncertainty_note": "Short observation window.",
            "notes": "Ears forward",
        },
        "motivation": {
            "label": "monitoring for change",
            "confidence": 0.61,
            "alternatives": ["checking environment"],
            "evidence": ["ears forward"],
            "uncertainty_note": "Trigger not visible.",
        },
        "expression": {
            "plain_text": "The pet appears alert and is monitoring the surroundings.",
            "pet_voice": "I am watching everything carefully right now.",
            "tone": "watchful",
            "grounded_in": ["ears forward"],
            "confidence": 0.74,
        },
        "evidence": ["ears forward"],
    }


def test_extract_embedded_json_raises_provider_parse_error_for_invalid_json() -> None:
    try:
        extract_embedded_json("not-json")
    except ProviderOutputParseError as exc:
        assert "valid JSON" in str(exc)
    else:
        raise AssertionError("Expected ProviderOutputParseError")
