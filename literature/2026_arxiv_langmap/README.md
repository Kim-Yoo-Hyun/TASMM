# LangMap: A Hierarchical Benchmark for Open-Vocabulary Goal Navigation

## Bibliographic Info

- Year/Venue: 2026 arXiv
- Source: https://arxiv.org/abs/2602.02220

## One-Line Contribution

Introduces HieraNav and LangMap for multi-granularity open-vocabulary navigation across scene, room, region, and instance goals.

## Existing Limitation

Open-vocabulary navigation benchmarks often lack hierarchical semantic levels and human-verified discriminative descriptions.

## Why This Is Semantic Mapping

Maps must support grounding at different abstraction levels, from whole scenes to specific instances.

## Method / Map Representation

Benchmark and task definition; not a mapping method.

## Dataset / Benchmark / Metrics

Real-world 3D indoor scans, human-verified annotations, 414 object categories, 18K+ navigation tasks; success across instruction styles and semantic levels.

## Author Organization Pattern

Defines communication need, builds hierarchical benchmark, evaluates zero-shot and supervised models, then analyzes failure modes.

## Useful Insight

Our thesis should decide which semantic granularity it claims to improve.

## Failure Lesson

If a map performs at instance level but fails room/region queries, it lacks abstraction.
