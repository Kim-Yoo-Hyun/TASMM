# ConceptGraphs: Open-Vocabulary 3D Scene Graphs for Perception and Planning

## Bibliographic Info

- Year/Venue: 2024 ICRA
- Source: https://concept-graphs.github.io/

## One-Line Contribution

Builds open-vocabulary 3D scene graphs from posed RGB-D observations for language querying, localization, and LLM-based planning.

## Existing Limitation

Per-point language feature maps do not scale well and lack semantic spatial relationships needed for planning.

## Why This Is Semantic Mapping

The semantic map is explicitly graph-structured: objects are nodes with VLM descriptors and edges encode relations for reasoning.

## Method / Map Representation

2D foundation models segment/caption observations, multi-view association fuses them into 3D objects, and LLM/VLM outputs form object captions and relations.

## Dataset / Benchmark / Metrics

Downstream planning, text queries, re-localization, and qualitative/quantitative scene understanding tasks.

## Author Organization Pattern

The paper frames dense feature maps as insufficient, introduces graph representation, then demonstrates multiple downstream uses.

## Useful Insight

A semantic mapping paper can argue through representation utility across several tasks, not one benchmark only.

## Failure Lesson

If graph queries fail on compositional or negated language, relation extraction and query reasoning are likely weak points.
