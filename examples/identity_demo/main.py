from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pawagent.identity.cropper import NoOpPetCropper
from pawagent.identity.embedder import HashIdentityEmbedder
from pawagent.identity.service import PetIdentityService
from pawagent.identity.store import JsonIdentityProfileStore


def main() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "identity_profiles.json"

        service = PetIdentityService(
            cropper=NoOpPetCropper(),
            embedder=HashIdentityEmbedder(),
            store=JsonIdentityProfileStore(store_path),
            match_threshold=0.85,
        )

        # Use the test images shipped with the repository.
        repo_root = Path(__file__).resolve().parents[2]
        coconut_path = repo_root / "tests" / "coconut.jpg"
        tuna_path = repo_root / "tests" / "tuna.jpg"

        if not coconut_path.exists() or not tuna_path.exists():
            print("Test images not found. Run this script from the repository root.")
            return

        # --- Enroll ---
        print("=== Enrollment ===")
        profile = service.enroll_image(
            image_path=coconut_path,
            pet_id="coconut",
            species_hint="cat",
        )
        print(f"Pet ID: {profile.pet_id}")
        print(f"References after first enroll: {len(profile.references)}")

        # Append a second reference view for the same pet.
        profile = service.enroll_image(
            image_path=coconut_path,
            pet_id="coconut",
            species_hint="cat",
        )
        print(f"References after second enroll: {len(profile.references)}")

        # --- Verify (same pet) ---
        print("\n=== Verification (same pet) ===")
        result = service.verify_image(
            image_path=coconut_path,
            pet_id="coconut",
            species_hint="cat",
        )
        print(f"Match: {'yes' if result.is_match else 'no'}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Best Similarity: {result.best_similarity:.3f}")
        print(f"Compared References: {result.compared_references}")

        # --- Verify (different pet) ---
        print("\n=== Verification (different pet) ===")
        result = service.verify_image(
            image_path=tuna_path,
            pet_id="coconut",
            species_hint="cat",
        )
        print(f"Match: {'yes' if result.is_match else 'no'}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Best Similarity: {result.best_similarity:.3f}")

        # --- Verify (missing profile) ---
        print("\n=== Verification (missing profile) ===")
        result = service.verify_image(
            image_path=tuna_path,
            pet_id="unknown-pet",
            species_hint="cat",
        )
        print(f"Match: {'yes' if result.is_match else 'no'}")
        print(f"Compared References: {result.compared_references}")
        if result.reason:
            print(f"Reason: {result.reason}")


if __name__ == "__main__":
    main()
