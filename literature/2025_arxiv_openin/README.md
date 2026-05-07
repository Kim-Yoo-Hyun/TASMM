# OpenIN: Open-Vocabulary Instance-Oriented Navigation in Dynamic Domestic Environments

## Bibliographic Info

- Year/Venue: 2025 arXiv
- Source: https://arxiv.org/abs/2501.04279

## One-Line Contribution

Uses carrier-relationship scene graphs to navigate to moved object instances in dynamic domestic environments.

## Existing Limitation

Object navigation often works at semantic category level and lacks dynamic update of scene representation for frequently moved instances.

## Why This Is Semantic Mapping

The map stores object-carrier relationships and updates carrying status as the scene changes.

## Method / Map Representation

Open-vocabulary Carrier-Relationship Scene Graph (CRSG), MDP navigation strategy, LLM commonsense, VLM similarity.

## Dataset / Benchmark / Metrics

Long-sequence tasks in Habitat and real robot validation; moved-target navigation efficiency and success.

## Author Organization Pattern

Motivates from daily object movement, defines carrier relations, then evaluates long-sequence dynamic navigation.

## Useful Insight

Stale object locations can be handled through relation memory, not only time decay.

## Failure Lesson

If carrier priors fail, commonsense location reasoning may be too brittle for user-specific homes.
