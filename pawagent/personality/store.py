from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from pawagent.models.personality import PersonalityProfile, PersonalityProfileSnapshot


class PersonalityProfileStore(Protocol):
    def get_snapshot(self, pet_id: str) -> PersonalityProfileSnapshot | None: ...

    def save_profile(self, profile: PersonalityProfile, based_on_record_count: int) -> PersonalityProfileSnapshot: ...


class InMemoryPersonalityProfileStore:
    def __init__(self) -> None:
        self._snapshots: dict[str, PersonalityProfileSnapshot] = {}

    def get_snapshot(self, pet_id: str) -> PersonalityProfileSnapshot | None:
        return self._snapshots.get(pet_id)

    def save_profile(self, profile: PersonalityProfile, based_on_record_count: int) -> PersonalityProfileSnapshot:
        snapshot = PersonalityProfileSnapshot(
            profile=profile,
            based_on_record_count=based_on_record_count,
            updated_at=datetime.now(UTC).isoformat(),
        )
        self._snapshots[profile.pet_id] = snapshot
        return snapshot


class JsonPersonalityProfileStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._write_snapshots({})

    def get_snapshot(self, pet_id: str) -> PersonalityProfileSnapshot | None:
        return self._read_snapshots().get(pet_id)

    def save_profile(self, profile: PersonalityProfile, based_on_record_count: int) -> PersonalityProfileSnapshot:
        snapshots = self._read_snapshots()
        snapshot = PersonalityProfileSnapshot(
            profile=profile,
            based_on_record_count=based_on_record_count,
            updated_at=datetime.now(UTC).isoformat(),
        )
        snapshots[profile.pet_id] = snapshot
        self._write_snapshots(snapshots)
        return snapshot

    def _read_snapshots(self) -> dict[str, PersonalityProfileSnapshot]:
        if not self._path.exists():
            return {}
        payload = json.loads(self._path.read_text(encoding="utf-8"))
        return {
            pet_id: PersonalityProfileSnapshot.model_validate(snapshot)
            for pet_id, snapshot in payload.items()
        }

    def _write_snapshots(self, snapshots: dict[str, PersonalityProfileSnapshot]) -> None:
        payload = {
            pet_id: snapshot.model_dump(mode="json")
            for pet_id, snapshot in snapshots.items()
        }
        self._path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
