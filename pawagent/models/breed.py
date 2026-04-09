from __future__ import annotations

from pydantic import BaseModel, Field


class BreedAlternative(BaseModel):
    breed: str
    confidence: float = Field(ge=0.0, le=1.0)


class BreedResult(BaseModel):
    species: str
    breed: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    alternatives: list[BreedAlternative] = Field(default_factory=list)
    traits: list[str] = Field(default_factory=list)
