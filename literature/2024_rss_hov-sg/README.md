# HOV-SG: Hierarchical Open-Vocabulary 3D Scene Graphs for Language-Grounded Robot Navigation

## Bibliographic Info

- Year/Venue: 2024 RSS
- Source: https://arxiv.org/abs/2403.17846

## One-Line Contribution

Constructs floor-room-object open-vocabulary 3D scene graphs for long-horizon language-grounded robot navigation.

## Existing Limitation

Dense open-vocabulary maps struggle with large-scale environments and abstract queries beyond object-level terms.

## Why This Is Semantic Mapping

The map stores hierarchical semantic entities and supports traversal over floors, rooms, and objects.

## Method / Map Representation

Segment-level 3D open-vocabulary maps are lifted into a hierarchy of floor, room, and object nodes plus a cross-floor Voronoi navigation graph.

## Dataset / Benchmark / Metrics

Three datasets, object/room/floor semantic accuracy, representation size, real-world multi-story navigation.

## Author Organization Pattern

Starts with scale and abstraction gap, introduces hierarchy, quantifies semantic accuracy and compression, then shows real navigation.

## Useful Insight

Hierarchy is not decoration; it provides the abstraction level needed for human commands.

## Failure Lesson

If hierarchy fails, the map may need better room/region boundary inference or relation grounding.
