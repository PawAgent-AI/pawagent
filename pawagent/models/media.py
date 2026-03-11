from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class ImageInput(BaseModel):
    path: Path
    mime_type: str = Field(default="image/jpeg")
