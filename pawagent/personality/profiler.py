from __future__ import annotations

from pawagent.memory.store import AnalysisStore
from pawagent.models.personality import PersonalityProfile
from pawagent.personality.store import PersonalityProfileStore
from pawagent.personality.updater import derive_traits


class PersonalityProfiler:
    def __init__(
        self,
        memory_store: AnalysisStore,
        profile_store: PersonalityProfileStore | None = None,
    ) -> None:
        self._memory_store = memory_store
        self._profile_store = profile_store

    def get_profile(self, pet_id: str) -> PersonalityProfile:
        record_count = self._memory_store.count_records(pet_id=pet_id)
        if self._profile_store is not None:
            snapshot = self._profile_store.get_snapshot(pet_id)
            if snapshot is not None and snapshot.based_on_record_count == record_count:
                return snapshot.profile

        return self.refresh_profile(pet_id)

    def refresh_profile(self, pet_id: str) -> PersonalityProfile:
        records = self._memory_store.get_recent_analysis(pet_id=pet_id, limit=20)
        profile = PersonalityProfile(pet_id=pet_id, traits=derive_traits(records))
        if self._profile_store is not None:
            self._profile_store.save_profile(
                profile=profile,
                based_on_record_count=self._memory_store.count_records(pet_id=pet_id),
            )
        return profile
