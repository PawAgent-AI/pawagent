from __future__ import annotations

from pathlib import Path

from pawagent.models.media import ImageInput
from pawagent.providers.errors import (
    ProviderAuthenticationError,
    ProviderExecutionError,
    ProviderOutputParseError,
)
from pawagent.providers import gemini_provider as gemini_provider_module
from pawagent.providers.gemini_provider import GeminiProvider


class _FakeGenerateModels:
    def __init__(self, text: str) -> None:
        self._text = text
        self.last_request: dict[str, object] | None = None

    def generate_content(self, **kwargs: object) -> object:
        self.last_request = kwargs
        return type("Response", (), {"text": self._text})()


class _FakeGeminiClient:
    def __init__(self, text: str) -> None:
        self.models = _FakeGenerateModels(text)

    def make_part_from_bytes(self, data: bytes, mime_type: str) -> dict[str, object]:
        return {"data": data, "mime_type": mime_type}


def test_gemini_provider_normalizes_response_and_builds_request(tmp_path: Path) -> None:
    image_path = tmp_path / "pet.jpg"
    image_path.write_bytes(b"fake-image")
    client = _FakeGeminiClient(
        '{"emotion":{"label":"alert","confidence":0.84,"arousal":"medium","tags":["focused"],"alternatives":["curious"],"evidence":["ears forward"],"uncertainty_note":"Could also be curiosity."},"behavior":{"label":"monitoring surroundings","confidence":0.81,"target":"environment","intensity":"moderate","evidence":["ears forward"],"alternatives":["observing"],"uncertainty_note":"Short clip limits duration certainty.","notes":"Ears forward"},"motivation":{"label":"monitoring for change","confidence":0.62,"alternatives":["checking environment"],"evidence":["ears forward"],"uncertainty_note":"Trigger not visible."},"expression":{"plain_text":"The pet appears alert and is monitoring the surroundings.","pet_voice":"I am watching everything carefully right now.","tone":"watchful","grounded_in":["ears forward"],"confidence":0.74},"evidence":["ears forward"]}'
    )
    provider = GeminiProvider(client=client)

    result = provider.analyze_image(ImageInput(path=image_path), "Analyze this pet image")

    assert result["emotion"]["label"] == "alert"
    assert result["emotion"]["arousal"] == "medium"
    assert result["behavior"]["label"] == "monitoring surroundings"
    request = client.models.last_request
    assert request is not None
    assert request["model"] == "gemini-2.5-flash"
    assert request["config"] == {"response_mime_type": "application/json"}
    image_part = request["contents"][1]
    if isinstance(image_part, dict):
        assert image_part["mime_type"] == "image/jpeg"
    else:
        assert image_part.inline_data.mime_type == "image/jpeg"


def test_gemini_provider_requires_api_key_or_vertexai_without_injected_client(monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_LOCATION", raising=False)
    provider = GeminiProvider(api_key=None)

    try:
        provider._get_client()
    except ProviderAuthenticationError as exc:
        assert "API key" in str(exc)
        assert "Vertex AI" in str(exc)
    else:
        raise AssertionError("Expected missing credentials to raise ProviderAuthenticationError")


def test_gemini_provider_wraps_backend_failures(tmp_path: Path) -> None:
    image_path = tmp_path / "pet.jpg"
    image_path.write_bytes(b"fake-image")

    class _FailingModels:
        def generate_content(self, **kwargs: object) -> object:
            del kwargs
            raise RuntimeError("boom")

    class _FailingClient:
        def __init__(self) -> None:
            self.models = _FailingModels()

    provider = GeminiProvider(client=_FailingClient())

    try:
        provider.analyze_image(ImageInput(path=image_path), "Analyze")
    except ProviderExecutionError as exc:
        assert "Gemini request failed" in str(exc)
    else:
        raise AssertionError("Expected ProviderExecutionError")


def test_gemini_provider_rejects_missing_text_output(tmp_path: Path) -> None:
    image_path = tmp_path / "pet.jpg"
    image_path.write_bytes(b"fake-image")

    class _EmptyModels:
        def generate_content(self, **kwargs: object) -> object:
            del kwargs
            return type("Response", (), {"text": ""})()

    class _EmptyClient:
        def __init__(self) -> None:
            self.models = _EmptyModels()

    provider = GeminiProvider(client=_EmptyClient())

    try:
        provider.analyze_image(ImageInput(path=image_path), "Analyze")
    except ProviderOutputParseError as exc:
        assert "text output" in str(exc)
    else:
        raise AssertionError("Expected ProviderOutputParseError")


def test_gemini_provider_analyze_video_uses_storyboard_fallback(monkeypatch, tmp_path: Path) -> None:
    storyboard_path = tmp_path / "storyboard.jpg"
    storyboard_path.write_bytes(b"fake-storyboard")
    client = _FakeGeminiClient(
        '{"emotion":{"label":"playful","confidence":0.9,"arousal":"high","tags":["engaged"],"alternatives":["excited"],"evidence":["fast repeated movement"],"uncertainty_note":"Short clip."},"behavior":{"label":"playing","confidence":0.88,"target":"human","intensity":"high","evidence":["fast repeated movement"],"alternatives":["running"],"uncertainty_note":"Short clip.","notes":"Sustained motion"},"motivation":{"label":"seeking engagement","confidence":0.8,"alternatives":["wants play"],"evidence":["fast repeated movement"],"uncertainty_note":"Target inferred."},"expression":{"plain_text":"The pet appears excited and is actively playing.","pet_voice":"I want to keep playing.","tone":"energetic","grounded_in":["fast repeated movement"],"confidence":0.79},"evidence":["fast repeated movement"]}',
    )

    captured: dict[str, Path] = {}

    def fake_prepare(video_path: Path) -> ImageInput:
        captured["video_path"] = video_path
        return ImageInput(path=storyboard_path)

    monkeypatch.setattr(
        gemini_provider_module.video_preprocess,
        "prepare_video_storyboard",
        fake_prepare,
    )
    provider = GeminiProvider(client=client)

    result = provider.analyze_video(str(tmp_path / "pet.mp4"), "Analyze this pet video")

    assert result["emotion"]["label"] == "playful"
    assert captured["video_path"] == tmp_path / "pet.mp4"
    request = client.models.last_request
    assert request is not None
    assert request["model"] == "gemini-2.5-flash"
    assert request["config"] == {"response_mime_type": "application/json"}
    prompt = request["contents"][0]
    assert isinstance(prompt, str)
    assert "Analyze this pet video" in prompt
    assert "storyboard generated from a video clip" in prompt
    image_part = request["contents"][1]
    if isinstance(image_part, dict):
        assert image_part["data"] == b"fake-storyboard"
        assert image_part["mime_type"] == "image/jpeg"
    else:
        assert image_part.inline_data.mime_type == "image/jpeg"


def test_gemini_provider_analyze_video_wraps_preprocessing_failures(monkeypatch, tmp_path: Path) -> None:
    def failing_prepare(video_path: Path) -> ImageInput:
        del video_path
        raise RuntimeError("boom")

    monkeypatch.setattr(
        gemini_provider_module.video_preprocess,
        "prepare_video_storyboard",
        failing_prepare,
    )
    provider = GeminiProvider(client=_FakeGeminiClient("{}"))

    try:
        provider.analyze_video(str(tmp_path / "pet.mp4"), "Analyze")
    except ProviderExecutionError as exc:
        assert "Gemini video preprocessing failed" in str(exc)
    else:
        raise AssertionError("Expected ProviderExecutionError")


def test_gemini_provider_vertexai_flag_from_project() -> None:
    provider = GeminiProvider(project="my-project")
    assert provider._vertexai is True
    assert provider._project == "my-project"


def test_gemini_provider_vertexai_creates_client_with_project_and_location(monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_LOCATION", raising=False)

    captured: dict[str, object] = {}
    original_client = None

    from google import genai as real_genai

    original_client = real_genai.Client

    class _CapturingClient:
        def __init__(self, **kwargs: object) -> None:
            captured.update(kwargs)

    monkeypatch.setattr(real_genai, "Client", _CapturingClient)

    provider = GeminiProvider(vertexai=True, project="proj-1", location="us-central1")
    provider._get_client()

    assert captured["vertexai"] is True
    assert captured["project"] == "proj-1"
    assert captured["location"] == "us-central1"


def test_gemini_provider_vertexai_env_vars(monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "env-project")
    monkeypatch.setenv("GOOGLE_CLOUD_LOCATION", "asia-east1")

    provider = GeminiProvider(vertexai=True)
    assert provider._project == "env-project"
    assert provider._location == "asia-east1"
