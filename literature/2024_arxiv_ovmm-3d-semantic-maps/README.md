# Open-Vocabulary Mobile Manipulation in Unseen Dynamic Environments with 3D Semantic Maps

## Bibliographic Info

- Year/Venue: 2024 arXiv
- Source: https://arxiv.org/abs/2406.18115

## One-Line Contribution

Uses 3D semantic maps plus LLM planning for zero-shot mobile manipulation in unseen dynamic environments.

## Existing Limitation

OVMM requires exploration, semantic understanding, planning, adaptation to changes, and language instruction following; many systems handle only pieces.

## Why This Is Semantic Mapping

The 3D semantic map provides spatial semantic context for planning and replanning when the initial plan fails.

## Method / Map Representation

VLM-based open-vocabulary detection, dense 3D entity reconstruction, spatial region abstraction, and LLM online planning.

## Dataset / Benchmark / Metrics

Real JSR-1 10-DoF robot, 105 episodes; navigation success, manipulation task success, SFT, SPL, replanning success.

## Author Organization Pattern

Frames an end-to-end embodied task, defines map layers, then evaluates real robot task success.

## Useful Insight

A top-tier semantic mapping paper is stronger when the map is connected to manipulation, not only search.

## Failure Lesson

If planning fails despite good detection, the map lacks actionable affordance or region abstraction.
