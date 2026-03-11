from __future__ import annotations

from pathlib import Path

from pawagent.models.media import ImageInput
from pawagent.providers.errors import (
    ProviderAuthenticationError,
    ProviderExecutionError,
    ProviderOutputParseError,
)
from pawagent.providers.openai_provider import OpenAIProvider


class _FakeResponses:
    def __init__(self, output_text: str) -> None:
        self._output_text = output_text
        self.last_request: dict[str, object] | None = None

    def create(self, **kwargs: object) -> object:
        self.last_request = kwargs
        return type("Response", (), {"output_text": self._output_text})()


class _FakeClient:
    def __init__(self, output_text: str) -> None:
        self.responses = _FakeResponses(output_text)


def test_openai_provider_normalizes_response_and_builds_image_request(tmp_path: Path) -> None:
    image_path = tmp_path / "pet.jpg"
    image_path.write_bytes(b"fake-image-bytes")
    client = _FakeClient(
        '{"emotion":{"label":"playful","confidence":0.93,"arousal":"high","tags":["engaged","happy"],"alternatives":["excited"],"evidence":["tail up"],"uncertainty_note":"Could also be excitement."},"behavior":{"label":"seeking interaction","confidence":0.85,"target":"human","intensity":"high","evidence":["tail up"],"alternatives":["playing"],"uncertainty_note":"Single frame limits duration certainty.","notes":"Tail up"},"motivation":{"label":"seeking engagement","confidence":0.79,"alternatives":["wants play"],"evidence":["tail up"],"uncertainty_note":"Single frame limits certainty."},"expression":{"plain_text":"The pet appears playful and is actively seeking interaction.","pet_voice":"I want to play with you right now.","tone":"eager","grounded_in":["tail up"],"confidence":0.78},"evidence":["tail up"]}'
    )
    provider = OpenAIProvider(client=client)

    result = provider.analyze_image(ImageInput(path=image_path), "Analyze this pet image")

    assert result["emotion"]["label"] == "playful"
    assert result["emotion"]["arousal"] == "high"
    assert result["behavior"]["label"] == "seeking interaction"
    assert result["expression"]["pet_voice"] == "I want to play with you right now."
    request = client.responses.last_request
    assert request is not None
    assert request["model"] == "gpt-4.1-mini"
    content = request["input"][0]["content"]
    assert content[1]["type"] == "input_image"
    assert str(content[1]["image_url"]).startswith("data:image/jpeg;base64,")


def test_openai_provider_parses_markdown_json_blocks() -> None:
    client = _FakeClient(
        '```json\n{"emotion":{"label":"relaxed","confidence":0.88,"arousal":"low","tags":["calm"],"alternatives":["tired"],"evidence":["eyes half closed"],"uncertainty_note":"Relaxed and tired can overlap."},"behavior":{"label":"resting","confidence":0.85,"target":"self","intensity":"low","evidence":["eyes half closed"],"alternatives":["settling"],"uncertainty_note":"Static image limits duration certainty.","notes":"Eyes half closed"},"motivation":{"label":"wants rest","confidence":0.79,"alternatives":["wants low stimulation"],"evidence":["eyes half closed"],"uncertainty_note":"Single frame limits duration certainty."},"expression":{"plain_text":"The pet appears comfortable and is likely resting.","pet_voice":"I feel comfortable and want to rest.","tone":"calm","grounded_in":["eyes half closed"],"confidence":0.8},"evidence":["eyes half closed"]}\n```'
    )
    provider = OpenAIProvider(client=client)

    result = provider._parse_response(client.responses._output_text)

    assert result["emotion"]["label"] == "relaxed"
    assert result["expression"]["pet_voice"] == "I feel comfortable and want to rest."


def test_openai_provider_requires_api_key_without_injected_client(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    provider = OpenAIProvider(api_key=None)

    try:
        provider._get_client()
    except ProviderAuthenticationError as exc:
        assert "OPENAI_API_KEY" in str(exc)
    else:
        raise AssertionError("Expected missing API key to raise ProviderAuthenticationError")


def test_openai_provider_wraps_backend_failures(tmp_path: Path) -> None:
    image_path = tmp_path / "pet.jpg"
    image_path.write_bytes(b"fake-image")

    class _FailingResponses:
        def create(self, **kwargs: object) -> object:
            del kwargs
            raise RuntimeError("boom")

    class _FailingClient:
        def __init__(self) -> None:
            self.responses = _FailingResponses()

    provider = OpenAIProvider(client=_FailingClient())

    try:
        provider.analyze_image(ImageInput(path=image_path), "Analyze")
    except ProviderExecutionError as exc:
        assert "OpenAI request failed" in str(exc)
    else:
        raise AssertionError("Expected ProviderExecutionError")


def test_openai_provider_rejects_missing_output_text(tmp_path: Path) -> None:
    image_path = tmp_path / "pet.jpg"
    image_path.write_bytes(b"fake-image")

    class _EmptyResponses:
        def create(self, **kwargs: object) -> object:
            del kwargs
            return type("Response", (), {"output_text": ""})()

    class _EmptyClient:
        def __init__(self) -> None:
            self.responses = _EmptyResponses()

    provider = OpenAIProvider(client=_EmptyClient())

    try:
        provider.analyze_image(ImageInput(path=image_path), "Analyze")
    except ProviderOutputParseError as exc:
        assert "output_text" in str(exc)
    else:
        raise AssertionError("Expected ProviderOutputParseError")
