from __future__ import annotations

from pawagent.models.analysis import AnalysisRecord
from pawagent.models.personality import PersonalityTrait
from pawagent.personality.traits import DEFAULT_TRAIT_NAMES


def derive_traits(records: list[AnalysisRecord]) -> list[PersonalityTrait]:
    if not records:
        return [PersonalityTrait(name=name, value=0.5) for name in DEFAULT_TRAIT_NAMES]

    playful_count = sum(1 for record in records if record.mood.primary == "playful")
    curious_count = sum(1 for record in records if record.mood.primary == "curious")
    relaxed_count = sum(1 for record in records if record.mood.primary == "relaxed")
    total = len(records)

    return [
        PersonalityTrait(name="energy_level", value=min(1.0, 0.4 + playful_count / total * 0.6)),
        PersonalityTrait(name="curiosity", value=min(1.0, 0.4 + curious_count / total * 0.6)),
        PersonalityTrait(name="playfulness", value=min(1.0, 0.4 + playful_count / total * 0.6)),
        PersonalityTrait(name="social_tendency", value=max(0.1, 0.7 - relaxed_count / total * 0.2)),
    ]
