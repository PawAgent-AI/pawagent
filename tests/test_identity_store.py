from __future__ import annotations

from pathlib import Path

from pawagent.identity.store import InMemoryIdentityProfileStore, JsonIdentityProfileStore
from pawagent.models.identity import IdentityReference


def test_in_memory_identity_profile_store_adds_references() -> None:
    store = InMemoryIdentityProfileStore()
    profile = store.add_reference(
        pet_id="pet-identity-1",
        species_hint="dog",
        reference=IdentityReference(
            source_path="dog-1.jpg",
            cropped_path="dog-1-crop.png",
            embedding=[0.1, 0.2, 0.3],
            detected_species="dog",
        ),
    )

    assert profile.pet_id == "pet-identity-1"
    assert profile.species_hint == "dog"
    assert len(profile.references) == 1


def test_json_identity_profile_store_persists_profiles(tmp_path: Path) -> None:
    path = tmp_path / "identity_profiles.json"
    store = JsonIdentityProfileStore(path)
    store.add_reference(
        pet_id="pet-identity-2",
        species_hint="cat",
        reference=IdentityReference(
            source_path="cat-1.jpg",
            cropped_path="cat-1-crop.png",
            embedding=[0.2, 0.3, 0.4],
            detected_species="cat",
        ),
    )

    reloaded = JsonIdentityProfileStore(path).get_profile("pet-identity-2")

    assert reloaded is not None
    assert reloaded.species_hint == "cat"
    assert len(reloaded.references) == 1


def test_json_identity_profile_store_appends_multiple_references(tmp_path: Path) -> None:
    path = tmp_path / "identity_profiles.json"
    store = JsonIdentityProfileStore(path)
    store.add_reference(
        pet_id="pet-identity-3",
        species_hint="cat",
        reference=IdentityReference(
            source_path="cat-1.jpg",
            cropped_path="cat-1-crop.png",
            embedding=[0.2, 0.3, 0.4],
            detected_species="cat",
        ),
    )
    store.add_reference(
        pet_id="pet-identity-3",
        species_hint="cat",
        reference=IdentityReference(
            source_path="cat-2.jpg",
            cropped_path="cat-2-crop.png",
            embedding=[0.25, 0.35, 0.45],
            detected_species="cat",
        ),
    )

    reloaded = JsonIdentityProfileStore(path).get_profile("pet-identity-3")

    assert reloaded is not None
    assert len(reloaded.references) == 2
    assert reloaded.references[0].source_path == "cat-1.jpg"
    assert reloaded.references[1].source_path == "cat-2.jpg"
