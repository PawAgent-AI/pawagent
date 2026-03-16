from __future__ import annotations

import argparse
import logging
from importlib.metadata import version as _pkg_version
from pathlib import Path

from pawagent.agents.behavior_agent import PetBehaviorAgent
from pawagent.agents.expression_agent import PetExpressionAgent
from pawagent.agents.mood_agent import PetEmotionAgent
from pawagent.agents.motivation_agent import PetMotivationAgent
from pawagent.expression.store import JsonExpressionLocalizationStore
from pawagent.identity.cropper import NoOpPetCropper, PetCropper, TorchvisionMaskPetCropper
from pawagent.identity.embedder import HashIdentityEmbedder, IdentityEmbedder, OpenClipIdentityEmbedder
from pawagent.identity.service import PetIdentityService
from pawagent.identity.store import JsonIdentityProfileStore
from pawagent.agents.personality_agent import PetPersonalityAgent
from pawagent.memory.store import JsonAnalysisStore
from pawagent.personality.profiler import PersonalityProfiler
from pawagent.personality.store import JsonPersonalityProfileStore
from pawagent.providers.factory import build_provider
from typing import Any


DEFAULT_MEMORY_PATH = Path(".pawagent") / "analysis_records.json"
DEFAULT_PROFILE_PATH = Path(".pawagent") / "personality_profiles.json"
DEFAULT_EXPRESSION_PATH = Path(".pawagent") / "expression_records.json"
DEFAULT_IDENTITY_PATH = Path(".pawagent") / "identity_profiles.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pawagent")
    parser.add_argument("--version", action="version", version=f"%(prog)s {_pkg_version('pawagent')}")
    parser.add_argument(
        "--memory-path",
        default=str(DEFAULT_MEMORY_PATH),
        help="Path to the persistent analysis store.",
    )
    parser.add_argument(
        "--profile-path",
        default=str(DEFAULT_PROFILE_PATH),
        help="Path to the persistent personality profile cache.",
    )
    parser.add_argument(
        "--expression-path",
        default=str(DEFAULT_EXPRESSION_PATH),
        help="Path to the persistent localized expression cache.",
    )
    parser.add_argument(
        "--identity-path",
        default=str(DEFAULT_IDENTITY_PATH),
        help="Path to the persistent pet identity profile store.",
    )
    parser.add_argument(
        "--provider",
        choices=["mock", "openai", "gemini", "gemini-cli", "codex", "claude", "claude-cli"],
        default="mock",
        help="Model provider to use.",
    )
    parser.add_argument(
        "--openai-model",
        default="gpt-4.1-mini",
        help="OpenAI model name when --provider openai is used.",
    )
    parser.add_argument(
        "--codex-model",
        default="gpt-5.4",
        help="Codex model name when --provider codex is used.",
    )
    parser.add_argument(
        "--gemini-model",
        default="gemini-2.5-flash",
        help="Gemini model name when --provider gemini is used.",
    )
    parser.add_argument(
        "--claude-model",
        default="claude-sonnet-4-6",
        help="Claude model name when --provider claude is used.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_emotion = subparsers.add_parser("analyze-emotion")
    analyze_emotion.add_argument("source_path")
    analyze_emotion.add_argument("--pet-id", default="unknown-pet")
    analyze_emotion.add_argument("--pet-name", default="Unknown")
    analyze_emotion.add_argument("--species", default="unknown")
    analyze_emotion.add_argument("--modality", choices=["image", "video"], default="image")

    analyze_behavior = subparsers.add_parser("analyze-behavior")
    analyze_behavior.add_argument("source_path")
    analyze_behavior.add_argument("--pet-id", default="unknown-pet")
    analyze_behavior.add_argument("--pet-name", default="Unknown")
    analyze_behavior.add_argument("--species", default="unknown")
    analyze_behavior.add_argument("--modality", choices=["image", "video"], default="image")

    analyze_motivation = subparsers.add_parser("analyze-motivation")
    analyze_motivation.add_argument("source_path")
    analyze_motivation.add_argument("--pet-id", default="unknown-pet")
    analyze_motivation.add_argument("--pet-name", default="Unknown")
    analyze_motivation.add_argument("--species", default="unknown")
    analyze_motivation.add_argument("--modality", choices=["image", "video"], default="image")

    profile_pet = subparsers.add_parser("profile-pet")
    profile_pet.add_argument("--pet-id", default="unknown-pet")

    express_pet = subparsers.add_parser("express-pet")
    express_pet.add_argument("source_path")
    express_pet.add_argument("--pet-id", default="unknown-pet")
    express_pet.add_argument("--pet-name", default="Unknown")
    express_pet.add_argument("--species", default="unknown")
    express_pet.add_argument("--modality", choices=["image", "video"], default="image")
    express_pet.add_argument("--locale", default="en")
    express_pet.add_argument("--style", default="default")

    enroll_identity = subparsers.add_parser("enroll-identity")
    enroll_identity.add_argument("source_path")
    enroll_identity.add_argument("--pet-id", required=True)
    enroll_identity.add_argument("--species", default="unknown")
    enroll_identity.add_argument("--identity-cropper", choices=["noop", "maskrcnn"], default="noop")
    enroll_identity.add_argument("--identity-embedder", choices=["hash", "openclip"], default="hash")

    verify_identity = subparsers.add_parser("verify-identity")
    verify_identity.add_argument("source_path")
    verify_identity.add_argument("--pet-id", required=True)
    verify_identity.add_argument("--species", default="unknown")
    verify_identity.add_argument("--identity-cropper", choices=["noop", "maskrcnn"], default="noop")
    verify_identity.add_argument("--identity-embedder", choices=["hash", "openclip"], default="hash")
    verify_identity.add_argument("--match-threshold", type=float, default=0.85)

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="WARNING",
        help="Set logging verbosity.",
    )

    return parser


def build_identity_service(
    *,
    identity_path: Path,
    cropper_name: str,
    embedder_name: str,
    match_threshold: float = 0.85,
) -> PetIdentityService:
    cropper: PetCropper
    if cropper_name == "maskrcnn":
        cropper = TorchvisionMaskPetCropper()
    else:
        cropper = NoOpPetCropper()

    embedder: IdentityEmbedder
    if embedder_name == "openclip":
        embedder = OpenClipIdentityEmbedder()
    else:
        embedder = HashIdentityEmbedder()

    return PetIdentityService(
        cropper=cropper,
        embedder=embedder,
        store=JsonIdentityProfileStore(identity_path),
        match_threshold=match_threshold,
    )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    memory = JsonAnalysisStore(Path(args.memory_path))
    profile_store = JsonPersonalityProfileStore(Path(args.profile_path))
    expression_store = JsonExpressionLocalizationStore(Path(args.expression_path))
    identity_path = Path(args.identity_path)
    provider = build_provider(
        args.provider,
        args.openai_model,
        args.codex_model,
        args.gemini_model,
        args.claude_model,
    )

    agent: Any
    result: Any

    if args.command == "analyze-emotion":
        profiler = PersonalityProfiler(memory, profile_store=profile_store)
        agent = PetEmotionAgent(provider=provider, memory_store=memory, profiler=profiler)
        result = agent.analyze_media(
            path=Path(args.source_path),
            pet_id=args.pet_id,
            pet_name=args.pet_name,
            species=args.species,
            modality=args.modality,
        )
        print(f"Emotion: {result.mood.primary}")
        print(f"Observed Species: {result.analysis.species.observed_species}")
        print(f"Confidence: {result.mood.confidence:.2f}")
        if result.analysis.species.mismatch_warning:
            print(f"Species Warning: {result.analysis.species.mismatch_warning}")
        if result.mood.arousal:
            print(f"Arousal: {result.mood.arousal}")
        if result.mood.alternatives:
            print(f"Alternatives: {', '.join(result.mood.alternatives)}")
        if result.mood.evidence:
            print(f"Evidence: {', '.join(result.mood.evidence)}")
        if result.mood.uncertainty_note:
            print(f"Uncertainty: {result.mood.uncertainty_note}")
        if result.summary:
            print(f"Summary: {result.summary}")
        return 0

    if args.command == "analyze-behavior":
        profiler = PersonalityProfiler(memory, profile_store=profile_store)
        agent = PetBehaviorAgent(provider=provider, memory_store=memory, profiler=profiler)
        result = agent.analyze_media(
            path=Path(args.source_path),
            pet_id=args.pet_id,
            pet_name=args.pet_name,
            species=args.species,
            modality=args.modality,
        )
        print(f"Behavior: {result.label}")
        print(f"Confidence: {result.confidence:.2f}")
        if result.target:
            print(f"Target: {result.target}")
        if result.intensity:
            print(f"Intensity: {result.intensity}")
        if result.alternatives:
            print(f"Alternatives: {', '.join(result.alternatives)}")
        if result.evidence:
            print(f"Evidence: {', '.join(result.evidence)}")
        if result.uncertainty_note:
            print(f"Uncertainty: {result.uncertainty_note}")
        if result.notes:
            print(f"Notes: {result.notes}")
        return 0

    if args.command == "analyze-motivation":
        profiler = PersonalityProfiler(memory, profile_store=profile_store)
        agent = PetMotivationAgent(provider=provider, memory_store=memory, profiler=profiler)
        result = agent.analyze_media(
            path=Path(args.source_path),
            pet_id=args.pet_id,
            pet_name=args.pet_name,
            species=args.species,
            modality=args.modality,
        )
        print(f"Motivation: {result.label}")
        print(f"Confidence: {result.confidence:.2f}")
        if result.alternatives:
            print(f"Alternatives: {', '.join(result.alternatives)}")
        if result.evidence:
            print(f"Evidence: {', '.join(result.evidence)}")
        if result.uncertainty_note:
            print(f"Uncertainty: {result.uncertainty_note}")
        return 0

    if args.command == "profile-pet":
        profiler = PersonalityProfiler(memory, profile_store=profile_store)
        agent = PetPersonalityAgent(memory_store=memory, profiler=profiler)
        result = agent.get_profile(pet_id=args.pet_id)
        print(f"Pet ID: {result.pet_id}")
        for trait in result.traits:
            print(f"{trait.name}: {trait.value:.2f}")
        return 0

    if args.command == "express-pet":
        profiler = PersonalityProfiler(memory, profile_store=profile_store)
        agent = PetExpressionAgent(
            provider=provider,
            memory_store=memory,
            profiler=profiler,
            localization_store=expression_store,
        )
        result = agent.express_image(
            image_path=Path(args.source_path),
            pet_id=args.pet_id,
            pet_name=args.pet_name,
            species=args.species,
            modality=args.modality,
            locale=args.locale,
            style=args.style,
        )
        print(f"Plain: {result.plain_text}")
        print(f"Pet Voice: {result.pet_voice}")
        print(f"Locale: {result.locale}")
        if result.tone:
            print(f"Tone: {result.tone}")
        if result.grounded_in:
            print(f"Grounded In: {', '.join(result.grounded_in)}")
        print(f"Confidence: {result.confidence:.2f}")
        return 0

    if args.command == "enroll-identity":
        service = build_identity_service(
            identity_path=identity_path,
            cropper_name=args.identity_cropper,
            embedder_name=args.identity_embedder,
        )
        profile = service.enroll_image(
            image_path=Path(args.source_path),
            pet_id=args.pet_id,
            species_hint=args.species,
        )
        print(f"Pet ID: {profile.pet_id}")
        print(f"References: {len(profile.references)}")
        print("Enrollment Mode: append")
        print(f"Species Hint: {profile.species_hint}")
        last = profile.references[-1]
        print(f"Latest Source: {last.source_path}")
        print(f"Detected Species: {last.detected_species}")
        print(f"Embedding Version: {last.embedding_version}")
        return 0

    if args.command == "verify-identity":
        service = build_identity_service(
            identity_path=identity_path,
            cropper_name=args.identity_cropper,
            embedder_name=args.identity_embedder,
            match_threshold=args.match_threshold,
        )
        result = service.verify_image(
            image_path=Path(args.source_path),
            pet_id=args.pet_id,
            species_hint=args.species,
        )
        print(f"Pet ID: {result.pet_id}")
        print(f"Match: {'yes' if result.is_match else 'no'}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Best Similarity: {result.best_similarity:.3f}")
        print(f"Compared References: {result.compared_references}")
        if result.reason:
            print(f"Reason: {result.reason}")
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
