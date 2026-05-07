# FindAnything: Open-Vocabulary and Object-Centric Mapping for Robot Exploration in Any Environment

## Bibliographic Info

- Year/Venue: 2025 arXiv
- Source: https://arxiv.org/abs/2504.08603

## One-Line Contribution

Builds object-centric volumetric submaps with VLM features for real-time open-vocabulary exploration.

## Existing Limitation

Real-time open-vocabulary semantic understanding of large unknown environments remains limited by compute and memory.

## Why This Is Semantic Mapping

It changes the storage granularity from dense pixels/features to object-centric submaps queried by language.

## Method / Map Representation

Volumetric occupancy submaps, eSAM segments, object-level VLM feature aggregation, deformation under pose updates.

## Dataset / Benchmark / Metrics

Replica semantic accuracy, memory/runtime efficiency, simulated search-and-rescue exploration, resource-constrained MAV deployment.

## Author Organization Pattern

Starts from deployment constraints, proposes object-centric storage, then proves task utility and resource feasibility.

## Useful Insight

Object-centric aggregation is a strong baseline for any efficient semantic mapping thesis.

## Failure Lesson

If small/occluded object queries fail, object-level aggregation may discard necessary fine detail.
