from __future__ import annotations

from pydantic import BaseModel, Field


class MoodResult(BaseModel):
    primary: str
    confidence: float = Field(ge=0.0, le=1.0)
    arousal: str = ""
    tags: list[str] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    uncertainty_note: str = ""
