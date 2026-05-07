# OpenMap: Instruction Grounding via Open-Vocabulary Visual-Language Mapping

## Bibliographic Info

- Year/Venue: 2025 ACM MM
- Source: https://openmap-project.github.io/openmap.github.io/

## One-Line Contribution

Builds instance-level open-vocabulary visual-language maps for grounding free-form navigation instructions.

## Existing Limitation

Visual-language maps can fail to align free-form commands with specific scene instances because of cross-view inconsistency and weak instruction interpretation.

## Why This Is Semantic Mapping

Instruction grounding depends on 3D instance aggregation and semantic consistency in the map.

## Method / Map Representation

Fine-grained instance-level semantic mapping with Structural-Semantic Consensus over global geometry and VLM similarity.

## Dataset / Benchmark / Metrics

Matterport3D navigation scenes; instruction-to-instance grounding accuracy.

## Author Organization Pattern

Starts from instruction grounding, identifies consistency and interpretation issues, then designs a consensus constraint.

## Useful Insight

For human-friendly robots, instance consistency matters more than category-level heatmaps.

## Failure Lesson

If generic instructions still fail, the map may lack relation and intent structure beyond instance labels.
