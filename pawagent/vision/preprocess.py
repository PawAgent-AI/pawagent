from __future__ import annotations

from pathlib import Path

from pawagent.models.media import ImageInput


def prepare_image(path: Path) -> ImageInput:
    return ImageInput(path=path)
