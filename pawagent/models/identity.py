from __future__ import annotations

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    x_min: int = Field(ge=0)
    y_min: int = Field(ge=0)
    x_max: int = Field(ge=0)
    y_max: int = Field(ge=0)


class CroppedPetImage(BaseModel):
    source_path: str
    cropped_path: str
    crop_version: str = "identity_crop_v1"
    mask_applied: bool = False
    detected_species: str = "other"
    bbox: BoundingBox | None = None


class IdentityReference(BaseModel):
    source_path: str
    cropped_path: str
    embedding: list[float] = Field(default_factory=list)
    detected_species: str = "other"
    crop_version: str = "identity_crop_v1"
    embedding_version: str = "identity_embedding_v1"


class PetIdentityProfile(BaseModel):
    pet_id: str
    species_hint: str = "unknown"
    references: list[IdentityReference] = Field(default_factory=list)


class IdentityMatchResult(BaseModel):
    pet_id: str
    is_match: bool
    confidence: float = Field(ge=0.0, le=1.0)
    best_similarity: float = Field(ge=-1.0, le=1.0)
    compared_references: int = Field(ge=0)
    reason: str = ""
