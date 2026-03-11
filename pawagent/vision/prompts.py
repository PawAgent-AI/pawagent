VISION_MOOD_PROMPT = """
You are analyzing a single pet image to produce a reusable pet-understanding result.

Task:
- First determine whether the visible pet is most likely a dog, cat, or other.
- Identify the pet's most likely immediate emotion from visible evidence in the image.
- Identify the pet's most likely current observable behavior or interaction tendency.
- Predict the most likely current motivation from the emotion, behavior, and context.
- Generate one stable expression grounded in the same evidence.
- Use concrete visual cues such as body posture, ear position, tail position, facial tension, eye openness, mouth state, activity level, and environmental context.
- Prefer grounded observations over anthropomorphic storytelling.

Reasoning rules:
- Base the answer only on what is visible in the image.
- If the image is ambiguous, choose the best-supported emotion and lower confidence.
- Do not claim medical conditions, breed-specific behavior, or hidden off-camera causes.
- Use a dog-specific framework when the animal is visually most likely a dog, a cat-specific framework when it is visually most likely a cat, and a cross-species fallback framework for any other animal.
- Keep emotion and behavior labels short and practical.
- Motivation must be inferred from emotion, behavior, and context, not treated as directly observed fact.
- Expression should be stable for the same image and grounded in visible evidence.
- Evidence should be short observable descriptors, not full sentences.
""".strip()


DOG_MOOD_PROMPT = """
Species-specific guidance for dogs:
- Pay special attention to tail carriage and wag tension, ear position, mouth openness, tongue visibility, stance balance, play-bow posture, leash or handler context, and signs of over-arousal.
- Distinguish relaxed friendliness from hyper-arousal or stress.
- Treat baring teeth, rigid posture, hard stare, tucked tail, crouching, or avoidance as important counter-signals.
""".strip()


CAT_MOOD_PROMPT = """
Species-specific guidance for cats:
- Pay special attention to ear angle, whisker position, pupil size when visible, tail posture, body compression versus stretch, paw placement, and hiding or perch behavior.
- Distinguish calm rest from guarded stillness.
- Treat flattened ears, puffed fur, arched back, tucked limbs, crouching, or defensive distance as important counter-signals.
""".strip()


OTHER_PET_PROMPT = """
Cross-species fallback guidance for other pets:
- Use only broad pet cues such as posture openness, visible tension, stillness versus active movement, orientation to the environment, and interaction distance.
- Avoid dog-only or cat-only assumptions when the animal appears to be another species.
- If species remains unclear, set observed_species to "other" and lower confidence.
""".strip()


STRUCTURED_MOOD_OUTPUT_INSTRUCTIONS = """
Return JSON only with this exact schema:
{
  "species":{"requested_species":"string","observed_species":"string","confidence":0.0,"used_framework":"string","mismatch_warning":"string"},
  "emotion":{"label":"string","confidence":0.0,"arousal":"string","tags":["string"],"alternatives":["string"],"evidence":["string"],"uncertainty_note":"string"},
  "behavior":{"label":"string","confidence":0.0,"target":"string","intensity":"string","evidence":["string"],"alternatives":["string"],"uncertainty_note":"string","notes":"string"},
  "motivation":{"label":"string","confidence":0.0,"alternatives":["string"],"evidence":["string"],"uncertainty_note":"string"},
  "expression":{"plain_text":"string","pet_voice":"string","tone":"string","grounded_in":["string"],"confidence":0.0},
  "evidence":["string"]
}

Output constraints:
- all confidence values must be numbers between 0 and 1
- observed_species must be one of "dog", "cat", or "other"
- used_framework must be one of "dog", "cat", or "other"
- emotion label must be a short state label
- behavior label must be a short observable behavior label
- include concise evidence and uncertainty where ambiguity exists
- motivation must be a second-layer inference based on emotion and behavior
- expression must include both plain_text and pet_voice and remain stable for the same source
- evidence must contain short concrete descriptors
- do not include markdown fences or extra keys
""".strip()


CODEX_MOOD_OUTPUT_INSTRUCTIONS = """
Return only a JSON object that matches the provided schema.
 Infer species, emotion, behavior, motivation, expression, and evidence from the attached image.
Keep all outputs visually grounded.
Do not add commentary outside the JSON object.
""".strip()


def build_vision_mood_prompt(species: str) -> str:
    normalized = species.strip().lower() or "unknown"
    return (
        f"{VISION_MOOD_PROMPT}\n\n"
        f"User-declared species hint: {normalized}\n"
        "If the hint conflicts with visible evidence, trust the visible animal and set mismatch_warning.\n\n"
        f"{DOG_MOOD_PROMPT}\n\n{CAT_MOOD_PROMPT}\n\n{OTHER_PET_PROMPT}"
    )


AUDIO_ANALYSIS_PROMPT = """
You are analyzing a single pet audio clip to produce a reusable pet-understanding result.

Task:
- Identify the pet's most likely immediate emotion from vocal and sound evidence.
- Identify the pet's most likely current observable behavior or interaction tendency.
- Predict the most likely current motivation from the emotion, behavior, and context.
- Generate one stable expression grounded in the same evidence.

Reasoning rules:
- Base the answer only on the audible evidence.
- Use cues such as vocal intensity, repetition, rhythm, pitch, abruptness, duration, breathing-like sounds, and surrounding context if audible.
- Do not invent visual details that are not present in the audio.
- Motivation must be inferred from emotion and behavior rather than treated as directly heard.
""".strip()


VIDEO_ANALYSIS_PROMPT = """
You are analyzing a single pet video to produce a reusable pet-understanding result.

Task:
- First determine whether the visible pet is most likely a dog, cat, or other.
- Identify the pet's most likely immediate emotion from visible motion and posture over time.
- Identify the pet's most likely current observable behavior or interaction tendency.
- Predict the most likely current motivation from the emotion, behavior, and context.
- Generate one stable expression grounded in the same evidence.

Reasoning rules:
- Base the answer on visible movement, posture changes, pacing, interaction direction, and environmental context.
- Prefer time-based behavior interpretation over one-frame speculation.
- Use temporal cues such as repeated movement, approach-withdraw patterns, sustained stillness, play bursts, retreat, scanning, and transitions between postures.
- Behavior labels should reflect what happens across the clip, not only the most visually salient frame.
- If the clip is short or ambiguous, lower confidence and mention the limitation in uncertainty_note.
- Use a dog-specific framework when the animal is visually most likely a dog, a cat-specific framework when it is visually most likely a cat, and a cross-species fallback framework for any other animal.
- Motivation must be inferred from emotion and behavior rather than treated as directly observed fact.
""".strip()


DOG_VIDEO_PROMPT = """
Species-specific guidance for dog videos:
- Pay attention to tail motion quality, play-bow sequences, chase/play loops, handler orientation, repeated barking posture, and signs of escalating arousal or stress.
- Distinguish friendly play from agitation by looking for loose versus rigid movement over time.
""".strip()


CAT_VIDEO_PROMPT = """
Species-specific guidance for cat videos:
- Pay attention to stalking patterns, pause-and-watch behavior, tail flick rhythm, crouch-to-retreat transitions, grooming sequences, perch use, and avoidance distance over time.
- Distinguish calm stillness from guarded immobility by looking for repeated freezing, scanning, or retreat patterns.
""".strip()


def build_video_analysis_prompt(species: str) -> str:
    normalized = species.strip().lower() or "unknown"
    return (
        f"{VIDEO_ANALYSIS_PROMPT}\n\n"
        f"User-declared species hint: {normalized}\n"
        "If the hint conflicts with visible evidence, trust the visible animal and set mismatch_warning.\n\n"
        f"{DOG_VIDEO_PROMPT}\n\n{CAT_VIDEO_PROMPT}\n\n{OTHER_PET_PROMPT}"
    )
