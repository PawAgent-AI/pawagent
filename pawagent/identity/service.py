from __future__ import annotations

import logging
from pathlib import Path

from pawagent.identity.cropper import PetCropper
from pawagent.identity.embedder import IdentityEmbedder, cosine_similarity
from pawagent.identity.store import IdentityProfileStore
from pawagent.models.identity import IdentityMatchResult, IdentityReference, PetIdentityProfile

logger = logging.getLogger(__name__)


class PetIdentityService:
    def __init__(
        self,
        *,
        cropper: PetCropper,
        embedder: IdentityEmbedder,
        store: IdentityProfileStore,
        match_threshold: float = 0.85,
    ) -> None:
        self._cropper = cropper
        self._embedder = embedder
        self._store = store
        self._match_threshold = match_threshold

    def enroll_image(self, image_path: Path, pet_id: str, species_hint: str = "unknown") -> PetIdentityProfile:
        logger.info("Enrolling identity for pet_id=%s from %s", pet_id, image_path)
        cropped = self._cropper.crop_pet(image_path=image_path, species_hint=species_hint)
        embedding = self._embedder.embed_image(cropped)
        reference = IdentityReference(
            source_path=str(image_path),
            cropped_path=cropped.cropped_path,
            embedding=embedding,
            detected_species=cropped.detected_species,
            crop_version=cropped.crop_version,
            embedding_version=self._embedder.embedding_version,
        )
        # Enrollment is append-only so each pet profile can accumulate multiple
        # reference views across lighting, pose, and background changes.
        profile = self._store.add_reference(pet_id=pet_id, reference=reference, species_hint=species_hint)
        logger.info("Enrolled identity for pet_id=%s, total references=%d", pet_id, len(profile.references))
        return profile

    def verify_image(self, image_path: Path, pet_id: str, species_hint: str = "unknown") -> IdentityMatchResult:
        logger.info("Verifying identity for pet_id=%s from %s", pet_id, image_path)
        profile = self._store.get_profile(pet_id)
        if profile is None or not profile.references:
            return IdentityMatchResult(
                pet_id=pet_id,
                is_match=False,
                confidence=0.0,
                best_similarity=0.0,
                compared_references=0,
                reason="No identity references enrolled for this pet.",
            )

        cropped = self._cropper.crop_pet(image_path=image_path, species_hint=species_hint)
        embedding = self._embedder.embed_image(cropped)
        similarities = [cosine_similarity(embedding, reference.embedding) for reference in profile.references]
        best_similarity = max(similarities) if similarities else 0.0
        best_similarity = max(-1.0, min(1.0, best_similarity))
        is_match = best_similarity >= self._match_threshold
        logger.info("Identity verification for pet_id=%s: match=%s, similarity=%.3f", pet_id, is_match, best_similarity)
        return IdentityMatchResult(
            pet_id=pet_id,
            is_match=is_match,
            confidence=max(0.0, min(1.0, (best_similarity + 1.0) / 2.0)),
            best_similarity=best_similarity,
            compared_references=len(profile.references),
            reason=f"Best similarity {best_similarity:.3f} across {len(profile.references)} reference image(s).",
        )
