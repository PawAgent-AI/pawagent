from __future__ import annotations

import io
import mimetypes
import subprocess
import tempfile
from pathlib import Path


HEIF_SUFFIXES = {".heic", ".heif"}


def is_heif_path(path: Path) -> bool:
    return path.suffix.lower() in HEIF_SUFFIXES


def _register_heif_opener() -> None:
    from pillow_heif import register_heif_opener

    register_heif_opener()


def _convert_heif_with_sips(path: Path) -> Path:
    temp_dir = Path(tempfile.mkdtemp(prefix="pawagent-heif-"))
    converted_path = temp_dir / f"{path.stem}.jpg"
    result = subprocess.run(
        ["sips", "-s", "format", "jpeg", str(path), "--out", str(converted_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "unknown sips error"
        raise RuntimeError(f"Failed to convert HEIC/HEIF image with sips: {message}")
    return converted_path


def open_image(path: Path):
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Pillow is required for local image decoding.") from exc

    if is_heif_path(path):
        try:
            _register_heif_opener()
        except ImportError:
            try:
                return Image.open(_convert_heif_with_sips(path))
            except Exception as fallback_exc:
                raise RuntimeError(
                    "HEIC/HEIF support requires pillow-heif or a working macOS `sips` fallback."
                ) from fallback_exc

    return Image.open(path)


def load_provider_image_bytes(path: Path) -> tuple[bytes, str]:
    if not is_heif_path(path):
        mime_type = mimetypes.guess_type(path.name)[0] or "image/jpeg"
        return path.read_bytes(), mime_type

    with open_image(path) as image:
        rgb = image.convert("RGB")
        buffer = io.BytesIO()
        rgb.save(buffer, format="JPEG", quality=95)
        return buffer.getvalue(), "image/jpeg"
