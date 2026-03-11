from __future__ import annotations

from pydantic import BaseModel


class Pet(BaseModel):
    pet_id: str
    name: str
    species: str
