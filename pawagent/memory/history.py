from __future__ import annotations

from pawagent.memory.store import AnalysisStore
from pawagent.models.analysis import AnalysisRecord


def get_recent_history(store: AnalysisStore, pet_id: str, limit: int = 5) -> list[AnalysisRecord]:
    return store.get_recent_analysis(pet_id=pet_id, limit=limit)
