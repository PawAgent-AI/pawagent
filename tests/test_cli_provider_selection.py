from __future__ import annotations

from unittest.mock import patch, MagicMock

from pawagent.providers.claude_cli_provider import ClaudeCliProvider
from pawagent.providers.claude_provider import ClaudeProvider
from pawagent.providers.factory import build_provider


def test_factory_builds_claude_provider() -> None:
    provider = build_provider("claude", "gpt-4.1-mini", "gpt-5.4", "gemini-2.5-flash", "claude-sonnet-4-6")
    assert isinstance(provider, ClaudeProvider)


def test_factory_builds_claude_cli_provider() -> None:
    provider = build_provider("claude-cli", "gpt-4.1-mini", "gpt-5.4", "gemini-2.5-flash", "claude-opus-4-6")
    assert isinstance(provider, ClaudeCliProvider)


def test_factory_passes_claude_model_to_provider() -> None:
    provider = build_provider("claude", "gpt-4.1-mini", "gpt-5.4", "gemini-2.5-flash", "claude-opus-4-6")
    assert isinstance(provider, ClaudeProvider)
    assert provider._model == "claude-opus-4-6"


def test_factory_passes_claude_model_to_cli_provider() -> None:
    provider = build_provider("claude-cli", "gpt-4.1-mini", "gpt-5.4", "gemini-2.5-flash", "claude-sonnet-4-6")
    assert isinstance(provider, ClaudeCliProvider)
    assert provider._model == "claude-sonnet-4-6"


def test_cli_parser_accepts_claude_provider() -> None:
    from cli.main import build_parser

    parser = build_parser()
    args = parser.parse_args([
        "--provider", "claude",
        "--claude-model", "claude-opus-4-6",
        "analyze-emotion", "dog.jpg",
        "--pet-id", "pet-1",
    ])
    assert args.provider == "claude"
    assert args.claude_model == "claude-opus-4-6"


def test_cli_parser_accepts_claude_cli_provider() -> None:
    from cli.main import build_parser

    parser = build_parser()
    args = parser.parse_args([
        "--provider", "claude-cli",
        "analyze-emotion", "dog.jpg",
        "--pet-id", "pet-1",
    ])
    assert args.provider == "claude-cli"
    assert args.claude_model == "claude-sonnet-4-6"


def test_cli_main_uses_claude_provider(tmp_path) -> None:
    """Verify that ``cli.main.main()`` constructs a ClaudeProvider when --provider claude is given."""
    from cli.main import main

    built_providers: list[object] = []
    original_build = build_provider

    def spy_build(*args, **kwargs):
        provider = original_build(*args, **kwargs)
        built_providers.append(provider)
        return provider

    with (
        patch("cli.main.build_provider", side_effect=spy_build),
        patch("sys.argv", [
            "pawagent",
            "--provider", "claude",
            "--claude-model", "claude-opus-4-6",
            "--memory-path", str(tmp_path / "mem.json"),
            "--profile-path", str(tmp_path / "prof.json"),
            "--expression-path", str(tmp_path / "expr.json"),
            "analyze-emotion", "dog.jpg",
            "--pet-id", "pet-1",
        ]),
        patch("pawagent.providers.claude_provider.ClaudeProvider.analyze_image") as mock_analyze,
    ):
        mock_analyze.return_value = {
            "emotion": {"label": "happy", "confidence": 0.9, "arousal": "high",
                        "tags": [], "alternatives": [], "evidence": [], "uncertainty_note": ""},
            "behavior": {"label": "playing", "confidence": 0.8, "target": "owner",
                         "intensity": "high", "evidence": [], "alternatives": [],
                         "uncertainty_note": "", "notes": ""},
            "motivation": {"label": "seeking engagement", "confidence": 0.7,
                           "alternatives": [], "evidence": [], "uncertainty_note": ""},
            "expression": {"plain_text": "Happy pup!", "pet_voice": "Woof!",
                           "tone": "excited", "grounded_in": [], "confidence": 0.8},
            "evidence": [],
            "species": {"observed_species": "dog"},
        }
        main()

    assert len(built_providers) == 1
    assert isinstance(built_providers[0], ClaudeProvider)
    assert built_providers[0]._model == "claude-opus-4-6"


def test_cli_main_uses_claude_cli_provider(tmp_path) -> None:
    """Verify that ``cli.main.main()`` constructs a ClaudeCliProvider when --provider claude-cli is given."""
    from cli.main import main

    built_providers: list[object] = []
    original_build = build_provider

    def spy_build(*args, **kwargs):
        provider = original_build(*args, **kwargs)
        built_providers.append(provider)
        return provider

    with (
        patch("cli.main.build_provider", side_effect=spy_build),
        patch("sys.argv", [
            "pawagent",
            "--provider", "claude-cli",
            "--memory-path", str(tmp_path / "mem.json"),
            "--profile-path", str(tmp_path / "prof.json"),
            "--expression-path", str(tmp_path / "expr.json"),
            "analyze-emotion", "dog.jpg",
            "--pet-id", "pet-1",
        ]),
        patch("pawagent.providers.cli_base.CliAgentProvider.analyze_image") as mock_analyze,
    ):
        mock_analyze.return_value = {
            "emotion": {"label": "happy", "confidence": 0.9, "arousal": "high",
                        "tags": [], "alternatives": [], "evidence": [], "uncertainty_note": ""},
            "behavior": {"label": "playing", "confidence": 0.8, "target": "owner",
                         "intensity": "high", "evidence": [], "alternatives": [],
                         "uncertainty_note": "", "notes": ""},
            "motivation": {"label": "seeking engagement", "confidence": 0.7,
                           "alternatives": [], "evidence": [], "uncertainty_note": ""},
            "expression": {"plain_text": "Happy pup!", "pet_voice": "Woof!",
                           "tone": "excited", "grounded_in": [], "confidence": 0.8},
            "evidence": [],
            "species": {"observed_species": "dog"},
        }
        main()

    assert len(built_providers) == 1
    assert isinstance(built_providers[0], ClaudeCliProvider)
