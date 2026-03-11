from __future__ import annotations

from pawagent.models.mood import MoodResult
from pawagent.models.personality import PersonalityProfile
from pawagent.models.pet import Pet


def summarize_analysis(pet: Pet, mood: MoodResult, profile: PersonalityProfile, context: str) -> str:
    prominent_traits = ", ".join(
        f"{trait.name}={trait.value:.2f}" for trait in profile.traits[:2]
    ) or "no established traits"
    return (
        f"{pet.name} appears {mood.primary} ({mood.confidence:.2f}). "
        f"Context: {context}. Personality: {prominent_traits}."
    )
