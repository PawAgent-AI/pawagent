from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from pawagent.core.images import load_provider_image_bytes


def test_load_provider_image_bytes_passthrough_for_jpeg(tmp_path: Path) -> None:
    path = tmp_path / "pet.jpg"
    Image.new("RGB", (4, 4), color=(255, 0, 0)).save(path, format="JPEG")

    image_bytes, mime_type = load_provider_image_bytes(path)

    assert mime_type == "image/jpeg"
    assert image_bytes == path.read_bytes()


def test_load_provider_image_bytes_converts_heic_to_jpeg(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "pet.heic"
    Image.new("RGB", (4, 4), color=(0, 255, 0)).save(path, format="JPEG")
    monkeypatch.setattr("pawagent.core.images._register_heif_opener", lambda: None)

    image_bytes, mime_type = load_provider_image_bytes(path)

    assert mime_type == "image/jpeg"
    assert image_bytes[:2] == b"\xff\xd8"


def test_load_provider_image_bytes_uses_sips_fallback_for_heic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "pet.heic"
    converted = tmp_path / "converted.jpg"
    Image.new("RGB", (4, 4), color=(0, 0, 255)).save(converted, format="JPEG")

    def _missing_register() -> None:
        raise ImportError("missing pillow-heif")

    monkeypatch.setattr("pawagent.core.images._register_heif_opener", _missing_register)
    monkeypatch.setattr("pawagent.core.images._convert_heif_with_sips", lambda _path: converted)

    image_bytes, mime_type = load_provider_image_bytes(path)

    assert mime_type == "image/jpeg"
    assert image_bytes[:2] == b"\xff\xd8"


def test_load_provider_image_bytes_reports_missing_heic_support(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "pet.heic"
    path.write_bytes(b"fake-heic")

    def _missing_register() -> None:
        raise ImportError("missing pillow-heif")

    def _missing_sips(_path: Path) -> Path:
        raise RuntimeError("sips unavailable")

    monkeypatch.setattr("pawagent.core.images._register_heif_opener", _missing_register)
    monkeypatch.setattr("pawagent.core.images._convert_heif_with_sips", _missing_sips)

    with pytest.raises(RuntimeError, match="HEIC/HEIF support requires pillow-heif or a working macOS `sips` fallback"):
        load_provider_image_bytes(path)
