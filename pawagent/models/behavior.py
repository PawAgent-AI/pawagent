from __future__ import annotations

from pydantic import BaseModel, Field


class BehaviorResult(BaseModel):
    label: str
    confidence: float = Field(ge=0.0, le=1.0)
    target: str = ""
    intensity: str = ""
    evidence: list[str] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)
    uncertainty_note: str = ""
    notes: str = ""
