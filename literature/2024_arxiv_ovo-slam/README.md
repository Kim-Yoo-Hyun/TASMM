# OVO-SLAM: Open-Vocabulary Online Semantic Mapping for SLAM

## Bibliographic Info

- Year/Venue: 2024 arXiv, accepted RA-L 2025
- Source: https://arxiv.org/abs/2411.15043

## One-Line Contribution

Presents an online open-vocabulary semantic SLAM pipeline integrated with SLAM backbones and loop closure.

## Existing Limitation

Many open-vocabulary 3D mapping methods assume ground-truth poses or offline reconstruction.

## Why This Is Semantic Mapping

It couples open-vocabulary semantic mapping with online SLAM, making semantic map construction feasible during robot operation.

## Method / Map Representation

Detects and tracks 3D segments, computes CLIP descriptors from observed viewpoints, and learns descriptor merging.

## Dataset / Benchmark / Metrics

Segmentation metrics, compute/memory footprint, integration with Gaussian-SLAM and ORB-SLAM2.

## Author Organization Pattern

Targets a systems assumption, contributes a mapping thread, then evaluates both semantic quality and SLAM integration.

## Useful Insight

Pose uncertainty and loop closure must be treated as part of semantic mapping, not preprocessing.

## Failure Lesson

If semantics degrade after loop closure, map update consistency is the missing contribution.
