from __future__ import annotations

from pathlib import Path

from pawagent.identity.service import PetIdentityService
from pawagent.identity.store import InMemoryIdentityProfileStore
from pawagent.models.identity import CroppedPetImage


class _FakeCropper:
    def crop_pet(self, image_path: Path, species_hint: str = "unknown") -> CroppedPetImage:
        return CroppedPetImage(
            source_path=str(image_path),
            cropped_path=str(image_path),
            crop_version="fake_crop_v1",
            mask_applied=True,
            detected_species="dog" if "dog" in image_path.stem else "cat",
        )


class _FakeEmbedder:
    @property
    def embedding_version(self) -> str:
        return "fake_embedder_v1"

    def embed_image(self, cropped_image: CroppedPetImage) -> list[float]:
        stem = Path(cropped_image.cropped_path).stem
        if "milo" in stem or "dog" in stem:
            return [1.0, 0.0, 0.0]
        if "luna" in stem or "cat" in stem:
            return [0.0, 1.0, 0.0]
        return [0.0, 0.0, 1.0]


def test_identity_service_enrolls_and_verifies_match() -> None:
    service = PetIdentityService(
        cropper=_FakeCropper(),
        embedder=_FakeEmbedder(),
        store=InMemoryIdentityProfileStore(),
        match_threshold=0.9,
    )

    profile = service.enroll_image(Path("milo-dog-a.jpg"), pet_id="pet-1", species_hint="dog")
    result = service.verify_image(Path("milo-dog-b.jpg"), pet_id="pet-1", species_hint="dog")

    assert len(profile.references) == 1
    assert result.is_match is True
    assert result.compared_references == 1
    assert result.best_similarity == 1.0


def test_identity_service_rejects_different_pet() -> None:
    service = PetIdentityService(
        cropper=_FakeCropper(),
        embedder=_FakeEmbedder(),
        store=InMemoryIdentityProfileStore(),
        match_threshold=0.9,
    )
    service.enroll_image(Path("milo-dog-a.jpg"), pet_id="pet-1", species_hint="dog")

    result = service.verify_image(Path("luna-cat-a.jpg"), pet_id="pet-1", species_hint="cat")

    assert result.is_match is False
    assert result.best_similarity == 0.0
    assert "Best similarity" in result.reason


def test_identity_service_compares_against_all_enrolled_references() -> None:
    service = PetIdentityService(
        cropper=_FakeCropper(),
        embedder=_FakeEmbedder(),
        store=InMemoryIdentityProfileStore(),
        match_threshold=0.9,
    )
    profile = service.enroll_image(Path("milo-dog-a.jpg"), pet_id="pet-1", species_hint="dog")
    profile = service.enroll_image(Path("milo-dog-b.jpg"), pet_id="pet-1", species_hint="dog")

    result = service.verify_image(Path("milo-dog-c.jpg"), pet_id="pet-1", species_hint="dog")

    assert len(profile.references) == 2
    assert result.is_match is True
    assert result.compared_references == 2
    assert result.best_similarity == 1.0
