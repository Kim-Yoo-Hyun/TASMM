# HM3D-OVON: A Dataset and Benchmark for Open-Vocabulary Object Goal Navigation

## Bibliographic Info

- Year/Venue: 2024 arXiv
- Source: https://arxiv.org/abs/2409.14296

## One-Line Contribution

Creates a large open-vocabulary ObjectNav benchmark on HM3D with free-form language goals.

## Existing Limitation

Prior ObjectNav benchmarks are limited to a small closed set of categories.

## Why This Is Semantic Mapping

Semantic maps must support retrieval and navigation to arbitrary household objects specified by text at test time.

## Method / Map Representation

Benchmark with baselines; not a new map representation.

## Dataset / Benchmark / Metrics

HM3D-Sem, 15k+ object instances, 379 categories; ObjectNav success, SPL, robustness to localization/actuation noise.

## Author Organization Pattern

Builds dataset motivation from closed-vocabulary limits, defines open-set benchmark, then compares agent families.

## Useful Insight

This is a natural first benchmark for open-vocabulary semantic navigation claims.

## Failure Lesson

If a semantic map fails here, it likely lacks category coverage or robust object localization.
