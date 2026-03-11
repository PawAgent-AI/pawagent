
# PawAgent Development Specification

This document defines the architecture and implementation plan for PawAgent.

PawAgent is an open-source Pet AI Agent framework implemented as a Python library.
It provides reusable AI capabilities for applications that aim to understand pets.

Examples:
- pet emotion detection
- pet behavior interpretation
- pet motivation prediction
- pet expression rendering
- pet identity enrollment and verification
- pet image and short-video analysis

Supported image inputs should include common formats such as JPG, PNG, WEBP, and HEIC/HEIF.
HEIC/HEIF inputs should be decoded locally before provider upload or identity fingerprinting.
On macOS, the implementation may fall back to the system `sips` converter when a native HEIF decoder is unavailable.

PawAgent is designed as a pure Python library, not a web service.
HTTP APIs and runtime deployment will be implemented in a separate project (pawagent-service).

--------------------------------------------------
1. DESIGN PRINCIPLES
--------------------------------------------------

1. Library First
PawAgent is a Python library, not a backend service.

2. Stateless Capability Modules
Vision/video modules should be stateless.

3. Separation of Layers
Layers:
- Providers (model connectors)
- Capabilities (vision/video)
- Identity (cropping, fingerprinting, verification)
- Unified Analysis (cross-modality semantic result)
- Task Agents / Views (emotion / behavior / motivation / expression)
- Memory / Cache (context retrieval and reusable analysis results)

4. Strong Data Schemas
All data must use Pydantic models.

5. Service Agnostic
The library must NOT include:
- FastAPI
- HTTP routes
- middleware
- authentication

--------------------------------------------------
2. REPOSITORY STRUCTURE
--------------------------------------------------

pawagent/
│
├── README.md
├── LICENSE
├── pyproject.toml
│
├── docs/
│   ├── architecture.md
│   └── concepts.md
│
├── tests/
│
├── examples/
│   ├── mood_detection_demo
│   └── personality_demo
│
├── cli/
│   └── main.py
│
└── pawagent/
    ├── __init__.py
    │
    ├── core/
    │   ├── agent.py
    │   ├── orchestrator.py
    │   └── workflow.py
    │
    ├── models/
    │   ├── pet.py
    │   ├── media.py
    │   ├── mood.py
    │   ├── behavior.py
    │   ├── analysis.py
    │   └── personality.py
    │
    ├── providers/
    │   ├── base.py
    │   ├── openai_provider.py
    │   ├── gemini_provider.py
    │   └── mock_provider.py
    │
    ├── vision/
    │   ├── analyzer.py
    │   ├── preprocess.py
    │   └── prompts.py
    │
    ├── audio/
    │   ├── analyzer.py
    │   └── preprocess.py
    │
    ├── video/
    │   └── analyzer.py
    │
    ├── memory/
    │   ├── store.py
    │   ├── history.py
    │   ├── context_builder.py
    │   └── summarizer.py
    │
    ├── personality/
    │   ├── profiler.py
    │   ├── traits.py
    │   └── updater.py
    │
    ├── expression/
    │   └── store.py
    │
    ├── identity/
    │   ├── cropper.py
    │   ├── embedder.py
    │   ├── service.py
    │   └── store.py
    │
    └── agents/
        ├── mood_agent.py
        ├── behavior_agent.py
        ├── motivation_agent.py
        ├── personality_agent.py
        └── expression_agent.py

--------------------------------------------------
3. LAYER RESPONSIBILITIES
--------------------------------------------------

Providers
Location:
pawagent/providers/

Responsibilities:
- connect to external AI models
- normalize inference APIs

Examples:
analyze_image()
generate_text()

Providers must not contain business logic.

--------------------------------------------------

Capability Modules
Locations:
vision/
video/

Responsibilities:
- preprocess inputs
- call providers
- normalize outputs into a shared semantic schema

Example output:

{
 "emotion": {...},
 "behavior": {...},
 "motivation": {...},
 "expression": {...},
 "evidence": [...]
}

These modules must be stateless.

--------------------------------------------------

Identity
Location:
pawagent/identity/

Responsibilities:
- crop or segment the pet subject
- generate a reusable visual fingerprint embedding
- persist identity reference profiles by `pet-id`
- verify whether a new image likely matches an enrolled pet

Recommended production path:
- mask segmentation / cropping
- OpenCLIP embedding

Fallback path:
- no-op cropper
- deterministic hash embedder

Identity should be treated as verification, not guaranteed biometric recognition.
Identity enrollment should append new reference views to the existing `pet-id` profile instead of overwriting it.
Real `openclip` usage may trigger a first-run public model download. `HF_TOKEN` is optional and only affects download limits and speed.

--------------------------------------------------

Unified Analysis
Location:
pawagent/models/

The core inference path should produce one reusable analysis result per source item.

This result should:
- be cacheable by content hash
- include provider, model, and prompt version metadata
- contain reusable slices for emotion, behavior, motivation, and expression
- be stable enough for multiple task views to consume without re-calling the model

Example fields:
- source hash
- modality
- emotion
- behavior
- motivation
- expression
- evidence
- provider metadata

--------------------------------------------------

Models
Location:
pawagent/models/

Defines domain schemas using Pydantic.

Example:

class MoodResult(BaseModel):
    mood: str
    confidence: float
    tags: list[str]

These models define the shared data language across modules.

--------------------------------------------------

Memory / Cache
Location:
pawagent/memory/

Responsibilities:
- store historical analysis
- retrieve past records
- cache unified analysis results by content hash
- invalidate cached results by analysis version / prompt version
- build analysis context

Example:

get_recent_analysis(pet_id)
build_context(pet_id)
get_cached_analysis(content_hash)

Memory should not perform inference.

--------------------------------------------------

Agents / Views
Location:
pawagent/agents/

Agents implement high-level tasks.

Examples:
PetEmotionAgent
PetBehaviorAgent
PetMotivationAgent
PetExpressionAgent

Task-specific agents should consume a shared analysis result instead of each issuing separate model requests for the same source item.

Recommended responsibilities:
- Emotion agent: return first-layer current state analysis
- Behavior agent: return first-layer observable action analysis
- Motivation agent: return second-layer inferred motive or interaction goal
- Expression agent: return a stable natural-language rendering grounded in the same structured result
- Localized expression flow: optionally render a requested locale from the structured result and cache it separately by locale/style

Typical flow:

image / video
→ modality analyzer
→ unified analysis result
→ cache by content hash
→ task-specific agent view
→ result

Recommended CLI shape:
- `analyze-emotion <source> --modality image|video`
- `analyze-behavior <source> --modality image|video`
- `analyze-motivation <source> --modality image|video`
- `express-pet <source> --modality image|video`
- `enroll-identity <source> --pet-id ...`
- `verify-identity <source> --pet-id ...`

Important boundary:
- Emotion and behavior are first-layer outputs and should be grounded directly in evidence.
- Motivation is a second-layer inference derived from emotion, behavior, and context.
- Expression is a rendering layer and should not introduce new unsupported facts.

--------------------------------------------------
4. CLI INTERFACE
--------------------------------------------------

PawAgent must provide a CLI.

Location:
cli/main.py

Example command:

pawagent analyze-emotion dog.jpg

Expected output:

Emotion: playful
Confidence: 0.87

The CLI must internally call agents.

The CLI should eventually support:
- running unified analysis once per content hash
- returning cached slices for different task requests
- exposing provider and analysis metadata for debugging

Current product emphasis:
- image analysis
- short-video analysis

Audio should remain optional and non-primary until its product value is validated more clearly.

--------------------------------------------------
5. EXAMPLE USAGE
--------------------------------------------------

Example Python usage:

1. Create or retrieve unified analysis for a source item.
2. Store the analysis by content hash with version metadata.
3. Return the requested task-specific slice.

--------------------------------------------------
6. DEVELOPMENT TASKS
--------------------------------------------------

Task 1
Create repository structure.

Task 2
Implement Pydantic models.

Task 3
Implement provider abstraction.

Task 4
Implement modality analyzers that emit a shared semantic structure.

Task 5
Implement unified analysis caching by content hash.

Task 6
Implement task-specific emotion / behavior / motivation / expression views.

Task 7
Implement personality cue aggregation and long-term profiler.

Task 8
Implement CLI interface over unified analysis and task views.

Task 9
Add examples and tests.

--------------------------------------------------
7. ACCEPTANCE CRITERIA
--------------------------------------------------

The project is complete when:

- pip install -e . works
- CLI command runs
- a unified analysis result can be cached and reused
- task-specific views can be returned without re-calling the model for the same content
- examples execute successfully
- tests pass

--------------------------------------------------
8. FUTURE EXTENSIONS
--------------------------------------------------

Future modules may include:

- video emotion analysis
- training pipelines
- plugin system
- device integrations
- hosted inference service
