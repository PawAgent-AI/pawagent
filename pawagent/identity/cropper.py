from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Protocol

from pawagent.core.images import open_image
from pawagent.models.identity import BoundingBox, CroppedPetImage


class PetCropper(Protocol):
    def crop_pet(self, image_path: Path, species_hint: str = "unknown") -> CroppedPetImage: ...


class NoOpPetCropper:
    def crop_pet(self, image_path: Path, species_hint: str = "unknown") -> CroppedPetImage:
        return CroppedPetImage(
            source_path=str(image_path),
            cropped_path=str(image_path),
            crop_version="identity_crop_noop_v1",
            mask_applied=False,
            detected_species=species_hint if species_hint in {"dog", "cat"} else "other",
        )


class TorchvisionMaskPetCropper:
    def __init__(
        self,
        *,
        score_threshold: float = 0.5,
        mask_threshold: float = 0.5,
        padding_ratio: float = 0.08,
        device: str = "cpu",
    ) -> None:
        self._score_threshold = score_threshold
        self._mask_threshold = mask_threshold
        self._padding_ratio = padding_ratio
        self._device = device
        self._model = None

    def crop_pet(self, image_path: Path, species_hint: str = "unknown") -> CroppedPetImage:
        model = self._get_model()
        image, tensor = self._load_image(image_path)
        prediction = model([tensor.to(self._device)])[0]
        best = self._select_detection(prediction, species_hint=species_hint)
        if best is None:
            return NoOpPetCropper().crop_pet(image_path=image_path, species_hint=species_hint)

        label, box, mask = best
        cropped_path, bbox = self._save_masked_crop(
            image_path=image_path,
            image=image,
            box=box,
            mask=mask,
        )
        return CroppedPetImage(
            source_path=str(image_path),
            cropped_path=str(cropped_path),
            crop_version="identity_mask_rcnn_v1",
            mask_applied=True,
            detected_species=label,
            bbox=bbox,
        )

    def _get_model(self):
        if self._model is not None:
            return self._model
        try:
            from torchvision.models.detection import MaskRCNN_ResNet50_FPN_Weights, maskrcnn_resnet50_fpn
        except ImportError as exc:
            raise RuntimeError(
                "TorchvisionMaskPetCropper requires the optional identity dependencies: pillow, torch, torchvision."
            ) from exc

        weights = MaskRCNN_ResNet50_FPN_Weights.DEFAULT
        model = maskrcnn_resnet50_fpn(weights=weights)
        model.eval()
        model.to(self._device)
        self._model = model
        return model

    def _load_image(self, image_path: Path):
        try:
            from torchvision.transforms import functional as F
        except ImportError as exc:
            raise RuntimeError(
                "TorchvisionMaskPetCropper requires the optional identity dependencies: pillow, torch, torchvision."
            ) from exc

        image = open_image(image_path).convert("RGBA")
        tensor = F.to_tensor(image.convert("RGB"))
        return image, tensor

    def _select_detection(self, prediction, species_hint: str):
        label_map = {17: "cat", 18: "dog"}
        scores = prediction["scores"].detach().cpu()
        labels = prediction["labels"].detach().cpu()
        boxes = prediction["boxes"].detach().cpu()
        masks = prediction["masks"].detach().cpu()

        candidates: list[tuple[str, object, object, float]] = []
        for index, score in enumerate(scores.tolist()):
            if score < self._score_threshold:
                continue
            label_name = label_map.get(int(labels[index].item()))
            if label_name is None:
                continue
            candidates.append((label_name, boxes[index], masks[index, 0], score))

        if not candidates:
            return None

        normalized_hint = species_hint.strip().lower()
        if normalized_hint in {"dog", "cat"}:
            hinted = [item for item in candidates if item[0] == normalized_hint]
            if hinted:
                label_name, box, mask, _score = max(hinted, key=lambda item: item[3])
                return label_name, box, mask

        label_name, box, mask, _score = max(candidates, key=lambda item: item[3])
        return label_name, box, mask

    def _save_masked_crop(self, image_path: Path, image, box, mask):
        try:
            from PIL import Image
        except ImportError as exc:
            raise RuntimeError("Pillow is required for TorchvisionMaskPetCropper.") from exc

        width, height = image.size
        x_min, y_min, x_max, y_max = [int(value) for value in box.tolist()]
        pad_x = int((x_max - x_min) * self._padding_ratio)
        pad_y = int((y_max - y_min) * self._padding_ratio)
        x_min = max(0, x_min - pad_x)
        y_min = max(0, y_min - pad_y)
        x_max = min(width, x_max + pad_x)
        y_max = min(height, y_max + pad_y)

        mask_array = (mask.numpy() > self._mask_threshold).astype("uint8") * 255
        alpha = Image.fromarray(mask_array, mode="L")
        rgba = image.copy()
        rgba.putalpha(alpha)
        crop = rgba.crop((x_min, y_min, x_max, y_max))

        temp_dir = Path(tempfile.mkdtemp(prefix="pawagent-identity-crop-"))
        cropped_path = temp_dir / f"{image_path.stem}_pet.png"
        crop.save(cropped_path)
        return cropped_path, BoundingBox(x_min=x_min, y_min=y_min, x_max=x_max, y_max=y_max)
