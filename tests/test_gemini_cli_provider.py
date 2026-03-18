from __future__ import annotations

import json
import subprocess
from pathlib import Path

from pawagent.models.media import ImageInput
from pawagent.providers import cli_base as cli_base_module
from pawagent.providers.errors import ProviderExecutionError
from pawagent.providers.gemini_cli_provider import GeminiCliProvider


def test_gemini_cli_provider_invokes_headless_cli_with_image_context(tmp_path: Path) -> None:
    image_path = tmp_path / "pet.jpg"
    image_path.write_bytes(b"fake-image")
    seen: dict[str, object] = {}

    def fake_runner(command: list[str], capture_output: bool, text: bool, check: bool) -> subprocess.CompletedProcess[str]:
        del capture_output, text, check
        seen["command"] = command
        stdout = json.dumps(
            {
                "response": '```json\n{"emotion":{"label":"curious","confidence":0.82,"arousal":"medium","tags":["observant"],"alternatives":["alert"],"evidence":["head tilt"],"uncertainty_note":"Curiosity and alertness overlap."},"behavior":{"label":"observing","confidence":0.74,"target":"environment","intensity":"moderate","evidence":["head tilt"],"alternatives":["exploring"],"uncertainty_note":"Short observation window.","notes":"Head tilt"},"motivation":{"label":"understanding the environment","confidence":0.68,"alternatives":["checking novelty"],"evidence":["head tilt"],"uncertainty_note":"Single frame limits the next-step prediction."},"expression":{"plain_text":"The pet appears curious and is observing the environment.","pet_voice":"I am figuring out what is happening here.","tone":"curious","grounded_in":["head tilt"],"confidence":0.69},"evidence":["head tilt"]}\n```'
            }
        )
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    provider = GeminiCliProvider(runner=fake_runner)
    result = provider.analyze_image(ImageInput(path=image_path), "Analyze this pet image")

    assert result["emotion"]["label"] == "curious"
    assert result["expression"]["pet_voice"] == "I am figuring out what is happening here."
    command = seen["command"]
    assert "--prompt" in command
    assert "--output-format" in command
    assert "json" in command
    assert "--include-directories" in command
    assert str(image_path.parent.resolve()) in command
    assert str(image_path.resolve()) in command[command.index("--prompt") + 1]


def test_gemini_cli_provider_surfaces_failures(tmp_path: Path) -> None:
    image_path = tmp_path / "pet.jpg"
    image_path.write_bytes(b"fake-image")

    def failing_runner(command: list[str], capture_output: bool, text: bool, check: bool) -> subprocess.CompletedProcess[str]:
        del capture_output, text, check
        return subprocess.CompletedProcess(command, 1, stdout="", stderr="not authenticated")

    provider = GeminiCliProvider(runner=failing_runner)

    try:
        provider.analyze_image(ImageInput(path=image_path), "Analyze")
    except ProviderExecutionError as exc:
        assert "not authenticated" in str(exc)
    else:
        raise AssertionError("Expected ProviderExecutionError for failed Gemini CLI execution")


def test_gemini_cli_provider_analyze_video_uses_storyboard_fallback(monkeypatch, tmp_path: Path) -> None:
    storyboard_path = tmp_path / "storyboard.jpg"
    storyboard_path.write_bytes(b"fake-storyboard")
    seen: dict[str, object] = {}

    def fake_runner(command: list[str], capture_output: bool, text: bool, check: bool) -> subprocess.CompletedProcess[str]:
        del capture_output, text, check
        seen["command"] = command
        stdout = json.dumps(
            {
                "response": '```json\n{"emotion":{"label":"curious","confidence":0.82},"behavior":{"label":"observing","confidence":0.74},"motivation":{"label":"understanding the environment","confidence":0.68},"expression":{"plain_text":"The pet appears curious and is observing the environment.","pet_voice":"I am figuring out what is happening here.","confidence":0.69},"evidence":["storyboard frame sequence"]}\n```'
            }
        )
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(
        cli_base_module.video_preprocess,
        "prepare_video_storyboard",
        lambda path: ImageInput(path=storyboard_path),
    )
    provider = GeminiCliProvider(runner=fake_runner)

    result = provider.analyze_video(str(tmp_path / "pet.mp4"), "Analyze this pet video")

    assert result["behavior"]["label"] == "observing"
    command = seen["command"]
    assert str(storyboard_path) in command[command.index("--prompt") + 1]
    assert "storyboard generated from a video clip" in command[command.index("--prompt") + 1]
