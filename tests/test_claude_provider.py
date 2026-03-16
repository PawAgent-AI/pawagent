from __future__ import annotations

from pathlib import Path

from pawagent.models.media import ImageInput
from pawagent.providers.errors import (
    ProviderAuthenticationError,
    ProviderExecutionError,
    ProviderOutputParseError,
)
from pawagent.providers.claude_provider import ClaudeProvider


class _FakeTextBlock:
    def __init__(self, text: str) -> None:
        self.type = "text"
        self.text = text


class _FakeResponse:
    def __init__(self, text: str) -> None:
        self.content = [_FakeTextBlock(text)]


class _FakeMessages:
    def __init__(self, output_text: str) -> None:
        self._output_text = output_text
        self.last_request: dict[str, object] | None = None

    def create(self, **kwargs: object) -> _FakeResponse:
        self.last_request = kwargs
        return _FakeResponse(self._output_text)


class _FakeClient:
    def __init__(self, output_text: str) -> None:
        self.messages = _FakeMessages(output_text)


SAMPLE_RESPONSE = '{"species":{"requested_species":"unknown","observed_species":"dog","confidence":0.95,"used_framework":"dog","mismatch_warning":""},"emotion":{"label":"playful","confidence":0.93,"arousal":"high","tags":["engaged","happy"],"alternatives":["excited"],"evidence":["tail up"],"uncertainty_note":"Could also be excitement."},"behavior":{"label":"seeking interaction","confidence":0.85,"target":"human","intensity":"high","evidence":["tail up"],"alternatives":["playing"],"uncertainty_note":"Single frame limits duration certainty.","notes":"Tail up"},"motivation":{"label":"seeking engagement","confidence":0.79,"alternatives":["wants play"],"evidence":["tail up"],"uncertainty_note":"Single frame limits certainty."},"expression":{"plain_text":"The pet appears playful and is actively seeking interaction.","pet_voice":"I want to play with you right now.","tone":"eager","grounded_in":["tail up"],"confidence":0.78},"evidence":["tail up"]}'


def test_claude_provider_normalizes_response_and_builds_request(tmp_path: Path) -> None:
    image_path = tmp_path / "pet.jpg"
    image_path.write_bytes(b"fake-image-bytes")
    client = _FakeClient(SAMPLE_RESPONSE)
    provider = ClaudeProvider(client=client)

    result = provider.analyze_image(ImageInput(path=image_path), "Analyze this pet image")

    assert result["emotion"]["label"] == "playful"
    assert result["emotion"]["arousal"] == "high"
    assert result["behavior"]["label"] == "seeking interaction"
    assert result["expression"]["pet_voice"] == "I want to play with you right now."
    request = client.messages.last_request
    assert request is not None
    assert request["model"] == "claude-sonnet-4-6"
    content = request["messages"][0]["content"]
    assert content[0]["type"] == "image"
    assert content[0]["source"]["type"] == "base64"
    assert content[0]["source"]["media_type"] == "image/jpeg"
    assert content[1]["type"] == "text"


def test_claude_provider_uses_custom_model(tmp_path: Path) -> None:
    image_path = tmp_path / "pet.jpg"
    image_path.write_bytes(b"fake-image-bytes")
    client = _FakeClient(SAMPLE_RESPONSE)
    provider = ClaudeProvider(model="claude-opus-4-6", client=client)

    provider.analyze_image(ImageInput(path=image_path), "Analyze this pet image")

    request = client.messages.last_request
    assert request["model"] == "claude-opus-4-6"


def test_claude_provider_parses_markdown_json_blocks() -> None:
    client = _FakeClient(
        '```json\n{"emotion":{"label":"relaxed","confidence":0.88,"arousal":"low","tags":["calm"],"alternatives":["tired"],"evidence":["eyes half closed"],"uncertainty_note":"Relaxed and tired can overlap."},"behavior":{"label":"resting","confidence":0.85,"target":"self","intensity":"low","evidence":["eyes half closed"],"alternatives":["settling"],"uncertainty_note":"Static image limits duration certainty.","notes":"Eyes half closed"},"motivation":{"label":"wants rest","confidence":0.79,"alternatives":["wants low stimulation"],"evidence":["eyes half closed"],"uncertainty_note":"Single frame limits duration certainty."},"expression":{"plain_text":"The pet appears comfortable and is likely resting.","pet_voice":"I feel comfortable and want to rest.","tone":"calm","grounded_in":["eyes half closed"],"confidence":0.8},"evidence":["eyes half closed"]}\n```'
    )
    provider = ClaudeProvider(client=client)

    result = provider._parse_response(client.messages._output_text)

    assert result["emotion"]["label"] == "relaxed"
    assert result["expression"]["pet_voice"] == "I feel comfortable and want to rest."


def test_claude_provider_requires_api_key_without_injected_client(monkeypatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    provider = ClaudeProvider(api_key=None)

    try:
        provider._get_client()
    except ProviderAuthenticationError as exc:
        assert "ANTHROPIC_API_KEY" in str(exc)
    else:
        raise AssertionError("Expected missing API key to raise ProviderAuthenticationError")


def test_claude_provider_wraps_backend_failures(tmp_path: Path) -> None:
    image_path = tmp_path / "pet.jpg"
    image_path.write_bytes(b"fake-image")

    class _FailingMessages:
        def create(self, **kwargs: object) -> object:
            del kwargs
            raise RuntimeError("boom")

    class _FailingClient:
        def __init__(self) -> None:
            self.messages = _FailingMessages()

    provider = ClaudeProvider(client=_FailingClient())

    try:
        provider.analyze_image(ImageInput(path=image_path), "Analyze")
    except ProviderExecutionError as exc:
        assert "Claude request failed" in str(exc)
    else:
        raise AssertionError("Expected ProviderExecutionError")


def test_claude_provider_rejects_missing_text_output(tmp_path: Path) -> None:
    image_path = tmp_path / "pet.jpg"
    image_path.write_bytes(b"fake-image")

    class _EmptyMessages:
        def create(self, **kwargs: object) -> object:
            del kwargs
            return type("Response", (), {"content": []})()

    class _EmptyClient:
        def __init__(self) -> None:
            self.messages = _EmptyMessages()

    provider = ClaudeProvider(client=_EmptyClient())

    try:
        provider.analyze_image(ImageInput(path=image_path), "Analyze")
    except ProviderOutputParseError as exc:
        assert "text output" in str(exc)
    else:
        raise AssertionError("Expected ProviderOutputParseError")


def test_claude_provider_render_expression_english_passthrough() -> None:
    from pawagent.models.analysis import (
        ExpressionResult,
        MotivationResult,
        SpeciesAssessment,
        UnifiedAnalysisResult,
    )
    from pawagent.models.behavior import BehaviorResult
    from pawagent.models.mood import MoodResult

    analysis = UnifiedAnalysisResult(
        species=SpeciesAssessment(
            requested_species="dog",
            observed_species="dog",
            confidence=0.9,
            used_framework="dog",
            mismatch_warning="",
        ),
        emotion=MoodResult(primary="happy", confidence=0.9),
        behavior=BehaviorResult(label="playing", confidence=0.8),
        motivation=MotivationResult(label="fun", confidence=0.7),
        expression=ExpressionResult(
            plain_text="Happy dog playing.",
            pet_voice="I am happy!",
            tone="joyful",
            grounded_in=["tail wagging"],
            confidence=0.85,
        ),
        evidence=["tail wagging"],
    )
    provider = ClaudeProvider(client=_FakeClient(""))
    result = provider.render_expression(analysis, locale="en")
    assert result["plain_text"] == "Happy dog playing."
    assert result["pet_voice"] == "I am happy!"
