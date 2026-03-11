# PawAgent Architecture

PawAgent is organized as a pure Python library with clear layer boundaries:

- `providers/`: model connectors only
- `vision/`, `video/`: primary stateless modality analyzers
- `memory/`: source history, unified analysis cache, and content-hash lookup
- `identity/`: pet cropping, fingerprint embedding, and pet-id verification
- `agents/`: task-specific views over shared analysis results
- `cli/`: thin interface over agents

Recommended flow:

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

Recommended CLI shape:

- `analyze-emotion <source> --modality image|video`
- `analyze-behavior <source> --modality image|video`
- `analyze-motivation <source> --modality image|video`
- `express-pet <source> --modality image|video`
- `enroll-identity <source> --pet-id ...`
- `verify-identity <source> --pet-id ...`

Identity notes:

- default CLI identity path uses a no-extra-dependency fallback (`noop` cropper + `hash` embedder)
- production-oriented local identity path is `maskrcnn` cropper + `openclip` embedder
- identity results should be treated as probabilistic verification, not guaranteed biometric recognition
- enrollment is append-only and should accumulate multiple reference views per `pet-id`
- the first real `openclip` run may download weights into local Hugging Face / torch caches
- `HF_TOKEN` is optional for public weights and only affects download rate limits
