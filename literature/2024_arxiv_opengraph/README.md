# OpenGraph: Open-Vocabulary Hierarchical 3D Graph Representation in Large-Scale Outdoor Environments

## Bibliographic Info

- Year/Venue: 2024 arXiv
- Source: https://arxiv.org/abs/2403.09412

## One-Line Contribution

Builds an open-vocabulary hierarchical graph representation for large-scale outdoor environments.

## Existing Limitation

Open-vocabulary maps are mainly designed for small indoor environments and do not generalize directly to outdoor, object-rich, task-complex scenes.

## Why This Is Semantic Mapping

The paper changes the map structure to support large-scale object-centric semantics and lane-graph hierarchy.

## Method / Map Representation

Instance extraction and captioning from images, projection into LiDAR point clouds, incremental object-centric mapping, and lane-connectivity hierarchy.

## Dataset / Benchmark / Metrics

SemanticKITTI; segmentation and query accuracy.

## Author Organization Pattern

States domain scale mismatch, designs outdoor hierarchy, then evaluates segmentation/query accuracy.

## Useful Insight

Scale changes the right map representation; indoor assumptions may not transfer.

## Failure Lesson

If graph hierarchy fails outdoors, semantic mapping may require stronger topology and traversability modeling.
