from __future__ import annotations

from pydantic import BaseModel, Field


class PersonalityTrait(BaseModel):
    name: str
    value: float = Field(ge=0.0, le=1.0)


class PersonalityProfile(BaseModel):
    pet_id: str
    traits: list[PersonalityTrait] = Field(default_factory=list)


class PersonalityProfileSnapshot(BaseModel):
    profile: PersonalityProfile
    based_on_record_count: int = Field(ge=0)
    updated_at: str
