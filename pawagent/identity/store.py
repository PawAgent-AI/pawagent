from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from pawagent.models.identity import IdentityReference, PetIdentityProfile


class IdentityProfileStore(Protocol):
    def get_profile(self, pet_id: str) -> PetIdentityProfile | None: ...

    def save_profile(self, profile: PetIdentityProfile) -> PetIdentityProfile: ...

    def add_reference(self, pet_id: str, reference: IdentityReference, species_hint: str = "unknown") -> PetIdentityProfile: ...


class InMemoryIdentityProfileStore:
    def __init__(self) -> None:
        self._profiles: dict[str, PetIdentityProfile] = {}

    def get_profile(self, pet_id: str) -> PetIdentityProfile | None:
        return self._profiles.get(pet_id)

    def save_profile(self, profile: PetIdentityProfile) -> PetIdentityProfile:
        self._profiles[profile.pet_id] = profile
        return profile

    def add_reference(self, pet_id: str, reference: IdentityReference, species_hint: str = "unknown") -> PetIdentityProfile:
        profile = self._profiles.get(pet_id) or PetIdentityProfile(pet_id=pet_id, species_hint=species_hint)
        profile.references.append(reference)
        if species_hint != "unknown":
            profile.species_hint = species_hint
        self._profiles[pet_id] = profile
        return profile


class JsonIdentityProfileStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._write_profiles({})

    def get_profile(self, pet_id: str) -> PetIdentityProfile | None:
        return self._read_profiles().get(pet_id)

    def save_profile(self, profile: PetIdentityProfile) -> PetIdentityProfile:
        profiles = self._read_profiles()
        profiles[profile.pet_id] = profile
        self._write_profiles(profiles)
        return profile

    def add_reference(self, pet_id: str, reference: IdentityReference, species_hint: str = "unknown") -> PetIdentityProfile:
        profiles = self._read_profiles()
        profile = profiles.get(pet_id) or PetIdentityProfile(pet_id=pet_id, species_hint=species_hint)
        profile.references.append(reference)
        if species_hint != "unknown":
            profile.species_hint = species_hint
        profiles[pet_id] = profile
        self._write_profiles(profiles)
        return profile

    def _read_profiles(self) -> dict[str, PetIdentityProfile]:
        if not self._path.exists():
            return {}
        payload = json.loads(self._path.read_text(encoding="utf-8"))
        return {pet_id: PetIdentityProfile.model_validate(item) for pet_id, item in payload.items()}

    def _write_profiles(self, profiles: dict[str, PetIdentityProfile]) -> None:
        payload = {pet_id: profile.model_dump(mode="json") for pet_id, profile in profiles.items()}
        self._path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
