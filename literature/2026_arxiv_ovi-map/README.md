# OVI-MAP: Open-Vocabulary Instance-Semantic Mapping

## Bibliographic Info

- Year/Venue: 2026 arXiv
- Source: https://arxiv.org/abs/2603.26541

## One-Line Contribution

Decouples class-agnostic instance reconstruction from semantic inference for real-time open-vocabulary mapping.

## Existing Limitation

Closed-set assumptions and dense per-pixel language fusion limit scalability and temporal consistency.

## Why This Is Semantic Mapping

It asks when and from which views semantic features should be extracted for a stable online instance map.

## Method / Map Representation

Incremental class-agnostic 3D instance map from RGB-D; semantic features extracted from selected views using VLMs.

## Dataset / Benchmark / Metrics

Standard open-vocabulary mapping benchmarks; real-time operation and state-of-the-art baseline comparison.

## Author Organization Pattern

Names robustness, real-time, and open-set reasoning as the key challenge; solves by decoupling geometry and semantics.

## Useful Insight

Decoupling instance tracking from semantic labeling may be essential for dynamic semantic memory.

## Failure Lesson

If selected views miss important semantics, the system needs active viewpoint selection tied to task intent.
