# O2V-Mapping: Online Open-Vocabulary Mapping with Neural Implicit Representation

## Bibliographic Info

- Year/Venue: 2024 ECCV
- Source: https://arxiv.org/abs/2404.06836

## One-Line Contribution

Builds an online open-vocabulary scene field with voxel-based language and geometry features.

## Existing Limitation

Open-vocabulary neural implicit mapping struggles with local updates, blurry hierarchical segmentation, and multi-view semantic inconsistency.

## Why This Is Semantic Mapping

The paper designs how language and geometry are stored and updated locally in a map during online observation.

## Method / Map Representation

Voxel-based open-vocabulary field, object-level language features from foundation segmentation, spatial adaptive voxel adjustment, and multi-view weighting.

## Dataset / Benchmark / Metrics

Open-vocabulary object localization and semantic segmentation.

## Author Organization Pattern

Clearly lists three technical obstacles, maps each obstacle to one method component, and validates with localization/segmentation.

## Useful Insight

A strong method section can be organized as limitation-to-module mapping.

## Failure Lesson

If online performance fails, the bottleneck may be semantic consistency under repeated viewpoints.
