from __future__ import annotations

import math
import subprocess
import tempfile
from pathlib import Path

from pawagent.models.media import ImageInput

DEFAULT_VIDEO_FRAME_COUNT = 4
DEFAULT_VIDEO_TILE_COLUMNS = 2
DEFAULT_VIDEO_FRAME_WIDTH = 512


def prepare_video_storyboard(
    video_path: Path,
    *,
    frame_count: int = DEFAULT_VIDEO_FRAME_COUNT,
    columns: int = DEFAULT_VIDEO_TILE_COLUMNS,
    frame_width: int = DEFAULT_VIDEO_FRAME_WIDTH,
) -> ImageInput:
    temp_dir = Path(tempfile.mkdtemp(prefix="pawagent-video-frames-"))
    frame_paths = _extract_video_frames(
        video_path=video_path,
        output_dir=temp_dir,
        frame_count=frame_count,
        frame_width=frame_width,
    )
    storyboard_path = temp_dir / f"{video_path.stem}_storyboard.jpg"
    _build_storyboard_image(frame_paths=frame_paths, output_path=storyboard_path, columns=columns)
    return ImageInput(path=storyboard_path, mime_type="image/jpeg")


def build_storyboard_prompt(prompt: str, *, frame_count: int = DEFAULT_VIDEO_FRAME_COUNT) -> str:
    return (
        f"{prompt}\n\n"
        "The attached image is a storyboard generated from a video clip.\n"
        f"It contains {frame_count} frames sampled in chronological order from left to right, top to bottom.\n"
        "Infer behavior and emotion from changes across frames rather than treating it as a single still photo.\n"
        "If the storyboard limits certainty about motion timing, mention that uncertainty explicitly."
    )


def _extract_video_frames(
    *,
    video_path: Path,
    output_dir: Path,
    frame_count: int,
    frame_width: int,
) -> list[Path]:
    duration = _probe_video_duration(video_path)
    timestamps = _sample_timestamps(duration=duration, frame_count=frame_count)
    frame_paths: list[Path] = []
    for index, timestamp in enumerate(timestamps, start=1):
        frame_path = output_dir / f"frame_{index:02d}.jpg"
        result = subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-ss",
                f"{timestamp:.3f}",
                "-i",
                str(video_path),
                "-frames:v",
                "1",
                "-vf",
                f"scale={frame_width}:-1:force_original_aspect_ratio=decrease",
                str(frame_path),
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0 or not frame_path.exists():
            message = result.stderr.strip() or result.stdout.strip() or "unknown ffmpeg error"
            raise RuntimeError(f"Failed to extract video frame {index} from {video_path}: {message}")
        frame_paths.append(frame_path)
    return frame_paths


def _probe_video_duration(video_path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "unknown ffprobe error"
        raise RuntimeError(f"Failed to inspect video duration for {video_path}: {message}")
    try:
        duration = float(result.stdout.strip())
    except ValueError as exc:
        raise RuntimeError(f"Video duration is not a valid number for {video_path}.") from exc
    if duration <= 0:
        raise RuntimeError(f"Video duration must be positive for {video_path}.")
    return duration


def _sample_timestamps(*, duration: float, frame_count: int) -> list[float]:
    interval = duration / (frame_count + 1)
    timestamps = [interval * index for index in range(1, frame_count + 1)]
    max_timestamp = max(duration - 0.05, 0.0)
    return [min(timestamp, max_timestamp) for timestamp in timestamps]


def _build_storyboard_image(*, frame_paths: list[Path], output_path: Path, columns: int) -> None:
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("Pillow is required for video storyboard generation.") from exc

    opened_frames = []
    for path in frame_paths:
        with Image.open(path) as image:
            opened_frames.append(image.convert("RGB"))
    try:
        cell_width = max(frame.width for frame in opened_frames)
        cell_height = max(frame.height for frame in opened_frames)
        rows = math.ceil(len(opened_frames) / columns)
        canvas = Image.new("RGB", (cell_width * columns, cell_height * rows), color=(255, 255, 255))
        for index, frame in enumerate(opened_frames):
            x = (index % columns) * cell_width
            y = (index // columns) * cell_height
            canvas.paste(frame, (x, y))
        canvas.save(output_path, format="JPEG", quality=90)
    finally:
        for frame in opened_frames:
            frame.close()
