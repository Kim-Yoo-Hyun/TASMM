# Language Embedded 3D Gaussians for Open-Vocabulary Scene Understanding

## Bibliographic Info

- Year/Venue: 2024 CVPR
- Source: https://cvpr.thecvf.com/virtual/2024/poster/29360

## One-Line Contribution

Embeds language semantics into 3D Gaussian representations while controlling memory and rendering cost.

## Existing Limitation

Language-embedded 3D representations can be expensive to train/render, and raw high-dimensional language features are costly to store.

## Why This Is Semantic Mapping

It asks what semantic signal should be stored inside a 3D map representation so open-vocabulary query remains efficient.

## Method / Map Representation

3D Gaussians with quantized language embeddings and a smoothing procedure to reduce multi-view inconsistency.

## Dataset / Benchmark / Metrics

Open-vocabulary localization and segmentation; rendering quality and real-time rendering frame rate.

## Author Organization Pattern

Starts from efficiency and memory limits, proposes representation compression, then evaluates both visual quality and language query accuracy.

## Useful Insight

Efficiency is a first-class contribution when semantic maps must run on robots.

## Failure Lesson

If compressed features hurt rare-object retrieval, the representation may be efficient but not human-friendly enough.
