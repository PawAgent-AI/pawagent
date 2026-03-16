# PawAgent Architecture

PawAgent is organized as a pure Python library with clear layer boundaries.

## Architecture Diagram

```text
┌─────────────────────────────────────────────────────────────────┐
│                         CLI / Application                       │
│                  (cli/main.py or user code)                     │
│         --log-level DEBUG|INFO|WARNING|ERROR                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
┌──────────────────┐ ┌──────────────┐ ┌─────────────────┐
│   Task Agents    │ │  Expression  │ │   Personality    │
│                  │ │    Agent     │ │     Agent        │
│ · EmotionAgent   │ │              │ │                  │
│ · BehaviorAgent  │ │ render +     │ │ profile from     │
│ · MotivationAgent│ │ localize     │ │ analysis history │
└────────┬─────────┘ └──────┬───────┘ └────────┬─────────┘
         │                  │                  │
         └──────────────────┼──────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              UnifiedMediaAnalysisService                        │
│                                                                 │
│  · one source → one UnifiedAnalysisResult                       │
│  · content-hash caching via AnalysisStore                       │
│  · dispatches to VisionAnalyzer or VideoAnalyzer                │
└────────────────────────────┬────────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼                             ▼
   ┌──────────────────┐          ┌──────────────────┐
   │  VisionAnalyzer  │          │  VideoAnalyzer   │
   │  (image input)   │          │  (video input)   │
   │  preprocess →    │          │  prompt →        │
   │  provider call   │          │  provider call   │
   └────────┬─────────┘          └────────┬─────────┘
            └──────────────┬──────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Provider Layer                             │
│                                                                 │
│  MockProvider │ OpenAIProvider │ GeminiProvider │ CLI Providers  │
│                                                                 │
│  Each provider accepts a prompt + media and returns raw JSON    │
│  that is parsed into UnifiedAnalysisResult                      │
└─────────────────────────────────────────────────────────────────┘

                  ─── Supporting Layers ───

┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│     Memory       │  │    Identity      │  │   Expression     │
│                  │  │                  │  │   Store          │
│ · AnalysisStore  │  │ · PetCropper     │  │                  │
│   (InMemory /    │  │   (NoOp /        │  │ · Localization   │
│    JSON)         │  │    MaskRCNN)     │  │   cache by       │
│ · content-hash   │  │ · IdentityEmbed  │  │   content hash   │
│   cache lookup   │  │   (Hash /        │  │   + locale       │
│ · history by     │  │    OpenClip)     │  │   + style        │
│   pet_id         │  │ · ProfileStore   │  │                  │
└──────────────────┘  └──────────────────┘  └──────────────────┘
```

## Data Flow

```text
Image/Video Source
       │
       ▼
  content_hash(source)
       │
       ├── cache hit? ──▶ return cached AnalysisRecord
       │
       ▼ (cache miss)
  VisionAnalyzer / VideoAnalyzer
       │
       ▼
  Provider.analyze_image / analyze_video
       │
       ▼
  raw JSON response
       │
       ▼
  parse → UnifiedAnalysisResult
       │
       ├── emotion   (first layer)
       ├── behavior  (first layer)
       ├── motivation (second layer)
       ├── expression (rendering layer)
       └── evidence
       │
       ▼
  AnalysisRecord → store in AnalysisStore
       │
       ▼
  Task Agent extracts its view (emotion / behavior / motivation / expression)
```

## Module Boundaries

- `providers/`: model connectors only
- `vision/`, `video/`: primary stateless modality analyzers
- `memory/`: source history, unified analysis cache, and content-hash lookup
- `identity/`: pet cropping, fingerprint embedding, and pet-id verification
- `agents/`: task-specific views over shared analysis results
- `personality/`: trait derivation from analysis history
- `expression/`: localized expression caching
- `cli/`: thin interface over agents

## Recommended Flow

1. CLI or application code submits an image or short video source.
2. The corresponding modality analyzer preprocesses input and uses a provider.
3. The analyzer produces one unified semantic result for that source item.
4. The result is cached by content hash plus provider/model/prompt version.
5. First-layer views expose emotion and behavior.
6. Second-layer views infer motivation from the first-layer results.
7. Expression views render the structured result into natural language.
8. Optional localized expression views render into a requested locale and cache the localized result by content hash, analysis version, locale, and style.
9. Identity services maintain a separate reference-profile store for verifying whether a new image likely matches an enrolled pet.

This design keeps model calls low, keeps task outputs consistent, and allows the same source item to support multiple agent views without repeated inference.

Audio can remain as an internal extension point, but it is not a primary user-facing workflow in the current product scope.

## Identity Notes

- Default CLI identity path uses a no-extra-dependency fallback (`noop` cropper + `hash` embedder)
- Production-oriented local identity path is `maskrcnn` cropper + `openclip` embedder
- Identity results should be treated as probabilistic verification, not guaranteed biometric recognition
- Enrollment is append-only and should accumulate multiple reference views per `pet-id`
- The first real `openclip` run may download weights into local Hugging Face / torch caches
- `HF_TOKEN` is optional for public weights and only affects download rate limits
