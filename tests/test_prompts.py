from __future__ import annotations

from pawagent.vision.prompts import (
    CAT_MOOD_PROMPT,
    CODEX_MOOD_OUTPUT_INSTRUCTIONS,
    CAT_VIDEO_PROMPT,
    DOG_MOOD_PROMPT,
    DOG_VIDEO_PROMPT,
    OTHER_PET_PROMPT,
    STRUCTURED_MOOD_OUTPUT_INSTRUCTIONS,
    VIDEO_ANALYSIS_PROMPT,
    VISION_MOOD_PROMPT,
    build_video_analysis_prompt,
    build_vision_mood_prompt,
)


def test_vision_prompt_emphasizes_visual_evidence_and_uncertainty() -> None:
    assert "Base the answer only on what is visible in the image." in VISION_MOOD_PROMPT
    assert "If the image is ambiguous" in VISION_MOOD_PROMPT
    assert "Prefer grounded observations over anthropomorphic storytelling." in VISION_MOOD_PROMPT


def test_output_instructions_enforce_structured_json() -> None:
    assert "Return JSON only" in STRUCTURED_MOOD_OUTPUT_INSTRUCTIONS
    assert '"species":{"requested_species":"string","observed_species":"string","confidence":0.0,"used_framework":"string","mismatch_warning":"string"}' in STRUCTURED_MOOD_OUTPUT_INSTRUCTIONS
    assert '"expression":{"plain_text":"string","pet_voice":"string","tone":"string","grounded_in":["string"],"confidence":0.0}' in STRUCTURED_MOOD_OUTPUT_INSTRUCTIONS
    assert "Do not add commentary outside the JSON object." in CODEX_MOOD_OUTPUT_INSTRUCTIONS


def test_species_specific_prompt_selection() -> None:
    dog_prompt = build_vision_mood_prompt("dog")
    cat_prompt = build_vision_mood_prompt("cat")
    other_prompt = build_vision_mood_prompt("rabbit")

    assert DOG_MOOD_PROMPT in dog_prompt
    assert CAT_MOOD_PROMPT in cat_prompt
    assert OTHER_PET_PROMPT in other_prompt
    assert "User-declared species hint: rabbit" in other_prompt


def test_video_prompt_selection() -> None:
    dog_prompt = build_video_analysis_prompt("dog")
    cat_prompt = build_video_analysis_prompt("cat")
    other_prompt = build_video_analysis_prompt("rabbit")

    assert DOG_VIDEO_PROMPT in dog_prompt
    assert CAT_VIDEO_PROMPT in cat_prompt
    assert OTHER_PET_PROMPT in other_prompt
    assert "User-declared species hint: rabbit" in other_prompt
