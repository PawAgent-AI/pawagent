from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

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


class _FakeFiles:
    def __init__(self, states: list[str]) -> None:
        self._states = states
        self.uploaded: Path | None = None
        self.upload_config: dict[str, object] | None = None
        self.get_calls = 0
        self.last_name: str | None = None

    def upload(self, *, file: Path, config: dict[str, object] | None = None) -> object:
        self.uploaded = file
        self.upload_config = config
        return SimpleNamespace(name="files/test-video", state=SimpleNamespace(name=self._states[0]))

    def get(self, *, name: str) -> object:
        self.get_calls += 1
        self.last_name = name
        index = min(self.get_calls, len(self._states) - 1)
        return SimpleNamespace(name=name, state=SimpleNamespace(name=self._states[index]))


class _FakeVideoClient:
    def __init__(self, text: str, states: list[str]) -> None:
        self.models = _FakeGenerateModels(text)
        self.files = _FakeFiles(states)


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


def test_gemini_provider_requires_api_key_without_injected_client(monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    provider = GeminiProvider(api_key=None)

    try:
        provider._get_client()
    except ProviderAuthenticationError as exc:
        assert "GEMINI_API_KEY" in str(exc)
    else:
        raise AssertionError("Expected missing API key to raise ProviderAuthenticationError")


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


def test_gemini_provider_analyze_video_uploads_and_polls_until_active(monkeypatch, tmp_path: Path) -> None:
    video_path = tmp_path / "pet.mp4"
    video_path.write_bytes(b"fake-video")
    monkeypatch.setattr(gemini_provider_module, "_VIDEO_FILE_POLL_INTERVAL_SECONDS", 0)
    client = _FakeVideoClient(
        '{"emotion":{"label":"playful","confidence":0.9,"arousal":"high","tags":["engaged"],"alternatives":["excited"],"evidence":["fast repeated movement"],"uncertainty_note":"Short clip."},"behavior":{"label":"playing","confidence":0.88,"target":"human","intensity":"high","evidence":["fast repeated movement"],"alternatives":["running"],"uncertainty_note":"Short clip.","notes":"Sustained motion"},"motivation":{"label":"seeking engagement","confidence":0.8,"alternatives":["wants play"],"evidence":["fast repeated movement"],"uncertainty_note":"Target inferred."},"expression":{"plain_text":"The pet appears excited and is actively playing.","pet_voice":"I want to keep playing.","tone":"energetic","grounded_in":["fast repeated movement"],"confidence":0.79},"evidence":["fast repeated movement"]}',
        ["PROCESSING", "ACTIVE"],
    )
    provider = GeminiProvider(client=client)

    result = provider.analyze_video(str(video_path), "Analyze this pet video")

    assert result["emotion"]["label"] == "playful"
    assert client.files.uploaded == video_path
    assert client.files.last_name == "files/test-video"
    assert client.files.get_calls == 1
    assert client.files.upload_config == {"mime_type": "video/mp4"}
    request = client.models.last_request
    assert request is not None
    assert request["model"] == "gemini-2.5-flash"
    assert request["config"] == {"response_mime_type": "application/json"}
    uploaded_file = request["contents"][0]
    assert getattr(uploaded_file, "name", "") == "files/test-video"
    prompt = request["contents"][1]
    assert isinstance(prompt, str)
    assert "Analyze this pet video" in prompt


def test_gemini_provider_analyze_video_wraps_backend_failures(tmp_path: Path) -> None:
    video_path = tmp_path / "pet.mp4"
    video_path.write_bytes(b"fake-video")

    class _FailingFiles:
        def upload(self, *, file: Path, config: dict[str, object] | None = None) -> object:
            del file, config
            raise RuntimeError("boom")

    class _FailingClient:
        def __init__(self) -> None:
            self.files = _FailingFiles()
            self.models = _FakeGenerateModels("{}")

    provider = GeminiProvider(client=_FailingClient())

    try:
        provider.analyze_video(str(video_path), "Analyze")
    except ProviderExecutionError as exc:
        assert "Gemini video request failed" in str(exc)
    else:
        raise AssertionError("Expected ProviderExecutionError")


def test_gemini_provider_analyze_video_rejects_failed_processing_state(tmp_path: Path) -> None:
    video_path = tmp_path / "pet.mp4"
    video_path.write_bytes(b"fake-video")
    provider = GeminiProvider(client=_FakeVideoClient("{}", ["FAILED"]))

    try:
        provider.analyze_video(str(video_path), "Analyze")
    except ProviderExecutionError as exc:
        assert "state FAILED" in str(exc)
    else:
        raise AssertionError("Expected ProviderExecutionError")


def test_gemini_provider_analyze_video_rejects_missing_text_output(tmp_path: Path) -> None:
    video_path = tmp_path / "pet.mp4"
    video_path.write_bytes(b"fake-video")
    provider = GeminiProvider(client=_FakeVideoClient("", ["ACTIVE"]))

    try:
        provider.analyze_video(str(video_path), "Analyze")
    except ProviderOutputParseError as exc:
        assert "video response did not contain text output" in str(exc)
    else:
        raise AssertionError("Expected ProviderOutputParseError")
