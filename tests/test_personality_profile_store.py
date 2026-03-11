from __future__ import annotations

from pathlib import Path

from pawagent.models.personality import PersonalityProfile, PersonalityTrait
from pawagent.personality.store import JsonPersonalityProfileStore


def test_json_personality_profile_store_persists_snapshot(tmp_path: Path) -> None:
    path = tmp_path / "personality_profiles.json"
    store = JsonPersonalityProfileStore(path)

    profile = PersonalityProfile(
        pet_id="pet-3",
        traits=[PersonalityTrait(name="energy_level", value=0.8)],
    )
    store.save_profile(profile, based_on_record_count=4)

    reloaded = JsonPersonalityProfileStore(path).get_snapshot("pet-3")

    assert reloaded is not None
    assert reloaded.profile.pet_id == "pet-3"
    assert reloaded.based_on_record_count == 4
