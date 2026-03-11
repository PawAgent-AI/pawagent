from __future__ import annotations

from pathlib import Path

from pawagent.memory.store import JsonAnalysisStore
from pawagent.models.analysis import AnalysisRecord, ExpressionResult, MotivationResult, UnifiedAnalysisResult
from pawagent.models.behavior import BehaviorResult
from pawagent.models.mood import MoodResult


def test_json_analysis_store_persists_records(tmp_path: Path) -> None:
    store_path = tmp_path / "analysis_records.json"

    first_store = JsonAnalysisStore(store_path)
    first_store.add_record(
        AnalysisRecord(
            pet_id="pet-7",
            content_hash="hash-cat-window",
            source_path="cat-window.jpg",
            analysis=UnifiedAnalysisResult(
                emotion=MoodResult(primary="curious", confidence=0.76, tags=["observant"]),
                behavior=BehaviorResult(label="observing", confidence=0.72, notes="Watching the scene."),
                motivation=MotivationResult(
                    label="understanding the environment",
                    confidence=0.68,
                    alternatives=["checking novelty"],
                    evidence=["steady gaze"],
                    uncertainty_note="Single image limits the next-step prediction.",
                ),
                expression=ExpressionResult(
                    plain_text="The pet appears curious and is observing the environment.",
                    pet_voice="I am figuring out what is happening here.",
                    tone="curious",
                    grounded_in=["steady gaze"],
                    confidence=0.69,
                ),
                evidence=["steady gaze"],
            ),
            metadata={"image_path": "cat-window.jpg"},
        )
    )

    second_store = JsonAnalysisStore(store_path)
    records = second_store.get_recent_analysis("pet-7")

    assert len(records) == 1
    assert records[0].mood.primary == "curious"
    assert records[0].analysis.motivation.label == "understanding the environment"
    assert records[0].analysis.expression.pet_voice == "I am figuring out what is happening here."
    assert records[0].metadata["image_path"] == "cat-window.jpg"
    assert second_store.get_cached_analysis("hash-cat-window", "unified_image_v1") is not None
