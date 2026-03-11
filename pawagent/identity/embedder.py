from __future__ import annotations

import hashlib
from math import sqrt
from pathlib import Path
from typing import Protocol

from pawagent.core.images import open_image
from pawagent.models.identity import CroppedPetImage


class IdentityEmbedder(Protocol):
    @property
    def embedding_version(self) -> str: ...

    def embed_image(self, cropped_image: CroppedPetImage) -> list[float]: ...


class HashIdentityEmbedder:
    @property
    def embedding_version(self) -> str:
        return "hash_embedder_v1"

    def embed_image(self, cropped_image: CroppedPetImage) -> list[float]:
        path = Path(cropped_image.cropped_path)
        hasher = hashlib.sha256()
        if path.exists():
            hasher.update(path.read_bytes())
        else:
            hasher.update(str(path).encode("utf-8"))
        digest = hasher.digest()
        values: list[float] = []
        for index in range(0, 32, 4):
            chunk = digest[index : index + 4]
            number = int.from_bytes(chunk, byteorder="big", signed=False)
            values.append(number / 4294967295.0)
        return values


class OpenClipIdentityEmbedder:
    def __init__(
        self,
        *,
        model_name: str = "ViT-B-32",
        pretrained: str = "laion2b_s34b_b79k",
        device: str = "cpu",
    ) -> None:
        self._model_name = model_name
        self._pretrained = pretrained
        self._device = device
        self._model = None
        self._preprocess = None

    @property
    def embedding_version(self) -> str:
        return f"openclip_{self._model_name}_{self._pretrained}".replace("/", "_")

    def embed_image(self, cropped_image: CroppedPetImage) -> list[float]:
        model, preprocess = self._get_model()
        try:
            import torch
        except ImportError as exc:
            raise RuntimeError(
                "OpenClipIdentityEmbedder requires the optional identity dependencies: pillow, torch, open-clip-torch."
            ) from exc

        image = open_image(Path(cropped_image.cropped_path)).convert("RGB")
        image_tensor = preprocess(image).unsqueeze(0).to(self._device)
        with torch.no_grad():
            features = model.encode_image(image_tensor)
            features = features / features.norm(dim=-1, keepdim=True)
        return [float(value) for value in features[0].detach().cpu().tolist()]

    def _get_model(self):
        if self._model is not None and self._preprocess is not None:
            return self._model, self._preprocess
        try:
            import open_clip
        except ImportError as exc:
            raise RuntimeError(
                "OpenClipIdentityEmbedder requires the optional identity dependency: open-clip-torch."
            ) from exc

        model, _, preprocess = open_clip.create_model_and_transforms(
            self._model_name,
            pretrained=self._pretrained,
            device=self._device,
        )
        model.eval()
        self._model = model
        self._preprocess = preprocess
        return model, preprocess


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    left_norm = sqrt(sum(value * value for value in left))
    right_norm = sqrt(sum(value * value for value in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    return dot / (left_norm * right_norm)
