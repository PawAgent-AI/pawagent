# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install in development mode
pip install -e .
pip install -e ".[identity]"   # includes MaskRCNN-based pet cropping

# Run tests
pytest
pytest tests/test_behavior_agent.py                                            # single file
pytest tests/test_behavior_agent.py::test_behavior_agent_infers_behavior_...  # single test
pytest -v --log-cli-level=DEBUG tests/test_behavior_agent.py                  # verbose with logs

# Type checking
mypy pawagent
```

## Architecture

PawAgent is a Python library for pet understanding from images and videos. It is not a web service — it's designed to sit underneath an application layer. The core flow:

```
Input (image/video)
  → UnifiedMediaAnalysisService   (caches by content hash; dispatches to VisionAnalyzer or VideoAnalyzer)
    → Provider                    (OpenAI, Gemini, Claude, Codex, Mock — stateless connectors)
  → UnifiedAnalysisResult         (single canonical result with emotion, behavior, motivation, expression)
  → Task-Specific Agent           (PetEmotionAgent, PetBehaviorAgent, etc. extract their view)
```

**Key insight — unified analysis**: One input produces one cached `UnifiedAnalysisResult`. All agents share this result rather than each making their own model call. Cache key: `(SHA256(file_content), analysis_version, prompt_version)`.

### Package layout

| Package | Role |
|---|---|
| `pawagent/agents/` | Task agents (emotion, behavior, motivation, expression, personality) |
| `pawagent/core/` | `UnifiedMediaAnalysisService`, content hashing, image utilities |
| `pawagent/providers/` | `BaseProvider` protocol + implementations (mock, openai, gemini, claude, codex) |
| `pawagent/vision/` | `VisionAnalyzer`, image preprocessing, prompt templates |
| `pawagent/video/` | `VideoAnalyzer`, video preprocessing |
| `pawagent/models/` | Pydantic data models (Mood, Behavior, Motivation, Expression, Pet, etc.) |
| `pawagent/memory/` | `AnalysisStore` protocol, `InMemoryAnalysisStore`, `JsonAnalysisStore`, summarizer |
| `pawagent/identity/` | Pet cropping, fingerprint embedding, verification, enrollment |
| `pawagent/expression/` | Localized expression rendering and caching |
| `pawagent/personality/` | Personality profiler, trait store, updater |
| `cli/` | CLI entry point (`pawagent` command) |

### Key data models

- **`UnifiedAnalysisResult`**: Central result — `emotion`, `behavior`, `motivation`, `expression`, `evidence`, `species`
- **`AnalysisRecord`**: Extends `UnifiedAnalysisResult` with cache metadata (`content_hash`, `analysis_version`, `prompt_version`), provider info, source path, and `pet_id`
- All agents accept `(provider, memory_store, profiler)` in `__init__` and delegate to `UnifiedMediaAnalysisService`

### Provider abstraction

`BaseProvider` defines `analyze_image()`, `analyze_video()`, `render_expression()`. Providers are stateless. `MockProvider` returns deterministic results without API keys — use it in all tests.

### Memory

`AnalysisStore` is a protocol with two implementations:
- `InMemoryAnalysisStore` — ephemeral, used in tests
- `JsonAnalysisStore` — persistent on disk

### Identity (optional extra)

Pet identity (enrollment + verification) uses a cropper + embedder pipeline. `NoOpCropper` + `HashEmbedder` are the defaults; `MaskRCNNCropper` + `OpenClipEmbedder` require `pip install -e ".[identity]"`.

## Testing conventions

Tests use `MockProvider` and `InMemoryAnalysisStore` — no API keys or network needed. The standard pattern:

```python
store = InMemoryAnalysisStore()
store.add_record(AnalysisRecord(...))   # seed history if needed
profiler = PersonalityProfiler(store)
agent = PetBehaviorAgent(provider=MockProvider(), memory_store=store, profiler=profiler)
result = agent.analyze_image(image_path=Path("..."), pet_id="...", ...)
```
