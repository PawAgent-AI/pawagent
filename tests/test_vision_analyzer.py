from __future__ import annotations

from pathlib import Path

from pawagent.vision.analyzer import VisionAnalyzer


class _CapturingProvider:
    def __init__(self) -> None:
        self.last_prompt = ""

    def analyze_image(self, image: object, prompt: str) -> dict[str, object]:
        del image
        self.last_prompt = prompt
        return {
            "species": {
                "observed_species": "dog",
                "confidence": 0.94,
                "used_framework": "dog",
                "mismatch_warning": "",
            },
            "emotion": {
                "label": "curious",
                "confidence": 0.8,
                "arousal": "medium",
                "tags": ["observant"],
                "alternatives": ["alert"],
                "evidence": ["steady gaze"],
                "uncertainty_note": "Curiosity and alertness overlap.",
            },
            "behavior": {
                "label": "observing",
                "confidence": 0.71,
                "target": "environment",
                "intensity": "moderate",
                "evidence": ["head tilt"],
                "alternatives": ["exploring"],
                "uncertainty_note": "Single frame limits duration certainty.",
                "notes": "Head tilt",
            },
            "motivation": {
                "label": "understanding the environment",
                "confidence": 0.66,
                "alternatives": ["checking novelty"],
                "evidence": ["steady gaze"],
                "uncertainty_note": "Single frame limits the next-step prediction.",
            },
            "expression": {
                "plain_text": "The pet appears curious and is observing the environment.",
                "pet_voice": "I am figuring out what is happening here.",
                "tone": "curious",
                "grounded_in": ["steady gaze"],
                "confidence": 0.69,
            },
            "evidence": ["steady gaze"],
        }


def test_vision_analyzer_uses_dog_specific_prompt() -> None:
    provider = _CapturingProvider()
    analyzer = VisionAnalyzer(provider)  # type: ignore[arg-type]

    analyzer.analyze(Path("dog.jpg"), species="dog")

    assert "Species-specific guidance for dogs" in provider.last_prompt
    assert "User-declared species hint: dog" in provider.last_prompt
    assert "tail carriage" in provider.last_prompt


def test_vision_analyzer_uses_cat_specific_prompt() -> None:
    provider = _CapturingProvider()
    analyzer = VisionAnalyzer(provider)  # type: ignore[arg-type]

    analyzer.analyze(Path("cat.jpg"), species="cat")

    assert "Species-specific guidance for cats" in provider.last_prompt
    assert "User-declared species hint: cat" in provider.last_prompt
    assert "whisker position" in provider.last_prompt
