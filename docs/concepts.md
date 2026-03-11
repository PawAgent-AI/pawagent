# PawAgent Concepts

## Provider

A provider connects PawAgent to a specific model backend. Providers normalize external APIs and avoid business logic.

## Capability

A capability module performs modality-specific processing such as image or video preparation and normalization. Capabilities are stateless.

## Unified Analysis

A unified analysis is the shared semantic result produced from one source item. It should contain reusable slices for emotion, behavior, motivation, expression, and evidence.

## Agent

An agent is a task-specific view over a unified analysis result. Different agents may answer different questions from the same source item without requiring repeated model calls.

## Memory

Memory stores past analysis records, caches unified analysis results by content hash, and exposes retrieval helpers for building context. It does not call models.

## Motivation

Motivation is a second-layer inference. It should be predicted from first-layer emotion and behavior outputs plus any grounded context, rather than treated as a directly observed fact.

## Expression

Expression is the stable human-readable or pet-voice rendering included in the unified result. It should be grounded in emotion, behavior, motivation, and evidence, and should not change across repeated requests for the same source item unless the analysis version changes.

Localized expression is a rendering-layer extension. It should reuse the structured analysis result, optionally use a lightweight second-pass model call, and cache per locale and style.

## Identity

Identity is a separate verification capability for checking whether a new image likely belongs to an enrolled `pet-id`.

It should use:

- subject cropping or segmentation
- visual fingerprint embedding
- a dedicated identity profile store

It should not treat emotion/behavior memory as an identity source of truth.

Identity verification is probabilistic and should be exposed as a confidence-based match result, not an absolute claim.
Identity enrollment should be append-only so a `pet-id` can accumulate multiple reference images across pose, lighting, and background changes.
For the real local pipeline, `openclip` may download public model files on first use. `HF_TOKEN` is optional and only improves Hugging Face download limits.

## Audio

Audio may remain as a future or internal extension, but it is not a primary product surface compared with image and short-video analysis.
