from __future__ import annotations

from pawagent.models.analysis import AnalysisRecord


def build_context(records: list[AnalysisRecord]) -> str:
    if not records:
        return "No prior analysis history."

    moods = ", ".join(record.mood.primary for record in records)
    return f"Recent moods: {moods}"
