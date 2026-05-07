# Paper Card

## Problem

Incremental open-vocabulary semantic mapping suffers when dense semantic fusion and instance reconstruction are tightly coupled.

## Core Idea

Decouple class-agnostic instance reconstruction from semantic inference.

## Input / Output

- Input: RGB-D observations
- Output: incremental instance-semantic map

## Method

Builds class-agnostic 3D instance map and extracts semantic features from selected views.

## Main Claims

- Decoupling geometry/instance reconstruction from semantic labeling improves real-time open-vocabulary instance-semantic mapping.

## Strengths

- Recent 2026 evidence for instance-first semantic mapping.

## Limitations

- Does not by itself solve human intent or stale memory.

## Relevance to My Research

Good representation baseline if implementing object-level memory.

## Follow-up Questions

- Can selected semantic views be chosen based on task intent or staleness?
