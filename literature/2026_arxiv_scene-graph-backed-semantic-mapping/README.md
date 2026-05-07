# A Scene Graph Backed Approach to Open Set Semantic Mapping

## Bibliographic Info

- Year/Venue: 2026 arXiv
- Source: https://arxiv.org/abs/2602.03781

## One-Line Contribution

Proposes using the 3D scene graph as the foundational backend for open-set semantic mapping.

## Existing Limitation

Many systems decouple perception and representation, treating scene graphs as post-hoc summaries, limiting consistency and scalability.

## Why This Is Semantic Mapping

The semantic map is the graph itself: a spatially grounded, updateable knowledge representation for reasoning.

## Method / Map Representation

Incremental scene graph prediction and update, supporting flat and hierarchical topologies for large-scale environments.

## Dataset / Benchmark / Metrics

Position/workflow proposal; evaluation direction is real-time consistency, scalability, and reasoning support.

## Author Organization Pattern

Conceptual architecture paper: identifies representation decoupling, proposes backend inversion, argues reasoning benefits.

## Useful Insight

This supports a thesis argument that graph memory should be online, not derived after mapping.

## Failure Lesson

If graph-as-backend cannot maintain geometry fidelity, a hybrid metric-graph representation is needed.
