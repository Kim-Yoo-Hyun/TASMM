# One Map to Find Them All: Real-Time Open-Vocabulary Mapping for Zero-Shot Multi-Object Navigation

## Bibliographic Info

- Year/Venue: 2024 arXiv
- Source: https://arxiv.org/abs/2409.11764

## One-Line Contribution

Introduces reusable probabilistic-semantic maps and a multi-object navigation benchmark for repeated open-vocabulary searches.

## Existing Limitation

Zero-shot object navigation often treats each query as a fresh unknown-environment search and discards useful prior search information.

## Why This Is Semantic Mapping

The core claim is that a reusable map with uncertainty should accumulate and exploit semantic evidence across multiple object queries.

## Method / Map Representation

Open-vocabulary feature map with probabilistic-semantic updates and uncertainty-guided exploration.

## Dataset / Benchmark / Metrics

Single and multi-object navigation in simulation and real robot; real-time Jetson Orin AGX deployment; success/SPL and object-search efficiency.

## Author Organization Pattern

Defines a new task gap, introduces benchmark, proposes a reusable map, and validates on sim plus robot hardware.

## Useful Insight

Repeated queries are a clean way to measure whether semantic memory is actually useful.

## Failure Lesson

If reuse hurts, stale or miscalibrated semantic uncertainty may be worse than no memory.
