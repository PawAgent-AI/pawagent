from __future__ import annotations

import json
import subprocess
from pathlib import Path

from pawagent.models.media import ImageInput
from pawagent.providers import cli_base as cli_base_module
from pawagent.providers.errors import ProviderExecutionError
from pawagent.providers.codex_provider import CodexProvider


def test_codex_provider_invokes_codex_exec_with_schema_and_image(tmp_path: Path) -> None:
    image_path = tmp_path / "pet.jpg"
    image_path.write_bytes(b"fake-image")
    seen: dict[str, object] = {}

    def fake_runner(command: list[str], capture_output: bool, text: bool, check: bool) -> subprocess.CompletedProcess[str]:
        del capture_output, text, check
        seen["command"] = command
        output_path = Path(command[command.index("--output-last-message") + 1])
        output_path.write_text(
            json.dumps(
                {
                    "emotion": {
                        "label": "curious",
                        "confidence": 0.81,
                        "arousal": "medium",
                        "tags": ["observant"],
                        "alternatives": ["alert"],
                        "evidence": ["head tilted toward the camera"],
                        "uncertainty_note": "Curiosity and alertness overlap.",
                    },
                    "behavior": {
                        "label": "observing",
                        "confidence": 0.74,
                        "target": "environment",
                        "intensity": "moderate",
                        "evidence": ["head tilted toward the camera"],
                        "alternatives": ["exploring"],
                        "uncertainty_note": "Short observation window.",
                        "notes": "Head tilted toward the camera",
                    },
                    "motivation": {
                        "label": "understanding the environment",
                        "confidence": 0.68,
                        "alternatives": ["checking novelty"],
                        "evidence": ["head tilted toward the camera"],
                        "uncertainty_note": "Single frame limits the next-step prediction.",
                    },
                    "expression": {
                        "plain_text": "The pet appears curious and is observing the environment.",
                        "pet_voice": "I am figuring out what is happening here.",
                        "tone": "curious",
                        "grounded_in": ["head tilted toward the camera"],
                        "confidence": 0.69,
                    },
                    "evidence": ["head tilted toward the camera"],
                }
            ),
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    provider = CodexProvider(model="gpt-5.4", runner=fake_runner)
    result = provider.analyze_image(ImageInput(path=image_path), "Analyze this pet image")

    assert result["emotion"]["label"] == "curious"
    assert result["expression"]["pet_voice"] == "I am figuring out what is happening here."
    command = seen["command"]
    assert "--image" in command
    assert str(image_path) in command
    assert "--output-schema" in command
    assert "--output-last-message" in command
    assert "Analyze this pet image" in command[-1]


def test_codex_provider_surfaces_exec_failures(tmp_path: Path) -> None:
    image_path = tmp_path / "pet.jpg"
    image_path.write_bytes(b"fake-image")

    def failing_runner(command: list[str], capture_output: bool, text: bool, check: bool) -> subprocess.CompletedProcess[str]:
        del capture_output, text, check
        return subprocess.CompletedProcess(command, 1, stdout="", stderr="not logged in")

    provider = CodexProvider(runner=failing_runner)

    try:
        provider.analyze_image(ImageInput(path=image_path), "Analyze")
    except ProviderExecutionError as exc:
        assert "not logged in" in str(exc)
    else:
        raise AssertionError("Expected ProviderExecutionError for failed codex execution")


def test_codex_provider_analyze_video_uses_storyboard_fallback(monkeypatch, tmp_path: Path) -> None:
    storyboard_path = tmp_path / "storyboard.jpg"
    storyboard_path.write_bytes(b"fake-storyboard")
    seen: dict[str, object] = {}

    def fake_runner(command: list[str], capture_output: bool, text: bool, check: bool) -> subprocess.CompletedProcess[str]:
        del capture_output, text, check
        seen["command"] = command
        output_path = Path(command[command.index("--output-last-message") + 1])
        output_path.write_text(
            json.dumps(
                {
                    "emotion": {"label": "curious", "confidence": 0.8},
                    "behavior": {"label": "exploring", "confidence": 0.76},
                    "motivation": {"label": "exploring novelty", "confidence": 0.7},
                    "expression": {
                        "plain_text": "The pet appears curious and is exploring.",
                        "pet_voice": "I am exploring what is here.",
                        "confidence": 0.68,
                    },
                    "evidence": ["storyboard frame sequence"],
                }
            ),
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(
        cli_base_module.video_preprocess,
        "prepare_video_storyboard",
        lambda path: ImageInput(path=storyboard_path),
    )
    provider = CodexProvider(runner=fake_runner)

    result = provider.analyze_video(str(tmp_path / "pet.mp4"), "Analyze this pet video")

    assert result["behavior"]["label"] == "exploring"
    command = seen["command"]
    assert str(storyboard_path) in command
    assert "storyboard generated from a video clip" in command[-1]
