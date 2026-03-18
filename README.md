# PawAgent

PawAgent is a Python framework for pet understanding from images and short videos.

It provides a reusable analysis stack for:

- Emotion analysis
- Behavior analysis
- Motivation prediction
- Expression rendering
- Pet identity enrollment and verification

PawAgent is a library, not a web service. It is intended to sit underneath a separate runtime or application layer.

## Status

- Core media analysis: implemented
- Image and short-video task views: implemented
- Gemini API video analysis: implemented natively
- OpenAI / Claude / CLI providers video analysis: implemented via local storyboard fallback
- Identity verification: implemented
- Real local identity path (`maskrcnn + openclip`): implemented
- Audio: internal extension path, not a primary user-facing workflow
- Live streaming: out of scope for the current product surface

## Why This Project

Most pet-AI demos collapse everything into one opaque caption. PawAgent instead separates:

- direct observations
- second-layer inference
- human-readable rendering

That makes the results easier to cache, explain, reuse, and evaluate.

## Core Model

One image or short video produces one unified analysis result:

```json
{
  "emotion": {},
  "behavior": {},
  "motivation": {},
  "expression": {},
  "evidence": []
}
```

Task-specific agents then read from that shared result instead of re-calling the model.

Result layering:

- First layer: `emotion`, `behavior`
- Second layer: `motivation`
- Expression layer: `expression`

## Feature Matrix

| Capability | Image | Short Video | Notes |
| --- | --- | --- | --- |
| Emotion | Yes | Yes | First-layer structured result |
| Behavior | Yes | Yes | Video usually gives stronger behavior cues |
| Motivation | Yes | Yes | Second-layer inference from emotion + behavior |
| Expression | Yes | Yes | Stable rendering over structured analysis |
| Identity | Yes | No | Separate verification pipeline |
| Audio | Internal | Internal | Not a primary user-facing workflow |

## Quick Start

Install from PyPI:

```bash
pip install pawagent
```

Install from source for development:

```bash
pip install -e .
```

Run the mock provider:

```bash
pawagent analyze-emotion dog.jpg --pet-id pet-1 --pet-name Milo
pawagent analyze-behavior clip.mp4 --pet-id pet-1 --pet-name Milo --modality video
pawagent express-pet dog.jpg --pet-id pet-1 --pet-name Milo --locale zh-CN
```

Install identity extras:

```bash
pip install -e ".[identity]"
```

Run real local identity verification:

```bash
pawagent enroll-identity tests/coconut.jpg --pet-id pet-1 --identity-cropper maskrcnn --identity-embedder openclip
pawagent verify-identity tests/coconut.jpg --pet-id pet-1 --identity-cropper maskrcnn --identity-embedder openclip
```

## CLI Overview

Task-view commands:

```bash
pawagent analyze-emotion <source> --modality image|video
pawagent analyze-behavior <source> --modality image|video
pawagent analyze-motivation <source> --modality image|video
pawagent express-pet <source> --modality image|video
```

Identity commands:

```bash
pawagent enroll-identity <source> --pet-id <pet-id>
pawagent verify-identity <source> --pet-id <pet-id>
```

### Example Commands

Image emotion:

```bash
pawagent analyze-emotion dog.jpg --pet-id pet-1 --pet-name Milo
```

Short-video behavior:

```bash
pawagent analyze-behavior clip.mp4 --pet-id pet-1 --pet-name Milo --modality video
```

Localized expression:

```bash
pawagent express-pet dog.jpg --pet-id pet-1 --pet-name Milo --locale zh-CN
```

HEIC input:

```bash
pawagent analyze-emotion tests/coconut.heic --pet-id pet-1 --pet-name Coconut
```

## Image Formats

Supported image inputs include:

- `JPG`
- `PNG`
- `WEBP`
- `HEIC`
- `HEIF`

`HEIC/HEIF` inputs are decoded locally before provider upload or identity fingerprinting.

On macOS, PawAgent can fall back to the system `sips` converter when `pillow-heif` is unavailable.

## Providers

Built-in provider options:

- `mock`
- `openai`
- `gemini`
- `gemini-cli`
- `codex`
- `claude`
- `claude-cli`

Video support notes:

- `gemini`: native video upload and analysis
- `openai`, `claude`, `codex`, `gemini-cli`, `claude-cli`: local `ffmpeg` storyboard fallback, then image analysis
- storyboard fallback requires local `ffmpeg` and `ffprobe`

### OpenAI

```bash
export OPENAI_API_KEY=your_api_key
pawagent --provider openai --openai-model gpt-4.1-mini analyze-emotion dog.jpg --pet-id pet-1 --pet-name Milo
```

OpenAI Platform API integration uses API keys for server-side model calls.
Video input is handled through the local storyboard fallback rather than a native OpenAI video understanding API.

### Gemini

```bash
export GEMINI_API_KEY=your_api_key
pawagent --provider gemini --gemini-model gemini-2.5-flash analyze-emotion dog.jpg --pet-id pet-1 --pet-name Milo
pawagent --provider gemini --gemini-model gemini-2.5-flash analyze-behavior clip.mp4 --pet-id pet-1 --pet-name Milo --modality video
```

Gemini uses native video upload for `--modality video`.

### Claude

```bash
export ANTHROPIC_API_KEY=your_api_key
pawagent --provider claude --claude-model claude-sonnet-4-6 analyze-emotion dog.jpg --pet-id pet-1 --pet-name Milo
```

Anthropic Claude API integration uses API keys for server-side model calls. Claude's strong vision capabilities make it well-suited for pet image analysis.
Video input is handled through the local storyboard fallback.

### Claude CLI

```bash
claude
pawagent --provider claude-cli --claude-model claude-sonnet-4-6 analyze-emotion dog.jpg --pet-id pet-1 --pet-name Milo
```

This provider shells out to the local `claude` CLI (Claude Code) and reuses its existing login state.
Video input is handled through the local storyboard fallback.

### Codex CLI

```bash
codex login
pawagent --provider codex --codex-model gpt-5.4 analyze-emotion dog.jpg --pet-id pet-1 --pet-name Milo
```

This provider shells out to the local `codex` CLI and reuses its existing login state.
Video input is handled through the local storyboard fallback.

### Gemini CLI

```bash
gemini
pawagent --provider gemini-cli --gemini-model gemini-2.5-flash analyze-emotion dog.jpg --pet-id pet-1 --pet-name Milo
```

Video input is handled through the local storyboard fallback.

## Identity

Identity is separate from emotion and behavior analysis. It uses its own profile store and should be treated as probabilistic verification, not biometric certainty.

Implementation paths:

- Fallback path: `noop` cropper + `hash` embedder
- Intended local path: `maskrcnn` cropper + `openclip` embedder

Identity enrollment is append-only. Repeated `enroll-identity` calls for the same `pet-id` add new reference views instead of overwriting the profile.

### Real Local Identity Notes

- the first `openclip` run may download files into `.pawagent/hf-cache` and `.pawagent/torch-cache`
- a Hugging Face unauthenticated-request warning during first download is expected
- `HF_TOKEN` is optional for public models and only improves download rate limits
- verification compares against all enrolled references for the target `pet-id`

## Architecture

```text
Task Views
  -> Unified Analysis
  -> Capability Layer (vision / video)
  -> Provider Layer

Supporting layers:
  - Memory / cache
  - Identity
  - Shared models
```

Key design rules:

- one source item should map to one unified analysis result
- repeated task-view requests should reuse cached analysis
- localized expression may use a lightweight second pass and is cached separately
- identity should never reuse emotion/behavior memory as its source of truth

## Repository Layout

```text
pawagent/
├── cli/
├── docs/
├── examples/
├── pawagent/
│   ├── agents/
│   ├── core/
│   ├── expression/
│   ├── identity/
│   ├── memory/
│   ├── models/
│   ├── personality/
│   ├── providers/
│   ├── video/
│   └── vision/
├── tests/
└── pyproject.toml
```

## Library Example

```python
from pathlib import Path

from pawagent.agents.mood_agent import PetEmotionAgent
from pawagent.memory.store import InMemoryAnalysisStore
from pawagent.personality.profiler import PersonalityProfiler
from pawagent.providers.mock_provider import MockProvider

memory = InMemoryAnalysisStore()
agent = PetEmotionAgent(
    provider=MockProvider(),
    memory_store=memory,
    profiler=PersonalityProfiler(memory),
)

result = agent.analyze_image(
    image_path=Path("dog.jpg"),
    pet_id="pet-1",
    pet_name="Milo",
    species="unknown",
)

print(result.mood.primary)
```

## Documentation

- [Architecture](docs/architecture.md)
- [Concepts](docs/concepts.md)
- [Specification](docs/spec.md)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions, code style guidelines, and how to submit pull requests.

Useful contribution areas:

- vision and video analysis
- behavior and motivation quality
- identity verification quality
- provider integrations
- documentation and benchmarks

## License

MIT License. See [LICENSE](LICENSE).
