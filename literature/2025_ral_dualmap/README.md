# DualMap: Online Open-Vocabulary Semantic Mapping for Natural Language Navigation in Dynamic Changing Scenes

## Bibliographic Info

- Year/Venue: 2025 RA-L
- Source: https://arxiv.org/abs/2506.01950

## One-Line Contribution

Uses a global abstract map and local concrete map to support online language navigation in dynamic scenes.

## Existing Limitation

Existing methods can be costly due to 3D object merging and brittle when environments change.

## Why This Is Semantic Mapping

The semantic map is split by function: global candidate selection and local goal reaching under dynamic updates.

## Method / Map Representation

Hybrid segmentation frontend, object-level status check, dual-map representation with dynamic update handling.

## Dataset / Benchmark / Metrics

Simulation and real-world scenarios; 3D open-vocabulary segmentation, mapping efficiency, language-guided navigation.

## Author Organization Pattern

Defines online/dynamic requirements, proposes map decomposition, then validates both mapping and navigation.

## Useful Insight

Separating abstract and concrete map roles is useful for intent-aware mapping.

## Failure Lesson

If global selection is right but local reaching fails, metric geometry and navigation interface are bottlenecks.
