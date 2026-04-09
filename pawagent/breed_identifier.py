from __future__ import annotations

import logging
from pathlib import Path

from pawagent.models.breed import BreedAlternative, BreedResult
from pawagent.providers.base import BaseProvider
from pawagent.vision.preprocess import prepare_image
from pawagent.vision.prompts import BREED_IDENTIFICATION_PROMPT

logger = logging.getLogger(__name__)


class BreedIdentifier:
    def __init__(self, provider: BaseProvider) -> None:
        self._provider = provider

    def identify(self, image_path: Path) -> BreedResult:
        logger.debug("BreedIdentifier processing image: %s", image_path)
        image = prepare_image(image_path)
        raw = self._provider.analyze_image(image=image, prompt=BREED_IDENTIFICATION_PROMPT)
        alternatives = [
            BreedAlternative(breed=str(a["breed"]), confidence=float(a["confidence"]))
            for a in raw.get("alternatives", [])
            if a.get("breed") is not None
        ]
        raw_breed = raw.get("breed")
        return BreedResult(
            species=str(raw["species"]),
            breed=str(raw_breed) if raw_breed else None,
            confidence=float(raw["confidence"]),
            alternatives=alternatives,
            traits=[str(t) for t in raw.get("traits", [])],
        )
