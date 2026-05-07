# OGScene3D: Incremental Open-Vocabulary 3D Gaussian Scene Graph Mapping for Scene Understanding

## Bibliographic Info

- Year/Venue: 2026 arXiv
- Source: https://arxiv.org/abs/2603.16301

## One-Line Contribution

Builds semantic Gaussian maps and scene graphs incrementally with confidence, temporal memory, and progressive graph updates.

## Existing Limitation

Many scene graph methods require a pre-built complete semantic map, which does not fit robots exploring incrementally.

## Why This Is Semantic Mapping

It jointly maintains map semantics and graph structure online as new observations arrive.

## Method / Map Representation

Confidence-based Gaussian semantic representation, hierarchical semantic optimization, temporal memory, and progressive scene graph construction.

## Dataset / Benchmark / Metrics

Widely used datasets and real-world scenes; open-vocabulary scene understanding.

## Author Organization Pattern

Frames incremental operation as the missing requirement, then connects confidence, consistency, memory, and graph update modules.

## Useful Insight

Confidence and temporal memory are becoming expected components in serious online semantic maps.

## Failure Lesson

If incremental graph updates drift, long-term semantic consistency remains unsolved.
