
# PawAgent

**PawAgent** is an open‑source Python framework for building AI systems that understand pets.

It provides reusable AI capabilities such as:

- Pet emotion analysis
- Pet behavior interpretation
- Pet motivation prediction
- Pet expression rendering
- Pet identity enrollment and verification
- Pet image and short-video analysis

Supported image inputs include common formats such as `JPG`, `PNG`, `WEBP`, and `HEIC/HEIF`.
`HEIC/HEIF` files are decoded locally and normalized before provider upload or identity fingerprinting.
On macOS, PawAgent falls back to the system `sips` converter if `pillow-heif` is not installed.

PawAgent is designed as a **pure Python library**, not a web service.  
Runtime services, APIs, and deployment are implemented in a separate project (e.g. `pawagent-service`).

---

# Vision

Pets communicate through body posture, sounds, and behavior.  
PawAgent aims to provide a **Human–Pet Interface** powered by AI.

Pet Signals → PawAgent AI → Human Understanding

The framework enables developers to build applications that translate pet signals into meaningful insights.

---

# Core Principles

### 1. Library First
PawAgent is a **framework**, not a backend service.

### 2. Stateless AI Capabilities
Modules such as `vision` and `video` are **stateless capability layers**.

### 3. Clear Layer Separation

Task Views  
↓  
Unified Multimodal Analysis  
↓  
Capabilities (vision / video)  
↓  
Providers (model connectors)

Additional supporting layers:

Memory / Cache → source records and reusable analysis results  
Identity → pet cropping, visual fingerprinting, and pet-id verification  
Models → shared data schemas

### 4. Strong Data Schemas
All shared data structures use **Pydantic models**.

---

# Repository Structure

pawagent/
├─ README.md
├─ LICENSE
├─ pyproject.toml
├─ docs/
├─ tests/
├─ examples/
├─ cli/
└─ pawagent/
   ├─ core/
   ├─ models/
   ├─ providers/
   ├─ vision/
   ├─ audio/
   ├─ video/
   ├─ memory/
   ├─ personality/
   └─ agents/

---

# Architecture Layers

## Providers
Location: pawagent/providers/

Responsible for connecting PawAgent to external AI models.

Examples:
- OpenAI
- Gemini
- Anthropic
- Local models

Responsibilities:
- send inference requests
- normalize outputs
- abstract model APIs

Providers contain **no business logic**.

---

## Capability Modules

Locations:

vision/  
video/

Responsibilities:
- preprocess inputs
- call providers
- normalize modality-specific outputs into a shared semantic structure

Example output:

{
  "emotion": {...},
  "behavior": {...},
  "motivation": {...},
  "expression": {...},
  "evidence": [...]
}

Capabilities must be **stateless**.

---

## Models

Location:

pawagent/models/

Defines domain data structures using Pydantic.

Examples:

- Pet
- ImageInput
- MoodResult
- AnalysisResult
- PersonalityProfile

These models form the **shared data language** of PawAgent.

---

## Memory

Location:

pawagent/memory/

Responsibilities:

- store source analysis history
- cache unified analysis results by content hash
- reuse existing analysis for different task views
- persist long-term personality snapshots

Memory does not perform AI inference.

## Identity

Location: `pawagent/identity/`

Responsibilities:

- crop or segment the pet subject before identity comparison
- generate a reusable visual fingerprint embedding
- store per-pet reference profiles
- verify whether a new image likely matches an existing `pet-id`

Current implementation paths:

- fallback path: `noop cropper + hash embedder`
- intended production path: `maskrcnn cropper + openclip embedder`

Identity is a verification layer. It should be treated as probabilistic matching, not absolute recognition.
Enrollment is append-only: repeated `enroll-identity` calls for the same `pet-id` add reference views to the same profile.

---

## Agents

Location:

pawagent/agents/

Agents expose task-specific views over a shared analysis result.

Examples:

PetEmotionAgent  
PetBehaviorAgent  
PetMotivationAgent  
PetExpressionAgent

In the recommended architecture, a single analysis request produces the reusable result.
Task-specific agents then read from that result and return only the requested slice.

Example workflow:

image / video  
↓  
modality analyzer  
↓  
unified analysis result  
↓  
cache by content hash  
↓  
task-specific agent view  
↓  
result  

### Task Boundaries

- Emotion: current state from available evidence
- Behavior: current observable action or interaction tendency
- Motivation: second-layer prediction inferred from emotion, behavior, and context
- Expression: human-readable rendering grounded in the structured analysis

Recommended result layering:

- First layer: `emotion`, `behavior`
- Second layer: `motivation`
- Expression layer: `expression`

---

# CLI

Example command:

pawagent analyze-emotion dog.jpg

Short-video example:

pawagent analyze-behavior clip.mp4 --modality video

Example output:

Emotion: playful  
Confidence: 0.87

Recommended architecture note:

- A single call should produce a unified result for the content hash.
- Repeated requests for emotion, behavior, motivation, or expression should read from cache.
- Expression for the same content should be stable, not regenerated differently on every request.
- Localized expression can be rendered from the structured result with a lightweight second pass and cached by content hash plus locale.
- Identity verification uses a separate profile store and does not reuse emotion/behavior memory as an identity source of truth.
- Current product focus is image and short-video analysis. Audio remains an internal extension path and is not a primary user-facing workflow.

OpenAI provider example:

export OPENAI_API_KEY=your_api_key
.venv/bin/python -m cli.main --provider openai --openai-model gpt-4.1-mini analyze-emotion dog.jpg --pet-id pet-1 --pet-name Milo

Note:
OpenAI Platform API uses API key authentication for server-side model calls. OAuth in OpenAI official docs applies to GPT Actions / connector-style user sign-in flows, not this library integration.

Experimental Codex OAuth-backed provider example:

codex login
.venv/bin/python -m cli.main --provider codex --codex-model gpt-5.4 analyze-emotion dog.jpg --pet-id pet-1 --pet-name Milo

This provider does not call the public OpenAI Platform API directly.
It shells out to the locally installed `codex` CLI and reuses its existing ChatGPT/Codex login state.

Gemini provider example:

export GEMINI_API_KEY=your_api_key
.venv/bin/python -m cli.main --provider gemini --gemini-model gemini-2.5-flash analyze-emotion dog.jpg --pet-id pet-1 --pet-name Milo

Experimental Gemini CLI provider example:

gemini
.venv/bin/python -m cli.main --provider gemini-cli --gemini-model gemini-2.5-flash analyze-emotion dog.jpg --pet-id pet-1 --pet-name Milo

Localized expression example:

.venv/bin/python -m cli.main express-pet dog.jpg --pet-id pet-1 --pet-name Milo --locale zh-CN

Video task-view example:

.venv/bin/python -m cli.main analyze-motivation clip.mp4 --pet-id pet-1 --pet-name Milo --modality video

The localized expression result is cached separately in `.pawagent/expression_records.json` by content hash, analysis version, locale, and style.

Identity enrollment example:

.venv/bin/python -m cli.main enroll-identity tests/coconut.jpg --pet-id pet-1

Identity verification example:

.venv/bin/python -m cli.main verify-identity tests/coconut.jpg --pet-id pet-1

HEIC example:

.venv/bin/python -m cli.main analyze-emotion tests/coconut.heic --pet-id pet-1 --pet-name Coconut
.venv/bin/python -m cli.main enroll-identity tests/coconut.heic --pet-id pet-1 --identity-cropper maskrcnn --identity-embedder openclip

Identity CLI defaults to the no-extra-dependency fallback path:

- cropper: `noop`
- embedder: `hash`

To use the intended visual fingerprint pipeline, install the optional identity dependencies and switch to:

- `--identity-cropper maskrcnn`
- `--identity-embedder openclip`

Real local identity pipeline notes:

- the first `openclip` run may download model files into `.pawagent/hf-cache` and `.pawagent/torch-cache`
- a Hugging Face unauthenticated-request warning is expected on first download and does not mean verification failed
- `HF_TOKEN` is optional for public model downloads; it only improves rate limits and download reliability
- verification compares against all enrolled references for the target `pet-id`

---

# Example Usage

from pathlib import Path

from pawagent.agents.mood_agent import PetMoodAgent
from pawagent.memory.store import InMemoryAnalysisStore
from pawagent.personality.profiler import PersonalityProfiler
from pawagent.providers.mock_provider import MockProvider

memory = InMemoryAnalysisStore()
agent = PetMoodAgent(
    provider=MockProvider(),
    memory_store=memory,
    profiler=PersonalityProfiler(memory),
)

result = agent.analyze_image(
    image_path=Path("dog.jpg"),
    pet_id="pet-1",
    pet_name="Milo",
    species="dog",
)

print(result.mood.primary)

---

# Installation

pip install pawagent

For development:

pip install -e .

For identity features with real local visual fingerprinting:

pip install -e ".[identity]"

---

# Ecosystem

PawAgent is designed to power higher-level systems such as:

- pawagent-service (runtime service layer)
- Paworld (consumer application)

Architecture example:

Paworld App  
↓  
pawagent-service  
↓  
PawAgent library  
↓  
AI Providers  

---

# Contributing

Contributions are welcome.

Suggested areas:

- vision models
- audio analysis
- behavior understanding
- personality modeling
- documentation
- benchmarks

---

# License

MIT License
